"""Append Phase 14 Part 2/2C Training and Resume evidence to notebooks/13_phase14_regional_refiner_diagnostic.ipynb."""
import json
import hashlib
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_markdown_cell, new_code_cell

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NB_PATH = PROJECT_ROOT / "notebooks/13_phase14_regional_refiner_diagnostic.ipynb"

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    nb = nbf.read(str(NB_PATH), as_version=4)
    
    # Filter out any old Part 2 cells if previously appended
    kept_cells = []
    for c in nb.cells:
        src = "".join(c.source)
        if "# PHASE 14" in src and "PART 2" in src:
            break
        if "# Phase 14 Part 2" in src:
            break
        kept_cells.append(c)
    nb.cells = kept_cells
    
    part2_cells = [
        new_markdown_cell("---"),
        new_markdown_cell("""# PHASE 14 -- PART 2 TRAINING & POWER-INTERRUPTION RESUME
**Single Frozen Regional-Refiner Training Run**

- **Experiment ID:** `phase14_diag_regional_unet_oracletrain_a3_seed42_v1`
- **POWER INTERRUPTION OCCURRED:** YES
- **LAST COMPLETE PRE-INTERRUPTION EPOCH:** 25
- **RESUMED SAME EXPERIMENT:** YES
- **RESUMED FROM:** `latest.pt` (epoch 25)
- **FIRST NEW EPOCH:** 26
- **FINAL EPOCH:** 29
- **STOP REASON:** `EARLY_STOPPING_PATIENCE_15` (bad_epochs = 15/15)
- **BEST EPOCH:** 14
- **BEST VAL CROP DICE:** 0.8437233057743712
- **CONFIGURATION CHANGED:** NO
- **EARLY STOPPING STATE RESTORED:** YES (`bad_epochs = 11`, `best_epoch = 14`, `best_score = 0.843723`)
- **SCHEDULER STATE RESTORED:** YES (`last_epoch = 25`, LR = `8.53553e-05`)
- **AMP SCALER STATE RESTORED:** YES
- **RNG STATE RESTORED:** YES
- **DATALOADER GENERATOR STATE RESTORED:** YES
- **BEST CHECKPOINT SHA-256:** `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0`
- **FINAL LATEST CHECKPOINT SHA-256:** `7cb4eb5c8316b1d6e2dba90ace9b49fea30432a4f825d515b7be15e79f80c5af`
"""),
        
        new_markdown_cell("## 1. Frozen Training Configuration & Provenance"),
        new_code_cell("""import json
from pathlib import Path
import pandas as pd

exp_id = "phase14_diag_regional_unet_oracletrain_a3_seed42_v1"
chk_dir = Path("../checkpoints") / exp_id
config_path = chk_dir / "config.json"

with open(config_path, "r", encoding="utf-8") as f:
    config = json.load(f)

print("Experiment ID:", config["experiment_id"])
print("Architecture:", config["architecture"])
print("Trainable Parameters:", config["trainable_params"])
print("Optimizer:", config["optimizer"])
print("Learning Rate:", config["lr"])
print("Weight Decay:", config["weight_decay"])
print("Scheduler:", config["scheduler"])
print("Scheduler T_max:", config.get("scheduler_t_max", 100))
print("Loss:", config["loss"])
print("Batch Size:", config["batch_size"])
print("AMP:", config["amp"])
print("Seed:", config["seed"])
print("Early Stopping Patience:", config["patience"])
print("Checkpoint Metric:", config["checkpoint_metric"])
"""),

        new_markdown_cell("## 2. Training History & Convergence Curves (Continuous Epochs)"),
        new_code_cell("""import matplotlib.pyplot as plt

history_path = chk_dir / "history.csv"
history_df = pd.read_csv(history_path)

print(f"Total Completed Epochs: {len(history_df)}")
print(f"Epoch Range: {int(history_df['epoch'].min())} to {int(history_df['epoch'].max())}")
assert len(history_df) == len(history_df['epoch'].unique()), "Duplicate epochs found in history!"

best_row = history_df.loc[history_df["val_crop_dice"].idxmax()]
best_ep = int(best_row['epoch'])
best_score = float(best_row['val_crop_dice'])
print(f"Best Epoch: {best_ep}")
print(f"Best Validation Crop Dice: {best_score:.6f}")

fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Train Loss
axes[0].plot(history_df["epoch"], history_df["train_loss"], color="#4C72B0", lw=2, label="Train Loss")
axes[0].axvline(25.5, color="gray", linestyle=":", alpha=0.7, label="Power Resume (Ep 25/26)")
axes[0].set_title("Phase 14 Refiner Training Loss (BCE+Dice)")
axes[0].set_xlabel("Epoch")
axes[0].set_ylabel("Loss")
axes[0].grid(True, alpha=0.3)
axes[0].legend()

# Validation Crop Dice
axes[1].plot(history_df["epoch"], history_df["val_crop_dice"], color="#55A868", lw=2, label="Oracle Val Crop Dice")
axes[1].axvline(25.5, color="gray", linestyle=":", alpha=0.7, label="Power Resume (Ep 25/26)")
axes[1].axvline(best_ep, color="red", linestyle="--", alpha=0.7, label=f"Best Ep {best_ep} ({best_score:.4f})")
axes[1].set_title("Validation Oracle Crop Dice")
axes[1].set_xlabel("Epoch")
axes[1].set_ylabel("Dice")
axes[1].grid(True, alpha=0.3)
axes[1].legend()

# Learning Rate
axes[2].plot(history_df["epoch"], history_df["learning_rate"], color="#8172B2", lw=2, label="CosineAnnealingLR")
axes[2].axvline(25.5, color="gray", linestyle=":", alpha=0.7, label="Power Resume (Ep 25/26)")
axes[2].set_title("Learning Rate Schedule")
axes[2].set_xlabel("Epoch")
axes[2].set_ylabel("Learning Rate")
axes[2].grid(True, alpha=0.3)
axes[2].legend()

plt.tight_layout()
plt.show()
"""),

        new_markdown_cell("## 3. Checkpoint Verification & Integrity"),
        new_code_cell("""import hashlib

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

best_pt = chk_dir / "best.pt"
latest_pt = chk_dir / "latest.pt"

assert best_pt.exists(), "best.pt does not exist!"
assert latest_pt.exists(), "latest.pt does not exist!"

best_sha = sha256_file(best_pt)
latest_sha = sha256_file(latest_pt)

print(f"best.pt path: {best_pt.resolve()}")
print(f"best.pt SHA-256: {best_sha}")
print(f"latest.pt path: {latest_pt.resolve()}")
print(f"latest.pt SHA-256: {latest_sha}")

import torch
best_ckpt = torch.load(best_pt, map_location='cpu', weights_only=False)
print("Best checkpoint epoch:", best_ckpt["epoch"])
print("Best checkpoint score:", best_ckpt["best_validation_score"])
print("Patience / stop state:", best_ckpt.get("early_stopping_state"))
"""),

        new_markdown_cell("""## 4. Governance & Diagnostic Status
**FULL DIAGNOSTIC ORACLE/PREDICTED EVALUATION NOT YET EXECUTED**

- Training of single frozen regional refiner: COMPLETE
- Phase 14 status: `TRAINING_COMPLETE_AWAITING_DIAGNOSTIC_EVALUATION`
- Full diagnostic contrasts (Global vs Oracle vs Predicted): PENDING SUPERVISOR AUTHORIZATION
- Phase 15 status: `NOT AUTHORIZED`
- Phase 16 status: `NOT STARTED`
""")
    ]
    
    nb.cells.extend(part2_cells)
    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Appended Part 2/2C cells to {NB_PATH}")

if __name__ == "__main__":
    main()
