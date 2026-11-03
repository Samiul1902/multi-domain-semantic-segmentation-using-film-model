"""B_phi -- per-seed Benefit Router producer.

5-fold cross-fit over ROUTER_DEVELOPMENT, then one final refit.

Frozen recipe (Phase-25D v1.2.1)
--------------------------------
architecture Linear(218,128) -> LayerNorm -> SiLU -> Dropout(0.10)
             -> Linear(128,64) -> LayerNorm -> SiLU -> Dropout(0.10) -> Linear(64,1)
             with ``Embedding(4,16)`` concatenated to the 202 numeric features
loss         HuberLoss(delta = 0.05)
optimizer    AdamW, lr 1e-3, weight_decay 1e-4
scheduler    ReduceLROnPlateau(min, factor 0.5, patience 8, threshold 1e-4 rel,
             min_lr 1e-6, eps 1e-8)
batch        128, max 200 epochs, patience 20
selection    minimum EARLY_STOP Huber
refit        median of the five fold best-epochs, seed 42
normalisation FIT-only standardisation of the eight scalar indices
             (192..197, 200, 201); zero-sigma columns are set to 0

Targets
-------
``delta_dice`` from the OOF label table of the SAME seed family.  The label for a
sample was produced by the refiner that did not see it, so the router never learns
from a prediction that had access to the sample.

Inputs are GT-free by construction: the 202-D vector is built from three feature
taps, the global probability map and ROI geometry.  No mask, no oracle Dice and no
``delta_dice`` value is reachable from the feature builder.
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

STAGE = "B"


# --------------------------------------------------------------------------- #
# B_phi is the single frozen Phase-25D definition, imported rather than copied.
# See src/models/barr/phase25_models.py for why the canonical producer cannot be
# imported directly, and tests/test_phase25_architecture_drift.py for the guard.
from src.models.barr.phase25_models import BARRBenefitRouterV1  # noqa: E402


def count_params(model: nn.Module) -> int:
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


# --------------------------------------------------------------------------- #
def load_family_inputs(ctx: RunContext) -> pd.DataFrame:
    """Join the per-seed features to the per-seed OOF labels, once.

    Returns one row per action-available ROUTER_DEVELOPMENT sample with
    ``feature_row_index``, ``task_id``, ``domain``, ``delta_dice``, ``gain_category``
    and ``cv_fold``.
    """
    label_path = ctx.l_dir / "labels.csv"
    if not label_path.exists():
        raise FileNotFoundError(f"label table missing for {ctx.tag}: {label_path}")
    labels = pd.read_csv(label_path)
    labels["sample_id"] = labels["sample_id"].astype(str)

    # cv fold membership (5-fold) -- frozen canonical table
    cv = ctx.folds("cv5")
    fold_of: Dict[str, int] = {}
    for k, v in cv.folds.items():
        for sid in v["outer_target"]:
            fold_of[sid] = k

    # ---- gather the per-seed 202-D feature row for every sample ------- #
    feats_by_id: Dict[str, np.ndarray] = {}
    for domain in R.DATASET_ORDER:
        p = ctx.cache_dir / domain / "router_features.npy"
        if not p.exists():
            continue
        arr = np.load(p)
        meta = pd.read_csv(ctx.cache_dir / domain / "meta.csv")
        for i, sid in enumerate(meta["sample_id"].astype(str)):
            feats_by_id[sid] = arr[i]
    if not feats_by_id:
        raise RuntimeError(f"no router features for {ctx.tag}")

    merged = labels[labels["action_available"].astype(bool)].copy().reset_index(drop=True)
    missing = [sid for sid in merged["sample_id"] if sid not in feats_by_id]
    if missing:
        raise RuntimeError(f"{len(missing)} labelled samples have no feature row")
    vectors = np.stack([feats_by_id[sid] for sid in merged["sample_id"]]).astype(np.float32)
    if vectors.shape[1] != R.B_NUMERIC_DIM:
        raise RuntimeError(f"router feature width {vectors.shape[1]} != {R.B_NUMERIC_DIM}")
    if not np.isfinite(vectors).all():
        raise RuntimeError("router feature matrix contains non-finite values")

    merged["cv_fold"] = merged["sample_id"].map(fold_of)
    if merged["cv_fold"].isna().any():
        raise RuntimeError("some labelled samples have no 5-fold CV assignment")
    merged["feature_row_index"] = np.arange(len(merged))
    merged.attrs["vectors"] = vectors
    return merged


def fit_normalize(fit_features: np.ndarray):
    idx = list(R.B_NORMALIZE_IDX)
    mu = fit_features[:, idx].mean(axis=0, keepdims=True)
    sigma = fit_features[:, idx].std(axis=0, keepdims=True, ddof=0)
    const = (sigma < 1e-12).squeeze()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (fit_features[:, idx] - mu) / sigma_safe
    norm[:, const.squeeze()] = 0.0
    out = fit_features.copy()
    out[:, idx] = norm
    return out, mu, sigma, const


def apply_normalize(features: np.ndarray, mu, sigma, const) -> np.ndarray:
    idx = list(R.B_NORMALIZE_IDX)
    out = features.copy()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (features[:, idx] - mu) / sigma_safe
    norm[:, const.squeeze()] = 0.0
    out[:, idx] = norm
    return out


def _train_one(ctx: RunContext, *, run_id: str, ckpt_dir: Path, exp_dir: Path, seed: int,
               fit_idx, es_idx, ot_idx, X: np.ndarray, y: np.ndarray, t: np.ndarray,
               epochs_target: int, early_stopping: bool, resume: bool, log) -> dict:
    device = get_device(require_cuda=(ctx.bounds.device == "cuda"))
    b = ctx.bounds
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)
    hist_path = exp_dir / "history.csv"
    best_path = ckpt_dir / "best.pt"
    latest_path = ckpt_dir / "latest.pt"

    fit_x_raw, es_x_raw, ot_x_raw = X[fit_idx], X[es_idx], X[ot_idx]
    fit_x, mu, sigma, const = fit_normalize(fit_x_raw)
    es_x = apply_normalize(es_x_raw, mu, sigma, const)
    ot_x = apply_normalize(ot_x_raw, mu, sigma, const)

    seed_everything(seed)
    gen = torch.Generator()
    gen.manual_seed(seed)
    model = BARRBenefitRouterV1().to(device)
    n = count_params(model)
    if n != R.B_EXPECTED_PARAMETERS:
        raise RuntimeError(f"B_phi parameter count {n} != {R.B_EXPECTED_PARAMETERS}")

    optimizer = torch.optim.AdamW(model.parameters(), lr=R.B_OPTIMIZER["learning_rate"],
                                  weight_decay=R.B_OPTIMIZER["weight_decay"])
    sc = R.B_SCHEDULER
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode=sc["mode"], factor=sc["factor"], patience=sc["patience"],
        threshold=sc["threshold"], threshold_mode=sc["threshold_mode"],
        cooldown=sc["cooldown"], min_lr=sc["min_lr"], eps=sc["eps"])
    criterion = nn.HuberLoss(delta=R.B_LOSS["delta"], reduction="mean")

    history: List[dict] = []
    start_epoch, best_loss, best_epoch, bad_epochs, resume_count = 1, float("inf"), -1, 0, 0
    if resume and latest_path.exists():
        ck = load_checkpoint(latest_path, map_location="cpu", component="B", seed=ctx.seed)
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
        log(f"[B/{ctx.tag}/{run_id}] resume from epoch {start_epoch}")

    fit_ds = TensorDataset(torch.from_numpy(fit_x), torch.from_numpy(t[fit_idx]),
                           torch.from_numpy(y[fit_idx]))
    es_ds = TensorDataset(torch.from_numpy(es_x), torch.from_numpy(t[es_idx]),
                          torch.from_numpy(y[es_idx]))
    upstream = ctx.upstream_for("B")
    t0 = time.time()

    for epoch in range(start_epoch, epochs_target + 1):
        fit_loader = DataLoader(fit_ds, batch_size=b.b_batch_size, shuffle=True, generator=gen)
        model.train()
        losses = []
        for xb, tb, yb in fit_loader:
            xb, tb, yb = xb.to(device), tb.to(device), yb.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(xb, tb), yb)
            if not torch.isfinite(loss):
                raise RuntimeError(f"[B/{ctx.tag}/{run_id}] non-finite loss at epoch {epoch}")
            loss.backward()
            optimizer.step()
            losses.append(float(loss.item()))
        train_huber = float(np.mean(losses)) if losses else float("nan")

        if early_stopping:
            model.eval()
            es_loader = DataLoader(es_ds, batch_size=b.b_batch_size, shuffle=False)
            es_losses = []
            with torch.no_grad():
                for xb, tb, yb in es_loader:
                    xb, tb, yb = xb.to(device), tb.to(device), yb.to(device)
                    es_losses.append(float(criterion(model(xb, tb), yb).item()))
            monitor = float(np.mean(es_losses))
        else:
            monitor = train_huber
        scheduler.step(monitor)

        is_best = False
        if early_stopping and monitor < best_loss - 1e-12:
            best_loss, best_epoch, bad_epochs, is_best = monitor, epoch, 0, True
        elif early_stopping:
            bad_epochs += 1

        row = {"run": run_id, "epoch": epoch, "train_huber": train_huber,
               "early_stop_huber": monitor if early_stopping else "",
               "learning_rate": optimizer.param_groups[0]["lr"],
               "bad_epochs": bad_epochs, "is_best": bool(is_best),
               "elapsed_seconds": round(time.time() - t0, 3), "resume_count": resume_count}
        history.append(row)
        atomic_write_text(pd.DataFrame(history).to_csv(index=False), hist_path)

        env = build_envelope(
            component="B", seed=ctx.seed, run_id=run_id, architecture_id=R.B_ARCHITECTURE_ID,
            model_state=model.state_dict(), upstream=upstream, epoch=epoch,
            best_epoch=best_epoch,
            selection={"rule": "minimum EARLY_STOP Huber", "best_loss": best_loss,
                       "best_epoch": best_epoch, "bad_epochs": bad_epochs,
                       "resume_count": resume_count},
            recipe={"b": ctx.recipe.b, "thresholds": ctx.recipe.thresholds},
            history=history, optimizer_state=optimizer.state_dict(),
            scheduler_state=scheduler.state_dict(), rng_state=capture_rng(),
            extra={"normalizer_mu": mu.tolist(), "normalizer_sigma": sigma.tolist(),
                   "normalizer_constant_mask": const.tolist(),
                   "normalizer_index": list(R.B_NORMALIZE_IDX),
                   "n_fit": int(len(fit_idx)), "n_early_stop": int(len(es_idx)),
                   "n_outer_target": int(len(ot_idx)),
                   "operational_override": ctx.bounds.overrides(),
                   "labels_sha256": sha256_file(ctx.l_dir / "labels.csv")},
        )
        atomic_torch_save(env, latest_path)
        if is_best:
            atomic_torch_save(env, best_path)

        if early_stopping and bad_epochs >= R.B_PATIENCE:
            break

    model.eval()
    with torch.no_grad():
        ot_loader = DataLoader(TensorDataset(torch.from_numpy(ot_x),
                                             torch.from_numpy(t[ot_idx])),
                               batch_size=b.b_batch_size, shuffle=False)
        preds = []
        for xb, tb in ot_loader:
            preds.extend(model(xb.to(device), tb.to(device)).cpu().numpy().tolist())
    preds = np.asarray(preds, dtype=np.float32)

    record = {"run": run_id, "seed": ctx.seed, "tag": ctx.tag,
              "epochs_completed": len(history), "epochs_target": epochs_target,
              "best_epoch": best_epoch,
              "best_early_stop_huber": best_loss if early_stopping else None,
              "n_fit": int(len(fit_idx)), "n_early_stop": int(len(es_idx)),
              "n_outer_target": int(len(ot_idx)),
              "parameter_count": n,
              "history_sha256": sha256_file(hist_path),
              "best_checkpoint_sha256": sha256_file(best_path) if best_path.exists() else None,
              "latest_checkpoint_sha256": sha256_file(latest_path),
              "upstream": {k: v["sha256"] for k, v in upstream.items()},
              "elapsed_seconds": round(time.time() - t0, 3),
              "completed_utc": utc_now()}
    atomic_write_json(record, exp_dir / "run.json")
    return {"record": record, "ot_preds": preds, "ot_idx": np.asarray(ot_idx)}


# --------------------------------------------------------------------------- #
def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    seed_everything(ctx.family.run_seed("B", "main"))
    merged = load_family_inputs(ctx)
    X = merged.attrs["vectors"]
    y = merged["delta_dice"].to_numpy(dtype=np.float32)
    t = merged["task_id"].to_numpy(dtype=np.int64)
    cv = merged["cv_fold"].to_numpy(dtype=np.int64)

    # The FIT / EARLY_STOP / OUTER_TARGET three-way split inside each CV fold comes
    # from the frozen Phase-25D table, not from an invented permutation.  Reusing it
    # keeps the router's cross-fit identical in structure to the canonical producer.
    table = ctx.folds("cv5")
    pos = {sid: i for i, sid in enumerate(merged["sample_id"].astype(str))}
    log(f"[B/{ctx.tag}] population={len(merged)} folds={sorted(set(cv.tolist()))}")

    fold_records, oof = {}, np.full(len(merged), np.nan, dtype=np.float32)
    for k in range(R.B_CV_FOLDS):
        fold_seed = ctx.family.run_seed("B", f"fold{k}")
        roles = table.folds[k]
        tr_idx = np.array([pos[s] for s in roles["fit"] if s in pos], dtype=np.int64)
        es_idx = np.array([pos[s] for s in roles["early_stop"] if s in pos], dtype=np.int64)
        ot_idx = np.array([pos[s] for s in roles["outer_target"] if s in pos], dtype=np.int64)
        if len(tr_idx) == 0 or len(es_idx) == 0 or len(ot_idx) == 0:
            raise RuntimeError(
                f"[B/{ctx.tag}] fold{k} has an empty role after restricting to "
                f"action-available samples: fit={len(tr_idx)} es={len(es_idx)} "
                f"ot={len(ot_idx)}")
        # the three roles must partition this fold's samples
        covered = np.concatenate([tr_idx, es_idx, ot_idx])
        if len(np.unique(covered)) != len(covered):
            raise RuntimeError(f"[B/{ctx.tag}] fold{k} roles overlap")

        res = _train_one(ctx, run_id=f"{ctx.tag}/B/fold{k}", ckpt_dir=ctx.b_dir / f"fold{k}",
                         exp_dir=ctx.b_dir / f"fold{k}", seed=fold_seed, fit_idx=tr_idx,
                         es_idx=es_idx, ot_idx=ot_idx, X=X, y=y, t=t,
                         epochs_target=int(ctx.bounds.b_max_epochs), early_stopping=True,
                         resume=resume, log=log)
        oof[ot_idx] = res["ot_preds"]
        fold_records[k] = res["record"]
        log(f"[B/{ctx.tag}] fold{k} best_epoch={res['record']['best_epoch']} "
            f"(fit={len(tr_idx)} es={len(es_idx)} ot={len(ot_idx)})")

    if not np.isfinite(oof).all():
        raise RuntimeError(f"[B/{ctx.tag}] OOF predictions contain non-finite values")

    ctx.b_dir.mkdir(parents=True, exist_ok=True)
    oof_df = pd.DataFrame({
        "sample_id": merged["sample_id"], "domain": merged["domain"],
        "task_id": merged["task_id"], "cv_fold": cv,
        "delta_dice": y, "delta_hat_oof": oof, "residual": y - oof,
    })
    oof_path = ctx.b_dir / "oof_predictions.csv"
    atomic_write_text(oof_df.to_csv(index=False), oof_path)

    best_epochs = sorted(int(r["best_epoch"]) for r in fold_records.values() if r["best_epoch"] >= 0)
    if not best_epochs:
        raise RuntimeError(f"[B/{ctx.tag}] no fold produced a best epoch")
    refit_epochs = best_epochs[len(best_epochs) // 2]
    refit_epochs = max(1, min(refit_epochs, int(ctx.bounds.b_max_epochs)))

    final_seed = ctx.family.run_seed("B", "final")
    all_idx = np.arange(len(merged))
    final = _train_one(ctx, run_id=f"{ctx.tag}/B/final", ckpt_dir=ctx.b_dir / "final",
                       exp_dir=ctx.b_dir / "final", seed=final_seed, fit_idx=all_idx,
                       es_idx=all_idx[:1], ot_idx=all_idx[:1], X=X, y=y, t=t,
                       epochs_target=refit_epochs, early_stopping=False, resume=resume,
                       log=log)

    from ..provenance import atomic_write_bytes
    latest = ctx.b_dir / "final" / "latest.pt"
    if not latest.exists():
        raise RuntimeError(f"[B/{ctx.tag}] final refit produced no checkpoint")
    atomic_write_bytes(latest.read_bytes(), ctx.b_dir / "final" / "final.pt")

    mae = float(np.mean(np.abs(y - oof)))
    record = {"artifact": "full_barr_stage_B", "stage": STAGE, "seed": ctx.seed,
              "tag": ctx.tag, "population_n": int(len(merged)),
              "folds": fold_records, "final": final["record"],
              "refit_epochs": refit_epochs, "fold_best_epochs": best_epochs,
              "oof_mae": mae, "oof_path": relpath_str(oof_path),
              "oof_sha256": sha256_file(oof_path),
              "final_checkpoint_sha256": sha256_file(ctx.b_dir / "final" / "final.pt"),
              "test_reads": 0, "router_holdout_reads": 0, "completed_utc": utc_now()}
    atomic_write_json(record, ctx.b_dir / "run.json")
    return StageRecord(stage=STAGE, status="COMPLETE",
                       artifacts={"run": str(ctx.b_dir / "run.json"),
                                  "final": str(ctx.b_dir / "final" / "final.pt"),
                                  "oof": str(oof_path)}, detail=record)


def is_complete(ctx: RunContext) -> bool:
    rec = read_json(ctx.b_dir / "run.json")
    final = ctx.b_dir / "final" / "final.pt"
    if not final.exists():
        return False
    return rec.get("final_checkpoint_sha256") == sha256_file(final)


def verify(ctx: RunContext) -> dict:
    final = ctx.b_dir / "final" / "final.pt"
    ck = load_checkpoint(final, component="B", seed=ctx.seed)
    return {"component": "B", "seed": ctx.seed, "sha256": sha256_file(final),
            "upstream": {k: v["sha256"] for k, v in ck["upstream"].items()},
            "verdict": "B_FAMILY_VERIFIED"}
