"""Training provenance figures for UNet++ (Phase 10 history)."""
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

ROOT = Path(__file__).resolve().parents[2]
T = ROOT / "experiments/phase10_kub_unetpp_seed42_512"
F = ROOT / "reports/figures/phase11_kub_failure_analysis"
F.mkdir(parents=True, exist_ok=True)
sns.set_theme(style="whitegrid")

def emit(fig, stem):
    for ext in ("png", "svg", "pdf"):
        fig.savefig(F / f"{stem}.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)

df = pd.read_csv(T / "history.csv")
best_epoch = 77
stop_epoch = 92

# 1. Training and Validation Loss Curves
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(df.epoch, df.train_loss, label="Train Loss", color="#4C72B0", lw=2)
ax.plot(df.epoch, df.val_loss, label="VAL Loss", color="#DD8452", lw=2)
ax.axvline(best_epoch, color="#55A868", ls="--", lw=1.5, label=f"Best Epoch ({best_epoch})")
ax.axvline(stop_epoch, color="#C44E52", ls=":", lw=1.5, label=f"Early Stop ({stop_epoch})")
ax.set_xlabel("Epoch"); ax.set_ylabel("Loss (BCE + Dice)"); ax.set_title("UNet++ Training & Validation Loss Provenance")
ax.legend(); emit(fig, "phase11_unetpp_training_loss_provenance")

# 2. Validation Macro Dice Curve
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(df.epoch, df.val_dice, color="#55A868", lw=2, label="VAL Macro Dice")
ax.axvline(best_epoch, color="#C44E52", ls="--", lw=1.5, label=f"Best Epoch ({best_epoch}: 0.7625)")
ax.set_ylim(0.3, 0.82); ax.set_xlabel("Epoch"); ax.set_ylabel("VAL Macro Dice")
ax.set_title("UNet++ Validation Macro Dice Provenance"); ax.legend(); emit(fig, "phase11_unetpp_val_dice_provenance")

# 3. Learning Rate Curve
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(df.epoch, df.learning_rate, color="#8172B2", lw=2, label="CosineAnnealingLR")
ax.set_xlabel("Epoch"); ax.set_ylabel("Learning Rate"); ax.set_title("UNet++ Learning Rate Schedule Provenance")
ax.legend(); emit(fig, "phase11_unetpp_lr_provenance")

print("UNet++ training provenance figures successfully generated.")
