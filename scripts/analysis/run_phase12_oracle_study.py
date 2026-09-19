"""Phase 12 KUB Oracle ROI / Zoom Upper-Bound Study."""
import hashlib, json, math, sys, time
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))

from src.analysis.oracle_roi import (
    compute_square_crop, crop_and_preprocess, extract_gt_components,
    restore_crop_probability, run_oracle_roi_image,
)
from src.metrics.object_metrics import object_metrics
from src.metrics.segmentation import binary_metrics, hd95
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock

TABLES_DIR = ROOT / "reports" / "tables"
FIGURES_DIR = ROOT / "reports" / "figures" / "phase12_oracle_roi"
QUAL_DIR = ROOT / "reports" / "qualitative" / "phase12_oracle_roi"
CACHE_DIR = ROOT / "data_cache" / "phase12_oracle_roi"
AUDIT_DIR = ROOT / "reports" / "audits"

for d in (TABLES_DIR, FIGURES_DIR, QUAL_DIR, CACHE_DIR, AUDIT_DIR):
    d.mkdir(parents=True, exist_ok=True)


def save_formatted_table(df, name):
    path = TABLES_DIR / name
    df.to_csv(path, index=False)
    headers = [str(c) for c in df.columns]
    markdown = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]

def run_eval_pass():
    verify_manifests(); verify_test_lock(ROOT)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda": raise RuntimeError("CUDA is required for Phase 12 Oracle ROI study")

    chk_path = ROOT / "checkpoints/phase10_kub_unetpp_seed42_512/best.pt"
    model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(chk_path, model, restore_rng=False, map_location=device)
    model.eval()

    val_samples = pd.read_csv(TABLES_DIR / "kub_val_samples_sized.csv")
    ff_samples = val_samples[val_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    val_components = pd.read_csv(TABLES_DIR / "kub_val_components_sized.csv")
    ff_components = val_components[val_components["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)

    global_per_img = pd.read_csv(TABLES_DIR / "phase10_unetpp_val_per_image.csv").set_index("sample_id")
    global_per_comp = pd.read_csv(TABLES_DIR / "phase10_unetpp_val_per_component.csv")

    assert len(ff_samples) == 106; assert len(ff_components) == 156

    margins = [0.10, 0.25, 0.50]
    per_image_rows, crop_geom_rows = [], []
    per_component_map = {row["sample_id"] + f"_{row['component_id']}": dict(row) for _, row in ff_components.iterrows()}

    for i, srow in ff_samples.iterrows():
        sid, pid, cat = srow["sample_id"], srow["patient_id"], srow["category"]
        img_path, mask_path = Path(srow["image_path"]), Path(srow["mask_path"])
        with Image.open(mask_path) as mf: raw_gt = (np.asarray(mf.convert("L")) > 0).astype(np.uint8)
        h_img, w_img = raw_gt.shape
        orig_comps, labeled_gt = extract_gt_components(raw_gt)
        g_row = global_per_img.loc[sid]

        oracle_res = {}
        for m in margins:
            res = run_oracle_roi_image(img_path, mask_path, model, device, margin=m, threshold=0.5)
            oracle_res[m] = res
            if m == 0.25:
                cache_img_dir = CACHE_DIR / sid; cache_img_dir.mkdir(parents=True, exist_ok=True)
                np.save(cache_img_dir / "prob_combined.npy", res["prob_combined"])
                np.save(cache_img_dir / "mask_combined.npy", res["mask_combined"])

        res25 = oracle_res[0.25]; prob25, mask25 = res25["prob_combined"], res25["mask_combined"]
        # Compute Dice/IoU directly from binary masks (prob_combined is already a probability, NOT logits;
        # passing it through binary_metrics would apply sigmoid again giving incorrect results).
        def _dice_from_masks(pred_mask, gt_mask):
            pred_b = pred_mask.astype(bool); gt_b = gt_mask.astype(bool)
            tp = int((pred_b & gt_b).sum()); fp = int((pred_b & ~gt_b).sum()); fn = int((~pred_b & gt_b).sum())
            eps = 1e-7
            dice = (2*tp + eps) / (2*tp + fp + fn + eps)
            iou = (tp + eps) / (tp + fp + fn + eps)
            prec = (tp + eps) / (tp + fp + eps)
            rec = (tp + eps) / (tp + fn + eps)
            return {"dice": dice, "iou": iou, "precision": prec, "recall": rec, "tp": tp, "fp": fp, "fn": fn}
        m25 = _dice_from_masks(mask25, raw_gt)
        d25 = hd95(mask25, raw_gt)
        g_comp_sub = global_per_comp[global_per_comp["sample_id"] == sid].set_index("original_component_id")
        for c_info in orig_comps:
            cid = c_info["component_id"]; ckey = f"{sid}_{cid}"; c_mask = labeled_gt == cid
            g_det = bool(g_comp_sub.loc[cid, "detected"]) if cid in g_comp_sub.index else False
            o10_det = bool((oracle_res[0.10]["mask_combined"] & c_mask).sum() >= 1)
            o25_det = bool((oracle_res[0.25]["mask_combined"] & c_mask).sum() >= 1)
            o50_det = bool((oracle_res[0.50]["mask_combined"] & c_mask).sum() >= 1)
            c_entry = per_component_map[ckey]
            c_entry.update({"global_detected": g_det, "oracle10_detected": o10_det, "oracle25_detected": o25_det,
                            "oracle50_detected": o50_det, "recovered_by_oracle25": o25_det and not g_det,
                            "lost_by_oracle25": g_det and not o25_det})
            geom25 = compute_square_crop(c_info, (h_img, w_img), margin=0.25)
            c_entry.update({"min_y": c_info["min_y"], "max_y": c_info["max_y"], "min_x": c_info["min_x"], "max_x": c_info["max_x"],
                            "crop_y1_25": geom25["y1"], "crop_y2_25": geom25["y2"], "crop_x1_25": geom25["x1"], "crop_x2_25": geom25["x2"],
                            "crop_side_pixels_25": geom25["crop_side_pixels"], "effective_magnification_25": geom25["effective_magnification"]})
            g10 = compute_square_crop(c_info, (h_img, w_img), margin=0.10)
            g50 = compute_square_crop(c_info, (h_img, w_img), margin=0.50)
            crop_geom_rows.append({"sample_id": sid, "patient_id": pid, "category": cat, "component_id": cid,
                                   "kub_size_v1_stratum": c_entry["size_stratum"], "component_pixels": c_entry["component_pixels"],
                                   "crop_side_10": g10["crop_side_pixels"], "mag_10": g10["effective_magnification"],
                                   "crop_side_25": geom25["crop_side_pixels"], "mag_25": geom25["effective_magnification"],
                                   "crop_side_50": g50["crop_side_pixels"], "mag_50": g50["effective_magnification"]})

        o10_dice = float(_dice_from_masks(oracle_res[0.10]["mask_combined"], raw_gt)["dice"])
        o25_dice = float(m25["dice"])
        o50_dice = float(_dice_from_masks(oracle_res[0.50]["mask_combined"], raw_gt)["dice"])
        g_det_cnt = sum(bool(g_comp_sub.loc[c["component_id"], "detected"]) for c in orig_comps) if len(orig_comps) > 0 else 0
        o25_det_cnt = sum(bool((mask25 & (labeled_gt == c["component_id"])).sum() >= 1) for c in orig_comps) if len(orig_comps) > 0 else 0

        per_image_rows.append({"sample_id": sid, "patient_id": pid, "category": cat, "original_H": h_img, "original_W": w_img,
                               "component_count_original": int(srow["component_count"]), "global_dice": float(g_row["dice"]),
                               "oracle10_dice": o10_dice, "oracle25_dice": o25_dice, "oracle50_dice": o50_dice,
                               "global_iou": float(g_row["iou"]), "oracle25_iou": float(m25["iou"]),
                               "global_precision": float(g_row["precision"]), "oracle25_precision": float(m25["precision"]),
                               "global_recall": float(g_row["recall"]), "oracle25_recall": float(m25["recall"]),
                               "global_hd95": float(g_row["hd95"]), "oracle25_hd95": d25["hd95"],
                               "global_empty_prediction": bool(g_row["empty_prediction"]), "oracle25_empty_prediction": d25["empty_prediction"],
                               "global_detected_components_original": g_det_cnt, "oracle25_detected_components_original": o25_det_cnt,
                               "dice_delta_oracle25_minus_global": o25_dice - float(g_row["dice"])})

    df_img = pd.DataFrame(per_image_rows); df_comp = pd.DataFrame(list(per_component_map.values())); df_geom = pd.DataFrame(crop_geom_rows)
    df_img.to_csv(TABLES_DIR / "phase12_oracle_roi_per_image.csv", index=False)
    df_comp.to_csv(TABLES_DIR / "phase12_oracle_roi_per_component.csv", index=False)

def build_summary_tables(df_img, df_comp):
    # 1. Summary across margins
    summary_rows = []
    for label, col_prefix, d_col in [("Global UNet++", "global", "global_dice"),
                                     ("Oracle 10%", "oracle10", "oracle10_dice"),
                                     ("Oracle 25%", "oracle25", "oracle25_dice"),
                                     ("Oracle 50%", "oracle50", "oracle50_dice")]:
        det_col = "global_detected" if col_prefix == "global" else f"{col_prefix}_detected"
        ff_comps = df_comp[df_comp["view_type"] == "FULL_FIELD"]
        comp_rec = ff_comps[det_col].mean()

        size_recs = {}
        for st in ["TINY", "SMALL", "MEDIUM", "LARGE"]:
            sub = ff_comps[ff_comps["size_stratum"] == st]
            size_recs[st] = sub[det_col].mean()

        if col_prefix == "oracle25":
            valid_hd = df_img.loc[df_img["oracle25_hd95"].notna(), "oracle25_hd95"]
            summary_rows.append({
                "Method": label, "FULL_FIELD_N": len(df_img),
                "Macro_Dice": df_img["oracle25_dice"].mean(), "Macro_IoU": df_img["oracle25_iou"].mean(),
                "Macro_Precision": df_img["oracle25_precision"].mean(), "Macro_Recall": df_img["oracle25_recall"].mean(),
                "HD95_Median": valid_hd.median(), "Empty_Prediction_Rate": df_img["oracle25_empty_prediction"].mean(),
                "Original_Component_Recall": comp_rec, "Tiny_Recall": size_recs["TINY"],
                "Small_Recall": size_recs["SMALL"], "Medium_Recall": size_recs["MEDIUM"], "Large_Recall": size_recs["LARGE"]
            })
        elif col_prefix == "global":
            valid_hd = df_img.loc[df_img["global_hd95"].notna() & df_img["global_hd95_valid"], "global_hd95"]
            summary_rows.append({
                "Method": label, "FULL_FIELD_N": len(df_img),
                "Macro_Dice": df_img["global_dice"].mean(), "Macro_IoU": df_img["global_iou"].mean(),
                "Macro_Precision": df_img["global_precision"].mean(), "Macro_Recall": df_img["global_recall"].mean(),
                "HD95_Median": valid_hd.median(), "Empty_Prediction_Rate": df_img["global_empty_prediction"].mean(),
                "Original_Component_Recall": comp_rec, "Tiny_Recall": size_recs["TINY"],
                "Small_Recall": size_recs["SMALL"], "Medium_Recall": size_recs["MEDIUM"], "Large_Recall": size_recs["LARGE"]
            })
        else:
            summary_rows.append({
                "Method": label, "FULL_FIELD_N": len(df_img),
                "Macro_Dice": df_img[d_col].mean(), "Macro_IoU": np.nan,
                "Macro_Precision": np.nan, "Macro_Recall": np.nan,
                "HD95_Median": np.nan, "Empty_Prediction_Rate": np.nan,
                "Original_Component_Recall": comp_rec, "Tiny_Recall": size_recs["TINY"],
                "Small_Recall": size_recs["SMALL"], "Medium_Recall": size_recs["MEDIUM"], "Large_Recall": size_recs["LARGE"]
            })

    df_summary = pd.DataFrame(summary_rows)
    save_formatted_table(df_summary, "phase12_oracle_roi_summary.csv")

    # 2. Size recovery table
    size_rows = []
    ff_comps = df_comp[df_comp["view_type"] == "FULL_FIELD"]
    for st in ["TINY", "SMALL", "MEDIUM", "LARGE"]:
        sub = ff_comps[ff_comps["size_stratum"] == st]
        gt_n = len(sub)
        g_det = int(sub["global_detected"].sum())
        g_miss = gt_n - g_det
        o_det = int(sub["oracle25_detected"].sum())
        o_miss = gt_n - o_det
        g_rec = g_det / gt_n
        o_rec = o_det / gt_n
        rec_cnt = int(sub["recovered_by_oracle25"].sum())
        lost_cnt = int(sub["lost_by_oracle25"].sum())

        size_rows.append({
            "Stratum": st, "GT_Components": gt_n,
            "Global_Detected": g_det, "Global_Missed": g_miss,
            "Oracle25_Detected": o_det, "Oracle25_Missed": o_miss,
            "Global_Recall": g_rec, "Oracle25_Recall": o_rec,
            "Delta_Recall": o_rec - g_rec,
            "Global_Misses_Recovered": rec_cnt, "Global_Detections_Lost": lost_cnt
        })

    df_size_rec = pd.DataFrame(size_rows)
    save_formatted_table(df_size_rec, "phase12_oracle_roi_size_recovery.csv")


def plot_figures(df_img, df_comp, df_summary, df_size_rec, df_multi):
    sns.set_theme(style="whitegrid")

    def emit(fig, stem):
        for ext in ("png", "svg", "pdf"):
            fig.savefig(FIGURES_DIR / f"{stem}.{ext}", dpi=320, bbox_inches="tight")
        plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 5))
    df_melt = df_img.melt(id_vars="sample_id", value_vars=["global_dice", "oracle25_dice"], var_name="Method", value_name="Dice")
    df_melt["Method"] = df_melt["Method"].map({"global_dice": "Global UNet++", "oracle25_dice": "Oracle 25%"})
    sns.boxplot(data=df_melt, x="Method", y="Dice", palette="colorblind", ax=ax)
    ax.set_ylim(0, 1.05); ax.set_title("FULL_FIELD VAL: Global UNet++ vs Oracle 25% ROI Dice")
    emit(fig, "phase12_global_vs_oracle_dice")

    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(df_img["dice_delta_oracle25_minus_global"], bins=20, kde=True, color="#4C72B0", ax=ax)
    ax.axvline(0, color="red", ls="--", lw=1.5)
    ax.set_xlabel("Oracle 25% Dice - Global Dice Delta"); ax.set_title("Distribution of Paired Oracle 25% Dice Gains")
    emit(fig, "phase12_dice_delta_distribution")

    fig, ax = plt.subplots(figsize=(8, 5))
    size_melt = df_size_rec.melt(id_vars="Stratum", value_vars=["Global_Recall", "Oracle25_Recall"], var_name="Method", value_name="Recall")
    size_melt["Method"] = size_melt["Method"].map({"Global_Recall": "Global UNet++", "Oracle25_Recall": "Oracle 25%"})
    sns.barplot(data=size_melt, x="Stratum", y="Recall", hue="Method", palette="colorblind", ax=ax)
    ax.set_ylim(0, 1.05); ax.set_title("FULL_FIELD Original-Component Recall by Size Stratum")
    emit(fig, "phase12_size_recall_global_vs_oracle")

    tiny_comps = df_comp[df_comp["size_stratum"] == "TINY"]
    fig, ax = plt.subplots(figsize=(7, 5))
    tiny_counts = pd.DataFrame([
        {"Category": "Globally Missed", "Count": int((~tiny_comps["global_detected"]).sum())},
        {"Category": "Recovered by Oracle25", "Count": int(tiny_comps["recovered_by_oracle25"].sum())},
        {"Category": "Remain Missed", "Count": int((~tiny_comps["oracle25_detected"]).sum())},
    ])
    sns.barplot(data=tiny_counts, x="Category", y="Count", palette="colorblind", ax=ax)
    ax.set_title("FULL_FIELD TINY Component Recovery Breakdown")
    emit(fig, "phase12_tiny_recovery")
    sns.scatterplot(data=tiny_comps, x="effective_magnification_25", y="component_pixels", hue="oracle25_detected", style="global_detected", s=100, ax=ax)
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlabel("Effective Linear Magnification (512 / Crop Side)"); ax.set_ylabel("Original Component Pixels")
    ax.set_title("TINY Component Pixels vs Effective Magnification")
    emit(fig, "phase12_magnification_vs_recovery")

    fig, ax = plt.subplots(figsize=(8, 5))
    sens_df = df_summary.copy()
    sns.barplot(data=sens_df, x="Method", y="Macro_Dice", palette="colorblind", ax=ax)
    ax.set_ylim(0, 1.05); ax.set_title("Oracle ROI Context Margin Sensitivity (Macro Dice)")
    emit(fig, "phase12_margin_sensitivity")

    fig, ax = plt.subplots(figsize=(8, 5))
    multi_melt = df_multi.melt(id_vars="Method", value_vars=["Complete_Detections", "Partial_Detections", "Complete_Misses"], var_name="Category", value_name="Image_Count")
    sns.barplot(data=multi_melt, x="Category", y="Image_Count", hue="Method", palette="colorblind", ax=ax)
    ax.set_title("Multi-Component Image Detection Breakdown")
    emit(fig, "phase12_multicomponent_recovery")

    empty_df = pd.DataFrame([
        {"Method": "Global UNet++", "Empty_Count": int(df_img["global_empty_prediction"].sum())},
        {"Method": "Oracle 25%", "Empty_Count": int(df_img["oracle25_empty_prediction"].sum())},
    ])
    fig, ax = plt.subplots(figsize=(6, 5))

def build_qualitative_panel(df_img, df_comp):
    rec_tiny_sid = df_comp[(df_comp["size_stratum"] == "TINY") & df_comp["recovered_by_oracle25"]].iloc[0]["sample_id"]
    miss_tiny_sid = df_comp[(df_comp["size_stratum"] == "TINY") & ~df_comp["oracle25_detected"]].iloc[0]["sample_id"]
    multi_imgs = df_img[df_img["component_count_original"] > 1]
    imp_multi_sid = multi_imgs.sort_values("dice_delta_oracle25_minus_global", ascending=False).iloc[0]["sample_id"]
    empty_rec_sid = df_img[df_img["global_empty_prediction"] & ~df_img["oracle25_empty_prediction"]].iloc[0]["sample_id"]
    no_imp_sid = df_img.sort_values("dice_delta_oracle25_minus_global", ascending=True).iloc[0]["sample_id"]

    selected_sids = list(dict.fromkeys([rec_tiny_sid, miss_tiny_sid, imp_multi_sid, empty_rec_sid, no_imp_sid]))

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(ROOT / "checkpoints/phase10_kub_unetpp_seed42_512/best.pt", model, restore_rng=False, map_location=device)
    model.eval()

    val_samples = pd.read_csv(TABLES_DIR / "kub_val_samples_sized.csv").set_index("sample_id")
    fig, axes = plt.subplots(len(selected_sids), 6, figsize=(18, 3.2 * len(selected_sids)), squeeze=False)

    for r_idx, sid in enumerate(selected_sids):
        srow = val_samples.loc[sid]
        img_path, mask_path = Path(srow["image_path"]), Path(srow["mask_path"])
        with Image.open(img_path) as im_f, Image.open(mask_path) as mf_f:
            raw_img = im_f.convert("L")
            raw_gt = (np.asarray(mf_f.convert("L")) > 0).astype(np.uint8)

        h_img, w_img = raw_gt.shape
        comps, _ = extract_gt_components(raw_gt)
        g_row = df_img[df_img["sample_id"] == sid].iloc[0]

        prob25 = np.load(CACHE_DIR / sid / "prob_combined.npy")
        mask25 = np.load(CACHE_DIR / sid / "mask_combined.npy")

        c0 = comps[0]
        geom0 = compute_square_crop(c0, (h_img, w_img), margin=0.25)
        c_y1, c_y2 = geom0["clip_y1"], geom0["clip_y2"]
        c_x1, c_x2 = geom0["clip_x1"], geom0["clip_x2"]
        crop_img_arr = np.asarray(raw_img)[c_y1:c_y2, c_x1:c_x2]

        axes[r_idx, 0].imshow(np.asarray(raw_img), cmap="gray"); axes[r_idx, 0].set_title(f"{sid[:8]}..\n{srow['category']}", fontsize=8); axes[r_idx, 0].axis("off")
        axes[r_idx, 1].imshow(raw_gt, cmap="gray"); axes[r_idx, 1].set_title(f"GT Mask\nComps={len(comps)}", fontsize=8); axes[r_idx, 1].axis("off")
        axes[r_idx, 2].imshow(mask25, cmap="gray"); axes[r_idx, 2].set_title(f"Global UNet++\nDice={g_row['global_dice']:.4f}", fontsize=8); axes[r_idx, 2].axis("off")
        axes[r_idx, 3].imshow(crop_img_arr, cmap="gray"); axes[r_idx, 3].set_title(f"Oracle Crop (25%)\nMag={geom0['effective_magnification']:.1f}x", fontsize=8); axes[r_idx, 3].axis("off")
        axes[r_idx, 4].imshow(prob25, cmap="magma", vmin=0, vmax=1); axes[r_idx, 4].set_title("Oracle Prob Map", fontsize=8); axes[r_idx, 4].axis("off")
        axes[r_idx, 5].imshow(mask25, cmap="gray"); axes[r_idx, 5].set_title(f"Oracle 25% Restored\nDice={g_row['oracle25_dice']:.4f}", fontsize=8); axes[r_idx, 5].axis("off")

    fig.suptitle("KUB Global UNet++ vs Oracle 25% ROI Qualitative Comparison", fontsize=12, fontweight="bold")
    plt.tight_layout()
    for ext in ("png", "svg", "pdf"):
        fig.savefig(QUAL_DIR / f"phase12_global_vs_oracle_panel.{ext}", dpi=320, bbox_inches="tight")
    plt.close(fig)
    (QUAL_DIR / "phase12_oracle_panel_selection.json").write_text(json.dumps({"selected_sample_ids": selected_sids}, indent=2), encoding="utf-8")


def main():
    df_img, df_comp, df_geom = run_eval_pass()
    df_summary, df_size_rec, df_multi = build_summary_tables(df_img, df_comp)
    plot_figures(df_img, df_comp, df_summary, df_size_rec, df_multi)
    build_qualitative_panel(df_img, df_comp)
    print("\nPhase 12 Oracle ROI upper-bound study completed successfully.")


if __name__ == "__main__":
    main()
