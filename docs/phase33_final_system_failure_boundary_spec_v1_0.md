# Phase 33 — Final System Failure & Boundary Error Analysis
## Entry Gate + Evidence-Population Ownership + Failure Taxonomy + Boundary-Metric Provenance + Pre-Analysis Specification

**Revision:** `ra_medfilm_barr_phase33_failure_boundary_v1_0`
**Classification:** `PRE_ANALYSIS_FAILURE_AND_BOUNDARY_PROVENANCE_SPECIFICATION`
**Method:** RA-MedFiLM-BARR
**Status:** SPECIFICATION COMPLETE — **failure analysis NOT executed**
**Generated:** 2026-10-04T08:10:50+00:00

> **Phase30 qualifier (mandatory wherever Phase30 ROUTER_HOLDOUT evidence is used):**
> `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`
> Phase30 remains `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL`.

---

## 1. Purpose

**What failure modes are present in the frozen final RA-MedFiLM-BARR system, and which of those
failure modes can be established from already-frozen evidence without reopening protected
populations or manufacturing new post-outcome definitions?**

Phase33 is descriptive/diagnostic evidence — not model selection, policy selection, threshold
tuning, training, a new validation benchmark, a new significance-testing phase, or a Phase39 TEST
substitute.

## 2. Evidence classes distinguished

| class | status |
|---|---|
| FINAL-SYSTEM FAILURE EVIDENCE (Phase30 ROUTER_HOLDOUT frozen tables) | available, table-only |
| HISTORICAL PHASE11 FAILURE EVIDENCE (KUB VAL280, 4 architectures) | historical descriptive only |
| NEW DESCRIPTIVE DERIVATIONS (from frozen non-pixel fields) | eligible |
| BOUNDARY ANALYSIS | **INELIGIBLE** |
| QUALITATIVE CASE ANALYSIS | **INELIGIBLE** |
| PROTECTED RAW POPULATIONS (ROUTER_HOLDOUT images/GT, TEST) | forbidden |

## 3. Population ownership

`ROUTER_HOLDOUT` = frozen result tables only · `VAL808` = frozen result tables only ·
`ROUTER_DEVELOPMENT` = historical descriptive only · `TRAIN` = frozen tables + metadata join ·
historical KUB VAL280 = historical descriptive only · external cohorts = historical descriptive only ·
**`TEST` = FORBIDDEN (locked until Phase39)**.

Raw access is **not** assumed merely because a population was opened in an earlier phase.

## 4. Frozen-artifact schema

Present in the frozen final-system tables: per-sample `global_dice`, `a8_dice`, `delta_dice_a8`,
`a7_dice`, `delta_dice_a7`, `router_decision`, `state_machine`, `somega_accept`, `somega_score`,
`delta_hat`, `utility`, `tau_C8`, `roi_available`, `dataset`, `sample_id`, plus `group_key` via a
metadata-only join.

**Absent:** IoU, precision, recall, HD95, FP/FN counts, connected components, object counts,
per-sample boundary distances.

## 5. Phase11 taxonomy provenance

Phase11 froze a failure protocol for **KUB VAL280 across four segmentation architectures**
(UNet, Attention U-Net, UNet++, DeepLabV3+) — **not** the final RA-MedFiLM-BARR system.

* Reusable: bottom-decile quantile **method**; 8-connectivity; minimum-overlap ≥ 1 px.
* Historical KUB-specific only: cutoffs `0.5461`, `83.07`, `4`; regime stratification.
* Not applicable to the final system: `ALL_FOUR_LOW`, architecture disagreement.
* Post-hoc if introduced now: HD95 decile, FP-component decile.

Numeric thresholds and the KUB taxonomy were **not** auto-transferred.

## 6. Phase33 failure taxonomy

**Eligible (descriptive):** `LOW_OVERLAP`, `ROUTER_HARMFUL_ACTIVATION`, `ROUTER_MISSED_BENEFIT`,
`EXECUTE_THEN_REJECT`, `DOMAIN_SPECIFIC_FAILURE`, `GROUP_OR_PATIENT_CLUSTERED_FAILURE`,
`EMPTY_PREDICTION` (Dice-0 proxy only).

**Ineligible:** `FALSE_POSITIVE_BURDEN`, `FALSE_NEGATIVE_BURDEN`, `OBJECT_MISS`,
`MULTI_COMPONENT_PARTIAL_DETECTION`, `MULTI_COMPONENT_COMPLETE_MISS`, `BOUNDARY_ERROR`.

## 7. Threshold provenance

* Low-Dice stratum → `DESCRIPTIVE_QUANTILE_METHOD_PROSPECTIVELY_FROZEN` (method frozen now; realized
  numeric quantile computed deterministically at execution from frozen tables).
* Benefit categories → `EXACT_PREDECESSOR_THRESHOLD_TRANSFERABLE` (BENEFICIAL ≥ +0.02, HARMFUL
  ≤ −0.01, NEUTRAL otherwise; distinct from the S_omega training target `DeltaDice > 0`).
* HD95 / FP-component deciles → `FORBIDDEN`.

No outcome-optimized threshold was selected.

## 8. Boundary-metric provenance ruling

**`FINAL_SYSTEM_BOUNDARY_ERROR_NEW_COMPUTATION_ELIGIBLE = false`.** The frozen final-system evidence
contains no valid boundary metric, and computing one would require GT/prediction pixel rereads
(TIER_3). Phase11 boundary evidence is preserved as **historical KUB descriptive evidence only**.
ROUTER_HOLDOUT GT was **not** reopened merely because the phase title mentions boundary error.

## 9. Component / object analysis ruling

**`NEW_COMPONENT_ANALYSIS_ELIGIBLE = false`** — frozen final-system artifacts carry no
component-level information and deriving it requires protected rereads.

## 10. Hard-case selection

Procedure frozen **before** selecting any case (strata, ordering, tie-break, dedup, group cap,
underfill policy). **0 cases selected.** Label: `DESCRIPTIVE_FAILURE_CASE_SELECTION` — not unbiased
performance estimation; never selected for visual attractiveness.

## 11. Qualitative evidence

**`QUALITATIVE_GALLERY_ELIGIBLE = false`** — requires raw images and/or prediction pixels, neither
authorized. 0 panels generated. This is an acceptable outcome.

## 12. Quantitative analysis plan

Per-domain / per-state failure rates, selected-vs-skipped and accepted-vs-rejected distributions,
harmful-activation and missed-benefit characteristics, low-Dice prevalence, group-cluster
concentration, cross-category overlap, and severity summaries — all from frozen fields only. **No new
significance test**; Phase31 Wilcoxon/Holm/Cohen-d **not** imported.

## 13. Analysis tiers

`TIER_0` frozen-table read-only (**eligible**) · `TIER_1` derived from frozen non-pixel fields
(**eligible**) · `TIER_2` frozen prediction pixel (**not authorized**) · `TIER_3` raw image/GT reread
(**blocked**) · `TIER_4` model rerun (**forbidden**).

## 14. Execution eligibility

| capability | eligible |
|---|---|
| table-only | **true** |
| derived non-pixel | **true** |
| prediction-pixel | false |
| raw image | false |
| raw GT | false |
| qualitative gallery | false |
| boundary metric | false |
| component metric | false |
| model rerun | false |
