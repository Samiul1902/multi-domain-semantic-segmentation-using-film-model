# Phase 11 — CLEAN-v3 Failure Protocol (SUPERVISOR FROZEN)

- Recorded: 2026-09-20T19:45:26.487487+00:00 · **before** any current failure inspection
- Authority: supervisor freeze decision accompanying Phase 11 Part 1B authorization

## 1A. Low-Dice stratum

- Method: **bottom decile (Q10) of Dice, per model**, from all 280 clean-v3 KUB VAL cases
- Quantile: `np.quantile(..., 0.10)`, default **linear** interpolation, float64 (historical method)
- Rule: `low_dice_model = dice <= model_specific_clean_v3_q10`; **ties included**
- v2 value `0.5461063385009766` is **provenance only — NOT reused**
- Do **not** force exactly 28 cases if ties produce more

## 1B. Historical replication anchor

- **UNet++** = `HISTORICAL_REPLICATION_ANALYSIS_ANCHOR`
- Explicitly **NOT**: winner · best model · superiority claim · Phase-12 reference decision
- All four models remain in the main clean-v3 analysis

## 1C. Shared failure

- Primary: **ALL_FOUR_LOW** = low in UNet **AND** Attention U-Net **AND** UNet++ **AND** DeepLabV3+
- Each flag uses that model's own clean-v3 bottom-decile cutoff
- `low_model_count` (0..4) also computed descriptively
- Mean/median Dice may be descriptive but are **not** the primary definition

## 1D. Architecture disagreement

- Continuous: `dice_range = max(Dice) − min(Dice)`
- **No** numeric threshold frozen; no binary disagreement flag
- Authorized: deterministic top-4 (dice_range desc, sample_id asc) as a **diagnostic view only**
- `dice_sd` may be reported descriptively

## 1E. HD95 stratum (UNet++ anchor)

- Q90 from **valid-only** cases; `HIGH_HD95_DECILE = valid hd95 >= clean-v3 Q90`
- v2 `83.07246563841615` is provenance only
- Invalid cases flagged explicitly; never silently dropped

## 1F. FP burden

- Recompute clean-v3 **Q90** of UNet++ `fp_eval_components`
- v2 integer `4` not automatically frozen; old ">=5" comment is superseded prose

## 1G. TP / FP / FN pixel extension

- Authorized as **CLEAN_V3_DESCRIPTIVE_EXTENSION**
- Does **not** redefine historical failure strata; no deployment/tuning thresholds

## 1H. Multi-component

- Authorized, **8-connectivity**, classes COMPLETE / PARTIAL / COMPLETE_MISS
- Component space declared explicitly

## 1I. Phase-12 reference model

- **NOT SELECTED** — `SUPERVISOR_DECISION_REQUIRED`

## Status: SUPERVISOR_FROZEN