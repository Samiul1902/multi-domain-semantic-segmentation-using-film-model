# Phase 11 — Historical Failure-Protocol Reconstruction

- Created: 2026-09-20T19:26:34.554019+00:00
- Historical Phase 11 found: **YES**

## Model / split scope

- Primary: **UNet++** (phase10_kub_unetpp_seed42_512)
- Comparator: **DeepLabV3+**
- Split: VAL_ONLY (283 KUB VAL cases, manifest phase4_v2) · threshold 0.5

## Units

- case-level (per_image)
- component/object-level (per_component)
- patient-level

## Numeric thresholds (descriptive strata, NOT tuning thresholds)

| Stratum | Cutoff | Comparison | n |
|---|---|---|---|
| low_dice_decile | 0.5461063385009766 | dice <= cutoff | 29 |
| high_hd95_decile | 83.07246563841615 | valid hd95 >= cutoff | 28 |
| high_fp_decile | 4.0 | fp evaluation components >= cutoff | 39 |

## Contracts

- Object: connectivity **8**, minimum overlap **1 px** (`src/metrics/object_metrics.py`)
- Size taxonomy: **kub_size_v1 (HISTORICAL; clean-v3 must use kub_size_clean_v3_v1)**
- Regime: FOV — ROI_CROP 177 / FULL_FIELD 106
- Category: Bladder 145 / Kidney 114 / Ureteric 24 (metadata)
- Multi-component: YES (n=50)
- Boundary: HD95 with `hd95_valid` (275 valid / 8 invalid)

## Hard-case selection (16 cases)

- 4 strata x 4 cases: empty prediction; missed GT component; severe FP (>=4); low-Dice decile
- Tie-break: sort by `sample_id` (low-dice stratum: ascending dice); later strata exclude earlier picks
- **Prediction-dependent by design** (failure cohort), unlike the Phase-10 qualitative gallery

## Phase-11 → Phase-12 rationale

> Observed FULL_FIELD, small-object, and multi-component failures motivate testing whether increased effective local resolution can recover missed targets; no claim that ROI will solve them.

## Discrepancies recorded

- **fp stratum** (minor): code uses fp_eval_components >= 4 but inline comment says ">=5" — recorded; use code value
- **low-dice label** (minor): cohort label says "Low Dice Decile (<0.30)" but actual cutoff is 0.5461 — recorded; cutoff is bottom decile, not 0.30
- **size taxonomy** (material-for-clean-v3): historical used kub_size_v1; clean-v3 requires kub_size_clean_v3_v1 — clean-v3 uses the clean taxonomy; historical retained for provenance
- **primary model** (governance): historical was UNet++-primary; clean-v3 must not adopt a reference from single-seed VAL — recorded; reference-model decision deferred to supervisor

## Status: RECONSTRUCTED