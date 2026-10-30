# Phase 30 — Final Development Validation Benchmark
## Pre-Execution Specification v1.2 (Comparator / Statistical-Scope Clarification)

**Specification revision:** `ra_medfilm_barr_phase30_final_dev_validation_v1_2`
**Classification:** `PRE_FIRST_OPEN_COMPARATOR_STATISTICAL_SCOPE_RECONCILIATION`
**Method:** RA-MedFiLM-BARR
**Status:** PRE-EXECUTION SPECIFICATION FROZEN (v1.2) — one-shot execution NOT authorized
**Generated:** 2026-10-04T03:00:40+00:00

Supersedes v1.1 **by addition / comparator-scope clarification**. v1.1
(`docs/phase30_final_development_validation_spec_v1_1.md`, SHA `ae79ce30b776ad481ad7029f5341e6c1ff8215c7bdb851bb3b337fe816871aa0`) is preserved
byte-for-byte. `science_changed = false`; `ROUTER_HOLDOUT_opened = false`.

---

## A. Carried-forward v1.1 numerical-order semantics (unchanged)

G batch membership scientifically material; ROUTER_HOLDOUT sample order (dataset asc, sample_id
asc); 875 samples; **111** G batch forwards (BUSI 12 / ISIC 48 / KUB 38 / KVASIR 13); 1 logical G
extraction pass; G batch manifest frozen; bootstrap plan frozen before first image access.

## B. Claim hierarchy (frozen)

| Tier | System | Status |
|---|---|---|
| **Primary claim-bearing** | **A8/C9 fixed canonical Phase26 bundle** | inferential |
| **Primary reference** | **canonical GlobalMedFiLM** | comparator |
| Companion | A7/C8 | **descriptive only** |
| — | Phase25G | owner of formal A7-vs-A8 controlled DEV comparison |
| — | H3 | descriptive only, no numeric success threshold |

**Primary claim:** A8/C9 final system versus the frozen global reference.
**Primary estimand:** macro-domain equal-weight mean
`DeltaDice_A8 = Dice(A8 final, GT) - Dice(global, GT)`.
**Primary preservation criterion:** lower 95% CI > −0.005. Per-domain reporting mandatory.
No seed ranking, no policy selection, no threshold change.

**A7** = `DESCRIPTIVE_COMPANION_ONLY`. No separate Phase30 superiority/non-inferiority claim; no
"A8 beats A7" adjudication.

**H3** = `DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD`. No new H3 threshold or hypothesis gate.

## C. Comparator ownership (authoritative)

The formal A7/C8-vs-A8/C9 controlled comparison is **owned and COMPLETE by Phase25G** on
ROUTER_DEVELOPMENT (n=4957): `phase25g_a7_a8_controlled_comparison_contract.json`,
`phase25g_final_freeze.json`, `phase25f_a7_a8_ownership_ruling_v1_0.json` (ruling F1),
`phase28_a7_a8_status_determination.json` (`A7_A8=SATISFIED_BY_PHASE25G_CANONICAL_EVIDENCE`).
Phase30 does **not** re-execute it. The v1.0 phrase *"Secondary: A8−A7"* is dispositioned
**`DEPRECATED_AMBIGUOUS_COMPARATOR_SCOPE`**.

## D. Raw paired p-value scope (frozen)

`raw_paired_two_sided_p_scope = A8_FINAL_VS_GLOBAL_REFERENCE_PRIMARY_COMPARISON_ONLY`.
It does **not** apply to A8−A7 and creates **no** new inferential comparator for A7.
Authority: `phase25e_evaluation_statistics_contract_v1_0.json` (raw paired p = primary comparison
statistic).

## E. A7 descriptive companion construction

A7 uses the **same** G output, B_phi score, router threshold, EXECUTE membership, ROI and R_psi
candidate as A8.

* EXECUTE: A7 final = refined candidate regardless of S_omega; A8 final = candidate if ACCEPT else global.
* SKIP: A7 final = global; A8 final = global.

A7 requires **0** additional G / B_phi / R_psi / S_omega forwards — a deterministic byproduct only.

## F. Bootstrap plan (unchanged)

`data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz` SHA `59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1` — **not regenerated**. The paired resampling index
structure is reusable; only the allowed estimand consumption is clarified (A8-vs-global
claim-bearing; A7 / A8−A7 descriptive-uncertainty only). No outcome read is authorized.

## G. Standing

ROUTER_HOLDOUT state `RESERVED_UNOPENED`; image reads 0; GT reads 0; outcome reads 0; model
forwards 0; TEST reads 0. **Phase30 one-shot execution has NOT started.**
