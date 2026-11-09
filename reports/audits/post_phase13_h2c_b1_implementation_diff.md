# POST-PHASE13 H2C-B1 — Implementation Diff vs H2A

- **Status: PASS**
- H2A runner SHA: `fead851788c69a4220de4cbcb0b3761651d60e5c568176206879198667cd60c1`
- H2C runner SHA: `666aabcb58572f6c0892302cb6ff1617b3b19f642dc37a688c84943cc1c66e70`
- H2A config SHA: `b4813b42e49b8cbe1e9265fd5b2b6ac9213a609d3216e21cd966d385c1927ae4`
- H2C config SHA: `b96223eecade2938a9ca9733ddcfba1bbd2f7cd34155ab4d48a1fba51f09bc33`

Runner changed lines: **128** · config changed lines: **30**

## The ONLY scientific change

`CHANGE_H2C_001` — `LOCALIZER_PREDICTION_HEAD_ARCHITECTURE`

- H2A head: `Conv2d(16 -> 1, kernel_size=1)`
- H2C head: `Conv2d(16 -> 16, kernel_size=3, padding=1) + ReLU(inplace=False) + Conv2d(16 -> 1, kernel_size=1)`
- head initialization changed vs H2A: **YES_PART_OF_SAME_FROZEN_HEAD_AXIS**
- post-freeze H2C initialization change: **NO**

## Mechanical unchanged-machinery probes

| probe | H2A count | H2C count | unchanged |
|---|---|---|---|
| loss_construction | 3 | 3 | **True** |
| loss_alpha_2 | 1 | 1 | **True** |
| optimizer | 1 | 1 | **True** |
| scheduler | 1 | 1 | **True** |
| amp_autocast | 2 | 2 | **True** |
| grad_scaler | 1 | 1 | **True** |
| zero_grad | 2 | 2 | **True** |
| backward | 1 | 1 | **True** |
| optimizer_step | 1 | 1 | **True** |
| scheduler_step | 1 | 1 | **True** |
| dataloader_shuffle_true | 1 | 1 | **True** |
| dataloader_shuffle_false | 1 | 1 | **True** |
| train_generator | 1 | 1 | **True** |
| val_generator | 1 | 1 | **True** |
| worker_init_fn | 2 | 2 | **True** |
| batch_size_from_config | 0 | 0 | **True** |
| selection_call | 1 | 1 | **True** |
| proposal_threshold | 1 | 1 | **True** |
| proposal_margin | 1 | 1 | **True** |
| proposal_top_k | 1 | 1 | **True** |
| proposal_nms | 1 | 1 | **True** |
| patience | 1 | 1 | **True** |

All probes unchanged: **True**

## Unchanged machinery

| item | state |
|---|---|
| loss | UNCHANGED (H2A CenterNetFocalLoss retained; H2B soft-target NOT used) |
| target_construction | UNCHANGED |
| optimizer | UNCHANGED |
| learning_rate | UNCHANGED |
| weight_decay | UNCHANGED |
| scheduler | UNCHANGED |
| amp | UNCHANGED |
| batch | UNCHANGED |
| backward | UNCHANGED |
| zero_grad | UNCHANGED |
| scaler | UNCHANGED |
| optimizer_step | UNCHANGED |
| scheduler_step | UNCHANGED |
| dataset_creation | UNCHANGED |
| population | UNCHANGED |
| preprocessing | UNCHANGED |
| augmentation | UNCHANGED |
| dataloader | UNCHANGED |
| shuffle_generator | UNCHANGED |
| workers | UNCHANGED |
| seed | UNCHANGED |
| checkpoint_selection | UNCHANGED |
| early_stopping | UNCHANGED |
| proposal_extraction | UNCHANGED |
| proposal_threshold | UNCHANGED |
| margin | UNCHANGED |
| top_k | UNCHANGED |
| nms | UNCHANGED |
| backbone | UNCHANGED (src/models/kub_localizer.py not modified) |

`src/models/kub_localizer.py` modified by H2C: **NO**

Unexpected material difference: **NONE** · CHECK_REQUIRED: **NO**
