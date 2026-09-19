import torch
from PIL import Image, ImageOps
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os, sys
from pathlib import Path

ROOT = Path('.').resolve()
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint

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
    print(f"Generating Phase 11 failure analysis cases on: {device}")
    
    # 1. Load failure table
    fail_df = pd.read_csv("reports/tables/phase11_kub_failure_analysis_per_image.csv")
    val_meta = pd.read_csv("reports/tables/kub_val_sample_characteristics_v2.csv")
    merged = pd.merge(fail_df, val_meta, on="sample_id", how="left")
    
    # Select distinct failure categories deterministically:
    # A. Global-Empty cases (prediction completely empty, empty_prediction == True) -> 4 cases
    # B. Missed component cases (missed_eval_components > 0) -> 4 cases
    # C. Severe False Positive burden (fp_eval_components >= 5) -> 4 cases
    # D. Lowest Dice decile (low_dice_decile == True) -> 4 cases
    
    c_empty = merged[merged['empty_prediction'] == True].sort_values('sample_id').head(4)
    c_miss = merged[(merged['missed_eval_components'] > 0) & (~merged['sample_id'].isin(c_empty['sample_id']))].sort_values('sample_id').head(4)
    c_fp = merged[(merged['fp_eval_components'] >= 4) & (~merged['sample_id'].isin(c_empty['sample_id'])) & (~merged['sample_id'].isin(c_miss['sample_id']))].sort_values('sample_id').head(4)
    c_low = merged[(merged['low_dice_decile'] == True) & (~merged['sample_id'].isin(c_empty['sample_id'])) & (~merged['sample_id'].isin(c_miss['sample_id'])) & (~merged['sample_id'].isin(c_fp['sample_id']))].sort_values('dice').head(4)
    
    cohort = pd.concat([
        c_empty.assign(failure_cat="Global-Empty (0 Pred Pixels)"),
        c_miss.assign(failure_cat="Missed GT Component(s)"),
        c_fp.assign(failure_cat="Severe False Positives (>=4 FPs)"),
        c_low.assign(failure_cat="Low Dice Decile (<0.30)")
    ]).reset_index(drop=True)
    
    cohort.to_csv("reports/tables/phase11_failure_16_selection.csv", index=False)
    print(f"Selected {len(cohort)} failure cases across 4 categories.")
    
    # Load UNet++
    ckpt_path = "checkpoints/phase10_kub_unetpp_seed42_512/best.pt"
    model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(ckpt_path, model, restore_rng=False, map_location=device)
    model.eval()
    
    os.makedirs("reports/figures/retrospective/phase11_failures", exist_ok=True)
    
    for idx, row in cohort.iterrows():
        sid = row["sample_id"]
        cat = row["failure_cat"]
        img_p = row["image_path"]
        msk_p = row["mask_path"]
        
        with Image.open(img_p) as im_f:
            raw_img = im_f.convert("L")
            img_arr = np.asarray(raw_img)
        with Image.open(msk_p) as mk_f:
            gt_arr = (np.asarray(mk_f.convert("L")) > 0).astype(np.uint8)
            
        tensor_512, meta = preprocess_image(raw_img, target_size=512)
        tensor_512 = tensor_512.to(device)
        
        with torch.inference_mode():
            with torch.amp.autocast("cuda", enabled=device.type == "cuda"):
                logits = model(tensor_512)
            p512 = torch.sigmoid(logits).squeeze().cpu().numpy().astype(np.float32)
            m512 = (p512 >= 0.50).astype(np.uint8)
            porig, morig = restore_coordinates(p512, m512, meta)
            
        d, iou, prec, rec = compute_metrics(gt_arr, morig)
        err_map = create_error_map(gt_arr, morig)
        
        # 1x5 Figure: Original | Ground Truth | UNet++ Probability | UNet++ Prediction | Error Map
        fig, axes = plt.subplots(1, 5, figsize=(20, 4.5))
        
        axes[0].imshow(img_arr, cmap="gray")
        axes[0].set_title(f"A. Original Radiograph\n{sid[:8]}... | {img_arr.shape[1]}x{img_arr.shape[0]}", fontsize=10)
        axes[0].axis("off")
        
        axes[1].imshow(img_arr, cmap="gray")
        axes[1].contour(gt_arr, levels=[0.5], colors="lime", linewidths=1.5)
        axes[1].set_title(f"B. Ground Truth Mask\nComponents: {row['gt_eval_components']}\nStratum: {row['dominant_object_stratum']}", fontsize=10)
        axes[1].axis("off")
        
        axes[2].imshow(porig, cmap="magma", vmin=0.0, vmax=1.0)
        axes[2].set_title("C. UNet++ Probability Map\nContinuous [0, 1]", fontsize=10)
        axes[2].axis("off")
        
        axes[3].imshow(img_arr, cmap="gray")
        if np.sum(morig) > 0:
            axes[3].contour(morig, levels=[0.5], colors="red", linewidths=1.5)
        axes[3].set_title(f"D. UNet++ Prediction\nDice: {d:.4f} | Prec: {prec:.2f}", fontsize=10)
        axes[3].axis("off")
        
        axes[4].imshow(err_map)
        axes[4].set_title(f"E. Error Map (TP=Grn, FP=Red, FN=Blu)\nFP Comps: {row['fp_eval_components']} | Missed: {row['missed_eval_components']}", fontsize=10)
        axes[4].axis("off")
        
        fig.suptitle(f"Phase 11 Failure Case {idx+1}/16 — Category: {cat} (Sample ID: {sid})", fontsize=12, fontweight="bold")
        plt.tight_layout()
        save_p = f"reports/figures/retrospective/phase11_failures/failure_{idx+1:02d}_{sid[:8]}.png"
        plt.savefig(save_p, dpi=180, bbox_inches="tight")
        plt.close(fig)
        print(f"Rendered failure case {idx+1}/16 -> {save_p}")

if __name__ == "__main__":
    main()

