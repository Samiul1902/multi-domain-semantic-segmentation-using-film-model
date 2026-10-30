"""POST-PHASE-13 R1-H1 — selective-acceptance hypothesis adjudication.

Reads ONLY frozen R1 artifacts. NO model execution, NO new policy search, NO new threshold.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
ADJ_UTC = "2026-09-22T07:15:00Z"
OUTCOME = "H1_PARTIAL_MITIGATION_INSUFFICIENT_AS_STANDALONE_REVISION"
MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
           "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}
CONFIGS = ["R1-C0", "R1-C1", "R1-C2", "R1-C3", "R1-C4", "R1-C5", "R1-C6"]

BIND = {
    "r1_evaluation": "reports/audits/post_phase13_regional_revision_r1_evaluation.json",
    "r1_control_verification": "reports/audits/post_phase13_r1_control_and_duplicate_verification.json",
    "r0_interpretation_clarification": "reports/audits/post_phase13_r0_interpretation_clarification.json",
    "r1_policy": "reports/audits/post_phase13_regional_revision_r1_policy_frozen.json",
    "summary_28": "reports/tables/post_phase13_r1_model_policy_summary.csv",
    "intervention_7": "reports/tables/post_phase13_r1_policy_intervention_summary.csv",
    "cross_arch_7": "reports/tables/post_phase13_r1_cross_architecture_policy_summary.csv",
    "case_model_policy_2884": "reports/tables/post_phase13_r1_case_model_policy_metrics.csv",
}


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    s = pd.read_csv(TABLES / "post_phase13_r1_model_policy_summary.csv")
    inter = pd.read_csv(TABLES / "post_phase13_r1_policy_intervention_summary.csv")
    cross = pd.read_csv(TABLES / "post_phase13_r1_cross_architecture_policy_summary.csv")
    ev = json.loads((AUDITS / "post_phase13_regional_revision_r1_evaluation.json").read_text("utf-8"))
    ctrl = json.loads((AUDITS / "post_phase13_r1_control_and_duplicate_verification.json").read_text("utf-8"))
    clar = json.loads((AUDITS / "post_phase13_r0_interpretation_clarification.json").read_text("utf-8"))

    # ---------- integrity precondition ----------
    integ = {
        "r1_evaluation_status_pass": ev["status"] == "PASS",
        "r1_integrity_failures_empty": ev["integrity_failures"] == [],
        "c0_reproduction_pass": ctrl["control_reproduction"]["result"] == "PASS",
        "c1_membership_eq_c3": ctrl["c1_c3_duplicate"]["membership_equal_result"] == "YES",
        "c1_output_eq_c3": ctrl["c1_c3_duplicate"]["output_equal"] == "YES",
        "summary_rows_28": len(s) == 28,
        "intervention_rows_7": len(inter) == 7,
        "cross_arch_rows_7": len(cross) == 7,
        "r0_clarification_canonical_scope_intact": clar["classification"]
        == "CAUSAL_LANGUAGE_SCOPE_CLARIFICATION_ONLY",
    }
    integrity_ok = all(integ.values())

    below = s["policy_macro_dice"] < s["global_macro_dice"]
    retention_neg = s["RETENTION_DICE"] < 0
    c0 = s[s.config_id == "R1-C0"]
    c5 = s[s.config_id == "R1-C5"]

    # ---------- Dimension A ----------
    A_rows = []
    for m in MODELS:
        r = c5[c5.model == m].iloc[0]
        A_rows.append({"model": m, "model_display": DISPLAY[m],
                       "global_macro_dice": float(r.global_macro_dice),
                       "c5_policy_macro_dice": float(r.policy_macro_dice),
                       "c5_delta_vs_global": float(r.DELTA_POLICY_GLOBAL_DICE),
                       "c5_mean_fp_delta": float(r.mean_fp_delta_vs_global),
                       "c5_mean_fn_delta": float(r.mean_fn_delta_vs_global),
                       "c5_cases_worse": int(r.cases_worse)})
    A = {
        "name": "GLOBAL_PRESERVATION",
        "question": "Does selective abstention remove the catastrophic FP / precision cost and restore acceptable global preservation?",
        "finding": (
            "NO. Every one of the 28 config/model combinations has policy macro Dice BELOW GLOBAL "
            f"({int(below.sum())}/28). The most aggressive policy (R1-C5) still trails GLOBAL by "
            "-0.131136 (UNet), -0.143855 (Attention U-Net), -0.157948 (UNet++) and -0.133755 (DeepLabV3+). "
            "Selectivity sharply reduces the FP burden (mean FP delta falls from +7778 to about +2049, a "
            "74% reduction) and roughly halves the Dice deficit, but the burden remains POSITIVE for every "
            "policy and the deficit is never closed. Case worsening is essentially unchanged: 93.0-94.5 of "
            "103 cases worsen under every policy."),
        "adjudicated_state": "NOT_RESTORED__MATERIALLY_IMPROVED_BUT_STILL_DEFICIENT",
        "supports_h1": False,
        "per_model_c5": A_rows,
    }

    # ---------- Dimension B ----------
    rec = {cfg: s[s.config_id == cfg]["component_recoveries_vs_global"].tolist() for cfg in CONFIGS}
    B = {
        "name": "REGIONAL_UTILITY_RETENTION",
        "question": "Does any selective policy retain genuine component / empty recovery benefit beyond GLOBAL?",
        "finding": (
            "PARTIALLY, AND NOT SUFFICIENTLY. Component losses are 0 for every policy and every "
            "architecture, and empty recoveries are largely retained (C0 8/3/5/11 vs C5 8/3/5/10). But "
            "component recoveries collapse under aggressive selectivity: 16/9/14/16 at C0 (55 total) down "
            "to 2/1/3/4 at C1 and C5 (10 total) - an 82% loss of the recovery signal. RETENTION_DICE is "
            "negative for ALL 28 config/model combinations, so no policy converts the oracle mechanism "
            "into positive deployable benefit."),
        "adjudicated_state": "PARTIAL__RECOVERY_SIGNAL_LOST_UNDER_AGGRESSIVE_SELECTIVITY",
        "supports_h1": False,
        "component_recoveries_by_config": rec,
        "component_losses_by_config": {cfg: int(s[s.config_id == cfg]["component_losses_vs_global"].sum()) for cfg in CONFIGS},
        "empty_recoveries_c0": c0["empty_recoveries"].tolist(),
        "empty_recoveries_c5": c5["empty_recoveries"].tolist(),
        "retention_negative_count": f"{int(retention_neg.sum())}/28",
        "retention_note": "never clipped; negative values preserved as measured",
    }

    # ---------- Dimension C ----------
    i0 = inter[inter.config_id == "R1-C0"].iloc[0]
    i5 = inter[inter.config_id == "R1-C5"].iloc[0]
    C = {
        "name": "INTERVENTION_SELECTIVITY",
        "question": "Does the policy reduce off-target proposal intervention?",
        "finding": (
            "YES - this is the dimension H1 clearly improves. Accepted proposals fall 494 -> 102 "
            "(C0 -> C5), GT-miss accepted proposals fall 372 -> 68, mean accepted proposals per image fall "
            "4.796 -> 0.990, and mean intervention union area falls 0.004846 -> 0.001486. Mean policy "
            "precision rises from 0.2342 to 0.4259 while mean recall is essentially unchanged "
            "(0.6664 -> 0.6502). Selectivity therefore does improve intervention precision. However the "
            "accepted GT-miss FRACTION remains 0.666667 (68/102) versus 0.753036 (372/494) at C0 - a real "
            "improvement, but two thirds of the surviving interventions are still off-target."),
        "adjudicated_state": "IMPROVED__BUT_OFF_TARGET_FRACTION_REMAINS_HIGH",
        "supports_h1": True,
        "c0": {"accepted": int(i0.accepted_proposals), "gt_miss_accepted": int(i0.gt_miss_accepted_proposals),
               "accepted_gt_miss_fraction": float(i0.accepted_gt_miss_fraction),
               "mean_accepted_per_image": float(i0.mean_accepted_proposals)},
        "c5": {"accepted": int(i5.accepted_proposals), "gt_miss_accepted": int(i5.gt_miss_accepted_proposals),
               "accepted_gt_miss_fraction": float(i5.accepted_gt_miss_fraction),
               "mean_accepted_per_image": float(i5.mean_accepted_proposals)},
        "membership_label_blind": "YES - GT fields are post-freeze descriptive evaluation only",
    }

    # ---------- Dimension D ----------
    c5x = cross[cross.config_id == "R1-C5"].iloc[0]
    D = {
        "name": "CROSS_ARCHITECTURE_CONSISTENCY",
        "question": "Does the behaviour generalize across all four architectures?",
        "finding": (
            "GENERAL, NOT ARCHITECTURE-SPECIFIC. The negative Dice-vs-GLOBAL behaviour holds in all four "
            "architectures for every policy (28/28 below GLOBAL). At R1-C5, cases worse in all four = 84 "
            "of 103, components recovered by >=1 architecture = 6, recovered by all four = 1, and "
            "components lost by >=1 architecture = 0. The mitigation is also consistent: every "
            "architecture improves under aggressive selectivity and loses recovery at the same time. No "
            "architecture is a winner, no ranking is made."),
        "adjudicated_state": "CONSISTENT_ACROSS_ARCHITECTURES__NEGATIVE_RESULT_IS_GENERAL",
        "supports_h1": False,
        "c5_cross_architecture": {k: int(c5x[k]) for k in (
            "cases_improved_all_four", "cases_nonworse_all_four", "cases_worse_all_four",
            "components_recovered_by_at_least_one", "components_recovered_by_all_four",
            "components_lost_by_at_least_one", "components_lost_by_all_four")},
    }

    # ---------- §8 trade-off pattern ----------
    def blk(cfg):
        sub = s[s.config_id == cfg]
        return {"mean_accepted_per_image": float(sub["mean_accepted_proposals_per_image"].mean()),
                "mean_macro_dice": float(sub["policy_macro_dice"].mean()),
                "mean_delta_vs_global": float(sub["DELTA_POLICY_GLOBAL_DICE"].mean()),
                "mean_retention": float(sub["RETENTION_DICE"].mean()),
                "mean_fp_delta": float(sub["mean_fp_delta_vs_global"].mean()),
                "total_component_recoveries": int(sub["component_recoveries_vs_global"].sum()),
                "total_component_losses": int(sub["component_losses_vs_global"].sum())}
    trade = {
        "pattern_tested": (
            "MILD selectivity preserves recovery but barely relieves the global Dice / FP failure; "
            "AGGRESSIVE selectivity substantially relieves FP but removes most component-recovery benefit "
            "and still remains below GLOBAL."),
        "pattern_supported": "YES__EXACTLY_REPRODUCED_IN_THE_FROZEN_TABLES",
        "mild": {cfg: blk(cfg) for cfg in ("R1-C2", "R1-C4", "R1-C6")},
        "aggressive": {cfg: blk(cfg) for cfg in ("R1-C1", "R1-C5")},
        "mild_evidence": (
            "C2 reproduces the C0 recovery profile exactly (16/9/14/16) while relieving only 2% of the FP "
            "burden (+7778 -> +7598); C4 keeps 52 of 55 recoveries and relieves 8%; C6 keeps 41 of 55 and "
            "relieves 12%. Mean macro Dice moves only 0.2999 -> 0.3054 / 0.3219 / 0.3314."),
        "aggressive_evidence": (
            "C1 and C5 relieve 73-74% of the FP burden (+7778 -> +2075 / +2049) and lift mean macro Dice to "
            "0.4608 / 0.4645, but total component recoveries fall 55 -> 10 (an 82% loss) and all four "
            "architectures remain below GLOBAL."),
        "eighth_policy_searched": "NO",
        "interpolated_threshold_created": "NO",
        "best_policy_declared": "NO",
    }

    # ---------- outcome ----------
    reasoning = (
        "Dimension C is clearly positive: selective acceptance does improve intervention precision "
        "(accepted 494 -> 102; GT-miss accepted 372 -> 68; mean precision 0.2342 -> 0.4259; FP burden "
        "reduced 74%). Dimensions A and B are materially improved but NOT resolved: every one of the 28 "
        "config/model combinations still has policy macro Dice below GLOBAL, the most aggressive policy "
        "still trails GLOBAL by 0.131-0.158, the FP burden remains positive for every policy, and "
        "RETENTION_DICE is negative in all 28 combinations. The trade-off is strict: mild selectivity "
        "preserves the recovery profile (C2 identical to C0) but relieves almost none of the FP burden, "
        "while aggressive selectivity relieves 74% of the FP burden but destroys 82% of the component "
        "recoveries. No frozen policy jointly restores global preservation AND retains enough regional "
        "utility. Selective acceptance alone is therefore a real but PARTIAL mitigation, insufficient as "
        "a standalone revision. This does NOT establish a representation failure: H1 isolated the "
        "acceptance-only axis, and its insufficiency leaves localizer representation, heatmap confidence "
        "calibration, proposal ranking, training objective, checkpoint-selection semantics and "
        "precision/recall balance as open contributors for H2 protocol design.")

    obj = {
        "artifact": "POST_PHASE13_REGIONAL_REVISION_R1_H1_ADJUDICATION",
        "status": "PASS" if integrity_ok else "CHECK_REQUIRED",
        "created_utc": ADJ_UTC,
        "hypothesis": "H1_FIRST_SELECTIVE_ACCEPTANCE",
        "h1_question": (
            "Is selective proposal acceptance / abstention, with all other scientific axes frozen, "
            "sufficient to make the current GT-free regional path a credible standalone revision?"),
        "h1_question_clarification": "H1 does NOT ask whether selectivity helps at all; it asks whether selectivity ALONE adequately resolves the Phase 13 deployable failure while retaining meaningful regional utility.",
        "integrity": {"result": "PASS" if integrity_ok else "FAIL", "checks": integ},
        "bindings": {k: {"path": v, "sha": sha(ROOT / v)} for k, v in BIND.items()},
        "dimensions": {"A": A, "B": B, "C": C, "D": D},
        "trade_off_adjudication": trade,
        "h1_outcome": OUTCOME,
        "reasoning": reasoning,
        "h1_proves_representation_failure": "NO",
        "h2_eligibility": {
            "h2_localizer_retraining_or_selection_redesign": "ELIGIBLE_FOR_PROTOCOL_DESIGN",
            "authorized_for_training": "NO",
            "reason": "H1 has isolated the acceptance-only axis and shown it is not sufficient by itself; this does NOT prove representation failure.",
            "open_h2_issues_unchanged_in_this_task": [
                "localizer representation", "heatmap confidence calibration", "proposal ranking",
                "training objective", "checkpoint-selection semantics",
                "proposal precision / recall balance"],
        },
        "bounded_search_closure": {
            "r1_candidate_family": "CLOSED",
            "post_hoc_r1_expansion": "FORBIDDEN",
            "forbidden": ["R1-C7", "new floor", "new max-proposal count",
                          "interpolated threshold", "outcome-driven candidate"],
            "without_new_supervisor_approved_protocol": "NO_FURTHER_R1_CANDIDATES",
        },
        "claim_limits": {
            "new_numerical_thresholds": 0, "new_configs": 0, "new_subgroup": 0,
            "winner": "NONE", "selected_threshold": "NONE", "weighted_score": "NONE",
            "optimization_after_seeing_results": "NONE",
            "go_no_go_gate_created": "NO",
        },
        "counters": {
            "training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
            "global_forwards": 0, "regional_forwards": 0, "localizer_forwards": 0,
            "proposal_generation": 0, "oracle_reruns": 0, "test_reads": 0, "external_test_reads": 0,
        },
        "continuity": {
            "phase13": "COMPLETE_FROZEN",
            "original_regional_gate": "REVISE_LOCALIZER_FROZEN",
            "revision_r0": "COMPLETE_PASS_FROZEN",
            "revision_r1_policy": "COMPLETE_PASS_FROZEN",
            "revision_r1_execution": "COMPLETE_PASS_FROZEN",
            "h1_adjudication": "COMPLETE_PASS",
            "h1": "CLOSED__PARTIAL_MITIGATION_INSUFFICIENT",
            "h2_protocol_design": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED",
            "h2_training": "NOT_AUTHORIZED",
            "phase14": "NOT_STARTED",
            "test": "UNTOUCHED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_H2_PROTOCOL_DESIGN_AUTHORIZATION",
    }
    (AUDITS / "post_phase13_regional_revision_r1_h1_adjudication.json").write_text(
        json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------- §13 evidence table ----------
    hdr = ["dimension_id", "dimension_name", "observed_evidence", "adjudicated_state",
           "supports_h1", "limitations"]
    rows = [
        ["A", "GLOBAL_PRESERVATION", A["finding"], A["adjudicated_state"], "NO",
         "No post-hoc cutoff applied; all 28 config/model combinations remain below GLOBAL; case worsening unchanged at 93.0-94.5 of 103."],
        ["B", "REGIONAL_UTILITY_RETENTION", B["finding"], B["adjudicated_state"], "NO",
         "RETENTION_DICE negative in 28/28; recovery collapse is measured, not inferred; component losses 0 are preserved as genuine favourable evidence."],
        ["C", "INTERVENTION_SELECTIVITY", C["finding"], C["adjudicated_state"], "YES",
         "GT fields are post-freeze descriptive only; membership was label-blind; accepted GT-miss fraction 0.666667 remains high."],
        ["D", "CROSS_ARCHITECTURE_CONSISTENCY", D["finding"], D["adjudicated_state"], "NO",
         "No winner and no ranking; the negative result is general, so no architecture-specific rescue is available."],
    ]
    with (TABLES / "post_phase13_regional_revision_r1_h1_adjudication.csv").open(
            "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(hdr); w.writerows(rows)

    print("integrity:", "PASS" if integrity_ok else "FAIL")
    print("H1 OUTCOME:", OUTCOME)
    print("supports_h1 per dimension:",
          {k: obj["dimensions"][k]["supports_h1"] for k in "ABCD"})
    print("below-global count:", f"{int(below.sum())}/28", "| retention negative:", f"{int(retention_neg.sum())}/28")


if __name__ == "__main__":
    main()
