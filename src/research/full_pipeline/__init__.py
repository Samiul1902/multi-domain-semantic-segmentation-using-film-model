"""FULL RA-MedFiLM-BARR — three-seed training pipeline (Phase A, coding only).

Package layout
--------------
``recipe``       frozen scientific constants inherited from Phases 21 / 25A / 25C /
                 25D / 25F.  Nothing here is re-derived; every value is traceable to a
                 canonical producer in this repository.
``provenance``   SHA-256 identity, atomic writes, checkpoint envelopes, family
                 compatibility enforcement.
``population``   population / fold membership resolution (frozen canonical tables, or
                 deterministically derived tables for synthetic populations).
``seeds``        seed-family registry and RNG control.
``stages``       the four producers G -> R -> B -> S plus the crop-cache and label
                 builders that connect them.
``orchestrator`` dependency resolution, resumable stage machine, stage plans.
``inference``    per-seed family loader + the verified Stage-6 GT-free adapter.
``cli``          the executable entry point.

The package never trains on VAL, never reads TEST, and never reads ROUTER_HOLDOUT.
Real execution remains subject to the existing authorization gates; this package
introduces no gate, mints no credential and bypasses nothing.
"""
from __future__ import annotations

__all__ = ["METHOD", "FAMILY", "SEEDS"]

METHOD = "RA-MedFiLM-BARR"
FAMILY = "FULL"
SEEDS = (42, 123, 3407)
