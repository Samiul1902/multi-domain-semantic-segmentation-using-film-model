"""Evaluate Phase-13B Stage-4D final bounded localizer best checkpoint."""
import hashlib
import json
from itertools import product
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.inference.predicted_roi import (
    apply_context_margin,
    evaluate_roi_coverage,
    extract_predicted_components,
    non_max_suppression,
    union_roi_area_fraction,
)
from src.losses.localization import CenterNetFocalLoss
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.reproducibility import make_generator, seed_worker
from src.utils.test_lock import verify_test_lock

THRESHOLDS = (0.1, 0.2, 0.3, 0.4, 0.5)
MARGINS = (0.1, 0.2)
TOPKS = (3, 5)


class Meta:
    def __init__(self, scale, rh, rw, padding):
        self.scale = float(scale)
        self.resized_height = int(rh)
        self.resized_width = int(rw)
        self.padding = tuple(int(x) for x in padding)


def gt_components(component_metadata):
    metadata = component_metadata.sort_values("component_id")
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


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def main():
    verify_manifests()
    verify_test_lock(ROOT)

    exp_id = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1"
    chk_dir = ROOT / "checkpoints" / exp_id
    exp_dir = ROOT / "experiments" / exp_id
    best_path = chk_dir / "best.pt"
    latest_path = chk_dir / "latest.pt"

    if not best_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {best_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = create_model("kub_localizer", in_channels=1, out_channels=1, base_channels=16, heatmap_resolution=128).to(device)
    checkpoint_state = load_training_checkpoint(best_path, model, restore_rng=False, map_location=device)
    best_epoch = checkpoint_state.get("epoch", -1)

    T = ROOT / "reports/tables"
    val_ds = KUBLocalizerDataset(T / "kub_val_samples_sized.csv", "VAL", resolution=512, sigma=0.75, heatmap_resolution=128)
    assert len(val_ds) == 106, f"Expected 106 VAL images, got {len(val_ds)}"

    val_loader = DataLoader(
        val_ds,
        batch_size=4,
        shuffle=False,
        num_workers=0,
        pin_memory=True,
        worker_init_fn=seed_worker,
        generator=make_generator(42),
    )

    phase13_components = pd.read_csv(T / "phase13_predicted_roi_per_component.csv")
    phase13_images = pd.read_csv(T / "phase13_predicted_roi_per_image.csv")
    hard_keys = set(
        zip(
            phase13_components[(phase13_components.kub_size_v1 == "TINY") & ~phase13_components.global_detected].sample_id,
            phase13_components[(phase13_components.kub_size_v1 == "TINY") & ~phase13_components.global_detected].component_id,
        )
    )
    empty_ids = set(phase13_images[phase13_images.global_empty_prediction].sample_id)

    component_table = phase13_components[["sample_id", "component_id", "min_y", "max_y", "min_x", "max_x", "kub_size_v1", "global_detected"]].copy()
    component_table["hard_tiny"] = [(sid, cid) in hard_keys for sid, cid in zip(component_table.sample_id, component_table.component_id)]
    component_table["global_empty_image"] = component_table.sample_id.isin(empty_ids)

    criterion = CenterNetFocalLoss(alpha=2.0, beta=4.0)
    model.eval()
    losses = []
    cache = []
    all_max_probs = []

    with torch.inference_mode():
        for batch in val_loader:
            image = batch["image"].to(device)
            target = batch["heatmap"].to(device)
            with torch.amp.autocast("cuda"):
                logits = model(image)
                loss = criterion(logits, target)
            losses.append(loss.item())
            probs = torch.sigmoid(logits).float().cpu().numpy()
            for i, sid in enumerate(batch["sample_id"]):
                pm = probs[i, 0]
                all_max_probs.append(float(pm.max()))
                cache.append({
                    "sample_id": sid,
                    "patient_id": batch["patient_id"][i],
                    "category": batch["category"][i],
                    "mask_path": batch["mask_path"][i],
                    "probability": pm,
                    "height": int(batch["original_height"][i]),
                    "width": int(batch["original_width"][i]),
                    "meta": Meta(batch["scale"][i], batch["resized_height"][i], batch["resized_width"][i], batch["padding"][i]),
                })

    for item in cache:
        metadata = component_table[component_table.sample_id == item["sample_id"]]
        item["gt"] = gt_components(metadata)
        item["comps"] = {}
        for t in THRESHOLDS:
            item["comps"][t] = extract_predicted_components(item["probability"], t, (item["height"], item["width"]), item["meta"])

    rows = []
    eval_cache = {}
    for threshold, margin, top_k in product(THRESHOLDS, MARGINS, TOPKS):
        cover = []
        image_metrics = []
        img_records = []
        for item in cache:
            components = item["comps"][threshold][:100]
            components = non_max_suppression(components, 0.3)[:top_k]
            proposals = []
            for rank, component in enumerate(components, start=1):
                proposals.append({
                    "rank": rank,
                    "score": component["max_probability"],
                    "mean_probability": component["mean_probability"],
                    "proposal_component_pixels_512": component["component_pixels_512"],
                    "proposal_bbox": component["bbox"],
                    "crop_geometry": apply_context_margin(component["bbox"], (item["height"], item["width"]), margin),
                })
            gt = item["gt"]
            out = evaluate_roi_coverage(proposals, gt)
            area, _ = union_roi_area_fraction(proposals, (item["height"], item["width"]))
            comp_rows = [{
                **result,
                "sample_id": item["sample_id"],
                "patient_id": item["patient_id"],
                "global_detected": component_table[(component_table.sample_id == item["sample_id"]) & (component_table.component_id == result["component_id"])].global_detected.iloc[0],
                **{key: component[key] for key in ("kub_size_v1", "hard_tiny", "global_empty_image")},
            } for result, component in zip(out, gt)]
            cover.extend(comp_rows)
            image_metrics.append((len(proposals), area))
            c90_cnt = sum(1 for r in out if r["covered90"])
            img_records.append({
                "sample_id": item["sample_id"],
                "patient_id": item["patient_id"],
                "num_proposals": len(proposals),
                "roi_area_fraction": area,
                "global_empty_image": item["sample_id"] in empty_ids,
                "num_gt_components": len(gt),
                "num_covered90": c90_cnt,
            })

        frame = pd.DataFrame(cover)
        hard = frame[frame.hard_tiny]
        empty = frame[frame.global_empty_image]
        tiny = frame[frame.kub_size_v1 == "TINY"]
        multi_ids = set(component_table.groupby("sample_id").size().loc[lambda v: v > 1].index)
        multi = frame[frame.sample_id.isin(multi_ids)]
        mean_area = float(np.mean([x[1] for x in image_metrics]))
        mean_props = float(np.mean([x[0] for x in image_metrics]))
        feasible = (mean_area <= 0.10) and (mean_props <= 5.0)

        cfg_key = (threshold, margin, top_k)
        eval_cache[cfg_key] = {
            "comp_df": frame,
            "img_df": pd.DataFrame(img_records),
            "areas": [x[1] for x in image_metrics],
            "props": [x[0] for x in image_metrics],
        }

        rows.append({
            "threshold": threshold,
            "margin": margin,
            "top_k": top_k,
            "nms_iou": 0.3,
            "hard_tiny_recovered90": int(hard.covered90.sum()),
            "global_empty_images_covered90": int(empty.groupby("sample_id").covered90.any().sum()),
            "global_empty_components_covered90": int(empty.covered90.sum()),
            "tiny_recall90": float(tiny.covered90.mean()) if len(tiny) else 0.0,
            "overall_recall90": float(frame.covered90.mean()) if len(frame) else 0.0,
            "overall_recall50": float(frame.covered50.mean()) if len(frame) else 0.0,
            "any_overlap_recall": float(frame.any_overlap.mean()) if len(frame) else 0.0,
            "mean_coverage": float(frame.coverage_fraction.mean()) if len(frame) else 0.0,
            "multi_component_recall90": float(multi.covered90.mean()) if len(multi) else 0.0,
            "mean_proposals_per_image": mean_props,
            "mean_roi_area_fraction": mean_area,
            "feasible": feasible,
            "p90_roi_area_fraction": float(np.percentile([x[1] for x in image_metrics], 90)),
            "p95_roi_area_fraction": float(np.percentile([x[1] for x in image_metrics], 95)),
            "max_roi_area_fraction": float(max([x[1] for x in image_metrics])),
            "median_roi_area_fraction": float(np.median([x[1] for x in image_metrics])),
        })

    grid_df = pd.DataFrame(rows)
    grid_df.to_csv(T / "phase13b_stage4d_proposal_grid.csv", index=False)

    feasible_configs = grid_df[grid_df.feasible]
    if len(feasible_configs) == 0:
        raise RuntimeError("No feasible configuration found in grid!")

    selected_row = feasible_configs.sort_values(
        ["tiny_recall90", "overall_recall90", "mean_roi_area_fraction", "mean_proposals_per_image", "threshold", "top_k", "margin"],
        ascending=[False, False, True, True, False, True, True],
    ).iloc[0]

    sel_cfg_df = pd.DataFrame([selected_row])
    sel_cfg_df.to_csv(T / "phase13b_stage4d_selected_config.csv", index=False)

    best_key = (float(selected_row.threshold), float(selected_row.margin), int(selected_row.top_k))
    best_eval = eval_cache[best_key]

    comp_df = best_eval["comp_df"]
    comp_df_out = comp_df[[
        "sample_id", "component_id", "kub_size_v1", "hard_tiny", "global_detected",
        "coverage_fraction", "covered90", "covered50", "any_overlap",
        "best_proposal_rank", "best_proposal_score",
    ]]
    comp_df_out.to_csv(T / "phase13b_stage4d_best_val_per_component.csv", index=False)

    img_df = best_eval["img_df"]
    img_df.to_csv(T / "phase13b_stage4d_best_val_per_image.csv", index=False)

    # Size-stratified summary
    size_records = []
    for sz in ["TINY", "SMALL", "MEDIUM", "LARGE"]:
        sub = comp_df[comp_df.kub_size_v1 == sz]
        gt_cnt = len(sub)
        c90 = int(sub.covered90.sum())
        missed = gt_cnt - c90
        rec90 = float(sub.covered90.mean()) if gt_cnt else 0.0
        c50 = int(sub.covered50.sum())
        rec50 = float(sub.covered50.mean()) if gt_cnt else 0.0
        rec_any = float(sub.any_overlap.mean()) if gt_cnt else 0.0
        mean_cov = float(sub.coverage_fraction.mean()) if gt_cnt else 0.0
        size_records.append({
            "Size": sz,
            "GT": gt_cnt,
            "covered90": c90,
            "missed": missed,
            "recall90": rec90,
            "covered50": c50,
            "recall50": rec50,
            "any_overlap_recall": rec_any,
            "mean_coverage": mean_cov,
        })
    gt_all = len(comp_df)
    c90_all = int(comp_df.covered90.sum())
    size_records.append({
        "Size": "ALL",
        "GT": gt_all,
        "covered90": c90_all,
        "missed": gt_all - c90_all,
        "recall90": float(comp_df.covered90.mean()),
        "covered50": int(comp_df.covered50.sum()),
        "recall50": float(comp_df.covered50.mean()),
        "any_overlap_recall": float(comp_df.any_overlap.mean()),
        "mean_coverage": float(comp_df.coverage_fraction.mean()),
    })
    size_df = pd.DataFrame(size_records)
    size_df.to_csv(T / "phase13b_stage4d_size_summary.csv", index=False)

    # Gate Evaluation Table
    gate_records = [
        {"criterion": "A: Tiny recall90 >= 0.50", "target": ">= 0.50", "achieved": f"{float(selected_row.tiny_recall90):.6f}", "passed": bool(selected_row.tiny_recall90 >= 0.50)},
        {"criterion": "B: Overall recall90 >= 0.50", "target": ">= 0.50", "achieved": f"{float(selected_row.overall_recall90):.6f}", "passed": bool(selected_row.overall_recall90 >= 0.50)},
        {"criterion": "C: Hard Tiny recovered90 >= 2/16", "target": ">= 2", "achieved": f"{int(selected_row.hard_tiny_recovered90)} / 16", "passed": bool(selected_row.hard_tiny_recovered90 >= 2)},
        {"criterion": "D: Mean ROI area <= 0.10", "target": "<= 0.10", "achieved": f"{float(selected_row.mean_roi_area_fraction):.6f}", "passed": bool(selected_row.mean_roi_area_fraction <= 0.10)},
        {"criterion": "E: Mean proposals/image <= 5.0", "target": "<= 5.0", "achieved": f"{float(selected_row.mean_proposals_per_image):.4f}", "passed": bool(selected_row.mean_proposals_per_image <= 5.0)},
    ]
    gate_df = pd.DataFrame(gate_records)
    gate_df.to_csv(T / "phase13b_stage4d_gate_evaluation.csv", index=False)

    all_passed = all(r["passed"] for r in gate_records)
    status_str = "FINAL_LOCALIZER_REDESIGN_PROMISING" if all_passed else "FINAL_LOCALIZER_REDESIGN_NOT_PROMISING"

    # JSON Audit
    hist_df = pd.read_csv(exp_dir / "history.csv")
    zero_props = int((img_df["num_proposals"] == 0).sum())
    audit = {
        "experiment_id": exp_id,
        "phase": "13B",
        "stage": "Stage-4D-R2",
        "best_epoch": int(best_epoch),
        "total_epochs": len(hist_df),
        "checkpoint_sha256": sha256_file(best_path),
        "latest_sha256": sha256_file(latest_path) if latest_path.exists() else None,
        "selected_configuration": {
            "threshold": float(selected_row.threshold),
            "margin": float(selected_row.margin),
            "top_k": int(selected_row.top_k),
            "nms_iou": 0.3,
        },
        "gate_evaluation": {
            "all_passed": all_passed,
            "status": status_str,
            "tiny_recall90": float(selected_row.tiny_recall90),
            "tiny_numerator": int(comp_df[comp_df.kub_size_v1 == "TINY"].covered90.sum()),
            "tiny_denominator": len(comp_df[comp_df.kub_size_v1 == "TINY"]),
            "overall_recall90": float(selected_row.overall_recall90),
            "overall_numerator": int(comp_df.covered90.sum()),
            "overall_denominator": len(comp_df),
            "hard_tiny_recovered90": int(selected_row.hard_tiny_recovered90),
            "global_empty_images_covered90": int(selected_row.global_empty_images_covered90),
            "mean_roi_area_fraction": float(selected_row.mean_roi_area_fraction),
            "median_roi_area_fraction": float(selected_row.median_roi_area_fraction),
            "p90_roi_area_fraction": float(selected_row.p90_roi_area_fraction),
            "p95_roi_area_fraction": float(selected_row.p95_roi_area_fraction),
            "max_roi_area_fraction": float(selected_row.max_roi_area_fraction),
            "mean_proposals_per_image": float(selected_row.mean_proposals_per_image),
            "zero_proposal_images": zero_props,
            "mean_max_heatmap_prob": float(np.mean(all_max_probs)),
            "median_max_heatmap_prob": float(np.median(all_max_probs)),
        },
        "size_summary": size_records,
        "runtime": {
            "mean_epoch_seconds": float(hist_df["epoch_seconds"].mean()),
            "total_training_seconds": float(hist_df["epoch_seconds"].sum()),
        },
    }

    audit_path = ROOT / "reports/audits/phase13b_stage4d_final_evaluation.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")
    print(f"Stage-4D evaluation complete. Status: {status_str}")
    print(f"Audit written to: {audit_path}")


if __name__ == "__main__":
    main()

