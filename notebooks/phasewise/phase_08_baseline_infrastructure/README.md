# Phase 08 — Baseline Infrastructure (`phase_08_baseline_infrastructure`)

## Status: **PART 1A + PART 1B COMPLETE** — no training performed

| Part | Scope | Status | Notebook SHA |
|---|---|---|---|
| **1A** | Clean-v3 data / target / device / reproducibility foundation | COMPLETE — 21/21 gates PASS | `abeb9df9776468a657929eef344b639e030de5db2924e8124078e3b52badb4e4` |
| **1B** | Trainer / validation / resume contract + historical Phase-09 protocol reconstruction | COMPLETE — 25/25 gates PASS | `0e9d5ca578d4220f6e65f3bcc8932c15dc2573ec799897119d980f432260416b` |

- **Active development manifest:** `phase4_v3`
- **Frozen KUB size taxonomy:** `kub_size_clean_v3_v1`
- **TEST content:** never accessed (0 image reads / 0 mask reads / 0 metrics / 0 visualizations)
- **Baseline training:** **NOT performed** (Phase 09 not started)
- **Scientific performance claims:** **NONE**

## 1. Purpose

Build and validate the clean-v3 engineering foundation for Phase 09 baseline training:
the binary target contract, image-mode handling, the spatial transform contract, a
TEST-locked manifest-backed loader, and reproducibility / metric / checkpoint / AMP /
device plumbing.

Production functionality lives under `src/`; the notebook imports and audits it.

## 2. Contracts established

| Contract | Value | Verified by |
|---|---|---|
| Foreground rule | **`mask > 0`** | `src/utils/targets.binarize_mask`, unit-tested on labels 1/2/3/255 |
| Background rule | `mask == 0` | same |
| Connectivity (object metadata) | **8** | `src/metrics/object_metrics`, `kub_object_size` |
| Input channels | **1** | `KUBDataset` (`convert("L")` then `unsqueeze(0)`) |
| Spatial transform | aspect-preserving resize + centre pad, `scale = min(size/w, size/h)` | `src/data/transforms.py` |
| Image interpolation | bilinear | same |
| Mask interpolation | **nearest** | same |
| Supported target sizes | 256 / 512 / 768 / 1024 | `SegmentationTransform` |
| Canonical device | **CUDA required**, no silent CPU fallback | `src/utils/device.get_device(require_cuda=True)` |
| Metric threshold | 0.5 | `src/metrics/segmentation.binary_metrics` |
| Metric epsilon | 1e-7 | same |
| Object recall | 8-connectivity, overlap-based, `minimum_overlap_pixels=1` | `src/metrics/object_metrics` |

## 3. Population (clean-v3)

| Quantity | Value |
|---|---:|
| KUB TRAIN cases | 1978 |
| KUB VAL cases | 280 |
| TRAIN patients | 318 |
| VAL patients | 111 |
| Patient overlap | 0 |

## 4. New canonical helpers added in Part 1A

| File | Purpose |
|---|---|
| `src/utils/targets.py` | `binarize_mask()` — the single authoritative `mask > 0` conversion; `foreground_label_signature()`, `is_binary()` |
| `src/utils/device.py` | `get_device(require_cuda=True)` (raises instead of silently using CPU), `device_report()`, `make_grad_scaler()`, `make_autocast()` |
| `src/utils/config.py` | extended with the canonical experiment schema (`REQUIRED_SCIENTIFIC_FIELDS`, `validate_experiment_config()`, `config_template()`); rejects placeholder values |
| `src/utils/checkpointing.py` | additive `taxonomy_id` field |
| `src/data/kub_dataset.py` | now uses `binarize_mask` (semantically identical, verified) and exposes `acquisition_type` |

Historical behaviour is preserved: `kub_size_v1`, the metric definitions, and the
transform are unchanged.

## 5. Notable findings

- **The canonical transform supports only sizes {256, 512, 768, 1024}** — other values
  raise `ValueError`. Infrastructure must use one of these.
- **TRAIN dataset access is stochastic by design** (augmentation on every
  `__getitem__`); reproducibility is achieved by seeding, and VAL access is deterministic.
- **Bitwise GPU determinism is NOT guaranteed** and is not claimed. `cudnn.deterministic`
  is set, but `torch.use_deterministic_algorithms` is not force-enabled because some CUDA
  ops lack deterministic kernels.
- **Pre-existing test issues** in unrelated historical modules were observed and left
  untouched: `test_predicted_roi` (3 failures), `test_kub_localizer` (1 failure),
  `test_phase14_part1` (hangs). The modules involved
  (`src/inference/predicted_roi.py`, `src/data/kub_localizer_dataset.py`,
  `src/models/kub_localizer.py`) are **unmodified** by this phase.

## 6. Deliverables

- **Notebook:** `phase08_clean_v3_training_infrastructure_validation.ipynb`
- **Module:** `code/phase08_infrastructure_audit.py`
- **Driver:** `code/run_phase08_audit.py`
- **Helpers:** `code/build_phase08_notebook.py`, `code/execute_phase08_notebook.py`,
  `code/finalize_phase08_audit.py`
- **Tables:** `reports/tables/phase08_*.csv` (5 artifacts)
- **Figures:** `reports/figures/phase08_baseline_infrastructure/*.png` (loader gallery)
- **Audit:** `reports/audits/phase08_clean_v3_infrastructure_audit.json` / `.md`
- **Tests:** `tests/test_phase08_infrastructure.py`

## 7. Limitations

- Infrastructure validation only: no training, no inference, no performance claims.
- The CUDA smoke step is an engineering check (`INFRASTRUCTURE_TEST_ONLY`), not a result.
- The frozen taxonomy is applied to FULL_FIELD object metadata only; ROI is not binned.
- No scientifically material default is chosen anywhere in this phase.

## 8. Next Phase

- **Phase 08 Part 1B** — COMPLETE (see below).
- **Phase 09** — NOT STARTED. Baseline training requires separate authorization.

---

# Part 1B — Trainer / Validation / Resume Contract + Phase-09 Protocol Reconstruction

## B1. Historical Phase-09 baseline (primary provenance)

Primary source: **`checkpoints/phase9_kub_unet_baseline_seed42_512`**

| Field | Value |
|---|---|
| experiment_id | `phase9_kub_unet_baseline_seed42_512` |
| Config source | `configs/kub/unet_baseline.yaml` |
| Config SHA | `9b8392f833c6f5350ae8780b24dae2afee1221e814f4517196e931ad169bce53` |
| Checkpoint-embedded config vs YAML | **identical (42/42 fields, 0 disagreements)** |
| best.pt SHA | `a32d7fff1e019a179ef011795b6be8ee98ab548831f790a557726f32b38db8ec` |
| latest.pt SHA | `2b535401e7db95469b39a62bd6b6df51e0e298c32d00047465bc39ababd0ad61` |
| best / latest epoch | 47 / 62 (early stopped) |
| best val macro dice | 0.7455300688743591 |

### Phase-09 baseline set = **one model** (UNet)

Phase 09 is **training**; Phase 10 is **comparison**. The Phase-10 models
(`attention_unet`, `unetpp`, `deeplabv3plus`) are **out of** the Phase-09 clean-rerun scope.

## B2. Reconstructed protocol

| Field | Value |
|---|---|
| architecture | `unet` (standard 4-stage), base_channels 32 |
| channels | 1 in / 1 out |
| resolution | 512 |
| loss | `bce_dice` (bce_weight 0.5, dice_weight 0.5, epsilon 1e-6) |
| optimizer | AdamW, lr 1e-4, weight_decay 1e-4 |
| scheduler | CosineAnnealingLR(T_max=100), **stepped per epoch AFTER train+val** |
| batch size | 4 (accum 1, effective 4) |
| AMP | true |
| seed | 42 |
| max epochs | 100 |
| augmentation | hflip p=0.5, rotation ±5°, brightness ±0.1, contrast ±0.1, vflip OFF |
| checkpoint metric | val macro dice (`val_info["dice"]`), **strict >** |
| early stopping | patience 15, ties count as bad epochs |
| prediction threshold | 0.5 |
| validation aggregation | **macro = mean of per-image metrics** (micro also reported) |
| workers / pin_memory | 0 / true |
| VAL shuffle / augmentation | **false / OFF** |
| gradient clipping / accumulation | none / 1 |

## B3. Phase-10 cross-check

34 fields compared field-by-field: **0 material differences**. Two non-material
observations are recorded: (a) the monitor string differs (`val_macro_dice` vs
`val_macro_dice_true_per_image` — same metric, different name); (b) Phase-10 adds an
explicit NaN/Inf guard that raises, which Phase-09 lacks.

## B4. Contracts

- **Checkpoint selection:** best.pt written only on strict improvement; latest.pt every
  epoch; ties never overwrite best.
- **Early stopping:** checked *after* the epoch checkpoint is saved, so the stopping
  epoch is checkpointed; `scheduler.step()` runs before the stop check.
- **Resume:** restores model/optimizer/scheduler/scaler/epoch/best-metric/early-stop
  counter/history/global_step/RNG/loader-generator state; reuses the **same**
  experiment ID; re-validates manifest version **and** hashes.
- **Single-writer lock:** `src/utils/run_lock.py` — an active lock fails loudly; stale
  recovery must be requested explicitly.
- **Resume-equivalence probe:** `INFRASTRUCTURE_TEST_ONLY`; continuous vs
  save/destroy/restore runs produce **identical losses and identical parameters**.

## B5. v2 → clean-v3 diff

48 protocol fields compared: **0 scientifically material differences**. Only authorized
provenance fields change (`manifest_version`, `taxonomy_id`, `experiment_id`, source SHAs).

Candidate config: `configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml`
— status `RECONSTRUCTED_AND_READY`, **not executed**.

## B6. Pre-existing test debt (documented, not repaired)

| Test | Observed | Disposition |
|---|---|---|
| `tests/test_phase14_part1.py` | hangs | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |
| `tests/test_predicted_roi.py` | 3 failures | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |
| `tests/test_kub_localizer.py` | 1 failure | DEFER_TO_AFFECTED_CLEAN_RERUN_PHASE |

The full repository suite does **not** pass; `pytest tests/` never completes.

## B7. Test results (scoped, reported separately)

| Suite | Result |
|---|---|
| Part-1A direct (`test_phase08_infrastructure.py`) | 49/49 PASS |
| Part-1B (`test_phase08b_trainer_protocol.py`) | 45/45 PASS |
| Other scoped (Phase-07 taxonomy + manifest guard) | 36/36 PASS |
