#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.1 - isolated profiling worker (one arm x one batch size x one mode per process).

Classification: PRE_EXECUTION_RUNTIME_NUMERICAL_SEMANTICS_AND_ANALYTICAL_COMPARATOR_
                RECONCILIATION__ISOLATED_WORKER
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_1

SUPERSEDES the v1.0 worker for FUTURE measurement (v1.0 worker preserved byte-for-byte).
Fresh-subprocess isolation prevents CUDA allocator history from a prior arm biasing a later
arm. Synthetic inputs only; no protected data.

!! ZERO-EXECUTION GUARD !!  Requires PHASE34_EXECUTE=1.

Component precision semantics (v1.1 corrected):
  G       : autocast(fp16) ENABLED + torch.no_grad()   (NOT inference_mode)
  R_psi   : autocast DISABLED + torch.inference_mode()
  B_phi   : autocast DISABLED + torch.inference_mode()
  S_omega : autocast DISABLED + torch.inference_mode()
"""
from __future__ import annotations

import argparse
import json
import os
import time

REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_1"

WARMUP_ITERATIONS = 50
MEASUREMENT_BLOCKS = 5
MEASURED_ITERATIONS_PER_BLOCK = 200
SYNTHETIC_SEED = 42

# Frozen arm definitions (predecessor-defined paths only).
ARMS = {
    "GLOBAL_ONLY_C1": {"components": ["G"], "runtime_profile":
                       "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
                       "predecessor_authority": "Phase25E literal C1 anchor"},
    "FINAL_ROUTED_A8_C9": {"components": ["G", "B_phi", "R_psi", "S_omega"],
                           "runtime_profile":
                               "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
                           "predecessor_authority": "Phase26 canonical A8/C9 bundle"},
    "LITERAL_ALWAYS_REFINE_C2_ANALYTICAL_ONLY": {"components": ["G", "R_psi"],
                                                 "runtime_profile": "ANALYTICAL_ONLY",
                                                 "predecessor_authority":
                                                     "Phase25E literal C2 no-routing anchor"},
    "GATED_EXECUTE_ALL_C9_IF_PREDECESSOR_AUTHORIZED":
        {"components": ["G", "B_phi", "R_psi", "S_omega"],
         "runtime_profile": "ANALYTICAL_ONLY",
         "predecessor_authority": "Phase26 state machine, 100% activation"},
    "G_COMPONENT": {"components": ["G"], "runtime_profile":
                    "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
                    "predecessor_authority": "Phase26 component inventory"},
    "R_PSI_COMPONENT": {"components": ["R_psi"], "runtime_profile":
                        "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
                        "predecessor_authority": "Phase25A resource accounting"},
    "B_PHI_COMPONENT": {"components": ["B_phi"], "runtime_profile":
                        "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
                        "predecessor_authority": "Phase25D router"},
    "S_OMEGA_COMPONENT": {"components": ["S_omega"], "runtime_profile":
                          "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
                          "predecessor_authority": "Phase25F post-safety"},
}

BATCH1_LABEL = ("CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_"
                "NUMERICAL_REPRODUCTION")
BATCH8_LABEL = "SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK"


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

    # NOTE (execution-time only): construct models from the frozen component registry, load
    # canonical checkpoints, model.eval(), and run each component under its OWN canonical
    # precision context (G: autocast fp16 + no_grad; others: autocast off + inference_mode).
    result = {
        "arm": a.arm, "batch_size": a.batch, "mode": a.mode, "revision": REVISION,
        "runtime_profile": ARMS[a.arm]["runtime_profile"],
        "predecessor_authority": ARMS[a.arm]["predecessor_authority"],
        "warmup_iterations": WARMUP_ITERATIONS, "blocks": MEASUREMENT_BLOCKS,
        "iters_per_block": MEASURED_ITERATIONS_PER_BLOCK, "synthetic_seed": SYNTHETIC_SEED,
        "batch1_label": BATCH1_LABEL, "batch8_label": BATCH8_LABEL,
        "canonical_numerical_reproduction": False,
        "timing_scope": "MODEL_COMPUTE_PATH_RUNTIME",
        "status": "EXECUTION_PATH_DEFINED_NOT_RUN_IN_SPEC_TASK",
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
