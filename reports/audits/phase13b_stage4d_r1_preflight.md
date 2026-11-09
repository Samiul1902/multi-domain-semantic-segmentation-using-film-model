# Phase 13B Stage-4D-R1: Final Bounded Localizer Preflight

## Controlled Implementation
The clean-V3 architecture remains exactly unchanged. A final parameter-free `AvgPool2d(4,4)` operation is applied to downsample the 512x512 output logits into a 128x128 heatmap.
- **Parameters:** 482,449 (Clean V3) $\to$ 482,449 (Stage-4D).
- **Difference:** 0 trainable parameters added or modified.
- **Initialization:** Constant logit $\log(0.1/0.9) \approx -2.1972$ mathematically commutes perfectly with average pooling, resulting in precisely $p=0.100000$ initially across the entire 128x128 heatmap.

## Heatmap Geometry & Sigma Equivalence
- **Sigma:** 0.75 in 128-space (geometrically equivalent to 3.0 in 512-space).
- **TRAIN Components:** 1162 expected, 1162 mapped, 1162 unique centers (0 collisions, 0 zero-center samples).
- **VAL Components:** 156 expected, 156 mapped, 156 unique centers (0 collisions, 0 zero-center samples).
- **Round-Trip Error:** Bounded structurally $\le 2.12$ px max (stride 4 block center). Mean error $\sim 1.06$ px, P95 error $\sim 1.85$ px.

## Loss Diagnostics
- **Batch Diagnostic (matched DataLoader batch):**
  - 512x512 heatmap: Total loss 139.84 (Pos: 1.87, Neg: 137.98). Grad: 657.02, Head grad: 537.93.
  - 128x128 heatmap: Total loss 10.49 (Pos: 1.87, Neg: 8.62). Grad: 38.43, Head grad: 31.12.
- **Single-Sample Diagnostic:**
  - 512x512 heatmap: Total loss 278.06 (Neg: 276.19). Head grad: 1199.79.
  - 128x128 heatmap: Total loss 19.13 (Neg: 17.26). Head grad: 73.70.
- *Conclusion:* The 16x reduction in spatial grid cells reduces the negative CenterNet Focal Loss burden from $\sim 138$ to $\sim 8.6$ ($\sim 16\times$ reduction) and head gradients from 538 to 31, proving the background optimization burden is decisively relieved while preserving positive loss identity ($1.87$ in both).

## Freeze Guarantees
- 512 pipeline path is fully intact for regression via parameter `heatmap_resolution=512`.
- Proposal logic, NMS, 20-config selection grid, feasibility rules, checkpoint selection, epochs, and early-stopping semantics remain strictly frozen.
