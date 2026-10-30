# MEMORY — Operational Continuity Handoff

**Purpose:** Compact, operational "resume work safely in 5 minutes" page: current strategy,
startup checklist, environment, frozen values, key paths, common misconceptions, traps, and
a machine-readable `current_state` YAML block. See [PRD.md](PRD.md),
[ARCHITECTURE.md](ARCHITECTURE.md), [RULES.md](RULES.md), [DESIGN.md](DESIGN.md),
[TASKS.md](TASKS.md) for the full treatments.

**Last verified:** 2026-09-21
**Strategy revision:** **SR-1** — status **ADOPTED**

**Canonical source paths:** `reports/audits/antigravity_current_state.json` ·
`manifests/manifest_registry.*` · `reports/audits/kub_size_clean_v3_v1_thresholds.json` ·
`configs/phase09_clean_v3/`, `configs/phase10_clean_v3/` · `src/utils/*` ·
`reports/audits/phase11_clean_v3_failure_analysis_audit.*`

---

## 0. CURRENT STRATEGY (read this first)

- **KUB is the REGIONAL-MECHANISM DISCOVERY AND VALIDATION LABORATORY** — not a standalone
  final product. Its regional phases exist to **validate and freeze a reusable regional
  mechanism** for later integration into the final multi-domain FiLM architecture,
  **conditional on evidence**.
- **Final intended system: `RA-MedFiLM-Seg++`** — Regional-Aware · Scale-Aware ·
  Multi-Domain · FiLM-Conditioned · **Binary** Semantic Segmentation.
- **Status: `PROPOSED_NOT_IMPLEMENTED`** — not implemented, not trained, not validated,
  not frozen.
- **Phase 12 oracle mechanism: `SUPPORTED_DESCRIPTIVE_EVIDENCE`** (clean-v3 KUB FULL_FIELD
  103 cases / 152 native components, all four models) — descriptive only.
- **Phase 13 progression: `SCIENTIFICALLY_JUSTIFIED`** — testing GT-free localization is
  justified; this does **not** mean the gate is GO or that predicted localization will work.
- **Regional mechanism: NOT PROMOTED.**
- **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`: REQUIRED · NOT_DECIDED** (decided only after
  Phase 13).
- **Current position: Phase 12 COMPLETE / PASS · Phase 13 Parts 1A / 1A-R1 / 1A-R2 / 1B-R0 /
  1B-R0-R1 COMPLETE · current executable protocol identity `R2 + R2A_LOSS_BINDING` · Phase 13
  Part 1B execution binding RESOLVED and `PASS` (STILL NO training).**
- **Part 1B-R0 resolved both prior blockers and left ONE open item.** (1) The supervisor supplied
  the exact clean-v3 `experiment_id`
  `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3` — collision check
  `NO_COLLISION`. (2) An executable clean-v3 config, a **new** clean-v3 runner
  (`scripts/training/train_phase13_clean_v3_localizer.py`), a clean-v3-safe inference wrapper
  (`src/inference/learned_roi_clean_v3.py`) and a pure selection module
  (`src/training/clean_v3_selection.py`) now exist. The historical runner and the defective
  historical helper are **unchanged**.
- **Loss binding RESOLVED by Part 1B-R0-R1 (supervisor decision L1).** The primary clean-v3
  localizer objective is `src.losses.localization.CenterNetFocalLoss` with **`alpha=2.0`,
  `beta=4.0`** and **NO Dice term** — label `EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1`, role
  `PRIMARY_PHASE13_CLEAN_V3_LOCALIZER_OBJECTIVE`. There is no `0.75/0.25` weighting, no
  `alpha 0.25` and no `gamma 2.0` on the executable path. Amendment (additive, R2 **not** edited):
  `reports/audits/phase13_clean_v3_localizer_loss_binding_r2a.json` `f3aececf…`. Resulting
  identity `R2 + R2A_LOSS_BINDING` — **not a new variant**. Dispositions: the composite contract
  string is `SUPERSEDED_DOCUMENTED_NOT_EXECUTING_OBJECTIVE` (provenance retained, rows not
  deleted); `SoftFocalDiceLoss` stays `NON_PRIMARY_IMPLEMENTATION_DEFECT` (dead code at
  `src/losses/localization.py` line 20, unrepaired). Physically re-verified: historical runner
  `5985b9eb…555a` executes exactly one criterion at line 121 =
  `CenterNetFocalLoss(alpha=2.0, beta=4.0)`; the historical best checkpoint (epoch 73) descends
  from that executing path, and its declared `configuration.loss = soft_focal_dice` is
  **declared-only / inert**.
- **Part 1B-R0-R1 made the runner genuinely training-ready.** `evaluate_fixed_config_localizer`
  is fully implemented (no `NotImplementedError` / TODO / dummy / fabricated metrics on the
  executable path); `set_seed(42, deterministic=True)` runs before model construction; TRAIN and
  VAL loaders get `make_generator(42)` + `seed_worker`; loader generator state is persisted (was
  `{}`) and restored before the resumed epoch sequence; authoritative `phase4_v3` TRAIN + VAL
  manifest SHAs are populated (was `{}`); checkpoints carry experiment_id, R2/R2A/config SHAs,
  taxonomy, `heatmap_resolution=128`, proposal config, selection tuple + term names, loss
  class/alpha/beta, seed and RNG state; resume safety gates fail **loudly** on any mismatch and
  refuse to overwrite existing state without `--resume`; training start/completion audit code
  paths exist (code only — artifacts NOT created now); history writes are canonical and atomic
  (one completed epoch = one row). Static/unit gates **A–P all PASS (34/34 tests, 0 failures)**.
  **Resolved artifacts:** `phase13_clean_v3_localizer_execution_binding_resolved.{json,md}` and
  `..._execution_binding_validation_resolved.{json,md}`. Prior `CHECK_REQUIRED` artifacts are
  **preserved** (binding `f066a1fb…`/`46e10e9d…`, validation `294f568a…`/`97530789…`).
- **Binding CSV defect repaired:** `reports/tables/phase13_clean_v3_executable_config_binding.csv`
  had an unquoted comma (`ParserError: Expected 6 fields in line 66, saw 7`); regenerated with a
  real CSV writer so `pandas.read_csv` succeeds with no special options (130 rows × 6 cols), with
  all 9 prior `CHECK_REQUIRED` rows preserved as `SUPERSEDED_PRIOR_CHECK_REQUIRED_AUDIT`.
- **Clean-v3 VAL GT/component source (reusable fact):** use
  `reports/tables/phase12_clean_v3_oracle_geometry.csv` (`29326d5b…7cc0`) — 152 components /
  103 cases, native bbox, strata TINY 72 / SMALL 28 / MEDIUM 36 / LARGE 16. The stale
  `kub_size_v1` table (`kub_*_components_sized.csv`) and the historical v2 manifest are
  **rejected** for clean-v3 VAL metrics.
- **phase4_v3 population join (reusable fact):** joining `manifests/phase4_v3/{train,val}.csv`
  into the v2-derived FULL_FIELD sample tables removes exactly **1 TRAIN** residual (771→770) and
  **3 VAL** residuals (106→103), reproducing R2's 770/1161 · 103/152.
- **Primary clean-v3 checkpoint selection = the 4-term EXECUTING historical tuple**
  `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` at the fixed proposal
  configuration. The R1 8-term tuple is `SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION` (provenance
  preserved). **Part 1B must use `phase13_clean_v3_localizer_protocol_frozen_r2.json`.**
- **Phase-13 historical localizer ran under `phase4_v2`** (VAL FULL_FIELD 106 / 156). Its frozen
  metrics are **not** clean-v3 numbers. Clean-v3 FULL_FIELD is **TRAIN 770 / 1161 · VAL 103 / 152**.
- **Frozen clean-v3 proposal config: `0.10 / 0.20 / 5 / 0.30`.** The per-epoch 20-config grid
  search is **DISABLED** for the clean-v3 primary experiment (`DEFERRED_SECONDARY_SENSITIVITY_ONLY`).
- **Frozen clean-v3 hard sets (re-derived, not reused):** hard-Tiny **15** · global-empty **5**
  (historical v2 was 16 / 7 — counts need not match). Role:
  **`SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM`** — they do **not** select the primary checkpoint.

## 1. Startup checklist (do this before any work)

1. Confirm environment: `D:\Softfors\jup\.venv\Scripts\python.exe`, kernel `jup-venv`,
   GPU NVIDIA GeForce RTX 3060 Ti, PyTorch 2.6.0+cu124, CUDA 12.4.
2. Confirm active manifest: `validate_manifest_version_strict('phase4_v3')`.
3. Confirm taxonomy: `kub_size_clean_v3_v1` (load from the freeze artifact; never hardcode).
4. Confirm current phase from `reports/audits/antigravity_current_state.json` — **not** from
   `PROJECT_CONTEXT.md` / `ANTIGRAVITY_WORKFLOW.md` (both stale; see §6).
5. Confirm TEST lock: `test_content_reads: 0`; never construct a TEST dataset.
6. If training: acquire `src/utils/run_lock.py` for the experiment ID first.
7. Stop and return `CHECK_REQUIRED` before any scientific parameter change.
8. Re-read §0 — do **not** implement RA-MedFiLM or promote the regional mechanism.

## 2. Environment

| Item | Value |
|---|---|
| Project root | `D:\Softfors\jup` |
| Python | `D:\Softfors\jup\.venv\Scripts\python.exe` |
| Jupyter kernel | `jup-venv` |
| GPU | NVIDIA GeForce RTX 3060 Ti |
| PyTorch / CUDA | 2.6.0+cu124 / 12.4 |
| Raw data | `D:\Softfors\omni_seg\data_raw` |
| External test (locked) | `D:\Softfors\final\external_test_ds` |
| Experiment A (never modify) | `D:\Softfors\final\medfilm_seg_kub_extension` |

## 3. Common misconceptions (each cost real rework)

| ❌ Misconception | ✅ Reality |
|---|---|
| "We are building a separate final KUB regional model" | KUB regional phases are intended to **validate and freeze a reusable regional mechanism** for later integration into the final multi-domain FiLM architecture, **conditional on evidence**. |
| "The final RA-MedFiLM design is already frozen" | It is the **official direction** but remains **`PROPOSED_NOT_IMPLEMENTED`** until the evidence and architecture-freeze phases. |
| "Kidney/Bladder/Ureteric are future segmentation classes" | They remain **metadata** (`REPORTING_ONLY`) unless genuine pixel-level class masks exist. |
| "VAL has 280 rows" | Global VAL has **808**; **KUB** VAL has **280**. Always filter `dataset == "KUB"`. |
| "mask == 1 is foreground" | Foreground is **`mask > 0`**; labels 1/2/3/255 are all foreground. Never `mask == 1`. |
| "UNet++ is the winner" | **No winner is declared.** All four models have clean-v3 runs; the final comparison is COMPLETE but single-seed with no significance testing. |
| "UNet++ is the Phase-12 reference model" | **No Phase-12 reference model was selected.** All four frozen baseline architectures were used in Phase 12. UNet++ remains historical replication provenance only. |
| "The Phase-13 Stage-4D numbers (53/73, 100/156) are clean-v3 results" | **No.** The historical localizer ran under **`phase4_v2`** (VAL FULL_FIELD **106 / 156**). Clean-v3 FULL_FIELD is **103 / 152**. Never compare them as if the splits matched. |
| "The frozen 16 Tiny / 7 global-empty hard sets can be reused in clean-v3" | **No.** They were derived on the v2 population. Clean-v3 **must re-derive** them from the clean-v3 global baselines using the same definitional rule. |
| "`learned_roi.predict_localizer` reproduces the Stage-4D heatmap" | **No — verified latent defect.** It builds `KUBLocalizer` **without** `heatmap_resolution=128`, silently dropping the parameter-free downsample and returning a 512-space heatmap. |
| "Phase 14's regional refiner result measured predicted-proposal refinement" | **No.** The refiner was **trained** on GT-derived + perturbed + background-negative crops (A3: 1162+2324+1542 = 5028/epoch) but **evaluated** on Stage-4D predicted proposals — a verified `HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH`. |
| "The historical checkpoint score included the hard-Tiny and global-empty terms" | **No.** The **executing** code (`scripts/training/train_phase13b_localizer.py:164`) used a **4-term** tuple `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)`. R1 briefly froze an 8-term extension; **R2 corrected the primary rule back to the executing 4-term tuple**. |
| "The 8-term checkpoint tuple is the frozen clean-v3 rule" | **No — superseded by R2.** The 8-term tuple is `SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION`; the **4-term executing historical tuple** is primary. |
| "The hard sets select the clean-v3 checkpoint" | **No.** They are `SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM` — computed and logged, excluded from primary selection. |
| "Part 1B should use the R1 frozen protocol JSON" | **No.** Use `phase13_clean_v3_localizer_protocol_frozen_r2.json`. The R1 JSON is `SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION`, preserved for provenance only. |
| "The clean-v3 localizer may search the 20-config proposal grid" | **No.** The primary clean-v3 experiment uses the **frozen** `0.10 / 0.20 / 5 / 0.30`; the grid is `DEFERRED_SECONDARY_SENSITIVITY_ONLY` and needs separate authorization after the primary result is frozen. |
| "The historical hard-set IDs (16 / 7) can be carried into clean-v3" | **No.** They were re-derived on clean-v3 (**15** hard-Tiny components · **5** global-empty images) using the same historical definition, anchored on the clean-v3 UNet++ global baseline. |
| "UNet++ is the Phase-13 reference model" | **No.** UNet++ is used **only** as the `HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY` to reproduce the historical hard-set definition. All four models remain the downstream scope. |
| "The Stage-4D design audit's `clean_v3_results` are clean-v3 metrics" | **No.** Denominator 156 = `phase4_v2`. Disposition: `STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT` → `HISTORICAL_v2_PROVENANCE_ONLY`. |
| "I can copy UNet++ hyperparameters to DeepLabV3+" | **No.** Architecture-specific params must come from that model's own historical provenance. |
| "Attention U-Net precision/recall are N/A" | They are **HISTORY_NATIVE**: 0.7729140812402236 / 0.7922248481868364. |
| "Gallery mean = VAL score" | No — gallery is `DETERMINISTIC_GALLERY_SUBSET_ONLY` (16 cases); authoritative metrics are the 280-case values. |
| "Phase 10/11 are still running" | Both are **COMPLETE**. **Phase 12 is COMPLETE / PASS.** Phase 13 **Parts 1A / 1A-R1 / 1A-R2 are COMPLETE** (protocol/definition only, protocol `SUPERVISOR_FROZEN_R2`); Part 1B is **ELIGIBLE / NOT AUTHORIZED**. |
| "The regional mechanism is approved" | **Not promoted.** It must pass `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`. |
| "PROJECT_CONTEXT.md is current" | It is **stale** (says no clean rerun executed, Phase 13B). Trust the audits. |
| "CPU fallback is fine" | `get_device(require_cuda=True)` **must** fail loudly. Never silently use CPU. |
| "Ties are improvements" | Improvement is **strict `>`**; ties count as **bad epochs**. |
| "Passing binary masks to `binary_metrics` is fine" | No — it applies **sigmoid internally**; binary 0/1 becomes all-foreground and every model scores identically. Pass logits. |

## 4. Frozen values (do not recompute or edit)

**Manifests — `phase4_v3` (active):** TRAIN 5832 · VAL 808 · TEST 1683 · QUARANTINED 118
· KUB TRAIN **1978** · KUB VAL **280** · KUB TEST 558 · KUB QUAR 4 · patient overlap **0**.

**Taxonomy `kub_size_clean_v3_v1`:** Q25 `0.0001497998649691358` ·
Q50 `0.0003401438395182292` · Q75 `0.0008279682677469136` · connectivity 8 ·
`component_ratio` · TINY ≤ Q25 · SMALL ≤ Q50 · MEDIUM ≤ Q75 · LARGE > Q75 ·
FULL_FIELD-only calibration (ROI = `ROI_NOT_PRIMARY_BINNED`).

**Protocol:** 512 · 1→1 channel · BCE+Dice 0.5/0.5 eps 1e-6 · AdamW 1e-4/1e-4 ·
CosineAnnealingLR T_max 100 · batch 4 (accum 1, eff 4) · AMP · seed 42 · 100 epochs ·
patience 15 · monitor VAL macro Dice · strict `>` · threshold 0.5 ·
aug (hflip 0.5, rot ±5°, bright ±0.1, contrast ±0.1, vflip false) · base_channels 32.

**Canonical gallery:** 16 KUB VAL cases ·
SHA `10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db` ·
Bladder 10 / Kidney 4 / Ureteric 2 · ROI 8 / FULL_FIELD 8 · reused by all four models.

**Verified clean-v3 VAL (no ranking — all single-seed, descriptive):**

| Model | Best ep | VAL Dice | IoU | Precision | Recall | Epochs |
|---|---|---|---|---|---|---|
| UNet | 44 | 0.7406133413314819 | 0.6253822445869446 | 0.7707186937332153 | 0.7839437127113342 | 59 |
| Attention U-Net | 54 | 0.7525129853960107 | 0.6349387691368995 | 0.7729140812402236 | 0.7922248481868364 | 69 |
| UNet++ | 70 | 0.7641595156062713 | 0.6525442690586191 | 0.7996825971468945 | 0.7912384169561990 | 85 |
| DeepLabV3+ | 52 | 0.7509140344161673 | 0.6460492792430865 | 0.7943328495850855 | 0.7822983241135557 | 67 |

**Phase-11 verified failure evidence:** per-model clean Dice Q10 —
UNet `0.4693939398443986` · Attention U-Net `0.5360238052845407` ·
UNet++ `0.5618055568014564` · DeepLabV3+ `0.3784289703007593`.
`ALL_FOUR_LOW` **12/280**; `low_model_count` `{0:233,1:17,2:7,3:11,4:12}`.
UNet++ anchor: HD95 Q90(valid) `85.24095485204775` (274 valid / 6 invalid); FP Q90 `5.0`
(31 high-FP). Empty predictions 8/3/6/11. Object recall 0.896341/0.923780/0.914634/0.881098.
Multi-component cases **49** (30/16/3, 33/12/4, 33/11/5, 27/16/6 complete/partial/miss).
Regime gap mean Dice **0.2276**. Hard cohort **16** (no underfilled), SHA
`72f16916e9a9e86b047514842634ab7b73c245d131d5fbbd37db9fff171e3c46`.

**Complete epoch tables (all four):** `phase10_final_epoch_results_{unet,attention_unet,unetpp,deeplabv3plus}.csv`
→ 59 / 69 / 85 / 67 rows. Combined `phase10_final_all_models_epoch_results_long.csv`
= **280 MODEL-EPOCH rows** (NOT the 280 VAL cases).

**Improvement events (canonical, from history):** UNet 21 · Attention U-Net 24 · UNet++ 21 ·
DeepLabV3+ 23. (A pasted Part-1C note said 24 for DeepLabV3+ — `SUPERSEDED_REPORTING_NOTE_ONLY`.)

**Phase-13 historical localizer (frozen, `phase4_v2` — do not edit):**
`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1` · best epoch **73 / 88** ·
best.pt `ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace` ·
latest.pt `a1461df2…` · history.csv `dcdb4369…` · selected proposal config
**0.10 / 0.20 / 5 / 0.30** · Tiny recall90 `53/73 = 0.726027397260274` ·
overall recall90 `100/156 = 0.6410256410256411` · hard Tiny `7/16` · global-empty `3/7` ·
mean ROI area `0.005898906179948982` · proposals/image `4.660377358490566` · params 482,449 ·
loss `0.75 CenterNet focal (α 0.25, γ 2.0) + 0.25 soft Dice` · 128×128 output heatmap ·
sigma `0.75` (≡ 3.0 in 512-space). Phase-14 frozen entry gate **NOT PASSED**
(A 7/16 < 8, B 3/7 < 4, C 0.726027 < 0.85, D 0.641026 < 0.85).

**Phase-13 clean-v3 protocol (R2 SUPERVISOR-FROZEN, not executed):** population TRAIN
**770 / 1161** · VAL **103 / 152** (Tiny 72 / Small 28 / Medium 36 / Large 16) · ROI excluded ·
hard sets re-derived (**15** hard-Tiny components `2f9828d7…` · **5** global-empty images
`a0b332ca…`) as `SECONDARY_DIAGNOSTIC_NOT_SELECTION_TERM` · proposal config
**`0.10 / 0.20 / 5 / 0.30`** (grid search **DISABLED**) · heatmap **512 → 128**,
`heatmap_resolution=128` always explicit · **primary checkpoint score = the 4-term executing
historical tuple** `(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)` at the
fixed config (the R1 8-term extension is `SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION`) ·
predicted-region primary `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` at margin **0.20** · retention
label `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION`. **Current frozen artifact
`reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` `ab451e03…`** (the R1
`…frozen.json` `999144bb…` is preserved as provenance and is
`SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION`).

**Paired VAL:** `phase10_clean_v3_paired_val_case_metrics.csv` — 280 cases × 4 models.

**Manifests — `phase4_v2` (historical, do not modify):** TRAIN 5913 · VAL 845 · TEST 1683 ·
KUB TRAIN 1979 / VAL 283 / TEST 558 · `kub_size_v1` immutable ·
leakage `KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY`.
TEST is byte-identical v2↔v3: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`.

## 5. Key paths

| Purpose | Path |
|---|---|
| Live state | `reports/audits/antigravity_current_state.json` |
| Manifest registry | `manifests/manifest_registry.md` / `.json` |
| Taxonomy artifact | `reports/audits/kub_size_clean_v3_v1_thresholds.json` |
| Clean configs | `configs/phase09_clean_v3/`, `configs/phase10_clean_v3/` |
| Targets contract | `src/utils/targets.py` (`binarize_mask`) |
| Device contract | `src/utils/device.py` (`get_device(require_cuda=True)`) |
| Run lock | `src/utils/run_lock.py` · Test lock `src/utils/test_lock.py` |
| Manifest guard | `src/utils/manifest_guard.py` |
| Metrics | `src/metrics/segmentation.py` (`binary_metrics`, `aggregate_*`, `hd95`) |
| Object metrics | `src/metrics/object_metrics.py` (8-conn, ≥1 px) |
| Dataset | `src/data/kub_dataset.py` (`KUBDataset`, TEST blocked) |
| Phase 10 reviewers | `notebooks/phasewise/phase_10_baseline_comparison/` |
| Phase 11 notebooks | `notebooks/phasewise/phase_11_failure_analysis/` |
| Phase 12 notebooks | `notebooks/phasewise/phase_12_oracle_roi/` |
| Phase-12 mechanism conclusion | `reports/audits/phase12_clean_v3_oracle_mechanism_conclusion.json` |
| Phase-12 mechanism conclusion (md) | `reports/audits/phase12_clean_v3_oracle_mechanism_conclusion.md` |
| Regional-integration gate state | `reports/tables/regional_integration_gate_state_after_phase12.csv` |
| Phase-11 bridge evidence | `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv` |
| Phase-13 Part-1A notebook | `notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_localizer_protocol_freeze.ipynb` |
| Phase-13 Part-1A support code | `notebooks/phasewise/phase_13_predicted_roi_localization/code/phase13_localizer_protocol.py` |
| Phase-13 reconstruction audit | `reports/audits/phase13_historical_localizer_protocol_reconstruction.json` |
| Phase-13 clean-v3 candidate audit | `reports/audits/phase13_clean_v3_localizer_protocol_candidate.json` |
| Phase-13 protocol matrix | `reports/tables/phase13_historical_localizer_protocol_matrix.csv` |
| Phase-13 clean-v3 population spec | `reports/tables/phase13_clean_v3_training_population_spec.csv` |
| Phase-13 retention contract | `reports/tables/phase13_oracle_retention_metric_contract.csv` |
| Phase-13 population census cache | `reports/audits/phase13_population_census_cache.json` |
| Phase-13 FROZEN protocol (R1, superseded) | `reports/audits/phase13_clean_v3_localizer_protocol_frozen.json` |
| **Phase-13 FROZEN protocol (R2, CURRENT)** | `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` |
| Phase-13 R2 notebook | `notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_localizer_checkpoint_selection_r2.ipynb` |
| Phase-13 R1→R2 diff | `reports/tables/phase13_r1_to_r2_protocol_diff.csv` |
| Phase-13 R1 amendment notebook | `notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_localizer_supervisor_freeze_amendment.ipynb` |
| Phase-13 clean-v3 hard-Tiny set | `reports/tables/phase13_clean_v3_hard_tiny_replication_set.csv` |
| Phase-13 clean-v3 global-empty set | `reports/tables/phase13_clean_v3_global_empty_replication_set.csv` |

## 6. Traps

- **Stale top-level docs.** `PROJECT_CONTEXT.md`, `PROJECT_MASTER_PLAN.md`, and
  `ANTIGRAVITY_WORKFLOW.md` all lag actual state. Treat `reports/audits/*` as authoritative.
  Full list in [PRD.md](PRD.md) §10.
- **Cross-domain VAL leak.** Selecting a gallery from the unfiltered 808-row VAL silently
  mixes ISIC/BUSI/Kvasir. Always hard-assert `dataset == "KUB"` and 280 rows.
- **`binary_metrics` takes logits.** It applies `sigmoid` internally. Passing binary 0/1
  makes every pixel "foreground" (`sigmoid(0)=0.5 >= 0.5`) and yields *identical* scores
  across models. Pass logits, or compute dice/IoU/precision/recall directly with
  `epsilon = 1e-7`.
- **`groupby` sorts keys.** Never assign per-model values positionally onto a grouped frame
  (alphabetical order ≠ explicit model order). Build a name-keyed dict and `.map()`, and
  assert invariants like `q90 <= max`.
- **Checkpoint key drift.** Historical checkpoints store `best_validation_score`; clean-v3
  runners store **`best_metric`**, with resolution/threshold/model name inside
  `configuration`. Resolve both.
- **History column drift.** Phase 09 clean-v3 uses `val_macro_dice`; Phase 10 clean-v3 runs
  use `val_dice`.
- **Resize math.** Reproducing validation metrics requires `max(1, round(extent*scale))`,
  **not** `int(...)`; `int()` produced ~1e-3 Dice errors.
- **CSV tensor casting.** Metrics returned as CUDA tensors must be `.float()`-cast before
  `np.mean`.
- **`matplotlib.use('Agg')` + `plt.show()`** produces no inline notebook output — use
  `%matplotlib inline` and `display(fig)`.
- **Regime mixing.** Don't apply FULL_FIELD-calibrated size rules to ROI crops.
- **Never reuse/overwrite** a historical experiment directory; clean runs get `*_clean_v3`.
- **State-file vs six-doc scope.** The six `docs/*.md` files are the continuity pack; a
  separate live JSON may drift. Record mismatches in this file's `known_conflicts` rather
  than silently editing.

## 7. Machine-readable state

```yaml
current_state:
  last_verified: "2026-09-21"
  strategy_revision:
    id: SR-1
    status: ADOPTED
    name: "Regional-Aware Multi-Domain FiLM"
  project_root: "D:\\Softfors\\jup"
  python_executable: "D:\\Softfors\\jup\\.venv\\Scripts\\python.exe"
  kernel: "jup-venv"
  gpu: "NVIDIA GeForce RTX 3060 Ti"
  pytorch: "2.6.0+cu124"
  cuda: "12.4"

  final_architecture_direction:
    name: "RA-MedFiLM-Seg++"
    status: PROPOSED_NOT_IMPLEMENTED
    multi_domain: true
    region_aware: true
    scale_aware: true
    film_conditioned: true
    binary_segmentation: true

  regional_integration_gate:
    name: REGIONAL_INTEGRATION_GATE_AFTER_PHASE13
    after_phase: 13
    required: true
    status: NOT_DECIDED
    outcomes: [GO, REVISE_LOCALIZER, NO_GO]
    numeric_thresholds_defined: false

  manifest:
    active_version: "phase4_v3"
    historical_version: "phase4_v2"
    v3_status: "CANONICAL_ACTIVE_DEVELOPMENT"
    v2_status: "HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT"
    v3_counts: {TRAIN: 5832, VAL: 808, TEST: 1683, QUARANTINED: 118, TOTAL: 8441}
    kub_v3_counts: {TRAIN: 1978, VAL: 280, TEST: 558, QUARANTINED: 4}
    v2_counts: {TRAIN: 5913, VAL: 845, TEST: 1683}
    kub_v2_counts: {TRAIN: 1979, VAL: 283, TEST: 558}
    train_val_patient_overlap: 0
    test_locked_until: "Phase 39"
    test_locked_until_phase: 39
    test_sha256: "9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727"
    test_content_reads: 0

  taxonomy:
    active_id: "kub_size_clean_v3_v1"
    status: "FROZEN"
    historical_id: "kub_size_v1"
    historical_status: "IMMUTABLE"
    Q25: 0.0001497998649691358
    Q50: 0.0003401438395182292
    Q75: 0.0008279682677469136
    foreground_rule: "mask > 0"
    connectivity: 8

  protocol:
    resolution: 512
    input_channels: 1
    output_channels: 1
    base_channels: 32
    loss: "bce_dice"
    loss_weights: [0.5, 0.5]
    dice_epsilon: 1.0e-6
    optimizer: "AdamW"
    learning_rate: 1.0e-4
    weight_decay: 1.0e-4
    scheduler: "CosineAnnealingLR"
    scheduler_T_max: 100
    batch_size: 4
    gradient_accumulation_steps: 1
    effective_batch_size: 4
    amp: true
    seed: 42
    max_epochs: 100
    early_stopping_patience: 15
    improvement_rule: "strict >"
    checkpoint_metric: "val_macro_dice"
    prediction_threshold: 0.5
    val_aggregation: "macro unweighted per-image"
    deep_supervision: false

  phase:
    current: 13
    current_part: "1A-R2"
    status: "PART_1A_COMPLETE"
    phase10_complete: true
    phase11_status: "COMPLETE"
    phase12_status: "COMPLETE"
    phase12_part1a: "COMPLETE"
    phase12_part1b: "COMPLETE"
    phase12_part1c: "COMPLETE"
    phase12_part1d: "COMPLETE"
    oracle_mechanism_value: "SUPPORTED_DESCRIPTIVE_EVIDENCE"
    phase13_eligible: true
    phase13_authorized: true
    phase13_authorized_scope: "PART_1A_1A_R1_AND_1A_R2_PROTOCOL_AND_DEFINITION_ONLY"
    phase13_started: true
    phase13_clean_v3_status: "PART_1A_COMPLETE"
    phase13_historical_status: "EXECUTED_AND_COMPLETE"
    phase13_part1a: "COMPLETE"
    phase13_part1a_notebook_sha: "68f787e1f70fcf706442b342e62cc615eeb347653e753149987becf793ac2bd0"
    phase13_part1a_r1: "COMPLETE"
    phase13_part1a_r1_notebook_sha: "6a08d6bd43e173f4b8b646d130fdabca0e95f3466b5caf0a91323cc52d34a622"
    phase13_part1a_r2: "COMPLETE"
    phase13_part1a_r2_notebook_sha: "47ff06a11116c9d43554121a2114a96b1bb7729a290f2524ed496d992610918e"
    phase13_protocol_status: "R2_PLUS_R2A_LOSS_BINDING"
    phase13_protocol_base_status: "SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING"
    phase13_protocol_frozen_r2_sha: "ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53"
    phase13_protocol_loss_amendment: "R2A_LOSS_BINDING"
    phase13_protocol_loss_amendment_path: "reports/audits/phase13_clean_v3_localizer_loss_binding_r2a.json"
    phase13_protocol_loss_amendment_sha: "f3aececfbe683fa7c60ea758b7b7d6446e3cc6584e86e8faa2c7eb4f14029667"
    phase13_protocol_r1_status_for_execution: "SUPERSEDED_BY_SUPERVISOR_R2_CHECKPOINT_SELECTION_CORRECTION"
    phase13_protocol_r1_frozen_sha: "999144bbad4af4e1d2dc006279aef1a5fb93f450006ae2c5db159c791c913703"
    phase13_part1b: "EXECUTION_BINDING_RESOLVED_AWAITING_TRAINING_REAUTHORIZATION"
    phase13_part1b_authorized: true
    phase13_part1b_executed: false
    phase13_part1b_check_required_audit: "reports/audits/phase13_clean_v3_localizer_part1b_check_required.json"
    phase13_part1b_binding_validation_status: "PASS"
    phase13_part1b_binding_resolved_audit: "reports/audits/phase13_clean_v3_localizer_execution_binding_resolved.json"
    phase13_part1b_validation_resolved_audit: "reports/audits/phase13_clean_v3_localizer_execution_binding_validation_resolved.json"
    phase13_clean_v3_loss_label: "EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1"
    phase13_clean_v3_loss_class: "src.losses.localization.CenterNetFocalLoss"
    phase13_clean_v3_loss_alpha: 2.0
    phase13_clean_v3_loss_beta: 4.0
    phase13_clean_v3_loss_dice_weight: 0.0
    phase13_training_started: false
    phase13_inference_started: false
    regional_integration_gate: "REVISE_LOCALIZER"
    regional_mechanism_promoted: false
    RA_MedFiLM_implemented: false
    failure_protocol_status: "SUPERVISOR_FROZEN"
    reference_model_selected: false
    phases_14_18_status: "PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE"
    winner_declared: false
    statistical_testing_performed: false
    next_eligible: "13"
    next_phase_title: "Phase 13 — GT-Free Region Proposal / Localization (Part 1B eligible, not authorized)"
    next_action: "WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_REAUTHORIZATION"

  phase13:
    historical_manifest_version: "phase4_v2"
    historical_population: "FULL_FIELD VAL 106 images / 156 components"
    historical_val_strata: {TINY: 73, SMALL: 29, MEDIUM: 36, LARGE: 18}
    historical_final_localizer: "phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1"
    historical_final_localizer_best_sha: "ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace"
    historical_final_metrics:
      best_epoch: 73
      total_epochs: 88
      tiny_recall90: 0.726027397260274
      overall_recall90: 0.6410256410256411
      hard_tiny_recovered90: 7
      global_empty_images_covered90: 3
      mean_roi_area_fraction: 0.005898906179948982
      mean_proposals_per_image: 4.660377358490566
    historical_selected_proposal_config: {threshold: 0.10, margin: 0.20, top_k: 5, nms_iou: 0.30}
    historical_executing_checkpoint_score:
      source: "scripts/training/train_phase13b_localizer.py:164"
      tuple: "(tiny_recall90, overall_recall90, -mean_roi_area_fraction, -val_loss)"
      length: 4
    historical_phase14_gate: "NOT_PASSED"
    clean_v3_population:
      TRAIN_FULL_FIELD: {images: 770, components: 1161, max_components_per_image: 11,
                         images_gt_5_components: 15}
      VAL_FULL_FIELD: {images: 103, components: 152, max_components_per_image: 2,
                       images_gt_5_components: 0}
      VAL_strata: {TINY: 72, SMALL: 28, MEDIUM: 36, LARGE: 16}
      roi_acquisitions: "EXCLUDED"
    frozen_hard_sets:
      hard_tiny: {count: 15,
                  sha: "2f9828d77c008e7c90cd69e82d0af3568902ca9d508fdfcb9d8ccf8abd569538",
                  path: "reports/tables/phase13_clean_v3_hard_tiny_replication_set.csv"}
      global_empty: {count: 5,
                     sha: "a0b332cad6bca4466ccc528cbe18cc527ef6503603ab69c55b9d699d7979f0ea",
                     path: "reports/tables/phase13_clean_v3_global_empty_replication_set.csv"}
      historical_v2_counts: {hard_tiny: 16, global_empty: 7}
      role: "PRE_FROZEN_SECONDARY_DIAGNOSTIC_COHORT"
      participates_in_primary_checkpoint_selection: false
      anchor_model: "UNet++"
      anchor_role: "HISTORICAL_PHASE13_HARDSET_REPLICATION_ANCHOR_ONLY"
      must_not_replace_gate_cohorts: ["Phase-11 ALL_FOUR_LOW", "Phase-11 hard cohort",
                                      "Phase-11 disagreement cohort", "Phase-12 FULL_FIELD 103"]
    frozen_proposal_configuration:
      threshold: 0.10
      margin: 0.20
      top_k: 5
      nms_iou: 0.30
      clean_v3_primary_grid_search: "DISABLED"
      historical_20_grid: "DEFERRED_SECONDARY_SENSITIVITY_ONLY"
    heatmap_contract: {input: "512x512", output_heatmap: "128x128", heatmap_resolution: 128,
                       explicit_argument_required: true}
    checkpoint_selection:
      mode: "FIXED_CONFIG_HISTORICAL_LEXICOGRAPHIC_SCORE"
      label: "EXECUTING_HISTORICAL_4TERM_FIXED_CONFIG_SELECTION"
      tuple: ["tiny_recall90", "overall_recall90", "-mean_roi_area_fraction", "-val_loss"]
      tuple_length: 4
      provenance: "HISTORICAL EXECUTING CODE"
      comparison: "STRICT_LEXICOGRAPHIC_GREATER_THAN"
      ties: "BAD_EPOCH"
      patience: 15
      r1_8term_tuple_status: "SUPERSEDED_FOR_PRIMARY_CHECKPOINT_SELECTION"
    diagnostic_metrics_not_selection_terms: ["hard_tiny_recovered90",
                                             "global_empty_images_covered90",
                                             "multi_component_recall90",
                                             "mean_proposals_per_image"]
    r1_to_r2_diff: {material: 1, authorized: 1, unauthorized: 0,
                    sha: "637bdffa4b6a51c2e5f1d5c00e5cfd59863e8a656f845a273ac2f3f67f8ca52c"}
    predicted_proposal_training_crops_in_phase13: false
    phase14_distribution_requirement: "DEFERRED_REQUIREMENT_FOR_PHASE14_IF_GATE_ALLOWS"
    downstream_primary: "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED"
    downstream_margin: 0.20
    oracle_comparator_margin: 0.25
    retention_label: "PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION"
    findings:
      - "HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH: VERIFIED (deferred to Phase 14)"
      - "LATENT_INFERENCE_HEATMAP_RESOLUTION_OMISSION: VERIFIED_DEFECT (fix approved)"
      - "STAGE4D_DESIGN_AUDIT_LABEL_PROVENANCE_DEFECT: historical v2 provenance only"
      - "NON_BLOCKING_HISTORICAL_ARTIFACT_GAP: val_search_epoch079.csv not fabricated"
      - "CHECKPOINT_SELECTION_PROVENANCE: executing 4-term tuple (R2), 8-term extension superseded"
    clean_v3_hard_sets: "RE_DERIVED_AND_FROZEN (secondary diagnostics only)"

  phase10:
    part_1a_attention_unet: "COMPLETE"
    part_1b_unetpp: "COMPLETE"
    part_1c_deeplabv3plus: "COMPLETE"
    final_four_model_comparison: "COMPLETE"
    winner_declared: false

  phase11:
    part_1a: "COMPLETE"
    part_1b: "COMPLETE"
    status: "COMPLETE"
    historical_v2_status: "COMPLETE (provenance only, phase4_v2, 283 VAL cases)"
    historical_replication_anchor: "UNet++ (HISTORICAL_REPLICATION_ANALYSIS_ANCHOR)"
    anchor_is_not: ["winner", "best model", "Phase-12 reference decision"]
    reference_model_selected: false
    failure_definitions_frozen: true
    new_thresholds_introduced: 0
    clean_v3_low_dice_q10: {UNet: 0.4693939398443986, Attention_UNet: 0.5360238052845407,
                            UNetpp: 0.5618055568014564, DeepLabV3plus: 0.3784289703007593}
    all_four_low_count: 12
    unetpp_hd95_q90_valid: 85.24095485204775
    unetpp_fp_q90: 5.0
    regime_gap_mean_dice: 0.2276
    hard_case_cohort: {target: 16, actual: 16, underfilled: []}
    bridge_verdict: "MOTIVATES_ORACLE_ROI_TEST (no claim that ROI solves the problem)"

  phase12:
    part_1a: "COMPLETE"
    part_1b: "COMPLETE"
    part_1c: "COMPLETE"
    part_1d: "COMPLETE"
    status: "COMPLETE"
    status_label: "PHASE12_COMPLETE_PASS"
    primary_population: "KUB FULL_FIELD VAL 103 cases / 152 native components"
    models: [UNet, Attention_UNet, UNetpp, DeepLabV3plus]
    reference_model: none
    primary_variant: "ORACLE_FLOAT_GLOBAL_RETAINED"
    comparator_variant: "GLOBAL_NATIVE"
    secondary_variant: "ORACLE_FLOAT_CROP_ONLY (SECONDARY_HISTORICAL_GEOMETRY_COMPARATOR)"
    legacy_label: "COMBINED_LEGACY_RESTORE_SENSITIVITY"
    global_reproduction_label: "DICE_IOU_GLOBAL_REPRODUCTION_GATE_PASS"
    oracle_mechanism_value: "SUPPORTED_DESCRIPTIVE_EVIDENCE"
    phase13_progression: "SCIENTIFICALLY_JUSTIFIED"
    macro_dice: {UNet: [0.594180, 0.724722], Attention_UNet: [0.629805, 0.699595],
                 UNetpp: [0.640516, 0.726679], DeepLabV3plus: [0.560251, 0.750372]}
    delta_dice_mean: {UNet: 0.130542, Attention_UNet: 0.069790,
                      UNetpp: 0.086164, DeepLabV3plus: 0.190121}
    component_model_recovery_events: 120
    unique_native_components: 152
    lost_component_detections: 0
    empty_case_model_recoveries: 27
    new_empty: 0
    worsened_case_model_rows: 150
    case_model_rows: 412
    max_worsening: -0.5866
    fp_precision_cost: "PRESENT (FP burden rises; precision slightly decreases)"
    cases_all_four_positive_delta_dice: 46
    cases_all_four_object_recall_nonworse: 103
    oracle_limitation: "GT-derived location / NOT deployable / does not prove Phase 13 reproduces the gain"
    final_regional_integration_gate: "REVISE_LOCALIZER"
    regional_mechanism_promoted: false
    accepted_notebook_shas:
      part1a: "c226ea0f28b93b9cafdc08e9720aec320f6080f8302369e51e201e1515867b05"
      part1b: "5848728526885a7186c5c32ab4e5b7cc9d4b7eaedc1a26994799afe81d27fef0"
      part1c: "7ebad54f1a7d45681138db298efff9e1af1567fac4051b27d325794be9e777a8"

  models_clean_v3:
    unet:
      experiment_id: "phase9_kub_unet_baseline_seed42_512_clean_v3"
      status: "TRAINED"
      best_epoch: 44
      val_macro_dice: 0.7406133413314819
      val_macro_iou: 0.6253822445869446
      precision: 0.7707186937332153
      recall: 0.7839437127113342
    attention_unet:
      experiment_id: "phase10_kub_attention_unet_seed42_512_clean_v3"
      status: "TRAINED"
      best_epoch: 54
      val_macro_dice: 0.7525129853960107
      val_macro_iou: 0.6349387691368995
      precision: 0.7729140812402236
      recall: 0.7922248481868364
      precision_recall_provenance: "HISTORY_NATIVE"
    unetpp:
      experiment_id: "phase10_kub_unetpp_seed42_512_clean_v3"
      status: "TRAINED"
      best_epoch: 70
      val_macro_dice: 0.7641595156062713
      val_macro_iou: 0.6525442690586191
      precision: 0.7996825971468945
      recall: 0.7912384169561990
    deeplabv3plus:
      experiment_id: "phase10_kub_deeplabv3plus_seed42_512_clean_v3"
      status: "TRAINED"
      architecture: "deeplabv3plus_resnet50_os16"
      backbone_pretrained: false
      output_stride: 16
      aspp_rates: [6, 12, 18]
      auxiliary_head: false
      parameter_count: 40340769
      best_epoch: 52
      val_macro_dice: 0.7509140344161673
      val_macro_iou: 0.6460492792430865
      precision: 0.7943328495850855
      recall: 0.7822983241135557
      epochs_completed: 67

  complete_epoch_tables:
    rule: "one row per completed epoch, untruncated, built from immutable history.csv"
    rows: {unet: 59, attention_unet: 69, unetpp: 85, deeplabv3plus: 67}
    note: "prior frozen notebooks were NOT retro-edited; final comparison reconstructs all four"

  gallery:
    canonical_selection: "reports/tables/phase09_clean_v3_val_gallery_selection.csv"
    sha256: "10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db"
    cases: 16
    scope: "KUB-only VAL"
    metrics_status: "DETERMINISTIC_GALLERY_SUBSET_ONLY"

  metadata_governance:
    classes: [CONDITIONING_ALLOWED, REPORTING_ONLY, FORBIDDEN_AS_INPUT]
    kub_kidney_bladder_ureteric: "REPORTING_ONLY (not pixel classes)"
    deployment_unavailable_metadata_as_input: "FORBIDDEN"

  ablation_plan:
    status: FUTURE_ABLATION_PLAN
    configurations: [A_SHARED_GLOBAL, B_GLOBAL_DOMAIN_FILM, C_GLOBAL_REGIONAL,
                     D_GLOBAL_DOMAIN_FILM_REGIONAL, E_GLOBAL_DOMAIN_FILM_REGION_SCALE_FILM,
                     F_FULL_ADAPTIVE_RA_MEDFILM_SEG_PP]
    results_exist: false

  statistics:
    performed: false
    note: "single-seed; no paired tests, CIs, or effect sizes yet"

  accepted_notebook_shas:
    phase10_final_comparison: "b9f5812eaef5b538dbd9b2640c974212a6e1dac0858fc13a882a4ff68971a06e"
    phase11_part1a_protocol_freeze: "aaf1d86ef80bbde84700544eebb6fa5177750bcabedf710623fa584426ee86dc"
    phase11_part1b_failure_analysis: "4c78815dc16554ecfe67c29ed16f2c9857cc09ad2d7552aae190025c3b825716"

  known_conflicts:
    - id: C1
      source: "PROJECT_CONTEXT.md"
      issue: "claims no clean-rerun phase executed"
      material: true
    - id: C2
      source: "PROJECT_CONTEXT.md"
      issue: "declares UNet++ strongest (v2 winner claim)"
      material: true
    - id: C3
      source: "PROJECT_MASTER_PLAN.md"
      issue: "Phase 09 clean-v3 marked NOT started"
      material: true
    - id: C4
      source: "ANTIGRAVITY_WORKFLOW.md"
      issue: "CURRENT PHASE 13B, next action NONE"
      material: true
    - id: C5
      source: "reports/audits/antigravity_current_state.json"
      issue: "phase10_unetpp_started=False while PART_1B_COMPLETE"
      material: false
      resolved: "repaired 2026-09-21 (Phase-11 preflight audit)"
    - id: C6
      source: "reports/audits/antigravity_current_state.json"
      issue: "Attention U-Net precision/recall recorded None (actually HISTORY_NATIVE)"
      material: false
    - id: C7
      source: "src/utils/test_lock.py"
      issue: "lock manifest_version labelled phase4_v2 (TEST byte-identical, lock valid)"
      material: false
```

---

---

## PHASE 13 PART 1B — CLOSURE STATE (2026-09-22)

**Phase13 Part1B: COMPLETE / PASS** · localizer training: **COMPLETE** ·
best checkpoint: **FROZEN** · best epoch **53** · final epoch **68** ·
termination **EARLY_STOPPING_PATIENCE** · final bad_epochs **15**.

Canonical primary coverage: **HISTORICAL_EXECUTING_BBOX_COVERAGE** (R2C).
Pixel coverage: **SECONDARY_COVERAGE_SENSITIVITY_ONLY** (never a selection term).

Canonical best tuple (bbox): `(0.6805555555555556, 0.5986842105263158,
-0.004846047236646169, -1.9175469095890338)`.

Canonical secondary bbox diagnostics: hard_tiny 4/15 · global_empty 1/5 ·
multi_component 0.5714285714285714 · mean_proposals_per_image 4.796116504854369.

Canonical selection sidecar: `reports/tables/phase13_part1b_canonical_selection_history.csv`
(68 rows; authoritative for checkpoint-selection replay — row 31's legacy
`history.csv` primaries are pixel-based and preserved as-is).

Closure repairs completed: R2C markdown runner-SHA erratum recorded additively;
training-completion R2C addendum created; epoch-results table rebuilt with ALL raw
history columns (68 contiguous rows); reviewer notebook rebuilt and Run-All clean
(0 unexecuted, 0 errors, SHA stable 3/3); artifact registry rebuilt (29 rows,
0 missing, 0 duplicates, 0 empty SHAs).

Provenance incidents disclosed in the notebook: two supervisor-ordered
interruptions (after epochs 28 and 31) with same-ID resumes; the pre-stop epoch-27
`best.pt` was overwritten by the authorized resume at epoch 31 (metrics survive in
history, weights do not).

**Part1C: ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION · AUTHORIZED: FALSE.**
Standalone proposal analysis NOT STARTED · predicted-region segmentation NOT STARTED ·
regional integration gate NOT_DECIDED · Phase14 NOT STARTED · TEST reads **0**.

next_action: `WAIT_FOR_SUPERVISOR_PHASE13_PART1C_AUTHORIZATION`

---

## PHASE-13 FINAL GATE RESULT (Parts 1D-B and 1E-B live state)

```
phase13_part1d_b_status: "COMPLETE_PASS_FROZEN"
phase13_part1e_a_status: "COMPLETE_PASS_FROZEN"
phase13_part1e_b_status: "COMPLETE_PASS"
phase13_status: "COMPLETE"
REGIONAL_INTEGRATION_GATE_AFTER_PHASE13: "REVISE_LOCALIZER"
regional_mechanism_promoted: false
phase14: "NOT_STARTED"
test: "UNTOUCHED"
```

**Part 1D-B** (four-model predicted-region evaluation) PASSED every integrity check (29/29).
Global reproduction reproduced the frozen Phase-12 `GLOBAL_NATIVE` rows at machine precision
(max abs per-case Dice difference 5.551e-17 … 1.110e-16, tolerance 1e-4). 1976 regional crop
evaluations (494 frozen proposals x 4 architectures). Macro Dice GLOBAL / ORACLE / PREDICTED:

| model | GLOBAL | ORACLE | PREDICTED | DELTA_PRED | RETENTION_DICE |
|---|---|---|---|---|---|
| UNet | 0.594180 | 0.724722 | 0.302314 | -0.291866 | -2.235800 |
| Attention U-Net | 0.629805 | 0.699595 | 0.308619 | -0.321186 | -4.602209 |
| UNet++ | 0.640516 | 0.726679 | 0.311355 | -0.329161 | -3.820171 |
| DeepLabV3+ | 0.560251 | 0.750372 | 0.277292 | -0.282959 | -1.488308 |

Precision decreases strongly for all four; recall is broadly preserved; component losses **0**;
new empty predictions **0**; 27 components recovered by >=1 architecture.

**Part 1E-B** adjudicated the gate strictly from the prospectively frozen dimensions:

| dim | dimension | adjudicated state | supports GO | supports REVISE |
|---|---|---|---|---|
| A | ORACLE_MECHANISM_VALUE | `SUPPORTED_DESCRIPTIVE_EVIDENCE` | as precondition | as precondition |
| B | PRACTICAL_LOCALIZATION_RETENTION | `WEAK__FAILS_TO_TRANSLATE_ORACLE_MECHANISM_INTO_DEPLOYABLE_UTILITY` | NO | YES |
| C | GLOBAL_PRESERVATION_FP_COST | `MATERIAL_GLOBAL_PRESERVATION_FP_COST` | NO | YES |
| D | GENERALITY | `CROSS_ARCHITECTURE_CONSISTENT_NEGATIVE__NOT_ISOLATED` | NO | as precondition |

**FINAL GATE VERDICT: `REVISE_LOCALIZER`.** The Phase-12 oracle regional-mechanism hypothesis
**remains supported** (A unchanged); the current frozen GT-free localization / proposal /
integration path is **NOT promoted** and does **NOT** authorize RA-MedFiLM regional integration
yet. `NO_GO` was unavailable by the frozen invariant (a poor GT-free localizer result alone cannot
produce `NO_GO` while A remains supported). No post-hoc numerical threshold, no new subgroup, no
weighted score, no ranking, no winner, no statistical or clinical superiority claim.

Gate artifact `reports/audits/phase13_regional_integration_gate_after_phase13.json`
sha `4436e6a5e13b99d422cfab1668c3f3f2d43993b4c43b19786308d106185a6c75` ·
dimension table `reports/tables/phase13_regional_integration_gate_after_phase13.csv` ·
gate review notebook
`notebooks/phasewise/phase_13_predicted_roi_localization/phase13_regional_integration_gate_review.ipynb`
sha `24eca67c1c3da87bfef03bcc06c6b6244f47e3163c38a83ebf94cc70032471ed`
(READ-ONLY, 0 unexecuted, 0 errors, SHA stable x3).

Counters for 1E-B: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · segmentation
forwards 0 · regional crop forwards 0 · localizer forwards 0 · proposal generation 0 · oracle
reruns 0 · TEST reads 0.

next_action: `WAIT_FOR_SUPERVISOR_REGIONAL_LOCALIZER_REVISION_PLAN`

---

## POST-PHASE-13 REGIONAL REVISION R0 — FAILURE DECOMPOSITION + PROTOCOL FREEZE (live state)

```
post_phase13_revision_branch: "OPEN"
post_phase13_revision_r0_status: "COMPLETE_PASS"
post_phase13_revision_r0_conclusion: "H1_FIRST_SELECTIVE_ACCEPTANCE"
post_phase13_revision_r0_selective_abstention_principle: "SUPPORTED"
post_phase13_revision_r1_status: "ELIGIBLE_AFTER_SUPERVISOR_REVIEW__NOT_AUTHORIZED"
post_phase13_revision_r1_authorized: false
post_phase13_revision_r1_config_count: 7
post_phase13_revision_r1_training_expected: 0
phase13: "COMPLETE_FROZEN"
original_gate: "REVISE_LOCALIZER"
regional_mechanism_promoted: false
phase14: "NOT_STARTED"
test: "UNTOUCHED"
```

Analysis only — 0 training, 0 model constructions, 0 CUDA, 0 inference, 0 proposal regeneration,
0 checkpoint writes, 0 TEST reads.

**Diagnosis.** The Phase-13 failure is an **intervention-precision** failure, not a representation
failure. Of 494 frozen proposals, 122 hit GT and 372 do not (GT-miss fraction **0.753036**). The
proposal score is near-degenerate (**68.22%** saturated at the maximum 0.125065; range 0.024717;
IQR 0.000533) yet still informative: saturated proposals hit GT at **0.335312** versus **0.057325**
below the maximum, ROC-AUC **0.670611**. Every **label-blind** marginal floor removes more off-target
proposals than GT-hit proposals — the q10 floor (0.119470) removes **50 off-target at zero hit cost**.
The strongest descriptor of the FP burden is `off_target_support_fraction`
(Spearman **rho 0.5918 – 0.6372**, consistent across all four architectures). Improvement concentrates
in cases where GLOBAL was already struggling (lower Part-1C `bbox_covered90`). **Component losses are 0
for all four architectures** and every recovered component had `bbox_any_overlap_rate` 1.000 —
favourable recovery evidence preserved.

**Conclusion.** `H1_FIRST_SELECTIVE_ACCEPTANCE` — change **only** which already-produced proposals are
accepted for regional intervention (score acceptance floor + maximum accepted proposals). Same localizer
weights, same segmentation checkpoints, same proposal geometry, same margin 0.20, same NMS 0.30, same
crop/restore, same fusion. Zero acceptance is an allowed outcome, and the frozen fusion rule already
guarantees `PREDICTED == GLOBAL` exactly when nothing is accepted.

**Frozen R1 candidate family (design only, NOT executed):** 7 configs (max 8) — control **R1-C0**
(floor 0.10, max 5) plus label-blind marginal score floors 0.119470 / 0.124532 / 0.125065 x max
accepted 1 / 5. R1 is **one** bounded policy-ablation round; candidate-family expansion after results is
**forbidden without supervisor approval**; if H1 fails, **STOP** — do not automatically move to
retraining.

**Artifacts.** `post_phase13_regional_revision_r0_failure_decomposition.{json,md}` ·
`post_phase13_regional_revision_r0_protocol_frozen.{json,md}` ·
`post_phase13_r0_proposal_score_rank_diagnostics.csv` ·
`post_phase13_r0_case_proposal_burden.csv` (103 rows) ·
`post_phase13_r0_proposal_to_segmentation_linkage.csv` ·
`post_phase13_r0_proposal_to_segmentation_scatter.csv` ·
`post_phase13_r0_improved_vs_worsened_context.csv` ·
`post_phase13_r0_component_recovery_context.csv` ·
`post_phase13_regional_revision_r1_candidate_family.csv`

**Publication discipline.** This is an adaptive development revision informed by Phase-13 VAL failure
evidence. VAL remains development data; TEST remains untouched until Phase 39. No revision VAL claim can
substitute for final TEST evaluation. No external-test tuning; no hidden candidate search.

next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_AUTHORIZATION`

---

## POST-PHASE-13 REVISION R0-B — R1 POLICY MEMBERSHIP / TIE-BREAK FREEZE (live state)

```
post_phase13_revision_r0b_status: "COMPLETE_PASS"
post_phase13_revision_r1_policy_status: "SUPERVISOR_FROZEN_R1_POLICY_READY_FOR_EXECUTION"
post_phase13_revision_r1_acceptance_comparator: "GREATER_THAN_OR_EQUAL"
post_phase13_revision_r1_order: "proposal_rank ASCENDING"
post_phase13_revision_r1_tie_handling: "FROZEN_PROPOSAL_RANK"
post_phase13_revision_r1_zero_acceptance: "GLOBAL_FALLBACK"
post_phase13_revision_r1_control_identity_pass: true
post_phase13_revision_r1_monotonicity_pass: true
post_phase13_revision_r1_distinct_memberships: 6
post_phase13_revision_r1_status: "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED"
post_phase13_revision_r1_authorized: false
```

**Execution semantics (frozen).** Acceptance is `proposal_score >= score_acceptance_floor`
(comparator **`>=`**, not `>`), using the floors physically stored in the candidate-family CSV as the
executable constants — recomputing a quantile in R1 or changing floor precision after outcomes is
forbidden. Selection is by **`proposal_rank` ASCENDING**, then capped at `max_accepted_proposals`.
`PROPOSAL_RANK_ROLE = DETERMINISTIC_FROZEN_ORDER_ONLY`, **not** confidence superiority within ties;
re-sorting tied proposals by GT / area / coverage / outcome / random / heuristics / floating score is
forbidden. Zero accepted → prediction **GLOBAL exactly** (valid and expected).

**Frozen membership** (label-blind, 3458 rows = 7 x 494) with acceptance counts
**494 / 103 / 444 / 103 / 372 / 102 / 337** for **R1-C0 … R1-C6**, and membership SHA-256
`ac5bbc02… · 844f70d3… · ec8c5b9c… · 844f70d3… · f58a5a94… · 0c424bb6… · 5b40128e…`.
R1 inference **must** verify these hashes before CUDA.

**Gates.** Control identity **PASS** (R1-C0 accepts 494/494 with per-case counts identical to Part-1C).
All 8 relationship checks **PASS** (floor monotonicity adds 0 accepted; cap subsets hold). Tie audit:
marginal max `0.1250653713941574`, **337** tied (0.682186), rank-1 saturated **102/103**, rank-2 91/103,
**0** proposals strictly between the stored 0.125065 floor and the exact max.

**Disclosed family redundancy — family NOT changed.** **R1-C1 ≡ R1-C3** (identical membership
`844f70d3…`): with `max=1` the choice is the lowest-rank floor-passing proposal and every rank-1 score is
`>= 0.124852`, above both floors. Distinct memberships **6** of **7**; no configs added or removed; R1
effectively tests **6 distinct policies**.

**R0 causal-language clarification (additive).** The persisted R0 artifacts used exclusionary wording
("not a representation failure") in 3 locations. Canonical replacement: *"dominated by poor intervention
precision / off-target intervention burden … does not exclude localizer representation or score
calibration as contributors."* Classification `CAUSAL_LANGUAGE_SCOPE_CLARIFICATION_ONLY`; R0 artifacts
**not** rewritten; H1 ordering, measurements, candidate family and membership **unchanged**.

Counters: training 0 · optimizer 0 · model constructions 0 · CUDA 0 · localizer forwards 0 ·
segmentation forwards 0 · regional crop forwards 0 · proposal generation 0 · checkpoint writes 0 ·
TEST reads 0 · external-test reads 0.

next_action: `WAIT_FOR_SUPERVISOR_REVISION_R1_EXECUTION_AUTHORIZATION`

---

## POST-PHASE-13 REVISION R1 EXECUTION — SELECTIVE-ACCEPTANCE POLICY ABLATION (live state)

```
post_phase13_revision_r1_execution_status: "COMPLETE_PASS"
post_phase13_revision_r1_run_id: "post_phase13_regional_revision_r1_selective_acceptance"
post_phase13_revision_r1_c0_reproduction: "PASS_ALL_FOUR"
post_phase13_revision_r1_c1_eq_c3_output: "YES"
post_phase13_revision_r1_regional_crop_evaluations: 1976
post_phase13_revision_r1_global_model_forwards: 0
post_phase13_revision_r1_global_cache_reused: true
post_phase13_revision_r1_h1_verdict: "NOT_ADJUDICATED"
h1_adjudication: "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED"
h2: "NOT_STARTED"
phase14: "NOT_STARTED"
test: "UNTOUCHED"
```

**Compute-efficiency contract honoured.** Each of the 494 frozen proposals was forwarded **once** per
architecture — **1976** regional crop evaluations (494 x 4), not 1976 x 7. All seven policies were
assembled from the same per-case regional maps. The verified Part-1D-B global cache was reused
(412/412 items; GLOBAL_NATIVE reproduced at 5.6e-17 … 1.1e-16 max abs Dice) so **0** global model forwards
were run. HD95 memoised by binary-prediction hash (1184 calls, 1700 memo hits).

**Gates.** Control reproduction **PASS** — R1-C0 reproduces frozen Part-1D-B with max abs per-case Dice
difference **8.7e-17 … 9.7e-17** (tolerance 1e-6) for all four models. **C1 == C3 duplicate PASS** —
identical ranks, fused probability, binary prediction, metrics (0.0) and component detection. **All 21
integrity gates PASS**, zero failures. Row contracts: case-policy-model **2884**, component-policy-model
**4256**, model-policy summary **28**, policy intervention summary **7**, cross-architecture **7**.

**Result (descriptive).** Macro Dice per policy (UNet / Attention / UNet++ / DeepLab):
C0 0.302/0.309/0.311/0.277 · C1(=C3) 0.458/0.481/0.477/0.426 · C2 0.308/0.314/0.316/0.283 ·
C4 0.326/0.332/0.331/0.298 · C5 0.463/0.486/0.483/0.426 · C6 0.340/0.341/0.341/0.304.
`RETENTION_DICE` is **negative for every policy and every architecture** (best C5: -1.00/-2.06/-1.83/-0.70).
Mean FP delta falls sharply with selectivity (+7325 → +1770 for UNet, a 76% reduction) and the Dice deficit
roughly halves, but component recoveries fall from 16/9/14/16 to 2/1/3/4 under the most aggressive
selectivity while mild selectivity (C2/C4/C6) largely preserves recovery. **Component losses remain 0 for
all policies and all architectures**; components lost by >=1 model = 0 for every policy.

**No R1 verdict.** No best policy, no winner, no optimal threshold, no GO/NO_GO, no promotion, no
retraining recommendation, no H2 authorization. Counters: training 0 · optimizer 0 · localizer forwards 0 ·
proposal generation 0 · global forwards 0 · regional crops 1976 · oracle reruns 0 · TEST reads 0 ·
external-test reads 0 · candidate-family expansion 0.

**Adaptive-development disclosure.** R1 is an adaptive VAL-development revision initiated after Phase 13
failed the gate; the 7-policy family was frozen before candidate-specific segmentation execution and
membership is label-blind; GT is post-freeze evaluation only; VAL is development data; R1 findings do not
replace final TEST; TEST untouched until Phase 39.

Notebook `post_phase13_regional_revision_r1_analysis.ipynb` — READ-ONLY, 21 sections, 0 unexecuted /
0 errors, SHA stable x3 `2cbf25da6290ca15ee5863b63da8a8de99f8deccff48b59e927cb306de3cbbdb`.

next_action: `WAIT_FOR_SUPERVISOR_R1_H1_ADJUDICATION_AUTHORIZATION`


**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[RULES.md](RULES.md) · [DESIGN.md](DESIGN.md) · [TASKS.md](TASKS.md)

---

## POST-PHASE-13 R1-H1 ADJUDICATION (live state)

```
post_phase13_revision_r1_h1_adjudication_status: "COMPLETE_PASS"
post_phase13_revision_r1_h1_outcome: "H1_PARTIAL_MITIGATION_INSUFFICIENT_AS_STANDALONE_REVISION"
post_phase13_revision_r1_h1_state: "CLOSED__PARTIAL_MITIGATION_INSUFFICIENT"
post_phase13_revision_r1_h1_dimension_A: "NOT_RESTORED__MATERIALLY_IMPROVED_BUT_STILL_DEFICIENT"
post_phase13_revision_r1_h1_dimension_B: "PARTIAL__RECOVERY_SIGNAL_LOST_UNDER_AGGRESSIVE_SELECTIVITY"
post_phase13_revision_r1_h1_dimension_C: "IMPROVED__BUT_OFF_TARGET_FRACTION_REMAINS_HIGH"
post_phase13_revision_r1_h1_dimension_D: "CONSISTENT_ACROSS_ARCHITECTURES__NEGATIVE_RESULT_IS_GENERAL"
post_phase13_revision_r1_h1_below_global_count: "28/28"
post_phase13_revision_r1_h1_retention_negative_count: "28/28"
post_phase13_revision_r1_h1_proves_representation_failure: false
r1_candidate_family: "CLOSED"
post_hoc_r1_expansion: "FORBIDDEN"
h2_protocol_design: "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED"
h2_training: "NOT_AUTHORIZED"
phase14: "NOT_STARTED"
test: "UNTOUCHED"
```

**Adjudication.** Selective acceptance materially improves intervention precision — dimension C is clearly
positive (accepted 494 → 102, GT-miss accepted 372 → 68, mean precision 0.2342 → 0.4259, FP burden −74%) —
but **no frozen policy jointly restores global preservation and retains enough regional utility**. All
**28/28** config/model combinations remain below GLOBAL; R1-C5 still trails by 0.131–0.158; the FP burden
stays positive everywhere; `RETENTION_DICE` is negative in **28/28**; and component recoveries collapse
55 → 10 (82%) under aggressive selectivity while mild selectivity relieves only 2% of the FP burden.

**H1 does NOT prove a representation failure.** It isolated the acceptance-only axis and showed that axis
is not sufficient by itself. Representation, heatmap confidence calibration, proposal ranking, training
objective, checkpoint-selection semantics and precision/recall balance remain open H2 contributors.

**Bounded search closed.** R1 family CLOSED; post-hoc expansion FORBIDDEN. New thresholds 0 · new configs 0
· new subgroup 0 · winner NONE · selected threshold NONE.

Artifacts: `post_phase13_regional_revision_r1_h1_adjudication.{json,md}` ·
`post_phase13_regional_revision_r1_h1_adjudication.csv` (4 rows A–D).

next_action: `WAIT_FOR_SUPERVISOR_H2_PROTOCOL_DESIGN_AUTHORIZATION`

---

## POST-PHASE-13 H2-A — SCORE-PATH AUDIT + SELECTION-ONLY PROTOCOL (live state)

```
post_phase13_h2a_status: "COMPLETE_PASS_FROZEN"
post_phase13_h2a_score_path_verdict: "SCORE_PATH_IMPLEMENTATION_VALID"
post_phase13_h2a_axis: "H2A_DEPLOYMENT_BALANCED_CHECKPOINT_SELECTION_ONLY"
post_phase13_h2a_execution_mode: "MODE_B__DETERMINISTIC_TRAINING_REPLAY_WITH_NEW_SELECTION"
post_phase13_h2a_trajectory_classification: "C__ONLY_BEST_AND_LATEST_AVAILABLE"
post_phase13_h2a_available_epoch_weights: [31, 53, 68]
post_phase13_h2a_score_plateau_imposed_by_code: false
post_phase13_h2a_material_scientific_observation: "DEGENERATE_LOCALIZER_HEAD__NEAR_CONSTANT_OUTPUT"
post_phase13_h2a_new_primary_utility: "DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90"
post_phase13_h2a_checkpoint_selection_changed: true
post_phase13_h2a_other_axes_changed: false
h2a_execution: "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED"
h2a_training: "NOT_AUTHORIZED"
h2_loss_redesign: "NOT_STARTED"
h3_fusion_redesign: "NOT_STARTED"
phase14: "NOT_STARTED"
test: "UNTOUCHED"
```

**Score path is VALID.** All twelve suspected defects absent: no clamp, no normalization, no rounding, no
quantization, sigmoid applied exactly once, no double sigmoid, no rescale, correct channel `[0,0]`, correct
per-component maximum, no serialization truncation, no top-k score replacement, no threshold substitution.
**The 0.125065 plateau is NOT code-imposed** — it equals `sigmoid(head output)`.

**Material scientific observation `DEGENERATE_LOCALIZER_HEAD__NEAR_CONSTANT_OUTPUT`.** All 16 head weights
are negative and near-identical (std 0.0018 vs mean -0.2036; abs-max/abs-mean 1.0195), so the head is
effectively `-0.2036 * sum(features) + bias`. Bias -1.9453773498535156 -> sigmoid 0.12505828655695442,
essentially the observed plateau. The heatmap is therefore near-constant. This is a trained-model property,
not a score-path defect — recorded, not hidden, and it pre-registers why H2A selection alone may prove
insufficient.

**Trajectory.** history.csv 68 contiguous epochs; best.pt epoch 53; latest.pt epoch 68; only epochs
{31, 53, 68} have weights; no per-epoch proposals. Hence **MODE_B deterministic training replay with new
selection** (identical gradient-update semantics; only the best-epoch rule changes).

**Frozen protocol.** New primary utility `DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90`; new 6-term tuple
adds P and puts the HMean first; strict lexicographic, ties BAD_EPOCH, patience 15. Only checkpoint
selection changes — loss/target/architecture/sigma/optimizer/data/augmentation/proposal config all
UNCHANGED. Proposal contract and downstream fusion unchanged; R1 selective acceptance NOT carried into H2A.
Experiment id has no collision.

next_action: `WAIT_FOR_SUPERVISOR_H2A_EXECUTION_AUTHORIZATION`

---

## POST-PHASE-13 H2-A-B1 — TRAINING REPLAY + DEPLOYMENT-BALANCED SELECTION (live state)

```
post_phase13_h2a_b1_status: "COMPLETE_PASS"
post_phase13_h2a_b1_completed_epochs: 98
post_phase13_h2a_b1_termination: "EARLY_STOPPING_PATIENCE"
post_phase13_h2a_b1_best_epoch: 83
post_phase13_h2a_b1_final_bad_epochs: 15
post_phase13_h2a_b1_trajectory_reproduction: "PASS"
post_phase13_h2a_b1_max_train_loss_diff: 4.441e-16
post_phase13_h2a_b1_max_val_loss_diff: 0.0
post_phase13_h2a_b1_selection_replay: "PASS"
post_phase13_h2a_b1_standalone_pixel_precision: 0.27571115973741794
post_phase13_h2a_b1_standalone_tiny90: 0.6944444444444444
post_phase13_h2a_b1_standalone_overall90: 0.6381578947368421
post_phase13_h2a_b1_standalone_proposals: 457
h2a_downstream: "ELIGIBLE_FOR_SUPERVISOR_REVIEW__NOT_AUTHORIZED"
h2a_outcome_adjudication: "NOT_STARTED"
h2_loss_redesign: "NOT_STARTED"
h3_fusion_redesign: "NOT_STARTED"
phase14: "NOT_STARTED"
test: "UNTOUCHED"
```

**Training.** 98 epochs, early stopping (best 83 + patience 15 = 98). Best six-term tuple
`(0.4522162369629855, 0.6944444444444444, 0.6381578947368421, 0.27571115973741794,`
`-0.0047946270615735415, -1.8425761369558482)`. best.pt `2e2e8f79…` · latest.pt `429041f8…` ·
history.csv `ed96c4b6…`.

**Integrity.** Trajectory reproduction **PASS** — 68 overlapping epochs, max abs train_loss diff **4.441e-16**,
max abs val_loss diff **0.000e+00**, 0 LR mismatches (gradient semantics bit-identical). Checkpoint
model-state cross-checks: **none** (best 83 / latest 98 are not 31/53/68 — no provenance-valid overlap, as
the protocol allows). Selection replay **PASS**, 0 mismatches.

**Standalone best-checkpoint evaluation.** 457 proposals (4.4369/img); P **0.275711** · tiny90 **0.694444** ·
overall90 **0.638158** · recall50 0.822368 · any-overlap 0.875 · mean coverage 0.787897 · mean union area
0.004795 · score max 0.141637 / IQR 0.001654 / fraction-at-max 0.645514 · ROC-AUC 0.701110 · PR-AUC
0.372936. Cohorts: hard-Tiny 3/15, global-empty 2/8, multi-component 61/98.

**vs Phase-13 best (epoch 53), descriptive only.** P 0.246964 → **0.275711** (+0.028748); tiny90 0.680556 →
**0.694444** (+0.013889); overall90 0.598684 → **0.638158** (+0.039474); proposals 494 → 457.
Every quantity improves except proposal count and mean union area. **No superiority or significance claim.**

**Notebook** `post_phase13_h2a_localizer_training_review.ipynb` — READ-ONLY, 26 sections, 0 unexecuted /
0 errors, epoch table 98/98 untruncated, SHA stable x3 `aace38193f1af10c34e9c449eb73f8eb6ad8577efc44f132745a40491de7a332`.

next_action: `WAIT_FOR_SUPERVISOR_H2A_DOWNSTREAM_AUTHORIZATION`

---

## POST-PHASE-13 H2-A-B2 — DOWNSTREAM REGIONAL SEGMENTATION EVALUATION (live state)

```
post_phase13_h2a_b2_status: "COMPLETE_PASS"
post_phase13_h2a_b2_run_id: "post_phase13_h2a_downstream_epoch83_native_policy"
post_phase13_h2a_b2_regional_crop_evaluations: 1828
post_phase13_h2a_b2_case_model_rows: 412
post_phase13_h2a_b2_component_model_rows: 608
post_phase13_h2a_b2_model_summary_rows: 4
post_phase13_h2a_b2_localizer_forwards: 0
post_phase13_h2a_b2_proposal_regeneration: 0
post_phase13_h2a_b2_new_global_forwards: 0
post_phase13_h2a_b2_frozen_proposals: 457
post_phase13_h2a_b2_complete_tables_rendered: {model_summary: "4/4", case_model: "412/412", component_model: "608/608"}
post_phase13_h2a_b2_b1_crosscheck_limitation: "NONBLOCKING_SECONDARY_INTEGRITY_CHECK_UNAVAILABLE"
post_phase13_h2a_b2_reporting_status: "RECONCILED_PASS"
post_phase13_h2a_b2_reporting_classification: "CHAT_TRANSCRIPTION_ONLY"
post_phase13_h2a_b2_reporting_reconciliation_sha: "04cebdc4474576f74c5473387e785e42c1ba21d35623044ef30fc513741fae25"
h2a_outcome: "ELIGIBLE_FOR_SUPERVISOR_ADJUDICATION"
h2a_outcome_authorized: False
next_action: "WAIT_FOR_SUPERVISOR_H2A_OUTCOME_ADJUDICATION_AUTHORIZATION"
```

**Downstream evaluation.** 457 frozen H2A proposals (no regeneration), 1828 regional crop evaluations
(457 x 4 models), 0 localizer forwards, 0 new global forwards, global cache reused (412/412 reproduced).

**Model summary.** H2A predicted-region Dice is **substantially LOWER than GLOBAL** for all 4 models
(macro Dice deficits -0.271 to -0.317) with large FP burden; it is **higher than Phase13 predicted**
for all 4 (+0.011 to +0.012), i.e. the localizer-level improvement translates downstream but the
absolute predicted-region path remains far below GLOBAL. Oracle-benefit retention is **negative**
across all models. 83 cases worse than GLOBAL in all 4 models; 3 cases improved in all 4.
29 components recovered by >=1 model (5 by all 4); 1 component lost by >=1 model.
FP delta vs GLOBAL is large positive for all 4 (+7047 to +8136).

> **Reporting reconciliation (2026-09-24).** The returned H2A-B2 chat final note was defective:
> `H2A−GLOBAL` was reported as **positive** (+0.019465/+0.011554/+0.012691/+0.011625) when the
> authoritative values are **negative** (-0.280400/-0.309632/-0.317470/-0.271334), and
> `fp_delta_vs_global` was reported as **+1064.8** when the authoritative values are
> **+7047.0/+7306.126214/+7721.980583/+8135.572816**. Classification `CHAT_TRANSCRIPTION_ONLY`;
> no authoritative table, frozen audit or notebook ever contained the wrong values.
> See `reports/audits/post_phase13_h2a_b2_reporting_reconciliation.json|.md`.

**Notebook** `post_phase13_h2a_downstream_analysis.ipynb` — READ-ONLY, 31 sections, 55 cells / 25 code,
Run-All 0 unexecuted / 0 errors, complete tables untruncated (4/4 · 412/412 · 608/608),
SHA stable x3 `97ad366a6a2fb4f34a506829923363fb3700794b285920186f544781d6543fa7`.

next_action: `WAIT_FOR_SUPERVISOR_H2A_OUTCOME_ADJUDICATION_AUTHORIZATION`


---

## PHASE 14 CLEAN-V3 — PRE-EXECUTION IMPLEMENTATION-BINDING INCIDENT (live state)

```
phase14_clean_v3_status: "FROZEN_AWAITING_EXECUTION__IMPLEMENTATION_PROSPECTIVELY_BOUND"
phase14_predecessor_classification: "INVALID_PRE_FREEZE_IMPLEMENTATION_BINDING"
phase14_pre_execution_implementation_binding_invalid_predecessor: "FAIL"
phase14_pre_execution_implementation_binding: "PASS (prospective, after rebinding)"
phase14_trainer_path: "scripts/training/train_phase14_refiner.py"
phase14_trainer_sha: "d768422f77abae415be8bd712ff67bef4e16605f053287db04e1840c9f7f0aa8"
phase14_predecessor_completed_epochs: 1
phase14_predecessor_invalid_checkpoint_latest_sha: "82d80ad4bde7f7a5533434bd9f6f58afa8ed69093d7eb33ff6a4ba1ed9957993"
phase14_predecessor_invalid_checkpoint_best_sha: "824a43a3d8744cef53d84284dd8d0fa412d9ded3c6fcabeccf677aea175903f0"
phase14_predecessor_checkpoints_disposition: "PRESERVED_IN_PLACE_FOR_AUDIT__NOT_RESUMED"
phase14_restart_from_epoch: 0
phase14_resume_forbidden: true
phase14_scientific_parameters_changed: false
phase14_bindings_count: 29
phase14_active_training_confirmed: false
phase14_log_epoch_evidence_present: false
next_action: "SUPERVISOR_REVIEW_OF_BOUND_MANIFEST_THEN_RESTART_PHASE14_CLEAN_V3_FROM_EPOCH_0"
```

**Determination (CASE B).** The pre-training freeze manifest was **not prospectively bound** to the
executed implementation. Evidence: (a) `phase14_clean_v3_freeze_manifest.json` was written at
`05:31:16` while `scripts/training/train_phase14_refiner.py` was created at `05:32:27` — **71 s later**,
so the manifest could not have hashed the trainer; (b) the manifest contains **no trainer-SHA key**
among its 17 `protocol_bindings`; (c) the executed trainer imports **10 unbound** implementation files
(itself, `src/utils/device.py`, `src/utils/config.py`, and transitively `src/inference/predicted_roi.py`
→ `kub_dataset.py`, `transforms.py`, `models/factory.py`, `utils/checkpointing.py`,
`utils/manifest_guard.py`, `utils/test_lock.py`).

**Premise correction (transparent).** The premise "a Phase-14 clean-v3 training process is currently
running" **could not be confirmed**. At audit time there were 3 `python.exe` processes (4.5 / 15.7 /
21.9 MB RSS — none CUDA-sized), GPU use was **1.10 GB / 8.59 GB**, and `logs/phase14_train.log` held
only **two `FutureWarning`s** with no `Epoch` line. **However** training logic *did* execute: both
checkpoints exist, written at `05:46:56`, at `epoch = 1`, `best_val_crop_dice = 0.8206131113202948`,
with embedded `configuration` matching the frozen protocol. `experiments/…/` is empty (no
`history.csv`, no `closure.json`) — so the run completed **epoch 1**, then terminated.

**Path-resolution ambiguity (recorded).** `regional_evaluator_py_sha`
(`ea09b9efc12b832ad1a7f6a3746fc30756193555ae4c5bfe2929a54b395773f2`) exists on disk but at
`src/inference/regional_evaluator.py`, **not** the `scripts/evaluation/phase14_regional_evaluator.py`
path implied by the key. SHA matches; path does not.

**Actions.** No process existed to stop; logs preserved unmodified; invalid checkpoints **preserved in
place and NOT resumed**; **no scientific parameter changed**; manifest re-issued with **29 bindings**
(the original manifest preserved verbatim under `superseded_pre_freeze_manifest`) and status
`FROZEN_AWAITING_EXECUTION__IMPLEMENTATION_PROSPECTIVELY_BOUND`; **restart from epoch 0 required**
(resume forbidden). All 20 resolvable bindings verified PASS against disk.
