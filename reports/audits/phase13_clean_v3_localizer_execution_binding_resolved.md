# PHASE-13 PART-1B-R0-R1 — EXECUTION BINDING (RESOLVED)

**Artifact type:** `NON_SCIENTIFIC_EXECUTION_BINDING_RESOLVED`
**Experiment ID:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`
**Protocol identity:** `R2 + R2A_LOSS_BINDING` (not a new variant)
**Status:** `READY_FOR_SUPERVISOR_TRAINING_REAUTHORIZATION_REVIEW`
**Gate:** `PASS_READY_FOR_SUPERVISOR_TRAINING_REAUTHORIZATION`

---

## 1. Supersession

This artifact is **additive**. The prior R0 binding audit is **preserved on disk, byte-for-byte**:

| Artifact | SHA-256 | State |
|---|---|---|
| `phase13_clean_v3_localizer_execution_binding.json` | `f066a1fb…5ad` | PRESERVED |
| `phase13_clean_v3_localizer_execution_binding.md` | `46e10e9d…4c3` | PRESERVED |
| `phase13_clean_v3_localizer_execution_binding_validation.json` | `294f568a…673` | PRESERVED |
| `phase13_clean_v3_localizer_execution_binding_validation.md` | `97530789…bab` | PRESERVED |

Prior status was `CHECK_REQUIRED` on exactly one blocker: `LOSS_OBJECTIVE_BINDING_NOT_PHYSICALLY_RESOLVED`. That blocker is now resolved by the supervisor's L1 decision, recorded additively, without erasing the CHECK_REQUIRED history.

---

## 2. Loss binding resolution (supervisor decision L1)

**Label:** `EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1`
**Role:** `PRIMARY_PHASE13_CLEAN_V3_LOCALIZER_OBJECTIVE`

| Field | Value |
|---|---|
| loss class | `src.losses.localization.CenterNetFocalLoss` |
| alpha | `2.0` |
| beta | `4.0` |
| Dice term | `NONE` |
| dice_weight | `0.0` |
| 0.75 / 0.25 weighting | ABSENT |
| alpha 0.25 | ABSENT |
| gamma 2.0 | ABSENT |

**Physical verification.** `scripts/training/train_phase13b_localizer.py`
SHA-256 `5985b9eb…555a` (matches expected) executes exactly one criterion
assignment at line 121: `CenterNetFocalLoss(alpha=2.0, beta=4.0)`. `SoftFocalDiceLoss`
is imported (lines 16–17) but **never constructed**. The historical best checkpoint
(epoch 73) descends from that executing path. Its declared
`configuration.loss = soft_focal_dice` is **declared-only and inert** — not an
executing objective.

### Dispositions (nothing deleted)

| Item | Disposition |
|---|---|
| `0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice` | `SUPERSEDED_DOCUMENTED_NOT_EXECUTING_OBJECTIVE` — provenance preserved |
| `src.losses.localization.SoftFocalDiceLoss` | `NON_PRIMARY_IMPLEMENTATION_DEFECT` — dead code, not repaired, not the primary objective |

Materiality: resolution of a prior ambiguity, **not** a material change relative to R2. R2 is silent on loss and remains unedited.

---

## 3. Collision check

`experiments/<id>` and `checkpoints/<id>` — **NO_COLLISION**. The supervisor-supplied
ID is used verbatim; no derivation, no suffix.

---

## 4. Clean-v3 VAL component source

| Property | Value |
|---|---|
| Path | `reports/tables/phase12_clean_v3_oracle_geometry.csv` |
| SHA-256 | `29326d5b…7cc0` |
| Components | 152 |
| Cases | 103 |
| Strata | TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16 |
| Coordinates | NATIVE (`bbox_min_y/max_y/min_x/max_x`, `native_H/W`) |

**Rejected:** the stale `kub_size_v1` component table (`kub_*_components_sized.csv`)
and the historical v2 manifest (known split contamination).

---

## 5. Executable binding summary

- experiment ID bound verbatim; `manifest_version = phase4_v3`; `taxonomy_id = kub_size_clean_v3_v1`
- `heatmap_resolution = 128` (explicit constructor argument, never the default 512); `input_resolution = 512`
- exactly **ONE** fixed proposal configuration: threshold 0.10 / margin 0.20 / top_k 5 / nms_iou 0.30; grid search disabled
- selection: `EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION`, tuple `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)`
- secondary diagnostics computed but structurally excluded from selection
- seed 42; `accumulation_steps = 1`; TEST reads 0

---

## 6. Training readiness

| Requirement | State |
|---|---|
| `evaluate_fixed_config_localizer` implemented | YES (no `NotImplementedError`) |
| `set_seed(42, deterministic=True)` before model construction | YES |
| TRAIN + VAL loader generators | YES (`make_generator(42)`, `seed_worker`) |
| loader generator state persisted in checkpoint | YES (previously `{}`) |
| manifest hashes populated (TRAIN + VAL) | YES (previously `{}`) |
| checkpoint metadata (experiment_id, R2/R2A/config SHAs, taxonomy, heatmap, proposal cfg, selection tuple, loss class/alpha/beta, seed, RNG) | YES |
| resume safety gates (loud failure on any mismatch) | YES |
| training start / completion audit code paths | YES (code only; artifacts not created) |
| atomic single-row-per-epoch history write | YES |

---

## 7. State

Training **NOT STARTED** · regional gate **NOT_DECIDED** · Phase 14 **NOT STARTED**
**Next action:** `WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_REAUTHORIZATION`
