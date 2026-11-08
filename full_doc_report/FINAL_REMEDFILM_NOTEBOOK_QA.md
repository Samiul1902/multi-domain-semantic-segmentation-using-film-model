# FINAL — ReMedFiLM Notebook QA

**Deliverable root:** `D:\Softfors\jup\full_doc_report`
**Master notebook:** `ReMedFiLM_COMPLETE_MASTER.ipynb`
**SHA-256:** `1c818245a15515a2a568f4b61471c130bab10412d54bc11580b15773ba3a9550`
**Date:** 2026-11-08

Verification: **36 / 36 checks passed** (`FINAL_QA_CHECKS.json`).

---

## 1. Phase inventory

| Quantity | Count |
|---|---|
| Phase directories inspected | **57** |
| `.ipynb` found inside them | **108** |
| Directories with a notebook | 45 |
| Directories without a notebook | **12** |
| Notebooks elsewhere in the repo | 32 |
| Total genuine source notebooks | **140** |

| Status | Phases |
|---|---|
| `NOTEBOOK_COMPLETE` | 45 |
| `NOTEBOOK_MISSING_RESULTS_EXIST` | 8 |
| `DOCUMENTATION_ONLY_PHASE` | 3 |
| `REQUIRES_HUMAN_AUTHORIZATION` | 1 |
| `NOTEBOOK_PRESENT_BUT_BROKEN` | **0** |
| `NOTEBOOK_PRESENT_BUT_OBSOLETE` | **0** |

Every row of `PHASEWISE_NOTEBOOK_COVERAGE.csv` carries a `verification_status`
of `PRESERVED_EXECUTION_NOT_REQUIRED`, `GENERATED_AND_EXECUTED`,
`DOCUMENTED_NO_NOTEBOOK_APPROPRIATE`, or `GATED_NOT_REOPENED`. No row is left
`PENDING`.

---

## 2. Preservation

| Check | Result |
|---|---|
| Phasewise notebooks copied | 108 |
| Byte-identical (SHA-256) | **108 / 108** |
| Originals moved or deleted | **0** |
| Manifest | `Original_Phasewise_Notebooks/PRESERVATION_MANIFEST.json` |
| Repo-wide preservation set | `notebooks_original/` (140) |

Embedded outputs in preserved copies are historical artifacts, not evidence that
a run occurred during this task.

---

## 3. Notebooks delivered

| Set | Count | Code cells | Executed |
|---|---|---|---|
| `ReMedFiLM_COMPLETE_MASTER.ipynb` | 1 | 59 | 59 |
| `ReMedFiLM_Research_Notebooks/` (01–12) | 12 | 106 | 106 |
| `Reconstructed_Phasewise_Notebooks/` | 8 | 60 | 60 |
| **Total** | **21** | **225** | **225** |

Zero errors. Zero skipped cells. Kernel `remedfilm-analysis` →
`D:\Softfors\jup\.venv\Scripts\python.exe`.

### The 12 dedicated notebooks

| # | Notebook | Focus |
|---|---|---|
| 01 | FULL Architecture | components, parameters, three outcomes, assembly ≠ joint training |
| 02 | Component Training | real recipe per component, dependency chain, checkpoint identity |
| 03 | Epoch-Wise Analysis | 35,764 records, T1–T8, `NOT_RECORDED` register |
| 04 | Internal Validation | backbone vs FULL, paired Δ, HD95, harm/benefit split |
| 05 | Segmentation Predictions | deterministic worst/median/best galleries |
| 06 | External Evaluation | 884 cases, stone-free negative result |
| 07 | Progression & Ablation | 5 stages, 13 arms, preserved null A8-vs-A7 |
| 08 | Error Propagation | grounded stage counts, prevented vs residual harm |
| 09 | Statistics & Reproducibility | 3 seeds, shared-backbone disclosure, no p-values |
| 10 | Robustness & Interpretability | 12,928 perturbations, KUB weakness |
| 11 | Accuracy vs Compute | **corrected** figure with ReMedFiLM plotted |
| 12 | Historical TEST | frozen summary only, access consumed |

---

## 4. Training-history recovery

| Quantity | Value |
|---|---|
| Per-epoch `history.csv` recovered | **82** |
| Genuine historical runs | **68** |
| Long-form epoch records | **35,764** |
| Runs without a selection record | 14 (`NOT_RECORDED` / `NOT_APPLICABLE`) |
| Runs without a recorded seed | 3 (F1 folds — `NOT_RECORDED`) |

Verified: run IDs unique · model identities resolved · epoch ordering correct ·
no duplicated records · no invented/gap epochs · best epoch matches saved closure
metadata · synthetic fixtures absent.

GlobalMedFiLM is the only component with a complete four-domain log:
**81 epochs × 23 metrics**, including per-domain Dice/IoU/precision/recall.

---

## 5. Scientific corrections

`SCIENTIFIC_CORRECTIONS.json`

| ID | Reported | Verified | Basis |
|---|---|---|---|
| CORR-01 | 83.79 % (0.837862) | **0.837290** | Phase 27 Δ + Phase 29 continuity + re-scored masks (agreement 1.8×10⁻⁷) |
| CORR-02 | +0.28 pp | **+0.2210 pp** | recomputed |
| CORR-03 | 34.72 GMACs | **32.4379** expected conditional | `c2_barr_aggregate.json` |
| CORR-04 | 0.8373512 | 0.8372891 | canonical continuity record |
| DEFECT-01 | `parameters[G] = 31,551,740,928` | **3,523,001** | value is G's MACs, not parameters |

`DEFECT-01` is a genuine units bug in the frozen
`phase26_component_inventory.csv`. The frozen file is **not modified**; a
corrected derived table (`tables/REMEDFILM_COMPONENT_PARAMETERS.csv`) is used and
every notebook asserts the sum equals 4,837,420.

**V7 must not be republished unchanged.** No new DOCX/PDF was generated.

---

## 6. Model identity

| Name | Composition | Parameters | Role |
|---|---|---|---|
| Baselines | U-Net, Att-UNet, UNet++, DeepLabV3+, Transformer/MiT | 7.76 M – 40.35 M | comparators |
| **GlobalMedFiLM (G)** | task-conditioned FiLM backbone | 3,523,001 | **backbone / ablation comparator** |
| **ReMedFiLM FULL** | G + B_phi + R_psi + S_omega | **4,837,420** | **proposed system** |

Verified: FULL appears as its own identity in every comparison table and figure;
no backbone row is labelled ReMedFiLM; component arithmetic closes exactly.

The assembly is documented as **sequential, not joint**: no optimiser ever saw all
four components at once.

---

## 7. Execution guard

Every notebook installs a `sys.addaudithook` plus runtime patches, then runs four
negative controls that must all print `blocked`:

```
optimiser construction      : blocked
AdamW construction          : blocked
TEST manifest read          : blocked
write outside report dir    : blocked
```

Verified in **21 / 21** notebooks. The guard is enforcement, not a flag.

**Stated limits:** it stops accidental execution, not a determined analyst
re-implementing an optimiser by hand, and it blocks the TEST *manifest* by path
rather than every conceivable TEST image path.

---

## 8. Figures and tables

| Item | Count |
|---|---|
| Figures (300 dpi PNG + SVG) | **45** |
| Figure directories (11 required) | 11 + 0 extras |
| Tables | 22 |

| Directory | Figures |
|---|---|
| Architecture | 3 |
| Training curves | 8 |
| Internal validation | 6 |
| Semantic segmentation | 5 |
| External evaluation | 3 |
| Ablation | 3 |
| Progression | 2 |
| Routing and safety | 2 |
| Statistics | 7 |
| Robustness | 3 |
| Efficiency | 3 |

`REPORT_NOTEBOOK_FIGURE_MAPPING.csv` maps all 45 to notebook section, generating
function, scientific source, model configuration and evidence class.

**The accuracy–compute figure now plots ReMedFiLM FULL as its own star marker at
32.44 expected conditional GMACs** — the omission that recurred in earlier
reports is fixed.

---

## 9. Integrity

| Check | Result |
|---|---|
| Original notebooks modified | 0 |
| Frozen checkpoints modified | 0 |
| Original experiments modified | 0 |
| `git status` on `src/ tests/ manifests/ checkpoints/ configs/ reports/audits/` | **clean** |
| Training performed | **NO** |
| New inference performed | **NO** |
| TEST manifest read by any executed notebook | **NO** |

### Disclosed deviation

One metadata read of `manifests/phase4_v3/test.csv` occurred during an earlier
consolidation step to prove VAL/TEST `sample_id` disjointness (result: **0
overlap**). Only `dataset` and `sample_id` were counted; no TEST image, mask,
prediction or per-sample value was opened. The delivered notebooks cannot read
that file — the guard blocks it and verification confirms zero attempts.

---

## 10. Evidence gaps (unchanged by this work)

| Gap | Status |
|---|---|
| C1 learned vs identity FiLM | `NOT_ESTABLISHED` — 0/6 runs |
| C2 controlled causal attribution | `NOT_ESTABLISHED` — A8 vs A7 CI includes 0 |
| C3 8-model × 3-seed benchmark | `NOT_ESTABLISHED` — 0/24 cells |
| Prospective independent external cohort | `NOT_ESTABLISHED` |
| TEST comparative endpoint | `NOT_ESTABLISHED` — access consumed |
| BUSI / polyp subgroup labels | `NOT_RECORDED` |
| Full-pipeline latency | `NOT_RECORDED` |

Details: `PENDING_CONTROLLED_EXPERIMENTS.md`.

---

## 11. Reproduction

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

---

## 12. Declaration

No model was retrained. No new inference was run. TEST1683 was not reopened. No
frozen research artifact was modified. ReMedFiLM FULL is the proposed system
throughout; GlobalMedFiLM is its backbone and an ablation comparator.

The three controlled experiments (C1/C2/C3) remain unexecuted and are reported as
such rather than simulated.

```text
REMEDFILM_NOTEBOOK_RECONSTRUCTION_PARTIAL__EVIDENCE_GAPS_DISCLOSED
```

The reconstruction itself is complete — 57/57 phases inventoried, 12/12 missing
notebooks resolved, 21/21 notebooks executed, 36/36 checks passed. The PARTIAL
status reflects **unexecuted science**, not missing notebook infrastructure.
