"""Versioned 202-D router features for the changed Lite backbone channels.

The original feature extractor intentionally enforces the frozen FULL model's
native tap widths. This separate implementation retains the feature order and
scalar semantics while adaptively reducing Lite tap vectors to 32 values each.
Its distribution is new and requires router retraining and fit-only scaling.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence

import numpy as np

from src.features.barr_pre_refinement_features import (
    DEEP_DIM,
    GROUP_ORDER,
    NUMERIC_DIM,
    adaptive_channel_reduce,
    pool_global,
    pool_roi,
    scalar_block,
)


def build_lite_feature_vector(
    feature_maps: Mapping[str, np.ndarray],
    probability: np.ndarray,
    roi_row: Mapping[str, object],
) -> np.ndarray:
    """Build the Lite-specific 202-D vector without reading labels or masks."""
    roi: Sequence[int] = (
        int(roi_row["clip_x1"]),
        int(roi_row["clip_y1"]),
        int(roi_row["clip_x2"]),
        int(roi_row["clip_y2"]),
    )
    deep_groups: list[np.ndarray] = []
    for _, tap, scope, _ in GROUP_ORDER:
        if tap not in feature_maps:
            raise ValueError(f"missing Lite router tap: {tap}")
        feature_map = np.asarray(feature_maps[tap], dtype=np.float32)
        if feature_map.ndim != 3 or feature_map.shape[0] < 4:
            raise ValueError(f"{tap} must have shape [C>=4, H, W]")
        native = pool_global(feature_map) if scope == "GLOBAL" else pool_roi(feature_map, roi)
        deep_groups.append(adaptive_channel_reduce(native))
    deep = np.concatenate(deep_groups).astype(np.float32)
    scalars = scalar_block(np.asarray(probability, dtype=np.float32), roi_row)
    result = np.concatenate((deep, scalars)).astype(np.float32)
    if result.shape != (NUMERIC_DIM,) or deep.shape != (DEEP_DIM,):
        raise RuntimeError("Lite router feature dimensions do not match the 202-D contract")
    if not np.isfinite(result).all():
        raise ValueError("Lite router features contain NaN or Inf")
    return result
