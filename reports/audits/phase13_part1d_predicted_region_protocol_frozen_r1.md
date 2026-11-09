# PHASE-13 PART-1D — PREDICTED-REGION SEGMENTATION PROTOCOL (FROZEN R1)

- status: **`SUPERVISOR_FROZEN_PART1D_R1_READY_FOR_INFERENCE`**
- revision: **R1**
- primary variant: **PREDICTED_REGION_FLOAT_GLOBAL_RETAINED**
- comparison: GLOBAL_NATIVE vs ORACLE_FLOAT_GLOBAL_RETAINED vs PREDICTED_REGION_FLOAT_GLOBAL_RETAINED
- reference model: **NONE** | winner: **NONE** | ranking: **NONE**
- supersedes: `phase13_part1d_predicted_region_protocol_frozen.json` (`8a7a163b…`) — base preserved, not rewritten

> **R1 is an implementation-fidelity amendment only.** No protocol semantics, scientific question,
> population, frozen proposals, fusion rule, retention formula or gate boundary changed.

## R1 amendment

| item | value |
|---|---|
| classification | **`MATERIAL_PRE_INFERENCE_IMPLEMENTATION_REPAIR`** |
| defect | pre-R1 helpers resized 512 **directly to the clipped rectangle** and cropped **without** square zero-padding |
| repaired helpers | `parse_proposal_geometry`, `assert_geometry_invariants`, `prepare_regional_crop_512`, `restore_probability_to_native`, `restore_probability_to_full_native`, `regional_probability_native` |
| removed helpers | `crop_native_gray`, `_float_bilinear_resize` |
| equivalence reference | `phase12_oracle_inference.py` → `crop_tensor`, `restore_float`, `compute_square_crop` |
| equivalence tolerance | max abs `1e-7` — **met** |
| protocol semantics changed | **NO** |

### Materiality

| group | n | max abs probability error |
|---|---|---|
| interior | 492 | **0.0** (numerically identical) |
| padded | **2** | **0.877** (bottom-padded, `pad_bottom` 14 and 15) |

## Crop / restore contract (frozen)

```
input crop : valid native region -> zero-pad to FULL square side -> 512 BILINEAR -> [0,1]
restore    : 512 -> FULL square side (bilinear, align_corners=False)
             -> strip pad_*  ->  place at clip coords
```

- `direct_512_to_clipped_rectangle`: **FORBIDDEN**
- `crop_without_square_padding`: **FORBIDDEN**
- uint8 quantisation / legacy PIL restore: **FORBIDDEN**
- zero-padding value: `0`
- pad strip rule: `prob_square[pad_top : crop_side-pad_bottom, pad_left : crop_side-pad_right]`

## Geometry contract

- source column: `proposal_crop_geometry`
- complete geometry physically available: **YES** — no re-derivation needed
- total proposals **494** | interior **492** | padded **2**
- pad distribution: `(0,14,0,0)` ×1, `(0,15,0,0)` ×1 — bottom-only
- margin `0.20` for all 494 | `crop_side` range **33 – 341**
- invariants enforced: **YES** | all 494 valid: **YES** | second margin: **NO**

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
- global reinference required in Part 1D-B: **YES** · global passes required: **4**
- Phase-12 global reproduction tolerance (max abs Dice): `0.0001`

## Retention

- label: `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`
- formula: `(D_pred - D_global) / (D_oracle - D_global)`
- valid only if `delta_oracle > 0` · clipped: **NO** · negative / >1 preserved: **YES**
- new gate threshold: **NO**

## Table contracts

case-model rows **412** (103×4) · component-model rows **608** (152×4) · model summary rows **4**

## Static preflight

| item | value |
|---|---|
| module | `scripts/inference/phase13_part1d_predicted_region_inference.py` |
| module SHA-256 | `8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284` |
| tests | `tests/test_phase13_part1d_a_static.py` |
| tests SHA-256 | `66df4bba0709fb1feb2c698f531a2e507f28ece1164e634aa9315a9a62e646c1` |
| supervisor cases | **A – AD** |
| tests passed | **31** | failed: **0** |
| tests before R1 | 19 |
| full Phase-13 suite | **117 passed / 0 failed** |
| model construction / CUDA / inference | **NOT PERFORMED** |
| pre-R1 digest recoverable | **NO** (`PRE_R1_DIGEST_NOT_RECOVERABLE`; not fabricated) |

## Four frozen segmentation checkpoints

| model | experiment | SHA-256 |
|---|---|---|
| unet | `phase9_kub_unet_baseline_seed42_512_clean_v3` | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` |
| attention_unet | `phase10_kub_attention_unet_seed42_512_clean_v3` | `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3` |
| unetpp | `phase10_kub_unetpp_seed42_512_clean_v3` | `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269` |
| deeplabv3plus | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad` |

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
| part1d_a_protocol_frozen (json) | `8a7a163b061607dbc3187b0588b3f354e2ee8dd18ea3f34930153d594e75bf78` |
| part1d_a_protocol_frozen (md) | `9e54fb41cd390a79209951cbad120b201670ba9aa9ac989a6f0c4f55a9e2322e` |
| part1d_a_protocol_reporting_erratum | `54f5240b09ca62a5b6ac109d07bb07f3b5fae6ec811613630f5dadc5a5c839ad` |
| part1d_a_crop_restore_semantics_repair | `77723943eaa5aff26041d2b31d0914ddd75b62e46c57f8ae7f34c2f49ea48451` |

### Phase-12 oracle Dice gains (all positive)

`unet +0.130542` · `attention_unet +0.069790` · `unetpp +0.086164` · `deeplabv3plus +0.190121`

## Immutability confirmed

frozen Part-1C proposals **not mutated** · Phase-12 artifacts **not mutated** · checkpoints
**not mutated** · localizer **not rerun** · GT filtering of proposals **not performed** ·
TEST **not constructed** · gate verdict **not issued**

## Gate boundary

- GO / REVISE_LOCALIZER / NO_GO: **FORBIDDEN in Part 1D**
- `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` = **NOT_DECIDED**
- gate belongs to a separate supervisor-reviewed **Part 1E**
- retrofit criteria after results: **FORBIDDEN**

## Zero-scientific-execution counters

training 0 · optimizer_creations 0 · model_constructions 0 · cuda_requests 0 ·
real_segmentation_forwards 0 · localizer_forwards 0 · proposal_generation 0 ·
regional_crop_inference 0 · test_reads 0 · checkpoint_writes 0 · cache_writes 0

**next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1D_B_INFERENCE_AUTHORIZATION`**
