"""S_omega -- per-seed Post-Refinement Safety producer.

5-fold cross-fit over ROUTER_DEVELOPMENT, then one final refit.

Frozen recipe (Phase-25F v1.0)
------------------------------
architecture Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)
input        indices 0..15  sixteen numeric post-refinement features
             indices 16..19 four fixed one-hot task indicators
loss         BCEWithLogitsLoss(reduction="mean")
optimizer    AdamW, lr 1e-3, weight_decay 1e-4
scheduler    ReduceLROnPlateau(min, factor 0.5, patience 8, threshold 1e-4 rel,
             min_lr 1e-6, eps 1e-8)
batch        128, max 200 epochs, patience 20
selection    minimum EARLY_STOP mean BCE (strict 1e-12 improvement, tie keeps earlier)
refit        median of the five fold best-epochs
accept       sigmoid(logit) >= 0.50

Labels
------
``safety_target = 1`` iff the OOF refinement gain for that sample is strictly
positive.  Both the target and the features come from the SAME seed family's OOF
pass, so no sample is described by a prediction that saw it.

Normalisation is FIT-only with ``ddof = 0``; a zero-sigma column is mapped to 0
instead of dividing by zero.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

from .. import recipe as R
from ..context import RunContext, StageRecord
from ..provenance import (atomic_torch_save, atomic_write_json, atomic_write_text,
                          build_envelope, load_checkpoint, read_json, relpath_str,
                          sha256_file, utc_now)
from ..seeds import capture_rng, restore_rng, seed_everything
from src.utils.device import get_device

STAGE = "S"


# --------------------------------------------------------------------------- #
# S_omega is the single frozen Phase-25F definition, imported rather than copied.
# See src/models/barr/phase25_models.py and tests/test_phase25_architecture_drift.py.
from src.models.barr.phase25_models import BARRPostSafetyV1  # noqa: E402


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def fit_normalization(fit_features: np.ndarray):
    num = fit_features[:, :R.S_NUMERIC_DIM].astype(np.float64)
    mu = num.mean(axis=0)
    sigma = num.std(axis=0, ddof=0)
    const = sigma < 1e-12
    return mu, sigma, const


def apply_normalization(features: np.ndarray, mu, sigma, const) -> np.ndarray:
    out = features.astype(np.float32).copy()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (features[:, :R.S_NUMERIC_DIM].astype(np.float64) - mu) / sigma_safe
    norm[:, const] = 0.0
    out[:, :R.S_NUMERIC_DIM] = norm.astype(np.float32)
    return out


def build_matrix(features: np.ndarray, task_ids: np.ndarray) -> np.ndarray:
    """16 numeric columns + 4 one-hot task columns."""
    onehot = np.zeros((len(task_ids), R.S_ONEHOT_DIM), dtype=np.float32)
    onehot[np.arange(len(task_ids)), task_ids.astype(int)] = 1.0
    return np.concatenate([features.astype(np.float32), onehot], axis=1)


# --------------------------------------------------------------------------- #
def load_family_inputs(ctx: RunContext) -> tuple:
    m = read_json(ctx.l_dir / "manifest.json")
    if not m.get("safety_features_sha256"):
        raise RuntimeError(f"[S/{ctx.tag}] label stage produced no safety features")
    feats = np.load(ctx.l_dir / "safety_features.npy").astype(np.float32)
    meta = pd.read_csv(ctx.l_dir / "safety_features_meta.csv")
    meta["sample_id"] = meta["sample_id"].astype(str)
    if feats.shape != (len(meta), R.S_NUMERIC_DIM):
        raise RuntimeError(f"safety feature matrix {feats.shape} != "
                           f"({len(meta)}, {R.S_NUMERIC_DIM})")
    if not np.isfinite(feats).all():
        raise RuntimeError("safety feature matrix contains non-finite values")

    cv = ctx.folds("cv5")
    fold_of: Dict[str, int] = {}
    for k, v in cv.folds.items():
        for sid in v["outer_target"]:
            fold_of[sid] = k
    meta["cv_fold"] = meta["sample_id"].map(fold_of)
    if meta["cv_fold"].isna().any():
        raise RuntimeError("some safety rows have no 5-fold CV assignment")

    X = build_matrix(feats, meta["task_id"].to_numpy())
    y = meta["safety_target"].to_numpy(dtype=np.float32)
    return meta, X, y


def _train_one(ctx: RunContext, *, run_id: str, ckpt_dir: Path, exp_dir: Path, seed: int,
               fit_idx, es_idx, ot_idx, X: np.ndarray, y: np.ndarray,
               epochs_target: int, early_stopping: bool, resume: bool, log) -> dict:
    device = get_device(require_cuda=(ctx.bounds.device == "cuda"))
    b = ctx.bounds
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)
    hist_path = exp_dir / "history.csv"
    best_path = ckpt_dir / "best.pt"
    latest_path = ckpt_dir / "latest.pt"

    mu, sigma, const = fit_normalization(X[fit_idx])
    fit_x = apply_normalization(X[fit_idx], mu, sigma, const)
    es_x = apply_normalization(X[es_idx], mu, sigma, const)
    ot_x = apply_normalization(X[ot_idx], mu, sigma, const)

    seed_everything(seed)
    gen = torch.Generator()
    gen.manual_seed(seed)
    model = BARRPostSafetyV1().to(device)
    n = count_params(model)
    if n != R.S_EXPECTED_PARAMETERS:
        raise RuntimeError(f"S_omega parameter count {n} != {R.S_EXPECTED_PARAMETERS}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=R.S_OPTIMIZER["learning_rate"],
                                  weight_decay=R.S_OPTIMIZER["weight_decay"])
    sc = R.S_SCHEDULER
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode=sc["mode"], factor=sc["factor"], patience=sc["patience"],
        threshold=sc["threshold"], threshold_mode=sc["threshold_mode"],
        cooldown=sc["cooldown"], min_lr=sc["min_lr"], eps=sc["eps"])
    criterion = nn.BCEWithLogitsLoss(reduction="mean")

    history: List[dict] = []
    start_epoch, best_loss, best_epoch, bad_epochs, resume_count = 1, float("inf"), -1, 0, 0
    if resume and latest_path.exists():
        ck = load_checkpoint(latest_path, map_location="cpu", component="S", seed=ctx.seed)
        model.load_state_dict(ck["model_state"])
        optimizer.load_state_dict(ck["optimizer_state"])
        scheduler.load_state_dict(ck["scheduler_state"])
        if ck.get("rng"):
            restore_rng(ck["rng"])
        start_epoch = int(ck["epoch"]) + 1
        best_loss = float(ck["selection"]["best_loss"])
        best_epoch = int(ck["selection"]["best_epoch"])
        bad_epochs = int(ck["selection"]["bad_epochs"])
        resume_count = int(ck["selection"].get("resume_count", 0)) + 1
        history = list(ck.get("history") or [])
        log(f"[S/{ctx.tag}/{run_id}] resume from epoch {start_epoch}")

    fit_ds = TensorDataset(torch.from_numpy(fit_x), torch.from_numpy(y[fit_idx]))
    es_ds = TensorDataset(torch.from_numpy(es_x), torch.from_numpy(y[es_idx]))
    upstream = ctx.upstream_for("S")
    t0 = time.time()

    for epoch in range(start_epoch, epochs_target + 1):
        fit_loader = DataLoader(fit_ds, batch_size=b.s_batch_size, shuffle=True, generator=gen)
        model.train()
        losses = []
        for xb, yb in fit_loader:
            xb, yb = xb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(xb), yb)
            if not torch.isfinite(loss):
                raise RuntimeError(f"[S/{ctx.tag}/{run_id}] non-finite loss at epoch {epoch}")
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
        train_bce = float(np.mean(losses)) if losses else float("nan")

        if early_stopping:
            model.eval()
            es_loader = DataLoader(es_ds, batch_size=b.s_batch_size, shuffle=False)
            es_losses = []
            with torch.no_grad():
                for xb, yb in es_loader:
                    xb, yb = xb.to(device), yb.to(device)
                    es_losses.append(float(criterion(model(xb), yb).item()))
            monitor = float(np.mean(es_losses))
        else:
            monitor = train_bce
        scheduler.step(monitor)

        is_best = False
        if early_stopping:
            if monitor < best_loss - R.S_IMPROVEMENT_EPS:
                best_loss, best_epoch, bad_epochs, is_best = monitor, epoch, 0, True
            else:
                bad_epochs += 1

        row = {"run": run_id, "epoch": epoch, "train_bce": train_bce,
               "early_stop_bce": monitor if early_stopping else "",
               "learning_rate": optimizer.param_groups[0]["lr"],
               "bad_epochs": bad_epochs, "is_best": bool(is_best),
               "elapsed_seconds": round(time.time() - t0, 3), "resume_count": resume_count}
        history.append(row)
        atomic_write_text(pd.DataFrame(history).to_csv(index=False), hist_path)

        env = build_envelope(
            component="S", seed=ctx.seed, run_id=run_id, architecture_id=R.S_ARCHITECTURE_ID,
            model_state=model.state_dict(), upstream=upstream, epoch=epoch,
            best_epoch=best_epoch,
            selection={"rule": "minimum EARLY_STOP mean BCE", "best_loss": best_loss,
                       "best_epoch": best_epoch, "bad_epochs": bad_epochs,
                       "resume_count": resume_count},
            recipe={"s": ctx.recipe.s, "thresholds": ctx.recipe.thresholds},
            history=history, optimizer_state=optimizer.state_dict(),
            scheduler_state=scheduler.state_dict(), rng_state=capture_rng(),
            extra={"normalizer_mu": mu.tolist(), "normalizer_sigma": sigma.tolist(),
                   "normalizer_constant_mask": const.tolist(),
                   "n_fit": int(len(fit_idx)), "n_early_stop": int(len(es_idx)),
                   "n_outer_target": int(len(ot_idx)),
                   "operational_override": ctx.bounds.overrides(),
                   "labels_sha256": sha256_file(ctx.l_dir / "labels.csv"),
                   "safety_features_sha256": sha256_file(ctx.l_dir / "safety_features.npy")},
        )
        atomic_torch_save(env, latest_path)
        if is_best:
            atomic_torch_save(env, best_path)

        if early_stopping and bad_epochs >= R.S_PATIENCE:
            break

    model.eval()
    with torch.no_grad():
        ot_loader = DataLoader(TensorDataset(torch.from_numpy(ot_x)), batch_size=b.s_batch_size,
                               shuffle=False)
        logits = []
        for (xb,) in ot_loader:
            logits.extend(model(xb.to(device)).cpu().numpy().tolist())
    logits = np.asarray(logits, dtype=np.float32)

    record = {"run": run_id, "seed": ctx.seed, "tag": ctx.tag,
              "epochs_completed": len(history), "epochs_target": epochs_target,
              "best_epoch": best_epoch,
              "best_early_stop_bce": best_loss if early_stopping else None,
              "n_fit": int(len(fit_idx)), "n_early_stop": int(len(es_idx)),
              "n_outer_target": int(len(ot_idx)), "parameter_count": n,
              "history_sha256": sha256_file(hist_path),
              "best_checkpoint_sha256": sha256_file(best_path) if best_path.exists() else None,
              "latest_checkpoint_sha256": sha256_file(latest_path),
              "upstream": {k: v["sha256"] for k, v in upstream.items()},
              "elapsed_seconds": round(time.time() - t0, 3), "completed_utc": utc_now()}
    atomic_write_json(record, exp_dir / "run.json")
    return {"record": record, "ot_logits": logits, "ot_idx": np.asarray(ot_idx)}


# --------------------------------------------------------------------------- #
def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    seed_everything(ctx.family.run_seed("S", "main"))
    meta, X, y = load_family_inputs(ctx)
    cv = meta["cv_fold"].to_numpy(dtype=np.int64)
    log(f"[S/{ctx.tag}] population={len(meta)} positives={int(y.sum())}")

    fold_records, oof = {}, np.full(len(meta), np.nan, dtype=np.float32)
    table = ctx.folds("cv5")
    pos = {sid: i for i, sid in enumerate(meta["sample_id"].astype(str))}
    for k in range(R.S_CV_FOLDS):
        fold_seed = ctx.family.run_seed("S", f"fold{k}")
        roles = table.folds[k]
        tr_idx = np.array([pos[s] for s in roles["fit"] if s in pos], dtype=np.int64)
        es_idx = np.array([pos[s] for s in roles["early_stop"] if s in pos], dtype=np.int64)
        ot_idx = np.array([pos[s] for s in roles["outer_target"] if s in pos], dtype=np.int64)
        if len(tr_idx) == 0 or len(es_idx) == 0 or len(ot_idx) == 0:
            raise RuntimeError(
                f"[S/{ctx.tag}] fold{k} has an empty role after restricting to "
                f"action-available samples: fit={len(tr_idx)} es={len(es_idx)} "
                f"ot={len(ot_idx)}")
        covered = np.concatenate([tr_idx, es_idx, ot_idx])
        if len(np.unique(covered)) != len(covered):
            raise RuntimeError(f"[S/{ctx.tag}] fold{k} roles overlap")

        res = _train_one(ctx, run_id=f"{ctx.tag}/S/fold{k}", ckpt_dir=ctx.s_dir / f"fold{k}",
                         exp_dir=ctx.s_dir / f"fold{k}", seed=fold_seed, fit_idx=tr_idx,
                         es_idx=es_idx, ot_idx=ot_idx, X=X, y=y,
                         epochs_target=int(ctx.bounds.s_max_epochs), early_stopping=True,
                         resume=resume, log=log)
        oof[ot_idx] = res["ot_logits"]
        fold_records[k] = res["record"]
        log(f"[S/{ctx.tag}] fold{k} best_epoch={res['record']['best_epoch']} "
            f"(fit={len(tr_idx)} es={len(es_idx)} ot={len(ot_idx)})")

    if not np.isfinite(oof).all():
        raise RuntimeError(f"[S/{ctx.tag}] OOF logits contain non-finite values")

    ctx.s_dir.mkdir(parents=True, exist_ok=True)
    oof_df = pd.DataFrame({"sample_id": meta["sample_id"], "domain": meta["domain"],
                           "task_id": meta["task_id"], "cv_fold": cv,
                           "delta_dice": meta["delta_dice"], "safety_target": y,
                           "safety_logit_oof": oof,
                           "safety_probability_oof": 1.0 / (1.0 + np.exp(-oof))})
    oof_path = ctx.s_dir / "oof_safety_predictions.csv"
    atomic_write_text(oof_df.to_csv(index=False), oof_path)

    best_epochs = sorted(int(r["best_epoch"]) for r in fold_records.values() if r["best_epoch"] >= 0)
    if not best_epochs:
        raise RuntimeError(f"[S/{ctx.tag}] no fold produced a best epoch")
    refit_epochs = best_epochs[len(best_epochs) // 2]
    refit_epochs = max(1, min(refit_epochs, int(ctx.bounds.s_max_epochs)))

    final_seed = ctx.family.run_seed("S", "final")
    all_idx = np.arange(len(meta))
    final = _train_one(ctx, run_id=f"{ctx.tag}/S/final", ckpt_dir=ctx.s_dir / "final",
                       exp_dir=ctx.s_dir / "final", seed=final_seed, fit_idx=all_idx,
                       es_idx=all_idx[:1], ot_idx=all_idx[:1], X=X, y=y,
                       epochs_target=refit_epochs, early_stopping=False, resume=resume,
                       log=log)

    from ..provenance import atomic_write_bytes
    latest = ctx.s_dir / "final" / "latest.pt"
    if not latest.exists():
        raise RuntimeError(f"[S/{ctx.tag}] final refit produced no checkpoint")
    atomic_write_bytes(latest.read_bytes(), ctx.s_dir / "final" / "final.pt")

    prob = 1.0 / (1.0 + np.exp(-oof))
    pred = (prob >= R.SOMEGA_ACCEPT_THRESHOLD).astype(np.float32)
    acc = float((pred == y).mean())
    record = {"artifact": "full_barr_stage_S", "stage": STAGE, "seed": ctx.seed,
              "tag": ctx.tag, "population_n": int(len(meta)),
              "positives": int(y.sum()), "negatives": int(len(y) - y.sum()),
              "folds": fold_records, "final": final["record"],
              "refit_epochs": refit_epochs, "fold_best_epochs": best_epochs,
              "oof_accuracy_at_0p50": acc,
              "oof_path": relpath_str(oof_path),
              "oof_sha256": sha256_file(oof_path),
              "accept_threshold": R.SOMEGA_ACCEPT_THRESHOLD,
              "final_checkpoint_sha256": sha256_file(ctx.s_dir / "final" / "final.pt"),
              "test_reads": 0, "router_holdout_reads": 0, "completed_utc": utc_now()}
    atomic_write_json(record, ctx.s_dir / "run.json")
    return StageRecord(stage=STAGE, status="COMPLETE",
                       artifacts={"run": str(ctx.s_dir / "run.json"),
                                  "final": str(ctx.s_dir / "final" / "final.pt"),
                                  "oof": str(oof_path)}, detail=record)


def is_complete(ctx: RunContext) -> bool:
    rec = read_json(ctx.s_dir / "run.json")
    final = ctx.s_dir / "final" / "final.pt"
    if not final.exists():
        return False
    return rec.get("final_checkpoint_sha256") == sha256_file(final)


def verify(ctx: RunContext) -> dict:
    final = ctx.s_dir / "final" / "final.pt"
    ck = load_checkpoint(final, component="S", seed=ctx.seed)
    return {"component": "S", "seed": ctx.seed, "sha256": sha256_file(final),
            "upstream": {k: v["sha256"] for k, v in ck["upstream"].items()},
            "verdict": "S_FAMILY_VERIFIED"}
