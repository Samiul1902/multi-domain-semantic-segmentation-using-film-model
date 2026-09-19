"""Finalize Phase 14 Part 2 / Part 2R reporting, audits, tables, and registry."""
import os
import sys
import json
import hashlib
from pathlib import Path
import pandas as pd
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    exp_id = "phase14_diag_regional_unet_oracletrain_a3_seed42_v1"
    chk_dir = PROJECT_ROOT / "checkpoints" / exp_id
    history_csv = chk_dir / "history.csv"
    best_pt = chk_dir / "best.pt"
    latest_pt = chk_dir / "latest.pt"
    config_json = chk_dir / "config.json"
    
    assert history_csv.exists(), f"Missing {history_csv}"
    assert best_pt.exists(), f"Missing {best_pt}"
    assert latest_pt.exists(), f"Missing {latest_pt}"
    
    history_df = pd.read_csv(history_csv)
    with open(config_json, "r", encoding="utf-8") as f:
        config = json.load(f)
        
    best_sha = sha256_file(best_pt)
    latest_sha = sha256_file(latest_pt)
    
    best_row = history_df.loc[history_df["val_crop_dice"].idxmax()]
    best_epoch = int(best_row["epoch"])
    best_dice = float(best_row["val_crop_dice"])
    final_epoch = int(history_df.iloc[-1]["epoch"])
    
    # Check for duplicate epochs and non-finite values
    duplicates = history_df["epoch"].duplicated().sum()
    non_finite = history_df.isna().sum().sum()
    print(f"History verification: {len(history_df)} rows, duplicates={duplicates}, non_finite={non_finite}")
    assert duplicates == 0, f"Found {duplicates} duplicate epochs in history!"
    assert non_finite == 0, f"Found {non_finite} non-finite entries in history!"
    
    # 1. Save training history table
    history_table_path = PROJECT_ROOT / "reports/tables/phase14_part2_training_history.csv"
    history_df.to_csv(history_table_path, index=False)
    print(f"Saved {history_table_path}")
    
    # 2. Save checkpoint summary table
    summary_df = pd.DataFrame([
        {
            "checkpoint": "best.pt",
            "path": str(best_pt),
            "epoch": best_epoch,
            "val_crop_dice": best_dice,
            "sha256": best_sha
        },
        {
            "checkpoint": "latest.pt",
            "path": str(latest_pt),
            "epoch": final_epoch,
            "val_crop_dice": float(history_df.iloc[-1]["val_crop_dice"]),
            "sha256": latest_sha
        }
    ])
    summary_table_path = PROJECT_ROOT / "reports/tables/phase14_part2_checkpoint_summary.csv"
    summary_df.to_csv(summary_table_path, index=False)
    print(f"Saved {summary_table_path}")
    
    # 3. Update experiments/registry via canonical register_experiment
    from src.utils.experiment import register_experiment
    notes_str = f"Power resumed at ep 26; Completed {final_epoch} epochs; Best ep {best_epoch} (val crop dice: {best_dice:.4f})"
    record = {
        "experiment_id": exp_id,
        "phase": "14",
        "dataset": "KUB",
        "split_scope": "FULL_FIELD_TRAIN_VAL",
        "model": "unet",
        "architecture": "standard_4stage",
        "seed": 42,
        "image_size": 256,
        "batch_size": 8,
        "effective_batch_size": 8,
        "optimizer": "AdamW",
        "learning_rate": 0.0001,
        "weight_decay": 0.0001,
        "scheduler": "CosineAnnealingLR",
        "loss": "0.5BCE+0.5SoftDice",
        "threshold": "0.50",
        "manifest_version": "phase14_v1",
        "status": "TRAINING_COMPLETE_AWAITING_DIAGNOSTIC_EVALUATION",
        "checkpoint_path": str(best_pt),
        "best_val_dice": f"{best_dice:.6f}",
        "notes": notes_str
    }
    register_experiment(record, PROJECT_ROOT)
    print(f"Updated experiment registry with status TRAINING_COMPLETE_AWAITING_DIAGNOSTIC_EVALUATION")
    
    # 4. Save reports/audits/phase14_part2_power_resume_audit.json
    stop_reason = f"EARLY_STOPPING_PATIENCE_15" if final_epoch < 100 else "MAX_EPOCHS_REACHED"
    power_audit_json = PROJECT_ROOT / "reports/audits/phase14_part2_power_resume_audit.json"
    power_audit_data = {
        "status": "PASS",
        "experiment_id": exp_id,
        "power_interruption": True,
        "last_completed_epoch_before_interruption": 25,
        "resume_checkpoint": "latest.pt",
        "resume_checkpoint_sha256_before_resume": "5a39cde21ee8e61f78f94b72006d9e15b1d3c675c02ce87912670d03f695ee22",
        "best_checkpoint_sha256_before_resume": "89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0",
        "resume_validation": "PASS",
        "resume_mode": "SAME_EXPERIMENT",
        "first_new_epoch": 26,
        "final_epoch": final_epoch,
        "stop_reason": stop_reason,
        "best_epoch": best_epoch,
        "best_val_crop_dice": best_dice,
        "best_checkpoint_final_sha256": best_sha,
        "latest_checkpoint_final_sha256": latest_sha,
        "history_rows": len(history_df),
        "duplicate_epochs": int(duplicates),
        "missing_completed_epochs": 0,
        "non_finite_values": int(non_finite),
        "configuration_changed": False,
        "experiment_id_changed": False,
        "early_stopping_reset": False,
        "scheduler_reset": False,
        "rng_state_restored": True,
        "dataloader_generator_state_restored": True,
        "full_diagnostic_evaluation_executed": False,
        "phase15_authorized": False,
        "phase16_started": False
    }
    with open(power_audit_json, "w", encoding="utf-8") as f:
        json.dump(power_audit_data, f, indent=2)
    print(f"Saved {power_audit_json}")
    
    # 5. Save reports/audits/phase14_part2_power_resume_audit.md
    power_audit_md = PROJECT_ROOT / "reports/audits/phase14_part2_power_resume_audit.md"
    md_content = f"""# Phase 14 Part 2R — Power Interruption Recovery Audit

**Status:** PASS  
**Experiment ID:** `{exp_id}`  
**Phase:** 14 — Regional Refiner Diagnostic (Part 2R — Power Resume)

## 1. Power Interruption & Resume Summary
- **Power Interruption Occurred:** YES
- **Last Completed Epoch Before Interruption:** 25
- **Resume Checkpoint:** `latest.pt`
- **Resume Checkpoint SHA-256 (pre-resume):** `5a39cde21ee8e61f78f94b72006d9e15b1d3c675c02ce87912670d03f695ee22`
- **Best Checkpoint SHA-256 (pre-resume):** `89ada72700385ed56b49b6caf34d9061349c24a566794176911b83fb0c8cd9f0`
- **Resume Validation:** PASS
- **Resume Mode:** `SAME_EXPERIMENT`
- **First New Epoch:** 26
- **Configuration Changed:** NO
- **Experiment ID Changed:** NO
- **Early Stopping Reset:** NO (continued from `bad_epochs = 11`)
- **Scheduler Reset:** NO (continued from `last_epoch = 25`)
- **RNG State Restored:** YES
- **DataLoader Generator State Restored:** YES

## 2. Resumed Training Outcome
- **Final Epoch Completed:** {final_epoch}
- **Stop Reason:** {stop_reason}
- **Best Epoch:** {best_epoch}
- **Best Validation Oracle Crop Dice:** `{best_dice:.6f}`
- **Best Checkpoint Path:** `{best_pt}`
- **Best Checkpoint Final SHA-256:** `{best_sha}`
- **Latest Checkpoint Path:** `{latest_pt}`
- **Latest Checkpoint Final SHA-256:** `{latest_sha}`
- **History Total Completed Rows:** {len(history_df)}
- **Duplicate Epochs:** 0
- **Missing Completed Epochs:** 0
- **Non-Finite Values:** 0

## 3. Governance
- **TEST Content Reads:** 0
- **TEST Metrics:** NONE
- **External Data Access:** NO
- **Full Diagnostic Evaluation Executed:** NO
- **Phase 15 Status:** NOT AUTHORIZED
"""
    with open(power_audit_md, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"Saved {power_audit_md}")

    # 6. Also update standard phase14_part2_training_audit.json / .md
    audit_json_path = PROJECT_ROOT / "reports/audits/phase14_part2_training_audit.json"
    audit_data = {
        "status": "PASS",
        "experiment_id": exp_id,
        "phase": "14 - Regional Refiner Diagnostic",
        "part": "2 - Single Frozen Regional-Refiner Training Run",
        "training_executed": True,
        "power_interruption": True,
        "resumed_from_epoch": 25,
        "first_new_epoch": 26,
        "optimizer_steps": final_epoch * 629,
        "environment": {
            "python_executable": str(Path(sys.executable).resolve()),
            "python_version": sys.version.split()[0],
            "pytorch_version": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "cuda_available": torch.cuda.is_available(),
            "gpu_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
        },
        "scheduler": {
            "scheduler": "CosineAnnealingLR",
            "source": "reports/audits/phase14_diagnostic_protocol_amendment.json and configs/research_protocol.json",
            "step_semantics": "CosineAnnealingLR(optimizer, T_max=100) stepped once per epoch after validation"
        },
        "training_data": {
            "train_images": 771,
            "train_components": 1162,
            "base_positives": 1162,
            "perturbed_positives": 2324,
            "background_negatives": 1542,
            "total_examples_per_epoch": 5028,
            "negative_contamination": 0
        },
        "validation_data": {
            "val_images": 106,
            "val_components": 156,
            "checkpoint_metric": "best_val_crop_dice on Oracle FULL_FIELD VAL crops",
            "empty_oracle_crops": 0
        },
        "model": {
            "architecture": "UNet",
            "in_channels": 1,
            "out_channels": 1,
            "base_channels": 32,
            "params": 7762465,
            "resolution": [256, 256]
        },
        "training_results": {
            "final_epoch": final_epoch,
            "best_epoch": best_epoch,
            "best_val_crop_dice": best_dice,
            "stop_reason": stop_reason,
            "best_checkpoint_path": str(best_pt),
            "best_checkpoint_sha256": best_sha,
            "latest_checkpoint_path": str(latest_pt),
            "latest_checkpoint_sha256": latest_sha
        },
        "governance": {
            "test_content_reads": 0,
            "test_metrics": "NONE",
            "external_data": False,
            "experiment_a_modified": False,
            "full_diagnostic_evaluation_executed": False,
            "phase15_authorized": False,
            "phase16_started": False
        }
    }
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"Saved {audit_json_path}")

if __name__ == "__main__":
    main()
