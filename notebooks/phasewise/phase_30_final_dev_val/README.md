# Final Development Validation Benchmark (phase_30_final_dev_val)

## 1. Scientific Overview
- **Phase ID:** phase_30_final_dev_val
- **Scientific Title:** Final Development Validation Benchmark
- **Current Status:** COMPLETE_WITH_PROTOCOL_DEVIATION / SCIENTIFIC_RESULT_PRESERVED / NOT_COMPLETE_CANONICAL
- **Core Question:** Phase 30 conducts final multi-domain validation before protocol freeze.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** docs/phase30_dev_val_spec.md
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

## 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.

<!-- PHASE30_ONE_SHOT_EXECUTION_CLOSURE_WITH_PROTOCOL_DEVIATION -->
## Phase 30 closure (one-shot ROUTER_HOLDOUT, with disclosed protocol deviation)

**Canonical status:** `COMPLETE_WITH_PROTOCOL_DEVIATION` · **Scientific result:** `PRESERVED` ·
**NOT** `COMPLETE_CANONICAL`.

**Supervisor adjudication terminal:**
`PHASE30_SUPERVISOR_ADJUDICATION_COMPLETE__SCIENTIFIC_RESULT_PRESERVED_WITH_PREOPEN_SOURCE_FREEZE_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL__NO_RERUN__PHASE31_QUALIFIED_ELIGIBLE_NOT_STARTED`

**Historical blocked terminal (preserved):**
`PHASE30_ONE_SHOT_EXECUTION_BLOCKED_AFTER_FIRST_OPEN__STAGE_B_SCIENTIFIC_SOURCE_NOT_IN_PREOPEN_SOURCE_FREEZE__EVIDENCE_PRESERVED__NO_RERUN_AUTHORIZED`

### Result (frozen, not recomputed)
* ROUTER_HOLDOUT n = 875 · global macro Dice 0.9285481511747413 · A8 macro Dice 0.9302871820357663
* macro ΔDice **+0.0017390308610248934** · 95% CI **[0.00111729355352301, 0.0024049809029647283]**
* criterion lower 95% CI > −0.005 → **PRESERVATION_ASSERTED = true** · p-values computed = **0**

### Protocol deviation (permanent historical provenance)
The Stage-B scientific scoring source `scripts/analysis/phase30_execution_stage_b.py`
(SHA `9331c75bab2a5502c37ea4d9e1cd9afcf52766a0897b03c4d96a2c4fcc744fed`) was **not** included in the
pre-open source freeze; it was authored at `2026-10-04T03:15:36.906972+00:00`, ~2.9 s **after** the
first-open marker `2026-10-04T03:15:34+00:00`. The deviation is **not** retroactively repairable and
the source is **not** relabelled governance-only.

**Mitigating evidence (does not erase the deviation):** prediction hash barrier PASS; GT reads at
barrier = 0; GT physically read exactly once (875); no second GT pass; no model rerun; no metric
recomputation; no bootstrap regeneration; no scientific artifact mutation; finalize script
governance-only (0 GT reads, 0 model forwards); TEST reads = 0; training = 0.

**Evidence class:**
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`

**Reporting:** the deviation must accompany any publication/reporting claim; no claim of perfect
preregistration/source-freeze conformance is permitted (see
`reports/audits/phase30_reporting_qualification_contract.json`).

**Phase31 eligibility:** `ELIGIBLE_WITH_PHASE30_PROTOCOL_DEVIATION_QUALIFIER`
(`reports/audits/phase30_phase31_qualified_handoff.json`). Phase31 NOT started.
