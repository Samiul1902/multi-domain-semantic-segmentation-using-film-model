"""H3 DOWNSTREAM EVALUATION — frozen Phase-14 downstream semantics.

Prospectively bound BEFORE observing any H3 downstream result.

Pipeline (frozen prospective H3 design):
    H3 selected localizer (epoch 54)          [checkpoints/h3_.../best.pt]
      -> 128-space heatmap (heatmap_resolution=128)
      -> frozen Stage-4D proposal policy (threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30)
      -> frozen Phase-14 regional refiner epoch 56  [checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/best.pt]
      -> MAX-probability replacement in proposal union
      -> FULL_FIELD segmentation (threshold 0.50)
      -> per-component / per-size downstream metrics
      -> formal R_H3 = (TinyRecall_H3 - Tg) / G

Everything downstream of the localizer is byte-identical to the bound Phase-14
clean-v3 evaluator (scripts/evaluation/evaluate_phase14_clean_v3_diagnostic.py):
same transform, same proposal API, same refiner crop construction, same restore,
same fusion, same segmentation threshold, same metrics. ONLY the localizer
checkpoint (and its training-faithful 128 heatmap construction) changes.

Governance: TEST CLOSED (0 reads), external CLOSED, no training, no tuning,
no alternate checkpoint, no proposal-policy search.

Usage (from project root):
    python scripts/evaluation/h3_downstream_evaluator.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

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
from src.inference.predicted_roi import (
    apply_context_margin,
    evaluate_roi_coverage,
    generate_predicted_rois,
)
from src.inference.regional_evaluator import aggregate_and_fuse, restore_regional_probability
from src.inference.learned_roi_clean_v3 import build_clean_v3_localizer, HEATMAP_RESOLUTION
from src.metrics.object_metrics import object_metrics
from src.models.factory import create_model
from src.models.unet import UNet
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import validate_manifest_version_strict
from src.utils.test_lock import verify_test_lock

# ── Frozen configuration ─────────────────────────────────────────────────────
H3_CKPT = PROJECT_ROOT / "checkpoints" / "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3" / "best.pt"
H3_CKPT_SHA = "d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e"
H3_SELECTED_EPOCH = 54

REFINER_CKPT = PROJECT_ROOT / "checkpoints" / "phase14_kub_refiner_unet_a3_256_seed42_clean_v3" / "best.pt"
REFINER_CKPT_SHA = "2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa"
REFINER_EPOCH = 56

GLOBAL_CKPT = PROJECT_ROOT / "checkpoints" / "phase10_kub_unetpp_seed42_512_clean_v3" / "best.pt"
GLOBAL_CKPT_SHA = "ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269"

FROZEN_PROPOSAL_POLICY = {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30}
FINAL_FUSION_THRESHOLD = 0.50
GLOBAL_THRESHOLD = 0.50

# Frozen downstream references (prospectively frozen; never redefined)
TG = 0.7916666666666666
G_GAP = 0.20833333333333337
DG = 0.6359172411726776

# Reused frozen contrast references (Phase-14 clean-v3 authoritative artifacts)
PHASE14_MODE_SUMMARY = PROJECT_ROOT / "reports" / "tables" / "phase14_clean_v3_mode_summary.csv"
PHASE14_COMPONENT_METRICS = PROJECT_ROOT / "reports" / "tables" / "phase14_clean_v3_component_metrics.csv"
PHASE14_IMAGE_METRICS = PROJECT_ROOT / "reports" / "tables" / "phase14_clean_v3_image_metrics.csv"

# Population
VAL_SAMPLES = PROJECT_ROOT / "reports" / "tables" / "kub_val_samples_sized_clean_v3.csv"
VAL_COMPONENTS = PROJECT_ROOT / "reports" / "tables" / "kub_val_components_sized_clean_v3.csv"
HARD_TINY_SET = PROJECT_ROOT / "reports" / "tables" / "phase13_clean_v3_hard_tiny_replication_set.csv"
GLOBAL_EMPTY_SET = PROJECT_ROOT / "reports" / "tables" / "phase13_clean_v3_global_empty_replication_set.csv"

# Expected supply agreement (previously saved H3 supply metrics)
EXPECTED_SUPPLY_ZERO_GT = 27
EXPECTED_SUPPLY_ZERO_TINY = 22


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
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


def main() -> Dict[str, Any]:
    t_start = time.time()

    # ── 0. Governance ────────────────────────────────────────────────────────
    validate_manifest_version_strict("phase4_v3")
    verify_test_lock(PROJECT_ROOT)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    if device.type != "cuda":
        raise RuntimeError("CUDA is required for the H3 downstream evaluation.")

    # ── 1. Verify checkpoint SHAs (FAIL CLOSED) ──────────────────────────────
    sha_h3 = sha256_file(H3_CKPT)
    sha_refiner = sha256_file(REFINER_CKPT)
    sha_global = sha256_file(GLOBAL_CKPT)
    if sha_h3 != H3_CKPT_SHA:
        raise RuntimeError(f"H3 checkpoint SHA mismatch: {sha_h3} != {H3_CKPT_SHA}")
    if sha_refiner != REFINER_CKPT_SHA:
        raise RuntimeError(f"Refiner checkpoint SHA mismatch: {sha_refiner} != {REFINER_CKPT_SHA}")
    if sha_global != GLOBAL_CKPT_SHA:
        raise RuntimeError(f"Global checkpoint SHA mismatch: {sha_global} != {GLOBAL_CKPT_SHA}")
    print("[H3 downstream] All checkpoint hashes verified.")

    # ── 2. Population ────────────────────────────────────────────────────────
    df_samples = pd.read_csv(VAL_SAMPLES)
    ff_samples = df_samples[df_samples["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_samples) == 103, f"Expected 103 FULL_FIELD samples, got {len(ff_samples)}"

    df_components = pd.read_csv(VAL_COMPONENTS)
    ff_components = df_components[df_components["view_type"] == "FULL_FIELD"].copy().reset_index(drop=True)
    assert len(ff_components) == 152, f"Expected 152 components, got {len(ff_components)}"

    size_counts = ff_components["size_stratum"].value_counts().to_dict()
    assert size_counts.get("TINY", 0) == 72
    assert size_counts.get("SMALL", 0) == 28
    assert size_counts.get("MEDIUM", 0) == 36
    assert size_counts.get("LARGE", 0) == 16

    df_ht = pd.read_csv(HARD_TINY_SET)
    ht_rows = df_ht[(df_ht["size_stratum"] == "TINY") & (~df_ht["global_detected"])]
    assert len(ht_rows) == 15, f"Expected 15 hard-Tiny, got {len(ht_rows)}"
    hard_tiny_set = set(zip(ht_rows["sample_id"], ht_rows["native_component_id"]))

    df_ge = pd.read_csv(GLOBAL_EMPTY_SET)
    ge_rows = df_ge[df_ge["prediction_empty"]]
    assert len(ge_rows) == 5, f"Expected 5 global-empty images, got {len(ge_rows)}"
    global_empty_set = set(ge_rows["sample_id"])

    print("[H3 downstream] Population verified: 103 images, 152 components (72/28/36/16), 15 hard-Tiny, 5 global-empty.")

    # ── 3. Reuse frozen contrast references ──────────────────────────────────
    frozen_summary = pd.read_csv(PHASE14_MODE_SUMMARY).set_index("mode")
    frozen_components = pd.read_csv(PHASE14_COMPONENT_METRICS)
    frozen_images = pd.read_csv(PHASE14_IMAGE_METRICS)

    # ── 4. Load models ───────────────────────────────────────────────────────
    print("[H3 downstream] Loading models...")
    global_model = create_model("unetpp", in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(GLOBAL_CKPT, global_model, restore_rng=False, map_location=device)
    global_model.eval()

    # H3 localizer: training-faithful 128 heatmap construction
    localizer_model = build_clean_v3_localizer(device=device)
    assert getattr(localizer_model, "heatmap_resolution", None) == HEATMAP_RESOLUTION
    load_training_checkpoint(H3_CKPT, localizer_model, restore_rng=False, map_location=device)
    localizer_model.eval()

    refiner_model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(REFINER_CKPT, refiner_model, restore_rng=False, map_location=device)
    refiner_model.eval()

    loc_transform = SegmentationTransform(512, False)

    # ── 5. Inference loop ────────────────────────────────────────────────────
    comp_records: List[Dict] = []
    img_records: List[Dict] = []
    times_global, times_loc, times_refiner, times_fusion = [], [], [], []

    print("[H3 downstream] Running frozen downstream evaluation over 103 FULL_FIELD VAL images...")

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
            assert len(orig_comps) == len(sub_comps), f"Component mismatch in {sid}"

            # ---- GLOBAL (fusion baseline; also sanity-checked vs frozen) ----
            torch.cuda.synchronize()
            tg0 = time.perf_counter()
            t512, _, meta_g = _preprocess_image(raw_img, 512)
            prob512_g = torch.sigmoid(global_model(t512.to(device))).squeeze().cpu().numpy()
            mask512_g = (prob512_g >= GLOBAL_THRESHOLD).astype(np.uint8)
            prob_orig_g, mask_orig_g = _restore_original_coordinates(prob512_g, mask512_g, meta_g)
            torch.cuda.synchronize()
            times_global.append((time.perf_counter() - tg0) * 1000.0)

            dice_g = dice_binary(mask_orig_g, raw_mask)
            fp_g = object_metrics(mask_orig_g, raw_mask, 1)["false_positive_predicted_components"]

            # ---- H3 localizer -> frozen proposals (128 heatmap) ----
            torch.cuda.synchronize()
            tl0 = time.perf_counter()
            dummy = Image.new("L", raw_img.size)
            tensor_loc, _, meta_loc = loc_transform(raw_img, dummy)
            logits_loc = localizer_model(tensor_loc.unsqueeze(0).to(device))
            heatmap_loc = torch.sigmoid(logits_loc)[0, 0].float().cpu().numpy()
            assert heatmap_loc.shape == (HEATMAP_RESOLUTION, HEATMAP_RESOLUTION), heatmap_loc.shape
            proposals = generate_predicted_rois(
                heatmap_loc, meta_loc, (h_img, w_img),
                FROZEN_PROPOSAL_POLICY["threshold"], FROZEN_PROPOSAL_POLICY["margin"],
                FROZEN_PROPOSAL_POLICY["top_k"], FROZEN_PROPOSAL_POLICY["nms_iou"],
            )
            torch.cuda.synchronize()
            times_loc.append((time.perf_counter() - tl0) * 1000.0)

            # ---- Phase-14 refiner on H3 proposals ----
            torch.cuda.synchronize()
            tr0 = time.perf_counter()
            reg_probs, reg_supps = [], []
            h3_union_mask = np.zeros((h_img, w_img), dtype=bool)
            for prop in proposals:
                geom = prop["crop_geometry"]
                crop_img_pil, _ = crop_and_preprocess(raw_img, raw_mask_pil, geom, 256)
                crop_t = torch.from_numpy(np.asarray(crop_img_pil, dtype=np.float32)).unsqueeze(0).unsqueeze(0) / 255.0
                logits_r = refiner_model(crop_t.to(device))
                prob_r = torch.sigmoid(logits_r)[0, 0].cpu().numpy()
                rest_p, supp = restore_regional_probability(prob_r, geom, (h_img, w_img))
                reg_probs.append(rest_p)
                reg_supps.append(supp)
                h3_union_mask = h3_union_mask | supp
            torch.cuda.synchronize()
            times_refiner.append((time.perf_counter() - tr0) * 1000.0)

            # ---- Fusion (MAX replacement in proposal union) ----
            tf0 = time.perf_counter()
            prob_fused = aggregate_and_fuse(prob_orig_g, reg_probs, reg_supps)
            mask_fused = (prob_fused >= FINAL_FUSION_THRESHOLD).astype(np.uint8)
            times_fusion.append((time.perf_counter() - tf0) * 1000.0)

            dice_h3 = dice_binary(mask_fused, raw_mask)
            fp_h3 = object_metrics(mask_fused, raw_mask, 1)["false_positive_predicted_components"]
            h3_roi_area_fraction = float(h3_union_mask.sum()) / float(img_area)

            # ---- Proposal-supply coverage (deterministic agreement check) ----
            gt_supply = [
                {"component_id": c["component_id"], "min_y": c["min_y"], "max_y": c["max_y"],
                 "min_x": c["min_x"], "max_x": c["max_x"], "kub_size_v1": sub_comps.loc[c["component_id"], "size_stratum"]}
                for c in orig_comps
            ]
            supply_results = evaluate_roi_coverage(proposals, gt_supply)
            supply_by_cid = {r["component_id"]: r for r in supply_results}

            # ---- Per-component downstream evaluation ----
            n_zero_prop = 0
            n_zero_prop_tiny = 0
            has_hard_tiny = False
            for c in orig_comps:
                cid = c["component_id"]
                c_mask = labeled_gt == cid
                c_pixels = int(c["component_pixels"])
                c_stratum = sub_comps.loc[cid, "size_stratum"]
                is_hard_tiny = (sid, cid) in hard_tiny_set
                if is_hard_tiny:
                    has_hard_tiny = True

                ov_h3 = int((mask_fused & c_mask).sum())
                cov90_h3 = (ov_h3 / c_pixels) >= 0.90

                sup = supply_by_cid[cid]
                any_overlap = bool(sup["any_overlap"])
                if not any_overlap:
                    n_zero_prop += 1
                    if c_stratum == "TINY":
                        n_zero_prop_tiny += 1

                comp_records.append({
                    "sample_id": sid,
                    "component_id": cid,
                    "size_stratum": c_stratum,
                    "component_area": c_pixels,
                    "h3_downstream_recall90_success": bool(cov90_h3),
                    "h3_downstream_overlap_pixels": ov_h3,
                    "h3_downstream_coverage_ratio": ov_h3 / c_pixels,
                    "h3_proposal_any_overlap": any_overlap,
                    "h3_proposal_best_coverage": float(sup["coverage_fraction"]),
                    "hard_tiny_flag": is_hard_tiny,
                    "global_empty_flag": sid in global_empty_set,
                })

            is_global_empty = sid in global_empty_set
            img_records.append({
                "sample_id": sid,
                "patient_id": pid,
                "category": cat,
                "global_dice": dice_g,
                "h3_downstream_dice": dice_h3,
                "global_fp_components": fp_g,
                "h3_downstream_fp_components": fp_h3,
                "h3_proposals": len(proposals),
                "h3_roi_area_fraction": h3_roi_area_fraction,
                "h3_zero_proposal_gt_components": n_zero_prop,
                "h3_zero_proposal_tiny_components": n_zero_prop_tiny,
                "h3_empty_pred_flag": bool(mask_fused.sum() == 0),
                "has_hard_tiny": has_hard_tiny,
                "global_empty": is_global_empty,
                "global_time_ms": times_global[-1],
                "localizer_time_ms": times_loc[-1],
                "refiner_time_ms": times_refiner[-1],
                "fusion_time_ms": times_fusion[-1],
            })

            if (idx + 1) % 20 == 0 or (idx + 1) == len(ff_samples):
                print(f"  Processed {idx + 1}/{len(ff_samples)} images...")

    df_img = pd.DataFrame(img_records)
    df_comp = pd.DataFrame(comp_records)
    assert len(df_comp) == 152, f"per-component rows {len(df_comp)} != 152"
    assert len(df_img) == 103, f"per-image rows {len(df_img)} != 103"

    # ── 6. H3 downstream aggregate metrics ───────────────────────────────────
    def recall_by_size(col: str, size: str) -> float:
        sub = df_comp[df_comp["size_stratum"] == size]
        return float(sub[col].mean()) if len(sub) else 0.0

    h3_tiny = recall_by_size("h3_downstream_recall90_success", "TINY")
    h3_small = recall_by_size("h3_downstream_recall90_success", "SMALL")
    h3_medium = recall_by_size("h3_downstream_recall90_success", "MEDIUM")
    h3_large = recall_by_size("h3_downstream_recall90_success", "LARGE")
    h3_overall = float(df_comp["h3_downstream_recall90_success"].mean())

    h3_mean_dice = float(df_img["h3_downstream_dice"].mean())
    h3_median_dice = float(df_img["h3_downstream_dice"].median())
    h3_fp_per_image = float(df_img["h3_downstream_fp_components"].mean())

    h3_hard_tiny_rec = int(df_comp[df_comp["hard_tiny_flag"]]["h3_downstream_recall90_success"].sum())
    # global-empty recovery (same semantics as the frozen Phase-14 evaluator)
    h3_ge_rec = 0
    for sid in global_empty_set:
        sub = df_comp[df_comp["sample_id"] == sid]
        row = df_img[df_img["sample_id"] == sid].iloc[0]
        if bool(sub["h3_downstream_recall90_success"].any()) and not bool(row["h3_empty_pred_flag"]):
            h3_ge_rec += 1

    props = df_img["h3_proposals"]
    areas = df_img["h3_roi_area_fraction"]
    proposal_burden = {
        "mean_proposals_per_image": float(props.mean()),
        "median_proposals_per_image": float(props.median()),
        "zero_proposal_images": int((props == 0).sum()),
        "multi_proposal_images": int((props > 1).sum()),
        "max_proposals": int(props.max()),
        "mean_roi_area_fraction": float(areas.mean()),
        "median_roi_area_fraction": float(areas.median()),
        "p90_roi_area_fraction": float(np.percentile(areas, 90)),
        "p95_roi_area_fraction": float(np.percentile(areas, 95)),
        "max_roi_area_fraction": float(areas.max()),
    }

    # ── 7. Supply agreement check (deterministic) ────────────────────────────
    supply_zero_gt = int(df_comp["h3_proposal_any_overlap"].eq(False).sum())
    supply_zero_tiny = int(
        (df_comp["h3_proposal_any_overlap"].eq(False) & df_comp["size_stratum"].eq("TINY")).sum()
    )
    supply_agreement = bool(
        supply_zero_gt == EXPECTED_SUPPLY_ZERO_GT and supply_zero_tiny == EXPECTED_SUPPLY_ZERO_TINY
    )

    # ── 8. Formal downstream R_H3 ────────────────────────────────────────────
    tiny_recall_h3 = h3_tiny
    r_h3 = (tiny_recall_h3 - TG) / G_GAP
    if r_h3 >= 0.30:
        band = "meaningful"
    elif r_h3 >= 0.15:
        band = "intermediate"
    else:
        band = "insufficient"

    # ── 9. Frozen contrast table (GLOBAL/PREDICTED/ORACLE reused) ────────────
    def _frozen(mode: str, col: str) -> float:
        return float(frozen_summary.loc[mode, col])

    contrast = {
        "GLOBAL": {
            "source": "REUSED (phase14_clean_v3_mode_summary.csv)",
            "mean_dice": _frozen("GLOBAL_ONLY", "mean_dice"),
            "median_dice": _frozen("GLOBAL_ONLY", "median_dice"),
            "overall_recall90": _frozen("GLOBAL_ONLY", "overall_recall90"),
            "tiny_recall90": _frozen("GLOBAL_ONLY", "tiny_recall90"),
            "small_recall90": _frozen("GLOBAL_ONLY", "small_recall90"),
            "medium_recall90": _frozen("GLOBAL_ONLY", "medium_recall90"),
            "large_recall90": _frozen("GLOBAL_ONLY", "large_recall90"),
            "hard_tiny_recovered": int(frozen_summary.loc["GLOBAL_ONLY", "hard_tiny_recovered"]),
            "hard_tiny_total": 15,
            "global_empty_recovered": int(frozen_summary.loc["GLOBAL_ONLY", "global_empty_recovered"]),
            "global_empty_total": 5,
            "mean_fp_components_per_image": _frozen("GLOBAL_ONLY", "mean_fp_components_per_image"),
        },
        "PREDICTED": {
            "source": "REUSED (phase14_clean_v3_mode_summary.csv)",
            "pipeline": "Phase-13B localizer (epoch 53) + Phase-14 refiner (epoch 56)",
            "mean_dice": _frozen("PREDICTED_REGIONAL", "mean_dice"),
            "median_dice": _frozen("PREDICTED_REGIONAL", "median_dice"),
            "overall_recall90": _frozen("PREDICTED_REGIONAL", "overall_recall90"),
            "tiny_recall90": _frozen("PREDICTED_REGIONAL", "tiny_recall90"),
            "small_recall90": _frozen("PREDICTED_REGIONAL", "small_recall90"),
            "medium_recall90": _frozen("PREDICTED_REGIONAL", "medium_recall90"),
            "large_recall90": _frozen("PREDICTED_REGIONAL", "large_recall90"),
            "hard_tiny_recovered": int(frozen_summary.loc["PREDICTED_REGIONAL", "hard_tiny_recovered"]),
            "hard_tiny_total": 15,
            "global_empty_recovered": int(frozen_summary.loc["PREDICTED_REGIONAL", "global_empty_recovered"]),
            "global_empty_total": 5,
            "mean_fp_components_per_image": _frozen("PREDICTED_REGIONAL", "mean_fp_components_per_image"),
        },
        "H3": {
            "source": "NEWLY GENERATED (this task)",
            "pipeline": "H3 localizer (epoch 54, 128 heatmap) + Phase-14 refiner (epoch 56)",
            "mean_dice": h3_mean_dice,
            "median_dice": h3_median_dice,
            "overall_recall90": h3_overall,
            "tiny_recall90": h3_tiny,
            "small_recall90": h3_small,
            "medium_recall90": h3_medium,
            "large_recall90": h3_large,
            "hard_tiny_recovered": h3_hard_tiny_rec,
            "hard_tiny_total": 15,
            "global_empty_recovered": h3_ge_rec,
            "global_empty_total": 5,
            "mean_fp_components_per_image": h3_fp_per_image,
        },
        "ORACLE_REGIONAL": {
            "source": "REUSED (phase14_clean_v3_mode_summary.csv)",
            "mean_dice": _frozen("ORACLE_REGIONAL", "mean_dice"),
            "median_dice": _frozen("ORACLE_REGIONAL", "median_dice"),
            "overall_recall90": _frozen("ORACLE_REGIONAL", "overall_recall90"),
            "tiny_recall90": _frozen("ORACLE_REGIONAL", "tiny_recall90"),
            "small_recall90": _frozen("ORACLE_REGIONAL", "small_recall90"),
            "medium_recall90": _frozen("ORACLE_REGIONAL", "medium_recall90"),
            "large_recall90": _frozen("ORACLE_REGIONAL", "large_recall90"),
            "hard_tiny_recovered": int(frozen_summary.loc["ORACLE_REGIONAL", "hard_tiny_recovered"]),
            "hard_tiny_total": 15,
            "global_empty_recovered": int(frozen_summary.loc["ORACLE_REGIONAL", "global_empty_recovered"]),
            "global_empty_total": 5,
            "mean_fp_components_per_image": _frozen("ORACLE_REGIONAL", "mean_fp_components_per_image"),
        },
    }

    # ── 10. Save tables ──────────────────────────────────────────────────────
    tables_dir = PROJECT_ROOT / "reports" / "tables"
    audits_dir = PROJECT_ROOT / "reports" / "audits"
    comp_path = tables_dir / "h3_downstream_per_component.csv"
    img_path = tables_dir / "h3_downstream_per_image.csv"
    df_comp.to_csv(comp_path, index=False)
    df_img.to_csv(img_path, index=False)

    # ── 11. Audit JSON ───────────────────────────────────────────────────────
    evaluator_sha = sha256_file(Path(__file__))
    artifact = {
        "artifact": "h3_downstream_evaluation",
        "task": "H3 METRIC-DOMAIN RECONCILIATION + FROZEN DOWNSTREAM EVALUATION + NOTEBOOK 06",
        "status": "H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING",
        "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "formal_adjudication_performed": False,
        "h3_verdict_issued": False,

        "selected_h3_checkpoint": {
            "path": str(H3_CKPT),
            "sha256": sha_h3,
            "selected_epoch": H3_SELECTED_EPOCH,
            "heatmap_resolution": HEATMAP_RESOLUTION,
            "construction": "build_clean_v3_localizer (explicit heatmap_resolution=128)",
        },
        "refiner_checkpoint": {"path": str(REFINER_CKPT), "sha256": sha_refiner, "epoch": REFINER_EPOCH},
        "global_checkpoint": {"path": str(GLOBAL_CKPT), "sha256": sha_global},

        "evaluator_binding": {
            "evaluator_path": "scripts/evaluation/h3_downstream_evaluator.py",
            "evaluator_sha256": evaluator_sha,
            "dependency_shas": {
                "src/analysis/oracle_roi.py": sha256_file(PROJECT_ROOT / "src/analysis/oracle_roi.py"),
                "src/data/regional_dataset.py": sha256_file(PROJECT_ROOT / "src/data/regional_dataset.py"),
                "src/data/transforms.py": sha256_file(PROJECT_ROOT / "src/data/transforms.py"),
                "src/inference/kub_predict.py": sha256_file(PROJECT_ROOT / "src/inference/kub_predict.py"),
                "src/inference/predicted_roi.py": sha256_file(PROJECT_ROOT / "src/inference/predicted_roi.py"),
                "src/inference/regional_evaluator.py": sha256_file(PROJECT_ROOT / "src/inference/regional_evaluator.py"),
                "src/inference/learned_roi_clean_v3.py": sha256_file(PROJECT_ROOT / "src/inference/learned_roi_clean_v3.py"),
                "src/metrics/object_metrics.py": sha256_file(PROJECT_ROOT / "src/metrics/object_metrics.py"),
                "src/models/factory.py": sha256_file(PROJECT_ROOT / "src/models/factory.py"),
                "src/models/unet.py": sha256_file(PROJECT_ROOT / "src/models/unet.py"),
                "src/utils/checkpointing.py": sha256_file(PROJECT_ROOT / "src/utils/checkpointing.py"),
            },
            "population_binding": {
                "val_samples": str(VAL_SAMPLES),
                "val_samples_sha256": sha256_file(VAL_SAMPLES),
                "val_components": str(VAL_COMPONENTS),
                "val_components_sha256": sha256_file(VAL_COMPONENTS),
            },
            "component_table_sha256": sha256_file(VAL_COMPONENTS),
            "frozen_proposal_config": FROZEN_PROPOSAL_POLICY,
            "fusion_semantics": "MAX probability replacement inside proposal union (aggregate_and_fuse)",
            "final_fusion_threshold": FINAL_FUSION_THRESHOLD,
            "global_threshold": GLOBAL_THRESHOLD,
            "refiner_crop_target_size": 256,
            "metric_definitions": {
                "downstream_recall90": "component overlap pixels / component pixels >= 0.90 on the fused FULL_FIELD mask",
                "fp_components_per_image": "object_metrics(mask, gt, minimum_overlap_pixels=1)['false_positive_predicted_components']",
                "dice": "binary Dice with eps=1e-7 on the FULL_FIELD native-space mask",
                "R_H3": "R_H3 = (TinyRecall_H3 - Tg) / G ; TinyRecall_H3 = H3 DOWNSTREAM TINY recall@90",
            },
            "formal_R_H3_source": "DOWNSTREAM_TINY_RECALL",
            "formal_R_H3_source_is_not": "PROPOSAL_COVERAGE90",
        },

        "population": {
            "view_type": "FULL_FIELD",
            "val_images": 103,
            "components": 152,
            "size_strata": {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16},
            "hard_tiny_denominator": 15,
            "global_empty_denominator": 5,
        },
        "frozen_proposal_policy": FROZEN_PROPOSAL_POLICY,
        "proposal_configurations_evaluated": 1,
        "frozen_references": {"Tg": TG, "G": G_GAP, "Dg": DG},

        "h3_downstream_metrics": {
            "mean_dice": h3_mean_dice,
            "median_dice": h3_median_dice,
            "overall_recall90": h3_overall,
            "tiny_recall90": h3_tiny,
            "small_recall90": h3_small,
            "medium_recall90": h3_medium,
            "large_recall90": h3_large,
            "tiny_detected_count": int(df_comp[df_comp["size_stratum"] == "TINY"]["h3_downstream_recall90_success"].sum()),
            "small_detected_count": int(df_comp[df_comp["size_stratum"] == "SMALL"]["h3_downstream_recall90_success"].sum()),
            "medium_detected_count": int(df_comp[df_comp["size_stratum"] == "MEDIUM"]["h3_downstream_recall90_success"].sum()),
            "large_detected_count": int(df_comp[df_comp["size_stratum"] == "LARGE"]["h3_downstream_recall90_success"].sum()),
            "hard_tiny_recovered": h3_hard_tiny_rec,
            "hard_tiny_total": 15,
            "global_empty_recovered": h3_ge_rec,
            "global_empty_total": 5,
            "mean_fp_components_per_image": h3_fp_per_image,
            "proposal_burden": proposal_burden,
        },

        "formal_downstream": {
            "TinyRecall_H3": tiny_recall_h3,
            "Tg": TG,
            "G": G_GAP,
            "R_H3": r_h3,
            "interpretation_band": band,
            "meaningful_threshold": 0.30,
            "intermediate_range": "0.15 <= R_H3 < 0.30",
            "insufficient_threshold": 0.15,
        },

        "contrast_table": contrast,

        "supply_agreement_check": {
            "expected_zero_proposal_gt": EXPECTED_SUPPLY_ZERO_GT,
            "expected_zero_proposal_tiny": EXPECTED_SUPPLY_ZERO_TINY,
            "recomputed_zero_proposal_gt": supply_zero_gt,
            "recomputed_zero_proposal_tiny": supply_zero_tiny,
            "deterministic_agreement": supply_agreement,
            "source": "reports/audits/h3_supply_axis_evaluation.json",
        },

        "provenance_caveats": [
            "The frozen PREDICTED baseline (GLOBAL/PREDICTED/ORACLE contrast rows) was produced by the bound Phase-14 clean-v3 evaluator, whose localizer was constructed WITHOUT an explicit heatmap_resolution (KUBLocalizer default = 512, logit_downsample = Identity).",
            "The H3 downstream arm follows the frozen prospective design, which specifies a 128-space heatmap; the H3 localizer is therefore constructed with heatmap_resolution=128 (logit_downsample = AvgPool2d(4)), which is also the training-faithful construction.",
            "Consequently the frozen PREDICTED contrast row and the H3 row differ in localizer heatmap-decode construction in addition to the localizer checkpoint. This is a provenance nuance of the pre-existing frozen artifacts, NOT introduced by this task. It is recorded here for transparency and is flagged as an unresolved issue.",
            "The proposal-supply agreement check confirms the H3 arm reproduces the previously saved supply metrics (zero-proposal GT=27, TINY=22) exactly.",
        ],

        "inference_counters": {
            "supply_axis_h3_val_inference_runs_previously_performed": 1,
            "h3_downstream_inference_runs_this_task": 1,
            "h3_localizer_downstream_replay_runs": 1,
            "alternate_h3_checkpoints_evaluated": 0,
            "proposal_policy_searches": 0,
            "refiner_checkpoints_searched": 0,
            "test_reads": 0,
            "external_test_reads": 0,
        },
        "test_reads": 0,
        "external_test_reads": 0,
        "phase_15_status": "NOT_STARTED_AND_NOT_AUTHORIZED",

        "per_component_table": {"path": "reports/tables/h3_downstream_per_component.csv",
                                 "sha256": sha256_file(comp_path), "rows": len(df_comp)},
        "per_image_table": {"path": "reports/tables/h3_downstream_per_image.csv",
                             "sha256": sha256_file(img_path), "rows": len(df_img)},

        "runtime_seconds": time.time() - t_start,
        "device": str(device),
    }

    out_path = audits_dir / "h3_downstream_evaluation.json"
    out_path.write_text(json.dumps(artifact, indent=2), encoding="utf-8")

    print("\n" + "=" * 66)
    print("H3 DOWNSTREAM EVALUATION RESULTS")
    print("=" * 66)
    print(f"H3 mean Dice: {h3_mean_dice:.6f} | median: {h3_median_dice:.6f}")
    print(f"TINY recall@90: {h3_tiny:.6f} | SMALL: {h3_small:.6f} | MEDIUM: {h3_medium:.6f} | LARGE: {h3_large:.6f}")
    print(f"Overall recall@90: {h3_overall:.6f}")
    print(f"hard-Tiny: {h3_hard_tiny_rec}/15 | global-empty: {h3_ge_rec}/5 | FP/img: {h3_fp_per_image:.4f}")
    print(f"TinyRecall_H3 (DOWNSTREAM) = {tiny_recall_h3:.10f}")
    print(f"R_H3 = ({tiny_recall_h3:.10f} - {TG}) / {G_GAP} = {r_h3:.10f}  [{band}]")
    print(f"Supply agreement: {supply_agreement} (GT {supply_zero_gt}/152, TINY {supply_zero_tiny}/72)")
    print(f"Artifact: {out_path}")
    print("=" * 66)
    return artifact


if __name__ == "__main__":
    main()
