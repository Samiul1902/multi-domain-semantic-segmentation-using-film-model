# Phase 09 — CLEAN-v3 KUB Baseline Training

## Part 1A: Scientific Training Execution (COMPLETE)

The clean-v3 UNet baseline was trained using the canonical runner:

```
notebooks/phasewise/phase_09_clean_v3_baseline/code/train_phase09_clean_v3.py
```

This runner is frozen execution provenance. Do not modify it.

### Experiment
- **ID**: `phase9_kub_unet_baseline_seed42_512_clean_v3`
- **Config**: `configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml`
- **Manifest**: `phase4_v3`
- **Taxonomy**: `kub_size_clean_v3_v1`
- **Epochs**: 59 (early stopped)
- **Best epoch**: 44
- **Best VAL macro Dice**: 0.7406133413314819

### Artifacts
- `checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt`
- `checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/latest.pt`
- `experiments/phase9_kub_unet_baseline_seed42_512_clean_v3/history.csv`
- `reports/audits/phase09_clean_v3_training_start_audit.json` / `.md`
- `reports/audits/phase09_clean_v3_training_completion_audit.json` / `.md`
- `reports/figures/phase09_clean_v3/phase09_clean_v3_training_curves.png`
- `reports/tables/phase09_clean_v3_training_history.csv`

## Part 1B: Reviewer Notebook / Packaging (THIS DIRECTORY)

- **Notebook**: `phase09_clean_v3_unet_training_review.ipynb`
- **Support code**: `code/phase09_training_review.py`
- **Code README**: `code/README.md`

The notebook is a read-only scientific reviewer artifact. It does not train. It loads the completed run's history, config, audits, and best checkpoint to verify integrity and produce visualizations.

## What is NOT here

- No TEST evaluation — TEST remains locked until Phase 39.
- No Phase-10 comparison models (`attention_unet`, `unetpp`, `deeplabv3plus`).
- No retraining or checkpoint modification.

## Historical v2 Separation

The historical v2 run (`phase9_kub_unet_baseline_seed42_512/`) used `phase4_v2` and
has no taxonomy binding. It remains immutable. Clean-v3 numbers are not directly
interchangeable with historical v2 numbers because the TRAIN/VAL population differs.
