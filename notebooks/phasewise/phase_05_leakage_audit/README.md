# Phase 05 — Data Leakage & Duplicate Audit (`phase_05_leakage_audit`)

## 1. Scientific Overview
- **Phase ID:** `phase_05_leakage_audit`
- **Scientific Title:** Forensic Data Leakage & Duplicate Audit
- **Current Status:** AUDIT EXECUTION: PASS | SCIENTIFIC LEAKAGE GATE: CHECK_REQUIRED
- **Core Question:** Is there evidence of leakage between TRAIN, VAL, and locked TEST caused by duplicate sample IDs, duplicate patient/group IDs, exact duplicate image content, exact duplicate mask content, near-duplicate medical images, renamed/copied source cases, or dataset-internal duplicated assets while strictly preserving the current TEST-content lock?

## 2. Multi-Level Evidence & Adjudication Summary
Rather than reducing data leakage to a single oversimplified yes/no claim, Phase 05 evaluates leakage across five distinct technical levels:

| Level | Audit Category | Comparison | Finding | Adjudication Status |
| :--- | :--- | :--- | :--- | :--- |
| **Level 1** | Sample ID Disjointness | TRAIN ∩ VAL ∩ TEST | **0 Overlaps** (8,441 unique cases) | Recomputed PASS |
| **Level 2** | Patient Group Disjointness | TRAIN ∩ VAL ∩ TEST | **0 Patient Overlaps** (KUB: 318 Tr, 111 Va, 282 Te; `patient-00360` 100% TRAIN) | Recomputed PASS |
| **Level 3** | Exact Image Content (SHA-256) | TRAIN <-> VAL | **1 Raw Asset Collision** (`patient-00273` in TRAIN vs `patient-00320` in VAL, KUB) | CONFIRMED_EXACT_DUPLICATE |
| **Level 4** | Exact Mask Content (SHA-256) | TRAIN <-> VAL | **0 Overlaps** (Mask Dice: 0.9108 on collision pair) | Recomputed PASS |
| **Level 5** | Perceptual Near-Duplicates | TRAIN <-> VAL | **64 Diagnostic Candidates** (13 likely same-acquisition in ISIC at d=0; 4 unresolved at d=2; 46 false positives at d>=4) | Adjudicated |
| **Historical** | Pre-Lock TEST Leakage | TRAIN/VAL <-> TEST | **0 Exact Overlaps**; 175 pHash candidates pre-lock | Historical Pre-Lock Evidence |

## 3. Strict TEST-Governance Boundary
- **TEST Image Content Reads:** STRICTLY 0.
- **TEST Mask Content Reads:** STRICTLY 0.
- **TEST Image Decodes:** STRICTLY 0.
- **TEST Visualizations:** STRICTLY 0 (No medical imagery from TEST split is rendered).
- **TEST Metrics / Inference:** STRICTLY NONE.
- **Evidence Distinction:** All TEST-related content findings represent frozen historical pre-lock records from `reports/audits/leakage_audit.json` and `reports/audits/near_duplicate_candidates.csv`.

## 4. Reviewer Deliverables
- **Primary Discovery Notebook (Part 1A):**
  `phase05_data_leakage_and_duplicate_audit.ipynb`
- **Adjudication & Impact Notebook (Part 1B Companion):**
  `phase05_duplicate_adjudication_and_downstream_impact.ipynb`
- **Phase-Local Reproduction Code:**
  - `code/phase05_leakage_audit.py`: Standalone multi-level audit script.
  - `code/phase05_leakage_visualization.py`: Generates diagnostic audit figures.
  - `code/phase05_duplicate_adjudication.py`: Standalone Part 1B adjudication and sensitivity script.
  - `code/README.md`: Directory documentation.
- **Output Tables & Audits:**
  - `reports/tables/phase05_leakage_summary.csv`
  - `reports/tables/phase05_duplicate_pairs.csv`
  - `reports/tables/phase05_kub_exact_collision_forensics.csv`
  - `reports/tables/phase05_train_val_candidate_adjudication.csv`
  - `reports/tables/phase05_downstream_impact_matrix.csv`
  - `reports/audits/phase05_leakage_audit.json` / `phase05_leakage_audit.md`
  - `reports/audits/phase05_part1b_adjudication.json` / `phase05_part1b_adjudication.md`
- **Adjudication Figures:**
  - `reports/figures/phase05_leakage_audit/adjudication/phase05_kub_exact_collision_forensics.png`
  - `reports/figures/phase05_leakage_audit/adjudication/phase05_train_val_adjudication_page01.png`
  - `reports/figures/phase05_leakage_audit/adjudication/phase05_train_val_adjudication_page02.png`
  - `reports/figures/phase05_leakage_audit/adjudication/phase05_train_val_adjudication_page03.png`

## 5. Next Phase
- **Phase 06 — KUB Anatomical & Radiographic Characterization** (DO NOT START: Awaiting supervisor decision on split remediation).
