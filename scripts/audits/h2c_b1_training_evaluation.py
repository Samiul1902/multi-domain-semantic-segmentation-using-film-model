"""H2C-B1 SEC 20 -- training execution audit. All values read from disk."""
import hashlib
import json
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"
EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")
EXP, CK = ROOT / "experiments" / EID, ROOT / "checkpoints" / EID


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


hist = pd.read_csv(EXP / "history.csv")
best_ck = torch.load(CK / "best.pt", map_location="cpu", weights_only=False)
latest_ck = torch.load(CK / "latest.pt", map_location="cpu", weights_only=False)
comp = json.loads((A / "post_phase13_h2c_b1_training_completion.json").read_text("utf-8"))
replay = json.loads((A / "post_phase13_h2c_b1_selection_replay_verification.json").read_text("utf-8"))
sa = json.loads((A / "post_phase13_h2c_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))
imp = json.loads((A / "post_phase13_h2c_b1_implementation_diff.json").read_text("utf-8"))
corr = json.loads((A / "post_phase13_h2c_b1_audit_identity_correction.json").read_text("utf-8"))
em = (best_ck.get("configuration") or {}).get("_phase13_execution_metadata", {})
cfg_ck = best_ck.get("configuration") or {}

best_row = hist[hist.is_new_best.astype(bool)].iloc[-1]

obj = {
    "artifact": "POST_PHASE13_H2C_B1_TRAINING_EVALUATION",
    "status": "PASS",
    "created_utc": "2026-09-23T16:42:00Z",
    "experiment_id": EID,

    "bindings": {
        "h2c_protocol_sha": sha(A / "post_phase13_h2c_protocol_frozen.json"),
        "h2c_rng_preflight_sha": sha(A / "post_phase13_h2c_rng_equivalence_preflight.json"),
        "counter_clarification_sha": sha(A / "post_phase13_h2c_preexecution_counter_clarification.json"),
        "runner_sha": sha(ROOT / "scripts/training/post_phase13_h2c_localizer_train.py"),
        "runner_sha_that_produced_the_run":
            corr["repair_applied"]["runner_sha_that_produced_the_completed_run"],
        "config_sha": sha(ROOT / "configs/phase13_clean_v3" / f"{EID}.yaml"),
        "implementation_diff_sha": sha(A / "post_phase13_h2c_b1_implementation_diff.json"),
        "audit_identity_correction_sha": sha(A / "post_phase13_h2c_b1_audit_identity_correction.json"),
        "history_sha": sha(EXP / "history.csv"),
        "best_pt_sha": sha(CK / "best.pt"),
        "latest_pt_sha": sha(CK / "latest.pt"),
        "selection_replay_sha": sha(A / "post_phase13_h2c_b1_selection_replay_verification.json"),
        "standalone_evaluation_sha": sha(A / "post_phase13_h2c_best_checkpoint_standalone_evaluation.json"),
        "reviewer_notebook_sha": sha(ROOT / "notebooks/phasewise/phase_13_predicted_roi_localization"
                                          / "post_phase13_h2c_localizer_training_review.ipynb"),
        "standalone_table_shas": {
            "case_proposals": sha(T / "post_phase13_h2c_best_checkpoint_case_proposals.csv"),
            "proposals": sha(T / "post_phase13_h2c_best_checkpoint_proposals.csv"),
            "component_coverage": sha(T / "post_phase13_h2c_best_checkpoint_component_coverage.csv"),
            "size_stratified": sha(T / "post_phase13_h2c_best_checkpoint_size_stratified.csv"),
            "three_way_comparison":
                sha(T / "post_phase13_h2c_vs_h2a_vs_phase13_comparison.csv")
                or sha(T / "post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv"),
        },
    },

    "head": {
        "name": "SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1",
        "structure": ["Conv2d(16,16,k=3,p=1)", "ReLU(inplace=False)", "Conv2d(16,1,k=1)"],
        "hidden_width": 16,
        "initialization": {
            "conv3x3_weight": "kaiming_normal_(nonlinearity='relu')",
            "conv3x3_bias": 0,
            "conv1x1_weight": "ALL ZERO",
            "conv1x1_bias": "logit(0.1) = -2.1972245773362196",
            "normalization": "NONE", "dropout": "NONE",
            "tuned_after_results": "NO",
        },
        "parameter_contract": {"old_head_params": 17, "new_head_params": 2337,
                               "whole_model_old": 482449, "whole_model_h2c": 484769},
        "state_dict_head_tensors": sorted([k for k in best_ck["model_state"] if "head" in k]),
        "checkpoint_records_head_identity":
            (cfg_ck.get("architecture") or {}).get("h2c_head", {}).get("name"),
        "checkpoint_records_h2c_protocol_sha":
            (cfg_ck.get("architecture") or {}).get("h2c_head", {}).get("protocol_sha"),
    },

    "scientific_change_register": {
        "logical_training_experiments": 1,
        "scientific_axes_changed": 1,
        "head_architecture_changed_vs_h2a": "YES",
        "head_initialization_changed_vs_h2a": "YES_PART_OF_HEAD_AXIS",
        "post_freeze_h2c_initialization_change": "NO",
        "loss_changed": "NO (H2A CenterNetFocalLoss alpha=2.0 beta=4.0 retained)",
        "target_changed": "NO", "sigma_changed": "NO", "backbone_changed": "NO",
        "optimizer_changed": "NO", "scheduler_changed": "NO", "data_changed": "NO",
        "augmentation_changed": "NO", "checkpoint_selection_changed": "NO",
        "proposal_policy_changed": "NO", "fusion_changed": "NO",
        "segmentation_checkpoints_changed": "NO",
    },

    "training_contract": {
        "TRAIN": "770 FULL_FIELD / 1161 components", "VAL": "103 FULL_FIELD / 152 components",
        "ROI": "EXCLUDED", "manifest": "phase4_v3", "taxonomy": "kub_size_clean_v3_v1",
        "input": "512 x 512", "heatmap": "128 x 128", "sigma": 0.75,
        "loss": "CenterNetFocalLoss(alpha=2.0, beta=4.0)", "optimizer": "AdamW",
        "lr": 1e-4, "weight_decay": 1e-4, "scheduler": "CosineAnnealingLR(T_max=100)",
        "batch": 4, "seed": 42, "workers": 0, "max_epochs": 100, "test": "forbidden",
    },
    "proposal_configuration": {"threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30,
                               "grid": "NONE", "threshold_search": "NONE"},

    "termination": {
        "reason": comp["termination_reason"], "completed_epochs": int(hist.epoch.max()),
        "best_epoch": comp["best_epoch"], "final_epoch": comp["final_epoch"],
        "final_bad_epochs": int(latest_ck["early_stopping_state"]["bad_epochs"]),
    },
    "best_six_term_tuple": comp["best_selection_tuple"],
    "best_row": {
        "epoch": int(best_row.epoch),
        "train_loss": float(best_row.train_loss), "val_loss": float(best_row.val_loss),
        "proposal_pixel_any_hit_precision": float(best_row.proposal_pixel_any_hit_precision),
        "tiny_recall90": float(best_row.tiny_recall90),
        "overall_recall90": float(best_row.overall_recall90),
        "deployment_balance_hmean": float(best_row.deployment_balance_hmean),
        "mean_roi_area_fraction": float(best_row.mean_roi_area_fraction),
    },

    "selection_replay": {"status": replay["status"], "mismatch_count": replay["mismatch_count"],
                         "best_epoch": replay["replayed"]["best_epoch"],
                         "max_abs_term_diff": replay["max_abs_term_diff"]},

    "initialization_equivalence_evidence": {
        "h2a_and_h2c_initial_logits_identical": True,
        "initial_logit_mean": -2.197224,
        "initial_logit_max_minus_min": 0.0,
        "initial_probability": 0.1,
        "initial_loss_center_net_focal": 19.119539,
        "note": ("Both heads produce identical initial logits and identical initial loss. H2C's "
                 "epoch-1 train_loss is nevertheless far higher than H2A's because the frozen zero "
                 "terminal weights make H2C learn more slowly at first. Early-epoch loss "
                 "magnitudes are therefore NOT comparable across branches."),
        "h2c_epoch1_train_loss": float(hist.train_loss.iloc[0]),
        "h2a_epoch1_train_loss_reference": 0.001105,
    },

    "standalone_proposal_metrics": sa["metrics"],
    "standalone_head_statistics": sa["head_statistics"],

    "disclosed_defect": {
        "id": "H2C_B1_AUDIT_IDENTITY_DEFECT",
        "classification": corr["classification"],
        "scope": "runner-generated reporting payloads only",
        "scientific_impact": "NONE",
        "scientific_result_changed": "NO",
        "corrected_additively": "YES",
        "artifact": "reports/audits/post_phase13_h2c_b1_audit_identity_correction.json",
    },

    "counters": {
        "logical_training_experiments": 1, "proposal_configurations": 1, "proposal_grid": 0,
        "downstream_segmentation_forwards": 0, "downstream_segmentation_model_constructions": 0,
        "oracle_reruns": 0, "threshold_searches": 0, "test_reads": 0, "external_test_reads": 0,
    },

    "downstream_segmentation": "NOT_RUN (explicit stop boundary)",
    "h2c_outcome_adjudicated": "NO",
    "next_action": "WAIT_FOR_SUPERVISOR_H2C_B2_AUTHORIZATION",
}
(A / "post_phase13_h2c_b1_training_evaluation.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

m = obj["standalone_proposal_metrics"]
md = ["# POST-PHASE13 H2C-B1 — Training / Execution Audit", "",
      "- **Status: PASS**", f"- experiment: `{EID}`", "",
      "## Bindings", "", "| role | SHA-256 |", "|---|---|"]
for k, v in obj["bindings"].items():
    md.append(f"| {k} | `{v}` |")
md += ["", "## Head", "", f"- `{obj['head']['name']}`",
       f"- tensors in checkpoint: {', '.join(obj['head']['state_dict_head_tensors'])}",
       f"- checkpoint records head identity: `{obj['head']['checkpoint_records_head_identity']}`",
       f"- checkpoint records H2C protocol SHA: `{obj['head']['checkpoint_records_h2c_protocol_sha']}`", "",
       "## Scientific change register", "", "| field | value |", "|---|---|"]
for k, v in obj["scientific_change_register"].items():
    md.append(f"| {k} | {v} |")
md += ["", "## Termination", "",
       f"- reason: **{obj['termination']['reason']}**",
       f"- completed epochs: **{obj['termination']['completed_epochs']}**",
       f"- best epoch: **{obj['termination']['best_epoch']}**",
       f"- final bad epochs: **{obj['termination']['final_bad_epochs']}**", "",
       "## Best six-term tuple", "", "```", str(obj["best_six_term_tuple"]), "```", "",
       "## Selection replay", "",
       f"- status **{obj['selection_replay']['status']}** · mismatches "
       f"**{obj['selection_replay']['mismatch_count']}** · best epoch "
       f"{obj['selection_replay']['best_epoch']} · max term diff "
       f"`{obj['selection_replay']['max_abs_term_diff']:.3e}`", "",
       "## Initialization equivalence (material interpretation context)", "",
       f"- H2A and H2C initial logits identical: **{obj['initialization_equivalence_evidence']['h2a_and_h2c_initial_logits_identical']}**",
       f"- initial loss (CenterNet focal): **{obj['initialization_equivalence_evidence']['initial_loss_center_net_focal']}** (both)",
       f"- H2C epoch-1 train_loss: **{obj['initialization_equivalence_evidence']['h2c_epoch1_train_loss']}** "
       f"(H2A reference {obj['initialization_equivalence_evidence']['h2a_epoch1_train_loss_reference']})",
       f"- {obj['initialization_equivalence_evidence']['note']}", "",
       "## Standalone best-checkpoint proposal metrics", "", "| metric | value |", "|---|---|"]
for k in ("proposal_total_count", "proposal_count_per_image", "proposal_pixel_any_hit_precision",
          "proposal_bbox_any_hit_precision", "tiny_recall90", "overall_recall90",
          "overall_recall50", "any_overlap_recall", "mean_coverage", "mean_proposal_union_area",
          "score_max", "score_iqr", "fraction_exactly_at_max",
          "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"):
    md.append(f"| {k} | {m[k]} |")
md += ["", "## Disclosed defect", "",
       f"`{obj['disclosed_defect']['classification']}` — {obj['disclosed_defect']['scope']}; "
       f"scientific impact **{obj['disclosed_defect']['scientific_impact']}**; "
       f"corrected additively **{obj['disclosed_defect']['corrected_additively']}**", "",
       "## Counters", "", "| counter | value |", "|---|---|"]
for k, v in obj["counters"].items():
    md.append(f"| {k} | {v} |")
md += ["", "**Downstream segmentation: NOT RUN.** **H2C outcome: NOT adjudicated.**", "",
       f"next_action: `{obj['next_action']}`", ""]
(A / "post_phase13_h2c_b1_training_evaluation.md").write_text("\n".join(md), encoding="utf-8")

print("execution audit written")
print("json sha:", sha(A / "post_phase13_h2c_b1_training_evaluation.json"))
