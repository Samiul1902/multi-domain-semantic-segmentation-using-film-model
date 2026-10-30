"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §11–§27.

Freeze every remaining execution-critical S_omega specification field:
  §11 architecture (F5) · §12 initialization · §13 normalization (F6)
  §14 CV manifest reuse (F7) · §15 seeds · §16 loss (F8) · §17 optimizer (F9)
  §18 scheduler (F10) · §19 checkpoint selection (F11) · §20 OOF predictions (F12)
  §21 decision threshold (F13) · §22 state machine (F14) · §23 fusion/fallback
  §24 final refit (F15) · §25 health/resume · §26 classifier reporting
  §27 Phase25G handoff

No model construction / training / forward pass / refinement / DeltaDice.

Outputs (reports/audits/):
  phase25f_architecture_contract_v1_0.json
  phase25f_normalization_contract_v1_0.json
  phase25f_cv_manifest_reuse_contract_v1_0.json
  phase25f_training_contract_v1_0.json
  phase25f_checkpoint_selection_contract_v1_0.json
  phase25f_decision_threshold_contract_v1_0.json
  phase25f_state_machine_contract_v1_0.json
  phase25f_final_refit_contract_v1_0.json
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

BASE = {"artifact": None, "phase": "25F", "method": C.METHOD,
        "specification_revision": C.REVISION}


def main() -> int:
    # ------------------------------------------------------------------ #
    # §11 architecture (ruling F5) + §12 initialization
    # ------------------------------------------------------------------ #
    p1 = 20 * 32 + 32
    p2 = 32 * 16 + 16
    p3 = 16 * 1 + 1
    total = p1 + p2 + p3
    assert total == C.EXPECTED_PARAM_COUNT, total
    arch = dict(BASE, artifact="phase25f_architecture_contract_v1_0",
                stage="SUPERVISOR_RULING_F5_BARRPOSTSAFETYV1",
                ruling_id="F5",
                class_name="BARRPostSafetyV1",
                input_dimension=20,
                layers=[
                    {"layer": 1, "op": "Linear", "in": 20, "out": 32,
                     "activation": "SiLU", "params": p1},
                    {"layer": 2, "op": "Linear", "in": 32, "out": 16,
                     "activation": "SiLU", "params": p2},
                    {"layer": 3, "op": "Linear", "in": 16, "out": 1,
                     "activation": None, "params": p3},
                ],
                architecture_string="Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)",
                absent_components=["LayerNorm", "BatchNorm", "Dropout",
                                   "residual connection", "attention",
                                   "task embedding", "second image encoder"],
                output="one RAW LOGIT",
                sigmoid_inside_model=False,
                inference_probability="p_accept = sigmoid(logit)",
                trainable_parameter_count=total,
                parameter_count_method="CLOSED_FORM_ARCHITECTURE_ARITHMETIC",
                module_instantiated=False,
                expected_parameter_count_closed_form=total,
                stop_if_measured_count_differs=True,
                initialization={
                    "equivalent_to": "standard PyTorch Linear initialization",
                    "weight": "kaiming_uniform_(a=sqrt(5))",
                    "bias": "Uniform(-bound, +bound), bound = 1/sqrt(fan_in)",
                    "custom_output_head_zero_init": False,
                    "controlled_by": "authorized execution seed",
                },
                activation_functions="SiLU (after Linear 20->32 and after Linear 32->16); "
                                     "none after the output Linear",
                normalization_layers="NONE (no LayerNorm, no BatchNorm)",
                dropout="NONE",
                output_dimension=1,
                output_interpretation="raw safety logit; sigmoid(logit) = P(ACCEPT_REFINEMENT)",
                all_pass=True)
    C.jdump(arch, C.AUD / "phase25f_architecture_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §13 normalization (ruling F6)
    # ------------------------------------------------------------------ #
    norm = dict(BASE, artifact="phase25f_normalization_contract_v1_0",
                stage="SUPERVISOR_RULING_F6_NORMALIZATION", ruling_id="F6",
                normalized_features="indices 0..15 (the 16 numeric features)",
                not_normalized_features="indices 16..19 (task one-hot)",
                statistics_source="FIT only, per CV fold",
                mu="mu_j = mean(FIT[:, j])",
                sigma="sigma_j = sqrt(mean((FIT[:, j] - mu_j)^2))  (population std, ddof=0)",
                zero_sigma_rule="if sigma_j < 1e-12 then transformed feature j = 0.0 "
                                "for FIT / EARLY_STOP / OUTER_TARGET",
                silent_epsilon_division=False,
                final_refit="statistics fit on all 4957 ROUTER_DEVELOPMENT rows",
                stats_persisted=True,
                model_forwards=0,
                all_pass=True)
    C.jdump(norm, C.AUD / "phase25f_normalization_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §14 CV manifest reuse (ruling F7)
    # ------------------------------------------------------------------ #
    man = pd.read_csv(C.PHASE25D_CV5_MANIFEST)
    man["sample_id"] = man["sample_id"].astype(str)
    folds = sorted(man["router_cv_fold"].unique().tolist())
    fold_sizes = man.groupby("router_cv_fold").size().to_dict()

    fold_binding = {}
    disjoint_ok = True
    union_ok = True
    group_safe = True
    for k in range(5):
        sets = {}
        for role in ("fit", "early_stop", "outer_target"):
            df = pd.read_csv(C.PHASE25D_CV_FOLD[k][role])
            df["sample_id"] = df["sample_id"].astype(str)
            sets[role] = df
            fold_binding[f"fold{k}_{role}"] = C.bind(C.PHASE25D_CV_FOLD[k][role])
        fit, es, ot = (set(sets["fit"]["sample_id"]),
                       set(sets["early_stop"]["sample_id"]),
                       set(sets["outer_target"]["sample_id"]))
        if fit & es or fit & ot or es & ot:
            disjoint_ok = False
        if len(fit) + len(es) + len(ot) != 4957:
            union_ok = False
        # outer_target must equal the manifest fold k membership
        if ot != set(man.loc[man["router_cv_fold"] == k, "sample_id"]):
            union_ok = False
        # group safety: outer_target groups must not appear in fit/early_stop
        g_ot = set(sets["outer_target"]["group_key"].astype(str))
        g_fe = set(sets["fit"]["group_key"].astype(str)) | set(
            sets["early_stop"]["group_key"].astype(str))
        if g_ot & g_fe:
            group_safe = False

    cv = dict(BASE, artifact="phase25f_cv_manifest_reuse_contract_v1_0",
              stage="SUPERVISOR_RULING_F7_REUSE_PHASE25D_CV", ruling_id="F7",
              invent_new_split=False,
              outer_manifest="reports/tables/phase25d_cv5_manifest.csv",
              outer_manifest_binding=C.bind(C.PHASE25D_CV5_MANIFEST),
              per_fold_role_manifests=fold_binding,
              reused_roles=["FIT", "EARLY_STOP", "OUTER_TARGET"],
              folds=folds,
              fold_sizes={int(k): int(v) for k, v in fold_sizes.items()},
              already_group_safe=group_safe,
              already_domain_aware=True,
              already_seed_frozen=True,
              already_target_independent=True,
              constructed_before_somega_exists=True,
              outer_target_never_used_for=["fitting", "normalization",
                                           "scheduler monitoring", "early stopping",
                                           "checkpoint selection"],
              disjointness_verified=disjoint_ok,
              partition_union_4957_verified=union_ok,
              group_leakage=0 if group_safe else 1,
              all_manifests_present=True,
              all_pass=bool(disjoint_ok and union_ok and group_safe),
              )
    C.jdump(cv, C.AUD / "phase25f_cv_manifest_reuse_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §16/§17/§18/§20/§25/§26/§27 + §15 seeds  -> training contract
    # ------------------------------------------------------------------ #
    train = dict(BASE, artifact="phase25f_training_contract_v1_0",
                 stage="SUPERVISOR_RULINGS_F8_F9_F10_TRAINING",
                 ruling_ids=["F8", "F9", "F10"],
                 seeds={
                     "scientific_master_seed": C.MASTER_SEED,
                     "somega_cv_execution_seeds": C.SOMEGA_CV_SEEDS,
                     "final_refit_seed": C.FINAL_REFIT_SEED,
                     "derived_fold_seeds_are_execution_seeds_only": True,
                 },
                 loss={
                     "class": "BCEWithLogitsLoss",
                     "ruling": "F8",
                     "target_dtype": "float32",
                     "target_values": [0, 1],
                     "reduction": "mean",
                     "class_weighting": "NONE",
                     "pos_weight": "NONE",
                     "label_smoothing": "NONE",
                     "focal_loss": False,
                     "balanced_bce": False,
                     "class_oversampling": False,
                     "minority_retuning_allowed": False,
                 },
                 optimizer={
                     "name": "AdamW", "ruling": "F9",
                     "lr": C.LR, "weight_decay": C.WEIGHT_DECAY,
                     "batch_size": C.BATCH_SIZE, "max_epochs": C.MAX_EPOCHS,
                     "early_stopping_patience": C.PATIENCE,
                     "amp": False, "training_dtype": "float32",
                     "hyperparameter_sweep": False,
                 },
                 scheduler={
                     "class": "ReduceLROnPlateau", "ruling": "F10",
                     "constructor": {"mode": "min", "factor": 0.5, "patience": 8,
                                     "threshold": 1e-4, "threshold_mode": "rel",
                                     "cooldown": 0, "min_lr": 1e-6, "eps": 1e-8},
                     "per_cv_epoch_order": [
                         "train FIT",
                         "evaluate complete EARLY_STOP",
                         "compute mean EARLY_STOP BCE",
                         "checkpoint decision",
                         "atomically persist history/checkpoint state",
                         "scheduler.step(early_stop_bce)",
                         "update early-stop patience",
                     ],
                     "outer_target_monitoring": False,
                     "controls": "LR only",
                 },
                 oof_predictions={
                     "ruling": "F12",
                     "rule": "after each fold's best checkpoint is frozen, predict exactly once "
                             "on that fold's OUTER_TARGET",
                     "persisted": ["p_accept_oof", "safety_logit_oof"],
                     "mode": "model.eval() + torch.inference_mode()",
                     "only_eligible_for": "Phase25G development A7/A8 evaluation",
                     "final_model_in_sample_for_development_claims": False,
                 },
                 training_health_resume={
                     "atomic_checkpoint_writes": True,
                     "atomic_history_writes": True,
                     "full_rng_state_persistence": True,
                     "full_rng_restoration": True,
                     "optimizer_state_restoration": True,
                     "scheduler_state_restoration": True,
                     "dataloader_generator_state_restoration": True,
                     "host_interruption_may_resume_same_logical_run": True,
                     "forbidden_retry_names": ["_retry", "_v2", "_fix", "_new"],
                 },
                 classifier_reporting={
                     "ruling": "classifier-level only",
                     "metrics": ["BCE", "ROC-AUC", "PR-AUC", "balanced accuracy", "accuracy",
                                 "precision", "recall/sensitivity", "specificity", "F1",
                                 "Brier score"],
                     "at_fixed_threshold": "p_accept >= 0.50",
                     "breakdowns": ["overall", "by domain", "by CV fold"],
                     "metric_class": "POST_SAFETY_TARGET_PREDICTION_METRICS",
                     "not": ["A7-vs-A8 segmentation results", "preservation proof",
                             "final system validation"],
                     "threshold_tuning_follows": False,
                 },
                 phase25g_handoff={
                     "deliverables": [
                         "five OOF safety prediction folds",
                         "4957 merged OOF p_accept",
                         "fixed 0.50 safety decisions",
                         "final S_omega checkpoint",
                         "final all-DEV normalization",
                         "fusion/fallback implementation",
                         "Phase25E frozen memberships / thresholds",
                         "Phase25A final refiner",
                         "global fallback contract",
                     ],
                     "phase25g_owns_first_integrated_evaluation": [
                         "A7 vs A8", "C8 vs C9", "segmentation preservation",
                         "post-safety rejection of harmful refinements",
                         "domain preservation", "integrated resource/preservation tradeoff"],
                     "phase25f_performs_comparison": False,
                 },
                 somega_training_example_construction=(
                     "one example per ROUTER_DEVELOPMENT sample (4957 rows); input = the frozen "
                     "20-D GT-free vector; label = safety_target from the canonical Phase25C OOF "
                     "delta_dice; CV membership = the frozen Phase25D five-fold identity manifests"),
                 post_refinement_feature_availability=(
                     "all 16 numeric features derive from already-computed post-refinement "
                     "quantities (P_g global crop, P_r OOF refined crop) plus two frozen "
                     "Phase25B pre-refinement ROI-geometry scalars; no GT and no refiner "
                     "hidden feature maps"),
                 model_constructed=False, training_runs=0, forward_passes=0,
                 test_reads=0, all_pass=True)
    C.jdump(train, C.AUD / "phase25f_training_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §19 checkpoint selection (ruling F11)
    # ------------------------------------------------------------------ #
    ckpt = dict(BASE, artifact="phase25f_checkpoint_selection_contract_v1_0",
                stage="SUPERVISOR_RULING_F11_CHECKPOINT_SELECTION", ruling_id="F11",
                primary_metric="EARLY_STOP mean BCEWithLogits loss",
                direction="MINIMIZE",
                update_rule="update best iff current_loss < best_loss - 1e-12",
                tie_rule="if abs(current_loss - best_loss) <= 1e-12 the earlier epoch remains "
                         "selected; a tie counts as non-improvement",
                forbidden_selection_metrics=["accuracy", "balanced accuracy", "AUROC",
                                             "PR-AUC", "precision", "recall", "specificity",
                                             "F1"],
                descriptive_only_metrics=["accuracy", "balanced accuracy", "AUROC", "PR-AUC",
                                          "precision", "recall", "specificity", "F1"],
                patience=C.PATIENCE,
                model_forwards=0, all_pass=True)
    C.jdump(ckpt, C.AUD / "phase25f_checkpoint_selection_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §21 decision threshold (ruling F13)
    # ------------------------------------------------------------------ #
    thr = dict(BASE, artifact="phase25f_decision_threshold_contract_v1_0",
               stage="SUPERVISOR_RULING_F13_SOMEGA_DECISION_THRESHOLD", ruling_id="F13",
               accept_rule="ACCEPT_REFINEMENT iff sigmoid(safety_logit) >= 0.50",
               equivalent_logit_rule="safety_logit >= 0.0",
               else_rule="FALLBACK_GLOBAL",
               constant_name="S_OMEGA_ACCEPT_PROBABILITY_THRESHOLD",
               value=0.50,
               distinct_from=[
                   {"role": "ROI proposal threshold", "value": 0.30},
                   {"role": "segmentation output threshold", "value": 0.50},
               ],
               numeric_equality_must_not_conflate_semantics=True,
               threshold_tuning=False, roc_threshold_selection=False, youden=False,
               f1_optimal=False, budget_dependent_safety_threshold=False,
               domain_specific_safety_threshold=False,
               model_forwards=0, all_pass=True)
    C.jdump(thr, C.AUD / "phase25f_decision_threshold_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §22 state machine (ruling F14) + §23 fusion/fallback
    # ------------------------------------------------------------------ #
    sm = dict(BASE, artifact="phase25f_state_machine_contract_v1_0",
              stage="SUPERVISOR_RULING_F14_PHASE25E_SKIP_INTERACTION", ruling_id="F14",
              states={
                  "STATE_A": {
                      "condition": "action_available = false",
                      "pre_gate": "FORCED_SKIP",
                      "refiner_executed": False,
                      "somega_executed": False,
                      "final": "GLOBAL",
                  },
                  "STATE_B": {
                      "condition": "action_available = true and Phase25E pre-gate says SKIP",
                      "refiner_executed": False,
                      "somega_executed": False,
                      "final": "GLOBAL",
                  },
                  "STATE_C": {
                      "condition": "Phase25E says EXECUTE",
                      "refiner_executes": True,
                      "candidate_fused_prediction_constructed": True,
                      "somega_features_computed": True,
                      "branch": {
                          "p_accept >= 0.50": {"outcome": "EXECUTE_THEN_ACCEPT",
                                               "final": "regional-fused candidate"},
                          "else": {"outcome": "EXECUTE_THEN_REJECT", "final": "GLOBAL"},
                      },
                  },
              },
              somega_never_changes="whether refinement was executed",
              somega_changes_only="which already-computed prediction is returned",
              fusion_fallback={
                  "if_accept": {"outside_frozen_roi": "p_final = p_global",
                                "inside_frozen_roi": "p_final = resized p_refined"},
                  "alpha_blending": False,
                  "learned_fusion": False,
                  "if_reject": "p_final = p_global everywhere",
                  "if_skip": "p_final = p_global everywhere",
                  "final_binary_segmentation": "p_final >= 0.50",
                  "roi_geometry_threshold": 0.30,
                  "threshold_role_substitution": False,
              },
              model_forwards=0, all_pass=True)
    C.jdump(sm, C.AUD / "phase25f_state_machine_contract_v1_0.json")

    # ------------------------------------------------------------------ #
    # §24 final refit (ruling F15)
    # ------------------------------------------------------------------ #
    refit = dict(BASE, artifact="phase25f_final_refit_contract_v1_0",
                 stage="SUPERVISOR_RULING_F15_FINAL_REFIT", ruling_id="F15",
                 inputs="best_epoch_0..best_epoch_4 from the five S_omega CV folds",
                 rule="FINAL_SAFETY_EPOCHS = sorted(best_epochs)[2] (exact integer median)",
                 fresh_model=True, model_class="BARRPostSafetyV1",
                 final_seed=C.FINAL_REFIT_SEED,
                 normalization="fit on all 4957 ROUTER_DEVELOPMENT features",
                 training_set="all 4957 samples",
                 epochs="exactly FINAL_SAFETY_EPOCHS",
                 validation=False, early_stopping=False,
                 optimizer="same AdamW",
                 scheduler="same ReduceLROnPlateau",
                 final_scheduler_monitor="full-epoch sample-weighted TRAIN BCE",
                 scheduler_controls="LR only",
                 final_checkpoint="LAST_FIXED_EPOCH",
                 select_earlier_training_loss_minimum=False,
                 model_constructed=False, training_runs=0, all_pass=True)
    C.jdump(refit, C.AUD / "phase25f_final_refit_contract_v1_0.json")

    print("contracts written: architecture, normalization, cv_manifest_reuse, training,")
    print("  checkpoint_selection, decision_threshold, state_machine, final_refit")
    print("param count:", total, "| cv disjoint:", disjoint_ok, "union:", union_ok,
          "group_safe:", group_safe)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
