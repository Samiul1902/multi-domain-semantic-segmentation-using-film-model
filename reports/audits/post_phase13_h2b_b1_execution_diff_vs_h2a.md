# POST-PHASE-13 H2B-B1 — One-Axis Execution Diff vs H2A

- **Status: PASS**
- H2A runner SHA: `fead851788c69a4220de4cbcb0b3761651d60e5c568176206879198667cd60c1`
- H2B runner SHA: `444f0ea7b5f6ce76c3d0955febfc67ebd0c36a80913604384ded054c443f7ddd`
- H2A config SHA: `b4813b42e49b8cbe1e9265fd5b2b6ac9213a609d3216e21cd966d385c1927ae4`
- H2B config SHA: `0ee34404c67e36aa27ef880c59295208f662908af996cf634f6a922875340f12`

Runner changed lines: **217** · config changed lines: **47**

## Allowed differences (only these)

- experiment id / provenance bindings
- loss import
- criterion construction: CenterNetFocalLoss(...) -> SoftTargetFocalBCE(gamma=2.0)
- objective-name reporting / metadata
- loss-block validation (enforces the new objective; does not alter gradient math)

## Runner diff regions

- module docstring (reporting)
- EXPERIMENT_ID (provenance)
- H2B_PROTOCOL_PATH / SHA / required status (provenance binding)
- LOSS_CLASS / LOSS_LABEL (objective identity)
- verify_loss_binding() body (validates the frozen objective)
- loss import (objective)
- criterion construction (objective)
- training-start audit text (reporting)

## Config diff regions

- header comment (reporting)
- experiment_id (provenance)
- part: H2B_B1 (provenance)
- loss block (THE scientific axis)
- checkpoint_selection label + frozen_by (provenance)

## Gradient-update code — all UNCHANGED

| item | state |
|---|---|
| model_construction | UNCHANGED |
| initialization | UNCHANGED |
| forward_pass | UNCHANGED |
| target_generation | UNCHANGED |
| dataset_membership | UNCHANGED |
| sample_preprocessing | UNCHANGED |
| augmentation | UNCHANGED |
| dataloader_construction | UNCHANGED |
| shuffle_semantics | UNCHANGED |
| generator_seed | UNCHANGED |
| batch_size | UNCHANGED |
| amp_autocast_semantics | UNCHANGED |
| scaler_semantics | UNCHANGED |
| zero_grad | UNCHANGED |
| backward | UNCHANGED |
| optimizer_step | UNCHANGED |
| scheduler_step | UNCHANGED |
| gradient_accumulation | UNCHANGED |
| optimizer | UNCHANGED |
| lr | UNCHANGED |
| weight_decay | UNCHANGED |
| scheduler | UNCHANGED |
| checkpoint_selection_rule | UNCHANGED |
| proposal_generation_config | UNCHANGED |

Unexpected gradient-affecting difference: **NONE** · CHECK_REQUIRED: **NO**

## Initialization semantics

| item | value |
|---|---|
| INITIALIZATION | FRESH_FROM_SCRATCH_SEED42 |
| WARM_START | NO |
| PRETRAINED_LOCALIZER_STATE | NONE |
| loads_h2a_epoch83_weights | NO |
| loads_phase13_epoch53_weights | NO |
| fine_tuning_previous_checkpoint | NO |
| partial_state_loading | NO |
| head_only_init_from_trained_model | NO |
