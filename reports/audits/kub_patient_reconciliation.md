# KUB Patient-ID and Split Reconciliation Report (Phase 4-R6)

## Patient ID Extraction Rule
- **Source**: Filename prefix (e.g., `00001-00-2500001.png`)
- **Regex**: `^(\d+)-` -> `patient-\1`
- **Missing / Ambiguous**: 0 / 0
- **Total Valid Paired KUB Rows**: 2820
- **Exact Unique KUB Patient IDs**: 711

## Patient Count Reconciliation (1146 vs 711)
- The prior cited count of 1146 was an unvalidated ratio estimate (`2820 / 2.46`).
- File-level regex extraction on the 2820 authoritative paired KUB rows measures **exactly 711 unique patient IDs**.

## Patient Sample Distribution
- **Min**: 1
- **Median**: 3.0
- **Mean**: 3.97
- **Max**: 50
- **Exactly 1 sample**: 8 patients
- **>1 sample**: 703 patients
- **Spanning >1 category**: 1 patient (`patient-00360`)

## Current Manifest SHA-256 Hashes
- `all_paired.csv`: `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc`
- `train.csv`: `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3`
- `val.csv`: `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4`
- `test.csv`: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`

## Patient Overlap Audit
- **Train Patients**: 318
- **Val Patients**: 111
- **Test Patients**: 282
- **Train Intersect Val**: 0
- **Train Intersect Test**: 0
- **Val Intersect Test**: 0
