"""Build deterministic Phase25D figures."""
import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path("D:/Softfors/jup")
REPORTS = ROOT / "reports"
EXP = ROOT / "experiments/phase25d_barr_benefit_router_v1_2_1_seed42"
OUT = ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1"

plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 150})

def read_history(fold):
    rows = []
    with open(EXP / f"fold{fold}" / "history.csv", "r", newline="") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows

# 1. CV training Huber curves
fig, ax = plt.subplots(figsize=(10, 6))
for k in range(5):
    hist = read_history(k)
    epochs = [int(r["epoch"]) for r in hist]
    train_h = [float(r["train_huber"]) for r in hist]
    ax.plot(epochs, train_h, label=f"Fold {k}", alpha=0.7)
ax.set_xlabel("Epoch")
ax.set_ylabel("Train Huber Loss")
ax.set_title("Phase25D CV Training Huber Curves")
ax.legend()
fig.savefig(REPORTS / "figures/p25d_cv_training_huber_curves.png", bbox_inches="tight")
plt.close(fig)

# 2. CV early-stop Huber curves
fig, ax = plt.subplots(figsize=(10, 6))
for k in range(5):
    hist = read_history(k)
    epochs = [int(r["epoch"]) for r in hist]
    es_h = [float(r["early_stop_huber"]) for r in hist]
    ax.plot(epochs, es_h, label=f"Fold {k}", alpha=0.7)
ax.set_xlabel("Epoch")
ax.set_ylabel("Early-Stop Huber Loss")
ax.set_title("Phase25D CV Early-Stop Huber Curves")
ax.legend()
fig.savefig(REPORTS / "figures/p25d_cv_early_stop_huber_curves.png", bbox_inches="tight")
plt.close(fig)

# 3. Best epoch summary
closures = [json.load(open(EXP / f"fold{k}" / "training_closure.json")) for k in range(5)]
best_epochs = [c["best_epoch"] for c in closures]
fig, ax = plt.subplots(figsize=(6, 4))
ax.bar(range(5), best_epochs, color="steelblue")
ax.set_xticks(range(5))
ax.set_xticklabels([f"Fold {k}" for k in range(5)])
ax.set_ylabel("Best Epoch")
ax.set_title(f"Best Epoch per Fold (Median = {sorted(best_epochs)[2]})")
for i, v in enumerate(best_epochs):
    ax.text(i, v + 3, str(v), ha="center", va="bottom")
fig.savefig(REPORTS / "figures/p25d_cv_best_epoch_summary.png", bbox_inches="tight")
plt.close(fig)

# 4. Predicted vs true delta
oof_rows = []
with open(OUT / "phase25d_oof_router_predictions.csv", "r", newline="") as f:
    for r in csv.DictReader(f):
        oof_rows.append(r)

deltas = np.array([float(r["delta_dice"]) for r in oof_rows])
preds = np.array([float(r["delta_hat_oof"]) for r in oof_rows])

fig, ax = plt.subplots(figsize=(7, 7))
ax.scatter(deltas, preds, alpha=0.3, s=8)
lim = max(abs(deltas.min()), abs(deltas.max()), abs(preds.min()), abs(preds.max()))
ax.plot([-lim, lim], [-lim, lim], "r--", lw=1)
ax.set_xlabel("True DeltaDice")
ax.set_ylabel("Predicted Delta_hat")
ax.set_title("OOF Predicted vs True DeltaDice")
fig.savefig(REPORTS / "figures/p25d_oof_predicted_vs_true_delta.png", bbox_inches="tight")
plt.close(fig)

# 5. Residual distribution
residuals = deltas - preds
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(residuals, bins=100, color="steelblue", edgecolor="white")
ax.set_xlabel("Residual (True - Predicted)")
ax.set_ylabel("Count")
ax.set_title("OOF Residual Distribution")
ax.axvline(0, color="red", linestyle="--", lw=1)
fig.savefig(REPORTS / "figures/p25d_oof_residual_distribution.png", bbox_inches="tight")
plt.close(fig)

# 6. Delta by domain
domains = [r["domain"] for r in oof_rows]
unique_domains = sorted(set(domains))
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()
for i, d in enumerate(unique_domains):
    mask = np.array([dom == d for dom in domains])
    axes[i].hist(deltas[mask], bins=50, alpha=0.5, label="True", color="blue")
    axes[i].hist(preds[mask], bins=50, alpha=0.5, label="Predicted", color="orange")
    axes[i].set_title(d)
    axes[i].legend()
fig.suptitle("DeltaDice Distribution by Domain")
fig.savefig(REPORTS / "figures/p25d_oof_delta_by_domain.png", bbox_inches="tight")
plt.close(fig)

# 7. Prediction by domain
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()
for i, d in enumerate(unique_domains):
    mask = np.array([dom == d for dom in domains])
    axes[i].scatter(deltas[mask], preds[mask], alpha=0.4, s=8)
    axes[i].plot([-lim, lim], [-lim, lim], "r--", lw=1)
    axes[i].set_xlabel("True")
    axes[i].set_ylabel("Predicted")
    axes[i].set_title(d)
fig.suptitle("Predicted vs True by Domain")
fig.savefig(REPORTS / "figures/p25d_oof_prediction_by_domain.png", bbox_inches="tight")
plt.close(fig)

# 8. Final refit training curve
final_hist = []
with open(EXP / "final" / "history.csv", "r", newline="") as f:
    for r in csv.DictReader(f):
        final_hist.append(r)
fig, ax = plt.subplots(figsize=(8, 5))
epochs = [int(r["epoch"]) for r in final_hist]
train_h = [float(r["train_huber"]) for r in final_hist]
ax.plot(epochs, train_h, color="steelblue")
ax.set_xlabel("Epoch")
ax.set_ylabel("Train Huber Loss")
ax.set_title("Final Refit Training Huber Curve")
fig.savefig(REPORTS / "figures/p25d_final_refit_training_huber_curve.png", bbox_inches="tight")
plt.close(fig)

print("All Phase25D figures created.")
