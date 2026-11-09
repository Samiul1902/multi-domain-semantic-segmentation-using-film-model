# Phase 30 — Final Development Validation Benchmark
## Pre-Execution One-Shot ROUTER_HOLDOUT Specification + First-Open Freeze

**Specification revision:** `ra_medfilm_barr_phase30_final_dev_validation_v1_0`
**Method:** RA-MedFiLM-BARR
**Status:** PRE-EXECUTION SPECIFICATION FROZEN — one-shot execution NOT authorized
**Generated:** 2026-10-04T02:46:58+00:00

---

## 0. Standing

This document is the **complete prospective Phase30 specification**. It is **pre-execution**:

* **ROUTER_HOLDOUT remains UNOPENED** (state `RESERVED_UNOPENED`).
* **One-shot execution is NOT yet authorized.**
* **TEST remains LOCKED (owner Phase39).**
* All scientific decisions below are **prospectively frozen before the first opening**.

It supersedes (does not overwrite) the Phase25G deferred stub
`phase30_router_holdout_deferred_contract_stub.json`, which explicitly declares
`is_phase30_specification = false`.

Predecessor: `PHASE29_PHASE_D_POSTCLOSURE_RECONCILED__SEED42_REUSE_COUNTS_AND_NOTEBOOK_FINAL_CHECK_PROVENANCE_FROZEN__PHASE29_COMPLETE__PHASE30_ELIGIBLE_NOT_STARTED`
(`phase29_phase_d_postclosure_terminal.json`,
SHA `e92c4e6eed1eef6e813d83fd785d8334be241cc7bef427f7b1bdf7f911aa6eb1`).

---

## 1. Ownership and role

| Field | Value |
|---|---|
| Owner | Phase30 |
| Population | ROUTER_HOLDOUT |
| n | 875 (exact, from `reports/audits/phase24_router_split_manifest.csv`) |
| Role | FINAL DEVELOPMENT VALIDATION BENCHMARK |
| Nature | ONE-SHOT CLEAN OUT-OF-SAMPLE DEVELOPMENT VALIDATION |
| State before execution | RESERVED_UNOPENED |
| TEST | LOCKED_UNTIL_PHASE39 |

Authority: `phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json` (ruling G1).

## 2. Population binding (metadata only)

* Split manifest: `reports/audits/phase24_router_split_manifest.csv`
  SHA-256 `b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555`
* Split seed: **42**; algorithm: per-domain group-greedy at ~15% holdout.
* Holdout n = **875**, groups = **628**.
* Domain composition: BUSI 90, ISIC 383,
  KUB 298, KVASIR 104.
* Task IDs: ISIC 0, BUSI 1, KVASIR 2, KUB 3.
* Overlap: DEV **0**, VAL808 **0**, TEST **0**; holdout ⊂ source TRAIN (5832).
* No image, mask or performance information was derived.

## 3. System under test (frozen before first open)

Canonical variant **A8/C9** — the fixed Phase26 canonical bundle
(`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json`, SHA `f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9`).

| Component | Class | Checkpoint | SHA-256 |
|---|---|---|---|
| G | GlobalMedFiLM | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` |
| R_psi | BARRRegionalRefinerV1 | `checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt` | `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109` |
| B_phi | BARRBenefitRouterV1 | `checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt` | `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b` |
| S_omega | BARRPostSafetyV1 | `checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt` | `eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e` |

Normalizations: router `ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb`,
post-safety `e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b`.

**Comparator scope resolution.** Phase30 evaluates the **A8/C9 fixed bundle** as its
claim-bearing target (authority: `phase26_evidence_class_contract_v1_0.json` —
"first clean one-shot evaluation of the fixed Phase26 bundle"; variant A8_C9). The
A7/C8-vs-A8/C9 controlled comparison is owned by **Phase25G on ROUTER_DEVELOPMENT**
(4957) and is already `COMPLETE_CANONICAL`; it is **not** re-executed as a Phase30
comparator. Because A7 shares identical routing membership and candidate output with A8
and differs only by the S_omega gate, the A7 companion state is a deterministic
byproduct requiring no additional inference and MAY be reported descriptively. **No new
comparator, threshold or policy is introduced.**

## 4. Canonical seed / bundle identity

`best_seed_selected = false`. seed123 and seed3407 are **not promoted**. No weight
averaging, no ensembling, no seed re-selection. The canonical seed42 bundle remains the
scientific reference bundle.

## 5. Frozen runtime thresholds (DEV-calibrated)

| Threshold | Value |
|---|---|
| ROI proposal | 0.30 |
| Segmentation output | 0.50 |
| S_omega ACCEPT | 0.50 |
| Runtime score | `delta_hat_final - 0.25*C` |
| Runtime utility threshold (exact) | `-5003565381643716252018011/205414980000000000000000000` |
| Final router raw threshold (exact) | `24796109646558761/20000000000000000000` |
| Normalized action cost (exact) | `1051648/10270749` |
| lambda | 1/4 |
| lambda*C (exact) | `262912/10270749` |
| Policy ID | C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY |

Decision form: `EXECUTE iff (delta_hat_final - 0.25*C) >= tau_C8`.

## 6. Lambda / budget policy treatment

The holdout receives the **already-frozen runtime rule**. No top-K forcing, no 25%
forcing, no threshold refitting, no lambda reselection, no post-hoc budget adjustment.
The nominal DEV calibration budget is **0.25**; the **realized holdout
activation fraction is an OUTCOME reported after execution** and may differ.

## 7. End-to-end causal inference order

```
G (once)
  -> pre-refinement B_phi 202-D inputs
  -> B_phi raw logit delta_hat
  -> frozen decision threshold
     SKIP    : final = global;  R_psi_exec = 0; S_omega_exec = 0
     EXECUTE : ROI -> R_psi -> regional fused candidate
               -> 20-D S_omega input -> S_omega
                  ACCEPT : final = refined candidate
                  REJECT : final = global
  -> threshold final probability at 0.50
```

`R_psi_exec = router_execute`; `S_omega_exec = R_psi_exec`. EXECUTE_THEN_REJECT incurs
refiner compute. S_omega does not save R_psi compute; the compute-saving decision is the
B_phi/C8 pre-execution router pre-gate.

## 8. Component numerical semantics

| Component | device | autocast | grad context | batch |
|---|---|---|---|---|
| G | cuda | fp16 ENABLED | `torch.no_grad()` | 8 |
| R_psi | cuda | disabled | `torch.inference_mode()` | 8 |
| B_phi | cuda | disabled | `torch.inference_mode()` | full matrix |
| S_omega | cuda | disabled | `torch.inference_mode()` | 128 |

G is the only component under autocast(fp16). Eval-mode batch size is not numerically
load-bearing for these frozen eval-mode models.

## 9. Image / GT two-stage protocol

* **Stage A (image-only):** read holdout images, never GT; persist all predictions,
  decision table and exact sample order; hash ALL outputs; write the prediction hash barrier.
* **Stage B (GT scoring):** open GT only after the barrier is durably frozen.
* GT must never affect G, features, router score/threshold/decision, ROI, R_psi,
  S_omega features/decision, fusion, policy or thresholds.

## 10. First-open audit

Before image access, a first-open marker must record timestamp, population/manifest/
system/threshold/policy/numeric-semantics contract SHAs, pre-open holdout counters, the
TEST counter, execution environment, git/source state and checkpoint hashes. Distinct
counters `ROUTER_HOLDOUT_image_reads` and `ROUTER_HOLDOUT_GT_reads` are mandatory; no
generic ambiguous counter may be used.

## 11. Statistical analysis plan

* Primary estimand: **macro-domain equal-weight mean ΔDice** (A8 final vs global reference).
* Secondary: A8−A7 (S_omega marginal effect); H3 harmful-replacement reduction.
* Bootstrap: DOMAIN_STRATIFIED_GROUP_BOOTSTRAP, unit = group_key, strata = 4 domains,
  B = 2000, seed 42, `PCG64(42)`, percentile 2.5/97.5, paired draws for A8/A7/A8−A7.
* Non-inferiority margin **0.005**; claim iff lower 95% CI > −0.005.
* Per-domain reporting mandatory. Primary = raw paired two-sided p; no new multiplicity
  correction.
* The holdout bootstrap plan is generated **at execution, pre-outcome, from metadata only**
  (the DEV plan does not cover the holdout). The Phase27/VAL808 bootstrap is **not** copied.

## 12. Metric definitions

* BENEFICIAL `DeltaDice >= +0.02`; HARMFUL `DeltaDice <= -0.01`; NEUTRAL otherwise.
* S_omega training target `DeltaDice > 0` — **distinct** from the benefit labels.
* Permitted metric families: segmentation, router, safety, state-machine (A/B/C/D), compute.

## 13. Compute semantics

Historical resource cost is an **ANALYTICAL MAC LOWER BOUND**
(G 31551740928, router 36160, refiner 3230662656,
S_omega 1168). The words *latency*, *runtime*, *energy*, *memory* and *mobile
performance* must never be used for these figures.

## 14. Post-open immutability

After the first open there may be **no** threshold/checkpoint/normalization/feature/lambda/
budget/policy/seed/calibration/training/metric/bootstrap/claim-criterion change. Any defect
found after opening is preserved and classified; policy must not be repaired using holdout
outcomes and rerun as if clean.

## 15. TEST lock

TEST owner = Phase39; TEST reads = 0; state `LOCKED_UNTIL_PHASE39`.

## 16. No-execution statement

This specification performs **zero** training, **zero** model forwards, **zero** holdout
image reads, **zero** holdout GT reads, **zero** outcome reads and **zero** TEST reads.
**Phase30 one-shot execution has NOT started.**
