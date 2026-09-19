import json
import time
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import sys
sys.path.insert(0, str(Path("D:/Softfors/jup").resolve()))
from PIL import Image, ImageOps

from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint

from src.data.transforms import SegmentationTransform
def dice_binary(pred_mask: np.ndarray, gt_mask: np.ndarray, eps: float = 1e-7) -> float:
    p = pred_mask > 0
    g = gt_mask > 0
    tp = float((p & g).sum())
    fp = float((p & ~g).sum())
    fn = float((~p & g).sum())
    return (2.0 * tp + eps) / (2.0 * tp + fp + fn + eps)
from src.metrics.object_metrics import object_metrics
from scipy.ndimage import label, find_objects
from src.data.regional_dataset import crop_and_preprocess
from src.inference.regional_evaluator import restore_regional_probability, aggregate_and_fuse
from src.inference.predicted_roi import generate_predicted_rois, union_roi_area_fraction, apply_context_margin

PROJECT_ROOT = Path("D:/Softfors/jup").resolve()

def get_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def map_to_512(mask_orig: np.ndarray, meta_g) -> np.ndarray:
    scale = meta_g.scale
    left, top, right, bottom = meta_g.padding
    resized_width, resized_height = 512 - left - right, 512 - top - bottom
    m_pil = Image.fromarray((mask_orig * 255).astype(np.uint8))
    m_pil = m_pil.resize((resized_width, resized_height), Image.Resampling.NEAREST)
    m_pil = ImageOps.expand(m_pil, (left, top, right, bottom))
    return (np.asarray(m_pil) > 0).astype(np.uint8)

def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    tables_dir = PROJECT_ROOT / "reports" / "tables"
    audits_dir = PROJECT_ROOT / "reports" / "audits"
    tables_dir.mkdir(parents=True, exist_ok=True)
    audits_dir.mkdir(parents=True, exist_ok=True)
    
    global_ckpt_path = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512" / "best.pt"
    regional_ckpt_path = PROJECT_ROOT / "checkpoints" / "phase14_diag_regional_unet_oracletrain_a3_seed42_v1" / "best.pt"
    localizer_ckpt_path = PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1" / "best.pt"
    
    sha_global = get_sha256(global_ckpt_path)
    sha_regional = get_sha256(regional_ckpt_path)
    sha_localizer = get_sha256(localizer_ckpt_path)
    
    # 1. Models
    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(global_ckpt_path, global_model, restore_rng=False, map_location=device)
    global_model.eval()
    
    regional_model = create_model("unet", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(regional_ckpt_path, regional_model, restore_rng=False, map_location=device)
    regional_model.eval()
    
    localizer_model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16, heatmap_resolution=128).to(device)
    assert localizer_model.heatmap_resolution == 128, "CHECK_REQUIRED"
    load_training_checkpoint(localizer_ckpt_path, localizer_model, restore_rng=False, map_location=device)
    localizer_model.eval()
    
    # 2. Data
    manifest = pd.read_csv(PROJECT_ROOT / "manifests" / "val.csv")
    val_sized = pd.read_csv(PROJECT_ROOT / "reports" / "tables" / "kub_val_samples_sized.csv")
    manifest = pd.merge(manifest, val_sized[["sample_id", "view_type"]], on="sample_id")
    ff_samples = manifest[(manifest["view_type"] == "FULL_FIELD")].reset_index(drop=True)
    
    # 3. Stage 4D Proposal stream matching
    from src.data.kub_localizer_dataset import KUBLocalizerDataset
    from torch.utils.data import DataLoader
    
    val_ds = KUBLocalizerDataset(PROJECT_ROOT / "reports" / "tables" / "kub_val_samples_sized.csv", "VAL", resolution=512, sigma=0.75, heatmap_resolution=128)
    val_loader = DataLoader(val_ds, batch_size=4, shuffle=False, drop_last=False)
    
    proposals_per_image = {}
    total_proposals = 0
    areas = []
    
    with torch.inference_mode():
        for batch in val_loader:
            images = batch["image"].to(device)
            with torch.amp.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = localizer_model(images)
            probs = torch.sigmoid(logits).float().cpu().numpy()
            
            for i, sid in enumerate(batch["sample_id"]):
                pm = probs[i, 0]
                from src.data.transforms import ResizePadMetadata
                meta_loc = ResizePadMetadata(
                    scale=float(batch["scale"][i]),
                    resized_height=int(batch["resized_height"][i]),
                    resized_width=int(batch["resized_width"][i]),
                    padding=tuple(int(x) for x in batch["padding"][i])
                )
                
                h, w = int(batch["original_height"][i]), int(batch["original_width"][i])
                proposals = generate_predicted_rois(
                    pm, meta_loc, (h, w), threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30
                )
                area, _ = union_roi_area_fraction(proposals, (h, w))
                areas.append(area)
                total_proposals += len(proposals)
                proposals_per_image[sid] = proposals
                
    mean_props = total_proposals / 106
    zero_props = sum(1 for p in proposals_per_image.values() if len(p) == 0)
    
    val_df = pd.DataFrame([
        {"metric": "total_proposals", "measured": total_proposals, "expected": 494, "match": total_proposals == 494},
        {"metric": "mean_proposals", "measured": mean_props, "expected": 4.660377, "match": abs(mean_props - 4.660377) < 1e-4},
    ])
    val_df.to_csv(tables_dir / "phase14_part3c_stage4d_proposal_validation.csv", index=False)
    if not val_df["match"].all():
        print(val_df)
        assert False, "CHECK_REQUIRED: Stage-4D proposal generation does not match canonical."

    # Hard sets
    hard_tiny_set = {"b5030438b4d8c8e1e7798b030e66e2c4", "c129e1f57cdcd1d2bb4d3db269477eb3", "f63c8da742886f376cc28784fc2e7960", "283c8f85f8f8ed97d42cf38a42e5d7a6", "7e00e008b8b0e71ce05b9f71c4c92a2a", "5e206ab0e5c98d60d2bc4a8b7dd5b331", "f75c879d72a71bf68c92cd86b2403d92", "ff3eb2de8626fdb1db0248c5a452efeb", "8b1390d40e94f1c3dc62db9435b80dd8", "2d7b5f92ffdf1b2c4e610dcc416e87f1", "ce90e21a4f0dbb72bc2bd530ce2c7308", "4f48b9f1d0725a3d76b100cead0a5b28", "8cd6e556cf8f2bbaafc0da0c0e9b97b0", "c34fba375837651a24d5ba7b53ec6e2d", "01438a2e1d00d9220fc0298a0d4c1cf6", "6860bc808adad53cb439bbdeea76dbfc"}
    global_empty_set = {"c129e1f57cdcd1d2bb4d3db269477eb3", "f63c8da742886f376cc28784fc2e7960", "59fbe2a0bdc5417abf378cd4a86f1e29", "a7a40ab7852c0bf7c8bb19eb3159ab95", "40f1a4e525ad200d768ffbd9dc0b6667", "c8d234a9efdf2b67f2bc29af6abdfca6", "7ff32c3f7fb4f07a1bbbcbe10f6bd39f"}

    image_records = []
    component_records = []
    times_global, times_loc, times_ref_pred, times_fuse_pred, times_tot_pred, times_ref_ora, times_fuse_ora = [], [], [], [], [], [], []
    def map_global_to_original(prob512: np.ndarray, meta: 'ResizePadMetadata', original_shape: tuple) -> np.ndarray:
        scale = meta.scale
        rw, rh = meta.resized_width, meta.resized_height
        left, top, right, bottom = meta.padding
        h_orig, w_orig = original_shape
        
        # 1. Unpad
        valid_512 = prob512[top:top+rh, left:left+rw]
        
        # 2. Resize to orig
        prob_pil = Image.fromarray((valid_512 * 255.0).astype(np.uint8)).resize(
            (w_orig, h_orig), Image.Resampling.BILINEAR
        )
        return np.asarray(prob_pil, dtype=np.float32) / 255.0

    with torch.inference_mode():
        for idx, srow in ff_samples.iterrows():
            sid = srow["sample_id"]
            img_path = PROJECT_ROOT / srow["image_path"]
            with Image.open(img_path) as im:
                raw_img = im.convert("L")
            raw_mask_pil = Image.open(PROJECT_ROOT / srow["mask_path"]).convert("L")
            raw_mask = (np.asarray(raw_mask_pil) > 0).astype(np.uint8)
            t_orig = SegmentationTransform(512, False)
            tensor_g, _, meta_g = t_orig(raw_img, raw_mask_pil)
            
            t0 = time.perf_counter()
            with torch.amp.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits_g = global_model(tensor_g.unsqueeze(0).to(device))
            prob512_g = torch.sigmoid(logits_g)[0, 0].cpu().numpy()
            mask512_g = (prob512_g >= 0.50).astype(np.uint8)
            t1 = time.perf_counter()
            
            prob_orig_g = map_global_to_original(prob512_g, meta_g, (raw_img.height, raw_img.width))
            mask_orig_g = (prob_orig_g > 0.5).astype(np.uint8)
            t_glob_ms = (t1 - t0) * 1000.0
            times_global.append(t_glob_ms)
            
            # ORACLE
            gt_labels, num_gt = label(raw_mask, structure=np.ones((3,3)))
            oracle_proposals = []
            for i in range(1, num_gt + 1):
                sl = find_objects((gt_labels == i).astype(int))[0]
                y1, y2, x1, x2 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
                geom = apply_context_margin((y1, x1, y2, x2), (raw_img.height, raw_img.width), 0.20)
                oracle_proposals.append({"y1": y1, "y2": y2, "x1": x1, "x2": x2, "crop_geometry": geom})
                
            t_ora_ref_st = time.perf_counter()
            r_probs_o, r_supp_o = [], []
            for prop in oracle_proposals:
                bbox = (prop["y1"], prop["x1"], prop["y2"], prop["x2"])
                geom = apply_context_margin(bbox, (raw_img.height, raw_img.width), 0.20)
                crop_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                crop_t = torch.from_numpy(np.asarray(crop_pil, dtype=np.float32).copy()).unsqueeze(0) / 255.0
                with torch.amp.autocast(device_type=device.type, enabled=device.type == "cuda"):
                    logits_o = regional_model(crop_t.unsqueeze(0).to(device))
                p_o = torch.sigmoid(logits_o)[0,0].cpu().numpy()
                rp, rs = restore_regional_probability(p_o, geom, (raw_img.height, raw_img.width))
                r_probs_o.append(rp)
                r_supp_o.append(rs)
            t_ora_ref_ms = (time.perf_counter() - t_ora_ref_st) * 1000.0
            times_ref_ora.append(t_ora_ref_ms)
            
            t_ora_fuse_st = time.perf_counter()
            prob_ora = aggregate_and_fuse(prob_orig_g, r_probs_o, r_supp_o)
            mask_ora = (prob_ora >= 0.5).astype(np.uint8)
            t_ora_fuse_ms = (time.perf_counter() - t_ora_fuse_st) * 1000.0
            times_fuse_ora.append(t_ora_fuse_ms)
            
            # PREDICTED
            proposals = proposals_per_image[sid]
            t_loc_st = time.perf_counter()
            # simulation of localizer time
            dummy_loc = localizer_model(tensor_g.unsqueeze(0).to(device))
            t_loc_ms = (time.perf_counter() - t_loc_st) * 1000.0
            times_loc.append(t_loc_ms)
            
            t_prd_ref_st = time.perf_counter()
            r_probs_p, r_supp_p = [], []
            for prop in proposals:
                geom = prop["crop_geometry"]
                crop_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                crop_t = torch.from_numpy(np.asarray(crop_pil, dtype=np.float32).copy()).unsqueeze(0) / 255.0
                with torch.amp.autocast(device_type=device.type, enabled=device.type == "cuda"):
                    logits_p = regional_model(crop_t.unsqueeze(0).to(device))
                p_p = torch.sigmoid(logits_p)[0,0].cpu().numpy()
                rp, rs = restore_regional_probability(p_p, geom, (raw_img.height, raw_img.width))
                r_probs_p.append(rp)
                r_supp_p.append(rs)
            t_prd_ref_ms = (time.perf_counter() - t_prd_ref_st) * 1000.0
            times_ref_pred.append(t_prd_ref_ms)
            
            t_prd_fuse_st = time.perf_counter()
            prob_prd = aggregate_and_fuse(prob_orig_g, r_probs_p, r_supp_p)
            mask_prd = (prob_prd >= 0.5).astype(np.uint8)
            t_prd_fuse_ms = (time.perf_counter() - t_prd_fuse_st) * 1000.0
            times_fuse_pred.append(t_prd_fuse_ms)
            
            times_tot_pred.append(t_glob_ms + t_loc_ms + t_prd_ref_ms + t_prd_fuse_ms)
            
            mask512_o = map_to_512(mask_ora, meta_g)
            mask512_p = map_to_512(mask_prd, meta_g)
            gt512 = map_to_512(raw_mask, meta_g)
            
            dice_g_512 = dice_binary(mask512_g, gt512)
            dice_o_512 = dice_binary(mask512_o, gt512)
            dice_p_512 = dice_binary(mask512_p, gt512)
            
            dice_g_orig = dice_binary(mask_orig_g, raw_mask)
            dice_o_orig = dice_binary(mask_ora, raw_mask)
            dice_p_orig = dice_binary(mask_prd, raw_mask)
            
            fp_g = object_metrics(mask_orig_g, raw_mask, 1)["false_positive_predicted_components"]
            fp_o = object_metrics(mask_ora, raw_mask, 1)["false_positive_predicted_components"]
            fp_p = object_metrics(mask_prd, raw_mask, 1)["false_positive_predicted_components"]
            
            is_global_empty = sid in global_empty_set
            has_hard_tiny_image = False
            
            source_components = pd.read_csv(PROJECT_ROOT / "reports" / "tables" / "kub_val_components_sized.csv")
            sc = source_components[source_components.sample_id == sid].sort_values("component_id")
            
            for c_idx in range(1, num_gt + 1):
                c_mask = (gt_labels == c_idx).astype(np.uint8)
                c_strat = sc.iloc[c_idx - 1]["size_stratum"]
                is_hard_tiny = c_strat == "TINY" and sid in hard_tiny_set
                if is_hard_tiny: has_hard_tiny_image = True
                
                c_mask_512 = map_to_512(c_mask, meta_g)
                c_pixels = int(c_mask.sum())
                c_pixels_512 = int(c_mask_512.sum())
                
                ov_g = int((mask_orig_g & c_mask).sum())
                ov_o = int((mask_ora & c_mask).sum())
                ov_p = int((mask_prd & c_mask).sum())
                ov_g_512 = int((mask512_g & c_mask_512).sum())
                ov_o_512 = int((mask512_o & c_mask_512).sum())
                ov_p_512 = int((mask512_p & c_mask_512).sum())
                
                component_records.append({
                    "sample_id": sid,
                    "patient_id": srow["patient_id"],
                    "component_id": c_idx,
                    "size_stratum": c_strat,
                    "pixels_original": c_pixels,
                    "pixels_512": c_pixels_512,
                    "is_hard_tiny": is_hard_tiny,
                    "overlap_global_orig": ov_g,
                    "overlap_oracle_orig": ov_o,
                    "overlap_predicted_orig": ov_p,
                    "detected_global_orig": ov_g >= 1,
                    "detected_oracle_orig": ov_o >= 1,
                    "detected_predicted_orig": ov_p >= 1,
                    "cov90_global_orig": (ov_g / c_pixels) >= 0.90,
                    "cov90_oracle_orig": (ov_o / c_pixels) >= 0.90,
                    "cov90_predicted_orig": (ov_p / c_pixels) >= 0.90,
                    "overlap_global_512": ov_g_512,
                    "overlap_oracle_512": ov_o_512,
                    "overlap_predicted_512": ov_p_512,
                    "detected_global_512": ov_g_512 >= 1,
                    "detected_oracle_512": ov_o_512 >= 1,
                    "detected_predicted_512": ov_p_512 >= 1,
                    "cov90_global_512": (ov_g_512 / max(1, c_pixels_512)) >= 0.90,
                    "cov90_oracle_512": (ov_o_512 / max(1, c_pixels_512)) >= 0.90,
                    "cov90_predicted_512": (ov_p_512 / max(1, c_pixels_512)) >= 0.90,
                })
                
            ora_area, _ = union_roi_area_fraction(oracle_proposals, (raw_img.height, raw_img.width))
            prd_area, _ = union_roi_area_fraction(proposals, (raw_img.height, raw_img.width))
            image_records.append({
                "sample_id": sid,
                "patient_id": srow["patient_id"],
                "category": srow["category"],
                "global_dice_orig": dice_g_orig,
                "oracle_dice_orig": dice_o_orig,
                "predicted_dice_orig": dice_p_orig,
                "global_dice_512": dice_g_512,
                "oracle_dice_512": dice_o_512,
                "predicted_dice_512": dice_p_512,
                "oracle_proposals": len(oracle_proposals),
                "predicted_proposals": len(proposals),
                "oracle_roi_area_fraction": ora_area,
                "predicted_roi_area_fraction": prd_area,
                "global_fp_components": fp_g,
                "oracle_fp_components": fp_o,
                "predicted_fp_components": fp_p,
                "has_hard_tiny": has_hard_tiny_image,
                "global_empty": is_global_empty,
                "global_empty_pred_flag_orig": is_global_empty and (mask_orig_g.sum() == 0),
                "oracle_empty_pred_flag_orig": is_global_empty and (mask_ora.sum() == 0),
                "predicted_empty_pred_flag_orig": is_global_empty and (mask_prd.sum() == 0),
                "global_empty_pred_flag_512": is_global_empty and (mask512_g.sum() == 0),
                "oracle_empty_pred_flag_512": is_global_empty and (mask512_o.sum() == 0),
                "predicted_empty_pred_flag_512": is_global_empty and (mask512_p.sum() == 0),
                "global_time_ms": t_glob_ms,
                "localizer_time_ms": t_loc_ms,
                "refiner_time_ms": t_prd_ref_ms,
                "fusion_time_ms": t_prd_fuse_ms,
                "total_predicted_time_ms": t_glob_ms + t_loc_ms + t_prd_ref_ms + t_prd_fuse_ms
            })
            if (idx + 1) % 20 == 0:
                print(f"[{idx+1}/106]")

    df_img = pd.DataFrame(image_records)
    df_comp = pd.DataFrame(component_records)
    
    # Save base tables
    df_img.to_csv(tables_dir / "phase14_part3_image_metrics.csv", index=False)
    df_comp.to_csv(tables_dir / "phase14_part3_component_metrics.csv", index=False)
    
    # Mode Summary
    mode_rows = []
    modes = [("GLOBAL_ONLY", "global"), ("ORACLE_REGIONAL", "oracle"), ("PREDICTED_REGIONAL", "predicted")]
    for mname, pfx in modes:
        mode_rows.append({
            "mode": mname,
            "mean_dice_512": df_img[f"{pfx}_dice_512"].mean(),
            "mean_dice_orig": df_img[f"{pfx}_dice_orig"].mean(),
            "median_dice_512": df_img[f"{pfx}_dice_512"].median(),
            "median_dice_orig": df_img[f"{pfx}_dice_orig"].median(),
            "overall_recall90_512": df_comp[f"cov90_{pfx}_512"].mean(),
            "overall_recall90_orig": df_comp[f"cov90_{pfx}_orig"].mean(),
            "tiny_recall90_512": df_comp[df_comp.size_stratum == "TINY"][f"cov90_{pfx}_512"].mean(),
            "tiny_recall90_orig": df_comp[df_comp.size_stratum == "TINY"][f"cov90_{pfx}_orig"].mean(),
            "small_recall90_512": df_comp[df_comp.size_stratum == "SMALL"][f"cov90_{pfx}_512"].mean(),
            "small_recall90_orig": df_comp[df_comp.size_stratum == "SMALL"][f"cov90_{pfx}_orig"].mean(),
            "medium_recall90_512": df_comp[df_comp.size_stratum == "MEDIUM"][f"cov90_{pfx}_512"].mean(),
            "medium_recall90_orig": df_comp[df_comp.size_stratum == "MEDIUM"][f"cov90_{pfx}_orig"].mean(),
            "large_recall90_512": df_comp[df_comp.size_stratum == "LARGE"][f"cov90_{pfx}_512"].mean(),
            "large_recall90_orig": df_comp[df_comp.size_stratum == "LARGE"][f"cov90_{pfx}_orig"].mean(),
            "hard_tiny_recovered_512": df_comp[df_comp.is_hard_tiny][f"detected_{pfx}_512"].sum(),
            "hard_tiny_recovered_orig": df_comp[df_comp.is_hard_tiny][f"detected_{pfx}_orig"].sum(),
            "global_empty_recovered_512": df_img[df_img.global_empty][f"{pfx}_empty_pred_flag_512"].sum(),
            "global_empty_recovered_orig": df_img[df_img.global_empty][f"{pfx}_empty_pred_flag_orig"].sum(),
            "mean_fp_per_image": df_img[f"{pfx}_fp_components"].mean(),
        })
    df_mode = pd.DataFrame(mode_rows)
    df_mode.to_csv(tables_dir / "phase14_part3_mode_summary.csv", index=False)
    
    # Hard Case Summary
    hc_rows = []
    for mname, pfx in modes:
        hc_rows.append({
            "mode": mname,
            "hard_tiny_recovered_512": df_comp[df_comp.is_hard_tiny][f"detected_{pfx}_512"].sum(),
            "hard_tiny_recovered_orig": df_comp[df_comp.is_hard_tiny][f"detected_{pfx}_orig"].sum(),
            "hard_tiny_total": df_comp.is_hard_tiny.sum(),
            "global_empty_recovered_512": df_img[df_img.global_empty][f"{pfx}_empty_pred_flag_512"].sum(),
            "global_empty_recovered_orig": df_img[df_img.global_empty][f"{pfx}_empty_pred_flag_orig"].sum(),
            "global_empty_total": df_img.global_empty.sum(),
        })
    pd.DataFrame(hc_rows).to_csv(tables_dir / "phase14_part3_hardcase_summary.csv", index=False)
    
    # Proposal Burden
    pb_rows = []
    for mname, pfx in [("ORACLE_REGIONAL", "oracle"), ("PREDICTED_REGIONAL", "predicted")]:
        props = df_img[f"{pfx}_proposals"]
        areas = df_img[f"{pfx}_roi_area_fraction"]
        pb_rows.append({
            "mode": mname,
            "mean_proposals": props.mean(),
            "median_proposals": props.median(),
            "zero_proposal_images": (props == 0).sum(),
            "one_proposal_images": (props == 1).sum(),
            "multi_proposal_images": (props > 1).sum(),
            "max_proposals": props.max(),
            "mean_roi_area_fraction": areas.mean(),
            "median_roi_area_fraction": areas.median(),
            "p90_roi_area_fraction": areas.quantile(0.90),
            "p95_roi_area_fraction": areas.quantile(0.95),
            "max_roi_area_fraction": areas.max()
        })
    pd.DataFrame(pb_rows).to_csv(tables_dir / "phase14_part3_roi_proposal_burden.csv", index=False)
    
    # Runtime
    runtime_rows = [
        {"pipeline": "GLOBAL_ONLY", "component": "Global UNet++", "mean_ms": df_img["global_time_ms"].mean(), "median_ms": df_img["global_time_ms"].median(), "p90_ms": df_img["global_time_ms"].quantile(0.90)},
        {"pipeline": "PREDICTED_REGIONAL", "component": "Global UNet++", "mean_ms": df_img["global_time_ms"].mean(), "median_ms": df_img["global_time_ms"].median(), "p90_ms": df_img["global_time_ms"].quantile(0.90)},
        {"pipeline": "PREDICTED_REGIONAL", "component": "Stage-4D Localizer", "mean_ms": df_img["localizer_time_ms"].mean(), "median_ms": df_img["localizer_time_ms"].median(), "p90_ms": df_img["localizer_time_ms"].quantile(0.90)},
        {"pipeline": "PREDICTED_REGIONAL", "component": "Regional Refiner UNet", "mean_ms": df_img["refiner_time_ms"].mean(), "median_ms": df_img["refiner_time_ms"].median(), "p90_ms": df_img["refiner_time_ms"].quantile(0.90)},
        {"pipeline": "PREDICTED_REGIONAL", "component": "Aggregation & Fusion", "mean_ms": df_img["fusion_time_ms"].mean(), "median_ms": df_img["fusion_time_ms"].median(), "p90_ms": df_img["fusion_time_ms"].quantile(0.90)},
        {"pipeline": "PREDICTED_REGIONAL", "component": "Total Pipeline", "mean_ms": df_img["total_predicted_time_ms"].mean(), "median_ms": df_img["total_predicted_time_ms"].median(), "p90_ms": df_img["total_predicted_time_ms"].quantile(0.90)},
        {"pipeline": "ORACLE_REGIONAL (Descriptive)", "component": "Regional Refiner UNet", "mean_ms": np.mean(times_ref_ora), "median_ms": np.median(times_ref_ora), "p90_ms": np.percentile(times_ref_ora, 90)},
        {"pipeline": "ORACLE_REGIONAL (Descriptive)", "component": "Aggregation & Fusion", "mean_ms": np.mean(times_fuse_ora), "median_ms": np.median(times_fuse_ora), "p90_ms": np.percentile(times_fuse_ora, 90)},
    ]
    pd.DataFrame(runtime_rows).to_csv(tables_dir / "phase14_part3_runtime.csv", index=False)
    
    # Gate Evaluation
    Tg, Dg = 0.780822, 0.652776
    To_512 = df_mode.loc[df_mode["mode"] == "ORACLE_REGIONAL", "tiny_recall90_512"].iloc[0]
    Tp_512 = df_mode.loc[df_mode["mode"] == "PREDICTED_REGIONAL", "tiny_recall90_512"].iloc[0]
    Do_512 = df_mode.loc[df_mode["mode"] == "ORACLE_REGIONAL", "mean_dice_512"].iloc[0]
    Dp_512 = df_mode.loc[df_mode["mode"] == "PREDICTED_REGIONAL", "mean_dice_512"].iloc[0]
    
    ht_p = df_mode.loc[df_mode["mode"] == "PREDICTED_REGIONAL", "hard_tiny_recovered_512"].iloc[0]
    ge_p = df_mode.loc[df_mode["mode"] == "PREDICTED_REGIONAL", "global_empty_recovered_512"].iloc[0]
    
    G = To_512 - Tg
    R = (Tp_512 - Tg) / G if G > 0 else "NOT_DEFINED"
    
    step1 = (G >= 0.05) and (Do_512 >= 0.632776)
    step2 = (R >= 0.50) if G > 0 else "NOT_DEFINED"
    step3 = (Tp_512 >= 0.780822) and (Dp_512 >= 0.632776) and (ht_p >= 2) and (ge_p >= 1)
    
    if not step1:
        fclass = "DIAGNOSTIC_REFUTED_REFINER_INEFFECTIVE"
        ph15 = "NOT_AUTHORIZED"
    elif not step2:
        fclass = "DIAGNOSTIC_PROPOSAL_BOTTLENECK"
        ph15 = "NOT_AUTHORIZED"
    elif not step3:
        fclass = "DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT"
        ph15 = "NOT_AUTHORIZED"
    else:
        fclass = "DIAGNOSTIC_PROMISING_SUPPORTING_REFINER"
        ph15 = "ELIGIBLE_FOR_SUPERVISOR_REVIEW"
        
    audit = {
        "status": "PASS",
        "diagnostic_classification": fclass,
        "phase15_status": ph15,
        "frozen_references": {"Tg": Tg, "Dg": Dg},
        "official_512_space": {"To_512": To_512, "Tp_512": Tp_512, "Do_512": Do_512, "Dp_512": Dp_512, "G": G, "R": R},
        "gates": {"step1_pass": bool(step1), "step2_pass": bool(step2), "step3_pass": bool(step3)}
    }
    with open(audits_dir / "phase14_part3_diagnostic_evaluation.json", "w") as f:
        json.dump(audit, f, indent=2)

    R_str = "NOT_DEFINED" if R == "NOT_DEFINED" else f"{R:.6f}"
    md = f"""# Phase 14 Part 3C - Corrected Diagnostic Evaluation
## Gate Arithmetic
- Tg: {Tg:.6f}, Dg: {Dg:.6f}
- To_512: {To_512:.6f}, Tp_512: {Tp_512:.6f}
- Do_512: {Do_512:.6f}, Dp_512: {Dp_512:.6f}
- G: {G:+.6f}, R: {R_str}

Step 1: {step1}, Step 2: {step2}, Step 3: {step3}

Final Classification: {fclass}
"""
    with open(audits_dir / "phase14_part3_diagnostic_evaluation.md", "w") as f:
        f.write(md)

if __name__ == "__main__":
    main()
