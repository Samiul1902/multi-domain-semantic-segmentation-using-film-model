# kub_size_clean_v3_v1 — FROZEN Threshold Artifact

**Taxonomy ID:** `kub_size_clean_v3_v1`  
**Status:** **FROZEN**  
**Artifact SHA-256:** `89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6`  
**Derivation timestamp:** 2026-09-20T04:22:30.624050+00:00

## Design

| Field | Value |
|---|---|
| Manifest version | `phase4_v3` |
| Derivation split | TRAIN |
| Dataset | KUB |
| Acquisition scope | FULL_FIELD |
| ROI handling | `ROI_NOT_PRIMARY_BINNED` |
| Foreground rule | `mask > 0` |
| Connectivity | 8 |
| Unit | connected_component |
| Metric | `component_ratio` = component_pixels / (native_height * native_width) |
| Coordinate system | native mask geometry normalized by native full-image area |

## Quantile method

- Implementation: `numpy.quantile`
- Method: default 'linear' interpolation
- Call: `np.quantile(values, [0.25, 0.50, 0.75])`
- Precision: float64
- Derivation cases: 770
- Derivation objects: 1161

## FROZEN thresholds

| Quartile | Value |
|---|---|
| Q25 | `0.0001497998649691358` |
| Q50 | `0.0003401438395182292` |
| Q75 | `0.0008279682677469136` |

## Boundary semantics

| Stratum | Condition |
|---|---|
| TINY | `x <= Q25` |
| SMALL | `Q25 < x <= Q50` |
| MEDIUM | `Q50 < x <= Q75` |
| LARGE | `x > Q75` |
| rounding | `no rounding applied before classification` |
| boundary_value_goes_to | `lower bin` |

## Historical reference (immutable)

- `kub_size_v1` (HISTORICAL_v2_IMMUTABLE)
- Q25 `0.0001499766777599`
- Q50 `0.00033976472454305`
- Q75 `0.0008266496069636999`
- Reproduced exactly: True

## Governance

- Threshold frozen: True
- VAL content reads before freeze: 0
- TEST content reads: 0
- Supervisor authorized: True

## Provenance

- Source manifest SHA: `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6`
- Object table SHA: `5c270dd4cb09e5697fdd5d7eb2ae4465f82489bb71ccead019a558934f5d1a08`
