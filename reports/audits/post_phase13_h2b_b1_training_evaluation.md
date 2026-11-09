# H2B-B1 — Training / Execution Audit

- **Status: PASS**
- experiment: `post_phase13_h2b_kub_localizer_r512_h128_sigmaeq075_softtargetfocalgamma2_deploymentbalance_seed42_clean_v3`

## Bindings

| role | SHA-256 |
|---|---|
| h2b_protocol_sha | `22d4e363a9375bc12828c944b1583921efa77d45b6df7d6387738d13d950949e` |
| h2a_adjudication_sha | `02af0558696880f5842abaefbc8f30e5b44b20a700350bd70f963e0b844aada6` |
| loss_implementation_sha | `40d359e36a5579ea7544a1f0079aa999e024b8b144956493c184388766c27b75` |
| unit_audit_sha | `cb870cade9b7daadccab05b9d923cd0ec686b91126e3f08c9d7cb33f1451f94d` |
| runner_sha | `444f0ea7b5f6ce76c3d0955febfc67ebd0c36a80913604384ded054c443f7ddd` |
| config_sha | `0ee34404c67e36aa27ef880c59295208f662908af996cf634f6a922875340f12` |
| one_axis_execution_diff_sha | `1ccda6dbf155e4f9e96027a24e08ef3ee5821125edf0ac70654ba3b3328b78b6` |
| invalidation_sha | `77d33b66357530117814bbd72eede5ad7810d964d4b19f45530f3a88f55cd2f5` |
| defect_linkage_sha | `df5ba20f83bc2e46cb8462e453a71761fa62bcdf54286cfc28487406a9c61401` |
| provenance_repair_tests_sha | `4df2332a4d3f9f82fb8b41211e2d38f98cd805a706ca36e80320bdd4fb71711b` |

## Initialization

- INITIALIZATION: **FRESH_FROM_SCRATCH_SEED42**
- WARM_START: **NO**
- PRETRAINED_LOCALIZER_STATE: **NONE**

## Loss (active objective identity)

- class: `src.losses.soft_target_focal_bce.SoftTargetFocalBCE`
- label: `H2B_SOFT_TARGET_FOCAL_BCE_GAMMA2`
- gamma: **2.0**
- modulation detached: NO
- dice term: NONE · auxiliary loss: NONE
- objective_change_id: `H2B_OBJECTIVE_ONLY_SOFT_TARGET_FOCAL_BCE_GAMMA2`
- stale `loss_alpha` present: **False** · stale `loss_beta` present: **False**

## Termination

- reason: **EARLY_STOPPING_PATIENCE**
- completed epochs: **46**
- best epoch: **31**
- final bad epochs: **15**

## Best six-term tuple

```
[0.3762759719105191, 0.6111111111111112, 0.5921052631578947, 0.2151639344262295, -0.005777940678754472, -0.000277110381060853]
```

## Selection replay

- status: **PASS** · mismatches: **0** · best epoch 31 · max term diff `7.199e-17`

**No trajectory-reproduction gate vs H2A/Phase-13** (SEC 11).

## Standalone best-checkpoint proposal metrics

| metric | value |
|---|---|
| proposal_total_count | 488 |
| proposal_count_per_image | 4.737864077669903 |
| proposal_pixel_any_hit_precision | 0.2151639344262295 |
| proposal_bbox_any_hit_precision | 0.21311475409836064 |
| tiny_recall90 | 0.6111111111111112 |
| overall_recall90 | 0.5921052631578947 |
| overall_recall50 | 0.6973684210526315 |
| any_overlap_recall | 0.7368421052631579 |
| mean_coverage | 0.6778087714762865 |
| mean_proposal_union_area | 0.005777940678754471 |
| score_max | 0.10875558853149414 |
| score_iqr | 0.0 |
| fraction_exactly_at_max | 0.7930327868852459 |
| roc_auc_score_to_pixel_any_hit | 0.6149073728708193 |
| pr_auc_score_to_pixel_any_hit | 0.22895342337838293 |

## Counters

| counter | value |
|---|---|
| logical_training_experiments | 1 |
| execution_attempt_count | 2 |
| proposal_configurations | 1 |
| proposal_grid | 0 |
| downstream_segmentation_forwards | 0 |
| downstream_segmentation_model_constructions | 0 |
| oracle_reruns | 0 |
| threshold_searches | 0 |
| test_reads | 0 |
| external_test_reads | 0 |

**Downstream segmentation: NOT RUN (explicit stop boundary).**
**H2B outcome: NOT adjudicated.**

next_action: `WAIT_FOR_SUPERVISOR_H2B_B2_AUTHORIZATION`
