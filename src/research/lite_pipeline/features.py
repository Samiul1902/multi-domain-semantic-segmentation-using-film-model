"""Lite adapter for the frozen 202-D pre-refinement router feature vector.

The canonical extractor (:mod:`src.features.barr_pre_refinement_features`)
deliberately hard-fails when a tap's native width is not the FULL width, because
silently reducing an unexpected tensor would invalidate every historical feature
row.  The Lite backbone has different widths (128 / 24 / 12 instead of
256 / 48 / 24), so the frozen extractor refuses it -- correctly.

:mod:`src.features.barr_lite_router_features` already provides the Lite
implementation: it keeps the frozen group order, the frozen
``DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`` reduction, the frozen ten
scalar descriptors and the 202-D width, and relaxes only the width assertion.
This module is the **pipeline-side adapter**, not a second implementation:

* it imports the Lite builder rather than restating it;
* it adds the *architecture* contract the builder cannot know -- the exact tap
  widths and feature-grid sides implied by the selected variant -- and fails
  closed on any deviation;
* it exposes the same ``(cmaps, p512, geom) -> float32[202]`` signature the FULL
  producers and the GT-free inference adapter already call, so it is drop-in.

Normalisation is deliberately NOT done here.  Router scaling is FIT-only per
cross-fit fold inside the B producer, so Lite feature statistics are computed
from Lite TRAIN data and never inherited from the FULL normaliser.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Sequence

import numpy as np

from src.features.barr_lite_router_features import build_lite_feature_vector
from src.features.barr_pre_refinement_features import (
    DEEP_DIM,
    NUMERIC_DIM,
    SCALAR_DIM,
    TAPS,
    feature_group_offsets,
)

from . import recipe as L

__all__ = [
    "LiteFeatureContractError",
    "assert_lite_tap_contract",
    "lite_feature_builder",
    "lite_feature_schema",
    "LITE_SCALAR_IDX",
]

#: The eight scalar indices that receive FIT-only standardisation.  Identical to
#: the FULL contract by construction -- the reduction preserves column order.
LITE_SCALAR_IDX: Sequence[int] = tuple(L.R.B_NORMALIZE_IDX)


class LiteFeatureContractError(ValueError):
    """Raised when a tap does not match the selected Lite architecture."""


def assert_lite_tap_contract(cmaps: Mapping[str, np.ndarray]) -> None:
    """Fail closed unless every tap has the Lite width and grid side.

    This is the check the generic builder cannot make: it accepts any ``C >= 4``,
    which would happily reduce a FULL tap into a 32-D group and produce a vector
    that is numerically plausible and scientifically meaningless.
    """
    for tap in TAPS:
        if tap not in cmaps:
            raise LiteFeatureContractError(f"missing Lite router tap {tap!r}")
        arr = np.asarray(cmaps[tap])
        if arr.ndim != 3:
            raise LiteFeatureContractError(
                f"tap {tap!r} must be [C, H, W], got shape {arr.shape}")
        expected_c = L.LITE_NATIVE_CHANNELS[tap]
        if arr.shape[0] != expected_c:
            raise LiteFeatureContractError(
                f"tap {tap!r} has {arr.shape[0]} channels, Lite architecture "
                f"requires {expected_c} (FULL would be {L.FULL_NATIVE_CHANNELS[tap]})")
        expected_side = L.LITE_FEATURE_GRID[tap]
        if arr.shape[-1] != expected_side or arr.shape[-2] != expected_side:
            raise LiteFeatureContractError(
                f"tap {tap!r} has grid {arr.shape[-2]}x{arr.shape[-1]}, Lite "
                f"architecture requires {expected_side}x{expected_side}")


def lite_feature_builder(cmaps: Mapping[str, np.ndarray], probability: np.ndarray,
                         roi_row: Mapping[str, object]) -> np.ndarray:
    """``(taps, p512, roi_geometry) -> float32[202]`` with the Lite contract enforced."""
    assert_lite_tap_contract(cmaps)
    vec = build_lite_feature_vector(cmaps, probability, roi_row)
    if vec.shape != (NUMERIC_DIM,):
        raise LiteFeatureContractError(
            f"Lite feature vector shape {vec.shape} != ({NUMERIC_DIM},)")
    if not np.isfinite(vec).all():
        raise LiteFeatureContractError("Lite feature vector contains NaN or Inf")
    return vec.astype(np.float32, copy=False)


def lite_feature_schema() -> dict:
    """Feature-group layout plus the Lite widths, for manifests and reports."""
    offsets = feature_group_offsets()
    return {
        "numeric_dim": NUMERIC_DIM,
        "deep_dim": DEEP_DIM,
        "scalar_dim": SCALAR_DIM,
        "groups": offsets["groups"],
        "scalar_start": offsets["scalar_start"],
        "scalar_order": offsets["scalar_order"],
        "normalize_idx": list(LITE_SCALAR_IDX),
        "lite_native_channels": dict(L.LITE_NATIVE_CHANNELS),
        "full_native_channels": dict(L.FULL_NATIVE_CHANNELS),
        "feature_grid": dict(L.LITE_FEATURE_GRID),
        "reduction_op": "DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1",
        "channel_counts_differ_from_full": True,
        "grid_sides_identical_to_full": True,
        "normalisation": (
            "FIT-only per cross-fit fold inside the B producer; Lite statistics are "
            "never inherited from the FULL normaliser"),
    }
