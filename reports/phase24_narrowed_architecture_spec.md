# PHASE 24 — NARROWED BENEFIT-AWARE REFINEMENT ARCHITECTURE + PRE-REGISTERED DEVELOPMENT PROTOCOL

**Status:** `DESIGN_ONLY_NOT_IMPLEMENTED`
**Classification:** `PRE_REGISTRATION_SPECIFICATION`
**Method name (frozen, provisional):** `RA-MedFiLM-BARR` — Resource-Aware MedFiLM with Benefit-Aware Refinement Routing
**Architecture id:** `ra_medfilm_barr_narrowed_v1`
**Phase-23 novelty basis:** `PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE` (max claim Level 2; strongest residual = axis D, system integration)

## 0. What this document is, and what it is NOT

This is a **pre-registration specification**. It answers exactly one question:

> *What exactly will we build, train and evaluate later?*

It does **not** build, train, evaluate, count parameters of, or run inference on anything.
Every numeric target in this document is a **DESIGN TARGET** and is explicitly marked
`measured: False`. No segmentation model forward call, no benefit-router forward call, and no
holdout-outcome inspection occurred in producing this document.

| Counter (Phase 24) | Value |
|---|---|
| Training runs | **0** |
| Segmentation inference | **0** |
| Benefit-router inference | **0** |
| Refinement forward passes | **0** |
| Router-holdout outcomes read | **0** |
| VAL outcome reads | **0** |
| TEST image reads / mask reads / inference / visualisation | **0 / 0 / 0 / 0** |
| Phase 25 modules started | **0** |

The terminal consequence of this document is a *specification*, not a result. Any future use of
the frozen name may not assert a finding.

## 1. Provenance and fail-closed entry

An entry gate (`scripts/analysis/run_phase24_entry_gate.py`) runs **before** any Phase-24
artifact is written and is **fail-closed**: a single failed check aborts with
`PHASE24_NARROWED_SPEC_BLOCKED__REDESIGN_REQUIRED`. Result: **27/27 PASS**, verdict
`PHASE24_ENTRY_GATE_PASS`. Bindings verified byte-for-byte:

| Predecessor | Bound value | Check |
|---|---|---|
| Phase-21 `best.pt` SHA-256 | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` | unchanged |
| Phase-22 protocol SHA-256 | `9d620d6c85276e1a9a086ec60172cdef3b94dc58fe8288222378d196dd4609b7` | unchanged |
| Phase-22 freeze SHA-256 | `9a0aa2f8c1a2850770fb09f2838e95f0fe08b3b40e55ab1d10c3564841107bca` | unchanged |
| Phase-23 canonical notebook SHA-256 | `e9f78ccefd96abad742fa5570a44110cd67c62f5510b99300448e44b961107b0` | unchanged |
| Phase-23 verdict | `PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE` | matched |
| Phase-23 max claim level | `2` | matched |
| Phase-23 naming status | `RENAME` | matched |
| Phase-23 visual integrity | 4 required valid / 0 corrupt | matched |
| Phase-23 final check | 42/42 | matched |
| Phase-23 corrected query ledger | 63 | matched |
| Phase-23 C1–C12 constraints | 12 present | matched |
| Existing `phase25_*` artifacts | 0 | none |
| Pre-existing `phase24_*` artifacts | 0 | none |
| TEST counters | all zero | CLOSED |

## 2. The narrowed contribution (Phase-23 residual)

Phase 23 established that the *individual primitives* of the original candidate mechanism are
**occupied**. Adopted verbatim, with no re-litigation:

| Axis | Phase-23 status |
|---|---|
| A — problem formulation | `OCCUPIED` |
| B — learning target | `NOT_OCCUPIED_AS_A_LEARNED_SEGMENTATION_TARGET` |
| C — decision mechanism | `PARTIALLY_OCCUPIED` |
| D — system integration | `NOT_OCCUPIED_AS_A_COMBINATION` ← **strongest residual** |

**The single novelty-bearing component** is therefore, and only, this:

> A **learned, GT-free, pre-refinement** predictor of the **paired refinement gain**, used to route an
> **optional** regional refinement, with a **preservation fallback** and an **explicit resource-cost
> term**, inside **one shared multi-domain medical-segmentation system**.

Everything else in the system is declared **non-novel** and is preserved deliberately
(`reports/audits/phase24_novelty_boundary.json`): the post-refinement fallback (closest to JFS), the
gate mechanism, the paired-gain target formulation, shared multi-domain segmentation, resource-aware
inference as engineering practice, and tiny-structure segmentation.

**Explicit non-claims:** no novelty for the gate mechanism, the paired-gain estimand, multi-domain
sharing, resource awareness, tiny-lesion segmentation, or any algorithmic primitive.
Phase-23 status `OCCUPIED_AT_THE_MECHANISM_LEVEL` is carried forward unchanged.

## 3. Frozen method name and terminology

`reports/audits/phase24_method_naming_decision.json` evaluated two candidates against five criteria
(acronym ambiguity, terminology collision, misleading implication, clarity relative to JFS,
consistency with the Phase-23 boundary).

| Candidate | Expansion | Verdict | Decisive reason |
|---|---|---|---|
| **`RA-MedFiLM-BARR`** | Resource-Aware MedFiLM with Benefit-Aware Refinement Routing | **SELECTED** | Encodes both load-bearing facts: routing is **benefit-aware** (matches Phase-23 `USE_BENEFIT_AWARE_ONLY`) *and* **resource-aware** (C6 requires an explicit cost term). "Benefit-Aware … Routing" signals pre-execution, which is exactly the JFS axis. |
| `RA-MedFiLM-GGR` | Resource-Aware MedFiLM with Gain-Gated Refinement | `NOT_SELECTED` | "Gating" is heavily overloaded **and** names the method after the primitive Phase 23 classified as `OCCUPIED`. Invites the "this is just a gate" objection. |

**Retired name:** `Counterfactual Benefit-Certified Refinement / CBCR` — retired because
*Counterfactual* is unsupported (both potential outcomes are fully observed during development, so
there is no identification problem → `PREFER_PAIRED_REFINEMENT_GAIN`) and *Certified* is unsupported
(no conformal, risk-control or calibration guarantee is earned → `USE_BENEFIT_AWARE_ONLY`).

**Forbidden tokens in the name:** `counterfactual`, `certified`, `causal`, `guaranteed` — check PASS.
**Required first-use form:** `RA-MedFiLM-BARR (Resource-Aware MedFiLM with Benefit-Aware Refinement
Routing)` — the bare acronym may never be the first mention.
**Binding:** provisional and design-level; carries no claim of novelty for any primitive.

## 4. System architecture

Full specification: `reports/audits/phase24_architecture_spec.json` (44 keys).
Design figure: `reports/figures/phase24_architecture_spec/p24_full_system_architecture.png`.

### 4.1 Global reference (frozen anchor)

- Role: produces the **fallback output** and the **reusable features**.
- Signature: `G(x, t) -> (p_global, F_global)`.
- Checkpoint: `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt`,
  SHA-256 `286689fdd5c63ad7…`, architecture `global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1`.
- Parameters: **3,523,001** (measured in Phase 21; the only measured parameter count in this document).
- **Modification policy:** MUST NOT be modified during the initial controlled Phase-25 experiments.
  Any fine-tuning is a separate, later, explicitly authorised change.
- **Feature-reuse requirement:** the router MUST reuse `F_global`. A *second* full Global MedFiLM
  forward purely to make the routing decision is **FORBIDDEN** — it would destroy the compute-saving
  claim (C4).

### 4.2 GT-free region proposal `P_roi`

Frozen rule: `p_global` predicted foreground → tight bounding box → fixed context expansion → clip to
image → square pad → resize to regional-refiner resolution. Constants (context expansion factor,
refiner resolution) derived from **TRAIN only**; tuning on VAL **forbidden**; GT rescue **forbidden**.

`empty_global_prediction` primary behaviour = **`A_SKIP_REFINEMENT`** — the minimal GT-free
zero-extra-cost rule: if the global model predicts no foreground there is no region to refine and the
global output is preserved by the fallback. A deterministic cheap uncertainty-based rescue is retained
**only** as a pre-registered controlled ablation, with any constant derived from TRAIN only and frozen
before Phase 25.

### 4.3 Dedicated regional refiner `R_psi`

- Role: produce the optional refinement `R(x_crop)`. `novelty_claimed: False`.
- **Must not be** the frozen Global MedFiLM checkpoint reused on resampled crops — Phase 22 showed
  that reuse was **harmful in aggregate**.
- Class: dedicated crop-trained lightweight residual U-Net / encoder–decoder.
- Input contract: `[R, G, B, p_global_crop]`; task/domain conditioning permitted (FiLM-style).
  Forbidden inputs: GT mask, GT geometry, GT size category, any GT-derived score.
- **Parameter envelope (DESIGN TARGET, unmeasured):** recommended 0.5M–1.5M; **hard ceiling 2.0M**.
- Avoid: large transformer, foundation-model decoder, oversized pretrained backbone.
- Output is a **candidate**, never a replacement, until the final selection. `novelty_claimed: False`.

### 4.4 Benefit router `B_phi` (the novelty-bearing component)

- Job: estimate the expected **paired refinement gain** *before* `R_psi` executes. It is **not** an
  uncertainty predictor.
- `pre_refinement: True`, `gt_free: True`.
- Allowed inputs: `reports/tables/phase24_router_input_contract.csv` — **15 allowed** features, every
  one of which satisfies `uses_GT=false ∧ available_pre_refinement=true ∧ inference_available=true`;
  **16 forbidden** features.
- Output: primary `Delta_hat_Dice` (predicted paired Dice gain); optional auxiliary `p_harm`.
- Architecture family: small MLP / shallow feature-fusion network. Forbidden: transformer router,
  foundation model, a second image encoder.
- **Envelopes (DESIGN TARGETS, unmeasured):** ≤ **250,000** parameters; ≤ **2%** of one global
  forward's analytical MACs, **preferred 1%**.

### 4.5 Pre-execution gate and post-refinement safety — the pivotal separation

This separation is the load-bearing structural claim, visualised in
`p24_pre_gate_vs_post_safety.png`.

| | Pre-execution gate | Post-refinement safety `S_omega` |
|---|---|---|
| Rule | `if U_hat_i > tau then EXECUTE else SKIP` | accept or reject the refinement output |
| When | **before** `R_psi` executes | **after** `R_psi` has executed |
| Saves compute? | **YES** | **NO** |
| Novelty | part of the residual | `CONTROLLED_CORE_EXTENSION`, closest to JFS |
| Mandated ablation | — | A7 (router, no post-safety) vs A8 (router + post-safety) |

`S_omega` must **NEVER** be presented as the compute-saving mechanism, because JFS already occupies
the post-hoc decision. `S_omega` inputs must be GT-free at deployment.

### 4.6 Fusion, conditioning, task handling

- Fusion primary rule: outside ROI retain `p_global`; inside ROI replace with `p_refined`.
  **No learned fusion in the primary design** — avoids confounding the benefit-routing hypothesis.
  Learned fusion is a future controlled ablation only.
- Task conditioning: **ONE** shared router, task/domain conditioning allowed. Separate per-domain
  routers are **forbidden** in the primary design (preserves the shared multi-domain contribution);
  they are later controlled ablations only.

## 5. Contracts

### 5.1 Paired refinement gain (`phase24_paired_refinement_gain_contract.json`)

```
DeltaDice_i = Dice(R_i, y_i) - Dice(G_i, y_i)
```

- Nature: a **supervised paired contrast**. During development both arms are fully observed.
- **Must not be described as** a causal treatment effect, a counterfactual effect, or an individual
  treatment effect.
- Why not causal: both potential outcomes are fully observed for every development image, because the
  system may simply run the refinement during development. There is no missing arm and therefore no
  identification problem. The refinement is also deterministic given
  `(x, frozen model, frozen ROI rule)` → Phase-23 outcome `PREFER_PAIRED_REFINEMENT_GAIN`.
- The CATE analogy may be stated **at most once**, with the clarification that the estimand is a
  deterministic paired contrast.
- Primary target: continuous `DeltaDice` (regression). Optional development labels: beneficial
  `>= +0.02`, harmful `<= -0.01`, neutral otherwise — **prospective**; any change must be justified
  before Phase 25 and never tuned on VAL.
- Uses GT for labels: yes. Uses GT for inputs: **no**. Computed only after refinement has run: yes.
  Used as a router input: **no**.

### 5.2 Resource utility (`phase24_resource_utility_contract.json`)

```
U_hat_i = Delta_hat_i - lambda * C_i
```

- `Delta_hat_i` = predicted Dice improvement from the router; `C_i` = explicit incremental resource
  cost of running the refinement; `lambda` = resource trade-off coefficient.
- **A single universal lambda is forbidden.** Pre-register a small *set* of lambda values with a
  fixed-budget sweep: **0% / 10% / 25% / 50% / 100%** (0% = global-only, 100% = always-refine);
  intermediate thresholds calibrated on **TRAIN development only**.
- Cost proxy: **normalized analytical incremental MACs**. Terminology kept strictly separate:
  `ANALYTICAL MACs` vs `MEASURED latency` / `MEASURED memory` / `MEASURED energy`. Analytical MACs is
  **not** latency and must never be described as CPU/mobile latency; device measurement belongs to
  Phase 34. Cost term required by Phase-23 constraint **C6**. Not measured in Phase 24.

### 5.3 Preservation (`phase24_preservation_contract.json`)

Principle: the global output must remain **available** until the final selection; **no destructive
replacement** may occur before the final decision.

| Outcome | Final output |
|---|---|
| `SKIP` | global |
| `EXECUTE_THEN_REJECT` | global |
| `EXECUTE_THEN_ACCEPT` | regional-fused |

Structural enforcement: the global probability map is retained in memory for the whole sample
lifetime; the regional candidate is stored separately and composed only at the final selection step.

**Non-inferiority test (frozen before Phase 25):** metric
`Delta = Dice(final routed system) - Dice(global reference)`; margin **0.005**; the claim is permitted
**only if** the lower confidence bound of `Delta > -0.005`. Per-domain reporting is **mandatory**;
the macro average may not hide domain-specific harm.

## 6. Data protocol (TRAIN-only) — `phase24_benefit_data_protocol.json`

**Critical leakage constraint:** benefit-router training labels may **never** be generated from the
existing Phase-22 VAL population. Only original TRAIN may be used.

| Population | Source | n | Role |
|---|---|---|---|
| Original TRAIN | `manifests/phase4_v3/train.csv` | **5832** | source of the two router splits (KUB 1978 / KVASIR 696 / ISIC 2556 / BUSI 602; grouped by `patient_id`, 319 groups) |
| `ROUTER_DEVELOPMENT` | 85% of original TRAIN | **≈4957** | cross-fitted gain labels + router fitting + threshold calibration |
| `ROUTER_HOLDOUT` | 15% of original TRAIN | **≈875** | clean out-of-sample routing evaluation |
| VAL (existing) | `manifests/phase4_v3/val.csv` | **808** | `SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK` |
| TEST | `manifests/phase4_v3/test.csv` | 1683 | **CLOSED** |

- Split: deterministic, domain-stratified, group-safe on `patient_id`, overlap 0, TRAIN-only, seed
  frozen in Phase 25 from a fixed constant.
- **`ROUTER_HOLDOUT`** is designated **before** any refiner-performance inspection, benefit-router
  fitting, feature selection, lambda selection or threshold fitting. In Phase 24 only `sample_ids`,
  `domain counts`, `group integrity`, `manifest sha` and `split seed` were inspected. **Outcomes read
  in Phase 24: 0.**
- The existing 808-case VAL is explicitly reclassified as `SECONDARY / CONTINUITY DEVELOPMENT
  BENCHMARK` — it is **not** router training data and **not** an untouched routing holdout. This is
  stated in every protocol artifact (`reports/tables/phase24_data_role_contract.csv`).

### 6.1 Out-of-fold 3-fold cross-fitting

Within `ROUTER_DEVELOPMENT`, 3 folds. For fold *k*: train `R_psi` on folds ≠ *k*, infer `R_psi` on
fold *k*, compute `DeltaDice_i = Dice(R_i, GT) - Dice(G_i, GT)` for fold-*k* samples. Output:
concatenated out-of-fold (OOF) paired-gain labels. Purpose: prevent refiner-overfit gain labels from
entering the router target — the refiner must be cross-fitted, never fit and evaluated on the same
samples. `executed_in_phase24: False`. Figure: `p24_crossfit_gain_label_generation.png`.

## 7. Hypotheses, comparators, metrics, statistics

### 7.1 Hypotheses (`HYPOTHESES_NOT_RESULTS`)

- **H1 (LOAD-BEARING):** a learned pre-execution GT-free predictor of paired refinement gain can
  allocate optional regional refinement more effectively than simple GT-free uncertainty/geometry
  proxies at equal refinement-activation budgets.
- **H2:** benefit-aware routing captures more positive gain per unit compute than random / entropy /
  margin / ROI-size routing.
- **H3:** post-refinement fallback reduces harmful replacement relative to always accepting an
  executed refinement.
- **H4:** a dedicated crop-trained refiner yields a more useful action distribution than the Phase-22
  diagnostic reuse of the full-field model.
- **H5:** benefit-aware routing produces a measurable accuracy–compute frontier.
- **H6:** learned paired refinement gain contains information beyond ordinary global uncertainty.

### 7.2 Comparators — `reports/tables/phase24_comparator_plan.csv` (11 rows, no ranking)

`C1 GLOBAL_ONLY` · `C2 ALWAYS_REFINE` · `C3 RANDOM_ROUTING` · `C4 ENTROPY_ROUTING` ·
`C5 MARGIN_ROUTING` · `C6 PREDICTED_ROI_SIZE_ROUTING` · **`C7 LEARNED_PAIRED_GAIN_ROUTING` (the
load-bearing comparator)** · `C8 +RESOURCE_COST` · `C9 +RESOURCE_COST+POST_SAFETY` ·
`C10 ORACLE_BENEFIT_ROUTING` (upper bound, uses GT, **not deployable**, never a result) ·
`C11 JFS_LIKE_POST_HOC_SELECTOR` (optional; if included it must record **full** refinement compute
because the expensive operation already occurred).

### 7.3 Metrics

- **Benefit prediction:** MAE, RMSE, Spearman, Pearson, ROC-AUC for useful-benefit detection, PR-AUC.
- **Routing:** precision@budget, benefit capture@budget, mean true `DeltaDice` among routed cases,
  harmful activation rate, missed-benefit rate, routing regret vs oracle.
- **Segmentation:** macro-domain Dice, per-domain Dice, IoU, existing standardized boundary metrics.
- **Compute:** activation fraction, incremental MACs, average total MACs, ratio vs global-only, ratio
  vs always-refine.
- **Preservation:** harmful replacement rate, fallback rate, per-domain degradation.

### 7.4 Statistics

**Paired bootstrap**, `n_boot = 2000`, `seed = 42`, domain-stratified for macro-domain metrics; report
point estimate, 95% CI, and paired p-value where appropriate. `test_used: False`.

## 8. Success / failure criteria — `reports/tables/phase24_success_failure_criteria.csv`

**Failures (F1–F5):** `REFINER_FAILURE`, `ROUTER_FAILURE`, `PRESERVATION_FAILURE`,
`RESOURCE_FAILURE`, `DOMAIN_COLLAPSE`.
**Successes (S1–S3):** `H1_SUPPORTED`, `PRESERVATION_SATISFIED`, `FRONTIER_MEASURED`.
All eight (5 failures + 3 successes) are frozen **before** Phase 25.

**Tiny-structure role:** tiny structures are **reporting-only** in this specification — they are a
stratification of the analysis, never a tuning target, never a routing input, and cannot be used to
select lambda or thresholds.

## 9. Ablations — `reports/tables/phase24_ablation_plan.csv` (13 rows)

Core `A0`–`A8` (global-only → always-refine → random → entropy → margin → ROI-size → learned
paired-gain → +resource cost → +post-safety), router ablations `R1`–`R3` (no deep global features;
no `task_id`; scalar-only features), and refiner ablation `F1` (refiner without the `p_global`
channel). `executed_in_phase24: False` for every row.

## 10. Prior-art differentiation — `reports/tables/phase24_prior_art_differentiation.csv` (12 rows)

A 14-column, **unranked** differentiation table. The closest analogue, `moon2024jfs` (JFS, ICIP 2025,
arXiv:2407.04519), shares the framing and a paired coarse-vs-refined comparison with revert-on-failure,
**but decides after the refinement has run, saves zero compute, and its decision rule is not a learned
regression.** The formal antecedent `russell1991metareasoning` defines *value of computation* as
expected benefit minus cost, decided before acting — our spec is a concrete learned instantiation of
that abstract principle inside a segmentation system, contributing no new formal machinery. No row
carries a novelty score; the table exists to expose differences, not to rank.

## 11. Design figures (§33) — `reports/figures/phase24_architecture_spec/`

All six carry the banner **"DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS"** and are declared in
`phase24_figure_manifest.json` with `contains_experimental_results: False` and
`contains_hypothetical_performance_curves: False`.

| Figure | Display name | SHA-256 (prefix) |
|---|---|---|
| `p24_full_system_architecture.png` | Full system architecture | `d152887addc1c0f3` |
| `p24_pre_gate_vs_post_safety.png` | Pre-execution gate vs post-refinement safety | `d4e37c91bce4fcb0` |
| `p24_train_router_holdout_flow.png` | TRAIN-only router development protocol | `470e8f58a459223c` |
| `p24_crossfit_gain_label_generation.png` | Out-of-fold paired-gain label generation | `f384894839aa4bcc` |
| `p24_resource_budget_evaluation.png` | Pre-registered fixed-budget evaluation grid | `044413d7193dc360` |
| `p24_novelty_boundary.png` | Novelty boundary | `566f7cc14f2ac886` |

## 12. Phase-25 module plan (PRE-REGISTERED, NOT STARTED) — `phase24_phase25_module_plan.json`

| id | Module | Depends on |
|---|---|---|
| 25A | Dedicated crop-trained regional refiner `R_psi` | — |
| 25B | GT-free feature extraction / ROI pipeline | — |
| 25C | Out-of-fold paired-gain label generation | 25A, 25B |
| 25D | Lightweight paired-gain benefit router `B_phi` | 25C |
| 25E | Resource-aware pre-execution gate + budget calibration | 25D |
| 25F | Post-refinement preservation selector + fusion | 25A |
| 25G | Integrated controlled development evaluation / freeze | 25E, 25F |

Ordering constraint: the router may only be fitted **after** out-of-fold gain labels exist (25C
precedes 25D). `no_module_started: true`.

## 13. Forbidden claims

`first-ever` · `first in the world` · `never done before` · `counterfactual causal effect` ·
`certified` · `guaranteed` · `novel value-of-computation` · `novel gating mechanism` ·
`novel CATE target` · `novel multi-domain segmentation` · `novel tiny-lesion segmentation` ·
`mobile ready` · `real-time` · `resource optimal` · `best method` · `performance preserving`
(until the frozen non-inferiority criterion is actually met).

**Current allowed wording:** *"We specify a benefit-aware refinement-routing system…"*
Level-2 wording may be used only after empirical support, and only for the exact integrated
contribution identified by Phase 23.

## 14. Artifact index (§36)

**Audits** — `phase24_entry_gate.json` (27/27), `phase24_method_naming_decision.json`,
`phase24_architecture_spec.json` (44 keys), `phase24_paired_refinement_gain_contract.json`,
`phase24_resource_utility_contract.json`, `phase24_preservation_contract.json`,
`phase24_novelty_boundary.json`, `phase24_benefit_data_protocol.json`,
`phase24_phase25_module_plan.json`, `phase24_no_execution_audit.json`,
`phase24_notebook_determinism.json`, `phase24_final_freeze.json`.

**Tables** — `phase24_module_spec.csv` (7×9), `phase24_router_input_contract.csv` (31×8),
`phase24_data_role_contract.csv` (5×8), `phase24_comparator_plan.csv` (11×7),
`phase24_ablation_plan.csv` (13×5), `phase24_success_failure_criteria.csv` (8×6),
`phase24_prior_art_differentiation.csv` (12×14).

**Figures** — `reports/figures/phase24_architecture_spec/` (6 PNG + manifest).

**Notebook** —
`notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec.ipynb`
(36 sections, all cells executed, 6 design figures embedded, 3× byte-identical).

**Report** — this document.

## 15. Non-modification guarantee

No predecessor science artifact was modified by Phase 24. Phase-21 `best.pt`, the Phase-22 protocol
and freeze, and the Phase-23 canonical notebook remain byte-identical to their bound SHAs. Phase-24
writes are additive. No `phase25_*` artifact exists.

## 16. Terminal state

```
PHASE24_NARROWED_BENEFIT_AWARE_REFINEMENT_SPEC_COMPLETE__PHASE25_ELIGIBLE_NOT_STARTED
```

On a fatal inconsistency the alternative terminal is
`PHASE24_NARROWED_SPEC_BLOCKED__REDESIGN_REQUIRED`. The success conditions are enumerated and
verified in `reports/audits/phase24_final_check.json`. **Phase 25 has NOT been started.**
