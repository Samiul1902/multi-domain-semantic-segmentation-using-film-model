# Phase 11 — CLEAN-v3 Failure-Analysis Protocol (candidate)

- Created: 2026-09-20T19:26:34.554019+00:00
- Manifest: phase4_v3 · Taxonomy: kub_size_clean_v3_v1

## Four-model scope (no ranking, no winner)

| Model | Best ep | Dice | IoU | Precision | Recall |
|---|---|---|---|---|---|
| UNet | 44 | 0.7406133413314819 | 0.6253822445869446 | 0.7707186937332153 | 0.7839437127113342 |
| Attention U-Net | 54 | 0.7525129853960107 | 0.6349387691368995 | 0.7729140812402236 | 0.7922248481868364 |
| UNet++ | 70 | 0.7641595156062713 | 0.6525442690586191 | 0.7996825971468945 | 0.7912384169561990 |
| DeepLabV3+ | 52 | 0.7509140344161673 | 0.6460492792430865 | 0.7943328495850855 | 0.7822983241135557 |

- **Reference model selected: False** — No reference/primary model chosen. Historical was UNet++-primary; adopting that for clean-v3 would require a supervisor decision (single-seed VAL is insufficient).

## Invariant contracts

- Foreground: `mask > 0` · connectivity **8** · min overlap **1 px**
- Taxonomy: `kub_size_clean_v3_v1` (FULL_FIELD scope; ROI = ROI_NOT_PRIMARY_BINNED)
- Regime: FULL_FIELD 103 / ROI 177 — never pooled unshown
- Category: metadata only (Ureteric n=24, do not overinterpret)
- Threshold 0.5 · KUB VAL 280 cases','
## Carried forward / proposed

**Carried forward (historically verified):** empty_prediction, object miss (8-conn, >=1px), multi-component COMPLETE/PARTIAL/COMPLETE_MISS, HD95 with validity flag, regime stratification, category metadata stratification, bottom-decile METHOD for low-Dice stratum (value to be recomputed, not frozen)

**Proposed extensions (NOT historically defined, not frozen):** per-case TP/FP/FN decomposition (NOT historically defined), under/over-segmentation fraction (NOT historically defined), prediction/GT area ratio (NOT historically defined)

**Candidate scores (awaiting supervisor decision):** shared: mean Dice across the four models, median Dice across models, number of models below the (recomputed) low-Dice stratum; disagreement: max Dice - min Dice, SD of per-model Dice

- New unauthorized thresholds introduced: **0**
- Hard-case selection: **PROCEDURE_FROZEN_NO_CASES_SELECTED**
- Upstream epoch rows: {'UNet': 59, 'Attention U-Net': 69, 'UNet++': 85, 'DeepLabV3+': 67}

## Status: READY_FOR_SUPERVISOR_FREEZE