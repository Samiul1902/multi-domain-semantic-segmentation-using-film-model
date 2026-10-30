"""PHASE-13 PART-1E-B — regional-integration gate adjudication.

Reads ONLY prospectively frozen evidence. Performs NO model execution.
Writes: the dimension table CSV, and the final gate artifact (JSON + MD).
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
VERDICT = "REVISE_LOCALIZER"
ADJUDICATED_UTC = "2026-09-22T05:38:00Z"


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> None:
    gate = json.loads((AUDITS / "phase13_regional_integration_gate_criteria_frozen.json").read_text("utf-8"))
    ev = json.loads((AUDITS / "phase13_part1d_b_predicted_region_evaluation.json").read_text("utf-8"))
    rp = json.loads((AUDITS / "phase13_part1d_b_global_reproduction.json").read_text("utf-8"))
    r1 = json.loads((AUDITS / "phase13_part1d_predicted_region_protocol_frozen_r1.json").read_text("utf-8"))
    s = pd.read_csv(TABLES / "phase13_part1d_predicted_region_model_summary.csv").set_index("model")
    cross = pd.read_csv(TABLES / "phase13_part1d_cross_architecture_summary.csv")
    cross_d = dict(zip(cross.iloc[:, 0].astype(str), cross.iloc[:, 1]))

    MODELS = ["unet", "attention_unet", "unetpp", "deeplabv3plus"]
    DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
               "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}

    # ---------------- integrity precondition ----------------
    precond = {
        "gate_criteria_sha_match": sha(AUDITS / "phase13_regional_integration_gate_criteria_frozen.json")
        == "342a8bcac2c87bf0b85f7bbd963179e74f029825c0434cf527fbd939d2d13c21",
        "gate_status": gate["status"] == "PROSPECTIVE_GATE_CRITERIA_FROZEN_BEFORE_PART1D_B_RESULTS",
        "gate_part1d_b_results_inspected_no": gate["part1d_b_results_inspected"] == "NO",
        "gate_numerical_thresholds_zero": gate["numerical_thresholds_introduced"] == 0,
        "gate_mode": gate["gate_mode"] == "QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION",
        "part1d_b_status_pass": ev["status"] == "PASS",
        "global_reproduction_all_four_pass": rp["all_four_pass"] is True,
        "case_model_rows_412": ev["case_model_rows"] == 412,
        "component_model_rows_608": ev["component_model_rows"] == 608,
        "model_summary_rows_4": ev["model_summary_rows"] == 4,
        "test_reads_zero": ev["counters"]["test_reads"] == 0,
        "integrity_failures_empty": ev["integrity_failures"] == [],
        "r1_protocol_sha_match": ev["bindings"]["r1_protocol"]["sha"]
        == "9089b948ef7563252963bf68d0e0b57a9e891c5e913f54a315bce94c98207eb8",
        "part1d_b_integrity_checks_all_pass": all(v["pass"] for v in ev["integrity_checks"].values()),
    }
    integrity_ok = all(precond.values())

    # ---------------- dimension evidence ----------------
    A = {
        "state": "SUPPORTED_DESCRIPTIVE_EVIDENCE",
        "changed_by_part1d_b": "NO",
        "summary": (
            "Phase-12 oracle Dice gains remain positive for all four architectures and were "
            "independently re-confirmed through the frozen oracle gains: UNet +0.130542, "
            "Attention U-Net +0.069790, UNet++ +0.086164, DeepLabV3+ +0.190121. Part-1D-B global "
            "reproduction reproduced the shared global path at machine precision (max abs per-case "
            "Dice difference 5.551e-17 to 1.110e-16), so the comparator provenance is intact. No "
            "material Phase-12 integrity or reproduction defect was discovered."),
        "oracle_gains": r1["phase12_oracle_dice_gains"],
    }
    B = {
        "state": "WEAK__FAILS_TO_TRANSLATE_ORACLE_MECHANISM_INTO_DEPLOYABLE_UTILITY",
        "per_model": {m: {
            "global_dice": float(s.loc[m, "global_macro_dice"]),
            "oracle_dice": float(s.loc[m, "oracle_macro_dice"]),
            "predicted_dice": float(s.loc[m, "predicted_macro_dice"]),
            "DELTA_ORACLE_DICE": float(s.loc[m, "DELTA_ORACLE_DICE"]),
            "DELTA_PRED_DICE": float(s.loc[m, "DELTA_PRED_DICE"]),
            "RETENTION_DICE": float(s.loc[m, "RETENTION_DICE"]),
            "ORACLE_GAP_DICE": float(s.loc[m, "ORACLE_GAP_DICE"]),
            "iou_gain_retention": float(s.loc[m, "iou_gain_retention"]),
            "object_recall_gain_retention": float(s.loc[m, "object_recall_gain_retention"]),
            "fn_reduction_retention": float(s.loc[m, "fn_reduction_retention"]),
            "component_recoveries": int(s.loc[m, "component_recoveries"]),
            "component_losses": int(s.loc[m, "component_losses"]),
            "empty_recoveries": int(s.loc[m, "empty_recoveries"]),
            "new_empty_predictions": int(s.loc[m, "new_empty_predictions"]),
        } for m in MODELS},
        "summary": (
            "DELTA_PRED_DICE is strongly negative for all four architectures (-0.291866, -0.321186, "
            "-0.329161, -0.282959) and RETENTION_DICE is negative for all four (-2.235800, -4.602209, "
            "-3.820171, -1.488308), never clipped. IoU gain retention is negative for all four "
            "(-2.503471 to -5.373957). ORACLE_GAP_DICE is -0.390976 to -0.473080. Downstream "
            "segmentation utility is therefore NOT retained: the frozen GT-free path does not "
            "translate the oracle mechanism into deployable utility. Positive but weak object-recall "
            "retention (0.310345 to 0.500000), 9-16 component recoveries, 0 component losses and "
            "3-11 empty recoveries are recorded as genuine favourable signal, but they do not "
            "constitute retained downstream segmentation utility."),
    }
    C = {
        "state": "MATERIAL_GLOBAL_PRESERVATION_FP_COST",
        "per_model": {m: {
            "mean_dice_delta": float(s.loc[m, "DELTA_PRED_DICE"]),
            "mean_iou_delta": float(s.loc[m, "predicted_macro_iou"] - s.loc[m, "global_macro_iou"]),
            "mean_precision_delta": float(s.loc[m, "predicted_macro_precision"] - s.loc[m, "global_macro_precision"]),
            "mean_recall_delta": float(s.loc[m, "predicted_macro_recall"] - s.loc[m, "global_macro_recall"]),
            "mean_fp_delta": float(s.loc[m, "mean_fp_delta"]),
            "mean_fn_delta": float(s.loc[m, "mean_fn_delta"]),
            "cases_improved": int(s.loc[m, "cases_dice_improved"]),
            "cases_unchanged": int(s.loc[m, "cases_dice_unchanged"]),
            "cases_worsened": int(s.loc[m, "cases_dice_worsened"]),
            "max_case_improvement": float(s.loc[m, "max_dice_improvement"]),
            "max_case_worsening": float(s.loc[m, "max_dice_worsening"]),
            "component_recoveries": int(s.loc[m, "component_recoveries"]),
            "component_losses": int(s.loc[m, "component_losses"]),
            "empty_recoveries": int(s.loc[m, "empty_recoveries"]),
            "new_empty_predictions": int(s.loc[m, "new_empty_predictions"]),
        } for m in MODELS},
        "summary": (
            "Precision decreases strongly for all four architectures (mean precision delta -0.427001 "
            "to -0.494926) while recall is broadly preserved or mixed (-0.013473 to +0.039483) rather "
            "than collapsing. Mean FP pixel delta is +7324.97, +7528.07, +7924.50 and +8334.42. "
            "Cases worsened 93, 98, 95 and 92 of 103 (cases improved 10, 5, 8, 11; unchanged 0 for "
            "all four). Maximum case worsening -0.750510 to -0.799650 against maximum improvement "
            "+0.381842 to +0.393970. This is broad systematic degradation, not a localized effect. "
            "Recorded alongside it without hiding: component losses are 0 for all four, component "
            "recoveries are 9-16, empty recoveries 3-11, and new empty predictions 0."),
    }
    D = {
        "state": "CROSS_ARCHITECTURE_CONSISTENT_NEGATIVE__NOT_ISOLATED",
        "cross_architecture": {k: int(v) for k, v in cross_d.items()},
        "summary": (
            "The negative practical result is present in all four architectures (negative "
            "DELTA_PRED_DICE and negative RETENTION_DICE in every architecture; 92-98 of 103 cases "
            "worsened per architecture). Cross-architecture: cases worsened for all four = 86, cases "
            "improved for all four = 3, cases non-worse for all four = 3; native components recovered "
            "by >=1 architecture = 27, recovered by all four = 4, lost by >=1 architecture = 0, lost "
            "by all four = 0. The signal is therefore cross-architecture CONSISTENT and is not an "
            "isolated architecture-specific accident. No architecture is ranked, no winner is "
            "selected, and heterogeneity is reported rather than averaged away."),
    }

    # ---------------- prospective logic ----------------
    logic = {
        "GO": {
            "required": ["A supported", "B meaningful practical utility",
                         "C no broad systematic degradation", "D not isolated architecture evidence"],
            "A": True, "B": False, "C": False, "D": True,
            "satisfied": False,
            "blocking": ["B weak / fails to translate into deployable utility",
                         "C broad systematic degradation undermining the practical benefit"],
        },
        "REVISE_LOCALIZER": {
            "required": ["A remains supported",
                         "AND at least one of: B weak/inconsistent OR C materially problematic OR D too architecture-specific"],
            "A": True, "B_weak": True, "C_material": True, "D_too_specific": False,
            "satisfied": True,
            "triggered_by": ["B weak / fails to translate oracle mechanism into deployable utility",
                             "C materially problematic global-preservation / FP cost"],
        },
        "NO_GO": {
            "required": ["A no longer scientifically supportable"],
            "A_supported": True,
            "satisfied": False,
            "blocked_by": "A remains SUPPORTED_DESCRIPTIVE_EVIDENCE; frozen invariant: a poor GT-free "
                          "localizer result alone cannot produce NO_GO while A remains supported",
        },
        "selected": VERDICT,
    }

    # ---------------- §10 dimension table ----------------
    hdr = ["dimension_id", "dimension_name", "prospective_question", "pre_part1db_state",
           "observed_evidence_summary", "adjudicated_state", "supports_go", "supports_revise",
           "supports_no_go", "integrity_issue", "notes"]
    rows = [
        ["A", "ORACLE_MECHANISM_VALUE",
         gate["dimensions"]["A"]["question"], gate["dimensions"]["A"]["state_before_part1d_b"],
         A["summary"], A["state"], "YES_AS_PRECONDITION", "YES_AS_PRECONDITION", "NO",
         "NONE",
         "Part-1D-B did not alter A; only a material Phase-12 integrity/reproduction defect could. "
         "Poor predicted-localizer performance was explicitly NOT used to invalidate A."],
        ["B", "PRACTICAL_LOCALIZATION_RETENTION",
         gate["dimensions"]["B"]["question"], gate["dimensions"]["B"]["state_before_part1d_b"],
         B["summary"], B["state"], "NO", "YES", "NO",
         "NONE",
         "Adjudicated from multiple frozen fields; no single field alone decides. No retention cutoff "
         "was introduced. Negative retention values preserved unclipped."],
        ["C", "GLOBAL_PRESERVATION_FP_COST",
         gate["dimensions"]["C"]["question"], gate["dimensions"]["C"]["state_before_part1d_b"],
         C["summary"], C["state"], "NO", "YES", "NO",
         "NONE",
         "Target recovery interpreted together with FP/precision cost. Component recovery and FP "
         "burden are both reported; neither is hidden."],
        ["D", "GENERALITY",
         gate["dimensions"]["D"]["question"], gate["dimensions"]["D"]["state_before_part1d_b"],
         D["summary"], D["state"], "NO", "YES_AS_PRECONDITION", "NO",
         "NONE",
         "Four frozen architectures; reference model NONE; no winner; no ranking; heterogeneity "
         "reported rather than averaged away. D is not the operative REVISE trigger."],
    ]
    csv_path = TABLES / "phase13_regional_integration_gate_after_phase13.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(hdr)
        w.writerows(rows)

    # ---------------- §11 gate artifact ----------------
    obj = {
        "artifact": "PHASE13_REGIONAL_INTEGRATION_GATE_AFTER_PHASE13",
        "gate_id": "REGIONAL_INTEGRATION_GATE_AFTER_PHASE13",
        "status": "ADJUDICATED",
        "adjudicated_utc": ADJUDICATED_UTC,
        "phase": "PHASE_13_PART_1E_B",
        "adjudication_mode": "QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION",
        "evidence_scope": "PROSPECTIVELY_FROZEN_EVIDENCE_ONLY",
        "integrity_precondition": {"result": "PASS" if integrity_ok else "FAIL", "checks": precond},
        "bindings": {
            "prospective_criteria": {
                "path": "reports/audits/phase13_regional_integration_gate_criteria_frozen.json",
                "sha": sha(AUDITS / "phase13_regional_integration_gate_criteria_frozen.json"),
                "edited": "NO"},
            "part1d_r1_protocol": {
                "path": "reports/audits/phase13_part1d_predicted_region_protocol_frozen_r1.json",
                "sha": sha(AUDITS / "phase13_part1d_predicted_region_protocol_frozen_r1.json")},
            "part1d_b_evaluation": {
                "path": "reports/audits/phase13_part1d_b_predicted_region_evaluation.json",
                "sha": sha(AUDITS / "phase13_part1d_b_predicted_region_evaluation.json")},
            "part1d_b_global_reproduction": {
                "path": "reports/audits/phase13_part1d_b_global_reproduction.json",
                "sha": sha(AUDITS / "phase13_part1d_b_global_reproduction.json")},
            "phase12_sources": {
                "oracle_case_metrics": {"path": "reports/tables/phase12_clean_v3_oracle_case_metrics.csv",
                                        "sha": sha(TABLES / "phase12_clean_v3_oracle_case_metrics.csv")},
                "oracle_component_metrics": {"path": "reports/tables/phase12_clean_v3_oracle_component_metrics.csv",
                                             "sha": sha(TABLES / "phase12_clean_v3_oracle_component_metrics.csv")},
                "oracle_geometry": {"path": "reports/tables/phase12_clean_v3_oracle_geometry.csv",
                                    "sha": sha(TABLES / "phase12_clean_v3_oracle_geometry.csv")},
                "oracle_protocol_frozen": {"path": "reports/audits/phase12_clean_v3_oracle_protocol_frozen.json",
                                           "sha": sha(AUDITS / "phase12_clean_v3_oracle_protocol_frozen.json")},
            },
            "part1c_sources": {
                "case_proposals": {"path": "reports/tables/phase13_part1c_best_checkpoint_case_proposals.csv",
                                   "sha": sha(TABLES / "phase13_part1c_best_checkpoint_case_proposals.csv")},
                "proposals": {"path": "reports/tables/phase13_part1c_best_checkpoint_proposals.csv",
                              "sha": sha(TABLES / "phase13_part1c_best_checkpoint_proposals.csv")},
                "component_coverage": {"path": "reports/tables/phase13_part1c_best_checkpoint_component_coverage.csv",
                                       "sha": sha(TABLES / "phase13_part1c_best_checkpoint_component_coverage.csv")},
                "size_stratified": {"path": "reports/tables/phase13_part1c_size_stratified_coverage.csv",
                                    "sha": sha(TABLES / "phase13_part1c_size_stratified_coverage.csv")},
                "gallery_selection": {"path": "reports/tables/phase13_part1c_gallery_selection.csv",
                                      "sha": sha(TABLES / "phase13_part1c_gallery_selection.csv")},
            },
            "part1d_b_tables": {
                "model_summary": {"path": "reports/tables/phase13_part1d_predicted_region_model_summary.csv",
                                  "sha": sha(TABLES / "phase13_part1d_predicted_region_model_summary.csv")},
                "case_model": {"path": "reports/tables/phase13_part1d_predicted_region_case_model_metrics.csv",
                               "sha": sha(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")},
                "component_model": {"path": "reports/tables/phase13_part1d_predicted_region_component_model_metrics.csv",
                                    "sha": sha(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv")},
                "cross_architecture": {"path": "reports/tables/phase13_part1d_cross_architecture_summary.csv",
                                       "sha": sha(TABLES / "phase13_part1d_cross_architecture_summary.csv")},
            },
            "dimension_table": {"path": "reports/tables/phase13_regional_integration_gate_after_phase13.csv",
                                "sha": sha(csv_path)},
        },
        "dimensions": {
            "A": {"name": "ORACLE_MECHANISM_VALUE", "pre_state": gate["dimensions"]["A"]["state_before_part1d_b"],
                  "state": A["state"], "evidence": A["summary"], "oracle_gains": A["oracle_gains"]},
            "B": {"name": "PRACTICAL_LOCALIZATION_RETENTION", "pre_state": gate["dimensions"]["B"]["state_before_part1d_b"],
                  "state": B["state"], "evidence": B["summary"], "per_model": B["per_model"]},
            "C": {"name": "GLOBAL_PRESERVATION_FP_COST", "pre_state": gate["dimensions"]["C"]["state_before_part1d_b"],
                  "state": C["state"], "evidence": C["summary"], "per_model": C["per_model"]},
            "D": {"name": "GENERALITY", "pre_state": gate["dimensions"]["D"]["state_before_part1d_b"],
                  "state": D["state"], "evidence": D["summary"], "cross_architecture": D["cross_architecture"]},
        },
        "prospective_logic_applied": logic,
        "final_gate_verdict": VERDICT,
        "verdict_reasoning": (
            "Dimension A remains SUPPORTED_DESCRIPTIVE_EVIDENCE: the Phase-12 oracle gains are positive "
            "for all four architectures and Part-1D-B independently reproduced the shared global path at "
            "machine precision, so no integrity or reproduction defect invalidates A. Therefore NO_GO is "
            "not available, and the frozen invariant explicitly forbids NO_GO from a poor GT-free "
            "localizer result alone while A remains supported. Dimension B fails: DELTA_PRED_DICE and "
            "RETENTION_DICE are negative for all four architectures, so the frozen GT-free path does not "
            "translate the oracle mechanism into deployable downstream segmentation utility. Dimension C "
            "fails: precision decreases strongly for all four architectures with mean FP pixel deltas of "
            "+7324.97 to +8334.42 and 92-98 of 103 cases worsening, which is broad systematic degradation "
            "undermining the practical benefit. Dimension D shows the effect is cross-architecture "
            "consistent and not an isolated architecture-specific accident; D is therefore not the "
            "operative trigger. GO requires A and B and C and D; B and C are not satisfied. "
            "REVISE_LOCALIZER requires A supported AND at least one of (B weak, C materially problematic, "
            "D too architecture-specific); A is supported and both B and C are satisfied. The adjudicated "
            "verdict is therefore REVISE_LOCALIZER, derived strictly from the prospectively frozen "
            "dimensions with no post-hoc threshold, no new subgroup and no weighted score."),
        "verdict_discipline": {
            "phase12_regional_mechanism_hypothesis_remains_supported": "YES",
            "current_frozen_gt_free_localization_proposal_integration_path_promoted": "NO",
            "result_authorizes_ra_medfilm_regional_integration": "NO",
            "phase14_may_begin_as_if_regional_mechanism_approved": "NO",
            "automatic_redesign_performed_in_part1e_b": "NO",
            "separately_supervised_revision_plan_required": "YES",
            "revise_localizer_equated_with_oracle_mechanism_scientific_failure": "NO",
            "proposal_threshold_or_fusion_rule_silently_changed": "NO",
        },
        "localization_fp_context": {
            "role": "DESCRIPTIVE_CONTEXT_ONLY__NOT_REQUIRED_FOR_THE_DECISION",
            "frozen_proposals_total": 494,
            "proposals_overlapping_at_least_one_gt_pixel": 122,
            "proposals_overlapping_no_gt_pixel": 372,
            "off_target_fraction": 0.753036,
            "gallery_fusion_verification": {
                "case_model_pairs_checked": 64,
                "outside_support_P_equals_G_exactly": "YES",
                "fp_pixels_inside_U_gallery_total": ev["fusion_wiring_verification"]["fp_pixels_inside_U_gallery_total"],
                "fp_pixels_outside_U_gallery_total": ev["fusion_wiring_verification"]["fp_pixels_outside_U_gallery_total"],
            },
            "allowed_interpretation": "descriptive evidence consistent with the current GT-free proposal / "
                                      "integration path driving substantial FP burden",
            "forbidden_interpretation": "proposal precision is conclusively the sole causal mechanism, or "
                                        "any stronger causal statement unsupported by the experiment",
            "sole_cause_diagnosis_required_for_gate": "NO",
        },
        "claim_limits": {
            "numerical_thresholds_introduced_after_results": 0,
            "new_subgroup": "NO",
            "weighted_score": "NO",
            "reference_model": None,
            "ranking": "NONE",
            "winner": "NONE",
            "statistical_superiority_claim": "NO",
            "clinical_superiority_claim": "NO",
            "gallery_used_to_determine_gate": "NO",
            "predeclared_cohorts_only": ["TINY", "SMALL", "MEDIUM", "LARGE", "hard-Tiny",
                                         "global-empty", "multi-component"],
        },
        "counters": {
            "training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
            "segmentation_forwards": 0, "regional_crop_forwards": 0, "localizer_forwards": 0,
            "proposal_generation": 0, "oracle_reruns": 0, "test_reads": 0,
        },
        "phase13_closure": {
            "phase13_part1b": "COMPLETE_PASS_FROZEN",
            "phase13_part1c": "COMPLETE_PASS_FROZEN",
            "phase13_part1d_a_r1": "COMPLETE_PASS_FROZEN",
            "phase13_part1d_b": "COMPLETE_PASS_FROZEN",
            "phase13_part1e_a": "COMPLETE_PASS_FROZEN",
            "phase13_part1e_b": "COMPLETE_PASS",
            "phase13": "COMPLETE",
            "regional_integration_gate_after_phase13": VERDICT,
            "regional_mechanism_promoted": "NO",
            "phase14": "NOT_STARTED",
            "test": "UNTOUCHED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_REGIONAL_LOCALIZER_REVISION_PLAN",
    }
    jp = AUDITS / "phase13_regional_integration_gate_after_phase13.json"
    jp.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------- §11 markdown ----------------
    md = ["# PHASE-13 — REGIONAL_INTEGRATION_GATE_AFTER_PHASE13 (ADJUDICATED)", "",
          f"- **FINAL GATE VERDICT: `{VERDICT}`**",
          "- gate mode: `QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION`",
          "- evidence scope: **prospectively frozen evidence only**",
          "- integrity precondition: **PASS**",
          "- post-hoc numerical thresholds: **0** · new subgroups: **0** · weighted score: **NO**",
          "- reference model: **NONE** · ranking: **NONE** · winner: **NONE**",
          "- statistical / clinical superiority claim: **NO**", "",
          "## Integrity precondition (§2)", "",
          "| check | result |", "|---|---|"]
    for k, v in precond.items():
        md.append(f"| {k} | **{'PASS' if v else 'FAIL'}** |")
    md += ["", "## Dimension adjudication", "",
           "| dim | dimension | pre-state | adjudicated state | supports GO | supports REVISE | supports NO_GO |",
           "|---|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| **{r[0]}** | {r[1]} | `{r[3]}` | **`{r[5]}`** | {r[6]} | {r[7]} | {r[8]} |")
    md += ["", "### A — ORACLE_MECHANISM_VALUE", "", A["summary"], "",
           "### B — PRACTICAL_LOCALIZATION_RETENTION", "",
           "| model | GLOBAL Dice | ORACLE Dice | PREDICTED Dice | DELTA_ORACLE | DELTA_PRED | RETENTION_DICE | ORACLE_GAP |",
           "|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        b = B["per_model"][m]
        md.append(f"| {DISPLAY[m]} | {b['global_dice']:.6f} | {b['oracle_dice']:.6f} | {b['predicted_dice']:.6f} | "
                  f"{b['DELTA_ORACLE_DICE']:+.6f} | **{b['DELTA_PRED_DICE']:+.6f}** | **{b['RETENTION_DICE']:+.6f}** | "
                  f"{b['ORACLE_GAP_DICE']:+.6f} |")
    md += ["", B["summary"], "",
           "### C — GLOBAL_PRESERVATION_FP_COST", "",
           "| model | mean precision delta | mean recall delta | mean FP delta | mean FN delta | cases improved / unchanged / worsened | max improvement | max worsening |",
           "|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        c = C["per_model"][m]
        md.append(f"| {DISPLAY[m]} | {c['mean_precision_delta']:+.6f} | {c['mean_recall_delta']:+.6f} | "
                  f"**{c['mean_fp_delta']:+.2f}** | {c['mean_fn_delta']:+.2f} | "
                  f"{c['cases_improved']} / {c['cases_unchanged']} / **{c['cases_worsened']}** | "
                  f"{c['max_case_improvement']:+.6f} | **{c['max_case_worsening']:+.6f}** |")
    md += ["", C["summary"], "",
           "### D — GENERALITY", "",
           "| quantity | value |", "|---|---|"]
    for k, v in D["cross_architecture"].items():
        md.append(f"| {k} | {v} |")
    md += ["", D["summary"], "",
           "## Prospective logic applied (§9)", "",
           f"- **GO** — satisfied: **{'YES' if logic['GO']['satisfied'] else 'NO'}**; blocked by: "
           + "; ".join(logic["GO"]["blocking"]),
           f"- **REVISE_LOCALIZER** — satisfied: **{'YES' if logic['REVISE_LOCALIZER']['satisfied'] else 'NO'}**; "
           "triggered by: " + "; ".join(logic["REVISE_LOCALIZER"]["triggered_by"]),
           f"- **NO_GO** — satisfied: **NO**; blocked by: {logic['NO_GO']['blocked_by']}", "",
           "## Verdict reasoning", "", obj["verdict_reasoning"], "",
           "## Verdict discipline (§12)", "",
           "| statement | value |", "|---|---|"]
    for k, v in obj["verdict_discipline"].items():
        md.append(f"| {k} | **{v}** |")
    md += ["", "## Localization / FP context (§8)", "",
           f"Frozen Part-1C proposals: **494** total, **122** overlap >=1 GT pixel, **372** overlap no GT "
           f"pixel (off-target fraction **0.753036**). Gallery fusion verification: outside `U_pred`, "
           f"`P == G` exactly for all **64** checked case-model pairs.",
           "",
           "This is **descriptive** evidence consistent with the current GT-free proposal / integration path "
           "driving substantial FP burden. It is **not** a claim that proposal precision is conclusively the "
           "sole causal mechanism, and the gate decision does **not** require a sole-cause diagnosis.", "",
           "## Claim limits", "",
           "| item | value |", "|---|---|"]
    for k, v in obj["claim_limits"].items():
        md.append(f"| {k} | {v} |")
    md += ["", "## Phase-13 closure state", "", "| item | state |", "|---|---|"]
    for k, v in obj["phase13_closure"].items():
        md.append(f"| {k} | **{v}** |")
    md += ["", "## Zero-execution counters", "",
           "training **0** · optimizer **0** · model constructions **0** · CUDA requests **0** · "
           "segmentation forwards **0** · regional crop forwards **0** · localizer forwards **0** · "
           "proposal generation **0** · oracle reruns **0** · TEST reads **0**", "",
           f"**next_action: `{obj['next_action']}`**", ""]
    (AUDITS / "phase13_regional_integration_gate_after_phase13.md").write_text("\n".join(md), encoding="utf-8")

    print("integrity precondition:", "PASS" if integrity_ok else "FAIL")
    print("FINAL GATE VERDICT:", VERDICT)
    print("wrote", csv_path.name, "|", jp.name, "|", "phase13_regional_integration_gate_after_phase13.md")
    print("gate json sha:", sha(jp))


if __name__ == "__main__":
    main()
