# Baseline Failure Analysis & Small-Stone Error Modes (phase_11_failure_analysis)

## 1. Scientific Overview
- **Phase ID:** phase_11_failure_analysis
- **Scientific Title:** Baseline Failure Analysis & Small-Stone Error Modes
- **Core Question:** Phase 11 analyzes false-negative patterns and tiny-stone miss rates.

### Two-dimensional status

| Dimension | Status |
|---|---|
| Historical v2 (`phase4_v2`) | **COMPLETE** — `phase11_kub_failure_analysis_and_tiny_stone_errors.ipynb` |
| Clean-v3 Part 1A (protocol reconstruction + definition freeze) | **COMPLETE** — `phase11_clean_v3_failure_analysis_protocol_freeze.ipynb` |
| Clean-v3 full failure analysis (Part 1B) | **NOT STARTED** — requires supervisor authorization |

> The historical analysis is **HISTORICAL_v2** provenance (283 KUB VAL cases, `phase4_v2`,
> `kub_size_v1`). It must **not** be silently reused as clean-v3 evidence.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

Phase 11 is the diagnostic bridge between Phase 10 (baseline comparison) and Phase 12 (Oracle
ROI). The historical Phase-11 → Phase-12 rationale is recorded as:

> Observed FULL_FIELD, small-object, and multi-component failures motivate testing whether
> increased effective local resolution can recover missed targets; **no claim that ROI will
> solve them**.

## 3. Inputs & Governance Boundaries
- **Canonical historical source:** `reports/audits/phase11_kub_failure_analysis.json`
- **Clean-v3 inputs:** four frozen clean-v3 baselines + the Phase-10 paired VAL table
  (`phase10_clean_v3_paired_val_case_metrics.csv`, 280 KUB cases)
- **Dataset cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables

**Historical (v2, immutable):**
- `phase11_kub_failure_analysis_and_tiny_stone_errors.ipynb`
- `reports/tables/phase11_*` — per-image / per-component / multicomponent / size / cross-model tables
- `reports/figures/phase11_kub_failure_analysis/`, `reports/qualitative/phase11_kub_failure_analysis/`

**Clean-v3 Part 1A (protocol artifacts — no failure counts populated):**
- `phase11_clean_v3_failure_analysis_protocol_freeze.ipynb` (this phase's protocol notebook)
- `code/phase11_failure_protocol.py` (read-only support; no trainer, no optimizer steps)
- `reports/tables/phase11_historical_source_inventory.csv`
- `reports/tables/phase11_historical_failure_definition_matrix.csv`
- `reports/tables/phase11_clean_v3_failure_analysis_dimensions.csv`
- `reports/tables/phase11_clean_v3_hard_case_selection_protocol.csv`
- `reports/tables/phase11_phase12_bridge_reconstruction.csv`
- `reports/audits/phase11_historical_failure_protocol_reconstruction.{json,md}`
- `reports/audits/phase11_clean_v3_failure_analysis_protocol_candidate.{json,md}`

## 5. Frozen clean-v3 contracts (Part 1A)
- Foreground `mask > 0`; connectivity **8**; object matching overlap **>= 1 px**
- Size taxonomy **only** `kub_size_clean_v3_v1` (FULL_FIELD scope; ROI = `ROI_NOT_PRIMARY_BINNED`)
- Threshold **0.5** (fixed); KUB VAL **280** cases
- Regime separation: **FULL_FIELD 103 / ROI 177** — never pooled without showing both
- Category (Kidney/Bladder/Ureteric) is **subgroup metadata**, not a pixel class (Ureteric n=24)
- **No winner, no reference model, no new numerical thresholds introduced in Part 1A**

## 6. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.
- Hard-case cohort selection is frozen as a **procedure** first; cases are selected only in
  Part 1B (prevents cherry-picking).

## 7. Current action
**WAIT_FOR_SUPERVISOR_PHASE11_PROTOCOL_FREEZE_DECISION** — then Part 1B.
Phase 12 is **NOT** started. TEST is **LOCKED** until Phase 39.
