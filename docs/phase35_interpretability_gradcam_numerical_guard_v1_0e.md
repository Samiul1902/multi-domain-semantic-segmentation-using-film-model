# Phase 35 v1.0e - Pre-Execution Grad-CAM Numerical Observability + Fail-Closed Finite Guard Amendment

**Revision:** `ra_medfilm_barr_phase35_interpretability_v1_0e`
**Classification:** `PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_FINITE_GUARD_AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE`
**Date:** 2026-10-04
**Status:** COMPLETE_CANONICAL (source authoring + static governance only; no execution)

## 1. Why v1.0e exists

The frozen v1.0d synthetic smoke PASSED (returncode 0, 42/42 checks) but disclosed three
reporting/verification gaps in `phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json`
(`4d9fc89a...`):

| Gap | What was not verified | Severity | v1.0e closure |
|-----|-----------------------|----------|---------------|
| **G1** | In-session empty-mask helper check not emitted | REPORTING_ONLY | `empty_mask_helper_check_insession` (no extra forward/autograd) |
| **G2** | Parameter non-null `.grad` counts not measurable after the frozen mode returned | REPORTING_ONLY | `parameter_grad_state_audit_insession` reads `.grad` in-session before return |
| **G3** | Gradient finiteness / pre-normalization CAM state not emitted or verified | **MATERIAL** | fail-closed finite guards + full diagnostics |

**G3 was material** because the frozen `cam_normalize` maps *any* non-finite CAM to all zeros
(`range = NaN`, `float(NaN) > 0` is `False` → `zeros_like`). Both v1.0d CAMs were all-zero
(`min = max = 0.0`). That observation was therefore consistent with **two** mutually exclusive
explanations: (a) a genuinely non-positive weighted-activation sum, or (b) non-finite gradients
silently masked by the frozen zero-range fallback. The v1.0d smoke could not distinguish them.

## 2. What v1.0e changes (implementation only)

The scientific Grad-CAM mathematics are **unchanged on finite inputs**. v1.0e adds exactly two
kinds of change, both fail-closed:

### 2.1 Finite guards (fail-closed)
`gradcam_gradient_enabled_numerically_guarded` inserts `_require_finite_tensor` /
`_require_finite_scalar` checks at each stage, in order:

1. `target_scalar_finite` — **before** `torch.autograd.grad`
2. `gradient_finite` — every raw `dA` per layer
3. `alpha_finite` — spatial-mean `dT/dA`
4. `pre_relu_weighted_map_finite` — `sum_k alpha_k A_k`
5. `post_relu_raw_cam_finite` — `ReLU(...)`
6. `upsampled_prenorm_cam_finite` — bilinear 512x512
7. `prenorm_cam_range_finite` — `max - min`
8. `normalized_cam_finite` — output of `cam_normalize_guarded`

`cam_normalize_guarded` preserves the frozen semantics **byte-for-byte on finite inputs**: a finite
zero-range CAM still falls back to all zeros. A **non-finite** CAM **raises** and can never reach the
zero-range fallback.

### 2.2 Direct diagnostics (observability)
Emitted from the same single forward/autograd: per-layer gradient shape/dtype/finite/min/max/abs_max,
alpha finite, pre-ReLU and post-ReLU CAM finite + abs_max, upsampled pre-normalization CAM range +
all-zero flag, normalized CAM min/max/finite, target scalar value + finite.

### 2.3 In-session reporting (G1 + G2)
- `empty_mask_helper_check_insession(mask_t)` — exercises the rank-safe helper with an all-False
  variant of the **already-computed** mask; full-field mean of a zero plane is exactly `0.0`. No extra
  forward, no extra autograd.
- `parameter_grad_state_audit_insession(models)` — reads `.grad` for every named parameter of G and
  B_phi inside the same process; expected `0 / 0`.

## 3. What does NOT change

- Scientific target source = persisted canonical `p_global >= 0.50` (built **before** the forward).
- Empty-mask fallback = full `[0,0,H,W]` foreground-logit mean.
- `alpha` = spatial mean of `dT/dA`; `cam_raw = ReLU(sum_k alpha_k A_k)`; bilinear 512x512 with
  `align_corners=False`; min-max normalization.
- Thresholds (segmentation output 0.50 / ROI proposal 0.30), Grad-CAM layers, CAM algorithm,
  precision/autocast, FiLM and router science, VAL64 gallery + display subset, read guards, claim
  guards, R_psi/S_omega exclusion.
- The frozen v1.0b / v1.0c / v1.0d modules are imported byte-identical and never modified.
- The frozen rank-safe target (`V0D.gradcam_target_scalar_rank_safe`) is reused by direct reference.

## 4. Governance results (all static, zero execution)

| Artifact | Result |
|----------|--------|
| Static preflight (`phase35_execution_source_static_preflight_v1_0e.json`) | **118/118** (54 original + 24 cumulative + 40 numerical-guard); 49 predecessors byte-identical |
| Model-free numerical-guard unit tests (`phase35_gradcam_numerical_guard_unit_v1_0e.json`) | **12/12** (CPU only, model-free) |
| Final check (`phase35_gradcam_numerical_guard_final_check_v1_0e.json`) | **18/18**; 22 artifacts bound |
| Model-free structural proof (stub model, CPU) | grads `[1,256,32,32]` / `[1,24,512,512]` finite; NaN target fails closed; empty-mask exact 0.0; param grads 0/0 |
| Gate env set | `PHASE35_SMOKE_EXECUTE` unset · `PHASE35_EXECUTE` unset |
| Mode invoked | NONE |
| Protected reads | VAL 0 · GT 0 · ROUTER_HOLDOUT 0 · TEST 0 |

## 5. Terminal

```
PHASE35_PREEXECUTION_GRADCAM_NUMERICAL_GUARD_V1_0E_COMPLETE__FIRST_V1_0D_SMOKE_PRESERVED_WITH_DISCLOSED_G1_G2_G3_REPORTING_GAPS__TARGET_GRADIENT_ALPHA_RAW_AND_PRENORMALIZATION_CAM_FINITE_GUARDS_AND_DIRECT_DIAGNOSTICS_IMPLEMENTED__FINITE_ZERO_RANGE_FALLBACK_PRESERVED_BUT_NONFINITE_INPUTS_FAIL_CLOSED__INSESSION_EMPTY_MASK_AND_PARAMETER_GRAD_REPORTING_BOUND__SCIENTIFIC_GRADCAM_MATHEMATICS_UNCHANGED_ON_FINITE_INPUTS__V1_0E_SOURCE_FREEZE_COMPLETE__SYNTHETIC_SMOKE_REEXECUTION_ELIGIBLE_NOT_STARTED
```

**The v1.0e synthetic smoke re-execution is ELIGIBLE but NOT STARTED.** Scientific Phase35 execution
requires `PHASE35_EXECUTE=1` and is **not** authorized by this work order. Phase36 not started.
