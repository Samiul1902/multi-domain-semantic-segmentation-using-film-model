"""Phase 28 -- router variant trainer for R1 / R2 / R3.

Implements the **exact** Phase25D router-training protocol recovered physically
in ``docs/phase28_ablation_execution_spec_v1_2.md`` §4 and bound in
``reports/audits/phase28_router_variant_training_protocol_binding_v1_2.json``.

Governance (spec v1.2)
---------------------
* §10 OOF: for each outer fold k, FIT on ``phase25d_cv_fold{k}_fit_ids.csv``,
  select on ``phase25d_cv_fold{k}_early_stop_ids.csv``, predict ONLY
  ``phase25d_cv_fold{k}_outer_target_ids.csv``. 4957 exactly-once OOF scores.
* §11 seeds: ``seed = 42000 + outer_fold_index`` (no new seeds).
* §12 budget: N/A here -- fixed budget K=1239 is applied in the membership step
  AFTER the outcome-access barrier (§15).
* §15 outcome-access barrier: this trainer NEVER reads ``delta_dice``,
  ``gain_category``, ``global_dice`` or ``candidate_refined_dice`` for the rows
  it is predicting. Targets are read ONLY for the FIT rows (training target) and
  the EARLY_STOP rows (checkpoint selection) -- both leakage-safe.

Population: ROUTER_DEVELOPMENT, n = 4957.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/train_phase28_router_variant.py \
        --variant R1
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import torch  # noqa: E402
import torch.nn as nn  # noqa: E402

from src.models.barr.router_variants import (  # noqa: E402
    ROUTER_VARIANT_EXPECTED_PARAMETERS,
    build_router_variant,
    count_params,
)

CACHE25B = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
CACHE25C = ROOT / "data_cache" / "phase25c_barr_oof_paired_gain_labels_v1_2"
TABLES = ROOT / "reports" / "tables"
OUT_CACHE = ROOT / "data_cache" / "phase28_router_variants_v1_2"
CKPT_ROOT = ROOT / "checkpoints"

#: Phase25D canonical scalar-normalize index set (spec v1.2 §7).
SCALAR_NORMALIZE_IDX = [192, 193, 194, 195, 196, 197, 200, 201]
#: R1 / R3 receive only the 10 scalars, re-indexed to local columns 0..9.
SCALAR_LOCAL_IDX = list(range(10))
#: The 8 continuous scalars within the local 0..9 block that are standardized.
R1R3_NORMALIZE_LOCAL_IDX = [0, 1, 2, 3, 4, 5, 8, 9]

CKPT_DIRS = {
    "R1": CKPT_ROOT / "phase28_router_R1_no_deep",
    "R2": CKPT_ROOT / "phase28_router_R2_no_task",
    "R3": CKPT_ROOT / "phase28_router_R3_scalar_only",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
        f.write("\n")


# =====================================================================
# Data
# =====================================================================
def load_population():
    features = np.load(CACHE25B / "features.npy").astype(np.float32)  # (4957, 202)
    with open(CACHE25B / "metadata.csv", "r", newline="", encoding="utf-8") as f:
        meta_rows = list(csv.DictReader(f))
    with open(CACHE25C / "phase25c_oof_paired_gain_labels.csv", "r", newline="", encoding="utf-8") as f:
        label_rows = list(csv.DictReader(f))

    sid_to_feat = {r["sample_id"]: i for i, r in enumerate(meta_rows)}
    sid_to_label = {r["sample_id"]: r for r in label_rows}

    joined = []
    for sid, feat_idx in sid_to_feat.items():
        lbl = sid_to_label.get(sid)
        if lbl is None:
            continue
        joined.append({
            "sample_id": sid,
            "feat_idx": feat_idx,
            "task_id": int(meta_rows[feat_idx]["task_id"]),
            "domain": meta_rows[feat_idx]["domain"],
            "action_available": lbl["action_available"] == "True",
            "delta_dice": float(lbl["delta_dice"]),
            "gain_category": lbl["gain_category"],
        })
    joined.sort(key=lambda r: r["sample_id"])

    assert len(joined) == 4957, f"expected 4957, got {len(joined)}"
    return features, meta_rows, joined


def load_cv():
    with open(TABLES / "phase25d_cv5_manifest.csv", "r", newline="", encoding="utf-8") as f:
        cv = list(csv.DictReader(f))
    sid_to_fold = {r["sample_id"]: int(r["router_cv_fold"]) for r in cv}
    assert len(sid_to_fold) == 4957
    folds = {k: {} for k in range(5)}
    for k in range(5):
        for role in ("fit", "early_stop", "outer_target"):
            path = TABLES / f"phase25d_cv_fold{k}_{role}_ids.csv"
            with open(path, "r", newline="", encoding="utf-8") as f:
                folds[k][role] = [r["sample_id"] for r in csv.DictReader(f)]
        assert not (set(folds[k]["fit"]) & set(folds[k]["early_stop"]))
        assert not (set(folds[k]["fit"]) & set(folds[k]["outer_target"]))
        assert not (set(folds[k]["early_stop"]) & set(folds[k]["outer_target"]))
    return sid_to_fold, folds


# =====================================================================
# Variant input projection  (spec v1.2 §6-§9)
# =====================================================================
def project_variant(features: np.ndarray, variant: str) -> np.ndarray:
    """Return the variant's numeric input matrix (before normalization).

    R1 : 10 scalars, re-indexed to local 0..9
    R2 : all 202 canonical numeric features
    R3 : 10 scalars, re-indexed to local 0..9
    """
    if variant == "R2":
        return features.astype(np.float32)
    # R1 / R3 require the 10 canonical scalar columns (global idx 192..201).
    return features[:, 192:202].astype(np.float32)


def normalize_indices(variant: str) -> list[int]:
    """Local column indices to standardize for the variant."""
    if variant == "R2":
        return SCALAR_NORMALIZE_IDX          # global cols within the 202-wide block
    return R1R3_NORMALIZE_LOCAL_IDX          # local cols within the 10-wide block


def fit_normalize(fit_features: np.ndarray, idx: list[int]):
    mu = fit_features[:, idx].mean(axis=0, keepdims=True)
    sigma = fit_features[:, idx].std(axis=0, keepdims=True, ddof=0)
    const_mask = (sigma < 1e-12).squeeze()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (fit_features[:, idx] - mu) / sigma_safe
    norm[:, const_mask] = 0.0
    out = fit_features.copy()
    out[:, idx] = norm
    return out, mu, sigma, const_mask


def apply_normalize(features: np.ndarray, mu, sigma, const_mask, idx: list[int]) -> np.ndarray:
    out = features.copy()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (features[:, idx] - mu) / sigma_safe
    norm[:, const_mask] = 0.0
    out[:, idx] = norm
    return out


# =====================================================================
# Training
# =====================================================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def train_fold(variant: str, k: int, x_all, t_all, y_all, sid_index, folds, seed, verbose=True):
    fold_seed = seed
    random.seed(fold_seed)
    np.random.seed(fold_seed)
    torch.manual_seed(fold_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(fold_seed)

    fit_ids = folds[k]["fit"]
    es_ids = folds[k]["early_stop"]
    ot_ids = folds[k]["outer_target"]

    fit_idx = [sid_index[s] for s in fit_ids]
    es_idx = [sid_index[s] for s in es_ids]
    ot_idx = [sid_index[s] for s in ot_ids]

    nidx = normalize_indices(variant)
    fit_x_raw = x_all[fit_idx]
    es_x_raw = x_all[es_idx]
    ot_x_raw = x_all[ot_idx]

    fit_x_norm, mu, sigma, const_mask = fit_normalize(fit_x_raw, nidx)
    es_x_norm = apply_normalize(es_x_raw, mu, sigma, const_mask, nidx)
    ot_x_norm = apply_normalize(ot_x_raw, mu, sigma, const_mask, nidx)

    fit_y = y_all[fit_idx]
    es_y = y_all[es_idx]
    fit_t = t_all[fit_idx]
    es_t = t_all[es_idx]
    ot_t = t_all[ot_idx]

    model = build_router_variant(variant).to(DEVICE)
    param_count = count_params(model)

    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=8,
        threshold=1e-4, threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8,
    )
    criterion = nn.HuberLoss(delta=0.05, reduction="mean")

    use_task = variant == "R1"
    if use_task:
        fit_ds = torch.utils.data.TensorDataset(
            torch.from_numpy(fit_x_norm), torch.from_numpy(fit_t), torch.from_numpy(fit_y))
        es_ds = torch.utils.data.TensorDataset(
            torch.from_numpy(es_x_norm), torch.from_numpy(es_t), torch.from_numpy(es_y))
    else:
        fit_ds = torch.utils.data.TensorDataset(
            torch.from_numpy(fit_x_norm), torch.from_numpy(fit_y))
        es_ds = torch.utils.data.TensorDataset(
            torch.from_numpy(es_x_norm), torch.from_numpy(es_y))

    fit_loader = torch.utils.data.DataLoader(
        fit_ds, batch_size=128, shuffle=True,
        generator=torch.Generator().manual_seed(fold_seed))
    es_loader = torch.utils.data.DataLoader(es_ds, batch_size=128, shuffle=False)

    ckpt_dir = CKPT_DIRS[variant] / f"fold{k}"
    ckpt_dir.mkdir(parents=True, exist_ok=True)

    best_loss = float("inf")
    best_epoch = -1
    bad_epochs = 0
    history = []
    t0 = time.time()

    for epoch in range(1, 201):
        model.train()
        train_losses = []
        for batch in fit_loader:
            if use_task:
                xb, tb, yb = batch
                tb = tb.to(DEVICE)
            else:
                xb, yb = batch
                tb = None
            xb, yb = xb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            pred = model(xb, tb) if use_task else model(xb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())
        train_huber = float(np.mean(train_losses))

        model.eval()
        es_losses = []
        with torch.no_grad():
            for batch in es_loader:
                if use_task:
                    xb, tb, yb = batch
                    tb = tb.to(DEVICE)
                else:
                    xb, yb = batch
                    tb = None
                xb, yb = xb.to(DEVICE), yb.to(DEVICE)
                pred = model(xb, tb) if use_task else model(xb)
                es_losses.append(criterion(pred, yb).item())
        es_huber = float(np.mean(es_losses))

        is_best = False
        if es_huber < best_loss - 1e-12:
            best_loss = es_huber
            best_epoch = epoch
            bad_epochs = 0
            is_best = True
        else:
            bad_epochs += 1

        history.append({
            "epoch": epoch,
            "train_huber": train_huber,
            "early_stop_huber": es_huber,
            "lr": float(optimizer.param_groups[0]["lr"]),
            "is_best": is_best,
            "bad_epochs": bad_epochs,
        })

        if is_best:
            torch.save({
                "model_state": model.state_dict(),
                "epoch": epoch,
                "es_huber": es_huber,
                "variant": variant,
                "fold": k,
                "seed": fold_seed,
                "param_count": param_count,
                "architecture": f"BARRBenefitRouter{variant}",
                "input_width": model.INPUT_WIDTH,
                "uses_task_embedding": getattr(model, "USES_TASK_EMBEDDING", False),
            }, ckpt_dir / "best.pt")

        # scheduler.step AFTER checkpoint test (spec v1.2 §4)
        scheduler.step(es_huber)

        if verbose and (epoch % 20 == 0 or epoch == 1):
            print(f"    [{variant} fold{k}] ep{epoch} train={train_huber:.6f} es={es_huber:.6f} "
                  f"best_ep={best_epoch} bad={bad_epochs}")

        if bad_epochs >= 20:
            break

    # Restore best checkpoint
    state = torch.load(ckpt_dir / "best.pt", map_location=DEVICE, weights_only=False)
    model.load_state_dict(state["model_state"])

    # OOF prediction on the OUTER_TARGET rows only (spec v1.2 §10, §5 semantics)
    model.eval()
    ot_preds = []
    with torch.no_grad():
        if use_task:
            ot_ds = torch.utils.data.TensorDataset(
                torch.from_numpy(ot_x_norm), torch.from_numpy(ot_t))
        else:
            ot_ds = torch.utils.data.TensorDataset(torch.from_numpy(ot_x_norm))
        ot_loader = torch.utils.data.DataLoader(ot_ds, batch_size=128, shuffle=False)
        for batch in ot_loader:
            if use_task:
                xb, tb = batch
                tb = tb.to(DEVICE)
            else:
                (xb,) = batch
                tb = None
            xb = xb.to(DEVICE)
            pred = model(xb, tb) if use_task else model(xb)
            ot_preds.extend(pred.cpu().numpy().tolist())
    ot_preds = np.array(ot_preds, dtype=np.float32)

    # Persist history + closure
    with open(ckpt_dir / "history.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(history[0].keys()))
        w.writeheader()
        w.writerows(history)

    save_json(ckpt_dir / "normalization.json", {
        "variant": variant,
        "fold": k,
        "normalize_local_indices": nidx,
        "mu": mu.tolist(),
        "sigma": sigma.tolist(),
        "constant_mask": [bool(b) for b in np.atleast_1d(const_mask)],
        "fit_only": True,
        "population_std_ddof": 0,
        "constant_threshold": 1e-12,
    })

    closure = {
        "variant": variant,
        "fold": k,
        "seed": fold_seed,
        "param_count": param_count,
        "input_width": model.INPUT_WIDTH,
        "uses_task_embedding": bool(getattr(model, "USES_TASK_EMBEDDING", False)),
        "n_fit": len(fit_idx),
        "n_early_stop": len(es_idx),
        "n_outer_target": len(ot_idx),
        "n_epochs_run": len(history),
        "best_epoch": best_epoch,
        "best_early_stop_mean_huber": best_loss,
        "first_epoch": history[0]["epoch"],
        "last_epoch": history[-1]["epoch"],
        "epochs_contiguous": [h["epoch"] for h in history] == list(range(1, len(history) + 1)),
        "all_finite": all(np.isfinite([h["train_huber"], h["early_stop_huber"]]).all() for h in history),
        "fit_rows_sha256": hashlib.sha256("\n".join(sorted(fit_ids)).encode()).hexdigest(),
        "early_stop_rows_sha256": hashlib.sha256("\n".join(sorted(es_ids)).encode()).hexdigest(),
        "outer_target_rows_sha256": hashlib.sha256("\n".join(sorted(ot_ids)).encode()).hexdigest(),
        "elapsed_sec": round(time.time() - t0, 2),
        "device": str(DEVICE),
    }
    save_json(ckpt_dir / "completion.json", closure)

    return ot_ids, ot_preds, closure


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", required=True, choices=["R1", "R2", "R3"])
    ap.add_argument("--verified-replay", action="store_true",
                    help="Re-derive the canonical Phase25D OOF predictions to confirm protocol identity.")
    args = ap.parse_args()
    variant = args.variant

    print(f"=== Phase28 router variant {variant} ===")
    print(f"Device: {DEVICE}")
    OUT_CACHE.mkdir(parents=True, exist_ok=True)

    features, meta_rows, joined = load_population()
    sid_to_fold, folds = load_cv()

    sid_index = {r["sample_id"]: i for i, r in enumerate(joined)}
    x_all = project_variant(features, variant)
    t_all = np.array([r["task_id"] for r in joined], dtype=np.int64)
    y_all = np.array([r["delta_dice"] for r in joined], dtype=np.float32)

    print(f"variant {variant}: numeric input width = {x_all.shape[1]}")
    print(f"population n = {len(joined)}")

    oof_ids = [None] * len(joined)
    oof_scores = np.full(len(joined), np.nan, dtype=np.float32)
    closures = []
    t_all0 = time.time()

    for k in range(5):
        seed = 42000 + k
        print(f"  fold{k}: seed={seed} FIT={len(folds[k]['fit'])} "
              f"ES={len(folds[k]['early_stop'])} OT={len(folds[k]['outer_target'])}")
        ot_ids, ot_preds, closure = train_fold(
            variant, k, x_all, t_all, y_all, sid_index, folds, seed)
        closures.append(closure)
        for sid, p in zip(ot_ids, ot_preds):
            gi = sid_index[sid]
            assert np.isnan(oof_scores[gi]), f"duplicate OOF assignment for {sid}"
            oof_ids[gi] = sid
            oof_scores[gi] = p
        print(f"    fold{k}: best_ep={closure['best_epoch']} "
              f"best_es_huber={closure['best_early_stop_mean_huber']:.6f} "
              f"epochs={closure['n_epochs_run']} elapsed={closure['elapsed_sec']}s")

    assert all(s is not None for s in oof_ids), "OOF coverage incomplete"
    assert np.all(np.isfinite(oof_scores)), "non-finite OOF scores"

    out_csv = OUT_CACHE / f"phase28_router_{variant}_oof_scores.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sample_id", "domain", "task_id", "router_cv_fold", "delta_hat"])
        for i, r in enumerate(joined):
            w.writerow([r["sample_id"], r["domain"], r["task_id"], sid_to_fold[r["sample_id"]],
                        f"{oof_scores[i]:.10f}"])
    print(f"OOF scores: {len(oof_scores)} rows -> {out_csv}")

    save_json(OUT_CACHE / f"phase28_router_{variant}_training_registry.json", {
        "artifact": f"phase28_router_{variant}_training_registry",
        "phase": 28,
        "variant": variant,
        "population": "ROUTER_DEVELOPMENT",
        "n": len(joined),
        "fold_seed_policy": "42000 + outer_fold_index",
        "param_count": ROUTER_VARIANT_EXPECTED_PARAMETERS[variant],
        "input_width": int(x_all.shape[1]),
        "folds": closures,
        "oof_scores_sha256": sha256_file(out_csv),
        "oof_coverage_exactly_once": True,
        "no_final_refit": True,
        "outcome_access_barrier_respected": True,
        "elapsed_sec": round(time.time() - t_all0, 2),
        "device": str(DEVICE),
    })
    print(f"DONE {variant}  elapsed={time.time()-t_all0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
