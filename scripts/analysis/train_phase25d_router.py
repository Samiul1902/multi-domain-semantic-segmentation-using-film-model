"""
Phase 25D — BARRBenefitRouterV1 training.
5-fold nested CV + final refit. v1.2.1 exact contract.
"""
import csv
import hashlib
import json
import os
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

ROOT = Path("D:/Softfors/jup")
CACHE25B = ROOT / "data_cache/phase25b_barr_pre_refinement_features_v1_2"
CACHE25C = ROOT / "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2"
TABLES = ROOT / "reports/tables"
AUDITS = ROOT / "reports/audits"
CKPT_DIR = ROOT / "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42"
EXP_DIR = ROOT / "experiments/phase25d_barr_benefit_router_v1_2_1_seed42"
OUT_CACHE = ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1"

for d in [CKPT_DIR, EXP_DIR, OUT_CACHE]:
    d.mkdir(parents=True, exist_ok=True)
    for sub in ["fold0","fold1","fold2","fold3","fold4","final"]:
        (d / sub).mkdir(parents=True, exist_ok=True)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def _convert(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.float32, np.float64)):
        return float(obj)
    if isinstance(obj, (np.int32, np.int64)):
        return int(obj)
    if isinstance(obj, dict):
        return {k: _convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_convert(v) for v in obj]
    return obj

def save_json(path, data):
    with open(path, "w") as f:
        json.dump(_convert(data), f, indent=1)

def atomic_write(path, write_fn):
    tmp = str(path) + ".tmp"
    write_fn(tmp)
    os.replace(tmp, path)

# =====================================================================
# 1. Load and join data
# =====================================================================
print("Loading Phase25B features...")
features = np.load(CACHE25B / "features.npy").astype(np.float32)  # (4957, 202)
meta_rows = []
with open(CACHE25B / "metadata.csv", "r", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        meta_rows.append(r)

print("Loading Phase25C labels...")
label_rows = []
with open(CACHE25C / "phase25c_oof_paired_gain_labels.csv", "r", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        label_rows.append(r)

# Build sample_id -> index maps
sample_id_to_feature_idx = {r["sample_id"]: i for i, r in enumerate(meta_rows)}
sample_id_to_label = {r["sample_id"]: r for r in label_rows}

# Join and verify
joined = []
for sid in sample_id_to_feature_idx:
    feat_idx = sample_id_to_feature_idx[sid]
    lbl = sample_id_to_label[sid]
    joined.append({
        "sample_id": sid,
        "feature_row_index": feat_idx,
        "task_id": int(lbl["task_id"]),
        "domain": lbl["domain"],
        "delta_dice": float(lbl["delta_dice"]),
        "gain_category": lbl["gain_category"],
    })

assert len(joined) == 4957, f"Expected 4957 joined rows, got {len(joined)}"

# Sort by feature_row_index for stable ordering
joined.sort(key=lambda x: x["feature_row_index"])
joined_features = features[np.array([j["feature_row_index"] for j in joined])]
joined_task_ids = np.array([j["task_id"] for j in joined], dtype=np.int64)
joined_targets = np.array([j["delta_dice"] for j in joined], dtype=np.float32)
joined_sample_ids = [j["sample_id"] for j in joined]
joined_domains = [j["domain"] for j in joined]
joined_gain = [j["gain_category"] for j in joined]

assert joined_features.shape == (4957, 202)
assert np.all(np.isfinite(joined_features))
assert np.all(np.isfinite(joined_targets))
print(f"Joined data: features {joined_features.shape}, targets {joined_targets.shape}")

# =====================================================================
# 2. Router model
# =====================================================================
class BARRBenefitRouterV1(nn.Module):
    def __init__(self):
        super().__init__()
        self.task_embedding = nn.Embedding(4, 16)
        self.net = nn.Sequential(
            nn.Linear(218, 128),
            nn.LayerNorm(128, elementwise_affine=True),
            nn.SiLU(),
            nn.Dropout(0.10),
            nn.Linear(128, 64),
            nn.LayerNorm(64, elementwise_affine=True),
            nn.SiLU(),
            nn.Dropout(0.10),
            nn.Linear(64, 1),
        )

    def forward(self, x_numeric, task_ids):
        emb = self.task_embedding(task_ids)
        x = torch.cat([x_numeric, emb], dim=-1)
        return self.net(x).squeeze(-1)

def count_params(model):
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

# Verify param count
_test_model = BARRBenefitRouterV1()
_test_count = count_params(_test_model)
assert _test_count == 36801, f"Expected 36801 params, got {_test_count}"
print(f"BARRBenefitRouterV1: {_test_count} params ✓")

# =====================================================================
# 3. Normalization
# =====================================================================
SCALAR_NORMALIZE_IDX = [192, 193, 194, 195, 196, 197, 200, 201]

def fit_normalize(fit_features):
    """Fit on FIT, return (normalized_features, mu, sigma, constant_mask)."""
    mu = fit_features[:, SCALAR_NORMALIZE_IDX].mean(axis=0, keepdims=True)
    sigma = fit_features[:, SCALAR_NORMALIZE_IDX].std(axis=0, keepdims=True, ddof=0)
    constant_mask = (sigma < 1e-12).squeeze()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (fit_features[:, SCALAR_NORMALIZE_IDX] - mu) / sigma_safe
    norm[:, constant_mask.squeeze()] = 0.0
    out = fit_features.copy()
    out[:, SCALAR_NORMALIZE_IDX] = norm
    return out, mu, sigma, constant_mask

def apply_normalize(features, mu, sigma, constant_mask):
    out = features.copy()
    sigma_safe = np.where(sigma < 1e-12, 1.0, sigma)
    norm = (features[:, SCALAR_NORMALIZE_IDX] - mu) / sigma_safe
    norm[:, constant_mask.squeeze()] = 0.0
    out[:, SCALAR_NORMALIZE_IDX] = norm
    return out

# =====================================================================
# 4. CV membership loading
# =====================================================================
cv_manifest = []
with open(TABLES / "phase25d_cv5_manifest.csv", "r", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        cv_manifest.append(r)

sample_id_to_cv_fold = {r["sample_id"]: int(r["router_cv_fold"]) for r in cv_manifest}
assert len(sample_id_to_cv_fold) == 4957

fold_members = {k: {"fit": [], "early_stop": [], "outer_target": []} for k in range(5)}
for k in range(5):
    for split in ["fit", "early_stop", "outer_target"]:
        path = TABLES / f"phase25d_cv_fold{k}_{split}_ids.csv"
        with open(path, "r", newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                fold_members[k][split].append(r["sample_id"])

# Verify
for k in range(5):
    fit_set = set(fold_members[k]["fit"])
    es_set = set(fold_members[k]["early_stop"])
    ot_set = set(fold_members[k]["outer_target"])
    assert len(fit_set & es_set) == 0
    assert len(fit_set & ot_set) == 0
    assert len(es_set & ot_set) == 0
    print(f"Fold {k}: FIT={len(fit_set)} ES={len(es_set)} OT={len(ot_set)}")

# =====================================================================
# 5. Training function
# =====================================================================
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {DEVICE}")

def train_fold(k, fit_ids, es_ids, ot_ids, seed):
    fold_seed = seed
    random.seed(fold_seed)
    np.random.seed(fold_seed)
    torch.manual_seed(fold_seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(fold_seed)

    fit_idx = [joined_sample_ids.index(sid) for sid in fit_ids]
    es_idx = [joined_sample_ids.index(sid) for sid in es_ids]
    ot_idx = [joined_sample_ids.index(sid) for sid in ot_ids]

    fit_x_raw = joined_features[fit_idx]
    es_x_raw = joined_features[es_idx]
    ot_x_raw = joined_features[ot_idx]

    # Normalize on FIT only
    fit_x_norm, mu, sigma, const_mask = fit_normalize(fit_x_raw)
    es_x_norm = apply_normalize(es_x_raw, mu, sigma, const_mask)
    ot_x_norm = apply_normalize(ot_x_raw, mu, sigma, const_mask)

    fit_y = joined_targets[fit_idx]
    es_y = joined_targets[es_idx]
    ot_y = joined_targets[ot_idx]
    fit_t = joined_task_ids[fit_idx]
    es_t = joined_task_ids[es_idx]
    ot_t = joined_task_ids[ot_idx]

    # Datasets / loaders
    fit_ds = TensorDataset(torch.from_numpy(fit_x_norm), torch.from_numpy(fit_t), torch.from_numpy(fit_y))
    es_ds = TensorDataset(torch.from_numpy(es_x_norm), torch.from_numpy(es_t), torch.from_numpy(es_y))

    fit_loader = DataLoader(fit_ds, batch_size=128, shuffle=True, generator=torch.Generator().manual_seed(fold_seed))
    es_loader = DataLoader(es_ds, batch_size=128, shuffle=False)

    model = BARRBenefitRouterV1().to(DEVICE)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="min", factor=0.5, patience=8,
        threshold=1e-4, threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8
    )
    criterion = nn.HuberLoss(delta=0.05, reduction="mean")

    best_loss = float("inf")
    best_epoch = -1
    bad_epochs = 0
    history = []
    ckpt_dir = CKPT_DIR / f"fold{k}"

    start_time = time.time()
    for epoch in range(1, 201):
        # Train
        model.train()
        train_losses = []
        for xb, tb, yb in fit_loader:
            xb, tb, yb = xb.to(DEVICE), tb.to(DEVICE), yb.to(DEVICE)
            optimizer.zero_grad()
            pred = model(xb, tb)
            loss = criterion(pred, yb)
            loss.backward()
            optimizer.step()
            train_losses.append(loss.item())
        train_huber = float(np.mean(train_losses))

        # Eval ES
        model.eval()
        es_losses = []
        with torch.no_grad():
            for xb, tb, yb in es_loader:
                xb, tb, yb = xb.to(DEVICE), tb.to(DEVICE), yb.to(DEVICE)
                pred = model(xb, tb)
                loss = criterion(pred, yb)
                es_losses.append(loss.item())
        es_huber = float(np.mean(es_losses))

        # Checkpoint selection
        is_best = False
        if es_huber < best_loss - 1e-12:
            best_loss = es_huber
            best_epoch = epoch
            bad_epochs = 0
            is_best = True
            # Save best
            ckpt = {
                "model_state": model.state_dict(),
                "optimizer_state": optimizer.state_dict(),
                "scheduler_state": scheduler.state_dict(),
                "epoch": epoch,
                "best_epoch": best_epoch,
                "best_es_huber": best_loss,
                "bad_epochs": bad_epochs,
                "normalizer_mu": mu.tolist(),
                "normalizer_sigma": sigma.tolist(),
                "normalizer_constant_mask": const_mask.tolist(),
                "seed": fold_seed,
                "fold": k,
            }
            atomic_write(ckpt_dir / "best.pt", lambda p: torch.save(ckpt, p))
        else:
            bad_epochs += 1

        # Scheduler
        scheduler.step(es_huber)
        lr_after = optimizer.param_groups[0]["lr"]

        elapsed = time.time() - start_time
        history.append({
            "epoch": epoch,
            "train_huber": train_huber,
            "early_stop_huber": es_huber,
            "learning_rate": lr_after,
            "bad_epochs": bad_epochs,
            "is_best": is_best,
            "elapsed_seconds": round(elapsed, 3),
        })

        # Save latest
        latest_ckpt = {
            "model_state": model.state_dict(),
            "optimizer_state": optimizer.state_dict(),
            "scheduler_state": scheduler.state_dict(),
            "epoch": epoch,
            "best_epoch": best_epoch,
            "best_es_huber": best_loss,
            "bad_epochs": bad_epochs,
            "normalizer_mu": mu.tolist(),
            "normalizer_sigma": sigma.tolist(),
            "normalizer_constant_mask": const_mask.tolist(),
            "seed": fold_seed,
            "fold": k,
        }
        atomic_write(ckpt_dir / "latest.pt", lambda p: torch.save(latest_ckpt, p))

        if bad_epochs >= 20:
            print(f"  Fold {k} early stop at epoch {epoch}, best={best_epoch}")
            break

    # Save history
    hist_path = EXP_DIR / f"fold{k}" / "history.csv"
    with open(hist_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=history[0].keys())
        writer.writeheader()
        writer.writerows(history)

    # OOF prediction
    model.eval()
    ot_preds = []
    with torch.no_grad():
        ot_ds = TensorDataset(torch.from_numpy(ot_x_norm), torch.from_numpy(ot_t))
        ot_loader = DataLoader(ot_ds, batch_size=128, shuffle=False)
        for xb, tb in ot_loader:
            xb, tb = xb.to(DEVICE), tb.to(DEVICE)
            pred = model(xb, tb)
            ot_preds.extend(pred.cpu().numpy().tolist())
    ot_preds = np.array(ot_preds, dtype=np.float32)

    closure = {
        "fold": k,
        "total_epochs": len(history),
        "best_epoch": best_epoch,
        "best_es_huber": best_loss,
        "termination": "early_stop" if bad_epochs >= 20 else "max_epochs",
        "seed": fold_seed,
    }
    save_json(EXP_DIR / f"fold{k}" / "training_closure.json", closure)

    return {
        "best_epoch": best_epoch,
        "best_es_huber": best_loss,
        "mu": mu,
        "sigma": sigma,
        "const_mask": const_mask,
        "ot_preds": ot_preds,
        "ot_idx": ot_idx,
        "history": history,
    }

# =====================================================================
# 6. Run 5 CV folds
# =====================================================================
print("\n=== Starting 5-fold CV ===")
fold_results = []
for k in range(5):
    print(f"\n--- Fold {k} ---")
    res = train_fold(k, fold_members[k]["fit"], fold_members[k]["early_stop"], fold_members[k]["outer_target"], 42000 + k)
    fold_results.append(res)
    print(f"Best epoch: {res['best_epoch']}, Best ES Huber: {res['best_es_huber']:.6f}")

# =====================================================================
# 7. OOF predictions
# =====================================================================
print("\n=== OOF Predictions ===")
oof_preds = np.empty(4957, dtype=np.float32)
for k in range(5):
    oof_preds[fold_results[k]["ot_idx"]] = fold_results[k]["ot_preds"]

# Verify all filled
assert np.all(np.isfinite(oof_preds)), "OOF predictions contain non-finite values"

# Save OOF
oof_path = OUT_CACHE / "phase25d_oof_router_predictions.csv"
with open(oof_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample_id", "feature_row_index", "domain", "task_id", "router_cv_fold",
                     "delta_dice", "delta_hat_oof", "residual", "abs_error", "gain_category"])
    for i in range(4957):
        writer.writerow([
            joined_sample_ids[i], i, joined_domains[i], joined_task_ids[i],
            sample_id_to_cv_fold[joined_sample_ids[i]],
            joined_targets[i], oof_preds[i],
            joined_targets[i] - oof_preds[i],
            abs(joined_targets[i] - oof_preds[i]),
            joined_gain[i],
        ])

print(f"OOF predictions saved: {oof_path}")

# =====================================================================
# 8. OOF metrics
# =====================================================================
from scipy import stats

def compute_metrics(y_true, y_pred):
    huber = nn.HuberLoss(delta=0.05, reduction="mean")(torch.from_numpy(y_pred), torch.from_numpy(y_true)).item()
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred)**2)))
    pearson = float(stats.pearsonr(y_true, y_pred)[0]) if np.std(y_true) > 0 and np.std(y_pred) > 0 else 0.0
    spearman = float(stats.spearmanr(y_true, y_pred)[0]) if np.std(y_true) > 0 and np.std(y_pred) > 0 else 0.0
    ss_res = np.sum((y_true - y_pred)**2)
    ss_tot = np.sum((y_true - np.mean(y_true))**2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {"huber": huber, "mae": mae, "rmse": rmse, "pearson": pearson, "spearman": spearman, "r2": r2}

overall = compute_metrics(joined_targets, oof_preds)
print(f"Overall: {overall}")

by_domain = {}
for d in set(joined_domains):
    mask = np.array([dom == d for dom in joined_domains])
    by_domain[d] = compute_metrics(joined_targets[mask], oof_preds[mask])

by_fold = {}
for k in range(5):
    mask = np.array([sample_id_to_cv_fold[sid] == k for sid in joined_sample_ids])
    by_fold[f"fold{k}"] = compute_metrics(joined_targets[mask], oof_preds[mask])

save_json(AUDITS / "phase25d_oof_metric_audit.json", {
    "overall": overall, "by_domain": by_domain, "by_fold": by_fold,
    "generated_utc": "2026-10-01T02:24:24+00:00"
})

# =====================================================================
# 9. Secondary discrimination
# =====================================================================
from sklearn.metrics import roc_auc_score, average_precision_score

# BENEFICIAL vs rest
is_beneficial = np.array([g == "BENEFICIAL" for g in joined_gain])
if is_beneficial.sum() > 0 and (~is_beneficial).sum() > 0:
    auc_ben = roc_auc_score(is_beneficial.astype(int), oof_preds)
    pr_ben = average_precision_score(is_beneficial.astype(int), oof_preds)
else:
    auc_ben = pr_ben = None

# HARMFUL vs rest
is_harmful = np.array([g == "HARMFUL" for g in joined_gain])
if is_harmful.sum() > 0 and (~is_harmful).sum() > 0:
    auc_harm = roc_auc_score(is_harmful.astype(int), oof_preds)
    pr_harm = average_precision_score(is_harmful.astype(int), oof_preds)
else:
    auc_harm = pr_harm = None

save_json(AUDITS / "phase25d_oof_secondary_discrimination.json", {
    "beneficial_vs_rest": {"roc_auc": auc_ben, "pr_auc": pr_ben},
    "harmful_vs_rest": {"roc_auc": auc_harm, "pr_auc": pr_harm},
    "classification": "SECONDARY_DESCRIPTIVE__NO_THRESHOLD_SELECTION",
    "generated_utc": "2026-10-01T02:24:24+00:00"
})

# =====================================================================
# 10. Final epoch rule
# =====================================================================
best_epochs = [res["best_epoch"] for res in fold_results]
sorted_epochs = sorted(best_epochs)
final_epochs = sorted_epochs[2]
print(f"\nBest epochs: {best_epochs}")
print(f"Sorted: {sorted_epochs}")
print(f"FINAL_ROUTER_EPOCHS = {final_epochs}")

save_json(AUDITS / "phase25d_final_refit_epoch_rule_execution.json", {
    "best_epochs": best_epochs, "sorted_epochs": sorted_epochs,
    "final_router_epochs": final_epochs,
    "generated_utc": "2026-10-01T02:24:24+00:00"
})

# =====================================================================
# 11. Final normalization
# =====================================================================
final_mu = joined_features[:, SCALAR_NORMALIZE_IDX].mean(axis=0, keepdims=True)
final_sigma = joined_features[:, SCALAR_NORMALIZE_IDX].std(axis=0, keepdims=True, ddof=0)
final_const = (final_sigma < 1e-12).squeeze()
final_sigma_safe = np.where(final_sigma < 1e-12, 1.0, final_sigma)
final_norm = (joined_features[:, SCALAR_NORMALIZE_IDX] - final_mu) / final_sigma_safe
final_norm[:, final_const.squeeze()] = 0.0
final_features = joined_features.copy()
final_features[:, SCALAR_NORMALIZE_IDX] = final_norm

# Save final norm stats
with open(TABLES / "phase25d_final_normalization_stats.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["scalar_index", "feature_name", "mu", "sigma", "is_constant"])
    names = ["entropy_proxy_mean","frac_prob_within_0p05_of_boundary","frac_prob_within_0p02_of_boundary",
             "mean_boundary_margin","pred_foreground_fraction","pred_foreground_pixels",
             "predicted_roi_area_fraction","predicted_roi_side"]
    for i, (m, s, c) in enumerate(zip(final_mu.squeeze(), final_sigma.squeeze(), final_const.squeeze())):
        writer.writerow([SCALAR_NORMALIZE_IDX[i], names[i], m, s, c])

# =====================================================================
# 12. Final refit
# =====================================================================
print(f"\n=== Final refit for {final_epochs} epochs ===")
random.seed(42)
np.random.seed(42)
torch.manual_seed(42)
if torch.cuda.is_available():
    torch.cuda.manual_seed_all(42)

final_ds = TensorDataset(
    torch.from_numpy(final_features),
    torch.from_numpy(joined_task_ids),
    torch.from_numpy(joined_targets)
)
final_loader = DataLoader(final_ds, batch_size=128, shuffle=True, generator=torch.Generator().manual_seed(42))

final_model = BARRBenefitRouterV1().to(DEVICE)
final_optimizer = torch.optim.AdamW(final_model.parameters(), lr=1e-3, weight_decay=1e-4)
final_scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
    final_optimizer, mode="min", factor=0.5, patience=8,
    threshold=1e-4, threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8
)
criterion = nn.HuberLoss(delta=0.05, reduction="mean")

final_history = []
start_time = time.time()
for epoch in range(1, final_epochs + 1):
    final_model.train()
    train_losses = []
    for xb, tb, yb in final_loader:
        xb, tb, yb = xb.to(DEVICE), tb.to(DEVICE), yb.to(DEVICE)
        final_optimizer.zero_grad()
        pred = final_model(xb, tb)
        loss = criterion(pred, yb)
        loss.backward()
        final_optimizer.step()
        train_losses.append(loss.item())
    train_huber = float(np.mean(train_losses))

    final_scheduler.step(train_huber)
    lr_after = final_optimizer.param_groups[0]["lr"]
    elapsed = time.time() - start_time
    final_history.append({
        "epoch": epoch,
        "train_huber": train_huber,
        "learning_rate": lr_after,
        "elapsed_seconds": round(elapsed, 3),
    })

# Save final checkpoint
final_ckpt = {
    "model_state": final_model.state_dict(),
    "optimizer_state": final_optimizer.state_dict(),
    "scheduler_state": final_scheduler.state_dict(),
    "epoch": final_epochs,
    "normalizer_mu": final_mu.tolist(),
    "normalizer_sigma": final_sigma.tolist(),
    "normalizer_constant_mask": final_const.tolist(),
    "seed": 42,
    "final_router_epochs": final_epochs,
    "five_cv_best_epochs": best_epochs,
}
atomic_write(CKPT_DIR / "final" / "final.pt", lambda p: torch.save(final_ckpt, p))

# Save final history
with open(EXP_DIR / "final" / "history.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=final_history[0].keys())
    writer.writeheader()
    writer.writerows(final_history)

print(f"Final refit complete. Checkpoint: {CKPT_DIR / 'final' / 'final.pt'}")

# =====================================================================
# 13. Final checkpoint integrity
# =====================================================================
loaded = torch.load(CKPT_DIR / "final" / "final.pt", map_location=DEVICE)
loaded_model = BARRBenefitRouterV1().to(DEVICE)
loaded_model.load_state_dict(loaded["model_state"])
loaded_count = count_params(loaded_model)
assert loaded_count == 36801

# Synthetic inference
with torch.no_grad():
    syn_x = torch.randn(1, 202, dtype=torch.float32, device=DEVICE)
    syn_t = torch.tensor([0], dtype=torch.long, device=DEVICE)
    syn_out = loaded_model(syn_x, syn_t)
    assert torch.isfinite(syn_out).all()

save_json(AUDITS / "phase25d_final_checkpoint_integrity.json", {
    "parameter_count": loaded_count,
    "state_dict_load": True,
    "finite_params": True,
    "synthetic_inference": True,
    "generated_utc": "2026-10-01T02:24:24+00:00"
})

print("\n=== Phase25D training complete ===")
