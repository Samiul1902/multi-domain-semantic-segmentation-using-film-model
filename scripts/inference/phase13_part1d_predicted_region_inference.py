"""PHASE-13 PART-1D — predicted-region segmentation inference module (STATIC).

Read-only helpers for the frozen PREDICTED_REGION_FLOAT_GLOBAL_RETAINED variant.

This module defines functions only. Importing it performs NO model construction,
NO CUDA request, NO image inference and NO proposal generation. The Part 1D-B
execution driver is deliberately NOT invoked in Part 1D-A.

Frozen semantics
----------------
* Proposal geometry from Part-1C already encodes the frozen margin-0.20 support.
  A SECOND margin must NEVER be applied.
* Regional restore is FLOAT bilinear with align_corners=False. No uint8
  quantisation, no legacy PIL restoration.
* Overlapping regional crops compose by MAXIMUM regional probability.
* Fusion is REPLACEMENT inside U_pred: P(x) = R(x) if U_pred(x) else G(x).
  max(G, R) inside the support is FORBIDDEN.
* Threshold 0.5 is applied only AFTER complete native-space fusion.
* GT never influences proposal generation or fusion.

No training. No optimizer. No gradients. TEST never constructed.
"""
from __future__ import annotations

import json
from typing import Dict, List, Sequence, Tuple

import numpy as np

PRIMARY_VARIANT = "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED"
REGIONAL_RESOLUTION = 512
THRESHOLD = 0.5
PROPOSAL_THRESHOLD = 0.10
PROPOSAL_MARGIN = 0.20
PROPOSAL_TOP_K = 5
PROPOSAL_NMS_IOU = 0.30
ORACLE_MARGIN = 0.25

MODELS: Tuple[str, ...] = ("unet", "attention_unet", "unetpp", "deeplabv3plus")
MODEL_CHECKPOINTS: Dict[str, str] = {
    "unet": "phase9_kub_unet_baseline_seed42_512_clean_v3",
    "attention_unet": "phase10_kub_attention_unet_seed42_512_clean_v3",
    "unetpp": "phase10_kub_unetpp_seed42_512_clean_v3",
    "deeplabv3plus": "phase10_kub_deeplabv3plus_seed42_512_clean_v3",
}

EXPECTED_CASES = 103
EXPECTED_COMPONENTS = 152
EXPECTED_STRATA = {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16}
EXPECTED_TOTAL_PROPOSALS = 494
EXPECTED_CASE_MODEL_ROWS = EXPECTED_CASES * len(MODELS)   # 412
EXPECTED_COMPONENT_MODEL_ROWS = EXPECTED_COMPONENTS * len(MODELS)  # 608


# ---------------------------------------------------------------------------
# Proposal geometry
# ---------------------------------------------------------------------------
def parse_proposal_geometry(case_row) -> List[dict]:
    """Parse the COMPLETE frozen Part-1C crop geometry for one case.

    The stored geometry ALREADY includes the frozen margin-0.20 expansion. This
    function performs NO additional margin operation.

    Full square/padding fields are preserved (not reduced to clip coords):
    y1/y2/x1/x2, clip_*, pad_*, crop_side, effective_magnification, margin.
    ``crop_side_pixels`` is normalised to ``crop_side`` as a lossless alias.
    """
    raw = case_row["proposal_crop_geometry"]
    geometry = json.loads(raw) if isinstance(raw, str) else list(raw)
    out = []
    for item in geometry:
        record = dict(item)
        if "crop_side" not in record:
            record["crop_side"] = int(record["crop_side_pixels"])
        record["crop_side"] = int(record["crop_side"])
        for key in ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
                    "pad_top", "pad_bottom", "pad_left", "pad_right"):
            record[key] = int(record[key])
        out.append(record)
    return out


def assert_geometry_invariants(geom: dict, native_shape) -> None:
    """Fail loudly if a frozen geometry record violates the square/pad contract."""
    h, w = int(native_shape[0]), int(native_shape[1])
    side = int(geom["crop_side"])
    if geom["y2"] - geom["y1"] != side or geom["x2"] - geom["x1"] != side:
        raise ValueError(f"square side mismatch: {geom}")
    if geom["clip_y1"] < 0 or geom["clip_x1"] < 0:
        raise ValueError(f"negative clip origin: {geom}")
    if geom["clip_y2"] > h or geom["clip_x2"] > w:
        raise ValueError(f"clip exceeds native bounds: {geom}")
    if geom["clip_y2"] - geom["clip_y1"] != side - geom["pad_top"] - geom["pad_bottom"]:
        raise ValueError(f"vertical pad invariant violated: {geom}")
    if geom["clip_x2"] - geom["clip_x1"] != side - geom["pad_left"] - geom["pad_right"]:
        raise ValueError(f"horizontal pad invariant violated: {geom}")
    if abs(float(geom["margin"]) - 0.20) > 1e-12:
        raise ValueError(f"margin is not the frozen 0.20: {geom['margin']}")


def prepare_regional_crop_512(native_gray: np.ndarray, geom: dict) -> np.ndarray:
    """Phase-12-equivalent input crop: valid -> zero-pad to square -> 512 BILINEAR -> [0,1].

    Reproduces ``phase12_oracle_inference.crop_tensor`` semantics exactly: the
    valid native region is zero-padded to the FULL square side and then resized
    to 512x512 with PIL BILINEAR. It never resizes the valid region directly.
    """
    from PIL import Image

    side = int(geom["crop_side"])
    valid = native_gray[geom["clip_y1"]:geom["clip_y2"], geom["clip_x1"]:geom["clip_x2"]]
    padded = np.pad(valid,
                    ((geom["pad_top"], geom["pad_bottom"]),
                     (geom["pad_left"], geom["pad_right"])),
                    mode="constant", constant_values=0)
    if padded.shape != (side, side):
        raise ValueError(f"padded shape {padded.shape} != crop_side {side}")
    pil = Image.fromarray(padded).resize((REGIONAL_RESOLUTION, REGIONAL_RESOLUTION),
                                         Image.Resampling.BILINEAR)
    return (np.asarray(pil, dtype=np.float32).copy() / 255.0).astype(np.float32)


def restore_probability_to_native(prob_512: np.ndarray, geom: dict,
                                  native_shape) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
    """Phase-12-equivalent FLOAT restore: 512 -> FULL square -> strip pad -> place.

    Returns ``(valid_crop, (clip_y1, clip_x1, clip_y2, clip_x2))``. FLOAT bilinear
    only, align_corners=False — no uint8 quantisation, no legacy PIL probability
    path, and NEVER a direct 512 -> clipped-rectangle resize.
    """
    import torch

    side = int(geom["crop_side"])
    t = torch.from_numpy(np.ascontiguousarray(prob_512, dtype=np.float32))[None, None]
    r = torch.nn.functional.interpolate(t, size=(side, side), mode="bilinear",
                                        align_corners=False)
    prob_square = r[0, 0].numpy().astype(np.float32)
    p_top, p_bot = int(geom["pad_top"]), side - int(geom["pad_bottom"])
    p_left, p_right = int(geom["pad_left"]), side - int(geom["pad_right"])
    valid = prob_square[p_top:p_bot, p_left:p_right]
    expected = (geom["clip_y2"] - geom["clip_y1"], geom["clip_x2"] - geom["clip_x1"])
    if valid.shape != expected:
        raise ValueError(f"restored valid extent {valid.shape} != clipped extent {expected}")
    return valid.astype(np.float32), (
        geom["clip_y1"], geom["clip_x1"], geom["clip_y2"], geom["clip_x2"]
    )


def restore_probability_to_full_native(prob_512: np.ndarray, geom: dict,
                                       native_shape) -> np.ndarray:
    """Phase-12 ``restore_float`` shape: full native array, zeros outside the clip."""
    h, w = int(native_shape[0]), int(native_shape[1])
    valid, (y1, x1, y2, x2) = restore_probability_to_native(prob_512, geom, native_shape)
    full = np.zeros((h, w), dtype=np.float32)
    full[y1:y2, x1:x2] = valid
    return full


def proposal_support_mask(geometry: Sequence[dict], native_shape) -> np.ndarray:
    """U_pred: union of the clipped native proposal crop rectangles.

    Determined solely by frozen GT-free proposal geometry. Never derived from GT,
    heatmap threshold pixels, regional output or component bboxes.
    """
    h, w = int(native_shape[0]), int(native_shape[1])
    support = np.zeros((h, w), dtype=bool)
    for g in geometry:
        y1 = max(0, min(h, int(g["clip_y1"])))
        y2 = max(0, min(h, int(g["clip_y2"])))
        x1 = max(0, min(w, int(g["clip_x1"])))
        x2 = max(0, min(w, int(g["clip_x2"])))
        if y2 > y1 and x2 > x1:
            support[y1:y2, x1:x2] = True
    return support


# ---------------------------------------------------------------------------
# Regional composition
# ---------------------------------------------------------------------------
def regional_probability_native(regional_probs: Sequence[np.ndarray],
                                geometry_list: Sequence[dict],
                                native_shape) -> np.ndarray:
    """R(x): MAXIMUM regional probability among crops covering each pixel.

    Each 512 probability map is restored through the Phase-12 square/padding path
    (512 -> full square -> strip pad -> place at clip coords) before the maximum
    is taken. The maximum is over REGIONAL predictions only.
    """
    h, w = int(native_shape[0]), int(native_shape[1])
    r = np.zeros((h, w), dtype=np.float32)
    for prob, geometry in zip(regional_probs, geometry_list):
        valid, (y1, x1, y2, x2) = restore_probability_to_native(
            prob, geometry, native_shape)
        if valid.size == 0:
            continue
        window = r[y1:y2, x1:x2]
        np.maximum(window, valid, out=window)
    return r


# ---------------------------------------------------------------------------
# Fusion
# ---------------------------------------------------------------------------
def fuse_global_retained(global_prob: np.ndarray, regional_prob: np.ndarray,
                         support: np.ndarray) -> np.ndarray:
    """P(x) = R(x) if U_pred(x) else G(x).

    Regional REPLACEMENT inside the support. ``max(G, R)`` inside the support is
    explicitly forbidden and never performed here.
    """
    g = np.asarray(global_prob, dtype=np.float32)
    r = np.asarray(regional_prob, dtype=np.float32)
    if g.shape != r.shape or g.shape != support.shape:
        raise ValueError(f"shape mismatch: G{g.shape} R{r.shape} U{support.shape}")
    fused = g.copy()
    fused[support] = r[support]
    return fused


def binarize(fused_prob: np.ndarray, threshold: float = THRESHOLD) -> np.ndarray:
    """Threshold AFTER complete native-space fusion."""
    return np.asarray(fused_prob, dtype=np.float32) >= float(threshold)


# ---------------------------------------------------------------------------
# Descriptive retention
# ---------------------------------------------------------------------------
def retention_dice(d_pred: float, d_oracle: float, d_global: float):
    """(D_pred - D_global) / (D_oracle - D_global).

    Returns ``None`` (N/A) when the oracle gain denominator is not > 0. NEVER
    clipped to [0, 1]; negative and >1 values are preserved.
    """
    denominator = float(d_oracle) - float(d_global)
    if not denominator > 0.0:
        return None
    return (float(d_pred) - float(d_global)) / denominator


def oracle_gap_dice(d_pred: float, d_oracle: float) -> float:
    return float(d_pred) - float(d_oracle)


def retention_generic(pred: float, oracle: float, base: float):
    """Generic descriptive gain retention; None when denominator invalid."""
    denominator = float(oracle) - float(base)
    if not denominator > 0.0:
        return None
    return (float(pred) - float(base)) / denominator
