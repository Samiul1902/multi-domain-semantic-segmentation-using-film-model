# Multi-Domain Global Baseline Evaluation (phase_20_multidomain_baselines)

## 1. Scientific Overview
- **Phase ID:** phase_20_multidomain_baselines
- **Scientific Title:** Multi-Domain Global Baseline Evaluation
- **Current Status:** COMPLETE — single frozen shared UNet++ four-domain baseline trained and canonically evaluated on 808 VAL samples (`PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`)
- **Core Question:** Phase 20 evaluates global baselines across all 4 medical modalities.

## 2. Rationale & Academic Significance
Understanding the specific scientific role of this phase within the 41-phase canonical progression (Stage A: KUB Regional/Tiny Development, Stage B: Multi-Domain Scaling, Stage C: Evidence & Rigor, Stage D: Verification & Freeze).

## 3. Inputs & Governance Boundaries
- **Canonical Provenance Source:** docs/phase20_multidomain_spec.md
- **Dataset Cohorts:** TRAIN and VAL only (TEST strictly locked: TEST reads = 0).
- **Hardware Profile:** NVIDIA GeForce RTX 3060 Ti 8GB certified.

## 4. Primary Outputs & Deliverables
- **Documented Artifacts:** Checkpoints, metrics tables, error maps, and qualitative panels.
- **Reviewer Notebook:** Reviewer-facing reproducible Jupyter Notebook.

## 5. Visual Standards
- **Sample Visualizations:** $\ge 12$ deterministic cases where applicable.
- **Prediction Panels:** $\ge 16$ deterministic cases with TP/FP/FN error maps.

## Phase-20 completion status

Phase 20 is **COMPLETE** (Stage B). One conventional shared four-domain baseline:
a single frozen **UNet++** (9,159,681 params) with one shared parameter
set and one output head, trained with a frozen domain-balanced sampler, and selected
on `phase20_macro_domain_mean_dice_v1`. Best epoch **55**, macro-domain
VAL Dice **0.792007**; early stopped at epoch 70.

No FiLM, no task conditioning, no regional module, no localizer, no ROI/proposal.
Terminal state: **`PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**. Phase 21 is **eligible but NOT started**.

## Phase-20B five-model conventional baseline benchmark

Phase 20B extends the Phase-20A baseline into a **five-architecture** benchmark run under the
*identical* frozen protocol (`reports/audits/phase20_shared_global_baseline_protocol.json`,
SHA `b74f1f9f…`). Only the model constructor and the experiment identity vary — no per-model
recipe, threshold, scheduler or augmentation change. TEST reads = 0; exactly **one** canonical
VAL inference pass per model over the **same 808 VAL samples**.

| Rank | Model | Class | Params | Best epoch | Macro-domain VAL Dice |
|---|---|---|---|---|---|
| 1 | DeepLabV3+ | `DeepLabV3Plus` | 40,347,041 | 57 | 0.827652 |
| 2 | Transformer/MiT-style U-Net | `TransformerMiTUNet` | 16,347,777 | 74 | 0.822383 |
| 3 | U-Net++ (20A) | `UNetPlusPlus` | 9,159,681 | 55 | 0.792010 |
| 4 | Attention U-Net | `AttentionUNet` | 7,851,285 | 64 | 0.789037 |
| 5 | U-Net | `UNet` | 7,763,041 | 74 | 0.787832 |

All five stopped by `EARLY_STOPPING_PATIENCE`. Paired domain-stratified percentile bootstrap
(`n_boot=2000`, `seed=42`, **same resampled VAL indices across models**):

- The **two-tier separation is statistically significant** — DeepLabV3+ vs U-Net++
  `+0.035643`, 95% CI `[+0.023153, +0.047986]`, p≈0.000; each two-stage model vs every U-Net
  variant also p≈0.000.
- The **top-two ordering is NOT significant** — DeepLabV3+ vs Transformer/MiT-style
  `+0.005270`, 95% CI `[−0.004246, +0.013870]`, p=0.282 → **tied within noise**.

Naming cautions: `deeplabv3plus` uses a random-init backbone (*not* ImageNet-pretrained);
`transformer_mit_unet` is `LOCAL_RANDOM_INIT` MiT-*style* (*not* official pretrained MiT-B1).

Deliverables: `reports/audits/phase20_five_model_baseline_benchmark_freeze.json`,
`reports/tables/phase20b_five_model_comparison_final.csv`,
`reports/tables/phase20b_five_model_paired_bootstrap.csv`,
`reports/tables/phase20b_five_model_per_image_val_metrics.csv`,
`reports/tables/phase20b_gallery_selection.csv`, and reviewer notebook
`phase20b_five_model_conventional_baselines.ipynb` (SHA `8c13cd14…`).

Terminal state: **`PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`**.
Phase 21 remains **eligible but NOT started**.
