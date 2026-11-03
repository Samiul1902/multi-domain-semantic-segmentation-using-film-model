"""R_psi -- per-seed Regional Refiner producer.

Three outer folds over ROUTER_DEVELOPMENT, then one final refit.

Frozen recipe (Phase-24 v1.1 ``refiner`` block, Phase-25A sections 14-21)
------------------------------------------------------------------------
loss      0.5 * BCEWithLogits + 0.5 * soft Dice
optimizer AdamW, lr 1e-4, weight_decay 1e-4
scheduler cosine annealing, T_max = 100
epochs    100, patience 15 (per outer fold)
batch     8
selection minimum EARLY_STOP total loss (Dice is a diagnostic only)
refit     median of the three fold best-epochs, no early stopping

Leakage
-------
Fold ``k``'s ``outer_target`` is NEVER seen during fit or early stopping; it is
reserved for the OOF label producer.  The refit uses all of ROUTER_DEVELOPMENT,
which is legitimate because the refit is the deployed model and its own predictions
are never used as training labels for B_phi or S_omega -- those come from the
fold-specific OOF pass in :mod:`label_stage`.

Data
----
Reads the per-seed crop cache produced by :mod:`cache_stage` through the unchanged
``BARRRefinerCropDataset``.  Samples whose global prediction is empty at the ROI
threshold are FORCED_SKIP and never enter refiner training.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from .. import recipe as R
from ..context import RunContext, StageRecord
from ..provenance import (atomic_torch_save, atomic_write_json, atomic_write_text,
                          build_envelope, load_checkpoint, read_json, sha256_file, utc_now)
from ..seeds import capture_rng, restore_rng, seed_everything
from src.data.barr_refiner_dataset import BARRRefinerCropDataset, barr_refiner_collate
from src.models.barr import (BARR_REFINER_ARCHITECTURE_ID, BARR_REFINER_EXPECTED_PARAMETERS,
                             BARRRegionalRefinerV1, count_parameters)
from src.utils.device import get_device

STAGE = "R"


# --------------------------------------------------------------------------- #
def _write_fold_manifests(ctx: RunContext) -> Dict[int, Dict[str, Path]]:
    """Materialise the fold membership as CSVs the unchanged dataset can read."""
    folds = ctx.folds("outer3")
    dev = ctx.population.development
    lookup = dev.set_index(dev["sample_id"].astype(str))
    out_dir = ctx.cache_dir / "folds"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths: Dict[int, Dict[str, Path]] = {}

    def _write(ids: List[str], path: Path) -> Path:
        rows = []
        for sid in ids:
            if sid not in lookup.index:
                raise RuntimeError(f"fold id {sid} is not in ROUTER_DEVELOPMENT")
            r = lookup.loc[sid]
            rows.append({"sample_id": sid, "dataset": str(r["dataset"]),
                         "task_id": int(r["task_id"]),
                         "group_key": str(r.get("group_key", f"SINGLETON::{r['dataset']}::{sid}"))})
        # always emit the header, even for an empty membership, so the reader gets a
        # well-formed (empty) frame instead of an EmptyDataError
        pd.DataFrame(rows, columns=["sample_id", "dataset", "task_id", "group_key"]
                     ).to_csv(path, index=False)
        return path

    for k, v in folds.folds.items():
        paths[k] = {
            "fit": _write(v["fit"], out_dir / f"fold{k}_fit.csv"),
            "early_stop": _write(v["early_stop"], out_dir / f"fold{k}_early_stop.csv"),
            "outer_target": _write(v["outer_target"], out_dir / f"fold{k}_outer_target.csv"),
        }
    all_ids = sorted({sid for v in folds.folds.values() for sid in
                      (v["fit"] + v["early_stop"] + v["outer_target"])})
    _write(all_ids, out_dir / "final_all_development.csv")
    return paths


def _loader(ds, batch_size: int, shuffle: bool, seed: int) -> DataLoader:
    gen = torch.Generator()
    gen.manual_seed(int(seed))
    return DataLoader(ds, batch_size=batch_size, shuffle=shuffle, num_workers=0,
                      pin_memory=True, drop_last=False, generator=gen,
                      collate_fn=barr_refiner_collate)


def _dice_from_logits(logits: torch.Tensor, targets: torch.Tensor,
                      threshold: float = 0.5, eps: float = 1e-6) -> float:
    pred = torch.sigmoid(logits).ge(threshold)
    tgt = targets.bool()
    dims = tuple(range(1, tgt.ndim))
    tp = (pred & tgt).sum(dims).float()
    fp = (pred & ~tgt).sum(dims).float()
    fn = (~pred & tgt).sum(dims).float()
    return float(((2 * tp + eps) / (2 * tp + fp + fn + eps)).mean().item())


def _build_model(ctx: RunContext) -> BARRRegionalRefinerV1:
    model = BARRRegionalRefinerV1()
    n = count_parameters(model)
    if n != BARR_REFINER_EXPECTED_PARAMETERS:
        raise RuntimeError(f"R_psi parameter count {n} != {BARR_REFINER_EXPECTED_PARAMETERS}")
    return model


def _train_one(ctx: RunContext, *, run_id: str, ckpt_dir: Path, exp_dir: Path,
               fit_csv: Path, es_csv: Path | None, seed: int, epochs_target: int,
               early_stopping: bool, resume: bool, log, model_factory=None,
               architecture_id: str | None = None) -> dict:
    device = get_device(require_cuda=(ctx.bounds.device == "cuda"))
    amp = bool(ctx.bounds.amp) and device.type == "cuda"
    b = ctx.bounds

    ckpt_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)
    hist_path = exp_dir / "history.csv"
    best_path = ckpt_dir / "best.pt"
    latest_path = ckpt_dir / "latest.pt"

    ds_train = BARRRefinerCropDataset(fit_csv, cache_root=ctx.cache_dir, train=True,
                                      base_seed=seed, epoch=0)
    if len(ds_train) == 0:
        raise RuntimeError(f"[R/{ctx.tag}/{run_id}] empty FIT population")
    ds_es = (BARRRefinerCropDataset(es_csv, cache_root=ctx.cache_dir, train=False,
                                    base_seed=seed, epoch=0) if early_stopping else None)
    if early_stopping and (ds_es is None or len(ds_es) == 0):
        raise RuntimeError(f"[R/{ctx.tag}/{run_id}] empty EARLY_STOP population")

    model = (model_factory or _build_model)(ctx).to(device)
    bce = torch.nn.BCEWithLogitsLoss()
    from src.losses.segmentation import DiceLoss
    dice_loss = DiceLoss(R.R_LOSS["dice_epsilon"])
    optimizer = torch.optim.AdamW(model.parameters(), lr=R.R_OPTIMIZER["learning_rate"],
                                  weight_decay=R.R_OPTIMIZER["weight_decay"])
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=R.R_SCHEDULER["T_max"])
    scaler = torch.amp.GradScaler("cuda", enabled=amp)

    history: List[dict] = []
    start_epoch = 0
    best_loss, best_epoch, bad_epochs, resume_count = float("inf"), -1, 0, 0

    if resume and latest_path.exists():
        ck = load_checkpoint(latest_path, map_location="cpu", component="R", seed=ctx.seed)
        model.load_state_dict(ck["model_state"])
        optimizer.load_state_dict(ck["optimizer_state"])
        scheduler.load_state_dict(ck["scheduler_state"])
        if ck.get("grad_scaler_state"):
            scaler.load_state_dict(ck["grad_scaler_state"])
        if ck.get("rng"):
            restore_rng(ck["rng"])
        start_epoch = int(ck["epoch"]) + 1
        best_loss = float(ck["selection"]["best_loss"])
        best_epoch = int(ck["selection"]["best_epoch"])
        bad_epochs = int(ck["selection"]["bad_epochs"])
        resume_count = int(ck["selection"].get("resume_count", 0)) + 1
        history = list(ck.get("history") or [])
        log(f"[R/{ctx.tag}/{run_id}] resume from epoch {start_epoch} (best={best_epoch})")

    upstream = ctx.upstream_for("R")
    t0 = time.time()
    stop_reason = ""
    for epoch in range(start_epoch, epochs_target):
        t_ep = time.time()
        ds_train.set_epoch(epoch)
        train_loader = _loader(ds_train, b.r_batch_size, True, seed + epoch)
        model.train()
        run_loss = run_bce = run_dl = 0.0
        n_seen = 0
        nonfinite = 0
        for batch in train_loader:
            inputs = batch["input"].to(device, non_blocking=True)
            targets = batch["target"].to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.amp.autocast(device_type=device.type, enabled=amp):
                logits = model(inputs)
                lb = bce(logits.float(), targets)
                ld = dice_loss(logits.float(), targets)
                loss = 0.5 * lb + 0.5 * ld
            if not torch.isfinite(loss):
                raise RuntimeError(f"[R/{ctx.tag}/{run_id}] non-finite loss at epoch {epoch}")
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            gn = torch.nn.utils.clip_grad_norm_(model.parameters(), float("inf"))
            if not torch.isfinite(gn):
                nonfinite += 1
            scaler.step(optimizer)
            scaler.update()
            bs = inputs.shape[0]
            run_loss += float(loss.item()) * bs
            run_bce += float(lb.item()) * bs
            run_dl += float(ld.item()) * bs
            n_seen += bs
        train_loss = run_loss / max(n_seen, 1)
        lr_now = float(optimizer.param_groups[0]["lr"])
        scheduler.step()

        es_loss, es_dice, is_best = float("nan"), float("nan"), False
        if early_stopping:
            model.eval()
            es_loader = _loader(ds_es, b.r_batch_size, False, seed)
            tot, n_es, dices = 0.0, 0, []
            with torch.no_grad():
                for batch in es_loader:
                    inputs = batch["input"].to(device, non_blocking=True)
                    targets = batch["target"].to(device, non_blocking=True)
                    with torch.amp.autocast(device_type=device.type, enabled=amp):
                        logits = model(inputs)
                        l = 0.5 * bce(logits.float(), targets) + 0.5 * dice_loss(
                            logits.float(), targets)
                    tot += float(l.item()) * inputs.shape[0]
                    n_es += inputs.shape[0]
                    dices.append(_dice_from_logits(logits.float(), targets))
            es_loss = tot / max(n_es, 1)
            es_dice = float(np.mean(dices)) if dices else float("nan")
            if es_loss < best_loss - 1e-12:
                best_loss, best_epoch, bad_epochs, is_best = es_loss, epoch, 0, True
            else:
                bad_epochs += 1

        row = {"run": run_id, "epoch": epoch, "train_loss": train_loss,
               "train_BCE": run_bce / max(n_seen, 1), "train_Dice_loss": run_dl / max(n_seen, 1),
               "early_stop_loss": es_loss, "early_stop_Dice": es_dice,
               "learning_rate": lr_now, "elapsed_seconds": round(time.time() - t_ep, 3),
               "amp": bool(amp), "checkpoint_event": bool(is_best),
               "best_epoch_so_far": best_epoch,
               "best_early_stop_loss_so_far": best_loss if early_stopping else "",
               "nonfinite_gradient_batches": nonfinite, "resume_count": resume_count}
        history.append(row)
        atomic_write_text(pd.DataFrame(history).to_csv(index=False), hist_path)

        env = build_envelope(
            component="R", seed=ctx.seed, run_id=run_id,
            architecture_id=architecture_id or BARR_REFINER_ARCHITECTURE_ID,
            model_state=model.state_dict(), upstream=upstream, epoch=epoch,
            best_epoch=best_epoch,
            selection={"rule": R.R_SELECTION, "best_loss": best_loss,
                       "best_epoch": best_epoch, "bad_epochs": bad_epochs,
                       "resume_count": resume_count},
            recipe={"r": ctx.recipe.r, "thresholds": ctx.recipe.thresholds},
            history=history, optimizer_state=optimizer.state_dict(),
            scheduler_state=scheduler.state_dict(), rng_state=capture_rng(),
            family=ctx.family_name,
            extra={"grad_scaler_state": scaler.state_dict(),
                   "operational_override": ctx.bounds.overrides(),
                   "cache_manifest_sha256": sha256_file(ctx.cache_dir / "manifest.json"),
                   "fit_manifest_sha256": sha256_file(fit_csv),
                   "early_stop_manifest_sha256": (sha256_file(es_csv) if es_csv else None),
                   "n_fit": len(ds_train),
                   "n_early_stop": len(ds_es) if ds_es is not None else 0},
        )
        atomic_torch_save(env, latest_path)
        if is_best:
            atomic_torch_save(env, best_path)

        if early_stopping and bad_epochs >= R.R_PATIENCE:
            stop_reason = f"early_stopping_patience_{R.R_PATIENCE}"
            break
    else:
        stop_reason = "max_epochs_reached"

    if not best_path.exists() and early_stopping:
        raise RuntimeError(f"[R/{ctx.tag}/{run_id}] no best checkpoint written")
    record = {"run": run_id, "seed": ctx.seed, "tag": ctx.tag,
              "epochs_completed": len(history), "epochs_target": epochs_target,
              "best_epoch": best_epoch,
              "best_early_stop_loss": best_loss if early_stopping else None,
              "stop_reason": stop_reason, "resume_count": resume_count,
              "n_fit": len(ds_train),
              "n_early_stop": len(ds_es) if ds_es is not None else 0,
              "parameter_count": count_parameters(model),
              "history_sha256": sha256_file(hist_path),
              "best_checkpoint_sha256": (sha256_file(best_path) if best_path.exists() else None),
              "latest_checkpoint_sha256": sha256_file(latest_path),
              "upstream": {k: v["sha256"] for k, v in upstream.items()},
              "elapsed_seconds": round(time.time() - t0, 3),
              "completed_utc": utc_now()}
    atomic_write_json(record, exp_dir / "run.json")
    return record


# --------------------------------------------------------------------------- #
def run(ctx: RunContext, *, resume: bool = False, log=print,
        model_factory=None, architecture_id: Optional[str] = None,
        expected_parameters: Optional[int] = None) -> StageRecord:
    """Produce R_psi: three outer folds plus a median-epoch refit.

    ``model_factory`` / ``architecture_id`` / ``expected_parameters`` are the
    injection points a different refiner family (Lite) uses to reuse this
    producer.  All default to the frozen FULL values.
    """
    base_factory = model_factory or _build_model
    if expected_parameters is None:
        factory = base_factory
    else:
        frozen_expected = int(expected_parameters)

        def factory(ctx, _base=base_factory, _expected=frozen_expected):
            model = _base(ctx)
            n = count_parameters(model)
            if n != _expected:
                raise RuntimeError(
                    f"R_psi parameter count {n} != expected {_expected}")
            return model

    seed_everything(ctx.family.run_seed("R", "main"))
    _write_fold_manifests(ctx)
    log(f"[R/{ctx.tag}] fold manifests written to {ctx.cache_dir / 'folds'}")

    fold_records = {}
    for k in R.R_OUTER_FOLDS:
        fold_seed = ctx.family.run_seed("R", f"fold{k}")
        seed_everything(fold_seed)
        rec = _train_one(ctx, run_id=f"{ctx.tag}/R/fold{k}", ckpt_dir=ctx.r_dir / f"fold{k}",
                         exp_dir=ctx.r_dir / f"fold{k}", fit_csv=ctx.cache_dir / "folds" / f"fold{k}_fit.csv",
                         es_csv=ctx.cache_dir / "folds" / f"fold{k}_early_stop.csv",
                         seed=fold_seed, epochs_target=int(ctx.bounds.r_max_epochs),
                         early_stopping=True, resume=resume, log=log,
                         model_factory=factory, architecture_id=architecture_id)
        fold_records[k] = rec
        log(f"[R/{ctx.tag}] fold{k} best_epoch={rec['best_epoch']} stop={rec['stop_reason']}")

    best_epochs = sorted(int(r["best_epoch"]) for r in fold_records.values() if r["best_epoch"] >= 0)
    if not best_epochs:
        raise RuntimeError(f"[R/{ctx.tag}] no fold produced a best epoch")
    refit_epochs = best_epochs[len(best_epochs) // 2]
    # a reduced run must still fit at least one epoch
    refit_epochs = max(1, min(refit_epochs, int(ctx.bounds.r_max_epochs)))
    log(f"[R/{ctx.tag}] final refit epochs={refit_epochs} (median of {best_epochs})")

    final_seed = ctx.family.run_seed("R", "final")
    seed_everything(final_seed)
    final_rec = _train_one(ctx, run_id=f"{ctx.tag}/R/final", ckpt_dir=ctx.r_dir / "final",
                           exp_dir=ctx.r_dir / "final",
                           fit_csv=ctx.cache_dir / "folds" / "final_all_development.csv",
                           es_csv=None, seed=final_seed, epochs_target=refit_epochs,
                           early_stopping=False, resume=resume, log=log,
                           model_factory=factory, architecture_id=architecture_id)
    # the deployed refiner is the refit; expose it under the canonical name
    refit_latest = ctx.r_dir / "final" / "latest.pt"
    if not refit_latest.exists():
        raise RuntimeError(f"[R/{ctx.tag}] final refit produced no checkpoint")
    import os
    from ..provenance import atomic_write_bytes
    atomic_write_bytes(refit_latest.read_bytes(), ctx.r_dir / "final" / "final.pt")

    record = {"artifact": f"{ctx.family_name.lower()}_barr_stage_R", "stage": STAGE,
              "seed": ctx.seed,
              "tag": ctx.tag, "folds": fold_records, "final": final_rec,
              "refit_epochs": refit_epochs, "fold_best_epochs": best_epochs,
              "final_checkpoint_sha256": sha256_file(ctx.r_dir / "final" / "final.pt"),
              "test_reads": 0, "router_holdout_reads": 0, "completed_utc": utc_now()}
    atomic_write_json(record, ctx.r_dir / "run.json")
    return StageRecord(stage=STAGE, status="COMPLETE",
                       artifacts={"run": str(ctx.r_dir / "run.json"),
                                  "final": str(ctx.r_dir / "final" / "final.pt")},
                       detail=record)


def is_complete(ctx: RunContext) -> bool:
    rec = read_json(ctx.r_dir / "run.json")
    final = ctx.r_dir / "final" / "final.pt"
    if not final.exists():
        return False
    return rec.get("final_checkpoint_sha256") == sha256_file(final)


def verify(ctx: RunContext) -> dict:
    final = ctx.r_dir / "final" / "final.pt"
    ck = load_checkpoint(final, component="R", seed=ctx.seed)
    return {"component": "R", "seed": ctx.seed, "sha256": sha256_file(final),
            "upstream": {k: v["sha256"] for k, v in ck["upstream"].items()},
            "verdict": "R_FAMILY_VERIFIED"}
