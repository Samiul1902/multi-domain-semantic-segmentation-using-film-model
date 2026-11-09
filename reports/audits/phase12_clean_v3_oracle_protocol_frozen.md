# Phase 12 — CLEAN-v3 Oracle Protocol (SUPERVISOR FROZEN)

- Recorded: 2026-09-21T00:33:02.161503+00:00 · **before** any clean-v3 oracle inference
- README restoration: **git checkout HEAD -- <path>; proven by empty git diff**

## Model scope

- All four: UNet · Attention U-Net · UNet++ · DeepLabV3+ — **no reference architecture**
- UNet++ = `HISTORICAL_v2_PROVENANCE_ONLY` (not winner / best / reference / RA-MedFiLM pick)

## Oracle geometry

- Population: KUB FULL_FIELD VAL — expected **103 cases / 152 native components**
- Unit: **PER_COMPONENT_BBOX** · connectivity **8** · bbox space **ORIGINAL_NATIVE**
- Margin: `round(0.25 * bbox_dim)` · primary **0.25** (0.10/0.50 NOT run; no tuning)
- Shape: SQUARE `side = max(expanded_h, expanded_w)` centred · clip + zero-pad
- Resolution 512 · image BILINEAR · **no resized GT crop used for evaluation**

## Map-back

- Primary: **FLOAT_BILINEAR** (no quantisation) — approved material correction

## Variants

- Primary: **ORACLE_FLOAT_GLOBAL_RETAINED** — `P(x)=R(x) if U(x) else G(x)` (regional replacement inside U; threshold 0.5 after)
- Secondary: **ORACLE_FLOAT_CROP_ONLY** (historical geometry comparator)
- Sensitivity: **ORACLE_LEGACY_UINT8_CROP_ONLY** (reuses the SAME crop inference)

## Gates

- Global EVALUATION_512 reproduction gate: max abs Dice diff **<= 1e-4** required before oracle inference
- Paired comparison in **native space** (`PHASE12_NATIVE_SPACE_GLOBAL_BASELINE`)

## Gate framework (frozen)

- Dimensions: ORACLE_MECHANISM_VALUE · PRACTICAL_LOCALIZATION_RETENTION · GLOBAL_PRESERVATION_FP_COST · GENERALITY
- **No scalar automatic GO/NO-GO threshold**; final gate is supervisor-reviewed

## Status: SUPERVISOR_FROZEN