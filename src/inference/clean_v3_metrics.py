"""PHASE-13 PART-1B R2B — clean-v3 VAL metric aggregation (frozen semantics).

Corrects three implementation defects while changing NO scientific definition:

  HARD_TINY_SAMPLE_LEVEL_INSTEAD_OF_COMPONENT_LEVEL
      -> hard_tiny_recovered90 = INTEGER COUNT of hard-Tiny COMPONENT rows whose
         covered90 is True (denominator 15). NOT a ratio, NOT sample-level.

  GLOBAL_EMPTY_GT_EMPTY_BRANCH_ERROR
      -> global_empty_images_covered90 = INTEGER COUNT of the 5 frozen image IDs
         for which ANY GT component has covered90 True (denominator 5).
         Evaluated even though global-empty images DO contain GT components.
         NOT restricted to a "no components" branch.

  MULTICOMPONENT_CASE_COMPLETE_INSTEAD_OF_COMPONENT_MEAN
      -> multi_component_recall90 = mean(covered90) over ALL COMPONENT ROWS of
         multi-component images (COMPONENT-level), NOT fraction of cases fully
         covered.

Reference: frozen historical executing semantics,
``scripts/training/train_phase13b_localizer.py`` lines 83 and 86.

Secondary diagnostics are NEVER selection terms.
No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import numpy as np

SECONDARY_DIAGNOSTIC_TERMS = (
    "hard_tiny_recovered90",
    "global_empty_images_covered90",
    "multi_component_recall90",
    "mean_proposals_per_image",
)

DESCRIPTIVE_TERMS = ("overall_recall50", "any_overlap_recall", "mean_coverage")


def _mean(values) -> float:
    return float(np.mean(values)) if len(values) else 0.0


def aggregate_clean_v3_metrics(
    component_rows,
    per_image_proposals,
    roial_area_fractions,
    multi_ids=frozenset(),
):
    """Aggregate coverage rows into the frozen clean-v3 VAL metric set.

    ``component_rows`` entries require:
        sample_id, size_stratum, hard_tiny, global_empty_image,
        coverage_fraction, covered90, covered50, any_overlap
    """
    if not component_rows:
        raise ValueError("aggregate_clean_v3_metrics received zero component rows")

    all_covered90 = [bool(r["covered90"]) for r in component_rows]
    all_covered50 = [bool(r["covered50"]) for r in component_rows]
    all_any = [bool(r["any_overlap"]) for r in component_rows]
    all_fraction = [float(r["coverage_fraction"]) for r in component_rows]

    tiny = [r for r in component_rows if r["size_stratum"] == "TINY"]
    hard = [r for r in component_rows if r["hard_tiny"]]
    empty = [r for r in component_rows if r["global_empty_image"]]
    multi = [r for r in component_rows if r["sample_id"] in multi_ids]

    # global-empty: distinct image IDs where ANY component is covered90
    empty_covered_ids = {r["sample_id"] for r in empty if r["covered90"]}

    return {
        # ---- PRIMARY (selection terms; val_loss joined by the caller) ----
        "tiny_recall90": _mean([bool(r["covered90"]) for r in tiny]),
        "overall_recall90": _mean(all_covered90),
        "mean_roi_area_fraction": _mean(roial_area_fractions),
        # ---- SECONDARY (diagnostics; never selection terms) ----
        "hard_tiny_recovered90": int(sum(1 for r in hard if r["covered90"])),
        "hard_tiny_total": int(len(hard)),
        "global_empty_images_covered90": int(len(empty_covered_ids)),
        "global_empty_total": int(len({r["sample_id"] for r in empty})),
        "multi_component_recall90": _mean([bool(r["covered90"]) for r in multi]),
        "mean_proposals_per_image": _mean(per_image_proposals),
        # ---- DESCRIPTIVE ----
        "overall_recall50": _mean(all_covered50),
        "any_overlap_recall": _mean(all_any),
        "mean_coverage": _mean(all_fraction),
        # ---- CONTROL ----
        "zero_denominator": bool(len(tiny) == 0 or len(component_rows) == 0),
    }


def multi_component_ids(component_rows) -> set:
    """Sample IDs having more than one native GT component (supervisor §10)."""
    counts = {}
    for row in component_rows:
        counts[row["sample_id"]] = counts.get(row["sample_id"], 0) + 1
    return {sid for sid, n in counts.items() if n > 1}
