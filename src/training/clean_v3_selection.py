"""Clean-v3 checkpoint selection scoring (Phase 13 Part 1B-R0).

Pure functions only. NO model, NO data, NO CUDA, NO forward pass.

The PRIMARY selection rule is the R2-frozen executing historical 4-term strict
lexicographic tuple:

    (tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)

Terms 3 and 4 are already negated, so a plain tuple ``>`` comparison IS the
required "maximise coverage, then minimise ROI area, then minimise val loss"
rule. Inputs are NEVER rounded before comparison.

SECONDARY DIAGNOSTICS
---------------------
``hard_tiny_recovered90``, ``global_empty_images_covered90``,
``multi_component_recall90`` and ``mean_proposals_per_image`` are recorded for
analysis but MUST NOT influence selection. The scorer therefore does not accept
them as inputs at all, which makes their exclusion structural rather than
conventional.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# Frozen term names (R2 checkpoint_selection.tuple)
# ---------------------------------------------------------------------------
SELECTION_TERM_NAMES: Tuple[str, ...] = (
    "tiny_recall90",
    "overall_recall90",
    "negative_mean_roi_area_fraction",
    "negative_val_loss",
)

DIAGNOSTIC_TERM_NAMES: Tuple[str, ...] = (
    "hard_tiny_recovered90",
    "global_empty_images_covered90",
    "multi_component_recall90",
    "mean_proposals_per_image",
)

SELECTION_LABEL: str = "EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION"


@dataclass(frozen=True)
class SelectionOutcome:
    """Result of one epoch's strict-lexicographic selection decision."""

    score: Optional[Tuple[float, float, float, float]]
    is_new_best: bool
    bad_epochs: int
    best_score: Optional[Tuple[float, float, float, float]]
    best_epoch: Optional[int]
    stopped: bool
    term_names: Tuple[str, ...] = SELECTION_TERM_NAMES
    selection_label: str = SELECTION_LABEL

    def as_row_fields(self) -> Dict[str, Any]:
        """Flat per-epoch history fields, including the explicit term breakdown."""
        score = self.score if self.score is not None else (None, None, None, None)
        return {
            "selection_term_1_tiny_recall90": score[0],
            "selection_term_2_overall_recall90": score[1],
            "selection_term_3_negative_mean_roi_area_fraction": score[2],
            "selection_term_4_negative_val_loss": score[3],
            "selection_tuple": None if self.score is None else list(self.score),
            "selection_term_names": list(self.term_names),
            "is_new_best": self.is_new_best,
            "best_epoch_so_far": self.best_epoch,
            "bad_epochs": self.bad_epochs,
        }


def build_selection_tuple(
    tiny_recall90: float,
    overall_recall90: float,
    mean_roi_area_fraction: float,
    val_loss: float,
) -> Tuple[float, float, float, float]:
    """Return the frozen 4-term tuple with NO rounding.

    Term 3 and term 4 are negated so that lexicographic ``>`` maximisation is
    equivalent to the R2 semantics (maximise recall, minimise ROI area,
    minimise val loss).
    """
    for name, value in (
        ("tiny_recall90", tiny_recall90),
        ("overall_recall90", overall_recall90),
        ("mean_roi_area_fraction", mean_roi_area_fraction),
        ("val_loss", val_loss),
    ):
        if value is None:
            raise ValueError(f"{name} is None; the four primary terms are mandatory")
        if isinstance(value, float) and (value != value):
            raise ValueError(f"{name} is NaN; refusing to score a non-finite epoch")
        if value in (float("inf"), float("-inf")):
            raise ValueError(f"{name} is Inf; refusing to score a non-finite epoch")
    return (
        float(tiny_recall90),
        float(overall_recall90),
        -float(mean_roi_area_fraction),
        -float(val_loss),
    )


def selection_terms_from_epoch_metrics(metrics: Mapping[str, Any]) -> Tuple[float, ...]:
    """Extract ONLY the four primary terms from a per-epoch metrics mapping.

    Accepts either the raw names or the already-negated term names. Any
    diagnostic key present in ``metrics`` is ignored by construction.
    """
    def _pick(raw: str, negated: str) -> float:
        if raw in metrics:
            return float(metrics[raw])
        if negated in metrics:
            return -float(metrics[negated])
        raise KeyError(f"missing primary selection term {raw!r} (or {negated!r})")

    return (
        _pick("tiny_recall90", "negative_tiny_recall90"),
        _pick("overall_recall90", "negative_overall_recall90"),
        _pick("mean_roi_area_fraction", "negative_mean_roi_area_fraction"),
        _pick("val_loss", "negative_val_loss"),
    )


def is_strict_improvement(
    candidate: Sequence[float],
    best: Optional[Sequence[float]],
) -> bool:
    """Strict lexicographic comparison; an exact tie is NOT an improvement."""
    if best is None:
        return True
    candidate = tuple(candidate)
    best = tuple(best)
    if len(candidate) != len(best):
        raise ValueError(
            f"tuple length mismatch: candidate {len(candidate)} vs best {len(best)}"
        )
    return candidate > best  # Python tuple comparison is lexicographic


def select_epoch(
    tiny_recall90: float,
    overall_recall90: float,
    mean_roi_area_fraction: float,
    val_loss: float,
    best_score: Optional[Sequence[float]] = None,
    best_epoch: Optional[int] = None,
    bad_epochs: int = 0,
    epoch: Optional[int] = None,
    patience: int = 15,
    proposal_configuration_count: int = 1,
    zero_denominator: bool = False,
) -> SelectionOutcome:
    """Apply the frozen 4-term strict-lexicographic selection decision.

    Pure and side-effect free. ``proposal_configuration_count`` must be 1: the
    clean-v3 primary protocol permits exactly one fixed proposal configuration
    and forbids any per-epoch grid search.
    """
    if proposal_configuration_count != 1:
        raise ValueError(
            "clean-v3 primary training permits exactly ONE fixed proposal "
            f"configuration; got {proposal_configuration_count}. Grid search is disabled."
        )
    if zero_denominator:
        raise ValueError(
            "zero_denominator_rule: STOP / CHECK_REQUIRED BEFORE TRAINING"
        )

    score = build_selection_tuple(
        tiny_recall90, overall_recall90, mean_roi_area_fraction, val_loss
    )
    improved = is_strict_improvement(score, best_score)

    if improved:
        new_best_score = score
        new_best_epoch = epoch if epoch is not None else best_epoch
        new_bad_epochs = 0
    else:
        new_best_score = None if best_score is None else tuple(best_score)
        new_best_epoch = best_epoch
        new_bad_epochs = bad_epochs + 1

    stopped = bool(patience > 0 and new_bad_epochs >= patience
                   and new_best_score is not None)

    return SelectionOutcome(
        score=score,
        is_new_best=improved,
        bad_epochs=new_bad_epochs,
        best_score=new_best_score,
        best_epoch=new_best_epoch,
        stopped=stopped,
    )


# ---------------------------------------------------------------------------
# H3 SUPPLY-AXIS CHECKPOINT SELECTION (ADDITIVE — does NOT alter the R2 4-term rule)
# ---------------------------------------------------------------------------
# Frozen rule (h3_proposal_supply_checkpoint_selection_rule.json):
#   primary  = VAL_LOCALIZATION_RECALL  (MAXIMISE)
#   tiebreak = VAL_LOSS                 (MINIMISE)
# VAL_LOCALIZATION_RECALL is component recall at the FIXED decode
# (threshold=0.10, margin=0.20, top_k=5, nms=0.30). In the Phase-13B trainer the
# per-config search grid already evaluates exactly that configuration, so
# VAL_LOCALIZATION_RECALL == overall_recall90 at (thr=0.10, margin=0.20, top_k=5).
H3_SUPPLY_SELECTION_LABEL = "H3_SUPPLY_MAX_VAL_LOCALIZATION_RECALL_TIEBREAK_VAL_LOSS"
H3_SUPPLY_TERM_NAMES: Tuple[str, ...] = ("val_localization_recall", "negative_val_loss")


@dataclass(frozen=True)
class H3SupplySelectionOutcome:
    """Result of one epoch's H3 supply-axis 2-term selection decision."""

    score: Optional[Tuple[float, float]]
    is_new_best: bool
    bad_epochs: int
    best_score: Optional[Tuple[float, float]]
    best_epoch: Optional[int]
    stopped: bool
    term_names: Tuple[str, ...] = H3_SUPPLY_TERM_NAMES
    selection_label: str = H3_SUPPLY_SELECTION_LABEL


def build_h3_supply_selection_tuple(
    val_localization_recall: float,
    val_loss: float,
) -> Tuple[float, float]:
    """Return the frozen H3 supply 2-term tuple with NO rounding.

    Term 2 is negated so a plain tuple ``>`` comparison IS the required
    "maximise localization recall, then minimise val loss" rule.
    """
    for name, value in (
        ("val_localization_recall", val_localization_recall),
        ("val_loss", val_loss),
    ):
        if value is None:
            raise ValueError(f"{name} is None; both H3 supply terms are mandatory")
        if isinstance(value, float) and (value != value):
            raise ValueError(f"{name} is NaN; refusing to score a non-finite epoch")
        if value in (float("inf"), float("-inf")):
            raise ValueError(f"{name} is Inf; refusing to score a non-finite epoch")
    return (float(val_localization_recall), -float(val_loss))


def select_h3_supply_epoch(
    val_localization_recall: float,
    val_loss: float,
    best_score: Optional[Sequence[float]] = None,
    best_epoch: Optional[int] = None,
    bad_epochs: int = 0,
    epoch: Optional[int] = None,
    patience: int = 15,
) -> H3SupplySelectionOutcome:
    """Apply the frozen H3 supply-axis 2-term selection decision.

    Pure and side-effect free. Maximises VAL_LOCALIZATION_RECALL, breaking ties
    on lower VAL_LOSS. Early stopping uses the same bad-epoch patience semantics
    as the R2 rule.
    """
    score = build_h3_supply_selection_tuple(val_localization_recall, val_loss)
    improved = is_strict_improvement(score, best_score)

    if improved:
        new_best_score = score
        new_best_epoch = epoch if epoch is not None else best_epoch
        new_bad_epochs = 0
    else:
        new_best_score = None if best_score is None else tuple(best_score)
        new_best_epoch = best_epoch
        new_bad_epochs = bad_epochs + 1

    stopped = bool(patience > 0 and new_bad_epochs >= patience
                   and new_best_score is not None)

    return H3SupplySelectionOutcome(
        score=score,
        is_new_best=improved,
        bad_epochs=new_bad_epochs,
        best_score=new_best_score,
        best_epoch=new_best_epoch,
        stopped=stopped,
    )


__all__ = [
    "SELECTION_TERM_NAMES",
    "DIAGNOSTIC_TERM_NAMES",
    "SELECTION_LABEL",
    "H3_SUPPLY_SELECTION_LABEL",
    "H3_SUPPLY_TERM_NAMES",
    "SelectionOutcome",
    "H3SupplySelectionOutcome",
    "build_selection_tuple",
    "selection_terms_from_epoch_metrics",
    "is_strict_improvement",
    "select_epoch",
    "build_h3_supply_selection_tuple",
    "select_h3_supply_epoch",
]
