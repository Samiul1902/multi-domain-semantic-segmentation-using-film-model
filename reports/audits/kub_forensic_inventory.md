# KUB Forensic Audit Report

This report resolves the dataset structure for KUB-StoneX and reconciles the count discrepancies.

## Dataset Inventory Reconciliation
- **Total Internal Segmentation Samples**: 8441 (3694+927+1000+2820). 
- **Count Explanation**: The previous 8159 total included non-segmentation files/subsets not found in approved raw roots. The 6649 total was incorrect due to undercounting nested KUB data.
- **KUB Pairings**: 2820 validated image-mask pairs.

## KUB Category Summary
| Category | Images | Masks | Paired | Images_Without_Masks |
| :--- | :--- | :--- | :--- | :--- |
| Kidney_Stone | 2033 | 1458 | 1457 | 576 |
| Bladder_Stone | 1460 | 1027 | 1026 | 434 |
| Ureteric_Stone | 547 | 338 | 337 | 210 |
| Normal_NoStone | 2776 | 0 | 0 | 2776 |

## Integrity Notes
- **Empty Masks**: 0
- **Duplicates**: None detected by standard inventory hash.
- **Provenance**: Historical 8159 count is **PROVENANCE UNRESOLVED**.
