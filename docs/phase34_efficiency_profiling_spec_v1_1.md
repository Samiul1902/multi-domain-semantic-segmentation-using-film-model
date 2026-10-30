# Phase 34 - Computational Efficiency & Runtime Profiling (v1.1)

**Revision:** `ra_medfilm_barr_phase34_efficiency_profiling_v1_1`
**Classification:** `PRE_EXECUTION_RUNTIME_NUMERICAL_SEMANTICS_AND_ANALYTICAL_COMPARATOR_RECONCILIATION`
**Phase folder / ID (immutable):** `phase_34_efficiency_profiling`
**Method:** RA-MedFiLM-BARR
**Supersedes for future measurement:** v1.0 (`ra_medfilm_barr_phase34_efficiency_profiling_v1_0`)

## 0. Standing
v1.0 was a **pre-execution** specification and produced **no measurements**. v1.1 corrects
runtime-profile semantics **before the first measurement**. No Phase34 measured result changed,
because none existed. Every v1.0 artifact is preserved byte-for-byte.

## 1. Issue 1 - component-specific runtime precision restored
v1.0 flattened all components into a uniform float32 / autocast-OFF / inference_mode
protocol. The frozen canonical inference semantics are component-specific:

| component | dtype | autocast | gradient context | inference_mode | scientific batch |
|---|---|---|---|---|---|
| G | float32 | **ENABLED (float16)** | `torch.no_grad()` | **false** | 8 |
| R_psi | float32 | disabled | `torch.inference_mode()` | true | 8 |
| B_phi | float32 | disabled | `torch.inference_mode()` | true | FULL_MATRIX_SINGLE_FORWARD |
| S_omega | float32 | disabled | `torch.inference_mode()` | true | 128 |

Authorities: `phase29_phase_d_component_inference_semantics_contract_v1_1.json`,
`phase30_component_inference_semantics_contract.json`,
`phase29_val808_shared_global_cache_contract_v1_2.json`.

Invariants: G's autocast semantics must **not** be applied to R_psi/B_phi/S_omega, and uniform
FP32/no-autocast must **not** replace G's canonical runtime semantics. Uniform FP32 is **not**
the canonical final-system runtime semantics; it survives only as an optional separately named
`STANDARDIZED_FP32_SYNTHETIC_RUNTIME_VARIANT`, which is `INELIGIBLE_NOT_REQUIRED` in v1.1.

## 2. Batch-size semantics
Primary latency remains batch 1, but it is labelled
`CANONICAL_GRAPH_HARDWARE_MICROBENCHMARK__BATCH1_NOT_CANONICAL_G_NUMERICAL_REPRODUCTION`. Reason: the frozen scientific G path uses batch 8 and is empirically
batch-membership-sensitive under autocast(fp16). Batch-1 timing is a hardware microbenchmark and
must **not** be described as bit-identical canonical Phase30 inference, canonical G numerical
reproduction, or literal Phase30 execution. Secondary batch-8 throughput uses G
autocast(fp16) + no_grad + inference_mode false and is labelled `SYNTHETIC_HARDWARE_THROUGHPUT_BENCHMARK`.

## 3. Issue 2 - analytical comparators reconciled
The literal predecessor ALWAYS_REFINE C2 comparator was conflated with a gated execute-all graph.

| comparator | graph | router | refiner | S_omega | MAC |
|---|---|---|---|---|---|
| LITERAL_GLOBAL_ONLY_C1 | G | no | no | no | 31551740928 |
| LITERAL_ALWAYS_REFINE_C2 | G + R_psi | **no** | yes | no | 34782403584 |
| FINAL_A8_C9_EXPECTED_CONDITIONAL | G + B_phi + p*(R_psi+S_omega) | yes | yes | yes | 32437902022.582855 |
| GATED_EXECUTE_ALL_C9 (optional) | G + B_phi + R_psi + S_omega | yes | yes | yes | 34782440912 |
| Phase25E gated K=N_eligible (pre-gate) | G + B_phi + R_psi | yes | yes | no | 34782439744 |

Predecessor authority (`phase25e_execution_metrics_contract_v1_0`): *"C1 and C2 bypass routing;
gated K=0 and gated K=N_eligible retain router overhead and must be labeled separately."*

Ratios (analytical MAC lower bound, static arithmetic):
- ratio vs LITERAL C1 = 1.0280859651
- ratio vs LITERAL C2 = 0.9325951826 ; saving = 2344501561.417 MACs
- ratio vs GATED_EXECUTE_ALL_C9 = 0.9325941818 ; saving = 2344538889.417 MACs

The two denominator semantics are **not merged**. `LITERAL_ALWAYS_REFINE_C2` has
`router_present = false`.

## 4. Timing scope
Frozen-harness timings cover only module forwards (and sigmoid where applicable) on
preconstructed synthetic tensors. They are labelled `MODEL_COMPUTE_PATH_RUNTIME` or
`SYNTHETIC_COMPONENT_RUNTIME` - never `END_TO_END_PIPELINE_RUNTIME`, because ROI geometry,
crop/resizing, interpolation, fusion, decision logic and host/device transfers are outside the
timed region.

## 5. Locks and status
TEST = `LOCKED_UNTIL_PHASE39`; ROUTER_HOLDOUT = `OPENED_AND_FROZEN`; Phase30 qualifier
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` (status COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL, not upgraded). Phase34 execution `NOT_STARTED`;
Phase35 `NOT_STARTED`. No model was loaded and no measurement was taken to produce this document.
