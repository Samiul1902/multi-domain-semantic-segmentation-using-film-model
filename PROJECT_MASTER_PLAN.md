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

## 6. Dataset / Split Summary (phase4_v2)
- **Total Images:** 8441 (ISIC: 3694, BUSI: 927, Kvasir: 1000, KUB: 2820).
- **Global Split:** TRAIN = 5913, VAL = 845, TEST = 1683 (LOCKED).
- **KUB Component Taxonomy:** Original-space connected components define authoritative count (1162 in TRAIN) and size quartiles (`kub_size_v1`).

---

## 7. Canonical 41-Phase Master Progression (Phase 00 through Phase 40)

### Stage A: KUB Radiograph Regional & Tiny-Object Development (Phases 00–18)
- **Phase 00:** Governance & Protocols (COMPLETE)
- **Phase 01:** Project Initialization & Layout (COMPLETE)
- **Phase 02:** Environment & CUDA Verification (COMPLETE)
- **Phase 03:** Dataset Discovery & Cataloging (COMPLETE)
- **Phase 04:** Manifest & Data Splits (COMPLETE)
- **Phase 05:** Forensic Leakage Audit (COMPLETE)
- **Phase 06:** KUB Anatomical Characterization (COMPLETE)
- **Phase 07:** Object Size Taxonomy & Quartiles (COMPLETE)
- **Phase 08:** Baseline Infrastructure & Factories (COMPLETE)
- **Phase 09:** Global Baseline Training (U-Net) (COMPLETE)
- **Phase 10:** Baseline Comparison (UNet vs UNet++ vs SegNet) (COMPLETE)
- **Phase 11:** Baseline Failure Analysis (COMPLETE)
- **Phase 12:** Oracle ROI Upper Bound Analysis (COMPLETE)
- **Phase 13:** Predicted ROI Proposal Localization (Stage 4D) (COMPLETE)
- **Phase 14:** Regional Refiner Diagnostic Evaluation (COMPLETE - DIAGNOSTIC)
- **Phase 15:** Regional Refiner Segmentation Loss Study (CURRENT - PROTOCOL FROZEN)
- **Phase 16:** Regional-Global Mask Fusion (NOT_STARTED)
- **Phase 17:** KUB Regional Pipeline Comprehensive Ablation (NOT_STARTED)
- **Phase 18:** KUB Final Development Validation Benchmark (NOT_STARTED)

### Stage B: Multi-Domain Harmonization & RA-MedFiLM Architecture (Phases 19–26)
- **Phase 19:** Multi-Domain Dataset Harmonization (ISIC, BUSI, Kvasir, KUB) (NOT_STARTED)
- **Phase 20:** Multi-Domain Global Baseline Evaluation (NOT_STARTED)
- **Phase 21:** Global MedFiLM Reference Architecture (NOT_STARTED)
- **Phase 22:** Multi-Domain Scale & Transfer Gap Analysis (NOT_STARTED)
- **Phase 23:** Literature & Methodological Novelty Positioning (NOT_STARTED)
- **Phase 24:** RA-MedFiLM Architectural Specification (NOT_STARTED)
- **Phase 25:** RA-MedFiLM Controlled Module Development (NOT_STARTED)
- **Phase 26:** Full Four-Domain Joint Architecture Training (NOT_STARTED)

### Stage C: Multi-Domain Rigor, Ablation, Reproducibility & Clinical Evidence (Phases 27–37)
- **Phase 27:** Multi-Domain Performance Preservation Audit (NOT_STARTED)
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
