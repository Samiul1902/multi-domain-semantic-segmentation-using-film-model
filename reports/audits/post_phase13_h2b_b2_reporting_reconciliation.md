# POST-PHASE13 H2B-B2 — Quantitative Reporting Reconciliation

- **Status: PASS**
- **Classification: `CHAT_TRANSCRIPTION_ONLY`**
- Scientific adjudication performed: **NO** · Inference/training performed: **NO**

## Finding

The pasted H2B-B2 chat final note contained quantitative values that do **not** appear in any
persisted artifact. The authoritative on-disk tables were always correct; the error existed
only in the chat transcript.

## Authoritative model summary (read from disk)

| model | H2B Dice | H2B−GLOBAL | H2B−P13 | H2B−H2A | fp_delta_vs_global | recov/loss vs GLOBAL |
|---|---|---|---|---|---|---|
| UNet | 0.279848 | -0.314331 | -0.022465 | -0.033931 | 9625.621359 | 10/0 |
| Attention U-Net | 0.290569 | -0.339236 | -0.018050 | -0.029604 | 9857.815534 | 7/0 |
| UNet++ | 0.294688 | -0.345827 | -0.016667 | -0.028358 | 10507.456311 | 11/0 |
| DeepLabV3+ | 0.264614 | -0.295637 | -0.012678 | -0.024303 | 11031.233010 | 16/0 |

## Stale values (chat only — NOT on disk)

| quantity | pasted chat | authoritative |
|---|---|---|
| recoveries/losses vs GLOBAL | 8/0 · 5/0 · 5/0 · 4/0 | **10/0 · 7/0 · 11/0 · 16/0** |
| fp_delta_vs_global | +7203.65 · +7410.66 · +7722.28 · +8083.96 | **+9625.621359 · +9857.815534 · +10507.456311 · +11031.233010** |
| mean_h2b_fp (UNet) | 8500.90 | **10922.873786** |

## Search result

- stale values found in persisted artifacts: **NO**
- `8500.90` found anywhere on disk: **NO**
- persisted H2B final-note artifact: **does not exist**
- notebook vs model summary: **PASS**

## Repair applied

- authoritative tables modified: **NO**
- frozen audits rewritten: **NO**
- continuity docs required correction: **NO** (they never carried the stale values)

## Preserved valid evidence (descriptive, unadjudicated)

- H2B macro Dice is below GLOBAL, Phase13 predicted **and** H2A predicted for all four architectures
- component losses vs GLOBAL are **zero** for all four
- cross-architecture union recovery retained as descriptive evidence

- scientific result changed: **NO**
- B2 execution status changed: **NO**

next_action: `WAIT_FOR_SUPERVISOR_H2B_OUTCOME_ADJUDICATION_AUTHORIZATION`
