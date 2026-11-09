# Phase 10 DeepLabV3+ CLEAN-v3 Reviewer Audit (Part 1C)

- Experiment: `phase10_kub_deeplabv3plus_seed42_512_clean_v3`
- Architecture: deeplabv3plus_resnet50_os16 (ResNet-50, **no pretrained**, os16)
- Params: 40,340,769 | ASPP [6, 12, 18] | aux head: False
- Manifest/Taxonomy: `phase4_v3` / `kub_size_clean_v3_v1`

## Provenance SHAs
- Training runner: `d1c5174c3bc6db09f03756ee93f2cf1d122f7a52731d88577da5f8c6a5ef3f33`
- Config: `a5220e3135618513a71e0094197b2cffe0aef9334f7d53e39642c7a00ddd5b57`
- History: `9c3a4611f0f38b474aa18537b0509bf9a4cb539baf077e6ba12c7880a73cd01f`
- Best ckpt: `f519027ba1a3a4d6212d83fecd4379f61f71bc05b0751924b9660da08d597dad`
- Latest ckpt: `69267fd0cd2104cb474665bda68f3f9a1b4c2c4dc9e074b603fea921434022ed`
- Review notebook: `17942c35387a59353ce176cfc9e335d157cdb726130c95b6d531f2467ecc15ee`
- Review code: `624b9182a76641475dbffa98b3f1b04f40ebfdadfcd0ba893713ccc68f75112e`

## Run
- Best epoch 52 / final 67 · EARLY_STOP (bad 15) · resume 0

## Authoritative VAL (280 KUB cases)
- Dice 0.7509140344161673
- IoU 0.6460492792430865
- Precision 0.7943328495850855
- Recall 0.7822983241135557

## Complete Epoch Table
- `phase10_deeplabv3plus_clean_v3_epoch_results.csv` SHA `8320b24653129f2bbde10cd7084bb6ef7741fb7756cdc22c7a3c3873684252fe`
- Rows 67 == history rows 67: **True**
- Missing [] · Duplicates [] · fully displayed in notebook: **True**

## Governance
- TEST reads/metrics/visualizations: 0 · training by notebook: False (0 steps, 0 epochs)
- Final comparison started: False
- **Winner declared: False** · Phase 11 started: False
- Prior baselines unchanged: UNet True, AttnUNet True, UNet++ True

## Status: PASS