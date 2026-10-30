# Phase 14 Regional Refiner

This folder documents the completed Phase-14 Regional Refiner Diagnostic on the frozen
clean-v3 population. The notebook is a reproducibility and research-results record:
it loads authoritative reports, tables, checkpoints, history, and scripts without
retraining or rerunning model inference.

## Notebook contents

`phase_14_regional_refiner_pipeline.ipynb` includes:

- full 71-epoch training history;
- training/validation loss curves;
- validation Dice trajectory and best-so-far curve;
- recorded scheduler trajectory;
- early-stopping trajectory;
- best-checkpoint progression;
- trainer revision and resume provenance;
- bit-exact resume-equivalence evidence;
- epoch timing analysis with host-clock-skew caveat;
- complete diagnostic mode tables and comparison figures;
- contrast, special-set, and step-wise adjudication tables;
- dataset/population and configuration tables;
- saved qualitative evidence when available;
- expanded artifact provenance with SHA-256;
- current Phase-14 terminal assertions.

## Authoritative scripts and artifacts

- `scripts/training/train_phase14_refiner.py`
- `scripts/evaluation/evaluate_phase14_clean_v3_diagnostic.py`
- `scripts/audits/verify_phase13_part1b_canonical_selection_replay.py`
- `reports/audits/phase14_clean_v3_final_training_closure.json`
- `reports/audits/phase14_clean_v3_checkpoint_selection_replay.json`
- `reports/audits/phase14_resume_equivalence_verification.json`
- `reports/audits/phase14_clean_v3_global_reference_freeze.json`
- `reports/audits/phase14_clean_v3_diagnostic_evaluation.json`
- `reports/audits/phase14_clean_v3_formal_adjudication.json`
- `reports/audits/phase14_clean_v3_final_governance_reconciliation.json`
- `reports/audits/phase14_clean_v3_freeze_manifest.json`

Complete history:
`experiments/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/history.csv`

Checkpoints remain referenced in place:

- `checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/`
- `checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3/`
- `checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/`

## Terminal adjudication

Phase 14: `PHASE14_CLEAN_V3_COMPLETE__DIAGNOSTIC_PROPOSAL_BOTTLENECK`

Phase 15: `NOT_STARTED_AND_NOT_AUTHORIZED`

TEST and external TEST: `CLOSED`

## H3 relationship

H3 is post-Phase-14 causal/root-cause work and is intentionally kept separate at
`notebooks/phasewise/post_phase14_h3_proposal_supply/`. H3 results are not backfilled
into this frozen Phase-14 notebook.

## Notebook provenance

- Pre-upgrade notebook SHA-256: `F5A218FCD329F5FDC2D163D7CB59CD5252883C732D4BC904873ECD67C282D888`
- Executed upgraded notebook SHA-256: `FAC5246D0D445DDA9DD78E40EBB422F5D701CC4604E7AA0556CAF6CDF56593A5`
- Upgraded notebook execution status: `PHASE14_COMPLETE_RESEARCH_NOTEBOOK_EXECUTED__REPRODUCIBILITY_PASS`
- Training/inference during notebook reconstruction: none

The notebook was executed top to bottom with 19/19 code cells completing, zero
traceback cells, and stored table/figure outputs.
