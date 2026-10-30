# Phase 34 - Computational Efficiency & Runtime Profiling

**Revision:** `ra_medfilm_barr_phase34_efficiency_profiling_v1_0`
**Classification:** `PRE_EXECUTION_COMPUTATIONAL_EFFICIENCY_RUNTIME_AND_CONDITIONAL_COMPUTATION_PROFILING_SPECIFICATION`
**Phase folder / ID (immutable):** `phase_34_efficiency_profiling`
**Method:** RA-MedFiLM-BARR

## 1. Scope and standing
This document freezes the Phase34 profiling protocol **before** any measured timing,
memory or model-profiler execution. It is a specification only: no model was loaded,
no forward pass was run, no latency/FPS/memory was measured, no protected data was
touched and no training occurred.

Phase34 succeeds the Phase33 canonical closure
(`phase33_final_closure.json`, status `COMPLETE_CANONICAL`). Phase30 evidence, whenever
reused for weighting, carries the mandatory qualifier
`ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION` and the status `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL` (not upgraded).

## 2. Four evidence classes (never merged)
1. **HISTORICAL_ANALYTICAL_COMPUTE** - frozen Conv2d/Linear MAC lower bounds.
2. **STATIC_MODEL_RESOURCE_PROFILE** - parameter counts, checkpoint size, static tensor memory.
3. **MEASURED_HARDWARE_SPECIFIC_RUNTIME_PROFILE** - latency, throughput/FPS, inference GPU memory.
4. **CONDITIONAL_COMPUTATION_PROFILE** - final routed-system expected compute/runtime from the
   frozen execution-state distribution.

Discipline: an ANALYTICAL MAC LOWER BOUND is **not** measured latency; MAC count is **not**
energy and **not** memory footprint; measured GPU latency is **not** universal device latency;
measured FPS is **not** a hardware-independent property.

## 3. Canonical components (frozen)
| id | class | checkpoint | params | analytical MACs |
|---|---|---|---|---|
| G | GlobalMedFiLM | phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt | 3523001 | 31551740928 |
| R_psi | BARRRegionalRefinerV1 | phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt | 1276401 | 3230662656 |
| B_phi | BARRBenefitRouterV1 | phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt | 36801 | 36160 |
| S_omega | BARRPostSafetyV1 | phase25f_barr_post_safety_v1_0_seed42/final/final.pt | 1217 | 1168 |

`ANALYTICAL MAC LOWER BOUND` - exact for Conv2d and Linear; excludes GroupNorm
affine/statistics, SiLU, MaxPool2d, bilinear interpolation, FiLM elementwise modulation,
sigmoid, Embedding lookup and LayerNorm.

## 4. Conditional computation
Frozen state machine (Phase26): `FORCED_SKIP` and `SKIP_GLOBAL` run refiner=0/s_omega=0;
`EXECUTE_THEN_ACCEPT` and `EXECUTE_THEN_REJECT` both run refiner=1/s_omega=1 - the two
EXECUTE states have **identical** compute.

`E[MAC] = MAC(G) + MAC(B_phi) + p_activate * (MAC(R_psi) + MAC(S_omega))`

with `p_activate` from the frozen Phase30 ROUTER_HOLDOUT routing-state frequencies
(SKIP 635 / ETA 236 / ETR 4, n = 875). Weighted runtime computed this way is a
`WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE`, **not** direct holdout runtime.

## 5. Data access
Default profiling input is `SYNTHETIC_ONLY_FOR_MODEL_EXECUTION` (deterministic
`torch.randn`, PCG seed 42, float32, cuda). ROUTER_HOLDOUT raw images/GT, TEST images/GT,
external validation images and training data are all forbidden or not required. Frozen
result tables may be read for metadata, routing-state frequencies, checkpoint/source
binding and historical analytical compute - never to reopen image pixels.

## 6. Measurement protocol
- Primary latency batch size **1**; secondary throughput batch size **8** (eligible).
- Warmup **50** iterations; **5** blocks x **200** measured iterations (1000 total).
- CUDA Events primary, synchronized; `torch.cuda.synchronize()` before/after each block.
- FPS = processed synthetic samples / synchronized wall-clock interval (never 1000/mean).
- Memory: separate `checkpoint_file_bytes`, `parameter_bytes`, loaded baselines, peak
  allocated/reserved, and incremental peak; `reset_peak_memory_stats()` at a frozen point;
  fresh subprocess per arm.
- Primary scope `STEADY_STATE_INFERENCE` (load excluded); cold-start not enabled.
- Precision: `model.eval()`, no grad, `torch.inference_mode()` preferred, float32, no
  autocast, TF32 matmul off / cuDNN TF32 on, cuDNN benchmark off, deterministic off.

## 7. Environment (pre-execution snapshot)
OS `Windows-10-10.0.26200-SP0`, Python 3.11.9, PyTorch 2.6.0+cu124,
CUDA runtime 12.4 (driver 596.36), cuDNN 90100, GPU NVIDIA GeForce RTX 3060 Ti
(compute capability 8.6, 8,589,279,232 bytes VRAM), 16 logical CPU cores,
34,281,005,056 bytes RAM. `torch.profiler` available; `fvcore`/`thop`/`ptflops`/`torchinfo`
absent - **no complete FLOP profiler is available**, which is an acceptable negative
result. Nothing was installed.

## 8. Claim language
Allowed: "On the specified GPU/software configuration...", "Under batch size 1 and the
frozen precision protocol...", "Analytical Conv/Linear MAC lower bound...", "Weighted
runtime estimate using frozen Phase30 routing-state frequencies...". Forbidden unqualified:
real-time, mobile efficient, low-power, energy efficient, hardware independent, faster on
all devices, memory efficient (without exact metric), and "X FLOPs" when the value is
actually historical MACs. Phase34 alone does not establish clinical deployment readiness.

## 9. Locks
TEST = `LOCKED_UNTIL_PHASE39`; ROUTER_HOLDOUT = `OPENED_AND_FROZEN`; Phase34 execution
`NOT_STARTED`; Phase35 `NOT_STARTED`.
