# POST-PHASE13 H2C-B1 — Training / Execution Audit

- **Status: PASS**
- experiment: `post_phase13_h2c_kub_localizer_spatialhead3x3relu_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`

## Bindings

| role | SHA-256 |
|---|---|
| h2c_protocol_sha | `91166259c10a84e9526eda43e83b227cc760a37b8834a4d4a65fe3e5a90ba4b6` |
| h2c_rng_preflight_sha | `aa5a9b7a7a4a39fcaa823ca3ef00f82779af9ae147d037d9c1bc82b86041fdda` |
| counter_clarification_sha | `5c7152295fbf6a075174fcb928dc296a4503e6b2508a5d94bf4932117d2323a4` |
| runner_sha | `666aabcb58572f6c0892302cb6ff1617b3b19f642dc37a688c84943cc1c66e70` |
| runner_sha_that_produced_the_run | `fbc8e2432732da1b3a275c513c021f7c5600b708ada0f95187fe04753c87a0c4` |
| config_sha | `b96223eecade2938a9ca9733ddcfba1bbd2f7cd34155ab4d48a1fba51f09bc33` |
| implementation_diff_sha | `bd299f7dcaf350231f0b9c3311b371fe90445f25d0123b97ff20bb668498b0f9` |
| audit_identity_correction_sha | `19b40c50ffdd02f2c6f77af794093669cf0de05254c0af899bd60366adaad5b3` |
| history_sha | `09ae65468fb981daa9a65bb8b0b77ad2e47f9fcc863caa9c7e972a83d5640be0` |
| best_pt_sha | `021ab63f2cbc064b5c4de90c5f181ebee75f8d10e7dead2eb53f4f9578060f98` |
| latest_pt_sha | `920282ace98f9972dc560466e019fac558f48238fcf3739223e09679a590d002` |
| selection_replay_sha | `fe2c47209bee3ae9dd676c7b7ae13b4612f7272a2b1aa7b17814db69c46098cb` |
| standalone_evaluation_sha | `711768cdda39b8e8e62e4af6e0b1e076f30bf18f3d29c05d393022f7f58df346` |
| reviewer_notebook_sha | `b6200ee59568a4555510962c60dda89583b5668031f7ce3fe61bcd2f74284369` |
| standalone_table_shas | `{'case_proposals': '97d22ad10d9a3a989b1367f97374111e1ac77947658e265aeecca2d84ccfe128', 'proposals': 'd742834a7275e1493428382d9b5da38ee52045969fa4c3c1304835fe5166d46c', 'component_coverage': '13faa3854323a5aeb197b3948152e0167b220b5e3c069a7ba964db0a79a69871', 'size_stratified': 'b298372a4a54af38999d5c0302d4efe823a291c022d7cd17d92f1d431cf020f9', 'three_way_comparison': 'fbd110a49347aa72b8510b42806e9635859981edcb10fc7fbce00807a92a1876'}` |

## Head

- `SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1`
- tensors in checkpoint: head.conv1x1.bias, head.conv1x1.weight, head.conv3x3.bias, head.conv3x3.weight
- checkpoint records head identity: `SPATIAL_DISCRIMINATIVE_HEAD_3X3_RELU_1X1_V1`
- checkpoint records H2C protocol SHA: `91166259c10a84e9526eda43e83b227cc760a37b8834a4d4a65fe3e5a90ba4b6`

## Scientific change register

| field | value |
|---|---|
| logical_training_experiments | 1 |
| scientific_axes_changed | 1 |
| head_architecture_changed_vs_h2a | YES |
| head_initialization_changed_vs_h2a | YES_PART_OF_HEAD_AXIS |
| post_freeze_h2c_initialization_change | NO |
| loss_changed | NO (H2A CenterNetFocalLoss alpha=2.0 beta=4.0 retained) |
| target_changed | NO |
| sigma_changed | NO |
| backbone_changed | NO |
| optimizer_changed | NO |
| scheduler_changed | NO |
| data_changed | NO |
| augmentation_changed | NO |
| checkpoint_selection_changed | NO |
| proposal_policy_changed | NO |
| fusion_changed | NO |
| segmentation_checkpoints_changed | NO |

## Termination

- reason: **EARLY_STOPPING_PATIENCE**
- completed epochs: **72**
- best epoch: **57**
- final bad epochs: **15**

## Best six-term tuple

```
[0.4598833654705356, 0.75, 0.6973684210526315, 0.2662337662337662, -0.005357889447390799, -1.7253184639490569]
```

## Selection replay

- status **PASS** · mismatches **0** · best epoch 57 · max term diff `9.888e-17`

## Initialization equivalence (material interpretation context)

- H2A and H2C initial logits identical: **True**
- initial loss (CenterNet focal): **19.119539** (both)
- H2C epoch-1 train_loss: **10.039225600544036** (H2A reference 0.001105)
- Both heads produce identical initial logits and identical initial loss. H2C's epoch-1 train_loss is nevertheless far higher than H2A's because the frozen zero terminal weights make H2C learn more slowly at first. Early-epoch loss magnitudes are therefore NOT comparable across branches.

## Standalone best-checkpoint proposal metrics

| metric | value |
|---|---|
| proposal_total_count | 462 |
| proposal_count_per_image | 4.485436893203883 |
| proposal_pixel_any_hit_precision | 0.2662337662337662 |
| proposal_bbox_any_hit_precision | 0.26406926406926406 |
| tiny_recall90 | 0.75 |
| overall_recall90 | 0.6973684210526315 |
| overall_recall50 | 0.8223684210526315 |
| any_overlap_recall | 0.8881578947368421 |
| mean_coverage | 0.8084159294904666 |
| mean_proposal_union_area | 0.005357889447390801 |
| score_max | 0.1509026288986206 |
| score_iqr | 0.004663035273551941 |
| fraction_exactly_at_max | 0.5497835497835498 |
| roc_auc_score_to_pixel_any_hit | 0.7564213252751997 |
| pr_auc_score_to_pixel_any_hit | 0.412665101791798 |

## Disclosed defect

`PERSISTED_REPORTING_DEFECT__AUTHORITATIVE_SCIENTIFIC_STATE_CORRECT` — runner-generated reporting payloads only; scientific impact **NONE**; corrected additively **YES**

## Counters

| counter | value |
|---|---|
| logical_training_experiments | 1 |
| proposal_configurations | 1 |
| proposal_grid | 0 |
| downstream_segmentation_forwards | 0 |
| downstream_segmentation_model_constructions | 0 |
| oracle_reruns | 0 |
| threshold_searches | 0 |
| test_reads | 0 |
| external_test_reads | 0 |

**Downstream segmentation: NOT RUN.** **H2C outcome: NOT adjudicated.**

next_action: `WAIT_FOR_SUPERVISOR_H2C_B2_AUTHORIZATION`
