# ReMedFiLM — Research Notebook Index

**Repository:** `D:\Softfors\jup`
**Deliverable root:** `full_doc_report\`
**Execution mode:** `ANALYSIS_ONLY` — no training, no new inference, no TEST access.

---

## 1. What this index covers

The repository accumulated 140 genuine research notebooks across 40+ phases,
written over roughly two months. They contain executable training and inference
cells and are therefore **preserved but never executed** here. This index states
what was found, what was preserved, and how the consolidated notebook relates to
each source.

| Quantity | Count |
|---|---|
| `.ipynb` files scanned (excluding venv, caches, build copies) | 418 |
| Genuine source notebooks discovered | **140** |
| Preserved byte-identically in `notebooks_original/` | **140** |
| Deliverable notebooks (1 master + 3 supplementary) | **4** |
| Superseded copies from an earlier consolidation attempt | 134 (archived) |
| Per-epoch training logs recovered | **82** |
| Long-form epoch records | **35,764** |
| Figures generated | **41** (PNG 300 dpi + SVG) |
| Tables generated | **17** |

---

## 2. Source distribution

| Location | Notebooks | Nature |
|---|---|---|
| `notebooks/` | 131 | phase-wise research notebooks, Phases 00–43 |
| `reports/audits/` | 7 | pre-repair snapshots kept as provenance |
| `.workbuddy-ai/` | 2 | Phase 21 notebook, pre-repair and repaired revisions |

`notebooks/` spans 24 phase sub-directories. The heaviest are Phase 13 (51 files,
KUB localisation), Phase 35 (42, interpretability), Phase 14 (36, regional
refiner) and Phase 25 (31, BARR components).

---

## 3. Deliverable notebooks

### 3.1 Master

**`ReMedFiLM_Complete_Research_Master.ipynb`** — 81 cells (61 code, 20 markdown), 18 numbered sections.

| § | Section | Figures |
|---|---|---|
| 00 | Research environment and execution guard | — |
| 01 | Research overview | A01–A03 |
| 02 | Dataset analysis | D01–D03 |
| 03 | Full ReMedFiLM architecture | — |
| 04 | Historical training run inventory | — |
| 05 | Epoch-by-epoch training improvements | T1–T8 |
| 06 | Historical baseline comparison | — |
| 07 | ReMedFiLM internal evaluation | I1–I4 |
| 08 | Class and subclass evaluation | SG1–SG2 |
| 09 | Semantic segmentation gallery | SEG × 5 |
| 10 | External retrospective evaluation | EXT01–EXT03 |
| 11 | Component progression | PROG01–PROG02 |
| 12 | Complete ablation study | ABL01–ABL03 |
| 13 | Error propagation and routing | RT01–RT02 |
| 14 | Robustness and interpretability | ROB01–ROB03 |
| 15 | Computational efficiency | EFF01–EFF03 |
| 16 | Historical TEST evidence | — |
| 17 | Conclusions and missing evidence | — |

### 3.2 Supplementary

| Notebook | Focus | Cells |
|---|---|---|
| `notebooks_generated/01_remedfilm_training_history_forensics.ipynb` | epoch contiguity, duplicates, selection provenance, metric-completeness matrix | 8 code |
| `notebooks_generated/02_remedfilm_ablation_and_routing_analysis.ipynb` | 13-arm ablation, paired CIs, routing state machine | 8 code |
| `notebooks_generated/03_remedfilm_external_and_robustness_analysis.ipynb` | 884 external cases, stone-free failure, 12 perturbations | 8 code |

---

## 4. Model identity

The proposed method is **ReMedFiLM FULL**, the four-component assembly. This
distinction is enforced throughout:

| Name | Composition | Parameters | Role |
|---|---|---|---|
| U-Net, Attention U-Net, U-Net++, DeepLabV3+, Transformer/MiT | conventional baselines | 7.76 M – 40.35 M | comparators |
| **GlobalMedFiLM (G)** | task-conditioned FiLM backbone | 3,523,001 | **backbone / ablation comparator** |
| **ReMedFiLM FULL** | G + B_phi + R_psi + S_omega | 4,837,420 | **proposed method** |

No GlobalMedFiLM-only prediction or checkpoint is labelled ReMedFiLM.

---

## 5. Where the evidence lives

| Artifact | Path |
|---|---|
| Per-epoch logs (source of truth) | `experiments/*/history.csv` (82 files) |
| Run registry | `full_doc_report/tables/TRAINING_RUN_REGISTRY.csv` |
| Epoch history, long form | `full_doc_report/tables/REMEDFILM_EPOCH_HISTORY.csv` |
| Per-sample internal scores | `full_doc_report/tables/REMEDFILM_INTERNAL_PER_SAMPLE.csv` |
| VAL808 masks | `reports/figures/phase27_preservation/masks/` (1,616 files) |
| Six-model comparison | `reports/tables/phase21_six_model_comparison.csv` |
| 13-arm ablation | `reports/tables/phase28_table_02_arm_primary_metrics.csv` |
| External cohorts | `reports/tables/c1_external_stress_summary.csv` |
| Robustness | `reports/audits/phase36_robustness_scientific_result_v1_23.json` |
| Efficiency | `reports/audits/phase34_efficiency_result_v1_4.json` |

---

## 6. Known discrepancies and corrections

Full register: `SCIENTIFIC_CORRECTIONS.json` (4 entries).

1. **CORR-01 — ReMedFiLM FULL VAL808 macro Dice.** V7 reports `83.79%`
   (`0.837862`). Re-scoring the saved Phase 27 masks gives `0.837290`, matching
   the frozen Phase 27 delta (`+0.0022101`) and the Phase 29 continuity record
   (`0.8372891053`). `0.837862` appears in no frozen artifact.
2. **CORR-02 — net gain.** `+0.28 pp` becomes **`+0.2210 pp`**.
3. **CORR-03 — analytical compute.** V7 quotes `34.72 GMACs`, the always-refine
   cost. The deployed system routes 24.3 % of cases, so its expected conditional
   cost is **`32.4379 GMACs`**. The 34.72 figure overstates compute by 7.0 %.
4. **CORR-04 — two seed-42 safety variants.** `phase29_val808_seedwise_metrics.json`
   gives `0.8373512` (n_accepted 268); the continuity artifact gives `0.8372891`
   (n_accepted 266), which is canonical and reproduced by re-scoring.
5. **KUB unit of analysis.** 2,258 KUB manifest rows are 873 full-field images
   plus 1,385 ROI instance patches — not 2,258 independent images.
6. **14 runs without a recorded selection epoch** are KUB ROI-localiser
   diagnostics and fixed-epoch component refits. Marked `NOT_RECORDED` /
   `NOT_APPLICABLE`, never imputed.

**V7 must not be republished unchanged.** Its DOCX/PDF are preserved as-is; the
corrected values live in the tables and figures listed above.

---

## 7. Execution guard

Section 00 of the master installs a real `sys.addaudithook`, not a flag. Four
negative controls run on every execution and must all report `blocked`:

```
optimiser construction      : blocked
AdamW construction          : blocked
TEST manifest read          : blocked
write outside report dir    : blocked
```

The notebook aborts if any control passes.

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
```

On this host the canonical interpreter must be launched from a native Windows
parent (a known `tsbx.dll` fault breaks direct MSYS2-parent launches). Every
script above was run that way.
