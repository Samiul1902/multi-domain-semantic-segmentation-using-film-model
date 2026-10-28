# C1 — GPU and Storage Readiness v1.0

Status: `READ_ONLY_VERIFIED`
All values below are either **MEASURED** on this host at the time of this task, or
explicitly labelled **ESTIMATE**. No training run was performed; no measured
runtime is claimed.

---

## 1. GPU — MEASURED

| Property | Value |
|---|---|
| Model | NVIDIA GeForce RTX 3060 Ti |
| Total VRAM | 8192 MiB (8191.375 MiB reported by torch) |
| Used at query time | 722 MiB |
| Free at query time | 7303 MiB |
| Driver | 610.88 |
| Compute capability | 8.6 |
| torch CUDA build | 12.4 |
| cuDNN | 9.1.0 |

### Competing GPU processes

`nvidia-smi --query-compute-apps` enumerated 25 processes, **all of them
desktop/compositor/UI processes** (`explorer.exe`, `ShellHost.exe`,
`msedgewebview2.exe`, `chrome.exe`, NVIDIA Overlay, NVIDIA Broadcast, Parsec,
WorkBuddyAI, VS Code, Windows Terminal, etc.). None is a compute workload.

Two entries reported `[Insufficient Permissions]` for name and `[N/A]` for
memory — these are almost certainly additional UI/system processes, but their
identity could not be confirmed without elevation. They are **not** confirmed
compute jobs, and the measured 722 MiB total GPU usage is consistent with
desktop compositing only.

**Conclusion:** no competing compute workload. The GPU is available.

### VRAM headroom at the frozen C1 recipe — MEASURED

The protocol fixes `resolution=512`, `train_batch_size=4`, `eval_batch_size=8`,
`amp=true`. These were exercised with **artificial tensors only**:

| Workload | Peak allocated | Peak reserved | Headroom of 8192 MiB |
|---|---|---|---|
| TRAIN 512×512, B=4, AMP, fwd+bwd+step | 3404.3 MiB | 3866.0 MiB | 4326.0 MiB |
| EVAL 512×512, B=8, AMP, no_grad | 2340.1 MiB | 2954.0 MiB | 5238.0 MiB |

Baseline allocated with model resident: 13.5 MiB (3,523,001 params × 4 B ≈ 13.4 MiB).

**Verdict:** the frozen recipe fits with >4.3 GiB headroom. No batch-size
reduction is required, and no protocol change is needed for VRAM reasons.

Caveat: these figures exclude CUDA context overhead outside torch's allocator
and exclude host-side worker memory. They also assume the frozen recipe is used
unchanged; a larger batch would need re-measurement.

## 2. Storage — MEASURED + ESTIMATE

| Item | Value | Type |
|---|---|---|
| Drive | D: | measured |
| Capacity | 932 GiB | measured |
| Used | 804 GiB (862,428,446,720 B) | measured |
| **Available** | **128.3 GiB (137,772,544,000 B)** | measured |
| Existing `checkpoints/` | 6.4 GiB | measured |
| One Phase-21 checkpoint file (`best.pt`) | 42,369,710 B ≈ 40.4 MiB | measured |

### Per-checkpoint size

Measured Phase-21 checkpoint: 42.37 MB, containing model + optimizer +
scheduler + scaler + RNG + history. This is the correct analogue for C1.

Independent ESTIMATE from parameter accounting agrees:
model 13.4 MiB + AdamW two moments 26.9 MiB + ~2 MiB overhead ≈ **42.3 MiB**.

### Six-run aggregate — ESTIMATE (not measured)

C1 is 2 arms × 3 seeds = **6 logical runs**. `EpochStore.commit` writes one
`epoch-NNNN-<uuid>.pt` per committed epoch and never deletes older ones, so
storage grows linearly with committed epochs per run.

| Scenario | Per run | 6 runs |
|---|---|---|
| Worst case, 100 epochs (protocol `max_epochs`) | 4.14 GiB | **24.83 GiB** |
| Typical, ~40 epochs (early stop patience 15) | 1.65 GiB | **9.93 GiB** |
| Early stop at minimum, ~20 epochs | 0.83 GiB | 4.96 GiB |

Against **128.3 GiB available**, the worst case (24.83 GiB) consumes ~19% of
free space and leaves ~103 GiB. **Storage is sufficient.**

Residual risk: the available figure is a point-in-time measurement on a drive
that is already 87% full and shared with 6.4 GiB of historical checkpoints plus
large `reports/`, `data_cache/`, and `experiments/` trees. Free space should be
re-measured immediately before launch, and the protocol's 96-hour cumulative
active-time cap should be treated as the real bound on epoch count.

## 3. Clock and host reliability — MEASURED, UNRESOLVED

| Check | Result |
|---|---|
| `Get-Service w32time` | **Stopped**, StartType = Manual |
| `w32tm /query /status` | `The service has not been started. (0x80070426)` |
| `w32tm /query /source` | same error — **source cannot be determined** |
| `w32tm /query /peers` | same error — **no NTP peer configured/queryable** |
| Last boot | 2026-10-27 20:49:24 |
| Uptime at check | 10 h 42 m |
| Kernel-Power 41 since current boot | **0** |
| Kernel-Power 41 in retained System log | **85 events** |
| Heaviest clusters | 2026-08-05 (12), 2026-10-20 (10), 2026-09-27 (8), 2026-10-14 (7), 2026-10-07 (7), 2026-09-19 (7), 2026-08-15 (6) |
| UPS / battery enumerated | **None** — `powercfg /batteryreport` produced no `Batteries` section; `Win32_Battery` returned nothing |

### Interpretation

The Windows Time service is not merely unsynchronised — it is **not running at
all**, and its start type is Manual. There is therefore no NTP source, no
measured offset, and no drift bound. Absolute wall-clock timestamps written by
this host carry an **unquantified** offset. Only *within-session ordering* is
trustworthy.

The 85 Kernel-Power 41 events are unclean-shutdown records (crash or power
loss). The 2026-10-20 cluster (10 events) predates the current boot; **zero**
have occurred in the current 10h42m session. That is a favourable but very short
observation window — it does not establish stability over a multi-day training
campaign.

No UPS is enumerated. On a host with a documented history of unclean shutdowns
and no battery-backed power, an unattended multi-hour or multi-day run is
exposed to abrupt termination. The recovery design (atomic pointer, per-epoch
commit, writer lock) is built for exactly this, but recovery is not a substitute
for power stability.

**Clock/host status: NOT_VERIFIED.** This remains an unresolved prerequisite.

## 4. What is measured versus estimated

| Claim | Status |
|---|---|
| GPU model, VRAM, driver, CC | MEASURED |
| No competing compute process | MEASURED (2 unidentified non-compute entries noted) |
| Train/eval VRAM at 512/B4/B8 AMP | MEASURED |
| Free disk | MEASURED |
| Single checkpoint size | MEASURED (Phase-21 analogue) + ESTIMATE (param arithmetic) |
| Six-run aggregate storage | ESTIMATE ONLY |
| Wall-clock training duration | **NOT MEASURED — no estimate offered** |
| Clock offset | **NOT MEASURABLE — service stopped** |
| Host power stability over a training campaign | NOT_VERIFIED |
