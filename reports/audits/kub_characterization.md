# Phase 6 — KUB Characterization Audit Report

## Executive Summary
KUB characterization has been completed rigorously using TRAIN (n=1979 samples across 318 unique patients). All statistics, tables, and figures derive deterministically from measured mask parameters. Test-set mask morphology was **not accessed** and remains 100% frozen.

## Key Findings
- **Analysis Population**: KUB TRAIN = 1979 samples, 318 patients.
- **Anatomical Category Breakdown**:
  - `Kidney_Stone`: 1133 samples
  - `Bladder_Stone`: 635 samples
  - `Ureteric_Stone`: 211 samples
- **Foreground Ratio**: Median = `0.209896` (Mean = `0.189589`, Min = `0.000000`, Max = `0.658871`).
- **Connected Components**: Total = 1214 (Mean = `0.61` components/image).
- **Multi-component Images**: 4 images contain >1 foreground component.
- **Patient Distribution**: Min 1, Median 3, Mean 6.22, Max 50 samples/patient.

## Derived Tables & Hashes
- `reports/tables/kub_train_sample_characteristics.csv`: SHA-256 `3a68c22026b7fac6f6c3304028ff1b1a5252844f7f2717189a7d7cf52dc71c51`
- `reports/tables/kub_train_components.csv`: SHA-256 `68c1853811382a75ce0ac618586d4763e4dd9c00a2a4a0d1225640457b4922be`

## Generated Publication Figures (300 DPI PNG & SVG)
- `reports/figures/kub_characterization/kub_category_composition.png`
- `reports/figures/kub_characterization/kub_foreground_ratio_by_category.png`
- `reports/figures/kub_characterization/kub_component_size_distribution.png`
- `reports/figures/kub_characterization/kub_components_per_image.png`
- `reports/figures/kub_characterization/kub_component_centroids.png`
- `reports/figures/kub_characterization/kub_train_val_distribution.png`
