# Phase 30 — Final Development Validation Benchmark
## Pre-Execution Specification v1.1 (Numerical-Order Repair)

**Specification revision:** `ra_medfilm_barr_phase30_final_dev_validation_v1_1`
**Classification:** `PRE_FIRST_OPEN_NUMERICAL_ORDER_SPECIFICATION_REPAIR`
**Method:** RA-MedFiLM-BARR
**Status:** PRE-EXECUTION SPECIFICATION FROZEN (v1.1) — one-shot execution NOT authorized
**Generated:** 2026-10-04T02:53:21+00:00

This document **supersedes v1.0 BY ADDITION / NUMERICAL-ORDER CLARIFICATION**. v1.0
(`docs/phase30_final_development_validation_spec.md`, SHA `ea7085b824c271157e37bdd1392c97ab9be6d6e050cae1482ecbec1318616ee8`) is preserved
byte-for-byte. `science_changed = false`; `ROUTER_HOLDOUT_opened = false`.

---

## A. Repair scope

v1.0 stated for GlobalMedFiLM G: *"Eval-mode batch size is not numerically load-bearing for
these frozen eval-mode models."* That statement is **not acceptable for G**. Frozen
predecessor evidence (`run_phase25b_determinism.py`; `phase27_batch_semantics_audit.json`;
`phase27_numeric_inference_mode_provenance_audit_v1_1.json`) establishes that under
`autocast(fp16)` **G forward numerics depend on batch membership** — replay achieved
`max_abs = 0.0` ONLY when the exact canonical batch membership was reproduced.

**Frozen:** `G_BATCH_MEMBERSHIP_SCIENTIFICALLY_MATERIAL = true`
(`SENSITIVE_UNDER_AUTOCAST_FP16__EXACT_PARTITION_MANDATORY`).

The non-load-bearing statement is **superseded semantically, not erased historically**.

## B. Canonical G authority (frozen)

G checkpoint `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` SHA `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` (params 3,523,001).

| Field | Value |
|---|---|
| device | cuda |
| model.eval() | true |
| model dtype | float32 |
| input dtype | float32 |
| autocast | enabled |
| autocast dtype | float16 |
| gradient context | `torch.no_grad()` |
| torch.inference_mode | false |
| batch size | 8 |
| probability computation | `sigmoid(logits.float())` → float32 |
| probability persistence | float16 |

## C. Frozen ROUTER_HOLDOUT G sample order and batch partition

**Ordering authority:** a **historically frozen canonical rule**
(`build_phase25a_global_cache.py:97,123-124,131-132,157-158`;
`run_phase27_exec_phaseA.py:234,262,268`), population-independent. It is **not** merely a
prospective Phase30 construction.

* sort keys: **dataset ascending, then sample_id ascending**
* domain ordering: **BUSI, ISIC, KUB, KVASIR**
* batch size: **8**
* batch boundary rule: **contiguous chunks of 8 within each domain**
* batches **do not** cross domain boundaries
* last partial batch: **trailing chunk of size n mod 8, not padded**

### Expected G batch counts

| Domain | n | batches | last batch |
|---|---|---|---|
| BUSI | 90 | 12 | 2 |
| ISIC | 383 | 48 | 7 |
| KUB | 298 | 38 | 2 |
| KVASIR | 104 | 13 | 8 |
| **TOTAL** | **875** | **111** | |

`logical_G_passes = 1`; `G_samples = 875`; `G_batch_forwards = 111`.

> **"G (once)" means ONE LOGICAL G EXTRACTION PASS over the complete ROUTER_HOLDOUT — NOT one
> literal model forward.** The 875 samples are processed in 111 batch forwards of
> ≤ 8 samples each.

The materialized membership manifest is
`reports/tables/phase30_router_holdout_g_batch_manifest.csv` (SHA `fc4c785770c45523fdfd440a464820f78caa6bcedeaa1cbe264e10ce5c4e0088`).

## D. Bootstrap plan frozen before first open

The holdout bootstrap draw plan is **materialized now**, before any image access, from
metadata only:
`data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz`
(SHA `59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1`).

DOMAIN_STRATIFIED_GROUP_BOOTSTRAP; unit = group_key; strata = BUSI/ISIC/KUB/KVASIR;
B = 2000; seed 42; `PCG64(42)`; percentile 2.5/97.5; paired draws. No GT, no predictions, no
outcomes. The Phase27/VAL808 plan is **not** copied. Immutable after first image access.

## E. Preserved v1.0 scientific decisions (unchanged)

ROUTER_HOLDOUT n = 875; A8/C9 target; seed42 canonical bundle; thresholds (ROI 0.30 / seg
0.50 / S_omega 0.50 / tau_C8 exact); lambda 1/4; cost constants; no top-K forcing; no
25%-forcing; GT separation; prediction hash barrier; statistics; metric definitions; compute
terminology (ANALYTICAL MAC LOWER BOUND); post-open immutability; TEST lock.

## F. Other components (unchanged)

R_psi: cuda, eval(), float32, autocast disabled, `torch.inference_mode()`, batch 8.
B_phi: cuda, eval(), float32, autocast disabled, `torch.inference_mode()`, canonical
full-matrix scoring path.
S_omega: cuda, eval(), float32, autocast disabled, `torch.inference_mode()`, batch 128.

The load-bearing correction applies **specifically to G**; the exact implementation batching
of every component remains frozen for reproducibility.

## G. Standing

ROUTER_HOLDOUT state `RESERVED_UNOPENED`; image reads 0; GT reads 0; outcome reads 0; model
forwards 0; TEST reads 0. **Phase30 one-shot execution has NOT started.**
