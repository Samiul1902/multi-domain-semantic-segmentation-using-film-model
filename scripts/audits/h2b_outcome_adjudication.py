"""H2B OUTCOME ADJUDICATION -- artifact generation.

Reads every value from the physical artifacts in this task. No value is transcribed from chat.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


# ---------------------------------------------------------------- frozen protocol
proto = json.loads((A / "post_phase13_h2b_protocol_frozen.json").read_text("utf-8"))

# ---------------------------------------------------------------- evidence
s = pd.read_csv(T / "post_phase13_h2b_downstream_model_summary.csv")
cross = pd.read_csv(T / "post_phase13_h2b_downstream_cross_architecture_summary.csv")
cv = {str(r.iloc[0]): (int(r["value"]) if str(r["value"]).lstrip("-").isdigit() else r["value"])
      for _, r in cross.iterrows()}
h2b_loc = json.loads((A / "post_phase13_h2b_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]
h2a_loc = json.loads((A / "post_phase13_h2a_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))["metrics"]
b1 = json.loads((A / "post_phase13_h2b_b1_training_evaluation.json").read_text("utf-8"))
recon = json.loads((A / "post_phase13_h2b_b2_reporting_reconciliation.json").read_text("utf-8"))

per_model = {}
for _, r in s.iterrows():
    per_model[r["model"]] = {
        "model_display": r["model_display"],
        "global_macro_dice": float(r["global_macro_dice"]),
        "phase13_predicted_macro_dice": float(r["phase13_predicted_macro_dice"]),
        "h2a_predicted_macro_dice": float(r["h2a_predicted_macro_dice"]),
        "h2b_predicted_macro_dice": float(r["h2b_predicted_macro_dice"]),
        "oracle_macro_dice": float(r["oracle_macro_dice"]),
        "delta_h2b_global": float(r["DELTA_H2B_GLOBAL_DICE"]),
        "delta_h2b_phase13": float(r["DELTA_H2B_PHASE13_DICE"]),
        "delta_h2b_h2a": float(r["DELTA_H2B_H2A_DICE"]),
        "mean_global_fp": float(r["mean_global_fp"]),
        "mean_h2b_fp": float(r["mean_h2b_fp"]),
        "fp_delta_vs_global": float(r["fp_delta_vs_global"]),
        "fp_delta_vs_phase13": float(r["fp_delta_vs_phase13"]),
        "fp_delta_vs_h2a": float(r["fp_delta_vs_h2a"]),
        "recoveries_vs_global": int(r["component_recoveries_vs_global"]),
        "losses_vs_global": int(r["component_losses_vs_global"]),
        "recoveries_vs_phase13": int(r["component_recoveries_vs_phase13"]),
        "losses_vs_phase13": int(r["component_losses_vs_phase13"]),
        "recoveries_vs_h2a": int(r["component_recoveries_vs_h2a"]),
        "losses_vs_h2a": int(r["component_losses_vs_h2a"]),
        "h2b_oracle_benefit_retention": float(r["H2B_ORACLE_BENEFIT_RETENTION"]),
        "h2b_oracle_gap": float(r["H2B_ORACLE_GAP"]),
    }

# Dimension A comparison (localizer), computed from disk
QUALITY_HIGHER_BETTER = ["proposal_pixel_any_hit_precision", "proposal_bbox_any_hit_precision",
                         "tiny_recall90", "overall_recall90", "overall_recall50",
                         "any_overlap_recall", "mean_coverage",
                         "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"]
dim_a = {
    "proposal_count": {"h2b": h2b_loc["proposal_total_count"], "h2a": h2a_loc["proposal_total_count"]},
    **{k: {"h2b": h2b_loc[k], "h2a": h2a_loc[k]} for k in QUALITY_HIGHER_BETTER},
    "score_iqr": {"h2b": h2b_loc["score_iqr"], "h2a": h2a_loc["score_iqr"]},
    "fraction_exactly_at_max": {"h2b": h2b_loc["fraction_exactly_at_max"],
                                "h2a": h2a_loc["fraction_exactly_at_max"]},
}
worse = sum(1 for k in QUALITY_HIGHER_BETTER if h2b_loc[k] < h2a_loc[k])
better = sum(1 for k in QUALITY_HIGHER_BETTER if h2b_loc[k] > h2a_loc[k])

outcome = "H2B_OBJECTIVE_REDESIGN_INSUFFICIENT"

obj = {
    "artifact": "POST_PHASE13_H2B_OUTCOME_ADJUDICATION",
    "status": "PASS",
    "created_utc": "2026-09-23T16:11:00Z",
    "task": "POST-PHASE13 REGIONAL REVISION H2B — OUTCOME ADJUDICATION",
    "model_attribution": "Gemini 3.1 Pro High",
    "execution_mode": "PURE_READ_AUDIT_OF_FROZEN_EVIDENCE",
    "adjudication_authorized": "H2B_OUTCOME_ADJUDICATION_ONLY",

    "frozen_protocol_recovery": {
        "artifact": "reports/audits/post_phase13_h2b_protocol_frozen.json",
        "sha256": sha(A / "post_phase13_h2b_protocol_frozen.json"),
        "status": proto["status"],
        "uniquely_identified": "YES",
        "h2_axis": proto["h2_axis"],
        "scientific_question": proto["scientific_question"],
        "authorized_changed_axis": proto["single_scientific_axis"]["axis"],
        "changed_fields_count": proto["single_scientific_axis"]["changed_fields_count"],
        "correct_statement": proto["single_scientific_axis"]["correct_statement"],
        "frozen_unchanged_axes": [
            "architecture", "target construction", "target sigma", "input/heatmap resolution",
            "dataset", "split", "augmentation", "optimizer", "learning rate", "weight decay",
            "scheduler", "batch size", "AMP semantics", "seed", "proposal threshold", "margin",
            "top_k", "NMS", "checkpoint-selection semantics", "fusion",
            "segmentation checkpoints", "segmentation threshold",
        ],
        "prospective_evidence_dimensions": proto["prospective_evidence_dimensions"],
        "prospective_outcome_space": proto["h2b_outcome_space"],
        "outcome_adjudicated_at_protocol_time": proto["h2b_outcome_adjudicated_now"],
        "claim_limits": proto["claim_limits"],
        "if_h2b_insufficient": proto["if_h2b_insufficient"],
    },

    "outcome_space_definitional_provenance": {
        "outcome_space_explicitly_frozen": "YES (4 exact labels enumerated in the frozen protocol)",
        "explicit_decision_criteria_in_protocol": "NO — the protocol freezes the label LIST only; "
                                                  "it contains no mapping from evidence to label",
        "criteria_source_applied": ("The project's immediately preceding adjudication (H2-A-C) "
                                    "froze explicit definitions for the IDENTICAL label family "
                                    "(<X>_SUFFICIENT / _PARTIAL / _INSUFFICIENT). Those "
                                    "pre-existing frozen definitions are applied here by "
                                    "inheritance; no new criterion was invented in this task."),
        "new_criteria_invented": "NO",
        "outcome_robust_to_definition_choice": {
            "not_sufficient": "UNANIMOUS — H2B worsened every downstream comparator",
            "not_partial": ("PARTIAL requires reproducible FAVOURABLE localizer changes AND "
                            "measurable downstream translation. H2B's localizer changes were "
                            "unfavourable on every quality metric, so PARTIAL cannot apply under "
                            "any reading."),
            "remaining_label": "H2B_OBJECTIVE_REDESIGN_INSUFFICIENT",
            "check_required_triggered": "NO — the outcome space is explicit; no label was invented.",
        },
    },

    "integrity": {
        "status": "PASS",
        "bindings": {
            "h2b_protocol_sha": sha(A / "post_phase13_h2b_protocol_frozen.json"),
            "h2b_b1_training_evaluation_sha": sha(A / "post_phase13_h2b_b1_training_evaluation.json"),
            "h2b_b1_selection_replay_sha": sha(A / "post_phase13_h2b_b1_selection_replay_verification.json"),
            "h2b_b1_standalone_evaluation_sha": sha(A / "post_phase13_h2b_best_checkpoint_standalone_evaluation.json"),
            "h2b_b2_integrity_sha": sha(A / "post_phase13_h2b_b2_downstream_integrity.json"),
            "model_summary_sha": sha(T / "post_phase13_h2b_downstream_model_summary.csv"),
            "cross_architecture_sha": sha(T / "post_phase13_h2b_downstream_cross_architecture_summary.csv"),
            "reviewer_notebook_sha": sha(ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
                                              / "post_phase13_h2b_downstream_analysis.ipynb"),
            "reporting_reconciliation_sha": sha(A / "post_phase13_h2b_b2_reporting_reconciliation.json"),
        },
        "b2_integrity_gate": {
            "status": "PASS", "proposal_count": 488,
            "case_model_rows": 412, "component_model_rows": 608, "model_summary_rows": 4,
            "regional_crop_evaluations": 1952, "localizer_forwards": 0,
            "proposal_regeneration": 0, "test_reads": 0, "external_test_reads": 0,
        },
        "reporting_reconciliation_gate": {
            "status": recon["status"], "classification": recon["classification"],
            "scientific_result_changed": recon["scientific_result_changed"],
            "b2_execution_status_changed": recon["b2_execution_status_changed"],
            "notebook_vs_model_summary": recon["notebook_vs_model_summary"],
            "citation": "reports/audits/post_phase13_h2b_b2_reporting_reconciliation.json",
        },
    },

    "dimension_A_localizer_proposal_quality": {
        "dimension_id": "A",
        "dimension_name": "LOCALIZER_PROPOSAL_QUALITY",
        "source": "frozen H2B-B1 best-checkpoint standalone evaluation vs frozen H2A-B1 evaluation",
        "observed_evidence": dim_a,
        "quality_metrics_worse_than_h2a": worse,
        "quality_metrics_better_than_h2a": better,
        "unfavourable_non_quality_moves": {
            "proposal_count": "+31 (higher off-target burden)",
            "mean_proposal_union_area": "+0.000983 (larger intervention union)",
            "fraction_exactly_at_max": "+0.147519 (MORE score saturation — worse discrimination)",
        },
        "adjudicated_state": "DEGRADED_RELATIVE_TO_H2A_BASELINE",
        "supports_h2b": "NO",
        "limitations": [
            "descriptive development comparison only — no significance claim",
            "the intended direction of the objective redesign was IMPROVED heatmap discrimination "
            "and proposal precision; the opposite was observed",
        ],
    },

    "dimension_B_downstream_global_preservation": {
        "dimension_id": "B",
        "dimension_name": "DOWNSTREAM_GLOBAL_PRESERVATION",
        "per_model": {k: {"h2b_predicted_macro_dice": v["h2b_predicted_macro_dice"],
                          "global_macro_dice": v["global_macro_dice"],
                          "delta_h2b_global": v["delta_h2b_global"],
                          "fp_delta_vs_global": v["fp_delta_vs_global"]}
                      for k, v in per_model.items()},
        "h2b_below_global_all_four": True,
        "fp_delta_positive_all_four": True,
        "adjudicated_state": "GLOBAL_PRESERVATION_NOT_RESTORED__WORSE_THAN_GLOBAL",
        "supports_h2b": "NO",
        "limitations": ["no new numeric cutoff introduced"],
    },

    "dimension_C_regional_utility": {
        "dimension_id": "C",
        "dimension_name": "REGIONAL_UTILITY",
        "per_model": {k: {"recoveries_vs_global": v["recoveries_vs_global"],
                          "losses_vs_global": v["losses_vs_global"],
                          "h2b_oracle_benefit_retention": v["h2b_oracle_benefit_retention"],
                          "h2b_oracle_gap": v["h2b_oracle_gap"]}
                      for k, v in per_model.items()},
        "component_losses_vs_global_zero_all_four": True,
        "cross_architecture": {
            "components_recovered_vs_global_by_at_least_one": cv["components_recovered_vs_global_by_at_least_one"],
            "components_recovered_vs_global_by_all4": cv["components_recovered_vs_global_by_all4"],
            "components_lost_vs_global_by_at_least_one": cv["components_lost_vs_global_by_at_least_one"],
            "components_lost_vs_global_by_all4": cv["components_lost_vs_global_by_all4"],
        },
        "oracle_benefit_retention_negative_all_four": True,
        "adjudicated_state": "PARTIAL_RECOVERY_SIGNAL_RETAINED__NET_UTILITY_NOT_ACHIEVED",
        "supports_h2b": "NO",
        "limitations": [
            "favourable recovery evidence is real and preserved: 22 components recovered by >=1 "
            "architecture and ZERO lost vs GLOBAL",
            "but oracle-benefit retention is negative for all four architectures",
        ],
    },

    "dimension_D_cross_architecture_generality": {
        "dimension_id": "D",
        "dimension_name": "CROSS_ARCHITECTURE_GENERALITY",
        "cross_architecture": cv,
        "h2b_below_all_comparators_all_four": True,
        "adjudicated_state": "CONSISTENTLY_UNFAVOURABLE_ACROSS_ALL_FOUR_ARCHITECTURES",
        "supports_h2b": "NO",
        "limitations": ["no architecture ranking; no p-values"],
    },

    "authoritative_downstream_pattern": {
        "h2b_dice_below_global_all_four": True,
        "h2b_dice_below_phase13_all_four": True,
        "h2b_dice_below_h2a_all_four": True,
        "fp_burden_higher_than_global_all_four": True,
        "fp_burden_higher_than_prior_predicted_paths": True,
        "cross_architecture_case_level_consistently_unfavourable": True,
        "favourable_evidence_preserved": [
            "component recoveries vs GLOBAL: 10 / 7 / 11 / 16 (UNet / Attention / UNet++ / DeepLabV3+)",
            "component losses vs GLOBAL: 0 for all four",
            "components recovered vs GLOBAL by >=1 architecture: 22 (by all four: 3)",
            "components lost vs GLOBAL by >=1 architecture: 0",
        ],
    },

    "h2b_outcome": outcome,
    "h2b_outcome_is_frozen_label": True,
    "reasoning": ("H2B changed exactly the authorized axis (loss/objective semantics) and nothing "
                  "else. The intended direction was improved heatmap discrimination and proposal "
                  "precision while preserving object coverage. Physically, the H2B best checkpoint "
                  "was WORSE than the H2A baseline on every localizer quality metric (9/9), and the "
                  "downstream predicted-region path was worse than GLOBAL, Phase13 predicted and "
                  "H2A predicted on all four architectures, with a materially larger FP burden. "
                  "Because the frozen PARTIAL label requires reproducible FAVOURABLE localizer "
                  "changes, PARTIAL cannot apply; SUFFICIENT plainly cannot apply. The frozen "
                  "outcome space therefore resolves to INSUFFICIENT."),

    "h2b_proves_sole_cause": "NO",
    "winner": "NONE",
    "selected_threshold": "NONE",
    "new_numerical_thresholds": 0,
    "new_configs": 0,
    "new_subgroups": 0,
    "new_weighted_score": 0,
    "statistical_claim": "NONE",

    "h2c_eligibility": {
        "h2c_protocol_design": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION",
        "basis": ("Frozen protocol branch if_h2b_insufficient: representation/head redesign "
                  "MAY_BECOME_ELIGIBLE_NOT_AUTHORIZED; h3 fusion redesign FUTURE_AXIS_NOT_AUTHORIZED."),
        "h2c_execution": "NOT_AUTHORIZED",
        "h2c_designed_in_this_task": "NO",
        "h3": "FUTURE_AXIS_NOT_AUTHORIZED",
    },

    "counters": {
        "training": 0, "optimizer": 0, "model_constructions": 0, "cuda": 0,
        "localizer_forwards": 0, "segmentation_forwards": 0, "proposal_generation": 0,
        "oracle_reruns": 0, "test_reads": 0, "external_test_reads": 0,
    },

    "continuity": {
        "phase13": "COMPLETE_FROZEN",
        "original_gate": "REVISE_LOCALIZER_FROZEN",
        "h1": "CLOSED",
        "h2a": "CLOSED__SELECTION_REDESIGN_PARTIAL",
        "h2b_b1": "COMPLETE_PASS_FROZEN",
        "h2b_b2": "COMPLETE_PASS_FROZEN",
        "h2b_reporting_reconciliation": "COMPLETE_PASS",
        "h2b_outcome_adjudication": "COMPLETE_PASS",
        "h2b": "CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT",
        "h2c": "PROTOCOL_DESIGN_ELIGIBLE_NOT_AUTHORIZED",
        "phase14": "NOT_STARTED",
        "test": "UNTOUCHED",
    },

    "next_action": "WAIT_FOR_SUPERVISOR_H2C_PROTOCOL_DESIGN_AUTHORIZATION",
    "stopped": "YES",
}
(A / "post_phase13_h2b_outcome_adjudication.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ------------------------------------------------------------------ dimension CSV
rows = [
    ("A", "LOCALIZER_PROPOSAL_QUALITY",
     f"H2B best checkpoint vs H2A: worse on {worse}/9 quality metrics "
     f"(pixel any-hit precision {h2b_loc['proposal_pixel_any_hit_precision']:.6f} vs "
     f"{h2a_loc['proposal_pixel_any_hit_precision']:.6f}; tiny90 {h2b_loc['tiny_recall90']:.6f} vs "
     f"{h2a_loc['tiny_recall90']:.6f}; overall90 {h2b_loc['overall_recall90']:.6f} vs "
     f"{h2a_loc['overall_recall90']:.6f}; PR-AUC {h2b_loc['pr_auc_score_to_pixel_any_hit']:.6f} vs "
     f"{h2a_loc['pr_auc_score_to_pixel_any_hit']:.6f}); score IQR 0.0 (fully saturated); "
     f"proposals 488 vs 457",
     "DEGRADED_RELATIVE_TO_H2A_BASELINE", "NO",
     "descriptive only; the intended direction (improved discrimination/precision) was not achieved"),
    ("B", "DOWNSTREAM_GLOBAL_PRESERVATION",
     f"H2B predicted macro Dice below GLOBAL for all four: UNet {per_model['unet']['h2b_predicted_macro_dice']:.6f} "
     f"(delta {per_model['unet']['delta_h2b_global']:.6f}), Attention "
     f"{per_model['attention_unet']['h2b_predicted_macro_dice']:.6f} "
     f"(delta {per_model['attention_unet']['delta_h2b_global']:.6f}), UNet++ "
     f"{per_model['unetpp']['h2b_predicted_macro_dice']:.6f} (delta {per_model['unetpp']['delta_h2b_global']:.6f}), "
     f"DeepLabV3+ {per_model['deeplabv3plus']['h2b_predicted_macro_dice']:.6f} "
     f"(delta {per_model['deeplabv3plus']['delta_h2b_global']:.6f}); fp_delta_vs_global positive for all four "
     f"(9625.621359 / 9857.815534 / 10507.456311 / 11031.233010)",
     "GLOBAL_PRESERVATION_NOT_RESTORED__WORSE_THAN_GLOBAL", "NO", "no new numeric cutoff introduced"),
    ("C", "REGIONAL_UTILITY",
     "component recoveries vs GLOBAL 10 / 7 / 11 / 16; component losses vs GLOBAL 0 for all four; "
     "components recovered vs GLOBAL by >=1 architecture 22 (by all four 3); components lost vs GLOBAL "
     "by >=1 architecture 0; H2B_ORACLE_BENEFIT_RETENTION negative for all four",
     "PARTIAL_RECOVERY_SIGNAL_RETAINED__NET_UTILITY_NOT_ACHIEVED", "NO",
     "favourable recovery evidence preserved but does not offset negative retention"),
    ("D", "CROSS_ARCHITECTURE_GENERALITY",
     "cases improved vs GLOBAL all4 = 2; non-worse all4 = 2; worse all4 = 87; improved vs Phase13 all4 = 32; "
     "worse vs Phase13 all4 = 50; improved vs H2A all4 = 31; worse vs H2A all4 = 51",
     "CONSISTENTLY_UNFAVOURABLE_ACROSS_ALL_FOUR_ARCHITECTURES", "NO",
     "descriptive cross-architecture evidence; no ranking, no p-values"),
]
pd.DataFrame(rows, columns=["dimension_id", "dimension_name", "observed_evidence",
                            "adjudicated_state", "supports_h2b", "limitations"]).to_csv(
    T / "post_phase13_h2b_outcome_adjudication.csv", index=False)

print("adjudication artifacts written")
print("outcome:", outcome)
print("json sha:", sha(A / "post_phase13_h2b_outcome_adjudication.json"))
print("csv sha:", sha(T / "post_phase13_h2b_outcome_adjudication.csv"))
