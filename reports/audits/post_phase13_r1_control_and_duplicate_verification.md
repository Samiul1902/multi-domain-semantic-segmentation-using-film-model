# POST-PHASE-13 R1 — CONTROL AND DUPLICATE VERIFICATION

- status: **PASS**
- run id: `post_phase13_regional_revision_r1_selective_acceptance`

## R1-C0 control reproduction

R1-C0 is exactly the frozen Phase-13 policy, so it must reproduce the frozen Part-1D-B
`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED` result. Primary criterion: **max abs per-case Dice
difference <= 1e-6**.

| model | cases | max abs Dice | max abs IoU | max abs precision | max abs recall | max abs TP | max abs FP | max abs FN | PASS |
|---|---|---|---|---|---|---|---|---|---|
| unet | 103/103 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | **PASS** |
| attention_unet | 103/103 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | **PASS** |
| unetpp | 103/103 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | **PASS** |
| deeplabv3plus | 103/103 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | 0.000e+00 | **PASS** |

**Control reproduction result: PASS**

IoU / precision / recall / TP / FP / FN differences are reported descriptively; no new scientific threshold is created from them.

## C1 / C3 duplicate verification

R1-C1 and R1-C3 have identical frozen membership, so their downstream outputs are identical **by
construction**. They are **not** treated as independent evidence.

| quantity | result |
|---|---|
| max_abs_diff_policy_dice | `0.0` |
| max_abs_diff_policy_iou | `0.0` |
| max_abs_diff_policy_precision | `0.0` |
| max_abs_diff_policy_recall | `0.0` |
| max_abs_diff_policy_tp_pixels | `0.0` |
| max_abs_diff_policy_fp_pixels | `0.0` |
| max_abs_diff_policy_fn_pixels | `0.0` |
| max_abs_diff_accepted_union_area_fraction | `0.0` |
| accepted_proposal_ranks_equal | `True` |
| policy_prediction_empty_equal | `True` |
| policy_hd95_valid_equal | `True` |
| policy_hd95_invalid_reason_equal | `True` |
| component_detection_equal | `True` |
| max_abs_float_diff | `0.0` |

**C1 == C3 output: YES**

## Counters

| counter | value |
|---|---|
| regional_forwards | **1976** |
| regional_forwards_expected | **1976** |
| regional_forwards_per_model | **{'UNet': 494, 'Attention U-Net': 494, 'UNet++': 494, 'DeepLabV3+': 494}** |
| global_forwards | **0** |
| global_forwards_note | **verified Part-1D-B global cache reused; no new global model pass** |
| training | **0** |
| optimizer | **0** |
| localizer_forwards | **0** |
| proposal_generation | **0** |
| oracle_reruns | **0** |
| test_reads | **0** |
| external_test_reads | **0** |

## HD95 compute

| item | value |
|---|---|
| hd95 calls | 1184 |
| hd95 memo hits | 1700 |

memoised by binary-prediction hash; C1 and C3 share one computation

The memo key is the binary-prediction hash, so configurations that produce identical predictions
(including C1 and C3, and cases with zero accepted proposals) share a single HD95 computation.
