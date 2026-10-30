"""Build the project-wide metric-governance artifacts.

Emits (all reproducible from this single source of truth):
  reports/audits/project_evaluation_metric_policy.json
  reports/audits/evaluation_empty_mask_policy.json
  reports/audits/project_metric_registry.json
  reports/audits/project_evaluation_metrics_inventory.json
  reports/tables/project_evaluation_metrics_inventory.csv

No inference. No training. No TEST access.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AUDITS = PROJECT_ROOT / "reports" / "audits"
TABLES = PROJECT_ROOT / "reports" / "tables"

DESCRIPTIVE = "DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE"

# ── A. Metric domains (task section 4) ──────────────────────────────────────
DOMAINS = {
    "A": "PIXEL_SEGMENTATION",
    "B": "OBJECT_COMPONENT_DETECTION",
    "C": "LOCALIZATION_PROPOSAL_SUPPLY",
    "D": "BOUNDARY_SURFACE_QUALITY",
    "E": "PROBABILITY_CALIBRATION",
    "F": "TRAINING_OPTIMIZATION",
    "G": "CAUSAL_COUNTERFACTUAL_DIAGNOSTIC",
    "H": "SYSTEM_PIPELINE_PERFORMANCE",
}

# ── B. Confusion-matrix policy (task section 18) ────────────────────────────
CONFUSION_POLICY = {
    "artifact": "project_evaluation_metric_policy",
    "status": "FROZEN_POLICY__DESCRIPTIVE_AUGMENTATION_ALLOWED",
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "governance_principle": (
        "Newly added metrics are DESCRIPTIVE and are NOT promoted into frozen prospective "
        "success/failure gates. Formal H3 adjudication continues to use the previously frozen criteria."
    ),
    "policies": {
        "segmentation": {
            "confusion_matrix": "YES",
            "form": "2x2 pixel confusion matrix (Background / Foreground) in BOTH raw counts and row-normalized form",
            "source_requirement": "actual pixel predictions versus actual GT masks only; never derived from aggregated Dice",
            "recommended_primary": ["dice", "iou", "precision", "recall", "boundary metrics", "PR-based metrics"],
            "explicit_caveat": "accuracy, specificity and ROC-AUC must NOT be presented alone as evidence of segmentation quality under class imbalance",
        },
        "image_level_binary_classification": {
            "confusion_matrix": "YES",
            "form": "standard 2x2 confusion matrix",
        },
        "component_detection": {
            "confusion_matrix": "NO_CONVENTIONAL_TN",
            "form": "TP / FP / FN summary + PR / FROC",
            "reason": "conventional TN is undefined without a defensible negative-unit definition",
        },
        "proposal_localization": {
            "confusion_matrix": "NO_FORCED_TN",
            "form": "matched / unmatched proposal and GT accounting",
        },
        "multi_class_segmentation_future": {
            "confusion_matrix": "YES",
            "form": "CxC confusion matrix + per-class metrics",
        },
    },
    "metric_domain_labels_required": [
        "PIXEL_SEGMENTATION", "PIXEL_SEGMENTATION_POOLED", "COMPONENT_DETECTION",
        "PROPOSAL_COVERAGE", "DOWNSTREAM_COMPONENT_DETECTION", "BOUNDARY_DISTANCE",
        "PROBABILITY_CALIBRATION", "TRAINING_OPTIMIZATION", "SYSTEM_PERFORMANCE",
    ],
    "label_rule": "Never use the same short label (e.g. 'Recall') across domains without explicit qualification.",
    "distance_unit_rule": "No pixel-spacing metadata exists in this repository; boundary distances are reported in PIXELS, never mm.",
}

# ── C. Empty-mask policy (task section 14) ──────────────────────────────────
EMPTY_POLICY = {
    "artifact": "evaluation_empty_mask_policy",
    "status": "FROZEN_POLICY",
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "principle": "Undefined metrics return NaN together with an explicit validity flag. They are NEVER silently zeroed.",
    "cases": {
        "gt_empty_pred_empty": {
            "dice": 1.0, "iou": 1.0, "precision": 1.0, "recall": 1.0, "specificity": 1.0, "npv": 1.0,
            "accuracy": 1.0, "balanced_accuracy": 1.0, "mcc": 1.0, "cohen_kappa": 1.0,
            "hd95": "NaN (invalid: both_empty)", "assd": "NaN (invalid)", "surface_dice": "NaN (invalid)",
            "rationale": "Perfect agreement on an empty foreground; boundary distances are undefined.",
        },
        "gt_empty_pred_nonempty": {
            "dice": 0.0, "iou": 0.0, "precision": 0.0, "recall": "NaN (undefined: no positives)",
            "specificity": 1.0, "npv": "NaN", "accuracy": "NaN", "balanced_accuracy": "NaN",
            "mcc": "NaN", "cohen_kappa": "NaN",
            "hd95": "NaN (invalid)", "assd": "NaN (invalid)", "surface_dice": "NaN (invalid)",
            "rationale": "False-positive-only case.",
        },
        "gt_nonempty_pred_empty": {
            "dice": 0.0, "iou": 0.0, "precision": "NaN (undefined: no predicted positives)",
            "recall": 0.0, "specificity": 1.0, "npv": 0.0, "accuracy": "NaN",
            "balanced_accuracy": "NaN", "mcc": "NaN", "cohen_kappa": "NaN",
            "hd95": "NaN (invalid: empty_prediction)", "assd": "NaN (invalid)", "surface_dice": "NaN (invalid)",
            "rationale": "False-negative-only case; boundary distances require both masks non-empty.",
        },
        "both_nonempty": {"note": "All metrics defined by their standard formulas."},
    },
    "component_detection": {
        "note": "Empty predictions simply yield zero detected components; component recall is 0 and FP components is 0.",
        "tn": "not defined",
    },
    "aggregation_rule": "NaN-valued images are excluded from image-level means but remain visible in the per-image table; pooled pixel metrics always include them via their raw counts.",
}

# ── D. Metric registry (task section 24) ────────────────────────────────────
def _m(name, domain, definition, unit, aggregation, higher_better, required, prospective, descriptive, impl):
    return {
        "name": name, "domain": domain, "definition": definition, "unit": unit,
        "aggregation": aggregation, "empty_mask_policy": "evaluation_empty_mask_policy",
        "higher_is_better": higher_better, "required_artifacts": required,
        "prospective_gate": prospective, "descriptive_only": descriptive,
        "implementation": impl, "version": "1.0.0",
    }


REGISTRY_METRICS: List[Dict[str, Any]] = [
    _m("tp_pixels", "PIXEL_SEGMENTATION", "count of predicted-foreground AND gt-foreground pixels", "pixels", "sum", None, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.binary_confusion_counts"),
    _m("tn_pixels", "PIXEL_SEGMENTATION", "count of predicted-background AND gt-background pixels", "pixels", "sum", None, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.binary_confusion_counts"),
    _m("fp_pixels", "PIXEL_SEGMENTATION", "count of predicted-foreground AND gt-background pixels", "pixels", "sum", None, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.binary_confusion_counts"),
    _m("fn_pixels", "PIXEL_SEGMENTATION", "count of predicted-background AND gt-foreground pixels", "pixels", "sum", None, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.binary_confusion_counts"),
    _m("dice", "PIXEL_SEGMENTATION", "2TP/(2TP+FP+FN), eps 1e-7", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", True, False, "src/metrics/evaluation_metrics.dice"),
    _m("iou", "PIXEL_SEGMENTATION", "TP/(TP+FP+FN), eps 1e-7", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.iou"),
    _m("precision", "PIXEL_SEGMENTATION", "TP/(TP+FP)", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.precision"),
    _m("recall", "PIXEL_SEGMENTATION", "TP/(TP+FN) = sensitivity = TPR", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", True, False, "src/metrics/evaluation_metrics.recall"),
    _m("specificity", "PIXEL_SEGMENTATION", "TN/(TN+FP) = TNR", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.specificity"),
    _m("npv", "PIXEL_SEGMENTATION", "TN/(TN+FN)", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.npv"),
    _m("accuracy", "PIXEL_SEGMENTATION", "(TP+TN)/N", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.accuracy"),
    _m("balanced_accuracy", "PIXEL_SEGMENTATION", "(recall + specificity)/2", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.balanced_accuracy"),
    _m("fpr", "PIXEL_SEGMENTATION", "FP/(FP+TN)", "ratio", "mean over images AND pooled", False, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.false_positive_rate"),
    _m("fnr", "PIXEL_SEGMENTATION", "FN/(FN+TP)", "ratio", "mean over images AND pooled", False, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.false_negative_rate"),
    _m("mcc", "PIXEL_SEGMENTATION", "Matthews correlation coefficient (0.0 when undefined)", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.mcc"),
    _m("cohen_kappa", "PIXEL_SEGMENTATION", "Cohen's kappa (NaN when degenerate)", "ratio", "mean over images AND pooled", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.cohen_kappa"),
    _m("hd95", "BOUNDARY_DISTANCE", "95th percentile symmetric surface distance", "pixel", "mean over images", False, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.hd95"),
    _m("assd", "BOUNDARY_DISTANCE", "average symmetric surface distance", "pixel", "mean over images", False, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.assd"),
    _m("surface_dice", "BOUNDARY_DISTANCE", "symmetric surface Dice at a pixel tolerance (2 px default)", "ratio", "mean over images", True, "prediction mask + gt mask", False, True, "src/metrics/evaluation_metrics.surface_dice"),
    _m("brier", "PROBABILITY_CALIBRATION", "mean((p - y)^2)", "ratio", "pooled over pixels", False, "probability map + gt mask", False, True, "src/metrics/evaluation_metrics.brier_score"),
    _m("ece", "PROBABILITY_CALIBRATION", "expected calibration error over 256 bins", "ratio", "pooled over pixels", False, "probability map + gt mask", False, True, "src/metrics/evaluation_metrics.expected_calibration_error"),
    _m("mce", "PROBABILITY_CALIBRATION", "maximum calibration error", "ratio", "pooled over pixels", False, "probability map + gt mask", False, True, "src/metrics/evaluation_metrics.maximum_calibration_error"),
    _m("roc_auc", "PROBABILITY_CALIBRATION", "area under the ROC curve (pixel level)", "ratio", "pooled over pixels", True, "probability map + gt mask", False, True, "src/metrics/evaluation_metrics.roc_auc"),
    _m("average_precision", "PROBABILITY_CALIBRATION", "PR-AUC / average precision (pixel level)", "ratio", "pooled over pixels", True, "probability map + gt mask", False, True, "src/metrics/evaluation_metrics.average_precision"),
    _m("component_recall", "COMPONENT_DETECTION", "detected GT components / GT components (overlap >= 1 px)", "ratio", "sum-based over population", True, "prediction mask + gt component labels", True, False, "src/metrics/evaluation_metrics.component_detection_metrics"),
    _m("component_precision", "COMPONENT_DETECTION", "matched predicted components / predicted components", "ratio", "sum-based over population", True, "prediction mask + gt component labels", False, True, "src/metrics/evaluation_metrics.component_detection_metrics"),
    _m("component_f1", "COMPONENT_DETECTION", "harmonic mean of component precision and recall", "ratio", "sum-based over population", True, "prediction mask + gt component labels", False, True, "src/metrics/evaluation_metrics.component_detection_metrics"),
    _m("fp_components_per_image", "COMPONENT_DETECTION", "unmatched predicted components per image", "components/image", "mean over images", False, "prediction mask + gt component labels", False, True, "src/metrics/object_metrics.object_metrics"),
    _m("tiny_recall90_detection", "DOWNSTREAM_COMPONENT_DETECTION", "fraction of TINY GT components with >=1 px predicted overlap (FROZEN domain)", "ratio", "mean over TINY components", True, "prediction mask + gt component labels", True, False, "frozen evaluate_phase14_clean_v3_diagnostic.py"),
    _m("coverage90", "PROPOSAL_COVERAGE", "component pixels inside proposal ROI / component pixels >= 0.90", "ratio", "mean over components", True, "proposal ROIs + gt component bboxes", False, True, "src/inference/predicted_roi.evaluate_roi_coverage"),
    _m("any_overlap_recall", "PROPOSAL_COVERAGE", "fraction of GT components with any proposal overlap", "ratio", "mean over components", True, "proposal ROIs + gt component bboxes", False, True, "src/inference/predicted_roi.evaluate_roi_coverage"),
    _m("val_macro_dice", "PIXEL_SEGMENTATION", "mean per-image macro Dice on the VAL split", "ratio", "mean over images", True, "prediction mask + gt mask", False, False, "src/metrics/segmentation.binary_metrics"),
    _m("zero_proposal_components", "LOCALIZATION_PROPOSAL_SUPPLY", "GT components receiving no proposal overlap", "components", "sum over population", False, "proposal ROIs + gt component bboxes", False, True, "src/inference/predicted_roi.evaluate_roi_coverage"),
    _m("proposals_per_image", "LOCALIZATION_PROPOSAL_SUPPLY", "mean proposals generated per image", "proposals/image", "mean over images", None, "proposal ROIs", False, True, "src/inference/predicted_roi.generate_predicted_rois"),
    _m("roi_area_fraction", "LOCALIZATION_PROPOSAL_SUPPLY", "union proposal ROI area / image area", "ratio", "mean over images", False, "proposal ROIs", False, True, "src/inference/predicted_roi.union_roi_area_fraction"),
]

REGISTRY = {
    "artifact": "project_metric_registry",
    "status": "ACTIVE__DEFAULT_METRIC_CONTRACT_FOR_FUTURE_PHASES",
    "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "version": "1.0.0",
    "purpose": "Default metric contract for all future research phases.",
    "module": "src/metrics/evaluation_metrics.py",
    "module_sha256": hashlib.sha256((PROJECT_ROOT / "src/metrics/evaluation_metrics.py").read_bytes()).hexdigest(),
    "domains": DOMAINS,
    "governance": {
        "new_metrics_label": DESCRIPTIVE,
        "rule": "Only metrics explicitly marked prospective_gate=True may enter a frozen adjudication.",
        "empty_mask_policy_artifact": "reports/audits/evaluation_empty_mask_policy.json",
        "confusion_policy_artifact": "reports/audits/project_evaluation_metric_policy.json",
        "distance_unit": "pixel",
    },
    "metrics": REGISTRY_METRICS,
}

# ── E. Inventory (task section 3) ───────────────────────────────────────────
def _inv(step, task_type, domains, pred, gt, population, existing, missing, derivable, needs_inf, appropriate, adjudicable, status):
    return {
        "phase_or_step": step, "task_type": task_type, "metric_domains": domains,
        "prediction_type": pred, "ground_truth_type": gt, "population": population,
        "existing_metrics": existing, "missing_recommended_metrics": missing,
        "derivable_from_saved_artifacts": derivable, "requires_new_inference": needs_inf,
        "scientifically_appropriate": appropriate, "usable_for_formal_adjudication": adjudicable,
        "status": status,
    }


INVENTORY: List[Dict[str, Any]] = [
    _inv("Phase 09 — KUB UNet baseline training", "TRAINING", ["F"],
         "per-epoch training/validation loss + VAL macro Dice", "native binary KUB masks",
         "clean-v3 VAL (all view types)",
         ["train loss (bce_dice)", "val loss", "val macro Dice", "epoch timing", "early-stop state"],
         ["per-image Dice distribution", "IoU", "pixel confusion", "boundary metrics", "calibration"],
         ["per-image Dice (only aggregate persisted)"], True, True, False,
         "EXISTING_PARTIAL__TRAINING_SCOPE_METRICS_SUFFICIENT"),
    _inv("Phase 10 — baseline comparison (clean-v3)", "SEGMENTATION", ["A", "H"],
         "UNet vs UNet++ binary masks", "native binary KUB masks", "clean-v3 VAL",
         ["mean/median Dice", "macro Dice", "runtime"],
         ["IoU", "precision", "recall", "specificity", "MCC", "pixel confusion", "HD95", "surface Dice", "calibration", "per-image CIs"],
         ["per-image Dice (persisted for the GLOBAL arm)"], True, True, False,
         "EXISTING_PARTIAL__DESCRIPTIVE_BACKFILL_AVAILABLE"),
    _inv("Phase 11 — failure analysis", "DIAGNOSTIC", ["G"],
         "failure taxonomy over saved predictions", "saved failure labels", "clean-v3 VAL",
         ["failure counts by category", "empty-prediction analysis"],
         ["none required (qualitative/diagnostic)"], [], False, True, False,
         "EXISTING_SUFFICIENT"),
    _inv("Phase 12 — oracle ROI", "LOCALIZATION", ["C"],
         "GT-derived ROI proposals", "GT component bboxes", "clean-v3 VAL",
         ["oracle ROI coverage", "retention metrics"],
         ["proposal precision/recall", "ROI area fraction"], ["coverage tables"], False, True, False,
         "EXISTING_SUFFICIENT__ORACLE_BOUND"),
    _inv("Phase 13 — predicted ROI / localizer", "LOCALIZATION", ["C", "B"],
         "localizer heatmap -> proposals (GT-free)", "GT component bboxes", "clean-v3 VAL",
         ["coverage_fraction", "covered90", "covered50", "any_overlap", "zero-proposal counts", "best_proposal_score"],
         ["PR curve", "FROC", "proposal-to-GT IoU", "center displacement", "duplicate rate"],
         ["coverage + best_proposal_score (enables descriptive PR/FROC)"], False, True, False,
         "EXISTING_PARTIAL__PR_FROC_DERIVABLE"),
    _inv("Phase 13 Part1D — predicted-region downstream", "SEGMENTATION", ["A", "B"],
         "regional model masks", "native binary KUB masks", "clean-v3 VAL",
         ["per-model Dice", "component coverage"],
         ["pixel confusion", "boundary metrics", "calibration"], [], True, True, False,
         "EXISTING_PARTIAL__PREDICTIONS_NOT_PERSISTED"),
    _inv("Phase 14 — regional refiner diagnostic (clean-v3)", "SEGMENTATION+DETECTION", ["A", "B", "H"],
         "GLOBAL / ORACLE_REGIONAL / PREDICTED_REGIONAL masks", "native binary KUB masks",
         "103 FULL_FIELD VAL images, 152 components",
         ["mean/median Dice", "detection recall@90 by size", "component recall", "FP/image", "hard-Tiny", "global-empty", "runtime", "ROI burden"],
         ["pixel confusion", "IoU", "precision", "specificity", "MCC", "HD95", "ASSD", "surface Dice", "PR-AUC", "ROC-AUC", "Brier", "ECE", "bootstrap CIs"],
         ["per-image Dice", "per-component overlap pixels", "coverage ratios"],
         True, True, False,
         "EXISTING_PARTIAL__BACKFILLED_DESCRIPTIVELY"),
    _inv("Post-Phase14 root-cause analysis", "CAUSAL_DIAGNOSTIC", ["G"],
         "counterfactual A-only vs C-only interventions", "saved component-level tables", "clean-v3 VAL",
         ["R_A", "R_C", "axis-priority verdict", "component-level deltas"],
         ["none required (causal diagnostic)"], [], False, True, False,
         "EXISTING_SUFFICIENT"),
    _inv("H3 training (size-adaptive sigma localizer)", "TRAINING", ["F", "C"],
         "heatmap localization + proposal supply", "saved localization targets", "clean-v3 TRAIN/VAL",
         ["val_localization_recall", "val_loss", "epoch timing", "selection replay"],
         ["PR/FROC on peak scores"], ["epoch-level metrics table"], False, True, False,
         "EXISTING_SUFFICIENT__TRAINING_SCOPE"),
    _inv("H3 supply-axis evaluation", "LOCALIZATION", ["C", "B"],
         "H3 proposals (GT-free)", "GT component bboxes", "103 FULL_FIELD VAL images, 152 components",
         ["zero-proposal GT/TINY", "any-overlap recall", "coverage90", "proposal precision (descriptive)", "proposals/image"],
         ["PR curve", "FROC", "proposal-to-GT IoU", "center displacement"], ["coverage + score tables"], False, True, False,
         "EXISTING_PARTIAL__PROPOSAL_DOMAIN_ONLY"),
    _inv("H3 downstream evaluation", "SEGMENTATION+DETECTION", ["A", "B", "H"],
         "H3 localizer -> frozen proposals -> Phase-14 refiner -> fused mask", "native binary KUB masks",
         "103 FULL_FIELD VAL images, 152 components",
         ["mean/median Dice", "detection recall@90 by size", "component recall", "FP/image", "hard-Tiny", "global-empty", "proposal burden"],
         ["pixel confusion", "IoU", "precision", "specificity", "MCC", "HD95", "ASSD", "surface Dice", "PR-AUC", "ROC-AUC", "Brier", "ECE", "bootstrap CIs"],
         ["per-image Dice", "per-component overlap pixels"],
         True, True, False,
         "EXISTING_PARTIAL__BACKFILLED_DESCRIPTIVELY"),
    _inv("Project-wide evaluation-metrics backfill (this task)", "SEGMENTATION+BOUNDARY+CALIBRATION", ["A", "D", "E"],
         "GLOBAL / ORACLE / PREDICTED / H3 masks + probability maps", "native binary KUB masks",
         "103 FULL_FIELD VAL images, 152 components",
         ["pixel confusion", "Dice", "IoU", "precision", "recall", "specificity", "NPV", "accuracy", "balanced accuracy", "MCC", "kappa", "HD95", "ASSD", "surface Dice", "Brier", "ECE", "MCE", "ROC-AUC", "PR-AUC", "bootstrap CIs", "paired tests"],
         ["per-pixel spacing (unavailable)", "multi-class metrics (not applicable)", "component TN (undefined)"],
         ["all backfilled values derived from the single safe replay"],
         True, True, False,
         "NEW__DESCRIPTIVE_ONLY__NOT_GATES"),
]


def main() -> None:
    AUDITS.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    (AUDITS / "project_evaluation_metric_policy.json").write_text(
        json.dumps(CONFUSION_POLICY, indent=2), encoding="utf-8")
    (AUDITS / "evaluation_empty_mask_policy.json").write_text(
        json.dumps(EMPTY_POLICY, indent=2), encoding="utf-8")
    (AUDITS / "project_metric_registry.json").write_text(
        json.dumps(REGISTRY, indent=2), encoding="utf-8")

    inventory = {
        "artifact": "project_evaluation_metrics_inventory",
        "status": "PROJECT_EVALUATION_METRICS_INVENTORY_COMPLETE",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "scope": "KUB research line: Phases 09-14, post-Phase14 H3 (training / supply / downstream), and this audit.",
        "out_of_scope_note": "Phase-15/16+ and the multi-domain (MedFILM) notebook directories were not evaluated as they are not part of the completed KUB chain under audit.",
        "metric_domains": DOMAINS,
        "governance": {
            "new_metrics_are_descriptive": True,
            "label": DESCRIPTIVE,
            "frozen_gates_unchanged": True,
            "test_reads": 0, "external_test_reads": 0,
            "phase15_status": "NOT_STARTED_AND_NOT_AUTHORIZED",
        },
        "rows": INVENTORY,
    }
    inv_path = AUDITS / "project_evaluation_metrics_inventory.json"
    inv_path.write_text(json.dumps(inventory, indent=2), encoding="utf-8")

    flat = []
    for r in INVENTORY:
        flat.append({
            "phase_or_step": r["phase_or_step"],
            "task_type": r["task_type"],
            "metric_domains": "|".join(r["metric_domains"]),
            "prediction_type": r["prediction_type"],
            "ground_truth_type": r["ground_truth_type"],
            "population": r["population"],
            "existing_metrics": "; ".join(r["existing_metrics"]),
            "missing_recommended_metrics": "; ".join(r["missing_recommended_metrics"]),
            "derivable_from_saved_artifacts": "; ".join(r["derivable_from_saved_artifacts"]) or "none",
            "requires_new_inference": r["requires_new_inference"],
            "scientifically_appropriate": r["scientifically_appropriate"],
            "usable_for_formal_adjudication": r["usable_for_formal_adjudication"],
            "status": r["status"],
        })
    csv_path = TABLES / "project_evaluation_metrics_inventory.csv"
    pd.DataFrame(flat).to_csv(csv_path, index=False)

    print("Wrote:")
    for p in [AUDITS / "project_evaluation_metric_policy.json",
              AUDITS / "evaluation_empty_mask_policy.json",
              AUDITS / "project_metric_registry.json", inv_path, csv_path]:
        print(f"  {p.relative_to(PROJECT_ROOT)}  sha256={hashlib.sha256(p.read_bytes()).hexdigest()[:16]}...")
    print(f"Inventory rows: {len(INVENTORY)} | registry metrics: {len(REGISTRY_METRICS)}")


if __name__ == "__main__":
    main()
