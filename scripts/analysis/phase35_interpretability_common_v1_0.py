#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 interpretability shared contracts (frozen constants + contracts; NO execution).

Classification: PRE_EXECUTION_FEATURE_ATTRIBUTION_VISUAL_INTERPRETABILITY_SPECIFICATION__COMMON
Revision: ra_medfilm_barr_phase35_interpretability_v1_0

This module contains NO model construction, NO checkpoint loading, NO forward, NO backward and
NO raw-image access. Importing it never touches a checkpoint or the GPU.

Protected data: ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN throughout Phase35.
"""
from __future__ import annotations

from collections import OrderedDict

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0"
PHASE_ID = "phase_35_interpretability"
PHASE_TITLE = "Feature Attribution & Visual Interpretability"

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30_STATUS = "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL"

# --------------------------------------------------------------------------- #
# thresholds (NEVER conflated)
# --------------------------------------------------------------------------- #
T_ROI_PROPOSAL = 0.30
T_SEGMENTATION_OUTPUT = 0.50

# --------------------------------------------------------------------------- #
# evidence families
# --------------------------------------------------------------------------- #
EVIDENCE_FAMILIES = OrderedDict([
    ("I1", "FILM_PARAMETER_INTERPRETABILITY"),
    ("I2", "SEGMENTATION_GRADIENT_SALIENCY"),
    ("I3", "ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION"),
    ("I4", "BENEFIT_ROUTER_FEATURE_ATTRIBUTION"),
])
OUT_OF_SCOPE = [
    "performance reevaluation", "new statistical hypothesis testing", "failure mining",
    "robustness perturbation", "counterfactual model retraining", "TEST evaluation",
]

# --------------------------------------------------------------------------- #
# canonical components (verified from final authority)
# --------------------------------------------------------------------------- #
COMPONENTS = OrderedDict([
    ("G", OrderedDict([
        ("model_class", "GlobalMedFiLM"),
        ("source_file", "src/models/film/global_medfilm.py"),
        ("config_file", "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"),
        ("checkpoint", "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"),
        ("checkpoint_sha256",
         "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"),
        ("parameter_count", 3523001), ("role", "GLOBAL_SEGMENTER"),
    ])),
    ("R_psi", OrderedDict([
        ("model_class", "BARRRegionalRefinerV1"),
        ("source_file", "src/models/barr/regional_refiner.py"),
        ("checkpoint", "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt"),
        ("checkpoint_sha256",
         "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"),
        ("parameter_count", 1276401), ("role", "REGIONAL_REFINER"),
    ])),
    ("B_phi", OrderedDict([
        ("model_class", "BARRBenefitRouterV1"),
        ("source_file", "scripts/analysis/train_phase25d_router.py"),
        ("checkpoint", "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt"),
        ("checkpoint_sha256",
         "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b"),
        ("parameter_count", 36801), ("role", "BENEFIT_ROUTER"),
    ])),
    ("S_omega", OrderedDict([
        ("model_class", "BARRPostSafetyV1"),
        ("source_file", "scripts/analysis/phase25f_execution_common.py"),
        ("checkpoint", "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt"),
        ("checkpoint_sha256",
         "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e"),
        ("parameter_count", 1217), ("role", "POST_SAFETY"),
    ])),
])

# --------------------------------------------------------------------------- #
# FiLM contract (from GlobalMedFiLM authority)
# --------------------------------------------------------------------------- #
FILM_SITES = ("bridge", "decoder4", "decoder3", "decoder2", "decoder1")
FILM_SITE_CHANNELS = OrderedDict([("bridge", 256), ("decoder4", 192), ("decoder3", 96),
                                  ("decoder2", 48), ("decoder1", 24)])
TASK_COUNT = 4
DOMAIN_TASK_ID = OrderedDict([("ISIC", 0), ("BUSI", 1), ("KVASIR", 2), ("KUB", 3)])
G_TASK_EMBEDDING_DIM = 32
B_PHI_TASK_EMBEDDING_DIM = 16

FILM_PRIMARY_QUANTITIES = ["gamma per task/site/channel", "beta per task/site/channel",
                           "mean(gamma)", "mean(abs(gamma))", "std(gamma)", "L2 norm gamma",
                           "mean(beta)", "mean(abs(beta))", "std(beta)", "L2 norm beta"]
FILM_PAIRWISE_QUANTITIES = ["L2 distance gamma", "cosine similarity gamma",
                            "L2 distance beta", "cosine similarity beta"]
FILM_REUSE_NOTE = ("phase21_film_parameter_summary.csv persists per-(task,site,parameter) "
                   "SUMMARY statistics only (mean/std/min/max/l2_norm/mean_abs), NOT per-channel "
                   "vectors; pairwise task comparisons therefore require loading the canonical G "
                   "checkpoint and calling film_parameters_for_tasks() in the future execution "
                   "(no image forward required).")

# --------------------------------------------------------------------------- #
# Grad-CAM contract
# --------------------------------------------------------------------------- #
GRADCAM_LAYERS = OrderedDict([
    ("bridge", OrderedDict([
        ("semantic_location", "bridge output (post-FiLM bridge feature map)"),
        ("exact_module_path", 'film_layers["bridge"]'),
        ("output_shape_expected", [1, 256, 32, 32]),
        ("channel_count", 256),
        ("hook_mechanism", "forward hook capturing the module OUTPUT tensor"),
        ("source_line_provenance",
         "src/models/film/global_medfilm.py L193 self.bridge = ResidualBlock(c4, cb); "
         "L281 bridge = self.bridge(self.pool(skip4)); L284 bridge,_,_ = "
         "film_layers['bridge'](bridge, embedding); L194 MaxPool2d(2,2) x4 -> 512/16 = 32"),
    ])),
    ("decoder1_pre_head", OrderedDict([
        ("semantic_location",
         "final decoder1 feature representation before the shared segmentation head"),
        ("exact_module_path", 'film_layers["decoder1"]'),
        ("output_shape_expected", [1, 24, 512, 512]),
        ("channel_count", 24),
        ("hook_mechanism", "forward hook capturing the module OUTPUT tensor"),
        ("source_line_provenance",
         "src/models/film/global_medfilm.py L200 self.decoder1 = DecoderBlock(c2, c1, c1); "
         "L288 decoded = self.decoder1(decoded, skip1); L289 decoded,_,_ = "
         "film_layers['decoder1'](decoded, embedding); L290 logits = self.head(decoded)"),
    ])),
])

GRADCAM_ALGORITHM = OrderedDict([
    ("weights", "alpha_k = mean over spatial positions of dT/dA_k"),
    ("raw_cam", "CAM_raw = ReLU(sum_k alpha_k * A_k)"),
    ("upsample", "bilinear to 512x512"), ("align_corners", False),
    ("normalization",
     "if max(CAM)-min(CAM) > 0: CAM = (CAM-min)/(max-min) else CAM = all zeros"),
    ("persisted_dtype", "float32"),
    ("post_hoc_smoothing", False), ("gaussian_blur", False),
    ("threshold_chosen_after_viewing_results", False),
])

GRADCAM_TARGET = OrderedDict([
    ("mask", "M_pred = p_global >= 0.50 (from the already-frozen persisted canonical prediction)"),
    ("primary",
     "T = mean(current_forward_foreground_logit[M_pred]) if M_pred has >= 1 foreground pixel"),
    ("fallback",
     "T = mean(current_forward_foreground_logit over the full 512x512 field)"),
    ("is_ground_truth", False),
    ("recomputed_from_new_phase35_forward_for_target_selection", False),
    ("target_selected_after_viewing_saliency", False),
])

GRADCAM_EXECUTION_SEMANTICS = OrderedDict([
    ("classification", "GRADIENT_ENABLED_INTERPRETABILITY_DIAGNOSTIC_FORWARD"),
    ("model_eval", True), ("parameter_storage_dtype", "float32"),
    ("input_dtype", "float32"), ("task_id", "correct canonical task id"),
    ("torch_enable_grad", True), ("torch_inference_mode", False),
    ("autocast_policy",
     "match canonical G CUDA autocast(fp16) forward semantics while enabling gradients"),
    ("gradient_context_differs_from_canonical_no_grad_inference", True),
    ("bit_identical_phase30_numerical_reproduction_claimed", False),
    ("parameter_updates", 0), ("optimizer", None),
    ("backward_used_solely_for_attribution", True),
])

SALIENCY_SELF_CONSISTENCY = OrderedDict([
    ("primary_metrics", ["foreground_saliency_mass_fraction", "roi_saliency_mass_fraction"]),
    ("foreground_saliency_mass_fraction", "sum(CAM * M_pred) / sum(CAM)"),
    ("roi_saliency_mass_fraction", "sum(CAM * M_roi) / sum(CAM)"),
    ("zero_cam_policy", "both values NULL with explicit ZERO_CAM flag"),
    ("cam_peak_inside_predicted_foreground", "boolean"),
    ("cam_peak_inside_roi_proposal", "boolean"),
    ("entropy_or_concentration", "only if the exact definition is frozen in this specification"),
    ("entropy_definition_frozen", False),
    ("are_localization_accuracy_against_GT", False),
])

# --------------------------------------------------------------------------- #
# ROI / proposal contract
# --------------------------------------------------------------------------- #
ROI_CONTRACT = OrderedDict([
    ("roi_proposal_threshold", T_ROI_PROPOSAL),
    ("segmentation_threshold", T_SEGMENTATION_OUTPUT),
    ("derivation", "from the already-persisted global probability map"),
    ("panel_elements", ["original image", "global probability heatmap",
                        "predicted foreground at t_seg=0.50",
                        "ROI proposal mask at t_roi=0.30",
                        "ROI bounding box / crop geometry"]),
    ("ground_truth_required", False),
    ("conflate_segmentation_mask_proposal_mask_crop_box_final_regional_output", False),
])

# --------------------------------------------------------------------------- #
# router contract
# --------------------------------------------------------------------------- #
ROUTER_POPULATION = OrderedDict([
    ("population", "VAL808 (NON-HOLDOUT)"),
    ("n", 808),
    ("cache_root", "data_cache/phase29_val808_shared_fixed_g_v1_1_canonical"),
    ("deep_features", "val808_router_deep_features_f32.npy (808x192 f32)"),
    ("scalars", "val808_router_scalars_f32.npy (808x10 f32)"),
    ("global_probability", "val808_global_prob_f16.npy (808x512x512 f16)"),
    ("roi_geometry", "val808_roi_geometry.json"),
    ("router_holdout_rows", 0), ("test_rows", 0),
    ("raw_image_reads_for_router_attribution", 0), ("gt_reads", 0),
])

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
    ("method", "GRADIENT_X_INPUT"),
    ("baseline_required", False),
    ("target", "raw B_phi output delta_hat (no sigmoid)"),
    ("per_sample", "a_j = x_j * d(delta_hat)/d(x_j)"),
    ("persisted", ["signed attribution", "absolute attribution"]),
    ("group_signed", "sum_j in g of a_j"),
    ("group_absolute", "sum_j in g of abs(a_j)"),
    ("normalized_absolute_share", "absolute_group / sum over all numeric features of abs(a_j)"),
    ("zero_denominator_policy", "NULL shares with explicit ZERO_ROUTER_GRAD_ATTRIBUTION flag"),
    ("preprocessing", "exact canonical preprocessing/normalization entering B_phi"),
    ("feature_perturbation", False), ("retraining", False), ("optimization", False),
])

ROUTER_TASK_ID_POLICY = OrderedDict([
    ("numeric_input_gradient_applied_to_integer_task_ids", False),
    ("static_characterization",
     "learned 16-D B_phi task embeddings: norm, pairwise Euclidean distance, cosine similarity"),
    ("counterfactual_task_id_analysis", "INELIGIBLE_NOT_REQUIRED"),
])

# --------------------------------------------------------------------------- #
# gallery contract
# --------------------------------------------------------------------------- #
GALLERY_PATH = "reports/tables/phase21_gallery_selection_64.csv"
GALLERY_N = 64
GALLERY_PER_DOMAIN = 16
GALLERY_DISPLAY_PER_DOMAIN = 4
GALLERY_DISPLAY_N = 16
DISPLAY_RULE = ("lowest frozen gallery rank within each domain, first 4 per domain; if no frozen "
                "gallery rank exists, sample_id ascending, first 4 per domain")
DISPLAY_FORBIDDEN_SELECTION = ["Dice", "failure severity", "saliency appearance",
                               "router outcome", "visual attractiveness", "Grad-CAM quality"]

# --------------------------------------------------------------------------- #
# data access contract
# --------------------------------------------------------------------------- #
DATA_ACCESS = OrderedDict([
    ("future_max_raw_val_images", 64),
    ("future_val_gt_reads", 0),
    ("router_holdout_raw_images", "FORBIDDEN"),
    ("router_holdout_gt", "FORBIDDEN"),
    ("test_images", "FORBIDDEN"),
    ("test_gt", "FORBIDDEN"),
    ("train_raw_images", "NOT_REQUIRED"),
    ("primary_figures_require_ground_truth", False),
    ("optional_gt_overlay", "INELIGIBLE_NOT_REQUIRED"),
])

# --------------------------------------------------------------------------- #
# figure contract
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
OPTIONAL_FIGURES = OrderedDict([
    ("F8_optional", "regional/refiner panel ONLY if regional eligibility is established"),
])
OUTCOME_SELECTED_GALLERIES_FORBIDDEN = True

# --------------------------------------------------------------------------- #
# claim boundary
# --------------------------------------------------------------------------- #
CLAIM_TYPE = "DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE"
CLAIM_NOT_AUTOMATICALLY = ["causal explanation", "feature necessity", "feature sufficiency",
                           "clinical reasoning", "human-like reasoning",
                           "ground-truth localization accuracy", "proof of trustworthiness",
                           "proof that FiLM caused performance improvement",
                           "proof that router attribution identifies biological importance"]
REQUIRED_LANGUAGE = ["attribution", "model sensitivity", "saliency",
                     "association within the frozen model",
                     "self-consistency with model prediction/proposal"]
FORBIDDEN_CAUSAL_WORDING = ["the model made the decision because...",
                            "FiLM caused the performance gain...",
                            "this region is clinically important..."]

# --------------------------------------------------------------------------- #
# execution source paths
# --------------------------------------------------------------------------- #
EXECUTION_SCRIPT = "scripts/analysis/phase35_interpretability_execution_v1_0.py"
COMMON_MODULE = "scripts/analysis/phase35_interpretability_common_v1_0.py"
NOTEBOOK = ("notebooks/phasewise/phase_35_interpretability/"
            "phase35_interpretability_spec_v1_0_review.ipynb")
SPEC_DOC = "docs/phase35_interpretability_spec_v1_0.md"

TERMINAL = ("PHASE35_INTERPRETABILITY_SPEC_V1_0_COMPLETE__PHASE34_CANONICAL_HANDOFF_BOUND__"
            "FILM_TASK_EMBEDDING_GRAD_CAM_ROI_PROPOSAL_AND_ROUTER_ATTRIBUTION_EVIDENCE_"
            "CONTRACTS_FROZEN__FIXED_VAL_GALLERY_AND_NONHOLDOUT_ROUTER_POPULATION_GOVERNED__"
            "CLAIM_BOUNDARY_AND_SOURCE_FREEZE_COMPLETE__EXECUTION_ELIGIBILITY_DETERMINED_"
            "NOT_STARTED")
