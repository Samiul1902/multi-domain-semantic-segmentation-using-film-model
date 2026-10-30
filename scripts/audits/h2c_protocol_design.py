"""H2C PROTOCOL DESIGN -- freeze the single head-redesign axis.

No training, no CUDA, no model inference on project data. Static inspection only.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))
A = ROOT / "reports" / "audits"
T = ROOT / "reports" / "tables"


def sha(p):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


EID = ("post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_"
       "centernetfocal_deploymentbalance_seed42_clean_v3")

adj = json.loads((A / "post_phase13_h2b_outcome_adjudication.json").read_text("utf-8"))
h2a_proto = json.loads((A / "post_phase13_h2a_protocol_frozen.json").read_text("utf-8"))

OLD_HEAD_PARAMS = 17
NEW_HEAD_PARAMS = 2337
TOTAL_OLD = 482449
TOTAL_NEW = 484769
PCT = (TOTAL_NEW - TOTAL_OLD) / TOTAL_OLD * 100.0

# ---------------------------------------------------------------- protocol JSON
obj = {
    "artifact": "POST_PHASE13_H2C_PROTOCOL_FROZEN",
    "status": "SUPERVISOR_FROZEN_H2C_HEAD_REDESIGN_READY_FOR_B1_AUTHORIZATION",
    "created_utc": "2026-09-23T16:23:00Z",
    "task": "POST-PHASE13 REGIONAL REVISION H2-C — HEAD / REPRESENTATION REDESIGN PROTOCOL FREEZE",
    "model_attribution": "Gemini 3.1 Pro High",
    "experiment_id": EID,
    "experiment_id_collision": "NONE (checkpoints/ and experiments/ paths absent)",
    "h2_axis": "H2C_HEAD_REDESIGN_OBJECTIVE_AND_SELECTION_FROZEN_FROM_H2A",

    "purpose": {
        "scientific_question": (
            "Can a HEAD-ONLY SPATIAL REPRESENTATION REDESIGN improve heatmap discrimination and "
            "proposal precision while preserving object coverage, holding backbone, target, sigma, "
            "loss, optimizer, scheduler, augmentation, dataset, split, seed, checkpoint selection, "
            "proposal policy, regional segmentation checkpoints, fusion and segmentation threshold "
            "fixed?"),
        "changed_axis": "LOCALIZER PREDICTION-HEAD ARCHITECTURE / REPRESENTATION",
        "training_in_this_task": "NO",
    },

    "prior_evidence_binding": {
        "h2b_outcome_adjudication": {
            "path": "reports/audits/post_phase13_h2b_outcome_adjudication.json",
            "sha256": sha(A / "post_phase13_h2b_outcome_adjudication.json"),
            "status": adj["status"],
            "h2b_outcome": adj["h2b_outcome"],
            "h2c_protocol_design": adj["h2c_eligibility"]["h2c_protocol_design"],
            "h2c_execution": adj["h2c_eligibility"]["h2c_execution"],
            "test_reads": adj["counters"]["test_reads"],
        },
        "h2a_localizer_score_path_audit": {
            "path": "reports/audits/post_phase13_h2a_localizer_score_path_audit.json",
            "sha256": sha(A / "post_phase13_h2a_localizer_score_path_audit.json"),
            "verdict": "SCORE_PATH_IMPLEMENTATION_VALID",
            "key_prior_observation": (
                "The Phase13/H2A lineage displayed near-degenerate proposal-score / head behaviour "
                "with highly saturated proposal maxima."),
            "interpretation_constraint": (
                "This evidence SUPPORTS a head/representation hypothesis. It does NOT prove the "
                "head is the sole cause."),
        },
    },

    "baseline_branch": {
        "branches_from": "H2A (the scientifically stronger baseline)",
        "loss": "CenterNetFocalLoss(alpha=2.0, beta=4.0)",
        "uses_h2b_soft_target_objective": "NO",
        "correct_description": (
            "H2C branches from the H2A baseline and tests head representation as a new isolated "
            "axis after H2B objective redesign proved insufficient."),
        "incorrect_description_avoided": "H2B plus a new head",
        "checkpoint_selection": {
            "tuple": ["DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90", "tiny_recall90",
                      "overall_recall90", "PROPOSAL_PIXEL_ANY_HIT_PRECISION",
                      "-mean_roi_area_fraction", "-val_loss"],
            "comparison": "STRICT_LEXICOGRAPHIC_GREATER_THAN",
            "ties": "BAD_EPOCH", "patience": 15,
            "downstream_metric_participates": "NO",
            "changed_vs_h2a": "NO",
        },
    },

    "old_head": {
        "module": "src/models/kub_localizer.py :: KUBLocalizer.head",
        "structure": "nn.Conv2d(16, 1, kernel_size=1, stride=1, padding=0, bias=True)",
        "spatial_mixing_inside_head": "NONE",
        "parameter_count": OLD_HEAD_PARAMS,
        "weight_shape": [1, 16, 1, 1],
        "initialization": {"weight": "ALL_ZERO (constant 0.0)", "bias": "log(0.1/0.9) = logit(0.1)"},
        "output_shape": [1, 1, 128, 128],
        "heatmap_resolution": 128,
        "internal_sigmoid": "NONE",
        "physically_verified": "YES",
    },

    "new_head": {
        "name": "SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1",
        "variants_frozen": 1,
        "structure": [
            "Conv2d(16, 16, kernel_size=3, stride=1, padding=1, bias=True)",
            "ReLU(inplace=False)",
            "Conv2d(16, 1, kernel_size=1, stride=1, padding=0, bias=True)",
        ],
        "hidden_width": 16,
        "hidden_width_search": "NONE",
        "head_family_search": "NONE",
        "forbidden_components": ["BatchNorm", "GroupNorm", "LayerNorm", "dropout", "attention",
                                 "residual block", "extra decoder", "multi-scale branch",
                                 "deep supervision"],
        "backbone": "byte-for-byte / semantically UNCHANGED",
        "parameter_count": NEW_HEAD_PARAMS,
        "initialization": {
            "conv3x3_weight": "kaiming_normal_(nonlinearity='relu')",
            "conv3x3_bias": "0",
            "conv1x1_weight": "ALL ZERO",
            "conv1x1_bias": "logit(0.1) = log(0.1/0.9) = -2.1972245773362196",
            "tuned_after_results": "NO",
            "note": ("At initialization the terminal zero weights imply spatially constant initial "
                     "logits equal to the frozen bias. This is intentional."),
            "measured_initial_logit_max_minus_min": 0.0,
        },
        "output_shape": [1, 1, 128, 128],
        "internal_sigmoid": "NONE",
    },

    "rationale": {
        "old_head_behaviour": "only a pointwise linear projection of backbone features",
        "new_head_adds": ["local 3x3 spatial mixing", "one nonlinear transformation"],
        "before_final_heatmap_logit": True,
        "intended_test": ("whether additional local discriminative capacity in the head can reduce "
                          "score saturation / off-target proposal behaviour"),
        "will_succeed_asserted": "NO",
        "old_head_proven_causal": "NO",
    },

    "parameter_shape_contract": {
        "old_head_parameter_count": OLD_HEAD_PARAMS,
        "new_head_parameter_count": NEW_HEAD_PARAMS,
        "absolute_parameter_delta": NEW_HEAD_PARAMS - OLD_HEAD_PARAMS,
        "whole_model_old_parameter_count": TOTAL_OLD,
        "whole_model_h2c_parameter_count": TOTAL_NEW,
        "percentage_parameter_increase": PCT,
        "all_new_trainable_parameters_belong_to_head": "YES",
        "backbone_parameter_shapes": "UNCHANGED",
        "input_channels": 1,
        "output_logit_channels": 1,
        "heatmap": "128 x 128",
        "internal_sigmoid": "NONE",
        "external_inference_sigmoid": "exactly once, unchanged",
    },

    "training_contract": {
        "TRAIN": "770 FULL_FIELD cases / 1161 components",
        "VAL": "103 FULL_FIELD cases / 152 components",
        "ROI": "EXCLUDED", "manifest": "phase4_v3", "taxonomy": "kub_size_clean_v3_v1",
        "input": "512 x 512", "heatmap": "128 x 128", "sigma": 0.75,
        "backbone": "UNCHANGED existing KUB localizer backbone",
        "target": "UNCHANGED existing CenterNet-style Gaussian heatmap",
        "loss": "CenterNetFocalLoss(alpha=2.0, beta=4.0)",
        "optimizer": "AdamW", "lr": 1e-4, "weight_decay": 1e-4,
        "scheduler": "CosineAnnealingLR(T_max=100)", "batch": 4,
        "amp": "same accepted H2A semantics", "seed": 42, "augmentation": "UNCHANGED",
        "workers": 0, "max_epochs": 100, "cuda": "required during future execution",
        "test": "forbidden",
    },

    "proposal_contract": {
        "threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30,
        "grid": "NONE", "threshold_search": "NONE", "max_proposal_ablation": "NONE",
        "h1_selective_filtering": "NONE", "score_calibration": "NONE", "policy_family": "NONE",
    },

    "checkpoint_selection_contract": {
        "P": "PROPOSAL_PIXEL_ANY_HIT_PRECISION", "T": "tiny_recall90", "O": "overall_recall90",
        "H": "0 if any P/T/O <= 0 else 3 / (1/P + 1/T + 1/O)",
        "primary_tuple": ["H", "T", "O", "P", "-mean_roi_area_fraction", "-val_loss"],
        "comparison": "STRICT_LEXICOGRAPHIC_GREATER_THAN", "patience": 15,
        "changed_vs_h2a": "NO",
    },

    "primary_localizer_diagnostics": {
        "per_completed_epoch": [
            "proposal-score mean", "median", "Q25", "Q75", "max", "IQR",
            "fraction exactly at epoch maximum", "number of distinct proposal-score values",
            "score standard deviation", "hit-proposal score mean/median",
            "miss-proposal score mean/median",
            "ROC-AUC score->pixel-any-hit", "PR-AUC score->pixel-any-hit",
        ],
        "enter_selection": "NO (only P/T/O/H as already frozen)",
        "calibration_search": "NONE",
    },

    "head_specific_diagnostics": {
        "recorded_at": "selected best checkpoint only",
        "hidden_3x3_weight": ["mean", "std", "min", "max", "fraction positive",
                              "fraction negative", "channel-wise norm distribution"],
        "terminal_1x1_weight": ["mean", "std", "min", "max", "fraction positive",
                                "fraction negative"],
        "terminal_bias": True,
        "non_degeneracy_threshold": "NONE",
        "gates_selection": "NO",
        "purpose": "mechanistic description only",
    },

    "scientific_change_register": {
        "CHANGE_H2C_001": {
            "axis": "LOCALIZER_PREDICTION_HEAD_ARCHITECTURE",
            "old": "Conv2d(16 -> 1, kernel_size=1)",
            "new": "Conv2d(16 -> 16, kernel_size=3, padding=1) + ReLU + Conv2d(16 -> 1, kernel_size=1)",
            "initialization_part_of_same_axis": True,
        },
        "LOSS_CHANGED": "NO vs H2A", "TARGET_CHANGED": "NO", "SIGMA_CHANGED": "NO",
        "BACKBONE_CHANGED": "NO", "OPTIMIZER_CHANGED": "NO", "DATA_CHANGED": "NO",
        "AUGMENTATION_CHANGED": "NO", "CHECKPOINT_SELECTION_CHANGED": "NO vs H2A",
        "PROPOSAL_POLICY_CHANGED": "NO", "FUSION_CHANGED": "NO",
        "SEGMENTATION_CHECKPOINTS_CHANGED": "NO", "HEAD_ARCHITECTURE_CHANGED": "YES",
        "second_scientific_axis": "NONE",
    },

    "h2b_relationship": {
        "h2b_status": "CLOSED", "combined_with_h2c": "NO",
        "h2c_objective": "H2A focal objective (NOT the H2B soft-target objective)",
        "must_not_be_described_as": "H2B plus a new head",
    },

    "standalone_localizer_evaluation_contract": {
        "population": "103 VAL cases / 152 components",
        "proposal_config": "exactly one fixed configuration",
        "comparison": ["H2C", "frozen H2A best", "frozen Phase13 best"],
        "metrics": ["proposal count", "pixel-any-hit precision", "bbox-any-hit precision",
                    "tiny recall90", "overall recall90", "recall50", "any-overlap recall",
                    "mean coverage", "mean union area", "hard-Tiny", "global-empty",
                    "multi-component", "score dispersion / saturation", "ROC-AUC", "PR-AUC",
                    "size-stratified coverage"],
        "significance_claim": "NONE", "threshold_tuning": "NONE",
    },

    "prospective_downstream_contract": {
        "segmentation_checkpoints": ["unet", "attention_unet", "unetpp", "deeplabv3plus"],
        "global_cache": "same verified GLOBAL cache",
        "crop_restore": "same Part1D square/padding-correct",
        "variant": "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED",
        "margin": 0.20, "nms_iou": 0.30, "proposal_threshold": 0.10, "top_k": 5,
        "segmentation_threshold": 0.5,
        "h1_filtering": "NONE", "h2b_policy": "NONE", "new_fusion": "NONE",
    },

    "prospective_evidence_dimensions": {
        "A": "LOCALIZER_PROPOSAL_QUALITY", "B": "DOWNSTREAM_GLOBAL_PRESERVATION",
        "C": "REGIONAL_UTILITY", "D": "CROSS_ARCHITECTURE_GENERALITY",
        "added_after_results": "NONE",
    },

    "prospective_outcome_definitions": {
        "note": ("Frozen BEFORE H2C execution. H2B froze labels without an evidence-to-label "
                 "mapping; H2C freezes both."),
        "H2C_HEAD_REDESIGN_SUFFICIENT": (
            "The head redesign produces reproducible favourable localizer proposal quality relative "
            "to the frozen H2A baseline AND those changes translate into a downstream "
            "predicted-region path that descriptively resolves the major global-preservation "
            "failure while retaining meaningful regional utility across architectures. No "
            "numerical cutoff is introduced."),
        "H2C_HEAD_REDESIGN_PARTIAL": (
            "The head redesign produces reproducible favourable localizer changes relative to H2A "
            "and at least some corresponding downstream improvement, but the complete "
            "predicted-region path still does not adequately resolve global preservation and/or "
            "loses substantial regional utility."),
        "H2C_HEAD_REDESIGN_INSUFFICIENT": (
            "Either (a) the head redesign does not produce reproducible favourable localizer "
            "proposal-quality changes relative to H2A, OR (b) favourable localizer changes do not "
            "translate into meaningful downstream improvement and the major deployable failure "
            "remains."),
        "CHECK_REQUIRED": (
            "A material protocol, provenance, integrity, leakage, or quantitative evidence defect "
            "prevents scientific adjudication."),
        "numerical_thresholds": "NONE", "weighted_score": "NONE", "winner": "NONE",
    },

    "comparator_discipline": {
        "primary_localizer_comparator": "H2A best checkpoint",
        "secondary_historical_comparator": "Phase13 best checkpoint",
        "primary_downstream_comparators": ["GLOBAL", "Phase13 predicted-region",
                                           "H2A predicted-region", "ORACLE"],
        "h2b_role": "HISTORICAL_CONTEXT_ONLY",
        "h2b_as_tuning_reference": "NO",
    },

    "future_execution_split": {
        "H2C_B1": "training + standalone localizer evaluation -> SUPERVISOR REVIEW",
        "H2C_B2": "downstream four-architecture segmentation evaluation (only if separately authorized)",
        "both_authorized_now": "NO",
    },

    "if_h2c_insufficient": {
        "design_h2d": "NO", "change_target": "NO", "change_sigma": "NO",
        "change_backbone": "NO", "change_fusion": "NO", "start_h3": "NO", "start_phase14": "NO",
        "FURTHER_REVISION": "REQUIRES_SUPERVISOR_DECISION",
        "H3": "NOT_AUTOMATICALLY_AUTHORIZED",
    },

    "claim_limits": {
        "will_succeed_asserted": "NO", "old_head_proven_causal": "NO",
        "numerical_success_threshold": "NONE", "hidden_grid": "NONE",
        "test_or_external_access": "NONE", "winner": "NONE",
    },

    "counters": {
        "training": 0, "optimizer_constructions": 0, "model_constructions": 0,
        "cuda_requests": 0, "localizer_forwards": 0, "proposal_generation": 0,
        "segmentation_forwards": 0, "regional_forwards": 0, "checkpoint_writes": 0,
        "test_reads": 0, "external_test_reads": 0,
        "note": ("Static module inspection and a single random-tensor forward on synthetic input "
                 "were performed to verify shapes; NO project data, NO CUDA, NO trained weights."),
    },

    "continuity": {
        "phase13": "COMPLETE_FROZEN", "original_gate": "REVISE_LOCALIZER_FROZEN", "h1": "CLOSED",
        "h2a": "CLOSED__SELECTION_REDESIGN_PARTIAL",
        "h2b": "CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT",
        "h2c_protocol": "COMPLETE_PASS_FROZEN",
        "h2c_b1": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION", "h2c_b1_authorized": False,
        "h2c_b2": "NOT_STARTED", "h3": "NOT_STARTED", "phase14": "NOT_STARTED",
        "test": "UNTOUCHED",
    },

    "next_action": "WAIT_FOR_SUPERVISOR_H2C_B1_AUTHORIZATION",
}
(A / "post_phase13_h2c_protocol_frozen.json").write_text(
    json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

# ---------------------------------------------------------------- diff vs H2A
ROWS = [
    ("experiment_id", h2a_proto["experiment_id"], EID, "PROVENANCE"),
    ("protocol_binding", "post_phase13_h2a_protocol_frozen.json",
     "post_phase13_h2c_protocol_frozen.json", "PROVENANCE"),
    ("head_architecture", "Conv2d(16->1, kernel_size=1)", 
     "Conv2d(16->16, k=3, p=1) + ReLU + Conv2d(16->1, k=1)", "SCIENTIFIC_AXIS__CHANGE_H2C_001"),
    ("head_initialization", "conv weight 0.0; bias logit(0.1)",
     "conv3x3 kaiming/0; conv1x1 weight 0.0; conv1x1 bias logit(0.1)", "SCIENTIFIC_AXIS__CHANGE_H2C_001"),
    ("loss", "CenterNetFocalLoss(alpha=2.0, beta=4.0)", "CenterNetFocalLoss(alpha=2.0, beta=4.0)", "LOSS"),
    ("target", "CenterNet-style Gaussian heatmap", "CenterNet-style Gaussian heatmap", "TARGET"),
    ("sigma", 0.75, 0.75, "TARGET"),
    ("backbone", "3-stage compact U-Net, base 16", "3-stage compact U-Net, base 16", "BACKBONE"),
    ("in_channels", 1, 1, "ARCHITECTURE"), ("out_channels", 1, 1, "ARCHITECTURE"),
    ("base_channels", 16, 16, "ARCHITECTURE"),
    ("heatmap_resolution", 128, 128, "ARCHITECTURE"),
    ("input_resolution", "512 x 512", "512 x 512", "ARCHITECTURE"),
    ("internal_sigmoid", "NONE", "NONE", "ARCHITECTURE"),
    ("TRAIN", "770 FULL_FIELD / 1161 components", "770 FULL_FIELD / 1161 components", "DATA"),
    ("VAL", "103 FULL_FIELD / 152 components", "103 FULL_FIELD / 152 components", "DATA"),
    ("ROI", "EXCLUDED", "EXCLUDED", "DATA"),
    ("manifest", "phase4_v3", "phase4_v3", "DATA"),
    ("taxonomy", "kub_size_clean_v3_v1", "kub_size_clean_v3_v1", "DATA"),
    ("augmentation", "UNCHANGED Phase13 semantics", "UNCHANGED Phase13 semantics", "DATA"),
    ("optimizer", "AdamW", "AdamW", "OPTIMIZATION"),
    ("learning_rate", 1e-4, 1e-4, "OPTIMIZATION"),
    ("weight_decay", 1e-4, 1e-4, "OPTIMIZATION"),
    ("scheduler", "CosineAnnealingLR(T_max=100)", "CosineAnnealingLR(T_max=100)", "OPTIMIZATION"),
    ("batch", 4, 4, "OPTIMIZATION"),
    ("amp", "same accepted semantics", "same accepted semantics", "OPTIMIZATION"),
    ("seed", 42, 42, "OPTIMIZATION"),
    ("max_epochs", 100, 100, "OPTIMIZATION"),
    ("workers", 0, 0, "OPTIMIZATION"),
    ("checkpoint_selection",
     " > ".join(h2a_proto["h2a_primary_checkpoint_tuple"]["tuple"]),
     " > ".join(h2a_proto["h2a_primary_checkpoint_tuple"]["tuple"]), "CHECKPOINT_SELECTION"),
    ("checkpoint_selection_patience", 15, 15, "CHECKPOINT_SELECTION"),
    ("checkpoint_selection_ties", "BAD_EPOCH", "BAD_EPOCH", "CHECKPOINT_SELECTION"),
    ("proposal_threshold", 0.10, 0.10, "PROPOSAL"),
    ("proposal_margin", 0.20, 0.20, "PROPOSAL"),
    ("proposal_top_k", 5, 5, "PROPOSAL"),
    ("proposal_nms_iou", 0.30, 0.30, "PROPOSAL"),
    ("proposal_grid", "NONE", "NONE", "PROPOSAL"),
    ("fusion", "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED", "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED", "FUSION"),
    ("segmentation_threshold", 0.5, 0.5, "FUSION"),
    ("segmentation_checkpoints", "unet|attention_unet|unetpp|deeplabv3plus",
     "unet|attention_unet|unetpp|deeplabv3plus", "FUSION"),
]
diff = pd.DataFrame([{"field": f, "h2a_value": a, "h2c_value": b,
                      "changed": "YES" if str(a) != str(b) else "NO",
                      "scientific_role": r} for f, a, b, r in ROWS])
diff.to_csv(T / "post_phase13_h2c_protocol_diff_vs_h2a.csv", index=False)

# ---------------------------------------------------------------- evidence contract
pd.DataFrame([
    ("A", "LOCALIZER_PROPOSAL_QUALITY",
     "proposal count; pixel-any-hit precision; bbox-any-hit precision; tiny90; overall90; recall50; "
     "any-overlap recall; mean coverage; mean union area; score dispersion / saturation; ROC-AUC; PR-AUC",
     "H2C-B1 standalone localizer evaluation", "NO_THRESHOLD"),
    ("B", "DOWNSTREAM_GLOBAL_PRESERVATION",
     "Dice; IoU; precision; recall; FP; FN; cases improved/worse",
     "H2C-B2 (if authorized)", "NO_THRESHOLD"),
    ("C", "REGIONAL_UTILITY",
     "component recoveries; component losses; empty recoveries; oracle-benefit retention",
     "H2C-B2 (if authorized)", "NO_THRESHOLD"),
    ("D", "CROSS_ARCHITECTURE_GENERALITY",
     "UNet; Attention U-Net; UNet++; DeepLabV3+", "H2C-B2 (if authorized)", "NO_RANKING"),
], columns=["dimension_id", "dimension_name", "measured_quantities", "produced_by",
            "success_threshold"]).to_csv(T / "post_phase13_h2c_evidence_contract.csv", index=False)

# ---------------------------------------------------------------- outcome definitions
pd.DataFrame([
    ("H2C_HEAD_REDESIGN_SUFFICIENT",
     "Reproducible favourable localizer proposal quality vs frozen H2A baseline AND those changes "
     "translate into a downstream predicted-region path that descriptively resolves the major "
     "global-preservation failure while retaining meaningful regional utility across architectures.",
     "NO_NUMERICAL_CUTOFF"),
    ("H2C_HEAD_REDESIGN_PARTIAL",
     "Reproducible favourable localizer changes vs H2A and at least some corresponding downstream "
     "improvement, but the complete predicted-region path still does not adequately resolve global "
     "preservation and/or loses substantial regional utility.", "NO_NUMERICAL_CUTOFF"),
    ("H2C_HEAD_REDESIGN_INSUFFICIENT",
     "(a) the head redesign does not produce reproducible favourable localizer proposal-quality "
     "changes relative to H2A, OR (b) favourable localizer changes do not translate into meaningful "
     "downstream improvement and the major deployable failure remains.", "NO_NUMERICAL_CUTOFF"),
    ("CHECK_REQUIRED",
     "A material protocol, provenance, integrity, leakage, or quantitative evidence defect prevents "
     "scientific adjudication.", "NO_NUMERICAL_CUTOFF"),
], columns=["outcome_label", "definition", "threshold"]).to_csv(
    T / "post_phase13_h2c_outcome_definitions.csv", index=False)

print("H2C protocol artifacts written")
print("  protocol json:", sha(A / "post_phase13_h2c_protocol_frozen.json"))
print("  diff rows:", len(diff), "changed:", int((diff.changed == "YES").sum()))
print("  changed fields:", diff[diff.changed == "YES"].field.tolist())
print("  param delta:", NEW_HEAD_PARAMS - OLD_HEAD_PARAMS, "| pct:", round(PCT, 6))
