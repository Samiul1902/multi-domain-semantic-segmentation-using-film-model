import torch
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, sys
from pathlib import Path

# Setup root
ROOT = Path('.').resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint

# Standardized error map colors:
# TP: Green [0, 255, 0]
# FP: Red [255, 0, 0]
# FN: Blue [0, 100, 255]
# Background: Black [0, 0, 0]
def create_error_map(gt_mask, pred_mask):
    gt = gt_mask > 0
    pred = pred_mask > 0
    tp = gt & pred
    fp = (~gt) & pred
    fn = gt & (~pred)
    
    h, w = gt.shape
    rgb = np.zeros((h, w, 3), dtype=np.uint8)
    rgb[tp] = [0, 255, 0]     # TP = Green
    rgb[fp] = [255, 30, 30]   # FP = Red
    rgb[fn] = [30, 120, 255]  # FN = Blue
    return rgb

def compute_metrics(gt_mask, pred_mask):
    gt = (gt_mask > 0).astype(np.float32)
    pred = (pred_mask > 0).astype(np.float32)
    intersection = np.sum(gt * pred)
    dice = (2.0 * intersection) / (np.sum(gt) + np.sum(pred) + 1e-8)
    iou = intersection / (np.sum(gt) + np.sum(pred) - intersection + 1e-8)
    precision = intersection / (np.sum(pred) + 1e-8) if np.sum(pred) > 0 else 0.0
    recall = intersection / (np.sum(gt) + 1e-8) if np.sum(gt) > 0 else 1.0
    return float(dice), float(iou), float(precision), float(recall)

def preprocess_image(raw_image, target_size=512):
    original_width, original_height = raw_image.size
    scale = min(target_size / original_width, target_size / original_height)
    rw, rh = max(1, round(original_width * scale)), max(1, round(original_height * scale))

    proc_img = raw_image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (target_size - rw) // 2, (target_size - rh) // 2
    right, bottom = target_size - rw - left, target_size - rh - top
    padding = (left, top, right, bottom)

    padded_img = ImageOps.expand(proc_img, padding)
    tensor = torch.from_numpy(np.asarray(padded_img, dtype=np.float32).copy()).unsqueeze(0).unsqueeze(0) / 255.0
    metadata = {
        "original_width": original_width,
        "original_height": original_height,
        "scale": scale,
        "resized_width": rw,
        "resized_height": rh,
        "padding": padding,
    }
    return tensor, metadata

def restore_coordinates(prob_512, mask_512, metadata):
    left, top, right, bottom = metadata["padding"]
    orig_w, orig_h = metadata["original_width"], metadata["original_height"]

    cropped_prob = prob_512[top:512-bottom, left:512-right]
    cropped_mask = mask_512[top:512-bottom, left:512-right]

    prob_pil = Image.fromarray((cropped_prob * 255.0).astype(np.uint8)).resize(
        (orig_w, orig_h), Image.Resampling.BILINEAR
    )
    prob_orig = np.asarray(prob_pil, dtype=np.float32) / 255.0

    mask_pil = Image.fromarray((cropped_mask * 255).astype(np.uint8)).resize(
        (orig_w, orig_h), Image.Resampling.NEAREST
    )
    mask_orig = (np.asarray(mask_pil) > 0).astype(np.uint8)
    return prob_orig, mask_orig

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Generating detailed 16 baseline comparisons on device: {device}")
    
    # Load selection table
    d16_df = pd.read_csv("reports/tables/phase15_val_detailed16_selection.csv")
    val_meta = pd.read_csv("reports/tables/kub_val_sample_characteristics_v2.csv")
    samples = pd.merge(d16_df, val_meta, on="sample_id", how="left")
    
    # Define models
    model_configs = [
        ("U-Net", "unet", "checkpoints/phase9_kub_unet_baseline_seed42_512/best.pt"),
        ("Attention U-Net", "attention_unet", "checkpoints/phase10_kub_attention_unet_seed42_512/best.pt"),
        ("UNet++", "unetpp", "checkpoints/phase10_kub_unetpp_seed42_512/best.pt"),
        ("DeepLabV3+", "deeplabv3plus", "checkpoints/phase10_kub_deeplabv3plus_seed42_512/best.pt"),
    ]
    
    # Pre-load models into memory
    loaded_models = {}
    for m_label, m_type, ckpt_path in model_configs:
        print(f"Loading {m_label} from {ckpt_path}...")
        m = create_model(m_type, in_channels=1, out_channels=1, base_channels=32).to(device)
        load_training_checkpoint(ckpt_path, m, restore_rng=False, map_location=device)
        m.eval()
        loaded_models[m_label] = m
        
    os.makedirs("reports/figures/retrospective/phase10_baselines", exist_ok=True)
    
    summary_records = []
    
    for idx, row in samples.iterrows():
        sid = row["sample_id"]
        rank = row["detailed_rank"]
        img_p = row["image_path"]
        msk_p = row["mask_path"]
        
        with Image.open(img_p) as im_f:
            raw_img = im_f.convert("L")
            img_arr = np.asarray(raw_img)
        with Image.open(msk_p) as mk_f:
            gt_arr = (np.asarray(mk_f.convert("L")) > 0).astype(np.uint8)
            
        tensor_512, meta = preprocess_image(raw_img, target_size=512)
        tensor_512 = tensor_512.to(device)
        
        preds = {}
        with torch.inference_mode():
            for m_label, _, _ in model_configs:
                m = loaded_models[m_label]
                with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                    logits = m(tensor_512)
                p512 = torch.sigmoid(logits).squeeze().cpu().numpy().astype(np.float32)
                m512 = (p512 >= 0.50).astype(np.uint8)
                porig, morig = restore_coordinates(p512, m512, meta)
                d, iou, prec, rec = compute_metrics(gt_arr, morig)
                preds[m_label] = {
                    "prob": porig,
                    "mask": morig,
                    "dice": d,
                    "iou": iou,
                    "precision": prec,
                    "recall": rec,
                    "error_map": create_error_map(gt_arr, morig)
                }
                summary_records.append({
                    "detailed_rank": rank,
                    "sample_id": sid,
                    "model": m_label,
                    "dice": d,
                    "iou": iou,
                    "precision": prec,
                    "recall": rec
                })
                
        # Generate 2x5 figure
        # Row 1: Original | GT | U-Net Pred | Attn U-Net Pred | UNet++ Pred
        # Row 2: DeepLabV3+ Pred | U-Net Err | Attn U-Net Err | UNet++ Err | DeepLab Err
        fig, axes = plt.subplots(2, 5, figsize=(20, 8))
        
        # Panel 1: Original Image
        axes[0, 0].imshow(img_arr, cmap="gray")
        axes[0, 0].set_title(f"A. Original Radiograph\nRank {rank} | {sid[:8]}...\nSize: {img_arr.shape[1]}x{img_arr.shape[0]}", fontsize=10)
        axes[0, 0].axis("off")
        
        # Panel 2: Ground Truth
        axes[0, 1].imshow(img_arr, cmap="gray")
        axes[0, 1].contour(gt_arr, levels=[0.5], colors="lime", linewidths=1.5)
        axes[0, 1].set_title(f"B. Ground Truth Mask\nComponents: {row['gt_component_count']}\nTiny: {row['Tiny_present']}", fontsize=10)
        axes[0, 1].axis("off")
        
        # Predictions & Error Maps
        models_order = ["U-Net", "Attention U-Net", "UNet++", "DeepLabV3+"]
        
        # Top row: Predictions overlaid
        for i, m_label in enumerate(models_order[:3]):
            col = i + 2
            axes[0, col].imshow(img_arr, cmap="gray")
            axes[0, col].contour(preds[m_label]["mask"], levels=[0.5], colors="red", linewidths=1.5)
            d_val = preds[m_label]["dice"]
            axes[0, col].set_title(f"C{i+1}. {m_label}\nDice: {d_val:.4f} | Rec: {preds[m_label]['recall']:.2f}", fontsize=10)
            axes[0, col].axis("off")
            
        # Bottom row 0: DeepLabV3+ prediction
        axes[1, 0].imshow(img_arr, cmap="gray")
        axes[1, 0].contour(preds["DeepLabV3+"]["mask"], levels=[0.5], colors="red", linewidths=1.5)
        axes[1, 0].set_title(f"C4. DeepLabV3+\nDice: {preds['DeepLabV3+']['dice']:.4f} | Rec: {preds['DeepLabV3+']['recall']:.2f}", fontsize=10)
        axes[1, 0].axis("off")
        
        # Bottom row 1-4: Error maps (U-Net, Attn U-Net, UNet++, DeepLabV3+)
        for i, m_label in enumerate(models_order):
            col = i + 1
            axes[1, col].imshow(preds[m_label]["error_map"])
            axes[1, col].set_title(f"D{i+1}. {m_label} Error Map\nTP=Green, FP=Red, FN=Blue", fontsize=10)
            axes[1, col].axis("off")
            
        fig.suptitle(f"Phase 9/10 Baseline Architecture Comparison — Detailed Case {rank}/16 (Sample ID: {sid})", fontsize=13, fontweight="bold")
        plt.tight_layout()
        fig_save_path = f"reports/figures/retrospective/phase10_baselines/case_{rank:02d}_{sid[:8]}.png"
        plt.savefig(fig_save_path, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"Generated case {rank}/16 -> {fig_save_path}")
        
    res_df = pd.DataFrame(summary_records)
    res_df.to_csv("reports/tables/phase10_detailed16_evaluated_metrics.csv", index=False)
    print("All 16 cases successfully rendered and evaluated!")

if __name__ == "__main__":
    main()

