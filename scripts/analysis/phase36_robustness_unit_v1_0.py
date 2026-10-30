#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 36 — MODEL-FREE UNIT TESTS for the perturbation & contract layer.

CPU only. NO torch model construction, NO checkpoint load, NO forward, NO data
access beyond a synthetic in-memory array. Emits
reports/audits/phase36_robustness_unit_v1_0.json.

Run: .venv/Scripts/python.exe scripts/analysis/phase36_robustness_unit_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase36_robustness_common_v1_0 as C  # noqa: E402

AUD = ROOT / "reports" / "audits"
RESULTS = []


def check(cid: str, desc: str, ok: bool, detail: str = "") -> None:
    RESULTS.append({"id": cid, "desc": desc, "pass": bool(ok), "detail": detail})


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    rng = np.random.default_rng(20261005)
    x = rng.random((4, 32, 32), dtype=np.float32)   # synthetic [0,1] float32

    # 01 identity
    out = C.apply_identity(x)
    check("01", "identity perturbation is exact and float32",
          np.array_equal(out, x.astype(np.float32)) and out.dtype == np.float32)

    # 02 brightness equations
    neg = C.apply_brightness(x, -0.10)
    pos = C.apply_brightness(x, +0.10)
    ok = np.allclose(neg, np.clip(x - 0.10, 0, 1), atol=1e-6) and \
         np.allclose(pos, np.clip(x + 0.10, 0, 1), atol=1e-6)
    check("02", "brightness x' = clip(x ± 0.10, 0, 1)", ok)

    # 03 contrast equations around per-image-per-channel spatial mean
    lo = C.apply_contrast(x, 0.80)
    mean = x.mean(axis=(-2, -1), keepdims=True)
    ok = np.allclose(lo, np.clip((x - mean) * 0.80 + mean, 0, 1), atol=1e-6)
    check("03", "contrast x' = clip((x - mean_hw)*f + mean_hw, 0, 1)", ok)

    # 04 gamma equations
    g_lo = C.apply_gamma(x, 0.80)
    ok = np.allclose(g_lo, np.clip(x, 0, 1) ** 0.80, atol=1e-6)
    check("04", "gamma x' = clip(x,0,1)^gamma", ok)

    # 05 deterministic noise: identical inputs -> identical outputs
    n1 = C.apply_gaussian_noise(x, 0.02, "abc123", 42)
    n2 = C.apply_gaussian_noise(x, 0.02, "abc123", 42)
    check("05", "gaussian noise deterministic given (sample_id, base_seed, sigma)",
          np.array_equal(n1, n2))

    # 06 different sample_id / base_seed -> different realization
    n3 = C.apply_gaussian_noise(x, 0.02, "abc124", 42)
    n4 = C.apply_gaussian_noise(x, 0.02, "abc123", 123)
    check("06", "noise differs across sample_id and base_seed",
          not np.array_equal(n1, n3) and not np.array_equal(n1, n4))

    # 07 seed derivation exact rule
    msg = "phase36|gaussian_noise|42|abc123".encode()
    exp_seed = int.from_bytes(hashlib.sha256(msg).digest()[:8], "big")
    check("07", "seed derivation = SHA256('phase36|gaussian_noise|<base>|<sid>')[:8]",
          C.derive_noise_seed(42, "abc123") == exp_seed)

    # 08 blur kernel normalization
    k, radius = C._gaussian_kernel1d(1.0)
    check("08", "gaussian blur kernel sums to 1 and radius = ceil(3*sigma)",
          abs(float(k.sum()) - 1.0) < 1e-6 and radius == int(np.ceil(3 * 1.0)),
          f"radius={radius}")

    # 09 blur applied preserves shape & range
    b = C.apply_gaussian_blur(x, 0.5)
    check("09", "blur preserves shape/range, float32",
          b.shape == x.shape and b.dtype == np.float32
          and float(b.min()) >= 0.0 and float(b.max()) <= 1.0)

    # 10 resolution output shape
    r = C.apply_resolution(x, 0.50, 512)
    check("10", "resolution restores to working resolution 512x512",
          r.shape == (x.shape[0], 512, 512) and r.dtype == np.float32,
          f"out_shape={r.shape}")

    # 11 alignment: align_corners frozen false
    check("11", "align_corners frozen False",
          C.IMAGE_CONDITIONS["RESOLUTION_050"]["align_corners"] is False)

    # 12 proposal shift geometry
    geom = C.proposal_geometry(100, 200, 120, 220, 512, 512)
    sh = C.apply_proposal_condition(geom, "SHIFT_LEFT_10", 512, 512)
    exp_delta = int(round(0.10 * geom["crop_side"]))
    check("12", "proposal shift magnitude = 0.10 * canonical crop side",
          abs(sh["center_x"] - (geom["center_x"] - exp_delta)) <= 1,
          f"delta={exp_delta}")

    # 13 proposal scale geometry
    sc = C.apply_proposal_condition(geom, "SCALE_085", 512, 512)
    exp_side = int(round(0.85 * geom["crop_side"]))
    check("13", "proposal scale side = factor * canonical crop side",
          abs(sc["crop_side"] - exp_side) <= 1, f"side={sc['crop_side']} exp={exp_side}")

    # 14 bounds/clamping
    edge = C.proposal_geometry(0, 50, 0, 50, 512, 512)
    cl = C.apply_proposal_condition(edge, "SHIFT_LEFT_10", 512, 512)
    inside = (0 <= cl["y1"] < cl["y2"] <= 512) and (0 <= cl["x1"] < cl["x2"] <= 512)
    check("14", "proposal coordinates clamped inside image bounds", inside)

    # 15 empty proposal handling
    check("15", "empty canonical proposal -> NOT_APPLICABLE_EMPTY_PROPOSAL",
          C.EMPTY_PROPOSAL_HANDLING == "NOT_APPLICABLE_EMPTY_PROPOSAL"
          and C.NO_OUTCOME_DEPENDENT_REPLACEMENT is True)

    # 16 condition registry uniqueness
    check("16", "image & proposal condition registries are unique",
          C.registries_unique())

    # 17 no perturbation chaining
    check("17", "no perturbation chaining (each from original clean input)",
          C.assert_no_chaining() and C.NO_CHAINING is True)

    # 18 KUB subgroup reporting-only
    check("18", "KUB subgroups are REPORTING_ONLY metadata, never classes/task ids",
          C.kube_reporting_only_ok()
          and C.KUB_SUBGROUPS == ["Kidney_Stone", "Bladder_Stone", "Ureteric_Stone"])
    check("19", "KUB metadata does not alter domain task-id mapping",
          C.DOMAIN_TASK_ID["KUB"] == 3 and len(C.DOMAIN_TASK_ID) == 4)

    # 20 TEST / HOLDOUT prohibition
    check("20", "TEST and ROUTER_HOLDOUT declared MUST_NOT_READ",
          "TEST" in C.MUST_NOT_READ and "ROUTER_HOLDOUT" in C.MUST_NOT_READ
          and C.TEST_ROWS == 0 and C.ROUTER_HOLDOUT_ROWS == 0)

    # 21 perturbation set is closed (no jpeg/rotation/crop/color-space)
    forbidden_present = [f for f in C.FORBIDDEN_PERTURBATIONS
                         if any(f.replace("_", "") in cid.lower().replace("_", "")
                                for cid in C.image_condition_ids())]
    check("21", "no jpeg / color-space / rotation / crop / random augmentation",
          not forbidden_present, f"forbidden_present={forbidden_present}")

    # 22 noise base seeds exactly {42,123,3407}
    seeds = set()
    for cid in ("GAUSSIAN_NOISE_LOW", "GAUSSIAN_NOISE_HIGH"):
        seeds |= set(C.IMAGE_CONDITIONS[cid]["base_seeds"])
    check("22", "noise base seeds exactly {42,123,3407}",
          seeds == {42, 123, 3407}, f"seeds={sorted(seeds)}")

    # 23 no best-seed selection
    check("23", "no best-seed selection (per-seed then arithmetic mean)",
          C.BEST_SEED_SELECTION is False
          and C.NOISE_SEED_SUMMARY_RULE == "per_seed_then_arithmetic_mean_across_three_frozen_seeds")

    # 24 metric binding exact
    check("24", "canonical Dice bound; IoU/HD95 bound before execution",
          C.PRIMARY_METRIC == "paired_delta_Dice"
          and C.SECONDARY_METRICS["iou"]["bound"] is True
          and C.SECONDARY_METRICS["hd95"]["bound"] is True)

    # 25 thresholds unaltered
    check("25", "canonical thresholds unchanged (seg 0.50 / roi 0.30)",
          C.T_SEGMENTATION_OUTPUT == 0.50 and C.T_ROI_PROPOSAL == 0.30
          and C.PROPOSAL_THRESHOLD == 0.30)

    # 26 gates fail-closed and separate
    check("26", "science gate PHASE36_EXECUTE and separate smoke gate",
          C.GATE_ENV == "PHASE36_EXECUTE"
          and C.SMOKE_GATE_ENV == "PHASE36_SMOKE_EXECUTE"
          and C.GATE_ENV != C.SMOKE_GATE_ENV)

    # 27 no import-time model execution in common module
    src = (ROOT / "scripts/analysis/phase36_robustness_common_v1_0.py").read_text(encoding="utf-8")
    # strip comments/strings heuristically
    check("27", "common module imports no torch at import time",
          "import torch" not in src.replace("#", ""))

    # 28 A8/C9 policy preserved
    check("28", "A8/C9 policy preserved (budget 0.25, no retraining, no threshold change)",
          C.A8_C9_POLICY["runtime_policy"] == "A8_C9"
          and C.A8_C9_POLICY["nominal_budget"] == 0.25
          and C.A8_C9_POLICY["joint_retraining"] is False
          and C.A8_C9_POLICY["threshold_modification"] is False)

    # 29 stress flags descriptive only
    check("29", "stress flags descriptive only; no p-values",
          C.STRESS_FLAGS_ARE_DESCRIPTIVE_ONLY and C.NO_NEW_PVALUES
          and C.NO_SIGNIFICANCE_CLAIMS)

    # 30 worst-case definitions exclude cross-family contamination
    check("30", "worst-case image min excludes proposal perturbations",
          "excludes proposal perturbations" in C.WORST_IMAGE_DEF
          and C.NO_POST_HOC_SET_EXPANSION is True)

    # 31 float32 clip domain maintained by all conditions
    ok = True
    for cid in C.image_condition_ids():
        seed = 42 if C.IMAGE_CONDITIONS[cid]["kind"] == "gaussian_noise" else None
        o = C.apply_image_condition(x, cid, "unit0001", seed)
        ok = ok and o.dtype == np.float32 and float(o.min()) >= 0.0 and float(o.max()) <= 1.0
    check("31", "all image conditions output float32 within [0,1]", ok)

    passed = sum(1 for r in RESULTS if r["pass"])
    total = len(RESULTS)
    artifact = {
        "artifact": "phase36_robustness_unit_v1_0",
        "section": "\u00a7Q",
        "phase": 36,
        "method": C.METHOD,
        "revision": C.REVISION,
        "classification": "MODEL_FREE_UNIT_TESTS__PERTURBATION_AND_CONTRACT",
        "model_free": True,
        "torch_used": False,
        "checks": RESULTS,
        "total_checks": total,
        "passed": passed,
        "failed": total - passed,
        "all_pass": passed == total,
        "generated_utc": now(),
    }
    AUD.mkdir(parents=True, exist_ok=True)
    out = AUD / "phase36_robustness_unit_v1_0.json"
    out.write_text(json.dumps(artifact, indent=1, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": total,
                      "failed": total - passed,
                      "sha256": hashlib.sha256(out.read_bytes()).hexdigest()}, indent=1))
    return 0 if passed == total else 1


if __name__ == "__main__":
    raise SystemExit(main())
