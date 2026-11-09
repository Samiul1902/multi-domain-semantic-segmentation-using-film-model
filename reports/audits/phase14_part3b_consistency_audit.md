# Phase 14 Part 3B — Proposal-Provenance + Metric-Space Consistency Audit

## 1. Discrepancy A: Proposal Burden (4.66 vs 4.97)
**Issue:** The canonical Phase-13B Stage-4D localizer yielded a mean of 4.66 proposals per image. The Phase-14 Part 3 evaluation measured 4.97 proposals per image using the same checkpoint and NMS logic.
**Root Cause:** Model initialization mismatch. In Phase-13B, the localizer model was explicitly instantiated with `heatmap_resolution=128`, applying a 4x average pooling layer to the native 512x512 feature map before the final sigmoid activation. In Phase-14 Part 3, the model was instantiated with the default `heatmap_resolution=512`. Because the downsample layer has no weights, loading the checkpoint succeeded, but the network bypassed pooling and output a raw 512x512 probability map. Thresholding the unpooled high-frequency map generated distinct connected components, altering the NMS cascade and inflating proposal counts.
**Resolution:** The Phase-13B 4.66 proposals/image is authoritative. Phase-14 Part 3 must be re-executed with `heatmap_resolution=128`.

## 2. Discrepancy B: Metric Space (512 vs Original)
**Issue:** The frozen gate references ($D_g=0.652776$, $T_g=0.780822$) stem from Phase-10, where all metrics were computed in 512x512 downsampled space. Phase-14 Part 3 evaluated the baseline in the original multi-megapixel space to align with regional crop restoration (yielding $D_g=0.642499$, $T_g=0.794521$).
**Root Cause:** A prospective ambiguity in the Phase-14 Part-0C protocol. It hardcoded the 512-space Phase-10 historical metrics into the gate logic, but architecturally required the regional model to evaluate in original space (restoring probabilities via bilinear interpolation).
**Resolution:** The 512-space Phase-10 values (0.652776 / 0.780822) are cryptographically frozen into the gate logic and remain authoritative for official gate passage. For scientific consistency, future evaluations should include a "SUPPLEMENTAL SAME-SPACE DESCRIPTIVE CONTRASTS" section using the original-space metrics for relative gap measurements.

## 3. Discrepancy C: Runtime Means Mismatch
**Issue:** A 0.01 ms textual mismatch was observed between the sum of individual component runtimes and the Total Pipeline runtime in the concluding note.
**Root Cause:** Floating-point rounding artifact. The individual component means are:
- Global: 145.3936 ms
- Stage4D: 37.9158 ms
- Refiner: 123.5979 ms
- Fusion: 96.6372 ms
The true mathematical mean of the total pipeline is 403.5445 ms (displayed as 403.54 ms in the CSV/notebook). Summing the individually rounded values (145.39 + 37.92 + 123.60 + 96.64) yields 403.55 ms.
**Resolution:** The CSV and Notebook values (403.54 ms) are mathematically authoritative.

## 4. Final Audit Decision
**`PART3_REEVALUATION_REQUIRED_FROZEN_PROPOSALS`**
Phase-14 Part 3 must be re-evaluated using the exact 128x128 heatmap localizer topology to ensure the frozen predicted proposals match the canonical Stage-4D distribution.

