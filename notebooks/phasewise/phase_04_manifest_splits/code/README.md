# Phase 04 — Code & Execution Audit Directory

This directory contains the reviewer-facing reproduction scripts for **Phase 04 (Canonical Manifest & Split Integrity)**.

## Scripts Overview

### 1. `phase04_manifest_split_audit.py`
- **Purpose:** Standalone, deterministic verification of the canonical manifests and population partitioning.
- **Key Functions:**
  - Validates cryptographic SHA-256 hashes of `all_paired.csv`, `train.csv`, `val.csv`, and `test.csv`.
  - Imports and executes the canonical split guard `src/utils/manifest_guard.py`.
  - Verifies exact sample counts across splits (TRAIN: 5,913, VAL: 845, TEST: 1,683; Total: 8,441).
  - Confirms strict disjointness: $\text{TRAIN} \cap \text{VAL} = 0$, $\text{TRAIN} \cap \text{TEST} = 0$, $\text{VAL} \cap \text{TEST} = 0$.
  - Audits KUB patient-level split partitioning: 318 TRAIN, 111 VAL, 282 TEST (0 patient-level overlap).
  - Verifies historical special record `patient-00360` is strictly allocated to TRAIN (24/24 cases).
  - Enforces zero TEST image or mask content reads.
  - Confirms cryptographic immutability of foundational notebooks (Phases 00, 01, 02, 03, and canonical Phase 14).
- **Execution:**
  ```powershell
  D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_04_manifest_splits/code/phase04_manifest_split_audit.py
  ```

### 2. `phase04_split_visualization.py`
- **Purpose:** Generates publication-ready figures representing split statistics and patient distributions using manifest metadata only.
- **Figures Generated:**
  1. `reports/figures/phase04_manifest_splits/aggregate/phase04_dataset_split_counts.png`: Stacked bar chart showing absolute counts per dataset and split.
  2. `reports/figures/phase04_manifest_splits/aggregate/phase04_dataset_split_proportions.png`: Normalized 100% stacked bar chart depicting split proportions (~70/10/20).
  3. `reports/figures/phase04_manifest_splits/aggregate/phase04_kub_patient_split_counts.png`: Bar chart of unique patient distribution in KUB.
  4. `reports/figures/phase04_manifest_splits/aggregate/phase04_split_overlap_matrix.png`: Heatmap demonstrating strict 0-overlap between splits.
  5. `reports/figures/phase04_manifest_splits/aggregate/phase04_kub_category_split_distribution.png`: Clinical stone category distribution across splits.
- **Execution:**
  ```powershell
  D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_04_manifest_splits/code/phase04_split_visualization.py
  ```

## Canonical Dependencies
- `src/utils/manifest_guard.py`: Single canonical source of truth for manifest cryptographic verification.

## Governance Boundaries
- **TEST Manifest Metadata Reads:** ALLOWED.
- **TEST Image/Mask Content Reads:** STRICTLY 0.
- **TEST Metrics / Inference:** STRICTLY NONE.

