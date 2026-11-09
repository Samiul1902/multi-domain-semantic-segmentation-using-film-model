# Project-Wide Notebook Visualization Standard (NV-1)

**Standard Version:** NV-1  
**Scope:** All past, current, and future modeling and evaluation phases in the KUB stone segmentation project.  
**Machine-Readable Spec:** [`reports/audits/notebook_visualization_standard.json`](file:///D:/Softfors/jup/reports/audits/notebook_visualization_standard.json)

---

## 1. Core Motivation & Principles

Scientific notebooks must communicate visual evidence directly to researchers and reviewers, not merely output summary tables, logs, or text metrics. For medical imaging tasks (specifically KUB abdominal radiograph stone detection and segmentation), visual validation provides indispensable confirmation of clinical plausibility, segmentation boundary sharpness, regional refiner localization quality, false positive patterns, and failure modes.

To ensure uniformity, scientific rigor, and prevent cherry-picking across all research phases, this document defines the binding visual evidence standard.

---

## 2. Governance & Immutability Rules

1. **Canonical Immutability:** Any historical notebook whose SHA-256 hash has been accepted and frozen (e.g., `notebooks/13_phase14_regional_refiner_diagnostic.ipynb`, SHA `b5b329d1...`) is strictly immutable. It must never be re-run, overwritten, or modified in place.
2. **Retrospective Companions:** Historical phases lacking complete visualization evidence are augmented via standalone companion notebooks placed in `notebooks/retrospective/`. These read-only companion notebooks consume frozen checkpoints and artifact tables to render visual evidence without altering historical findings.
3. **Prospective Enforcement:** All future and current modeling phases (beginning with Phase 15) must incorporate this visual standard into their primary execution notebooks prior to freeze.
4. **Test Set Lock:** Developing or inspecting visual results on the `TEST` split is strictly prohibited (`TEST reads = 0`, `TEST visualizations = 0`). All visual inspections during development must use `VAL` (or `TRAIN`) splits and be explicitly labeled as such.

---

## 3. Mandatory Notebook Visual Stages

Every modeling and evaluation notebook must include visual evidence covering the following lifecycle stages:

### A. Sample Data Inspection (Stage 1)
- **Cohort Size:** 8 to 12 representative cases rendered at the outset of the notebook.
- **Content:** Raw radiograph, ground truth segmentation contours/masks, bounding boxes (where applicable), and clinical metadata (patient/sample ID, FOV dimensions, stone count, stone size strata).
- **Purpose:** Verifies preprocessing, intensity normalization, aspect ratios, and mask integrity before modeling.

### B. Intermediate Pipeline Step-by-Step Visualization (Stage 2)
For multi-stage or composite architectures (e.g., CenterNet localizer + Regional Refiner):
- **Stage 4D Localizer Output:** Continuous CenterNet stone heatmap $[0, 1]$ and peak detections.
- **Proposal Generation:** Candidate bounding boxes overlaid on the radiograph, proposal union masks, and area burden.
- **Regional Refiner Input:** Cropped context-expanded ROIs.
- **Regional Prediction:** Crop-level probability maps and logits.
- **Canvas Restoration:** Inverse projection back onto the original radiograph coordinate space.

### C. Training Curves & Optimization Dynamics (Stage 3)
Mandatory for all training phases:
- **Loss Curves:** Training loss and validation loss vs. epoch.
- **Checkpoint Metric:** Monitoring metric (e.g., Val Object Recall@90 or Val Dice) vs. epoch.
- **Learning Rate Schedule:** Learning rate curve vs. step/epoch.
- **Milestones:** Visual markers indicating best checkpoint selection epoch, early stopping epoch, and any power-resume/warmup transitions.

### D. Aggregate Evaluation & Error Distributions (Stage 4)
Mandatory for all evaluation notebooks:
- **Metric Distributions:** Box plots and violin plots of Dice coefficients across samples.
- **Stratified Recall:** Object-level recall bar charts broken down by stone size strata (**Tiny** $<5\text{mm}$, **Small** $5-10\text{mm}$, **Medium** $10-20\text{mm}$, **Large** $\ge 20\text{mm}$).
- **False Positive Characterization:** Distribution of false positive components per image and area burden.
- **Ablation Comparisons:** Side-by-side bar/radar comparisons across loss functions or model variants.

### E. Standardized Error Maps & Detailed Predictions (Stage 5)
- **Standard Detailed Cohort Count:** Default $N = 16$ cases (allowed range: 10 to 20 cases).
- **Deterministic Selection:** Cases must be chosen prospectively and deterministically using prediction-independent SHA-256 hash ranking:
  $$\text{rank} = \text{SHA256}(\text{seed\_prefix} + \text{sample\_id})$$
- **Mandatory 6-Stage Panel Sequence:**
  1. **Panel A — Original Radiograph:** Grayscale radiograph.
  2. **Panel B — Ground Truth Mask:** Binary GT stone contours/mask (lime green).
  3. **Panel C — Model Probability Map:** Continuous probability $[0, 1]$ displayed with a perceptually uniform colormap (e.g., `magma` or `viridis`).
  4. **Panel D — Binary Prediction:** Hard mask thresholded at operating point (e.g., $\tau = 0.50$).
  5. **Panel E — Standardized Error Map:**
     - **True Positive (TP):** Green / Cyan
     - **False Positive (FP):** Red / Orange
     - **False Negative (FN):** Blue / Yellow
     - **Background (TN):** Black / Transparent
  6. **Panel F — Radiograph Overlay:** Final predicted contours overlaid on raw radiograph.

---

## 4. Phase 15 Loss Study Concrete Specifications

Phase 15 implements a dual-cohort visual protocol:

| Specification | Primary Loss Study Notebook (`14_phase15_loss_study.ipynb`) | Validation Gallery Notebook (`14b_phase15_val_prediction_gallery.ipynb`) |
| :--- | :--- | :--- |
| **Cohort Size** | $N = 16$ cases (`phase15_val_detailed16_selection.csv`) | $N = 75$ cases (`phase15_val_gallery_selection.csv`) |
| **Selection Hash** | `phase15_detailed16_seed42\|{sample_id}` | `phase15_gallery_seed42\|{sample_id}` |
| **Pagination** | 4 pages $\times$ 4 cases/page | 5 pages $\times$ 15 cases/page |
| **Panels per Case** | 11 panels (A: Original, B: GT, C: Localizer, D: Proposals, E: L0, F: L1, G: L2, H: L3, I: Selected Best, J: Error Map, K: Overlay) | 5 panels (Original, GT, L0 Baseline, Selected Best, Error Map) |
| **Hard-Case Appendix**| Independent appendix for 16 Hard-Tiny and 7 Global-Empty | Independent appendix for 16 Hard-Tiny and 7 Global-Empty |
| **Output Figures** | Saved to `reports/figures/phase15/detailed16/` | Saved to `reports/figures/phase15/gallery75/` |

---

## 5. Storage, Resolution, and Notebook Bloat Control

To prevent Jupyter notebooks from swelling to hundreds of megabytes with embedded base64 strings:
1. All figures must be saved to disk as high-resolution PNG files under `reports/figures/<phase>/`.
2. Notebooks should display saved figures using `IPython.display.Image(filename)` or tightly configured `matplotlib` figures rendered on the fly with resolution targeted to clinical readability ($150-200$ DPI).
3. The master visual navigation index is maintained at [`notebooks/00_project_visual_index.ipynb`](file:///D:/Softfors/jup/notebooks/00_project_visual_index.ipynb).

---

## 6. Future Notebook Hard Gate

From Phase 15 onward, a phase cannot be declared notebook-complete unless, where scientifically applicable, all items below pass:

- **SAMPLE DATA:** PASS (8-12 representative samples at outset)
- **PIPELINE STEPS:** PASS (Intermediate representations visualized)
- **TRAINING CURVES:** PASS/NA (Loss, metric, LR, best/early-stop epoch from history)
- **AGGREGATE RESULTS:** PASS (Distributions, boxplots, summary tables)
- **DETAILED PREDICTIONS:** 10-20 (Default 16 deterministic non-cherry-picked cases)
- **FAILURE VISUALIZATION:** PASS (Hard cases, false positives, missed stones)
- **REAL SCORES:** PASS (Per-case scores matching displayed visual figures)
- **FIGURES SAVED:** PASS (All major figures saved to `reports/figures/<phase>/`)
- **FIGURES DISPLAYED IN NOTEBOOK:** PASS (Embedded `display(fig)` or `Image(filename)`)
- **RUN ALL:** PASS (Notebook executes cleanly from start to finish)
- **UNEXECUTED CODE CELLS:** 0
- **ERROR OUTPUTS:** 0
- **SHA-256:** RECORDED (Notebook JSON hash logged in audits)
- **TEST LEAKAGE:** 0 (`TEST reads = 0`, `TEST visualizations = 0`)

