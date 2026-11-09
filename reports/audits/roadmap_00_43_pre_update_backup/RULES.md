# RULES — Hard Governance Constraints

## Phase25E policy evaluation complete — current state (2026-10-01)

Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: **COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: **COMPLETE_FROZEN**. Phase25F post-safety specification v1.0 (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN** (execution **COMPLETE_CANONICAL**). Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30). **Phase25 = COMPLETE_CANONICAL**; Phase26 = **ELIGIBLE_NOT_STARTED**.

The normalized incremental action cost is exactly `3,230,662,656 / 31,551,740,928` (`1051648/10270749`, approximately `0.10239253242387678`) for available actions; unavailable actions cost zero and are FORCED_SKIP. Pre-gate router overhead is `36,160` Conv/Linear MACs, separate from action cost. All compute is **ANALYTICAL MAC LOWER BOUND**, never measured latency.

Lambdas `{0.00, 0.25, 0.50, 1.00}` and budgets `{0%, 10%, 25%, 50%, 100%}` are frozen. All 4,957 DEV rows are action-available; exact top-K counts are `{0, 495, 1239, 2478, 4957}`. Rank by score descending, sample_id ascending. Random priorities (PCG64 seed 42) and 45 label-blind memberships were frozen before outcomes. Under constant action cost, C7 and C8 have **identical membership at every fixed budget and lambda**; they are not independent evidence.

The 45 frozen OOF memberships were joined to the frozen Phase25C paired-gain outcomes on ROUTER_DEVELOPMENT only (4957). The statistics (domain-stratified group bootstrap, 2000 replicates, seed 42) and the final-router DEV thresholds were frozen **before** the outcome join. Result: under the frozen PRIMARY statistic (raw paired two-sided p), the learned paired-gain router (C7) **significantly beats every simple GT-free proxy on precision@budget at the 10% and 25% budgets**, with the advantage shrinking to statistical non-significance at 50% (Holm-Bonferroni retained only as a secondary sensitivity: 10%); preservation holds (macro-domain lower 95% CI bound > -0.005, no domain collapse); a usable accuracy-compute frontier exists. **H1 is scoped to the tight and medium budgets (10%/25%)** (Level-2 novelty); it is not a uniform win.

The frozen final benefit-router checkpoint was loaded once and run in a single outcome-blind forward pass over the 4,957 ROUTER_DEVELOPMENT feature rows (no global-model forward, no regional-refiner forward, no training); no lambda was selected; the resource gate was not calibrated for deployment beyond the frozen DEV-score thresholds; the C9 post-safety comparator was not evaluated. ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39.

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





**Purpose:** The non-negotiable MUST / MUST NOT rule set. When a rule and a convenience
conflict, the rule wins. Violating a MUST is a scientific-integrity event: stop and return
`CHECK_REQUIRED`. See [PRD.md](PRD.md) for goals, [ARCHITECTURE.md](ARCHITECTURE.md) for
structure, [DESIGN.md](DESIGN.md) for experiment design, [TASKS.md](TASKS.md) for status,
[MEMORY.md](MEMORY.md) for operational handoff.

**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)
Phase25E policy evaluation COMPLETE_FROZEN;
Phase25F post-safety specification v1.0 COMPLETE_FROZEN
**Strategy revision:** **SR-1** (Regional-Aware Multi-Domain FiLM) — status **ADOPTED**;
method name **RA-MedFiLM-BARR**

**Canonical source paths:**
- `PROJECT_MASTER_PLAN.md` §4–6, §8–11 (governance, test lock, provenance, notebook, statistics)
- `ANTIGRAVITY_WORKFLOW.md` (agent contract, TEST lock, what requires approval)
- `PROJECT_CONTEXT.md` §Governance
- `src/utils/test_lock.py`, `manifest_guard.py`, `device.py`, `run_lock.py`, `targets.py`
- `reports/audits/antigravity_current_state.json` (live `test_content_reads: 0`)

---

## 1. TEST lock — absolute

- **MUST NOT** use TEST for training, validation, checkpoint selection, threshold tuning,
  architecture selection, loss selection, preprocessing selection, **proposal selection,
  fusion selection, FiLM-design selection**, or hyperparameter tuning.
- **MUST** maintain **0 TEST content reads** during development.
- TEST is evaluated **only in Phase 39**, after protocols/thresholds/architectures are
  frozen in Phase 38. **No tuning after TEST access.**
- `KUBDataset` **MUST** raise on TEST construction unless `allow_test=True` (never set in
  development). `src/utils/test_lock.py` provides lock verification.
- **External data is locked** from tuning as well.

## 2. Manifest discipline — v3 active, v2 historical

- **MUST** use `phase4_v3` (`manifests/phase4_v3/`) for all new scientific development.
- **MUST NOT** silently load root `manifests/train.csv` (that is **historical v2** evidence).
- **MUST** call `validate_manifest_version_strict('phase4_v3')` before loading.
- **MUST NOT** modify or delete `phase4_v2` — required to reproduce historical Phases 06–15.
- **MUST NOT** present a v2 result as a clean-v3 result, or compare v2↔v3 numbers as if the
  splits matched.

## 3. Leakage

- Historical v2 leakage status is
  `KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY`; v3 is `REMEDIATED` (Phase 05 1E).
- **MUST** preserve patient-level disjointness between TRAIN and VAL (verified: overlap 0).
- **MUST NOT** reintroduce quarantined or duplicate-grouped samples into development splits.

## 4. Frozen taxonomy — `kub_size_clean_v3_v1`

- **MUST** use `kub_size_clean_v3_v1` for clean-v3 KUB size work
  (`reports/audits/kub_size_clean_v3_v1_thresholds.json`).
- **MUST NOT** modify, recompute, or conflate it with historical `kub_size_v1` (**IMMUTABLE**).
- **MUST NOT** use the taxonomy to retune training; it is reporting/stratification metadata.
- **MUST NOT** apply KUB size thresholds directly to other domains; each domain needs its own
  TRAIN-derived scale characterization if scale-stratified analysis is required.

## 5. Foreground rule — binary segmentation is FROZEN

- **MUST** define KUB foreground as `mask > 0` via `src/utils/targets.py::binarize_mask`.
- **MUST NEVER** test `mask == 1`. Raw labels 1/2/3/255 are all foreground.
- **MUST NOT** reinterpret raw labels as multiclass pixel classes, and **MUST NOT**
  manufacture multiclass masks for any domain.
- All four domains remain **binary** semantic segmentation (lesion/polyp/stone vs background).

## 6. Device / CUDA — fail loud

- **MUST** use `get_device(require_cuda=True)` on canonical paths.
- **MUST NOT** silently fall back to CPU. If CUDA is unavailable: **STOP / CHECK_REQUIRED**.
- Expected GPU: NVIDIA GeForce RTX 3060 Ti; interpreter `D:\Softfors\jup\.venv\Scripts\python.exe`.

## 7. Scientific change control — STOP before changing science

- **MUST STOP and return `CHECK_REQUIRED`** before any change to: architecture, loss,
  learning rate / weight decay, batch size, resolution, augmentation, scheduler, patience,
  threshold, seed, checkpoint metric, preprocessing, **proposal mechanism, fusion, gate,
  FiLM site, conditioning input, or metadata input**.
- Agents **MAY** fix mechanical / path / logging bugs without authorization.
- **MUST NOT** tune because metrics look good or bad; **MUST NOT** reduce batch size
  autonomously on OOM; **MUST NOT** silently skip NaN/Inf batches (STOP instead).
- **MUST NOT** autonomously advance to the next phase or train unapproved models.

## 8. Single-writer and resume

- **MUST** acquire `src/utils/run_lock.py` before training; an **active** conflict
  **MUST** fail loudly.
- A **stale** lock **MAY** be reclaimed only after explicit inspection, with the recovery
  recorded.
- **MUST** resume with the **same** experiment ID. **MUST NOT** append `_retry`, `_v2`,
  `_new`, `_fix` for ordinary interruption recovery.
- **MUST** compare `latest.pt` against `history.csv` before resuming; if inconsistent, STOP.
- Exactly **one** training process per experiment ID.

## 9. Evidence, notebooks, statistics

- **MUST NOT** fabricate metrics, figures, tables, statistics, or epochs.
- **One-row-per-completed-epoch rule (MANDATORY for every training reviewer notebook).**
  `1 completed epoch = 1 table row`; the table **MUST** be complete and **untruncated**,
  built from the **immutable** `history.csv`; no missing epochs, no duplicate epochs;
  `history.csv` itself **MUST NOT** be modified. Applies later to regional-component
  training, localizer training (if epoch-based), multi-domain baseline training,
  Global MedFiLM, RA-MedFiLM-Seg++, and ablation/reproducibility runs.
- Notebooks are **display / analysis / audit** artifacts, **not training**. They **MUST**
  run top-to-bottom (Run All: unexecuted 0, errors 0), **MUST NOT** touch TEST, and
  **MUST** report reproducible SHA-256 hashes. **MUST NOT** auto-retrain on Run All.
- **MUST NOT** claim significance unless actually tested (paired testing, confidence
  intervals, effect sizes). **MUST NOT** claim superiority from a single seed.
- Reviewer VAL scope **MUST** be KUB-only (280 rows). **MUST NOT** let multi-domain
  (ISIC/BUSI/Kvasir) or `NOT_AVAILABLE` rows into a KUB gallery.
- Gallery subset means **MUST** be labelled `DETERMINISTIC_GALLERY_SUBSET_ONLY`.
- **MUST** keep Experiment A (`D:\Softfors\final\medfilm_seg_kub_extension`) unmodified.

## 10. Material vs cosmetic — blocking policy

| Class | Examples | Action |
|---|---|---|
| **MATERIAL (blocking)** | architecture, deep supervision, loss/weights, LR, WD, batch, accumulation, resolution, augmentation, scheduler, patience, threshold, seed, checkpoint metric, preprocessing, manifest version, taxonomy, TRAIN/VAL membership, TEST access, **proposal/fusion/gate/FiLM design, conditioning inputs** | **STOP → `CHECK_REQUIRED`**; requires supervisor authorization |
| **COSMETIC / GOVERNANCE (non-blocking, must be declared)** | fail-loud CUDA contract, centralized `mask > 0` helper, single-writer lock, NaN/Inf fail-loud guard, extra provenance/checkpoint metadata, clean experiment ID, taxonomy metadata binding, logging/path fixes | Proceed; record in the protocol-diff audit as `scientifically_material = False` |

Every clean-v3 rerun **MUST** produce a v2→v3 protocol-diff table with columns
`field, historical_v2, clean_v3, same_or_changed, change_reason, scientifically_material`.
**Unauthorized material differences MUST be 0**; if nonzero → `CHECK_REQUIRED`.

## 11. SR-1 architecture governance (adopted direction)

- **A.** No agent **MUST** implement or train `RA-MedFiLM-Seg++` before its authorized phase
  (Phase 24–26). The architecture is `PROPOSED_NOT_IMPLEMENTED`.
- **B.** No agent **MUST** skip **Phase 12**, **Phase 13**, and
  **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** before promoting the regional mechanism.
- **C.** Phases **14–18 are conditional** on that gate
  (`PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE`). They **MUST NOT** proceed automatically.
- **D.** No agent **MUST** autonomously redesign Phases 14–26.
- **E.** Any new architecture, conditioning input, proposal mechanism, fusion, gate, FiLM
  site, metadata input, loss, or threshold **MUST** have supervisor authorization.
- **F.** Metadata unavailable at deployment **MUST NOT** be silently used as model
  conditioning (see §13).
- **G.** Kidney/Bladder/Ureteric **MUST** remain metadata, not segmentation mask classes.
- **H.** TEST **MUST** remain Phase 39 only.
- **I.** The one-row-per-completed-epoch notebook rule (§9) **MUST** remain mandatory for
  all training phases.

## 12. Prospective gate freeze

- The **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** criteria (GO / REVISE_LOCALIZER /
  NO_GO) **MUST** be frozen **prospectively** — before inspecting the relevant Phase-12/13
  results.
- **MUST NOT** define numerical GO/NO-GO thresholds post hoc to fit observed results.

## 13. Metadata conditioning governance

Every metadata field used in future multi-domain work **MUST** eventually be classified as
one of:

- **`CONDITIONING_ALLOWED`** — legitimately available at inference/deployment time.
- **`REPORTING_ONLY`** — usable for stratified reporting, never as model input.
- **`FORBIDDEN_AS_INPUT`** — ground-truth-only or annotation-derived; cannot be an
  inference-time shortcut.

- **MUST NOT** automatically feed diagnosis, pathology result, GT subtype, or
  annotation-derived information into FiLM.
- **KUB Kidney/Bladder/Ureteric remain `REPORTING_ONLY`** unless future governance
  explicitly proves legitimate inference-time availability.

## 14. Current locked state (must be encoded consistently everywhere)

> **Updated 2026-10-01** (Phase25D canonical reviewer-notebook compliance repair complete).
> The Phase-11/12/13 statements historically recorded here are retained in
> [MEMORY_ARCHIVE_pre_2026_09_30.md](MEMORY_ARCHIVE_pre_2026_09_30.md) and the dated logs.

- **Phases 00–23 COMPLETE** (historical roadmap status preserved).
- **Phase 24 COMPLETE**; **Phase 24 v1.1** exact-spec freeze historical;
  **Phase 24 v1.2** router feature specification **COMPLETE** (RF-1/RF-2/RF-3 + D1 + D2).
- **Phase 25A COMPLETE canonical** — terminal
  `PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED`;
  refiner checkpoint `6d28608a…`; ROI-0.50 run **NONCANONICAL_PROTOCOL_DEVIATION** (preserved only).
- **Phase 25B COMPLETE canonical** — 202-D GT-free pre-refinement feature cache frozen
  (4957 × 202); handoff semantics repaired (`science_changed = false`).
- **Phase 25C COMPLETE canonical** — 4957 leakage-safe OOF paired refinement-gain labels frozen;
  at Phase25C completion, Phase25D was eligible/not started; it has since completed canonically.
- **Phase25D first blocked attempt = BLOCKED_ATTEMPT_PROVENANCE**.
- **Phase25D router training spec v1.2.1 = COMPLETE / FROZEN**.
- **Phase25D benefit router = COMPLETE_CANONICAL / TRAINED / FROZEN**.
- **Phase25E resource-gate specification = COMPLETE_FROZEN**.
- **Phase25E scientific policy evaluation = COMPLETE_FROZEN** (45 frozen OOF memberships joined to
  Phase25C outcomes on DEV; bootstrap + frontier + adjudication frozen).
- **Phase25F = EXECUTION_ELIGIBLE_NOT_STARTED** (post-safety specification v1.0 `ra_medfilm_barr_post_safety_v1_0` COMPLETE_FROZEN).
- **Phase25G = NOT_STARTED**.
- **TEST is locked until Phase 39.**
- The benefit router is **TRAINED / FROZEN**. The historical Phase-21/22 baselines are
  **TIED** — no winner is declared.

## 15. Consolidated hard rules (RA-MedFiLM-BARR)

1. **TEST remains locked until Phase 39.**
2. **ROUTER_HOLDOUT outcomes remain locked** until the designated one-shot evaluation.
3. **Existing VAL808 is continuity/development only** — not router training data.
4. **Never silently resolve a frozen-value conflict** — report `CHECK_REQUIRED`.
5. **Additive provenance only.** Historical artifacts are never deleted or overwritten.
6. **Never rename/delete a frozen artifact without an explicit migration record.**
7. **Historical noncanonical runs remain preserved** and scientifically excluded where declared.
8. **ROI threshold 0.30 ≠ segmentation threshold 0.50.**
9. **Feature extraction for the router must be pre-refinement and GT-free.**
10. **No refined features enter the pre-execution benefit router.**
11. **No architecture/hyperparameter changes based on holdout outcomes.**
12. **A blocked phase ⇒ do NOT manufacture a fake completion notebook.**
13. **Every completed scientific phase requires a real executed notebook.**
14. **Training notebooks include complete epoch tables.**
15. **Notebook build determinism must not trigger retraining.**
16. **Normalize nondeterministic execution metadata / stream chunking only when that
    normalization changes presentation/provenance bytes, not scientific content.**
17. **All checkpoint writes atomic.**
18. **RNG state restored on legitimate resume.**
19. **Assert generated artifacts exist; builder exit code alone is insufficient.**
20. **Never use pandas `~` directly on an object-dtype bool Series for fail-closed checks;
    cast to bool first.**
21. **If a specification is incomplete, STOP before execution.**

---

**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[DESIGN.md](DESIGN.md) · [TASKS.md](TASKS.md) · [MEMORY.md](MEMORY.md)

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
