# Phase 13 Part 1B — Pre-Training Gate Record

**Status:** **`CHECK_REQUIRED`** — training NOT started
**Model:** Gemini 3.8 Flash Medium · **Date:** 2026-09-21
**Task:** clean-v3 localizer training — pre-training gates
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`

---

Part 1B was authorized. Every pre-training gate that could be evaluated **passed**, but training
was **not started** because the R2 frozen protocol contains **no executable clean-v3
`experiment_id`**, which is an unconditional STOP condition under Part 1B §5.

**No optimizer was created. No model was constructed. No epoch ran. No checkpoint was written.
No lock was taken. TEST was not touched.**

## 1. Protocol identity — PASS

| Item | Value |
|---|---|
| R2 protocol | `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` |
| R2 SHA-256 | `ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53` (**matches expected**) |
| R2 status | `SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING` (**matches expected**) |
| R2 MD SHA | `b9bad4e583a6a46d4482ed5aa7bf30fd93c2299858183e46c61e3c7c4b18ff89` |
| R2 notebook SHA | `47ff06a11116c9d43554121a2114a96b1bb7729a290f2524ed496d992610918e` |
| R1 artifact | `SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION` — preserved, not executed |

## 2. Pre-training immutability — PASS (10 / 10 unchanged)

Part-1A notebook `68f787e1…` · R1 amendment notebook `6a08d6bd…` · R1 frozen JSON `999144bb…` ·
R2 notebook `47ff06a1…` · R2 frozen JSON `ab451e03…` · hard-Tiny `2f9828d7…` ·
global-empty `a0b332ca…` · historical `history.csv` `dcdb4369…` · historical `best.pt`
`ece906df…` · historical `latest.pt` `a1461df2…`

## 3. Population gates — PASS

| Gate | Value | Expected | Result |
|---|---|---|---|
| Manifest | `phase4_v3` | `phase4_v3` | PASS |
| Foreground rule | `mask > 0` | `mask > 0` | PASS |
| Connectivity | 8 | 8 | PASS |
| TRAIN KUB FULL_FIELD images | **770** | 770 | PASS |
| VAL KUB FULL_FIELD images | **103** | 103 | PASS |
| VAL native components | **152** | 152 | PASS |
| VAL strata | TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16 | same | PASS |
| ROI acquisitions | excluded (1208 TRAIN / 177 VAL) | excluded | PASS |
| TRAIN/VAL patient overlap | **0** | 0 | PASS |
| TEST content reads | **0** | 0 | PASS |

> **Check-method trap recorded.** Filtering `reports/tables/kub_view_type_inventory.csv` by its
> **own** `split` column yields **771 / 106** — that column carries **stale `phase4_v2` split
> labels**. The active `phase4_v3` manifest MUST be joined in on `sample_id`. Future parts must
> not mis-report the clean-v3 population.

## 4. Hard-set integrity — PASS

| Item | Value |
|---|---|
| hard-Tiny count | **15** · SHA `2f9828d77c008e7c90cd69e82d0af3568902ca9d508fdfcb9d8ccf8abd569538` |
| global-empty count | **5** · SHA `a0b332cad6bca4466ccc528cbe18cc527ef6503603ab69c55b9d699d7979f0ea` |
| Role | `PRE_FROZEN_SECONDARY_DIAGNOSTIC_COHORT` — does **not** select the checkpoint |
| Anchor | UNet++ = `HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY` (not winner / reference / final) |

## 5. BLOCKER B1 — no executable clean-v3 experiment ID (§5)

> §5: *"Use the EXACT clean-v3 experiment ID specified by the R2 frozen protocol. Do NOT invent a
> new ID. Do NOT append `_retry` / `_fix` / `_new` / `_v2` / `_v3b`. **If the R2 artifact does
> not contain an executable experiment ID: STOP CHECK_REQUIRED before training.**"*

**Finding:** the R2 frozen protocol contains **no `experiment_id` field**.

Searched: R2 JSON (all 35 top-level keys) · R1 JSON · `phase13_clean_v3_localizer_protocol_candidate.csv`
(27 protocol fields) · `phase13_v2_to_clean_v3_localizer_protocol_diff.csv` ·
`phase13_r1_to_r2_diff` table · `configs/`. The only experiment-like key in R2 is
`experiment_a_modified` (a governance flag).

Every experiment ID that exists in the repository is **historical v2**:
`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`, the
`_r512_s3_seed42{,_v2,_v3}` pilots, the `_centernetfocal_` pilots and
`_r512_s3_centernetfocal_stride4_seed42_v1`.

**Collision risk.** The historical runner (`scripts/training/train_phase13b_localizer.py`) takes
`--exp_id` or defaults to `phase13b_kub_localizer_r{resolution}_h{heatmap_resolution}_s{sigma}_seed42_v1`
— **exactly** the frozen historical experiment directory. Using it would write into an immutable
historical experiment (§2 / §32 forbid this). Deriving or inventing an ID is therefore **unsafe
as well as unauthorized**.

**Required from supervisor:** the exact clean-v3 experiment ID, or an authorized derivation rule.

## 6. BLOCKER B2 — no executable clean-v3 localizer config (§29 / §8)

§29 requires the artifact registry to include an **executable config**. No clean-v3 localizer
config exists on disk. The only localizer config, `configs/kub/phase13b_localizer.yaml`, is the
**historical v2** config (declares `phase: 13B`; the historical runner hardcodes
`manifest_version: 'phase4_v2'`).

**Required from supervisor:** authorization to create the clean-v3 executable config (and the
clean-v3-safe training/validation wrapper), or a supervisor-supplied config path + SHA.

## 7. §8 training core — satisfiable, but R2 is not self-contained

§8 permits reading the scientific core from *"the R2 frozen protocol / accepted historical
reconstruction"*, so the missing fields are **recoverable** and are **not** themselves a blocker.

- **Present in R2:** `heatmap_contract` (512×512 → 128×128, `heatmap_resolution=128`),
  `proposal_configuration`, `checkpoint_selection`, `population`, `hard_sets`,
  `coverage_contract`, `downstream_*`, `retention_contract`, `gate_governance`.
- **Absent from R2, recoverable from the Part-1A candidate:** `model_architecture`
  (KUBLocalizer compact 3-stage U-Net, base_channels 16) · `target_sigma` (0.75 in 128-space) ·
  `loss` (0.75 CenterNet focal α 0.25 γ 2.0 + 0.25 soft Dice) · `optimizer` (AdamW 1e-4 / 1e-4) ·
  `scheduler` (CosineAnnealingLR T_max 100) · `effective_batch` (4) · `seed` (42) ·
  `max_epochs` (100) · `early_stopping_patience` (15).

## 8. §17 scheduler / early-stop ordering — verified, pending the clean-v3 runner

Verified from the **executing** source `scripts/training/train_phase13b_localizer.py`
(SHA `5985b9eb2fe43018babbd88004bf7e5b99d2783dcfa78c7404591a02bdcb555a`):

1. TRAIN epoch → 2. VAL evaluate → 3. proposal config chosen from the grid (the VAL-dependent
behaviour R1/R2 removed) → 4. checkpoint score → 5. strict `>` improvement test + `bad_epochs` →
6. **`scheduler.step()`** → 7. history row appended → 8. `latest.pt` → 9. `best.pt` if improved.

The localizer ordering is *scheduler stepped per epoch after train+VAL and after the selection
bookkeeping, then history append, then `latest.pt`, then `best.pt`*. **Phase-10 segmentation
ordering was not borrowed.** This must be re-confirmed against the clean-v3 runner once it exists.

## 9. Not executed

| Item | Value |
|---|---|
| Training / optimizer created / model constructed | **0 / no / no** |
| Forward passes / optimizer steps / epochs | **0 / 0 / 0** |
| Localizer inference / proposals | **0 / 0** |
| Grid configurations evaluated | **0** |
| Predicted-region segmentation | **0** |
| Checkpoints written / history rows written | **0 / 0** |
| Run lock acquired | **no** |
| TEST content reads | **0** |
| Phase 14 started / RA-MedFiLM implemented | **no / no** |
| Historical artifacts modified | **no** |

## 10. Artifacts deliberately NOT created

| Artifact | Why |
|---|---|
| `phase13_clean_v3_localizer_training_start.{json,md}` | §19 requires it *before epoch 1*; epoch 1 was never reached |
| `phase13_clean_v3_localizer_training_completion.{json,md}` | §21 requires natural completion |
| `phase13_clean_v3_localizer_epoch_results.csv` | §22 derives it from an immutable `history.csv`; none exists |
| `phase13_clean_v3_localizer_training_review.ipynb` | §24 requires a completed run; creating one would falsely imply training occurred |
| `reports/figures/phase13_clean_v3_localizer_training/` | no data to plot |
| `phase13_part1b_training_artifact_registry.csv` | nothing trained to register |

## 11. Next action

`WAIT_FOR_SUPERVISOR_PHASE13_PART1B_EXPERIMENT_ID_AND_CONFIG_AUTHORIZATION`

**STOP.** No training. No inference. No grid search. No predicted-region segmentation.
No GO / REVISE_LOCALIZER / NO_GO. No Phase 14. No RA-MedFiLM. TEST untouched.
