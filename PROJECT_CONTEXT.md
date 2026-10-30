# PROJECT CONTEXT — AUTHORITATIVE HANDOFF

Project root: `D:\Softfors\jup`  
Python: `D:\Softfors\jup\.venv\Scripts\python.exe`  
Jupyter kernel: `jup-venv`  
GPU: NVIDIA GeForce RTX 3060 Ti  
PyTorch: 2.6.0+cu124  
CUDA: 12.4

## Phase control

Phases 0-15: historical execution complete under `phase4_v2` provenance.
**Phase 05: COMPLETE** (leakage audit + v3 promotion, Part 1E).
Current clean-refresh next phase: **Phase 06 — Descriptive Dataset Analysis (clean-v3 refresh)**.
Phase 06 is NOT authorized. No clean-rerun phase has been executed.

### Two-dimensional status model

| Phase | Historical scientific status (v2) | Clean-v3 revalidation status |
|---|---|---|
| 06 | COMPLETE | RERUN_REQUIRED |
| 07 | COMPLETE | RERUN_REQUIRED |
| 08 | COMPLETE | PARTIAL_RERUN_REQUIRED |
| 09 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |
| 10 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |
| 11 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |
| 12 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |
| 13 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |
| 14 | COMPLETE / FROZEN DIAGNOSTIC | REVALIDATION_REQUIRED |
| 15 | COMPLETE / v2 CONTAMINATED | REVALIDATION_REQUIRED |

Historical Phases 06-15 results are `MANIFEST_VERSION = phase4_v2` with
`LEAKAGE STATUS = KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY`.
No historical result may be silently presented as a clean-v3 result.

## Authoritative manifest

**Active development version:** `phase4_v3` (`manifests/phase4_v3/`) — CANONICAL_ACTIVE_DEVELOPMENT
**Historical version:** `phase4_v2` (root `manifests/*.csv`) — HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT

### phase4_v3 (active — use for all future development)

- TRAIN: 5,832
- VAL: 808
- TEST: 1,683 LOCKED (byte-identical to v2)
- QUARANTINED: 118
- TOTAL: 8,441

SHA-256:

- `manifests/phase4_v3/all_paired.csv`: `eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded`
- `manifests/phase4_v3/train.csv`: `28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6`
- `manifests/phase4_v3/val.csv`: `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315`
- `manifests/phase4_v3/test.csv`: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`
- `manifests/phase4_v3/quarantined.csv`: `a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c`
- `manifests/phase4_v3/duplicate_groups.csv`: `830d3c0ce08f735081e5a44fe3a740031da1c70cfc19ebcb4ef89c31acd704fb`
- `manifests/phase4_v3/grouping_provenance.csv`: `3eff84851d33e1c8b5894ce05049433287067a5e6088a90f5c67394230317f66`

### phase4_v2 (historical — reproduce Phases 06-15 only; DO NOT modify/delete)

- KUB TRAIN: 1,979 | VAL: 283 | TEST: 558 LOCKED
- Global TEST: 1,683 LOCKED

SHA-256:

- `all_paired.csv`: `66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc`
- `train.csv`: `d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3`
- `val.csv`: `46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4`
- `test.csv`: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`

### Version-aware loading (mandatory)

All future code MUST load manifests explicitly by version:

```python
import pandas as pd
from src.utils.manifest_guard import validate_manifest_version_strict
validate_manifest_version_strict('phase4_v3')
train = pd.read_csv(r'D:\Softfors\jup\manifests\phase4_v3\train.csv')
val   = pd.read_csv(r'D:\Softfors\jup\manifests\phase4_v3\val.csv')
test  = pd.read_csv(r'D:\Softfors\jup\manifests\phase4_v3\test.csv')
```

Do NOT rely on the ambiguous root `manifests/train.csv` for new experiments — those are
historical v2 evidence. See `manifests/manifest_registry.json` and
`reports/audits/phase05_v3_promotion_audit.md`.

### BUSI provenance

- BUSI patient-group mapping: `reports/tables/phase05_busi_patient_group_mapping.csv`
- Mapping SHA: `df4b01487ea6e1cb5c004e11535e4c3252c19dc3b84cbb21816c737dbaf2753b`
- Source metadata SHA: `14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44`

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

<!-- PHASE26_CANONICAL_INTEGRATION_COMPLETE -->

## Phase26 canonical integration - COMPLETE_CANONICAL (2026-10-02)

**Phase26 = COMPLETE_CANONICAL** (assembly only; legacy title 'Full Four-Domain
RA-MedFiLM-BARR Training' redefined to 'Full Four-Domain RA-MedFiLM-BARR Integration &
Canonical Bundle Freeze'). Phase27 = ELIGIBLE_NOT_STARTED; Phase28/29/30 = NOT_STARTED.

- Bundle: `artifacts/phase26_ra_medfilm_barr_bundle_v1_0` (manifest SHA `f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9`)
- Wrapper: `src/models/barr/ra_medfilm_barr.py` (SHA `342f2163690c2fa8d5a601ab1d18178b982d701b916935c33e0793b0801c3724`, 0 trainable parameters)
- Notebook: `notebooks/phasewise/phase_26_full_system_integration/phase26_canonical_integration_and_bundle_freeze.ipynb` (SHA `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0`, 3x byte-identical)
- Runtime policy: `A8_C9`, nominal budget 0.25, score `delta_hat_final - 0.25*C`,
  threshold `-5003565381643716252018011/205414980000000000000000000` (EXECUTE iff `>=`).
- Final-router DEV calibration selected count = 1239.
- ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; VAL808 = UNOPENED; TEST = LOCKED_UNTIL_PHASE39.
- 0 model training / 0 backward / 0 optimizer / 0 scientific-data forwards.

<!-- PHASE27_PRESERVATION_SPEC_COMPLETE -->

## Phase27 multi-domain performance preservation audit - SPEC_COMPLETE_FROZEN (2026-10-02)

**Phase27 specification = COMPLETE_FROZEN**; Phase27 = **EXECUTION_ELIGIBLE_NOT_STARTED**.
Governance / specification only - no VAL808 inference, no model construction, no training.

**SUPERVISOR RULING**: Phase27 owns VAL808 as the `SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK`;
Phase30 retains exclusive `ROUTER_HOLDOUT` ownership. VAL808 is not an untouched routing holdout.

- Specification: `docs/phase27_preservation_spec.md` (revision `ra_medfilm_barr_preservation_v1_0`).
- VAL808 = 808 rows (ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84); total groups = 639 under the
  metadata-only composite patient/singleton rule (proven equivalent to the canonical Phase24
  `group_key` partition on all 5832 TRAIN rows).
- Estimand: macro-domain equal-weight mean Dice delta; margin 0.005; claim iff lower 95% CI > -0.005.
- Bootstrap: domain-stratified group bootstrap, B = 2000, seed 42, PCG64, percentile CI 2.5/97.5;
  draw plan frozen **before** inference (`data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_plan_v1_0.npz`).
- ROUTER_HOLDOUT = RESERVED_UNOPENED_FOR_PHASE30; TEST = LOCKED_UNTIL_PHASE39; Phase28/30 = NOT_STARTED.
- 0 model forwards / 0 training / 0 VAL808 image or mask reads / 0 holdout reads / 0 test reads.

Terminal: `PHASE27_PRESERVATION_SPEC_COMPLETE__VAL808_CONTINUITY_BENCHMARK_AND_NONINFERIORITY_PROTOCOL_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED`

Terminal: `PHASE26_CANONICAL_INTEGRATION_COMPLETE__A8_C9_25PCT_FINAL_ROUTER_RUNTIME_POLICY_AND_BUNDLE_FROZEN__PHASE27_ELIGIBLE_NOT_STARTED`


<!-- PHASE27_PRESERVATION_SPEC_V1_1_EXECUTION_SEMANTICS_REPAIR -->

## Phase27 spec v1.1 - execution-semantics repair (2026-10-02)

`GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY`. Phase27 spec = **V1_1_COMPLETE_FROZEN**;
Phase27 = **EXECUTION_ELIGIBLE_NOT_STARTED**; Phase26 remains **COMPLETE_CANONICAL**.

- Phase26 notebook closure reconciled: canonical Phase26 notebook SHA now `5d063ecb57a7e213c2260a11e1daa66bb58bc2f6b5b4029cfc1ae0e3e91aa8c8`
  (old `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0` = PRE_POSTCLOSURE_NOTEBOOK_REPAIR_PROVENANCE).
- Numerical inference mode resolved from authoritative predecessor evidence (CASE A):
  **CUDA + autocast(float16) + no_grad, eval mode**; batch 8, contiguous chunks per domain,
  order `(dataset, sample_id)`; probability computed float32, stored float16.
- Evidence class = `CONTINUITY_DEVELOPMENT_EVIDENCE`.
- Frozen VAL808 statistics unchanged: n 808, ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84,
  639 groups, bootstrap B 2000 seed 42 PCG64, plan SHA `8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93`.
- Completeness table v1.1: `reports/tables/phase27_specification_completeness_v1_1.csv`
  (34 rows, exact schema, `blocking_fields = []`).
- 0 VAL808 image/mask reads; 0 scientific forwards; 0 training; ROUTER_HOLDOUT + TEST unopened.

Terminal: `PHASE27_SPEC_V1_1_COMPLETE__PHASE26_NOTEBOOK_CLOSURE_RECONCILED__NUMERICAL_INFERENCE_AND_EVIDENCE_PROVENANCE_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED`
