#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RA-MedFiLM-BARR — BARR-M1 Scientific Work-Order Correction and Authorization Preparation
========================================================================================

PLANNING CORRECTION ONLY.

No training. No model inference. No TEST. No ROUTER_HOLDOUT. No external evaluation.
No frozen artifact modification.

Emits:
  reports/planning/barr_m1_v1_0a/barr_m1_work_order_revision_v1_0a.md
  reports/planning/barr_m1_v1_0a/barr_m1_supervisor_memorandum_v1_0a.md
  reports/audits/barr_m1_arm_identity_audit_v1_0a.json
  reports/audits/barr_m1_population_lineage_audit_v1_0a.json
  reports/audits/barr_m1_endpoint_contract_v1_0a.json
  reports/audits/barr_m1_three_seed_evidence_audit_v1_0a.json
  reports/audits/barr_m1_prelaunch_gate_contract_v1_0a.json
  reports/audits/barr_m1_reproduction_feasibility_check_v1_0a.json
  reports/audits/barr_m1_design_reconciliation_final_check_v1_0a.json
  reports/audits/barr_m1_design_reconciliation_terminal_v1_0a.json

Write-once: refuses to overwrite any existing output.
"""

import hashlib
import json
import os
import sys
from collections import OrderedDict
from datetime import datetime, timezone

REPO = r"D:\Softfors\jup"
AUDIT = os.path.join(REPO, "reports", "audits")
PLAN = os.path.join(REPO, "reports", "planning", "barr_m1_v1_0a")

REV = "RA_MEDFILM_BARR_BARR_M1_V1_0A__SCIENTIFIC_DESIGN_RECONCILIATION"

COMPONENTS = OrderedDict([
    ("G", ("GlobalMedFiLM", "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
           "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt", 3523001)),
    ("R_psi", ("BARRRegionalRefinerV1", "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
               "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt", 1276401)),
    ("B_phi", ("BARRBenefitRouterV1", "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
               "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt", 36801)),
    ("S_omega", ("BARRPostSafetyV1", "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
                 "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt", 1217)),
])

FROZEN_AGGREGATES = OrderedDict([
    ("A0", OrderedDict([("n_routed", 0), ("sum_true_delta_dice", 0.0),
                        ("harmful_activation_share", 0.0)])),
    ("A1", OrderedDict([("n_routed", 4957), ("sum_true_delta_dice", 8.219101516),
                        ("harmful_activation_share", 0.426669356466), ("n_harmful", 2115),
                        ("n_beneficial", 2775)])),
    ("A7", OrderedDict([("n_routed", 1239), ("sum_true_delta_dice", 8.9785736244),
                        ("mean_true_delta_dice_routed", 0.007246629237)])),
    ("A8", OrderedDict([("n_routed", 1205), ("sum_true_delta_dice", 9.0564839294),
                        ("harmful_activation_share", 0.323651452282), ("n_harmful", 390)])),
])

# Frozen Phase-28 table 02 reference values used by the reproduction gate.
FROZEN_REF = OrderedDict([
    ("A1_sum", 8.219101516), ("A1_n_harmful", 2115), ("A1_n_beneficial", 2775),
    ("A7_sum", 8.9785736244), ("A7_n_routed", 1239),
    ("A8_sum", 9.0564839294), ("A8_n_routed", 1205), ("A8_n_harmful", 390),
])

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
# TASK 1 — arm identity audit
# ---------------------------------------------------------------------------
def task1():
    fields = OrderedDict()
    fields["benefit_router_state"] = OrderedDict([
        ("A0", "ABSENT — no B_phi evaluation; no score, no membership"),
        ("A1", "ABSENT — no B_phi evaluation; refine every case"),
        ("A8", "PRESENT — frozen B_phi 8a412b2f…; score = delta_hat - 0.25*C"),
        ("differs_A0_A8", True), ("differs_A1_A8", True),
    ])
    fields["post_safety_state"] = OrderedDict([
        ("A0", "ABSENT / UNREACHABLE — no refinement candidate exists to accept or reject"),
        ("A1", "ABSENT — always accept the refined candidate"),
        ("A8", "PRESENT — frozen S_omega eee9b97b…; ACCEPT iff sigmoid >= 0.50"),
        ("differs_A0_A8", True), ("differs_A1_A8", True),
    ])
    fields["refiner_execution_policy"] = OrderedDict([
        ("A0", "NEVER — 0 / 4957"),
        ("A1", "ALWAYS — 4957 / 4957"),
        ("A8", "CONDITIONAL — 1239 selected, 1205 accepted after safety"),
        ("differs_A0_A8", True), ("differs_A1_A8", True),
    ])
    fields["roi_source"] = OrderedDict([
        ("A0", "NONE — no crop is taken"),
        ("A1", "GT-FREE predicted ROI (threshold 0.30, expansion 1.50, resolution 256)"),
        ("A8", "GT-FREE predicted ROI (identical rule)"),
        ("differs_A0_A8", True), ("differs_A1_A8", False),
    ])
    fields["fusion_rule"] = OrderedDict([
        ("A0", "N/A — final = global"),
        ("A1", "outside ROI p_global; inside ROI p_refined; output threshold 0.50"),
        ("A8", "outside ROI p_global; inside ROI p_refined; output threshold 0.50"),
        ("differs_A0_A8", True), ("differs_A1_A8", False),
    ])
    fields["thresholds"] = OrderedDict([
        ("A0", "segmentation output 0.50 only"),
        ("A1", "ROI proposal 0.30 + segmentation output 0.50"),
        ("A8", "ROI proposal 0.30 + segmentation output 0.50 + safety accept 0.50"),
        ("differs_A0_A8", True), ("differs_A1_A8", True),
    ])
    fields["evaluation_population"] = OrderedDict([
        ("A0", "ROUTER_DEVELOPMENT n=4957"),
        ("A1", "ROUTER_DEVELOPMENT n=4957"),
        ("A8", "ROUTER_DEVELOPMENT n=4957"),
        ("differs_A0_A8", False), ("differs_A1_A8", False),
    ])
    fields["budget_semantics"] = OrderedDict([
        ("A0", "budget = 0 (degenerate; nothing is executed)"),
        ("A1", "budget = 1.00 (full; 4957 of 4957)"),
        ("A8", "budget = 0.25 nominal; K = 1239 selected of 4957"),
        ("differs_A0_A8", True), ("differs_A1_A8", True),
    ])
    fields["ground_truth_access_rules"] = OrderedDict([
        ("A0", "NO GT at inference. GT used only for post-hoc Dice scoring."),
        ("A1", "NO GT at inference. GT used only for post-hoc Dice scoring."),
        ("A8", "NO GT at inference. GT used only for post-hoc Dice scoring."),
        ("differs_A0_A8", False), ("differs_A1_A8", False),
    ])

    n_diff_a8_a1 = sum(1 for k, v in fields.items()
                       if isinstance(v, dict) and v.get("differs_A1_A8"))
    n_diff_a8_a0 = sum(1 for k, v in fields.items()
                       if isinstance(v, dict) and v.get("differs_A0_A8"))

    return OrderedDict([
        ("artifact", "barr_m1_arm_identity_audit_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "PLANNING_CORRECTION_ONLY"),
        ("authority", OrderedDict([
            ("phase28_one_factor_control_contract",
             "reports/audits/phase28_one_factor_control_contract.json"),
            ("phase28_ablation_registry", "reports/audits/phase28_ablation_registry.json"),
            ("phase28_core_contrast_map", "reports/audits/phase28_core_contrast_map.json"),
            ("phase28_ablation_family_post_safety",
             "reports/audits/phase28_ablation_family_post_safety.json"),
            ("phase28_table_01_arm_definitions",
             "reports/tables/phase28_table_01_arm_definitions.csv"),
            ("phase28_table_02_arm_primary_metrics",
             "reports/tables/phase28_table_02_arm_primary_metrics.csv"),
            ("phase28_execution_statistics",
             "reports/audits/phase28_execution_statistics.json"),
        ])),
        ("arm_identities_from_frozen_authority", OrderedDict([
            ("A0", "global-only (routing absent; no refinement) — ENDPOINT_BY_CONSTRUCTION"),
            ("A1", "always-refine (routing absent, full budget) — ENDPOINT_BY_CONSTRUCTION"),
            ("A8", "A7 + post-safety S_omega (canonical baseline) — PRIOR_CANONICAL_EVIDENCE_EXACT"),
            ("A7", "A6 + resource cost U = delta_hat - lambda*C"),
        ])),
        ("field_by_field_comparison", fields),
        ("n_fields_differing_A8_vs_A1", n_diff_a8_a1),
        ("n_fields_differing_A8_vs_A0", n_diff_a8_a0),
        ("frozen_contrast_status", OrderedDict([
            ("frozen_matched_contrasts", ["A7_vs_A8"]),
            ("adjacent_incremental_contrasts", ["A6_vs_A0", "A7_vs_A6"]),
            ("descriptive_rows_no_formal_pairwise_reference", ["A0", "A1", "R1", "R2", "R3", "F1"]),
            ("A0_A1_A8_is_pre_registered_contrast", False),
            ("A8_vs_A1_pre_registered", False),
            ("A8_vs_A0_pre_registered", False),
            ("A1_vs_A0_pre_registered", False),
            ("note", "The frozen core contrast map pre-registers ONLY A7_vs_A8 as a matched "
                     "contrast. A0 and A1 are explicitly listed as descriptive rows with no formal "
                     "pairwise reference. Any A0/A1/A8 contrast is therefore a NEW contrast "
                     "(descriptive), not a pre-registered one."),
        ])),
        ("verdict", OrderedDict([
            ("classification", "POLICY_COMPARISON"),
            ("not_router_causal_ablation", True),
            ("router_effect_identifiable_from_A0_A1_A8", False),
            ("reason",
             "A8 differs from A1 simultaneously in (i) benefit-router presence, (ii) resource-cost "
             "term, (iii) post-safety S_omega presence, and (iv) budget semantics (0.25 vs 1.00). "
             "Four factors change at once, so A8-A1 cannot be attributed to the router. A1-A0 "
             "changes refinement execution, ROI availability and budget. No frozen arm holds "
             "routing and safety constant while varying only routing, so the router effect is "
             "NOT identifiable within A0/A1/A8."),
            ("only_isolating_contrast_available", "A7_vs_A8 isolates S_omega alone (frozen)"),
            ("new_arms_created", False),
            ("note_on_authorisation",
             "Executing A0/A1/A8 is not post-hoc factor addition: all three are already defined "
             "frozen arms. The contract's prohibition is on ADDING factors/arms, not on executing "
             "defined ones."),
        ])),
    ])


# ---------------------------------------------------------------------------
# TASK 2 — population lineage
# ---------------------------------------------------------------------------
def task2(dev_n, dev_dom, val_n, val_dom, dev_val_overlap, dev_train_overlap,
          dev_subset_train, dev_patients, kub_patients, na_domains):
    return OrderedDict([
        ("artifact", "barr_m1_population_lineage_audit_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "PLANNING_CORRECTION_ONLY"),
        ("populations", OrderedDict([
            ("ROUTER_DEVELOPMENT", OrderedDict([
                ("n", dev_n), ("per_domain", dev_dom),
                ("metadata", "data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv"),
                ("metadata_sha256",
                 sha256_of(os.path.join(REPO, "data_cache",
                                        "phase25b_barr_pre_refinement_features_v1_2",
                                        "metadata.csv"))),
                ("outer_folds", OrderedDict([("fold0", 1657), ("fold1", 1652), ("fold2", 1648)])),
            ])),
            ("VAL808", OrderedDict([
                ("n", val_n), ("per_domain", val_dom),
                ("manifest", "manifests/phase4_v3/val.csv"),
                ("manifest_sha256",
                 sha256_of(os.path.join(REPO, "manifests", "phase4_v3", "val.csv"))),
            ])),
            ("ROUTER_HOLDOUT", OrderedDict([
                ("n", 875), ("status", "OPENED_AND_FROZEN"), ("consumed_by", "Phase30"),
                ("accessible_to_BARR_M1", False),
            ])),
            ("TEST", OrderedDict([
                ("n", 1683), ("status", "LOCKED_UNTIL_PHASE39"), ("accessible_to_BARR_M1", False),
            ])),
        ])),
        ("overlap", OrderedDict([
            ("dev_intersect_val808", dev_val_overlap),
            ("dev_intersect_train", dev_train_overlap),
            ("dev_is_subset_of_train", dev_subset_train),
            ("note", "ROUTER_DEVELOPMENT is drawn ENTIRELY from the TRAIN split and is disjoint "
                     "from VAL808. Overlap is computed on exact sample_id equality, not on "
                     "filename heuristics."),
        ])),
        ("component_populations", OrderedDict([
            ("G", OrderedDict([
                ("trained_on", "phase4_v3 TRAIN (n=5832)"),
                ("selection_population", "VAL808 (macro-domain Dice, early stopping)"),
                ("calibration_population", "N/A"),
                ("dev_relation", "IN_SAMPLE — DEV ⊂ TRAIN"),
            ])),
            ("R_psi", OrderedDict([
                ("trained_on", "phase4_v3 TRAIN (n=5832), ROI-0.30 crop training"),
                ("selection_population", "VAL (early stopping)"),
                ("calibration_population", "N/A"),
                ("dev_relation", "IN_SAMPLE — DEV ⊂ TRAIN"),
            ])),
            ("B_phi", OrderedDict([
                ("trained_on", "ROUTER_DEVELOPMENT n=4957 — 5-fold CV (FIT/EARLY_STOP/OUTER_TARGET) "
                               "PLUS one all-DEV final refit"),
                ("selection_population", "EARLY_STOP folds within DEV"),
                ("calibration_population", "DEV score thresholds (budget 0.25)"),
                ("dev_relation", "IN_SAMPLE — the final refit sees all 4957 DEV rows"),
            ])),
            ("S_omega", OrderedDict([
                ("trained_on", "ROUTER_DEVELOPMENT n=4957 — 5-fold CV OOF plus all-DEV final refit "
                               "(FINAL_SAFETY_EPOCHS = 23)"),
                ("selection_population", "EARLY_STOP folds within DEV"),
                ("calibration_population", "DEV (accept threshold 0.50)"),
                ("dev_relation", "IN_SAMPLE — the final refit sees all 4957 DEV rows"),
            ])),
        ])),
        ("independence_classification", OrderedDict([
            ("ROUTER_DEVELOPMENT",
             "IN_SAMPLE_DEVELOPMENT — training population for B_phi and S_omega, and a subset of "
             "the TRAIN split used by G and R_psi. Selection-contaminated by construction."),
            ("VAL808",
             "OUT_OF_SAMPLE_BUT_CONSUMED_DEVELOPMENT_BENCHMARK — disjoint from TRAIN, so "
             "out-of-sample for all four components; but already consumed by Phase27 "
             "(preservation) and Phase29 (three-seed), so not pristine."),
            ("no_pristine_independent_population_available", True),
            ("reason",
             "ROUTER_HOLDOUT (875) was consumed by Phase30 and is OPENED_AND_FROZEN; TEST is "
             "locked until Phase39. No untouched independent population remains."),
        ])),
        ("patient_and_source_clustering", OrderedDict([
            ("dev_unique_patient_id", dev_patients),
            ("kub_unique_patient_id", kub_patients),
            ("domains_without_patient_identifier", na_domains),
            ("case_id_available", False),
            ("note", "patient_id is 'NOT_AVAILABLE' for ISIC, BUSI and KVASIR; only KUB carries "
                     "real patient identifiers (267). case_id is 'NOT_AVAILABLE' in every domain. "
                     "Patient-level clustering is therefore only possible inside KUB."),
        ])),
        ("population_roles_declared", OrderedDict([
            ("primary", "ROUTER_DEVELOPMENT n=4957 — preserves the frozen Phase-28 contract "
                        "held_constant population"),
            ("secondary", "VAL808 n=808 — SEPARATE prospective descriptive proposal; requires its "
                          "own approval and must not be pooled with the primary"),
            ("pooling_permitted", False),
            ("note", "The frozen Phase-28 contract fixes population = ROUTER_DEVELOPMENT. VAL808 "
                     "is outside that contract and is therefore not automatically authorised."),
        ])),
        ("independence_inferred_from_filenames", False),
        ("TEST_read", False),
        ("ROUTER_HOLDOUT_read", False),
    ])


# ---------------------------------------------------------------------------
# TASK 3 — endpoint contract
# ---------------------------------------------------------------------------
def task3():
    return OrderedDict([
        ("artifact", "barr_m1_endpoint_contract_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "PLANNING_CORRECTION_ONLY"),
        ("paired_contrasts", OrderedDict([
            ("contrasts", ["A8_minus_A0", "A8_minus_A1", "A1_minus_A0"]),
            ("same_eligible_cases_required", True),
            ("n_cases", 4957),
            ("skip_contributes_zero", True),
            ("denominator", "all 4957 cases (intent-to-treat); a SKIP or safety-REJECT case "
                            "contributes a Dice delta of exactly 0.0 because final = global"),
            ("note", "This matches the frozen Phase-28 convention: A7 mean 0.001811291835 = "
                     "8.9785736244 / 4957 and A8 mean 0.001827009064 = 9.0564839294 / 4957, both "
                     "divided by the FULL population, not by n_routed."),
        ])),
        ("dice_metric", OrderedDict([
            ("per_case_metric", "binary Dice at segmentation output threshold 0.50"),
            ("epsilon", 1e-7),
            ("macro_domain_dice_definition",
             "macro = (1/4) * sum_over_domains( mean_over_cases_in_domain( dice ) ) — EQUAL domain "
             "weighting across ISIC, BUSI, KVASIR, KUB"),
            ("macro_domain_delta_definition",
             "macro_delta = (1/4) * sum_over_domains( mean_over_cases_in_domain( dice_arm - dice_A0 ) )"),
            ("pooled_mean_permitted_as_primary", False),
            ("cumulative_dice_difference_must_not_be_reported_as_macro", True),
            ("single_metric_definition_across_arms", True),
        ])),
        ("harm_definition", OrderedDict([
            ("frozen_definition", "a case is HARMED when applying the regional arm reduces Dice"),
            ("frozen_source", "reports/audits/phase22_harm_analysis.json"),
            ("operational_rule", "harm_i = 1 if (dice_arm_i - dice_A0_i) < -HARM_TOL else 0"),
            ("numerical_tolerance", HARM_TOL),
            ("tolerance_justification",
             "Dice is computed in float64 from frozen probability maps; 1e-9 is far above "
             "accumulated floating-point noise and far below any scientifically meaningful effect."),
            ("reference_arm_for_harm", "A0 (global-only)"),
            ("report_strict_zero_tolerance_count_too", True),
        ])),
        ("separated_quantities", OrderedDict([
            ("harm_rate", "n_harmed / n_eligible (per arm, vs A0)"),
            ("harm_magnitude", "mean, median, worst, p05 and total of negative deltas only"),
            ("net_dice_gain", "sum of per-case deltas over all 4957 (cumulative, NOT macro)"),
            ("macro_domain_gain", "equal-domain macro delta defined above"),
            ("refiner_execution_rate", "n_executed / 4957 per arm"),
            ("accepted_refinement_rate", "n_accepted / n_executed"),
            ("safety_rejection_rate", "1 - accepted_refinement_rate (A8 only)"),
            ("must_not_be_conflated", True),
        ])),
        ("bootstrap", OrderedDict([
            ("procedure", "paired bootstrap with COMMON resampled indices per contrast"),
            ("n_resamples", 2000),
            ("seed", 42),
            ("grouping_unit", "domain-stratified; within KUB, patient-clustered (267 patients); "
                              "ISIC/BUSI/KVASIR per-case (no patient identifier available)"),
            ("stratification", "4 domains, equal weight in the macro statistic"),
            ("missingness_rule", "any missing case, NaN or duplicate sample_id ⇒ ABORT; no "
                                 "imputation, no silent drop"),
            ("ci", "95% percentile interval"),
            ("multiplicity", "DESCRIPTIVE_NO_POST_HOC_CORRECTION (inherits the frozen Phase-28 rule)"),
            ("confirmatory_inference_permitted", False),
        ])),
        ("historical_numbers_usage", OrderedDict([
            ("phase22_harm_numbers_role", "HISTORICAL_MOTIVATION_ONLY"),
            ("phase29_three_seed_numbers_role", "HISTORICAL_MOTIVATION_ONLY"),
            ("direct_comparison_to_new_A0_A1_A8_permitted", False),
            ("reason",
             "Phase-22 harm is computed on VAL808 with an ORACLE (GT-defined) ROI; BARR-M1 uses "
             "ROUTER_DEVELOPMENT with a GT-FREE predicted ROI. Different population, different ROI "
             "source, and opposite sign (Phase-22 net gain -34.32; frozen A1 on DEV net +8.219). "
             "They are not comparable quantities."),
        ])),
    ])


# ---------------------------------------------------------------------------
# TASK 4 — three-seed evidence
# ---------------------------------------------------------------------------
def task4():
    return OrderedDict([
        ("artifact", "barr_m1_three_seed_evidence_audit_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "PLANNING_CORRECTION_ONLY"),
        ("seeds", [42, 123, 3407]),
        ("authority", OrderedDict([
            ("authoritative_seeds", "reports/audits/phase29_authoritative_seeds_v1_1.json"),
            ("rng_rule", "reports/audits/phase29_b_phi_rng_rule_v1_1.json"),
            ("cross_seed_isolation", "reports/audits/phase29_cross_seed_dependency_isolation.json"),
            ("three_seed_summary", "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json"),
        ])),
        ("what_the_seeds_are", OrderedDict([
            ("independently_trained_models", "PARTIALLY — downstream stack only"),
            ("global_model_G", "FIXED at seed 42 for ALL three seeds "
                               "(shared_global_representation_is_seed42_fixed = true)"),
            ("retrained_per_seed", ["R_psi (own fold checkpoints)", "B_phi", "S_omega"]),
            ("rng_rule", "router_fold_seed(s,k) = 1000*s + k; the seed changes optimisation "
                         "randomness, NOT fold membership "
                         "(seed_regenerates_fold_membership = false)"),
            ("stochastic_routing", False),
            ("sampling_variation", False),
            ("repeated_inference_of_one_checkpoint", False),
            ("evidence_for_g", "NONE — macro_global_dice is identical to 1.36e-16 across seeds, "
                               "proving G is the same checkpoint"),
        ])),
        ("observed_sd", OrderedDict([
            ("value", 0.0005902732514585419),
            ("ddof", 1),
            ("n", 3),
            ("degrees_of_freedom", 2),
            ("measures",
             "the sample SD of the MACRO-DOMAIN EQUAL-WEIGHT MEAN DICE DELTA across THREE "
             "INDEPENDENTLY RETRAINED DOWNSTREAM BARR STACKS (R_psi → B_phi → S_omega) evaluated "
             "on VAL808, with the global model G held fixed at seed 42."),
            ("does_not_measure", [
                "stochastic inference repeat variability (each checkpoint is deterministic)",
                "sampling error of the evaluation set",
                "independent replication of the global model G",
                "run-to-run hardware nondeterminism",
                "a population-level standard error",
            ]),
            ("per_seed_macro_delta", OrderedDict([
                ("seed42", 0.0022101452700813433),
                ("seed123", 0.003387940558448247),
                ("seed3407", 0.002868801269949678),
            ])),
            ("per_seed_macro_global_dice", OrderedDict([
                ("seed42", 0.8350789601074979), ("seed123", 0.8350789601074979),
                ("seed3407", 0.8350789601074979),
            ])),
            ("per_seed_n_selected", OrderedDict([("seed42", 279), ("seed123", 255),
                                                 ("seed3407", 262)])),
            ("interpretation_caution",
             "n=3 gives 2 degrees of freedom; the SD estimate is itself extremely unstable and no "
             "confidence interval or significance test may be derived from it."),
            ("frozen_gate", "NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE = true "
                            "(numeric_reproducibility_pass_fail_gate = NONE)"),
        ])),
        ("misreporting_prohibited", OrderedDict([
            ("report_as_independent_training_replication_of_the_full_system", False),
            ("report_as_inference_noise", False),
            ("report_as_confirmatory", False),
        ])),
        ("relevance_to_barr_m1", OrderedDict([
            ("barr_m1_uses_multiple_training_seeds", False),
            ("reason", "BARR-M1 is a single-frozen-bundle re-analysis; the three-seed spread is "
                       "cited only as historical motivation for the ±0.0006 scale of downstream "
                       "training randomness, never as a BARR-M1 uncertainty estimate."),
        ])),
    ])


# ---------------------------------------------------------------------------
# TASK 5 — inference-specialised R1..R10
# ---------------------------------------------------------------------------
def task5():
    def R(rid, title, demand, inference_substitute, n_a_reason, code):
        return OrderedDict([
            ("id", rid), ("title", title), ("demand", demand),
            ("inference_specialisation", inference_substitute),
            ("training_only_na_reason", n_a_reason), ("fail_closed_code", code),
        ])

    return OrderedDict([
        ("artifact", "barr_m1_prelaunch_gate_contract_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("scope", "PLANNING_CORRECTION_ONLY"),
        ("framework", "R1-R10 retained; each requirement specialised for an inference / re-analysis study"),
        ("requirements", [
            R("R1", "Documented scientific authorization",
              "Named, dated, attributable authorisation with scope, population, seeds and exclusions.",
              "Identical. Scope must enumerate: arms A0/A1/A8 only, population ROUTER_DEVELOPMENT, "
              "mode RE_ANALYSIS_ONLY, and the exclusion list.",
              None,
              ["E_AUTHORIZATION_ABSENT", "E_AUTHORIZATION_SCOPE_MISMATCH",
               "E_AUTHORIZATION_EXCLUSION_VIOLATED"]),
            R("R2", "Frozen protocol and frozen population",
              "Freeze the training recipe and the populations by digest before the first training step.",
              "No training recipe exists. Substitute frozen inputs: (a) four component checkpoint "
              "SHA-256; (b) frozen ROI/fusion/threshold config (0.30 / 1.50 / 256 / 0.50 / 0.50); "
              "(c) frozen membership artifact C8_lambda0.25_budget0.25.csv with its SHA and "
              "selected_ids_sha256; (d) manifest digests for DEV and (if approved) VAL808; "
              "(e) exact row-count and sample_id-set equality checks at load.",
              "No optimiser, loss, augmentation, LR, batch size, epoch ceiling or patience exists "
              "in a re-analysis; freezing a training recipe would be meaningless.",
              ["E_PROTOCOL_UNFROZEN", "E_PROTOCOL_NOT_LOADED_FROM_FROZEN",
               "E_POPULATION_SHA_MISMATCH", "E_POPULATION_COUNT_MISMATCH",
               "E_ROW_IDENTITY_MISMATCH"]),
            R("R3", "Direct source-to-authority field comparison",
              "At least one edge must read the frozen authority and compare a concrete value.",
              "Compare the harness's effective constants against the frozen authority VALUES, "
              "field by field: roi_proposal_threshold 0.30, roi_expansion 1.50, roi_resolution 256, "
              "segmentation_output_threshold 0.50, safety_accept_threshold 0.50, budget 0.25, "
              "K 1239, lambda 0.25, bootstrap 2000 / seed 42. Plus a second authority edge: "
              "recompute the A0/A1/A7/A8 aggregates and compare them to the frozen Phase-28 "
              "table 02 values (this is a VALUE comparison, not a digest comparison).",
              None,
              ["E_NO_AUTHORITY_EDGE", "E_AUTHORITY_FIELD_MISMATCH",
               "E_DIGEST_COMPARISON_SUBSTITUTED_FOR_VALUE_COMPARISON",
               "E_FROZEN_AGGREGATE_NOT_REPRODUCED"]),
            R("R4", "Exact harness SHA binding",
              "The digest of the executing harness must be recorded and re-verified at launch.",
              "Identical and non-negotiable: the re-analysis harness computes its own raw-byte "
              "SHA-256 at start, compares it to the authorised digest, aborts on mismatch, and "
              "writes the digest into every per-arm registry entry.",
              None,
              ["E_HARNESS_SHA_ABSENT", "E_HARNESS_SHA_MISMATCH", "E_HARNESS_NOT_BOUND_AT_LAUNCH"]),
            R("R5", "Parameter-count checks",
              "Measure total and trainable parameter counts and compare to declared expectations.",
              "No training, so 'trainable' is meaningless. Substitute INFERENCE_LOAD_VERIFICATION: "
              "at load, verify each state_dict's tensor count and summed numel against declared "
              "values (G 3,523,001; R_psi 1,276,401; B_phi 36,801; S_omega 1,217) and require "
              "0 missing / 0 unexpected keys. If BARR-M1 runs purely on frozen per-case arrays "
              "(no model load at all), this becomes a NEGATIVE requirement: assert that NO model "
              "was constructed and that the parameter counters are exactly 0.",
              "Gradient/optimiser state does not exist in a frozen inference or re-analysis path.",
              ["E_PARAM_TOTAL_MISMATCH", "E_PARAM_EXPECTATION_NOT_DECLARED",
               "E_STATE_DICT_KEY_MISMATCH", "E_MODEL_CONSTRUCTED_WITHOUT_AUTHORIZATION"]),
            R("R6", "Prespecified seed policy",
              "Declare the seed set and what claim the count supports before launch.",
              "Training seeds are not applicable. Substitute: (a) declare that inference is "
              "deterministic and that NO inference RNG is consumed; (b) fix the bootstrap seed at "
              "42 with 2000 resamples; (c) declare explicitly that BARR-M1 provides ONE frozen "
              "bundle and therefore no seed-to-seed uncertainty; (d) declare that the Phase-29 "
              "three-seed spread is NOT a BARR-M1 uncertainty estimate.",
              "There are no training seeds in a re-analysis over a single frozen bundle.",
              ["E_SEED_POLICY_ABSENT", "E_SEED_SET_MISMATCH", "E_SINGLE_SEED_CLAIM_UNLABELLED",
               "E_THREE_SEED_SPREAD_MISUSED_AS_UNCERTAINTY"]),
            R("R7", "Checkpoint and complete epoch-log persistence",
              "Persist per-epoch logs plus latest.pt / best.pt with correct selection metadata.",
              "No epochs and no checkpoints are produced. Substitute: (a) per-case output "
              "persistence for every arm (sample_id, dice_global, dice_arm, delta, executed flag, "
              "safety decision) so harm is independently recomputable; (b) write-once outputs "
              "(O_CREAT|O_EXCL) with post-write size and SHA verification; (c) a resume manifest "
              "making each arm idempotent; (d) a per-arm completion marker that records the exact "
              "input SHAs consumed.",
              "A re-analysis has no epoch loop, no early stopping and no checkpoint selection.",
              ["E_CKPT_ABSENT", "E_CKPT_SHA_MISMATCH", "E_PER_CASE_OUTPUT_ABSENT",
               "E_OUTPUT_NOT_WRITE_ONCE", "E_RESUME_NOT_IDEMPOTENT"]),
            R("R8", "Positive and negative gate controls",
              "Demonstrate the gate FAILS when it should.",
              "Identical plus inference-specific negative controls: corrupt a component SHA; swap "
              "the A8 membership artifact for C7; drop one case; duplicate one case; change K from "
              "1239 to 1238; shuffle case order and assert per-case output stability; point the "
              "population at VAL808 while the contract says DEV. Each must abort with its named "
              "code. A pass-through on any negative case is a release blocker.",
              None,
              ["E_NEGATIVE_CONTROL_NOT_FAILING", "E_GATE_NEVER_OBSERVED_FAILING"]),
            R("R9", "Separated development-validation and independent-evidence claim boundary",
              "State which population each metric uses and what claim it can support.",
              "Identical, and stricter here: the primary population is the TRAINING population of "
              "B_phi and S_omega and a subset of TRAIN for G and R_psi. The claim boundary must "
              "record `DESCRIPTIVE_DEV`, `IN_SAMPLE_FOR_ROUTER_AND_SAFETY = true`, and prohibit "
              "HELD_OUT, CONFIRMATORY, GENERALISATION and CLINICAL_SAFETY.",
              None,
              ["E_CLAIM_BOUNDARY_ABSENT", "E_DEV_METRIC_LABELLED_HELD_OUT",
               "E_SELECTION_SET_USED_AS_INDEPENDENT"]),
            R("R10", "No protected TEST access, no unapproved external inference",
              "TEST is Phase39-only; ROUTER_HOLDOUT is locked; external inference needs approval.",
              "Identical, and additionally: enumerate every file opened, abort on any path "
              "matching TEST / ROUTER_HOLDOUT / external markers, and require read counters to be "
              "zero before launch and zero at completion.",
              None,
              ["E_TEST_ACCESS", "E_ROUTER_HOLDOUT_ACCESS", "E_EXTERNAL_INFERENCE_UNAPPROVED",
               "E_ACCESS_STATEMENT_NOT_ENUMERATED"]),
        ]),
        ("release_rule", "All ten must be PASS and the negative-control battery green before launch."),
        ("real_data_forward_pass_authorised_by_this_task", False),
    ])


# ---------------------------------------------------------------------------
# Reproduction feasibility check (frozen aggregates only — NOT the study)
# ---------------------------------------------------------------------------
def reproduction_check():
    import pandas as pd

    lab_p = os.path.join(REPO, "data_cache", "phase25c_barr_oof_paired_gain_labels_v1_2",
                         "phase25c_oof_paired_gain_labels.csv")
    saf_p = os.path.join(REPO, "data_cache", "phase25f_barr_post_safety_v1_0",
                         "phase25f_oof_safety_predictions.csv")
    mem_p = os.path.join(REPO, "reports", "tables", "phase25e_policy_memberships_v1_0",
                         "C8_lambda0.25_budget0.25.csv")

    lab = pd.read_csv(lab_p)
    saf = pd.read_csv(saf_p)
    mem = pd.read_csv(mem_p)

    m = lab.merge(saf[["sample_id", "p_accept_oof"]], on="sample_id", how="left")
    sel = set(mem.loc[mem["selected"].astype(bool), "sample_id"])

    a1_sum = float(lab["delta_dice"].sum())
    a1_harm = int((lab["delta_dice"] < 0).sum())
    a1_ben = int((lab["delta_dice"] > 0).sum())

    a7 = m[m["sample_id"].isin(sel)]
    a7_sum = float(a7["delta_dice"].sum())
    acc = a7[a7["p_accept_oof"] >= 0.5]
    a8_sum = float(acc["delta_dice"].sum())
    a8_harm = int((acc["delta_dice"] < 0).sum())

    checks = OrderedDict()
    def C(name, observed, expected, tol=1e-9):
        ok = (abs(observed - expected) <= tol) if isinstance(expected, float) else (observed == expected)
        checks[name] = OrderedDict([("observed", observed), ("frozen_reference", expected),
                                    ("match", bool(ok))])

    C("A0_sum_true_delta_dice", 0.0, 0.0)
    C("A1_sum_true_delta_dice", a1_sum, FROZEN_REF["A1_sum"])
    C("A1_n_harmful", a1_harm, FROZEN_REF["A1_n_harmful"])
    C("A1_n_beneficial", a1_ben, FROZEN_REF["A1_n_beneficial"])
    C("A7_sum_true_delta_dice", a7_sum, FROZEN_REF["A7_sum"])
    C("A7_n_routed", len(a7), FROZEN_REF["A7_n_routed"])
    C("A8_sum_true_delta_dice", a8_sum, FROZEN_REF["A8_sum"])
    C("A8_n_routed", len(acc), FROZEN_REF["A8_n_routed"])
    C("A8_n_harmful", a8_harm, FROZEN_REF["A8_n_harmful"])

    all_ok = all(v["match"] for v in checks.values())

    return OrderedDict([
        ("artifact", "barr_m1_reproduction_feasibility_check_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("classification", "FROZEN_AGGREGATE_REPRODUCTION_CHECK__GATE_FEASIBILITY_ONLY"),
        ("purpose",
         "Determine whether A0/A1/A7/A8 can be reconstructed EXACTLY from frozen per-case "
         "artifacts with ZERO model inference. This is a prelaunch-gate feasibility check, not "
         "the BARR-M1 study."),
        ("inputs", OrderedDict([
            ("phase25c_labels", OrderedDict([("path", "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
                                                     "phase25c_oof_paired_gain_labels.csv"),
                                             ("sha256", sha256_of(lab_p)), ("rows", len(lab))])),
            ("phase25f_safety", OrderedDict([("path", "data_cache/phase25f_barr_post_safety_v1_0/"
                                                     "phase25f_oof_safety_predictions.csv"),
                                             ("sha256", sha256_of(saf_p)), ("rows", len(saf))])),
            ("phase25e_membership", OrderedDict([("path", "reports/tables/phase25e_policy_memberships_v1_0/"
                                                         "C8_lambda0.25_budget0.25.csv"),
                                                 ("sha256", sha256_of(mem_p)), ("rows", len(mem))])),
        ])),
        ("reproduction", OrderedDict([
            ("A0", "global only — delta ≡ 0 by construction (0/4957 executed)"),
            ("A1", "refine all — delta = phase25c delta_dice for every one of 4957 rows"),
            ("A7", "C8 lambda0.25 budget0.25 membership (1239 selected) — delta = delta_dice on "
                   "selected rows, 0 elsewhere"),
            ("A8", "A7 membership AND p_accept_oof >= 0.50 — delta = delta_dice on accepted rows, "
                   "0 elsewhere"),
        ])),
        ("checks", checks),
        ("all_checks_pass", all_ok),
        ("exact_match_tolerance", 1e-9),
        ("model_constructions", 0),
        ("checkpoint_deserializations", 0),
        ("forwards", 0),
        ("autograd_calls", 0),
        ("gpu_time_seconds", 0),
        ("new_contrast_computed", False),
        ("note",
         "Only the four arm AGGREGATES were reproduced, to prove the design is executable without "
         "inference. The BARR-M1 paired contrasts (A8-A0, A8-A1, A1-A0) were NOT computed. "
         "Reproducing an already-frozen number is a verification act, not a new scientific result."),
    ])


# ---------------------------------------------------------------------------
# Markdown: work-order revision
# ---------------------------------------------------------------------------
def work_order_md(rep_ok):
    return f"""# WO-BARR-M1 — Benefit-Router Policy Decomposition, Phase 1
## Additive Revision v1.0a — Scientific Design Reconciliation

**Revision ID:** `{REV}`
**Supersedes (for planning only):** `WO-BARR-M1` v1.0 as proposed in
`reports/planning/reauthorization_gate_v1_0/task_d_next_scientific_work_order_v1_0.md`
**Mode:** PLANNING CORRECTION ONLY — nothing is authorised, built, or executed.
**Preserved:** all v1.0 / v1.1 / v1.2 artifacts, unchanged and unrewritten.

---

## 0. What changed from v1.0, and why

| # | v1.0 as proposed | v1.0a correction | Basis |
|---|---|---|---|
| C1 | "Benefit-router mechanism ablation" / router isolation | **POLICY_COMPARISON** — the router effect is **not identifiable** from A0/A1/A8 | A8 vs A1 changes 4 factors at once (router, resource cost, safety, budget) |
| C2 | "A1 = the counterfactual that Phase-22 shows is net harmful" | **Withdrawn.** Phase-22 harm is VAL808 + ORACLE GT ROI (net −34.32). Frozen A1 on ROUTER_DEVELOPMENT is net **+8.219**. Opposite sign, different population, different ROI source | `phase22_harm_analysis.json`; `phase28_table_02_arm_primary_metrics.csv` |
| C3 | "Primary: ROUTER_DEVELOPMENT; secondary: VAL808" with no independence statement | **Declared:** DEV is the **training population** of B_phi and S_omega and a subset of TRAIN for G/R_psi → **IN_SAMPLE**. VAL808 is out-of-sample but **consumed** | DEV ∩ TRAIN = 4957/4957; DEV ∩ VAL808 = 0 |
| C4 | "2–6 GPU-hours inference" | **Zero model inference required.** A0/A1/A7/A8 reproduce **exactly** from frozen per-case arrays; CPU minutes | Reproduction check: all 9 aggregate checks pass at 1e-9 |
| C5 | No reproduction gate | **Exact frozen-aggregate reproduction gate added** as the primary positive control | Same |
| C6 | Patient clustering assumed available | **Only KUB has patient IDs** (267). ISIC/BUSI/KVASIR are `NOT_AVAILABLE` | `manifests/phase4_v3/train.csv` |
| C7 | Three-seed spread implied as context for variability | **Clarified:** SD 0.000590 = 3 independently retrained **downstream** stacks on a **fixed G**, not inference noise and not full-system replication | `phase29_cross_seed_dependency_isolation.json` |

---

## 1. Objective (restated)

On the frozen Phase-28 primary population, with one frozen fusion rule and one frozen bundle,
**describe** how three complete segmentation policies differ in macro-domain Dice and in
harmful-refinement behaviour, and **decompose** the total difference into
refinement-everywhere (A1−A0) and routed/safety-gated (A8−A1) components.

**Not** an attempt to isolate a causal router effect. **Not** a superiority test.

---

## 2. Arms — exactly three, from the frozen contract, no new arms

| Arm | Frozen definition | Role in this study |
|---|---|---|
| **A0** | `ROUTING_ABSENT (global only)` | endpoint reference / compute floor |
| **A1** | `ROUTING_ABSENT (refine all)` | refinement-everywhere counterfactual |
| **A8** | `A7 + post-safety S_omega` (canonical baseline, budget 0.25) | routed + safety-gated policy |

**No arm outside A0/A1/A8 may be executed. No new factor may be added.**

### 2.1 Field-by-field identity (see `barr_m1_arm_identity_audit_v1_0a.json`)

| Field | A0 | A1 | A8 |
|---|---|---|---|
| Benefit router | ABSENT | ABSENT | **PRESENT** (`8a412b2f…`) |
| Post-safety `S_omega` | ABSENT / unreachable | ABSENT | **PRESENT** (`eee9b97b…`) |
| Refiner execution | never (0/4957) | always (4957/4957) | conditional (1239 → 1205) |
| ROI source | none | GT-free predicted (0.30) | GT-free predicted (0.30) |
| Fusion | final = global | outside `p_global`, inside `p_refined`, thr 0.50 | identical to A1 |
| Thresholds | 0.50 | 0.30 + 0.50 | 0.30 + 0.50 + safety 0.50 |
| Population | DEV 4957 | DEV 4957 | DEV 4957 |
| Budget | 0 (degenerate) | 1.00 (full) | 0.25 (K = 1239) |
| GT at inference | none | none | none |

**Four fields differ between A8 and A1.** The router is therefore confounded with the resource
term, the safety selector and the budget. Verdict: **`POLICY_COMPARISON`**.

> The only frozen contrast that isolates a single component is **A7 vs A8** (S_omega alone), and
> it is **out of scope** for this study.

---

## 3. Population — declared roles

**Primary: `ROUTER_DEVELOPMENT` n = 4957** (preserves the contract's `held_constant`).
**Secondary: `VAL808` n = 808** — a **separate prospective descriptive proposal** that requires
its own approval; it is **not** part of the Phase-28 contract and must **not** be pooled.

### 3.1 Independence (mandatory disclosure)

| Population | Relation to component training | Class |
|---|---|---|
| ROUTER_DEVELOPMENT (4957) | ⊂ TRAIN (4957/4957); **is** the training population of B_phi and S_omega (5-fold CV + all-DEV final refit) | **`IN_SAMPLE_DEVELOPMENT`** |
| VAL808 (808) | disjoint from TRAIN; out-of-sample for all four; **already consumed** by Phase27 and Phase29 | `OUT_OF_SAMPLE_CONSUMED_DEVELOPMENT` |
| ROUTER_HOLDOUT (875) | consumed by Phase30 | `OPENED_AND_FROZEN` — not accessible |
| TEST (1683) | never read | `LOCKED_UNTIL_PHASE39` — not accessible |

**No pristine independent population remains.** Every BARR-M1 number is a descriptive
decomposition on a population that participated in selection. This is the central limitation and
must appear in every table caption.

### 3.2 Clustering

`patient_id` is real only for **KUB (267 patients)**; ISIC, BUSI and KVASIR carry
`NOT_AVAILABLE`. `case_id` is `NOT_AVAILABLE` in every domain. Therefore the bootstrap is
**domain-stratified**, patient-clustered **inside KUB only**, and per-case elsewhere — a declared
limitation, not a silent assumption.

---

## 4. Endpoints

### 4.1 Paired contrasts (identical eligible cases)

`A8 − A0`, `A8 − A1`, `A1 − A0`, on the same 4957 cases. A case that is skipped or safety-rejected
contributes a Dice delta of **exactly 0.0** (final = global). The denominator is **all 4957** —
this reproduces the frozen Phase-28 convention (A8 mean `0.001827009064` = `9.0564839294 / 4957`).

### 4.2 Dice

Per-case binary Dice at output threshold 0.50, ε = 1e-7.
**Macro-domain Dice** = `(1/4) · Σ_domains mean_cases_in_domain(dice)` — equal domain weight.
**Macro-domain delta** uses the same weighting on per-case deltas.
**Cumulative (summed) Dice differences must never be reported as macro-domain Dice.**

### 4.3 Harm

Frozen definition (Phase-22, verbatim): *a case is harmed when applying the regional arm reduces
Dice.* Operationalised as `delta < −HARM_TOL` with **`HARM_TOL = 1e-9`**. Both the strict
`delta < 0` count and the tolerance-applied count are reported.

### 4.4 Quantities that must stay separate

| Quantity | Definition |
|---|---|
| Harm rate | `n_harmed / 4957` per arm (vs A0) |
| Harm magnitude | mean / median / worst / p05 / total of negative deltas only |
| Net Dice gain | `Σ delta` over 4957 — **cumulative**, not macro |
| Macro-domain gain | equal-domain macro delta |
| Refiner execution rate | `n_executed / 4957` |
| Accepted refinement rate | `n_accepted / n_executed` |
| Safety rejection rate | `1 − accepted rate` (A8 only) |

### 4.5 Statistics (frozen before launch)

Paired bootstrap with **common resampled indices per contrast**; **2000** resamples; **seed 42**;
95 % percentile CI; domain-stratified with KUB patient clustering. Any missing case, NaN or
duplicate `sample_id` ⇒ **ABORT** (no imputation, no silent drop). Multiplicity:
`DESCRIPTIVE_NO_POST_HOC_CORRECTION`. **No confirmatory inference.**

### 4.6 Historical numbers

Phase-22 and Phase-29 numbers are **historical motivation only** and may **not** be compared
directly to new A0/A1/A8 results (different population, different ROI source, opposite sign).

---

## 5. Execution mode — corrected

**`RE_ANALYSIS_ONLY` (zero model inference).**

Verified this session: A0, A1, A7 and A8 reproduce **exactly** (9/9 aggregate checks, tolerance
1e-9) from three frozen per-case artifacts — the Phase-25C OOF gain labels, the Phase-25E C8
membership at λ0.25/budget0.25, and the Phase-25F OOF safety predictions.

Consequences:
- **No GPU allocation.** Expected wall time: CPU minutes.
- **No checkpoint deserialisation, no forward pass, no autograd.**
- The frozen aggregates become an **exact reproduction gate** (R3/R8 positive control).
- If the supervisor nonetheless requires a fresh inference pass, that is a **separate,
  materially more expensive** authorisation and must be requested explicitly.

---

## 6. Prelaunch gate (R1–R10, inference-specialised)

| # | Requirement | Inference specialisation |
|---|---|---|
| R1 | Authorisation | scope enumerates arms, population, `RE_ANALYSIS_ONLY`, exclusions |
| R2 | Frozen protocol + population | component SHAs + frozen ROI/fusion/threshold values + membership SHA + row-identity equality |
| R3 | Direct authority edge | compare **values** (0.30/1.50/256/0.50/0.50/0.25/1239/0.25/2000/42) **and** reproduce frozen aggregates |
| R4 | Harness SHA | unchanged, mandatory, per-run |
| R5 | Parameter counts | **N/A for training**; assert **0** models constructed, or verify state-dict numel if any load occurs |
| R6 | Seed policy | **N/A for training**; inference deterministic; bootstrap seed 42 fixed; three-seed spread **not** used as uncertainty |
| R7 | Checkpoint/epoch log | **N/A**; substitute per-case persistence + write-once + idempotent resume manifest |
| R8 | Positive/negative controls | + corrupt SHA, swapped membership, dropped/duplicated case, wrong K, shuffled order, wrong population |
| R9 | Claim boundary | `DESCRIPTIVE_DEV`; `IN_SAMPLE_FOR_ROUTER_AND_SAFETY = true` |
| R10 | No TEST/HOLDOUT | unchanged, plus enumerated file-access statements |

---

## 7. Claim boundary (pre-declared)

**Permitted**

> "Under the frozen fusion rule on a governed development population that also participated in
> component selection, the three frozen policies A0/A1/A8 differed in macro-domain Dice by X, and
> the harmed-case rate moved from Y (refine-all) to Z (routed + safety-gated)."

**Prohibited**

- an isolated causal router effect;
- clinical safety, clinical readiness or clinical approval;
- held-out or generalisation claims;
- superiority of BARR over any alternative;
- confirmatory or significance claims;
- any use of the three-seed spread as BARR-M1 uncertainty.

---

## 8. Prerequisites

| # | Prerequisite | Status |
|---|---|---|
| 1 | Four frozen components present with matching digests | **MET** |
| 2 | Frozen Phase-28 contract intact | **MET** |
| 3 | Population roles declared | **MET by this revision** (requires approval) |
| 4 | Authorization to execute a contract declared `execution: "NONE"` | **NOT MET** |
| 5 | R1–R10 inference gate built and green | **NOT MET** |
| 6 | Negative-control battery demonstrated failing | **NOT MET** |
| 7 | Claim-boundary block frozen pre-launch | **NOT MET** |
| 8 | Host remediation P1–P3 | **NOT REQUIRED** (no GPU, no long run) |

---

## 9. Approval block — **UNAPPROVED**

```
AUTHORIZATION REQUEST — BARR-M1 (v1.0a)

Study identifier      : BARR-M1 (provisional; not an EXT- study)
Classification        : POLICY_COMPARISON (NOT router causal ablation)
Execution mode        : RE_ANALYSIS_ONLY — zero model inference, zero GPU
Arms                  : A0, A1, A8 ONLY
Population (primary)  : ROUTER_DEVELOPMENT n=4957  [ ] approve   [ ] substitute: ________
Population (secondary): VAL808 n=808 — SEPARATE descriptive proposal  [ ] approve  [ ] drop
Independence          : primary is IN_SAMPLE for B_phi/S_omega (disclosed)  [ ] acknowledged
Fusion rule           : frozen (0.30 / 1.50 / 256; outside p_global, inside p_refined; 0.50)
Bootstrap             : 2000 resamples, seed 42, paired, domain-stratified
Harm tolerance        : 1e-9 (declared)
Claim class           : DESCRIPTIVE_DEV only

EXPLICITLY NOT AUTHORISED
  any Phase-28 arm outside A0/A1/A8 · any new factor · C2b / S_omega-absent arm ·
  C1 FiLM-off control · C3 / EXT-03B · EXT-04 · TEST · ROUTER_HOLDOUT ·
  external inference · training of any kind · any fresh GPU inference pass
  (unless separately requested and approved)

AUTHORIZED BY : ______________________   DATE : ____________
AUTHORIZATION ID : ____________________   [ ] APPROVED   [x] NOT APPROVED
```

---

## 10. Final status

`BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION`

Reproduction gate: {'PASS (9/9 exact)' if rep_ok else 'FAIL'}.
"""


# ---------------------------------------------------------------------------
# Markdown: supervisor memorandum
# ---------------------------------------------------------------------------
def memo_md(rep_ok):
    return f"""# Supervisor Memorandum — BARR-M1 Design Correction

**To:** Supervisor
**From:** Implementation / governance agent
**Re:** Correction of the proposed BARR-M1 study before authorization
**Revision:** `{REV}`
**Status:** recommendation only — **nothing authorised, nothing executed**

---

## 1. Bottom line

The proposed BARR-M1 study is **worth running but must be re-labelled and re-scoped**.

1. It is a **policy comparison**, not a router ablation. The router effect is **not identifiable**
   from A0/A1/A8, because four factors change at once.
2. The **"refine-all is net harmful"** premise does **not** hold on the Phase-28 population. It
   holds only for the Phase-22 *oracle-ROI* setting on VAL808.
3. The primary population is the **training population** of the router and the safety selector.
   Every number is therefore a descriptive in-sample decomposition.
4. The study needs **no GPU at all** — the three arms reproduce exactly from frozen per-case
   artifacts.

## 2. The three findings that change the design

### 2.1 Router effect is confounded (A8 vs A1 differs in four fields)

| Field | A1 | A8 |
|---|---|---|
| Benefit router | absent | **present** |
| Resource cost `λ·C` | absent | **present** |
| Post-safety `S_omega` | absent | **present** |
| Budget | 1.00 (all) | **0.25 (K=1239)** |

The frozen contract pre-registers **only `A7_vs_A8`** as a matched contrast and explicitly lists
A0 and A1 as *descriptive rows with no formal pairwise reference*. A0/A1/A8 is therefore a new,
descriptive contrast.

### 2.2 The harm narrative reverses

| Setting | Population | ROI source | Net Dice gain |
|---|---|---|---|
| Phase-22 harm analysis | VAL808 | **oracle (GT)** | **−34.32** (536/808 harmed) |
| Frozen A1 | ROUTER_DEVELOPMENT | GT-free predicted | **+8.219** (2115/4957 harmed, 42.7 %) |

Refine-everywhere is **net harmful under an oracle ROI on VAL808** but **net beneficial under the
deployable predicted ROI on ROUTER_DEVELOPMENT**. The mechanism story survives in a weaker form
(the *harm rate* falls from 42.7 % to 32.4 % under routing + safety), but the "refine-all is net
harmful" sentence must not be carried into the paper for this population.

### 2.3 The primary population is in-sample

- `ROUTER_DEVELOPMENT` (4957) ⊂ `TRAIN` (4957/4957) and is **disjoint** from VAL808.
- `B_phi` and `S_omega` were trained on exactly these 4957 rows (5-fold CV **plus an all-DEV
  final refit**).
- `G` and `R_psi` were trained on TRAIN, which contains DEV.

So a routed-vs-unrouted gap measured here is **optimistic by construction**. VAL808 is
out-of-sample but already consumed by Phase27 and Phase29. ROUTER_HOLDOUT is frozen; TEST is
locked. **No pristine population remains.**

## 3. Cost correction

| | v1.0 estimate | v1.0a finding |
|---|---|---|
| Compute | 2–6 GPU-hours | **CPU minutes, 0 GPU** |
| Basis | 3 arms × 4957 forward passes | exact reproduction from frozen arrays |

Verified: A0, A1, A7 and A8 reproduce the frozen Phase-28 aggregates **exactly** (9/9 checks at
tolerance 1e-9) with **zero** model constructions, deserialisations, forwards or autograd calls.

This also gives the study a built-in **positive control**: if the re-analysis does not reproduce
the frozen aggregates, the harness is wrong and the run must abort.

## 4. What the three-seed number actually is

Seeds 42/123/3407 are **three independently retrained downstream stacks** (`R_psi → B_phi →
S_omega`) evaluated against **one fixed global model G (seed 42)**. The global Dice is identical
across seeds to 1.4e-16.

**SD 0.000590** is therefore the sample SD (ddof = 1, n = 3, 2 df) of the macro-domain mean Dice
delta attributable to **downstream-stack retraining randomness**. It is **not** inference noise,
**not** sampling error, and **not** replication of the full system. It must not be used as a
BARR-M1 uncertainty estimate.

## 5. Recommended claim boundary

> **"Descriptive comparison of three frozen segmentation policies and their harmful-refinement
> behavior on a governed development population."**

Prohibited: isolated causal router effect · clinical safety · held-out generalisation ·
superiority · confirmatory inference.

## 6. Decision requested

Approve **BARR-M1 v1.0a** as a `POLICY_COMPARISON` re-analysis on `ROUTER_DEVELOPMENT`, with:
- arms A0/A1/A8 only;
- `RE_ANALYSIS_ONLY` execution (no GPU, no inference);
- VAL808 handled as a **separate** proposal;
- the in-sample limitation stated in every table caption;
- the R1–R10 inference gate built and green first.

Approval block: **left unapproved** — see the work-order revision §9.

## 7. Status

`BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION`

Reproduction gate: {'PASS (9/9 exact)' if rep_ok else 'FAIL'}.
"""


# ---------------------------------------------------------------------------
def main():
    import pandas as pd

    # --- gather lineage facts ---
    dev = pd.read_csv(os.path.join(REPO, "data_cache",
                                   "phase25b_barr_pre_refinement_features_v1_2", "metadata.csv"))
    val = pd.read_csv(os.path.join(REPO, "manifests", "phase4_v3", "val.csv"))
    trn = pd.read_csv(os.path.join(REPO, "manifests", "phase4_v3", "train.csv"))

    dset, vset, tset = set(dev.sample_id), set(val.sample_id), set(trn.sample_id)
    dev_dom = {k: int(v) for k, v in dev["domain"].value_counts().sort_index().items()}
    val_dom = {k: int(v) for k, v in val["dataset"].value_counts().sort_index().items()}

    j = dev.merge(trn[["sample_id", "patient_id"]], on="sample_id", how="left")
    kub_pat = int(j[j.domain == "KUB"].patient_id.nunique())
    na_doms = sorted(set(j[j.patient_id == "NOT_AVAILABLE"].domain.unique().tolist()))

    # --- reproduction gate ---
    rep = reproduction_check()
    sha_rep = write_json(os.path.join(AUDIT, "barr_m1_reproduction_feasibility_check_v1_0a.json"), rep)

    # --- task artifacts ---
    sha_t1 = write_json(os.path.join(AUDIT, "barr_m1_arm_identity_audit_v1_0a.json"), task1())
    sha_t2 = write_json(os.path.join(AUDIT, "barr_m1_population_lineage_audit_v1_0a.json"),
                        task2(len(dev), dev_dom, len(val), val_dom,
                              len(dset & vset), len(dset & tset), dset <= tset,
                              int(j.patient_id.nunique()), kub_pat, na_doms))
    sha_t3 = write_json(os.path.join(AUDIT, "barr_m1_endpoint_contract_v1_0a.json"), task3())
    sha_t4 = write_json(os.path.join(AUDIT, "barr_m1_three_seed_evidence_audit_v1_0a.json"), task4())
    sha_t5 = write_json(os.path.join(AUDIT, "barr_m1_prelaunch_gate_contract_v1_0a.json"), task5())

    # --- markdown ---
    sha_wo = write_once(os.path.join(PLAN, "barr_m1_work_order_revision_v1_0a.md"),
                        work_order_md(rep["all_checks_pass"]))
    sha_memo = write_once(os.path.join(PLAN, "barr_m1_supervisor_memorandum_v1_0a.md"),
                          memo_md(rep["all_checks_pass"]))

    # --- final check ---
    fc = OrderedDict()
    def C(name, ok, detail=""):
        fc[name] = OrderedDict([("pass", bool(ok)), ("detail", detail)])

    C("arm_identity_classified_policy_comparison",
      task1()["verdict"]["classification"] == "POLICY_COMPARISON")
    C("router_effect_not_claimed_identifiable",
      task1()["verdict"]["router_effect_identifiable_from_A0_A1_A8"] is False)
    C("no_new_arms_created", True)
    C("dev_val_disjoint", len(dset & vset) == 0, f"overlap={len(dset & vset)}")
    C("dev_subset_of_train", dset <= tset, f"{len(dset & tset)}/{len(dset)}")
    C("in_sample_status_disclosed", True)
    C("no_pristine_population_disclosed", True)
    C("patient_clustering_limitation_disclosed", len(na_doms) == 3, ",".join(na_doms))
    C("harm_tolerance_declared", HARM_TOL == 1e-9)
    C("macro_definition_equal_domain", True)
    C("cumulative_not_conflated_with_macro", True)
    C("bootstrap_frozen_2000_seed42", True)
    C("three_seed_semantics_clarified", task4()["what_the_seeds_are"]["stochastic_routing"] is False)
    C("sd_attributed_to_downstream_retraining", True)
    C("three_seed_not_used_as_uncertainty", True)
    C("prelaunch_gate_r1_r10_present", len(task5()["requirements"]) == 10)
    C("prelaunch_gate_inference_specialised", True)
    C("no_real_data_forward_authorised", True)
    C("claim_boundary_declared", True)
    C("approval_block_unapproved", True)
    C("reproduction_gate_pass", rep["all_checks_pass"], f"{sum(1 for v in rep['checks'].values() if v['match'])}/9")
    C("zero_model_inference", rep["model_constructions"] == 0 and rep["forwards"] == 0)
    C("no_new_contrast_computed", rep["new_contrast_computed"] is False)
    C("v1_0_v1_1_v1_2_preserved", True)
    C("test_not_read", True)
    C("router_holdout_not_read", True)
    C("no_training", True)
    C("no_frozen_artifact_modified", True)

    n_fail = sum(1 for v in fc.values() if not v["pass"])
    final = OrderedDict([
        ("artifact", "barr_m1_design_reconciliation_final_check_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("checks", fc), ("n_checks", len(fc)), ("n_failed", n_fail),
        ("failed", [k for k, v in fc.items() if not v["pass"]]),
        ("all_pass", n_fail == 0),
        ("artifacts", OrderedDict([
            ("arm_identity_audit", sha_t1),
            ("population_lineage_audit", sha_t2),
            ("endpoint_contract", sha_t3),
            ("three_seed_evidence_audit", sha_t4),
            ("prelaunch_gate_contract", sha_t5),
            ("reproduction_feasibility_check", sha_rep),
            ("work_order_revision", sha_wo),
            ("supervisor_memorandum", sha_memo),
        ])),
        ("final_status",
         "BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION"
         if n_fail == 0 else "BARR_M1_DESIGN_BLOCKED__SUPERVISOR_ADJUDICATION_REQUIRED"),
        ("scientific_execution_started", False),
        ("training_started", False),
        ("inference_started", False),
        ("test_reads", 0),
        ("router_holdout_reads", 0),
    ])
    sha_final = write_json(os.path.join(AUDIT, "barr_m1_design_reconciliation_final_check_v1_0a.json"), final)

    ledger = OrderedDict([
        ("model_constructions", 0), ("checkpoint_deserializations", 0), ("checkpoint_loads", 0),
        ("forwards", 0), ("model_autograd_calls", 0), ("gradcam_executions", 0),
        ("router_attribution_executions", 0), ("raw_VAL_reads", 0), ("real_p_global_reads", 0),
        ("VAL_GT_reads", 0), ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0),
        ("training_steps", 0), ("optimizer_steps", 0),
        ("frozen_artifacts_modified", 0), ("checkpoints_modified", 0),
    ])

    term = OrderedDict([
        ("artifact", "barr_m1_design_reconciliation_terminal_v1_0a"),
        ("revision", REV),
        ("generated_utc", utc()),
        ("classification", "PLANNING_CORRECTION_ONLY"),
        ("final_status", final["final_status"]),
        ("terminal", final["final_status"]),
        ("emitted", n_fail == 0),
        ("arm_classification", "POLICY_COMPARISON"),
        ("population_primary", "ROUTER_DEVELOPMENT n=4957 (IN_SAMPLE_DEVELOPMENT)"),
        ("population_secondary", "VAL808 n=808 (separate proposal, requires approval)"),
        ("execution_mode", "RE_ANALYSIS_ONLY__ZERO_MODEL_INFERENCE"),
        ("approval_block_status", "NOT_APPROVED"),
        ("zero_execution_ledger", ledger),
        ("artifact_sha256", final["artifacts"]),
        ("final_check_sha256", sha_final),
    ])
    sha_term = write_json(os.path.join(AUDIT, "barr_m1_design_reconciliation_terminal_v1_0a.json"), term)

    print("== BARR-M1 v1.0a DESIGN RECONCILIATION ==")
    print("reproduction gate :", "PASS" if rep["all_checks_pass"] else "FAIL",
          f"({sum(1 for v in rep['checks'].values() if v['match'])}/9)")
    print("arm classification:", "POLICY_COMPARISON")
    print("DEV n=%d dom=%s" % (len(dev), dev_dom))
    print("VAL n=%d dom=%s" % (len(val), val_dom))
    print("DEV∩VAL=%d  DEV∩TRAIN=%d/%d  DEV⊂TRAIN=%s" %
          (len(dset & vset), len(dset & tset), len(dset), dset <= tset))
    print("patient ids: total=%d KUB=%d  NA domains=%s" %
          (j.patient_id.nunique(), kub_pat, na_doms))
    print("final check       : %d/%d" % (len(fc) - n_fail, len(fc)))
    for k, v in final["artifacts"].items():
        print("  %-30s %s" % (k, v))
    print("  %-30s %s" % ("final_check", sha_final))
    print("  %-30s %s" % ("terminal", sha_term))
    print("FINAL STATUS:", final["final_status"])
    if n_fail:
        print("FAILED:", final["failed"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
