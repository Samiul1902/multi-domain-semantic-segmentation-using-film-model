"""Sequential Lite component producers: G -> R_psi -> B_phi -> S_omega.

Every stage checkpoint records its family, variant, seed and the SHA-256 of
each upstream checkpoint.  A Lite stage refuses FULL-family weights and any
upstream hash that is not the exact predecessor used for training.
Real-data execution is blocked here exactly like the C3 harness; only
synthetic loaders may run until a separate release exists.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import numpy as np
import torch
from torch import nn

from src.models.lite.ra_medfilm_barr_lite import LiteVariantSpec, seed_lite_training

LITE_FAMILY = "RA-MedFiLM-BARR-Lite"
STAGES = ("G", "R_psi", "B_phi", "S_omega")
UPSTREAM = {"G": (), "R_psi": ("G",), "B_phi": ("G", "R_psi"), "S_omega": ("G", "R_psi", "B_phi")}
EXPECTED_SEEDS = (42, 123, 3407)
REAL_BLOCK = "LITE_REAL_EXECUTION_BLOCKED_PENDING_SEPARATE_AUTHORIZATION"


class LiteChainError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def save_stage_checkpoint(path: Path, *, stage: str, model: nn.Module, spec: LiteVariantSpec, seed: int,
                          upstream_sha256: Mapping[str, str], extra: Mapping[str, Any] | None = None) -> str:
    """Atomically persist one stage and return its file SHA-256."""
    if stage not in STAGES:
        raise LiteChainError(f"unknown stage {stage}")
    if set(upstream_sha256) != set(UPSTREAM[stage]):
        raise LiteChainError(f"{stage} requires upstream hashes exactly {UPSTREAM[stage]}")
    payload = {"family": LITE_FAMILY, "stage": stage, "variant": spec.variant_id,
               "architecture_sha256": spec.sha256(), "seed": int(seed),
               "upstream_sha256": dict(sorted(upstream_sha256.items())),
               "state_dict": model.state_dict(), "extra": dict(extra or {})}
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            torch.save(payload, f)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except Exception:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return sha256_file(path)


def load_stage_checkpoint(path: Path, *, stage: str, model: nn.Module, spec: LiteVariantSpec, seed: int,
                          upstream_paths: Mapping[str, Path]) -> dict[str, Any]:
    """Load only an exact Lite-family checkpoint trained on exactly these upstream files."""
    payload = torch.load(Path(path), map_location="cpu", weights_only=False)
    if not isinstance(payload, dict) or payload.get("family") != LITE_FAMILY:
        raise LiteChainError("not a Lite-family stage checkpoint (FULL weights are never loadable here)")
    if payload.get("stage") != stage or payload.get("variant") != spec.variant_id:
        raise LiteChainError("stage or variant mismatch")
    if payload.get("architecture_sha256") != spec.sha256() or payload.get("seed") != int(seed):
        raise LiteChainError("architecture or seed mismatch")
    if set(upstream_paths) != set(UPSTREAM[stage]):
        raise LiteChainError(f"{stage} requires upstream {UPSTREAM[stage]}")
    expected = {k: sha256_file(p) for k, p in sorted(upstream_paths.items())}
    if payload["upstream_sha256"] != expected:
        raise LiteChainError("upstream dependency hash mismatch (component-family mixing)")
    model.load_state_dict(payload["state_dict"], strict=True)
    return payload


def validate_lite_chain(paths: Mapping[str, Path], spec: LiteVariantSpec, seed: int) -> dict[str, str]:
    """Verify G, R_psi, B_phi, S_omega form one dependency-consistent Lite chain."""
    if set(paths) != set(STAGES):
        raise LiteChainError(f"chain requires all stages {STAGES}")
    digests = {s: sha256_file(paths[s]) for s in STAGES}
    for stage in STAGES:
        payload = torch.load(Path(paths[stage]), map_location="cpu", weights_only=False)
        if payload.get("family") != LITE_FAMILY or payload.get("stage") != stage:
            raise LiteChainError(f"{stage}: not a Lite {stage} checkpoint")
        if payload.get("variant") != spec.variant_id or payload.get("seed") != int(seed):
            raise LiteChainError(f"{stage}: variant/seed mismatch")
        if payload["upstream_sha256"] != {u: digests[u] for u in sorted(UPSTREAM[stage])}:
            raise LiteChainError(f"{stage}: upstream hash chain broken")
    return digests


def bce_dice_loss(logits: torch.Tensor, target: torch.Tensor, eps: float = 1e-6) -> torch.Tensor:
    bce = nn.functional.binary_cross_entropy_with_logits(logits, target)
    p = torch.sigmoid(logits)
    inter = (p * target).sum(dim=(1, 2, 3))
    dice = 1.0 - (2 * inter + eps) / (p.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3)) + eps)
    return 0.5 * bce + 0.5 * dice.mean()


def _dice(logits: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    pred = (torch.sigmoid(logits) >= 0.5).float()
    inter = (pred * target).sum(dim=(1, 2, 3))
    denom = pred.sum(dim=(1, 2, 3)) + target.sum(dim=(1, 2, 3))
    return torch.where(denom > 0, 2 * inter / denom.clamp_min(1.0), torch.ones_like(inter))


def _forward(stage: str, model: nn.Module, batch: Mapping[str, Any], device: torch.device) -> torch.Tensor:
    if stage == "G":
        return model(batch["image"].to(device), batch["task_id"].to(device))
    return model(batch["input"].to(device))


def train_segmentation_stage(
    stage: str, model: nn.Module, spec: LiteVariantSpec, seed: int, out_dir: Path,
    train_loader_factory: Callable[[int], Iterable[Mapping[str, Any]]],
    val_loader: Iterable[Mapping[str, Any]], *, epochs: int, upstream_paths: Mapping[str, Path],
    synthetic: bool, device: str = "cpu", resume: bool = False, lr: float = 1e-4,
    weight_decay: float = 1e-4, patience: int = 15,
) -> dict[str, Any]:
    """Train Lite G or R_psi (BCE+Dice, AdamW, cosine) with best/latest + resume.

    Selection: G maximises equal-domain macro-Dice (``batch['domain']``); R_psi minimises
    validation loss.  Resume restores model, optimiser, scheduler and RNG state.
    """
    if stage not in ("G", "R_psi"):
        raise LiteChainError("segmentation stages are G and R_psi")
    if not synthetic:
        raise LiteChainError(REAL_BLOCK)
    if seed not in EXPECTED_SEEDS or epochs <= 0:
        raise LiteChainError("invalid seed or epochs")
    for name, p in upstream_paths.items():
        if not Path(p).is_file():
            raise LiteChainError(f"missing upstream {name} checkpoint")
    dev = torch.device(device)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    upstream_sha = {k: sha256_file(p) for k, p in upstream_paths.items()}
    seed_lite_training(seed)
    model.to(dev)
    opt = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=weight_decay)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=max(1, epochs))
    latest = out_dir / "latest.pt"
    start, best, bad, history = 1, -math.inf, 0, []
    if resume:
        if not latest.is_file():
            raise LiteChainError("resume requires latest.pt")
        ck = torch.load(latest, map_location="cpu", weights_only=False)
        if (ck["stage"], ck["variant"], ck["seed"], ck["upstream_sha256"]) != (stage, spec.variant_id, seed, upstream_sha):
            raise LiteChainError("resume identity mismatch")
        model.load_state_dict(ck["model_state"])
        opt.load_state_dict(ck["optimizer_state"])
        sched.load_state_dict(ck["scheduler_state"])
        torch.set_rng_state(ck["rng_cpu"])
        start, best, bad, history = ck["epoch"] + 1, ck["best"], ck["bad"], ck["history"]
    for epoch in range(start, epochs + 1):
        model.train()
        losses = []
        for batch in train_loader_factory(epoch):
            opt.zero_grad(set_to_none=True)
            loss = bce_dice_loss(_forward(stage, model, batch, dev), batch["mask"].to(dev))
            loss.backward()
            opt.step()
            losses.append(float(loss.detach()))
        sched.step()
        model.eval()
        per_domain: dict[str, list[float]] = {}
        val_losses = []
        with torch.inference_mode():
            for batch in val_loader:
                logits = _forward(stage, model, batch, dev)
                mask = batch["mask"].to(dev)
                val_losses.append(float(bce_dice_loss(logits, mask)))
                for dom, d in zip(batch["domain"], _dice(logits, mask).cpu().tolist()):
                    per_domain.setdefault(str(dom), []).append(d)
        macro = float(np.mean([np.mean(v) for v in per_domain.values()]))
        score = macro if stage == "G" else -float(np.mean(val_losses))
        history.append({"epoch": epoch, "train_loss": float(np.mean(losses)),
                        "val_loss": float(np.mean(val_losses)), "val_macro_dice": macro})
        if score > best + 1e-12:
            best, bad = score, 0
            save_stage_checkpoint(out_dir / "best.pt", stage=stage, model=model, spec=spec, seed=seed,
                                  upstream_sha256=upstream_sha, extra={"epoch": epoch})
        else:
            bad += 1
        torch.save({"stage": stage, "variant": spec.variant_id, "seed": seed, "upstream_sha256": upstream_sha,
                    "epoch": epoch, "best": best, "bad": bad, "history": history,
                    "model_state": model.state_dict(), "optimizer_state": opt.state_dict(),
                    "scheduler_state": sched.state_dict(), "rng_cpu": torch.get_rng_state()}, latest)
        if bad >= patience:
            break
    (out_dir / "history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")
    return {"stage": stage, "epochs_completed": history[-1]["epoch"], "best_score": best,
            "best_checkpoint_sha256": sha256_file(out_dir / "best.pt"), "run_mode": "SYNTHETIC_ONLY"}


def fit_normalizer(x: np.ndarray, columns: Iterable[int]) -> dict[str, np.ndarray]:
    """Fit-only normaliser (mean/std, constant mask) over selected columns."""
    cols = list(columns)
    sub = x[:, cols].astype(np.float64)
    mu, sigma = sub.mean(0), sub.std(0)
    const = sigma < 1e-12
    return {"columns": np.asarray(cols), "mu": mu, "sigma": np.where(const, 1.0, sigma), "const": const}


def train_head_stage(
    stage: str, model: nn.Module, spec: LiteVariantSpec, seed: int, out_dir: Path, *,
    fit: Mapping[str, np.ndarray], early_stop: Mapping[str, np.ndarray], upstream_paths: Mapping[str, Path],
    synthetic: bool, device: str = "cpu", max_epochs: int = 200, patience: int = 20,
) -> dict[str, Any]:
    """Train Lite B_phi (Huber 0.05 on paired gain) or S_omega (BCE) on supplied OOF tables.

    ``fit``/``early_stop`` hold ``x`` (already normalised with a fit-only normaliser),
    ``task`` (int64) and ``y``.  Labels must come from Lite-R_psi cross-fitted outputs on
    TRAIN only; this function never constructs labels itself.
    """
    if stage not in ("B_phi", "S_omega"):
        raise LiteChainError("head stages are B_phi and S_omega")
    if not synthetic:
        raise LiteChainError(REAL_BLOCK)
    if set(upstream_paths) != set(UPSTREAM[stage]):
        raise LiteChainError(f"{stage} requires upstream {UPSTREAM[stage]}")
    upstream_sha = {k: sha256_file(p) for k, p in upstream_paths.items()}
    seed_lite_training(seed)
    dev = torch.device(device)
    model.to(dev)
    crit = nn.HuberLoss(delta=0.05) if stage == "B_phi" else nn.BCEWithLogitsLoss()
    opt = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, mode="min", factor=0.5, patience=8)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    def run(tables: Mapping[str, np.ndarray]) -> torch.Tensor:
        x = torch.from_numpy(tables["x"]).float().to(dev)
        t = torch.from_numpy(tables["task"]).long().to(dev)
        return model(x, t).reshape(-1) if stage == "B_phi" else model(x).reshape(-1)

    y_fit = torch.from_numpy(fit["y"]).float().to(dev)
    y_es = torch.from_numpy(early_stop["y"]).float().to(dev)
    best, bad, history = math.inf, 0, []
    for epoch in range(1, max_epochs + 1):
        model.train()
        opt.zero_grad(set_to_none=True)
        loss = crit(run(fit), y_fit)
        loss.backward()
        opt.step()
        model.eval()
        with torch.inference_mode():
            es = float(crit(run(early_stop), y_es))
        sched.step(es)
        history.append({"epoch": epoch, "fit_loss": float(loss.detach()), "early_stop_loss": es})
        if es < best - 1e-12:
            best, bad = es, 0
            save_stage_checkpoint(out_dir / "best.pt", stage=stage, model=model, spec=spec, seed=seed,
                                  upstream_sha256=upstream_sha, extra={"epoch": epoch})
        else:
            bad += 1
            if bad >= patience:
                break
    return {"stage": stage, "epochs_completed": history[-1]["epoch"], "best_early_stop_loss": best,
            "best_checkpoint_sha256": sha256_file(out_dir / "best.pt"), "run_mode": "SYNTHETIC_ONLY"}
