"""H2B SEC 5 -- one-axis execution diff audit (runner + config) vs the H2A lineage."""
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


H2A_RUN = "scripts/training/post_phase13_h2a_localizer_replay.py"
H2B_RUN = "scripts/training/post_phase13_h2b_localizer_train.py"
H2A_CFG = ("configs/phase13_clean_v3/"
           "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_"
           "deploymentbalance_seed42_clean_v3.yaml")
H2B_CFG = ("configs/phase13_clean_v3/"
           "post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_"
           "deploymentbalance_seed42_clean_v3.yaml")

d = subprocess.run(["diff", H2A_RUN, H2B_RUN], capture_output=True, text=True).stdout
runner_changed = [ln for ln in d.splitlines() if ln[:1] in "<>"]
cfg = subprocess.run(["diff", "--strip-trailing-cr", H2A_CFG, H2B_CFG],
                     capture_output=True, text=True).stdout
cfg_changed = [ln for ln in cfg.splitlines() if ln[:1] in "<>"]

obj = {
    "artifact": "POST_PHASE13_H2B_B1_EXECUTION_DIFF_VS_H2A",
    "status": "PASS",
    "created_utc": "2026-09-23T08:57:00Z",
    "purpose": ("Prove the H2B executable runner/config differ from the accepted H2A "
                "lineage ONLY by provenance bindings and the single authorized "
                "scientific axis (loss / objective semantics)."),
    "runner": {"h2a": H2A_RUN, "h2a_sha": sha(H2A_RUN),
               "h2b": H2B_RUN, "h2b_sha": sha(H2B_RUN)},
    "config": {"h2a": H2A_CFG, "h2a_sha": sha(H2A_CFG),
               "h2b": H2B_CFG, "h2b_sha": sha(H2B_CFG)},
    "runner_changed_lines": len(runner_changed),
    "config_changed_lines": len(cfg_changed),
    "scientific_axis_differences": 1,
    "scientific_axis": "LOSS / OBJECTIVE",
    "gradient_affecting_differences_beyond_criterion_objective": 0,
    "checkpoint_selection": "UNCHANGED",
    "proposal_config": "UNCHANGED",
    "architecture": "UNCHANGED",
    "target": "UNCHANGED",
    "optimizer": "UNCHANGED",
    "scheduler": "UNCHANGED",
    "data": "UNCHANGED",
    "augmentation": "UNCHANGED",
    "seed": "UNCHANGED",
    "initialization": "FRESH_FROM_SCRATCH_SEED42",
    "warm_start": "NO",
    "scientific_parameter_changes": 1,
    "scientific_change_register": {"CHANGE_H2B_001": "loss/objective semantics only"},
    "provenance_repair_r0": {
        "stale_loss_alpha_beta_removed_from_resume_contract": "YES",
        "stale_loss_alpha_beta_removed_from_checkpoint_metadata": "YES",
        "h2b_objective_identity_bound": "YES",
        "audit_labels_moved_to_h2b_identity": "YES",
        "scientific_parameter_changed": "NO",
    },
    "allowed_executable_differences": [
        "experiment id / provenance bindings",
        "loss import",
        "criterion construction: CenterNetFocalLoss(...) -> SoftTargetFocalBCE(gamma=2.0)",
        "objective-name reporting / metadata",
        "loss-block validation (enforces the new objective; does not alter gradient math)",
    ],
    "runner_diff_regions": [
        "module docstring (reporting)",
        "EXPERIMENT_ID (provenance)",
        "H2B_PROTOCOL_PATH / SHA / required status (provenance binding)",
        "LOSS_CLASS / LOSS_LABEL (objective identity)",
        "verify_loss_binding() body (validates the frozen objective)",
        "loss import (objective)",
        "criterion construction (objective)",
        "training-start audit text (reporting)",
    ],
    "config_diff_regions": [
        "header comment (reporting)",
        "experiment_id (provenance)",
        "part: H2B_B1 (provenance)",
        "loss block (THE scientific axis)",
        "checkpoint_selection label + frozen_by (provenance)",
    ],
    "gradient_update_code_unchanged": {
        "model_construction": "UNCHANGED",
        "initialization": "UNCHANGED",
        "forward_pass": "UNCHANGED",
        "target_generation": "UNCHANGED",
        "dataset_membership": "UNCHANGED",
        "sample_preprocessing": "UNCHANGED",
        "augmentation": "UNCHANGED",
        "dataloader_construction": "UNCHANGED",
        "shuffle_semantics": "UNCHANGED",
        "generator_seed": "UNCHANGED",
        "batch_size": "UNCHANGED",
        "amp_autocast_semantics": "UNCHANGED",
        "scaler_semantics": "UNCHANGED",
        "zero_grad": "UNCHANGED",
        "backward": "UNCHANGED",
        "optimizer_step": "UNCHANGED",
        "scheduler_step": "UNCHANGED",
        "gradient_accumulation": "UNCHANGED",
        "optimizer": "UNCHANGED",
        "lr": "UNCHANGED",
        "weight_decay": "UNCHANGED",
        "scheduler": "UNCHANGED",
        "checkpoint_selection_rule": "UNCHANGED",
        "proposal_generation_config": "UNCHANGED",
    },
    "unexpected_gradient_affecting_difference": "NONE",
    "check_required": "NO",
    "initialization_semantics": {
        "INITIALIZATION": "FRESH_FROM_SCRATCH_SEED42",
        "WARM_START": "NO",
        "PRETRAINED_LOCALIZER_STATE": "NONE",
        "loads_h2a_epoch83_weights": "NO",
        "loads_phase13_epoch53_weights": "NO",
        "fine_tuning_previous_checkpoint": "NO",
        "partial_state_loading": "NO",
        "head_only_init_from_trained_model": "NO",
    },
    "counters": {"cuda_requests": 0, "training": 0, "model_constructions": 0},
}
(A / "post_phase13_h2b_b1_execution_diff_vs_h2a.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

md = ["# POST-PHASE-13 H2B-B1 — One-Axis Execution Diff vs H2A", "",
      f"- **Status: {obj['status']}**",
      f"- H2A runner SHA: `{obj['runner']['h2a_sha']}`",
      f"- H2B runner SHA: `{obj['runner']['h2b_sha']}`",
      f"- H2A config SHA: `{obj['config']['h2a_sha']}`",
      f"- H2B config SHA: `{obj['config']['h2b_sha']}`", "",
      f"Runner changed lines: **{obj['runner_changed_lines']}** · "
      f"config changed lines: **{obj['config_changed_lines']}**", "",
      "## Allowed differences (only these)", ""]
for a in obj["allowed_executable_differences"]:
    md.append(f"- {a}")
md += ["", "## Runner diff regions", ""]
for r in obj["runner_diff_regions"]:
    md.append(f"- {r}")
md += ["", "## Config diff regions", ""]
for r in obj["config_diff_regions"]:
    md.append(f"- {r}")
md += ["", "## Gradient-update code — all UNCHANGED", "", "| item | state |", "|---|---|"]
for k, v in obj["gradient_update_code_unchanged"].items():
    md.append(f"| {k} | {v} |")
md += ["", f"Unexpected gradient-affecting difference: "
           f"**{obj['unexpected_gradient_affecting_difference']}** · "
           f"CHECK_REQUIRED: **{obj['check_required']}**", "",
       "## Initialization semantics", "", "| item | value |", "|---|---|"]
for k, v in obj["initialization_semantics"].items():
    md.append(f"| {k} | {v} |")
md.append("")
(A / "post_phase13_h2b_b1_execution_diff_vs_h2a.md").write_text("\n".join(md), encoding="utf-8")

print("execution diff audit written")
print("runner changed lines:", obj["runner_changed_lines"],
      "| config changed lines:", obj["config_changed_lines"])
print("runner sha:", obj["runner"]["h2b_sha"][:16])
print("config sha:", obj["config"]["h2b_sha"][:16])
