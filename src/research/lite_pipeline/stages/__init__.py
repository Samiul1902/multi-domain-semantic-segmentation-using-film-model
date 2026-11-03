"""Lite stage adapters.

Each Lite stage is a *thin adapter* over the corresponding FULL producer, which
was parameterised (with default-preserving injection points) so that a different
model family can reuse it.  Nothing here re-implements a training loop, a fold
assignment, a label rule or a model class.

============================  ==================================================
stage                         implementation
============================  ==================================================
``G_LITE``                    ``global_stage.run`` + Lite model factory
``CACHE_LITE``                ``cache_stage.run`` + Lite loader + Lite features
``R_LITE``                    ``refiner_stage.run`` + Lite refiner factory
``LABELS_LITE``               ``label_stage.run`` + Lite refiner + Lite contract
``B_LITE``                    ``router_stage`` **unchanged**
``S_LITE``                    ``safety_stage`` **unchanged**
============================  ==================================================

The last two are not wrappers: B_phi and S_omega are the canonical Phase-25
models with the canonical recipes, so the canonical producers already do exactly
the right thing when handed a Lite context.  They are listed here so the DAG has
one import surface, and so it is obvious that no second definition exists.
"""
from __future__ import annotations

from src.research.full_pipeline.stages import (label_stage, refiner_stage,
                                              router_stage, safety_stage)

from . import cache_lite, global_lite, label_lite, refiner_lite

__all__ = [
    "G_LITE",
    "CACHE_LITE",
    "R_LITE",
    "LABELS_LITE",
    "B_LITE",
    "S_LITE",
    "MODULES",
]

G_LITE = global_lite
CACHE_LITE = cache_lite
R_LITE = refiner_lite
LABELS_LITE = label_lite
#: canonical producers, reused verbatim
B_LITE = router_stage
S_LITE = safety_stage

MODULES = {
    "G": G_LITE,
    "CACHE": CACHE_LITE,
    "R": R_LITE,
    "L": LABELS_LITE,
    "B": B_LITE,
    "S": S_LITE,
}
