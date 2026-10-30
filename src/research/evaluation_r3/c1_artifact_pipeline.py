"""
Adapter and comprehensive pipeline connecting C1 real-artifact production outputs
to the authoritative R3/R1 statistical evaluation contracts.
"""
from __future__ import annotations

import copy
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from src.research.evaluation_r3.analysis_contract import R3AnalysisContract
from src.research.evaluation_r1.statistics import paired_bootstrap

EXPECTED_ARMS = ("C1-T", "C1-C")
EXPECTED_SEEDS = (42, 123, 3407)
EXPECTED_DOMAINS = ("KUB", "ISIC", "BUSI", "KVASIR")
VAL808_COUNTS = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}

FROZEN_C1_N_BOOT = 10000
FROZEN_C1_RNG_SEED = 20261027
FROZEN_C1_CONFIDENCE = 0.95
FROZEN_C1_PATIENT_DOMAINS = ("KUB",)


def load_val808_patient_roster(manifest_path: Optional[Path] = None) -> Dict[str, Optional[str]]:
    """Loads sample_id -> patient_id mapping from canonical Manifest v3 val.csv."""
    if manifest_path is None:
        manifest_path = Path(__file__).resolve().parents[3] / "manifests/phase4_v3/val.csv"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Canonical validation manifest not found at {manifest_path}")

    roster = {}
    with open(manifest_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = row["sample_id"]
            pid = row.get("patient_id")
            if pid is None or pid.strip() == "" or pid.upper() == "NOT_AVAILABLE":
                roster[sid] = None
            else:
                roster[sid] = pid.strip()
    return roster


class C1ArtifactAnalysisPipeline:
    """Reads genuine (or synthetic fixture) C1 experiment runs and executes statistical analysis."""

    def __init__(self, experiment_root: Path, patient_roster: Optional[Dict[str, Optional[str]]] = None):
        self.root = Path(experiment_root)
        self.patient_roster = patient_roster

    def discover_and_validate_run(self, seed: int, arm: str) -> Dict[str, Any]:
        """Verify directory structure, lifecycle, checkpoint pointers, and payload for one arm/seed."""
        run_dir = self.root / f"seed{seed}" / arm
        if not run_dir.exists():
            raise FileNotFoundError(f"Missing expected run directory: {run_dir}")

        # 1. Lifecycle verification
        lifecycle_file = run_dir / "lifecycle.json"
        if not lifecycle_file.exists():
            raise ValueError(f"Missing lifecycle.json in {run_dir}")
        lifecycle = json.loads(lifecycle_file.read_text(encoding="utf-8"))
        if lifecycle.get("state") != "COMPLETE":
            raise ValueError(f"Run {arm}-seed{seed} incomplete or interrupted: state={lifecycle.get('state')}")

        # 2. Latest pointer verification
        latest_file = run_dir / "latest.json"
        if not latest_file.exists():
            raise ValueError(f"Missing latest.json in {run_dir}")
        pointer = json.loads(latest_file.read_text(encoding="utf-8"))

        checkpoint_name = pointer.get("file")
        checkpoint_path = run_dir / checkpoint_name
        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Pointed checkpoint {checkpoint_name} missing in {run_dir}")

        raw_bytes = checkpoint_path.read_bytes()
        actual_sha = hashlib.sha256(raw_bytes).hexdigest()
        if actual_sha != pointer.get("sha256"):
            raise ValueError(f"Checkpoint corruption detected in {checkpoint_name}: hash mismatch")

        # 3. Load payload safely
        state = torch.load(io.BytesIO(raw_bytes), map_location="cpu", weights_only=True)
        if state.get("identity") != pointer.get("identity"):
            raise ValueError(f"Identity mismatch between pointer and payload in {checkpoint_name}")

        # 4. Check contract consistency
        contract = state.get("contract", {})
        if contract.get("arm") != arm:
            raise ValueError(f"Contract arm mismatch: expected {arm}, got {contract.get('arm')}")
        if contract.get("seed") != seed:
            raise ValueError(f"Contract seed mismatch: expected {seed}, got {contract.get('seed')}")

        # 5. Extract best records and history
        best_records = state.get("best_records", [])
        if not best_records:
            raise ValueError(f"No best_records found in state of {arm}-seed{seed}")

        domain_dice = {}
        for d in EXPECTED_DOMAINS:
            d_dices = [r["dice"] for r in best_records if r.get("domain") == d]
            if not d_dices:
                raise ValueError(f"No validation records for domain {d} in {arm}-seed{seed}")
            domain_dice[d] = float(np.mean(d_dices))

        return {
            "arm": arm,
            "seed": seed,
            "identity": state.get("identity"),
            "model_checkpoint_sha256": actual_sha,
            "training_config_sha256": hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest(),
            "dataset_manifest_sha256": contract.get("protocol_sha256", "0" * 64),
            "selected_epoch": state.get("best_epoch"),
            "duration_seconds": state.get("active_seconds", 0.0),
            "gpu_peak_memory_mb": 0.0,
            "metric_version": "c1_phase21_compatibility_v1",
            "per_domain_results": domain_dice,
            "best_records": best_records,
            "mode": contract.get("mode", "SCIENTIFIC_C1"),
        }

    def execute_campaign_analysis(
        self,
        *,
        allow_synthetic: bool = False,
        n_boot: Optional[int] = None,
        rng_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Verify all 6 runs and perform paired treatment-control statistical evaluation."""
        if n_boot is None:
            n_boot = 200 if allow_synthetic else FROZEN_C1_N_BOOT
        if rng_seed is None:
            rng_seed = FROZEN_C1_RNG_SEED

        t_records = {}
        c_records = {}
        all_runs = []

        # Step 1: Collect and validate all 6 runs
        for seed in EXPECTED_SEEDS:
            t_rec = self.discover_and_validate_run(seed, "C1-T")
            c_rec = self.discover_and_validate_run(seed, "C1-C")

            if not allow_synthetic:
                if t_rec["mode"] == "SYNTHETIC_ONLY" or c_rec["mode"] == "SYNTHETIC_ONLY":
                    raise ValueError("Synthetic run rejected in production analysis (mode=SYNTHETIC_ONLY)")

            t_records[seed] = t_rec
            c_records[seed] = c_rec
            all_runs.extend([t_rec, c_rec])

        # Step 2: Validate against R3 analysis contract
        for r in all_runs:
            val = R3AnalysisContract.validate_c1_run_record(r)
            if not val.get("valid"):
                raise ValueError(f"R3 contract violation for {r['arm']}-seed{r['seed']}: {val.get('reason')}")

        # Step 3: Align case-level records across pairs
        paired_case_rows = []
        cluster_census = {"KUB_patients": set(), "image_only_cases": 0}

        for seed in EXPECTED_SEEDS:
            t_cases = {r["sample_id"]: r for r in t_records[seed]["best_records"]}
            c_cases = {r["sample_id"]: r for r in c_records[seed]["best_records"]}

            if set(t_cases.keys()) != set(c_cases.keys()):
                raise ValueError(f"Sample ID mismatch between C1-T and C1-C for seed {seed}")

            for sid, t_item in t_cases.items():
                c_item = c_cases[sid]
                domain = t_item["domain"]

                # Patient cluster identifier lookup
                patient_id = None
                if domain in FROZEN_C1_PATIENT_DOMAINS:
                    if self.patient_roster is not None and sid in self.patient_roster:
                        patient_id = self.patient_roster[sid]
                    elif allow_synthetic:
                        # For synthetic test fixture, establish mock patient clustering
                        patient_id = f"synthetic_pat_{sid}"
                    else:
                        raise ValueError(f"Verified patient ID missing for {domain} sample {sid}")
                    cluster_census["KUB_patients"].add(patient_id)
                else:
                    cluster_census["image_only_cases"] += 1

                paired_case_rows.append({
                    "domain": domain,
                    "sample_id": sid,
                    "seed": seed,
                    "treatment": float(t_item["dice"]),
                    "control": float(c_item["dice"]),
                    "patient_id": patient_id,
                })

        # Step 4: Run paired cluster bootstrap
        boot_res = paired_bootstrap(
            paired_case_rows,
            seeds=EXPECTED_SEEDS,
            domains=EXPECTED_DOMAINS,
            n_boot=n_boot,
            rng_seed=rng_seed,
            confidence=FROZEN_C1_CONFIDENCE,
            patient_domains=FROZEN_C1_PATIENT_DOMAINS,
        )

        ci_low = boot_res["ci"][0]
        ci_high = boot_res["ci"][1]

        # Step 5: Format publication-ready summary
        summary = R3AnalysisContract.format_c1_summary_table(
            t_records, c_records, bootstrap_ci=(ci_low, ci_high)
        )
        summary["status"] = "CONFIRMED_EXECUTED_RESULT" if not allow_synthetic else "SYNTHETIC_TEST_ONLY"
        summary["case_level_bootstrap_result"] = boot_res
        summary["cluster_census"] = {
            "KUB_patient_clusters": len(cluster_census["KUB_patients"]),
            "patient_domains": list(FROZEN_C1_PATIENT_DOMAINS),
            "bootstrap_draws": n_boot,
            "rng_seed": rng_seed,
            "ci_method": boot_res.get("ci_method"),
        }

        # Add domain-level details
        domain_summary = {}
        for d in EXPECTED_DOMAINS:
            d_deltas = [
                t_records[s]["per_domain_results"][d] - c_records[s]["per_domain_results"][d]
                for s in EXPECTED_SEEDS
            ]
            domain_summary[d] = {
                "mean_treatment": float(np.mean([t_records[s]["per_domain_results"][d] for s in EXPECTED_SEEDS])),
                "mean_control": float(np.mean([c_records[s]["per_domain_results"][d] for s in EXPECTED_SEEDS])),
                "paired_delta": float(np.mean(d_deltas)),
            }
        summary["per_domain_summary"] = domain_summary

        return summary
