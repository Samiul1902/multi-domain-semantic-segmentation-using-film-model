# Phase 09 CLEAN-v3 — Training Start Audit

**Experiment ID:** `phase9_kub_unet_baseline_seed42_512_clean_v3`  
**Start (UTC):** 2026-09-20T06:53:00.854097+00:00  
**Status:** `STARTED`

| Field | Value |
|---|---|
| Config | `configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml` |
| Config SHA | `8a45458c7c5e34062214a741550a84ff9ab56e4ad9ceef81cbcf263052b5172a` |
| Manifest version | `phase4_v3` |
| Taxonomy ID | `kub_size_clean_v3_v1` |
| Taxonomy artifact SHA | `89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6` |
| Git commit | `fb160ac442084f8a11b647f5a8411abe700f9835` |
| Seed | 42 |
| Run lock PID | 28392 |
| Stale lock recovered | False |

## Environment

| Field | Value |
|---|---|
| cuda_available | True |
| cuda_device_count | 1 |
| cuda_device | NVIDIA GeForce RTX 3060 Ti |
| pytorch_version | 2.6.0+cu124 |
| cuda_runtime_version | 12.4 |
| cudnn_version | 90100 |
| cuda_capability | [8, 6] |
| canonical_requires_cuda | True |

## Pre-run gates

| Gate | Result |
|---|---|
| manifest_guard | PASS |
| kub_train_1978 | PASS |
| kub_val_280 | PASS |
| patient_overlap_zero | PASS |
| test_construction_blocked | PASS |
| taxonomy_artifact_sha | PASS |
| cuda_available | PASS |
| device_require_cuda | PASS |
| config_validation | PASS |
| test_lock_verified | PASS |

## Authorized differences vs historical v2

- manifest_version phase4_v2 -> phase4_v3
- taxonomy_id None -> kub_size_clean_v3_v1
- experiment_id new clean-v3 logical run
- fail-loud CUDA device contract
- centralized mask > 0 target helper
- additional provenance/checkpoint/resume metadata
- single-writer protection

- TEST content reads: 0
- Scientific parameter changes: 0
