# DESIGN — Experimental Design and Verified Results

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





**Purpose:** Record the *experimental design*: philosophy, exact clean-v3 split counts, the
two KUB acquisition regimes, the frozen taxonomy, the frozen training protocol, the
**verified** clean-v3 VAL results (no ranking), the **verified** Phase-11 failure evidence,
and the **proposed** SR-1 RA-MedFiLM design with its future ablation plan.
See [PRD.md](PRD.md) for goals, [ARCHITECTURE.md](ARCHITECTURE.md) for structure,
[RULES.md](RULES.md) for constraints, [TASKS.md](TASKS.md) for status,
[MEMORY.md](MEMORY.md) for handoff.

**Last verified:** 2026-10-01 — Phase25G integrated controlled development evaluation COMPLETE_CANONICAL (A7 vs A8 / C8 vs C9 / preservation / H3 frozen; Phase25 = COMPLETE_CANONICAL; Phase26 ELIGIBLE_NOT_STARTED; ROUTER_HOLDOUT RESERVED_UNOPENED_FOR_PHASE30; TEST LOCKED UNTIL PHASE39)
**Strategy revision:** **SR-1** — status **ADOPTED**; method name **RA-MedFiLM-BARR**

> **Separation is mandatory in this document:**
> `VERIFIED_EVIDENCE` (measured) · `PROPOSED_DESIGN` (not implemented) ·
> `FUTURE_EXPERIMENT` (not run). Never present one as another.

**Canonical source paths:**
- `manifests/phase4_v3/*` + `manifests/manifest_registry.*` — split counts
- `reports/audits/kub_size_clean_v3_v1_thresholds.json` — taxonomy quantiles
- `configs/phase09_clean_v3/`, `configs/phase10_clean_v3/` — frozen configs
- `experiments/*/history.csv` (clean-v3) — verified results
- `reports/audits/phase11_clean_v3_failure_analysis_audit.*` — Phase-11 evidence
- `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv` — Phase-11 → Phase-12 bridge
- `reports/audits/phase13_historical_localizer_protocol_reconstruction.*` — Phase-13 Part-1A
  historical reconstruction
- `reports/audits/phase13_clean_v3_localizer_protocol_candidate.*` — Phase-13 Part-1A clean-v3
  protocol candidate (superseded by the frozen artifact below)
- `reports/audits/phase13_clean_v3_localizer_protocol_frozen.*` — Phase-13 Part-1A-R1 frozen
  clean-v3 localizer protocol (**superseded for execution by R2**, preserved as provenance)
- `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.*` — Phase-13 Part-1A-R2
  **current SUPERVISOR-FROZEN R2** clean-v3 localizer protocol
- `reports/tables/phase13_r1_to_r2_protocol_diff.csv` — additive R1→R2 protocol diff
- `reports/tables/phase13_clean_v3_hard_tiny_replication_set.csv` — clean-v3 hard-Tiny cohort
- `reports/tables/phase13_clean_v3_global_empty_replication_set.csv` — clean-v3 global-empty cohort
- `reports/tables/phase13_historical_localizer_protocol_matrix.csv` — Phase-13 protocol matrix
- `reports/tables/phase13_clean_v3_training_population_spec.csv` — clean-v3 localizer population

---

## 1. Experimental philosophy

- **One variable at a time.** Clean-v3 reruns reproduce historical protocols exactly,
  changing only authorized governance/provenance fields ([RULES.md](RULES.md) §10).
- **Evidence over narrative.** Every verified number is traceable to a hashed artifact.
- **Frozen before comparison.** Protocols, thresholds, architectures frozen before any
  conclusion; TEST touched once, in Phase 39.
- **Seed discipline.** All clean-v3 runs use **seed 42**, single-seed → **no superiority
  claim is permitted** ([RULES.md](RULES.md) §9).
- **Evidence-gated complexity.** Regional machinery must **earn** inclusion via Phase 12/13
  and `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` — not by assertion.

## 2. REVISED SCIENTIFIC HYPOTHESIS (SR-1) — `PROPOSED` hypothesis

> A single global segmentation scale may be insufficient across heterogeneous medical
> domains and object scales, and **adaptive regional processing may recover small/local
> difficult targets while preserving global performance.**

`FUTURE_EXPERIMENT` — this is a hypothesis to be validated, **not** an established result.
Phase 11 provides *motivating* (not conclusive) evidence (§7).

## 3. Exact CLEAN-v3 split counts — `VERIFIED_EVIDENCE`

Global (`phase4_v3`, total 8441):

| Split | Count | Notes |
|---|---|---|
| TRAIN | 5832 | |
| VAL | 808 | |
| TEST | 1683 | **LOCKED**, byte-identical to v2 |
| QUARANTINED | 118 | excluded from development |

KUB subset: TRAIN **1978** · VAL **280** · TEST 558 (locked) · QUARANTINED 4.
VAL KUB composition: **Bladder_Stone 144, Kidney_Stone 112, Ureteric_Stone 24**.
VAL acquisition: **ROI 177, FULL_FIELD 103**. TRAIN/VAL patient overlap: **0**.

> Because KUB is only part of the global VAL (808), **any KUB VAL analysis MUST filter
> `dataset == "KUB"`**. Loading the full 808-row VAL silently mixes ISIC/BUSI/Kvasir — this
> error invalidated an earlier Phase-09 reviewer gallery
> (`INVALID_SUPERSEDED_CROSS_DOMAIN_SELECTION`).

## 4. FULL_FIELD vs ROI regimes, and the frozen taxonomy — `VERIFIED_EVIDENCE`

| | FULL_FIELD | ROI (crop) |
|---|---|---|
| Meaning | Full radiograph | Zoomed crop around a stone |
| Typical scale | Large (~2304–3072 px wide) | Small (tens–hundreds of px) |
| VAL count | 103 | 177 |

- **MUST** report FULL_FIELD and ROI separately; never pool without showing both.
- Taxonomy is calibrated on **FULL_FIELD** only; ROI = `ROI_NOT_PRIMARY_BINNED`.

**`kub_size_clean_v3_v1`** (status `FROZEN`, split TRAIN, scope FULL_FIELD):

| Property | Value |
|---|---|
| Foreground rule | `mask > 0` |
| Unit | connected component (connectivity **8**) |
| Metric | `component_ratio = component_pixels / (native_h * native_w)` |
| Quantiles (numpy default 'linear', float64) | Q25 **0.0001497998649691358** · Q50 **0.0003401438395182292** · Q75 **0.0008279682677469136** |
| Boundaries (lower-inclusive) | TINY `x ≤ Q25` · SMALL `Q25 < x ≤ Q50` · MEDIUM `Q50 < x ≤ Q75` · LARGE `x > Q75` |

Dataset-relative, **not** clinical millimetres.
Historical `kub_size_v1` (IMMUTABLE, v2 only): Q25 `0.0001499766777599` · Q50
`0.00033976472454305` · Q75 `0.0008266496069636999`. Never conflate.

> **SR-1 note:** KUB size thresholds **MUST NOT** be applied to other domains; each domain
> needs its own TRAIN-derived scale characterization ([RULES.md](RULES.md) §4).

## 5. Frozen training protocol (clean-v3 KUB runs) — `VERIFIED_EVIDENCE`

| Field | Value |
|---|---|
| Resolution | 512 · input/output channels 1 / 1 |
| Preprocessing | aspect-preserving resize + centre/symmetric pad; image BILINEAR, mask NEAREST; scaling [0,1]; extent `max(1, round(...))` |
| Loss | BCE + Dice, **0.5 / 0.5**, dice epsilon **1e-6** |
| Optimizer | **AdamW**, lr **1e-4**, weight decay **1e-4** |
| Scheduler | **CosineAnnealingLR**, T_max **100** (stepped per epoch, after train+val) |
| Batch / accum / effective | **4 / 1 / 4** |
| AMP | true · Seed **42** · Max epochs **100** |
| Early stopping | patience **15**, monitor **VAL macro Dice**, **strict `>`** (ties = bad epoch) |
| VAL | augmentation OFF, shuffle FALSE, KUB-only |
| Threshold | **0.5** (fixed) |
| Augmentation | hflip p=0.5, rot ±5°, brightness ±0.1, contrast ±0.1, vflip **false** |
| Init | random Kaiming, **no pretrained weights** |
| Epoch order | TRAIN → VAL → scheduler.step → improvement → early-stop → latest → best → stop |

Architecture-specific: UNet / Attention U-Net / UNet++ use **base_channels = 32**; UNet++
is `unetpp_nested_4_level_no_deep_supervision` (**deep supervision OFF**).

## 6. Verified CLEAN-v3 VAL results — `VERIFIED_EVIDENCE` (NO RANKING)

| Model | Experiment | Epochs | Best ep. | VAL Dice | VAL IoU | Precision | Recall |
|---|---|---|---|---|---|---|---|
| UNet | `phase9_kub_unet_baseline_seed42_512_clean_v3` | 59 | 44 | 0.7406133413314819 | 0.6253822445869446 | 0.7707186937332153 | 0.7839437127113342 |
| Attention U-Net | `phase10_kub_attention_unet_seed42_512_clean_v3` | 69 | 54 | 0.7525129853960107 | 0.6349387691368995 | 0.7729140812402236 | 0.7922248481868364 |
| UNet++ | `phase10_kub_unetpp_seed42_512_clean_v3` | 85 | 70 | 0.7641595156062713 | 0.6525442690586191 | 0.7996825971468945 | 0.7912384169561990 |
| DeepLabV3+ | `phase10_kub_deeplabv3plus_seed42_512_clean_v3` | 67 | 52 | 0.7509140344161673 | 0.6460492792430865 | 0.7943328495850855 | 0.7822983241135557 |

**NO RANKING · NO WINNER · SINGLE-SEED DESCRIPTIVE VAL.** The final descriptive Phase-10
comparison is **COMPLETE** (`phase10_clean_v3_final_baseline_comparison.ipynb`). DeepLabV3+
is `deeplabv3plus_resnet50_os16` (ResNet-50, no pretrained, os16, ASPP (6,12,18) + image
pooling, no aux head, 40,340,769 params).

**Complete epoch-by-epoch tables (mandatory rule).** One row per completed epoch,
untruncated, from the immutable `history.csv`, with derived reviewer-only columns
(`delta_val_dice_vs_previous_epoch`, `delta_best_metric`, `is_new_best`, `is_best_epoch`,
`epochs_since_best`). `history.csv` is never modified; unavailable fields show `N/A`.
Rows: UNet 59 · Attention U-Net 69 · UNet++ 85 · DeepLabV3+ 67.

## 7. Phase-11 verified failure evidence — `VERIFIED_EVIDENCE`

Manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1` · **KUB VAL 280** · 4 models ·
**reference model NOT selected** · historical replication anchor **UNet++**
(`HISTORICAL_REPLICATION_ANALYSIS_ANCHOR` only — **not** winner / best / Phase-12 reference).
Failure protocol: **`SUPERVISOR_FROZEN`** (frozen before inspection).

**Per-model clean-v3 Dice Q10** (bottom decile, ties included):
UNet `0.4693939398443986` · Attention U-Net `0.5360238052845407` ·
UNet++ `0.5618055568014564` · DeepLabV3+ `0.3784289703007593`.

**Shared failure — `ALL_FOUR_LOW`: 12 / 280.** `low_model_count` distribution:
`{0: 233, 1: 17, 2: 7, 3: 11, 4: 12}`.

**UNet++ anchored strata:** HD95 Q90 (valid only) `85.24095485204775`; valid/invalid
**274 / 6**. FP Q90 **5.0**; HIGH_FP count **31**.

**Empty predictions:** UNet 8 · Attention U-Net 3 · UNet++ 6 · DeepLabV3+ 11
(concentrated in FULL_FIELD).

**Object recall (eval-512, 8-conn, ≥1 px):** UNet `0.896341` · Attention U-Net `0.923780` ·
UNet++ `0.914634` · DeepLabV3+ `0.881098`.

**Multi-component native cases: 49.** Outcomes (complete / partial / miss):
UNet 30/16/3 · Attention U-Net 33/12/4 · UNet++ 33/11/5 · DeepLabV3+ 27/16/6.

**Regime gap (mean Dice): `0.2276`** (ROI ≫ FULL_FIELD for every model).

**Hard-case cohort: 16** (target 16, no underfilled strata). Selection SHA
`72f16916e9a9e86b047514842634ab7b73c245d131d5fbbd37db9fff171e3c46`.
Selection is **prediction-dependent by design** (unlike the prediction-independent Phase-10
gallery).

## 8. REGIONAL MECHANISM EVIDENCE CHAIN — `VERIFIED` → `FUTURE_EXPERIMENT`

```
clean data (Phase 05)                                    [VERIFIED]
  -> KUB characterization (Phase 06)                      [VERIFIED]
  -> tiny-object taxonomy (Phase 07, kub_size_clean_v3_v1) [VERIFIED]
  -> global baselines (Phases 08–09)                      [VERIFIED]
  -> four-model failure analysis (Phases 10–11)           [VERIFIED]
  -> oracle regional-resolution test (Phase 12)           [VERIFIED]
  -> GT-free localization feasibility (Phase 13)          [FUTURE_EXPERIMENT]
  -> REGIONAL_INTEGRATION_GATE_AFTER_PHASE13              [FUTURE_GATE]
  -> regional mechanism development (Phases 14–18)        [PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE]
  -> multi-domain global model (Phases 19–20)             [FUTURE]
  -> global MedFiLM (Phase 21)                            [FUTURE]
  -> regional-aware MedFiLM (Phases 22–26)                [FUTURE]
  -> RA-MedFiLM-Seg++ (final intended system)             [PROPOSED_NOT_IMPLEMENTED]
```

### Phase-11 → Phase-12 bridge conclusion — `OBSERVED_DIAGNOSTIC_EVIDENCE`

Verdict: **`MOTIVATES_ORACLE_ROI_TEST`** — **with the explicit qualification that there is
no claim that ROI solves the problem.** Boundary-error and FP-burden items are recorded
**`MIXED`**. Source: `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv`.

## 9. Phase 12 verified oracle evidence — `VERIFIED_EVIDENCE` (COMPLETE / PASS)

**PHASE 12 — ORACLE REGIONAL-RESOLUTION UPPER BOUND.** *Does increased effective local
resolution recover failures that global segmentation misses?* — **answered descriptively,
across all four architectures** (no single reference model).

- Population: **KUB FULL_FIELD VAL 103 cases / 152 native components** · margin 0.25 ·
  threshold 0.5 · per-component oracle crops · FLOAT map-back
- Primary comparison: **`GLOBAL_NATIVE` vs `ORACLE_FLOAT_GLOBAL_RETAINED`** (paired, same
  case / architecture / native space / GT / threshold)
- Comparators (never primary): `ORACLE_FLOAT_CROP_ONLY` (secondary historical geometry) ·
  `ORACLE_LEGACY_UINT8_CROP_ONLY` (`COMBINED_LEGACY_RESTORE_SENSITIVITY`)
- Global reproduction: `DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS`

| Model | GLOBAL Dice | PRIMARY Dice | delta |
|---|---|---|---|
| UNet | 0.594180 | 0.724722 | +0.130542 |
| Attention U-Net | 0.629805 | 0.699595 | +0.069790 |
| UNet++ | 0.640516 | 0.726679 | +0.086164 |
| DeepLabV3+ | 0.560251 | 0.750372 | +0.190121 |

- Native object recall rises to **0.9951–1.0000** for all four models
- **120 component×model recovery events** (pooled over 152 × 4 = 608 rows — **not** 120
  unique components) · **0 lost** component detections
- Size-stratified recovery events: **TINY 74 · SMALL 20 · MEDIUM 19 · LARGE 7**
- Empty-prediction recoveries: **27** case×model · **0 new** empty predictions
- Cross-architecture: **46/103** cases positive for all four models; **103/103** non-worse
  object recall

**Cost (preserved, not hidden):** **150/412** case×model rows worsen (max **−0.5866** Dice);
mean precision slightly decreases (−0.0004 … −0.0500); mean FP pixel burden rises
(+2197 … +4167); mean FN pixel burden falls strongly (−1225 … −2194).
**Target recovery benefit is accompanied by a real FP / precision cost.** Phase 12 is **not**
universally beneficial case-by-case.

**Supervisor conclusion:** `ORACLE_MECHANISM_VALUE = SUPPORTED_DESCRIPTIVE_EVIDENCE` ·
`PHASE13_PROGRESSION = SCIENTIFICALLY_JUSTIFIED`. This does **not** mean the gate is GO, the
regional mechanism is promoted, predicted localization will work, or statistical superiority
is established.

**Oracle limitation:** Phase 12 uses GT-derived target location ⇒ an **oracle upper-bound /
mechanism experiment**, **not deployable**; it does not prove Phase 13 can reproduce the gain.
The crop-only comparator additionally enjoys oracle background suppression.

## 10. Phase 13 purpose — `PARTS_1A_1A_R1_1A_R2_COMPLETE / PROTOCOL_SUPERVISOR_FROZEN_R2`

**PHASE 13 — GT-FREE REGION PROPOSAL / LOCALIZATION.**
**Status: PARTS 1A / 1A-R1 / 1A-R2 COMPLETE · PROTOCOL `SUPERVISOR_FROZEN_R2` · PART 1B
ELIGIBLE but NOT AUTHORIZED.** Phase 13 progression is `SCIENTIFICALLY_JUSTIFIED` by Phase 12.
Part 1A reconstructed the historical (`phase4_v2`) localizer protocol; Part 1A-R1 recorded the
supervisor decisions and froze the clean-v3 protocol; Part 1A-R2 corrected the primary
checkpoint-selection rule to the executing historical 4-term tuple. Current frozen artifact:
`reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json`. No training, no inference
and no proposal generation has been performed, and Part 1B may not start without supervisor
authorization.
Primary question: *can a deployable GT-free proposal mechanism preserve enough of the
Phase-12 oracle benefit while controlling FP burden and preserving global segmentation
quality?*

**Part-1A reconstruction (frozen, historical `phase4_v2`):** final localizer
`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1` · best epoch **73 / 88** ·
Tiny recall90 `53/73 = 0.726027` · overall `100/156 = 0.641026` · hard Tiny `7/16` ·
global-empty `3/7` · selected proposal config `0.10 / 0.20 / 5 / 0.30`. The Phase-14 frozen
entry gate was **NOT PASSED**. **Clean-v3 FULL_FIELD is TRAIN 770 / 1161 · VAL 103 / 152** —
the historical numbers belong to a different population (106 / 156) and must not be compared
with clean-v3 numbers as if the splits matched.

**R2 primary checkpoint-selection contract:** the **4-term executing historical tuple**
`(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)`, strict lexicographic,
ties = bad epoch, patience 15, evaluated at the fixed proposal configuration. Label
`EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION`. The R1 8-term tuple is
`SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION` and preserved as provenance.
`hard_tiny_recovered90`, `global_empty_images_covered90`, `multi_component_recall90` and
`mean_proposals_per_image` are `SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM` — computed and logged,
excluded from selection.

**Part-1A-R1 frozen clean-v3 protocol (unchanged by R2):** hard sets **re-derived** on clean-v3
(hard-Tiny **15** components `2f9828d7…` · global-empty **5** images `a0b332ca…`; historical v2
was 16 / 7 and the counts need not match), anchored on UNet++ as
`HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY`; proposal configuration frozen at
**`0.10 / 0.20 / 5 / 0.30`** with the per-epoch 20-config grid search **DISABLED**
(`DEFERRED_SECONDARY_SENSITIVITY_ONLY`); heatmap contract **512×512 → 128×128** with
`heatmap_resolution=128` always explicit and fail-loud shape assertions; predicted-proposal
training crops **removed** from Phase-13 scope; Phase-14 distribution-match requirement
`DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS`; downstream primary
`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` at margin **0.20** (the Phase-12 oracle used 0.25), so
the retention metric is `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION` and is **not** a pure
localization-error isolation study.

**Findings:** `HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH` (VERIFIED, deferred to
Phase 14), `LATENT_INFERENCE_HEATMAP_RESOLUTION_OMISSION` (VERIFIED_DEFECT, fix approved),
`STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT` (historical v2 provenance only),
`NON_BLOCKING_HISTORICAL_ARTIFACT_GAP` (`val_search_epoch079.csv`, not fabricated).
**Checkpoint-selection provenance:** the executing code
(`scripts/training/train_phase13b_localizer.py:164`) used a **4-term** tuple; R1 briefly froze an
8-term extension, and **R2 restored the executing 4-term tuple as primary** (executing source is
higher-authority evidence than prose, and the correction minimises v2→v3 drift).

- Proposal system should be architecture-agnostic where feasible, exposing a reusable
  interface: `image -> proposal representation -> box / heatmap / confidence / scale estimate`.
- Evaluate: proposal target coverage · small/tiny coverage · multi-component coverage ·
  FULL_FIELD localization · proposal count · proposal precision · downstream segmentation
  utility.
- Compare: **GLOBAL vs ORACLE REGION vs PREDICTED REGION**.
- Output feeds `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`.

## 11. REGIONAL_INTEGRATION_GATE_AFTER_PHASE13 — `FUTURE_GATE`

| Outcome | Meaning | Action |
|---|---|---|
| **GO** | Oracle helps **AND** predicted localization retains meaningful utility | Promote the regional mechanism toward RA-MedFiLM-Seg++ |
| **REVISE_LOCALIZER** | Oracle helps **BUT** predicted localization loses too much benefit | Do **not** abandon the hypothesis; redesign localizer work first |
| **NO_GO** | Even oracle provides insufficient meaningful benefit | Do **not** force regional complexity; proceed with global multi-domain MedFiLM and document the negative evidence |

> **Criteria MUST be prospectively frozen** before inspecting Phase-12/13 results.
> **No numerical thresholds are defined in this pack** ([RULES.md](RULES.md) §12).

### Gate state after Phase 12 — **NOT_DECIDED**

| Dim | Dimension | Status after Phase 12 |
|---|---|---|
| **A** | ORACLE_MECHANISM_VALUE | **SUPPORTED_DESCRIPTIVE_EVIDENCE** |
| **B** | PRACTICAL_LOCALIZATION_RETENTION | **NOT_EVALUABLE_UNTIL_PHASE13** |
| **C** | GLOBAL_PRESERVATION_FP_COST | **MIXED_DESCRIPTIVE_EVIDENCE** |
| **D** | GENERALITY | **SUPPORTED_WITH_HETEROGENEITY** |

**Final gate: NOT_DECIDED.** No GO / REVISE_LOCALIZER / NO_GO is issued. The regional
mechanism is **NOT promoted**. The gate is decided only after Phase 13.
State table: `reports/tables/regional_integration_gate_state_after_phase12.csv`.

## 12. RA-MedFiLM design — `IMPLEMENTED_IN_PART` (see §16 for the frozen contract)

> **Status update 2026-10-01.** The design below is **no longer merely proposed**: the
> global model and the regional refiner are **implemented, trained and frozen**
> (Phase-21 / Phase-25A), and the benefit-router feature contract is **frozen in v1.2**
> (§16). The router is **TRAINED / FROZEN in Phase25D (COMPLETE_CANONICAL)**; Phase25B and Phase25C are COMPLETE canonical.
> Phase25E scientific policy evaluation is **COMPLETE_FROZEN**. The bullets below retain the original design intent.

Intended capability set (SR-1): modality/input adaptation · shared/global segmentation
representation · task/domain FiLM conditioning · GT-free region proposal/localization ·
higher-effective-resolution regional processing · regional/refinement representation ·
scale/region-aware FiLM conditioning · adaptive global-regional fusion/routing · final
binary segmentation output.

Conceptual FiLM form `F' = gamma(c) * F + beta(c)` with candidate conditioning vector
`c = [domain_embedding, scale_embedding, proposal_confidence, global_context]`
(+ legitimate inference-available metadata only).

**Metadata governance.** Every metadata field used in multi-domain work **MUST** be
classified as `CONDITIONING_ALLOWED` (legitimately available at inference),
`REPORTING_ONLY` (reporting only), or `FORBIDDEN_AS_INPUT` (GT-only / annotation-derived).
Kidney/Bladder/Ureteric remain `REPORTING_ONLY` ([RULES.md](RULES.md) §13).

See [ARCHITECTURE.md](ARCHITECTURE.md) §9 for the current architecture and §16 below for
the frozen v1.2 router-feature contract.

### Adaptive-routing hypothesis — `HYPOTHESIS_UNDER_TEST`

If regional refinement genuinely helps mainly where objects are small/local, an adaptive
router should **naturally activate differently by domain and by case** — more regional
compute on FULL_FIELD/small-object cases, less on ROI/large-object cases. This is a
hypothesis to test, not a result. **Phase-22 evidence already shows regional benefit is
strongly heterogeneous, and always-on regional HURTS in aggregate.**

### Multi-domain preservation principle — `FUTURE_EXPERIMENT`

Adding FiLM/regional machinery **MUST NOT** degrade per-domain performance. Phase 27 is the
preservation audit; it is a required gate, not a formality.

## 13. FUTURE causal ablation plan — `FUTURE_ABLATION_PLAN`

No ablation result exists yet. The intended high-level causal structure:

| ID | Configuration | Isolates |
|---|---|---|
| **A** | Shared Global | parameter sharing baseline |
| **B** | Global + Domain FiLM | FiLM contribution |
| **C** | Global + Regional Mechanism | regional processing contribution |
| **D** | Global + Domain FiLM + Regional Mechanism | FiLM + regional interaction |
| **E** | Global + Domain FiLM + Region/Scale FiLM | regional FiLM contribution |
| **F** | Full adaptive RA-MedFiLM-Seg++ | adaptive routing/fusion |

Purpose: separate the contribution of **parameter sharing · FiLM · regional processing ·
regional FiLM · adaptive routing/fusion**. **No winner claims before formal evidence**
(Phase 28 + Phase 31).

## 14. Pending statistics

- **Not performed.** No paired testing, confidence intervals, effect sizes, or significance
  tests on clean-v3 results.
- Still NOT performed: Phase 29 three-seed reproducibility, Phase 31 statistical
  significance. Until then, all clean-v3 numbers are **single-seed descriptive VAL
  findings** — no ranking, no winner, no significance.

## 15. HISTORICAL_v2 caveat — `HISTORICAL_PROVENANCE`

| Model | v2 best epoch | v2 VAL Dice | v2 epochs |
|---|---|---|---|
| UNet | 47 | (see v2 artifacts) | 62 |
| Attention U-Net | 77 | 0.7530131340026855 | 92 |
| UNet++ | 77 | 0.7625221610069275 | 92 |
| DeepLabV3+ | 37 | 0.7487905025482178 | 52 |

v2 used `phase4_v2` with **different** KUB TRAIN/VAL membership and
`KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY`. Any clean-v3 vs v2 difference
**MUST NOT** be attributed solely to leakage remediation. The v2 statement "strongest
baseline is UNet++" is **historical** and is **not** a clean-v3 winner.

## 16. CURRENT EXACT IMPLEMENTATION DECISIONS — RA-MedFiLM-BARR (v1.2)

`status: FROZEN_SPECIFICATION` · `science_changed = false` · `method_changed = false`

### 16.1 Phase-24 router-feature specification, v1.2

The router consumes a **GT-free, pre-refinement** feature vector. v1.1 declared the
dimension (`202`) but left the *operation* undefined. v1.2 completes it.

**C→32 deterministic adaptive channel averaging.** Each native tap map is pooled
spatially (global mean, or ROI mean over the mapped cells) to `v ∈ R^C`, then reduced by
the frozen, non-trainable operator
`DETERMINISTIC_CHANNEL_ADAPTIVE_AVG_POOL_1D_V1`:

```
for j in 0..31:
    start_j = floor(j * C / 32)
    end_j   = ceil((j + 1) * C / 32)
    z[j]    = mean(v[start_j:end_j])
```

No trainable projection is introduced (`trainable_conv_projection_before_pooling = false`).
When `C < 32` the floor/ceil bins **overlap**; starts are monotone non-decreasing and the
bins cover `[0, C)`, using every source channel.

**Six-vector order (frozen):**
`bridge_global, bridge_roi, decoder2_global, decoder2_roi, decoder1_global, decoder1_roi`.

**Native feature widths:** bridge `= 256`, decoder2 `= 48`, decoder1 `= 24`.

**ROI→feature-map mapping (freeze).** Canvas `H = W = 512`; half-open `[x0, x1)`. For a
tap whose feature grid is `Wf × Hf`:

```
fx0 = floor(x0 * Wf / 512)   fy0 = floor(y0 * Hf / 512)
fx1 = ceil (x1 * Wf / 512)   fy1 = ceil (y1 * Hf / 512)
```

clipped to the grid; computed **per tap** (bridge 32×32, decoder2 256×256, decoder1 512×512).
Empty ROI ⇒ all-zero group.

**The ten scalar descriptors** (order frozen):
`entropy_proxy_mean` (THRESHOLD_FREE),
`frac_prob_within_0p05_of_boundary`, `frac_prob_within_0p02_of_boundary`,
`mean_boundary_margin` (all `t_seg = 0.50`),
`pred_foreground_fraction`, `pred_foreground_pixels`, `pred_roi_exists`, `pred_empty`,
`predicted_roi_area_fraction`, `predicted_roi_side` (all `t_roi = 0.30`).

**Threshold semantics — two DIFFERENT thresholds:**
`t_roi = 0.30` (ROI proposal → bbox / `action_available`; not Dice) and
`t_seg = 0.50` (segmentation output → final mask / Dice / IoU).

**Corrected `predicted_roi_area_fraction` (D1 ruling / C3).**
`w_in = max(0, min(512, x2) − max(0, x1))`, `h_in = max(0, min(512, y2) − max(0, y1))`,
`predicted_roi_area_fraction = w_in * h_in / 512²`, `float32`, range `[0, 1]`.
External padding is excluded. The old provisional `crop_side_pixels² / 512²`
(range up to `2.25`) is marked
`SUPERSEDED_PRE_EXECUTION_SPEC_FORMULA__NOT_USED_FOR_PHASE25B`.
`predicted_roi_side` retains the pre-resize square crop side separately.

**Dimensions.** 192 deep + 10 scalar = **202** numeric pre-router dims; **+16** learned
task embedding (added at Phase25D) = **218** router input.

### 16.2 BARRBenefitRouterV1 — exact architecture (TRAINED / FROZEN in Phase25D)

`Embedding(4, 16)` → 218 input → `Linear(218,128)` → `LayerNorm(128)[affine=true]` →
`SiLU` → `Dropout(0.10)` → `Linear(128,64)` → `LayerNorm(64)[affine=true]` → `SiLU` →
`Dropout(0.10)` → `Linear(64,1)`. No optional harm head in the primary router.

**Total trainable parameters = 36,801.** Breakdown: task embedding `64` +
`Linear(218,128)` `27,904 + 128` + `LayerNorm(128)` `256` + `Linear(128,64)`
`8,192 + 64` + `LayerNorm(64)` `128` + `Linear(64,1)` `64 + 1`.

The historical figure **36,353 = the linear-core-only count** (`Linear(218,128)` +
`Linear(128,64)` + `Linear(64,1)`, excluding the 64 embedding and 384 affine LayerNorm
parameters). It is **not** the total trainable count. This is a **bookkeeping correction
(D2)**; the architecture is unchanged and no model has been trained.

**Router target:** OOF paired `DeltaDice` refinement gain. **Resource utility** is a
separate, explicitly-computed consideration. **Preservation / fallback role:** the global
path remains the safety net when the router says skip.

### 16.3 DESIGN DECISION HISTORY

| Revision | Decision |
|---|---|
| **v1.1** | Router feature specification **underspecified** (dimension declared, operation undefined) |
| **v1.2** | Feature semantics **completed before extraction** (RF-1 C→32 reduction; RF-2 ROI→grid mapping; RF-3 scalar + threshold roles) |
| **D1** | `predicted_roi_area_fraction` **area-fraction correction** (clipped in-canvas, `[0,1]`) |
| **D2** | Router **parameter bookkeeping correction** (36,353 = linear core; 36,801 = total trainable) |

**No result-driven tuning occurred.** No holdout outcome was inspected. `TFREE`
normalisation only touched presentation bytes.

### 16.4 BARRBenefitRouterV1 — router training specification v1.2.1 (FROZEN)

Additive specification revision `ra_medfilm_barr_router_training_v1_2_1`, frozen
**before** any router construction or training.

| Field | Frozen value |
|---|---|
| Outer CV | `BARR_ROUTER_CV5_GROUP_SAFE_DOMAIN_STRATIFIED_V1` — 5 folds, `StratifiedGroupKFold(shuffle=True, random_state=42)`, group = canonical composite `group_key`, stratify = domain only |
| Inner split | `StratifiedGroupKFold(n_splits=10, random_state=4200+k)` per outer fold; index 0 = EARLY_STOP, 1–9 = FIT |
| Checkpoint selection | lowest **EARLY_STOP mean Huber loss**; direction MINIMIZE; tie = earlier epoch wins; patience 20 |
| Target | raw `delta_dice` (float32); **no scaling, no centering, no clipping** |
| Feature normalization | 8 continuous scalars standardized (population std, ddof=0) on FIT only; 192 deep + 16 embedding untouched; constant columns → 0.0 |
| Final epoch rule | exact median of 5 best epochs: `sorted([e0,e1,e2,e3,e4])[2]` |
| Final refit seed | 42, **fresh initialization** (not from any CV checkpoint) |
| Final refit scheduler | `ReduceLROnPlateau` monitors **train Huber loss per epoch**; LR only; no validation; no early stopping; checkpoint = last fixed epoch |
| Data-loader seed | fold seed = `42000 + router_cv_fold`; resume restores all RNG states |
| OOF prediction | load best checkpoint; eval mode; predict ONCE on OUTER_TARGET_k; never modifies model/scheduler |

All other hyperparameters carried forward unchanged from Phase-24 v1.2
(§16.2 architecture, Huber δ=0.05, AdamW lr=1e-3 wd=1e-4, batch=128, max_epochs=200,
scheduler `ReduceLROnPlateau(factor=0.5, patience=8, min_lr=1e-6)`).

Blocked attempt preserved:
`reports/audits/phase25d_blocked_spec_incomplete.json`.

---

**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULES.md](RULES.md) · [TASKS.md](TASKS.md) · [MEMORY.md](MEMORY.md)

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
## Canonical 00-43 Roadmap + Governance Synchronization — DESIGN.md (2026-10-04)

**Revision ID:** `RA_MEDFILM_BARR_ROADMAP_EXTENSION_V1_0__00_TO_43` — **DOCUMENTATION/GOVERNANCE ONLY** (`science_changed = false`, `model_weights_changed = false`, `scientific_execution_started = false`).

This block is **additive**. The original **00-40 / 41-phase scientific roadmap is PRESERVED verbatim** above (allocation unchanged, no phase renumbered, no historical result rewritten). It records: the current state **through Phase35 v1.0f**, the **Phase36-40** roadmap, the supervisor-adopted **Phase41-43** deployment extension (Stage E), and the canonical **00-43 (44-phase)** roadmap.

**CURRENT STATE (through Phase35 v1.0f).** Phases **00-27, 31, 32, 33, 34** are
**COMPLETE_CANONICAL** (Phases 06-15 historical v2 with clean-v3 revalidation status preserved as
provenance). **Phase 30** = `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` (qualifier
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`)
— this qualifier is **retained verbatim** and must not be upgraded. **Phase 35** scientific
execution is **NOT_STARTED**; the pre-execution source chain is frozen at **v1.0f**. **Phase 28/29**
are **NOT_STARTED** / **SPEC_FROZEN_ELIGIBLE_NOT_STARTED**. **Phases 36-40** are **NOT_STARTED**.
**Phase 41-43 (Stage E)** are **NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION**. **TEST remains
locked until Phase 39** (`test_reads = 0`); **ROUTER_HOLDOUT** = `OPENED_AND_FROZEN` (Phase30
one-shot consumed); **VAL808** = frozen development benchmark (consumed by Phase27, do not re-open
for tuning).

### FUTURE_EXPERIMENT — Phase 36 (Robustness & Image Perturbation Analysis)

- **Status:** `FUTURE_EXPERIMENT` (not run).
- **Design intent:** quantify degradation under controlled, pre-registered perturbations to the 512 single-channel input (illumination/contrast, blur, noise, compression, occlusion) plus region/proposal perturbation of the ROI pathway. Report per-domain and macro-domain Dice deltas with paired CIs; preservation criterion per frozen policy.
- **Guards:** no threshold tuning from perturbation outcomes; TEST untouched; ROUTER_HOLDOUT not re-opened; report as descriptive unless pre-registered.

### FUTURE_EXPERIMENT — Phase 37 (Comprehensive Visual & Tabular Evidence Consolidation)

- **Status:** `FUTURE_EXPERIMENT` (not run).
- **Design intent:** consolidate the visual (figure galleries, attribution maps) and tabular evidence produced across Phases 19-36 into a single evidence index with provenance binding.
- **Guards:** no new scientific computation; consolidation is display/audit only.

### FUTURE_EXPERIMENT — Phases 38-40 (Freeze → single-pass TEST → publication)

- **Phase 38:** `Manuscript Protocol & Checkpoint Freeze` — freeze all protocols, thresholds, and checkpoints before TEST.
- **Phase 39:** `Final Untouched Test Cohort Evaluation` — the **only** TEST phase; exactly one evaluation; no tuning afterwards.
- **Phase 40:** `Publication Package & Reproducibility Audit`.

### Phase35 v1.0f — Grad-CAM / attribution design note

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

This block is **additive**. Everything above is **PRESERVED verbatim**. It repairs two defects:

- **D2** (`V1_0_CROSS_DOCUMENT_STAGE_E_TITLE_CHECK_FALSE_POSITIVE`): the exact Stage E phase titles were present only in [PRD.md](PRD.md), [TASKS.md](TASKS.md) and `PROJECT_MASTER_PLAN.md`; this document restates them verbatim so the title check becomes a true exact-substring check.
- **D3** (`V1_0_DESIGN_STAGE_E_PROSPECTIVE_EXPERIMENT_CONTENT_INCOMPLETE`): the v1.0 Stage E record existed only as a topology sketch. DESIGN is the designated home for prospective experiment design, so this document now carries explicit prospective `FUTURE_EXPERIMENT` sections for Phases 41/42/43, structurally parallel to the Phase36/37/38-40 sections above.

**Exact Stage E phase titles (canonical, authoritative spelling):**

| Phase | Exact canonical title | Status |
|---|---|---|
| 41 | **Deployment Engineering & Model Packaging** | NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION |
| 42 | **End-to-End Deployment Validation** | NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION |
| 43 | **Research Deployment Release, Monitoring & Maintenance** | NOT_STARTED / NOT_AUTHORIZED_FOR_EXECUTION |

### FUTURE_EXPERIMENT — Phase 41 (Deployment Engineering & Model Packaging)

- **Status:** `FUTURE_EXPERIMENT` (not run; not authorized).
- **Design intent:** convert the frozen research bundle (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/`) into a packaged, versioned, deployable artifact. Serialize/export the four frozen components (G `286689fd…`, R_psi `6d28608a…`, B_phi `8a412b2f…`, S_omega `eee9b97b…`); freeze the deterministic 512 single-channel preprocessing (aspect-preserving resize + centre/symmetric pad; image BILINEAR, mask NEAREST); define a versioned configuration schema that pins thresholds and the router input contract.
- **Design acceptance criteria (prospective):** packaged weights byte-bound to the frozen checkpoint SHAs with an expected-vs-observed audit; exported-model inference semantics identical to the in-repo research path on a frozen control batch; configuration schema complete and fail-loud on missing/placeholder fields.
- **Guards:** no retraining / fine-tuning / recalibration; TEST untouched (Phase39-only); ROUTER_HOLDOUT not re-opened; VAL808 not re-opened for tuning. `NOT_AUTHORIZED_FOR_EXECUTION`.

### FUTURE_EXPERIMENT — Phase 42 (End-to-End Deployment Validation)

- **Status:** `FUTURE_EXPERIMENT` (not run; not authorized).
- **Design intent:** validate that a bundled inference harness reproduces the frozen research inference path **exactly**, and characterize deployment cost on target hardware. Confirm bit-exact output parity between the packaged harness and the frozen research path on frozen DEV inputs; profile latency, throughput and memory.
- **Design acceptance criteria (prospective):** bit-exact parity on the frozen control population (no tolerance drift); the ROI-vs-segmentation threshold distinction preserved (0.30 ≠ 0.50); router input verified pre-refinement and GT-free at 218 dims.
- **Evidence-class discipline:** any deployment latency/throughput/memory numbers are **measured deployment numbers** and must be reported separately from the Phase34 **ANALYTICAL MAC LOWER BOUND**; never merged, never presented as a new scientific result.
- **Guards:** no threshold tuning from deployment outcomes; no model change; TEST untouched; ROUTER_HOLDOUT not re-opened. `NOT_AUTHORIZED_FOR_EXECUTION`.

### FUTURE_EXPERIMENT — Phase 43 (Research Deployment Release, Monitoring & Maintenance)

- **Status:** `FUTURE_EXPERIMENT` (not run; not authorized).
- **Design intent:** issue a semantic version for the packaged system, register it in a versioned artifact registry, and define monitoring/drift-regression hooks plus a maintenance and rollback protocol.
- **Design acceptance criteria (prospective):** immutable, write-once versioned release artifact; a monitoring specification covering input-distribution drift and output-regression triggers; an explicit rollback procedure to a prior frozen version; a maintenance protocol that forbids silent provenance migration.
- **Guards:** all release artifacts write-once and versioned; no frozen research artifact overwritten; a failed or blocked release phase returns `CHECK_REQUIRED` with a preserved failure record (never a fake completion). `NOT_AUTHORIZED_FOR_EXECUTION`.

**Design constraints binding on all Stage E work.** The packaging must reproduce the **frozen** inference semantics exactly (ROI proposal threshold 0.30 ≠ segmentation output threshold 0.50; router input = pre-refinement, GT-free, 218 dims). TEST remains Phase39-only. Deployment must not silently retrain, recalibrate thresholds, or alter the router input contract. Stage E remains **NOT_AUTHORIZED_FOR_EXECUTION**.

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
## Post-Freeze Research Extension — Post-Freeze Study Design (2026-10-11)

**Revision ID:** `RA_MEDFILM_BARR_POST_FREEZE_EXTENSION_V1_0` — **DOCUMENTATION/PLANNING ONLY** (`science_changed = false`, `model_weights_changed = false`, `scientific_execution_started = false`, `scientific_delta = 0`).

**This block is additive.** Everything above is **PRESERVED verbatim**. The frozen **RA-MedFiLM-BARR V1** study (Phases 0–40 + manuscript release; final scope `MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY`; TEST evidence class `POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES`; Phase30 qualifier `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` retained verbatim) is **immutable historical evidence** and is never rewritten. A clearly separated **POST-FREEZE RESEARCH EXTENSION** begins here. All new work is `PLANNED` / `NOT_STARTED` / `ELIGIBILITY_PENDING`.

### Data classes (never conflated)

| Class | Meaning |
|---|---|
| DEVELOPMENT DATA | TRAIN / development-validation (TRAIN, VAL808, ROUTER_DEVELOPMENT) — usable for V2 development |
| INTERNAL EVALUATION | frozen internal evaluation populations (ROUTER_HOLDOUT, TEST) |
| EXTERNAL EVALUATION | the four external datasets, evaluated once per frozen model |
| PRIOR-USED EXTERNAL DATA | external datasets previously used by the older MedFiLM-Seg programme (HAM10000, CVC-ClinicDB, BrEaST-Lesions_USG) |
| NEW-STATUS EXTERNAL DATA | external datasets with no prior use identified (Stones_where_are_you) — `ELIGIBILITY_PENDING` |

### Study designs (all PLANNED)

1. **External dataset eligibility** (EXT-01/02): audit → freeze populations, inclusion/exclusion, task mapping, preprocessing, thresholds, checkpoints, metrics (Dice primary; IoU, Precision, Recall, HD95 secondary), aggregation, bootstrap/CI plan, failure rules, empty-mask/HD95 conventions.
2. **Baseline benchmarking** (EXT-03): same-protocol baselines (U-Net, Attention U-Net, UNet++, DeepLabV3+, optional hybrid).
3. **Progression study** (EXT-04): P1→P4 with Dice/IoU/Precision/Recall/HD95, Global→Final DeltaDice, execute/accept/reject/FORCED_SKIP rates, MAC estimate.
4. **Leave-one-domain-out** (EXT-05): four 3-domain settings.
5. **External validation** (EXT-06): per domain n/Dice/IoU/Precision/Recall/HD95 + router rates; GlobalMedFiLM vs RA-MedFiLM-BARR.
6. **Precision/recall + error analysis** (EXT-08/09): FP-dominant vs FN-dominant; errors stratified by PRESET factors only.
7. **Model-improvement separation**: any V2 change lives in a separate branch and is never adopted solely because it improves TEST/external numbers.

### Freeze-before-inference rule

No external outcome may be inspected before the EXT-02 protocol freeze. The segmentation threshold is frozen beforehand. Subgroup definitions are frozen before results.

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
