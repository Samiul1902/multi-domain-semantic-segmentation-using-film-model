#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.1 — robustness common (ADDITIVE layer over the frozen v1.0 common).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_1

This module NEVER modifies v1.0. It RE-EXPORTS every frozen v1.0 registry unchanged
(image/proposal registries, severities, base seeds, population, thresholds, A8/C9,
figures, tables, counters, claim boundary) and OVERRIDES exactly one implementation:

    derive_noise_seed_v1_1  -- the v1.1 prospectively-frozen seed conversion
                               int(sha256_hexdigest()[:8], 16)  (32-bit, FIRST 8 HEX CHARS)

No torch import. No model. No file I/O on medical data.
"""
from __future__ import annotations

import hashlib

import numpy as np

import scripts.analysis.phase36_robustness_common_v1_0 as V0

# --------------------------------------------------------------------------- #
# Re-export the frozen v1.0 contract surface verbatim
# --------------------------------------------------------------------------- #
EVIDENCE_CLASS = V0.EVIDENCE_CLASS
GATE_ENV = V0.GATE_ENV
SMOKE_GATE_ENV = V0.SMOKE_GATE_ENV
MODES = V0.MODES

POPULATION_NAME = V0.POPULATION_NAME
POPULATION_N = V0.POPULATION_N
VAL_MANIFEST = V0.VAL_MANIFEST
VAL_MANIFEST_SHA = V0.VAL_MANIFEST_SHA

CLEAN_REFERENCE = V0.CLEAN_REFERENCE
COMPONENTS = V0.COMPONENTS
A8_C9_POLICY = V0.A8_C9_POLICY
STATE_MACHINE = V0.STATE_MACHINE

IMAGE_CONDITIONS = V0.IMAGE_CONDITIONS
IMAGE_DOMAIN = V0.IMAGE_DOMAIN
NO_CHAINING = V0.NO_CHAINING
NOISE_BASE_SEEDS = V0.NOISE_BASE_SEEDS
NOISE_GENERATION = V0.NOISE_GENERATION
FORBIDDEN_PERTURBATIONS = V0.FORBIDDEN_PERTURBATIONS

PROPOSAL_CONDITIONS = V0.PROPOSAL_CONDITIONS
PROPOSAL_THRESHOLD = V0.PROPOSAL_THRESHOLD
PROPOSAL_SHIFT_BASE = V0.PROPOSAL_SHIFT_BASE
PROPOSAL_BOUNDS = V0.PROPOSAL_BOUNDS
EMPTY_PROPOSAL_HANDLING = V0.EMPTY_PROPOSAL_HANDLING
NO_OUTCOME_DEPENDENT_REPLACEMENT = V0.NO_OUTCOME_DEPENDENT_REPLACEMENT

FIGURES = V0.FIGURES
TABLES = V0.TABLES
COUNTERS_REQUIRED = V0.COUNTERS_REQUIRED
COUNTERS_FOREVER_ZERO = V0.COUNTERS_FOREVER_ZERO

apply_identity = V0.apply_identity
apply_brightness = V0.apply_brightness
apply_contrast = V0.apply_contrast
apply_gamma = V0.apply_gamma
apply_gaussian_blur = V0.apply_gaussian_blur
apply_resolution = V0.apply_resolution
proposal_geometry = V0.proposal_geometry
proposal_shift = V0.proposal_shift
proposal_scale = V0.proposal_scale
apply_proposal_condition = V0.apply_proposal_condition
image_condition_ids = V0.image_condition_ids
proposal_condition_ids = V0.proposal_condition_ids
registries_unique = V0.registries_unique
assert_no_chaining = V0.assert_no_chaining
kube_reporting_only_ok = V0.kube_reporting_only_ok

# --------------------------------------------------------------------------- #
# v1.1 PROSPECTIVE SEED CONVERSION (supersedes v1.0 for all v1.1 execution)
# --------------------------------------------------------------------------- #
NOISE_SEED_RULE_V1_1 = 'SHA256("phase36|gaussian_noise|<base_seed>|<sample_id>")[:8]'
NOISE_SEED_DERIVATION_V1_1 = (
    "seed_text = f'phase36|gaussian_noise|{base_seed}|{sample_id}'; "
    "digest_hex = sha256(seed_text.encode('utf-8')).hexdigest(); "
    "seed_uint32 = int(digest_hex[:8], 16); "
    "rng = numpy.random.Generator(numpy.random.PCG64(seed_uint32))"
)
HEX_CHARS = 8
SEED_UINT32_MIN = 0
SEED_UINT32_MAX = 0xFFFFFFFF


def derive_noise_seed(base_seed: int, sample_id: str) -> int:
    """v1.1 frozen rule: FIRST EIGHT HEX CHARACTERS of the SHA-256 hexdigest, base 16."""
    seed_text = f"phase36|gaussian_noise|{int(base_seed)}|{sample_id}"
    digest_hex = hashlib.sha256(seed_text.encode("utf-8")).hexdigest()
    return int(digest_hex[:HEX_CHARS], 16)


def seed_conversion_audit() -> dict:
    """Prove the v1.1 conversion differs from v1.0 in a disclosed, deterministic way."""
    msg = f"phase36|gaussian_noise|42|SYNTH_PHASE36_TASK0"
    d = hashlib.sha256(msg.encode("utf-8")).digest()
    v1_1 = int(d.hex()[:HEX_CHARS], 16)
    v1_0 = int.from_bytes(d[:8], "big")
    return {
        "seed_text": msg,
        "v1_1_hex_prefix": d.hex()[:HEX_CHARS],
        "v1_1_seed": v1_1,
        "v1_0_seed_8_bytes_big": v1_0,
        "rules_differ": bool(v1_1 != v1_0),
        "v1_1_in_uint32_range": bool(SEED_UINT32_MIN <= v1_1 <= SEED_UINT32_MAX),
    }


def apply_gaussian_noise(x, sigma: float, sample_id: str, base_seed: int):
    """v1.1 noise: v1.1 seed conversion -> PCG64 -> float32 standard normal * sigma."""
    seed = derive_noise_seed(base_seed, sample_id)
    rng = np.random.Generator(np.random.PCG64(seed))
    x = np.asarray(x, dtype=np.float32)
    noise = rng.standard_normal(size=x.shape, dtype=np.float32) * np.float32(sigma)
    y = x + noise.astype(np.float32)
    return np.clip(y, 0.0, 1.0).astype(np.float32)


def apply_image_condition(x, condition_id: str, sample_id: str = "SYNTH",
                          base_seed=None):
    """v1.1 image condition dispatcher (mirrors v1.0 dispatch, v1.1 noise)."""
    spec = IMAGE_CONDITIONS[condition_id]
    kind = spec["kind"]
    if kind == "identity":
        return apply_identity(x)
    if kind == "brightness":
        return apply_brightness(x, spec["delta"])
    if kind == "contrast":
        return apply_contrast(x, spec["factor"])
    if kind == "gamma":
        return apply_gamma(x, spec["gamma"])
    if kind == "gaussian_noise":
        if base_seed is None:
            raise ValueError("gaussian noise requires a base_seed")
        return apply_gaussian_noise(x, spec["sigma"], sample_id, base_seed)
    if kind == "gaussian_blur":
        return apply_gaussian_blur(x, spec["sigma"])
    if kind == "resolution":
        return apply_resolution(x, spec["factor"], spec["working_resolution"])
    raise KeyError(condition_id)


# --------------------------------------------------------------------------- #
# v1.1 semantic contract flags (§H)
# --------------------------------------------------------------------------- #
PROPOSAL_CONTRACT_V1_1 = {
    "proposal_perturbation_changes_router_input":
        "TRUE_WHEN_CANONICAL_202D_EXTRACTOR_HAS_GEOMETRY_DEPENDENT_TERMS",
    "proposal_perturbation_changes_router_input_resolved": True,
    "B_phi_decision_recomputed": True,
    "R_psi_crop_uses_perturbed_geometry": True,
    "S_omega_recomputed_if_execute": True,
    "G_recomputed_for_proposal_perturbation": False,
    "geometry_dependent_dims": 98,
    "global_only_dims": 104,
    "extractor_roi_fields": ["clip_x1", "clip_y1", "clip_x2", "clip_y2", "crop_side_pixels"],
}

CLEAN_MASK_AUTHORITY_V1_1 = {
    "mask_type": "binary",
    "source": "frozen CLEAN execution path inside the same Phase36 science run",
    "prohibited_reconstruction_inputs": [
        "final_dice", "foreground_pixel_count", "router_decision",
        "final_source", "any scalar Phase27/29 field"],
}

CLEAN_EQUIVALENCE_GATE_V1_1 = {
    "sample_id_population": POPULATION_N,
    "task_domain_identity_exact": True,
    "routing_compatibility_required": True,
    "final_dice_comparator": "np.isclose(generated, bound, atol=1e-7, rtol=0)",
    "atol": 1e-7,
    "rtol": 0,
    "require_all_pass": True,
    "stop_before_perturbation_on_failure": True,
}

HD95_SUMMARY_RULE_V1_1 = {
    "n_total": True, "n_finite": True, "n_nan": True,
    "mean": "over finite values only", "median": "over finite values only",
    "nan_substitution": "NEVER (no 0, no infinity)",
}

STUB_MARKERS = ["NotImplementedError", "raise RuntimeError", "TODO", "FIXME", "raise NotImplemented"]
