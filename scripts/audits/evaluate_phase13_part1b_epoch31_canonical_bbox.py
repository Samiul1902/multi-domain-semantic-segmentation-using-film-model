"""PHASE-13 PART-1B §7 — epoch-31 canonical bbox re-evaluation.

Loads the current epoch-31 checkpoint and runs ONE deterministic FULL_FIELD VAL
evaluation (103 cases / 152 components) at the single frozen proposal
configuration (0.10 / 0.20 / 5 / 0.30). No grid. No tuning.

Computes BOTH:
  * historical executing BBOX coverage  (PRIMARY, R2C canonical)
  * native pixel-mask coverage          (SECONDARY sensitivity)

The pixel metrics must reproduce the immutable epoch-31 history row within
deterministic tolerance; a material mismatch is CHECK_REQUIRED.

Writes reports/audits/phase13_part1b_epoch31_canonical_bbox_evaluation.json.
TEST is never touched.
"""
from __future__ import annotations

import csv
import datetime
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXP = "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
HISTORY = ROOT / "experiments" / EXP / "history.csv"
LATEST = ROOT / "checkpoints" / EXP / "latest.pt"
OUT = ROOT / "reports" / "audits" / "phase13_part1b_epoch31_canonical_bbox_evaluation.json"
TOL = 1e-6


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "p13_r2c", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    import torch
    import yaml
    from torch.utils.data import DataLoader

    from src.data.kub_localizer_dataset import KUBLocalizerDataset
    from src.inference.clean_v3_components import (
        assert_component_contract,
        build_clean_v3_val_components,
    )
    from src.inference.clean_v3_coverage import (
        evaluate_historical_bbox_coverage,
        evaluate_pixel_mask_coverage,
    )
    from src.inference.clean_v3_metrics import (
        aggregate_clean_v3_metrics,
        multi_component_ids,
    )
    from src.inference.predicted_roi import (
        generate_predicted_rois,
        union_roi_area_fraction,
    )
    from src.losses.localization import CenterNetFocalLoss
    from src.models.factory import create_model
    from src.utils.checkpointing import load_training_checkpoint
    from src.utils.device import get_device
    from src.utils.manifest_guard import get_manifest_path, validate_manifest_version_strict
    from src.utils.reproducibility import make_generator, seed_worker, set_seed
    from src.utils.run_lock import acquire_lock, release_lock
    from src.utils.test_lock import verify_test_lock

    runner = _load_runner()
    verify_test_lock(ROOT)
    validate_manifest_version_strict(runner.MANIFEST_VERSION)

    config = yaml.safe_load(runner.CONFIG_PATH.read_text(encoding="utf-8"))
    seed = int(config["training"]["seed"])
    set_seed(seed, deterministic=True)
    device = get_device(require_cuda=True)

    exp_dir = ROOT / "experiments" / EXP
    acquire_lock(exp_dir, EXP, recover_stale=True)
    try:
        val_ids = set(
            pd.read_csv(get_manifest_path(runner.MANIFEST_VERSION, "val"))["sample_id"].astype(str)
        )
        val_frame = pd.read_csv(ROOT / config["data"]["sample_table_val"])
        val_frame = val_frame[
            val_frame["view_type"].eq("FULL_FIELD")
            & val_frame["sample_id"].astype(str).isin(val_ids)
        ].reset_index(drop=True)

        geometry = pd.read_csv(runner.VAL_COMPONENT_TABLE)
        val_components_frame = geometry[
            geometry["sample_id"].astype(str).isin(val_ids)
        ].reset_index(drop=True)

        hard_tiny_keys, global_empty_ids = runner._load_hard_sets()
        grouped = build_clean_v3_val_components(
            val_components_frame, val_frame,
            hard_tiny_keys=hard_tiny_keys, global_empty_ids=global_empty_ids,
        )
        contract = assert_component_contract(
            grouped, hard_tiny_keys=hard_tiny_keys, global_empty_ids=global_empty_ids
        )
        flat = [c for comps in grouped.values() for c in comps]
        multi_ids = multi_component_ids(flat)

        sigma = float(config["target"]["sigma"])
        val_ds = KUBLocalizerDataset(
            val_frame, "VAL", runner.INPUT_RESOLUTION, sigma,
            heatmap_resolution=runner.HEATMAP_RESOLUTION,
        )
        val_loader = DataLoader(
            val_ds, batch_size=int(config["training"]["batch_size"]), shuffle=False,
            num_workers=0, pin_memory=True,
            generator=make_generator(seed), worker_init_fn=seed_worker,
        )

        model = create_model(
            "kub_localizer", in_channels=1, out_channels=1, base_channels=16,
            heatmap_resolution=runner.HEATMAP_RESOLUTION,
        ).to(device)
        state = load_training_checkpoint(LATEST, model, restore_rng=False, map_location=device)
        ckpt_epoch = int(state["epoch"])

        criterion = CenterNetFocalLoss(
            alpha=float(config["loss"]["alpha"]), beta=float(config["loss"]["beta"])
        )

        from PIL import Image

        from src.data.transforms import SegmentationTransform

        model.eval()
        transform = SegmentationTransform(runner.INPUT_RESOLUTION, False)
        total_loss, n_batches = 0.0, 0
        bbox_rows, pixel_rows = [], []
        per_image_proposals, roi_fractions = [], []

        with torch.inference_mode():
            for batch in val_loader:
                images = batch["image"].to(device)
                targets = batch["heatmap"].to(device)
                with torch.amp.autocast("cuda"):
                    logits = model(images)
                    loss = criterion(logits, targets)
                total_loss += float(loss.item())
                n_batches += 1
                probs = torch.sigmoid(logits.float()).cpu().numpy()
                for index, sample_id in enumerate(batch["sample_id"]):
                    sample_id = str(sample_id)
                    original_shape = (
                        int(batch["original_height"][index]),
                        int(batch["original_width"][index]),
                    )
                    probability_map = probs[index, 0]
                    runner._assert_native_geometry(probability_map)
                    with Image.open(Path(str(batch["image_path"][index]))) as handle:
                        native = handle.convert("L")
                    _img, _mask, metadata = transform(native, Image.new("L", native.size))
                    proposals = runner._generate_proposals_fixed_config(
                        probability_map, metadata, original_shape,
                        generate_predicted_rois=generate_predicted_rois,
                    )
                    per_image_proposals.append(len(proposals))
                    if proposals:
                        uf, _ = union_roi_area_fraction(proposals, original_shape)
                    else:
                        uf = 0.0
                    roi_fractions.append(float(uf))
                    comps = grouped[sample_id]
                    for row, comp in zip(
                        evaluate_historical_bbox_coverage(proposals, comps), comps
                    ):
                        bbox_rows.append({
                            "sample_id": sample_id,
                            "component_id": int(comp["component_id"]),
                            "size_stratum": comp["size_stratum"],
                            "hard_tiny": bool(comp["hard_tiny"]),
                            "global_empty_image": bool(comp["global_empty_image"]),
                            "coverage_fraction": float(row["coverage_fraction"]),
                            "covered90": bool(row["covered90"]),
                            "covered50": bool(row["covered50"]),
                            "any_overlap": bool(row["any_overlap"]),
                        })
                    for row, comp in zip(
                        evaluate_pixel_mask_coverage(proposals, comps), comps
                    ):
                        pixel_rows.append({
                            "sample_id": sample_id,
                            "component_id": int(comp["component_id"]),
                            "size_stratum": comp["size_stratum"],
                            "hard_tiny": bool(comp["hard_tiny"]),
                            "global_empty_image": bool(comp["global_empty_image"]),
                            "coverage_fraction": float(row["coverage_fraction"]),
                            "covered90": bool(row["covered90"]),
                            "covered50": bool(row["covered50"]),
                            "any_overlap": bool(row["any_overlap"]),
                        })
    finally:
        release_lock(exp_dir, force=True)

    val_loss = float(total_loss / n_batches)
    bbox_metrics = aggregate_clean_v3_metrics(bbox_rows, per_image_proposals, roi_fractions, multi_ids=multi_ids)
    pixel_metrics = aggregate_clean_v3_metrics(pixel_rows, per_image_proposals, roi_fractions, multi_ids=multi_ids)

    hist = list(csv.DictReader(open(HISTORY, newline="", encoding="utf-8")))
    e31 = next(r for r in hist if int(r["epoch"]) == 31)

    payload = {
        "artifact": "PHASE13_PART1B_EPOCH31_CANONICAL_BBOX_EVALUATION",
        "document_type": "R2C_CANONICAL_REEVALUATION",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_id": EXP,
        "checkpoint": str(LATEST),
        "checkpoint_epoch": ckpt_epoch,
        "val_cases": len(val_frame),
        "val_components": len(val_components_frame),
        "component_contract": contract,
        "proposal_config": {
            "threshold": runner.PROPOSAL_THRESHOLD, "margin": runner.PROPOSAL_MARGIN,
            "top_k": runner.PROPOSAL_TOP_K, "nms_iou": runner.PROPOSAL_NMS_IOU,
        },
        "grid_configurations_evaluated": 0,
        "val_loss": val_loss,
        "bbox_primary": {k: v for k, v in bbox_metrics.items()},
        "pixel_secondary": {k: v for k, v in pixel_metrics.items()},
        "history_epoch31": {
            "tiny_recall90": float(e31["tiny_recall90"]),
            "overall_recall90": float(e31["overall_recall90"]),
            "mean_roi_area_fraction": float(e31["mean_roi_area_fraction"]),
            "mean_proposals_per_image": float(e31["mean_proposals_per_image"]),
            "val_loss": float(e31["val_loss"]),
        },
        "pixel_reproduction": {
            "tiny_recall90_abs_diff": abs(pixel_metrics["tiny_recall90"] - float(e31["tiny_recall90"])),
            "overall_recall90_abs_diff": abs(pixel_metrics["overall_recall90"] - float(e31["overall_recall90"])),
            "mean_roi_area_fraction_abs_diff": abs(pixel_metrics["mean_roi_area_fraction"] - float(e31["mean_roi_area_fraction"])),
            "mean_proposals_per_image_abs_diff": abs(pixel_metrics["mean_proposals_per_image"] - float(e31["mean_proposals_per_image"])),
            "val_loss_abs_diff": abs(val_loss - float(e31["val_loss"])),
            "tolerance": TOL,
        },
        "test_reads": 0,
    }
    repro = payload["pixel_reproduction"]
    payload["pixel_reproduction_ok"] = all(
        repro[k] <= TOL for k in repro if k.endswith("_abs_diff")
    )
    payload["status"] = "PASS" if payload["pixel_reproduction_ok"] else "CHECK_REQUIRED"
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"checkpoint epoch      : {ckpt_epoch}")
    print(f"val_loss              : {val_loss!r}  (history {float(e31['val_loss'])!r})")
    print(f"BBOX  tiny_recall90   : {bbox_metrics['tiny_recall90']!r}")
    print(f"BBOX  overall_recall90: {bbox_metrics['overall_recall90']!r}")
    print(f"BBOX  mean_roi_frac   : {bbox_metrics['mean_roi_area_fraction']!r}")
    print(f"PIXEL tiny_recall90   : {pixel_metrics['tiny_recall90']!r}  (history {float(e31['tiny_recall90'])!r})")
    print(f"PIXEL overall_recall90: {pixel_metrics['overall_recall90']!r}  (history {float(e31['overall_recall90'])!r})")
    print(f"proposals/image       : {pixel_metrics['mean_proposals_per_image']!r}")
    print(f"pixel reproduction ok : {payload['pixel_reproduction_ok']}")
    print(f"STATUS                : {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
