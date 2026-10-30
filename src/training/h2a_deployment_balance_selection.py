"""H2A deployment-balanced checkpoint selection (POST-PHASE-13 REVISION H2-A-B1).

Pure functions only. NO model, NO data, NO CUDA, NO forward pass.

Frozen by ``reports/audits/post_phase13_h2a_protocol_frozen.json``
(status ``SUPERVISOR_FROZEN_H2A_SELECTION_ONLY_READY_FOR_EXECUTION``).

PRIMARY selection rule (6-term strict lexicographic tuple):

    (DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90,
     tiny_recall90,
     overall_recall90,
     PROPOSAL_PIXEL_ANY_HIT_PRECISION,
     -mean_roi_area_fraction,
     -val_loss)

Terms 5 and 6 are already negated, so a plain tuple ``>`` comparison IS the
required rule. Inputs are NEVER rounded before comparison.

This module is a SEPARATE artifact from ``src/training/clean_v3_selection.py``,
which remains UNMODIFIED (Phase-13 lineage). The ONLY scientific change from
Phase-13 is the selection tuple itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

SELECTION_TERM_NAMES: Tuple[str, ...] = (
    "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90",
    "tiny_recall90",
    "overall_recall90",
    "PROPOSAL_PIXEL_ANY_HIT_PRECISION",
    "negative_mean_roi_area_fraction",
    "negative_val_loss",
)

SELECTION_TERM_LENGTH: int = 6

DIAGNOSTIC_TERM_NAMES: Tuple[str, ...] = (
    "hard_tiny_recovered90",
    "global_empty_images_covered90",
    "multi_component_recall90",
    "mean_proposals_per_image",
)

SELECTION_LABEL: str = "H2A_DEPLOYMENT_BALANCED_6TERM_FIXED_CONFIG_SELECTION"
UTILITY_LABEL: str = "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90"


def deployment_balance_hmean(P: float, T: float, O: float) -> float:
    """3 / (1/P + 1/T + 1/O), or 0.0 if any input is <= 0.

    NOT a statistical F1 score. NOT weighted. NOT clipped.
    """
    for name, value in (("P", P), ("T", T), ("O", O)):
        if value is None:
            raise ValueError(f"{name} is None; P/T/O are mandatory")
        if isinstance(value, float) and (value != value):
            raise ValueError(f"{name} is NaN; refusing to score a non-finite epoch")
        if value in (float("inf"), float("-inf")):
            raise ValueError(f"{name} is Inf; refusing to score a non-finite epoch")
    P, T, O = float(P), float(T), float(O)
    if P <= 0.0 or T <= 0.0 or O <= 0.0:
        return 0.0
    return 3.0 / (1.0 / P + 1.0 / T + 1.0 / O)


@dataclass(frozen=True)
class SelectionOutcome:
    """Result of one epoch's strict-lexicographic selection decision."""

    score: Optional[Tuple[float, ...]]
    is_new_best: bool
    bad_epochs: int
    best_score: Optional[Tuple[float, ...]]
    best_epoch: Optional[int]
    stopped: bool
    term_names: Tuple[str, ...] = SELECTION_TERM_NAMES
    selection_label: str = SELECTION_LABEL

    def as_row_fields(self) -> Dict[str, Any]:
        s = self.score if self.score is not None else (None,) * SELECTION_TERM_LENGTH
        return {
            "selection_term_1_deployment_balance_hmean": s[0],
            "selection_term_2_tiny_recall90": s[1],
            "selection_term_3_overall_recall90": s[2],
            "selection_term_4_proposal_pixel_any_hit_precision": s[3],
            "selection_term_5_negative_mean_roi_area_fraction": s[4],
            "selection_term_6_negative_val_loss": s[5],
            "selection_tuple": None if self.score is None else list(self.score),
            "selection_term_names": list(self.term_names),
            "is_new_best": self.is_new_best,
            "best_epoch_so_far": self.best_epoch,
            "bad_epochs": self.bad_epochs,
        }


def build_selection_tuple(
    deployment_balance_hmean: float,
    tiny_recall90: float,
    overall_recall90: float,
    proposal_pixel_any_hit_precision: float,
    mean_roi_area_fraction: float,
    val_loss: float,
) -> Tuple[float, ...]:
    """Return the frozen 6-term tuple with NO rounding."""
    for name, value in (
        ("deployment_balance_hmean", deployment_balance_hmean),
        ("tiny_recall90", tiny_recall90),
        ("overall_recall90", overall_recall90),
        ("proposal_pixel_any_hit_precision", proposal_pixel_any_hit_precision),
        ("mean_roi_area_fraction", mean_roi_area_fraction),
        ("val_loss", val_loss),
    ):
        if value is None:
            raise ValueError(f"{name} is None; the six primary terms are mandatory")
        if isinstance(value, float) and (value != value):
            raise ValueError(f"{name} is NaN; refusing to score a non-finite epoch")
        if value in (float("inf"), float("-inf")):
            raise ValueError(f"{name} is Inf; refusing to score a non-finite epoch")
    return (
        float(deployment_balance_hmean),
        float(tiny_recall90),
        float(overall_recall90),
        float(proposal_pixel_any_hit_precision),
        -float(mean_roi_area_fraction),
        -float(val_loss),
    )


def selection_terms_from_epoch_metrics(metrics: Mapping[str, Any]) -> Tuple[float, ...]:
    """Extract ONLY the six primary terms from a per-epoch metrics mapping."""
    def _pick(raw: str, negated: str) -> float:
        if raw in metrics:
            return float(metrics[raw])
        if negated in metrics:
            return -float(metrics[negated])
        raise KeyError(f"missing primary selection term {raw!r} (or {negated!r})")

    return (
        _pick("deployment_balance_hmean", "negative_deployment_balance_hmean"),
        _pick("tiny_recall90", "negative_tiny_recall90"),
        _pick("overall_recall90", "negative_overall_recall90"),
        _pick("proposal_pixel_any_hit_precision", "negative_proposal_pixel_any_hit_precision"),
        _pick("mean_roi_area_fraction", "negative_mean_roi_area_fraction"),
        _pick("val_loss", "negative_val_loss"),
    )


def is_strict_improvement(candidate: Sequence[float], best: Optional[Sequence[float]]) -> bool:
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
    deployment_balance_hmean: float,
    tiny_recall90: float,
    overall_recall90: float,
    proposal_pixel_any_hit_precision: float,
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
    """Apply the frozen H2A 6-term strict-lexicographic selection decision.

    Pure and side-effect free. ``proposal_configuration_count`` must be 1.
    """
    if proposal_configuration_count != 1:
        raise ValueError(
            "H2A training permits exactly ONE fixed proposal configuration; "
            f"got {proposal_configuration_count}. Grid search is disabled."
        )
    if zero_denominator:
        raise ValueError("zero_denominator_rule: STOP / CHECK_REQUIRED BEFORE TRAINING")

    score = build_selection_tuple(
        deployment_balance_hmean, tiny_recall90, overall_recall90,
        proposal_pixel_any_hit_precision, mean_roi_area_fraction, val_loss,
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

    stopped = bool(patience > 0 and new_bad_epochs >= patience and new_best_score is not None)

    return SelectionOutcome(
        score=score, is_new_best=improved, bad_epochs=new_bad_epochs,
        best_score=new_best_score, best_epoch=new_best_epoch, stopped=stopped,
    )


def proposal_pixel_any_hit_precision(hit_count: int, total_count: int) -> float:
    """P = hits / total, or 0.0 when the denominator is zero."""
    if total_count <= 0:
        return 0.0
    return float(hit_count) / float(total_count)


__all__ = [
    "SELECTION_TERM_NAMES", "SELECTION_TERM_LENGTH", "DIAGNOSTIC_TERM_NAMES",
    "SELECTION_LABEL", "UTILITY_LABEL", "SelectionOutcome",
    "deployment_balance_hmean", "build_selection_tuple",
    "selection_terms_from_epoch_metrics", "is_strict_improvement", "select_epoch",
    "proposal_pixel_any_hit_precision",
]
