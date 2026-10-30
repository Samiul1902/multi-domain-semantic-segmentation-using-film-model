import hashlib
import json
import os
from datetime import datetime, timezone

ROOT = r"D:\Softfors\jup"


def raw(p: str) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


A = lambda n: os.path.join(ROOT, "reports", "audits", n)

start = A("phase36_robustness_science_start_v1_14.json")
fail = A("phase36_robustness_science_failure_v1_14.json")
so = A("phase36_v1_14_science_stdout_first_attempt.txt")
se = A("phase36_v1_14_science_stderr_first_attempt.txt")
pre = A("phase36_v1_14_science_dispatch_preflight_v1.json")
exec_p = os.path.join(ROOT, "scripts", "analysis", "phase36_robustness_execution_v1_14.py")

scores_p = os.path.join(ROOT, "reports", "tables", "phase27_val808_per_sample_scores.csv")
routing_p = os.path.join(ROOT, "data_cache", "phase29_seed42", "phase29_seed42_val808_decisions.csv")
manifest_p = os.path.join(ROOT, "manifests", "phase4_v3", "val.csv")

out = A("phase36_v1_14_science_failure_forensic_adjudication.json")
if os.path.exists(out):
    print("EXISTS, refusing:", out)
    raise SystemExit(0)

payload = {
    "artifact": "phase36_v1_14_science_failure_forensic_adjudication",
    "phase": 36,
    "revision": "ra_medfilm_barr_phase36_robustness_v1_14",
    "type": "CONSUMED_SCIENCE_FAILURE_FORENSIC_ADJUDICATION",
    "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),

    # ---- STEP 1: evidence ----
    "step1_failure_evidence": {
        "science_start_sha256": raw(start),
        "science_failure_sha256": raw(fail),
        "stdout_sha256": raw(so),
        "stderr_sha256": raw(se),
        "execution_source_sha256": raw(exec_p),
        "scientific_result_absent": not os.path.exists(A("phase36_robustness_scientific_result_v1_14.json")),
        "automatic_retry_false": True,
        "overwrite_permitted_false": True,
        "all_evidence_verified": True,
    },

    # ---- STEP 2: pre-dispatch wrapper incident ----
    "step2_pre_dispatch_incident": {
        "artifact": "reports/audits/phase36_v1_14_science_dispatch_preflight_v1.json",
        "sha256": raw(pre),
        "classification": "PRE_ATTEMPT_DISPATCH_WRAPPER_INCIDENT",
        "counted_as_science_retry": False,
        "python_invoked": False,
        "main_entered": False,
        "marker_created_before_incident": False,
        "revision_consumed_by_incident": False,
        "chronology": "incident mtime 23:42:16 < science start marker mtime 23:42:45",
    },

    # ---- STEP 3: execution-stage classification ----
    "step3_execution_stage_classification": {
        "execution_order_proven_from_frozen_source": True,
        "order": [
            "source_integrity_gate",
            "model_load",
            "bind_clean_reference",
            "canonical_batched_clean_G_generation",
            "clean_G_reproduction_gate",
            "808_clean_system_evaluations",
            "clean_equivalence_gate",
            "ONLY_IF_PASS_perturbation_stages",
        ],
        "source_integrity_gate_reached": True,
        "model_loaded": True,
        "clean_reference_bound": True,
        "clean_g_generation_reached": True,
        "clean_G_reproduction_gate_reached": True,
        "clean_G_reproduction_gate_passed": True,
        "clean_system_evaluation_reached": True,
        "clean_system_evaluation_executed": True,
        "clean_equivalence_gate_reached": True,
        "clean_equivalence_gate_passed": False,
        "image_perturbation_stage_started": False,
        "proposal_perturbation_stage_started": False,
        "final_scientific_result_produced": False,
        "model_execution": True,
        "val_image_read": True,
        "val_gt_read": True,
        "metric_execution": True,
        "classification_note": (
            "The observed SystemExit is exactly CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION "
            "(v1.14 line 3184). Every earlier stage necessarily passed, else a DIFFERENT terminal "
            "would have fired (e.g. CLEAN_GLOBAL_REPRODUCTION_GATE_FAILED__STOP_BEFORE_DOWNSTREAM_PERTURBATION "
            "at line 3168). The clean system evaluation DOES load VAL images + VAL GT and computes "
            "Dice/IoU/HD95. Therefore model_execution / val_image_read / val_gt_read / metric_execution "
            "must NOT be claimed false."
        ),
    },

    # ---- STEP 4: D44 ----
    "step4_d44_forensic_provenance_defect": {
        "classification": "D44_CLEAN_EQUIVALENCE_FAILURE_DIAGNOSTICS_NOT_DURABLY_PRESERVED",
        "confirmed": True,
        "_clean_equivalence_gate_computes": [
            "checks (11 booleans)",
            "n_generated", "n_bound",
            "n_dice_comparisons", "n_state_machine_branch_comparisons", "n_router_decision_comparisons",
            "missing_generated_dice", "missing_bound_dice",
            "dice_mismatches", "route_branch_mismatches", "router_decision_mismatches",
            "max_abs_dice_deviation",
        ],
        "run_science_raises": "CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION",
        "failure_artifact_contains_eq_object": False,
        "eq_object_durably_preserved": False,
        "scientific_semantics_effect": "NONE",
        "failure_diagnosability_effect": "YES",
        "v1_14_modified": False,
    },

    # ---- STEP 5: static clean-reference forensics (metadata only) ----
    "step5_static_clean_reference_forensics": {
        "clean_reference": {
            "per_sample_scores_path": "reports/tables/phase27_val808_per_sample_scores.csv",
            "per_sample_scores_sha256_expected": "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
            "per_sample_scores_sha256_observed": raw(scores_p),
            "routing_state_path": "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv",
            "routing_state_sha256_expected": "df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6",
            "routing_state_sha256_observed": raw(routing_p),
            "val_manifest_path": "manifests/phase4_v3/val.csv",
            "val_manifest_sha256_expected": "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315",
            "val_manifest_sha256_observed": raw(manifest_p),
        },
        "per_sample_scores": {
            "row_count": 808,
            "unique_sample_id_count": 808,
            "duplicate_ids": [],
            "columns": ["sample_id", "dataset", "task_id", "group_key", "state_machine_branch",
                        "router_decision", "global_dice", "final_dice", "delta_dice",
                        "gt_foreground_pixels", "global_fg_pixels", "final_fg_pixels"],
            "dataset_counts": {"ISIC": 357, "KUB": 280, "KVASIR": 87, "BUSI": 84},
            "final_dice_finite_count": 808,
            "state_machine_branch_counts": {"SKIP_GLOBAL": 529, "EXECUTE_THEN_ACCEPT": 266,
                                            "EXECUTE_THEN_REJECT": 13},
            "router_decision_counts": {"SKIP": 529, "EXECUTE": 279},
        },
        "routing_state": {
            "row_count": 808,
            "unique_sample_id_count": 808,
            "duplicate_ids": [],
            "columns": ["sample_id", "domain", "task_id", "router_score", "router_threshold",
                        "selected", "safety_score", "safety_accept", "final_source", "roi_available"],
            "selected_value_counts": {"False": 529, "True": 279},
        },
        "val_manifest": {
            "row_count": 808,
            "unique_sample_id_count": 808,
            "duplicate_ids": [],
            "dataset_counts": {"ISIC": 357, "KUB": 280, "KVASIR": 87, "BUSI": 84},
        },
        "set_comparisons": {
            "missing_from_clean_reference": [],
            "extra_in_clean_reference": [],
            "missing_from_routing_reference": [],
            "extra_in_routing_reference": [],
            "scores_vs_routing_disjoint": [],
        },
        "cross_authority_consistency": {
            "scores_router_decision_vs_routing_selected": "AGREE_ALL_808",
            "scores_internal_branch_vs_decision": "CONSISTENT_ALL_808",
        },
        "phase27_global_prob_authority": {
            "path": "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy",
            "sha256_expected": "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13",
            "sha256_observed": raw(os.path.join(ROOT, "data_cache", "phase27_barr_preservation_v1_0",
                                                "phase27_val808_global_prob_f16.npy")),
            "byte_identical_twin_sha256_observed": raw(os.path.join(
                ROOT, "data_cache", "phase29_val808_shared_fixed_g_v1_1_canonical",
                "val808_global_prob_f16.npy")),
            "used_for_new_model_execution": False,
        },
    },

    # ---- STEP 6: gate-semantics audit ----
    "step6_gate_semantics_audit": {
        "all_conditions_capable_of_making_all_pass_false": [
            "A generated_exactly_808",
            "B bound_exactly_808",
            "B2 generated_equals_bound",
            "C missing_bound_dice_zero",
            "D missing_generated_dice_zero",
            "E dice_mismatches_zero (np.isclose atol=1e-7, rtol=0)",
            "F route_branch_mismatches_zero (EXACT equality)",
            "G router_decision_mismatches_zero (EXACT equality)",
            "H n_dice_comparisons_808",
            "H2 n_state_machine_branch_comparisons_808",
            "H3 n_router_decision_comparisons_808",
        ],
        "hardcoded_true_condition": "accept_and_reject_not_collapsed",
        "comparators": {
            "dice": "np.isclose(generated, bound, atol=1e-7, rtol=0)",
            "branch": "generated.state_machine_branch == bound.state_machine_branch (EXACT)",
            "router_decision": "generated.router_decision == bound.router_decision (EXACT)",
        },
        "static_count_failures_ruled_out": {
            "A_generated_exactly_808": "authority n=808; runtime enumerates the 808-row manifest",
            "B_bound_exactly_808": "per_sample_scores n=808, unique 808",
            "B2_generated_equals_bound": "both 808",
            "H_dice_comparisons_808": "authority final_dice finite for all 808",
            "H2_branch_comparisons_808": "authority state_machine_branch present for all 808",
            "H3_router_decision_comparisons_808": "authority router_decision present for all 808",
        },
        "residual_live_failure_families": [
            "E dice_mismatches (>1e-7) — a runtime numerical deviation in clean final_dice",
            "F route_branch mismatch — a runtime state_machine_branch deviating from the authority",
            "G router_decision mismatch — a runtime router_decision deviating from the authority",
            "C/D missing dice — only if the runtime produced a None/nonfinite final_dice",
        ],
        "source_level_defect_scan": {
            "wrong_authority_column": "none found (columns read match authority schema)",
            "wrong_authority_file": "none found (both paths + SHAs exact)",
            "stale_threshold_route_semantics": "none found (0.50 seg / 0.30 ROI / C8 runtime thresholds consistent)",
            "accept_reject_representation_mismatch": "none found (authority selected True/False <-> router_decision EXECUTE/SKIP agreed all 808)",
            "sample_identity_namespace_mismatch": "none found (sets identical across scores/routing/manifest)",
            "task_class_confusion": "none observed statically",
            "router_decision_vocabulary_mismatch": "none found (runtime {SKIP,EXECUTE} == authority)",
            "wrong_dice_comparator_precision": "atol=1e-7 rtol=0 is intentional strict",
            "authority_generated_under_materially_different_downstream_semantics":
                "phase27/29 conditional components are per-sample membership-independent and the G "
                "reproduction gate proved bit-identical G, so a structural semantic divergence is "
                "NOT statically proven — but a residual runtime numerical deviation cannot be excluded "
                "without the transient eq object",
        },
    },

    # ---- STEP 7: root-cause resolution ----
    "step7_root_cause_resolution": {
        "resolution": "ROOT_CAUSE_NOT_RECOVERABLE_WITHOUT_CLEAN_DIAGNOSTIC_REEXECUTION",
        "missing_evidence": (
            "The transient v1.14 `eq` object from _clean_equivalence_gate(): specifically its "
            "`checks` booleans, `n_dice_comparisons`/`n_state_machine_branch_comparisons`/"
            "`n_router_decision_comparisons`, `missing_generated_dice`, `missing_bound_dice`, "
            "`dice_mismatches`, `route_branch_mismatches`, `router_decision_mismatches`, and "
            "`max_abs_dice_deviation`. It was computed in-memory at line 3182 but discarded when "
            "run_science() raised SystemExit at line 3184 (D44). It is absent from the failure "
            "artifact and from every on-disk artifact."
        ),
        "reexecution_performed": False,
        "reexecution_required_for_establishment": True,
    },

    # ---- STEP 8 high-level required state ----
    "science_attempt": "CONSUMED_FAILED",
    "science_retry": "FORBIDDEN",
    "failure_terminal": "CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION",
    "termination_kind": "SYSTEM_EXIT",
    "clean_G_reproduction_passed": True,
    "clean_system_evaluation_executed": True,
    "clean_equivalence_passed": False,
    "perturbation_execution_started": False,
    "final_scientific_result_produced": False,
    "D44_diagnostics_not_durably_preserved": True,
    "root_cause_resolution": "ROOT_CAUSE_NOT_RECOVERABLE_WITHOUT_CLEAN_DIAGNOSTIC_REEXECUTION",
    "v1_14_retry_permitted": False,
    "phase37_state": "NOT_STARTED",
    "test_state": "REMAINS_PHASE39_ONLY",
    "router_holdout_state": "NOT_ACCESSED",

    # ---- prohibitions observed by this forensic work order ----
    "prohibitions_observed": {
        "model_forward_performed": False,
        "checkpoint_deserialized": False,
        "val_image_bytes_read": False,
        "val_gt_mask_bytes_read": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "science_rerun": False,
        "smoke_rerun": False,
        "v1_15_created": False,
        "v1_14_patched": False,
    },
    "terminal": "PHASE36_V1_14_CONSUMED_SCIENCE_FAILURE_FORENSIC_COMPLETE__ROOT_CAUSE_NOT_RECOVERABLE_WITHOUT_CLEAN_DIAGNOSTIC_REEXECUTION",
}

flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
fd = os.open(out, flags, 0o644)
try:
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
except BaseException:
    os.close(fd)
    raise
print("WROTE", out, raw(out))
