# Three-Seed Deterministic Reproducibility Study (phase_29_3seed_reproducibility)

## 1. Scientific Overview
- **Phase ID:** phase_29_3seed_reproducibility
- **Scientific Title:** Three-Seed Deterministic Reproducibility Study
- **Current Status:** PHASE_D_COMPLETE (PHASE29 COMPLETE)
- **Core Question:** Phase 29 verifies stability and variance across 3 frozen random seeds.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** docs/phase29_repro_spec.md
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

## 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.

<!-- PHASE29_V1_1_EVALUATION_POPULATION_CLARIFICATION -->
## Additive clarification (Phase 29 spec v1.1)

The historical "TRAIN+VAL" wording above is **superseded operationally** for Phase 29 by:

* PRIMARY = `ROUTER_DEVELOPMENT` OOF
* SECONDARY = VAL808 continuity

`ROUTER_HOLDOUT` remains excluded (Phase 30 only). The original wording is preserved, not deleted.

<!-- PHASE29_PHASE_D_CANONICAL_EXECUTION_CLOSURE -->
## Phase D closure (canonical three-seed validation)

**Terminal:**
`PHASE29_PHASE_D_COMPLETE__CANONICAL_GLOBAL_REPRODUCED_SEED123_SEED3407_VAL808_INFERENCE_HASH_FROZEN_AND_THREE_SEED_REPRODUCIBILITY_FINALIZED__PHASE29_COMPLETE`

Reviewer notebook: `phase29_phase_d_canonical_three_seed_validation.ipynb` (executed, 3× deterministic).

* Canonical shared fixed-G cache: `data_cache/phase29_val808_shared_fixed_g_v1_1_canonical/`
  (one logical G pass, 102 batch forwards, exact Phase27 autocast-fp16 numerics).
* **Global reproduction gate PASSED**: canonical global prob is **bit-identical** to
  `phase27_val808_global_prob_f16.npy`
  (SHA `cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13`).
* seed123 / seed3407 executed from the canonical cache with frozen DEV-derived thresholds;
  `n_selected == n_refiner_forwards == n_somega_forwards` (255 / 262).
* All predictions hashed before any GT read → `PREDICTION_HASH_BARRIER_PASS`.
* Three-seed macro-domain equal-weight ΔDice: seed42 +0.002210, seed123 +0.003388, seed3407 +0.002869
  (all lower 95% CI bounds > −0.005) — **descriptive**, no ranking, no numeric pass/fail gate.
* ROUTER_HOLDOUT reads 0; TEST reads 0; training runs during Phase D 0. Phase30 NOT started.

The superseded (noncanonical) `data_cache/phase29_val808_shared_fixed_g_v1_0/` cache and the earlier
`data_cache/phase29_seed{s}/phase29_seed{s}_val808_decisions.csv` are preserved as evidence only.

