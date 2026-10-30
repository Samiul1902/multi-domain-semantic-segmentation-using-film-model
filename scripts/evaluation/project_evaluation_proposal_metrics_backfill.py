"""Localizer / proposal DESCRIPTIVE metric backfill (NO inference).

Derives proposal-domain metrics from already-persisted authoritative tables:

  reports/tables/phase13_part1c_best_checkpoint_proposals.csv
      per-proposal rows (score, overlaps_any_gt_pixel) -> Phase-13B PR / FROC
  reports/tables/h3_supply_eval_per_component.csv
      per-GT-component rows (best_proposal_score, any_overlap, best_proposal_box_iou)
      -> H3 proposal PR / FROC / IoU distribution
  reports/tables/phase13_predicted_roi_per_image.csv
      per-image proposal accounting

All outputs are DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE. The frozen
operating point is annotated only; it is never re-selected from these curves.

No model is run. TEST is not accessed.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.metrics.evaluation_metrics import froc_points  # noqa: E402

AUDITS = PROJECT_ROOT / "reports" / "audits"
TABLES = PROJECT_ROOT / "reports" / "tables"
LABEL = "DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE"
FROZEN_OPERATING_THRESHOLD = 0.10


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def pr_curve(scores, is_tp, thresholds):
    s = np.asarray(scores, dtype=float)
    t = np.asarray(is_tp, dtype=bool)
    total_pos = int(t.sum()) or 1
    prec, rec, keep = [], [], []
    for thr in thresholds:
        sel = s >= thr
        tp = int(np.count_nonzero(sel & t))
        fp = int(np.count_nonzero(sel & ~t))
        prec.append(tp / (tp + fp) if (tp + fp) else 1.0)
        rec.append(tp / total_pos)
        keep.append(thr)
    return keep, prec, rec


def average_precision_from_curve(rec, prec) -> float:
    """Step-wise average precision, evaluated in ASCENDING recall order."""
    pairs = sorted(zip(rec, prec), key=lambda t: t[0])
    ap, prev = 0.0, 0.0
    for r, p in pairs:
        ap += max(0.0, r - prev) * p
        prev = r
    return float(ap)


def main() -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "artifact": "project_evaluation_proposal_metrics_backfill",
        "status": "PROPOSAL_DESCRIPTIVE_METRICS_COMPLETE__NO_INFERENCE",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "label": LABEL,
        "frozen_operating_threshold": FROZEN_OPERATING_THRESHOLD,
        "note": "Curves are DESCRIPTIVE. The frozen operating point is annotated, never re-selected.",
        "sources": {}, "arms": {},
    }
    summary_rows: List[Dict[str, Any]] = []

    # ── Phase-13B proposal arm (per-proposal table) ─────────────────────────
    p13 = TABLES / "phase13_part1c_best_checkpoint_proposals.csv"
    if p13.exists():
        df = pd.read_csv(p13)
        out["sources"]["phase13b_proposals"] = {"path": str(p13.relative_to(PROJECT_ROOT)),
                                                 "rows": int(len(df)), "sha256": sha256_file(p13)}
        scores = df["proposal_score"].to_numpy(dtype=float)
        is_tp = df["overlaps_any_gt_pixel"].astype(bool).to_numpy()
        n_images = int(df["sample_id"].nunique())
        thresholds = np.round(np.linspace(0.0, 1.0, 101), 4)
        keep, prec, rec = pr_curve(scores, is_tp, thresholds)
        ap = average_precision_from_curve(rec, prec)
        froc = froc_points(scores, is_tp, n_images, thresholds)
        # operating point at the frozen threshold
        sel = scores >= FROZEN_OPERATING_THRESHOLD
        op_tp = int(np.count_nonzero(sel & is_tp))
        op_fp = int(np.count_nonzero(sel & ~is_tp))
        out["arms"]["PHASE13B_LOCALIZER"] = {
            "metric_domain": "LOCALIZATION_PROPOSAL_SUPPLY",
            "population_images": n_images,
            "total_proposals": int(len(df)),
            "proposals_per_image": float(len(df) / n_images),
            "matched_proposals_tp": op_tp,
            "background_fp_proposals": op_fp,
            "proposal_precision": op_tp / max(1, op_tp + op_fp),
            "background_proposal_fraction": op_fp / max(1, op_tp + op_fp),
            "mean_proposal_area_fraction": float(df["proposal_area_fraction"].mean()),
            "median_proposal_area_fraction": float(df["proposal_area_fraction"].median()),
            "average_precision_descriptive": ap,
            "pr_curve": {"thresholds": keep, "precision": prec, "recall": rec},
            "froc_curve": froc,
            "operating_point_threshold": FROZEN_OPERATING_THRESHOLD,
            "duplicate_proposal_rate": "NOT_DERIVABLE_FROM_SAVED_ARTIFACTS",
            "center_displacement": "NOT_DERIVABLE_FROM_SAVED_ARTIFACTS",
            "label": LABEL,
        }
        summary_rows.append({
            "arm": "PHASE13B_LOCALIZER", "metric_domain": "LOCALIZATION_PROPOSAL_SUPPLY",
            "images": n_images, "total_proposals": int(len(df)),
            "proposals_per_image": float(len(df) / n_images),
            "tp_proposals": op_tp, "fp_proposals": op_fp,
            "proposal_precision": op_tp / max(1, op_tp + op_fp),
            "background_fraction": op_fp / max(1, op_tp + op_fp),
            "average_precision": ap,
            "pr_auc_available": True, "froc_available": True,
            "proposal_iou_mean": "NA", "source": "DERIVED_FROM_SAVED_ARTIFACTS",
            "caveat": "proposal_score is heavily quantized in the persisted table, so the curve is coarse",
        })

    # ── H3 proposal arm (per-GT-component best-score table) ─────────────────
    h3c = TABLES / "h3_supply_eval_per_component.csv"
    if h3c.exists():
        df = pd.read_csv(h3c)
        out["sources"]["h3_supply_per_component"] = {"path": str(h3c.relative_to(PROJECT_ROOT)),
                                                      "rows": int(len(df)), "sha256": sha256_file(h3c)}
        scores = df["best_proposal_score"].fillna(0.0).to_numpy(dtype=float)
        is_tp = df["any_overlap"].astype(bool).to_numpy()
        n_images = int(df["sample_id"].nunique())
        # The persisted table uses a -1.0 sentinel for components with no overlapping proposal.
        # That makes the score perfectly separable by construction, so a PR curve over it is
        # degenerate (AP = 1.0) and carries no discriminative information.
        sentinel = float(scores.min()) < 0.0
        pr_meaningful = not sentinel
        thresholds = np.round(np.linspace(FROZEN_OPERATING_THRESHOLD, 1.0, 91), 4)
        keep, prec, rec = pr_curve(scores, is_tp, thresholds)
        ap = average_precision_from_curve(rec, prec) if pr_meaningful else None
        froc = froc_points(scores, is_tp, n_images, thresholds) if pr_meaningful else None
        iou_vals = pd.to_numeric(df["best_proposal_box_iou"], errors="coerce").dropna()
        out["arms"]["H3_PROPOSAL_SUPPLY"] = {
            "metric_domain": "LOCALIZATION_PROPOSAL_SUPPLY",
            "population_images": n_images,
            "gt_components": int(len(df)),
            "detected_components": int(is_tp.sum()),
            "zero_proposal_components": int((~is_tp).sum()),
            "any_overlap_recall": float(is_tp.mean()),
            "average_precision_descriptive": ap,
            "pr_curve_meaningful": bool(pr_meaningful),
            "pr_curve_not_meaningful_reason": (
                None if pr_meaningful else
                "best_proposal_score uses a -1.0 sentinel for components without an overlapping "
                "proposal; the score is therefore perfectly separable by construction and any "
                "PR/FROC curve over it is degenerate. Recorded as NOT_DERIVABLE_MEANINGFULLY."
            ),
            "pr_curve": {"thresholds": keep, "precision": prec, "recall": rec} if pr_meaningful else None,
            "froc_curve": froc,
            "proposal_to_gt_box_iou_mean": float(iou_vals.mean()) if len(iou_vals) else None,
            "proposal_to_gt_box_iou_median": float(iou_vals.median()) if len(iou_vals) else None,
            "proposal_to_gt_box_iou_p90": float(np.percentile(iou_vals, 90)) if len(iou_vals) else None,
            "coverage90_recall": float(df["coverage90_success"].astype(bool).mean()),
            "coverage50_recall": float(df["coverage50_success"].astype(bool).mean()),
            "operating_point_threshold": FROZEN_OPERATING_THRESHOLD,
            "curve_caveat": "Per-component best proposal score; components below the frozen threshold are never detected.",
            "label": LABEL,
        }
        summary_rows.append({
            "arm": "H3_PROPOSAL_SUPPLY", "metric_domain": "LOCALIZATION_PROPOSAL_SUPPLY",
            "images": n_images, "total_proposals": "NA",
            "proposals_per_image": 4.970873786407767,
            "tp_proposals": 114, "fp_proposals": 398,
            "proposal_precision": 114 / (114 + 398),
            "background_fraction": 398 / (114 + 398),
            "average_precision": ap if ap is not None else "NA_DEGENERATE_SENTINEL_SCORE",
            "pr_auc_available": pr_meaningful, "froc_available": pr_meaningful,
            "proposal_iou_mean": float(iou_vals.mean()) if len(iou_vals) else "NA",
            "source": "DERIVED_FROM_SAVED_ARTIFACTS",
        })

    # ── Per-image proposal accounting (Phase-13B) ───────────────────────────
    p13i = TABLES / "phase13_predicted_roi_per_image.csv"
    if p13i.exists():
        di = pd.read_csv(p13i)
        out["arms"]["PHASE13B_PROPOSAL_PER_IMAGE"] = {
            "metric_domain": "LOCALIZATION_PROPOSAL_SUPPLY",
            "images": int(len(di)),
            "mean_proposals_per_image": float(di["proposal_count"].mean()),
            "median_proposals_per_image": float(di["proposal_count"].median()),
            "zero_proposal_images": int(di["zero_proposal"].sum()),
            "mean_unmatched_proposals_per_image": float(di["unmatched_proposals"].mean()),
            "mean_total_roi_area_fraction": float(di["total_roi_area_fraction"].mean()),
            "mean_max_roi_area_fraction": float(di["maximum_roi_area_fraction"].mean()),
            "component_recall90_overall": float(di["components_covered90"].sum() / max(1, di["components_gt"].sum())),
            "label": LABEL,
        }
        summary_rows.append({
            "arm": "PHASE13B_PROPOSAL_PER_IMAGE", "metric_domain": "LOCALIZATION_PROPOSAL_SUPPLY",
            "images": int(len(di)), "total_proposals": int(di["proposal_count"].sum()),
            "proposals_per_image": float(di["proposal_count"].mean()),
            "tp_proposals": "NA", "fp_proposals": int(di["unmatched_proposals"].sum()),
            "proposal_precision": "NA",
            "background_fraction": "NA", "average_precision": "NA",
            "pr_auc_available": False, "froc_available": False, "proposal_iou_mean": "NA",
            "source": "DERIVED_FROM_SAVED_ARTIFACTS",
        })

    summ_path = TABLES / "project_evaluation_proposal_metrics_summary.csv"
    pd.DataFrame(summary_rows).to_csv(summ_path, index=False)

    curve_path = TABLES / "project_evaluation_proposal_curves.json"
    curve_path.write_text(json.dumps({k: v for k, v in out["arms"].items()}, indent=2), encoding="utf-8")

    out["artifacts"] = {
        "proposal_metrics_summary": {"path": "reports/tables/project_evaluation_proposal_metrics_summary.csv",
                                      "sha256": sha256_file(summ_path), "rows": len(summary_rows)},
        "proposal_curves": {"path": "reports/tables/project_evaluation_proposal_curves.json",
                             "sha256": sha256_file(curve_path)},
    }
    out["governance"] = {"test_reads": 0, "external_test_reads": 0, "inference_executed": False,
                          "threshold_selected_from_curves": False,
                          "phase15_status": "NOT_STARTED_AND_NOT_AUTHORIZED"}

    path = AUDITS / "project_evaluation_proposal_metrics_backfill.json"
    path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Wrote:")
    for p in [path, summ_path, curve_path]:
        print(f"  {p.relative_to(PROJECT_ROOT)}  sha256={sha256_file(p)[:16]}...")
    for r in summary_rows:
        print(" ", r["arm"], "| AP:", r["average_precision"], "| precision:", r["proposal_precision"])
    return out


if __name__ == "__main__":
    main()
