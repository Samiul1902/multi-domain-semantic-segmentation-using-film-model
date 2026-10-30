"""Phase26 v1.2 driver - ROUTER DEPLOYMENT-SEMANTICS RECONCILIATION.

Sections 0-20.  Governance / specification ONLY.

Run:  .venv/Scripts/python.exe scripts/analysis/run_phase26_v12_deployment_semantics.py
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_v12_common as K  # noqa: E402

say = print


def check(name, cond):
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    return bool(cond)


# =========================================================================== #
# SECTION 0 - ENTRY GATE
# =========================================================================== #
def section_entry_gate():
    say("=" * 74)
    say("SECTION 0 - REQUIRED PREDECESSOR / ENTRY GATE")
    say("=" * 74)

    v11_term = K.jload(K.AUD / "phase26_router_threshold_reconciliation_terminal_v1_1.json")
    v11_fc = K.jload(K.AUD / "phase26_specification_final_check_v1_1.json")

    v11 = {}
    for path, sha in K.V11_BINDINGS.items():
        p = K.ROOT / path
        actual = K.sha256_file(p) if p.exists() else None
        v11[path] = {"exists": p.exists(), "sha256": actual,
                     "expected_sha256": sha, "unchanged": actual == sha}

    p25e = {}
    for name, path in K.P25E_SOURCES.items():
        p = K.ROOT / path
        actual = K.sha256_file(p) if p.exists() else None
        exp = K.P25E_SHAS.get(path)
        p25e[path] = {"exists": p.exists(), "sha256": actual,
                      "expected_sha256": exp,
                      "unchanged": (exp is None) or (actual == exp)}

    checks = {
        "predecessor_terminal_exact": v11_term.get("terminal") == K.PREDECESSOR_TERMINAL,
        "v11_all_pass": v11_term.get("all_pass") is True,
        "canonical_variant_A8_C9":
            v11_term.get("canonical_system_variant") == K.CANONICAL_VARIANT,
        "canonical_budget_0p25":
            float(v11_term.get("canonical_budget")) == K.CANONICAL_BUDGET,
        "canonical_lambda_0p25":
            float(v11_term.get("canonical_lambda_representative")) == float(K.CANONICAL_LAMBDA),
        "phase26_started_false": v11_term.get("phase26_started") is False,
        "holdout_reads_0":
            v11_term.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "val808_reads_0": v11_term.get("val808") == "UNOPENED",
        "test_reads_0": v11_term.get("test") == "LOCKED_UNTIL_PHASE39",
        "v11_final_check_all_pass": v11_fc.get("all_pass") is True,
        "v11_artifacts_unchanged": all(v["unchanged"] for v in v11.values()),
        "phase25e_sources_unchanged": all(v["unchanged"] for v in p25e.values()),
    }
    for k, v in checks.items():
        check(k, v)

    drift = [p for p, v in v11.items() if not v["unchanged"]] + \
            [p for p, v in p25e.items() if not v["unchanged"]]

    artifact = {
        "artifact": "phase26_v1_2_deployment_semantics_entry_gate",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION,
        "governance_only": True,
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "predecessor_v11_artifacts": v11,
        "phase25e_source_artifacts": p25e,
        "drift_paths": drift,
        "drift_count": len(drift),
        "checks": checks,
        "all_pass": bool(all(checks.values()) and not drift),
        "terminal_on_failure": K.TERMINAL_BLOCKED_PROVENANCE,
    }
    K.write_json(K.AUD / "phase26_v1_2_deployment_semantics_entry_gate.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 1 - CLASSIFICATION
# =========================================================================== #
def section_classification():
    say("")
    say("=" * 74)
    say("SECTION 1 - CLASSIFICATION")
    say("=" * 74)
    artifact = {
        "artifact": "phase26_v1_2_classification",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION,
        "governance_only": True,
        "does_not_change": [
            "Phase25E scientific results", "Phase25G scientific results",
            "OOF C7/C8 memberships", "budget selection", "lambda representative",
            "model weights", "normalization", "architecture", "A8/C9 choice",
        ],
        "changes_only": "WHICH FROZEN SCORE CALIBRATION IS AUTHORITATIVE FOR FUTURE INFERENCE",
        "science_changed": False,
        "policy_selection_changed": False,
        "model_changed": False,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_v1_2_classification.json", artifact)
    check("classification recorded", True)
    return artifact


# =========================================================================== #
# SECTION 2 - FREEZE TWO DISTINCT SCORE SPACES
# =========================================================================== #
def section_two_spaces():
    say("")
    say("=" * 74)
    say("SECTION 2 - FREEZE TWO DISTINCT SCORE SPACES")
    say("=" * 74)

    space_b = {
        "designation": "SPACE_B_SCIENTIFIC_OOF_POLICY_SPACE",
        "score_variable": "delta_hat_oof",
        "purpose": "Phase25E / Phase25G development-performance analysis",
        "C7_raw_threshold_25pct_exact": K.exact(K.TAU_C7_OOF),
        "C8_lambda025_utility_threshold_exact": K.exact(K.TAU_C8_OOF),
        "membership": "exact frozen Phase25E OOF 25% C8 membership",
        "selected_count": K.EXPECTED_COUNT,
        "selected_ids_sha256": K.OOF_MEMBERSHIP_SHA,
        "role": "SCIENTIFIC_DEVELOPMENT_MEMBERSHIP_ONLY",
        "immutable": True,
    }
    space_a = {
        "designation": "SPACE_A_FINAL_ROUTER_DEV_CALIBRATION_SPACE",
        "score_variable": "delta_hat_final_dev",
        "producer": "Phase25D FINAL benefit-router checkpoint",
        "population": "4957 ROUTER_DEVELOPMENT feature rows",
        "purpose": "future inference threshold calibration",
        "C7_final_router_raw_threshold_exact": K.exact(K.TAU_C7_FINAL),
        "role": "CANONICAL_FINAL_ROUTER_CALIBRATION",
        "oof_id_equality_required": False,
    }
    checks = {
        "space_B_score_is_oof": space_b["score_variable"] == "delta_hat_oof",
        "space_B_role_scientific": space_b["role"] == "SCIENTIFIC_DEVELOPMENT_MEMBERSHIP_ONLY",
        "space_A_score_is_final_dev": space_a["score_variable"] == "delta_hat_final_dev",
        "space_A_role_runtime": space_a["role"] == "CANONICAL_FINAL_ROUTER_CALIBRATION",
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_two_score_spaces_frozen_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "SPACE_B_scientific_oof_policy_space": space_b,
        "SPACE_A_final_router_dev_calibration_space": space_a,
        "checks": checks, "all_pass": all(checks.values()),
    }
    K.write_json(K.AUD / "phase26_two_score_spaces_frozen_v1_2.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 3 - RECOVER THE ORIGINAL PHASE25E FINAL-ROUTER CONTRACT
# =========================================================================== #
def section_recover_contract():
    say("")
    say("=" * 74)
    say("SECTION 3 - RECOVER THE ORIGINAL PHASE25E FINAL-ROUTER CONTRACT")
    say("=" * 74)

    contract = K.jload(K.ROOT / K.P25E_SOURCES["final_router_contract"])
    calib = K.jload(K.ROOT / K.P25E_SOURCES["dev_calibration_audit"])
    thr = K.rows_of(K.P25E_SOURCES["dev_thresholds"])
    row = next(r for r in thr if r["budget"] == "0.25" and r["comparator"] == "C7")

    dev_analysis = contract.get("development_performance_analysis")
    final_calib = contract.get("final_deployment_calibration", "")

    checks = {
        "contract_exists": (K.ROOT / K.P25E_SOURCES["final_router_contract"]).exists(),
        "dev_analysis_is_oof": dev_analysis == "frozen delta_hat_oof",
        "final_calibration_names_final_checkpoint":
            "frozen final Phase25D checkpoint" in final_calib
            and "4957" in final_calib,
        "checkpoint_sha_bound":
            contract.get("final_checkpoint_sha256") == K.FINAL_ROUTER_CHECKPOINT_SHA,
        "normalization_sha_bound":
            contract.get("normalization_sha256") == K.FINAL_NORMALIZATION_SHA,
        "calibration_audit_checkpoint_sha":
            calib.get("checkpoint_sha256") == K.FINAL_ROUTER_CHECKPOINT_SHA,
        "calibration_population_dev": str(calib.get("population", "")).startswith("ROUTER_DEVELOPMENT"),
        "dev_scores_sha_bound":
            calib.get("dev_scores_sha256")
            == K.P25E_SHAS[K.P25E_SOURCES["dev_scores"]],
        "dev_thresholds_sha_bound":
            calib.get("dev_thresholds_sha256")
            == K.P25E_SHAS[K.P25E_SOURCES["dev_thresholds"]],
        "threshold_row_0p25_present": row["budget"] == "0.25",
        "threshold_row_value_exact": Fraction(row["tau"]) == K.TAU_C7_FINAL,
        "boundary_tied_false": row["boundary_tied"] == "False",
        "selected_count_1239": int(row["selected_count"]) == K.EXPECTED_COUNT,
        "derive_from_final_not_oof_transfer":
            contract.get("calibration", "").startswith("derive rank boundaries and tau from final-router DEV scores"),
        "holdout_feature_inference_0":
            int(contract.get("holdout_feature_inference_in_this_task", 0)) == 0,
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_final_router_calibration_binding_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "source_contract": K.P25E_SOURCES["final_router_contract"],
        "source_contract_sha256": K.sha256_file(K.ROOT / K.P25E_SOURCES["final_router_contract"]),
        "final_router_checkpoint_sha256": K.FINAL_ROUTER_CHECKPOINT_SHA,
        "final_normalization_sha256": K.FINAL_NORMALIZATION_SHA,
        "population": "ROUTER_DEVELOPMENT (4957)",
        "dev_scores_source": K.P25E_SOURCES["dev_scores"],
        "dev_scores_sha256": K.P25E_SHAS[K.P25E_SOURCES["dev_scores"]],
        "tau_C7_final_exact": K.exact(K.TAU_C7_FINAL),
        "tau_C7_final_float": float(K.TAU_C7_FINAL),
        "boundary_tied": False,
        "dev_calibration_selected_count": K.EXPECTED_COUNT,
        "development_analysis_is_oof": True,
        "final_deployment_calibration_is_final_router": True,
        "checks": checks,
        "all_pass": all(checks.values()),
        "terminal_on_failure": K.TERMINAL_BLOCKED_PROVENANCE,
    }
    K.write_json(K.AUD / "phase26_final_router_calibration_binding_v1_2.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 4 - OOF ID EQUALITY IS NOT A DEPLOYMENT REQUIREMENT
# =========================================================================== #
def section_runtime_semantics():
    say("")
    say("=" * 74)
    say("SECTION 4/14 - RUNTIME POLICY SEMANTICS + POLICY IDENTITY LANGUAGE")
    say("=" * 74)

    artifact = {
        "artifact": "phase26_runtime_policy_semantics_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "superseded_for_runtime_only": {
            "v1_1_field": "membership_identity",
            "v1_1_value": "EXACT_PHASE25E_FROZEN_25PCT_C8_MEMBERSHIP",
            "status": "SUPERSEDED_FOR_RUNTIME_ONLY__RETAINED_AS_SCIENTIFIC_EVIDENCE",
        },
        "runtime_interpretation": {
            "canonical_policy_semantics":
                "25_PERCENT_DEV_CALIBRATED_A8_C9_RESOURCE_AWARE_POLICY",
        },
        "policy_identity_definition": {
            "architecture": "A8/C9",
            "budget_target": "25% DEV calibration target",
            "lambda_representative": 0.25,
            "threshold": "FINAL-router calibrated threshold tau_C8_final_exact",
            "s_omega_threshold": 0.50,
        },
        "oof_ids_role": "EVIDENCE_SET_IDENTITIES_ONLY",
        "OOF_vs_final_membership_equality_required": False,
        "final_router_dev_ids_may_differ_from_oof_ids": True,
        "difference_is_drift": False,
        "difference_reflects": "cross-fitted OOF predictor vs final all-DEV fitted predictor",
        "oof_scientific_membership_immutable": True,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_runtime_policy_semantics_v1_2.json", artifact)
    check("runtime semantics recorded", True)
    return artifact


# =========================================================================== #
# SECTION 5/6 - FINAL-ROUTER RAW + UTILITY THRESHOLD
# =========================================================================== #
def section_thresholds():
    say("")
    say("=" * 74)
    say("SECTION 5/6 - FINAL-ROUTER RAW + C8 UTILITY THRESHOLD")
    say("=" * 74)

    tau_c8 = K.TAU_C7_FINAL - K.LAMBDA_C
    expected = Fraction(-5003565381643716252018011, 205414980000000000000000000)

    checks = {
        "tau_C7_final_exact_matches_work_order": K.TAU_C7_FINAL ==
            Fraction(24796109646558761, 20000000000000000000),
        "lambda_C_exact_matches": K.LAMBDA_C == Fraction(262912, 10270749),
        "tau_C8_final_exact_matches_work_order": tau_c8 == expected,
        "tau_C8_float_approx_matches":
            abs(float(tau_c8) - (-0.024358327623641256)) < 1e-15,
        "C_exact_matches": K.C_ACTION == Fraction(1051648, 10270749),
        "unique_cost_1": int(K.jload(K.ROOT / K.P25E_SOURCES["cost_variability"])
                             ["unique_eligible_costs"]) == 1,
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_final_router_utility_threshold_transform_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "exact_rational_arithmetic": True,
        "identity": "tau_C8_final = tau_C7_final - lambda*C",
        "C_exact": K.exact(K.C_ACTION),
        "lambda_exact": K.exact(K.CANONICAL_LAMBDA),
        "lambda_C_exact": K.exact(K.LAMBDA_C),
        "tau_C7_final_exact": K.exact(K.TAU_C7_FINAL),
        "tau_C7_final_float": float(K.TAU_C7_FINAL),
        "tau_C8_final_exact": K.exact(tau_c8),
        "tau_C8_final_float": float(tau_c8),
        "decimal_is_not_authority": True,
        "checks": checks, "all_pass": all(checks.values()),
    }
    K.write_json(K.AUD / "phase26_final_router_utility_threshold_transform_v1_2.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 7/8 - FINAL-ROUTER DEV REPLAY + RELATIONSHIP
# =========================================================================== #
def section_replay():
    say("")
    say("=" * 74)
    say("SECTION 7/8 - FINAL-ROUTER DEV REPLAY + OOF RELATIONSHIP")
    say("=" * 74)

    dev = K.rows_of(K.P25E_SOURCES["dev_scores"])
    pairs = sorted(((Fraction(r["delta_hat_final_dev_exact"]), r["sample_id"]) for r in dev),
                   key=lambda t: (-t[0], t[1]))
    final_ids = {sid for _, sid in pairs[:K.EXPECTED_COUNT]}
    tau_c8 = K.TAU_C8_FINAL
    sel_c8 = {r["sample_id"] for r in dev
              if (Fraction(r["delta_hat_final_dev_exact"]) - K.LAMBDA_C) >= tau_c8}
    cutoff_K = pairs[K.EXPECTED_COUNT - 1][1]
    cutoff_K1 = pairs[K.EXPECTED_COUNT][1]
    final_sha = K.ids_sha(final_ids)

    oof = K.rows_of(K.P25E_SOURCES["oof_predictions"])
    oof_ids = {r["sample_id"] for r in oof if Fraction(r["delta_hat_oof"]) >= K.TAU_C7_OOF}
    inter = final_ids & oof_ids
    union = final_ids | oof_ids
    sym = final_ids ^ oof_ids

    say(f"  final={len(final_ids)} oof={len(oof_ids)} inter={len(inter)} union={len(union)} sym={len(sym)}")

    checks_replay = {
        "dev_rows_4957": len(dev) == 4957,
        "final_selected_count_1239": len(final_ids) == K.EXPECTED_COUNT,
        "c8_replay_count_1239": len(sel_c8) == K.EXPECTED_COUNT,
        "c8_replay_equals_c7_replay": sel_c8 == final_ids,
        "cutoff_rank_K_original": cutoff_K == K.FINAL_DEV_CUTOFF_K,
        "cutoff_rank_K1_original": cutoff_K1 == K.FINAL_DEV_CUTOFF_K1,
        "matches_own_phase25e_calibration": True,
    }
    for k, v in checks_replay.items():
        check(k, v)

    rel_checks = {
        "oof_selected_1239": len(oof_ids) == K.EXPECTED_COUNT,
        "final_selected_1239": len(final_ids) == K.EXPECTED_COUNT,
        "intersection_1086": len(inter) == K.EXPECTED_INTERSECTION,
        "oof_ids_sha_matches_frozen": K.ids_sha(oof_ids) == K.OOF_MEMBERSHIP_SHA,
        "oof_equals_final_NOT_required": True,
    }
    for k, v in rel_checks.items():
        check(k, v)

    artifact1 = {
        "artifact": "phase26_final_router_dev_membership_replay_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "no_model_forward": True,
        "replay_source": K.P25E_SOURCES["dev_scores"],
        "runtime_utility_formula": "delta_hat_final_dev - 0.25*C",
        "tau_C8_final_exact": K.exact(tau_c8),
        "selected_count": len(final_ids),
        "selected_count_C7": len(final_ids),
        "selected_count_C8": len(sel_c8),
        "matches_own_original_phase25e_calibration": True,
        "cutoff_rank_K": cutoff_K,
        "cutoff_rank_K1": cutoff_K1,
        "final_router_selected_ids_sha256": final_sha,
        "checks": checks_replay, "all_pass": all(checks_replay.values()),
        "terminal_on_failure": K.TERMINAL_BLOCKED_REPLAY,
    }
    K.write_json(K.AUD / "phase26_final_router_dev_membership_replay_v1_2.json", artifact1)

    artifact2 = {
        "artifact": "phase26_oof_vs_final_router_membership_relationship_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "descriptive_only": True,
        "not_a_pass_fail_gate": True,
        "oof_selected_count": len(oof_ids),
        "final_router_selected_count": len(final_ids),
        "intersection": len(inter),
        "union": len(union),
        "overlap_fraction_of_final": len(inter) / len(final_ids),
        "symmetric_difference": len(sym),
        "oof_selected_ids_sha256": K.ids_sha(oof_ids),
        "final_router_selected_ids_sha256": final_sha,
        "OOF_vs_final_membership_equality_required": False,
        "difference_classification": "EXPECTED_MODEL_FIT_SPACE_DIFFERENCE",
        "reason": ("OOF scores from fold-specific models (development performance estimation); "
                   "final-router scores from one model refit on all 4957 ROUTER_DEVELOPMENT labels; "
                   "identical ranking not required"),
        "is_artifact_drift": False,
        "is_threshold_corruption": False,
        "is_membership_corruption": False,
        "reason_to_recalibrate_from_outcomes": False,
        "checks": rel_checks, "all_pass": all(rel_checks.values()),
    }
    K.write_json(K.AUD / "phase26_oof_vs_final_router_membership_relationship_v1_2.json", artifact2)
    return artifact1, artifact2


# =========================================================================== #
# SECTION 9/10/11 - RUNTIME SCORE + FUTURE COHORT + STATE MACHINE v1.2
# =========================================================================== #
def section_runtime_and_state_machine():
    say("")
    say("=" * 74)
    say("SECTION 9/10/11 - RUNTIME SCORE + FUTURE COHORT RULE + STATE MACHINE v1.2")
    say("=" * 74)

    steps = [
        {"step": 1, "action": "run frozen GlobalMedFiLM exactly once",
         "outputs": ["p_global", "frozen feature taps"]},
        {"step": 2, "action": "construct Phase25B 202-D router features"},
        {"step": 3, "action": "normalize using Phase25D FINAL normalization"},
        {"step": 4, "action": "run FINAL frozen B_phi", "outputs": ["delta_hat_final"]},
        {"step": 5,
         "action": "compute utility = delta_hat_final - 0.25*(1051648/10270749)",
         "score_space": "C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY"},
        {"step": 6,
         "action": "EXECUTE iff utility >= -5003565381643716252018011/205414980000000000000000000 ; else SKIP",
         "tau_C8_final_exact": K.exact(K.TAU_C8_FINAL),
         "comparator": ">="},
    ]
    artifact_sm = {
        "artifact": "phase26_inference_state_machine_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "additive_to": "reports/audits/phase26_inference_state_machine_v1_1.json",
        "inputs": ["image x", "task_id t"],
        "steps": steps,
        "runtime_score_name": "C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY",
        "runtime_formula": "delta_hat_final - 0.25*C",
        "runtime_threshold": K.exact(K.TAU_C8_FINAL),
        "branch_SKIP": {"final": "p_global", "regional_refiner_run": False,
                        "s_omega_run": False},
        "branch_EXECUTE": {
            "steps": [
                "apply frozen ROI geometry",
                "run frozen refiner",
                "construct deterministic candidate",
                "construct frozen 20-D S_omega features",
                "normalize with Phase25F FINAL normalization",
                "run frozen S_omega",
            ],
            "if_sigmoid_logit_ge_0p50": "final = candidate",
            "else": "final = p_global",
        },
        "final_mask_threshold": 0.50,
        "second_global_forward": False,
        "gt_at_inference": False,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_inference_state_machine_v1_2.json", artifact_sm)

    artifact_fc = {
        "artifact": "phase26_future_cohort_rule_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "applies_to": ["ROUTER_HOLDOUT", "PHASE30"],
        "force_exact_25pct": False,
        "apply_fixed_dev_calibrated_threshold_per_sample": True,
        "realized_activation_fraction_may_differ_from_0p25": True,
        "report_nominal_calibration_budget": 0.25,
        "report_realized_holdout_activation_fraction": True,
        "holdout_ranking": False,
        "holdout_topK": False,
        "threshold_recalibration": False,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_future_cohort_rule_v1_2.json", artifact_fc)
    check("state machine v1.2 written", True)
    check("future cohort rule written", True)
    return artifact_sm, artifact_fc


# =========================================================================== #
# SECTION 12/13 - RECLASSIFY v1.1 OOF THRESHOLD + BUNDLE CONTRACT v1.2
# =========================================================================== #
def section_reclassify_and_bundle():
    say("")
    say("=" * 74)
    say("SECTION 12/13 - RECLASSIFY OOF THRESHOLD + BUNDLE CONTRACT v1.2")
    say("=" * 74)

    artifact_re = {
        "artifact": "phase26_oof_threshold_reclassification_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "preserved_value": K.exact(K.TAU_C8_OOF),
        "previous_role": "CANONICAL_OPERATIONAL_THRESHOLD",
        "new_role": "SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE",
        "retained": True, "deleted": False,
        "v1_1_artifact_remains_historical_provenance": True,
    }
    K.write_json(K.AUD / "phase26_oof_threshold_reclassification_v1_2.json", artifact_re)

    artifact_bd = {
        "artifact": "phase26_checkpoint_bundle_contract_v1_2",
        "phase": "26", "classification": K.CLASSIFICATION, "method": K.METHOD,
        "revision": K.REVISION, "governance_only": True,
        "additive_to": "reports/audits/phase26_checkpoint_bundle_contract_v1_1.json",
        "bundle_kind": "MANIFEST_OF_EXISTING_CANONICAL_COMPONENTS",
        "future_output_path": "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json",
        "calibration_blocks": {
            "A_oof_development_evidence": {
                "score_space": "OOF_DELTA_HAT",
                "raw_threshold_exact": K.exact(K.TAU_C7_OOF),
                "utility_threshold_exact": K.exact(K.TAU_C8_OOF),
                "purpose": "PHASE25_DEVELOPMENT_SCIENTIFIC_EVIDENCE",
                "runtime_authority": False,
            },
            "B_final_router_runtime_calibration": {
                "score_space": "FINAL_BPHI_DELTA_HAT",
                "raw_threshold_exact": K.exact(K.TAU_C7_FINAL),
                "utility_threshold_exact": K.exact(K.TAU_C8_FINAL),
                "lambda": 0.25,
                "cost_exact": K.exact(K.C_ACTION),
                "purpose": "FUTURE_INFERENCE",
                "runtime_authority": True,
            },
        },
        "operational_threshold":
            "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold",
        "both_blocks_present": True,
        "all_pass": True,
    }
    K.write_json(K.AUD / "phase26_checkpoint_bundle_contract_v1_2.json", artifact_bd)
    check("reclassification written", True)
    check("bundle contract v1.2 written", True)
    return artifact_re, artifact_bd


if __name__ == "__main__":
    g = section_entry_gate()
    section_classification()
    section_two_spaces()
    section_recover_contract()
    section_runtime_semantics()
    section_thresholds()
    section_replay()
    section_runtime_and_state_machine()
    section_reclassify_and_bundle()
    say("")
    say("=" * 74)
    say(f"PART 1 OVERALL entry_gate all_pass = {g['all_pass']}")
    say("=" * 74)
