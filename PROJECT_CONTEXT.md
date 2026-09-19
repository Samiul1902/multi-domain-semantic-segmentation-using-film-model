# PROJECT CONTEXT — AUTHORITATIVE HANDOFF

Project root: `D:\Softfors\jup`  
Python: `D:\Softfors\jup\.venv\Scripts\python.exe`  
Jupyter kernel: `jup-venv`  
GPU: NVIDIA GeForce RTX 3060 Ti  
PyTorch: 2.6.0+cu124  
CUDA: 12.4

## Phase control

Phases 0-8: PASS. Current phase: Phase 9 — KUB U-Net Baseline Training. Phase 10 is not authorized.

## Authoritative manifest

Version: `phase4_v2`

- KUB TRAIN: 1,979
- KUB VAL: 283
- KUB TEST: 558 LOCKED
- Global TEST: 1,683 LOCKED

SHA-256:

- `all_paired.csv`: `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc`
- `train.csv`: `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3`
- `val.csv`: `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4`
- `test.csv`: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`

## Governance

TEST must not be used for training, validation, checkpoint selection, threshold tuning, architecture selection, loss selection, preprocessing selection, or hyperparameter tuning. External data is locked. Experiment A must not be modified. Metrics, figures, tables, and statistics must not be fabricated.

## KUB semantics and subgroups

Foreground is `mask > 0`; model targets are binary float32 `{0,1}`. FULL_FIELD and ROI_CROP are reported separately. TRAIN contains 771 FULL_FIELD and 1,208 ROI_CROP samples.

### Frozen object-size taxonomy `kub_size_v1`

Defined from TRAIN FULL_FIELD components only:

- Q25 = 0.0001499766777599
- Q50 = 0.00033976472454305
- Q75 = 0.0008266496069636999
- TINY: ratio <= Q25
- SMALL: Q25 < ratio <= Q50
- MEDIUM: Q50 < ratio <= Q75
- LARGE: ratio > Q75

These are dataset-relative, not clinical millimeter categories.

## Frozen Phase-9 baseline

Standard U-Net; 1 input channel; 1 output channel; base channels 32; 7,762,465 parameters. Resolution 512; batch/effective batch 4; seed 42. AdamW, learning rate 1e-4, weight decay 1e-4; CosineAnnealingLR. Loss is 0.5 BCEWithLogitsLoss + 0.5 DiceLoss. AMP enabled. Maximum 100 epochs; early-stopping patience 15; VAL macro Dice for early stopping and checkpoint selection; fixed threshold 0.5. No threshold, architecture, loss, or preprocessing tuning.

## Current Phase-9 run

Experiment ID: `phase9_kub_unet_baseline_seed42_512`. Training reached epoch 62. Best epoch 47. Reported checkpoint-selection VAL macro Dice 0.7455300688743591. Training stopped after 15 consecutive epochs without improvement.

Existing assets:

- `checkpoints/phase9_kub_unet_baseline_seed42_512/best.pt`
- `checkpoints/phase9_kub_unet_baseline_seed42_512/latest.pt`
- `experiments/phase9_kub_unet_baseline_seed42_512/history.csv`
- `experiments/phase9_kub_unet_baseline_seed42_512/summary.json`
- `experiments/phase9_kub_unet_baseline_seed42_512/training.log`

Do not retrain unless these artifacts are proven invalid. Evaluate `best.pt` on VAL only at threshold 0.5 and finalize Phase-9 per-image/component results, overall/FOV/category/size metrics, HD95, object metrics, figures, deterministic qualitative/failure panels, notebook 07, and provenance/hashes. Notebook 07 must not auto-retrain on Run All. Stop after Phase 9; Phase 10 requires explicit authorization.

## Frozen Phase-10 conclusion

Phase 10 — KUB Fair Baseline Model Comparison: **PASS**. The strongest global KUB baseline is **UNet++** (`phase10_kub_unetpp_seed42_512`) because it achieved the highest finalized overall VAL macro Dice, FULL_FIELD Dice, frozen TINY-object recall, and evaluation-space object recall. DeepLabV3+ had the lowest false-positive component burden, but lower FULL_FIELD Dice and TINY-object recall. These are single-seed descriptive VAL findings; TEST remains locked.

Permanent component-space convention: original-space connected components define identity, `kub_size_v1`, and single/multi-component grouping. Model object recall, prediction components, and false-positive components are measured in transformed 512×512 evaluation space. Resize/padding can merge original components (known provenance example: `32c06da36a7221dc5369e3ee4723c10c`); these spaces must never be silently mixed.


## Final unified inference goal & Auto-domain routing design

Future unified inference target:
Unknown medical image → automatic 4-domain router → task ID → task-conditioned RA-MedFiLM-Seg++ → domain-appropriate segmentation.

4 Domains:
- Task 0: ISIC (dermatology / skin lesion)
- Task 1: BUSI (breast ultrasound / breast lesion)
- Task 2: Kvasir-SEG (gastrointestinal endoscopy / polyp)
- Task 3: KUB-StoneX (urinary radiography / stone)

Current Phase 11-R1 state: manual prediction utility is KUB-only (`predict_kub`). Generic `predict(..., task='auto')` raises `NotImplementedError` until trained/validated in the future multi-domain phase. Automatic domain routing is NOT operational in Phase 11.

## Frozen Phase-12 conclusion

Phase 12 — KUB Oracle ROI / Zoom Upper-Bound Study: **PASS**. Primary Oracle margin: 25% (predeclared). On 106 FULL_FIELD VAL images, frozen UNet++ macro Dice increased from `0.652776413200` globally to `0.775736153740` with component-wise GT-localized zoom. Original-space TINY recall increased from `0.780821917808` to `0.986301369863`; 15 of 16 globally missed TINY components were recovered. Interpretation: strong Oracle upper-bound evidence of localization/effective-resolution headroom, motivating—but not proving—the value of a future predicted ROI localizer. Oracle is non-deployable; TEST remains locked.


## Frozen Phase-13 conclusion

Phase 12 is frozen PASS: FULL_FIELD global Dice `0.652776`, Oracle25 Dice `0.775736`, and original-space TINY recall `0.780822 → 0.986301`, recovering 15/16 global TINY misses; Oracle Phase-13 gate was YES. Phase 13 predicted-ROI proposal development selected the GT-free configuration `proposal threshold=0.50, margin=0.15, Top-K=3, NMS IoU=0.30` by the predeclared VAL-only lexicographic rule. Selected overall component recall90 was `0.743590` and TINY recall90 `0.684932`, but 0/16 globally missed TINY components and 0/7 global-empty cases were usefully localized. Phase-14 gate: **WEAK**; consider a separately authorized stronger learned localizer before refiner training. TEST remains locked.



## Frozen Phase-13B conclusion

- **Stage-3**: FAIL / CHECK_REQUIRED
  - Provisional run invalid. Deterministic evaluation requires strict tie-breaking without scaling penalties. Loss function unweighted focal reduction corrected.
- **Stage-4A**: CHECK_REQUIRED
  - root cause = protocol design issue
  - unconstrained recall selected full-image ROIs
- **Stage-4B**: Feasibility-constrained selection v1
  - constraints: mean ROI area <=0.10, mean proposals <=5
  - pilot: r512_s3_seed42_v3
  - result: FAIL / CHECK_REQUIRED. With full-image ROIs rejected, compact proposals yielded near-zero recall (Tiny recall90 1.3%, overall 3.8%). Current loss fails to teach localization.
- **Stage-4C**: CenterNet focal pilot
  - result: CHECK_REQUIRED
  - Target Validation failed. Gaussian heatmap peaks do not reach exactly 1.0 due to sub-pixel centers, breaking the positive-center selection in the loss function. Training aborted.
- **Stage-4C-R4**: Clean CenterNet V3 pilot (`phase13b_kub_localizer_r512_s3_centernetfocal_seed42_v3`)
  - Phase13B notebook created: `notebooks/11b_kub_learned_localizer.ipynb`
  - Run-All validated: YES
  - Stage4C clean V3 result: NOT_PROMISING (Tiny recall90=0.4658, overall recall90=0.2821, hard Tiny=1/16, mean ROI area=0.000863)

- **Stage-4D-R2**: Final Bounded Localizer (`phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`)
  - Power cut resume validated. Best Epoch 73.
  - Phase 13 Final Notebook created: `notebooks/11c_kub_final_localizer_redesign.ipynb` (Run-All: YES).
  - Stage-4D result: **PROMISING_VALIDATED_ON_VAL**. All gates passed.
  - Tiny recall90 = 0.7260, overall recall90 = 0.6410, hard Tiny = 7/16 recovered, mean ROI area = 0.0059, proposals/image = 4.66.

## Final Phase-13 Decision
Phase 13: executed and complete
Phase 14: closed without execution after frozen entry gate not passed
Phase 15: closed without execution because Phase 14 did not execute
Phase 16: next eligible phase
