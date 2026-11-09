# POST-PHASE14 Proposal / Localizer Bottleneck Root-Cause Diagnostic — Frozen Protocol

**Status:** `FROZEN_AWAITING_EXECUTION`
**Authorization context:** Phase-14 clean-v3 closed as `DIAGNOSTIC_PROPOSAL_BOTTLENECK`; Phase-15 `NOT_STARTED_AND_NOT_AUTHORIZED`; H3 `NOT_STARTED` (training NOT authorized). This is a diagnostic / causal-decomposition task ONLY.

## 1. Population (frozen)
- Manifest `phase4_v3`, view `FULL_FIELD`, split `VAL` (clean-v3).
- **103 images**, **152 components**.
- Size strata: **TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16**.
- Hard-Tiny denominator **15**; Global-Empty denominator **5**.
- **TEST split excluded (0 reads); external data excluded.**

## 2. Frozen Checkpoints (SHA-256 bound)
| Role | Path | SHA-256 | Epoch |
|---|---|---|---|
| GLOBAL UNet++ (clean-v3) | `checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt` | `ec7eb13f…1283269` | best |
| Regional Refiner (clean-v3) | `checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/best.pt` | `2e09e3a9…caa45daa` | 56 |
| Stage-4D Localizer (clean-v3) | `checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3/best.pt` | `7673c34a…ca492273` | 53 |

## 3. Frozen Proposal Policy (Stage-4D localizer contract — NO change)
- `threshold = 0.10`, `margin = 0.20`, `top_k = 5`, `nms_iou = 0.30`.

## 4. Frozen Downstream Behavior (NO parameter change)
- Refiner: same frozen regional refiner (epoch 56).
- Regional preprocessing: `crop_and_preprocess(img, mask, geom, target_size=256)`.
- Fusion: `P_final(x) = max_i(P_regional_i(x))` if `x` in union(ROIs) else `P_global(x)` — MAX/DIRECT replacement inside proposal union.
- Segmentation threshold: `0.50`. Global retained outside proposal union.
- Zero-proposal rule: fall back to GLOBAL everywhere.
- Oracle reference margin: `0.20`.

## 5. Frozen References
- `Dg_clean_v3 = 0.6359172411726776`, `Tg_clean_v3 = 0.7916666666666666`.

## 6. Scientific Question
Primary: why does the frozen Stage-4D predicted-proposal pipeline fail to transfer the strong Oracle-refiner potential (Do=0.8024) into practical performance (Dp=0.4185, R=0, Tp==Tg)?
Candidate mechanisms (do NOT assume; classify by evidence):
- **A** Proposal-supply / recall limitation
- **B** Proposal-geometry limitation
- **C** Proposal-contamination limitation
- **D** Proposal-ranking limitation
- **E** Refiner domain shift on predicted crops
- **F** Mixed bottleneck

## 7. No Search / No Tuning
No threshold/top-k/NMS/margin sweep; no proposal grid; no checkpoint/architecture comparison; no retraining/fine-tuning/loss/augmentation redesign; no H3; no TEST. All search/tuning counters = 0.

## 8. Allowed Counterfactuals (descriptive, non-deployable)
- **A** Best-candidate oracle selection within the already-generated frozen candidate set (label `ORACLE_SELECTION_WITHIN_FROZEN_CANDIDATE_SET__DIAGNOSTIC_ONLY`).
- **B** GT-assisted removal of confirmed-background proposals (label `GT_ASSISTED_FALSE_POSITIVE_DECOMPOSITION__NON_DEPLOYABLE`).
- Must NOT choose thresholds.

## 9. Implementation Binding
- Evaluator: `scripts/evaluation/diagnose_phase14_proposal_bottleneck.py`
- Companion timestamp correction: `reports/audits/phase14_clean_v3_governance_timestamp_correction.json`
