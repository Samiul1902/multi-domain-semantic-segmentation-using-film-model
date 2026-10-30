#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 36 — Robustness & Image Perturbation Analysis
COMMON CONTRACT (frozen).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_0

This module defines the FROZEN perturbation registries, deterministic RNG rule,
metric bindings, and figure/table contracts for Phase36. It imports NO torch and
performs NO model/data execution at import time. It is pure configuration +
deterministic array math (numpy only, and numpy is imported lazily inside the
functions that need it so that registry/contract inspection stays model-free).

FORBIDDEN in this work order: model construction, checkpoint deserialization,
any forward, autograd, raw VAL image bytes, VAL GT bytes, ROUTER_HOLDOUT, TEST,
training, optimizer, scientific robustness outputs.
"""
from __future__ import annotations

import hashlib
from collections import OrderedDict

# --------------------------------------------------------------------------- #
# identity
# --------------------------------------------------------------------------- #
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase36_robustness_v1_0"
PHASE = 36

EVIDENCE_CLASS = "DEVELOPMENT_SET_SYNTHETIC_PERTURBATION_ROBUSTNESS_EVIDENCE"

CLAIM_BOUNDARY_NOT = [
    "clinical robustness",
    "external generalization",
    "adversarial robustness",
    "TEST performance",
    "deployment reliability proof",
    "causal explanation",
    "feature necessity",
    "feature sufficiency",
    "ground-truth localization accuracy",
]

FORBIDDEN_CLAIM_TERMS = [
    "causal", "necessity", "sufficiency", "clinical robustness",
    "adversarial robustness", "deployment reliability", "external generaliz",
]

# --------------------------------------------------------------------------- #
# gates
# --------------------------------------------------------------------------- #
GATE_ENV = "PHASE36_EXECUTE"           # science gate: must equal "1"
SMOKE_GATE_ENV = "PHASE36_SMOKE_EXECUTE"  # smoke gate: must equal "1"
MODES = ["smoke", "science"]

# --------------------------------------------------------------------------- #
# population — VAL808 ONLY
# --------------------------------------------------------------------------- #
POPULATION_NAME = "VAL808"
POPULATION_N = 808
VAL_MANIFEST = "manifests/phase4_v3/val.csv"
VAL_MANIFEST_SHA = "082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315"
DOMAINS = ["ISIC", "BUSI", "KVASIR", "KUB"]
DOMAIN_TASK_ID = OrderedDict([("ISIC", 0), ("BUSI", 1), ("KVASIR", 2), ("KUB", 3)])
DOMAIN_COUNTS = OrderedDict([("ISIC", 357), ("BUSI", 84), ("KVASIR", 87), ("KUB", 280)])

ROUTER_HOLDOUT_ROWS = 0
TEST_ROWS = 0

# The population that future Phase36 EXECUTION may read (raw VAL images + VAL GT).
# It MUST NOT read ROUTER_HOLDOUT or TEST.
MAY_READ = ["VAL808_RAW_IMAGES", "VAL808_GT"]
MUST_NOT_READ = ["ROUTER_HOLDOUT", "TEST"]

# KUB subgroup metadata is REPORTING_ONLY — never a segmentation class / task id.
KUB_REPORTING_ONLY = True
KUB_SUBGROUPS = ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"]
KUB_SUBGROUP_SOURCE = "manifests/phase4_v3/val.csv::category (KUB rows only)"
KUB_CATEGORY_COUNTS_EXPECTED = OrderedDict(
    [("Bladder_Stone", 144), ("Kidney_Stone", 112), ("Ureteric_Stone", 24)])

# --------------------------------------------------------------------------- #
# canonical thresholds (never altered by Phase36)
# --------------------------------------------------------------------------- #
T_SEGMENTATION_OUTPUT = 0.50
T_ROI_PROPOSAL = 0.30

# --------------------------------------------------------------------------- #
# clean reference authority (Phase27/29 frozen final-system clean VAL808)
# --------------------------------------------------------------------------- #
CLEAN_REFERENCE = OrderedDict([
    ("per_sample_scores", {
        "path": "reports/tables/phase27_val808_per_sample_scores.csv",
        "sha256": "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
        "n": 808,
        "provides": ["sample_id", "dataset", "task_id", "group_key",
                     "state_machine_branch", "router_decision",
                     "global_dice", "final_dice", "delta_dice",
                     "gt_foreground_pixels", "global_fg_pixels", "final_fg_pixels"],
    }),
    ("routing_state", {
        "path": "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv",
        "sha256": "df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6",
        "n": 808,
        "provides": ["sample_id", "domain", "task_id", "router_score",
                     "router_threshold", "selected", "safety_score",
                     "safety_accept", "final_source", "roi_available"],
    }),
])
CLEAN_REFERENCE_COMPLETE = True   # both per-sample Dice AND routing state exist
CLEAN_REFERENCE_GENERATION_FALLBACK = (
    "If the bound clean per-sample reference is unavailable at execution time, "
    "Phase36 execution generates exactly ONE clean reference pass under the "
    "frozen Phase36 source BEFORE any perturbation execution, and declares this "
    "prospectively now (never after perturbation results exist)."
)

# --------------------------------------------------------------------------- #
# component binding (frozen; NEVER re-trained / re-selected by Phase36)
# --------------------------------------------------------------------------- #
COMPONENTS = OrderedDict([
    ("G", {"class": "GlobalMedFiLM",
           "source_path": "src/models/film/global_medfilm.py",
           "source_sha256": "a04ff3e61b4d900ff47c2f390da4a999e73bd6047b28a19e41b05115e431d11f",
           "checkpoint_path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
           "checkpoint_sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
           "role": "GLOBAL_SEGMENTER"}),
    ("B_phi", {"class": "BARRBenefitRouterV1",
               "source_path": "scripts/analysis/train_phase25d_router.py",
               "source_sha256": "fc7c1bdf263ae4551dcb8f170d3203adb8540fbc189846265b74f6eca1541e91",
               "checkpoint_path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
               "checkpoint_sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
               "role": "BENEFIT_ROUTER"}),
    ("R_psi", {"class": "BARRRegionalRefinerV1",
               "source_path": "src/models/barr/regional_refiner.py",
               "source_sha256": "4fe0abde3ec3a183d930f676c4400b4d9ba778793ea64abf1755c5b8dabf947a",
               "checkpoint_path": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
               "checkpoint_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
               "role": "REGIONAL_REFINER"}),
    ("S_omega", {"class": "BARRPostSafetyV1",
                 "source_path": "scripts/analysis/phase25f_execution_common.py",
                 "source_sha256": "98cf958a377e2de30e0b67e63fd56bafea418b2b061a362ee7284e852012cd2e",
                 "checkpoint_path": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                 "checkpoint_sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
                 "role": "POST_SAFETY"}),
])

# A8/C9 frozen runtime policy (Phase26 canonical bundle)
A8_C9_POLICY = OrderedDict([
    ("variant", "A8/C9"),
    ("bundle", "artifacts/phase26_ra_medfilm_barr_bundle_v1_0"),
    ("bundle_manifest", "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json"),
    ("bundle_manifest_sha256",
     "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"),
    ("runtime_policy", "A8_C9"),
    ("nominal_budget", 0.25),
    ("score", "delta_hat_final - 0.25*C"),
    ("execution_iff", "score >= frozen_threshold"),
    ("canonical_router_threshold_binding",
     "reports/audits/phase26_canonical_router_threshold_binding_v1_0.json"),
    ("canonical_router_threshold_binding_sha256",
     "c49a1e53fd3e85ff793cc4ce41fd3f20210f33e6b1880ea0f55bd2b788fbbb37"),
    ("joint_retraining", False),
    ("threshold_modification", False),
])

# --------------------------------------------------------------------------- #
# frozen final-system state machine
# --------------------------------------------------------------------------- #
STATE_MACHINE = [
    "G", "B_phi", "SKIP_OR_EXECUTE",
    "R_psi_IF_EXECUTE", "S_omega",
    "EXECUTE_THEN_ACCEPT_OR_EXECUTE_THEN_REJECT", "FINAL_ROUTED_SEGMENTATION",
]
ROUTE_STATES = ["SKIP", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"]

# --------------------------------------------------------------------------- #
# IMAGE PERTURBATION REGISTRY (frozen; each generated from the ORIGINAL clean
# input independently — NO chaining)
# --------------------------------------------------------------------------- #
IMAGE_CONDITIONS = OrderedDict([
    ("CLEAN",              {"kind": "identity"}),
    ("BRIGHTNESS_NEG",     {"kind": "brightness", "delta": -0.10}),
    ("BRIGHTNESS_POS",     {"kind": "brightness", "delta": +0.10}),
    ("CONTRAST_LOW",       {"kind": "contrast", "factor": 0.80, "mean": "per_image_channel_spatial_mean"}),
    ("CONTRAST_HIGH",      {"kind": "contrast", "factor": 1.20, "mean": "per_image_channel_spatial_mean"}),
    ("GAMMA_LOW",          {"kind": "gamma", "gamma": 0.80}),
    ("GAMMA_HIGH",         {"kind": "gamma", "gamma": 1.20}),
    ("GAUSSIAN_NOISE_LOW", {"kind": "gaussian_noise", "sigma": 0.02,
                            "base_seeds": [42, 123, 3407]}),
    ("GAUSSIAN_NOISE_HIGH", {"kind": "gaussian_noise", "sigma": 0.05,
                             "base_seeds": [42, 123, 3407]}),
    ("GAUSSIAN_BLUR_LOW",  {"kind": "gaussian_blur", "sigma": 0.5,
                            "radius_rule": "ceil(3*sigma)", "padding": "reflect",
                            "separable": True, "learned": False}),
    ("GAUSSIAN_BLUR_HIGH", {"kind": "gaussian_blur", "sigma": 1.0,
                            "radius_rule": "ceil(3*sigma)", "padding": "reflect",
                            "separable": True, "learned": False}),
    ("RESOLUTION_075",     {"kind": "resolution", "factor": 0.75,
                            "working_resolution": 512, "restore": "bilinear",
                            "align_corners": False}),
    ("RESOLUTION_050",     {"kind": "resolution", "factor": 0.50,
                            "working_resolution": 512, "restore": "bilinear",
                            "align_corners": False}),
])
IMAGE_DOMAIN = "float32 [0,1]"
NO_CHAINING = True
NOISE_BASE_SEEDS = [42, 123, 3407]
NOISE_SEED_RULE = 'SHA256("phase36|gaussian_noise|<base_seed>|<sample_id>")'
NOISE_SEED_DERIVATION = (
    "deterministic_seed = int.from_bytes("
    "sha256(f'phase36|gaussian_noise|{base_seed}|{sample_id}'.encode()).digest()[:8],"
    "'big')  ->  Generator(PCG64(deterministic_seed)); one realization frozen per "
    "(sample, base_seed, severity)"
)
NOISE_GENERATION = "CPU-side float32; then clip to [0,1]"
FORBIDDEN_PERTURBATIONS = ["jpeg", "color_space_conversion", "rotation", "crop",
                           "random_augmentation", "adversarial_optimization"]

# --------------------------------------------------------------------------- #
# REGION / PROPOSAL PERTURBATION REGISTRY (frozen; from CLEAN image / CLEAN G)
# --------------------------------------------------------------------------- #
PROPOSAL_CONDITIONS = OrderedDict([
    ("PROPOSAL_CLEAN", {"kind": "identity"}),
    ("SHIFT_LEFT_10",  {"kind": "shift", "axis": "x", "direction": "left",  "magnitude_frac": 0.10}),
    ("SHIFT_RIGHT_10", {"kind": "shift", "axis": "x", "direction": "right", "magnitude_frac": 0.10}),
    ("SHIFT_UP_10",    {"kind": "shift", "axis": "y", "direction": "up",    "magnitude_frac": 0.10}),
    ("SHIFT_DOWN_10",  {"kind": "shift", "axis": "y", "direction": "down",  "magnitude_frac": 0.10}),
    ("SCALE_085",      {"kind": "scale", "side_factor": 0.85}),
    ("SCALE_115",      {"kind": "scale", "side_factor": 1.15}),
])
PROPOSAL_THRESHOLD = T_ROI_PROPOSAL   # canonical p_global >= 0.30 — NEVER altered
PROPOSAL_SHIFT_BASE = "0.10 x canonical_crop_side"
PROPOSAL_BOUNDS = "clamped_to_image_bounds_deterministic_center_adjustment"
EMPTY_PROPOSAL_HANDLING = "NOT_APPLICABLE_EMPTY_PROPOSAL"
NO_OUTCOME_DEPENDENT_REPLACEMENT = True

# --------------------------------------------------------------------------- #
# METRIC CONTRACT
# --------------------------------------------------------------------------- #
DICE_IMPL = "src.metrics.evaluation_metrics.dice (eps=1e-7)"
DICE_IMPL_PATH = "src/metrics/evaluation_metrics.py"
DICE_IMPL_SHA = "6c515f6f1a495315c79238292c385a082ae8347489130ad5bff34d74c4f181f6"
EMPTY_MASK_POLICY = "reports/audits/evaluation_empty_mask_policy.json"
EMPTY_MASK_POLICY_SHA = "16e702fd83b65e872acdab4cee06e0dd7c816f2659379ddc704c39c2efdac5f0"
GT_RULE = "full_field_gt: NEAREST 512 + centre pad, (arr>0)"

PRIMARY_METRIC = "paired_delta_Dice"
PRIMARY_METRIC_DEF = "Dice_perturbed - Dice_clean"
ALSO_RECORD = ["Dice_clean", "Dice_perturbed"]

# Secondary metrics are included IFF their exact implementation + empty-case
# handling can be bound BEFORE execution. Both are bound here from the canonical
# src/metrics/evaluation_metrics.py + the frozen empty-mask policy.
SECONDARY_METRICS = OrderedDict([
    ("iou", {"impl": "src.metrics.evaluation_metrics.iou (eps=1e-7)",
             "bound": True,
             "empty_policy": "frozen empty-mask policy"}),
    ("hd95", {"impl": "src.metrics.evaluation_metrics.hd95",
              "bound": True,
              "empty_policy": "NaN (invalid) on empty cases per frozen policy"}),
])

STATE_METRICS = [
    "prediction_consistency_Dice",
    "route_state_clean", "route_state_perturbed", "route_state_changed",
    "B_phi_execute_clean", "B_phi_execute_perturbed", "B_phi_decision_changed",
    "S_omega_state", "execution_rate", "accept_rate", "reject_rate",
    "proposal_valid", "proposal_crop_geometry",
]
PREDICTION_CONSISTENCY_DEF = "Dice(final_prediction_perturbed, final_prediction_clean)"

STRESS_FLAGS = [("delta_Dice <= -0.05", -0.05), ("delta_Dice <= -0.10", -0.10)]
STRESS_FLAGS_ARE_DESCRIPTIVE_ONLY = True
NO_NEW_PVALUES = True
NO_SIGNIFICANCE_CLAIMS = True

# noise summarization: per-seed first, then arithmetic mean across seeds.
NOISE_SEED_SUMMARY_RULE = "per_seed_then_arithmetic_mean_across_three_frozen_seeds"
BEST_SEED_SELECTION = False

# --------------------------------------------------------------------------- #
# worst-case definitions (prospective)
# --------------------------------------------------------------------------- #
WORST_IMAGE_DEF = ("worst_image_perturbation_delta_Dice = min paired_delta_Dice "
                   "over the FIXED image perturbation set (excludes proposal perturbations)")
WORST_PROPOSAL_DEF = ("worst_proposal_perturbation_delta_Dice = min paired_delta_Dice "
                      "over APPLICABLE fixed proposal perturbations")
NO_POST_HOC_SET_EXPANSION = True

# --------------------------------------------------------------------------- #
# FIGURE CONTRACT (F1-F7 -> R1-R5)
# --------------------------------------------------------------------------- #
FIGURES = OrderedDict([
    ("R1", "image-perturbation mean paired DeltaDice heatmap (domain x condition)"),
    ("R2", "severity curves for noise / blur / resolution degradation"),
    ("R3", "route-state-change / execution-rate heatmap"),
    ("R4", "proposal perturbation paired DeltaDice summary"),
    ("R5", "worst-case image/proposal DeltaDice distribution by domain"),
])
OUTCOME_SELECTED_GALLERY_REQUIRED = False
EXAMPLE_VIZ_MEMBERSHIP_FROZEN_BEFORE_OUTPUTS = True

# --------------------------------------------------------------------------- #
# TABLE CONTRACT
# --------------------------------------------------------------------------- #
TABLES = [
    "phase36_image_robustness_per_sample.csv",
    "phase36_image_robustness_by_domain_condition.csv",
    "phase36_noise_seed_summary.csv",
    "phase36_proposal_robustness_per_sample.csv",
    "phase36_proposal_robustness_by_domain_condition.csv",
    "phase36_route_stability_summary.csv",
    "phase36_worst_case_per_sample.csv",
    "phase36_worst_case_by_domain.csv",
    "phase36_kub_subgroup_robustness.csv",   # if metadata authority passes
]
PERTURBATION_REGISTRY_PERSISTED_SEPARATELY = True

# --------------------------------------------------------------------------- #
# execution counters required of future execution
# --------------------------------------------------------------------------- #
COUNTERS_REQUIRED = [
    "unique_raw_val_images", "unique_val_gt",
    "clean_g_forwards", "perturbed_g_forwards",
    "b_phi_forwards", "r_psi_forwards", "s_omega_forwards",
    "image_perturbation_instances", "proposal_perturbation_instances",
    "route_states", "metric_evaluations",
]
COUNTERS_FOREVER_ZERO = [
    "router_holdout_reads", "test_reads", "training", "optimizer_steps",
    "parameter_mutations",
]

# --------------------------------------------------------------------------- #
# deterministic perturbation primitives (numpy only; lazy import)
# --------------------------------------------------------------------------- #
def _np():
    import numpy as np
    return np


def _clip01(x):
    np = _np()
    return np.clip(x, 0.0, 1.0).astype(np.float32, copy=False)


def apply_identity(x):
    return _clip01(x)


def apply_brightness(x, delta: float):
    return _clip01(x + float(delta))


def apply_contrast(x, factor: float):
    np = _np()
    x = np.asarray(x, dtype=np.float32)
    mean = x.mean(axis=(-2, -1), keepdims=True)   # per-image per-channel spatial mean
    return _clip01((x - mean) * float(factor) + mean)


def apply_gamma(x, gamma: float):
    np = _np()
    return _clip01(np.power(np.clip(x, 0.0, 1.0), float(gamma)))


def derive_noise_seed(base_seed: int, sample_id: str) -> int:
    """Frozen rule: SHA256('phase36|gaussian_noise|<base_seed>|<sample_id>')."""
    msg = f"phase36|gaussian_noise|{int(base_seed)}|{sample_id}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(msg).digest()[:8], "big")


def apply_gaussian_noise(x, sigma: float, sample_id: str, base_seed: int):
    np = _np()
    seed = derive_noise_seed(base_seed, sample_id)
    rng = np.random.Generator(np.random.PCG64(seed))
    x = np.asarray(x, dtype=np.float32)
    noise = rng.standard_normal(size=x.shape, dtype=np.float32) * np.float32(sigma)
    return _clip01(x + noise.astype(np.float32))


def _gaussian_kernel1d(sigma: float):
    np = _np()
    radius = int(-(-(3.0 * float(sigma)) // 1))   # ceil(3*sigma)
    coords = np.arange(-radius, radius + 1, dtype=np.float64)
    k = np.exp(-(coords ** 2) / (2.0 * float(sigma) ** 2))
    k = k / k.sum()
    return k.astype(np.float32), radius


def apply_gaussian_blur(x, sigma: float):
    """Deterministic separable Gaussian blur; reflect padding; no learned filter."""
    np = _np()
    x = np.asarray(x, dtype=np.float32)
    k, radius = _gaussian_kernel1d(sigma)
    squeezed = x.ndim == 2
    if squeezed:
        x = x[None, ...]
    pad = np.pad(x, ((0, 0), (0, 0), (radius, radius)), mode="reflect")
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"),
                              2, pad)
    pad2 = np.pad(out, ((0, 0), (radius, radius), (0, 0)), mode="reflect")
    out = np.apply_along_axis(lambda m: np.convolve(m, k, mode="valid"),
                              1, pad2)
    out = out.astype(np.float32)
    if squeezed:
        out = out[0]
    return _clip01(out)


def apply_resolution(x, factor: float, working: int = 512):
    """Downsample to factor*working then bilinearly restore; align_corners=False."""
    np = _np()
    x = np.asarray(x, dtype=np.float32)
    lo = max(1, int(round(factor * working)))
    # nearest-free deterministic bilinear resize implemented by index interpolation
    def _resize(a, h, w):
        H, W = a.shape[-2], a.shape[-1]
        ys = (np.arange(h, dtype=np.float64) + 0.5) * (H / h) - 0.5
        xs = (np.arange(w, dtype=np.float64) + 0.5) * (W / w) - 0.5
        ys = np.clip(ys, 0, H - 1); xs = np.clip(xs, 0, W - 1)
        y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
        y1 = np.minimum(y0 + 1, H - 1); x1 = np.minimum(x0 + 1, W - 1)
        wy = (ys - y0).astype(np.float32)
        wx = (xs - x0).astype(np.float32)
        a = np.asarray(a, dtype=np.float32)
        # gather the four neighbours using advanced indexing on the last two axes
        top_l = a[..., y0[:, None], x0[None, :]]
        top_r = a[..., y0[:, None], x1[None, :]]
        bot_l = a[..., y1[:, None], x0[None, :]]
        bot_r = a[..., y1[:, None], x1[None, :]]
        wyb = wy[:, None]; wxb = wx[None, :]
        top = top_l * (1 - wxb) + top_r * wxb
        bot = bot_l * (1 - wxb) + bot_r * wxb
        return (top * (1 - wyb) + bot * wyb).astype(np.float32)
    down = _resize(x, lo, lo)
    up = _resize(down, working, working)
    return _clip01(up)


def apply_image_condition(x, condition_id: str, sample_id: str,
                          base_seed: int | None = None):
    """Dispatch a frozen image condition. NEVER chains perturbations."""
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
            raise ValueError("gaussian_noise requires a base_seed")
        return apply_gaussian_noise(x, spec["sigma"], sample_id, base_seed)
    if kind == "gaussian_blur":
        return apply_gaussian_blur(x, spec["sigma"])
    if kind == "resolution":
        return apply_resolution(x, spec["factor"], spec["working_resolution"])
    raise KeyError(f"unknown image condition kind: {kind}")


# --------------------------------------------------------------------------- #
# proposal geometry primitives (frozen)
# --------------------------------------------------------------------------- #
def proposal_geometry(y1, y2, x1, x2, H, W):
    np = _np()
    y1 = int(np.clip(y1, 0, H - 1)); y2 = int(np.clip(y2, 0, H))
    x1 = int(np.clip(x1, 0, W - 1)); x2 = int(np.clip(x2, 0, W))
    if y2 <= y1: y2 = min(H, y1 + 1)
    if x2 <= x1: x2 = min(W, x1 + 1)
    side = max(y2 - y1, x2 - x1)
    return {"y1": y1, "y2": y2, "x1": x1, "x2": x2,
            "crop_side": int(side), "center_y": (y1 + y2) / 2.0,
            "center_x": (x1 + x2) / 2.0}


def proposal_shift(geom, axis: str, direction: str, magnitude_frac: float,
                   H: int, W: int):
    """Shift by magnitude_frac * canonical crop side; clamp inside image bounds."""
    np = _np()
    delta = int(round(float(magnitude_frac) * geom["crop_side"]))
    sign = {"left": -1, "up": -1, "right": +1, "down": +1}[direction]
    cy, cx = geom["center_y"], geom["center_x"]
    if axis == "x":
        cx += sign * delta
    else:
        cy += sign * delta
    half = geom["crop_side"] / 2.0
    cy = float(np.clip(cy, half, H - half))
    cx = float(np.clip(cx, half, W - half))
    c = int(round(half))
    return proposal_geometry(int(round(cy - c)), int(round(cy - c)) + 2 * c,
                             int(round(cx - c)), int(round(cx - c)) + 2 * c, H, W)


def proposal_scale(geom, side_factor: float, H: int, W: int):
    np = _np()
    new_side = int(round(float(side_factor) * geom["crop_side"]))
    new_side = max(1, min(new_side, min(H, W)))
    cy, cx = geom["center_y"], geom["center_x"]
    half = new_side / 2.0
    cy = float(np.clip(cy, half, H - half))
    cx = float(np.clip(cx, half, W - half))
    c = int(round(half))
    return proposal_geometry(int(round(cy - c)), int(round(cy - c)) + 2 * c,
                             int(round(cx - c)), int(round(cx - c)) + 2 * c, H, W)


def apply_proposal_condition(geom, condition_id: str, H: int, W: int):
    spec = PROPOSAL_CONDITIONS[condition_id]
    kind = spec["kind"]
    if kind == "identity":
        return dict(geom)
    if kind == "shift":
        return proposal_shift(geom, spec["axis"], spec["direction"],
                              spec["magnitude_frac"], H, W)
    if kind == "scale":
        return proposal_scale(geom, spec["side_factor"], H, W)
    raise KeyError(f"unknown proposal condition kind: {kind}")


# --------------------------------------------------------------------------- #
# registry integrity helpers (used by unit tests / preflight)
# --------------------------------------------------------------------------- #
def image_condition_ids():
    return list(IMAGE_CONDITIONS.keys())


def proposal_condition_ids():
    return list(PROPOSAL_CONDITIONS.keys())


def registries_unique() -> bool:
    return (len(IMAGE_CONDITIONS) == len(set(IMAGE_CONDITIONS))
            and len(PROPOSAL_CONDITIONS) == len(set(PROPOSAL_CONDITIONS)))


def assert_no_chaining() -> bool:
    """No perturbation accepts another perturbation's output as its own spec."""
    for cid, spec in IMAGE_CONDITIONS.items():
        if "chain" in spec or "on" in spec:
            return False
    for cid, spec in PROPOSAL_CONDITIONS.items():
        if "chain" in spec or "on" in spec:
            return False
    return True


def kube_reporting_only_ok() -> bool:
    return (KUB_REPORTING_ONLY
            and set(KUB_SUBGROUPS) == {"Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"}
            and all(isinstance(v, int) for v in DOMAIN_TASK_ID.values()))


CONTRACT_LOCKED = True
