# TASKS — Live Phase Roadmap and Execution State

## Phase25E policy evaluation complete — current state (2026-10-01)

Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: **COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: **COMPLETE_FROZEN**. Phase25F post-safety specification v1.0 (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN** (execution **COMPLETE_CANONICAL**). Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30). **Phase25 = COMPLETE_CANONICAL**; Phase26 = **ELIGIBLE_NOT_STARTED**.

The normalized incremental action cost is exactly `3,230,662,656 / 31,551,740,928` (`1051648/10270749`, approximately `0.10239253242387678`) for available actions; unavailable actions cost zero and are FORCED_SKIP. Pre-gate router overhead is `36,160` Conv/Linear MACs, separate from action cost. All compute is **ANALYTICAL MAC LOWER BOUND**, never measured latency.

Lambdas `{0.00, 0.25, 0.50, 1.00}` and budgets `{0%, 10%, 25%, 50%, 100%}` are frozen. All 4,957 DEV rows are action-available; exact top-K counts are `{0, 495, 1239, 2478, 4957}`. Rank by score descending, sample_id ascending. Random priorities (PCG64 seed 42) and 45 label-blind memberships were frozen before outcomes. Under constant action cost, C7 and C8 have **identical membership at every fixed budget and lambda**; they are not independent evidence.

The 45 frozen OOF memberships were joined to the frozen Phase25C paired-gain outcomes on ROUTER_DEVELOPMENT only (4957). The statistics (domain-stratified group bootstrap, 2000 replicates, seed 42) and the final-router DEV thresholds were frozen **before** the outcome join. Result: under the frozen PRIMARY statistic (raw paired two-sided p), C7 **significantly beats every simple GT-free proxy on precision@budget at the 10% and 25% budgets**, the advantage shrinking to non-significance at 50% (Holm-Bonferroni retained only as a secondary sensitivity: 10%); preservation holds; a usable accuracy-compute frontier exists. H1 is scoped to the tight and medium budgets (10%/25%).

The frozen final benefit-router checkpoint was loaded once and run in a single outcome-blind forward pass over the 4,957 ROUTER_DEVELOPMENT feature rows (no global-model forward, no regional-refiner forward, no training); no lambda was selected; the gate was not calibrated for deployment beyond frozen DEV-score thresholds; C9 post-safety was not evaluated. ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39.

Executed scientific notebook: `notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb`; SHA-256 `b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797` (3× byte-identical; post-reconciliation rebuild superseding the archived pre-reconciliation build SHA `e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718`). Evidence: `reports/audits/phase25e_policy_evaluation_summary.json`, `reports/audits/phase25e_adjudication.json` (original closure), `reports/audits/phase25e_adjudication_reconciled.json` (PRIMARY adjudication, raw paired p), `reports/audits/phase25e_multiplicity_provenance_audit.json`, `reports/audits/phase25e_final_freeze.json`.

Terminal: `PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED`.

## Phase25F post-safety specification v1.0 — COMPLETE_FROZEN (2026-10-01)

Phase25F post-safety specification (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN**; Phase25F execution: **EXECUTION_ELIGIBLE_NOT_STARTED**. The first blocked Phase25F attempt (`PHASE25F_BLOCKED__POST_SAFETY_EXECUTION_SPEC_INCOMPLETE`; 54 blocking fields, 12 hard-stop conditions) is preserved verbatim as **BLOCKED_ATTEMPT_PROVENANCE** (no audit overwritten or deleted).

The repair prospectively froze the exact S_omega input vector (20-D = 16 numeric + 4 one-hot task), the leakage-safe OOF post-refinement source (Phase25C fold-specific `_tmp_refined_crop_prob_<DOMAIN>.npy`, provenance-proven and promoted to `data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy`), `BARRPostSafetyV1` (`Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)`, **1,217** trainable parameters, raw logit output), the training objective (`BCEWithLogitsLoss`, mean reduction, no class weighting / pos_weight / label smoothing), the reused Phase25D five-fold CV identity manifests (FIT / EARLY_STOP / OUTER_TARGET), FIT-only ddof=0 normalization of the 16 numeric features, the fixed ACCEPT/FALLBACK threshold (`sigmoid >= 0.50` / `logit >= 0.0`; distinct from the 0.30 ROI-proposal and 0.50 segmentation-output thresholds), the Phase25E SKIP interaction state machine, the final-refit rule (exact median of the five best epochs, seed 42, LAST_FIXED_EPOCH checkpoint), and A7/A8 ownership (Phase25F constructs the C9 artifact on ROUTER_DEVELOPMENT; Phase25G owns the integrated A7-vs-A8 / C8-vs-C9 evaluation).

All 73 specification fields are now complete; `blocking_fields = []` and `hard_stop_conditions_triggered = []`. **No model was constructed, no training ran, no forward pass occurred, no refinement or DeltaDice was regenerated, and no threshold was tuned.** ROUTER_HOLDOUT, VAL808 and TEST remain closed; Phase25G is NOT_STARTED.

Evidence: `reports/audits/phase25f_post_safety_spec_completion_v1_0.json`, `phase25f_oof_refinement_source_contract_v1_0.json`, `phase25f_oof_refinement_source_promotion.json`, `phase25f_feature_equation_contract_v1_0.json`, `phase25f_feature_cache_determinism.json`, `phase25f_target_contract_v1_0.json`, `phase25f_architecture_contract_v1_0.json`, `phase25f_training_contract_v1_0.json`, `phase25f_decision_threshold_contract_v1_0.json`, `phase25f_state_machine_contract_v1_0.json`, `phase25f_final_refit_contract_v1_0.json`, `phase25f_a7_a8_ownership_ruling_v1_0.json`, `phase25f_spec_repair_no_execution.json`, `phase25f_spec_repair_final_check.json`.

Terminal: `PHASE25F_POST_SAFETY_SPEC_V1_0_COMPLETE__OOF_FEATURE_SOURCE_ARCHITECTURE_TRAINING_THRESHOLD_AND_OWNERSHIP_FROZEN__PHASE25F_EXECUTION_ELIGIBLE_NOT_STARTED`.

## Phase25F post-safety execution — COMPLETE_CANONICAL (2026-10-01)

`BARRPostSafetyV1` (`Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)`, **1,217** trainable parameters, raw logit) was constructed and trained for exactly **five frozen CV logical runs** (seeds 54000–54004; reused Phase25D FIT/EARLY_STOP/OUTER_TARGET manifests) plus **one all-DEV final refit** (`FINAL_SAFETY_EPOCHS = 23` = exact integer median of the five selected epochs; seed 42; LAST_FIXED_EPOCH checkpoint). **4,957 OOF safety logits / probabilities / decisions** were produced on ROUTER_DEVELOPMENT and are bit-reproducible (3x replay, max abs difference 0.0). The **C9 post-safety state/decision artifact** (20 frozen C8 lambda×budget policies × 4,957 rows) was constructed. Classifier-level metrics describe S_omega itself at the fixed 0.50 threshold; they are **not** segmentation results and **not** a preservation proof.

**Scope**: no A7-vs-A8 segmentation comparison, no C8-vs-C9 system-performance comparison, no preservation adjudication, no new budget/lambda selection, no threshold tuning. ROUTER_HOLDOUT, VAL808 and TEST were never read; TEST stays locked until Phase39. Phase25G owns the integrated controlled development evaluation and is **ELIGIBLE_NOT_STARTED**.

Executed notebook: `notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb` (41 sections; 9 figures; 3x byte-identical SHA-256 `1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90`).

Terminal: `PHASE25F_POST_SAFETY_EXECUTION_COMPLETE__OOF_SAFETY_PREDICTIONS_FINAL_CHECKPOINT_AND_C9_ARTIFACTS_FROZEN__PHASE25G_ELIGIBLE_NOT_STARTED`.

## Phase25G specification v1.1 — COMPLETE_FROZEN (2026-10-01)

Phase25F execution: **COMPLETE_CANONICAL**. Phase25G specification v1.1 (`ra_medfilm_barr_integrated_evaluation_v1_0`): **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only).

**SUPERVISOR RULING (G1)**: ROUTER_HOLDOUT phase ownership = **Phase30** (Final Development Validation Benchmark), one-shot clean out-of-sample development validation. ROUTER_HOLDOUT = **RESERVED_UNOPENED_FOR_PHASE30**; it MUST NOT be opened by Phase25G, Phase26, Phase27, Phase28 or Phase29. Phase30 is the first eligible owner, subject to a separate pre-execution one-shot protocol freeze. The ruling is additive / prospective / pre-outcome (`science_changed = false`) and resolves the single Phase25G governance blocker.

Phase25G population = **ROUTER_DEVELOPMENT (4957)**; evaluation sources: Phase25C OOF delta_dice, Phase25E frozen prospective C8 memberships, Phase25F OOF S_omega probabilities/decisions and the Phase25F C9 manifest (no new model inference). The repaired completeness matrix (`phase25g_specification_completeness_v1_1.csv`) has 28 rows, `blocking_fields = []`, `hard_stop_conditions = []`; the five conditional holdout-execution fields are marked `NOT_APPLICABLE_TO_PHASE25G__HOLDOUT_RESERVED_FOR_PHASE30`.

**Blocked provenance preserved**: the pre-ruling state `PHASE25G_BLOCKED__ONE_SHOT_HOLDOUT_OWNERSHIP_UNRESOLVED` (spec `INCOMPLETE__HOLDOUT_OWNERSHIP_UNRESOLVED`, blocking field `ROUTER_HOLDOUT ownership`) and its artifacts remain verbatim (no audit or table overwritten).

Current state: **Phase25 = COMPLETE_CANONICAL (25A-25G)**; Phase26 = ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; Phase30 = NOT_STARTED; VAL808 = UNOPENED / continuity benchmark; TEST = LOCKED UNTIL PHASE39.

Evidence: `reports/audits/phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json`, `phase25g_holdout_reservation_for_phase30.json`, `phase25g_specification_repair_addendum.json`, `phase25g_specification_final_check_v1_1.json`, `phase25g_specification_governance_v1_1.json`, `phase25g_holdout_ownership_repair_final_check.json`, `phase30_router_holdout_deferred_contract_stub.json`.

Terminal: `PHASE25G_SPEC_V1_1_COMPLETE__ROUTER_HOLDOUT_RESERVED_FOR_PHASE30__DEV_ONLY_INTEGRATED_EVALUATION_FROZEN__PHASE25G_EXECUTION_ELIGIBLE_NOT_STARTED`.

## Phase25G integrated controlled development evaluation — COMPLETE_CANONICAL (2026-10-01)

Phase25G (`CANONICAL_PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION`, spec `ra_medfilm_barr_integrated_evaluation_v1_0`, repair v1.1) evaluated **A7 (C8: learned-gain + resource gate, always accept)** against **A8 (C9: same membership + S_omega post-safety)** over the complete frozen 20-policy grid (lambda {0.00,0.25,0.50,1.00} x budget {0,10,25,50,100%}) on **ROUTER_DEVELOPMENT (n=4957)**, reconstructed entirely from the frozen Phase25C OOF `delta_dice`, the Phase25E prospective C8 memberships and the Phase25F C9 decision manifest.

**No model was constructed, no training ran, no forward pass occurred, no refinement or DeltaDice was regenerated, and no threshold was tuned.** Evidence class = `CONTROLLED_META_LEVEL_OOF_DEVELOPMENT_EVIDENCE`.

**Lambda redundancy**: because the action cost is constant, C8 membership is structurally identical across lambda for a fixed budget — the four lambda replicas are **DUPLICATE MEMBERSHIP**, so only **5 unique membership sets** carry inferential weight.

**Results (5 unique budgets)**: post-safety (A8) weakly improves the macro-domain Dice delta at every informative budget and **reduces harmful replacements** (delta_dice < 0) monotonically with budget; preservation holds for every frozen policy (macro-domain lower 95% CI > -0.005). H3 is reported **descriptively only** — no numeric success threshold was pre-registered (`H3_NUMERICAL_SUCCESS_THRESHOLD_NOT_PRE_REGISTERED = true`). S_omega adds an analytical `a * 1168` MAC increment and **saves no compute**.

**No policy selected**: `lambda_selected = false`, `best_budget_selected = false`, `policy_selected = false`. R1/R2/R3/F1 belong to Phase28; C11 = `C11_NOT_EXECUTED`.

Notebook: `notebooks/phasewise/phase_25g_controlled_validation/phase25g_integrated_controlled_evaluation.ipynb` (SHA-256 `5f6b6642fe013d9ad69cac8a0e319d5f86362d8457febdab42fde6cbe14c4487`, 41 sections, 9 figures, 3x byte-identical).

Evidence: `reports/audits/phase25g_final_freeze.json`, `phase25g_reconstruction_integrity.json`, `phase25g_a7_a8_identity_control_audit.json`, `phase25g_preservation_adjudication.json`, `phase25g_h3_result.json`, `phase25g_compute_accounting_audit.json`, `phase25g_notebook_determinism.json`, `reports/tables/phase25g_c8_c9_comparison.csv`.

Current state: **Phase25 = COMPLETE_CANONICAL (25A-25G)**; Phase26 = ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; Phase30 = NOT_STARTED; VAL808 = UNOPENED; TEST = LOCKED UNTIL PHASE39.

Terminal: `PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION_COMPLETE__A7_A8_C8_C9_PRESERVATION_AND_H3_FROZEN__PHASE25_COMPLETE__PHASE26_ELIGIBLE_NOT_STARTED`.





**Purpose:** The live 00–40 roadmap with statuses, current subpart state, deferred debt, the
next-step procedure, and the definition of done. See [PRD.md](PRD.md) for goals,
[ARCHITECTURE.md](ARCHITECTURE.md) for structure, [RULES.md](RULES.md) for constraints,
[DESIGN.md](DESIGN.md) for results, [MEMORY.md](MEMORY.md) for handoff.

**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)
**Strategy revision:** **SR-1** — status **ADOPTED**; method name **RA-MedFiLM-BARR**

> **CURRENT FOCUS (2026-10-01):** Phase 24 v1.2 router feature specification **COMPLETE**.
> Phase 25A **COMPLETE canonical**. Phase 25B **COMPLETE canonical** (202-D GT-free pre-refinement
> feature cache frozen, 4957 × 202, `data_cache/phase25b_barr_pre_refinement_features_v1_2/`).
> **Phase 25C `COMPLETE canonical`** — the canonical `ROUTER_DEVELOPMENT` OOF paired refinement-gain
> label table is frozen (4957 rows, `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/`).
> **Phase 25D `COMPLETE canonical`** — 5 CV folds trained (best epochs 37/34/139/199/80),
> final refit 80 epochs, 4957 OOF Delta_hat predictions frozen, reviewer notebook 3× deterministic.
> Blocked attempt preserved. Phase **25E specification** is **COMPLETE_FROZEN**; **scientific policy evaluation** is **COMPLETE_FROZEN** (45 frozen OOF memberships joined to Phase25C outcomes on DEV; bootstrap, frontier and adjudication frozen). **Phase 25F post-safety specification v1.0 COMPLETE_FROZEN; execution EXECUTION_ELIGIBLE_NOT_STARTED.** **TEST CLOSED until Phase 39.**
> Sections below §3 retain historical Phase-13-era detail as provenance.

**Canonical source paths:**
- `PROJECT_MASTER_PLAN.md` §7 — canonical 41-phase progression
- `reports/audits/antigravity_current_state.json` — live status fields
- `reports/tables/phase05_clean_rerun_scope.csv` — clean-v3 rerun scope
- `notebooks/phasewise/phase_NN_*/` — one directory per phase
- `reports/audits/phase11_*` — Phase-11 audits

> **Status legend:** `COMPLETE` · `PARTIAL` (subpart-done) · `NOT_STARTED` ·
> `COMPLETE (v2 evidence)` = historical only · `DEFERRED_HISTORICAL` ·
> `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` (conditional on the gate).

---

## 1. Two-dimensional status model

Every phase has **two** independent statuses, never collapsed:

1. **Historical v2 status** — what was done under `phase4_v2`.
2. **Clean-v3 status** — what has been done under `phase4_v3`.

Phases 06–15 were executed historically under v2. **Clean-v3: Phases 05–12 are COMPLETE;
Phase 13 Parts 1A, 1A-R1 and 1A-R2 (protocol/definition) are COMPLETE and the protocol is
`SUPERVISOR_FROZEN_R2`.**

## 2. Roadmap table (00 → 40)

### Stage A — KUB Regional & Tiny-Object Development (00–18)

| Phase | Title | Historical v2 | Clean-v3 / current |
|---|---|---|---|
| 00 | Governance & Protocols | COMPLETE | n/a (governance) |
| 01 | Project Initialization & Layout | COMPLETE | n/a |
| 02 | Environment & CUDA Verification | COMPLETE | n/a |
| 03 | Dataset Discovery & Cataloging | COMPLETE | n/a |
| 04 | Manifest & Data Splits | COMPLETE (v2) | superseded by 05 |
| 05 | Forensic Leakage Audit + v3 Promotion | n/a | **COMPLETE** (Part 1E, gate PASS) |
| 06 | KUB Characterization | COMPLETE | **COMPLETE** (clean-v3, Part 1A-R1) |
| 07 | Object Size Taxonomy & Quartiles | COMPLETE (`kub_size_v1`) | **COMPLETE** (`kub_size_clean_v3_v1` FROZEN) |
| 08 | Baseline Infrastructure & Factories | COMPLETE | **COMPLETE** (Part 1A + 1B; no training) |
| 09 | KUB UNet Baseline Training | COMPLETE (contaminated) | **COMPLETE** (best ep 44, Dice 0.740613) |
| 10 | Baseline Comparison (UNet / AttnUNet / UNet++ / DeepLabV3+) | COMPLETE (contaminated) | **COMPLETE** (1A + 1B + 1C + final four-model comparison) |
| 11 | Baseline Failure Analysis | COMPLETE (contaminated) | **COMPLETE** (Part 1A protocol freeze + Part 1B four-model failure analysis) |
| 12 | **Oracle Regional-Resolution Upper Bound** | COMPLETE (contaminated) | **COMPLETE / PASS** (1A protocol freeze · 1B four-model oracle inference · 1C paired analysis · 1D supervisor conclusion) |
| 13 | **GT-Free Region Proposal / Localization** | COMPLETE (Stages incl. 4D) | **Parts 1A / 1A-R1 / 1A-R2 / 1B-R0 / 1B-R0-R1 COMPLETE** · protocol **`R2 + R2A_LOSS_BINDING`** · Part 1B **`EXECUTION_BINDING_RESOLVED_AWAITING_TRAINING_REAUTHORIZATION`** |
| — | **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** | n/a | **REQUIRED · NOT_DECIDED** (decided after Phase 13) |
| 14 | Regional Refiner Component Development | COMPLETE (FROZEN DIAGNOSTIC, gate NOT passed) | `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` |
| 15 | Regional Objective / Loss Study | PROTOCOL FROZEN (L1/L2/L3 not trained) | `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` |
| 16 | Global–Regional Fusion / Routing | NOT_STARTED | `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` |
| 17 | Regional Mechanism Ablation | NOT_STARTED | `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` |
| 18 | Regional Mechanism Freeze (Spec v1) | NOT_STARTED | `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` |

> **Phases 14–18 are CONDITIONAL** on the post-Phase-13 gate and **MUST NOT** proceed
> automatically ([RULES.md](RULES.md) §11C). They are **not** an automatic standalone KUB
> final product; they develop a **reusable** regional mechanism for later integration.
> Future multi-domain metadata must be classified `CONDITIONING_ALLOWED` /
> `REPORTING_ONLY` / `FORBIDDEN_AS_INPUT`; Kidney/Bladder/Ureteric stay `REPORTING_ONLY`.

### Stage B — Multi-Domain Harmonization & RA-MedFiLM (19–26)

> **Updated 2026-09-30** — actual roadmap state.

| Phase | Title | Status |
|---|---|---|
| 19 | Multi-Domain Dataset Harmonization | **COMPLETE** |
| 20 | Shared Multi-Domain Global Baseline (no FiLM, no regional) | **COMPLETE** (20 / 20B) |
| 21 | Global MedFiLM Reference (FiLM conditioning, no regional) | **COMPLETE** (3,523,001 params; ckpt `286689fd…`) |
| 22 | Multi-Domain Scale / Regional Gap Analysis | **COMPLETE** (benefit strongly heterogeneous; always-on regional HURTS in aggregate) |
| 23 | Literature & Methodological Novelty Audit | **COMPLETE** (max novelty = Level 2) |
| 24 | RA-MedFiLM Architecture Specification | **COMPLETE** |
| 24 v1.1 | Exact-spec freeze | **COMPLETE** (historical; notebook `612d7170…`) |
| **24 v1.2** | **Router feature specification** | **COMPLETE** (RF-1/RF-2/RF-3 + **D1** + **D2** adjudicated) |
| **25A** | Dedicated crop-trained regional refiner | **COMPLETE canonical** (1,276,401 params; 3.230663 GMAC; ckpt `6d28608a…`) |
| 25A (ROI-0.50) | Superseded first Phase-25A run | **NONCANONICAL_PROTOCOL_DEVIATION** / preserved only |
| **25B** | GT-free pre-refinement feature extraction | **COMPLETE canonical** (202-D cache frozen; 4957 × 202; notebook `phase25b_gt_free_pre_refinement_features.ipynb`) |
| 25C | OOF paired-refinement-gain labels | **COMPLETE canonical** (4957 OOF labels; `phase25c_oof_paired_gain_labels.csv` `fd6ca32c…`; notebook `564105ea…`) |
| 25D | Benefit router (`B_phi`) training | **COMPLETE canonical** (5 CV folds + final refit; 4957 OOF predictions; notebook `phase25d_benefit_router.ipynb`) |
| 25E | Resource-aware pre-execution gate | Specification **COMPLETE_FROZEN**; scientific policy evaluation **COMPLETE_FROZEN** |
| 25F | Post-safety + fusion | Specification **COMPLETE_FROZEN**; execution **EXECUTION_ELIGIBLE_NOT_STARTED** |
| 25G | Controlled validation | **NOT_STARTED** |
| 26 | Full four-domain RA-MedFiLM-BARR training | NOT_STARTED |

> **Phase 25B is COMPLETE.** The canonical 202-D GT-free pre-refinement feature cache is frozen
> at `data_cache/phase25b_barr_pre_refinement_features_v1_2/` (4957 × 202, float32, no NaN/Inf),
> with a 3× byte-identical reviewer notebook and all gates passing. At Phase25B completion, no router had yet been trained;
> no refiner forward was performed, and no holdout/VAL/TEST row was touched. **TEST is locked until Phase 39.**

> **Phase 25C is COMPLETE canonical.** The `ROUTER_DEVELOPMENT` OOF paired refinement-gain label
> table is frozen at `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/`
> (`phase25c_oof_paired_gain_labels.csv`, 4957 rows, SHA `fd6ca32c…`). Every label is produced by the
> **fold-specific** ROI-0.30 regional refiner whose outer target fold contains the sample (cross-fit:
> outer ∩ FIT = outer ∩ EARLY_STOP = 0 for all three folds). `global_model_forward_passes = 0` — the
> frozen Phase-25B global cache was reused, never re-run. Labels are **gain supervision only**: Phase25C itself did not train the
> router, no 16-D task embedding was trained, and no holdout/VAL/TEST row was touched.
>
> **Interpretation discipline (Phase 25C).** Phase25C shows **strongly heterogeneous paired
> refinement gain**. Most samples are neutral under the pre-registered thresholds, while both
> beneficial and harmful cases exist. This heterogeneity motivates benefit-aware selective routing.
> Aggregate behaviour of earlier regional procedures belongs to prior Phase22 evidence and must not be
> conflated with the Phase25C OOF dedicated-refiner result.

### Stage C — Rigor, Ablation, Reproducibility, Clinical Evidence (27–37)

| Phase | Title | Status |
|---|---|---|
| 27 | Multi-Domain Performance Preservation Audit | NOT_STARTED |
| 28 | Full Architecture Ablation Matrix | NOT_STARTED |
| 29 | Three-Seed Deterministic Reproducibility Study | NOT_STARTED |
| 30 | Final Development Validation Benchmark | NOT_STARTED |
| 31 | Statistical Significance & Hypothesis Testing | NOT_STARTED |
| 32 | External Dataset & Domain-Shift Evaluation | NOT_STARTED |
| 33 | Final System Failure & Boundary Error Analysis | NOT_STARTED |
| 34 | Computational Efficiency & Conditional-Computation Profiling | NOT_STARTED |
| 35 | Feature Attribution & Visual Interpretability (FiLM γ/β, proposal maps, routing) | NOT_STARTED |
| 36 | Robustness & Image Perturbation Analysis (incl. region/proposal perturbation) | NOT_STARTED |
| 37 | Comprehensive Visual & Tabular Evidence Consolidation | NOT_STARTED |

### Stage D — Freeze, Test, Publication (38–40)

| Phase | Title | Status |
|---|---|---|
| 38 | Manuscript Protocol & Checkpoint Freeze | NOT_STARTED |
| 39 | **Final Untouched Test Cohort Evaluation** | NOT_STARTED — **the only TEST phase** |
| 40 | Publication Package & Reproducibility Audit | NOT_STARTED |

## 3. Current focus — Phase 24 v1.2 CLOSED · Phase 25B COMPLETE · Phase 25C COMPLETE · Phase25D COMPLETE · Phase25E COMPLETE_FROZEN

| Item | Status | Key evidence |
|---|---|---|
| Phase 21 Global MedFiLM | **COMPLETE** | checkpoint `286689fd…` |
| Phase 22 regional gap | **COMPLETE** | benefit heterogeneous; always-on hurts |
| Phase 23 novelty audit | **COMPLETE** | max novelty Level 2 |
| Phase 24 v1.1 exact-spec freeze | **COMPLETE** (historical) | notebook `612d7170…` |
| Phase 24 v1.2 router feature spec | **COMPLETE** | `phase24_v1_2_feature_spec_final_check.json` (all PASS) |
| D1 `predicted_roi_area_fraction` | **RESOLVED (C3)** | `phase24_predicted_roi_area_fraction_adjudication.json` |
| D2 router parameter count | **RESOLVED** (36,801 total / 36,353 linear core) | `phase24_router_parameter_count_adjudication.json` |
| Phase 25A canonical refiner | **COMPLETE canonical** | notebook `fd2bab01…`; ckpt `6d28608a…` |
| Phase 25A ROI-0.50 run | **NONCANONICAL_PROTOCOL_DEVIATION** | `phase25a_roi050_supersession.json` |
| Phase 25B blocked attempt | **BLOCKED_ATTEMPT_PROVENANCE** | `phase25b_blocked_attempt_final_freeze.json` |
| **Phase 25B** | **COMPLETE canonical** | `phase25b_final_freeze.json` → `PHASE25B_GT_FREE_PRE_REFINEMENT_FEATURES_COMPLETE__202D_CANONICAL_FEATURE_CACHE_FROZEN__PHASE25C_ELIGIBLE_NOT_STARTED` |
| Phase 25B global equivalence | **BIT-IDENTICAL** (max_abs = 0.0) | `phase25b_global_forward_equivalence.json` |
| Phase 25B determinism | **PASS** | `phase25b_feature_determinism.json` |
| **Phase 25C** | **COMPLETE canonical** | `phase25c_final_freeze.json` → `PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED` |
| Phase 25C cross-fit leakage | **CLEAN** (all outer∩fit = outer∩es = 0) | `phase25c_crossfit_leakage_audit.json` |
| Phase 25C notebook | **3× byte-identical** `564105ea…` (8/8 PNG valid) | `phase25c_notebook_determinism.json` / `phase25c_notebook_visual_integrity.json` |
| Phase 25C scope guard | **PASS** — router/task-embedding untouched | `phase25c_scope_guard.json` |
| Phase 25D | **COMPLETE_CANONICAL / TRAINED / FROZEN** — includes learned 16-D task embedding | `phase25d_final_freeze.json` + `phase25d_final_freeze_notebook_compliance_addendum.json`; notebook `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63`; final checkpoint `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b`; OOF `837be08e569053676b71d1ab216ff604184b2b61df567cca45e6f8a5546d4441`; `PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN__PHASE25E_ELIGIBLE_NOT_STARTED` |
| Phase25E specification | **COMPLETE_FROZEN** | `phase25e_spec_final_check.json`; notebook SHA `a431b3604021c0f4ffaaa6153302d674a38167b1792ab55d09a58a8ad2a5c41c` |
| Phase25E scientific policy evaluation | **COMPLETE_FROZEN** | `phase25e_final_freeze.json`; 45 frozen OOF memberships joined to Phase25C outcomes on DEV; bootstrap (2000, seed 42), frontier and adjudication frozen (PRIMARY adjudication reconciled: raw paired p; Holm retained as a secondary sensitivity); notebook `b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797` |
| TEST | **CLOSED until Phase 39** | `test_reads = 0` |

### Historical (retained as provenance — Phase-13 era)

| Item | Status | Key evidence |
|---|---|---|
| Phase 11 Part 1A / 1B | **COMPLETE** | `aaf1d86e…` / `4c78815d…` |
| Phase 12 Part 1A | **COMPLETE** | protocol freeze notebook `c226ea0f…` |
| Phase 12 Part 1B | **COMPLETE** | four-model oracle inference notebook `5848728526…` |
| Phase 12 Part 1C | **COMPLETE** | paired mechanism analysis notebook `7ebad54f…` |
| Phase 12 Part 1D | **COMPLETE** | supervisor conclusion + closure |
| Oracle mechanism value | **SUPPORTED_DESCRIPTIVE_EVIDENCE** | 103 FULL_FIELD cases · 152 native components · 4 models |
| **Phase 13 Part 1A** | **COMPLETE** | reconstruction + candidate audit; notebook `68f787e1…` |
| **Phase 13 Part 1A-R1** | **COMPLETE** | supervisor freeze amendment; notebook `6a08d6bd…` |
| **Phase 13 Part 1A-R2** | **COMPLETE** | checkpoint-selection provenance correction; notebook `47ff06a1…` |
| Phase 13 protocol (current) | **`R2 + R2A_LOSS_BINDING`** | base `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` `ab451e03…` (unedited) + amendment `reports/audits/phase13_clean_v3_localizer_loss_binding_r2a.json` `f3aececf…` |
| Phase 13 protocol (R2 base, still frozen) | **`SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING`** | `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` `ab451e03…` · SILENT on loss (amended by R2A, not superseded) |
| Phase 13 protocol (R1, superseded) | **`SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION`** | `…frozen.json` `999144bb…` — preserved for provenance |
| Phase 13 Part 1B | **`EXECUTION_BINDING_RESOLVED_AWAITING_TRAINING_REAUTHORIZATION`** — **not executed** | binding `…_execution_binding_resolved.json` · validation `…_validation_resolved.json` (`PASS`); prior `CHECK_REQUIRED` gate record `phase13_clean_v3_localizer_part1b_check_required.json` `7a2206b1…` preserved |
| Regional-integration gate | **NOT_DECIDED** | decided only after Phase 13 |
| Regional mechanism promoted | **NO** | — |
| Reference model selected | **NO** | none (all four in scope) |

### Phase-13 Part-1A reconstruction outcome

- **Historical Phase-13/13B localizer ran under `phase4_v2`** — VAL FULL_FIELD **106 images /
  156 components** (Tiny 73 / Small 29 / Medium 36 / Large 18). The frozen Stage-4D metrics
  (Tiny `53/73`, overall `100/156`) belong to that population and **must not** be compared with
  clean-v3 numbers as if the splits matched.
- **Authoritative historical localizer:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`,
  best epoch **73 / 88**, checkpoint SHA `ece906df…`; selected proposal config
  threshold `0.10` / margin `0.20` / top_k `5` / nms `0.30`. All nine handoff claims **VERIFIED**.
- **Clean-v3 population (recomputed, TEST never read):** TRAIN FULL_FIELD **770 / 1161**,
  VAL FULL_FIELD **103 / 152** (Tiny 72 / Small 28 / Medium 36 / Large 16). VAL 152
  independently reproduces the Phase-12 clean-v3 oracle population.
- **`HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH` — VERIFIED.** The historical
  Phase-14 regional refiner was *trained* on GT-derived + perturbed + background-negative crops
  (Option A3: 1162 + 2324 + 1542 = 5028/epoch) but *evaluated* on Stage-4D predicted proposals.
  Its Step-3 failure (`D_p` 0.383905 vs `D_g` 0.652776; 5.43 FP components/image vs 0.37) is
  therefore **not** a clean measurement of predicted-proposal regional refinement.
- **Verified latent defect:** `src/inference/learned_roi.predict_localizer` builds
  `KUBLocalizer` **without** `heatmap_resolution=128`, so the Stage-4D checkpoint's parameter-free
  downsample is silently dropped and a 512-space heatmap is returned. Historical frozen numbers
  are unaffected (the 13B notebooks used the dataset/evaluator path).
- **Ambiguity flagged:** `phase13b_stage4d_design_audit.json` labels Stage-4C numbers as
  `clean_v3_results` although the denominator was 156 (v2). Most plausibly refers to the
  clean-v3 *architecture*. Supervisor confirmation required before reuse.
- **Artifact gap:** `experiments/…_v1/val_search_epoch079.csv` is absent (87 of 88 search dumps);
  `history.csv` has 88 contiguous epochs.

> **Phase-13 Part-1A governance:** localizer training **0** · localizer inference **0** ·
> proposals generated **0** · TEST reads **0** · Phase 14 not executed · no winner, no reference
> model, gate **NOT_DECIDED**.

### Phase-13 Part-1A-R1 — supervisor freeze amendment

| Item | Frozen value |
|---|---|
| Protocol status (R1) | **`SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION`** (preserved for provenance) |
| Frozen artifact (R1) | `reports/audits/phase13_clean_v3_localizer_protocol_frozen.json` `999144bb…` · `.md` `f62a562a…` |
| Amendment notebook | `phase13_clean_v3_localizer_supervisor_freeze_amendment.ipynb` `6a08d6bd…` (35 cells, 19 code, 0 unexecuted, 0 errors) |
| Accepted Part-1A notebook | `68f787e1…` — **UNCHANGED** (verified) |
| clean-v3 hard-Tiny set | **15 components** · `phase13_clean_v3_hard_tiny_replication_set.csv` `2f9828d7…` |
| clean-v3 global-empty set | **5 images** · `phase13_clean_v3_global_empty_replication_set.csv` `a0b332ca…` |
| Hard-set anchor | **UNet++ = `HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY`** (not winner / best / reference / final) |
| Heatmap contract | input 512×512 → output **128×128**, `heatmap_resolution=128` always explicit, fail-loud shape assertions |
| Frozen proposal config | threshold **0.10** · margin **0.20** · top_k **5** · nms_iou **0.30** |
| clean-v3 primary grid search | **DISABLED** |
| Historical 20-grid | `DEFERRED_SECONDARY_SENSITIVITY_ONLY` |
| Checkpoint selection (R1) | fixed-config historical lexicographic score (**8 terms**) — **SUPERSEDED** by R2 |
| Predicted-proposal training crops in Phase 13 | **NO** |
| Phase-14 distribution-match requirement | `DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS` |
| Downstream predicted-region primary | `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` (margin **0.20**, not the Phase-12 oracle 0.25) |
| Retention interpretation | `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION` |
| Unauthorized material differences | **0** |

**Hard-set definitions (reproduced, not substituted).** `hard_tiny` = TINY native components
(`kub_size_clean_v3_v1`) whose clean-v3 **UNet++** global prediction misses them, where
`global_detected` = ≥ 1 native-space pixel of the 8-connected GT component has `GLOBAL_NATIVE`
probability ≥ 0.5 (executing definition, `phase12_oracle_inference.py` line 459).
`global_empty_image` = FULL_FIELD images whose clean-v3 UNet++ global prediction is empty
(`prediction_empty == true`), cross-validated between the frozen Phase-11 and Phase-12 tables
(identical sets). Counts need **not** equal the historical v2 counts (16 / 7).
These replication cohorts may feed the historical-style checkpoint metric but **must not**
replace the architecture-independent gate cohorts (`Phase-11 ALL_FOUR_LOW`, Phase-11 hard
cohort, Phase-11 disagreement cohort, `Phase-12 FULL_FIELD 103`).

> **Checkpoint-selection provenance (RESOLVED by R2).** Verification of
> `scripts/training/train_phase13b_localizer.py` line 164 established that the historical
> **executing** score was a **4-term** tuple
> `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` — it did **not**
> include `hard_tiny_recovered90`, `global_empty_images_covered90` or
> `multi_component_recall90`, although those were logged into `history.csv`. `PHASE13B.md`
> documents an 8-term protocol and the Stage-3 correction a 3-term one. R1 initially froze the
> 8-term extension; **R2 corrected the primary rule to the executing 4-term tuple** (executing
> source is higher-authority evidence than prose, and the correction minimises v2→v3 drift).
> The R1 8-term tuple is `SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION` and preserved as
> provenance.

> **Phase-13 Part-1A-R1 governance:** training **0** · optimizer steps **0** · forward passes
> **0** · localizer inference **0** · predicted-region inference **0** · proposals **0** ·
> clean-v3 grid search **not run** · TEST reads **0** · Phase 14 **not started** · historical
> artifacts **not modified**.

### Phase-13 Part-1A-R2 — checkpoint-selection provenance correction

| Item | Frozen value |
|---|---|
| Protocol status (current) | **`SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING`** |
| R2 frozen artifact | `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` `ab451e03…` · `.md` `b9bad4e5…` |
| R2 notebook | `phase13_clean_v3_localizer_checkpoint_selection_r2.ipynb` `47ff06a1…` (29 cells, 17 code, 0 unexecuted, 0 errors) |
| Additive R1→R2 diff | `reports/tables/phase13_r1_to_r2_protocol_diff.csv` `637bdffa…` |
| **Primary checkpoint selection** | **4-term executing historical tuple** at the fixed proposal configuration |
| Label | `EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION` |
| Tuple | `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` |
| Comparison / ties / patience | strict lexicographic `>` · ties = bad epoch · patience **15** |
| Checkpoint save | `best.pt` only on strict tuple improvement; `latest.pt` every completed epoch |
| Checkpoint metadata | must store the complete tuple **and** the tuple term names |
| R1 8-term tuple | `SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION` (provenance preserved) |
| Hard-set / diagnostic role | **`SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM`** |
| R1→R2 material differences | **1** (authorized) · unauthorized **0** |

**Diagnostics retained, excluded from primary selection:** `hard_tiny_recovered90`,
`global_empty_images_covered90`, `multi_component_recall90`, `mean_proposals_per_image` — each
labelled `SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM`. `mean_proposals_per_image` appeared in the
R1 8-term extension but not in the executing 4-tuple; it is a diagnostic only.

**Hard sets (unchanged, now secondary diagnostic cohorts):** hard-Tiny **15** `2f9828d7…` ·
global-empty **5** `a0b332ca…` · anchor UNet++ =
`HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY` · role
`PRE_FROZEN_SECONDARY_DIAGNOSTIC_COHORT` · **does not** select the primary checkpoint · useful
for localization analysis, difficult-case analysis and historical comparison · **must not**
replace the architecture-independent gate cohorts.

**Unchanged by R2** (proven by key-level comparison of the R1 vs R2 frozen JSON): proposal
config `0.10 / 0.20 / 5 / 0.30`, primary grid search `DISABLED`, historical 20-grid
`DEFERRED_SECONDARY_SENSITIVITY_ONLY`, heatmap 512→128 contract, architecture, target
generation/sigma, loss and coefficients, optimizer, LR, weight decay, scheduler, batch/AMP,
seed, augmentation, max epochs, patience, FULL_FIELD-only population and TRAIN/VAL membership,
downstream `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` composition, retention metric and gate
governance.

> **Phase-13 Part-1A-R2 governance:** training **0** · optimizer steps **0** · forward passes
> **0** · localizer inference **0** · predicted-region inference **0** · proposals **0** ·
> clean-v3 grid search **not run** · TEST reads **0** · Phase 14 **not started** · R1 and
> historical artifacts **not modified**.

### Phase-13 Part 1B — AUTHORIZED, stopped at `CHECK_REQUIRED`

Part 1B (clean-v3 localizer training) was authorized and its **pre-training gates were run**.
Every gate that could be evaluated **PASSED**, but **training was not started** because of two
blockers. Gate record: `reports/audits/phase13_clean_v3_localizer_part1b_check_required.json`
`7a2206b1…` · `.md` `3a0b56f7…`.

| Gate | Result |
|---|---|
| §1 R2 SHA + status (`ab451e03…` / `SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING`) | **PASS** |
| §2 pre-training immutability (10 artifacts) | **PASS** |
| §3 population — TRAIN 770 / VAL 103 / 152 components / strata 72·28·36·16 · ROI excluded · overlap 0 | **PASS** |
| §4 hard-set integrity (15 `2f9828d7…` · 5 `a0b332ca…`) | **PASS** |
| §5 executable experiment ID | **BLOCKED** |
| §6 run lock / §7 CUDA | NOT_REACHED (stopped at §5) |
| §8 training core | satisfiable from R2 + Part-1A candidate (not itself a blocker) |
| §17 scheduler / early-stop ordering | verified from executing source, pending the clean-v3 runner |

**Blocker B1 (§5).** The R2 frozen protocol contains **no `experiment_id`**. §5 is unconditional:
*"If the R2 artifact does not contain an executable experiment ID: STOP CHECK_REQUIRED before
training."* Searched: R2 JSON (all 35 keys), R1 JSON, the Part-1A candidate protocol table
(27 fields), both diff tables and `configs/`. Every experiment ID in the repo is **historical
v2**, and the historical runner's default ID is *exactly* the frozen historical experiment
directory — so inventing or deriving an ID would also write into an immutable historical
experiment (§2 / §32).

**Blocker B2 (§29 / §8).** No executable **clean-v3** localizer config exists. The only localizer
config, `configs/kub/phase13b_localizer.yaml`, is the historical v2 config (declares `phase: 13B`;
the historical runner hardcodes `manifest_version: 'phase4_v2'`).

**Verified and recorded.** The historical localizer ordering is: TRAIN → VAL → proposal config
chosen from the grid → checkpoint score → strict `>` test + `bad_epochs` → **`scheduler.step()`**
→ history append → `latest.pt` → `best.pt` if improved. Phase-10 segmentation ordering was **not**
borrowed.

**Check-method trap recorded.** Filtering `reports/tables/kub_view_type_inventory.csv` by its own
`split` column gives **771 / 106** — that column carries **stale `phase4_v2` split labels**. The
active `phase4_v3` manifest must be joined in on `sample_id` to obtain 770 / 103.

**Not created (and why):** no start audit (§19 requires it *before epoch 1*), no completion audit
(§21), no epoch-results table (§22), no reviewer notebook (§24 — would falsely imply training
occurred), no figures, no artifact registry.

> **Phase-13 Part-1B governance:** training **0** · optimizer created **no** · model constructed
> **no** · forward passes **0** · optimizer steps **0** · epochs **0** · localizer inference **0** ·
> proposals **0** · grid configs evaluated **0** · predicted-region segmentation **0** ·
> checkpoints written **0** · history rows **0** · run lock **not acquired** · TEST reads **0** ·
> Phase 14 **not started** · historical artifacts **not modified**.

> **Canonical training-notebook rule (mandatory, prospective):** every scientific training
> reviewer notebook **MUST** contain a **complete epoch-by-epoch table** — one row per
> completed epoch, untruncated, from the immutable `history.csv`, with no missing/duplicate
> epochs. `history.csv` is never modified. Applies to regional-component training,
> localizer training (if epoch-based), multi-domain baseline, Global MedFiLM,
> RA-MedFiLM-Seg++, and ablation/reproducibility runs.

## 4. Deferred debt (labelled HISTORICAL — do not silently carry forward)

| Item | Disposition |
|---|---|
| `PROJECT_CONTEXT.md` "no clean-rerun phase has been executed" | DEFERRED_HISTORICAL — stale (see [PRD.md](PRD.md) §10, C1) |
| `PROJECT_CONTEXT.md` "strongest KUB baseline is UNet++" (v2 conclusion) | DEFERRED_HISTORICAL — v2 only; **not** a clean-v3 winner (C2) |
| `PROJECT_MASTER_PLAN.md` Phase 09 "clean-v3 NOT started" | DEFERRED_HISTORICAL — stale (C3) |
| `ANTIGRAVITY_WORKFLOW.md` "CURRENT PHASE: 13B" | DEFERRED_HISTORICAL — stale (C4) |
| Pre-repair Phase-09 reviewer gallery (all-domain VAL) | `INVALID_SUPERSEDED_CROSS_DOMAIN_SELECTION` — do not use |
| Historical Phases 12–15 results | DEFERRED_HISTORICAL — v2 evidence |
| Phase 13B localizer stages | DEFERRED_HISTORICAL — v2 pilot evidence |
| `antigravity_current_state.json` `phase10_unetpp_started` inconsistency | **Repaired** 2026-09-21 (Phase-11 preflight audit) |

## 5. Next-step procedure (Phase 13 Part 1B — after the blockers are cleared)

**Phase 13 Parts 1A, 1A-R1 and 1A-R2 are COMPLETE; the current executable protocol is
`SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING`. Part 1B is AUTHORIZED but stopped at
`CHECK_REQUIRED`.** Two inputs are needed before training can start:

1. **The exact clean-v3 experiment ID** (§5) — or an authorized derivation rule. It is not in the
   R2 protocol, and the historical default would collide with the frozen historical experiment.
2. **An executable clean-v3 localizer config** (§29 / §8) — or a supervisor-supplied path + SHA.

Once supplied, Part 1B proceeds under the already-verified gates: execute **exactly**
`phase13_clean_v3_localizer_protocol_frozen_r2.json` (not the superseded R1 JSON); use the
**primary 4-term checkpoint-selection tuple**
`(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` at the **frozen** proposal
configuration `0.10 / 0.20 / 5 / 0.30`; compute and log the hard-set / multi-component /
proposals-per-image diagnostics but **exclude them from selection**; pass
`heatmap_resolution=128` explicitly and assert the 128×128 shape contract. The historical
20-config grid remains `DEFERRED_SECONDARY_SENSITIVITY_ONLY`. **MUST NOT** declare a winner,
select a reference architecture, or touch TEST (locked to Phase 39), and **MUST NOT** start
Phases 14–18 automatically. The regional-integration gate remains **NOT_DECIDED**.

Until both inputs arrive, the only valid action is to wait.

## 6. Definition of Done (per phase/subpart)

- [ ] Scientific artifacts unchanged from authorization (config/history/checkpoint SHAs).
- [ ] History internally consistent: contiguous epochs, no duplicates, unique strict max,
      early-stop arithmetic consistent.
- [ ] Completion audit written with SHAs; `scientific_parameter_changes = 0`;
      `nan_inf_events = 0`; finite losses.
- [ ] Reviewer notebook exists, read-only, Run-All clean (unexecuted 0, errors 0), reports
      SHAs, uses **KUB-only** VAL, and displays the **complete untruncated epoch table**.
- [ ] Target contract honoured: foreground **`mask > 0`**; Kidney/Bladder/Ureteric metadata,
      not pixel classes; manifest `phase4_v3`; taxonomy `kub_size_clean_v3_v1`.
- [ ] Required tables + audit written; gallery labelled `DETERMINISTIC_GALLERY_SUBSET_ONLY`.
- [ ] TEST untouched: image/mask reads 0, metrics 0, visualizations 0.
- [ ] No unauthorized phase/model advancement; **STOPPED: YES** recorded.

## 7. Current action

**WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_REAUTHORIZATION** — **Phase 13
Parts 1A, 1A-R1, 1A-R2, 1B-R0 and 1B-R0-R1 are COMPLETE**; the current executable
protocol identity is **`R2 + R2A_LOSS_BINDING`** (R2 base
`phase13_clean_v3_localizer_protocol_frozen_r2.json` `ab451e03…`, unedited; additive loss
amendment `phase13_clean_v3_localizer_loss_binding_r2a.json` `f3aececf…`).

Part 1B-R0 repaired both execution-binding blockers from the earlier `CHECK_REQUIRED` stop:

- **B1 resolved** — the supervisor supplied the exact clean-v3 experiment ID
  `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`. Collision check
  returned **NO_COLLISION** (both `experiments/<id>` and `checkpoints/<id>` absent).
- **B2 resolved** — a clean-v3 executable config, a **new** clean-v3 runner, a clean-v3-safe
  inference wrapper and a pure selection module now exist. The historical runner
  (`train_phase13b_localizer.py`) and the defective historical helper (`learned_roi.py`) are
  **unchanged**.

Part 1B-R0-R1 then closed the single remaining `CHECK_REQUIRED` blocker:

- **Loss binding RESOLVED (supervisor decision L1).** The primary clean-v3 objective is
  `src.losses.localization.CenterNetFocalLoss` with **`alpha=2.0`, `beta=4.0`** and **NO Dice
  term** (label `EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1`). The old composite contract
  `0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice` is disposed as
  `SUPERSEDED_DOCUMENTED_NOT_EXECUTING_OBJECTIVE` (provenance retained, rows not deleted);
  `SoftFocalDiceLoss` remains a `NON_PRIMARY_IMPLEMENTATION_DEFECT` (dead code, unrepaired).
  Physically re-verified: the historical runner (`5985b9eb…555a`) executes exactly
  `CenterNetFocalLoss(alpha=2.0, beta=4.0)` at line 121, and the historical best checkpoint
  (epoch 73) descends from that executing path.
- **Training-readiness REPAIRED.** `evaluate_fixed_config_localizer(...)` is now fully implemented
  (no `NotImplementedError` / TODO / dummy / fabricated metrics on the executable path);
  deterministic seeding (`set_seed(42, deterministic=True)` before model construction,
  `make_generator(42)` for TRAIN + VAL, `seed_worker`); real loader generator state persisted
  (was `{}`); authoritative `phase4_v3` TRAIN + VAL manifest SHAs populated (was `{}`); full
  checkpoint metadata; loud resume safety gates; code paths for training start/completion audits
  (code only — artifacts NOT created); canonical atomic history writes (one completed epoch = one
  row).
- **Binding CSV REPAIRED.** `reports/tables/phase13_clean_v3_executable_config_binding.csv` had a
  raw unquoted comma causing `ParserError: Expected 6 fields in line 66, saw 7`. Regenerated with a
  real CSV writer: `pandas.read_csv` now succeeds with no special options (130 rows × 6 cols); all
  9 prior `CHECK_REQUIRED` rows preserved as `SUPERSEDED_PRIOR_CHECK_REQUIRED_AUDIT`; loss rows now
  cite R2A.
- **Clean-v3 VAL component source bound.** `reports/tables/phase12_clean_v3_oracle_geometry.csv`
  (`29326d5b…7cc0`) — 152 components / 103 cases, native bbox, strata TINY 72 / SMALL 28 /
  MEDIUM 36 / LARGE 16. The stale `kub_size_v1` table and the v2 manifest are **rejected**.

`Phase13 Part1B = EXECUTION_BINDING_RESOLVED_AWAITING_TRAINING_REAUTHORIZATION`; validation status
**`PASS`** — gates A–P all PASS (34/34 unit tests, 0 failures).

**Part1B training: NOT STARTED.** `experiment_id` collision NO; execution binding
`READY_FOR_SUPERVISOR_TRAINING_REAUTHORIZATION_REVIEW`; scientific protocol
`R2 + R2A_LOSS_BINDING`; regional gate `NOT_DECIDED`; Phase 14 `NOT_STARTED`. Training 0 · model
constructions 0 · forward passes 0 · optimizer creations 0 · localizer inference 0 · proposals 0 ·
grid configs evaluated 0 · TEST content reads 0 · scientifically material changes 0.

Supervisor conclusion carried forward: `ORACLE_MECHANISM_VALUE = SUPPORTED_DESCRIPTIVE_EVIDENCE`
and `PHASE13_PROGRESSION = SCIENTIFICALLY_JUSTIFIED`.
**No winner declared; no reference model selected; no statistical testing performed;
regional mechanism NOT promoted; `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` NOT_DECIDED;
final architecture `PROPOSED_NOT_IMPLEMENTED`; TEST locked to Phase 39.**

---

---

## PHASE 13 PART 1B — CLOSURE STATE (2026-09-22)

**Phase13 Part1B: COMPLETE / PASS** · localizer training: **COMPLETE** ·
best checkpoint: **FROZEN** · best epoch **53** · final epoch **68** ·
termination **EARLY_STOPPING_PATIENCE** · final bad_epochs **15**.

Canonical primary coverage: **HISTORICAL_EXECUTING_BBOX_COVERAGE** (R2C).
Pixel coverage: **SECONDARY_COVERAGE_SENSITIVITY_ONLY** (never a selection term).

Canonical best tuple (bbox): `(0.6805555555555556, 0.5986842105263158,
-0.004846047236646169, -1.9175469095890338)`.

Canonical secondary bbox diagnostics: hard_tiny 4/15 · global_empty 1/5 ·
multi_component 0.5714285714285714 · mean_proposals_per_image 4.796116504854369.

Canonical selection sidecar: `reports/tables/phase13_part1b_canonical_selection_history.csv`
(68 rows; authoritative for checkpoint-selection replay — row 31's legacy
`history.csv` primaries are pixel-based and preserved as-is).

Closure repairs completed: R2C markdown runner-SHA erratum recorded additively;
training-completion R2C addendum created; epoch-results table rebuilt with ALL raw
history columns (68 contiguous rows); reviewer notebook rebuilt and Run-All clean
(0 unexecuted, 0 errors, SHA stable 3/3); artifact registry rebuilt (29 rows,
0 missing, 0 duplicates, 0 empty SHAs).

Provenance incidents disclosed in the notebook: two supervisor-ordered
interruptions (after epochs 28 and 31) with same-ID resumes; the pre-stop epoch-27
`best.pt` was overwritten by the authorized resume at epoch 31 (metrics survive in
history, weights do not).

**Part1C: ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION · AUTHORIZED: FALSE.**
Standalone proposal analysis NOT STARTED · predicted-region segmentation NOT STARTED ·
regional integration gate NOT_DECIDED · Phase14 NOT STARTED · TEST reads **0**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1C_AUTHORIZATION`


**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULES.md](RULES.md) · [DESIGN.md](DESIGN.md) · [MEMORY.md](MEMORY.md)

---

## PHASE 13 PART 1C — COMPLETE / PASS (2026-09-22)

Frozen best-checkpoint (epoch 53) standalone GT-free proposal evaluation on the
103 clean-v3 FULL_FIELD VAL images at the single frozen configuration
0.10 / 0.20 / 5 / 0.30. Exactly **one** authorized inference pass.

Canonical BBOX (PRIMARY, HISTORICAL_EXECUTING_BBOX_COVERAGE): tiny_recall90 **49/72**,
overall_recall90 **91/152**, mean_roi_area_fraction 0.004846047236646169,
hard-Tiny **4/15**, global-empty **1/5**, multi-component 0.5714285714285714,
total proposals **494**, mean proposals/image 4.796116504854369.

Pixel sensitivity (SECONDARY): tiny 50/72, overall 101/152, hard-Tiny 5/15.

Reproduction gate vs the frozen Part-1B integrity audit: **0 mismatches**.

Bbox/pixel disagreement: covered90 **10**, covered50 **4**, any-overlap **0**.
Uncovered components (bbox covered90 == FALSE): **61**.

**Part1C: COMPLETE / PASS.** Part1D ELIGIBLE but **NOT AUTHORIZED**.
Regional integration gate **NOT_DECIDED**; regional mechanism NOT promoted;
Phase14 NOT STARTED; RA-MedFiLM NOT_IMPLEMENTED; TEST reads **0**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1D_PREDICTED_REGION_SEGMENTATION_AUTHORIZATION`

### Part-1C stratified reporting erratum (2026-09-22)

Classification `PART1C_FINAL_NOTE_STRATIFICATION_REPORTING_ERROR_ONLY`. The Part-1C
narrative final note misreported three strata. Canonical physical values:

| stratum | N | bbox covered90 | rate | pixel covered90 | rate |
|---|---|---|---|---|---|
| TINY | 72 | 49 | 0.6806 | 50 | 0.6944 |
| SMALL | 28 | 16 | 0.5714 | 20 | 0.7143 |
| MEDIUM | 36 | 19 | 0.5278 | 22 | 0.6111 |
| LARGE | 16 | 7 | 0.4375 | 9 | 0.5625 |
| ALL | 152 | 91 | 0.5987 | 101 | 0.6645 |

Withdrawn: `SMALL = 82%` and `LARGE = 12.5%`. Aggregate 91/152 (bbox) and 101/152
(pixel) unchanged. Label: `DESCRIPTIVE_STRATIFIED_LOCALIZATION_RESULT` — no
significance testing, no causal hardness claim. No persisted artifact contained the
wrong counts; the notebook and all tables were already correct and remain byte-exact.

---

## PHASE 13 PART 1D-A — PROTOCOL FREEZE + STATIC PREFLIGHT: COMPLETE / PASS (2026-09-22)

Status `SUPERVISOR_FROZEN_PART1D_READY_FOR_INFERENCE`. Primary variant
`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED`; three-way comparison GLOBAL_NATIVE vs
ORACLE_FLOAT_GLOBAL_RETAINED vs PREDICTED_REGION_FLOAT_GLOBAL_RETAINED across all
four architectures (UNet, Attention U-Net, UNet++, DeepLabV3+). **No reference model,
no winner, no ranking.**

Fusion frozen: `P(x) = R(x) if U_pred(x) else G(x)` — regional REPLACEMENT inside
support, global retained outside; overlap = MAX among regional crops only;
`max(G,R)` inside support FORBIDDEN; threshold 0.5 AFTER full native fusion.
Oracle margin **0.25**; predicted proposal margin **0.20 already encoded in Part-1C
geometry** (no second margin). Retention = `(D_pred − D_global)/(D_oracle − D_global)`,
**never clipped**; label `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`; no new gate threshold.

Static preflight: `scripts/inference/phase13_part1d_predicted_region_inference.py`
with `tests/test_phase13_part1d_a_static.py` — **19/19 PASS** (supervisor cases A–R).
No model construction, no CUDA request, no inference, no proposal regeneration.

**Global cache: NOT available.** `data_cache/global` is empty; the only populated
probability cache (`data_cache/phase13_predicted_roi`, 106 images) is a HISTORICAL_v2
run with a different checkpoint and is NOT reusable. Part 1D-B therefore requires
**one deterministic global segmentation pass per architecture (4 passes)**; Phase-12
global reproduction tolerance max-abs Dice 1e-4 must pass first.

**Part1D-B: ELIGIBLE / NOT AUTHORIZED.** Regional integration gate **NOT_DECIDED**
(belongs to a separate supervisor-reviewed Part 1E). Part1E NOT STARTED; Phase14 NOT
STARTED; TEST reads **0**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1D_B_INFERENCE_AUTHORIZATION`

---

## Phase 13 Part 1E-A — Prospective Regional-Integration Gate Criteria Freeze

**COMPLETE / PASS / FROZEN.** Status
`PROSPECTIVE_GATE_CRITERIA_FROZEN_BEFORE_PART1D_B_RESULTS`. Criteria frozen **before** any
Part-1D-B predicted-region result existed. Part1D-B results inspected: **NO**.
Numerical gate thresholds introduced: **0**. Weighted score: **NO**. Rank: **NO**.
Reference model: **NONE**; model ranking: **NONE**. Gate mode:
`QUALITATIVE_PROSPECTIVE_EVIDENCE_ADJUDICATION`.

Four frozen dimensions — **A** `ORACLE_MECHANISM_VALUE` (state before Part-1D-B:
`SUPPORTED_DESCRIPTIVE_EVIDENCE`; Part-1D-B may **not** alter it unless it exposes a material
integrity/reproduction defect) · **B** `PRACTICAL_LOCALIZATION_RETENTION`
(`NOT_EVALUABLE_UNTIL_PHASE13`; per-model D_GLOBAL/D_ORACLE/D_PREDICTED, delta Dice,
`RETENTION_DICE`, `ORACLE_GAP_DICE`, IoU/object-recall/FN-reduction retention, component
recovery/lost events, empty recovery/new-empty events, localization-coverage → segmentation-
recovery linkage; **no single field alone decides**) · **C** `GLOBAL_PRESERVATION_FP_COST`
(`MIXED_DESCRIPTIVE_EVIDENCE`; Dice/IoU/precision/recall deltas, FP/FN pixel deltas, cases
improved/unchanged/worsened, max improvement/worsening, new-empty/empty recoveries, component
recoveries/losses; **target recovery MUST be read together with FP/precision cost**) ·
**D** `GENERALITY` (`SUPPORTED_WITH_HETEROGENEITY`; four architectures, no winner/rank;
single-architecture evidence insufficient for GO; heterogeneity reported, not averaged away).

Outcome logic frozen: **GO** (A supported + B meaningful practical utility + C no broad
systematic degradation + D not an isolated architecture artifact) · **REVISE_LOCALIZER**
(A supported but B weak/inconsistent, or C materially problematic, or D too
architecture-specific — hypothesis not abandoned) · **NO_GO** (only when **A is no longer
scientifically supportable**) · **CHECK_REQUIRED** (integrity override).

**Invariant:** a poor GT-free localizer result alone **MUST NOT** produce `NO_GO` while A
remains supported. Integrity failure → `CHECK_REQUIRED`, no verdict issued.

Part-1E-B evidence contract: only the pre-declared Part-1D-B outputs (412-row case-model,
608-row component-model, 4-row model summary, cross-architecture summary, Part-1C tables,
Phase-12 frozen oracle tables, Part-1D-B reproduction audit); no new tuned threshold; no
post-hoc subgroup; the 16-case gallery is REVIEW ONLY and cannot determine the gate.
No statistical-superiority / ranking / winner / clinical claim; no p-value threshold.

Artifacts: `reports/audits/phase13_regional_integration_gate_criteria_frozen.{json,md}`,
`reports/tables/phase13_regional_integration_gate_criteria.csv`.
Counters: training 0 · model constructions 0 · CUDA 0 · segmentation forwards 0 · localizer
forwards 0 · proposal generation 0 · TEST reads 0.

**Part1D-B: ELIGIBLE / NOT AUTHORIZED.** `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`
**NOT_DECIDED**; Part1E-B gate adjudication **NOT_STARTED**; Phase14 **NOT_STARTED**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1D_B_INFERENCE_AUTHORIZATION`

---

## Phase 13 Part 1D-B — Four-Model Predicted-Region Segmentation Evaluation

**COMPLETE / PASS.** Run id `phase13_part1d_b_predicted_region_clean_v3`. All bindings verified
physically before CUDA; TEST reads **0**; no training, no optimizer, no localizer inference, no
proposal regeneration, no oracle rerun, no gate verdict.

### Global reproduction (§9–§12) — ALL FOUR PASS at machine precision

One deterministic 103-case `GLOBAL_NATIVE` pass per architecture, **completed for all four before
any regional crop inference**. Max absolute per-case Dice difference vs the frozen Phase-12
`GLOBAL_NATIVE` rows (tolerance 1e-4):

| model | max abs Dice diff | mean Dice new | mean Dice Phase-12 |
|---|---|---|---|
| UNet | 5.551e-17 | 0.594180 | 0.594180 |
| Attention U-Net | 1.110e-16 | 0.629805 | 0.629805 |
| UNet++ | 1.110e-16 | 0.640516 | 0.640516 |
| DeepLabV3+ | 1.110e-16 | 0.560251 | 0.560251 |

Secondary reproduction fields (IoU / precision / recall) reported descriptively — **no new
threshold invented**.

### Predicted-region inference (§13–§14)

**1976** regional crop evaluations (494 frozen GT-free proposals x 4 architectures). The **2**
bottom-padded proposals per architecture used the corrected R1 square/padding semantics. Fusion
`P(x) = R(x) if U_pred(x) else G(x)`; regional replacement; overlap = MAX among regional crops only;
threshold 0.5 after native fusion. **Fusion wiring verified bit-exactly**: outside `U_pred`,
`P == G` for all 64 gallery case-model pairs.

### Results (descriptive; NO winner, NO rank, NO gate verdict)

| model | D_GLOBAL | D_ORACLE | D_PREDICTED | DELTA_ORACLE | DELTA_PRED | RETENTION_DICE |
|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.724722 | 0.302314 | +0.130542 | **-0.291866** | **-2.235800** |
| Attention U-Net | 0.629805 | 0.699595 | 0.308619 | +0.069790 | **-0.321186** | **-4.602209** |
| UNet++ | 0.640516 | 0.726679 | 0.311355 | +0.086164 | **-0.329161** | **-3.820171** |
| DeepLabV3+ | 0.560251 | 0.750372 | 0.277292 | +0.190121 | **-0.282959** | **-1.488308** |

**The GT-free predicted-region path does NOT retain the oracle benefit.** Precision collapses
(0.69/0.67/0.74/0.71 -> 0.23/0.24/0.24/0.21) while recall is broadly preserved
(0.65/0.70/0.66/0.59 -> 0.67/0.69/0.68/0.62). Mean FP delta **+7,325 to +8,334** pixels.
Cases improved / unchanged / worsened: 10/0/93 · 5/0/98 · 8/0/95 · 11/0/92.
Cross-architecture: improved-all-four **3**, non-worse-all-four **3**, worse-all-four **86**.

Component events remain favourable: recoveries 16/9/14/16, **losses 0/0/0/0**, empty recoveries
8/3/5/11, new empties **0**. Object recall retention 0.49/0.31/0.50/0.39.

**Mechanistic explanation (descriptive):** 372 of the 494 frozen proposals (**75%**) overlap **no
GT pixel at all**; the FP burden is overwhelmingly generated *inside* `U_pred` (gallery: 114k–123k
FP inside vs 3.7k–6.9k outside). The regional mechanism is not the limiting factor — the GT-free
proposal **precision** is.

### Defect found and corrected before artifact release

`PART1D_B_ORACLE_VARIANT_LOOKUP_DEFECT` — the first execution indexed the ORACLE columns from the
`GLOBAL_NATIVE` variant index, producing `D_O == D_G` and `RETENTION_DICE = None`. Caught by a new
**ORACLE_SOURCE_GUARD** (D_O − D_G must reproduce the frozen Phase-12 oracle Dice gain to 1e-4).
The defective run was discarded and the phase re-executed; a permanent guard now fails loud.

### Artifacts

`reports/tables/phase13_part1d_predicted_region_case_model_metrics.csv` (412) ·
`…_component_model_metrics.csv` (608) · `…_model_summary.csv` (4) ·
`phase13_part1d_b_global_reproduction_gate.csv` (4) ·
`phase13_part1d_cross_architecture_summary.csv` · `…_cohort_summary.csv` ·
`…_localization_segmentation_linkage.csv` ·
`reports/audits/phase13_part1d_b_{inference_start,global_reproduction,predicted_region_evaluation}.{json,md}` ·
cache `data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512/` (412 FLOAT32 maps + manifest).

Reviewer notebook `notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_predicted_region_segmentation_analysis.ipynb`
— **READ-ONLY**, 22 sections, Run-All **0 unexecuted / 0 errors**, SHA stable x3
`4cc9e8561aeea4e13b05585971bbb7e6dff8c0671b55f7c3370ab8818b8e7890`.

Counters: training 0 · optimizer 0 · localizer forwards 0 · proposal generation 0 · grid 0 ·
oracle reruns 0 · TEST reads 0 · gate verdict **NOT_DECIDED**.

**Part1D-B: COMPLETE / PASS.** Part1E-B **ELIGIBLE / NOT AUTHORIZED**;
`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` **NOT_DECIDED**; Phase14 **NOT_STARTED**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1E_B_GATE_ADJUDICATION_AUTHORIZATION`

---

## Phase 13 Part 1E-B — Regional-Integration Gate Adjudication

**COMPLETE / PASS. FINAL GATE VERDICT: `REVISE_LOCALIZER`.**

Adjudicated strictly from the evidence prospectively frozen in Part 1E-A (criteria SHA
`342a8bcac2c87bf0b85f7bbd963179e74f029825c0434cf527fbd939d2d13c21`, inspected `NO`, thresholds `0`,
not edited or reinterpreted). Integrity precondition **PASS** (Part-1D-B status PASS, global
reproduction all four PASS, 412/608/4 row contracts, TEST reads 0, integrity failures `[]`, R1
protocol SHA matched). All required physical evidence values matched the frozen tables **exactly**.

### Dimension adjudication

| dim | dimension | pre-state | adjudicated state | GO | REVISE | NO_GO |
|---|---|---|---|---|---|---|
| **A** | ORACLE_MECHANISM_VALUE | `SUPPORTED_DESCRIPTIVE_EVIDENCE` | **`SUPPORTED_DESCRIPTIVE_EVIDENCE`** (unchanged) | precondition | precondition | NO |
| **B** | PRACTICAL_LOCALIZATION_RETENTION | `NOT_EVALUABLE_UNTIL_PHASE13` | **`WEAK__FAILS_TO_TRANSLATE_ORACLE_MECHANISM_INTO_DEPLOYABLE_UTILITY`** | NO | **YES** | NO |
| **C** | GLOBAL_PRESERVATION_FP_COST | `MIXED_DESCRIPTIVE_EVIDENCE` | **`MATERIAL_GLOBAL_PRESERVATION_FP_COST`** | NO | **YES** | NO |
| **D** | GENERALITY | `SUPPORTED_WITH_HETEROGENEITY` | **`CROSS_ARCHITECTURE_CONSISTENT_NEGATIVE__NOT_ISOLATED`** | NO | precondition | NO |

### Why `REVISE_LOCALIZER` and not `NO_GO`

- **A remains supported.** Phase-12 oracle gains stay positive for all four architectures
  (+0.130542 / +0.069790 / +0.086164 / +0.190121) and Part-1D-B independently reproduced the shared
  global path at machine precision, so no integrity or reproduction defect invalidates A. The frozen
  invariant therefore forbids `NO_GO` from a poor GT-free localizer result alone.
- **B fails.** `DELTA_PRED_DICE` and `RETENTION_DICE` are negative for all four architectures
  (-0.291866 / -0.321186 / -0.329161 / -0.282959 and -2.235800 / -4.602209 / -3.820171 / -1.488308),
  never clipped. The frozen GT-free path does not translate the oracle mechanism into deployable
  downstream segmentation utility.
- **C fails.** Precision decreases strongly for all four (mean precision delta -0.427001 to
  -0.494926) with mean FP pixel deltas of +7324.97 to +8334.42 and 92-98 of 103 cases worsening —
  broad systematic degradation. Reported alongside, not hidden: component losses 0, 9-16 recoveries,
  3-11 empty recoveries, 0 new empties.
- **D is not the operative trigger.** The negative result is cross-architecture consistent
  (worse-for-all-four 86 cases; 0 components lost by any architecture), so it is not an isolated
  architecture-specific accident.

### Verdict discipline

Phase-12 regional mechanism hypothesis **remains supported** · current frozen GT-free
localization / proposal / integration path **NOT promoted** · result does **NOT** authorize
RA-MedFiLM regional integration yet · Phase14 **must not** begin as if the regional mechanism were
approved · **no** automatic redesign performed in Part 1E-B · a separately supervised revision plan
is required. `REVISE_LOCALIZER` is **not** equated with scientific failure of the oracle mechanism.
No proposal threshold or fusion rule was silently changed.

### Artifacts

`reports/audits/phase13_regional_integration_gate_after_phase13.{json,md}` (sha `4436e6a5…`) ·
`reports/tables/phase13_regional_integration_gate_after_phase13.csv` (4 dimension rows, no score,
no rank, no threshold) · gate review notebook
`notebooks/phasewise/phase_13_predicted_roi_localization/phase13_regional_integration_gate_review.ipynb`
(READ-ONLY, 10 sections, 0 unexecuted / 0 errors, SHA stable x3 `24eca67c…`).

Counters: training 0 · optimizer 0 · model constructions 0 · CUDA requests 0 · segmentation
forwards 0 · regional crop forwards 0 · localizer forwards 0 · proposal generation 0 · oracle
reruns 0 · TEST reads 0.

### Phase-13 closure

| phase | state |
|---|---|
| Part 1B | COMPLETE / PASS / FROZEN |
| Part 1C | COMPLETE / PASS / FROZEN |
| Part 1D-A-R1 | COMPLETE / PASS / FROZEN |
| Part 1D-B | COMPLETE / PASS / FROZEN |
| Part 1E-A | COMPLETE / PASS / FROZEN |
| Part 1E-B | **COMPLETE / PASS** |
| **Phase 13** | **COMPLETE** |
| `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` | **REVISE_LOCALIZER** |
| `REGIONAL_MECHANISM_PROMOTED` | **NO** |
| Phase 14 | NOT_STARTED |
| TEST | UNTOUCHED |

next_action: `WAIT_FOR_SUPERVISOR_REGIONAL_LOCALIZER_REVISION_PLAN`

---

## Post-Phase-13 Regional Revision R0 — Failure Decomposition + Bounded Revision Protocol Freeze

**COMPLETE / PASS.** Separate post-Phase-13 revision branch. Phase-13 evidence **not** reopened or
rewritten. Analysis only — no training, no inference, no proposal regeneration, no checkpoint writes.

### Binding verification

All seven frozen inputs verified by SHA-256 and row count (final gate `4436e6a5…`,
Part-1D-B evaluation `9a9838ac…`, Part-1C proposals 494 `8c3151a3…`, Part-1C case proposals 103
`d25c44ec…`, Part-1C component coverage `2a3623fe…`, Part-1D-B case-model 412 `53e93982…`,
Part-1D-B component-model 608 `f82e0632…`). `final_gate_verdict == REVISE_LOCALIZER` confirmed.

### Failure decomposition

**The failure is an intervention-precision failure, not a representation failure.**

- 494 proposals: **122 GT-hit · 372 GT-miss · GT-miss fraction 0.753036**
- Rank pixel-hit rates: rank1 0.339806 · rank2 0.398058 · rank3 0.176471 · rank4 0.145833 · rank5 0.155556
- **Score is near-degenerate**: 337/494 (**68.22%**) saturated at the maximum 0.125065; range 0.024717;
  IQR 0.000533 — yet still informative: saturated hit rate **0.335312** vs below-max **0.057325** (5.85×)
- Score separability (diagnostic only): **ROC-AUC 0.670611**, PR-AUC 0.305819 vs base rate 0.246964
- Every **label-blind** marginal floor removes more off-target than GT-hit proposals —
  q10 (0.119470) removes **50 off-target at 0 hit cost**; q25 removes 118 off-target / 4 hits;
  marginal max removes 148 off-target / 9 hits
- **Dominant linkage**: `off_target_support_fraction` vs FP-pixel-delta Spearman **rho 0.5918 – 0.6372**,
  positive and consistent across all four architectures. GT-miss *count* is only weakly linked to FP
  delta and unassociated with Dice delta. Language: **ASSOCIATION — not CAUSE**
- Improved cases carry **more** GT-hit proposals and **larger** intervention area, and have **lower**
  Part-1C `bbox_covered90` — improvement concentrates where GLOBAL was already struggling
- **Component losses are 0 for all four architectures** and every recovered component had
  `bbox_any_overlap_rate` 1.000 — favourable recovery evidence preserved

### R0 conclusion — `H1_FIRST_SELECTIVE_ACCEPTANCE`

**Selective-abstention principle: SUPPORTED.** The frozen fusion rule already guarantees
`PREDICTED == GLOBAL` exactly when nothing is accepted, so maximum proposal recall is not required.

H1 is the minimum justified change: zero training, zero checkpoint change, zero geometry change, zero
fusion change, and reversible. H2 would change the weights before establishing whether the existing
weights are limiting; H3 would confound the accept/reject test by changing the fusion rule.

This is a **revision-development ordering decision** — not GO, not NO_GO, not promotion.

### Frozen R1 candidate family (design only, NOT executed)

7 configurations (max 8) in `reports/tables/post_phase13_regional_revision_r1_candidate_family.csv`:
control **R1-C0** (floor 0.10, max 5) plus floor x max-accepted combinations using label-blind marginal
score floors 0.119470 / 0.124532 / 0.125065 and max accepted 1 / 5. Changed axis: **score acceptance
floor + maximum accepted proposals only**. Frozen: localizer checkpoint, proposal coordinates, margin
0.20, NMS 0.30, regional crop/restore, segmentation checkpoints, fusion rule, threshold 0.5.

### Artifacts

`reports/audits/post_phase13_regional_revision_r0_failure_decomposition.{json,md}` ·
`reports/audits/post_phase13_regional_revision_r0_protocol_frozen.{json,md}` ·
`reports/tables/post_phase13_r0_proposal_score_rank_diagnostics.csv` ·
`post_phase13_r0_case_proposal_burden.csv` (103) ·
`post_phase13_r0_proposal_to_segmentation_linkage.csv` ·
`post_phase13_r0_proposal_to_segmentation_scatter.csv` ·
`post_phase13_r0_improved_vs_worsened_context.csv` ·
`post_phase13_r0_component_recovery_context.csv` ·
`post_phase13_regional_revision_r1_candidate_family.csv`

Counters: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · localizer forwards 0 ·
segmentation forwards 0 · regional crop forwards 0 · proposal regeneration 0 · checkpoint writes 0 ·
TEST reads 0 · external-test reads 0.

Phase13 **COMPLETE / FROZEN** · gate **REVISE_LOCALIZER** · promoted **NO** · Phase14 **NOT_STARTED** ·
Revision R0 **COMPLETE / PASS** · Revision R1 **ELIGIBLE after supervisor review — NOT AUTHORIZED** ·
TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_AUTHORIZATION`

---

## Post-Phase-13 Revision R0-B — R1 Policy Membership / Tie-Break Freeze

**COMPLETE / PASS.** Status `SUPERVISOR_FROZEN_R1_POLICY_READY_FOR_EXECUTION`. Defines the
deterministic execution semantics of the already-frozen 7-config family. **No** model inference, no
training, no proposal regeneration, no checkpoint writes, TEST untouched.

### Frozen execution semantics

- **Acceptance operator:** `proposal_score >= score_acceptance_floor` — comparator
  **`GREATER_THAN_OR_EQUAL`**, not `>`. The floors physically stored in the candidate-family CSV are the
  executable constants (C0 0.100000 · C1/C2 0.119470 · C3/C4 0.124532 · C5/C6 0.125065); recomputing a
  quantile during R1 or changing floor precision after outcomes is **forbidden**.
- **Within-case order:** `proposal_rank` **ASCENDING**, then retain at most `max_accepted_proposals`.
  `PROPOSAL_RANK_ROLE = DETERMINISTIC_FROZEN_ORDER_ONLY` — **not** confidence superiority within ties.
  Re-sorting by GT / area / coverage / outcome / random / heuristics / floating score is **forbidden**.
- **Zero acceptance:** accepted 0 → regional intervention NONE → prediction **GLOBAL exactly**. Valid and
  expected; forcing at least one proposal is **forbidden**.

### Frozen membership (label-blind)

`post_phase13_regional_revision_r1_frozen_membership.csv` — **3458 rows** (7 x 494), containing only
`config_id · sample_id · proposal_rank · proposal_score · score_acceptance_floor · score_passes_floor ·
max_accepted_proposals · selected_by_rank_cap · accepted · accepted_order_within_case`.
**No GT, no segmentation outcome, no component labels, no hit/miss labels.**

| config | floor | max | accepted | cases 0 | membership SHA-256 |
|---|---|---|---|---|---|
| R1-C0 | 0.100000 | 5 | **494** | 0 | `ac5bbc02…` |
| R1-C1 | 0.119470 | 1 | 103 | 0 | `844f70d3…` |
| R1-C2 | 0.119470 | 5 | 444 | 0 | `ec8c5b9c…` |
| R1-C3 | 0.124532 | 1 | 103 | 0 | `844f70d3…` |
| R1-C4 | 0.124532 | 5 | 372 | 0 | `f58a5a94…` |
| R1-C5 | 0.125065 | 1 | 102 | **1** | `0c424bb6…` |
| R1-C6 | 0.125065 | 5 | 337 | **1** | `5b40128e…` |

Hashes are SHA-256 over `(sample_id, proposal_rank, accepted)` ordered by `sample_id` ascending then
`proposal_rank` ascending. **R1 inference MUST verify them before CUDA.**

### Gates

- **Control identity: PASS** — R1-C0 accepts **494 / 494** and its per-case counts are identical to the
  frozen Part-1C proposal counts.
- **Relationship checks: all PASS** — floor monotonicity (same cap) adds **0** accepted proposals
  (C0 ⊇ C2 ⊇ C4 ⊇ C6, C1 ⊇ C3 ⊇ C5); cap subsets hold (C1 ⊆ C2, C3 ⊆ C4, C5 ⊆ C6).
- **Tie audit** — marginal max `0.1250653713941574`; **337** tied (0.682186); rank-1 saturated
  **102 / 103**; rank-2 91 / 103; **0** proposals strictly between the stored 0.125065 floor and the
  exact max.

### Disclosed family redundancy (family NOT changed)

**R1-C1 and R1-C3 produce identical membership** (`844f70d3…`). With `max_accepted_proposals = 1` the
selection is the lowest-rank floor-passing proposal, and every rank-1 proposal scores **>= 0.124852** —
above both floors — so the two floors never differ in effect. Distinct memberships **6** across **7**
configs. No configs added or removed; the family remains frozen as supervisor-authored. R1 will
effectively test **6 distinct policies**.

### R0 causal-language clarification (additive)

`post_phase13_r0_interpretation_clarification.{json,md}` —
`CAUSAL_LANGUAGE_SCOPE_CLARIFICATION_ONLY`. The persisted R0 artifacts contained exclusionary wording
("not a representation failure") in 3 locations; the canonical replacement is *"dominated by poor
intervention precision / off-target intervention burden … does not exclude localizer representation or
score calibration as contributors."* R0 artifacts **not** rewritten. H1 ordering, measurements, candidate
family and membership all **unchanged**.

### Artifacts

`reports/audits/post_phase13_regional_revision_r1_policy_frozen.{json,md}` ·
`reports/audits/post_phase13_r0_interpretation_clarification.{json,md}` ·
`reports/tables/post_phase13_regional_revision_r1_frozen_membership.csv` (3458) ·
`reports/tables/post_phase13_regional_revision_r1_membership_summary.csv` (7)

Counters: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · localizer forwards 0 ·
segmentation forwards 0 · regional crop forwards 0 · proposal generation 0 · checkpoint writes 0 ·
TEST reads 0 · external-test reads 0.

Phase13 **COMPLETE / FROZEN** · regional gate **REVISE_LOCALIZER / FROZEN** · Revision R0
**COMPLETE / PASS / FROZEN** · Revision R1 policy definition **COMPLETE / PASS** · Revision R1
scientific execution **ELIGIBLE / NOT AUTHORIZED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_EXECUTION_AUTHORIZATION`

---

## Post-Phase-13 Revision R1 — Bounded Selective-Acceptance Policy Ablation

**COMPLETE / PASS.** Run id `post_phase13_regional_revision_r1_selective_acceptance`. Authorized axis:
proposal acceptance / abstention **only**. No training, no optimizer, no localizer inference, no proposal
regeneration, no oracle rerun, no fusion change, no candidate-family expansion, TEST untouched.

### Compute-efficiency contract honoured

Each of the 494 frozen proposals was forwarded **once** per architecture: **1976** regional crop
evaluations (494 x 4), **not** 1976 x 7. All seven policies were assembled from the **same** per-case
regional maps. The verified Part-1D-B global cache was reused (412/412 items verified, GLOBAL_NATIVE
reproduced at 5.6e-17 … 1.1e-16 max abs Dice), so **0** global model forwards were run. HD95 was memoised
by binary-prediction hash (1184 calls, 1700 memo hits).

### Gates

- **Control reproduction PASS** — R1-C0 reproduces the frozen Part-1D-B result with max abs per-case Dice
  difference **8.7e-17 … 9.7e-17** (tolerance 1e-6) for all four architectures.
- **C1 == C3 duplicate PASS** — identical accepted ranks, identical fused probability, identical binary
  prediction, all metrics identical to **0.0**, identical component detection. Not treated as independent
  evidence.
- **All 21 integrity gates PASS**, zero failures.

### Results (descriptive; no winner, no rank, no verdict)

Macro Dice per policy (UNet / Attention / UNet++ / DeepLab):

| config | intervention | macro Dice | DELTA_POLICY_GLOBAL | RETENTION_DICE | mean FP delta | component recoveries |
|---|---|---|---|---|---|---|
| R1-C0 | 494 accepted (4.80/img) | 0.302 / 0.309 / 0.311 / 0.277 | -0.292 / -0.321 / -0.329 / -0.283 | -2.24 / -4.60 / -3.82 / -1.49 | +7325 / +7528 / +7924 / +8334 | 16 / 9 / 14 / 16 |
| R1-C1 (= C3) | 103 accepted (1.00/img) | 0.458 / 0.481 / 0.477 / 0.426 | -0.136 / -0.149 / -0.163 / -0.134 | -1.04 / -2.13 / -1.90 / -0.70 | +1797 / +1999 / +2202 / +2301 | 2 / 1 / 3 / 4 |
| R1-C2 | 444 accepted (4.31/img) | 0.308 / 0.314 / 0.316 / 0.283 | -0.286 / -0.316 / -0.325 / -0.277 | -2.19 / -4.52 / -3.77 / -1.46 | +7137 / +7361 / +7778 / +8119 | 16 / 9 / 14 / 16 |
| R1-C4 | 372 accepted (3.61/img) | 0.326 / 0.332 / 0.331 / 0.298 | -0.268 / -0.298 / -0.309 / -0.262 | -2.05 / -4.27 / -3.59 / -1.38 | +6613 / +6904 / +7357 / +7598 | 15 / 8 / 13 / 16 |
| R1-C5 | 102 accepted (0.99/img) | 0.463 / 0.486 / 0.483 / 0.426 | -0.131 / -0.144 / -0.158 / -0.134 | -1.00 / -2.06 / -1.83 / -0.70 | +1770 / +1974 / +2177 / +2274 | 2 / 1 / 3 / 4 |
| R1-C6 | 337 accepted (3.27/img) | 0.340 / 0.341 / 0.341 / 0.304 | -0.254 / -0.289 / -0.300 / -0.257 | -1.95 / -4.14 / -3.48 / -1.35 | +6315 / +6640 / +7086 / +7276 | 13 / 5 / 10 / 13 |

**Descriptive trade-off.** Reducing intervention cuts the FP burden sharply (mean FP delta +7325 → +1770
for UNet, a 76% reduction) and roughly halves the Dice deficit (0.302 → 0.463), but `RETENTION_DICE`
remains **negative for every policy and every architecture**, and component recoveries fall from 16/9/14/16
to 2/1/3/4 under the most aggressive selectivity. Mild selectivity (C2/C4/C6) largely preserves recovery
while barely moving Dice. **Component losses remain 0 for all policies and all architectures.**

Cross-architecture: cases worse in all four 84–87 of 103; components lost by >=1 model **0** for every policy.

### Tables

`post_phase13_r1_case_model_policy_metrics.csv` (**2884** = 7 x 4 x 103) ·
`post_phase13_r1_component_model_policy_metrics.csv` (**4256** = 7 x 4 x 152) ·
`post_phase13_r1_model_policy_summary.csv` (**28**) ·
`post_phase13_r1_policy_intervention_summary.csv` (**7**) ·
`post_phase13_r1_cross_architecture_policy_summary.csv` (**7**)

### Audits and notebook

`reports/audits/post_phase13_r1_control_and_duplicate_verification.{json,md}` ·
`reports/audits/post_phase13_regional_revision_r1_evaluation.{json,md}` ·
notebook `notebooks/phasewise/phase_13_predicted_roi_localization/post_phase13_regional_revision_r1_analysis.ipynb`
— READ-ONLY, 21 sections, 45 cells / 22 code, Run-All **0 unexecuted / 0 errors**, SHA stable x3
`2cbf25da6290ca15ee5863b63da8a8de99f8deccff48b59e927cb306de3cbbdb`.

### Adaptive-development disclosure

R1 is an **adaptive VAL-development revision** initiated after Phase 13 failed the regional-integration
gate. The seven-policy family was frozen **before** candidate-specific segmentation execution and
membership is **label-blind**; GT is used only for post-freeze evaluation. VAL remains development data;
R1 findings do **not** replace final TEST evaluation; TEST remains untouched until Phase 39. No
external-test tuning, no hidden candidate search.

### No R1 verdict

**H1 verdict `NOT_ADJUDICATED`.** No best policy, no winner, no optimal threshold, no GO/NO_GO, no
promotion, no retraining recommendation, no H2 authorization.

Counters: training 0 · optimizer 0 · localizer forwards 0 · proposal generation 0 · global model forwards
**0** · regional crop evaluations **1976** · oracle reruns 0 · TEST reads 0 · external-test reads 0 ·
candidate-family expansion 0.

Phase13 **COMPLETE / FROZEN** · regional gate **REVISE_LOCALIZER / FROZEN** · Revision R0
**COMPLETE / PASS / FROZEN** · Revision R1 policy **COMPLETE / PASS / FROZEN** · Revision R1 execution
**COMPLETE / PASS** · H1 adjudication **ELIGIBLE / NOT AUTHORIZED** · H2 **NOT_STARTED** · Phase14
**NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_R1_H1_ADJUDICATION_AUTHORIZATION`

---

## Post-Phase-13 R1-H1 — Selective-Acceptance Hypothesis Adjudication

**COMPLETE / PASS. H1 OUTCOME: `H1_PARTIAL_MITIGATION_INSUFFICIENT_AS_STANDALONE_REVISION`.**

Integrity precondition PASS (R1 evaluation PASS with `integrity_failures []`, C0 reproduction PASS,
C1 membership == C3, C1 output == C3, 28/7/7 row contracts, R0 clarification scope intact). Every
quoted figure in the task brief was verified physically against the frozen tables.

### Dimension adjudication

| dim | dimension | adjudicated state | supports H1 |
|---|---|---|---|
| **A** | GLOBAL_PRESERVATION | `NOT_RESTORED__MATERIALLY_IMPROVED_BUT_STILL_DEFICIENT` | **NO** |
| **B** | REGIONAL_UTILITY_RETENTION | `PARTIAL__RECOVERY_SIGNAL_LOST_UNDER_AGGRESSIVE_SELECTIVITY` | **NO** |
| **C** | INTERVENTION_SELECTIVITY | `IMPROVED__BUT_OFF_TARGET_FRACTION_REMAINS_HIGH` | **YES** |
| **D** | CROSS_ARCHITECTURE_CONSISTENCY | `CONSISTENT_ACROSS_ARCHITECTURES__NEGATIVE_RESULT_IS_GENERAL` | **NO** |

- **A — not restored.** **28/28** config/model combinations remain **below GLOBAL**. R1-C5 still trails by
  −0.131136 / −0.143855 / −0.157948 / −0.133755. FP burden reduced **74%** (+7778 → ≈+2049) but remains
  positive everywhere; cases worse unchanged at 93.0–94.5 of 103.
- **B — partial, insufficient.** Component **losses 0** throughout and empty recoveries largely retained,
  but recoveries collapse 55 → 10 (82% loss) under aggressive selectivity; `RETENTION_DICE` negative in
  **28/28**.
- **C — improved.** Accepted 494 → 102; GT-miss accepted 372 → 68; mean precision 0.2342 → 0.4259 with
  recall essentially unchanged. Accepted GT-miss fraction 0.753036 → **0.666667** — better, but two thirds
  of surviving interventions remain off-target.
- **D — general.** The negative result holds in all four architectures; at C5, cases worse in all four 84,
  recovered by ≥1 architecture 6, lost by ≥1 architecture 0. No winner, no ranking.

### Trade-off pattern — exactly reproduced

Mild selectivity (C2) reproduces the C0 recovery profile exactly (16/9/14/16) while relieving only **2%** of
the FP burden; aggressive selectivity (C1/C5) relieves **74%** of the FP burden but destroys **82%** of the
recoveries. No eighth policy searched, no threshold interpolated, no best policy declared.

### H1 does NOT prove representation failure

H1 isolated the acceptance-only axis and showed it is not sufficient by itself. Localizer representation,
heatmap confidence calibration, proposal ranking, training objective, checkpoint-selection semantics and
precision/recall balance remain open contributors for H2 protocol design.

### Bounded search closure

R1 candidate family **CLOSED**. `POST_HOC_R1_EXPANSION: FORBIDDEN` — no R1-C7, no new floor, no new
max-proposal count, no interpolated threshold, no outcome-driven candidate without a new
supervisor-approved scientific protocol.

### Artifacts

`reports/audits/post_phase13_regional_revision_r1_h1_adjudication.{json,md}` ·
`reports/tables/post_phase13_regional_revision_r1_h1_adjudication.csv` (4 rows A–D)

Counters: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · global forwards 0 · regional
forwards 0 · localizer forwards 0 · proposal generation 0 · oracle reruns 0 · TEST reads 0 ·
external-test reads 0. New numerical thresholds **0** · new configs **0** · new subgroup **0** ·
winner **NONE** · selected threshold **NONE**.

Phase13 **COMPLETE / FROZEN** · original gate **REVISE_LOCALIZER / FROZEN** · R0 **COMPLETE / PASS /
FROZEN** · R1 policy **COMPLETE / PASS / FROZEN** · R1 execution **COMPLETE / PASS / FROZEN** ·
H1 adjudication **COMPLETE / PASS** · H1 **CLOSED — PARTIAL_MITIGATION_INSUFFICIENT** · H2 protocol design
**ELIGIBLE / NOT AUTHORIZED** · H2 training **NOT AUTHORIZED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2_PROTOCOL_DESIGN_AUTHORIZATION`

---

## Post-Phase-13 H2-A — Localizer Score-Path Audit + Selection-Only Protocol Freeze

**COMPLETE / PASS / FROZEN.** Static analysis only — no training, no model construction, no CUDA, no
forward pass, no proposal generation, no checkpoint writes, TEST untouched.

### §3–§4 Score-path audit — `SCORE_PATH_IMPLEMENTATION_VALID`

Six-stage path inspected physically (logits -> sigmoid -> 8-connected component extraction -> per-component
max score -> score-descending NMS -> top-k + serialization). **All twelve suspected defects are ABSENT**:
no hard clamp · no normalization to a fixed ceiling · no score rounding · no quantization · sigmoid applied
**exactly once** · no double sigmoid · no post-processing rescale · correct heatmap channel `[0,0]` ·
correct per-component maximum · no serialization truncation · no top-k score replacement · no threshold
substitution. **The 0.125065 maximum is NOT imposed by code.**

**Root cause (recorded, not hidden):** the plateau equals `sigmoid(head output)`. The trained head is
**degenerate** — all 16 channel weights are negative and nearly identical in magnitude (range
-0.20109390 … -0.20757976, std 0.00180099, abs-max/abs-mean **1.019491**, 0/16 positive), so the head is
effectively `-0.203611 * sum(features) + bias`. The bias is `-1.9453773498535156` (sigmoid
`0.12505828655695442`) versus the plateau's logit `-1.9453126016481144`. The head produces a
**near-constant output field**. Recorded as material scientific observation
**`DEGENERATE_LOCALIZER_HEAD__NEAR_CONSTANT_OUTPUT`** — it is a trained-model property, not a score-path
defect, so it does **not** trigger `CHECK_REQUIRED`; but it pre-registers a plausible reason H2A may prove
insufficient, in which case representation/objective redesign (not selection) becomes indicated.

### §5 Trajectory availability — classification `C__ONLY_BEST_AND_LATEST_AVAILABLE`

history.csv **68 contiguous rows** (epochs 1–68, sha `344cfc01…`). best.pt epoch **53**; latest.pt epoch
**68**. Available epoch weights: **{31, 53, 68} = 3 of 68** (epoch 31 retained under `provenance/` from the
R2B/R2C archive). No per-epoch proposal tables or sidecars; history has **no** precision/hit columns, so
per-epoch proposal hit-precision is **not reconstructable without inference**. No checkpoints invented.

### §14 Execution mode — `MODE_B__DETERMINISTIC_TRAINING_REPLAY_WITH_NEW_SELECTION`

The new rule needs `PROPOSAL_PIXEL_ANY_HIT_PRECISION` for every epoch, which needs each epoch's weights and
an inference pass. With 3 of 68 epoch weights and no persisted proposals, replay-only is impossible. The
replay MUST retain identical gradient-update semantics; the only scientific change is which epoch is
declared best.

### §6–§13 Frozen H2A protocol

Experiment id
`post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`
— **no collision** (both `checkpoints/` and `experiments/` paths absent).

New primary utility **`DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90`** = `0.0` if any of P,T,O <= 0 else
`3 / (1/P + 1/T + 1/O)`, with P = `PROPOSAL_PIXEL_ANY_HIT_PRECISION`, T = `tiny_recall90`,
O = `overall_recall90`. Not a statistical F1 score.

New 6-term checkpoint tuple: `(DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90, tiny_recall90,
overall_recall90, PROPOSAL_PIXEL_ANY_HIT_PRECISION, -mean_roi_area_fraction, -val_loss)` — strict
lexicographic `>`, ties BAD_EPOCH, patience 15. No downstream segmentation metric, no Phase-12 oracle
result and no R1 outcome participates in selection.

**Only one scientific axis changes.** `LOSS_CHANGED: NO` · `TARGET_CHANGED: NO` ·
`ARCHITECTURE_CHANGED: NO` · `SIGMA_CHANGED: NO` · `OPTIMIZER_CHANGED: NO` · `DATA_CHANGED: NO` ·
`AUGMENTATION_CHANGED: NO` · `PROPOSAL_CONFIG_CHANGED: NO` · **`CHECKPOINT_SELECTION_CHANGED: YES`**.

Proposal contract unchanged (threshold 0.10 / margin 0.20 / top_k 5 / NMS 0.30, no grid). Downstream
evaluation frozen to the same four segmentation checkpoints, same
`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` fusion and the localizer's **native** proposal policy —
**R1 selective acceptance is NOT carried into H2A**.

### Artifacts

`reports/audits/post_phase13_h2a_localizer_score_path_audit.{json,md}` ·
`reports/audits/post_phase13_h2a_protocol_frozen.{json,md}` ·
`reports/tables/post_phase13_h2a_protocol_diff_vs_phase13.csv` (41 fields; **5** rows marked changed — 3 checkpoint-selection fields, 1 new evaluation-only metric, 1 provenance experiment id; **0** gradient-update fields changed) ·
`reports/tables/post_phase13_h2a_evidence_contract.csv`

Counters: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · localizer forwards 0 · segmentation
forwards 0 · regional forwards 0 · proposal generation 0 · checkpoint writes 0 · TEST reads 0 ·
external-test reads 0.

Phase13 **COMPLETE / FROZEN** · original gate **REVISE_LOCALIZER / FROZEN** · H1
**CLOSED__PARTIAL_MITIGATION_INSUFFICIENT** · H2A protocol **COMPLETE / PASS / FROZEN** · H2A execution
**ELIGIBLE / NOT AUTHORIZED** · H2 loss redesign **NOT_STARTED** · H3 fusion redesign **NOT_STARTED** ·
Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2A_EXECUTION_AUTHORIZATION`

---

## Post-Phase-13 H2-A-B1 — Deterministic Localizer Training Replay + Deployment-Balanced Selection

**COMPLETE / PASS.** Experiment id
`post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`.

### Training

| item | value |
|---|---|
| completed epochs | **98** |
| termination | **EARLY_STOPPING_PATIENCE** (best 83 + patience 15 = 98) |
| best epoch | **83** |
| final bad_epochs | **15** |
| best.pt SHA | `2e2e8f7909649f50cf7b830aab357d9e14a4b62b71a00fc0efe22aa300ba54c8` |
| latest.pt SHA | `429041f8aabfda238cf226f3872991c236c63a8fd6938656d4016bebb1492588` |
| history.csv SHA | `ed96c4b617a8940c30df30d9a9b8f562819e31d1370b31ee60776142fd077b99` |

**Best six-term tuple:** `(0.4522162369629855, 0.6944444444444444, 0.6381578947368421,`
`0.27571115973741794, -0.0047946270615735415, -1.8425761369558482)`
= HMean **0.4522162369629855** · tiny90 **0.6944444444444444** · overall90 **0.6381578947368421** ·
P **0.27571115973741794** · mean ROI area **0.0047946270615735415** · val_loss **1.8425761369558482**

### Integrity

- **Trajectory reproduction PASS** — 68 overlapping epochs, max abs `train_loss` diff **4.441e-16**, max abs
  `val_loss` diff **0.000e+00** (bit-exact), **0** LR mismatches. Gradient-update semantics are identical to
  Phase-13, exactly as the selection-only claim requires.
- **Checkpoint model-state cross-checks: none** — best epoch 83 and latest 98 are not the historical 31/53/68,
  so no provenance-valid overlap exists. The protocol explicitly does not require reaching any particular epoch.
- **Selection replay PASS** — 0 mismatches; replayed best epoch 83, final bad_epochs 15, early stop 98.
- **All integrity gates PASS.**

### Standalone best-checkpoint proposal evaluation (103 cases / 152 components)

| quantity | value |
|---|---|
| proposals | **457** (4.436893/img) |
| P (pixel any-hit precision) | **0.27571115973741794** |
| bbox any-hit precision | 0.2735229759299781 |
| tiny recall90 | 0.6944444444444444 |
| overall recall90 | 0.6381578947368421 |
| overall recall50 | 0.8223684210526315 |
| any-overlap recall | 0.875 |
| mean coverage | 0.7878969538240504 |
| mean proposal union area | 0.0047946270615735415 |
| score max / IQR / fraction at max | 0.14163722097873688 / 0.0016540437936782837 / 0.6455142231947484 |
| ROC-AUC / PR-AUC | 0.7011101520164964 / 0.3729361181989911 |

Cohorts: hard-Tiny n15 covered90 **3** (0.2) · global-empty n8 covered90 **2** (0.25) ·
multi-component n98 covered90 **61** (0.6224).

### Descriptive comparison vs Phase-13 best (epoch 53) — NO superiority claim

| quantity | Phase-13 | H2A | delta |
|---|---|---|---|
| proposals | 494 | 457 | −37 |
| **P (pixel any-hit precision)** | 0.246964 | **0.275711** | **+0.028748** |
| bbox any-hit precision | 0.248988 | 0.273523 | +0.024535 |
| tiny recall90 | 0.680556 | **0.694444** | +0.013889 |
| overall recall90 | 0.598684 | **0.638158** | +0.039474 |
| overall recall50 | 0.789474 | 0.822368 | +0.032895 |
| any-overlap recall | 0.848684 | 0.875 | +0.026316 |
| mean coverage | 0.758402 | 0.787897 | +0.029495 |
| mean proposal union area | 0.004846 | 0.004795 | −0.000051 |
| score max | 0.125065 | 0.141637 | +0.016572 |
| fraction exactly at max | 0.682186 | 0.645514 | −0.036672 |

**Every quantity improves except proposal count (fewer, more precise proposals) and mean union area
(marginally smaller).** Descriptive development comparison only.

### Artifacts

`reports/audits/post_phase13_h2a_training_evaluation.{json,md}` ·
`post_phase13_h2a_training_trajectory_reproduction.{json,md}` ·
`post_phase13_h2a_selection_replay_verification.{json,md}` ·
`post_phase13_h2a_best_checkpoint_standalone_evaluation.json` ·
`reports/tables/post_phase13_h2a_best_checkpoint_{proposals,case_proposals,component_coverage,size_stratified}.csv` ·
`reports/tables/post_phase13_h2a_vs_phase13_localizer_comparison.csv` ·
notebook `post_phase13_h2a_localizer_training_review.ipynb` — READ-ONLY, 26 sections, 54 cells / 27 code,
Run-All **0 unexecuted / 0 errors**, epoch table **98/98 untruncated**, SHA stable x3 `aace3819…`.

Counters: logical training experiments **1** · optimizer construction **1** · proposal configs **1** ·
proposal grid **0** · downstream segmentation model constructions **0** · downstream segmentation forwards
**0** · oracle reruns **0** · TEST reads **0** · external test reads **0**.

H2A protocol **COMPLETE / PASS / FROZEN** · H2A-B1 training **COMPLETE / PASS** · H2A standalone localizer
evaluation **COMPLETE / PASS** · H2A downstream segmentation **ELIGIBLE_FOR_SUPERVISOR_REVIEW / NOT
AUTHORIZED** · H2A outcome adjudication **NOT_STARTED** · H2 loss/target redesign **NOT_STARTED** · H3
**NOT_STARTED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2A_DOWNSTREAM_AUTHORIZATION`

---

## Post-Phase-13 H2-A-B2 — Downstream Regional Segmentation Evaluation

**COMPLETE / PASS.** Run id `post_phase13_h2a_downstream_epoch83_native_policy`.

### Execution Summary

| item | value |
|---|---|
| frozen H2A proposals | **457** (authoritative, no regeneration) |
| regional crop evaluations | **1828** = 457 x 4 models |
| localizer forwards | **0** |
| proposal regeneration | **0** |
| new global forwards | **0** |
| global cache reused | **YES** (412/412 reproduced) |
| case-model rows | **412** |
| component-model rows | **608** |
| model-summary rows | **4** |

### Model Summary (4 architectures)

| model | GLOBAL Dice | Phase13 Pred | H2A Pred | ORACLE Dice | H2A-Global | H2A-P13 | Retention |
|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.302314 | 0.313779 | 0.724722 | -0.280400 | +0.011466 | -2.1480 |
| Attention U-Net | 0.629805 | 0.308619 | 0.320173 | 0.699595 | -0.309632 | +0.011554 | -4.4367 |
| UNet++ | 0.640516 | 0.311355 | 0.323046 | 0.726679 | -0.317470 | +0.011691 | -3.6845 |
| DeepLabV3+ | 0.560251 | 0.277292 | 0.288917 | 0.750372 | -0.271334 | +0.011625 | -1.4272 |

### Cross-Architecture Consistency

| metric | value |
|---|---|
| cases improved vs GLOBAL in all 4 | 3 |
| cases non-worse vs GLOBAL in all 4 | 3 |
| cases worse vs GLOBAL in all 4 | 83 |
| cases improved vs Phase13 in all 4 | 37 |
| cases worse vs Phase13 in all 4 | 38 |
| components recovered vs GLOBAL by >=1 model | 29 |
| components recovered vs GLOBAL by all 4 | 5 |
| components lost vs GLOBAL by >=1 model | 1 |
| components lost vs GLOBAL by all 4 | 0 |

### Key Observations (descriptive only)

- H2A predicted-region Dice is **substantially lower than GLOBAL** for all 4 models (macro Dice deficits
  approximately -0.271 to -0.317), with large positive FP burden relative to GLOBAL.
- H2A is **higher than Phase13 predicted** for all 4 models (+0.011 to +0.012), demonstrating downstream
  translation of the localizer-level improvement.
- The oracle-benefit retention is **negative** across all models, indicating H2A does not recover the
  full oracle-to-global gap.
- **83 cases are worse than GLOBAL in all 4 models simultaneously**, while only 3 cases improve in all 4.
- **29 components are recovered by at least one model** (5 by all 4), with only 1 component lost by >=1 model.

### Counters

| counter | value |
|---|---|
| new localizer training | 0 |
| localizer forwards | 0 |
| proposal regeneration | 0 |
| new global segmentation forwards | 0 |
| regional segmentation models | 4 (frozen) |
| regional crop evaluations | 1828 |
| oracle reruns | 0 |
| threshold searches | 0 |
| proposal grids | 0 |
| TEST reads | 0 |
| external TEST reads | 0 |

### Artifacts

`reports/audits/post_phase13_h2a_downstream_integrity.{json,md}` ·
`reports/tables/post_phase13_h2a_downstream_case_model_metrics.csv` (412 rows) ·
`reports/tables/post_phase13_h2a_downstream_component_model_metrics.csv` (608 rows) ·
`reports/tables/post_phase13_h2a_downstream_model_summary.csv` (4 rows) ·
`reports/tables/post_phase13_h2a_downstream_cross_architecture_summary.csv` ·
`reports/tables/post_phase13_h2a_localizer_to_downstream_comparison.csv` ·
notebook `post_phase13_h2a_downstream_analysis.ipynb` — READ-ONLY, 31 sections, 55 cells / 25 code,
Run-All **0 unexecuted / 0 errors**, complete tables rendered untruncated (4/4 summary, 412/412
case-model, 608/608 component-model), SHA stable x3 `97ad366a6a2fb4f34a506829923363fb3700794b285920186f544781d6543fa7`.

### Completion State

H2A protocol: **COMPLETE / PASS / FROZEN** · H2A-B1: **COMPLETE / PASS / FROZEN** ·
H2A-B2 downstream: **COMPLETE / PASS / FROZEN** · H2A outcome: **ELIGIBLE_FOR_SUPERVISOR_ADJUDICATION / NOT AUTHORIZED** ·
H2 loss/target redesign: **NOT_STARTED** · H3: **NOT_STARTED** · Phase14: **NOT_STARTED** ·
TEST: **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2A_OUTCOME_ADJUDICATION_AUTHORIZATION`

---

## H2-A-C — Formal H2A Outcome Adjudication — COMPLETE / PASS

Adjudicated from frozen evidence only (0 training / 0 CUDA / 0 forwards / 0 new search /
0 TEST reads). Integrity precondition **PASS** on every required field.

Dimensions (4, no score / no rank / no numerical success threshold):

| id | dimension | adjudicated_state | supports_h2a |
|---|---|---|---|
| A | LOCALIZER_PROPOSAL_QUALITY | MEANINGFUL_LOCALIZER_LEVEL_IMPROVEMENT_DESCRIPTIVELY_VERIFIED | YES_LOCALIZER_LEVEL_ONLY |
| B | DOWNSTREAM_GLOBAL_PRESERVATION | GLOBAL_PRESERVATION_NOT_RESTORED | NO |
| C | REGIONAL_UTILITY | REGIONAL_UTILITY_NOT_RETAINED | NO |
| D | CROSS_ARCHITECTURE_GENERALITY | CONSISTENT_BUT_INSUFFICIENT__FAILURE_ALSO_CROSS_ARCHITECTURE | PARTIAL_LOCALIZER_LEVEL_ONLY |

**H2A OUTCOME: `H2A_SELECTION_REDESIGN_PARTIAL`.**
Checkpoint selection contributed: **YES** · alone sufficient: **NO** ·
fusion failure proven: **NO** · localizer representation failure proven: **NO**.

B2 causal-language clarification: **NOT_REQUIRED** (no persisted sole-causal wording found;
no frozen evidence rewritten).

### Artifacts

`reports/audits/post_phase13_h2a_outcome_adjudication.{json,md}` ·
`reports/tables/post_phase13_h2a_outcome_adjudication.csv` (exactly 4 rows).

### Completion State (post-adjudication)

Phase13: **COMPLETE / FROZEN** · original gate: **REVISE_LOCALIZER / FROZEN** ·
H1: **CLOSED__PARTIAL_MITIGATION_INSUFFICIENT** · H2A-B1: **COMPLETE / PASS / FROZEN** ·
H2A-B2: **COMPLETE / PASS / FROZEN** · H2A adjudication: **COMPLETE / PASS** ·
H2A: **CLOSED__SELECTION_REDESIGN_PARTIAL** · H2B protocol design: **ELIGIBLE / NOT AUTHORIZED** ·
H2B training: **NOT AUTHORIZED** · H3: **FUTURE_AXIS / NOT AUTHORIZED** ·
Phase13 Part1B-R0 thread: **HISTORICAL / STALE — NOT RESUMED** ·
Phase14: **NOT_STARTED** · TEST: **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2B_PROTOCOL_DESIGN_AUTHORIZATION`


---

## H2-A-C — Supervisor Adjudication Verification + Continuity Lock — COMPLETE / PASS

Verification-only task. No training, no inference, no new scientific search.
Zero execution: training 0 · optimizer 0 · model constructions 0 · CUDA 0 ·
localizer forwards 0 · segmentation forwards 0 · proposal generation 0 · TEST reads 0 ·
external TEST reads 0.

### B1 / B2 verification

- B1 `post_phase13_h2a_training_evaluation.json` **PASS** · best epoch 83 ·
  best.pt `2e2e8f79…` · trajectory PASS · selection replay PASS
- B2 `post_phase13_h2a_downstream_integrity.json` **PASS** · 457 proposals · 1828 regional ·
  0 localizer forwards · 0 proposal regeneration · 0 TEST · 0 external TEST
- model summary: **4 rows**

### Existing H2-A-C artifact

`reports/audits/post_phase13_h2a_outcome_adjudication.{json,md}` ·
`reports/tables/post_phase13_h2a_outcome_adjudication.csv`

**EXISTING_H2A_C_ADJUDICATION: VERIFIED_AND_ACCEPTED_BY_SUPERVISOR.**
Scientific content matched exactly (`H2A_SELECTION_REDESIGN_PARTIAL`, 0 new thresholds,
no winner, no TEST, no Phase14 authorization, H2B protocol design eligible only).
Material scientific difference: **NONE** · CHECK_REQUIRED: **NO**.

Two provenance bindings were re-pointed (additive, non-scientific) so the artifact binds the
**final** B1/B2 evidence, following the immediately-preceding authorized B2 repair task:

| binding | superseded | current |
|---|---|---|
| `b2_integrity_sha` | `0c3b1175…` | `c80a5b7d…` |
| `b2_reviewer_notebook_sha` | `a6db814c…` | `97ad366a…` |

All 10 bindings now resolve. Frozen scientific tables byte-identical.

### Dimension states (supervisor-frozen)

| id | dimension | state |
|---|---|---|
| A | LOCALIZER_PROPOSAL_QUALITY | IMPROVED_BUT_MODEST |
| B | DOWNSTREAM_GLOBAL_PRESERVATION | NOT_RESTORED |
| C | REGIONAL_UTILITY | PARTIAL |
| D | CROSS_ARCHITECTURE_GENERALITY | CONSISTENT_PARTIAL_IMPROVEMENT |

### B1 crosscheck limitation (preserved)

`NONBLOCKING_SECONDARY_INTEGRITY_CHECK_UNAVAILABLE` — 68 overlapping epochs reproduce the
loss/LR trajectory to machine precision, supporting unchanged gradient semantics. Direct
model-tensor equality at epochs 31/53/68 unavailable (snapshots not retained).
No mathematical proof of identical model tensors claimed. Does not change the H2A outcome.

### H2A closure

H2A protocol / B1 / B2: **COMPLETE / PASS / FROZEN** · outcome: **H2A_SELECTION_REDESIGN_PARTIAL** ·
**H2A: CLOSED**. No further threshold search · no alternate checkpoint search ·
no combination with R1 selective acceptance.

### Next frontier

`H2B_PROTOCOL_DESIGN`: **ELIGIBLE / NOT AUTHORIZED** · `H2B_TRAINING`: **NOT AUTHORIZED** ·
**H2B axis selected: NONE** (no axis decided in this task; no multiple-axis experiment authorized) ·
`H3`: **NOT_STARTED / FUTURE_AXIS / NOT AUTHORIZED** ·
`Phase14`: **NOT_STARTED** · `TEST`: **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2B_PROTOCOL_DESIGN_AUTHORIZATION`

---

## H2-B-A — Objective-Only Localizer Redesign Protocol — COMPLETE / PASS / FROZEN

**Axis:** `H2B_SOFT_TARGET_FOCAL_BCE_OBJECTIVE_ONLY` — exactly ONE new scientific axis:
**LOSS / OBJECTIVE SEMANTICS**.

**Experiment id:** `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3` — collision **NONE**.

### Frozen objective

`SoftTargetFocalBCE(gamma=2.0)` — `src/losses/soft_target_focal_bce.py`

```
L = mean( |sigmoid(z) - y|^2 * BCEWithLogits(z, y) )     # gamma = 2.0 FIXED
```

Modulation **NOT detached** (gradients flow through BCE **and** modulation). Target asserted
finite and in [0,1] — never silently clamped. No grid, no alpha/beta sweep, no coefficient search.
gamma=2 fixed prospectively; optimality NOT claimed.

### One-axis diff vs H2A (52 fields)

Changed: **2** scientific-axis (`loss_name`, `loss_mathematical_semantics`) +
**3** provenance (`experiment_id`, `protocol_binding`, `loss_implementation_sha`).
Everything else **UNCHANGED**: architecture · head · target · sigma · data · augmentation ·
optimizer · scheduler · checkpoint selection · proposal config · fusion · segmentation threshold.

### Synthetic loss/gradient audit (CPU-only)

All checks PASS — finite losses/gradients (no NaN/Inf) · y=0 increases as p→1 · y=1 increases as
p→0 · soft target minimised at/near p=y · symmetry `L(y=0,q)=L(y=1,1−q)` (max diff 4.77e-7) ·
modulation not detached · out-of-range and non-finite targets rejected.
35 rows. 0 model constructions · 0 CUDA · 0 project images/masks.

### Artifacts

`reports/audits/post_phase13_h2b_protocol_frozen.{json,md}` ·
`reports/audits/post_phase13_h2b_soft_target_focal_loss_unit_audit.{json,md}` ·
`reports/tables/post_phase13_h2b_soft_target_focal_gradient_sanity.csv` (35 rows) ·
`reports/tables/post_phase13_h2b_protocol_diff_vs_h2a.csv` (52 rows) ·
`reports/tables/post_phase13_h2b_evidence_contract.csv` (4 rows) ·
`src/losses/soft_target_focal_bce.py`

### Completion state

Phase13 **COMPLETE / FROZEN** · original gate **REVISE_LOCALIZER / FROZEN** · H1 **CLOSED** ·
H2A **CLOSED__SELECTION_REDESIGN_PARTIAL** · H2B protocol **COMPLETE / PASS / FROZEN** ·
H2B-B1 execution **ELIGIBLE / NOT AUTHORIZED** · H2B-B2 **NOT_STARTED** ·
H3 **FUTURE_AXIS / NOT AUTHORIZED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

Zero execution: training 0 · optimizer 0 · localizer model constructions 0 · CUDA 0 ·
localizer forwards 0 · proposal generation 0 · segmentation constructions 0 ·
segmentation forwards 0 · TEST reads 0 · external TEST reads 0.

next_action: `WAIT_FOR_SUPERVISOR_H2B_B1_EXECUTION_AUTHORIZATION`

---

## H2-B-B1 — Objective-Only Localizer Training — COMPLETE / PASS

**Axis:** LOSS / OBJECTIVE ONLY · `SoftTargetFocalBCE(gamma=2.0)` · experiment
`post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`

### Training

- **FRESH_FROM_SCRATCH_SEED42** · WARM_START NO · PRETRAINED_LOCALIZER_STATE NONE
- completed epochs **46** · termination **EARLY_STOPPING_PATIENCE** · **best epoch 31**
- best six-term tuple `[0.3762759719105191, 0.6111111111111112, 0.5921052631578947,
  0.2151639344262295, -0.005777940678754472, -0.000277110381060853]`
- best.pt `a9147ad7…` · latest.pt · history `ce8512ff…`
- **Selection replay PASS** — 0 mismatches, max abs term diff 7.2e-17, best epoch 31
- **No loss-trajectory gate vs H2A** (SEC 11: objective changed)

### Best-checkpoint standalone evaluation (103 VAL cases / 152 components)

| metric | H2B best | H2A best | Δ H2B−H2A |
|---|---|---|---|
| proposals | 488 | 457 | +31 |
| pixel any-hit precision | 0.215164 | 0.275711 | −0.060547 |
| bbox any-hit precision | 0.213115 | 0.273523 | −0.060408 |
| tiny recall90 | 0.611111 | 0.694444 | −0.083333 |
| overall recall90 | 0.592105 | 0.638158 | −0.046053 |
| overall recall50 | 0.697368 | 0.822368 | −0.125000 |
| any-overlap recall | 0.736842 | 0.875000 | −0.138158 |
| mean coverage | 0.677809 | 0.787897 | −0.110088 |
| score max | 0.108756 | 0.141637 | −0.032882 |
| score IQR | **0.000000** | 0.001654 | −0.001654 |
| fraction at max | 0.793033 | 0.645514 | +0.147519 |
| ROC-AUC | 0.614907 | 0.701110 | −0.086203 |
| PR-AUC | 0.228953 | 0.372936 | −0.143983 |

Head diagnostics (DIAGNOSTIC ONLY): 16/16 weights negative, mean −0.16419, bias −2.10409,
`sigmoid(bias)=0.10870`, **score IQR 0.0** → proposal scores fully saturated at the epoch max.

**Descriptive only — no superiority claim, no significance language, no checkpoint re-selection.**

### Execution-provenance repair (R0) applied before this run

Pre-fix attempt (4 epochs) invalidated as
`STALE_OBJECTIVE_IDENTITY_METADATA_IN_CHECKPOINT_AND_RESUME_CONTRACT` and archived to
`reports/superseded/post_phase13_h2b_b1_invalidated_pre_fix_attempt_20260923T0936Z/`.
Stale `loss_alpha`/`loss_beta` removed from resume contract + checkpoint metadata; H2B objective
identity bound; `zero_denominator_rule` wording reconciled. 43/43 repair tests PASS.
`logical_scientific_experiment_count = 1`; `execution_attempt_count = 2`.

### Artifacts

`reports/audits/post_phase13_h2b_b1_training_evaluation.{json,md}` ·
`post_phase13_h2b_b1_selection_replay_verification.{json,md}` ·
`post_phase13_h2b_best_checkpoint_standalone_evaluation.json` ·
`reports/tables/post_phase13_h2b_best_checkpoint_{case_proposals,proposals,component_coverage,size_stratified}.csv` ·
`reports/tables/post_phase13_h2b_vs_h2a_localizer_comparison.csv` ·
notebook `post_phase13_h2b_localizer_training_review.ipynb` — READ-ONLY, 30 sections,
56 cells / 26 code, Run-All **0 unexecuted / 0 errors**, complete 46/46-epoch table untruncated,
SHA stable ×3 `2fc28742580aede858886b2658dad4db59d59e348a7ff1b3abcd944582c66965`.

### Completion state

H2B protocol **COMPLETE / PASS / FROZEN** · H2B-B1 training **COMPLETE / PASS** ·
H2B standalone localizer evaluation **COMPLETE / PASS** ·
H2B-B2 **ELIGIBLE_FOR_SUPERVISOR_REVIEW / NOT AUTHORIZED** ·
H2B outcome **NOT_ADJUDICATED** · representation/head redesign **NOT_STARTED** ·
H3 **NOT_STARTED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

Downstream segmentation forwards 0 · proposal grid 0 · threshold searches 0 ·
oracle reruns 0 · TEST reads 0 · external TEST reads 0.

next_action: `WAIT_FOR_SUPERVISOR_H2B_B2_AUTHORIZATION`

---

## H2-B-B2 — Downstream Regional Segmentation Evaluation — COMPLETE / PASS

Run id: `post_phase13_h2b_downstream_best_native_policy`
Frozen input: **488** H2B best-checkpoint (epoch 31) proposals · 103 VAL cases · 152 components
Compute: 488 × 4 = **1952** regional crop evaluations · 0 localizer forwards · 0 proposal
regeneration · 0 new global forwards · 0 threshold search · TEST 0.

### Results (descriptive — NOT adjudicated)

| model | GLOBAL | Phase13 | H2A | **H2B** | Oracle | H2B−GLOBAL | H2B−Phase13 | H2B−H2A | retention |
|---|---|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.302314 | 0.313779 | **0.279848** | 0.724722 | −0.314331 | −0.022465 | −0.033931 | −2.407893 |
| Attention U-Net | 0.629805 | 0.308619 | 0.320173 | **0.290569** | 0.699595 | −0.339236 | −0.018050 | −0.029604 | −4.860838 |
| UNet++ | 0.640516 | 0.311355 | 0.323046 | **0.294688** | 0.726679 | −0.345827 | −0.016667 | −0.028358 | −4.013603 |
| DeepLabV3+ | 0.560251 | 0.277292 | 0.288917 | **0.264614** | 0.750372 | −0.295637 | −0.012678 | −0.024303 | −1.554992 |

**H2B is below GLOBAL, Phase13 and H2A on all four architectures.** Oracle-benefit retention is
negative for all four. Cross-architecture: improved vs GLOBAL in all4 = **2**, worse in all4 = **87**;
improved vs H2A in all4 = 31, worse vs H2A in all4 = 51; components recovered vs GLOBAL by ≥1 = 22
(by all4 = 3); lost vs GLOBAL by ≥1 = **0** (by all4 = 0).

### Artifacts

`reports/audits/post_phase13_h2b_b2_downstream_integrity.{json,md}` ·
`reports/tables/post_phase13_h2b_downstream_case_model_metrics.csv` (412) ·
`post_phase13_h2b_downstream_component_model_metrics.csv` (608) ·
`post_phase13_h2b_downstream_model_summary.csv` (4) ·
`post_phase13_h2b_downstream_cross_architecture_summary.csv` (11) ·
`post_phase13_h2b_localizer_to_downstream_comparison.csv` (4) ·
notebook `post_phase13_h2b_downstream_analysis.ipynb` — READ-ONLY, 33 sections, 64 cells / 31 code,
Run-All **0 unexecuted / 0 errors**, complete tables untruncated (4/4, 412/412, 608/608),
SHA stable ×3 `40af2ee250478229fc6c0546afe9139d05407d4cf91462fef4be3dd91153de41`.

H2A downstream comparator: **AVAILABLE and included** (not invented).

### Completion state

H2B-B1 **COMPLETE / PASS / FROZEN** · H2B-B2 **COMPLETE / PASS** ·
H2B outcome **ELIGIBLE_FOR_SUPERVISOR_ADJUDICATION / NOT AUTHORIZED** ·
H2C **NOT_STARTED** · H3 **NOT_STARTED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION`

---

## H2B-B2 R — Quantitative Reporting Reconciliation — COMPLETE / PASS

**Classification: `CHAT_TRANSCRIPTION_ONLY`.**

The pasted H2B-B2 chat final note carried quantitative values absent from every persisted
artifact. The authoritative tables were always correct; the error existed only in the chat
transcript. No persisted quantitative artifact required correction.

### Stale (chat only) vs authoritative (disk)

| quantity | pasted chat | authoritative |
|---|---|---|
| recoveries/losses vs GLOBAL | 8/0 · 5/0 · 5/0 · 4/0 | **10/0 · 7/0 · 11/0 · 16/0** |
| fp_delta_vs_global | +7203.65 · +7410.66 · +7722.28 · +8083.96 | **+9625.621359 · +9857.815534 · +10507.456311 · +11031.233010** |
| mean_h2b_fp (UNet) | 8500.90 | **10922.873786** |

### Checks

- notebook vs model summary: **PASS**
- stale values found in persisted artifacts: **NO** (`8500.90` appears nowhere on disk)
- persisted H2B final-note artifact: **does not exist**
- authoritative tables modified: **NO** · frozen audits rewritten: **NO**
- continuity docs required correction: **NO** (they never carried the stale values)

Artifact: `reports/audits/post_phase13_h2b_b2_reporting_reconciliation.{json,md}`

### Preserved valid evidence (descriptive, unadjudicated)

H2B macro Dice below GLOBAL, Phase13 predicted and H2A predicted for all four architectures ·
component losses vs GLOBAL zero for all four · cross-architecture union recovery retained.

scientific result changed **NO** · B2 execution status changed **NO**.

next_action: `WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION`

---

## H2B — Outcome Adjudication — COMPLETE / PASS

**OUTCOME: `H2B_OBJECTIVE_REDESIGN_INSUFFICIENT`**

### Frozen H2B contract (recovered, not inferred)

`reports/audits/post_phase13_h2b_protocol_frozen.json` — uniquely identified.
Question: can a SOFT-TARGET objective improve heatmap discrimination and proposal precision while
preserving object coverage, holding everything else fixed? Changed axis: **LOSS / OBJECTIVE**
(1 field). Four prospective dimensions: A localizer proposal quality · B downstream global
preservation · C regional utility · D cross-architecture generality.
Frozen outcome space: `H2B_OBJECTIVE_REDESIGN_{SUFFICIENT,PARTIAL,INSUFFICIENT}` / `CHECK_REQUIRED`.

### Outcome-space definitional provenance

The protocol freezes the outcome **label list** but contains **no evidence→label decision
criteria**. The project's pre-existing frozen definitions (H2-A-C, identical label family) were
applied by inheritance; **no new criterion was invented**. The outcome is robust: SUFFICIENT is
unanimously excluded, and PARTIAL requires reproducible *favourable* localizer changes — H2B was
worse than H2A on **9/9** quality metrics, so PARTIAL cannot apply under any reading.

### Dimension states

| id | dimension | state | supports H2B |
|---|---|---|---|
| A | LOCALIZER_PROPOSAL_QUALITY | DEGRADED_RELATIVE_TO_H2A_BASELINE | NO |
| B | DOWNSTREAM_GLOBAL_PRESERVATION | GLOBAL_PRESERVATION_NOT_RESTORED__WORSE_THAN_GLOBAL | NO |
| C | REGIONAL_UTILITY | PARTIAL_RECOVERY_SIGNAL_RETAINED__NET_UTILITY_NOT_ACHIEVED | NO |
| D | CROSS_ARCHITECTURE_GENERALITY | CONSISTENTLY_UNFAVOURABLE_ACROSS_ALL_FOUR_ARCHITECTURES | NO |

### Preserved favourable evidence

Component recoveries vs GLOBAL 10 / 7 / 11 / 16 · losses vs GLOBAL **0** for all four ·
recovered by ≥1 architecture **22** (by all four 3) · lost by ≥1 architecture **0**.

### Artifacts

`reports/audits/post_phase13_h2b_outcome_adjudication.{json,md}` ·
`reports/tables/post_phase13_h2b_outcome_adjudication.csv` (exactly 4 rows).

H2B proves sole cause: **NO** · winner **NONE** · selected threshold **NONE** ·
new thresholds 0 · new configs 0 · new subgroups 0.

### Continuity

H2B-B1 **COMPLETE / FROZEN** · H2B-B2 **COMPLETE / PASS / FROZEN** ·
H2B reporting reconciliation **COMPLETE / PASS** · H2B outcome adjudication **COMPLETE / PASS** ·
H2B **CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT** ·
H2C protocol design **ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION** · H2C execution **NOT AUTHORIZED** ·
H3 **NOT_STARTED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED** ·
original Phase13 gate preserved as **REVISE_LOCALIZER / FROZEN**.

next_action: `WAIT_FOR_SUPERVISOR_H2C_PROTOCOL_DESIGN_AUTHORIZATION`

---

## H2-C — Head / Representation Redesign Protocol — COMPLETE / PASS / FROZEN

**Axis (exactly ONE):** `LOCALIZER_PREDICTION_HEAD_ARCHITECTURE` (`CHANGE_H2C_001`).
Branches from the **H2A** baseline (H2A focal objective) — **not** from H2B. H2B is CLOSED and not
combined; H2C must not be described as "H2B plus a new head".

Experiment id: `post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3` — collision **NONE**.

### Old head (physically verified)

`nn.Conv2d(16, 1, kernel_size=1, stride=1, padding=0, bias=True)` — no spatial mixing ·
**17 params** · weight ALL ZERO · bias `log(0.1/0.9)` · output `(1,1,128,128)` · internal sigmoid **NONE**.

### New head — ONE variant only

`SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1`
`Conv2d(16→16, k=3, p=1)` → `ReLU(inplace=False)` → `Conv2d(16→1, k=1)` · hidden width **16**
(no search) · no norm/dropout/attention/residual/multi-scale/deep-supervision.

Init: conv3x3 kaiming/0 · conv1x1 weight **ALL ZERO** · conv1x1 bias `logit(0.1) = -2.1972245773362196`.
Measured initial logit spread (max−min) = **0.0** → spatially constant, as intended.

### Parameter contract

| quantity | value |
|---|---|
| old head | 17 |
| new head | 2337 |
| absolute delta | +2320 |
| whole-model old | 482449 |
| whole-model H2C | 484769 |
| increase | 0.480880% |

All new trainable parameters belong to the head; backbone parameter shapes UNCHANGED.

### Diff vs H2A (40 fields)

Changed: **4** — 2 provenance (`experiment_id`, `protocol_binding`) + 2 scientific-axis rows
(`head_architecture`, `head_initialization`) belonging to the **single** change id
`CHANGE_H2C_001`. LOSS · TARGET · SIGMA · BACKBONE · OPTIMIZER · DATA · AUGMENTATION ·
CHECKPOINT_SELECTION · PROPOSAL_POLICY · FUSION · SEGMENTATION_CHECKPOINTS all **UNCHANGED**.

### Outcome definitions frozen prospectively

`H2C_HEAD_REDESIGN_{SUFFICIENT,PARTIAL,INSUFFICIENT}` + `CHECK_REQUIRED` — each with an explicit
evidence-to-label definition frozen **before** execution (addressing the H2B gap where labels were
frozen without a mapping). No numerical thresholds, no weighted score, no winner.

### Artifacts

`reports/audits/post_phase13_h2c_protocol_frozen.{json,md}` ·
`reports/tables/post_phase13_h2c_protocol_diff_vs_h2a.csv` (40 rows) ·
`post_phase13_h2c_evidence_contract.csv` (4 rows) ·
`post_phase13_h2c_outcome_definitions.csv` (4 rows).

### Completion state

Phase13 **COMPLETE / FROZEN** · original gate **REVISE_LOCALIZER / FROZEN** · H1 **CLOSED** ·
H2A **CLOSED__SELECTION_REDESIGN_PARTIAL** · H2B **CLOSED__OBJECTIVE_REDESIGN_INSUFFICIENT** ·
H2C protocol **COMPLETE / PASS / FROZEN** · H2C-B1 **ELIGIBLE / NOT AUTHORIZED** ·
H2C-B2 **NOT_STARTED** · H3 **NOT_STARTED** · Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

Zero execution: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · localizer forwards 0 ·
proposal generation 0 · segmentation forwards 0 · regional forwards 0 · checkpoint writes 0 ·
TEST reads 0 · external TEST reads 0.

next_action: `WAIT_FOR_SUPERVISOR_H2C_B1_AUTHORIZATION`

---

## H2-C B0 — RNG-Equivalence + Execution-Provenance Preflight — COMPLETE / PASS

**RNG classification: `RNG_STREAMS_ALREADY_ISOLATED`** · execution fix required: **NO** · no
executable training semantics changed.

### Stream ownership (physical)

| stream | owner |
|---|---|
| model initialization | torch global RNG (`nn.init.kaiming_normal_`) |
| shuffle | dedicated `torch.Generator` seeded with 42 (per DataLoader, `make_generator(seed)`) |
| augmentation | Python `random` module (global) — a separate stream from torch |
| worker | `seed_worker()` from `torch.initial_seed()`; `num_workers=0` so unused |
| VAL ordering | deterministic sequential (`shuffle=False`) |
| numpy | seeded by `set_seed` but NOT consumed by augmentation |

`set_seed(seed, deterministic=True)` at runner line 1261 precedes model construction (line 1341).
The extra H2C kaiming draws advance only the **torch global RNG**, which no downstream stream
consumes — no `torch.rand/randn/normal` or `Dropout` exists on the training path.

### Empirical equivalence (CPU-only; no image decoded, no model forward)

| check | result | hash H2A | hash H2C |
|---|---|---|---|
| TRAIN order (770 indices) | **TRUE** | `a7005312…` | `a7005312…` |
| VAL order | **TRUE** | `f5e37d72…` | `f5e37d72…` |
| augmentation RNG trace | **TRUE** | `53d3baec…` | `53d3baec…` |

Python random state, numpy state, train generator and val generator states all equivalent.
`torch_global_rng_state_equivalent = False` — **expected and inert** (unused downstream).

### Terminal zero-weight note

`FROZEN_INITIALIZATION_CONSEQUENCE` / `NOT_A_PROTOCOL_DEFECT` — the hidden 3x3 may receive zero
gradient through the zero terminal weights on the first backward pass until the terminal layer
updates. Intentional; no warmup, no optimizer change, no initialization change.

### Counter clarification (additive — frozen protocol NOT rewritten)

`reports/audits/post_phase13_h2c_preexecution_counter_clarification.{json,md}`
PROJECT_DATA_MODEL_FORWARDS **0** · TRAINING_FORWARDS **0** · VAL_FORWARDS **0** · TEST_FORWARDS **0** ·
SYNTHETIC_SHAPE_CHECK_FORWARDS **1** (synthetic input only, no CUDA, no trained weights, not a
scientific measurement).

### Artifacts

`reports/audits/post_phase13_h2c_rng_equivalence_preflight.{json,md}` (`aa5a9b7a…` / `5f9ae5cd…`) ·
`reports/audits/post_phase13_h2c_preexecution_counter_clarification.{json,md}` (`5c715229…`).

### Change register after preflight

HEAD_ARCHITECTURE_CHANGED **YES** · HEAD_INITIALIZATION_CHANGED **YES (same frozen head axis)** ·
LOSS/TARGET/SIGMA/BACKBONE/OPTIMIZER/SCHEDULER/DATA/SPLIT/AUGMENTATION_DISTRIBUTION/
TRAIN_ORDER_SEMANTICS/CHECKPOINT_SELECTION/PROPOSAL_POLICY/FUSION all **NO** ·
SECOND_SCIENTIFIC_AXIS **NONE**.

Zero scientific execution: training epochs 0 · optimizer steps 0 · checkpoint writes 0 ·
project TRAIN forwards 0 · project VAL forwards 0 · TEST reads 0 · external TEST reads 0.

next_action: `WAIT_FOR_SUPERVISOR_H2C_B1_EXECUTION_AUTHORIZATION`

---

## H2-C-B1 — Frozen Localizer-Head Training + Standalone Evaluation — COMPLETE / PASS

**Axis (1):** `LOCALIZER_PREDICTION_HEAD_ARCHITECTURE` (`CHANGE_H2C_001`) — incl. its frozen init.
Branches from **H2A**; retains the H2A `CenterNetFocalLoss(alpha=2.0, beta=4.0)` objective.

### Training

- 72 epochs · **EARLY_STOPPING_PATIENCE** · **best epoch 57**
- best tuple `[0.4598833654705356, 0.75, 0.6973684210526315, 0.2662337662337662,
  -0.005357889447390799, -1.7253184639490569]`
- best.pt `021ab63f…` · history `09ae6546…`
- **Selection replay PASS** — 0 mismatches, max abs term diff 9.9e-17, final bad_epochs 15

### Standalone best-checkpoint (103 VAL / 152 components)

| metric | H2C | H2A | Δ |
|---|---|---|---|
| proposals | 462 | 457 | +5 |
| pixel any-hit precision | 0.266234 | 0.275711 | −0.009477 |
| bbox any-hit precision | 0.264069 | 0.273523 | −0.009454 |
| tiny recall90 | 0.750000 | 0.694444 | **+0.055556** |
| overall recall90 | 0.697368 | 0.638158 | **+0.059211** |
| any-overlap recall | 0.888158 | 0.875000 | +0.013158 |
| mean coverage | 0.808416 | 0.787897 | **+0.020519** |
| score max | 0.150903 | 0.141637 | +0.009265 |
| score IQR | 0.004663 | 0.001654 | **+0.003009** |
| fraction at max | 0.549784 | 0.645514 | **−0.095731** |
| ROC-AUC | 0.756421 | 0.701110 | **+0.055311** |
| PR-AUC | 0.412665 | 0.372936 | **+0.039729** |

Head at best checkpoint: hidden 3×3 non-degenerate (73.8 % positive, channel norms 1.55–1.78);
terminal 1×1 all negative (mean −0.0539); bias −1.7276. **Score saturation materially reduced**
(fraction-at-max 0.6455 → 0.5498; IQR 0.0017 → 0.0047) — the mechanism the redesign targeted.

Descriptive single-seed evidence only. **No winner, no superiority claim, no significance claim.**

### Material interpretation context

H2A and H2C heads produce **identical initial logits** (max−min 0.0, p = 0.1) and identical initial
loss 19.119539, but H2C learns more slowly at first (epoch-1 train_loss 10.039 vs H2A 0.001105) —
the disclosed `FROZEN_INITIALIZATION_CONSEQUENCE` of the zero terminal weights.
**Early-epoch loss magnitudes are not comparable across branches.**

### Disclosed defect (corrected additively)

`PERSISTED_REPORTING_DEFECT__AUTHORITATIVE_SCIENTIFIC_STATE_CORRECT` — the runner inherited
Phase-13 audit payload identity strings (mislabeled `artifact` / `protocol_identity` /
`scientific_changes: 0`). **Checkpoint is correct** (records H2C head identity + H2C protocol SHA +
the retained H2A focal objective). Runner fixed (audit strings only; all 22 machinery probes
unchanged); correction at `post_phase13_h2c_b1_audit_identity_correction.{json,md}`.
Scientific impact **NONE**; no restart warranted.

### Artifacts

`reports/audits/post_phase13_h2c_b1_training_evaluation.{json,md}` ·
`post_phase13_h2c_b1_selection_replay_verification.{json,md}` ·
`post_phase13_h2c_best_checkpoint_standalone_evaluation.json` ·
`reports/tables/post_phase13_h2c_best_checkpoint_{case_proposals(103),proposals(462),
component_coverage(152),size_stratified(5)}.csv` ·
`post_phase13_h2c_vs_h2a_vs_phase13_localizer_comparison.csv` (14) ·
notebook `post_phase13_h2c_localizer_training_review.ipynb` — READ-ONLY, 24 sections,
45 cells / 21 code, **0 unexecuted / 0 errors**, complete 72/72-epoch table untruncated,
SHA stable ×3 `b4d2021f1597cf9b3b028cbeeb0011a027b79e27a74b0eac72186aeca6cb85ad`.

### Completion state

H2C protocol **COMPLETE / PASS / FROZEN** · H2C RNG preflight **COMPLETE / PASS / FROZEN** ·
H2C-B1 training **COMPLETE / PASS** · H2C standalone localizer evaluation **COMPLETE / PASS** ·
H2C-B2 **ELIGIBLE_FOR_SUPERVISOR_REVIEW / NOT AUTHORIZED** · H2C outcome **NOT_ADJUDICATED** ·
Phase14 **NOT_STARTED** · TEST **UNTOUCHED**.

next_action: `WAIT_FOR_SUPERVISOR_H2C_B2_AUTHORIZATION`

---

## H2C-B2 — Downstream Regional Segmentation Evaluation + Adjudication — COMPLETE / PASS

Run id `post_phase13_h2c_downstream_best_native_policy` · authorization
`USER_SUPERVISOR_MESSAGE_POST_H2C_B1` = **GRANTED**.
Frozen input: **462** H2C epoch-57 proposals · 103 VAL cases / 152 components.
Compute: 462 × 4 = **1848** regional crops · 0 localizer forwards · 0 regeneration · 0 new global
forwards · 1 checkpoint candidate · TEST 0.

### Closure verification (pre-B2)

17/17 PASS — incl. best.pt SHA match, epoch 57, replay 0 mismatches, H2C head tensors present
(conv3x3 16×16×3×3), checkpoint records H2C head identity + H2C protocol SHA, retained H2A focal
objective, no post-freeze modification, no prior downstream consumption, TEST untouched, no grid/
search/oracle/second experiment, audit-identity correction present and confined to reporting.

### Results (Dice, from disk)

| model | GLOBAL | Phase13 | H2A | **H2C** | Oracle | H2C−GLOBAL | H2C−P13 | H2C−H2A | retention |
|---|---|---|---|---|---|---|---|---|---|
| UNet | 0.594180 | 0.302314 | 0.313779 | **0.300230** | 0.724722 | −0.293950 | −0.002084 | −0.013550 | −2.251764 |
| Attention U-Net | 0.629805 | 0.308619 | 0.320173 | **0.301089** | 0.699595 | −0.328716 | −0.007530 | −0.019084 | −4.710103 |
| UNet++ | 0.640516 | 0.311355 | 0.323046 | **0.304042** | 0.726679 | −0.336474 | −0.007313 | −0.019004 | −3.905048 |
| DeepLabV3+ | 0.560251 | 0.277292 | 0.288917 | **0.282357** | 0.750372 | −0.277894 | **+0.005065** | −0.006560 | −1.461668 |

Cross-arch: improved vs GLOBAL all4 **3** · worse all4 **82** · improved vs Phase13 all4 **44** ·
worse vs Phase13 all4 36 · improved vs H2A all4 **38** · worse vs H2A all4 45 ·
components recovered vs GLOBAL by ≥1 **33** (H2A: 22) · by all4 5 · lost by ≥1 **0** · by all4 **0**.

### Adjudication (frozen rule, applied verbatim)

**`H2C_HEAD_REDESIGN_INSUFFICIENT`** — clause (b): favourable localizer changes did not translate
into meaningful downstream improvement and the major deployable failure remains. The frozen PARTIAL
definition additionally requires "at least some corresponding downstream improvement" measured
against the protocol-designated **primary** downstream comparator (H2A); H2C macro Dice is below H2A
on **all four** architectures, so that clause fails.

**Disclosed as a CLOSE CALL.** Countervailing evidence recorded: H2C−Phase13 ≈ neutral
(DeepLabV3+ **improved** +0.005065), 38/103 cases improved in all four vs H2A, and components
recovered vs GLOBAL rose 22 → 33 with zero losses. A reader measuring "downstream improvement"
against Phase13 or at case level could reasonably argue PARTIAL.

### Artifacts

`reports/audits/post_phase13_h2c_b2_freeze_manifest.{json,md}` ·
`post_phase13_h2c_b2_downstream_integrity.{json,md}` ·
`post_phase13_h2c_b2_outcome_adjudication.{json,md}` ·
`post_phase13_h2c_b2_execution_audit.{json,md}` ·
`post_h2c_chain_closure_report.json` ·
`reports/tables/post_phase13_h2c_downstream_{case_model_metrics(412),component_model_metrics(608),
model_summary(4),cross_architecture_summary(11)}.csv` ·
`post_phase13_h2c_localizer_to_downstream_comparison.csv` ·
notebook `post_phase13_h2c_downstream_analysis.ipynb` — READ-ONLY, 19 sections, 37 cells / 18 code,
**0 unexecuted / 0 errors**, complete tables untruncated (4/4, 412/412, 608/608),
SHA stable ×3 `7eb813a66b28c83ff6710be57db2ed03ffd6cf3decaeeee46fc3ceab07b6aabd`.

### Final state

`H2C_B2_COMPLETE__H2C_ADJUDICATED__PHASE14_ELIGIBLE_NOT_STARTED`
H2C **CLOSED__HEAD_REDESIGN_INSUFFICIENT** · Phase14 **ELIGIBLE / NOT STARTED** · TEST **UNTOUCHED**.
Reporting-defect scientific impact **NONE**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE14_AUTHORIZATION`

<!-- PHASE26_SPEC_V1_0_REPAIR -->
## Phase26 specification repair — COMPLETE_FROZEN (2026-10-02)

**SUPERVISOR SPECIFICATION REPAIR** — `SUPERVISOR_SPECIFICATION_REPAIR__PHASE26_OPERATIONAL_REDEFINITION`
(revision `ra_medfilm_barr_phase26_integration_v1_0`; `science_changed = false`, `model_weights_changed = false`).

- Phase26 legacy roadmap title **"Full Four-Domain RA-MedFiLM-BARR Training"** =
  **PRESERVED_PROVENANCE** (`LEGACY_ROADMAP_TITLE`).
- Canonical Phase26 operational title = **Full Four-Domain RA-MedFiLM-BARR Integration & Canonical Bundle Freeze**.
- `phase26_training_required = false` · `phase26_training_mode = ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION`.
  Phase26 performs **NO new parameter optimization** (no training / no fine-tuning / no backward /
  no optimizer / no model forward). Canonical spec: [`docs/phase26_training_spec.md`](../docs/phase26_training_spec.md).
- All four learned components **FROZEN_NO_GRAD**: G (Phase21), R_psi (Phase25A ROI-0.30), B_phi (Phase25D),
  S_omega (Phase25F); fusion = deterministic. `trainable_parameter_set = EMPTY`.
- `training_population = NONE` (n=0) → **holdout contamination risk RESOLVED**.
- Canonical system variant = **A8/C9** · canonical budget = **25%** (= 0.25, DEV count 1239) ·
  canonical lambda representative = **0.25** (`MEMBERSHIP_EQUIVALENT__NOT_PERFORMANCE_SELECTED`).
- Exact final-router threshold bound (DEV-calibrated, budget 0.25 / lambda 0.25) in
  `reports/audits/phase26_canonical_router_threshold_binding_v1_0.json`.
- Completeness matrix repaired: `phase26_specification_completeness_v1_0.csv` = **49/49 defined, 0 blocking**.
- **Phase26 spec = COMPLETE_FROZEN** · **Phase26 = EXECUTION_ELIGIBLE_NOT_STARTED**.
- ROUTER_HOLDOUT = **RESERVED_UNOPENED_FOR_PHASE30** · VAL808 = UNOPENED · TEST = LOCKED UNTIL PHASE39 ·
  Phase30 = NOT_STARTED.

Terminal: `PHASE26_SPEC_V1_0_COMPLETE__MODULAR_INTEGRATION_NO_RETRAINING_AND_CANONICAL_25PCT_A8_POLICY_FROZEN__PHASE26_EXECUTION_ELIGIBLE_NOT_STARTED`.

<!-- PHASE29_SPEC_V1_1 -->
## Phase 29 specification — v1.1 (additive)

* Phase29 specification = `COMPLETE_FROZEN_V1_1`
* Phase29 = `EXECUTION_ELIGIBLE_NOT_STARTED`
* GlobalMedFiLM fixed across seeds
* BARR downstream stack seeds = 42 / 123 / 3407
* `ROUTER_HOLDOUT` remains Phase30 only
* TEST remains Phase39 only
* Original blocked terminal `PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED` preserved as provenance.
