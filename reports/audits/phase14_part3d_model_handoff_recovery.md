# Phase 14 Part 3D-R2 — Model Handoff Recovery Audit

## Executive Summary
- **Status:** PASS
- **Previous Model:** Gemini 3.1 Pro High (and Claude Opus Thinking interim)
- **Recovery Model:** Gemini 3.8 Flash
- **Previous Gemini Work Preserved:** YES (494-proposal canonical count, autocast repair, heatmap resolution 128, all 7 figures, qualitative panel, SUPERSEDED markings)
- **Full Evaluation Rerun:** NO (preserved existing valid evaluation CSVs)
- **Proposal Regeneration:** NO
- **Scientific Settings Changed:** NO
- **Training Executed:** NO

## Canonical Proposal State Verification
- **Total Proposals:** 494
- **Mean Proposals per Image:** 4.660377
- **Heatmap Resolution:** 128
- **AvgPool4:** Active

## Repaired Column Mapping & Cell Adjustments
1. **Cell 29 (Component Metrics):**
   - `size_group` -> `size_stratum`
   - `global_recall90_success` -> `cov90_global_512`
   - `oracle_recall90_success` -> `cov90_oracle_512`
   - `predicted_recall90_success` -> `cov90_predicted_512`
2. **Cell 31 (Hard Cases Summary):**
   - Displayed canonical mode-level hardcase summary table (`phase14_part3_hardcase_summary.csv`) replacing non-existent per-case filters.
3. **Cell 37 (Diagnostic Contrasts & Gate Hierarchy):**
   - Aligned dictionary keys with audit JSON (`diagnostic_contrasts`, `official_512_space`).
   - Handled `step2_status` (`NOT_DEFINED`) and `step2_pass` (`null`).
4. **Cell 39 (Summary Figures):**
   - `global_dice` -> `global_dice_512`
   - `oracle_dice` -> `oracle_dice_512`
   - `predicted_dice` -> `predicted_dice_512`
5. **Cell 44 (Part-3C/3D Audit Loader):**
   - `predicted_proposals_512` -> `predicted_proposals`
   - Safe access for `step2_status` (`NOT_DEFINED`).
6. **Cell 46 (KUB Stone Segmentation Demo):**
   - Deterministic sample selection: lexicographically first FULL_FIELD VAL sample with $\ge 1$ GT stone (`0785b56594049121d6281aa40e475e26`).
   - Fixed `SegmentationTransform(size=512, train=False)`.
   - Cast logits to `.float()` for PIL compatibility under AMP autocast.
   - Fixed proposal `crop_geometry` dictionary unpacking for matplotlib bounding box rendering.

## Step-2 Machine-Readable Semantics
- **G:** -0.136986
- **R:** NOT_DEFINED (G <= 0 precludes ratio denominator)
- **Step 1:** FAIL
- **Step 2 Status:** NOT_DEFINED
- **Step 2 Pass:** `null` (strictly non-boolean)
- **Step 3:** FAIL
- **Final Classification:** `DIAGNOSTIC_REFUTED_REFINER_INEFFECTIVE`
- **Phase 15 Status:** `NOT_AUTHORIZED`

## Final Notebook Validation
- **Notebook File:** `notebooks/13_phase14_regional_refiner_diagnostic.ipynb`
- **Total Cells:** 47
- **Markdown Cells:** 26
- **Code Cells:** 21
- **Executed Code Cells:** 21
- **Unexecuted Code Cells:** 0
- **Notebook Errors:** 0
- **Training Side Effects:** NONE
- **Test Set Reads:** 0
- **Final Notebook SHA-256:** `4392272f44c8be3d51ba3c2687b938e8860123b4d2e36f280169f76721701ce7`

## Read-Only Demonstration Validation
- **Sample ID:** `0785b56594049121d6281aa40e475e26`
- **Split:** VAL
- **FOV:** FULL_FIELD
- **GT Components:** 2
- **Proposal Count:** 5
- **ROI Union Fraction:** 0.0032
- **Global Dice:** 0.8036
- **Predicted-Regional Dice:** 0.3542
- **Global FP Components:** 0
- **Predicted FP Components:** 4

