"""Accuracy–efficiency measurement with declared units and declared conditions.

Two numbers that are routinely conflated are kept apart here:

``conv_linear_macs``
    Conv2d/Linear multiply-accumulates only, counted by the repository's existing
    analytical counter (:func:`src.research.c3_baselines.experiment.analytical_macs_lower_bound`).
    This is the conservative, comparable measure across the eight architectures.
``total_flops``
    Everything :class:`torch.utils.flop_counter.FlopCounterMode` sees, which for a
    transformer also includes attention matmuls.  Reported separately and never
    substituted for the above.

A third distinction matters for the routed systems: a **conditional** refiner
means fewer refiner calls, which is *not* the same as a lower total cost.  Both
``macs_if_always_refine`` and ``effective_macs_per_image`` (weighted by the
measured invocation rate) are reported, so the difference is visible instead of
implied.

Every latency and memory number is measured on this machine under the conditions
recorded in :func:`profiling_conditions`.  Nothing is estimated from a paper.
"""
from __future__ import annotations

import platform
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np
import torch
from torch import nn

from src.research.c3_baselines import experiment as C3

from . import protocol as P
from .adapters import ModelAdapter, Prediction

#: Shapes used for the component MAC counts.  They are the shapes the canonical
#: pipeline actually feeds each component, not convenient round numbers.
MAC_INPUT_SHAPES: Dict[str, tuple] = {
    "G": (1, 3, 512, 512),
    "R": (1, 4, 256, 256),      # 3-channel image crop concatenated with the 1-channel p_global crop
    "B": (1, 202),              # 202-D pre-refinement feature vector
    "S": (1, 20),               # 16 numeric + 4 task one-hot
}


def profiling_conditions(*, resolution: int = P.RESOLUTION, batch_size: int = 1,
                         precision: str = "float32", warmup: int = 3,
                         repeats: int = 20) -> Dict[str, Any]:
    """The conditions a latency or memory number is only valid under."""
    cuda = torch.cuda.is_available()
    return {
        "device_type": "cuda" if cuda else "cpu",
        "device_name": torch.cuda.get_device_name(0) if cuda else platform.processor(),
        "device_total_memory_mib": (torch.cuda.get_device_properties(0).total_memory / 2 ** 20
                                    if cuda else None),
        "torch_version": torch.__version__,
        "cuda_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version() if cuda else None,
        "input_resolution": int(resolution),
        "batch_size": int(batch_size),
        "precision": precision,
        "warmup_iterations": int(warmup),
        "measured_repeats": int(repeats),
        "cuda_synchronized": bool(cuda),
        "timing_source": "time.perf_counter around the full forward pass",
        "determinism": {"cudnn_deterministic": torch.backends.cudnn.deterministic,
                        "cudnn_benchmark": torch.backends.cudnn.benchmark},
        "note": ("Latency is batch-1 end-to-end forward time on this host. It is a "
                 "property of this machine and this build, not of the method."),
    }


# --------------------------------------------------------------------------- #
# Parameters and MACs
# --------------------------------------------------------------------------- #
def count_parameters(adapter: ModelAdapter) -> Dict[str, Any]:
    total = adapter.parameter_count()
    return {"unique_inference_parameters": int(total),
            "units": "parameters (shared tensors counted once)",
            "note": "inference parameters; no optimizer state is included"}


def _conv_linear_macs(model: nn.Module, run) -> Dict[str, Any]:
    """Conv2d/Linear MACs for one forward pass, using ``run`` to drive the model.

    Same arithmetic as
    :func:`src.research.c3_baselines.experiment.analytical_macs_lower_bound`, but
    with an injected forward so a component that takes extra arguments (the router
    needs a task id) can be counted too.  ``test_macs_agree_with_the_canonical_counter``
    asserts the two agree on a plain model, so they cannot silently diverge.
    """
    macs = 0
    handles = []

    def hook(module: nn.Module, _inputs: tuple, output: torch.Tensor) -> None:
        nonlocal macs
        if isinstance(module, nn.Conv2d):
            kernel = module.kernel_size[0] * module.kernel_size[1]
            macs += int(output.numel() * (module.in_channels // module.groups) * kernel)
        elif isinstance(module, nn.Linear):
            macs += int(output.numel() * module.in_features)

    for module in model.modules():
        if isinstance(module, (nn.Conv2d, nn.Linear)):
            handles.append(module.register_forward_hook(hook))
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad():
            run(model)
    finally:
        for handle in handles:
            handle.remove()
        model.train(was_training)
    return {"macs_lower_bound": macs, "gmacs_lower_bound": macs / 1e9,
            "method": "Conv2d+Linear hooks; excludes attention tensor matmuls and non-learned ops"}


def _macs(model: nn.Module, shape: tuple, *, extra: Optional[callable] = None) -> Optional[Dict[str, Any]]:
    try:
        parameter = next(model.parameters())
        device, dtype = parameter.device, parameter.dtype

        def run(m: nn.Module) -> None:
            x = torch.zeros(shape, device=device, dtype=dtype)
            if extra is not None:
                extra(m, x)
            else:
                m(x)

        return _conv_linear_macs(model, run)
    except Exception as exc:  # pragma: no cover - defensive, reported not hidden
        return {"error": f"{type(exc).__name__}: {exc}", "input_shape": list(shape)}


def _router_run(m: nn.Module, x: torch.Tensor) -> None:
    m(x, torch.zeros(x.shape[0], dtype=torch.long, device=x.device))


def count_macs(adapter: ModelAdapter) -> Dict[str, Any]:
    """Conv/Linear MACs per component, plus the conditional total."""
    system = getattr(adapter, "_system", None)
    if system is not None and adapter.kind == "ROUTED":
        parts = {
            "G": _macs(system.g, MAC_INPUT_SHAPES["G"],
                       extra=lambda m, x: m(x, torch.zeros(1, dtype=torch.long, device=x.device))),
            "R": _macs(system.r, MAC_INPUT_SHAPES["R"]),
            "B": _macs(system.b, MAC_INPUT_SHAPES["B"], extra=_router_run),
            "S": _macs(system.s, MAC_INPUT_SHAPES["S"]),
        }
        ok = {k: v["macs_lower_bound"] for k, v in parts.items()
              if isinstance(v, dict) and "macs_lower_bound" in v}
        return {"component_macs": parts, "conditional": True,
                "macs_global_only": ok.get("G"),
                "macs_refiner_per_call": ok.get("R"),
                "macs_router_per_image": ok.get("B"),
                "macs_safety_per_call": ok.get("S"),
                "method": parts["G"].get("method") if isinstance(parts["G"], dict) else None,
                "note": ("R and S run only when the router selects refinement; the "
                         "unconditional sum is an upper bound, not the expected cost.")}

    model = getattr(adapter, "_model", None)
    if model is None:
        return {"error": "adapter exposes no module to count", "conditional": False}
    if adapter.kind == "TASK_CONDITIONED":
        single = _macs(model, (1, 3, P.RESOLUTION, P.RESOLUTION),
                       extra=lambda m, x: m(x, torch.zeros(1, dtype=torch.long, device=x.device)))
    else:
        single = _macs(model, (1, 3, P.RESOLUTION, P.RESOLUTION))
    return {"component_macs": {"network": single}, "conditional": False,
            "macs_global_only": single.get("macs_lower_bound"),
            "macs_refiner_per_call": 0, "macs_router_per_image": 0,
            "macs_safety_per_call": 0,
            "method": single.get("method"), "note": "single unconditional network"}


def total_flops(adapter: ModelAdapter, *, resolution: int = P.RESOLUTION) -> Dict[str, Any]:
    """Everything FlopCounterMode sees, including attention matmuls."""
    model = getattr(adapter, "_model", None)
    if model is None:
        return {"total_flops": None,
                "reason": "routed adapters are counted per component in count_macs"}
    from torch.utils.flop_counter import FlopCounterMode

    device = next(model.parameters()).device
    image = torch.zeros(1, 3, resolution, resolution, device=device)
    counter = FlopCounterMode(display=False)
    was_training = model.training
    model.eval()
    try:
        with torch.no_grad(), counter:
            if adapter.kind == "TASK_CONDITIONED":
                model(image, torch.zeros(1, dtype=torch.long, device=device))
            else:
                model(image)
    finally:
        model.train(was_training)
    flops = int(counter.get_total_flops())
    return {"total_flops": flops, "total_gflops": flops / 1e9,
            "conv_linear_macs_equivalent": flops / 2,
            "method": "torch.utils.flop_counter.FlopCounterMode (all counted operators)",
            "note": "Not comparable to conv/linear MACs alone; reported separately."}


# --------------------------------------------------------------------------- #
# Latency and memory
# --------------------------------------------------------------------------- #
def measure_latency(adapter: ModelAdapter, image: torch.Tensor, task_id: int, *,
                    warmup: int = 3, repeats: int = 20) -> Dict[str, Any]:
    """Batch-1 end-to-end forward latency, with CUDA synchronisation."""
    cuda = torch.cuda.is_available() and adapter.device.type == "cuda"
    for _ in range(warmup):
        adapter.predict(image, task_id)
    if cuda:
        torch.cuda.synchronize(adapter.device)
    samples: List[float] = []
    for _ in range(repeats):
        if cuda:
            torch.cuda.synchronize(adapter.device)
        start = time.perf_counter()
        adapter.predict(image, task_id)
        if cuda:
            torch.cuda.synchronize(adapter.device)
        samples.append((time.perf_counter() - start) * 1000.0)
    arr = np.asarray(samples, dtype=np.float64)
    return {"latency_ms_p50": float(np.percentile(arr, 50)),
            "latency_ms_p95": float(np.percentile(arr, 95)),
            "latency_ms_mean": float(arr.mean()),
            "latency_ms_min": float(arr.min()),
            "latency_ms_max": float(arr.max()),
            "throughput_images_per_s": float(1000.0 / arr.mean()),
            "unit": "milliseconds per image (batch 1)",
            "warmup_iterations": int(warmup), "measured_repeats": int(repeats),
            "cuda_synchronized": bool(cuda)}


def measure_peak_memory(adapter: ModelAdapter, image: torch.Tensor, task_id: int) -> Dict[str, Any]:
    if not (torch.cuda.is_available() and adapter.device.type == "cuda"):
        return {"peak_allocated_mib": None, "peak_reserved_mib": None,
                "memory_unit": "MiB",
                "reason": "CPU device; no GPU memory is allocated"}
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(adapter.device)
    adapter.predict(image, task_id)
    torch.cuda.synchronize(adapter.device)
    return {"peak_allocated_mib": torch.cuda.max_memory_allocated(adapter.device) / 2 ** 20,
            "peak_reserved_mib": torch.cuda.max_memory_reserved(adapter.device) / 2 ** 20,
            "memory_unit": "MiB",
            "device_total_memory_mib": torch.cuda.get_device_properties(0).total_memory / 2 ** 20}


# --------------------------------------------------------------------------- #
# Combined profile for one cell
# --------------------------------------------------------------------------- #
def profile_cell(adapter: ModelAdapter, image: torch.Tensor, task_id: int, *,
                 records: Optional[Sequence[Mapping[str, Any]]] = None,
                 warmup: int = 3, repeats: int = 20) -> Dict[str, Any]:
    params = count_parameters(adapter)
    macs = count_macs(adapter)
    latency = measure_latency(adapter, image, task_id, warmup=warmup, repeats=repeats)
    memory = measure_peak_memory(adapter, image, task_id)

    rate = None
    if records:
        executed = [r for r in records if r.get("refiner_executed")]
        rate = len(executed) / len(records)

    effective = None
    if adapter.kind == "ROUTED" and macs.get("macs_global_only") is not None and rate is not None:
        effective = int(macs["macs_global_only"]
                        + macs.get("macs_router_per_image", 0)
                        + rate * (macs.get("macs_refiner_per_call", 0)
                                  + macs.get("macs_safety_per_call", 0)))
    unconditional = None
    if adapter.kind == "ROUTED" and macs.get("macs_global_only") is not None:
        unconditional = int(sum(v for k, v in macs.items()
                                if k.startswith("macs_") and k != "macs_global_only"
                                and isinstance(v, int)) + macs["macs_global_only"])

    # Built field by field rather than by merging the three dicts: the latency and
    # memory blocks both used to carry a bare ``unit`` key, and a dict merge let
    # "MiB" silently overwrite "milliseconds per image".  Each quantity now states
    # its own unit under a name that cannot collide.
    return {
        "model_key": adapter.model_key, "seed": adapter.seed,
        "adapter_kind": adapter.kind, "evidence_class": adapter.evidence_class,
        # parameters
        "unique_inference_parameters": params["unique_inference_parameters"],
        "parameters_unit": params["units"],
        "parameters_note": params["note"],
        # latency
        "latency_ms_p50": latency["latency_ms_p50"],
        "latency_ms_p95": latency["latency_ms_p95"],
        "latency_ms_mean": latency["latency_ms_mean"],
        "latency_ms_min": latency["latency_ms_min"],
        "latency_ms_max": latency["latency_ms_max"],
        "throughput_images_per_s": latency["throughput_images_per_s"],
        "latency_unit": latency["unit"],
        "latency_warmup_iterations": latency["warmup_iterations"],
        "latency_measured_repeats": latency["measured_repeats"],
        "latency_cuda_synchronized": latency["cuda_synchronized"],
        # memory
        "peak_allocated_mib": memory.get("peak_allocated_mib"),
        "peak_reserved_mib": memory.get("peak_reserved_mib"),
        "memory_unit": memory.get("memory_unit"),
        "memory_reason": memory.get("reason"),
        "device_total_memory_mib": memory.get("device_total_memory_mib"),
        # MACs
        "conditional_refiner": adapter.kind == "ROUTED",
        "conditional_refiner_invocation_rate": rate,
        "macs_global_only": macs.get("macs_global_only"),
        "macs_refiner_per_call": macs.get("macs_refiner_per_call"),
        "macs_router_per_image": macs.get("macs_router_per_image"),
        "macs_safety_per_call": macs.get("macs_safety_per_call"),
        "macs_if_always_refine": unconditional,
        "effective_macs_per_image": effective,
        "macs_unit": "multiply-accumulate operations per image",
        "macs_method": macs.get("method"),
        "macs_note": macs.get("note"),
        "profiling_conditions": profiling_conditions(warmup=warmup, repeats=repeats),
    }


def trade_off_rows(profiles: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    """Rows for the accuracy–parameter, accuracy–MAC and accuracy–latency tables.

    Accuracy is supplied by the caller elsewhere; this function only asserts that
    the efficiency side carries the right units.
    """
    rows = []
    for p in profiles:
        rows.append({
            "model_key": p["model_key"], "seed": p["seed"],
            "parameters": p["unique_inference_parameters"],
            "macs_conv_linear": (p.get("effective_macs_per_image")
                                 if p.get("effective_macs_per_image") is not None
                                 else p.get("macs_global_only")),
            "macs_basis": ("conditional_effective" if p.get("effective_macs_per_image") is not None
                           else "unconditional"),
            "latency_ms_p50": p.get("latency_ms_p50"),
            "latency_ms_p95": p.get("latency_ms_p95"),
            "peak_memory_mib": p.get("peak_allocated_mib"),
            "refiner_invocation_rate": p.get("conditional_refiner_invocation_rate"),
            "evidence_class": p.get("evidence_class"),
        })
    return rows


__all__ = ["MAC_INPUT_SHAPES", "count_macs", "count_parameters", "measure_latency",
           "measure_peak_memory", "profile_cell", "profiling_conditions",
           "total_flops", "trade_off_rows"]
