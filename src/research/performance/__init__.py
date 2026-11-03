"""Phase D — performance, reliability and reproducibility engineering.

Every artifact this package produces is stamped ``SYNTHETIC_BENCHMARK``.  The
weights are fixtures, the routing decisions are scripted or incidental, and no
number here is a real-data segmentation result or a clinical claim.

Modules
-------
``bench``        the eight-model benchmark: init, forward, pipeline, pre/post,
                 percentiles, memory, MACs, cold vs warm, batch, precision
``conditional``  the four routing states, ROI edge cases, and
                 global-only vs always-refine vs conditional
``memory``       peak allocations for each training stage and inference path
``determinism``  seeding, loader order, RNG capture/restore, resume
``film``         functional verification of task conditioning
``faults``       injected failures at each pipeline stage
``isolation``    structural separation of synthetic from research evidence
``stability``    repeated-inference growth and handle leaks
``parity``       CPU versus CUDA agreement
``cli``          one runner for all of the above

What this package does not do: it does not train a real model, does not score a
protected split, and does not convert a synthetic artifact into research
evidence.
"""
from __future__ import annotations

from . import bench, conditional

__all__ = ["bench", "conditional"]
