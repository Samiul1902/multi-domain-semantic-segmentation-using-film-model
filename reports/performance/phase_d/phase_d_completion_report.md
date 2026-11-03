# Phase D — GPU Performance, Reliability and Reproducibility

**Status:** `PHASE_D_COMPLETE`  
**Evidence class:** `SYNTHETIC_BENCHMARK` — every measured number below comes from fixture weights and synthetic inputs. None of it is a real-data segmentation result.

## Deliverables

| # | Deliverable | Source | Present |
|---|---|---|---|
| 1 | Git HEAD and changed files | `git.json` | yes |
| 2 | Performance benchmark methodology | `benchmark.json` | yes |
| 3 | Actual measured CPU/GPU latency | `benchmark.json` | yes |
| 4 | Memory measurements | `memory.json` | yes |
| 5 | FULL versus Lite conditional compute | `conditional.json` | yes |
| 6 | FiLM gradient and conditioning verification | `film_conditioning.json` | yes |
| 7 | Checkpoint/resume reliability | `determinism.json` | yes |
| 8 | Synthetic evidence-isolation tests | `evidence_isolation.json` | yes |
| 9 | Failure-injection results | `failure_injection.json` | yes |
| 10 | CPU/CUDA parity observations | `cpu_cuda_parity.json` | yes |
| 11 | Complete regression-test results | `regression.json` | yes |
| 12 | Remaining technical blockers | `computed` | yes |
| 13 | Git commit hash | `git.json` | yes |
| 14 | Phase D completion decision | `computed` | yes |

## 1 / 13 — Git state

- HEAD: `279ed48cac46d58d42463bf3c159c06e51901c1c` on `master`
- commit used for this report: `279ed48cac46d58d42463bf3c159c06e51901c1c`
- changed files at report time: 50
  - `M .workbuddy-ai/memory/2026-11-03.md`
  - ` M .workbuddy-ai/memory/MEMORY.md`
  - ` M paper_doc/figures/fig01_method_architecture.pdf`
  - ` M paper_doc/figures/fig01_method_architecture.png`
  - ` M paper_doc/figures/fig01_method_architecture.svg`
  - ` M paper_doc/figures/fig02_dataset_protocol.pdf`
  - ` M paper_doc/figures/fig02_dataset_protocol.png`
  - ` M paper_doc/figures/fig02_dataset_protocol.svg`
  - ` M paper_doc/figures/fig02_dataset_protocol_source.csv`
  - ` M paper_doc/figures/fig05_barr_routing_safety.pdf`
  - ` M paper_doc/figures/fig05_barr_routing_safety.png`
  - ` M paper_doc/figures/fig05_barr_routing_safety.svg`
  - ` M paper_doc/figures/fig05_barr_routing_safety_source.csv`
  - ` M paper_doc/figures/fig06_internal_performance.pdf`
  - ` M paper_doc/figures/fig06_internal_performance.png`
  - ` M paper_doc/figures/fig06_internal_performance.svg`
  - ` M paper_doc/figures/fig06_internal_performance_source.csv`
  - ` M paper_doc/figures/fig07_external_stress_test.pdf`
  - ` M paper_doc/figures/fig07_external_stress_test.png`
  - ` M paper_doc/figures/fig07_external_stress_test.svg`
  - ` M paper_doc/figures/fig07_external_stress_test_source.csv`
  - ` M paper_doc/figures/fig08_main_qualitative.pdf`
  - ` M paper_doc/figures/fig08_main_qualitative.png`
  - ` M paper_doc/figures/fig08_main_qualitative.svg`
  - ` M paper_doc/figures/fig08_main_qualitative_source.csv`
  - ` M paper_doc/figures/fig08s_qualitative_overview.pdf`
  - ` M paper_doc/figures/fig08s_qualitative_overview.png`
  - ` M paper_doc/figures/fig08s_qualitative_overview.svg`
  - ` M paper_doc/figures/fig08s_qualitative_overview_source.csv`
  - ` M paper_doc/figures/fig09_failure_analysis.pdf`
  - ` M paper_doc/figures/fig09_failure_analysis.png`
  - ` M paper_doc/figures/fig09_failure_analysis.svg`
  - ` M paper_doc/figures/fig09_failure_analysis_source.csv`
  - ` M paper_doc/figures/fig10_accuracy_vs_cost.pdf`
  - ` M paper_doc/figures/fig10_accuracy_vs_cost.png`
  - ` M paper_doc/figures/fig10_accuracy_vs_cost.svg`
  - ` M paper_doc/figures/fig10_accuracy_vs_cost_source.csv`
  - ` M reports/audits/c1_r4_execution/synthetic_chain_test.json`
  - ` M scripts/analysis/run_c1_campaign_launch.py`
  - ` M src/research/evaluation/adapters.py`
  - ` M src/research/evaluation/provenance.py`
  - ` M src/research/evaluation/reports.py`
  - `?? _tmp/`
  - `?? paper_doc/RA_MedFiLM_BARR_Scientific_Report.pdf`
  - `?? paper_doc/render/`
  - `?? paper_doc/render_new/`
  - `?? scripts/analysis/phase_d_performance.py`
  - `?? src/research/performance/`
  - `?? tests/test_performance_phase_d.py`
  - `?? tests/test_rc2_missing_store_isolation.py`

## 2 — Benchmark methodology

- timing: time.perf_counter with CUDA synchronisation on both sides
- warm-up: 5 discarded iterations; 30 measured repeats per call
- statistics: median, p90, p95, mean, min, max, stdev per call
- cold versus warm: the first call is recorded separately as cold_first_call and never averaged into the warm figure
- MACs versus wall time: conv/linear MACs are architectural; latency is this host and this build. They are never substituted
- batch policy: FULL and Lite run per-image ROI geometry, routing and a safety gate; a batch>1 number for them would describe a pipeline that does not exist
- seeds: [42, 123, 3407]
- device: NVIDIA GeForce RTX 3060 Ti · torch 2.6.0+cu124 · CUDA 12.4 · cuDNN 90100
- CUDA synchronised for every GPU timing: yes

## 3 — Measured latency

`SYNTHETIC_BENCHMARK` — batch 1, FP32, 512×512, RTX 3060 Ti.

| model | seed | init ms | forward p50 | forward p95 | pipeline p50 | pipeline p95 | img/s | peak alloc MiB | refiner rate |
|---|---|---|---|---|---|---|---|---|---|
| `RA_MEDFILM_BARR_FULL` | 42 | 389.2 | 15.09 | 15.59 | 87.99 | 104.35 | 11.4 | 352.5 | 1.00 |
| `RA_MEDFILM_BARR_FULL` | 123 | 383.3 | 17.18 | 24.58 | 101.04 | 113.88 | 9.9 | 352.5 | 1.00 |
| `RA_MEDFILM_BARR_FULL` | 3407 | 391.6 | 15.54 | 28.53 | 99.25 | 110.81 | 10.1 | 352.5 | 1.00 |
| `GLOBAL_MEDFILM` | 42 | 364.4 | 15.17 | 32.12 | 15.14 | 15.61 | 65.9 | 322.5 | — |
| `GLOBAL_MEDFILM` | 123 | 367.9 | 14.82 | 15.73 | 15.59 | 16.54 | 67.5 | 322.5 | — |
| `GLOBAL_MEDFILM` | 3407 | 367.0 | 15.25 | 26.65 | 15.59 | 16.36 | 65.6 | 322.5 | — |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 42 | 189.8 | 13.54 | 13.94 | 42.46 | 54.46 | 23.6 | 227.6 | 0.00 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 123 | 188.1 | 13.02 | 19.31 | 75.02 | 82.03 | 13.3 | 227.6 | 1.00 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 3407 | 193.5 | 12.66 | 12.79 | 40.88 | 44.82 | 24.5 | 227.6 | 0.00 |
| `UNET` | 42 | 441.0 | 11.33 | 11.59 | 12.41 | 12.75 | 88.3 | 282.8 | — |
| `UNET` | 123 | 439.2 | 11.69 | 11.90 | 12.54 | 12.86 | 85.5 | 282.8 | — |
| `UNET` | 3407 | 445.3 | 11.75 | 17.27 | 12.41 | 12.63 | 85.1 | 282.8 | — |
| `ATTENTION_UNET` | 42 | 496.5 | 13.35 | 14.05 | 14.06 | 14.51 | 74.9 | 343.1 | — |
| `ATTENTION_UNET` | 123 | 482.3 | 13.24 | 14.17 | 14.11 | 14.43 | 75.5 | 343.1 | — |
| `ATTENTION_UNET` | 3407 | 488.4 | 13.68 | 14.64 | 14.31 | 14.79 | 73.1 | 343.1 | — |
| `UNETPP` | 42 | 1108.7 | 34.80 | 35.80 | 35.05 | 36.37 | 28.7 | 712.2 | — |
| `UNETPP` | 123 | 1138.1 | 34.61 | 34.93 | 35.76 | 36.09 | 28.9 | 712.2 | — |
| `UNETPP` | 3407 | 1111.6 | 34.62 | 34.93 | 35.78 | 36.09 | 28.9 | 712.2 | — |
| `DEEPLABV3PLUS` | 42 | 806.8 | 14.62 | 15.83 | 16.08 | 17.51 | 68.4 | 308.2 | — |
| `DEEPLABV3PLUS` | 123 | 798.0 | 15.16 | 16.27 | 16.27 | 18.51 | 66.0 | 308.2 | — |
| `DEEPLABV3PLUS` | 3407 | 795.7 | 14.91 | 15.99 | 15.80 | 16.31 | 67.1 | 308.2 | — |
| `TRANSFORMER_MIT_UNET` | 42 | 412.4 | 11.64 | 12.30 | 11.83 | 12.25 | 85.9 | 208.6 | — |
| `TRANSFORMER_MIT_UNET` | 123 | 419.0 | 11.83 | 28.26 | 11.68 | 11.97 | 84.5 | 208.6 | — |
| `TRANSFORMER_MIT_UNET` | 3407 | 414.6 | 11.43 | 30.18 | 11.67 | 12.02 | 87.5 | 208.6 | — |

The **refiner rate** column is the fraction of the 30 measured calls in which the refiner actually ran. On a randomly initialised fixture this number is an artifact of untrained logits, not a property of the architecture: Phase C saw 1.00 for FULL and 0.00 for Lite on the same kind of fixture. It is reported to make the pipeline figure interpretable (a rate of 1.00 means the pipeline number includes the refiner on every call), never as expected behaviour of a trained model. Nothing was tuned to move it.

Pre/post-processing: preprocessing median 6.80 ms (CPU, PIL decode + resize + normalise), post-processing measured separately so it is never folded into model latency.

### FP32 versus mixed precision

| model | fp32 p50 | amp p50 | speed-up | max abs difference |
|---|---|---|---|---|
| `RA_MEDFILM_BARR_FULL` | 86.93 | 97.03 | 0.90× | 0.0000 |
| `GLOBAL_MEDFILM` | 25.03 | 23.26 | 1.08× | 0.0013 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 46.82 | 45.64 | 1.03× | 0.0000 |
| `UNET` | 21.34 | 13.76 | 1.55× | 0.0024 |
| `ATTENTION_UNET` | 24.38 | 15.52 | 1.57× | 0.0018 |
| `UNETPP` | 59.51 | 51.47 | 1.16× | 0.0038 |
| `DEEPLABV3PLUS` | 27.88 | 16.68 | 1.67× | 0.2943 |
| `TRANSFORMER_MIT_UNET` | 19.10 | 16.72 | 1.14× | 0.0051 |

Autocast changes the arithmetic; the delta is shown so a speed-up is never reported as free.

### Batch scaling (single-network models only)

| model | batch | per-image ms | images/s |
|---|---|---|---|
| `GLOBAL_MEDFILM` | 1 | 15.60 | 64.1 |
| `GLOBAL_MEDFILM` | 2 | 12.24 | 81.7 |
| `GLOBAL_MEDFILM` | 4 | 11.02 | 90.7 |
| `GLOBAL_MEDFILM` | 8 | 10.40 | 96.2 |
| `UNET` | 1 | 11.35 | 88.1 |
| `UNET` | 2 | 10.68 | 93.6 |
| `UNET` | 4 | 10.06 | 99.4 |
| `UNET` | 8 | 10.10 | 99.0 |
| `ATTENTION_UNET` | 1 | 12.89 | 77.6 |
| `ATTENTION_UNET` | 2 | 12.16 | 82.2 |
| `ATTENTION_UNET` | 4 | 11.73 | 85.3 |
| `ATTENTION_UNET` | 8 | 11.41 | 87.6 |
| `UNETPP` | 1 | 34.78 | 28.8 |
| `UNETPP` | 2 | 30.58 | 32.7 |
| `UNETPP` | 4 | 34.17 | 29.3 |
| `UNETPP` | 8 | 114.26 | 8.8 |
| `DEEPLABV3PLUS` | 1 | 15.81 | 63.3 |
| `DEEPLABV3PLUS` | 2 | 13.87 | 72.1 |
| `DEEPLABV3PLUS` | 4 | 13.07 | 76.5 |
| `DEEPLABV3PLUS` | 8 | 12.23 | 81.8 |
| `TRANSFORMER_MIT_UNET` | 1 | 13.57 | 73.7 |
| `TRANSFORMER_MIT_UNET` | 2 | 9.31 | 107.4 |
| `TRANSFORMER_MIT_UNET` | 4 | 8.76 | 114.2 |
| `TRANSFORMER_MIT_UNET` | 8 | 8.35 | 119.8 |

FULL and Lite are excluded: their ROI and safety stages are per-image, so a batched figure for them would describe a pipeline that does not exist.

## 4 — Memory

`SYNTHETIC_BENCHMARK`. `peak_allocated` is live memory; `peak_reserved` is allocator cache and is not a leak.

| stage | batch | micro-batch | accum | autocast | peak alloc MiB | peak reserved MiB |
|---|---|---|---|---|---|---|
| G_train | 1 | 1 | 1 | no | 934.9 | 1112.0 |
| G_train | 2 | 2 | 1 | no | 1762.1 | 2166.0 |
| G_train | 4 | 4 | 1 | no | 3412.8 | 4252.0 |
| R_train | 1 | 1 | 1 | no | 218.4 | 244.0 |
| R_train | 2 | 2 | 1 | no | 359.0 | 446.0 |
| R_train | 4 | 4 | 1 | no | 637.3 | 806.0 |
| B_train | 1 | 1 | 1 | no | 65.4 | 82.0 |
| B_train | 2 | 2 | 1 | no | 65.4 | 82.0 |
| B_train | 4 | 4 | 1 | no | 65.4 | 82.0 |
| S_train | 1 | 1 | 1 | no | 65.0 | 82.0 |
| S_train | 2 | 2 | 1 | no | 65.0 | 82.0 |
| S_train | 4 | 4 | 1 | no | 65.0 | 82.0 |

| inference path | peak alloc MiB | peak reserved MiB | parameters |
|---|---|---|---|
| `RA_MEDFILM_BARR_FULL` | 384.5 | 454.0 | 4837420 |
| `GLOBAL_MEDFILM` | 354.5 | 396.0 | 3523001 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 260.6 | 330.0 | 272601 |
| `UNET` | 315.3 | 422.0 | 7763041 |
| `ATTENTION_UNET` | 375.6 | 450.0 | 7851285 |
| `UNETPP` | 744.2 | 1076.0 | 9159681 |
| `DEEPLABV3PLUS` | 341.9 | 390.0 | 40347041 |
| `TRANSFORMER_MIT_UNET` | 240.6 | 306.0 | 16347777 |

Capacity search (largest batch that completes one step without OOM):

- G_train: max batch 16 (GPU total 8191 MiB)
- R_train: max batch 32 (GPU total 8191 MiB)
- B_train: max batch 32 (GPU total 8191 MiB)
- S_train: max batch 32 (GPU total 8191 MiB)

## 5 — FULL versus Lite conditional compute

`SYNTHETIC_BENCHMARK`. These are **branch costs**, not routing rates: the router scalar and the safety logit are scripted so each branch is reachable without a trained model. No threshold was changed.

| model | seed | scenario | state | latency p50 ms | G | R | refiner | safety |
|---|---|---|---|---|---|---|---|---|
| `RA_MEDFILM_BARR_FULL` | 42 | forced_skip | FORCED_SKIP | 20.66 | 1 | 0 | 0 | 0 |
| `RA_MEDFILM_BARR_FULL` | 42 | router_skip | SKIP_GLOBAL | 52.41 | 1 | 1 | 0 | 0 |
| `RA_MEDFILM_BARR_FULL` | 42 | safety_accept | EXECUTE_THEN_ACCEPT | 85.03 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_FULL` | 42 | safety_reject | EXECUTE_THEN_REJECT | 87.53 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_FULL` | 123 | forced_skip | FORCED_SKIP | 31.41 | 1 | 0 | 0 | 0 |
| `RA_MEDFILM_BARR_FULL` | 123 | router_skip | SKIP_GLOBAL | 62.84 | 1 | 1 | 0 | 0 |
| `RA_MEDFILM_BARR_FULL` | 123 | safety_accept | EXECUTE_THEN_ACCEPT | 99.18 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_FULL` | 123 | safety_reject | EXECUTE_THEN_REJECT | 102.38 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_FULL` | 3407 | forced_skip | FORCED_SKIP | 20.69 | 1 | 0 | 0 | 0 |
| `RA_MEDFILM_BARR_FULL` | 3407 | router_skip | SKIP_GLOBAL | 52.02 | 1 | 1 | 0 | 0 |
| `RA_MEDFILM_BARR_FULL` | 3407 | safety_accept | EXECUTE_THEN_ACCEPT | 79.18 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_FULL` | 3407 | safety_reject | EXECUTE_THEN_REJECT | 85.86 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 42 | forced_skip | FORCED_SKIP | 25.14 | 1 | 0 | 0 | 0 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 42 | router_skip | SKIP_GLOBAL | 45.52 | 1 | 1 | 0 | 0 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 42 | safety_accept | EXECUTE_THEN_ACCEPT | 79.16 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 42 | safety_reject | EXECUTE_THEN_REJECT | 77.87 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 123 | forced_skip | FORCED_SKIP | 19.93 | 1 | 0 | 0 | 0 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 123 | router_skip | SKIP_GLOBAL | 40.92 | 1 | 1 | 0 | 0 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 123 | safety_accept | EXECUTE_THEN_ACCEPT | 74.63 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 123 | safety_reject | EXECUTE_THEN_REJECT | 77.21 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 3407 | forced_skip | FORCED_SKIP | 23.92 | 1 | 0 | 0 | 0 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 3407 | router_skip | SKIP_GLOBAL | 44.94 | 1 | 1 | 0 | 0 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 3407 | safety_accept | EXECUTE_THEN_ACCEPT | 78.85 | 1 | 1 | 1 | 1 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 3407 | safety_reject | EXECUTE_THEN_REJECT | 81.53 | 1 | 1 | 1 | 1 |

| model | seed | global-only ms | always-refine ms | conditional ms | effective MACs | MACs if always refine |
|---|---|---|---|---|---|---|
| `RA_MEDFILM_BARR_FULL` | 42 | 14.14 | 77.40 | 79.96 | 34782440912 | 34782440912 |
| `RA_MEDFILM_BARR_FULL` | 123 | 15.01 | 90.19 | 97.70 | 34782440912 | 34782440912 |
| `RA_MEDFILM_BARR_FULL` | 3407 | 14.71 | 78.80 | 80.30 | 34782440912 | 34782440912 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 42 | 13.06 | 73.97 | 46.75 | 1619485760 | 1819687120 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 123 | 12.80 | 69.20 | 74.33 | 1819687120 | 1819687120 |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | 3407 | 12.93 | 74.35 | 46.52 | 1619485760 | 1819687120 |

A lower refiner count is not by itself a lower total cost, so the effective MAC figure is reported beside the branch count.

The three seeds share one architecture and differ only in randomly initialised weights, so the seed-to-seed spread above is not a performance difference between checkpoints. It comes from the fixture routing different numbers of ROIs on the same input, plus ordinary host state (allocator warm-up, clocks). Read each seed as one draw from the same distribution, not as a ranking.

## 6 — FiLM conditioning

- **PASS** `identity_propagation` — all 5 declared sites ran once and received the task embedding for the requested ids
- **PASS** `gradients_and_updates` — at step 0 only the FiLM output projection receives gradient (the zero initialisation blocks the hidden layer and the embedding); from step 1 all three do, and all three parameters move off their initial values
- **PASS** `learned_task_dependence` — loss fell 0.6994 -> 0.0000, below the task-blind optimum ln 2 = 0.6931; the same image under task 0 and task 1 now differs by max |delta| 156.73 in logit space (was 0.00e+00 at initialization), and a same-task repeat is bitwise identical
- **PASS** `c1_identity_control` — the arms start bitwise identical with equal total parameter counts; the control's conditioning is frozen and never moves, so its two task outputs are identical (max |delta| = 0) and it stays at the task-blind optimum (loss 0.6931 vs ln 2 = 0.6931), while the treatment conditions (max |delta| 156.73, loss 0.0000)
- **PASS** `unrelated_components_untouched` — a second model instance, the FiLM site list, the architecture id, the expected parameter counts and the C1 matched-arm construction are all bitwise unchanged after 30 optimization steps, while the treatment itself moved (c037f5764e65 -> 03557acd22fb)

## 7 — Checkpoint and resume reliability

- **PASS** `seeding` (exact) — python/numpy/torch draws reproduce exactly after re-seeding
- **PASS** `rng_capture_restore` (exact) — all four RNG sources replay exactly from a captured state
- **PASS** `empty_rng_state_refused` (exact) — cannot restore an empty RNG state
- **PASS** `loader_order` (exact) — the generator advances between epochs and a captured state reproduces the order exactly
- **PASS** `resume_equivalence` (exact) — resume with the generator state reproduces the uninterrupted trajectory exactly and ends on identical weights; without it the first resumed epoch diverges (0.445927 vs 0.446605)
- **PASS** `cuda_algorithms` (exact) — deterministic algorithms on, cudnn deterministic, benchmark off, CUBLAS workspace fixed; three repeats bitwise identical
- **PASS** `checkpoint_selection` (exact) — selection is identical in batch, streaming and after a CSV round-trip; a tie keeps the earlier epoch (4)
- **PASS** `dependency_identities` (exact) — the dependency fingerprint is stable across two reads; requirements.txt is UNPINNED, so the environment is recorded rather than guaranteed
- **PASS** `prediction_export` (exact) — the same records export byte-identically (same per-image hash and seal); per-image values and the aggregate are order-independent
- **PASS** `per_image_results` (exact) — per-image Dice/IoU/HD95 are identical on repetition; the float64 path differs by 0.000e+00 (tolerance, not identity)

## 8 — Synthetic evidence isolation

7/7 attacks blocked.

| attack | blocked | mechanism |
|---|---|---|
| output_directory_reuse | yes | publish_cell refuses a namespace change in one cell directory |
| registry_import | yes | verify_matrix counts only cells that pass research_evidence_reasons |
| report_aggregation | yes | collect_results shares the same promotion gate |
| resume_promotion | yes | a resume may not change the namespace of the cell it resumes |
| checkpoint_substitution | yes | research evidence requires a genuine 64-hex weight digest |
| artifact_copy | yes | a copied cell keeps its namespace; a foreign marker is found anywhere under the root, not only on a registry path |
| evidence_class_tamper | yes | the document is self-sealed, and the gate re-checks the weight digest |

## 9 — Failure injection

8/8 injections detected.

| stage | injection | detected by |
|---|---|---|
| global_training | G/best.pt replaced with an R-component envelope | FamilyCompatibilityError |
| cache_creation | cache manifest marked incomplete, then pinned to a different G digest | RuntimeError |
| refiner_training | R/final/final.pt replaced with a G-component envelope | FamilyCompatibilityError |
| benefit_label_generation | delta_dice inconsistent with candidate_refined_dice - global_dice | LABELS_INCONSISTENT |
| router_training | router feature matrix carrying a NaN | RuntimeError |
| safety_training | label manifest with no safety_features_sha256 | RuntimeError |
| evaluation_export | a roster missing two images, then a duplicated sample_id | PublicationError |
| result_publication | a relabelled sealed document, then a namespace change in an existing cell | REJECTED |

## 10 — CPU/CUDA parity

Tolerances inherited unchanged from the Phase B gate: binary agreement ≥ 0.99, mean |Δ| ≤ 0.002, exact routing-state match.

| model | shape | finite | max abs Δ | mean abs Δ | binary agreement | state |
|---|---|---|---|---|---|---|
| `RA_MEDFILM_BARR_FULL` | yes | yes | 0.000145 | 0.000016 | 1.0000 | EXECUTE_THEN_ACCEPT / EXECUTE_THEN_ACCEPT |
| `GLOBAL_MEDFILM` | yes | yes | 0.000221 | 0.000051 | 1.0000 | NOT_APPLICABLE / NOT_APPLICABLE |
| `RA_MEDFILM_BARR_LITE_DEPTHWISE` | yes | yes | 0.012309 | 0.000203 | 0.9994 | SKIP_GLOBAL / SKIP_GLOBAL |
| `UNET` | yes | yes | 0.000212 | 0.000029 | 0.9999 | NOT_APPLICABLE / NOT_APPLICABLE |
| `ATTENTION_UNET` | yes | yes | 0.000279 | 0.000039 | 1.0000 | NOT_APPLICABLE / NOT_APPLICABLE |
| `UNETPP` | yes | yes | 0.000428 | 0.000091 | 1.0000 | NOT_APPLICABLE / NOT_APPLICABLE |
| `DEEPLABV3PLUS` | yes | yes | 0.042412 | 0.000280 | 0.9997 | NOT_APPLICABLE / NOT_APPLICABLE |
| `TRANSFORMER_MIT_UNET` | yes | yes | 0.000637 | 0.000098 | 0.9997 | NOT_APPLICABLE / NOT_APPLICABLE |

No cross-device bitwise equality is claimed; these are agreement criteria on a numerically different implementation.

## 11 — Regression results

| run | passed | failed | errors | skipped | xfailed | exit |
|---|---|---|---|---|---|---|
| targeted (§13 areas) | 309 | 0 | 0 | 1 | 0 | 0 |

| area | passed | failed | errors | skipped |
|---|---|---|---|---|
| Architecture drift | 12 | 0 | 0 | 0 |
| CUDA memory | 49 | 0 | 0 | 0 |
| Checkpoint recovery | 1 | 0 | 0 | 0 |
| Dataset and ROI | 18 | 0 | 0 | 0 |
| Evidence-class separation | 26 | 0 | 0 | 0 |
| FULL pipeline | 24 | 0 | 0 | 0 |
| FiLM conditioning | 18 | 0 | 0 | 0 |
| Lite pipeline | 70 | 0 | 0 | 0 |
| Metrics and statistics | 25 | 0 | 0 | 0 |
| Phase C evaluation | 19 | 0 | 0 | 1 |
| Stage 6 | 47 | 0 | 0 | 0 |

No test failed in either run, so the classification table is empty.


## 12 — Remaining blockers

None recorded by this phase.

## 14 — Completion decision

`PHASE_D_COMPLETE`

| criterion | met | detail |
|---|---|---|
| all eight adapters profiled | yes | 8 distinct model keys profiled |
| routing branches benchmarked | yes | all four canonical states reached and asserted, plus the global-only / always-refine / conditional comparison |
| gpu memory characterised | yes | per-stage training peaks, inference peaks and a capacity search |
| deterministic resume demonstrated | yes | ablation shows the data-order fix is necessary and sufficient |
| film conditioning functionally verified | yes | functional task dependence plus a frozen-conditioning control that stays at the task-blind optimum |
| synthetic cannot masquerade | yes | 7/7 attacks blocked |
| interruption and corruption recovery | yes | 8/8 injections detected |
| new engineering regressions resolved | yes | new regressions: [] |
| protected restrictions intact | yes | Phase D code references no protected-split identifier and no institutional trust-store path (audited by the package scan in test_18), no trust-store file was written, and no real training was launched; this is a scope attestation for Phase D, not a measurement |
