# Phase 09 CLEAN-v3 — Training Completion Audit

**Status:** `PASS`  
**Experiment ID:** `phase9_kub_unet_baseline_seed42_512_clean_v3`

## Run summary

| Field | Value |
|---|---|
| Config SHA | `8a45458c7c5e34062214a741550a84ff9ab56e4ad9ceef81cbcf263052b5172a` |
| Manifest version | `phase4_v3` |
| Taxonomy ID | `kub_size_clean_v3_v1` |
| Start (UTC) | 2026-09-20T06:53:00.854097+00:00 |
| End (UTC) | 2026-09-20T07:56:57.745831+00:00 |
| Wall seconds | 3837.3 |
| Resume count | 0 |
| Epochs completed | 59 |
| Best epoch | 44 |
| Best VAL macro Dice | 0.7406133413314819 |
| VAL macro IoU @ best | 0.6253822445869446 |
| VAL macro Precision @ best | 0.7707186937332153 |
| VAL macro Recall @ best | 0.7839437127113342 |
| Final/latest epoch | 59 |
| Stop reason | **EARLY_STOP** |
| Early-stop bad_epochs | 15 |

## Checkpoints

| Field | Value |
|---|---|
| best.pt | `checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt` |
| best.pt SHA | `7b955ba86464a2fec2d569ecb6124de1fa9a4e66d0b5d58b267be9a280b4c2c0` |
| best.pt epoch | 44 |
| latest.pt | `checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/latest.pt` |
| latest.pt SHA | `6de118bf21cacd560769bfc5781d2928e0ef0c96e41035c34d6bb17f375e4509` |
| latest.pt epoch | 59 |
| best taxonomy_id | `kub_size_clean_v3_v1` |
| latest taxonomy_id | `kub_size_clean_v3_v1` |
| best manifest_version | `phase4_v3` |
| latest manifest_version | `phase4_v3` |

## History

- Path: `experiments/phase9_kub_unet_baseline_seed42_512_clean_v3/history.csv`
- SHA: `7678a5822542cd356f85e9c153da460a87e58d85e7cd1221d8fb66e323f60217`

## Governance

- Finite losses: True
- NaN/Inf events: 0
- Scientific parameter changes: 0
- TEST content reads: 0
- TEST metrics: 0
- TEST visualizations: 0
- TEST checkpoint selection: False
