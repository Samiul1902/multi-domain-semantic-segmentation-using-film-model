"""
Audit and Leakage-Detection Contract for R2 Evaluation Engine.

Provides automated checks for dataset integrity, split leakage, patient overlap,
manifest verification, and prediction artifact contracts across C1/C2/C3 pipelines.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
import numpy as np


class LeakageAuditContract:
    def __init__(self, ontology_path: Optional[str] = None):
        if ontology_path is None:
            ontology_path = str(Path(__file__).parent / "ontology_r2.json")
        with open(ontology_path, "r", encoding="utf-8-sig") as f:
            self.ontology = json.load(f)

    def verify_split_disjointness(
        self,
        train_samples: Set[str],
        val_samples: Set[str],
        train_patients: Optional[Dict[str, str]] = None,
        val_patients: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Verify strict absence of overlap in sample IDs and patient IDs."""
        sample_overlap = train_samples.intersection(val_samples)
        result = {
            "sample_overlap_count": len(sample_overlap),
            "sample_overlap_ids": sorted(list(sample_overlap))[:10],
            "sample_disjoint": len(sample_overlap) == 0,
            "patient_disjoint": "NOT_CHECKED",
            "status": "PASS" if len(sample_overlap) == 0 else "FAIL_LEAKAGE"
        }

        if train_patients is not None and val_patients is not None:
            train_p = {v for k, v in train_patients.items() if v and v != "NOT_AVAILABLE"}
            val_p = {v for k, v in val_patients.items() if v and v != "NOT_AVAILABLE"}
            patient_overlap = train_p.intersection(val_p)
            result["patient_overlap_count"] = len(patient_overlap)
            result["patient_overlap_ids"] = sorted(list(patient_overlap))[:10]
            result["patient_disjoint"] = len(patient_overlap) == 0
            if len(patient_overlap) > 0:
                result["status"] = "FAIL_PATIENT_LEAKAGE"

        return result

    def validate_evaluation_request(
        self,
        split: str,
        domain: str,
        probabilities: np.ndarray,
        ground_truth: np.ndarray,
        spacing: Optional[Tuple[float, float]] = None,
        patient_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate evaluation inputs against domain ontology, rejected splits,
        and spacing physical reality.
        """
        issues = []

        # 1. Reject prohibited splits
        if split.upper() in {"TEST", "ROUTER_HOLDOUT", "QUARANTINE", "EXTERNAL"}:
            return {
                "valid": False,
                "reason": f"PROHIBITED_SPLIT_ACCESS: {split} evaluation is unauthorized without explicit protocol unlock.",
                "status": "REJECTED"
            }

        # 2. Domain check & canonicalization
        canon_domain = None
        for dom, info in self.ontology["domains"].items():
            if domain in info["valid_aliases"] or domain == dom:
                canon_domain = dom
                break

        if canon_domain is None:
            return {
                "valid": False,
                "reason": f"UNKNOWN_DOMAIN: {domain} not in canonical ontology.",
                "status": "REJECTED"
            }

        # 3. Shape & value sanity
        if probabilities.shape != ground_truth.shape:
            return {
                "valid": False,
                "reason": f"SHAPE_MISMATCH: prob shape {probabilities.shape} != gt shape {ground_truth.shape}",
                "status": "REJECTED"
            }

        if np.isnan(probabilities).any() or np.isinf(probabilities).any():
            return {
                "valid": False,
                "reason": "INVALID_PROBABILITIES: NaNs or Infs present in probability map.",
                "status": "REJECTED"
            }

        if (probabilities < 0.0).any() or (probabilities > 1.0).any():
            return {
                "valid": False,
                "reason": "OUT_OF_BOUNDS_PROBABILITIES: values outside [0.0, 1.0].",
                "status": "REJECTED"
            }

        # 4. Spacing interpretation check
        dom_meta = self.ontology["domains"][canon_domain]
        spacing_unit = "pixel"
        if spacing is not None:
            if not dom_meta["physical_pixel_spacing"]["measured_mm_available"]:
                issues.append("PHYSICAL_SPACING_UNVERIFIED: Native physical mm spacing is NOT_AVAILABLE for domain; treating spacing as unitless pixel ratio.")
            spacing_unit = "mm" if dom_meta["physical_pixel_spacing"]["measured_mm_available"] else "pixel"

        # 5. Patient ID availability check
        has_pat_id = patient_id is not None and patient_id != "NOT_AVAILABLE" and str(patient_id).strip() != ""
        if has_pat_id and not dom_meta["patient_identifiers"]["cluster_bootstrap_eligible"]:
            issues.append(f"UNVERIFIED_PATIENT_ID: Domain {canon_domain} has no verified patient ID in canonical split; ID {patient_id} cannot be used for cluster bootstrap.")

        return {
            "valid": True,
            "status": "PASS" if len(issues) == 0 else "PASS_WITH_WARNINGS",
            "canonical_domain": canon_domain,
            "spacing_unit": spacing_unit,
            "cluster_bootstrap_eligible": dom_meta["patient_identifiers"]["cluster_bootstrap_eligible"] and has_pat_id,
            "warnings": issues
        }
