"""Create all additive router-training specification artifacts (v1.2.1)."""
import json
from pathlib import Path

ROOT = Path("D:/Softfors/jup")
AUDITS = ROOT / "reports/audits"
AUDITS.mkdir(parents=True, exist_ok=True)

COMMON = {
    "phase": "25D",
    "classification": "PRE_EXECUTION_SPECIFICATION_COMPLETENESS_REPAIR",
    "router_training_spec_revision": "ra_medfilm_barr_router_training_v1_2_1",
    "method": "RA-MedFiLM-BARR",
    "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
    "generated_utc": "2026-10-01T02:01:22+00:00"
}

def save(name, data):
    path = AUDITS / name
    with open(path, "w") as f:
        json.dump(data, f, indent=1)
    print(f"Wrote {path.name}")

# ------------------------------------------------------------------
# 1. Router training spec completion (umbrella)
# ------------------------------------------------------------------
save("phase25d_router_training_spec_completion_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_router_training_spec_completion_v1_2_1",
    "purpose": "Additive completion of all fields previously absent from phase24_exact_implementation_spec.json#router",
    "carried_forward_unchanged": {
        "router_class": "BARRBenefitRouterV1",
        "input_dim": 218,
        "input_breakdown": {"deep_features": 192, "scalars": 10, "task_embedding": 16},
        "architecture": "Embedding(4,16) -> Linear(218,128) -> LayerNorm(128,elementwise_affine=True) -> SiLU -> Dropout(0.10) -> Linear(128,64) -> LayerNorm(64,elementwise_affine=True) -> SiLU -> Dropout(0.10) -> Linear(64,1)",
        "output": "Delta_hat_Dice (single unconstrained scalar)",
        "canonical_total_trainable_parameters": 36801,
        "loss": "Huber(delta=0.05, reduction='mean')",
        "optimizer": "AdamW(lr=1e-3, weight_decay=1e-4)",
        "batch_size": 128,
        "max_epochs": 200,
        "early_stopping_patience": 20,
        "scheduler_class": "ReduceLROnPlateau",
        "scheduler_base_params": {"mode": "min", "factor": 0.5, "patience": 8, "threshold": 1e-4, "threshold_mode": "rel", "cooldown": 0, "min_lr": 1e-6, "eps": 1e-8},
        "seed": 42,
        "target": "Phase25C delta_dice",
        "resource_cost_enters_delta_hat": False,
        "ROUTER_HOLDOUT_for_fitting_or_epoch_selection": False
    },
    "newly_frozen_fields": [
        "cv_fold_count",
        "cv_assignment_algorithm",
        "cv_group_key",
        "cv_stratification_key",
        "inner_split_rule",
        "checkpoint_selection_metric",
        "checkpoint_selection_direction",
        "checkpoint_tie_rule",
        "target_scaling",
        "feature_normalization_columns",
        "normalization_statistic_definition",
        "normalization_constant_behavior",
        "final_epoch_rule",
        "final_refit_seed",
        "final_refit_scheduler_monitor",
        "final_refit_early_stopping",
        "final_checkpoint_rule",
        "oof_prediction_rule",
        "fold_seed_derivation"
    ]
})

# ------------------------------------------------------------------
# 2. CV protocol
# ------------------------------------------------------------------
save("phase25d_cv_protocol_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_cv_protocol_v1_2_1",
    "cv_name": "BARR_ROUTER_CV5_GROUP_SAFE_DOMAIN_STRATIFIED_V1",
    "population": "ROUTER_DEVELOPMENT only, n=4957",
    "outer_folds": 5,
    "group_key": "canonical composite group_key from phase24_router_split_manifest.csv (PATIENT/ASSET/RISK/SINGLETON)",
    "group_key_is_model_input": False,
    "stratification_label": "domain only",
    "sort_before_split": ["domain", "group_key", "sample_id"],
    "algorithm": "sklearn.model_selection.StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)",
    "inputs": {"X": "dummy row indices", "y": "domain", "groups": "group_key"},
    "library_versions": {"python": "3.11.9", "numpy": "2.4.6", "scikit-learn": "1.9.1"},
    "outer_target_reserved_for": "OOF prediction only; must not influence checkpoint, scheduler, or early stopping",
    "requirements": {
        "each_sample_exactly_once": True,
        "router_cv_fold_domain": "{0,1,2,3,4}",
        "no_group_straddles_outer_folds": True,
        "all_four_domains_represented": "where mathematically possible",
        "no_target_derived_assignment": True
    }
})

# ------------------------------------------------------------------
# 3. Checkpoint selection contract
# ------------------------------------------------------------------
save("phase25d_checkpoint_selection_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_checkpoint_selection_contract_v1_2_1",
    "primary_metric": "EARLY_STOP mean Huber loss",
    "target": "raw delta_dice",
    "direction": "MINIMIZE",
    "aggregate": "sample-weighted mean over every EARLY_STOP sample",
    "current_loss_definition": "mean Huber loss across the complete EARLY_STOP population",
    "best_checkpoint_update_rule": "current_loss < best_loss - 1e-12",
    "tie_rule": "if abs(current_loss - best_loss) <= 1e-12, the EARLIER epoch remains selected; ties count as non-improvement for patience",
    "initial_best": "+infinity",
    "forbidden_metrics": ["MAE", "RMSE", "Pearson", "Spearman", "R2", "ROC-AUC", "PR-AUC", "beneficial_rate", "harmful_rate", "outer_target_metrics"]
})

# ------------------------------------------------------------------
# 4. Target contract
# ------------------------------------------------------------------
save("phase25d_target_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_target_contract_v1_2_1",
    "target": "raw Phase25C delta_dice",
    "dtype": "float32",
    "transformations": {
        "target_scaling": "NONE",
        "target_mean_centering": False,
        "target_standardization": False,
        "target_clipping": False,
        "target_winsorization": False,
        "target_log_transform": False,
        "target_rank_transform": False,
        "target_category_conversion": False
    },
    "huber_delta_applies_in": "Dice-difference units",
    "interpretability": "Delta_hat is predicted Dice change"
})

# ------------------------------------------------------------------
# 5. Feature normalization contract
# ------------------------------------------------------------------
save("phase25d_feature_normalization_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_feature_normalization_contract_v1_2_1",
    "deep_features": "192 features remain exactly as stored; NO normalization",
    "task_embedding": "16-D learned embedding remains raw; NO normalization",
    "standardized_scalars": [
        "entropy_proxy_mean",
        "frac_prob_within_0p05_of_boundary",
        "frac_prob_within_0p02_of_boundary",
        "mean_boundary_margin",
        "pred_foreground_fraction",
        "pred_foreground_pixels",
        "predicted_roi_area_fraction",
        "predicted_roi_side"
    ],
    "non_standardized_scalars": ["pred_roi_exists", "pred_empty"],
    "normalization_statistic": "population standard deviation (ddof=0)",
    "constant_column_behavior": "if sigma_j < 1e-12, record as CONSTANT_IN_FIT and set transformed value to 0.0 for all splits",
    "cv_normalization": "fit statistics ONLY on FIT_k; apply same mu/sigma to FIT_k, EARLY_STOP_k, OUTER_TARGET_k",
    "final_refit_normalization": "fit eight scalar means/stds on ALL 4957 ROUTER_DEVELOPMENT rows; persist in final checkpoint and standalone artifact",
    "holdout_statistics_forbidden": True
})

# ------------------------------------------------------------------
# 6. Final refit epoch contract
# ------------------------------------------------------------------
save("phase25d_final_refit_epoch_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_final_refit_epoch_contract_v1_2_1",
    "rule_name": "exact_median_of_five",
    "description": "After five outer CV runs, collect best_epoch_0..best_epoch_4 (selected by lowest EARLY_STOP Huber). Sort. Take sorted_epochs[2] = exact integer median of five values.",
    "forbidden": ["mean_epoch", "maximum_epoch", "minimum_epoch", "performance_weighted_epoch", "post_hoc_chosen_epoch"],
    "persist_before_final_training": True
})

# ------------------------------------------------------------------
# 7. Final refit seed contract
# ------------------------------------------------------------------
save("phase25d_final_refit_seed_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_final_refit_seed_contract_v1_2_1",
    "final_refit_seed": 42,
    "initialization": "FRESH from seed 42",
    "forbidden": ["initialize_from_any_CV_checkpoint", "averaged_CV_checkpoint", "best_performing_CV_fold", "router_selected_by_OOF_performance"],
    "task_embedding_initialization": "freshly initialized under the same seed"
})

# ------------------------------------------------------------------
# 8. Final refit scheduler contract
# ------------------------------------------------------------------
save("phase25d_final_refit_scheduler_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_final_refit_scheduler_contract_v1_2_1",
    "population": "ALL 4957 ROUTER_DEVELOPMENT rows",
    "validation_population": "NONE",
    "early_stopping": False,
    "fixed_epoch_count": "FINAL_ROUTER_EPOCHS (exact median of five best epochs)",
    "optimizer": "AdamW(lr=1e-3, weight_decay=1e-4)",
    "scheduler_class": "ReduceLROnPlateau",
    "scheduler_constructor": {"mode": "min", "factor": 0.5, "patience": 8, "threshold": 1e-4, "threshold_mode": "rel", "cooldown": 0, "min_lr": 1e-6, "eps": 1e-8},
    "scheduler_monitor": "FULL-EPOCH TRAINING HUBER LOSS",
    "monitor_definition": "sample-weighted mean Huber loss over every training example processed during that epoch",
    "scheduler_step_call": "scheduler.step(train_huber_epoch)",
    "scheduler_effects": "LR only; MUST NOT change FINAL_ROUTER_EPOCHS, trigger early stopping, or select a checkpoint",
    "final_checkpoint_rule": "LAST_FIXED_EPOCH",
    "forbidden": ["choose_best_training_loss_epoch_afterward", "use_validation_monitor", "use_holdout_monitor", "use_VAL808_monitor"]
})

# ------------------------------------------------------------------
# 9. Data-loader / randomness semantics
# ------------------------------------------------------------------
save("phase25d_data_loader_randomness_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_data_loader_randomness_contract_v1_2_1",
    "base_seed": 42,
    "fold_seed_derivation": "42000 + router_cv_fold",
    "fold_seed_uses": ["model initialization", "task embedding initialization", "training-shuffle generator"],
    "per_fold_fresh": ["model", "optimizer", "scheduler", "loader RNG"],
    "final_refit_seed": 42,
    "checkpoint_persistence_required": ["Python RNG state", "NumPy RNG state", "Torch CPU RNG state", "Torch CUDA RNG state", "DataLoader generator state"],
    "resume_restores_all": True,
    "no_retry_seed": True,
    "no_v2_seed": True
})

# ------------------------------------------------------------------
# 10. OOF prediction rule
# ------------------------------------------------------------------
save("phase25d_oof_prediction_contract_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_oof_prediction_contract_v1_2_1",
    "timing": "After a CV fold's checkpoint is frozen from EARLY_STOP loss",
    "procedure": "load best checkpoint; model.eval(); torch.inference_mode(); predict ONCE on OUTER_TARGET_k",
    "output": "delta_hat_oof",
    "must_not_modify": ["scheduler", "checkpoint", "epoch_choice", "normalization_stats", "model_parameters"],
    "concatenation": "five OUTER_TARGET predictions concatenated = 4957 OOF Delta_hat values",
    "execution_note": "This rule is frozen now but NOT executed during this repair"
})

# ------------------------------------------------------------------
# 11. CV / final refit hierarchy summary
# ------------------------------------------------------------------
save("phase25d_cv_final_refit_hierarchy_v1_2_1.json", {
    **COMMON,
    "artifact": "phase25d_cv_final_refit_hierarchy_v1_2_1",
    "hierarchy_text": "ROUTER_DEVELOPMENT(4957) -> OUTER CV 5 folds -> for each fold k: SOURCE_k = other 4 folds -> inner StratifiedGroupKFold(10) -> FIT_k (~90%) + EARLY_STOP_k (~10%). Checkpoint selected ONLY on EARLY_STOP_k. Frozen checkpoint predicts OUTER_TARGET_k once. Concatenate five OUTER_TARGET predictions = 4957 OOF Delta_hat. Collect five best epochs -> exact median = FINAL_ROUTER_EPOCHS. Fresh router seed=42, normalization on all DEV, train all 4957, fixed epoch count, scheduler monitors train Huber, final checkpoint = last fixed epoch.",
    "outer_fold_count": 5,
    "inner_fold_count": 10,
    "inner_early_stop_index": 0,
    "inner_fit_indices": "1-9"
})

print("All v1.2.1 specification artifacts written.")
