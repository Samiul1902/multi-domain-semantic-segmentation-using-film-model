# Phase 4 v3 — Leakage-Safe Canonical Development Manifests

## Status: CANONICAL_ACTIVE_DEVELOPMENT

**Promotion Date:** 2026-09-20 (UTC)  
**Authorized by:** Supervisor (Phase-05 Part-1E)  
**Supersedes:** `manifests/phase4_v2/` (root `manifests/*.csv`)

## Purpose

This directory contains the canonical leakage-safe development splits for
all future clean scientific work. It was produced by Phase-05 leakage audit
and remediation (Parts 1A–1D) and formally promoted in Part 1E.

## Files

| File | Rows | Description |
|---|---|---|
| `all_paired.csv` | 8441 | All samples with v3 split assignment |
| `train.csv` | 5832 | Active training set |
| `val.csv` | 808 | Active validation set |
| `test.csv` | 1683 | Immutable test set (byte-identical to v2) |
| `quarantined.csv` | 118 | Quarantined development samples |
| `duplicate_groups.csv` | — | Duplicate group assignments |
| `grouping_provenance.csv` | — | Quarantine rule provenance |

## SHA-256 Hashes

| File | SHA-256 |
|---|---|
| `all_paired.csv` | `eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded` |
| `train.csv` | `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` |
| `val.csv` | `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315` |
| `test.csv` | `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` |
| `quarantined.csv` | `a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c` |
| `duplicate_groups.csv` | `830d3c0ce08f735081e5a44fe3a740031da1c70cfc19ebcb4ef89c31acd704fb` |
| `grouping_provenance.csv` | `3eff84851d33e1c8b5894ce05049433287067a5e6088a90f5c67394230317f66` |

## v3 vs v2 Changes

| Dataset | v2 TRAIN | v3 TRAIN | Delta | v2 VAL | v3 VAL | Delta | QUARANTINED |
|---|---|---|---|---|---|---|---|
| KUB | 1979 | 1978 | -1 | 283 | 280 | -3 | 4 |
| ISIC | 2581 | 2556 | -25 | 378 | 357 | -21 | 46 |
| BUSI | 656 | 602 | -54 | 97 | 84 | -13 | 67 |
| KVASIR | 697 | 696 | -1 | 87 | 87 | 0 | 1 |

**TEST: unchanged (1683 samples, byte-identical to v2)**

## Quarantine Summary (118 total)

| Reason | Count |
|---|---|
| QUARANTINED_TEST_LINKED_PATIENT_OVERLAP | 62 |
| QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK | 34 |
| QUARANTINED_SAME_ACQUISITION | 13 |
| QUARANTINED_BUSI_PATIENT_OVERLAP | 5 |
| CONSERVATIVE_HIGH_RISK_GROUPING | 3 |
| QUARANTINED_EXACT_DUPLICATE | 1 |

## Usage

```python
import pandas as pd
PROJECT_ROOT = r'D:\Softfors\jup'
train = pd.read_csv(f'{PROJECT_ROOT}/manifests/phase4_v3/train.csv')
val   = pd.read_csv(f'{PROJECT_ROOT}/manifests/phase4_v3/val.csv')
test  = pd.read_csv(f'{PROJECT_ROOT}/manifests/phase4_v3/test.csv')
```

## Historical Note

Do NOT load `manifests/train.csv` (v2 root) for new experiments.  
v2 root files remain for historical reproducibility of Phases 06–15.

