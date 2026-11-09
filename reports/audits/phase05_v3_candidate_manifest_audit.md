# Phase 05 Part 1D-R3: Manifest v3 Candidate Audit Report

**Status**: CANDIDATE ONLY - NOT CANONICAL - NOT FROZEN
**Scientific Gate**: CHECK_REQUIRED (Pending supervisor review)

## 1. Population Accounting
- **v2 Canonical Total**: 8,441
- **v3 Provenance Total**: 8441 (Missing: 0, Duplicate: 0, Unexpected: 0)
- **Active Candidate Splits**:
  - TRAIN: 5832 (-81 delta vs v2)
  - VAL: 808 (-37 delta vs v2)
  - TEST: 1683 (0 delta vs v2, byte-identical)
- **Quarantined Exclusions**: 118 cases

## 2. Test Immutability Gate
- SHA-256: 9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727
- Byte Identical: YES
- Test Content Reads / Visualizations: 0

## 3. Quarantine Reason Breakdown
- QUARANTINED_TEST_LINKED_PATIENT_OVERLAP: 62
- QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK: 34
- QUARANTINED_SAME_ACQUISITION: 13 
- QUARANTINED_BUSI_PATIENT_OVERLAP: 5
- CONSERVATIVE_HIGH_RISK_GROUPING: 3
- QUARANTINED_EXACT_DUPLICATE: 1

## 4. Active Leakage Audit Gates
- Sample ID Cross-Split Overlaps: 0
- KUB Patient Overlaps: 0
- BUSI Patient Overlaps: 0
- TRAIN-VAL Exact Image Content Duplicates: 0
- Cross-Split Duplicate/Risk Groups: 0
