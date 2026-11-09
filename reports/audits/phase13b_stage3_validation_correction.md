# Phase 13B Stage-3 Validation & Checkpoint-Selection Correction

**Status:** PASS

## Audit Summary
- **Provisional Run:** `phase13b_kub_localizer_r512_s3_seed42` reached epoch 19.
- **Validity:** Run is preserved but is `INVALID_FOR_FINAL_SELECTION`. A restart from epoch 0 is required.
- **Reason:** Audit detected unapproved positive/negative pixel class-balancing in the focal loss (`positive_focal + negative_focal` separate normalizations) and unapproved metrics (`hard_tiny_recovered90`, `mean_area` binary penalty) used for checkpoint selection.

## Code Corrections Made
- **Loss:** Standardized `SoftFocalDiceLoss` to compute unweighted pixel-wise mean (`focal_values.mean()`) to strictly match the requested `0.75 * Focal(gamma=2, alpha=0.25) + 0.25 * SoftDice`.
- **Checkpoint Selection:** Enforced the frozen objective: `primary = VAL Tiny recall90`, `tie 1 = overall component recall90`, `tie 2 = lower VAL localization loss`.
- **Epoch Proposal-Config Selection:** Sorted the 20 exact proposal grid configs using the deterministic hierarchy: maximize `Tiny recall90`, maximize `overall recall90`, minimize `proposals/image`, minimize `ROI area`, higher `threshold`, smaller `Top-K`, smaller `margin`.
- **Efficiency:** Verified that inference is run once per epoch, GT is unused during proposal generation, and the exact 20-config grid is evaluated.

## Verification
- Added test coverage in `test_kub_localizer.py` verifying the 20-config grid, deterministic selection rules, checkpoint logic, and standard focal loss behavior.
- All tests passed.
- Governance locks untouched; 0 TEST reads.

