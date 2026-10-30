# Post-Phase14 / H3 Proposal-Supply Notebook Set

This folder is the stepwise research record for the post-Phase14 proposal-supply branch.
It is separate from the Phase-14 Regional Refiner notebook because it documents causal
decomposition, axis prioritization, H3 design, pre-execution corrections, calibration,
H3 training boundaries, and the frozen H3 downstream evaluation after Phase-14 closure.

It is not Phase 15. Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`. TEST and external
TEST remain `CLOSED`.

## Notebook index

| Step | Notebook | Purpose | Status | Executed | Terminal state |
|---|---|---|---|---|---|
| 01 | `01_proposal_root_cause_diagnostic.ipynb` | Proposal/localizer root-cause decomposition | Complete | Yes | `F_MIXED_BOTTLENECK` |
| 02 | `02_h3_axis_priority_diagnostic.ipynb` | A-only vs C-only causal priority | Complete | Yes | `H3_DESIGN_ELIGIBLE__AXIS_PROPOSAL_SUPPLY_RECALL` |
| 03 | `03_h3_design_and_pretraining_binding.ipynb` | H3 design, correction, calibration, binding | Complete | Yes | `H3_FINAL_PRETRAINING_BINDING_COMPLETE__AWAITING_TRAINING_AUTHORIZATION` |
| 04 | `04_h3_training.ipynb` | H3 training record | Complete | Yes | `H3_TRAINING_COMPLETE__CHECKPOINT_SELECTION_REPLAY_PASS__SUPPLY_EVALUATION_PENDING` |
| 05 | `05_h3_supply_axis_evaluation.ipynb` | H3 supply-axis evaluation (**metric-domain RECONCILED**) | Complete / Reconciled | Yes | `H3_SUPPLY_METRIC_DOMAIN_RECONCILED__DOWNSTREAM_R_H3_PENDING` |
| 06 | `06_h3_downstream_evaluation.ipynb` | H3 **frozen downstream evaluation** | Complete | Yes | `H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING` |
| 07 | `07_h3_adjudication.ipynb` | Formal H3 adjudication | Complete / Formally adjudicated | Yes | `H3_SUPPLY_REDESIGN_INSUFFICIENT` |

Notebook SHA-256 values are recorded in the executed master index.

> **Renumbering note (additive).** The former step-06 slot ("Formal H3 adjudication") is now
> step 07. The new step 06 is the frozen downstream evaluation, which must precede adjudication.

## Executed notebook provenance

| Notebook | SHA-256 | Execution |
|---|---|---|
| `01_proposal_root_cause_diagnostic.ipynb` | `a9fd0dd734f9311655677eadc3e8d1710d9725c01681c36973ab4852d8583232` | 16 cells, 9/9 code cells, 0 errors |
| `02_h3_axis_priority_diagnostic.ipynb` | `ee8787c6d76acd6fe0208a694104d8d4b9b65e6fc3ea905ece4b541c340c83eb` | 13 cells, 7/7 code cells, 0 errors |
| `03_h3_design_and_pretraining_binding.ipynb` | `b98538a9d83e8da3dc696364f1cdb0a10bc07eb13b8c339179cee1666d6c6da7` | 16 cells, 9/9 code cells, 0 errors |
| `04_h3_training.ipynb` (scaffold, historical) | `f587807e2e2ffde8ba873f82d16dd0d67c0afac661cf0efe05e277d50104af3e` | 2/2 scaffold cells, 0 errors |
| `04_h3_training.ipynb` (executed, final) | `83aabc82f682d6c5685812f815077bf83b068e84ce7311c51366d67883ed350d` | 53 cells, 25/25 code cells, 0 errors |
| `05_h3_supply_axis_evaluation.ipynb` (pre-reconciliation, historical) | `fe69339ceddca6cd7d4a949f81d59154ccd19057b4d9bd24158d8ff825e9b1b0` | 65 cells |
| `05_h3_supply_axis_evaluation.ipynb` (reconciled, current) | `e3771f0a33cf8e69b0fe734001494d2974d1d896e540ced958b730bca39a3198` | 69 cells, 31/31 code cells, 0 errors |
| `06_h3_downstream_evaluation.ipynb` (current) | `557b8185edf2ab12e1332afdc3d346d8a4678346f3a9a16c501754ce839fa3ab` | 81 cells, 40/40 code cells, 0 errors |
| `post_phase14_h3_proposal_supply_pipeline.ipynb` (pre-closure, historical) | `cbf8dc30db8468049b069883f7716580b1699a148d0071e5c8ccb2283eb8e0d6` | 2/2 code cells, 0 errors |
| `post_phase14_h3_proposal_supply_pipeline.ipynb` (pre-step06, historical) | `881127ec760a6048fa2a2eee546a9271751c93c4a2bbf1353e5d52d5a9bd78dd` | 2/2 code cells, 0 errors |
| `07_h3_adjudication.ipynb` (formal adjudication) | `08c3ec4216bfc14f5aa4eb2dc2f12b00caaf53203f78056ffd1b57d7d7bcc66b` | 73 cells, 36/36 code cells, 0 errors |
| `post_phase14_h3_proposal_supply_pipeline.ipynb` (current) | `bb019f51deed0ebba0c04647f4ddf0da43943036246a752d1335b173e4d0ab91` | 4 cells, 2/2 code cells, 0 errors |

## H3 downstream evaluation (step 06)

The single frozen H3 downstream evaluation binds the selected H3 localizer (epoch 54,
heatmap resolution 128) to the frozen Stage-4D proposal policy
(threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30), the frozen Phase-14 regional refiner
(epoch 56), MAX-probability fusion (threshold 0.50), and per-component segmentation metrics.

- **Formal metric domain:** detection (`component overlap >= 1 px`), identical to the frozen
  GLOBAL/PREDICTED/ORACLE reference (`phase14_clean_v3_global_reference_freeze.json`).
- **TinyRecall_H3:** `59/72 = 0.8194444444444444`.
- **Formal R_H3** = `(TinyRecall_H3 - Tg) / G` = `2/15 = 0.13333333333333333` → band `insufficient`.
- **Strict cov90 sensitivity** (descriptive only): TINY `36/72 = 0.5`, R_H3 = `-1.4`.
- **Formal adjudication:** performed in step 07 (see *Formal H3 adjudication* below).

## Formal H3 adjudication (step 07)

The formal H3 adjudication applied the prospectively frozen criteria to the authoritative
observed values. It is a **disk-only** adjudication (no training, no inference, no TEST access).

| Clause | Frozen rule | Observed | Result |
|---|---|---|---|
| Supply Criterion A | zero-proposal TINY <= 20/72 | **22/72** | **FAIL** |
| Supply Criterion B | zero-proposal GT <= 35/152 | **27/152** | **PASS** |
| Combined primary supply | A AND B | — | **FAIL** |
| Downstream gate | R_H3 >= 0.30 | **2/15 = 0.1333** | **FAIL** |
| Failure clause 1 | zero-proposal TINY >= 45/72 | 22/72 | not fired |
| Failure clause 2 | R_H3 < 0.15 | 0.1333 | **FIRED** |

- **Formal metric domain:** detection (`component overlap >= 1 px`), matching the frozen Tg/G.
- **Formal TinyRecall_H3:** `59/72 = 0.8194444444444444`; **Tg** `57/72`; **G** `15/72`.
- **Formal R_H3:** `2/15 = 0.13333333333333333` → band `insufficient`.
- **Frozen scientific label:** **`H3_SUPPLY_REDESIGN_INSUFFICIENT`**.
- **Interpretation:** the size-adaptive target-support intervention materially improved proposal
  supply (zero-proposal GT 79→27, TINY 57→22) but the recovered supply did not translate into
  sufficient downstream Tiny-recall gain under the frozen Stage-4D pipeline.
- **Adjudication artifact:** `reports/audits/h3_formal_adjudication.json`.

**H3 did NOT succeed.** The failure boundary fired. The regional hypothesis is NOT erased:
ORACLE_REGIONAL remains a valid diagnostic upper bound; the predicted-localization path still
fails to retain enough practical regional benefit, so the `REVISE_LOCALIZER` problem remains
unresolved. Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`; TEST and external TEST remain CLOSED.

## Authoritative artifacts

- `reports/audits/phase14_diag_root_cause.json`
- `reports/audits/post_phase14_h3_axis_priority_results.json`
- `reports/audits/h3_proposal_supply_design_protocol.json`
- `reports/audits/h3_proposal_supply_design_correction.json`
- `reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json`
- `reports/audits/h3_proposal_supply_pre_execution_checklist.json`
- `reports/audits/h3_training_launch_binding.json`
- `reports/audits/h3_proposal_supply_training_closure.json`
- `reports/audits/h3_checkpoint_selection_replay.json`
- `reports/audits/h3_supply_axis_evaluation.json` (SHA `00e6f41351d725817810eba13b738b2631c5b0cc023af192b1479af7321b9687`)
- `reports/audits/h3_supply_axis_metric_domain_reconciliation.json` (SHA `457e87a7b51b378d3364d62884ab2fea98859684397762140abc66b63ea9d802`)
- `reports/audits/h3_downstream_evaluator_binding.json` (SHA `0fc5db464241b4e8e644cc7d3e60c81ba736187c735a94841c265a2b37e843ef`)
- `reports/audits/h3_downstream_evaluation.json` (authoritative; SHA `9bfbf32f4ddaee7b3c34fadad22a6c09b1ce299349d5deaec74a75f0590cccb7`)
- `reports/audits/h3_downstream_evaluation_v1_asrun.json` (as-run cov90, preserved; SHA `6acf4880c6b3aa180108083c1fd1efbecf7b414e1fe0105277970c50747a284d`)
- `reports/audits/h3_downstream_metric_domain_correction.json` (SHA `ba85a57861263a6c771e9f6eceb027769aaff81e330bf99a7b18d82efac949d0`)
- `reports/audits/h3_downstream_resolution_diagnostic.json` (pipeline-fidelity diagnostic; SHA `1c028da2933fb4780ceea07e37013b4f2b2436725081360d08e1501b53763be0`)
- `reports/tables/h3_downstream_per_component.csv` (SHA `84db1d11dd7374c90d960a610e990d1140dedf5c9acddd86aeccec75966712af`)
- `reports/tables/h3_downstream_per_image.csv` (SHA `cb120f3e13503d700706360265b9784c90558a2a45bf8f6ab80199b6f58b4a23`)
- `reports/tables/phase15_h3_axis_priority_component_level.csv`
- `reports/tables/phase15_h3_axis_priority_image_summary.csv`
- `reports/tables/phase15_h3_axis_priority_aonly_injected.csv`
- `reports/tables/phase15_h3_axis_priority_ac_component_level.csv`
- `reports/tables/h3_v2_area_distribution.json`
- `reports/tables/h3_v2_component_area_audit.csv`

## Evaluators

- `scripts/evaluation/h3_downstream_evaluator.py` (SHA `5afb3d9419ebebd2096ed29c52fe744af6197e5260ed1f8d91f9e7de61688a1d`) —
  the single frozen downstream evaluation (bound prospectively before results).
- `scripts/evaluation/h3_downstream_metric_domain_correction.py` (SHA `326b90212e60fb6b49a75092a487078a3868561d5bcb7261964f254038f72cda`) —
  additive metric-layer correction to the frozen detection domain (no new inference).
- `scripts/evaluation/h3_downstream_resolution_diagnostic.py` (SHA `0576002d70964d8851ff9b6295429a9ede7aa181f180e061b5a07d0183b9e309`) —
  pipeline-fidelity diagnostic confirming the evaluator reproduces the frozen PREDICTED arm.

## Training boundary

H3 training is COMPLETE (69 epochs, early stopping patience 15, best epoch 54 by the frozen
`(val_localization_recall, -val_loss)` tuple, replay verdict `H3_CHECKPOINT_SELECTION_REPLAY_PASS`).
The authoritative training closure (`reports/audits/h3_proposal_supply_training_closure.json`)
and disk-only checkpoint-selection replay (`reports/audits/h3_checkpoint_selection_replay.json`)
exist and are synchronized into notebook 04 and the master index above. Supply-axis evaluation
(notebook 05) is COMPLETE and RECONCILED; the frozen downstream evaluation (notebook 06) is
COMPLETE; formal adjudication (notebook 07) is COMPLETE (frozen label `H3_SUPPLY_REDESIGN_INSUFFICIENT`);
Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`; TEST and external TEST remain `CLOSED`.

No notebook in this synchronization started training, ran inference, accessed TEST, or started
Phase 15.
