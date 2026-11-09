# POST-PHASE13 H2C — RNG-Equivalence + Execution-Provenance Preflight

- **Status: PASS**
- **RNG classification: `RNG_STREAMS_ALREADY_ISOLATED`**
- Execution fix required: **NO** · applied: **NONE (no executable training semantics were changed)**

## Why this matters

H2C adds a kaiming-initialised 3x3 convolution, which consumes RNG. If model initialization shared a stream with data ordering or augmentation, H2C would silently change more than the head architecture despite the unchanged seed 42.

## Stream ownership (physical)

| stream | owner |
|---|---|
| model_initialization_rng | torch global RNG (torch.nn.init.kaiming_normal_) |
| shuffle_rng | dedicated torch.Generator seeded with 42 (per DataLoader) |
| augmentation_rng | Python `random` module (global), seeded once by set_seed |
| worker_rng | seed_worker() from torch.initial_seed(); num_workers=0 -> unused |
| val_ordering_semantics | deterministic sequential (shuffle=False) |
| numpy_rng | seeded by set_seed but NOT consumed by augmentation |

## Answers

| question | answer |
|---|---|
| A_train_shuffle_uses_dedicated_generator | YES (make_generator(seed), line 1410) |
| B_val_ordering_stochastic | NO (shuffle=False; deterministic sequential order) |
| C_augmentation_rng_source | Python `random` (module-level global), NOT torch and NOT numpy |
| D_model_construction_relative_to_seeding | AFTER final training RNG initialization |
| E_extra_kaiming_draws_alter_later_streams | NO — the extra draws advance only the torch GLOBAL RNG, which no downstream stream consumes: shuffling uses dedicated generators, augmentation uses Python `random`, and no torch.rand/randn/normal or Dropout exists on the training path |

## Empirical equivalence

| check | result | hash (H2A) | hash (H2C) |
|---|---|---|---|
| TRAIN order (770 indices) | **True** | `a7005312d5604601…` | `a7005312d5604601…` |
| VAL order | **True** | `f5e37d7233f6091c…` | `f5e37d7233f6091c…` |
| augmentation RNG trace | **True** | `53d3baecbd834547…` | `53d3baecbd834547…` |

Python random state equivalent: **True** · numpy state equivalent: **True** · train generator equivalent: **True** · val generator equivalent: **True**

torch global RNG state equivalent: **False** — EXPECTED to differ: the H2C head performs additional kaiming draws. No downstream stream consumes the torch global RNG, so this difference is inert.

## Terminal zero-weight note

`FROZEN_INITIALIZATION_CONSEQUENCE` — H2C terminal 1x1 weights initialize to zero. On the first backward pass the hidden 3x3 layer may receive zero gradient through the zero terminal weights until the terminal layer has been updated. This is an intentional consequence of the frozen initialization.

## Scientific change register after preflight

| field | value |
|---|---|
| HEAD_ARCHITECTURE_CHANGED | YES |
| HEAD_INITIALIZATION_CHANGED | YES_PART_OF_SAME_FROZEN_HEAD_AXIS |
| LOSS_CHANGED | NO |
| TARGET_CHANGED | NO |
| SIGMA_CHANGED | NO |
| BACKBONE_CHANGED | NO |
| OPTIMIZER_CHANGED | NO |
| SCHEDULER_CHANGED | NO |
| DATA_CHANGED | NO |
| SPLIT_CHANGED | NO |
| AUGMENTATION_DISTRIBUTION_CHANGED | NO |
| TRAIN_ORDER_SEMANTICS_CHANGED | NO |
| CHECKPOINT_SELECTION_CHANGED | NO |
| PROPOSAL_POLICY_CHANGED | NO |
| FUSION_CHANGED | NO |
| SECOND_SCIENTIFIC_AXIS | NONE |

## Zero scientific execution

training epochs **0** · optimizer steps **0** · checkpoint writes **0** · project TRAIN model forwards **0** · project VAL model forwards **0** · TEST reads **0** · external TEST reads **0** · synthetic shape-check forwards **1**

**next_action:** `WAIT_FOR_SUPERVISOR_H2C_B1_EXECUTION_AUTHORIZATION`
