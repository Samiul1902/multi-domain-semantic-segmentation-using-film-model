"""H3 supply-axis evaluator — authoritative per-component/per-image evaluation.

Prospectively bound before inference.  Implements the EXACT same proposal
generation and coverage-evaluation path as the training script's
``h3_supply_axis_metrics`` / ``evaluate`` functions, extended to produce
detailed per-component (152-row) and per-image (103-row) tables plus all
supply-axis metrics required by the frozen H3 success/failure criteria.

Frozen decode: threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30
Checkpoint:     h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/best.pt
Population:     canonical clean-v3 FULL_FIELD VAL (103 images, 152 GT components)

Usage (from project root):
    python scripts/evaluation/h3_supply_axis_evaluator.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import DataLoader

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.inference.predicted_roi import (
    extract_predicted_components,
    non_max_suppression,
    apply_context_margin,
    evaluate_roi_coverage,
    union_roi_area_fraction,
    compute_iou,
)
from src.inference.learned_roi_clean_v3 import (
    HEATMAP_RESOLUTION,
    INPUT_RESOLUTION,
    build_clean_v3_localizer,
    load_clean_v3_localizer,
)
from src.utils.checkpointing import load_training_checkpoint

# ── Frozen configuration ────────────────────────────────────────────────────
FROZEN_DECODE = {
    "threshold": 0.10,
    "margin": 0.20,
    "top_k": 5,
    "nms_iou": 0.30,
}
CHECKPOINT_PATH = PROJECT_ROOT / "checkpoints" / "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3" / "best.pt"
EXPECTED_CHECKPOINT_SHA = "d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e"
VAL_MANIFEST = PROJECT_ROOT / "manifests" / "phase4_v3" / "val.csv"
COMPONENT_TABLE_V2 = PROJECT_ROOT / "reports" / "tables" / "phase13_predicted_roi_per_component.csv"
IMAGE_TABLE_V2 = PROJECT_ROOT / "reports" / "tables" / "phase13_predicted_roi_per_image.csv"
SAMPLES_TABLE = PROJECT_ROOT / "reports" / "tables" / "kub_val_samples_sized.csv"

# Frozen criteria references
TG = 0.7916666666666666   # GLOBAL/PREDICTED baseline TINY recall
G_GAP = 0.20833333333333337  # gap to oracle (1.0 - Tg)

# Baseline (PRE-H3 Phase-13B) supply values
BASELINE = {
    "zero_proposal_gt": 79,
    "zero_proposal_tiny": 57,
    "val_components": 152,
    "val_tiny": 72,
    "any_overlap_recall_overall": 0.8223684210526315,  # from PREDICTED condition
    "tiny_any_overlap_recall": (72 - 57) / 72,  # 15/72 = 0.208333...
    "tiny_covered90_recall": 0.7916666666666666,  # Tg
    "small_covered90_recall": 0.8928571428571429,
    "medium_covered90_recall": 1.0,
    "large_covered90_recall": 0.9375,
    "overall_covered90_recall": 0.875,
    "coverage90_overall": 0.875,
    "proposal_precision": None,  # not directly available from baseline
    "background_fraction": None,
    "proposals_per_image": None,
}


class Meta:
    """Transform metadata carrier matching training-script interface."""
    def __init__(self, scale, rh, rw, padding):
        self.scale = float(scale)
        self.resized_height = int(rh)
        self.resized_width = int(rw)
        self.padding = tuple(int(x) for x in padding)


def sha256_file(path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build_component_table() -> pd.DataFrame:
    """Build the authoritative 152-row component table (same path as training)."""
    phase13_components = pd.read_csv(COMPONENT_TABLE_V2)
    phase13_images = pd.read_csv(IMAGE_TABLE_V2)
    val_manifest = pd.read_csv(VAL_MANIFEST)
    val_sids = set(val_manifest["sample_id"].astype(str))

    # Filter to clean-v3 VAL sample_ids
    ct = phase13_components[
        phase13_components["sample_id"].astype(str).isin(val_sids)
    ].copy()

    hard_keys = set(zip(
        phase13_components[
            (phase13_components["kub_size_v1"] == "TINY")
            & ~phase13_components["global_detected"]
        ]["sample_id"].astype(str),
        phase13_components[
            (phase13_components["kub_size_v1"] == "TINY")
            & ~phase13_components["global_detected"]
        ]["component_id"],
    ))
    empty_ids = set(
        phase13_images[phase13_images["global_empty_prediction"]]["sample_id"].astype(str)
    )

    ct["hard_tiny"] = [
        (str(sid), cid) in hard_keys
        for sid, cid in zip(ct["sample_id"], ct["component_id"])
    ]
    ct["global_empty_image"] = ct["sample_id"].astype(str).isin(empty_ids)
    ct = ct.sort_values(["sample_id", "component_id"]).reset_index(drop=True)
    return ct


def gt_components_for_image(mask_path, metadata) -> List[Dict]:
    """Build GT component list (same as training gt_components)."""
    metadata = metadata.sort_values("component_id")
    items = []
    for _, meta in metadata.iterrows():
        items.append({
            "component_id": int(meta.component_id),
            "min_y": int(meta.min_y),
            "max_y": int(meta.max_y),
            "min_x": int(meta.min_x),
            "max_x": int(meta.max_x),
            "kub_size_v1": meta.kub_size_v1,
            "hard_tiny": bool(meta.hard_tiny),
            "global_empty_image": bool(meta.global_empty_image),
        })
    return items


def run_evaluation(
    checkpoint_path: Path = CHECKPOINT_PATH,
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """Run the full H3 supply-axis evaluation on canonical clean-v3 VAL.

    Returns a dict with per_component DataFrame, per_image DataFrame, and
    all aggregate metrics.
    """
    # ── Verify checkpoint SHA ───────────────────────────────────────────────
    ckpt_sha = sha256_file(checkpoint_path)
    if ckpt_sha != EXPECTED_CHECKPOINT_SHA:
        raise RuntimeError(
            f"Checkpoint SHA mismatch: {ckpt_sha} != expected {EXPECTED_CHECKPOINT_SHA}"
        )

    # ── Build component table ────────────────────────────────────────────────
    component_table = build_component_table()
    n_components = len(component_table)
    n_images = component_table["sample_id"].nunique()
    assert n_components == 152, f"Expected 152 components, got {n_components}"
    assert n_images == 103, f"Expected 103 images, got {n_images}"

    # Verify size strata
    size_counts = component_table["kub_size_v1"].value_counts().to_dict()
    assert size_counts.get("TINY", 0) == 72, f"TINY != 72: {size_counts}"
    assert size_counts.get("SMALL", 0) == 28, f"SMALL != 28: {size_counts}"
    assert size_counts.get("MEDIUM", 0) == 36, f"MEDIUM != 36: {size_counts}"
    assert size_counts.get("LARGE", 0) == 16, f"LARGE != 16: {size_counts}"

    # ── Build VAL dataset (same as training) ────────────────────────────────
    val_ds = KUBLocalizerDataset(
        SAMPLES_TABLE, "VAL", INPUT_RESOLUTION, sigma=0.75,
        heatmap_resolution=HEATMAP_RESOLUTION,
        size_adaptive_sigma=False,  # evaluation does not use size-adaptive targets
        manifest_path=VAL_MANIFEST,
    )
    assert len(val_ds) == 103, f"VAL dataset has {len(val_ds)} images, expected 103"

    val_loader = DataLoader(val_ds, batch_size=1, shuffle=False, num_workers=0)

    # ── Load model ───────────────────────────────────────────────────────────
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, _state = load_clean_v3_localizer(checkpoint_path, device=device)
    model.eval()

    # ── Frozen decode parameters ─────────────────────────────────────────────
    thr = FROZEN_DECODE["threshold"]
    margin = FROZEN_DECODE["margin"]
    top_k = FROZEN_DECODE["top_k"]
    nms = FROZEN_DECODE["nms_iou"]

    # ── Inference + proposal generation + coverage evaluation ───────────────
    per_component_rows: List[Dict] = []
    per_image_rows: List[Dict] = []
    total_proposals = 0
    total_tp_proposals = 0  # proposals overlapping >=1 GT component

    with torch.inference_mode():
        for batch_idx, batch in enumerate(val_loader):
            sample_id = batch["sample_id"][0]
            image_tensor = batch["image"].to(device)
            height = int(batch["original_height"][0])
            width = int(batch["original_width"][0])
            scale = float(batch["scale"][0])
            rh = int(batch["resized_height"][0])
            rw = int(batch["resized_width"][0])
            padding = tuple(int(x) for x in batch["padding"][0])
            meta = Meta(scale, rh, rw, padding)

            # Forward pass
            with torch.amp.autocast(
                device_type=device.type, enabled=device.type == "cuda"
            ):
                logits = model(image_tensor)
            probs = torch.sigmoid(logits)[0, 0].float().cpu().numpy()

            # Generate proposals (exact training path)
            components = extract_predicted_components(
                probs, thr, (height, width), meta
            )
            components = components[:100]  # cap at 100 for NMS
            components = non_max_suppression(components, nms)[:top_k]

            proposals = []
            for rank, comp in enumerate(components, start=1):
                proposals.append({
                    "rank": rank,
                    "score": comp["max_probability"],
                    "mean_probability": comp["mean_probability"],
                    "proposal_component_pixels_512": comp["component_pixels_512"],
                    "proposal_bbox": comp["bbox"],
                    "crop_geometry": apply_context_margin(
                        comp["bbox"], (height, width), margin
                    ),
                })

            n_proposals = len(proposals)
            total_proposals += n_proposals

            # Get GT components for this image
            metadata = component_table[
                component_table["sample_id"].astype(str) == str(sample_id)
            ]
            gt = gt_components_for_image(batch["mask_path"][0], metadata)

            # Evaluate coverage
            results = evaluate_roi_coverage(proposals, gt)

            # Track TP proposals (unique ranks with any overlap)
            tp_ranks = set()

            # Build per-component rows
            for result, gt_comp in zip(results, gt):
                comp_size = gt_comp["kub_size_v1"]
                gt_y1, gt_x1, gt_y2, gt_x2 = (
                    gt_comp["min_y"], gt_comp["min_x"],
                    gt_comp["max_y"], gt_comp["max_x"],
                )
                gt_bbox = (gt_y1, gt_x1, gt_y2, gt_x2)

                # Count matched proposals (any overlap)
                n_matched = 0
                best_box_iou = 0.0
                best_proposal_id = None
                for prop in proposals:
                    prop_bbox = prop["proposal_bbox"]
                    geom = prop["crop_geometry"]
                    # Check overlap between proposal ROI and GT bbox
                    iy = max(0, min(gt_y2 + 1, geom["clip_y2"]) - max(gt_y1, geom["clip_y1"]))
                    ix = max(0, min(gt_x2 + 1, geom["clip_x2"]) - max(gt_x1, geom["clip_x1"]))
                    if iy > 0 and ix > 0:
                        n_matched += 1
                        # Box IoU between proposal_bbox and GT bbox
                        box_iou = compute_iou(prop_bbox, gt_bbox)
                        if box_iou > best_box_iou:
                            best_box_iou = box_iou
                            best_proposal_id = prop["rank"]

                if result["any_overlap"] and not (
                    isinstance(result["best_proposal_rank"], float)
                    and np.isnan(result["best_proposal_rank"])
                ):
                    tp_ranks.add(int(result["best_proposal_rank"]))

                per_component_rows.append({
                    "sample_id": str(sample_id),
                    "component_id": int(gt_comp["component_id"]),
                    "size_stratum": comp_size,
                    "gt_area_pixels": int(gt_comp["max_y"] - gt_comp["min_y"] + 1) * int(gt_comp["max_x"] - gt_comp["min_x"] + 1),
                    "gt_min_y": gt_comp["min_y"],
                    "gt_max_y": gt_comp["max_y"],
                    "gt_min_x": gt_comp["min_x"],
                    "gt_max_x": gt_comp["max_x"],
                    "n_matched_proposals": n_matched,
                    "any_overlap": bool(result["any_overlap"]),
                    "max_gt_coverage": float(result["coverage_fraction"]),
                    "coverage50_success": bool(result["covered50"]),
                    "coverage90_success": bool(result["covered90"]),
                    "best_proposal_box_iou": float(best_box_iou),
                    "best_proposal_rank": int(result["best_proposal_rank"]) if not (
                        isinstance(result["best_proposal_rank"], float)
                        and np.isnan(result["best_proposal_rank"])
                    ) else -1,
                    "best_proposal_score": float(result["best_proposal_score"]) if not (
                        isinstance(result["best_proposal_score"], float)
                        and np.isnan(result["best_proposal_score"])
                    ) else -1.0,
                    "hard_tiny": bool(gt_comp["hard_tiny"]),
                    "global_empty_image": bool(gt_comp["global_empty_image"]),
                })

            n_tp = len(tp_ranks)
            total_tp_proposals += n_tp
            n_bg_fp = n_proposals - n_tp

            # Coverage stats for this image
            coverages = [r["coverage_fraction"] for r in results]
            mean_cov = float(np.mean(coverages)) if coverages else 0.0
            max_cov = float(np.max(coverages)) if coverages else 0.0
            n_zero_proposal_comps = sum(1 for r in results if not r["any_overlap"])

            # Union ROI area fraction
            union_area, max_roi_area = union_roi_area_fraction(
                proposals, (height, width)
            )

            per_image_rows.append({
                "sample_id": str(sample_id),
                "gt_component_count": len(gt),
                "proposal_count": n_proposals,
                "tp_proposal_count": n_tp,
                "background_fp_proposal_count": n_bg_fp,
                "zero_proposal_image": n_proposals == 0,
                "zero_proposal_gt_components": n_zero_proposal_comps,
                "mean_coverage": mean_cov,
                "max_coverage": max_cov,
                "union_roi_area_fraction": union_area,
                "max_roi_area_fraction": max_roi_area,
            })

    # ── Build DataFrames ────────────────────────────────────────────────────
    per_component_df = pd.DataFrame(per_component_rows)
    per_image_df = pd.DataFrame(per_image_rows)

    # ── Compute aggregate metrics ────────────────────────────────────────────
    n_total = len(per_component_df)
    n_tiny = int((per_component_df["size_stratum"] == "TINY").sum())
    n_small = int((per_component_df["size_stratum"] == "SMALL").sum())
    n_medium = int((per_component_df["size_stratum"] == "MEDIUM").sum())
    n_large = int((per_component_df["size_stratum"] == "LARGE").sum())

    zero_proposal_gt = int((~per_component_df["any_overlap"]).sum())
    zero_proposal_tiny = int(
        ((~per_component_df["any_overlap"]) & (per_component_df["size_stratum"] == "TINY")).sum()
    )
    zero_proposal_small = int(
        ((~per_component_df["any_overlap"]) & (per_component_df["size_stratum"] == "SMALL")).sum()
    )
    zero_proposal_medium = int(
        ((~per_component_df["any_overlap"]) & (per_component_df["size_stratum"] == "MEDIUM")).sum()
    )
    zero_proposal_large = int(
        ((~per_component_df["any_overlap"]) & (per_component_df["size_stratum"] == "LARGE")).sum()
    )

    def _recall_by_size(col, size):
        sub = per_component_df[per_component_df["size_stratum"] == size]
        return float(sub[col].mean()) if len(sub) > 0 else 0.0

    # Any-overlap recall by size
    any_overlap_overall = float(per_component_df["any_overlap"].mean())
    any_overlap_tiny = _recall_by_size("any_overlap", "TINY")
    any_overlap_small = _recall_by_size("any_overlap", "SMALL")
    any_overlap_medium = _recall_by_size("any_overlap", "MEDIUM")
    any_overlap_large = _recall_by_size("any_overlap", "LARGE")

    # Covered90 recall by size
    cov90_overall = float(per_component_df["coverage90_success"].mean())
    cov90_tiny = _recall_by_size("coverage90_success", "TINY")
    cov90_small = _recall_by_size("coverage90_success", "SMALL")
    cov90_medium = _recall_by_size("coverage90_success", "MEDIUM")
    cov90_large = _recall_by_size("coverage90_success", "LARGE")

    # Covered50 recall by size
    cov50_overall = float(per_component_df["coverage50_success"].mean())
    cov50_tiny = _recall_by_size("coverage50_success", "TINY")
    cov50_small = _recall_by_size("coverage50_success", "SMALL")
    cov50_medium = _recall_by_size("coverage50_success", "MEDIUM")
    cov50_large = _recall_by_size("coverage50_success", "LARGE")

    mean_coverage = float(per_component_df["max_gt_coverage"].mean())
    median_coverage = float(per_component_df["max_gt_coverage"].median())

    n_zero_proposal_images = int(per_image_df["zero_proposal_image"].sum())
    proposals_per_image = float(per_image_df["proposal_count"].mean())

    tp_proposals = total_tp_proposals
    bg_fp_proposals = total_proposals - total_tp_proposals
    precision = float(tp_proposals / total_proposals) if total_proposals > 0 else 0.0
    background_fraction = 1.0 - precision

    # Duplicate burden: proposals that overlap with a GT component already
    # matched by a better-ranked proposal (descriptive only)
    duplicate_burden = 0  # simplified; would need per-component match tracking

    mean_roi_area = float(per_image_df["union_roi_area_fraction"].mean())

    # ── R_H3 computation (frozen formula) ────────────────────────────────────
    # TinyRecall_H3 = H3 localizer's TINY covered90 recall (from proposals)
    tiny_recall_h3 = cov90_tiny
    r_h3 = (tiny_recall_h3 - TG) / G_GAP

    # ── Primary supply criteria ───────────────────────────────────────────────
    criterion_a = zero_proposal_tiny <= 20  # <= 20/72
    criterion_b = zero_proposal_gt <= 35    # <= 35/152
    combined_primary = criterion_a and criterion_b

    # ── Failure boundary ──────────────────────────────────────────────────────
    failure_tiny = zero_proposal_tiny >= 45  # >= 45/72
    failure_r_h3 = r_h3 < 0.15
    failure_fired = failure_tiny or failure_r_h3

    # ── R_H3 interpretation band ─────────────────────────────────────────────
    if r_h3 >= 0.30:
        r_h3_band = "meaningful"
    elif r_h3 >= 0.15:
        r_h3_band = "intermediate"
    else:
        r_h3_band = "insufficient"

    metrics = {
        "proposal_counts": {
            "total_proposals": int(total_proposals),
            "proposals_per_image": proposals_per_image,
            "zero_proposal_images": n_zero_proposal_images,
            "zero_proposal_gt": zero_proposal_gt,
            "zero_proposal_gt_fraction": float(zero_proposal_gt / n_total),
        },
        "supply_recall": {
            "any_overlap_overall": any_overlap_overall,
            "any_overlap_tiny": any_overlap_tiny,
            "any_overlap_small": any_overlap_small,
            "any_overlap_medium": any_overlap_medium,
            "any_overlap_large": any_overlap_large,
        },
        "coverage": {
            "coverage50_overall": cov50_overall,
            "coverage50_tiny": cov50_tiny,
            "coverage50_small": cov50_small,
            "coverage50_medium": cov50_medium,
            "coverage50_large": cov50_large,
            "coverage90_overall": cov90_overall,
            "coverage90_tiny": cov90_tiny,
            "coverage90_small": cov90_small,
            "coverage90_medium": cov90_medium,
            "coverage90_large": cov90_large,
            "mean_gt_coverage": mean_coverage,
            "median_gt_coverage": median_coverage,
        },
        "zero_proposal_by_size": {
            "TINY": zero_proposal_tiny,
            "SMALL": zero_proposal_small,
            "MEDIUM": zero_proposal_medium,
            "LARGE": zero_proposal_large,
        },
        "contamination_descriptive": {
            "tp_proposal_count": int(tp_proposals),
            "background_fp_proposal_count": int(bg_fp_proposals),
            "proposal_precision": precision,
            "background_fraction": float(background_fraction),
            "duplicate_burden": duplicate_burden,
            "mean_proposals_per_image": proposals_per_image,
            "mean_roi_area_fraction": mean_roi_area,
        },
        "r_h3": {
            "tiny_recall_h3": tiny_recall_h3,
            "Tg": TG,
            "G": G_GAP,
            "R_H3": r_h3,
            "interpretation_band": r_h3_band,
            "meaningful_threshold": 0.30,
            "insufficient_threshold": 0.15,
        },
        "primary_criteria": {
            "criterion_a": {
                "label": "zero_proposal_TINY <= 20/72",
                "value": zero_proposal_tiny,
                "threshold": 20,
                "denominator": 72,
                "passed": bool(criterion_a),
            },
            "criterion_b": {
                "label": "zero_proposal_GT <= 35/152",
                "value": zero_proposal_gt,
                "threshold": 35,
                "denominator": 152,
                "passed": bool(criterion_b),
            },
            "combined_passed": bool(combined_primary),
        },
        "failure_boundary": {
            "label": "H3_SUPPLY_REDESIGN_INSUFFICIENT",
            "condition_tiny": {
                "rule": "zero_proposal_TINY >= 45/72",
                "value": zero_proposal_tiny,
                "threshold": 45,
                "fired": bool(failure_tiny),
            },
            "condition_r_h3": {
                "rule": "R_H3 < 0.15",
                "value": r_h3,
                "threshold": 0.15,
                "fired": bool(failure_r_h3),
            },
            "fired": bool(failure_fired),
        },
        "population": {
            "val_images": n_images,
            "val_components": n_components,
            "tiny": n_tiny,
            "small": n_small,
            "medium": n_medium,
            "large": n_large,
        },
    }

    return {
        "per_component": per_component_df,
        "per_image": per_image_df,
        "metrics": metrics,
        "checkpoint_sha": ckpt_sha,
    }


def save_results(
    results: Dict[str, Any],
    output_dir: Path = PROJECT_ROOT / "reports" / "tables",
) -> Dict[str, str]:
    """Save per-component and per-image tables; return paths and SHAs."""
    output_dir.mkdir(parents=True, exist_ok=True)

    comp_path = output_dir / "h3_supply_eval_per_component.csv"
    image_path = output_dir / "h3_supply_eval_per_image.csv"

    results["per_component"].to_csv(comp_path, index=False)
    results["per_image"].to_csv(image_path, index=False)

    return {
        "per_component_path": str(comp_path),
        "per_component_sha": sha256_file(comp_path),
        "per_image_path": str(image_path),
        "per_image_sha": sha256_file(image_path),
    }


if __name__ == "__main__":
    print("=" * 72)
    print("H3 SUPPLY-AXIS EVALUATOR")
    print("=" * 72)
    print(f"Checkpoint: {CHECKPOINT_PATH}")
    print(f"Expected SHA: {EXPECTED_CHECKPOINT_SHA}")
    print(f"Frozen decode: {FROZEN_DECODE}")
    print(f"VAL manifest: {VAL_MANIFEST}")
    print()

    results = run_evaluation()
    paths = save_results(results)
    metrics = results["metrics"]

    print("\n--- RESULTS ---")
    print(f"Checkpoint SHA: {results['checkpoint_sha']}")
    print(f"Population: {metrics['population']}")
    print(f"Total proposals: {metrics['proposal_counts']['total_proposals']}")
    print(f"Proposals/image: {metrics['proposal_counts']['proposals_per_image']:.4f}")
    print(f"Zero-proposal GT: {metrics['proposal_counts']['zero_proposal_gt']}/152")
    print(f"Zero-proposal TINY: {metrics['zero_proposal_by_size']['TINY']}/72")
    print(f"Any-overlap recall overall: {metrics['supply_recall']['any_overlap_overall']:.6f}")
    print(f"Any-overlap recall TINY: {metrics['supply_recall']['any_overlap_tiny']:.6f}")
    print(f"Coverage90 overall: {metrics['coverage']['coverage90_overall']:.6f}")
    print(f"Coverage90 TINY: {metrics['coverage']['coverage90_tiny']:.6f}")
    print(f"Mean coverage: {metrics['coverage']['mean_gt_coverage']:.6f}")
    print(f"R_H3: {metrics['r_h3']['R_H3']:.6f} ({metrics['r_h3']['interpretation_band']})")
    print(f"Criterion A (TINY<=20): {metrics['primary_criteria']['criterion_a']['passed']}")
    print(f"Criterion B (GT<=35): {metrics['primary_criteria']['criterion_b']['passed']}")
    print(f"Failure boundary fired: {metrics['failure_boundary']['fired']}")
    print(f"\nPer-component table: {paths['per_component_path']}")
    print(f"Per-image table: {paths['per_image_path']}")
