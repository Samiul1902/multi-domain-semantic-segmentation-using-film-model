"""PHASE-13 PART-1B §16 — epoch-28 corrected-evaluator integrity check.

Narrowly scoped VAL integrity inference. Loads latest.pt (epoch 28) and runs the
103 clean-v3 FULL_FIELD VAL cases through the R2B-corrected evaluator at the ONE
frozen proposal configuration (0.10 / 0.20 / 5 / 0.30). No grid. No tuning.

This is a METRIC_REPAIR_INTEGRITY_CHECK. It is NOT standalone proposal analysis.

Expected (from pre-stop evidence): 0 proposals on all 103 images, all primary
and secondary terms zero, and corrected val_loss matching immutable history
epoch 28 within 1e-6.

Writes reports/audits/phase13_part1b_epoch28_corrected_integrity.json.
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
OUT = ROOT / "reports" / "audits" / "phase13_part1b_epoch28_corrected_integrity.json"
VAL_TOL = 1e-6


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "p13_runner", ROOT / "scripts" / "training" / "train_phase13_clean_v3_localizer.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    import torch
    import yaml
    from torch.utils.data import DataLoader

    from src.data.kub_localizer_dataset import KUBLocalizerDataset
    from src.losses.localization import CenterNetFocalLoss
    from src.models.factory import create_model
    from src.utils.checkpointing import load_training_checkpoint
    from src.utils.manifest_guard import (
        get_manifest_path,
        validate_manifest_version_strict,
    )
    from src.utils.run_lock import acquire_lock, release_lock
    from src.utils.reproducibility import make_generator, seed_worker, set_seed
    from src.utils.test_lock import verify_test_lock

    runner = _load_runner()
    verify_test_lock(ROOT)

    config = yaml.safe_load(runner.CONFIG_PATH.read_text(encoding="utf-8"))
    validate_manifest_version_strict(runner.MANIFEST_VERSION)
    seed = int(config["training"]["seed"])
    set_seed(seed, deterministic=True)

    from src.utils.device import get_device

    device = get_device(require_cuda=True)

    exp_dir = ROOT / "experiments" / EXP
    acquire_lock(exp_dir, EXP, recover_stale=True)
    try:
        val_ids = set(
            pd.read_csv(get_manifest_path(runner.MANIFEST_VERSION, "val"))["sample_id"].astype(str)
        )
        data_cfg = config["data"]
        val_frame = pd.read_csv(ROOT / data_cfg["sample_table_val"])
        val_frame = val_frame[
            val_frame["view_type"].eq("FULL_FIELD")
            & val_frame["sample_id"].astype(str).isin(val_ids)
        ].reset_index(drop=True)
        if len(val_frame) != runner.EXPECTED_VAL_CASES:
            raise ValueError(f"VAL cases {len(val_frame)} != {runner.EXPECTED_VAL_CASES}")

        geometry = pd.read_csv(runner.VAL_COMPONENT_TABLE)
        val_components = geometry[
            geometry["sample_id"].astype(str).isin(val_ids)
        ].reset_index(drop=True)
        if len(val_components) != runner.EXPECTED_VAL_COMPONENTS:
            raise ValueError(f"VAL components {len(val_components)} mismatch")

        sigma = float(config["target"]["sigma"])
        val_ds = KUBLocalizerDataset(
            val_frame, "VAL", runner.INPUT_RESOLUTION, sigma,
            heatmap_resolution=runner.HEATMAP_RESOLUTION,
        )
        batch_size = int(config["training"]["batch_size"])
        val_loader = DataLoader(
            val_ds, batch_size=batch_size, shuffle=False,
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

        val_loss, metrics = runner.evaluate_fixed_config_localizer(
            model, val_loader, criterion, device, config,
            val_component_frame=val_components,
            val_sample_frame=val_frame,
        )
    finally:
        release_lock(exp_dir, force=True)

    hist = list(csv.DictReader(open(HISTORY, newline="", encoding="utf-8")))
    e28 = hist[-1]
    hist_val_loss = float(e28["val_loss"])
    hist_tuple = [
        float(e28["tiny_recall90"]),
        float(e28["overall_recall90"]),
        -float(e28["mean_roi_area_fraction"]),
        -float(e28["val_loss"]),
    ]
    corrected_tuple = [
        float(metrics["tiny_recall90"]),
        float(metrics["overall_recall90"]),
        -float(metrics["mean_roi_area_fraction"]),
        -float(val_loss),
    ]

    payload = {
        "artifact": "PHASE13_PART1B_EPOCH28_CORRECTED_INTEGRITY",
        "document_type": "METRIC_REPAIR_INTEGRITY_CHECK",
        "created_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "experiment_id": EXP,
        "checkpoint": str(LATEST),
        "checkpoint_epoch": ckpt_epoch,
        "val_cases": len(val_frame),
        "val_components": len(val_components),
        "proposal_config": {
            "threshold": runner.PROPOSAL_THRESHOLD,
            "margin": runner.PROPOSAL_MARGIN,
            "top_k": runner.PROPOSAL_TOP_K,
            "nms_iou": runner.PROPOSAL_NMS_IOU,
        },
        "grid_configurations_evaluated": 0,
        "corrected_metrics": {k: v for k, v in metrics.items() if k != "component_contract"},
        "component_contract": metrics.get("component_contract"),
        "val_loss_corrected": float(val_loss),
        "val_loss_history_epoch28": hist_val_loss,
        "val_loss_abs_diff": abs(float(val_loss) - hist_val_loss),
        "val_loss_tolerance": VAL_TOL,
        "val_loss_within_tolerance": abs(float(val_loss) - hist_val_loss) <= VAL_TOL,
        "primary_tuple_history_epoch28": hist_tuple,
        "primary_tuple_corrected": corrected_tuple,
        "primary_tuple_equal": all(
            abs(a - b) <= VAL_TOL for a, b in zip(hist_tuple, corrected_tuple)
        ),
        "expected_zero_proposals": True,
        "mean_proposals_per_image": metrics["mean_proposals_per_image"],
        "no_grid": True,
        "no_tuning": True,
        "not_standalone_proposal_analysis": True,
        "test_reads": 0,
    }
    payload["status"] = (
        "PASS"
        if (
            payload["val_loss_within_tolerance"]
            and payload["primary_tuple_equal"]
            and metrics["mean_proposals_per_image"] == 0.0
        )
        else "CHECK_REQUIRED"
    )
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    print(f"checkpoint epoch          : {ckpt_epoch}")
    print(f"val cases / components    : {len(val_frame)} / {len(val_components)}")
    print(f"val_loss corrected        : {float(val_loss)!r}")
    print(f"val_loss history epoch 28 : {hist_val_loss!r}")
    print(f"abs diff                  : {payload['val_loss_abs_diff']!r}")
    print(f"primary tuple equal       : {payload['primary_tuple_equal']}")
    print(f"mean_proposals_per_image  : {metrics['mean_proposals_per_image']}")
    print(f"hard_tiny_recovered90     : {metrics['hard_tiny_recovered90']} / {metrics['hard_tiny_total']}")
    print(f"global_empty_covered90    : {metrics['global_empty_images_covered90']} / {metrics['global_empty_total']}")
    print(f"STATUS                    : {payload['status']}")
    return 0 if payload["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
