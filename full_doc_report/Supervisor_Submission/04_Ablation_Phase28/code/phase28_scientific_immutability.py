"""Phase 28 -- notebook compliance repair §4/§20 scientific immutability checks.

Shared module: binds every scientific Phase28 output. Used by both the pre-repair
precheck (§4) and the post-repair postcheck (§20).

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/phase28_scientific_immutability.py pre
    ./.venv/Scripts/python.exe scripts/analysis/phase28_scientific_immutability.py post
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures"
RCK = {
    "R1": ROOT / "checkpoints" / "phase28_router_R1_no_deep",
    "R2": ROOT / "checkpoints" / "phase28_router_R2_no_task",
    "R3": ROOT / "checkpoints" / "phase28_router_R3_scalar_only",
}
F1_CK = ROOT / "checkpoints" / "phase28_refiner_F1_no_pglobal"
F1_EXP = ROOT / "experiments" / "phase28_refiner_F1_no_pglobal"
D28 = ROOT / "data_cache" / "phase28_router_variants_v1_2"
F1C = ROOT / "data_cache" / "phase28_f1_refiner_v1_2"

PRE_PATH = AUD / "phase28_notebook_repair_scientific_immutability_precheck.json"
POST_PATH = AUD / "phase28_notebook_repair_scientific_immutability_postcheck.json"

SINGLE = [
    ("base_final_freeze", AUD / "phase28_final_freeze.json"),
    ("terminal_state", AUD / "phase28_terminal_state.json"),
    ("project_status", AUD / "phase28_project_status.json"),
    ("training_run_registry_json", AUD / "phase28_training_run_registry.json"),
    ("comprehensive_ablation_matrix", AUD / "phase28_comprehensive_ablation_matrix.json"),
    ("router_primary_metrics", AUD / "phase28_router_primary_metrics.json"),
    ("router_membership_barrier", AUD / "phase28_router_membership_barrier.json"),
    ("outcome_opening", AUD / "phase28_outcome_opening.json"),
    ("f1_refiner_level_comparison", AUD / "phase28_f1_refiner_level_comparison.json"),
    ("f1_integrated_secondary", AUD / "phase28_f1_integrated_secondary.json"),
    ("f1_pipeline_validation", AUD / "phase28_f1_pipeline_validation.json"),
    ("f1_integrated_per_sample_csv", TAB / "phase28_f1_integrated_per_sample.csv"),
    ("f1_refiner_level_paired_csv", TAB / "phase28_f1_refiner_level_paired.csv"),
    ("execution_statistics", AUD / "phase28_execution_statistics.json"),
    ("negative_result_acceptance", AUD / "phase28_negative_result_acceptance.json"),
    ("training_run_registry_csv", TAB / "phase28_training_run_registry.csv"),
    ("ablation_matrix_13arm_csv", TAB / "phase28_ablation_matrix_13arm.csv"),
    ("compute_accounting_table", TAB / "phase28_table_09_compute_accounting.csv"),
    ("execution_counts_table", TAB / "phase28_table_10_execution_counts.csv"),
]

TABLES = [(f"table_{i:02d}", TAB / f"phase28_table_{i:02d}_{n}") for i, n in [
    (1, "arm_definitions.csv"), (2, "arm_primary_metrics.csv"),
    (3, "router_variant_vs_full.csv"), (4, "router_membership_overlap.csv"),
    (5, "f1_refiner_level_paired.csv"), (6, "f1_integrated_secondary.csv"),
    (7, "matched_paired_contrasts.csv"), (8, "bootstrap_statistics.csv"),
    (9, "compute_accounting.csv"), (10, "execution_counts.csv")]]

FIGURES = [(p.stem, p) for p in sorted(FIG.glob("p28_fig*.png"))]

MEMBERSHIPS = [(f"membership_{v}", D28 / f"phase28_router_{v}_membership_K1239.csv")
               for v in ("R1", "R2", "R3")]

OOF_TABLES = [(f"oof_scores_{v}", D28 / f"phase28_router_{v}_oof_scores.csv")
              for v in ("R1", "R2", "R3")]

F1_ARTIFACTS = [
    ("f1_safety_fold_mapping", AUD / "phase28_f1_oof_contract_v1_2.json"),
    ("f1_membership_rule", AUD / "phase28_f1_membership_rule_v1_2.json"),
    ("f1_post_safety_rule", AUD / "phase28_f1_post_safety_rule_v1_2.json"),
    ("f1_input_contract", AUD / "phase28_f1_input_contract_v1_2.json"),
    ("f1_training_protocol_binding", AUD / "phase28_f1_training_protocol_binding_v1_2.json"),
]
for k in range(3):
    F1_ARTIFACTS.append((f"f1_fold{k}_refined_crop_index", F1C / f"fold{k}_refined_crop_index.csv"))


def sha(p: Path):
    p = Path(p)
    if not p.exists():
        return None
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def rel(p: Path) -> str:
    return str(Path(p).relative_to(ROOT)).replace("\\", "/")


def collect() -> dict:
    """Return the full scientific immutability binding map."""
    out = {"single_artifacts": {}, "checkpoints": {}, "histories": {},
           "router_oof_tables": {}, "memberships": {}, "f1_artifacts": {},
           "tables": {}, "figures": {}}
    for name, p in SINGLE:
        out["single_artifacts"][name] = {"path": rel(p), "sha256": sha(p),
                                          "exists": Path(p).exists()}
    for v, root in RCK.items():
        for k in range(5):
            key = f"{v}_fold{k}"
            out["checkpoints"][key] = {"path": rel(root / f"fold{k}" / "best.pt"),
                                       "sha256": sha(root / f"fold{k}" / "best.pt")}
            out["histories"][key] = {"path": rel(root / f"fold{k}" / "history.csv"),
                                     "sha256": sha(root / f"fold{k}" / "history.csv")}
    for k in range(3):
        key = f"F1_fold{k}"
        out["checkpoints"][key] = {"path": rel(F1_CK / f"fold{k}" / "best.pt"),
                                   "sha256": sha(F1_CK / f"fold{k}" / "best.pt")}
        out["histories"][key] = {"path": rel(F1_EXP / f"fold{k}" / "history.csv"),
                                 "sha256": sha(F1_EXP / f"fold{k}" / "history.csv")}
    for name, p in OOF_TABLES:
        out["router_oof_tables"][name] = {"path": rel(p), "sha256": sha(p)}
    for name, p in MEMBERSHIPS:
        out["memberships"][name] = {"path": rel(p), "sha256": sha(p)}
    for name, p in F1_ARTIFACTS:
        out["f1_artifacts"][name] = {"path": rel(p), "sha256": sha(p)}
    for name, p in TABLES:
        out["tables"][name] = {"path": rel(p), "sha256": sha(p)}
    for name, p in FIGURES:
        out["figures"][name] = {"path": rel(p), "sha256": sha(p)}
    return out


def counts_of(b: dict) -> dict:
    return {
        "n_single_artifacts": len(b["single_artifacts"]),
        "n_checkpoints": len(b["checkpoints"]),
        "n_histories": len(b["histories"]),
        "n_router_oof_tables": len(b["router_oof_tables"]),
        "n_memberships": len(b["memberships"]),
        "n_f1_artifacts": len(b["f1_artifacts"]),
        "n_tables": len(b["tables"]),
        "n_figures": len(b["figures"]),
    }


def compare(a: dict, b: dict) -> dict:
    """Return drift report: entries whose sha differs or that vanished."""
    drift = []
    for section in a:
        for name, rec in a[section].items():
            b_rec = b.get(section, {}).get(name)
            if b_rec is None:
                drift.append({"section": section, "name": name,
                              "reason": "MISSING_IN_LATER", "pre": rec.get("sha256")})
            elif b_rec.get("sha256") != rec.get("sha256"):
                drift.append({"section": section, "name": name, "reason": "SHA_CHANGED",
                              "pre": rec.get("sha256"), "post": b_rec.get("sha256")})
    return {"n_drift": len(drift), "drift": drift, "no_drift": len(drift) == 0}


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "pre"
    b = collect()
    counts = counts_of(b)
    if mode == "pre":
        obj = {
            "artifact": "phase28_notebook_repair_scientific_immutability_precheck",
            "phase": 28,
            "classification": "PHASE28_NOTEBOOK_REPAIR_SCIENTIFIC_IMMUTABILITY_PRECHECK",
            "stage": "PRE_REPAIR",
            "counts": counts,
            "binding": b,
            "all_present": all(rec["exists"] is not False
                               for rec in b["single_artifacts"].values()),
            "all_pass": True,
        }
        AUD.mkdir(parents=True, exist_ok=True)
        with open(PRE_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print("precheck written:", counts)
        missing = [f"{s}/{n}" for s in b for n, r in b[s].items()
                   if r.get("sha256") is None]
        print("missing/None shas:", missing if missing else "none")
        return 1 if missing else 0
    else:
        pre = json.load(open(PRE_PATH, encoding="utf-8"))
        cmp = compare(pre["binding"], b)
        obj = {
            "artifact": "phase28_notebook_repair_scientific_immutability_postcheck",
            "phase": 28,
            "classification": "PHASE28_NOTEBOOK_REPAIR_SCIENTIFIC_IMMUTABILITY_POSTCHECK",
            "stage": "POST_REPAIR",
            "counts": counts,
            "binding": b,
            "drift_report": cmp,
            "scientific_artifact_drift": cmp["n_drift"],
            "all_predecessor_shas_unchanged": cmp["no_drift"],
            "checkpoints_unchanged": _section_unchanged(pre, b, "checkpoints"),
            "histories_unchanged": _section_unchanged(pre, b, "histories"),
            "oof_predictions_unchanged": _section_unchanged(pre, b, "router_oof_tables"),
            "memberships_unchanged": _section_unchanged(pre, b, "memberships"),
            "f1_outputs_unchanged": _section_unchanged(pre, b, "f1_artifacts"),
            "tables_unchanged": _section_unchanged(pre, b, "tables"),
            "figures_unchanged": _section_unchanged(pre, b, "figures"),
            "base_final_freeze_unchanged": _one_unchanged(pre, b, "base_final_freeze"),
            "all_pass": cmp["no_drift"],
        }
        with open(POST_PATH, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write("\n")
        print("postcheck written | n_drift:", cmp["n_drift"])
        if cmp["n_drift"]:
            for d in cmp["drift"][:20]:
                print("  DRIFT:", d)
        return 0 if cmp["no_drift"] else 1


def _section_unchanged(pre, post, section) -> bool:
    a, b = pre["binding"][section], post[section]
    if set(a) != set(b):
        return False
    return all(a[k].get("sha256") == b[k].get("sha256") for k in a)


def _one_unchanged(pre, post, name) -> bool:
    a = pre["binding"]["single_artifacts"][name]["sha256"]
    b = post["single_artifacts"][name]["sha256"]
    return a == b


if __name__ == "__main__":
    raise SystemExit(main())
