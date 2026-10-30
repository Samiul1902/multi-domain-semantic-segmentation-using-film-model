# Phase 05 — Data Leakage & Duplicate Audit (`phase_05_leakage_audit`)

## Final Status: **COMPLETE**

- **Final active development manifest:** `phase4_v3` (CANONICAL_ACTIVE_DEVELOPMENT)
- **Historical reproducibility manifest:** `phase4_v2` (HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT)
- **Scientific gate:** PASS
- **Clean-v3 revalidation:** REQUIRED for Phases 06–15 (see `reports/tables/phase05_clean_rerun_scope.csv`)

## 0. Notebook Sequence

Phase 05 proceeded through four reviewer notebooks. Each builds on the previous; none
silently replaces another.

| # | Notebook | Role | SHA-256 (executed) |
|---|---|---|---|
| 1 | `phase05_data_leakage_and_duplicate_audit.ipynb` | **Initial discovery** of multi-level leakage evidence | `1dbc8dfc687ddc879a8a335b60073c088032995cf93deff169daf20e4b3e7d78` |
| 2 | `phase05_duplicate_adjudication_and_downstream_impact.ipynb` | **Forensic adjudication** + downstream impact assessment | `91e462716ad9254dc861dca38d8db7e3cb3374bb781ebdbf4b3c4293797a10d8` |
| 3 | `phase05_leakage_safe_manifest_v3_candidate.ipynb` | **Candidate construction/audit** — leakage-safe v3 rebuild | `2d94668e4ec34a98eb20e87f90757460797298063df4d8b6950a2b3f4f6ec3f0` |
| 4 | `phase05_manifest_v3_promotion_and_leakage_closure.ipynb` | **Final canonical promotion** + Phase-05 closure | `cb6fa37d395022eb0aed7115f29c29e679ba3b63744aeda9925de24668d0592a` |

1. `phase05_data_leakage_and_duplicate_audit.ipynb` -> initial discovery
2. `phase05_duplicate_adjudication_and_downstream_impact.ipynb` -> forensic adjudication
3. `phase05_leakage_safe_manifest_v3_candidate.ipynb` -> candidate construction/audit
4. `phase05_manifest_v3_promotion_and_leakage_closure.ipynb` -> final canonical promotion

## 1. Scientific Overview
- **Phase ID:** `phase_05_leakage_audit`
- **Scientific Title:** Forensic Data Leakage & Duplicate Audit
- **Current Status:** PROMOTION: PASS | SCIENTIFIC LEAKAGE GATE: PASS | PHASE: COMPLETE
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
- **Leakage-Safe Candidate Notebook (Part 1D-R6 Candidate):**
  `phase05_leakage_safe_manifest_v3_candidate.ipynb`
- **Promotion & Closure Notebook (Part 1E Final):**
  `phase05_manifest_v3_promotion_and_leakage_closure.ipynb`
- **Phase-Local Reproduction Code:**
  - `code/phase05_leakage_audit.py`: Standalone multi-level audit script.
  - `code/phase05_leakage_visualization.py`: Generates diagnostic audit figures.
  - `code/phase05_duplicate_adjudication.py`: Standalone Part 1B adjudication and sensitivity script.
  - `code/phase05_closure_figures.py`: Generates the four Part 1E closure figures.
  - `code/build_phase05_closure_nb.py`: Builds the promotion/closure notebook.
  - `code/execute_phase05_closure_nb.py`: Executes the closure notebook and reports stats.
  - `code/build_phase05_promotion_audit.py`: Builds the promotion audit + rerun scope.
  - `code/README.md`: Directory documentation.
- **Output Tables & Audits:**
  - `reports/tables/phase05_leakage_summary.csv`
  - `reports/tables/phase05_duplicate_pairs.csv`
  - `reports/tables/phase05_kub_exact_collision_forensics.csv`
  - `reports/tables/phase05_train_val_candidate_adjudication.csv`
  - `reports/tables/phase05_downstream_impact_matrix.csv`
  - `reports/tables/phase05_busi_patient_group_mapping.csv`
  - `reports/tables/phase05_clean_rerun_scope.csv`
  - `reports/audits/phase05_leakage_audit.json` / `phase05_leakage_audit.md`
  - `reports/audits/phase05_part1b_adjudication.json` / `phase05_part1b_adjudication.md`
  - `reports/audits/phase05_v3_promotion_audit.json` / `phase05_v3_promotion_audit.md`
- **Canonical Promoted Manifest:**
  - `manifests/phase4_v3/` (train 5832 / val 808 / test 1683 / quarantined 118)
  - `manifests/manifest_registry.json` / `manifests/manifest_registry.md`
- **Adjudication & Closure Figures:**
  - `reports/figures/phase05_leakage_audit/adjudication/phase05_kub_exact_collision_forensics.png`
  - `reports/figures/phase05_leakage_audit/adjudication/phase05_train_val_adjudication_page*.png`
  - `reports/figures/phase05_leakage_audit/closure/phase05_closure_v2_vs_v3_population.png`
  - `reports/figures/phase05_leakage_audit/closure/phase05_closure_quarantine_breakdown.png`
  - `reports/figures/phase05_leakage_audit/closure/phase05_closure_leakage_gate_matrix.png`
  - `reports/figures/phase05_leakage_audit/closure/phase05_closure_governance_flow.png`

## 5. Next Phase
- **Phase 06 — Descriptive Dataset Analysis (clean-v3 refresh)** — DO NOT START.
  Awaiting separate supervisor authorization.
- **Governance rule:** all future development uses `phase4_v3`. Historical Phases 06–15
  retain `phase4_v2` provenance and must not be silently presented as clean-v3 results.
