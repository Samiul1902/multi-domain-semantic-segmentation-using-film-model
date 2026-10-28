"""Additive matched C1 arms using the unchanged frozen GlobalMedFiLM class.

No datasets, historical checkpoints, training driver, or CUDA execution here.
Callers may use fresh models on synthetic tensors for implementation tests.
"""
from __future__ import annotations

import copy
import hashlib
from pathlib import Path

import torch

from src.models.film.global_medfilm import GlobalMedFiLM

ARCHITECTURE_SHA256 = "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f"
CONDITIONING_PREFIXES = ("task_embedding.", "film_layers.")
EXPECTED_COUNTS = {"total": 3523001, "conditioning": 90768, "backbone": 3432233}


def is_conditioning(name: str) -> bool:
    return name.startswith(CONDITIONING_PREFIXES)


def verify_architecture_source() -> None:
    source = Path(__file__).resolve().parents[2] / "models/film/global_medfilm.py"
    if hashlib.sha256(source.read_bytes()).hexdigest() != ARCHITECTURE_SHA256:
        raise RuntimeError("C1_ARCHITECTURE_SOURCE_DRIFT")


def parameter_accounting(model: GlobalMedFiLM) -> dict:
    named = tuple(model.named_parameters())
    total = sum(p.numel() for _, p in named)
    conditioning = sum(p.numel() for n, p in named if is_conditioning(n))
    return {
        "total": total,
        "conditioning": conditioning,
        "backbone": total - conditioning,
        "trainable": sum(p.numel() for _, p in named if p.requires_grad),
        "frozen": sum(p.numel() for _, p in named if not p.requires_grad),
        "parameter_bytes_fp32": sum(p.numel() * p.element_size() for _, p in named),
    }


def verify_identity_control(model: GlobalMedFiLM) -> None:
    """Check frozen projections and exactly zero gamma/beta for every task/site."""
    for name, p in model.named_parameters():
        if is_conditioning(name) and p.requires_grad:
            raise RuntimeError("C1_CONDITIONING_NOT_FROZEN")
    for layer in model.film_layers.values():
        if torch.count_nonzero(layer.output.weight).item() != 0:
            raise RuntimeError("C1_NONIDENTITY_WEIGHT")
        if torch.count_nonzero(layer.output.bias).item() != 0:
            raise RuntimeError("C1_NONIDENTITY_BIAS")
    device = model.task_embedding.weight.device
    with torch.no_grad():
        params = model.film_parameters_for_tasks(torch.arange(4, device=device))
    for gamma, beta in params.values():
        if not torch.isfinite(gamma).all() or not torch.isfinite(beta).all():
            raise RuntimeError("C1_NONFINITE_MODULATION")
        if torch.count_nonzero(gamma).item() or torch.count_nonzero(beta).item():
            raise RuntimeError("C1_NONIDENTITY_MODULATION")


def build_matched_arms(seed: int) -> tuple[GlobalMedFiLM, GlobalMedFiLM]:
    """Fresh canonical treatment + exact initial-state copy with conditioning frozen.

    Copying occurs before optimization, not from a trained treatment checkpoint.
    CPU RNG state is restored; no different draw order between the arm backbones.
    """
    if type(seed) is not int or seed not in (42, 123, 3407):
        raise ValueError("C1_SEED_NOT_PREDECLARED")
    verify_architecture_source()
    with torch.random.fork_rng(devices=[]):
        torch.random.default_generator.manual_seed(seed)
        treatment = GlobalMedFiLM()
    control = copy.deepcopy(treatment)
    for name, p in control.named_parameters():
        if is_conditioning(name):
            p.requires_grad_(False)
    for model, trainable in ((treatment, 3523001), (control, 3432233)):
        counts = parameter_accounting(model)
        if any(counts[k] != v for k, v in EXPECTED_COUNTS.items()):
            raise RuntimeError("C1_PARAMETER_ACCOUNTING_DRIFT")
        if counts["trainable"] != trainable:
            raise RuntimeError("C1_TRAINABLE_ACCOUNTING_DRIFT")
    verify_identity_control(control)
    return treatment, control


def optimizer_group_spec(model: GlobalMedFiLM) -> list[dict]:
    """One AdamW group; frozen tensors are not handed to the optimizer.

    C1 lr/wd are inherited from Phase21. Not an authorization to train.
    """
    params = [p for p in model.parameters() if p.requires_grad]
    return [{"params": params, "lr": 1e-4, "weight_decay": 1e-4}]
