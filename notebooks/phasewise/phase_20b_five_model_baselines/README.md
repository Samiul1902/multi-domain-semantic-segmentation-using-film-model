# Phase 20B — Five-Model Conventional Baseline Benchmark

**Subphase of Phase 20.** Phase 20B is *not* a new roadmap phase — it is an extension of
Phase 20. The canonical sequence is `19 → 20A → 20B → 21 → 22 → …`; there is no "Phase 20.5".

- **Phase ID:** `phase_20b_five_model_baselines`
- **Scientific title:** Five-Model Conventional Baseline Benchmark (multi-domain)
- **Stage:** B — Multi-Domain Scaling
- **Current status:** **COMPLETE** — training, canonical evaluation and freeze all done
- **Scientific terminal state:** `PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`
- **Reviewer-package terminal state:** `PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED`

## 1. What Phase 20A vs 20B are

| | Phase 20A | Phase 20B |
|---|---|---|
| Role | frozen shared **reference** baseline | additional conventional baselines + five-model freeze |
| Architecture | a single shared **UNet++** | U-Net · Attention U-Net · DeepLabV3+ · Transformer/MiT-style U-Net |
| Params | 9,159,681 | 7.76 M / 7.85 M / 40.35 M / 16.35 M |
| Status | **COMPLETE** | **COMPLETE** |

Phase 20A establishes the shared four-domain reference. Phase 20B adds four more conventional
architectures and produces the **five-model** benchmark and freeze. The five models are ranked
on the *same* 808 VAL cases under the *same* protocol; UNet++ (20A) is included as the
reference row so the comparison is read as one five-way benchmark.

## 2. Governance boundaries (unchanged from Phase 19/20)

- **Data protocol:** identical Phase-19 harmonized four-domain contract
  (`manifests/phase4_v3`), loaded by explicit version.
- **Cohorts read:** TRAIN and VAL only.
- **TEST:** `CLOSED` — 0 image reads, 0 mask reads, 0 inference, 0 visualizations.
  Phase 39 remains the only TEST-evaluation phase.
- **VAL population:** the **same 808 cases** for every model
  (ISIC 357 · BUSI 84 · KVASIR 87 · KUB 280).
- **Threshold:** `0.5` (frozen, identical for every model).
- **Sampler / loss / optimizer / scheduler contract:** identical for every model —
  `phase20_domain_balanced_uniform_v1` sampler; `bce_dice` loss (0.5/0.5, ε=1e-6);
  AdamW (lr 1e-4, wd 1e-4); CosineAnnealingLR (T_max 100, stepped per epoch after train+val);
  batch 4; AMP on; seed 42.
- **No task conditioning. No FiLM. No regional module. No localizer. No ROI/proposal.**
  `task_id` is never a model input.
- **Selection rule:** `phase20_macro_domain_mean_dice_v1` (macro-domain mean VAL Dice;
  tie-break lower validation loss). Identical for every model.
- Only the **model constructor** and the **experiment identity** vary between models —
  there is **no per-model recipe, threshold, scheduler or augmentation change**.

## 3. Frozen five-model result

Ranked at each model's own best epoch on the identical 808 VAL cases.

| Rank | Model | Class | Params | Best epoch | Final epoch | Macro-domain VAL Dice |
|---|---|---|---|---|---|---|
| 1 | DeepLabV3+ | `DeepLabV3Plus` | 40,347,041 | 57 | 72 | **0.827652** |
| 2 | Transformer/MiT-style U-Net | `TransformerMiTUNet` | 16,347,777 | 74 | 89 | **0.822383** |
| 3 | U-Net++ (20A reference) | `UNetPlusPlus` | 9,159,681 | 55 | 70 | 0.792010 |
| 4 | Attention U-Net | `AttentionUNet` | 7,851,285 | 64 | 79 | 0.789037 |
| 5 | U-Net | `UNet` | 7,763,041 | 74 | 89 | 0.787832 |

All five stopped by `EARLY_STOPPING_PATIENCE` (patience 15).

**Statistical interpretation (paired domain-stratified percentile bootstrap, `n_boot=2000`,
`seed=42`, the *same* resampled VAL indices across models):**

- The **two-tier separation is statistically significant** — each two-stage architecture
  (DeepLabV3+, Transformer/MiT-style) beats every U-Net-family variant
  (p ≈ 0.000).
- The **top-two ordering is NOT significant** — DeepLabV3+ vs Transformer/MiT-style
  `+0.005270`, 95% CI `[−0.004246, +0.013870]`, `p = 0.282`.
  **DeepLabV3+ must not be called the definitive winner**; it has the highest *observed*
  macro-domain Dice, but the top-two difference is not statistically significant.

**Architecture-naming cautions.**
`deeplabv3plus` uses a **random-init** backbone — it is **not** ImageNet-pretrained.
`transformer_mit_unet` is `LOCAL_RANDOM_INIT` — a MiT-*style* U-Net, **not** official
pretrained MiT-B1.

## 4. Canonical artifacts

- **Canonical notebook:**
  `notebooks/phasewise/phase_20b_five_model_baselines/phase20b_five_model_conventional_baselines.ipynb`
  (SHA recorded in `reports/audits/phase20b_notebook_determinism.json`).
- **Canonical comparison artifacts:**
  - `reports/audits/phase20_five_model_baseline_benchmark_freeze.json` — frozen science
  - `reports/tables/phase20b_five_model_comparison_final.csv`
  - `reports/tables/phase20b_five_model_paired_bootstrap.csv`
  - `reports/tables/phase20b_five_model_per_image_val_metrics.csv`
  - `reports/tables/phase20b_gallery_selection.csv` — the frozen 64-case VAL gallery
- **Figure directory:** `reports/figures/phase20b_five_model_baselines/`
  (`training/ primary_comparison/ metric_heatmaps/ confusion/ roc_pr/ calibration/
  boundary/ bootstrap/ distributions/ kub_subgroups/ kub_size/ tiny/ efficiency/
  agreement/ galleries/ failure_cases/`)
- **Figure inventory:** `reports/audits/phase20b_figure_inventory.{csv,json}`
- **Visualization coverage:** `reports/audits/phase20b_evaluation_matrix_visualization_coverage.csv`
- **Reviewer package audit:** `reports/audits/phase20b_reviewer_package_audit.json`

## 5. Phase 21

Phase 21 (Global MedFiLM reference architecture) is **ELIGIBLE but NOT STARTED**. All Phase-21
entry criteria are met and the Phase-20 five-model baseline is frozen and immutable, but
starting Phase 21 requires **fresh supervisor authorization**. Phase 21 must be compared against
this baseline on the **same 64** deterministically selected VAL cases
(`reports/tables/phase20b_gallery_selection.csv`, IDs byte-identical to the frozen Phase-20A set).

**Terminal state:** `PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`
· **Phase 21: ELIGIBLE_NOT_STARTED.**
