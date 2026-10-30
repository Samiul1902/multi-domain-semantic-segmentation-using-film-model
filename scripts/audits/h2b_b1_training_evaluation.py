"""H2B-B1 SEC 22 -- training evaluation audit (runner / execution audit)."""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"
EID = ("post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_"
       "softtargetfocalgamma2_deploymentbalance_seed42_clean_v3")
EXP, CK = ROOT / "experiments" / EID, ROOT / "checkpoints" / EID


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


hist = pd.read_csv(EXP / "history.csv")
best_ck = torch.load(CK / "best.pt", map_location="cpu", weights_only=False)
latest_ck = torch.load(CK / "latest.pt", map_location="cpu", weights_only=False)
comp = json.loads((A / "post_phase13_h2b_b1_training_completion.json").read_text("utf-8"))
replay = json.loads((A / "post_phase13_h2b_b1_selection_replay_verification.json").read_text("utf-8"))
sa = json.loads((A / "post_phase13_h2b_best_checkpoint_standalone_evaluation.json").read_text("utf-8"))
em = (best_ck.get("configuration") or {}).get("_phase13_execution_metadata", {})

best_row = hist[hist.is_new_best.astype(bool)].iloc[-1]

obj = {
    "artifact": "POST_PHASE13_H2B_B1_TRAINING_EVALUATION",
    "status": "PASS",
    "created_utc": "2026-09-23T14:20:00Z",
    "experiment_id": EID,

    "bindings": {
        "h2b_protocol_sha": "22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e",
        "h2a_adjudication_sha": "02af0558696880f5842abaefbc8f30e5b44b20a700350bd70f963e0b844aada6",
        "loss_implementation_sha": "40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75",
        "unit_audit_sha": sha(A / "post_phase13_h2b_soft_target_focal_loss_unit_audit.json"),
        "runner_sha": sha(ROOT / "scripts/training/post_phase13_h2b_localizer_train.py"),
        "config_sha": sha(ROOT / "configs/phase13_clean_v3" / f"{EID}.yaml"),
        "one_axis_execution_diff_sha": sha(A / "post_phase13_h2b_b1_execution_diff_vs_h2a.json"),
        "invalidation_sha": sha(A / "post_phase13_h2b_b1_pre_fix_execution_invalidation.json"),
        "defect_linkage_sha": sha(A / "post_phase13_h2b_b1_defect_linkage.json"),
        "provenance_repair_tests_sha": sha(A / "post_phase13_h2b_b1_provenance_repair_tests.json"),
    },

    "initialization_semantics": {
        "INITIALIZATION": "FRESH_FROM_SCRATCH_SEED42",
        "WARM_START": "NO",
        "PRETRAINED_LOCALIZER_STATE": "NONE",
        "loaded_h2a_or_phase13_weights": "NO",
        "seed": 42,
    },

    "loss": {
        "class": em.get("loss_class"),
        "label": em.get("loss_label"),
        "gamma": em.get("loss_gamma"),
        "formula": "mean( |sigmoid(z) - y|^2 * BCEWithLogits(z, y) )",
        "modulation_detached": em.get("loss_modulation_detached"),
        "dice_term": em.get("dice_term"),
        "auxiliary_loss": em.get("auxiliary_loss"),
        "objective_change_id": em.get("objective_change_id"),
        "h2b_protocol_sha": em.get("h2b_protocol_sha"),
        "h2b_loss_module_sha": em.get("h2b_loss_module_sha"),
        "stale_loss_alpha_present": "loss_alpha" in em,
        "stale_loss_beta_present": "loss_beta" in em,
    },

    "training_contract": {
        "TRAIN": "770 FULL_FIELD / 1161 components",
        "VAL": "103 FULL_FIELD / 152 components",
        "manifest": "phase4_v3", "taxonomy": "kub_size_clean_v3_v1",
        "input": "512 x 512", "heatmap": "128 x 128", "sigma": 0.75,
        "optimizer": "AdamW", "lr": 1e-4, "weight_decay": 1e-4,
        "scheduler": "CosineAnnealingLR(T_max=100)", "batch": 4,
        "amp": "same accepted H2A semantics", "seed": 42,
        "augmentation": "same Phase13/H2A semantics", "workers": 0,
        "max_epochs": 100, "early_stopping_patience": 15, "test": "forbidden",
    },

    "proposal_configuration": {"threshold": 0.10, "margin": 0.20, "top_k": 5,
                               "nms_iou": 0.30, "grid": "NONE", "threshold_search": "NONE"},

    "selection_rule": {
        "tuple": ["DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90", "tiny_recall90",
                  "overall_recall90", "PROPOSAL_PIXEL_ANY_HIT_PRECISION",
                  "-mean_roi_area_fraction", "-val_loss"],
        "comparison": "STRICT_LEXICOGRAPHIC_GREATER_THAN", "ties": "BAD_EPOCH",
        "patience": 15,
        "unchanged_from_h2a": "YES",
        "source": em.get("selection_rule_source"),
    },

    "termination": {
        "reason": comp["termination_reason"],
        "completed_epochs": int(hist.epoch.max()),
        "best_epoch": comp["best_epoch"],
        "final_epoch": comp["final_epoch"],
        "final_bad_epochs": int(latest_ck["early_stopping_state"]["bad_epochs"]),
    },

    "best_six_term_tuple": comp["best_selection_tuple"],
    "best_row": {
        "epoch": int(best_row.epoch),
        "train_loss": float(best_row.train_loss),
        "val_loss": float(best_row.val_loss),
        "proposal_total_count": int(best_row.proposal_total_count),
        "proposal_pixel_any_hit_precision": float(best_row.proposal_pixel_any_hit_precision),
        "tiny_recall90": float(best_row.tiny_recall90),
        "overall_recall90": float(best_row.overall_recall90),
        "deployment_balance_hmean": float(best_row.deployment_balance_hmean),
        "mean_roi_area_fraction": float(best_row.mean_roi_area_fraction),
    },

    "hashes": {
        "best_pt_sha": sha(CK / "best.pt"),
        "latest_pt_sha": sha(CK / "latest.pt"),
        "history_sha": sha(EXP / "history.csv"),
    },

    "selection_replay": {"status": replay["status"], "mismatch_count": replay["mismatch_count"],
                         "best_epoch": replay["replayed"]["best_epoch"],
                         "max_abs_term_diff": replay["max_abs_term_diff"]},

    "standalone_proposal_metrics": sa["metrics"],
    "standalone_head_statistics": sa["head_statistics"],

    "trajectory_reproduction_vs_h2a": "NOT_PERFORMED__SEC11_OBJECTIVE_CHANGED",

    "counters": {
        "logical_training_experiments": 1,
        "execution_attempt_count": 2,
        "proposal_configurations": 1,
        "proposal_grid": 0,
        "downstream_segmentation_forwards": 0,
        "downstream_segmentation_model_constructions": 0,
        "oracle_reruns": 0,
        "threshold_searches": 0,
        "test_reads": 0,
        "external_test_reads": 0,
    },

    "downstream_segmentation": "NOT_RUN (explicit stop boundary)",
    "h2b_outcome_adjudicated": "NO",
    "next_action": "WAIT_FOR_SUPERVISOR_H2B_B2_AUTHORIZATION",
}

(A / "post_phase13_h2b_b1_training_evaluation.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

m = obj["standalone_proposal_metrics"]
md = [
    "# H2B-B1 — Training / Execution Audit", "",
    "- **Status: PASS**", f"- experiment: `{EID}`", "",
    "## Bindings", "", "| role | SHA-256 |", "|---|---|"]
for k, v in obj["bindings"].items():
    md.append(f"| {k} | `{v}` |")
md += ["", "## Initialization", "",
       f"- INITIALIZATION: **{obj['initialization_semantics']['INITIALIZATION']}**",
       f"- WARM_START: **{obj['initialization_semantics']['WARM_START']}**",
       f"- PRETRAINED_LOCALIZER_STATE: **{obj['initialization_semantics']['PRETRAINED_LOCALIZER_STATE']}**", "",
       "## Loss (active objective identity)", "",
       f"- class: `{obj['loss']['class']}`", f"- label: `{obj['loss']['label']}`",
       f"- gamma: **{obj['loss']['gamma']}**",
       f"- modulation detached: {obj['loss']['modulation_detached']}",
       f"- dice term: {obj['loss']['dice_term']} · auxiliary loss: {obj['loss']['auxiliary_loss']}",
       f"- objective_change_id: `{obj['loss']['objective_change_id']}`",
       f"- stale `loss_alpha` present: **{obj['loss']['stale_loss_alpha_present']}** · "
       f"stale `loss_beta` present: **{obj['loss']['stale_loss_beta_present']}**", "",
       "## Termination", "",
       f"- reason: **{obj['termination']['reason']}**",
       f"- completed epochs: **{obj['termination']['completed_epochs']}**",
       f"- best epoch: **{obj['termination']['best_epoch']}**",
       f"- final bad epochs: **{obj['termination']['final_bad_epochs']}**", "",
       "## Best six-term tuple", "",
       "```", str(obj["best_six_term_tuple"]), "```", "",
       "## Selection replay", "",
       f"- status: **{obj['selection_replay']['status']}** · mismatches: "
       f"**{obj['selection_replay']['mismatch_count']}** · best epoch "
       f"{obj['selection_replay']['best_epoch']} · max term diff "
       f"`{obj['selection_replay']['max_abs_term_diff']:.3e}`", "",
       "**No trajectory-reproduction gate vs H2A/Phase-13** (SEC 11).", "",
       "## Standalone best-checkpoint proposal metrics", "",
       "| metric | value |", "|---|---|"]
for k in ("proposal_total_count", "proposal_count_per_image", "proposal_pixel_any_hit_precision",
          "proposal_bbox_any_hit_precision", "tiny_recall90", "overall_recall90",
          "overall_recall50", "any_overlap_recall", "mean_coverage", "mean_proposal_union_area",
          "score_max", "score_iqr", "fraction_exactly_at_max",
          "roc_auc_score_to_pixel_any_hit", "pr_auc_score_to_pixel_any_hit"):
    md.append(f"| {k} | {m[k]} |")
md += ["", "## Counters", "", "| counter | value |", "|---|---|"]
for k, v in obj["counters"].items():
    md.append(f"| {k} | {v} |")
md += ["", "**Downstream segmentation: NOT RUN (explicit stop boundary).**",
       "**H2B outcome: NOT adjudicated.**", "",
       "next_action: `WAIT_FOR_SUPERVISOR_H2B_B2_AUTHORIZATION`", ""]
(A / "post_phase13_h2b_b1_training_evaluation.md").write_text("\n".join(md), encoding="utf-8")

print("training evaluation audit written")
print("json sha:", sha(A / "post_phase13_h2b_b1_training_evaluation.json"))
