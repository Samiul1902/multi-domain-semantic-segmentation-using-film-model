# MEMORY — Operational Continuity Handoff

## Phase25E policy evaluation complete — current state (2026-10-01)

Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: **COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: **COMPLETE_FROZEN**. Phase25F post-safety specification v1.0 (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN** (execution **COMPLETE_CANONICAL**). Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30). **Phase25 = COMPLETE_CANONICAL**; Phase26 = **ELIGIBLE_NOT_STARTED**.

The normalized incremental action cost is exactly `3,230,662,656 / 31,551,740,928` (`1051648/10270749`, approximately `0.10239253242387678`) for available actions; unavailable actions cost zero and are FORCED_SKIP. Pre-gate router overhead is `36,160` Conv/Linear MACs, separate from action cost. All compute is **ANALYTICAL MAC LOWER BOUND**, never measured latency.

Lambdas `{0.00, 0.25, 0.50, 1.00}` and budgets `{0%, 10%, 25%, 50%, 100%}` are frozen. All 4,957 DEV rows are action-available; exact top-K counts are `{0, 495, 1239, 2478, 4957}`. Rank by score descending, sample_id ascending. Random priorities (PCG64 seed 42) and 45 label-blind memberships were frozen before outcomes. Under constant action cost, C7 and C8 have **identical membership at every fixed budget and lambda**; they are not independent evidence.

The 45 frozen OOF memberships were joined to the frozen Phase25C paired-gain outcomes on ROUTER_DEVELOPMENT only (4957). Statistics (domain-stratified group bootstrap, 2000 replicates, seed 42) and final-router DEV thresholds were frozen **before** the outcome join. Result: under the frozen PRIMARY statistic (raw paired two-sided p), C7 **significantly beats every simple GT-free proxy on precision@budget at the 10% and 25% budgets**, the advantage shrinking to non-significance at 50% (Holm-Bonferroni retained only as a secondary sensitivity: 10%); preservation holds (macro-domain lower 95% CI bound > -0.005, no domain collapse); a usable accuracy-compute frontier exists. **H1 is scoped to the tight and medium budgets (10%/25%).**

The frozen final benefit-router checkpoint was loaded once and run in a single outcome-blind forward pass over the 4,957 ROUTER_DEVELOPMENT feature rows (no global-model forward, no regional-refiner forward, no training); no lambda was selected; the gate was not calibrated for deployment beyond the frozen DEV-score thresholds; C9 post-safety was not evaluated. ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39.

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





**Resume-in-5-minutes page.** Full detail: [MEMORY_ARCHIVE_pre_2026_09_30.md](MEMORY_ARCHIVE_pre_2026_09_30.md),
`.workbuddy-ai/memory/` (dated logs + `NOTES_ARCHIVE.md`), [ARCHITECTURE.md](ARCHITECTURE.md),
[DESIGN.md](DESIGN.md), [RULES.md](RULES.md), [PRD.md](PRD.md), [TASKS.md](TASKS.md).

**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)
**Method:** **RA-MedFiLM-BARR** (v1.1 architecture)

## STATUS

Phase 00–23 COMPLETE · **Phase 24 COMPLETE** · Phase 24 v1.1 historical · **Phase 24 v1.2
(router feature spec) COMPLETE** (D1+D2 adjudicated) · **Phase 25A COMPLETE canonical** ·
Phase 25A ROI-0.50 NONCANONICAL_PROTOCOL_DEVIATION (preserved only) · Phase 25B blocked
attempt BLOCKED_ATTEMPT_PROVENANCE · **Phase 25B COMPLETE canonical (202-D GT-free feature
cache frozen; handoff semantics repaired)** · **Phase 25C COMPLETE canonical (4957 OOF paired
refinement-gain labels frozen)** · **Phase 25D blocked attempt BLOCKED_ATTEMPT_PROVENANCE**
· **Phase 25D router training spec v1.2.1 COMPLETE frozen** · **Phase 25D
COMPLETE canonical** (5 CV folds + final refit + 4957 OOF predictions + notebook) · **Phase25E specification COMPLETE_FROZEN** · **Phase25E scientific policy evaluation COMPLETE_FROZEN** · Phase 25F post-safety specification COMPLETE_FROZEN (execution EXECUTION_ELIGIBLE_NOT_STARTED); Phase 25G NOT_STARTED · Phase 26+ roadmap
retained · **TEST CLOSED until Phase 39.**

## TERMINAL

Scientific terminal (Phase 25C):

```
PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED
```

Historical Phase25C governance terminal (superseded):

```
PHASE25C_GOVERNANCE_CLEANUP_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED
```

Historical Phase25D spec-repair terminal (before accepted training):

```
PHASE25D_ROUTER_TRAINING_SPEC_V1_2_1_COMPLETE__CV_CHECKPOINT_TARGET_NORMALIZATION_AND_FINAL_REFIT_RULES_FROZEN__PHASE25D_REENTRY_ELIGIBLE_NOT_STARTED
```

Phase 25D completion terminal:

```
PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN__PHASE25E_ELIGIBLE_NOT_STARTED
```

**Phase 25D is `COMPLETE canonical`.** 5 CV folds trained (best epochs: 37/34/139/199/80),
FINAL_ROUTER_EPOCHS = 80, 4957 OOF Delta_hat predictions frozen, final checkpoint saved.
OOF metrics: Huber 7.11e-05, MAE 0.00664, Pearson 0.300, R2 = 0.087657630443573 (≈0.088 to 3 decimals). Notebook 3x deterministic.
Blocked attempt preserved.

Phase 25E policy-evaluation terminal:

```
PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED
```

**Phase 25E scientific policy evaluation is `COMPLETE_FROZEN`.** 45 frozen OOF memberships joined to
frozen Phase25C outcomes on ROUTER_DEVELOPMENT only. S1/H1 = **PARTIAL** (significant vs all simple
GT-free proxies at 10% and 25% budgets under the frozen primary raw paired p; non-significant at 50%); S2 preservation satisfied; S3 frontier
measured; no domain collapse. No lambda selected; exactly one outcome-blind forward pass of the frozen final router over the DEV rows (no global-model or refiner forward, no training); holdout/VAL808/TEST untouched.
Phase 25F post-safety specification v1.0 is `COMPLETE_FROZEN`; Phase 25F execution is `COMPLETE_CANONICAL`.

(Superseded: `PHASE25B_HANDOFF_SEMANTICS_REPAIRED__PHASE25C_OOF_PAIRED_GAIN_LABEL_GENERATION_ELIGIBLE_NOT_STARTED`.)

## DOWNSTREAM STAGE OWNERSHIP (verified 2026-10-01; Phase25D COMPLETE canonical)

- **Phase 25C = OOF paired refinement-gain label generation — COMPLETE canonical.** Used
  fold-specific canonical ROI-0.30 refiners on untouched outer folds to compute leakage-safe OOF
  `Dice_global`, `Dice_candidate_refined`, `DeltaDice = Dice_cand - Dice_global`, and
  beneficial/harmful/neutral categories. GT used only for label creation. Did **NOT** train the
  router and did **NOT** train the task embedding. `global_model_forward_passes = 0` (Phase-25B
  global cache reused).
- **Phase 25D = benefit-router training.** Joined Phase-25B 202-D features + Phase-25C labels by
  `sample_id` and trained `BARRBenefitRouterV1` including its learned `Embedding(4,16)`
  (202 numeric + 16 task-embedding = 218 router input dims). The **16-D task embedding belongs
  to Phase 25D only.** Phase25D is **COMPLETE canonical**. It trained BARRBenefitRouterV1 and its learned Embedding(4,16).
- Phase 25C classification: `PHASE25C_EXECUTED_EVIDENCE`. Documentation/governance repair of
  Phase 25B was separately governed: `science_changed = false`, `feature_cache_changed = false`.
- **Interpretation discipline (Phase 25C).** Phase25C shows **strongly heterogeneous paired
  refinement gain**. Most samples are neutral under the pre-registered thresholds, while both
  beneficial and harmful cases exist. This heterogeneity motivates benefit-aware selective routing.
  Aggregate behaviour of earlier regional procedures belongs to prior Phase22 evidence and must not
  be conflated with the Phase25C OOF dedicated-refiner result.

## CANONICAL SHAs

- Phase25D canonical notebook: `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63`
- Phase25D final checkpoint: `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b`
- Phase25D OOF predictions: `837be08e569053676b71d1ab216ff604184b2b61df567cca45e6f8a5546d4441`
- Phase25D final history: `a5f1c8bc95da53fc8ba3cca794339a380c9354c3e4095f8fcd69a503edb39247`
- Phase25E scientific policy-evaluation notebook: `b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797` (3× byte-identical; 8/8 embedded PNG valid)
- Phase25E bootstrap plan: `data_cache/phase25e_barr_resource_gate_v1_0/phase25e_bootstrap_plan_v1_0.npz` (plan SHA `918e971cfe5ac20a0c2306548604938a1a31e4cab210cff255141d7e65f39861`)
- Phase25E final-router DEV thresholds: `reports/tables/phase25e_final_router_dev_thresholds.csv`
- PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `29518fc13f3de60113e1110a12a3f38bac5f54c246751503fe29e595f6dbe997`

- Phase-25A notebook `fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd`
- Phase-25A final refiner checkpoint `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109`
- Phase-21 global checkpoint `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7`
- Phase-25B notebook: `acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a` (3× byte-identical; pre-repair `11a1a62a…` retained as provenance)
- Phase-25B feature cache: `data_cache/phase25b_barr_pre_refinement_features_v1_2/` (4957 × 202)
- Phase-25C OOF label table: `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv` `fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f` (4957 rows)
- Phase-25C notebook: `564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613` (3× byte-identical; 8/8 embedded PNG valid)
- Phase-24 v1.1 provenance notebook `612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef`
- Phase-24 v1.2 notebook: `reports/audits/phase24_v1_2_notebook_determinism.json`

Costs: Global MedFiLM **3,523,001** params · BARRRegionalRefinerV1 **1,276,401** params /
**3.230663** GMAC · BARRBenefitRouterV1 **218** input dims / **36,801** trainable
params (linear core 36,353 = bookkeeping only); **TRAINED / FROZEN in Phase25D**.

## THRESHOLD SEMANTICS

```
ROI proposal        = 0.30  (bbox -> action_available / FORCED_SKIP)
segmentation output = 0.50  (final mask / Dice / IoU)
```

## HARD RULES

1. **TEST CLOSED** until Phase 39; metadata only; `test_reads = 0`.
2. **ROUTER_HOLDOUT outcomes CLOSED** until the designated one-shot evaluation.
3. **VAL808 continuity/development only** — not router training data.
4. **Never silently resolve a frozen-value conflict** — report `CHECK_REQUIRED`.
5. **Additive provenance only**; never rename/delete a frozen artifact without a migration record.
6. ROI 0.30 ≠ segmentation 0.50.
7. Router features are **pre-refinement + GT-free**; no refined features enter the router.
8. No architecture/hyperparameter change based on holdout outcomes.
9. **Blocked phase ⇒ no fake completion notebook.**
10. Completed scientific phase ⇒ **real executed notebook** (full epoch tables).
11. Incomplete specification ⇒ **STOP before execution**.
12. `RA-MedFiLM-BARR`; max novelty **Level 2**, scoped to the integrated GT-free paired-gain
    router. Forbidden: counterfactual / certified / causal / guaranteed.
13. Phase-21/22 baselines **TIED**; never write "FiLM caused +X".

## GOTCHAS

- **pandas object-dtype bool inversion** — cast to `bool` before `~` in fail-closed checks.
- **Assert artifact existence after builders** — exit code ≠ file on disk.
- **No notebook circular freeze dependency.**
- **Atomic checkpoint writes** (temp-then-rename).
- **Restore RNG on legitimate resume.**
- **Deterministic notebooks:** merge consecutive same-name `stream` outputs *before*
  normalising; also normalise `metadata.execution` + `0x…` addresses; fix Styler UUIDs.
  Never normalise scientific numeric content.
- **Harness tears down the process tree every ~2–3.5 h** — a clean log with no traceback is
  external teardown, not a crash. `tasklist` is not a liveness check.

## SEE ALSO

`reports/audits/antigravity_current_state.json` · `PROJECT_MASTER_PLAN.md` §7 ·
`notebooks/phasewise/PHASE_INDEX.md`.

**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULES.md](RULES.md) · [DESIGN.md](DESIGN.md) · [TASKS.md](TASKS.md)

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

<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->
## Canonical 00-43 Roadmap + Governance Synchronization — MEMORY.md (2026-10-04)

**Revision ID:** `RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43` — **DOCUMENTATION/GOVERNANCE ONLY** (`science_changed = false`, `model_weights_changed = false`, `scientific_execution_started = false`).

This block is **additive**. The original **00-40 / 41-phase scientific roadmap is PRESERVED verbatim** above (allocation unchanged, no phase renumbered, no historical result rewritten). It records: the current state **through Phase35 v1.0f**, the **Phase36-40** roadmap, the supervisor-adopted **Phase41-43** deployment extension (Stage E), and the canonical **00-43 (44-phase)** roadmap.


### RESUME-IN-5-MINUTES (handoff top) — 2026-10-04

**Where we are.** Documentation/governance synchronization only. **Phase35 = pre-execution source chain frozen at v1.0f; scientific execution NOT_STARTED; the v1.0f synthetic smoke is ELIGIBLE_NOT_STARTED.** **Phase36-40 = NOT_STARTED.** **Phase41-43 (Stage E) = NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION.**

**Hard locks (do not violate).** TEST locked until Phase39 (`test_reads = 0`); ROUTER_HOLDOUT = `OPENED_AND_FROZEN` (Phase30 one-shot consumed, do not re-open); VAL808 = consumed development benchmark (Phase27), do not re-open for tuning; Phase30 status qualifier is **retained verbatim** (`COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL`).

**Next action (blocked on supervisor).** A separate pre-execution work order is required before the v1.0f synthetic smoke may run. Do **NOT** run the smoke, Phase36, or any TEST work without authorization.

**Policy recap (unchanged).** All gates PASS before proceeding; on mismatch STOP with the specified terminal; never silently overwrite/repair frozen artifacts; additive provenance only.

### Phase35 v1.0f — canonical bindings

- **Phase35 v1.0f = PRE-EXECUTION ACTUAL-LOGITS EMPTY-MASK OBSERVABILITY REPAIR — COMPLETE (zero-execution).**
  Repairs the single defect that blocked the first v1.0e smoke
  (`V1_0E_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_INCOMPLETE`). Execution source
  `scripts/analysis/phase35_interpretability_execution_v1_0f.py` `6a6097f4…` supersedes v1.0e;
  the empty-mask fallback is now validated with the **ACTUAL logits from the SAME synthetic G
  forward** (`empty_mask_helper_check_insession_actual_logits`), comparison fixed at
  `atol=1e-7, rtol=0`. The zero-logit surrogate is **UNREACHABLE** from the reachable smoke path.
  All v1.0e numerical finite guards (8-stage order) and the G2 parameter-grad audit are preserved.
  Static preflight `db37af29…` = **112/112** (54 original + 25 cumulative + 5 v1.0e-guard
  preservation + 28 actual-logits); 75 predecessors byte-identical; unit tests 7/7; final check
  `85f65e0b…` = **35/35**; reviewer notebook `0b28cbf7…` (22 cells, 0 errors, 3× byte-identical).
  Terminal `63a34ca8…`:
  `PHASE35_PREEXECUTION_EMPTY_MASK_ACTUAL_LOGITS_REPAIR_V1_0F_COMPLETE__…__SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED`.
  **No scientific protocol change.** The v1.0f synthetic smoke is **NOT_STARTED**; scientific
  Phase35 execution is **NOT_STARTED**; Phase36 is **NOT_STARTED**. TEST remains locked until Phase39.


<!-- ROADMAP_EXTENSION_V1_0A__STAGE_E_RECONCILIATION -->
## Stage E Deployment Extension — Cross-Document Reconciliation (v1.0a, 2026-10-05)

**Revision ID:** `RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0A__00_TO_43_ADDITIVE_RECONCILIATION` — **DOCUMENTATION/GOVERNANCE ONLY** (`science_changed = false`, `model_weights_changed = false`, `scientific_execution_started = false`).

This block is **additive**. Everything above is **PRESERVED verbatim**. It repairs defect **D2** (`V1_0_CROSS_DOCUMENT_STAGE_E_TITLE_CHECK_FALSE_POSITIVE`): the v1.0 final check reported the Phase41/42/43 exact-title checks as PASS across documents, but the exact Stage E phase titles were actually present only in [PRD.md](PRD.md), [TASKS.md](TASKS.md) and `PROJECT_MASTER_PLAN.md`. This document restates the exact titles verbatim so the check becomes a true exact-substring check.

**Exact Stage E phase titles (canonical, authoritative spelling):**

| Phase | Exact canonical title | Status |
|---|---|---|
| 41 | **Deployment Engineering & Model Packaging** | NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION |
| 42 | **End-to-End Deployment Validation** | NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION |
| 43 | **Research Deployment Release, Monitoring & Maintenance** | NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION |

**Operational handoff (Stage E).** No Stage E work exists on disk. There is **no** packaged bundle, **no** deployment harness, **no** release artifact and **no** monitoring hook. A future Stage E run requires (a) an explicit supervisor work order, (b) a pre-execution protocol freeze, and (c) the frozen inference contract at packaging time (ROI threshold 0.30 ≠ segmentation threshold 0.50; router input = pre-refinement, GT-free, 218 dims). Stage E must **not** re-open TEST (Phase39-only), ROUTER_HOLDOUT (`OPENED_AND_FROZEN`) or VAL808 (consumed by Phase27).

**Status unchanged by this repair:** Phase35 pre-execution source chain frozen at v1.0f, scientific execution **NOT_STARTED**; Phases 36-40 **NOT_STARTED**; Phase 41-43 **NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION**; TEST locked until Phase39 (`test_reads = 0`).

<!-- ROADMAP_EXTENSION_V1_0B__ADOPTION_EXECUTION_DISTINCTION -->
## Canonical Roadmap v1.0b — Adoption vs Execution Authorization + Phase35 Identity (2026-10-05)

**Revision ID:** `RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0B__CANONICAL_GOVERNANCE_CLOSURE` — **DOCUMENTATION/GOVERNANCE ONLY** (`science_changed = false`, `model_weights_changed = false`, `scientific_execution_started = false`).

This block is **additive**. Everything above is **PRESERVED verbatim**. It closes the v1.0b governance invariants that the v1.0a content repair did not independently state in this document: the explicit **adoption-vs-execution-authorization distinction**, the **current Phase35 identity**, and the **KUB subgroup-semantics boundary**.

### Adoption vs execution authorization (canonical, non-contradictory)

- **Roadmap extension adoption:** the supervisor-adopted deployment extension of Phases **Phase41–Phase43** is part of the canonical **Phase00–Phase43 (44-phase)** roadmap. `roadmap_extension_adopted = true`.
- **Execution authorization:** `phase41_execution_authorized = false`, `phase42_execution_authorized = false`, `phase43_execution_authorized = false`.
- **Explicit distinction:** `ROADMAP_ADOPTION_DOES_NOT_AUTHORIZE_EXECUTION`. Adopting the roadmap is **not** authorizing execution. The project roadmap is adopted; Phases 41/42/43 have **not** been authorized to execute. These two statements are **not contradictory**.
- **Phase41** = `NOT_STARTED` / `NOT_AUTHORIZED_FOR_EXECUTION`.
- **Phase42** = `NOT_STARTED` / `NOT_AUTHORIZED_FOR_EXECUTION`.
- **Phase43** = `NOT_STARTED` / `NOT_AUTHORIZED_FOR_EXECUTION`.

### Current Phase35 identity (unchanged)

- **Phase35 title = Feature Attribution & Visual Interpretability.**
- **Phase35 revision = `ra_medfilm_barr_phase35_interpretability_v1_0f`.**
- **Phase35 synthetic smoke = `ELIGIBLE_NOT_STARTED`.**
- **Phase35 scientific execution = `NOT_STARTED`.**
- **Phase36 = `NOT_STARTED`.**

### KUB subgroup-semantics boundary (unchanged)

KUB **Kidney / Bladder / Ureteric** remain **subgroup metadata** — they are **not** segmentation mask classes and **not** semantic classes. No domain- or subgroup-derived information becomes a segmentation class.

### Protected state (unchanged)

TEST = `LOCKED_UNTIL_PHASE39` (Phase39 only); ROUTER_HOLDOUT = `OPENED_AND_FROZEN`; Phase30 status qualifier retained verbatim. No v1.0b document amendment authorizes any execution.

<!-- POST_FREEZE_RESEARCH_EXTENSION_V1_0 -->
## Post-Freeze Research Extension — Authoritative State (append-only) (2026-10-11)

**Revision ID:** `RA_MEDFILM_BARR_POST_FREEZE_EXTENSION_V1_0` — **DOCUMENTATION/PLANNING ONLY** (`science_changed = false`, `model_weights_changed = false`, `scientific_execution_started = false`, `scientific_delta = 0`).

**This block is additive.** Everything above is **PRESERVED verbatim**. The frozen **RA-MedFiLM-BARR V1** study (Phases 0–40 + manuscript release; final scope `MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY`; TEST evidence class `POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES`; Phase30 qualifier `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` retained verbatim) is **immutable historical evidence** and is never rewritten. A clearly separated **POST-FREEZE RESEARCH EXTENSION** begins here. All new work is `PLANNED` / `NOT_STARTED` / `ELIGIBILITY_PENDING`.

### Current authoritative state (2026-10-11)

- **Frozen RA-MedFiLM-BARR V1 study complete** (Phases 0–40 + manuscript release; final scope `MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY`). V1 is immutable.

**Available external datasets:**

- `D:\Softfors\final\external_test_ds\HAM10000`
- `D:\Softfors\final\external_test_ds\Stones_where_are_you-.v3i.coco-segmentation`
- `D:\Softfors\final\external_test_ds\CVC-ClinicDB`
- `D:\Softfors\final\external_test_ds\BrEaST-Lesions_USG-images_and_masks`

**Prior-use history (disclosed):**

- HAM10000 — used in older MedFiLM-Seg
- CVC-ClinicDB — used in older MedFiLM-Seg
- BrEaST-Lesions_USG — used in older MedFiLM-Seg
- Stones_where_are_you — no prior use identified in the supplied old report (this alone does NOT prove independence; explicit audit required)

**Recorded states:**

- External validation for current RA-MedFiLM-BARR = **NOT YET PERFORMED**
- Progression study for RA-MedFiLM-BARR = **PLANNED EXTENSION**
- Same-protocol baseline benchmark = **PLANNED EXTENSION**
- Next action = **EXT-01 (External Dataset Audit & Eligibility)**

**Never rewrite old memory entries — append only.**

<!-- EXT01_EXTERNAL_DATASET_AUDIT_V1_0 -->
## EXT-01 External Dataset Audit — COMPLETE (2026-10-11)

**Revision ID:** `RA_MEDFILM_BARR_EXT01_EXTERNAL_DATASET_AUDIT_V1_0` — **DOCUMENTATION/AUDIT ONLY** (`science_changed = false`, `scientific_delta = 0`). Read-only dataset audit; **no model inference, no training, no metrics**.

**EXT-01 status = COMPLETE.** **EXT-02 = NOT_STARTED** (not authorized). Original Phases 0–40 and frozen V1 remain unchanged.

### Resolved dataset statuses (supersede the earlier CANDIDATE / ELIGIBILITY_PENDING rows)

| Domain | Dataset | Seg GT | Candidate task | Compatibility | Prior use | Overlap | Eligibility | Study track |
|---|---|---|---|---|---|---|---|---|
| ISIC | HAM10000 (ISIC-2018 Task 3 input) | FOUND (10,015 binary masks) | 0 | EXACT_COMPATIBLE | PRIOR_RESEARCH_PROGRAM_USE | 0 exact; same ISIC namespace → CHECK_REQUIRED | SECONDARY_EXTERNAL_BENCHMARK_ELIGIBLE | TRACK_B_PRIOR_USED_EXTERNAL_BENCHMARK |
| KUB | Stones_where_are_you? v3 (Roboflow COCO-seg) | FOUND (polygons; class→binary rule not frozen) | 3 | DETERMINISTICALLY_MAPPABLE | NONE_IDENTIFIED (independence not proven) | 0 exact | ELIGIBILITY_PENDING | TRACK_A_CANDIDATE_INDEPENDENT_EXTERNAL_VALIDATION |
| KVASIR | CVC-ClinicDB | FOUND (612 binary masks) | 2 | EXACT_COMPATIBLE | PRIOR_RESEARCH_PROGRAM_USE | 0 exact | SECONDARY_EXTERNAL_BENCHMARK_ELIGIBLE | TRACK_B_PRIOR_USED_EXTERNAL_BENCHMARK |
| BUSI | BrEaST-Lesions_USG | FOUND (252 tumour masks) | 1 | EXACT_COMPATIBLE | PRIOR_RESEARCH_PROGRAM_USE | 0 exact | SECONDARY_EXTERNAL_BENCHMARK_ELIGIBLE | TRACK_B_PRIOR_USED_EXTERNAL_BENCHMARK |

**All four datasets DO contain usable segmentation ground truth.** HAM10000 is the ISIC-2018 Task-3 segmentation variant (images/ + masks/, 1:1), **not** classification-only; its `metadata.csv` 7-class diagnosis is REPORTING-ONLY. No dataset is yet `PRIMARY_EXTERNAL_ELIGIBLE`.

**Known administrative manifest discrepancy (EXT-01 metadata only):** `KNOWN_ADMINISTRATIVE_MANIFEST_DISCREPANCY` — the final-release `final_submission_checklist.json` was finalized after its manifest was written (self-referential ordering wrinkle). Administrative only; no scientific evidence affected; the frozen manifest is NOT rewritten.

**Artifacts:** `reports/external_extension/ext01_*` (inventory CSV+JSON, eligibility, overlap audit, prior-use ledger, annotation compatibility, preprocessing compatibility, audit summary, SHA-256 manifest).

<!-- EXT02_EXTERNAL_PROTOCOL_FREEZE_V1_0 -->
## EXT-02 External Evaluation Protocol Freeze — COMPLETE (2026-10-11)

**Revision ID:** `RA_MEDFILM_BARR_EXT02_EXTERNAL_PROTOCOL_FREEZE_V1_0` — **PROTOCOL/PREFLIGHT ONLY** (`science_changed = false`, `scientific_delta = 0`). No model inference, no training, no external performance metric produced.

**Status:** EXT-01 = **COMPLETE** · EXT-02 = **COMPLETE** · EXT-03 = **ELIGIBLE_NOT_STARTED**. Phases 0–40 unchanged.

### Frozen external cohorts (pre-inference)
| Dataset | task | evaluable n | exclusions | evidence class | track |
|---|---|---|---|---|---|
| HAM10000 | 0 | 10015 | 0 | SECONDARY_EXTERNAL_BENCHMARK | B |
| CVC-ClinicDB | 2 | 612 | 0 (PNG canonical; TIF not counted) | SECONDARY_EXTERNAL_BENCHMARK | B |
| BrEaST-Lesions_USG | 1 | 252 | 4 (GT_UNAVAILABLE: case045/061/209/213) | SECONDARY_EXTERNAL_BENCHMARK | B |
| Stones_where_are_you | 3 | 460 (115 source groups) | 0 | ELIGIBILITY_PENDING (annotation completeness not established) | A candidate |

### Frozen choices
- **Annotation mapping:** HAM lesion / CVC polyp / BREAST tumour; Stones: `category=='stone' -> fg`, all other categories -> bg (reporting only); kidney/bladder/ureter NOT foreground; no new task IDs.
- **Preprocessing:** frozen V1 pipeline; RGBA->RGB for BREAST (alpha dropped); Stones COCO polygons rasterized at native res.
- **Model identities:** G `286689fd…`, B_phi `8a412b2f…`, R_psi `6d28608a…`, S_omega `eee9b97b…`; total 4,837,420; wrapper trainable 0.
- **Comparator panel (frozen):** A GlobalMedFiLM, B RA-MedFiLM-BARR V1, C U-Net, D Attention U-Net, E UNet++, F DeepLabV3+ (labels SAME_PROTOCOL/CONTEXTUAL_ONLY assigned later; no add/remove after outcomes).
- **Metrics:** Dice primary; IoU/Precision/Recall/HD95 secondary; BARR rates + paired DeltaDice.
- **Statistics:** cluster-aware bootstrap, 10,000 reps, seed 20261011; units HAM=case, CVC=sequence_id, BREAST=caseXXX, Stones=source_group_id.
- **Evidence hierarchy:** Track A (Stones candidate) vs Track B (others); no combined "independent" statement; MIXED-PROVENANCE EXTERNAL MACRO descriptive only.
- **Progression (P1 ISIC → P4 four-domain) and LODO:** frozen now; **external evaluation NOT intended** for either (would require post-hoc labelling).
- **Qualitative figure rule:** deterministic ID-based or GT-only morphology quantiles; never best/worst after outcomes.

### Strengthened dependency (anti-leakage)
EXT-06 external evaluation requires: EXT-01 PASS + EXT-02 PASS + **EXT-03 required baselines FROZEN** + (if externally reported) EXT-04/EXT-05 model identities FROZEN. **NO external inference in EXT-03/EXT-04/EXT-05.**

**Stones:** `PRIMARY_EXTERNAL_VALIDATION_NOT_ESTABLISHED` (annotation completeness unresolved); EXT-02 not failed for this (Stones held as ELIGIBILITY_PENDING / Track A candidate).

**Artifacts:** `reports/external_extension/ext02_*` + `reports/external_extension/manifests/ext02_*_manifest.csv` (ext02_sha256_manifest.json = 17 artifacts).

<!-- EXT02_1_RECONCILIATION_AMENDMENT_V1_0 -->
## EXT-02.1 Pre-EXT03 Protocol Reconciliation Amendment — COMPLETE (2026-10-11)

**Revision ID:** `RA_MEDFILM_BARR_EXT02_1_PRE_EXT03_RECONCILIATION_V1_0` — **ADDITIVE GOVERNANCE/PROTOCOL ONLY** (`scientific_delta = 0`). Historical EXT-01/EXT-02 artifacts are preserved exactly; this amendment supersedes only affected FUTURE-execution fields. No external model outcome exists.

**Status:** EXT-01 **COMPLETE** · EXT-02 **COMPLETE** · EXT-02.1 **COMPLETE** · EXT-03 **ELIGIBLE_NOT_STARTED**.

### Resolved ambiguities
- **Stones evidence class (final):** `DOMAIN_SHIFT_STRESS_TEST` (secondary `SECONDARY_EXTERNAL_BENCHMARK`); mandatory `PRIMARY_EXTERNAL_VALIDATION_NOT_ESTABLISHED`; **NOT** Track A primary.
- **Zero-annotation handling:** 4 valid images (all variants of one source group `997c58b1…_jumbo_jpeg`) frozen `evaluable=false`, `ANNOTATION_COMPLETENESS_UNRESOLVED__ZERO_ANNOTATION`; never treated as stone-negative GT.
- **Comparator panel (7, final):** A GlobalMedFiLM (`SAME_PROTOCOL_REFERENCE`), B RA-MedFiLM-BARR V1 (`SAME_PROTOCOL_TARGET`), C U-Net, D Attention U-Net, E UNet++, F DeepLabV3+, G SegFormer-B0 (all `SAME_PROTOCOL_CANDIDATE`). `OPTIONAL_HYBRID = NOT_INCLUDED`. Candidate → `SAME_PROTOCOL` only on proven compliance; else `CONTEXTUAL_ONLY`; never performance-based.
- **Baseline training protocol frozen:** common recipe, seed set **42/123/3407**, checkpoint selection = macro-domain internal development-validation Dice (equal weighting); no external/HOLDOUT/TEST use; EXT-03 may not tune from baseline performance.
- **Preprocessing authority:** bound to canonical `scripts/analysis/phase36_robustness_execution_v1_23.py` (SHA `2287cc78…`; `_load_clean_image_tensor`/`_load_val_gt`); Phase39 v1.2 delegates to it → **VERIFIED_MATCH**; BREAST RGBA→RGB by dropping alpha.
- **Metric edge cases:** resolved (no placeholders); Dice/IoU both-empty=1.0, one-empty=0.0; HD95 undefined unless both non-empty.
- **Licenses:** HAM10000 CC BY-NC 4.0; CVC/BrEaST `LICENSE_CHECK_REQUIRED` (does not block internal EXT-03; required for EXT-06 publication).
- **Progression (P1 ISIC→P4 four-domain) and LODO:** preserved as internal-only; no external evaluation intended.

**Artifacts:** `reports/external_extension/ext02_1_*` + `manifests/ext02_1_stones_manifest_reconciled.csv`.
**Counters:** external model forwards = 0 · external performance metrics = 0 · training steps = 0 · optimizer steps = 0 · protected TEST pixel reads = 0.

<!-- EXT02_1A_ADVANCED_STUDY_PROGRAM_V1_0 -->
## EXT-02.1A Advanced Study Programme Freeze — COMPLETE (2026-10-11T16:00:00Z)

**Revision ID:** `RA_MEDFILM_BARR_EXT02_1A_ADVANCED_STUDY_PROGRAM_V1_0` — **PLANNING/PRE-REGISTRATION ONLY** (`scientific_delta = 0`). Preregistered BEFORE EXT-03; no result-driven study addition allowed later.

**Status:** EXT-01 COMPLETE · EXT-02 COMPLETE · EXT-02.1 COMPLETE · EXT-02.1A COMPLETE · EXT-03 ELIGIBLE_NOT_STARTED.

- **AS-01..AS-32 preregistered** (all `NOT_STARTED`). Tiers: TIER 1 = AS-01,03,04,05,06,08,09,10,11,12,13,15,16,20,21,24,27,30,31; TIER 2 = AS-02,14,17,18,19,22,23,25,26,29; TIER 3 = AS-07,28,32.
- **Offline evaluation architecture (EVALUATION TOOLS, NOT deployed model components):** oracle evaluator, budget simulator, uncertainty evaluator, error stratifier, study registry.
- **Rules added:** no outcome-dependent studies; no external-driven model selection; no TEST reuse; no post-hoc subgroup definitions; no best-seed headline; negative results retained; oracle internal-development only; LODO terminology gated by architecture validity; exploratory != confirmatory; reuse Phase36 where sufficient.
- **Roadmap:** EXT-03 (AS-08/AS-27) → EXT-04 (AS-01–05,07) → EXT-05 (AS-06) → EXT-05B (AS-09–13,30) → EXT-05C (AS-14,15) → EXT-06 (AS-20) → EXT-07 (AS-16–19) → EXT-08 (AS-21–24) → EXT-09 (AS-25,26,29,31) → EXT-09B (AS-28,32) → EXT-10 → EXT-11.
- **Registry:** `docs/ADVANCED_STUDY_REGISTRY.md`, `reports/planning/advanced_study_registry.json`, `reports/planning/advanced_paper_output_registry.json` (T-ADV-01..12, F-ADV-01..14).

**Counters:** model forwards = 0 · training steps = 0 · optimizer steps = 0 · external performance metrics = 0 · protected TEST reads = 0.

<!-- EXT03R_STAGE_A_TECHNICAL_RECOVERY_V1_0 -->
## EXT-03R Stage-A Technical Recovery — COMPLETE (2026-10-11)

**Revision ID:** `RA_MEDFILM_BARR_EXT03R_STAGE_A_RECOVERY_V1_0` — **TECHNICAL RECOVERY ONLY** (`scientific_delta = 0`). The historical EXT-03 blocker is preserved and disclosed; no science was amended.

**Status:** EXT-03 **STAGE-A RECOVERED** · **EXT-03 STAGE-B ELIGIBLE_NOT_STARTED** · AS-08 **NOT_STARTED** · AS-27 **NOT_STARTED**.

- **Package change (project venv only):** `transformers==5.19.0` installed (+ tokenizers 0.23.3, huggingface-hub 2.2.0, safetensors 0.8.0). No global install; no medical-pretrained weights downloaded.
- **SegFormer-B0 bound:** `src/models/segformer_b0.py` (config-only MiT-B0, `num_labels=1`, raw logits, bilinear resize to `[B,1,512,512]`; no `from_pretrained`), integrated via `src/models/factory.py`.
- **Five-architecture smoke tests PASS** (TECHNICAL_ONLY synthetic, 3-channel same-protocol construction), each `[2,1,512,512]` raw logits: U-Net 7,763,041 · Attention U-Net 7,851,285 · UNet++ 9,159,681 · DeepLabV3+ 40,347,041 · SegFormer-B0 3,714,401 params (no implementation drift vs the original 1-channel defaults).
- **Resumable harness frozen:** `scripts/training/run_ext03_baseline_matrix.py` (+ `.ps1` launcher); resume command `.venv\Scripts\python.exe scripts\training\run_ext03_baseline_matrix.py --resume`; session-independent; states NOT_STARTED/RUNNING/INTERRUPTED_RESUMABLE/COMPLETE/TECHNICAL_FAILURE (performance never controls retry).
- **Compute estimate (engineering only):** ≈24.8 img/s (U-Net) … 7.7 img/s (UNet++); full 15-run matrix (100-epoch ceiling) ≈48.6 h on the RTX 3060 Ti.
- **Unchanged:** training recipe, TRAIN authority, VAL808 authority, seeds 42/123/3407, metrics, checkpoint selection, 15-run matrix, seven-model panel.

**Counters:** external reads = 0 · TEST reads = 0 · ROUTER_HOLDOUT reads = 0 · scientific training steps = 0 · scientific optimizer steps = 0.
