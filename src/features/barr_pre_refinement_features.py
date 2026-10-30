"""Canonical GT-free pre-refinement feature extraction -- RA-MedFiLM-BARR.

Implements EXACTLY the frozen Phase-24 router-feature specification revision
``ra_medfilm_barr_narrowed_v1_2``:

  * three frozen Global MedFiLM feature taps (bridge / decoder2 / decoder1)
  * per tap, a GLOBAL and a ROI-aware pooled native vector  -> 6 logical vectors
  * ``DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`` C -> 32 channel reduction
  * ten prediction-only scalar descriptors
  * exact 202-D numeric ordering

Nothing here is trained.  Nothing here reads a GT mask for feature construction,
runs the regional refiner, the benefit router or the post-safety module, or
computes any paired-gain / DeltaDice quantity.

Public API (single source of truth for module, driver and notebook)
------------------------------------------------------------------
    TAPS, GROUP_ORDER, SCALAR_ORDER, FEATURE_ORDER
    channel_bins(C, K=32)                    -> list[(start, end)]
    adaptive_channel_reduce(v, K=32)         -> np.float32[K]
    map_roi_to_grid(x0, y0, x1, y1, S)       -> tuple[int, int, int, int]
    pool_global(F)                           -> np.float32[C]
    pool_roi(F, roi)                         -> np.float32[C]
    extract_tap_features(cmaps, roi)         -> np.float32[192]
    extract_scalars(P, roi_row)              -> np.float32[10]
    build_feature_vector(cmaps, P, roi_row)  -> np.float32[202]
    scalar_definitions()                     -> list[dict]
    feature_schema()                         -> list[dict]
"""
from __future__ import annotations

import math
from typing import Iterable, Mapping, Sequence

import numpy as np

# --------------------------------------------------------------------------- #
# Frozen constants
# --------------------------------------------------------------------------- #
CANVAS_RESOLUTION = 512
T_ROI = 0.30                  # ROI PROPOSAL threshold
T_SEG = 0.50                  # SEGMENTATION OUTPUT threshold
N_CANVAS_PIXELS = CANVAS_RESOLUTION * CANVAS_RESOLUTION
REDUCTION_K = 32
REDUCTION_OP = "DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1"

TAPS: tuple[str, ...] = ("bridge", "decoder2", "decoder1")
NATIVE_CHANNELS: dict[str, int] = {"bridge": 256, "decoder2": 48, "decoder1": 24}
# Feature-grid side of each tap inside the 512x512 global U-Net.
FEATURE_GRID: dict[str, int] = {"bridge": 32, "decoder2": 256, "decoder1": 512}

# Frozen six-vector order (index ranges are half-open).
GROUP_ORDER: tuple[tuple[str, str, int, int], ...] = (
    ("bridge_global", "bridge", "GLOBAL", 0),
    ("bridge_roi", "bridge", "ROI", 32),
    ("decoder2_global", "decoder2", "GLOBAL", 64),
    ("decoder2_roi", "decoder2", "ROI", 96),
    ("decoder1_global", "decoder1", "GLOBAL", 128),
    ("decoder1_roi", "decoder1", "ROI", 160),
)

SCALAR_ORDER: tuple[str, ...] = (
    "entropy_proxy_mean",
    "frac_prob_within_0p05_of_boundary",
    "frac_prob_within_0p02_of_boundary",
    "mean_boundary_margin",
    "pred_foreground_fraction",
    "pred_foreground_pixels",
    "pred_roi_exists",
    "pred_empty",
    "predicted_roi_area_fraction",
    "predicted_roi_side",
)

DEEP_DIM = 6 * REDUCTION_K          # 192
SCALAR_DIM = len(SCALAR_ORDER)      # 10
NUMERIC_DIM = DEEP_DIM + SCALAR_DIM  # 202

# Scalar index map for readability.
_IDX = {name: DEEP_DIM + i for i, name in enumerate(SCALAR_ORDER)}


# --------------------------------------------------------------------------- #
# RF-1 -- deterministic C -> 32 reduction
# --------------------------------------------------------------------------- #
def channel_bins(C: int, K: int = REDUCTION_K) -> list[tuple[int, int]]:
    """Half-open adaptive bins: ``start_j = floor(j*C/K)``, ``end_j = ceil((j+1)*C/K)``.

    When ``C < K`` the bins overlap; that is intended by the frozen operation.
    """
    C, K = int(C), int(K)
    if C < 1:
        raise ValueError("C must be >= 1")
    return [(math.floor(j * C / K), math.ceil((j + 1) * C / K)) for j in range(K)]


def adaptive_channel_reduce(v: np.ndarray, K: int = REDUCTION_K) -> np.ndarray:
    """``DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`` on a native vector.

    ``z[j] = mean(v[start_j:end_j])`` with the frozen floor/ceil bins.
    Zero trainable parameters; every source channel is used.
    """
    v = np.asarray(v, dtype=np.float32).reshape(-1)
    C = int(v.shape[0])
    bins = channel_bins(C, K)
    out = np.empty(K, dtype=np.float32)
    for j, (s, e) in enumerate(bins):
        if not (0 <= s < C and 1 <= e <= C and e > s):
            raise ValueError(f"invalid bin j={j}: ({s},{e}) for C={C}")
        out[j] = np.float32(v[s:e].mean(dtype=np.float64))
    return out


# --------------------------------------------------------------------------- #
# RF-2 -- ROI -> feature-grid mapping
# --------------------------------------------------------------------------- #
def map_roi_to_grid(x0: int, y0: int, x1: int, y1: int, S: int) -> tuple[int, int, int, int]:
    """Image-space half-open ROI ``[x0,x1) x [y0,y1)`` on the 512 canvas ->
    feature-grid half-open window ``(fx0, fy0, fx1, fy1)`` for a grid of side ``S``.

    ``start = floor(...)``, ``end = ceil(...)``, then clip.  External crop
    padding is outside ``[0,512)`` and therefore contributes no feature cells.
    """
    fx0 = math.floor(x0 * S / CANVAS_RESOLUTION)
    fy0 = math.floor(y0 * S / CANVAS_RESOLUTION)
    fx1 = math.ceil(x1 * S / CANVAS_RESOLUTION)
    fy1 = math.ceil(y1 * S / CANVAS_RESOLUTION)
    fx0 = min(max(fx0, 0), S - 1)
    fy0 = min(max(fy0, 0), S - 1)
    fx1 = min(max(fx1, fx0 + 1), S)
    fy1 = min(max(fy1, fy0 + 1), S)
    return fx0, fy0, fx1, fy1


def pool_global(F: np.ndarray) -> np.ndarray:
    """``v_global[c] = mean over all spatial positions of F[c,y,x]`` -> float32[C]."""
    F = np.asarray(F, dtype=np.float32)
    return F.mean(axis=(1, 2), dtype=np.float64).astype(np.float32)


def pool_roi(F: np.ndarray, roi: Sequence[int]) -> np.ndarray:
    """``v_roi[c] = mean over the mapped ROI cells`` -> float32[C].

    ``roi`` is the canonical half-open image-space ``(x0, y0, x1, y1)``.
    """
    F = np.asarray(F, dtype=np.float32)
    if F.ndim != 3:
        raise ValueError("F must be [C, Hf, Wf]")
    S = int(F.shape[-1])
    if int(F.shape[-2]) != S:
        raise ValueError("feature grid must be square")
    x0, y0, x1, y1 = (int(v) for v in roi)
    fx0, fy0, fx1, fy1 = map_roi_to_grid(x0, y0, x1, y1, S)
    win = F[:, fy0:fy1, fx0:fx1]
    if win.size == 0:
        raise RuntimeError("mapped ROI contains no feature cells (FAIL CLOSED)")
    return win.mean(axis=(1, 2), dtype=np.float64).astype(np.float32)


def extract_tap_features(cmaps: Mapping[str, np.ndarray],
                         roi: Sequence[int]) -> np.ndarray:
    """Six 32-D groups in the frozen order -> float32[192]."""
    parts: list[np.ndarray] = []
    for name, tap, scope, _ in GROUP_ORDER:
        F = cmaps[tap]
        native = pool_global(F) if scope == "GLOBAL" else pool_roi(F, roi)
        if native.shape[0] != NATIVE_CHANNELS[tap]:
            raise ValueError(f"{tap}: expected C={NATIVE_CHANNELS[tap]}, got {native.shape[0]}")
        parts.append(adaptive_channel_reduce(native, REDUCTION_K))
    out = np.concatenate(parts).astype(np.float32)
    if out.shape != (DEEP_DIM,):
        raise ValueError(f"deep block shape {out.shape} != ({DEEP_DIM},)")
    return out


# --------------------------------------------------------------------------- #
# RF-3 -- the ten closed-form scalar descriptors
# --------------------------------------------------------------------------- #
def scalar_block(P: np.ndarray, roi_row: Mapping[str, object]) -> np.ndarray:
    """Ten prediction-only scalars in the frozen order -> float32[10].

    ``P`` is the float32 512x512 global probability map.  ``roi_row`` supplies
    the canonical half-open ROI bounds and the crop support.
    """
    P = np.asarray(P, dtype=np.float32)
    if P.shape != (CANVAS_RESOLUTION, CANVAS_RESOLUTION):
        raise ValueError(f"P must be {CANVAS_RESOLUTION}x{CANVAS_RESOLUTION}, got {P.shape}")
    N = float(N_CANVAS_PIXELS)

    # 12.1 Shannon entropy proxy, normalised to bits.
    q = np.clip(P, 1e-7, 1.0 - 1e-7)
    h = -(q * np.log(q) + (1.0 - q) * np.log(1.0 - q)) / math.log(2.0)
    entropy_proxy_mean = np.float32(h.mean(dtype=np.float64))

    # 12.2/12.3 boundary-band fractions at t_seg = 0.50.
    d = np.abs(P - np.float32(T_SEG))
    frac_005 = np.float32(np.count_nonzero(d <= np.float32(0.05)) / N)
    frac_002 = np.float32(np.count_nonzero(d <= np.float32(0.02)) / N)

    # 12.4 mean boundary margin (NOT negated).
    mean_boundary_margin = np.float32(d.mean(dtype=np.float64))

    # 12.5-12.8 ROI proposal descriptors at t_roi = 0.30 (lower-inclusive float32).
    pred_foreground_pixels = np.float32(
        float(np.count_nonzero(P >= np.float32(T_ROI))))
    pred_foreground_fraction = np.float32(pred_foreground_pixels / N)
    pred_roi_exists = np.float32(1.0 if pred_foreground_pixels > 0 else 0.0)
    pred_empty = np.float32(1.0 - pred_roi_exists)

    # 12.9 SUPERVISOR-CORRECTED v1.2 area fraction: clipped in-canvas area.
    x0, x1 = int(roi_row["clip_x1"]), int(roi_row["clip_x2"])
    y0, y1 = int(roi_row["clip_y1"]), int(roi_row["clip_y2"])
    w_in = max(0, min(CANVAS_RESOLUTION, x1) - max(0, x0))
    h_in = max(0, min(CANVAS_RESOLUTION, y1) - max(0, y0))
    predicted_roi_area_fraction = np.float32((w_in * h_in) / float(N_CANVAS_PIXELS))

    # 12.10 crop support BEFORE resize (may legitimately exceed 512).
    predicted_roi_side = np.float32(float(roi_row["crop_side_pixels"]))

    out = np.array([
        entropy_proxy_mean,
        frac_005,
        frac_002,
        mean_boundary_margin,
        pred_foreground_fraction,
        pred_foreground_pixels,
        pred_roi_exists,
        pred_empty,
        predicted_roi_area_fraction,
        predicted_roi_side,
    ], dtype=np.float32)
    if out.shape != (SCALAR_DIM,):
        raise ValueError(f"scalar block shape {out.shape} != ({SCALAR_DIM},)")
    return out


def build_feature_vector(cmaps: Mapping[str, np.ndarray], P: np.ndarray,
                         roi_row: Mapping[str, object]) -> np.ndarray:
    """Full frozen 202-D numeric vector for one sample."""
    deep = extract_tap_features(cmaps, (int(roi_row["clip_x1"]), int(roi_row["clip_y1"]),
                                        int(roi_row["clip_x2"]), int(roi_row["clip_y2"])))
    scal = scalar_block(P, roi_row)
    vec = np.concatenate([deep, scal]).astype(np.float32)
    if vec.shape != (NUMERIC_DIM,):
        raise ValueError(f"feature vector shape {vec.shape} != ({NUMERIC_DIM},)")
    return vec


# --------------------------------------------------------------------------- #
# Reporting helpers (single source of truth for driver + notebook)
# --------------------------------------------------------------------------- #
def feature_schema() -> list[dict]:
    """One row per numeric feature column, in frozen order."""
    rows: list[dict] = []
    for name, tap, scope, start in GROUP_ORDER:
        for j in range(REDUCTION_K):
            rows.append({
                "feature_index": start + j,
                "feature_name": f"{name}_{j:02d}",
                "feature_group": name,
                "source_tap": tap,
                "pooling_scope": scope,
                "native_channels": NATIVE_CHANNELS[tap],
                "reduction_op": REDUCTION_OP,
                "dtype": "float32",
                "uses_GT": False,
                "pre_refinement": True,
            })
    for sname in SCALAR_ORDER:
        rows.append({
            "feature_index": _IDX[sname],
            "feature_name": sname,
            "feature_group": "scalars",
            "source_tap": "P_global",
            "pooling_scope": "SCALAR",
            "native_channels": "",
            "reduction_op": "",
            "dtype": "float32",
            "uses_GT": False,
            "pre_refinement": True,
        })
    assert len(rows) == NUMERIC_DIM, len(rows)
    return rows


def scalar_definitions() -> list[dict]:
    """Closed-form definitions of the ten scalars, with governing threshold roles."""
    return [
        {"feature_index": _IDX["entropy_proxy_mean"], "feature_name": "entropy_proxy_mean",
         "threshold_role": "THRESHOLD_FREE", "threshold_value": None,
         "formula": "mean over all N pixels of -[q*ln q + (1-q)*ln(1-q)]/ln 2, q = clip(P, 1e-7, 1-1e-7)",
         "units": "dimensionless in [0,1]", "input_source": "P (global probability map)",
         "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["frac_prob_within_0p05_of_boundary"],
         "feature_name": "frac_prob_within_0p05_of_boundary",
         "threshold_role": "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", "threshold_value": T_SEG,
         "formula": "(1/N) * sum 1[|P - 0.50| <= 0.05]", "units": "fraction in [0,1]",
         "input_source": "P", "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["frac_prob_within_0p02_of_boundary"],
         "feature_name": "frac_prob_within_0p02_of_boundary",
         "threshold_role": "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", "threshold_value": T_SEG,
         "formula": "(1/N) * sum 1[|P - 0.50| <= 0.02]", "units": "fraction in [0,1]",
         "input_source": "P", "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["mean_boundary_margin"], "feature_name": "mean_boundary_margin",
         "threshold_role": "SEGMENTATION_OUTPUT_PROBABILITY_BOUNDARY", "threshold_value": T_SEG,
         "formula": "mean over all N pixels of |P - 0.50| (NOT negated)",
         "units": "probability distance in [0,0.5]", "input_source": "P",
         "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["pred_foreground_pixels"],
         "feature_name": "pred_foreground_pixels",
         "threshold_role": "ROI_PROPOSAL", "threshold_value": T_ROI,
         "formula": "sum M_roi where M_roi = 1[P >= 0.30]",
         "units": "pixels on the 512x512 canvas", "input_source": "P",
         "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["pred_foreground_fraction"],
         "feature_name": "pred_foreground_fraction",
         "threshold_role": "ROI_PROPOSAL", "threshold_value": T_ROI,
         "formula": "pred_foreground_pixels / N", "units": "fraction in [0,1]",
         "input_source": "P", "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["pred_roi_exists"], "feature_name": "pred_roi_exists",
         "threshold_role": "ROI_PROPOSAL", "threshold_value": T_ROI,
         "formula": "1.0 if pred_foreground_pixels > 0 else 0.0", "units": "binary indicator",
         "input_source": "P", "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["pred_empty"], "feature_name": "pred_empty",
         "threshold_role": "ROI_PROPOSAL", "threshold_value": T_ROI,
         "formula": "1.0 - pred_roi_exists", "units": "binary indicator",
         "input_source": "P", "dtype": "float32", "uses_GT": False},
        {"feature_index": _IDX["predicted_roi_area_fraction"],
         "feature_name": "predicted_roi_area_fraction",
         "threshold_role": "ROI_PROPOSAL", "threshold_value": T_ROI,
         "formula": ("w_in = max(0, min(512, x1) - max(0, x0)); "
                     "h_in = max(0, min(512, y1) - max(0, y0)); "
                     "predicted_roi_area_fraction = w_in * h_in / (512 * 512)"),
         "units": "fraction of the native 512x512 canvas (clipped in-canvas ROI)",
         "input_source": "ROI030 crop metadata", "dtype": "float32", "uses_GT": False,
         "expected_range": "[0,1]", "external_padding_excluded": True,
         "superseded_formula": "crop_side_pixels^2 / (512^2)",
         "superseded_status": "SUPERSEDED_PRE_EXECUTION_SPEC_FORMULA__NOT_USED_FOR_PHASE25B"},
        {"feature_index": _IDX["predicted_roi_side"], "feature_name": "predicted_roi_side",
         "threshold_role": "ROI_PROPOSAL", "threshold_value": T_ROI,
         "formula": "canonical cache field crop_side_pixels (before resize to 256x256)",
         "units": "pixels on the 512 canvas (crop support incl. padding; may exceed 512)",
         "input_source": "ROI030 crop metadata", "dtype": "float32", "uses_GT": False,
         "may_exceed_512": True},
    ]


def feature_group_offsets() -> dict:
    return {
        "groups": [
            {"name": name, "tap": tap, "scope": scope, "start": start,
             "stop": start + REDUCTION_K, "dim": REDUCTION_K}
            for name, tap, scope, start in GROUP_ORDER
        ],
        "deep_dim": DEEP_DIM,
        "scalar_start": DEEP_DIM,
        "numeric_dim": NUMERIC_DIM,
        "scalar_order": list(SCALAR_ORDER),
    }
