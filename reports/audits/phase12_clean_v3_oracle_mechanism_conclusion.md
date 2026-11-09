# Phase 12 — CLEAN-v3 Oracle Mechanism Conclusion

- Created: 2026-09-21T01:27:43.558400+00:00
- Status: **PHASE12_COMPLETE_PASS**

## Supervisor conclusion

```
PHASE12_ORACLE_MECHANISM_CONCLUSION:
  ORACLE_MECHANISM_VALUE      = SUPPORTED_DESCRIPTIVE_EVIDENCE
  PHASE13_PROGRESSION         = SCIENTIFICALLY_JUSTIFIED
```

> Clean-v3 KUB FULL_FIELD evidence demonstrates exploitable regional-resolution headroom. The GT-derived oracle regional intervention provides sufficiently strong descriptive evidence to justify testing whether a deployable GT-free localization mechanism can retain useful regional benefit.

**This does NOT mean:** regional integration gate = GO; regional mechanism promoted; RA-MedFiLM regional path approved; predicted localization will work; statistical superiority established; one baseline architecture selected.

## Scope

- Population: KUB FULL_FIELD VAL 103 cases / 152 native components
- Models: UNet, Attention U-Net, UNet++, DeepLabV3+ (no reference model)
- Primary variant: **ORACLE_FLOAT_GLOBAL_RETAINED** vs comparator `GLOBAL_NATIVE`

## Supporting evidence

| Model | GLOBAL Dice | PRIMARY Dice | delta |
|---|---|---|---|
| UNet | 0.594180 | 0.724722 | +0.130542 |
| Attention U-Net | 0.629805 | 0.699595 | +0.069790 |
| UNet++ | 0.640516 | 0.726679 | +0.086164 |
| DeepLabV3+ | 0.560251 | 0.750372 | +0.190121 |

- Object recall: {'UNet': [0.7864, 0.9951], 'Attention U-Net': [0.8544, 0.9951], 'UNet++': [0.8398, 0.9951], 'DeepLabV3+': [0.7621, 1.0]}
- Empty recoveries: {'UNet': 8, 'Attention U-Net': 3, 'UNet++': 5, 'DeepLabV3+': 11} (total 27, new 0)
- Component-model recovery events: **120** (120 is pooled over 152 components x 4 models = 608 component-model rows; it is NOT 120 unique components (only 152 unique native GT components exist))
- Lost component-detection events: **0**
- Size-stratified recovery events: {'TINY': 74, 'SMALL': 20, 'MEDIUM': 19, 'LARGE': 7, 'total': 120}
- Cross-architecture: 46/103 cases positive for all four models; 103/103 non-worse object recall

## Counter-evidence / cost (preserved)

- case x model rows: 412 · worsened: **150** · max worsening -0.5866
- mean precision change: {'UNet': -0.0236, 'Attention U-Net': -0.0117, 'UNet++': -0.05, 'DeepLabV3+': -0.0004}
- mean FP pixel burden: increases for all four models
- mean FN pixel burden: decreases strongly for all four models

> TARGET RECOVERY BENEFIT IS ACCOMPANIED BY A REAL FP / PRECISION COST. Phase 12 is not universally beneficial case-by-case.

## Oracle limitations

- Phase 12 uses GT-derived target location: it is an ORACLE UPPER-BOUND / MECHANISM experiment
- It is NOT deployable
- It does NOT prove Phase 13 predicted localization can reproduce the gain
- The crop-only comparator is additionally advantaged by oracle background suppression because predictions outside GT-defined crop support are zeroed
- The primary SR-1 result remains ORACLE_FLOAT_GLOBAL_RETAINED, not ORACLE_FLOAT_CROP_ONLY

## Regional-integration gate state (after Phase 12)

| Dim | Dimension | Status |
|---|---|---|
| A | ORACLE_MECHANISM_VALUE | **SUPPORTED_DESCRIPTIVE_EVIDENCE** |
| B | PRACTICAL_LOCALIZATION_RETENTION | **NOT_EVALUABLE_UNTIL_PHASE13** |
| C | GLOBAL_PRESERVATION_FP_COST | **MIXED_DESCRIPTIVE_EVIDENCE** |
| D | GENERALITY | **SUPPORTED_WITH_HETEROGENEITY** |

- Final gate: **NOT_DECIDED** (decided after Phase 13)
- Regional mechanism promoted: **False**

## Phase 13

- Eligible: **True** · authorized: **False** · started: **False**
- Question: *Can a GT-free region proposal/localization mechanism retain enough of the Phase-12 oracle regional-resolution benefit while controlling FP burden and preserving global segmentation quality? (compare GLOBAL vs ORACLE REGION vs PREDICTED REGION)*

## Governance

- TEST reads **0** · training **0** · optimizer steps **0** · statistics **False**
- Winner **none** · reference model **none**

## Status: PHASE12_COMPLETE_PASS