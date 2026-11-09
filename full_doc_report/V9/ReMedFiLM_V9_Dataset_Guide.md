# ReMedFiLM Comprehensive Eight-Dataset Resource & Provenance Guide

**Author:** Medical Image Segmentation Research Lead & Biostatistician  
**Scope:** Primary Development Benchmarks, Secondary External Benchmarks, and Evaluated Extension Cohorts

---

## 1. Primary Multi-Domain Benchmarks (Internal Development: TRAIN, VAL808, TEST1683)

### 1. ISIC 2018 (Task 1: Lesion Boundary Segmentation)
- **Modality:** Dermatoscopy (Optical Skin Surface Imaging)
- **Clinical Target:** Cutaneous Lesions (Melanoma, Nevi, Seborrheic Keratoses)
- **Annotation Type:** Pixel-level binary lesion boundary masks
- **Public URL:** [https://challenge.isic-archive.com/data/](https://challenge.isic-archive.com/data/)
- **Primary Citation:** Codella et al., "Skin Lesion Analysis Toward Melanoma Detection 2018: A Challenge Hosted by the International Skin Imaging Collaboration (ISIC)", *arXiv:1902.03368* (2019); Tschandl et al., *Scientific Data* (2018).
- **Licence:** Creative Commons Attribution-NonCommercial 4.0 International (CC BY-NC 4.0).
- **Repository Split Allocation:** Train: 1,816; Val: 259 (in VAL808); Protected Test: 519 (in TEST1683). All images preprocessed to 512×512 resolution.

### 2. BUSI-WHU (Breast Ultrasound Dataset)
- **Modality:** B-Mode Ultrasound
- **Clinical Target:** Breast Neoplasms (Benign Fibroadenomas, Malignant Carcinomas)
- **Annotation Type:** Ground-truth tumor contour boundary masks
- **Public URL:** [https://data.mendeley.com/datasets/k6cpmwybk3/3](https://data.mendeley.com/datasets/k6cpmwybk3/3)
- **Primary Citation:** Al-Dhabyani et al., "Dataset of breast ultrasound images", *Data in Brief*, 28:104863 (2020).
- **Licence:** Creative Commons Attribution 4.0 International (CC BY 4.0).
- **Repository Split Allocation:** Train: 546; Val: 78 (in VAL808); Protected Test: 156 (in TEST1683). Normal/clean scans excluded from segmentation training.

### 3. Kvasir-SEG (Gastrointestinal Polyp Dataset)
- **Modality:** Endoscopy (Optical Colonoscopy)
- **Clinical Target:** Colorectal Polyps (Precancerous Adenomas, Hyperplastic Lesions)
- **Annotation Type:** Expert-verified pixel-level segmentation masks
- **Public URL:** [https://datasets.simula.no/kvasir-seg/](https://datasets.simula.no/kvasir-seg/)
- **Primary Citation:** Jha et al., "Kvasir-SEG: A Segmented Polyp Dataset", *MultiMedia Modeling (MMM)*, pp. 451–462 (2020).
- **Licence:** Open Access (Simula Research Laboratory Open License).
- **Repository Split Allocation:** Train: 700; Val: 100 (in VAL808); Protected Test: 200 (in TEST1683).

### 4. KUB-StoneX (Pelvic Radiograph Calculi Benchmark)
- **Modality:** Abdominal & Pelvic Radiography (X-Ray)
- **Clinical Target:** Urinary Tract Calculi (Kidney, Ureter, Bladder Stones)
- **Annotation Type:** Bounding boxes and stone segmentation masks
- **Public URL:** [https://doi.org/10.6084/m9.figshare.32049369.v1](https://doi.org/10.6084/m9.figshare.32049369.v1)
- **Primary Citation:** Project Research Consortium, "KUB-StoneX: A Multi-Center Benchmark for Urinary Calculi Detection and Boundary Delineation" (2025).
- **Licence:** Open Academic Research License.
- **Repository Split Allocation:** Train: 566; Val: 80 (in VAL808); Protected Test: 162 (in TEST1683). Exhibits significant acoustic noise, pelvic bone shadows, and faint calcifications.

---

## 2. Retrospective External Multi-Center Generalization Cohorts (EXTERNAL884)

### 5. CVC-ClinicDB (Polyps in Colonoscopy)
- **Modality:** Endoscopy
- **Clinical Target:** Polyp Boundaries
- **Evaluated Count:** $n = 612$ frames
- **Public URL:** [https://polyp.grand-challenge.org/CVCClinicDB/](https://polyp.grand-challenge.org/CVCClinicDB/)
- **Primary Citation:** Bernal et al., "WM-DOVA maps for accurate polyp detection in colonoscopy: Validation vs. saliency maps from physicians", *Computerized Medical Imaging and Graphics*, 43:99–111 (2015).
- **Role in Project:** External out-of-distribution endoscopic stress test.

### 6. BrEaST-Lesions-USG (Multi-Center Breast Ultrasound)
- **Modality:** Ultrasound
- **Clinical Target:** Breast Lesions
- **Evaluated Count:** $n = 252$ scans
- **Public URL:** [https://www.cancerimagingarchive.net/collection/breast-lesions-usg/](https://www.cancerimagingarchive.net/collection/breast-lesions-usg/)
- **Primary Citation:** Pawłowska et al., "A machine learning approach for the classification of breast lesions in ultrasound images using deep features", *Cancer Imaging Archive (TCIA)* (2024).
- **Role in Project:** Retrospective multi-center breast lesion generalization benchmark.

### 7. Stones_where_are_you (Roboflow Radiography)
- **Modality:** Abdominal X-Ray
- **Clinical Target:** Urinary Calculi
- **Evaluated Count:** $n = 20$ scans (6 stone-positive, 14 stone-free controls)
- **Public URL:** [https://universe.roboflow.com/xray-abdomen-to-identify-stones/stones_where_are_you](https://universe.roboflow.com/xray-abdomen-to-identify-stones/stones_where_are_you)
- **Role in Project:** External pelvic calculi test and negative control false-positive assessment.

---

## 3. Evaluated Extension Cohort (Audited Offline)

### 8. HAM10000 ("Human Against Machine with 10000 training images")
- **Modality:** Dermatoscopy
- **Clinical Target:** Pigmented Skin Lesions
- **Annotation Type:** Diagnostic multi-class categorical labels + binary masks (10,015 images/masks)
- **Public URL:** [https://doi.org/10.7910/DVN/DBW86T](https://doi.org/10.7910/DVN/DBW86T)
- **Primary Citation:** Tschandl, Rosendahl, Kittler, "The HAM10000 dataset, a large collection of multi-source dermatoscopic images of common pigmented skin lesions", *Scientific Data*, 5:180161 (2018).
- **Local Filesystem Status:** `D:\Softfors\final\external_test_ds\HAM10000` (10,015 pairs intact).
- **Scientific Status in ReMedFiLM:** `EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED`. Completely independent of ISIC 2018 project splits (0% overlap).
