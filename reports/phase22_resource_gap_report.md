# Phase 22 — Multi-Domain Scale, Regional-Benefit & Resource Gap Analysis

**Diagnostic gap analysis on the frozen Phase-21 Global MedFiLM reference.** No training, no architecture change, no benefit predictor, no TEST access.

| Item | Value |
|---|---|
| Protocol | `phase22_diagnostic_protocol_v1` (frozen=True) |
| Reference | `phase21_global_medfilm_fourdomain_seed42_clean_v3` (frozen, unchanged) |
| Reference binding | PHASE22_REFERENCE_BINDING_PASS (38/38) |
| Population | 808 VAL cases (identical to Phase 21) |
| TEST | CLOSED — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Terminal state | `PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE__PHASE23_ELIGIBLE_NOT_STARTED` |

## Interpretation guards (binding)

1. The **ORACLE regional arm uses ground-truth geometry**. It is an **upper bound**, not a deployable result, and no method may be said to attain it.
2. Where a paired CI overlaps zero, the arms are **not separable**; no ordering claim is made.
3. The reference is the **lightest of the six-model panel**, but its absolute compute is **not small**. 'Lightest of the panel' is not 'fit for constrained deployment'.
4. Phrasing is restricted to *"the reference achieved X compared with baseline Y"*. **"X caused +Y" is forbidden** — there is no architecture-matched control.

## 1. Decision-rule audit

The persisted Phase-21 maps store a **float16** probability and a **uint8** prediction. A float16 probability cannot reproduce the stored uint8 prediction exactly: pixels at *exactly* 0.5 are labelled both ways across the corpus.

| Quantity | Value |
|---|---|
| Adopted rule | `pred = (float32(prob) >= 0.5)` |
| Exact-0.5 pixels | 3362 (foreground: 2284, background: 1078) |
| Mixed labels present | True |
| Maps with mixed tie labels | 327 |
| `>=` rule residual | 1078 px over 373 maps |
| `>` rule residual | 2284 px over 460 maps |
| Unexplained (non-0.5) disagreements | {} |

Root cause: the canonical pass thresholded float32 sigmoid outputs and then persisted the probabilities as float16; the two sides of the boundary collapse onto the same stored value

The **smaller-residual** rule is adopted **and** it is the frozen evaluation rule; it is applied **identically** to the reference and to every probe arm, so no arm is advantaged by the choice.

## 2. Global failure atlas

- Population: **808** VAL cases; pooled mean Dice **0.838782**, median **0.890095**, p05 **0.514941**; mean IoU **0.750597**, precision **0.849898**, recall **0.859699**.
- Dice below 0.5: **38**; below 0.7: **102**; empty-case rows: **0**; total foreground pixel error: **5144149**.

| Category | n | share |
|---|---|---|
| EMPTY_CASE_BOTH | 0 | 0.00% |
| EMPTY_CASE_FALSE_POS | 0 | 0.00% |
| EMPTY_CASE_MISSED | 0 | 0.00% |
| OVER_SEGMENTATION | 43 | 5.32% |
| UNDER_SEGMENTATION | 32 | 3.96% |
| MIXED_BOUNDARY | 25 | 3.09% |
| GOOD | 708 | 87.62% |

Taxonomy thresholds were **declared prospectively** in the frozen protocol and were **not** used to select any case for intervention.

## 3. Scale sensitivity (256 / 512 / 768 / 1024)

Every probe re-runs the **same frozen checkpoint** at a different input resolution and is scored in **native image space**. 512 is the canonical reference, read from the persisted Phase-21 maps (never re-inferred).

> **Required wording (B5).** For the frozen checkpoint trained at 512, 512 had the highest observed performance among the tested diagnostic resolutions (256/512/768/1024); all tested off-canonical sizes were worse. **This does not establish a globally optimal inference resolution.** The ordering is confounded with the training resolution and is off-training-distribution for every non-512 probe.

| Size | macro Dice | Δ vs 512 | 95% CI | Separable |
|---|---|---|---|---|
| 256 | 0.688499 | -0.138240 | [-0.155253, -0.122172] | True |
| 512 | 0.835343 | 0.000000 | [0.000000, 0.000000] | False |
| 768 | 0.776819 | -0.036888 | [-0.044632, -0.029160] | True |
| 1024 | 0.682561 | -0.100413 | [-0.110645, -0.090445] | True |

- **Pipeline-fidelity gate A**: PASS (residual 2884 px, all within 0.02 of the decision boundary: True).
- **Probability gate B**: max |Δp| in the shared 512 canvas 0.00923365 (verdict REVIEW).
- **Gate C** (vs stored prediction): REPORTED_NOT_GATED — reported, not gated, because of the float16 incompatibility above.
- Dice by decision source: `{"probe_reinference_canonical_rule_native": 0.8390402334224809, "canonical_stored_pred_native": 0.8384789752954946, "canonical_stored_pred_in_512_square_space": 0.8387815425121063, "note": "Dice is insensitive to the float16 tie artefact at this scale; all three agree to ~1e-4."}`

## 4. Regional intervention (ORACLE and PREDICTION-DERIVED)

Frozen ROI rule: tight bbox → centre-preserving 1.50× expansion → clip → square-pad → aspect-preserving resize to 512 → paste over the ROI footprint only. Re-centred after clip: **False**.

| Variant | n exec | n no-ROI | mean Δ (exec) | mean Δ (ITT) |
|---|---|---|---|---|
| oracle | 808 | 0 | -0.042478 | -0.042478 |
| predicted | 808 | 0 | -0.060218 | -0.060218 |

**The oracle variant uses ground truth. It is an upper bound and must never be reported as a deployable gain.**

## 5. Benefit heterogeneity, oracle ceiling, routing regret and harm

- Executed oracle gain: mean **-0.042478**, median **-0.013680**, improved/worsened/unchanged **271/536/1**.
- Concentration: Gini **0.6440**, top-10% share of benefit **49.24%**.
- Correlation of gain with baseline Dice: **-0.2118**; with ROI area fraction: **0.1453**.

| Policy value | Dice |
|---|---|
| Always global | 0.839040 |
| Always regional (oracle) | 0.796562 |
| **ORACLE accept-if-beneficial ceiling** | **0.860074** |

Acceptance rate **33.54%**; ceiling gain over always-global **0.021034**. This is a **ceiling**, not an achieved result, and is **not deployable**.

`deployable` = the rule consults **only predicted information** (never ground truth).

| Policy | deployable | uses GT | fraction routed | pooled Dice | regret vs ceiling |
|---|---|---|---|---|---|
| ALWAYS_GLOBAL | True | False | 0.00% | 0.839040 | 0.021034 |
| ALWAYS_REGIONAL_ORACLE | True | False | 100.00% | 0.796562 | 0.063512 |
| ORACLE_ACCEPT_IF_BENEFICIAL | False | True | 33.54% | 0.860074 | 0.000000 |
| PRED_ROI_EXISTS | True | False | 100.00% | 0.796562 | 0.063512 |
| PRED_ROI_EXISTS_AND_BASELINE_BELOW_MEDIAN | True | False | 50.00% | 0.816364 | 0.043710 |
| PRED_ACCEPT_IF_PREDICTED_BENEFICIAL | True | False | 29.21% | 0.851804 | 0.008270 |

No selector was **trained**; these are fixed rules evaluated offline. **The `ORACLE_ACCEPT_IF_BENEFICIAL` row is not deployable** (`deployable = False`) — it peeks at the ground truth and exists only to define the ceiling.

> **CRITICAL CAVEAT: every policy here, including PRED_ACCEPT_IF_PREDICTED_BENEFICIAL, is EVALUATED ON THE SAME VAL POPULATION IT WAS INSPECTED ON. Its regret is therefore a POST-HOC, optimistically-biased quantity, NOT an out-of-sample estimate. No policy may be reported as a generalisable achieved result; establishing that would require a held-out protocol and training, both of which Phase 22 forbids.**

- Harm: **536/808** executed cases (66.34%); worst harm **-0.833422**; harm rate (ITT) **66.34%**.

## 6. Prediction-derived ROI and uncertainty-vs-benefit

- **NO_PREDICTED_ROI rate: 0.00%** (0/808). A total miss yields no ROI, so the deployable-shaped path fails exactly where recovery is most needed.
- Mean Δ Dice (ITT) **-0.060218**; executed **-0.060218**; corr(predicted gain, oracle gain) **0.6839**.

### 6.1 Deployable (GT-free) benefit proxies

A routing signal is only **deployable** if it can be computed **without ground truth**, **before** any refinement, and **at inference time**. The following signals satisfy that test, and are ranked by |Spearman| against the oracle regional gain (the *target* may use ground truth; the *input signal* must not).

| Deployable signal | uses GT | before refinement | at inference | n | Pearson | Spearman | ROC-AUC | PR-AUC |
|---|---|---|---|---|---|---|---|---|
| `predicted_roi_side` | None | None | None | 808 | -0.0094 | -0.0689 | 0.4188 | 0.2994 |
| `frac_prob_within_0p02_of_boundary` | None | None | None | 808 | 0.0807 | 0.0573 | 0.5026 | 0.3481 |
| `frac_prob_within_0p05_of_boundary` | None | None | None | 808 | 0.0793 | 0.0564 | 0.5026 | 0.3467 |
| `predicted_roi_area_fraction` | None | None | None | 808 | 0.1325 | 0.0562 | 0.4946 | 0.3433 |
| `mean_boundary_margin` | None | None | None | 808 | -0.0792 | -0.0481 | 0.5026 | 0.4104 |
| `entropy_proxy_mean` | None | None | None | 808 | 0.0812 | 0.0471 | 0.4964 | 0.3348 |
| `task_id` | None | None | None | 808 | -0.0567 | -0.0213 | 0.5551 | 0.3806 |
| `pred_foreground_fraction` | None | None | None | 808 | 0.0793 | 0.0201 | 0.4622 | 0.3076 |

- Best **GT-free** signal: `predicted_roi_side` with ρ = **-0.0689** (|ρ| = 0.0689), ROC-AUC **0.4188**. **This is essentially no predictive signal**: every deployable proxy is weak in magnitude and near-chance in ROC-AUC. No threshold was fitted, no policy selected and no model trained, so **no deployable router is established**.

### 6.2 Post-hoc ground-truth associations (NOT deployable)

The frozen analysis ranked ground-truth-derived quantities alongside the deployable ones and reported `recall` as the best **deployable** signal. That claim was **invalid**: `recall`, `precision`, `Dice`, `IoU`, ground-truth `ECE`/`Brier`, the oracle ROI area, the ground-truth foreground size and `predicted_delta_dice` **all require the ground-truth mask** and cannot be computed at deployment. They are reported here, separately, purely as **post-hoc diagnostics**.

| GT-derived signal | uses GT | deployable | n | Pearson | Spearman |
|---|---|---|---|---|---|
| `oracle_delta_dice` | True | False | 808 | 1.0000 | 1.0000 |
| `predicted_delta_dice` | True | False | 808 | 0.6839 | 0.7739 |
| `mce` | True | False | 808 | 0.0588 | 0.1857 |
| `recall` | True | False | 808 | -0.1005 | 0.1409 |
| `precision` | True | False | 808 | -0.2573 | -0.1255 |
| `iou` | True | False | 808 | -0.1605 | -0.1193 |
| `dice` | True | False | 808 | -0.2205 | -0.1193 |
| `ece` | True | False | 808 | 0.1093 | 0.1189 |
| `mcc` | True | False | 808 | -0.2224 | -0.1099 |
| `brier` | True | False | 808 | 0.1053 | 0.0854 |
| `specificity` | True | False | 808 | -0.1346 | -0.0671 |
| `oracle_roi_area_fraction` | True | False | 808 | 0.1453 | 0.0628 |
| `balanced_accuracy` | True | False | 808 | -0.1344 | 0.0318 |
| `gt_foreground_pixels` | True | False | 808 | 0.0446 | -0.0157 |

> **`predicted_delta_dice` is ground-truth-derived, despite its name.** It equals `predicted_dice − global_dice`, and both operands are Dice scores measured against the ground-truth mask (identity verified to a maximum residual of 3.1e-16). It must never be used as a deployable routing signal.

## 7. Resource frontier, envelopes and the resource gap

- Reference: **3,523,001** params, **31.5517 G MACs** per 1×3×512×512 image (param rank 1, compute rank 1 of the six-model panel).
- Absolute cost is small: **False**. the reference is the LIGHTEST of the six-model panel, but ~31.6 G MACs per image is NOT a small absolute cost. 'Lightest of the panel' must never be reported as 'fit for constrained deployment'. No pruning, quantization, distillation, or NAS has been performed and none is claimed.
- Measurement provenance: MACs are an exact closed-form count for Conv2d and Linear layers and a LOWER bound on total arithmetic; GroupNorm, SiLU, pooling, bilinear interpolation, FiLM modulation and sigmoid are excluded

**Conditional-compute caveat.** the regional pass always costs ONE full 512x512 forward regardless of crop size, because the crop is resampled to 512. Conditional compute therefore saves EXECUTIONS, not resolution. A smaller crop does NOT cost less.

**Approximation.** MAC counts at non-512 resolutions are scaled by (size/512)**2; this is exact for a fully convolutional stack at fixed channel widths and is an approximation for the true graph

| Policy | fraction regional | mean G MACs | ×always-global | pooled Dice | regret |
|---|---|---|---|---|---|
| ALWAYS_GLOBAL | 0.00% | 31.5517 | 1.0000 | 0.839040 | 0.021034 |
| ALWAYS_REGIONAL_ORACLE | 100.00% | 63.1035 | 2.0000 | 0.796562 | 0.063512 |
| ORACLE_ACCEPT_IF_BENEFICIAL | 33.54% | 42.1341 | 1.3354 | 0.860074 | 0.000000 |
| PRED_ROI_EXISTS | 100.00% | 63.1035 | 2.0000 | 0.796562 | 0.063512 |
| PRED_ACCEPT_IF_PREDICTED_BENEFICIAL | 29.21% | 40.7673 | 1.2921 | 0.851804 | 0.008270 |

**CPU baseline (measurement).** batch 1, AMP=False, threads 8:

| Size | mean ms | max process RSS MiB | analytical G MACs |
|---|---|---|---|
| 256 | 93.3 | 646.1 | 7.8879 |
| 512 | 389.5 | 913.2 | 31.5517 |
| 768 | 768.4 | 1323.0 | 70.9914 |

process RSS (working set) is the metric; tracemalloc was rejected because it reports 0.0 for a torch forward pass - the tensor arena is C-allocated and invisible to it

these timings are host-specific and are reported as an absolute baseline, not as a hardware-independent quantity. CPU timings are recorded separately from the analytical MAC count, which is device-independent.

## 8. KUB TINY, domain preservation, statistics, scale-vs-regional

- **KUB TINY** (`kub_size_clean_v3_v1`): TINY optimised on = **False**. TINY = component_ratio <= Q25 = 0.0001497998649691358 (frozen, lower-inclusive)
  - TINY stratum oracle Δ Dice (ITT) **0.013197**, executed **0.013197**, n = 44, baseline Dice 0.532079.

  - **Required wording (B5).** KUB TINY was the only frozen size stratum with a positive observed mean oracle regional gain (+0.013197 Dice), but the paired 95% CI [-0.084062, 0.105133] includes zero (p=0.763); therefore the TINY effect is descriptive and not statistically established.
  - This does **not** weaken the useful finding: regional benefit is **strongly heterogeneous**, and always-on regional processing is **harmful in aggregate**.

- **Domain preservation**: the reference is frozen, so no per-domain property of the reference can change. Reference unchanged: **True**.

| Comparison | Δ | 95% CI | p | separable |
|---|---|---|---|---|
| oracle_regional_vs_global_executed | -0.042478 | [-0.052343, -0.032363] | 0.0000 | True |
| oracle_regional_vs_global_intent_to_treat | -0.042478 | [-0.052343, -0.032363] | 0.0000 | True |
| predicted_regional_vs_global_intent_to_treat | -0.060218 | [-0.070553, -0.050742] | 0.0000 | True |
| predicted_regional_vs_global_executed | -0.060218 | [-0.070553, -0.050742] | 0.0000 | True |
| scale_256_vs_512_native | -0.138240 | [-0.155253, -0.122172] | 0.0000 | True |
| scale_768_vs_512_native | -0.036888 | [-0.044632, -0.029160] | 0.0000 | True |
| scale_1024_vs_512_native | -0.100413 | [-0.110645, -0.090445] | 0.0000 | True |

where the CI overlaps zero the arms are NOT separable and no ordering claim may be made

| Axis | macro Dice | relative cost | uses ground truth |
|---|---|---|---|
| scale_256 | 0.688499 | 0.2500 | False |
| scale_512 | 0.835343 | 1.0000 | False |
| scale_768 | 0.776819 | 2.2500 | False |
| scale_1024 | 0.682561 | 4.0000 | False |
| regional_oracle_512 | 0.781349 | 2.0000 | True |
| regional_predicted_512 | 0.765239 | 2.0000 | False |
| baseline_512_global | 0.835079 | 1.0000 | False |

The **REGION** arm is the only one that consumes ground-truth geometry (the oracle ROI); the scale and baseline arms do not.

**the scale axis is a genuine (if off-training-distribution) measurement. The regional-ORACLE axis is an UPPER BOUND that uses ground truth. The two are NOT directly comparable as methods, and the oracle must not be presented as the better 'method'.**

## 9. Governance: no-new-training audit and candidate evidence

- Verdict: **PHASE22_NO_NEW_TRAINING_AUDIT_PASS** (8/8).
- Forbidden training constructs found in Phase-22 code: **0** (expected 0; 12 files scanned).
- `training_jobs_started` = **0**; optimizer constructed = **False**; backward called = **False**; checkpoint written = **False**; new experiment directory = **False**.
- TEST reads: image 0, mask 0, inference 0, visualization 0.

- **Future benefit-label contract** (contracted, NOT used): quantity `delta_dice = dice(regional_fused) - dice(global)`; geometry source for a *deployable* label must be **PREDICTED (the model's own prediction), never the ground truth**. Status: **CONTRACT_PROPOSED_NOT_IMPLEMENTED**; it is a training artifact: **False**.

- **C1 REGIONAL ZOOM (oracle upper bound)** — status `BOUNDED_ONLY`. Supports: a positive, measurable ceiling exists for a perfect selector on this population Does **not** support: ['that any deployable selector attains it', 'that the gain survives on TEST (never measured)']
- **C2 PREDICTION-DERIVED ROI (untrained)** — status `WEAK_AS_IMPLEMENTED`. Supports: the ROI can be derived without ground truth, so the shape of a deployable pipeline is realisable Does **not** support: that the untrained ROI is an effective policy; the no-ROI rate and the ITT delta are the evidence against
- **C3 SCALE (input resolution)** — status `MEASURED_OFF_TRAINING_DISTRIBUTION`. Supports: resolution is a real sensitivity of this reference Does **not** support: ['that any non-512 resolution is better (the model was trained at 512)', 'that re-training at another resolution would reproduce this ordering']
- **C4 ROUTING (benefit-aware compute allocation)** — status `PRE_TRAINING_EVIDENCE_ONLY`. Supports: a well-defined cost/accuracy trade-off exists Does **not** support: any claim about a learned router: none was trained, and Phase 22 forbids training one
- **C5 COMPRESSION / EFFICIENCY** — status `UNSUPPORTED`. Supports: the reference is the lightest of the six-model panel Does **not** support: ['that ~31.6 G MACs is small in absolute terms', 'that pruning/quantization/distillation would preserve accuracy: none was performed']

## 10. Boundary

Phase 22 is a **diagnostic gap analysis**. It does **not** propose, train or validate any method. It contains **no** router, localizer, benefit predictor, fusion module, compression or architecture search, and it reads **no** TEST data. Phase 23 is **ELIGIBLE but NOT STARTED**.

> **STOP.** Phase 23 is not started.

