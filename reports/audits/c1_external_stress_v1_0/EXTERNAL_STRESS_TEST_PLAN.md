# External Stress-Test Evaluation Plan — RA-MedFiLM-BARR

**Study:** RA-MedFiLM-BARR external stress test
**Plan revision:** `c1_external_stress_plan_v1_0`
**Status:** `PRE_REGISTERED__FROZEN_BEFORE_ANY_EXTERNAL_INFERENCE`
**Written (UTC, host clock):** 2026-10-31T03:59:29Z

> **Clock caveat.** The host RTC is not synchronised (no NTP source, `Leap Indicator: 3`).
> This timestamp carries an unquantified offset. Only the *ordering* of events in this
> audit is trustworthy: this plan was committed to disk **before** any external
> probability array, binary mask or metric existed. That ordering is the binding claim,
> not the absolute time.

---

## 1. Classification of this study

This is a **`RETROSPECTIVE_EXTERNAL_STRESS_TEST`**.

It is **not**:

- a prospective validation study;
- a preregistered clinical trial;
- an independent confirmatory test of BARR superiority;
- a replacement for the locked internal TEST split.

Consequences that must appear wherever these results are reported:

1. The external cohorts were **not** held out from the model-development process in any
   auditable way. Some of these datasets were consulted during earlier exploratory work
   on this project (see §2.4).
2. No external cohort was used to select a checkpoint, tune a threshold, choose a
   preprocessing convention or pick a seed. The design decisions in §4–§6 were fixed
   by this document, before execution.
3. All external results are **descriptive**. No confirmatory p-value is computed (§9).
4. The internal locked TEST split remains unread. `ROUTER_HOLDOUT` remains unread.

---

## 2. Cohorts

### 2.1 Included cohorts

| # | Cohort | Manifest (frozen) | Evaluable N | `task_id` | Domain analogue |
|---|--------|-------------------|-------------|-----------|-----------------|
| 1 | CVC-ClinicDB | `reports/external_extension/manifests/ext02_cvc_clinicdb_manifest.csv` | 612 | 2 | KVASIR (colonoscopy) |
| 2 | BrEaST-Lesions-USG | `reports/external_extension/manifests/ext02_breast_us_manifest.csv` | 252 | 1 | BUSI (breast ultrasound) |
| 3 | Stones_where_are_you (test split) | `reports/external_extension/manifests/ext02_1_stones_manifest_reconciled.csv`, `original_split == "test"` | 20 | 3 | KUB (abdominal radiograph) |

**Total analysed images: 884.**

Manifest SHA-256 (recorded in `plan_manifest.json`):

- CVC — `b3a1ca429ba974766787709108d84344df2a963836fb00f3fe14aa47c02386c4`
- BrEaST — `24697ef0e4226a70025e33dba428f238515d5ad1aa323c3230db5947dec0001b`
- Stones — `31f08db493f83f1f5ea85a0dbd385e82330484b63698f5d7c978ee0c4adc8b8b`

### 2.2 Exclusion rule (applied mechanically, not case by case)

A row is included **iff** `evaluable == True` in its frozen manifest **and** both
`image_path` and the ground-truth reference resolve to an existing file **and** the
ground-truth mask is non-degenerate after rasterisation (see §4.4).

This rule yields: CVC 612/612, BrEaST 252/256 (4 rows carry `evaluable == False`),
Stones 20/20 within the test split (456/460 evaluable across all splits; only the
test split is analysed).

Rows excluded by the manifest itself, and the counts, are reported in
`cohort_construction.json`. No row is dropped post hoc.

### 2.3 BrEaST pairing

BrEaST ships 270 images and 252 tumour masks. The 18 images without a paired mask are
**excluded by construction**, not imputed. The frozen manifest already encodes the 252
paired cases; this plan adds no further pairing logic.

### 2.4 Stones cohort and the 6-positive subgroup

The Stones test split contains 20 images and 81 COCO annotations across 10 categories.
Only `category_id == 7` (`stone`) is foreground; every other category is background.

- 6 of 20 test images carry at least one `stone` annotation.
- 14 of 20 carry none.

Because a 6-image subgroup cannot support an inferential claim, Stones is reported in
**three** framings and no other:

- **all-20** — the primary Stones number;
- **6-positive** — foreground-detection behaviour where a stone exists;
- **14-absent** — false-positive behaviour where no stone exists.

The 14-absent subgroup is the only place in this study where a *true-negative* claim is
even arithmetically available, and it is reported as a count, not a rate with a CI.

### 2.5 Prior consultation disclosure

These external datasets were examined during earlier exploratory work on this project
(manifest construction, evidence classification, and a figure pilot). Specifically:

- CVC-ClinicDB, BrEaST-Lesions-USG and Stones were all previously used to build the
  `ext02` manifests and to classify evidence provenance.
- A small **figure pilot** previously ran the global model on 8 hand-picked single cases
  drawn from these cohorts, using a **different, non-canonical resize convention**
  (plain 512×512 stretch instead of the canonical aspect-preserving pad). Those pilot
  numbers are **not** reused here and **must not** be pooled with the results of this
  study. They are superseded.

This is disclosed because it bears on the independence of the stress test. The prior
exposure was to *dataset structure and a handful of individual images*, not to
aggregate external performance; no threshold, checkpoint or seed was chosen on the
basis of it. Nevertheless the study is labelled retrospective for exactly this reason.

### 2.6 HAM10000 — EXCLUDED

HAM10000 is **excluded from this study**.

Reason: the HAM10000 folder in this workspace is the **ISIC-2018 Task 3**
classification release, which ships **no segmentation masks**. The workspace nonetheless
contains 10,015 mask files with no recorded provenance. Without provenance the masks
cannot be attributed to an annotator, a release or a licence, so any Dice computed
against them is not a measurement of the model.

Status: `HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED`. No HAM10000 inference is run,
and no previously quoted HAM10000 figure (including the 79.15 % Dice that circulated in
an earlier report build) may be cited as an external result of this study.

---

## 3. Frozen model identities

All four components are hash-verified before inference. Any mismatch aborts the run;
there is no fallback.

| Component | Path | SHA-256 |
|-----------|------|---------|
| Global `G_theta` (GlobalMedFiLM) | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` |
| Regional refiner `R_psi` | `checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt` | `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109` |
| Benefit router `B_phi` | `checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt` | `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b` |
| Post-safety `S_omega` | `checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt` | `eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e` |

Global config: `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json`
SHA-256 `66ec701aeac503cbeceff75aa070e30b46146c9069e46594cbd484f6816260f5`
(`in_channels = 3`, `input_channel_policy = RGB_3CH`, `input_resolution = 512`,
`task_count = 4`, FiLM sites `bridge, decoder4, decoder3, decoder2, decoder1`).

Note the refiner path is the **`_roi030` variant**, not `phase25a_barr_regional_refiner_v1_1`.
That is the component the frozen Phase 29 canonical inference binds for seed 42; the
`v1_1` directory is a different artefact and is not used.

No component is retrained, fine-tuned, re-initialised or partially reloaded.
`strict=True` state-dict loading is required.

---

## 4. Preprocessing — frozen, single convention

### 4.1 Image

`src/data/transforms.py::SegmentationTransform(size=512, train=False, image_mode="RGB")`:

1. convert to RGB;
2. `scale = min(512/W, 512/H)`; resize to `(round(W*scale), round(H*scale))` with
   **bilinear**;
3. centre the result on a 512×512 canvas with **zero** padding;
4. divide by 255.0, layout `(3, 512, 512)`.

This is the canonical Phase 21 inference geometry. It is **aspect-preserving**; the
model was trained and validated on it.

> **Superseded convention.** The earlier figure pilot stretched each image directly to
> 512×512 with no padding. That changes the effective scale of every object and is
> **not** used here. Stress-test numbers and stress-test figures both use the
> aspect-preserving convention above.

### 4.2 Ground truth

The mask is passed through the **same** geometry (`SegmentationTransform.__call__`
returns both tensors): resize with **nearest**, same pad, then binarise as `> 0`.

For COCO cohorts (Stones), the mask is rasterised at **native** image resolution first
(polygon fill, `category_id == 7` only), then put through the same geometry. Rasterising
after resize is forbidden — it would change which pixels are foreground.

### 4.3 Probability and decision

- logits → `sigmoid` in float32;
- binary mask = `prob >= 0.5` (lower-inclusive, float32 comparison);
- **one** threshold for every cohort. No per-cohort, per-domain or per-image tuning.
- no test-time augmentation, no ensembling, no post-processing, no morphological
  clean-up, no connected-component filtering.

### 4.4 Degenerate cases

A case is **kept** if its ground-truth mask is empty or full; it is scored and counted.
Degenerate cases are not dropped, because dropping them would flatter the model.

An empty *prediction* against a non-empty GT is scored as `FN > 0`, `TP = 0`,
`Dice = 0`. Surface distances are undefined in that case and are recorded as `NaN`
with an explicit `surface_undefined_reason` field, never as 0 or as a large sentinel.

---

## 5. BARR executability — determination recorded before execution

### 5.1 Determination

**`BARR_EXECUTABLE_FROM_VERIFIED_ARTIFACTS`.**

Justification, established by static inspection before any inference:

- A frozen end-to-end composition exists at
  `scripts/analysis/phase29_phase_d_canonical_seed_inference.py`, which runs
  `G → 202-D router features → B_phi → ROI → R_psi → fuse → 16-D safety features → S_omega`
  using only frozen artefacts.
- The 202-D router feature vector is built by the frozen
  `src/features/barr_pre_refinement_features.py` (`build_feature_vector`), reading three
  Global MedFiLM feature taps (`bridge`, `decoder2`, `decoder1`) through **read-only
  forward hooks**. No model code is modified.
- The 16-D post-safety feature vector is built by the frozen
  `scripts/analysis/phase25f_post_safety_features.py::compute_numeric_features`.
- The class definitions used for `B_phi` and `S_omega` are extracted from
  `scripts/analysis/train_phase25d_router.py` and
  `scripts/analysis/phase25f_execution_common.py`, both of which still hash-match their
  Phase 29 bindings (`fc7c1bdf…`, `98cf958a…`).
- All four checkpoints hash-match (§3).

### 5.2 What must NOT be claimed

The composition is **not** a reimplementation and is **not** a new model, but the
external run does require a **new driver**: the Phase 29 script is hard-wired to the
VAL808 population and its precomputed cache. The external driver therefore reuses every
frozen *component and feature extractor* verbatim and supplies only the population and
the per-case bookkeeping. This distinction must be stated whenever BARR external results
are reported.

### 5.3 Frozen decision rule (seed 42)

- `tau_C7 = 24796109646558761 / 20000000000000000000`
- `lambda_C = (1/4) * (1051648 / 10270749)`
- `tau_C8 = tau_C7 - lambda_C`
- select iff `delta_hat >= tau_C7`, equivalently `delta_hat - lambda_C >= tau_C8`
  (the two forms are asserted equal on every case).

**Router input normalisation.** Only the 8 frozen scalar indices
`[192, 193, 194, 195, 196, 197, 200, 201]` are standardised, using the checkpoint's own
`normalizer_mu` / `normalizer_sigma` / `normalizer_constant_mask`. The 192 deep features
are passed **raw**. This reproduces the Phase 29 convention exactly and is not a choice
made here.

**S_omega input.** 16 numeric features standardised with the checkpoint's own statistics,
concatenated with a 4-D task one-hot. Accept iff `sigmoid(logit) >= 0.50`.

**ROI geometry.** `src/data/barr_roi.py::roi_geometry(p_global, threshold=0.30,
margin=0.25)` — GT-free, deterministic from the predicted probability map.

### 5.4 Per-case state vocabulary

Every case receives exactly one state, and the seven counts must sum to N:

| State | Meaning |
|-------|---------|
| `NOT_ATTEMPTED` | BARR was not run for this case. |
| `ROUTED` | Router evaluated and selected the case for refinement. |
| `EXECUTED` | The regional refiner actually ran on a real crop. |
| `ACCEPTED` | `S_omega` accepted; final mask is the refined candidate. |
| `REJECTED` | `S_omega` rejected; final mask is the global mask. |
| `FALLBACK_TO_GLOBAL` | Selected, but no ROI existed; refiner could not run; final is global. |
| `FAILED` | An exception occurred; the case is excluded from BARR metrics and reported. |

A case that is not selected is `NOT_ATTEMPTED` for refinement purposes and its final mask
equals the global mask. `ROUTED` and `EXECUTED` are staged states, not terminal ones; the
terminal state of a selected case is `ACCEPTED`, `REJECTED`, `FALLBACK_TO_GLOBAL` or
`FAILED`. The report must therefore give both the stage counts and the terminal counts,
and must not present `ROUTED` as if it were an outcome.

### 5.5 Abort condition

If at execution time any component hash mismatches, any state-dict fails `strict`
loading, or the router decision forms disagree on any case, the run aborts and BARR is
reported as `BARR_NOT_EXECUTABLE_FROM_VERIFIED_ARTIFACTS` with the global-only results
standing alone. The abort reason is recorded verbatim; it is never smoothed over.

---

## 6. Metrics — exact definitions

Computed on the 512×512 canvas, per case, from `pred_bin` and `gt_bin`:

| Metric | Definition |
|--------|------------|
| TP, FP, FN, TN | pixel counts against `gt_bin` |
| Dice | `2TP / (2TP + FP + FN)` |
| IoU | `TP / (TP + FP + FN)` |
| Precision | `TP / (TP + FP)` |
| Recall / Sensitivity | `TP / (TP + FN)` |
| Specificity | `TN / (TN + FP)` |
| Accuracy | `(TP + TN) / (TP + FP + FN + TN)` |
| HD95 | 95th percentile of the symmetric surface-distance set, **pixels** |
| ASSD | mean of the symmetric surface-distance set, **pixels** |
| NSD (τ = 2 px) | fraction of reference-surface points within 2 px of the prediction surface, symmetrised by averaging both directions |
| Region size error | `(|pred| - |gt|) / |gt|`, `NaN` when `|gt| = 0` |
| Empty-mask frequency | fraction of cases with `|pred| = 0` |
| FP-only case | `|gt| = 0` and `|pred| > 0` |
| FN-only case | `|gt| > 0` and `|pred| = 0` |
| Latency | wall-clock seconds per case, **single-threaded, batch size 1, warm-up excluded**, reported as median and IQR |

### 6.1 Surface-metric units and honesty constraint

**No external cohort ships physical pixel spacing.** CVC-ClinicDB, BrEaST and Stones all
provide pixel arrays with no DICOM header, no calibration phantom and no documented
mm-per-pixel. HD95, ASSD and NSD are therefore reported in **pixels**, and any
millimetre figure is forbidden in every downstream document.

This makes HD95/ASSD **not comparable** across cohorts with different field-of-view and
acquisition geometry. Cross-cohort surface-metric comparison is prohibited; only
within-cohort comparisons between Global and BARR are permitted, because those share the
same canvas.

### 6.2 Degenerate-GT handling

When `|gt| = 0` and `|pred| = 0`: Dice, IoU, precision, recall are `NaN` (undefined),
specificity is 1, accuracy is 1, surface metrics are `NaN`.
When `|gt| = 0` and `|pred| > 0`: Dice = 0, IoU = 0, precision = 0, recall = `NaN`,
specificity < 1, surface metrics are `NaN`.

`NaN` is never replaced by 0, and never silently dropped from a mean. Every aggregate
reports both `n_total` and `n_defined`.

---

## 7. Aggregation

Primary aggregate: **per-cohort macro mean over cases** of each metric (each case
weighted equally). Pooled pixel-level aggregation is also computed but is **secondary**,
because it lets large lesions dominate. Whenever a number is quoted, its aggregation
mode is stated.

Per-cohort reporting always includes: `n`, mean, SD, median, Q1, Q3, min, max.

**No cross-cohort pooled number is computed.** A single "external Dice" across CVC +
BrEaST + Stones is forbidden: the three cohorts measure different tasks with different
positive-class prevalence and different GT provenance.

---

## 8. Global vs BARR comparison

BARR is evaluated on the **same 884 cases** as the global model, using the same
preprocessing and the same 0.5 threshold, so pairs are exact and no case is lost.

The comparison is reported as a **per-case paired difference in Dice** (`BARR − Global`),
with:

- the count of improved, unchanged and worsened cases;
- median and IQR of the difference;
- the same statistic restricted to cases the router actually selected.

No significance test is applied (§9). The comparison is described as an *observed
difference on this cohort*, never as evidence that BARR is better or worse.

---

## 9. Statistics — deliberately limited

- **Zero confirmatory p-values.** `p_values_computed = 0`. This is a hard output field,
  not a description.
- Uncertainty is expressed as a **percentile bootstrap** 95 % CI, 2000 resamples,
  seed 42, resampling at the **cluster** level:
  - CVC-ClinicDB: cluster = `sequence_id` (29 clusters — frames from one video are not
    independent);
  - BrEaST: cluster = `case_id` (252 clusters, one image per case);
  - Stones: **no CI**. n = 20 with 6 positives; a bootstrap CI would be theatre.
    Point estimates and counts only.
- CIs are labelled *descriptive interval under a stated resampling scheme*, never
  "confidence interval" in a confirmatory sense.
- No multiplicity correction, because no family of hypotheses is tested.
- No subgroup inferential comparison. Subgroup differences are described as observed.

---

## 10. Figures — pre-registered column definitions

Five mandatory columns, one row per case:

1. **Input image** — the 512×512 canvas exactly as fed to the model.
2. **Ground truth** — binary reference mask.
3. **Global prediction** — binary mask at threshold 0.50.
4. **Global error map** — TP / FP / FN / TN, using the fixed palette below.
5. **Global probability map** — continuous, fixed 0–1 scale.

If BARR executes (§5), three further columns are added, for eight total:

6. **BARR final prediction** — binary mask after the state machine.
7. **BARR error map** — same palette, same scale.
8. **BARR decision trace** — the ROI window drawn on the image, with the terminal state,
   router score, threshold and `S_omega` acceptance probability printed as text.

**Fixed error palette** (identical to the already-published figures, so the two figure
sets remain visually comparable):

| Class | RGB |
|-------|-----|
| TP | `(0, 230, 0)` |
| FP | `(255, 32, 32)` |
| FN | `(32, 96, 255)` |
| TN | `(24, 24, 24)` |

Every panel is annotated with the case identifier, the cohort, and the per-case Dice.
A panel must never imply a clinical verdict. Text such as "rejected by safety filter"
may appear **only** where the recorded state is literally `REJECTED`, and must carry the
actual `S_omega` probability next to it.

Case selection for the figure is fixed by rule, not by eye: for each cohort, the case at
the **median** Dice, plus the **worst** and **best** case, plus — for Stones — the
**largest** and **smallest** ground-truth lesion. If a selected case is degenerate
(GT ≤ 20 px), the panel must say so on its face.

---

## 11. Prohibitions (binding on this run)

1. No training, fine-tuning, or parameter update of any component.
2. No threshold tuning, no per-cohort calibration, no operating-point selection.
3. No access to the locked internal TEST split; no access to `ROUTER_HOLDOUT`.
4. No HAM10000 inference.
5. No fabricated, interpolated or hand-edited predictions. Every saved probability array
   must be reproducible by re-running the frozen checkpoint.
6. No millimetre surface metrics (§6.1).
7. No pooled cross-cohort Dice (§7).
8. No confirmatory p-values (§9).
9. No change to any C1 trust boundary, approval state or `scientific_execution_enabled`
   flag. C1 remains `NO-GO`.
10. No modification of a frozen component source file. If a frozen source must change,
    the study stops and the change is reported instead.

---

## 12. Deliverables and their identity

| Artefact | Path |
|----------|------|
| This plan | `reports/audits/c1_external_stress_v1_0/EXTERNAL_STRESS_TEST_PLAN.md` |
| Machine-readable twin | `reports/audits/c1_external_stress_v1_0/external_stress_plan.json` |
| Plan identity manifest | `reports/audits/c1_external_stress_v1_0/plan_manifest.json` |
| Cohort construction audit | `reports/audits/c1_external_stress_v1_0/cohort_construction.json` |
| Global inference record | `reports/audits/c1_external_stress_v1_0/global_inference.json` |
| BARR execution record | `reports/audits/c1_external_stress_v1_0/barr_execution.json` |
| Probability arrays | `data_cache/c1_external_stress_v1_0/<cohort>/prob_global.npy` (+ BARR) |
| Binary masks | `data_cache/c1_external_stress_v1_0/<cohort>/pred_global.npy` (+ BARR) |
| Sample IDs | `data_cache/c1_external_stress_v1_0/<cohort>/sample_ids.json` |
| Per-case metrics | `reports/tables/c1_external_stress_per_case.csv` |
| Cohort summary | `reports/tables/c1_external_stress_summary.csv` |
| Figures | `reports/figures/fig6_external_global.png`, `fig7_external_barr.png` |

---

## 13. Terminal condition of this plan

This plan is **frozen on write**. It is hashed and the hash is recorded in
`plan_manifest.json`, which does not contain its own hash.

Any deviation discovered during execution is reported in
`deviations.json` with the reason, and the affected result is flagged in every document
that quotes it. A deviation is never silently absorbed.

If the plan itself must change, a **new revision** (`v1_1`) is written and the earlier
one is preserved — never overwritten.
