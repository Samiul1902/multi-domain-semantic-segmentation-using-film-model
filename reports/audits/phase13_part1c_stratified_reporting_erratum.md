# PHASE-13 PART-1C — STRATIFIED REPORTING ERRATUM

- **classification:** `PART1C_FINAL_NOTE_STRATIFICATION_REPORTING_ERROR_ONLY`
- **status:** **PASS**

## Defect

The Part-1C chat **final note** reported:

| stratum | reported (WRONG) | canonical (physical table) |
|---|---|---|
| TINY | 49 / 72 | **49 / 72** |
| SMALL | **23 / 28** | **16 / 28** |
| MEDIUM | **17 / 36** | **19 / 36** |
| LARGE | **2 / 16** | **7 / 16** |

Those three wrong counts appear **nowhere** in any persisted artifact. The physical
stratified table and the reviewer notebook were both already correct. The error was
confined to the narrative final note.

## Canonical physical values

| stratum | N | bbox covered90 | bbox rate | pixel covered90 | pixel rate |
|---|---|---|---|---|---|
| TINY | 72 | **49** | 0.6805555555555556 | **50** | 0.6944444444444444 |
| SMALL | 28 | **16** | 0.5714285714285714 | **20** | 0.7142857142857143 |
| MEDIUM | 36 | **19** | 0.5277777777777778 | **22** | 0.6111111111111112 |
| LARGE | 16 | **7** | 0.4375 | **9** | 0.5625 |
| ALL | 152 | **91** | 0.5986842105263158 | **101** | 0.6644736842105263 |

Aggregate overall **91/152 (bbox)** and **101/152 (pixel)** are unchanged.

## Corrected interpretation

`DESCRIPTIVE_STRATIFIED_LOCALIZATION_RESULT`

> Under historical bbox coverage at the frozen 90% criterion, TINY was 49/72 (68.1%),
> SMALL 16/28 (57.1%), MEDIUM 19/36 (52.8%), and LARGE 7/16 (43.8%). LARGE had the
> lowest covered90 rate among the four strata, but the result does not support the
> previously reported 2/16 (12.5%) figure.

**Explicitly withdrawn:** `SMALL = 82%` and `LARGE = 12.5%`. No significance testing
was performed and no causal hardness claim is made.

## Immutability

| declaration | value |
|---|---|
| scientific inference changed | **NO** |
| checkpoint changed | NO |
| proposal outputs changed | NO |
| tables changed | NO |
| notebook already correct | **YES** (left byte-exact) |

| counter | value |
|---|---|
| model inference | 0 |
| proposal generation | 0 |
| grid configs | 0 |
| TEST reads | **0** |
