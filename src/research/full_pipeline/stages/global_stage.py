"""G -- per-seed GlobalMedFiLM producer.

One shared network, four domains, task-conditioned FiLM at five sites, one shared
foreground head.  ``task_id`` is the ONLY task signal.

Inherited from ``scripts/training/train_phase21_global_medfilm.py`` and
``scripts/training/phase21_common.py``.  The differences are strictly mechanical:

* the seed is the family seed instead of the literal 42;
* the checkpoint is written through the family envelope (atomic, provenance
  stamped) instead of a bare ``state_dict`` bundle;
* the trainer is a callable used by the orchestrator instead of a ``__main__``
  script, so three families can be produced by one process.

Nothing scientific changes: same model, same loss, same optimiser, same schedule,
same sampler, same per-epoch derived seed, same macro-domain-Dice selection with
the validation-loss tie-break, same early-stopping patience.

Resume is bit-exact BY CONSTRUCTION: epoch ``k``'s data order and every stochastic
augmentation derive from ``derive_epoch_seed(seed, k)``, and the full RNG state is
captured in every checkpoint and restored on resume.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
import torch

from .. import recipe as R
from ..context import RunContext, StageRecord
from ..provenance import (atomic_torch_save, atomic_write_json, atomic_write_text,
                          build_envelope, load_checkpoint, sha256_file, utc_now)
from ..seeds import capture_rng, restore_rng, seed_everything
from src.data.domain_balanced_sampler import (BALANCED_SAMPLING_POLICY_ID,
                                              build_domain_balanced_sampler,
                                              derive_epoch_seed)
from src.data.loaders import create_loader
from src.data.multidomain_dataset import (DATASET_ORDER, MultiDomainDataset,
                                          harmonized_collate)
from src.losses.segmentation import BCEDiceLoss
from src.models.film import GlobalMedFiLM
from src.training.phase20_selection import (SELECTION_RULE_ID, is_new_best,
                                            macro_domain_dice)
from src.utils.device import get_device

STAGE = "G"
HISTORY_COLUMNS = (
    ["epoch", "train_loss", "val_loss", "macro_domain_dice"]
    + [f"val_dice_{d}" for d in DATASET_ORDER]
    + [f"val_iou_{d}" for d in DATASET_ORDER]
    + [f"val_precision_{d}" for d in DATASET_ORDER]
    + [f"val_recall_{d}" for d in DATASET_ORDER]
    + ["learning_rate", "is_new_best", "best_epoch_so_far", "best_so_far",
       "bad_epochs", "epoch_seconds", "cumulative_seconds"]
)


# --------------------------------------------------------------------------- #
def build_model(ctx: RunContext) -> GlobalMedFiLM:
    m = R.G_MODEL
    model = GlobalMedFiLM(
        task_count=m["task_count"], in_channels=m["in_channels"],
        out_channels=m["out_channels"], channels=tuple(m["channels"]),
        task_embedding_dim=m["task_embedding_dim"], film_hidden_dim=m["film_hidden_dim"],
    )
    if not getattr(model, "medfilm_components_present", False):
        raise RuntimeError("GlobalMedFiLM reports no FiLM components")
    forbidden = ("localizer", "proposal", "roi", "regional", "refiner", "router")
    bad = [n for n, _ in model.named_modules() if any(k in n.lower() for k in forbidden)]
    if bad:
        raise RuntimeError(f"G must not contain regional/routing modules: {bad[:5]}")
    return model


@torch.no_grad()
def validate(model, loader, criterion, device, threshold: float, amp: bool):
    """Deterministic VAL pass; identical arithmetic to the Phase-21 validator."""
    from src.training.phase20_selection import DOMAIN_ORDER

    model.eval()
    losses = []
    acc = {d: {k: [] for k in ("dice", "iou", "precision", "recall")} for d in DATASET_ORDER}
    for batch in loader:
        images = batch["image"].to(device, non_blocking=True)
        masks = batch["mask"].to(device, non_blocking=True)
        task_ids = batch["task_id"].to(device, non_blocking=True)
        datasets = batch["dataset"]
        with torch.amp.autocast(device_type=device.type, enabled=amp):
            logits = model(images, task_ids)
            loss = criterion(logits, masks)
        losses.append(float(loss.item()))
        preds = torch.sigmoid(logits).ge(threshold)
        tgts = masks.bool()
        dims = tuple(range(1, tgts.ndim))
        tp = (preds & tgts).sum(dims).float()
        fp = (preds & ~tgts).sum(dims).float()
        fn = (~preds & tgts).sum(dims).float()
        eps = 1e-7
        metrics = {
            "dice": (2 * tp + eps) / (2 * tp + fp + fn + eps),
            "iou": (tp + eps) / (tp + fp + fn + eps),
            "precision": (tp + eps) / (tp + fp + eps),
            "recall": (tp + eps) / (tp + fn + eps),
        }
        for key, tensor in metrics.items():
            values = tensor.detach().cpu().numpy()
            for i, ds in enumerate(datasets):
                acc[str(ds)][key].append(float(values[i]))
    out = {d: {k: float(np.mean(v)) if v else float("nan") for k, v in acc[d].items()}
           for d in DATASET_ORDER}
    # a domain with no VAL rows would make macro Dice undefined; fail loudly
    empty = [d for d in DOMAIN_ORDER if not acc[d]["dice"]]
    if empty:
        raise RuntimeError(f"VAL has no samples for domain(s) {empty}")
    return float(np.mean(losses)), out


# --------------------------------------------------------------------------- #
def _make_datasets(ctx: RunContext) -> tuple:
    ds_train = MultiDomainDataset(ctx.population.train_manifest, "TRAIN",
                                  size=R.G_INPUT_RESOLUTION, train=True,
                                  channel_policy=R.G_INPUT_CHANNEL_POLICY)
    ds_val = MultiDomainDataset(ctx.population.val_manifest, "VAL",
                                size=R.G_INPUT_RESOLUTION, train=False,
                                channel_policy=R.G_INPUT_CHANNEL_POLICY)
    return ds_train, ds_val


def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    b = ctx.bounds
    device = get_device(require_cuda=(b.device == "cuda"))
    amp = bool(b.g_amp) and device.type == "cuda"

    ctx.g_dir.mkdir(parents=True, exist_ok=True)
    hist_path = ctx.g_dir / "history.csv"
    best_path = ctx.g_dir / "best.pt"
    latest_path = ctx.g_dir / "latest.pt"

    seed = ctx.family.run_seed("G", "main")
    seed_everything(seed)
    log(f"[G/{ctx.tag}] seed={seed} device={device} amp={amp}")

    ds_train, ds_val = _make_datasets(ctx)
    log(f"[G/{ctx.tag}] TRAIN={len(ds_train)} VAL={len(ds_val)}")

    model = build_model(ctx).to(device)
    n_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    if n_params != R.G_EXPECTED_PARAMETERS:
        raise RuntimeError(
            f"G parameter count {n_params} != frozen {R.G_EXPECTED_PARAMETERS}")

    criterion = BCEDiceLoss(R.G_LOSS["bce_weight"], R.G_LOSS["dice_weight"],
                            R.G_LOSS["dice_epsilon"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=R.G_OPTIMIZER["learning_rate"],
                                  weight_decay=R.G_OPTIMIZER["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=R.G_SCHEDULER["T_max"])
    scaler = torch.amp.GradScaler("cuda", enabled=amp)
    threshold = R.G_TRAINING["threshold"]
    patience = R.G_TRAINING["early_stopping_patience"]

    best_macro, best_epoch, best_val_loss, bad_epochs = float("-inf"), 0, float("inf"), 0
    history: list = []
    start_epoch = 1
    resume_count = 0
    prior_cumulative = 0.0

    if resume and latest_path.exists():
        ck = load_checkpoint(latest_path, map_location=device, component="G", seed=ctx.seed)
        model.load_state_dict(ck["model_state"])
        optimizer.load_state_dict(ck["optimizer_state"])
        scheduler.load_state_dict(ck["scheduler_state"])
        if ck.get("grad_scaler_state"):
            scaler.load_state_dict(ck["grad_scaler_state"])
        best_macro = float(ck["selection"]["best_macro_domain_dice"])
        best_epoch = int(ck["selection"]["best_epoch"])
        best_val_loss = float(ck["selection"]["best_val_loss"])
        bad_epochs = int(ck["selection"]["bad_epochs"])
        start_epoch = int(ck["epoch"]) + 1
        resume_count = int(ck["selection"].get("resume_count", 0)) + 1
        history = list(ck.get("history") or [])
        if ck.get("rng"):
            restore_rng(ck["rng"])
        prior_cumulative = float(history[-1]["cumulative_seconds"]) if history else 0.0
        log(f"[G/{ctx.tag}] resume from epoch {ck['epoch']} -> {start_epoch} "
            f"(best_epoch={best_epoch} macro={best_macro:.6f})")

    max_epochs = int(b.g_max_epochs)
    t_run = time.time()
    stop_reason = None

    for epoch in range(start_epoch, max_epochs + 1):
        t0 = time.perf_counter()
        ep_seed = derive_epoch_seed(seed, epoch)
        torch.manual_seed(ep_seed)
        np.random.seed(ep_seed)
        import random as _random
        _random.seed(ep_seed)

        sampler = build_domain_balanced_sampler(ds_train.frame["dataset"].tolist(), seed, epoch)
        loader_train = create_loader(ds_train, batch_size=b.g_batch_size, shuffle=False,
                                     seed=ep_seed, num_workers=b.g_num_workers,
                                     persistent_workers=R.G_TRAINING["persistent_workers"],
                                     collate_fn=harmonized_collate, sampler=sampler)
        loader_val = create_loader(ds_val, batch_size=b.g_eval_batch_size, shuffle=False,
                                   seed=seed, num_workers=0,
                                   collate_fn=harmonized_collate)

        model.train()
        optimizer.zero_grad(set_to_none=True)
        losses = []
        for batch in loader_train:
            images = batch["image"].to(device, non_blocking=True)
            masks = batch["mask"].to(device, non_blocking=True)
            task_ids = batch["task_id"].to(device, non_blocking=True)
            with torch.amp.autocast(device_type=device.type, enabled=amp):
                logits = model(images, task_ids)
                loss = criterion(logits, masks)
            if not torch.isfinite(loss):
                raise RuntimeError(f"[G/{ctx.tag}] non-finite loss at epoch {epoch}")
            scaler.scale(loss).backward()
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad(set_to_none=True)
            losses.append(float(loss.item()))
        train_loss = float(np.mean(losses)) if losses else float("nan")

        val_loss, per_domain = validate(model, loader_val, criterion, device, threshold, amp)
        scheduler.step()
        elapsed = time.perf_counter() - t0

        macro = macro_domain_dice({d: per_domain[d]["dice"] for d in DATASET_ORDER})
        new_best = is_new_best(macro, val_loss, best_macro, best_val_loss)
        if new_best:
            best_macro, best_epoch, best_val_loss, bad_epochs = macro, epoch, val_loss, 0
        else:
            bad_epochs += 1

        row = {
            "epoch": epoch, "train_loss": train_loss, "val_loss": val_loss,
            "macro_domain_dice": macro,
            **{f"val_dice_{d}": per_domain[d]["dice"] for d in DATASET_ORDER},
            **{f"val_iou_{d}": per_domain[d]["iou"] for d in DATASET_ORDER},
            **{f"val_precision_{d}": per_domain[d]["precision"] for d in DATASET_ORDER},
            **{f"val_recall_{d}": per_domain[d]["recall"] for d in DATASET_ORDER},
            "learning_rate": optimizer.param_groups[0]["lr"],
            "is_new_best": bool(new_best),
            "best_epoch_so_far": best_epoch,
            "best_so_far": best_macro,
            "bad_epochs": bad_epochs,
            "epoch_seconds": elapsed,
            "cumulative_seconds": prior_cumulative + time.time() - t_run,
        }
        history.append(row)
        # history is persisted BEFORE the checkpoint so a checkpoint always carries
        # a history covering epochs 1..epoch (no gap on resume)
        atomic_write_text(pd.DataFrame(history).to_csv(index=False), hist_path)

        env = build_envelope(
            component="G", seed=ctx.seed, run_id=f"{ctx.tag}/G", architecture_id=R.G_ARCHITECTURE_ID,
            model_state=model.state_dict(), upstream={}, epoch=epoch, best_epoch=best_epoch,
            selection={"rule": SELECTION_RULE_ID, "best_macro_domain_dice": best_macro,
                       "best_epoch": best_epoch, "best_val_loss": best_val_loss,
                       "bad_epochs": bad_epochs, "resume_count": resume_count},
            recipe={"g": ctx.recipe.g, "thresholds": ctx.recipe.thresholds},
            history=history, optimizer_state=optimizer.state_dict(),
            scheduler_state=scheduler.state_dict(), rng_state=capture_rng(),
            extra={"grad_scaler_state": scaler.state_dict(),
                   "operational_override": ctx.bounds.overrides(),
                   "dataset_populations": {
                       "TRAIN": len(ds_train), "VAL": len(ds_val),
                       "train_manifest_sha256": sha256_file(ctx.population.train_manifest),
                       "val_manifest_sha256": sha256_file(ctx.population.val_manifest)},
                   "sampling_policy": BALANCED_SAMPLING_POLICY_ID},
        )
        atomic_torch_save(env, latest_path)
        if new_best:
            atomic_torch_save(env, best_path)

        log(f"[G/{ctx.tag}] epoch {epoch:03d} train={train_loss:.4f} val={val_loss:.4f} "
            f"macro={macro:.6f} best_ep={best_epoch} bad={bad_epochs} {elapsed:.1f}s")

        if bad_epochs >= patience:
            stop_reason = "EARLY_STOPPING_PATIENCE"
            break
    stop_reason = stop_reason or "MAX_EPOCHS"

    if not best_path.exists():
        raise RuntimeError(f"[G/{ctx.tag}] no best checkpoint was written")

    record = {
        "artifact": "full_barr_stage_G",
        "stage": STAGE, "seed": ctx.seed, "tag": ctx.tag,
        "best_epoch": best_epoch, "best_macro_domain_dice": best_macro,
        "best_val_loss": best_val_loss, "epochs_completed": len(history),
        "stop_reason": stop_reason, "resume_count": resume_count,
        "parameter_count": n_params,
        "best_checkpoint_sha256": sha256_file(best_path),
        "latest_checkpoint_sha256": sha256_file(latest_path),
        "history_sha256": sha256_file(hist_path),
        "train_n": len(ds_train), "val_n": len(ds_val),
        "operational_override": ctx.bounds.overrides(),
        "test_reads": 0, "router_holdout_reads": 0,
        "completed_utc": utc_now(),
    }
    atomic_write_json(record, ctx.g_dir / "closure.json")
    return StageRecord(stage=STAGE, status="COMPLETE",
                       artifacts={"best": str(best_path), "latest": str(latest_path),
                                  "history": str(hist_path),
                                  "closure": str(ctx.g_dir / "closure.json")},
                       detail=record)


def is_complete(ctx: RunContext) -> bool:
    best = ctx.g_dir / "best.pt"
    closure = ctx.g_dir / "closure.json"
    if not (best.exists() and closure.exists()):
        return False
    from ..provenance import read_json
    rec = read_json(closure)
    return rec.get("best_checkpoint_sha256") == sha256_file(best)


def verify(ctx: RunContext) -> dict:
    best = ctx.g_dir / "best.pt"
    ck = load_checkpoint(best, component="G", seed=ctx.seed)
    return {"component": "G", "seed": ctx.seed,
            "sha256": sha256_file(best),
            "parameter_count": sum(v.numel() for v in ck["model_state"].values()
                                   if v.dtype.is_floating_point),
            "best_epoch": ck["best_epoch"],
            "upstream": {},
            "verdict": "G_FAMILY_VERIFIED"}
