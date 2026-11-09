# PHASE-13 PART-1D-B — GLOBAL_NATIVE REPRODUCTION AUDIT

- status: **PASS**
- tolerance (max abs case Dice): **1e-4**
- all four PASS: **YES**
- regional inference started: **YES**

| model | rows | max abs Dice diff | mean abs Dice diff | mean Dice new | mean Dice Phase-12 | max abs IoU diff | result |
|---|---|---|---|---|---|---|---|
| UNet | 103/103 | 5.551e-17 | 4.615e-18 | 0.594180 | 0.594180 | 5.551e-17 | **PASS** |
| Attention U-Net | 103/103 | 1.110e-16 | 5.524e-18 | 0.629805 | 0.629805 | 7.633e-17 | **PASS** |
| UNet++ | 103/103 | 1.110e-16 | 4.716e-18 | 0.640516 | 0.640516 | 5.551e-17 | **PASS** |
| DeepLabV3+ | 103/103 | 1.110e-16 | 6.669e-18 | 0.560251 | 0.560251 | 8.327e-17 | **PASS** |

Secondary reproduction fields (IoU / precision / recall) are reported descriptively;
**no new pass threshold is invented** for them.

```
GLOBAL_NATIVE = native-space inversion of the canonical 512 evaluation prediction
  native grayscale -> canonical 512 aspect-preserving resize + centre pad -> model
  -> sigmoid FLOAT -> strip pad -> FLOAT bilinear (align_corners=False) -> native
  -> threshold 0.5 only after native restoration
```
