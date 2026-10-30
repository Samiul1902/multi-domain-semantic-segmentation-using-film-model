# PHASE_INDEX — Phasewise Notebook Registry and Naming Governance

## Phase27 multi-domain preservation audit complete — current state (2026-10-02)

**Phase25 = COMPLETE_CANONICAL**; **Phase26 = COMPLETE_CANONICAL** (canonical bundle frozen);
**Phase27 = COMPLETE_CANONICAL** (frozen Phase26 A8/C9 bundle evaluated on VAL808 under the
pre-frozen 0.005 non-inferiority contract; `PRESERVATION_ASSERTED = True`, macro CI
`[+0.001133, +0.003298]`). Phase28/Phase29 = NOT_STARTED. ROUTER_HOLDOUT =
**RESERVED_UNOPENED_FOR_PHASE30**; TEST = **LOCKED_UNTIL_PHASE39**.

- Notebook: `phase_27_preservation/phase27_multidomain_preservation_audit.ipynb` (3x byte-identical).
- Terminal: `PHASE27_MULTIDOMAIN_PRESERVATION_AUDIT_COMPLETE__VAL808_CONTINUITY_RESULT_FROZEN__PHASE28_ELIGIBLE_NOT_STARTED`

## Phase25E policy evaluation complete — current state (2026-10-01)

Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: **COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: **COMPLETE_FROZEN**. Phase25F post-safety specification v1.0 (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN** (execution **COMPLETE_CANONICAL**). Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30). **Phase25 = COMPLETE_CANONICAL**; Phase26 = **ELIGIBLE_NOT_STARTED**.

The normalized incremental action cost is exactly `3,230,662,656 / 31,551,740,928` (`1051648/10270749`, approximately `0.10239253242387678`) for available actions; unavailable actions cost zero and are FORCED_SKIP. Pre-gate router overhead is `36,160` Conv/Linear MACs, separate from action cost. All compute is **ANALYTICAL MAC LOWER BOUND**, never measured latency.

Lambdas `{0.00, 0.25, 0.50, 1.00}` and budgets `{0%, 10%, 25%, 50%, 100%}` are frozen. All 4,957 DEV rows are action-available; exact top-K counts are `{0, 495, 1239, 2478, 4957}`. Rank by score descending, sample_id ascending. Random priorities (PCG64 seed 42) and 45 label-blind memberships were frozen before outcomes. Under constant action cost, C7 and C8 have **identical membership at every fixed budget and lambda**; they are not independent evidence.

The 45 frozen OOF memberships were joined to the frozen Phase25C paired-gain outcomes on ROUTER_DEVELOPMENT only (4957). Statistics (domain-stratified group bootstrap, 2000 replicates, seed 42) and final-router DEV thresholds were frozen **before** the outcome join. Result: under the frozen PRIMARY statistic (raw paired two-sided p), C7 **significantly beats every simple GT-free proxy on precision@budget at the 10% and 25% budgets**, the advantage shrinking to non-significance at 50% (Holm-Bonferroni retained only as a secondary sensitivity: 10%); preservation holds; a usable accuracy-compute frontier exists. H1 is scoped to the tight and medium budgets (10%/25%).

The frozen final benefit-router checkpoint was loaded once and run in a single outcome-blind forward pass over the 4,957 ROUTER_DEVELOPMENT feature rows (no global-model forward, no regional-refiner forward, no training); no lambda was selected; C9 post-safety was not evaluated. ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39.

Executed scientific notebook: `notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb`; SHA-256 `b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797` (3× byte-identical; post-reconciliation rebuild superseding the archived pre-reconciliation build SHA `e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718`). Evidence: `reports/audits/phase25e_policy_evaluation_summary.json`, `reports/audits/phase25e_adjudication.json` (original closure), `reports/audits/phase25e_adjudication_reconciled.json` (PRIMARY adjudication, raw paired p), `reports/audits/phase25e_multiplicity_provenance_audit.json`, `reports/audits/phase25e_final_freeze.json`.

Terminal: `PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED`.

## Phase25F post-safety specification v1.0 — COMPLETE_FROZEN (2026-10-01)

Phase25F post-safety specification (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN**; Phase25F execution: **COMPLETE_CANONICAL**. The first blocked Phase25F attempt (`PHASE25F_BLOCKED__POST_SAFETY_EXECUTION_SPEC_INCOMPLETE`; 54 blocking fields, 12 hard-stop conditions) is preserved verbatim as **BLOCKED_ATTEMPT_PROVENANCE** (no audit overwritten or deleted).

The repair prospectively froze the exact S_omega input vector (20-D = 16 numeric + 4 one-hot task), the leakage-safe OOF post-refinement source (Phase25C fold-specific `_tmp_refined_crop_prob_<DOMAIN>.npy`, provenance-proven and promoted to `data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy`), `BARRPostSafetyV1` (`Linear(20,32)->SiLU->Linear(32,16)->SiLU->Linear(16,1)`, **1,217** trainable parameters, raw logit output), the training objective (`BCEWithLogitsLoss`, mean reduction, no class weighting / pos_weight / label smoothing), the reused Phase25D five-fold CV identity manifests (FIT / EARLY_STOP / OUTER_TARGET), FIT-only ddof=0 normalization of the 16 numeric features, the fixed ACCEPT/FALLBACK threshold (`sigmoid >= 0.50` / `logit >= 0.0`; distinct from the 0.30 ROI-proposal and 0.50 segmentation-output thresholds), the Phase25E SKIP interaction state machine, the final-refit rule (exact median of the five best epochs, seed 42, LAST_FIXED_EPOCH checkpoint), and A7/A8 ownership (Phase25F constructs the C9 artifact on ROUTER_DEVELOPMENT; Phase25G owns the integrated A7-vs-A8 / C8-vs-C9 evaluation).

All 73 specification fields are now complete; `blocking_fields = []` and `hard_stop_conditions_triggered = []`. **No model was constructed, no training ran, no forward pass occurred, no refinement or DeltaDice was regenerated, and no threshold was tuned.** ROUTER_HOLDOUT, VAL808 and TEST remain closed; Phase25G is NOT_STARTED.

Evidence: `reports/audits/phase25f_post_safety_spec_completion_v1_0.json`, `phase25f_oof_refinement_source_contract_v1_0.json`, `phase25f_oof_refinement_source_promotion.json`, `phase25f_feature_equation_contract_v1_0.json`, `phase25f_feature_cache_determinism.json`, `phase25f_target_contract_v1_0.json`, `phase25f_architecture_contract_v1_0.json`, `phase25f_training_contract_v1_0.json`, `phase25f_decision_threshold_contract_v1_0.json`, `phase25f_state_machine_contract_v1_0.json`, `phase25f_final_refit_contract_v1_0.json`, `phase25f_a7_a8_ownership_ruling_v1_0.json`, `phase25f_spec_repair_no_execution.json`, `phase25f_spec_repair_final_check.json`.

Terminal: `PHASE25F_POST_SAFETY_SPEC_V1_0_COMPLETE__OOF_FEATURE_SOURCE_ARCHITECTURE_TRAINING_THRESHOLD_AND_OWNERSHIP_FROZEN__PHASE25F_EXECUTION_ELIGIBLE_NOT_STARTED`.

## Phase25F post-safety execution — COMPLETE_CANONICAL (2026-10-01)

`BARRPostSafetyV1` was constructed and trained for five frozen CV logical runs (seeds 54000–54004) plus one all-DEV final refit (`FINAL_SAFETY_EPOCHS = 23`; seed 42; LAST_FIXED_EPOCH). **4,957 OOF safety logits / probabilities / decisions** were produced on ROUTER_DEVELOPMENT and are bit-reproducible (3x replay, max abs 0.0). The **C9 post-safety state/decision artifact** (20 frozen C8 policies × 4,957 rows) was constructed. Classifier-level metrics describe S_omega itself; they are not segmentation results and not a preservation proof. No A7/A8 segmentation comparison, no C8/C9 system-performance comparison, no preservation adjudication, no new budget/lambda, no threshold tuning. ROUTER_HOLDOUT / VAL808 / TEST were never read. Phase25G is **ELIGIBLE_NOT_STARTED**.

Notebook: `notebooks/phasewise/phase_25f_post_safety/phase25f_post_safety_execution.ipynb` (SHA-256 `1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90`, 41 sections, 9 figures, 3x byte-identical).

**PRE_COMPLIANCE_REPAIR_PROVENANCE**: the superseded reviewer notebook `reports/audits/phase25f_post_safety_execution_pre_compliance_repair.ipynb` (SHA-256 `d40120ab35956335e884f2b71398a4a6727e3ca3b50be788fd1d86f33e948908`) is preserved byte-for-byte. Its CV epoch tables rendered only 8 rows per fold; the canonical notebook now renders the complete histories (36 / 27 / 86 / 55 / 43). TEST reads = 0.

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





**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)
**Method name:** RA-MedFiLM-BARR

This index is the single entry point for "which notebook is canonical for which phase,
and what is its exact SHA". It intentionally **does not** rename any frozen artifact —
historical path + SHA remain part of provenance. Preferred future names are recorded here
only.

---

## 1. Canonical / frozen notebooks

Terminal strings record each phase's historical completion boundary; current state is in the Status column and current-focus text.

| Phase | Subphase | Purpose | Canonical notebook path | Canonical notebook SHA-256 | Status | Class | Supersedes | Terminal | TEST reads | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| 21 | Global MedFiLM | FiLM-conditioned shared global model | `notebooks/phasewise/phase_21_global_medfilm/phase21_global_medfilm_reference.ipynb` | `e7fadc7c…` (see `reports/audits/` for full SHA) | COMPLETE | Canonical | — | — | 0 | ckpt `286689fd…`; 3,523,001 params |
| 22 | Resource gap | Multi-domain scale / regional gap analysis | `notebooks/phasewise/phase_22_resource_gap/phase22_resource_gap_analysis.ipynb` | `cca76123…` | COMPLETE | Canonical | — | — | 0 | benefit strongly heterogeneous; always-on regional HURTS in aggregate |
| 23 | Literature & novelty | Methodological novelty audit | `notebooks/phasewise/phase_23_literature_novelty/phase23_literature_methodological_novelty_audit.ipynb` | `e9f78cce…` | COMPLETE | Canonical | — | — | 0 | max novelty = Level 2 |
| 24 | v1.1 exact-spec freeze | Frozen exact implementation specification | `notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb` | `612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef` | COMPLETE | **Historical provenance** | superseded by v1.2 | `PHASE24_SPEC_COMPLETENESS_REPAIR_COMPLETE…` | 0 | **NEVER RENAME**; v1.1 router features underspecified |
| 24 | **v1.2 router feature spec** | Router input contract completion (RF-1/2/3 + D1/D2) | `notebooks/phasewise/phase_24_architecture_spec/phase24_narrowed_benefit_aware_refinement_spec.ipynb` | `9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027` | **COMPLETE** | **Canonical** | supersedes v1.1 | `PHASE24_V1_2_FULLY_CLOSED__PROJECT_DOCS_AND_PHASEWISE_INDEX_SYNCED__PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED` | 0 | 3× byte-identical; pre-closure SHA `97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff` retained as provenance |
| 25A | Dedicated regional refiner | Crop-trained `R_psi` (`BARRRegionalRefinerV1`) | `notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb` | `fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd` | **COMPLETE_CANONICAL** | **Canonical** | supersedes ROI-0.50 run | `PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED` | 0 | ckpt `6d28608a…`; 1,276,401 params; 3.230663 GMAC |
| 25A | ROI-0.50 run | First Phase-25A execution at ROI threshold 0.50 | `notebooks/phasewise/phase_25a_regional_refiner/phase25a_dedicated_regional_refiner.ipynb` (historical content, SHA `7dfcf505…`) | `7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f` | **NONCANONICAL_PROTOCOL_DEVIATION** | **Historical / forbidden for science** | superseded by canonical | — | 0 | scientific use **FORBIDDEN**; preserved per `phase25a_roi050_supersession.json` |
| 25B | GT-free pre-refinement features | Router feature extraction (202-D, GT-free) | `notebooks/phasewise/phase_25b_gt_free_features/phase25b_gt_free_pre_refinement_features.ipynb` | `acdfe90a5042ef364c5ab28ec67ecd3fe3146b30e1e5715a2631a36deb4dc38a` | **COMPLETE_CANONICAL** | **Canonical** | supersedes blocked attempt | `PHASE25B_HANDOFF_SEMANTICS_REPAIRED__PHASE25C_OOF_PAIRED_GAIN_LABEL_GENERATION_ELIGIBLE_NOT_STARTED` | 0 | 202-D cache frozen (4957 × 202); global equivalence max_abs = 0.0; 3× byte-identical; handoff semantics repaired (pre-repair SHA `11a1a62a…` retained as provenance) |
| 25C | OOF paired-gain labels | Leakage-safe OOF paired refinement-gain label generation | `notebooks/phasewise/phase_25c_paired_gain_labels/phase25c_oof_paired_refinement_gain.ipynb` | `564105eabfdb4cfb12613ca65cab7dc0c4410bea667239e5c1302e15060db613` | **COMPLETE_CANONICAL** | **Canonical** | — | `PHASE25C_OOF_PAIRED_REFINEMENT_GAIN_LABELS_COMPLETE__PHASE25D_BENEFIT_ROUTER_ELIGIBLE_NOT_STARTED` | 0 | 4957 OOF rows (BENEFICIAL 282 / NEUTRAL 4340 / HARMFUL 335); label CSV `fd6ca32c…`; 3× byte-identical; 8/8 embedded PNG valid; `global_model_forward_passes = 0` |
| **25D** | **Benefit router training** | `BARRBenefitRouterV1` 5-fold CV + final refit | `notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb` | `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63` | **COMPLETE_CANONICAL** | **Canonical** | — | `PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN__PHASE25E_ELIGIBLE_NOT_STARTED` | 0 | 5 CV folds (best epochs 37/34/139/199/80); final refit 80 epochs; 4957 OOF predictions; 3× byte-identical notebook |
| **25E-SPEC** | **Resource-gate specification** | Prospective cost/lambda/budget/tie/comparator and membership freeze | `notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate_specification.ipynb` | `a431b3604021c0f4ffaaa6153302d674a38167b1792ab55d09a58a8ad2a5c41c` | **COMPLETE_FROZEN** | **Canonical DESIGN/AUDIT** | — | `PHASE25E_RESOURCE_GATE_SPEC_V1_0_COMPLETE__COST_BUDGET_LAMBDA_TIE_AND_COMPARATOR_RULES_FROZEN__PHASE25E_POLICY_EVALUATION_ELIGIBLE_NOT_STARTED` | 0 | 45 policies; no outcome evaluation; 3× byte-identical |
| **25E-EVAL** | **Resource-gate policy evaluation** | 45 frozen OOF memberships joined to Phase25C outcomes on DEV; bootstrap + frontier + adjudication | `notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb` | `b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797` | **COMPLETE_FROZEN** | **Canonical** | pre-reconciliation build (SHA `e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718`, archived) | `PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED` | 0 | S1/H1 PARTIAL (primary raw paired p significant at the 10% and 25% budgets; not at 50%); S2 satisfied; no domain collapse; bootstrap 2000 seed 42; 3× byte-identical; 8/8 PNG valid |

> **Row 25B is now COMPLETE.** The canonical 202-D GT-free feature cache is frozen at
> `data_cache/phase25b_barr_pre_refinement_features_v1_2/`, the reviewer notebook is
> 3× byte-identical, and every scope/lock gate passes. Post-phase handoff semantics were
> repaired (documentation/governance only — no science, cache, or model change):
> **Phase 25C = OOF paired refinement-gain label generation**; **Phase 25D = benefit-router
> training** (owner of the 16-D task embedding and of `BARRBenefitRouterV1`). The Phase 25B
> notebook file was **not** renamed.

> **Row 25C is now COMPLETE canonical.** The canonical `ROUTER_DEVELOPMENT` OOF paired
> refinement-gain label table is frozen at
> `data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv`
> (4957 rows, SHA `fd6ca32c…`). Labels come from **fold-specific** ROI-0.30 refiners applied to
> outer folds entirely excluded from their own fitting (cross-fit leakage audit CLEAN);
> `global_model_forward_passes = 0` (Phase-25B global cache reused). Phase 25C created **labels
> only** — no router training, no 16-D task embedding, `test_reads = 0`.
> At Phase25C completion, Phase25D was eligible/not-started and no Phase25D notebook yet existed.
> Phase25D has since completed canonically. Phase25E scientific policy evaluation is now
> **COMPLETE_FROZEN** (see row 25E-EVAL).

PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `29518fc13f3de60113e1110a12a3f38bac5f54c246751503fe29e595f6dbe997`

The original notebook is preserved at `reports/audits/phase25d_notebook_compliance_pre_repair.ipynb`.
The original scientific freeze is unchanged; the notebook migration is bound by
`reports/audits/phase25d_final_freeze_notebook_compliance_addendum.json`.

---

## 2. Blocked / provenance-only attempts

| Phase | Attempt | Canonical notebook | Status | Reason |
|---|---|---|---|---|
| 25B | First entry (pre-repair) | **NONE** | `BLOCKED_ATTEMPT_PROVENANCE` | frozen feature specification incomplete (RF-1/RF-2/RF-3); preserved at `reports/audits/phase25b_blocked_attempt_final_freeze.json` |
| 25A | ROI-0.50 execution | historical content of the 25A path | `NONCANONICAL_PROTOCOL_DEVIATION` | ROI threshold 0.50 ≠ frozen 0.30 |
| 25D | First entry (pre-repair) | **NONE** | `BLOCKED_ATTEMPT_PROVENANCE` | frozen router-training spec incomplete (cv_fold_assignment_algorithm, cv_inner_split_rule, checkpoint_selection_rule, target_scaling_semantics, final_refit_scheduler_semantics); preserved at `reports/audits/phase25d_blocked_spec_incomplete.json` |

---

## 3. Future canonical organization (preferred names — NOT applied retroactively)

These directory names are the **preferred future convention**. They are declared here for
forward consistency; **no existing frozen notebook is renamed** to match them.

```
phase_24_architecture_spec/
  phase24_narrowed_benefit_aware_refinement_spec.ipynb          # v1.2 canonical
  phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb

phase_25a_regional_refiner/
  phase25a_dedicated_regional_refiner.ipynb                     # canonical

phase_25b_gt_free_features/
  phase25b_gt_free_pre_refinement_features.ipynb                # canonical (202-D, GT-free)

phase_25c_paired_gain_labels/
  phase25c_oof_paired_refinement_gain.ipynb                     # canonical

phase_25d_benefit_router/
  phase25d_benefit_router.ipynb                                 # canonical
  # Phase25D first entry: BLOCKED_PRE_MODEL_CONSTRUCTION (router training spec incomplete)
  # Historical after spec repair v1.2.1, before training: REENTRY_ELIGIBLE_NOT_STARTED
  # Current: COMPLETE_CANONICAL / TRAINED / FROZEN
  # After execution: COMPLETE canonical

phase_25e_resource_gate/
  phase25e_resource_gate_specification.ipynb                  # COMPLETE_FROZEN DESIGN/AUDIT
  phase25e_resource_aware_pre_gate.ipynb                        # ELIGIBLE_NOT_STARTED; NOT YET CREATED

phase_25f_post_safety/
  phase25f_post_safety_execution.ipynb                         # COMPLETE_CANONICAL canonical SHA 1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90

phase_25g_controlled_validation/
  phase25g_integrated_controlled_evaluation.ipynb               # COMPLETE_CANONICAL canonical SHA 5f6b6642fe013d9ad69cac8a0e319d5f86362d8457febdab42fde6cbe14c4487
```

**No empty future `.ipynb` files have been created.** A Phase-25x notebook is created only
when that subphase actually executes.

---

## 4. Immutability notice

The following canonical paths are **frozen and MUST NOT be renamed or deleted**:

- Phase-21 notebook · Phase-22 notebook · Phase-23 notebook
- Phase-24 v1.1 provenance notebook · Phase-24 v1.2 notebook
- Phase-25A canonical notebook · Phase-25A ROI-0.50 superseded reference
- **Phase-25B canonical notebook** (`acdfe90a…`)
- **Phase-25C canonical notebook** (`564105ea…`)
- **Phase-25D canonical notebook** (`phase25d_benefit_router.ipynb`) — SHA-256 `733ff56a2b67e1427772ed49badc713c75ac309c2e8af27cbce2f604b6acfc63`

- **Phase25E specification notebook** (`phase25e_resource_gate_specification.ipynb`) — SHA-256 `a431b3604021c0f4ffaaa6153302d674a38167b1792ab55d09a58a8ad2a5c41c`

- **Phase25F canonical notebook** (`phase25f_post_safety_execution.ipynb`) — SHA-256 `1ba9c08bee97e95926994b11268017e8d6b45150929ebe6edfca4dfe95715c90`
- **Phase25G canonical notebook** (`phase25g_integrated_controlled_evaluation.ipynb`) — SHA-256 `5f6b6642fe013d9ad69cac8a0e319d5f86362d8457febdab42fde6cbe14c4487`

The list above covers every frozen notebook from Phase21 through the Phase25E specification subphase. If a filename is
aesthetically inconsistent with §3, the preferred convention is recorded here rather than applied
physically.

---

**Cross-links:** [../../docs/ARCHITECTURE.md](../../docs/ARCHITECTURE.md) ·
[../../docs/TASKS.md](../../docs/TASKS.md) · [README.md](README.md)

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

<!-- PHASE26_CANONICAL_INTEGRATION_COMPLETE -->

## Phase26 canonical integration - COMPLETE_CANONICAL (2026-10-02)

**Phase26 = COMPLETE_CANONICAL** (assembly only; legacy title 'Full Four-Domain
RA-MedFiLM-BARR Training' redefined to 'Full Four-Domain RA-MedFiLM-BARR Integration &
Canonical Bundle Freeze'). Phase27 = ELIGIBLE_NOT_STARTED; Phase28/29/30 = NOT_STARTED.

- Bundle: `artifacts/phase26_ra_medfilm_barr_bundle_v1_0` (manifest SHA `f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9`)
- Wrapper: `src/models/barr/ra_medfilm_barr.py` (SHA `342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724`, 0 trainable parameters)
- Notebook: `notebooks/phasewise/phase_26_full_system_integration/phase26_canonical_integration_and_bundle_freeze.ipynb` (SHA `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0`, 3x byte-identical)
- Runtime policy: `A8_C9`, nominal budget 0.25, score `delta_hat_final - 0.25*C`,
  threshold `-5003565381643716252018011/205414980000000000000000000` (EXECUTE iff `>=`).
- Final-router DEV calibration selected count = 1239.
- ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; VAL808 = UNOPENED; TEST = LOCKED_UNTIL_PHASE39.
- 0 model training / 0 backward / 0 optimizer / 0 scientific-data forwards.

Terminal: `PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED`

<!-- PHASE27_PRESERVATION_SPEC_COMPLETE -->

## Phase27 multi-domain performance preservation audit - SPEC_COMPLETE_FROZEN (2026-10-02)

**Phase27 specification = COMPLETE_FROZEN**; Phase27 = **EXECUTION_ELIGIBLE_NOT_STARTED**.
Governance / specification only - no VAL808 inference, no model construction, no training.

**SUPERVISOR RULING**: Phase27 owns VAL808 as the `SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK`.
Phase30 retains exclusive `ROUTER_HOLDOUT` ownership (one-shot). VAL808 is **not** an untouched
routing holdout and must never substitute for it.

- Specification: `docs/phase27_preservation_spec.md`; revision `ra_medfilm_barr_preservation_v1_0`.
- VAL808 manifest `manifests/phase4_v3/val.csv` (SHA `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315`),
  n = 808, domains ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84 (task_id 0/3/2/1), metadata only.
- Group rule `METADATA_ONLY_COMPOSITE_PATIENT_SINGLETON` (KUB `PATIENT::patient_id`; other domains singleton).
  Total groups = **639** (ISIC 357 / KUB 111 / KVASIR 87 / BUSI 84). The metadata-only partition is
  **provably identical** to the canonical Phase24 `group_key` partition on all 5832 TRAIN rows
  (all 16 `RISK::` pHash groups are singletons, so relabelling never merges rows).
- Estimand: macro-domain equal-weight mean Dice delta (`Delta_i = Dice(final_A8_i, GT) - Dice(global_i, GT)`);
  non-inferiority margin **0.005**, claim iff lower 95% CI bound > -0.005 (strict).
- Bootstrap: domain-stratified **group** bootstrap, B = 2000, seed 42, PCG64, percentile CI 2.5/97.5.
  Draw plan frozen **before** inference at
  `data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_plan_v1_0.npz`
  (SHA `8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93`).
- System under test = frozen Phase26 bundle A8/C9; global reference = the SAME frozen GlobalMedFiLM in the bundle.
- GT/inference separation: two-phase with a hash barrier (predictions hashed before any GT read).
- ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; TEST = LOCKED_UNTIL_PHASE39; Phase28/30 = NOT_STARTED.
- 0 model forwards / 0 scientific forwards / 0 training / 0 VAL808 image or mask reads / 0 holdout reads / 0 test reads.

Evidence: `reports/audits/phase27_spec_entry_gate.json`, `phase27_population_ownership_ruling_v1_0.json`,
`phase27_val808_population_binding_v1_0.json`, `phase27_phase26_bundle_binding_v1_0.json`,
`phase27_preservation_contract_binding_v1_0.json`, `phase27_component_identity_binding_v1_0.json`,
`phase27_statistics_contract_v1_0.json`, `phase27_bootstrap_plan_freeze_v1_0.json`,
`phase27_gt_inference_separation_contract.json`, `phase27_prediction_artifact_contract.json`,
`phase27_reproducibility_contract.json`, `phase27_holdout_lock.json`, `phase27_test_lock.json`,
`phase27_scope_guard.json`, `phase27_specification_final_check.json`;
`reports/tables/phase27_specification_completeness.csv` (56 fields, `blocking_fields = []`).

Terminal: `PHASE27_PRESERVATION_SPEC_COMPLETE__VAL808_CONTINUITY_BENCHMARK_AND_NONINFERIORITY_PROTOCOL_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED`

<!-- PHASE26_NOTEBOOK_POSTCLOSURE_RECONCILIATION -->

## Phase26 notebook postclosure reconciliation (2026-10-02)

Reviewer-evidence repair only (`REVIEWER_NOTEBOOK_POSTCLOSURE_RECONCILIATION_ONLY`).
Phase26 remains **COMPLETE_CANONICAL**; scientific status unchanged.

- Canonical Phase26 notebook SHA (new): `5d063ecb57a7e213c2260a11e1daa66bb58bc2f6b5b4029cfc1ae0e3e91aa8c8`
- Old notebook SHA: `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0` = `PRE_POSTCLOSURE_NOTEBOOK_REPAIR_PROVENANCE`
- Archived byte-for-byte at
  `reports/audits/phase26_canonical_integration_pre_postclosure_notebook_repair.ipynb`
- Repaired reviewer cells: `p-046` validator SHA -> `912d886599adae810db14edf17331a25c37d4e92abd8fbe1fe67f94ab7810300`;
  `p-078` terminal -> `PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED`
- Base `reports/audits/phase26_final_freeze.json` NOT rewritten (SHA `e709f5301894dc0377420500a9b6d6e95bd54858fde4cb472cad73d630b8adb4`).
- Addendum: `reports/audits/phase26_final_freeze_notebook_postclosure_addendum.json`
- 3x byte-identical; 40/40 code cells; 0 errors; 2/2 valid PNGs.
- `science_changed = false`; bundle / wrapper / checkpoint SHAs unchanged.


<!-- PHASE27_PRESERVATION_SPEC_V1_1_EXECUTION_SEMANTICS_REPAIR -->

## Phase27 spec v1.1 - execution-semantics repair (2026-10-02)

`GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY`. Phase27 spec = **V1_1_COMPLETE_FROZEN**;
Phase27 = **EXECUTION_ELIGIBLE_NOT_STARTED**; Phase26 remains **COMPLETE_CANONICAL**.

- Phase26 notebook closure reconciled: canonical Phase26 notebook SHA now `5d063ecb57a7e213c2260a11e1daa66bb58bc2f6b5b4029cfc1ae0e3e91aa8c8`
  (old `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0` = PRE_POSTCLOSURE_NOTEBOOK_REPAIR_PROVENANCE).
- Numerical inference mode resolved from authoritative predecessor evidence (CASE A):
  **CUDA + autocast(float16) + no_grad, eval mode**; batch 8, contiguous chunks per domain,
  order `(dataset, sample_id)`; probability computed float32, stored float16.
- Evidence class = `CONTINUITY_DEVELOPMENT_EVIDENCE`.
- Frozen VAL808 statistics unchanged: n 808, ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84,
  639 groups, bootstrap B 2000 seed 42 PCG64, plan SHA `8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93`.
- Completeness table v1.1: `reports/tables/phase27_specification_completeness_v1_1.csv`
  (34 rows, exact schema, `blocking_fields = []`).
- 0 VAL808 image/mask reads; 0 scientific forwards; 0 training; ROUTER_HOLDOUT + TEST unopened.

Terminal: `PHASE27_SPEC_V1_1_COMPLETE__PHASE26_NOTEBOOK_CLOSURE_RECONCILED__NUMERICAL_INFERENCE_AND_EVIDENCE_PROVENANCE_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED`

<!-- PHASE27_PRESERVATION_AUDIT_COMPLETE -->

## Phase27 multi-domain preservation audit - COMPLETE_CANONICAL (2026-10-02)

**Phase27 = COMPLETE_CANONICAL** (frozen Phase26 A8/C9 bundle evaluated on VAL808 under the
pre-frozen 0.005 non-inferiority contract; `PRESERVATION_ASSERTED = True`, macro CI
`[+0.001133, +0.003298]`). Phase28/Phase29 = NOT_STARTED. ROUTER_HOLDOUT =
**RESERVED_UNOPENED_FOR_PHASE30**; TEST = **LOCKED_UNTIL_PHASE39**.

- Notebook: `phase_27_preservation/phase27_multidomain_preservation_audit.ipynb` (3x byte-identical).
- Terminal: `PHASE27_MULTIDOMAIN_PRESERVATION_AUDIT_COMPLETE__VAL808_CONTINUITY_RESULT_FROZEN__PHASE28_ELIGIBLE_NOT_STARTED`

<!-- PHASE27_VISUAL_CLARITY_REPAIR_COMPLETE -->

## Phase27 qualitative panel visual-clarity repair - COMPLETE (2026-10-02)

**REVIEWER-VISUALIZATION-ONLY REPAIR** (`PHASE27_REVIEWER_VISUAL_CLARITY_REPAIR_ONLY`).
Phase27 scientific freeze **UNCHANGED**; all predictions, metrics, bootstrap, sample
selection, GT, and TP/FN/FP semantics remain byte-identical.

- **Pre-repair provenance:**
  - Notebook SHA: `1413a847a3f252661603f8eabb5b06c03d4c4a7337fe8bf0b3e481e25d2e0d1d`
  - Figure SHA: `d2aae28a219546a4708a7f59c1736a990d8bcc774372caedb4c80346ff251773`
  - Figure dimensions: 1924 × 379 px (WIDE_1X4_GROUP_LAYOUT)
  - Archived at `reports/audits/phase27_multidomain_preservation_pre_visual_clarity_repair.ipynb`
    and `reports/audits/phase27_qualitative_panels_pre_visual_clarity_repair.png`

- **Post-repair state:**
  - Notebook SHA: `c577b5ea200013db588459869e8dac7abb6c439f148b3f68465da178f0e38b69` (3× byte-identical)
  - Figure SHA: `6dc9b3f975f29e49f80349a4801d2e6b8c7c038d537729fbb29e39a93c06d262`
  - Figure dimensions: 4783 × 3233 px at 250 dpi (REVIEWER_READABLE_2X2_GROUP_LAYOUT)
  - Layout: 2×2 group blocks (BUSI|ISIC / KUB|KVASIR), each domain = 4 samples × 5 columns
  - Typography: title 18 pt, column headers 11 pt, domain/sample labels 9 pt
  - Added compact TP/FN/FP legend (green=TP, blue=FN, red=FP)
  - Interpolation: nearest for all panels; aspect: equal; axes hidden

- **Source usage (GOVERNANCE RECONCILED — see below):**
  - Canonical visual repair rebuilt from frozen reviewer artifacts only
    (frozen 512×512 mask PNGs for prediction columns; frozen reviewer RGB/GT raster
    panels for the RGB/GT columns; frozen gallery selection CSV).
  - 0 raw VAL808 source reads / 0 model forward passes / 0 training runs /
    0 metric recomputation / 0 bootstrap changes.

- **Governance reconciliation (2026-10-02):**
  - A first visual-repair attempt populated the RGB/GT columns by re-reading raw VAL808
    RGB images and GT masks (visualization only). This was a work-order scope deviation
    (`REVIEWER_VISUAL_REPAIR_SCOPE_DEVIATION__RAW_VAL808_RGB_GT_REREAD`) with
    **no scientific impact** (predictions/metrics/bootstrap unchanged).
  - That scope-deviating high-resolution output is **retained and documented** as
    `NONCANONICAL_VISUAL_REPAIR_PROVENANCE` at
    `reports/audits/phase27_noncanonical_visual_repair_provenance/`
    (not deleted, not declared scientifically invalid).
  - The canonical reviewer visual was then **rebuilt from frozen reviewer artifacts only**
    (`SOURCE_LIMITATION = RELAYOUT_FROM_FROZEN_REVIEWER_RASTER`); the underlying RGB/GT
    source pixels are unchanged — visual clarity comes from layout enlargement only.

- **Outputs (canonical rebuild):**
  - `reports/figures/phase27_preservation/p27_qualitative_panels.png`
  - `reports/figures/phase27_preservation/p27_qualitative_panels.pdf`

- **Provenance (noncanonical scope-deviation attempt, retained):**
  - `reports/audits/phase27_visual_repair_scope_deviation_reconciliation.json`
  - `reports/audits/phase27_qualitative_panel_visual_clarity_repair_provenance_preservation.json`

- Phase28 = **ELIGIBLE_NOT_STARTED**; ROUTER_HOLDOUT = **RESERVED_UNOPENED_FOR_PHASE30**;
  TEST = **LOCKED_UNTIL_PHASE39**.

Terminal: `PHASE27_VISUAL_REPAIR_GOVERNANCE_RECONCILED__CANONICAL_QUALITATIVE_FIGURE_REBUILT_FROM_FROZEN_ARTIFACTS__SCIENTIFIC_FREEZE_UNCHANGED__PHASE28_ELIGIBLE_NOT_STARTED`


<!-- PHASE28_NOTEBOOK_COMPLIANCE_REPAIR_COMPLETE -->

## Phase28 comprehensive ablation - COMPLETE_CANONICAL (repaired) (2026-10-02)

**Phase28 = COMPLETE_CANONICAL**. Canonical comprehensive 13-arm system ablation
(A0-A8, R1-R3, F1) on ROUTER_DEVELOPMENT (n=4957) under the frozen fixed budget rule
(b=0.25, K=1239). 18 new training runs (R1/R2/R3 x 15 folds + F1 x 3 folds), 10 tables,
8 figures, negative F1 result reported. Scientific results are **UNCHANGED** by this
entry — this entry records a **reviewer-notebook compliance repair only**.

- **Repair classification:** `REVIEWER_NOTEBOOK_COMPLIANCE_ONLY`
- **Prior (pre-repair) notebook SHA:** `72cfbc12e76a58fab3449e6dbf8163cbe988e7473e716e10bf87741fa8c10326`
  (`PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE`; archived byte-for-byte at
  `reports/audits/phase28_comprehensive_ablation_pre_notebook_compliance_repair.ipynb`; retained, never deleted/overwritten)
- **Canonical repaired notebook SHA:** `ba40b5f22febb2250f14fb6b863ce974a46667b07f3cb3fff46293c67eb486e1` (executed; 3x byte-identical)
- **Repaired notebook:** `notebooks/phasewise/phase_28_model_ablation/phase28_comprehensive_ablation.ipynb`
- **Defects repaired:** (i) the prior notebook was UNEXECUTED (35 code cells,
  `execution_count = null`, 0 outputs, 0 embedded figures); (ii) complete epoch
  histories for all 18 runs were not visibly rendered.
- **Repair evidence:** 45/45 code cells executed with contiguous counts 1..45, 0 errors,
  0 tracebacks; all 18 runs render COMPLETE one-row-per-epoch histories (891 epoch rows,
  zero truncation); all 10 frozen tables rendered in full; all 8 frozen figures embedded
  from frozen PNG bytes (embedded SHA set == frozen figure SHA set).
- **Scientific immutability:** post-repair drift = 0; all checkpoints, histories, OOF
  predictions, memberships, F1 artifacts, tables, figures and the canonical Phase26
  bundle (`f7aebb0f...`) are byte-identical to pre-repair.
- **Addendum:** `reports/audits/phase28_final_freeze_notebook_compliance_addendum.json`
  (base freeze `phase28_final_freeze.json` SHA `ac4b9f72...` is unchanged / not rewritten).
- **Ruling (unchanged):** A6/C7 > R1 > R3 ~ R2; A8 = 0.0075158 (1205 ACCEPT / 34 FALLBACK);
  F1 refiner-level and integrated both NEGATIVE. No policy selected, no deployment winner.
- ROUTER_HOLDOUT = **RESERVED_UNOPENED_FOR_PHASE30**; TEST = **LOCKED_UNTIL_PHASE39**;
  Phase29 = **ELIGIBLE_NOT_STARTED**; Phase30 = **NOT_STARTED**.
- 0 ROUTER_HOLDOUT reads / 0 VAL808 reads / 0 TEST reads; 0 training, 0 model forwards,
  0 OOF/membership/metric/bootstrap recomputation during the repair.

Terminal: `PHASE28_CANONICAL_CLOSURE_REPAIRED__EXECUTED_FULL_18_RUN_HISTORY_NOTEBOOK_FROZEN__SCIENTIFIC_ARTIFACTS_UNCHANGED__PHASE29_ELIGIBLE_NOT_STARTED`

*STOP. DO NOT START PHASE29. DO NOT START PHASE30. DO NOT OPEN ROUTER_HOLDOUT. DO NOT OPEN TEST.*

<!-- PHASE29_SPEC_V1_1 -->
## Phase 29 specification — v1.1 (additive)

* Phase29 specification = `COMPLETE_FROZEN_V1_1`
* Phase29 = `EXECUTION_ELIGIBLE_NOT_STARTED`
* GlobalMedFiLM fixed across seeds
* BARR downstream stack seeds = 42 / 123 / 3407
* `ROUTER_HOLDOUT` remains Phase30 only
* TEST remains Phase39 only
* Original blocked terminal `PHASE29_BLOCKED__REPRODUCIBILITY_TRAINING_SCOPE_UNRESOLVED` preserved as provenance.

---

## Phase 30 — Final Development Validation Benchmark (ONE-SHOT ROUTER_HOLDOUT)

**Status:** `COMPLETE_WITH_PROTOCOL_DEVIATION` · `SCIENTIFIC_RESULT_PRESERVED` ·
**NOT** `COMPLETE_CANONICAL`.

* `ROUTER_HOLDOUT` = `OPENED_AND_FROZEN` (n = 875; one-shot; no rerun).
* Result (frozen, not recomputed): macro ΔDice **+0.0017390308610248934**, 95% CI
  **[0.00111729355352301, 0.0024049809029647283]** → **PRESERVATION_ASSERTED = true**;
  p-values computed = 0.
* **Protocol deviation (permanent):** the Stage-B scientific scoring source
  (`scripts/analysis/phase30_execution_stage_b.py`, SHA `9331c75b…`) was authored ~2.9 s **after** the
  irreversible first-open marker (`2026-10-04T03:15:34+00:00`) and was **not** in the pre-open source
  freeze. Not retroactively repairable; not relabelled governance-only.
* **Mitigating evidence:** barrier PASS; GT reads at barrier 0; GT read exactly once (875); no second
  GT pass; no model rerun; no metric recomputation; no bootstrap regeneration; no artifact mutation;
  finalize governance-only; TEST reads 0; training 0.
* **Evidence class:**
  `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`.
* **Reporting:** the deviation must accompany any publication/reporting claim; no
  "COMPLETE_CANONICAL" / "fully preregistered" / "no protocol deviations" wording is permitted.
* **Phase31 eligibility:** `ELIGIBLE_WITH_PHASE30_PROTOCOL_DEVIATION_QUALIFIER` — Phase31 NOT started.
* Preserved terminals: execution terminal `f511fdc2…`, blocked-after-first-open terminal
  `75faa3ed…`, 19/20 reconciliation final check `1e86a3a5…` (all byte-for-byte).

---

## Phase 31 — Statistical Significance & Hypothesis Testing (GOVERNANCE-ONLY CLOSURE)

**Status:** `COMPLETE_CANONICAL` · **GOVERNANCE-ONLY STATISTICAL CLAIM-PROVENANCE ADJUDICATION** ·
**NO NEW STATISTICAL EXECUTION** · revision `ra_medfilm_barr_phase31_statistics_v1_1`.

* **Conclusion:** **NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE** (not "no significance
  exists" / "not significant" / "failed to reach significance").
* Hypothesis distribution (10 candidates): 0 confirmatory / 1 method-incomplete / 5
  already-adjudicated / 2 descriptive-only / 1 post-hoc exploratory / 1 forbidden-or-out-of-scope.
* Test registry: T01–T04 all `execution_authorized = false` and `execution_eligible = false`;
  confirmatory executable = 0; exploratory executable = 0.
* Phase30 qualifier carried forward (mandatory):
  `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`.
  Phase30 remains `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL`; result unchanged.
* `ROUTER_HOLDOUT` = `OPENED_AND_FROZEN__NO_PHASE31_RAW_REREAD`; `TEST` = `LOCKED_UNTIL_PHASE39`;
  **Phase32 = `ELIGIBLE_NOT_STARTED`**.
* Terminal: `PHASE31_STATISTICAL_CLAIM_GOVERNANCE_COMPLETE_CANONICAL__NO_NEW_CONFIRMATORY_OR_EXPLORATORY_STATISTICAL_EXECUTION_ELIGIBLE_OR_REQUIRED__PHASE30_PROTOCOL_DEVIATION_QUALIFIER_PRESERVED__PHASE32_ELIGIBLE_NOT_STARTED`.

---

## Phase 32 — External Dataset & Domain Shift Evaluation (GOVERNANCE-ONLY CLOSURE)

**Status:** `COMPLETE_CANONICAL` · **Closure class:**
`GOVERNANCE_ONLY_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_CLOSURE__NO_NEW_EXTERNAL_EXECUTION` ·
revision `ra_medfilm_barr_phase32_external_domain_shift_v1_0`.

* **Conclusion:** `NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE` — **no external execution performed**.
* 19 discovered candidates; 9 historically outcome-exposed; 8 `HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK`;
  2 overlap-risk; 4 provenance-ambiguous; 5 task-mismatch; **0 primary / 0 secondary / 0 stress-test**.
* Reviewer notebooks packaged: `phase_31_statistical_significance/phase31_statistical_significance_review.ipynb`
  and `phase_32_external_validation/phase32_external_domain_shift_review.ipynb` (both read-only).
* Phase30 qualifier remains mandatory; Phase30 not upgraded. `ROUTER_HOLDOUT` = `OPENED_AND_FROZEN__NO_PHASE32_REREAD`;
  `TEST` = `LOCKED_UNTIL_PHASE39`; **Phase33 = `ELIGIBLE_NOT_STARTED`**.
* Terminal: `PHASE32_EXTERNAL_DOMAIN_SHIFT_GOVERNANCE_COMPLETE_CANONICAL__NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE_AND_NO_EXTERNAL_EXECUTION_PERFORMED__PHASE31_AND_PHASE32_REVIEWER_NOTEBOOKS_PACKAGED__PHASE30_QUALIFIER_PRESERVED__PHASE33_ELIGIBLE_NOT_STARTED`.

---

## Phase 33 — Final System Failure & Boundary Error Analysis (PRE-ANALYSIS SPECIFICATION)

**Status:** `SPEC_COMPLETE` — **failure analysis NOT executed** · revision
`ra_medfilm_barr_phase33_failure_boundary_v1_0`.

* Eligible: **table-only** and **derived non-pixel** descriptive failure analysis from frozen
  Phase30 tables.
* Ineligible: boundary metric (`FINAL_SYSTEM_BOUNDARY_ERROR_NEW_COMPUTATION_ELIGIBLE=false`),
  component/object metric, qualitative gallery, prediction-pixel, raw image, raw GT, model rerun.
* Hard-case procedure frozen with **0 cases selected**; 0 qualitative panels generated.
* Phase11 failure evidence (KUB VAL280, 4 architectures) preserved as **historical descriptive only**;
  numeric thresholds **not** transferred.
* Phase30 qualifier remains mandatory; `ROUTER_HOLDOUT` raw not reopened; `TEST` `LOCKED_UNTIL_PHASE39`;
  **Phase34 not started**.
* Reviewer notebook: `phase_33_final_failure_analysis/phase33_failure_boundary_spec_review.ipynb`.
* Terminal: `PHASE33_FAILURE_BOUNDARY_SPEC_COMPLETE__POPULATION_ARTIFACT_FAILURE_TAXONOMY_BOUNDARY_PROVENANCE_HARD_CASE_AND_ANALYSIS_TIERS_FROZEN__TABLE_ONLY_AND_DERIVED_NONPIXEL_EXECUTION_ELIGIBLE__BOUNDARY_COMPONENT_QUALITATIVE_RAW_AND_RERUN_INELIGIBLE__EXECUTION_ELIGIBILITY_DETERMINED_NOT_STARTED`.

### Phase 33 — v1.1 taxonomy summary reconciliation

Top-level failure-family summary partition repaired (v1.0 `eligible_families` erroneously listed all
13). Corrected: **7 eligible / 6 ineligible / 13 total · overlap 0 · disjoint · exhaustive**.
`EMPTY_PREDICTION` eligible **only** as the Dice-0 proxy. **No science changed**; execution eligibility
unchanged; execution **not started**; Phase34 **not started**. Terminal:
`PHASE33_FAILURE_BOUNDARY_SPEC_V1_1_COMPLETE__FAILURE_TAXONOMY_ELIGIBLE_INELIGIBLE_SUMMARY_PARTITION_RECONCILED__7_ELIGIBLE_6_INELIGIBLE_DISJOINT_AND_EXHAUSTIVE__TABLE_ONLY_AND_DERIVED_NONPIXEL_EXECUTION_ELIGIBLE__NO_SCIENCE_CHANGED__EXECUTION_ELIGIBLE_NOT_STARTED`.

### Phase 33 — TIER_0/TIER_1 execution (FAIL-CLOSED BLOCK)

Authorized TIER_0/TIER_1 descriptive execution **blocked at pre-analysis**: the LOW_OVERLAP
realization rule is not exactly frozen (target Dice field ambiguous; comparison operator and
missing/NaN handling absent). **No results computed**; no partial outcome analysis. Preflight 11/11
pass (n=875, groups=628). Terminal:
`PHASE33_TIER0_TIER1_EXECUTION_BLOCKED_PREANALYSIS__LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN__NO_RESULTS_COMPUTED`.
