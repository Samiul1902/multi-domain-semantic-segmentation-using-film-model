# R2 Dataset Integrity, Label Ontology, Leakage Prevention, and Evaluation Verification Report

**Milestone State:** `C1_RC2_GIT_RECONSTRUCTIBLE__RELEASE_FROZEN__EXTERNAL_AUTHORIZATION_PENDING__NO_SCIENTIFIC_EXECUTION`  
**Phase State:** `RA_MEDFILM_BARR_R2_DATASET_ONTOLOGY_AND_EVALUATION_INTEGRITY_VERIFIED__SCIENTIFIC_EXECUTION_UNCHANGED`

---

## 1. Executive Summary & Objective

This Phase R2 investigation establishes an uncompromised, verified dataset, annotation, and label-ontology foundation for the RA-MedFiLM-BARR project. In strict accordance with governance boundaries:
- **Zero real-data inference, training, or re-scoring was executed.**
- **No protected test sets (`TEST`, `ROUTER_HOLDOUT`, `QUARANTINE`) were opened or scored.**
- **C1 RC2 frozen release digest (`54794efc6d99d94fae9eaebd992e01e4e9923b5055d024ea1d5f02a8a5e737ed`) remains bitwise preserved.**

---

## 2. Canonical Four-Domain Reconciliation & Label Ontology

The four segmentation tasks and their alias bindings have been reconciled across source manifests and implementations (`src/research/evaluation_r2/ontology_r2.json`):

| Domain | Canonical Dataset Identity | Modality | Target Semantics | Binary / Multiclass | Label Values in Raw Mask | Harmonized Mask Rule | Patient Identifiers | Physical Spacing (mm) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **KUB** | KUB-StoneX | Digital Radiography (X-Ray) | Urinary calculi | Binary | `{0, 1, 2, 3, 255}` | `mask > 0` | `VERIFIED_FROM_AUTHORITY` (429 groups) | `NOT_AVAILABLE` (unitless pixel) |
| **ISIC** | ISIC 2018 Task 1 | Dermoscopy | Skin lesion boundary | Binary | `{0, 255}` | `mask > 0` | `NOT_AVAILABLE` (Image IDs only) | `NOT_AVAILABLE` (unitless pixel) |
| **BUSI** | WHU Breast Ultrasound | Ultrasound (BUS) | Breast lesion / mass | Binary | `{0, 255}` | `mask > 0` | `INFERRED` (Audit sidecar only) | `NOT_AVAILABLE` (unitless pixel) |
| **KVASIR** | Kvasir-SEG | Gastrointestinal Endoscopy | Colorectal polyp | Binary | Nonzero intensities (JPEG artifacts) | `mask > 0` | `NOT_AVAILABLE` | `NOT_AVAILABLE` (unitless pixel) |

### Key Ontology Reconciliations:
1. **Patient Identifier Audit (KUB vs. ISIC/DERM):**
   - Earlier C1 records correctly noted that only KUB possesses verified patient identifiers in canonical manifests (`patient-00001`, etc.).
   - ISIC/DERM filenames are image IDs; no patient mapping exists in canonical segmentation manifests. R1's fallback to image-level resampling for ISIC is **mandatory and mathematically verified**.
2. **BUSI Patient Grouping Sidecar:**
   - In Phase 05, a sidecar mapping (`reports/tables/phase05_busi_patient_group_mapping.csv`, 927 mapped samples) was used for patient-disjoint split construction.
   - However, the canonical `manifests/phase4_v3/train.csv` and `val.csv` list `patient_id: NOT_AVAILABLE`. Therefore, under the frozen C1 statistical plan, BUSI must be evaluated with case-level bootstrap, not patient-cluster bootstrap.
3. **Physical Pixel Spacing:**
   - No domain possesses measured physical millimeter spacing in canonical manifests. Any historical or synthetic `(1.0, 1.0)` is an isotropic pixel grid ratio, **not physical mm**. Boundary metrics are reported in pixel units.
4. **Binary vs. Multiclass:**
   - All four domains are strictly binary foreground segmentation tasks. Nonzero integers in KUB and Kvasir are encoding/compression artifacts, not anatomical subclasses.

---

## 3. Dataset & Split Integrity Audit

Audit of active development manifest version `phase4_v3` (`manifests/manifest_registry.json`):
- **TRAIN Manifest:** `manifests/phase4_v3/train.csv` — SHA-256: `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` ($N = 5,832$).
- **VAL Manifest:** `manifests/phase4_v3/val.csv` — SHA-256: `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315` ($N = 808$).
- **Sample Disjointness:** Exactly 0 overlapping `sample_id`s ($5,832 \cap 808 = \emptyset$).
- **Image Path Disjointness:** Exactly 0 overlapping `image_path`s.
- **KUB Patient Disjointness:** Exactly 0 overlapping `patient_id`s ($318 \cap 111 = \emptyset$).
- **Quarantined Samples:** 118 samples quarantined across domains to remediate historical split contamination.

---

## 4. Targeted Review of R1 Implementation

| Question | Assessment | Verification Status |
| :--- | :--- | :--- |
| **A. C1 Compatibility** | `c1_compatibility` reproduces the exact frozen equation $\frac{2 \cdot TP + \epsilon}{2 \cdot TP + FP + FN + \epsilon}$ with $\tau=0.5, \epsilon=10^{-7}$, and float32 counts. Tested against `scripts/training/phase21_common.py::per_image_dice_iou_precision_recall`. | `IMPLEMENTATION_VERIFIED` |
| **B. Hierarchical Statistics** | Unweighted domain macro average is strictly decoupled from pooled pixels. Sample SD enforces $ddof=1$. Paired bootstrap enforces common seed draws and patient clustering for KUB. | `IMPLEMENTATION_VERIFIED` |
| **C. Manifest Identity Scheme** | `artifact_manifest.json` correctly excludes itself from its internal list of hashed files and notes `self_excluded`, preventing circular digest definitions. | `METADATA_VERIFIED` |
| **D. Grad-CAM Classification** | In the R1 evidence map, Grad-CAM attribution had no supporting executed artifact in the evaluation package. It is strictly classified as `ALREADY_EXECUTED_DESCRIPTIVE` / `SCIENTIFIC_VALIDATION_PENDING` (descriptive exploration only, no causal claim). | `SCIENTIFIC_VALIDATION_PENDING` |

---

## 5. Automated Leakage & Evaluation Audit Contract

Implemented in [`src/research/evaluation_r2/leakage_contract.py`](file:///D:/Softfors/jup/src/research/evaluation_r2/leakage_contract.py):
- Reusable `LeakageAuditContract` class.
- Rejects prohibited splits (`TEST`, `ROUTER_HOLDOUT`, `QUARANTINE`, `EXTERNAL`).
- Canonicalizes domain aliases (`DERM` $\rightarrow$ `ISIC`, `KUB-StoneX` $\rightarrow$ `KUB`, `POLYP` $\rightarrow$ `KVASIR`).
- Validates shapes, NaNs, Infs, and bounds $[0.0, 1.0]$.
- Flags unverified patient IDs and unverified physical mm spacing.

---

## 6. Synthetic Unit & Mathematical Validation

All 35 unit tests passed cleanly:
```text
tests/test_evaluation_r1_reference.py (10 passed)
tests/test_evaluation_r1_contract.py (4 passed)
tests/test_evaluation_r1_metrics.py (16 passed)
tests/test_evaluation_r2_integrity.py (5 passed)
============================= 35 passed in 4.75s =============================
```

---

## 7. Evidence & Limitations Classification

- `IMPLEMENTATION_VERIFIED`: Exact formula matching, unit test mathematical correctness, zero-denominator handling, and leakage contract validation.
- `METADATA_VERIFIED`: Canonical manifest SHA-256 hashes, TRAIN/VAL sample counts (5832/808), KUB patient disjointness.
- `SCIENTIFIC_VALIDATION_PENDING`: Grad-CAM spatial attribution, regional refiner benefit, selective router acceptance.
- `NOT_ESTABLISHED`: Clinical efficacy, multi-class segmentation, independent external generalization.
