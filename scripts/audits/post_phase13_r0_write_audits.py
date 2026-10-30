"""POST-PHASE-13 R0 — write the failure-decomposition and frozen-protocol artifacts."""
from __future__ import annotations

import hashlib
import json
import importlib.util
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
ADJ_UTC = "2026-09-22T05:52:00Z"

BINDINGS = {
    "final_gate": ("reports/audits/phase13_regional_integration_gate_after_phase13.json",
                   "4436e6a5e13b99d422cfab1668c3f3f2d43993b4c43b19786308d106185a6c75"),
    "part1d_b_evaluation": ("reports/audits/phase13_part1d_b_predicted_region_evaluation.json",
                            "9a9838ac64af5109c13e0625066e6b891068c93ef5b726f89f03a65e4828ad28"),
    "part1c_proposals": ("reports/tables/phase13_part1c_best_checkpoint_proposals.csv",
                         "8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a"),
    "part1c_case_proposals": ("reports/tables/phase13_part1c_best_checkpoint_case_proposals.csv",
                              "d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed"),
    "part1c_component_coverage": ("reports/tables/phase13_part1c_best_checkpoint_component_coverage.csv",
                                  "2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87"),
    "part1d_b_case_model": ("reports/tables/phase13_part1d_predicted_region_case_model_metrics.csv",
                            "53e93982c0235e32568e01fbddbdd858d205077e3e0a50fd69bef992454f2658"),
    "part1d_b_component_model": ("reports/tables/phase13_part1d_predicted_region_component_model_metrics.csv",
                                 "f82e0632898467d32916eb0b71a9fff75818548665477052e2db9b365d313c9d"),
}


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_r0():
    spec = importlib.util.spec_from_file_location(
        "r0", str(ROOT / "scripts" / "audits" / "post_phase13_r0_failure_decomposition.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, m.main()


def main() -> None:
    m, r = load_r0()
    diag, sep, floors = r["diag"], r["sep"], r["floors"]
    burden, linkage, imp_wor, rec, fam = r["burden"], r["linkage"], r["imp_wor"], r["rec"], r["family"]

    bind = {k: {"path": p, "sha": sha(ROOT / p), "expected": e,
                "match": sha(ROOT / p) == e} for k, (p, e) in BINDINGS.items()}
    assert all(v["match"] for v in bind.values()), "binding mismatch"

    rho = linkage.pivot_table(index=["x_quantity", "y_quantity"], columns="model",
                              values="spearman_rho")

    def rhos(x, y):
        return {k: float(rho.loc[(x, y), k]) for k in r["MODELS"]}

    off_vs_fp = rhos("off_target_support_fraction", "fp_pixel_delta")
    miss_vs_fp = rhos("gt_miss_proposal_count", "fp_pixel_delta")
    miss_vs_dice = rhos("gt_miss_proposal_count", "predicted_minus_global_dice")
    off_vs_dice = rhos("off_target_support_fraction", "predicted_minus_global_dice")
    cnt_vs_fp = rhos("total_proposal_count", "fp_pixel_delta")
    top_vs_dice = rhos("top_proposal_score", "predicted_minus_global_dice")

    # ---------------- failure decomposition ----------------
    dec = {
        "artifact": "POST_PHASE13_REGIONAL_REVISION_R0_FAILURE_DECOMPOSITION",
        "status": "PASS",
        "created_utc": ADJ_UTC,
        "branch": "SEPARATE_POST_PHASE13_REVISION_BRANCH",
        "phase13_evidence_reopened_or_rewritten": "NO",
        "analysis_only": "YES",
        "bindings": bind,
        "inputs": {
            "proposals_analyzed": int(len(r["prop"])),
            "cases": int(burden.shape[0]),
            "case_model_rows": 412,
            "component_model_rows": 608,
            "components": int(rec[rec["event"] == "recovered"]["n_components"].iloc[0] +
                              rec[rec["event"] == "not_recovered"]["n_components"].iloc[0]),
        },
        "s5_proposal_score_rank_diagnostics": {
            "table": "reports/tables/post_phase13_r0_proposal_score_rank_diagnostics.csv",
            "per_rank": diag.to_dict(orient="records"),
            "gt_hit_proposals": int(r["prop"]["gt_hit_pixel"].sum()),
            "gt_miss_proposals": int((~r["prop"]["gt_hit_pixel"]).sum()),
            "gt_miss_fraction": float((~r["prop"]["gt_hit_pixel"]).mean()),
            "note": "no threshold tuned here; no threshold called optimal",
        },
        "s6_score_separability": {
            **sep,
            "rank_conditional_pixel_hit_rates": {
                str(int(x.proposal_rank)): float(x.pixel_any_hit_rate) for x in diag.itertuples()},
            "score_saturation_finding": (
                "The proposal score is near-degenerate: 337/494 (68.22%) sit exactly at the maximum "
                "0.125065, the full range is only 0.024717 and the IQR is 0.000533. The score is "
                "therefore saturated, yet still informative: the saturated group hits GT at 0.3353 "
                "versus 0.0573 for the below-maximum group (5.85x). ROC-AUC 0.670611 and PR-AUC "
                "0.305819 against a 0.246964 base rate (lift 1.24x). Reported strictly as diagnostics, "
                "not as deployment-performance claims; no threshold was chosen from labels here."),
            "rank_ordering_caveat": (
                "Because 102/103 rank-1 and 91/103 rank-2 proposals are saturated, ordering WITHIN the "
                "saturated group is effectively a tie-break. Rank-2 has a higher hit rate (0.398058) "
                "than rank-1 (0.339806), which is consistent with arbitrary tie ordering rather than a "
                "meaningful confidence ordering."),
        },
        "s6_floor_tradeoff_label_blind": {
            "table_note": "floors q10/q25/max are MARGINAL score quantiles computed WITHOUT GT labels",
            "floors": floors,
            "finding": (
                "Every marginal-derived floor removes far more off-target proposals than GT-hit "
                "proposals: q10 (0.119470) rejects 50 off-target proposals and 0 hits; q25 (0.124532) "
                "rejects 118 off-target and 4 hits (3.28% of all hits); the marginal maximum "
                "(0.125065) rejects 148 off-target (39.78% of all off-target) and 9 hits (7.38%). "
                "This is the strongest proposal-level evidence that selective acceptance can reduce "
                "off-target intervention at low hit cost."),
            "gt_labels_used_to_change_the_family": "NO",
        },
        "s7_case_off_target_burden": {
            "table": "reports/tables/post_phase13_r0_case_proposal_burden.csv",
            "rows": int(burden.shape[0]),
            "summary": {
                "proposal_count_mean": float(burden["proposal_count"].mean()),
                "gt_hit_proposal_count_mean": float(burden["gt_hit_proposal_count"].mean()),
                "gt_miss_proposal_count_mean": float(burden["gt_miss_proposal_count"].mean()),
                "fraction_proposals_off_target_mean": float(burden["fraction_proposals_off_target"].mean()),
                "proposal_union_area_fraction_mean": float(burden["proposal_union_area_fraction"].mean()),
                "off_target_proposal_union_area_fraction_mean":
                    float(burden["off_target_proposal_union_area_fraction"].mean()),
                "off_target_share_of_union_area_mean": float(
                    (burden["off_target_proposal_union_area_fraction"] /
                     burden["proposal_union_area_fraction"].replace(0, pd.NA)).mean()),
                "top_proposal_score_mean": float(burden["top_proposal_score"].mean()),
                "minimum_accepted_score_under_old_policy": 0.10,
            },
            "new_inference": "NONE",
            "off_target_union_area_derivation": "DETERMINISTIC from frozen clip geometry + frozen GT-hit flags",
        },
        "s8_proposal_to_segmentation_linkage": {
            "table": "reports/tables/post_phase13_r0_proposal_to_segmentation_linkage.csv",
            "scatter_table": "reports/tables/post_phase13_r0_proposal_to_segmentation_scatter.csv",
            "spearman_rho": {
                "off_target_support_fraction__vs__fp_pixel_delta": off_vs_fp,
                "gt_miss_proposal_count__vs__fp_pixel_delta": miss_vs_fp,
                "gt_miss_proposal_count__vs__predicted_minus_global_dice": miss_vs_dice,
                "off_target_support_fraction__vs__predicted_minus_global_dice": off_vs_dice,
                "total_proposal_count__vs__fp_pixel_delta": cnt_vs_fp,
                "top_proposal_score__vs__predicted_minus_global_dice": top_vs_dice,
            },
            "dominant_association": (
                "off_target_support_fraction is the strongest descriptor of the FP burden, "
                "rho = 0.5918 to 0.6372, positive and consistent across all four architectures. "
                "Total proposal count is a weak positive descriptor (0.2509 to 0.2613). "
                "GT-miss COUNT is only weakly associated with FP delta (0.0960 to 0.2208) and "
                "essentially unassociated with Dice delta (-0.0921 to 0.0814). "
                "Top proposal score is unassociated with Dice delta (-0.1032 to 0.1232)."),
            "interpretation_language": "ASSOCIATION__DESCRIPTIVE_LINKAGE",
            "causal_claim": "NONE",
            "p_value_claimed": "NO",
        },
        "s9_improved_vs_worsened_context": {
            "table": "reports/tables/post_phase13_r0_improved_vs_worsened_context.csv",
            "findings": (
                "Improved cases carry MORE GT-hit proposals than worsened cases "
                "(1.60/2.20/1.75/1.73 vs 1.14/1.13/1.14/1.12) and a LARGER proposal union area "
                "(0.00718/0.00810/0.00709/0.00663 vs 0.00460/0.00468/0.00466/0.00463), while the "
                "GT-miss proposal count is similar (3.40/2.80/3.25/3.27 vs 3.63/3.65/3.64/3.65). "
                "Improved cases have LOWER Part-1C bbox_covered90 fraction "
                "(0.450/0.200/0.250/0.318 vs 0.629/0.633/0.642/0.647), i.e. improvement concentrates "
                "where the GLOBAL path was already struggling. FP delta is higher in improved cases."),
            "interpretation": "DIAGNOSTIC_ONLY__NO_NEW_GATE_SUBGROUP__NO_CLASSIFIER_DEFINED",
            "implication_for_revision": (
                "Improvement and FP burden both scale with intervention coverage, so a policy that "
                "reduces accepted proposals trades recovery against FP cost. This is precisely the "
                "trade-off the bounded R1 policy ablation must measure."),
        },
        "s10_component_recovery_context": {
            "table": "reports/tables/post_phase13_r0_component_recovery_context.csv",
            "component_losses_in_frozen_phase13": {
                k: int(v) for k, v in
                rec[rec["event"] == "lost"].set_index("model")["n_components"].items()},
            "recovered_components_bbox_any_overlap_rate": {
                k: float(v) for k, v in
                rec[rec["event"] == "recovered"].set_index("model")["bbox_any_overlap_rate"].items()},
            "finding": (
                "Every recovered component (16/9/14/16) had bbox_any_overlap_rate 1.000, i.e. "
                "component recovery requires at least one proposal to overlap the component. "
                "Component losses are 0 for all four architectures and must NOT be erased by the FP "
                "failure. TINY recoveries 9/4/5/8; SMALL 4/2/3/3; MEDIUM 2/3/5/4; LARGE 1/0/1/1."),
            "favourable_evidence_preserved": "YES",
        },
        "s11_hypothesis_hierarchy": {
            "H1_SELECTIVE_PROPOSAL_ACCEPTANCE_ABSTENTION": {
                "rank": 1, "status": "SELECTED_AS_FIRST_REVISION",
                "changed_axis": "WHICH_ALREADY_PRODUCED_PROPOSALS_ARE_ACCEPTED_FOR_REGIONAL_INTERVENTION",
                "held_constant": ["localizer weights", "segmentation checkpoints",
                                  "proposal geometry generation", "margin 0.20", "NMS 0.30",
                                  "regional crop/restore", "regional replacement fusion",
                                  "segmentation threshold 0.5"],
                "zero_acceptance_allowed": "YES",
            },
            "H2_LOCALIZER_RETRAINING_SELECTION_REDESIGN": {
                "rank": 2, "status": "NOT_SELECTED__CONDITIONAL_ON_H1",
                "motivation": "the existing localizer was selected primarily for recall and intervention "
                              "area rather than deployable proposal precision",
                "new_loss_designed": "NO",
            },
            "H3_FUSION_ROUTING_REDESIGN": {
                "rank": 3, "status": "NOT_SELECTED__CONDITIONAL_ON_H1_H2",
                "concept": "adaptive / confidence-aware regional routing",
                "implemented_or_frozen": "NO",
            },
            "simultaneous_change": "FORBIDDEN",
        },
        "s18_conclusion": {
            "choice": "H1_FIRST_SELECTIVE_ACCEPTANCE",
            "why_minimum_justified_change": (
                "H1 is the only axis that is simultaneously (a) directly implicated by the evidence, "
                "(b) achievable with ZERO training, ZERO checkpoint change, ZERO geometry change and "
                "ZERO fusion change, and (c) reversible. The frozen evidence shows the failure is an "
                "intervention-precision failure, not a representation failure: 122 GT-hit proposals "
                "already exist and 27 components are recovered with 0 losses, so the localizer does "
                "produce usable targets. What is missing is a mechanism to decline the 372 off-target "
                "proposals, and the off-target support fraction is the strongest descriptor of the FP "
                "burden (rho 0.5918-0.6372, consistent across all four architectures). The score, "
                "although saturated, retains moderate discriminative information (ROC-AUC 0.670611), "
                "and every label-blind marginal floor removes strictly more off-target than GT-hit "
                "proposals (q10 removes 50 off-target and 0 hits). H2 would change the model weights "
                "before establishing whether the existing weights are the limiting factor, and H3 "
                "would confound the analysis by changing the fusion rule while the accept/reject "
                "policy is still untested. H1 is therefore the lowest-complexity intervention capable "
                "of testing a credible explanation of the Phase-13 failure."),
            "this_is_a_revision_development_ordering_decision": "YES",
            "is_go_no_go_or_promotion": "NO",
        },
        "counters": {"training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
                     "localizer_forwards": 0, "segmentation_forwards": 0, "regional_crop_forwards": 0,
                     "proposal_regeneration": 0, "checkpoint_writes": 0, "test_reads": 0,
                     "external_test_reads": 0},
        "next_action": "WAIT_FOR_SUPERVISOR_REVISION_R1_AUTHORIZATION",
    }
    (AUDITS / "post_phase13_regional_revision_r0_failure_decomposition.json").write_text(
        json.dumps(dec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------- frozen protocol ----------------
    proto = {
        "artifact": "POST_PHASE13_REGIONAL_REVISION_R0_PROTOCOL_FROZEN",
        "status": "REVISION_PROTOCOL_FROZEN_BEFORE_R1_EXECUTION",
        "created_utc": ADJ_UTC,
        "revision_branch": "POST_PHASE13_REGIONAL_REVISION",
        "phase13_evidence_reopened": "NO",
        "phase13_gate_verdict": "REVISE_LOCALIZER",
        "oracle_mechanism_value": "SUPPORTED_DESCRIPTIVE_EVIDENCE",
        "revision_question": (
            "Which single failure axis should be tested FIRST: proposal acceptance/abstention, "
            "localizer representation/training/selection, or regional fusion/gating? The future "
            "experiment must change only ONE primary scientific axis at a time."),
        "selected_first_axis": "H1_SELECTIVE_PROPOSAL_ACCEPTANCE_ABSTENTION",
        "hypothesis_under_test": "SELECTIVE_REGIONAL_INTERVENTION_WITH_ABSTENTION",
        "hypothesis_promoted": "NO__UNDER_TEST_IN_R1",
        "safety_property_relied_upon": {
            "statement": "if no predicted proposal is accepted then PREDICTED output == GLOBAL output exactly",
            "source": "frozen Part-1D-B fusion semantics (P(x) = R(x) if U_pred(x) else G(x))",
            "consequence": "maximum proposal recall is not required; abstention is a legitimate outcome",
        },
        "selective_abstention_principle_assessment": {
            "verdict": "SUPPORTED",
            "supporting_evidence": [
                "score retains moderate discriminative information despite saturation (ROC-AUC 0.670611, PR-AUC 0.305819 vs 0.246964 base rate)",
                "saturated proposals hit GT at 0.3353 vs 0.0573 below maximum (5.85x)",
                "every label-blind marginal floor removes more off-target than GT-hit proposals (q10: 50 off-target, 0 hits)",
                "off-target support fraction is the strongest descriptor of FP burden (rho 0.5918-0.6372, all four architectures)",
                "the fusion rule already provides exact GLOBAL fallback when nothing is accepted",
            ],
            "counter_evidence_recorded": [
                "proposal scores are near-degenerate: 337/494 saturated at 0.125065, range 0.024717, IQR 0.000533",
                "rank ordering within the saturated group is effectively a tie-break",
                "improved cases carry MORE GT-hit proposals and LARGER intervention area, so reducing intervention may cost recovery",
            ],
        },
        "r1_candidate_family": {
            "table": "reports/tables/post_phase13_regional_revision_r1_candidate_family.csv",
            "config_count": int(len(fam)),
            "maximum_allowed": 8,
            "configs": fam.to_dict(orient="records"),
            "allowed_changed_fields": ["proposal score acceptance floor",
                                       "maximum accepted proposals per image"],
            "frozen_fields": ["localizer checkpoint", "proposal coordinates", "proposal margin 0.20",
                              "NMS 0.30", "regional crop/restore", "segmentation checkpoints",
                              "fusion rule", "segmentation threshold 0.5"],
            "zero_acceptance_allowed": "YES",
            "localizer_retraining_in_r1": "NO",
            "score_weighting": "NONE",
            "new_fusion": "NONE",
            "control_present": "YES (R1-C0 = frozen Phase-13 policy, floor 0.10, max 5)",
        },
        "anti_overfitting_rule": {
            "family_constructed_from_part1d_b_dice_outcomes": "NO",
            "floors_derived_from": "MARGINAL_PROPOSAL_SCORE_DISTRIBUTION_WITHOUT_GT_LABELS",
            "max_accepted_candidates": [1, 5],
            "max_accepted_allowed_set": [1, 2, 3, 5],
            "baseline_appears_as_control": "YES",
            "family_frozen_before_any_candidate_specific_segmentation_inference": "YES",
            "gt_labels_may_describe_but_not_change_the_family": "YES",
        },
        "r1_evidence_dimensions": {
            "note": "letters are R1-local and MUST NOT be confused with the Part-1E-B gate dimensions A-D",
            "R1_A_GLOBAL_PRESERVATION": {
                "question": "Does selective abstention remove the catastrophic FP / precision cost?",
                "fields": ["mean Dice delta vs GLOBAL", "mean IoU delta", "mean precision delta",
                           "mean recall delta", "mean FP pixel delta", "mean FN pixel delta",
                           "cases improved/unchanged/worsened", "max improvement/worsening",
                           "new empty predictions"],
            },
            "R1_B_REGIONAL_UTILITY_RETENTION": {
                "question": "Does any selective policy retain genuine component / empty recovery benefit beyond GLOBAL?",
                "fields": ["component recoveries", "component losses", "empty recoveries",
                           "new empty predictions", "PREDICTED minus GLOBAL Dice", "object recall"],
            },
            "R1_C_INTERVENTION_SELECTIVITY": {
                "question": "Does the policy reduce off-target proposal intervention?",
                "fields": ["accepted proposal count", "accepted off-target count",
                           "accepted support area fraction", "cases with zero accepted proposals"],
            },
            "R1_D_CROSS_ARCHITECTURE_CONSISTENCY": {
                "question": "Does the behavior generalize across all four architectures?",
                "fields": ["per-architecture direction and magnitude", "heterogeneity report",
                           "no winner", "no rank"],
            },
            "new_numerical_go_threshold": "NONE",
            "weighted_score": "NONE",
            "automatic_winner": "NONE",
            "verdict_issuer": "SUPERVISOR",
        },
        "bounded_revision_budget": {
            "r1_scope": "ONE_BOUNDED_POLICY_ABLATION_ROUND",
            "candidate_family_expansion_after_results": "FORBIDDEN_WITHOUT_SUPERVISOR_APPROVAL",
            "if_h1_fails": "STOP__DO_NOT_AUTOMATICALLY_MOVE_TO_RETRAINING",
            "h2_requires_supervisor_decision": "YES",
            "open_ended_val_search": "FORBIDDEN",
        },
        "publication_validation_discipline": {
            "nature": "ADAPTIVE_DEVELOPMENT_REVISION_INFORMED_BY_PHASE13_VAL_FAILURE_EVIDENCE",
            "val_role": "DEVELOPMENT_DATA",
            "test_untouched_until": "PHASE_39",
            "revision_val_results_substitute_for_test": "NO",
            "external_test_tuning": "FORBIDDEN",
            "hidden_candidate_search": "FORBIDDEN",
        },
        "counters": {"training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
                     "localizer_forwards": 0, "segmentation_forwards": 0, "regional_crop_forwards": 0,
                     "proposal_regeneration": 0, "checkpoint_writes": 0, "test_reads": 0,
                     "external_test_reads": 0},
        "continuity": {
            "phase13": "COMPLETE_FROZEN",
            "original_gate": "REVISE_LOCALIZER_FROZEN",
            "regional_mechanism_promoted": "NO",
            "phase14": "NOT_STARTED",
            "post_phase13_revision_r0": "COMPLETE_PASS",
            "revision_r1": "ELIGIBLE_AFTER_SUPERVISOR_REVIEW__NOT_AUTHORIZED",
            "test": "UNTOUCHED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_REVISION_R1_AUTHORIZATION",
    }
    (AUDITS / "post_phase13_regional_revision_r0_protocol_frozen.json").write_text(
        json.dumps(proto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("wrote failure decomposition + frozen protocol (json)")
    print("family configs:", len(fam))
    print("conclusion:", dec["s18_conclusion"]["choice"])
    return dec, proto, r


if __name__ == "__main__":
    main()
