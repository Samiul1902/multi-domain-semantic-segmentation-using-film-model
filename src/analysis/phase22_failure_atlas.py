"""Phase 22 — global failure atlas from PERSISTED predictions (no new inference).

Every number here is derived from artifacts already on disk:

  * ``reports/tables/phase21_per_image_val_metrics.csv``  (808 VAL rows, Global MedFiLM)
  * ``reports/predictions/<experiment>/val/**/*.npz``     (per-sample prob/pred/gt)

No training. No inference. No TEST.

The atlas answers, per domain and overall: WHERE does the frozen Global MedFiLM
reference fail, HOW does it fail, and WHAT KIND of failure is it?

Failure taxonomy (mutually exclusive, assigned in this order):

  EMPTY_CASE_BOTH      GT empty and prediction empty   -> not a failure
  EMPTY_CASE_FALSE_POS GT empty, prediction non-empty  -> hallucination
  EMPTY_CASE_MISSED    GT non-empty, prediction empty  -> total miss
  OVER_SEGMENTATION    recall >= 0.80 and precision < 0.60
  UNDER_SEGMENTATION   precision >= 0.80 and recall < 0.60
  MIXED_BOUNDARY       both precision and recall < 0.80
  GOOD                 otherwise (precision >= 0.60 and recall >= 0.60)

The thresholds 0.80 / 0.60 are DECLARED HERE, prospectively, and are policy
choices for describing failure shape, not scientific constants. They are not used
for model selection and are not tuned on any outcome.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.analysis import phase22_common as C  # noqa: E402
from src.metrics.segmentation import hd95  # noqa: E402

OUT_AUDIT = C.AUDITS / "phase22_global_failure_atlas.json"
OUT_TABLE = C.TABLES / "phase22_global_failure_atlas.csv"
OUT_DOMAIN = C.TABLES / "phase22_failure_by_domain.csv"
OUT_TAXONOMY = C.TABLES / "phase22_failure_taxonomy.csv"
OUT_WORST = C.TABLES / "phase22_worst_cases_per_domain.csv"

GOOD_PRECISION = 0.60
GOOD_RECALL = 0.60
IMBALANCE_PRECISION = 0.80
IMBALANCE_RECALL = 0.80

TAXONOMY_ORDER = [
    "EMPTY_CASE_BOTH", "EMPTY_CASE_FALSE_POS", "EMPTY_CASE_MISSED",
    "OVER_SEGMENTATION", "UNDER_SEGMENTATION", "MIXED_BOUNDARY", "GOOD",
]


def classify(precision: float, recall: float, gt_empty: bool, pred_empty: bool) -> str:
    if gt_empty and pred_empty:
        return "EMPTY_CASE_BOTH"
    if gt_empty and not pred_empty:
        return "EMPTY_CASE_FALSE_POS"
    if (not gt_empty) and pred_empty:
        return "EMPTY_CASE_MISSED"
    p, r = float(precision), float(recall)
    if r >= IMBALANCE_RECALL and p < GOOD_PRECISION:
        return "OVER_SEGMENTATION"
    if p >= IMBALANCE_PRECISION and r < GOOD_RECALL:
        return "UNDER_SEGMENTATION"
    if p < GOOD_PRECISION and r < GOOD_RECALL:
        return "MIXED_BOUNDARY"
    return "GOOD"


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase-22 global failure atlas.")
    ap.add_argument("--hd95-sample", type=int, default=200,
                    help="Boundary metrics are computed on this many worst-Dice "
                         "cases per domain plus a fixed random sample (deterministic).")
    args = ap.parse_args()

    C.verify_no_test_access()
    src = C.TABLES / "phase21_per_image_val_metrics.csv"
    df = pd.read_csv(src)
    if len(df) != 808:
        raise RuntimeError(f"expected 808 VAL rows, found {len(df)}")

    manifest = pd.read_csv(C.TABLES / "phase21_prediction_manifest.csv")
    npz_of = dict(zip(manifest["sample_id"], manifest["npz_path"]))

    df["failure_mode"] = [
        classify(p, r, bool(ge), bool(pe))
        for p, r, ge, pe in zip(df["precision"], df["recall"],
                                df["gt_empty"], df["pred_empty"])
    ]
    df["foreground_pixel_error"] = (df["pred_foreground_pixels"]
                                    - df["gt_foreground_pixels"])
    df["abs_foreground_pixel_error"] = df["foreground_pixel_error"].abs()

    df.to_csv(OUT_TABLE, index=False)

    # ---- per-domain summary --------------------------------------------- #
    per_domain = (df.groupby("dataset")
                  .agg(n=("dice", "size"),
                       mean_dice=("dice", "mean"), median_dice=("dice", "median"),
                       sd_dice=("dice", "std"),
                       p05_dice=("dice", lambda s: s.quantile(0.05)),
                       p25_dice=("dice", lambda s: s.quantile(0.25)),
                       min_dice=("dice", "min"),
                       mean_iou=("iou", "mean"),
                       mean_precision=("precision", "mean"),
                       mean_recall=("recall", "mean"),
                       n_empty_case=("empty_case", lambda s: int((s != "both_nonempty").sum())),
                       n_gt_empty=("gt_empty", "sum"),
                       n_pred_empty=("pred_empty", "sum"))
                  .reset_index())
    overall = pd.DataFrame([{
        "dataset": "ALL", "n": int(len(df)),
        "mean_dice": float(df["dice"].mean()),
        "median_dice": float(df["dice"].median()),
        "sd_dice": float(df["dice"].std()),
        "p05_dice": float(df["dice"].quantile(0.05)),
        "p25_dice": float(df["dice"].quantile(0.25)),
        "min_dice": float(df["dice"].min()),
        "mean_iou": float(df["iou"].mean()),
        "mean_precision": float(df["precision"].mean()),
        "mean_recall": float(df["recall"].mean()),
        "n_empty_case": int((df["empty_case"] != "both_nonempty").sum()),
        "n_gt_empty": int(df["gt_empty"].sum()),
        "n_pred_empty": int(df["pred_empty"].sum()),
    }])
    domain_table = pd.concat([per_domain, overall], ignore_index=True)
    domain_table.to_csv(OUT_DOMAIN, index=False)

    # ---- taxonomy --------------------------------------------------------- #
    tax = (df.groupby(["dataset", "failure_mode"]).size()
           .unstack(fill_value=0)
           .reindex(columns=TAXONOMY_ORDER, fill_value=0)
           .reset_index())
    tax_all = df["failure_mode"].value_counts().reindex(TAXONOMY_ORDER, fill_value=0)
    totals = tax[TAXONOMY_ORDER].sum(axis=1)
    for col in TAXONOMY_ORDER:
        tax[f"{col}_pct"] = (tax[col] / totals * 100).round(4)
    tax.to_csv(OUT_TAXONOMY, index=False)

    # ---- worst cases and boundary metrics on a deterministic subset ------- #
    rng = np.random.default_rng(42)
    worst_rows = []
    picks = []
    for name in C.DATASET_ORDER:
        sub = df[df["dataset"] == name].sort_values("dice")
        head = sub.head(args.hd95_sample // 2)
        pool = sub.iloc[args.hd95_sample // 2:]
        tail = pool.sample(n=min(len(pool), args.hd95_sample // 2),
                           random_state=42) if len(pool) else pool
        sel = pd.concat([head, tail]).drop_duplicates(subset=["sample_id"])
        picks.append(sel)
        for i, (_, row) in enumerate(sub.head(10).iterrows(), 1):
            worst_rows.append({
                "dataset": name, "rank_within_domain": i,
                "sample_id": row["sample_id"], "dice": row["dice"],
                "iou": row["iou"], "precision": row["precision"],
                "recall": row["recall"], "failure_mode": row["failure_mode"],
                "gt_foreground_pixels": row["gt_foreground_pixels"],
                "pred_foreground_pixels": row["pred_foreground_pixels"],
                "empty_case": row["empty_case"],
            })
    pd.DataFrame(worst_rows).to_csv(OUT_WORST, index=False)

    sel = pd.concat(picks).drop_duplicates(subset=["sample_id"])
    bd = []
    for row in sel.itertuples(index=False):
        z = np.load(ROOT / npz_of[row.sample_id])
        pred, gt = z["pred"].astype(bool), z["gt"].astype(bool)
        h = hd95(pred, gt)
        bd.append({"sample_id": row.sample_id, "dataset": row.dataset,
                   "dice": float(row.dice), "hd95": h["hd95"],
                   "hd95_valid": bool(h["hd95_valid"]),
                   "invalid_reason": h["invalid_reason"],
                   "selected_as_worst": bool(row.dice <= df[df.dataset == row.dataset]["dice"].nsmallest(10).max())})
    bdf = pd.DataFrame(bd)
    bdf.to_csv(C.TABLES / "phase22_boundary_metrics_subset.csv", index=False)

    bd_summary = {}
    for name in C.DATASET_ORDER:
        s = bdf[(bdf["dataset"] == name) & bdf["hd95_valid"]]["hd95"]
        bd_summary[name] = {
            "n_valid": int(len(s)),
            "mean_hd95": float(s.mean()) if len(s) else float("nan"),
            "median_hd95": float(s.median()) if len(s) else float("nan"),
        }

    payload = {
        "artifact": "phase22_global_failure_atlas",
        "phase": 22,
        "source": "reports/tables/phase21_per_image_val_metrics.csv (808 VAL rows)",
        "new_inference_performed": False,
        "training_jobs_started": 0,
        "n_samples": int(len(df)),
        "taxonomy": {
            "order_of_assignment": TAXONOMY_ORDER,
            "declared_thresholds": {
                "good_precision": GOOD_PRECISION, "good_recall": GOOD_RECALL,
                "imbalance_precision": IMBALANCE_PRECISION,
                "imbalance_recall": IMBALANCE_RECALL,
            },
            "declared_prospectively": True,
            "used_for_model_selection": False,
            "note": ("policy definitions for describing failure shape; they are not "
                     "scientific constants and were not tuned on any outcome"),
        },
        "overall": {
            "mean_dice": float(df["dice"].mean()),
            "median_dice": float(df["dice"].median()),
            "p05_dice": float(df["dice"].quantile(0.05)),
            "min_dice": float(df["dice"].min()),
            "n_dice_below_0p5": int((df["dice"] < 0.5).sum()),
            "n_dice_below_0p7": int((df["dice"] < 0.7).sum()),
            "mean_iou": float(df["iou"].mean()),
            "mean_precision": float(df["precision"].mean()),
            "mean_recall": float(df["recall"].mean()),
            "n_empty_case": int((df["empty_case"] != "both_nonempty").sum()),
            "n_gt_empty": int(df["gt_empty"].sum()),
            "n_pred_empty": int(df["pred_empty"].sum()),
            "total_foreground_pixel_error": int(df["abs_foreground_pixel_error"].sum()),
        },
        "taxonomy_counts": {k: int(v) for k, v in tax_all.items()},
        "taxonomy_pct": {k: round(float(v) / len(df) * 100, 4) for k, v in tax_all.items()},
        "boundary_metrics": {
            "subset_size": int(len(bdf)),
            "selection": ("per domain: 10 worst-Dice cases + a deterministic "
                          "random_state=42 sample of half the remaining budget"),
            "per_domain": bd_summary,
            "note": "HD95 is descriptive on this subset; it is not a full-population mean.",
        },
        "tables": {
            "per_image": "reports/tables/phase22_global_failure_atlas.csv",
            "by_domain": "reports/tables/phase22_failure_by_domain.csv",
            "taxonomy": "reports/tables/phase22_failure_taxonomy.csv",
            "worst_cases": "reports/tables/phase22_worst_cases_per_domain.csv",
            "boundary_subset": "reports/tables/phase22_boundary_metrics_subset.csv",
        },
        "test_reads": 0,
    }
    C.write_json(OUT_AUDIT, payload)

    print(domain_table.to_string(index=False))
    print("\nfailure taxonomy (overall):")
    for k, v in tax_all.items():
        print(f"  {k:24s} {int(v):4d}  ({float(v)/len(df)*100:6.2f}%)")
    print(f"\nWROTE {OUT_AUDIT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
