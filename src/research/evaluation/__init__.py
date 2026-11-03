"""Phase C unified evaluation package.

Reuses, rather than re-implements:

* :mod:`src.metrics.evaluation_metrics` — pixel confusion, empty-mask taxonomy,
  boundary distances, bootstrap helpers
* :mod:`src.research.stage6.end_to_end` — the canonical GT-free G/R/B/S state
  machine that FULL and Lite both drive
* :mod:`src.research.full_pipeline` / :mod:`src.research.lite_pipeline` — the
  family bundles and their checkpoint verification
* :mod:`src.research.c3_baselines.experiment` — the five external architectures
  and the analytical MAC counter
* :mod:`src.research.stage6.matrix` — the eight model keys and the 24-cell layout

What this package deliberately does **not** do:

* it adds no second cell-acceptance gate — ``stage6.matrix.validate_cell`` keeps
  sole ownership of that decision;
* it produces no p-value — no frozen statistical protocol authorizes a
  confirmatory test for these comparisons, so every result is
  ``EXPLORATORY_UNCERTAINTY_ONLY``;
* it never converts a synthetic execution into an established research cell —
  ``research_cells_completed`` stays 0 unless a real, protocol-compliant VAL808
  evaluation has been published;
* it never reads the protected TEST1683 split, and it says so structurally rather
  than in prose (``protocol.assert_split_readable``).
"""
from __future__ import annotations

from . import adapters, efficiency, metrics, protocol, provenance, registry, reports, runner, stats

__all__ = ["adapters", "efficiency", "metrics", "protocol", "provenance", "registry",
           "reports", "runner", "stats"]
