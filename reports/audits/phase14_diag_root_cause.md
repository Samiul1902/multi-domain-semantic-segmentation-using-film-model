# POST-PHASE14 Root-Cause Diagnostic — Proposal / Localizer Bottleneck

Population: 103 FULL_FIELD VAL images, 152 components (TINY 72/SMALL 28/MEDIUM 36/LARGE 16).

## §5 Proposal Supply (overall)
- Total proposals: 514; per image mean 4.9903; zero-proposal images: 0.
- Proposal precision (TP fraction): 14.4%; background-proposal fraction: 85.6%; duplicate-proposal rate: 1.17%.
- Components with ZERO matched proposal: 79/152 (51.97%).
- Component proposal recall: any-overlap 48.03%, >=0.50 47.37%, >=0.90 39.47%.
- TINY emphasis: zero-proposal 57/72 (79.17%); recall any 20.83%, >=0.90 20.83%.

## §6 Geometry Bridge (components with a proposal)
- GT coverage inside predicted ROI: mean 0.9474, median 1.0; fraction with >=0.90 context 82.19%.
- Center displacement: mean 27.753 px; ROI box IoU vs Oracle: mean 0.4497.
- Excess background area fraction: mean 0.002585.

## §7 Conditional Refiner (by best-proposal coverage stratum)
- **COV_GE_0.90** (n=60): predicted_cov90 53.33%, refiner-crop coverage 0.8621, refiner improves global 55.0%.
- **COV_0.50_0.90** (n=12): predicted_cov90 0.0%, refiner-crop coverage 0.391, refiner improves global 66.67%.
- **COV_LT_0.50** (n=1): predicted_cov90 0.0%, refiner-crop coverage 0.0245, refiner improves global 100.0%.
- **NO_MATCHED_PROPOSAL** (n=79): predicted_cov90 15.19%, refiner-crop coverage 0.0, refiner improves global 35.44%.
- Image Dice where an adequate (>=0.90) proposal exists: GLOBAL 0.5848 -> PREDICTED 0.3054 (n=49).

## §8 Counterfactuals
- Dice: GLOBAL 0.6359, PREDICTED 0.4185, ORACLE_SEL 0.6304, FP_REMOVED 0.6288.
- Tiny recall: GLOBAL 79.17, PREDICTED 79.17, ORACLE_SEL 79.17.
- FP burden: PREDICTED 7.7767, ORACLE_SEL 0.6796, FP_REMOVED 0.6893.

## §9 Failure Attribution
- Dominant mechanism: **F_MIXED_BOTTLENECK**
- Primary face: **A_PROPOSAL_SUPPLY_RECALL_LIMITATION**; secondary face: **C_PROPOSAL_CONTAMINATION_LIMITATION**
- Refuted mechanisms (evidence): B_PROPOSAL_GEOMETRY_LIMITATION, D_PROPOSAL_RANKING_LIMITATION, E_REFINER_DOMAIN_SHIFT_ON_PREDICTED_CROPS
- Mechanism scores: C_PROPOSAL_CONTAMINATION_LIMITATION=0.856, A_PROPOSAL_SUPPLY_RECALL_LIMITATION=0.520, B_PROPOSAL_GEOMETRY_LIMITATION=0.086, D_PROPOSAL_RANKING_LIMITATION=0.000, E_REFINER_DOMAIN_SHIFT_ON_PREDICTED_CROPS=0.000
- Interpretation: A = supply/recall (52% of components, 79% of TINY, get NO proposal) -> R=0, tiny recall frozen at global. C = precision/background (85.6% of proposals are background FPs; FP burden 7.78/img) -> Dice collapses 0.6359->0.4185; FP removal recovers 0.6288. Refiner (E) works on adequate crops (0.862 coverage), so NOT the bottleneck. Geometry (B) and ranking (D) refuted.

## §10 H3 Readiness
- Status: **H3_NOT_READY__CAUSE_UNRESOLVED**.
- Phase 15: NOT_STARTED_AND_NOT_AUTHORIZED. H3 training: NOT_STARTED.

## Governance
- No training, no H3, no threshold/search/tuning. TEST reads 0; external TEST reads 0.