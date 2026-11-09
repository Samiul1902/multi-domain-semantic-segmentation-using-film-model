# POST-PHASE13 H2C-B2 — Freeze Manifest

- **Status: FROZEN_PRE_FIRST_SEGMENTATION_FORWARD**

| field | value |
|---|---|
| h2c_experiment_id | `post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3` |
| h2c_b1_best_checkpoint_path | `checkpoints/post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3/best.pt` |
| h2c_b1_best_checkpoint_sha256 | `021ab63f2cbc064b5c4de90c5f181ebee75f8d10e7dead2eb53f4f9578060f98` |
| selected_epoch | `57` |
| head_identity | `SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1` |
| authoritative_h2c_protocol_sha | `91166259c10a84e9526eda43e83b227cc760a37b8834a4d4a65fe3e5a90ba4b6` |
| authorization_identity | `USER_SUPERVISOR_MESSAGE_POST_H2C_B1` |
| scientific_axis_change_count | `1` |
| test_read_counter | `0` |
| external_test_read_counter | `0` |
| downstream_forward_counter_before_b2 | `0` |

## Confirmations

- `NO_SCIENTIFIC_PARAMETER_SELECTED_USING_B2_RESULTS` = **True**
- `H2C_B2_IS_EVALUATION_ONLY` = **True**

## Segmentation checkpoints

| model | SHA-256 |
|---|---|
| unet | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` |
| attention_unet | `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3` |
| unetpp | `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269` |
| deeplabv3plus | `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad` |

## Proposal policy

- source `post_phase13_h2c_best_checkpoint_proposals.csv` (462 rows)
- threshold 0.10 / margin 0.20 / top_k 5 / NMS 0.30
