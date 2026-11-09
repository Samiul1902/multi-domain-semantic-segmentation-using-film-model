# PHASE-13 PART-1D-A — PREDICTED-REGION SEGMENTATION PROTOCOL FREEZE

- status: **SUPERVISOR_FROZEN_PART1D_READY_FOR_INFERENCE**
- primary variant: **PREDICTED_REGION_FLOAT_GLOBAL_RETAINED**
- comparison: GLOBAL_NATIVE vs ORACLE_FLOAT_GLOBAL_RETAINED vs PREDICTED_REGION_FLOAT_GLOBAL_RETAINED
- reference model: **NONE** | winner: **NONE** | ranking: **NONE**

## Population and frozen proposals

| item | value |
|---|---|
| cases | 103 |
| components | 152 |
| strata | TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16 |
| ROI | EXCLUDED |
| TEST | LOCKED |
| total proposals | **494** |
| proposal config | 0.10 / 0.20 / 5 / 0.30 |
| margin already applied | **YES** |
| second margin applied | **NO** |

## Fusion (frozen)

```
P(x) = R(x)   if U_pred(x)
     = G(x)   otherwise
```

- overlap: **MAX among regional crops only**
- `max(G,R)` inside support: **FORBIDDEN**
- threshold: **0.5 AFTER complete native fusion**
- zero-proposal image: `P = G` exactly
- oracle margin: **0.25** (change FORBIDDEN)

## Global native contract

- global cache available: **NO**
- global reinference required in Part 1D-B: **YES**
- global passes required: **4**
- Phase-12 global reproduction tolerance (max abs Dice): 0.0001

> The only populated probability cache (`data_cache/phase13_predicted_roi`) is a
> **HISTORICAL_v2** run with a different checkpoint and 106 images. It is NOT a
> reusable clean-v3 GLOBAL_NATIVE cache. `data_cache/global` is empty.

## Retention

- label: `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`
- formula: `(D_pred - D_global) / (D_oracle - D_global)`
- valid only if: `delta_oracle > 0`
- clipped: **NO**
- negative / >1 preserved: **YES**
- new gate threshold: **NO**

## Table contracts

- case-model rows: **412** (103 x 4)
- component-model rows: **608** (152 x 4)
- model summary rows: **4**

## Bindings

| artifact | SHA-256 |
|---|---|
| part1c_case_proposals | `d25c44ec1361365e261d36458e86e707ad3bcb58cf000763a732605db0f856ed` |
| part1c_proposals | `8c3151a3f1f9a56f0692c6ff2d2171472a777a56e99fa2e474aff8a3478a564a` |
| part1c_component_coverage | `2a3623fecbc1fc5dd5a2c2a12fbd6d5e78fe2e123a9c45431ba53ca14e4e4b87` |
| part1c_size_stratified | `147d3947d53fce5102ad290d8caa5f19ccb3eebcc61f75634fcb261780c792f9` |
| gallery_selection | `1fcbc0ae93e1b63ef3b7c3f045af740e9c353cb7635fd5c98e61d31e177d49d3` |
| phase12_oracle_case_metrics | `080f158fb8b3e3552ac7854c6d9a116e11564bcefa9efdcdbb3511dba090b436` |
| phase12_oracle_component_metrics | `d66933a3c2821d3ab9375eadb5c0540fea145edcf49b648064fe9aa4c460c753` |
| phase12_oracle_geometry | `29326d5b9a3bf71add74d8743750511f146d8c4dfbd1dc5b04a5e1b647c37cc0` |
| phase12_oracle_protocol_frozen | `f5227bdd67ec780ccd4c520a9bf1576601164939d2ff4132680885bc35124a48` |
| phase12_global_reproduction_gate | `7654d5b3eb4d18a62562453ccc3b8d9868b6d2b0ade871716163c59403dc91d8` |
| part1b_final_best_integrity | `6a4c5748ccded2758e6d7c530758d5fb2382de4c71fa7e7cd57e393f4ec6507e` |
| part1c_evaluation_audit | `1c67ee6550f55bace37c31b7d532832cc4f5779bc81faad7c3a9c5d8f7ea0565` |

### Four frozen segmentation checkpoints

> **R1 reporting erratum (reporting-only).** In the original rendering of this
> table the `experiment` column repeated the literal model-name tuple
> `['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']` on every row instead of
> each model's experiment id. The machine-readable
> `bindings.segmentation_checkpoints` block in the JSON was always correct and is
> unchanged. No SHA-256 binding, no checkpoint path, no protocol semantic and no
> scientific value was affected. See
> `reports/audits/phase13_part1d_a_protocol_reporting_erratum.json`.

| model | experiment | SHA-256 |
|---|---|---|
| unet | `phase9_kub_unet_baseline_seed42_512_clean_v3` | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` |
| attention_unet | `phase10_kub_attention_unet_seed42_512_clean_v3` | `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3` |
| unetpp | `phase10_kub_unetpp_seed42_512_clean_v3` | `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269` |
| deeplabv3plus | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad` |

### Phase-12 oracle Dice gains (all positive)

`{"unet": 0.130542, "attention_unet": 0.06979, "unetpp": 0.086164, "deeplabv3plus": 0.190121, "all_positive": true, "note": "computed from the frozen Phase-12 authoritative case table (GLOBAL_NATIVE vs ORACLE_FLOAT_GLOBAL_RETAINED mean Dice)"}`

## Static preflight

- module: `scripts/inference/phase13_part1d_predicted_region_inference.py`
- tests: `tests/test_phase13_part1d_a_static.py`
- tests passed: **19** | failed: **0**
- model construction: **NOT PERFORMED**
- CUDA request: **NOT PERFORMED**
- inference: **NOT PERFORMED**

## Zero-scientific-execution counters

| counter | value |
|---|---|
| training | **0** |
| optimizer_creations | **0** |
| model_constructions | **0** |
| cuda_requests | **0** |
| real_segmentation_forwards | **0** |
| localizer_forwards | **0** |
| proposal_generation | **0** |
| regional_crop_inference | **0** |
| test_reads | **0** |

## Gate boundary

- GO / REVISE_LOCALIZER / NO_GO: **FORBIDDEN in Part 1D**
- `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` = **NOT_DECIDED**
- gate belongs to a separate supervisor-reviewed **Part 1E**
- retrofit criteria after results: **FORBIDDEN**
