# PHASE-13 PART-1D-A — PROTOCOL REPORTING ERRATUM

- classification: **`PART1D_A_CHECKPOINT_EXPERIMENT_ID_REPORTING_ERROR_ONLY`**
- phase: PHASE_13_PART_1D_A_R1
- scope: **REPORTING ONLY — no scientific execution**

## Defect

The Part-1D-A frozen protocol **markdown** table *"Four frozen segmentation checkpoints"*
rendered the literal model-name tuple in the `experiment` column on **all four rows**:

```
| model            | experiment                                       | SHA-256 |
| unet             | ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus'] | 7b955ba8… |
| attention_unet   | ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus'] | a49b19d6… |
| unetpp           | ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus'] | ec7eb13f… |
| deeplabv3plus    | ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus'] | f519027b… |
```

Root cause: the markdown renderer iterated the `MODELS` name list for the experiment
column instead of `MODEL_CHECKPOINTS` (the model → experiment-id mapping).

Affected artifact: `reports/audits/phase13_part1d_predicted_region_protocol_frozen.md`
(one table only).

## Not affected

| item | status |
|---|---|
| `phase13_part1d_predicted_region_protocol_frozen.json` | **UNCHANGED** |
| `bindings.segmentation_checkpoints` | **always correct** |
| checkpoint paths | UNCHANGED |
| checkpoint SHA-256 bindings | UNCHANGED |
| protocol semantics / population / proposals / fusion / retention / table contracts / gate boundary | UNCHANGED |
| scientific value / measurement / inference | **NONE affected** |

## Correct experiment ids

| model | experiment id |
|---|---|
| unet | `phase9_kub_unet_baseline_seed42_512_clean_v3` |
| attention_unet | `phase10_kub_attention_unet_seed42_512_clean_v3` |
| unetpp | `phase10_kub_unetpp_seed42_512_clean_v3` |
| deeplabv3plus | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` |

Verified against the JSON binding path and against disk: `checkpoints/<experiment_id>/best.pt`
exists for **all four** models.

## Repair

- action: **markdown experiment column corrected in place, with a visible erratum note**
- erroneous rendering hidden: **NO** (quoted verbatim above and in the JSON)
- JSON modified: **NO**
- pre-repair md SHA-256: `13d9408d5eccb042cf7fc95ac4c8b540c2460ab8ccb3a951baf88a753cb51e89`
- post-repair md SHA-256: `9e54fb41cd390a79209951cbad120b201670ba9aa9ac989a6f0c4f55a9e2322e`
- JSON SHA-256 (before and after): `8a7a163b061607dbc3187b0588b3f354e2ee8dd18ea3f34930153d594e75bf78`

## Propagation search

Token `['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']` searched across
`reports/ docs/ notebooks/phasewise/ scripts/ src/ tests/ manifests/ configs/`.

**9 raw textual matches, 0 reporting defects.** All matches are either:

- legitimate `MODELS` / `MODEL_ORDER` / `CLEAN_V3_MODELS` list constants in the Phase-10/11/12
  code (the token is *correct* there), or
- intentional verbatim quotations of this defect inside the erratum artifacts.

No other artifact rendered a model list in an experiment-id field.

## Withdrawn claims

**None.** No scientific claim was made from this table.

## Counters

training 0 · optimizer 0 · model constructions 0 · CUDA requests 0 · segmentation forwards 0 ·
localizer forwards 0 · proposal generation 0 · regional crop inference 0 · TEST reads 0 ·
checkpoint writes 0 · cache writes 0

**status: `PART1D_A_PROTOCOL_REPORTING_ERRATUM_COMPLETE`**
