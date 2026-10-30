# Phase 30 — Final Development Validation Benchmark
## Pre-Execution Specification v1.3 (Primary Inferential Role)

**Specification revision:** `ra_medfilm_barr_phase30_final_dev_validation_v1_3`
**Classification:** `PRE_FIRST_OPEN_PRIMARY_INFERENTIAL_ROLE_RECONCILIATION`
**Method:** RA-MedFiLM-BARR
**Status:** PRE-EXECUTION SPECIFICATION FROZEN (v1.3) — one-shot execution NOT authorized
**Generated:** 2026-10-04T03:07:47+00:00

Supersedes v1.2 **by addition / primary-inferential-role clarification**. v1.2
(`docs/phase30_final_development_validation_spec_v1_2.md`, SHA `e988667d3bf0836c79f92fa6968a7901caa8c8ecc9a0b991f588c773164db94a`) is preserved
byte-for-byte. `science_changed = false`; `ROUTER_HOLDOUT_opened = false`.

---

## PRIMARY ADJUDICATION

> **PRIMARY ADJUDICATION = BOOTSTRAP NON-INFERIORITY CI**
> **criterion = lower macro 95% CI > −0.005 (strict)**
> **raw paired p = CASE P2 — `OPTIONAL_DESCRIPTIVE_NOT_COMPUTED_UNLESS_EXACT_PREDECESSOR_METHOD_RECOVERED`**
> **the raw paired p is NOT allowed to override or replace the CI gate.**

## A. Primary claim (frozen)

* **Primary estimand:** macro-domain equal-weight mean
  `DeltaDice_A8 = Dice(A8 final, GT) − Dice(global reference, GT)`.
* **Primary reference:** canonical GlobalMedFiLM (same frozen bundle).
* **Bootstrap method:** DOMAIN_STRATIFIED_GROUP_BOOTSTRAP (plan SHA `59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1`).
* **Non-inferiority margin:** 0.005.
* **Claim criterion:** lower 95% bootstrap CI of macro ΔDice_A8 **> −0.005** (strict).
* Per-domain reporting mandatory; macro may not hide domain harm.
* No seed ranking, no policy selection, no threshold change.

This criterion is the claim-bearing adjudication. **No p-value may override it.**

## B. Raw p-value provenance (CASE P2)

No exact paired p-value procedure was frozen for the A8-vs-global preservation comparison:

* Phase24 preservation contract defines the claim **only** via the lower confidence bound.
* Phase24 architecture statistics block declares only the generic item *"paired p-value where
  appropriate"* (`test_used = false`); no exact procedure.
* The Phase25E/25G raw paired two-sided p is scoped to the **C7-vs-comparator family
  (C1..C6, C10)** on ROUTER_DEVELOPMENT — **not** an A8-vs-global preservation procedure.
* Phase27 statistics contract defines point estimate + 95% CI only
  (`no_new_multiplicity_correction = true`).
* Phase27 decision rule contract: `p_value_role = "secondary / descriptive only for the primary
  preservation claim"`, `no_p_value_gating_for_primary = true`.

**Disposition:** the raw paired p **must not** be transferred from the C7 family merely because
both are labelled "primary". For canonical Phase30 execution the p-value is **not computed and not
adjudicated**; the claim-bearing inference reports **point estimate, 95% CI and the
non-inferiority criterion only**.

## C. Zero-difference vs non-inferiority (do not conflate)

Testing whether `DeltaDice = 0` (a two-sided p against zero) is **not** the Phase30
non-inferiority gate. The claim remains **lower 95% CI > −0.005**. No "statistically significant
improvement" claim is required for preservation.

## D. A7 / H3 (unchanged from v1.2)

* **A7** = `DESCRIPTIVE_COMPANION_ONLY`; inferential comparator = false; A8−A7 = descriptive point
  difference only; **no** A7 p-value may become a success criterion.
* **H3** = `DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD`; no numeric threshold, no hypothesis
  gate, no H3 p-value as a success criterion.

## E. Bootstrap plan (unchanged)

`data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz` SHA `59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1` — **not regenerated**. It remains the frozen
resampling plan for the A8-vs-global macro/per-domain CI and any already-authorized descriptive
uncertainty. No outcome access.

## F. Standing

ROUTER_HOLDOUT state `RESERVED_UNOPENED`; image reads 0; GT reads 0; outcome reads 0; model
forwards 0; TEST reads 0. **Phase30 one-shot execution has NOT started.**
