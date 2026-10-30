# Phase 06 — KUB Dataset Characterization (`phase_06_kub_characterization`)

## Final Status: **PART 1A-R1 COMPLETE**

- **Active development manifest:** `phase4_v3`
- **Historical manifest:** `phase4_v2`
- **Scope:** clean-v3 KUB descriptive characterization (TRAIN + VAL)
- **TEST medical content:** never accessed (0 reads / 0 visualizations / 0 metrics)

## 1. Scientific Overview
- **Phase ID:** `phase_06_kub_characterization`
- **Scientific Title:** KUB Dataset Characterization — Clean-v3 Development Population + Geometry
- **Core Question:** What are the empirical population, patient, anatomical, acquisition, and image/object-geometry properties of the clean-v3 KUB development split, and how do they differ between TRAIN and VAL?
- **This phase does NOT:** define a tiny-object threshold (Phase 07 does), train a model, run inference, or perform hypothesis testing.

## 1b. Part 1A-R1 Repair Scope
Targeted repair of Part 1A. The computed geometry was accepted and unchanged.
Fixed: (a) an unsupported "descriptively similar" TRAIN/VAL claim, (b) missing
stratified geometry summaries, (c) table-registry consistency, (d) gallery
presentation. **No population, manifest, or split membership was changed.**

- Pre-repair notebook SHA: `488af85c93ba6c986a13b57def06db94adfac7e0f26c965e2ace42f63edfe7d2`
- Post-repair notebook SHA: `c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888`

## 2. Governance Boundary
- Uses KUB medical content from `manifests/phase4_v3/train.csv` and `val.csv` only.
- TEST referenced through **manifest metadata only** (counts / IDs).
- No manifest modified. No Phase-05 artifact modified.
- **Mask foreground rule:** `mask > 0` (binary). See section 4.

## 3. Population (clean-v3)
| Split | Cases | Unique patients |
|---|---:|---:|
| KUB TRAIN | 1978 | 318 |
| KUB VAL | 280 | 111 |
| KUB TEST (metadata only) | 558 | — |
| KUB QUARANTINED | 4 | — |

TRAIN/VAL sample overlap = 0 · TRAIN/VAL patient overlap = 0.

## 4. Key Finding — Mask Label Vocabulary

KUB masks use a **heterogeneous, category-correlated nonzero label vocabulary**.
Every nonzero value is foreground under the binary target semantics `mask > 0`.

| Label signature | Cases | Dominant category |
|---|---:|---|
| `{0,255}` | 1385 | all categories |
| `{0,1}` | 465 | Kidney_Stone |
| `{0,2}` | 304 | Bladder_Stone |
| `{0,3}` | 101 | Ureteric_Stone |
| `{0,1,2}` | 3 | Bladder_Stone |

> **Downstream governance.** All CLEAN-v3 KUB segmentation loaders and
> target-generation code must binarize the native mask as **`(mask > 0)`**.
> Phase 08 infrastructure must unit-test this invariant before clean model
> training. Downstream code must **NOT** assume `mask == 1`.

## 5. Key Finding — Two Acquisition Regimes

| Acquisition | Cases | Distinct resolutions | Width min/median/max | Image mode |
|---|---:|---:|---|---|
| FULL_FIELD | 873 | 35 | 1476 / 2304 / 3096 | RGB |
| ROI | 1385 | 1199 | 41 / 83 / 495 | L (single-channel) |

Combined-development quantiles are therefore **mixture statistics** and must be
read with the stratified summaries.

## 6. Descriptive TRAIN-vs-VAL Differences (not significance claims)

| Quantity | TRAIN | VAL | Difference |
|---|---|---|---|
| Kidney_Stone | 57.28% | 40.00% | 17.28 pp |
| Bladder_Stone | 32.05% | 51.43% | **19.38 pp (max)** |
| Ureteric_Stone | 10.67% | 8.57% | 2.10 pp |
| ROI acquisition | 61.07% | 63.21% | **2.14 pp (max)** |
| Multi-component masks | 10.72% | 17.50% | +6.78 pp |
| Cases per patient (median) | 5 | 3 | — |

TRAIN and VAL are **patient-disjoint but not compositionally identical**,
especially in anatomical-category proportions. This does **not** invalidate the
frozen v3 split.

## 7. Reviewer Deliverables
- **Primary notebook:** `phase06_kub_dataset_characterization_clean_v3.ipynb`
- **Reusable module:** `code/phase06_kub_characterization.py`
- **Driver:** `code/run_phase06_characterization.py`
- **Helpers:** `code/build_phase06_notebook.py`, `code/execute_phase06_notebook.py`, `code/finalize_phase06_audit.py`
- **Tables:** `reports/tables/phase06_kub_v3_*.csv` (12 artifacts)
- **Figures:** `reports/figures/phase06_kub_characterization/*.png` (16 figures, incl. 4 gallery pages)
- **Audit:** `reports/audits/phase06_kub_v3_characterization_audit.json` / `.md`

## 8. Explicit Limitations
- KUB TRAIN/VAL development data only; TEST medical content locked.
- Geometry depends on the available binary masks.
- Kidney / Bladder / Ureteric are **metadata**, not pixel-level multiclass targets.
- TRAIN and VAL are patient-disjoint but show anatomical composition imbalance.
- Combined-development quantiles are mixture statistics across ROI and FULL_FIELD regimes.
- Phase-07 threshold derivation must avoid VAL-driven threshold tuning.
- Descriptive distributions do **not** define "tiny".
- Phase 07 defines the prospective tiny-object criterion.

## 9. Phase-07 Governance Constraint

> Phase 07 must **NOT** choose a tiny-object threshold by optimizing against VAL.
> The prospective tiny-object definition must be **frozen using TRAIN-only
> empirical geometry and/or predeclared domain/geometric rationale** before
> examining VAL prevalence/results under that threshold. VAL may then be used for
> evaluation/characterization after the freeze. **No threshold is defined yet.**

## 10. Next Phase
- **Phase 07 — Object Size Taxonomy** (NOT STARTED: awaiting supervisor final review of Phase 06).

