# ReMedFiLM Computational Efficiency, Complexity, and Latency Reconciliation

**Auditor:** Principal Research Software Engineer & Performance Architect  
**Scope:** ReMedFiLM FULL vs GlobalMedFiLM Backbone vs Baseline Networks

---

## 1. Disentangling Analytical GMACs from Empirical Routing Frequencies

In Version 8 (Table 4 and Figure 1), ReMedFiLM FULL was reported with `32.4379` conditional GMACs alongside the `VAL808` headline Dice score ($0.837290$). Our source audit of `reports/tables/c2_barr/c2_barr_aggregate.json` reveals the exact mathematical origin of this figure:

### Analytical Breakdown:
- **Global Backbone ($G$) Base GMACs:**  
  $$C_{\text{global}} = 31.551740928 \text{ GMACs} \quad (\approx 31.55 \text{ GMACs})$$
- **Regional Refiner ($R_\psi$) Full Execution GMACs:**  
  $$C_{\text{refine\_delta}} = 3.230662656 \text{ GMACs}$$
- **Always-Refine Upper Bound (Arm A1):**  
  $$C_{\text{always}} = C_{\text{global}} + C_{\text{refine\_delta}} = 34.782403584 \text{ GMACs} \quad (\approx 34.78 \text{ GMACs})$$

### The Population Mismatch in V8:
The reported conditional compute $C_{\text{conditional}} = 32.437902022 \text{ GMACs}$ was derived using the routing activation frequency from the **`ROUTER_HOLDOUT_875`** dataset ($n = 875$):
$$p_{\text{routed}} = \frac{240}{875} = 0.274286 \quad (27.43\%)$$
$$C_{\text{holdout}} = 31.551741 + (0.274286 \times 3.230663) = 32.437902 \text{ GMACs}$$

In contrast, on the canonical **`VAL808`** evaluation cohort ($n = 808$):
- $n_{\text{routed}} = 279$ cases ($34.53\%$)
- $n_{\text{accepted}} = 266$ cases ($32.92\%$)
- $n_{\text{rejected}} = 13$ cases ($1.61\%$)
- $n_{\text{skip}} = 529$ cases ($65.47\%$)

Calculating expected conditional compute on **`VAL808`** yields:
$$C_{\text{VAL808}} = 31.551741 + (0.345297 \times 3.230663) = \mathbf{32.667232 \text{ GMACs}} \quad (\approx 32.67 \text{ GMACs})$$

### V9 Resolution:
Both numbers are mathematically valid within their respective domains:
1. **$32.44$ GMACs** is the **benchmark design specification** evaluated across the 875-case router holdout.
2. **$32.67$ GMACs** is the **empirical operational compute** on the 808-case validation split.
In Version 9, we report both values with explicit population labels to prevent conflating the design benchmark with the validation run.

---

## 2. Latency Profiling and Measurement Qualification

In `reports/tables/c2_barr/c2_barr_aggregate.json`, batch-1 latency measurements on an NVIDIA RTX 3060 Ti are cataloged:

| Pipeline Branch / Component | Mean Latency (ms) | Median (P50) Latency (ms) | Measurement Scope |
| :--- | :--- | :--- | :--- |
| **Global Backbone Only ($G$)** | $15.77 \pm 0.64$ ms | $15.72$ ms | Standard 512×512 forward pass |
| **Router ($B_\phi$) Alone** | $0.37 \pm 0.08$ ms | $0.35$ ms | 202-D MLP forward evaluation |
| **Refiner ($R_\psi$) Alone** | $4.53 \pm 0.73$ ms | $4.48$ ms | 256×256 4-channel crop refinement |
| **Safety Gate ($S_\omega$) Alone**| $0.25 \pm 0.08$ ms | $0.24$ ms | 16-D MLP safety scoring |
| **FULL Pipeline — SKIP Path** | $15.72 \pm 0.59$ ms | $15.71$ ms | $G$ pass + $B_\phi$ evaluation (fallback) |
| **FULL Pipeline — EXECUTE Path** | $18.89 \pm 0.66$ ms | $18.89$ ms | $G + B_\phi + R_\psi + S_\omega$ + Window Fusion |

### Scientific Disclosure on End-to-End Latency:
- The executed path incurs only **+3.17 ms** of additional latency over the backbone (18.89 ms vs 15.72 ms).
- On the 65.47% of images that are skipped, latency is practically identical to the backbone (15.71 ms).
- **Caveat:** These benchmarks represent controlled forward-only execution on pre-extracted feature tensors. They do not include disk I/O, raw DICOM ingestion, or online feature extraction.
