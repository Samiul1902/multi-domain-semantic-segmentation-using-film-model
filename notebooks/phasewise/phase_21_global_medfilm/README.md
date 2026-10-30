# Global MedFiLM Reference Architecture (phase_21_global_medfilm)

## 1. Scientific Overview
- **Phase ID:** phase_21_global_medfilm
- **Scientific Title:** Global MedFiLM Reference Architecture
- **Current Status:** ELIGIBLE / NOT STARTED — Phase-20 baseline is frozen and all Phase-21 entry criteria are met; scientific execution requires fresh supervisor authorization
- **Core Question:** Phase 21 establishes unified feature-interleaved multi-domain backbone.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** docs/phase21_medfilm_spec.md
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

## 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.

## Phase-21 eligibility

Phase 21 (Global MedFiLM) is **ELIGIBLE but NOT STARTED**. All **12/12** Phase-21 entry criteria are met (`reports/audits/phase20_phase21_entry_criteria.json`), and the Phase-20 baseline
checkpoint is frozen and immutable. Starting Phase 21 requires a fresh supervisor
authorization; it must be compared against the Phase-20 baseline on the **same 64**
deterministically selected VAL cases.
