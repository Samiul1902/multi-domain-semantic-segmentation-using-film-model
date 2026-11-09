# Phase 08 Part 1A — CLEAN-v3 Infrastructure Audit

**Status:** `PASS`  
**Model:** Gemini 3.8 Flash Medium  
**Generated:** 2026-09-20T04:49:57.809067+00:00

## Environment

| Field | Value |
|---|---|
| PyTorch | `2.6.0+cu124` |
| CUDA available | True |
| CUDA device | NVIDIA GeForce RTX 3060 Ti |
| CUDA runtime | `12.4` |
| cuDNN | 90100 |
| Canonical requires CUDA | True |

## Manifest verification

| Field | Value |
|---|---|
| manifest_version | `phase4_v3` |
| guard ok | True |
| TRAIN rows | 5832 |
| VAL rows | 808 |
| KUB TRAIN cases | 1978 |
| KUB VAL cases | 280 |
| TRAIN patients | 318 |
| VAL patients | 111 |
| patient overlap | 0 |
| TEST metadata rows (never decoded) | 558 |

## Target contract

- Foreground rule: **`mask > 0`**
- Samples audited: 360
- Raw label union: [0, 1, 2, 3, 255]
- Non-1 foreground labels: [2, 3, 255]
- Binarization equivalence failures: 0
- Non-binary after binarize: 0

### Observed raw label signatures

| Signature | Samples |
|---|---:|
| `0|1` | 120 |
| `0|1|2` | 3 |
| `0|2` | 117 |
| `0|255` | 23 |
| `0|3` | 97 |

## Image mode / channel convention

- Input channels: **1**
- KUBDataset calls Image.convert("L") then unsqueeze(0), so both RGB (FULL_FIELD) and L (ROI) images become a 1-channel tensor. This is the historical convention and is preserved.

| Source mode | Tensor channels | Shape |
|---|---:|---|
| L | 1 | `(1, 256, 256)` |
| RGB | 1 | `(1, 256, 256)` |

## Transform contract

| Target | Source | scale | resized | pad (l,t,r,b) | aligned | mask binary |
|---|---:|---:|---|---|---:|---:|
| 256 | 3072x3072 | 0.083333 | 256x256 | (0,0,0,0) | True | True |
| 256 | 2880x2304 | 0.088889 | 205x256 | (25,0,26,0) | True | True |
| 256 | 80x60 | 3.200000 | 192x256 | (32,0,32,0) | True | True |
| 256 | 512x512 | 0.500000 | 256x256 | (0,0,0,0) | True | True |
| 512 | 3072x3072 | 0.166667 | 512x512 | (0,0,0,0) | True | True |
| 512 | 2880x2304 | 0.177778 | 410x512 | (51,0,51,0) | True | True |
| 512 | 80x60 | 6.400000 | 384x512 | (64,0,64,0) | True | True |
| 512 | 512x512 | 1.000000 | 512x512 | (0,0,0,0) | True | True |

## Metric contract

| Metric | Module | Version | Threshold | Epsilon | Empty handling |
|---|---|---|---|---|---|
| dice | `src.metrics.segmentation` | v1 | 0.5 | 1e-07 | epsilon-smoothed, defined for empty masks |
| iou | `src.metrics.segmentation` | v1 | 0.5 | 1e-07 | epsilon-smoothed |
| precision | `src.metrics.segmentation` | v1 | 0.5 | 1e-07 | epsilon-smoothed |
| recall | `src.metrics.segmentation` | v1 | 0.5 | 1e-07 | epsilon-smoothed |
| hd95 | `src.metrics.segmentation` | v1 | nan | nan | explicit hd95_valid flag; NaN or supplied penalty; never 0 |
| object_recall | `src.metrics.object_metrics` | phase14_authoritative | nan | nan | NaN recall when no GT components |

## Reproducibility

| Check | Result | Detail |
|---|---|---|
| python_numpy_torch_seed | PASS | set_seed reproduces python/numpy/torch draws |
| cuda_seed | PASS | cuda.manual_seed_all reproduces CUDA draws |
| dataloader_generator | PASS | make_generator(seed) is reproducible |
| worker_seed | PASS | seed_worker produces deterministic per-worker streams |
| rng_state_roundtrip | PASS | capture/restore reproduces the torch CPU stream |
| determinism_policy | DOCUMENTED | cudnn.deterministic=True, cudnn.benchmark=False; bitwise GPU determinism is NOT claimed |
| torch_deterministic_algorithms | False | not force-enabled: some CUDA ops lack deterministic kernels |

## Checkpoint contract

| Item | Supported | Detail |
|---|---|---|
| model_state | True | written by save_training_checkpoint |
| optimizer_state | True | written by save_training_checkpoint |
| scheduler_state | True | written by save_training_checkpoint |
| grad_scaler_state | True | written by save_training_checkpoint |
| epoch | True | written by save_training_checkpoint |
| best_validation_score | True | written by save_training_checkpoint |
| experiment_id | True | written by save_training_checkpoint |
| seed | True | written by save_training_checkpoint |
| manifest_version | True | written by save_training_checkpoint |
| taxonomy_id | True | written by save_training_checkpoint |
| configuration | True | written by save_training_checkpoint |
| random_state | True | written by save_training_checkpoint |
| taxonomy_id_parameter | True | additive Phase-08 parameter |
| rng_state | True | capture_random_state()/restore_random_state() |
| roundtrip_experiment_id | True | phase08_infra_probe |
| roundtrip_taxonomy_id | True | kub_size_clean_v3_v1 |
| roundtrip_manifest_version | True | phase4_v3 |

## Taxonomy integration

- taxonomy_id: `kub_size_clean_v3_v1`
- thresholds: {'Q25': 0.0001497998649691358, 'Q50': 0.0003401438395182292, 'Q75': 0.0008279682677469136}
- ROI handling: `ROI_NOT_PRIMARY_BINNED`
- ROI-specific taxonomy created: False

## Loader sample audit

- Cases: 16
- Selection SHA: `c29d47a855c56a2fa3218a23b133e3380de9ee89a28790622794f874a83abc2b`
- Acquisition types: {'ROI': 8, 'FULL_FIELD': 8}
- Categories: {'Bladder_Stone': 7, 'Kidney_Stone': 6, 'Ureteric_Stone': 3}
- Raw label signatures: {'0|255': 8, '0|1': 3, '0|2': 2, '0|3': 2, '0|1|2': 1}
- All masks binary: True

## CUDA smoke test (INFRASTRUCTURE_TEST_ONLY)

- Label: **INFRASTRUCTURE_TEST_ONLY**
- Device: NVIDIA GeForce RTX 3060 Ti
- Batches: 2 (batch size 2)
- Input shape: `(2, 1, 256, 256)` | target shape: `(2, 1, 256, 256)`
- Target binary: True
- Losses finite: True
- AMP enabled: True | GradScaler used: True
- Peak GPU memory: 53.28 MB
- Scientific claim: **NONE**

## Governance

- TEST content reads: 0
- TEST image reads: 0
- TEST mask reads: 0
- TEST metrics: 0
- TEST visualizations: 0
- Full training performed: False
- Scientific performance claims: NONE
- Phase 09 started: False

## Scientific / engineering gate

| Gate | Result |
|---|---|
| manifest_phase4_v3_validated | PASS |
| kub_counts_ok | PASS |
| mask_gt_zero_enforced | PASS |
| non_one_labels_exercised | PASS |
| input_channel_convention_documented | PASS |
| transform_geometry_verified | PASS |
| mask_nearest_neighbour_verified | PASS |
| cuda_required_path_works | PASS |
| reproducibility_helpers_work | PASS |
| metric_contract_explicit | PASS |
| taxonomy_integration_works | PASS |
| checkpoint_roundtrip_works | PASS |
| cuda_smoke_passed | PASS |
| no_test_content_access | PASS |
| no_baseline_training | PASS |
| loader_audit_ge_12 | PASS |
| gallery_ge_12 | PASS |

**Overall: PASS**

## Table artifacts

| Table | SHA-256 |
|---|---|
| `phase08_kub_v3_loader_sample_audit.csv` | `5da08756a67a8666c12095cda8fdd51afc4989bf0bf79fa23a773aef41748cfd` |
| `phase08_transform_contract_audit.csv` | `8ebdfb532f6ec3c45f0dcd55a42594824468ca4806349810ae6e5faba84e4c17` |
| `phase08_metric_contract.csv` | `030210f16d841591c652d7eff2f228c8beab2221845591c6a0ab2cbfb45aaa86` |
| `phase08_reproducibility_audit.csv` | `725ddce8fccef503291b5c7e48a6d2482de38500a27853b9c87d95a6d1009928` |
| `phase08_checkpoint_contract.csv` | `a7519387ff3f2c3bb36c93f830da221312c306dac60db12a498bc233fdef626b` |
