"""Phase D reproducible performance benchmark.

Every number this package produces is stamped ``SYNTHETIC_BENCHMARK``.  None of
it is a real-data segmentation result: the weights are fixtures and the routing
decisions are scripted or incidental, never the behaviour of a trained model.

What is measured, and what each measurement does *not* mean
----------------------------------------------------------
``initialization_ms``
    Time to construct the module.  Architecture and allocator cost only.
``model_forward_ms``
    One forward of one network on one tensor.  Not a pipeline.
``pipeline_ms``
    The complete inference path the evaluator actually calls
    (``adapter.predict``), including preprocessing-free tensor work, routing,
    ROI geometry, crop, fusion and the safety gate where applicable.
``preprocessing_ms`` / ``postprocessing_ms``
    The transform and the threshold/aggregate step, timed separately so they are
    never silently folded into "model latency".
``peak_allocated_mib`` / ``peak_reserved_mib``
    CUDA allocator peaks.  *Reserved* stays high after a run by design; only
    *allocated* is evidence about live tensors.

Three distinctions the mission requires and this module keeps:

* **cold vs warm** — the first call pays lazy CUDA context work and kernel
  autotuning; it is reported separately and never averaged into the warm figure.
* **conv/linear MACs vs wall time** — MACs are a property of the architecture,
  latency is a property of this host and this build.  They are never substituted
  for each other, and ``total_flops`` (which includes attention matmuls) is kept
  apart from conv/linear MACs.
* **batch 1 vs batch N** — batching is only meaningful for a single-network
  model.  The routed FULL/Lite pipeline is batch-1 by contract (its ROI and
  safety stages are per-image), so a batch > 1 is refused for it rather than
  silently measured as if it were batched.
"""
from __future__ import annotations

import platform
import statistics
import time
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Dict, List, Optional, Sequence

import numpy as np
import torch

from src.research.c3_baselines import experiment as C3
from src.research.evaluation import adapters as A
from src.research.evaluation import efficiency as EF
from src.research.evaluation import protocol as P
from src.research.evaluation import registry as REG

EVIDENCE_CLASS = "SYNTHETIC_BENCHMARK"

#: Benchmark conditions.  Every latency figure is only valid under exactly these.
DEFAULT_WARMUP = 5
DEFAULT_REPEATS = 30
DEFAULT_BATCH = 1
MAX_BATCH = 8


@dataclass(frozen=True)
class Conditions:
    """The declared measurement conditions for one benchmark run."""

    device: str = "cuda"
    resolution: int = P.RESOLUTION
    batch_size: int = DEFAULT_BATCH
    precision: str = "fp32"          # "fp32" | "amp"
    warmup: int = DEFAULT_WARMUP
    repeats: int = DEFAULT_REPEATS

    def with_(self, **changes: Any) -> "Conditions":
        return replace(self, **changes)

    def as_dict(self) -> Dict[str, Any]:
        cuda = torch.cuda.is_available()
        return {
            "device_type": "cuda" if cuda and self.device.startswith("cuda") else "cpu",
            "device_name": (torch.cuda.get_device_name(0) if cuda and self.device.startswith("cuda")
                            else platform.processor()),
            "device_total_memory_mib": (torch.cuda.get_device_properties(0).total_memory / 2 ** 20
                                        if cuda and self.device.startswith("cuda") else None),
            "torch_version": torch.__version__,
            "cuda_version": torch.version.cuda,
            "cudnn_version": torch.backends.cudnn.version() if cuda else None,
            "input_resolution": int(self.resolution),
            "batch_size": int(self.batch_size),
            "precision": self.precision,
            "warmup_iterations": int(self.warmup),
            "measured_repeats": int(self.repeats),
            "cuda_synchronized": bool(cuda and self.device.startswith("cuda")),
            "timing_source": "time.perf_counter around the measured call",
            "determinism": {"cudnn_deterministic": torch.backends.cudnn.deterministic,
                            "cudnn_benchmark": torch.backends.cudnn.benchmark},
            "note": ("Latency is a property of this host and this build, not of the method. "
                     "Synthetic weights: no accuracy claim follows from these numbers."),
        }


# --------------------------------------------------------------------------- #
# Timing primitives
# --------------------------------------------------------------------------- #
def synchronize(device: str | torch.device) -> None:
    """CUDA synchronisation guard, so a GPU time is not measured as launch time."""
    dev = torch.device(device)
    if dev.type == "cuda" and torch.cuda.is_available():
        torch.cuda.synchronize(dev)


def percentiles(samples: Sequence[float]) -> Dict[str, Any]:
    """Median / p90 / p95 with the counts that produced them."""
    arr = np.asarray([s for s in samples if s is not None and np.isfinite(s)], dtype=np.float64)
    if arr.size == 0:
        return {"n": 0, "median": None, "p90": None, "p95": None, "mean": None,
                "min": None, "max": None, "stdev": None}
    return {"n": int(arr.size),
            "median": float(np.median(arr)),
            "p90": float(np.percentile(arr, 90)),
            "p95": float(np.percentile(arr, 95)),
            "mean": float(arr.mean()),
            "min": float(arr.min()),
            "max": float(arr.max()),
            "stdev": float(arr.std(ddof=1)) if arr.size > 1 else 0.0,
            "unit": "milliseconds"}


def time_call(fn: Callable[[], Any], *, warmup: int, repeats: int,
              device: str | torch.device) -> Dict[str, Any]:
    """Time ``fn`` with warm-up discarded and CUDA synchronised on both sides."""
    cold: Optional[float] = None
    synchronize(device)
    start = time.perf_counter()
    fn()
    synchronize(device)
    cold = (time.perf_counter() - start) * 1000.0
    for _ in range(int(warmup)):
        fn()
    synchronize(device)
    samples: List[float] = []
    for _ in range(int(repeats)):
        synchronize(device)
        start = time.perf_counter()
        fn()
        synchronize(device)
        samples.append((time.perf_counter() - start) * 1000.0)
    out = percentiles(samples)
    out["cold_first_call"] = cold
    out["warmup_iterations"] = int(warmup)
    out["measured_repeats"] = int(repeats)
    return out


def measure_initialization(builder: Callable[[], Any], *, repeats: int = 5,
                           device: str = "cuda",
                           cleanup: Optional[Callable[[Any], None]] = None) -> Dict[str, Any]:
    """Construction time of a module, measured on fresh constructions only.

    ``cleanup`` runs **outside** the timed region, so releasing the previous
    object does not inflate the measurement and five systems are never resident
    at once (which would change the allocator's behaviour mid-benchmark).
    """
    synchronize(device)
    samples: List[float] = []
    for _ in range(int(repeats)):
        start = time.perf_counter()
        built = builder()
        samples.append((time.perf_counter() - start) * 1000.0)
        if cleanup is not None:
            cleanup(built)
    out = percentiles(samples)
    out["constructions"] = int(repeats)
    return out


def measure_peak_memory(fn: Callable[[], Any], *, device: str) -> Dict[str, Any]:
    """Peak allocated and reserved MiB around one call."""
    if not (torch.cuda.is_available() and torch.device(device).type == "cuda"):
        return {"peak_allocated_mib": None, "peak_reserved_mib": None,
                "memory_unit": "MiB", "reason": "CPU device"}
    torch.cuda.empty_cache()
    torch.cuda.reset_peak_memory_stats(device)
    fn()
    synchronize(device)
    return {"peak_allocated_mib": torch.cuda.max_memory_allocated(device) / 2 ** 20,
            "peak_reserved_mib": torch.cuda.max_memory_reserved(device) / 2 ** 20,
            "memory_unit": "MiB"}


def reset_memory(device: str) -> None:
    """Drop cached blocks and peak counters between measurements."""
    if torch.cuda.is_available() and torch.device(device).type == "cuda":
        torch.cuda.empty_cache()
        torch.cuda.reset_peak_memory_stats(device)
        torch.cuda.synchronize(device)


def process_rss_mib() -> Optional[float]:
    """Resident host memory of this process.

    Kept because a GPU-only view hides a real failure mode: the CPU side of the
    pipeline (PIL decode, ROI crops, the metric battery) can be the limit on a
    512x512 contract long before the card is full.
    """
    try:
        import psutil

        return psutil.Process().memory_info().rss / 2 ** 20
    except Exception:                                        # pragma: no cover - optional dep
        return None


# --------------------------------------------------------------------------- #
# Synthetic inputs
# --------------------------------------------------------------------------- #
def synthetic_image(batch: int = 1, *, resolution: int = P.RESOLUTION,
                    device: str = "cpu", seed: int = 20261103) -> torch.Tensor:
    """A deterministic pseudo-image in [0, 1].  Not a medical image."""
    gen = torch.Generator(device="cpu").manual_seed(int(seed))
    image = torch.rand((batch, 3, resolution, resolution), generator=gen, dtype=torch.float32)
    return image.to(device)


def synthetic_pil_image(*, size: int = 640, seed: int = 20261103):
    """A PIL image for preprocessing timing (the transform consumes PIL)."""
    from PIL import Image

    gen = np.random.default_rng(int(seed))
    array = (gen.random((size, size, 3)) * 255).astype(np.uint8)
    return Image.fromarray(array, mode="RGB")


def synthetic_mask(*, size: int = 640, seed: int = 20261104):
    from PIL import Image

    gen = np.random.default_rng(int(seed))
    array = (gen.random((size, size)) > 0.5).astype(np.uint8) * 255
    return Image.fromarray(array, mode="L")


# --------------------------------------------------------------------------- #
# Pre / post processing
# --------------------------------------------------------------------------- #
def benchmark_preprocessing(*, repeats: int = 20) -> Dict[str, Any]:
    """The frozen Phase-4 v3 transform, timed on its own."""
    from src.data.transforms import SegmentationTransform

    transform = SegmentationTransform(P.RESOLUTION, train=False, image_mode=P.CHANNEL_POLICY[:3])
    image, mask = synthetic_pil_image(), synthetic_mask()
    out = time_call(lambda: transform(image, mask), warmup=3, repeats=repeats, device="cpu")
    out["preprocessing_id"] = P.PREPROCESSING_ID
    out["note"] = "PIL decode + resize/pad to 512 + normalise; CPU only, by contract"
    return out


def benchmark_postprocessing(probability: np.ndarray, *, repeats: int = 20) -> Dict[str, Any]:
    """Threshold plus aggregate, timed separately from model inference."""
    from src.research.evaluation import metrics as MET

    def run() -> None:
        MET.score_prediction(sample_id="bench", domain="KUB", task_id=3,
                             final_probability=probability,
                             ground_truth=(probability >= 0.5))

    out = time_call(run, warmup=3, repeats=repeats, device="cpu")
    out["note"] = "threshold + confusion + Dice/IoU/HD95 on a 512x512 map"
    return out


# --------------------------------------------------------------------------- #
# Per-model benchmark
# --------------------------------------------------------------------------- #
def _forward_fn(adapter: A.ModelAdapter, image: torch.Tensor, task_id: int,
                precision: str) -> Callable[[], Any]:
    """A raw forward under the declared precision, bypassing the adapter wrapper."""
    model = getattr(adapter, "_model", None)
    if model is None:
        return lambda: adapter.predict(image, task_id)
    device = adapter.device
    if adapter.kind == "TASK_CONDITIONED":
        task = torch.full((image.shape[0],), int(task_id), dtype=torch.long, device=device)

        def run() -> Any:
            if precision == "amp":
                with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                    return model(image, task)
            return model(image, task)
        return run

    def run() -> Any:
        if precision == "amp":
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                return model(image)
        return model(image)
    return run


def benchmark_single_network(model_key: str, *, seed: int = 42, conditions: Conditions,
                             adapter: Optional[A.ModelAdapter] = None) -> Dict[str, Any]:
    """A TASK_CONDITIONED or PLAIN model: batched forward is meaningful here."""
    own = adapter is None
    if own:
        adapter = A.build_synthetic(model_key, seed, device=conditions.device)
        adapter.load()
    try:
        image = synthetic_image(conditions.batch_size, resolution=conditions.resolution,
                                device=conditions.device)
        forward = _forward_fn(adapter, image, 3, conditions.precision)
        forward_ms = time_call(forward, warmup=conditions.warmup, repeats=conditions.repeats,
                               device=conditions.device)
        pipeline_ms = time_call(lambda: adapter.predict(image[:1], 3),
                                warmup=conditions.warmup, repeats=conditions.repeats,
                                device=conditions.device)
        memory = measure_peak_memory(lambda: adapter.predict(image[:1], 3),
                                     device=conditions.device)
        macs = EF.count_macs(adapter)
        record = {
            "model_key": model_key, "seed": int(seed), "adapter_kind": adapter.kind,
            "batched_forward": True,
            "model_forward_ms": forward_ms,
            "pipeline_ms": pipeline_ms,
            "memory": memory,
            "parameters": adapter.parameter_count(),
            "macs": {"conv_linear_macs": macs.get("macs_global_only"),
                     "method": macs.get("method"), "unit": "multiply-accumulate"},
            "conditional_refiner_invocation_rate": None,
            "throughput_images_per_s": (1000.0 / forward_ms["median"]
                                        if forward_ms["median"] else None),
            "notes": ["batched forward; batch = %d" % conditions.batch_size],
        }
        if adapter.kind == "TASK_CONDITIONED":
            record["notes"].append("task id is a genuine model input")
        else:
            record["notes"].append("PLAIN baseline: no task input by design")
        return record
    finally:
        if own and adapter is not None:
            adapter.close()


def benchmark_routed(model_key: str, *, seed: int = 42, conditions: Conditions,
                     adapter: Optional[A.ModelAdapter] = None) -> Dict[str, Any]:
    """FULL or Lite: the complete G/R/B/S pipeline, batch-1 by contract."""
    if conditions.batch_size != 1:
        raise ValueError(
            f"{model_key} is a routed pipeline whose ROI and safety stages are per-image; "
            f"batch {conditions.batch_size} is not a supported measurement")
    own = adapter is None
    if own:
        adapter = A.build_synthetic(model_key, seed, device=conditions.device)
        adapter.load()
    try:
        system = adapter._system
        image = synthetic_image(1, resolution=conditions.resolution, device=conditions.device)
        task = torch.tensor([3], dtype=torch.long, device=conditions.device)

        # the pipeline as the evaluator calls it
        pipeline_ms = time_call(lambda: adapter.predict(image, 3),
                                warmup=conditions.warmup, repeats=conditions.repeats,
                                device=conditions.device)
        memory = measure_peak_memory(lambda: adapter.predict(image, 3), device=conditions.device)

        # component costs, each measured on its own so the split is visible
        component: Dict[str, Any] = {}
        component["G"] = time_call(lambda: system.g(image, task_ids=task),
                                   warmup=2, repeats=max(3, conditions.repeats // 3),
                                   device=conditions.device)
        r_input = torch.zeros((1, 4, 256, 256), device=conditions.device)
        component["R"] = time_call(lambda: system.r(r_input), warmup=2,
                                   repeats=max(3, conditions.repeats // 3),
                                   device=conditions.device)
        b_input = torch.zeros((1, 202), device=conditions.device)
        component["B"] = time_call(lambda: system.b(b_input, task), warmup=2,
                                   repeats=max(3, conditions.repeats // 3),
                                   device=conditions.device)
        s_input = torch.zeros((1, 20), device=conditions.device)
        component["S"] = time_call(lambda: system.s(s_input), warmup=2,
                                   repeats=max(3, conditions.repeats // 3),
                                   device=conditions.device)

        # the observed decision, on the fixture — NOT a property of a trained model
        decision = adapter.predict(image, 3)
        macs = EF.count_macs(adapter)
        always = None
        if macs.get("macs_global_only") is not None:
            always = int(macs["macs_global_only"] + macs.get("macs_router_per_image", 0)
                         + macs.get("macs_refiner_per_call", 0)
                         + macs.get("macs_safety_per_call", 0))
        return {
            "model_key": model_key, "seed": int(seed), "adapter_kind": adapter.kind,
            "batched_forward": False,
            "model_forward_ms": component["G"],
            "component_ms": component,
            "pipeline_ms": pipeline_ms,
            "memory": memory,
            "parameters": adapter.parameter_count(),
            "macs": {"conv_linear_macs_global_only": macs.get("macs_global_only"),
                     "conv_linear_macs_if_always_refine": always,
                     "method": macs.get("method"), "unit": "multiply-accumulate"},
            "observed_state": decision.state,
            "observed_router_score": decision.router_score,
            "observed_safety_probability": decision.safety_probability,
            "conditional_refiner_invocation_rate": (
                1.0 if decision.state in ("EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT") else 0.0),
            "throughput_images_per_s": (1000.0 / pipeline_ms["median"]
                                        if pipeline_ms["median"] else None),
            "notes": ["batch-1 by contract: ROI and safety are per-image",
                      "observed_state is a fixture outcome, not trained-model behaviour"],
        }
    finally:
        if own and adapter is not None:
            adapter.close()


def benchmark_model(model_key: str, *, seed: int = 42, conditions: Conditions) -> Dict[str, Any]:
    """Dispatch to the right measurement for the model's adapter kind."""
    kind = REG.ADAPTER_KINDS[model_key]
    if kind == "ROUTED":
        record = benchmark_routed(model_key, seed=seed, conditions=conditions)
    else:
        record = benchmark_single_network(model_key, seed=seed, conditions=conditions)
    record["initialization_ms"] = benchmark_initialization(
        model_key, seed=seed, device=conditions.device)
    record["cpu_memory_mib"] = process_rss_mib()
    record["conditions"] = conditions.as_dict()
    record["evidence_class"] = EVIDENCE_CLASS
    return record


def benchmark_initialization(model_key: str, *, seed: int = 42, device: str = "cuda",
                             repeats: int = 5) -> Dict[str, Any]:
    """Module construction time only: architecture + allocator, no data."""
    kind = REG.ADAPTER_KINDS[model_key]

    def build() -> Any:
        adapter = A.build_synthetic(model_key, seed, device=device)
        adapter.load()
        return adapter

    def release(adapter: Any) -> None:
        adapter.close()
        reset_memory(device)

    out = measure_initialization(build, repeats=repeats, device=device, cleanup=release)
    out["scope"] = ("complete G/R/B/S system" if kind == "ROUTED" else "single network")
    return out


def benchmark_batch_scaling(model_key: str, *, seed: int = 42, device: str = "cuda",
                            batches: Sequence[int] = (1, 2, 4, 8),
                            warmup: int = 3, repeats: int = 10) -> Dict[str, Any]:
    """Forward latency and throughput at several batch sizes.

    Only a single-network model is batched.  A routed pipeline is refused rather
    than measured, because its ROI and safety stages are per-image by contract
    and a "batched" number for it would be a fiction.
    """
    if REG.ADAPTER_KINDS[model_key] == "ROUTED":
        raise ValueError(
            f"{model_key} is batch-1 by contract; batching its per-image ROI and safety "
            "stages would measure a pipeline that does not exist")
    adapter = A.build_synthetic(model_key, seed, device=device)
    adapter.load()
    rows: List[Dict[str, Any]] = []
    try:
        for batch in batches:
            image = synthetic_image(int(batch), resolution=P.RESOLUTION, device=device)
            forward = _forward_fn(adapter, image, 3, "fp32")
            timing = time_call(forward, warmup=warmup, repeats=repeats, device=device)
            median = timing.get("median")
            rows.append({"batch_size": int(batch),
                         "model_forward_ms": timing,
                         "per_image_ms": (median / batch) if median else None,
                         "throughput_images_per_s": (1000.0 * batch / median) if median else None,
                         "peak_memory": measure_peak_memory(lambda: forward(), device=device)})
            reset_memory(device)
    finally:
        adapter.close()
    return {"model_key": model_key, "seed": int(seed), "evidence_class": EVIDENCE_CLASS,
            "rows": rows,
            "note": ("Batching changes throughput, not per-image work. A per-image latency "
                     "claim must be made at batch 1.")}


def _as_comparable(value: Any) -> torch.Tensor:
    """Coerce a forward result to a comparable tensor.

    A single-network model returns a tensor; a routed adapter returns its
    ``Prediction``, whose probability field is the numpy array the evaluator
    consumes.  Comparing across precisions has to use the same object in both
    arms, so the routed case compares the final probability field rather than a
    single internal logit.
    """
    if isinstance(value, torch.Tensor):
        return value.detach().float().cpu()
    for attribute in ("probability", "global_probability", "mask", "logits"):
        candidate = getattr(value, attribute, None)
        if isinstance(candidate, np.ndarray):
            return torch.from_numpy(np.ascontiguousarray(candidate)).float()
        if isinstance(candidate, torch.Tensor):
            return candidate.detach().float().cpu()
    if isinstance(value, (tuple, list)) and value:
        return _as_comparable(value[0])
    raise TypeError(f"cannot compare a forward result of type {type(value).__name__}")


def benchmark_precision(model_key: str, *, seed: int = 42, device: str = "cuda",
                        warmup: int = 5, repeats: int = 20) -> Dict[str, Any]:
    """FP32 versus mixed precision on the same input, with the numerical delta.

    Autocast is a numerical change, not only a speed change, so the maximum
    absolute output difference is reported next to the timing.  A speed-up that
    moves the output is not free and is never reported as such.
    """
    adapter = A.build_synthetic(model_key, seed, device=device)
    adapter.load()
    try:
        batch = 1 if REG.ADAPTER_KINDS[model_key] == "ROUTED" else 2
        image = synthetic_image(batch, resolution=P.RESOLUTION, device=device)
        fp32_fn = _forward_fn(adapter, image, 3, "fp32")
        amp_fn = _forward_fn(adapter, image, 3, "amp")
        fp32_t = time_call(fp32_fn, warmup=warmup, repeats=repeats, device=device)
        amp_t = time_call(amp_fn, warmup=warmup, repeats=repeats, device=device)

        with torch.no_grad():
            reference = fp32_fn()
            candidate = amp_fn()
        ref_t = _as_comparable(reference)
        cand_t = _as_comparable(candidate)
        shape_match = tuple(ref_t.shape) == tuple(cand_t.shape)
        delta = (float((ref_t - cand_t).abs().max()) if shape_match else None)
        return {"model_key": model_key, "seed": int(seed),
                "evidence_class": EVIDENCE_CLASS,
                "batch_size": int(batch),
                "compared_field": ("final probability field"
                                   if REG.ADAPTER_KINDS[model_key] == "ROUTED"
                                   else "logits"),
                "fp32": fp32_t, "amp": amp_t,
                "speedup": (fp32_t["median"] / amp_t["median"]
                            if amp_t.get("median") else None),
                "numerical": {"shape_match": shape_match,
                              "max_abs_difference": delta,
                              "note": ("autocast changes the arithmetic; the delta is "
                                       "reported so a speed-up is never reported as free")},
                "peak_memory": {"fp32": measure_peak_memory(fp32_fn, device=device),
                                "amp": measure_peak_memory(amp_fn, device=device)}}
    finally:
        adapter.close()


def benchmark_all(*, seeds: Sequence[int] = (42,), device: str = "cuda",
                  warmup: int = DEFAULT_WARMUP, repeats: int = DEFAULT_REPEATS,
                  models: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Every model at the declared conditions, plus preprocessing timing."""
    models = tuple(models or REG.DISPLAY_ORDER)
    records: List[Dict[str, Any]] = []
    for model_key in models:
        for seed in seeds:
            conditions = Conditions(device=device, warmup=warmup, repeats=repeats)
            records.append(benchmark_model(model_key, seed=seed, conditions=conditions))
    return {"schema": "phase_d_benchmark_v1", "evidence_class": EVIDENCE_CLASS,
            "conditions": Conditions(device=device, warmup=warmup,
                                     repeats=repeats).as_dict(),
            "preprocessing": benchmark_preprocessing(),
            "records": records,
            "note": ("SYNTHETIC_BENCHMARK. Fixture weights; routing outcomes are incidental. "
                     "No accuracy or real-data performance claim follows.")}


def full_sweep(*, seeds: Sequence[int] = REG.SEEDS, device: str = "cuda",
               warmup: int = DEFAULT_WARMUP, repeats: int = DEFAULT_REPEATS,
               models: Optional[Sequence[str]] = None,
               batch_scaling: bool = True, precision: bool = True) -> Dict[str, Any]:
    """The complete §2 measurement set in one document.

    Latency at the declared conditions, then the two contrasts that must not be
    inferred from it: batching (single-network models only) and precision.
    """
    models = tuple(models or REG.DISPLAY_ORDER)
    base = benchmark_all(seeds=seeds, device=device, warmup=warmup, repeats=repeats,
                         models=models)
    base["batch_scaling"] = ([benchmark_batch_scaling(key, seed=seeds[0], device=device,
                                                      warmup=max(2, warmup // 2),
                                                      repeats=max(5, repeats // 3))
                              for key in models if REG.ADAPTER_KINDS[key] != "ROUTED"]
                             if batch_scaling else [])
    base["precision"] = ([benchmark_precision(key, seed=seeds[0], device=device,
                                              warmup=warmup,
                                              repeats=max(5, repeats // 2))
                          for key in models] if precision else [])
    base["routed_batch_policy"] = {
        "batched_models": [k for k in models if REG.ADAPTER_KINDS[k] != "ROUTED"],
        "batch1_only": [k for k in models if REG.ADAPTER_KINDS[k] == "ROUTED"],
        "reason": ("FULL and Lite run per-image ROI geometry, routing and a safety gate; "
                   "a batch>1 number for them would describe a pipeline that does not exist")}
    base["seeds"] = [int(s) for s in seeds]
    return base


__all__ = ["Conditions", "DEFAULT_BATCH", "DEFAULT_REPEATS", "DEFAULT_WARMUP",
           "EVIDENCE_CLASS", "MAX_BATCH", "benchmark_all", "benchmark_batch_scaling",
           "benchmark_initialization", "benchmark_model", "benchmark_postprocessing",
           "benchmark_precision", "benchmark_preprocessing", "benchmark_routed",
           "benchmark_single_network", "full_sweep", "measure_initialization",
           "measure_peak_memory", "percentiles", "process_rss_mib", "reset_memory",
           "synchronize", "synthetic_image", "synthetic_mask", "synthetic_pil_image",
           "time_call"]
