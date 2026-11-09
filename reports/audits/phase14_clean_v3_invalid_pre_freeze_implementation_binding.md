# PHASE-14 CLEAN-V3 — PRE-EXECUTION IMPLEMENTATION-BINDING INTEGRITY CHECK

- **Status: `INVALID_PRE_FREEZE_IMPLEMENTATION_BINDING`** (additive incident report; supersedes nothing)
- Determination: **CASE B — the frozen manifest was NOT prospectively bound to the executed implementation**
- `PRE_EXECUTION_IMPLEMENTATION_BINDING = FAIL`
- Scientific adjudication performed: **NO** · Training performed by this audit: **NO** · TEST reads: **0**

---

## 1. The determining question, answered

> *Given the sequence `freeze manifest locked` → `training script built` → `training launched`, could the
> frozen manifest have contained the exact trainer SHA before training began?*

**No.** The manifest could not have hashed the trainer, because the trainer file **did not exist** when
the manifest was written. Persisted mtimes are unambiguous and 71 seconds apart:

| # | artifact | mtime (BST) |
|---|---|---|
| 1 | `src/data/regional_dataset.py` (implementation repair, still unbound) | `05:27:46.18` |
| 2 | **`reports/audits/phase14_clean_v3_freeze_manifest.json`** (frozen) | **`05:31:16.10`** |
| 3 | **`scripts/training/train_phase14_refiner.py`** (created **after** the freeze) | **`05:32:27.05`** |
| 4 | `logs/phase14_train.log` | `05:34:32.23` |
| 5 | `checkpoints/.../latest.pt` | `05:46:56.67` |
| 6 | `checkpoints/.../best.pt` | `05:46:56.78` |

`trainer_mtime − manifest_mtime = +71 s`. Independently, the manifest contains **no trainer-SHA key at
all** — `protocol_bindings` has 17 keys and none of them names the training script:

```
phase14_protocol_path · phase14_protocol_sha · phase14_protocol_md_sha · authorization_source
parent_chain_closure_sha · parent_h2c_adjudication_sha · h2c_protocol_sha
phase13b_clean_v3_best_pt_sha · phase13b_clean_v3_latest_pt_sha
global_baseline_unetpp_clean_v3_sha · train_manifest_sha · val_manifest_sha
view_type_inventory_sha · regional_dataset_py_sha · regional_evaluator_py_sha
unet_model_py_sha · segmentation_loss_py_sha
```

## 2. Unbound implementation closure

The executed trainer imports, directly or transitively, **10 implementation files that the frozen
manifest never bound**:

| file | SHA-256 | how reached |
|---|---|---|
| `scripts/training/train_phase14_refiner.py` | `d768422f77abae415be8bd712ff67bef4e16605f053287db04e1840c9f7f0aa8` | the trainer itself |
| `src/utils/device.py` | `9adabfbd145a5952275aa25b0ec99aab8a5114bb41aa443ecde52ce19a8448b6` | direct import |
| `src/utils/config.py` | `577deb1db96c8c4ed12e4c41a959f0c6fee8e41af3836dc998a18c928c7f28dd` | direct import |
| `src/inference/predicted_roi.py` | `bd9f8be84595f49ff1e25e6052b548488fb6ae6a48aa7adbc78b880fb8f2d4e7` | via `regional_dataset` |
| `src/data/kub_dataset.py` | `937e04ed7af3b0399fa5e34cd529f04ebc95a7b072f95a9527e1b32dfd36cbb6` | via `predicted_roi` |
| `src/data/transforms.py` | `8a8b636b58843d36810ebf5f3527a8ca1287b93483b962d5cf8e323a92566223` | via `predicted_roi` |
| `src/models/factory.py` | `3377bbe021d7bd13c07350ff5c4927705c2d67f93fa99c388caf2cc79ef4086d` | via `predicted_roi` |
| `src/utils/checkpointing.py` | `08366f72f3141e5d18f008981465f5e9138c0b51336fd65cae7c619456ee1eca` | via `predicted_roi` |
| `src/utils/manifest_guard.py` | `64c5f4d11bbb443c7b47aff7ab84b41e2d2496af981d7b1c6877758cf3461bea` | via `predicted_roi` |
| `src/utils/test_lock.py` | `7cff4732b1f643738c410d672372684486d79e475eae18da5fee7ae10d2d22f3` | via `predicted_roi` |

Bound **and** verified to match: `src/data/regional_dataset.py` (`4e495350…`),
`src/models/unet.py` (`62edc8fb…`), `src/losses/segmentation.py` (`2af539bd…`),
`manifests/phase4_v3/train.csv` (`28702fc3…`), `manifests/phase4_v3/val.csv` (`082c80b2…`),
`reports/tables/kub_view_type_inventory.csv` (`e9fa31fd…`).

### Path-resolution ambiguity (recorded, not repaired)

`regional_evaluator_py_sha` is declared as `ea09b9efc12b832ad1a7f6a3746fc30756193555ae4c5bfe2929a54b395773f2`.
That SHA **does** exist on disk — but at `src/inference/regional_evaluator.py`, **not** at the
`scripts/evaluation/phase14_regional_evaluator.py` path implied by the key name. SHA match: **YES**.
Path match: **NO**. Classified `PATH_RESOLUTION_AMBIGUITY__SHA_MATCHES`.

## 3. Execution reality check (transparent premise assessment)

> **The premise could not be confirmed.** A Phase-14 clean-v3 training process **was not running** at
> audit time, and the log contains **no epoch evidence**.

| probe | result |
|---|---|
| `python.exe` processes | 3 (`30440` 4.5 MB · `10596` 15.7 MB · `31196` 21.9 MB RSS) — **none** is a CUDA training job |
| GPU memory via `torch.cuda.mem_get_info` | **1.10 GB / 8.59 GB used** — inconsistent with an active training job |
| `nvidia-smi` | `Failed to initialize NVML` (host driver query unavailable; `torch.cuda` is functional) |
| `logs/phase14_train.log` | **4 lines / 517 bytes** — only two `FutureWarning`s (lines 122 and 61 of the trainer). No `Device:` line, no `Train items:` line, **no `Epoch ###` line** |

**However — training logic did execute.** Both checkpoints exist and were written at `05:46:56`:

| checkpoint | SHA-256 | epoch | `best_val_crop_dice` |
|---|---|---|---|
| `.../latest.pt` | `82d80ad4bde7f7a5533434bd9f6f58afa8ed69093d7eb33ff6a4ba1ed9957993` | **1** | 0.8206131113202948 |
| `.../best.pt` | `824a43a3d8744cef53d84284dd8d0fa412d9ded3c6fcabeccf677aea175903f0` | **1** | 0.8206131113202948 |

Embedded `configuration` matches the frozen protocol exactly. `scheduler_state.last_epoch = 1`,
`grad_scaler.growth_tracker = 628`. `experiments/.../` is **empty** — no `history.csv`, no `closure.json`.

**Reconstruction:** a process executed the trainer, completed **epoch 1**, wrote both checkpoints, then
terminated before producing epoch 2. It was already gone by the time this audit ran.

## 4. Scientific parameter binding check

The frozen protocol and the executed trainer were compared axis-by-axis. **No undisclosed scientific
parameter change was found**: model `UNet(1,1,32)`, loss `BCEDiceLoss(0.5,0.5,1e-6)`, optimizer
`AdamW(lr=1e-4, wd=1e-4)`, scheduler `CosineAnnealingLR(T_max=100)`, batch 8, seed 42, max_epochs 100,
patience 15, crop 256, AMP true — **all match**.

One **documented textual ambiguity** is recorded, not repaired: the manifest's `frozen_axes` states
*"ROI margin (0.25 for oracle, 0.20 for predicted)"* while `training_config.roi_margin_rule = 0.25`;
the executed trainer uses `margin=0.20` for both TRAIN and VAL. Repairing this requires a protocol
decision and is therefore left to the supervisor.

## 5. Actions taken

| action | result |
|---|---|
| stop the running training process | **N/A — no active process existed to stop** |
| preserve logs for audit | **YES** — `logs/phase14_train.log` left in place, unmodified |
| resume from the invalid checkpoint | **NO** — not attempted, not used as a resume source |
| delete the invalid checkpoints | **NO** — preserved in place for audit |
| change any scientific parameter | **NO** |
| create a new prospective freeze manifest | **YES** — `reports/audits/phase14_clean_v3_freeze_manifest.json` |
| restart from epoch 0 | **REQUIRED** — pending supervisor review of the bound manifest |

## 6. Counters

| counter | value |
|---|---|
| training performed by this audit | **0** |
| CUDA requests by this audit | **1** (`mem_get_info` / `get_device_name`, GPU-state verification only) |
| model constructed / forwards / backwards | **0 / 0 / 0** |
| TEST reads · external TEST reads | **0 · 0** |
| proposal generation | **0** |

next_action: `SUPERVISOR_REVIEW_OF_BOUND_MANIFEST_THEN_RESTART_PHASE14_CLEAN_V3_FROM_EPOCH_0`
