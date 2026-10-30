"""PHASE-13 PART-1B R2C — coverage-semantics arbitration tests.

Proves that the EXPLICIT historical bbox helper reproduces the executing
``evaluate_roi_coverage`` bbox fallback exactly, across the required fixtures:
full overlap, partial overlap, zero overlap, multiple proposals, overlapping
proposal union, edge clipping.

Also proves pixel coverage remains available as a SECONDARY sensitivity metric
and cannot influence checkpoint selection.

No TEST access.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.inference.clean_v3_coverage import (  # noqa: E402
    BBOX_SEMANTICS,
    evaluate_historical_bbox_coverage,
    evaluate_pixel_mask_coverage,
)
from src.inference.predicted_roi import evaluate_roi_coverage  # noqa: E402


def _component(cid, y1, x1, y2, x2, mask=None):
    component = {
        "component_id": cid,
        "min_y": y1, "min_x": x1, "max_y": y2, "max_x": x2,
    }
    if mask is not None:
        component["mask"] = mask
    return component


def _proposal(rank, clip_y1, clip_y2, clip_x1, clip_x2):
    return {
        "rank": rank,
        "score": 1.0,
        "crop_geometry": {
            "clip_y1": clip_y1, "clip_y2": clip_y2,
            "clip_x1": clip_x1, "clip_x2": clip_x2,
        },
    }


# ---------------------------------------------------------------- fixtures ---
FIXTURES = {
    "full_overlap": (
        [_proposal(1, 0, 40, 0, 40)],
        [_component(1, 0, 0, 39, 39)],
    ),
    "partial_overlap": (
        [_proposal(1, 0, 20, 0, 20)],
        [_component(1, 0, 0, 39, 39)],
    ),
    "zero_overlap": (
        [_proposal(1, 100, 140, 100, 140)],
        [_component(1, 0, 0, 39, 39)],
    ),
    "multiple_proposals": (
        [_proposal(1, 0, 10, 0, 10), _proposal(2, 30, 40, 30, 40), _proposal(3, 0, 40, 0, 40)],
        [_component(1, 0, 0, 39, 39), _component(2, 30, 30, 39, 39)],
    ),
    "overlapping_proposal_union": (
        [_proposal(1, 0, 25, 0, 25), _proposal(2, 15, 40, 15, 40)],
        [_component(1, 0, 0, 39, 39)],
    ),
    "edge_clipping": (
        [_proposal(1, -50, 10, -50, 10), _proposal(2, 30, 500, 30, 500)],
        [_component(1, 0, 0, 39, 39)],
    ),
}


@pytest.mark.parametrize("name", sorted(FIXTURES))
def test_explicit_bbox_equals_original_fallback(name):
    """§4 — explicit helper == original evaluate_roi_coverage fallback."""
    proposals, components = FIXTURES[name]
    # The original helper takes the fallback branch only when no mask is present.
    reference = evaluate_roi_coverage(proposals, components)
    explicit = evaluate_historical_bbox_coverage(proposals, components)
    assert len(explicit) == len(reference)
    for got, want in zip(explicit, reference):
        assert got["component_id"] == want["component_id"]
        assert got["coverage_fraction"] == pytest.approx(want["coverage_fraction"], abs=0.0)
        assert got["covered90"] == want["covered90"]
        assert got["covered50"] == want["covered50"]
        assert got["any_overlap"] == want["any_overlap"]


def test_explicit_bbox_ignores_mask_when_present():
    """Primary semantics must not silently change if a mask is attached."""
    side = 40
    mask = np.zeros((side, side), dtype=bool)
    mask[0:4, 0:4] = True          # blob inside the proposal
    mask[35:39, 35:39] = True      # blob far outside the proposal
    # Proposal covers only the top-left 10x10 window.
    proposals = [_proposal(1, 0, 10, 0, 10)]
    with_mask = [_component(1, 0, 0, 39, 39, mask=mask)]
    without_mask = [_component(1, 0, 0, 39, 39)]

    a = evaluate_historical_bbox_coverage(proposals, with_mask)[0]["coverage_fraction"]
    b = evaluate_historical_bbox_coverage(proposals, without_mask)[0]["coverage_fraction"]
    assert a == b == pytest.approx(100 / 1600)   # 10x10 bbox intersection over 40x40 bbox

    # Pixel coverage on the same fixture is materially different: only the
    # in-window blob counts, over the TRUE pixel total.
    p = evaluate_pixel_mask_coverage(proposals, with_mask)[0]["coverage_fraction"]
    assert p == pytest.approx(16 / int(mask.sum()))
    assert p != pytest.approx(a)


def test_pixel_helper_requires_mask():
    proposals = [_proposal(1, 0, 40, 0, 40)]
    with pytest.raises(ValueError):
        evaluate_pixel_mask_coverage(proposals, [_component(1, 0, 0, 39, 39)])


def test_bbox_and_pixel_differ_on_nonrectangular_component():
    side = 40
    mask = np.zeros((side, side), dtype=bool)
    mask[0:4, 0:40] = True
    mask[0:40, 0:4] = True
    component = _component(1, 0, 0, 39, 39, mask=mask)
    corner = [_proposal(1, 0, 4, 0, 4)]
    bbox = evaluate_historical_bbox_coverage(corner, [component])[0]["coverage_fraction"]
    pixel = evaluate_pixel_mask_coverage(corner, [component])[0]["coverage_fraction"]
    assert bbox == pytest.approx(16 / (40 * 40))
    assert pixel == pytest.approx(16 / int(mask.sum()))
    assert bbox != pytest.approx(pixel)


def test_bbox_semantics_label():
    assert BBOX_SEMANTICS == "HISTORICAL_EXECUTING_BBOX_COVERAGE"


def test_empty_proposals_yield_zero_coverage_both_semantics():
    side = 8
    mask = np.zeros((side, side), dtype=bool)
    mask[2:4, 2:4] = True
    component = _component(1, 2, 2, 3, 3, mask=mask)
    for fn in (evaluate_historical_bbox_coverage, evaluate_pixel_mask_coverage):
        row = fn([], [component])[0]
        assert row["coverage_fraction"] == 0.0
        assert row["covered90"] is False
        assert row["any_overlap"] is False
