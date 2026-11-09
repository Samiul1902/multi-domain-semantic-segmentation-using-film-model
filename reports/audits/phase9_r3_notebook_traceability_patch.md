# Phase 9-R3 — Notebook Completeness and Traceability Patch

**Status: PASS**  
**Scope: presentation/audit only; no retraining, inference, or metric changes**

## Notebook additions

`notebooks/07_kub_unet_baseline_training.ipynb` now displays:

- The existing learning-rate curve from `reports/figures/phase9_unet_baseline/phase9_unet_lr_curve.png`.
- FULL_FIELD single- versus multi-component results derived from retained CSV tables.
- Versioned R3 qualitative and failure panels with row labels containing sample ID, category, FOV, Dice, and IoU.
- An explicit traceability explanation for the 333 per-component rows versus 332 preprocessed GT components.

Restart/Run All completed with 10/10 code cells executed and zero errors. Static notebook inspection found no training entrypoint, optimizer step, backward pass, DataLoader construction, or checkpoint loading. It remains display-only.

Notebook SHA-256: `a0f522b0392ff5ed867dbc7e5319b5939250de9481c46c5447c6f1c64a0e5d25`

## FULL_FIELD component analysis

Grouping uses the original-space `component_count` metadata in the unchanged per-image table. Pooled object recall uses detection rows in the unchanged original-space per-component table.

| Group | Images | Macro Dice | GT components | Detected | Object recall | Missed-object rate |
|---|---:|---:|---:|---:|---:|---:|
| Single component | 56 | 0.605988733165677 | 56 | 46 | 0.8214285714285714 | 0.1785714285714286 |
| Multi component | 50 | 0.620884684556593 | 100 | 79 | 0.7900000000000000 | 0.2100000000000000 |

## Per-component row traceability

- Per-component CSV rows: **333**
- Object-summary preprocessed GT components: **332**
- Difference: **1**

The two values represent different, explicit stages:

1. `phase9_unet_val_per_component.csv` has one row per **original-space GT component**, based on retained component metadata.
2. The object summary labels the binary masks **after** aspect-ratio-preserving resize and symmetric padding at 512×512.

Exactly one sample differs: `32c06da36a7221dc5369e3ee4723c10c`. It has two original FULL_FIELD components of 1,145 and 1,047 pixels. After nearest-neighbor downsampling, those components become touching and form one 8-connected component in the preprocessed mask. Consequently, this sample contributes two original-component rows but one preprocessed component to the object summary.

The 333rd row is therefore neither prediction-only nor spurious. The tables are scientifically consistent within their documented schemas.

## Versioned panels

Existing assets were preserved. R3 label-only versions were added in PNG (320 DPI), SVG, and PDF:

- `reports/qualitative/phase9_unet_baseline/phase9_val_qualitative_panel_r3.*`
- `reports/qualitative/phase9_unet_baseline/phase9_val_failure_panel_r3.*`

The deterministic selections are unchanged.

## Integrity

- Authoritative overall VAL macro Dice: **0.7455439340960021** (unchanged)
- Phase-9 metrics changed: **NO**
- Source result tables changed: **NO**
- Retraining or extra epochs: **NO**
- TEST accessed: **NO**
- External data accessed: **NO**
- Experiment A modified: **NO**
- Phase 10 executed: **NO**

**STOP.**
