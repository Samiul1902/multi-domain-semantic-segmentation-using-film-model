# Phase 13 Part 1B-R0 — Execution Binding Validation

- **Status:** `CHECK_REQUIRED`
- **Date:** 2026-09-21 · **Model:** Gemini 3.8 Flash Medium
- **Reason:** every authorized static/unit gate PASSes, but one scientifically material
  executable field (the training objective) has an unresolved disagreement between the
  frozen sources. Section 5 forbids inventing a value, and section 20 is therefore not met.

## Gate results

| Gate | Result |
|---|---|
| Experiment-ID collision check | PASS — both dirs ABSENT; nothing deleted/overwritten |
| Config parses | PASS — 42 top-level keys |
| All required fields present | PASS — 27/27 sections |
| R2 SHA matched | PASS — `ab451e03…5e53` |
| R2 status matched | PASS — `SUPERVISOR_FROZEN_R2_READY_FOR_PART1B_TRAINING` |
| Manifest bound `phase4_v3` | PASS — strict validation passed (7 files) |
| Population 770/1161 · 103/152 | PASS — reproduced exactly via the v3 manifest join |
| TRAIN/VAL patient overlap 0 | PASS |
| TEST lock | PASS — `test_allowed=false`, 0 reads |
| Historical runner unchanged | PASS — `5985b9eb…555a` |
| Historical helper unchanged | PASS — `457aa10a…1590` |
| New runner compile/import | PASS — import performs no CUDA/model/data work |
| New wrapper compile/import | PASS |
| 4-term unit tests | PASS — **17/17** |
| Secondary-diagnostic exclusion test | PASS — structural (no diagnostic parameter exists) |
| Grid search disabled | PASS — no `itertools.product`; `GRID_SEARCH_ENABLED=False` |
| One proposal config only | PASS — `PROPOSAL_CONFIGURATION_COUNT=1` |
| Heatmap 128 explicitly encoded | PASS — runner **and** wrapper |
| No executable `phase4_v2` path | PASS — guard positive + negative controls verified |
| Config binding diff table complete | PASS — every field traced |
| Scientifically material changes | **0** |
| Immutability (section 19) | PASS — all 8 hashes exact |
| **Loss objective bound unambiguously** | **CHECK_REQUIRED** |

## Governance counters

training **0** · optimizer created **false** · optimizer steps **0** · model constructed
**false** · forward passes **0** · localizer inference **0** · proposals **0** · grid configs
evaluated **0** · VAL images evaluated **0** · run lock **false** · checkpoints written **0** ·
history rows **0** · TEST reads **0** · Phase 14 **not started**.

## The one open item

**`LOSS_OBJECTIVE_BINDING_NOT_PHYSICALLY_RESOLVED`** (BLOCKING)

| Source | Training objective |
|---|---|
| R2 protocol (rank 1) | **silent** — no loss field |
| Accepted Part-1A candidate (rank 2) | `0.75 CenterNet focal (alpha 0.25, gamma 2.0) + 0.25 soft Dice` |
| Historical EXECUTING code (evidence) | `CenterNetFocalLoss(alpha=2.0, beta=4.0)` — **no Dice, alpha=2.0** |

The composite option additionally maps to `SoftFocalDiceLoss`, whose focal term is
overwritten by dead code at line 20. R0 records the discrepancy explicitly instead of
choosing. Supervisor options: **L1** (executing objective), **L2** (Part-1A composite,
variant pinned), **L3** (exact module + params + SHA).

## Next action

`WAIT_FOR_SUPERVISOR_PHASE13_PART1B_EXECUTION_BINDING_REVIEW` — stopped, no training.
