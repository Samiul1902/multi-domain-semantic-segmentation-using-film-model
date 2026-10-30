#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0d EXECUTABLE interpretability harness - Grad-CAM target-mask RANK-SAFETY amendment.

Classification: PRE_EXECUTION_GRADCAM_TARGET_RANK_SAFETY_IMPLEMENTATION_AMENDMENT__NO_SCIENTIFIC_
                PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0d

Repairs the prospectively disclosed defect
`PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY`.

SUPERSEDES v1.0c ONLY where the Grad-CAM target scalar / Grad-CAM path / smoke target mask are
concerned. The frozen v1.0b execution module (`58192684...`) and the frozen v1.0c smoke-amendment
module (`4058fc55...`) are preserved byte-for-byte and are imported here - never modified.

WHAT CHANGES (implementation only; the frozen scientific intent is unchanged)
  * `gradcam_target_scalar_rank_safe` replaces the frozen `logits[mask]` indexing with an explicit
    contract: logits rank 4, shape [1,1,H,W]; mask rank 2, shape [H,W], dtype bool.
  * `gradcam_gradient_enabled_rank_safe` is the v1.0b per-sample gradient path with the SINGLE
    target-scalar call rebound to the repaired helper. Hooks, enable_grad, autocast fp16,
    torch.autograd.grad, alpha/ReLU/bilinear/align_corners, and `cam_normalize` are unchanged.
  * The synthetic smoke target mask is now rank-2 [512,512] and is consumed by the SAME repaired
    helper that scientific Grad-CAM uses (the v1.0c rank-4 workaround is removed).

WHAT DOES NOT CHANGE
  * scientific target source = persisted canonical p_global >= 0.50, built BEFORE the new forward;
  * empty-mask fallback = full [0,0,H,W] foreground-logit mean;
  * thresholds (segmentation output 0.50 / ROI proposal 0.30); Grad-CAM layers; CAM algorithm;
    precision/autocast context; FiLM and router science; VAL64 gallery + display subset; read
    guards; claim guards; R_psi/S_omega exclusion.

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

ROOT = REPO_ROOT
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0d"
CLASSIFICATION = ("PRE_EXECUTION_GRADCAM_TARGET_RANK_SAFETY_IMPLEMENTATION_AMENDMENT__"
                  "NO_SCIENTIFIC_PROTOCOL_CHANGE")

# --------------------------------------------------------------------------- #
# frozen target-scalar input contract (prospective; see docs + defect record)
# --------------------------------------------------------------------------- #
TARGET_LOGITS_RANK = 4
TARGET_LOGITS_BATCH = 1
TARGET_LOGITS_CHANNELS = 1
TARGET_MASK_RANK = 2
TARGET_MASK_DTYPE = "bool"
TARGET_SCALAR_IMPL = "gradcam_target_scalar_rank_safe"
GRADCAM_GRADIENT_IMPL = "gradcam_gradient_enabled_rank_safe"
GRADCAM_LAYERS = ("bridge", "decoder1")

# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"
SCIENCE_GATE_ENV = "PHASE35_EXECUTE"

# --------------------------------------------------------------------------- #
# smoke: reuse the frozen v1.0c counter store VERBATIM (semantics preserved)
# --------------------------------------------------------------------------- #
SMOKE_COUNTERS = V0C.SMOKE_COUNTERS
SMOKE_EXPECTED_COUNTERS = V0C.SMOKE_EXPECTED_COUNTERS
SMOKE_SEED = V0C.SMOKE_SEED
SMOKE_IMAGE_SHAPE = V0C.SMOKE_IMAGE_SHAPE
SMOKE_TASK_ID = V0C.SMOKE_TASK_ID
SMOKE_TARGET_MASK_NAME = "SMOKE_SYNTHETIC_TARGET_MASK_RANK2"
SMOKE_TARGET_MASK_SHAPE = [512, 512]          # rank 2 - the canonical scientific mask shape
SMOKE_TARGET_MASK_GEOMETRY = (
    "boolean tensor [512,512]; centered square rows 192:320, columns 192:320 = True, all other "
    "positions False (non-empty). Rank 2 is the CANONICAL scientific mask shape, so the smoke "
    "validates the same rank-4 logits + rank-2 mask contract that scientific Grad-CAM uses, through "
    "the same repaired helper `gradcam_target_scalar_rank_safe`. No rank-4 workaround.")
SMOKE_FORBIDDEN_CALLS = ["load_persisted_p_global", "load_gallery_allowlist",
                         "router_population_verify", "resolve_display_subset",
                         "guard_raw_path"]


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# --------------------------------------------------------------------------- #
# REPAIRED target scalar (the single scientific implementation change)
# --------------------------------------------------------------------------- #
def _validate_target_logits(logits):
    """Fail-closed contract for the scientific Grad-CAM logits tensor."""
    import torch
    if not torch.is_tensor(logits):
        raise TypeError(f"GRADCAM_TARGET: logits must be a torch.Tensor, got {type(logits)}")
    logits_f = logits.float()
    if logits_f.ndim != TARGET_LOGITS_RANK:
        raise RuntimeError(f"GRADCAM_TARGET: logits rank must be {TARGET_LOGITS_RANK}, "
                           f"got {logits_f.ndim}")
    if int(logits_f.shape[0]) != TARGET_LOGITS_BATCH:
        raise RuntimeError(f"GRADCAM_TARGET: logits batch must be {TARGET_LOGITS_BATCH}, "
                           f"got {int(logits_f.shape[0])}")
    if int(logits_f.shape[1]) != TARGET_LOGITS_CHANNELS:
        raise RuntimeError(f"GRADCAM_TARGET: logits channels must be {TARGET_LOGITS_CHANNELS}, "
                           f"got {int(logits_f.shape[1])}")
    return logits_f


def _validate_target_mask(logits_f, mask):
    """Fail-closed contract for the canonical rank-2 Boolean target mask. NO broadcasting."""
    import torch
    mask_t = torch.as_tensor(mask, device=logits_f.device)
    if mask_t.ndim != TARGET_MASK_RANK:
        raise RuntimeError(f"GRADCAM_TARGET: mask rank must be {TARGET_MASK_RANK}, "
                           f"got {mask_t.ndim} (shape {tuple(mask_t.shape)})")
    if tuple(mask_t.shape) != tuple(logits_f.shape[-2:]):
        raise RuntimeError(f"GRADCAM_TARGET: mask spatial shape must equal logits H,W "
                           f"{tuple(logits_f.shape[-2:])}, got {tuple(mask_t.shape)}")
    if mask_t.dtype != torch.bool:
        raise RuntimeError(f"GRADCAM_TARGET: mask dtype must be {TARGET_MASK_DTYPE}, "
                           f"got {mask_t.dtype}")
    return mask_t


def gradcam_target_scalar_rank_safe(logits, mask):
    """Rank-safe equivalent of the frozen scientific target scalar.

    Frozen intent (unchanged):
      M_pred = persisted p_global >= 0.50
      if M_pred non-empty:  T = mean(foreground logits under M_pred)
      else:                 T = mean(foreground logits over the full field)

    The rank-2 mask is the canonical representation. It is NEVER broadcast, never expanded to
    unrelated batch/channel dimensions, never created from the current forward, never the ROI-0.30
    mask, never GT, and never a sigmoid probability target.

    Implemented with explicit raises rather than `assert` so the fail-closed property survives
    `python -O`; semantics are identical to the specified assert-based contract.
    """
    logits_f = _validate_target_logits(logits)
    mask_t = _validate_target_mask(logits_f, mask)
    foreground_logits = logits_f[0, 0]                 # explicit [0,0] foreground plane
    if bool(mask_t.any()):
        return foreground_logits[mask_t].mean()        # mean ONLY the selected pixels
    return foreground_logits.mean()                    # empty-mask full-field fallback


def gradcam_gradient_enabled_rank_safe(g_model, images, task_ids, m_pred,
                                       layers=GRADCAM_LAYERS):
    """v1.0b per-sample Grad-CAM gradient path with the SINGLE target-scalar call rebound.

    Unchanged relative to the frozen v1.0b implementation: hook targets + deterministic removal,
    torch.enable_grad(), autocast fp16, torch.autograd.grad(T, [activations]), alpha = spatial mean
    of dT/dA, ReLU(sum_k alpha_k A_k), bilinear 512x512 with align_corners from the frozen contract,
    and `cam_normalize`. No optimizer, no optimizer.step(), no training backward.
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
        mask_t = _validate_target_mask(logits.float(), m_pred)
        empty_fallback = not bool(mask_t.any())
        T = gradcam_target_scalar_rank_safe(logits, m_pred)   # <-- repaired rank-safe target scalar
        grads = torch.autograd.grad(T, [acts[n] for n in layers], retain_graph=False)
        cams = {}
        for name, A, dA in zip(layers, [acts[n] for n in layers], grads):
            alpha = dA.mean(dim=(2, 3), keepdim=True)
            cam_raw = torch.relu((alpha * A).sum(dim=1, keepdim=True))
            cam = torch.nn.functional.interpolate(
                cam_raw, size=(512, 512), mode="bilinear",
                align_corners=C.GRADCAM_ALGORITHM["align_corners"])
            cams[name] = V0B.cam_normalize(cam).detach().float().cpu()
        return {"cams": cams, "T": float(T),
                "empty_prediction_fallback_used": empty_fallback,
                "target_scalar_impl": TARGET_SCALAR_IMPL,
                "activation_shapes": {n: list(acts[n].shape) for n in layers}}
    finally:
        for h in handles:
            h.remove()                                   # deterministic hook removal


def gradcam_path_contract() -> dict:
    """Declarative binding of the per-sample Grad-CAM path to the repaired target scalar.

    This is the static call-graph anchor: `mode_gradcam` and `mode_science` reference it, and it
    references the repaired helper - never the frozen defective `logits[mask]` implementation.
    """
    return OrderedDict([
        ("target_scalar", gradcam_target_scalar_rank_safe.__name__),
        ("target_scalar_module", __name__),
        ("per_sample_gradient_path", gradcam_gradient_enabled_rank_safe.__name__),
        ("cam_normalization", V0B.cam_normalize.__name__),
        ("layers", list(GRADCAM_LAYERS)),
        ("logits_rank_contract", TARGET_LOGITS_RANK),
        ("logits_batch_contract", TARGET_LOGITS_BATCH),
        ("logits_channels_contract", TARGET_LOGITS_CHANNELS),
        ("mask_rank_contract", TARGET_MASK_RANK),
        ("mask_dtype_contract", TARGET_MASK_DTYPE),
        ("scientific_mask_source", "persisted canonical p_global >= T_SEGMENTATION_OUTPUT (0.50)"),
        ("defective_v1_0b_target_scalar_reachable", False),
        ("defective_v1_0b_gradient_path_reachable", False),
    ])


# --------------------------------------------------------------------------- #
# smoke-only helpers
# --------------------------------------------------------------------------- #
def smoke_synthetic_target_mask_rank2():
    """SMOKE_SYNTHETIC_TARGET_MASK_RANK2: deterministic rank-2 centered square.

    NOT the scientific mechanism: scientific Grad-CAM still uses `persisted p_global >= 0.50`. This
    mask is smoke-only, is never routed through the persisted-prediction loader, and is consumed by
    the SAME repaired helper that scientific Grad-CAM uses.
    """
    import torch
    mask = torch.zeros(*SMOKE_TARGET_MASK_SHAPE, dtype=torch.bool, device="cuda")
    mask[192:320, 192:320] = True
    if not bool(mask.any()):
        raise RuntimeError("SMOKE target mask must be non-empty")
    if mask.ndim != TARGET_MASK_RANK:
        raise RuntimeError(f"SMOKE target mask rank must be {TARGET_MASK_RANK}")
    SMOKE_COUNTERS["synthetic_smoke_target_masks"] += 1
    return mask


def smoke_gradcam(g_model) -> dict:
    """ONE synthetic gradient-enabled G forward through the REPAIRED canonical Grad-CAM path."""
    img, tid = V0C.smoke_synthetic_image()
    mask = smoke_synthetic_target_mask_rank2()
    res = gradcam_gradient_enabled_rank_safe(g_model, img, tid, mask, layers=GRADCAM_LAYERS)
    SMOKE_COUNTERS["G_synthetic_forwards"] += 1
    SMOKE_COUNTERS["total_model_forwards"] += 1
    SMOKE_COUNTERS["G_gradcam_autograd_calls"] += 1
    SMOKE_COUNTERS["total_autograd_calls"] += 1
    cams = res["cams"]
    SMOKE_COUNTERS["synthetic_CAM_maps"] += len(cams)
    cam_meta = {}
    for name, cam in cams.items():
        cam_meta[name] = {"shape": list(cam.shape), "dtype": str(cam.dtype),
                          "finite": bool(cam.isfinite().all()),
                          "min": float(cam.min()), "max": float(cam.max())}
    return {"activation_shapes": res["activation_shapes"], "cams": cam_meta,
            "scalar_target_evaluations": 1,
            "autograd_calls": 1,
            "target_scalar_impl": res["target_scalar_impl"],
            "target_mask_name": SMOKE_TARGET_MASK_NAME,
            "target_mask_geometry": SMOKE_TARGET_MASK_GEOMETRY,
            "target_mask_shape": SMOKE_TARGET_MASK_SHAPE,
            "target_mask_rank": TARGET_MASK_RANK,
            "scientific_target_selection_used": False,
            "rank4_workaround_used": False,
            "mask_rank_contract": {
                "canonical_logits_rank": TARGET_LOGITS_RANK,
                "canonical_logits_shape_batch1": [1, 1, 512, 512],
                "smoke_mask_shape": SMOKE_TARGET_MASK_SHAPE,
                "smoke_mask_rank": TARGET_MASK_RANK,
                "scientific_mask_producer": "build_target_mask(persisted p_global >= 0.50)",
                "scientific_mask_shape": [512, 512],
                "scientific_mask_rank_compatible_with_canonical_helper": True,
                "repaired_defect": "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY",
                "repair_revision": REVISION,
            }}


# --------------------------------------------------------------------------- #
# v1.0d-local modes
# --------------------------------------------------------------------------- #
def mode_smoke() -> dict:
    """PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION - real implementation, rank-2 target mask."""
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
                          and ev["zero_denominator_policy"]["ZERO_ROUTER_GRAD_ATTRIBUTION"])
    return ev


def mode_gradcam() -> dict:
    """Frozen v1.0b display-subset resolution + binding to the REPAIRED per-sample Grad-CAM path."""
    gallery, allow = V0B.load_gallery_allowlist()
    display = V0B.resolve_display_subset(gallery)            # BEFORE any saliency exists
    return {"mode": "gradcam", "allowlist_size": len(allow), "display_subset": display,
            "display_subset_resolved_before_saliency": True,
            "raw_val_image_reads": V0B.COUNTERS["raw_val_image_reads"],
            "gradcam_path": gradcam_path_contract(),
            "target_scalar_impl": gradcam_target_scalar_rank_safe.__name__,
            "defective_v1_0b_target_path_used": False}


def mode_science() -> dict:
    """Family composition. Only the Grad-CAM component binding changes (implementation only)."""
    return {"mode": "science", "families": list(C.EVIDENCE_FAMILIES),
            "F8_regional_implemented": C.F8_REGIONAL_IMPLEMENTED,
            "component_binding": OrderedDict([
                ("I1_FILM_PARAMETER_INTERPRETABILITY",
                 {"implementation": "V0B.mode_film", "semantics_changed": False}),
                ("I2_SEGMENTATION_GRADIENT_SALIENCY",
                 {"implementation": gradcam_path_contract.__name__,
                  "target_scalar": gradcam_target_scalar_rank_safe.__name__,
                  "gradient_path": gradcam_gradient_enabled_rank_safe.__name__,
                  "semantics_changed": False,
                  "implementation_change": "IMPLEMENTATION_SHAPE_SAFETY_FIX_ONLY"}),
                ("I3_ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION",
                 {"implementation": "V0B (verbatim)", "semantics_changed": False}),
                ("I4_BENEFIT_ROUTER_FEATURE_ATTRIBUTION",
                 {"implementation": "V0B.mode_router", "semantics_changed": False}),
            ])}


MODE_DISPATCH = OrderedDict([
    ("smoke", mode_smoke),
    ("film", V0B.mode_film),          # frozen v1.0b, reused verbatim
    ("gradcam", mode_gradcam),        # v1.0d-local, bound to the repaired target scalar
    ("router", V0B.mode_router),      # frozen v1.0b, reused verbatim
    ("science", mode_science),        # v1.0d-local composition; Grad-CAM -> repaired helper
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
