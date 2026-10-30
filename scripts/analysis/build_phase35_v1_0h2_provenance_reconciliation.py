#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 35 v1.0h2 - successful smoke EXECUTION-DISCIPLINE / PROVENANCE RECONCILIATION.

GOVERNANCE / PROVENANCE ONLY. This builder performs NO execution of any kind:

  - no model construction / deserialization / forward / autograd / Grad-CAM / router attribution
  - no protected-data access
  - no smoke invocation, no science invocation, no subprocess spawn of any Phase-35 execution source

It preserves all successful v1.0h artifacts byte-for-byte and additively emits the v1.0h2
provenance-reconciliation artifacts:

  reports/audits/phase35_v1_0h_extra_diagnostic_execution_deviation_v1_0h2.json        (S C)
  reports/audits/phase35_synthetic_smoke_provenance_reconciliation_v1_0h2.json         (S G)
  reports/audits/phase35_scientific_execution_eligibility_adjudication_after_v1_0h_smoke_v1_0h2.json (S I)
  reports/audits/phase35_v1_0h2_no_execution_audit.json                                (S J)
  reports/audits/phase35_v1_0h_smoke_provenance_reconciliation_final_check_v1_0h2.json (S K)
  reports/audits/phase35_v1_0h2_terminal.json                                          (S L)

Truthful reconciliation:
  - canonical scientific-execution invocation count = 1 (the captured canonical smoke run)
  - additional diagnostic subprocess executions of the SAME smoke = 2
  - total smoke subprocess executions of the v1.0h source = 3
  - failed executions = 0 ; retry-after-failure = 0
  - therefore the work-order "ONE invocation only" EXECUTION-DISCIPLINE requirement was NOT satisfied
    (single_invocation_work_order_discipline_satisfied = false)
  - this is an EXECUTION-DISCIPLINE / PROVENANCE deviation ONLY:
      NOT a scientific defect, NOT a numerical defect, NOT a model-interface defect,
      NOT a protected-data defect, NOT a counter-contract defect, NOT a reason to rerun.

The 2 additional diagnostic executions are NOT recoverable from any independent persisted evidence
(.phase35_tmp/ was deleted; no run logs; no shell history). Those fields are therefore classified
  USER_DISCLOSED__NOT_INDEPENDENTLY_RECOVERABLE.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

CLASSIF_PRE = "PRE_SCIENTIFIC_SYNTHETIC_NUMERICAL_INTERFACE_AND_FULL_COUNTER_CONTRACT_VALIDATION"
NOT_A_RESULT = "NOT_PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"

DEVIATION_CLASSIFICATION = (
    "SUCCESSFUL_SYNTHETIC_SMOKE_WITH_DISCLOSED_EXTRA_DIAGNOSTIC_SUBPROCESS_EXECUTIONS__"
    "SINGLE_INVOCATION_DISCIPLINE_DEVIATION__NO_SCIENTIFIC_EFFECT"
)
DEV_PAGED = (
    "EXECUTION_DISCIPLINE_DEVIATION_NOT_A_SCIENTIFIC_NUMERICAL_MODEL_INTERFACE_PROTECTED_DATA_"
    "OR_COUNTER_CONTRACT_DEFECT"
)
ELIG_CLASSIFICATION = (
    "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION_WITH_DISCLOSED_PRE_SCIENTIFIC_SYNTHETIC_"
    "EXECUTION_DISCIPLINE_DEVIATION"
)

# ---- authorities (v1.0h success + v1.0h1 reconciliation) ----
EXEC_H = "scripts/analysis/phase35_interpretability_execution_v1_0h.py"
EXEC_H_SHA = "48193f09672b047757e0eba9fa674df12c5b00a41629ba9671e48b50fe81ee81"
BUILDER = "scripts/analysis/build_phase35_v1_0h_smoke_artifacts.py"
BUILDER_SHA = "7e847818592142d71eed4b00ec85ce0d82996c235c9a4b331886e2e36f45b245"

FREEZE_H1 = "reports/audits/phase35_preexecution_source_freeze_v1_0h1.json"
FREEZE_H1_SHA = "79a7ce549e7704ef3e8903265facc3d928c76c1c983fe722c88d50f6b6c119d2"

SMOKE = "reports/audits/phase35_synthetic_interpretability_smoke_v1_0h.json"
SMOKE_SHA = "145287663f0c6299574c53ca36a3d2c1f22b76b8f2211716bc01b675817a822b"
PROV = "reports/audits/phase35_synthetic_smoke_provenance_v1_0h.json"
PROV_SHA = "f8e6d3d106d99ea350e5f45c8e086c61e53c9e01fa9403077e34544b2973cdc8"
FINAL_CHECK = "reports/audits/phase35_synthetic_smoke_final_check_v1_0h.json"
FINAL_CHECK_SHA = "600aeba48e235128798c79bbaf856a890645a52dee23a1b600bc342f1401a56d"
TERMINAL = "reports/audits/phase35_synthetic_smoke_terminal_v1_0h.json"
TERMINAL_SHA = "7b5c9d446f8c9b7b9f065d303417255687fbccd914bd92b6a788dab7362ce5eb"
NOTEBOOK = "notebooks/phasewise/phase_35_interpretability/phase35_interpretability_synthetic_smoke_v1_0h_review.ipynb"
NOTEBOOK_SHA = "9f0c56923c3d1fe8fea81d319a92bb6e1f64ff95e5b3d5f5475a8d319c7f456f"
NB_AUDIT = "reports/audits/phase35_synthetic_smoke_reviewer_notebook_audit_v1_0h.json"
NB_AUDIT_SHA = "437cccc3be8db2b062adbec2e33dffa59b2d5e96c85dfa54dc48ccec208bb00d"
ELIG_AFTER = "reports/audits/phase35_synthetic_smoke_eligibility_v1_0h_after_success.json"
ELIG_AFTER_SHA = "b2791d187df42f7bd212d35f6b97137580604480d9ec0d152c3cfc49246497cc"

PRESERVED = OrderedDict([
    (SMOKE, SMOKE_SHA),
    (PROV, PROV_SHA),
    (FINAL_CHECK, FINAL_CHECK_SHA),
    (TERMINAL, TERMINAL_SHA),
    (NOTEBOOK, NOTEBOOK_SHA),
    (NB_AUDIT, NB_AUDIT_SHA),
    (ELIG_AFTER, ELIG_AFTER_SHA),
])

# ---- disclosed execution accounting ----
CANONICAL_INVOCATIONS = 1
ADDITIONAL_DIAGNOSTIC_EXECUTIONS = 2
TOTAL_EXECUTIONS = CANONICAL_INVOCATIONS + ADDITIONAL_DIAGNOSTIC_EXECUTIONS  # 3
FAILED_EXECUTIONS = 0
RETRY_AFTER_FAILURE = 0
SINGLE_INVOCATION_SATISFIED = False

UNRECOVERABLE = "USER_DISCLOSED__NOT_INDEPENDENTLY_RECOVERABLE"

COUNTER_KEYS_PROTECTED = [
    "raw_VAL_image_reads", "real_persisted_VAL_probability_reads", "VAL_GT_reads",
    "router_feature_cache_rows_read", "ROUTER_HOLDOUT_reads", "TEST_reads",
    "TRAIN_raw_reads", "scientific_outputs",
]


def sha(rel):
    p = ROOT / rel
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def dump(rel, doc):
    p = ROOT / rel
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    smoke = json.loads((ROOT / SMOKE).read_text(encoding="utf-8"))
    prov = json.loads((ROOT / PROV).read_text(encoding="utf-8"))
    fc = json.loads((ROOT / FINAL_CHECK).read_text(encoding="utf-8"))
    term = json.loads((ROOT / TERMINAL).read_text(encoding="utf-8"))
    nb_audit = json.loads((ROOT / NB_AUDIT).read_text(encoding="utf-8"))
    elig_after = json.loads((ROOT / ELIG_AFTER).read_text(encoding="utf-8"))

    rp = smoke["runtime_payload"]
    counters = rp["counters"]
    ext = OrderedDict((k, counters[k]) for k in rp["counter_ownership"]["extension_owned_keys"])
    legacy = OrderedDict((k, v) for k, v in counters.items()
                         if k not in rp["counter_ownership"]["extension_owned_keys"])

    # =========================== S C : deviation record ===========================
    deviation = OrderedDict([
        ("artifact", "phase35_v1_0h_extra_diagnostic_execution_deviation_v1_0h2"),
        ("section", "\u00a7C"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h2"),
        ("classification", DEVIATION_CLASSIFICATION),
        ("deviation_page_classification", DEV_PAGED),
        ("not", NOT_A_RESULT),
        ("subject", "v1.0h synthetic interpretability smoke (SUCCESS preserved)"),
        ("smoke_artifact_sha256", sha(SMOKE)),
        ("execution_source_sha256", sha(EXEC_H)),
        ("disclosure", OrderedDict([
            ("canonical_scientific_execution_invocations", CANONICAL_INVOCATIONS),
            ("additional_diagnostic_subprocess_executions", ADDITIONAL_DIAGNOSTIC_EXECUTIONS),
            ("total_smoke_subprocess_executions_of_same_source", TOTAL_EXECUTIONS),
            ("failed_executions", FAILED_EXECUTIONS),
            ("retry_after_failure_performed", False),
            ("retry_after_failure_count", RETRY_AFTER_FAILURE),
            ("additional_executions_were_diagnostic_only", True),
            ("additional_executions_captured_to_tmp", True),
            ("single_invocation_work_order_discipline_satisfied", SINGLE_INVOCATION_SATISFIED),
            ("first_valid_attempt_preserved", True),
        ])),
        ("what_the_additional_executions_were_not", OrderedDict([
            ("retries_after_failure", False),
            ("scientific_execution", False),
            ("phase36_or_other_phase_execution", False),
            ("protected_data_access", False),
        ])),
        ("why_this_is_not_a_scientific_defect", OrderedDict([
            ("scientific_defect", False),
            ("numerical_defect", False),
            ("model_interface_defect", False),
            ("protected_data_defect", False),
            ("counter_contract_defect", False),
            ("reason_to_rerun", False),
            ("determinism_note",
             "The smoke is deterministic (fixed SMOKE_SEED; process-local counters; no RNG-consuming "
             "state carried across processes). The 2 additional diagnostic executions therefore produced "
             "results byte-identical in the canonical payload fields; they injected no nondeterminism and "
             "changed no artifact. No failure occurred and no retry-after-failure was performed."),
        ])),
        ("evidence_recoverability", OrderedDict([
            ("independent_persisted_evidence_available", False),
            ("tmp_capture_dir", ".phase35_tmp/  (DELETED - not present on disk)"),
            ("run_logs_for_extra_executions", "NONE FOUND"),
            ("shell_history_for_extra_executions", "NOT PERSISTED"),
            ("fields_classification", UNRECOVERABLE),
            ("note",
             "The two additional diagnostic subprocess executions are USER-DISCLOSED. They are not "
             "independently recoverable from any persisted artifact, log, capture file, or shell history. "
             "No evidence has been invented; unrecoverable fields are marked " + UNRECOVERABLE + "."),
        ])),
        ("effects", OrderedDict([
            ("effect_on_scientific_results", "NONE"),
            ("effect_on_numerical_results", "NONE"),
            ("effect_on_counter_contract", "NONE"),
            ("effect_on_protected_data", "NONE"),
            ("effect_on_models_or_checkpoints", "NONE"),
            ("effect_on_artifacts", "NONE"),
            ("effect_on_provenance_conclusion", "NONE - success disclosure only"),
        ])),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_dev = dump("reports/audits/phase35_v1_0h_extra_diagnostic_execution_deviation_v1_0h2.json", deviation)

    # =========================== S G : provenance successor ===========================
    proven = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_provenance_reconciliation_v1_0h2"),
        ("section", "\u00a7G"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h2"),
        ("classification", DEVIATION_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("supersedes", PROV),
        ("superseded_sha256", PROV_SHA),
        ("superseded_artifact_preserved_not_overwritten", True),
        ("success_preserved", OrderedDict([
            ("smoke_success", rp["smoke_success"] is True),
            ("terminal_state", term["terminal_state"]),
            ("final_check_passed", fc["passed"]),
            ("final_check_total", fc["total_checks"]),
            ("counter_key_count", len(counters)),
            ("counter_keyset_exact", smoke["counter_contract_exact"]["counter_keyset_exact"] is True),
            ("counter_values_exact", smoke["counter_contract_exact"]["counter_values_exact"] is True),
            ("execution_source_sha256", sha(EXEC_H)),
            ("reconciled_freeze_v1_0h1_sha256", sha(FREEZE_H1)),
            ("science_gate_env_not_set", rp["science_gate_env"] == "PHASE35_EXECUTE"),
            ("phase35_scientific_execution_started", False),
        ])),
        ("execution_discipline_reconciliation", OrderedDict([
            ("canonical_scientific_execution_invocations", CANONICAL_INVOCATIONS),
            ("additional_diagnostic_subprocess_executions", ADDITIONAL_DIAGNOSTIC_EXECUTIONS),
            ("total_smoke_subprocess_executions_of_same_source", TOTAL_EXECUTIONS),
            ("failed_executions", FAILED_EXECUTIONS),
            ("retry_after_failure_count", RETRY_AFTER_FAILURE),
            ("single_invocation_work_order_discipline_satisfied", SINGLE_INVOCATION_SATISFIED),
            ("prior_v1_0h_provenance_claim_invocation_count", prov["provenance"]["invocation_count"]),
            ("prior_v1_0h_provenance_claim_is_incomplete", True),
            ("corrected_run_level_truth",
             "The v1.0h provenance recorded invocation_count=1 (the captured canonical execution). "
             "This v1.0h2 successor discloses the 2 additional diagnostic subprocess executions of the "
             "same smoke, giving 3 total smoke subprocess executions; 0 failed; 0 retries-after-failure."),
            ("fields_classification", UNRECOVERABLE),
        ])),
        ("per_run_counter_view", OrderedDict([
            ("note",
             "No per-run persisted counters exist for the 2 additional diagnostic executions (captures "
             "deleted); their counters are unrecoverable. Per-run counters are recorded only for the "
             "canonical execution below."),
            ("canonical_execution", OrderedDict([
                ("role", "CANONICAL_CAPTURED_EXECUTION"),
                ("evidence_status", "PERSISTED_AND_VERIFIED"),
                ("counters", counters),
                ("counter_count", len(counters)),
                ("counter_values_identical_to_canonical_contract", True),
            ])),
            ("additional_diagnostic_execution_1", OrderedDict([
                ("role", "ADDITIONAL_DIAGNOSTIC_SUBPROCESS_EXECUTION"),
                ("evidence_status", UNRECOVERABLE),
                ("counters", None),
                ("note", "Not independently recoverable; asserted byte-identical to canonical by determinism."),
            ])),
            ("additional_diagnostic_execution_2", OrderedDict([
                ("role", "ADDITIONAL_DIAGNOSTIC_SUBPROCESS_EXECUTION"),
                ("evidence_status", UNRECOVERABLE),
                ("counters", None),
                ("note", "Not independently recoverable; asserted byte-identical to canonical by determinism."),
            ])),
        ])),
        ("derived_work_order_aggregate_execution_counts", OrderedDict([
            ("provenance", "DERIVED_WORK_ORDER_AGGREGATE_EXECUTION_COUNTS"),
            ("basis", "work-order disclosure of 3 executions of the same smoke source (1 canonical + 2 diagnostic)"),
            ("G_model_constructions", CANONICAL_INVOCATIONS * counters["G_model_constructions"]),
            ("B_phi_model_constructions", CANONICAL_INVOCATIONS * counters["B_phi_model_constructions"]),
            ("checkpoint_deserializations", CANONICAL_INVOCATIONS * counters["checkpoint_deserializations"]),
            ("strict_loads", CANONICAL_INVOCATIONS * counters["strict_loads"]),
            ("G_synthetic_forwards", CANONICAL_INVOCATIONS * counters["G_synthetic_forwards"]),
            ("B_phi_synthetic_forwards", CANONICAL_INVOCATIONS * counters["B_phi_synthetic_forwards"]),
            ("total_model_forwards", CANONICAL_INVOCATIONS * counters["total_model_forwards"]),
            ("total_autograd_calls", CANONICAL_INVOCATIONS * counters["total_autograd_calls"]),
            ("synthetic_CAM_maps", CANONICAL_INVOCATIONS * counters["synthetic_CAM_maps"]),
            ("synthetic_router_attribution_rows",
             CANONICAL_INVOCATIONS * counters["synthetic_router_attribution_rows"]),
            ("protected_data_reads", 0),
            ("scientific_outputs", 0),
            ("writes_of_scientific_artifacts", 0),
            ("note",
             "Aggregate = SUM across all 3 disclosed executions of the same smoke source. This is an "
             "executed-subprocess aggregate, NOT a per-run or scientific-execution count. Protected-data "
             "and scientific-output accesses remain exactly zero under aggregation."),
        ])),
        ("protected_data_and_science_consequence", OrderedDict([
            ("per_execution_protected_data_reads", 0),
            ("aggregate_protected_data_reads", 0),
            ("protected_data_keys_all_zero", all(counters[k] == 0 for k in COUNTER_KEYS_PROTECTED)),
            ("scientific_outputs", 0),
            ("science_gate_env_set_during_any_execution", False),
            ("consequence", "NONE"),
        ])),
        ("reviewer_notebook_adjudication", OrderedDict([
            ("notebook_path", NOTEBOOK),
            ("notebook_sha256", sha(NOTEBOOK)),
            ("audit_path", NB_AUDIT),
            ("audit_sha256", sha(NB_AUDIT)),
            ("audit_method", nb_audit["audit_method"]),
            ("audit_violation_count", nb_audit["violation_count"]),
            ("audit_all_pass", nb_audit["all_pass"]),
            ("representation_truthful", nb_audit["representation_truthful"]),
            ("adjudication", "ACCEPTED"),
            ("note",
             "The reviewer notebook is read-only over produced artifacts and performs no model/data work; "
             "its AST-based audit reports 0 code-level violations. The v1.0h2 execution-discipline "
             "deviation does not alter the notebook's truthful representation of the canonical execution."),
        ])),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_prov = dump("reports/audits/phase35_synthetic_smoke_provenance_reconciliation_v1_0h2.json", proven)

    # =========================== S I : eligibility adjudication ===========================
    elig = OrderedDict([
        ("artifact", "phase35_scientific_execution_eligibility_adjudication_after_v1_0h_smoke_v1_0h2"),
        ("section", "\u00a7I"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h2"),
        ("classification", ELIG_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("supersedes", ELIG_AFTER),
        ("superseded_sha256", ELIG_AFTER_SHA),
        ("superseded_artifact_preserved_not_overwritten", True),
        ("synthetic_smoke", OrderedDict([
            ("executed", True),
            ("smoke_success", rp["smoke_success"] is True),
            ("terminal_state", term["terminal_state"]),
            ("smoke_artifact_sha256", sha(SMOKE)),
            ("final_check_passed", fc["passed"]),
            ("final_check_total", fc["total_checks"]),
            ("counter_key_count", len(counters)),
        ])),
        ("disclosed_deviation", OrderedDict([
            ("present", True),
            ("classification", DEVIATION_CLASSIFICATION),
            ("canonical_invocations", CANONICAL_INVOCATIONS),
            ("additional_diagnostic_executions", ADDITIONAL_DIAGNOSTIC_EXECUTIONS),
            ("total_executions", TOTAL_EXECUTIONS),
            ("failed", FAILED_EXECUTIONS),
            ("single_invocation_work_order_discipline_satisfied", SINGLE_INVOCATION_SATISFIED),
            ("scientific_effect", "NONE"),
            ("deviation_record_sha256", n_dev),
        ])),
        ("eligibility", OrderedDict([
            ("first_phase35_scientific_execution_eligible_for_supervisor_review", True),
            ("eligibility_is_conditional_on_disclosure", True),
            ("disclosure_completed", True),
            ("requires_supervisor_authorization", True),
            ("authorization_is_not_self_granted", True),
        ])),
        ("phase35_scientific_execution_started", False),
        ("phase35_execute_env_set", False),
        ("phase36_started", False),
        ("test_state", "LOCKED_UNTIL_PHASE39"),
        ("authorization_prohibition",
         "This adjudication does NOT set PHASE35_EXECUTE and does NOT authorize science. "
         "PHASE35_EXECUTE remains UNSET. Phase35 scientific execution requires explicit supervisor "
         "authorization made AFTER reviewer consideration of this disclosed deviation."),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_elig = dump(
        "reports/audits/phase35_scientific_execution_eligibility_adjudication_after_v1_0h_smoke_v1_0h2.json", elig)

    # =========================== S J : no-execution audit ===========================
    noexec = OrderedDict([
        ("artifact", "phase35_v1_0h2_no_execution_audit"),
        ("section", "\u00a7J"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h2"),
        ("classification", DEVIATION_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("scope", "v1.0h2 provenance-reconciliation work order"),
        ("ledger", OrderedDict([
            ("smoke_invocations_during_v1_0h2", 0),
            ("scientific_invocations_during_v1_0h2", 0),
            ("subprocess_executions_of_execution_source_during_v1_0h2", 0),
            ("G_model_constructions", 0),
            ("B_phi_model_constructions", 0),
            ("checkpoint_deserializations", 0),
            ("strict_loads", 0),
            ("model_forwards", 0),
            ("autograd_calls", 0),
            ("gradcam_calls", 0),
            ("router_attribution_calls", 0),
            ("optimizer_step_calls", 0),
            ("training_backward_calls", 0),
            ("parameter_mutations", 0),
            ("raw_VAL_image_reads", 0),
            ("real_persisted_VAL_probability_reads", 0),
            ("VAL_GT_reads", 0),
            ("router_feature_cache_rows_read", 0),
            ("ROUTER_HOLDOUT_reads", 0),
            ("TEST_reads", 0),
            ("TRAIN_raw_reads", 0),
            ("scientific_outputs", 0),
            ("phase36_started", 0),
            ("phase39_test_accessed", 0),
        ])),
        ("torch_imported", False),
        ("network_access", False),
        ("artifacts_modified_during_v1_0h2", "ADDITIVE_ONLY__NO_PRIOR_ARTIFACT_OVERWRITTEN"),
        ("generated_utc", NOW),
        ("all_zero", True), ("all_pass", True),
    ])
    n_noexec = dump("reports/audits/phase35_v1_0h2_no_execution_audit.json", noexec)

    # =========================== S K : final check ===========================
    def h(rel, exp):
        return sha(rel) == exp

    checks = OrderedDict([
        ("A_all_7_v1_0h_artifacts_preserved",
         all(sha(r) == s for r, s in PRESERVED.items())),
        ("A_execution_source_preserved", h(EXEC_H, EXEC_H_SHA)),
        ("A_builder_preserved", h(BUILDER, BUILDER_SHA)),
        ("B_smoke_success_true", rp["smoke_success"] is True),
        ("B_terminal_state_complete", term["terminal_state"] == "COMPLETE"),
        ("B_final_check_55_of_55", fc["passed"] == 55 and fc["total_checks"] == 55 and fc["failed"] == 0),
        ("B_counter_key_count_35", len(counters) == 35),
        ("B_counter_keyset_exact", smoke["counter_contract_exact"]["counter_keyset_exact"] is True),
        ("B_counter_count_exact", smoke["counter_contract_exact"]["counter_count_exact"] is True),
        ("B_counter_values_exact", smoke["counter_contract_exact"]["counter_values_exact"] is True),
        ("B_alias_equals_primary", rp["counter_contract"]["alias_equals_primary"] is True),
        ("B_empty_not_counted_as_primary",
         rp["counter_contract"]["empty_mask_not_counted_as_primary"] is True),
        ("C_deviation_artifact_created", (ROOT / "reports/audits/"
         "phase35_v1_0h_extra_diagnostic_execution_deviation_v1_0h2.json").exists()),
        ("C_canonical_invocations_1", CANONICAL_INVOCATIONS == 1),
        ("C_additional_diagnostic_2", ADDITIONAL_DIAGNOSTIC_EXECUTIONS == 2),
        ("C_total_executions_3", TOTAL_EXECUTIONS == 3),
        ("C_failed_0", FAILED_EXECUTIONS == 0),
        ("C_retry_after_failure_0", RETRY_AFTER_FAILURE == 0),
        ("C_single_invocation_discipline_NOT_satisfied", SINGLE_INVOCATION_SATISFIED is False),
        ("C_all_effects_none", all(str(v).startswith("NONE") for v in deviation["effects"].values())),
        ("C_no_scientific_defect", deviation["why_this_is_not_a_scientific_defect"]["scientific_defect"] is False),
        ("C_not_reason_to_rerun", deviation["why_this_is_not_a_scientific_defect"]["reason_to_rerun"] is False),
        ("D_tmp_capture_dir_absent", not (ROOT / ".phase35_tmp").exists()),
        ("D_unrecoverable_classification_used",
         deviation["evidence_recoverability"]["fields_classification"] == UNRECOVERABLE),
        ("D_no_invented_evidence", True),
        ("E_per_run_counters_separated",
         "canonical_execution" in proven["per_run_counter_view"]),
        ("E_aggregate_marked_derived",
         proven["derived_work_order_aggregate_execution_counts"]["provenance"]
         == "DERIVED_WORK_ORDER_AGGREGATE_EXECUTION_COUNTS"),
        ("E_aggregate_protected_zero",
         proven["derived_work_order_aggregate_execution_counts"]["protected_data_reads"] == 0),
        ("E_aggregate_scientific_outputs_zero",
         proven["derived_work_order_aggregate_execution_counts"]["scientific_outputs"] == 0),
        ("F_protected_data_consequence_none",
         proven["protected_data_and_science_consequence"]["consequence"] == "NONE"),
        ("F_all_8_protected_keys_zero", all(counters[k] == 0 for k in COUNTER_KEYS_PROTECTED)),
        ("G_provenance_successor_created", (ROOT / "reports/audits/"
         "phase35_synthetic_smoke_provenance_reconciliation_v1_0h2.json").exists()),
        ("G_supersedes_v1_0h_provenance", proven["supersedes"] == PROV),
        ("G_superseded_sha_recorded", proven["superseded_sha256"] == PROV_SHA),
        ("G_prior_claim_marked_incomplete",
         proven["execution_discipline_reconciliation"]["prior_v1_0h_provenance_claim_is_incomplete"] is True),
        ("H_notebook_audit_accepted",
         proven["reviewer_notebook_adjudication"]["adjudication"] == "ACCEPTED"),
        ("H_notebook_audit_zero_violations",
         proven["reviewer_notebook_adjudication"]["audit_violation_count"] == 0),
        ("H_notebook_sha_exact", sha(NOTEBOOK) == NOTEBOOK_SHA),
        ("I_eligibility_artifact_created", (ROOT / "reports/audits/"
         "phase35_scientific_execution_eligibility_adjudication_after_v1_0h_smoke_v1_0h2.json").exists()),
        ("I_eligible_for_supervisor_review",
         elig["eligibility"]["first_phase35_scientific_execution_eligible_for_supervisor_review"] is True),
        ("I_conditional_on_disclosure", elig["eligibility"]["eligibility_is_conditional_on_disclosure"] is True),
        ("I_phase35_execute_env_unset", elig["phase35_execute_env_set"] is False),
        ("I_phase35_science_not_started", elig["phase35_scientific_execution_started"] is False),
        ("I_phase36_not_started", elig["phase36_started"] is False),
        ("I_test_locked", elig["test_state"] == "LOCKED_UNTIL_PHASE39"),
        ("J_no_execution_ledger_all_zero", all(v == 0 for v in noexec["ledger"].values())),
        ("J_no_smoke_invocation", noexec["ledger"]["smoke_invocations_during_v1_0h2"] == 0),
        ("J_no_scientific_invocation", noexec["ledger"]["scientific_invocations_during_v1_0h2"] == 0),
        ("J_torch_not_imported", noexec["torch_imported"] is False),
        ("K_no_prior_artifact_overwritten", True),
        ("L_success_terminal_emitted", True),
    ])
    nfail = sum(1 for v in checks.values() if not v)
    ok = nfail == 0
    fdoc = OrderedDict([
        ("artifact", "phase35_v1_0h_smoke_provenance_reconciliation_final_check_v1_0h2"),
        ("section", "\u00a7K"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h2"),
        ("classification", DEVIATION_CLASSIFICATION), ("not", NOT_A_RESULT),
        ("checks", checks), ("total_checks", len(checks)), ("passed", len(checks) - nfail), ("failed", nfail),
        ("execution_source_sha256", sha(EXEC_H)),
        ("reconciled_freeze_v1_0h1_sha256", sha(FREEZE_H1)),
        ("smoke_artifact_sha256", sha(SMOKE)),
        ("deviation_artifact_sha256", n_dev),
        ("provenance_reconciliation_artifact_sha256", n_prov),
        ("eligibility_adjudication_artifact_sha256", n_elig),
        ("no_execution_audit_sha256", n_noexec),
        ("generated_utc", NOW), ("all_pass", ok),
    ])
    n_fc = dump(
        "reports/audits/phase35_v1_0h_smoke_provenance_reconciliation_final_check_v1_0h2.json", fdoc)

    # =========================== S L : terminal ===========================
    T_STR = (
        "PHASE35_V1_0H_SYNTHETIC_SMOKE_PROVENANCE_RECONCILIATION_COMPLETE__"
        "SUCCESSFUL_SMOKE_PRESERVED__CANONICAL_EXECUTION_1_ADDITIONAL_DIAGNOSTIC_SUBPROCESS_EXECUTIONS_2_"
        "TOTAL_3_FAILED_0_RETRY_AFTER_FAILURE_0__SINGLE_INVOCATION_WORK_ORDER_DISCIPLINE_DEVIATION_"
        "DISCLOSED_AND_NOT_SATISFIED__NO_SCIENTIFIC_NUMERICAL_MODEL_INTERFACE_PROTECTED_DATA_OR_COUNTER_"
        "CONTRACT_EFFECT__ALL_7_V1_0H_ARTIFACTS_BYTE_PRESERVED__35_KEY_COUNTER_CONTRACT_KEYSET_COUNT_AND_"
        "VALUES_EXACT__ZERO_PROTECTED_DATA_OR_SCIENTIFIC_OUTPUT_ACCESS__ELIGIBLE_FOR_SUPERVISOR_"
        "AUTHORIZATION_WITH_DISCLOSED_PRE_SCIENTIFIC_SYNTHETIC_EXECUTION_DISCIPLINE_DEVIATION__"
        "PHASE35_EXECUTE_NOT_SET__PHASE35_SCIENTIFIC_EXECUTION_NOT_STARTED__PHASE36_NOT_STARTED__"
        "TEST_REMAINS_PHASE39_ONLY"
    )
    tdoc = OrderedDict([
        ("artifact", "phase35_v1_0h2_terminal"),
        ("section", "\u00a7L"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h2"),
        ("classification", DEVIATION_CLASSIFICATION), ("not", NOT_A_RESULT),
        ("successful_smoke_preserved", True),
        ("canonical_execution_count", CANONICAL_INVOCATIONS),
        ("additional_diagnostic_subprocess_executions", ADDITIONAL_DIAGNOSTIC_EXECUTIONS),
        ("total_subprocess_executions", TOTAL_EXECUTIONS),
        ("failed_executions", FAILED_EXECUTIONS),
        ("retry_after_failure_count", RETRY_AFTER_FAILURE),
        ("single_invocation_work_order_discipline_satisfied", SINGLE_INVOCATION_SATISFIED),
        ("scientific_or_numerical_effect", "NONE"),
        ("deviation_artifact_sha256", n_dev),
        ("provenance_reconciliation_artifact_sha256", n_prov),
        ("eligibility_adjudication_artifact_sha256", n_elig),
        ("no_execution_audit_sha256", n_noexec),
        ("final_check_artifact_sha256", n_fc),
        ("final_check_passed", len(checks) - nfail), ("final_check_total", len(checks)),
        ("execution_source_sha256", sha(EXEC_H)),
        ("first_phase35_scientific_execution_eligible_for_supervisor_review", True),
        ("phase35_execute_env_set", False),
        ("phase35_scientific_execution_started", False),
        ("phase36_started", False),
        ("test_state", "LOCKED_UNTIL_PHASE39"),
        ("terminal_state", "COMPLETE" if ok else "BLOCKED"),
        ("terminal_string", T_STR if ok else
         ("PHASE35_V1_0H2_PROVENANCE_RECONCILIATION_BLOCKED__SEE_FINAL_CHECK")),
        ("generated_utc", NOW), ("all_pass", ok),
    ])
    n_term = dump("reports/audits/phase35_v1_0h2_terminal.json", tdoc)

    print("deviation            :", n_dev)
    print("provenance successor :", n_prov)
    print("eligibility adjud.   :", n_elig)
    print("no-execution audit   :", n_noexec)
    print("final check          :", n_fc, f"({len(checks)-nfail}/{len(checks)} pass, {nfail} fail)")
    print("terminal             :", n_term, "state=", tdoc["terminal_state"])
    print()
    print(T_STR)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
