"""
Canonical device contract (Phase 08 Part 1A).

Canonical scientific runs are CUDA-first. Canonical training/evaluation paths
must FAIL rather than silently fall back to CPU.

CPU may be used only in explicitly labelled unit tests that do not represent
canonical experiment execution.
"""
from __future__ import annotations

import torch

CANONICAL_REQUIRES_CUDA = True


class CudaUnavailableError(RuntimeError):
    """Raised when a canonical path requires CUDA but CUDA is unavailable."""


def cuda_available() -> bool:
    return bool(torch.cuda.is_available())


def get_device(require_cuda: bool = CANONICAL_REQUIRES_CUDA,
               index: int = 0,
               allow_cpu_fallback: bool = False) -> torch.device:
    """
    Resolve the execution device.

    Parameters
    ----------
    require_cuda : bool
        When True (the canonical default), raise if CUDA is unavailable.
    index : int
        CUDA device index.
    allow_cpu_fallback : bool
        Explicit opt-out for non-canonical contexts (e.g. labelled unit tests).
        When True and CUDA is unavailable, returns CPU instead of raising.

    Returns
    -------
    torch.device

    Raises
    ------
    CudaUnavailableError
        When ``require_cuda`` is True, CUDA is unavailable, and
        ``allow_cpu_fallback`` is False.
    """
    if torch.cuda.is_available():
        return torch.device(f"cuda:{index}")
    if require_cuda and not allow_cpu_fallback:
        raise CudaUnavailableError(
            "CUDA is required for canonical execution but is unavailable. "
            "Refusing to silently fall back to CPU. Pass allow_cpu_fallback=True "
            "only in explicitly labelled non-canonical unit tests."
        )
    return torch.device("cpu")


def device_report() -> dict:
    """Environment/device report for audit artifacts."""
    available = cuda_available()
    return {
        "cuda_available": available,
        "cuda_device_count": torch.cuda.device_count() if available else 0,
        "cuda_device": torch.cuda.get_device_name(0) if available else None,
        "pytorch_version": torch.__version__,
        "cuda_runtime_version": torch.version.cuda,
        "cudnn_version": torch.backends.cudnn.version() if available else None,
        "cuda_capability": (list(torch.cuda.get_device_capability(0)) if available else None),
        "canonical_requires_cuda": CANONICAL_REQUIRES_CUDA,
    }


def amp_supported() -> bool:
    """CUDA AMP availability (autocast + GradScaler)."""
    return cuda_available()


def make_grad_scaler(enabled: bool = True):
    """
    Construct a GradScaler compatible with PyTorch 2.6.

    ``torch.amp.GradScaler('cuda', ...)`` is the current API; the bare
    ``torch.cuda.amp.GradScaler`` form is deprecated.
    """
    if enabled and not cuda_available():
        raise CudaUnavailableError("AMP GradScaler requested but CUDA is unavailable")
    try:
        return torch.amp.GradScaler("cuda", enabled=enabled)
    except (AttributeError, TypeError):
        return torch.cuda.amp.GradScaler(enabled=enabled)


def make_autocast(enabled: bool = True):
    """Return an autocast context manager compatible with PyTorch 2.6."""
    try:
        return torch.amp.autocast("cuda", enabled=enabled)
    except (AttributeError, TypeError):
        return torch.cuda.amp.autocast(enabled=enabled)
