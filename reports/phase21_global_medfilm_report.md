# Phase 21 — GLOBAL MedFiLM Reference
## Four-domain task-conditioned global segmentation

**Report generated:** 2026-09-28T22:55:15.534209+00:00  
**Phase state:** `COMPLETE`  
**Terminal state:** `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED`

> **Scope guard.** Phase 21 is a **GLOBAL reference only**. It is **NOT** the final
> RA-MedFiLM-Seg++ model. It contains NO ROI proposal, NO localizer, NO regional refiner,
> NO high-resolution crop branch, NO global-regional fusion, NO benefit predictor, NO
> counterfactual refinement gain, NO resource/budget router, NO adaptive conditional
> computation, NO compression/pruning/quantization/distillation, NO architecture search,
> and NO TEST evaluation.

> **Interpretation guard.** There is **no architecture-matched control** (no identical plain
> model trained under this Phase-21 run). The only permitted phrasing is *"Global MedFiLM
> achieved X compared with baseline Y"*. Claiming *"FiLM caused +X"* is **forbidden**.
> Where a paired CI overlaps zero, the models are **not separable**.

## 1. At a glance

| Item | Value |
|---|---|
| Phase | 21 (Stage B) |
| Experiment ID | `phase21_global_medfilm_fourdomain_seed42_clean_v3` |
| Architecture ID | `global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1` |
| Model | ONE shared four-domain task-conditioned Global MedFiLM |
| Task conditioning | FiLM `F_hat = (1 + gamma(t)) * F + beta(t)` at 5 sites |
| Output | ONE shared 1x1 head -> single foreground logit (no dataset-specific head) |
| Parameters | 3,523,001 |
| Protocol | `reports/audits/phase20_shared_global_baseline_protocol.json` (frozen) |
| Protocol SHA-256 | `b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c` |
| Manifest | `phase4_v3` |
| Populations | TRAIN 5832 / VAL 808 |
| Selection rule | `phase20_macro_domain_mean_dice_v1` (frozen) |
| Cohorts read | TRAIN and VAL only |
| TEST | **CLOSED** — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Logical training runs | 1 (no architecture sweep, no hyperparameter sweep) |
| Canonical VAL inference runs | 1 |
| Phase 22 | ELIGIBLE_NOT_STARTED |

## 2. Fail-closed entry gate

**Verdict:** `PHASE21_ENTRY_GATE_PASS` — 15/15 checks passed, `training_may_start = True`

| Check | Passed | Detail |
|---|---|---|
| `phase19_complete` | True | {"phase_id": "19", "status": "COMPLETE"} |
| `phase20a_complete` | True | {"phase_id": "20", "status": "COMPLETE"} |
| `phase20b_complete` | True | {"phase_id": "20B", "status": "COMPLETE"} |
| `five_model_scientific_freeze_exists` | True | {"path": "reports/audits/phase20_five_model_baseline_benchmark_freeze.json", "te |
| `protocol_sha_matches_frozen_phase20` | True | {"repo_protocol_sha256": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17 |
| `train_population_5832` | True | {"rows": 5832} |
| `val_population_808` | True | {"rows": 808} |
| `test_remains_locked` | True | {"manifest_version": "phase4_v2", "test_sample_count": 1683, "full_test_sha256": |
| `test_reads_zero` | True | {"test_image_reads": 0, "test_mask_reads": 0, "test_inference": 0, "test_visuali |
| `four_task_ids_frozen` | True | {"manifest_mapping": {"KUB": 3, "KVASIR": 2, "ISIC": 0, "BUSI": 1}, "expected":  |
| `phase20b_canonical_notebook_exists` | True | {"path": "notebooks/phasewise/phase_20b_five_model_baselines/phase20b_five_model |
| `phase20b_reviewer_package_audit_pass` | True | {"coverage": 1.0, "all_visualized": true, "zero_tracebacks": true, "deterministi |
| `no_unresolved_leakage_blocker` | True | {"phase19": "REMEDIATED", "phase20_duplicate": "PHASE20_DUPLICATE_AUDIT_PASS__NO |
| `phase21_previously_not_started` | True | {"map_status": "ELIGIBLE_NOT_STARTED", "experiment_dir_exists": false, "checkpoi |
| `supervisor_authorization_present` | True | Explicit Phase-21 AUTHORIZATION in the supervisor instruction for this task |

Artifact: `reports/audits/phase21_entry_gate.json` · SHA `567093d222e9fc73...`

## 3. Data contract

| Domain | task_id | TRAIN | VAL | Modality |
|---|---|---|---|---|
| ISIC | 0 | 2556 | 357 | dermoscopy (RGB) |
| BUSI | 1 | 602 | 84 | ultrasound (L) |
| KVASIR | 2 | 696 | 87 | endoscopy (RGB) |
| KUB | 3 | 1978 | 280 | radiograph (L/RGB) |
| **Total** | | **5832** | **808** | |

`task_id` is `CONDITIONING_ALLOWED` but is **never** a channel, never concatenated to the
image, and never selects a dataset-specific head. The following are **never** model inputs:
`mask_path`, foreground fraction, `patient_id`, `case_id`, GT-derived metadata, KUB stone
`category` (Kidney/Ureteric/Bladder), object-size bin (TINY/SMALL/MEDIUM/LARGE), ROI
coordinates.

## 4. Protocol binding — Phase-20 inheritance

**Verdict:** `PHASE21_PROTOCOL_BINDING_PASS` · 24/24 inherited values identical · **unintentional differences = 0**

| Inherited field | Phase-20 protocol | Phase-21 | Identical |
|---|---|---|---|
| `manifest_version` | `"phase4_v3"` | `"phase4_v3"` | True |
| `task_ids` | `{"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}` | `{"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}` | True |
| `train_total` | `5832` | `5832` | True |
| `val_total` | `808` | `808` | True |
| `input_channel_policy` | `"RGB_3CH"` | `"RGB_3CH"` | True |
| `input_resolution` | `512` | `512` | True |
| `sampling_policy` | `"phase20_domain_balanced_uniform_v1"` | `"phase20_domain_balanced_uniform_v1"` | True |
| `loss` | `{"name": "bce_dice", "bce_weight": 0.5, "dice_` | `{"name": "bce_dice", "bce_weight": 0.5, "dice_` | True |
| `optimizer` | `{"name": "AdamW", "learning_rate": 0.0001, "we` | `{"name": "AdamW", "learning_rate": 0.0001, "we` | True |
| `learning_rate` | `0.0001` | `0.0001` | True |
| `weight_decay` | `0.0001` | `0.0001` | True |
| `scheduler` | `{"name": "CosineAnnealingLR", "T_max": 100, "s` | `{"name": "CosineAnnealingLR", "T_max": 100, "s` | True |
| `batch_size` | `4` | `4` | True |
| `eval_batch_size` | `8` | `8` | True |
| `num_workers` | `4` | `4` | True |
| `amp` | `true` | `true` | True |
| `seed` | `42` | `42` | True |
| `max_epochs` | `100` | `100` | True |
| `early_stopping_patience` | `15` | `15` | True |
| `checkpoint_selection_rule` | `"phase20_macro_domain_mean_dice_v1"` | `"phase20_macro_domain_mean_dice_v1"` | True |
| `evaluation_threshold` | `0.5` | `0.5` | True |
| `bootstrap` | `{"n_boot": 2000, "seed": 42, "alpha": 0.05, "u` | `{"n_boot": 2000, "seed": 42, "alpha": 0.05, "u` | True |
| `metrics_implementation` | `"src.metrics.evaluation_metrics"` | `"src.metrics.evaluation_metrics"` | True |
| `test_locks` | `0` | `0` | True |

### Declared intentional differences

| Field | Class | Reason |
|---|---|---|
| `architecture` | INTENTIONAL_ARCHITECTURAL | Phase 21 is the task-conditioned Global MedFiLM reference. The shared UNet++ architecture is replaced by the reconstructed historical GLOBAL MedFiLM (residual shared encoder-decoder + 5 FiLM sites + ONE shared head). |
| `experiment_id` | INTENTIONAL_IDENTITY | New phase, new experiment identity and new isolated output directories. |
| `model.input_channels_consumed` | INTENTIONAL_NO_CHANGE_DOCUMENTED | No change: the Phase-20 RGB_3CH channel policy is inherited EXACTLY. Listed here only to record that the legacy MedFiLM's 3-channel encoder first stage required no adapter. |
| `task_id_role` | INTENTIONAL_ARCHITECTURAL | The defining Phase-21 change: task_id is permitted as a CONDITIONING input only. It is never a channel, never concatenated to the image, never a separate head, and no mask-derived metadata enters the model. |
| `output_isolation` | INTENTIONAL_IDENTITY | Isolated output directories; no frozen artifact is overwritten. |

Artifact: `reports/audits/phase21_protocol_binding.json` · SHA `d86a6b04c080ddad...`

## 5. Legacy MedFiLM architecture audit

**Evidence status:** `PRIOR_ENGINEERING_EXPERIMENTAL_EVIDENCE` · historical results claimed as current: **False**

| Item | Value |
|---|---|
| Legacy FiLM module | `FeatureWiseLinearModulation` |
| Legacy model class | `MedFiLMSharedEncoderMultiTaskSegmenter` |
| FiLM equation | `F_hat = (1 + gamma(t)) * F + beta(t)` |
| gamma / beta | `gamma = tanh(gamma_raw)` / `beta = tanh(beta_raw)` |
| Identity at init | True |
| FiLM sites | ['bridge', 'decoder4', 'decoder3', 'decoder2', 'decoder1'] |
| Squeeze-and-Excitation | False |
| Deep supervision | False |
| External pretrained weights | False |
| Legacy domains | ['isic2018', 'busi', 'kvasir'] (no KUB) |

### Reuse classification

**Reuse-safe**

- FeatureWiseLinearModulation (equation, bounded tanh, zero-init identity)
- task_embedding nn.Embedding(task_count, dim) with normal_(0, 0.02) init
- 5-site FiLM insertion pattern (bridge, decoder4..decoder1)
- ResidualBlock / DecoderBlock topology (residual, no SE, no deep supervision)
- film_parameters_for_tasks() diagnostic accessor
- _validate_task_ids contract (shape [B], range-checked)

**Must NOT reuse**

- SparseSeedSegmentationLoss / CollapseResistantWeakSegmentationLoss (weak-label loss)
- weak_segmentation_dataset_v2 sparse 0/1..254/255 CAM-seed encoding
- per-task multi-class heads (Phase 21 requires ONE shared output definition)
- legacy weak-label image adapter / sparse-seed dataset (Phase 21 is fully supervised)
- legacy 3-domain task registry (Phase 21 is four-domain)
- legacy hyperparameters (256 px, batch 8, lr 3e-4, patience 12)

**Reference only**

- legacy global_config.json task-ID corroboration
- legacy metric-name vocabulary

### Files inspected

| Key | Path | SHA-256 |
|---|---|---|
| `medfilm_module` | `D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\medfilm_weak_segmentation_v2.py` | `64c4eb409b081a8d...` |
| `plain_topology` | `D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\plain_weak_segmentation_v2.py` | `47b604296880cdbf...` |
| `attention_unet_comparator` | `D:\Softfors\final\medfilm_seg_v2\src_v2\models_v2\attention_unet_weak_segmentation_v2.py` | `3ec86ce716612613...` |
| `legacy_global_config` | `D:\Softfors\final\medfilm_seg\configs\global_config.json` | `2ccad74762510f3b...` |
| `legacy_training_contract` | `D:\Softfors\final\medfilm_seg_v2\configs_v2\medfilm_weak_segmentation_training_contract_v2.json` | `d0bfc675e586b477...` |

### Recorded ambiguities

- Legacy FiLM sites operate on decoder feature maps only; no encoder-stage FiLM. Phase 21 preserves the 5-site decoder+bridge placement.
- Legacy output projection zero-init makes FiLM an exact identity at step 0; task conditioning therefore must be LEARNED. A weak conditioning effect at convergence is a possible outcome and must be reported honestly (CONDITIONING_EFFECT_WEAK), not hidden.
- Legacy embedding_dim=32 and film_hidden_dim=64 were tuned for a 3-domain weak-label problem; Phase 21 adopts them as the best-supported historical reference values and freezes them BEFORE training.
- Legacy task embedding init std 0.02 combined with zero-init FiLM output means the embedding gradient at step 0 is zero for gamma/beta; conditioning emerges after the output projection leaves zero.

Artifact: `reports/audits/phase21_legacy_medfilm_architecture_audit.json` · SHA `1c68656ee29ea96e...`

## 6. Frozen architecture (frozen BEFORE training)

**Verdict:** `PHASE21_ARCHITECTURE_FROZEN` · frozen before training: **True** · parameters: **3,523,001**

### FiLM conditioning

| Property | Value |
|---|---|
| mechanism | `FiLM (feature-wise linear modulation)` |
| equation | `F_hat = (1 + gamma(t)) * F + beta(t)` |
| gamma | `tanh(gamma_raw)` |
| beta | `tanh(beta_raw)` |
| output_projection_init | `zeros -> EXACT identity at initialisation` |
| task_embedding | `nn.Embedding(task_count, 32)` |
| task_embedding_init | `normal_(mean=0.0, std=0.02)` |
| film_hidden_dim | `64` |
| sites | `["bridge", "decoder4", "decoder3", "decoder2", "decoder1"]` |
| site_count | `5` |
| site_channels | `{"bridge": 256, "decoder4": 192, "decoder3": 96, "decoder2": 48, "decoder1": 24}` |
| sole_task_signal | `true` |

### Shared backbone

| Property | Value |
|---|---|
| encoder_stages | `["encoder1", "encoder2", "encoder3", "encoder4", "bridge"]` |
| decoder_stages | `["decoder4", "decoder3", "decoder2", "decoder1"]` |
| block | `ResidualBlock(ConvNormAct + ConvNorm + 1x1 skip + SiLU)` |
| normalization | `GroupNorm (groups from (8,4,2,1))` |
| activation | `SiLU` |
| pooling | `MaxPool2d(2,2)` |
| upsampling | `bilinear interpolate to skip size` |
| channels | `[24, 48, 96, 192, 256]` |
| in_channels | `3` |
| out_channels | `1` |

### Components present / absent

| Component | Present |
|---|---|
| residual_connections | **True** |
| task_embedding | **True** |
| film_conditioning | **True** |
| shared_segmentation_network | **True** |
| four_domain_joint_training | **True** |
| roi_proposal | False |
| localizer | False |
| regional_refiner | False |
| high_resolution_crop_branch | False |
| global_regional_fusion | False |
| benefit_predictor | False |
| counterfactual_refinement_gain | False |
| resource_budget_router | False |
| adaptive_conditional_computation | False |
| mobile_compression | False |
| pruning | False |
| quantization | False |
| distillation | False |
| architecture_search | False |
| squeeze_excitation | False |
| deep_supervision | False |
| test_evaluation | False |

### Search policy

| Property | Value |
|---|---|
| architectures_considered_for_execution | 1 |
| architecture_sweep_performed | False |
| hyperparameter_sweep_performed | False |
| logical_runs_authorized | 1 |
| seed | 42 |
| resume_is_same_logical_run | True |
| second_seed_belongs_to_later_phase | True |

Artifact: `reports/audits/phase21_global_medfilm_architecture_binding.json` · SHA `21e2c195c8da33da...`

## 7. Pre-execution sanity checks

**Verdict:** `PHASE21_PRE_EXECUTION_CHECK_PASS` — 27/27 passed · `training_may_start = True`

| Check | Passed | Detail |
|---|---|---|
| `architecture_binding_present` | True | `{"verdict": "PHASE21_ARCHITECTURE_FROZEN"}` |
| `model_file_sha_matches_binding` | True | `{"repo": "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f", "bi` |
| `parameter_count_matches_binding` | True | `{"measured": 3523001, "binding": 3523001}` |
| `forward_shape` | True | `{"out_shape": [2, 1, 512, 512]}` |
| `output_spatial_matches_input` | True | `{"in": [512, 512], "out": [512, 512]}` |
| `single_output_channel` | True | `{"out_channels": 1}` |
| `unknown_task_id_rejected` | True | `{"attempted": [0, 4], "task_count": 4}` |
| `task_id_shape_enforced` | True | `{"attempted": "[1] for batch 2"}` |
| `all_four_task_ids_accepted` | True | `{"task_ids": [0, 1, 2, 3]}` |
| `film_identity_at_init` | True | `{"max_abs_output_diff_across_tasks": 0.0, "meaning": "zero-initialised FiLM outp` |
| `film_parameters_zero_at_init` | True | `{"max_abs_gamma": 0.0, "max_abs_beta": 0.0, "sites": ["bridge", "decoder4", "dec` |
| `conditioning_path_wired` | True | `{"max_abs_output_diff_after_film_perturbation": 0.08887243270874023, "meaning": ` |
| `film_output_projection_receives_gradient_at_init` | True | `{"bridge_output_grad_norm": 0.011237830854952335}` |
| `task_embedding_gradient_zero_at_init_by_construction` | True | `{"embedding_grad_norm_at_step0": 0.0, "meaning": "zero-initialised FiLM output p` |
| `task_embedding_receives_gradient_after_one_step` | True | `{"embedding_grad_norm_after_step1": 0.0035784945357590914, "meaning": "the condi` |
| `determinism_same_seed` | True | `{"max_abs_diff": 0.0}` |
| `no_forbidden_modules` | True | `{"hits": {}}` |
| `forward_accepts_only_image_and_task_id` | True | `{"signature": ["self", "images", "task_ids"], "meaning": "no mask-derived metada` |
| `dataset_exposes_task_id_separately` | True | `{"task_id": 1, "dataset": "BUSI"}` |
| `collate_returns_task_id_and_image_separately` | True | `{"keys": ["dataset", "image", "mask", "sample_id", "split", "task_id"]}` |
| `image_channels_3` | True | `{"shape": [2, 3, 512, 512]}` |
| `test_split_rejected_by_dataset` | True | `{"attempted_split": "TEST"}` |
| `test_lock_verified` | True | `{"detail": "manifests/test.csv sha256 matches the frozen lock"}` |
| `no_checkpoints_before_training` | True | `{"checkpoint_dir": "checkpoints\\phase21_global_medfilm_fourdomain_seed42_clean_` |
| `train_population_5832` | True | `{"n": 5832}` |
| `val_population_808` | True | `{"n": 808}` |
| `four_domains_present` | True | `{"distribution": {"ISIC": 2556, "KUB": 1978, "KVASIR": 696, "BUSI": 602}}` |

**Key recorded finding.** The FiLM output projection is zero-initialised, so every site is an
EXACT identity at initialisation and `d(loss)/d(task_embedding)` is exactly **0** at step 0.
The projection itself *does* receive gradient at step 0, and after ONE optimizer step the
embedding path opens. Task conditioning is therefore **learned, not injected**. A weak
conditioning effect at convergence is a legitimate scientific finding and is reported as
`CONDITIONING_EFFECT_WEAK`, never hidden.

Artifact: `reports/audits/phase21_pre_execution_check.json` · SHA `d1becc85f1ad9c1a...`

## 8. Training configuration (inherited protocol)

| Field | Value |
|---|---|
| Loss | `{"name": "bce_dice", "bce_weight": 0.5, "dice_weight": 0.5, "dice_epsilon": 1e-06}` |
| Optimizer | `{"name": "AdamW", "learning_rate": 0.0001, "weight_decay": 0.0001}` |
| Scheduler | `{"name": "CosineAnnealingLR", "T_max": 100, "step": "per_epoch_after_train_and_val"}` |
| Batch size | 4 |
| Eval batch size | 8 |
| Num workers | 4 |
| AMP | True |
| Seed | 42 |
| Max epochs | 100 |
| Early-stopping patience | 15 |
| Sampling policy | `phase20_domain_balanced_uniform_v1` |
| Checkpoint metric | `phase20_macro_domain_mean_dice_v1` |
| Input channel policy | `RGB_3CH` |
| Input resolution | 512 |
| Augmentation | `src.data.transforms.SegmentationTransform(train=True): horizontal mirror p=0.5, rotation +/-5 deg, brightness +/-0.10, contrast +/-0.10; mask NEAREST; VAL disabled` |

## 9. Training progress

**Completed epochs:** 81 · **best epoch:** 66 · **best macro-domain VAL Dice:** 0.835079

**Per-epoch time:** mean 426.6 s · median 409.5 s · min 379.2 s · max 596.4 s

| Epoch | train_loss | val_loss | macro Dice | ISIC | BUSI | KVASIR | KUB | LR | new best | bad | s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.3894 | 0.2901 | **0.615488** | 0.8067 | 0.6790 | 0.4858 | 0.4904 | 9.998e-05 | True | 0 | 596.4 |
| 2 | 0.2992 | 0.2646 | **0.638738** | 0.8216 | 0.7312 | 0.4996 | 0.5026 | 9.990e-05 | True | 0 | 444.1 |
| 3 | 0.2632 | 0.2449 | **0.665535** | 0.8533 | 0.7497 | 0.5510 | 0.5082 | 9.978e-05 | True | 0 | 423.6 |
| 4 | 0.2451 | 0.2515 | **0.686645** | 0.8320 | 0.8079 | 0.5682 | 0.5385 | 9.961e-05 | True | 0 | 467.1 |
| 5 | 0.2194 | 0.2140 | **0.717838** | 0.8638 | 0.8013 | 0.6402 | 0.5661 | 9.938e-05 | True | 0 | 455.1 |
| 6 | 0.2048 | 0.2133 | **0.728646** | 0.8619 | 0.8005 | 0.6841 | 0.5681 | 9.911e-05 | True | 0 | 409.5 |
| 7 | 0.1893 | 0.2099 | **0.730743** | 0.8574 | 0.8259 | 0.6589 | 0.5808 | 9.880e-05 | True | 0 | 455.9 |
| 8 | 0.1813 | 0.1929 | **0.757922** | 0.8744 | 0.8406 | 0.7225 | 0.5942 | 9.843e-05 | True | 0 | 505.9 |
| 9 | 0.1727 | 0.1907 | **0.761398** | 0.8797 | 0.8384 | 0.7115 | 0.6160 | 9.801e-05 | True | 0 | 515.2 |
| 10 | 0.1601 | 0.1920 | **0.761331** | 0.8607 | 0.8196 | 0.7269 | 0.6381 | 9.755e-05 | False | 1 | 500.6 |
| 11 | 0.1557 | 0.2098 | **0.762426** | 0.8678 | 0.8328 | 0.7359 | 0.6133 | 9.704e-05 | True | 0 | 461.3 |
| 12 | 0.1502 | 0.1752 | **0.779625** | 0.8862 | 0.8233 | 0.7533 | 0.6557 | 9.649e-05 | True | 0 | 409.0 |
| 13 | 0.1459 | 0.1705 | **0.791480** | 0.8866 | 0.8541 | 0.7493 | 0.6758 | 9.589e-05 | True | 0 | 399.1 |
| 14 | 0.1397 | 0.1695 | **0.795301** | 0.8849 | 0.8409 | 0.7766 | 0.6787 | 9.524e-05 | True | 0 | 406.5 |
| 15 | 0.1339 | 0.1789 | **0.783655** | 0.8730 | 0.8276 | 0.7448 | 0.6892 | 9.455e-05 | False | 1 | 418.9 |
| 16 | 0.1317 | 0.1713 | **0.791727** | 0.8852 | 0.8386 | 0.7676 | 0.6756 | 9.382e-05 | False | 2 | 415.6 |
| 17 | 0.1239 | 0.1648 | **0.804096** | 0.8836 | 0.8512 | 0.7710 | 0.7106 | 9.304e-05 | True | 0 | 408.8 |
| 18 | 0.1244 | 0.1640 | **0.803018** | 0.8831 | 0.8450 | 0.7742 | 0.7098 | 9.222e-05 | False | 1 | 418.2 |
| 19 | 0.1200 | 0.1550 | **0.815116** | 0.8942 | 0.8553 | 0.7900 | 0.7210 | 9.135e-05 | True | 0 | 415.1 |
| 20 | 0.1196 | 0.1601 | **0.808827** | 0.8878 | 0.8605 | 0.7740 | 0.7130 | 9.045e-05 | False | 1 | 412.9 |
| 21 | 0.1160 | 0.1577 | **0.809158** | 0.8864 | 0.8521 | 0.7744 | 0.7238 | 8.951e-05 | False | 2 | 415.8 |
| 22 | 0.1101 | 0.1615 | **0.808425** | 0.8847 | 0.8525 | 0.7877 | 0.7088 | 8.853e-05 | False | 3 | 394.5 |
| 23 | 0.1101 | 0.1648 | **0.809806** | 0.8839 | 0.8630 | 0.7799 | 0.7124 | 8.751e-05 | False | 4 | 413.1 |
| 24 | 0.1083 | 0.1548 | **0.816123** | 0.8900 | 0.8613 | 0.7949 | 0.7183 | 8.645e-05 | True | 0 | 415.4 |
| 25 | 0.1047 | 0.1595 | **0.815989** | 0.8838 | 0.8591 | 0.7930 | 0.7281 | 8.536e-05 | False | 1 | 397.8 |
| 26 | 0.1045 | 0.1638 | **0.811633** | 0.8738 | 0.8546 | 0.7860 | 0.7322 | 8.423e-05 | False | 2 | 449.4 |
| 27 | 0.1003 | 0.1542 | **0.819244** | 0.8879 | 0.8566 | 0.7927 | 0.7397 | 8.307e-05 | True | 0 | 517.5 |
| 28 | 0.0997 | 0.1595 | **0.813106** | 0.8819 | 0.8412 | 0.7975 | 0.7319 | 8.187e-05 | False | 1 | 494.5 |
| 29 | 0.1000 | 0.1540 | **0.819002** | 0.8882 | 0.8460 | 0.8003 | 0.7416 | 8.065e-05 | False | 2 | 436.4 |
| 30 | 0.0968 | 0.1533 | **0.818102** | 0.8896 | 0.8580 | 0.7882 | 0.7365 | 7.939e-05 | False | 3 | 576.6 |
| 31 | 0.0962 | 0.1519 | **0.819843** | 0.8908 | 0.8609 | 0.7876 | 0.7400 | 7.810e-05 | True | 0 | 409.5 |
| 32 | 0.0941 | 0.1482 | **0.826218** | 0.8931 | 0.8624 | 0.8038 | 0.7457 | 7.679e-05 | True | 0 | 422.0 |
| 33 | 0.0931 | 0.1523 | **0.824620** | 0.8870 | 0.8548 | 0.8064 | 0.7503 | 7.545e-05 | False | 1 | 416.9 |
| 34 | 0.0921 | 0.1530 | **0.823577** | 0.8841 | 0.8606 | 0.7943 | 0.7553 | 7.409e-05 | False | 2 | 405.5 |
| 35 | 0.0876 | 0.1621 | **0.815344** | 0.8770 | 0.8563 | 0.7949 | 0.7332 | 7.270e-05 | False | 3 | 510.7 |
| 36 | 0.0898 | 0.1572 | **0.820482** | 0.8895 | 0.8657 | 0.7928 | 0.7339 | 7.129e-05 | False | 4 | 489.1 |
| 37 | 0.0857 | 0.1506 | **0.821889** | 0.8912 | 0.8632 | 0.7937 | 0.7395 | 6.986e-05 | False | 5 | 501.6 |
| 38 | 0.0849 | 0.1508 | **0.822007** | 0.8946 | 0.8542 | 0.7998 | 0.7394 | 6.841e-05 | False | 6 | 471.2 |
| 39 | 0.0846 | 0.1507 | **0.825716** | 0.8918 | 0.8649 | 0.8030 | 0.7432 | 6.694e-05 | False | 7 | 458.1 |
| 40 | 0.0824 | 0.1515 | **0.821368** | 0.8893 | 0.8525 | 0.7920 | 0.7516 | 6.545e-05 | False | 8 | 384.1 |
| 41 | 0.0824 | 0.1500 | **0.828046** | 0.8933 | 0.8636 | 0.8049 | 0.7504 | 6.395e-05 | True | 0 | 411.0 |
| 42 | 0.0800 | 0.1477 | **0.829219** | 0.8939 | 0.8578 | 0.8070 | 0.7582 | 6.243e-05 | True | 0 | 407.5 |
| 43 | 0.0807 | 0.1522 | **0.823631** | 0.8888 | 0.8612 | 0.8021 | 0.7424 | 6.091e-05 | False | 1 | 460.5 |
| 44 | 0.0789 | 0.1481 | **0.831430** | 0.8953 | 0.8631 | 0.8150 | 0.7524 | 5.937e-05 | True | 0 | 477.2 |
| 45 | 0.0767 | 0.1501 | **0.826136** | 0.8920 | 0.8612 | 0.8017 | 0.7496 | 5.782e-05 | False | 1 | 481.3 |
| 46 | 0.0758 | 0.1491 | **0.828811** | 0.8928 | 0.8633 | 0.8095 | 0.7497 | 5.627e-05 | False | 2 | 470.0 |
| 47 | 0.0760 | 0.1476 | **0.827858** | 0.8927 | 0.8496 | 0.8143 | 0.7549 | 5.471e-05 | False | 3 | 464.0 |
| 48 | 0.0771 | 0.1500 | **0.827236** | 0.8920 | 0.8581 | 0.8056 | 0.7533 | 5.314e-05 | False | 4 | 476.4 |
| 49 | 0.0745 | 0.1461 | **0.832606** | 0.8946 | 0.8652 | 0.8162 | 0.7544 | 5.157e-05 | True | 0 | 451.1 |
| 50 | 0.0710 | 0.1452 | **0.832528** | 0.8916 | 0.8586 | 0.8175 | 0.7624 | 5.000e-05 | False | 1 | 388.6 |
| 51 | 0.0720 | 0.1647 | **0.814579** | 0.8788 | 0.8509 | 0.7775 | 0.7511 | 4.843e-05 | False | 2 | 396.8 |
| 52 | 0.0731 | 0.1546 | **0.821463** | 0.8921 | 0.8585 | 0.7827 | 0.7525 | 4.686e-05 | False | 3 | 391.6 |
| 53 | 0.0708 | 0.1503 | **0.829493** | 0.8920 | 0.8660 | 0.8138 | 0.7461 | 4.529e-05 | False | 4 | 388.0 |
| 54 | 0.0706 | 0.1467 | **0.831893** | 0.8958 | 0.8581 | 0.8101 | 0.7635 | 4.373e-05 | False | 5 | 395.9 |
| 55 | 0.0697 | 0.1485 | **0.828784** | 0.8924 | 0.8572 | 0.8105 | 0.7551 | 4.218e-05 | False | 6 | 395.4 |
| 56 | 0.0689 | 0.1477 | **0.829861** | 0.8944 | 0.8616 | 0.8135 | 0.7500 | 4.063e-05 | False | 7 | 387.2 |
| 57 | 0.0687 | 0.1464 | **0.833947** | 0.8937 | 0.8698 | 0.8178 | 0.7545 | 3.909e-05 | True | 0 | 383.7 |
| 58 | 0.0660 | 0.1538 | **0.829911** | 0.8876 | 0.8637 | 0.8158 | 0.7526 | 3.757e-05 | False | 1 | 381.9 |
| 59 | 0.0678 | 0.1537 | **0.827500** | 0.8897 | 0.8569 | 0.8156 | 0.7477 | 3.605e-05 | False | 2 | 379.2 |
| 60 | 0.0664 | 0.1494 | **0.830241** | 0.8925 | 0.8622 | 0.8194 | 0.7469 | 3.455e-05 | False | 3 | 391.4 |
| 61 | 0.0663 | 0.1503 | **0.830842** | 0.8925 | 0.8622 | 0.8164 | 0.7522 | 3.306e-05 | False | 4 | 397.5 |
| 62 | 0.0661 | 0.1496 | **0.831393** | 0.8909 | 0.8639 | 0.8155 | 0.7553 | 3.159e-05 | False | 5 | 393.6 |
| 63 | 0.0644 | 0.1530 | **0.828830** | 0.8929 | 0.8588 | 0.8164 | 0.7472 | 3.014e-05 | False | 6 | 388.2 |
| 64 | 0.0624 | 0.1481 | **0.833201** | 0.8962 | 0.8669 | 0.8147 | 0.7550 | 2.871e-05 | False | 7 | 395.6 |
| 65 | 0.0637 | 0.1537 | **0.823475** | 0.8848 | 0.8354 | 0.8179 | 0.7558 | 2.730e-05 | False | 8 | 390.4 |
| 66 | 0.0636 | 0.1469 | **0.835079** | 0.8972 | 0.8588 | 0.8202 | 0.7641 | 2.591e-05 | True | 0 | 381.4 |
| 67 | 0.0620 | 0.1503 | **0.832690** | 0.8952 | 0.8593 | 0.8178 | 0.7585 | 2.455e-05 | False | 1 | 387.1 |
| 68 | 0.0604 | 0.1502 | **0.832588** | 0.8948 | 0.8602 | 0.8170 | 0.7583 | 2.321e-05 | False | 2 | 396.3 |
| 69 | 0.0619 | 0.1502 | **0.832354** | 0.8952 | 0.8575 | 0.8208 | 0.7559 | 2.190e-05 | False | 3 | 391.4 |
| 70 | 0.0608 | 0.1477 | **0.832262** | 0.8968 | 0.8538 | 0.8181 | 0.7604 | 2.061e-05 | False | 4 | 394.2 |
| 71 | 0.0598 | 0.1470 | **0.833488** | 0.8982 | 0.8577 | 0.8189 | 0.7591 | 1.935e-05 | False | 5 | 387.8 |
| 72 | 0.0599 | 0.1481 | **0.832418** | 0.8938 | 0.8563 | 0.8177 | 0.7618 | 1.813e-05 | False | 6 | 419.7 |
| 73 | 0.0608 | 0.1497 | **0.831988** | 0.8932 | 0.8563 | 0.8168 | 0.7616 | 1.693e-05 | False | 7 | 396.0 |
| 74 | 0.0601 | 0.1489 | **0.833808** | 0.8941 | 0.8573 | 0.8195 | 0.7644 | 1.577e-05 | False | 8 | 382.7 |
| 75 | 0.0578 | 0.1503 | **0.832779** | 0.8958 | 0.8598 | 0.8164 | 0.7591 | 1.464e-05 | False | 9 | 388.5 |
| 76 | 0.0583 | 0.1491 | **0.834150** | 0.8941 | 0.8626 | 0.8200 | 0.7599 | 1.355e-05 | False | 10 | 396.2 |
| 77 | 0.0576 | 0.1505 | **0.832780** | 0.8933 | 0.8582 | 0.8197 | 0.7600 | 1.249e-05 | False | 11 | 384.3 |
| 78 | 0.0569 | 0.1498 | **0.832451** | 0.8948 | 0.8589 | 0.8167 | 0.7594 | 1.147e-05 | False | 12 | 399.4 |
| 79 | 0.0573 | 0.1529 | **0.831825** | 0.8939 | 0.8592 | 0.8192 | 0.7550 | 1.049e-05 | False | 13 | 384.0 |
| 80 | 0.0556 | 0.1499 | **0.832839** | 0.8952 | 0.8594 | 0.8173 | 0.7594 | 9.549e-06 | False | 14 | 397.5 |
| 81 | 0.0560 | 0.1507 | **0.831697** | 0.8944 | 0.8574 | 0.8173 | 0.7576 | 8.646e-06 | False | 15 | 408.8 |

Best-so-far macro-domain VAL Dice: **0.835079**

**Training status:** NATURALLY TERMINATED — `EARLY_STOPPING_PATIENCE` at epoch 81, best epoch 66, resume_count 1

| Closure field | Value |
|---|---|
| best_epoch | `66` |
| final_epoch | `81` |
| stop_reason | `EARLY_STOPPING_PATIENCE` |
| best_macro_domain_dice | `0.8350791259413984` |
| best_val_loss | `0.14694273973455524` |
| resume_count | `1` |
| independent_duplicate_runs | `0` |
| model_params | `3523001` |
| total_elapsed_seconds | `34588.8289809227` |
| checkpoint_selection_replay_verdict | `PHASE21_CHECKPOINT_SELECTION_REPLAY_PASS` |

| Domain | Dice at best epoch |
|---|---|
| ISIC | 0.897189 |
| BUSI | 0.858823 |
| KVASIR | 0.820246 |
| KUB | 0.764059 |

| Checkpoint | Bytes | SHA-256 (16) |
|---|---|---|
| `best.pt` | 42,369,710 | `286689fdd5c63ad7...` |
| `last.pt` | 42,369,710 | `1de2865578865195...` |
| `latest.pt` | 42,380,390 | `e265140c8b559e96...` |

## 10. Canonical VAL evaluation

| Item | Value |
|---|---|
| Canonical VAL inference runs | **1** |
| Samples expected | 808 |
| Samples evaluated | 808 |
| Threshold | 0.5 |
| No TTA / no threshold tuning / no morphology | True / True / True |
| Probability maps persisted | 808 |
| Checkpoint SHA-256 | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` |

## 11. Results

### Global MedFiLM

| Metric | Value |
|---|---|
| Macro-domain VAL Dice | **0.835079** |
| 95% CI | [0.787749, 0.878006] |
| Macro-domain IoU | 0.744837 |
| Pooled Dice (descriptive) | 0.878424 |
| Rank among six models | 1/6 |

| Domain | Dice | IoU |
|---|---|---|
| ISIC | 0.897189 | 0.829819 |
| BUSI | 0.858823 | 0.763646 |
| KVASIR | 0.820247 | 0.735523 |
| KUB | 0.764058 | 0.650358 |

### Six-model ranking

| Rank | Model | Macro-domain Dice | 95% CI | Parameters |
|---|---|---|---|---|
| 1 | Global MedFiLM | 0.835079 | [0.787749, 0.878006] | 3,523,001 |
| 2 | DeepLabV3+ | 0.827652 | [0.770725, 0.876131] | 40,347,041 |
| 3 | Transformer/MiT-style U-Net | 0.822383 | [0.759882, 0.875536] | 16,347,777 |
| 4 | U-Net++ | 0.792010 | [0.744572, 0.838188] | 9,159,681 |
| 5 | Attention U-Net | 0.789037 | [0.728752, 0.844685] | 7,851,285 |
| 6 | U-Net | 0.787832 | [0.738143, 0.837522] | 7,763,041 |

### Paired domain-stratified bootstrap vs the five frozen baselines

Method: paired domain-stratified percentile bootstrap, `n_boot=2000`, seed=42, unit=image; the same resampled VAL indices are used for both models.

- Statistically separable (CI excludes 0): **['unet', 'attention_unet', 'unetpp', 'transformer_mit_unet']**
- CI overlaps zero (NOT separable): **['deeplabv3plus']**
## 12. KUB analyses (REPORTING ONLY)

Size taxonomy `kub_size_clean_v3_v1` strata n: `{"TINY": 44, "SMALL": 19, "MEDIUM": 27, "LARGE": 13, "ROI_NOT_PRIMARY_BINNED": 177}`

TINY stratum preserved for Phase 22: **True** · optimised on TINY: **False**

## 13. Task-conditioning diagnostic and FiLM sanity

| Item | Value |
|---|---|
| Scope | frozen 64-case gallery (16 per domain), reused UNCHANGED |
| Cases | 64 |
| Mean \|delta Dice\| with wrong task ID | 0.184192 |
| Max \|delta Dice\| with wrong task ID | 0.927052 |
| Flag | **CONDITIONING_EFFECT_PRESENT** |
| Flag rule | CONDITIONING_EFFECT_WEAK when mean|delta Dice| < 0.005 |

> A weak effect is a legitimate scientific finding about this reference model and is reported as-is. It is NOT evidence that task conditioning is useless in general, and a strong effect here would NOT by itself prove that FiLM caused the benchmark gap (no architecture-matched control exists).

## 14. Galleries

- **Frozen 64-case gallery** (16 per domain) reused **UNCHANGED**, extended to a six-model
  panel. Selection: `reports/tables/phase21_gallery_selection_64.csv`.
- **Detailed gallery** (>=16 per domain), explicitly labelled `ANALYTICAL_OUTCOME_SELECTED`.
- **Failure-analysis gallery** (worst-16), explicitly labelled `ANALYTICAL_OUTCOME_SELECTED`.
- The two outcome-selected galleries are **distinct** from the fixed 64-case gallery.

## 15. Figures and notebook

Figure root: `reports/figures/phase21_global_medfilm/` with subfolders `training/`,
`comparison/`, `kub/`, `conditioning/`, `gallery/`, `failure/`, `efficiency/`.

Reviewer notebook: `notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb` — deterministic cell IDs, fixed Styler UUIDs,
normalised memory addresses, stripped volatile metadata, stable output order; three
consecutive builds must be byte-identical.

## 16. Parameter and compute accounting (MEASUREMENT ONLY)

- Parameters: **3523001**
- Compute: **31.5517 G MACs** (**63.1035 G FLOPs** at the 2x-MACs convention) for a 1x3x512x512 input.
- Method: exact closed-form `Conv2d`/`Linear` count (`scripts/analysis/phase21_mac_count.py`). This is a **lower bound** on total
  arithmetic: it excludes GroupNorm, SiLU, pooling, interpolation and the FiLM
  elementwise modulation. No third-party FLOP library was used (thop / fvcore / ptflops / torchinfo are all absent).

| Block | G MACs | Share |
|---|---|---|
| `decoder3` | 5.8888 | 18.7% |
| `decoder2` | 5.8888 | 18.7% |
| `decoder1` | 5.8888 | 18.7% |
| `decoder4` | 4.8822 | 15.5% |
| `encoder2` | 2.1139 | 6.7% |
| `encoder3` | 2.1139 | 6.7% |
| `encoder4` | 2.1139 | 6.7% |
| `encoder1` | 1.5477 | 4.9% |
| `bridge` | 1.1073 | 3.5% |
| `head` | 0.0063 | 0.0% |
| `film_layers` | 0.0001 | 0.0% |


### 16.1 Six-model comparison (identical protocol, 1x3x512x512)

All six models are the frozen Phase-20/20B panel plus the Phase-21 Global MedFiLM
reference. Parameters and MACs are measured on the same input shape, so those columns
are directly comparable. Accuracy is tabulated separately in §11 and `phase21_six_model_comparison.csv`, because the frozen baselines are reported at
their own best epoch under the frozen Phase-20 protocol while Global MedFiLM is a
Phase-21 result; the two must not be silently mixed without that caveat.

| Model | Parameters | Params rank | G MACs | MACs rank | vs MedFiLM (params x) | vs MedFiLM (MACs x) |
|---|---|---|---|---|---|---|
| Global MedFiLM | 3,523,001 | 1 | 31.5517 | 1 | 1.000 | 1.000 |
| U-Net | 7,763,041 | 2 | 46.1373 | 2 | 2.204 | 1.462 |
| Attention U-Net | 7,851,285 | 3 | 47.2190 | 3 | 2.229 | 1.497 |
| DeepLabV3+ | 40,347,041 | 6 | 69.1394 | 4 | 11.452 | 2.191 |
| Transformer/MiT | 16,347,777 | 5 | 99.0986 | 5 | 4.640 | 3.141 |
| U-Net++ | 9,159,681 | 4 | 137.9423 | 6 | 2.600 | 4.372 |

Global MedFiLM ranks **1 of 6 on parameters AND 1 of 6 on compute** — it is
simultaneously the smallest and the cheapest model in the panel, i.e. **the
lightest on both axes**. This is a *relative* statement about this six-model
panel only: the absolute cost (31.55 G MACs at 512 px) remains substantial, so
being the lightest member here does not by itself establish fitness for
constrained deployment.

- Arithmetic per parameter: **8,956 MACs per parameter** (8.96 G MACs per M params). The highest in the
  panel is U-Net++ at 15,060 MACs per parameter — so a low parameter count does not by itself imply low arithmetic.
- Measurement device for this table: `cpu`; `task_ids` passed to `1` of 6 models (only the task-conditioned reference).

- GPU latency, peak memory, per-epoch wall time and an optional CPU latency benchmark: `reports/tables/phase21_efficiency_accounting.csv`.
- Per-epoch wall time for the live run is available now from the training history (§9).
- **No** optimization, pruning, quantization or compression was performed.

## 17. Interpretation rules applied

- Permitted: *"Global MedFiLM achieved X compared with baseline Y."*
- Forbidden: *"FiLM caused +X."* — no architecture-matched control exists.
- CI overlapping zero ⇒ the models are **not separable** and no ordering claim is made.
- No historical (legacy) result is claimed as a current Phase-21 result.

## 18. TEST lock

| Counter | Value |
|---|---|
| TEST image reads | 0 |
| TEST mask reads | 0 |
| TEST inference | 0 |
| TEST visualizations | 0 |

Enforced by `src.utils.test_lock.verify_test_lock`, `src.data.loaders.create_loader` and
`src.data.multidomain_dataset.MultiDomainDataset`, and re-verified at the start of training,
evaluation, analysis and reporting.

## 19. Artifact index

| Artifact | SHA-256 (16) | Bytes |
|---|---|---|
| `reports/audits/phase21_analysis.json` | `24a92bc09d3bf8f1...` | 3,429 |
| `reports/audits/phase21_analytical_mac_count.json` | `eb35c87f191196c6...` | 1,954 |
| `reports/audits/phase21_efficiency_accounting.json` | `4e499b280578c981...` | 3,923 |
| `reports/audits/phase21_entry_gate.json` | `567093d222e9fc73...` | 4,036 |
| `reports/audits/phase21_final_freeze.json` | `cc8de39cb61f698d...` | 13,481 |
| `reports/audits/phase21_global_medfilm_architecture_binding.json` | `21e2c195c8da33da...` | 5,371 |
| `reports/audits/phase21_global_medfilm_confusion_matrices.json` | `b9d97203c5f7c62b...` | 2,636 |
| `reports/audits/phase21_governance_sync.json` | `6cd9576f1990fd3d...` | 1,079 |
| `reports/audits/phase21_legacy_medfilm_architecture_audit.json` | `1c68656ee29ea96e...` | 9,371 |
| `reports/audits/phase21_notebook_determinism.json` | `907833ad67c4b688...` | 790 |
| `reports/audits/phase21_paired_bootstrap.json` | `bb85bbfca14759fa...` | 945 |
| `reports/audits/phase21_pre_execution_check.json` | `d1becc85f1ad9c1a...` | 5,588 |
| `reports/audits/phase21_prediction_manifest.json` | `bee34b857321aaa8...` | 1,982 |
| `reports/audits/phase21_progress_status.json` | `0f44ce842e2dbff7...` | 1,651 |
| `reports/audits/phase21_protocol_binding.json` | `d86a6b04c080ddad...` | 8,610 |
| `reports/audits/phase21_task_conditioning_diagnostic.json` | `8084d339e02aeb86...` | 1,516 |
| `reports/audits/phase21_val_evaluation.json` | `fdcba4126d9a99f1...` | 1,132 |
| `reports/tables/phase21_all_trained_models_comparison.csv` | `77f5d6a7da549759...` | 1,263 |
| `reports/tables/phase21_efficiency_accounting.csv` | `3f3b5166433d915e...` | 2,022 |
| `reports/tables/phase21_film_parameter_summary.csv` | `5ce63c95ce38f0a6...` | 5,905 |
| `reports/tables/phase21_gallery_selection_64.csv` | `2bc7c16286999ced...` | 5,481 |
| `reports/tables/phase21_global_medfilm_calibration_ranking.csv` | `4598617946477aae...` | 666 |
| `reports/tables/phase21_global_medfilm_confusion_matrices.csv` | `6e19e306ee21c90f...` | 858 |
| `reports/tables/phase21_global_medfilm_domain_bootstrap_ci.csv` | `4ebf24b7bfd4a682...` | 1,106 |
| `reports/tables/phase21_global_medfilm_domain_performance.csv` | `7b311e2a8a1e124b...` | 3,418 |
| `reports/tables/phase21_kub_size_stratification.csv` | `ed4f8a9fcf736c61...` | 652 |
| `reports/tables/phase21_kub_size_stratification_per_sample.csv` | `7bd4ab84e0acbb6a...` | 30,071 |
| `reports/tables/phase21_kub_subgroup_analysis.csv` | `8a87bf504e343d78...` | 644 |
| `reports/tables/phase21_paired_bootstrap_vs_baselines.csv` | `d16ade357abb1bee...` | 2,446 |
| `reports/tables/phase21_per_image_all_models.csv` | `a45804af1d63c5c7...` | 2,582,381 |
| `reports/tables/phase21_per_image_val_metrics.csv` | `8d8dad2cc12d00bd...` | 501,416 |
| `reports/tables/phase21_prediction_manifest.csv` | `02c0b27caf99cc11...` | 441,862 |
| `reports/tables/phase21_six_model_comparison.csv` | `81ee9990f90c4ef7...` | 1,448 |
| `reports/tables/phase21_six_model_compute.csv` | `5e88da50faaee41a...` | 1,193 |
| `reports/tables/phase21_task_conditioning_diagnostic.csv` | `58eb88ca051453c3...` | 548 |
| `reports/tables/phase21_task_conditioning_per_case.csv` | `bfb123fc09ce252e...` | 14,668 |

### Frozen science untouched

- `reports/audits/phase20_shared_global_baseline_protocol.json` — SHA `b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c` (expected `b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c`) — matches: **True**
- No `phase20_*` or `phase20b_*` artifact was modified.

## 20. Remaining steps to the terminal state

None. Phase 21 is COMPLETE.

**Phase 22 is NOT started.**
