#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.2 executable profiling worker (one arm x one batch x one mode per process).

Classification: PRE_MEASUREMENT_EXECUTABLE_HARNESS_AND_SYNTHETIC_TASK_CONDITIONING_
                BINDING_AMENDMENT__EXECUTABLE_WORKER
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_2

SUPERSEDES the non-executable v1.1 worker for future measurement (v1.1 preserved).

!! ZERO-EXECUTION GUARD !!
Everything below `main()` runs only when PHASE34_EXECUTE=1. Importing this module does NOT
construct a model, does NOT deserialize a checkpoint, does NOT run a forward and does NOT
touch CUDA. Static audit tasks must not require the gate.

Per-component canonical precision contexts (bound from phase29/phase30 authority):
  G       : eval + float32 + autocast(fp16) ENABLED + torch.no_grad()   (NOT inference_mode)
  R_psi   : eval + float32 + autocast OFF + torch.inference_mode()
  B_phi   : eval + float32 + autocast OFF + torch.inference_mode()
  S_omega : eval + float32 + autocast OFF + torch.inference_mode()

Protected data: NEVER reads ROUTER_HOLDOUT images/GT, NEVER reads TEST, NEVER trains.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase34_v1_2_common as C  # noqa: E402

ROOT = Path(r"D:\Softfors\jup")
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_2"
GATE_ENV = "PHASE34_EXECUTE"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# canonical model construction (constructor arguments taken from predecessor code)
# --------------------------------------------------------------------------- #
def _build_G(device):
    import json as _json

    import torch
    from src.models.film import GlobalMedFiLM
    spec = C.COMPONENTS["G"]
    cfg = _json.loads((ROOT / spec["config_file"]).read_text(encoding="utf-8"))["model"]
    model = GlobalMedFiLM(
        task_count=cfg["task_count"], in_channels=cfg["in_channels"],
        out_channels=cfg["out_channels"], channels=tuple(cfg["channels"]),
        task_embedding_dim=cfg["task_embedding_dim"], film_hidden_dim=cfg["film_hidden_dim"],
    )
    return model, torch.device(device)


def _build_R_psi(device):
    import torch
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    return BARRRegionalRefinerV1(), torch.device(device)


def _build_B_phi(device):
    """Rebuild the canonical Phase25D router class from its authoritative source file."""
    import torch
    from torch import nn
    src = (ROOT / "scripts/analysis/train_phase25d_router.py").read_text(encoding="utf-8")
    m = re.search(r"class BARRBenefitRouterV1\(nn\.Module\):.*?(?=\ndef count_params)", src,
                  re.S)
    if m is None:
        raise RuntimeError("canonical BARRBenefitRouterV1 class block not found")
    ns = {"__name__": "phase34_bphi_arch", "torch": torch, "nn": nn,
          "F": torch.nn.functional}
    exec("import torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n"
         + m.group(0), ns)
    return ns["BARRBenefitRouterV1"](), torch.device(device)


def _build_S_omega(device):
    import torch
    sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
    from phase25f_execution_common import BARRPostSafetyV1
    return BARRPostSafetyV1(), torch.device(device)


BUILDERS = {"G": _build_G, "R_psi": _build_R_psi, "B_phi": _build_B_phi,
            "S_omega": _build_S_omega}


def load_component(cid: str, device: str = "cuda"):
    """Verify checkpoint SHA -> construct -> strict load -> CUDA -> eval -> verify params."""
    import torch
    spec = C.COMPONENTS[cid]
    ckpt = ROOT / spec["checkpoint"]
    obs = sha256_file(ckpt)
    if obs != spec["checkpoint_sha256"]:
        raise RuntimeError(f"CHECKPOINT SHA MISMATCH {cid}: {obs}")
    model, dev = BUILDERS[cid](device)
    state = torch.load(ckpt, map_location="cpu", weights_only=False)
    if spec["state_dict_key"] not in state:
        raise RuntimeError(f"missing state_dict key {spec['state_dict_key']} for {cid}")
    res = model.load_state_dict(state[spec["state_dict_key"]], strict=True)
    if list(res.missing_keys):
        raise RuntimeError(f"STRICT LOAD missing keys {cid}: {list(res.missing_keys)}")
    if list(res.unexpected_keys):
        raise RuntimeError(f"STRICT LOAD unexpected keys {cid}: {list(res.unexpected_keys)}")
    model.to(dev)
    for p in model.parameters():
        p.requires_grad = False
    model.eval()
    n = sum(p.numel() for p in model.parameters())
    if n != spec["expected_parameters"]:
        raise RuntimeError(f"PARAMETER COUNT MISMATCH {cid}: {n} != "
                           f"{spec['expected_parameters']}")
    dtypes = {str(p.dtype) for p in model.parameters()}
    if dtypes != {"torch.float32"}:
        raise RuntimeError(f"PARAMETER DTYPE MISMATCH {cid}: {dtypes}")
    return model, dev, {"checkpoint_sha256": obs, "parameter_count": n,
                        "parameter_dtypes": sorted(dtypes),
                        "strict_load_missing_keys": list(res.missing_keys),
                        "strict_load_unexpected_keys": list(res.unexpected_keys)}


# --------------------------------------------------------------------------- #
# canonical execution contexts (G autocast must never leak into the others)
# --------------------------------------------------------------------------- #
def forward_G(model, images, task_ids):
    """eval + float32 + autocast(fp16) + torch.no_grad()  (NOT torch.inference_mode())."""
    import torch
    with torch.no_grad():
        with torch.amp.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
            logits = model(images, task_ids)
    return torch.sigmoid(logits.float())


def forward_R_psi(model, x):
    """eval + float32 + autocast disabled + torch.inference_mode()."""
    import torch
    with torch.inference_mode():
        out = model(x)
    return torch.sigmoid(out.float())


def forward_B_phi(model, feats, task_ids):
    """eval + float32 + autocast disabled + torch.inference_mode(); returns a raw logit."""
    import torch
    with torch.inference_mode():
        return model(feats, task_ids)


def forward_S_omega(model, x):
    """eval + float32 + autocast disabled + torch.inference_mode(); returns a raw logit."""
    import torch
    with torch.inference_mode():
        return model(x)


# --------------------------------------------------------------------------- #
# synthetic inputs
# --------------------------------------------------------------------------- #
def make_inputs(cid: str, batch_size: int, device: str, start_index: int = 0):
    if cid == "G":
        return (C.build_G_image(batch_size, device),
                C.build_G_task_ids(batch_size, start_index, device))
    if cid == "R_psi":
        return (C.build_Rpsi_input(batch_size, device),)
    if cid == "B_phi":
        return (C.build_Bphi_features(batch_size, device),
                C.build_G_task_ids(batch_size, start_index, device))
    if cid == "S_omega":
        return (C.build_Somega_features(batch_size, start_index, device),)
    raise ValueError(cid)


FORWARDS = {"G": forward_G, "R_psi": forward_R_psi, "B_phi": forward_B_phi,
            "S_omega": forward_S_omega}


def call_component(model, cid, args):
    return FORWARDS[cid](model, *args)


# --------------------------------------------------------------------------- #
# measurement primitives (synchronized CUDA events)
# --------------------------------------------------------------------------- #
def _sync():
    import torch
    torch.cuda.synchronize()


def time_latency(fn):
    """warmup=50, blocks=5, iterations_per_block=200, batch=1, synchronized CUDA Events."""
    import torch
    for k in range(C.WARMUP_ITERATIONS):
        fn(k % C.TASK_COUNT)
    _sync()
    per_block_ms, wall_ms = [], []
    for _ in range(C.MEASUREMENT_BLOCKS):
        start = torch.cuda.Event(enable_timing=True)
        end = torch.cuda.Event(enable_timing=True)
        _sync()
        t0 = time.perf_counter()
        start.record()
        for k in range(C.MEASURED_ITERATIONS_PER_BLOCK):
            fn(k % C.TASK_COUNT)
        end.record()
        _sync()
        end.synchronize()
        per_block_ms.append(start.elapsed_time(end))
        wall_ms.append((time.perf_counter() - t0) * 1000.0)
    ms = sorted(per_block_ms)
    n = C.MEASUREMENT_BLOCKS * C.MEASURED_ITERATIONS_PER_BLOCK
    return {
        "n_observations": n, "blocks": C.MEASUREMENT_BLOCKS,
        "iterations_per_block": C.MEASURED_ITERATIONS_PER_BLOCK,
        "batch_size": C.PRIMARY_LATENCY_BATCH_SIZE,
        "mean_ms": sum(ms) / len(ms), "min_ms": ms[0], "max_ms": ms[-1],
        "median_ms": ms[len(ms) // 2], "p50_ms": ms[len(ms) // 2],
        "p90_ms": ms[min(len(ms) - 1, int(0.90 * len(ms)))],
        "p95_ms": ms[min(len(ms) - 1, int(0.95 * len(ms)))],
        "p99_ms": ms[min(len(ms) - 1, int(0.99 * len(ms)))],
        "wall_clock_block_ms": wall_ms,
        "timer": "torch.cuda.Event(enable_timing=True) + torch.cuda.synchronize()",
        "wall_clock_cross_check_ms": sum(wall_ms) / len(wall_ms),
        "task_schedule": "iteration_index mod 4 (0=ISIC,1=BUSI,2=KVASIR,3=KUB)",
        "warmup_iterations": C.WARMUP_ITERATIONS,
    }


def time_throughput(fn):
    """FPS = processed synthetic samples / synchronized wall-clock seconds (batch 8)."""
    import torch
    for _ in range(C.WARMUP_ITERATIONS):
        fn(0)
    _sync()
    t0 = time.perf_counter()
    for _ in range(C.MEASUREMENT_BLOCKS * C.MEASURED_ITERATIONS_PER_BLOCK):
        fn(0)
    _sync()
    wall = time.perf_counter() - t0
    processed = C.MEASUREMENT_BLOCKS * C.MEASURED_ITERATIONS_PER_BLOCK * \
        C.SECONDARY_THROUGHPUT_BATCH_SIZE
    return {"batch_size": C.SECONDARY_THROUGHPUT_BATCH_SIZE, "processed_samples": processed,
            "timed_seconds": wall, "fps": processed / wall,
            "fps_definition": "processed_samples / synchronized_wall_seconds",
            "task_vector": C.BATCH8_TASK_VECTOR,
            "warmup_iterations": C.WARMUP_ITERATIONS}


def measure_memory(fn):
    """Frozen memory protocol; reset_peak_memory_stats immediately before the timed region."""
    import torch
    gc.collect()
    torch.cuda.empty_cache()
    base_alloc = torch.cuda.memory_allocated()
    base_res = torch.cuda.memory_reserved()
    torch.cuda.reset_peak_memory_stats()
    fn(0)
    _sync()
    return {"baseline_gpu_allocated_after_model_load": base_alloc,
            "baseline_gpu_reserved_after_model_load": base_res,
            "peak_gpu_allocated_during_inference": torch.cuda.max_memory_allocated(),
            "peak_gpu_reserved_during_inference": torch.cuda.max_memory_reserved(),
            "incremental_peak_allocated_over_loaded_baseline":
                torch.cuda.max_memory_allocated() - base_alloc,
            "reserved_memory_labeled_model_memory": False}


# --------------------------------------------------------------------------- #
# arm drivers
# --------------------------------------------------------------------------- #
def run_arm(arm_id: str, batch: int, mode: str, device: str = "cuda") -> dict:
    comps = C.ARMS[arm_id]["components"]
    models, meta = {}, {}
    for cid in comps:
        m, dev, info = load_component(cid, device)
        models[cid], meta[cid] = m, info
    device_str = str(device)

    # All large numeric tensors are PRECONSTRUCTED before the timed region.
    if batch == C.PRIMARY_LATENCY_BATCH_SIZE:
        per_task = {t: {cid: make_inputs(cid, batch, device_str, t) for cid in comps}
                    for t in C.TASK_ORDER}
    else:
        per_task = {None: {cid: make_inputs(cid, batch, device_str, 0) for cid in comps}}

    def step(key):
        bucket = per_task[key] if key in per_task else per_task[None]
        for cid in comps:
            call_component(models[cid], cid, bucket[cid])

    if mode == "identity":
        out = {"mode": "identity", "components": meta}
    elif mode == "latency":
        out = {"mode": "latency", "latency": time_latency(step)}
    elif mode == "throughput":
        out = {"mode": "throughput", "throughput": time_throughput(step)}
    elif mode == "memory":
        out = {"mode": "memory", "memory": measure_memory(step)}
    else:
        raise ValueError(mode)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=sorted(C.ARMS))
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--mode", required=True,
                    choices=["identity", "latency", "throughput", "memory"])
    a = ap.parse_args()

    if os.environ.get(GATE_ENV) != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    import torch
    if not torch.cuda.is_available():
        print(json.dumps({"arm": a.arm, "status": "INELIGIBLE_NO_CUDA"}))
        return 0

    result = {"arm": a.arm, "batch_size": a.batch, "revision": REVISION,
              "runtime_profile": "COMPONENT_SPECIFIC_CANONICAL_PRECISION_SEMANTICS",
              "batch1_label": C.BATCH1_LABEL, "batch8_label": C.BATCH8_LABEL,
              "canonical_numerical_reproduction": False,
              "timing_scope": C.TIMED_OPERATIONS.get(
                  a.arm, {}).get("scope", "MODEL_COMPUTE_PATH_RUNTIME"),
              "generator": C.GENERATOR_SEMANTICS,
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    result.update(run_arm(a.arm, a.batch, a.mode))
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
