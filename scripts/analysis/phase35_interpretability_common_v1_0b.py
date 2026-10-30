#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0b interpretability shared contracts (frozen constants; NO execution).

Classification: PRE_EXECUTION_EXECUTABLE_INTERPRETABILITY_HARNESS_IMPLEMENTATION_AMENDMENT__
                NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0b

SUPERSEDES `phase35_interpretability_common_v1_0.py` for FUTURE EXECUTION (the v1.0 file is
preserved byte-for-byte as evidence of the pre-execution implementation defect).

This module contains NO model construction, NO checkpoint loading, NO forward, NO autograd and
NO raw-image access.

Protected data: ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN. Primary visual
execution may read ONLY the 64 authorized VAL gallery images and ZERO ground truth.
"""
from __future__ import annotations

from collections import OrderedDict

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0b"
PHASE_ID = "phase_35_interpretability"
PHASE_TITLE = "Feature Attribution & Visual Interpretability"

# --------------------------------------------------------------------------- #
# authority gates (verified BEFORE any raw image read)
# --------------------------------------------------------------------------- #
AUTHORITY_GATES = OrderedDict([
    ("phase34_final_closure", ("reports/audits/phase34_final_closure.json",
                               "00f975e71a1c4cdef606ab4324e0de226d66be2daa6cebe9f063cf0f2134d6da")),
    ("phase34_final_closure_check", ("reports/audits/phase34_final_closure_check.json",
                                     "1e89f313be39a2273a54337d15f4a273caf72f10ffdba60f6a876578a4691fd3")),
    ("phase34_phase35_handoff", ("reports/audits/phase34_phase35_handoff.json",
                                 "68e10f3e7964fce079785bcecfd79c34fc2ac6e6cb3ee1047c167d0be87e7710")),
    ("phase35_v1_0_specification_terminal",
     ("reports/audits/phase35_specification_terminal_v1_0.json",
      "cec3b2aadbc90a7a8ebd06e8149cd7a53122d42e3f6077c30634e7de96ac312b")),
    ("canonical_gallery", ("reports/tables/phase21_gallery_selection_64.csv",
                           "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9")),
])

# --------------------------------------------------------------------------- #
# thresholds (NEVER conflated)
# --------------------------------------------------------------------------- #
T_SEGMENTATION_OUTPUT = 0.50
T_ROI_PROPOSAL = 0.30
assert T_SEGMENTATION_OUTPUT != T_ROI_PROPOSAL
assert T_SEGMENTATION_OUTPUT == 0.50
assert T_ROI_PROPOSAL == 0.30

# --------------------------------------------------------------------------- #
# evidence families
# --------------------------------------------------------------------------- #
EVIDENCE_FAMILIES = OrderedDict([
    ("I1", "FILM_PARAMETER_INTERPRETABILITY"),
    ("I2", "SEGMENTATION_GRADIENT_SALIENCY"),
    ("I3", "ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION"),
    ("I4", "BENEFIT_ROUTER_FEATURE_ATTRIBUTION"),
])
OUT_OF_SCOPE = ["performance reevaluation", "new statistical hypothesis testing", "failure mining",
                "robustness perturbation", "counterfactual model retraining", "TEST evaluation"]

# --------------------------------------------------------------------------- #
# components: ONLY G and B_phi are executable for primary v1.0/v1.0b Phase35
# --------------------------------------------------------------------------- #
EXECUTABLE_COMPONENTS = ("G", "B_phi")
NON_EXECUTABLE_COMPONENTS = ("R_psi", "S_omega")

COMPONENTS = OrderedDict([
    ("G", OrderedDict([
        ("model_class", "GlobalMedFiLM"),
        ("source_file", "src/models/film/global_medfilm.py"),
        ("config_file",
         "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"),
        ("checkpoint", "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"),
        ("checkpoint_sha256",
         "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        ("parameter_count", 3523001), ("role", "GLOBAL_SEGMENTER"),
    ])),
    ("B_phi", OrderedDict([
        ("model_class", "BARRBenefitRouterV1"),
        ("source_file", "scripts/analysis/train_phase25d_router.py"),
        ("checkpoint", "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"),
        ("checkpoint_sha256",
         "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        ("parameter_count", 36801), ("role", "BENEFIT_ROUTER"),
        ("task_embedding_dim", 16),
    ])),
    ("R_psi", OrderedDict([
        ("model_class", "BARRRegionalRefinerV1"),
        ("checkpoint", "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"),
        ("checkpoint_sha256",
         "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
        ("parameter_count", 1276401), ("role", "REGIONAL_REFINER"),
    ])),
    ("S_omega", OrderedDict([
        ("model_class", "BARRPostSafetyV1"),
        ("checkpoint", "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"),
        ("checkpoint_sha256",
         "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
        ("parameter_count", 1217), ("role", "POST_SAFETY"),
    ])),
])

# --------------------------------------------------------------------------- #
# FiLM + task embedding
# --------------------------------------------------------------------------- #
FILM_SITES = ("bridge", "decoder4", "decoder3", "decoder2", "decoder1")
FILM_SITE_CHANNELS = OrderedDict([("bridge", 256), ("decoder4", 192), ("decoder3", 96),
                                  ("decoder2", 48), ("decoder1", 24)])
TASK_COUNT = 4
DOMAIN_TASK_ID = OrderedDict([("ISIC", 0), ("BUSI", 1), ("KVASIR", 2), ("KUB", 3)])
G_TASK_EMBEDDING_DIM = 32
B_PHI_TASK_EMBEDDING_DIM = 16
FILM_SUMMARY_QUANTITIES = ["mean", "mean_abs", "std", "l2_norm"]
FILM_PAIRWISE_QUANTITIES = ["gamma_l2_distance", "gamma_cosine_similarity",
                            "beta_l2_distance", "beta_cosine_similarity"]
SIGNIFICANCE_TESTS_PERFORMED = False

# --------------------------------------------------------------------------- #
# Grad-CAM
# --------------------------------------------------------------------------- #
GRADCAM_HOOKS = OrderedDict([
    ("bridge", OrderedDict([
        ("module_attribute", 'film_layers["bridge"]'),
        ("semantic_activation", "post-FiLM bridge representation"),
        ("expected_shape_batch1", [1, 256, 32, 32]), ("channels", 256),
    ])),
    ("decoder1", OrderedDict([
        ("module_attribute", 'film_layers["decoder1"]'),
        ("semantic_activation",
         "post-FiLM decoder1 representation immediately before shared segmentation head"),
        ("expected_shape_batch1", [1, 24, 512, 512]), ("channels", 24),
    ])),
])
GRADCAM_FORWARD_SEMANTICS = OrderedDict([
    ("model_eval", True), ("parameter_dtype", "float32"), ("input_dtype", "float32"),
    ("task_id_dtype", "int64"), ("torch_enable_grad", True),
    ("inference_mode_disabled", True), ("cuda_autocast_enabled", True),
    ("autocast_dtype", "float16"), ("no_grad_around_gradcam_forward", False),
    ("optimizer", None), ("optimizer_step_calls", 0), ("training_backward", False),
    ("gradient_mechanism", "torch.autograd.grad(T, [bridge_activation, decoder1_activation])"),
])
GRADCAM_ALGORITHM = OrderedDict([
    ("alpha", "spatial mean of dT/dA per channel"),
    ("cam_raw", "ReLU(sum_k alpha_k * A_k)"),
    ("upsample", "bilinear to 512x512"), ("align_corners", False),
    ("dtype", "float32"),
    ("normalization",
     "if max(CAM_raw)-min(CAM_raw) > 0: (CAM_raw-min)/(max-min) else all zeros"),
    ("gaussian_blur", False), ("morphology", False), ("smoothing", False),
    ("outcome_dependent_clipping", False), ("post_hoc_saliency_threshold", False),
])

# --------------------------------------------------------------------------- #
# persisted global prediction authority (contains a `gt` key -> must NOT be read)
# --------------------------------------------------------------------------- #
PREDICTION_ROOT = ("reports/predictions/phase21_global_medfilm_fourdomain_seed42_clean_v3/val")
PERSISTED_KEYS_ALLOWED = ("prob",)
PERSISTED_KEYS_FORBIDDEN = ("gt",)
PERSISTED_PROB_DTYPE = "float16"
TARGET_MASK_SOURCE = "PERSISTED_CANONICAL_PHASE21_VAL_GLOBAL_PROBABILITY"
TARGET_MASK_FROM_CURRENT_FORWARD_PROHIBITED = True
ROI_MASK_SOURCE = "PERSISTED_CANONICAL_PHASE21_VAL_GLOBAL_PROBABILITY"

# --------------------------------------------------------------------------- #
# gallery / display subset
# --------------------------------------------------------------------------- #
GALLERY_PATH = "reports/tables/phase21_gallery_selection_64.csv"
GALLERY_SHA256 = "2bc7c16286999ced374840cc987dcd352c3e546668322a9ccc4d1e8e8a097fd9"
GALLERY_N = 64
GALLERY_PER_DOMAIN = 16
MAX_RAW_VAL_IMAGE_READS = 64
DISPLAY_PER_DOMAIN = 4
DISPLAY_N = 16
DISPLAY_RULE = ("within each domain: if the authoritative gallery contains a frozen ranking "
                "field, select the lowest frozen gallery rank (first 4); else sort by sample_id "
                "ascending and take the first 4")
DISPLAY_FORBIDDEN_SELECTION = ["Dice", "router state", "saliency", "CAM magnitude",
                               "failure severity", "visual quality", "attribution magnitude"]

# --------------------------------------------------------------------------- #
# router authority
# --------------------------------------------------------------------------- #
ROUTER_CACHE_ROOT = "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical"
ROUTER_FILES = OrderedDict([
    ("deep_features", "val808_router_deep_features_f32.npy"),
    ("scalars", "val808_router_scalars_f32.npy"),
    ("global_probability", "val808_global_prob_f16.npy"),
    ("roi_geometry", "val808_roi_geometry.json"),
])
ROUTER_POPULATION_N = 808
ROUTER_HOLDOUT_ROWS = 0
ROUTER_TEST_ROWS = 0
ROUTER_RAW_IMAGE_READS = 0
ROUTER_GT_READS = 0
ROUTER_FEATURE_SCHEMA = "reports/tables/phase25b_feature_schema.csv"
ROUTER_FEATURE_SCHEMA_SHA = "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"
ROUTER_NORMALIZATION_AUTHORITY = "reports/tables/phase25d_final_normalization_stats.csv"
ROUTER_NORMALIZATION_AUTHORITY_SHA = \
    "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"
ROUTER_NORMALIZED_SCALAR_INDICES = [192, 193, 194, 195, 196, 197, 200, 201]
ROUTER_UNNORMALIZED_SCALAR_INDICES = [198, 199]
ROUTER_DEEP_FEATURE_DIM = 192
ROUTER_SCALAR_DIM = 10
ROUTER_TOTAL_DIM = 202
ROUTER_FEATURE_GROUPS = OrderedDict([
    ("bridge_global", 32), ("bridge_roi", 32), ("decoder2_global", 32),
    ("decoder2_roi", 32), ("decoder1_global", 32), ("decoder1_roi", 32),
])
ROUTER_SCALAR_FEATURES = [
    "entropy_proxy_mean", "frac_prob_within_0p05_of_boundary",
    "frac_prob_within_0p02_of_boundary", "mean_boundary_margin",
    "pred_foreground_fraction", "pred_foreground_pixels", "pred_roi_exists", "pred_empty",
    "predicted_roi_area_fraction", "predicted_roi_side",
]
ROUTER_ATTRIBUTION = OrderedDict([
    ("method", "GRADIENT_X_INPUT"), ("target", "raw B_phi output delta_hat"),
    ("sigmoid_applied", False), ("baseline_required", False),
    ("attribution", "a = x * grad"),
    ("gradient_mechanism", "torch.autograd.grad(delta_hat.sum(), x)"),
    ("task_id_numeric_gradient", False),
    ("persisted", ["signed attribution", "absolute attribution"]),
    ("zero_denominator_policy",
     "normalized_absolute_share_group = NULL with ZERO_ROUTER_GRAD_ATTRIBUTION = true; "
     "no epsilon denominator, no renormalization after excluding scalar groups"),
    ("feature_perturbation", False), ("retraining", False), ("optimization", False),
])
ROUTER_COUNTERFACTUAL_TASK_ID = "INELIGIBLE_NOT_REQUIRED"
ROUTER_SCORE_REPRODUCTION_TOLERANCE_FROZEN = True   # implemented and frozen, NOT run in v1.0b

# --------------------------------------------------------------------------- #
# figure contract (F1-F7 only; F8 regional resolved ineligible)
# --------------------------------------------------------------------------- #
FIGURES = OrderedDict([
    ("F1", "FiLM gamma heatmap by task x site/channel-summary"),
    ("F2", "FiLM beta heatmap by task x site/channel-summary"),
    ("F3", "task-embedding geometry matrix/heatmap"),
    ("F4", "fixed 16-case visual panel: image + predicted foreground + ROI proposal + "
           "bridge Grad-CAM + decoder1 Grad-CAM"),
    ("F5", "saliency self-consistency summary by domain/layer"),
    ("F6", "router attribution group summary"),
    ("F7", "router scalar-feature attribution summary"),
])
F8_REGIONAL_IMPLEMENTED = False
OUTCOME_SELECTED_PANELS_PERMITTED = False
ALL_64_AGGREGATES_MUST_INCLUDE_ALL_ELIGIBLE_SAMPLES = True

# --------------------------------------------------------------------------- #
# claim guard
# --------------------------------------------------------------------------- #
CLAIM_TYPE = "DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE"
ALLOWED_TERMINOLOGY = ["attribution", "model sensitivity", "saliency",
                       "association within the frozen model",
                       "self-consistency with model prediction/proposal"]
FORBIDDEN_CLAIM_TERMS = ["causal", "causality", "clinical reasoning", "biological importance",
                         "feature necessity", "feature sufficiency", "trustworthiness proof",
                         "ground-truth localization accuracy",
                         "FiLM caused performance improvement", "clinically important"]

# --------------------------------------------------------------------------- #
# execution modes
# --------------------------------------------------------------------------- #
MODES = ("smoke", "film", "gradcam", "router", "science")
SCIENTIFIC_MODES = ("film", "gradcam", "router", "science")
GATE_ENV = "PHASE35_EXECUTE"

TERMINAL = ("PHASE35_PREEXECUTION_SOURCE_AMENDMENT_V1_0B_COMPLETE__V1_0A_STATIC_PREFLIGHT_BLOCK_"
            "PRESERVED__EXECUTABLE_CANONICAL_G_AND_B_PHI_FILM_TASK_EMBEDDING_GRADCAM_ROI_AND_"
            "ROUTER_ATTRIBUTION_PATHS_IMPLEMENTED__PERSISTED_PGLOBAL_TARGET_AND_SEG050_ROI030_"
            "THRESHOLD_SEPARATION_BOUND__VAL64_AND_VAL808_DATA_GUARDS_FROZEN__ALL_ORIGINAL_STATIC_"
            "CHECKS_REPAIRED__V1_0B_SOURCE_FREEZE_COMPLETE__SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED")
