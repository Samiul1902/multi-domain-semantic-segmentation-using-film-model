# Phase 12 — Historical README Errata (provenance repair)

**Created:** 2026-09-21T00:33:02.161503+00:00
**Status:** `HISTORICAL_README_PROSE_ERROR` · `DO_NOT_EDIT_HISTORICAL_ARTIFACT` · `AUTHORITATIVE_AUDIT_PRECEDENCE`

## What happened

During Phase 12 **Part 1A**, `notebooks/phasewise/phase_12_oracle_roi/README.md` was edited to
correct a factually wrong prose statement. That edit was documentation-only, but it violated
the requested historical-artifact immutability boundary.

In Phase 12 **Part 1B** the file was **restored byte-exactly from version control**
(`git checkout HEAD -- <path>`), proven by an **empty `git diff`**.

## Restoration proof

| Evidence | Value |
|---|---|
| VCS-restored on-disk SHA-256 (CRLF working tree) | `5f8db1300364a45cf37997fcb3c3094ba875782f539b32a361bfc987780d0990` |
| LF-normalised SHA-256 (as reported by Part 1A) | `9cb2eb5fae0021ab500fa7f79faf2e94e574aa9f0da89e891e6a830bfab8b23d` |
| git blob object | `7be8bd177e71dc95c1919ab0aa98109472f07e1c` |
| `git diff` after restore | **empty** (working tree == VCS version) |
| file size | 1259 bytes (CRLF; 23 CRLF, 0 bare LF) |

> **Line-ending note (recorded for honesty):** the SHA reported by Part 1A
> (`9cb2eb5f…`) was computed on **LF-normalised** text because Part 1A reconstructed the
> content rather than hashing the original file. The true on-disk file uses **CRLF** and
> hashes to `5f8db130…`. Both describe the same logical content; the VCS-restored bytes are
> authoritative.

## The incorrect historical statement

> **Historical README statement (INCORRECT):** "Phase 12 proves **+16.2% Dice and 100% tiny
> recall** given perfect GT bounding boxes."

## Authoritative historical audit values

Source: `reports/audits/phase12_oracle_roi_upper_bound.json`

| Quantity | Global | Oracle 25% | Paired delta |
|---|---|---|---|
| Macro Dice | 0.6527764131996552 | 0.7757361537396281 | **+0.12295974053997309 absolute** = **+12.295974 percentage points** |
| Tiny recall | 0.7808219178082192 | 0.9863013698630136 | +0.2054794520547944 |

- The README's "**+16.2%**" overstates the audit's **+12.30 pp**.
- The README's "**100% tiny recall**" is wrong: the audit records **0.9863013698630136**
  (57/73 recovered globally → 72/73 under oracle25; 1 tiny component remained missed).

## Disposition

1. The historical README is **restored and MUST NOT be edited again**.
2. The corrected figures live **here**, as a separate companion errata artifact.
3. Where the historical README prose conflicts with the frozen historical audit, the
   **audit takes precedence** (`AUTHORITATIVE_AUDIT_PRECEDENCE`).
4. Historical numerical results remain `HISTORICAL_v2_PROVENANCE_ONLY` and are never
   clean-v3 evidence.

## Immutability

- Restored README SHA: `5f8db1300364a45cf37997fcb3c3094ba875782f539b32a361bfc987780d0990`
- Historical notebook SHA: `ba6a7e02562c17ab5be48d8291819ba5209510e4aeb016f5853d5199b9dd6d0e`
- Historical audit SHA: `3073662ad772f17fb90d040dddd3be068b94966f1337eb9c6f48f440d2df91e1`
