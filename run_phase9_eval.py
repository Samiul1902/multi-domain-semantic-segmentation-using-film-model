import sys
import json
import time
import hashlib
import datetime
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import yaml
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock
from src.utils.reproducibility import set_seed
from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.data.loaders import create_loader
from src.models.factory import create_model
from src.losses.segmentation import BCEDiceLoss
from src.metrics.segmentation import binary_metrics, aggregate_binary_metrics, hd95
from src.metrics.object_metrics import object_metrics
from src.utils.checkpointing import load_training_checkpoint
from src.utils.experiment import register_experiment
from src.analysis.kub_object_size import stratum_for_ratio
from scripts.training.train_kub_baseline import evaluate_and_finalize, generate_reports_and_artifacts, get_file_sha256

def main():
    print("=== RUNNING PHASE 9 EVALUATION AND REPORT GENERATION ===")
    verify_manifests()
    verify_test_lock(PROJECT_ROOT)

    config_path = PROJECT_ROOT / "configs" / "kub" / "unet_baseline.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seed = config["training"]["seed"]
    set_seed(seed, deterministic=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    exp_id = "phase9_kub_unet_baseline_seed42_512"
    exp_dir = PROJECT_ROOT / "experiments" / exp_id
    chk_dir = PROJECT_ROOT / "checkpoints" / exp_id
    tables_dir = PROJECT_ROOT / "reports" / "tables"
    figures_dir = PROJECT_ROOT / "reports" / "figures" / "phase9_unet_baseline"
    qual_dir = PROJECT_ROOT / "reports" / "qualitative" / "phase9_unet_baseline"
    audit_dir = PROJECT_ROOT / "reports" / "audits"

    figures_dir.mkdir(parents=True, exist_ok=True)
    qual_dir.mkdir(parents=True, exist_ok=True)

    val_transform = SegmentationTransform(config["input_resolution"], train=False)
    val_ds = KUBDataset(PROJECT_ROOT / "manifests" / "val.csv", "VAL", val_transform, tables_dir / "kub_val_samples_sized.csv")

    model = create_model("unet", in_channels=config["model"]["input_channels"], out_channels=config["model"]["output_channels"], base_channels=config["model"]["base_channels"]).to(device)

    latest_state = torch.load(chk_dir / "latest.pt", map_location="cpu", weights_only=False)
    best_state = torch.load(chk_dir / "best.pt", map_location="cpu", weights_only=False)
    history = latest_state["training_history"]
    best_epoch = int(best_state["epoch"])
    best_val_dice = float(best_state["best_validation_score"])
    early_state = latest_state.get("early_stopping_state") or {}
    bad_epochs = int(early_state.get("bad_epochs", latest_state["epoch"] - best_epoch))
    early_stopped = bad_epochs >= config["training"]["early_stopping_patience"]
    total_duration = float(sum(row.get("epoch_seconds", 0.0) for row in history))

    manifest_meta = json.loads((PROJECT_ROOT / "manifests" / "manifest_metadata.json").read_text(encoding="utf-8"))

    reg_record = {
        "experiment_id": exp_id,
        "phase": 9,
        "dataset": "KUB",
        "split_scope": "TRAIN/VAL",
        "model": config["model"]["name"],
        "architecture": "standard_unet_4_stage",
        "seed": seed,
        "image_size": config["input_resolution"],
        "batch_size": config["training"]["batch_size"],
        "effective_batch_size": config["training"]["effective_batch_size"],
        "optimizer": config["optimizer"]["name"],
        "learning_rate": config["optimizer"]["learning_rate"],
        "weight_decay": config["optimizer"]["weight_decay"],
        "scheduler": config["scheduler"]["name"],
        "loss": "0.5_BCE+0.5_Dice",
        "threshold": config["training"]["threshold"],
        "manifest_version": "phase4_v2",
        "status": "COMPLETED",
        "start_time": "2026-09-14T03:09:38.075888+00:00",
        "end_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "checkpoint_path": str(chk_dir / "best.pt"),
        "best_val_dice": best_val_dice,
        "git_commit": "",
        "notes": "Phase 9 baseline training completed"
    }

    eval_res = evaluate_and_finalize(exp_id, exp_dir, chk_dir, tables_dir, figures_dir, qual_dir, audit_dir, config, seed, device, val_ds, model, history, best_epoch, best_val_dice, early_stopped, total_duration, manifest_meta, reg_record)
    generate_reports_and_artifacts(exp_id, exp_dir, chk_dir, tables_dir, figures_dir, qual_dir, audit_dir, config, seed, device, val_ds, model, history, best_epoch, best_val_dice, early_stopped, total_duration, manifest_meta, reg_record, *eval_res)

    print("Phase 9 evaluation and reporting successfully finalized.")

if __name__ == "__main__":
    main()
