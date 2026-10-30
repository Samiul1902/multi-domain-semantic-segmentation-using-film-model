# Phase 30 — Final Development Validation Benchmark
## One-Shot ROUTER_HOLDOUT Evaluation (with disclosed protocol deviation)

- **Phase ID:** phase_30_final_validation
- **Scientific Title:** Final Development Validation Benchmark
- **Canonical status:** `COMPLETE_WITH_PROTOCOL_DEVIATION` · `SCIENTIFIC_RESULT_PRESERVED` · **NOT** `COMPLETE_CANONICAL`
- **ROUTER_HOLDOUT state:** `OPENED_AND_FROZEN` (n = 875; one-shot; no rerun)
- **Population:** ROUTER_HOLDOUT — **FINAL DEVELOPMENT VALIDATION BENCHMARK — NOT TEST**
- **Specification revision:** `ra_medfilm_barr_phase30_final_dev_validation_v1_3`

## Reviewer notebook

`phase30_final_development_validation.ipynb` — SHA-256
`635eb080f8d68ba82b1b150ce2099b2955f4eb0f5326bd2e4f056454905005c8`.
Evidence-replay only: **no model inference**, **no raw holdout image read**, **no GT read**.

## Result (frozen; not recomputed)

| quantity | value |
|---|---|
| global macro Dice | 0.9285481511747413 |
| A8 macro Dice | 0.9302871820357663 |
| macro ΔDice | **+0.0017390308610248934** |
| macro 95% CI | **[0.00111729355352301, 0.0024049809029647283]** |
| criterion | lower 95% CI > −0.005 |
| **PRESERVATION_ASSERTED** | **true** |
| p-values computed | **0** |

## Protocol deviation (permanent historical provenance)

The Stage-B scientific scoring source `scripts/analysis/phase30_execution_stage_b.py`
(SHA `9331c75bab2a5502c37ea4d9e1cd9afcf52766a0897b03c4d96a2c4fcc744fed`) was **not** included in the
pre-open source freeze. It was authored at `2026-10-04T03:15:36.906972+00:00`, ~2.9 s **after** the
irreversible first-open marker `2026-10-04T03:15:34+00:00`.

* Not retroactively repairable.
* Not relabelled governance-only.
* No retrospective pre-open SHA created.

**Mitigating evidence (supports the result; does not erase the deviation):** prediction hash barrier
PASS; GT reads at barrier = 0; GT physically read exactly once (875); no second GT pass; Stage-B
executed exactly once; no model rerun; no metric recomputation; no bootstrap regeneration; no
scientific artifact mutation; finalize script governance-only (0 GT reads, 0 model forwards);
TEST reads = 0; training = 0; all claim-bearing scientific outputs persisted before the §25 exception.

## Terminals

* Execution: `PHASE30_ONE_SHOT_ROUTER_HOLDOUT_EXECUTION_COMPLETE__A8_C9_FINAL_DEVELOPMENT_VALIDATION_RESULT_FROZEN__PHASE31_ELIGIBLE_NOT_STARTED`
* Blocked after first open: `PHASE30_ONE_SHOT_EXECUTION_BLOCKED_AFTER_FIRST_OPEN__STAGE_B_SCIENTIFIC_SOURCE_NOT_IN_PREOPEN_SOURCE_FREEZE__EVIDENCE_PRESERVED__NO_RERUN_AUTHORIZED`
* Supervisor adjudication: `PHASE30_SUPERVISOR_ADJUDICATION_COMPLETE__SCIENTIFIC_RESULT_PRESERVED_WITH_PREOPEN_SOURCE_FREEZE_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL__NO_RERUN__PHASE31_QUALIFIED_ELIGIBLE_NOT_STARTED`

## Evidence class

`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`

## Reporting boundary

Any publication/reporting claim must carry the deviation. Forbidden unqualified wording:
"fully preregistered execution", "perfectly source-frozen one-shot validation",
"Phase30 COMPLETE_CANONICAL", "no protocol deviations", "strictly protocol-perfect holdout".

## Phase31

Eligibility: `ELIGIBLE_WITH_PHASE30_PROTOCOL_DEVIATION_QUALIFIER`. Phase31 NOT started; TEST closed.
