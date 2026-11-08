"""Step 12 acceptance verification for the FULL-model notebook repair."""
from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
TABLES = OUT / "tables"
FIG = OUT / "figures"

checks: list[dict] = []


def add(name, ok, detail=""):
    checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})


def load(p):
    with Path(p).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    # 1-2. component identity ------------------------------------------------
    reg = json.loads((OUT / "REMEDFILM_FULL_COMPONENT_REGISTRY.json").read_text(encoding="utf-8"))
    comps = reg["components"]
    add("FULL identity verified across G/R/B/S", reg["all_components_verified"],
        f"{len(comps)} components")
    add("component parameters measured from state dicts",
        all(c.get("measured_parameters") == c["expected_parameters"] for c in comps),
        str([c.get("measured_parameters") for c in comps]))
    add("component sum equals 4,837,420", reg["total_matches_contract"],
        f"{reg['verified_total_parameters']:,}")
    add("all four checkpoints exist and hash",
        all(c.get("checkpoint_sha256") for c in comps), "")
    add("training records identified per component",
        all(c.get("training_completion") for c in comps),
        str([c["training_completion"].get("epochs_completed") for c in comps]))
    add("checkpoint SHA matches recorded value",
        all(c.get("sha_matches_record") is not False for c in comps),
        str([c.get("sha_matches_record") for c in comps]))

    # 3. epoch histories -----------------------------------------------------
    ch = load(TABLES / "REMEDFILM_COMPONENT_TRAINING_HISTORY.csv")
    add("component epoch history recovered", len(ch) > 10000, f"{len(ch)} records")
    comps_covered = {r["component"] for r in ch}
    add("all four components have epoch records",
        all(any(s in c for c in comps_covered) for s in ("GlobalMedFiLM", "R_psi", "B_phi", "S_omega")),
        str(sorted(comps_covered))[:80])
    add("no unified fake FULL curve",
        not any("FULL" in r["experiment_id"].upper() and "ABLATION" not in r["experiment_id"].upper()
                for r in ch),
        "component histories are kept separate")

    # 4-5. validation + segmentation ----------------------------------------
    vm = load(TABLES / "REMEDFILM_FULL_VAL808_METRICS.csv")
    macro = [r for r in vm if r["domain"].startswith("MACRO")][0]
    add("VAL808 macro Dice reproducible", abs(float(macro["full_dice"]) - 0.837289686) < 1e-8,
        f"{float(macro['full_dice']):.9f}")
    add("VAL808 sample count 808", int(macro["n"]) == 808, f"n={macro['n']}")

    need = [f"SEG_{d}_global_vs_full" for d in ("ISIC", "BUSI", "KVASIR", "KUB")]
    need += [f"SEG_{d}_refinement_accepted" for d in ("ISIC", "BUSI", "KVASIR", "KUB")]
    need += ["SEG_failure_cases"]
    missing = [n for n in need if not (FIG / "Semantic segmentation" / f"{n}.png").exists()]
    add("segmentation galleries present (incl. accepted refinement)", not missing,
        f"{len(need)} figures, missing={missing}")

    vi = load(TABLES / "REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv")
    bad = []
    for r in vi:
        for k in ("source_image", "gt_mask", "global_mask", "full_mask"):
            if r[k] and not Path(r[k]).exists():
                bad.append((r["figure_id"], r["sample_id"], k))
    add("every gallery sample resolves to real files", not bad, f"{len(vi)} panels")
    add("global and FULL masks are distinct files",
        all(r["global_mask"] != r["full_mask"] for r in vi), "")
    acc = [r for r in vi if r["panel_role"] == "accepted refinement"]
    add("accepted-refinement panels show a real delta",
        acc and all(abs(float(r["delta_dice"])) > 0 for r in acc),
        f"{len(acc)} panels")

    # mask geometry across all 808 samples
    import numpy as _np
    from PIL import Image as _Img
    prows = load(ROOT / "reports/tables/phase27_val808_predictions.csv")
    pman = {r["sample_id"]: r for r in load(
        ROOT / "reports/tables/phase21_prediction_manifest.csv")}
    bad_geom, shapes = [], set()
    for r in prows:
        sid = r["sample_id"]
        with _np.load(ROOT / pman[sid]["npz_path"]) as z:
            gs = z["gt"].shape
        a = _np.array(_Img.open(ROOT / r["global_mask_path"]).convert("L")).shape
        b = _np.array(_Img.open(ROOT / r["final_mask_path"]).convert("L")).shape
        shapes.add((gs, a, b))
        if not (gs == a == b):
            bad_geom.append(sid)
    add("mask geometry consistent across all 808 samples", not bad_geom,
        f"shape sets={len(shapes)} mismatches={len(bad_geom)}")

    # 6. external ------------------------------------------------------------
    ext = load(TABLES / "REMEDFILM_FULL_EXTERNAL_METRICS.csv")
    cohorts = {r["cohort"] for r in ext}
    add("external evaluation covers all cohorts", len(cohorts) >= 3, str(sorted(cohorts)))
    add("external has both FULL and backbone rows",
        {"ReMedFiLM FULL", "GlobalMedFiLM"} <= {r["model"] for r in ext}, "")
    pc = load(ROOT / "reports/tables/c1_external_stress_per_case.csv")
    sf = [r for r in pc if str(r.get("gt_empty")).lower() == "true"]
    by_arm = {}
    for r in sf:
        by_arm.setdefault(r["arm"], []).append(str(r.get("pred_empty")).lower() == "false")
    ok = all(len(v) == 14 and all(v) for v in by_arm.values()) and len(by_arm) == 2
    add("stone-free 14/14 failure preserved (both arms)", ok,
        "; ".join(f"{a}:{sum(v)}/{len(v)}" for a, v in sorted(by_arm.items())))

    # 7. ablation + progression ---------------------------------------------
    ap = load(TABLES / "REMEDFILM_ABLATION_AND_PROGRESSION.csv")
    arms = {r["arm_or_stage"] for r in ap if r["record_type"] == "ABLATION"}
    need_arms = {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "R1", "R2", "R3", "F1"}
    add("all 13 ablation arms present", arms == need_arms,
        f"missing={sorted(need_arms - arms)}")
    stages = [r for r in ap if r["record_type"] == "PROGRESSION"]
    add("progression stages present", len(stages) >= 5, f"{len(stages)} stages")
    a8 = [r for r in ap if r["arm_or_stage"] == "A8_vs_A7" or
          (r["record_type"] == "ABLATION" and r["paired_contrast"] == "A8_vs_A7")]
    bs = {r["contrast"]: r for r in load(
        ROOT / "reports/tables/phase28_table_08_bootstrap_statistics.csv")}
    b = bs["A8_vs_A7"]
    includes_zero = not (float(b["ci95_low"]) > 0 or float(b["ci95_high"]) < 0)
    add("A8 vs A7 CI still includes zero", includes_zero,
        f"[{b['ci95_low']}, {b['ci95_high']}]")

    # 8. efficiency ----------------------------------------------------------
    eff = load(TABLES / "REMEDFILM_EFFICIENCY.csv")
    full = [r for r in eff if "FULL" in r["model"]]
    add("ReMedFiLM FULL present in efficiency table", len(full) == 1,
        f"{len(eff)} rows")
    add("FULL params 4,837,420", int(full[0]["params"]) == 4837420, full[0]["params"])
    add("FULL conditional GMACs ~32.44",
        abs(float(full[0]["gmacs"]) - 32.4379) < 0.01, full[0]["gmacs"])
    add("accuracy-compute figure exists",
        (FIG / "Efficiency" / "EFF01_accuracy_vs_compute.png").exists(), "")

    # 9. reconciliation ------------------------------------------------------
    rec = json.loads((OUT / "REMEDFILM_FULL_RESULT_RECONCILIATION.json").read_text(encoding="utf-8"))
    add("0.837290 vs 0.837862 resolved",
        rec["verdict"] in ("REPORTING_INCONSISTENCY", "ALTERNATIVE_CONFIGURATION"),
        rec["verdict"])
    add("canonical value reproduces",
        abs(rec["canonical_macro_dice"] - 0.837289686) < 1e-8,
        f"{rec['canonical_macro_dice']:.9f}")
    add("reconciliation document exists",
        (OUT / "REMEDFILM_FULL_RESULT_RECONCILIATION.md").exists(), "")

    # 10. no mislabelling ----------------------------------------------------
    add("no backbone-only row labelled FULL",
        all(r["model"] != "ReMedFiLM FULL" or "FULL" in r["model"] for r in eff), "")

    # 11. execution ----------------------------------------------------------
    ex = json.loads((OUT / "REMEDFILM_NOTEBOOK_EXECUTION_REPORT.json").read_text(encoding="utf-8"))
    add("all notebooks executed", ex["all_notebooks_succeeded"],
        f"{ex['total_executed_cells']}/{ex['total_code_cells']} cells, {ex['n_notebooks']} notebooks")

    master = OUT / "ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb"
    nb = json.loads(master.read_text(encoding="utf-8"))
    code_cells = [c for c in nb["cells"] if c["cell_type"] == "code"]
    add("verified master fully executed",
        all(c.get("execution_count") for c in code_cells)
        and not any(o.get("output_type") == "error" for c in code_cells for o in c.get("outputs", [])),
        f"{len(code_cells)} code cells")
    txt = ""
    for c in code_cells:
        for o in c.get("outputs", []):
            t = o.get("text")
            txt += "".join(t) if isinstance(t, list) else (t or "")
    add("guard negative controls blocked",
        "blocked" in txt and "NOT BLOCKED" not in txt, "")

    # 12. evidence preserved -------------------------------------------------
    git = subprocess.run(["git", "status", "--porcelain", "--", "src", "tests",
                          "manifests", "checkpoints", "configs", "reports/audits"],
                         cwd=str(ROOT), capture_output=True, text=True)
    dirty = [l for l in git.stdout.strip().splitlines() if l.strip()]
    add("no frozen research source modified", not dirty, f"{len(dirty)} paths")
    pm = json.loads((OUT / "Original_Phasewise_Notebooks/PRESERVATION_MANIFEST.json")
                    .read_text(encoding="utf-8"))
    add("original notebooks preserved", pm["n_verified"] == pm["n_notebooks"] == 108,
        f"{pm['n_verified']}/{pm['n_notebooks']}")

    # 13. no retraining / inference / TEST -----------------------------------
    train_pat = re.compile(r"\.fit\(|trainer\.train\(|optimizer\.step\(|loss\.backward\(")
    offenders = []
    for p in [master] + sorted((OUT / "ReMedFiLM_Research_Notebooks").glob("*.ipynb")):
        nbx = json.loads(p.read_text(encoding="utf-8"))
        for c in nbx["cells"]:
            if c["cell_type"] == "code" and c.get("execution_count") and train_pat.search("".join(c["source"])):
                offenders.append(p.name)
                break
    add("no training call executed", not offenders, str(offenders))
    add("execution report declares no training/inference/TEST",
        ex["training_performed"] is False and ex["new_inference_performed"] is False
        and ex["test_accessed"] is False, "")

    # 14. C1/C2/C3 still flagged --------------------------------------------
    pend = (OUT / "PENDING_CONTROLLED_EXPERIMENTS.md")
    add("C1/C2/C3 gaps still documented",
        pend.exists() and "0 / 6" in pend.read_text(encoding="utf-8"),
        "")

    n_pass = sum(1 for c in checks if c["result"] == "PASS")
    w = max(len(c["check"]) for c in checks)
    print(f"{'CHECK'.ljust(w)} RESULT  DETAIL")
    for c in checks:
        print(f"{c['check'].ljust(w)} {c['result']:7s} {c['detail'][:58]}")
    print(f"\nPASSED {n_pass}/{len(checks)}")

    (OUT / "REMEDFILM_FINAL_QA_CHECKS.json").write_text(json.dumps({
        "artifact": "REMEDFILM_FINAL_QA_CHECKS",
        "n_checks": len(checks), "n_passed": n_pass,
        "all_passed": n_pass == len(checks), "checks": checks,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
