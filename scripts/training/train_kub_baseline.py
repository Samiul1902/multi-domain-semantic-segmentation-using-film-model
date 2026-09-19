"""Phase 9 KUB U-Net Baseline Training Entrypoint."""
import os
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

PROJECT_ROOT = Path(__file__).resolve().parents[2]
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
from src.training.trainer import Trainer, EarlyStopping
from src.utils.checkpointing import save_training_checkpoint, load_training_checkpoint
from src.utils.experiment import register_experiment
from src.analysis.kub_object_size import stratum_for_ratio

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

def get_file_sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def train_baseline():
    print("=== STARTING PHASE 9 KUB U-NET BASELINE TRAINING ===")
    verify_manifests()
    test_lock = verify_test_lock(PROJECT_ROOT)
    print("Governance checks PASS. Test lock verified.")

    config_path = PROJECT_ROOT / "configs" / "kub" / "unet_baseline.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    seed = config["training"]["seed"]
    set_seed(seed, deterministic=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA is required for Phase 9 training.")

    exp_id = "phase9_kub_unet_baseline_seed42_512"
    exp_dir = PROJECT_ROOT / "experiments" / exp_id
    exp_dir.mkdir(parents=True, exist_ok=True)
    chk_dir = PROJECT_ROOT / "checkpoints" / exp_id
    chk_dir.mkdir(parents=True, exist_ok=True)
    tables_dir = PROJECT_ROOT / "reports" / "tables"
    figures_dir = PROJECT_ROOT / "reports" / "figures" / "phase9_unet_baseline"
    qual_dir = PROJECT_ROOT / "reports" / "qualitative" / "phase9_unet_baseline"
    audit_dir = PROJECT_ROOT / "reports" / "audits"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    qual_dir.mkdir(parents=True, exist_ok=True)

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
        "status": "RUNNING",
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "end_time": "",
        "checkpoint_path": str(chk_dir / "best.pt"),
        "best_val_dice": "",
        "git_commit": "",
        "notes": "Phase 9 baseline training"
    }
    register_experiment(reg_record, PROJECT_ROOT)

    resolution = config["input_resolution"]
    train_transform = SegmentationTransform(resolution, train=True)
    val_transform = SegmentationTransform(resolution, train=False)

    train_ds = KUBDataset(PROJECT_ROOT / "manifests" / "train.csv", "TRAIN", train_transform, tables_dir / "kub_train_samples_sized.csv")
    val_ds = KUBDataset(PROJECT_ROOT / "manifests" / "val.csv", "VAL", val_transform, tables_dir / "kub_val_samples_sized.csv")

    model = create_model("unet", in_channels=config["model"]["input_channels"], out_channels=config["model"]["output_channels"], base_channels=config["model"]["base_channels"]).to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=float(config["optimizer"]["learning_rate"]), weight_decay=float(config["optimizer"]["weight_decay"]))
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config["scheduler"]["max_epochs"])
    criterion = BCEDiceLoss(bce_weight=config["loss"]["bce_weight"], dice_weight=config["loss"]["dice_weight"], epsilon=float(config["loss"]["dice_epsilon"]))
    trainer = Trainer(model, optimizer, scheduler, criterion, device, amp=config["training"]["amp"], gradient_accumulation_steps=config["training"]["gradient_accumulation_steps"], threshold=config["training"]["threshold"], patience=config["training"]["early_stopping_patience"])

    manifest_meta = json.loads((PROJECT_ROOT / "manifests" / "manifest_metadata.json").read_text(encoding="utf-8"))
    history = []
    best_val_dice = -1.0
    best_epoch = -1
    early_stopped = False
    start_epoch = 1
    train_generator_state = None
    latest_path = chk_dir / "latest.pt"
    if latest_path.exists():
        state = load_training_checkpoint(latest_path, model, optimizer, scheduler, trainer.scaler, True, device)
        if state["manifest_version"] != "phase4_v2" or state["manifest_hashes"] != manifest_meta["hashes"]:
            raise RuntimeError("Resume checkpoint manifest metadata does not match the frozen manifests")
        history = state["training_history"]
        best_val_dice = float(state["best_validation_score"])
        start_epoch = int(state["epoch"]) + 1
        trainer.global_step = int(state["global_step"])
        best_epoch = int(torch.load(chk_dir / "best.pt", map_location="cpu", weights_only=False)["epoch"])
        early_state = state.get("early_stopping_state") or {}
        trainer.early_stopping.best = float(early_state.get("best", best_val_dice))
        trainer.early_stopping.bad_epochs = int(early_state.get("bad_epochs", max(0, state["epoch"] - best_epoch)))
        train_generator_state = (state.get("loader_generator_states") or {}).get("train")

    train_loader = create_loader(train_ds, batch_size=config["training"]["batch_size"], shuffle=True, seed=seed, num_workers=config["training"]["num_workers"], pin_memory=config["training"]["pin_memory"], generator_state=train_generator_state)
    val_loader = create_loader(val_ds, batch_size=config["training"]["batch_size"], shuffle=False, seed=seed, num_workers=config["training"]["num_workers"], pin_memory=config["training"]["pin_memory"])
    if start_epoch > 1 and train_generator_state is None:
        # Legacy Phase-9 checkpoints predate persisted loader-generator state. Replay
        # completed sampler epochs without reading images to recover its exact state.
        for _ in range(start_epoch - 1):
            iterator = iter(train_loader)
            list(iterator._sampler_iter)

    start_time = time.time()
    log_file = open(exp_dir / "training.log", "a" if start_epoch > 1 else "w", encoding="utf-8")
    log_file.write(f"{'Training resumed at epoch ' + str(start_epoch) if start_epoch > 1 else 'Training started at'} {datetime.datetime.now().isoformat()}\n")
    log_file.flush()

    for epoch in range(start_epoch, config["training"]["max_epochs"] + 1):
        ep_start = time.time()
        tr_info = trainer.train_one_epoch(train_loader)
        val_info, _ = trainer.validate(val_loader)
        scheduler.step()
        ep_time = time.time() - ep_start

        peak_allocated = torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0
        peak_reserved = torch.cuda.max_memory_reserved() if torch.cuda.is_available() else 0
        current_lr = optimizer.param_groups[0]["lr"]

        epoch_rec = {
            "epoch": epoch,
            "train_loss": tr_info["loss"],
            "val_loss": val_info["loss"],
            "val_dice": val_info["dice"],
            "val_iou": val_info["iou"],
            "val_precision": val_info["precision"],
            "val_recall": val_info["recall"],
            "learning_rate": current_lr,
            "epoch_seconds": ep_time,
            "peak_gpu_allocated": peak_allocated,
            "peak_gpu_reserved": peak_reserved
        }
        history.append(epoch_rec)

        msg = f"Epoch {epoch:03d}/{config['training']['max_epochs']} | Train Loss: {tr_info['loss']:.4f} | Val Loss: {val_info['loss']:.4f} | Val Dice: {val_info['dice']:.4f} | Val IoU: {val_info['iou']:.4f} | LR: {current_lr:.6f} | Time: {ep_time:.1f}s"
        print(msg)
        log_file.write(msg + "\n")
        log_file.flush()

        improved = val_info["dice"] > best_val_dice
        if improved:
            best_val_dice = val_info["dice"]
            best_epoch = epoch

        should_stop = trainer.early_stopping.update(val_info["dice"])
        early_state = {
            "best": trainer.early_stopping.best,
            "bad_epochs": trainer.early_stopping.bad_epochs,
            "patience": trainer.early_stopping.patience,
            "stopped": should_stop,
        }
        loader_states = {"train": train_loader.generator.get_state(), "val": val_loader.generator.get_state()}
        save_training_checkpoint(chk_dir / "latest.pt", model, optimizer, scheduler, trainer.scaler, epoch, trainer.global_step, best_val_dice, config, seed, history, "phase4_v2", manifest_meta["hashes"], exp_id, "unet", resolution, config["training"]["threshold"], early_stopping_state=early_state, loader_generator_states=loader_states)

        if improved:
            save_training_checkpoint(chk_dir / "best.pt", model, optimizer, scheduler, trainer.scaler, epoch, trainer.global_step, best_val_dice, config, seed, history, "phase4_v2", manifest_meta["hashes"], exp_id, "unet", resolution, config["training"]["threshold"], early_stopping_state=early_state, loader_generator_states=loader_states)
            log_file.write(f"--> Saved new best checkpoint at epoch {epoch} with Val Dice {best_val_dice:.4f}\n")

        if should_stop:
            print(f"Early stopping triggered at epoch {epoch}")
            log_file.write(f"Early stopping triggered at epoch {epoch}\n")
            early_stopped = True
            break

    total_duration = float(sum(row.get("epoch_seconds", 0.0) for row in history))
    log_file.close()

    df_hist = pd.DataFrame(history)
    df_hist.to_csv(exp_dir / "history.csv", index=False)
    print(f"\nTraining completed in {total_duration:.1f}s. Best Epoch: {best_epoch}, Best Val Dice: {best_val_dice:.4f}")
    return (exp_id, exp_dir, chk_dir, tables_dir, figures_dir, qual_dir, audit_dir,
            config, seed, device, val_ds, model, history, best_epoch, best_val_dice,
            early_stopped, total_duration, manifest_meta, reg_record)


def evaluate_and_finalize(exp_id, exp_dir, chk_dir, tables_dir, figures_dir, qual_dir, audit_dir, config, seed, device, val_ds, model, history, best_epoch, best_val_dice, early_stopped, total_duration, manifest_meta, reg_record):
    print("\n--- EVALUATING BEST CHECKPOINT ON VAL SPLIT ---")
    best_state = load_training_checkpoint(chk_dir / "best.pt", model, restore_rng=False, map_location=device)
    model.eval()

    with open(audit_dir / "kub_object_size_thresholds.json", "r", encoding="utf-8") as f:
        thresh_info = json.load(f)

    val_per_image_rows = []
    val_per_comp_rows = []
    val_component_metadata = pd.read_csv(tables_dir / "kub_val_components_sized.csv")

    with torch.no_grad():
        for i in range(len(val_ds)):
            item = val_ds[i]
            img_t = item["image"].unsqueeze(0).to(device)
            mask_t = item["mask"].unsqueeze(0).to(device)

            with torch.amp.autocast("cuda", enabled=config["training"]["amp"]):
                logits = model(img_t)

            probs = torch.sigmoid(logits).squeeze().cpu().numpy()
            pred_binary = (probs >= config["training"]["threshold"]).astype(np.uint8)
            gt_binary = (item["mask"].squeeze().cpu().numpy() > 0).astype(np.uint8)

            bm = binary_metrics(logits, mask_t, threshold=config["training"]["threshold"])
            dice_i = bm["dice"].item()
            iou_i = bm["iou"].item()
            prec_i = bm["precision"].item()
            rec_i = bm["recall"].item()

            hd_res = hd95(pred_binary, gt_binary)
            hd_val = hd_res["hd95"]
            hd_valid = hd_res["hd95_valid"]
            empty_pred = hd_res["empty_prediction"]

            om_res = object_metrics(pred_binary, gt_binary, minimum_overlap_pixels=1)

            tp = int(np.sum((pred_binary > 0) & (gt_binary > 0)))
            fp = int(np.sum((pred_binary > 0) & (gt_binary == 0)))
            fn = int(np.sum((pred_binary == 0) & (gt_binary > 0)))
            val_per_image_rows.append({
                "sample_id": item["sample_id"],
                "patient_id": item["patient_id"],
                "category": item["category"],
                "view_type": item["view_type"],
                "component_count": item["component_count"],
                "dominant_object_stratum": item["dominant_object_stratum"],
                "dice": dice_i,
                "iou": iou_i,
                "precision": prec_i,
                "recall": rec_i,
                "hd95": hd_val,
                "hd95_valid": hd_valid,
                "empty_prediction": empty_pred,
                "hd95_invalid_reason": hd_res["invalid_reason"],
                "predicted_component_count": om_res["predicted_component_count"],
                "gt_component_count": om_res["gt_component_count"],
                "detected_gt_components": om_res["detected_gt_components"],
                "missed_gt_components": om_res["missed_gt_components"],
                "false_positive_components": om_res["false_positive_predicted_components"],
                "true_positive_pixels": tp,
                "false_positive_pixels": fp,
                "false_negative_pixels": fn
            })

            from scipy.ndimage import label
            from PIL import ImageOps
            with Image.open(item["mask_path"]) as original_mask_file:
                original_gt = np.asarray(original_mask_file.convert("L")) > 0
            original_labels, original_n = label(original_gt, structure=np.ones((3, 3)))
            sample_components = val_component_metadata[val_component_metadata["sample_id"] == item["sample_id"]].sort_values("component_id")
            if original_n != len(sample_components):
                raise RuntimeError(f"Component metadata mismatch for {item['sample_id']}: mask={original_n}, table={len(sample_components)}")
            left, top, right, bottom = [int(value) for value in item["padding"].tolist()]
            resized_width = config["input_resolution"] - left - right
            resized_height = config["input_resolution"] - top - bottom

            for c_id in range(1, original_n + 1):
                original_component = original_labels == c_id
                component_image = Image.fromarray(original_component.astype(np.uint8) * 255)
                component_image = component_image.resize((resized_width, resized_height), Image.Resampling.NEAREST)
                component_image = ImageOps.expand(component_image, (left, top, right, bottom))
                resized_component = np.asarray(component_image) > 0
                overlap = int(np.sum((pred_binary > 0) & resized_component))
                source = sample_components.iloc[c_id - 1]
                val_per_comp_rows.append({
                    "sample_id": item["sample_id"],
                    "patient_id": item["patient_id"],
                    "category": item["category"],
                    "view_type": item["view_type"],
                    "component_id": c_id,
                    "kub_size_v1_stratum": source["size_stratum"],
                    "original_component_pixels": int(source["component_pixels"]),
                    "original_component_ratio": float(source["component_ratio"]),
                    "resized_component_pixels": int(np.sum(resized_component)),
                    "detected": bool(overlap >= 1),
                    "overlap_pixels": overlap
                })

    df_val_img = pd.DataFrame(val_per_image_rows)
    df_val_comp = pd.DataFrame(val_per_comp_rows)

    df_val_img.to_csv(tables_dir / "phase9_unet_val_per_image.csv", index=False)
    df_val_comp.to_csv(tables_dir / "phase9_unet_val_per_component.csv", index=False)


    global_tp = int(df_val_img["true_positive_pixels"].sum())
    global_fp = int(df_val_img["false_positive_pixels"].sum())
    global_fn = int(df_val_img["false_negative_pixels"].sum())
    val_summary = pd.DataFrame([{
        "Metric_Type": "Macro_and_Micro",
        "N_Samples": len(df_val_img),
        "Macro_Dice": df_val_img["dice"].mean(),
        "Macro_IoU": df_val_img["iou"].mean(),
        "Macro_Precision": df_val_img["precision"].mean(),
        "Macro_Recall": df_val_img["recall"].mean(),
        "Micro_Dice": (2 * global_tp) / (2 * global_tp + global_fp + global_fn),
        "Micro_IoU": global_tp / (global_tp + global_fp + global_fn),
        "Global_TP_Pixels": global_tp,
        "Global_FP_Pixels": global_fp,
        "Global_FN_Pixels": global_fn,
        "HD95_Valid_N": df_val_img["hd95_valid"].sum(),
        "HD95_Invalid_N": (~df_val_img["hd95_valid"]).sum(),
        "Empty_Predictions_N": df_val_img["empty_prediction"].sum(),
        "Empty_Prediction_Rate": df_val_img["empty_prediction"].mean(),
        "Median_Valid_HD95": df_val_img[df_val_img["hd95_valid"]]["hd95"].median(),
        "Mean_Valid_HD95": df_val_img[df_val_img["hd95_valid"]]["hd95"].mean()
    }])
    val_summary.to_csv(tables_dir / "phase9_unet_val_summary.csv", index=False)

    fov_rows = []
    for vt, grp in df_val_img.groupby("view_type"):
        fov_rows.append({
            "View_Type": vt,
            "N_Samples": len(grp),
            "Macro_Dice": grp["dice"].mean(),
            "Macro_IoU": grp["iou"].mean(),
            "Macro_Precision": grp["precision"].mean(),
            "Macro_Recall": grp["recall"].mean(),
            "Empty_Prediction_Rate": grp["empty_prediction"].mean(),
            "Object_Recall": grp["detected_gt_components"].sum() / grp["gt_component_count"].sum() if grp["gt_component_count"].sum() > 0 else np.nan
        })
    df_fov_sum = pd.DataFrame(fov_rows)
    df_fov_sum.to_csv(tables_dir / "phase9_unet_fov_summary.csv", index=False)

    cat_rows = []
    for cat, grp in df_val_img.groupby("category"):
        cat_rows.append({
            "Category": cat,
            "N_Samples": len(grp),
            "Macro_Dice": grp["dice"].mean(),
            "Macro_IoU": grp["iou"].mean(),
            "Macro_Precision": grp["precision"].mean(),
            "Macro_Recall": grp["recall"].mean(),
            "Empty_Prediction_Rate": grp["empty_prediction"].mean(),
            "Object_Recall": grp["detected_gt_components"].sum() / grp["gt_component_count"].sum() if grp["gt_component_count"].sum() > 0 else np.nan
        })
    df_cat_sum = pd.DataFrame(cat_rows)
    df_cat_sum.to_csv(tables_dir / "phase9_unet_category_summary.csv", index=False)

    size_rows = []
    full_field_components = df_val_comp[df_val_comp["view_type"] == "FULL_FIELD"]
    for st, grp in full_field_components.groupby("kub_size_v1_stratum"):
        size_rows.append({
            "Stratum": st,
            "GT_Components": len(grp),
            "Detected_Components": grp["detected"].sum(),
            "Object_Recall": grp["detected"].mean()
        })
    df_size_sum = pd.DataFrame(size_rows)
    df_size_sum.to_csv(tables_dir / "phase9_unet_size_summary.csv", index=False)

    obj_summary = pd.DataFrame([{
        "Total_GT_Components": df_val_img["gt_component_count"].sum(),
        "Total_Predicted_Components": df_val_img["predicted_component_count"].sum(),
        "Detected_GT_Components": df_val_img["detected_gt_components"].sum(),
        "Missed_GT_Components": df_val_img["missed_gt_components"].sum(),
        "Object_Recall": df_val_img["detected_gt_components"].sum() / df_val_img["gt_component_count"].sum(),
        "Missed_Object_Rate": df_val_img["missed_gt_components"].sum() / df_val_img["gt_component_count"].sum(),
        "False_Positive_Components": df_val_img["false_positive_components"].sum()
    }])
    obj_summary.to_csv(tables_dir / "phase9_unet_object_summary.csv", index=False)

    def save_paper_table(frame, stem):
        headers = [str(col) for col in frame.columns]
        rows = [headers] + [[str(val) for val in row] for row in frame.itertuples(index=False, name=None)]
        markdown = ["| " + " | ".join(rows[0]) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
        markdown.extend("| " + " | ".join(row) + " |" for row in rows[1:])
        (tables_dir / f"{stem}.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
        (tables_dir / f"{stem}.tex").write_text(frame.to_latex(index=False), encoding="utf-8")

    save_paper_table(val_summary, "phase9_unet_val_summary")
    save_paper_table(df_fov_sum, "phase9_unet_fov_summary")
    save_paper_table(df_cat_sum, "phase9_unet_category_summary")
    save_paper_table(df_size_sum, "phase9_unet_size_summary")
    save_paper_table(obj_summary, "phase9_unet_object_summary")

    return df_val_img, df_val_comp, val_summary, df_fov_sum, df_cat_sum, df_size_sum, obj_summary

def generate_reports_and_artifacts(exp_id, exp_dir, chk_dir, tables_dir, figures_dir, qual_dir, audit_dir, config, seed, device, val_ds, model, history, best_epoch, best_val_dice, early_stopped, total_duration, manifest_meta, reg_record, df_val_img, df_val_comp, val_summary, df_fov_sum, df_cat_sum, df_size_sum, obj_summary):

    def save_fig(fig, stem):
        for ext in ("png", "svg", "pdf"):
            fig.savefig(figures_dir / f"{stem}.{ext}", dpi=300, bbox_inches="tight")
        plt.close(fig)

    df_hist = pd.DataFrame(history)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df_hist["epoch"], df_hist["train_loss"], label="Train Loss", color="#1f77b4")
    ax.plot(df_hist["epoch"], df_hist["val_loss"], label="Val Loss", color="#ff7f0e")
    ax.set_title("KUB U-Net Baseline Loss Curves (Seed 42)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Epoch", fontsize=10); ax.set_ylabel("BCE + Dice Loss", fontsize=10)
    ax.legend(); plt.tight_layout(); save_fig(fig, "phase9_unet_loss_curves")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df_hist["epoch"], df_hist["val_dice"], label="Val Macro Dice", color="#2ca02c")
    ax.axvline(best_epoch, color="red", linestyle="--", label=f"Best Epoch {best_epoch} ({best_val_dice:.4f})")
    ax.set_title("KUB U-Net Baseline Validation Macro Dice Curve", fontsize=12, fontweight="bold")
    ax.set_xlabel("Epoch", fontsize=10); ax.set_ylabel("Macro Dice", fontsize=10)
    ax.legend(); plt.tight_layout(); save_fig(fig, "phase9_unet_val_dice_curve")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(df_hist["epoch"], df_hist["learning_rate"], label="Learning Rate", color="#d62728")
    ax.set_title("KUB U-Net Baseline Learning Rate Schedule (Cosine Annealing)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Epoch", fontsize=10); ax.set_ylabel("Learning Rate", fontsize=10)
    ax.legend(); plt.tight_layout(); save_fig(fig, "phase9_unet_lr_curve")

    fig, ax = plt.subplots(figsize=(8, 4.5))
    for m_col, col_color in zip(["val_dice", "val_iou", "val_precision", "val_recall"], ["#2ca02c", "#1f77b4", "#ff7f0e", "#9467bd"]):
        ax.plot(df_hist["epoch"], df_hist[m_col], label=m_col.replace("val_", "Val ").title(), color=col_color)
    ax.set_title("KUB U-Net Baseline Validation Metrics Progress", fontsize=12, fontweight="bold")
    ax.set_xlabel("Epoch", fontsize=10); ax.set_ylabel("Metric Value", fontsize=10)
    ax.legend(); plt.tight_layout(); save_fig(fig, "phase9_unet_metrics_curve")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(data=df_fov_sum, x="View_Type", y="Macro_Dice", hue="View_Type", palette=["#1f77b4", "#ff7f0e"], legend=False, ax=ax)
    ax.set_title("KUB U-Net Baseline Validation Macro Dice by FOV Subgroup", fontsize=12, fontweight="bold")
    ax.set_xlabel("Field of View Type", fontsize=10); ax.set_ylabel("Macro Dice", fontsize=10)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.4f}", (p.get_x() + p.get_width() / 2., p.get_height()), ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")
    plt.tight_layout(); save_fig(fig, "phase9_unet_fov_performance")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(data=df_cat_sum, x="Category", y="Macro_Dice", hue="Category", palette="tab10", legend=False, ax=ax)
    ax.set_title("KUB U-Net Baseline Validation Macro Dice by Category", fontsize=12, fontweight="bold")
    ax.set_xlabel("Anatomical Category", fontsize=10); ax.set_ylabel("Macro Dice", fontsize=10)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.4f}", (p.get_x() + p.get_width() / 2., p.get_height()), ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")
    plt.tight_layout(); save_fig(fig, "phase9_unet_category_performance")

    fig, ax = plt.subplots(figsize=(7, 4.5))
    sns.barplot(data=df_size_sum, x="Stratum", y="Object_Recall", hue="Stratum", palette="Reds", legend=False, ax=ax)
    ax.set_title("KUB U-Net Baseline Object Recall by kub_size_v1 Stratum (FULL_FIELD VAL)", fontsize=12, fontweight="bold")
    ax.set_xlabel("Object Size Stratum (Frozen TRAIN Thresholds)", fontsize=10); ax.set_ylabel("Object Recall", fontsize=10)
    for p in ax.patches:
        ax.annotate(f"{p.get_height():.4f}", (p.get_x() + p.get_width() / 2., p.get_height()), ha="center", va="bottom", fontsize=10, xytext=(0, 3), textcoords="offset points")
    plt.tight_layout(); save_fig(fig, "phase9_unet_size_object_recall")


    # evaluate_and_finalize has already loaded best.pt into this model.

    # --- QUALITATIVE PANELS (VAL ONLY) ---
    val_sorted = df_val_img.sort_values(by="dice")
    rep_indices = [0, len(val_sorted)//4, len(val_sorted)//2, 3*len(val_sorted)//4, len(val_sorted)-1]
    rep_samples = val_sorted.iloc[rep_indices]

    fig, axes = plt.subplots(len(rep_samples), 4, figsize=(12, 3*len(rep_samples)))
    for idx, (_, row) in enumerate(rep_samples.iterrows()):
        item = val_ds[df_val_img[df_val_img["sample_id"]==row["sample_id"]].index[0]]
        img_arr = (item["image"].squeeze().cpu().numpy() * 255).astype(np.uint8)
        mask_arr = item["mask"].squeeze().cpu().numpy() > 0

        with torch.no_grad(), torch.amp.autocast("cuda", enabled=config["training"]["amp"]):
            prob = torch.sigmoid(model(item["image"].unsqueeze(0).to(device))).squeeze().cpu().numpy()
        pred_b = (prob >= 0.5)

        overlay = np.stack([img_arr]*3, axis=-1)
        overlay[mask_arr, 0] = np.clip(overlay[mask_arr, 0].astype(int) + 160, 0, 255)
        overlay[pred_b, 1] = np.clip(overlay[pred_b, 1].astype(int) + 160, 0, 255)

        axes[idx, 0].imshow(img_arr, cmap="gray"); axes[idx, 0].set_title(f"Image ({row['view_type']})"); axes[idx, 0].axis("off")
        axes[idx, 1].imshow(mask_arr, cmap="gray"); axes[idx, 1].set_title(f"GT Mask ({row['category']})"); axes[idx, 1].axis("off")
        axes[idx, 2].imshow(prob, cmap="magma"); axes[idx, 2].set_title("Probability Map"); axes[idx, 2].axis("off")
        axes[idx, 3].imshow(overlay); axes[idx, 3].set_title(f"Overlay | Dice: {row['dice']:.4f}"); axes[idx, 3].axis("off")

    plt.suptitle("KUB U-Net Baseline Validation Deterministic Predictions Panel", fontsize=13, fontweight="bold")
    plt.tight_layout()
    for ext in ("png", "svg", "pdf"):
        fig.savefig(qual_dir / f"phase9_val_qualitative_panel.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

    fail_samples = df_val_img.sort_values(by="dice").head(4)
    fig, axes = plt.subplots(len(fail_samples), 4, figsize=(12, 3*len(fail_samples)))
    for idx, (_, row) in enumerate(fail_samples.iterrows()):
        item = val_ds[df_val_img[df_val_img["sample_id"]==row["sample_id"]].index[0]]
        img_arr = (item["image"].squeeze().cpu().numpy() * 255).astype(np.uint8)
        mask_arr = item["mask"].squeeze().cpu().numpy() > 0

        with torch.no_grad(), torch.amp.autocast("cuda", enabled=config["training"]["amp"]):
            prob = torch.sigmoid(model(item["image"].unsqueeze(0).to(device))).squeeze().cpu().numpy()
        pred_b = (prob >= 0.5)

        overlay = np.stack([img_arr]*3, axis=-1)
        overlay[mask_arr, 0] = np.clip(overlay[mask_arr, 0].astype(int) + 160, 0, 255)
        overlay[pred_b, 2] = np.clip(overlay[pred_b, 2].astype(int) + 160, 0, 255)

        axes[idx, 0].imshow(img_arr, cmap="gray"); axes[idx, 0].set_title(f"Image ({row['view_type']})"); axes[idx, 0].axis("off")
        axes[idx, 1].imshow(mask_arr, cmap="gray"); axes[idx, 1].set_title(f"GT Mask ({row['category']})"); axes[idx, 1].axis("off")
        axes[idx, 2].imshow(prob, cmap="magma"); axes[idx, 2].set_title("Probability Map"); axes[idx, 2].axis("off")
        axes[idx, 3].imshow(overlay); axes[idx, 3].set_title(f"Failure Overlay | Dice: {row['dice']:.4f}"); axes[idx, 3].axis("off")
    plt.suptitle("KUB U-Net Baseline Validation Failure Cases", fontsize=13, fontweight="bold")
    plt.tight_layout()
    for ext in ("png", "svg", "pdf"):
        fig.savefig(qual_dir / f"phase9_val_failure_panel.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)

    summary_json = {
        "experiment_id": exp_id,
        "status": "COMPLETED",
        "model": "unet",
        "parameter_count": sum(p.numel() for p in model.parameters()),
        "seed": seed,
        "epochs_completed": len(history),
        "best_epoch": best_epoch,
        "early_stopped": early_stopped,
        "best_val_macro_dice": float(best_val_dice),
        "fixed_threshold": 0.5,
        "preprocessing": "aspect_ratio_resize_symmetric_pad_512",
        "loss": "0.5_BCE+0.5_Dice",
        "optimizer": "AdamW",
        "scheduler": "CosineAnnealingLR",
        "batch_size": config["training"]["batch_size"],
        "effective_batch_size": config["training"]["effective_batch_size"],
        "total_training_seconds": total_duration,
        "gpu": torch.cuda.get_device_name(0),
        "manifest_version": "phase4_v2",
        "manifest_hashes": manifest_meta["hashes"],
        "best_checkpoint": str(chk_dir / "best.pt"),
        "latest_checkpoint": str(chk_dir / "latest.pt"),
        "test_accessed": False,
        "external_accessed": False,
        "validation_metrics": val_summary.to_dict("records")[0],
        "object_metrics": obj_summary.to_dict("records")[0],
        "fov_metrics": df_fov_sum.to_dict("records"),
        "category_metrics": df_cat_sum.to_dict("records"),
        "full_field_size_metrics": df_size_sum.to_dict("records")
    }
    with open(exp_dir / "summary.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2)

    reg_record["status"] = "COMPLETED"
    reg_record["best_val_dice"] = float(best_val_dice)
    reg_record["best_epoch"] = int(best_epoch)
    reg_record["epochs"] = int(len(history))
    reg_record["end_time"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    register_experiment(reg_record, PROJECT_ROOT)

    audit_json = {
        "phase": "9 - KUB U-Net Baseline Training",
        "status": "PASS",
        "experiment_id": exp_id,
        "seed": seed,
        "best_epoch": best_epoch,
        "best_val_macro_dice": float(best_val_dice),
        "best_checkpoint_sha256": get_file_sha256(chk_dir / "best.pt"),
        "latest_checkpoint_sha256": get_file_sha256(chk_dir / "latest.pt"),
        "history_sha256": get_file_sha256(exp_dir / "history.csv"),
        "val_per_image_sha256": get_file_sha256(tables_dir / "phase9_unet_val_per_image.csv"),
        "val_per_component_sha256": get_file_sha256(tables_dir / "phase9_unet_val_per_component.csv"),
        "test_accessed": False,
        "external_accessed": False,
        "experiment_a_modified": False,
        "manifest_modified": False,
        "overall_val_metrics": val_summary.to_dict("records")[0],
        "fov_summary": df_fov_sum.to_dict("records"),
        "category_summary": df_cat_sum.to_dict("records"),
        "size_summary": df_size_sum.to_dict("records"),
        "object_summary": obj_summary.to_dict("records")[0]
    }
    with open(audit_dir / "phase9_kub_unet_baseline.json", "w", encoding="utf-8") as f:
        json.dump(audit_json, f, indent=2)

    md_audit = f"""# Phase 9 — KUB U-Net Baseline Training Audit Report

## Executive Summary
The first scientific KUB U-Net baseline (`phase9_kub_unet_baseline_seed42_512`) trained successfully on the frozen development split (`phase4_v2`).
- **Epochs Completed**: {len(history)} (Early stopped: {early_stopped})
- **Best Epoch**: {best_epoch}
- **Best Validation Macro Dice**: `{best_val_dice:.4f}`
- **Test Set Protection**: **100% LOCKED** (0 TEST reads/evaluations performed).

## Overall Validation Metrics (Best Checkpoint @ Threshold 0.5)
- **Macro Dice**: `{val_summary['Macro_Dice'].iloc[0]:.4f}`
- **Macro IoU**: `{val_summary['Macro_IoU'].iloc[0]:.4f}`
- **Macro Precision**: `{val_summary['Macro_Precision'].iloc[0]:.4f}`
- **Macro Recall**: `{val_summary['Macro_Recall'].iloc[0]:.4f}`
- **Micro/Global Dice**: `{val_summary['Micro_Dice'].iloc[0]:.4f}`
- **Micro/Global IoU**: `{val_summary['Micro_IoU'].iloc[0]:.4f}`
- **Empty Prediction Rate**: `{val_summary['Empty_Prediction_Rate'].iloc[0]:.4f}` ({val_summary['Empty_Predictions_N'].iloc[0]} / 283)
- **Valid HD95 Median**: `{val_summary['Median_Valid_HD95'].iloc[0]:.2f}` pixels

## Subgroup Summaries
### FOV Subgroups
{df_fov_sum.to_markdown(index=False)}

### Category Subgroups
{df_cat_sum.to_markdown(index=False)}

### Object-Size Subgroups (FULL_FIELD VAL)
{df_size_sum.to_markdown(index=False)}

## Checkpoints & Artifacts
- **Best Checkpoint**: `checkpoints/{exp_id}/best.pt` (SHA-256: `{audit_json['best_checkpoint_sha256']}`)
- **Latest Checkpoint**: `checkpoints/{exp_id}/latest.pt` (SHA-256: `{audit_json['latest_checkpoint_sha256']}`)
- **Per-Image Evaluation Table**: `reports/tables/phase9_unet_val_per_image.csv`
- **Per-Component Evaluation Table**: `reports/tables/phase9_unet_val_per_component.csv`
"""
    with open(audit_dir / "phase9_kub_unet_baseline.md", "w", encoding="utf-8") as f:
        f.write(md_audit)

    print("\nPhase 9 U-Net baseline training & evaluation completed successfully.")

def main():
    args = train_baseline()
    eval_res = evaluate_and_finalize(*args)
    generate_reports_and_artifacts(*args, *eval_res)

if __name__ == "__main__":
    main()

