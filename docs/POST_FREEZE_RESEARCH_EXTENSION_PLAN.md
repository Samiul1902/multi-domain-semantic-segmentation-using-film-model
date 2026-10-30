# RA-MedFiLM-BARR — Post-Freeze Research Extension Plan

**Revision ID:** `RA_MEDFILM_BARR_POST_FREEZE_EXTENSION_V1_0` — DOCUMENTATION/PLANNING ONLY (`scientific_delta = 0`).
**Frozen baseline:** RA-MedFiLM-BARR V1 (Phases 0–40 + manuscript release; scope `MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY`).

This plan adds a clearly separated extension that strengthens the eventual paper **without altering any completed Phase 0–40 result**.

## 1. Motivation

The frozen V1 study already contains a multi-domain GlobalMedFiLM, conditional refinement, a learned benefit router, post-safety, preservation evidence, a 13-arm ablation, 3-seed reproducibility, the one-shot ROUTER_HOLDOUT evaluation, failure analysis, efficiency, interpretability, image robustness, proposal robustness, and a descriptive TEST evaluation. Two opportunities remain: (1) external/domain-shift validation was not completed; (2) a systematic 4-domain progression study has not been done.

## 2. External datasets

- `D:\Softfors\final\external_test_ds\HAM10000` → candidate ISIC / task 0
- `D:\Softfors\final\external_test_ds\Stones_where_are_you-.v3i.coco-segmentation` → candidate KUB / task 3
- `D:\Softfors\final\external_test_ds\CVC-ClinicDB` → candidate KVASIR / task 2
- `D:\Softfors\final\external_test_ds\BrEaST-Lesions_USG-images_and_masks` → candidate BUSI / task 1

**Prior-use status:** HAM10000, CVC-ClinicDB, BrEaST-Lesions_USG were used in the older MedFiLM-Seg programme and must NOT be labelled "untouched/never-seen/prospective clean" without proof. Stones_where_are_you has no prior use identified in the supplied old report — which alone does NOT prove independence. Evidence classes: `EXTERNALLY_SOURCED_WITH_PRIOR_RESEARCH_PROGRAM_USE` (HAM10000/CVC-ClinicDB/BrEaST) and `ELIGIBILITY_PENDING` (Stones_where_are_you).

## 3. Extension phases

| Phase | Title | Status | Depends on |
|---|---|---|---|
| EXT-01 | External Dataset Audit & Eligibility | NOT_STARTED | — (next action) |
| EXT-02 | External Evaluation Protocol Freeze | NOT_STARTED | EXT-01 PASS |
| EXT-03 | Same-Protocol Baseline Benchmark | NOT_STARTED | EXT-02 PASS |
| EXT-04 | Four-Domain Progression Study (ISIC→+BUSI→+KVASIR→+KUB) | NOT_STARTED | EXT-02 PASS |
| EXT-05 | Multi-Domain Generalization / Leave-One-Domain-Out | NOT_STARTED | EXT-04 design frozen |
| EXT-06 | External Validation (once per frozen model) | NOT_STARTED | EXT-01 PASS + EXT-02 PASS + frozen identities |
| EXT-07 | Calibration / Uncertainty Analysis | NOT_STARTED | EXT-06 probabilities |
| EXT-08 | Precision / Recall / Error Characterization | NOT_STARTED | EXT-06 |
| EXT-09 | Error / Failure Stratification | NOT_STARTED | EXT-08 (subgroups frozen first) |
| EXT-10 | Extended Evidence Consolidation | NOT_STARTED | EXT-03…EXT-09 complete |
| EXT-11 | Manuscript V2 / Supervisor Report V2 | NOT_STARTED | EXT-10 complete |

## 4. EXT-01 audit content (read-only)

Per dataset: identity; source/provenance; license; citation; image + mask counts; image/annotation format; dimensions; foreground semantics; binary segmentation compatibility; patient/case identifiers; duplicate filenames; duplicate file hashes; overlap with TRAIN / VAL808 / ROUTER_DEVELOPMENT / ROUTER_HOLDOUT / TEST; previous research use; candidate task-ID compatibility; preprocessing compatibility; exclusion criteria. Special care: HAM10000 must be checked for real segmentation masks; Stones_where_are_you (COCO-seg) must be checked for deterministic mapping to the frozen binary KUB foreground target.

Outputs: `reports/external_extension/external_dataset_inventory.json`, `_eligibility.json`, `_overlap_audit.json`, `_prior_use_ledger.json`. **STOP after audit; no inference.**

## 5. Metrics (freeze before any external inference)

Primary: Dice. Secondary: IoU, Precision, Recall, HD95. Accuracy is NOT the main metric (background imbalance). Empty-mask and HD95 conventions fixed before inference.

## 6. V1 / V2 separation

V1 is immutable. Any improved model is a NEW `RA-MedFiLM-BARR V2` branch using TRAIN + development-validation only; it must not tune on original-TEST or opened-external outcomes and can never replace V1 results.

## 7. Immutable boundaries

Phases 0–40 (and the frozen manuscript release) are never rewritten; prior-use external datasets carry disclosure; no external inference before freeze; no tuning on external/TEST outcomes; no "untouched" claim without proof; negative results preserved; no best-seed selection.

## 8. Next phase

**EXT-01 — External Dataset Audit & Eligibility — `ELIGIBLE_NOT_STARTED`.**

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
