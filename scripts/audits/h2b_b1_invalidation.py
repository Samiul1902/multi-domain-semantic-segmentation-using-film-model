"""H2B-B1 R0 -- write the pre-fix execution invalidation artifact."""
import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"
ARCH = ROOT / "reports" / "superseded" / "post_phase13_h2b_b1_invalidated_pre_fix_attempt_20260923T0936Z"

EID = ("post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
       "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3")


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


obj = {
    "artifact": "POST_PHASE13_H2B_B1_PRE_FIX_EXECUTION_INVALIDATION",
    "status": "INVALIDATED_AND_PRESERVED",
    "created_utc": "2026-09-23T09:36:00Z",
    "classification":
        "INVALIDATED_EXECUTION_ATTEMPT__NON_SCIENTIFIC_CODE_PROVENANCE_DEFECT",
    "experiment_id": EID,
    "reason_for_invalidation":
        "STALE_OBJECTIVE_IDENTITY_METADATA_IN_CHECKPOINT_AND_RESUME_CONTRACT",

    "defect": {
        "summary": ("The H2B runner executed the CORRECT SoftTargetFocalBCE objective, but its "
                    "resume-identity contract, checkpoint metadata and start audit still carried "
                    "the stale Phase-13 CenterNet objective fields loss_alpha=2.0 / loss_beta=4.0, "
                    "and declared protocol_identity 'R2 + R2A_LOSS_BINDING' as the ACTIVE identity."),
        "material": True,
        "why_material": ("A checkpoint/resume contract that asserts alpha=2.0 / beta=4.0 as the "
                         "active objective would make a resume, an audit reader or a downstream "
                         "consumer believe the Phase-13 CenterNet objective was the executed "
                         "objective. That is a provenance contradiction even though the executed "
                         "mathematics was correct."),
        "observed_in_checkpoint": {
            "path": f"configuration/_phase13_execution_metadata",
            "loss_alpha": 2.0,
            "loss_beta": 4.0,
        },
        "observed_in_runner": {
            "resume_identity_extended_identity": "loss_alpha=2.0, loss_beta=4.0",
            "checkpoint_metadata_write": "loss_alpha=2.0, loss_beta=4.0, loss_dice_weight=0.0",
            "start_audit_protocol_identity": "R2 + R2A_LOSS_BINDING",
            "completion_audit_protocol_identity": "R2 + R2A_LOSS_BINDING",
            "start_audit_artifact_label": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_START",
            "completion_audit_artifact_label": "PHASE13_CLEAN_V3_LOCALIZER_TRAINING_COMPLETION",
            "scientific_changes": 0,
        },
    },

    "interrupted_attempt_state": {
        "completed_epochs": 4,
        "epochs": [1, 2, 3, 4],
        "history_sha": sha(ARCH / "experiments" / "history.csv"),
        "latest_pt_sha": sha(ARCH / "checkpoints" / "latest.pt"),
        "best_pt_sha": sha(ARCH / "checkpoints" / "best.pt"),
        "runner_sha_at_attempt": "2e9c1faf0a6a2e823fcd0dec4a47401fa979f43b574152068aee55d76bda542d",
        "config_sha_at_attempt": "2ceaa71d614475fed54248c353e247848f41df3ace423e3c36aba63d59431152",
        "training_start_audit_sha": sha(ARCH / "audits" / "post_phase13_h2b_b1_training_start.json"),
        "training_log_sha": sha(ARCH / "audits" / "training.log"),
    },

    "preservation": {
        "archive_location":
            "reports/superseded/post_phase13_h2b_b1_invalidated_pre_fix_attempt_20260923T0936Z/",
        "archived_files": [
            "experiments/history.csv",
            "experiments/.experiment.lock",
            "checkpoints/latest.pt",
            "checkpoints/best.pt",
            "audits/post_phase13_h2b_b1_training_start.json",
            "audits/post_phase13_h2b_b1_training_start.md",
            "audits/training.log",
        ],
        "silently_deleted": "NO",
    },

    "promotion": {
        "scientific_measurements_promoted": "NO",
        "checkpoint_promoted": "NO",
        "history_promoted": "NO",
        "h2b_hypothesis_changed": "NO",
        "h2b_protocol_changed": "NO",
    },

    "counts": {
        "logical_scientific_experiment_count": 1,
        "execution_attempt_count": 2,
        "invalid_attempt_counts_as_scientific_experiment": "NO",
        "test_reads": 0,
        "external_test_reads": 0,
    },

    "repair_applied": {
        "stale_loss_alpha_beta_removed_from_resume_contract": "YES",
        "stale_loss_alpha_beta_removed_from_checkpoint_metadata": "YES",
        "h2b_objective_identity_bound_in_resume_gate": "YES",
        "h2b_objective_identity_bound_in_checkpoint_metadata": "YES",
        "audit_artifact_labels_moved_to_h2b_identity": "YES",
        "scientific_changes_corrected_to": 1,
        "zero_denominator_rule_wording_reconciled": "YES",
        "scientific_parameter_changed": "NO",
    },
}
(A / "post_phase13_h2b_b1_pre_fix_execution_invalidation.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

md = [
    "# H2B-B1 — Pre-Fix Execution Invalidation", "",
    "- **Status: INVALIDATED_AND_PRESERVED**",
    "- **Classification:** `INVALIDATED_EXECUTION_ATTEMPT__NON_SCIENTIFIC_CODE_PROVENANCE_DEFECT`",
    f"- **Experiment id:** `{EID}`",
    "- **Reason:** `STALE_OBJECTIVE_IDENTITY_METADATA_IN_CHECKPOINT_AND_RESUME_CONTRACT`", "",
    "## What was wrong", "",
    "The H2B runner executed the **correct** `SoftTargetFocalBCE(gamma=2.0)` objective, but its",
    "resume-identity contract, checkpoint metadata and start/completion audits still carried the",
    "stale Phase-13 CenterNet fields `loss_alpha=2.0` / `loss_beta=4.0` and declared",
    "`protocol_identity = R2 + R2A_LOSS_BINDING` as the **active** identity.", "",
    "Observed in the checkpoint: `configuration/_phase13_execution_metadata.loss_alpha = 2.0`,",
    "`loss_beta = 4.0`.", "",
    "## Interrupted attempt", "",
    "| field | value |", "|---|---|",
    f"| completed epochs | **4** (1, 2, 3, 4) |",
    f"| history SHA | `{obj['interrupted_attempt_state']['history_sha']}` |",
    f"| latest.pt SHA | `{obj['interrupted_attempt_state']['latest_pt_sha']}` |",
    f"| best.pt SHA | `{obj['interrupted_attempt_state']['best_pt_sha']}` |",
    f"| runner SHA (at attempt) | `{obj['interrupted_attempt_state']['runner_sha_at_attempt']}` |",
    f"| config SHA (at attempt) | `{obj['interrupted_attempt_state']['config_sha_at_attempt']}` |",
    "", "## Preservation", "",
    "Archived (not deleted) at",
    f"`{obj['preservation']['archive_location']}`:", ""]
for f in obj["preservation"]["archived_files"]:
    md.append(f"- `{f}`")
md += ["", "## Promotion", "",
       "- scientific measurements promoted: **NO**",
       "- checkpoint promoted: **NO**",
       "- history promoted: **NO**",
       "- H2B hypothesis changed: **NO**",
       "- H2B protocol changed: **NO**", "",
       "The invalid pre-fix execution is **NOT** a second scientific experiment.",
       "`logical_scientific_experiment_count = 1`; `execution_attempt_count = 2`.", "",
       "**TEST reads: 0 · external TEST reads: 0**", ""]
(A / "post_phase13_h2b_b1_pre_fix_execution_invalidation.md").write_text(
    "\n".join(md), encoding="utf-8")

print("invalidation artifact written")
print("json sha:", sha(A / "post_phase13_h2b_b1_pre_fix_execution_invalidation.json"))
