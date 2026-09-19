# Phase 03 Multi-Domain Dataset Discovery Code

## Overview
This directory contains the reviewer-facing, standalone execution scripts for auditing dataset discovery, verifying paired inventory integrity across four medical imaging modalities, and rendering publication-quality qualitative visual panels.

## Scripts & Responsibilities
1. **`phase03_dataset_discovery_audit.py`:**
   - Audits the authoritative paired dataset inventory ($8,441$ total cases across ISIC, BUSI, Kvasir, KUB).
   - Confirms that the historical unresolved $8,159$ count was not artificially forced.
   - Verifies the deterministic, TRAIN-only selection of $48$ samples ($12$ per dataset) with zero TEST leakage (`TEST reads = 0`).
   - Checks image/mask file existence and exact spatial dimension alignment.
   - Cryptographically verifies SHA-256 hashes of foundational notebooks (Phases 00, 01, 02, and 14).

2. **`phase03_sample_visualization.py`:**
   - Loads the frozen selection records from `reports/tables/phase03_train_sample_selection.csv`.
   - Renders $12$ structured figure pages ($3$ pages per dataset, $4$ cases per page) displaying:
     `Original Image` | `Ground-Truth Binary Mask` | `High-Contrast Green Contour Overlay`.
   - Preserves native aspect ratios and modalities (RGB for ISIC/Kvasir, anatomical grayscale for KUB/BUSI).
   - Exports metadata and page hashes to `reports/audits/phase03_figure_manifest.json`.

## Execution Instructions
Run the audit:
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_03_dataset_discovery/code/phase03_dataset_discovery_audit.py
```

Run the visual sample renderer:
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_03_dataset_discovery/code/phase03_sample_visualization.py
```

## Governance Constraints & Non-Actions
- **TRAIN Split Only:** Visualizations use strictly the authorized training partition (`split == TRAIN`).
- **No Test Content Reads:** Strictly zero reads or visualizations of the locked test cohort.
- **No Training / Inference:** Pure data inspection and visualization only.

