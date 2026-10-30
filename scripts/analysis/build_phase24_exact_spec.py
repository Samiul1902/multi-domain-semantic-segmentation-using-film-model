"""Phase 24 — SPECIFICATION COMPLETENESS REPAIR (2/5).

Freeze the EXACT implementation specification: ROI constants, the exact regional refiner
architecture, the exact router architecture, feature taps, training protocols, the
cross-fit refit rule, the threshold/lambda policy, post-safety and fusion.

DESIGN ONLY. Parameter counts are CLOSED-FORM architecture arithmetic. NO module is
instantiated, NO forward pass, NO training, NO inference, NO outcome inspection.

Writes:
    reports/audits/phase24_exact_implementation_spec.json
    reports/audits/phase24_architecture_revision_v1_1.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/build_phase24_exact_spec.py
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
UTC = datetime.now(timezone.utc).isoformat()

OLD_NB = (ROOT / "notebooks/phasewise/phase_24_architecture_spec"
          / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
OLD_NB_SHA = "e4383d5ac9c33787b809407e4884cd7069f1f4514ed0abf7c21c844024221207"
PROTOCOL = AUD / "phase24_benefit_data_protocol_exact.json"


def j(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


# ===========================================================================
# CLOSED-FORM ARCHITECTURE ARITHMETIC (no module instantiation)
# ===========================================================================
def _gn(c: int) -> int:
    return 2 * c


def _conv(k: int, cin: int, cout: int, bias: bool = False) -> int:
    return k * k * cin * cout + (cout if bias else 0)


def _resblock(cin: int, cout: int) -> int:
    """Conv3x3 -> GN -> SiLU -> Conv3x3 -> GN -> add -> SiLU; 1x1 proj when cin != cout."""
    p = _conv(3, cin, cout) + _gn(cout) + _conv(3, cout, cout) + _gn(cout)
    if cin != cout:
        p += _conv(1, cin, cout)
    return p


def refiner_params(ch: list[int], dec_extra: bool = False) -> int:
    t = _conv(3, 4, ch[0]) + _gn(ch[0])      # stem: 4 -> ch[0]
    t += _resblock(ch[0], ch[0])             # stage-0 residual block
    for i in range(1, len(ch)):
        t += _resblock(ch[i - 1], ch[i])     # stage-i block (maxpool has no params)
    t += _resblock(ch[-1], ch[-1])           # bridge residual block
    cur = ch[-1]
    for s in ch[-2::-1]:                     # decoder: up x2, concat skip, residual block
        t += _resblock(cur + s, s)
        if dec_extra:
            t += _resblock(s, s)
        cur = s
    t += _conv(1, ch[0], 1, bias=True)       # 1x1 head to 1 logit channel
    return t


CH_PRIMARY = [16, 32, 64, 128, 192]
CH_FALLBACK = [16, 32, 64, 96, 128]
REFINER_PRIMARY_PARAMS = refiner_params(CH_PRIMARY)
REFINER_FALLBACK_PARAMS = refiner_params(CH_FALLBACK)
HARD_CEILING = 2_000_000
RECOMMENDED_MAX = 1_500_000

refiner_envelope_ok = REFINER_PRIMARY_PARAMS <= HARD_CEILING
# Deterministic pre-declared envelope reduction (documented BEFORE training).
refiner_active_channels = CH_PRIMARY if refiner_envelope_ok else CH_FALLBACK
refiner_active_params = (REFINER_PRIMARY_PARAMS if refiner_envelope_ok
                         else REFINER_FALLBACK_PARAMS)

# ---- router ----
ROUTER_TAPS = ["bridge", "decoder2", "decoder1"]
D_POOL_PER_TAP = 2            # global pool + ROI pool
D_SCALAR = 10                 # fixed scalar descriptors
D_TASK = 16                   # 4 tasks -> 16
D_TAP_FEATURES = None         # resolved below from the feature list
N_TAP_AXES = len(ROUTER_TAPS) * D_POOL_PER_TAP

# The pooled tap vectors are summaries, not raw channel counts: we freeze the tap
# summarisation to a FIXED width per tap-axis so the router input dim is closed-form.
POOL_WIDTH_PER_AXIS = 32       # fixed summary width per (tap, pool) axis
D_FEATURES = N_TAP_AXES * POOL_WIDTH_PER_AXIS + D_SCALAR + D_TASK


def mlp_params(d_in: int, h1: int, h2: int) -> int:
    p = d_in * h1 + h1                      # Linear(in,128) + LayerNorm(128)
    p += h1 * h2 + h2                       # Linear(128,64) + LayerNorm(64)
    p += h2 * 1 + 1                         # head Linear(64,1)
    return p


ROUTER_H1, ROUTER_H2 = 128, 64
ROUTER_PRIMARY_PARAMS = mlp_params(D_FEATURES, ROUTER_H1, ROUTER_H2)
ROUTER_MAX_PARAMS = 250_000
router_envelope_ok = ROUTER_PRIMARY_PARAMS <= ROUTER_MAX_PARAMS
# Deterministic hidden-size reduction exactly as §14 prescribes.
router_active_h1 = ROUTER_H1 if router_envelope_ok else 96
router_active_h2 = ROUTER_H2 if router_envelope_ok else 48
ROUTER_ACTIVE_PARAMS = mlp_params(D_FEATURES, router_active_h1, router_active_h2)

# ===========================================================================
# EXACT IMPLEMENTATION SPEC (§20)
# ===========================================================================
spec = {
    "artifact": "phase24_exact_implementation_spec",
    "phase": 24,
    "repair": "POST_PHASE24_SPECIFICATION_COMPLETENESS_REPAIR",
    "spec_version": "ra_medfilm_barr_narrowed_v1_1",
    "supersedes_only_incompleteness": True,
    "science_changed": False,
    "method_name": "RA-MedFiLM-BARR",
    "architecture_id": "ra_medfilm_barr_narrowed_v1_1",
    "supersedes_architecture_id": "ra_medfilm_barr_narrowed_v1",
    "purpose": ("freeze every remaining implementation degree of freedom BEFORE Phase 25 so "
                "Phase 25 cannot silently choose architecture or protocol based on observed "
                "performance"),
    "classification": "SPECIFICATION_COMPLETENESS_REPAIR",
    "not_architecture_search": True,
    "not_phase25_implementation": True,

    # ---------------- split ----------------
    "split_seed": 42,
    "split_algorithm_ref": "phase24_benefit_data_protocol_exact.json",
    "split_manifest_shas": {
        "phase24_router_split_manifest.csv": j(PROTOCOL).get("manifest_sha256"),
        "phase4_v3/train.csv": j(PROTOCOL).get("source_train_manifest_sha256"),
        "phase4_v3/val.csv": j(PROTOCOL).get("source_val_manifest_sha256"),
        "phase4_v3/test.csv": j(PROTOCOL).get("source_test_manifest_sha256"),
    },
    "split_development_n": j(PROTOCOL).get("development_n"),
    "split_holdout_n": j(PROTOCOL).get("holdout_n"),
    "split_zero_overlap": j(PROTOCOL).get("zero_overlap"),
    "split_val_overlap_zero": j(PROTOCOL).get("phase22_val_overlap_zero"),
    "split_test_overlap_zero": j(PROTOCOL).get("test_overlap_zero"),

    # ---------------- ROI (§5) ----------------
    "roi": {
        "predicted_foreground_threshold": 0.30,
        "expansion_factor": 1.50,
        "fractional_margin_equivalent": 0.25,
        "margin_constant_name": "ORACLE_DERIVED_REFINER_MARGIN",
        "margin_constant_value": 0.25,
        "margin_constant_source": "src/data/regional_dataset.py:22",
        "context_expansion_inherited_from": "Phase-22 regional geometry",
        "input_resolution": 256,
        "roi_rule": (
            "predicted foreground -> tight bbox -> center-preserving 1.50x expansion -> clip "
            "-> square pad -> resize to 256x256"
        ),
        "resize_modes": {
            "image": "bilinear",
            "probability_map": "bilinear",
            "gt_mask_training_target_only": "nearest",
        },
        "empty_prediction_behavior": "FORCED_SKIP",
        "gt_rescue": False,
        "train_val_sweep_over_roi_scale_in_primary": False,
        "reason_256": (
            "dedicated regional crop provides zoom; substantially lower incremental compute "
            "than another full 512 pass; consistent with the resource-aware goal; selected "
            "prospectively, NOT from performance. This is a DESIGN CHOICE, not a claim that "
            "256 is optimal."
        ),
        "resolution_ablation_status": "NOT_PART_OF_PRIMARY; must be pre-registered separately",
    },

    # ---------------- refiner (§6) ----------------
    "refiner": {
        "name": "BARRRegionalRefinerV1",
        "input_channels": 4,
        "input_channel_names": ["R", "G", "B", "p_global_crop"],
        "output_channels": 1,
        "output_kind": "logits",
        "input_resolution": 256,
        "encoder_bridge_channels_declared": CH_PRIMARY,
        "encoder_bridge_channels_active": refiner_active_channels,
        "architecture": {
            "encoder_resolution_transitions": 4,
            "bridge": True,
            "downsample": "max-pool 2x2 between encoder stages",
            "residual_block_per_encoder_stage": True,
            "residual_block_at_bridge": True,
            "decoder_upsample": "bilinear x2",
            "decoder_skip": "concatenate corresponding encoder skip",
            "residual_block_after_each_concatenation": True,
            "decoder_extra_second_residual_block": False,
            "head": "final 1x1 Conv2d to 1 logit channel (with bias)",
        },
        "residual_block_spec": (
            "Conv3x3 -> GroupNorm -> SiLU -> Conv3x3 -> GroupNorm -> residual addition -> SiLU"
        ),
        "conv_bias": "bias=False for convolutions followed by GroupNorm",
        "projection_shortcut": "1x1 Conv when input/output channels differ (bias=False)",
        "groupnorm_groups": "prefer 8 groups where channel count permits, otherwise the "
                            "largest divisor <= 8 chosen deterministically",
        "groupnorm_group_table": {str(c): (8 if c % 8 == 0 else max(
            [d for d in range(1, 9) if c % d == 0])) for c in set(refiner_active_channels)},
        "dropout": False,
        "attention": False,
        "se_blocks": False,
        "transformer": False,
        "deep_supervision": False,
        "pretrained_weights": False,
        "foundation_model_component": False,
        "task_conditioning_film": False,
        "task_conditioning_reason": (
            "the refiner is not the novelty-bearing component and task_id already enters the "
            "benefit router; keeping R_psi simple reduces degrees of freedom. A task-conditioned "
            "refiner is a future controlled ablation only."
        ),
        "loss": "0.5 * BCEWithLogits + 0.5 * soft Dice",
        "optimizer": "AdamW",
        "lr": 1e-4,
        "weight_decay": 1e-4,
        "scheduler": "cosine annealing",
        "max_epochs": 100,
        "early_stopping_patience": 15,
        "batch_size": 8,
        "amp": "enabled when supported by the training device",
        "seed": 42,
        "checkpoint_selection": "lowest validation loss (primary); Dice recorded as secondary "
                                "diagnostic only",
        "augmentation": "inherited SegmentationTransform(train=True) constants (see augmentation block)",
        "expected_parameter_count_closed_form": refiner_active_params,
        "expected_parameter_count_declared_channels": REFINER_PRIMARY_PARAMS,
        "parameter_count_method": "closed-form architecture arithmetic; no module instantiated",
        "hard_ceiling": HARD_CEILING,
        "recommended_envelope": [500_000, 1_500_000],
        "envelope_within_ceiling": refiner_active_params <= HARD_CEILING,
        "envelope_within_recommended": 500_000 <= refiner_active_params <= RECOMMENDED_MAX,
        "envelope_reduction_applied": not refiner_envelope_ok,
        "envelope_reduction_rule": (
            "declared channels [16,32,64,128,192] with one residual block per stage compute to "
            "2,317,553 params, which EXCEEDS the 2,000,000 hard ceiling. Before any training, "
            "and without consulting any outcome, the pre-declared deterministic reduction "
            "[16,32,64,96,128] (one residual block per stage) is adopted, giving 1,276,401 "
            "params - inside the recommended 0.5M-1.5M envelope. Channels may NOT be changed "
            "after observing performance."
        ),
        "envelope_reduction_alternatives_considered": {
            "[16,32,64,128,192] one_block": REFINER_PRIMARY_PARAMS,
            "[16,32,64,128,192] two_block": refiner_params(CH_PRIMARY, True),
            "[16,32,64,96,128] one_block": refiner_params(CH_FALLBACK),
            "[16,32,64,96,128] two_block": refiner_params(CH_FALLBACK, True),
        },
    },

    # ---------------- crossfit (§7, §10) ----------------
    "crossfit": {
        "outer_folds": 3,
        "within": "ROUTER_DEVELOPMENT",
        "assignment": "deterministic, group-safe, domain-stratified, seed 42",
        "inner_fitting_fraction": 0.90,
        "inner_early_stop_fraction": 0.10,
        "inner_split_rules": ["group-safe", "domain-stratified", "seed 42"],
        "inner_split_purpose": (
            "the held-out OOF fold may be used only for OOF prediction/label creation, never "
            "checkpoint selection; a nested TRAIN-INTERNAL 90/10 fitting/early-stop split is "
            "created inside each refiner-training portion so early stopping never touches the "
            "OOF target fold"
        ),
        "oof_fold_role": "UNTOUCHED until prediction, then used only for OOF gain labels",
        "oof_target_fold_never_used_for_checkpoint_selection": True,
        "infer_once_per_fold": True,
        "persist_provenance_and_checkpoint_sha": True,
        "no_training_on_fold_before_oof_produced": True,
        "executed_in_phase24": False,
    },

    # ---------------- final refiner (§11) ----------------
    "final_refiner": {
        "name": "R_psi_final",
        "refit_rule": (
            "after the three OOF refiner runs have produced gain labels, train ONE final "
            "regional refiner on ALL executable-action ROUTER_DEVELOPMENT samples"
        ),
        "data_allowed": "all executable-action ROUTER_DEVELOPMENT samples",
        "holdout_forbidden": True,
        "holdout_for_checkpoint_selection": False,
        "holdout_use": "integrated evaluation ONLY",
        "epoch_rule": (
            "reinitialize BARRRegionalRefinerV1 from seed 42 and train for exactly the median "
            "integer best epoch of the three OOF refiner runs (prospectively determined)"
        ),
        "early_stopping_on_holdout": False,
        "sole_regional_refiner_for": [
            "ROUTER_HOLDOUT integrated evaluation",
            "later continuity VAL evaluation",
            "future Phase 26+ development unless explicitly superseded",
        ],
        "arbitrary_fold_refiner_selection_forbidden": True,
    },

    # ---------------- router features (§12, §13) ----------------
    "router": {
        "name": "BARRBenefitRouterV1",
        "feature_taps": ROUTER_TAPS,
        "tap_spec": [
            "bridge global average pool",
            "bridge ROI-aware average pool",
            "decoder2 global average pool",
            "decoder2 ROI-aware average pool",
            "decoder1 global average pool",
            "decoder1 ROI-aware average pool",
        ],
        "pool_width_per_axis": POOL_WIDTH_PER_AXIS,
        "roi_pool_mapping": "ROI-aware average pool mapped to that feature grid",
        "second_global_forward": False,
        "trainable_conv_projection_before_pooling": False,
        "scalar_descriptors": [
            "entropy_proxy_mean",
            "frac_prob_within_0p05_of_boundary",
            "frac_prob_within_0p02_of_boundary",
            "mean_boundary_margin",
            "pred_foreground_fraction",
            "pred_foreground_pixels",
            "pred_roi_exists",
            "pred_empty",
            "predicted_roi_area_fraction",
            "predicted_roi_side",
        ],
        "n_scalar_descriptors": D_SCALAR,
        "task_conditioning": {
            "n_tasks": 4,
            "embedding_dim": 16,
            "task_id_mapping": {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3},
        },
        "normalization": "mean/std computed on ROUTER_DEVELOPMENT only for scalar continuous "
                         "descriptors",
        "normalization_stats_source": "ROUTER_DEVELOPMENT only",
        "normalization_from_holdout_val_test": "FORBIDDEN",
        "input_dim_closed_form": D_FEATURES,
        "input_dim_breakdown": {
            "tap_axes": N_TAP_AXES,
            "tap_axes_x_width": N_TAP_AXES * POOL_WIDTH_PER_AXIS,
            "scalars": D_SCALAR,
            "task_embedding": D_TASK,
        },
        "hidden_dimensions_declared": [ROUTER_H1, ROUTER_H2],
        "hidden_dimensions_active": [router_active_h1, router_active_h2],
        "architecture": (
            "Linear(input_dim,128) -> LayerNorm(128) -> SiLU -> Dropout(0.10) -> "
            "Linear(128,64) -> LayerNorm(64) -> SiLU -> Dropout(0.10) -> Linear(64,1)"
        ),
        "activation": "SiLU",
        "dropout": 0.10,
        "output": "Delta_hat_Dice (single continuous scalar)",
        "harm_head": "NOT part of the primary router; pre-registered extension only",
        "loss": "Huber loss, delta = 0.05",
        "loss_reason": "paired gain can contain extreme harmed/improved cases; Huber is robust "
                       "while preserving continuous-gain supervision",
        "optimizer": "AdamW",
        "lr": 1e-3,
        "weight_decay": 1e-4,
        "batch_size": 128,
        "max_epochs": 200,
        "early_stopping_patience": 20,
        "scheduler": "ReduceLROnPlateau(factor=0.5, patience=8, min_lr=1e-6)",
        "seed": 42,
        "epoch_selection": "deterministic 5-fold group-safe cross-validation inside "
                           "ROUTER_DEVELOPMENT OOF gain rows",
        "final_training": "B_phi_final trained on all eligible ROUTER_DEVELOPMENT gain rows for "
                          "the median selected epoch count",
        "holdout_for_fitting_or_epoch_selection": False,
        "expected_parameter_count_closed_form": ROUTER_ACTIVE_PARAMS,
        "expected_parameter_count_declared_hidden": ROUTER_PRIMARY_PARAMS,
        "parameter_count_method": "closed-form architecture arithmetic; no module instantiated",
        "max_parameters": ROUTER_MAX_PARAMS,
        "max_analytical_macs_fraction": 0.02,
        "preferred_analytical_macs_fraction": 0.01,
        "envelope_within_ceiling": ROUTER_ACTIVE_PARAMS <= ROUTER_MAX_PARAMS,
        "envelope_reduction_applied": not router_envelope_ok,
        "envelope_reduction_rule": (
            "if the fixed feature dimensionality causes >250k params, hidden dimensions are "
            "reduced deterministically 128->96 and 64->48 and documented before training; "
            "features are NEVER reduced based on outcome performance"
        ),
        "resource_cost_enters_delta_hat": False,
        "resource_cost_enters_utility_separately": True,
    },

    # ---------------- routing (§16) ----------------
    "routing": {
        "score": "score_i = Delta_hat_Dice_i",
        "budgets": ["0%", "10%", "25%", "50%", "100%"],
        "zero_percent": "global only",
        "hundred_percent": "all ACTION-AVAILABLE samples refine",
        "fixed_budget_routing": "thresholds from ROUTER_DEVELOPMENT score quantiles only",
        "threshold_source": "ROUTER_DEVELOPMENT quantiles only",
        "holdout_outcome_determines_threshold": False,
        "utility": "U_hat_i = Delta_hat_i - lambda * C_i",
        "lambda_grid": [0.0, 0.25, 0.5, 1.0],
        "lambda_searched_on_holdout_outcomes": False,
        "cost_definition": "normalized incremental analytical MAC cost",
        "cost_scale_derivation": "architecture arithmetic only, never outcome metrics",
        "single_universal_lambda_forbidden": True,
    },

    # ---------------- post-safety (§17) ----------------
    "post_safety": {
        "name": "BARRPostSafetyV1",
        "extension_status": "CONTROLLED_CORE_EXTENSION",
        "primary_evaluation_excludes_it": True,
        "primary_evaluation": "A7 / benefit + resource gate WITHOUT post-safety",
        "included_in": "A8",
        "saves_compute": False,
        "jfs_differentiation_required": True,
        "second_image_encoder": False,
        "inputs_from": "already-computed post-refinement quantities only",
        "feature_family_examples": [
            "global/refined probability summary difference",
            "foreground-area change",
            "component-count change",
            "mean probability change",
            "boundary-size change",
            "ROI geometry",
            "task_id",
        ],
        "gt_at_inference": False,
        "target": "ACCEPT iff DeltaDice > 0",
        "target_source": "OOF refinement predictions from ROUTER_DEVELOPMENT only",
        "architecture": "input -> 32 -> 16 -> 1 (sigmoid/logit)",
        "loss": "binary cross entropy",
        "holdout_training": False,
        "executed_in_phase24": False,
    },

    # ---------------- fusion (§18) ----------------
    "fusion": {
        "rule": "outside frozen ROI: p_final_candidate = p_global; inside frozen ROI: "
                "p_final_candidate = resized p_refined",
        "alpha_blending": False,
        "learned_fusion": False,
        "segmentation_threshold": 0.5,
        "segmentation_threshold_source": "INHERITED",
        "threshold_tuning": False,
    },

    # ---------------- action availability (§9) ----------------
    "action_availability": {
        "definition": "action_available_i = predicted ROI exists",
        "global_empty_action_available": False,
        "global_empty_pre_gate": "FORCED_SKIP",
        "global_empty_final": "global",
        "global_empty_included_in_integrated_evaluation": True,
        "global_empty_synthetic_gt_roi": False,
        "global_empty_fabricated_gain_target": False,
        "global_empty_excluded_from_regression_training_rows": True,
        "global_empty_report_label": "ACTION_UNAVAILABLE_GLOBAL_EMPTY",
        "purpose": "distinguish 'predicted negative benefit' from 'no legal refinement action exists'",
    },

    # ---------------- augmentation (§8) ----------------
    "augmentation": {
        "inherited_from": "src.data.transforms.SegmentationTransform(train=True)",
        "inherited_source_artifact": "src/data/transforms.py",
        "applied_consistently_to": ["RGB crop", "p_global crop", "GT mask geometry"],
        "inherited_constants": {
            "flip_probability": 0.5,
            "flip_axis": "horizontal (ImageOps.mirror)",
            "rotation_degrees": 5.0,
            "rotation_range": "continuous uniform(-5.0, +5.0)",
            "rotation_image_resample": "bilinear",
            "rotation_mask_resample": "nearest",
            "brightness": 0.1,
            "brightness_range": "uniform(1-0.1, 1+0.1)",
            "contrast": 0.1,
            "contrast_range": "uniform(1-0.1, 1+0.1)",
        },
        "additional_requested_operations": {
            "vertical_flip": "NOT_INHERITED (the inherited pipeline defines no vertical flip)",
            "90_degree_rotation_set": "NOT_INHERITED (the inherited pipeline uses continuous "
                                      "+/-5 degree rotation, not a {0,90,180,270} set)",
        },
        "inheritance_decision": (
            "Per the repair instruction, existing frozen Phase-20/21 augmentation constants are "
            "inherited EXACTLY rather than replaced with new invented operations. The inherited "
            "pipeline does not define vertical flip or 90-degree rotation, so those two "
            "operations are recorded as NOT_INHERITED and are NOT added to the primary refiner."
        ),
        "p_global_crop_consistency": "the p_global crop is transformed with the SAME geometric "
                                     "operations as the RGB crop (nearest resample for any "
                                     "mask-like/probability array)",
        "forbidden_for_primary": ["elastic deformation", "CutMix", "MixUp",
                                  "aggressive domain-specific augmentation"],
    },

    # ---------------- run policy (§19) ----------------
    "run_policy": {
        "one_authorized_primary_logical_run_per_fold_or_configuration": True,
        "seed": 42,
        "resume_counts_as_same_logical_run": True,
        "architecture_sweep": False,
        "lr_sweep": False,
        "hidden_size_sweep": False,
        "loss_sweep": False,
        "future_ablation_is_separate_named_experiment": True,
    },

    "forbidden_tuning_sources": [
        "ROUTER_HOLDOUT outcomes",
        "Phase-22 VAL outcomes",
        "TEST",
        "any outcome-driven feature selection",
        "any outcome-driven architecture or channel change",
        "any outcome-driven lambda or threshold selection",
    ],
    "no_architecture_search_allowed": True,
    "holdout_outcomes_read_in_phase24": 0,
    "val_outcome_reads_in_phase24": 0,
    "test_reads": 0,
    "training_runs": 0,
    "module_instantiations": 0,
    "forward_passes": 0,
    "phase25_started": False,
    "generated_utc": UTC,
}
(AUD / "phase24_exact_implementation_spec.json").write_text(
    json.dumps(spec, indent=1), encoding="utf-8")

# ===========================================================================
# ARCHITECTURE REVISION v1.1 (§21)
# ===========================================================================
revision = {
    "artifact": "phase24_architecture_revision_v1_1",
    "phase": 24,
    "architecture_id": "ra_medfilm_barr_narrowed_v1_1",
    "supersedes_architecture_id": "ra_medfilm_barr_narrowed_v1",
    "revision_reason": "SPECIFICATION_COMPLETENESS_ONLY",
    "method_name_unchanged": "RA-MedFiLM-BARR",
    "is_new_method": False,
    "science_changed": False,
    "historical_provenance_preserved": {
        "architecture_id": "ra_medfilm_barr_narrowed_v1",
        "artifact": "reports/audits/phase24_architecture_spec.json",
        "notebook_sha256": OLD_NB_SHA,
    },
    "exact_spec_ref": "reports/audits/phase24_exact_implementation_spec.json",
    "refiner_expected_params": refiner_active_params,
    "router_expected_params": ROUTER_ACTIVE_PARAMS,
    "governance_pointer_updated_to": "ra_medfilm_barr_narrowed_v1_1",
    "generated_utc": UTC,
    "test_reads": 0,
}
(AUD / "phase24_architecture_revision_v1_1.json").write_text(
    json.dumps(revision, indent=1), encoding="utf-8")

print("=== exact implementation spec frozen ===")
print(f"  refiner declared channels {CH_PRIMARY} -> {REFINER_PRIMARY_PARAMS:,} params "
      f"(ceiling {HARD_CEILING:,}) -> {'OK' if refiner_envelope_ok else 'EXCEEDS'}")
print(f"  refiner active channels   {refiner_active_channels} -> {refiner_active_params:,} params")
print(f"  router input dim          {D_FEATURES}")
print(f"  router declared hidden    [{ROUTER_H1},{ROUTER_H2}] -> {ROUTER_PRIMARY_PARAMS:,} params "
      f"(max {ROUTER_MAX_PARAMS:,}) -> {'OK' if router_envelope_ok else 'EXCEEDS'}")
print(f"  router active hidden      [{router_active_h1},{router_active_h2}] -> {ROUTER_ACTIVE_PARAMS:,} params")
print(f"  refiner within hard ceiling   : {refiner_active_params <= HARD_CEILING}")
print(f"  refiner within recommended    : {500_000 <= refiner_active_params <= RECOMMENDED_MAX}")
print(f"  router within 250k ceiling    : {ROUTER_ACTIVE_PARAMS <= ROUTER_MAX_PARAMS}")
print("  wrote phase24_exact_implementation_spec.json")
print("  wrote phase24_architecture_revision_v1_1.json")

assert refiner_active_params <= HARD_CEILING
assert ROUTER_ACTIVE_PARAMS <= ROUTER_MAX_PARAMS
