# POST-PHASE13 H2C-B2 — Execution Audit

- **Status: PASS**
- run id: `post_phase13_h2c_downstream_best_native_policy`

## Authorization

- source: `USER_SUPERVISOR_MESSAGE_POST_H2C_B1`
- H2C-B2: **GRANTED**

## Bindings

| role | SHA-256 |
|---|---|
| h2c_protocol_sha | `91166259c10a84e9526eda43e83b227cc760a37b8834a4d4a65fe3e5a90ba4b6` |
| h2c_b1_training_evaluation_sha | `ae20f39de080d60f59fbfef93ff42bc0fdebf9f4410149440b06873f1c6f975b` |
| h2c_b2_freeze_manifest_sha | `3efb739df79f67a5782c7655ecd0fbf474ce8a772343310727a3d2ae5335d92d` |
| h2c_best_pt_sha | `021ab63f2cbc064b5c4de90c5f181ebee75f8d10e7dead2eb53f4f9578060f98` |
| evaluation_script_sha | `928fc170300497220cf498e75a9206b95de9b0d08adf2625af3bfdd2839805d6` |
| b2_integrity_sha | `8aad74d04ba0373dc60a7433ae953c7ceab04cd93f332b5c55886413221e15ec` |
| adjudication_sha | `b1d19ba8032520d98f3f2b25132795142c9bb4f98e565d9431b1795c23fe48fe` |
| model_summary_sha | `bdc0962bd5aa4a1e92775f2123bf0d3be83aae15a29a64f6eaa264f56c9e273c` |
| case_model_sha | `b95041f4cd259acbeb77dd731d93ed930d284e34208adf2f6845f60b0ac304d3` |
| component_model_sha | `35b2b718325e442ea6f12fdff00e1645236e70200e713f812a9f29035b511c0b` |
| cross_architecture_sha | `89b4e548eda50b0dca0555fe75cbc90ce8f4cf3815f8f4ff9ffc5417f9ea0184` |
| localizer_to_downstream_sha | `5fa7c01a5e35f4353cb1f73ecb13d7e85f465a4733f09abf397d40ea6d8d945d` |
| comparison_sha | `fbd110a49347aa72b8510b42806e9635859981edcb10fc7fbce00807a92a1876` |
| reviewer_notebook_sha | `7eb813a66b28c83ff6710be57db2ed03ffd6cf3decaeeee46fc3ceab07b6aabd` |

## Downstream configuration

- architectures: unet, attention_unet, unetpp, deeplabv3plus
- proposal policy: threshold 0.10 / margin 0.20 / top_k 5 / NMS 0.30
- fusion: `PREDICTED_REGION_FLOAT_GLOBAL_RETAINED`
- configurations: **1**

## Results per model

| model | H2C | GLOBAL | Phase13 | H2A | Oracle | H2C−GLOBAL | H2C−P13 | H2C−H2A | retention |
|---|---|---|---|---|---|---|---|---|---|
| unet | 0.300230 | 0.594180 | 0.302314 | 0.313779 | 0.724722 | -0.293950 | -0.002084 | -0.013550 | -2.251764 |
| attention_unet | 0.301089 | 0.629805 | 0.308619 | 0.320173 | 0.699595 | -0.328716 | -0.007530 | -0.019084 | -4.710103 |
| unetpp | 0.304042 | 0.640516 | 0.311355 | 0.323046 | 0.726679 | -0.336474 | -0.007313 | -0.019004 | -3.905048 |
| deeplabv3plus | 0.282357 | 0.560251 | 0.277292 | 0.288917 | 0.750372 | -0.277894 | +0.005065 | -0.006560 | -1.461668 |

## Counters

| counter | value |
|---|---|
| logical_training_experiments | 1 |
| h2c_training_experiments | 1 |
| proposal_configurations | 1 |
| proposal_grid | 0 |
| threshold_searches | 0 |
| oracle_reruns | 0 |
| downstream_segmentation_model_constructions | 4 |
| downstream_segmentation_forwards | 1848 |
| checkpoint_candidates_evaluated_downstream | 1 |
| validation_reads | 103 VAL cases |
| test_reads | 0 |
| external_test_reads | 0 |

## Counter explanations

- **downstream_segmentation_model_constructions**: 4 frozen architectures loaded (0 trained)
- **downstream_segmentation_forwards**: 462 proposals x 4 architectures = 1848 regional crops
- **checkpoint_candidates_evaluated_downstream**: exactly 1 (H2C epoch 57 best.pt)

**H2C outcome: `H2C_HEAD_REDESIGN_INSUFFICIENT`**

**Reporting defect scientific impact: NONE**

**Phase 14: ELIGIBLE_NOT_STARTED**

next_action: `WAIT_FOR_SUPERVISOR_PHASE14_AUTHORIZATION`
