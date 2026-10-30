"""H2C-B2 SEC 11 -- execution audit + post-H2C chain closure report."""
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


integ = json.loads((A / "post_phase13_h2c_b2_downstream_integrity.json").read_text("utf-8"))
adj = json.loads((A / "post_phase13_h2c_b2_outcome_adjudication.json").read_text("utf-8"))
fm = json.loads((A / "post_phase13_h2c_b2_freeze_manifest.json").read_text("utf-8"))
b1 = json.loads((A / "post_phase13_h2c_b1_training_evaluation.json").read_text("utf-8"))
s = pd.read_csv(T / "post_phase13_h2c_downstream_model_summary.csv")

per_model = {r["model"]: {k: (int(r[k]) if k.startswith(("component_", "cases_")) else float(r[k]))
                          for k in ("global_macro_dice", "phase13_predicted_macro_dice",
                                    "h2a_predicted_macro_dice", "h2c_predicted_macro_dice",
                                    "oracle_macro_dice", "DELTA_H2C_GLOBAL_DICE",
                                    "DELTA_H2C_PHASE13_DICE", "DELTA_H2C_H2A_DICE",
                                    "H2C_ORACLE_BENEFIT_RETENTION", "H2C_ORACLE_GAP")}
             for _, r in s.iterrows()}

audit = {
    "artifact": "POST_PHASE13_H2C_B2_EXECUTION_AUDIT",
    "status": "PASS",
    "created_utc": "2026-09-24T00:29:00Z",
    "run_id": "post_phase13_h2c_downstream_best_native_policy",
    "h2c_experiment_id": EID,
    "authorization": {"source": "USER_SUPERVISOR_MESSAGE_POST_H2C_B1",
                      "h2c_b2_supervisor_authorization": "GRANTED"},

    "bindings": {
        "h2c_protocol_sha": sha(A / "post_phase13_h2c_protocol_frozen.json"),
        "h2c_b1_training_evaluation_sha": sha(A / "post_phase13_h2c_b1_training_evaluation.json"),
        "h2c_b2_freeze_manifest_sha": sha(A / "post_phase13_h2c_b2_freeze_manifest.json"),
        "h2c_best_pt_sha": sha(ROOT / "checkpoints" / EID / "best.pt"),
        "evaluation_script_sha": sha(ROOT / "scripts/inference/post_phase13_h2c_downstream_eval.py"),
        "b2_integrity_sha": sha(A / "post_phase13_h2c_b2_downstream_integrity.json"),
        "adjudication_sha": sha(A / "post_phase13_h2c_b2_outcome_adjudication.json"),
        "model_summary_sha": sha(T / "post_phase13_h2c_downstream_model_summary.csv"),
        "case_model_sha": sha(T / "post_phase13_h2c_downstream_case_model_metrics.csv"),
        "component_model_sha": sha(T / "post_phase13_h2c_downstream_component_model_metrics.csv"),
        "cross_architecture_sha": sha(T / "post_phase13_h2c_downstream_cross_architecture_summary.csv"),
        "localizer_to_downstream_sha": sha(T / "post_phase13_h2c_localizer_to_downstream_comparison.csv"),
        "comparison_sha": sha(T / "post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv"),
        "reviewer_notebook_sha": sha(ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
                                          / "post_phase13_h2c_downstream_analysis.ipynb"),
    },

    "downstream_configuration": {
        "segmentation_checkpoints": ["unet", "attention_unet", "unetpp", "deeplabv3plus"],
        "proposal_source": "frozen H2C-B1 best-checkpoint proposals (epoch 57)",
        "proposal_policy": {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30},
        "fusion_variant": "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED",
        "segmentation_threshold": 0.5,
        "crop_restore": "Part1D square/padding-correct",
        "global_cache": "frozen Phase13 Part1D-B float32 cache",
        "configurations": 1,
    },

    "results_per_model": per_model,
    "b2_integrity": {"status": integ["status"], "proposal_count": integ["proposal_count"],
                     "regional_crop_evaluations": integ["regional_crop_evaluations"],
                     "global_reproduction": integ["global_reproduction"],
                     "case_model_rows": integ["case_model_rows"],
                     "component_model_rows": integ["component_model_rows"],
                     "model_summary_rows": integ["model_summary_rows"]},

    "h2c_outcome": adj["h2c_outcome"],
    "adjudication_basis": adj["frozen_rule_source"],

    "counters": {
        "logical_training_experiments": 1, "h2c_training_experiments": 1,
        "proposal_configurations": 1, "proposal_grid": 0, "threshold_searches": 0,
        "oracle_reruns": 0, "downstream_segmentation_model_constructions": 4,
        "downstream_segmentation_forwards": integ["regional_crop_evaluations"],
        "checkpoint_candidates_evaluated_downstream": 1,
        "validation_reads": "103 VAL cases",
        "test_reads": 0, "external_test_reads": 0,
    },
    "counter_explanations": {
        "downstream_segmentation_model_constructions": "4 frozen architectures loaded (0 trained)",
        "downstream_segmentation_forwards": "462 proposals x 4 architectures = 1848 regional crops",
        "checkpoint_candidates_evaluated_downstream": "exactly 1 (H2C epoch 57 best.pt)",
    },

    "reporting_defect_scientific_impact": "NONE",
    "scientific_axes_changed_during_b2": 0,
    "phase14": "ELIGIBLE_NOT_STARTED",
    "next_action": "WAIT_FOR_SUPERVISOR_PHASE14_AUTHORIZATION",
}
(A / "post_phase13_h2c_b2_execution_audit.json").write_text(
    json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------------- chain closure report
closure = {
    "artifact": "POST_H2C_CHAIN_CLOSURE_REPORT",
    "status": "COMPLETE",
    "created_utc": "2026-09-24T00:29:00Z",
    "chain": {
        "phase13": "COMPLETE_FROZEN", "original_gate": "REVISE_LOCALIZER_FROZEN",
        "h1": "CLOSED__PARTIAL_MITIGATION_INSUFFICIENT",
        "h2a": "CLOSED__SELECTION_REDESIGN_PARTIAL",
        "h2b": "CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT",
        "h2c_protocol": "COMPLETE_PASS_FROZEN",
        "h2c_rng_preflight": "COMPLETE_PASS_FROZEN",
        "h2c_b1": "COMPLETE_PASS_FROZEN",
        "h2c_b2": "COMPLETE_PASS",
        "h2c_adjudication": "COMPLETE_PASS",
        "h2c": "CLOSED__HEAD_REDESIGN_INSUFFICIENT",
        "phase14": "ELIGIBLE_NOT_STARTED",
        "test": "UNTOUCHED",
    },
    "final_state": "H2C_B2_COMPLETE__H2C_ADJUDICATED__PHASE14_ELIGIBLE_NOT_STARTED",
    "defects_disclosed": [
        {"id": "H2C_B1_AUDIT_IDENTITY_DEFECT",
         "classification": "PERSISTED_REPORTING_DEFECT__AUTHORITATIVE_SCIENTIFIC_STATE_CORRECT",
         "scientific_impact": "NONE", "corrected_additively": "YES"},
    ],
    "test_reads": 0, "external_test_reads": 0,
    "next_action": "WAIT_FOR_SUPERVISOR_PHASE14_AUTHORIZATION",
}
(A / "post_h2c_chain_closure_report.json").write_text(
    json.dumps(closure, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = ["# POST-PHASE13 H2C-B2 — Execution Audit", "", "- **Status: PASS**",
      f"- run id: `{audit['run_id']}`", "",
      "## Authorization", "",
      f"- source: `{audit['authorization']['source']}`",
      f"- H2C-B2: **{audit['authorization']['h2c_b2_supervisor_authorization']}**", "",
      "## Bindings", "", "| role | SHA-256 |", "|---|---|"]
for k, v in audit["bindings"].items():
    md.append(f"| {k} | `{v}` |")
md += ["", "## Downstream configuration", "",
       f"- architectures: {', '.join(audit['downstream_configuration']['segmentation_checkpoints'])}",
       f"- proposal policy: threshold 0.10 / margin 0.20 / top_k 5 / NMS 0.30",
       f"- fusion: `{audit['downstream_configuration']['fusion_variant']}`",
       f"- configurations: **{audit['downstream_configuration']['configurations']}**", "",
       "## Results per model", "",
       "| model | H2C | GLOBAL | Phase13 | H2A | Oracle | H2C−GLOBAL | H2C−P13 | H2C−H2A | retention |",
       "|---|---|---|---|---|---|---|---|---|---|"]
for k, v in per_model.items():
    md.append(f"| {k} | {v['h2c_predicted_macro_dice']:.6f} | {v['global_macro_dice']:.6f} | "
              f"{v['phase13_predicted_macro_dice']:.6f} | {v['h2a_predicted_macro_dice']:.6f} | "
              f"{v['oracle_macro_dice']:.6f} | {v['DELTA_H2C_GLOBAL_DICE']:+.6f} | "
              f"{v['DELTA_H2C_PHASE13_DICE']:+.6f} | {v['DELTA_H2C_H2A_DICE']:+.6f} | "
              f"{v['H2C_ORACLE_BENEFIT_RETENTION']:.6f} |")
md += ["", "## Counters", "", "| counter | value |", "|---|---|"]
for k, v in audit["counters"].items():
    md.append(f"| {k} | {v} |")
md += ["", "## Counter explanations", ""]
for k, v in audit["counter_explanations"].items():
    md.append(f"- **{k}**: {v}")
md += ["", f"**H2C outcome: `{audit['h2c_outcome']}`**", "",
       f"**Reporting defect scientific impact: {audit['reporting_defect_scientific_impact']}**", "",
       f"**Phase 14: {audit['phase14']}**", "",
       f"next_action: `{audit['next_action']}`", ""]
(A / "post_phase13_h2c_b2_execution_audit.md").write_text("\n".join(md), encoding="utf-8")

print("execution audit + closure written")
print("exec sha:", sha(A / "post_phase13_h2c_b2_execution_audit.json"))
print("closure sha:", sha(A / "post_h2c_chain_closure_report.json"))
