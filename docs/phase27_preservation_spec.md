# Phase 27 - Multi-Domain Performance Preservation Audit

## Provenance note
This is a **prospective pre-execution specification** frozen BEFORE any VAL808
inference.  It is governance / specification only.

- `phase27_classification = PHASE27_PRE_EXECUTION_PRESERVATION_AUDIT_SPECIFICATION`
- `phase27_operational_meaning = GOVERNANCE_SPECIFICATION_ONLY__NO_INFERENCE`
- Revision: `ra_medfilm_barr_preservation_v1_0`
- `governance_only = true` - `no_execution = true` - `science_changed = false`
- `training_authorized = false` - `fine_tuning_authorized = false` -
  `recalibration_authorized = false` - `policy_selection_authorized = false`
- `holdout_opened = false` - `test_opened = false`

## 1. Operational definition
Audit that regional refinement does not degrade multi-domain global performance,
by evaluating the **frozen Phase26 canonical bundle** on the **VAL808**
continuity development benchmark using a pre-frozen non-inferiority protocol.

- **System under test:** A8 / C9 (frozen Phase26 canonical bundle).
- **Global reference:** the SAME frozen GlobalMedFiLM inside the Phase26 bundle.
- **Preservation estimand:** macro-domain equal-weight mean Dice delta
  (`Delta_i = Dice(final_A8_i, GT_i) - Dice(global_i, GT_i)`; the four domain
  mean deltas are averaged with weight 1/4 each).
- **Non-inferiority margin:** 0.005; **claim only if** the lower 95% CI bound is
  strictly greater than -0.005.

## 2. Population ownership (supervisor ruling)
| Population | n | Role | Owner | Phase27 access |
|---|---|---|---|---|
| VAL808 | 808 | SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK | **Phase27** | allowed at execution |
| ROUTER_HOLDOUT | 875 | final development validation (one-shot) | **Phase30** | **FORBIDDEN** |
| TEST | 1683 | untouched final evaluation | Phase39 | **FORBIDDEN** |

VAL808 is **not** an untouched routing holdout and must never be used as a
substitute for ROUTER_HOLDOUT.

## 3. VAL808 population binding
- Manifest: `manifests/phase4_v3/val.csv` (metadata only; no image / mask read)
- SHA-256: `082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315`
- n = 808; domains: ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84
  (task_id 0/3/2/1)
- Group rule: `METADATA_ONLY_COMPOSITE_PATIENT_SINGLETON`
  (`KUB -> PATIENT::<patient_id>; ISIC/BUSI/KVASIR -> SINGLETON::<dataset>::<sample_id>`)
- Total groups = 639 (ISIC 357 / KUB 111 / KVASIR 87 / BUSI 84)
- Group partition is **provably identical** to the canonical Phase24 `group_key`
  partition on all 5832 TRAIN rows: the 16 `RISK::` pHash groups are singletons,
  so pHash relabelling never merges rows.

## 4. Statistics contract (frozen before inference)
- Estimator: domain-stratified **group** bootstrap, B = 2000, seed = 42,
  RNG = `numpy.random.Generator(numpy.random.PCG64(42))`, percentile CI at 2.5 / 97.5.
- Draw plan frozen at specification time in
  `data_cache/phase27_barr_preservation_v1_0/phase27_val808_bootstrap_plan_v1_0.npz`
  (authorized because group identifiers are obtainable from manifest metadata).
- Per-domain reporting is mandatory; a macro average may not hide domain harm.

## 5. GT / inference separation
Two-phase protocol with a hash barrier: VAL808 **images only** are read to produce
predictions for the global reference and the final A8 system; predictions are
written and hashed **before** any GT mask is read; GT is read only during scoring.
GT is never used for routing, fusion, or safety.

## 6. Reproducibility rule / locks
- Runtime policy (frozen): `delta_hat_final - 0.25*C`;
  `EXECUTE iff utility >= -5003565381643716252018011/205414980000000000000000000`.
- Runtime threshold exact: `-5003565381643716252018011/205414980000000000000000000`.
- Three distinct thresholds, never conflated: ROI proposal 0.3,
  segmentation output 0.5, S_omega accept 0.5.
- Reproducibility: MASTER seed 42; under autocast the forward depends on batch
  membership, so any replay reuses the canonical VAL808 sorted-by-(dataset,sample_id)
  contiguous chunk-of-8 partition.

## 7. Forbidden
NO VAL808 scientific inference in this specification · NO model construction ·
NO training · NO fine-tuning · NO backward · NO optimizer · NO recalibration ·
NO policy selection · NO budget change · NO lambda change · NO threshold change ·
NO ROUTER_HOLDOUT · NO TEST · NO Phase28 · NO Phase30.

<!-- PHASE27_PRESERVATION_SPEC_COMPLETE -->

<!-- PHASE27_PRESERVATION_SPEC_V1_1_EXECUTION_SEMANTICS_REPAIR -->

## v1.1 execution-semantics repair (2026-10-02)

Additive amendment.  v1.0 content above is preserved unchanged.

### Predecessor notebook rebind
- Canonical Phase26 notebook SHA = `5d063ecb57a7e213c2260a11e1daa66bb58bc2f6b5b4029cfc1ae0e3e91aa8c8`
  (old `57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0` preserved as `HISTORICAL_PREDECESSOR_PROVENANCE` in the archived
  pre-postclosure notebook).

### Numerical inference mode (evidence-based, CASE A)
Resolved from AUTHORITATIVE predecessor implementation evidence (not from this spec's own wording):
- device policy: CUDA-first, canonical requires CUDA (`src/utils/device.py`).
- autocast: **enabled**, dtype **float16** (`torch.amp.autocast(device_type='cuda', enabled=True)`);
  proven by `reports/audits/phase25b_global_checkpoint_binding.json` (`amp_autocast_enabled = true`)
  and the canonical Phase25A/25B forward paths.
- input dtype float32; parameter dtype float32; output probability computed float32,
  stored float16 (`prob512[gi] = p512.astype(np.float16)`).
- batch: size 8, contiguous chunks inside a single domain, order
  `sort_values(['dataset','sample_id'])`; outputs are **batch-membership dependent under autocast**
  and the exact canonical partition is prospectively frozen before VAL808 inference.

### Evidence class
`Phase27 evidence class = CONTINUITY_DEVELOPMENT_EVIDENCE`
(never `UNTOUCHED_HOLDOUT` / `EXTERNAL_VALIDATION` / `TEST_EVIDENCE`).

### Frozen VAL808 statistics (unchanged)
n = 808; ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84; groups = 639;
bootstrap B = 2000, seed 42, PCG64; bootstrap-plan SHA `8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93`.
The bootstrap plan is **not** regenerated.

### Secondary metrics / compute / failure behavior
- Secondary metrics: IoU / precision / recall **only if** canonical scorer semantics are frozen;
  else `NOT_REPORTED__SEMANTICS_NOT_FROZEN`.  Dice remains PRIMARY.
- Compute: `ANALYTICAL MAC LOWER BOUND` only (no latency / runtime / energy / memory /
  mobile-performance claim; Phase34 owns measured profiling).
- Failure behavior: if non-inferiority is not established, record the failure; no budget / lambda /
  threshold change, no retraining, no fine-tuning.

### Phase boundaries
Phase28 = Comprehensive System Ablation Matrix (not Phase27 work);
Phase30 = Final Development Validation Benchmark (exclusive ROUTER_HOLDOUT owner);
Phase39 = only TEST evaluation phase.

<!-- PHASE27_PRESERVATION_EXECUTION_COMPLETE -->

## Execution closure (2026-10-02)
The frozen Phase26 A8/C9 canonical bundle was evaluated on VAL808 under the
pre-frozen 0.005 non-inferiority contract.
- macro-domain point delta = +0.002210
- macro 95% CI = [+0.001133, +0.003298]
- preservation_asserted = True (lower bound > -0.005)
- terminal = `PHASE27_MULTIDOMAIN_PRESERVATION_AUDIT_COMPLETE__VAL808_CONTINUITY_RESULT_FROZEN__PHASE28_ELIGIBLE_NOT_STARTED`
