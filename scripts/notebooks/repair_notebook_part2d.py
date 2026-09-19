"""Rebuild notebook 13 with all Part 2D repairs."""
import json
from pathlib import Path
import nbformat as nbf
from nbformat.v4 import new_markdown_cell, new_code_cell

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NB_PATH = PROJECT_ROOT / "notebooks/13_phase14_regional_refiner_diagnostic.ipynb"

def main():
    with open(NB_PATH, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)
        
    # Cell 0: Relabel stale pretraining statement as historical Part 1B
    cell0_content = """# Phase 14 Regional Refiner Diagnostic - Part 1B Implementation
**PART 1B -- PRE-TRAINING IMPLEMENTATION PREFLIGHT**
*Historical state at time of Part 1B: PHASE 14 TRAINING HAD NOT YET BEEN EXECUTED*"""
    nb.cells[0] = new_markdown_cell(cell0_content)
    
    # Retain cells 0 through 12 (Part 1B preflight, pytest, CUDA preflight, real mini-pipelines)
    base_cells = nb.cells[:13]
    
    # Part 2 / 2C / 2D Cells
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
- **TRAINING VALIDITY:** `VALID_SAME_EXPERIMENT`
- **CURRENT STATUS:** PART 2 TRAINING COMPLETE; FULL DIAGNOSTIC EVALUATION NOT YET EXECUTED
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

        new_markdown_cell("## 2. Training History, Convergence Curves & History Invariant Assertions"),
        new_code_cell("""import matplotlib.pyplot as plt
import pandas as pd

history_path = chk_dir / "history.csv"
history_df = pd.read_csv(history_path)

# Strict History Invariant Assertions
print(f"Total Completed Epochs: {len(history_df)}")
assert len(history_df) == 29, f"Expected 29 rows, got {len(history_df)}"
assert int(history_df["epoch"].min()) == 1, f"Min epoch expected 1, got {history_df['epoch'].min()}"
assert int(history_df["epoch"].max()) == 29, f"Max epoch expected 29, got {history_df['epoch'].max()}"
assert len(history_df["epoch"].unique()) == 29, "Duplicate epochs found in history!"
assert set(history_df["epoch"]) == set(range(1, 30)), "Missing epochs in history sequence!"
assert history_df.isna().sum().sum() == 0, "Non-finite values found in history!"

best_row = history_df.loc[history_df["val_crop_dice"].idxmax()]
best_ep = int(best_row['epoch'])
best_score = float(best_row['val_crop_dice'])
print(f"Best Epoch: {best_ep}")
print(f"Best Validation Crop Dice: {best_score:.6f}")
assert best_ep == 14, f"Expected best epoch 14, got {best_ep}"
assert abs(best_score - 0.8437233057743712) < 1e-12, f"Unexpected best score: {best_score}"

# Verify bad_epochs progression for resumed epochs 25-29
bad_epochs_25_29 = list(history_df.loc[history_df["epoch"] >= 25, "bad_epochs"])
print(f"Epochs 25-29 bad_epochs sequence: {bad_epochs_25_29}")
assert bad_epochs_25_29 == [11, 12, 13, 14, 15], f"Unexpected bad_epochs progression: {bad_epochs_25_29}"
assert history_df.loc[history_df["epoch"] == 29, "val_crop_dice"].values[0] < best_score
assert not bool(history_df.loc[history_df["epoch"] == 29, "improved"].values[0])

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

        new_markdown_cell("""## 3. Final Checkpoint Verification & Integrity (best.pt and latest.pt)
> **Important State Distinction:**  
> - `best.pt` was saved when epoch 14 established the top validation score (`bad_epochs = 0` at save time).  
> - `latest.pt` represents the final termination state at epoch 29 following 15 consecutive unimproved epochs (`bad_epochs = 15`, `stopped = True`).
"""),
        new_code_cell("""import hashlib
import torch

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

print(f"best.pt SHA-256: {best_sha}")
print(f"latest.pt SHA-256: {latest_sha}")

assert best_sha == "89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0"
assert latest_sha == "7cb4eb5c8316b1d6e2dba90ace9b49fea30432a4f825d515b7be15e79f80c5af"

# --- Verify best.pt ---
best_ckpt = torch.load(best_pt, map_location='cpu', weights_only=False)
print(f"best.pt: epoch={best_ckpt['epoch']}, score={best_ckpt['best_validation_score']}")
assert best_ckpt["epoch"] == 14
assert abs(best_ckpt["best_validation_score"] - 0.8437233057743712) < 1e-12

# --- Verify latest.pt ---
latest_ckpt = torch.load(latest_pt, map_location='cpu', weights_only=False)
print(f"latest.pt: epoch={latest_ckpt['epoch']}, global_step={latest_ckpt['global_step']}")
assert latest_ckpt["epoch"] == 29
assert latest_ckpt["experiment_id"] == "phase14_diag_regional_unet_oracletrain_a3_seed42_v1"
assert latest_ckpt["seed"] == 42
assert latest_ckpt["global_step"] == 18241  # 29 * 629
assert abs(latest_ckpt["best_validation_score"] - 0.8437233057743712) < 1e-12

early_state = latest_ckpt["early_stopping_state"]
print(f"latest.pt early_stopping_state: {early_state}")
assert early_state["best_epoch"] == 14
assert early_state["bad_epochs"] == 15
assert early_state["patience"] == 15
assert early_state["stopped"] is True

# Verify presence and non-empty validity of required state dictionaries
for key in ['model_state', 'optimizer_state', 'scheduler_state', 'grad_scaler_state', 
            'random_state', 'loader_generator_states', 'configuration', 'training_history']:
    assert key in latest_ckpt and latest_ckpt[key] is not None, f"Missing or empty key in latest.pt: {key}"
print("All best.pt and latest.pt integrity assertions passed.")
"""),

        new_markdown_cell("""## 4. PART 2C -- SOURCE CONTINUITY AUDIT
Executable verification of the formal training closure and provenance audit artifact.
"""),
        new_code_cell("""closure_audit_path = Path("../reports/audits/phase14_part2_final_training_closure.json")
assert closure_audit_path.exists(), f"Missing closure audit at {closure_audit_path}"

with open(closure_audit_path, "r", encoding="utf-8") as f:
    closure_data = json.load(f)

print("Training Validity Decision:", closure_data["training_validity_decision"])
assert closure_data["training_validity_decision"] == "VALID_SAME_EXPERIMENT"

prov = closure_data["provenance_investigation"]
print("Scientific Training Semantics Changed:", prov["scientific_training_semantics_changed"])
assert prov["scientific_training_semantics_changed"] is False

print("Initial Trainer SHA-256:", prov["trainer_sha256_initial"])
assert prov["trainer_sha256_initial"] == "21090b6753d9aaf07240ae8414a5b35c5a509765f5398e967de7fd778af94cff"

print("Resumed Trainer SHA-256:", prov["trainer_sha256_resumed"])
assert prov["trainer_sha256_resumed"] == "b3824384b1bd1e7e0e0e45b3ae732c2460a49cc64f8df00f24619b00be13ee79"

cont = closure_data["continuity_verifications"]
print("Configuration Continuity:", cont["configuration_continuity"])
assert cont["configuration_continuity"] == "PASS"

print("Global Step Continuity:", cont["global_step_continuity"])
assert cont["global_step_continuity"] == "PASS"
assert cont["actual_final_global_step"] == 18241

print("Early-Stop Continuity:", cont["early_stop_continuity"])
assert cont["early_stop_continuity"] == "PASS"

print("Scheduler Continuity:", cont["scheduler_continuity"])
assert cont["scheduler_continuity"] == "PASS"

print("Source continuity audit verified successfully.")
"""),

        new_markdown_cell("""## 5. Notebook Current Status & Governance
- **PHASE 14 PART 1:** IMPLEMENTATION/PREFLIGHT COMPLETE
- **PHASE 14 PART 2:** TRAINING COMPLETE
- **POWER INTERRUPTION:** YES
- **SAME EXPERIMENT RESUME:** VALIDATED
- **FINAL EPOCH:** 29
- **STOP:** `EARLY_STOPPING_PATIENCE_15`
- **BEST EPOCH:** 14
- **BEST VAL CROP DICE:** 0.8437233057743712
- **TRAINING VALIDITY:** `VALID_SAME_EXPERIMENT`
- **FULL ORACLE/PREDICTED DIAGNOSTIC EVALUATION:** NOT YET EXECUTED
- **PHASE 14 COMPLETE:** NO
- **PHASE 15:** NOT AUTHORIZED
""")
    ]
    
    nb.cells = base_cells + part2_cells
    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Successfully repaired {NB_PATH} (Total cells: {len(nb.cells)})")

if __name__ == "__main__":
    main()

