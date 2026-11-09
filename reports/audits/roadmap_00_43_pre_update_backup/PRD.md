# PRD — Product / Research Requirements

## Phase25E policy evaluation complete — current state (2026-10-01)

Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: **COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: **COMPLETE_FROZEN**. Phase25F post-safety specification v1.0 (`ra_medfilm_barr_post_safety_v1_0`): **COMPLETE_FROZEN** (execution **COMPLETE_CANONICAL**). Phase25G specification v1.1: **COMPLETE_FROZEN**; Phase25G: **COMPLETE_CANONICAL** (ROUTER_DEVELOPMENT only; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30). **Phase25 = COMPLETE_CANONICAL**; Phase26 = **ELIGIBLE_NOT_STARTED**.

The normalized incremental action cost is exactly `3,230,662,656 / 31,551,740,928` (`1051648/10270749`, approximately `0.10239253242387678`) for available actions; unavailable actions cost zero and are FORCED_SKIP. Pre-gate router overhead is `36,160` Conv/Linear MACs, separate from action cost. All compute is **ANALYTICAL MAC LOWER BOUND**, never measured latency.

Lambdas `{0.00, 0.25, 0.50, 1.00}` and budgets `{0%, 10%, 25%, 50%, 100%}` are frozen. All 4,957 DEV rows are action-available; exact top-K counts are `{0, 495, 1239, 2478, 4957}`. Rank by score descending, sample_id ascending. C6 uses negative predicted ROI area, a prospective geometry heuristic. Random priorities (PCG64 seed 42) and 45 label-blind memberships are frozen before outcomes. Under constant action cost, C7 and C8 have **identical membership at every fixed budget and lambda**; they are not independent evidence.

The 45 frozen OOF memberships were joined to the frozen Phase25C paired-gain outcomes on ROUTER_DEVELOPMENT only (4957). Statistics (domain-stratified group bootstrap, 2000 replicates, seed 42) and final-router DEV thresholds were frozen **before** the outcome join. Result: under the frozen PRIMARY statistic (raw paired two-sided p), C7 **significantly beats every simple GT-free proxy on precision@budget at the 10% and 25% budgets**, the advantage shrinking to non-significance at 50% (Holm-Bonferroni retained only as a secondary sensitivity: 10%); preservation holds; a usable accuracy-compute frontier exists. H1 is scoped to the tight and medium budgets (10%/25%).

The frozen final benefit-router checkpoint was loaded once and run in a single outcome-blind forward pass over the 4,957 ROUTER_DEVELOPMENT feature rows (no global-model forward, no regional-refiner forward, no training); no lambda was selected; C9 post-safety was not evaluated. ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39.

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





**Purpose:** Define *what* this project is trying to achieve and *why* — the goal,
motivation, task definition, scope, phase roadmap, success criteria, and non-goals.
It is the "why" document; see [ARCHITECTURE.md](ARCHITECTURE.md) for "how it is built",
[RULES.md](RULES.md) for constraints, [DESIGN.md](DESIGN.md) for experimental design,
[TASKS.md](TASKS.md) for roadmap status, [MEMORY.md](MEMORY.md) for operational handoff.

**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)
**Strategy revision:** **SR-1** (Regional-Aware Multi-Domain FiLM) — status **ADOPTED**;
method name **RA-MedFiLM-BARR**

**Canonical source paths (this document is derived from these, never from memory):**
- `PROJECT_MASTER_PLAN.md` — goal, domains, governance, 41-phase progression
- `PROJECT_CONTEXT.md` — historical handoff context (see conflict warning below)
- `ANTIGRAVITY_WORKFLOW.md` — agent operating contract
- `manifests/manifest_registry.md` / `.json` — manifest versions
- `reports/audits/antigravity_current_state.json` — live phase/run state
- `reports/audits/phase11_clean_v3_failure_analysis_audit.*` — Phase-11 evidence
- `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv` — Phase-11 → Phase-12 bridge

> **Fact / proposal classification is mandatory in this pack.** Every substantial claim is
> one of: `VERIFIED_CURRENT_FACT` · `HISTORICAL_PROVENANCE` ·
> `SUPERVISOR_ADOPTED_STRATEGIC_DIRECTION` · `PROPOSED_FUTURE_DESIGN` · `FUTURE_EXPERIMENT`.
> A proposed design **MUST NOT** be written as a verified fact.

---

## 1. Goal and Motivation

Build a **rigorous, publication-quality medical image segmentation framework** suitable for
a top-tier Q1/A* paper.

**Current research system: `RA-MedFiLM-BARR`** — Regional-Aware, Multi-Domain,
FiLM-Conditioned **binary** semantic segmentation with **Benefit-Aware Regional Refinement**.
The global model and the regional refiner are **implemented, trained and frozen**
(Phase-21 / Phase-25A); the benefit router is **TRAINED / FROZEN in Phase25D (COMPLETE_CANONICAL)**.
Phase25B and Phase25C are COMPLETE canonical; Phase25E scientific policy evaluation is **COMPLETE_FROZEN**.

### Primary objective

Develop and evaluate a **shared multi-domain medical segmentation system that predicts the
expected benefit of OPTIONAL regional refinement BEFORE paying for the refinement
computation.**

### Key desired properties

- **GT-free routing at inference** (the router never sees ground truth).
- **Global fallback** — the global path is always available as a safety net.
- **Explicit compute-awareness** — refinement cost is modelled, not ignored.
- **Shared multi-domain design** (one backbone conditioned by task/domain).
- A **measurable segmentation-vs-compute frontier.**
- A **preservation criterion** (regional machinery must not degrade per-domain performance).
- **Reproducible methodology** (frozen artifacts, hashed manifests/checkpoints).

### Explicit non-promises

Not certified · not causal · not guaranteed · not "first-ever" · not mobile-ready yet ·
not real-time yet · not globally resource-optimal · not guaranteed performance-preserving
until non-inferiority evidence exists.

### Scientific hypothesis (SR-1) — a hypothesis to be validated

> A single global segmentation scale may be insufficient across heterogeneous medical
> domains and object scales, and **adaptive regional processing may recover small/local
> difficult targets while preserving global performance.**

This is a **hypothesis**, not an established result. Phase-22 evidence already shows the
regional benefit is **strongly heterogeneous**, and **always-on regional HURTS in
aggregate** — which is precisely why benefit-aware routing (rather than always-on
refinement) is the research object.

Motivation is scientific credibility: every claim must be traceable to frozen artifacts,
reproducible from hashed manifests/checkpoints, and free of leakage or TEST contamination.

## 2. Task Definition

**Binary semantic segmentation.** For every domain the model predicts a single
foreground/background mask.

| Domain | Foreground | Background |
|---|---|---|
| ISIC 2018 | lesion | background |
| BUSI | breast lesion | background |
| Kvasir-SEG | polyp | background |
| KUB-StoneX | stone | background |

### KUB foreground rule (canonical, non-negotiable)

```
BACKGROUND : mask == 0
FOREGROUND : mask > 0
```

Native KUB masks use a heterogeneous, category-correlated nonzero label vocabulary —
`{0,255}`, `{0,1}`, `{0,2}`, `{0,3}`, `{0,1,2}` all occur. **Every nonzero value is
foreground.** Code must NEVER test `mask == 1`. Defined once in `src/utils/targets.py`
(`binarize_mask`, `FOREGROUND_RULE = "mask > 0"`).

### Kidney / Bladder / Ureteric are METADATA, not classes

`PROJECT_MASTER_PLAN.md` §2: *"Kidney, Bladder, and Ureteric are subgroup metadata, not
semantic classes."* They are used for **stratified reporting** — never as pixel class
channels. The model has **1 output channel**. **Do NOT manufacture multiclass masks.**

## 3. Domains / Tasks

| Task ID | Domain | Modality | Target |
|---|---|---|---|
| 0 | ISIC 2018 | Dermatology / skin | Skin lesion |
| 1 | BUSI | Breast ultrasound | Breast lesion |
| 2 | Kvasir-SEG | GI endoscopy | Polyp |
| 3 | KUB-StoneX | Urinary radiography | Stone |

Initial experiments use **true task IDs**. Automatic domain routing is a separate future
module and must not contaminate the core segmentation study. Manual prediction is KUB-only
(`predict_kub`); `predict(..., task='auto')` raises `NotImplementedError` — **automatic
routing is NOT operational**.

## 4. Strategy Revision SR-1 — adopted direction

**Original roadmap (historical):** standalone KUB regional development, followed later by a
separate multi-domain FiLM architecture.

**Strategy Revision SR-1 (supervisor-adopted):** reinterpret the KUB regional work as
**reusable regional-mechanism development** intended for eventual integration into
`RA-MedFiLM-Seg++`. Existing completed phases remain valid; history is **not** rewritten as
though SR-1 always existed.

**KUB is reframed as the REGIONAL-MECHANISM DISCOVERY AND VALIDATION LABORATORY** — not
wasted work. The scientific chain:

```
clean data
  -> KUB characterization
  -> tiny-object taxonomy
  -> global baselines
  -> four-model failure analysis
  -> oracle regional-resolution test
  -> GT-free localization feasibility
  -> regional integration gate
  -> regional mechanism development
  -> multi-domain global model
  -> global MedFiLM
  -> regional-aware MedFiLM
  -> RA-MedFiLM-Seg++
```

The final paper should present a **causal development story**, not two unrelated systems.

### Proposed future architecture (SR-1) — `PROPOSED_NOT_IMPLEMENTED`

Intended components: modality/input adaptation · shared global segmentation representation ·
task/domain FiLM conditioning · GT-free region proposal/localization ·
higher-effective-resolution regional processing · regional/refinement representation ·
scale/region-aware FiLM conditioning · adaptive global-regional fusion/routing ·
final binary segmentation output.

The original design described the future direction. The global model, regional refiner and
benefit router have since been trained and frozen through Phase25D. The resource-gate policy evaluation
is now COMPLETE_FROZEN (Phase25E); the complete integrated routing system remains to be validated in
later phases (Phase25F post-safety onward).

## 5. Phase Roadmap (00–40)

41 phases in four stages (`PROJECT_MASTER_PLAN.md` §7), with SR-1 reinterpretations:

- **Stage A — KUB Regional & Tiny-Object Development (00–18)** — Phases 14–18 are
  `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` (conditional, not automatic)
- **Stage B — Multi-Domain Harmonization & RA-MedFiLM Architecture (19–26)**
- **Stage C — Multi-Domain Rigor, Ablation, Reproducibility & Clinical Evidence (27–37)**
- **Stage D — Protocol Freeze, Single-Pass Test Benchmark & Publication (38–40)**

Per-status detail in [TASKS.md](TASKS.md). The three most important gates:

- **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** (§7) — decides whether the regional
  mechanism is promoted, revised, or dropped.
- **Phase 38** — manuscript protocol & checkpoint freeze.
- **Phase 39** — the **only** phase in which the untouched TEST cohort is evaluated.
- **Phase 40** — publication package & reproducibility audit.

## 6. Success Criteria

1. **Leakage-free evidence** — all development results traceable to `phase4_v3`
   (leakage status `REMEDIATED`, Phase-05 Part 1E).
2. **Reproducibility** — unique experiment IDs with hashed config / history / `best.pt` /
   `latest.pt`, and deterministic review notebooks.
3. **Evidence-gated regional mechanism** — the regional mechanism is promoted **only** if
   Phase 12/13 evidence passes the gate; a negative result is a legitimate outcome.
4. **Multi-domain preservation** — adding FiLM/regional machinery must not degrade
   per-domain performance (Phase 27).
5. **Statistical honesty** — no superiority claim from a single seed; significance only when
   actually tested with paired tests, CIs, effect sizes (`PROJECT_MASTER_PLAN.md` §10).
6. **Single-pass TEST** — TEST evaluated exactly once, in Phase 39, after Phase 38 freeze.
   No tuning after TEST access.

## 7. REGIONAL_INTEGRATION_GATE_AFTER_PHASE13

Formal governance gate occurring **after Phase 12 and Phase 13**.

| Outcome | Meaning | Action |
|---|---|---|
| **GO** | Oracle regional processing helps **AND** predicted localization retains meaningful practical utility | Promote the regional mechanism toward RA-MedFiLM-Seg++ |
| **REVISE_LOCALIZER** | Oracle helps **BUT** predicted localization loses too much benefit | Do **not** abandon the regional hypothesis; redesign/localizer work first |
| **NO_GO** | Even oracle regional processing provides insufficient meaningful benefit | Do **not** force regional complexity into the final FiLM architecture; proceed with global multi-domain MedFiLM and document the negative regional evidence |

> **No numerical GO/NO-GO thresholds are defined in this documentation pack.** Those
> criteria must be **prospectively frozen** before inspecting the relevant Phase-12/13
> results ([RULES.md](RULES.md) §12).

## 8. Non-Goals

- **No multi-class KUB segmentation.** Kidney/Bladder/Ureteric are not classes.
- **No TEST usage before Phase 39** — not for training, validation, threshold, architecture,
  loss, preprocessing, proposal, fusion, FiLM-design, or checkpoint selection.
- **No automatic domain routing yet** (future work).
- **No clinical mm-scale size claims** — the size taxonomy is dataset-relative
  (`component_ratio`), not clinical millimetres.
- **No silent migration of historical v2 results into clean-v3 claims.**
- **No claiming the system as validated, frozen, or novel** before the corresponding
  evidence phases. Specifically: **no claim that the benefit router works, that routing
  helps, or that refinement is worth its cost** until the router is trained and evaluated.
- **No "certified / causal / guaranteed / counterfactual / first-ever" claims.**
- **No "mobile-ready", "real-time", or "globally resource-optimal" claims.**
- **No deployment-unavailable metadata as model conditioning.** Every metadata field used in
  future multi-domain work **MUST** be classified as `CONDITIONING_ALLOWED`,
  `REPORTING_ONLY`, or `FORBIDDEN_AS_INPUT` ([RULES.md](RULES.md) §13). Kidney/Bladder/
  Ureteric remain `REPORTING_ONLY`.

## 9. HISTORICAL_v2 vs CLEAN_v3 separation (mandatory framing)

| Aspect | HISTORICAL_v2 | CLEAN_v3 |
|---|---|---|
| Manifest | `phase4_v2` (root `manifests/*.csv`) | `phase4_v3` (`manifests/phase4_v3/`) |
| Status | `HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT` | `CANONICAL_ACTIVE_DEVELOPMENT` |
| Leakage | `KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY` | `REMEDIATED` |
| Global split | TRAIN 5913 / VAL 845 / TEST 1683 | TRAIN 5832 / VAL 808 / TEST 1683 / QUAR 118 |
| KUB split | TRAIN 1979 / VAL 283 / TEST 558 | TRAIN 1978 / VAL 280 / TEST 558 / QUAR 4 |
| Taxonomy | `kub_size_v1` (IMMUTABLE) | `kub_size_clean_v3_v1` (FROZEN) |
| Use | Reproduce historical Phases 06–15 only | All future scientific development |

> TEST is **byte-identical** between v2 and v3
> (`9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`).
> **No v2 result may be silently presented as a clean-v3 result**, and no v3 result may be
> compared to v2 as if the splits matched.

## 10. ⚠ Material source conflicts (recorded)

Detected while deriving this pack; recorded, not silently resolved:

| # | Source | Conflicting claim | Evidence-based reality | Material? |
|---|---|---|---|---|
| C1 | `PROJECT_CONTEXT.md` | "No clean-rerun phase has been executed." | Clean-v3 **Phases 05–12 are COMPLETE**; **Phase 13 Part 1A (protocol/definition) is COMPLETE**; Part 1B is not authorized | **YES** |
| C2 | `PROJECT_CONTEXT.md` | "The strongest global KUB baseline is **UNet++**" — a winner declaration | `phase10_winner_declared = False`; that is a **historical v2** statement | **YES** |
| C3 | `PROJECT_MASTER_PLAN.md` | Phase 09 clean-v3 "**NOT started**" | Completed 2026-09-20; best ep 44, Dice 0.7406133413314819 | **YES** |
| C4 | `ANTIGRAVITY_WORKFLOW.md` | "CURRENT PHASE: 13B"; "NEXT AUTHORIZED ACTION: NONE" | Live state: **Phase 12 COMPLETE / PASS**; **Phase 13 Part 1A COMPLETE** (protocol/definition only); Part 1B not authorized | **YES** |
| C5 | `antigravity_current_state.json` | Earlier `phase10_unetpp_started: False` | **Repaired 2026-09-21** (Phase-11 preflight audit); now consistent | Resolved |
| C6 | `antigravity_current_state.json` | Attention U-Net `val_precision_at_best = None` | Resolved as **HISTORY_NATIVE**: `0.7729140812402236` / `0.7922248481868364` | Minor |
| C7 | `src/utils/test_lock.py` | Lock `manifest_version` labelled `phase4_v2` | TEST is byte-identical v2↔v3, so the lock is valid | No |

**Disposition:** C1–C4 remain material. Treat
`reports/audits/antigravity_current_state.json` + per-run audits as the live authority.
Do not "fix" stale top-level files without authorization.

---

**Cross-links:** [ARCHITECTURE.md](ARCHITECTURE.md) · [RULES.md](RULES.md) ·
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
