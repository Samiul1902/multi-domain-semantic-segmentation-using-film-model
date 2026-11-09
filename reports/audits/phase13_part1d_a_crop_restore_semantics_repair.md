# PHASE-13 PART-1D-A-R1 — SQUARE / PADDING CROP-RESTORE SEMANTICS REPAIR

- classification: **`MATERIAL_PRE_INFERENCE_IMPLEMENTATION_REPAIR`**
- phase: PHASE_13_PART_1D_A_R1
- scope: **STATIC IMPLEMENTATION ONLY — no model inference**

## Why this is material

The pre-R1 Part-1D-A regional crop/restore helpers did **not** reproduce the frozen
Phase-12 *square crop + zero-padding* semantics. Regional probability maps are composed
into the fused field, so a wrong map-back would have silently corrupted the primary
`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` variant **before any inference was ever run**.

## Pre-R1 defects

| id | function | defect | required by protocol |
|---|---|---|---|
| **D1** | `restore_probability_to_native` | resized 512 **directly to the CLIPPED rectangle** | 512 → **full square** → strip `pad_*` → place at clip coords (Phase-12 `restore_float`) |
| **D2** | `crop_native_gray` | cropped valid region, resized straight to 512, **no square padding** | valid → zero-pad to **full square** → 512 BILINEAR → [0,1] (Phase-12 `crop_tensor`) |
| **D3** | `parse_proposal_geometry` | reduced each record to **clip coords only** | preserve the **complete** record (`y1/y2/x1/x2`, `clip_*`, `pad_*`, `crop_side`, `effective_magnification`, `margin`) |
| **D4** | *(absent)* | no geometry validation | **fail loudly** on malformed geometry |

## Repairs applied

| id | function | change |
|---|---|---|
| **R1** | `parse_proposal_geometry` | preserves **all** square/pad fields; normalises `crop_side_pixels → crop_side` as a lossless alias; int-casts coordinates; **no second margin** |
| **R2** | `assert_geometry_invariants` | fail-loud: `y2-y1 == crop_side`, `x2-x1 == crop_side`, non-negative clip origin, clip within native bounds, vertical + horizontal pad invariants, `margin == 0.20` |
| **R3** | `prepare_regional_crop_512` | valid → zero-pad to **full square side** → 512 BILINEAR → `/255` [0,1] |
| **R4** | `restore_probability_to_native` | 512 → **full square side** (`F.interpolate`, `bilinear`, `align_corners=False`) → strip `pad_*` → valid crop; FLOAT only, **no uint8** |
| **R5** | `restore_probability_to_full_native` | Phase-12 `restore_float` shape: full native array, zeros outside the clip |
| **R6** | `regional_probability_native` | each 512 map restored through the square/padding path before the regional maximum |
| **R7** | `crop_native_gray`, `_float_bilinear_resize` | **deleted** — no direct 512 → clipped-rectangle shortcut remains |

## Materiality measurement

Method: pre-R1 direct-resize restore vs repaired Phase-12-equivalent restore, over **all 494**
frozen Part-1C proposals, with a synthetic random 512×512 probability map.

| group | n | max abs probability diff | verdict |
|---|---|---|---|
| interior geometries | 492 | **0.0** | numerically identical (clip extent == `crop_side`) |
| padded geometries | **2** | **0.877** (min 0.823, mean 0.214) | **materially divergent** |

Padded details:

| sample_id | native | crop_side | clip | pad_bottom | max abs diff |
|---|---|---|---|---|---|
| `b5bbbfc3de80044febb15a558cbe3350` | 2880×2304 | 96 | 2798,1318,2880,1414 | 14 | 0.809189 |
| `717b2beeb7c72cee7955b912183469fa` | 2880×2304 | 97 | 2798,1296,2880,1393 | 15 | 0.876666 |

**Conclusion:** 2 of 494 frozen proposals would have been map-backed with up to **~0.88**
probability error — enough to flip the 0.5-threshold binarisation across many pixels of the
fused field.

## Geometry availability finding

The **complete** square/pad geometry **is** physically available in the frozen Part-1C column
`proposal_crop_geometry`. No re-derivation is needed.

- total proposals **494** · interior **492** · padded **2**
- pad distribution: `(0,14,0,0)` ×1, `(0,15,0,0)` ×1 — **bottom-only padding**
- margin `0.20` for **all 494** · `crop_side` range **33 – 341**
- **all 494 satisfy** the R1 invariants

## Equivalence evidence

Direct numerical comparison against the authoritative read-only Phase-12 helpers
(`crop_tensor`, `restore_float`, `compute_square_crop`) at tolerance `1e-7` — **met**, across
interior, all four edges and both corners.

| item | value |
|---|---|
| tests before R1 | 19 |
| tests after R1 | **31** |
| tests failed | **0** |
| full Phase-13 suite | **117 passed / 0 failed** |

New cases **S–AD**: parser field preservation · interior/edge/corner crop ≡ Phase-12 ·
interior/edge/corner restore ≡ Phase-12 · padded square dims == `crop_side` · valid extent ==
clipped extent · support excludes padding · no direct 512 → clipped shortcut · all 494 real
frozen geometries valid.

## Provenance limitation (disclosed)

**`PRE_R1_DIGEST_NOT_RECOVERABLE`** — for both the module and the test file. Both are
**untracked in git** (never committed), no artifact recorded their pre-R1 SHA-256, and no source
backup or pre-R1 bytecode was retained. **No pre-R1 digest is fabricated.**

Post-R1 SHA-256:

- module `scripts/inference/phase13_part1d_predicted_region_inference.py` → `8cd7e39814a049a025f706c57ccea0b535a230908a177690d6289318234c6284`
- tests `tests/test_phase13_part1d_a_static.py` → `66df4bba0709fb1feb2c698f531a2e507f28ece1164e634aa9315a9a62e646c1`

## Bindings unchanged

`part1c_case_proposals d25c44ec…` · `part1c_proposals 8c3151a3…` · `part1c_component 2a3623fe…`

Frozen proposals **not mutated** · checkpoints **not mutated** · Phase-12 artifacts **not mutated**.

## Counters

training 0 · optimizer 0 · model constructions 0 · CUDA requests 0 · segmentation forwards 0 ·
localizer forwards 0 · proposal generation 0 · regional crop inference 0 · TEST reads 0 ·
checkpoint writes 0 · cache writes 0

**status: `MATERIAL_PRE_INFERENCE_IMPLEMENTATION_REPAIR_COMPLETE`**
