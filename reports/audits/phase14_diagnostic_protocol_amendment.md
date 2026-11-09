# Phase 14 Diagnostic Protocol Amendment: Controlled Regional Refinement Study

**Document Type:** Prospective Diagnostic Protocol Specification (Design Only)  
**Status:** DIAGNOSTIC_PROTOCOL_FROZEN_AWAITING_IMPLEMENTATION  
**Parent Phase:** Phase 14 (Regional segmentation / coarse-to-fine refinement)  
**Execution Authorization:** NONE (Design and Audit Only)

---

## 1. Preservation of Original Confirmatory History
The original Phase-14 confirmatory entry gate was **NOT PASSED** based on the frozen Stage-4D localizer evaluation.
- The confirmatory Phase-14 path remains formally closed as COMPLETE_CLOSED_NOT_RUN with reason FROZEN_ENTRY_GATE_NOT_MET. 
- This amendment introduces a separate, prospective **Diagnostic Branch** designed to isolate regional refiner capability from proposal quality.

---

## 2. Core Diagnostic Questions
The diagnostic branch investigates three specific questions:
1. **Q1 (Upper Bound Capability):** Does regional refinement help when ROI localization is effectively ideal?
2. **Q2 (Proposal Bottleneck Quantification):** Does the SAME regional refiner help when driven by frozen Stage-4D predicted proposals?
3. **Q3 (Degradation Ratio):** What fraction of the oracle regional-refinement benefit is lost because of proposal quality?

---

## 3. Controlled Three-Way Comparison Structure
- **Condition A (Global Only):** Frozen strongest global baseline (UNet++, phase10_kub_unetpp_seed42_512).
- **Condition B (Oracle Regional Refinement):** Regional refiner evaluated with ground-truth component ROIs (margin 0.20 to match Stage-4D).
- **Condition C (Predicted-ROI Regional Refinement):** Identical regional refiner receiving bounding boxes from the frozen Stage-4D proposal generator.

---

## 4. Phase-14 Population & Component Basis (Part 0C Freeze)

### 4.1 FULL_FIELD Constraint
- Regional refinement applies **ONLY** to KUB `FULL_FIELD` images.
- **ROI_CROP Rule:** `ROI_CROP` predictions remain exactly the unchanged frozen global baseline. Regional refiner does not process them.
- **Combined Metrics:** Any combined KUB metric must be explicitly labeled `HYBRID DEVELOPMENT PIPELINE METRIC`.

### 4.2 Component & Image Counts
- **TRAIN FULL_FIELD:** 771 images, 1162 components.
- **VAL FULL_FIELD:** 106 images, 156 components.
- **Max Components / Image:** TRAIN max is 11. VAL max is 2.
- **Images > 5 Components:** 15 in TRAIN, 0 in VAL.
- **Oracle Budget Match:** Because images with > 5 components exist in TRAIN, the Primary Oracle evaluation is constrained to **TopK=5 largest GT components by area**. `ORACLE_UNBOUNDED` is optional.

---

## 5. Methodological Resolutions & Architecture 

### 5.1 Geometry Control & Ambiguity
- **Margin:** `margin=0.20`. Stage-4D's `apply_context_margin` returns a `crop_geometry` that is **already expanded**. The refiner must consume the `crop_geometry` directly without further expansion. Oracle Match uses `margin=0.20` strictly.

### 5.2 Fusion & Overlap Rules
- **Regional Aggregation:** $P_{regional\_union}(x) = \max_i(P_{regional\_i}(x))$ for pixels covered by proposals.
- **Global/Regional Fusion:** DIRECT_REPLACEMENT_IN_PROPOSAL_UNION. $P_{final}(x) = P_{regional\_union}(x)$ inside union of regional ROIs, and $P_{global}(x)$ outside.
- **Threshold & Zero-Proposal:** Final mask threshold at $0.50$. If 0 proposals exist for an image, $P_{final} = P_{global}$ everywhere (no synthetic fallback).

### 5.3 Granular Definitions
- **Crop Target**: The training target mask inside a crop contains **ALL** GT foreground pixels present within the crop boundary.
- **Interpolation**: Image resize (Bilinear), Prob restore (Bilinear), Mask resize for target (Nearest Neighbor).
- **BBox Clipping**: Hard clip to `[0, height]` and `[0, width]`. Rounding is standard half-to-even `round()`.
- **Hyperparameter Provenance**: U-Net (matches Phase-10 capacity, ~1.9M to 7.76M params based on config), 32 channels (matches UNet++ encoder), 256 crop (standard medical zoom).

---

## 6. A3 Exact Training Dataset Specification

The selected Option A3 training policy mixes 1 positive base crop with 2 perturbed crops and negative background crops to ensure robustness to Stage-4D errors.

- **Base Positive Crops:** 1162 crops per epoch (1 per TRAIN component). Margin=0.20.
- **Perturbed Positive Crops:** 
  - **Rule:** 2 crops per component per epoch (2324 total).
  - **Jitter:** Translation $\sim U(-0.10, 0.10) \times \text{crop\_side}$, Scale $\sim U(0.90, 1.10)$.
  - **Rationale:** Simulates plausible proposal imprecision to teach the model to handle imperfect Stage-4D centering.
- **Background Negative Crops:**
  - **Rule:** 2 crops per image per epoch (1542 total).
  - **Generation:** $U(64, 256)$ size. Up to 10 random sampling retries for pure zero-GT crop.
  - **Target:** All zeros.
  - **Rationale:** Fixed prospective rate (~30%) forces the model to learn to suppress false positive proposals.
- **Epoch Composition:** Exactly 5028 crops, determined dynamically each epoch.
- **Augmentation:** Matches Phase-10 baseline exactly. HFlip (0.5), VFlip (0.5), Rotation ($\pm 45^\circ$), Brightness/Contrast factor ($\pm 0.2$).
- **Seed:** 42 for PyTorch default generator.

---

## 7. Model Optimization Freeze
- **Architecture**: Standard 4-stage U-Net, 32 base channels
- **Input Resolution**: $256 \times 256$
- **Loss**: $0.5 \times \text{BCE} + 0.5 \times \text{SoftDice}$
- **Optimizer & LR**: AdamW, $1e-4$ learning rate, $1e-4$ weight decay
- **Batch Size & AMP**: 8 crops per batch, bfloat16/float16 Enabled
- **Early Stopping**: Patience 15 epochs. Max 100 epochs.
- **Checkpoint Rule**: Single checkpoint selected via `best_val_crop_dice` (Macro Dice per crop averaged across Oracle FULL_FIELD VAL. Empty/Empty Dice=1.0. Non-Empty/Empty Dice=0.0).

---

## 8. Diagnostic Decision Gate
- **Step 1 (Refiner Potential):** Contrast 1 (Oracle Regional) > Global Baseline. Tiny Recall@90 gain >= +0.05 AND Oracle FULL_FIELD Dice >= 0.632776.
- **Step 2 (Proposal Bottleneck):** Contrast 2 (Predicted Regional) drop is < 50% of the Oracle gain from Step 1 ($R \ge 0.50$).
- **Step 3 (Practical Net Benefit):** Contrast 3 (Predicted Regional) > Global Baseline. Tiny Recall@90 >= 0.780822, Full Field Dice drop <= 0.02 (Dice >= 0.632776), Hard Tiny >= 2/16 recovered, Global-empty >= 1/7 recovered.
- **Phase-15 Reopen Rule:** Reopen Phase 15 **IF AND ONLY IF** Step 1 and Step 3 are passed. Eligible for supervisor review.

---

## 9. Implementation Plan
**PHASE 14 DIAGNOSTIC PART 1: IMPLEMENTATION + UNIT/PREFLIGHT TESTS**
1. FULL_FIELD regional crop dataset & GT crop geometry utility
2. TRAIN-only perturbation generator & background-negative generator
3. Crop preprocessing & probability coordinate restoration
4. Multi-proposal regional aggregation & direct-replacement global/regional fusion
5. Oracle evaluator & Frozen Stage-4D predicted evaluator
6. Metric accumulator, regression tests, and CUDA preflight

---

## 10. Cryptographic & Governance Verification
- **TEST Split Access:** 0 content reads authorized.
- **TEST Metrics:** NONE.
- **External Data Access:** NONE.
- **Experiment A (Reference):** UNTOUCHED.
- **Active Training Execution:** NONE in this design task.
