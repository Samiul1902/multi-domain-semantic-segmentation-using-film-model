# Phase 10 Attention U-Net CLEAN-v3 Reviewer Audit (Part 1A-R1)

- **Experiment**: `phase10_kub_attention_unet_seed42_512_clean_v3`
- **Architecture**: attention_unet
- **Manifest**: `phase4_v3`
- **Taxonomy**: `kub_size_clean_v3_v1`

## Artifact SHAs
- Config: `70e08ad5b89461db0bb9cbb8e75da8bbc9ef357af36e5d70a3c4653818260c02`
- Training runner: `1e215dbf70faf7efc62c725fb8a9c5988362e2e5f4f143022e97545347f1dbfc`
- History: `ee5073f0bea745280ae7d9a8f651cc4cae72a18d408750623d838f7cd8d24e58`
- Best checkpoint: `a49b19d66e43b57ed082ea6efc0ac10bccf444277abd3540dc68612bf30b88b3`
- Latest checkpoint: `74a7e612ac9d6a2fcc05c2b25d007f156959d69b3507f198562c07ff4926cd20`
- Review notebook: `71ae94180551c96f768ffbe1f9b999bc14408b59bd1d4f36269e52a48cde9d9a`
- Review support code: `bc0e96283087443f954ed84d8bc8e555c9a36b51ac273cd28f1bb8ca8c219db3`
- Gallery selection: `10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db`
- Gallery metrics: `d85184cfc2b91233a5fb164fe55b2d4938b74b0c88b9b627a1b16b76d3c76a51`

## Run Summary
- Best epoch: 54 | Final epoch: 69
- Stop: EARLY_STOP (bad_epochs=15)

## Authoritative VAL Metrics (280 KUB cases)
- Dice: 0.7525129853960107
- IoU: 0.6349387691368995
- Precision: 0.7729140812402236
- Recall: 0.7922248481868364
- Provenance: HISTORY_NATIVE

### Precision / Recall resolution
val_precision and val_recall are written natively per-epoch into history.csv by the training loop. Values at epoch 54 exactly match the completion audit. The earlier execution-note N/A was a reporting error, not missing data.

## VAL Scope
- Review VAL rows: 280 (KUB)
- Categories: {'Bladder_Stone': 144, 'Kidney_Stone': 112, 'Ureteric_Stone': 24}
- Acquisition: {'ROI': 177, 'FULL_FIELD': 103}

## Gallery
- Cases: 16 (KUB 16, non-KUB 0)
- Metrics status: DETERMINISTIC_GALLERY_SUBSET_ONLY

## Governance
- TEST reads: 0 | metrics: 0 | visualizations: 0
- Training performed by notebook: False
- Optimizer steps: 0 | Training epochs: 0
- UNet++ started: False | DeepLabV3+ started: False
- Final comparison started: False
- Winner declared: False
- Training artifacts modified: False

## Status: PASS