# Phase 10 — Reviewer Support Code

Read-only modules live here: one reviewer per completed clean-v3 architecture, plus the
final four-model comparison module.

**Per-architecture reviewers:**
- `phase10_attention_unet_review.py` — Attention U-Net (Part 1A)
- `phase10_unetpp_review.py` — UNet++ (Part 1B)
- `phase10_deeplabv3plus_review.py` — DeepLabV3+ (Part 1C)

**Final comparison:**
- `phase10_final_comparison.py` — four-model clean-v3 comparison (UNet, Attention U-Net,
  UNet++, DeepLabV3+): history normalization, per-epoch table generation, paired 280-case
  KUB VAL inference, subgroup summaries, figure generation, hash verification.
- `run_paired_inference.py` — driver that runs the read-only paired inference and writes the
  paired / overall / stratified / delta / disagreement tables.

All modules are **read-only** analysis support.

## Common contract

Each module loads history/audits/config, verifies SHAs, loads `best.pt` for inference,
filters **KUB-only VAL**, reuses the **canonical frozen 16-case gallery**
(SHA `10ad09cb...`, never reselected), and generates training figures.

The DeepLabV3+ module additionally builds the **complete epoch-by-epoch reviewer table**
(`build_epoch_table` / `verify_epoch_table` / `save_epoch_table`): exactly one row per
completed epoch, with derived reviewer-only columns
(`delta_val_dice_vs_previous_epoch`, `delta_best_metric`, `is_new_best`, `is_best_epoch`,
`epochs_since_best`). The physical `history.csv` is **never** modified.

### NO winner / no significance testing

No module performs ranking, winner selection, or significance testing. All four
architectures have clean-v3 runs, but they are **single-seed (42) descriptive VAL
evidence** and Phase 29 (three-seed reproducibility) / Phase 31 (statistical testing) have
not run. Paired deltas and disagreement counts are computed for **understanding only** and
are labelled `DESCRIPTIVE_SINGLE_SEED_ONLY`. **No Phase-10 winner is declared** anywhere in
this code.

### What this code is

This module provides reviewer utilities for inspecting the completed run:

- load config, start/completion audits, and training history
- verify history continuity and strict-max best epoch
- load checkpoint metadata safely (no model instantiation for metadata)
- verify artifact SHA-256 against recorded provenance
- verify checkpoint provenance (experiment, manifest, taxonomy, seed, resolution, threshold)
- verify early-stop consistency
- derive KUB-only VAL population (hard-gated to 280 rows)
- deterministic, prediction-independent gallery selection
- best-checkpoint VAL inference with per-case Dice/IoU
- training-curve generation from real history
- artifact hashing utilities

### What this code is NOT

- It is **not** a trainer.
- It does **not** call `optimizer.step()`.
- It does **not** run training epochs.
- It does **not** write checkpoints.
- It does **not** modify config, history, or checkpoints.
- It does **not** change any scientific parameter.

### Where the scientific training was executed

The actual training was performed by the canonical runner:

```
notebooks/phasewise/phase_10_clean_v3_comparison/code/train_phase10_attention_unet_clean_v3.py
```

That runner is **frozen execution provenance**. Do not move, rename, rewrite, or reformat it.
Do not duplicate its training loop here or in the notebook.

### Governance

- **TEST is locked**: TEST reads = 0, TEST metrics = 0, TEST visualizations = 0.
  The module never constructs a TEST dataset and never reads TEST images/masks.
- **KUB-only**: the VAL population is hard-filtered to `dataset == "KUB"` (280 rows)
  with assertions that reject ISIC/BUSI/Kvasir and NOT_AVAILABLE rows. This avoids
  the cross-domain selection bug that affected the pre-repair Phase-09 reviewer.
- **No cross-model comparison**: this reviews Attention U-Net only. UNet++ and
  DeepLabV3+ have not been rerun, so no winner is declared and no statistical
  comparison is performed.
- **Gallery metrics are descriptive only**: any 16-case mean is
  `DETERMINISTIC_GALLERY_SUBSET_ONLY` and is not the authoritative full-VAL score.
