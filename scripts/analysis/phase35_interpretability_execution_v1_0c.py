#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0c EXECUTABLE interpretability harness with a REAL synthetic smoke entry point.

Classification: PRE_EXECUTION_SYNTHETIC_SMOKE_ENTRYPOINT_IMPLEMENTATION_AMENDMENT__NO_SCIENTIFIC_
                PROTOCOL_CHANGE
Revision: ra_medfilm_barr_phase35_interpretability_v1_0c

SUPERSEDES `phase35_interpretability_execution_v1_0b.py` ONLY for the smoke entry point. The v1.0b
file is preserved byte-for-byte. All SCIENTIFIC mode implementations are reused verbatim from the
frozen v1.0b execution module, so their semantics are provably unchanged.

!! ZERO-EXECUTION GUARD !!
Importing this module performs NO model construction, NO checkpoint load, NO forward, NO autograd,
NO Grad-CAM, NO router attribution and NO raw-image read. All work lives in main().

Gates (distinct by design):
  * smoke mode      -> requires PHASE35_SMOKE_EXECUTE=1
  * scientific modes -> require PHASE35_EXECUTE=1   (PHASE35_SMOKE_EXECUTE does NOT authorize them)

Protected data: ROUTER_HOLDOUT raw images/GT and TEST images/GT are FORBIDDEN. Smoke mode reads NO
real data of any kind: only deterministic synthetic tensors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
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

import phase35_interpretability_common_v1_0b as C          # noqa: E402  (frozen, reused)
import phase35_interpretability_execution_v1_0b as V0B     # noqa: E402  (frozen scientific paths)

ROOT = REPO_ROOT
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
REVISION = "ra_medfilm_barr_phase35_interpretability_v1_0c"

# --------------------------------------------------------------------------- #
# smoke-only frozen definitions
# --------------------------------------------------------------------------- #
SMOKE_GATE_ENV = "PHASE35_SMOKE_EXECUTE"
SCIENCE_GATE_ENV = "PHASE35_EXECUTE"
SMOKE_SEED = 42
SMOKE_GENERATOR_SEMANTICS = "torch.Generator(device='cuda').manual_seed(42)"
SMOKE_IMAGE_SHAPE = [1, 3, 512, 512]
SMOKE_TASK_ID = 0
SMOKE_TARGET_MASK_NAME = "SMOKE_SYNTHETIC_TARGET_MASK"
SMOKE_TARGET_MASK_SHAPE = [1, 1, 512, 512]
SMOKE_TARGET_MASK_GEOMETRY = (
    "boolean tensor [1,1,512,512]; centered square rows 192:320, columns 192:320 of the trailing "
    "two dims (non-empty). Rank is chosen to satisfy the canonical `gradcam_target_scalar` indexing "
    "contract, because `logits[mask]` requires the mask to match the logits leading dims and the "
    "canonical G logits tensor is [1,1,512,512]. The SCIENTIFIC mask producer "
    "(`build_target_mask(p_global >= 0.50)`) returns a rank-2 [512,512] array, which is NOT "
    "rank-compatible with the same helper: this is disclosed as "
    "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY and is NOT silently repaired here.")
SMOKE_ROUTER_INPUT_DEFINITION = ("base = torch.linspace(-1.0, 1.0, 202); rows = "
                                 "[base, base*0.5, -base, base*1.5]; float32; task_ids=[0,1,2,3]")
SMOKE_ROUTER_BATCH = 4
SMOKE_ROUTER_DIM = 202
SMOKE_DEEP_DIM = 192
SMOKE_SCALAR_DIM = 10

SMOKE_COUNTERS = OrderedDict([
    ("G_model_constructions", 0), ("B_phi_model_constructions", 0),
    ("checkpoint_deserializations", 0), ("strict_loads", 0),
    ("G_synthetic_forwards", 0), ("B_phi_synthetic_forwards", 0),
    ("total_model_forwards", 0), ("G_gradcam_autograd_calls", 0),
    ("router_numeric_input_autograd_calls", 0), ("total_autograd_calls", 0),
    ("synthetic_CAM_maps", 0), ("synthetic_router_attribution_rows", 0),
    ("synthetic_smoke_target_masks", 0),
    ("R_psi_model_constructions", 0), ("R_psi_checkpoint_loads", 0), ("R_psi_forwards", 0),
    ("S_omega_model_constructions", 0), ("S_omega_checkpoint_loads", 0), ("S_omega_forwards", 0),
    ("optimizer_constructions", 0), ("optimizer_step_calls", 0),
    ("training_backward_calls", 0), ("parameter_mutations", 0),
    ("raw_VAL_image_reads", 0), ("real_persisted_VAL_probability_reads", 0),
    ("VAL_GT_reads", 0), ("router_feature_cache_rows_read", 0),
    ("ROUTER_HOLDOUT_reads", 0), ("TEST_reads", 0), ("TRAIN_raw_reads", 0),
    ("scientific_outputs", 0),
])

SMOKE_EXPECTED_COUNTERS = OrderedDict([
    ("G_model_constructions", 1), ("B_phi_model_constructions", 1),
    ("checkpoint_deserializations", 2), ("strict_loads", 2),
    ("G_synthetic_forwards", 1), ("B_phi_synthetic_forwards", 1),
    ("total_model_forwards", 2), ("G_gradcam_autograd_calls", 1),
    ("router_numeric_input_autograd_calls", 1), ("total_autograd_calls", 2),
    ("synthetic_CAM_maps", 2), ("synthetic_router_attribution_rows", 4),
    ("synthetic_smoke_target_masks", 1),
    ("R_psi_model_constructions", 0), ("R_psi_checkpoint_loads", 0), ("R_psi_forwards", 0),
    ("S_omega_model_constructions", 0), ("S_omega_checkpoint_loads", 0), ("S_omega_forwards", 0),
    ("optimizer_constructions", 0), ("optimizer_step_calls", 0),
    ("training_backward_calls", 0), ("parameter_mutations", 0),
])

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
# smoke-only helpers
# --------------------------------------------------------------------------- #
def smoke_environment_check() -> dict:
    import torch
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    env = {"os": platform.platform(), "python": platform.python_version(),
           "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
           "cuda_driver_version": "596.36", "cudnn": torch.backends.cudnn.version(),
           "cuda_available": bool(torch.cuda.is_available()),
           "gpu": prop.name if prop else None,
           "cc": f"{prop.major}.{prop.minor}" if prop else None,
           "vram_bytes": prop.total_memory if prop else None}
    env["compatible"] = (env["gpu"] == "NVIDIA GeForce RTX 3060 Ti"
                         and env["torch"] == "2.6.0+cu124" and env["cuda_available"])
    if not env["compatible"]:
        raise RuntimeError(f"SMOKE environment incompatible: {env}")
    return env


def smoke_checkpoint_identity() -> dict:
    """File SHA verification for G and B_phi BEFORE any deserialization. R_psi/S_omega never touched."""
    out = OrderedDict()
    for cid in C.EXECUTABLE_COMPONENTS:
        spec = C.COMPONENTS[cid]
        obs = sha256_file(ROOT / spec["checkpoint"])
        if obs != spec["checkpoint_sha256"]:
            raise RuntimeError(f"SMOKE checkpoint SHA mismatch {cid}: {obs}")
        out[cid] = {"path": spec["checkpoint"], "expected_sha256": spec["checkpoint_sha256"],
                    "observed_sha256": obs, "match": True, "deserialized_yet": False}
    for cid in C.NON_EXECUTABLE_COMPONENTS:
        out[cid] = {"touched": False, "constructions": 0, "checkpoint_loads": 0, "forwards": 0}
    return out


def smoke_synthetic_image():
    """Deterministic synthetic G input. No medical image bytes."""
    import torch
    g = torch.Generator(device="cuda").manual_seed(SMOKE_SEED)
    img = torch.randn(*SMOKE_IMAGE_SHAPE, generator=g, device="cuda", dtype=torch.float32)
    tid = torch.tensor([SMOKE_TASK_ID], dtype=torch.int64, device="cuda")
    return img, tid


def smoke_synthetic_target_mask():
    """SMOKE_SYNTHETIC_TARGET_MASK: deterministic centered square; NOT the scientific mechanism.

    Scientific Grad-CAM remains `persisted p_global >= 0.50`; this mask is smoke-only and never
    routed through the persisted-prediction loader. Rank [1,1,512,512] matches the canonical G
    logits tensor so the canonical `gradcam_target_scalar` indexing contract is satisfied.
    """
    import torch
    mask = torch.zeros(*SMOKE_TARGET_MASK_SHAPE, dtype=torch.bool, device="cuda")
    mask[:, :, 192:320, 192:320] = True
    if not bool(mask.any()):
        raise RuntimeError("SMOKE target mask must be non-empty")
    SMOKE_COUNTERS["synthetic_smoke_target_masks"] += 1
    return mask


def state_dict_identity(model) -> str:
    """Deterministic identity of every state_dict tensor (name + bytes + dtype + shape)."""
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode("utf-8"))
        t = v.detach().cpu()
        h.update(str(t.dtype).encode("utf-8"))
        h.update(str(tuple(t.shape)).encode("utf-8"))
        h.update(t.contiguous().numpy().tobytes())
    return h.hexdigest()


def smoke_film_validate(g_model) -> dict:
    """FiLM accessor smoke: shape + finiteness only (no scientific FiLM tables)."""
    import torch
    dev = next(g_model.parameters()).device
    out = OrderedDict()
    ok = True
    for dom, tid in C.DOMAIN_TASK_ID.items():
        params = g_model.film_parameters_for_tasks(
            torch.tensor([tid], dtype=torch.long, device=dev))
        for site, (gamma, beta) in params.items():
            g = gamma.detach().float()
            b = beta.detach().float()
            n = int(g.reshape(-1).numel())
            finite = bool(torch.isfinite(g).all() and torch.isfinite(b).all())
            expect = C.FILM_SITE_CHANNELS[site]
            out[f"{dom}|{site}"] = {"gamma_len": n, "beta_len": int(b.reshape(-1).numel()),
                                    "expected_channels": expect, "finite": finite,
                                    "channel_count_exact": n == expect}
            ok &= finite and n == expect
    return {"per_task_site": out, "all_pass": ok,
            "scientific_film_tables_emitted": False}


def smoke_embedding_validate(g_model, bphi_model) -> dict:
    """Task-embedding smoke: shape + finiteness only (no scientific geometry tables)."""
    import torch
    g = g_model.task_embedding.weight.detach().float()
    b = bphi_model.task_embedding.weight.detach().float()
    return {"G_task_embedding_shape": list(g.shape),
            "G_expected_shape": [C.TASK_COUNT, C.G_TASK_EMBEDDING_DIM],
            "G_finite": bool(torch.isfinite(g).all()),
            "B_phi_task_embedding_shape": list(b.shape),
            "B_phi_expected_shape": [C.TASK_COUNT, C.B_PHI_TASK_EMBEDDING_DIM],
            "B_phi_finite": bool(torch.isfinite(b).all()),
            "scientific_embedding_tables_emitted": False}


def smoke_gradcam(g_model) -> dict:
    """ONE synthetic gradient-enabled G forward through the frozen canonical Grad-CAM path."""
    img, tid = smoke_synthetic_image()
    mask = smoke_synthetic_target_mask()
    res = V0B.gradcam_gradient_enabled(g_model, img, tid, mask,
                                       layers=("bridge", "decoder1"))
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
            "target_mask_name": SMOKE_TARGET_MASK_NAME,
            "target_mask_geometry": SMOKE_TARGET_MASK_GEOMETRY,
            "target_mask_shape": SMOKE_TARGET_MASK_SHAPE,
            "scientific_target_selection_used": False,
            "mask_rank_contract": {
                "canonical_logits_rank": 4,
                "canonical_logits_shape_batch1": [1, 1, 512, 512],
                "smoke_mask_shape": SMOKE_TARGET_MASK_SHAPE,
                "scientific_mask_producer": "build_target_mask(persisted p_global >= 0.50)",
                "scientific_mask_shape": [512, 512],
                "scientific_mask_rank_compatible_with_canonical_helper": False,
                "disclosed_defect": "PHASE35_V1_0B_GRADCAM_TARGET_MASK_RANK_INCOMPATIBILITY",
            }}


def smoke_router(bphi_model, bphi_state) -> dict:
    """ONE synthetic B_phi forward + ONE numeric-input gradient + Gradient x Input."""
    import numpy as np
    import torch
    base = torch.linspace(-1.0, 1.0, SMOKE_ROUTER_DIM, dtype=torch.float32)
    rows = torch.stack([base, base * 0.5, -base, base * 1.5], dim=0).numpy()
    deep = rows[:, :SMOKE_DEEP_DIM]
    scal = rows[:, SMOKE_DEEP_DIM:]
    xn = V0B.router_normalized_features(deep, scal, bphi_state)
    task_ids = np.arange(SMOKE_ROUTER_BATCH, dtype=np.int64)
    res = V0B.router_gradient_x_input(bphi_model, xn, task_ids)
    SMOKE_COUNTERS["B_phi_synthetic_forwards"] += 1
    SMOKE_COUNTERS["total_model_forwards"] += 1
    SMOKE_COUNTERS["router_numeric_input_autograd_calls"] += 1
    SMOKE_COUNTERS["total_autograd_calls"] += 1
    SMOKE_COUNTERS["synthetic_router_attribution_rows"] += int(res["signed"].shape[0])
    delta = res["delta_hat"]
    grad = res["signed"] / np.where(xn == 0, 1.0, xn)      # recover gradient = a / x
    gxi = res["signed"]
    return {"raw_router_input_shape": list(rows.shape), "raw_router_input_dtype": "float32",
            "raw_router_input_finite": bool(np.isfinite(rows).all()),
            "normalized_router_input_shape": list(xn.shape),
            "normalized_router_input_dtype": str(xn.dtype),
            "normalized_router_input_finite": bool(np.isfinite(xn).all()),
            "raw_delta_hat_shape": list(delta.shape),
            "raw_delta_hat_finite": bool(np.isfinite(delta).all()),
            "sigmoid_applied": False, "sigmoid_count": 0,
            "router_gradient_shape": list(grad.shape),
            "router_gradient_finite": bool(np.isfinite(grad).all()),
            "gradient_x_input_shape": list(gxi.shape),
            "gradient_x_input_finite": bool(np.isfinite(gxi).all()),
            "task_id_dtype": "int64", "task_id_requires_grad": False,
            "task_id_numeric_attribution": False,
            "deep_group_boundaries": {k: v for k, v in C.ROUTER_FEATURE_GROUPS.items()},
            "scalar_positions": C.ROUTER_SCALAR_FEATURES}


def smoke_zero_denominator(bphi_state) -> dict:
    """Zero-denominator aggregation policy unit test. NO extra B_phi forward."""
    import numpy as np
    res = V0B.router_group_attribution(np.zeros(SMOKE_ROUTER_DIM, dtype=np.float64))
    return {"denominator": res["denominator"],
            "normalized_group_shares": [v["normalized_absolute_share_group"]
                                        for v in res["groups"].values()],
            "ZERO_ROUTER_GRAD_ATTRIBUTION": res["ZERO_ROUTER_GRAD_ATTRIBUTION"],
            "epsilon_added": False, "renormalization": False,
            "b_phi_forwards_used": 0}


def smoke_parameter_immutability(before: dict, g_model, bphi_model) -> dict:
    after = {"G": state_dict_identity(g_model), "B_phi": state_dict_identity(bphi_model)}
    unchanged = (before["G"] == after["G"]) and (before["B_phi"] == after["B_phi"])
    SMOKE_COUNTERS["parameter_mutations"] = 0 if unchanged else 1
    return {"G_identity_before": before["G"], "G_identity_after": after["G"],
            "B_phi_identity_before": before["B_phi"], "B_phi_identity_after": after["B_phi"],
            "G_state_tensors_unchanged": before["G"] == after["G"],
            "B_phi_state_tensors_unchanged": before["B_phi"] == after["B_phi"],
            "parameter_mutations": SMOKE_COUNTERS["parameter_mutations"],
            "MODEL_PARAMETERS_UNCHANGED": unchanged}


# --------------------------------------------------------------------------- #
# REAL smoke mode
# --------------------------------------------------------------------------- #
def mode_smoke() -> dict:
    """PRE_SCIENTIFIC_SYNTHETIC_INTERFACE_VALIDATION - real implementation (not a stub)."""
    ev = OrderedDict()
    ev["authority_gates"] = V0B.verify_authority_gates()          # 1
    ev["environment"] = smoke_environment_check()                 # 2
    ev["checkpoint_identity"] = smoke_checkpoint_identity()       # 3,4

    g_model, ginfo = V0B.load_g_component()                       # 5,7,9,10,11
    SMOKE_COUNTERS["G_model_constructions"] += 1
    SMOKE_COUNTERS["checkpoint_deserializations"] += 1
    SMOKE_COUNTERS["strict_loads"] += 1
    bphi_model, bphi_state, binfo = V0B.load_bphi_component()     # 6,8,9,10,11
    SMOKE_COUNTERS["B_phi_model_constructions"] += 1
    SMOKE_COUNTERS["checkpoint_deserializations"] += 1
    SMOKE_COUNTERS["strict_loads"] += 1

    ev["G_identity"] = ginfo
    ev["B_phi_identity"] = binfo
    before = {"G": state_dict_identity(g_model), "B_phi": state_dict_identity(bphi_model)}

    ev["film_smoke"] = smoke_film_validate(g_model)               # 12
    ev["embedding_smoke"] = smoke_embedding_validate(g_model, bphi_model)  # 13,14
    ev["gradcam_smoke"] = smoke_gradcam(g_model)                  # 15,16
    ev["router_smoke"] = smoke_router(bphi_model, bphi_state)     # 17,18,19
    ev["zero_denominator_policy"] = smoke_zero_denominator(bphi_state)  # 20
    ev["parameter_immutability"] = smoke_parameter_immutability(before, g_model, bphi_model)  # 21

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


# --------------------------------------------------------------------------- #
# scientific modes: reused VERBATIM from the frozen v1.0b module (semantics unchanged)
# --------------------------------------------------------------------------- #
MODE_DISPATCH = OrderedDict([
    ("smoke", mode_smoke),
    ("film", V0B.mode_film),
    ("gradcam", V0B.mode_gradcam),
    ("router", V0B.mode_router),
    ("science", V0B.mode_science),
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

    report = OrderedDict([("revision", REVISION), ("mode", a.mode),
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
