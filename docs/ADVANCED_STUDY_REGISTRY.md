# ADVANCED STUDY REGISTRY — RA-MedFiLM-BARR (EXT-02.1A)

**Revision ID:** `RA_MEDFILM_BARR_EXT02_1A_ADVANCED_STUDY_PROGRAM_V1_0` — **PLANNING/PRE-REGISTRATION ONLY** (`scientific_delta = 0`).
**Status:** all 32 studies `NOT_STARTED`. Preregistered before EXT-03; no result-driven study addition allowed later.

## Priority tiers

- **TIER 1 (main paper / must):** AS-01, AS-03, AS-04, AS-05, AS-06, AS-08, AS-09, AS-10, AS-11, AS-12, AS-13, AS-15, AS-16, AS-20, AS-21, AS-24, AS-27, AS-30, AS-31
- **TIER 2 (strong support / supplement):** AS-02, AS-14, AS-17, AS-18, AS-19, AS-22, AS-23, AS-25, AS-26, AS-29
- **TIER 3 (resource dependent):** AS-07, AS-28, AS-32

## Study matrix

| ID | Name | Tier | Class | Training | New inference | External | Protected | Status |
|---|---|---|---|---|---|---|---|---|
| AS-01 | Four-Domain Dataset Progression | TIER 1 | CORE_CONFIRMATORY_EXTENSION | True | True | False | False | NOT_STARTED |
| AS-02 | Fixed-N Domain-Diversity Progression | TIER 2 | PRESPECIFIED_ESTIMATION | True | True | False | False | NOT_STARTED |
| AS-03 | Training Data-Volume / Learning-Curve Study | TIER 1 | CORE_CONFIRMATORY_EXTENSION | True | True | False | False | NOT_STARTED |
| AS-04 | Single-Domain vs Shared Multi-Domain | TIER 1 | CORE_CONFIRMATORY_EXTENSION | True | True | False | False | NOT_STARTED |
| AS-05 | Negative Transfer / Domain Retention | TIER 1 | CORE_CONFIRMATORY_EXTENSION | True | True | False | False | NOT_STARTED |
| AS-06 | Leave-One-Domain-Out / Domain-Exclusion Generalization | TIER 1 | PRESPECIFIED_ESTIMATION | True | True | False | False | NOT_STARTED |
| AS-07 | Domain-Order Sensitivity | TIER 3 | OPTIONAL_RESOURCE_DEPENDENT | True | True | False | False | NOT_STARTED |
| AS-08 | Same-Protocol Model Benchmark | TIER 1 | CORE_CONFIRMATORY_EXTENSION | True | True | False | False | NOT_STARTED |
| AS-09 | Oracle Refinement Upper Bound | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-10 | Router Regret / Oracle Gap | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-11 | Benefit-Capture Study | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-12 | Harm-Avoidance / Safety-Rescue Study | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-13 | State-Machine Performance | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-14 | Execution-Budget Study | TIER 2 | PRESPECIFIED_ESTIMATION | False | True | False | False | NOT_STARTED |
| AS-15 | Compute-Accuracy Pareto Study | TIER 1 | PRESPECIFIED_ESTIMATION | False | True | False | False | NOT_STARTED |
| AS-16 | Router Calibration | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-17 | Segmentation Uncertainty | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | False | False | NOT_STARTED |
| AS-18 | Selective Risk / Coverage | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | False | False | NOT_STARTED |
| AS-19 | Domain-Shift / OOD Uncertainty | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | True | False | NOT_STARTED |
| AS-20 | External Cross-Dataset Evaluation | TIER 1 | CORE_CONFIRMATORY_EXTENSION | False | True | True | False | NOT_STARTED |
| AS-21 | Foreground-Size Stratification | TIER 1 | PRESPECIFIED_ESTIMATION | False | True | False | False | NOT_STARTED |
| AS-22 | Input-Difficulty / Contrast Stratification | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | False | False | NOT_STARTED |
| AS-23 | Boundary-Quality Study | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | False | False | NOT_STARTED |
| AS-24 | FP/FN Error Decomposition | TIER 1 | PRESPECIFIED_ESTIMATION | False | True | False | False | NOT_STARTED |
| AS-25 | Corruption-Severity / Robustness Curves | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | False | False | NOT_STARTED |
| AS-26 | ROI / Proposal Sensitivity | TIER 2 | PRESPECIFIED_EXPLORATORY | False | True | False | False | NOT_STARTED |
| AS-27 | Seed Stability / Reproducibility | TIER 1 | CORE_CONFIRMATORY_EXTENSION | True | True | False | False | NOT_STARTED |
| AS-28 | Model Capacity / Size | TIER 3 | OPTIONAL_RESOURCE_DEPENDENT | True | True | False | False | NOT_STARTED |
| AS-29 | FiLM / Representation Analysis | TIER 2 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-30 | Counterfactual Safety Study | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-31 | Structured Qualitative Error Atlas | TIER 1 | PRESPECIFIED_MECHANISTIC | False | True | False | False | NOT_STARTED |
| AS-32 | Foundation-Model Context Benchmark | TIER 3 | OPTIONAL_RESOURCE_DEPENDENT | True | True | False | False | NOT_STARTED |

## Computational-scope rule

Do NOT train every model for every study. The seven-model panel is used mainly for AS-08. Primary advanced-study systems are
GlobalMedFiLM and RA-MedFiLM-BARR; router studies use RA-MedFiLM-BARR only; standard baselines reuse frozen EXT-03 checkpoints.

## Execution roadmap

- EXT-03: AS-08, AS-27 (baseline reproducibility)
- EXT-04: AS-01, AS-02, AS-03, AS-04, AS-05, AS-07 (optional)
- EXT-05: AS-06 · EXT-05B: AS-09, AS-10, AS-11, AS-12, AS-13, AS-30 · EXT-05C: AS-14, AS-15
- EXT-06: AS-20 · EXT-07: AS-16, AS-17, AS-18, AS-19 · EXT-08: AS-21, AS-22, AS-23, AS-24
- EXT-09: AS-25, AS-26, AS-29, AS-31 · EXT-09B: AS-28, AS-32 · EXT-10: consolidation · EXT-11: manuscript V2

## Claim boundaries

- No outcome-dependent studies; no external-driven model selection; no TEST reuse; no post-hoc subgroup definitions; no best-seed headline.
- Oracle/safety studies are internal-development only. LODO terminology is gated by architecture validity (learned task embeddings):
  if a held-out task embedding is untrained, use DOMAIN_EXCLUSION_GENERALIZATION_STRESS_TEST, NOT zero-shot LODO generalization.
- Exploratory studies are not confirmatory. Reuse Phase36 evidence where sufficient. Negative results are retained.

**EXT-03 remains ELIGIBLE_NOT_STARTED.** No scientific outcome observed.

## EXT-03R Stage-A Technical Recovery (2026-10-11)

EXT-03 **STAGE-A RECOVERED** (SegFormer-B0 bound; five-architecture smoke tests PASS; resumable 15-run harness frozen). **EXT-03 STAGE-B ELIGIBLE_NOT_STARTED.** AS-08 = `NOT_STARTED`; AS-27 = `NOT_STARTED` (not advanced by recovery). Historical EXT-03 blocker preserved and disclosed.
