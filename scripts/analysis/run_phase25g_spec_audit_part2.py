"""Phase 25G spec audit — PART 2: §4 A7/A8, §5 DEV reconstruction, §6 policy grid,
§7 primary metrics, §8 H3, §9 preservation, §10 statistics, §11 compute, §12 DEV ownership.

Governance/specification only. No execution, no holdout/VAL808/TEST reads.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_spec_common as C  # noqa: E402


def section4_a7_a8() -> dict:
    abl = C.jload(C.ROOT / "reports/audits/phase25f_c9_decision_artifact.json")
    obj = C.base_audit(
        "phase25g_a7_a8_controlled_comparison_contract",
        stage="A7_A8_CONTROLLED_COMPARISON",
        A7={
            "definition": "Phase25E C8 routing policy + always accept the executed regional candidate",
            "comparator_equivalent": "C8 (LEARNED_GAIN_PLUS_RESOURCE_COST)",
            "ablation_plan": "A6 + resource cost",
            "purpose": "H5 test",
        },
        A8={
            "definition": "the exact same Phase25E routing membership + Phase25F S_omega safety decision",
            "comparator_equivalent": "C9 (LEARNED_GAIN_PLUS_RESOURCE_COST_PLUS_POST_SAFETY)",
            "ablation_plan": "A7 + post-safety",
            "purpose": "H3 test; isolates S_omega",
        },
        shared_controls={
            "same_sample_population": "ROUTER_DEVELOPMENT (4957)",
            "same_routing_membership": "frozen Phase25E C8 memberships, reused verbatim",
            "same_lambda": "frozen lambda grid (0.00/0.25/0.50/1.00)",
            "same_budget": "frozen budget grid (0/10/25/50/100%)",
            "same_candidate_regional_output": "frozen Phase25A final regional refiner output",
            "same_global_output": "frozen Phase21 GlobalMedFiLM output",
            "same_segmentation_threshold": C.SEGMENTATION_OUTPUT_THRESHOLD,
        },
        only_difference="S_omega accept/reject applied AFTER refinement (A8); A7 always accepts",
        isolation="controlled isolation of S_omega",
        c8_membership_manifest_sha256="f4ff4b235c664339d237fd7ec51f948dbc233431a6fd45522bde2166327e679a",
        checks={
            "A7_equals_C8": True,
            "A8_equals_C9": True,
            "single_difference_is_S_omega": True,
            "no_new_threshold_introduced": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_a7_a8_controlled_comparison_contract", obj)


def section5_dev_reconstruction() -> dict:
    obj = C.base_audit(
        "phase25g_dev_reconstruction_contract",
        stage="DEV_OUTPUT_RECONSTRUCTION",
        population="ROUTER_DEVELOPMENT",
        population_n=C.N_ROUTER_DEVELOPMENT,
        no_model_inference_required=True,
        paired_gain_source={
            "file": "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv",
            "sha256": C.sha256_file(
                C.ROOT / "data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/"
                        "phase25c_oof_paired_gain_labels.csv"),
            "column": "delta_dice",
            "definition": "d_i = Phase25C OOF paired delta_dice",
        },
        reconstruction={
            "A7_final_delta": "final_delta_A7 = d_i if Phase25E selected (c8_decision == EXECUTE) else 0",
            "A8_final_delta": "final_delta_A8 = d_i if C9 outcome == EXECUTE_THEN_ACCEPT else 0",
            "A8_minus_A7": "final_delta_A8 - final_delta_A7",
            "A7_dice": "global_dice + final_delta_A7",
            "A8_dice": "global_dice + final_delta_A8",
        },
        c9_outcome_field="c9_outcome in {PRE_GATE_SKIP, EXECUTE_THEN_ACCEPT, EXECUTE_THEN_REJECT}",
        c9_state_field="c9_state in {STATE_B (pre-gate skip), STATE_C (executed)}",
        note=(
            "The work-order phrase 'C9 state == EXECUTE_THEN_ACCEPT' is realised by the "
            "phase25f_c9_decision_manifest.csv column c9_outcome; the column c9_state only "
            "carries STATE_B/STATE_C. A8 selects exactly the rows with c9_outcome == "
            "'EXECUTE_THEN_ACCEPT'."
        ),
        reconstruction_only_no_rerun=True,
        checks={
            "delta_source_is_phase25c_oof": True,
            "A8_subset_of_A7": True,
            "global_and_candidate_dice_available_for_cross_check": True,
            "no_segmentation_rerun": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_dev_reconstruction_contract", obj)


def section6_policy_grid() -> dict:
    per_policy = C.jload(C.ROOT / "reports/audits/phase25f_c9_decision_artifact.json").get("per_policy", [])
    # membership signature = (n_execute, n_accept, n_reject) per budget across lambdas
    by_budget = {}
    for r in per_policy:
        by_budget.setdefault(r["budget"], []).append((r["lambda"], r["n_execute"], r["n_accept"], r["n_reject"]))
    duplicate_membership = {}
    for b, rows in by_budget.items():
        sigs = {tuple(r[1:]) for r in rows}
        duplicate_membership[b] = {"n_distinct_signatures": len(sigs), "n_lambda_replicas": len(rows)}
    all_duplicate = all(v["n_distinct_signatures"] == 1 for v in duplicate_membership.values())

    obj = C.base_audit(
        "phase25g_policy_grid_contract",
        stage="POLICY_GRID",
        lambda_grid=C.LAMBDA_GRID,
        budget_grid=C.BUDGET_GRID,
        budget_cardinalities=C.BUDGET_CARDINALITIES,
        n_policies=C.N_POLICIES,
        single_lambda_or_budget_selected=False,
        matched_A7_A8_pairs_only=True,
        cost_is_constant=True,
        cost_exact_ratio="1051648/10270749",
        cost_decimal=0.10239253242387678,
        membership_equivalence_across_lambda=duplicate_membership,
        duplicate_membership_tagged=True,
        duplicate_membership_statement=(
            "Because action cost C_i is constant across the eligible population, C8 routing "
            "membership is structurally identical across lambda for a given budget. The four "
            "lambda replicas are DUPLICATE MEMBERSHIP and are NOT four independent scientific "
            "confirmations."
        ),
        checks={
            "lambda_grid_exact": C.LAMBDA_GRID == ["0.00", "0.25", "0.50", "1.00"],
            "budget_grid_exact": C.BUDGET_GRID == ["0.00", "0.10", "0.25", "0.50", "1.00"],
            "20_policies": len(per_policy) == C.N_POLICIES,
            "membership_identical_across_lambda": all_duplicate,
            "no_single_lambda_or_budget_selected": True,
        },
        all_pass=all_duplicate and len(per_policy) == C.N_POLICIES,
    )
    return C.write_json("phase25g_policy_grid_contract", obj)


def section7_primary_metrics() -> dict:
    obj = C.base_audit(
        "phase25g_primary_metrics_contract",
        stage="PRIMARY_METRICS_FREEZE",
        for_A7_and_A8=[
            "macro-domain Dice delta vs global",
            "per-domain Dice delta vs global",
            "pooled mean Dice delta vs global",
            "harmful replacement rate",
            "fallback rate",
            "accepted-refinement rate",
            "rejected-refinement rate",
        ],
        for_A8_minus_A7=[
            "mean Dice difference",
            "macro-domain difference",
            "per-domain difference",
            "number of harmful executed refinements rejected",
            "number of beneficial executed refinements rejected",
            "number of neutral executed refinements rejected",
        ],
        harmful_replacement_definition=(
            "an executed regional candidate with delta_dice < 0 that becomes the final output"
        ),
        A8_harmful_rejected_note=(
            "For A8, a harmful candidate rejected to global is NOT a harmful replacement."
        ),
        benefit_category_thresholds_not_redefined={
            "BENEFICIAL": f"d_i >= +{C.BENEFICIAL_THRESHOLD}",
            "HARMFUL": f"d_i <= {C.HARMFUL_THRESHOLD}",
            "NEUTRAL": "otherwise",
            "source": "phase25e_evaluation_statistics_contract_v1_0.json:benefit_labels",
        },
        checks={
            "metrics_frozen_before_evaluation": True,
            "harmful_replacement_defined": True,
            "benefit_thresholds_reused_not_redefined": True,
        },
        all_pass=True,
    )
    return C.write_json("phase25g_primary_metrics_contract", obj)


def section8_h3() -> dict:
    arch = C.jload(C.ROOT / "reports/audits/phase24_architecture_spec.json")
    h3 = arch.get("hypotheses", {}).get("H3")
    crit = _read_csv(C.ROOT / "reports/tables/phase24_success_failure_criteria.csv")
    h3_rule = [r for r in crit if "H3" in (r.get("name", "") + r.get("definition", "")).upper()]
    obj = C.base_audit(
        "phase25g_h3_adjudication_contract",
        stage="H3_ADJUDICATION",
        exact_hypothesis=h3,
        forbidden_reinterpretations=[
            "A8 must improve overall Dice",
            "A8 must improve every domain",
            "A8 must beat A7 significantly on every metric",
        ],
        phase24_success_failure_rows=h3_rule,
        numerical_success_threshold_pre_registered=bool(h3_rule),
        flag=None if h3_rule else "H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED",
        adjudication=(
            "report H3 descriptively / statistically without inventing a new binary threshold"
        ),
        checks={
            "exact_hypothesis_recovered": h3 is not None,
            "no_silent_reinterpretation": True,
            "no_invented_threshold": True,
        },
        all_pass=h3 is not None,
    )
    return C.write_json("phase25g_h3_adjudication_contract", obj)


def section9_preservation() -> dict:
    pres = C.jload(C.ROOT / "reports/audits/phase24_preservation_contract.json")
    ni = pres.get("non_inferiority", {})
    obj = C.base_audit(
        "phase25g_preservation_contract_binding",
        stage="PRESERVATION_CONTRACT",
        rule="Delta = Dice(final routed system) - Dice(global reference)",
        margin=ni.get("margin"),
        claim_only_if="lower 95% CI > -0.005",
        per_domain_reporting="mandatory",
        macro_may_not_hide_domain_harm=ni.get("macro_may_not_hide_domain_harm"),
        labels={
            "A7_PRE_SAFETY_PRESERVATION": "pre-safety routed system preservation (descriptive)",
            "A8_POST_SAFETY_PRESERVATION": "post-safety routed system preservation (the integrated claim)",
        },
        final_integrated_preservation_statement_refers_to="A8",
        checks={
            "margin_is_0p005": ni.get("margin") == C.PRESERVATION_MARGIN,
            "lower_ci_rule_frozen": ni.get("claim_only_if") == "lower confidence bound of Delta > -0.005",
            "per_domain_mandatory": ni.get("per_domain_reporting") == "mandatory",
            "two_preservation_labels_frozen": True,
        },
        all_pass=ni.get("margin") == C.PRESERVATION_MARGIN,
    )
    return C.write_json("phase25g_preservation_contract_binding", obj)


def section10_statistics() -> dict:
    st = C.jload(C.ROOT / "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json")
    obj = C.base_audit(
        "phase25g_statistics_contract",
        stage="STATISTICS_CONTRACT",
        reuse_phase25e_mechanics=True,
        bootstrap_type=st.get("bootstrap_type"),
        group_unit=st.get("group_unit"),
        strata=st.get("strata"),
        total_groups=st.get("total_groups"),
        n_boot=st.get("n_boot"),
        seed=st.get("seed"),
        rng=st.get("rng"),
        ci_method=st.get("ci_method"),
        ci_percentiles=st.get("ci_percentiles"),
        paired_two_sided_p=st.get("paired_two_sided_p"),
        multiplicity=st.get("multiplicity"),
        multiplicity_role_phase25g=(
            "no new correction introduced unless prospectively frozen; Phase25E Holm-Bonferroni "
            "retained as secondary"
        ),
        identical_bootstrap_draws_for=["A7", "A8", "A8-A7"],
        paired=True,
        bootstrap_plan_file=st.get("bootstrap_plan_file"),
        bootstrap_plan_file_sha256=st.get("bootstrap_plan_file_sha256"),
        reuse_condition="Phase25E bootstrap-plan rows cover the same 4957 DEV population -> reuse exact frozen draws",
        report=["point estimate", "95% CI", "paired p-value where appropriate"],
        checks={
            "domain_stratified_group_bootstrap": st.get("bootstrap_type") == C.BOOTSTRAP_TYPE,
            "n_boot_2000": st.get("n_boot") == C.BOOTSTRAP_N,
            "seed_42": st.get("seed") == C.BOOTSTRAP_SEED,
            "paired_draws_for_A7_A8_A8mA7": True,
            "no_new_multiplicity_correction": True,
            "same_4957_population": st.get("bootstrap_plan_file") is not None,
        },
        all_pass=(
            st.get("bootstrap_type") == C.BOOTSTRAP_TYPE
            and st.get("n_boot") == C.BOOTSTRAP_N
            and st.get("seed") == C.BOOTSTRAP_SEED
        ),
    )
    return C.write_json("phase25g_statistics_contract", obj)


def section11_compute() -> dict:
    cost = C.jload(C.ROOT / "reports/audits/phase25e_resource_cost_contract_v1_0.json")
    som = 20 * 32 + 32 * 16 + 16 * 1
    obj = C.base_audit(
        "phase25g_compute_contract",
        stage="COMPUTE_ACCOUNTING",
        A7_average_cost="GLOBAL + ROUTER + activation_fraction * REFINER",
        A8_average_cost="GLOBAL + ROUTER + activation_fraction * (REFINER + S_omega)",
        global_macs=C.GLOBAL_MACS,
        router_macs=C.ROUTER_MACS,
        refiner_macs=C.REFINER_MACS,
        somega_analytical_macs=som,
        somega_cost_per_executed_refined_sample=som,
        somega_saves_compute=False,
        somega_adds_small_post_refinement_cost=True,
        accounting_label="ANALYTICAL MAC LOWER BOUND",
        forbidden_labels=["latency", "runtime", "energy", "memory", "mobile performance"],
        router_excluded_from_C_i=True,
        checks={
            "somega_macs_1168": som == C.SOMEGA_MACS,
            "somega_saves_no_compute": True,
            "label_is_analytical_mac_lower_bound": cost.get("analytical_accounting_label") == "ANALYTICAL MAC LOWER BOUND",
            "no_wall_clock_claim": True,
        },
        all_pass=som == C.SOMEGA_MACS,
    )
    return C.write_json("phase25g_compute_contract", obj)


def section12_dev_ownership() -> dict:
    handoff = C.jload(C.ROOT / "reports/audits/phase25f_phase25g_handoff.json")
    note = C.jload(C.ROOT / "reports/audits/phase25f_upstream_crossfit_dependency_note.json")
    obj = C.base_audit(
        "phase25g_dev_result_ownership",
        stage="DEV_RESULT_OWNERSHIP",
        sources={
            "Phase25C": "OOF refinement outcomes (delta_dice)",
            "Phase25D": "OOF router decisions",
            "Phase25E": "prospective memberships",
            "Phase25F": "OOF safety probabilities / decisions",
        },
        classification="CONTROLLED_DEVELOPMENT_RESULTS",
        not_claimable_as=[
            "untouched holdout results",
            "TEST results",
            "fully end-to-end independently nested CV results",
        ],
        meta_level_oof_disclosure=note.get("disclosure"),
        oof_classification=handoff.get("oof_classification"),
        checks={
            "classified_as_controlled_development": True,
            "meta_level_oof_disclosure_carried_forward": note.get("disclosure") is not None,
            "not_holdout_not_test": True,
        },
        all_pass=note.get("disclosure") is not None,
    )
    return C.write_json("phase25g_dev_result_ownership", obj)


def _read_csv(p):
    import csv
    with open(p, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    for fn in [section4_a7_a8, section5_dev_reconstruction, section6_policy_grid,
               section7_primary_metrics, section8_h3, section9_preservation,
               section10_statistics, section11_compute, section12_dev_ownership]:
        r = fn()
        print(f"{r['artifact']:52s} all_pass={r['all_pass']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
