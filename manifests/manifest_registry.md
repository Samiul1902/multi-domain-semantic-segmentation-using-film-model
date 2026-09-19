# Manifest Registry

Generated: 2026-09-19T19:03:33.820707Z

## Active Development Manifest

**Version:** `phase4_v3`  
**Status:** CANONICAL_ACTIVE_DEVELOPMENT  
**Directory:** `manifests/phase4_v3/`

| File | SHA-256 |
|---|---|
| `train.csv` (5832) | `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6` |
| `val.csv` (808) | `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315` |
| `test.csv` (1683) | `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` |
| `quarantined.csv` (118) | `a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c` |
| `all_paired.csv` | `eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded` |

## Historical Manifest

**Version:** `phase4_v2`  
**Status:** HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT  
**Directory:** `manifests/` (root CSV files)  
**Leakage Status:** KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY

Required to reproduce historical Phases 06–15. DO NOT delete or modify.

| File | SHA-256 |
|---|---|
| `train.csv` (5913) | `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3` |
| `val.csv` (845) | `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4` |
| `test.csv` (1683) | `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727` |
| `all_paired.csv` | `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc` |

## Promotion

- **Authorized by:** Supervisor (Phase-05 Part-1E)
- **Date:** 2026-09-19T19:03:33.820707Z
- **Reason:** Phase-05 leakage audit and remediation
- **Quarantined:** 118 development samples
- **TEST:** Byte-identical between v2 and v3

## Governance Rule

> All future scientific development MUST use `phase4_v3`.  
> Historical experiments retain `phase4_v2` provenance.  
> Do NOT silently load root `manifests/train.csv` for new experiments.
