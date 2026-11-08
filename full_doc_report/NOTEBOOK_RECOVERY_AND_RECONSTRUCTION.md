# Notebook Recovery and Reconstruction

**Repository:** `D:\Softfors\jup`
**Deliverable root:** `full_doc_report\`
**Date:** 2026-11-08

---

## 1. What was scanned

| Quantity | Count |
|---|---|
| Phase directories under `notebooks/phasewise` | **57** |
| `.ipynb` files inside them | **108** |
| Phase directories with ≥ 1 notebook | 45 |
| Phase directories with **no** notebook | **12** |
| Additional notebooks elsewhere in the repository | 32 (`reports/audits`, `.workbuddy-ai`) |
| Total genuine source notebooks | **140** |

Every directory is listed in `PHASEWISE_NOTEBOOK_COVERAGE.csv` with a status, an
implementation status, an experiment status, and a documented resolution.

---

## 2. Classification result

| Status | Phases |
|---|---|
| `NOTEBOOK_COMPLETE` | 45 |
| `NOTEBOOK_MISSING_RESULTS_EXIST` | 8 |
| `DOCUMENTATION_ONLY_PHASE` | 3 |
| `REQUIRES_HUMAN_AUTHORIZATION` | 1 |
| `NOTEBOOK_PRESENT_BUT_BROKEN` | 0 |
| `NOTEBOOK_PRESENT_BUT_OBSOLETE` | 0 |

No notebook was found with invalid JSON, no executable cells, or a majority of
unresolvable absolute paths. The 45 existing notebooks are structurally sound.

---

## 3. The 12 directories without a notebook

### 3.1 Reconstructed (8) — implementation **and** results exist

| Phase | Folder | Evidence used | Generated notebook |
|---|---|---|---|
| 09 | `phase_09_clean_v3_baseline` | 28 tables, 4 epoch histories | `phase09_clean_v3_baseline_reconstructed.ipynb` |
| 10 | `phase_10_clean_v3_comparison` | 101 tables, paired per-case metrics | `phase10_clean_v3_comparison_reconstructed.ipynb` |
| 24 | `phase_24_ra_medfilm_design` | 45 audits, module/router/ablation specs | `phase24_architecture_spec_reconstructed.ipynb` |
| 25 | `phase_25_ra_medfilm_dev` | 347 audits, 133 tables, component histories | `phase25_component_development_reconstructed.ipynb` |
| 26 | `phase_26_full_four_domain_training` | component inventory, bundle + state-machine tests | `phase26_full_system_integration_reconstructed.ipynb` |
| 30 | `phase_30_final_dev_val` | ROUTER_HOLDOUT non-inferiority result | `phase30_holdout_validation_reconstructed.ipynb` |
| 36 | `phase_36_robustness_perturbation` | 12,928 perturbation rows | `phase36_robustness_perturbation_reconstructed.ipynb` |
| 40 | `phase_40_publication_reproducibility_audit` | numeric-provenance and claim-scope audits | `phase40_reproducibility_audit_reconstructed.ipynb` |

Each imports the real artifact set, shows genuine tables and figures, and states
the historical execution status. None contains invented results.

### 3.2 Documentation only (3) — no evidence exists

| Phase | Folder | Reason |
|---|---|---|
| 16 | `phase_16_fusion` | superseded before execution; no artifacts |
| 17 | `phase_17_kub_regional_ablation` | superseded by clean-v3 / Phase 28 |
| 18 | `phase_18_kub_final_dev_benchmark` | replaced by VAL808 and ROUTER_HOLDOUT |

Each receives a `PHASE_INDEX.md` explaining why no notebook is appropriate.
Generating a notebook with no data to analyse would be fabrication.

### 3.3 Authorization-gated (1) — deliberately **not** reconstructed

| Phase | Folder | Reason |
|---|---|---|
| 39 | `phase_39_untouched_test_evaluation` | one-shot TEST1683 access consumed |

A notebook here would have to open the TEST manifest, images or predictions.
Instead, `PHASE_INDEX.md` explains the constraint, and the descriptive result is
read from the frozen summary in
`ReMedFiLM_Research_Notebooks/12_ReMedFiLM_Historical_Test_Evidence.ipynb`.

---

## 4. Preservation

`Original_Phasewise_Notebooks/` mirrors the phasewise tree exactly.

| Check | Result |
|---|---|
| Notebooks copied | 108 |
| SHA-256 verified byte-identical | **108 / 108** |
| Originals moved or deleted | **0** |
| Manifest | `Original_Phasewise_Notebooks/PRESERVATION_MANIFEST.json` |

The repo-wide preservation set (`notebooks_original/`, 140 notebooks) is also
retained. Embedded outputs in preserved copies are historical artifacts and are
not evidence that a run happened during this task.

---

## 5. Repairs applied to generated copies

| Defect class | Handling |
|---|---|
| Missing `matplotlib` import | added to the shared notebook bootstrap |
| Undefined `reg` in notebook 03 | registry loaded before use |
| Broken parameter arithmetic | replaced with a corrected derived table (see §6) |
| Stale figure paths | all figures regenerated under the 11 requested directories |
| Missing kernel metadata | every notebook carries an explicit `kernelspec` and a `remedfilm` metadata block |
| Repeated initialisation | one shared bootstrap cell per notebook |

No frozen algorithm, protocol or experiment definition was altered to make a
notebook execute.

---

## 6. Genuine defects found in frozen artifacts

### DEFECT-01 — units error in `phase26_component_inventory.csv`

```
column : parameters
row    : G
stored : 31,551,740,928
actual :  3,523,001
```

The stored value equals G's **total MACs**
(`phase21_analytical_mac_count.json → total_macs`), not its parameter count. Any
sum over that column overstates the system by ~31.5 billion and cannot reconcile
to 4,837,420.

The frozen table is **not modified**. A corrected derived table,
`tables/REMEDFILM_COMPONENT_PARAMETERS.csv`, is used instead, and every notebook
asserts that the component sum equals the Phase 34 contract total.

### CORR-01..04 — reported values that do not match any frozen artifact

| ID | Reported | Verified | Basis |
|---|---|---|---|
| CORR-01 | 83.79 % / 0.837862 | **0.837290** | Phase 27 Δ, Phase 29 continuity, re-scored masks (agreement 1.8e-07) |
| CORR-02 | +0.28 pp | **+0.2210 pp** | recomputed |
| CORR-03 | 34.72 GMACs | **32.4379** | `c2_barr_aggregate.json` |
| CORR-04 | 0.8373512 (268 accepted) | 0.8372891 (266 accepted) | canonical continuity record |

Full register: `SCIENTIFIC_CORRECTIONS.json`. V7 must not be republished unchanged.

---

## 7. Supersession

The previous phase-ordered consolidation (`ReMedFiLM_Complete_Research_Master.ipynb`
plus three supplements) is retained unchanged in
`_prior_consolidation_archive/v1_phase_ordered/`. It is superseded by the
workflow-organised set:

* `ReMedFiLM_COMPLETE_MASTER.ipynb` — 17 sections, 59 code cells
* `ReMedFiLM_Research_Notebooks/` — 12 dedicated notebooks
* `Reconstructed_Phasewise_Notebooks/` — 8 notebooks + 4 phase indexes

Nothing was deleted.

---

## 8. Reproduction

```bat
cd /d D:\Softfors\jup
.venv\Scripts\python.exe full_doc_report\Scripts\build_inventory.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_phase_inventory.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_training_history.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_metrics.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_tables_extra.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_component_parameters.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_required_tables.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_figures.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_phase_notebooks.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_remedfilm_notebooks.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_complete_master.py
.venv\Scripts\python.exe full_doc_report\Scripts\execute_notebooks.py
.venv\Scripts\python.exe full_doc_report\Scripts\finalize_reconstruction.py
.venv\Scripts\python.exe full_doc_report\Scripts\verify_reconstruction.py
```

On this host the canonical interpreter must be launched from a native Windows
parent — a known `tsbx.dll` fault breaks direct MSYS2-parent launches. Every
command above was run that way.
