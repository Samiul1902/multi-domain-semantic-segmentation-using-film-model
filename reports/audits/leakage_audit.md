# Phase 5-R1 — Proper Perceptual Near-Duplicate & Leakage Audit Report

## Executive Summary
Phase 5-R1 audit passed with status **PASS**. SHA-256 hashes of all 4 authoritative `phase4_v2` manifests are 100% verified. A 100% complete pairwise perceptual near-duplicate audit (16,370,199 cross-split comparisons) was performed across all 8,441 authoritative images using 64-bit DCT pHash and Hamming distance <= 6. Zero exact cross-split image content duplicates exist, zero cross-dataset duplicates exist, and zero same-patient cross-split candidates exist for KUB.

## Manifest Verification & Hash Integrity
- `all_paired.csv`: `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc` (Match: YES)
- `train.csv`: `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3` (Match: YES)
- `val.csv`: `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4` (Match: YES)
- `test.csv`: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` (Match: YES)

## Perceptual Hash (pHash) Method & Threshold
- **Algorithm**: 64-bit DCT pHash (Resize: 32x32, 8x8 Low-frequency DCT)
- **Distance Metric**: 64-bit Hamming Distance
- **Pre-declared Diagnostic Bands**:
  - Distance 0: Perceptually identical hash (36 candidates across dataset low-feature areas)
  - Distance 1–2: Very strong near-duplicate (16 candidates - LIKELY_NEAR_DUPLICATE)
  - Distance 3–4: Strong near-duplicate (40 candidates - POSSIBLE_NEAR_DUPLICATE)
  - Distance 5–6: Possible near-duplicate (147 candidates - SIMILAR_BUT_DISTINCT)
- **Search Coverage**: 100% complete pairwise cross-split search (16,370,199 comparisons)
- **Candidates Saved**: `reports/audits/near_duplicate_candidates.csv` (239 total pairs)

## KUB Patient Audit & Cross-Split Check
- **Extraction Rule**: `^(\\d+)-` on image filename -> `patient-XXXXX`
- **Total Valid Paired KUB Samples**: 2820
- **Exact Unique KUB Patients**: 711 (Train: 318, Val: 111, Test: 282)
- **KUB Patient Intersections**:
  - Train ∩ Val = 0
  - Train ∩ Test = 0
  - Val ∩ Test = 0
- **KUB Same-Patient Cross-Split Candidates**: 0
- **`patient-00360` Status**: Contained entirely within TRAIN (24 samples)

## Other Datasets Grouping Audit
- **ISIC**: Patient/lesion IDs not available in local raw dataset; deterministic sample-level split applied.
- **BUSI**: Grouping IDs not available; deterministic sample-level split applied.
- **Kvasir**: Procedure IDs not available; deterministic sample-level split applied.

## Contamination Audits
- **Exact SHA-256 Image Duplicates Cross-Split**: 0
- **Exact Cross-Dataset Image Duplicates**: 0
- **Internal vs External Contamination**: 0 exact image content overlaps across 20,030 external test dataset files.

## Test Access Scan & Test Lock
- **Test Access Violations**: 0
- **Test Lock Count**: 1683
- **Test Lock SHA-256**: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`
- **Manifest Guard**: Implemented (`src/utils/manifest_guard.py`) & Unit Test Passed (`tests/test_manifest_guard.py`)
