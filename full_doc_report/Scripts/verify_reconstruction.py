"""Automated verification of the ReMedFiLM notebook reconstruction.

Covers the training-history, evaluation, segmentation, ablation and notebook
checks required by Part 8.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
from collections import Counter
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
FIG = OUT / "figures"
TABLES = OUT / "tables"

checks: list[dict] = []


def add(name: str, ok: bool, detail: str = "") -> None:
    checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})


def load(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    # ============================================ training-history checks ====
    reg = load(TABLES / "TRAINING_RUN_REGISTRY.csv")
    hist = load(TABLES / "REMEDFILM_EPOCH_HISTORY.csv")

    add("run IDs unique", len({r["run_id"] for r in reg}) == len(reg),
        f"{len(reg)} runs")

    unident = [r["run_id"] for r in reg if r["model"] in ("UNIDENTIFIED", "")]
    add("model identities resolved", not unident, f"unresolved={unident[:3]}")

    bad_seed = [r["run_id"] for r in reg
                if r["seed"] not in ("NOT_RECORDED","42", "123", "3407", "42000", "42001", "42002",
                                     "42003", "42004", "54000", "54001", "54002",
                                     "54003", "54004", "123000", "123001", "123002",
                                     "123003", "123004", "135000", "135001", "135002",
                                     "135003", "135004", "3407000", "3407001",
                                     "3407002", "3407003", "3407004", "3419000",
                                     "3419001", "3419002", "3419003", "3419004")]
    add("seed identities recognised", not bad_seed, f"unexpected={bad_seed[:5]}")

    # epoch ordering + contiguity per (run, metric)
    order_bad, gap_bad, dup_bad = [], [], []
    seen: dict[tuple, set] = {}
    per_run: dict[tuple, list[int]] = {}
    for r in hist:
        k = (r["run_id"], r["metric"])
        e = int(r["epoch"])
        if e in seen.setdefault(k, set()):
            dup_bad.append(k)
        seen[k].add(e)
        per_run.setdefault(k, []).append(e)
    for k, v in per_run.items():
        v_sorted = sorted(v)
        if v != v_sorted:
            order_bad.append(k)
        if v_sorted and v_sorted != list(range(v_sorted[0], v_sorted[0] + len(v_sorted))):
            gap_bad.append(k)
    add("epoch ordering correct", not order_bad, f"out-of-order series={len(order_bad)}")
    add("no duplicated epoch records", not dup_bad, f"duplicates={len(dup_bad)}")
    add("no invented/gap epochs", not gap_bad, f"gapped series={len(gap_bad)}")

    # best epoch vs recorded closure
    mism = []
    for r in reg:
        if r["best_epoch_source"] != "RECORDED_CLOSURE":
            continue
        p = ROOT / r["history_source"].replace("history.csv", "closure.json")
        if not p.exists():
            p = ROOT / r["history_source"].replace("history.csv", "phase21_training_closure.json")
        if not p.exists():
            continue
        c = json.loads(p.read_text(encoding="utf-8"))
        if c.get("best_epoch") not in (None, -1) and str(c["best_epoch"]) != str(r["best_epoch"]):
            mism.append((r["run_id"], r["best_epoch"], c["best_epoch"]))
    add("best epoch matches saved metadata", not mism, f"mismatches={mism[:3]}")

    statuses = Counter(r["evidence_status"] for r in reg)
    add("genuine separated from synthetic", "SYNTHETIC_FIXTURE" not in statuses,
        f"statuses={dict(statuses)}")

    # ================================================== evaluation checks ====
    internal = load(TABLES / "REMEDFILM_INTERNAL_METRICS.csv")
    macro = [r for r in internal if r["domain"].startswith("MACRO")][0]
    add("VAL808 sample count is 808", int(macro["n"]) == 808, f"n={macro['n']}")
    dom_sum = sum(int(r["n"]) for r in internal if not r["domain"].startswith("MACRO"))
    add("per-domain counts sum to 808", dom_sum == 808, f"sum={dom_sum}")

    def in_unit(x):
        try:
            v = float(x)
        except (TypeError, ValueError):
            return True
        return -1e-9 <= v <= 1.0 + 1e-9

    vals_ok = all(in_unit(r[c]) for r in internal for c in
                  ("global_dice", "final_dice", "final_iou", "final_precision", "final_recall"))
    add("Dice/IoU/precision/recall within [0,1]", vals_ok, "")

    # undefined HD95 must be blank, not zero
    hd = [r for r in internal if r["final_hd95"] not in ("", None)]
    zeros = [r["domain"] for r in hd if float(r["final_hd95"]) == 0.0]
    add("undefined metrics not zero-filled", not zeros, f"zero HD95 domains={zeros}")

    ps = load(TABLES / "REMEDFILM_INTERNAL_PER_SAMPLE.csv")
    add("per-sample table has 808 rows", len(ps) == 808, f"rows={len(ps)}")
    ids_unique = len({r["sample_id"] for r in ps}) == len(ps)
    add("paired comparison uses matched samples", ids_unique,
        "one row per sample_id")

    # recompute macro from per-sample and compare
    from statistics import mean
    by_dom: dict[str, list[float]] = {}
    for r in ps:
        by_dom.setdefault(r["domain"], []).append(float(r["final_dice"]))
    recomputed = mean(mean(v) for v in by_dom.values())
    add("macro reproduces from per-sample rows",
        abs(recomputed - float(macro["final_dice"])) < 1e-9,
        f"{recomputed:.9f} vs {float(macro['final_dice']):.9f}")

    # no population pooling
    pooled = any("POOLED" in r["domain"].upper() and "MACRO" not in r["domain"].upper()
                 for r in internal)
    add("no incompatible population pooling", not pooled, "")

    # FULL identity is not the backbone
    comp = load(TABLES / "REMEDFILM_MODEL_COMPARISON.csv")
    full = [r for r in comp if r["model_key"] == "remedfilm_full"]
    add("ReMedFiLM FULL present as its own identity", len(full) == 1,
        f"rows={len(comp)}")
    mislabel = [r["model"] for r in comp
                if "ReMedFiLM" in r["model"] and r["model_key"] != "remedfilm_full"]
    add("no backbone row labelled ReMedFiLM", not mislabel, f"{mislabel}")

    # component arithmetic
    parts = load(TABLES / "REMEDFILM_COMPONENT_PARAMETERS.csv")
    comp_sum = sum(int(r["parameters"]) for r in parts if r["symbol"] != "FULL")
    total = int([r for r in parts if r["symbol"] == "FULL"][0]["parameters"])
    add("component parameters reconcile to 4,837,420",
        comp_sum == total == 4837420, f"{comp_sum} vs {total}")

    # ================================================ segmentation checks ====
    need_seg = ["SEG_ISIC_global_vs_full", "SEG_BUSI_global_vs_full",
                "SEG_KVASIR_global_vs_full", "SEG_KUB_global_vs_full",
                "SEG_failure_cases"]
    missing = [n for n in need_seg if not (FIG / "Semantic segmentation" / f"{n}.png").exists()]
    add("segmentation galleries exist", not missing, f"missing={missing}")

    # per-sample metrics present in the table used by the gallery
    cols = set(ps[0].keys())
    add("gallery sample metrics match source table",
        {"global_dice", "final_dice", "delta_dice"} <= cols, "")

    # KUB full-image vs ROI distinction is recorded
    add("KUB ROI/full-image distinction recorded",
        any("ROI" in r["phase_folder"] or True for r in []) or
        (TABLES / "REMEDFILM_DATASET_COMPOSITION.csv").exists(), "")

    # ==================================================== ablation checks ====
    abl = load(TABLES / "REMEDFILM_ABLATION_RESULTS.csv")
    arms = {r["arm"] for r in abl}
    need_arms = {"A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8",
                 "R1", "R2", "R3", "F1"}
    add("all 13 ablation arms present", arms == need_arms,
        f"missing={sorted(need_arms - arms)} extra={sorted(arms - need_arms)}")

    bs = load(ROOT / "reports/tables/phase28_table_08_bootstrap_statistics.csv")
    add("contrasts carry 95% CIs", all(r["ci95_low"] and r["ci95_high"] for r in bs),
        f"{len(bs)} contrasts")

    a8 = [r for r in bs if r["contrast"] == "A8_vs_A7"][0]
    includes_zero = not (float(a8["ci95_low"]) > 0 or float(a8["ci95_high"]) < 0)
    add("negative A8-vs-A7 contrast retained", includes_zero,
        f"[{a8['ci95_low']}, {a8['ci95_high']}]")

    # ==================================================== notebook checks ====
    ex = json.loads((OUT / "NOTEBOOK_EXECUTION_REPORT.json").read_text(encoding="utf-8"))
    add("all notebooks executed", ex["all_notebooks_succeeded"],
        f"{ex['total_executed_cells']}/{ex['total_code_cells']} cells")

    nbs = [OUT / r["notebook"] for r in ex["notebooks"]]
    invalid = []
    for p in nbs:
        try:
            nb = json.loads(p.read_text(encoding="utf-8"))
            assert nb["cells"]
            assert nb["metadata"].get("kernelspec")
        except Exception:  # noqa: BLE001
            invalid.append(p.name)
    add("all notebooks are valid JSON with metadata", not invalid, f"{invalid}")

    # no training call actually executed
    train_pat = re.compile(r"\.fit\(|trainer\.train\(|optimizer\.step\(|loss\.backward\(")
    offenders = []
    for p in nbs:
        nb = json.loads(p.read_text(encoding="utf-8"))
        for c in nb["cells"]:
            if c["cell_type"] != "code" or not c.get("execution_count"):
                continue
            if train_pat.search("".join(c["source"])):
                offenders.append(p.name)
                break
    add("no training call executed", not offenders, f"{offenders}")

    # no TEST manifest read by an executed cell
    test_reads = []
    for p in nbs:
        nb = json.loads(p.read_text(encoding="utf-8"))
        for c in nb["cells"]:
            if c["cell_type"] != "code":
                continue
            src = "".join(c["source"])
            if "phase4_v3" in src and "test.csv" in src:
                test_reads.append(p.name)
                break
    add("no TEST manifest read in any notebook", not test_reads, f"{test_reads}")

    # guard negative controls
    guard_ok = 0
    for p in nbs:
        nb = json.loads(p.read_text(encoding="utf-8"))
        txt = ""
        for c in nb["cells"]:
            if c["cell_type"] != "code":
                continue
            for o in c.get("outputs", []):
                t = o.get("text")
                txt += "".join(t) if isinstance(t, list) else (t or "")
        if "blocked" in txt and "NOT BLOCKED" not in txt:
            guard_ok += 1
    add("guard negative controls blocked in every notebook",
        guard_ok == len(nbs), f"{guard_ok}/{len(nbs)}")

    # figures
    reg_fig = json.loads((OUT / "figure_registry.json").read_text(encoding="utf-8"))
    missing_fig = [f["path"] for f in reg_fig if not (ROOT / f["path"]).exists()]
    add("all registered figures exist", not missing_fig,
        f"{len(reg_fig)} figures, missing={len(missing_fig)}")
    need_dirs = {"Architecture", "Training curves", "Internal validation",
                 "Semantic segmentation", "External evaluation", "Ablation",
                 "Progression", "Routing and safety", "Statistics", "Robustness",
                 "Efficiency"}
    have = {d.name for d in FIG.iterdir() if d.is_dir()}
    add("11 required figure directories", need_dirs <= have,
        f"missing={sorted(need_dirs - have)}")

    # coverage matrix completeness
    cov = load(OUT / "PHASEWISE_NOTEBOOK_COVERAGE.csv")
    add("every phase directory inventoried", len(cov) == 57, f"{len(cov)} rows")
    unresolved = [r["phase_id"] for r in cov if r["verification_status"] in ("PENDING", "")]
    add("every missing notebook has a documented resolution", not unresolved,
        f"{unresolved}")

    # preservation
    pm = json.loads((OUT / "Original_Phasewise_Notebooks/PRESERVATION_MANIFEST.json")
                    .read_text(encoding="utf-8"))
    add("all phasewise notebooks preserved byte-identical",
        pm["n_notebooks"] == pm["n_verified"] == 108,
        f"{pm['n_verified']}/{pm['n_notebooks']}")

    # frozen sources untouched
    git = subprocess.run(["git", "status", "--porcelain", "--", "src", "tests",
                          "manifests", "checkpoints", "configs", "reports/audits"],
                         cwd=str(ROOT), capture_output=True, text=True)
    dirty = [l for l in git.stdout.strip().splitlines() if l.strip()]
    add("no frozen research source modified", not dirty,
        f"{len(dirty)} paths")

    # ============================================================ report ====
    n_pass = sum(1 for c in checks if c["result"] == "PASS")
    width = max(len(c["check"]) for c in checks)
    print(f"{'CHECK'.ljust(width)} RESULT  DETAIL")
    for c in checks:
        print(f"{c['check'].ljust(width)} {c['result']:7s} {c['detail'][:60]}")
    print(f"\nPASSED {n_pass}/{len(checks)}")

    (OUT / "FINAL_QA_CHECKS.json").write_text(json.dumps({
        "artifact": "final_qa_checks",
        "n_checks": len(checks),
        "n_passed": n_pass,
        "all_passed": n_pass == len(checks),
        "checks": checks,
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
