# C1 compute and execution feasibility — read-only inspection

## Current resource observations (not a training benchmark)

- `nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader`: NVIDIA GeForce RTX3060 Ti,8192 MiB total,4655 MiB free, driver610.88. Free VRAM is a transient inspection value, not reserved capacity; do not launch alongside other GPU work.
- Existing venv metadata: Python3.11.9; PyTorch2.6.0+cu124, CUDA build12.4; CUDA availability=True; cuDNN90100; pytest9.1.1. This shows driver/runtime visibility, not validated 512-batch training or recovery. Only CPU synthetic forward/backward/optimizer steps were exercised; no GPU model smoke test.
- Disk at inspection: C free90,689,236,992 bytes; D free137,929,134,080 bytes. Not a storage guarantee. Workstation load, checkpoint retention and outputs require an approved operator plan.
- `w32tm /query /status` failed: service not started (0x80070426). Do not claim synchronized Windows time or trustworthy absolute run timestamps. Operator must restore/verify timekeeping before real execution. Synthetic elapsed seconds are test-run observations, not wall-clock authorization evidence.

## Recomputed model footprint (CPU synthetic construction)

| Quantity | C1-T | C1-C |
|---|---:|---:|
| Total parameters | 3,523,001 | 3,523,001 |
| Trainable | 3,523,001 | 3,432,233 |
| Frozen | 0 | 90,768 |
| FP32 parameter bytes | 14,092,004 | 14,092,004 |
| Approx. parameters + trainable gradients + two FP32 Adam moments (bytes) | 56,368,016 | 55,278,800 |

Last row is tensor arithmetic, not measured GPU memory; excludes activations, convolution workspaces, allocator, AMP state, optimizer temporaries, dataloader buffers and checkpoint serialization. Two arms must train sequentially, not simultaneously. The control retains FiLM modules/forward arithmetic but excludes their gradients/optimizer state. Identical total size is not identical effective compute. The Phase26 G inventory gives31,551,740,928 Conv/Linear MACs as an **analytical lower bound**, not timing/energy; this control was not separately profiled for MACs or latency.

## Historical timing and conservative allocation

`reports/audits/phase21_final_freeze.json`, training:34,588.8289809227 elapsed seconds,81 epochs, one logical seed42 run, one resume, best epoch66. That is historical evidence under its own environment, not a benchmark for prospective arms/seeds. Six fresh runs at up to100 epochs need a reserved multi-day GPU window and monitored storage. Proposed96 cumulative active GPU-hours is a stop/approval budget, not a prediction that the study will finish within it. No future per-epoch, six-run ETA, speed-up, OOM margin or powered sample-size claim is measured.

Do not reduce batch/resolution, remove augmentation, change LR/precision or retry a failure for score. OOM or any nonfinite batch stops the run and requires accountable review. More free GPU memory can be obtained operationally by scheduling, not by changing science.

## Recovery/source readiness risk

Historical Phase21 trainer creates historical directories before completing preflight, directly saves checkpoints after writing history and does not persist all RNG states. Its docstring's bit-exact resume claim must not be mistaken for tested atomic multi-file recovery. C1 must not invoke that unchanged executable on the historical namespace. A separately integrated additive real-data runner needs verified locks, atomic writes/recovery, source/input digests, approved scope and per-arm RNG replay before launch. Current control helper is functional; full real-data trainer/recovery integration is not included.

Forty pre-existing tracked modifications/deletions differ from the older Git HEAD and were preserved. A targeted check of current src/data/transforms.py, src/data/loaders.py and src/data/multidomain_dataset.py found their raw hashes match the Phase20 protocol's recorded code digests. Git dirtiness is not by itself scientific recipe drift. A future driver must nevertheless bind all executed dependencies and refuse any unexplained authority mismatch. Frozen GlobalMedFiLM source hash is verified by the control helper.

**Git dependency limitation:** Frozen GlobalMedFiLM source exists and hash-matches locally but is not tracked by the current Git history. The preparation commit intentionally stages only new C1 files, not historical/unrelated source. It is not a self-contained fresh-clone training release. A reproducibility/launch plan must preserve and provide these exact hash-bound dependencies without silently substituting models or editing authority.

**Feasibility conclusion:** the exact identity control is implementable and CPU-synthetic tested. Historical hardware makes canonical-size training plausible but does not demonstrate present free-VRAM sufficiency. Clock service, driver integration/recovery, dependency drift review, GPU reservation and scientific approval/launch remain blockers. Overall EXECUTION_READY=false; no real scientific execution started.
