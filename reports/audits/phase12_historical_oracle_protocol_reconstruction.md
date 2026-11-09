# Phase 12 — Historical Oracle-Protocol Reconstruction

- Created: 2026-09-21T00:02:00.193786+00:00
- Historical Phase 12 found: **YES**

## Model / split scope

- Model: **UNet++ only** (`phase10_kub_unetpp_seed42_512`)
- Manifest: **phase4_v2** · split VAL_ONLY · FOV FULL_FIELD
- Population: **106 images / 156 components** (v2)

## Oracle geometry (executing source: `src/analysis/oracle_roi.py`)

- Oracle unit: **PER_COMPONENT_BBOX (one square crop per native GT component)**
- Connectivity: **8** · bbox space: **ORIGINAL_NATIVE**
- Margin: **round(margin * bbox_dim) per axis** · margins [0.1, 0.25, 0.5] · primary **0.25**
- Shape: **SQUARE (side = max(expanded_h, expanded_w), centred)** · resolution **512 x 512**
- Boundary: clip to image + zero-pad to side · image interp BILINEAR
- Mask interpolation: N/A (native GT evaluation; mask never resized in oracle path)

## Mapping / fusion

- Map-back: restore prob to (side,side) bilinear, strip pad, place at clip coords into zero array
- Fusion: **pixelwise MAX of restored component probabilities, threshold AFTER fusion**
- Global outside crop: **NOT retained (zeros)**
- Threshold: 0.5

## Multi-component

- one crop per native component; predictions fused across crops

## Metrics / gate

- Metrics: macro/micro dice/iou/precision/recall, hd95 + validity, empty prediction rate, size-stratified object recall
- Object recall: fraction of native GT components with >=1 overlapping predicted pixel
- Historical taxonomy: **kub_size_v1**
- Numeric gate threshold frozen: **False** · Phase-13 gate: **YES**

## Phase-12 → Phase-13 rationale

> Meaningful FULL_FIELD Dice and TINY-component recovery demonstrates exploitable localization/resolution headroom; no claim that predicted ROI will reproduce the Oracle gain.

## Ambiguities / conflicts recorded

- **AE prob restore uint8 quantisation** (AMBIGUOUS): restore_crop_probability casts prob to uint8 before bilinear resize — clean-v3 should restore in float; flagged for supervisor
- **AG README prose conflict** (CONFLICT): README claims "+16.2% Dice and 100% tiny recall"; audit gives +12.30 pp and 0.986301 — audit (rank 2) is authoritative over README prose (rank 4)
- **V global prediction not retained outside crop** (VERIFIED_BUT_CONSEQUENTIAL): oracle mask is crop-only; outside-crop is zero — clean-v3 should report both crop-only and global-retained variants; supervisor decision

## Historical numerical results (PROVENANCE ONLY)

- global macro Dice `0.6527764131996552`
- oracle25 macro Dice `0.7757361537396281`
- paired delta mean `0.12295974053997309`
- tiny recall global `0.7808219178082192` → oracle25 `0.9863013698630136`

**HISTORICAL_v2_PROVENANCE_ONLY — never clean-v3 evidence.**

## Status: RECONSTRUCTED