"""Synthetic fixed-config metric contract tests for PHASE-13 PART-1B.

PRE-CUDA GATE B.

These tests exercise the **same pure helper functions** that
``evaluate_fixed_config_localizer()`` calls:

    * ``src.inference.predicted_roi.evaluate_roi_coverage``
    * ``src.inference.predicted_roi.union_roi_area_fraction``
    * ``src.inference.predicted_roi.apply_context_margin``

plus the aggregate arithmetic that ``evaluate_fixed_config_localizer()``
performs over those helper outputs.

No model. No CUDA. No TRAIN/VAL images. Fabricated arrays and component
geometry only.

Helper semantics (read directly from ``src/inference/predicted_roi.py``)
------------------------------------------------------------------------
``evaluate_roi_coverage`` reads, per GT component, ``min_y/min_x/max_y/max_x``
and an optional ``mask`` (a FULL native-space boolean array). Coverage is:

    inside = component_mask[clip_y1:clip_y2, clip_x1:clip_x2].sum()
    coverage = inside / component_mask.sum()

So the mask must be a full-size array and the proposal is described by
``proposal["crop_geometry"]["clip_y1/clip_y2/clip_x1/clip_x2"]``.

``union_roi_area_fraction`` returns ``union_area / (H*W)`` over the clipped
proposal rectangles.

The metric definitions below are FROZEN and sourced from the immutable
historical trainer ``scripts/training/train_phase13b_localizer.py``
(SHA ``5985b9eb2fe43018babbd88004bf7e5b99d2783dcfa78c7404591a02bdcb555a``),
lines 82-86. If the implementing code and these frozen definitions disagree,
the test must FAIL and the run must STOP CHECK_REQUIRED. Definitions are never
modified to make a test pass.
"""
from __future__ import annotations

import inspect

import numpy as np
import pytest

from src.inference.predicted_roi import (
    apply_context_margin,
    evaluate_roi_coverage,
    union_roi_area_fraction,
)


# ---------------------------------------------------------------------------
# Synthetic fixtures
# ---------------------------------------------------------------------------
def _component(component_id, mask, min_y=0, min_x=0, max_y=None, max_x=None):
    """A GT component in native space with a full-size boolean mask."""
    mask = np.asarray(mask, dtype=bool)
    height, width = mask.shape
    return {
        "component_id": int(component_id),
        "min_y": int(min_y),
        "min_x": int(min_x),
        "max_y": int(height - 1 if max_y is None else max_y),
        "max_x": int(width - 1 if max_x is None else max_x),
        "mask": mask,
    }


def _proposal(rank, clip_y1, clip_y2, clip_x1, clip_x2, score=1.0):
    """A proposal carrying only the geometry the coverage helper reads."""
    return {
        "rank": int(rank),
        "score": float(score),
        "crop_geometry": {
            "clip_y1": int(clip_y1),
            "clip_y2": int(clip_y2),
            "clip_x1": int(clip_x1),
            "clip_x2": int(clip_x2),
        },
    }


def _rect_mask(shape, y1, y2, x1, x2):
    """Full-size boolean mask with a solid rectangle set to True."""
    mask = np.zeros(shape, dtype=bool)
    mask[y1:y2, x1:x2] = True
    return mask


def _ratio(numerator, denominator):
    if denominator == 0:
        return float("nan")
    return float(numerator) / float(denominator)


def _aggregate(per_component_results, *, strata=None, sample_ids=None,
               components_per_sample=None, hard_tiny_flags=None,
               global_empty_ids=None, per_image_area=None,
               per_image_proposals=None):
    """Reproduce the evaluator's aggregate arithmetic over helper outputs."""
    covered90 = [r["covered90"] for r in per_component_results]
    covered50 = [r["covered50"] for r in per_component_results]
    any_overlap = [r["any_overlap"] for r in per_component_results]
    coverage = [r["coverage_fraction"] for r in per_component_results]

    out = {
        "overall_recall90": float(np.mean(covered90)) if covered90 else float("nan"),
        "overall_recall50": float(np.mean(covered50)) if covered50 else float("nan"),
        "any_overlap_recall": float(np.mean(any_overlap)) if any_overlap else float("nan"),
        "mean_coverage": float(np.mean(coverage)) if coverage else float("nan"),
    }

    if strata is not None:
        tiny = [r for r, s in zip(per_component_results, strata) if s == "TINY"]
        out["tiny_recall90_denominator"] = len(tiny)
        out["tiny_recall90_numerator"] = int(sum(r["covered90"] for r in tiny))
        out["tiny_recall90"] = (
            float(np.mean([r["covered90"] for r in tiny])) if tiny else float("nan")
        )

    if components_per_sample is not None:
        multi_ids = {sid for sid, count in components_per_sample.items() if count > 1}
        multi = [
            r for r, sid in zip(per_component_results, sample_ids) if sid in multi_ids
        ]
        out["multi_component_recall90"] = (
            float(np.mean([r["covered90"] for r in multi])) if multi else float("nan")
        )

    if hard_tiny_flags is not None:
        # frozen: hard = frame[frame.hard_tiny]; hard_tiny_recovered90 =
        # int(hard.covered90.sum())
        hard = [
            r for r, flag in zip(per_component_results, hard_tiny_flags) if flag
        ]
        out["hard_tiny_denominator"] = len(hard)
        out["hard_tiny_recovered90"] = int(sum(r["covered90"] for r in hard))

    if global_empty_ids is not None:
        covered_empty = {
            sid
            for r, sid in zip(per_component_results, sample_ids)
            if sid in global_empty_ids and r["covered90"]
        }
        out["global_empty_images_covered90"] = int(len(covered_empty))

    if per_image_area is not None:
        out["mean_roi_area_fraction"] = float(np.mean(per_image_area))

    if per_image_proposals is not None:
        out["mean_proposals_per_image"] = float(np.mean(per_image_proposals))

    return out


# ===========================================================================
# A. Full coverage
# ===========================================================================
def test_A_component_with_full_proposal_support():
    """100% of the component lies inside a proposal rectangle."""
    mask = _rect_mask((100, 100), 40, 50, 40, 50)          # 100 component pixels
    component = _component(1, mask)
    proposal = _proposal(1, 0, 100, 0, 100)                # covers everything

    result = evaluate_roi_coverage([proposal], [component])[0]

    assert result["coverage_fraction"] == pytest.approx(1.0)
    assert result["covered90"] is True
    assert result["covered50"] is True
    assert result["any_overlap"] is True


# ===========================================================================
# B. Sub-90% but at least 50%
# ===========================================================================
def test_B_component_coverage_between_fifty_and_ninety_percent():
    """Exactly 70% of the component pixels lie inside the proposal rectangle."""
    mask = _rect_mask((100, 100), 0, 10, 0, 10)            # 100 pixels
    component = _component(1, mask)
    proposal = _proposal(1, 0, 100, 0, 7)                  # keeps the left 7 cols

    result = evaluate_roi_coverage([proposal], [component])[0]

    assert result["coverage_fraction"] == pytest.approx(0.70)
    assert result["covered90"] is False
    assert result["covered50"] is True
    assert result["any_overlap"] is True


# ===========================================================================
# C. Zero overlap
# ===========================================================================
def test_C_component_with_zero_overlap():
    mask = _rect_mask((100, 100), 0, 10, 0, 10)
    component = _component(1, mask)
    proposal = _proposal(1, 50, 60, 50, 60)                # disjoint rectangle

    result = evaluate_roi_coverage([proposal], [component])[0]

    assert result["coverage_fraction"] == pytest.approx(0.0)
    assert result["covered90"] is False
    assert result["covered50"] is False
    assert result["any_overlap"] is False


# ===========================================================================
# D. Known mixed synthetic population — exact numerators/denominators
# ===========================================================================
def test_D_mixed_population_exact_counts():
    """5 components: 2 TINY (1 covered), 3 non-TINY (2 covered).

    Exact expectations:
      tiny_recall90    = 1/2
      overall_recall90 = 3/5
      overall_recall50 = 4/5   (the partially covered one is >= 0.50)
      mean_coverage    = mean of the five coverage fractions
    """
    hit = _proposal(1, 0, 100, 0, 100)
    miss = _proposal(1, 60, 100, 60, 100)
    half = _proposal(1, 0, 100, 0, 5)                      # keeps left 5 cols

    full_mask = _rect_mask((100, 100), 0, 10, 0, 10)

    components = [
        _component(1, full_mask),   # TINY   -> covered  (1.0)
        _component(2, full_mask),   # TINY   -> missed   (0.0)
        _component(3, full_mask),   # SMALL  -> covered  (1.0)
        _component(4, full_mask),   # MEDIUM -> half     (0.5)
        _component(5, full_mask),   # LARGE  -> covered  (1.0)
    ]
    proposals = [[hit], [miss], [hit], [half], [hit]]
    strata = ["TINY", "TINY", "SMALL", "MEDIUM", "LARGE"]

    results = [
        evaluate_roi_coverage(p, [c])[0] for c, p in zip(components, proposals)
    ]

    assert [r["coverage_fraction"] for r in results] == pytest.approx(
        [1.0, 0.0, 1.0, 0.5, 1.0]
    )

    agg = _aggregate(results, strata=strata)

    assert agg["tiny_recall90_numerator"] == 1
    assert agg["tiny_recall90_denominator"] == 2
    assert agg["tiny_recall90"] == pytest.approx(0.5)

    assert agg["overall_recall90"] == pytest.approx(3 / 5)
    assert agg["overall_recall50"] == pytest.approx(4 / 5)
    assert agg["any_overlap_recall"] == pytest.approx(4 / 5)
    assert agg["mean_coverage"] == pytest.approx((1.0 + 0.0 + 1.0 + 0.5 + 1.0) / 5)


# ===========================================================================
# E. Multi-component fixture — frozen definition
# ===========================================================================
def test_E_multi_component_recall90_matches_frozen_definition():
    """multi_component_recall90 = mean(covered90) over samples with >1 component.

    Frozen definition (historical trainer line 83):
        multi_ids = component_table.groupby('sample_id').size() > 1
        multi     = frame[frame.sample_id.isin(multi_ids)]
        multi_component_recall90 = multi.covered90.mean()

    Fixture: two samples with 2 components each.
      S1: comp1 covered, comp2 missed
      S2: comp1 covered, comp2 covered
    -> multi subset = all 4 components; mean(covered90) = 3/4
    """
    sample_ids = ["S1", "S1", "S2", "S2"]
    components_per_sample = {"S1": 2, "S2": 2}

    hit = _proposal(1, 0, 100, 0, 100)
    miss = _proposal(1, 60, 100, 60, 100)
    full_mask = _rect_mask((100, 100), 0, 10, 0, 10)

    results = [
        evaluate_roi_coverage([hit], [_component(1, full_mask)])[0],
        evaluate_roi_coverage([miss], [_component(2, full_mask)])[0],
        evaluate_roi_coverage([hit], [_component(1, full_mask)])[0],
        evaluate_roi_coverage([hit], [_component(2, full_mask)])[0],
    ]

    agg = _aggregate(
        results, sample_ids=sample_ids, components_per_sample=components_per_sample
    )
    assert agg["multi_component_recall90"] == pytest.approx(3 / 4)

    # single-component samples are excluded entirely
    comps_single = {"S1": 1, "S2": 1}
    agg_single = _aggregate(
        results, sample_ids=sample_ids, components_per_sample=comps_single
    )
    assert np.isnan(agg_single["multi_component_recall90"])


# ===========================================================================
# F. Known proposal rectangles — frozen native-space area definition
# ===========================================================================
def test_F_mean_roi_area_fraction_matches_frozen_definition():
    """mean_roi_area_fraction = mean over images of union area / (H*W).

    Frozen definition (historical trainer line 82):
        area, _ = union_roi_area_fraction(proposals, (height, width))
    """
    height, width = 100, 100
    total = height * width

    # Image 1: one 20x20 proposal -> 400/10000 = 0.04
    proposals_1 = [_proposal(1, 0, 20, 0, 20)]
    # Image 2: two disjoint 10x10 proposals -> 200/10000 = 0.02
    proposals_2 = [_proposal(1, 0, 10, 0, 10), _proposal(2, 50, 60, 50, 60)]
    # Image 3: two 10x10 proposals sharing a 5x10 strip
    #          union = 100 + 100 - 50 = 150 -> 0.015
    proposals_3 = [_proposal(1, 0, 10, 0, 10), _proposal(2, 0, 10, 5, 15)]

    expected = [400 / total, 200 / total, 150 / total]
    actual = []
    for proposals in (proposals_1, proposals_2, proposals_3):
        union_fraction, _max_fraction = union_roi_area_fraction(
            proposals, (height, width)
        )
        actual.append(union_fraction)

    assert actual == pytest.approx(expected)

    # max individual rectangle for image 2 is 100 pixels
    _u2, max2 = union_roi_area_fraction(proposals_2, (height, width))
    assert max2 == pytest.approx(100 / total)

    agg = _aggregate(per_component_results=[], per_image_area=actual)
    assert agg["mean_roi_area_fraction"] == pytest.approx(np.mean(expected))


# ===========================================================================
# G. Hard-Tiny diagnostic fixture
# ===========================================================================
def test_G_hard_tiny_recovered90_counts_only_predeclared_identities():
    """hard_tiny_recovered90 = sum(covered90) over predeclared hard-Tiny keys.

    Frozen definition (historical trainer line 86):
        hard = frame[frame.hard_tiny]
        hard_tiny_recovered90 = int(hard.covered90.sum())

    Fixture: 4 components over 2 samples; only 2 components are predeclared
    hard-Tiny (the historical trainer carries ``hard_tiny`` as a per-COMPONENT
    boolean column, and subsets ``frame[frame.hard_tiny]``).
      * row 0 ("S1", c1) hard_tiny=True  + covered -> counts
      * row 1 ("S1", c2) hard_tiny=True  + missed  -> does not count
      * row 2 ("S2", c1) hard_tiny=False + covered -> must NOT count
      * row 3 ("S2", c2) hard_tiny=False + covered -> must NOT count
    Expected hard_tiny_recovered90 = 1, denominator = 2.
    """
    sample_ids = ["S1", "S1", "S2", "S2"]
    hard_tiny_flags = [True, True, False, False]

    hit = _proposal(1, 0, 100, 0, 100)
    miss = _proposal(1, 60, 100, 60, 100)
    full_mask = _rect_mask((100, 100), 0, 10, 0, 10)

    results = [
        evaluate_roi_coverage([hit], [_component(1, full_mask)])[0],   # S1,1 covered
        evaluate_roi_coverage([miss], [_component(2, full_mask)])[0],  # S1,2 missed
        evaluate_roi_coverage([hit], [_component(1, full_mask)])[0],   # S2,1 covered
        evaluate_roi_coverage([hit], [_component(2, full_mask)])[0],   # S2,2 covered
    ]

    agg = _aggregate(
        results, sample_ids=sample_ids, hard_tiny_flags=hard_tiny_flags
    )

    assert agg["hard_tiny_denominator"] == 2
    assert agg["hard_tiny_recovered90"] == 1
    # the two non-hard covered components must be excluded from the numerator
    assert agg["overall_recall90"] == pytest.approx(3 / 4)


# ===========================================================================
# H. Global-empty diagnostic fixture
# ===========================================================================
def test_H_global_empty_images_covered90_follows_frozen_definition():
    """global_empty_images_covered90 = distinct hard-set global-empty sample_ids
    having ANY covered90 component.

    Frozen definition (historical trainer line 86):
        empty = frame[frame.global_empty_image]
        global_empty_images_covered90 = int(empty.groupby('sample_id').covered90.any().sum())

    Fixture: 3 global-empty samples.
      * E1: 2 components, neither covered      -> NOT counted
      * E2: 2 components, exactly one covered  -> counted (ANY)
      * E3: 1 component, covered               -> counted
    Expected = 2, denominator = 3.
    """
    sample_ids = ["E1", "E1", "E2", "E2", "E3"]
    global_empty_ids = {"E1", "E2", "E3"}

    hit = _proposal(1, 0, 100, 0, 100)
    miss = _proposal(1, 60, 100, 60, 100)
    full_mask = _rect_mask((100, 100), 0, 10, 0, 10)

    results = [
        evaluate_roi_coverage([miss], [_component(1, full_mask)])[0],  # E1 c1
        evaluate_roi_coverage([miss], [_component(2, full_mask)])[0],  # E1 c2
        evaluate_roi_coverage([hit], [_component(1, full_mask)])[0],   # E2 c1 covered
        evaluate_roi_coverage([miss], [_component(2, full_mask)])[0],  # E2 c2
        evaluate_roi_coverage([hit], [_component(1, full_mask)])[0],   # E3 c1 covered
    ]

    agg = _aggregate(
        results, sample_ids=sample_ids, global_empty_ids=global_empty_ids
    )

    assert agg["global_empty_images_covered90"] == 2
    assert len(global_empty_ids) == 3


# ===========================================================================
# I. Secondary diagnostics cannot change the 4-term selection tuple
# ===========================================================================
def test_I_secondary_diagnostics_cannot_change_selection_tuple():
    """Varying ONLY secondary diagnostics must not move the selection tuple."""
    from src.training.clean_v3_selection import (
        SELECTION_TERM_NAMES,
        select_epoch,
    )

    params = set(inspect.signature(select_epoch).parameters)
    for diagnostic in (
        "hard_tiny_recovered90",
        "global_empty_images_covered90",
        "multi_component_recall90",
        "mean_proposals_per_image",
    ):
        assert diagnostic not in params, (
            f"{diagnostic} must not be a selection parameter"
        )
        assert not any(diagnostic in term for term in SELECTION_TERM_NAMES)

    assert len(SELECTION_TERM_NAMES) == 4
    assert SELECTION_TERM_NAMES == (
        "tiny_recall90",
        "overall_recall90",
        "negative_mean_roi_area_fraction",
        "negative_val_loss",
    )

    primary = dict(
        tiny_recall90=0.5,
        overall_recall90=0.6,
        mean_roi_area_fraction=0.03,
        val_loss=1.5,
        best_score=None,
        epoch=1,
        patience=15,
    )
    outcome = select_epoch(**primary)
    assert outcome.score == (0.5, 0.6, -0.03, -1.5)

    # an identical call with wildly different (hypothetical) diagnostics is
    # impossible to express — the tuple is unchanged
    assert select_epoch(**primary).score == outcome.score


# ===========================================================================
# J. Proposal geometry helper — frozen square + clip contract
# ===========================================================================
def test_J_apply_context_margin_is_square_and_clipped():
    """The frozen margin contract: expand, square, then clip/pad."""
    geometry = apply_context_margin((40, 40, 59, 59), (100, 100), 0.20)

    assert geometry["margin"] == pytest.approx(0.20)
    # a centred 20x20 box with margin 0.20 -> side = 20 + 2*round(0.20*20) = 28
    assert geometry["crop_side_pixels"] == 28
    # coordinates are inclusive-bounds half-open by construction: y2 = y1 + side
    assert geometry["y2"] - geometry["y1"] == geometry["crop_side_pixels"]
    assert geometry["x2"] - geometry["x1"] == geometry["crop_side_pixels"]
    # clipping stays inside the image
    assert 0 <= geometry["clip_y1"] < geometry["clip_y2"] <= 100
    assert 0 <= geometry["clip_x1"] < geometry["clip_x2"] <= 100
    # effective magnification uses the 512-space convention
    assert geometry["effective_magnification"] == pytest.approx(512.0 / 28)


# ===========================================================================
# K. Proposal count feeds mean_proposals_per_image
# ===========================================================================
def test_K_mean_proposals_per_image_arithmetic():
    """mean_proposals_per_image = mean over images of len(proposals)."""
    per_image_proposals = [5, 3, 0, 1, 5]                  # frozen top_k = 5
    agg = _aggregate(
        per_component_results=[], per_image_proposals=per_image_proposals
    )
    assert agg["mean_proposals_per_image"] == pytest.approx((5 + 3 + 0 + 1 + 5) / 5)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v", "--no-header"]))
