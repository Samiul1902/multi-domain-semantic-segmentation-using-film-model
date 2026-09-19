# Baseline Comparison (U-Net vs UNet++ vs SegNet) (phase_10_baseline_comparison)

## 1. Scientific Overview
- **Phase ID:** phase_10_baseline_comparison
- **Scientific Title:** Baseline Comparison (U-Net vs UNet++ vs SegNet)
- **Current Status:** COMPLETE
- **Core Question:** Phase 10 benchmarks standard architectures, showing UNet++ superiority.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** reports/audits/phase10_kub_baseline_comparison.json
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

## 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.
