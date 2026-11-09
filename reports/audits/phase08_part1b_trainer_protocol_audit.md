# Phase 08 Part 1B — Trainer / Protocol Audit

**Status:** `PASS`  
**Model:** Gemini 3.1 Pro High  
**Generated:** 2026-09-20T06:27:14.769260+00:00

## Historical Phase-09 provenance

| Field | Value |
|---|---|
| experiment_id | `phase9_kub_unet_baseline_seed42_512` |
| checkpoint dir | `checkpoints/phase9_kub_unet_baseline_seed42_512` |
| primary config source | `configs/kub/unet_baseline.yaml` |
| config SHA | `9b8392f833c6f5350ae8780b24dae2afee1221e814f4517196e931ad169bce53` |
| checkpoint-embedded config == YAML | True |
| best checkpoint SHA | `a32d7fff1e019a179ef011795b6be8ee98ab548831f790a557726f32b38db8ec` |
| latest checkpoint SHA | `2b535401e7db95469b39a62bd6b6df51e0e298c32d00047465bc39ababd0ad61` |
| best epoch | 47 |
| latest epoch | 62 |
| best val macro dice | 0.7455300688743591 |
| early stopped | True |

## Phase-09 baseline set

| Phase | Model | Experiment ID | In Phase-09 clean rerun scope |
|---|---|---|---|
| 9 | unet | `phase9_kub_unet_baseline_seed42_512` | True |
| 10 | attention_unet | `phase10_kub_attention_unet_seed42_512` | False |
| 10 | unetpp | `phase10_kub_unetpp_seed42_512` | False |
| 10 | deeplabv3plus | `phase10_kub_deeplabv3plus_seed42_512` | False |

## Phase-10 cross-check

| Field | Phase 09 | Phase 10 | Same? | Material | Comment |
|---|---|---|---|---|---|
| input_resolution | 512 | 512 | same | False | identical |
| loss.name | bce_dice | bce_dice | same | False | identical |
| loss.bce_weight | 0.5 | 0.5 | same | False | identical |
| loss.dice_weight | 0.5 | 0.5 | same | False | identical |
| loss.dice_epsilon | 1e-06 | 1e-06 | same | False | identical |
| optimizer.name | AdamW | AdamW | same | False | identical |
| optimizer.learning_rate | 0.0001 | 0.0001 | same | False | identical |
| optimizer.weight_decay | 0.0001 | 0.0001 | same | False | identical |
| scheduler.name | CosineAnnealingLR | CosineAnnealingLR | same | False | identical |
| scheduler.max_epochs | 100 | 100 | same | False | identical |
| training.max_epochs | 100 | 100 | same | False | identical |
| training.early_stopping_patience | 15 | 15 | same | False | identical |
| training.threshold | 0.5 | 0.5 | same | False | identical |
| training.seed | 42 | 42 | same | False | identical |
| training.amp | True | True | same | False | identical |
| training.num_workers | 0 | 0 | same | False | identical |
| training.pin_memory | True | True | same | False | identical |
| augmentation.horizontal_flip_probability | 0.5 | 0.5 | same | False | identical |
| augmentation.rotation_degrees | 5.0 | 5.0 | same | False | identical |
| augmentation.brightness | 0.1 | 0.1 | same | False | identical |
| augmentation.contrast | 0.1 | 0.1 | same | False | identical |
| augmentation.vertical_flip | False | False | same | False | identical |
| preprocessing.strategy | aspect_ratio_resize_symmetric_pad | aspect_ratio_resize_symmetric_pad | same | False | identical |
| preprocessing.image_interpolation | bilinear | bilinear | same | False | identical |
| preprocessing.mask_interpolation | nearest | nearest | same | False | identical |
| model.input_channels | 1 | 1 | same | False | identical |
| model.output_channels | 1 | 1 | same | False | identical |
| model.base_channels | 32 | 32 | same | False | identical |
| training.monitor | val_macro_dice | val_macro_dice_true_per_image | different | False | different monitor STRING for the same metric ("val_macro_dice" vs "val_macro_dice_true_per_image"); naming only, no behavioural difference |
| loop.scheduler_step_after_val | True | True | same | False | identical |
| loop.strict_improvement | True | True | same | False | identical |
| loop.latest_saved_every_epoch | True | True | same | False | identical |
| loop.best_saved_on_improvement | True | True | same | False | identical |
| loop.nan_inf_guard | False | True | different | False | Phase-10 adds an explicit finite-value guard that raises; Phase-09 lacks it. Infrastructure improvement, not a scientific difference. |

## Contracts

### Checkpoint selection

| Item | Value | Source |
|---|---|---|
| metric | val_macro_dice | config + trainer.validate()["dice"] |
| direction | higher_is_better (max) | scripts/training/train_kub_baseline.py:183 |
| improvement_comparison | strict > | val_info["dice"] > best_val_dice |
| minimum_delta | nan | no delta configured |
| tie_handling | tie -> not improved; best.pt NOT overwritten | strict > semantics |
| best_checkpoint_semantics | written only on improvement | if improved: save best.pt |
| latest_checkpoint_semantics | written EVERY epoch | save latest.pt (unconditional) |
| selection_split | VAL only | trainer.validate requires VAL |
| test_usage | NEVER | verify_test_lock + allow_test=false |

### Early stopping

| Item | Value |
|---|---|
| implementation | src/training/trainer.py::EarlyStopping |
| patience | 15 |
| improvement_rule | score > best (strict) |
| no_improvement_rule | bad_epochs += 1 |
| tie_resets_counter | False |
| stop_condition | bad_epochs >= patience |
| minimum_delta | None |
| order_vs_checkpoint | early_stopping.update() then save latest/best, then stop check |
| order_vs_scheduler | scheduler.step() happens before the early-stop check |
| observed_final_state | {'best': 0.7455300688743591, 'bad_epochs': 15, 'patience': 15, 'stopped': True} |

### Scheduler

| Item | Value |
|---|---|
| type | CosineAnnealingLR |
| parameters | T_max=100 |
| step_frequency | per epoch |
| step_timing | after train_one_epoch AND after validate |
| metric_driven | False |
| resume_state_required | True |
| first_epoch_lr | initial lr (1e-4) |

### Resume

| Item | Value |
|---|---|
| resume_source | latest.pt |
| start_epoch | state["epoch"] + 1 |
| experiment_id | reused unchanged |
| manifest_guard_on_resume | manifest_version AND hashes must match |
| model_state | True |
| optimizer_state | True |
| scheduler_state | True |
| grad_scaler_state | True |
| epoch | True |
| best_metric | True |
| best_epoch | from best.pt epoch |
| early_stop_counter | True |
| history_continuity | True |
| global_step | True |
| rng_state | True |
| loader_generator_state | True |
| taxonomy_id | None |
| single_writer | implemented in src/utils/run_lock.py |

### Validation aggregation

| Example | per-image | macro | micro | macro == micro |
|---|---|---:|---:|---|
| two_images_equal_area_one_perfect_one_empty | 1.0, 0.0 | 0.500000 | 0.500000 | True |
| three_images_large_perfect_small_failure | 1.0, 1.0, 0.0 | 0.666667 | 0.952381 | False |
| all_perfect | 1.0, 1.0 | 1.000000 | 1.000000 | True |

## Resume-equivalence probe (INFRASTRUCTURE_TEST_ONLY)

- Device: cpu | steps: 6 | split at: 3
- Losses identical: **True** (max abs diff 0.000e+00)
- LR schedule identical: True
- Parameters identical: **True** (max abs diff 0.000e+00)
- Restored experiment_id: `phase08_resume_probe`
- Restored manifest_version: `phase4_v3`
- Restored taxonomy_id: `kub_size_clean_v3_v1`
- Scientific claim: **NONE**

## v2 → clean-v3 protocol diff

| Field | historical v2 | clean-v3 | Changed | Material | Reason |
|---|---|---|---|---|---|
| experiment_id | phase9_kub_unet_baseline_seed42_512 | phase9_kub_unet_baseline_seed42_512_clean_v3 | changed | False | new logical run id |
| architecture | standard_unet_4_stage | standard_unet_4_stage | same | False | preserved from historical protocol |
| model_key | unet | unet | same | False | preserved from historical protocol |
| input_channels | 1 | 1 | same | False | preserved from historical protocol |
| output_channels | 1 | 1 | same | False | preserved from historical protocol |
| base_channels | 32 | 32 | same | False | preserved from historical protocol |
| resolution | 512 | 512 | same | False | preserved from historical protocol |
| manifest_version | phase4_v2 | phase4_v3 | changed | False | authorized clean-v3 provenance |
| loss | bce_dice | bce_dice | same | False | preserved from historical protocol |
| loss_parameters | bce_weight=0.5, dice_weight=0.5, dice_epsilon=1e-06 | bce_weight=0.5, dice_weight=0.5, dice_epsilon=1e-06 | same | False | preserved from historical protocol |
| optimizer | AdamW | AdamW | same | False | preserved from historical protocol |
| learning_rate | 0.0001 | 0.0001 | same | False | preserved from historical protocol |
| weight_decay | 0.0001 | 0.0001 | same | False | preserved from historical protocol |
| scheduler | CosineAnnealingLR | CosineAnnealingLR | same | False | preserved from historical protocol |
| scheduler_parameters | T_max=100 | T_max=100 | same | False | preserved from historical protocol |
| scheduler_step_timing | per epoch, after train AND validation | per epoch, after train AND validation | same | False | preserved from historical protocol |
| batch_size | 4 | 4 | same | False | preserved from historical protocol |
| gradient_accumulation_steps | 1 | 1 | same | False | preserved from historical protocol |
| effective_batch_size | 4 | 4 | same | False | preserved from historical protocol |
| amp | True | True | same | False | preserved from historical protocol |
| seed | 42 | 42 | same | False | preserved from historical protocol |
| max_epochs | 100 | 100 | same | False | preserved from historical protocol |
| augmentation_policy | horizontal_flip(p=0.5), rotation(+-5.0 deg), brightness(+-0.1), contrast(+-0.1), vertical_flip=OFF | horizontal_flip(p=0.5), rotation(+-5.0 deg), brightness(+-0.1), contrast(+-0.1), vertical_flip=OFF | same | False | preserved from historical protocol |
| checkpoint_metric | val_macro_dice | val_macro_dice | same | False | preserved from historical protocol |
| checkpoint_mode | max (higher is better) | max (higher is better) | same | False | preserved from historical protocol |
| checkpoint_improvement_rule | strict > | strict > | same | False | preserved from historical protocol |
| early_stopping_patience | 15 | 15 | same | False | preserved from historical protocol |
| early_stopping_min_delta | None | None | same | False | preserved from historical protocol |
| prediction_threshold | 0.5 | 0.5 | same | False | preserved from historical protocol |
| validation_aggregation | macro (mean of per-image metrics); micro also reported | macro (mean of per-image metrics); micro also reported | same | False | preserved from historical protocol |
| val_shuffle | False | False | same | False | preserved from historical protocol |
| val_augmentation | False | False | same | False | preserved from historical protocol |
| num_workers | 0 | 0 | same | False | preserved from historical protocol |
| pin_memory | True | True | same | False | preserved from historical protocol |
| persistent_workers | False | False | same | False | preserved from historical protocol |
| gradient_clipping | None | None | same | False | preserved from historical protocol |
| source_config | configs/kub/unet_baseline.yaml | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| source_config_sha | 9b8392f833c6f5350ae8780b24dae2afee1221e814f4517196e931ad169bce53 | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| source_trainer | scripts/training/train_kub_baseline.py | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| source_trainer_sha | c1c97d0a19445550f69291539c0090b492f186a535000e5221e94d980be2ec27 | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| source_trainer_class | src/training/trainer.py | src/training/trainer.py | same | False | preserved from historical protocol |
| source_trainer_class_sha | 99189ce029aaeb43df7370b02d6f7e6de859d59310ca6b83bde4965ce27a49c3 | 99189ce029aaeb43df7370b02d6f7e6de859d59310ca6b83bde4965ce27a49c3 | same | False | preserved from historical protocol |
| checkpoint_best_sha | a32d7fff1e019a179ef011795b6be8ee98ab548831f790a557726f32b38db8ec | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| checkpoint_latest_sha | 2b535401e7db95469b39a62bd6b6df51e0e298c32d00047465bc39ababd0ad61 | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| protocol_status | VERIFIED | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| historical_role | Phase-09 baseline (training) | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| epochs_completed | 62.0 | <clean-v3 provenance> | changed | False | authorized provenance metadata |
| best_epoch | 47.0 | <clean-v3 provenance> | changed | False | authorized provenance metadata |

## Candidate clean-v3 configs

- Files: ['configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml']
- Status: **RECONSTRUCTED_AND_READY**
- Executed: False

## Test debt (not repaired)

| Test file | Observed | Disposition |
|---|---|---|
| `tests/test_phase14_part1.py` | HANGS (never completes) | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |
| `tests/test_predicted_roi.py` | 3 failures | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |
| `tests/test_kub_localizer.py` | 1 failure | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |

## Governance

- TEST content reads: 0
- Full scientific training performed: False
- Phase 09 started: False

## Phase-08 final gate

| Gate | Result |
|---|---|
| historical_protocol_reconstructed | PASS |
| no_material_source_disagreements | PASS |
| checkpoint_embedded_config_matches_yaml | PASS |
| phase09_baseline_set_identified | PASS |
| phase10_crosscheck_no_material_diff | PASS |
| validation_aggregation_explicit | PASS |
| checkpoint_selection_explicit | PASS |
| early_stopping_explicit | PASS |
| scheduler_timing_explicit | PASS |
| resume_restores_all_state | PASS |
| resume_same_experiment_id | PASS |
| resume_equivalence_probe_passed | PASS |
| single_writer_lock_implemented | PASS |
| config_placeholder_rejection | PASS |
| protocol_diff_no_material_change | PASS |
| candidate_config_ready | PASS |
| no_test_content_access | PASS |
| no_full_scientific_training | PASS |
| test_debt_documented | PASS |

**Overall: PASS**

## Table artifacts

| Table | SHA-256 |
|---|---|
| `phase08_phase09_checkpoint_artifact_provenance.csv` | `7527e6123962eb3994778da1fc70078049230cc6db43779de9bec9b110b233b5` |
| `phase08_phase09_historical_protocol_matrix.csv` | `3ffab9d43fcbd72d04f63cc8325f34a4eb2397948544c9e80cb53d52cc9ed141` |
| `phase08_phase09_phase_model_mapping.csv` | `7a0d9333bd917c9994dc6d9de6edb1df3fbee1118ff241ba115ef9f48959d29c` |
| `phase08_phase09_phase10_crosscheck.csv` | `fde37c6f347365005d168122f3372412f333662a4a84742a2acb694c40e859cd` |
| `phase08_validation_aggregation_contract.csv` | `2096b299fa2c1f314c1b771d670885587b3d7ecb7e6a15e22e1f53bfc5c5dec2` |
| `phase08_checkpoint_selection_contract.csv` | `8b8a92af17383d2ac9707ea9aaba73c77c7070843f7dc308ca25083a4228e062` |
| `phase08_early_stopping_contract.csv` | `3a63e2f0759465ef45e2ddd58b84b45ea19a2fc60a02d94b4770840b50f2d5ae` |
| `phase08_scheduler_contract.csv` | `3fa2376766b9004828e6b705fec988c37b9d6490e5c3ab0dcda7bef26a7138f3` |
| `phase08_resume_contract.csv` | `2235a0d342876869f0fa933f31ce456b09437356d344855240000055cce3cb1e` |
| `phase08_phase09_v2_to_clean_v3_protocol_diff.csv` | `7a5efadcb06a0be83b0b8f95b234f57289563c2641c6d44aee8ae6d7e050603c` |
| `phase08_phase09_clean_v3_candidate_configs.csv` | `9d5304abc7858408c540b5424984b2eb7459c97cbbac9350a37bba2eb53123fc` |
