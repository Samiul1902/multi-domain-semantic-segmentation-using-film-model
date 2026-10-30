#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.4 LATENCY-ONLY worker: one CUDA-event interval per individual forward.

Classification: LATENCY_GRANULARITY_REPAIR__PER_FORWARD_CUDA_EVENT_WORKER
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_4

Repairs DEFECT 1 of the v1.3 latency implementation: the v1.3 worker timed ONE 200-iteration
block per CUDA-event pair and mislabeled the 5 block totals as 1000 per-iteration observations.

This worker reuses the FROZEN v1.3 worker's constructors, strict checkpoint loading, synthetic
input builders, canonical precision contexts and arm definitions (import, not copy), and replaces
ONLY the timing granularity with a per-forward CUDA-event interval.

!! ZERO-EXECUTION GUARD !!  main() requires PHASE34_EXECUTE=1. Importing this module constructs
no model, deserializes no checkpoint, runs no forward and does not time CUDA.

Protected data: NEVER reads ROUTER_HOLDOUT images/GT, NEVER reads TEST, NEVER trains.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

# Frozen v1.3 semantics (constructors / strict load / precision contexts / inputs / arms).
import phase34_efficiency_profiling_worker_v1_3 as W3  # noqa: E402
import phase34_v1_2_common as C  # noqa: E402

ROOT = REPO_ROOT
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"
GATE_ENV = "PHASE34_EXECUTE"

# Frozen v1.4 latency contract
WARMUP_ITERATIONS = 50
MEASUREMENT_BLOCKS = 5
OBSERVATIONS_PER_BLOCK = 200
TOTAL_OBSERVATIONS = MEASUREMENT_BLOCKS * OBSERVATIONS_PER_BLOCK      # 1000
BATCH_SIZE = 1
TASK_COUNT = 4
QUANTILE_METHOD = "linear"
STD_DDOF = 1

# Exactly SIX canonical latency arms (aliases are NOT executed physically).
LATENCY_ARMS = ["GLOBAL_ONLY_C1", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
                "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]
ALIASES = {"G_COMPONENT": "GLOBAL_ONLY_C1", "FINAL_ROUTED_A8_C9": "EXECUTE_CONTROLLED_PATH"}
MODES = ("latency", "identity")


def _sync():
    import torch
    torch.cuda.synchronize()


def time_latency_per_forward(arm_id: str, step) -> tuple:
    """One CUDA-event interval per individual forward; 5 blocks x 200 observations."""
    import numpy as np
    import torch

    for k in range(WARMUP_ITERATIONS):
        step(k % TASK_COUNT)
    _sync()

    rows, values = [], []
    for block_id in range(MEASUREMENT_BLOCKS):
        starts = [torch.cuda.Event(enable_timing=True) for _ in range(OBSERVATIONS_PER_BLOCK)]
        ends = [torch.cuda.Event(enable_timing=True) for _ in range(OBSERVATIONS_PER_BLOCK)]
        for i in range(OBSERVATIONS_PER_BLOCK):
            gi = block_id * OBSERVATIONS_PER_BLOCK + i
            starts[i].record()
            step(gi % TASK_COUNT)
            ends[i].record()
        _sync()
        for i in range(OBSERVATIONS_PER_BLOCK):
            gi = block_id * OBSERVATIONS_PER_BLOCK + i
            ms = float(starts[i].elapsed_time(ends[i]))
            values.append(ms)
            rows.append({"arm": arm_id, "block_id": block_id,
                         "iteration_within_block": i, "global_iteration_index": gi,
                         "task_id": gi % TASK_COUNT, "latency_ms": ms})

    arr = np.asarray(values, dtype=np.float64)
    q = np.quantile(arr, [0.50, 0.90, 0.95, 0.99], method=QUANTILE_METHOD)
    summary = {
        "arm": arm_id, "n": int(arr.size), "batch_size": BATCH_SIZE,
        "warmup_count": WARMUP_ITERATIONS, "blocks": MEASUREMENT_BLOCKS,
        "observations_per_block": OBSERVATIONS_PER_BLOCK,
        "observation_unit": "ONE_MODEL_COMPUTE_PATH_FORWARD_AT_BATCH_1",
        "estimand": "PER_FORWARD_BATCH1_MODEL_COMPUTE_PATH_LATENCY_MS",
        "mean_ms": float(np.mean(arr, dtype=np.float64)),
        "std_ms": float(np.std(arr, ddof=STD_DDOF, dtype=np.float64)),
        "p50_ms": float(q[0]), "p90_ms": float(q[1]), "p95_ms": float(q[2]),
        "p99_ms": float(q[3]), "min_ms": float(np.min(arr)), "max_ms": float(np.max(arr)),
        "timer_type": "torch.cuda.Event(enable_timing=True) per individual forward + "
                      "torch.cuda.synchronize() once per block",
        "quantile_method": QUANTILE_METHOD, "std_ddof": STD_DDOF,
        "task_schedule": "global_iteration_index mod 4 (0=ISIC,1=BUSI,2=KVASIR,3=KUB)",
        "precision_semantics": "component-specific canonical",
        "task_condition_counts": {d: TOTAL_OBSERVATIONS // TASK_COUNT
                                  for d in ("ISIC", "BUSI", "KVASIR", "KUB")},
    }
    return summary, rows


def run_latency(arm_id: str, device: str = "cuda"):
    comps = C.ARMS[arm_id]["components"]
    models, meta = {}, {}
    for cid in comps:
        m, dev, info = W3.load_component(cid, device)
        models[cid], meta[cid] = m, info
    device_str = str(device)
    per_task = {t: {cid: W3.make_inputs(cid, BATCH_SIZE, device_str, t) for cid in comps}
                for t in C.TASK_ORDER}

    def step(key):
        bucket = per_task[key]
        for cid in comps:
            W3.call_component(models[cid], cid, bucket[cid])

    summary, rows = time_latency_per_forward(arm_id, step)
    summary["components"] = comps
    summary["component_meta"] = meta
    return summary, rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=LATENCY_ARMS)
    ap.add_argument("--mode", required=True, choices=list(MODES))
    a = ap.parse_args()

    if os.environ.get(GATE_ENV) != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    import torch
    if not torch.cuda.is_available():
        print(json.dumps({"arm": a.arm, "status": "INELIGIBLE_NO_CUDA"}))
        return 0

    out = {"arm": a.arm, "mode": a.mode, "revision": REVISION,
           "repo_root": str(REPO_ROOT), "repo_root_resolution": "FILE_RELATIVE",
           "aliases_not_executed": ALIASES,
           "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    if a.mode == "identity":
        comps = C.ARMS[a.arm]["components"]
        meta = {}
        for cid in comps:
            _, _, info = W3.load_component(cid, "cuda")
            meta[cid] = info
        out["components"] = meta
    else:
        summary, rows = run_latency(a.arm, "cuda")
        out["summary"] = summary
        out["observations"] = rows
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
