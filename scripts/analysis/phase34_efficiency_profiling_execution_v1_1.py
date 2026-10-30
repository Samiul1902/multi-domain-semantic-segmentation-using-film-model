#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.1 - Computational Efficiency & Runtime Profiling: FUTURE EXECUTION HARNESS.

Classification: PRE_EXECUTION_RUNTIME_NUMERICAL_SEMANTICS_AND_ANALYTICAL_COMPARATOR_
                RECONCILIATION__EXECUTION_HARNESS
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_1

SUPERSEDES the v1.0 harness for FUTURE measurement. The v1.0 harness
(`phase34_efficiency_profiling_execution_v1_0.py`) is PRESERVED byte-for-byte but MUST NOT
be used, because it flattened the canonical component-specific inference semantics into a
uniform FP32 / autocast-OFF protocol.

!! ZERO-EXECUTION GUARD !!
Importing this module performs NO model construction, NO checkpoint load, NO forward pass,
NO CUDA timing and NO memory measurement. All heavy work lives in main(), gated on
PHASE34_EXECUTE=1.

CORRECTED COMPONENT SEMANTICS (bound from
reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json and
reports/audits/phase30_component_inference_semantics_contract.json):
  G       : cuda, eval, float32, autocast(fp16) ENABLED, torch.no_grad(), inference_mode FALSE
  R_psi   : cuda, eval, float32, autocast DISABLED, torch.inference_mode()
  B_phi   : cuda, eval, float32, autocast DISABLED, torch.inference_mode()
  S_omega : cuda, eval, float32, autocast DISABLED, torch.inference_mode()

INVARIANT: G autocast semantics MUST NOT be applied to R_psi/B_phi/S_omega.
INVARIANT: uniform FP32/no-autocast MUST NOT replace G's canonical runtime semantics.

Protected data: this harness NEVER reads ROUTER_HOLDOUT images/GT, NEVER reads TEST
images/GT and NEVER trains. Benchmarking uses deterministic synthetic tensors only.
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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_1"
METHOD = "RA-MedFiLM-BARR"

PRIMARY_LATENCY_BATCH_SIZE = 1
SECONDARY_THROUGHPUT_BATCH_SIZE = 8
WARMUP_ITERATIONS = 50
MEASUREMENT_BLOCKS = 5
MEASURED_ITERATIONS_PER_BLOCK = 200
SYNTHETIC_SEED = 42

# --- canonical component-specific precision semantics (v1.1, corrected) --- #
COMPONENT_SEMANTICS = {
    "G": {"autocast_enabled": True, "autocast_dtype": "float16",
          "grad_context": "torch.no_grad()", "inference_mode": False,
          "batch_size_scientific": 8, "input_shape": [1, 3, 512, 512]},
    "R_psi": {"autocast_enabled": False, "autocast_dtype": None,
              "grad_context": "torch.inference_mode()", "inference_mode": True,
              "batch_size_scientific": 8, "input_shape": [1, 4, 256, 256]},
    "B_phi": {"autocast_enabled": False, "autocast_dtype": None,
              "grad_context": "torch.inference_mode()", "inference_mode": True,
              "batch_size_scientific": "FULL_MATRIX_SINGLE_FORWARD",
              "input_shape": [1, 218]},
    "S_omega": {"autocast_enabled": False, "autocast_dtype": None,
                "grad_context": "torch.inference_mode()", "inference_mode": True,
                "batch_size_scientific": 128, "input_shape": [1, 20]},
}

COMPONENTS = {
    "G": {"model_class": "GlobalMedFiLM",
          "source_file": "src/models/film/global_medfilm.py",
          "checkpoint": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
          "checkpoint_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
          "historical_params": 3523001, "historical_macs": 31551740928},
    "R_psi": {"model_class": "BARRRegionalRefinerV1",
              "source_file": "src/models/barr/regional_refiner.py",
              "checkpoint": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
              "checkpoint_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
              "historical_params": 1276401, "historical_macs": 3230662656},
    "B_phi": {"model_class": "BARRBenefitRouterV1",
              "source_file": "src/models/barr/router_variants.py",
              "checkpoint": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
              "checkpoint_sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
              "historical_params": 36801, "historical_macs": 36160},
    "S_omega": {"model_class": "BARRPostSafetyV1",
                "source_file": "src/models/barr/ra_medfilm_barr.py",
                "checkpoint": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                "checkpoint_sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
                "historical_params": 1217, "historical_macs": 1168},
}

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
    for p in paths:
        low = str(p).lower().replace("\\", "/")
        if any(tok in low for tok in FORBIDDEN_PATH_TOKENS):
            raise RuntimeError(f"PROTECTED-DATA GUARD TRIPPED: {p}")


# --------------------------------------------------------------------------- #
# Canonical forward contexts. G is the ONLY component under autocast(fp16).
# --------------------------------------------------------------------------- #
def forward_G(model, x):
    """G canonical: eval + float32 + autocast(fp16) + torch.no_grad() (NOT inference_mode)."""
    import torch
    with torch.no_grad():
        with torch.amp.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
            out = model(x)
    return torch.sigmoid(out.float())


def forward_no_autocast(model, x):
    """R_psi / B_phi / S_omega canonical: eval + float32 + autocast OFF + inference_mode."""
    import torch
    with torch.inference_mode():
        out = model(x)
    return out


FORWARD_FN = {"G": forward_G, "R_psi": forward_no_autocast,
              "B_phi": forward_no_autocast, "S_omega": forward_no_autocast}


def validate_environment() -> dict:
    import platform
    import torch
    env = {"platform": platform.platform(), "python": platform.python_version(),
           "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
           "cudnn": torch.backends.cudnn.version(),
           "cuda_available": torch.cuda.is_available()}
    if not env["cuda_available"]:
        raise RuntimeError("GPU profiling requires CUDA; mark family INELIGIBLE.")
    prop = torch.cuda.get_device_properties(0)
    env.update({"gpu": prop.name, "cc": f"{prop.major}.{prop.minor}",
                "vram_bytes": prop.total_memory})
    return env


def validate_checkpoints() -> dict:
    out = {}
    for k, c in COMPONENTS.items():
        obs = sha256_file(ROOT / c["checkpoint"])
        out[k] = {"expected": c["checkpoint_sha256"], "observed": obs,
                  "match": obs == c["checkpoint_sha256"]}
        if obs != c["checkpoint_sha256"]:
            raise RuntimeError(f"CHECKPOINT SHA MISMATCH {k}: {obs}")
    return out


def build_synthetic_input(symbol: str, batch_size: int):
    import torch
    shape = [batch_size] + COMPONENT_SEMANTICS[symbol]["input_shape"][1:]
    g = torch.Generator(device="cuda").manual_seed(SYNTHETIC_SEED)
    return torch.randn(*shape, generator=g, device="cuda", dtype=torch.float32)


def count_parameters(model) -> dict:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total_parameters": total, "trainable_parameters": trainable,
            "non_trainable_parameters": total - trainable}


def analytical_compute_report() -> dict:
    """Frozen predecessor ANALYTICAL MAC LOWER BOUND values (re-reported, not recomputed)."""
    g = COMPONENTS["G"]["historical_macs"]
    b = COMPONENTS["B_phi"]["historical_macs"]
    r = COMPONENTS["R_psi"]["historical_macs"]
    s = COMPONENTS["S_omega"]["historical_macs"]
    p_act = 240 / 875
    return {
        "label": "ANALYTICAL MAC LOWER BOUND",
        "literal_global_only_C1": {"mac": g, "router": False, "refiner": False,
                                   "s_omega": False},
        "literal_always_refine_C2": {"mac": g + r, "router": False, "refiner": True,
                                     "s_omega": False},
        "final_A8_C9_expected_conditional": {"mac": g + b + p_act * (r + s),
                                             "p_activate": p_act},
        "gated_execute_all_C9": {"mac": g + b + r + s, "router": True, "refiner": True,
                                 "s_omega": True},
        "phase25e_gated_K_N_eligible_pre_gate": {"mac": g + b + r, "router": True,
                                                 "refiner": True, "s_omega": False},
        "phase30_qualifier": PHASE30_QUALIFIER,
    }


def _sync():
    import torch
    torch.cuda.synchronize()


def time_latency(fn, warmup=WARMUP_ITERATIONS, blocks=MEASUREMENT_BLOCKS,
                 iters=MEASURED_ITERATIONS_PER_BLOCK):
    import torch
    for _ in range(warmup):
        fn()
    _sync()
    ms = []
    for _ in range(blocks):
        start, end = torch.cuda.Event(True), torch.cuda.Event(True)
        start.record()
        for _ in range(iters):
            fn()
        end.record()
        _sync()
        ms.append(start.elapsed_time(end))
    ms.sort()
    return {"n_observations": blocks * iters, "mean_latency_ms": sum(ms) / len(ms),
            "min_ms": ms[0], "max_ms": ms[-1], "median_ms": ms[len(ms) // 2],
            "scope": "MODEL_COMPUTE_PATH_RUNTIME"}


def time_throughput(fn, batch_size: int, blocks=MEASUREMENT_BLOCKS,
                    iters=MEASURED_ITERATIONS_PER_BLOCK):
    import torch
    for _ in range(WARMUP_ITERATIONS):
        fn()
    _sync()
    t0 = time.perf_counter()
    for _ in range(blocks * iters):
        fn()
    _sync()
    wall = time.perf_counter() - t0
    return {"batch_size": batch_size, "processed_samples": blocks * iters * batch_size,
            "wall_seconds": wall, "fps": blocks * iters * batch_size / wall,
            "scope": "MODEL_COMPUTE_PATH_RUNTIME"}


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
    n = 875
    p_skip = 635 / n
    p_ex = 240 / n
    return {"label": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
            "expected_latency_ms": p_skip * measured["skip_ms"] + p_ex * measured["execute_ms"],
            "phase30_qualifier": PHASE30_QUALIFIER,
            "not_direct_holdout_runtime": True}


def _run_isolated_worker(arm_id: str, batch_size: int, mode: str) -> dict:
    worker = ROOT / "scripts" / "analysis" / "phase34_efficiency_profiling_worker_v1_1.py"
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
        "component_semantics": COMPONENT_SEMANTICS,
        "environment": validate_environment(),
        "checkpoints": validate_checkpoints(),
        "analytical_compute": analytical_compute_report(),
        "batch1_label":
            "CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_"
            "NUMERICAL_REPRODUCTION",
        "arms": [],
    }
    for arm in ("GLOBAL_ONLY_C1", "FINAL_ROUTED_A8_C9", "G_COMPONENT",
                "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT"):
        for bs, mode in ((PRIMARY_LATENCY_BATCH_SIZE, "latency"),
                         (SECONDARY_THROUGHPUT_BATCH_SIZE, "throughput")):
            report["arms"].append(_run_isolated_worker(arm, bs, mode))
    out = AUD / "phase34_efficiency_profiling_execution_results_v1_1.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
