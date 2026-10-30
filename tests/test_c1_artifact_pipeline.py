"""
Tests verifying the realistic synthetic C1 producer-to-consumer pipeline integration.
Demonstrates end-to-end compatibility between frozen C1 training outputs and R3 evaluation.
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import shutil
import tempfile
from pathlib import Path

import numpy as np
import pytest
import torch

from src.research.evaluation_r3.c1_artifact_pipeline import (
    C1ArtifactAnalysisPipeline,
    EXPECTED_ARMS,
    EXPECTED_SEEDS,
    EXPECTED_DOMAINS,
)


def _generate_synthetic_run_artifacts(
    run_dir: Path,
    seed: int,
    arm: str,
    *,
    is_complete: bool = True,
    corrupt_checkpoint: bool = False,
    is_synthetic_mode: bool = True,
):
    run_dir.mkdir(parents=True, exist_ok=True)
    identity = f"c1_run_identity_{arm}_{seed}"

    # 1. lifecycle.json
    lifecycle = {
        "state": "COMPLETE" if is_complete else "PAUSED",
        "identity": identity,
    }
    (run_dir / "lifecycle.json").write_text(json.dumps(lifecycle), encoding="utf-8")

    # 2. Build mock validation records
    best_records = []
    domains_counts = {"ISIC": 10, "BUSI": 5, "KVASIR": 5, "KUB": 10}
    for d, n in domains_counts.items():
        for i in range(n):
            base_dice = 0.85 if arm == "C1-T" else 0.83
            dice_val = min(1.0, max(0.0, base_dice + (seed % 5) * 0.01 + np.sin(i) * 0.02))
            best_records.append({
                "sample_id": f"mock_{d}_{i:03d}",
                "domain": d,
                "dice": float(dice_val),
                "iou": float(dice_val / (2 - dice_val)),
                "precision": 0.88,
                "recall": 0.86,
            })

    contract = {
        "schema": 1,
        "study_id": "C1_FILM_ATTRIBUTION_V1",
        "protocol_sha256": "0" * 64,
        "arm": arm,
        "seed": seed,
        "mode": "SYNTHETIC_ONLY" if is_synthetic_mode else "SCIENTIFIC_C1",
    }

    state = {
        "schema": 1,
        "identity": identity,
        "contract": contract,
        "epoch": 20,
        "best_epoch": 15,
        "best_macro": 0.85 if arm == "C1-T" else 0.83,
        "best_loss": 0.15,
        "active_seconds": 1250.0,
        "counts": {"total": 3523001, "trainable": 3523001 if arm == "C1-T" else 3432233},
        "best_records": best_records,
        "history": [],
    }

    buf = io.BytesIO()
    torch.save(state, buf)
    raw_bytes = buf.getvalue()

    checkpoint_file = f"epoch-0015-{arm}-{seed}.pt"

    # Write latest.json pointer with original uncorrupted hash
    pointer = {
        "file": checkpoint_file,
        "sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "epoch": 15,
        "identity": identity,
    }
    (run_dir / "latest.json").write_text(json.dumps(pointer), encoding="utf-8")

    # If corrupting, tamper with raw_bytes written to file
    if corrupt_checkpoint:
        raw_bytes = raw_bytes[:-10] + b"corrupt123"

    (run_dir / checkpoint_file).write_bytes(raw_bytes)


class TestC1ArtifactAnalysisPipeline:
    def test_full_synthetic_six_run_campaign(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            exp_root = Path(tmp_dir)

            for seed in EXPECTED_SEEDS:
                for arm in EXPECTED_ARMS:
                    run_dir = exp_root / f"seed{seed}" / arm
                    _generate_synthetic_run_artifacts(run_dir, seed, arm, is_synthetic_mode=True)

            pipeline = C1ArtifactAnalysisPipeline(exp_root)

            # In production mode (allow_synthetic=False), should reject mode=SYNTHETIC_ONLY
            with pytest.raises(ValueError, match="Synthetic run rejected in production analysis"):
                pipeline.execute_campaign_analysis(allow_synthetic=False)

            # In synthetic test mode, executes all 6 runs, calculates paired bootstrap and summary
            summary = pipeline.execute_campaign_analysis(allow_synthetic=True)
            assert summary["status"] == "SYNTHETIC_TEST_ONLY"
            assert "primary_estimand" in summary
            assert len(summary["per_seed_rows"]) == 3
            assert "bootstrap_95_ci" in summary
            assert len(summary["bootstrap_95_ci"]) == 2
            assert "per_domain_summary" in summary
            assert set(summary["per_domain_summary"].keys()) == set(EXPECTED_DOMAINS)

    def test_incomplete_run_rejection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            exp_root = Path(tmp_dir)

            for seed in EXPECTED_SEEDS:
                for arm in EXPECTED_ARMS:
                    run_dir = exp_root / f"seed{seed}" / arm
                    # Mark seed 42 C1-C as incomplete (PAUSED)
                    is_complete = not (seed == 42 and arm == "C1-C")
                    _generate_synthetic_run_artifacts(run_dir, seed, arm, is_complete=is_complete)

            pipeline = C1ArtifactAnalysisPipeline(exp_root)
            with pytest.raises(ValueError, match="incomplete or interrupted"):
                pipeline.execute_campaign_analysis(allow_synthetic=True)

    def test_corrupted_checkpoint_rejection(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            exp_root = Path(tmp_dir)

            for seed in EXPECTED_SEEDS:
                for arm in EXPECTED_ARMS:
                    run_dir = exp_root / f"seed{seed}" / arm
                    # Corrupt seed 123 C1-T
                    corrupt = (seed == 123 and arm == "C1-T")
                    _generate_synthetic_run_artifacts(run_dir, seed, arm, corrupt_checkpoint=corrupt)

            pipeline = C1ArtifactAnalysisPipeline(exp_root)
            with pytest.raises(ValueError, match="Checkpoint corruption detected"):
                pipeline.execute_campaign_analysis(allow_synthetic=True)
