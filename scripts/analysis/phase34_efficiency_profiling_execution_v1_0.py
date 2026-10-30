#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 - Computational Efficiency & Runtime Profiling: FUTURE EXECUTION HARNESS.

Classification: PRE_EXECUTION_COMPUTATIONAL_EFFICIENCY_RUNTIME_AND_CONDITIONAL_
                COMPUTATION_PROFILING_SPECIFICATION__EXECUTION_HARNESS
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_0

!! ZERO-EXECUTION GUARD !!
This file is SOURCE-FROZEN but MUST NOT be executed during the specification task.
Importing this module performs NO model construction, NO checkpoint load, NO forward
pass, NO CUDA timing and NO memory measurement. All heavy work lives inside main(),
which requires the explicit environment gate PHASE34_EXECUTE=1.

Protected-data guards: this harness NEVER reads ROUTER_HOLDOUT images/GT, NEVER reads
TEST images/GT, and NEVER trains. Primary benchmarking uses deterministic synthetic
tensors only.

Run (only after an explicit future execution authorization):
    PHASE34_EXECUTE=1 python scripts/analysis/phase34_efficiency_profiling_execution_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_0"
METHOD = "RA-MedFiLM-BARR"

# ----------------------------- frozen component registry ----------------------------- #
COMPONENTS = {
    "G": {
        "symbol": "G", "model_class": "GlobalMedFiLM",
        "source_file": "src/models/film/global_medfilm.py",
        "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
        "checkpoint_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "conditional": False, "input_shape": [1, 3, 512, 512],
        "historical_params": 3523001, "historical_macs": 31551740928,
    },
    "R_psi": {
        "symbol": "R_psi", "model_class": "BARRRegionalRefinerV1",
        "source_file": "src/models/barr/regional_refiner.py",
        "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
        "checkpoint_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
        "conditional": True, "input_shape": [1, 4, 256, 256],
        "historical_params": 1276401, "historical_macs": 3230662656,
    },
    "B_phi": {
        "symbol": "B_phi", "model_class": "BARRBenefitRouterV1",
        "source_file": "src/models/barr/router_variants.py",
        "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
        "checkpoint_sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
        "conditional": True, "input_shape": [1, 218],
        "historical_params": 36801, "historical_macs": 36160,
    },
    "S_omega": {
        "symbol": "S_omega", "model_class": "BARRPostSafetyV1",
        "source_file": "src/models/barr/ra_medfilm_barr.py",
        "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
        "checkpoint_sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
        "conditional": True, "input_shape": [1, 20],
        "historical_params": 1217, "historical_macs": 1168,
    },
}

# ----------------------------- frozen protocol constants ----------------------------- #
PRIMARY_LATENCY_BATCH_SIZE = 1
SECONDARY_THROUGHPUT_BATCH_SIZE = 8          # eligible: canonical batch 8 interface
WARMUP_ITERATIONS = 50
MEASUREMENT_BLOCKS = 5
MEASURED_ITERATIONS_PER_BLOCK = 200
TIMER = "CUDA_EVENTS_PRIMARY__SYNCHRONIZED_WALL_CLOCK_CROSS_CHECK"
SYNTHETIC_SEED = 42
SYNTHETIC_GENERATOR = "torch.Generator(device='cuda').manual_seed(42)"

# Frozen state-machine compute model (Phase26 state_machine_contract):
#   FORCED_SKIP        refiner=0 s_omega=0
#   SKIP_GLOBAL        refiner=0 s_omega=0
#   EXECUTE_THEN_ACCEPT refiner=1 s_omega=1
#   EXECUTE_THEN_REJECT refiner=1 s_omega=1   <-- identical compute to ACCEPT
STATE_COMPUTE = {
    "FORCED_SKIP": {"refiner": 0, "s_omega": 0},
    "SKIP_GLOBAL": {"refiner": 0, "s_omega": 0},
    "EXECUTE_THEN_ACCEPT": {"refiner": 1, "s_omega": 1},
    "EXECUTE_THEN_REJECT": {"refiner": 1, "s_omega": 1},
}

# Frozen Phase30 ROUTER_HOLDOUT routing-state frequencies (weights only; never re-derived)
PHASE30_FREQ = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}
PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")

FORBIDDEN_PATH_TOKENS = ("router_holdout", "test", "external")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def guard_no_protected_data(paths):
    """Fail closed if any candidate path looks like protected raw data."""
    for p in paths:
        low = str(p).lower().replace("\\", "/")
        if any(tok in low for tok in FORBIDDEN_PATH_TOKENS):
            raise RuntimeError(f"PROTECTED-DATA GUARD TRIPPED: {p}")


# ----------------------------- pipeline stages ----------------------------- #
def validate_environment() -> dict:
    import platform
    import torch
    env = {
        "platform": platform.platform(), "python": platform.python_version(),
        "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
        "cudnn": torch.backends.cudnn.version(), "cuda_available": torch.cuda.is_available(),
    }
    if not env["cuda_available"]:
        raise RuntimeError("GPU batch profiling requires CUDA; mark family INELIGIBLE.")
    prop = torch.cuda.get_device_properties(0)
    env.update({"gpu": prop.name, "cc": f"{prop.major}.{prop.minor}",
                "vram_bytes": prop.total_memory})
    return env


def validate_checkpoints() -> dict:
    out = {}
    for k, c in COMPONENTS.items():
        p = ROOT / c["checkpoint"]
        obs = sha256_file(p)
        out[k] = {"path": c["checkpoint"], "expected": c["checkpoint_sha256"],
                  "observed": obs, "match": obs == c["checkpoint_sha256"]}
        if obs != c["checkpoint_sha256"]:
            raise RuntimeError(f"CHECKPOINT SHA MISMATCH {k}: {obs}")
    return out


def build_synthetic_input(symbol: str, batch_size: int):
    """Deterministic synthetic tensors matching the canonical interface. No real data."""
    import torch
    shape = [batch_size] + COMPONENTS[symbol]["input_shape"][1:]
    g = torch.Generator(device="cuda").manual_seed(SYNTHETIC_SEED)
    return torch.randn(*shape, generator=g, device="cuda", dtype=torch.float32)


def count_parameters(model) -> dict:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total_parameters": total, "trainable_parameters": trainable,
            "non_trainable_parameters": total - trainable}


def analytical_compute_report() -> dict:
    """Historical ANALYTICAL MAC LOWER BOUND - re-reported, NOT recomputed."""
    g = COMPONENTS["G"]["historical_macs"]
    b = COMPONENTS["B_phi"]["historical_macs"]
    r = COMPONENTS["R_psi"]["historical_macs"]
    s = COMPONENTS["S_omega"]["historical_macs"]
    p_exec = PHASE30_FREQ["EXECUTE_THEN_ACCEPT"] + PHASE30_FREQ["EXECUTE_THEN_REJECT"]
    p_act = p_exec / PHASE30_FREQ["n"]
    return {
        "label": "ANALYTICAL MAC LOWER BOUND",
        "component_macs": {"G": g, "B_phi": b, "R_psi": r, "S_omega": s},
        "global_only_macs": g,
        "always_refine_macs": g + b + r + s,
        "activation_fraction": p_act,
        "expected_conditional_macs": g + b + p_act * (r + s),
        "formula": "E[MAC] = MAC(G) + MAC(B_phi) + p_activate*(MAC(R_psi)+MAC(S_omega))",
        "phase30_qualifier": PHASE30_QUALIFIER,
    }


def _sync():
    import torch
    torch.cuda.synchronize()


def time_latency(fn, warmup=WARMUP_ITERATIONS, blocks=MEASUREMENT_BLOCKS,
                 iters=MEASURED_ITERATIONS_PER_BLOCK):
    """Synchronized CUDA-event latency protocol (frozen)."""
    import torch
    for _ in range(warmup):
        fn()
    _sync()
    obs = []
    for _ in range(blocks):
        start, end = torch.cuda.Event(True), torch.cuda.Event(True)
        t0 = time.perf_counter()
        start.record()
        for _ in range(iters):
            fn()
        end.record()
        _sync()
        wall = time.perf_counter() - t0
        obs.append((start.elapsed_time(end), wall))
    ms = sorted(o[0] for o in obs)
    wall = sorted(o[1] for o in obs)
    n = blocks * iters
    return {"n_observations": n, "blocks": blocks, "iters_per_block": iters,
            "mean_latency_ms": sum(ms) / len(ms), "min_ms": ms[0], "max_ms": ms[-1],
            "median_ms": ms[len(ms) // 2],
            "wall_clock_block_seconds": wall}


def time_throughput(fn, batch_size: int, blocks=MEASUREMENT_BLOCKS,
                    iters=MEASURED_ITERATIONS_PER_BLOCK):
    """FPS = processed_samples / synchronized wall-clock interval (NOT 1000/mean)."""
    import torch
    for _ in range(WARMUP_ITERATIONS):
        fn()
    _sync()
    t0 = time.perf_counter()
    for _ in range(blocks * iters):
        fn()
    _sync()
    wall = time.perf_counter() - t0
    processed = blocks * iters * batch_size
    return {"batch_size": batch_size, "processed_samples": processed,
            "wall_seconds": wall, "fps": processed / wall}


def measure_memory(fn) -> dict:
    import torch
    torch.cuda.empty_cache()
    base_alloc = torch.cuda.memory_allocated()
    base_res = torch.cuda.memory_reserved()
    torch.cuda.reset_peak_memory_stats()
    fn()
    _sync()
    return {"baseline_GPU_allocated_after_model_load": base_alloc,
            "baseline_GPU_reserved_after_model_load": base_res,
            "peak_GPU_allocated_during_inference": torch.cuda.max_memory_allocated(),
            "peak_GPU_reserved_during_inference": torch.cuda.max_memory_reserved(),
            "incremental_peak_allocated_over_loaded_baseline":
                torch.cuda.max_memory_allocated() - base_alloc}


def conditional_weighting(measured: dict) -> dict:
    """WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE from frozen Phase30 frequencies."""
    n = PHASE30_FREQ["n"]
    skip = PHASE30_FREQ["SKIP"] / n
    ex = (PHASE30_FREQ["EXECUTE_THEN_ACCEPT"] + PHASE30_FREQ["EXECUTE_THEN_REJECT"]) / n
    return {"label": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
            "p_skip": skip, "p_execute": ex,
            "expected_latency_ms": skip * measured["skip_ms"] + ex * measured["execute_ms"],
            "phase30_qualifier": PHASE30_QUALIFIER,
            "not_direct_holdout_runtime": True}


def _run_isolated_worker(arm_id: str, batch_size: int, mode: str) -> dict:
    """Each measured arm/path runs in a FRESH subprocess (frozen isolation rule)."""
    worker = ROOT / "scripts" / "analysis" / "phase34_efficiency_profiling_worker_v1_0.py"
    cmd = [sys.executable, str(worker), "--arm", arm_id,
           "--batch", str(batch_size), "--mode", mode]
    env = dict(os.environ, PHASE34_EXECUTE="1")
    r = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(ROOT))
    if r.returncode != 0:
        raise RuntimeError(f"worker failed for {arm_id}: {r.stderr[-2000:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def main() -> int:
    if os.environ.get("PHASE34_EXECUTE") != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2
    guard_no_protected_data([c["checkpoint"] for c in COMPONENTS.values()])
    report = {
        "revision": REVISION, "method": METHOD,
        "environment": validate_environment(),
        "checkpoints": validate_checkpoints(),
        "analytical_compute": analytical_compute_report(),
        "arms": [], "generated_utc": None,
    }
    for arm in ("GLOBAL_ONLY", "FINAL_ROUTED_A8_C9"):
        for bs, mode in ((PRIMARY_LATENCY_BATCH_SIZE, "latency"),
                         (SECONDARY_THROUGHPUT_BATCH_SIZE, "throughput")):
            report["arms"].append(_run_isolated_worker(arm, bs, mode))
    out = AUD / "phase34_efficiency_profiling_execution_results_v1_0.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
