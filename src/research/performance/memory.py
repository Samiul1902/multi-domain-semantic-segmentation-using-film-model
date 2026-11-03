"""GPU and CPU memory characterisation for each training stage and inference path.

Measured, not estimated.  Every figure comes from
``torch.cuda.max_memory_allocated`` / ``max_memory_reserved`` around a real
forward/backward, with ``empty_cache`` and a peak-stat reset before each
measurement so one stage cannot inflate the next.

Two numbers, two meanings
-------------------------
``peak_allocated_mib``
    Live tensors at the peak — parameters, activations, gradients, optimizer
    state.  This is the figure that says whether a stage fits.
``peak_reserved_mib``
    What the caching allocator is holding.  It stays high after a stage by
    design; treating it as a leak is the classic misreading, and
    :mod:`src.research.performance.stability` distinguishes the two explicitly.

Contract shapes
---------------
The global stage is measured at the frozen 512x512 canvas; the regional refiner
at the frozen 256x256 ROI contract with 4 input channels (3-channel image crop
concatenated with the 1-channel global-probability crop).  The router takes the
202-D pre-refinement feature vector, the safety module the 20-D vector
(16 numeric + 4 task one-hot).  These are the shapes the pipeline actually feeds,
not convenient round numbers.
"""
from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import torch
from torch import nn

from src.models.barr.phase25_models import BARRBenefitRouterV1, BARRPostSafetyV1
from src.models.barr.regional_refiner import BARRRegionalRefinerV1
from src.models.film.global_medfilm import GlobalMedFiLM
from src.research.evaluation import adapters as A
from src.research.evaluation import protocol as P
from src.research.evaluation import registry as REG
from src.research.full_pipeline import recipe as R

from . import bench as B

EVIDENCE_CLASS = B.EVIDENCE_CLASS
GPU_TOTAL_MIB_HINT = 8192.0     # RTX 3060 Ti, approximately 8 GB
SAFETY_NUMERIC_WIDTH = 16
SAFETY_ONE_HOT_WIDTH = 4
#: The safety module consumes 16 numeric features concatenated with a 4-wide task
#: one-hot, i.e. 20 inputs — the same width the Phase C MAC counter uses.
SAFETY_INPUT_WIDTH = SAFETY_NUMERIC_WIDTH + SAFETY_ONE_HOT_WIDTH
ROUTER_FEATURE_WIDTH = 202
ROI_SIDE = 256
GLOBAL_SIDE = P.RESOLUTION


# --------------------------------------------------------------------------- #
# CPU memory
# --------------------------------------------------------------------------- #
def cpu_rss_mib() -> Optional[float]:
    """Process resident set size, or ``None`` when psutil is unavailable."""
    try:
        import psutil
    except ImportError:  # pragma: no cover - psutil is present on this host
        return None
    return float(psutil.Process(os.getpid()).memory_info().rss) / 2 ** 20


def cuda_available(device: str) -> bool:
    return torch.cuda.is_available() and torch.device(device).type == "cuda"


# --------------------------------------------------------------------------- #
# Stage specifications
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class StageSpec:
    """One measurable training or inference stage."""

    name: str
    build: Callable[[str], nn.Module]
    inputs: Callable[[int, str], Tuple[Any, torch.Tensor]]
    loss: str                     # "bce" | "huber"
    description: str


def _g_inputs(batch: int, device: str):
    images = B.synthetic_image(batch, resolution=GLOBAL_SIDE, device=device)
    task = torch.full((batch,), 3, dtype=torch.long, device=device)
    target = (torch.rand((batch, 1, GLOBAL_SIDE, GLOBAL_SIDE), device=device) > 0.7).float()
    return (images, task), target


def _r_inputs(batch: int, device: str):
    roi = torch.rand((batch, 4, ROI_SIDE, ROI_SIDE), device=device)
    target = (torch.rand((batch, 1, ROI_SIDE, ROI_SIDE), device=device) > 0.7).float()
    return (roi,), target


def _b_inputs(batch: int, device: str):
    features = torch.rand((batch, ROUTER_FEATURE_WIDTH), device=device)
    task = torch.full((batch,), 2, dtype=torch.long, device=device)
    target = torch.rand((batch,), device=device)
    return (features, task), target


def _s_inputs(batch: int, device: str):
    numeric = torch.rand((batch, SAFETY_NUMERIC_WIDTH), device=device)
    one_hot = torch.zeros((batch, SAFETY_ONE_HOT_WIDTH), device=device)
    one_hot[:, 3] = 1.0                       # task id 3, as a one-hot
    features = torch.cat([numeric, one_hot], dim=1)
    target = (torch.rand((batch,), device=device) > 0.5).float()
    return (features,), target


STAGE_SPECS: Dict[str, StageSpec] = {
    "G_train": StageSpec("G_train", lambda d: GlobalMedFiLM(task_count=4, in_channels=3,
                                                            out_channels=1),
                         _g_inputs, "bce",
                         "GlobalMedFiLM forward/backward at 512x512"),
    "R_train": StageSpec("R_train", lambda d: BARRRegionalRefinerV1(), _r_inputs, "bce",
                         "regional refiner forward/backward at the 256x256 ROI contract"),
    "B_train": StageSpec("B_train", lambda d: BARRBenefitRouterV1(), _b_inputs, "huber",
                         "benefit router forward/backward on the 202-D feature vector"),
    "S_train": StageSpec("S_train", lambda d: BARRPostSafetyV1(), _s_inputs, "bce",
                         "safety module forward/backward on the 20-D vector"),
}


def _criterion(kind: str) -> Callable[[torch.Tensor, torch.Tensor], torch.Tensor]:
    if kind == "bce":
        return nn.BCEWithLogitsLoss()
    if kind == "huber":
        return nn.HuberLoss(delta=R.B_LOSS["delta"], reduction="mean")
    raise ValueError(f"unknown loss {kind!r}")


# --------------------------------------------------------------------------- #
# One training stage
# --------------------------------------------------------------------------- #
def measure_training_stage(stage: str, *, device: str = "cuda", batch: int = 2,
                           steps: int = 3, autocast: bool = False,
                           accumulation: int = 1,
                           optimizer: str = "adamw") -> Dict[str, Any]:
    """Peak memory for one training stage, measured over ``steps`` real updates.

    ``accumulation`` splits each step into that many micro-batches, so the peak
    should stay near the micro-batch size while the effective batch grows — that
    is the property gradient accumulation is supposed to have, and it is measured
    rather than assumed.
    """
    if stage not in STAGE_SPECS:
        raise ValueError(f"unknown stage {stage!r}; known: {sorted(STAGE_SPECS)}")
    spec = STAGE_SPECS[stage]
    if accumulation < 1:
        raise ValueError("accumulation must be >= 1")

    B.reset_memory(device)
    rss_before = cpu_rss_mib()
    torch.manual_seed(20261103)

    model = spec.build(device).to(device)
    criterion = _criterion(spec.loss)
    parameters = [p for p in model.parameters() if p.requires_grad]
    if optimizer == "adamw":
        opt = torch.optim.AdamW(parameters, lr=1e-4, weight_decay=1e-4)
    else:
        opt = torch.optim.SGD(parameters, lr=1e-3)

    micro = max(1, batch // accumulation)
    peak_alloc = 0.0
    peak_reserved = 0.0
    step_losses: List[float] = []
    started = time.perf_counter()
    try:
        for _ in range(int(steps)):
            opt.zero_grad(set_to_none=True)
            for _micro in range(accumulation):
                inputs, target = spec.inputs(micro, device)
                with torch.autocast(device_type=torch.device(device).type,
                                    enabled=bool(autocast) and cuda_available(device)):
                    output = model(*inputs)
                    loss = criterion(output.float(), target.float()) / accumulation
                loss.backward()
                step_losses.append(float(loss.detach()))
            opt.step()
        B.synchronize(device)
        if cuda_available(device):
            peak_alloc = torch.cuda.max_memory_allocated(device) / 2 ** 20
            peak_reserved = torch.cuda.max_memory_reserved(device) / 2 ** 20
        elapsed = time.perf_counter() - started
        rss_after = cpu_rss_mib()
        return {
            "stage": stage, "description": spec.description,
            "batch": int(batch), "micro_batch": int(micro),
            "accumulation": int(accumulation), "steps": int(steps),
            "optimizer": optimizer, "autocast": bool(autocast),
            "peak_allocated_mib": peak_alloc if cuda_available(device) else None,
            "peak_reserved_mib": peak_reserved if cuda_available(device) else None,
            "memory_unit": "MiB",
            "cpu_rss_before_mib": rss_before, "cpu_rss_after_mib": rss_after,
            "cpu_rss_delta_mib": (None if (rss_before is None or rss_after is None)
                                  else rss_after - rss_before),
            "parameters": sum(p.numel() for p in model.parameters()),
            "final_loss": step_losses[-1] if step_losses else None,
            "elapsed_seconds": elapsed,
            "device": device, "evidence_class": EVIDENCE_CLASS,
            "note": ("Synthetic tensors and synthetic targets. This characterises memory, "
                     "not convergence."),
        }
    finally:
        del model, opt
        B.reset_memory(device)


# --------------------------------------------------------------------------- #
# Inference paths
# --------------------------------------------------------------------------- #
def measure_inference_path(model_key: str, *, device: str = "cuda", seed: int = 42,
                           batch: int = 1) -> Dict[str, Any]:
    """Peak memory for one model's inference, at its supported batch size."""
    if REG.ADAPTER_KINDS[model_key] == "ROUTED" and batch != 1:
        raise ValueError(f"{model_key} is a routed pipeline and is batch-1 by contract")
    B.reset_memory(device)
    rss_before = cpu_rss_mib()
    adapter = A.build_synthetic(model_key, seed, device=device)
    adapter.load()
    try:
        image = B.synthetic_image(batch, resolution=GLOBAL_SIDE, device=device)
        memory = B.measure_peak_memory(lambda: adapter.predict(image[:1], 3), device=device)
        rss_after = cpu_rss_mib()
        return {"model_key": model_key, "seed": int(seed), "adapter_kind": adapter.kind,
                "batch": int(batch), **memory,
                "cpu_rss_before_mib": rss_before, "cpu_rss_after_mib": rss_after,
                "parameters": adapter.parameter_count(),
                "device": device, "evidence_class": EVIDENCE_CLASS,
                "note": "Synthetic weights and a synthetic image."}
    finally:
        adapter.close()
        B.reset_memory(device)


# --------------------------------------------------------------------------- #
# Capacity search
# --------------------------------------------------------------------------- #
def max_batch_that_fits(stage: str, *, device: str = "cuda",
                        candidates: Sequence[int] = (1, 2, 4, 8, 16, 32),
                        autocast: bool = False) -> Dict[str, Any]:
    """Largest batch that completes one training step without an OOM."""
    if not cuda_available(device):
        return {"stage": stage, "device": device, "max_batch": None,
                "reason": "no CUDA device"}
    spec = STAGE_SPECS[stage]
    best: Optional[int] = None
    failures: List[Dict[str, Any]] = []
    for batch in candidates:
        B.reset_memory(device)
        model = spec.build(device).to(device)
        criterion = _criterion(spec.loss)
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
        try:
            inputs, target = spec.inputs(int(batch), device)
            opt.zero_grad(set_to_none=True)
            with torch.autocast(device_type=torch.device(device).type,
                                enabled=bool(autocast) and cuda_available(device)):
                output = model(*inputs)
                loss = criterion(output.float(), target.float())
            loss.backward()
            opt.step()
            B.synchronize(device)
            best = int(batch)
        except (torch.cuda.OutOfMemoryError, RuntimeError) as exc:
            failures.append({"batch": int(batch), "reason": f"{type(exc).__name__}"})
            break
        finally:
            del model, opt
            B.reset_memory(device)
    return {"stage": stage, "device": device, "max_batch": best,
            "autocast": bool(autocast), "attempted": list(candidates),
            "failures": failures,
            "gpu_total_mib": (torch.cuda.get_device_properties(0).total_memory / 2 ** 20
                              if cuda_available(device) else None)}


# --------------------------------------------------------------------------- #
# DataLoader and transfer behaviour
# --------------------------------------------------------------------------- #
def dataloader_overhead(*, workers: int = 0, pin_memory: bool = False,
                        batch: int = 4, batches: int = 6, warmup_batches: int = 1,
                        device: str = "cuda") -> Dict[str, Any]:
    """Iteration cost of a loader feeding the 512 contract.

    Worker startup is separated from steady state on purpose.  On Windows each
    worker process re-imports torch, which costs seconds; measuring a short run
    end-to-end therefore reports the *spawn* cost as if it were throughput
    (measured here: 9.1 img/s with 2 workers against 1182 with none, at six
    batches).  The first ``warmup_batches`` iterations are excluded from the
    measured window and reported separately as ``startup_seconds``, so neither
    number can be mistaken for the other.

    ``workers > 0`` uses multiprocessing; call it from the CLI entry point (which
    has a ``__main__`` guard), not from a test module, because Windows spawn
    re-imports the module.
    """
    from torch.utils.data import DataLoader, TensorDataset

    images = torch.rand((batch * batches, 3, GLOBAL_SIDE, GLOBAL_SIDE))
    targets = torch.rand((batch * batches, 1, GLOBAL_SIDE, GLOBAL_SIDE))
    dataset = TensorDataset(images, targets)
    loader = DataLoader(dataset, batch_size=batch, shuffle=False,
                        num_workers=int(workers), pin_memory=bool(pin_memory))

    def transfer(xb: torch.Tensor) -> torch.Tensor:
        if cuda_available(device):
            return xb.to(device, non_blocking=bool(pin_memory))
        return xb

    B.synchronize(device)
    startup_started = time.perf_counter()
    iterator = iter(loader)
    warm = 0
    for _ in range(max(0, int(warmup_batches))):
        try:
            xb, _yb = next(iterator)
        except StopIteration:                                # pragma: no cover
            break
        transfer(xb)
        warm += 1
    B.synchronize(device)
    startup = time.perf_counter() - startup_started

    started = time.perf_counter()
    transferred = 0
    for xb, _yb in iterator:
        transfer(xb)
        transferred += int(xb.shape[0])
    B.synchronize(device)
    elapsed = time.perf_counter() - started
    return {"workers": int(workers), "pin_memory": bool(pin_memory),
            "batch": int(batch), "batches": int(batches),
            "warmup_batches_excluded": warm,
            "images_measured": transferred,
            "elapsed_seconds": elapsed,
            "startup_seconds": startup,
            "images_per_second": transferred / elapsed if elapsed > 0 else None,
            "startup_dominated": startup > elapsed,
            "note": ("Transfer cost only; no model runs here. startup_seconds is the "
                     "cost to reach the first batch (worker spawn and torch import on "
                     "Windows) and is excluded from images_per_second.")}


# --------------------------------------------------------------------------- #
# Full report
# --------------------------------------------------------------------------- #
def memory_report(*, device: str = "cuda", batches: Sequence[int] = (1, 2, 4),
                  steps: int = 2) -> Dict[str, Any]:
    """Every training stage, every inference path, plus a capacity search."""
    training: List[Dict[str, Any]] = []
    for stage in STAGE_SPECS:
        for batch in batches:
            training.append(measure_training_stage(stage, device=device, batch=batch,
                                                   steps=steps))
    # autocast comparison at one fixed batch, to show the effect in isolation
    autocast: List[Dict[str, Any]] = []
    for stage in ("G_train", "R_train"):
        for enabled in (False, True):
            autocast.append(measure_training_stage(stage, device=device, batch=2,
                                                   steps=steps, autocast=enabled))
    # gradient accumulation: same effective batch, different micro-batch
    accumulation: List[Dict[str, Any]] = []
    for accum in (1, 2):
        accumulation.append(measure_training_stage("G_train", device=device, batch=2,
                                                   steps=steps, accumulation=accum))
    inference = [measure_inference_path(model_key, device=device)
                 for model_key in REG.DISPLAY_ORDER]
    capacity = [max_batch_that_fits(stage, device=device) for stage in STAGE_SPECS]
    return {"schema": "phase_d_memory_v1", "evidence_class": EVIDENCE_CLASS,
            "device": device, "training": training, "autocast": autocast,
            "accumulation": accumulation, "inference": inference,
            "capacity": capacity,
            "transfer": [dataloader_overhead(workers=0, pin_memory=False, device=device),
                         dataloader_overhead(workers=0, pin_memory=True, device=device)],
            "note": ("SYNTHETIC_BENCHMARK. peak_allocated_mib is live memory; "
                     "peak_reserved_mib is allocator cache and is not a leak.")}


__all__ = ["EVIDENCE_CLASS", "GPU_TOTAL_MIB_HINT", "ROI_SIDE", "STAGE_SPECS", "StageSpec",
           "cpu_rss_mib", "cuda_available", "dataloader_overhead", "max_batch_that_fits",
           "measure_inference_path", "measure_training_stage", "memory_report"]
