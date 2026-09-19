# Phase 05 — Code & Execution Audit Directory

This directory contains the reviewer-facing reproduction scripts for **Phase 05 (Forensic Data Leakage & Duplicate Audit)**.

## Scripts Overview

### 1. `phase05_leakage_audit.py`
- **Purpose:** Standalone, deterministic verification of multi-level data leakage boundaries without opening locked TEST image content.
- **Audit Levels Executed:**
  - **Level 1 (Sample ID Disjointness):** Confirms $\text{TRAIN} \cap \text{VAL} = 0$, $\text{TRAIN} \cap \text{TEST} = 0$, $\text{VAL} \cap \text{TEST} = 0$ across all 8,441 unique cases.
  - **Level 2 (Patient Group Disjointness):** Confirms zero patient overlap across splits for KUB (318 TRAIN, 111 VAL, 282 TEST) and 100% TRAIN containment for `patient-00360` (24 cases). Confirms non-KUB cohorts lack canonical group IDs.
  - **Level 3 (Exact TRAIN <-> VAL Image Content):** Recomputes binary SHA-256 for all 6,758 TRAIN and VAL image assets. Discloses 1 inherited raw KUB image asset collision (`00273-01` vs `00320-01`).
  - **Level 4 (Exact TRAIN <-> VAL Mask Content):** Recomputes binary SHA-256 for all 6,758 TRAIN and VAL ground-truth masks (0 cross-split duplicates).
  - **Level 5 (Perceptual Near-Duplicates):** Audits pre-calculated diagnostic 64-bit DCT pHash candidates (Hamming distance $\le 6$, 64 TRAIN <-> VAL candidates flagged).
  - **Historical TEST Evidence Audit:** Reads frozen pre-lock leakage audit records from `reports/audits/leakage_audit.json`.
  - **Immutability Check:** Confirms unchanged SHA-256 digests for Phases 00, 01, 02, 03, 04, and canonical Phase 14.
  - **Zero-Test-Read Governance:** Enforces `test_image_reads = 0`, `test_mask_reads = 0`, and `test_visualizations = 0`.
- **Execution:**
  ```powershell
  D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_05_leakage_audit/code/phase05_leakage_audit.py
  ```

### 2. `phase05_leakage_visualization.py`
- **Purpose:** Generates publication-quality charts and qualitative panels representing multi-level leakage evidence.
- **Figures Generated:**
  1. `phase05_leakage_evidence_matrix.png`: Multi-level leakage matrix clearly separating current recomputations from frozen pre-lock evidence.
  2. `phase05_dataset_leakage_status.png`: Per-dataset leakage status and duplicate counts summary.
  3. `phase05_phash_distance_distribution.png`: Hamming distance distribution of TRAIN <-> VAL near-duplicate candidates.
  4. `phase05_top_train_val_duplicate_candidates.png`: Qualitative comparison panels for top 12 near-duplicate candidate pairs (NO TEST imagery displayed).
- **Execution:**
  ```powershell
  D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_05_leakage_audit/code/phase05_leakage_visualization.py
  ```

### 3. `phase05_duplicate_adjudication.py`
- **Purpose:** Standalone, deterministic adjudication script for confirmed KUB exact collisions and all 64 near-duplicate candidates.
- **Key Features:**
  - Forensically characterizes KUB collision (`patient-00273` vs `patient-00320`).
  - Traces affected validation case across Phases 09-15 and recomputes leave-this-case-out sensitivity metrics.
  - Generates `phase05_train_val_candidate_adjudication.csv`, `phase05_downstream_impact_matrix.csv`, and `phase05_kub_exact_collision_forensics.csv`.
- **Execution:**
  ```powershell
  D:\Softfors\jup\.venv\Scripts\python.exe notebooks/phasewise/phase_05_leakage_audit/code/phase05_duplicate_adjudication.py
  ```

## Canonical Dependencies
- `manifests/all_paired.csv`, `train.csv`, `val.csv`, `test.csv`: Canonical population partitions.
- `reports/audits/leakage_audit.json`: Historical pre-lock audit evidence source.
- `reports/audits/near_duplicate_candidates.csv`: Pre-lock pairwise pHash candidate records.

## Governance Boundaries
- Current run reads TRAIN and VAL image/mask content only.
- TEST image and mask content reads = 0.
- TEST metrics = NONE.
- Model inference = NO.

