#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0e EXECUTABLE interpretability harness - Grad-CAM numerical observability + fail-closed
finiteness amendment.

Classification: PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_FINITE_GUARD_
                AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0e

Resolves the three reporting/verification gaps disclosed by the frozen v1.0d smoke
(`phase35_synthetic_smoke_reporting_gap_disclosure_v1_0d.json`, `4d9fc89a...`):
  G1  in-session empty-mask helper check not emitted;
  G2  parameter non-null `.grad` counts not measurable after the frozen mode returned;
  G3  gradient finiteness / pre-normalization CAM state not emitted or verified, so an all-zero CAM
       is consistent with BOTH a non-positive weighted-activation sum AND non-finite gradients masked
       by the frozen zero-range fallback in `cam_normalize`.

SUPERSEDES v1.0d ONLY where the Grad-CAM numerical guards, the finite/observability diagnostics, and
the smoke Grad-CAM reporting are concerned. The frozen v1.0b execution module (`58192684...`), the
frozen v1.0c smoke-amendment module (`4058fc55...`) and the frozen v1.0d rank-safety module
(`cccc109a...`) are preserved byte-for-byte and are IMPORTED here - never modified. The repaired
rank-safe target scalar / gradient path from v1.0d are reused by direct reference.

WHAT CHANGES (implementation only; the frozen scientific mathematics are unchanged)
  * FINITE GUARDS on the Grad-CAM path (fail-closed, before any masking can hide a problem):
      - target scalar T must be finite, else raise (BEFORE `torch.autograd.grad`);
      - each raw gradient tensor dA must be FINITE (and carry its declared shape/dtype), else raise;
      - alpha (spatial-mean dT/dA) must be finite, else raise;
      - the pre-ReLU weighted map and the post-ReLU raw CAM must be finite, else raise;
      - the upsampled PRE-NORMALIZATION CAM must be finite with a finite range, else raise;
      - `cam_normalize_guarded` NEVER reaches the frozen all-zeros zero-range fallback on a NON-FINITE
        input: a finite zero-range CAM still falls back to all zeros (frozen semantics preserved),
        but a non-finite CAM fails closed (raises).
  * DIAGNOSTICS emitted from the same single forward/autograd: per-layer gradient shape/dtype/
    finite/min/max/abs_max, alpha finite, pre-ReLU and post-ReLU CAM finite + range, upsampled
    pre-normalization CAM finite + range, normalized CAM min/max/finite, target scalar value + finite,
    and an in-session empty-mask helper check computed from the ALREADY-COMPUTED mask (NO extra
    forward, NO extra autograd).
  * PARAMETER GRAD COUNTS for G and B_phi are read directly in-session right after the smoke work,
    inside the same process, before the mode returns.

WHAT DOES NOT CHANGE (frozen scientific intent)
  * scientific target source = persisted canonical p_global >= 0.50, built BEFORE the new forward;
  * empty-mask fallback = full [0,0,H,W] foreground-logit mean;
  * alpha = spatial mean of dT/dA; cam_raw = ReLU(sum_k alpha_k A_k); bilinear 512x512 with
    align_corners=False; min-max normalization with all-zeros zero-range fallback ON FINITE INPUTS;
  * thresholds (segmentation output 0.50 / ROI proposal 0.30); Grad-CAM layers; CAM algorithm;
    precision/autocast context; FiLM and router science; VAL64 gallery + display subset; read guards;
    claim guards; R_psi/S_omega exclusion.

ON FINITE INPUTS the computed CAM is bit-identical to the frozen v1.0b/v1.0d CAM: the guards only
raise on non-finite states and only ADD observability; they do not alter any arithmetic result.

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

ROOT = REPO_ROOT
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0e"
CLASSIFICATION = ("PRE_EXECUTION_GRADCAM_NUMERICAL_OBSERVABILITY_AND_FAIL_CLOSED_FINITE_GUARD_"
                  "AMENDMENT__NO_SCIENTIFIC_PROTOCOL_CHANGE")

# --------------------------------------------------------------------------- #
# frozen Grad-CAM numerical contract (prospective; see docs + gap record)
# --------------------------------------------------------------------------- #
GRADCAM_LAYERS = V0D.GRADCAM_LAYERS                      # ("bridge", "decoder1")
TARGET_LOGITS_RANK = V0D.TARGET_LOGITS_RANK              # 4
TARGET_LOGITS_BATCH = V0D.TARGET_LOGITS_BATCH            # 1
TARGET_LOGITS_CHANNELS = V0D.TARGET_LOGITS_CHANNELS      # 1
TARGET_MASK_RANK = V0D.TARGET_MASK_RANK                  # 2
TARGET_MASK_DTYPE = V0D.TARGET_MASK_DTYPE                # "bool"
TARGET_SCALAR_IMPL = V0D.TARGET_SCALAR_IMPL              # gradcam_target_scalar_rank_safe
GRADCAM_GRADIENT_IMPL = "gradcam_gradient_enabled_numerically_guarded"
NORMALIZE_IMPL = "cam_normalize_guarded"
EMPTY_MASK_CHECK_IMPL = "empty_mask_helper_check_insession"
PARAM_GRAD_AUDIT_IMPL = "parameter_grad_state_audit_insession"

# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"
SCIENCE_GATE_ENV = "PHASE35_EXECUTE"

# --------------------------------------------------------------------------- #
# smoke: reuse the frozen v1.0c counter store VERBATIM (semantics preserved);
# v1.0e adds NO new counters and changes NO expected count.
# --------------------------------------------------------------------------- #
SMOKE_COUNTERS = V0C.SMOKE_COUNTERS
SMOKE_EXPECTED_COUNTERS = V0C.SMOKE_EXPECTED_COUNTERS
SMOKE_SEED = V0C.SMOKE_SEED
SMOKE_IMAGE_SHAPE = V0C.SMOKE_IMAGE_SHAPE
SMOKE_TASK_ID = V0C.SMOKE_TASK_ID
SMOKE_TARGET_MASK_NAME = V0D.SMOKE_TARGET_MASK_NAME
SMOKE_TARGET_MASK_SHAPE = V0D.SMOKE_TARGET_MASK_SHAPE
SMOKE_TARGET_MASK_GEOMETRY = V0D.SMOKE_TARGET_MASK_GEOMETRY
SMOKE_FORBIDDEN_CALLS = V0D.SMOKE_FORBIDDEN_CALLS

# --------------------------------------------------------------------------- #
# frozen finite-guard contract
# --------------------------------------------------------------------------- #
FINITE_GUARD_STAGES = (
    "target_scalar_finite",
    "gradient_finite",
    "alpha_finite",
    "pre_relu_weighted_map_finite",
    "post_relu_raw_cam_finite",
    "upsampled_prenorm_cam_finite",
    "prenorm_cam_range_finite",
    "normalized_cam_finite",
)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# finite-guard helpers (fail-closed; explicit raises survive `python -O`)
# --------------------------------------------------------------------------- #
def _require_finite_tensor(t, stage: str, extra: str = ""):
    """Fail CLOSED if a tensor contains any non-finite element. Returns the tensor unchanged."""
    import torch
    if not torch.is_tensor(t):
        raise TypeError(f"GRADCAM_FINITE_GUARD[{stage}]: expected a torch.Tensor, got {type(t)}")
    if not bool(torch.isfinite(t).all()):
        n_bad = int((~torch.isfinite(t)).sum())
        raise RuntimeError(
            f"GRADCAM_FINITE_GUARD[{stage}]: tensor contains {n_bad} non-finite element(s) "
            f"(shape {tuple(t.shape)}, dtype {t.dtype}){(' | ' + extra) if extra else ''}")
    return t


def _require_finite_scalar(s, stage: str, extra: str = ""):
    """Fail CLOSED if a scalar is non-finite (NaN or +/-inf)."""
    import math
    v = float(s)
    if not math.isfinite(v):
        raise RuntimeError(f"GRADCAM_FINITE_GUARD[{stage}]: scalar is non-finite ({v})"
                           f"{(' | ' + extra) if extra else ''}")
    return v


def _tensor_stats(t) -> dict:
    """Deterministic diagnostic statistics for a tensor (finite tensors only by contract)."""
    import torch
    d = t.detach().float()
    return OrderedDict([
        ("shape", list(d.shape)), ("dtype", str(t.dtype)),
        ("finite", bool(torch.isfinite(t).all())),
        ("min", float(d.min())), ("max", float(d.max())),
        ("abs_max", float(d.abs().max())),
    ])


def cam_normalize_guarded(cam):
    """Frozen `cam_normalize` semantics with a fail-closed non-finite guard.

    Frozen intent (unchanged ON FINITE INPUTS):
      rng = max(c) - min(c)
      if rng > 0: (c - min)/rng  else all-zeros fallback.

    v1.0e adds EXACTLY ONE property: the input must be finite. A finite zero-range CAM still takes
    the frozen all-zeros fallback (semantics preserved byte-for-byte). A NON-finite CAM fails closed
    and can NEVER reach the zero-range fallback, so an all-zero normalized CAM always means "genuine
    non-positive weighted-activation sum", never "masked NaN/inf".
    """
    import torch
    _require_finite_tensor(cam, "prenorm_cam_range_finite",
                           "cam_normalize_guarded refuses non-finite input")
    c = cam[0, 0] if cam.dim() == 4 else cam
    rng = c.max() - c.min()
    if not bool(torch.isfinite(rng)):
        raise RuntimeError(f"GRADCAM_FINITE_GUARD[prenorm_cam_range_finite]: range non-finite "
                           f"(min={float(c.min())}, max={float(c.max())})")
    if float(rng) > 0:
        return (c - c.min()) / rng
    return torch.zeros_like(c)


# --------------------------------------------------------------------------- #
# numerically guarded, rank-safe Grad-CAM gradient path (the scientific path)
# --------------------------------------------------------------------------- #
def gradcam_gradient_enabled_numerically_guarded(g_model, images, task_ids, m_pred,
                                                 layers=GRADCAM_LAYERS):
    """v1.0d rank-safe Grad-CAM path + fail-closed numerical guards + full diagnostics.

    Identical scientific mathematics to `V0D.gradcam_gradient_enabled_rank_safe`: same hooks, same
    enable_grad + autocast fp16, same rank-safe target scalar, same `torch.autograd.grad`, same
    alpha/ReLU/bilinear/align_corners, and the same min-max normalization on finite inputs. The only
    additions are the finite guards and the emitted diagnostics.
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

        return {"cams": cams, "T": float(T), "target_scalar_finite": True,
                "empty_prediction_fallback_used": empty_fallback,
                "target_scalar_impl": TARGET_SCALAR_IMPL,
                "normalization_impl": NORMALIZE_IMPL,
                "gradient_impl": GRADCAM_GRADIENT_IMPL,
                "finite_guards_applied": list(FINITE_GUARD_STAGES),
                "activation_shapes": {n: list(acts[n].shape) for n in layers},
                "gradient_diagnostics": grad_diag,
                "cam_diagnostics": cam_diag,
                "mask_t": mask_t}
    finally:
        for h in handles:
            h.remove()                                   # deterministic hook removal


def gradcam_per_sample_runner():
    """Static, side-effect-free binding of the executable per-sample Grad-CAM runner.

    Returns the guarded, rank-safe per-sample gradient function as a first-class callable. This is
    the FUNCTION-level anchor for the scientific Grad-CAM path: `mode_gradcam`, `mode_science` and
    `smoke_gradcam` all bind to THIS function, so a static call-graph audit resolves the guarded
    helper (and, transitively, the frozen v1.0d rank-safe target scalar) from every scientific mode.
    Calling this function performs no model work; it only returns the function object.
    """
    return gradcam_gradient_enabled_numerically_guarded


def gradcam_path_contract() -> dict:
    """Declarative binding of the per-sample Grad-CAM path to the guarded, rank-safe helper."""
    return OrderedDict([
        ("target_scalar", TARGET_SCALAR_IMPL),
        ("target_scalar_module", V0D.__name__),
        ("per_sample_gradient_path", GRADCAM_GRADIENT_IMPL),
        ("per_sample_gradient_path_module", __name__),
        ("cam_normalization", NORMALIZE_IMPL),
        ("cam_normalization_module", __name__),
        ("frozen_cam_normalization_reused_for_finite_inputs", V0B.cam_normalize.__name__),
        ("empty_mask_check", EMPTY_MASK_CHECK_IMPL),
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
        ("scientific_mathematics_changed", False),
    ])


# --------------------------------------------------------------------------- #
# in-session diagnostics (NO extra forward, NO extra autograd)
# --------------------------------------------------------------------------- #
def empty_mask_helper_check_insession(mask_t) -> dict:
    """In-session empty-mask helper check on the ALREADY-COMPUTED mask (closes G1).

    Exercises `V0D.gradcam_target_scalar_rank_safe` with an all-False variant of the mask that was
    already produced by the single guarded forward. It performs NO forward and NO autograd: the
    logits tensor is fabricated with `torch.zeros` and the helper only ever reduces it, so the
    frozen full-field mean of a zero plane is exactly 0.0 (a deterministic bound, not an estimate).
    """
    import torch
    empty = torch.zeros_like(mask_t)
    logits_zero = torch.zeros(1, TARGET_LOGITS_CHANNELS, *tuple(mask_t.shape),
                              dtype=torch.float32, device=mask_t.device)
    T_empty = V0D.gradcam_target_scalar_rank_safe(logits_zero, empty)
    val = _require_finite_scalar(T_empty, "target_scalar_finite", "empty-mask helper check")
    SMOKE_COUNTERS["synthetic_smoke_target_masks"] += 1
    return OrderedDict([
        ("empty_mask_any", bool(empty.any())),
        ("full_field_fallback_used", True),
        ("empty_mask_scalar", val),
        ("empty_mask_scalar_exact_zero", bool(val == 0.0)),
        ("fusion_mask_source", "zero plane (deterministic bound; NOT a real logits tensor)"),
        ("extra_forward_performed", False),
        ("extra_autograd_performed", False),
    ])


def parameter_grad_state_audit_insession(models: dict) -> dict:
    """Direct in-session parameter `.grad` non-null counts (closes G2).

    Read inside the SAME process right after the smoke work, before the mode returns. The expected
    contract is 0 / 0 for each model: `torch.autograd.grad` (used for both the Grad-CAM target and
    the router numeric input) does NOT populate `.grad`, and every attribution target is an
    activation or a numeric input, never a parameter.
    """
    out = OrderedDict()
    total_nonnull = 0
    for label, model in models.items():
        n_named = 0
        n_nonnull = 0
        for _name, p in model.named_parameters():
            n_named += 1
            if p.grad is not None:
                n_nonnull += 1
        total_nonnull += n_nonnull
        out[label] = OrderedDict([
            ("named_parameter_tensors", n_named),
            ("non_null_grad_tensors", n_nonnull),
            ("all_grads_null", n_nonnull == 0),
        ])
    out["total_non_null_grad_tensors"] = total_nonnull
    out["NO_PARAMETER_GRAD_POPULATED"] = (total_nonnull == 0)
    out["mechanism"] = ("torch.autograd.grad does not populate .grad; attribution targets are "
                        "activations / numeric inputs, never parameters")
    return out


# --------------------------------------------------------------------------- #
# smoke-only helpers (guarded variants of the frozen v1.0c/v1.0d smoke helpers)
# --------------------------------------------------------------------------- #
def smoke_synthetic_target_mask_rank2():
    """SMOKE_SYNTHETIC_TARGET_MASK_RANK2: deterministic rank-2 centered square (frozen v1.0d)."""
    return V0D.smoke_synthetic_target_mask_rank2()


def smoke_gradcam(g_model) -> dict:
    """ONE synthetic gradient-enabled G forward through the GUARDED canonical Grad-CAM path."""
    img_t, tid = V0C.smoke_synthetic_image()
    mask = smoke_synthetic_target_mask_rank2()
    res = gradcam_gradient_enabled_numerically_guarded(
        g_model, img_t, tid, mask, layers=GRADCAM_LAYERS)
    SMOKE_COUNTERS["G_synthetic_forwards"] += 1
    SMOKE_COUNTERS["total_model_forwards"] += 1
    SMOKE_COUNTERS["G_gradcam_autograd_calls"] += 1
    SMOKE_COUNTERS["total_autograd_calls"] += 1

    cams = res["cams"]
    SMOKE_COUNTERS["synthetic_CAM_maps"] += len(cams)

    # G1: in-session empty-mask helper check (no extra forward/autograd)
    empty_check = empty_mask_helper_check_insession(res["mask_t"])

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
            ("observability_amendment_revision", REVISION),
        ])),
    ])


# --------------------------------------------------------------------------- #
# v1.0e-local modes
# --------------------------------------------------------------------------- #
def mode_smoke() -> dict:
    """PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION - guarded, fully observable."""
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

    ev["classification"] = "PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION"
    ev["not"] = "PHASE35_SCIENTIFIC_INTERPRETABILITY_RESULT"
    ev["counters"] = dict(SMOKE_COUNTERS)
    ev["expected_counters"] = dict(SMOKE_EXPECTED_COUNTERS)
    ev["counts_match_expected"] = all(
        SMOKE_COUNTERS[k] == v for k, v in SMOKE_EXPECTED_COUNTERS.items())
    ev["all_pass"] = bool(ev["film_smoke"]["all_pass"]
                          and ev["parameter_immutability"]["MODEL_PARAMETERS_UNCHANGED"]
                          and ev["counts_match_expected"]
                          and ev["zero_denominator_policy"]["ZERO_ROUTER_GRAD_ATTRIBUTION"]
                          and ev["gradcam_smoke"]["all_gradients_finite"]
                          and ev["gradcam_smoke"]["all_prenorm_cams_finite"]
                          and ev["gradcam_smoke"]["all_normalized_cams_finite"]
                          and ev["gradcam_smoke"]["empty_mask_helper_check"]["empty_mask_scalar_exact_zero"]
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
    """Family composition. Only the Grad-CAM numerical-guard binding changes (implementation only)."""
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
                      "IMPLEMENTATION_NUMERICAL_SAFETY_AND_OBSERVABILITY_ONLY"}),
                ("I3_ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION",
                 {"implementation": "V0B (verbatim)", "semantics_changed": False}),
                ("I4_BENEFIT_ROUTER_FEATURE_ATTRIBUTION",
                 {"implementation": "V0B.mode_router", "semantics_changed": False}),
            ])}


MODE_DISPATCH = OrderedDict([
    ("smoke", mode_smoke),
    ("film", V0B.mode_film),          # frozen v1.0b, reused verbatim
    ("gradcam", mode_gradcam),        # v1.0e-local, bound to the guarded rank-safe path
    ("router", V0B.mode_router),      # frozen v1.0b, reused verbatim
    ("science", mode_science),        # v1.0e-local composition; Grad-CAM -> guarded path
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
