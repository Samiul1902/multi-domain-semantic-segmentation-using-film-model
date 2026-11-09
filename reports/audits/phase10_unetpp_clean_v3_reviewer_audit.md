# Phase 10 UNet++ CLEAN-v3 Reviewer Audit (Part 1B)

- **Experiment**: `phase10_kub_unetpp_seed42_512_clean_v3`
- **Architecture**: unetpp_nested_4_level_no_deep_supervision (deep supervision OFF)
- **Manifest / Taxonomy**: `phase4_v3` / `kub_size_clean_v3_v1`

## Provenance SHAs
- Training runner: `096a084dcc66cc4da5db53418f69f094217009406494951629816f3ca4d82b58`
- Config: `e2788e504b09cd8544e45fb7aef4001b8363452963d7d793f693647b4df24f53`
- History: `a733d8366278d2ddb1a44db0d94ff7525fb9b10afefba787abfd036c1fb1de5a`
- Best checkpoint: `ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269`
- Latest checkpoint: `77a39b4f510f69956233af898f7f62d4ae755fac57375bab70f95102b142c8ef`
- Review notebook: `0fd9176fb82340b7762c130ab3b51ae4fc425da434b5553b3f55859061bb18e5`
- Review support code: `f4d7c90c6a4eb3807852550a7133726c0079bd15159b841054e470c5691901af`

## Run Summary
- Best epoch 70 / final epoch 85
- Stop: EARLY_STOP (bad_epochs=15), resume_count=0

## Authoritative VAL Metrics (280 KUB cases)
- Dice: 0.7641595156062713
- IoU: 0.6525442690586191
- Precision: 0.7996825971468945
- Recall: 0.791238416956199

## Gallery (paired with UNet / Attention U-Net)
- Cases: 16 (KUB 16, non-KUB 0)
- Selection SHA: `10ad09cbcaabb56bc6bc6aefe016c83b2173933bf6d1f16e4baaf3f0845613db` (identical to prior models: YES)
- Metrics status: DETERMINISTIC_GALLERY_SUBSET_ONLY

## Governance
- TEST reads/metrics/visualizations: 0
- Training by notebook: False (optimizer steps 0, epochs 0)
- DeepLabV3+ started: False
- Final comparison started: False
- **Winner declared: False**
- Training artifacts modified: False

## Status: PASS