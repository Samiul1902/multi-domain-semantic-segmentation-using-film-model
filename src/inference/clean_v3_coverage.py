"""PHASE-13 PART-1B R2C — explicit coverage-semantics helpers.

R2C arbitration: the PRIMARY checkpoint-selection coverage semantics are
``HISTORICAL_EXECUTING_BBOX_COVERAGE``. The historical executing path
(``gt_components`` -> ``evaluate_roi_coverage``) never attached component masks,
so ``evaluate_roi_coverage`` always took its BBOX fallback branch.

This module makes that semantics EXPLICIT instead of relying on a silent
fallback, and keeps pixel-mask coverage available as an explicitly named
SECONDARY sensitivity metric.

Authoritative source for the bbox branch (verbatim, unmodified):
``src/inference/predicted_roi.py::evaluate_roi_coverage`` else-branch:

    intersection_y = max(0, min(y2 + 1, geometry["clip_y2"]) - max(y1, geometry["clip_y1"]))
    intersection_x = max(0, min(x2 + 1, geometry["clip_x2"]) - max(x1, geometry["clip_x1"]))
    coverage = float(intersection_y * intersection_x / ((y2-y1+1)*(x2-x1+1)))

No new formula is inferred from prose. This reproduces the executing behaviour.

No training. No model. No CUDA. No TEST.
"""
from __future__ import annotations

import numpy as np

BBOX_SEMANTICS = "HISTORICAL_EXECUTING_BBOX_COVERAGE"
PIXEL_SEMANTICS = "PIXEL_MASK_COMPONENT_COVERAGE"


def _result(component_id, coverage, best_proposal):
    return {
        "component_id": component_id,
        "coverage_fraction": coverage,
        "covered90": coverage >= 0.90,
        "covered50": coverage >= 0.50,
        "any_overlap": coverage > 0,
        "best_proposal_rank": best_proposal["rank"] if best_proposal else np.nan,
        "best_proposal_score": best_proposal["score"] if best_proposal else np.nan,
        "best_roi_coordinates": (
            best_proposal["crop_geometry"] if best_proposal else None
        ),
    }


def evaluate_historical_bbox_coverage(proposals, gt_components):
    """EXPLICIT historical bbox-intersection coverage.

    Reproduces the executing fallback bit-for-bit. Component masks are
    deliberately IGNORED even when present, so the primary semantics cannot
    silently change.
    """
    results = []
    for component in gt_components:
        y1, x1, y2, x2 = (
            int(component[key]) for key in ("min_y", "min_x", "max_y", "max_x")
        )
        best_coverage, best_proposal = 0.0, None
        for proposal in proposals:
            geometry = proposal["crop_geometry"]
            intersection_y = max(
                0, min(y2 + 1, geometry["clip_y2"]) - max(y1, geometry["clip_y1"])
            )
            intersection_x = max(
                0, min(x2 + 1, geometry["clip_x2"]) - max(x1, geometry["clip_x1"])
            )
            coverage = float(
                intersection_y * intersection_x / ((y2 - y1 + 1) * (x2 - x1 + 1))
            )
            if coverage > best_coverage:
                best_coverage, best_proposal = coverage, proposal
        results.append(
            _result(component["component_id"], best_coverage, best_proposal)
        )
    return results


def evaluate_pixel_mask_coverage(proposals, gt_components):
    """EXPLICIT native pixel-mask coverage (SECONDARY sensitivity only).

    Fails loudly if any component lacks a usable mask — no silent bbox fallback.
    """
    results = []
    for component in gt_components:
        mask = component.get("mask")
        if mask is None:
            raise ValueError(
                f"component {component.get('component_id')} has no native mask; "
                "pixel coverage cannot be evaluated without silent bbox fallback"
            )
        total = int(mask.sum())
        if total == 0:
            raise ValueError(
                f"component {component.get('component_id')} has an empty mask"
            )
        best_coverage, best_proposal = 0.0, None
        for proposal in proposals:
            geometry = proposal["crop_geometry"]
            inside = mask[
                geometry["clip_y1"]:geometry["clip_y2"],
                geometry["clip_x1"]:geometry["clip_x2"],
            ].sum()
            coverage = float(inside / total)
            if coverage > best_coverage:
                best_coverage, best_proposal = coverage, proposal
        results.append(
            _result(component["component_id"], best_coverage, best_proposal)
        )
    return results
