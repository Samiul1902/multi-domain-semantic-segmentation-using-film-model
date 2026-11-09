# Phase 7-R1 FOV Count Reconciliation

## Resolution
The apparent Phase-7 contradiction was a **unit mix-up**, not a source-population error:

- `771 FULL_FIELD / 1208 ROI_CROP` are **TRAIN sample counts**.
- `1162 FULL_FIELD / 1214 ROI_CROP` are **TRAIN connected-component counts**.

These reconcile independently to 1,979 non-empty samples and 2,376 8-connected components.

## TRAIN Sample-Level FOV × Category

| Category | FULL_FIELD samples | ROI_CROP samples | Unresolved | Total samples |
|---|---:|---:|---:|---:|
| Kidney_Stone | 421 | 712 | 0 | 1133 |
| Bladder_Stone | 253 | 382 | 0 | 635 |
| Ureteric_Stone | 97 | 114 | 0 | 211 |
| **Total** | **771** | **1208** | **0** | **1979** |

## TRAIN Component-Level FOV × Category

| Category | FULL_FIELD components | ROI_CROP components | Unresolved | Total components |
|---|---:|---:|---:|---:|
| Kidney_Stone | 709 | 717 | 0 | 1426 |
| Bladder_Stone | 344 | 383 | 0 | 727 |
| Ureteric_Stone | 109 | 114 | 0 | 223 |
| **Total** | **1162** | **1214** | **0** | **2376** |

## Component Arithmetic
- FULL_FIELD: 771 samples, 1,162 components, mean 1.507134 components/image.
- ROI_CROP: 1,208 samples, 1,214 components, mean 1.004967 components/image.
- FULL_FIELD images with >1 component: 206.
- FULL_FIELD component-count distribution: 1=565, 2=123, 3=41, >3=42.

## Taxonomy Verification
`kub_size_v1` is validated unchanged from 1,162 TRAIN FULL_FIELD components:

- Q25 = 0.0001499766777599
- Q50 = 0.00033976472454305
- Q75 = 0.0008266496069636999

The component-level category × size totals (709/344/109) match the FULL_FIELD component category totals exactly.

## Validation Transfer
VAL has 106 FULL_FIELD samples and 156 FULL_FIELD components (mean 1.471698 components/image). Frozen TRAIN thresholds produce TINY=73, SMALL=29, MEDIUM=36, LARGE=18.

## Controls
- TEST mask reads: 0
- External data access: none
- Raw data modified: no
- Manifest modified: no
- Training: no
