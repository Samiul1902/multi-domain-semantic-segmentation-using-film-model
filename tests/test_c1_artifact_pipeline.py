"""
Tests verifying the exact C1 statistical protocol, patient-cluster resolution,
and genuine producer-to-consumer serialization integration.
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

from src.research.c1_film.integration_contract import make_contract
from src.research.c1_film.training_engine import Trainer
from src.research.c1_film.synthetic_fixture import fixture_loaders
from src.research.evaluation_r3.c1_artifact_pipeline import (
    C1ArtifactAnalysisPipeline,
    EXPECTED_ARMS,
    EXPECTED_SEEDS,
    EXPECTED_DOMAINS,
    FROZEN_C1_N_BOOT,
    FROZEN_C1_RNG_SEED,
    load_val808_patient_roster,
)


class TestC1StatisticalAndSerializationPipeline:
    def test_val808_patient_roster_loading(self):
        """Verify that val808 roster correctly extracts KUB patient IDs without opening images."""
        roster = load_val808_patient_roster()
        assert len(roster) == 808
        kub_with_patients = [sid for sid, pid in roster.items() if pid is not None and pid.startswith("patient-")]
        assert len(kub_with_patients) == 280
        distinct_kub_patients = {roster[sid] for sid in kub_with_patients}
        assert len(distinct_kub_patients) == 111

    def test_genuine_producer_serialization_and_pipeline_execution(self):
        """Use actual Trainer class and fixture_loaders to generate real serialized checkpoints."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            exp_root = Path(tmp_dir)

            for seed in EXPECTED_SEEDS:
                for arm in EXPECTED_ARMS:
                    run_dir = exp_root / f"seed{seed}" / arm
                    contract = make_contract(arm, seed, synthetic=True, device="cpu")
                    trainer = Trainer(contract)
                    result = trainer.run(run_dir, fixture_loaders)
                    assert result["complete"] is True
                    assert (run_dir / "lifecycle.json").exists()
                    assert (run_dir / "latest.json").exists()

            pipeline = C1ArtifactAnalysisPipeline(exp_root)

            # In production mode (allow_synthetic=False), mode=SYNTHETIC_ONLY must be rejected
            with pytest.raises(ValueError, match="Synthetic run rejected in production analysis"):
                pipeline.execute_campaign_analysis(allow_synthetic=False)

            # In synthetic test mode, executes paired bootstrap under frozen RNG seed
            summary = pipeline.execute_campaign_analysis(allow_synthetic=True, n_boot=500, rng_seed=FROZEN_C1_RNG_SEED)
            assert summary["status"] == "SYNTHETIC_TEST_ONLY"
            assert "primary_estimand" in summary
            assert len(summary["per_seed_rows"]) == 3
            assert len(summary["bootstrap_95_ci"]) == 2
            assert summary["cluster_census"]["bootstrap_draws"] == 500
            assert summary["cluster_census"]["rng_seed"] == FROZEN_C1_RNG_SEED

    def test_checkpoint_tampering_and_lineage_rejection(self):
        """Verify that tampering with raw checkpoint bytes or lifecycle fails validation."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            exp_root = Path(tmp_dir)

            # Generate runs using actual Trainer
            for seed in EXPECTED_SEEDS:
                for arm in EXPECTED_ARMS:
                    run_dir = exp_root / f"seed{seed}" / arm
                    contract = make_contract(arm, seed, synthetic=True, device="cpu")
                    trainer = Trainer(contract)
                    trainer.run(run_dir, fixture_loaders)

            # 1. Tamper with checkpoint bytes in seed 42 C1-T
            target_dir = exp_root / "seed42" / "C1-T"
            pointer = json.loads((target_dir / "latest.json").read_text(encoding="utf-8"))
            ckpt_path = target_dir / pointer["file"]
            raw = ckpt_path.read_bytes()
            ckpt_path.write_bytes(raw[:-10] + b"tampered99")

            pipeline = C1ArtifactAnalysisPipeline(exp_root)
            with pytest.raises(ValueError, match="Checkpoint corruption detected"):
                pipeline.execute_campaign_analysis(allow_synthetic=True)

            # Restore checkpoint bytes, then tamper with lifecycle.json state
            ckpt_path.write_bytes(raw)
            (target_dir / "lifecycle.json").write_text(json.dumps({"state": "PAUSED", "identity": pointer["identity"]}))
            with pytest.raises(ValueError, match="incomplete or interrupted"):
                pipeline.execute_campaign_analysis(allow_synthetic=True)
