"""Paired, secondary evaluation contracts for future BARR-Lite results."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
import hashlib
import json
import math
from typing import Any

from src.models.lite.ra_medfilm_barr_lite import CANDIDATE_SPECS


DOMAINS = ("ISIC", "BUSI", "KVASIR", "KUB")
TASK_IDS = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
EXPECTED_DOMAIN_COUNTS = {"ISIC": 357, "BUSI": 84, "KVASIR": 87, "KUB": 280}
LITE_SEEDS = (42, 123, 3407)
VAL_MANIFEST_SHA256 = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
HD95_UNDEFINED_REASONS = {"both_empty", "empty_prediction", "empty_ground_truth"}
METRIC_KEYS = ("dice", "iou", "precision", "recall")
FULL_COMPONENT_SHA256 = {
    "G": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "R_psi": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "B_phi": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
    "S_omega": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
}


class LiteEvaluationError(ValueError):
    """Raised when a Lite evaluation cannot support a paired comparison."""


def _validate_manifest(manifest: Mapping[str, Any], expected_identity: str) -> None:
    if manifest.get("synthetic_only") is not False:
        raise LiteEvaluationError("synthetic output cannot be accepted as research evidence")
    if manifest.get("status") != "CONFIRMED_EXECUTED_RESULT":
        raise LiteEvaluationError("evaluation manifest is not a completed real-data run")
    if manifest.get("model_identity") != expected_identity:
        raise LiteEvaluationError("evaluation model identity mismatch")
    if manifest.get("population") != "phase4_v3_VAL808":
        raise LiteEvaluationError("evaluation population must be phase4_v3_VAL808")
    if manifest.get("val_manifest_sha256") != VAL_MANIFEST_SHA256:
        raise LiteEvaluationError("validation manifest digest mismatch")
    if manifest.get("protected_splits_accessed") != []:
        raise LiteEvaluationError("protected split access invalidates this evaluation")
    if manifest.get("training_performed") is not True:
        raise LiteEvaluationError("evaluation requires trained checkpoint provenance")
    seed = manifest.get("seed")
    components = manifest.get("components")
    if not isinstance(seed, int) or not isinstance(components, Mapping):
        raise LiteEvaluationError("checkpoint component provenance is required")
    if set(components) != {"G", "R_psi", "B_phi", "S_omega"}:
        raise LiteEvaluationError("checkpoint bundle must contain exactly four components")
    hashes: dict[str, str] = {}
    for name, component in components.items():
        if not isinstance(component, Mapping) or component.get("seed") != seed:
            raise LiteEvaluationError(f"checkpoint component seed mismatch: {name}")
        digest = component.get("checkpoint_sha256")
        if (not isinstance(digest, str) or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest.lower())):
            raise LiteEvaluationError(f"invalid checkpoint digest: {name}")
        hashes[name] = digest
    global_hash = hashes["G"]
    refiner_hash = hashes["R_psi"]
    router_hash = hashes["B_phi"]
    if components["R_psi"].get("trained_against_global_sha256") != global_hash:
        raise LiteEvaluationError("refiner is not bound to this global checkpoint")
    if (components["B_phi"].get("trained_against_global_sha256") != global_hash
            or components["B_phi"].get("trained_against_refiner_sha256") != refiner_hash):
        raise LiteEvaluationError("router checkpoint family mismatch")
    if (components["S_omega"].get("trained_against_global_sha256") != global_hash
            or components["S_omega"].get("trained_against_refiner_sha256") != refiner_hash
            or components["S_omega"].get("trained_against_router_sha256") != router_hash):
        raise LiteEvaluationError("safety checkpoint family mismatch")
    bundle_serialized = json.dumps(
        dict(sorted(hashes.items())), separators=(",", ":")
    )
    bundle_digest = hashlib.sha256(
        bundle_serialized.encode("utf-8")
    ).hexdigest()
    if manifest.get("component_bundle_sha256") != bundle_digest:
        raise LiteEvaluationError("component bundle digest mismatch")
    if (expected_identity == "RA-MedFiLM-BARR (FULL)"
            and hashes != FULL_COMPONENT_SHA256):
        raise LiteEvaluationError("FULL comparison reference checkpoint family mismatch")
    if expected_identity == "RA-MedFiLM-BARR-Lite":
        variant = manifest.get("lite_variant_id")
        architecture_hash = manifest.get("architecture_sha256")
        matched_spec = next(
            (spec for spec in CANDIDATE_SPECS.values() if spec.variant_id == variant),
            None,
        )
        if matched_spec is None or matched_spec.sha256() != architecture_hash:
            raise LiteEvaluationError("Lite architecture identity or digest mismatch")


def _validate_records(
    records: Sequence[Mapping[str, Any]],
    expected_roster: Mapping[str, tuple[str, int]],
    *,
    run_seed: int,
) -> dict[str, Mapping[str, Any]]:
    if set(expected_roster) != {str(sample_id) for sample_id in expected_roster}:
        raise LiteEvaluationError("expected roster sample IDs must be strings")
    expected_counts = {domain: 0 for domain in DOMAINS}
    for domain, task_id in expected_roster.values():
        if domain not in TASK_IDS or TASK_IDS[domain] != task_id:
            raise LiteEvaluationError("expected roster has an invalid domain/task mapping")
        expected_counts[domain] += 1
    if expected_counts != EXPECTED_DOMAIN_COUNTS or len(expected_roster) != 808:
        raise LiteEvaluationError("expected roster must match canonical VAL808 domain counts")
    by_id: dict[str, Mapping[str, Any]] = {}
    for row in records:
        sample_id = str(row.get("sample_id", ""))
        if not sample_id or sample_id in by_id:
            raise LiteEvaluationError("empty or duplicate per-image sample ID")
        if sample_id not in expected_roster:
            raise LiteEvaluationError(f"unexpected validation sample: {sample_id}")
        domain, task_id = expected_roster[sample_id]
        if row.get("domain") != domain or int(row.get("task_id", -1)) != task_id:
            raise LiteEvaluationError(f"domain/task identity mismatch for {sample_id}")
        if row.get("split") != "VAL" or int(row.get("seed", -1)) != run_seed:
            raise LiteEvaluationError(f"split/seed identity mismatch for {sample_id}")
        for key in METRIC_KEYS:
            value = row.get(key)
            if (isinstance(value, bool) or not isinstance(value, (int, float))
                    or not math.isfinite(float(value)) or not 0 <= float(value) <= 1):
                raise LiteEvaluationError(f"invalid {key} for {sample_id}")
        if row.get("router_state") not in {
            "FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT",
        }:
            raise LiteEvaluationError(f"invalid BARR router/safety state for {sample_id}")
        global_dice = row.get("global_dice")
        if (isinstance(global_dice, bool) or not isinstance(global_dice, (int, float))
                or not math.isfinite(float(global_dice)) or not 0 <= float(global_dice) <= 1):
            raise LiteEvaluationError(f"invalid global-only Dice for {sample_id}")
        candidate_dice = row.get("candidate_refinement_dice")
        accepted = row["router_state"] == "EXECUTE_THEN_ACCEPT"
        if accepted:
            if (isinstance(candidate_dice, bool) or not isinstance(candidate_dice, (int, float))
                    or not math.isfinite(float(candidate_dice))
                    or not 0 <= float(candidate_dice) <= 1):
                raise LiteEvaluationError(f"accepted refinement lacks candidate Dice for {sample_id}")
            if not math.isclose(float(candidate_dice), float(row["dice"]), abs_tol=1e-10):
                raise LiteEvaluationError(f"accepted candidate Dice differs from final Dice: {sample_id}")
        elif candidate_dice is not None:
            raise LiteEvaluationError(f"non-accepted case must not report candidate Dice: {sample_id}")
        elif not math.isclose(float(global_dice), float(row["dice"]), abs_tol=1e-10):
            raise LiteEvaluationError(f"non-accepted final Dice differs from global Dice: {sample_id}")
        if not isinstance(row.get("ground_truth_empty"), bool):
            raise LiteEvaluationError(f"ground-truth emptiness flag missing for {sample_id}")
        fp_pixels = row.get("false_positive_pixels")
        if (isinstance(fp_pixels, bool) or not isinstance(fp_pixels, int) or fp_pixels < 0):
            raise LiteEvaluationError(f"invalid false-positive pixel count for {sample_id}")
        if row["ground_truth_empty"] and float(row["dice"]) != 1.0 and fp_pixels == 0:
            raise LiteEvaluationError(f"empty-GT Dice/false-positive inconsistency for {sample_id}")
        hd95 = row.get("hd95")
        reason = row.get("hd95_undefined_reason")
        if hd95 is None:
            if reason not in HD95_UNDEFINED_REASONS:
                raise LiteEvaluationError(f"undefined HD95 lacks valid reason for {sample_id}")
        elif (isinstance(hd95, bool) or not isinstance(hd95, (int, float))
              or not math.isfinite(float(hd95)) or float(hd95) < 0 or reason is not None):
            raise LiteEvaluationError(f"invalid HD95 value/reason for {sample_id}")
        by_id[sample_id] = row
    if set(by_id) != set(expected_roster):
        raise LiteEvaluationError("per-image evaluation roster differs from canonical VAL808")
    return by_id


def aggregate_full_vs_lite(
    full_manifest: Mapping[str, Any],
    full_records: Sequence[Mapping[str, Any]],
    lite_manifest: Mapping[str, Any],
    lite_records: Sequence[Mapping[str, Any]],
    expected_roster: Mapping[str, tuple[str, int]],
) -> dict[str, Any]:
    """Aggregate paired per-image metrics without claiming matched training seeds."""
    _validate_manifest(full_manifest, "RA-MedFiLM-BARR (FULL)")
    _validate_manifest(lite_manifest, "RA-MedFiLM-BARR-Lite")
    full_seed = full_manifest.get("seed")
    lite_seed = lite_manifest.get("seed")
    if full_seed != 42:
        raise LiteEvaluationError("reference FULL bundle must identify canonical seed 42")
    if lite_seed not in LITE_SEEDS:
        raise LiteEvaluationError("Lite seed must be one of 42, 123, 3407")
    full = _validate_records(full_records, expected_roster, run_seed=42)
    lite = _validate_records(lite_records, expected_roster, run_seed=int(lite_seed))

    by_domain: dict[str, list[dict[str, float]]] = defaultdict(list)
    raw_metrics: dict[str, dict[str, dict[str, list[float]]]] = {
        model_key: {domain: {metric: [] for metric in METRIC_KEYS} for domain in DOMAINS}
        for model_key in ("full", "lite")
    }
    differences: list[dict[str, Any]] = []
    for sample_id, expected in expected_roster.items():
        a = full[sample_id]
        b = lite[sample_id]
        if (a["domain"], int(a["task_id"])) != (b["domain"], int(b["task_id"])):
            raise LiteEvaluationError(f"paired domain/task mismatch for {sample_id}")
        if a["ground_truth_empty"] != b["ground_truth_empty"]:
            raise LiteEvaluationError(f"paired ground-truth emptiness mismatch for {sample_id}")
        row_delta = {metric: float(b[metric]) - float(a[metric]) for metric in METRIC_KEYS}
        by_domain[expected[0]].append(row_delta)
        for metric in METRIC_KEYS:
            raw_metrics["full"][expected[0]][metric].append(float(a[metric]))
            raw_metrics["lite"][expected[0]][metric].append(float(b[metric]))
        differences.append({
            "sample_id": sample_id,
            "domain": expected[0],
            "task_id": expected[1],
            **row_delta,
            "full_hd95": a["hd95"],
            "lite_hd95": b["hd95"],
            "full_hd95_undefined_reason": a["hd95_undefined_reason"],
            "lite_hd95_undefined_reason": b["hd95_undefined_reason"],
            "hd95_lite_minus_full": (
                float(b["hd95"]) - float(a["hd95"])
                if a["hd95"] is not None and b["hd95"] is not None else None
            ),
        })
    if set(by_domain) != set(DOMAINS):
        raise LiteEvaluationError("paired evaluation must contain all four domains")
    per_domain = {
        domain: {
            metric: sum(row[metric] for row in by_domain[domain]) / len(by_domain[domain])
            for metric in METRIC_KEYS
        }
        for domain in DOMAINS
    }
    per_domain_metrics: dict[str, dict[str, Any]] = {}
    for domain in DOMAINS:
        per_domain_metrics[domain] = {}
        for metric in METRIC_KEYS:
            full_values = raw_metrics["full"][domain][metric]
            lite_values = raw_metrics["lite"][domain][metric]
            per_domain_metrics[domain][metric] = {
                "full": sum(full_values) / len(full_values),
                "lite": sum(lite_values) / len(lite_values),
                "lite_minus_full": per_domain[domain][metric],
            }
        full_hd95_values = [
            float(full[sample_id]["hd95"])
            for sample_id, (case_domain, _) in expected_roster.items()
            if case_domain == domain and full[sample_id]["hd95"] is not None
        ]
        lite_hd95_values = [
            float(lite[sample_id]["hd95"])
            for sample_id, (case_domain, _) in expected_roster.items()
            if case_domain == domain and lite[sample_id]["hd95"] is not None
        ]
        paired_hd95_deltas = [
            float(row["hd95_lite_minus_full"]) for row in differences
            if row["domain"] == domain and row["hd95_lite_minus_full"] is not None
        ]
        per_domain_metrics[domain]["hd95_pixels"] = {
            "full": sum(full_hd95_values) / len(full_hd95_values) if full_hd95_values else None,
            "lite": sum(lite_hd95_values) / len(lite_hd95_values) if lite_hd95_values else None,
            "full_n_defined": len(full_hd95_values),
            "lite_n_defined": len(lite_hd95_values),
            "paired_n_defined": len(paired_hd95_deltas),
            "mean_paired_lite_minus_full": (
                sum(paired_hd95_deltas) / len(paired_hd95_deltas)
                if paired_hd95_deltas else None
            ),
        }
    outcome_summary: dict[str, dict[str, int]] = {}
    for model_key, records in (("full", full), ("lite", lite)):
        states = [row["router_state"] for row in records.values()]
        accepted_rows = [
            row for row in records.values()
            if row["router_state"] == "EXECUTE_THEN_ACCEPT"
        ]
        outcome_summary[model_key] = {
            "all_cases": len(records),
            "routed_accepted": len(accepted_rows),
            "routed_rejected": sum(
                state == "EXECUTE_THEN_REJECT" for state in states
            ),
            "router_skipped_or_unavailable": sum(
                state in {"SKIP_GLOBAL", "FORCED_SKIP"} for state in states
            ),
            "accepted_beneficial": sum(
                float(row["candidate_refinement_dice"]) > float(row["global_dice"])
                for row in accepted_rows
            ),
            "accepted_harmful": sum(
                float(row["candidate_refinement_dice"]) < float(row["global_dice"])
                for row in accepted_rows
            ),
            "accepted_tied": sum(
                float(row["candidate_refinement_dice"]) == float(row["global_dice"])
                for row in accepted_rows
            ),
            "empty_ground_truth_cases": sum(
                row["ground_truth_empty"] for row in records.values()
            ),
            "empty_ground_truth_false_positive_cases": sum(
                row["ground_truth_empty"] and int(row["false_positive_pixels"]) > 0
                for row in records.values()
            ),
        }
    return {
        "status": "DESCRIPTIVE_PAIRED_SECONDARY_EVALUATION",
        "full_model_identity": "RA-MedFiLM-BARR (FULL)",
        "lite_model_identity": "RA-MedFiLM-BARR-Lite",
        "full_seed": 42,
        "lite_seed": int(lite_seed),
        "training_seed_pairing": "UNMATCHED_REFERENCE: fixed FULL seed 42 versus Lite seed",
        "population": "phase4_v3_VAL808",
        "selection_status": "selection-consumed validation; not independent generalization",
        "external_generalization_status": (
            "NOT_ESTABLISHED; no Lite external inference performed and historical FULL "
            "external results cannot be paired with this variant"
        ),
        "n_paired_samples": len(differences),
        "per_domain_metrics": per_domain_metrics,
        "per_domain_mean_lite_minus_full": per_domain,
        "router_safety_failure_summary": outcome_summary,
        "equal_domain_macro_differences": {
            metric: sum(per_domain[domain][metric] for domain in DOMAINS) / len(DOMAINS)
            for metric in METRIC_KEYS
        },
        "per_image_paired_differences": differences,
        "inferential_claims": "none; report descriptive paired differences only",
    }


def pareto_frontier(summaries: Sequence[Mapping[str, Any]]) -> list[str]:
    """Return non-dominated model IDs for higher Dice and lower resource costs."""
    required = ("model_key", "equal_domain_macro_dice", "parameters", "gmacs",
                "latency_ms_p50", "evidence_status", "synthetic_only",
                "latency_device_fingerprint", "latency_batch_size")
    rows: list[dict[str, Any]] = []
    for summary in summaries:
        if any(key not in summary for key in required):
            raise LiteEvaluationError("Pareto input is missing an accuracy or cost field")
        if (summary["evidence_status"] != "CONFIRMED_EXECUTED_RESULT"
                or summary["synthetic_only"] is not False):
            raise LiteEvaluationError("synthetic or unconfirmed accuracy cannot enter Pareto analysis")
        if summary["latency_batch_size"] != 1:
            raise LiteEvaluationError("Pareto latency comparisons require batch size one")
        values = [summary["equal_domain_macro_dice"], summary["parameters"],
                  summary["gmacs"], summary["latency_ms_p50"]]
        if any(not isinstance(value, (int, float)) or not math.isfinite(float(value))
               for value in values):
            raise LiteEvaluationError("Pareto inputs must contain finite measured values")
        if not 0 <= float(values[0]) <= 1 or any(float(value) <= 0 for value in values[1:]):
            raise LiteEvaluationError("Pareto metrics/costs are outside their valid range")
        rows.append(dict(summary))
    devices = {row["latency_device_fingerprint"] for row in rows}
    if len(devices) != 1 or not next(iter(devices)):
        raise LiteEvaluationError("Pareto latency measurements must share a hardware fingerprint")
    frontier = []
    for candidate in rows:
        dominated = any(
            other["model_key"] != candidate["model_key"]
            and other["equal_domain_macro_dice"] >= candidate["equal_domain_macro_dice"]
            and other["parameters"] <= candidate["parameters"]
            and other["gmacs"] <= candidate["gmacs"]
            and other["latency_ms_p50"] <= candidate["latency_ms_p50"]
            and any((
                other["equal_domain_macro_dice"] > candidate["equal_domain_macro_dice"],
                other["parameters"] < candidate["parameters"],
                other["gmacs"] < candidate["gmacs"],
                other["latency_ms_p50"] < candidate["latency_ms_p50"],
            ))
            for other in rows
        )
        if not dominated:
            frontier.append(str(candidate["model_key"]))
    return frontier
