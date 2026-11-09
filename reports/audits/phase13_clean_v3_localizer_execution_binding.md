# Phase 13 Part 1B-R0 — Clean-v3 Localizer Execution Binding

- **Status:** `READY_FOR_SUPERVISOR_PART1B_EXECUTION_REVIEW` (with one `CHECK_REQUIRED` blocker recorded)
- **Date:** 2026-09-21
- **Model:** Gemini 3.8 Flash Medium
- **Task:** PART1B EXECUTION BINDING REPAIR (no training)
- **Binding type:** `NON_SCIENTIFIC_EXECUTION_BINDING` — does **not** supersede R2 scientifically

## 1. Scientific protocol (unchanged)

| Item | Value |
|---|---|
| Protocol | `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` |
| SHA-256 | `ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53` |
| Status | `SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING` |
| Modified by this task | **No** |
| R3 created | **No** |

## 2. Experiment ID

```
phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3
```

Supervisor-supplied, exact, unaltered. No `_retry` / `_fix` / `_new` / `_v2` / `_v3b` / `_r1` / `_r2`.

**Collision check — NO COLLISION.** Both `experiments/<id>` and `checkpoints/<id>` are
**ABSENT**. No `history.csv`, `best.pt`, `latest.pt`, training state, or unapproved-run
evidence exists. Nothing was deleted or overwritten.

## 3. Artifacts created

| Artifact | Path | SHA-256 |
|---|---|---|
| Executable config | `configs/phase13_clean_v3/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3.yaml` | `f6057d4795848f428616aba83426db23c1e694120c85181a5152f1484f36a281` |
| Clean-v3 runner (new) | `scripts/training/train_phase13_clean_v3_localizer.py` | `ea6448d6c8f250540c1dd15c4037c28053aaa88ef313c093370421216f94e09b` |
| Safe inference wrapper (new) | `src/inference/learned_roi_clean_v3.py` | `613e03d6e4dccccce2b743974dfaccd8a29a2c0932048f0af3d37a6d2a0241bf` |
| Selection module (pure) | `src/training/clean_v3_selection.py` | `e4083bc1adda0effdd54630e018fe56b678bfcc8673c77f8ecc38340e56cce6e` |
| Unit tests | `tests/test_phase13_clean_v3_selection.py` | `14fae0a1a65c64a98b1cd69dedcceeca62e8e9bbbaac0a520f6937cccd67c7f8` |
| Config diff table | `reports/tables/phase13_clean_v3_executable_config_binding.csv` | — |

**Untouched (immutable):** `scripts/training/train_phase13b_localizer.py`,
`src/inference/learned_roi.py`, the R2/R1 protocols, the Part-1A notebook, and all
historical experiment/checkpoint artifacts. All eight section-19 hashes re-verified exact.

## 4. Binding summary

| Bound field | Value | Role |
|---|---|---|
| manifest_version | `phase4_v3` | R2_FROZEN |
| TRAIN population | 770 cases / 1161 components | R2_FROZEN |
| VAL population | 103 cases / 152 components | R2_FROZEN |
| VAL strata | TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16 | R2_FROZEN |
| TRAIN/VAL patient overlap | 0 | R2_FROZEN |
| Heatmap | 512×512 → 128×128, `heatmap_resolution=128` **explicit** | R2_FROZEN |
| Proposal config | 0.10 / 0.20 / 5 / 0.30 | R2_FROZEN |
| Primary proposal configs | **1** | R2_FROZEN |
| Primary grid search | **DISABLED** | R2_FROZEN |
| Checkpoint tuple | `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` | R2_FROZEN |
| Comparison | strict lexicographic `>`; ties = BAD_EPOCH; patience 15 | R2_FROZEN |
| Hard-Tiny | 15, SHA `2f9828d7…` | SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM |
| Global-empty | 5, SHA `a0b332ca…` | SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM |
| TEST allowed | `false` | R2_FROZEN |

`phase4_v3` population derivation: joining `manifests/phase4_v3/{train,val}.csv`
into the v2-derived FULL_FIELD sample tables removes exactly **1 TRAIN** residual
(771→770) and **3 VAL** residuals (106→103), reproducing R2 exactly.

### Training order (no best-of-20-grid stage in clean-v3)

`TRAIN → VAL → fixed proposal metrics (one config) → 4-term score → strict improvement /
bad_epochs → scheduler.step() → history row → latest.pt → best.pt if improved → stop decision`

## 5. Blocking discrepancy — `CHECK_REQUIRED`

**`LOSS_OBJECTIVE_BINDING_NOT_PHYSICALLY_RESOLVED`**

Section 5 requires the executable config to bind the loss and forbids inventing a value.
The frozen sources genuinely disagree on this scientifically material parameter:

- **R2** — **silent**: contains no loss / optimizer / scheduler field.
- **Accepted Part-1A candidate table** — `0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice`.
- **Historical EXECUTING code** (`train_phase13b_localizer.py` line 121) — `CenterNetFocalLoss(alpha=2.0, beta=4.0)`, **no Dice term**, **alpha=2.0 not 0.25**. `SoftFocalDiceLoss` is imported but never used.

An additional defect: the composite option maps to `SoftFocalDiceLoss`, whose focal term is
overwritten by dead code at line 20 — binding it would bind an objective that is not the one
it computes.

R0 does **not** choose silently. The config records this block explicitly, currently
recording the historical executing objective (Option L1) as the flagged placeholder.
Supervisor options: **L1** bind `CenterNetFocalLoss(2.0, 4.0)`; **L2** bind the Part-1A
composite (requires specifying the variant precisely / repairing the dead-code defect);
**L3** supply an exact module + parameters + SHA.

> Also noted: the config file already on disk from the stopped Part-1B attempt bound
> `SoftFocalDiceLoss` while describing itself as "CenterNet focal" — a mislabelled silent
> resolution of exactly this ambiguity. R0 replaced it with an explicit, flagged binding.

## 6. Governance (R0)

training **0** · model constructions **0** · forward passes **0** · optimizer creations **0** ·
localizer inference **0** · proposals **0** · grid configs evaluated **0** · run lock **0** ·
TEST content reads **0** · Phase 14 **not started**.
Scientifically material changes **0** · unauthorized material differences **0**.

## 7. Next action

`WAIT_FOR_SUPERVISOR_PHASE13_PART1B_EXECUTION_BINDING_REVIEW` — stopping, per instruction.
