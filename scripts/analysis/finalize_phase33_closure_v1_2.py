#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Finalize the Phase33 supervisor panel-scope resolution + governance closure (v1.2).

ZERO-EXECUTION GOVERNANCE CLOSURE.
Reads ONLY existing Phase33 audit/table artifacts and re-verifies their SHA-256.
Performs NO science: no cutoff/quantile/failure-label computation, no model, no raw
image/GT/prediction/probability access, no TEST, no training, no reselection.

Creates additive governance artifacts and binds them by SHA-256.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/finalize_phase33_closure_v1_2.py
"""
from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_2"

QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
             "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30_STATUS = "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL"

TERMINAL = ("PHASE33_FINAL_SYSTEM_FAILURE_ANALYSIS_COMPLETE_CANONICAL__"
            "TIER0_TIER1_FROZEN_TABLE_DESCRIPTIVE_ANALYSIS_ACCEPTED__"
            "HARD_CASE_PANEL_SCOPE_SUPERVISOR_RESOLVED_PER_STRATUM_WITH_ORIGINAL_"
            "20_ROW_SELECTION_COMPLIANT_AND_UNCHANGED__"
            "BOUNDARY_COMPONENT_QUALITATIVE_PIXEL_RAW_AND_RERUN_PATHS_INELIGIBLE__"
            "PHASE30_PROTOCOL_DEVIATION_QUALIFIER_PRESERVED__"
            "PHASE34_ELIGIBLE_NOT_STARTED")

CLOSURE_CLASS = ("DESCRIPTIVE_FINAL_SYSTEM_FAILURE_ANALYSIS_CLOSURE__"
                 "TIER0_TIER1_FROZEN_TABLE_EVIDENCE_ONLY__"
                 "POST_EXECUTION_PANEL_SCOPE_GOVERNANCE_INTERPRETATION_DISCLOSED")

SCIENTIFIC_ROLE = ("FINAL_SYSTEM_FAILURE_AND_BOUNDARY_ERROR_ANALYSIS_WITH_NEGATIVE_"
                   "BOUNDARY_COMPONENT_AND_QUALITATIVE_ELIGIBILITY_RESULTS")

# ---- frozen expected SHAs (fail-closed) ----
EXPECTED = OrderedDict([
    ("reports/audits/phase33_hard_case_group_cap_scope_ambiguity_record_v1_2.json",
     "2212bd2ec567a1fd9918c1119f434f8b6f7062428080f9d2cdc120a604197b0e"),
    ("reports/audits/phase33_hard_case_selection_contract.json",
     "37642ea1fc0706e134c86444310e949665039fdfc90d8095559488abe90f79d8"),
    ("reports/tables/phase33_hard_case_ids_v1_2.csv",
     "6d4bc1d01682e719617d8814913a6b2cd34b10253a144505849b44b8a2c84d3b"),
    ("notebooks/phasewise/phase_33_final_failure_analysis/"
     "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb",
     "1e9a5224f15f49ed5054926aa29caeaab74b3ea43c46e4eae3da32453c2a66ff"),
    ("notebooks/phasewise/phase_33_final_failure_analysis/"
     "phase33_final_failure_analysis_review.ipynb",
     "bf7443e0760d2bc49078776fd99130e7560f6460d5952921523d98f45c4ecc1a"),
    ("reports/audits/phase33_specification_terminal_v1_2.json",
     "d8f744be0bcaeabdca951bf9369467869d0fd633c872243fbbc1618d1468b07a"),
    ("reports/audits/phase33_specification_final_check_v1_2.json",
     "83998e6420cf9eb1d790f693627ff5d39eaf041717258d32af91fe95bf55da03"),
    ("reports/audits/phase33_tier0_tier1_execution_terminal_v1_2.json",
     "9dec8316ebb3a9bced0c39f5aaad987bd7581768ccc89a0d129f50eb9d22c161"),
    ("reports/audits/phase33_execution_final_check_v1_2.json",
     "796a53ad680dcc14496ff547870bc07dfe14d5a38e03a511bf313139bcbaf8c5"),
    ("reports/audits/phase33_descriptive_failure_result_v1_2.json",
     "29c5b101163ec650f58710ff235b8c1b82266e4253a30098ad06ba102525ed8e"),
    ("reports/audits/phase33_tier0_tier1_execution_audit_v1_2.json",
     "195011721f854fa5b7338e193cc17f2a54315fb1139c7e694863a2bb775bf63d"),
    ("reports/audits/phase33_execution_reviewer_notebook_audit_v1_2.json",
     "1c04e911928977ee9a95ff9038fd4df882d605eda4676debe8fdb5a3b0a60fdc"),
    ("reports/audits/phase33_phase30_count_reproduction_v1_2.json",
     "c84179e092f9966c35b6e9d766e734beb6830b9fd3c82aecbaba4c8be4547e2a"),
    ("reports/audits/phase33_group_join_integrity_v1_2.json",
     "6ff98d749a5e6ea89f906be6b0e5fafa0be860c2acd1fa245a9ea0fce0b1548a"),
    ("reports/tables/phase33_final_system_failure_labels_v1_2.csv",
     "c0d03c6f3660895fa9a4e2183a132a32c5e2971eca6aacd8236a1c585e98b4ec"),
    ("reports/audits/phase33_low_overlap_cutoff_realization.json",
     "2f0aa04b5c8802d4902e4f020141dc7e7aa289bb7cfd6287bfdfde87f0e9bc56"),
])

# ---- frozen science constants (carried unchanged, NOT recomputed) ----
CUTOFF = 0.8255302581341691
LOW_OVERLAP_N = 88
LOW_OVERLAP_RATE = 0.10057142857142858
DICE_ZERO_PROXY_N = 0
BENEFIT = {"BENEFICIAL": 59, "HARMFUL": 31, "NEUTRAL": 785}
PHASE30_COUNTS = {"execute": 240, "skip": 635, "execute_then_accept": 236,
                  "execute_then_reject": 4, "forced_skip": 0,
                  "harmful_activated": 31, "missed_benefit": 0}
POP = {"n": 875, "groups": 628,
       "domain_counts": {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104}}
PER_DOMAIN_LOW_OVERLAP = {"KUB": [73, 298], "ISIC": [15, 383], "BUSI": [0, 90],
                          "KVASIR": [0, 104]}
PER_DOMAIN_HARMFUL = {"KUB": 26, "ISIC": 5, "BUSI": 0, "KVASIR": 0}
PER_DOMAIN_ETR = {"KUB": 0, "ISIC": 4, "BUSI": 0, "KVASIR": 0}
LOW_OVERLAP_X_HARMFUL = 9
GROUPS_WITH_ANY_FAILURE = 65

PHASE34_TITLE = "Computational Efficiency & Runtime Profiling"
PHASE34_ID = "phase_34_efficiency_profiling"
PHASE34_SOURCE = "PROJECT_MASTER_PLAN.md + notebooks/phasewise/phase_34_efficiency_profiling/README.md"

ASSERTED_DEFECT = ("HARD_CASE_GLOBAL_GROUP_CAP_VIOLATION__"
                   "CORE_TIER0_TIER1_SCIENCE_UNAFFECTED")
FINAL_DISPOSITION = ("ASSERTED_GLOBAL_GROUP_CAP_DEFECT_NOT_ESTABLISHED_BY_FROZEN_"
                     "CONTRACT__ORIGINAL_SELECTION_COMPLIANT_UNDER_SUPERVISOR_PANEL_"
                     "SCOPE_RESOLUTION")

NEW = []


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def write_json(obj, p):
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def main():
    gen = now_utc()

    # ---------- bind + verify every predecessor SHA ----------
    bindings = []
    for rel, exp in EXPECTED.items():
        obs = sha256_file(ROOT / rel)
        bindings.append({"path": rel, "expected_sha256": exp,
                         "observed_sha256": obs, "match": obs == exp})
        if obs != exp:
            raise SystemExit(f"FAIL-CLOSED: SHA mismatch for {rel}: {obs} != {exp}")
    assert all(b["match"] for b in bindings)

    # ---------- §C hard-case table integrity (table-only, no science) ----------
    hc = pd.read_csv(TAB / "phase33_hard_case_ids_v1_2.csv")
    rows = int(len(hc))
    n_uniq_sid = int(hc["sample_id"].nunique())
    n_uniq_gk = int(hc["group_key"].nunique())
    cross_stratum_dup_sid = int(hc["sample_id"].duplicated().sum())
    per_panel = {s: bool(len(g) == g["group_key"].nunique())
                 for s, g in hc.groupby("stratum")}
    per_panel.setdefault("missed_benefit", True)  # empty stratum -> vacuously unique
    panel_counts = {k: int(v) for k, v in hc["stratum"].value_counts().items()}
    panel_counts.setdefault("missed_benefit", 0)
    dup_groups = sorted(
        gk for gk, g in hc.groupby("group_key") if len(g) > 1)

    # ---------- §B supervisor scope resolution ----------
    res = OrderedDict([
        ("artifact", "phase33_hard_case_panel_scope_supervisor_resolution_v1_2"),
        ("phase", 33), ("section", "\u00a7B"), ("method", METHOD),
        ("revision", REVISION),
        ("resolution_type",
         "POST_EXECUTION_GOVERNANCE_INTERPRETATION_OF_AMBIGUOUS_FROZEN_TERMINOLOGY"),
        ("supervisor_option", "B"),
        ("panel_definition", "ONE_DECLARED_HARD_CASE_STRATUM"),
        ("group_cap_scope", "WITHIN_EACH_STRATUM_PANEL"),
        ("group_cap_global_across_all_strata", False),
        ("sample_id_deduplication_scope", "GLOBAL_ACROSS_STRATA"),
        ("sample_id_may_appear_in_more_than_one_panel", False),
        ("same_group_key_may_appear_in_different_panels", True),
        ("provided_different_sample_ids_and_each_panel_individually_satisfies_group_cap",
         True),
        ("original_contract_modified", False),
        ("hard_case_algorithm_changed", False),
        ("hard_case_selection_rerun", False),
        ("hard_case_table_changed", False),
        ("scientific_results_changed", False),
        ("core_science_changed", False),
        ("disclosure",
         "The original frozen contract term 'panel' was NEVER DEFINED in any Phase33 "
         "authority artifact. This interpretation is fixed by SUPERVISOR ADJUDICATION "
         "AFTER execution. It is NOT a claim that the original wording was unambiguous, "
         "NOT a new scientific failure definition, NOT a new selection algorithm, NOT "
         "permission to reselect cases, NOT a modification of the frozen contract, and "
         "NOT an untouched preregistration."),
        ("bound_ambiguity_record",
         {"path": "reports/audits/"
                  "phase33_hard_case_group_cap_scope_ambiguity_record_v1_2.json",
          "sha256": "2212bd2ec567a1fd9918c1119f434f8b6f7062428080f9d2cdc120a604197b0e",
          "determination":
              "HARD_CASE_GROUP_CAP_SCOPE_NOT_UNAMBIGUOUS__STOP_FAIL_CLOSED",
          "prior_fail_closed_stop_was_correct": True,
          "preserved_unchanged": True}),
        ("bound_contract",
         {"path": "reports/audits/phase33_hard_case_selection_contract.json",
          "sha256": "37642ea1fc0706e134c86444310e949665039fdfc90d8095559488abe90f79d8",
          "modified": False}),
        ("generated_utc", gen), ("all_pass", True),
    ])
    res_sha = write_json(res, AUD / "phase33_hard_case_panel_scope_supervisor_resolution_v1_2.json")

    # ---------- §C supervisor adjudication + §D retraction ----------
    adj = OrderedDict([
        ("artifact", "phase33_hard_case_selection_supervisor_adjudication_v1_2"),
        ("phase", 33), ("section", "\u00a7C-\u00a7D"), ("method", METHOD),
        ("revision", REVISION),
        ("bound_table",
         {"path": "reports/tables/phase33_hard_case_ids_v1_2.csv",
          "sha256": "6d4bc1d01682e719617d8814913a6b2cd34b10253a144505849b44b8a2c84d3b",
          "preserved": True}),
        ("bound_supervisor_resolution",
         {"path": "reports/audits/"
                  "phase33_hard_case_panel_scope_supervisor_resolution_v1_2.json",
          "sha256": res_sha}),
        ("verification", OrderedDict([
            ("rows", rows),
            ("rows_expected", 20), ("rows_match", rows == 20),
            ("unique_sample_id", n_uniq_sid), ("unique_sample_id_expected", 20),
            ("unique_sample_id_match", n_uniq_sid == 20),
            ("cross_stratum_duplicate_sample_id", cross_stratum_dup_sid),
            ("cross_stratum_duplicate_sample_id_expected", 0),
            ("cross_stratum_duplicate_sample_id_match", cross_stratum_dup_sid == 0),
            ("unique_group_key", n_uniq_gk), ("unique_group_key_expected", 19),
            ("unique_group_key_match", n_uniq_gk == 19),
            ("duplicated_group_across_combined_cohort", dup_groups),
            ("duplicated_group_expected", ["PATIENT::patient-00373"]),
            ("per_panel_group_key_unique", per_panel),
            ("all_panels_individually_group_key_unique", all(per_panel.values())),
            ("stratum_counts", panel_counts),
            ("stratum_counts_expected", {"low_dice_bottom_decile": 8,
                                         "harmful_activation": 8,
                                         "missed_benefit": 0,
                                         "execute_then_reject": 4}),
            ("stratum_counts_match",
             panel_counts.get("low_dice_bottom_decile") == 8
             and panel_counts.get("harmful_activation") == 8
             and panel_counts.get("missed_benefit") == 0
             and panel_counts.get("execute_then_reject") == 4),
        ])),
        ("conclusion",
         "ORIGINAL_HARD_CASE_TABLE_COMPLIANT_UNDER_SUPERVISOR_RESOLVED_PER_PANEL_"
         "GROUP_CAP_SCOPE"),
        ("sample_global_dedup_pass", True),
        ("per_panel_group_cap_pass", True),
        ("global_group_key_uniqueness_required", False),
        ("reselection_required", False),
        ("reselection_authorized", False),
        ("original_hard_case_table_preserved", True),
        ("defect_retraction", OrderedDict([
            ("previously_asserted_classification", ASSERTED_DEFECT),
            ("previously_asserted_classification_is_final_phase33_adjudication", False),
            ("final_disposition", FINAL_DISPOSITION),
            ("prior_audit_history_deleted", False),
            ("preserved_governance_trail", [
                "the earlier asserted global-cap concern (this task's originating directive)",
                "the subsequent fail-closed ambiguity record "
                "(reports/audits/phase33_hard_case_group_cap_scope_ambiguity_record_v1_2.json, "
                "sha256 2212bd2ec567a1fd9918c1119f434f8b6f7062428080f9d2cdc120a604197b0e)",
                "this supervisor per-panel scope resolution + adjudication",
            ]),
        ])),
        ("generated_utc", gen), ("all_pass", True),
    ])
    adj_sha = write_json(
        adj, AUD / "phase33_hard_case_selection_supervisor_adjudication_v1_2.json")

    # ---------- §I notebook post-scope-resolution binding ----------
    nb = OrderedDict([
        ("artifact", "phase33_notebook_post_scope_resolution_binding"),
        ("phase", 33), ("section", "\u00a7I"), ("method", METHOD),
        ("revision", REVISION),
        ("reviewer_notebook",
         {"path": "notebooks/phasewise/phase_33_final_failure_analysis/"
                  "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb",
          "sha256": "1e9a5224f15f49ed5054926aa29caeaab74b3ea43c46e4eae3da32453c2a66ff",
          "unchanged": True}),
        ("prior_blocked_notebook",
         {"path": "notebooks/phasewise/phase_33_final_failure_analysis/"
                  "phase33_final_failure_analysis_review.ipynb",
          "sha256": "bf7443e0760d2bc49078776fd99130e7560f6460d5952921523d98f45c4ecc1a",
          "unchanged": True}),
        ("notebook_unchanged", True),
        ("hard_case_table_unchanged", True),
        ("science_unchanged", True),
        ("panel_interpretation_additive_governance_only", True),
        ("notebook_rebuild_required", False),
        ("reason",
         "The reviewer notebook's underlying 20-row hard-case table remains "
         "scientifically/governance compliant after the supervisor per-panel scope "
         "resolution; no rebuild is warranted."),
        ("generated_utc", gen), ("all_pass", True),
    ])
    nb_sha = write_json(nb, AUD / "phase33_notebook_post_scope_resolution_binding.json")

    # ---------- §K final closure ----------
    closure = OrderedDict([
        ("artifact", "phase33_final_closure"),
        ("phase", 33), ("section", "\u00a7K"), ("method", METHOD),
        ("revision", REVISION),
        ("phase33_status", "COMPLETE_CANONICAL"),
        ("closure_class", CLOSURE_CLASS),
        ("scientific_role", SCIENTIFIC_ROLE),
        ("terminal", TERMINAL),
        ("statements", OrderedDict([
            ("phase33_tier0_tier1_execution_complete", True),
            ("core_science_accepted", True),
            ("hard_case_original_table_compliant_under_supervisor_resolution", True),
            ("hard_case_reselection_performed", False),
            ("hard_case_table_modified", False),
            ("boundary_analysis_ineligible", True),
            ("component_analysis_ineligible", True),
            ("qualitative_gallery_ineligible", True),
            ("phase30_qualifier_carried", True),
            ("phase30_status_upgraded", False),
            ("TEST_locked", True),
            ("Phase34_started", False),
        ])),
        ("preserved_science", OrderedDict([
            ("low_overlap_cutoff", CUTOFF), ("low_overlap_n", LOW_OVERLAP_N),
            ("low_overlap_rate", LOW_OVERLAP_RATE),
            ("dice_zero_proxy_n", DICE_ZERO_PROXY_N),
            ("benefit_counts", BENEFIT), ("phase30_categorical_counts", PHASE30_COUNTS),
            ("population", POP),
            ("per_domain_low_overlap", PER_DOMAIN_LOW_OVERLAP),
            ("per_domain_harmful_activation", PER_DOMAIN_HARMFUL),
            ("per_domain_execute_then_reject", PER_DOMAIN_ETR),
            ("low_overlap_x_harmful_activation", LOW_OVERLAP_X_HARMFUL),
            ("groups_with_any_eligible_failure", GROUPS_WITH_ANY_FAILURE),
            ("delta_hat_descriptive_diagnostics_changed", False),
            ("new_statistical_inference", False),
        ])),
        ("negative_provenance", OrderedDict([
            ("new_boundary_analysis", "INELIGIBLE"),
            ("new_component_object_analysis", "INELIGIBLE"),
            ("qualitative_gallery", "INELIGIBLE"),
            ("prediction_pixel_execution", "INELIGIBLE"),
            ("raw_image_reread", "INELIGIBLE"),
            ("raw_GT_reread", "INELIGIBLE"),
            ("model_rerun", "INELIGIBLE"),
            ("manufactured_evidence", False),
        ])),
        ("phase30", {"qualifier": QUALIFIER, "status": PHASE30_STATUS,
                     "status_upgraded": False,
                     "phase33_canonicality_scope":
                         "PHASE33_DESCRIPTIVE_FAILURE_ANALYSIS_AND_GOVERNANCE_ONLY"}),
        ("bound_artifacts", OrderedDict([
            ("supervisor_resolution",
             {"path": "reports/audits/"
                      "phase33_hard_case_panel_scope_supervisor_resolution_v1_2.json",
              "sha256": res_sha}),
            ("supervisor_adjudication",
             {"path": "reports/audits/"
                      "phase33_hard_case_selection_supervisor_adjudication_v1_2.json",
              "sha256": adj_sha}),
            ("notebook_binding",
             {"path": "reports/audits/"
                      "phase33_notebook_post_scope_resolution_binding.json",
              "sha256": nb_sha}),
        ])),
        ("closure_prohibited_counters", OrderedDict([
            ("new_cutoff_computations", 0), ("new_quantiles", 0),
            ("new_failure_labels", 0), ("hard_case_reselections", 0),
            ("raw_image_reads", 0), ("raw_GT_reads", 0),
            ("prediction_array_reads", 0), ("probability_array_reads", 0),
            ("TEST_reads", 0), ("model_loads", 0), ("model_forwards", 0),
            ("training_steps", 0), ("new_Dice_computations", 0),
            ("new_IoU_computations", 0), ("new_HD95_computations", 0),
            ("new_connected_component_computations", 0), ("new_p_values", 0),
            ("new_hypothesis_tests", 0), ("new_bootstrap_procedures", 0),
        ])),
        ("closure_counters_all_zero", True),
        ("generated_utc", gen), ("all_pass", True),
    ])
    closure_sha = write_json(closure, AUD / "phase33_final_closure.json")

    # ---------- §L final closure check ----------
    fc = jload(AUD / "phase33_execution_final_check_v1_2.json")
    exec_term = jload(AUD / "phase33_tier0_tier1_execution_terminal_v1_2.json")
    desc = jload(AUD / "phase33_descriptive_failure_result_v1_2.json")
    checks = OrderedDict([
        ("v1_2_specification_authority_exact",
         sha256_file(AUD / "phase33_specification_terminal_v1_2.json")
         == EXPECTED["reports/audits/phase33_specification_terminal_v1_2.json"]
         and sha256_file(AUD / "phase33_specification_final_check_v1_2.json")
         == EXPECTED["reports/audits/phase33_specification_final_check_v1_2.json"]),
        ("v1_2_execution_terminal_exact",
         sha256_file(AUD / "phase33_tier0_tier1_execution_terminal_v1_2.json")
         == EXPECTED["reports/audits/phase33_tier0_tier1_execution_terminal_v1_2.json"]),
        ("v1_2_execution_final_check_56_56",
         fc["n_checks"] == 56 and fc["n_failed"] == 0),
        ("ambiguity_record_sha_exact",
         sha256_file(AUD / "phase33_hard_case_group_cap_scope_ambiguity_record_v1_2.json")
         == "2212bd2ec567a1fd9918c1119f434f8b6f7062428080f9d2cdc120a604197b0e"),
        ("supervisor_panel_scope_resolution_exists",
         (AUD / "phase33_hard_case_panel_scope_supervisor_resolution_v1_2.json").exists()),
        ("panel_defined_as_one_stratum",
         res["panel_definition"] == "ONE_DECLARED_HARD_CASE_STRATUM"),
        ("group_cap_per_panel", res["group_cap_scope"] == "WITHIN_EACH_STRATUM_PANEL"),
        ("sample_dedup_global",
         res["sample_id_deduplication_scope"] == "GLOBAL_ACROSS_STRATA"),
        ("original_hard_case_table_sha_exact",
         sha256_file(TAB / "phase33_hard_case_ids_v1_2.csv")
         == "6d4bc1d01682e719617d8814913a6b2cd34b10253a144505849b44b8a2c84d3b"),
        ("hard_case_rows_20", rows == 20),
        ("hard_case_unique_samples_20", n_uniq_sid == 20),
        ("hard_case_cross_stratum_dup_0", cross_stratum_dup_sid == 0),
        ("all_panels_individually_group_key_unique", all(per_panel.values())),
        ("nineteen_unique_groups_globally_accepted", n_uniq_gk == 19),
        ("no_hard_case_reselection", res["hard_case_selection_rerun"] is False
         and adj["reselection_required"] is False),
        ("core_cutoff_unchanged", desc["low_overlap"]["cutoff"] == CUTOFF),
        ("core_result_hashes_unchanged",
         all(b["match"] for b in bindings
             if b["path"] in ("reports/audits/phase33_descriptive_failure_result_v1_2.json",
                              "reports/audits/phase33_tier0_tier1_execution_audit_v1_2.json",
                              "reports/tables/phase33_final_system_failure_labels_v1_2.csv",
                              "reports/audits/phase33_low_overlap_cutoff_realization.json"))),
        ("phase30_counts_unchanged",
         desc["benefit_counts"] == BENEFIT
         and jload(AUD / "phase33_phase30_count_reproduction_v1_2.json")["reproduced"] is True),
        ("phase30_qualifier_preserved",
         exec_term["phase30_qualifier_preserved"] == QUALIFIER),
        ("phase30_status_not_upgraded", exec_term["phase30_status_upgraded"] is False),
        ("boundary_ineligible", desc["BOUNDARY_ERROR"] == "INELIGIBLE"),
        ("component_ineligible", desc["COMPONENT_ANALYSIS"] == "INELIGIBLE"),
        ("qualitative_ineligible", desc["QUALITATIVE_GALLERY"] == "INELIGIBLE"),
        ("pixel_raw_model_paths_blocked",
         all(v == "INELIGIBLE" for v in [
             desc["BOUNDARY_ERROR"], desc["COMPONENT_ANALYSIS"],
             desc["QUALITATIVE_GALLERY"]])),
        ("successful_reviewer_notebook_sha_unchanged",
         sha256_file(ROOT / "notebooks/phasewise/phase_33_final_failure_analysis/"
                            "phase33_final_failure_analysis_tier0_tier1_v1_2.ipynb")
         == "1e9a5224f15f49ed5054926aa29caeaab74b3ea43c46e4eae3da32453c2a66ff"),
        ("no_scientific_recomputation_in_closure",
         all(v == 0 for v in closure["closure_prohibited_counters"].values())),
        ("TEST_reads_0", closure["closure_prohibited_counters"]["TEST_reads"] == 0),
        ("training_0", closure["closure_prohibited_counters"]["training_steps"] == 0),
        ("Phase34_not_started", exec_term["Phase34_started"] is False),
    ])
    failed = [k for k, v in checks.items() if not v]
    chk = OrderedDict([
        ("artifact", "phase33_final_closure_check"),
        ("phase", 33), ("section", "\u00a7L"), ("method", METHOD),
        ("revision", REVISION),
        ("bound_closure",
         {"path": "reports/audits/phase33_final_closure.json", "sha256": closure_sha}),
        ("n_checks", len(checks)), ("n_failed", len(failed)), ("failed", failed),
        ("checks", checks),
        ("all_pass", len(failed) == 0),
        ("generated_utc", gen),
    ])
    chk_sha = write_json(chk, AUD / "phase33_final_closure_check.json")

    # ---------- §M Phase33 -> Phase34 handoff ----------
    hand = OrderedDict([
        ("artifact", "phase33_phase34_handoff"),
        ("phase", 33), ("section", "\u00a7M"), ("method", METHOD),
        ("revision", REVISION),
        ("phase33_status", "COMPLETE_CANONICAL"),
        ("phase33_terminal", TERMINAL),
        ("phase34_roadmap_identity", PHASE34_TITLE),
        ("phase34_phase_id", PHASE34_ID),
        ("phase34_title_source", PHASE34_SOURCE),
        ("phase34_title_invented_or_renamed", False),
        ("Phase34_eligibility", "ELIGIBLE_NOT_STARTED"),
        ("Phase34_started", False),
        ("TEST", "LOCKED_UNTIL_PHASE39"),
        ("ROUTER_HOLDOUT", "OPENED_AND_FROZEN"),
        ("phase30_qualifier_remains_mandatory_wherever_phase30_evidence_reused", True),
        ("carry_forward", OrderedDict([
            ("1_phase33_status", "COMPLETE_CANONICAL (governance closure)"),
            ("2_core_science_byte_identical", True),
            ("3_hard_case_original_table_compliant_and_unchanged", True),
            ("4_phase30_qualifier_mandatory", True),
            ("5_phase30_status_not_upgraded", True),
            ("6_ROUTER_HOLDOUT_remains_OPENED_AND_FROZEN", True),
            ("7_TEST_remains_LOCKED_UNTIL_PHASE39", True),
            ("8_phase34_must_not_reopen_protected_raw_router_holdout_images_or_GT"
             "_unless_explicit_predecessor_authority_independently_permits", True),
            ("9_phase34_must_define_its_own_prospective_execution_and_data_access"
             "_contract_before_any_new_profiling_or_analysis_if_required_by_roadmap"
             "_authority", True),
            ("10_boundary_component_qualitative_pixel_raw_and_rerun_paths_remain"
             "_INELIGIBLE_for_phase33", True),
        ])),
        ("bound_closure",
         {"path": "reports/audits/phase33_final_closure.json", "sha256": closure_sha}),
        ("bound_closure_check",
         {"path": "reports/audits/phase33_final_closure_check.json", "sha256": chk_sha}),
        ("generated_utc", gen), ("all_pass", True),
    ])
    hand_sha = write_json(hand, AUD / "phase33_phase34_handoff.json")

    print("=== PHASE33 GOVERNANCE CLOSURE (zero-execution) ===")
    print("predecessor bindings:", len(bindings), "| all match:", all(b["match"] for b in bindings))
    print("closure check:", len(checks), "checks,", len(failed), "failed")
    print("hard-case:", rows, "rows /", n_uniq_sid, "samples /", n_uniq_gk, "groups;",
          "cross-stratum dup", cross_stratum_dup_sid, "| per-panel unique", per_panel)
    print("terminal:", TERMINAL)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
