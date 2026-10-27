# C1 integration compute feasibility — metadata and estimates only

## Observed environment

Read-only nvidia-smi: NVIDIA GeForce RTX3060 Ti,8192 MiB total,4651 MiB free, driver610.88 at inspection. PyTorch2.6.0+cu124, CUDA build12.4 visible, Python3.11.9. CPU synthetic tests are the only model execution performed. CUDA visibility is not a 512-batch training feasibility benchmark and no GPU forward/backward or real inference was run.

Disk at inspection: C free90,527,449,088 bytes; D free137,866,403,840 bytes. Transient values, not reservation. Windows `w32tm /query /status` returned service not started (0x80070426); synchronization/reliable absolute timestamps are NOT established. Do not treat local times as approval evidence. Operator remediation/readiness required before scientific execution.

## Footprint and storage estimate

Both models contain3,523,001 FP32 parameters (14,092,004 bytes); treatment trainable3,523,001, control3,432,233. Each committed epoch contains current parameters, selected best parameters, two Adam moment tensors for trainable parameters, optimizer/scheduler/scaler bookkeeping, full growing history and selected-case records. Approximate baseline parameter/moment payload: treatment56,368,016 bytes; control55,641,872 bytes (four parameter copies equivalent for treatment, two full parameter copies plus two trainable moment copies for control). This is byte arithmetic, not measured VRAM or serialized checkpoint size. NumPy/RNG/records and serialization overhead add size.

Conservative planning allowance: about60–80 MiB per committed epoch,100 epochs x6 runs gives roughly35–47 GiB retained checkpoint space, plus orphan attempts, temp write duplication and logs/metadata. Reserve at least60 GiB on the approved output volume as a planning assumption, reassess against real serialization before launch. No retention pruning is automatic. RAM includes two fresh model construction states, current/best payload and serialization buffers; reserve several GiB, while activation/workspace demands are not measured. Sequential one-arm GPU training only.

Protocol max96 cumulative active GPU-hours is an administrative cap, not an ETA. Historical Phase21 freeze reports34,588.8289809227 seconds across81 epochs/one resume. That does not benchmark these prospective arms/seeds, changed resource occupancy or recovery. No performance speed-up, energy, mobile readiness or powered sample-size claim follows.

## Compatibility and recovery limits

CPU bitwise uninterrupted-versus-resumed equality is tested on fixed environment synthetic fixtures. CUDA, AMP and multiprocess augmentation recovery are not live-validated here. Resume identities bind software/device mode and integration source hashes; same runtime is required. Loader/sampler generator states are saved, but epochs—not mid-epoch workers—are replay units. Directory-entry durability against physical power loss on Windows is not guaranteed by file fsync alone. Exclusive local-disk writer assumptions apply; no network/distributed lease guarantee.

Current real-data entries always refuse before data or output access. Frozen protocol flags remain false. Genuine C1 approval, separate launch, clock/GPU/storage readiness, approved dependency provisioning, actual path/cohort checks and aggregate six-run budget supervision are still blockers. Exact hashed source dependencies exist locally but several are untracked historical workspace files; the scoped commit does not constitute a self-contained fresh-clone scientific release.

Git remote remains absent: GIT_REMOTE_CONFIGURATION_REQUIRED; push BLOCKED. Nothing in Git maintenance authorizes C1 or BARR-M1 execution.
