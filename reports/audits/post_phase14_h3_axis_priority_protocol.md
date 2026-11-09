# POST-PHASE14 H3 SINGLE-AXIS PRIORITY DIAGNOSTIC — PROTOCOL

Status: **FROZEN_AWAITING_EXECUTION**

## Authorization context
- Phase 14 outcome: F_MIXED_BOTTLENECK (primary A = proposal-supply/recall; secondary C = proposal-contamination).
- Phase 15: NOT_STARTED_AND_NOT_AUTHORIZED. H3 training: NOT_STARTED / NOT AUTHORIZED.
- Task type: causal-priority decomposition only. **No H3 training.** Sole purpose: decide whether ONE H3 axis (A vs C) can be uniquely selected prospectively.

## Population (frozen clean-v3 FULL_FIELD VAL)
- 103 images, 152 components: TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16.
- hard-tiny denominator 15; global-empty denominator 5.
- TEST = CLOSED (0 reads). External = CLOSED.

## Frozen artifacts (SHA-bound)
- GLOBAL ckpt phase10 unetpp: ec7eb13f...
- Refiner ckpt phase14 UNet epoch56: 2e09e3a9...
- Localizer ckpt phase13b Centernet-Focal epoch53: 7673c34a...
- Existing root-cause JSON: dd9b5b86...
- Component table: 59605f3b... / Proposal table: 7632a261... / Image table: d4468288...
- Phase-14 governance reconciliation: d4ebe2b4...
- Diagnostic evaluator (this task): 5029c4bf...

## Frozen proposal policy
threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30. **Unchanged.** A-only keeps every predicted proposal (incl. background FPs) and only ADDS GT-assisted ROIs for zero-proposal components.

## Frozen references
Tg (Tiny-Recall gate) = 0.7916666666666666; G = 0.20833333333333337 (=1-Tg);
Dg = 0.6359172411726776; Dice gate = Dg-0.02 = 0.6159172411726776.

## Scientific question
Can the first H3 axis be uniquely selected between A_PROPOSAL_SUPPLY_RECALL_LIMITATION and
C_PROPOSAL_CONTAMINATION_LIMITATION without changing both? Decisive test: if missing proposal
supply is repaired while contamination is left untouched, does the frozen system recover the
Tiny-recall signal required by Phase 14?

## Interventions (all NON-DEPLOYABLE)
- **A-only** `GT_ASSISTED_MISSING_PROPOSAL_SUPPLY_COMPLETION__NON_DEPLOYABLE`: for every GT component
  with ZERO matched predicted proposal, add ONE GT-derived Oracle-geometry ROI (margin 0.20);
  KEEP all original predicted proposals (incl. FPs); same refiner/preproc/fusion/threshold.
- **C-only** `GT_ASSISTED_FALSE_POSITIVE_DECOMPOSITION__NON_DEPLOYABLE`: remove confirmed-background
  proposals; supply unchanged (reuse existing root-cause metrics).
- **A+C** `GT_ASSISTED_SUPPLY_PLUS_FP_REMOVAL__UPPER_BOUND_ONLY` (optional upper bound, not an H3 design).

Conditions reported: GLOBAL, PREDICTED, A_ONLY, C_ONLY, A_PLUS_C, ORACLE_REGIONAL.

## No training / tuning / search
All forbidden (retraining, fine-tuning, H3, threshold/top-k/NMS/margin changes, checkpoint/architecture
comparison, loss/augmentation change, hyperparameter search, TEST reads). Counters = 0.

## Prospectively frozen priority rule
- A_PRIORITY -> H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL if A-only materially increases Tiny
  Recall over PREDICTED (lift >= 0.10), R_A >= 0.50, and C-only does NOT materially increase Tiny Recall.
- C_PRIORITY -> H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_CONTAMINATION_SUPPRESSION only if C-only corrects the
  dominant downstream failure AND A-only fails to restore meaningful Tiny Recall.
- STILL_MIXED -> H3_NOT_READY__TWO_AXES_JOINTLY_REQUIRED.
- INSUFFICIENT -> H3_NOT_READY__INSUFFICIENT_CAUSAL_SEPARATION.
- Do not invent another label. If eligible, name EXACTLY ONE axis.
