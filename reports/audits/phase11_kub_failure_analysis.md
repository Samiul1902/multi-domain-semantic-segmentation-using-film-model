# Phase 11 — KUB Global Baseline Failure Analysis

**Status: PASS**

Primary: UNet++. Secondary FP comparator: DeepLabV3+. VAL only at threshold 0.5.

FULL_FIELD Dice: 0.652776413200; ROI_CROP Dice: 0.828201264901. Empty predictions: 8.

Original-space size summary is retained in `phase11_kub_size_failure_summary.csv`. Descriptive strata are analysis labels, not tuning thresholds. Original and evaluation component spaces remain explicit. The evidence motivates testing an ROI/zoom upper bound but does not claim ROI will solve the failures. TEST reads: 0; external: false; Experiment A untouched; no training; Phase 12 not executed.

Notebook SHA-256: `7d0d4b8a0728980c9486f7cb9220dc5f344c426a7ec98c8c3b0cd5a2562dc758`
