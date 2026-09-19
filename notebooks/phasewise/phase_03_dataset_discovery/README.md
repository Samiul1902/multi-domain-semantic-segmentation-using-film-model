# Phase 03: Multi-Domain Dataset Discovery (`phase_03_dataset_discovery`)

## 1. Scientific Overview
- **Phase ID:** `phase_03_dataset_discovery`
- **Scientific Title:** Multi-Domain Dataset Discovery, Pairing Integrity, and Modality Verification
- **Current Status:** `COMPLETE`
- **Overall Project Status:** Phase 15 (`CURRENT_PROTOCOL_DESIGN` / `AWAITING_SUPERVISOR_AUTHORIZATION`)
- **Core Question:** *What medical-image datasets are actually available to the project, how are images and masks paired, what are their basic modalities/geometries, and does the discovered paired dataset match the canonical project inventory?*

---

## 2. Directory Structure & Deliverables
```text
phase_03_dataset_discovery/
|-- README.md                                                             # This document
|-- phase03_multidomain_dataset_discovery_and_pairing_integrity.ipynb    # Reviewer-facing executed notebook (Run-All PASS)
`-- code/
    |-- phase03_dataset_discovery_audit.py                                # Standalone discovery & pairing audit script
    |-- phase03_sample_visualization.py                                   # Multi-domain sample renderer (12 pages, 48 cases)
    `-- README.md                                                         # Instructions for running audit & visualization code
```

---

## 3. Authoritative Paired Population Summary
The multi-domain discovery census reconciles to **8,441** paired image/mask cases across four medical imaging modalities:
- **ISIC 2018 (Dermoscopy):** 3,694 paired cases
- **BUSI (Breast Ultrasound):** 927 paired cases
- **Kvasir-SEG (GI Endoscopy):** 1,000 paired cases
- **KUB-Stone (Plain Radiography):** 2,820 paired cases
- **Historical 8,159 Count:** Preserved as unresolved historical evidence without being artificially forced onto canonical data.

---

## 4. Qualitative Sample Coverage Standard
- **TRAIN-Only Protocol:** Exactly 48 cases (12 cases per dataset) selected deterministically from the authorized training split via `SHA256("phase03_dataset_sample_seed42|" + dataset + "|" + sample_id)`.
- **Zero Test Access:** `TEST reads = 0`, `TEST visualizations = 0`, `TEST metrics = NONE`.
- **Rendered Figure Deliverables:** 12 structured sample figure pages (3 pages per dataset, 4 cases per page) displaying `Original Image` | `Ground-Truth Mask` | `High-Contrast Green Overlay`.
- **Spatial Alignment:** 100% of selected cases verified to share identical image and mask pixel dimensions.

---

## 5. Key Artifacts & References
- **Dataset Discovery Summary:** [`reports/tables/phase03_dataset_discovery_summary.csv`](file:///D:/Softfors/jup/reports/tables/phase03_dataset_discovery_summary.csv)
- **TRAIN Sample Selection Record:** [`reports/tables/phase03_train_sample_selection.csv`](file:///D:/Softfors/jup/reports/tables/phase03_train_sample_selection.csv)
- **Figure Manifest & Page Hashes:** [`reports/audits/phase03_figure_manifest.json`](file:///D:/Softfors/jup/reports/audits/phase03_figure_manifest.json)
- **Dataset Inventory Audit:** [`reports/audits/dataset_inventory.json`](file:///D:/Softfors/jup/reports/audits/dataset_inventory.json)
- **Paired Counts Chart:** [`reports/figures/phase03_dataset_discovery/aggregate/phase03_paired_dataset_counts.png`](file:///D:/Softfors/jup/reports/figures/phase03_dataset_discovery/aggregate/phase03_paired_dataset_counts.png)

---

## 6. Reviewer Execution Instructions
### Running the Discovery Audit
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_03_dataset_discovery/code/phase03_dataset_discovery_audit.py
```
*Expected Output:* `PHASE 03 DATASET DISCOVERY AUDIT RESULT: PASS` (0 errors, 0 test content reads, 0 model training).

### Running the Sample Visualizer
```powershell
& "D:\Softfors\jup\.venv\Scripts\python.exe" notebooks/phasewise/phase_03_dataset_discovery/code/phase03_sample_visualization.py
```

### Running the Jupyter Notebook
Open and execute `phase03_multidomain_dataset_discovery_and_pairing_integrity.ipynb` using kernel `jup-venv`. Verified 100% Run-All clean with 32 cells, 0 errors, 13 rendered high-resolution figures (12 dataset sample pages + 1 aggregate count chart).

---

## 7. Next Phase
- **Next Phase:** [`phase_04_manifest_splits/`](file:///D:/Softfors/jup/notebooks/phasewise/phase_04_manifest_splits/README.md) (Canonical Manifest & Patient Splits)
- **Next Phase Status:** `NOT_STARTED` (Awaiting supervisor authorization).
