"""Exact output parity and measured inference cost on supplied control tensors."""
from __future__ import annotations

import time
from typing import Any, Callable, Sequence

import numpy as np
import torch

from .artifacts import ArtifactError


def assert_exact(reference: Any, candidate: Any, path: str = "output") -> None:
    """Reject shape, dtype, discrete-decision, key or finite-value differences."""
    if isinstance(reference, torch.Tensor):
        if not isinstance(candidate, torch.Tensor) or reference.dtype != candidate.dtype:
            raise ArtifactError(f"{path}: tensor type/dtype mismatch")
        if not torch.isfinite(reference).all() or not torch.isfinite(candidate).all() or not torch.equal(reference.cpu(), candidate.cpu()):
            raise ArtifactError(f"{path}: tensor parity failure")
    elif isinstance(reference, np.ndarray):
        if not isinstance(candidate, np.ndarray) or reference.dtype != candidate.dtype or not np.isfinite(reference).all() or not np.isfinite(candidate).all() or not np.array_equal(reference, candidate):
            raise ArtifactError(f"{path}: array parity failure")
    elif isinstance(reference, dict):
        if not isinstance(candidate, dict) or reference.keys() != candidate.keys():
            raise ArtifactError(f"{path}: output keys differ")
        for key in reference:
            assert_exact(reference[key], candidate[key], f"{path}.{key}")
    elif isinstance(reference, (list, tuple)):
        if type(reference) is not type(candidate) or len(reference) != len(candidate):
            raise ArtifactError(f"{path}: sequence mismatch")
        for i, (a, b) in enumerate(zip(reference, candidate)):
            assert_exact(a, b, f"{path}[{i}]")
    else:
        if isinstance(reference, (float, np.floating)) and not np.isfinite(reference):
            raise ArtifactError(f"{path}: nonfinite output")
        if type(reference) is not type(candidate) or reference != candidate:
            raise ArtifactError(f"{path}: scalar/decision mismatch")


def validate_control_batch(reference: Callable, packaged: Callable,
                           controls: Sequence[tuple[torch.Tensor, int]], *,
                           device: str = "cpu", warmup: int = 1,
                           repeats: int = 3, synthetic: bool = True) -> dict:
    """No data loaders or tuning; callers own control-population authorization."""
    if not controls or warmup < 0 or repeats < 1:
        raise ArtifactError("nonempty controls and positive repetitions required")
    gpu = torch.device(device).type == "cuda"
    if gpu and not torch.cuda.is_available():
        raise ArtifactError("CUDA requested but unavailable")
    for image, task in controls:
        if task not in range(4) or image.ndim != 4 or not torch.isfinite(image).all():
            raise ArtifactError("invalid control image/task")
        assert_exact(reference(image.clone(), task), packaged(image.clone(), task))
    for _ in range(warmup):
        for image, task in controls:
            packaged(image.clone(), task)
    if gpu:
        torch.cuda.synchronize(device)
        torch.cuda.reset_peak_memory_stats(device)
    elapsed = []
    for _ in range(repeats):
        for image, task in controls:
            if gpu:
                torch.cuda.synchronize(device)
            start = time.perf_counter()
            packaged(image.clone(), task)
            if gpu:
                torch.cuda.synchronize(device)
            elapsed.append(time.perf_counter() - start)
    return {"parity": "BIT_EXACT", "control_count": len(controls),
            "evidence_class": "SYNTHETIC_TEST_ONLY" if synthetic else "MEASURED_DEPLOYMENT_CONTROL_BATCH",
            "latency_seconds_mean": float(np.mean(elapsed)),
            "throughput_samples_per_second": len(elapsed) / sum(elapsed),
            "peak_allocated_bytes": torch.cuda.max_memory_allocated(device) if gpu else None,
            "analytical_macs": None, "scientific_validation": False}
