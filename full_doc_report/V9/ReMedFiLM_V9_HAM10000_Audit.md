# HAM10000 Dataset Forensic Audit & Evidence Disposition

**Dataset:** HAM10000 ("Human Against Machine with 10000 training images")  
**Local Project Path:** `D:\Softfors\final\external_test_ds\HAM10000`  
**Auditor:** Principal Research Software Engineer & Scientific Results Auditor  
**Status:** Complete Audit; Explicit Non-Inclusion Disposition

---

## 1. Local Filesystem Discovery & Structural Verification

An inspection of `D:\Softfors\final\external_test_ds\HAM10000` revealed:
- **Total Images:** 10,015 images in JPEG format (`images/ISIC_*.jpg`).
- **Total Masks:** 10,015 segmentation mask files in PNG format (`masks/ISIC_*.png`).
- **Metadata:** `metadata.csv` containing 10,015 rows and diagnostic disease labels:
  - Columns: `image`, `MEL`, `NV`, `BCC`, `AKIEC`, `BKL`, `DF`, `VASC`.
- **Attribution & Licensing:** `ATTRIBUTION.txt` confirming public benchmark release for melanoma detection and dermatoscopic analysis under CC BY-NC 4.0.

---

## 2. Overlap Analysis with Project Benchmark Manifests

We conducted an exhaustive automated overlap audit comparing all 10,015 HAM10000 image identifiers against every canonical manifest in `manifests/phase4_v3/`:

| Manifest Split | Population File | Total ISIC Images | Identical Overlap with HAM10000 | Overlap Percentage |
| :--- | :--- | :--- | :--- | :--- |
| **TRAIN** | `manifests/phase4_v3/train.csv` | 2,556 | 0 | 0.0% |
| **VAL808** | `manifests/phase4_v3/val.csv` | 357 | 0 | 0.0% |
| **TEST1683** | `manifests/phase4_v3/test.csv` | 735 | 0 | 0.0% |
| **ALL_PAIRED** | `manifests/phase4_v3/all_paired.csv` | 3,694 | 0 | 0.0% |

**Key Finding:** There is **zero exact image identifier overlap** between the project's internal ISIC 2018 Task 1 benchmark partitions and the local HAM10000 dataset.

---

## 3. Investigation of Historical ReMedFiLM Evaluation Records

We audited all historical audit records in `reports/audits/`, `reports/tables/`, and `reports/external_extension/`:
1. In `reports/tables/phase32_external_cohort_role_registry.csv`, HAM10000 was flagged as `EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY` during exploratory discovery.
2. In `reports/tables/phase37_consolidated/T37-06_external_domain_shift_evidence_summary.csv`, HAM10000 is officially categorized as:
   - `n_image_files_metadata_only = 20030` (referencing combined parts),
   - `candidate_status = HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK / 0 primary-eligible`.
3. In `reports/external_extension/manifests/ext02_ham10000_manifest.csv`, preliminary manifests were cataloged, but **no multi-model inference run or paired ReMedFiLM vs GlobalMedFiLM evaluation was ever executed or logged**.
4. In the historical external benchmark (`reports/tables/c1_external_stress_summary.csv`), the frozen evaluation suite consists strictly of:
   - CVC-ClinicDB: $n = 612$
   - BrEaST-Lesions-USG: $n = 252$
   - Stones_where_are_you: $n = 20$
   - **Total:** $n = 884$ (EXTERNAL884)

---

## 4. Scientific Disposition for Version 9

1. **Explicit Classification:**  
   `EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED`
2. **Denominators Preserved:**  
   The historical EXTERNAL884 benchmark total is preserved exactly. We strictly reject fabricating or simulating retrospective HAM10000 metrics to artificially inflate external numbers.
3. **Future Research Guidance:**  
   Because HAM10000 contains high-quality dermatoscopic images and paired lesion masks completely disjoint from the ISIC 2018 splits, it represents a prime candidate for an authorized, prospective external evaluation in future research phases.
