"""Explicit binary/multiclass overlap and 2-D pixel-centre boundary metrics."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt


def _labels(pred, truth):
    p, g = np.asarray(pred), np.asarray(truth)
    if p.ndim != 2 or p.shape != g.shape or not p.size:
        raise ValueError("nonempty, matching 2-D masks required")
    for x in (p, g):
        if x.dtype.kind not in "biuf" or not np.isfinite(x).all() or not np.equal(x, np.floor(x)).all():
            raise ValueError("finite integer labels required")
    return p, g


def _ratio(n, d):
    return float(n / d) if d else None


def binary_metrics(pred, truth):
    p, g = _labels(pred, truth)
    if not np.isin(p, [0, 1]).all() or not np.isin(g, [0, 1]).all():
        raise ValueError("binary labels must be 0 or 1")
    p, g = p.astype(bool), g.astype(bool)
    tp, fp, tn, fn = (int(np.count_nonzero(x)) for x in (p & g, p & ~g, ~p & ~g, ~p & g))
    precision, recall = _ratio(tp, tp + fp), _ratio(tp, tp + fn)
    specificity, npv = _ratio(tn, tn + fp), _ratio(tn, tn + fn)
    dice = _ratio(2 * tp, 2 * tp + fp + fn)
    iou = _ratio(tp, tp + fp + fn)
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": precision, "recall": recall, "specificity": specificity,
            "npv": npv, "balanced_accuracy": (recall + specificity) / 2 if recall is not None and specificity is not None else None,
            "dice": 1.0 if dice is None else dice, "f1": 1.0 if dice is None else dice,
            "iou": 1.0 if iou is None else iou,
            "predicted_area_pixels": tp + fp, "reference_area_pixels": tp + fn,
            "area_error_pixels": fp - fn, "absolute_area_error_pixels": abs(fp - fn),
            "relative_area_error": _ratio(fp - fn, tp + fn),
            "empty_case": "both_empty" if not p.any() and not g.any() else "prediction_empty" if not p.any() else "reference_empty" if not g.any() else "both_nonempty"}


def c1_compatibility(probability, truth):
    """Frozen C1 per-image probability threshold >= .5, epsilon 1e-7.

    Uses float32 count arithmetic as in the frozen torch helper. It is a
    compatibility calculation, not a replacement for stored best_records.
    """
    p = np.asarray(probability)
    if p.dtype.kind not in "fiu" or not np.isfinite(p).all() or np.any((p < 0) | (p > 1)):
        raise ValueError("finite probabilities in [0,1] required")
    c = binary_metrics((p >= 0.5).astype(np.uint8), truth)
    tp, fp, fn = (np.float32(c[k]) for k in ("tp", "fp", "fn"))
    e = np.float32(1e-7)
    return {"dice": float((np.float32(2) * tp + e) / (np.float32(2) * tp + fp + fn + e)),
            "iou": float((tp + e) / (tp + fp + fn + e)),
            "precision": float((tp + e) / (tp + fp + e)),
            "recall": float((tp + e) / (tp + fn + e)), "threshold": 0.5, "epsilon": 1e-7,
            "version": "c1_phase21_compatibility_v1"}


def multiclass_metrics(pred, truth, class_ids):
    p, g = _labels(pred, truth)
    ids = list(class_ids)
    if not ids or len(set(ids)) != len(ids) or any(type(i) is not int for i in ids):
        raise ValueError("unique integer class IDs required")
    if not np.isin(p, ids).all() or not np.isin(g, ids).all():
        raise ValueError("unknown class ID")
    per = {i: binary_metrics(p == i, g == i) for i in ids}
    support = {i: int(np.count_nonzero(g == i)) for i in ids}
    n = sum(support.values())
    sums = {k: sum(per[i][k] for i in ids) for k in ("tp", "fp", "fn")}
    return {"per_class": per, "support": support,
            "macro_dice": float(np.mean([per[i]["dice"] for i in ids])),
            "macro_iou": float(np.mean([per[i]["iou"] for i in ids])),
            "weighted_dice": sum(support[i] * per[i]["dice"] for i in ids) / n,
            "weighted_iou": sum(support[i] * per[i]["iou"] for i in ids) / n,
            "micro_dice": _ratio(2 * sums["tp"], 2 * sums["tp"] + sums["fp"] + sums["fn"]),
            "micro_iou": _ratio(sums["tp"], sums["tp"] + sums["fp"] + sums["fn"])}


def surface_metrics(pred, truth, spacing=None, tolerance=1.0):
    """Symmetric distances between 8-connected boundary pixel centres.

    Spacing is (row, column) in mm or None (pixel units). Surfaces have equal
    pixel-centre weight, not physical contour-length weighting. HD95 is the
    95th percentile of the concatenated directed distances (linear percentile).
    """
    p, g = _labels(pred, truth)
    if not np.isin(p, [0, 1]).all() or not np.isin(g, [0, 1]).all():
        raise ValueError("binary labels required")
    if not np.isfinite(tolerance) or tolerance < 0:
        raise ValueError("nonnegative finite tolerance required")
    if spacing is None:
        sampling, unit = (1.0, 1.0), "pixel"
    else:
        sampling = np.asarray(spacing, dtype=float)
        if sampling.shape != (2,) or not np.isfinite(sampling).all() or np.any(sampling <= 0):
            raise ValueError("spacing must be positive finite (row, column) in mm")
        unit = "mm"
    p, g = p.astype(bool), g.astype(bool)
    names = ("hd95", "hausdorff", "assd", "surface_dice", "surface_precision", "surface_recall")
    result = {"unit": unit, "spacing": list(sampling), "tolerance": float(tolerance),
              "weighting": "boundary_pixel_centres_equal", "valid": bool(p.any() and g.any())}
    if not result["valid"]:
        result.update({k: None for k in names})
        result["undefined_reason"] = "one_or_both_masks_empty"
        return result
    structure = np.ones((3, 3), dtype=bool)
    ps = p & ~binary_erosion(p, structure=structure, border_value=0)
    gs = g & ~binary_erosion(g, structure=structure, border_value=0)
    pd = distance_transform_edt(~gs, sampling=sampling)[ps]
    gd = distance_transform_edt(~ps, sampling=sampling)[gs]
    both = np.concatenate((pd, gd))
    result.update({"hd95": float(np.percentile(both, 95)), "hausdorff": float(both.max()),
                   "assd": float(both.mean()), "surface_dice": float(((pd <= tolerance).sum() + (gd <= tolerance).sum()) / both.size),
                   "surface_precision": float(np.mean(pd <= tolerance)), "surface_recall": float(np.mean(gd <= tolerance)),
                   "undefined_reason": None})
    return result
