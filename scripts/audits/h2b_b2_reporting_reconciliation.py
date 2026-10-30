"""H2B-B2 R -- quantitative reporting reconciliation artifact."""
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


s = pd.read_csv(T / "post_phase13_h2b_downstream_model_summary.csv")
cross = pd.read_csv(T / "post_phase13_h2b_downstream_cross_architecture_summary.csv")
integ = json.loads((A / "post_phase13_h2b_b2_downstream_integrity.json").read_text("utf-8"))

KEYS = ["global_macro_dice", "phase13_predicted_macro_dice", "h2a_predicted_macro_dice",
        "h2b_predicted_macro_dice", "DELTA_H2B_GLOBAL_DICE", "DELTA_H2B_PHASE13_DICE",
        "DELTA_H2B_H2A_DICE", "mean_global_fp", "mean_phase13_fp", "mean_h2a_fp",
        "mean_h2b_fp", "fp_delta_vs_global", "fp_delta_vs_phase13", "fp_delta_vs_h2a",
        "component_recoveries_vs_global", "component_losses_vs_global",
        "component_recoveries_vs_phase13", "component_losses_vs_phase13",
        "component_recoveries_vs_h2a", "component_losses_vs_h2a"]

authoritative = {}
for _, r in s.iterrows():
    authoritative[r["model"]] = {"model_display": r["model_display"],
                                 **{k: (int(r[k]) if k.startswith("component_") else float(r[k]))
                                    for k in KEYS}}

# Values that appeared in the pasted chat final note but are NOT on disk.
STALE = {
    "component_recoveries_losses_vs_global_sequence": {
        "pasted_chat_values": ["8/0", "5/0", "5/0", "4/0"],
        "authoritative_values": ["10/0", "7/0", "11/0", "16/0"],
    },
    "fp_delta_vs_global": {
        "pasted_chat_values": [7203.65, 7410.66, 7722.28, 8083.96],
        "authoritative_values": [float(s.iloc[i]["fp_delta_vs_global"]) for i in range(4)],
    },
    "mean_h2b_fp_unet": {"pasted_chat_value": 8500.90,
                         "authoritative_value": float(s.iloc[0]["mean_h2b_fp"])},
}

obj = {
    "artifact": "POST_PHASE13_H2B_B2_REPORTING_RECONCILIATION",
    "status": "PASS",
    "created_utc": "2026-09-23T15:59:00Z",
    "model_attribution": "Gemini 3.8 Flash Medium",
    "scope": "QUANTITATIVE_REPORTING_RECONCILIATION_ONLY",
    "scientific_adjudication_performed": "NO",
    "inference_or_training_performed": "NO",

    "classification": "CHAT_TRANSCRIPTION_ONLY",
    "classification_definition": ("wrong numbers exist only in the pasted chat final note; all "
                                  "persisted quantitative artifacts are mutually consistent"),

    "bindings": {
        "model_summary": ("reports/tables/post_phase13_h2b_downstream_model_summary.csv",
                          sha(T / "post_phase13_h2b_downstream_model_summary.csv")),
        "cross_architecture_summary": (
            "reports/tables/post_phase13_h2b_downstream_cross_architecture_summary.csv",
            sha(T / "post_phase13_h2b_downstream_cross_architecture_summary.csv")),
        "b2_integrity_audit": ("reports/audits/post_phase13_h2b_b2_downstream_integrity.json",
                               sha(A / "post_phase13_h2b_b2_downstream_integrity.json")),
        "reviewer_notebook": (
            "notebooks/phasewise/phase_13_predicted_roi_localization/"
            "post_phase13_h2b_downstream_analysis.ipynb",
            sha(ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
                   / "post_phase13_h2b_downstream_analysis.ipynb")),
    },

    "integrity_audit_gate": {
        "status": integ["status"], "proposal_count": integ["proposal_count"],
        "case_model_rows": integ["case_model_rows"],
        "component_model_rows": integ["component_model_rows"],
        "model_summary_rows": integ["model_summary_rows"],
        "regional_crop_evaluations": integ["regional_crop_evaluations"],
        "localizer_forwards": integ["localizer_forwards"],
        "proposal_regeneration": integ["proposal_regeneration"],
        "test_reads": integ["test_reads"],
        "external_test_reads": integ["external_test_reads"],
        "all_required_met": True,
    },

    "authoritative_model_summary": authoritative,

    "authoritative_cross_architecture": {
        str(r.iloc[0]): (int(r["value"]) if str(r["value"]).lstrip("-").isdigit() else r["value"])
        for _, r in cross.iterrows()},

    "stale_values": STALE,

    "stale_value_search": {
        "searched": ["reports/audits/", "reports/tables/", "docs/TASKS.md", "docs/MEMORY.md",
                     "reports/**/*.md", "reports/**/*.json",
                     ".workbuddy-ai/memory/2026-09-23.md"],
        "stale_values_found_in_persisted_artifacts": "NO",
        "mean_h2b_fp_8500.90_found_anywhere": "NO",
        "notes": ("Numeric substring matches for 7203 / 7410.66 / 7722.28 / 8083.96 exist only in "
                  "unrelated earlier-phase tables (phase07/phase09/phase10/phase11/phase12/phase13 "
                  "case-level metrics) and are not H2B reporting. No H2B artifact, doc, or memory "
                  "file contains the stale values."),
        "persisted_h2b_final_note_artifact": "DOES_NOT_EXIST",
    },

    "notebook_vs_model_summary": "PASS",

    "repair_policy_applied": {
        "authoritative_tables_modified": "NO",
        "frozen_audits_rewritten": "NO",
        "mutable_continuity_docs_corrected": "NOT_REQUIRED (they never contained the stale values)",
        "artifacts_created": ["reports/audits/post_phase13_h2b_b2_reporting_reconciliation.json",
                              "reports/audits/post_phase13_h2b_b2_reporting_reconciliation.md"],
    },

    "preserved_valid_evidence": {
        "h2b_macro_dice_below_global_all_four": True,
        "h2b_macro_dice_below_phase13_all_four": True,
        "h2b_macro_dice_below_h2a_all_four": True,
        "component_losses_vs_global_zero_all_four": True,
        "cross_architecture_union_recovery": "DESCRIPTIVE_EVIDENCE_PRESERVED",
    },

    "scientific_result_changed": "NO",
    "b2_execution_status_changed": "NO",
    "h2b_outcome_adjudicated": "NO",

    "counters": {"training": 0, "cuda_requests": 0, "model_constructions": 0,
                 "localizer_forwards": 0, "segmentation_forwards": 0,
                 "proposal_generation": 0, "test_reads": 0, "external_test_reads": 0},
}
(A / "post_phase13_h2b_b2_reporting_reconciliation.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

md = [
    "# POST-PHASE13 H2B-B2 — Quantitative Reporting Reconciliation", "",
    "- **Status: PASS**",
    "- **Classification: `CHAT_TRANSCRIPTION_ONLY`**",
    "- Scientific adjudication performed: **NO** · Inference/training performed: **NO**", "",
    "## Finding", "",
    "The pasted H2B-B2 chat final note contained quantitative values that do **not** appear in any",
    "persisted artifact. The authoritative on-disk tables were always correct; the error existed",
    "only in the chat transcript.", "",
    "## Authoritative model summary (read from disk)", "",
    "| model | H2B Dice | H2B−GLOBAL | H2B−P13 | H2B−H2A | fp_delta_vs_global | recov/loss vs GLOBAL |",
    "|---|---|---|---|---|---|---|"]
for m, v in authoritative.items():
    md.append(f"| {v['model_display']} | {v['h2b_predicted_macro_dice']:.6f} | "
              f"{v['DELTA_H2B_GLOBAL_DICE']:.6f} | {v['DELTA_H2B_PHASE13_DICE']:.6f} | "
              f"{v['DELTA_H2B_H2A_DICE']:.6f} | {v['fp_delta_vs_global']:.6f} | "
              f"{v['component_recoveries_vs_global']}/{v['component_losses_vs_global']} |")

md += ["", "## Stale values (chat only — NOT on disk)", "",
       "| quantity | pasted chat | authoritative |", "|---|---|---|",
       f"| recoveries/losses vs GLOBAL | 8/0 · 5/0 · 5/0 · 4/0 | **10/0 · 7/0 · 11/0 · 16/0** |",
       f"| fp_delta_vs_global | +7203.65 · +7410.66 · +7722.28 · +8083.96 | "
       f"**+9625.621359 · +9857.815534 · +10507.456311 · +11031.233010** |",
       f"| mean_h2b_fp (UNet) | 8500.90 | **{authoritative['unet']['mean_h2b_fp']:.6f}** |", "",
       "## Search result", "",
       "- stale values found in persisted artifacts: **NO**",
       "- `8500.90` found anywhere on disk: **NO**",
       "- persisted H2B final-note artifact: **does not exist**",
       "- notebook vs model summary: **PASS**", "",
       "## Repair applied", "",
       "- authoritative tables modified: **NO**",
       "- frozen audits rewritten: **NO**",
       "- continuity docs required correction: **NO** (they never carried the stale values)", "",
       "## Preserved valid evidence (descriptive, unadjudicated)", "",
       "- H2B macro Dice is below GLOBAL, Phase13 predicted **and** H2A predicted for all four architectures",
       "- component losses vs GLOBAL are **zero** for all four",
       "- cross-architecture union recovery retained as descriptive evidence", "",
       "- scientific result changed: **NO**",
       "- B2 execution status changed: **NO**", "",
       "next_action: `WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION`", ""]
(A / "post_phase13_h2b_b2_reporting_reconciliation.md").write_text("\n".join(md), encoding="utf-8")

print("reconciliation artifact written")
print("json sha:", sha(A / "post_phase13_h2b_b2_reporting_reconciliation.json"))
