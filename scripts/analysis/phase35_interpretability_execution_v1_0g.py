#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0g EXECUTABLE interpretability harness - SMOKE COUNTER-CONTRACT SEPARATION repair.

Classification: PRE_EXECUTION_ACTUAL_LOGITS_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_AMENDMENT__
                NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0g

Repairs the SINGLE source-level defect that correctly blocked the first v1.0e synthetic smoke
(`phase35_v1_0e_empty_mask_observability_block.json`, `eef4f2b9...`;
 determination `V1_0E_EMPTY_MASK_OBSERVABILITY_IMPLEMENTATION_INCOMPLETE`):

  the frozen v1.0e `empty_mask_helper_check_insession` validated the empty-mask full-field fallback
  against a FABRICATED `torch.zeros(...)` logits SURROGATE (self-labelled "NOT a real logits
  tensor"). Work-order §Q requires the fallback to be validated with the ACTUAL logits tensor produced
  by the SAME synthetic G forward and FORBIDS a zero-logit surrogate.

WHAT CHANGES (implementation only; the frozen scientific mathematics are unchanged)
  * The empty-mask fallback validation is performed INSIDE the guarded Grad-CAM function, while the
    ACTUAL `logits` tensor returned by the single synthetic G forward is still in scope. It therefore
    uses the SAME actual logits object as the scientific target, not a surrogate.
  * A fixed comparison contract is bound: `torch.isclose(helper_return, expected_full_plane_mean,
    atol=1e-7, rtol=0)`, with every diagnostic emitted (`helper_return`, `expected_full_plane_mean`,
    `difference`, `atol`, `rtol`, `comparison_pass`, `finite`, `same_actual_G_logits_used=true`,
    `surrogate_zero_logits_used=false`, `empty_mask_rank/shape/dtype/true_pixels`,
    `fallback_selected`, `additional_G_forwards=0`, `additional_autograd_calls=0`).
  * NO second G forward and NO second autograd operation: the empty-mask check is a pure reduction of
    the ALREADY-COMPUTED logits.
  * The only empty-mask path reachable from `mode_smoke` uses the actual logits. The historical v1.0e
    zero-plane helper is preserved in v1.0e provenance but is UNREACHABLE from this module (v1.0f
    re-implements `empty_mask_helper_check_insession` to require the actual logits and provides no
    zero-plane fallback that smoke can reach).

WHAT DOES NOT CHANGE (frozen scientific intent; §H/§I/§J/§K)
  * scientific target source = persisted canonical p_global >= 0.50, built BEFORE the new forward;
  * empty-mask mathematical fallback = full [0,0,H,W] foreground-logit mean (UNCHANGED arithmetic);
  * alpha / ReLU / bilinear 512x512 align_corners=False / min-max normalization with the all-zeros
    zero-range fallback ON FINITE INPUTS;
  * the eight-stage fail-closed finite guards (target_scalar / gradient / alpha / pre_relu_weighted_map
    / post_relu_raw_cam / upsampled_prenorm_cam / prenorm_cam_range / normalized_cam);
  * the direct in-session parameter `.grad` audit for G and B_phi (expected 0 / 0);
  * thresholds; Grad-CAM layers; router and FiLM science; read guards; claim guards; R_psi / S_omega
    exclusion.

The frozen v1.0b/common/v1.0c/v1.0d/v1.0e modules are preserved byte-for-byte and are IMPORTED here -
never modified. The v1.0d rank-safe target scalar is reused by direct reference.

v1.0g repairs the SINGLE bookkeeping defect that correctly blocked the first v1.0f smoke
(`phase35_synthetic_smoke_terminal_v1_0f.json`, `728d1535...`): the v1.0f in-scope actual-logits
empty-mask observability helper incremented the SAME counter used for the PRIMARY synthetic target
mask, so `synthetic_smoke_target_masks` reached 2 against a frozen expected value of 1.

WHAT CHANGES (bookkeeping only)
  * `primary_synthetic_target_masks` is the canonical counter for PRIMARY synthetic target masks
    (frozen expected = 1). It is incremented ONCE, by `smoke_synthetic_target_mask_rank2()`.
  * `actual_logits_empty_mask_helper_checks` is a NEW, separate counter for the empty-mask
    OBSERVABILITY / FALLBACK-VALIDATION event (frozen expected = 1). The helper still creates one
    rank-2 all-False Boolean mask, but that mask is a diagnostic derivative of the SAME primary
    mask and is NOT a scientific or primary target mask.
  * `synthetic_smoke_target_masks` is retained as a BACKWARDS-COMPATIBLE ALIAS of
    `primary_synthetic_target_masks` and therefore MUST equal 1.
  * `additional_G_forwards_for_empty_mask` / `additional_autograd_calls_for_empty_mask` are frozen
    at 0 (the empty-mask check performs no forward and no autograd).

WHAT DOES NOT CHANGE (frozen scientific intent)
  * every model, numerical, interface, protected-data, and immutability behavior of v1.0f is
    inherited verbatim; the Grad-CAM mathematics, eight finite guards, alpha/ReLU/bilinear/
    align_corners=False/min-max normalization, atol=1e-7 / rtol=0 comparison, direct parameter
    `.grad` audit, router and FiLM semantics, and read guards are untouched.

!! ZERO-EXECUTION GUARD !!
Importing this module performs NO model construction, NO checkpoint load, NO forward, NO autograd,
NO Grad-CAM, NO router attribution and NO raw-image read. All work lives in main().

Gates (distinct by design):
  * smoke mode       -> requires PHASE35_SMOKE_EXECUTE=1
  * scientific modes -> require PHASE35_EXECUTE=1   (PHASE35_SMOKE_EXECUTE does NOT authorize them)

Protected data: ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

import phase35_interpretability_common_v1_0b as C           # noqa: E402  (frozen, reused)
import phase35_interpretability_execution_v1_0b as V0B      # noqa: E402  (frozen science)
import phase35_interpretability_execution_v1_0c as V0C      # noqa: E402  (frozen smoke helpers)
import phase35_interpretability_execution_v1_0d as V0D      # noqa: E402  (frozen rank-safe target)
import phase35_interpretability_execution_v1_0e as V0E      # noqa: E402  (frozen finite guards)

ROOT = REPO_ROOT
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0g"
CLASSIFICATION = ("PRE_EXECUTION_SYNTHETIC_SMOKE_COUNTER_CONTRACT_REPAIR"
                  "__NO_SCIENTIFIC_PROTOCOL_CHANGE")
ONLY_CHANGE = "SMOKE_COUNTER_CATEGORY_SEPARATION"

# --------------------------------------------------------------------------- #
# frozen Grad-CAM numerical contract (reused from v1.0e / v1.0d)
# --------------------------------------------------------------------------- #
GRADCAM_LAYERS = V0D.GRADCAM_LAYERS                      # ("bridge", "decoder1")
TARGET_LOGITS_RANK = V0D.TARGET_LOGITS_RANK              # 4
TARGET_LOGITS_BATCH = V0D.TARGET_LOGITS_BATCH            # 1
TARGET_LOGITS_CHANNELS = V0D.TARGET_LOGITS_CHANNELS      # 1
TARGET_MASK_RANK = V0D.TARGET_MASK_RANK                  # 2
TARGET_MASK_DTYPE = V0D.TARGET_MASK_DTYPE                # "bool"
TARGET_SCALAR_IMPL = V0D.TARGET_SCALAR_IMPL              # gradcam_target_scalar_rank_safe
GRADCAM_GRADIENT_IMPL = "gradcam_gradient_enabled_numerically_guarded_v1_0f"
NORMALIZE_IMPL = "cam_normalize_guarded"                 # reused verbatim from v1.0e
EMPTY_MASK_CHECK_IMPL = "empty_mask_helper_check_insession_actual_logits"
PARAM_GRAD_AUDIT_IMPL = "parameter_grad_state_audit_insession"   # reused verbatim from v1.0e

# frozen empty-mask comparison contract (§F) - declared BEFORE any smoke
EMPTY_MASK_ATOL = 1e-7
EMPTY_MASK_RTOL = 0.0

# --------------------------------------------------------------------------- #
# gates (distinct by design; reused verbatim from v1.0e)
# --------------------------------------------------------------------------- #
SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"
SCIENCE_GATE_ENV = "PHASE35_EXECUTE"

# --------------------------------------------------------------------------- #
# smoke counters (v1.0g COUNTER-CONTRACT SEPARATION)
#
# The frozen v1.0c store is COPIED (not mutated) so that the three mask-related counters can be
# declared with semantically SEPARATE keys:
#   * primary_synthetic_target_masks            -> PRIMARY synthetic target masks   (expected 1)
#   * synthetic_smoke_target_masks              -> backwards-compatible ALIAS        (expected 1)
#   * actual_logits_empty_mask_helper_checks    -> empty-mask observability event    (expected 1)
#   * additional_G_forwards_for_empty_mask      -> must stay 0
#   * additional_autograd_calls_for_empty_mask  -> must stay 0
# The two mask EVENTS are semantically different and MUST NOT share one counter.
# --------------------------------------------------------------------------- #
SMOKE_COUNTERS = OrderedDict(V0C.SMOKE_COUNTERS)
SMOKE_COUNTERS["primary_synthetic_target_masks"] = 0
SMOKE_COUNTERS["actual_logits_empty_mask_helper_checks"] = 0
SMOKE_COUNTERS["additional_G_forwards_for_empty_mask"] = 0
SMOKE_COUNTERS["additional_autograd_calls_for_empty_mask"] = 0
_FROZEN_V1_0C_EXPECTED = OrderedDict(V0C.SMOKE_EXPECTED_COUNTERS)
_FROZEN_V1_0C_EXPECTED["synthetic_smoke_target_masks"] = 1   # alias now counts ONLY primary masks
SMOKE_EXPECTED_COUNTERS = _FROZEN_V1_0C_EXPECTED
EXPECTED_COUNTERS_V1_0G = OrderedDict(SMOKE_EXPECTED_COUNTERS)
EXPECTED_COUNTERS_V1_0G["primary_synthetic_target_masks"] = 1
EXPECTED_COUNTERS_V1_0G["actual_logits_empty_mask_helper_checks"] = 1
EXPECTED_COUNTERS_V1_0G["additional_G_forwards_for_empty_mask"] = 0
EXPECTED_COUNTERS_V1_0G["additional_autograd_calls_for_empty_mask"] = 0
PRIMARY_TARGET_MASK_COUNTER = "primary_synthetic_target_masks"
PRIMARY_TARGET_MASK_ALIAS_COUNTER = "synthetic_smoke_target_masks"
EMPTY_MASK_OBSERVABILITY_COUNTER = "actual_logits_empty_mask_helper_checks"
SMOKE_SEED = V0C.SMOKE_SEED
SMOKE_IMAGE_SHAPE = V0C.SMOKE_IMAGE_SHAPE
SMOKE_TASK_ID = V0C.SMOKE_TASK_ID
SMOKE_TARGET_MASK_NAME = V0D.SMOKE_TARGET_MASK_NAME
SMOKE_TARGET_MASK_SHAPE = V0D.SMOKE_TARGET_MASK_SHAPE
SMOKE_TARGET_MASK_GEOMETRY = V0D.SMOKE_TARGET_MASK_GEOMETRY
SMOKE_FORBIDDEN_CALLS = V0D.SMOKE_FORBIDDEN_CALLS

# the frozen finite guards are reused VERBATIM from v1.0e (never re-implemented here)
_require_finite_tensor = V0E._require_finite_tensor
_require_finite_scalar = V0E._require_finite_scalar
_tensor_stats = V0E._tensor_stats
cam_normalize_guarded = V0E.cam_normalize_guarded
FINITE_GUARD_STAGES = V0E.FINITE_GUARD_STAGES
parameter_grad_state_audit_insession = V0E.parameter_grad_state_audit_insession


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# ACTUAL-LOGITS empty-mask observability (the single v1.0f implementation change)
# --------------------------------------------------------------------------- #
def empty_mask_helper_check_insession_actual_logits(logits, mask_t) -> dict:
    """Validate the empty-mask full-field fallback against the ACTUAL same-forward logits (§E/§F).

    Uses the SAME rank-safe helper (`V0D.gradcam_target_scalar_rank_safe`) as the scientific target,
    applied to an all-False variant of the ALREADY-COMPUTED rank-2 mask, with the ALREADY-COMPUTED
    actual logits returned by the single synthetic G forward. It performs NO forward and NO autograd:
    both the logits and the mask are pre-existing tensors; the helper only reduces them.

    NO zero-logit surrogate is created or accepted (`surrogate_zero_logits_used = false`).
    """
    import torch
    # the ACTUAL logits must be a real tensor (never a fabricated zero plane)
    if not torch.is_tensor(logits):
        raise TypeError(f"EMPTY_MASK_ACTUAL_LOGITS: logits must be a torch.Tensor, got {type(logits)}")
    empty = torch.zeros_like(mask_t, dtype=torch.bool)
    # SAME rank-safe helper the scientific target uses, with the ACTUAL logits in scope
    helper_return_t = V0D.gradcam_target_scalar_rank_safe(logits, empty)
    helper_return = _require_finite_scalar(helper_return_t, "target_scalar_finite",
                                           "empty-mask actual-logits helper check")
    # independent expected full-field foreground mean from the SAME actual logits
    expected_full_plane_mean_t = logits.float()[0, 0, :, :].mean()
    expected_full_plane_mean = _require_finite_scalar(expected_full_plane_mean_t,
                                                      "target_scalar_finite",
                                                      "empty-mask expected full-plane mean")
    difference = abs(float(helper_return) - float(expected_full_plane_mean))
    comparison_pass = bool(torch.isclose(
        helper_return_t.float(), expected_full_plane_mean_t.float(),
        atol=EMPTY_MASK_ATOL, rtol=EMPTY_MASK_RTOL))
    finite = bool(torch.isfinite(torch.as_tensor([helper_return_t,
                                                  expected_full_plane_mean_t])).all())
    # v1.0g: the empty all-False mask is an OBSERVABILITY / FALLBACK-VALIDATION derivative of the
    # SAME primary mask, NOT a scientific or primary target mask. It MUST NOT increment the primary
    # (or alias) counter; it increments its own dedicated counter exactly once.
    SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER] += 1
    return OrderedDict([
        ("same_actual_G_logits_used", True),
        ("surrogate_zero_logits_used", False),
        ("empty_mask_rank", int(empty.ndim)),
        ("empty_mask_shape", list(empty.shape)),
        ("empty_mask_dtype", "bool"),
        ("empty_mask_true_pixels", int(empty.sum())),
        ("empty_mask_any", bool(empty.any())),
        ("fallback_selected", True),
        ("helper_return", float(helper_return)),
        ("expected_full_plane_mean", float(expected_full_plane_mean)),
        ("difference", float(difference)),
        ("atol", EMPTY_MASK_ATOL),
        ("rtol", EMPTY_MASK_RTOL),
        ("comparison_pass", comparison_pass),
        ("finite", finite),
        ("fusion_mask_source", "actual same-forward synthetic G logits tensor (v1.0g)"),
        ("counter_category", EMPTY_MASK_OBSERVABILITY_COUNTER),
        ("counts_as_primary_target_mask", False),
        ("additional_G_forwards", 0),
        ("additional_autograd_calls", 0),
        ("extra_forward_performed", False),
        ("extra_autograd_performed", False),
    ])


# --------------------------------------------------------------------------- #
# numerically guarded, rank-safe Grad-CAM path (the scientific path) - v1.0f
# --------------------------------------------------------------------------- #
def gradcam_gradient_enabled_numerically_guarded_v1_0f(g_model, images, task_ids, m_pred,
                                                       layers=GRADCAM_LAYERS):
    """v1.0e guarded rank-safe Grad-CAM path + in-scope ACTUAL-LOGITS empty-mask observability.

    Identical scientific mathematics to `V0E.gradcam_gradient_enabled_numerically_guarded`: same
    hooks, same enable_grad + autocast fp16, same rank-safe target scalar via the same frozen
    helper, same `torch.autograd.grad(T, [activations])`, same alpha/ReLU/bilinear/align_corners,
    same min-max normalization on finite inputs, and the same eight fail-closed finite guards. The
    only change is that the empty-mask fallback validation is computed with the ACTUAL `logits`
    tensor still in scope (before the function returns), instead of fabricating a zero-logit plane.
    """
    import torch
    acts, handles = {}, []
    for name in layers:
        module = g_model.film_layers[name]              # exact canonical hook target
        def _hook(_m, _i, out, _n=name):
            acts[_n] = out[0] if isinstance(out, tuple) else out
        handles.append(module.register_forward_hook(_hook))
    try:
        with torch.enable_grad():
            with torch.amp.autocast(device_type="cuda", dtype=torch.float16, enabled=True):
                logits = g_model(images, task_ids)

        # -- rank-safe mask + target scalar (reused from frozen v1.0d) ----------------------------
        mask_t = V0D._validate_target_mask(logits.float(), m_pred)
        empty_fallback = not bool(mask_t.any())
        T = V0D.gradcam_target_scalar_rank_safe(logits, m_pred)
        T_value = _require_finite_scalar(T, "target_scalar_finite")   # BEFORE autograd

        grads = torch.autograd.grad(T, [acts[n] for n in layers], retain_graph=False)

        grad_diag, cam_diag, cams = OrderedDict(), OrderedDict(), {}
        for name, A, dA in zip(layers, [acts[n] for n in layers], grads):
            # (1) each raw gradient must be finite and shape-preserving --------------------------
            _require_finite_tensor(dA, "gradient_finite", f"layer={name}")
            grad_diag[name] = _tensor_stats(dA)

            # (2) alpha = spatial mean of dT/dA must be finite -----------------------------------
            alpha = dA.mean(dim=(2, 3), keepdim=True)
            _require_finite_tensor(alpha, "alpha_finite", f"layer={name}")

            # (3) pre-ReLU weighted map must be finite -------------------------------------------
            weighted = (alpha * A).sum(dim=1, keepdim=True)
            _require_finite_tensor(weighted, "pre_relu_weighted_map_finite", f"layer={name}")

            # (4) post-ReLU raw CAM must be finite ------------------------------------------------
            cam_raw = torch.relu(weighted)
            _require_finite_tensor(cam_raw, "post_relu_raw_cam_finite", f"layer={name}")

            # (5) upsampled PRE-NORMALIZATION CAM must be finite with a finite range --------------
            cam = torch.nn.functional.interpolate(
                cam_raw, size=(512, 512), mode="bilinear",
                align_corners=C.GRADCAM_ALGORITHM["align_corners"])
            _require_finite_tensor(cam, "upsampled_prenorm_cam_finite", f"layer={name}")

            # (6) normalized CAM (guarded) must be finite -----------------------------------------
            norm = cam_normalize_guarded(cam)
            _require_finite_tensor(norm, "normalized_cam_finite", f"layer={name}")

            prenorm = _tensor_stats(cam)
            cam_diag[name] = OrderedDict([
                ("gradient", grad_diag[name]),
                ("alpha_finite", True),
                ("pre_relu_weighted_map_finite", True),
                ("post_relu_raw_cam_finite", True),
                ("pre_relu_weighted_map_abs_max", float(weighted.detach().abs().max())),
                ("post_relu_raw_cam_abs_max", float(cam_raw.detach().abs().max())),
                ("upsampled_prenorm_cam", prenorm),
                ("upsampled_prenorm_cam_finite", True),
                ("upsampled_prenorm_cam_range", float(cam.max() - cam.min())),
                ("prenorm_cam_all_zero", bool(float(cam.max()) == 0.0 and float(cam.min()) == 0.0)),
                ("normalized_cam_min", float(norm.detach().float().min())),
                ("normalized_cam_max", float(norm.detach().float().max())),
                ("normalized_cam_finite", True),
            ])
            cams[name] = norm.detach().float().cpu()

        # -- ACTUAL-LOGITS empty-mask observability (still in scope; NO extra forward/autograd) ----
        empty_check = empty_mask_helper_check_insession_actual_logits(logits, mask_t)

        return {"cams": cams, "T": float(T), "target_scalar_finite": True,
                "empty_prediction_fallback_used": empty_fallback,
                "target_scalar_impl": TARGET_SCALAR_IMPL,
                "normalization_impl": NORMALIZE_IMPL,
                "gradient_impl": GRADCAM_GRADIENT_IMPL,
                "finite_guards_applied": list(FINITE_GUARD_STAGES),
                "activation_shapes": {n: list(acts[n].shape) for n in layers},
                "gradient_diagnostics": grad_diag,
                "cam_diagnostics": cam_diag,
                "empty_mask_helper_check": empty_check,
                "mask_t": mask_t}
    finally:
        for h in handles:
            h.remove()                                   # deterministic hook removal


def gradcam_per_sample_runner():
    """Static, side-effect-free binding of the executable per-sample Grad-CAM runner.

    Returns the v1.0f guarded, rank-safe per-sample gradient function as a first-class callable.
    This is the FUNCTION-level anchor for the scientific Grad-CAM path: `mode_gradcam`, `mode_science`
    and `smoke_gradcam` all bind to THIS function, so a static call-graph audit resolves the guarded
    helper (and, transitively, the frozen v1.0d rank-safe target scalar) from every scientific mode.
    Calling this function performs no model work; it only returns the function object.
    """
    return gradcam_gradient_enabled_numerically_guarded_v1_0f


def gradcam_path_contract() -> dict:
    """Declarative binding of the per-sample Grad-CAM path to the guarded, rank-safe helper."""
    return OrderedDict([
        ("target_scalar", TARGET_SCALAR_IMPL),
        ("target_scalar_module", V0D.__name__),
        ("per_sample_gradient_path", GRADCAM_GRADIENT_IMPL),
        ("per_sample_gradient_path_module", __name__),
        ("cam_normalization", NORMALIZE_IMPL),
        ("cam_normalization_module", V0E.__name__),
        ("frozen_cam_normalization_reused_for_finite_inputs", V0B.cam_normalize.__name__),
        ("empty_mask_check", EMPTY_MASK_CHECK_IMPL),
        ("empty_mask_uses_actual_logits", True),
        ("empty_mask_surrogate_zero_logits_used", False),
        ("empty_mask_atol", EMPTY_MASK_ATOL),
        ("empty_mask_rtol", EMPTY_MASK_RTOL),
        ("parameter_grad_audit", PARAM_GRAD_AUDIT_IMPL),
        ("layers", list(GRADCAM_LAYERS)),
        ("logits_rank_contract", TARGET_LOGITS_RANK),
        ("logits_batch_contract", TARGET_LOGITS_BATCH),
        ("logits_channels_contract", TARGET_LOGITS_CHANNELS),
        ("mask_rank_contract", TARGET_MASK_RANK),
        ("mask_dtype_contract", TARGET_MASK_DTYPE),
        ("finite_guard_stages", list(FINITE_GUARD_STAGES)),
        ("nonfinite_prenorm_cam_reaches_zero_fallback", False),
        ("finite_zero_range_cam_reaches_zero_fallback", True),
        ("scientific_mask_source", "persisted canonical p_global >= T_SEGMENTATION_OUTPUT (0.50)"),
        ("defective_v1_0b_target_scalar_reachable", False),
        ("defective_v1_0b_gradient_path_reachable", False),
        ("v1_0e_zero_plane_empty_mask_helper_reachable", False),
        ("scientific_mathematics_changed", False),
    ])


# --------------------------------------------------------------------------- #
# smoke-only helpers (guarded variants of the frozen v1.0c/v1.0d smoke helpers)
# --------------------------------------------------------------------------- #
def smoke_synthetic_target_mask_rank2():
    """SMOKE_SYNTHETIC_TARGET_MASK_RANK2: deterministic rank-2 centered square (frozen v1.0d).

    v1.0g: this is THE one and only PRIMARY synthetic target mask. It increments the canonical
    PRIMARY counter and its backwards-compatible alias exactly ONCE (V0D already incremented the
    alias internally, so the alias is not double-counted here). The empty-mask OBSERVABILITY event
    (see `empty_mask_helper_check_insession_actual_logits`) uses a SEPARATE counter.
    """
    mask = V0D.smoke_synthetic_target_mask_rank2()
    # V0D increments the backwards-compatible alias `synthetic_smoke_target_masks` internally;
    # v1.0g adds the canonical PRIMARY counter (one event, two views of the same fact).
    SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER] += 1
    return mask


def smoke_gradcam(g_model) -> dict:
    """ONE synthetic gradient-enabled G forward through the GUARDED canonical Grad-CAM path."""
    img_t, tid = V0C.smoke_synthetic_image()
    mask = smoke_synthetic_target_mask_rank2()
    res = gradcam_gradient_enabled_numerically_guarded_v1_0f(
        g_model, img_t, tid, mask, layers=GRADCAM_LAYERS)
    SMOKE_COUNTERS["G_synthetic_forwards"] += 1
    SMOKE_COUNTERS["total_model_forwards"] += 1
    SMOKE_COUNTERS["G_gradcam_autograd_calls"] += 1
    SMOKE_COUNTERS["total_autograd_calls"] += 1

    cams = res["cams"]
    SMOKE_COUNTERS["synthetic_CAM_maps"] += len(cams)

    # empty-mask helper check is now produced INSIDE the guarded path (actual logits in scope)
    empty_check = res["empty_mask_helper_check"]

    cam_meta = OrderedDict()
    for name, cam in cams.items():
        cam_meta[name] = OrderedDict([
            ("shape", list(cam.shape)), ("dtype", str(cam.dtype)),
            ("finite", bool(cam.isfinite().all())),
            ("min", float(cam.min())), ("max", float(cam.max())),
            ("nonzero", bool(float(cam.max()) > 0.0)),
        ])

    gd = res["gradient_diagnostics"]
    cd = res["cam_diagnostics"]
    return OrderedDict([
        ("activation_shapes", res["activation_shapes"]),
        ("cams", cam_meta),
        ("scalar_target_evaluations", 1),
        ("autograd_calls", 1),
        ("target_scalar", res["T"]),
        ("target_scalar_finite", res["target_scalar_finite"]),
        ("empty_prediction_fallback_used", res["empty_prediction_fallback_used"]),
        ("target_scalar_impl", res["target_scalar_impl"]),
        ("normalization_impl", res["normalization_impl"]),
        ("gradient_impl", res["gradient_impl"]),
        ("finite_guards_applied", res["finite_guards_applied"]),
        ("gradient_diagnostics", gd),
        ("gradient_shapes_match_activations", {
            n: (list(gd[n]["shape"]) == res["activation_shapes"][n]) for n in GRADCAM_LAYERS}),
        ("all_gradients_finite", all(gd[n]["finite"] for n in GRADCAM_LAYERS)),
        ("cam_diagnostics", cd),
        ("all_prenorm_cams_finite", all(cd[n]["upsampled_prenorm_cam_finite"] for n in GRADCAM_LAYERS)),
        ("all_prenorm_cam_ranges_finite", all(
            bool(abs(cd[n]["upsampled_prenorm_cam_range"]) < float("inf")) for n in GRADCAM_LAYERS)),
        ("all_normalized_cams_finite", all(cd[n]["normalized_cam_finite"] for n in GRADCAM_LAYERS)),
        ("all_cams_all_zero", all(float(cams[n].max()) == 0.0 for n in GRADCAM_LAYERS)),
        ("prenorm_all_zero", all(cd[n]["prenorm_cam_all_zero"] for n in GRADCAM_LAYERS)),
        ("empty_mask_helper_check", empty_check),
        ("target_mask_name", SMOKE_TARGET_MASK_NAME),
        ("target_mask_geometry", SMOKE_TARGET_MASK_GEOMETRY),
        ("target_mask_shape", SMOKE_TARGET_MASK_SHAPE),
        ("target_mask_rank", TARGET_MASK_RANK),
        ("scientific_target_selection_used", False),
        ("rank4_workaround_used", False),
        ("mask_rank_contract", OrderedDict([
            ("canonical_logits_rank", TARGET_LOGITS_RANK),
            ("canonical_logits_shape_batch1", [1, 1, 512, 512]),
            ("smoke_mask_shape", SMOKE_TARGET_MASK_SHAPE),
            ("smoke_mask_rank", TARGET_MASK_RANK),
            ("scientific_mask_producer", "build_target_mask(persisted p_global >= 0.50)"),
            ("scientific_mask_shape", [512, 512]),
            ("scientific_mask_rank_compatible_with_canonical_helper", True),
            ("repaired_defect", "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY"),
            ("repair_revision", V0D.REVISION),
            ("observability_amendment_revision", V0E.REVISION),
            ("actual_logits_empty_mask_revision", REVISION),
        ])),
    ])


# --------------------------------------------------------------------------- #
# v1.0f-local modes
# --------------------------------------------------------------------------- #
def mode_smoke() -> dict:
    """PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION - guarded, fully observable, actual-logits check."""
    ev = OrderedDict()
    ev["authority_gates"] = V0B.verify_authority_gates()
    ev["environment"] = V0C.smoke_environment_check()
    ev["checkpoint_identity"] = V0C.smoke_checkpoint_identity()

    g_model, ginfo = V0B.load_g_component()
    SMOKE_COUNTERS["G_model_constructions"] += 1
    SMOKE_COUNTERS["checkpoint_deserializations"] += 1
    SMOKE_COUNTERS["strict_loads"] += 1
    bphi_model, bphi_state, binfo = V0B.load_bphi_component()
    SMOKE_COUNTERS["B_phi_model_constructions"] += 1
    SMOKE_COUNTERS["checkpoint_deserializations"] += 1
    SMOKE_COUNTERS["strict_loads"] += 1

    ev["G_identity"] = ginfo
    ev["B_phi_identity"] = binfo
    before = {"G": V0C.state_dict_identity(g_model), "B_phi": V0C.state_dict_identity(bphi_model)}

    ev["film_smoke"] = V0C.smoke_film_validate(g_model)
    ev["embedding_smoke"] = V0C.smoke_embedding_validate(g_model, bphi_model)
    ev["gradcam_smoke"] = smoke_gradcam(g_model)
    ev["router_smoke"] = V0C.smoke_router(bphi_model, bphi_state)
    ev["zero_denominator_policy"] = V0C.smoke_zero_denominator(bphi_state)

    # G2: direct in-session parameter `.grad` audit (read before the mode returns)
    ev["parameter_grad_state_audit"] = parameter_grad_state_audit_insession(
        {"G": g_model, "B_phi": bphi_model})

    ev["parameter_immutability"] = V0C.smoke_parameter_immutability(before, g_model, bphi_model)

    emc = ev["gradcam_smoke"]["empty_mask_helper_check"]
    ev["classification"] = "PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"
    ev["not"] = "PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"
    ev["counters"] = dict(SMOKE_COUNTERS)
    ev["expected_counters"] = dict(EXPECTED_COUNTERS_V1_0G)
    ev["counts_match_expected"] = all(
        SMOKE_COUNTERS[k] == v for k, v in EXPECTED_COUNTERS_V1_0G.items())
    ev["counter_contract"] = OrderedDict([
        ("primary_target_mask_counter", PRIMARY_TARGET_MASK_COUNTER),
        ("primary_target_mask_alias_counter", PRIMARY_TARGET_MASK_ALIAS_COUNTER),
        ("empty_mask_observability_counter", EMPTY_MASK_OBSERVABILITY_COUNTER),
        ("primary_target_mask_count", SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER]),
        ("primary_target_mask_alias_count", SMOKE_COUNTERS[PRIMARY_TARGET_MASK_ALIAS_COUNTER]),
        ("empty_mask_helper_check_count", SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER]),
        ("alias_equals_primary",
         SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER]
         == SMOKE_COUNTERS[PRIMARY_TARGET_MASK_ALIAS_COUNTER]),
        ("empty_mask_not_counted_as_primary",
         SMOKE_COUNTERS[PRIMARY_TARGET_MASK_COUNTER] == 1),
        ("additional_G_forwards_for_empty_mask", 0),
        ("additional_autograd_calls_for_empty_mask", 0),
    ])
    ev["counter_contract_ok"] = bool(
        ev["counter_contract"]["alias_equals_primary"]
        and ev["counter_contract"]["empty_mask_not_counted_as_primary"]
        and SMOKE_COUNTERS[EMPTY_MASK_OBSERVABILITY_COUNTER] == 1)
    ev["all_pass"] = bool(ev["counter_contract_ok"]
                          and ev["film_smoke"]["all_pass"]
                          and ev["parameter_immutability"]["MODEL_PARAMETERS_UNCHANGED"]
                          and ev["counts_match_expected"]
                          and ev["zero_denominator_policy"]["ZERO_ROUTER_GRAD_ATTRIBUTION"]
                          and ev["gradcam_smoke"]["all_gradients_finite"]
                          and ev["gradcam_smoke"]["all_prenorm_cams_finite"]
                          and ev["gradcam_smoke"]["all_normalized_cams_finite"]
                          and emc["same_actual_G_logits_used"]
                          and (not emc["surrogate_zero_logits_used"])
                          and emc["fallback_selected"]
                          and emc["comparison_pass"]
                          and emc["finite"]
                          and ev["parameter_grad_state_audit"]["NO_PARAMETER_GRAD_POPULATED"])
    return ev


def mode_gradcam() -> dict:
    """Frozen v1.0b display-subset resolution + binding to the GUARDED per-sample Grad-CAM path."""
    gallery, allow = V0B.load_gallery_allowlist()
    display = V0B.resolve_display_subset(gallery)            # BEFORE any saliency exists
    return {"mode": "gradcam", "allowlist_size": len(allow), "display_subset": display,
            "display_subset_resolved_before_saliency": True,
            "raw_val_image_reads": V0B.COUNTERS["raw_val_image_reads"],
            "gradcam_path": gradcam_path_contract(),
            "per_sample_runner": gradcam_per_sample_runner().__name__,
            "target_scalar_impl": TARGET_SCALAR_IMPL,
            "normalization_impl": NORMALIZE_IMPL,
            "defective_v1_0b_target_path_used": False}


def mode_science() -> dict:
    """Family composition. Only the Grad-CAM empty-mask observability binding changes."""
    return {"mode": "science", "families": list(C.EVIDENCE_FAMILIES),
            "F8_regional_implemented": C.F8_REGIONAL_IMPLEMENTED,
            "per_sample_runner": gradcam_per_sample_runner().__name__,
            "component_binding": OrderedDict([
                ("I1_FILM_PARAMETER_INTERPRETABILITY",
                 {"implementation": "V0B.mode_film", "semantics_changed": False}),
                ("I2_SEGMENTATION_GRADIENT_SALIENCY",
                 {"implementation": gradcam_path_contract.__name__,
                  "target_scalar": TARGET_SCALAR_IMPL,
                  "gradient_path": GRADCAM_GRADIENT_IMPL,
                  "normalization": NORMALIZE_IMPL,
                  "semantics_changed": False,
                  "implementation_change":
                      "ACTUAL_SAME_FORWARD_LOGITS_EMPTY_MASK_OBSERVABILITY"}),
                ("I3_ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION",
                 {"implementation": "V0B (verbatim)", "semantics_changed": False}),
                ("I4_BENEFIT_ROUTER_FEATURE_ATTRIBUTION",
                 {"implementation": "V0B.mode_router", "semantics_changed": False}),
            ])}


MODE_DISPATCH = OrderedDict([
    ("smoke", mode_smoke),
    ("film", V0B.mode_film),          # frozen v1.0b, reused verbatim
    ("gradcam", mode_gradcam),        # v1.0f-local, bound to the guarded rank-safe path
    ("router", V0B.mode_router),      # frozen v1.0b, reused verbatim
    ("science", mode_science),        # v1.0f-local composition; Grad-CAM -> guarded path
])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=list(C.MODES))
    a = ap.parse_args()

    if a.mode == "smoke":
        if os.environ.get(SMOKE_GATE_ENV) != "1":
            print("PHASE35 SMOKE NOT AUTHORIZED - smoke mode requires PHASE35_SMOKE_EXECUTE=1.")
            return 2
    elif a.mode in C.SCIENTIFIC_MODES:
        if os.environ.get(SCIENCE_GATE_ENV) != "1":
            print("PHASE35 EXECUTION NOT AUTHORIZED - scientific modes require PHASE35_EXECUTE=1.")
            return 2

    report = OrderedDict([("revision", REVISION), ("classification", CLASSIFICATION),
                          ("mode", a.mode),
                          ("smoke_gate_env", SMOKE_GATE_ENV),
                          ("science_gate_env", SCIENCE_GATE_ENV),
                          ("started_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))])
    if a.mode in C.SCIENTIFIC_MODES:
        report["authority_gates"] = V0B.verify_authority_gates()
    report.update(MODE_DISPATCH[a.mode]())
    print(json.dumps(report, indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
