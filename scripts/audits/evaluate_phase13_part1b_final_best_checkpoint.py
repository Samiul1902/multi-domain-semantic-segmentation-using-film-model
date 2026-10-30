"""PHASE-13 PART-1B §20 — final best-checkpoint integrity evaluation.

One fixed-config full-VAL evaluation of the final best.pt (103 FULL_FIELD VAL
cases, exactly one proposal configuration, no tuning), computing BOTH:

  * canonical historical BBOX coverage  (the checkpoint-selection metrics)
  * pixel-mask coverage                 (descriptive sensitivity only)

Canonical best-selection claims use BBOX only. Pixel metrics are never called the
checkpoint-selection metrics.

This is a TRAINING_COMPLETION_INTEGRITY_CHECK. Not standalone proposal analysis,
not a proposal grid, not downstream regional segmentation. TEST is never touched.
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
BEST = ROOT / "checkpoints" / EXP / "best.pt"
CANON = ROOT / "reports" / "tables" / "phase13_part1b_canonical_selection_history.csv"
OUT = ROOT / "reports" / "audits" / "phase13_clean_v3_localizer_final_best_checkpoint_integrity.json"
TOL = 1e-6


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "p13_final", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
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
    from src.inference.clean_v3_metrics import aggregate_clean_v3_metrics, multi_component_ids
    from src.inference.predicted_roi import generate_predicted_rois, union_roi_area_fraction
    from src.losses.localization import CenterNetFocalLoss
    from src.models.factory import create_model
    from src.utils.checkpointing import load_training_checkpoint
    from src.utils.device import get_device
    from src.utils.manifest_guard import get_manifest_path, validate_manifest_version_strict
    from src.utils.reproducibility import make_generator, seed_worker, set_seed
    from src.utils.run_lock import acquire_lock, release_lock
    from src.utils.test_lock import verify_test_lock
    from PIL import Image
    from src.data.transforms import SegmentationTransform

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
        comp_frame = geometry[geometry["sample_id"].astype(str).isin(val_ids)].reset_index(drop=True)

        hard_keys, empty_ids = runner._load_hard_sets()
        grouped = build_clean_v3_val_components(
            comp_frame, val_frame, hard_tiny_keys=hard_keys, global_empty_ids=empty_ids
        )
        contract = assert_component_contract(
            grouped, hard_tiny_keys=hard_keys, global_empty_ids=empty_ids
        )
        multi_ids = multi_component_ids([c for cs in grouped.values() for c in cs])

        sigma = float(config["target"]["sigma"])
        val_ds = KUBLocalizerDataset(
            val_frame, "VAL", runner.INPUT_RESOLUTION, sigma,
            heatmap_resolution=runner.HEATMAP_RESOLUTION,
        )
        loader = DataLoader(
            val_ds, batch_size=int(config["training"]["batch_size"]), shuffle=False,
            num_workers=0, pin_memory=True,
            generator=make_generator(seed), worker_init_fn=seed_worker,
        )
        model = create_model(
            "kub_localizer", in_channels=1, out_channels=1, base_channels=16,
            heatmap_resolution=runner.HEATMAP_RESOLUTION,
        ).to(device)
        state = load_training_checkpoint(BEST, model, restore_rng=False, map_location=device)
        best_epoch = int(state["epoch"])
        criterion = CenterNetFocalLoss(
            alpha=float(config["loss"]["alpha"]), beta=float(config["loss"]["beta"])
        )

        model.eval()
        transform = SegmentationTransform(runner.INPUT_RESOLUTION, False)
        total_loss, n_batches = 0.0, 0
        bbox_rows, pixel_rows, props, rois = [], [], [], []
        with torch.inference_mode():
            for batch in loader:
                images = batch["image"].to(device)
                targets = batch["heatmap"].to(device)
                with torch.amp.autocast("cuda"):
                    logits = model(images)
                    loss = criterion(logits, targets)
                total_loss += float(loss.item()); n_batches += 1
                probs = torch.sigmoid(logits.float()).cpu().numpy()
                for i, sid in enumerate(batch["sample_id"]):
                    sid = str(sid)
                    shape = (int(batch["original_height"][i]), int(batch["original_width"][i]))
                    pm = probs[i, 0]
                    runner._assert_native_geometry(pm)
                    with Image.open(Path(str(batch["image_path"][i]))) as h:
                        native = h.convert("L")
                    _im, _mk, meta = transform(native, Image.new("L", native.size))
                    proposals = runner._generate_proposals_fixed_config(
                        pm, meta, shape, generate_predicted_rois=generate_predicted_rois
                    )
                    props.append(len(proposals))
                    rois.append(float(union_roi_area_fraction(proposals, shape)[0]) if proposals else 0.0)
                    comps = grouped[sid]
                    for row, comp in zip(evaluate_historical_bbox_coverage(proposals, comps), comps):
                        bbox_rows.append({
                            "sample_id": sid, "component_id": int(comp["component_id"]),
                            "size_stratum": comp["size_stratum"],
                            "hard_tiny": bool(comp["hard_tiny"]),
                            "global_empty_image": bool(comp["global_empty_image"]),
                            "coverage_fraction": float(row["coverage_fraction"]),
                            "covered90": bool(row["covered90"]),
                            "covered50": bool(row["covered50"]),
                            "any_overlap": bool(row["any_overlap"]),
                        })
                    for row, comp in zip(evaluate_pixel_mask_coverage(proposals, comps), comps):
                        pixel_rows.append({
                            "sample_id": sid, "component_id": int(comp["component_id"]),
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
    bbox_m = aggregate_clean_v3_metrics(bbox_rows, props, rois, multi_ids=multi_ids)
    pixel_m = aggregate_clean_v3_metrics(pixel_rows, props, rois, multi_ids=multi_ids)

    hist = list(csv.DictReader(open(HISTORY, newline="", encoding="utf-8")))
    row = next(r for r in hist if int(r["epoch"]) == best_epoch)
    canon = list(csv.DictReader(open(CANON, newline="", encoding="utf-8")))
    canon_row = next(r for r in canon if int(r["epoch"]) == best_epoch)

    canon_tuple = [
        float(bbox_m["tiny_recall90"]), float(bbox_m["overall_recall90"]),
        -float(bbox_m["mean_roi_area_fraction"]), -val_loss,
    ]
    history_tuple = json.loads(canon_row["canonical_selection_tuple"])

    payload = {
        "artifact": "PHASE13_CLEAN_V3_LOCALIZER_FINAL_BEST_CHECKPOINT_INTEGRITY",
        "document_type": "TRAINING_COMPLETION_INTEGRITY_CHECK",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_id": EXP,
        "best_checkpoint_path": str(BEST),
        "best_checkpoint_epoch": best_epoch,
        "val_cases": len(val_frame),
        "val_components": len(comp_frame),
        "component_contract": contract,
        "proposal_config": {
            "threshold": runner.PROPOSAL_THRESHOLD, "margin": runner.PROPOSAL_MARGIN,
            "top_k": runner.PROPOSAL_TOP_K, "nms_iou": runner.PROPOSAL_NMS_IOU,
        },
        "grid_configurations_evaluated": 0,
        "val_loss": val_loss,
        "canonical_bbox_metrics": dict(bbox_m),
        "pixel_sensitivity_metrics": dict(pixel_m),
        "canonical_bbox_tuple": canon_tuple,
        "canonical_history_tuple": history_tuple,
        "canonical_tuple_matches_history": all(
            abs(a - b) <= TOL for a, b in zip(canon_tuple, history_tuple)
        ),
        "val_loss_abs_diff_vs_history": abs(val_loss - float(row["val_loss"])),
        "canonical_final_secondary_diagnostics_bbox": {
            "hard_tiny_recovered90": bbox_m["hard_tiny_recovered90"],
            "hard_tiny_total": bbox_m["hard_tiny_total"],
            "global_empty_images_covered90": bbox_m["global_empty_images_covered90"],
            "global_empty_total": bbox_m["global_empty_total"],
            "multi_component_recall90": bbox_m["multi_component_recall90"],
            "mean_proposals_per_image": bbox_m["mean_proposals_per_image"],
        },
        "selection_metrics_semantics": "HISTORICAL_EXECUTING_BBOX_COVERAGE",
        "pixel_metrics_are_selection_metrics": False,
        "not_standalone_proposal_analysis": True,
        "not_proposal_grid_analysis": True,
        "not_downstream_regional_segmentation": True,
        "test_reads": 0,
    }
    payload["status"] = "PASS" if payload["canonical_tuple_matches_history"] else "CHECK_REQUIRED"
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"best epoch                 : {best_epoch}")
    print(f"val_loss                   : {val_loss!r} (history {float(row['val_loss'])!r})")
    print(f"BBOX  tiny / overall       : {bbox_m['tiny_recall90']!r} / {bbox_m['overall_recall90']!r}")
    print(f"PIXEL tiny / overall       : {pixel_m['tiny_recall90']!r} / {pixel_m['overall_recall90']!r}")
    print(f"canonical tuple            : {canon_tuple}")
    print(f"matches history tuple      : {payload['canonical_tuple_matches_history']}")
    print(f"hard_tiny (bbox)           : {bbox_m['hard_tiny_recovered90']} / {bbox_m['hard_tiny_total']}")
    print(f"global_empty (bbox)        : {bbox_m['global_empty_images_covered90']} / {bbox_m['global_empty_total']}")
    print(f"multi_component (bbox)     : {bbox_m['multi_component_recall90']!r}")
    print(f"proposals/image            : {bbox_m['mean_proposals_per_image']!r}")
    print(f"STATUS                     : {payload['status']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
