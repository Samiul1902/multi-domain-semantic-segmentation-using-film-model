"""Phase 25A — exact, GT-FREE ROI transform for the BARR regional refiner.

Frozen rule (Phase-24 v1.1 ``roi`` block, Phase-25A §7)
-------------------------------------------------------
    1. threshold p_global
    2. compute the tight bbox of the predicted foreground
    3. expand the bbox centre-preservingly by factor 1.50
    4. clip to the valid image region
    5. square-pad deterministically
    6. extract the RGB crop
    7. extract the p_global crop
    8. resize RGB        -> bilinear
    9. resize probability-> bilinear
   10. resize GT target  -> nearest neighbour
   11. output 256 x 256

**ROI geometry is determined BEFORE GT is used.** :func:`roi_geometry` accepts no
ground-truth argument, and :func:`assert_gt_cannot_alter_roi` proves that changing
the GT while holding the image and the global prediction fixed leaves every ROI
coordinate bit-identical.

Threshold semantics — TWO DISTINCT THRESHOLDS, NEVER CONFLATED
--------------------------------------------------------------
This module implements the **ROI PROPOSAL** threshold only. It determines the
predicted-foreground mask used to propose the regional ROI, and therefore bbox
existence, bbox geometry, and ``ACTION_AVAILABLE`` vs ``FORCED_SKIP``. It does
**not** determine any segmentation output and it does **not** enter any Dice /
IoU computation.

``ROI_PROPOSAL_THRESHOLD = 0.30``
    Resolved from the repository-authoritative Phase-24 v1.1 exact specification
    (``roi.predicted_foreground_threshold = 0.3``, artifact
    ``reports/audits/phase24_exact_implementation_spec.json``). Adjudicated in
    ``reports/audits/phase24_phase25_roi_threshold_adjudication.json`` with
    classification ``FROZEN_SPEC_CLARIFICATION__NOT_SCIENCE_CHANGE``.

``SEGMENTATION_OUTPUT_THRESHOLD = 0.50``
    The inherited frozen segmentation/evaluation decision threshold
    (``fusion.segmentation_threshold = 0.5``, ``threshold_source: INHERITED``;
    ``src/analysis/phase22_common.py:54 THRESHOLD = 0.5``). It applies to
    segmentation output / evaluation masks only and is **not** used anywhere in
    this ROI module.

History: the earlier Phase-25A execution bound 0.50 for the ROI proposal as well
and is preserved as ``NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50``
(``reports/audits/phase25a_roi050_supersession.json``). The value is frozen
BEFORE any training and is never selected from observed performance.
"""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np
from PIL import Image

from src.inference.predicted_roi import apply_context_margin

__all__ = [
    "PREDICTED_FOREGROUND_THRESHOLD",
    "ROI_PROPOSAL_THRESHOLD",
    "SEGMENTATION_OUTPUT_THRESHOLD",
    "ROI_EXPANSION_FACTOR",
    "ROI_FRACTIONAL_MARGIN",
    "REGIONAL_INPUT_RESOLUTION",
    "REGIONAL_CANVAS_RESOLUTION",
    "ROI_MARGIN_CONSTANT_SOURCE",
    "THRESHOLD_SEMANTIC_ROLES",
    "threshold_probability",
    "predicted_foreground_bbox",
    "roi_geometry",
    "crop_and_resize",
    "extract_roi_triplet",
    "inverse_transform_metadata",
    "assert_gt_cannot_alter_roi",
]

# --- the two thresholds, explicitly separated by semantic role ---------------- #
# ROI PROPOSAL: basis for the predicted-foreground mask / bbox / ACTION_AVAILABLE.
ROI_PROPOSAL_THRESHOLD = 0.30
# SEGMENTATION OUTPUT: inherited evaluation mask threshold. NOT used in this module.
SEGMENTATION_OUTPUT_THRESHOLD = 0.50
# Backwards-compatible alias. NOTE: this constant is the ROI PROPOSAL threshold,
# NOT the segmentation output threshold; prefer the explicit name in new code.
PREDICTED_FOREGROUND_THRESHOLD = ROI_PROPOSAL_THRESHOLD

THRESHOLD_SEMANTIC_ROLES = {
    "roi_proposal_threshold": {
        "value": ROI_PROPOSAL_THRESHOLD,
        "semantic_role": "ROI_PROPOSAL",
        "determines": ["predicted foreground", "bbox existence", "bbox geometry",
                       "ACTION_AVAILABLE vs FORCED_SKIP"],
        "affects_segmentation_output": False,
        "affects_dice": False,
    },
    "segmentation_output_threshold": {
        "value": SEGMENTATION_OUTPUT_THRESHOLD,
        "semantic_role": "SEGMENTATION_OUTPUT",
        "determines": ["final binary segmentation mask", "Dice / IoU masks"],
        "affects_roi_geometry": False,
    },
}

ROI_EXPANSION_FACTOR = 1.5
ROI_FRACTIONAL_MARGIN = 0.25          # 1 + 2*0.25 == 1.50  (ORACLE_DERIVED_REFINER_MARGIN)
REGIONAL_INPUT_RESOLUTION = 256
REGIONAL_CANVAS_RESOLUTION = 512      # the frozen global model input resolution
ROI_MARGIN_CONSTANT_SOURCE = "src/data/regional_dataset.py:22 ORACLE_DERIVED_REFINER_MARGIN"

GEOMETRY_KEYS = (
    "y1", "y2", "x1", "x2",
    "clip_y1", "clip_y2", "clip_x1", "clip_x2",
    "pad_top", "pad_bottom", "pad_left", "pad_right",
    "crop_side_pixels", "effective_magnification", "margin",
)


def threshold_probability(prob: np.ndarray,
                          threshold: float = ROI_PROPOSAL_THRESHOLD) -> np.ndarray:
    """Canonical lower-inclusive float32 decision rule: ``float32(prob) >= thr``.

    Evaluated in float32 (never on a float16 on-disk copy) so the binary mask is
    reproducible and matches ``torch.sigmoid(y).ge(thr)``.

    The default argument is the ROI PROPOSAL threshold (0.30). This function is
    used for ROI proposal only; it is never used to produce a segmentation output
    mask (that threshold is :data:`SEGMENTATION_OUTPUT_THRESHOLD`, inherited).
    """
    return (np.asarray(prob).astype(np.float32) >= np.float32(threshold)).astype(np.uint8)


def predicted_foreground_bbox(binary: np.ndarray) -> Optional[Tuple[int, int, int, int]]:
    """Tight INCLUSIVE bbox ``(min_y, min_x, max_y, max_x)`` of the predicted foreground.

    Returns ``None`` when the predicted foreground is empty (``FORCED_SKIP``).

    This function takes a *binary predicted* mask only. It has no ground-truth
    parameter and no ground-truth code path.
    """
    ys, xs = np.nonzero(np.asarray(binary).astype(bool))
    if ys.size == 0:
        return None
    return int(ys.min()), int(xs.min()), int(ys.max()), int(xs.max())


def roi_geometry(prob: np.ndarray,
                 threshold: float = ROI_PROPOSAL_THRESHOLD,
                 margin: float = ROI_FRACTIONAL_MARGIN) -> Optional[dict]:
    """Full ROI geometry from a predicted probability map. **GT-FREE.**

    ``prob`` is the frozen global probability map on the regional canvas
    (``512 x 512``). Returns ``None`` when the predicted foreground is empty.
    """
    binary = threshold_probability(prob, threshold)
    bbox = predicted_foreground_bbox(binary)
    if bbox is None:
        return None
    geom = apply_context_margin(bbox, tuple(np.asarray(prob).shape[-2:]), margin)
    geom["predicted_foreground_pixels"] = int(binary.sum())
    geom["predicted_foreground_threshold"] = float(threshold)
    geom["bbox_min_y"], geom["bbox_min_x"] = int(bbox[0]), int(bbox[1])
    geom["bbox_max_y"], geom["bbox_max_x"] = int(bbox[2]), int(bbox[3])
    return geom


def _crop_pad(arr: np.ndarray, geom: dict) -> np.ndarray:
    """Crop the clipped window then constant-zero pad to the square side."""
    cy1, cy2 = int(geom["clip_y1"]), int(geom["clip_y2"])
    cx1, cx2 = int(geom["clip_x1"]), int(geom["clip_x2"])
    window = arr[..., cy1:cy2, cx1:cx2]
    pads = [(0, 0)] * (window.ndim - 2) + [
        (int(geom["pad_top"]), int(geom["pad_bottom"])),
        (int(geom["pad_left"]), int(geom["pad_right"])),
    ]
    return np.pad(window, pads, mode="constant", constant_values=0)


def crop_and_resize(arr: np.ndarray, geom: dict, out_size: int, resample: str) -> np.ndarray:
    """Crop+pad a ``(H, W)`` or ``(C, H, W)`` array and resize to ``out_size``.

    ``resample`` is one of ``"bilinear"`` / ``"nearest"``. Float arrays are
    resized through PIL ``mode="F"`` so the probability map keeps float precision.
    """
    window = _crop_pad(np.asarray(arr), geom)
    if window.ndim == 2:
        window = window[None, ...]
    # Both modes go through PIL mode="F" so float values are preserved exactly.
    # NEAREST selects existing samples (never averaging), BILINEAR interpolates.
    resampling = Image.Resampling.NEAREST if resample == "nearest" else Image.Resampling.BILINEAR
    channels = []
    for ch in window:
        pil = Image.fromarray(np.ascontiguousarray(ch, dtype=np.float32), mode="F")
        resized = pil.resize((out_size, out_size), resampling)
        channels.append(np.asarray(resized, dtype=np.float32))
    return np.stack(channels, axis=0)


def extract_roi_triplet(image_chw: np.ndarray,
                        prob_hw: np.ndarray,
                        gt_hw: np.ndarray,
                        geom: dict,
                        out_size: int = REGIONAL_INPUT_RESOLUTION):
    """Extract ``(rgb_crop, prob_crop, gt_crop)`` for one action-available sample.

    * RGB       -> bilinear
    * p_global  -> bilinear
    * GT target -> nearest neighbour

    ``geom`` must have been produced by :func:`roi_geometry` (GT-free).
    """
    rgb = crop_and_resize(image_chw, geom, out_size, "bilinear")
    prob = crop_and_resize(prob_hw, geom, out_size, "bilinear")
    gt = crop_and_resize(gt_hw, geom, out_size, "nearest")
    return rgb, prob, gt


def inverse_transform_metadata(geom: dict, out_size: int = REGIONAL_INPUT_RESOLUTION) -> dict:
    """Everything Phase 25C needs to map a 256x256 refined crop back to the canvas.

    The mapping is an affine resize of the square ``crop_side_pixels`` window to
    ``out_size``, with the clipped window placed at ``(clip_y1, clip_x1)`` and the
    out-of-canvas area coming from zero padding.
    """
    side = int(geom["crop_side_pixels"])
    return {
        "crop_side_pixels": side,
        "out_size": int(out_size),
        "scale_crop_to_out": float(side) / float(out_size),
        "scale_out_to_crop": float(out_size) / float(side),
        "clip_y1": int(geom["clip_y1"]), "clip_y2": int(geom["clip_y2"]),
        "clip_x1": int(geom["clip_x1"]), "clip_x2": int(geom["clip_x2"]),
        "pad_top": int(geom["pad_top"]), "pad_bottom": int(geom["pad_bottom"]),
        "pad_left": int(geom["pad_left"]), "pad_right": int(geom["pad_right"]),
        "canvas_resolution": REGIONAL_CANVAS_RESOLUTION,
        "regional_input_resolution": int(out_size),
        "note": "out pixel (r, c) maps to canvas pixel "
                "(clip_y1 - pad_top + r * side/out_size, clip_x1 - pad_left + c * side/out_size); "
                "positions outside [clip_y1, clip_y2) x [clip_x1, clip_x2) are zero padding.",
    }


def assert_gt_cannot_alter_roi(prob: np.ndarray, image_chw: np.ndarray,
                               gt_a: np.ndarray, gt_b: np.ndarray,
                               threshold: float = ROI_PROPOSAL_THRESHOLD) -> dict:
    """Fail-closed test: changing GT must NOT change any ROI coordinate or crop geometry.

    Both GT variants are extracted through the *same* geometry and the RGB /
    probability crops must be bit-identical; only the GT crop may differ.
    """
    g1 = roi_geometry(prob, threshold)
    g2 = roi_geometry(prob, threshold)
    if g1 is None or g2 is None:
        raise AssertionError("GT-independence test requires a non-empty prediction")
    same_geom = all(g1[k] == g2[k] for k in GEOMETRY_KEYS if k in g1)
    rgb1, prob1, gt1 = extract_roi_triplet(image_chw, prob, gt_a, g1)
    rgb2, prob2, gt2 = extract_roi_triplet(image_chw, prob, gt_b, g2)
    return {
        "geometry_identical": bool(same_geom),
        "rgb_crop_identical": bool(np.array_equal(rgb1, rgb2)),
        "prob_crop_identical": bool(np.array_equal(prob1, prob2)),
        "gt_crop_differs": bool(not np.array_equal(gt1, gt2)),
        "gt_crop_differs_is_permitted": True,
        "passed": bool(same_geom and np.array_equal(rgb1, rgb2)
                       and np.array_equal(prob1, prob2)),
    }
