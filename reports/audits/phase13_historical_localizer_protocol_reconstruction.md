# Phase 13 Part 1A — Historical Localizer Protocol Reconstruction

- Status: **COMPLETE**
- Historical manifest: `phase4_v2` · taxonomy `kub_size_v1`

## Historical population (phase4_v2)

- TRAIN FULL_FIELD: 771 images / 1162 components
- VAL FULL_FIELD: 106 images / 156 components · strata {'TINY': 73, 'SMALL': 29, 'MEDIUM': 36, 'LARGE': 18}

## Authoritative stage (Stage-4D-R2)

- experiment: `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`
- best epoch 73 / 88 total
- checkpoint SHA `ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace`
- selected config {'threshold': 0.1, 'margin': 0.2, 'top_k': 5, 'nms_iou': 0.3}
- Tiny recall90 0.726027 · overall recall90 0.641026
- hard Tiny recovered90 7/16 · global-empty 3/7
- mean ROI area 0.005899 · proposals/image 4.660377

## Handoff claims — all VERIFIED

- Stage-4D best.pt SHA-256: `ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace` — **VERIFIED**
- Stage-4D best_epoch: `73` — **VERIFIED**
- Stage-4D total_epochs: `88` — **VERIFIED**
- selected threshold: `0.1` — **VERIFIED**
- selected margin: `0.2` — **VERIFIED**
- selected top_k: `5` — **VERIFIED**
- selected nms_iou: `0.3` — **VERIFIED**
- Tiny recall90 numerator/denominator: `53/73` — **VERIFIED**
- Overall recall90 numerator/denominator: `100/156` — **VERIFIED**

## Findings

### `HISTORICAL_TRAIN_INFERENCE_PROPOSAL_DISTRIBUTION_MISMATCH` — **VERIFIED**

The historical Phase-14 regional refiner was TRAINED on GT-derived base crops, GT-perturbed crops and random background negatives, but EVALUATED on Stage-4D predicted proposals. The training and inference proposal distributions therefore did not match.

**Consequence.** The Phase-14 Step-3 failure (D_p 0.383905 vs D_g 0.652776, driven by 5.43 FP components/image vs 0.37 baseline) is at least partly attributable to this distribution gap and is NOT a clean measurement of predicted-proposal regional refinement.

**Clean-v3 action.** Any clean-v3 regional integration must draw training crops from predicted proposals (with an explicit negative-sampling policy) or explicitly declare and measure the gap.

### `LATENT_INFERENCE_HEATMAP_RESOLUTION_OMISSION` — **VERIFIED_DEFECT**

The Stage-4D checkpoint was trained with a 128x128 output heatmap (AvgPool2d(4,4)). The inference helper would construct the 512-output variant. Because the logit downsample is parameter-free and the head is a 1x1 convolution, the state dict still loads, so the mismatch is silent and the helper would return a 512-space heatmap.

**Clean-v3 action.** Pass heatmap_resolution explicitly (or freeze an output-resolution contract) and add a regression test.

### `STAGE4D_DESIGN_AUDIT_LABEL_AMBIGUITY` — **AMBIGUOUS**

The label most plausibly refers to the clean-v3 ARCHITECTURE (KUBLocalizer), not the clean-v3 MANIFEST.

**Clean-v3 action.** Supervisor confirmation before any reuse of the Stage-4C numbers.

### `MISSING_VAL_SEARCH_EPOCH_079` — **VERIFIED**

Only the per-epoch proposal-grid dump for epoch 079 is missing; the epoch history itself is complete.

**Clean-v3 action.** None required for Phase 13; noted for provenance.

## Governance

- TEST reads **0** · training **0** · inference **0** · proposals **0**
- No checkpoint/history/config/manifest was modified
- Phase 14 not executed · Experiment A untouched

**Conclusion.** Historical Phase-13/13B localizer protocol reconstructed and frozen. The historical population is phase4_v2 (106/156). Four findings recorded, including a VERIFIED train/inference proposal-distribution mismatch in the historical Phase-14 refiner.
