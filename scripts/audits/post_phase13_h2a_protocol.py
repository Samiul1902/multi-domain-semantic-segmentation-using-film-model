"""POST-PHASE-13 H2-A — localizer score-path audit + selection-only protocol freeze.

STATIC inspection only. No training, no model construction, no CUDA, no forward pass,
no proposal generation, no checkpoint writes, no TEST access.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path

import pandas as pd
import torch

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
FREEZE_UTC = "2026-09-22T07:28:00Z"
CKPT_DIR = ROOT / "checkpoints" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
EXP_DIR = ROOT / "experiments" / "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3"
H2A_ID = "post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3"
PLATEAU = 0.1250653713941574


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> dict:
    h1 = json.loads((AUDITS / "post_phase13_regional_revision_r1_h1_adjudication.json").read_text("utf-8"))
    clar = json.loads((AUDITS / "post_phase13_r0_interpretation_clarification.json").read_text("utf-8"))
    ck = torch.load(CKPT_DIR / "best.pt", map_location="cpu", weights_only=False)
    ck68 = torch.load(CKPT_DIR / "latest.pt", map_location="cpu", weights_only=False)
    hist = pd.read_csv(EXP_DIR / "history.csv")

    hw = ck["model_state"]["head.weight"].flatten().float()
    hb = float(ck["model_state"]["head.bias"][0])
    head = {
        "weight_shape": list(ck["model_state"]["head.weight"].shape),
        "weight_values": [float(v) for v in hw.tolist()],
        "weight_max": float(hw.max()), "weight_min": float(hw.min()),
        "weight_mean": float(hw.mean()), "weight_std": float(hw.std()),
        "weight_abs_max": float(hw.abs().max()), "weight_abs_mean": float(hw.abs().mean()),
        "weight_abs_max_over_abs_mean": float(hw.abs().max() / hw.abs().mean()),
        "weight_positive_count": int((hw > 0).sum()), "weight_negative_count": int((hw < 0).sum()),
        "bias": hb, "sigmoid_of_bias": 1.0 / (1.0 + math.exp(-hb)),
        "head_init_marker": "phase13b_centernet_head_init_p01_v1 (weight=0, bias=logit(0.1))",
    }

    # ---------------- §3 / §4 score-path audit ----------------
    audit = {
        "artifact": "POST_PHASE13_H2A_LOCALIZER_SCORE_PATH_AUDIT",
        "status": "COMPLETE",
        "created_utc": FREEZE_UTC,
        "method": ("STATIC code inspection + static checkpoint tensor inspection. "
                   "No model construction, no forward pass, no CUDA request."),
        "observed_phenomenon": {
            "plateau_score": PLATEAU,
            "count_at_plateau": 337, "proposals_total": 494,
            "fraction_at_plateau": 0.6821862348178138,
            "equivalent_logit": math.log(PLATEAU / (1 - PLATEAU)),
        },
        "score_path": [
            {"stage": "1. model logits", "location": "src/models/kub_localizer.py:forward -> self.head(...) -> logit_downsample",
             "detail": "KUBLocalizer emits (1,1,128,128) logits; final layer `head` is a 1x1 conv (1,16,1,1) with bias."},
            {"stage": "2. probability transform", "location": "src/inference/learned_roi_clean_v3.py:171",
             "detail": "heatmap = torch.sigmoid(logits)[0, 0].float().cpu().numpy() -> (128,128) float32 in [0,1]."},
            {"stage": "3. component proposal extraction", "location": "src/inference/predicted_roi.py:extract_predicted_components",
             "detail": "binary = probability_map >= threshold; scipy.ndimage.label with 3x3 (8-connectivity); per-component bbox + pixel count."},
            {"stage": "4. score assignment", "location": "src/inference/predicted_roi.py:142-143",
             "detail": "max_probs = scipy.ndimage.maximum(probability_map, labels=labeled, index=indices); "
                       "max_probability = float(max_probs[cid-1]) -> per-component MAXIMUM sigmoid probability."},
            {"stage": "5. NMS", "location": "src/inference/predicted_roi.py:47-53,145,154",
             "detail": "components sorted by (-max_probability, bbox); deterministic score-descending box NMS at nms_iou."},
            {"stage": "6. top-k + serialization", "location": "src/inference/predicted_roi.py:154-162",
             "detail": "components[:top_k]; proposal dict {'rank','score': max_probability, ...}. Score written as raw Python float."},
        ],
        "defect_matrix": {
            "hard_clamp": {"present": False, "evidence": "no torch.clamp / np.clip / min / max on the probability or score anywhere in the score path"},
            "normalization_to_fixed_ceiling": {"present": False, "evidence": "no division or rescaling of the heatmap or score"},
            "rounding_of_score": {"present": False, "evidence": "score stored as raw float; no round()/np.round on the score"},
            "quantization": {"present": False, "evidence": "probability stays float32 from sigmoid to serialization; no uint8 cast"},
            "incorrect_sigmoid_application": {"present": False, "evidence": "torch.sigmoid applied on logits in learned_roi_clean_v3.py:171"},
            "double_sigmoid": {"present": False, "evidence": "model forward returns logits only (no internal sigmoid in kub_localizer.py); sigmoid applied exactly once"},
            "post_processing_rescale": {"present": False, "evidence": "no post-hoc rescale between sigmoid and score assignment"},
            "wrong_heatmap_channel": {"present": False, "evidence": "indexing [0, 0] = batch 0, channel 0; out_channels == 1"},
            "wrong_local_max_extraction": {"present": False, "evidence": "scipy.ndimage.maximum per label is the correct per-component maximum"},
            "serialization_truncation": {"present": False, "evidence": "float written at full precision; 0.1250653713941574 round-trips exactly in the frozen CSV"},
            "top_k_score_replacement": {"present": False, "evidence": "top_k only truncates the sorted list; scores are never overwritten"},
            "threshold_substitution": {"present": False, "evidence": "threshold is used only for binarization (>= threshold); it never becomes the score"},
        },
        "sigmoid_application": "EXACTLY_ONCE",
        "score_clipped": "NO",
        "score_normalized": "NO",
        "score_rounded": "NO",
        "serialization_truncation": "NO",
        "plateau_maximum_imposed_by_code": "NO",
        "root_cause_of_plateau": {
            "classification": "TRAINED_MODEL_OUTPUT_PROPERTY__NOT_A_SCORE_PATH_DEFECT",
            "evidence": (
                "The plateau equals sigmoid(head output). The trained head is degenerate: all 16 channel weights are "
                "NEGATIVE and nearly identical in magnitude (range -0.20109390 to -0.20757976, std 0.00180099, "
                "abs-max/abs-mean = 1.019491, 0/16 positive), so the head is effectively -0.203611 * sum(features) + bias. "
                "The bias is -1.9453773498535156, whose sigmoid is 0.12505828655695442 - essentially the observed plateau "
                "(0.1250653713941574, which corresponds to logit -1.9453126016481144). The head therefore produces a "
                "NEAR-CONSTANT output field, and the plateau is the sigmoid of that near-constant logit."),
            "implication": (
                "The score path is implemented correctly. The near-ceiling saturation is a property of the trained "
                "network, not of the code that extracts the score. This does NOT trigger CHECK_REQUIRED for the score "
                "path, but it is a MATERIAL SCIENTIFIC OBSERVATION that must inform H2A expectations."),
        },
        "verdict": "SCORE_PATH_IMPLEMENTATION_VALID",
        "material_scientific_observation": {
            "id": "DEGENERATE_LOCALIZER_HEAD__NEAR_CONSTANT_OUTPUT",
            "severity": "MATERIAL",
            "is_score_path_defect": "NO",
            "blocks_h2a_freeze": "NO",
            "disclosure": (
                "Recorded, not hidden. Because the heatmap is near-constant, no checkpoint-selection rule can "
                "substantially improve proposal precision on its own. H2A is therefore a genuine and necessary test "
                "of the selection axis, but this finding pre-registers a plausible reason H2A may prove insufficient - "
                "in which case representation/objective redesign (not selection) becomes the indicated direction."),
            "head_initialization": head["head_init_marker"],
        },
        "head_tensor_evidence": head,
        "bindings": {
            "h1_adjudication": {"path": "reports/audits/post_phase13_regional_revision_r1_h1_adjudication.json",
                                "sha": sha(AUDITS / "post_phase13_regional_revision_r1_h1_adjudication.json"),
                                "h1_outcome": h1["h1_outcome"]},
            "r0_clarification": {"path": "reports/audits/post_phase13_r0_interpretation_clarification.json",
                                 "sha": sha(AUDITS / "post_phase13_r0_interpretation_clarification.json"),
                                 "classification": clar["classification"]},
            "localizer_best_pt": {"path": str((CKPT_DIR / "best.pt").relative_to(ROOT)).replace("\\", "/"),
                                  "sha": sha(CKPT_DIR / "best.pt"), "epoch": int(ck["epoch"])},
            "history_csv": {"path": str((EXP_DIR / "history.csv").relative_to(ROOT)).replace("\\", "/"),
                            "sha": sha(EXP_DIR / "history.csv"), "rows": int(len(hist))},
            "score_path_sources": {
                "learned_roi_clean_v3": {"path": "src/inference/learned_roi_clean_v3.py",
                                         "sha": sha(ROOT / "src/inference/learned_roi_clean_v3.py")},
                "predicted_roi": {"path": "src/inference/predicted_roi.py",
                                  "sha": sha(ROOT / "src/inference/predicted_roi.py")},
                "kub_localizer": {"path": "src/models/kub_localizer.py",
                                  "sha": sha(ROOT / "src/models/kub_localizer.py")},
            },
        },
        "counters": {"training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
                     "localizer_forwards": 0, "segmentation_forwards": 0, "regional_forwards": 0,
                     "proposal_generation": 0, "checkpoint_writes": 0, "test_reads": 0,
                     "external_test_reads": 0},
    }
    (AUDITS / "post_phase13_h2a_localizer_score_path_audit.json").write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------- §5 trajectory availability ----------------
    epoch_ckpts = []
    for p in sorted(CKPT_DIR.rglob("*.pt")):
        c = torch.load(p, map_location="cpu", weights_only=False)
        epoch_ckpts.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"),
                            "epoch": int(c["epoch"]), "sha": sha(p)})
    avail = sorted({e["epoch"] for e in epoch_ckpts})
    traj = {
        "history_rows_expected": 68,
        "history_rows_observed": int(len(hist)),
        "history_contiguous_epochs": bool((hist.epoch.diff().dropna() == 1).all()),
        "history_csv_sha": sha(EXP_DIR / "history.csv"),
        "best_pt_epoch": int(ck["epoch"]), "best_pt_history_rows": len(ck["training_history"]),
        "latest_pt_epoch": int(ck68["epoch"]), "latest_pt_history_rows": len(ck68["training_history"]),
        "best_pt_best_validation_score": [float(v) for v in ck["best_validation_score"]],
        "best_pt_early_stopping_state": ck["early_stopping_state"],
        "latest_pt_early_stopping_state": ck68["early_stopping_state"],
        "checkpoint_files": epoch_ckpts,
        "available_epoch_weights": avail,
        "available_epoch_weight_count": len(avail),
        "epochs_total": 68,
        "per_epoch_proposal_tables_or_sidecars": "NONE (only history.csv exists)",
        "per_epoch_proposal_hit_precision_in_history": "NO (no precision/hit columns present)",
        "proposal_hit_precision_reconstructable_without_inference": "NO",
        "classification": "C__ONLY_BEST_AND_LATEST_AVAILABLE",
        "classification_note": (
            "Only best.pt (epoch 53) and latest.pt (epoch 68) exist as live checkpoints, plus two archived epoch-31 "
            "checkpoints retained under provenance/ from the R2B/R2C provisional archive. Distinct epoch weights "
            f"available: {avail} = {len(avail)} of 68. No per-epoch proposal outputs exist. Proposal hit-precision "
            "therefore CANNOT be reconstructed for every epoch without model inference."),
        "invented_checkpoints": "NONE",
    }

    # ---------------- §6-§11 frozen H2A protocol ----------------
    NEW_TUPLE = ["DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90", "tiny_recall90", "overall_recall90",
                 "PROPOSAL_PIXEL_ANY_HIT_PRECISION", "-mean_roi_area_fraction", "-val_loss"]
    OLD_TUPLE = ["tiny_recall90", "overall_recall90", "-mean_roi_area_fraction", "-val_loss"]

    proto = {
        "artifact": "POST_PHASE13_H2A_PROTOCOL_FROZEN",
        "status": "SUPERVISOR_FROZEN_H2A_SELECTION_ONLY_READY_FOR_EXECUTION",
        "created_utc": FREEZE_UTC,
        "experiment_id": H2A_ID,
        "experiment_id_collision": "NONE (both checkpoints/ and experiments/ paths absent)",
        "h2_axis": "H2A_DEPLOYMENT_BALANCED_CHECKPOINT_SELECTION_ONLY",
        "scientific_question": (
            "Can a deployment-aligned LOCALIZER CHECKPOINT-SELECTION rule improve proposal precision / "
            "precision-recall balance sufficiently WITHOUT changing architecture, training target, sigma, loss, "
            "optimizer, scheduler, augmentation, data, seed, proposal geometry, proposal threshold, margin, top-k, "
            "NMS, regional segmentation models or fusion semantics?"),
        "score_path_verdict": audit["verdict"],
        "trajectory_classification": traj["classification"],
        "execution_mode": "MODE_B__DETERMINISTIC_TRAINING_REPLAY_WITH_NEW_SELECTION",
        "execution_mode_reason": (
            "The new rule requires PROPOSAL_PIXEL_ANY_HIT_PRECISION for EVERY epoch. That quantity needs proposals, "
            "which need each epoch's weights and an inference pass. Only 3 distinct epoch weights exist (31, 53, 68 of "
            "68) and no per-epoch proposal outputs were persisted, so checkpoint replay alone cannot apply the new "
            "rule. MODE_B is therefore required. The replay MUST retain identical gradient-update semantics; the ONLY "
            "scientific change is which epoch is declared best and drives early stopping."),
        "frozen_training_contract": {
            "TRAIN": "770 FULL_FIELD cases / 1161 components", "VAL": "103 FULL_FIELD cases / 152 components",
            "ROI": "EXCLUDED", "manifest": "phase4_v3", "taxonomy": "kub_size_clean_v3_v1",
            "input": "512 x 512", "heatmap": "128 x 128", "sigma": 0.75,
            "architecture": "existing compact KUB localizer", "in_channels": 1, "out_channels": 1,
            "base_channels": 16, "target": "existing CenterNet-style heatmap target unchanged",
            "loss": "CenterNetFocalLoss(alpha=2.0, beta=4.0)", "optimizer": "AdamW", "lr": 1e-4,
            "weight_decay": 1e-4, "scheduler": "CosineAnnealingLR(T_max=100)", "batch": 4,
            "amp": "same accepted Phase13 semantics", "seed": 42,
            "augmentation": "UNCHANGED from clean-v3 Phase13", "max_epochs": 100, "workers": 0,
            "cuda": "required", "test": "forbidden",
        },
        "frozen_proposal_evaluation_contract": {
            "threshold": 0.10, "margin": 0.20, "top_k": 5, "nms_iou": 0.30,
            "grid": "NONE", "threshold_search": "NONE", "per_epoch_sensitivity_analysis": "NONE",
            "coverage_semantics": "canonical historical executing BBOX coverage remains available; pixel semantics remain secondary sensitivity where appropriate",
            "new_primary_quantity": {
                "name": "PROPOSAL_PIXEL_ANY_HIT_PRECISION",
                "numerator": "number of generated proposals whose CLIPPED native proposal support contains at least one native GT foreground pixel",
                "denominator": "total generated proposals across the complete 103-case VAL population",
                "zero_denominator_rule": "precision = 0.0",
            },
            "secondary_diagnostic": "PROPOSAL_BBOX_ANY_HIT_PRECISION",
        },
        "new_primary_checkpoint_utility": {
            "label": "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90",
            "definition": "0.0 if any of P,T,O <= 0 else 3 / (1/P + 1/T + 1/O)",
            "P": "PROPOSAL_PIXEL_ANY_HIT_PRECISION", "T": "tiny_recall90", "O": "overall_recall90",
            "is_statistical_f1": "NO - must not be called an F1 score",
            "purpose": "balance proposal intervention precision, tiny-object coverage and overall component coverage without an arbitrary weighted sum",
        },
        "h2a_primary_checkpoint_tuple": {
            "tuple": NEW_TUPLE, "tuple_length": 6,
            "comparison": "STRICT_LEXICOGRAPHIC_GREATER_THAN", "ties": "BAD_EPOCH",
            "early_stop_patience": 15, "checkpoint": "strict improvement only",
            "latest_pt": "every completed epoch",
            "downstream_segmentation_metric_participates": "NO",
            "phase12_oracle_result_participates": "NO",
            "r1_segmentation_outcome_participates": "NO",
        },
        "secondary_per_epoch_diagnostics": {
            "computed_but_structurally_excluded_from_selection": [
                "proposal_bbox_any_hit_precision", "proposal_count_per_image", "hard_Tiny_recovery",
                "global_empty_recovery", "multi_component_recall", "overall_recall50", "any_overlap_recall",
                "mean_coverage", "proposal_score_mean", "proposal_score_median", "proposal_score_Q25",
                "proposal_score_Q75", "proposal_score_max", "fraction_proposals_exactly_at_epoch_max_score",
                "score_IQR", "hit_proposal_score_distribution", "miss_proposal_score_distribution",
                "ROC_AUC_score_to_pixel_any_hit", "PR_AUC_score_to_pixel_any_hit"],
            "auc_role": "DIAGNOSTIC_ONLY", "score_calibration_threshold_search": "NONE",
        },
        "selection_only_interpretation": {
            "loss_changed": "NO", "target_changed": "NO", "architecture_changed": "NO",
            "sigma_changed": "NO", "data_changed": "NO", "augmentation_changed": "NO",
            "optimizer_changed": "NO", "proposal_config_changed": "NO",
            "checkpoint_selection_changed": "YES",
        },
        "h2_standalone_localizer_evaluation_contract": {
            "population": "103 cases / 152 components",
            "required": ["proposal_count", "proposal_pixel_any_hit_precision", "proposal_bbox_any_hit_precision",
                         "tiny_recall90", "overall_recall90", "recall50", "any_overlap_recall", "mean_coverage",
                         "mean_proposal_union_area", "hard_Tiny", "global_empty", "multi_component",
                         "score_saturation_distribution", "size_stratified_coverage"],
            "proposal_threshold_tuning": "NONE", "grid": "NONE",
        },
        "downstream_evaluation_contract": {
            "segmentation_checkpoints": ["unet", "attention_unet", "unetpp", "deeplabv3plus"],
            "global_cache": "same GLOBAL cache where provenance remains valid",
            "variant": "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED",
            "fusion": "unchanged",
            "crop_restore": "square/padding-correct", "margin": 0.20, "nms_iou": 0.30,
            "segmentation_threshold": 0.5,
            "r1_selective_acceptance_carried_over": "NO",
            "primary_downstream_policy": "localizer native frozen proposal policy (threshold 0.10, top_k 5)",
            "rationale": "H2A must isolate checkpoint selection; it must NOT be combined with H1 selectivity",
        },
        "prospective_evidence_dimensions": {
            "A_LOCALIZER_PROPOSAL_QUALITY": ["proposal_pixel_any_hit_precision", "tiny_recall90",
                                             "overall_recall90", "score_separability_saturation"],
            "B_DOWNSTREAM_GLOBAL_PRESERVATION": ["Dice", "IoU", "precision", "recall", "FP_burden",
                                                 "FN_burden", "cases_improved_worsened"],
            "C_REGIONAL_UTILITY": ["component_recoveries", "component_losses", "empty_recoveries",
                                   "oracle_benefit_retention"],
            "D_CROSS_ARCHITECTURE_GENERALITY": ["all four segmentation architectures"],
            "numerical_success_threshold": "NONE", "weighted_downstream_score": "NONE",
            "model_ranking": "NONE", "winner": "NONE",
        },
        "h2a_outcome_space": ["H2A_SELECTION_REDESIGN_SUFFICIENT", "H2A_SELECTION_REDESIGN_PARTIAL",
                              "H2A_SELECTION_REDESIGN_INSUFFICIENT", "CHECK_REQUIRED"],
        "adjudicated_now": "NO",
        "if_h2a_insufficient": "loss/target/representation redesign MAY become eligible later; NOT automatically authorized",
        "training_notebook_requirement": {
            "applies_if_mode_b_authorized": "YES",
            "must_display": ["epoch", "train_loss", "val_loss", "P", "T", "O", "deployment_balance_hmean",
                             "proposal_count", "mean_roi_area", "checkpoint_tuple", "is_new_best", "bad_epochs"],
            "one_completed_epoch_per_row": "YES", "untruncated": "YES",
        },
        "scientific_change_register": [{
            "id": "CHANGE_H2A_001", "field": "checkpoint selection",
            "old": OLD_TUPLE, "new": NEW_TUPLE,
            "motivation": ("Phase13 + H1 show recall-first selection yields useful target recovery but unacceptable "
                           "off-target intervention / downstream FP burden, while acceptance-only mitigation is "
                           "insufficient. No causal claim is made."),
        }],
        "claim_limits": {
            "new_numerical_success_threshold": "NONE", "hidden_grid": "NONE",
            "downstream_metric_in_selection": "NO", "phase12_oracle_in_selection": "NO",
            "r1_outcome_in_selection": "NO", "test_or_external_access": "NONE",
            "selection_redesign_will_succeed_asserted": "NO",
        },
        "counters": {"training": 0, "optimizer_construction": 0, "model_construction": 0,
                     "cuda_requests": 0, "localizer_forwards": 0, "segmentation_forwards": 0,
                     "regional_forwards": 0, "proposal_generation": 0, "checkpoint_writes": 0,
                     "test_reads": 0, "external_test_reads": 0},
        "continuity": {
            "phase13": "COMPLETE_FROZEN", "original_regional_gate": "REVISE_LOCALIZER_FROZEN",
            "h1": "CLOSED__PARTIAL_MITIGATION_INSUFFICIENT",
            "h2a_protocol": "COMPLETE_PASS_FROZEN",
            "h2a_execution": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED",
            "h2_loss_redesign": "NOT_STARTED", "h3_fusion_redesign": "NOT_STARTED",
            "phase14": "NOT_STARTED", "test": "UNTOUCHED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_H2A_EXECUTION_AUTHORIZATION",
    }
    (AUDITS / "post_phase13_h2a_protocol_frozen.json").write_text(
        json.dumps(proto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------- §20 protocol diff CSV ----------------
    F = "UNCHANGED"
    diff = [
        ("experiment_id", "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3",
         H2A_ID, "YES", "provenance / non-scientific"),
        ("TRAIN population", "770 FULL_FIELD / 1161 components", "770 FULL_FIELD / 1161 components", "NO", "data"),
        ("VAL population", "103 FULL_FIELD / 152 components", "103 FULL_FIELD / 152 components", "NO", "data"),
        ("ROI", "EXCLUDED", "EXCLUDED", "NO", "data"),
        ("manifest", "phase4_v3", "phase4_v3", "NO", "data"),
        ("taxonomy", "kub_size_clean_v3_v1", "kub_size_clean_v3_v1", "NO", "data"),
        ("input resolution", "512 x 512", "512 x 512", "NO", "architecture"),
        ("heatmap resolution", "128 x 128", "128 x 128", "NO", "architecture"),
        ("sigma", "0.75", "0.75", "NO", "target"),
        ("architecture", "compact KUB localizer (in=1,out=1,base=16)", "compact KUB localizer (in=1,out=1,base=16)", "NO", "architecture"),
        ("training target", "CenterNet-style heatmap target", "CenterNet-style heatmap target", "NO", "target"),
        ("loss", "CenterNetFocalLoss(alpha=2.0, beta=4.0)", "CenterNetFocalLoss(alpha=2.0, beta=4.0)", "NO", "objective"),
        ("optimizer", "AdamW", "AdamW", "NO", "optimisation"),
        ("learning rate", "1e-4", "1e-4", "NO", "optimisation"),
        ("weight decay", "1e-4", "1e-4", "NO", "optimisation"),
        ("scheduler", "CosineAnnealingLR(T_max=100)", "CosineAnnealingLR(T_max=100)", "NO", "optimisation"),
        ("batch size", "4", "4", "NO", "optimisation"),
        ("AMP", "accepted Phase13 semantics", "accepted Phase13 semantics", "NO", "optimisation"),
        ("seed", "42", "42", "NO", "reproducibility"),
        ("augmentation", "clean-v3 Phase13", "clean-v3 Phase13", "NO", "data"),
        ("max epochs", "100", "100", "NO", "optimisation"),
        ("workers", "0", "0", "NO", "execution"),
        ("CUDA", "required", "required", "NO", "execution"),
        ("TEST", "forbidden", "forbidden", "NO", "governance"),
        ("proposal threshold", "0.10", "0.10", "NO", "proposal"),
        ("proposal margin", "0.20", "0.20", "NO", "proposal"),
        ("proposal top_k", "5", "5", "NO", "proposal"),
        ("proposal NMS IoU", "0.30", "0.30", "NO", "proposal"),
        ("proposal grid", "none", "none", "NO", "proposal"),
        ("coverage semantics (primary)", "HISTORICAL_EXECUTING_BBOX_COVERAGE", "HISTORICAL_EXECUTING_BBOX_COVERAGE", "NO", "evaluation"),
        ("new primary proposal quantity", "not computed", "PROPOSAL_PIXEL_ANY_HIT_PRECISION", "YES", "evaluation (new metric, no gradient effect)"),
        ("primary checkpoint utility", "none (first term was tiny_recall90)",
         "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90", "YES", "checkpoint selection - PRIMARY SCIENTIFIC CHANGE"),
        ("checkpoint selection tuple", " ; ".join(OLD_TUPLE), " ; ".join(NEW_TUPLE), "YES", "checkpoint selection - PRIMARY SCIENTIFIC CHANGE"),
        ("checkpoint tuple length", "4", "6", "YES", "checkpoint selection"),
        ("checkpoint comparison", "strict lexicographic >", "strict lexicographic >", "NO", "checkpoint selection"),
        ("checkpoint ties", "BAD_EPOCH", "BAD_EPOCH", "NO", "checkpoint selection"),
        ("early stopping patience", "15", "15", "NO", "checkpoint selection"),
        ("latest.pt policy", "every completed epoch", "every completed epoch", "NO", "checkpointing"),
        ("best.pt policy", "strict improvement only", "strict improvement only", "NO", "checkpointing"),
        ("downstream segmentation metric in selection", "NO", "NO", "NO", "governance"),
        ("R1 selective acceptance carried into H2A", "n/a", "NO", "NO", "governance"),
    ]
    with (TABLES / "post_phase13_h2a_protocol_diff_vs_phase13.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["field", "phase13_value", "h2a_value", "changed", "scientific_role"])
        w.writerows(diff)

    # ---------------- §20 evidence contract CSV ----------------
    ev_rows = [
        ("A", "LOCALIZER_PROPOSAL_QUALITY", "proposal_pixel_any_hit_precision",
         "new primary quantity; numerator = proposals whose clipped native support contains >=1 native GT foreground pixel; denominator = all generated proposals over 103 VAL cases",
         "computed every epoch; participates in the primary selection tuple", "no threshold tuning"),
        ("A", "LOCALIZER_PROPOSAL_QUALITY", "tiny_recall90",
         "tiny-object coverage at 90% coverage threshold", "selection term 2", "bbox primary semantics; pixel secondary"),
        ("A", "LOCALIZER_PROPOSAL_QUALITY", "overall_recall90",
         "overall component coverage at 90% coverage threshold", "selection term 3", "bbox primary semantics; pixel secondary"),
        ("A", "LOCALIZER_PROPOSAL_QUALITY", "score_separability_and_saturation",
         "ROC-AUC / PR-AUC score->pixel-any-hit, plateau fraction, score IQR",
         "DIAGNOSTIC ONLY; structurally excluded from selection", "no calibration threshold search"),
        ("B", "DOWNSTREAM_GLOBAL_PRESERVATION", "Dice / IoU / precision / recall / FP / FN / cases improved-worsened",
         "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED vs GLOBAL_NATIVE on 103 VAL cases x 4 architectures",
         "evaluated after H2A localizer execution; NOT used in checkpoint selection", "no numerical success threshold"),
        ("C", "REGIONAL_UTILITY", "component_recoveries / component_losses / empty_recoveries / oracle_benefit_retention",
         "GLOBAL->PREDICTED recovery and loss on 152 components; RETENTION_DICE vs frozen Phase-12 oracle",
         "evaluated after H2A execution; NOT used in selection", "negative retention preserved unclipped"),
        ("D", "CROSS_ARCHITECTURE_GENERALITY", "UNet / Attention U-Net / UNet++ / DeepLabV3+",
         "same H2A localizer and same frozen segmentation checkpoints across all four architectures",
         "descriptive cross-architecture comparison", "no ranking, no winner"),
    ]
    with (TABLES / "post_phase13_h2a_evidence_contract.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["dimension_id", "dimension_name", "quantity", "definition", "role", "limitation"])
        w.writerows(ev_rows)

    print("score path verdict:", audit["verdict"])
    print("execution mode:", proto["execution_mode"])
    print("trajectory class:", traj["classification"], "| available epochs:", avail)
    print("history rows:", len(hist), "| collision:", proto["experiment_id_collision"])
    print("wrote 4 artifacts")
    return {"audit": audit, "proto": proto, "traj": traj}


if __name__ == "__main__":
    main()
