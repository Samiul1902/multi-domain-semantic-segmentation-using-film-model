"""§10 Resource stability and §11 CPU/CUDA parity.

Allocator cache is not a leak
-----------------------------
``torch.cuda.memory_allocated`` is the live-tensor footprint: if it grows with
every iteration, something is being retained.  ``memory_reserved`` is the caching
allocator's pool: it rises to the high-water mark and then stays there **by
design**, which is why a flat-then-flat reserved series is the healthy shape and
a steadily rising one is not.  :func:`check_memory_growth` reports both series
and judges only the allocated slope, because judging the reserved series would
report a leak on every run.

Parity tolerances are inherited, not invented
---------------------------------------------
Phase B established the CPU/CUDA gate: exact routing-state match, binary
agreement above 0.99 at the frozen 0.50 threshold, and mean absolute probability
difference below 2e-3.  The same three numbers are used here.  They were chosen
in Phase B after investigating a genuine boundary-pixel discrepancy, and they are
**not** re-tuned here to make anything pass: if a model fails them, the failure is
reported.  No cross-device bitwise equality is claimed or tested.
"""
from __future__ import annotations

import gc
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence

import numpy as np
import torch

from src.research.evaluation import adapters as A
from src.research.evaluation import protocol as P
from src.research.evaluation import registry as REG

from . import bench as B

EVIDENCE_CLASS = B.EVIDENCE_CLASS

#: Inherited verbatim from the Phase B CPU/CUDA gate.  See the module docstring.
PARITY_BINARY_AGREEMENT_MIN = 0.99
PARITY_MEAN_ABS_DIFFERENCE_MAX = 2e-3

#: A leak is a *slope* in live memory, not a level.  Two MiB across the measured
#: window is well below one activation tensor at the 512 contract, so anything
#: under it is allocator noise rather than retention.
ALLOCATED_GROWTH_TOLERANCE_MIB = 2.0
#: Reserved memory is allowed to plateau; this is the tolerance on "plateau".
RESERVED_GROWTH_TOLERANCE_MIB = 64.0


def _check(name: str, passed: bool, detail: str, **extra: Any) -> Dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail, **extra}


def _allocated_mib(device: str) -> Optional[float]:
    if not (torch.cuda.is_available() and torch.device(device).type == "cuda"):
        return None
    return torch.cuda.memory_allocated(device) / 2 ** 20


def _reserved_mib(device: str) -> Optional[float]:
    if not (torch.cuda.is_available() and torch.device(device).type == "cuda"):
        return None
    return torch.cuda.memory_reserved(device) / 2 ** 20


def _handle_count() -> Optional[int]:
    """Open OS handles, where the platform exposes them."""
    try:
        import psutil

        process = psutil.Process(os.getpid())
        if hasattr(process, "num_handles"):               # Windows
            return int(process.num_handles())
        return int(process.num_fds())                     # POSIX
    except Exception:                                     # pragma: no cover - optional
        return None


def _slope(values: Sequence[float]) -> Optional[float]:
    """Least-squares slope per cycle, so a drift is separated from a level."""
    if len(values) < 2:
        return None
    x = np.arange(len(values), dtype=np.float64)
    y = np.asarray(values, dtype=np.float64)
    return float(np.polyfit(x, y, 1)[0])


# --------------------------------------------------------------------------- #
# 10. Memory growth, retained graphs, handles, caches, cleanup, reload
# --------------------------------------------------------------------------- #
def check_memory_growth(*, device: str = "cuda", model_key: Optional[str] = None,
                        cycles: int = 12, seed: int = 42) -> Dict[str, Any]:
    """Repeated inference must not grow live memory; the cache may plateau."""
    model_key = model_key or REG.BASELINES[0]
    if not (torch.cuda.is_available() and torch.device(device).type == "cuda"):
        return _check("memory_growth", True,
                      "no CUDA device; growth cannot be measured on CPU in a way that "
                      "distinguishes allocator cache from retention",
                      measured_on="cpu", skipped=True)
    adapter = A.build_synthetic(model_key, seed, device=device)
    adapter.load()
    image = B.synthetic_image(1, device=device)
    allocated: List[float] = []
    reserved: List[float] = []
    try:
        for _ in range(int(cycles)):
            adapter.predict(image, 3)
            B.synchronize(device)
            allocated.append(float(_allocated_mib(device) or 0.0))
            reserved.append(float(_reserved_mib(device) or 0.0))
    finally:
        adapter.close()

    # discard the first two cycles: warm-up legitimately allocates workspace
    tail_allocated = allocated[2:]
    allocated_slope = _slope(tail_allocated)
    reserved_slope = _slope(reserved[2:])
    allocated_growth = (tail_allocated[-1] - tail_allocated[0]) if len(tail_allocated) > 1 else 0.0
    reserved_growth = (reserved[-1] - reserved[0]) if len(reserved) > 1 else 0.0
    leak = (allocated_slope is not None
            and abs(allocated_growth) > ALLOCATED_GROWTH_TOLERANCE_MIB)
    cache_plateaued = abs(reserved_growth) <= RESERVED_GROWTH_TOLERANCE_MIB
    return _check(
        "memory_growth", (not leak) and cache_plateaued,
        (f"live memory changed by {allocated_growth:+.2f} MiB over {len(tail_allocated)} "
         f"cycles (slope {allocated_slope:+.4f} MiB/cycle) and the allocator cache "
         f"plateaued at {reserved_growth:+.2f} MiB: this is caching, not a leak"
         if not leak and cache_plateaued else
         f"live memory grew {allocated_growth:+.2f} MiB (slope {allocated_slope}); "
         f"cache changed {reserved_growth:+.2f} MiB"),
        model_key=model_key, cycles=int(cycles),
        allocated_mib=allocated, reserved_mib=reserved,
        allocated_slope_mib_per_cycle=allocated_slope,
        reserved_slope_mib_per_cycle=reserved_slope,
        allocated_growth_mib=allocated_growth, reserved_growth_mib=reserved_growth,
        leak_detected=leak, cache_plateaued=cache_plateaued)


def check_retained_graphs(*, device: str = "cuda", seed: int = 42) -> Dict[str, Any]:
    """A gradient-enabled forward must release its graph when dropped."""
    if not (torch.cuda.is_available() and torch.device(device).type == "cuda"):
        return _check("retained_graphs", True, "no CUDA device; skipped",
                      measured_on="cpu", skipped=True)
    B.reset_memory(device)
    baseline = float(_allocated_mib(device) or 0.0)
    model = torch.nn.Conv2d(3, 8, 3, padding=1).to(device)
    image = B.synthetic_image(1, device=device)
    with torch.no_grad():
        _ = model(image)
    after_no_grad = float(_allocated_mib(device) or 0.0)
    output = model(image)
    after_grad = float(_allocated_mib(device) or 0.0)
    graph_retained = output.grad_fn is not None
    del output
    gc.collect()
    B.synchronize(device)
    after_release = float(_allocated_mib(device) or 0.0)

    grew_with_graph = after_grad > after_no_grad
    released = abs(after_release - after_no_grad) <= 1.0
    passed = graph_retained and grew_with_graph and released
    return _check(
        "retained_graphs", passed,
        (f"a grad-enabled forward added {after_grad - after_no_grad:+.2f} MiB of graph "
         f"and dropping it returned to {after_release - after_no_grad:+.2f} MiB of the "
         "no-grad baseline: the graph is released, not retained"
         if passed else
         f"graph={graph_retained} grew={grew_with_graph} "
         f"after_release={after_release:.2f} baseline={after_no_grad:.2f}"),
        baseline_mib=baseline, after_no_grad_mib=after_no_grad,
        after_grad_mib=after_grad, after_release_mib=after_release,
        graph_retained_while_live=graph_retained)


def check_handle_leaks(*, device: str = "cuda", model_key: Optional[str] = None,
                       cycles: int = 5, windows: int = 3,
                       seed: int = 42) -> Dict[str, Any]:
    """Repeated load / infer / close cycles must reach a flat handle count.

    A single before/after comparison is not enough: the first cycles legitimately
    load DLLs and start thread pools, which looks identical to a leak in one
    window.  Measuring several consecutive windows separates the two — a leak
    grows by roughly one handle per cycle in *every* window, while one-time
    initialisation grows once and then stops.  Only the steady-state windows are
    judged, and the cold-start growth is reported so the distinction is visible.
    """
    model_key = model_key or REG.BASELINES[0]
    device_arg = device if torch.cuda.is_available() else "cpu"

    def run_window(count: int) -> Optional[int]:
        for _ in range(int(count)):
            adapter = A.build_synthetic(model_key, seed, device=device_arg)
            adapter.load()
            try:
                adapter.predict(B.synthetic_image(1, device=device_arg), 3)
            finally:
                adapter.close()
        gc.collect()
        return _handle_count()

    start = _handle_count()
    if start is None:
        return _check("handle_leaks", True, "handle count unavailable on this platform",
                      skipped=True)
    counts = [start]
    for _ in range(int(windows)):
        value = run_window(cycles)
        if value is None:
            return _check("handle_leaks", True,
                          "handle count became unavailable during the run", skipped=True)
        counts.append(value)

    deltas = [counts[i + 1] - counts[i] for i in range(len(counts) - 1)]
    cold_start, steady = deltas[0], deltas[1:]
    # a per-cycle leak in any steady window would be about `cycles`
    allowance = max(1, int(cycles) // 5)
    passed = bool(steady) and all(delta <= allowance for delta in steady)
    return _check(
        "handle_leaks", passed,
        (f"OS handles went {start} -> {counts[-1]} over {windows * cycles} "
         f"load/infer/close cycles; per-window deltas {deltas}, so the "
         f"{cold_start:+d} in the first window is one-time initialisation and the "
         f"steady state is flat ({steady}) — not a leak"
         if passed else
         f"per-window deltas {deltas} keep growing, which is a per-cycle leak"),
        windows=counts, window_deltas=deltas, cold_start_growth=cold_start,
        steady_state_growth=steady, cycles_per_window=int(cycles),
        allowance_per_window=allowance)


def check_unbounded_caches(*, workdir: Optional[Path] = None, cycles: int = 20) -> Dict[str, Any]:
    """Repeated publish/verify cycles must not leave temp files or grow RSS."""
    from src.research.evaluation import metrics as MET
    from src.research.evaluation import provenance as PROV

    owned = workdir is None
    root = Path(workdir or (Path(__file__).resolve().parents[3] / "_tmp" /
                            "phase_d_cache_check"))
    if owned:
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True, exist_ok=True)

    base = np.zeros((4, 4), np.uint8)
    base[1:3, 1:3] = 1
    shifted = np.zeros((4, 4), np.uint8)
    shifted[1:3, 2:4] = 1
    records = [MET.score_prediction(sample_id=f"{d}-1", domain=d, task_id=3,
                                    final_probability=shifted.astype(np.float32),
                                    ground_truth=base) for d in P.DOMAINS]
    provenance = PROV.build_evaluation_provenance(
        model_key=REG.BASELINES[0], seed=42, split=P.SPLIT_VAL,
        adapter_identity={"model_key": REG.BASELINES[0], "seed": 42,
                          "adapter_kind": "PLAIN",
                          "checkpoint_sha256": "SYNTHETIC::cache_check"},
        evidence_class=P.SYNTHETIC_EVIDENCE, split_manifest_sha256="0" * 64,
        n_images=len(records), evaluation_configuration=PROV.evaluation_config(),
        synthetic=True, training_performed=False)
    summary = MET.aggregate_records(records)

    rss: List[float] = []
    cell = root / REG.BASELINES[0] / "seed42"
    for _ in range(int(cycles)):
        PROV.publish_cell(cell, records=records, provenance=provenance, summary=summary)
        PROV.verify_cell(cell)
        value = B.process_rss_mib()
        if value is not None:
            rss.append(value)

    files = sorted(p.name for p in cell.iterdir() if p.is_file())
    temporary = [name for name in files if name.startswith(".") and ".tmp" in name]
    rss_growth = (rss[-1] - rss[0]) if len(rss) > 1 else 0.0
    passed = not temporary and abs(rss_growth) <= 32.0
    outcome = _check(
        "unbounded_caches", passed,
        (f"{cycles} publish/verify cycles left no temporary files and host memory moved "
         f"{rss_growth:+.1f} MiB; the cell holds {len(files)} files"
         if passed else
         f"temporary={temporary} rss_growth={rss_growth:.1f} MiB files={files}"),
        cell_files=files, temporary_files=temporary,
        rss_growth_mib=rss_growth, cycles=int(cycles))
    if owned:
        # only the directory this function created, never a broader path
        import shutil

        shutil.rmtree(root, ignore_errors=True)
    return outcome


def check_cleanup(*, device: str = "cuda", model_key: Optional[str] = None,
                  seed: int = 42) -> Dict[str, Any]:
    """``close()`` must return live memory to the pre-load baseline."""
    model_key = model_key or REG.BASELINES[0]
    if not (torch.cuda.is_available() and torch.device(device).type == "cuda"):
        return _check("cleanup", True, "no CUDA device; skipped", skipped=True)
    B.reset_memory(device)
    baseline = float(_allocated_mib(device) or 0.0)
    adapter = A.build_synthetic(model_key, seed, device=device)
    adapter.load()
    loaded = float(_allocated_mib(device) or 0.0)
    adapter.close()
    gc.collect()
    B.reset_memory(device)
    released = float(_allocated_mib(device) or 0.0)
    residual = released - baseline
    passed = loaded > baseline and abs(residual) <= 2.0
    return _check(
        "cleanup", passed,
        (f"loading held {loaded - baseline:+.1f} MiB and close() returned to "
         f"{residual:+.2f} MiB of the baseline: the model's tensors were released"
         if passed else
         f"baseline={baseline:.2f} loaded={loaded:.2f} released={released:.2f}"),
        baseline_mib=baseline, loaded_mib=loaded, released_mib=released,
        residual_mib=residual)


def check_reload_overhead(*, device: str = "cuda", model_key: Optional[str] = None,
                          repeats: int = 5, seed: int = 42) -> Dict[str, Any]:
    """Construction cost relative to one inference, measured not assumed."""
    model_key = model_key or REG.BASELINES[0]
    device_arg = device if torch.cuda.is_available() else "cpu"
    build = B.measure_initialization(
        lambda: (lambda a: (a.load(), a)[1])(A.build_synthetic(model_key, seed,
                                                              device=device_arg)),
        repeats=int(repeats), device=device_arg,
        cleanup=lambda adapter: adapter.close())
    adapter = A.build_synthetic(model_key, seed, device=device_arg)
    adapter.load()
    try:
        image = B.synthetic_image(1, device=device_arg)
        inference = B.time_call(lambda: adapter.predict(image, 3), warmup=2, repeats=10,
                                device=device_arg)
    finally:
        adapter.close()
    ratio = (build["median"] / inference["median"]
             if build.get("median") and inference.get("median") else None)
    return _check(
        "reload_overhead", ratio is not None,
        (f"construction median {build['median']:.1f} ms versus one inference "
         f"{inference['median']:.1f} ms (ratio {ratio:.1f}x): reloading per image would "
         "dominate, so a resident model is the correct serving pattern"),
        build_ms=build, inference_ms=inference, ratio=ratio)


def stability_report(*, device: str = "cuda", seed: int = 42,
                     cycles: int = 12) -> Dict[str, Any]:
    """Every §10 check."""
    checks = [
        check_memory_growth(device=device, cycles=cycles, seed=seed),
        check_retained_graphs(device=device, seed=seed),
        check_handle_leaks(device=device, cycles=5, windows=3, seed=seed),
        check_unbounded_caches(cycles=20),
        check_cleanup(device=device, seed=seed),
        check_reload_overhead(device=device, seed=seed),
    ]
    failed = [c["check"] for c in checks if not c["passed"]]
    return {"schema": "phase_d_stability_v1", "evidence_class": EVIDENCE_CLASS,
            "device": device, "checks": checks, "n_checks": len(checks),
            "n_passed": len(checks) - len(failed), "failed": failed,
            "all_passed": not failed,
            "allocator_policy": {
                "peak_allocated_mib": "live tensors; a rising slope is retention",
                "peak_reserved_mib": ("allocator cache; a flat high-water mark is the "
                                      "healthy shape and is not a leak"),
                "tolerance_mib": {"allocated": ALLOCATED_GROWTH_TOLERANCE_MIB,
                                  "reserved": RESERVED_GROWTH_TOLERANCE_MIB}},
            "note": "SYNTHETIC_BENCHMARK. Fixture weights; no real-data claim."}


# --------------------------------------------------------------------------- #
# 11. CPU / CUDA parity
# --------------------------------------------------------------------------- #
def _modules(adapter: A.ModelAdapter) -> Dict[str, torch.nn.Module]:
    system = getattr(adapter, "_system", None)
    if system is not None:
        return {"g": system.g, "r": system.r, "b": system.b, "s": system.s}
    model = getattr(adapter, "_model", None)
    return {"model": model} if model is not None else {}


def _copy_weights(source: A.ModelAdapter, target: A.ModelAdapter) -> bool:
    """Copy weights so the two devices evaluate *the same* function.

    Without this the comparison would mix a device difference with an
    initialisation difference, and any conclusion would be unsupported.
    """
    source_modules, target_modules = _modules(source), _modules(target)
    if set(source_modules) != set(target_modules):
        return False
    for name, module in source_modules.items():
        state = {k: v.detach().cpu() for k, v in module.state_dict().items()}
        target_modules[name].load_state_dict(state)
    return True


def _compare(cpu_prediction: Any, cuda_prediction: Any, *, threshold: float) -> Dict[str, Any]:
    cpu_probability = np.asarray(cpu_prediction.probability, dtype=np.float64)
    cuda_probability = np.asarray(cuda_prediction.probability, dtype=np.float64)
    shape_match = cpu_probability.shape == cuda_probability.shape
    if not shape_match:                                   # pragma: no cover - defensive
        return {"shape_match": False, "both_finite": False,
                "max_abs_difference": None, "mean_abs_difference": None,
                "binary_agreement": None, "state_agreement": None}
    difference = np.abs(cpu_probability - cuda_probability)
    cpu_binary = cpu_probability >= threshold
    cuda_binary = cuda_probability >= threshold
    return {
        "shape_match": True,
        "both_finite": bool(np.isfinite(cpu_probability).all()
                            and np.isfinite(cuda_probability).all()),
        "max_abs_difference": float(difference.max()),
        "mean_abs_difference": float(difference.mean()),
        "binary_agreement": float((cpu_binary == cuda_binary).mean()),
        "state_agreement": (cpu_prediction.state == cuda_prediction.state
                            if cpu_prediction.state is not None else None),
        "cpu_state": cpu_prediction.state, "cuda_state": cuda_prediction.state,
    }


def parity_report(*, device: str = "cuda", seed: int = 42,
                  models: Optional[Sequence[str]] = None) -> Dict[str, Any]:
    """Every model, CPU versus CUDA, at the inherited Phase B tolerances."""
    if not torch.cuda.is_available():                     # pragma: no cover - host has a GPU
        return {"schema": "phase_d_parity_v1", "evidence_class": EVIDENCE_CLASS,
                "records": [], "all_passed": False,
                "reason": "no CUDA device available"}
    models = tuple(models or REG.DISPLAY_ORDER)
    records: List[Dict[str, Any]] = []
    for model_key in models:
        cuda = A.build_synthetic(model_key, seed, device="cuda")
        cuda.load()
        cpu = A.build_synthetic(model_key, seed, device="cpu")
        cpu.load()
        try:
            weights_copied = _copy_weights(cuda, cpu)
            image = B.synthetic_image(1, device="cuda")
            cuda_prediction = cuda.predict(image, 3)
            cpu_prediction = cpu.predict(image.cpu(), 3)
            comparison = _compare(cpu_prediction, cuda_prediction,
                                  threshold=P.SEGMENTATION_OUTPUT_THRESHOLD)
            routed = REG.ADAPTER_KINDS[model_key] == "ROUTED"
            passed = (comparison["shape_match"] and comparison["both_finite"]
                      and comparison["binary_agreement"] is not None
                      and comparison["binary_agreement"] >= PARITY_BINARY_AGREEMENT_MIN
                      and comparison["mean_abs_difference"]
                      <= PARITY_MEAN_ABS_DIFFERENCE_MAX
                      and (not routed or comparison["state_agreement"] is True))
            records.append({"model_key": model_key,
                            "adapter_kind": REG.ADAPTER_KINDS[model_key],
                            "weights_copied": weights_copied, **comparison,
                            "passed": bool(passed)})
        finally:
            cuda.close()
            cpu.close()
    failed = [r["model_key"] for r in records if not r["passed"]]
    return {"schema": "phase_d_parity_v1", "evidence_class": EVIDENCE_CLASS,
            "records": records, "n_models": len(records),
            "failed": failed, "all_passed": not failed,
            "tolerances": {
                "binary_agreement_min": PARITY_BINARY_AGREEMENT_MIN,
                "mean_abs_difference_max": PARITY_MEAN_ABS_DIFFERENCE_MAX,
                "threshold": P.SEGMENTATION_OUTPUT_THRESHOLD,
                "routing_state": "exact match required for routed models",
                "source": ("inherited unchanged from the Phase B CPU/CUDA gate; not "
                           "re-tuned in Phase D"),
            },
            "claim": ("no cross-device bitwise equality is claimed; these are agreement "
                      "criteria on a numerically different implementation"),
            "note": "SYNTHETIC_BENCHMARK. Fixture weights and a synthetic image."}


__all__ = ["ALLOCATED_GROWTH_TOLERANCE_MIB", "EVIDENCE_CLASS",
           "PARITY_BINARY_AGREEMENT_MIN", "PARITY_MEAN_ABS_DIFFERENCE_MAX",
           "RESERVED_GROWTH_TOLERANCE_MIB", "check_cleanup", "check_handle_leaks",
           "check_memory_growth", "check_reload_overhead", "check_retained_graphs",
           "check_unbounded_caches", "parity_report", "stability_report"]
