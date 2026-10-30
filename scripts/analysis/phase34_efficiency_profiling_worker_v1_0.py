#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 - isolated profiling worker (one arm x one batch size x one mode per process).

Classification: PRE_EXECUTION_COMPUTATIONAL_EFFICIENCY_RUNTIME_AND_CONDITIONAL_
                COMPUTATION_PROFILING_SPECIFICATION__ISOLATED_WORKER
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_0

!! ZERO-EXECUTION GUARD !!
Not executed during the specification task. Requires PHASE34_EXECUTE=1.
Fresh-subprocess isolation prevents CUDA allocator history from a prior arm biasing
a later arm (frozen process-isolation rule). Synthetic inputs only; no protected data.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_0"

WARMUP_ITERATIONS = 50
MEASUREMENT_BLOCKS = 5
MEASURED_ITERATIONS_PER_BLOCK = 200
SYNTHETIC_SEED = 42

# Frozen arm definitions (predecessor-defined paths only).
ARMS = {
    "GLOBAL_ONLY": {"components": ["G"], "states": ["SKIP_GLOBAL"],
                    "predecessor_authority": "Phase21 global-only baseline"},
    "FINAL_ROUTED_A8_C9": {"components": ["G", "B_phi", "R_psi", "S_omega"],
                           "states": ["EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"],
                           "predecessor_authority": "Phase26 canonical A8/C9 bundle"},
}


def _build(model, batch_size):
    import torch
    shapes = {"G": (batch_size, 3, 512, 512), "R_psi": (batch_size, 4, 256, 256),
              "B_phi": (batch_size, 218), "S_omega": (batch_size, 20)}
    g = torch.Generator(device="cuda").manual_seed(SYNTHETIC_SEED)
    return {k: torch.randn(*shapes[k], generator=g, device="cuda", dtype=torch.float32)
            for k in model}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=sorted(ARMS))
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--mode", required=True, choices=["latency", "throughput", "memory"])
    a = ap.parse_args()

    if os.environ.get("PHASE34_EXECUTE") != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    import torch
    if not torch.cuda.is_available():
        print(json.dumps({"arm": a.arm, "status": "INELIGIBLE_NO_CUDA"}))
        return 0

    # NOTE (execution-time only): construct models from the frozen component registry,
    # load the canonical checkpoints, model.eval(), torch.inference_mode(), then run the
    # frozen warmup / block protocol. All of that happens ONLY under PHASE34_EXECUTE=1.
    result = {
        "arm": a.arm, "batch_size": a.batch, "mode": a.mode, "revision": REVISION,
        "warmup_iterations": WARMUP_ITERATIONS, "blocks": MEASUREMENT_BLOCKS,
        "iters_per_block": MEASURED_ITERATIONS_PER_BLOCK,
        "synthetic_seed": SYNTHETIC_SEED,
        "predecessor_authority": ARMS[a.arm]["predecessor_authority"],
        "status": "EXECUTION_PATH_DEFINED_NOT_RUN_IN_SPEC_TASK",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
