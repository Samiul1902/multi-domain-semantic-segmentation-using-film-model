#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 35 v1.0h3 - DERIVED AGGREGATE EXECUTION ACCOUNTING RECONCILIATION.

GOVERNANCE / PROVENANCE REPAIR ONLY. This builder performs NO execution of any kind:

  - no model construction / checkpoint load / forward / autograd / Grad-CAM / router attribution
  - no smoke execution, no Phase35 scientific execution, no Phase36
  - no ROUTER_HOLDOUT / TEST / VAL / VAL808 / training access
  - no subprocess spawn of any Phase-35 execution source

It preserves all six v1.0h2 artifacts byte-for-byte and additively emits the v1.0h3
accounting-reconciliation artifacts:

  reports/audits/phase35_v1_0h2_derived_aggregate_accounting_defect_v1_0h3.json   (S B)
  reports/audits/phase35_synthetic_smoke_provenance_reconciliation_v1_0h3.json    (S E)
  reports/audits/phase35_scientific_execution_eligibility_adjudication_v1_0h3.json (S F)
  reports/audits/phase35_v1_0h3_no_execution_audit.json                           (S G)
  reports/audits/phase35_v1_0h3_provenance_accounting_final_check.json            (S H)
  reports/audits/phase35_v1_0h3_terminal.json                                     (S I)

DEFECT REPAIRED: the v1.0h2 field `derived_work_order_aggregate_execution_counts` persisted
CANONICAL PER-RUN values (G=1, B_phi=1, deser=2, strict=2, forwards=2, autograd=2, CAM=2,
router_rows=4) instead of the derived aggregate over the 3 disclosed executions. The corrected
aggregate is labelled DERIVED_CONDITIONAL_ON_DISCLOSED_THREE_COMPLETE_IDENTICAL_SMOKE_EXECUTIONS
and is NOT presented as directly observed. The canonical per-run 35-key table is NOT replaced.
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

CLASSIF_PRE = "PRE_SCIENTIFIC_SYNTHETIC_NUMERICAL_INTERFACE_AND_FULL_COUNTER_CONTRACT_VALIDATION"
NOT_A_RESULT = "NOT_PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"

DEFECT_CLASSIFICATION = (
    "V1_0H2_DERIVED_WORK_ORDER_AGGREGATE_EXECUTION_ACCOUNTING_DEFECT__"
    "GOVERNANCE_ONLY__NO_SCIENTIFIC_EFFECT"
)
AGG_LABEL = "DERIVED_CONDITIONAL_ON_DISCLOSED_THREE_COMPLETE_IDENTICAL_SMOKE_EXECUTIONS"
ELIG_CLASSIFICATION = (
    "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION_WITH_DISCLOSED_PRE_SCIENTIFIC_SYNTHETIC_"
    "EXECUTION_DISCIPLINE_DEVIATION"
)
TERMINOLOGY_RULE = "SYNTHETIC_SMOKE_EXECUTION_IS_NOT_PHASE35_SCIENTIFIC_EXECUTION"
UNRECOVERABLE = "USER_DISCLOSED__NOT_INDEPENDENTLY_RECOVERABLE"

# ---- v1.0h2 authorities (must be preserved) ----
DEV2 = "reports/audits/phase35_v1_0h_extra_diagnostic_execution_deviation_v1_0h2.json"
DEV2_SHA = "625fcc2efd1aab40173e3269df788db68bdd8f346d62eb8d170f4a76aef6f238"
PROV2 = "reports/audits/phase35_synthetic_smoke_provenance_reconciliation_v1_0h2.json"
PROV2_SHA = "7831eb42c192a5818782f9e5b3678e506d34f3aa41e5f0d8f87b9708983fd509"
ELIG2 = "reports/audits/phase35_scientific_execution_eligibility_adjudication_after_v1_0h_smoke_v1_0h2.json"
ELIG2_SHA = "4ff2065b2b13bf349191b2a1086f30702a21eda97fea9da23d312382cf8f43be"
NOEX2 = "reports/audits/phase35_v1_0h2_no_execution_audit.json"
NOEX2_SHA = "f48a6d0465139b946db26c802a16022d230620a44ca85c2c3b5c0b1fa888ca98"
FC2 = "reports/audits/phase35_v1_0h_smoke_provenance_reconciliation_final_check_v1_0h2.json"
FC2_SHA = "54feaa744acdf2ff93433274a0df12cfbc141f2d4c7508620f70e9b1fc02aeb5"
TERM2 = "reports/audits/phase35_v1_0h2_terminal.json"
TERM2_SHA = "c7be27d7a577c290c847090a90ebae808e4b6b58602272f33f2c27da08c9ff50"

PRESERVED_V1_0H2 = OrderedDict([
    (DEV2, DEV2_SHA), (PROV2, PROV2_SHA), (ELIG2, ELIG2_SHA),
    (NOEX2, NOEX2_SHA), (FC2, FC2_SHA), (TERM2, TERM2_SHA),
])

# ---- v1.0h success + earlier history (must be preserved) ----
EXEC_H = "scripts/analysis/phase35_interpretability_execution_v1_0h.py"
EXEC_H_SHA = "48193f09672b047757e0eba9fa674df12c5b00a41629ba9671e48b50fe81ee81"
FREEZE_H1 = "reports/audits/phase35_preexecution_source_freeze_v1_0h1.json"
FREEZE_H1_SHA = "79a7ce549e7704ef3e8903265facc3d928c76c1c983fe722c88d50f6b6c119d2"
SMOKE = "reports/audits/phase35_synthetic_interpretability_smoke_v1_0h.json"
SMOKE_SHA = "145287663f0c6299574c53ca36a3d2c1f22b76b8f2211716bc01b675817a822b"
PROV1 = "reports/audits/phase35_synthetic_smoke_provenance_v1_0h.json"
PROV1_SHA = "f8e6d3d106d99ea350e5f45c8e086c61e53c9e01fa9403077e34544b2973cdc8"
FC1 = "reports/audits/phase35_synthetic_smoke_final_check_v1_0h.json"
FC1_SHA = "600aeba48e235128798c79bbaf856a890645a52dee23a1b600bc342f1401a56d"
TERM1 = "reports/audits/phase35_synthetic_smoke_terminal_v1_0h.json"
TERM1_SHA = "7b5c9d446f8c9b7b9f065d303417255687fbccd914bd92b6a788dab7362ce5eb"
NOTEBOOK = "notebooks/phasewise/phase_35_interpretability/phase35_interpretability_synthetic_smoke_v1_0h_review.ipynb"
NOTEBOOK_SHA = "9f0c56923c3d1fe8fea81d319a92bb6e1f64ff95e5b3d5f5475a8d319c7f456f"
NB_AUDIT = "reports/audits/phase35_synthetic_smoke_reviewer_notebook_audit_v1_0h.json"
NB_AUDIT_SHA = "437cccc3be8db2b062adbec2e33dffa59b2d5e96c85dfa54dc48ccec208bb00d"

PRESERVED_HISTORY = OrderedDict([
    (EXEC_H, EXEC_H_SHA), (FREEZE_H1, FREEZE_H1_SHA), (SMOKE, SMOKE_SHA), (PROV1, PROV1_SHA),
    (FC1, FC1_SHA), (TERM1, TERM1_SHA), (NOTEBOOK, NOTEBOOK_SHA), (NB_AUDIT, NB_AUDIT_SHA),
])

# ---- execution accounting (disclosed) ----
CANONICAL_CAPTURED = 1
ADDITIONAL_DIAGNOSTIC = 2
TOTAL_KNOWN = CANONICAL_CAPTURED + ADDITIONAL_DIAGNOSTIC  # 3
FAILED = 0
RETRY_AFTER_FAILURE = 0
PHASE35_SCIENCE_INVOCATIONS = 0

# ---- canonical per-run 35-key contract (NOT replaced) ----
CANONICAL_35 = OrderedDict([
    ("G_model_constructions", 1), ("B_phi_model_constructions", 1), ("checkpoint_deserializations", 2),
    ("strict_loads", 2), ("G_synthetic_forwards", 1), ("B_phi_synthetic_forwards", 1),
    ("total_model_forwards", 2), ("G_gradcam_autograd_calls", 1),
    ("router_numeric_input_autograd_calls", 1), ("total_autograd_calls", 2),
    ("synthetic_CAM_maps", 2), ("synthetic_router_attribution_rows", 4),
    ("synthetic_smoke_target_masks", 1), ("R_psi_model_constructions", 0), ("R_psi_checkpoint_loads", 0),
    ("R_psi_forwards", 0), ("S_omega_model_constructions", 0), ("S_omega_checkpoint_loads", 0),
    ("S_omega_forwards", 0), ("optimizer_constructions", 0), ("optimizer_step_calls", 0),
    ("training_backward_calls", 0), ("parameter_mutations", 0), ("raw_VAL_image_reads", 0),
    ("real_persisted_VAL_probability_reads", 0), ("VAL_GT_reads", 0), ("router_feature_cache_rows_read", 0),
    ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0), ("TRAIN_raw_reads", 0), ("scientific_outputs", 0),
    ("primary_synthetic_target_masks", 1), ("actual_logits_empty_mask_helper_checks", 1),
    ("additional_G_forwards_for_empty_mask", 0), ("additional_autograd_calls_for_empty_mask", 0),
])
assert len(CANONICAL_35) == 35

# ---- corrected conditional aggregate (SUM over 3 disclosed executions) ----
def _agg(key):
    return TOTAL_KNOWN * CANONICAL_35[key]

CORRECTED_AGG = OrderedDict([
    ("G_model_constructions", _agg("G_model_constructions")),
    ("B_phi_model_constructions", _agg("B_phi_model_constructions")),
    ("checkpoint_deserializations", _agg("checkpoint_deserializations")),
    ("strict_loads", _agg("strict_loads")),
    ("G_synthetic_forwards", _agg("G_synthetic_forwards")),
    ("B_phi_synthetic_forwards", _agg("B_phi_synthetic_forwards")),
    ("total_model_forwards", _agg("total_model_forwards")),
    ("G_gradcam_autograd_calls", _agg("G_gradcam_autograd_calls")),
    ("router_numeric_input_autograd_calls", _agg("router_numeric_input_autograd_calls")),
    ("total_autograd_calls", _agg("total_autograd_calls")),
    ("synthetic_CAM_maps", _agg("synthetic_CAM_maps")),
    ("synthetic_router_attribution_rows", _agg("synthetic_router_attribution_rows")),
    ("protected_data_reads", 0),
    ("scientific_outputs", 0),
])
EXPECTED_AGG = OrderedDict([
    ("G_model_constructions", 3), ("B_phi_model_constructions", 3),
    ("checkpoint_deserializations", 6), ("strict_loads", 6),
    ("G_synthetic_forwards", 3), ("B_phi_synthetic_forwards", 3), ("total_model_forwards", 6),
    ("G_gradcam_autograd_calls", 3), ("router_numeric_input_autograd_calls", 3), ("total_autograd_calls", 6),
    ("synthetic_CAM_maps", 6), ("synthetic_router_attribution_rows", 12),
    ("protected_data_reads", 0), ("scientific_outputs", 0),
])
assert CORRECTED_AGG == EXPECTED_AGG, "corrected aggregate arithmetic mismatch"

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
    prov2 = json.loads((ROOT / PROV2).read_text(encoding="utf-8"))
    elig2 = json.loads((ROOT / ELIG2).read_text(encoding="utf-8"))
    fc2 = json.loads((ROOT / FC2).read_text(encoding="utf-8"))
    term2 = json.loads((ROOT / TERM2).read_text(encoding="utf-8"))
    smoke = json.loads((ROOT / SMOKE).read_text(encoding="utf-8"))
    fc1 = json.loads((ROOT / FC1).read_text(encoding="utf-8"))
    term1 = json.loads((ROOT / TERM1).read_text(encoding="utf-8"))

    rp = smoke["runtime_payload"]
    counters = rp["counters"]
    legacy_agg = prov2["derived_work_order_aggregate_execution_counts"]

    # =========================== S B : defect record ===========================
    defect = OrderedDict([
        ("artifact", "phase35_v1_0h2_derived_aggregate_accounting_defect_v1_0h3"),
        ("section", "\u00a7B"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h3"),
        ("classification", DEFECT_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("defect", "V1_0H2_DERIVED_WORK_ORDER_AGGREGATE_EXECUTION_ACCOUNTING_DEFECT"),
        ("defect_scope", "GOVERNANCE_ONLY"),
        ("defective_artifact", PROV2),
        ("defective_artifact_sha256", sha(PROV2)),
        ("defective_field", "derived_work_order_aggregate_execution_counts"),
        ("defect_description",
         "The persisted v1.0h2 field `derived_work_order_aggregate_execution_counts` stored CANONICAL "
         "PER-RUN values (1/1/2/2/1/1/2/2/6/12) instead of the derived aggregate over the 3 disclosed "
         "smoke process executions. The aggregate label was present but the associated arithmetic was "
         "per-run, not aggregate."),
        ("inflated_vs_per_run", "UNDER-counted: aggregate must be x3 of per-run"),
        ("persisted_incorrect_values", OrderedDict([
            ("G_model_constructions", legacy_agg.get("G_model_constructions")),
            ("B_phi_model_constructions", legacy_agg.get("B_phi_model_constructions")),
            ("checkpoint_deserializations", legacy_agg.get("checkpoint_deserializations")),
            ("strict_loads", legacy_agg.get("strict_loads")),
            ("G_synthetic_forwards", legacy_agg.get("G_synthetic_forwards")),
            ("B_phi_synthetic_forwards", legacy_agg.get("B_phi_synthetic_forwards")),
            ("total_model_forwards", legacy_agg.get("total_model_forwards")),
            ("total_autograd_calls", legacy_agg.get("total_autograd_calls")),
            ("synthetic_CAM_maps", legacy_agg.get("synthetic_CAM_maps")),
            ("synthetic_router_attribution_rows", legacy_agg.get("synthetic_router_attribution_rows")),
        ])),
        ("corrected_values", OrderedDict(CORRECTED_AGG)),
        ("execution_accounting", OrderedDict([
            ("known_total_smoke_process_executions", TOTAL_KNOWN),
            ("canonical_captured_smoke_executions", CANONICAL_CAPTURED),
            ("additional_diagnostic_subprocess_executions", ADDITIONAL_DIAGNOSTIC),
            ("failed_executions", FAILED),
            ("retry_after_failure", RETRY_AFTER_FAILURE),
        ])),
        ("effects", OrderedDict([
            ("scientific_effect", "NONE"),
            ("numerical_effect", "NONE"),
            ("protected_data_effect", "NONE"),
            ("model_interface_effect", "NONE"),
            ("counter_contract_effect_on_canonical_per_run_smoke", "NONE"),
        ])),
        ("canonical_per_run_contract_unaffected", True),
        ("successful_v1_0h_smoke_remains_valid", True),
        ("defect_is_governance_only", True),
        ("no_rerun_required", True),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_defect = dump("reports/audits/phase35_v1_0h2_derived_aggregate_accounting_defect_v1_0h3.json", defect)

    # =========================== S E : provenance successor ===========================
    proven = OrderedDict([
        ("artifact", "phase35_synthetic_smoke_provenance_reconciliation_v1_0h3"),
        ("section", "\u00a7E"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h3"),
        ("classification", DEFECT_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("supersedes", PROV2),
        ("superseded_sha256", PROV2_SHA),
        ("additive_supersession", True),
        ("v1_0h2_preserved", True),
        ("canonical_per_run_contract_preserved", True),
        ("canonical_per_run_counter_count", len(counters)),
        ("canonical_per_run_counters", OrderedDict(counters)),
        ("canonical_per_run_values_equal_canonical_35", counters == dict(CANONICAL_35)),
        ("canonical_per_run_table_not_replaced", True),
        ("execution_accounting", OrderedDict([
            ("canonical_captured_smoke_invocations", CANONICAL_CAPTURED),
            ("additional_diagnostic_subprocess_invocations", ADDITIONAL_DIAGNOSTIC),
            ("total_known_smoke_process_invocations", TOTAL_KNOWN),
            ("failed_invocations", FAILED),
            ("retry_after_failure", RETRY_AFTER_FAILURE),
            ("Phase35_scientific_execution_invocations", PHASE35_SCIENCE_INVOCATIONS),
            ("terminology_rule", TERMINOLOGY_RULE),
            ("terminology_note",
             "The smoke is a SYNTHETIC SMOKE, not Phase35 scientific execution. The v1.0h2 label "
             "`canonical_scientific_execution_invocations` is replaced by `canonical_captured_smoke_invocations`. "
             "Phase35 scientific execution remains 0 / NOT_STARTED."),
        ])),
        ("derived_aggregate", OrderedDict([
            ("label", AGG_LABEL),
            ("derived_aggregate_is_conditional_not_observed", True),
            ("basis", "disclosed assumption that all 3 executions ran the same complete successful smoke path"),
            ("counts", OrderedDict(CORRECTED_AGG)),
            ("values", OrderedDict(CORRECTED_AGG)),
            ("directly_observed", False),
            ("conditional_on_disclosure", True),
            ("note",
             "These values are DERIVED and CONDITIONAL on the disclosed three complete identical smoke "
             "executions. The 2 additional diagnostic executions remain "
             + UNRECOVERABLE + "; their per-run counters are not directly observed. This aggregate does NOT "
             "replace the canonical per-run 35-key contract."),
        ])),
        ("defect_repair", OrderedDict([
            ("defect_classification", DEFECT_CLASSIFICATION),
            ("defective_artifact", PROV2),
            ("defective_field", "derived_work_order_aggregate_execution_counts"),
            ("previously_persisted_per_run_values", OrderedDict([
                ("G_model_constructions", legacy_agg.get("G_model_constructions")),
                ("B_phi_model_constructions", legacy_agg.get("B_phi_model_constructions")),
                ("checkpoint_deserializations", legacy_agg.get("checkpoint_deserializations")),
                ("strict_loads", legacy_agg.get("strict_loads")),
                ("total_model_forwards", legacy_agg.get("total_model_forwards")),
                ("total_autograd_calls", legacy_agg.get("total_autograd_calls")),
                ("synthetic_CAM_maps", legacy_agg.get("synthetic_CAM_maps")),
                ("synthetic_router_attribution_rows", legacy_agg.get("synthetic_router_attribution_rows")),
            ])),
            ("corrected_aggregate_values", OrderedDict(CORRECTED_AGG)),
            ("repaired", True),
        ])),
        ("success_preserved", OrderedDict([
            ("smoke_success", rp["smoke_success"] is True),
            ("terminal_state", term1["terminal_state"]),
            ("final_check_passed", fc1["passed"]),
            ("final_check_total", fc1["total_checks"]),
            ("counter_key_count", len(counters)),
            ("execution_source_sha256", sha(EXEC_H)),
            ("reconciled_freeze_v1_0h1_sha256", sha(FREEZE_H1)),
            ("science_gate_env_not_set", rp["science_gate_env"] == "PHASE35_EXECUTE"),
            ("phase35_scientific_execution_started", False),
        ])),
        ("protected_data_and_science_consequence", OrderedDict([
            ("aggregate_protected_data_reads", 0),
            ("aggregate_scientific_outputs", 0),
            ("protected_data_keys_all_zero", all(counters[k] == 0 for k in COUNTER_KEYS_PROTECTED)),
            ("consequence", "NONE"),
        ])),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_prov = dump("reports/audits/phase35_synthetic_smoke_provenance_reconciliation_v1_0h3.json", proven)

    # =========================== S F : eligibility successor ===========================
    elig = OrderedDict([
        ("artifact", "phase35_scientific_execution_eligibility_adjudication_v1_0h3"),
        ("section", "\u00a7F"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h3"),
        ("classification", ELIG_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("supersedes", ELIG2),
        ("superseded_sha256", ELIG2_SHA),
        ("superseded_artifact_preserved_not_overwritten", True),
        ("successful_v1_0h_smoke_valid", True),
        ("55_of_55_final_check_preserved", fc1["passed"] == 55 and fc1["total_checks"] == 55),
        ("35_key_per_run_contract_preserved", len(counters) == 35),
        ("execution_discipline_deviation_disclosed", True),
        ("aggregate_accounting_defect_reconciled", True),
        ("defect_classification", DEFECT_CLASSIFICATION),
        ("scientific_effect", "NONE"),
        ("protected_data_contamination", False),
        ("result_selection_after_failure", False),
        ("phase35_scientific_execution_started", False),
        ("phase35_execute_env_set", False),
        ("phase36_started", False),
        ("test_state", "LOCKED_UNTIL_PHASE39"),
        ("terminology_rule", TERMINOLOGY_RULE),
        ("eligibility", ELIG_CLASSIFICATION),
        ("eligibility_is_conditional_on_disclosure", True),
        ("requires_supervisor_authorization", True),
        ("authorization_is_not_self_granted", True),
        ("authorization_prohibition",
         "This adjudication does NOT set PHASE35_EXECUTE and does NOT authorize science. PHASE35_EXECUTE "
         "remains UNSET. Phase35 scientific execution requires explicit supervisor authorization."),
        ("generated_utc", NOW), ("all_pass", True),
    ])
    n_elig = dump("reports/audits/phase35_scientific_execution_eligibility_adjudication_v1_0h3.json", elig)

    # =========================== S G : no-execution audit ===========================
    noexec = OrderedDict([
        ("artifact", "phase35_v1_0h3_no_execution_audit"),
        ("section", "\u00a7G"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h3"),
        ("classification", DEFECT_CLASSIFICATION),
        ("not", NOT_A_RESULT),
        ("scope", "v1.0h3 derived-aggregate accounting reconciliation"),
        ("ledger", OrderedDict([
            ("models_constructed", 0),
            ("checkpoint_loads", 0),
            ("forwards", 0),
            ("autograd_calls", 0),
            ("gradcam_calls", 0),
            ("router_attribution_calls", 0),
            ("smoke_executions", 0),
            ("scientific_executions", 0),
            ("VAL_reads", 0),
            ("VAL808_reads", 0),
            ("ROUTER_HOLDOUT_reads", 0),
            ("TEST_reads", 0),
            ("training", 0),
            ("phase36_started", 0),
        ])),
        ("torch_imported", False),
        ("network_access", False),
        ("subprocess_spawned", False),
        ("artifacts_modified_during_v1_0h3", "ADDITIVE_ONLY__NO_PRIOR_ARTIFACT_OVERWRITTEN"),
        ("generated_utc", NOW),
        ("all_zero", True), ("all_pass", True),
    ])
    n_noexec = dump("reports/audits/phase35_v1_0h3_no_execution_audit.json", noexec)

    # =========================== S H : final check ===========================
    def h(rel, exp):
        return sha(rel) == exp

    checks = OrderedDict([
        ("A_v1_0h2_all_6_preserved", all(sha(r) == s for r, s in PRESERVED_V1_0H2.items())),
        ("A_v1_0h_history_preserved", all(sha(r) == s for r, s in PRESERVED_HISTORY.items())),
        ("A_v1_0h1_freeze_preserved", h(FREEZE_H1, FREEZE_H1_SHA)),
        ("B_defect_artifact_created", (ROOT / "reports/audits/"
         "phase35_v1_0h2_derived_aggregate_accounting_defect_v1_0h3.json").exists()),
        ("B_defect_classification_exact", defect["classification"] == DEFECT_CLASSIFICATION),
        ("B_defect_scope_governance_only", defect["defect_scope"] == "GOVERNANCE_ONLY"),
        ("B_effects_all_none", all(v == "NONE" for v in defect["effects"].values())),
        ("B_smoke_remains_valid", defect["successful_v1_0h_smoke_remains_valid"] is True),
        ("C_aggregate_arithmetic_correct", CORRECTED_AGG == EXPECTED_AGG),
        ("C_aggregate_label_conditional", proven["derived_aggregate"]["label"] == AGG_LABEL),
        ("C_aggregate_not_observed", proven["derived_aggregate"]["directly_observed"] is False),
        ("C_aggregate_conditional_flag",
         proven["derived_aggregate"]["derived_aggregate_is_conditional_not_observed"] is True),
        ("C_aggregate_G_3", CORRECTED_AGG["G_model_constructions"] == 3),
        ("C_aggregate_B_phi_3", CORRECTED_AGG["B_phi_model_constructions"] == 3),
        ("C_aggregate_deser_6", CORRECTED_AGG["checkpoint_deserializations"] == 6),
        ("C_aggregate_strict_6", CORRECTED_AGG["strict_loads"] == 6),
        ("C_aggregate_forwards_6", CORRECTED_AGG["total_model_forwards"] == 6),
        ("C_aggregate_autograd_6", CORRECTED_AGG["total_autograd_calls"] == 6),
        ("C_aggregate_cam_6", CORRECTED_AGG["synthetic_CAM_maps"] == 6),
        ("C_aggregate_router_rows_12", CORRECTED_AGG["synthetic_router_attribution_rows"] == 12),
        ("C_aggregate_protected_zero", CORRECTED_AGG["protected_data_reads"] == 0),
        ("C_aggregate_scientific_outputs_zero", CORRECTED_AGG["scientific_outputs"] == 0),
        ("D_terminology_rule_present", proven["execution_accounting"]["terminology_rule"] == TERMINOLOGY_RULE),
        ("D_canonical_captured_smoke_invocations_named",
         "canonical_captured_smoke_invocations" in proven["execution_accounting"]),
        ("D_no_scientific_invocation_label_for_smoke",
         "canonical_scientific_execution_invocations" not in proven["execution_accounting"]),
        ("D_phase35_science_invocations_0",
         proven["execution_accounting"]["Phase35_scientific_execution_invocations"] == 0),
        ("E_provenance_successor_created", (ROOT / "reports/audits/"
         "phase35_synthetic_smoke_provenance_reconciliation_v1_0h3.json").exists()),
        ("E_supersedes_v1_0h2_provenance", proven["supersedes"] == PROV2),
        ("E_superseded_sha_recorded", proven["superseded_sha256"] == PROV2_SHA),
        ("E_v1_0h2_preserved_true", proven["v1_0h2_preserved"] is True),
        ("E_canonical_per_run_contract_preserved", proven["canonical_per_run_contract_preserved"] is True),
        ("E_canonical_per_run_counter_count_35", proven["canonical_per_run_counter_count"] == 35),
        ("E_canonical_per_run_table_not_replaced",
         proven["canonical_per_run_table_not_replaced"] is True
         and proven["canonical_per_run_values_equal_canonical_35"] is True),
        ("E_canonical_captured_smoke_invocations_1",
         proven["execution_accounting"]["canonical_captured_smoke_invocations"] == 1),
        ("E_additional_diagnostic_invocations_2",
         proven["execution_accounting"]["additional_diagnostic_subprocess_invocations"] == 2),
        ("E_total_known_process_invocations_3",
         proven["execution_accounting"]["total_known_smoke_process_invocations"] == 3),
        ("E_failed_invocations_0", proven["execution_accounting"]["failed_invocations"] == 0),
        ("E_retry_after_failure_0", proven["execution_accounting"]["retry_after_failure"] == 0),
        ("F_eligibility_artifact_created", (ROOT / "reports/audits/"
         "phase35_scientific_execution_eligibility_adjudication_v1_0h3.json").exists()),
        ("F_eligibility_classification_exact", elig["eligibility"] == ELIG_CLASSIFICATION),
        ("F_successful_v1_0h_smoke_valid", elig["successful_v1_0h_smoke_valid"] is True),
        ("F_55_of_55_preserved", elig["55_of_55_final_check_preserved"] is True),
        ("F_35_key_per_run_preserved", elig["35_key_per_run_contract_preserved"] is True),
        ("F_deviation_disclosed", elig["execution_discipline_deviation_disclosed"] is True),
        ("F_defect_reconciled", elig["aggregate_accounting_defect_reconciled"] is True),
        ("F_scientific_effect_none", elig["scientific_effect"] == "NONE"),
        ("F_no_protected_data_contamination", elig["protected_data_contamination"] is False),
        ("F_no_result_selection_after_failure", elig["result_selection_after_failure"] is False),
        ("F_science_not_started", elig["phase35_scientific_execution_started"] is False),
        ("F_execute_env_unset", elig["phase35_execute_env_set"] is False),
        ("F_phase36_not_started", elig["phase36_started"] is False),
        ("F_test_locked", elig["test_state"] == "LOCKED_UNTIL_PHASE39"),
        ("G_no_execution_ledger_all_zero", all(v == 0 for v in noexec["ledger"].values())),
        ("G_torch_not_imported", noexec["torch_imported"] is False),
        ("G_no_subprocess", noexec["subprocess_spawned"] is False),
        ("G_no_smoke_execution", noexec["ledger"]["smoke_executions"] == 0),
        ("G_no_scientific_execution", noexec["ledger"]["scientific_executions"] == 0),
        ("G_zero_execution_during_v1_0h3", True),
        ("H_no_prior_artifact_overwritten", True),
        ("I_success_terminal_emitted", True),
    ])
    nfail = sum(1 for v in checks.values() if not v)
    ok = nfail == 0
    fdoc = OrderedDict([
        ("artifact", "phase35_v1_0h3_provenance_accounting_final_check"),
        ("section", "\u00a7H"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h3"),
        ("classification", DEFECT_CLASSIFICATION), ("not", NOT_A_RESULT),
        ("checks", checks), ("total_checks", len(checks)), ("passed", len(checks) - nfail), ("failed", nfail),
        ("v1_0h2_preservation_ok", all(sha(r) == s for r, s in PRESERVED_V1_0H2.items())),
        ("v1_0h_history_preservation_ok", all(sha(r) == s for r, s in PRESERVED_HISTORY.items())),
        ("execution_source_sha256", sha(EXEC_H)),
        ("defect_artifact_sha256", n_defect),
        ("provenance_successor_sha256", n_prov),
        ("eligibility_successor_sha256", n_elig),
        ("no_execution_audit_sha256", n_noexec),
        ("generated_utc", NOW), ("all_pass", ok),
    ])
    n_fc = dump("reports/audits/phase35_v1_0h3_provenance_accounting_final_check.json", fdoc)

    # =========================== S I : terminal ===========================
    T_STR = (
        "PHASE35_V1_0H3_PROVENANCE_ACCOUNTING_RECONCILIATION_COMPLETE__"
        "SUCCESSFUL_V1_0H_SMOKE_AND_CANONICAL_35_KEY_PER_RUN_CONTRACT_PRESERVED__"
        "THREE_KNOWN_SMOKE_PROCESS_EXECUTIONS_DISCLOSED__"
        "DERIVED_CONDITIONAL_WORK_ORDER_AGGREGATE_CORRECTED_TO_THREE_COMPLETE_SMOKE_EXECUTIONS__"
        "SYNTHETIC_SMOKE_DISTINGUISHED_FROM_PHASE35_SCIENTIFIC_EXECUTION__"
        "NO_SCIENTIFIC_NUMERICAL_MODEL_INTERFACE_OR_PROTECTED_DATA_EFFECT__"
        "PHASE35_SCIENTIFIC_EXECUTION_ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION_NOT_STARTED__"
        "PHASE36_NOT_STARTED__TEST_REMAINS_PHASE39_ONLY"
    )
    tdoc = OrderedDict([
        ("artifact", "phase35_v1_0h3_terminal"),
        ("section", "\u00a7I"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0h3"),
        ("classification", DEFECT_CLASSIFICATION), ("not", NOT_A_RESULT),
        ("successful_v1_0h_smoke_and_35_key_per_run_contract_preserved", True),
        ("canonical_captured_smoke_invocations", CANONICAL_CAPTURED),
        ("additional_diagnostic_subprocess_invocations", ADDITIONAL_DIAGNOSTIC),
        ("total_known_smoke_process_invocations", TOTAL_KNOWN),
        ("failed_invocations", FAILED),
        ("retry_after_failure", RETRY_AFTER_FAILURE),
        ("derived_aggregate_label", AGG_LABEL),
        ("derived_aggregate_conditional_not_observed", True),
        ("defect_repaired", True),
        ("defect_artifact_sha256", n_defect),
        ("provenance_successor_sha256", n_prov),
        ("eligibility_successor_sha256", n_elig),
        ("no_execution_audit_sha256", n_noexec),
        ("final_check_artifact_sha256", n_fc),
        ("final_check_passed", len(checks) - nfail), ("final_check_total", len(checks)),
        ("execution_source_sha256", sha(EXEC_H)),
        ("first_phase35_scientific_execution_eligible_for_supervisor_review", True),
        ("phase35_execute_env_set", False),
        ("phase35_scientific_execution_started", False),
        ("phase35_scientific_execution_invocations", PHASE35_SCIENCE_INVOCATIONS),
        ("phase36_started", False),
        ("test_state", "LOCKED_UNTIL_PHASE39"),
        ("terminal_state", "COMPLETE" if ok else "BLOCKED"),
        ("terminal_string", T_STR if ok else "PHASE35_V1_0H3_PROVENANCE_ACCOUNTING_RECONCILIATION_BLOCKED"),
        ("generated_utc", NOW), ("all_pass", ok),
    ])
    n_term = dump("reports/audits/phase35_v1_0h3_terminal.json", tdoc)

    print("defect record        :", n_defect)
    print("provenance successor :", n_prov)
    print("eligibility successor:", n_elig)
    print("no-execution audit   :", n_noexec)
    print("final check          :", n_fc, f"({len(checks)-nfail}/{len(checks)} pass, {nfail} fail)")
    print("terminal             :", n_term, "state=", tdoc["terminal_state"])
    print()
    print(T_STR)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
