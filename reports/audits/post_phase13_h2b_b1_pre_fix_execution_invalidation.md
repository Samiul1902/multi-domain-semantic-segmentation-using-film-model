# H2B-B1 — Pre-Fix Execution Invalidation

- **Status: INVALIDATED_AND_PRESERVED**
- **Classification:** `INVALIDATED_EXECUTION_ATTEMPT__NON_SCIENTIFIC_CODE_PROVENANCE_DEFECT`
- **Experiment id:** `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`
- **Reason:** `STALE_OBJECTIVE_IDENTITY_METADATA_IN_CHECKPOINT_AND_RESUME_CONTRACT`

## What was wrong

The H2B runner executed the **correct** `SoftTargetFocalBCE(gamma=2.0)` objective, but its
resume-identity contract, checkpoint metadata and start/completion audits still carried the
stale Phase-13 CenterNet fields `loss_alpha=2.0` / `loss_beta=4.0` and declared
`protocol_identity = R2 + R2A_LOSS_BINDING` as the **active** identity.

Observed in the checkpoint: `configuration/_phase13_execution_metadata.loss_alpha = 2.0`,
`loss_beta = 4.0`.

## Interrupted attempt

| field | value |
|---|---|
| completed epochs | **4** (1, 2, 3, 4) |
| history SHA | `12b28ab5fb209ce9a70df8d331d50a3b1bf7cb075e68a93c709265b40b19b9e6` |
| latest.pt SHA | `b8565e095c7b1b487220ed2448903876fed37355b2cb9c66dfbdc619998c7bac` |
| best.pt SHA | `f3206ecc3802b0b8da449cd1a612441944298a1252d0ac13db48144f74ef0188` |
| runner SHA (at attempt) | `2e9c1faf0a6a2e823fcd0dec4a47401fa979f43b574152068aee55d76bda542d` |
| config SHA (at attempt) | `2ceaa71d614475fed54248c353e247848f41df3ace423e3c36aba63d59431152` |

## Preservation

Archived (not deleted) at
`reports/superseded/post_phase13_h2b_b1_invalidated_pre_fix_attempt_20260923T0936Z/`:

- `experiments/history.csv`
- `experiments/.experiment.lock`
- `checkpoints/latest.pt`
- `checkpoints/best.pt`
- `audits/post_phase13_h2b_b1_training_start.json`
- `audits/post_phase13_h2b_b1_training_start.md`
- `audits/training.log`

## Promotion

- scientific measurements promoted: **NO**
- checkpoint promoted: **NO**
- history promoted: **NO**
- H2B hypothesis changed: **NO**
- H2B protocol changed: **NO**

The invalid pre-fix execution is **NOT** a second scientific experiment.
`logical_scientific_experiment_count = 1`; `execution_attempt_count = 2`.

**TEST reads: 0 · external TEST reads: 0**
