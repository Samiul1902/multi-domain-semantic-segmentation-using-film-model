# Phase 21 — Handoff Bundle for an External Reviewer (ChatGPT)

Generated `2026-09-29T02:16:31.500367+00:00` by `scripts/analysis/build_phase21_handoff.py`.

**How to use this document.** It is a single self-contained snapshot of the Phase-21 experiment. Paste it whole into the external model and ask it for the next step. Everything below is read from persisted artifacts — nothing here is recomputed, and no file attachment is required.

---

## 1. TL;DR — status in one paragraph

Phase 21 is **COMPLETE** and frozen. It trained exactly ONE shared four-domain task-conditioned segmentation model (`Global MedFiLM`, architecture id `global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1`) on the frozen Phase-20 protocol. Canonical VAL result: macro-domain Dice **n/a** on 808 VAL samples at a single threshold of 0.5. It ranks **1 of 6** on accuracy in the panel and **1 of 6** on both parameters and compute, but a paired bootstrap says it is **NOT separable from DeepLabV3+** (the runner-up) — the top two are tied. Terminal state `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED`; Phase 22 is ELIGIBLE but **NOT STARTED** by design.

> **This is a GLOBAL reference model only.** It is NOT the final `RA-MedFiLM-Seg++`. No ROI proposal, no localizer, no regional refiner, no HR crop, no fusion, no benefit predictor, no router, no compression and no NAS were built or evaluated. TEST was never read.

## 2. Hard constraints that any proposed next step MUST respect

These are standing rules for this repository. A next-step proposal that violates any of them is not admissible.

| # | Constraint |
|---|---|
| 1 | **TEST is locked.** TEST image reads, mask reads, inference and visualization must all remain **0**. Never propose anything that reads TEST. |
| 2 | **One architecture frozen before training.** No hyperparameter sweep, no second seed, no architecture edits to the Phase-21 model. |
| 3 | **One canonical VAL pass.** It has already happened (808 samples, once). Never re-run it; any re-execution must use `--skip-eval`. |
| 4 | **Phase 22 must NOT be started** as a side effect. It is eligible, nothing more. |
| 5 | **No causal claim about FiLM.** There is no architecture-matched control (no identical plain model trained under this run), so only *"Global MedFiLM achieved X compared with baseline Y"* is permitted. *"FiLM caused +X"* is forbidden. |
| 6 | **CI overlap rule.** Where a paired confidence interval overlaps zero the models are NOT separable and no ordering claim may be made. |
| 7 | **The frozen Phase-20 protocol** (`phase20_shared_global_baseline_protocol.json`) and every `phase21_*_binding.json` / `*_pre_execution_check.json` are immutable. |
| 8 | **This is a GLOBAL reference only**, not the final RA-MedFiLM-Seg++. |

## 3. The frozen protocol (shared with Phase 20 — the comparison basis)

Phase 21 inherited the frozen Phase-20 protocol **byte-for-byte**: protocol SHA `see file`. The only intentional change is the architecture plus `task_id` conditioning. Full protocol below.

### 3.1 Frozen shared protocol

`reports/audits/phase20_shared_global_baseline_protocol.json`

- size: `8730` bytes
- sha256: `b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c`

```json
{
  "artifact": "phase20_shared_global_baseline_protocol",
  "phase_id": 20,
  "stage": "B",
  "title": "Shared Multi-Domain Global Baseline (single frozen UNet++, no FiLM, no regional module)",
  "status": "PHASE20_PROTOCOL_FROZEN__AWAITING_EXECUTION",
  "primary_question": "How well can ONE shared conventional segmentation model represent all four medical domains under the harmonized Stage-B data contract, WITHOUT task-conditioned FiLM and WITHOUT the regional mechanism?",
  "is_model_training_phase": true,
  "experiment_id": "phase20_shared_unetpp_fourdomain_seed42_clean_v3",
  "architecture": "unetpp_nested_4_level_no_deep_supervision_base32",
  "architecture_selection_evidence": "reports/audits/phase20_baseline_architecture_freeze.json",
  "input_representation": {
    "channel_policy": "RGB_3CH",
    "contract_label": "PHASE20_BASELINE_OPERATIONAL_INPUT_ONLY",
    "not_the_final_phase24_policy": true,
    "rules": [
      "native RGB domains remain deterministic RGB",
      "native-L domains are deterministically replicated to 3 identical channels",
      "no learned modality adapter",
      "no domain-specific normalization branch"
    ],
    "intensity_normalization": "divide by 255.0 -> [0, 1]",
    "model_input_excludes": [
      "task_id",
      "dataset_id",
      "KUB category",
      "patient_id",
      "case_id",
      "foreground_fraction",
      "mask-derived metadata"
    ]
  },
  "input_resolution": 512,
  "resolution_decision": {
    "frozen": 512,
    "decision_time": "PRE_TRAINING",
    "no_resolution_search": true,
    "did_not_compare": [
      "256 vs 384",
      "256 vs 512",
      "384 vs 512"
    ],
    "evidence": [
      "No legacy KUB-bearing four-domain shared baseline exists (reports/audits/phase20_legacy_baseline_selection_evidence.json).",
      "The legacy fully-supervised shared three-domain baseline used 256 px (medfilm_seg) but belongs to a superseded pipeline whose hyperparameters the Phase-19 reuse map explicitly does NOT adopt.",
      "The frozen architecture's own repository clean-v3 evidence (Phase-10 UNet++) was obtained at 512 px.",
      "512 is the Phase-19 preprocessing default_size and preserves KUB tiny-object detail, which is the project's central difficulty.",
      "A throughput probe (execution mechanism only) confirmed 512 px at batch 4 with 4 loader workers costs ~7.3 min/epoch against ~7.0 min/epoch of GPU time, so 512 is operationally affordable."
    ],
    "supported_sizes_available": [
      256,
      512,
      768,
      1024
    ]
  },
  "preprocessing_contract_id": "phase19_preprocessing_contract_v1",
  "preprocessing_contract_sha256": "a1db4b083611bc5a6ec4928427c77fcc49a949481aabfadaa5277735bf53fdf0",
  "evaluation_contract_id": "phase19_evaluation_contract_v1",
  "evaluation_contract_sha256": "7f7f18fc17e1f377ef8fefcd9f4c9280cd46443b1b1f500071037525f3d32355",
  "dataset_populations": {
    "manifest_version": "phase4_v3",
    "TRAIN": {
      "BUSI": 602,
      "ISIC": 2556,
      "KUB": 1978,
      "KVASIR": 696
    },
    "VAL": {
      "BUSI": 84,
      "ISIC": 357,
      "KUB": 280,
      "KVASIR": 87
    },
    "TRAIN_total": 5832,
    "VAL_total": 808,
    "task_ids": {
      "ISIC": 0,
      "BUSI": 1,
      "KVASIR": 2,
      "KUB": 3
    }
  },
  "sampling_policy": {
    "policy_id": "phase20_domain_balanced_uniform_v1",
    "type": "domain_balanced_weighted",
    "num_samples_per_epoch": 5832,
    "replacement": true,
    "task_id_role": "sampling_only__never_a_model_input",
    "audit": "reports/audits/phase20_sampling_policy_audit.json"
  },
  "loss": {
    "name": "bce_dice",
    "bce_weight": 0.5,
    "dice_weight": 0.5,
    "dice_epsilon": 1e-06
  },
  "optimizer": {
    "name": "AdamW",
    "learning_rate": 0.0001,
    "weight_decay": 0.0001
  },
  "learning_rate": 0.0001,
  "weight_decay": 0.0001,
  "scheduler": {
    "name": "CosineAnnealingLR",
    "T_max": 100,
    "step": "per_epoch_after_train_and_val"
  },
  "batch_size": 4,
  "eval_batch_size": 8,
  "num_workers": 4,
  "amp": true,
  "seed": 42,
  "max_epochs": 100,
  "early_stopping": {
    "enabled": true,
    "patience": 15,
    "ties_count_as_bad_epochs": true,
    "check_after_checkpoint_save": true
  },
  "checkpoint_selection": {
    "rule_id": "phase20_macro_domain_mean_dice_v1",
    "metric": "macro_domain_mean_validation_dice",
    "formula": "mean(Dice_ISIC, Dice_BUSI, Dice_KVASIR, Dice_KUB)",
    "per_domain_aggregation": "unweighted mean of per-image Dice within the domain",
    "tie_break": "lower validation loss",
    "not_used": [
      "pooled/micro pixel Dice",
      "KUB alone",
      "weighted Dice"
    ],
    "replayed_from_disk_after_training": true
  },
  "evaluation_metrics": {
    "per_domain_and_macro": [
      "dice",
      "iou",
      "precision",
      "recall",
      "specificity",
      "balanced_accuracy",
      "mcc"
    ],
    "boundary": [
      "hd95",
      "assd",
      "surface_dice"
    ],
    "calibration": [
      "brier",
      "ece",
      "mce"
    ],
    "ranking": [
      "roc_auc",
      "average_precision"
    ],
    "summary_statistics": [
      "mean",
      "median",
      "sd",
      "iqr",
      "bootstrap_95_ci"
    ],
    "threshold": 0.5,
    "boundary_unit": "pixel",
    "implementation": "src.metrics.evaluation_metrics",
    "bootstrap": {
      "n_boot": 2000,
      "seed": 42,
      "alpha": 0.05,
      "unit": "image"
    }
  },
  "single_run_authorization": {
    "logical_runs_authorized": 1,
    "seed": 42,
    "no_architecture_alternatives": true,
    "no_post_hoc_restart_from_epoch_1": true,
    "resume_is_same_logical_run": true,
    "second_seed_belongs_to_phase_29": true
  },
  "test_locks": {
    "test_image_reads": 0,
    "test_mask_reads": 0,
    "test_inference": 0,
    "test_visualization": 0,
    "final_test_evaluation_phase": 39,
    "enforced_by": [
      "src.utils.test_lock",
      "src.data.loaders.create_loader",
      "src.data.multidomain_dataset.MultiDomainDataset"
    ]
  },
  "output_isolation": {
    "experiment_dir": "experiments/phase20_shared_unetpp_fourdomain_seed42_clean_v3",
    "checkpoint_dir": "checkpoints/phase20_shared_unetpp_fourdomain_seed42_clean_v3",
    "overwrites_legacy_checkpoints": false,
    "overwrites_stage_a_checkpoints": false
  },
  "code_shas": {
    "scripts/training/train_phase20_shared_unetpp.py": "7ba1ed8238c18277d62c47081a1ff2de0fd1a8fa6b9ef67c04de9d09c108bd85",
    "src/models/unetpp.py": "87adb3f39d72fc4220445eb8a29f4f9a2c1930f98563b012edb7bd7847425db2",
    "src/models/unet.py": "62edc8fb481eb02c46c2c64f6e7219254a57d7ba935a4c840a5a7965b41bdfc2",
    "src/data/multidomain_dataset.py": "461062e5d6bf564872645c51c4175e69cb6169b729f1e5f311f2783f3f0b70b3",
    "src/data/transforms.py": "09fcff4887ff8cda4daa215efad1d504d4d61f70982262022b6c2a30c8cf8bd1",
    "src/data/loaders.py": "eb0c1b5d295d3b77b3e9745fcdeb4ff93f985fd7a58fc8909d8098b5820a8f1a",
    "src/data/domain_balanced_sampler.py": "a59782f1aa85882aa6c1f0dddd75a9888ec34ecc1bdbcc7f0cd733a4ae0ef0d2",
    "src/losses/segmentation.py": "2af539bd47a07c966d4a2784f4df7d81bce0620af8ef8e8ddc8b34a3e6de0e8f",
    "src/training/phase20_selection.py": "99d412361445c10e45f148ba87dfc39b95e9ca51f82b2a1571964ca2df9421c3",
    "src/metrics/evaluation_metrics.py": "6c515f6f1a495315c79238292c385a082ae8347489130ad5bff34d74c4f181f6",
    "src/utils/targets.py": "cd586a75e503b7d5c61f2d83ffd401a85c6d62b1c6f88b90a72bbe2535fd2b19",
    "src/utils/test_lock.py": "7cff4732b1f643738c410d672372684486d79e475eae18da5fee7ae10d2d22f3",
    "src/utils/device.py": "9adabfbd145a5952275aa25b0ec99aab8a5114bb41aa443ecde52ce19a8448b6",
    "src/utils/reproducibility.py": "1f4e1fd2de7ed8b1697eb2b3e8ebe6d98a90fc84b66e35b0c6e46dbdeea374ee",
    "src/utils/run_lock.py": "0a38f2338775fbf6b6a8c12c3bf2e65d0fe1b410c6bb9f8f6d158b4633c0fada"
  },
  "entry_conditions": {
    "phase19_authority_binding": "reports/audits/phase20_phase19_authority_binding.json",
    "entry_gate": "reports/audits/phase20_entry_gate.json",
    "duplicate_audit": "reports/audits/phase20_cross_domain_duplicate_audit.json",
    "pre_execution_check": "reports/audits/phase20_pre_execution_check.json"
  },
  "governance": {
    "training_performed": false,
    "inference_performed": false,
    "checkpoints_created": 0,
    "film_used": false,
    "regional_module_used": false,
    "localizer_used": false,
    "roi_proposal_used": false,
    "task_conditioning_used": false,
    "test_reads": 0
  }
}
```

**Protocol summary (key fields):**

```json
{
  "input_resolution": 512,
  "loss": {
    "name": "bce_dice",
    "bce_weight": 0.5,
    "dice_weight": 0.5,
    "dice_epsilon": 1e-06
  },
  "optimizer": {
    "name": "AdamW",
    "learning_rate": 0.0001,
    "weight_decay": 0.0001
  },
  "scheduler": {
    "name": "CosineAnnealingLR",
    "T_max": 100,
    "step": "per_epoch_after_train_and_val"
  },
  "batch_size": 4,
  "eval_batch_size": 8,
  "num_workers": 4,
  "amp": true,
  "seed": 42,
  "max_epochs": 100
}
```

## 4. What was trained

| Field | Value |
|---|---|
| experiment id | `phase21_global_medfilm_fourdomain_seed42_clean_v3` |
| architecture id | `global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1` |
| parameters | `n/a` |
| is_global_reference_only | `True` |
| is_final_ra_medfilm_seg_plus_plus | `False` |

Architecture in words: ONE shared residual encoder–decoder (channels 24/48/96/192/256, no squeeze-excite, no deep supervision) + a task embedding `nn.Embedding(4, 32)` + FiLM `F_hat = (1 + gamma(t)) * F + beta(t)` applied at **5 sites** (bridge, and decoder4..decoder1). `gamma`/`beta` are `tanh`-bounded and the FiLM output projection is **zero-initialised**, so the model is an **exact identity at initialisation** — conditioning is genuinely learned, not injected. ONE shared 1x1 foreground head.

### 4.1 Architecture binding (frozen)

`reports/audits/phase21_global_medfilm_architecture_binding.json`

- size: `5371` bytes
- sha256: `21e2c195c8da33da761965817bab99f0eeec5fa84a846d05ae765b9567017e78`

```json
{
  "artifact": "phase21_global_medfilm_architecture_binding",
  "phase": 21,
  "generated_utc": "2026-09-28T11:26:12.717649+00:00",
  "frozen_before_training": true,
  "training_performed_at_binding_time": false,
  "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
  "architecture_id": "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1",
  "architecture_family": "GLOBAL_MEDFILM_TASK_CONDITIONED_SHARED_SEGMENTATION",
  "is_final_ra_medfilm_seg_plus_plus": false,
  "is_global_reference_only": true,
  "model_class": "src.models.film.global_medfilm.GlobalMedFiLM",
  "model_file": "src/models/film/global_medfilm.py",
  "model_file_sha256": "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f",
  "model_package_init_sha256": "3df73eaa3439429137bd09ea8c53f73baa75edcdc1acf57a3c57160da2ebeca7",
  "factory_file": "src/models/factory.py",
  "factory_file_sha256": "f97f97a5632675ae54e4c42a629d06d1b5e265f73c85ba6d0a2077b9147afdde",
  "measured_parameter_count": 3523001,
  "measured_parameter_count_including_buffers": 3523001,
  "one_shared_parameter_set": true,
  "dataset_specific_head": false,
  "output_definition": "single shared 1x1 head -> 1 foreground logit",
  "component_specification": {
    "task_conditioning": {
      "mechanism": "FiLM (feature-wise linear modulation)",
      "equation": "F_hat = (1 + gamma(t)) * F + beta(t)",
      "gamma": "tanh(gamma_raw)",
      "beta": "tanh(beta_raw)",
      "output_projection_init": "zeros -> EXACT identity at initialisation",
      "task_embedding": "nn.Embedding(task_count, 32)",
      "task_embedding_init": "normal_(mean=0.0, std=0.02)",
      "film_hidden_dim": 64,
      "sites": [
        "bridge",
        "decoder4",
        "decoder3",
        "decoder2",
        "decoder1"
      ],
      "site_count": 5,
      "site_channels": {
        "bridge": 256,
        "decoder4": 192,
        "decoder3": 96,
        "decoder2": 48,
        "decoder1": 24
      },
      "sole_task_signal": true
    },
    "shared_backbone": {
      "encoder_stages": [
        "encoder1",
        "encoder2",
        "encoder3",
        "encoder4",
        "bridge"
      ],
      "decoder_stages": [
        "decoder4",
        "decoder3",
        "decoder2",
        "decoder1"
      ],
      "block": "ResidualBlock(ConvNormAct + ConvNorm + 1x1 skip + SiLU)",
      "normalization": "GroupNorm (groups from (8,4,2,1))",
      "activation": "SiLU",
      "pooling": "MaxPool2d(2,2)",
      "upsampling": "bilinear interpolate to skip size",
      "channels": [
        24,
        48,
        96,
        192,
        256
      ],
      "in_channels": 3,
      "out_channels": 1
    },
    "present": {
      "residual_connections": true,
      "task_embedding": true,
      "film_conditioning": true,
      "shared_segmentation_network": true,
      "four_domain_joint_training": true
    },
    "absent": {
      "roi_proposal": false,
      "localizer": false,
      "regional_refiner": false,
      "high_resolution_crop_branch": false,
      "global_regional_fusion": false,
      "benefit_predictor": false,
      "counterfactual_refinement_gain": false,
      "resource_budget_router": false,
      "adaptive_conditional_computation": false,
      "mobile_compression": false,
      "pruning": false,
      "quantization": false,
      "distillation": false,
      "architecture_search": false,
      "squeeze_excitation": false,
      "deep_supervision": false,
      "test_evaluation": false
    }
  },
  "forbidden_module_audit": {
    "tokens_checked": [
      "localizer",
      "proposal",
      "roi",
      "regional",
      "refiner",
      "crop_branch",
      "benefit",
      "router",
      "budget",
      "counterfactual",
      "distill",
      "prune",
      "quant",
      "architecture_search"
    ],
    "hits": {},
    "passed": true
  },
  "search_policy": {
    "architectures_considered_for_execution": 1,
    "architecture_sweep_performed": false,
    "hyperparameter_sweep_performed": false,
    "logical_runs_authorized": 1,
    "seed": 42,
    "resume_is_same_logical_run": true,
    "second_seed_belongs_to_later_phase": true
  },
  "inherited_protocol": {
    "path": "reports/audits/phase20_shared_global_baseline_protocol.json",
    "sha256": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
    "binding_artifact": "reports/audits/phase21_protocol_binding.json"
  },
  "legacy_evidence": {
    "path": "reports/audits/phase21_legacy_medfilm_architecture_audit.json",
    "reuse_type": "REFERENCE_ONLY",
    "historical_result_claimed_as_current": false
  },
  "governance": {
    "training_performed": false,
    "inference_performed": false,
    "checkpoints_created": 0,
    "film_used": true,
    "regional_module_used": false,
    "localizer_used": false,
    "roi_proposal_used": false,
    "benefit_router_used": false,
    "test_reads": 0
  },
  "output_isolation": {
    "experiment_dir": "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3",
    "checkpoint_dir": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3",
    "overwrites_phase20_checkpoints": false
  },
  "verdict": "PHASE21_ARCHITECTURE_FROZEN"
}
```

## 5. Training outcome

| Field | Value |
|---|---|
| best_epoch | `66` |
| stop_reason | `EARLY_STOPPING_PATIENCE` |
| resume_count | `1` |
| naturally_terminated | see closure below |

Note on `resume_count`: the host **tears down the launching process tree** every roughly 2–3.5 hours. The Phase-21 run was killed once this way (from epoch 29) and resumed; the trajectory is continuous. Resume is bit-exact **by construction** (per-epoch `derive_epoch_seed`, explicit generator + `seed_worker`, and a dataset with no internal RNG), which is why the checkpoints legitimately store no RNG state.

### 5.1 Training closure

`experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/phase21_training_closure.json`

- size: `4837` bytes
- sha256: `5d58c9233160e77fad6a03f1cb53907345b14cf9a0c8418f3a5d56d1fb0391ac`

```json
{
  "artifact": "phase21_training_closure",
  "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
  "phase": 21,
  "manifest_version": "phase4_v3",
  "architecture_id": "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1",
  "selection_rule_id": "phase20_macro_domain_mean_dice_v1",
  "best_epoch": 66,
  "best_macro_domain_dice": 0.8350791259413984,
  "best_val_loss": 0.14694273973455524,
  "per_domain_dice_at_best": {
    "ISIC": 0.8971889995309819,
    "BUSI": 0.8588225990533829,
    "KVASIR": 0.8202460642006006,
    "KUB": 0.764058840980628
  },
  "final_epoch": 81,
  "total_completed_epochs": 81,
  "stop_reason": "EARLY_STOPPING_PATIENCE",
  "early_stopping_patience": 15,
  "history_path": "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/history.csv",
  "history_sha256": "e2ea06c5261c6fce155e9bc7109a1c03e77ba55c638a16250ade61e8a39022a0",
  "best_checkpoint_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
  "last_checkpoint_sha256": "1de286557886519553ccf773d00c2d470c030ed1c3b81a8703c6cc4baa53bf58",
  "trainer_path": "scripts/training/train_phase21_global_medfilm.py",
  "trainer_sha256": "ec17641b8e6e680af4e912332dbae00cf5d66e56b33cac70229e39d506f20785",
  "model_file_sha256": "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f",
  "frozen_protocol_sha256": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
  "resume_events": [
    {
      "at": "2026-09-28T22:21:11",
      "resumed_from_epoch": 29
    }
  ],
  "resume_count": 1,
  "independent_duplicate_runs": 0,
  "test_reads": {
    "test_image_reads": 0,
    "test_mask_reads": 0,
    "test_inference": 0,
    "test_visualization": 0
  },
  "training_performed": true,
  "model_params": 3523001,
  "total_elapsed_seconds": 34588.8289809227,
  "checkpoint_selection_replay_verdict": "PHASE21_CHECKPOINT_SELECTION_REPLAY_PASS",
  "configuration": {
    "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
    "phase": 21,
    "manifest_version": "phase4_v3",
    "dataset": "MULTI_DOMAIN_ISIC_BUSI_KVASIR_KUB",
    "architecture": "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1",
    "model": {
      "name": "GlobalMedFiLM",
      "task_count": 4,
      "in_channels": 3,
      "out_channels": 1,
      "channels": [
        24,
        48,
        96,
        192,
        256
      ],
      "task_embedding_dim": 32,
      "film_hidden_dim": 64,
      "film_sites": [
        "bridge",
        "decoder4",
        "decoder3",
        "decoder2",
        "decoder1"
      ],
      "film_equation": "F_hat = (1 + gamma(t)) * F + beta(t); gamma=tanh(gamma_raw), beta=tanh(beta_raw)",
      "film_output_projection": "zero_initialised__identity_at_init",
      "heads": "ONE shared 1x1 foreground head (no dataset-specific head)"
    },
    "input_channel_policy": "RGB_3CH",
    "input_resolution": 512,
    "loss": {
      "name": "bce_dice",
      "bce_weight": 0.5,
      "dice_weight": 0.5,
      "dice_epsilon": 1e-06
    },
    "optimizer": {
      "name": "AdamW",
      "learning_rate": 0.0001,
      "weight_decay": 0.0001
    },
    "scheduler": {
      "name": "CosineAnnealingLR",
      "T_max": 100,
      "step": "per_epoch_after_train_and_val"
    },
    "training": {
      "batch_size": 4,
      "eval_batch_size": 8,
      "num_workers": 4,
      "persistent_workers": false,
      "max_epochs": 100,
      "early_stopping_patience": 15,
      "amp": true,
      "seed": 42,
      "gradient_accumulation_steps": 1,
      "effective_batch_size": 4,
      "threshold": 0.5,
      "sampling_policy": "phase20_domain_balanced_uniform_v1",
      "checkpoint_metric": "phase20_macro_domain_mean_dice_v1",
      "checkpoint_metric_description": "macro-domain mean VAL Dice (unweighted mean of the four per-domain per-image macro Dice)",
      "tie_break": "lower validation loss"
    },
    "augmentation_policy": "src.data.transforms.SegmentationTransform(train=True): horizontal mirror p=0.5, rotation +/-5 deg, brightness +/-0.10, contrast +/-0.10; mask NEAREST; VAL disabled",
    "governance": {
      "allow_test": false,
      "allow_external": false,
      "task_id_as_model_input": "CONDITIONING_ALLOWED",
      "task_id_forbidden_channels": [
        "mask_path",
        "foreground",
        "patient",
        "case",
        "gt_derived",
        "kub_category",
        "object_size_bin",
        "roi_coords"
      ],
      "film": true,
      "regional_module": false,
      "localizer": false,
      "roi_proposal": false,
      "benefit_router": false,
      "test_evaluation": false
    },
    "taxonomy_id": "kub_size_clean_v3_v1"
  }
}
```

## 6. The result (canonical VAL, 808 samples, threshold 0.5)

| Metric | Value |
|---|---|
| **macro-domain VAL Dice** | **0.8350794169575282** |
| 95% CI | [0.787749404492504, 0.8780060341568547] |
| macro-domain IoU | 0.7448366561463977 |
| pooled Dice (descriptive only) | 0.8784243406054913 |
| rank among six models | 1/6 |

| Domain | Dice | IoU |
|---|---|---|
| ISIC | 0.8971891751747457 | 0.8298191988836973 |
| BUSI | 0.8588228931389639 | 0.7636461980901246 |
| KVASIR | 0.8202473579060531 | 0.735522787626195 |
| KUB | 0.7640582416103505 | 0.6503584399855742 |

Bootstrap protocol: paired, domain-stratified, percentile; `n_boot=2000`, `seed=42`, resampling unit = image; **identical resampled VAL indices for both models** in every replicate. Paired comparison table below.

### 6.1 Paired bootstrap vs the five frozen baselines

`reports/tables/phase21_paired_bootstrap_vs_baselines.csv`

- size: `2446` bytes
- sha256: `d16ade357abb1beec172446a8154aec5f46013f74227bc47c32c7318788aa5bf`

```csv
model_a,model_b,observed_macro_dice_a,observed_macro_dice_b,observed_diff,diff_ci_low,diff_ci_high,ci_excludes_zero,p_value_two_sided,significant_at_0.05,n_boot,seed,resampling_unit,method,interpretation_guard
global_medfilm,unet,0.8350794169575282,0.7878323103837185,0.047247106573809705,0.03395372575378896,0.06057072784036907,True,0.0,True,2000,42,domain_stratified_paired_image,paired percentile bootstrap; same resampled VAL indices for both models,"A non-significant difference means the CI OVERLAPS zero; the two models must not be declared different. No architecture-matched control exists, so no causal attribution to FiLM is permitted."
global_medfilm,attention_unet,0.8350794169575282,0.7890365756433061,0.046042841314222094,0.033900185222353156,0.059170819885408746,True,0.0,True,2000,42,domain_stratified_paired_image,paired percentile bootstrap; same resampled VAL indices for both models,"A non-significant difference means the CI OVERLAPS zero; the two models must not be declared different. No architecture-matched control exists, so no causal attribution to FiLM is permitted."
global_medfilm,unetpp,0.8350794169575282,0.79200985543761,0.04306956151991814,0.03109831817311329,0.05594390027077758,True,0.0,True,2000,42,domain_stratified_paired_image,paired percentile bootstrap; same resampled VAL indices for both models,"A non-significant difference means the CI OVERLAPS zero; the two models must not be declared different. No architecture-matched control exists, so no causal attribution to FiLM is permitted."
global_medfilm,deeplabv3plus,0.8350794169575282,0.8276524069994395,0.007427009958088648,-0.002041778253366025,0.018312666571371754,False,0.124,False,2000,42,domain_stratified_paired_image,paired percentile bootstrap; same resampled VAL indices for both models,"A non-significant difference means the CI OVERLAPS zero; the two models must not be declared different. No architecture-matched control exists, so no causal attribution to FiLM is permitted."
global_medfilm,transformer_mit_unet,0.8350794169575282,0.8223827696935152,0.012696647264012983,0.00286046594759215,0.02264541281182093,True,0.013,True,2000,42,domain_stratified_paired_image,paired percentile bootstrap; same resampled VAL indices for both models,"A non-significant difference means the CI OVERLAPS zero; the two models must not be declared different. No architecture-matched control exists, so no causal attribution to FiLM is permitted."
```

**How to read that table.** A row is *separable* only when the CI excludes 0. Against `deeplabv3plus` the CI **includes 0** (p = 0.124), so Global MedFiLM and DeepLabV3+ are **tied** — do not claim a single winner. The other four baselines are separated.

### 6.2 Six-model accuracy comparison

`reports/tables/phase21_six_model_comparison.csv`

- size: `1448` bytes
- sha256: `81ee9990f90c4ef7c035ec89195cddb4582f72a533e9dd0e6fe421f7ca4fae45`

```csv
model_key,display_name,phase,params,macro_domain_dice,macro_domain_dice_ci_low,macro_domain_dice_ci_high,macro_domain_iou,pooled_dice_descriptive,dice_ISIC,dice_BUSI,dice_KVASIR,dice_KUB
global_medfilm,Global MedFiLM,21,,0.8350794169575282,0.787749404492504,0.8780060341568547,0.7448366561463977,0.8784243406054913,0.8971891751747457,0.8588228931389639,0.8202473579060531,0.7640582416103505
deeplabv3plus,DeepLabV3+,20B,40347041.0,0.8276524069994395,0.7707247524150636,0.87613136286568,0.741204783887321,0.8710387515780342,0.8853450897003098,0.8669176360310503,0.8196864443899969,0.7386604578764013
transformer_mit_unet,Transformer/MiT-style U-Net,20B,16347777.0,0.8223827696935152,0.7598816856532261,0.8755363425431457,0.7365987380965594,0.8737299208463981,0.8870904963527378,0.8639821887335537,0.8132768757279857,0.7251815179597835
unetpp,U-Net++,20A,9159681.0,0.79200985543761,0.7445723575169626,0.8381880974808651,0.6910262721598444,0.8412168142725415,0.8600736116535601,0.81630258330817,0.7710009445354833,0.7206622822532268
attention_unet,Attention U-Net,20B,7851285.0,0.7890365756433061,0.7287523896377449,0.8446846088108573,0.692749218587638,0.8328756074443346,0.8616938188891261,0.8276753987325884,0.7709990316787128,0.6957780532727972
unet,U-Net,20B,7763041.0,0.7878323103837185,0.7381428397969765,0.8375217809704605,0.6880960516732018,0.8354980550027805,0.8552735404680322,0.8197700214728889,0.7551962357227685,0.7210894438711845
```

### 6.3 Frozen five-model panel (the citable baseline ranking)

`reports/tables/phase20b_five_model_comparison.csv`

- size: `1566` bytes
- sha256: `6e2ea0522ee45af8017f6a914bba6c8f3e720a0f3d45cb379a6301a62288eea8`

```csv
﻿model_key,display_name,phase,class_name,module,source_file,architecture,params,best_epoch,best_macro_domain_dice,final_epoch,stop_reason,resume_count,per_domain_dice_ISIC,per_domain_dice_BUSI,per_domain_dice_KVASIR,per_domain_dice_KUB,status
deeplabv3plus,DeepLabV3+,20B,DeepLabV3Plus,src.models.deeplabv3plus,src/models/deeplabv3plus.py,deeplabv3plus_resnet50_os16_random_init_no_pretrained_aspp_rates_6_12_18,40347041,57,0.8276526736178511,72,EARLY_STOPPING_PATIENCE,0,0.885253,0.866908,0.819683,0.738766,COMPLETE
transformer_mit_unet,Transformer/MiT-style U-Net,20B,TransformerMiTUNet,src.models.transformer_mit_unet,src/models/transformer_mit_unet.py,transformer_mit_style_unet_local_random_init,16347777,74,0.8223808915834625,89,EARLY_STOPPING_PATIENCE,0,0.887129,0.864,0.8133,0.7252,COMPLETE
unetpp,UNet++,20A,UNetPP,src.models.unetpp,src/models/unetpp.py,unetpp_4_stage_nested_skip_base32,9159681,55,0.792007328746103,70,EARLY_STOPPING_PATIENCE,,0.8600706700810291,0.8163009576854252,0.7709952691976972,0.7206624180202605,COMPLETE
attention_unet,Attention U-Net,20B,AttentionUNet,src.models.attention_unet,src/models/attention_unet.py,attention_unet_4_stage_additive_skip_gates_base32,7851285,64,0.7890388550575124,79,EARLY_STOPPING_PATIENCE,0,0.861694912937533,0.827679296334774,0.7709997009042813,0.6957815100534616,COMPLETE
unet,U-Net,20B,UNet,src.models.unet,src/models/unet.py,unet_4_stage_plain_skip_base32,7763041,74,0.787832506974712,89,EARLY_STOPPING_PATIENCE,1,0.8552744720831389,0.8197688641298048,0.7551979881594655,0.7210887035264385,COMPLETE
```

## 7. Secondary analyses

### 7.1 Task-conditioning diagnostic

Verdict: **`see file`** — measured by re-scoring the frozen 64-case gallery with the WRONG task id. A large mean absolute Dice change means the conditioning is genuinely used.

### Conditioning diagnostic artifact

`reports/audits/phase21_task_conditioning_diagnostic.json`

- size: `1516` bytes
- sha256: `8084d339e02aeb866ca920fd0cf3e452fcee75e2a0ad24966a763c16bbb8a120`

```json
{
  "artifact": "phase21_task_conditioning_diagnostic",
  "phase": 21,
  "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
  "checkpoint_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
  "checkpoint_epoch": 66,
  "scope": "frozen 64-case gallery (16 per domain), reused UNCHANGED",
  "n_cases": 64,
  "design": "Per-case inference with the CORRECT task ID vs each INCORRECT task ID. The canonical VAL result is NOT recomputed and NOT replaced; this is a diagnostic only.",
  "threshold_frozen_before_reading": 0.005,
  "mean_abs_delta_dice_wrong_task": 0.18419164050715645,
  "max_abs_delta_dice_wrong_task": 0.9270517063993946,
  "mean_dice_correct_task": 0.859145553979417,
  "flag": "CONDITIONING_EFFECT_PRESENT",
  "flag_rule": "CONDITIONING_EFFECT_WEAK when mean|delta Dice| < 0.005",
  "honesty_note": "A weak effect is a legitimate scientific finding about this reference model and is reported as-is. It is NOT evidence that task conditioning is useless in general, and a strong effect here would NOT by itself prove that FiLM caused the benchmark gap (no architecture-matched control exists).",
  "film_parameter_summary": {
    "rows": 40,
    "tasks": 4,
    "sites": 5,
    "parameters": [
      "gamma",
      "beta"
    ],
    "table": "reports/tables/phase21_film_parameter_summary.csv"
  },
  "test_reads": {
    "test_image_reads": 0,
    "test_mask_reads": 0,
    "test_inference": 0,
    "test_visualization": 0
  }
}
```

### 7.2 KUB size strata (REPORTING ONLY)

KUB is stratified by a frozen taxonomy (`kub_size_clean_v3_v1`) using connected-8 components on the foreground (`mask > 0`), FULL_FIELD only. **These strata are a reporting device, never a selection or promotion criterion.**

Gallery stratum counts: `{"TINY": 44, "SMALL": 19, "MEDIUM": 27, "LARGE": 13, "ROI_NOT_PRIMARY_BINNED": 177}`

### 7.3 Cost / efficiency

| Metric | Value | Unit |
|---|---|---|
| macs | 31551740928 |  |
| gmacs | 31.5517 |  |
| gflops_2x | 63.1035 |  |

The MAC count is an **exact closed-form Conv2d/Linear count** and therefore a **LOWER BOUND** — it excludes norm, activation, pooling, interpolation and the element-wise FiLM ops. Cost is resolution-driven: the three stride-1 decoder stages each account for ~18.7% of total arithmetic.

### Six-model compute table

`reports/tables/phase21_six_model_compute.csv`

- size: `1193` bytes
- sha256: `5e88da50faaee41aba9efaf2c6ad07d92f5d5e6be058a727f00969d9ed9b8a24`

```csv
model_key,display_name,params,params_expected,params_match,macs,gmacs,gflops_2x,gmacs_per_mparam,task_ids_passed,input_shape,device,method,params_rank,gmacs_rank,params_vs_medfilm_x,gmacs_vs_medfilm_x
global_medfilm,Global MedFiLM,3523001,3523001,True,31551740928,31.5517,63.1035,8.9559,True,1x3x512x512,cpu,analytical Conv2d/Linear count (lower bound),1,1,1.0,1.0
unet,U-Net,7763041,7763041,True,46137344000,46.1373,92.2747,5.9432,False,1x3x512x512,cpu,analytical Conv2d/Linear count (lower bound),2,2,2.204,1.462
attention_unet,Attention U-Net,7851285,7851285,True,47218950144,47.219,94.4379,6.0142,False,1x3x512x512,cpu,analytical Conv2d/Linear count (lower bound),3,3,2.229,1.497
deeplabv3plus,DeepLabV3+,40347041,40347041,True,69139431424,69.1394,138.2789,1.7136,False,1x3x512x512,cpu,analytical Conv2d/Linear count (lower bound),6,4,11.452,2.191
transformer_mit_unet,Transformer/MiT,16347777,16347777,True,99098624000,99.0986,198.1972,6.0619,False,1x3x512x512,cpu,analytical Conv2d/Linear count (lower bound),5,5,4.64,3.141
unetpp,U-Net++,9159681,9159681,True,137942269952,137.9423,275.8845,15.0597,False,1x3x512x512,cpu,analytical Conv2d/Linear count (lower bound),4,6,2.6,4.372
```

### 7.4 Figure + notebook inventory

- notebook builds: `3` (three byte-identical: `True`)
- notebook path: `notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb`

- figures produced: **43** (embedded in notebook: 43)

## 8. Full Phase-21 report (verbatim)

The complete reviewer-facing report follows. This is the authoritative narrative and it supersedes anything summarised above.

### Phase-21 report

`reports/phase21_global_medfilm_report.md`

- size: `39490` bytes
- sha256: `4f0af7a907a5727e92933f1bca514bf93d1c6739a61be32597dece56767f99e1`

```markdown
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
```

## 9. Consolidated all-trained-models comparison

Every previously trained model in the project, on one page, with explicit **FROZEN vs LIVE** provenance.

### All trained models

`reports/tables/phase21_all_trained_models_comparison.md`

- size: `6703` bytes
- sha256: `4c8b86606c135fbc8b02d58cbb64eef7db5407ad3ff890963c7d8caf52b57343`

```markdown
# Consolidated comparison — all previously trained models

Generated 2026-09-28T22:56:40Z by `scripts/analysis/build_phase21_all_models_table.py`.

## ⚠️ Comparability notice — read before citing any number

This table mixes **two different kinds of evidence**:

| Provenance | Meaning |
|---|---|
| **FROZEN** | One canonical VAL pass over a frozen best checkpoint. Safe to cite as a benchmark result. |
| **LIVE** | A per-epoch validation value from a run that **has not terminated**. The checkpoint selection is **not final**. Orientation only — **not a result**. |

**Every row is FROZEN** — each is a single canonical VAL pass over a fixed best
checkpoint. The Phase-21 Global MedFiLM row was trained under the identical frozen
Phase-20 protocol, so the panel is directly comparable.

## 1. Full panel — macro-domain VAL Dice

| # | Model | Phase | Params | G MACs | Macro Dice | ISIC | BUSI | KVASIR | KUB | Provenance |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Global MedFiLM | 21 | 3,523,001 | 31.55 | **0.835079** | 0.8972 | 0.8588 | 0.8202 | 0.7641 | FROZEN |
| 2 | DeepLabV3+ | 20B | 40,347,041 | 69.14 | **0.827653** | 0.8853 | 0.8669 | 0.8197 | 0.7388 | FROZEN |
| 3 | Transformer/MiT-style U-Net | 20B | 16,347,777 | 99.10 | **0.822381** | 0.8871 | 0.8640 | 0.8133 | 0.7252 | FROZEN |
| 4 | UNet++ | 20A | 9,159,681 | 137.94 | **0.792007** | 0.8601 | 0.8163 | 0.7710 | 0.7207 | FROZEN |
| 5 | Attention U-Net | 20B | 7,851,285 | 47.22 | **0.789039** | 0.8617 | 0.8277 | 0.7710 | 0.6958 | FROZEN |
| 6 | U-Net | 20B | 7,763,041 | 46.14 | **0.787833** | 0.8553 | 0.8198 | 0.7552 | 0.7211 | FROZEN |

## 2. Frozen benchmark — the citable ranking (6 models)

| Rank | Model | Macro Dice | Best ep | Final ep | Params |
|---|---|---|---|---|---|
| 1 | Global MedFiLM | **0.835079** | 66 | 81 | 3,523,001 |
| 2 | DeepLabV3+ | **0.827653** | 57 | 72 | 40,347,041 |
| 3 | Transformer/MiT-style U-Net | **0.822381** | 74 | 89 | 16,347,777 |
| 4 | UNet++ | **0.792007** | 55 | 70 | 9,159,681 |
| 5 | Attention U-Net | **0.789039** | 64 | 79 | 7,851,285 |
| 6 | U-Net | **0.787833** | 74 | 89 | 7,763,041 |

Every row in this section is a frozen best checkpoint evaluated in ONE canonical VAL pass,
with `test_reads = 0` on all four counters.

### 2.1 Tier structure

| Tier | Models | Macro Dice band | Verdict |
|---|---|---|---|
| 1 | Global MedFiLM, DeepLabV3+, Transformer/MiT | 0.8224 – 0.8351 | Tier-1 band; Global MedFiLM separable from MiT/UNet++, NOT from DeepLabV3+ |
| 2 | U-Net++, Attention U-Net, U-Net | 0.7878 – 0.7920 | mutually indistinguishable |

Global MedFiLM leads the panel, but its paired CI against **DeepLabV3+** overlaps zero
(Δ +0.007427, CI [−0.002042, +0.018313], p = 0.124), so those two are **not separable**.

## 3. Paired domain-stratified bootstrap (all frozen models)

Within-panel comparisons. The Phase-21 Global MedFiLM vs-baseline bootstrap is reported
separately in the Phase-21 report §3 and in `phase21_paired_bootstrap_vs_baselines.csv`.

Method: paired percentile bootstrap, `n_boot=2000`, `seed=42`, resampling unit `domain_stratified_paired_image`, identical resampled VAL indices
for both models in each replicate.

| Model A | Model B | Δ(A−B) | 95% CI | p | Separable? |
|---|---|---|---|---|---|
| U-Net | DeepLabV3+ | -0.039820 | [-0.053127, -0.026640] | 0.000 | **YES** |
| Attention U-Net | DeepLabV3+ | -0.038616 | [-0.051391, -0.026347] | 0.000 | **YES** |
| DeepLabV3+ | U-Net++ | +0.035643 | [+0.023153, +0.047986] | 0.000 | **YES** |
| U-Net | Transformer/MiT | -0.034550 | [-0.048555, -0.020799] | 0.000 | **YES** |
| Attention U-Net | Transformer/MiT | -0.033346 | [-0.046688, -0.021403] | 0.000 | **YES** |
| Transformer/MiT | U-Net++ | +0.030373 | [+0.016946, +0.044389] | 0.000 | **YES** |
| DeepLabV3+ | Transformer/MiT | +0.005270 | [-0.004246, +0.013870] | 0.282 | no (CI spans 0) |
| U-Net | U-Net++ | -0.004178 | [-0.015182, +0.007565] | 0.488 | no (CI spans 0) |
| Attention U-Net | U-Net++ | -0.002973 | [-0.014766, +0.008504] | 0.577 | no (CI spans 0) |
| U-Net | Attention U-Net | -0.001204 | [-0.009941, +0.008359] | 0.830 | no (CI spans 0) |

**Key conclusion:** the top-two ordering (DeepLabV3+ vs Transformer/MiT) is **NOT**
significant (Δ +0.005270, CI [−0.004246, +0.013870], p = 0.282). These two models are
**tied** on this evidence — never claim a single winner. The three U-Net-family variants
are likewise mutually indistinguishable. Only the Tier-1 / Tier-2 separation is robust.

## 4. Per-domain breakdown (frozen panel)

| Model | ISIC | BUSI | KVASIR | KUB | Macro | Strongest | Weakest |
|---|---|---|---|---|---|---|---|
| Global MedFiLM | 0.8972 | 0.8588 | 0.8202 | 0.7641 | **0.835079** | ISIC | KUB |
| DeepLabV3+ | 0.8853 | 0.8669 | 0.8197 | 0.7388 | **0.827653** | ISIC | KUB |
| Transformer/MiT-style U-Net | 0.8871 | 0.8640 | 0.8133 | 0.7252 | **0.822381** | ISIC | KUB |
| UNet++ | 0.8601 | 0.8163 | 0.7710 | 0.7207 | **0.792007** | ISIC | KUB |
| Attention U-Net | 0.8617 | 0.8277 | 0.7710 | 0.6958 | **0.789039** | ISIC | KUB |
| U-Net | 0.8553 | 0.8198 | 0.7552 | 0.7211 | **0.787833** | ISIC | KUB |

**KUB is the bottleneck for every model** and the field is tightest there (span 0.6958–0.7388,
~4.3 pp). ISIC and BUSI are saturated (all models within ~3.2 pp and ~5.1 pp respectively).

## 5. Parameter / compute cost axis

| Model | Params | Params rank | G MACs | MACs rank | vs MedFiLM (×) |
|---|---|---|---|---|---|
| Global MedFiLM | 3,523,001 | 1/6 | 31.5517 | 1/6 | 1.000 |
| U-Net | 7,763,041 | 2/6 | 46.1373 | 2/6 | 1.462 |
| Attention U-Net | 7,851,285 | 3/6 | 47.2190 | 3/6 | 1.497 |
| DeepLabV3+ | 40,347,041 | 6/6 | 69.1394 | 4/6 | 2.191 |
| Transformer/MiT | 16,347,777 | 5/6 | 99.0986 | 5/6 | 3.141 |
| U-Net++ | 9,159,681 | 4/6 | 137.9423 | 6/6 | 4.372 |

Global MedFiLM is the **lightest on both axes** of this six-model panel, but its absolute
cost (31.55 G MACs at 512 px) is not small. Measurement is an exact closed-form
Conv2d/Linear count and is therefore a **lower bound**.


## 6. Phase-21 status

- Epochs completed: **81** (best at epoch 66)
- Stop reason: **EARLY_STOPPING_PATIENCE**
- Early-stopping patience used: **15 / 15**
- Resume count: **1** (one host teardown recovered)
- Macro-domain VAL Dice (ONE canonical pass over 808 VAL samples): **0.835079**
- The canonical VAL pass has completed, so this row is directly comparable to the
  frozen panel in §2. See §3 of the Phase-21 report for the paired bootstrap
  against each frozen baseline (this table's §3 covers the frozen panel only).
```

## 10. Governance and freeze evidence

| Check | Result |
|---|---|
| freeze_verified | `True` |
| validation_problems | `[]` |
| terminal_state | `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED` |
| phase22_eligible | `True` |
| phase22_started | `False` |
| test_reads_total_observed | `0` |
| test_lock_clean | `True` |
| manifest_version | `phase4_v3` |
| val_population | `808` |
| train_population | `5832` |

### 10.1 Interpretation guard (binding on any write-up)

- **PERMITTED:** Global MedFiLM achieved X compared with baseline Y.
- **FORBIDDEN:** FiLM caused +X.
- **Reason:** No architecture-matched control exists (no identical plain model trained under the Phase-21 run), so the difference cannot be causally attributed to FiLM.
- **CI-overlap rule:** Where the paired CI overlaps zero, the models are NOT separable and no ordering claim may be made.

### 10.2 Final freeze artifact (authoritative)

`reports/audits/phase21_final_freeze.json`

- size: `13481` bytes
- sha256: `aad7baab700710dcf51f0b549b52ddd340bd06d1ec50c39a86f48b00745e98af`

```json
{
  "artifact": "phase21_final_freeze",
  "phase": 21,
  "title": "PHASE 21 \u2014 GLOBAL MEDFILM REFERENCE / FOUR-DOMAIN TASK-CONDITIONED GLOBAL SEGMENTATION",
  "generated_utc": "2026-09-28T23:05:48.599056+00:00",
  "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
  "architecture_id": "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1",
  "is_final_ra_medfilm_seg_plus_plus": false,
  "is_global_reference_only": true,
  "terminal_state": "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED",
  "phase22_eligible": true,
  "phase22_started": false,
  "frozen_bindings": {
    "protocol_path": "reports/audits/phase20_shared_global_baseline_protocol.json",
    "protocol_sha256": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
    "protocol_sha256_expected": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
    "protocol_sha_matches": true,
    "protocol_binding": "reports/audits/phase21_protocol_binding.json",
    "protocol_binding_sha256": "d86a6b04c080ddad33df885977b114a152b4bd7c39849332ce0d921cb3717882",
    "protocol_unintentional_differences": [],
    "architecture_binding": "reports/audits/phase21_global_medfilm_architecture_binding.json",
    "architecture_binding_sha256": "21e2c195c8da33da761965817bab99f0eeec5fa84a846d05ae765b9567017e78",
    "entry_gate": "reports/audits/phase21_entry_gate.json",
    "entry_gate_verdict": "PHASE21_ENTRY_GATE_PASS",
    "pre_execution_check": "reports/audits/phase21_pre_execution_check.json",
    "pre_execution_verdict": "PHASE21_PRE_EXECUTION_CHECK_PASS",
    "legacy_medfilm_audit": "reports/audits/phase21_legacy_medfilm_architecture_audit.json"
  },
  "training": {
    "logical_runs": 1,
    "architecture_sweep_performed": false,
    "hyperparameter_sweep_performed": false,
    "seed": 42,
    "best_epoch": 66,
    "final_epoch": 81,
    "stop_reason": "EARLY_STOPPING_PATIENCE",
    "early_stopping_patience": 15,
    "resume_count": 1,
    "independent_duplicate_runs": 0,
    "best_macro_domain_dice": 0.8350791259413984,
    "best_val_loss": 0.14694273973455524,
    "per_domain_dice_at_best": {
      "ISIC": 0.8971889995309819,
      "BUSI": 0.8588225990533829,
      "KVASIR": 0.8202460642006006,
      "KUB": 0.764058840980628
    },
    "model_params": 3523001,
    "total_elapsed_seconds": 34588.8289809227,
    "selection_rule_id": "phase20_macro_domain_mean_dice_v1",
    "checkpoint_selection_replay_verdict": "PHASE21_CHECKPOINT_SELECTION_REPLAY_PASS",
    "checkpoint_selection_replay_matches": true,
    "best_checkpoint_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "history_sha256": "e2ea06c5261c6fce155e9bc7109a1c03e77ba55c638a16250ade61e8a39022a0",
    "trainer_sha256": "ec17641b8e6e680af4e912332dbae00cf5d66e56b33cac70229e39d506f20785"
  },
  "canonical_val_evaluation": {
    "canonical_val_inference_runs": 1,
    "samples_expected": 808,
    "samples_evaluated": 808,
    "threshold": 0.5,
    "no_tta": true,
    "no_threshold_tuning": true,
    "no_morphology": true,
    "prob_maps_persisted": 808,
    "per_image_table": "reports/tables/phase21_per_image_val_metrics.csv",
    "per_image_table_sha256": "8d8dad2cc12d00bd41c89b921d97940cc2f02543a66585efb1f6c3d0c6c9cf84"
  },
  "results": {
    "global_medfilm": {
      "macro_domain_dice": 0.8350794169575282,
      "macro_domain_dice_ci_low": 0.787749404492504,
      "macro_domain_dice_ci_high": 0.8780060341568547,
      "macro_domain_iou": 0.7448366561463977,
      "pooled_dice_descriptive": 0.8784243406054913,
      "per_domain_dice": {
        "ISIC": 0.8971891751747457,
        "BUSI": 0.8588228931389639,
        "KVASIR": 0.8202473579060531,
        "KUB": 0.7640582416103505
      },
      "per_domain_iou": {
        "ISIC": 0.8298191988836973,
        "BUSI": 0.7636461980901246,
        "KVASIR": 0.735522787626195,
        "KUB": 0.6503584399855742
      },
      "per_domain_extra": {
        "ISIC": {
          "roc_auc": 0.991544817720604,
          "pr_auc_average_precision": 0.9674908019135804,
          "brier": 0.02693255497526657,
          "ece": 0.019945425553596977,
          "mce": 0.21818451006185735
        },
        "BUSI": {
          "roc_auc": 0.9819675115222886,
          "pr_auc_average_precision": 0.922583931821467,
          "brier": 0.010592866374221717,
          "ece": 0.009552320531188993,
          "mce": 0.32401996356225293
        },
        "KVASIR": {
          "roc_auc": 0.9561335977421732,
          "pr_auc_average_precision": 0.8705654419416674,
          "brier": 0.04157783046939034,
          "ece": 0.03759042214933916,
          "mce": 0.26462594297066955
        },
        "KUB": {
          "roc_auc": 0.987864602168808,
          "pr_auc_average_precision": 0.9347717745524698,
          "brier": 0.032934732279694186,
          "ece": 0.01773981256331223,
          "mce": 0.19247466176034345
        }
      },
      "params": 3523001,
      "rank_among_six": 1
    },
    "six_model_ranking": [
      "global_medfilm",
      "deeplabv3plus",
      "transformer_mit_unet",
      "unetpp",
      "attention_unet",
      "unet"
    ],
    "benchmark_top_model": {
      "model_key": "global_medfilm",
      "display_name": "Global MedFiLM",
      "macro_domain_dice": 0.8350794169575282
    },
    "paired_bootstrap": {
      "comparisons": 5,
      "significant_vs_baselines": [
        "unet",
        "attention_unet",
        "unetpp",
        "transformer_mit_unet"
      ],
      "non_significant_vs_baselines": [
        "deeplabv3plus"
      ],
      "method": "paired domain-stratified percentile bootstrap, n_boot=2000, seed=42"
    },
    "tables": {
      "six_model_comparison": "reports/tables/phase21_six_model_comparison.csv",
      "paired_bootstrap": "reports/tables/phase21_paired_bootstrap_vs_baselines.csv",
      "domain_performance": "reports/tables/phase21_global_medfilm_domain_performance.csv",
      "domain_bootstrap_ci": "reports/tables/phase21_global_medfilm_domain_bootstrap_ci.csv",
      "calibration_ranking": "reports/tables/phase21_global_medfilm_calibration_ranking.csv"
    }
  },
  "kub": {
    "subgroup_table": "reports/tables/phase21_kub_subgroup_analysis.csv",
    "subgroup_role": "REPORTING_ONLY",
    "size_taxonomy_id": "kub_size_clean_v3_v1",
    "size_table": "reports/tables/phase21_kub_size_stratification.csv",
    "size_n": {
      "TINY": 44,
      "SMALL": 19,
      "MEDIUM": 27,
      "LARGE": 13,
      "ROI_NOT_PRIMARY_BINNED": 177
    },
    "tiny_stratum_preserved_for_phase22": true,
    "optimised_on_tiny": false
  },
  "conditioning": {
    "diagnostic": "reports/audits/phase21_task_conditioning_diagnostic.json",
    "flag": "CONDITIONING_EFFECT_PRESENT",
    "mean_abs_delta_dice_wrong_task": 0.18419164050715645,
    "n_cases": 64,
    "scope": "frozen 64-case gallery (16 per domain), reused UNCHANGED",
    "film_parameter_summary": "reports/tables/phase21_film_parameter_summary.csv",
    "film_sites": [
      "bridge",
      "decoder4",
      "decoder3",
      "decoder2",
      "decoder1"
    ]
  },
  "gallery": {
    "frozen_64_reused_unchanged": true,
    "gallery_selection": "reports/tables/phase21_gallery_selection_64.csv",
    "gallery_cases": 64,
    "six_model_panel_figures": "reports/figures/phase21_global_medfilm/gallery/",
    "detailed_gallery_figures": "reports/figures/phase21_global_medfilm/gallery/",
    "failure_gallery_figures": "reports/figures/phase21_global_medfilm/failure/",
    "analytical_outcome_selected_label_used": true
  },
  "figures": {
    "figure_root": "reports/figures/phase21_global_medfilm",
    "n_figures": 43,
    "n_embedded_in_notebook": 43,
    "groups": {
      "comparison": 17,
      "conditioning": 5,
      "efficiency": 3,
      "failure": 2,
      "gallery": 8,
      "kub": 2,
      "training": 6
    },
    "inventory": "reports/figures/phase21_global_medfilm/phase21_figure_inventory.csv"
  },
  "notebook": {
    "path": "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb",
    "sha256": "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed",
    "determinism": {
      "artifact": "phase21_notebook_determinism",
      "phase": 21,
      "notebook_path": "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb",
      "builds": 3,
      "sha256_per_build": [
        "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed",
        "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed",
        "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed"
      ],
      "three_builds_byte_identical": true,
      "deterministic_practices": [
        "deterministic cell ids (p21000..p21NNN)",
        "stripped metadata.execution",
        "coalesced stream outputs",
        "fixed pandas Styler uuids via set_uuid",
        "normalised object memory addresses (0x... -> 0xADDR)",
        "stable output ordering"
      ],
      "test_reads": 0
    },
    "three_builds_byte_identical": true
  },
  "efficiency": {
    "parameter_count": 3523001,
    "macs": 31551740928,
    "macs_reason": "no third-party FLOP-counting library is installed (thop/fvcore/ptflops/torchinfo all absent); the analytical count above is used instead and is exact for conv/linear layers",
    "measurement_only": true,
    "no_optimisation_performed": true,
    "table": "reports/tables/phase21_efficiency_accounting.csv"
  },
  "governance": {
    "film_used": true,
    "task_conditioning_used": true,
    "task_id_role": "CONDITIONING_ALLOWED (FiLM task embedding only)",
    "forbidden_components": {
      "roi_proposal": false,
      "localizer": false,
      "regional_refiner": false,
      "high_resolution_crop_branch": false,
      "global_regional_fusion": false,
      "benefit_predictor": false,
      "counterfactual_refinement_gain": false,
      "resource_budget_router": false,
      "adaptive_conditional_computation": false,
      "mobile_compression": false,
      "pruning": false,
      "quantization": false,
      "distillation": false,
      "architecture_search": false,
      "test_evaluation": false
    },
    "forbidden_components_present": [],
    "test_locks": {
      "test_image_reads": 0,
      "test_mask_reads": 0,
      "test_inference": 0,
      "test_visualization": 0
    },
    "test_reads_total_observed": 0,
    "test_lock_clean": true,
    "manifest_version": "phase4_v3",
    "val_population": 808,
    "train_population": 5832
  },
  "interpretation": {
    "permitted": "Global MedFiLM achieved X compared with baseline Y.",
    "forbidden": "FiLM caused +X.",
    "reason": "No architecture-matched control exists (no identical plain model trained under the Phase-21 run), so the difference cannot be causally attributed to FiLM.",
    "ci_overlap_rule": "Where the paired CI overlaps zero, the models are NOT separable and no ordering claim may be made.",
    "historical_results_claimed_as_current": false
  },
  "artifacts": {
    "audits": [
      "reports/audits/phase21_entry_gate.json",
      "reports/audits/phase21_legacy_medfilm_architecture_audit.json",
      "reports/audits/phase21_protocol_binding.json",
      "reports/audits/phase21_global_medfilm_architecture_binding.json",
      "reports/audits/phase21_pre_execution_check.json",
      "reports/audits/phase21_prediction_manifest.json",
      "reports/audits/phase21_val_evaluation.json",
      "reports/audits/phase21_analysis.json",
      "reports/audits/phase21_paired_bootstrap.json",
      "reports/audits/phase21_global_medfilm_confusion_matrices.json",
      "reports/audits/phase21_task_conditioning_diagnostic.json",
      "reports/audits/phase21_efficiency_accounting.json",
      "reports/audits/phase21_notebook_determinism.json"
    ],
    "tables": [
      "reports/tables/phase21_per_image_val_metrics.csv",
      "reports/tables/phase21_prediction_manifest.csv",
      "reports/tables/phase21_global_medfilm_domain_performance.csv",
      "reports/tables/phase21_global_medfilm_domain_bootstrap_ci.csv",
      "reports/tables/phase21_global_medfilm_confusion_matrices.csv",
      "reports/tables/phase21_global_medfilm_calibration_ranking.csv",
      "reports/tables/phase21_kub_subgroup_analysis.csv",
      "reports/tables/phase21_kub_size_stratification.csv",
      "reports/tables/phase21_kub_size_stratification_per_sample.csv",
      "reports/tables/phase21_six_model_comparison.csv",
      "reports/tables/phase21_paired_bootstrap_vs_baselines.csv",
      "reports/tables/phase21_per_image_all_models.csv",
      "reports/tables/phase21_task_conditioning_diagnostic.csv",
      "reports/tables/phase21_task_conditioning_per_case.csv",
      "reports/tables/phase21_film_parameter_summary.csv",
      "reports/tables/phase21_efficiency_accounting.csv",
      "reports/tables/phase21_gallery_selection_64.csv"
    ],
    "predictions_root": "reports/predictions/phase21_global_medfilm_fourdomain_seed42_clean_v3/val",
    "figures_root": "reports/figures/phase21_global_medfilm"
  },
  "validation_problems": [],
  "freeze_verified": true
}
```

### 10.3 Progress status

`reports/audits/phase21_progress_status.json`

- size: `1651` bytes
- sha256: `279955c61190cf6fd80a368cee25d838ed09dbf50f666c386982f0447fc6c031`

```json
{
  "artifact": "phase21_progress_status",
  "phase": 21,
  "generated_utc": "2026-09-28T22:55:15.678256+00:00",
  "phase_state": "COMPLETE",
  "experiment_id": "phase21_global_medfilm_fourdomain_seed42_clean_v3",
  "architecture_id": "global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1",
  "protocol_sha256": "b74f1f9f429adbce374f0306180943b9f373f872e1e69e115b7d17e81414283c",
  "protocol_sha_matches_frozen": true,
  "entry_gate_verdict": "PHASE21_ENTRY_GATE_PASS",
  "protocol_binding_verdict": "PHASE21_PROTOCOL_BINDING_PASS",
  "protocol_unintentional_differences": [],
  "architecture_binding_verdict": "PHASE21_ARCHITECTURE_FROZEN",
  "pre_execution_verdict": "PHASE21_PRE_EXECUTION_CHECK_PASS",
  "model_params": 3523001,
  "training": {
    "epochs_completed": 81,
    "best_epoch": 66,
    "best_macro_domain_dice": 0.8350791259413984,
    "mean_epoch_seconds": 426.641326674074,
    "naturally_terminated": true,
    "stop_reason": "EARLY_STOPPING_PATIENCE",
    "resume_count": 1
  },
  "canonical_val": {
    "completed": true,
    "canonical_val_inference_runs": 1,
    "samples_evaluated": 808
  },
  "results_available": true,
  "final_freeze_written": true,
  "terminal_state": "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED",
  "target_terminal_state": "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED",
  "phase22_started": false,
  "report_path": "reports/phase21_global_medfilm_report.md",
  "test_reads": {
    "test_image_reads": 0,
    "test_mask_reads": 0,
    "test_inference": 0,
    "test_visualization": 0
  }
}
```

### 10.4 Governance sync (additive only)

`reports/audits/phase21_governance_sync.json`

- size: `805` bytes
- sha256: `e4fbbfe82ebba257c0a7876a34144e935e48fc74981c2508f64fcc520d5dc81c`

```json
{
  "artifact": "phase21_governance_sync",
  "phase": 21,
  "generated_utc": "2026-09-28T23:05:49.166335+00:00",
  "additive_only": true,
  "frozen_science_modified": false,
  "notebook_path": "notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb",
  "notebook_sha256": "bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed",
  "files_changed": [
    "phasewise_notebook_map.csv",
    "phasewise_notebook_map.json",
    "phasewise_notebook_map.md",
    "phasewise_notebook_execution_manifest.md"
  ],
  "phase_status": {
    "20A": "COMPLETE",
    "20B": "COMPLETE",
    "21": "COMPLETE",
    "22": "ELIGIBLE_NOT_STARTED"
  },
  "terminal_state": "PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED",
  "test_reads": 0
}
```

## 11. Repository conventions the reviewer should assume

| Item | Convention |
|---|---|
| Manifest | `manifests/phase4_v3/` — TRAIN 5832 / VAL 808 / TEST 1683 / QUARANTINED 118. Root `manifests/*.csv` are the OLD frozen phase4_v2 set: never load. |
| Foreground mask | `mask > 0` (connectivity 8) — never `mask == 1` |
| Preprocessing | aspect-preserving resize + centre pad, `scale = min(s/w, s/h)`, sizes {256, 512, 768, 1024}; Phase-21 model uses RGB 3ch at 512 px |
| Metrics | Dice/IoU at threshold 0.5, eps 1e-7 |
| Determinism | TRAIN is stochastic (augmentation); VAL is deterministic. Bitwise GPU determinism is NOT claimed. |
| Run artifacts | `experiments/<id>/` holds history/state/config/closure; `checkpoints/<id>/` holds ONLY best/last/latest `.pt` |
| Result presentation | Stock convention: **increase = red, decrease = green**, currency ¥ (for any charts) |

### 11.1 Task / domain ids

| task_id | Domain | Notes |
|---|---|---|
| 0 | ISIC 2018 | RGB, dermoscopy |
| 1 | BUSI | grayscale, ultrasound |
| 2 | Kvasir-SEG | RGB, endoscopy |
| 3 | KUB | grayscale/RGB, radiography |

## 12. Open questions / what legitimately comes next

Phase 21 answered a narrow question: *does a single shared, task-conditioned network hold up against five per-domain baselines under one frozen protocol?* It does, as a **GLOBAL reference**. What is deliberately NOT established:

1. **No causal attribution to FiLM** — there is no architecture-matched plain control trained under this run. A control run would be needed to isolate the conditioning effect.
2. **Global MedFiLM vs DeepLabV3+ is a tie**, not a win (CI spans zero, p = 0.124).
3. **No deployment claim.** 31.55 G MACs at 512 px is the lightest in the panel, but that is a *relative* statement; nothing here shows fitness for constrained hardware.
4. **No compression / distillation / NAS / pruning work** has been done.
5. **No ROI, localizer, regional refiner, fusion, benefit predictor or router** — the full `RA-MedFiLM-Seg++` is untouched.
6. **KUB is the bottleneck** for every model in the panel (best KUB Dice ≈ 0.764 here).

## 13. Artifact hash index

Use these to confirm the reviewer is reasoning about exactly this revision.

| Artifact | sha256 |
|---|---|
| `reports/audits/phase21_final_freeze.json` | `aad7baab700710dcf51f0b549b52ddd340bd06d1ec50c39a86f48b00745e98af` |
| `reports/audits/phase21_analysis.json` | `24a92bc09d3bf8f1c33eb7550421779fc8642747b5e0b914ea69781b7bed01b6` |
| `reports/audits/phase21_val_evaluation.json` | `fdcba4126d9a99f19d80aebe8c0956956a4738d68979cd7ab90a598050d0b201` |
| `reports/tables/phase21_paired_bootstrap_vs_baselines.csv` | `d16ade357abb1beec172446a8154aec5f46013f74227bc47c32c7318788aa5bf` |
| `reports/tables/phase21_six_model_comparison.csv` | `81ee9990f90c4ef7c035ec89195cddb4582f72a533e9dd0e6fe421f7ca4fae45` |
| `reports/tables/phase21_six_model_compute.csv` | `5e88da50faaee41aba9efaf2c6ad07d92f5d5e6be058a727f00969d9ed9b8a24` |
| `reports/tables/phase21_all_trained_models_comparison.md` | `4c8b86606c135fbc8b02d58cbb64eef7db5407ad3ff890963c7d8caf52b57343` |
| `reports/phase21_global_medfilm_report.md` | `4f0af7a907a5727e92933f1bca514bf93d1c6739a61be32597dece56767f99e1` |
| `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/phase21_training_closure.json` | `5d58c9233160e77fad6a03f1cb53907345b14cf9a0c8418f3a5d56d1fb0391ac` |
| `notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb` | `bb916f54296719b0c38643c0a9302e713cacd33a418850dc9b316d8d9a26a4ed` |

---

## 14. Suggested prompt to hand to the external reviewer

> You are reviewing a completed machine-learning experiment, Phase 21 of a phase-wise medical image segmentation project. The attached document is a complete, self-contained snapshot: status, frozen protocol, architecture, results, statistical comparisons, cost, governance evidence, and the explicit constraints. Read section 2 (hard constraints) and section 10.1 (interpretation guard) first — they are binding. Section 12 lists what is deliberately NOT established. Then propose the single best next step for this project, and justify it against the constraints. If your proposal requires reading the TEST split, re-running the canonical VAL pass, changing the frozen protocol, or starting Phase 22, it is not admissible. State explicitly which open question in section 12 your proposal addresses.
