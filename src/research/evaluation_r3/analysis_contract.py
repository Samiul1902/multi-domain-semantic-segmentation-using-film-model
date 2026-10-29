"""
Prospective Analysis and Schema Contracts for R3 Scientific Evaluation.
"""

from typing import Dict, Any, List, Optional
import json
import numpy as np


class R3AnalysisContract:
    """Enforces prospective analysis, budget accounting, and publication artifact schema."""

    @staticmethod
    def validate_c1_run_record(record: Dict[str, Any]) -> Dict[str, Any]:
        """Validate structure and required fields of a single C1 run record."""
        required = [
            "arm", "seed", "model_checkpoint_sha256", "training_config_sha256",
            "dataset_manifest_sha256", "per_domain_results", "selected_epoch",
            "duration_seconds", "gpu_peak_memory_mb", "metric_version"
        ]
        missing = [f for f in required if f not in record]
        if missing:
            return {"valid": False, "reason": f"Missing required fields: {missing}"}

        if record["arm"] not in {"C1-T", "C1-C"}:
            return {"valid": False, "reason": f"Invalid arm: {record['arm']}. Must be C1-T or C1-C."}

        if record["seed"] not in {42, 123, 3407}:
            return {"valid": False, "reason": f"Invalid seed: {record['seed']}. Frozen seeds are [42, 123, 3407]."}

        domains = set(record["per_domain_results"].keys())
        expected_domains = {"KUB", "ISIC", "BUSI", "KVASIR"}
        if domains != expected_domains:
            return {"valid": False, "reason": f"Domain mismatch: got {domains}, expected {expected_domains}"}

        return {"valid": True, "status": "VERIFIED"}

    @staticmethod
    def compute_equal_domain_macro(domain_means: Dict[str, float]) -> float:
        """Compute unweighted 4-domain macro average."""
        expected = ["KUB", "ISIC", "BUSI", "KVASIR"]
        if not all(d in domain_means for d in expected):
            raise ValueError(f"All 4 domains {expected} required for equal macro.")
        return float(np.mean([domain_means[d] for d in expected]))

    @staticmethod
    def format_c1_summary_table(
        t_records: Dict[int, Dict[str, Any]],
        c_records: Dict[int, Dict[str, Any]],
        bootstrap_ci: tuple
    ) -> Dict[str, Any]:
        """Generate publication-ready table structure for C1 matched comparison."""
        rows = []
        seed_deltas = []
        seeds = [42, 123, 3407]

        for s in seeds:
            t_macro = R3AnalysisContract.compute_equal_domain_macro(t_records[s]["per_domain_results"])
            c_macro = R3AnalysisContract.compute_equal_domain_macro(c_records[s]["per_domain_results"])
            delta = t_macro - c_macro
            seed_deltas.append(delta)
            rows.append({
                "seed": s,
                "c1_treatment_macro": t_macro,
                "c1_control_macro": c_macro,
                "paired_delta": delta,
                "domain_details": {
                    d: {
                        "t": t_records[s]["per_domain_results"][d],
                        "c": c_records[s]["per_domain_results"][d],
                        "delta": t_records[s]["per_domain_results"][d] - c_records[s]["per_domain_results"][d]
                    } for d in ["KUB", "ISIC", "BUSI", "KVASIR"]
                }
            })

        mean_delta = float(np.mean(seed_deltas))
        sd_delta = float(np.std(seed_deltas, ddof=1))

        return {
            "primary_estimand": "Mean over 3 matched seeds of EqualDomainMacroDice(C1-T) - EqualDomainMacroDice(C1-C)",
            "mean_paired_delta": mean_delta,
            "seed_sample_sd": sd_delta,
            "bootstrap_95_ci": list(bootstrap_ci),
            "per_seed_rows": rows,
            "status": "SYNTHETIC_TEST_ONLY"
        }
