# Phase 13B Stage-4C: Center-Heatmap Loss Redesign Pilot

## Status
FAIL / CHECK_REQUIRED

## Objective
Replace the standard Focal+SoftDice loss with a CenterNet-style modified Focal loss to improve compact localization.

## Target Validation Failure
During the predeclared Target Validation step, the target heatmaps were audited:
- **Result:** FAILED. Target peaks do NOT reach exactly 1.0. 
- **Reason:** When the component bounding boxes are scaled to the 512x512 resolution, their geometric centers often fall on sub-pixel coordinates (e.g., `256.4`). The `make_gaussian_heatmap` utility assigns the peak density based on the distance to the nearest integer pixel. Since the distance is not exactly 0, the maximum Gaussian density value is slightly less than 1.0 (e.g., `0.991`).
- **Consequence:** The CenterNet loss formula `target.eq(1.0)` fails to find ANY positive centers. 

## Gradient Diagnostic
The gradient diagnostic confirmed the catastrophic failure:
- **Old Loss:** 0.4343 (Grad Norm: 1.89)
- **New Loss:** 343,782.6 (Grad Norm: 3,529,166.1)
- **Positive Center Contribution:** 0.0000

Because 0 positive centers were detected, the loss penalized every single pixel in the image as a negative background pixel and summed the raw loss without positive normalization. 

## Action Taken
As instructed by the protocol: `"If target peaks do not reach exactly 1.0: CHECK_REQUIRED and STOP. Do not silently modify targets."`
The pilot training was NOT started. The target generation logic (`make_gaussian_heatmap`) must be redesigned to force the nearest integer pixel to exactly 1.0.

