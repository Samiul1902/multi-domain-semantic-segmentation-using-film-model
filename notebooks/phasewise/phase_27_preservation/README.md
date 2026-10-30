# Multi-Domain Performance Preservation Audit (phase_27_preservation)

## 1. Scientific Overview
- **Phase ID:** phase_27_preservation
- **Scientific Title:** Multi-Domain Performance Preservation Audit
- **Current Status:** COMPLETE_CANONICAL (VAL808 continuity result frozen)
- **Core Question:** Phase 27 audits that regional refinement does not degrade global domain performance.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** docs/phase27_preservation_spec.md
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Predictions CSV + per-sample scores, per-domain + macro preservation tables, 5 deterministic figures, qualitative panels.
- **Reviewer Notebook:** `phase27_multidomain_preservation_audit.ipynb` (3x byte-identical).
- **Result:** macro-domain delta point `+0.002210`, 95% CI `[+0.001133, +0.003298]`;
  `PRESERVATION_ASSERTED = True` (lower bound strictly > -0.005); no domain harm.

## 5. Visual Standards
- **Sample Visualizations:** 5 deterministic figures (forest, macro-vs-margin, activation, Dice distributions, qualitative).
- **Prediction Panels:** 16 deterministic cases with TP/FP/FN error maps.

<!-- PHASE27_PRESERVATION_SPEC_COMPLETE -->
<!-- PHASE27_PRESERVATION_EXECUTION_COMPLETE -->

Terminal: `PHASE27_MULTIDOMAIN_PRESERVATION_AUDIT_COMPLETE__VAL808_CONTINUITY_RESULT_FROZEN__PHASE28_ELIGIBLE_NOT_STARTED`
