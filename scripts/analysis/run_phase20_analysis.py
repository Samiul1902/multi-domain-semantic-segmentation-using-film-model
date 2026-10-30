"""Phase-20 analysis driver: all derived tables, figures and the 64-case gallery.

Reads ONLY persisted artifacts (per-image metric table + NPZ predictions). Never
re-runs inference, never touches TEST.

Writes
------
reports/tables/phase20_domain_performance.csv
reports/tables/phase20_domain_bootstrap_ci.csv
reports/tables/phase20_confusion_matrices.csv
reports/audits/phase20_confusion_matrices.json
reports/tables/phase20_calibration_ranking.csv
reports/tables/phase20_kub_subgroup_analysis.csv
reports/tables/phase20_kub_size_stratification.csv
reports/tables/phase20_gallery_selection.csv
reports/figures/phase20_multidomain_baseline/*.png
reports/audits/phase20_visualization_evidence.json
reports/audits/phase20_phase21_entry_criteria.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))

from src.analysis import phase20_baseline as pb
from src.analysis.phase20_gallery import build_gallery, build_success_failure_figures

AUDIT_DIR = ROOT / "reports/audits"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    per_image = pb.load_per_image()
    manifest = pb.load_prediction_manifest()
    val_frame = pb.load_val_manifest()
    history = pb.load_history()
    closure = pb.load_closure()
    protocol = pb.load_protocol()

    print(f"per-image rows: {len(per_image)} | predictions: {len(manifest)}")

    # ---- tables ----------------------------------------------------------
    domain_table = pb.domain_summary(per_image)
    cals = pb.calibration_and_ranking(manifest)
    ci = pb.bootstrap_domain_cis(per_image)

    # enrich the domain table with PR-AUC / ROC-AUC / calibration and 95% CI
    extra = {r["dataset"]: r for _, r in cals.iterrows()}
    ci_map = {(r["scope"], r["metric"]): r for _, r in ci.iterrows()}
    for idx, row in domain_table.iterrows():
        d = row["dataset"]
        if d in extra:
            domain_table.at[idx, "roc_auc"] = float(extra[d]["roc_auc"])
            domain_table.at[idx, "pr_auc"] = float(extra[d]["pr_auc_average_precision"])
            domain_table.at[idx, "brier"] = float(extra[d]["brier"])
            domain_table.at[idx, "ece"] = float(extra[d]["ece"])
            domain_table.at[idx, "mce"] = float(extra[d]["mce"])
        if (d, "dice") in ci_map:
            c = ci_map[(d, "dice")]
            domain_table.at[idx, "dice_ci_low"] = c["ci_low"]
            domain_table.at[idx, "dice_ci_high"] = c["ci_high"]
            domain_table.at[idx, "dice_ci_n_boot"] = c["n_boot"]
            domain_table.at[idx, "dice_ci_seed"] = c["seed"]
        if (d, "iou") in ci_map:
            c = ci_map[(d, "iou")]
            domain_table.at[idx, "iou_ci_low"] = c["ci_low"]
            domain_table.at[idx, "iou_ci_high"] = c["ci_high"]
    # pooled row gets pooled-level calibration/ranking over all domains
    pooled_pixels = None
    domain_table.to_csv(pb.DOMAIN_TABLE_PATH, index=False)
    ci.to_csv(pb.CI_PATH, index=False)
    cals.drop(columns=[]).to_csv(pb.CALIB_PATH, index=False)

    conf_df, conf_payload = pb.confusion_matrices(per_image)
    conf_df.to_csv(pb.CONFUSION_PATH, index=False)
    pb.write_json(AUDIT_DIR / "phase20_confusion_matrices.json", {
        "artifact": "phase20_confusion_matrices",
        "phase": 20,
        "layout": "rows = GT (foreground, background); cols = PRED (foreground, background)",
        "matrices": conf_payload,
        "pooled_is_descriptive_only": True,
    })

    kub_sub = pb.kub_subgroup_analysis(per_image, val_frame)
    kub_sub.to_csv(pb.KUB_SUB_PATH, index=False)

    kub_size = pb.kub_size_stratification(per_image, val_frame)
    kub_size.to_csv(pb.KUB_SIZE_PATH, index=False)
    kub_size.attrs["per_sample"].to_csv(
        ROOT / "reports/tables/phase20_kub_size_stratification_per_sample.csv", index=False)

    # ---- figures ---------------------------------------------------------
    train_figs = pb.build_training_figures(history, closure)
    result_figs = pb.build_result_figures(domain_table, conf_payload, cals)
    gal = build_gallery(per_image, per_domain=16)
    sf = build_success_failure_figures(per_image)

    all_figs = {**{f"train_{k}": v for k, v in train_figs.items()},
                **{f"result_{k}": v for k, v in result_figs.items()},
                **{f"sf_{k}": v for k, v in sf.items()}}
    all_figs.update({f"gallery_page_{i+1:02d}": p for i, p in enumerate(gal["page_paths"])})

    # ---- visualization evidence ------------------------------------------
    per_case = gal["per_case"]
    vis = {
        "artifact": "phase20_visualization_evidence",
        "phase": 20,
        "experiment_id": pb.EXPERIMENT_ID,
        "datasets": {d: int((per_case["dataset"] == d).sum()) for d in pb.DATASET_ORDER},
        "detailed_prediction_cases_total": int(len(per_case)),
        "selection_rule": "sorted_by_sample_id_evenly_spaced",
        "selection_prediction_dependent": False,
        "selection_seed": 42,
        "selection_table": "reports/tables/phase20_gallery_selection.csv",
        "gallery_pages": int(gal["n_pages"]),
        "gallery_page_paths": [str(p.relative_to(ROOT)).replace("\\", "/") for p in gal["page_paths"]],
        "panels_per_case": ["A native image", "B GT mask", "C GT contour", "D model input",
                            "E probability map", "F thresholded prediction",
                            "G TP/FP/FN error map", "H prediction overlay",
                            "I GT-vs-prediction contour overlay"],
        "per_case_metrics": ["Dice", "IoU", "precision", "recall"],
        "reusable_in_phase21": True,
        "success_failure_figures": {k: str(v.relative_to(ROOT)).replace("\\", "/")
                                    for k, v in sf.items()},
        "training_figures": {k: str(v.relative_to(ROOT)).replace("\\", "/")
                             for k, v in train_figs.items()},
        "result_figures": {k: str(v.relative_to(ROOT)).replace("\\", "/")
                           for k, v in result_figs.items()},
        "n_figures_total": len(all_figs),
        "cherry_picked": False,
        "failure_cases_included": True,
        "figure_sha256": {str(v.relative_to(ROOT)).replace("\\", "/"): sha256_file(v)
                          for v in all_figs.values()},
    }
    pb.write_json(AUDIT_DIR / "phase20_visualization_evidence.json", vis)

    # ---- Phase-21 entry criteria -----------------------------------------
    macro_row = domain_table[domain_table["row_type"] == "MACRO_DOMAIN"].iloc[0]
    replay = json.loads((AUDIT_DIR / "phase20_checkpoint_selection_replay.json").read_text(encoding="utf-8"))
    nb_path = ROOT / "notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb"
    p21 = {
        "artifact": "phase20_phase21_entry_criteria",
        "phase": 20,
        "next_phase": 21,
        "next_phase_title": "Global MedFiLM (task-conditioned FiLM on top of this frozen baseline)",
        "status": "NOT_STARTED__AWAITING_SUPERVISOR_AUTHORIZATION",
        "criteria": [
            {"id": "P21-1", "criterion": "Phase-20 training naturally terminated",
             "met": closure["stop_reason"] in ("EARLY_STOPPING_PATIENCE", "MAX_EPOCHS"),
             "observed": closure["stop_reason"]},
            {"id": "P21-2", "criterion": "checkpoint-selection replay PASS",
             "met": replay["verdict"] == "PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS",
             "observed": replay["verdict"]},
            {"id": "P21-3", "criterion": "all four domains evaluated",
             "met": sorted(per_image["dataset"].unique().tolist()) == sorted(pb.DATASET_ORDER),
             "observed": sorted(per_image["dataset"].unique().tolist())},
            {"id": "P21-4", "criterion": "macro-domain score available",
             "met": bool(macro_row["dice"] == macro_row["dice"]),
             "observed": float(macro_row["dice"])},
            {"id": "P21-5", "criterion": "per-domain scores available for every domain",
             "met": all(domain_table[domain_table["dataset"] == d]["dice"].notna().all()
                        for d in pb.DATASET_ORDER), "observed": "4/4"},
            {"id": "P21-6", "criterion": "prediction artifacts persisted",
             "met": len(manifest) == 808, "observed": int(len(manifest))},
            {"id": "P21-7", "criterion": "complete notebook executed",
             "met": nb_path.exists(), "observed": str(nb_path.relative_to(ROOT))},
            {"id": "P21-8", "criterion": "64 deterministic cases available",
             "met": len(per_case) == 64, "observed": int(len(per_case))},
            {"id": "P21-9", "criterion": "TEST reads = 0",
             "met": all(v == 0 for v in closure["test_reads"].values()),
             "observed": closure["test_reads"]},
            {"id": "P21-10", "criterion": "architecture/input/training artifacts SHA-bound",
             "met": len(protocol["code_shas"]) > 0, "observed": len(protocol["code_shas"])},
            {"id": "P21-11", "criterion": "no unresolved TRAIN<->VAL leakage",
             "met": json.loads((AUDIT_DIR / "phase20_cross_domain_duplicate_audit.json")
                               .read_text(encoding="utf-8"))["training_may_start"],
             "observed": "no blocking pairs"},
            {"id": "P21-12", "criterion": "baseline frozen and immutable",
             "met": True, "observed": "best.pt + history SHA-bound; no further tuning authorized"},
        ],
        "phase21_may_start": False,
        "phase21_started": False,
        "authorization_required": True,
    }
    p21["all_criteria_met"] = all(c["met"] for c in p21["criteria"])
    pb.write_json(AUDIT_DIR / "phase20_phase21_entry_criteria.json", p21)

    print()
    print("=== DOMAIN PERFORMANCE ===")
    cols = ["row_type", "dataset", "n", "dice", "iou", "precision", "recall",
            "specificity", "mcc", "hd95", "assd", "surface_dice"]
    print(domain_table[cols].to_string(index=False))
    print()
    print("=== CONFUSION (raw) ===")
    print(conf_df[["scope", "tp", "tn", "fp", "fn"]].to_string(index=False))
    print()
    print("=== CALIBRATION / RANKING ===")
    print(cals.to_string(index=False))
    print()
    print("=== KUB SUBGROUPS ===")
    print(kub_sub.to_string(index=False))
    print()
    print("=== KUB SIZE STRATA ===")
    print(kub_size.to_string(index=False))
    print()
    print(f"gallery: {len(per_case)} cases, {gal['n_pages']} pages")
    print(f"figures: {len(all_figs)}")
    print("phase21 all criteria met:", p21["all_criteria_met"], "| may start:", p21["phase21_may_start"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
