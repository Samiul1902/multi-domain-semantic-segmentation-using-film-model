# POST-PHASE14 H3 SINGLE-AXIS PRIORITY DIAGNOSTIC — REPORT

## 1. Objective
Determine whether the FIRST H3 scientific axis can be uniquely selected between
**A_PROPOSAL_SUPPLY_RECALL_LIMITATION** and **C_PROPOSAL_CONTAMINATION_LIMITATION**
without changing both at once. Decisive question: if missing proposal supply is repaired while the
existing contamination burden is left completely untouched, does the frozen system recover the
Tiny-recall signal required by Phase 14? (Complementary C-only experiment already established:
removing contamination repairs Dice but leaves Tiny Recall at 79.17%.)

## 2. Method
Frozen clean-v3 FULL_FIELD VAL population: **103 images, 152 components** (TINY 72 / SMALL 28 /
MEDIUM 36 / LARGE 16; hard-tiny denom 15; global-empty denom 5). Reused the EXACT frozen Stage-4D
pipeline (Phase-10 GLOBAL UNet++, Phase-14 refiner epoch 56, Phase-13B localizer epoch 53; proposal
contract threshold=0.10 / margin=0.20 / top_k=5 / nms_iou=0.30; 256 refiner crops; MAX/DIRECT fusion;
segmentation threshold 0.50). TEST = CLOSED; external = CLOSED.

Conditions:
- GLOBAL: Phase-10 UNet++ only.
- PREDICTED: frozen Stage-4D predicted proposals (supply + contamination as-is).
- A_ONLY `GT_ASSISTED_MISSING_PROPOSAL_SUPPLY_COMPLETION__NON_DEPLOYABLE`: for every GT component
  with ZERO matched predicted proposal, add exactly ONE GT-derived Oracle-geometry ROI (margin 0.20);
  **KEEP every original predicted proposal including all background FPs**; same refiner/preproc/fusion.
- C_ONLY `GT_ASSISTED_FALSE_POSITIVE_DECOMPOSITION__NON_DEPLOYABLE`: remove confirmed-background
  proposals; supply unchanged (metrics reused from the existing root-cause diagnostic).
- A_PLUS_C `GT_ASSISTED_SUPPLY_PLUS_FP_REMOVAL__UPPER_BOUND_ONLY`: diagnostic upper bound only.
- ORACLE_REGIONAL: every GT component gets a GT-derived ROI (Phase-14 reference; Do=0.8024).

"No training, no tuning, no search" enforced: all counters = 0. R_A=(Tp_A-Tg)/G, Tg=0.7916666666666666,
G=0.20833333333333337, Dice gate = Dg-0.02 = 0.6159172411726776.

## 3. Condition metrics
| Condition | Dice | TINY Rec | SMALL Rec | MED Rec | LARGE Rec | Overall Rec | FP/img | hard-tiny rec | glob-empty rec |
|---|---|---|---|---|---|---|---|---|---|
| GLOBAL | 0.6359 | 0.7917 | 0.8214 | 0.8611 | 0.8750 | 0.8224 | 0.485 | 0.000 | 0.000 |
| PREDICTED | 0.4185 | 0.7917 | 0.8929 | 1.0000 | 0.9375 | 0.8750 | 7.777 | 0.000 | 0.200 |
| A_ONLY | 0.4780 | **1.0000** | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 7.806 | **1.000** | **1.000** |
| C_ONLY | 0.6288 | 0.7917 | 0.8929 | 1.0000 | 0.9375 | 0.8750 | 0.689 | 0.000 | 0.200 |
| A_PLUS_C | 0.7372 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.718 | 1.000 | 1.000 |
| ORACLE_REGIONAL | 0.8024 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 0.631 | 1.000 | 1.000 |

Zero-proposal GT components = 79 / 152; zero-proposal TINY = 57 / 72.

## 4. A-only intervention detail
- Injected diagnostic ROIs = **79** (of which **57 TINY**).
- Recall@90 successes among injected = **79 / 79 (100%)**; failures = **0**.
- Dice delta vs frozen PREDICTED = **+0.0595** (Dice rises only slightly because all background FPs are retained).

## 5. Causal quantities (frozen references)
- Tp_PREDICTED (TINY Recall) = 0.7917; Tp_A_only = **1.0000**; Tp_C_only = 0.7917; Tp_A_plus_C = 1.0000.
- **R_A = 1.0000**; **R_C = 0.0000**; **R_AC = 1.0000**.
- A-only lift over PREDICTED = +0.2083 (>= material threshold 0.10); C-only lift = 0.0.

## 6. Priority-rule outcome
Prospectively frozen rule **A_PRIORITY** fired:
- A-only materially increases Tiny Recall over PREDICTED (lift 0.2083 >= 0.10);
- R_A = 1.0000 >= 0.50;
- C-only does NOT materially increase Tiny Recall (R_C = 0).
=> **H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL**; eligible axis = **A_PROPOSAL_SUPPLY_RECALL_LIMITATION**.

## 7. Causal necessity / sufficiency (kept separate)
- **A (supply) is causally NECESSARY** for the regional Tiny-recall signal: supplying one GT-assisted ROI
  per zero-proposal component restores ~all missing-tiny detection (R_A = 1.0, hard-tiny 0/15 -> 15/15,
  global-empty 1/5 -> 5/5). A is **NOT sufficient alone**: it keeps all background FPs, so FP burden
  (7.806/img) and Dice (0.4780) remain at the PREDICTED failure level -> contamination residual.
- **C (contamination) is NOT necessary** for the Tiny-recall failure: removing FP proposals leaves Tiny
  Recall at 0.7917 (R_C = 0). C is **NOT sufficient alone** for the recall signal: the regional
  Tiny-recall contribution stays at zero.

## 8. Residual failure after each isolated intervention
- **After A-only**: contamination residual — FP burden and Dice remain at/near PREDICTED; Dice gate
  (0.6159) NOT reached. Tiny Recall fully restored.
- **After C-only**: supply/recall residual — regional Tiny-Recall contribution remains zero; Tiny Recall
  unchanged (0.7917); hard-tiny 0/15; global-empty 1/5. Dice gate reached (0.6288) but the recall signal
  the regional pipeline is supposed to provide is still absent.
- (A+C upper bound reaches Dice 0.7372 and full recall, still below ORACLE_REGIONAL 0.8024 because the
  73 already-covered components still use predicted-crop refinements rather than GT ROIs.)

## 9. H3 readiness
**H3_DESIGN_ELIGIBLE** with EXACTLY ONE axis: **A_PROPOSAL_SUPPLY_RECALL_LIMITATION**.
Phase 15: NOT_STARTED_AND_NOT_AUTHORIZED. H3 training: NOT_STARTED. Per authorization, this diagnostic
STOPS after naming the axis; no H3 architecture, loss, threshold, top-k, NMS, or training is begun. The
next supervisor task will prospectively design H3 around this single supply axis.
