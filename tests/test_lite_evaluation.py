from __future__ import annotations

import hashlib
import json

import pytest

from src.research.lite.evaluation import (
    FULL_COMPONENT_SHA256,
    LiteEvaluationError,
    VAL_MANIFEST_SHA256,
    aggregate_full_vs_lite,
    pareto_frontier,
)
from src.models.lite.ra_medfilm_barr_lite import CANDIDATE_SPECS


def _manifest(identity: str, seed: int, component_hashes: dict[str, str]):
    components = {
        name: {
            "checkpoint_sha256": digest,
            "seed": seed,
            "trained_against_global_sha256": component_hashes["G"],
            "trained_against_refiner_sha256": component_hashes["R_psi"],
            "trained_against_router_sha256": component_hashes["B_phi"],
        }
        for name, digest in component_hashes.items()
    }
    components["G"].pop("trained_against_global_sha256")
    components["G"].pop("trained_against_refiner_sha256")
    components["G"].pop("trained_against_router_sha256")
    bundle = hashlib.sha256(
        json.dumps(dict(sorted(component_hashes.items())), separators=(",", ":")).encode()
    ).hexdigest()
    return {
        "status": "CONFIRMED_EXECUTED_RESULT",
        "synthetic_only": False,
        "training_performed": True,
        "model_identity": identity,
        "population": "phase4_v3_VAL808",
        "val_manifest_sha256": VAL_MANIFEST_SHA256,
        "protected_splits_accessed": [],
        "seed": seed,
        "components": components,
        "component_bundle_sha256": bundle,
        **({
            "lite_variant_id": CANDIDATE_SPECS["depthwise_compact"].variant_id,
            "architecture_sha256": CANDIDATE_SPECS["depthwise_compact"].sha256(),
        } if identity == "RA-MedFiLM-BARR-Lite" else {}),
    }


def _records(roster, seed: int, dice: float):
    rows = []
    for sample_id, (domain, task_id) in roster.items():
        rows.append({
            "sample_id": sample_id,
            "domain": domain,
            "task_id": task_id,
            "split": "VAL",
            "seed": seed,
            "dice": dice,
            "iou": dice / (2.0 - dice),
            "precision": dice,
            "recall": dice,
            "global_dice": dice,
            "candidate_refinement_dice": None,
            "router_state": "SKIP_GLOBAL",
            "ground_truth_empty": False,
            "false_positive_pixels": 0,
            "hd95": None,
            "hd95_undefined_reason": "both_empty",
        })
    return rows


def _roster():
    return {
        f"{domain}-{index}": (domain, task_id)
        for domain, task_id, count in (
            ("ISIC", 0, 357),
            ("BUSI", 1, 84),
            ("KVASIR", 2, 87),
            ("KUB", 3, 280),
        )
        for index in range(count)
    }


def test_paired_aggregation_checks_roster_and_component_dependencies():
    roster = _roster()
    full_manifest = _manifest("RA-MedFiLM-BARR (FULL)", 42, FULL_COMPONENT_SHA256)
    lite_hashes = {name: chr(ord("a") + index) * 64
                   for index, name in enumerate(("G", "R_psi", "B_phi", "S_omega"))}
    lite_manifest = _manifest("RA-MedFiLM-BARR-Lite", 123, lite_hashes)
    summary = aggregate_full_vs_lite(
        full_manifest, _records(roster, 42, 0.6),
        lite_manifest, _records(roster, 123, 0.7),
        roster,
    )
    assert summary["n_paired_samples"] == 808
    assert summary["equal_domain_macro_differences"]["dice"] == pytest.approx(0.1)
    assert summary["training_seed_pairing"].startswith("UNMATCHED_REFERENCE")

    corrupted = dict(lite_manifest)
    corrupted["components"] = dict(lite_manifest["components"])
    corrupted["components"]["S_omega"] = dict(lite_manifest["components"]["S_omega"])
    corrupted["components"]["S_omega"]["trained_against_router_sha256"] = "0" * 64
    with pytest.raises(LiteEvaluationError, match="safety checkpoint family"):
        aggregate_full_vs_lite(
            full_manifest, _records(roster, 42, 0.6),
            corrupted, _records(roster, 123, 0.7), roster,
        )


def test_synthetic_and_incomplete_predictions_are_rejected():
    roster = _roster()
    full_manifest = _manifest("RA-MedFiLM-BARR (FULL)", 42, FULL_COMPONENT_SHA256)
    lite_hashes = {name: chr(ord("a") + index) * 64
                   for index, name in enumerate(("G", "R_psi", "B_phi", "S_omega"))}
    lite_manifest = _manifest("RA-MedFiLM-BARR-Lite", 42, lite_hashes)
    lite_manifest["synthetic_only"] = True
    with pytest.raises(LiteEvaluationError, match="synthetic output"):
        aggregate_full_vs_lite(
            full_manifest, _records(roster, 42, 0.6),
            lite_manifest, _records(roster, 42, 0.7), roster,
        )
    lite_manifest["synthetic_only"] = False
    with pytest.raises(LiteEvaluationError, match="roster differs"):
        aggregate_full_vs_lite(
            full_manifest, _records(roster, 42, 0.6),
            lite_manifest, _records(roster, 42, 0.7)[:-1], roster,
        )


def test_pareto_frontier_requires_measured_accuracy_and_costs():
    rows = [
        {"model_key": "full", "equal_domain_macro_dice": 0.8,
         "parameters": 4_800_000, "gmacs": 34.8, "latency_ms_p50": 1000.0,
         "evidence_status": "CONFIRMED_EXECUTED_RESULT", "synthetic_only": False,
         "latency_device_fingerprint": "device-a", "latency_batch_size": 1},
        {"model_key": "lite", "equal_domain_macro_dice": 0.79,
         "parameters": 270_000, "gmacs": 1.82, "latency_ms_p50": 400.0,
         "evidence_status": "CONFIRMED_EXECUTED_RESULT", "synthetic_only": False,
         "latency_device_fingerprint": "device-a", "latency_batch_size": 1},
    ]
    assert set(pareto_frontier(rows)) == {"full", "lite"}
    with pytest.raises(LiteEvaluationError, match="missing"):
        pareto_frontier([{"model_key": "unmeasured"}])
    rows[0]["synthetic_only"] = True
    with pytest.raises(LiteEvaluationError, match="synthetic"):
        pareto_frontier(rows)


def test_router_harm_and_empty_ground_truth_failures_are_counted():
    roster = _roster()
    full_manifest = _manifest("RA-MedFiLM-BARR (FULL)", 42, FULL_COMPONENT_SHA256)
    lite_hashes = {name: chr(ord("a") + index) * 64
                   for index, name in enumerate(("G", "R_psi", "B_phi", "S_omega"))}
    lite_manifest = _manifest("RA-MedFiLM-BARR-Lite", 42, lite_hashes)
    full_rows = _records(roster, 42, 0.7)
    lite_rows = _records(roster, 42, 0.7)
    lite_rows[0].update({
        "dice": 0.5,
        "global_dice": 0.7,
        "candidate_refinement_dice": 0.5,
        "router_state": "EXECUTE_THEN_ACCEPT",
    })
    for rows in (full_rows, lite_rows):
        rows[1].update({
            "dice": 0.0,
            "global_dice": 0.0,
            "ground_truth_empty": True,
            "false_positive_pixels": 3,
        })
    summary = aggregate_full_vs_lite(
        full_manifest, full_rows, lite_manifest, lite_rows, roster
    )
    assert summary["router_safety_failure_summary"]["lite"]["accepted_harmful"] == 1
    assert summary["router_safety_failure_summary"]["lite"][
        "empty_ground_truth_false_positive_cases"
    ] == 1
