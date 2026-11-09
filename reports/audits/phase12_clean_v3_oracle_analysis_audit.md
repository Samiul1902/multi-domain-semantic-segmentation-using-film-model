# Phase 12 Part 1C — Paired Oracle Mechanism Analysis Audit

- Created: 2026-09-21T01:18:26.771911+00:00
- Primary comparison: **GLOBAL_NATIVE vs ORACLE_FLOAT_GLOBAL_RETAINED**
- Population: 103 FULL_FIELD cases · 152 native components · 4 models

## Part-1B errata

- Erratum A: `DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS` (gate compared Dice/IoU only)
- Erratum B: `COMBINED_LEGACY_RESTORE_SENSITIVITY` (uint8 + engine confound)

## Primary macro Dice (native)

| Model | GLOBAL | PRIMARY | diff | improved / unchanged / worsened |
|---|---|---|---|---|
| UNet | 0.594180 | 0.724722 | +0.130542 | 67/0/36 |
| Attention U-Net | 0.629805 | 0.699595 | +0.069790 | 59/0/44 |
| UNet++ | 0.640516 | 0.726679 | +0.086164 | 62/0/41 |
| DeepLabV3+ | 0.560251 | 0.750372 | +0.190121 | 74/0/29 |

## Component recovery

- recovered: **120** · lost detections: **0**
- empty recovered: 27 · new empty: 0
- ALL_FOUR_LOW mean delta Dice: 0.4857
- cases with 4/4 positive delta Dice: 46 of 103

## Worsening (exhaustive)

- case-model rows with delta_dice < 0: **150**
- max worsening: -0.5866
- of those, object recall improves despite Dice decrease: **4**

## Evidence matrix

- status counts: {'SUPPORTIVE_DESCRIPTIVE_EVIDENCE': 8, 'MIXED_DESCRIPTIVE_EVIDENCE': 5, 'NOT_EVALUABLE': 1}

## Governance

- model loading **0** · inference passes **0** · training **0** · optimizer steps **0**
- source tables modified **0** · TEST reads **0** · statistical testing **false**
- winner **none** · reference model **none**
- final Phase-12 conclusion: **NOT_ISSUED**
- regional integration gate decision: **NOT_YET**

## Status: PASS — READY_FOR_SUPERVISOR_PHASE12_MECHANISM_CONCLUSION