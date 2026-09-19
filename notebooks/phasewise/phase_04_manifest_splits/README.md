# Phase 04 — Canonical Manifest & Split Integrity (`phase_04_manifest_splits`)

## 1. Scientific Overview
- **Phase ID:** `phase_04_manifest_splits`
- **Scientific Title:** Canonical Manifest & Data Split Governance
- **Current Status:** ACCEPTED / VERIFIED
- **Core Question:** What is the exact canonical paired-data manifest, how are the 8,441 cases partitioned into TRAIN, VAL, and TEST, and can those splits be reproduced and cryptographically verified without opening locked TEST image content?

## 2. Canonical Manifest Artifacts & Accepted SHA-256 Hashes
The 8,441 paired cases across ISIC, BUSI, Kvasir-SEG, and KUB are governed by the following canonical manifest CSV files located in `manifests/`:
- `all_paired.csv`: `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc` (8,441 cases)
- `train.csv`: `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3` (5,913 cases)
- `val.csv`: `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4` (845 cases)
- `test.csv`: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` (1,683 cases)

All hashes match reference accepted values exactly. Manifest verification is enforced via canonical utility `src/utils/manifest_guard.py`.

## 3. Population Allocation & Split Counts
| Dataset Cohort | TRAIN Count (%) | VAL Count (%) | TEST Count (%) | Total Paired Count |
| :--- | :---: | :---: | :---: | :---: |
| **ISIC 2018** | 2,581 (69.87%) | 378 (10.23%) | 735 (19.90%) | **3,694** |
| **BUSI** | 656 (70.77%) | 97 (10.46%) | 174 (18.77%) | **927** |
| **Kvasir-SEG** | 697 (69.70%) | 87 (8.70%) | 216 (21.60%) | **1,000** |
| **KUB-Stone** | 1,979 (70.18%) | 283 (10.04%) | 558 (19.79%) | **2,820** |
| **Authoritative Total** | **5,913 (70.05%)** | **845 (10.01%)** | **1,683 (19.94%)** | **8,441** |

## 4. Patient Grouping & Split Disjointness
- **Sample ID Overlap:**
  - $\text{TRAIN} \cap \text{VAL} = 0$
  - $\text{TRAIN} \cap \text{TEST} = 0$
  - $\text{VAL} \cap \text{TEST} = 0$
  - Unique sample IDs: 8,441 / 8,441 (100% unique membership).
- **KUB Patient-Level Grouping:**
  - Total Unique Patients: 711
  - TRAIN: 318 patients | VAL: 111 patients | TEST: 282 patients.
  - Patient Overlap across all split intersections is strictly **0**.
  - Historical special record `patient-00360` (24 cases) is 100% allocated to TRAIN.
- **Other Datasets (ISIC, BUSI, Kvasir):** Patient metadata is recorded as `NOT_AVAILABLE` in the canonical manifests. No speculative grouping or artificial IDs were fabricated.

## 5. Semantic Pixel Target vs. Subclass Metadata
- **Pixel-Level Target:** Binary foreground vs background segmentation across all domains:
  - ISIC: skin lesion
  - BUSI: breast lesion
  - Kvasir: polyp
  - KUB: stone
- **Subclass Metadata:** KUB includes anatomical stone location metadata (`Kidney_Stone`, `Bladder_Stone`, `Ureteric_Stone`) as case-level clinical attributes. These are **not** pixel segmentation classes, and no multiclass masks were created.

## 6. Reviewer Deliverables
- **Main Reviewer Notebook:**
  `phase04_canonical_manifest_and_split_integrity.ipynb`
- **Phase-Local Reproduction Code:**
  - `code/phase04_manifest_split_audit.py`: Standalone audit verifying hashes, counts, disjointness, and guard compliance.
  - `code/phase04_split_visualization.py`: Generates all publication-quality split charts and figures.
  - `code/README.md`: Directory guide and usage notes.
- **Output Tables & Audits:**
  - `reports/tables/phase04_split_counts.csv`
  - `reports/tables/phase04_manifest_review_rows.csv` (96 deterministic reviewer metadata rows)
  - `reports/audits/phase04_manifest_integrity.json`
  - `reports/audits/phase04_manifest_integrity.md`
  - `reports/audits/phase04_figure_manifest.json`

## 7. Next Phase
- **Phase 05 — Leakage Audit & Near-Duplicate Analysis** (Do not start without supervisor authorization).
