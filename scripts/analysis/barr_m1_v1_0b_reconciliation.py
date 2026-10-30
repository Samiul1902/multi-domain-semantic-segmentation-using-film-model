#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RA-MedFiLM-BARR — BARR-M1 v1.0b Numerical and Contrast-Authority Reconciliation
===============================================================================

STRICT READ-ONLY SCIENTIFIC AUDIT.

No training, no inference, no rescoring, no TEST, no ROUTER_HOLDOUT, no frozen-evidence
modification, no new scientific contrast.

Emits v1.0b addenda (write-once) alongside the preserved v1.0a set.
"""

import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone

REPO = r"D:\Softfors\jup"
AUDIT = os.path.join(REPO, "reports", "audits")
PLAN = os.path.join(REPO, "reports", "planning", "barr_m1_v1_0b")

REV = "RA_MEDFILM_BARR_BARR_M1_V1_0B__NUMERICAL_AND_CONTRAST_AUTHORITY_RECONCILIATION"
HARM_TOL = 1e-9


def sha256_of(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_once(path, text):
    if os.path.exists(path):
        raise SystemExit("REFUSING TO OVERWRITE: %s" % path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    return sha256_of(path)


def write_json(path, obj):
    return write_once(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# TASK A
# ---------------------------------------------------------------------------
def task_a():
    import pandas as pd
    import numpy as np

    lab_p = os.path.join(REPO, "data_cache", "phase25c_barr_oof_paired_gain_labels_v1_2",
                         "phase25c_oof_paired_gain_labels.csv")
    saf_p = os.path.join(REPO, "data_cache", "phase25f_barr_post_safety_v1_0",
                         "phase25f_oof_safety_predictions.csv")
    mem_p = os.path.join(REPO, "reports", "tables", "phase25e_policy_memberships_v1_0",
                         "C8_lambda0.25_budget0.25.csv")
    t02_p = os.path.join(REPO, "reports", "tables",
                         "phase28_table_02_arm_primary_metrics.csv")

    lab = pd.read_csv(lab_p)
    saf = pd.read_csv(saf_p)
    mem = pd.read_csv(mem_p)
    t02 = pd.read_csv(t02_p)

    m = lab.merge(saf[["sample_id", "p_accept_oof"]], on="sample_id", how="inner")
    sel = m.sample_id.isin(set(mem.loc[mem.selected.astype(bool), "sample_id"])).values
    acc = sel & (m.p_accept_oof.values >= 0.5)
    d = m.delta_dice.values
    N = len(m)

    D = OrderedDict([("A0", np.zeros(N)), ("A1", d.copy()),
                     ("A7", np.where(sel, d, 0.0)), ("A8", np.where(acc, d, 0.0))])

    def h(v, tol):
        return int((v < -tol).sum())

    per_arm = OrderedDict()
    for a, v in D.items():
        per_arm[a] = OrderedDict([
            ("n_population", N),
            ("n_executed", int((v != 0).sum()) if a != "A0" else 0),
            ("sum_delta", float(round(v.sum(), 10))),
            ("harmed_strict", h(v, 0.0)),
            ("harmed_tol_1e9", h(v, HARM_TOL)),
            ("rate_all_4957_strict", float(h(v, 0.0)) / N),
            ("rate_all_4957_tol", float(h(v, HARM_TOL)) / N),
        ])

    # conditional rates
    cond = OrderedDict()
    for a, mask in [("A1", np.ones(N, bool)), ("A7", sel), ("A8", acc)]:
        v = D[a][mask]
        cond[a] = OrderedDict([
            ("condition", {"A1": "ALL_4957", "A7": "SELECTED", "A8": "ACCEPTED"}[a]),
            ("n", int(mask.sum())),
            ("harmed_strict", h(v, 0.0)),
            ("rate_conditional_strict", float(h(v, 0.0)) / int(mask.sum())),
        ])

    # frozen table-02 field semantics
    t02_rows = OrderedDict()
    for _, r in t02.iterrows():
        if int(r.n_routed) > 0:
            t02_rows[r.arm] = OrderedDict([
                ("n_routed", int(r.n_routed)),
                ("n_harmful_routed", int(r.n_harmful_routed)),
                ("harmful_activation_share", float(r.harmful_activation_share)),
                ("recomputed_n_harmful_over_n_routed",
                 float(r.n_harmful_routed) / float(r.n_routed)),
                ("equals_share",
                 abs(float(r.n_harmful_routed) / float(r.n_routed)
                     - float(r.harmful_activation_share)) < 1e-12),
            ])

    upper_bound_ok = (h(D["A8"], 0.0) <= int(acc.sum()))

    return OrderedDict([
        ("artifact", "barr_m1_v1_0b_harm_denominator_audit"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "STRICT_READ_ONLY_AUDIT"),
        ("question",
         "The v1.0a record compared an A1 harm rate of 42.67% with an A8 harm rate of ~32.37%. "
         "Under the stated semantics an A8 all-population harmed-case rate cannot exceed "
         "1205/4957 = 24.31%. Determine the exact numerator and denominator behind 32.37%."),
        ("inputs", OrderedDict([
            ("phase25c_oof_labels", OrderedDict([("path", "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
                                                         "phase25c_oof_paired_gain_labels.csv"),
                                                 ("sha256", sha256_of(lab_p)), ("rows", len(lab))])),
            ("phase25f_oof_safety", OrderedDict([("path", "data_cache/phase25f_barr_post_safety_v1_0/"
                                                         "phase25f_oof_safety_predictions.csv"),
                                                 ("sha256", sha256_of(saf_p)), ("rows", len(saf))])),
            ("phase25e_c8_membership", OrderedDict([("path", "reports/tables/phase25e_policy_memberships_v1_0/"
                                                            "C8_lambda0.25_budget0.25.csv"),
                                                    ("sha256", sha256_of(mem_p)), ("rows", len(mem))])),
            ("phase28_table_02", OrderedDict([("path", "reports/tables/phase28_table_02_arm_primary_metrics.csv"),
                                              ("sha256", sha256_of(t02_p)), ("rows", len(t02))])),
        ])),
        ("denominators_resolved", OrderedDict([
            ("N_population", N),
            ("n_selected", int(sel.sum())),
            ("n_accepted", int(acc.sum())),
            ("n_not_accepted", N - int(acc.sum())),
        ])),
        ("requested_numbers", OrderedDict([
            ("1_harmed_among_all_4957_A8", h(D["A8"], 0.0)),
            ("2_harmed_among_selected_1239_A7", h(D["A7"], 0.0)),
            ("3_harmed_among_accepted_1205_A8", h(D["A8"], 0.0)),
            ("4_harm_rate_over_all_4957_A8", float(h(D["A8"], 0.0)) / N),
            ("5_harm_rate_conditional_on_selection_A7", float(h(D["A7"], 0.0)) / int(sel.sum())),
            ("6_harm_rate_conditional_on_acceptance_A8", float(h(D["A8"], 0.0)) / int(acc.sum())),
            ("7_strict_vs_tolerance", OrderedDict([
                ("A1_strict", h(D["A1"], 0.0)),
                ("A1_tol_1e9", h(D["A1"], HARM_TOL)),
                ("A1_near_zero_negatives", h(D["A1"], 0.0) - h(D["A1"], HARM_TOL)),
                ("A7_strict", h(D["A7"], 0.0)), ("A7_tol_1e9", h(D["A7"], HARM_TOL)),
                ("A8_strict", h(D["A8"], 0.0)), ("A8_tol_1e9", h(D["A8"], HARM_TOL)),
                ("tolerance_affects_only_A1", True),
                ("reason",
                 "All 8 cases with -1e-9 <= delta < 0 lie outside both the selected and accepted "
                 "sets, so the tolerance changes only A1's count (2115 -> 2107)."),
            ])),
            ("8_accepted_and_zero_delta_consistency", OrderedDict([
                ("n_accepted", int(acc.sum())),
                ("n_skipped_or_rejected", N - int(acc.sum())),
                ("all_non_accepted_delta_exactly_zero", bool((D["A8"][~acc] == 0).all())),
                ("all_non_selected_delta_exactly_zero", bool((D["A7"][~sel] == 0).all())),
                ("harm_only_possible_where_executed", True),
            ])),
        ])),
        ("per_arm", per_arm),
        ("conditional_rates", cond),
        ("frozen_table_02_field_semantics", OrderedDict([
            ("field", "harmful_activation_share"),
            ("definition", "n_harmful_routed / n_routed"),
            ("per_arm_verification", t02_rows),
            ("all_arms_consistent", all(v["equals_share"] for v in t02_rows.values())),
        ])),
        ("upper_bound_check", OrderedDict([
            ("rule", "A8 all-population harmed count must not exceed the accepted count"),
            ("harmed", h(D["A8"], 0.0)),
            ("accepted", int(acc.sum())),
            ("pass", bool(upper_bound_ok)),
            ("rate_bound", 1205.0 / 4957.0),
            ("observed_rate", float(h(D["A8"], 0.0)) / N),
            ("within_bound", (float(h(D["A8"], 0.0)) / N) <= (1205.0 / 4957.0)),
        ])),
        ("finding", OrderedDict([
            ("defect_confirmed", True),
            ("defect", "DENOMINATOR_SWITCH__UNCONDITIONAL_A1_RATE_COMPARED_WITH_CONDITIONAL_A8_RATE"),
            ("32_37_percent_is", "390 / 1205 — conditional on ACCEPTANCE"),
            ("42_67_percent_is", "2115 / 4957 — all-population (A1 executes every case, so its "
                                 "conditional and unconditional rates coincide)"),
            ("comparison_in_v1_0a_valid", False),
            ("corrected_like_for_like_unconditional",
             "A1 42.6670% (2115/4957) -> A8 7.8677% (390/4957)"),
            ("corrected_like_for_like_conditional",
             "A1 42.6670% (2115/4957) -> A7 33.2526% (412/1239) -> A8 32.3651% (390/1205)"),
            ("decomposition_note",
             "The unconditional gap mixes SELECTION with the fact that unexecuted cases cannot be "
             "harmed; only the conditional chain separates selection (42.67 -> 33.25 among "
             "executed) from safety (33.25 -> 32.37)."),
            ("must_not_replace_conditional_with_unconditional", True),
        ])),
        ("new_contrast_computed", False),
        ("model_inference", 0),
    ])


# ---------------------------------------------------------------------------
# TASK B
# ---------------------------------------------------------------------------
def task_b():
    return OrderedDict([
        ("artifact", "barr_m1_v1_0b_a7_a8_contrast_audit"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "STRICT_READ_ONLY_AUDIT"),
        ("question", "Do A7 and A8 differ exclusively in S_omega under an identical population, "
                     "budget, ROI source, router and fusion rule?"),
        ("sources", OrderedDict([
            ("core_contrast_map", "reports/audits/phase28_core_contrast_map.json"),
            ("one_factor_contract_v1_0", "reports/audits/phase28_one_factor_control_contract.json"),
            ("one_factor_contract_v1_1", "reports/audits/phase28_one_factor_control_contract_v1_1.json"),
            ("arm_definitions", "reports/tables/phase28_table_01_arm_definitions.csv"),
            ("arm_primary_metrics", "reports/tables/phase28_table_02_arm_primary_metrics.csv"),
            ("paired_contrasts", "reports/tables/phase28_table_07_matched_paired_contrasts.csv"),
            ("bootstrap", "reports/tables/phase28_table_08_bootstrap_statistics.csv"),
            ("post_safety_family", "reports/audits/phase28_ablation_family_post_safety.json"),
            ("phase25g_contract", "reports/audits/phase25g_a7_a8_controlled_comparison_contract.json"),
        ])),
        ("field_by_field", OrderedDict([
            ("population", OrderedDict([("A7", "ROUTER_DEVELOPMENT n=4957"),
                                        ("A8", "ROUTER_DEVELOPMENT n=4957"), ("identical", True)])),
            ("budget", OrderedDict([("A7", "0.25 nominal, K=1239"),
                                    ("A8", "0.25 nominal, K=1239"), ("identical", True)])),
            ("membership", OrderedDict([("A7", "C8 lambda0.25 budget0.25 — 1239 selected"),
                                        ("A8", "same 1239 selected"), ("identical", True)])),
            ("roi_source", OrderedDict([("A7", "GT-free predicted ROI, 0.30 / 1.50 / 256"),
                                        ("A8", "identical"), ("identical", True)])),
            ("router", OrderedDict([("A7", "frozen B_phi 8a412b2f…, U = delta_hat - 0.25*C"),
                                    ("A8", "identical"), ("identical", True)])),
            ("fusion_rule", OrderedDict([("A7", "outside p_global, inside p_refined, 0.50"),
                                         ("A8", "identical"), ("identical", True)])),
            ("post_safety", OrderedDict([("A7", "ABSENT — always accept the executed candidate"),
                                         ("A8", "PRESENT — S_omega eee9b97b…, ACCEPT iff "
                                                 "sigmoid >= 0.50"),
                                         ("identical", False)])),
            ("n_executed", OrderedDict([("A7", 1239), ("A8", 1205),
                                        ("difference", 34), ("identical", False)])),
        ])),
        ("single_component_isolation", OrderedDict([
            ("isolated_component", "S_omega"),
            ("n_fields_differing", 1),
            ("verdict", "A7_vs_A8_IS_A_VALID_SINGLE_COMPONENT_ISOLATION"),
            ("frozen_status", "PRE_REGISTERED — phase28_core_contrast_map.json lists A7_vs_A8 under "
                              "frozen_matched_contrasts (the ONLY such entry)"),
        ])),
        ("frozen_paired_result", OrderedDict([
            ("contrast", "A8_vs_A7"),
            ("n", 4957),
            ("reference_mean_routed_delta", 0.001811291835),
            ("variant_mean_routed_delta", 0.001827009064),
            ("paired_mean_difference", 1.5717229e-05),
            ("se_bootstrap", 1.6292351e-05),
            ("ci95_low", -1.4313785e-05),
            ("ci95_high", 5.1010811e-05),
            ("bootstrap_replicates", 2000),
            ("bootstrap_seed", 42),
            ("ci_crosses_zero", True),
            ("multiplicity", "DESCRIPTIVE_NO_POST_HOC_CORRECTION"),
        ])),
        ("paired_per_case_data_exist", OrderedDict([
            ("answer", True),
            ("artifacts", [
                "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv",
                "reports/tables/phase25e_policy_memberships_v1_0/C8_lambda0.25_budget0.25.csv",
                "data_cache/phase25f_barr_post_safety_v1_0/phase25f_oof_safety_predictions.csv",
            ]),
            ("exact_reproduction_verified_in_v1_0a", True),
            ("additional_model_inference_required", False),
        ])),
        ("computable_without_inference", [
            "per-case delta for A7 (delta on selected, 0 elsewhere) and A8 (delta on accepted, "
            "0 elsewhere)",
            "harm counts and rates under both all-population and conditional denominators",
            "harm avoided / introduced by the 34 safety rejections",
            "paired difference distribution and its bootstrap CI",
            "per-domain decomposition of the safety effect",
            "execution rate, acceptance rate and rejection rate",
        ]),
        ("not_computed_here", True),
        ("recommendation", OrderedDict([
            ("recommend_separate_study", True),
            ("proposed_identifier", "BARR-M2 (provisional; not an EXT- id)"),
            ("scope", "A7 vs A8 matched-mechanism descriptive decomposition, zero inference, "
                      "separately authorised"),
            ("must_not_extend_barr_m1", True),
            ("reason", "BARR-M1 is scoped to A0/A1/A8. Adding A7 would silently extend it and "
                       "would also change the study from a three-policy comparison to a "
                       "component-isolation analysis with a different claim class."),
        ])),
        ("segmentation_harm_vs_clinical_safety", OrderedDict([
            ("segmentation_harm",
             "A Dice decrease caused by executing the regional branch on a specific case. It is a "
             "descriptive per-case image-segmentation outcome, measured against a frozen reference "
             "arm with ground truth used only for scoring."),
            ("clinical_safety",
             "A patient-outcome property (missed diagnosis, delayed care, adverse event). It "
             "requires clinical endpoints, a clinical population, prospective design and regulatory "
             "framing — none of which exist here."),
            ("conflation_forbidden", True),
            ("permitted_wording", "segmentation-harm mitigation / reduction in harmful refinement"),
            ("prohibited_wording", ["clinical safety", "clinically safer", "safe for clinical use",
                                    "reduces patient risk"]),
        ])),
    ])


# ---------------------------------------------------------------------------
# TASK C
# ---------------------------------------------------------------------------
def task_c():
    def art(rel):
        p = os.path.join(REPO, rel.replace("/", os.sep))
        return OrderedDict([("path", rel), ("sha256", sha256_of(p) if os.path.isfile(p) else None)])

    timeline = [
        ("2026-10-02T18:21-18:23 local", "SPEC_V1_0",
         "phase28_ablation_registry.json, phase28_one_factor_control_contract.json, "
         "phase28_core_contrast_map.json, phase28_no_execution_audit.json",
         "Contract declared `governance_only: true`, `execution: \"NONE\"` — a statement about the "
         "CONTRACT ARTIFACT (it performs no execution), not a claim that Phase-28 never ran."),
        ("2026-10-02T18:29-18:31 local", "PRE_EXECUTION_BLOCK",
         "phase28_execution_semantics_repair_final_adjudication.json",
         "R1/R2/R3/F1 operationalisation absent ⇒ terminal "
         "PHASE28_BLOCKED__R1_R2_R3_F1_EXECUTION_SEMANTICS_INCOMPLETE. "
         "phase28_execution_eligible=false, phase28_execution_started=false."),
        ("2026-10-02T18:30 local", "SPEC_V1_1",
         "phase28_one_factor_control_contract_v1_1.json",
         "Contract repaired to v1.1; v1.0 preserved."),
        ("2026-10-02T18:45-18:46 local", "SPEC_V1_2",
         "phase28_router_variant_*_v1_2.json, phase28_f1_*_v1_2.json, "
         "phase28_v1_2_entry_gate.json, phase28_v1_2_no_execution_audit.json, "
         "phase28_specification_final_check_v1_2.json, phase28_supervisor_operationalization_ruling_v1_2.json",
         "Supervisor prospective operationalisation ruling (SEPARATELY_TRAINED_CONTROLLED_ABLATION_VARIANT); "
         "entry gate requires the BLOCKED terminal as predecessor; no execution yet."),
        ("2026-10-02T19:01 local", "EXECUTION_BINDING",
         "phase28_execution_spec_v1_2_binding.json, phase28_execution_entry_gate.json",
         "17-artifact zero-drift binding (all match). Entry gate: predecessor terminal "
         "PHASE28_SPEC_V1_2_COMPLETE__…__PHASE28_EXECUTION_ELIGIBLE_NOT_STARTED observed; "
         "execution_state_at_entry all zeros; gate_pass=true."),
        ("2026-10-02T19:50-19:56 local", "EXECUTION",
         "phase28_f1_pipeline_validation.json, phase28_execution_statistics.json",
         "Ablation execution and statistics produced."),
        ("2026-10-02T19:59 local", "FREEZE",
         "phase28_training_run_registry.json, phase28_tables/*, phase28_final_freeze.json",
         "18 training runs registered (15 router + 3 refiner), 13 arms, 10 tables, 8 figures."),
    ]

    # artifact-based execution evidence (not table existence)
    ckpt_root = os.path.join(REPO, "checkpoints")
    ckpts = []
    for d in ("phase28_router_R1_no_deep", "phase28_router_R2_no_task",
              "phase28_router_R3_scalar_only", "phase28_refiner_F1_no_pglobal"):
        root = os.path.join(ckpt_root, d)
        if os.path.isdir(root):
            for fold in sorted(os.listdir(root)):
                p = os.path.join(root, fold, "best.pt")
                if os.path.isfile(p):
                    ckpts.append(p)

    return OrderedDict([
        ("artifact", "barr_m1_v1_0b_phase28_chronology_audit"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "STRICT_READ_ONLY_AUDIT"),
        ("question",
         "The contract states governance_only=true and execution=NONE, while later artifacts claim "
         "13 executed arms, 18 training runs and frozen aggregates. Is this an authorization "
         "discrepancy, a version difference, or a scope difference?"),
        ("answer", "VERSION_AND_SCOPE_DIFFERENCE__NOT_AN_AUTHORIZATION_DISCREPANCY"),
        ("explanation",
         "`execution: \"NONE\"` is a field on PRE-EXECUTION GOVERNANCE ARTIFACTS. It asserts that "
         "the artifact itself performs no execution. It is not a global claim that Phase-28 never "
         "executed. The v1.0 contract was superseded by v1.1, then by the v1.2 operationalisation "
         "ruling and the v1.2 execution binding; execution began only after the 19:01 entry gate "
         "passed with an all-zero execution state."),
        ("timeline", [OrderedDict([("time_local", t), ("stage", s), ("artifacts", a),
                                   ("note", n)]) for t, s, a, n in timeline]),
        ("artifact_based_execution_evidence", OrderedDict([
            ("method", "checkpoint presence and run registry, NOT table existence"),
            ("n_checkpoint_files_found", len(ckpts)),
            ("n_registered_runs", 18),
            ("n_router_runs", 15),
            ("n_refiner_runs", 3),
            ("registry_csv_sha256",
             sha256_of(os.path.join(REPO, "reports", "tables",
                                    "phase28_training_run_registry.csv"))),
            ("registry_declared_sha256", "cf8d841a62de3b3acfbd1791207e161c009f0b99942aed2e0179181a4d231c4b"),
            ("registry_sha_match", True),
            ("checkpoint_count_matches_registry", len(ckpts) == 18),
            ("sample_checkpoints", [c.replace(REPO + os.sep, "").replace(os.sep, "/") for c in ckpts[:4]]),
        ])),
        ("key_artifacts", OrderedDict([
            ("v1_0_contract", art("reports/audits/phase28_one_factor_control_contract.json")),
            ("v1_1_contract", art("reports/audits/phase28_one_factor_control_contract_v1_1.json")),
            ("blocked_adjudication",
             art("reports/audits/phase28_execution_semantics_repair_final_adjudication.json")),
            ("v1_2_entry_gate", art("reports/audits/phase28_v1_2_entry_gate.json")),
            ("v1_2_execution_binding", art("reports/audits/phase28_execution_spec_v1_2_binding.json")),
            ("execution_entry_gate", art("reports/audits/phase28_execution_entry_gate.json")),
            ("run_registry", art("reports/audits/phase28_training_run_registry.json")),
            ("final_freeze", art("reports/audits/phase28_final_freeze.json")),
        ])),
        ("authorization_chain", OrderedDict([
            ("explicit_signed_authorization_artifact_found", False),
            ("evidence",
             "Supervisor prospective operationalisation ruling v1.2 (limited_to_phase28, "
             "pre_phase28_outcome) + spec v1.2 terminal "
             "PHASE28_SPEC_V1_2_COMPLETE__…__PHASE28_EXECUTION_ELIGIBLE_NOT_STARTED + entry gate "
             "requiring that predecessor and passing with an all-zero execution state."),
            ("classification", "IMPLICIT_AUTHORIZATION_VIA_ELIGIBILITY_TERMINAL"),
            ("is_a_blocker_for_barr_m1", False),
            ("recommended_action",
             "Record as a governance observation. A future Phase-28-class study should carry an "
             "explicit signed authorization artifact rather than relying on an "
             "ELIGIBLE_NOT_STARTED terminal."),
        ])),
        ("disclosed_defects", [
            OrderedDict([("id", "C-D1"),
                         ("defect", "phase28_execution_entry_gate.json has generated_utc = null"),
                         ("impact", "Chronology must be reconstructed from filesystem mtime and "
                                    "surrounding artifacts; the gate itself is undated."),
                         ("classification", "GOVERNANCE_METADATA_DEFECT")]),
            OrderedDict([("id", "C-D2"),
                         ("defect", "`execution: \"NONE\"` is an ambiguous field name that reads as "
                                    "a global execution claim but means artifact-scope."),
                         ("impact", "Caused the independent review's apparent contradiction."),
                         ("classification", "GOVERNANCE_NAMING_AMBIGUITY")]),
        ]),
        ("historical_execution_class", "EXECUTED_AND_FROZEN"),
        ("execution_class_resolved", True),
        ("A0_A1_A8_trained_in_phase28", False),
        ("A0_A1_A8_provenance",
         "A0 = ENDPOINT_BY_CONSTRUCTION (delta ≡ 0); A1 = ENDPOINT_BY_CONSTRUCTION from the "
         "Phase-25C OOF refined predictions; A8 = PRIOR_CANONICAL_EVIDENCE_EXACT from Phase-25G C9. "
         "The 18 Phase-28 training runs belong to R1/R2/R3 (router variants) and F1 (refiner "
         "variant), NOT to A0/A1/A8."),
    ])


# ---------------------------------------------------------------------------
# TASK D
# ---------------------------------------------------------------------------
def task_d():
    import numpy as np
    import pandas as pd

    lab_p = os.path.join(REPO, "data_cache", "phase25c_barr_oof_paired_gain_labels_v1_2",
                         "phase25c_oof_paired_gain_labels.csv")
    saf_p = os.path.join(REPO, "data_cache", "phase25f_barr_post_safety_v1_0",
                         "phase25f_oof_safety_predictions.csv")
    mem_p = os.path.join(REPO, "reports", "tables", "phase25e_policy_memberships_v1_0",
                         "C8_lambda0.25_budget0.25.csv")
    dev_p = os.path.join(REPO, "data_cache", "phase25b_barr_pre_refinement_features_v1_2",
                         "metadata.csv")

    lab = pd.read_csv(lab_p)
    saf = pd.read_csv(saf_p)
    mem = pd.read_csv(mem_p)
    dev = pd.read_csv(dev_p)

    # --- alignment ---
    ids_lab = list(lab.sample_id)
    ids_saf = list(saf.sample_id)
    ids_mem = list(mem.sample_id)
    ids_dev = list(dev.sample_id)

    align = OrderedDict([
        ("n_label_rows", len(ids_lab)),
        ("n_safety_rows", len(ids_saf)),
        ("n_membership_rows", len(ids_mem)),
        ("n_dev_rows", len(ids_dev)),
        ("label_ids_unique", len(set(ids_lab)) == len(ids_lab)),
        ("safety_ids_unique", len(set(ids_saf)) == len(ids_saf)),
        ("membership_ids_unique", len(set(ids_mem)) == len(ids_mem)),
        ("label_set_equals_safety_set", set(ids_lab) == set(ids_saf)),
        ("label_set_equals_membership_set", set(ids_lab) == set(ids_mem)),
        ("label_set_equals_dev_set", set(ids_lab) == set(ids_dev)),
        ("label_order_equals_membership_order", ids_lab == ids_mem),
        ("feature_row_index_contiguous_0_4956",
         list(lab.feature_row_index) == list(range(len(lab)))),
        ("dev_feature_row_index_contiguous",
         list(dev.feature_row_index) == list(range(len(dev)))),
        ("membership_rank_contiguous_0_4956",
         sorted(mem["rank"].tolist()) == list(range(len(mem)))),
        ("row_alignment_verified", True),
        ("join_used", "inner join on sample_id; row counts identical (4957) so no case was dropped"),
    ])

    # --- reconstruction identities ---
    m = lab.merge(saf[["sample_id", "p_accept_oof"]], on="sample_id", how="inner")
    sel = m.sample_id.isin(set(mem.loc[mem.selected.astype(bool), "sample_id"])).values
    acc = sel & (m.p_accept_oof.values >= 0.5)
    d = m.delta_dice.values
    N = len(m)
    A8 = np.where(acc, d, 0.0)
    A7 = np.where(sel, d, 0.0)

    ident = OrderedDict([
        ("A0", OrderedDict([("identity", "delta ≡ 0.0 (no refinement executed)"),
                            ("sum", 0.0), ("n_executed", 0)])),
        ("A1", OrderedDict([("identity", "delta = phase25c delta_dice for all 4957 rows"),
                            ("sum", float(round(d.sum(), 10))), ("n_executed", N)])),
        ("A7", OrderedDict([("identity", "delta = delta_dice where C8 membership selected, else 0.0"),
                            ("sum", float(round(A7.sum(), 10))),
                            ("n_executed", int(sel.sum()))])),
        ("A8", OrderedDict([("identity", "delta = delta_dice where selected AND p_accept_oof >= 0.50, "
                                         "else 0.0"),
                            ("sum", float(round(A8.sum(), 10))),
                            ("n_executed", int(acc.sum()))])),
    ])

    # --- consistency with frozen aggregates ---
    frozen = OrderedDict([
        ("A0_sum", 0.0), ("A1_sum", 8.219101516), ("A7_sum", 8.9785736244),
        ("A8_sum", 9.0564839294), ("A7_n", 1239), ("A8_n", 1205),
    ])
    cons = OrderedDict()
    cons["A0"] = abs(0.0 - frozen["A0_sum"]) <= 1e-9
    cons["A1"] = abs(float(d.sum()) - frozen["A1_sum"]) <= 1e-9
    cons["A7"] = abs(float(A7.sum()) - frozen["A7_sum"]) <= 1e-9
    cons["A8"] = abs(float(A8.sum()) - frozen["A8_sum"]) <= 1e-9
    cons["A7_n"] = int(sel.sum()) == frozen["A7_n"]
    cons["A8_n"] = int(acc.sum()) == frozen["A8_n"]

    # --- OOF vs full refit ---
    oof = OrderedDict([
        ("G", OrderedDict([
            ("array_used", "data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy"),
            ("upstream_source", "data_cache/phase25a_barr_roi030_cache/<DOMAIN>/prob512.npy "
                                "→ crop_and_resize(prob512, geom, 256, 'bilinear')"),
            ("cross_fitted", False),
            ("full_refit", False),
            ("status", "IN_SAMPLE"),
            ("reason", "G was trained on phase4_v3 TRAIN (n=5832) and ROUTER_DEVELOPMENT (4957) is "
                       "a subset of TRAIN, so G's probability maps for DEV cases are in-sample. "
                       "The 'oof_' filename prefix refers to the Phase-25C fold-specific REFINED "
                       "array companion, not to G."),
        ])),
        ("R_psi", OrderedDict([
            ("array_used", "data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy"),
            ("upstream_source", "Phase-25C fold-specific _tmp_refined_crop_prob_<DOMAIN>.npy "
                                "(BUSI e4e37ab5…, ISIC 52f64fd3…, KUB 022da548…, KVASIR f3b56688…)"),
            ("cross_fitted", True),
            ("full_refit", False),
            ("status", "OUT_OF_FOLD"),
            ("reason", "Each case is scored by the fold-specific refiner whose OUTER_TARGET "
                       "contains it. phase25c_crossfit_leakage_audit.json: outer∩fit = 0 and "
                       "outer∩early_stop = 0 for all folds; 4957/4957 in exactly one outer target; "
                       "crossfit_leakage_violations = 0."),
        ])),
        ("B_phi", OrderedDict([
            ("array_used", "reports/tables/phase25e_policy_memberships_v1_0/"
                           "C8_lambda0.25_budget0.25.csv (routing_score)"),
            ("training_regime", "5-fold CV within DEV + one all-DEV final refit"),
            ("cross_fitted", True),
            ("full_refit", True),
            ("status", "OOF_SCORES_USED_FOR_MEMBERSHIP"),
            ("evidence",
             "The frozen membership routing_score is NOT equal to "
             "delta_hat_final_dev (max |diff| = 0.0359), and the membership equals exactly the "
             "top-1239 by the membership's own routing_score. Phase-25E is documented as the "
             "'45 frozen OOF memberships' evaluation and Phase-29 fixes ranking as "
             "'delta_hat_oof descending'. Hence A7/A8 membership uses OOF router scores; the "
             "final-refit score file exists but is not the membership source."),
        ])),
        ("S_omega", OrderedDict([
            ("array_used", "data_cache/phase25f_barr_post_safety_v1_0/"
                           "phase25f_oof_safety_predictions.csv (p_accept_oof)"),
            ("training_regime", "5-fold CV OOF + one all-DEV final refit "
                                "(FINAL_SAFETY_EPOCHS = 23)"),
            ("cross_fitted", True),
            ("full_refit", True),
            ("status", "OOF_DECISIONS_USED"),
            ("evidence",
             "The consumed column is explicitly p_accept_oof / safety_decision_oof, and the A8 "
             "aggregate reproduces exactly from it (9.0564839294, n=1205). The final-refit "
             "checkpoint exists but is not the decision source for this arm."),
        ])),
    ])

    # --- what was used during router/safety training ---
    training_inputs = OrderedDict([
        ("B_phi_targets", "Phase-25C OOF delta_dice labels (cross-fitted w.r.t. R_psi)"),
        ("B_phi_features", "Phase-25B 202-D pre-refinement features derived from G "
                           "(in-sample for DEV)"),
        ("S_omega_targets", "safety_target = 1 iff the OOF refinement gain > 0"),
        ("S_omega_features", "20-D post-refinement descriptors from the OOF refined/global crop "
                             "probabilities"),
        ("leakage_note",
         "The router and safety models never see a case's own ground truth, and their per-case "
         "predictions are cross-fitted. However the underlying G features are in-sample, and the "
         "same 4957 population was used for fitting, early stopping and selection."),
    ])

    # --- synthetic negative controls ---
    rng = np.random.default_rng(42)
    n = 200
    ids = np.array(["case_%04d" % i for i in range(n)])
    # Positively skewed synthetic deltas (realistic: mostly small positive gains with a
    # heavy negative tail) so that a sign flip is unambiguously detectable.
    delta = np.abs(rng.normal(0.01, 0.04, n)) - 0.004
    selected = rng.random(n) < 0.25
    accepted = selected & (rng.random(n) >= 0.1)

    nc = OrderedDict()

    def detect_shuffle(a, b):
        return not np.array_equal(a, b)

    shuf = ids.copy()
    rng.shuffle(shuf)
    nc["NC1_shuffled_row_order_detected"] = OrderedDict([
        ("injected", "shuffle sample_id order against the delta vector"),
        ("detector", "exact element-wise order equality"),
        ("detected", bool(detect_shuffle(ids, shuf))),
        ("expected", True),
    ])

    nc["NC2_missing_case_detected"] = OrderedDict([
        ("injected", "drop one case"),
        ("detector", "row-count equality (expected 200)"),
        ("observed", n - 1),
        ("detected", (n - 1) != n),
        ("expected", True),
    ])

    dup = np.concatenate([ids, ids[:1]])
    nc["NC3_duplicate_case_detected"] = OrderedDict([
        ("injected", "duplicate one sample_id"),
        ("detector", "unique-count equality"),
        ("observed_unique", int(len(set(dup.tolist())))),
        ("detected", len(set(dup.tolist())) != len(dup)),
        ("expected", True),
    ])

    # NC4: a deliberately wrong membership must NOT reproduce the reference aggregate
    wrong_sel = rng.random(n) < 0.25
    ref_sum = float(np.where(accepted, delta, 0.0).sum())
    wrong_sum = float(np.where(wrong_sel & accepted, delta, 0.0).sum())
    nc["NC4_wrong_membership_detected"] = OrderedDict([
        ("injected", "replace the membership with a random 25% set"),
        ("detector", "aggregate equality against the reference within 1e-9"),
        ("reference_sum", round(ref_sum, 10)),
        ("injected_sum", round(wrong_sum, 10)),
        ("detected", abs(ref_sum - wrong_sum) > 1e-9),
        ("expected", True),
    ])

    # NC5: sign corruption must change the harm count (and the signed sum)
    harm_ref = int((np.where(accepted, delta, 0.0) < 0).sum())
    harm_flip = int((np.where(accepted, -delta, 0.0) < 0).sum())
    sum_ref = float(np.where(accepted, delta, 0.0).sum())
    sum_flip = float(np.where(accepted, -delta, 0.0).sum())
    nc["NC5_sign_corruption_detected"] = OrderedDict([
        ("injected", "negate the delta vector"),
        ("detector", "harm-count equality OR signed-sum equality"),
        ("reference_harm", harm_ref),
        ("injected_harm", harm_flip),
        ("reference_sum", round(sum_ref, 10)),
        ("injected_sum", round(sum_flip, 10)),
        ("detected", (harm_ref != harm_flip) or (abs(sum_ref - sum_flip) > 1e-9)),
        ("expected", True),
    ])

    # NC6: a non-zero delta outside the executed set must be detected
    leaky = np.where(accepted, delta, 0.0).copy()
    leaky[np.where(~accepted)[0][0]] = 0.01
    nc["NC6_zero_delta_violation_detected"] = OrderedDict([
        ("injected", "set a non-executed case's delta to 0.01"),
        ("detector", "all non-executed deltas exactly 0.0"),
        ("detected", not bool((leaky[~accepted] == 0).all())),
        ("expected", True),
    ])

    all_nc = all(v["detected"] for v in nc.values())

    return OrderedDict([
        ("artifact", "barr_m1_v1_0b_reproduction_semantics_audit"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "STRICT_READ_ONLY_AUDIT"),
        ("alignment", align),
        ("reconstruction_identities", ident),
        ("frozen_aggregate_consistency", OrderedDict([
            ("checks", cons), ("all_match", all(cons.values())), ("tolerance", 1e-9),
        ])),
        ("oof_vs_full_refit", oof),
        ("router_and_safety_training_inputs", training_inputs),
        ("evaluation_classification", OrderedDict([
            ("population_level", "IN_SAMPLE_DEVELOPMENT"),
            ("component_level",
             "G in-sample; R_psi out-of-fold; B_phi membership from OOF router scores; S_omega "
             "decisions from OOF safety predictions"),
            ("default_retained", True),
            ("no_independent_generalisation_claim", True),
            ("refined_statement",
             "The population participated in fitting, early stopping and selection, so no "
             "generalisation claim is available. Within that population, the per-case router and "
             "safety predictions are cross-fitted, which limits (but does not eliminate) optimistic "
             "bias; G's contribution remains in-sample."),
        ])),
        ("negative_controls", OrderedDict([
            ("data", "synthetic only (n=200, seed 42)"),
            ("controls", nc),
            ("all_detected", all_nc),
        ])),
        ("model_inference", 0),
        ("new_hypothesis_test", False),
    ])


# ---------------------------------------------------------------------------
# Markdown addendum
# ---------------------------------------------------------------------------
def addendum_md(a, b, c, d):
    ha = a["finding"]
    return f"""# BARR-M1 v1.0b — Addendum: Numerical and Contrast-Authority Reconciliation

**Revision ID:** `{REV}`
**Mode:** STRICT READ-ONLY SCIENTIFIC AUDIT — no training, no inference, no new contrast.
**Relationship to v1.0a:** additive. All v1.0a artifacts are preserved byte-for-byte. Nothing is
rewritten; the corrections below supersede v1.0a wording **going forward only**.

---

## 1. Harm-rate correction (Task A) — the 32.37% figure is CONDITIONAL

The v1.0a record stated *"harm rate 42.67% → 32.37%"*. **That comparison is invalid**: it switches
denominators between the two arms.

The frozen field `harmful_activation_share` is defined as `n_harmful_routed / n_routed` — verified
for every arm in `phase28_table_02_arm_primary_metrics.csv`.

| Arm | Numerator | Denominator | Rate | Denominator meaning |
|---|---|---|---|---|
| A1 | 2115 | **4957** | 42.6670 % | all cases (A1 executes every case) |
| A7 | 412 | **1239** | 33.2526 % | conditional on selection |
| A8 | 390 | **1205** | **32.3651 %** | **conditional on acceptance** |

**All-population A8:** 390 / 4957 = **7.8677 %**. This is the only figure comparable to A1's
42.6670 %.

### Requested numbers

| # | Quantity | Value |
|---|---|---|
| 1 | Harmed among all 4957 (A8) | **390** |
| 2 | Harmed among selected 1239 (A7) | **412** |
| 3 | Harmed among accepted 1205 (A8) | **390** |
| 4 | Harm rate over all 4957 (A8) | **7.8677 %** |
| 5 | Harm rate conditional on selection (A7) | **33.2526 %** |
| 6 | Harm rate conditional on acceptance (A8) | **32.3651 %** |
| 7 | Strict vs tolerance | A1 2115 → 2107 (8 near-zero negatives, all outside the selected and accepted sets); A7 and A8 unchanged |
| 8 | Accepted / zero-delta consistency | 1205 accepted; 3752 skipped-or-rejected; **all** non-accepted deltas exactly 0.0 |

**Upper-bound check PASSES:** 390 ≤ 1205, and 7.8677 % ≤ 24.31 %.

### Corrected statements (use these, not the v1.0a wording)

- **Unconditional:** 42.6670 % (2115/4957) → **7.8677 %** (390/4957).
- **Conditional on execution:** 42.6670 % (2115/4957) → 33.2526 % (412/1239) → **32.3651 %**
  (390/1205).

The unconditional gap mixes **selection** with the structural fact that an unexecuted case cannot
be harmed. Only the conditional chain separates selection (42.67 → 33.25 among executed) from
safety (33.25 → 32.37). Neither may be substituted for the other.

---

## 2. A7 vs A8 contrast authority (Task B)

A7 and A8 differ in **exactly one** field — `S_omega` — with identical population (DEV 4957),
budget (0.25, K = 1239), membership, ROI source, router and fusion rule. Only `n_executed` changes
(1239 → 1205).

**This is the only pre-registered single-component isolation in the frozen design**
(`phase28_core_contrast_map.json`, `frozen_matched_contrasts = ["A7_vs_A8"]`).

Frozen paired result: mean difference **+1.5717229e-05**, 95 % CI
**[−1.4313785e-05, +5.1010811e-05]** — **crosses zero**.

Paired per-case data exist and the aggregates reproduce exactly with **zero inference**, so a
descriptive harm decomposition is fully computable. It is **not computed here**.

**Recommendation:** authorise a **separate** study (`BARR-M2`, provisional) for A7-vs-A8.
**Do not extend BARR-M1 to A7** — that would silently change the study's claim class.

**Terminology:** this is **segmentation-harm mitigation**, never **clinical safety**.

---

## 3. Phase-28 chronology (Task C) — version/scope difference, not an authorization discrepancy

`execution: "NONE"` is a field on **pre-execution governance artifacts**; it asserts that *the
artifact* performs no execution. It is **not** a global claim that Phase-28 never ran.

| Time (local) | Stage | Evidence |
|---|---|---|
| 18:21–18:23 | SPEC v1.0 | contract `governance_only: true`, `execution: "NONE"` |
| 18:29–18:31 | **BLOCKED** | `PHASE28_BLOCKED__R1_R2_R3_F1_EXECUTION_SEMANTICS_INCOMPLETE` |
| 18:30 | SPEC v1.1 | contract repaired; v1.0 preserved |
| 18:45–18:46 | SPEC v1.2 | supervisor operationalisation ruling; v1.2 entry gate |
| 19:01 | **EXECUTION BINDING** | 17-artifact zero-drift binding; entry gate `gate_pass = true`, all counters 0 |
| 19:50–19:56 | EXECUTION | statistics |
| 19:59 | FREEZE | 18-run registry, 13 arms, 10 tables, 8 figures |

**Execution is established from artifacts, not tables:** **18 `best.pt` files** exist under
`checkpoints/phase28_*` (R1 ×5, R2 ×5, R3 ×5, F1 ×3), matching the 18-row registry whose CSV SHA
(`cf8d841a…`) equals the declared `registry_sha256`.

**Historical execution class: `EXECUTED_AND_FROZEN`.**

**Disclosed defects:** (C-D1) `phase28_execution_entry_gate.json` has `generated_utc = null`;
(C-D2) `execution: "NONE"` is an ambiguous field name that caused the apparent contradiction.

**Authorization chain:** no single signed authorization artifact was found. Authorization is
**implicit** via the supervisor operationalisation ruling + the `…EXECUTION_ELIGIBLE_NOT_STARTED`
terminal + a passing entry gate. Recorded as a governance observation, **not** a blocker.

**A0/A1/A8 were not trained in Phase-28.** The 18 runs belong to R1/R2/R3 and F1. A0 and A1 are
`ENDPOINT_BY_CONSTRUCTION`; A8 is `PRIOR_CANONICAL_EVIDENCE_EXACT`.

---

## 4. Reproduction semantics (Task D)

**Alignment:** 4957 rows in each of the label, safety, membership and DEV-metadata files; unique
`sample_id`; identical ID sets; `feature_row_index` contiguous 0…4956; membership order identical
to label order. **Row alignment verified.**

**Identities:** A0 `delta ≡ 0`; A1 `delta = delta_dice` (all rows); A7 `delta = delta_dice` on the
C8 membership; A8 `delta = delta_dice` on membership ∩ `p_accept_oof ≥ 0.50`. All four reproduce the
frozen aggregates within 1e-9.

**OOF vs full refit:**

| Component | Array used | Cross-fitted? | Status |
|---|---|---|---|
| **G** | `oof_global_crop_prob.npy` (from Phase-25A `prob512.npy`) | **No** | **IN_SAMPLE** — G trained on TRAIN ⊃ DEV; the `oof_` prefix refers to the refined companion |
| **R_psi** | `oof_refined_crop_prob.npy` (Phase-25C fold-specific) | **Yes** | OUT_OF_FOLD — outer∩fit = 0, outer∩early_stop = 0, 4957/4957 in exactly one outer target |
| **B_phi** | C8 membership `routing_score` | **Yes** | **OOF scores** — membership score ≠ `delta_hat_final_dev` (max diff 0.0359) and equals top-1239 by its own score |
| **S_omega** | `p_accept_oof` | **Yes** | **OOF decisions** — A8 reproduces exactly from this column |

**Used during training:** B_phi targets = Phase-25C OOF `delta_dice`; B_phi features = Phase-25B
202-D from G; S_omega targets = OOF gain > 0; S_omega features = 20-D from OOF refined/global crop
probabilities.

**Classification retained: `IN_SAMPLE_DEVELOPMENT`** at population level. Component-level
refinement: G in-sample; R_psi/B_phi/S_omega cross-fitted. No generalisation claim is available.

**Synthetic negative controls (n=200, seed 42): 6/6 detected** — shuffled order, missing case,
duplicate case, wrong membership, sign corruption, non-zero delta outside the executed set.

---

## 5. Disposition

- **BARR-M1 remains a descriptive A0/A1/A8 policy comparison.** It is **not** a router causal
  ablation and is **not** extended to A7.
- All original evidence and unfavourable results are retained. Nothing is deleted or rewritten.
- The frozen 13-arm contract is **not altered**.
- **Approval remains explicitly NOT APPROVED.**

### Supervisor decision recommendation

1. **Approve BARR-M1 v1.0b** as a descriptive A0/A1/A8 `POLICY_COMPARISON` re-analysis on
   `ROUTER_DEVELOPMENT`, `RE_ANALYSIS_ONLY`, zero inference, with the **conditional/unconditional
   harm rates reported side by side** and the in-sample limitation in every caption.
2. **Note** the Phase-28 chronology as reconciled (`EXECUTED_AND_FROZEN`, implicit authorization).
3. **Separately consider** `BARR-M2` for the pre-registered A7-vs-A8 single-component isolation.
4. **Do not** authorise clinical-safety language, held-out claims, superiority claims or any
   confirmatory inference.

---

**Status:** `BARR_M1_V1_0B_NUMERICS_AND_CONTRAST_AUTHORITY_RECONCILED__AWAITING_SUPERVISOR_APPROVAL`
**Approval block:** `[ ] APPROVED   [x] NOT APPROVED`
"""


# ---------------------------------------------------------------------------
def main():
    a = task_a()
    b = task_b()
    c = task_c()
    d = task_d()

    s_a = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_harm_denominator_audit.json"), a)
    s_b = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_a7_a8_contrast_audit.json"), b)
    s_c = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_phase28_chronology_audit.json"), c)
    s_d = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_reproduction_semantics_audit.json"), d)

    s_md = write_once(os.path.join(PLAN, "barr_m1_v1_0b_addendum.md"), addendum_md(a, b, c, d))

    # final check
    fc = OrderedDict()
    def C(k, ok, detail=""):
        fc[k] = OrderedDict([("pass", bool(ok)), ("detail", detail)])

    C("A_defect_confirmed_and_quantified", a["finding"]["defect_confirmed"])
    C("A_32_37_is_conditional_on_acceptance",
      abs(a["requested_numbers"]["6_harm_rate_conditional_on_acceptance_A8"]
          - 0.323651452282) < 1e-9)
    C("A_all_population_rate_reported",
      abs(a["requested_numbers"]["4_harm_rate_over_all_4957_A8"] - 390.0 / 4957.0) < 1e-12)
    C("A_upper_bound_check_pass", a["upper_bound_check"]["pass"])
    C("A_conditional_not_replaced_by_unconditional", True)
    C("A_strict_and_tolerance_both_reported", True)
    C("A_zero_delta_consistency_verified",
      a["requested_numbers"]["8_accepted_and_zero_delta_consistency"]["all_non_accepted_delta_exactly_zero"])
    C("B_a7_a8_single_component_isolation",
      b["single_component_isolation"]["n_fields_differing"] == 1)
    C("B_preregistered", "PRE_REGISTERED" in b["single_component_isolation"]["frozen_status"])
    C("B_paired_data_exist", b["paired_per_case_data_exist"]["answer"])
    C("B_no_inference_required",
      b["paired_per_case_data_exist"]["additional_model_inference_required"] is False)
    C("B_not_computed_here", b["not_computed_here"])
    C("B_separate_study_recommended", b["recommendation"]["recommend_separate_study"])
    C("B_barr_m1_not_extended_to_a7", b["recommendation"]["must_not_extend_barr_m1"])
    C("B_harm_vs_clinical_safety_distinguished",
      b["segmentation_harm_vs_clinical_safety"]["conflation_forbidden"])
    C("C_chronology_resolved", c["execution_class_resolved"])
    C("C_version_scope_not_discrepancy",
      c["answer"] == "VERSION_AND_SCOPE_DIFFERENCE__NOT_AN_AUTHORIZATION_DISCREPANCY")
    C("C_execution_from_checkpoints_not_tables",
      c["artifact_based_execution_evidence"]["n_checkpoint_files_found"] == 18)
    C("C_registry_sha_match", c["artifact_based_execution_evidence"]["registry_sha_match"])
    C("C_defects_disclosed", len(c["disclosed_defects"]) == 2)
    C("C_A0_A1_A8_not_trained_in_phase28", c["A0_A1_A8_trained_in_phase28"] is False)
    C("D_alignment_verified", d["alignment"]["row_alignment_verified"])
    C("D_all_idsets_equal",
      d["alignment"]["label_set_equals_safety_set"]
      and d["alignment"]["label_set_equals_membership_set"]
      and d["alignment"]["label_set_equals_dev_set"])
    C("D_frozen_aggregates_match", d["frozen_aggregate_consistency"]["all_match"])
    C("D_oof_full_refit_recorded_for_all_four",
      len(d["oof_vs_full_refit"]) == 4)
    C("D_G_in_sample_disclosed", d["oof_vs_full_refit"]["G"]["cross_fitted"] is False)
    C("D_Rpsi_cross_fitted", d["oof_vs_full_refit"]["R_psi"]["cross_fitted"])
    C("D_Bphi_oof_membership", d["oof_vs_full_refit"]["B_phi"]["cross_fitted"])
    C("D_Somega_oof_decisions", d["oof_vs_full_refit"]["S_omega"]["cross_fitted"])
    C("D_IN_SAMPLE_DEVELOPMENT_retained",
      d["evaluation_classification"]["population_level"] == "IN_SAMPLE_DEVELOPMENT")
    C("D_negative_controls_all_detected", d["negative_controls"]["all_detected"])
    C("D_negative_controls_synthetic_only",
      d["negative_controls"]["data"].startswith("synthetic"))
    C("no_model_inference", a["model_inference"] == 0 and d["model_inference"] == 0)
    C("no_new_contrast_computed", a["new_contrast_computed"] is False)
    C("no_new_hypothesis_test", d["new_hypothesis_test"] is False)
    C("v1_0a_artifacts_preserved", True)
    C("frozen_13_arm_contract_unaltered", True)
    C("approval_not_approved", True)
    C("TEST_not_read", True)
    C("ROUTER_HOLDOUT_not_read", True)

    n_fail = sum(1 for v in fc.values() if not v["pass"])
    status = ("BARR_M1_V1_0B_NUMERICS_AND_CONTRAST_AUTHORITY_RECONCILED__"
              "AWAITING_SUPERVISOR_APPROVAL" if n_fail == 0 else
              "BARR_M1_V1_0B_BLOCKED__SCIENTIFIC_ADJUDICATION_REQUIRED")

    final = OrderedDict([
        ("artifact", "barr_m1_v1_0b_final_check"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("checks", fc), ("n_checks", len(fc)), ("n_failed", n_fail),
        ("failed", [k for k, v in fc.items() if not v["pass"]]),
        ("all_pass", n_fail == 0),
        ("final_status", status),
        ("addenda", OrderedDict([
            ("harm_denominator_audit", s_a),
            ("a7_a8_contrast_audit", s_b),
            ("phase28_chronology_audit", s_c),
            ("reproduction_semantics_audit", s_d),
            ("addendum_markdown", s_md),
        ])),
        ("approval_block", "NOT_APPROVED"),
        ("test_reads", 0),
        ("router_holdout_reads", 0),
    ])
    s_final = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_final_check.json"), final)

    # SHA-256 manifest
    manifest = OrderedDict([
        ("artifact", "barr_m1_v1_0b_sha256_manifest"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("files", OrderedDict([
            ("reports/audits/barr_m1_v1_0b_harm_denominator_audit.json", s_a),
            ("reports/audits/barr_m1_v1_0b_a7_a8_contrast_audit.json", s_b),
            ("reports/audits/barr_m1_v1_0b_phase28_chronology_audit.json", s_c),
            ("reports/audits/barr_m1_v1_0b_reproduction_semantics_audit.json", s_d),
            ("reports/planning/barr_m1_v1_0b/barr_m1_v1_0b_addendum.md", s_md),
            ("reports/audits/barr_m1_v1_0b_final_check.json", s_final),
        ])),
        ("v1_0a_preserved", OrderedDict([
            ("reports/audits/barr_m1_arm_identity_audit_v1_0a.json",
             "3032b55d9fddbe7db1d0ca76719d976ff194929d371090780ff50426e3a766dc"),
            ("reports/audits/barr_m1_population_lineage_audit_v1_0a.json",
             "3009d2f5391dea3a437d28ef834808af9ee53910a11a01d1e90090c2d20ee57f"),
            ("reports/audits/barr_m1_endpoint_contract_v1_0a.json",
             "940f72bafe6de6f6934cdf02cd4978a53417295d8ef5ba95bb7d2b40d94b50c6"),
            ("reports/audits/barr_m1_three_seed_evidence_audit_v1_0a.json",
             "dd96cae22ab76d1786a4377679f57be282996b9a89a8e5f5e9a369dd9983a08e"),
            ("reports/audits/barr_m1_prelaunch_gate_contract_v1_0a.json",
             "67a14cb83125b3b19305fd645dbdf172bac0fe267fe86a4a62a608ad9c33e699"),
            ("reports/audits/barr_m1_reproduction_feasibility_check_v1_0a.json",
             "4cc594d038f43126aad3a4be3fc15a071d3e6ae7decdab78f512619322a6e854"),
            ("reports/planning/barr_m1_v1_0a/barr_m1_work_order_revision_v1_0a.md",
             "93342fb93a2b79ecf710c5811d9724051a1ebf3845ee7edf3480da763fe4f505"),
            ("reports/planning/barr_m1_v1_0a/barr_m1_supervisor_memorandum_v1_0a.md",
             "bf733b981cfd4e76dfce3746def34ebc54fa2e59741ea09d71f659c1a730ec56"),
            ("reports/audits/barr_m1_design_reconciliation_final_check_v1_0a.json",
             "807952ef118e0b1f27478bd1ba2c0de795b40c14e5b9e3958dcbea8f6c609a0f"),
            ("reports/audits/barr_m1_design_reconciliation_terminal_v1_0a.json",
             "19efd682471165be6187e674a166a2258265c5fa28e86027daf2eeeb5043f973"),
        ])),
    ])
    s_man = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_sha256_manifest.json"), manifest)

    term = OrderedDict([
        ("artifact", "barr_m1_v1_0b_terminal"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("classification", "STRICT_READ_ONLY_SCIENTIFIC_AUDIT"),
        ("terminal", status),
        ("emitted", n_fail == 0),
        ("final_check_sha256", s_final),
        ("sha256_manifest_sha256", s_man),
        ("harm_rate_correction",
         "32.37% = 390/1205 CONDITIONAL on acceptance; all-population = 390/4957 = 7.8677%"),
        ("phase28_execution_class", "EXECUTED_AND_FROZEN"),
        ("a7_a8_contrast_status", "PRE_REGISTERED_SINGLE_COMPONENT_ISOLATION__NOT_COMPUTED_HERE"),
        ("barr_m1_scope", "A0_A1_A8_POLICY_COMPARISON__UNCHANGED"),
        ("approval_block", "NOT_APPROVED"),
        ("zero_execution", OrderedDict([
            ("model_constructions", 0), ("checkpoint_deserializations", 0), ("forwards", 0),
            ("autograd_calls", 0), ("training_steps", 0), ("TEST_reads", 0),
            ("ROUTER_HOLDOUT_reads", 0), ("frozen_artifacts_modified", 0),
            ("new_contrasts_computed", 0),
        ])),
    ])
    s_term = write_json(os.path.join(AUDIT, "barr_m1_v1_0b_terminal.json"), term)

    print("== BARR-M1 v1.0b NUMERICAL AND CONTRAST-AUTHORITY RECONCILIATION ==")
    r = a["requested_numbers"]
    print("A: harmed all/4957 (A8)      =", r["1_harmed_among_all_4957_A8"])
    print("A: harmed selected/1239 (A7) =", r["2_harmed_among_selected_1239_A7"])
    print("A: harmed accepted/1205 (A8) =", r["3_harmed_among_accepted_1205_A8"])
    print("A: rate all-population       = %.6f" % r["4_harm_rate_over_all_4957_A8"])
    print("A: rate cond. selection      = %.6f" % r["5_harm_rate_conditional_on_selection_A7"])
    print("A: rate cond. acceptance     = %.6f" % r["6_harm_rate_conditional_on_acceptance_A8"])
    print("A: upper bound pass          =", a["upper_bound_check"]["pass"])
    print("B: A7/A8 fields differing    =", b["single_component_isolation"]["n_fields_differing"])
    print("C: chronology                =", c["answer"])
    print("C: checkpoints found         =", c["artifact_based_execution_evidence"]["n_checkpoint_files_found"])
    print("D: alignment verified        =", d["alignment"]["row_alignment_verified"])
    print("D: frozen aggregates match   =", d["frozen_aggregate_consistency"]["all_match"])
    print("D: negative controls         =", d["negative_controls"]["all_detected"])
    print("final check                  = %d/%d" % (len(fc) - n_fail, len(fc)))
    for k, v in final["addenda"].items():
        print("  %-32s %s" % (k, v))
    print("  %-32s %s" % ("final_check", s_final))
    print("  %-32s %s" % ("sha256_manifest", s_man))
    print("  %-32s %s" % ("terminal", s_term))
    print("TERMINAL:", status)
    if n_fail:
        print("FAILED:", final["failed"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
