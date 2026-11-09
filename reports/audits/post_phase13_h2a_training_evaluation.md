# POST-PHASE-13 H2-A-B1 — EXECUTION AUDIT

- status: **PASS**
- experiment id: `post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`
- completed epochs: **98** | termination: **EARLY_STOPPING_PATIENCE**
- best epoch: **83** | latest epoch: **98** | final bad_epochs: **15**

## Best six-term tuple
```
[0.4522162369629855, 0.6944444444444444, 0.6381578947368421, 0.27571115973741794, -0.0047946270615735415, -1.8425761369558482]
```

## Checkpoint SHAs

| artifact | SHA-256 |
|---|---|
| best.pt | `2e2e8f7909649f50cf7b830aab357d9e14a4b62b71a00fc0efe22aa300ba54c8` |
| latest.pt | `429041f8aabfda238cf226f3872991c236c63a8fd6938656d4016bebb1492588` |
| history.csv | `ed96c4b617a8940c30df30d9a9b8f562819e31d1370b31ee60776142fd077b99` |

## Trajectory reproduction (§10)

| quantity | value |
|---|---|
| overlapping epochs | 68 |
| max abs train_loss diff | 4.441e-16 |
| max abs val_loss diff | 0.000e+00 |
| train_loss exact match | False |
| val_loss exact match | True |
| LR mismatches | 0 |
| gradient semantics changed | **NO** |
| overlapping checkpoint cross-checks | 0 (best epoch 83 / latest 98 are not 31/53/68 — no overlap, as the protocol allows) |

## Selection replay (§14)

- result: **PASS** | mismatches **0** | max abs term diff **2.220e-16**
- replayed best epoch **83** · final bad_epochs **15** · early stop **98**

## Standalone best-checkpoint proposal evaluation (§16)

| quantity | value |
|---|---|
| proposal_total_count | 457 |
| proposal_count_per_image | 4.436893203883495 |
| proposal_pixel_hit_count | 126 |
| proposal_pixel_any_hit_precision | 0.27571115973741794 |
| proposal_bbox_any_hit_precision | 0.2735229759299781 |
| tiny_recall90 | 0.6944444444444444 |
| overall_recall90 | 0.6381578947368421 |
| overall_recall50 | 0.8223684210526315 |
| any_overlap_recall | 0.875 |
| mean_coverage | 0.7878969538240504 |
| mean_proposal_union_area | 0.0047946270615735415 |
| score_max | 0.14163722097873688 |
| score_iqr | 0.0016540437936782837 |
| fraction_exactly_at_max | 0.6455142231947484 |
| roc_auc_score_to_pixel_any_hit | 0.7011101520164964 |
| pr_auc_score_to_pixel_any_hit | 0.3729361181989911 |

### Cohorts

| cohort | n | covered90 | covered90 rate | any_overlap |
|---|---|---|---|---|
| hard_tiny | 15 | 3 | 0.2 | 7 |
| global_empty | 8 | 2 | 0.25 | 3 |
| multi_component | 98 | 61 | 0.6224489795918368 | n/a |

## Comparison vs Phase-13 best (epoch 53) — DESCRIPTIVE ONLY

| quantity | Phase-13 | H2A | delta |
|---|---|---|---|
| proposal_total_count | 494 | 457 | -37 |
| proposal_pixel_any_hit_precision | 0.24696356275303644 | 0.27571115973741794 | 0.028747596984381507 |
| proposal_bbox_any_hit_precision | 0.24898785425101214 | 0.2735229759299781 | 0.02453512167896596 |
| tiny_recall90 | 0.6805555555555556 | 0.6944444444444444 | 0.01388888888888884 |
| overall_recall90 | 0.5986842105263158 | 0.6381578947368421 | 0.03947368421052633 |
| overall_recall50 | 0.7894736842105263 | 0.8223684210526315 | 0.0328947368421052 |
| any_overlap_recall | 0.8486842105263158 | 0.875 | 0.02631578947368418 |
| mean_coverage | 0.7584022780771768 | 0.7878969538240504 | 0.0294946757468737 |
| mean_proposal_union_area | 0.004846047236646118 | 0.0047946270615735415 | -5.1420175072576166e-05 |
| proposal_score_max | 0.1250653713941574 | 0.14163722097873688 | 0.016571849584579468 |
| fraction_exactly_at_max | 0.6821862348178138 | 0.6455142231947484 | -0.03667201162306544 |
| proposal_count_per_image | 4.796116504854369 | 4.436893203883495 | -0.3592233009708732 |

Every quantity improves except the proposal count (fewer, more precise proposals) and the mean
proposal union area (marginally smaller). **No superiority claim. No significance claim. No threshold change.**

## Counters

| counter | value |
|---|---|
| logical_training_experiments | 1 |
| optimizer_construction | 1 |
| localizer_model_constructions | as technically required within the SAME logical run |
| cuda | required |
| proposal_configs | 1 |
| proposal_grid | 0 |
| downstream_segmentation_model_constructions | 0 |
| downstream_segmentation_forwards | 0 |
| oracle_reruns | 0 |
| test_reads | 0 |
| external_test_reads | 0 |

## Stop boundary

- downstream regional segmentation: **NOT RUN**
- R1 selective acceptance applied: **NO**
- segmentation models loaded: **NO**

## Adaptive-development disclosure

H2A is an adaptive VAL-development experiment initiated after Phase 13 `REVISE_LOCALIZER` and H1
acceptance-only insufficiency. The H2A selection rule was frozen BEFORE training. VAL remains
development data. No H2A result substitutes for final TEST evaluation. TEST remains untouched.

**next_action: `WAIT_FOR_SUPERVISOR_H2A_DOWNSTREAM_AUTHORIZATION`**
