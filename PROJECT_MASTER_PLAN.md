# PROJECT MASTER PLAN - RA-MedFiLM-Seg++

## 1. Project Goal
Develop a rigorous, publication-quality medical image segmentation framework (RA-MedFiLM-Seg++) suitable for a top-tier Q1/A* paper.
The core hypothesis is that regional scale-aware refinement (GT-free regional proposal + crop/zoom) improves recovery of small/tiny targets often missed by global full-field segmentation, while preserving performance on larger targets and other domains.

## 2. Domains & Task Definition
- **Domains (Task IDs):** ISIC 2018 (0), BUSI (1), Kvasir-SEG (2), KUB-Stone (3).
- **Task Definition (KUB):** Binary semantic segmentation (Foreground = stone, Background = everything else). Kidney, Bladder, and Ureteric are subgroup metadata, not semantic classes.
- **Routing:** Initial experiments use true task IDs. Automatic domain routing is a separate future module and must not contaminate the core segmentation study.

## 3. Major Paths
- **Project Root:** `D:\Softfors\jup`
- **Internal Raw Data:** `D:\Softfors\omni_seg\data_raw`
- **External Test Data:** `D:\Softfors\final\external_test_ds`
- **Frozen Experiment A (Reference):** `D:\Softfors\final\medfilm_seg_kub_extension` (MUST NEVER BE MODIFIED)
- **Compact Context:** `PROJECT_CONTEXT.md`
- **Agent Operating Contract:** `ANTIGRAVITY_WORKFLOW.md`
- **Project Interpreter:** `D:\Softfors\jup\.venv\Scripts\python.exe`

## 4. Scientific Governance & Scientific Change Control
- **Authorization:** Only the researcher and supervising ChatGPT can authorize phase advancement or changes to protocols (loss, architecture, metrics, seeds, datasets).
- **Agent Role:** Antigravity is the implementation, execution, software engineering, monitoring, audit, and reproducibility agent. It does NOT make final scientific decisions.
- **Change Control:** Agents MAY fix mechanical/path/logging bugs, but MUST STOP and request `CHECK_REQUIRED` before changing scientific methodology (architecture, learning rate, thresholds, augmentations, etc.).

## 5. Test Lock & External Lock
- **Development uses TRAIN and VAL only.**
- **TEST is strictly locked (0 content reads, NONE metrics) until Phase 39.**
- External data is locked from tuning.
- TEST and external data must NEVER be used for hyperparameter, architecture, threshold, or checkpoint selection.

## 6. Dataset / Split Summary

### Active development split — `phase4_v3` (CANONICAL_ACTIVE_DEVELOPMENT)
- **Total Images:** 8441 (ISIC: 3694, BUSI: 927, Kvasir: 1000, KUB: 2820) — provenance conserved.
- **Global Split:** TRAIN = 5832, VAL = 808, TEST = 1683 (LOCKED), QUARANTINED = 118.
- **Promoted:** Phase-05 Part 1E (leakage-safe remediation), byte-for-byte from the audited candidate.
- **Leakage status:** REMEDIATED.

### Historical split — `phase4_v2` (HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT)
- **Global Split:** TRAIN = 5913, VAL = 845, TEST = 1683 (LOCKED).
- **Leakage status:** KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY.
- Required to reproduce historical Phases 06–15. DO NOT modify or delete.
- **KUB Component Taxonomy:** Original-space connected components define authoritative count (1162 in TRAIN) and size quartiles (`kub_size_v1`).

> All future scientific development uses `phase4_v3`. Historical Phases 06–15 remain
> `phase4_v2` provenance, not clean-v3 evidence. See `manifests/manifest_registry.json`.

---

## Stage-B activation and regional-branch deferral

**Post-H3 supervisor governance transition.** The post-Phase14 / H3 target-support branch is
**CLOSED** with the frozen scientific label **`H3_SUPPLY_REDESIGN_INSUFFICIENT`**. The regional
mechanism is **DEFERRED / NOT PROMOTED** (preserved as diagnostically supported by the Oracle
but not deployably resolved — neither erased nor successfully integrated).

- **Option B / Option C:** `DEFERRED__NOT_AUTHORIZED`
- **Phases 15-18:** `DEFERRED_CONDITIONAL__NOT_EXECUTED` (roadmap numbering unchanged)
- **Stage B:** ACTIVE — the main multi-domain program begins at **Phase 19**
- **Phase 19:** COMPLETE (dataset harmonization; **not** a training phase)
- **Phase 20 / 20A:** COMPLETE (shared four-domain global UNet++ baseline)
- **Phase 20B:** COMPLETE (five-model conventional baseline benchmark; reviewer package frozen)
- **Phase 21:** `ELIGIBLE_NOT_STARTED` (fresh supervisor authorization required)
- **TEST / external TEST:** `CLOSED` (Phase-19 TEST reads = 0)

Authorization artifact: `reports/audits/stage_b_phase19_authorization.json`.

---

## Stage-B Phase-20 completion (shared four-domain global baseline)

**Phase 20 COMPLETE.** ONE conventional shared four-domain baseline under the frozen
Phase-19 harmonized protocol — **no FiLM, no task conditioning, no regional module,
no localizer, no ROI/proposal**.

- Experiment: `phase20_shared_unetpp_fourdomain_seed42_clean_v3`
- Single frozen **UNet++**, 9,159,681 params, one shared parameter set, one head
- **Macro-domain VAL Dice 0.792007** at best epoch 55; early stopped at epoch 70
- Canonical VAL evaluation: 808 samples, exactly one inference run
- TEST reads: **0** (image / mask / inference / visualization)
- **Phase 21: ELIGIBLE but NOT STARTED** (authorization required)
- Terminal state: **`PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**

---

## Stage-B Phase-20B completion (five-model conventional baseline benchmark)

**Phase 20B COMPLETE.** Four additional conventional architectures trained strictly sequentially
under the **same** frozen protocol as the Phase-20A UNet++ reference, giving a five-model benchmark.

- Models: `unet`, `attention_unet`, `unetpp` (20A reference), `deeplabv3plus`, `transformer_mit_unet`
- Five-model macro-domain VAL Dice: DeepLabV3+ **0.827652** > Transformer/MiT **0.822383** >
  UNet++ **0.792010** > Attention U-Net **0.789037** > U-Net **0.787832**
- Two tiers separated (p ≈ 0.000); **top-two ordering NOT significant** (Δ ≈ +0.005270, CI crosses
  zero, p ≈ 0.282) — DeepLabV3+ is the highest *observed* model but **not** a separated winner
- 808 VAL cases per model, exactly one canonical inference run each; **4040** persisted NPZ
- Reviewer package: **153 figures** (114 embedded), **51/51 evaluation matrices visualized (100 %)**
- Notebook determinism: **3 consecutive builds → identical SHA-256**
  (`77dc0aa84259ff7438253206c03f60fad5423b5ce41c3c3b00b029217ddd55b7`)
- TEST reads: **0** (image / mask / inference / visualization)
- Terminal state: **`PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**
- Documentation state: **`PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED`**

---

## 7. Canonical 41-Phase Master Progression (Phase 00 through Phase 40)

> **Clean-v3 refresh is now required.** Phases 06–15 executed historically under `phase4_v2`
> and are marked `COMPLETE (v2 evidence)`. Their clean-v3 revalidation status is
> `REVALIDATION_REQUIRED` / `RERUN_REQUIRED` (see `reports/tables/phase05_clean_rerun_scope.csv`).

### Stage A: KUB Radiograph Regional & Tiny-Object Development (Phases 00–18)
- **Phase 00:** Governance & Protocols (COMPLETE)
- **Phase 01:** Project Initialization & Layout (COMPLETE)
- **Phase 02:** Environment & CUDA Verification (COMPLETE)
- **Phase 03:** Dataset Discovery & Cataloging (COMPLETE)
- **Phase 04:** Manifest & Data Splits (COMPLETE — v2 historical)
- **Phase 05:** Forensic Leakage Audit + v3 Promotion (COMPLETE — scientific gate PASS)
- **Phase 06:** Descriptive Dataset Analysis / KUB Characterization (PART 1A-R1 COMPLETE — clean-v3, gate PASS; remaining parts pending)
- **Phase 07:** Object Size Taxonomy & Quartiles (COMPLETE — `kub_size_clean_v3_v1` FROZEN; historical `kub_size_v1` immutable; VAL characterized post-freeze)
- **Phase 08:** Baseline Infrastructure & Factories (COMPLETE — Part 1A clean-v3 foundation + Part 1B trainer/resume contract & Phase-09 protocol reconstruction; no training)
- **Phase 09:** KUB UNet Baseline Training (historical v2 COMPLETE; clean-v3 candidate config `RECONSTRUCTED_AND_READY`, NOT started)
- **Phase 09:** Global Baseline Training (U-Net) (COMPLETE v2 / CLEAN-V3 REVALIDATION REQUIRED)
- **Phase 10:** Baseline Comparison (UNet vs UNet++ vs SegNet) (COMPLETE v2 / CLEAN-V3 REVALIDATION REQUIRED)
- **Phase 11:** Baseline Failure Analysis (COMPLETE v2 / CLEAN-V3 REVALIDATION REQUIRED)
- **Phase 12:** Oracle ROI Upper Bound Analysis (COMPLETE v2 / CLEAN-V3 REVALIDATION REQUIRED)
- **Phase 13:** Predicted ROI Proposal Localization (Stage 4D) (COMPLETE v2 / CLEAN-V3 REVALIDATION REQUIRED)
- **Phase 14:** Regional Refiner Diagnostic Evaluation (COMPLETE v2 / FROZEN DIAGNOSTIC / CLEAN-V3 REVALIDATION REQUIRED)
- **Phase 15:** Regional Refiner Segmentation Loss Study (DEFERRED_CONDITIONAL__NOT_EXECUTED — protocol frozen; deferred after H3 insufficiency)
- **Phase 16:** Regional-Global Mask Fusion (DEFERRED_CONDITIONAL__NOT_EXECUTED)
- **Phase 17:** KUB Regional Pipeline Comprehensive Ablation (DEFERRED_CONDITIONAL__NOT_EXECUTED)
- **Phase 18:** KUB Final Development Validation Benchmark (DEFERRED_CONDITIONAL__NOT_EXECUTED)

### Stage B: Multi-Domain Harmonization & RA-MedFiLM Architecture (Phases 19–26)
- **Phase 19:** Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) (**COMPLETE**)
- **Phase 20:** Shared Four-Domain Global Baseline — single frozen UNet++ (**COMPLETE**; macro-domain VAL Dice 0.792007)
- **Phase 20B:** Five-Model Conventional Baseline Benchmark — U-Net · Attention U-Net · UNet++ · DeepLabV3+ · Transformer/MiT (**COMPLETE**; top observed DeepLabV3+ 0.827652, top-two ordering not significant)
- **Phase 21:** Global MedFiLM Reference Architecture (**ELIGIBLE / NOT STARTED** — authorization required)
- **Phase 22:** Multi-Domain Scale & Transfer Gap Analysis (NOT_STARTED)
- **Phase 23:** Literature & Methodological Novelty Positioning (NOT_STARTED)
- **Phase 24:** RA-MedFiLM Architectural Specification (NOT_STARTED)
- **Phase 25:** RA-MedFiLM Controlled Module Development (NOT_STARTED)
- **Phase 26:** Full Four-Domain Joint Architecture Training (NOT_STARTED)

### Stage C: Multi-Domain Rigor, Ablation, Reproducibility & Clinical Evidence (Phases 27–37)
- **Phase 27:** Multi-Domain Performance Preservation Audit (SPEC_COMPLETE_FROZEN / EXECUTION_ELIGIBLE_NOT_STARTED)
- **Phase 28:** Comprehensive System Ablation Matrix (NOT_STARTED)
- **Phase 29:** Three-Seed Deterministic Reproducibility Study (NOT_STARTED)
- **Phase 30:** Final Development Validation Benchmark (NOT_STARTED)
- **Phase 31:** Statistical Significance & Hypothesis Testing (NOT_STARTED)
- **Phase 32:** External Dataset & Domain Shift Evaluation (NOT_STARTED)
- **Phase 33:** Final System Failure & Boundary Error Analysis (NOT_STARTED)
- **Phase 34:** Computational Efficiency & Runtime Profiling (NOT_STARTED)
- **Phase 35:** Feature Attribution & Visual Interpretability (NOT_STARTED)
- **Phase 36:** Robustness & Image Perturbation Analysis (NOT_STARTED)
- **Phase 37:** Comprehensive Visual & Tabular Evidence Consolidation (NOT_STARTED)

### Stage D: Protocol Freeze, Single-Pass Untouched Test Benchmark & Publication Package (Phases 38–40)
- **Phase 38:** Manuscript Protocol & Checkpoint Freeze (NOT_STARTED)
- **Phase 39:** Final Untouched Test Cohort Evaluation (NOT_STARTED)
- **Phase 40:** Publication Package & Reproducibility Audit (NOT_STARTED)

---

## 8. Experiment Provenance Rules
- **Unique IDs:** Every run needs a unique ID. Never reuse a contaminated directory or mix old state with new configs.
- **Valid/Invalid:** Tag failed runs as `INVALID_FOR_FINAL_SELECTION`, `DIAGNOSTIC_ONLY`, or `ABORTED`. Do not delete scientific evidence.
- **Single Process:** Exactly ONE training process per ID using `.venv/Scripts/python.exe`.
- **Power Resume:** On interruption, carefully compare `latest.pt` with `history.csv` before resuming. If inconsistent, STOP.
- **Checkpoints:** Maintain `best.pt` and `latest.pt`. Use atomic writes.

## 9. Notebook Policy
- Notebooks are scientific artifacts for DISPLAY / ANALYSIS / AUDIT, not training.
- They must run top-to-bottom safely (Run All), not touch TEST, and report reproducible SHA-256 hashes.
- Standard qualitative coverage: $\ge 12$ sample cases per dataset, $\ge 16$ prediction panels per model.

## 10. Statistics Policy
- Claim significance ONLY if actually tested using paired testing, confidence intervals, and effect sizes.
- NO superiority claims from a single seed.

## 11. Final Test Policy
- Evaluation on the TEST split occurs ONLY in Phase 39 after all protocols, thresholds, and architectures are frozen (Phase 38).
- No tuning is permitted after accessing TEST.

<!-- BEGIN PROJECT-EVALUATION-METRICS-AUDIT -->
## Project-Wide Evaluation-Metrics Audit (audit record)

A project-wide evaluation-metrics audit, standardization and descriptive
backfill was completed across the finished KUB research line. It produced a
reusable metric module (`src/metrics/evaluation_metrics.py`), a metric registry
(`reports/audits/project_metric_registry.json`), a project metric inventory, and
a single logged deterministic VAL-only replay that backfilled previously
unpersisted pixel / boundary / calibration / uncertainty metrics.

All new metrics are labelled `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`
and are **not** promoted into any frozen gate. The H3 formal adjudication remains
pending; Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED.

See `notebooks/evaluation/project_evaluation_metrics_audit.ipynb`.
<!-- END PROJECT-EVALUATION-METRICS-AUDIT -->

## Phase 21 — Global MedFiLM Reference (COMPLETE)

| Item | Value |
|---|---|
| Status | COMPLETE |
| Experiment | `phase21_global_medfilm_fourdomain_seed42_clean_v3` |
| Architecture | `global_medfilm_shared_residual_unet_film5_no_se_no_deep_supervision_v1` |
| Parameters | 3,523,001 |
| Best epoch | 66 |
| Macro-domain VAL Dice | 0.835079 [0.787749, 0.878006] |
| Stop reason | EARLY_STOPPING_PATIENCE |
| Protocol | inherited exactly from the frozen Phase-20 protocol (`b74f1f9f...`), 0 unintentional differences |
| Canonical VAL inference runs | 1 (808 samples) |
| TEST reads | 0 (image / mask / inference / visualization) |
| Phase 22 | ELIGIBLE_NOT_STARTED |

Terminal state: `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED`

Phase 20A (shared UNet++ global baseline) and Phase 20B (five-model conventional benchmark) are both COMPLETE and frozen.

## Phase 22 — Multi-Domain Scale / Regional-Benefit / Resource Gap (COMPLETE)

| Item | Value |
|---|---|
| Status | COMPLETE |
| Type | diagnostic gap analysis (inference-only, no training) |
| Reference | frozen Phase-21 Global MedFiLM (3,523,001 params, unchanged) |
| Protocol | `reports/audits/phase22_diagnostic_protocol.json` (frozen) |
| Scales probed | 256 / 512 / 768 / 1024 (native-space scoring) |
| Regional arms | ORACLE (upper bound) + PREDICTION-DERIVED (deployable shape) |
| Benefit predictor | NOT trained (label contracted only) |
| Router | NOT trained (fixed rules evaluated offline) |
| Terminal state | `PHASE22_MULTIDOMAIN_SCALE_REGIONAL_RESOURCE_GAP_ANALYSIS_COMPLETE__PHASE23_ELIGIBLE_NOT_STARTED` |

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

<!-- ROADMAP_EXTENSION_V1_0__00_TO_43 -->
## Canonical 00-43 Roadmap + Governance Synchronization — PROJECT_MASTER_PLAN.md (2026-10-04)

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

### Preserved original scientific roadmap (00-40)

§7 above, *Canonical 41-Phase Master Progression (Phase 00 through Phase 40)*, is the **original, preserved** roadmap. Its allocation (Stage A 00-18, Stage B 19-26, Stage C 27-37, Stage D 38-40) is unchanged. Stage E (below) is an **additive deployment extension**, not a renumbering.

### Canonical 00-43 (44-phase) roadmap

### Stage C — Multi-Domain Rigor, Ablation, Reproducibility & Evidence (27-37)

| Phase | Title | Status |
|---|---|---|
| 27 | Multi-Domain Performance Preservation Audit | **COMPLETE_CANONICAL** |
| 28 | Comprehensive System Ablation Matrix | NOT_STARTED |
| 29 | Three-Seed Deterministic Reproducibility Study | SPEC v1.1 COMPLETE_FROZEN; EXECUTION_ELIGIBLE_NOT_STARTED |
| 30 | Final Development Validation Benchmark (ROUTER_HOLDOUT one-shot) | **COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL** |
| 31 | Statistical Significance & Hypothesis Testing | **COMPLETE_CANONICAL** |
| 32 | External Dataset & Domain Shift Evaluation | **COMPLETE_CANONICAL** |
| 33 | Final System Failure & Boundary Error Analysis | **COMPLETE_CANONICAL** |
| 34 | Computational Efficiency & Runtime Profiling | **COMPLETE_CANONICAL** |
| 35 | Feature Attribution & Visual Interpretability | v1.0f SOURCE-FROZEN; SYNTHETIC SMOKE ELIGIBLE_NOT_STARTED; SCIENTIFIC EXECUTION NOT_STARTED |
| 36 | Robustness & Image Perturbation Analysis | NOT_STARTED |
| 37 | Comprehensive Visual & Tabular Evidence Consolidation | NOT_STARTED |

### Stage D — Protocol Freeze, Single-Pass Untouched Test Benchmark & Publication Package (38-40)

| Phase | Title | Status |
|---|---|---|
| 38 | Manuscript Protocol & Checkpoint Freeze | NOT_STARTED |
| 39 | **Final Untouched Test Cohort Evaluation** | NOT_STARTED — **the ONLY TEST phase** |
| 40 | Publication Package & Reproducibility Audit | NOT_STARTED |

### Stage E — Deployment Engineering & Post-Release Operations (41-43)
> **Supervisor-adopted deployment extension (roadmap extension v1.0).** Stage E is
> **NOT_AUTHORIZED_FOR_EXECUTION**; it does not infer that Phases 36-40 are complete. It exists
> solely to give the canonical roadmap an explicit deployment terminus, subject to separate
> pre-execution authorisation.

| Phase | Title | Status |
|---|---|---|
| 41 | Deployment Engineering & Model Packaging | NOT_STARTED (NOT_AUTHORIZED_FOR_EXECUTION) |
| 42 | End-to-End Deployment Validation | NOT_STARTED (NOT_AUTHORIZED_FOR_EXECUTION) |
| 43 | Research Deployment Release, Monitoring & Maintenance | NOT_STARTED (NOT_AUTHORIZED_FOR_EXECUTION) |

### Phase35 v1.0f bindings

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
