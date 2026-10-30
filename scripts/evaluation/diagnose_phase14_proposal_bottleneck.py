"""POST-PHASE14 PROPOSAL / LOCALIZER BOTTLENECK ROOT-CAUSE DIAGNOSTIC (frozen, no tuning).

Governance:
  - TEST locked (0 reads), external data = NO.
  - No training / optimizer steps. No H3. No threshold/top-k/NMS/margin sweep.
  - Evaluates the frozen Stage-4D config EXACTLY as-is (same checkpoints, same proposal
    contract, same refiner, same regional preprocessing, same MAX/DIRECT fusion).

Captures EVERY frozen predicted proposal and performs a deterministic per-proposal /
per-component decomposition, plus the geometry bridge, the refiner conditional-performance
decomposition, and two allowed counterfactual probes (no tuning):
  (A) best-candidate oracle selection within the already-generated frozen candidate set;
  (B) removal of confirmed-background proposals.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.analysis.oracle_roi import extract_gt_components
from src.data.regional_dataset import crop_and_preprocess
from src.data.transforms import SegmentationTransform
from src.inference.kub_predict import _preprocess_image, _restore_original_coordinates
from src.inference.predicted_roi import apply_context_margin, generate_predicted_rois, compute_iou
from src.inference.regional_evaluator import aggregate_and_fuse, restore_regional_probability
from src.metrics.object_metrics import object_metrics
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests, validate_manifest_version_strict
from src.utils.test_lock import verify_test_lock


FROZEN_PROPOSAL_CONFIG = {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30}
REFINER_CROP_TARGET = 256
ORACLE_MARGIN = 0.20
SEG_THRESHOLD = 0.50

EXPECTED_SHA_GLOBAL = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"
EXPECTED_SHA_REGIONAL = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"
EXPECTED_SHA_LOCALIZER = "7673c34a2f2c86eca2e45c1bc6abe77842d17cd09f122f2da0f2d414ca492273"


def sha256_file(fp: Path) -> str:
    h = hashlib.sha256()
    with open(fp, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def dice_binary(pred_mask: np.ndarray, gt_mask: np.ndarray, eps: float = 1e-7) -> float:
    p = pred_mask > 0
    g = gt_mask > 0
    tp = float((p & g).sum())
    fp = float((p & ~g).sum())
    fn = float((~p & g).sum())
    return (2.0 * tp + eps) / (2.0 * tp + fp + fn + eps)


def coverage_fraction_of_component(p_geom: dict, labeled_gt: np.ndarray, cid: int) -> float:
    c_y1, c_y2 = p_geom["clip_y1"], p_geom["clip_y2"]
    c_x1, c_x2 = p_geom["clip_x1"], p_geom["clip_x2"]
    comp_mask = labeled_gt == cid
    total = float(comp_mask.sum())
    if total == 0:
        return 0.0
    inside = float(comp_mask[c_y1:c_y2, c_x1:c_x2].sum())
    return inside / total


def best_proposal_for_component(labeled_gt, proposals, cid):
    """Deterministic best-matching proposal for a GT component (frozen prospectively).

    Key = (coverage, score, -rank) -> maximize coverage, then score, then lower rank.
    """
    best = None
    best_key = None
    for p in proposals:
        cov = coverage_fraction_of_component(p["crop_geometry"], labeled_gt, cid)
        if cov <= 0.0:
            continue
        key = (cov, p["score"], -p["rank"])
        if best is None or key > best_key:
            best = p
            best_key = key
    return best, (best_key[0] if best_key is not None else 0.0)


def main():
    validate_manifest_version_strict("phase4_v3")
    verify_test_lock(PROJECT_ROOT)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        print("[WARN] CUDA not available; running on CPU (results identical, slower).")

    tables_dir = PROJECT_ROOT / "reports" / "tables"
    audits_dir = PROJECT_ROOT / "reports" / "audits"
    tables_dir.mkdir(parents=True, exist_ok=True)
    audits_dir.mkdir(parents=True, exist_ok=True)

    val_samples_path = tables_dir / "kub_val_samples_sized_clean_v3.csv"
    val_comps_path = tables_dir / "kub_val_components_sized_clean_v3.csv"
    p13_comps_path = tables_dir / "phase13_clean_v3_hard_tiny_replication_set.csv"
    p12_imgs_path = tables_dir / "phase13_clean_v3_global_empty_replication_set.csv"

    global_ckpt = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"
    regional_ckpt = PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"
    localizer_ckpt = PROJECT_ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3" / "best.pt"

    sha_global = sha256_file(global_ckpt)
    sha_regional = sha256_file(regional_ckpt)
    sha_localizer = sha256_file(localizer_ckpt)
    assert sha_global == EXPECTED_SHA_GLOBAL, f"Global SHA mismatch: {sha_global}"
    assert sha_regional == EXPECTED_SHA_REGIONAL, f"Regional SHA mismatch: {sha_regional}"
    assert sha_localizer == EXPECTED_SHA_LOCALIZER, f"Localizer SHA mismatch: {sha_localizer}"
    print("[DIAG] All three frozen checkpoint hashes verified.")

    df_samples = pd.read_csv(val_samples_path)
    ff_samples = df_samples[df_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_samples) == 103
    df_components = pd.read_csv(val_comps_path)
    ff_components = df_components[df_components["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_components) == 152

    df_p13 = pd.read_csv(p13_comps_path)
    hard_tiny_rows = df_p13[(df_p13["size_stratum"] == "TINY") & (~df_p13["global_detected"])]
    assert len(hard_tiny_rows) == 15
    hard_tiny_set = set(zip(hard_tiny_rows["sample_id"], hard_tiny_rows["native_component_id"]))
    df_p12 = pd.read_csv(p12_imgs_path)
    global_empty_rows = df_p12[df_p12["prediction_empty"]]
    assert len(global_empty_rows) == 5
    global_empty_set = set(global_empty_rows["sample_id"])

    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(global_ckpt, global_model, restore_rng=False, map_location=device)
    global_model.eval()
    localizer_model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16).to(device)
    load_training_checkpoint(localizer_ckpt, localizer_model, restore_rng=False, map_location=device)
    localizer_model.eval()
    refiner_model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(regional_ckpt, refiner_model, restore_rng=False, map_location=device)
    refiner_model.eval()
    loc_transform = SegmentationTransform(512, False)
    print("[DIAG] Models loaded.")

    proposal_rows = []
    component_rows = []
    geometry_rows = []
    conditional_rows = []
    img_summary_rows = []

    t_start = time.time()
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

            orig_comps, labeled_gt = extract_gt_components(raw_mask)
            sub_comps = ff_components[ff_components["sample_id"] == sid].set_index("component_id")
            assert len(orig_comps) == len(sub_comps), f"comp count mismatch {sid}"

            # A. GLOBAL
            t512, _, meta_g = _preprocess_image(raw_img, 512)
            logits_g = global_model(t512.to(device))
            prob512_g = torch.sigmoid(logits_g).squeeze().cpu().numpy()
            mask512_g = (prob512_g >= SEG_THRESHOLD).astype(np.uint8)
            prob_orig_g, mask_orig_g = _restore_original_coordinates(prob512_g, mask512_g, meta_g)

            # C. PREDICTED proposals (frozen contract)
            dummy = Image.new("L", raw_img.size)
            tensor_loc, _, meta_loc = loc_transform(raw_img, dummy)
            logits_loc = localizer_model(tensor_loc.unsqueeze(0).to(device))
            heatmap_loc = torch.sigmoid(logits_loc)[0, 0].cpu().numpy()
            proposals = generate_predicted_rois(
                heatmap_loc, meta_loc, (h_img, w_img),
                threshold=FROZEN_PROPOSAL_CONFIG["threshold"],
                margin=FROZEN_PROPOSAL_CONFIG["margin"],
                top_k=FROZEN_PROPOSAL_CONFIG["top_k"],
                nms_iou=FROZEN_PROPOSAL_CONFIG["nms_iou"],
            )

            per_prop_restored = []
            for prop in proposals:
                geom = prop["crop_geometry"]
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, REFINER_CROP_TARGET)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                logits_r = refiner_model(crop_t.to(device))
                prob_r = torch.sigmoid(logits_r)[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, geom, (h_img, w_img))
                per_prop_restored.append((rest_p, supp))

            reg_probs_pred = [r[0] for r in per_prop_restored]
            reg_supps_pred = [r[1] for r in per_prop_restored]

            # Standard PREDICTED fusion
            prob_fused_pred = aggregate_and_fuse(prob_orig_g, reg_probs_pred, reg_supps_pred)
            mask_fused_pred = (prob_fused_pred >= SEG_THRESHOLD).astype(np.uint8)

            # ---- Counterfactual masks (computed once, reused per-component) ----------------
            # (A) best-candidate oracle selection within the already-generated frozen set
            best_prop_of = {}
            for c in orig_comps:
                cid = c["component_id"]
                bp, cov = best_proposal_for_component(labeled_gt, proposals, cid)
                best_prop_of[cid] = (bp, cov)
            claimed_by = {}
            for cid, (bp, cov) in best_prop_of.items():
                if bp is not None:
                    claimed_by[cid] = bp
            selected_props, seen = [], set()
            for cid, (bp, cov) in best_prop_of.items():
                if bp is not None and id(bp) not in seen:
                    seen.add(id(bp))
                    selected_props.append(bp)
            sel_rest = [per_prop_restored[proposals.index(p)][0] for p in selected_props]
            sel_supp = [per_prop_restored[proposals.index(p)][1] for p in selected_props]
            mask_fused_oraclesel = (aggregate_and_fuse(prob_orig_g, sel_rest, sel_supp) >= SEG_THRESHOLD).astype(np.uint8)

            # (B) remove confirmed-background proposals (overlap no GT)
            keep_props = [p for p in proposals if any(
                coverage_fraction_of_component(p["crop_geometry"], labeled_gt, c["component_id"]) > 0.0
                for c in orig_comps)]
            fp_rest = [per_prop_restored[proposals.index(p)][0] for p in keep_props]
            fp_supp = [per_prop_restored[proposals.index(p)][1] for p in keep_props]
            mask_fused_fpremoved = (aggregate_and_fuse(prob_orig_g, fp_rest, fp_supp) >= SEG_THRESHOLD).astype(np.uint8)

            # ---- Per-proposal classification (TP / FP / duplicate / best) ------------------
            for pi, prop in enumerate(proposals):
                matches = [c["component_id"] for c in orig_comps
                           if coverage_fraction_of_component(prop["crop_geometry"], labeled_gt, c["component_id"]) > 0.0]
                is_tp = len(matches) > 0
                is_best = prop in claimed_by.values()
                geom = prop["crop_geometry"]
                clip_area = (geom["clip_y2"] - geom["clip_y1"]) * (geom["clip_x2"] - geom["clip_x1"])
                proposal_rows.append({
                    "sample_id": sid,
                    "proposal_index": pi,
                    "rank": prop["rank"],
                    "score": float(prop["score"]),
                    "mean_probability": float(prop.get("mean_probability", prop["score"])),
                    "proposal_bbox": json.dumps(list(prop["proposal_bbox"])),
                    "crop_geometry": json.dumps({k: geom[k] for k in
                        ["y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
                         "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels",
                         "effective_magnification", "margin"]}),
                    "crop_area_pixels": int(clip_area),
                    "area_fraction": float(clip_area) / float(img_area),
                    "n_matched_gt": len(matches),
                    "matched_gt_ids": json.dumps(matches),
                    "is_tp": is_tp,
                    "is_fp_background": (not is_tp),
                    "is_duplicate": (is_tp and not is_best),
                    "is_best_match_for_any_component": is_best,
                })

            # ---- Per-component decomposition --------------------------------------------
            img_fp_pred = object_metrics(mask_fused_pred, raw_mask, 1)["false_positive_predicted_components"]
            for c in orig_comps:
                cid = c["component_id"]
                c_mask = labeled_gt == cid
                c_pixels = int(c["component_pixels"])
                c_stratum = sub_comps.loc[cid, "size_stratum"]
                is_hard_tiny = (sid, cid) in hard_tiny_set
                bp, best_cov = best_prop_of[cid]
                if bp is not None:
                    iou = compute_iou(tuple(bp["proposal_bbox"]),
                                      (c["min_y"], c["min_x"], c["max_y"], c["max_x"]))
                    bp_score = float(bp["score"])
                    bp_rank = int(bp["rank"])
                else:
                    iou = 0.0
                    bp_score = float("nan")
                    bp_rank = -1

                ov_p = int((mask_fused_pred & c_mask).sum())
                cov_p = ov_p / c_pixels
                ov_g = int((mask_orig_g & c_mask).sum())
                cov_g = ov_g / c_pixels
                ov_os = int((mask_fused_oraclesel & c_mask).sum())
                cov_os = ov_os / c_pixels
                ov_fpr = int((mask_fused_fpremoved & c_mask).sum())
                cov_fpr = ov_fpr / c_pixels

                if bp is not None:
                    pr_idx = proposals.index(bp)
                    rest_p, supp = per_prop_restored[pr_idx]
                    ref_th = (rest_p >= SEG_THRESHOLD)
                    ref_inter = int((ref_th & c_mask).sum())
                    ref_union = int((ref_th | c_mask).sum())
                    ref_iou = (ref_inter / ref_union) if ref_union > 0 else 0.0
                    ref_cov = ref_inter / c_pixels
                else:
                    ref_iou = 0.0
                    ref_cov = 0.0

                zero_prop = (bp is None)
                good_not_top = (bp is not None and bp["rank"] > 1 and best_cov >= 0.50)

                component_rows.append({
                    "sample_id": sid,
                    "component_id": cid,
                    "size_stratum": c_stratum,
                    "component_area": c_pixels,
                    "hard_tiny_flag": is_hard_tiny,
                    "global_empty_image": sid in global_empty_set,
                    "best_proposal_exists": (bp is not None),
                    "best_proposal_rank": bp_rank,
                    "best_proposal_score": bp_score,
                    "best_proposal_coverage": float(best_cov),
                    "best_proposal_bbox_iou": float(iou),
                    "zero_proposal_component": zero_prop,
                    "good_proposal_exists_not_top_rank": good_not_top,
                    "predicted_coverage_ratio": float(cov_p),
                    "predicted_cov90": bool(cov_p >= 0.90),
                    "predicted_cov50": bool(cov_p >= 0.50),
                    "predicted_recall90_success": bool((mask_fused_pred & c_mask).any()),
                    "global_coverage_ratio": float(cov_g),
                    "oracle_sel_coverage_ratio": float(cov_os),
                    "oracle_sel_cov90": bool(cov_os >= 0.90),
                    "oracle_sel_recall90_success": bool((mask_fused_oraclesel & c_mask).any()),
                    "fp_removed_coverage_ratio": float(cov_fpr),
                    "fp_removed_cov90": bool(cov_fpr >= 0.90),
                    "fp_removed_recall90_success": bool((mask_fused_fpremoved & c_mask).any()),
                    "refiner_crop_iou": float(ref_iou),
                    "refiner_crop_coverage": float(ref_cov),
                    "refiner_improves_global": bool(cov_p > cov_g),
                })

                if best_cov >= 0.90:
                    cov_stratum = "COV_GE_0.90"
                elif best_cov >= 0.50:
                    cov_stratum = "COV_0.50_0.90"
                elif best_cov > 0.0:
                    cov_stratum = "COV_LT_0.50"
                else:
                    cov_stratum = "NO_MATCHED_PROPOSAL"
                ptype = "NO_MATCHED_PROPOSAL" if bp is None else ("TP_BEST" if bp in claimed_by.values() else "OTHER")
                conditional_rows.append({
                    "sample_id": sid,
                    "component_id": cid,
                    "size_stratum": c_stratum,
                    "best_proposal_coverage": float(best_cov),
                    "coverage_stratum": cov_stratum,
                    "proposal_type": ptype,
                    "global_coverage_ratio": float(cov_g),
                    "predicted_coverage_ratio": float(cov_p),
                    "predicted_cov90": bool(cov_p >= 0.90),
                    "oracle_sel_coverage_ratio": float(cov_os),
                    "fp_removed_coverage_ratio": float(cov_fpr),
                    "refiner_crop_iou": float(ref_iou),
                    "refiner_crop_coverage": float(ref_cov),
                    "refiner_improves_global": bool(cov_p > cov_g),
                })

                # §6 geometry bridge
                if bp is not None:
                    o_geom = apply_context_margin((c["min_y"], c["min_x"], c["max_y"], c["max_x"]),
                                                  (h_img, w_img), ORACLE_MARGIN)
                    p_geom = bp["crop_geometry"]
                    o_cx = (o_geom["clip_x1"] + o_geom["clip_x2"]) / 2.0
                    o_cy = (o_geom["clip_y1"] + o_geom["clip_y2"]) / 2.0
                    p_cx = (p_geom["clip_x1"] + p_geom["clip_x2"]) / 2.0
                    p_cy = (p_geom["clip_y1"] + p_geom["clip_y2"]) / 2.0
                    o_w = o_geom["clip_x2"] - o_geom["clip_x1"]
                    o_h = o_geom["clip_y2"] - o_geom["clip_y1"]
                    p_w = p_geom["clip_x2"] - p_geom["clip_x1"]
                    p_h = p_geom["clip_y2"] - p_geom["clip_y1"]
                    o_area = max(o_w * o_h, 1)
                    p_area = max(p_w * p_h, 1)
                    gt_in_pred = coverage_fraction_of_component(p_geom, labeled_gt, cid)
                    excess_bg = (p_area - gt_in_pred * c_pixels) / img_area if c_pixels > 0 else 0.0
                    geom_iou = compute_iou(
                        (p_geom["clip_y1"], p_geom["clip_x1"], p_geom["clip_y2"], p_geom["clip_x2"]),
                        (o_geom["clip_y1"], o_geom["clip_x1"], o_geom["clip_y2"], o_geom["clip_x2"]))
                    geometry_rows.append({
                        "sample_id": sid,
                        "component_id": cid,
                        "size_stratum": c_stratum,
                        "center_displacement_px": float(((p_cx - o_cx) ** 2 + (p_cy - o_cy) ** 2) ** 0.5),
                        "width_ratio_pred_over_oracle": float(p_w / o_w) if o_w > 0 else float("nan"),
                        "height_ratio_pred_over_oracle": float(p_h / o_h) if o_h > 0 else float("nan"),
                        "area_ratio_pred_over_oracle": float(p_area / o_area),
                        "gt_coverage_in_predicted_roi": float(gt_in_pred),
                        "excess_background_area_fraction": float(excess_bg),
                        "roi_box_iou": float(geom_iou),
                        "predicted_roi_contains_enough_context": bool(gt_in_pred >= 0.90),
                    })

            dice_p = dice_binary(mask_fused_pred, raw_mask)
            dice_os = dice_binary(mask_fused_oraclesel, raw_mask)
            dice_fpr = dice_binary(mask_fused_fpremoved, raw_mask)
            fp_os = object_metrics(mask_fused_oraclesel, raw_mask, 1)["false_positive_predicted_components"]
            fp_fpr = object_metrics(mask_fused_fpremoved, raw_mask, 1)["false_positive_predicted_components"]
            img_summary_rows.append({
                "sample_id": sid,
                "patient_id": pid,
                "category": cat,
                "global_dice": dice_binary(mask_orig_g, raw_mask),
                "predicted_dice": dice_p,
                "oracle_sel_dice": dice_os,
                "fp_removed_dice": dice_fpr,
                "predicted_fp": img_fp_pred,
                "oracle_sel_fp": fp_os,
                "fp_removed_fp": fp_fpr,
                "n_proposals": len(proposals),
                "n_selected_oracle": len(selected_props),
                "n_kept_fp": len(keep_props),
                "global_empty": sid in global_empty_set,
            })

            if (idx + 1) % 20 == 0 or (idx + 1) == len(ff_samples):
                print(f"  [DIAG] processed {idx + 1}/{len(ff_samples)} images ({time.time() - t_start:.1f}s)")

    df_prop = pd.DataFrame(proposal_rows)
    df_comp = pd.DataFrame(component_rows)
    df_geom = pd.DataFrame(geometry_rows)
    df_cond = pd.DataFrame(conditional_rows)
    df_img = pd.DataFrame(img_summary_rows)

    prop_path = tables_dir / "phase14_diag_proposal_level.csv"
    comp_path = tables_dir / "phase14_diag_component_level.csv"
    geom_path = tables_dir / "phase14_diag_geometry_bridge.csv"
    cond_path = tables_dir / "phase14_diag_conditional_refiner.csv"
    img_path = tables_dir / "phase14_diag_image_summary.csv"
    df_prop.to_csv(prop_path, index=False)
    df_comp.to_csv(comp_path, index=False)
    df_geom.to_csv(geom_path, index=False)
    df_cond.to_csv(cond_path, index=False)
    df_img.to_csv(img_path, index=False)
    print(f"[DIAG] Wrote {prop_path} ({len(df_prop)} rows)")
    print(f"[DIAG] Wrote {comp_path} ({len(df_comp)} rows)")
    print(f"[DIAG] Wrote {geom_path} ({len(df_geom)} rows)")
    print(f"[DIAG] Wrote {cond_path} ({len(df_cond)} rows)")
    print(f"[DIAG] Wrote {img_path} ({len(df_img)} rows)")

    run_state = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "population": {"val_full_field_images": 103, "components": 152},
        "checkpoints": {
            "global_unetpp": {"sha256": sha_global},
            "regional_refiner": {"sha256": sha_regional, "epoch": 56},
            "stage4d_localizer": {"sha256": sha_localizer, "config": FROZEN_PROPOSAL_CONFIG},
        },
        "counters": {"search_sweeps": 0, "tuning_runs": 0, "checkpoint_comparisons": 0,
                     "retraining": 0, "h3_training": 0, "test_reads": 0, "external_test_reads": 0},
        "governance": {"no_training": True, "no_h3": True, "no_threshold_search": True,
                       "no_proposal_search": True, "no_checkpoint_change": True,
                       "external_data_used": False, "test_split_reads": 0},
    }
    rs_path = audits_dir / "phase14_diag_execution_state.json"
    with open(rs_path, "w", encoding="utf-8") as f:
        json.dump(run_state, f, indent=2)
    print(f"[DIAG] Wrote {rs_path}")
    print("[DIAG] Diagnostic inference + decomposition complete.")


if __name__ == "__main__":
    main()
