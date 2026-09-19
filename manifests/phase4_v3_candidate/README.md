# Leakage-Safe Manifest v3 Candidate

This directory contains the v3 candidate dataset manifests, generated to resolve cross-split data leakage discovered in Phase 05 Part 1A.

## Key Changes
- **Immutable TEST**: `test_v3_candidate.csv` is byte-identical (modulo new grouping columns if any, but the set of samples is identical) to the v2 `test.csv`.
- **Exact Duplicate Resolved**: The KUB exact duplicate pair was resolved by keeping the TRAIN member and quarantining the VAL member.
- **Near Duplicates Resolved**: 13 ISIC distance-0 pairs and 4 distance-2 unresolved pairs spanning TRAIN/VAL were resolved by quarantining the VAL member.
- **BUSI Patient Leakage Resolved**: BUSI patients that spanned across splits were resolved. Any patient spanning into TEST had its TRAIN/VAL members quarantined. Any patient spanning TRAIN/VAL had its VAL members quarantined.

## Files
- `all_paired_v3_candidate.csv`: Master provenance file including `QUARANTINED` items.
- `train_v3_candidate.csv`, `val_v3_candidate.csv`, `test_v3_candidate.csv`: The candidate active splits.
- `quarantined_v3_candidate.csv`: Items removed from active splits due to leakage risk.
- `duplicate_groups_v3_candidate.csv`: Registry of grouped items.
- `grouping_provenance_v3_candidate.csv`: Summary of applied rules.
