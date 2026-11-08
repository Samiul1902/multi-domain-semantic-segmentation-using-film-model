# FINAL NOTEBOOK QA — ReMedFiLM Consolidation

**Date:** 2026-11-08
**Deliverable root:** `D:\Softfors\jup\full_doc_report`
**Master notebook:** `ReMedFiLM_Complete_Research_Master.ipynb`
**SHA-256:** `2627a57dbf9b34b2de3accb7ef184dfae54b18aa4c2de9a697af378cfbaef1d9`
**Status:** `REMEDFILM_RESEARCH_MASTER_NOTEBOOK_COMPLETE__ANALYSIS_ONLY__NO_RETRAINING`

Verification suite: **19/19 checks passed** (`FINAL_QA_CHECKS.json`).

---

## 1. Notebook completeness

| Requirement | Result |
|---|---|
| Every relevant source notebook copied unchanged | **PASS** — 140 / 140 byte-identical (`NOTEBOOK_PRESERVATION_MANIFEST.json`) |
| Represented in the inventory | **PASS** — 418 rows; 140 `SOURCE_OF_TRUTH`, 140 `PRESERVED_SOURCE`, 4 `DELIVERABLE`, 134 `ARCHIVED_SUPERSEDED` |
| Incorporated into the master or linked | **PASS** — each source maps to a section in `NOTEBOOK_MERGE_MANIFEST.json` as `PRESERVED_SOURCE_ONLY` |
| Accounted for in the merge manifest | **PASS** — 18 sections, 140 sources, duplicates and exclusions listed |
| Duplicates reported | **PASS** — identical-SHA groups flagged `DUPLICATE_FILE(n)` |
| Intentionally excluded reported | **PASS** — 134 superseded copies archived with a README |

### Why source notebooks are preserved rather than merged

The 140 sources contain executable `trainer.train(...)`, `optimizer.step(...)` and
inference cells. Copying them into a single notebook would either execute training
or require deleting the code — both forbidden. They are therefore preserved
byte-identically and referenced by section. The master rebuilds their *analysis*
from persisted artifacts instead.

---

## 2. Epoch-history verification

| Check | Result |
|---|---|
| History files recovered | **82** |
| Long-form epoch records | **35,764** |
| Duplicated `(run, metric, epoch)` records | **0** |
| Registry covers every history file | **PASS** — 82 / 82 |
| Epoch contiguity | **PASS** — every log is gap-free and duplicate-free |
| Selection provenance labelled | **PASS** — `best_epoch_source` distinguishes `RECORDED_*` from `DERIVED_*` |

### Training-history completeness per model

| Model family | Runs | Epoch records | Metrics logged |
|---|---|---|---|
| R_psi (Regional Refiner) | 21 | 6,476 | 9 |
| B_phi (Benefit Router) | 13 | 4,649 | 4 |
| KUB baseline (U-Net family) | 6 | 4,349 | 11 |
| S_omega (Post-Safety Gate) | 18 | 3,407 | 4 |
| U-Net (four-domain) | 3 | 3,050 | 31 |
| KUB localiser (ROI proposal) | 8 | 2,592 | 9 |
| Transformer/MiT-style U-Net | 1 | 1,958 | 22 |
| **GlobalMedFiLM (G)** | **1** | **1,863** | **23** |
| Attention U-Net | 1 | 1,738 | 22 |
| DeepLabV3+ | 1 | 1,584 | 22 |
| U-Net++ | 1 | 1,540 | 22 |
| KUB localiser (H2/H3) | 4 | 1,848 | 8 |
| Regional refiner precursor | 1 | 426 | 6 |
| F1 ablation variant | 3 | 284 | 4 |

GlobalMedFiLM logged **23 distinct metrics at every one of its 81 epochs**,
including per-domain Dice, IoU, precision and recall. That is why Section 05 can
show genuine per-domain learning curves rather than reconstructions.

### Honest gaps

| Gap | Consequence |
|---|---|
| 14 runs have no per-epoch selection record | Marked `NOT_RECORDED` (8 KUB localiser diagnostics) or `NOT_APPLICABLE` (6 fixed-epoch refits). No value imputed. |
| `B_phi` and `S_omega` logs carry only 4 metrics | No Dice/IoU curve exists for these components; only their selection loss. |
| GlobalMedFiLM trained **once** | Seeds 123/3407 re-fit downstream components on a shared frozen backbone. Figure T7 states this explicitly; they are never drawn as three independent backbone trainings. |
| Phase 35 interpretability | Scientific execution NOT_STARTED — reported as such, no figure fabricated. |

---

## 3. Visual correctness

| Check | Result |
|---|---|
| ReMedFiLM FULL appears in every applicable comparison | **PASS** — model comparison table (7 rows incl. FULL), EFF01 has its own star marker, I1/I2/SEG show both systems |
| GlobalMedFiLM identified as backbone | **PASS** — labelled "GlobalMedFiLM (G) · BACKBONE" in A02, I1, EFF01 |
| Segmentation masks match source images | **PASS** — GT taken from the evaluation `.npz`, images aspect-resized and centre-padded to 512 to match the frozen contract |
| Training curves reflect genuine logs | **PASS** — all from `history.csv`; no interpolation |
| Missing metrics filled with invented values | **PASS** — none; absent metrics have no curve |
| Outdated labels | **PASS** — the stale 0.837862 value is replaced and the correction disclosed |
| External cohorts represented separately | **PASS** — CVC 612 / BrEaST 252 / Stones 20 never pooled |
| Incompatible populations pooled | **PASS** — VAL808, ROUTER_DEVELOPMENT 4,957 and ROUTER_HOLDOUT 875 are kept apart in every table and figure |
| Unsupported significance labels | **PASS** — only bootstrap CIs are shown; A8 vs A7 is labelled *includes zero* |

**Figures:** 41 total, each with a 300 dpi PNG and an SVG twin, in exactly the 12
required sub-directories.

| Sub-directory | Figures |
|---|---|
| architecture | 3 |
| datasets | 3 |
| training_epochs | 8 |
| internal_evaluation | 4 |
| subgroups | 2 |
| segmentation | 5 |
| external_evaluation | 3 |
| progression | 2 |
| ablation | 3 |
| routing_safety | 2 |
| robustness | 3 |
| efficiency | 3 |

---

## 4. Execution verification

`NOTEBOOK_EXECUTION_REPORT.json`

| Notebook | Code cells | Executed | Errors |
|---|---|---|---|
| `ReMedFiLM_Complete_Research_Master.ipynb` | 61 | **61** | **0** |
| `notebooks_generated/01_remedfilm_training_history_forensics.ipynb` | 8 | **8** | **0** |
| `notebooks_generated/02_remedfilm_ablation_and_routing_analysis.ipynb` | 8 | **8** | **0** |
| `notebooks_generated/03_remedfilm_external_and_robustness_analysis.ipynb` | 8 | **8** | **0** |
| **Total** | **85** | **85** | **0** |

Kernel: `remedfilm-analysis` → `D:\Softfors\jup\.venv\Scripts\python.exe`
(launched from a native Windows parent; a known `tsbx.dll` fault breaks direct
MSYS2-parent launches on this host).

### Guard enforcement

Section 00 installs a `sys.addaudithook` plus runtime patches. Four negative
controls execute on every run and must all report `blocked`, otherwise the
notebook aborts:

```
optimiser construction      : blocked
AdamW construction          : blocked
TEST manifest read          : blocked
write outside report dir    : blocked
All negative controls blocked. Analysis-only enforcement verified.
```

The guard is enforcement, not a flag: `torch.optim.Adam/AdamW/SGD` are replaced by
raising callables, `Module.train(True)` raises, and the audit hook intercepts
`open()` and every process-launch event.

**Limits of the guard (stated plainly):** it cannot prevent a determined analyst
from re-implementing an optimiser by hand, and it blocks the TEST *manifest* by
path rather than every possible TEST image path. It prevents accidental
execution, which is the actual risk in an analysis notebook.

---

## 5. Filesystem integrity

`FILESYSTEM_INTEGRITY.json`

| Check | Result |
|---|---|
| Original notebooks modified | **0** — 140 preserved copies re-hash identical |
| Frozen checkpoints modified | **0** |
| Original experiments modified | **0** |
| `git status` on `src/ tests/ manifests/ checkpoints/ configs/ reports/audits/` | **clean** |
| Training started | **NO** |
| New inference performed | **NO** |

### Disclosed deviation

One **metadata read** of `manifests/phase4_v3/test.csv` was performed during
consolidation to prove VAL/TEST `sample_id` disjointness (result: **0 overlap**,
VAL 808 vs TEST 1,683). Only the `dataset` and `sample_id` columns were counted.
No TEST image, mask, prediction or per-sample value was opened. The executed
notebooks cannot read that file — the guard blocks it.

---

## 6. Scientific corrections

`SCIENTIFIC_CORRECTIONS.json`

Four corrections are registered in `SCIENTIFIC_CORRECTIONS.json`. Three of them
are present in the current **V7** report, which therefore **must not be
republished unchanged**.

| ID | Field | V7 / prior value | Corrected | Basis |
|---|---|---|---|---|
| CORR-01 | ReMedFiLM FULL VAL808 macro Dice (seed 42) | `83.79%` (`0.837862`) | **`83.729%`** (`0.837290`) | Phase 27 Δ `+0.0022101`; Phase 29 continuity `0.8372891053`; independent re-scoring (agreement `1.8×10⁻⁷`) |
| CORR-02 | Net gain over backbone | `+0.28 pp` | **`+0.2210 pp`** | recomputed from CORR-01 |
| CORR-03 | ReMedFiLM analytical compute | `34.72 GMACs` | **`32.4379 GMACs`** (expected conditional) | `c2_barr_aggregate.json` |
| CORR-04 | Seed-42 Dice, second safety variant | `0.8373512` (n_accepted 268) | `0.8372891` (n_accepted 266, canonical) | Phase 27 + Phase 29 continuity |

**CORR-03 matters most for the efficiency claim.** `34.72` is the always-refine
cost. The deployed system routes only 24.3 % of cases, so its expected cost is
`31.5517 + 0.2431 × 3.646 = 32.4379` GMACs. Quoting 34.72 overstates the proposed
system's compute by 7.0 % and understates its efficiency advantage.

The old accuracy–compute figure omitted ReMedFiLM entirely;
`figures/efficiency/EFF01_accuracy_vs_compute.png` now plots it as its own marked
star at 32.44 expected conditional GMACs.

**No new DOCX/PDF was generated.** Rebuilding the report is a separate authorised
task; republishing with the stale charts is prohibited, and the older report
files are preserved untouched.

---

## 7. Remaining evidence gaps

| Gap | Status | Why it matters |
|---|---|---|
| C1 FiLM attribution (learned vs identity) | `NOT_ESTABLISHED` — 0/6 runs | The central causal claim is untested |
| C2 controlled component attribution | `NOT_ESTABLISHED` | A8 vs A7 CI includes zero; A1→A8 is confounded |
| C3 eight-model × three-seed benchmark | `NOT_ESTABLISHED` — 24/24 cells missing | No independent multi-seed baseline matrix |
| Prospective independent external cohort | `NOT_ESTABLISHED` | All external evidence is retrospective |
| TEST comparative endpoint | `NOT_ESTABLISHED` | One-shot access consumed; descriptive only |
| BUSI / polyp subgroup labels | `NOT_RECORDED` | Subgroup analysis limited to KUB |
| Full-pipeline latency | `NOT_RECORDED` | Only forward-only GPU timing exists |

---

## 8. Reproduction

```bat
cd /d D:\Softfors\jup
.venv\Scripts\python.exe full_doc_report\Scripts\build_inventory.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_preserve.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_training_history.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_metrics.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_tables_extra.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_figures.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_notebook.py
.venv\Scripts\python.exe full_doc_report\Scripts\build_supplementary.py
.venv\Scripts\python.exe full_doc_report\Scripts\execute_notebooks.py
.venv\Scripts\python.exe full_doc_report\Scripts\finalize.py
.venv\Scripts\python.exe full_doc_report\Scripts\verify.py
```

---

## 9. Declaration

No model was retrained. No new inference was run. No frozen scientific evidence
was modified. TEST1683 was not reopened. ReMedFiLM FULL is the proposed method
throughout, with GlobalMedFiLM explicitly identified as its backbone.

```text
REMEDFILM_RESEARCH_MASTER_NOTEBOOK_COMPLETE__ANALYSIS_ONLY__NO_RETRAINING
```
