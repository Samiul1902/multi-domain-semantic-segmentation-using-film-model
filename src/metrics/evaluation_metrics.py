"""Reusable evaluation metrics for the KUB research pipeline.

This module is ADDITIVE. It does not modify or replace the historical metric
implementations in ``src/metrics/segmentation.py`` or
``src/metrics/object_metrics.py``; historical evaluation results must remain
reproducible.

Domains
-------
PIXEL_SEGMENTATION      : binary_confusion_counts, dice, iou, precision, recall,
                          specificity, npv, accuracy, balanced_accuracy, fpr, fnr,
                          mcc, cohen_kappa
BOUNDARY_DISTANCE       : hd95, assd, surface_dice
PROBABILITY_CALIBRATION : brier_score, expected_calibration_error,
                          maximum_calibration_error, reliability_bins
RANKING / CURVES        : roc_auc, average_precision, precision_recall_curve,
                          roc_curve_points, froc_points
COMPONENT_DETECTION     : component_detection_metrics
UNCERTAINTY             : bootstrap_ci, paired_bootstrap_ci, cluster_bootstrap_ci

Empty-mask policy
-----------------
Defined centrally in ``EMPTY_MASK_POLICY`` and mirrored in
``reports/audits/evaluation_empty_mask_policy.json``. Undefined metrics return
``nan`` together with an explicit validity flag; they are never silently zeroed.

Distance units
--------------
No pixel-spacing metadata exists in this repository, so all boundary distances
are in PIXELS. Functions return an explicit ``unit`` field.
"""
from __future__ import annotations

from typing import Dict, Iterable, Optional, Sequence, Tuple

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt

__all__ = [
    "EMPTY_MASK_POLICY",
    "binary_confusion_counts",
    "dice",
    "iou",
    "precision",
    "recall",
    "specificity",
    "npv",
    "accuracy",
    "balanced_accuracy",
    "false_positive_rate",
    "false_negative_rate",
    "mcc",
    "cohen_kappa",
    "segmentation_metrics",
    "pooled_segmentation_metrics",
    "hd95",
    "assd",
    "surface_dice",
    "brier_score",
    "expected_calibration_error",
    "maximum_calibration_error",
    "reliability_bins",
    "roc_auc",
    "average_precision",
    "precision_recall_curve",
    "roc_curve_points",
    "froc_points",
    "component_detection_metrics",
    "bootstrap_ci",
    "paired_bootstrap_ci",
]

_EPS = 1e-7

EMPTY_MASK_POLICY: Dict[str, Dict[str, object]] = {
    "gt_empty_pred_empty": {
        "dice": 1.0, "iou": 1.0, "precision": 1.0, "recall": 1.0,
        "specificity": 1.0, "npv": 1.0, "accuracy": 1.0, "balanced_accuracy": 1.0,
        "mcc": 1.0, "cohen_kappa": 1.0,
        "hd95": "nan_invalid", "assd": "nan_invalid", "surface_dice": "nan_invalid",
        "rationale": "Perfect agreement on an empty foreground; boundary distances undefined.",
    },
    "gt_empty_pred_nonempty": {
        "dice": 0.0, "iou": 0.0, "precision": 0.0, "recall": "nan_invalid",
        "specificity": 1.0, "npv": "nan_invalid", "accuracy": "nan_invalid",
        "balanced_accuracy": "nan_invalid", "mcc": "nan_invalid", "cohen_kappa": "nan_invalid",
        "hd95": "nan_invalid", "assd": "nan_invalid", "surface_dice": "nan_invalid",
        "rationale": "False-positive-only case; recall/NPV/accuracy are undefined without positives.",
    },
    "gt_nonempty_pred_empty": {
        "dice": 0.0, "iou": 0.0, "precision": "nan_invalid", "recall": 0.0,
        "specificity": 1.0, "npv": 0.0, "accuracy": "nan_invalid",
        "balanced_accuracy": "nan_invalid", "mcc": "nan_invalid", "cohen_kappa": "nan_invalid",
        "hd95": "nan_invalid", "assd": "nan_invalid", "surface_dice": "nan_invalid",
        "rationale": "False-negative-only case; boundary distances require both masks non-empty.",
    },
    "both_nonempty": {
        "note": "All metrics defined by their standard formulas.",
    },
}


# ── Pixel confusion ─────────────────────────────────────────────────────────
def binary_confusion_counts(prediction, target) -> Dict[str, int]:
    """Raw pixel confusion counts. Foreground is ``> 0``."""
    p = np.asarray(prediction) > 0
    g = np.asarray(target) > 0
    if p.shape != g.shape:
        raise ValueError(f"shape mismatch: {p.shape} vs {g.shape}")
    tp = int(np.count_nonzero(p & g))
    fp = int(np.count_nonzero(p & ~g))
    fn = int(np.count_nonzero(~p & g))
    tn = int(np.count_nonzero(~p & ~g))
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn,
            "total": int(p.size), "foreground_gt": tp + fn, "foreground_pred": tp + fp}


def _ratio(num: float, den: float, eps: float = _EPS) -> float:
    return float((num + eps) / (den + eps))


def dice(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((2.0 * c["tp"] + eps) / (2.0 * c["tp"] + c["fp"] + c["fn"] + eps))


def iou(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["tp"] + eps) / (c["tp"] + c["fp"] + c["fn"] + eps))


def precision(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["tp"] + eps) / (c["tp"] + c["fp"] + eps))


def recall(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["tp"] + eps) / (c["tp"] + c["fn"] + eps))


def specificity(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["tn"] + eps) / (c["tn"] + c["fp"] + eps))


def npv(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["tn"] + eps) / (c["tn"] + c["fn"] + eps))


def accuracy(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["tp"] + c["tn"] + eps) / (c["total"] + eps))


def balanced_accuracy(c: Dict[str, int], eps: float = _EPS) -> float:
    return 0.5 * (recall(c, eps) + specificity(c, eps))


def false_positive_rate(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["fp"] + eps) / (c["fp"] + c["tn"] + eps))


def false_negative_rate(c: Dict[str, int], eps: float = _EPS) -> float:
    return float((c["fn"] + eps) / (c["fn"] + c["tp"] + eps))


def mcc(c: Dict[str, int], eps: float = _EPS) -> float:
    tp, tn, fp, fn = c["tp"], c["tn"], c["fp"], c["fn"]
    denom = float((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    if denom <= 0.0:
        # scikit-learn convention: MCC is 0.0 when it is not defined.
        return 0.0
    return float((tp * tn - fp * fn) / np.sqrt(denom))


def cohen_kappa(c: Dict[str, int], eps: float = _EPS) -> float:
    tp, tn, fp, fn = c["tp"], c["tn"], c["fp"], c["fn"]
    total = tp + tn + fp + fn
    if total == 0:
        return float("nan")
    po = (tp + tn) / total
    pe = ((tp + fp) * (tp + fn) + (tn + fn) * (tn + fp)) / (total * total)
    if abs(1.0 - pe) < 1e-15:
        return float("nan")
    return float((po - pe) / (1.0 - pe))


def segmentation_metrics(prediction, target) -> Dict[str, object]:
    """Full binary pixel metric bundle with explicit empty-mask handling."""
    p = np.asarray(prediction) > 0
    g = np.asarray(target) > 0
    c = binary_confusion_counts(p, g)
    gt_empty = c["foreground_gt"] == 0
    pred_empty = c["foreground_pred"] == 0

    out: Dict[str, object] = dict(c)
    if gt_empty and pred_empty:
        case = "gt_empty_pred_empty"
        out.update(dice=1.0, iou=1.0, precision=1.0, recall=1.0, specificity=1.0, npv=1.0,
                   accuracy=1.0, balanced_accuracy=1.0, mcc=1.0, cohen_kappa=1.0,
                   fpr=0.0, fnr=float("nan"))
        out["undefined"] = ["fnr"]
    elif gt_empty and not pred_empty:
        case = "gt_empty_pred_nonempty"
        out.update(dice=0.0, iou=0.0, precision=0.0, recall=float("nan"), specificity=1.0,
                   npv=float("nan"), accuracy=float("nan"), balanced_accuracy=float("nan"),
                   mcc=float("nan"), cohen_kappa=float("nan"), fpr=1.0, fnr=float("nan"))
        out["undefined"] = ["recall", "npv", "accuracy", "balanced_accuracy", "mcc", "cohen_kappa", "fnr"]
    elif not gt_empty and pred_empty:
        case = "gt_nonempty_pred_empty"
        out.update(dice=0.0, iou=0.0, precision=float("nan"), recall=0.0, specificity=1.0,
                   npv=0.0, accuracy=float("nan"), balanced_accuracy=float("nan"),
                   mcc=float("nan"), cohen_kappa=float("nan"), fpr=0.0, fnr=1.0)
        out["undefined"] = ["precision", "accuracy", "balanced_accuracy", "mcc", "cohen_kappa"]
    else:
        case = "both_nonempty"
        out.update(dice=dice(c), iou=iou(c), precision=precision(c), recall=recall(c),
                   specificity=specificity(c), npv=npv(c), accuracy=accuracy(c),
                   balanced_accuracy=balanced_accuracy(c), mcc=mcc(c), cohen_kappa=cohen_kappa(c),
                   fpr=false_positive_rate(c), fnr=false_negative_rate(c))
        out["undefined"] = []
    out["empty_case"] = case
    out["gt_empty"] = bool(gt_empty)
    out["pred_empty"] = bool(pred_empty)
    out["metric_domain"] = "PIXEL_SEGMENTATION"
    return out


def pooled_segmentation_metrics(confusions: Sequence[Dict[str, int]]) -> Dict[str, float]:
    """Pool raw pixel counts across images, then derive normalized metrics.

    Kept strictly separate from image-level averages.
    """
    agg = {k: int(sum(c[k] for c in confusions)) for k in ("tp", "tn", "fp", "fn", "total")}
    agg["foreground_gt"] = agg["tp"] + agg["fn"]
    agg["foreground_pred"] = agg["tp"] + agg["fp"]
    out = dict(agg)
    out.update(dice=dice(agg), iou=iou(agg), precision=precision(agg), recall=recall(agg),
               specificity=specificity(agg), npv=npv(agg), accuracy=accuracy(agg),
               balanced_accuracy=balanced_accuracy(agg), mcc=mcc(agg), cohen_kappa=cohen_kappa(agg),
               fpr=false_positive_rate(agg), fnr=false_negative_rate(agg))
    out["metric_domain"] = "PIXEL_SEGMENTATION_POOLED"
    return out


# ── Boundary metrics (units = PIXELS) ───────────────────────────────────────
def _surfaces(mask: np.ndarray, connectivity: int = 8):
    structure = np.ones((3, 3), dtype=bool) if connectivity == 8 else None
    m = np.asarray(mask, dtype=bool)
    return m ^ binary_erosion(m, structure=structure, border_value=0)


def _boundary_distances(pred: np.ndarray, gt: np.ndarray):
    ps, gs = _surfaces(pred), _surfaces(gt)
    d_gt = distance_transform_edt(~gs)
    d_pred = distance_transform_edt(~ps)
    return d_gt[ps], d_pred[gs]


def hd95(prediction, target) -> Dict[str, object]:
    """95th-percentile symmetric surface distance, in pixels."""
    pred = np.asarray(prediction) > 0
    gt = np.asarray(target) > 0
    if not pred.any() or not gt.any():
        reason = "both_empty" if (not pred.any() and not gt.any()) else (
            "empty_prediction" if not pred.any() else "empty_ground_truth")
        return {"hd95": float("nan"), "valid": False, "reason": reason, "unit": "pixel",
                "metric_domain": "BOUNDARY_DISTANCE"}
    a, b = _boundary_distances(pred, gt)
    return {"hd95": float(np.percentile(np.concatenate([a, b]), 95)), "valid": True,
            "reason": "", "unit": "pixel", "metric_domain": "BOUNDARY_DISTANCE"}


def assd(prediction, target) -> Dict[str, object]:
    """Average symmetric surface distance, in pixels."""
    pred = np.asarray(prediction) > 0
    gt = np.asarray(target) > 0
    if not pred.any() or not gt.any():
        reason = "both_empty" if (not pred.any() and not gt.any()) else (
            "empty_prediction" if not pred.any() else "empty_ground_truth")
        return {"assd": float("nan"), "valid": False, "reason": reason, "unit": "pixel",
                "metric_domain": "BOUNDARY_DISTANCE"}
    a, b = _boundary_distances(pred, gt)
    return {"assd": float(0.5 * (a.mean() + b.mean())), "valid": True, "reason": "",
            "unit": "pixel", "metric_domain": "BOUNDARY_DISTANCE"}


def surface_dice(prediction, target, tolerance: float = 2.0) -> Dict[str, object]:
    """Symmetric surface Dice at a pixel tolerance (default 2 px)."""
    pred = np.asarray(prediction) > 0
    gt = np.asarray(target) > 0
    if not pred.any() or not gt.any():
        reason = "both_empty" if (not pred.any() and not gt.any()) else (
            "empty_prediction" if not pred.any() else "empty_ground_truth")
        return {"surface_dice": float("nan"), "valid": False, "reason": reason,
                "tolerance": float(tolerance), "unit": "pixel", "metric_domain": "BOUNDARY_DISTANCE"}
    ps, gs = _surfaces(pred), _surfaces(gt)
    d_gt = distance_transform_edt(~gs)
    d_pred = distance_transform_edt(~ps)
    a = float(np.mean(d_gt[ps] <= tolerance))
    b = float(np.mean(d_pred[gs] <= tolerance))
    return {"surface_dice": 0.5 * (a + b), "valid": True, "reason": "",
            "tolerance": float(tolerance), "unit": "pixel", "metric_domain": "BOUNDARY_DISTANCE"}


# ── Calibration ─────────────────────────────────────────────────────────────
def brier_score(y_true, y_prob) -> float:
    y = np.asarray(y_true, dtype=np.float64).ravel()
    p = np.asarray(y_prob, dtype=np.float64).ravel()
    return float(np.mean((p - y) ** 2))


def reliability_bins(y_true, y_prob, n_bins: int = 15) -> Dict[str, list]:
    y = np.asarray(y_true, dtype=np.float64).ravel()
    p = np.asarray(y_prob, dtype=np.float64).ravel()
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    conf, acc, count = [], [], []
    for b in range(n_bins):
        m = idx == b
        n = int(np.count_nonzero(m))
        count.append(n)
        conf.append(float(p[m].mean()) if n else float("nan"))
        acc.append(float(y[m].mean()) if n else float("nan"))
    return {"bin_edges": edges.tolist(), "bin_count": count,
            "bin_confidence": conf, "bin_accuracy": acc}


def expected_calibration_error(y_true, y_prob, n_bins: int = 15) -> float:
    rb = reliability_bins(y_true, y_prob, n_bins)
    counts = np.asarray(rb["bin_count"], dtype=np.float64)
    total = counts.sum()
    if total == 0:
        return float("nan")
    conf = np.asarray(rb["bin_confidence"], dtype=np.float64)
    acc = np.asarray(rb["bin_accuracy"], dtype=np.float64)
    valid = ~np.isnan(conf)
    return float(np.sum((counts[valid] / total) * np.abs(acc[valid] - conf[valid])))


def maximum_calibration_error(y_true, y_prob, n_bins: int = 15) -> float:
    rb = reliability_bins(y_true, y_prob, n_bins)
    conf = np.asarray(rb["bin_confidence"], dtype=np.float64)
    acc = np.asarray(rb["bin_accuracy"], dtype=np.float64)
    counts = np.asarray(rb["bin_count"], dtype=np.float64)
    valid = (~np.isnan(conf)) & (counts > 0)
    if not valid.any():
        return float("nan")
    return float(np.max(np.abs(acc[valid] - conf[valid])))


# ── Ranking metrics ─────────────────────────────────────────────────────────
def roc_curve_points(y_true, y_score, n_bins: int = 4096):
    """Histogram-approximated ROC points (tp_rate, fp_rate) ascending by score."""
    y = np.asarray(y_true, dtype=np.float64).ravel()
    p = np.asarray(y_score, dtype=np.float64).ravel()
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    pos = float(np.count_nonzero(y > 0.5)) or 1.0
    neg = float(np.count_nonzero(y <= 0.5)) or 1.0
    tp = np.bincount(idx[y > 0.5], minlength=n_bins).astype(np.float64)
    fp = np.bincount(idx[y <= 0.5], minlength=n_bins).astype(np.float64)
    tp_c = np.cumsum(tp[::-1]) / pos
    fp_c = np.cumsum(fp[::-1]) / neg
    return np.concatenate([[0.0], fp_c]), np.concatenate([[0.0], tp_c])


def roc_auc(y_true, y_score, n_bins: int = 4096) -> float:
    """ROC-AUC via the trapezoidal rule on a histogram-approximated ROC curve."""
    fpr, tpr = roc_curve_points(y_true, y_score, n_bins)
    trapz = getattr(np, "trapezoid", None) or np.trapz  # NumPy 2.x renamed trapz
    return float(trapz(tpr, fpr))


def precision_recall_curve(y_true, y_score, n_bins: int = 4096):
    y = np.asarray(y_true, dtype=np.float64).ravel()
    p = np.asarray(y_score, dtype=np.float64).ravel()
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    idx = np.clip(np.digitize(p, edges[1:-1], right=False), 0, n_bins - 1)
    pos = float(np.count_nonzero(y > 0.5)) or 1.0
    tp = np.bincount(idx[y > 0.5], minlength=n_bins).astype(np.float64)
    fp = np.bincount(idx[y <= 0.5], minlength=n_bins).astype(np.float64)
    tp_c = np.cumsum(tp[::-1])
    fp_c = np.cumsum(fp[::-1])
    rec = tp_c / pos
    prec = np.where((tp_c + fp_c) > 0, tp_c / np.maximum(tp_c + fp_c, 1e-12), 1.0)
    return rec, prec


def average_precision(y_true, y_score, n_bins: int = 4096) -> float:
    """PR-AUC via the step-wise average precision definition."""
    y = np.asarray(y_true, dtype=np.float64).ravel()
    if np.count_nonzero(y > 0.5) == 0:
        return float("nan")
    rec, prec = precision_recall_curve(y, y_score, n_bins)
    prev_r = 0.0
    ap = 0.0
    for r, p in zip(rec, prec):
        ap += max(0.0, r - prev_r) * p
        prev_r = r
    return float(ap)


# ── Detection / proposal curves ─────────────────────────────────────────────
def froc_points(scores: Sequence[float], is_tp: Sequence[bool], n_images: int,
                thresholds: Optional[Iterable[float]] = None) -> Dict[str, list]:
    """FROC: sensitivity vs false positives per image, over a score sweep.

    DESCRIPTIVE ONLY. The frozen operating point is never changed by this curve.
    """
    s = np.asarray(scores, dtype=np.float64)
    t = np.asarray(is_tp, dtype=bool)
    if thresholds is None:
        thresholds = np.unique(np.round(np.linspace(0.0, 1.0, 101), 4))
    total_pos = int(np.count_nonzero(t)) or 1
    sens, fp_per_img = [], []
    for thr in thresholds:
        sel = s >= thr
        sens.append(float(np.count_nonzero(sel & t)) / total_pos)
        fp_per_img.append(float(np.count_nonzero(sel & ~t)) / max(1, n_images))
    return {"thresholds": [float(x) for x in thresholds], "sensitivity": sens,
            "fp_per_image": fp_per_img}


# ── Component detection ─────────────────────────────────────────────────────
def component_detection_metrics(labeled_gt, predicted_mask, size_labels: Optional[Dict[int, str]] = None,
                                min_overlap_pixels: int = 1) -> Dict[str, object]:
    """Overlap-based GT-component detection accounting (TP/FN, plus FP components).

    NOTE: conventional TN is undefined for component detection, so no 2x2
    confusion matrix is produced here.
    """
    from scipy.ndimage import label as _label

    gt = np.asarray(labeled_gt)
    pred = np.asarray(predicted_mask) > 0
    pred_labels, n_pred = _label(pred, structure=np.ones((3, 3), dtype=int))

    gt_ids = [int(v) for v in np.unique(gt) if v > 0]
    matched_pred = set()
    per_size: Dict[str, Dict[str, int]] = {}
    detected = 0
    for gid in gt_ids:
        gm = gt == gid
        overlap = np.unique(pred_labels[gm])
        overlap = overlap[overlap > 0]
        valid = [int(pid) for pid in overlap
                 if np.count_nonzero((pred_labels == pid) & gm) >= min_overlap_pixels]
        hit = bool(valid)
        detected += int(hit)
        matched_pred.update(valid)
        if size_labels is not None:
            s = size_labels.get(gid, "UNKNOWN")
            d = per_size.setdefault(s, {"gt": 0, "detected": 0})
            d["gt"] += 1
            d["detected"] += int(hit)

    n_gt = len(gt_ids)
    fp_components = n_pred - len(matched_pred)
    precision_c = (len(matched_pred) / n_pred) if n_pred else float("nan")
    recall_c = (detected / n_gt) if n_gt else float("nan")
    f1_c = (2 * precision_c * recall_c / (precision_c + recall_c)) if (
        n_gt and n_pred and (precision_c + recall_c) > 0) else float("nan")
    return {
        "metric_domain": "COMPONENT_DETECTION",
        "gt_components": n_gt,
        "predicted_components": int(n_pred),
        "tp_components": detected,
        "fn_components": n_gt - detected,
        "fp_components": int(fp_components),
        "component_precision": precision_c,
        "component_recall": recall_c,
        "component_f1": f1_c,
        "per_size": per_size,
        "min_overlap_pixels": min_overlap_pixels,
        "tn_defined": False,
    }


# ── Uncertainty ─────────────────────────────────────────────────────────────
def bootstrap_ci(values: Sequence[float], statistic=np.mean, n_boot: int = 2000,
                 seed: int = 42, alpha: float = 0.05, resampling_unit: str = "image") -> Dict[str, object]:
    """Percentile bootstrap CI with a deterministic seed."""
    v = np.asarray([x for x in values if not (isinstance(x, float) and np.isnan(x))], dtype=np.float64)
    if v.size == 0:
        return {"estimate": float("nan"), "ci_low": float("nan"), "ci_high": float("nan"),
                "n_boot": n_boot, "seed": seed, "resampling_unit": resampling_unit,
                "ci_method": "percentile", "n": 0}
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    stats = statistic(v[idx], axis=1)
    return {
        "estimate": float(statistic(v)),
        "ci_low": float(np.percentile(stats, 100 * alpha / 2)),
        "ci_high": float(np.percentile(stats, 100 * (1 - alpha / 2))),
        "n_boot": int(n_boot), "seed": int(seed), "alpha": float(alpha),
        "resampling_unit": resampling_unit, "ci_method": "percentile", "n": int(v.size),
    }


def paired_bootstrap_ci(a: Sequence[float], b: Sequence[float], n_boot: int = 2000,
                        seed: int = 42, alpha: float = 0.05,
                        resampling_unit: str = "image") -> Dict[str, object]:
    """Paired percentile bootstrap CI for mean(a) - mean(b) on matched units."""
    x = np.asarray(a, dtype=np.float64)
    y = np.asarray(b, dtype=np.float64)
    if x.shape != y.shape:
        raise ValueError(f"paired arrays must match: {x.shape} vs {y.shape}")
    d = x - y
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, d.size, size=(n_boot, d.size))
    stats = d[idx].mean(axis=1)
    return {
        "mean_difference": float(d.mean()),
        "median_difference": float(np.median(d)),
        "ci_low": float(np.percentile(stats, 100 * alpha / 2)),
        "ci_high": float(np.percentile(stats, 100 * (1 - alpha / 2))),
        "n_boot": int(n_boot), "seed": int(seed), "alpha": float(alpha),
        "resampling_unit": resampling_unit, "ci_method": "percentile_paired", "n": int(d.size),
    }
