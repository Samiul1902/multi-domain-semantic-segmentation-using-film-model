# Phase 13 — Clean-v3 Localizer Loss Binding Amendment (R2A)

- **Status:** `SUPERVISOR_AUTHORIZED_LOSS_BINDING_L1`
- **Date:** 2026-09-21 · **Model:** Gemini 3.8 Flash Medium
- **Scope:** `LOSS_OBJECTIVE_ONLY` — **additive**; does **not** supersede any R2 field

## Base protocol (unchanged)

| Item | Value |
|---|---|
| Base | `SUPERVISOR_FROZEN_R2` |
| Path | `reports/audits/phase13_clean_v3_localizer_protocol_frozen_r2.json` |
| SHA-256 | `ab451e03366c589fae5c303ebf1382e086f4f115b97768eb36d491256a3b5e53` |
| Modified by this task | **No** |

## The loss decision — L1

```python
src.losses.localization.CenterNetFocalLoss(alpha=2.0, beta=4.0)
```

| Field | Value |
|---|---|
| Loss class | `src.losses.localization.CenterNetFocalLoss` |
| alpha | **2.0** |
| beta | **4.0** |
| Dice term | **NONE** |
| focal_weight | *absent* (no 0.75 weighting) |
| dice_weight | **0.0** |
| Label | `EXECUTING_HISTORICAL_CENTERNET_FOCAL_L1` |
| Role | `PRIMARY_PHASE13_CLEAN_V3_LOCALIZER_OBJECTIVE` |

**Reason:** the physically verified historical **executing** trainer has higher authority than
the historical config/prose when they disagree.

## Physical verification (prose alone was NOT trusted)

| Check | Result |
|---|---|
| `scripts/training/train_phase13b_localizer.py` SHA-256 | `5985b9eb…555a` — **matches expected** |
| Executing construction (line 121) | `criterion=CenterNetFocalLoss(alpha=2.0, beta=4.0)` — **exact** |
| Class signature | `CenterNetFocalLoss(self, alpha=2.0, beta=4.0)` |
| `SoftFocalDiceLoss` constructed on executable path | **No** (imported at lines 16–17, never called) |
| Criterion assignments in the runner | **exactly 1** |

**Best-checkpoint lineage — used the executing path: YES.** The runner has exactly one criterion
assignment, so every epoch of the historical run — including best epoch 73 — was optimised with
`CenterNetFocalLoss(alpha=2.0, beta=4.0)`
(`checkpoints/…_seed42_v1/best.pt`, SHA `ece906df…cace`).

> Notable: that checkpoint's declared `configuration.loss` field reads
> `soft_focal_dice / focal_weight 0.75 / dice_weight 0.25 / alpha 0.25 / gamma 2.0` — copied
> verbatim from the historical YAML. It is **declared-only, not executing**. That exact
> declared-vs-executing divergence is the ambiguity R2A resolves.

## Dispositions

| Item | Disposition |
|---|---|
| Part-1A documented composite (`0.75 CenterNet focal (α 0.25, γ 2.0) + 0.25 soft Dice`) | `SUPERSEDED_DOCUMENTED_NOT_EXECUTING_OBJECTIVE` — preserved as provenance; candidate/protocol-matrix rows **not deleted** |
| `SoftFocalDiceLoss` dead-code defect (focal term overwritten at `localization.py` line 20) | `NON_PRIMARY_IMPLEMENTATION_DEFECT` — **no repair required**; the class is not on the clean-v3 path. Module **not modified** |

## Materiality

| Question | Answer |
|---|---|
| Material change relative to R2? | **NO** — R2 is silent on loss; this resolves a gap, not an R2 decision |
| Material resolution of prior ambiguity? | **YES** |
| Supervisor-authorized? | **YES** (L1 only) |
| All other R2 fields | **UNCHANGED** |
| Resulting executable protocol identity | **R2 + R2A_LOSS_BINDING** — *not* a new experimental variant |

## Governance

training 0 · model constructions 0 · forward passes 0 · optimizer creations 0 · inference 0 ·
proposals 0 · grid configs 0 · TEST reads 0 · Phase 14 not started · R2 unmodified · R3 not created.

**Next:** `WAIT_FOR_SUPERVISOR_PHASE13_PART1B_TRAINING_REAUTHORIZATION`
