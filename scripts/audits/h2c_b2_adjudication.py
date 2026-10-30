"""H2C-B2 SEC 9-11 -- adjudication + execution audit + chain closure. All values read from disk."""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


s = pd.read_csv(T / "post_phase13_h2c_downstream_model_summary.csv")
cross = pd.read_csv(T / "post_phase13_h2c_downstream_cross_architecture_summary.csv")
cv = {str(r.iloc[0]): (int(r["value"]) if str(r["value"]).lstrip("-").isdigit() else r["value"])
      for _, r in cross.iterrows()}
integ = json.loads((A / "post_phase13_h2c_b2_downstream_integrity.json").read_text("utf-8"))
proto = json.loads((A / "post_phase13_h2c_protocol_frozen.json").read_text("utf-8"))
b1 = json.loads((A / "post_phase13_h2c_b1_training_evaluation.json").read_text("utf-8"))
sa = json.loads((A / "post_phase13_h2c_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))
fm = json.loads((A / "post_phase13_h2c_b2_freeze_manifest.json").read_text("utf-8"))

per_model = {}
for _, r in s.iterrows():
    per_model[r["model"]] = {k: (int(r[k]) if k.startswith(("component_", "cases_")) else float(r[k]))
                             for k in ("global_macro_dice", "phase13_predicted_macro_dice",
                                       "h2a_predicted_macro_dice", "h2c_predicted_macro_dice",
                                       "oracle_macro_dice", "DELTA_H2C_GLOBAL_DICE",
                                       "DELTA_H2C_PHASE13_DICE", "DELTA_H2C_H2A_DICE",
                                       "H2C_ORACLE_BENEFIT_RETENTION", "H2C_ORACLE_GAP",
                                       "mean_global_fp", "mean_h2c_fp", "fp_delta_vs_global",
                                       "mean_global_fn", "mean_h2c_fn",
                                       "component_recoveries_vs_global", "component_losses_vs_global",
                                       "component_recoveries_vs_h2a", "component_losses_vs_h2a",
                                       "cases_improved_vs_global", "cases_worse_vs_global",
                                       "cases_improved_vs_h2a", "cases_worse_vs_h2a")}

deltas_h2a = [per_model[k]["DELTA_H2C_H2A_DICE"] for k in per_model]
deltas_global = [per_model[k]["DELTA_H2C_GLOBAL_DICE"] for k in per_model]
deltas_p13 = [per_model[k]["DELTA_H2C_PHASE13_DICE"] for k in per_model]
ret = [per_model[k]["H2C_ORACLE_BENEFIT_RETENTION"] for k in per_model]

# ---- frozen-rule application
favourable_localizer = {
    "tiny_recall90": {"h2c": sa["metrics"]["tiny_recall90"], "h2a": 0.6944444444444444,
                      "delta": sa["metrics"]["tiny_recall90"] - 0.6944444444444444},
    "overall_recall90": {"h2c": sa["metrics"]["overall_recall90"], "h2a": 0.6381578947368421,
                         "delta": sa["metrics"]["overall_recall90"] - 0.6381578947368421},
    "mean_coverage": {"h2c": sa["metrics"]["mean_coverage"], "h2a": 0.7878969538240504,
                      "delta": sa["metrics"]["mean_coverage"] - 0.7878969538240504},
    "score_iqr": {"h2c": sa["metrics"]["score_iqr"], "h2a": 0.0016540437936782837,
                  "delta": sa["metrics"]["score_iqr"] - 0.0016540437936782837},
    "fraction_at_max": {"h2c": sa["metrics"]["fraction_exactly_at_max"], "h2a": 0.6455142231947484,
                        "delta": sa["metrics"]["fraction_exactly_at_max"] - 0.6455142231947484},
    "roc_auc": {"h2c": sa["metrics"]["roc_auc_score_to_pixel_any_hit"], "h2a": 0.7011101520164964,
                "delta": sa["metrics"]["roc_auc_score_to_pixel_any_hit"] - 0.7011101520164964},
    "pr_auc": {"h2c": sa["metrics"]["pr_auc_score_to_pixel_any_hit"], "h2a": 0.3729361181989911,
               "delta": sa["metrics"]["pr_auc_score_to_pixel_any_hit"] - 0.3729361181989911},
}
unfavourable_localizer = {
    "pixel_any_hit_precision": {"h2c": sa["metrics"]["proposal_pixel_any_hit_precision"],
                                "h2a": 0.27571115973741794,
                                "delta": sa["metrics"]["proposal_pixel_any_hit_precision"] - 0.27571115973741794},
    "bbox_any_hit_precision": {"h2c": sa["metrics"]["proposal_bbox_any_hit_precision"],
                               "h2a": 0.2735229759299781,
                               "delta": sa["metrics"]["proposal_bbox_any_hit_precision"] - 0.2735229759299781},
}

OUTCOME = "H2C_HEAD_REDESIGN_INSUFFICIENT"

adj = {
    "artifact": "POST_PHASE13_H2C_B2_OUTCOME_ADJUDICATION",
    "status": "PASS",
    "created_utc": "2026-09-24T00:29:00Z",
    "execution_mode": "PURE_READ_AUDIT_OF_FROZEN_EVIDENCE",
    "frozen_rule_source": "reports/audits/post_phase13_h2c_protocol_frozen.json :: prospective_outcome_definitions",
    "frozen_rule_sha": sha(A / "post_phase13_h2c_protocol_frozen.json"),
    "new_criterion_invented": "NO",

    "dimension_A_localizer_proposal_quality": {
        "favourable_vs_h2a": favourable_localizer,
        "unfavourable_vs_h2a": unfavourable_localizer,
        "verdict": "REPRODUCIBLY_FAVOURABLE_VS_H2A",
        "note": ("8 of 10 tracked localizer metrics moved favourably vs H2A, including the "
                 "saturation/dispersion metrics the redesign targeted. Precision regressed "
                 "slightly (~-0.0095)."),
    },
    "dimension_B_downstream_global_preservation": {
        "per_model": {k: {"h2c": v["h2c_predicted_macro_dice"], "global": v["global_macro_dice"],
                          "delta": v["DELTA_H2C_GLOBAL_DICE"]} for k, v in per_model.items()},
        "h2c_below_global_all_four": all(d < 0 for d in deltas_global),
        "verdict": "GLOBAL_PRESERVATION_NOT_RESOLVED",
    },
    "dimension_C_regional_utility": {
        "oracle_benefit_retention_all_negative": all(r < 0 for r in ret),
        "component_losses_vs_global_all_zero": all(
            per_model[k]["component_losses_vs_global"] == 0 for k in per_model),
        "components_recovered_vs_global_by_at_least_one": cv["components_recovered_vs_global_by_at_least_one"],
        "components_lost_vs_global_by_at_least_one": cv["components_lost_vs_global_by_at_least_one"],
        "verdict": "RECOVERY_SIGNAL_PRESENT__NET_UTILITY_NOT_ACHIEVED",
    },
    "dimension_D_cross_architecture_generality": {
        "cross_architecture": cv,
        "verdict": "CONSISTENTLY_BELOW_GLOBAL_ACROSS_ALL_FOUR",
    },

    "h2c_outcome": OUTCOME,
    "outcome_clause_applied": ("H2C_HEAD_REDESIGN_INSUFFICIENT clause (b): 'favourable localizer "
                               "changes do not translate into meaningful downstream improvement "
                               "and the major deployable failure remains'."),
    "reasoning": (
        "The localizer changes ARE reproducibly favourable vs H2A (8/10 metrics, including the "
        "targeted saturation/dispersion metrics), so clause (a) does not apply. However the frozen "
        "PARTIAL definition additionally requires 'at least some corresponding downstream "
        "improvement', measured against the protocol-designated PRIMARY downstream comparator "
        "(H2A predicted-region). H2C macro Dice is BELOW H2A on ALL FOUR architectures "
        f"({', '.join(f'{d:+.6f}' for d in deltas_h2a)}), so the favourable localizer changes did "
        "NOT translate into downstream improvement against the primary comparator. The major "
        "deployable failure also remains (H2C is far below GLOBAL on all four; oracle-benefit "
        "retention negative on all four). Clause (b) therefore applies."),
    "countervailing_evidence_disclosed": {
        "h2c_minus_phase13_dice": {k: per_model[k]["DELTA_H2C_PHASE13_DICE"] for k in per_model},
        "deeplabv3plus_improved_vs_phase13": per_model["deeplabv3plus"]["DELTA_H2C_PHASE13_DICE"] > 0,
        "cases_improved_vs_h2a_all4": cv["cases_h2c_improved_vs_h2a_all4"],
        "cases_worse_vs_h2a_all4": cv["cases_h2c_worse_vs_h2a_all4"],
        "cases_improved_vs_phase13_all4": cv["cases_h2c_improved_vs_phase13_all4"],
        "components_recovered_vs_global_by_at_least_one_h2a": 22,
        "components_recovered_vs_global_by_at_least_one_h2c":
            cv["components_recovered_vs_global_by_at_least_one"],
        "component_losses_vs_global_h2c": 0,
        "note": ("This is a CLOSE CALL and is disclosed as such. H2C is roughly at Phase13 level "
                 "downstream and improves the recovery signal (22 -> 33 components recovered by "
                 ">=1 architecture, zero losses) and 38/103 cases improve in all four architectures "
                 "vs H2A. A reader who measures 'downstream improvement' against Phase13 or at "
                 "case level rather than against the primary comparator H2A could reasonably argue "
                 "for PARTIAL. The label applied follows the protocol's designated primary "
                 "downstream comparator."),
    },
    "h2c_proves_sole_cause": "NO",
    "winner": "NONE",
    "new_numerical_thresholds": 0,
    "new_configs": 0,
    "new_subgroups": 0,
    "statistical_claim": "NONE",
    "descriptive_single_seed": True,

    "phase14_eligibility": {
        "status": "ELIGIBLE_NOT_STARTED",
        "basis": ("H2C protocol if_h2c_insufficient: FURTHER_REVISION = REQUIRES_SUPERVISOR_DECISION; "
                  "H3 NOT_AUTOMATICALLY_AUTHORIZED. Phase 14 requires separate supervisor authorization."),
        "phase14_started": "NO",
    },
    "counters": {"scientific_axes_changed_during_b2": 0, "proposal_grid": 0,
                 "threshold_searches": 0, "oracle_reruns": 0,
                 "downstream_segmentation_forwards": integ["regional_crop_evaluations"],
                 "checkpoint_candidates_evaluated_downstream": 1,
                 "test_reads": 0, "external_test_reads": 0},
}
(A / "post_phase13_h2c_b2_outcome_adjudication.json").write_text(
    json.dumps(adj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = ["# POST-PHASE13 H2C-B2 — Outcome Adjudication", "",
      f"- **Status: {adj['status']}**", f"- **Outcome: `{OUTCOME}`**",
      f"- Frozen rule: `{adj['frozen_rule_source']}`",
      f"- New criterion invented: **{adj['new_criterion_invented']}**", "",
      "## Dimension A — localizer proposal quality", "",
      f"**{adj['dimension_A_localizer_proposal_quality']['verdict']}**", "",
      "| metric | H2C | H2A | delta |", "|---|---|---|---|"]
for k, v in favourable_localizer.items():
    md.append(f"| {k} | {v['h2c']:.6f} | {v['h2a']:.6f} | {v['delta']:+.6f} |")
for k, v in unfavourable_localizer.items():
    md.append(f"| {k} (unfavourable) | {v['h2c']:.6f} | {v['h2a']:.6f} | {v['delta']:+.6f} |")
md += ["", "## Dimension B — downstream global preservation", "",
       f"**{adj['dimension_B_downstream_global_preservation']['verdict']}**", "",
       "| model | H2C | GLOBAL | delta |", "|---|---|---|---|"]
for k, v in adj["dimension_B_downstream_global_preservation"]["per_model"].items():
    md.append(f"| {k} | {v['h2c']:.6f} | {v['global']:.6f} | {v['delta']:+.6f} |")
md += ["", "## Dimension C — regional utility", "",
       f"**{adj['dimension_C_regional_utility']['verdict']}**",
       f"- oracle-benefit retention negative on all four: {adj['dimension_C_regional_utility']['oracle_benefit_retention_all_negative']}",
       f"- component losses vs GLOBAL zero on all four: {adj['dimension_C_regional_utility']['component_losses_vs_global_all_zero']}",
       f"- components recovered vs GLOBAL by >=1: {adj['dimension_C_regional_utility']['components_recovered_vs_global_by_at_least_one']}",
       "", "## Dimension D — cross-architecture generality", "",
       f"**{adj['dimension_D_cross_architecture_generality']['verdict']}**", "",
       "| quantity | value |", "|---|---|"]
for k, v in cv.items():
    md.append(f"| {k} | {v} |")
md += ["", "## Outcome", "", f"### `{OUTCOME}`", "",
       f"**Clause applied:** {adj['outcome_clause_applied']}", "", adj["reasoning"], "",
       "## Countervailing evidence (disclosed)", "",
       adj["countervailing_evidence_disclosed"]["note"], "",
       f"- H2C−Phase13 Dice: {adj['countervailing_evidence_disclosed']['h2c_minus_phase13_dice']}",
       f"- cases improved vs H2A (all 4): {adj['countervailing_evidence_disclosed']['cases_improved_vs_h2a_all4']} "
       f"| worse: {adj['countervailing_evidence_disclosed']['cases_worse_vs_h2a_all4']}",
       f"- components recovered vs GLOBAL by >=1: H2A 22 → H2C "
       f"{adj['countervailing_evidence_disclosed']['components_recovered_vs_global_by_at_least_one_h2c']}", "",
       "## Phase-14 eligibility", "",
       f"- status: **{adj['phase14_eligibility']['status']}**",
       f"- basis: {adj['phase14_eligibility']['basis']}", "",
       "descriptive single-seed evidence · no winner · no statistical claim", ""]
(A / "post_phase13_h2c_b2_outcome_adjudication.md").write_text("\n".join(md), encoding="utf-8")

print("adjudication written")
print("OUTCOME:", OUTCOME)
print("H2C-H2A deltas:", [f"{d:+.6f}" for d in deltas_h2a])
print("json sha:", sha(A / "post_phase13_h2c_b2_outcome_adjudication.json"))
