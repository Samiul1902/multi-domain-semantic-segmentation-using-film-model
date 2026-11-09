# Phase 13B Stage-4D: Final Localizer Design Audit

## 1. Clean V3 Diagnosis
The clean V3 localizer (512x512 heatmap, $\sigma=3$, CenterNet Focal Loss) failed the promising gate because the dense background (262,144 pixels) suppressed positive probability peaks. The mean max probability across images remained clustered near the initialization prior of `0.1003`. The few useful detections occurred solely because the search grid threshold dipped to `0.10`, catching minute noise fluctuations slightly above the prior. There is no evidence of coordinate mapping error or target-generation error (both were strictly verified in Stage-4C-R3).

## 2. Pipeline Reconstructed
- **Input:** 512x512 KUB FULL_FIELD image.
- **Localizer Network:** Compact U-Net producing a 512x512 logit map.
- **Target Heatmap:** Original components mapped to 512-space via affine scaling, rendering a Gaussian peak at EXACTLY 1.0 with $\sigma=3$.
- **Loss:** CenterNet Focal Loss (no Dice).
- **Peak Extraction:** 3x3 Max Pool equality check.
- **Proposal Search:** Feasibility constraints (ROI $\le 0.10$, Props $\le 5$).

## 3. Geometry & Collision Audit
A spatial target audit was conducted to evaluate the safety of lower-resolution heatmaps:
- **512x512 (Stride 1):** 262,144 pixels (~174k pixels per positive). Collisions: 0. Equivalent $\sigma$: 3.0
- **256x256 (Stride 2):** 65,536 pixels (~43k pixels per positive). Collisions: 0. Equivalent $\sigma$: 1.5
- **128x128 (Stride 4):** 16,384 pixels (~11k pixels per positive). Collisions: 0. Equivalent $\sigma$: 0.75
- **64x64 (Stride 8):** 4,096 pixels (~2.7k pixels per positive). Collisions: 4 (TRAIN), 3 (VAL). Equivalent $\sigma$: 0.375

*Finding:* 128x128 is the optimal geometry. It reduces the background penalty burden by 16x without causing a single component collision. Quantization error back to 512-space is $\pm 2$ pixels, which is well within the acceptable margin for ROI proposal crops.

## 4. Architecture Options Considered
1. **Option A (Decoder Tapping):** Extract the 1-channel heatmap directly from the `d3` (stride-4) decoder block of the existing U-Net, dropping the final two upsampling stages. This strictly isolates the resolution variable while saving FLOPs.
2. **Option B (Explicit Stride Head):** Maintain the 512x512 U-Net but attach a stride-4 pooling head. This computes full resolution features only to downsample them, which is wasteful.
3. **Option C (New Backbone):** Use a standard ResNet-CenterNet architecture. This introduces massive confounding variables (new depth, new capacity, new skip connection patterns).

## 5. Recommended Single Design
**FINAL_BOUNDED_REDESIGN_JUSTIFIED**

We recommend a single, final, bounded experiment using **Option A (Decoder Tapping)** at **128x128 (Stride 4)**.
- **Single Variable Changed:** Output spatial resolution (stride 4 vs stride 1).
- **Frozen Variables:** Loss, init ($p=0.10$), optimizer, target components, seeds, gates, proposal grid limits.
- **Geometrically Equivalent Sigma:** $0.75$ in 128-space.
- **Pre-Registered ID:** `phase13b_kub_localizer_r512_s3_centernetfocal_stride4_seed42_v1`
- **Stopping Policy:** If this single pilot fails the established Stage-4C gate, the learned-localizer branch will be formally closed.

