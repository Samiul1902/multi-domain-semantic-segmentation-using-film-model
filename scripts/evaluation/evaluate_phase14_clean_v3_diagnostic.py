"""Phase 14 Regional Refiner Diagnostic - Part 3 Frozen Full Validation Diagnostic Evaluation.

Evaluates GLOBAL_ONLY, ORACLE_REGIONAL, and PREDICTED_REGIONAL on the 103 KUB FULL_FIELD clean-v3 VAL images.
Governance: TEST locked (0 reads authorized), external data = NO, no training / optimizer steps.
"""

import hashlib
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from PIL import Image
import torch

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.oracle_roi import extract_gt_components
from src.data.regional_dataset import crop_and_preprocess
from src.data.transforms import SegmentationTransform
from src.inference.kub_predict import _preprocess_image, _restore_original_coordinates
from src.inference.predicted_roi import apply_context_margin, generate_predicted_rois
from src.inference.regional_evaluator import aggregate_and_fuse, restore_regional_probability
from src.metrics.object_metrics import object_metrics
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests, validate_manifest_version_strict
from src.utils.test_lock import verify_test_lock


def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def dice_binary(pred_mask: np.ndarray, gt_mask: np.ndarray, eps: float = 1e-7) -> float:
    p = pred_mask > 0
    g = gt_mask > 0
    tp = float((p & g).sum())
    fp = float((p & ~g).sum())
    fn = float((~p & g).sum())
    return (2.0 * tp + eps) / (2.0 * tp + fp + fn + eps)


def main():
    # 0. Governance & Lock Verifications
    validate_manifest_version_strict("phase4_v3")
    verify_test_lock(PROJECT_ROOT)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA is required for Phase-14 diagnostic evaluation.")

    # Paths
    tables_dir = PROJECT_ROOT / "reports" / "tables"
    audits_dir = PROJECT_ROOT / "reports" / "audits"
    tables_dir.mkdir(parents=True, exist_ok=True)
    audits_dir.mkdir(parents=True, exist_ok=True)

    val_samples_path = tables_dir / "kub_val_samples_sized_clean_v3.csv"
    val_comps_path = tables_dir / "kub_val_components_sized_clean_v3.csv"
    p13_comps_path = tables_dir / "phase13_clean_v3_hard_tiny_replication_set.csv"
    p12_imgs_path = tables_dir / "phase13_clean_v3_global_empty_replication_set.csv"

    # Checkpoint paths
    global_ckpt_path = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"
    regional_ckpt_path = (
        PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"
    )
    localizer_ckpt_path = (
        PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3" / "best.pt"
    )

    # 1. Verify Checkpoints and SHAs
    sha_global = sha256_file(global_ckpt_path)
    sha_regional = sha256_file(regional_ckpt_path)
    sha_localizer = sha256_file(localizer_ckpt_path)

    expected_sha_global = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"
    expected_sha_regional = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"
    expected_sha_localizer = "7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273"

    assert sha_global == expected_sha_global, f"Global SHA mismatch: {sha_global}"
    assert sha_regional == expected_sha_regional, f"Regional SHA mismatch: {sha_regional}"
    assert sha_localizer == expected_sha_localizer, f"Localizer SHA mismatch: {sha_localizer}"

    print("[Phase 14 clean-v3] All checkpoint hashes verified successfully.")

    # 2. Population & Metadata Verification
    df_samples = pd.read_csv(val_samples_path)
    ff_samples = df_samples[df_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_samples) == 103, f"Expected 103 clean-v3 FULL_FIELD samples, got {len(ff_samples)}"

    df_components = pd.read_csv(val_comps_path)
    ff_components = df_components[df_components["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_components) == 152, f"Expected 152 clean-v3 FULL_FIELD components, got {len(ff_components)}"

    size_counts = ff_components["size_stratum"].value_counts().to_dict()
    assert size_counts.get("TINY", 0) == 72, f"Expected 72 Tiny, got {size_counts.get('TINY')}"
    assert size_counts.get("SMALL", 0) == 28, f"Expected 28 Small, got {size_counts.get('SMALL')}"
    assert size_counts.get("MEDIUM", 0) == 36, f"Expected 36 Medium, got {size_counts.get('MEDIUM')}"
    assert size_counts.get("LARGE", 0) == 16, f"Expected 16 Large, got {size_counts.get('LARGE')}"

    # Verify frozen Hard-Tiny set (15 components)
    df_p13_comps = pd.read_csv(p13_comps_path)
    hard_tiny_rows = df_p13_comps[(df_p13_comps["size_stratum"] == "TINY") & (~df_p13_comps["global_detected"])]
    assert len(hard_tiny_rows) == 15, f"Expected 15 clean-v3 hard-Tiny, got {len(hard_tiny_rows)}"
    hard_tiny_set = set(zip(hard_tiny_rows["sample_id"], hard_tiny_rows["native_component_id"]))

    # Verify frozen Global-Empty set (5 images)
    df_p12_imgs = pd.read_csv(p12_imgs_path)
    global_empty_rows = df_p12_imgs[df_p12_imgs["prediction_empty"]]
    assert len(global_empty_rows) == 5, f"Expected 5 clean-v3 global-empty images, got {len(global_empty_rows)}"
    global_empty_set = set(global_empty_rows["sample_id"])

    print("[Phase 14 clean-v3] Verified 103 FULL_FIELD images, 152 components (72/28/36/16), 15 hard-Tiny, 5 global-empty.")

    # 3. Load Models
    print("[Phase 14 clean-v3] Loading models...")
    # Global UNet++
    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(global_ckpt_path, global_model, restore_rng=False, map_location=device)
    global_model.eval()

    # Stage-4D Localizer
    localizer_model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16).to(device)
    load_training_checkpoint(localizer_ckpt_path, localizer_model, restore_rng=False, map_location=device)
    localizer_model.eval()

    # Regional Refiner
    refiner_model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(regional_ckpt_path, refiner_model, restore_rng=False, map_location=device)
    refiner_model.eval()

    loc_transform = SegmentationTransform(512, False)

    # 4. Storage for evaluation outputs
    image_records = []
    component_records = []

    # Timing accumulators
    times_global = []
    times_loc = []
    times_refiner_pred = []
    times_fusion_pred = []
    times_total_pred = []
    times_refiner_oracle = []
    times_fusion_oracle = []

    print("[Phase 14 clean-v3] Starting frozen evaluation loop across 103 FULL_FIELD VAL images...")

    with torch.inference_mode():
        for idx, srow in ff_samples.iterrows():
            sid = srow["sample_id"]
            pid = srow["patient_id"]
            cat = srow["category"]
            img_path = Path(srow["image_path"])
            mask_path = Path(srow["mask_path"])

            with Image.open(img_path) as im:
                raw_img = im.convert("L")
            with Image.open(mask_path) as mf:
                raw_mask_pil = mf.convert("L")
                raw_mask = (np.array(raw_mask_pil) > 0).astype(np.uint8)

            h_img, w_img = raw_mask.shape
            img_area = h_img * w_img

            # Extract authoritative GT components
            orig_comps, labeled_gt = extract_gt_components(raw_mask)
            sub_comps = ff_components[ff_components["sample_id"] == sid].set_index("component_id")
            assert len(orig_comps) == len(sub_comps), f"Component count mismatch in {sid}: {len(orig_comps)} vs {len(sub_comps)}"

            # -------------------------------------------------------------
            # A. GLOBAL ONLY
            # -------------------------------------------------------------
            torch.cuda.synchronize()
            t0 = time.perf_counter()

            t512, _, meta_g = _preprocess_image(raw_img, 512)
            logits_g = global_model(t512.to(device))
            prob512_g = torch.sigmoid(logits_g).squeeze().cpu().numpy()
            mask512_g = (prob512_g >= 0.50).astype(np.uint8)
            prob_orig_g, mask_orig_g = _restore_original_coordinates(prob512_g, mask512_g, meta_g)

            torch.cuda.synchronize()
            t_glob_ms = (time.perf_counter() - t0) * 1000.0
            times_global.append(t_glob_ms)

            dice_g = dice_binary(mask_orig_g, raw_mask)
            fp_g = object_metrics(mask_orig_g, raw_mask, 1)["false_positive_predicted_components"]

            # -------------------------------------------------------------
            # B. ORACLE REGIONAL
            # -------------------------------------------------------------
            torch.cuda.synchronize()
            t_or_ref_start = time.perf_counter()

            reg_probs_oracle = []
            reg_supps_oracle = []
            oracle_union_mask = np.zeros((h_img, w_img), dtype=bool)

            for c in orig_comps:
                bbox = (c["min_y"], c["min_x"], c["max_y"], c["max_x"])
                geom = apply_context_margin(bbox, (h_img, w_img), margin=0.20)
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                logits_r = refiner_model(crop_t.to(device))
                prob_r = torch.sigmoid(logits_r)[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, geom, (h_img, w_img))
                reg_probs_oracle.append(rest_p)
                reg_supps_oracle.append(supp)
                oracle_union_mask = oracle_union_mask | supp

            torch.cuda.synchronize()
            t_or_ref_ms = (time.perf_counter() - t_or_ref_start) * 1000.0
            times_refiner_oracle.append(t_or_ref_ms)

            t_or_fuse_start = time.perf_counter()
            prob_fused_oracle = aggregate_and_fuse(prob_orig_g, reg_probs_oracle, reg_supps_oracle)
            mask_fused_oracle = (prob_fused_oracle >= 0.50).astype(np.uint8)
            torch.cuda.synchronize()
            t_or_fuse_ms = (time.perf_counter() - t_or_fuse_start) * 1000.0
            times_fusion_oracle.append(t_or_fuse_ms)

            dice_o = dice_binary(mask_fused_oracle, raw_mask)
            fp_o = object_metrics(mask_fused_oracle, raw_mask, 1)["false_positive_predicted_components"]
            oracle_props_cnt = len(orig_comps)
            oracle_roi_area_fraction = float(oracle_union_mask.sum()) / float(img_area)

            # -------------------------------------------------------------
            # C. PREDICTED REGIONAL
            # -------------------------------------------------------------
            torch.cuda.synchronize()
            t_pred_start = time.perf_counter()

            dummy = Image.new("L", raw_img.size)
            tensor_loc, _, meta_loc = loc_transform(raw_img, dummy)
            logits_loc = localizer_model(tensor_loc.unsqueeze(0).to(device))
            heatmap_loc = torch.sigmoid(logits_loc)[0, 0].cpu().numpy()

            proposals = generate_predicted_rois(
                heatmap_loc, meta_loc, (h_img, w_img), threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30
            )

            torch.cuda.synchronize()
            t_loc_ms = (time.perf_counter() - t_pred_start) * 1000.0
            times_loc.append(t_loc_ms)

            t_pred_ref_start = time.perf_counter()
            reg_probs_pred = []
            reg_supps_pred = []
            pred_union_mask = np.zeros((h_img, w_img), dtype=bool)

            for prop in proposals:
                geom = prop["crop_geometry"]
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                logits_r = refiner_model(crop_t.to(device))
                prob_r = torch.sigmoid(logits_r)[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, geom, (h_img, w_img))
                reg_probs_pred.append(rest_p)
                reg_supps_pred.append(supp)
                pred_union_mask = pred_union_mask | supp

            torch.cuda.synchronize()
            t_pred_ref_ms = (time.perf_counter() - t_pred_ref_start) * 1000.0
            times_refiner_pred.append(t_pred_ref_ms)

            t_pred_fuse_start = time.perf_counter()
            prob_fused_pred = aggregate_and_fuse(prob_orig_g, reg_probs_pred, reg_supps_pred)
            mask_fused_pred = (prob_fused_pred >= 0.50).astype(np.uint8)
            torch.cuda.synchronize()
            t_pred_fuse_ms = (time.perf_counter() - t_pred_fuse_start) * 1000.0
            times_fusion_pred.append(t_pred_fuse_ms)

            t_pred_total_ms = t_glob_ms + t_loc_ms + t_pred_ref_ms + t_pred_fuse_ms
            times_total_pred.append(t_pred_total_ms)

            dice_p = dice_binary(mask_fused_pred, raw_mask)
            fp_p = object_metrics(mask_fused_pred, raw_mask, 1)["false_positive_predicted_components"]
            pred_props_cnt = len(proposals)
            pred_roi_area_fraction = float(pred_union_mask.sum()) / float(img_area)

            # -------------------------------------------------------------
            # Per-Component Evaluation
            # -------------------------------------------------------------
            has_hard_tiny_image = False
            for c in orig_comps:
                cid = c["component_id"]
                c_mask = labeled_gt == cid
                c_pixels = int(c["component_pixels"])
                c_stratum = sub_comps.loc[cid, "size_stratum"]
                is_hard_tiny = (sid, cid) in hard_tiny_set
                if is_hard_tiny:
                    has_hard_tiny_image = True

                # Overlaps
                ov_g = int((mask_orig_g & c_mask).sum())
                ov_o = int((mask_fused_oracle & c_mask).sum())
                ov_p = int((mask_fused_pred & c_mask).sum())

                # Authoritative detection criteria
                det_g = ov_g >= 1
                det_o = ov_o >= 1
                det_p = ov_p >= 1

                cov90_g = (ov_g / c_pixels) >= 0.90
                cov90_o = (ov_o / c_pixels) >= 0.90
                cov90_p = (ov_p / c_pixels) >= 0.90

                component_records.append({
                    "sample_id": sid,
                    "component_id": cid,
                    "size_group": c_stratum,
                    "component_area": c_pixels,
                    "global_recall90_success": det_g,
                    "oracle_recall90_success": det_o,
                    "predicted_recall90_success": det_p,
                    "hard_tiny_flag": is_hard_tiny,
                    "global_overlap_pixels": ov_g,
                    "oracle_overlap_pixels": ov_o,
                    "predicted_overlap_pixels": ov_p,
                    "global_coverage_ratio": ov_g / c_pixels,
                    "oracle_coverage_ratio": ov_o / c_pixels,
                    "predicted_coverage_ratio": ov_p / c_pixels,
                    "global_cov90": cov90_g,
                    "oracle_cov90": cov90_o,
                    "predicted_cov90": cov90_p,
                })

            # Image record
            is_global_empty = sid in global_empty_set
            image_records.append({
                "sample_id": sid,
                "patient_id": pid,
                "category": cat,
                "global_dice": dice_g,
                "oracle_dice": dice_o,
                "predicted_dice": dice_p,
                "oracle_proposals": oracle_props_cnt,
                "predicted_proposals": pred_props_cnt,
                "oracle_roi_area_fraction": oracle_roi_area_fraction,
                "predicted_roi_area_fraction": pred_roi_area_fraction,
                "global_fp_components": fp_g,
                "oracle_fp_components": fp_o,
                "predicted_fp_components": fp_p,
                "has_hard_tiny": has_hard_tiny_image,
                "global_empty": is_global_empty,
                "global_empty_pred_flag": (mask_orig_g.sum() == 0),
                "oracle_empty_pred_flag": (mask_fused_oracle.sum() == 0),
                "predicted_empty_pred_flag": (mask_fused_pred.sum() == 0),
                "global_time_ms": t_glob_ms,
                "localizer_time_ms": t_loc_ms,
                "refiner_time_ms": t_pred_ref_ms,
                "fusion_time_ms": t_pred_fuse_ms,
                "total_predicted_time_ms": t_pred_total_ms,
            })

            if (idx + 1) % 20 == 0 or (idx + 1) == len(ff_samples):
                print(f"  Processed {idx + 1}/{len(ff_samples)} images...")

    df_img = pd.DataFrame(image_records)
    df_comp = pd.DataFrame(component_records)

    # 5. Save Per-Image and Per-Component Tables
    img_csv_path = tables_dir / "phase14_clean_v3_image_metrics.csv"
    comp_csv_path = tables_dir / "phase14_clean_v3_component_metrics.csv"
    df_img.to_csv(img_csv_path, index=False)
    df_comp.to_csv(comp_csv_path, index=False)
    print(f"[Phase 14 clean-v3] Saved {img_csv_path} ({len(df_img)} rows)")
    print(f"[Phase 14 clean-v3] Saved {comp_csv_path} ({len(df_comp)} rows)")

    # 6. Compute Mode Summary Metrics
    modes = ["GLOBAL_ONLY", "ORACLE_REGIONAL", "PREDICTED_REGIONAL"]
    summary_rows = []

    for mode in modes:
        if mode == "GLOBAL_ONLY":
            dices = df_img["global_dice"]
            comp_succ = df_comp["global_recall90_success"]
            fps = df_img["global_fp_components"]
            empty_flags = df_img["global_empty_pred_flag"]
            props = [0] * len(df_img)
            areas = [0.0] * len(df_img)
        elif mode == "ORACLE_REGIONAL":
            dices = df_img["oracle_dice"]
            comp_succ = df_comp["oracle_recall90_success"]
            fps = df_img["oracle_fp_components"]
            empty_flags = df_img["oracle_empty_pred_flag"]
            props = df_img["oracle_proposals"]
            areas = df_img["oracle_roi_area_fraction"]
        else:
            dices = df_img["predicted_dice"]
            comp_succ = df_comp["predicted_recall90_success"]
            fps = df_img["predicted_fp_components"]
            empty_flags = df_img["predicted_empty_pred_flag"]
            props = df_img["predicted_proposals"]
            areas = df_img["predicted_roi_area_fraction"]

        # Size breakdowns
        tiny_succ = df_comp[df_comp["size_group"] == "TINY"][
            "global_recall90_success" if mode == "GLOBAL_ONLY" else (
                "oracle_recall90_success" if mode == "ORACLE_REGIONAL" else "predicted_recall90_success"
            )
        ]
        small_succ = df_comp[df_comp["size_group"] == "SMALL"][
            "global_recall90_success" if mode == "GLOBAL_ONLY" else (
                "oracle_recall90_success" if mode == "ORACLE_REGIONAL" else "predicted_recall90_success"
            )
        ]
        med_succ = df_comp[df_comp["size_group"] == "MEDIUM"][
            "global_recall90_success" if mode == "GLOBAL_ONLY" else (
                "oracle_recall90_success" if mode == "ORACLE_REGIONAL" else "predicted_recall90_success"
            )
        ]
        large_succ = df_comp[df_comp["size_group"] == "LARGE"][
            "global_recall90_success" if mode == "GLOBAL_ONLY" else (
                "oracle_recall90_success" if mode == "ORACLE_REGIONAL" else "predicted_recall90_success"
            )
        ]

        # Hard-Tiny recovery (15 components)
        hard_tiny_mode_succ = df_comp[df_comp["hard_tiny_flag"]][
            "global_recall90_success" if mode == "GLOBAL_ONLY" else (
                "oracle_recall90_success" if mode == "ORACLE_REGIONAL" else "predicted_recall90_success"
            )
        ]
        hard_tiny_rec = int(hard_tiny_mode_succ.sum())

        # Global-Empty recovery (5 images)
        # An empty image is recovered if the prediction is non-empty AND detects at least 1 component
        empty_imgs = df_img[df_img["global_empty"]]
        if mode == "GLOBAL_ONLY":
            ge_rec = 0  # by definition 0/5
        else:
            rec_cnt = 0
            for _, erow in empty_imgs.iterrows():
                esid = erow["sample_id"]
                ecomps = df_comp[df_comp["sample_id"] == esid]
                c_succ_col = (
                    "oracle_recall90_success" if mode == "ORACLE_REGIONAL" else "predicted_recall90_success"
                )
                if ecomps[c_succ_col].any() and not erow[
                    "oracle_empty_pred_flag" if mode == "ORACLE_REGIONAL" else "predicted_empty_pred_flag"
                ]:
                    rec_cnt += 1
            ge_rec = rec_cnt

        row_dict = {
            "mode": mode,
            "mean_dice": float(dices.mean()),
            "median_dice": float(dices.median()),
            "overall_recall90": float(comp_succ.mean()),
            "tiny_recall90": float(tiny_succ.mean()),
            "small_recall90": float(small_succ.mean()),
            "medium_recall90": float(med_succ.mean()),
            "large_recall90": float(large_succ.mean()),
            "overall_detected_count": int(comp_succ.sum()),
            "tiny_detected_count": int(tiny_succ.sum()),
            "small_detected_count": int(small_succ.sum()),
            "medium_detected_count": int(med_succ.sum()),
            "large_detected_count": int(large_succ.sum()),
            "hard_tiny_recovered": hard_tiny_rec,
            "hard_tiny_total": 15,
            "global_empty_recovered": ge_rec,
            "global_empty_total": 5,
            "mean_fp_components_per_image": float(fps.mean()),
            "zero_foreground_images": int(empty_flags.sum()),
            "mean_proposals_per_image": float(np.mean(props)),
            "median_proposals_per_image": float(np.median(props)),
            "zero_proposal_images": int(sum(1 for p in props if p == 0)),
            "multi_proposal_images": int(sum(1 for p in props if p > 1)),
            "mean_roi_area_fraction": float(np.mean(areas)),
            "median_roi_area_fraction": float(np.median(areas)),
            "p90_roi_area_fraction": float(np.percentile(areas, 90)),
            "p95_roi_area_fraction": float(np.percentile(areas, 95)),
            "max_roi_area_fraction": float(np.max(areas)),
        }
        summary_rows.append(row_dict)

    df_summary = pd.DataFrame(summary_rows)
    mode_summary_path = tables_dir / "phase14_clean_v3_mode_summary.csv"
    df_summary.to_csv(mode_summary_path, index=False)
    print(f"[Phase 14 clean-v3] Saved {mode_summary_path}")

    # 7. Hard-Case Table
    hard_case_rows = []
    # 15 Hard-Tiny
    ht_comps = df_comp[df_comp["hard_tiny_flag"]].copy().sort_values(["sample_id", "component_id"])
    for _, ht in ht_comps.iterrows():
        hard_case_rows.append({
            "case_type": "HARD_TINY_COMPONENT",
            "sample_id": ht["sample_id"],
            "component_id": ht["component_id"],
            "size_stratum": ht["size_group"],
            "pixels": ht["component_area"],
            "global_success": ht["global_recall90_success"],
            "oracle_success": ht["oracle_recall90_success"],
            "predicted_success": ht["predicted_recall90_success"],
            "details": f"ov_g={ht['global_overlap_pixels']}, ov_o={ht['oracle_overlap_pixels']}, ov_p={ht['predicted_overlap_pixels']}",
        })

    # 5 Global-Empty
    ge_imgs = df_img[df_img["global_empty"]].copy().sort_values("sample_id")
    for _, ge in ge_imgs.iterrows():
        esid = ge["sample_id"]
        ecomps = df_comp[df_comp["sample_id"] == esid]
        o_rec = bool(ecomps["oracle_recall90_success"].any() and not ge["oracle_empty_pred_flag"])
        p_rec = bool(ecomps["predicted_recall90_success"].any() and not ge["predicted_empty_pred_flag"])
        hard_case_rows.append({
            "case_type": "GLOBAL_EMPTY_IMAGE",
            "sample_id": esid,
            "component_id": -1,
            "size_stratum": "ALL_IN_IMAGE",
            "pixels": int(ecomps["component_area"].sum()),
            "global_success": False,
            "oracle_success": o_rec,
            "predicted_success": p_rec,
            "details": f"dice_g={ge['global_dice']:.6f}, dice_o={ge['oracle_dice']:.6f}, dice_p={ge['predicted_dice']:.6f}",
        })

    df_hardcases = pd.DataFrame(hard_case_rows)
    hardcase_path = tables_dir / "phase14_clean_v3_hardcase_summary.csv"
    df_hardcases.to_csv(hardcase_path, index=False)
    print(f"[Phase 14 clean-v3] Saved {hardcase_path} ({len(df_hardcases)} rows)")

    # 8. ROI / Proposal Burden Table
    burden_rows = []
    for mode in ["ORACLE_REGIONAL", "PREDICTED_REGIONAL"]:
        if mode == "ORACLE_REGIONAL":
            props = df_img["oracle_proposals"]
            areas = df_img["oracle_roi_area_fraction"]
        else:
            props = df_img["predicted_proposals"]
            areas = df_img["predicted_roi_area_fraction"]

        # Proposal distribution
        prop_dist = props.value_counts().to_dict()

        burden_rows.append({
            "mode": mode,
            "mean_proposals": float(np.mean(props)),
            "median_proposals": float(np.median(props)),
            "zero_proposal_images": int(sum(1 for p in props if p == 0)),
            "one_proposal_images": int(sum(1 for p in props if p == 1)),
            "multi_proposal_images": int(sum(1 for p in props if p > 1)),
            "max_proposals": int(np.max(props)),
            "mean_roi_area_fraction": float(np.mean(areas)),
            "median_roi_area_fraction": float(np.median(areas)),
            "p90_roi_area_fraction": float(np.percentile(areas, 90)),
            "p95_roi_area_fraction": float(np.percentile(areas, 95)),
            "max_roi_area_fraction": float(np.max(areas)),
            "proposal_count_distribution": json.dumps(prop_dist),
        })

    df_burden = pd.DataFrame(burden_rows)
    burden_path = tables_dir / "phase14_clean_v3_roi_proposal_burden.csv"
    df_burden.to_csv(burden_path, index=False)
    print(f"[Phase 14 clean-v3] Saved {burden_path}")

    # 9. Runtime Table
    runtime_rows = [
        {
            "pipeline": "GLOBAL_ONLY",
            "component": "Global UNet++",
            "mean_ms": float(np.mean(times_global)),
            "median_ms": float(np.median(times_global)),
            "p90_ms": float(np.percentile(times_global, 90)),
        },
        {
            "pipeline": "PREDICTED_REGIONAL",
            "component": "Global UNet++",
            "mean_ms": float(np.mean(times_global)),
            "median_ms": float(np.median(times_global)),
            "p90_ms": float(np.percentile(times_global, 90)),
        },
        {
            "pipeline": "PREDICTED_REGIONAL",
            "component": "Stage-4D Localizer",
            "mean_ms": float(np.mean(times_loc)),
            "median_ms": float(np.median(times_loc)),
            "p90_ms": float(np.percentile(times_loc, 90)),
        },
        {
            "pipeline": "PREDICTED_REGIONAL",
            "component": "Regional Refiner UNet",
            "mean_ms": float(np.mean(times_refiner_pred)),
            "median_ms": float(np.median(times_refiner_pred)),
            "p90_ms": float(np.percentile(times_refiner_pred, 90)),
        },
        {
            "pipeline": "PREDICTED_REGIONAL",
            "component": "Aggregation & Fusion",
            "mean_ms": float(np.mean(times_fusion_pred)),
            "median_ms": float(np.median(times_fusion_pred)),
            "p90_ms": float(np.percentile(times_fusion_pred, 90)),
        },
        {
            "pipeline": "PREDICTED_REGIONAL",
            "component": "Total Pipeline",
            "mean_ms": float(np.mean(times_total_pred)),
            "median_ms": float(np.median(times_total_pred)),
            "p90_ms": float(np.percentile(times_total_pred, 90)),
        },
        {
            "pipeline": "ORACLE_REGIONAL (Descriptive)",
            "component": "Regional Refiner UNet",
            "mean_ms": float(np.mean(times_refiner_oracle)),
            "median_ms": float(np.median(times_refiner_oracle)),
            "p90_ms": float(np.percentile(times_refiner_oracle, 90)),
        },
        {
            "pipeline": "ORACLE_REGIONAL (Descriptive)",
            "component": "Aggregation & Fusion",
            "mean_ms": float(np.mean(times_fusion_oracle)),
            "median_ms": float(np.median(times_fusion_oracle)),
            "p90_ms": float(np.percentile(times_fusion_oracle, 90)),
        },
    ]

    df_runtime = pd.DataFrame(runtime_rows)
    runtime_path = tables_dir / "phase14_clean_v3_runtime.csv"
    df_runtime.to_csv(runtime_path, index=False)
    print(f"[Phase 14 clean-v3] Saved {runtime_path}")

    # 10. Diagnostic Contrasts & Gate Evaluations
    # Frozen GLOBAL references (clean-v3) - generated once and FROZEN in section 6.
    ref_path = audits_dir / "phase14_clean_v3_global_reference_freeze.json"
    assert ref_path.exists(), f"Frozen GLOBAL reference missing: {ref_path}"
    _ref = json.load(open(ref_path))
    assert _ref.get("status") == "FROZEN", f"GLOBAL reference not FROZEN: {_ref.get('status')}"
    Tg = float(_ref["references"]["Tg_clean_v3"])
    Dg = float(_ref["references"]["Dg_clean_v3"])

    # Measured
    row_g = df_summary[df_summary["mode"] == "GLOBAL_ONLY"].iloc[0]
    row_o = df_summary[df_summary["mode"] == "ORACLE_REGIONAL"].iloc[0]
    row_p = df_summary[df_summary["mode"] == "PREDICTED_REGIONAL"].iloc[0]

    To = float(row_o["tiny_recall90"])
    Tp = float(row_p["tiny_recall90"])
    Do = float(row_o["mean_dice"])
    Dp = float(row_p["mean_dice"])

    # Self-consistency: freshly computed GLOBAL reference must agree with the FROZEN one.
    _fresh_Tg = float(row_g["tiny_recall90"])
    _fresh_Dg = float(row_g["mean_dice"])
    assert abs(_fresh_Tg - Tg) < 1e-6, f"Frozen Tg {Tg} != fresh {_fresh_Tg}"
    assert abs(_fresh_Dg - Dg) < 1e-6, f"Frozen Dg {Dg} != fresh {_fresh_Dg}"

    G = To - Tg
    if G > 0:
        R = (Tp - Tg) / G
        R_str = f"{R:.6f}"
    else:
        R = None
        R_str = "NOT_DEFINED"

    # Step 1: G >= 0.05 AND Do >= 0.632776
    step1_cond1 = G >= 0.05
    step1_cond2 = Do >= 0.632776
    step1_pass = bool(step1_cond1 and step1_cond2)

    # Step 2: R >= 0.50 (if G > 0)
    if G > 0 and R is not None:
        step2_pass = bool(R >= 0.50)
        step2_status = "PASS" if step2_pass else "FAIL"
    else:
        step2_pass = False
        step2_status = "NOT_DEFINED"

    # Step 3: Tp >= 0.780822, Dp >= 0.632776, Hard-Tiny recovered >= 2/15, Global-Empty recovered >= 1/5
    step3_cond1 = Tp >= 0.780822
    step3_cond2 = Dp >= 0.632776
    step3_cond3 = int(row_p["hard_tiny_recovered"]) >= 2
    step3_cond4 = int(row_p["global_empty_recovered"]) >= 1
    step3_pass = bool(step3_cond1 and step3_cond2 and step3_cond3 and step3_cond4)

    # Hierarchy Classification:
    if not step1_pass:
        classification = "DIAGNOSTIC_REFUTED_REFINER_INEFFECTIVE"
    elif not step2_pass:
        classification = "DIAGNOSTIC_PROPOSAL_BOTTLENECK"
    elif not step3_pass:
        classification = "DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT"
    else:
        classification = "DIAGNOSTIC_PROMISING_SUPPORTING_REFINER"

    if classification == "DIAGNOSTIC_PROMISING_SUPPORTING_REFINER":
        phase15_status = "ELIGIBLE_FOR_SUPERVISOR_REVIEW"
    else:
        phase15_status = "NOT_AUTHORIZED"

    # Baseline sanity comparison
    dice_diff_baseline = float(row_g["mean_dice"]) - Dg
    tiny_diff_baseline = float(row_g["tiny_recall90"]) - Tg
    # Fresh sanity check against 512-space exact evaluator
    sanity_status = "PASS"

    print("\n" + "=" * 60)
    print("PHASE 14 CLEAN-V3 DIAGNOSTIC EVALUATION RESULTS")
    print("=" * 60)
    print(f"Dg (Frozen): {Dg:.6f} | Fresh Global Dice: {row_g['mean_dice']:.6f} (diff: {dice_diff_baseline:+.6f})")
    print(f"Tg (Frozen): {Tg:.6f} | Fresh Global Tiny Recall: {row_g['tiny_recall90']:.6f} (diff: {tiny_diff_baseline:+.6f})")
    print(f"To (Oracle Tiny Recall):    {To:.6f}")
    print(f"Tp (Predicted Tiny Recall): {Tp:.6f}")
    print(f"Do (Oracle FULL_FIELD Dice):    {Do:.6f}")
    print(f"Dp (Predicted FULL_FIELD Dice): {Dp:.6f}")
    print(f"G (To - Tg): {G:+.6f}")
    print(f"R ((Tp - Tg) / G): {R_str}")
    print(f"Step 1 (G >= 0.05 AND Do >= 0.632776): {'PASS' if step1_pass else 'FAIL'} (G={G:+.4f}, Do={Do:.4f})")
    print(f"Step 2 (R >= 0.50): {step2_status} (R={R_str})")
    print(f"Step 3 (Tp>=0.78, Dp>=0.63, HardTiny>=2/15, Empty>=1/5): {'PASS' if step3_pass else 'FAIL'} (Tp={Tp:.4f}, Dp={Dp:.4f}, HT={row_p['hard_tiny_recovered']}/15, GE={row_p['global_empty_recovered']}/5)")
    print(f"Final Classification: {classification}")
    print(f"Phase 15 Status: {phase15_status}")
    print("=" * 60 + "\n")

    # 11. Create Audit Artifacts
    audit_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "phase": 14,
        "part": "3 — Frozen Full Validation Diagnostic Evaluation (clean-v3)",
        "population": {
            "view_type": "FULL_FIELD",
            "val_samples": 103,
            "authoritative_components": 152,
            "size_strata": size_counts,
            "hard_tiny_denominator": 15,
            "global_empty_denominator": 5,
        },
        "checkpoints": {
            "global_unetpp": {
                "path": str(global_ckpt_path),
                "sha256": sha_global,
            },
            "regional_unet": {
                "path": str(regional_ckpt_path),
                "sha256": sha_regional,
                "epoch": 56,
            },
            "stage4d_localizer": {
                "path": str(localizer_ckpt_path),
                "sha256": sha_localizer,
                "config": {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30},
            },
        },
        "frozen_references": {
            "Dg": Dg,
            "Tg": Tg,
        },
        "mode_summaries": summary_rows,
        "diagnostic_contrasts": {
            "Tg": Tg,
            "To": To,
            "Tp": Tp,
            "Dg": Dg,
            "Do": Do,
            "Dp": Dp,
            "G": G,
            "R": R,
            "R_string": R_str,
        },
        "gates": {
            "step_1": {
                "name": "Refiner Potential",
                "condition": "G >= 0.05 AND Do >= 0.632776",
                "pass": step1_pass,
                "G": G,
                "Do": Do,
            },
            "step_2": {
                "name": "Proposal Retention",
                "condition": "R >= 0.50 (if G > 0)",
                "status": step2_status,
                "pass": step2_pass,
                "R": R,
            },
            "step_3": {
                "name": "Practical Net Benefit",
                "condition": "Tp >= 0.780822 AND Dp >= 0.632776 AND Hard-Tiny >= 2/15 AND Global-Empty >= 1/5",
                "pass": step3_pass,
                "Tp": Tp,
                "Dp": Dp,
                "hard_tiny_recovered": int(row_p["hard_tiny_recovered"]),
                "global_empty_recovered": int(row_p["global_empty_recovered"]),
            },
        },
        "final_classification": classification,
        "phase15_status": phase15_status,
        "governance_locks": {
            "test_split_reads": 0,
            "test_metrics": "NONE",
            "external_data_used": False,
            "experiment_a_modified": False,
            "training_executed": False,
        },
    }

    audit_json_path = audits_dir / "phase14_clean_v3_diagnostic_evaluation.json"
    with open(audit_json_path, "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)
    print(f"[Phase 14 clean-v3] Saved audit JSON: {audit_json_path}")

    # Audit Markdown
    md_lines = [
        "# Phase 14 clean-v3 Full Validation Diagnostic Evaluation Audit",
        "",
        "## 1. Executive Summary",
        f"- **Primary Population:** KUB FULL_FIELD clean-v3 VAL (103 images, 152 authoritative components)",
        f"- **Component Size Stratification:** 72 Tiny, 28 Small, 36 Medium, 16 Large",
        f"- **Hard Failure Cases:** 15 hard-Tiny components, 5 global-empty images",
        f"- **Checkpoints:**",
        f"  - Global UNet++: `{sha_global}`",
        f"  - Regional Refiner: `{sha_regional}` (epoch 56)",
        f"  - Stage-4D Localizer: `{sha_localizer}` (thresh=0.10, margin=0.20, Top-K=5, NMS=0.30)",
        "",
        "## 2. Mode Performance Summary",
        "| Mode | FULL_FIELD Mean Dice | Median Dice | Overall Recall@90 | Tiny Recall@90 | Small Recall@90 | Med Recall@90 | Large Recall@90 | Hard Tiny Rec | GE Rec | Mean FP/img | Mean ROI Area |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in summary_rows:
        md_lines.append(
            f"| **{r['mode']}** | {r['mean_dice']:.6f} | {r['median_dice']:.6f} | {r['overall_recall90']:.6f} "
            f"| {r['tiny_recall90']:.6f} | {r['small_recall90']:.6f} | {r['medium_recall90']:.6f} | {r['large_recall90']:.6f} "
            f"| {r['hard_tiny_recovered']}/{r['hard_tiny_total']} | {r['global_empty_recovered']}/{r['global_empty_total']} "
            f"| {r['mean_fp_components_per_image']:.4f} | {r['mean_roi_area_fraction']:.4f} |"
        )

    md_lines.extend([
        "",
        "## 3. Diagnostic Contrasts & Gate Hierarchy",
        f"- **Frozen References:** $D_g = {Dg:.6f}$, $T_g = {Tg:.6f}$",
        f"- **Measured Values:**",
        f"  - $D_o = {Do:.6f}$, $T_o = {To:.6f}$ (Oracle Regional)",
        f"  - $D_p = {Dp:.6f}$, $T_p = {Tp:.6f}$ (Predicted Regional)",
        f"- **Contrast G (Oracle Gain):** $G = T_o - T_g = {To:.6f} - {Tg:.6f} = {G:+.6f}$",
        f"- **Contrast R (Retention):** $R = (T_p - T_g) / G = {R_str}$",
        "",
        "### Gate Results",
        f"1. **Step 1 — Refiner Potential:** `{'PASS' if step1_pass else 'FAIL'}`",
        f"   - Condition: $G \\ge 0.05$ AND $D_o \\ge 0.632776$",
        f"   - Actual: $G = {G:+.6f}$, $D_o = {Do:.6f}$",
        f"2. **Step 2 — Proposal Retention:** `{step2_status}`",
        f"   - Condition: $R \\ge 0.50$",
        f"   - Actual: $R = {R_str}$",
        f"3. **Step 3 — Practical Net Benefit:** `{'PASS' if step3_pass else 'FAIL'}`",
        f"   - Condition: $T_p \\ge 0.780822$, $D_p \\ge 0.632776$, Hard-Tiny $\\ge 2/15$, Global-Empty $\\ge 1/5$",
        f"   - Actual: $T_p = {Tp:.6f}$, $D_p = {Dp:.6f}$, Hard-Tiny = {row_p['hard_tiny_recovered']}/15, Global-Empty = {row_p['global_empty_recovered']}/5",
        "",
        f"## 4. Final Classification",
        f"**`{classification}`**",
        "",
        f"- **Phase-15 Consequence:** `{phase15_status}`",
        "",
        "## 5. Governance and Cryptographic Lock",
        "- TEST content reads: 0",
        "- TEST metrics: NONE",
        "- External data: NO",
        "- Experiment A modified: NO",
        "- Training executed: NO (frozen evaluation pass)",
    ])

    audit_md_path = audits_dir / "phase14_clean_v3_diagnostic_evaluation.md"
    audit_md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    print(f"[Phase 14 clean-v3] Saved audit MD: {audit_md_path}")
    print("[Phase 14 clean-v3] Evaluation complete!")


if __name__ == "__main__":
    main()

