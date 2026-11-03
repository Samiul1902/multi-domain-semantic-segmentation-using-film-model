"""Stage producers for the FULL three-seed family.

Each module exposes the same small surface::

    run(ctx, *, resume=False) -> dict        # produce the stage, return a record
    is_complete(ctx) -> bool                 # terminal-state check
    verify(ctx) -> dict                      # re-verify artifacts from disk

so the orchestrator can treat every stage uniformly.
"""
from __future__ import annotations

__all__ = ["global_stage", "cache_stage", "refiner_stage", "label_stage",
           "router_stage", "safety_stage"]
