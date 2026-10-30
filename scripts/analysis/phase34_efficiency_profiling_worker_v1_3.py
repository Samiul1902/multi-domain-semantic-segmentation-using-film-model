#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 executable profiling worker (repository-root-bound + untimed smoke mode).

Classification: PRE_MEASUREMENT_WORKER_IMPORT_AND_UNTIMED_SMOKE_EXECUTION_AMENDMENT__WORKER
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

SUPERSEDES the v1.2 worker for future execution (v1.2 preserved byte-for-byte). Retains every
accepted v1.2 semantic: constructors, strict checkpoint loading, parameter verification,
synthetic input contracts, task schedules, precision contexts, timed-operation scope, CUDA-event
timing, throughput, memory profiling, controlled-path semantics, process isolation and the
PHASE34_EXECUTE gate. Adds ONLY:
  (a) deterministic FILE-RELATIVE repository-root import binding (cwd independent), and
  (b) an explicit untimed `smoke` mode (UNTIMED_INTERFACE_AND_IDENTITY_VALIDATION).

!! ZERO-EXECUTION GUARD !!  main() requires PHASE34_EXECUTE=1. Importing this module constructs
no model, deserializes no checkpoint, runs no forward and touches no CUDA.

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

# --------------------------------------------------------------------------- #
# (a) repository-root import binding - resolved from THIS FILE, never from cwd
# --------------------------------------------------------------------------- #
REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

import phase34_v1_2_common as C  # noqa: E402  (frozen v1.2 semantics, unchanged)

ROOT = REPO_ROOT
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"
GATE_ENV = "PHASE34_EXECUTE"

# (b) frozen smoke task identity - NO scientific weighting interpretation
SMOKE_TASK_ID = 0
SMOKE_DOMAIN = "ISIC"
SMOKE_MODES = ("smoke", "identity", "latency", "throughput", "memory")
SMOKE_COMPONENT_ORDER = ["G", "R_psi", "B_phi", "S_omega"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# canonical model construction (identical to v1.2)
# --------------------------------------------------------------------------- #
def _build_G(device):
    import json as _json

    import torch
    from src.models.film import GlobalMedFiLM
    spec = C.COMPONENTS["G"]
    cfg = _json.loads((ROOT / spec["config_file"]).read_text(encoding="utf-8"))["model"]
    return GlobalMedFiLM(
        task_count=cfg["task_count"], in_channels=cfg["in_channels"],
        out_channels=cfg["out_channels"], channels=tuple(cfg["channels"]),
        task_embedding_dim=cfg["task_embedding_dim"],
        film_hidden_dim=cfg["film_hidden_dim"]), torch.device(device)


def _build_R_psi(device):
    import torch
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    return BARRRegionalRefinerV1(), torch.device(device)


def _build_B_phi(device):
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
# canonical execution contexts (identical to v1.2)
# --------------------------------------------------------------------------- #
def forward_G(model, images, task_ids):
    """eval + float32 + autocast(fp16) + torch.no_grad()  (NOT torch.inference_mode())."""
    import torch
    with torch.no_grad():
        with torch.amp.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
            logits = model(images, task_ids)
    return torch.sigmoid(logits.float())


def forward_R_psi(model, x):
    import torch
    with torch.inference_mode():
        out = model(x)
    return torch.sigmoid(out.float())


def forward_B_phi(model, feats, task_ids):
    import torch
    with torch.inference_mode():
        return model(feats, task_ids)


def forward_S_omega(model, x):
    import torch
    with torch.inference_mode():
        return model(x)


FORWARDS = {"G": forward_G, "R_psi": forward_R_psi, "B_phi": forward_B_phi,
            "S_omega": forward_S_omega}


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


def call_component(model, cid, args):
    return FORWARDS[cid](model, *args)


# --------------------------------------------------------------------------- #
# smoke validation (UNTIMED)
# --------------------------------------------------------------------------- #
def validate_output(cid: str, out) -> dict:
    import torch
    if not isinstance(out, torch.Tensor):
        raise RuntimeError(f"SMOKE: {cid} output is not a torch.Tensor ({type(out)})")
    finite = bool(torch.isfinite(out).all().item())
    if not finite:
        raise RuntimeError(f"SMOKE: {cid} output contains non-finite values")
    if out.shape[0] != 1:
        raise RuntimeError(f"SMOKE: {cid} output batch dim != 1 ({tuple(out.shape)})")
    return {"output_shape": list(out.shape), "output_dtype": str(out.dtype),
            "finite": finite}


def smoke_component(cid: str, device: str = "cuda") -> dict:
    """Untimed interface + identity validation for ONE component. Exactly ONE forward."""
    import torch
    model, dev, info = load_component(cid, device)
    args = make_inputs(cid, C.PRIMARY_LATENCY_BATCH_SIZE, str(dev), SMOKE_TASK_ID)
    with torch.no_grad():
        out = call_component(model, cid, args)
    return {"component": cid, "constructed": True, "eval": True,
            "strict_load": {"missing_keys": info["strict_load_missing_keys"],
                            "unexpected_keys": info["strict_load_unexpected_keys"]},
            "parameter_count": info["parameter_count"],
            "parameter_dtypes": info["parameter_dtypes"],
            "checkpoint_sha256": info["checkpoint_sha256"],
            "smoke_task_id": SMOKE_TASK_ID, "smoke_domain": SMOKE_DOMAIN,
            "forward_calls": 1, "timed": False, **validate_output(cid, out)}


def smoke_path(arm_id: str, device: str = "cuda") -> dict:
    """Untimed controlled-path smoke using independently preconstructed synthetic inputs."""
    import torch
    comps = C.ARMS[arm_id]["components"]
    models, per = {}, {}
    for cid in comps:
        m, dev, _ = load_component(cid, device)
        models[cid] = m
        per[cid] = make_inputs(cid, C.PRIMARY_LATENCY_BATCH_SIZE, str(dev), SMOKE_TASK_ID)
    calls = 0
    outs = {}
    with torch.no_grad():
        for cid in comps:
            outs[cid] = call_component(models[cid], cid, per[cid])
            calls += 1
    return {"arm": arm_id, "components": comps, "forward_calls": calls, "timed": False,
            "route_forced": True, "natural_route_replay": False,
            "b_phi_output_used_to_choose_route": False,
            "outputs": {k: validate_output(k, v) for k, v in outs.items()}}


def run_smoke(arm_id: str, device: str = "cuda") -> dict:
    if arm_id in C.ARMS and C.ARMS[arm_id]["kind"] == "component":
        cid = C.ARMS[arm_id]["components"][0]
        r = smoke_component(cid, device)
        return {"mode": "smoke", "scope": "COMPONENT", "component": r,
                "individual_component_smoke_model_forward_calls": 1,
                "controlled_path_smoke_model_forward_calls": 0,
                "total_smoke_model_forward_calls": 1}
    if arm_id in ("SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"):
        r = smoke_path(arm_id, device)
        return {"mode": "smoke", "scope": "CONTROLLED_PATH", "path": r,
                "individual_component_smoke_model_forward_calls": 0,
                "controlled_path_smoke_model_forward_calls": r["forward_calls"],
                "total_smoke_model_forward_calls": r["forward_calls"]}
    raise ValueError(f"arm {arm_id} is not smoke-eligible")


# --------------------------------------------------------------------------- #
# measurement primitives (identical to v1.2)
# --------------------------------------------------------------------------- #
def _sync():
    import torch
    torch.cuda.synchronize()


def time_latency(fn):
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
    return {"n_observations": C.TOTAL_MEASURED_ITERATIONS,
            "blocks": C.MEASUREMENT_BLOCKS,
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
            "warmup_iterations": C.WARMUP_ITERATIONS}


def time_throughput(fn):
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
            "task_vector": C.BATCH8_TASK_VECTOR, "warmup_iterations": C.WARMUP_ITERATIONS}


def measure_memory(fn):
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


def run_arm(arm_id: str, batch: int, mode: str, device: str = "cuda") -> dict:
    if mode == "smoke":
        return run_smoke(arm_id, device)
    comps = C.ARMS[arm_id]["components"]
    models, meta = {}, {}
    for cid in comps:
        m, dev, info = load_component(cid, device)
        models[cid], meta[cid] = m, info
    device_str = str(device)
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
        return {"mode": "identity", "components": meta}
    if mode == "latency":
        return {"mode": "latency", "latency": time_latency(step)}
    if mode == "throughput":
        return {"mode": "throughput", "throughput": time_throughput(step)}
    if mode == "memory":
        return {"mode": "memory", "memory": measure_memory(step)}
    raise ValueError(mode)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True, choices=sorted(C.ARMS))
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--mode", required=True, choices=list(SMOKE_MODES))
    a = ap.parse_args()

    if os.environ.get(GATE_ENV) != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    import torch
    if not torch.cuda.is_available():
        print(json.dumps({"arm": a.arm, "status": "INELIGIBLE_NO_CUDA"}))
        return 0

    result = {"arm": a.arm, "batch_size": a.batch, "revision": REVISION,
              "repo_root": str(REPO_ROOT), "repo_root_resolution": "FILE_RELATIVE",
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
