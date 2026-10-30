# Phase 28 — Ablation Execution Specification v1.2

**Method:** RA-MedFiLM-BARR
**Phase:** 28 — Comprehensive System Ablation Matrix
**Document class:** SUPERVISOR_PROSPECTIVE_OPERATIONALIZATION_RULING
**Revision:** v1.2
**Status:** SPECIFICATION / GOVERNANCE ONLY — no execution performed
**Predecessor terminal:** `PHASE28_BLOCKED__R1_R2_R3_F1_EXECUTION_SEMANTICS_INCOMPLETE`

---

## 0. Purpose

This document prospectively resolves the two remaining execution-semantics
ambiguities that blocked Phase 28 at the v1.1 boundary:

1. the exact operational meaning of the R1/R2/R3/F1 ablations;
2. the exact comparison/reference topology for A0–A8 (already recovered in v1.1
   and preserved unchanged here).

**Provenance statement.** The original Phase-24 ablation definitions remain
**unchanged**. v1.2 supplies the previously missing *execution mechanics* only.
No Phase-28 outcome existed when this ruling was frozen. This ruling is
prospective, pre-outcome, and limited to Phase 28.

**No training, no model forward, no ablation execution, no metrics, no
ROUTER_HOLDOUT, no TEST occurred in the production of this document.** All
execution counters are zero.

---

## 1. Governing ruling — trained ablation variants

R1/R2/R3/F1 are frozen as:

```
SEPARATELY_TRAINED_CONTROLLED_ABLATION_VARIANT
```

They are **NOT**:

- inference-time feature zeroing;
- input occlusion;
- post-hoc masking of the canonical trained model.

**Rationale.** The frozen wording is literally *"router without deep global
features"*, *"router without task_id"*, *"router with scalar-only features"*, and
*"refiner without p_global channel"*. The scientifically faithful implementation
of "without X" is to remove X from the model **input during fitting and
evaluation** — i.e. to train a genuinely different model — not to zero or mask a
canonical model's input at inference time.

Recorded consequences:

| Field | Value |
|---|---|
| `prior_scientific_results_changed` | `false` |
| `canonical_Phase26_bundle_changed` | `false` |
| `Phase28_execution_spec_changed` | `true` |

---

## 2. Training authorization — limited scope

The prior Phase-28 blanket `NO_TRAINING` is **superseded** by:

```
ABLATION_ONLY_TRAINING_AUTHORIZED_FOR_R1_R2_R3_F1
```

Training remains **forbidden** for A0–A8, GlobalMedFiLM, the canonical Phase25D
`B_phi`, the canonical Phase25A refiner, and the canonical Phase25F `S_omega`.
No canonical checkpoint may be overwritten. All ablation checkpoints must live
under new Phase-28-specific paths (§29).

---

## 3. Router ablation reference

For R1/R2/R3 the principal router reference is:

```
FULL_FEATURE_BENEFIT_ROUTER   ==  A6 / C7 learned paired-gain router
```

Population: `ROUTER_DEVELOPMENT`, n = 4957.

**Primary router-level question.** Does removing the specified router information
reduce the quality of paired-gain routing at the *same fixed compute budget*?

For integrated system reporting, each R-variant system is compared against the
`A8 / C9` canonical full system, holding all downstream components unchanged.

---

## 4. Router training protocol inheritance

R1/R2/R3 inherit the **exact** Phase25D router-training protocol, bound physically
to the authoritative artifacts:

| Field | Frozen value | Source |
|---|---|---|
| Outer folds | 5 | `phase25d_cv_protocol_v1_2_1.json` |
| Outer algorithm | `StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)` | idem |
| Outer group key | canonical composite `group_key` from `phase24_router_split_manifest.csv` | idem |
| Outer stratification | domain only | idem |
| Sort before split | `[domain, group_key, sample_id]` | idem |
| Inner split | `StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=4200+outer_fold_index)` | `phase25d_nested_cv_split_contract_v1_2_1.json` |
| Inner role rule | inner fold 0 = EARLY_STOP, inner folds 1–9 = FIT | idem |
| CV manifest | `reports/tables/phase25d_cv5_manifest.csv` (sha `008b92963664f38e…`) | idem |
| Per-fold role manifests | `phase25d_cv_fold{k}_{fit,early_stop,outer_target}_ids.csv` with per-fold SHA binding | idem |
| Loss | `HuberLoss(delta=0.05, reduction="mean")` | `phase25d_frozen_training_spec_binding_v1_2_1.json` |
| Optimizer | `AdamW(lr=1e-3, weight_decay=1e-4)` | idem |
| Batch size | 128 | idem |
| Max epochs | 200 | idem |
| Early-stop patience | 20 | idem |
| Scheduler | `ReduceLROnPlateau(mode="min", factor=0.5, patience=8, threshold=1e-4, threshold_mode="rel", cooldown=0, min_lr=1e-6, eps=1e-8)` | idem |
| Checkpoint metric | EARLY_STOP mean Huber loss | `phase25d_checkpoint_selection_contract_v1_2_1.json` |
| Checkpoint direction | MINIMIZE | idem |
| Checkpoint tie rule | earlier epoch wins; ties count as non-improvement | idem |
| Scheduler ordering | `scheduler.step(es_huber)` after checkpoint test | `scripts/analysis/train_phase25d_router.py` L314 |
| Fold seed | **`42000 + outer_fold_index`** (verified in `fold0/best.pt` `seed=42000`) | trainer L396 |
| Deterministic settings | `random/np/torch.manual_seed(fold_seed)` (+ CUDA all) | trainer L214–218 |

**Recovery status: COMPLETE.** Every scientifically material Phase25D training
value is physically recoverable — no value was taken from memory, and the
physical trainer `scripts/analysis/train_phase25d_router.py` agrees with the
frozen JSON contracts (notably on the fold-seed policy `42000 + k`).

**Fail-closed rule.** If any material value could not be physically recovered the
order directs `PHASE28_V1_2_BLOCKED__ROUTER_ABLATION_TRAINING_PROTOCOL_INCOMPLETE`.
That condition is not met.

---

## 5. Router target

Use exactly the existing Phase25C paired-gain target:

```
DeltaDice = Dice(refined_candidate, GT) - Dice(global, GT)
```

No new target, no target scaling, no new outcome definition. Same target table
(`data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv`)
and exact frozen SHA.

---

## 6. R1 — no deep global features

Canonical router input before task embedding: **202 numeric features** = 192 deep
global + 10 scalar.

- R1 **removes** all 192 deep global features.
- R1 **retains** all 10 frozen scalar features and task_id conditioning.

Model input: 10 scalar numeric + the same learned task embedding `Embedding(4,16)`.
Effective first-layer width **10 + 16 = 26**.

Architecture after input width is identical to Phase25D:
`Linear(·,128) → LayerNorm(128) → SiLU → Dropout(0.10) → Linear(128,64) →
LayerNorm(64) → SiLU → Dropout(0.10) → Linear(64,1)`.

Only the input dimensionality changes.

---

## 7. R1 normalization

Exactly the Phase25D scalar-normalization semantics. Among the 10 scalars the
same frozen continuous subset is standardized:

```
entropy_proxy_mean, frac_prob_within_0p05_of_boundary,
frac_prob_within_0p02_of_boundary, mean_boundary_margin,
pred_foreground_fraction, pred_foreground_pixels,
predicted_roi_area_fraction, predicted_roi_side
```

FIT-only statistics per outer fold; population std `ddof=0`; constant std
`< 1e-12 → normalized 0.0`. Keeping the same unnormalized flags exactly as
Phase25D: `pred_roi_exists`, `pred_empty` are **not** standardized. task_id is
never normalized. No new statistics are invented.

---

## 8. R2 — no task_id

- R2 retains all canonical 202 numeric features.
- R2 removes the task embedding and task_id input completely.

**There is no zero task embedding vector.** The embedding module does not exist in
R2. Effective first-layer width **202**.

Then the identical hidden topology
`Linear(202,128) → LN → SiLU → Dropout → Linear(128,64) → LN → SiLU → Dropout →
Linear(64,1)`. All numeric normalization semantics remain identical to Phase25D.

---

## 9. R3 — scalar-only router

R3 is the explicit minimal-feature control.

- R3 retains ONLY the 10 frozen scalar router features.
- R3 removes the 192 deep global features, task_id, and the task embedding.

Effective first-layer width **10**, then the identical hidden topology.

R3 is a **FEATURE-SET CONTROL**. It must not be described as a single-input-variable
causal isolation.

---

## 10. Router OOF requirement

R1/R2/R3 scientific predictions MUST be out-of-fold. For each outer fold: train
only on that fold's inherited FIT rows; use inherited EARLY_STOP rows for model
selection; predict only the inherited OUTER_TARGET rows.

Every one of the 4957 rows receives exactly one OOF score. No sample contributes
to fitting or checkpoint selection for the model that predicts that sample.

**No final all-DEV refit is required for Phase28.** These are ablation models, not
deployment candidates.

---

## 11. Router variant seeds

Reuse the exact Phase25D fold seed policy: **`seed = 42000 + outer_fold_index`**.
No different seeds may be introduced because these are ablations.

---

## 12. Router budget / calibration ruling

This ruling **supersedes** the missing scalar-threshold requirement for R1/R2/R3.
Phase28 router ablations are evaluated at a FIXED EQUAL ACTIVATION BUDGET.

| Symbol | Value |
|---|---|
| Primary budget | 0.25 |
| Eligible N | 4957 |
| K = floor(0.25 × 4957) | **1239** |

For EACH R1/R2/R3 variant: rank its OOF `delta_hat` score **descending**,
tie-break by **sample_id ascending**, select exactly the first **1239**.

This rule is frozen NOW, before any variant score exists. No GT outcome may affect
membership.

---

## 13. No scalar tau required for R1/R2/R3

Do NOT derive a deployment threshold. Do NOT reuse the canonical final-router tau.
Do NOT create a final-router runtime calibration.

R1/R2/R3 are development-only ablations. Their policy identity is:

```
variant architecture + OOF score + fixed K=1239 rank rule
```

Record: `scalar_tau = NOT_APPLICABLE__DEVELOPMENT_FIXED_BUDGET_ABLATION`.

---

## 14. Resource term for router variants

The regional action cost `C` is constant. At fixed K, `delta_hat` and
`delta_hat − lambda*C` have identical ranking. Therefore for R1/R2/R3, lambda does
NOT create an independent membership. Use lambda representative = `0.25` for
compatibility with A8 serialization only. Do NOT claim resource cost improves
R1/R2/R3 ranking.

---

## 15. Router outcome-access barrier

After R1/R2/R3 OOF scores are generated: freeze score files, freeze rank order,
freeze K=1239 memberships, and hash them. **ONLY THEN** evaluate them against
Phase25C DeltaDice outcomes.

Membership creation must not use `DeltaDice`, `gain_category`, `global_dice`, or
`candidate_refined_dice` — except where those values are the training target
inside the leakage-safe FIT portions.

---

## 16. Router primary metrics

At fixed 25% budget report: precision@budget, benefit capture, mean true DeltaDice
among routed samples, harmful activation share, beneficial coverage, missed
benefit, oracle regret — using the already frozen metric equations. Primary
R1/R2/R3 comparisons are variant vs full `A6/C7` router at exactly K=1239. **Do
not select a winner for deployment.**

---

## 17. Router integrated secondary analysis

For each R1/R2/R3 selected membership: use the SAME canonical regional candidate
artifacts as Phase25C and the SAME canonical OOF post-safety decisions from
Phase25F where scientifically valid — because neither the refiner nor `S_omega` is
changed by R1/R2/R3. Construct the full-system output exactly as A8 except for
routing membership. Compare descriptively against canonical A8/C9. **Do not alter
any downstream checkpoint.**

---

## 18. F1 — trained refiner without p_global input channel

F1 is a separately trained regional-refiner ablation.

- Canonical refiner input: RGB crop **+** `p_global` crop → `(4, 256, 256)`.
- F1 input: **RGB crop ONLY** → `(3, 256, 256)`.

The `p_global` channel is **physically absent** from the model input. Do NOT feed
zeros as a fourth channel, mask the fourth channel, or reuse the 4-channel weights.
F1 requires a new Phase-28 ablation checkpoint family. Only the first input stage
changes (stem `Conv3x3(4→16)` becomes `Conv3x3(3→16)`); every other architecture
and training choice remains frozen.

---

## 19. F1 ROI geometry remains canonical

F1 removes `p_global` as a REFINER INPUT CHANNEL only. It does **not** remove
`p_global` from the upstream ROI proposal mechanism. Keep exactly:

| Parameter | Value |
|---|---|
| ROI proposal threshold | 0.30 |
| expansion | 1.50 |
| crop resolution | 256 |
| canonical ROI geometry | unchanged |

The controlled factor is therefore `REFINER_INPUT_P_GLOBAL_CHANNEL` and **not**
the ROI proposal mechanism.

---

## 20. F1 training protocol

F1 inherits the exact leakage-safe Phase25A / Phase25C regional-refiner protocol:

| Field | Frozen value | Source |
|---|---|---|
| OOF folds | 3 (cross-fit over ROUTER_DEVELOPMENT) | `phase25a_crossfit_protocol.json` |
| Assignment | deterministic group-safe domain-stratified; `sha256('42::<salt>::<group_key>')` bucket fill; seed 42 | idem |
| Inner split | FIT 0.9 / EARLY_STOP 0.1, group-safe, domain-stratified, seed 42 | idem |
| Fold manifests | `data_cache/phase25a_barr_roi030_cache/folds/` (fit / early_stop / outer_target per fold) | trainer L287–289 |
| Loss | `0.5 * BCEWithLogits + 0.5 * soft Dice(eps=1e-6)` | trainer L338–339, L488 |
| Optimizer | `AdamW(lr=1e-4, weight_decay=1e-4)` | trainer L340 |
| Scheduler | `CosineAnnealingLR(T_max=100)` | trainer L341 |
| Max epochs | 100 | trainer L79 |
| Early-stop patience | 15 | trainer L80 |
| Batch size | 8 | trainer L76 |
| Checkpoint rule | minimum EARLY_STOP total loss | trainer L145 |
| Seed | 42 (all folds) | trainer L75 |
| AMP | enabled on CUDA | trainer L144 |
| Deterministic | `cudnn.deterministic=True`, `benchmark=False` | trainer L301–302 |
| Input preprocessing | RGB/255.0; prob channel as stored; concatenate `[rgb, prob]` | `barr_refiner_dataset.py` L162–170 |
| Augmentation | `SegmentationTransform`: H-flip p=0.5, rotation ±5°, brightness 0.9–1.1, contrast 0.9–1.1 (RGB only) | `phase25a_augmentation_binding.json` |
| Crop geometry | 256×256 ROI crop from ROI-0.30 cache | idem |
| Target mask | 256×256 GT crop (nearest) | idem |
| Output/fusion semantics | logits (no internal sigmoid); head `Conv2d(16,1,1)` | `phase25a_refiner_architecture_binding.json` |
| Architecture | `BARRRegionalRefinerV1`, channels `(16,32,64,96,128)`, 1,276,401 params | idem |

**Only allowed model change:** the first input stage accepts RGB channels without
`p_global`. All other architecture/training choices remain frozen.

**Recovery status: COMPLETE.** The physical trainer
`scripts/training/train_phase25a_refiner.py` and the ROI-0.30 cache agree with the
frozen contracts. The fail-closed condition
`PHASE28_V1_2_BLOCKED__F1_TRAINING_PROTOCOL_INCOMPLETE` is not met.

---

## 21. F1 leakage-safe OOF output

For every ROUTER_DEVELOPMENT sample, the F1 candidate prediction must come from the
F1 fold model for which that sample belongs to OUTER_TARGET. The sample must not
participate in FIT, EARLY_STOP, or checkpoint selection.

Require 4957 exactly-once OOF F1 candidates. No final F1 refiner is needed. F1 is
not a deployment candidate.

---

## 22. F1 primary refiner-level comparison

**Primary question.** Does supplying `p_global` as a refiner input channel improve
refinement?

**Primary comparison:** canonical OOF regional candidate vs F1 OOF regional
candidate — same sample, ROI geometry, global prediction, fusion geometry, and GT
scorer. Report paired candidate DeltaDice difference. This is the cleanest direct
F1 isolation.

---

## 23. F1 routing membership ruling

For integrated F1 reporting, routing membership is frozen to:

```
EXACT CANONICAL A8 25% OOF ROUTING MEMBERSHIP
```

Do NOT rerun or recalibrate `B_phi`. Do NOT change K. Do NOT alter sample selection
because of F1 outcomes. This isolates the refiner-input intervention.

---

## 24. F1 post-safety ruling

F1 changes the candidate prediction, so the post-safety feature vector may also
change downstream. For integrated F1 analysis: recompute ONLY the deterministic
20-D `S_omega` feature vector from the F1 candidate, then run the corresponding
already-frozen OOF Phase25F `S_omega` fold model for that OUTER_TARGET sample.

- Do NOT retrain `S_omega`.
- Do NOT use the Phase25F final all-DEV `S_omega` on OOF evaluation if a
  fold-specific OOF safety model exists.
- Require leakage-safe fold ownership.

**Fold-checkpoint availability.** The frozen Phase25F fold checkpoints are
physically present (`checkpoints/phase25f_barr_post_safety_v1_0_seed42/cv_fold0..4`),
and Phase25F reuses the Phase25D CV5 manifest
(`phase25f_cv_manifest_reuse_contract_v1_0.json`, F7 ruling). The integrated
F1 + `S_omega` analysis is therefore **AVAILABLE**.

Failure contingency (not triggered): if the fold checkpoints were absent, the
integrated analysis would be marked unavailable — never improvised.

---

## 25. F1 reference

- Primary F1 refiner-level reference: canonical Phase25C OOF refiner candidate.
- Integrated F1 reference: `A8/C9` canonical system, with exact A8 routing
  membership retained.

Thus the manipulated scientific factor is `presence/absence of p_global as refiner
input`.

---

## 26. A0–A8 core topology — preserved

The v1.1 contrast map is preserved **unchanged**:

| Ablation | Role |
|---|---|
| A0, A1 | endpoint references |
| A2–A5 | routing-signal comparators vs A6 |
| A6 | learned router vs A0 |
| A7 | A6 + resource formulation |
| A8 | A7 + post-safety |

A7-vs-A8 remains the already-frozen matched post-safety isolation. **Do NOT
redefine all core rows as direct A8 one-factor comparisons.**

---

## 27. A0–A8 execution policy

- A0–A5: artifact reconstruction only.
- A6–A8: reuse prior canonical evidence where exact.

No new A0–A8 model training or inference. No duplicate scientific rerun merely to
fill the matrix.

---

## 28. Statistics

Use the already frozen Phase-28 statistical contract: paired bootstrap with 2000
replicates, seed 42, group/domain-aware mechanics as already bound. Use common
paired draws for matched comparisons. Do not introduce a new multiplicity
procedure. If Phase-28 v1.1 left multiplicity intentionally descriptive, preserve
that status. No post-hoc correction choice after results.

---

## 29. Training artifact contract

Phase28-only output roots:

```
checkpoints/phase28_router_R1_no_deep/
checkpoints/phase28_router_R2_no_task/
checkpoints/phase28_router_R3_scalar_only/
checkpoints/phase28_refiner_F1_no_pglobal/
```

No predecessor checkpoint may be overwritten. Each fold must save: config,
history, best checkpoint, completion audit, normalization (if applicable), fold
identity, and FIT/ES/OUTER_TARGET SHA binding.

---

## 30. Full training-history governance

Because Phase28 now includes ablation training, the future Phase28 reviewer
notebook MUST render **complete immutable epoch histories** for every trained fold.
No `.tail()`, no `.head()`, no truncated epoch tables. For each run verify:
contiguous epoch numbering, no duplicates, finite losses, checkpoint-selected epoch
matches history, and correct early-stop semantics.

---

## 31. Execution counts — this spec repair only

This v1.2 repair itself has:

| Counter | Value |
|---|---|
| training_runs | 0 |
| model_forwards | 0 |
| new_predictions | 0 |
| ablation_metrics | 0 |
| ROUTER_HOLDOUT_reads | 0 |
| TEST_reads | 0 |

Variant training is NOT begun in this work order.

---

## 32. Document control

- Class: `SUPERVISOR_PROSPECTIVE_OPERATIONALIZATION_RULING`.
- Original Phase-24 definitions: **unchanged**.
- v1.2 supplies previously missing execution mechanics.
- No Phase-28 outcome existed when this ruling was frozen.
- Historical v1.0 / v1.1 artifacts are preserved and unmodified.

---

## 33. Executability (v1.2)

See `reports/tables/phase28_ablation_executability_v1_2.csv`. R1/R2/R3/F1 are
`READY_ABLATION_TRAINING_AND_OOF_INFERENCE` only because all inherited training
contracts are physically recoverable. No row is READY based solely on this prompt.

---

## 34. Completeness (v1.2)

See `reports/tables/phase28_specification_completeness_v1_2.csv`. Required
resolution set: R1/R2/R3/F1 execution semantics, training protocols, input
schemas; router variant budget/membership/scalar-tau rules; F1 membership and
post-safety rules; OOF leakage rule; training-history governance. Requirement:
`blocking_fields = []`.
