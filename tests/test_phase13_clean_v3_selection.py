"""Deterministic unit tests for clean-v3 checkpoint selection (Phase 13 Part 1B-R0).

FABRICATED SCALAR NUMBERS ONLY. No data, no model, no CUDA, no forward pass.
These tests are NOT scientific inference.
"""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.training.clean_v3_selection import (
    DIAGNOSTIC_TERM_NAMES,
    SELECTION_TERM_NAMES,
    build_selection_tuple,
    is_strict_improvement,
    select_epoch,
    selection_terms_from_epoch_metrics,
)


# ---------------------------------------------------------------------------
# 1. Tuple construction
# ---------------------------------------------------------------------------
def test_tuple_has_four_terms_in_frozen_order():
    score = build_selection_tuple(0.70, 0.60, 0.05, 2.0)
    assert score == (0.70, 0.60, -0.05, -2.0)
    assert len(score) == 4
    assert len(SELECTION_TERM_NAMES) == 4


def test_tuple_does_not_round_inputs():
    # Values that would collapse if rounded to 2dp must remain distinguishable.
    assert build_selection_tuple(0.7000001, 0.0, 0.0, 0.0) != build_selection_tuple(0.7000002, 0.0, 0.0, 0.0)


def test_tuple_rejects_nan_and_inf():
    with pytest.raises(ValueError):
        build_selection_tuple(float("nan"), 0.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        build_selection_tuple(0.0, float("inf"), 0.0, 0.0)


# ---------------------------------------------------------------------------
# 2. Term 1 dominates all later terms
# ---------------------------------------------------------------------------
def test_term1_dominates_all_later_terms():
    better_term1 = (0.80, 0.00, -9.99, -9.99)
    worse_term1 = (0.79, 0.99, -0.01, -0.01)
    assert is_strict_improvement(better_term1, worse_term1) is True
    assert is_strict_improvement(worse_term1, better_term1) is False


# ---------------------------------------------------------------------------
# 3. Term 2 breaks ties in term 1
# ---------------------------------------------------------------------------
def test_term2_breaks_term1_tie():
    better_term2 = (0.70, 0.90, -9.99, -9.99)
    worse_term2 = (0.70, 0.89, -0.01, -0.01)
    assert is_strict_improvement(better_term2, worse_term2) is True
    assert is_strict_improvement(worse_term2, better_term2) is False


# ---------------------------------------------------------------------------
# 4. Smaller ROI area wins after the first two tie
# ---------------------------------------------------------------------------
def test_smaller_roi_area_wins_after_two_ties():
    smaller_area = (0.70, 0.80, -0.04, -9.99)   # area 0.04
    larger_area = (0.70, 0.80, -0.09, -0.01)    # area 0.09
    assert is_strict_improvement(smaller_area, larger_area) is True
    assert is_strict_improvement(larger_area, smaller_area) is False


# ---------------------------------------------------------------------------
# 5. Lower val loss wins after the first three tie
# ---------------------------------------------------------------------------
def test_lower_val_loss_wins_after_three_ties():
    lower_loss = (0.70, 0.80, -0.05, -1.10)     # loss 1.10
    higher_loss = (0.70, 0.80, -0.05, -1.90)    # loss 1.90
    assert is_strict_improvement(lower_loss, higher_loss) is True
    assert is_strict_improvement(higher_loss, lower_loss) is False


# ---------------------------------------------------------------------------
# 6. Exact tuple tie is NOT an improvement
# ---------------------------------------------------------------------------
def test_exact_tuple_tie_is_not_an_improvement():
    same = (0.70, 0.80, -0.05, -1.10)
    assert is_strict_improvement(same, same) is False


# ---------------------------------------------------------------------------
# 7. End-to-end select_epoch: ties produce BAD_EPOCH, not improvement
# ---------------------------------------------------------------------------
def test_select_epoch_tie_increments_bad_epochs_and_keeps_best():
    first = select_epoch(0.70, 0.80, 0.05, 1.10, best_score=None, epoch=1)
    assert first.is_new_best is True
    assert first.bad_epochs == 0

    tied = select_epoch(
        0.70, 0.80, 0.05, 1.10,
        best_score=first.best_score, best_epoch=first.best_epoch,
        bad_epochs=first.bad_epochs, epoch=2,
    )
    assert tied.is_new_best is False
    assert tied.bad_epochs == 1
    assert tied.best_epoch == 1


def test_select_epoch_improvement_resets_bad_epochs():
    first = select_epoch(0.70, 0.80, 0.05, 1.10, best_score=None, epoch=1)
    worse = select_epoch(0.60, 0.80, 0.05, 1.10,
                         best_score=first.best_score, best_epoch=1,
                         bad_epochs=0, epoch=2)
    assert worse.is_new_best is False
    assert worse.bad_epochs == 1
    better = select_epoch(0.90, 0.80, 0.05, 1.10,
                          best_score=worse.best_score, best_epoch=worse.best_epoch,
                          bad_epochs=worse.bad_epochs, epoch=3)
    assert better.is_new_best is True
    assert better.bad_epochs == 0
    assert better.best_epoch == 3


def test_select_epoch_stops_after_patience_exhausted():
    best = build_selection_tuple(0.90, 0.90, 0.01, 1.0)
    outcome = select_epoch(0.10, 0.10, 0.50, 9.0,
                           best_score=best, best_epoch=1,
                           bad_epochs=14, epoch=16, patience=15)
    assert outcome.is_new_best is False
    assert outcome.bad_epochs == 15
    assert outcome.stopped is True


# ---------------------------------------------------------------------------
# 8. Grid search / multiple proposal configs must be rejected
# ---------------------------------------------------------------------------
def test_multiple_proposal_configurations_rejected():
    with pytest.raises(ValueError):
        select_epoch(0.7, 0.8, 0.05, 1.1, proposal_configuration_count=20)
    with pytest.raises(ValueError):
        select_epoch(0.7, 0.8, 0.05, 1.1, proposal_configuration_count=0)


def test_zero_denominator_rule_blocks_scoring():
    with pytest.raises(ValueError):
        select_epoch(0.7, 0.8, 0.05, 1.1, zero_denominator=True)


# ---------------------------------------------------------------------------
# 9. SECONDARY DIAGNOSTIC EXCLUSION
#    Changing ONLY diagnostic values cannot change score / is_new_best /
#    bad_epochs when the four primary terms are unchanged.
# ---------------------------------------------------------------------------
def _diagnostic_metrics(scale: float) -> dict:
    """Fabricated per-epoch metrics with only diagnostics varying.

    ``scale`` must be >= 0. The four PRIMARY terms are held constant so that any
    change in the selection outcome is attributable to diagnostics alone.
    """
    return {
        "tiny_recall90": 0.70,
        "overall_recall90": 0.80,
        "mean_roi_area_fraction": 0.05,
        "val_loss": 1.10,
        "hard_tiny_recovered90": int(round(scale)),
        "global_empty_images_covered90": int(round(scale)),
        "multi_component_recall90": float(0.1 * scale),
        "mean_proposals_per_image": float(1.0 * scale),
    }


def test_diagnostics_cannot_change_the_selection_tuple():
    base = selection_terms_from_epoch_metrics(_diagnostic_metrics(1.0))
    perturbed = selection_terms_from_epoch_metrics(_diagnostic_metrics(987654.0))
    assert base == perturbed
    assert build_selection_tuple(
        _diagnostic_metrics(1.0)["tiny_recall90"],
        _diagnostic_metrics(1.0)["overall_recall90"],
        _diagnostic_metrics(1.0)["mean_roi_area_fraction"],
        _diagnostic_metrics(1.0)["val_loss"],
    ) == build_selection_tuple(
        _diagnostic_metrics(5.0)["tiny_recall90"],
        _diagnostic_metrics(5.0)["overall_recall90"],
        _diagnostic_metrics(5.0)["mean_roi_area_fraction"],
        _diagnostic_metrics(5.0)["val_loss"],
    )


def test_diagnostics_cannot_change_is_new_best_or_bad_epochs():
    best = build_selection_tuple(0.70, 0.80, 0.05, 1.10)

    low = _diagnostic_metrics(0.0)
    high = _diagnostic_metrics(1_000_000.0)
    # Only diagnostics differ; primary terms are identical by construction.
    for name in DIAGNOSTIC_TERM_NAMES:
        assert low[name] != high[name]

    outcome_low = select_epoch(
        low["tiny_recall90"], low["overall_recall90"],
        low["mean_roi_area_fraction"], low["val_loss"],
        best_score=best, best_epoch=1, bad_epochs=3, epoch=5,
    )
    outcome_high = select_epoch(
        high["tiny_recall90"], high["overall_recall90"],
        high["mean_roi_area_fraction"], high["val_loss"],
        best_score=best, best_epoch=1, bad_epochs=3, epoch=5,
    )

    assert outcome_low.score == outcome_high.score
    assert outcome_low.is_new_best == outcome_high.is_new_best
    assert outcome_low.bad_epochs == outcome_high.bad_epochs
    assert outcome_low.stopped == outcome_high.stopped
    assert outcome_low.best_epoch == outcome_high.best_epoch


def test_diagnostic_names_are_disjoint_from_selection_names():
    assert set(DIAGNOSTIC_TERM_NAMES).isdisjoint(set(SELECTION_TERM_NAMES))
    for name in DIAGNOSTIC_TERM_NAMES:
        assert name not in SELECTION_TERM_NAMES


def test_select_epoch_signature_accepts_no_diagnostics():
    """Structural exclusion: the scorer has no diagnostic parameter at all."""
    import inspect

    params = set(inspect.signature(select_epoch).parameters)
    assert params.isdisjoint(set(DIAGNOSTIC_TERM_NAMES))
