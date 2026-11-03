"""Seed-family registry and RNG control.

A *seed family* is one complete, independently trained G -> R -> B -> S chain.
Nothing is shared between families except frozen data, frozen partitions and
frozen recipes: no checkpoint, no normaliser statistic, no calibration threshold
and no crop cache crosses a family boundary.

Derived seeds
-------------
Downstream stages cannot use the raw family seed directly, because doing so would
make, e.g., fold 0 of R and fold 0 of B share an initialisation stream.  Each
(component, run) therefore gets a deterministic *derived* seed::

    derived = int(sha256("RA-MedFiLM-BARR|FULL|<seed>|<component>|<run>")[:8], 16) % 2**31

The mapping is pure, recorded in every checkpoint, and reproducible without the
checkpoint.  The canonical phase seeds (B: 42000+k, S: 54000+k, final 42) are kept
verbatim for the canonical seed-42 family so it stays bit-comparable with the
historical producers; for new families the same *offsets* are applied to the
family seed rather than to a fixed base.
"""
from __future__ import annotations

import hashlib
import os
import random
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import torch

from . import recipe as R

# cuBLAS must be told to use a fixed workspace BEFORE the first CUDA kernel runs,
# otherwise GEMM reduction order varies between processes and two identical runs
# disagree in the 7th decimal place.  This is a reproducibility requirement, not a
# performance tuning knob.
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

__all__ = ["SeedFamily", "derived_seed", "seed_everything", "capture_rng", "restore_rng",
           "canonical_family_seed", "determinism_report"]

FAMILY_SEEDS = (42, 123, 3407)


@dataclass(frozen=True)
class SeedFamily:
    """One independent replicate."""

    seed: int
    label: str = ""

    def __post_init__(self) -> None:
        if self.seed not in FAMILY_SEEDS:
            raise ValueError(f"seed {self.seed} is not one of {FAMILY_SEEDS}")

    @property
    def tag(self) -> str:
        return self.label or f"seed{self.seed}"

    def run_seed(self, component: str, run: str = "main") -> int:
        """Deterministic per-(component, run) seed."""
        return derived_seed(self.seed, component, run)


def canonical_family_seed(component: str, run_index: int) -> int:
    """The seed the historical single-seed producer used for this run.

    B_phi and S_omega used ``base + k`` over their CV folds and 42 for the final
    refit; G and R used 42 throughout.  Recorded so the seed-42 family can be
    compared with the frozen historical artifacts on a like-for-like basis.
    """
    if component == "B":
        return R.B_FOLD_SEED_BASE + run_index if run_index >= 0 else R.B_FINAL_SEED
    if component == "S":
        return R.S_FOLD_SEED_BASE + run_index if run_index >= 0 else R.S_FINAL_SEED
    return 42


def derived_seed(family_seed: int, component: str, run: str) -> int:
    key = f"RA-MedFiLM-BARR|FULL|{family_seed}|{component}|{run}".encode("utf-8")
    return int(hashlib.sha256(key).hexdigest()[:8], 16) % (2 ** 31)


def seed_everything(seed: int, *, deterministic_cudnn: bool = True,
                    strict: bool = True) -> None:
    """Seed every RNG source and switch CUDA into a reproducible mode.

    ``strict`` enables ``torch.use_deterministic_algorithms``.  This is required:
    with only ``cudnn.deterministic`` set, two identical runs on this device
    disagreed by ~4e-7 in the epoch-1 training loss, which makes
    "resume is bit-exact" and "export is reproducible" untestable claims.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    if deterministic_cudnn:
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    if strict:
        torch.use_deterministic_algorithms(True, warn_only=False)


def determinism_report() -> dict:
    """Record the determinism configuration in every produced manifest."""
    return {
        "cudnn_deterministic": bool(torch.backends.cudnn.deterministic),
        "cudnn_benchmark": bool(torch.backends.cudnn.benchmark),
        "deterministic_algorithms": bool(torch.are_deterministic_algorithms_enabled()),
        "cublas_workspace_config": os.environ.get("CUBLAS_WORKSPACE_CONFIG"),
        "rng_sources": ["python", "numpy", "torch_cpu", "torch_cuda"],
    }


def capture_rng() -> dict:
    """Every RNG source that can influence a training stream."""
    return {
        "python": random.getstate(),
        "numpy": np.random.get_state(),
        "torch_cpu": torch.get_rng_state(),
        "torch_cuda": (torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None),
    }


def _as_cpu_byte_tensor(t):
    if isinstance(t, torch.Tensor):
        return t.detach().to(device="cpu", dtype=torch.uint8).contiguous()
    return torch.tensor(list(t), dtype=torch.uint8)


def restore_rng(state) -> None:
    """Restore a captured RNG state; a missing state is a hard error on resume.

    Without this a resumed run is not bit-exact: ``DataLoader(shuffle=True)`` and
    every augmentation draw from these streams.
    """
    if not state:
        raise ValueError("cannot restore an empty RNG state")
    if state.get("python") is not None:
        random.setstate(state["python"])
    if state.get("numpy") is not None:
        np.random.set_state(state["numpy"])
    if state.get("torch_cpu") is not None:
        torch.set_rng_state(_as_cpu_byte_tensor(state["torch_cpu"]))
    cuda_states = state.get("torch_cuda")
    if cuda_states is not None and torch.cuda.is_available():
        coerced = [_as_cpu_byte_tensor(s) for s in cuda_states]
        if len(coerced) == torch.cuda.device_count():
            torch.cuda.set_rng_state_all(coerced)


def family_order(seeds: Iterable[int] = FAMILY_SEEDS) -> list:
    """Stable execution order for the three families."""
    return [SeedFamily(int(s)) for s in seeds]
