"""Phase C metric engine.

This is a **façade** over :mod:`src.metrics.evaluation_metrics`, which already
implements the pixel confusion, the empty-mask taxonomy and the boundary
distances.  Nothing here re-derives a Dice coefficient from scratch: the shared
module is called and its result is wrapped with the contracts the evaluator
needs — units, spacing, non-finite policy and explicit aggregation levels.

Three aggregation levels are kept strictly apart, because averaging over them
gives different numbers and only one of them is the protocol aggregate:

``PER_IMAGE``
    each image contributes one value; the domain value is the unweighted mean
    over that domain's images.
``PER_DOMAIN``
    the four domain means, plus ``equal_domain_macro_dice`` — the unweighted mean
    of the four, which is the protocol's headline aggregate.
``POOLED``
    raw pixel counts summed over images, then the ratio recomputed.  A different
    quantity, reported separately and never substituted for the above.

HD95 units
----------
The KUB corpus records **no physical pixel spacing**, so every distance metric
here is in **pixels** and ``hd95_unit`` says so.  A physical millimetre value is
computed only when a caller supplies spacing; otherwise ``hd95_mm`` is ``None``
and no physical number is invented.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from src.metrics import evaluation_metrics as EM

from . import protocol as P

EPS = 1e-7


class MetricError(RuntimeError):
    pass


class NonFiniteProbabilityError(MetricError):
    pass


class ShapeMismatchError(MetricError):
    pass


# --------------------------------------------------------------------------- #
# Boundary metrics with explicit units
# --------------------------------------------------------------------------- #
def hd95_with_units(prediction: np.ndarray, target: np.ndarray, *,
                    spacing: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    """HD95 in pixels, and in millimetres only when spacing is supplied.

    ``spacing`` is ``(row_mm, col_mm)``.  When it is ``None`` the physical value
    is ``None`` — the function never assumes an isotropic 1 mm pixel.
    """
    pred = np.asarray(prediction) > 0
    gt = np.asarray(target) > 0
    if pred.shape != gt.shape:
        raise ShapeMismatchError(f"shape mismatch: {pred.shape} vs {gt.shape}")

    base = EM.hd95(pred, gt)
    out: Dict[str, Any] = {
        "hd95": base["hd95"], "hd95_valid": bool(base["valid"]),
        "hd95_invalid_reason": base["reason"], "hd95_unit": "pixel",
        "hd95_mm": None, "hd95_spacing_mm": None,
        "hd95_convention": ("symmetric 95th percentile of pooled surface distances; "
                            "any empty mask -> undefined, never 0"),
    }
    if spacing is None or not base["valid"]:
        return out

    row_mm, col_mm = (float(spacing[0]), float(spacing[1]))
    if not (row_mm > 0 and col_mm > 0):
        raise MetricError(f"spacing must be positive, got {spacing!r}")
    from scipy.ndimage import distance_transform_edt

    structure = np.ones((3, 3), dtype=bool)
    ps = EM._surfaces(pred)          # noqa: SLF001 - shared surface definition
    gs = EM._surfaces(gt)
    d_gt = distance_transform_edt(~gs, sampling=(row_mm, col_mm))
    d_pred = distance_transform_edt(~ps, sampling=(row_mm, col_mm))
    pooled = np.concatenate([d_gt[ps], d_pred[gs]])
    out["hd95_mm"] = float(np.percentile(pooled, 95))
    out["hd95_spacing_mm"] = [row_mm, col_mm]
    return out


# --------------------------------------------------------------------------- #
# Single-image scoring
# --------------------------------------------------------------------------- #
def _validate_probability(probability: np.ndarray, *, on_non_finite: str) -> Tuple[np.ndarray, int]:
    arr = np.asarray(probability, dtype=np.float64)
    if arr.ndim != 2:
        raise MetricError(f"probability map must be 2-D, got shape {arr.shape}")
    bad = int((~np.isfinite(arr)).sum())
    if bad:
        if on_non_finite == "raise":
            raise NonFiniteProbabilityError(f"{bad} non-finite probability value(s)")
        if on_non_finite != "mask":
            raise MetricError(f"unknown on_non_finite policy {on_non_finite!r}")
        arr = np.where(np.isfinite(arr), arr, 0.0)
    return arr, bad


def score_prediction(*, sample_id: str, domain: str, task_id: int,
                     final_probability: np.ndarray, ground_truth: np.ndarray,
                     global_probability: Optional[np.ndarray] = None,
                     state: str = "NOT_APPLICABLE",
                     threshold: float = P.SEGMENTATION_OUTPUT_THRESHOLD,
                     spacing: Optional[Sequence[float]] = None,
                     on_non_finite: str = "raise",
                     patient_id: Optional[str] = None,
                     group_key: Optional[str] = None) -> Dict[str, Any]:
    """Score ONE image.  The ground truth is used here and nowhere upstream.

    ``final_probability`` and ``ground_truth`` must have the same shape; the
    original image geometry is preserved, so a non-square image simply produces
    a non-square probability map.
    """
    prob, non_finite = _validate_probability(final_probability, on_non_finite=on_non_finite)
    gt = np.asarray(ground_truth) > 0
    if prob.shape != gt.shape:
        raise ShapeMismatchError(f"{sample_id}: probability {prob.shape} vs GT {gt.shape}")

    pred = prob >= float(threshold)
    conf = EM.binary_confusion_counts(pred, gt)
    bundle = EM.segmentation_metrics(pred, gt)
    hd = hd95_with_units(pred, gt, spacing=spacing)

    record: Dict[str, Any] = {
        "sample_id": str(sample_id), "domain": str(domain), "task_id": int(task_id),
        "state": str(state),
        "threshold": float(threshold),
        "height": int(gt.shape[0]), "width": int(gt.shape[1]),
        "non_square": bool(gt.shape[0] != gt.shape[1]),
        "tp": conf["tp"], "fp": conf["fp"], "fn": conf["fn"], "tn": conf["tn"],
        "dice": float(bundle["dice"]), "iou": float(bundle["iou"]),
        "precision": float(bundle["precision"]), "recall": float(bundle["recall"]),
        "specificity": float(bundle["specificity"]),
        "gt_empty": bool(bundle["gt_empty"]), "pred_empty": bool(bundle["pred_empty"]),
        "empty_case": bundle["empty_case"],
        "all_foreground_gt": bool(conf["tn"] == 0 and conf["foreground_gt"] > 0),
        "undefined_metrics": list(bundle["undefined"]),
        "hd95": hd["hd95"], "hd95_valid": hd["hd95_valid"],
        "hd95_invalid_reason": hd["hd95_invalid_reason"],
        "hd95_unit": hd["hd95_unit"], "hd95_mm": hd["hd95_mm"],
        "empty_gt_false_positive": bool(bundle["gt_empty"] and not bundle["pred_empty"]),
        "non_finite_pixels": non_finite,
        "patient_id": patient_id, "group_key": group_key,
        "metric_implementation_version": P.METRIC_IMPLEMENTATION_VERSION,
    }
    if global_probability is not None:
        gprob, _ = _validate_probability(global_probability, on_non_finite="mask")
        if gprob.shape != gt.shape:
            raise ShapeMismatchError(f"{sample_id}: global map {gprob.shape} vs GT {gt.shape}")
        gb = EM.segmentation_metrics(gprob >= float(threshold), gt)
        record["global_dice"] = float(gb["dice"])
        record["delta_dice_vs_global"] = record["dice"] - float(gb["dice"])
    executed = state in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT")
    accepted = state == "EXECUTE_THEN_ACCEPT"
    record["refiner_executed"] = executed
    record["accepted"] = accepted
    record["harmful_accepted"] = bool(
        accepted and "global_dice" in record and record["dice"] < record["global_dice"] - 1e-9)
    return record


# --------------------------------------------------------------------------- #
# Aggregation
# --------------------------------------------------------------------------- #
def _finite(values: Iterable[Any]) -> List[float]:
    out = []
    for v in values:
        try:
            f = float(v)
        except (TypeError, ValueError):
            continue
        if np.isfinite(f):
            out.append(f)
    return out


def aggregate_records(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Per-domain and across-domain aggregates, with the levels kept separate."""
    if not records:
        raise MetricError("no records to aggregate")
    per_domain: Dict[str, Dict[str, Any]] = {}
    for domain in P.DOMAINS:
        rows = [r for r in records if r["domain"] == domain]
        if not rows:
            continue
        hd = _finite(r["hd95"] for r in rows)
        per_domain[domain] = {
            "n": len(rows),
            "dice": float(np.mean([r["dice"] for r in rows])),
            "iou": float(np.mean([r["iou"] for r in rows])),
            "precision": float(np.mean(_finite(r["precision"] for r in rows))) if _finite(
                r["precision"] for r in rows) else None,
            "recall": float(np.mean(_finite(r["recall"] for r in rows))) if _finite(
                r["recall"] for r in rows) else None,
            "hd95_mean": float(np.mean(hd)) if hd else None,
            "hd95_defined_n": len(hd),
            "hd95_unit": "pixel",
            "empty_gt_n": int(sum(r["gt_empty"] for r in rows)),
            "empty_pred_n": int(sum(r["pred_empty"] for r in rows)),
            "empty_gt_false_positives": int(sum(r["empty_gt_false_positive"] for r in rows)),
            "non_square_n": int(sum(bool(r["non_square"]) for r in rows)),
            "all_foreground_gt_n": int(sum(bool(r["all_foreground_gt"]) for r in rows)),
            "undefined_precision_n": int(sum("precision" in r["undefined_metrics"] for r in rows)),
            "undefined_recall_n": int(sum("recall" in r["undefined_metrics"] for r in rows)),
        }
    missing = [d for d in P.DOMAINS if d not in per_domain]
    if missing:
        raise MetricError(f"records must cover all four domains; missing {missing}")

    confusions = [{"tp": r["tp"], "tn": r["tn"], "fp": r["fp"], "fn": r["fn"],
                   "total": r["tp"] + r["tn"] + r["fp"] + r["fn"]} for r in records]
    pooled = EM.pooled_segmentation_metrics(confusions)
    empty_rows = [r for r in records if r["gt_empty"]]

    out: Dict[str, Any] = {
        "n_images": len(records),
        "per_domain": per_domain,
        "domain_n": {d: per_domain[d]["n"] for d in P.DOMAINS},
        "equal_domain_macro_dice": float(np.mean([per_domain[d]["dice"] for d in P.DOMAINS])),
        "equal_domain_macro_iou": float(np.mean([per_domain[d]["iou"] for d in P.DOMAINS])),
        "image_weighted_dice": float(np.mean([r["dice"] for r in records])),
        "pooled_dice": float(pooled["dice"]),
        "pooled_iou": float(pooled["iou"]),
        "empty_mask_false_positive_rate": (
            sum(r["empty_gt_false_positive"] for r in empty_rows) / len(empty_rows)
            if empty_rows else None),
        "empty_gt_n": len(empty_rows),
        "hd95_unit": "pixel",
        "hd95_defined_n": int(sum(1 for r in records if r["hd95_valid"])),
        "hd95_undefined_n": int(sum(1 for r in records if not r["hd95_valid"])),
        "aggregation_levels": ["PER_IMAGE", "PER_DOMAIN", "POOLED"],
        "primary_aggregate": "equal_domain_macro_dice",
        "metric_implementation_version": P.METRIC_IMPLEMENTATION_VERSION,
    }
    executed = [r for r in records if r.get("refiner_executed")]
    if any("refiner_executed" in r for r in records):
        out.update({
            "refiner_invocation_rate": len(executed) / len(records),
            "safety_accept_fraction_of_executed": (
                sum(r["accepted"] for r in executed) / len(executed) if executed else None),
            "safety_reject_fraction_of_executed": (
                sum(not r["accepted"] for r in executed) / len(executed) if executed else None),
            "harmful_accepted_refinements": int(sum(r["harmful_accepted"] for r in records)),
        })
    return out


def pooled_metrics(records: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    """Pixel-pooled metrics alone, kept in its own function so it is never mixed in."""
    confusions = [{"tp": r["tp"], "tn": r["tn"], "fp": r["fp"], "fn": r["fn"],
                   "total": r["tp"] + r["tn"] + r["fp"] + r["fn"]} for r in records]
    return EM.pooled_segmentation_metrics(confusions)


# --------------------------------------------------------------------------- #
# Known-answer fixtures (independently hand-computed)
# --------------------------------------------------------------------------- #
def _block(shape: Tuple[int, int], r0: int, r1: int, c0: int, c1: int) -> np.ndarray:
    arr = np.zeros(shape, dtype=np.uint8)
    arr[r0:r1, c0:c1] = 1
    return arr


def known_answer_cases() -> List[Dict[str, Any]]:
    """Small masks whose metrics can be computed by hand.

    Each entry states the expected value and the arithmetic that produces it, so
    a regression in the metric engine fails against a stated derivation rather
    than against a previously recorded output.
    """
    sq = (4, 4)
    identical = _block(sq, 1, 3, 1, 3)
    shifted = _block(sq, 1, 3, 2, 4)          # same block moved one column right
    cases: List[Dict[str, Any]] = [
        {"name": "identical_2x2_block", "gt": identical, "pred": identical,
         "expect": {"dice": 1.0, "iou": 1.0, "precision": 1.0, "recall": 1.0,
                    "hd95": 0.0, "tp": 4, "fp": 0, "fn": 0, "tn": 12},
         "derivation": "tp=4 fp=0 fn=0 -> dice=8/8"},
        {"name": "shifted_one_pixel", "gt": identical, "pred": shifted,
         "expect": {"dice": 0.5, "iou": 1.0 / 3.0, "precision": 0.5, "recall": 0.5,
                    "hd95": 1.0, "tp": 2, "fp": 2, "fn": 2, "tn": 10},
         "derivation": "tp=2 fp=2 fn=2 -> dice=4/8=0.5; iou=2/6=1/3; surfaces are "
                       "1 px apart so every pooled surface distance is 0 or 1"},
        {"name": "gt_empty_pred_empty", "gt": np.zeros(sq, np.uint8),
         "pred": np.zeros(sq, np.uint8),
         "expect": {"dice": 1.0, "iou": 1.0, "hd95_valid": False,
                    "hd95_invalid_reason": "both_empty", "empty_case": "gt_empty_pred_empty"},
         "derivation": "vacuous agreement is 1.0 by the declared convention"},
        {"name": "gt_empty_pred_nonempty", "gt": np.zeros(sq, np.uint8),
         "pred": _block(sq, 1, 3, 1, 3),
         "expect": {"dice": 0.0, "iou": 0.0, "precision": 0.0,
                    "empty_case": "gt_empty_pred_nonempty", "empty_gt_false_positive": True},
         "derivation": "tp=0 fp=4 fn=0 -> dice=0/8=0; recall undefined"},
        {"name": "gt_nonempty_pred_empty", "gt": _block(sq, 1, 3, 1, 3),
         "pred": np.zeros(sq, np.uint8),
         "expect": {"dice": 0.0, "iou": 0.0, "recall": 0.0,
                    "hd95_invalid_reason": "empty_prediction",
                    "empty_case": "gt_nonempty_pred_empty"},
         "derivation": "tp=0 fp=0 fn=4 -> dice=0/8=0; precision undefined"},
        {"name": "all_foreground", "gt": np.ones(sq, np.uint8), "pred": np.ones(sq, np.uint8),
         "expect": {"dice": 1.0, "iou": 1.0, "tn": 0, "all_foreground_gt": True},
         "derivation": "no background pixel exists; specificity is undefined"},
        {"name": "disconnected_prediction",
         "gt": np.concatenate([_block((4, 8), 1, 3, 1, 3), _block((4, 8), 1, 3, 5, 7)], axis=1),
         "pred": np.concatenate([_block((4, 8), 1, 3, 1, 3), _block((4, 8), 1, 3, 5, 7)], axis=1),
         "expect": {"dice": 1.0, "hd95": 0.0, "non_square": True},
         "derivation": "two components, both exact -> 1.0; 4x8 is non-square"},
        {"name": "non_square_shape", "gt": _block((3, 5), 1, 2, 1, 4),
         "pred": _block((3, 5), 1, 2, 1, 4),
         "expect": {"dice": 1.0, "non_square": True, "height": 3, "width": 5},
         "derivation": "3x5 has no square assumption anywhere in the pipeline"},
    ]
    return cases


def verify_known_answers(*, tol: float = 1e-6) -> Dict[str, Any]:
    """Run the fixtures and compare against the stated expectations.

    ``tol`` is 1e-6 because the engine applies the declared ``eps = 1e-7`` inside
    every ratio, so a hand-computed exact fraction differs by at most ~1e-7.  The
    expected values themselves remain the independently derived fractions — they
    are not restated as epsilon-shifted numbers.
    """
    failures: List[str] = []
    results = []
    for case in known_answer_cases():
        record = score_prediction(sample_id=case["name"], domain="KUB", task_id=3,
                                  final_probability=np.asarray(case["pred"], np.float32),
                                  ground_truth=case["gt"], on_non_finite="raise")
        for key, expected in case["expect"].items():
            got = record.get(key)
            if isinstance(expected, bool) or isinstance(got, bool):
                ok = bool(got) == bool(expected)
            elif expected is None:
                ok = got is None
            elif isinstance(expected, str):
                ok = str(got) == expected
            else:
                ok = got is not None and abs(float(got) - float(expected)) <= tol
            if not ok:
                failures.append(f"{case['name']}.{key}: expected {expected!r}, got {got!r}")
        results.append({"name": case["name"], "derivation": case["derivation"],
                        "dice": record["dice"], "iou": record["iou"], "hd95": record["hd95"],
                        "empty_case": record["empty_case"]})
    return {"cases": len(results), "results": results, "failures": failures,
            "all_match": not failures,
            "metric_implementation_version": P.METRIC_IMPLEMENTATION_VERSION}


__all__ = ["MetricError", "NonFiniteProbabilityError", "ShapeMismatchError",
           "aggregate_records", "hd95_with_units", "known_answer_cases",
           "pooled_metrics", "score_prediction", "verify_known_answers"]
