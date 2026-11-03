"""RA-MedFiLM-BARR-Lite training pipeline (Phase B).

A **separate, secondary** experiment.  The FULL family and its frozen protocol are
untouched: this package reuses the FULL stage producers through their
default-preserving injection points, and shares every scientific constant by
import rather than by restatement.

DAG (identical shape to FULL, different models in three nodes)::

    G_LITE -> CACHE_LITE -> R_LITE -> LABELS_LITE -> B_LITE -> S_LITE

``B_LITE`` and ``S_LITE`` are the canonical Phase-25 B_phi and S_omega producers,
unchanged, because those two models and their recipes are identical in both
families.

Nothing in this package starts a real training run.  A real run requires the
operator grant surface that already exists (see :mod:`.orchestrator`); a synthetic
run is always stamped ``synthetic: true`` and is never evidence.
"""
from __future__ import annotations

from . import context, features, recipe, strict_oof
from .context import LiteRunContext, lite_seed_family, make_lite_context

__all__ = [
    "LiteRunContext",
    "context",
    "features",
    "lite_seed_family",
    "make_lite_context",
    "recipe",
    "strict_oof",
]
