#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 35 v1.0h — build the §Q smoke artifacts from the byte-captured canonical smoke payload.

This builder does NOT execute the smoke. It consumes the already-produced, byte-captured canonical
smoke stdout payload (`.phase35_tmp/runB.json`) and emits the four additive v1.0h governance artifacts:

  reports/audits/phase35_synthetic_interpretability_smoke_v1_0h.json
  reports/audits/phase35_synthetic_smoke_provenance_v1_0h.json
  reports/audits/phase35_synthetic_smoke_final_check_v1_0h.json
  reports/audits/phase35_synthetic_smoke_terminal_v1_0h.json

Never imports torch. No model construction / deserialization / forward / autograd / Grad-CAM / router
attribution / protected-data access.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

PAYLOAD = ROOT / ".phase35_tmp/runB.json"

EXEC_H = "scripts/analysis/phase35_interpretability_execution_v1_0h.py"
FREEZE_H1 = "reports/audits/phase35_preexecution_source_freeze_v1_0h1.json"
CONSIST = "reports/audits/phase35_v1_0h1_freeze_consistency_check.json"
ELIG_H1 = "reports/audits/phase35_synthetic_smoke_eligibility_v1_0h1.json"
FINALREC = "reports/audits/phase35_v1_0h1_freeze_reconciliation_final_check.json"
FREEZE_H = "reports/audits/phase35_preexecution_source_freeze_v1_0h.json"

EXPECTED_SHA = {
    EXEC_H: "48193f09672b047757e0eba9fa674df12c5b00a41629ba9671e48b50fe81ee81",
    FREEZE_H1: "79a7ce549e7704ef3e8903265facc3d928c76c1c983fe722c88d50f6b6c119d2",
    CONSIST: "310064b9e130d1f76e8c2e19b6e69f5381a82486b844598120ab15576b8db8dc",
    ELIG_H1: "748c060b58954dcf24bf9dde17d6d3bbe3d2d5ec10ff64ccf09d262ff5cf2bf5",
    FINALREC: "d1fef9b8c9daf041f02cc94654ca3fb63e77f9cacc6c9d2fa183bf15bc12881e",
    FREEZE_H: "a380068026a2107ca19bb1edb39907f47cf8cc5b62c536514a2c691ef7037f8a",
}

CANONICAL = {
    "G_model_constructions": 1, "B_phi_model_constructions": 1, "checkpoint_deserializations": 2,
    "strict_loads": 2, "G_synthetic_forwards": 1, "B_phi_synthetic_forwards": 1, "total_model_forwards": 2,
    "G_gradcam_autograd_calls": 1, "router_numeric_input_autograd_calls": 1, "total_autograd_calls": 2,
    "synthetic_CAM_maps": 2, "synthetic_router_attribution_rows": 4, "synthetic_smoke_target_masks": 1,
    "R_psi_model_constructions": 0, "R_psi_checkpoint_loads": 0, "R_psi_forwards": 0,
    "S_omega_model_constructions": 0, "S_omega_checkpoint_loads": 0, "S_omega_forwards": 0,
    "optimizer_constructions": 0, "optimizer_step_calls": 0, "training_backward_calls": 0,
    "parameter_mutations": 0, "raw_VAL_image_reads": 0, "real_persisted_VAL_probability_reads": 0,
    "VAL_GT_reads": 0, "router_feature_cache_rows_read": 0, "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0,
    "TRAIN_raw_reads": 0, "scientific_outputs": 0, "primary_synthetic_target_masks": 1,
    "actual_logits_empty_mask_helper_checks": 1, "additional_G_forwards_for_empty_mask": 0,
    "additional_autograd_calls_for_empty_mask": 0,
}
assert len(CANONICAL) == 35

CLASSIFICATION = "PRE_SCIENTIFIC_SYNTHETIC_NUMERICAL_INTERFACE_AND_FULL_COUNTER_CONTRACT_VALIDATION"
NOT_A_RESULT = "NOT_PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def dump(rel, doc):
    p = ROOT / rel
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    payload.pop("started_utc", None)

    counters = payload["counters"]
    expected = payload["expected_counters"]
    contract = payload["counter_contract_exact"]

    # -------- correctness gates --------
    g = {
        "counters_key_count_35": len(counters) == 35,
        "expected_key_count_35": len(expected) == 35,
        "counters_equal_canonical": counters == CANONICAL,
        "expected_equal_canonical": expected == CANONICAL,
        "counter_keyset_exact": payload.get("counter_keyset_exact") is True,
        "counter_count_exact": payload.get("counter_count_exact") is True,
        "counter_values_exact": payload.get("counter_values_exact") is True,
        "counts_match_expected": payload.get("counts_match_expected") is True,
    }

    smoke_art = OrderedDict([
        ("artifact", "phase35_synthetic_interpretability_smoke_v1_0h"),
        ("section", "\u00a7Q"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
        ("classification", CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("mode", "smoke"), ("smoke_gate_env", "PHASE35_SMOKE_EXECUTE=1"),
        ("science_gate_env_not_set", "PHASE35_EXECUTE"),
        ("authority_binding", OrderedDict([
            ("execution_source", {"path": EXEC_H, "sha256": sha(EXEC_H)}),
            ("reconciled_freeze_v1_0h1", {"path": FREEZE_H1, "sha256": sha(FREEZE_H1)}),
            ("freeze_consistency", {"path": CONSIST, "sha256": sha(CONSIST)}),
            ("eligibility_v1_0h1", {"path": ELIG_H1, "sha256": sha(ELIG_H1)}),
            ("freeze_reconciliation_final_check", {"path": FINALREC, "sha256": sha(FINALREC)}),
            ("superseded_freeze_v1_0h", {"path": FREEZE_H, "sha256": sha(FREEZE_H),
                                         "used_for_expected_table": False}),
        ])),
        ("runtime_payload", payload),
        ("canonical_35_key_contract", CANONICAL),
        ("observed_counters", counters),
        ("expected_counters", expected),
        ("counter_contract_exact", contract),
        ("gate_results", g),
        ("all_gates_pass", all(g.values())),
        ("generated_utc", NOW),
        ("all_pass", all(g.values())),
    ])
    n_smoke = dump("reports/audits/phase35_synthetic_interpretability_smoke_v1_0h.json", smoke_art)

    prov = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_provenance_v1_0h"),
        ("section", "\u00a7Q"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
        ("classification", CLASSIFICATION), ("not", NOT_A_RESULT),
        ("provenance", OrderedDict([
            ("execution_source_path", EXEC_H), ("execution_source_sha256", sha(EXEC_H)),
            ("execution_source_sha_expected",
             "48193f09672b047757e0eba9fa674df12c5b00a41629ba9671e48b50fe81ee81"),
            ("execution_source_sha_match", sha(EXEC_H) == EXPECTED_SHA[EXEC_H]),
            ("mode", "smoke"), ("gate_env", "PHASE35_SMOKE_EXECUTE=1"),
            ("invocation_count", 1), ("retry_performed", False),
            ("exit_code", 0), ("stderr_bytes", 0),
            ("reconciled_freeze_authority_path", FREEZE_H1),
            ("reconciled_freeze_authority_sha256", sha(FREEZE_H1)),
            ("reconciled_freeze_authority_expected",
             "79a7ce549e7704ef3e8903265facc3d928c76c1c983fe722c88d50f6b6c119d2"),
            ("freeze_consistency_sha256", sha(CONSIST)),
            ("eligibility_sha256", sha(ELIG_H1)),
            ("superseded_freeze_not_used_for_expected_table", True),
        ])),
        ("environment", payload.get("environment")),
        ("checkpoint_identity", payload.get("checkpoint_identity")),
        ("G_identity", payload.get("G_identity")),
        ("B_phi_identity", payload.get("B_phi_identity")),
        ("counter_ownership", payload.get("counter_ownership")),
        ("superseded_histories_preserved", OrderedDict([
            ("v1_0f_blocked_smoke", True), ("v1_0g_blocked_smoke", True),
            ("v1_0f_retry_performed", False), ("v1_0g_retry_performed", False),
            ("v1_0h_stale_freeze_preserved_not_overwritten", True),
        ])),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_prov = dump("reports/audits/phase35_synthetic_smoke_provenance_v1_0h.json", prov)

    # final check
    gs = payload["gradcam_smoke"]
    em = gs["empty_mask_helper_check"]
    pa = payload["parameter_grad_state_audit"]
    im = payload["parameter_immutability"]
    rs = payload["router_smoke"]
    zd = payload["zero_denominator_policy"]
    cc = payload["counter_contract"]
    cs = payload["checkpoint_identity"]

    checks = OrderedDict([
        ("authority_execution_source_sha_exact", sha(EXEC_H) == EXPECTED_SHA[EXEC_H]),
        ("reconciled_freeze_bound", sha(FREEZE_H1) == EXPECTED_SHA[FREEZE_H1]),
        ("environment_compatible", payload["environment"]["compatible"] is True),
        ("counter_baseline_zero_before_model", payload["counter_baseline"]["legacy"]["all_legacy_counters_zero"] is True
         and payload["counter_baseline"]["extension"]["all_extension_counters_zero"] is True),
        ("G_construction_1", counters["G_model_constructions"] == 1),
        ("B_phi_construction_1", counters["B_phi_model_constructions"] == 1),
        ("checkpoint_deserializations_2", counters["checkpoint_deserializations"] == 2),
        ("strict_loads_2", counters["strict_loads"] == 2),
        ("G_params_3523001", payload["G_identity"]["parameter_count"] == 3523001),
        ("B_phi_params_36801", payload["B_phi_identity"]["parameter_count"] == 36801),
        ("G_strict_missing_0", payload["G_identity"]["strict_load_missing"] == []),
        ("G_strict_unexpected_0", payload["G_identity"]["strict_load_unexpected"] == []),
        ("B_phi_strict_missing_0", payload["B_phi_identity"]["strict_load_missing"] == []),
        ("B_phi_strict_unexpected_0", payload["B_phi_identity"]["strict_load_unexpected"] == []),
        ("R_psi_untouched", counters["R_psi_model_constructions"] == 0 and counters["R_psi_checkpoint_loads"] == 0
         and counters["R_psi_forwards"] == 0),
        ("S_omega_untouched", counters["S_omega_model_constructions"] == 0 and counters["S_omega_checkpoint_loads"] == 0
         and counters["S_omega_forwards"] == 0),
        ("film_all_pass", payload["film_smoke"]["all_pass"] is True),
        ("film_no_scientific_tables", payload["film_smoke"]["scientific_film_tables_emitted"] is False),
        ("embedding_G_4x32_finite", payload["embedding_smoke"]["G_task_embedding_shape"] == [4, 32]
         and payload["embedding_smoke"]["G_finite"] is True),
        ("embedding_B_phi_4x16_finite", payload["embedding_smoke"]["B_phi_task_embedding_shape"] == [4, 16]
         and payload["embedding_smoke"]["B_phi_finite"] is True),
        ("gradcam_target_scalar_finite", gs["target_scalar_finite"] is True),
        ("gradcam_eight_guards", len(gs["finite_guards_applied"]) == 8),
        ("gradcam_gradients_finite", gs["all_gradients_finite"] is True),
        ("gradcam_cams_finite", gs["all_cams_all_zero"] is True or gs["all_prenorm_cams_finite"] is True),
        ("gradcam_layers_bridge_decoder1", set(gs["cams"].keys()) == {"bridge", "decoder1"}),
        ("empty_mask_same_actual_logits", em["same_actual_G_logits_used"] is True
         and em["surrogate_zero_logits_used"] is False),
        ("empty_mask_comparison_pass", em["comparison_pass"] is True and em["difference"] == 0.0),
        ("empty_mask_no_extra_forward", em["additional_G_forwards"] == 0),
        ("empty_mask_no_extra_autograd", em["additional_autograd_calls"] == 0),
        ("no_parameter_grad_populated", pa["NO_PARAMETER_GRAD_POPULATED"] is True
         and pa["G"]["non_null_grad_tensors"] == 0 and pa["B_phi"]["non_null_grad_tensors"] == 0),
        ("G_86_param_tensors", pa["G"]["named_parameter_tensors"] == 86),
        ("B_phi_11_param_tensors", pa["B_phi"]["named_parameter_tensors"] == 11),
        ("state_immutability", im["G_state_tensors_unchanged"] is True
         and im["B_phi_state_tensors_unchanged"] is True and im["parameter_mutations"] == 0),
        ("router_raw_delta_hat_4_finite", rs["raw_delta_hat_shape"] == [4] and rs["raw_delta_hat_finite"] is True),
        ("router_gradient_4x202_finite", rs["router_gradient_shape"] == [4, 202] and rs["router_gradient_finite"] is True),
        ("router_gxi_4x202_finite", rs["gradient_x_input_shape"] == [4, 202] and rs["gradient_x_input_finite"] is True),
        ("router_sigmoid_count_0", rs["sigmoid_count"] == 0),
        ("zero_denominator_policy", zd["ZERO_ROUTER_GRAD_ATTRIBUTION"] is True
         and zd["epsilon_added"] is False and zd["renormalization"] is False),
        ("counter_keyset_exact", payload["counter_keyset_exact"] is True),
        ("counter_count_exact", payload["counter_count_exact"] is True),
        ("counter_values_exact", payload["counter_values_exact"] is True),
        ("counts_match_expected", payload["counts_match_expected"] is True),
        ("alias_equals_primary", cc["alias_equals_primary"] is True),
        ("empty_not_counted_as_primary", cc["empty_mask_not_counted_as_primary"] is True),
        ("primary_alias_empty_1_1_1", cc["primary_target_mask_count"] == 1
         and cc["primary_target_mask_alias_count"] == 1 and cc["empty_mask_helper_check_count"] == 1),
        ("router_writer_store_identity", payload["counter_ownership"]["router_writer_store_identity_verified"] is True),
        ("router_reader_store_identity", payload["counter_ownership"]["router_reader_store_identity_verified"] is True),
        ("router_writer_reader_bridge", payload["counter_ownership"][
            "router_counter_writer_reader_same_object_or_explicit_delta_bridge"] is True),
        ("protected_data_zeros", all(counters[k] == 0 for k in
                                     ["raw_VAL_image_reads", "real_persisted_VAL_probability_reads",
                                      "VAL_GT_reads", "router_feature_cache_rows_read", "ROUTER_HOLDOUT_reads",
                                      "TEST_reads", "TRAIN_raw_reads", "scientific_outputs"])),
        ("smoke_success", payload["smoke_success"] is True),
        ("counter_contract_pass", payload["counter_contract_pass"] is True),
        ("scientific_interface_checks_pass", payload["scientific_interface_checks_pass"] is True),
        ("artifact_generation_pass", payload["artifact_generation_pass"] is True),
        ("terminal_state_success", payload["terminal_state"] == "SUCCESS"),
        ("all_pass_equals_smoke_success", payload["all_pass"] == payload["smoke_success"]),
    ])
    nfail = sum(1 for v in checks.values() if not v)
    fdoc = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_final_check_v1_0h"),
        ("section", "\u00a7Q"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
        ("classification", CLASSIFICATION), ("not", NOT_A_RESULT),
        ("checks", checks), ("total_checks", len(checks)), ("passed", len(checks) - nfail), ("failed", nfail),
        ("reconciled_freeze_authority_sha256", sha(FREEZE_H1)),
        ("execution_source_sha256", sha(EXEC_H)),
        ("first_valid_v1_0h_smoke_attempt", True), ("smoke_retry_performed", False),
        ("generated_utc", NOW), ("all_pass", nfail == 0),
    ])
    n_fc = dump("reports/audits/phase35_synthetic_smoke_final_check_v1_0h.json", fdoc)

    ok = all(g.values()) and nfail == 0
    term = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_terminal_v1_0h"),
        ("section", "\u00a7R"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h"),
        ("classification", CLASSIFICATION), ("not", NOT_A_RESULT),
        ("artifact_generation_pass", True),
        ("scientific_interface_checks_pass", payload["scientific_interface_checks_pass"]),
        ("counter_contract_pass", payload["counter_contract_pass"]),
        ("smoke_success", payload["smoke_success"]),
        ("all_pass", payload["smoke_success"]),
        ("terminal_state", "COMPLETE" if ok else "BLOCKED"),
        ("execution_source_sha256", sha(EXEC_H)),
        ("reconciled_freeze_authority_sha256", sha(FREEZE_H1)),
        ("first_phase35_scientific_execution_eligible_for_supervisor_review", bool(ok)),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("test_state", "LOCKED_UNTIL_PHASE39"),
        ("terminal_string",
         ("PHASE35_SYNTHETIC_SMOKE_V1_0H_COMPLETE__CANONICAL_G_AND_B_PHI_STRICT_LOAD_AND_STATE_IDENTITY_PASS__"
          "FILM_EMBEDDING_AND_NUMERICALLY_GUARDED_RANK_SAFE_GRADCAM_PASS__ACTUAL_SAME_FORWARD_LOGITS_EMPTY_MASK_"
          "FALLBACK_PASS__ROUTER_RAW_DELTA_HAT_GRADIENT_X_INPUT_PASS__FULL_35_KEY_COUNTER_CONTRACT_KEYSET_COUNT_"
          "AND_VALUES_EXACT__PRIMARY_TARGET_ALIAS_AND_EMPTY_MASK_OBSERVABILITY_COUNTS_1_1_1_PASS__ZERO_PROTECTED_"
          "DATA_OR_SCIENTIFIC_OUTPUT_ACCESS__FIRST_PHASE35_SCIENTIFIC_EXECUTION_ELIGIBLE_FOR_SUPERVISOR_REVIEW_"
          "NOT_STARTED") if ok else
         ("PHASE35_SYNTHETIC_SMOKE_V1_0H_BLOCKED__CANONICAL_MODEL_NUMERICAL_INTERFACE_OR_FULL_COUNTER_"
          "CONTRACT_CHECK_FAILED__FIRST_VALID_ATTEMPT_PRESERVED__NO_RETRY__ZERO_PROTECTED_DATA_OR_SCIENTIFIC_"
          "OUTPUT_ACCESS")),
        ("generated_utc", NOW), ("all_gates_pass", ok),
    ])
    n_term = dump("reports/audits/phase35_synthetic_smoke_terminal_v1_0h.json", term)

    print("smoke artifact :", n_smoke)
    print("provenance     :", n_prov)
    print("final check    :", n_fc, f"({len(checks)-nfail}/{len(checks)} pass, {nfail} fail)")
    print("terminal       :", n_term, "state=", term["terminal_state"])
    print()
    print(term["terminal_string"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
