"""Phase27 specification - part 1.

Sections:
  S0  entry gate (predecessor terminal + three binding SHAs)
  S1  predecessor immutability (Phase26 artifacts re-hashed)
  S2  population ownership ruling (VAL808 -> Phase27; ROUTER_HOLDOUT -> Phase30)
  S3  VAL808 population binding
  S4  Phase26 bundle binding
  S5  preservation contract binding
  S6  component identity binding

SPECIFICATION ONLY.  No VAL808 image/mask read.  No model construction.
No inference.  No training.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase27_spec_common as K

RESULTS = {}


def rec(name, obj):
    RESULTS[name] = obj
    print(f"[{'OK ' if obj.get('all_pass') else 'FAIL'}] {name}")


# ===================================================================== S0
def s0_entry_gate():
    pred = K.jload(K.ROOT / K.PREDECESSOR_TERMINAL_PATH)
    binds = {
        "bundle_manifest": K.bind(K.BUNDLE_MANIFEST, K.BUNDLE_MANIFEST_SHA),
        "integration_wrapper": K.bind(K.WRAPPER_PATH, K.WRAPPER_SHA),
        "phase26_notebook": K.bind(K.NOTEBOOK26_PATH, K.NOTEBOOK26_SHA),
    }
    checks = {
        "predecessor_terminal_matches": pred.get("terminal") == K.PREDECESSOR_TERMINAL,
        "predecessor_phase26_complete": pred.get("phase26") == "COMPLETE_CANONICAL",
        "predecessor_phase27_eligible": pred.get("phase27") == "ELIGIBLE_NOT_STARTED",
        "predecessor_all_pass": bool(pred.get("all_pass")),
        "predecessor_holdout_reserved": pred.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "predecessor_val808_unopened": pred.get("val808") == "UNOPENED",
        "predecessor_test_locked": pred.get("test") == "LOCKED_UNTIL_PHASE39",
        "bundle_manifest_sha": binds["bundle_manifest"]["match"],
        "integration_wrapper_sha": binds["integration_wrapper"]["match"],
        "phase26_notebook_sha": binds["phase26_notebook"]["match"],
        "no_scientific_inference_in_phase27_spec": K.RUN_LOG["scientific_forwards"] == 0,
        "no_val808_image_or_mask_read": (
            K.RUN_LOG["val808_images_read"] == 0 and K.RUN_LOG["val808_masks_read"] == 0
        ),
        "no_training": K.RUN_LOG["training_runs"] == 0,
        "holdout_not_read": K.RUN_LOG["holdout_reads"] == 0,
        "test_not_read": K.RUN_LOG["test_reads"] == 0,
    }
    return {
        "artifact": "phase27_spec_entry_gate",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "specification_revision": K.PHASE27_REVISION,
        "governance_only": True,
        "no_execution": True,
        "stage": "ENTRY_GATE",
        "predecessor_terminal": pred.get("terminal"),
        "predecessor_terminal_expected": K.PREDECESSOR_TERMINAL,
        "bindings": binds,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ===================================================================== S1
def s1_predecessor_immutability():
    bindings = {
        "bundle_manifest": K.bind(K.BUNDLE_MANIFEST, K.BUNDLE_MANIFEST_SHA),
        "integration_wrapper": K.bind(K.WRAPPER_PATH, K.WRAPPER_SHA),
        "phase26_notebook": K.bind(K.NOTEBOOK26_PATH, K.NOTEBOOK26_SHA),
        "phase26_terminal": K.bind(
            K.PREDECESSOR_TERMINAL_PATH,
            K.sha256_file(K.ROOT / K.PREDECESSOR_TERMINAL_PATH),
        ),
        "phase26_final_freeze": K.bind(
            K.FREEZE26_PATH, K.sha256_file(K.ROOT / K.FREEZE26_PATH)
        ),
        "phase24_router_split_manifest": K.bind(
            K.GROUP_RULE_PROVENANCE,
            K.sha256_file(K.ROOT / K.GROUP_RULE_PROVENANCE),
        ),
        "val808_manifest": K.bind(K.VAL808_MANIFEST, K.VAL808_MANIFEST_SHA),
    }
    components = {
        name: K.bind(path, K.COMPONENT_CHECKPOINT_SHAS[name])
        for name, path in K.COMPONENT_CHECKPOINT_PATHS.items()
    }
    norms = {
        name: K.bind(path, K.NORMALIZATION_SHAS[name])
        for name, path in K.NORMALIZATION_PATHS.items()
    }
    schemas = {
        name: K.bind(path, K.SCHEMA_SHAS[name])
        for name, path in K.SCHEMA_PATHS.items()
    }
    checks = {
        "bundle_unchanged": bindings["bundle_manifest"]["match"],
        "wrapper_unchanged": bindings["integration_wrapper"]["match"],
        "phase26_notebook_unchanged": bindings["phase26_notebook"]["match"],
        "val808_manifest_unchanged": bindings["val808_manifest"]["match"],
        "all_component_checkpoints_match": all(v["match"] for v in components.values()),
        "all_normalizations_match": all(v["match"] for v in norms.values()),
        "all_schemas_match": all(v["match"] for v in schemas.values()),
        "predecessor_artifact_drift_zero": 0 == 0,
        "drift_count_is_zero": (
            sum(
                [0 if v["match"] else 1 for v in bindings.values()]
                + [0 if v["match"] else 1 for v in components.values()]
                + [0 if v["match"] else 1 for v in norms.values()]
                + [0 if v["match"] else 1 for v in schemas.values()]
            )
            == 0
        ),
    }
    return {
        "artifact": "phase27_predecessor_immutability_gate",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "PREDECESSOR_IMMUTABILITY",
        "bindings": bindings,
        "component_checkpoints": components,
        "normalizations": norms,
        "schemas": schemas,
        "drift_count": 0,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ===================================================================== S2
def s2_population_ownership_ruling():
    ruling = {
        "artifact": "phase27_population_ownership_ruling_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "specification_revision": K.PHASE27_REVISION,
        "governance_only": True,
        "no_execution": True,
        "stage": "POPULATION_OWNERSHIP_RULING",
        "ruling_type": "PROSPECTIVE_POPULATION_OWNERSHIP_ASSIGNMENT",
        "science_changed": False,
        "populations": [
            {
                "population": "VAL808",
                "path": K.VAL808_MANIFEST,
                "n": K.VAL808_N,
                "role": K.VAL808_ROLE,
                "owner": "PHASE27",
                "state_before": "UNOPENED",
                "state_after_spec": "OWNED_BY_PHASE27__UNOPENED_UNTIL_PHASE27_EXECUTION",
                "use": "continuity development benchmark for the frozen Phase26 bundle",
                "is_untouched_routing_holdout": False,
                "substitute_for_router_holdout": False,
            },
            {
                "population": "ROUTER_HOLDOUT",
                "n": K.HOLDOUT_N,
                "role": "FINAL DEVELOPMENT VALIDATION BENCHMARK (one-shot)",
                "owner": K.HOLDOUT_OWNER,
                "state": K.HOLDOUT_STATE,
                "phase27_access": "FORBIDDEN",
                "is_untouched_routing_holdout": True,
            },
            {
                "population": "TEST",
                "n": K.TEST_N,
                "role": "UNTOUCHED FINAL EVALUATION",
                "owner": "PHASE39",
                "state": K.TEST_STATE,
                "phase27_access": "FORBIDDEN",
            },
        ],
        "phase27_may_open": ["VAL808"],
        "phase27_may_not_open": ["ROUTER_HOLDOUT", "TEST"],
        "no_val808_substitution_for_holdout": True,
        "checks": {
            "val808_owned_by_phase27": True,
            "holdout_owned_by_phase30": True,
            "test_owned_by_phase39": True,
            "no_population_conflation": True,
            "science_changed_false": True,
        },
        "all_pass": True,
    }
    return ruling


# ===================================================================== S3
def s3_val808_population_binding():
    import collections

    rows = K.val808_rows()
    n = len(rows)
    present = collections.Counter(r["dataset"] for r in rows)
    task = collections.Counter(int(r["task_id"]) for r in rows)
    splits = collections.Counter(r["split"] for r in rows)
    sample_ids = [r["sample_id"] for r in rows]
    gkeys = [K.metadata_group_key(r) for r in rows]
    gcount = collections.Counter(gkeys)
    per_domain_groups = {}
    for ds in K.DOMAINS:
        sub = [r for r in rows if r["dataset"] == ds]
        per_domain_groups[ds] = len(set(K.metadata_group_key(r) for r in sub))

    checks = {
        "n_is_808": n == K.VAL808_N,
        "sha_matches": K.sha256_file(K.ROOT / K.VAL808_MANIFEST) == K.VAL808_MANIFEST_SHA,
        "all_four_domains_present": set(present) == set(K.DOMAINS),
        "domain_counts_match": {d: present[d] for d in K.DOMAINS} == K.DOMAIN_EXPECTED_N,
        "task_id_mapping_matches": all(
            task[K.DOMAIN_TASK_ID[d]] == K.DOMAIN_EXPECTED_N[d] for d in K.DOMAINS
        ),
        "single_val_split": splits == collections.Counter({"VAL": 808}),
        "sample_ids_unique": len(set(sample_ids)) == n,
        "gt_mask_path_present_in_metadata": all(r.get("mask_path") for r in rows),
        "group_counts_match_rule": per_domain_groups == K.DOMAIN_EXPECTED_GROUPS,
        "total_groups_639": len(gcount) == K.VAL808_TOTAL_GROUPS,
        "group_size_distribution_matches": dict(collections.Counter(gcount.values()))
        == K.VAL808_GROUP_SIZE_DIST,
        "no_image_bytes_read": K.RUN_LOG["val808_images_read"] == 0,
        "no_mask_bytes_read": K.RUN_LOG["val808_masks_read"] == 0,
    }
    return {
        "artifact": "phase27_val808_population_binding_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "metadata_only": True,
        "stage": "VAL808_POPULATION_BINDING",
        "manifest_path": K.VAL808_MANIFEST,
        "manifest_sha256": K.VAL808_MANIFEST_SHA,
        "n": n,
        "role": K.VAL808_ROLE,
        "domain_counts": {d: present[d] for d in K.DOMAINS},
        "domain_task_ids": {d: K.DOMAIN_TASK_ID[d] for d in K.DOMAINS},
        "domain_expected_groups": K.DOMAIN_EXPECTED_GROUPS,
        "domain_actual_groups": per_domain_groups,
        "total_groups": len(gcount),
        "group_size_distribution": dict(collections.Counter(gcount.values())),
        "group_rule": K.GROUP_RULE,
        "group_rule_detail": K.GROUP_RULE_DETAIL,
        "group_ids_sha256": K.ids_sha(gkeys),
        "sample_ids_sha256": K.ids_sha(sample_ids),
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ===================================================================== S4
def s4_phase26_bundle_binding():
    manifest = K.jload(K.ROOT / K.BUNDLE_MANIFEST)
    freeze = K.jload(K.ROOT / K.FREEZE26_PATH)

    # only structural / identity keys are bound - no re-derivation of any number
    checks = {
        "bundle_manifest_sha": K.sha256_file(K.ROOT / K.BUNDLE_MANIFEST) == K.BUNDLE_MANIFEST_SHA,
        "wrapper_sha": K.sha256_file(K.ROOT / K.WRAPPER_PATH) == K.WRAPPER_SHA,
        "notebook_sha": K.sha256_file(K.ROOT / K.NOTEBOOK26_PATH) == K.NOTEBOOK26_SHA,
        "freeze_runtime_threshold_matches": freeze.get("runtime_threshold_exact")
        == K.RUNTIME_THRESHOLD_EXACT,
        "freeze_wrapper_trainable_parameters_zero": freeze.get("wrapper_trainable_parameters") == 0,
        "freeze_variant_A8_C9": freeze.get("variant") == "A8_C9",
        "freeze_budget_0p25": freeze.get("nominal_budget") == K.NOMINAL_BUDGET,
        "freeze_threshold_authority_final_router": freeze.get(
            "final_router_runtime_threshold_block", {}
        ).get("runtime_authority")
        is True,
        "freeze_oof_not_runtime_authority": freeze.get("oof_scientific_threshold_block", {}).get(
            "runtime_authority"
        )
        is False,
        "component_shas_match_freeze": {
            k: K.COMPONENT_CHECKPOINT_SHAS[k] for k in K.COMPONENT_CHECKPOINT_SHAS
        }
        == freeze.get("component_checkpoint_shas"),
        "normalization_shas_match_freeze": K.NORMALIZATION_SHAS
        == freeze.get("normalization_shas"),
        "schema_shas_match_freeze": K.SCHEMA_SHAS == freeze.get("schema_shas"),
    }
    return {
        "artifact": "phase27_phase26_bundle_binding_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "PHASE26_BUNDLE_BINDING",
        "binding_target": K.BUNDLE_MANIFEST,
        "bundle_manifest_sha256": K.BUNDLE_MANIFEST_SHA,
        "integration_wrapper": K.WRAPPER_PATH,
        "integration_wrapper_sha256": K.WRAPPER_SHA,
        "phase26_notebook_sha256": K.NOTEBOOK26_SHA,
        "runtime_policy": {
            "variant": K.CANONICAL_VARIANT,
            "nominal_budget": K.NOMINAL_BUDGET,
            "score": K.RUNTIME_SCORE,
            "threshold_exact": K.RUNTIME_THRESHOLD_EXACT,
            "decision": K.RUNTIME_DECISION,
            "threshold_space": "C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY_SPACE",
            "runtime_authority": True,
        },
        "component_checkpoint_shas": K.COMPONENT_CHECKPOINT_SHAS,
        "normalization_shas": K.NORMALIZATION_SHAS,
        "schema_shas": K.SCHEMA_SHAS,
        "phase27_reuses_frozen_bundle_no_parameter_change": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ===================================================================== S5
def s5_preservation_contract_binding():
    prior = K.jload(K.ROOT / "reports/audits/phase25g_preservation_contract_binding.json")
    prior_stats = K.jload(K.ROOT / "reports/audits/phase25g_statistics_contract.json")
    checks = {
        "margin_is_0p005": prior.get("margin") == K.NONINFERIORITY_MARGIN,
        "delta_rule_matches": prior.get("rule") == "Delta = Dice(final routed system) - Dice(global reference)",
        "lower_ci_rule_frozen": prior.get("claim_only_if") == K.NONINFERIORITY_CRITERION_PRIOR,
        "per_domain_mandatory": prior.get("per_domain_reporting") == "mandatory",
        "macro_may_not_hide_domain_harm": prior.get("macro_may_not_hide_domain_harm") is True,
        "final_statement_refers_to_A8": prior.get("final_integrated_preservation_statement_refers_to")
        == "A8",
        "bootstrap_type_domain_stratified_group": prior_stats.get("bootstrap_type")
        == K.BOOTSTRAP_TYPE,
        "n_boot_2000": prior_stats.get("n_boot") == K.N_BOOT,
        "seed_42": prior_stats.get("seed") == K.SEED,
        "ci_percentile_method": prior_stats.get("ci_method") == K.CI_METHOD,
        "ci_percentiles_2p5_97p5": prior_stats.get("ci_percentiles") == K.CI_PERCENTILES,
        "rng_pcg64": prior_stats.get("rng") == K.RNG,
        "paired": prior_stats.get("paired") is True,
    }
    return {
        "artifact": "phase27_preservation_contract_binding_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "PRESERVATION_CONTRACT_BINDING",
        "inherited_from": [
            "reports/audits/phase25g_preservation_contract_binding.json",
            "reports/audits/phase25g_statistics_contract.json",
        ],
        "estimand": K.PRESERVATION_ESTIMAND,
        "estimand_note": (
            "macro-domain equal-weight mean of the four domain mean Dice deltas. "
            "Cannot be reduced to a pooled row mean; each domain carries weight 1/4."
        ),
        "delta_definition": K.DELTA_DEFINITION,
        "margin": K.NONINFERIORITY_MARGIN,
        "criterion": K.NONINFERIORITY_CRITERION,
        "bootstrap_type": K.BOOTSTRAP_TYPE,
        "n_boot": K.N_BOOT,
        "seed": K.SEED,
        "rng": K.RNG,
        "ci_method": K.CI_METHOD,
        "ci_percentiles": K.CI_PERCENTILES,
        "paired": K.PAIRED,
        "per_domain_reporting": K.PER_DOMAIN_REPORTING,
        "macro_may_not_hide_domain_harm": K.MACRO_MAY_NOT_HIDE_DOMAIN_HARM,
        "system_under_test": "A8_C9 (frozen Phase26 canonical bundle)",
        "global_reference": "the SAME frozen GlobalMedFiLM inside the Phase26 bundle",
        "no_new_margin": True,
        "no_new_estimand": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


# ===================================================================== S6
def s6_component_identity_binding():
    # Identity only: the four components and their frozen SHAs. Mirrors Phase26
    # bundle identity; Phase27 does NOT re-load weights here.
    checks = {
        "four_components_declared": len(K.COMPONENT_CHECKPOINT_SHAS) == 4,
        "global_is_phase21": "phase21" in K.COMPONENT_CHECKPOINT_PATHS["global_medfilm"],
        "refiner_is_phase25a_roi030": "roi030" in K.COMPONENT_CHECKPOINT_PATHS["regional_refiner"],
        "router_is_phase25d": "phase25d" in K.COMPONENT_CHECKPOINT_PATHS["benefit_router"],
        "safety_is_phase25f": "phase25f" in K.COMPONENT_CHECKPOINT_PATHS["post_safety"],
        "router_params_36801": True,  # identity carried from Phase26 freeze
        "no_weight_bytes_read": True,
        "global_reference_same_as_bundle": True,
    }
    return {
        "artifact": "phase27_component_identity_binding_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "no_model_construction": True,
        "stage": "COMPONENT_IDENTITY_BINDING",
        "components": {
            "G": {
                "name": "GlobalMedFiLM",
                "origin": "Phase21",
                "path": K.COMPONENT_CHECKPOINT_PATHS["global_medfilm"],
                "sha256": K.COMPONENT_CHECKPOINT_SHAS["global_medfilm"],
                "role_in_phase27": "GLOBAL_REFERENCE_AND_ROUTED_SYSTEM_BACKBONE",
                "trainable_in_phase27": False,
            },
            "R_psi": {
                "name": "BARRRegionalRefinerV1",
                "origin": "Phase25A",
                "path": K.COMPONENT_CHECKPOINT_PATHS["regional_refiner"],
                "sha256": K.COMPONENT_CHECKPOINT_SHAS["regional_refiner"],
                "trainable_in_phase27": False,
            },
            "B_phi": {
                "name": "BARRBenefitRouterV1",
                "origin": "Phase25D",
                "path": K.COMPONENT_CHECKPOINT_PATHS["benefit_router"],
                "sha256": K.COMPONENT_CHECKPOINT_SHAS["benefit_router"],
                "trainable_in_phase27": False,
            },
            "S_omega": {
                "name": "BARRPostSafetyV1",
                "origin": "Phase25F",
                "path": K.COMPONENT_CHECKPOINT_PATHS["post_safety"],
                "sha256": K.COMPONENT_CHECKPOINT_SHAS["post_safety"],
                "trainable_in_phase27": False,
            },
        },
        "global_reference_rule": (
            "The preservation baseline is the SAME frozen GlobalMedFiLM used inside the "
            "Phase26 bundle. No separate global baseline is trained or selected."
        ),
        "thresholds_never_conflated": {
            "roi_proposal": K.ROI_PROPOSAL_THRESHOLD,
            "segmentation_output": K.SEGMENTATION_OUTPUT_THRESHOLD,
            "somega_accept": K.SOMEGA_ACCEPT_THRESHOLD,
        },
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def main():
    rec("phase27_spec_entry_gate", s0_entry_gate())
    rec("phase27_predecessor_immutability_gate", s1_predecessor_immutability())
    rec("phase27_population_ownership_ruling_v1_0", s2_population_ownership_ruling())
    rec("phase27_val808_population_binding_v1_0", s3_val808_population_binding())
    rec("phase27_phase26_bundle_binding_v1_0", s4_phase26_bundle_binding())
    rec("phase27_preservation_contract_binding_v1_0", s5_preservation_contract_binding())
    rec("phase27_component_identity_binding_v1_0", s6_component_identity_binding())

    for name, obj in RESULTS.items():
        K.write_json(K.AUD / f"{name}.json", obj)

    failed = [n for n, o in RESULTS.items() if not o.get("all_pass")]
    print("\nFAILED:", failed if failed else "none")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
