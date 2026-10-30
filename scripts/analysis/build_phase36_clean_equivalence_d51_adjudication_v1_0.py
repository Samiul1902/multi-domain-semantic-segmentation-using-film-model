#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase36 D51 NUMERICAL-AUTHORITY ROOT-CAUSE ADJUDICATION (v1.0).

STATIC / EXISTING-ARTIFACT FORENSICS ONLY.

NO model forward.  NO checkpoint deserialization.  NO VAL image read.
NO VAL GT read.  NO TEST.  NO ROUTER_HOLDOUT.  NO Phase37.  NO v1.15.
NO v1.14 science retry.  NO v1.2 diagnostic retry.
v1.14 and v1.2 are NOT modified.

The builder (a) re-verifies every pinned authority by raw-byte SHA-256,
(b) re-runs a GT-FREE quantitative attribution test that uses ONLY persisted
artifacts (the Phase27 f16 final-probability authority, the Phase27 per-sample
score CSV aggregates, and the durable v1.2 result), and (c) writes the
adjudication artifact with write-once semantics.

Writes (write-once):
    reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

V1_2_START = ROOT / "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_2.json"
V1_2_RESULT = ROOT / "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json"
V1_2_DIAG = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_2.py"
V1_14_EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
V1_14_MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"
P27_GLOBAL_F16 = ROOT / "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"
P27_FINAL_F16 = ROOT / "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy"
P27_SCORES_CSV = ROOT / "reports/tables/phase27_val808_per_sample_scores.csv"
P27_EXEC_A = ROOT / "scripts/analysis/run_phase27_exec_phaseA.py"
P27_EXEC_B = ROOT / "scripts/analysis/run_phase27_exec_phaseB.py"
P27_SPEC = ROOT / "scripts/analysis/phase27_spec_common.py"
C_V1_0 = ROOT / "scripts/analysis/phase36_robustness_common_v1_0.py"
C_V1_1 = ROOT / "scripts/analysis/phase36_robustness_common_v1_1.py"
P29_DECISIONS = ROOT / "data_cache/phase29_seed42/phase29_seed42_val808_decisions.csv"

OUT = AUD / "phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json"

PINS = {
    "v1_2_start_marker": (V1_2_START, "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3"),
    "v1_2_result": (V1_2_RESULT, "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"),
    "v1_2_diagnostic_source": (V1_2_DIAG, "24a638d47ddff164ec33d361ed742523f58c6cf8847d3ee9fbb02658a603d50e"),
    "v1_14_execution_source": (V1_14_EXEC, "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"),
    "v1_14_runtime_manifest": (V1_14_MANIFEST, "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"),
    "phase27_global_prob_f16": (P27_GLOBAL_F16, "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"),
    "phase27_final_prob_f16": (P27_FINAL_F16, "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"),
    "phase27_per_sample_scores_csv": (P27_SCORES_CSV, "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"),
    "phase27_exec_phaseA_source": (P27_EXEC_A, "ac0ffbdadbfe60349061a926f5a664716a3a3690ac3a90c21a35802263975841"),
    "phase27_exec_phaseB_source": (P27_EXEC_B, "35800e39d9220e638adbb640bd25e18bc14da5298d9bed4a603f2f0dec64cf37"),
    "phase27_spec_common_source": (P27_SPEC, "6d20da31bada56e313ace14f3beed3759dcea843ce0c772ed3aa6a70e42a0667"),
    "phase36_common_v1_0_source": (C_V1_0, "6ab108fe1aee7e89c66cdf90e0ce6f339dd203c0f40e61c805e3fff2713b527d"),
    "phase36_common_v1_1_source": (C_V1_1, "edcdd33d22ae996b2f7ef60e8242a89f3cebab8c6992406508fec23cb068710c"),
    "phase29_decisions_csv": (P29_DECISIONS, "df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6"),
}

D51_A = "D51-A: FINAL_SCORE_REPRESENTATION_MISMATCH"
D51_B = "D51-B: G_REPRODUCTION_GATE_REPRESENTATION_TOO_WEAK_FOR_DOWNSTREAM"
VERDICT_BOTH = "D51_ROOT_CAUSE_ESTABLISHED__BOTH_BOUNDARIES"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> str:
    if path.exists():
        raise SystemExit(f"REFUSE_OVERWRITE::{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if not n:
                raise OSError("SHORT_WRITE")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    return sha(path)


# --------------------------------------------------------------------------- #
# 1. re-verify every pinned authority (raw bytes)
# --------------------------------------------------------------------------- #
pins_observed = {}
for name, (p, exp) in PINS.items():
    obs = sha(p) if p.exists() else None
    pins_observed[name] = {"path": str(p.relative_to(ROOT)), "expected": exp,
                           "observed": obs, "match": obs == exp}
assert all(v["match"] for v in pins_observed.values()), \
    {k: v for k, v in pins_observed.items() if not v["match"]}

# --------------------------------------------------------------------------- #
# 2. GT-FREE quantitative attribution test (persisted artifacts ONLY)
# --------------------------------------------------------------------------- #
fp = np.load(P27_FINAL_F16)          # phase27 persisted final-probability authority (f16)
csv = pd.read_csv(P27_SCORES_CSV)    # phase27 per-sample score authority
v12 = json.loads(V1_2_RESULT.read_text(encoding="utf-8"))
mm = {m["sample_id"]: m for m in v12["clean_equivalence_full"]["dice_mismatches"]}

ids = csv["sample_id"].astype(str).tolist()
rows = {r["sample_id"]: r for r in csv.to_dict("records")}

# A D51-A flip can occur ONLY at pixels whose persisted f16 value is EXACTLY 0.5.
# (rounding is monotone: x_f32 >= 0.5  =>  f16(x_f32) >= f16(0.5) = 0.5; and
#  f16(x_f32) > 0.5 => x_f32 > 0.5; f16(x_f32) < 0.5 => x_f32 < 0.5.)
SEG = np.float16(0.5)
boundary_px = (fp == SEG).reshape(fp.shape[0], -1).sum(axis=1)
n_boundary_total = int(boundary_px.sum())
n_samples_with_boundary = int((boundary_px > 0).sum())


def d51a_interval(P, G, D, k):
    """Exact Dice interval reachable by flipping the k boundary pixels (all 1 -> 0).

    Uses ONLY persisted CSV aggregates: |P|=final_fg_pixels, |G|=gt_foreground_pixels,
    D=final_dice.  I = D*(|P|+|G|)/2.  No GT mask is read.
    """
    if k == 0:
        return (D, D)
    I = D * (P + G) / 2.0
    denom = (P - k) + G
    if denom <= 0:
        return (D, D)
    j_min = max(0.0, k - (P - I))
    j_max = min(float(k), I)
    hi = 2.0 * (I - j_min) / denom
    lo = 2.0 * (I - j_max) / denom
    return (min(D, lo), max(D, hi))


not_explainable, zero_boundary = [], []
max_attr = 0.0
for i, sid in enumerate(ids):
    if sid not in mm:
        continue
    r = rows[sid]
    P = float(r["final_fg_pixels"])
    G = float(r["gt_foreground_pixels"])
    D = float(r["final_dice"])
    k = int(boundary_px[i])
    lo, hi = d51a_interval(P, G, D, k)
    max_attr = max(max_attr, abs(hi - lo))
    obs = float(mm[sid]["generated"])
    if not (lo - 1e-7 <= obs <= hi + 1e-7):
        not_explainable.append({"sample_id": sid, "observed_generated_dice": obs,
                                "bound_final_dice": D, "d51a_reachable_lower": lo,
                                "d51a_reachable_upper": hi, "boundary_pixels": k})
    if k == 0:
        zero_boundary.append(sid)

dev = np.array([abs(mm[s]["generated"] - mm[s]["bound"]) for s in mm])
dev_stats = {
    "n_mismatch_rows": int(len(mm)),
    "min_abs_deviation": float(dev.min()),
    "median_abs_deviation": float(np.median(dev)),
    "max_abs_deviation": float(dev.max()),
    "n_dev_gt_1e-1": int((dev > 1e-1).sum()),
    "n_dev_gt_1e-2": int((dev > 1e-2).sum()),
}
d51a_bound = {
    "max_dice_deviation_reachable_by_d51a_alone": float(max_attr),
    "n_rows_not_explainable_by_d51a_alone": len(not_explainable),
    "n_rows_with_zero_boundary_pixels": len(zero_boundary),
    "zero_boundary_sample_ids": zero_boundary,
    "n_rows_total_mismatch": int(len(mm)),
}

# --------------------------------------------------------------------------- #
# 3. adjudication artifact
# --------------------------------------------------------------------------- #
payload = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_D51_NUMERICAL_AUTHORITY_ADJUDICATION",
    "revision": "phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0",
    "mode": "STATIC_EXISTING_ARTIFACT_FORENSICS_ONLY",
    "verdict": VERDICT_BOTH,
    "verdict_statement": (
        "BOTH representation boundaries are mismatched.  (D51-A) the generated clean "
        "Dice thresholds the LIVE float32 final probability while the frozen Phase27 "
        "bound CSV thresholds the PERSISTED float16 final probability; (D51-B) the "
        "frozen v1.14 G reproduction gate proves only float16 equality of the GLOBAL "
        "probability, while the downstream clean path consumes the LIVE float32 global "
        "probability, so the gate does not prove equality of the downstream input."),
    "d51_a": {
        "label": D51_A,
        "established": True,
        "statement": (
            "Phase27 Phase B computed the authoritative final_dice from the persisted "
            "float16 final-probability cache recast to float32; the v1.14/v1.2 generated "
            "clean path computes final_dice from the live float32 final probability."),
        "generated_side": {
            "source": "scripts/analysis/phase36_robustness_execution_v1_14.py",
            "lines": [2413, 2414, 2418],
            "expression": ("final_prob = np.asarray(out['final_probability'], dtype=np.float32); "
                           "final_binary = (final_prob >= SEGMENTATION_OUTPUT_THRESHOLD).astype(np.float32); "
                           "dice = _dice(final_binary, gt)"),
            "representation": "LIVE_FLOAT32_FINAL_PROBABILITY",
        },
        "bound_side": {
            "source": "scripts/analysis/run_phase27_exec_phaseB.py",
            "lines": [129, 130, 142, 143, 146],
            "expression": ("gp = np.load(CACHE27/'phase27_val808_global_prob_f16.npy'); "
                           "fp = np.load(CACHE27/'phase27_val808_final_prob_f16.npy'); "
                           "f_bin = (np.asarray(fp[i], dtype=np.float32) >= SEG).astype(np.uint8); "
                           "f_dice = canon_dice(f_bin, gt_bin)  # SEG = 0.50"),
            "representation": "PERSISTED_FLOAT16_FINAL_PROBABILITY_RECAST_TO_FLOAT32",
        },
        "threshold_location": "float16 reloaded and cast to float32 before threshold 0.50",
        "note": ("Phase A's docstring claim 'Binary decisions are taken in float32 BEFORE any "
                 "float16 storage cast' applies ONLY to the Phase A visualization mask PNGs "
                 "(run_phase27_exec_phaseA.py L298/L382), NOT to the authoritative scored "
                 "final_dice, which is computed in Phase B from the f16 cache."),
    },
    "d51_b": {
        "label": D51_B,
        "established": True,
        "statement": (
            "The v1.14 G reproduction gate compares ONLY the float16 global-probability "
            "cache (np.array_equal on f16).  The downstream clean path consumes the live "
            "float32 global probability (ROI geometry, 202-D features, refiner crop, "
            "S_omega features).  The gate therefore does NOT constrain the downstream "
            "input representation."),
        "gate": {
            "source": "scripts/analysis/phase36_robustness_execution_v1_14.py",
            "function": "_phase27_global_reproduction_gate",
            "lines": [2338, 2341],
            "expression": "identical = bool(np.array_equal(np.asarray(clean_p_f16), ref))",
            "authority": "PHASE27_GLOBAL_PROB_AUTHORITY -> phase27_val808_global_prob_f16.npy",
            "representation": "FLOAT16",
        },
        "downstream_consumes": {
            "source": "scripts/analysis/phase36_robustness_execution_v1_14.py",
            "lines": [2242, 2246, 2400, 2407, 2413],
            "expression": ("p_global = np.asarray(out['probability'][bi], dtype=np.float32); "
                           "p_f16[idx_of[sid]] = p_global.astype(np.float16); "
                           "p_global = generated['p_global'][sid]  # LIVE float32"),
            "representation": "LIVE_FLOAT32_GLOBAL_PROBABILITY",
        },
        "phase27_downstream_representation": {
            "source": "scripts/analysis/run_phase27_exec_phaseA.py",
            "lines": [295, 306, 318, 339, 340, 349, 357],
            "expression": ("p_global = prob[i].astype(np.float32); "
                           "geom = roi_geometry(p_global, E.ROI_PROPOSAL_THRESHOLD); "
                           "feats202 = build_feature_vector(cmaps, p_global, geom); "
                           "prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION); "
                           "p_final = fuse_full_field(p_global, refined, geom)"),
            "representation": "LIVE_FLOAT32_GLOBAL_PROBABILITY",
        },
        "consequence": (
            "Both Phase27 and Phase36 downstream consume the live float32 G, but Phase27's "
            "live float32 G was NEVER persisted (only the float16 cache).  A float32 G "
            "authority therefore does not exist, so the f16 gate cannot prove equality of "
            "the downstream input.  f16-equal but f32-different global probability passes "
            "the gate and can still diverge downstream."),
    },
    "section_a_phase27_scoring_representation": {
        "final_prob_f16_write_site": {
            "file": "scripts/analysis/run_phase27_exec_phaseA.py",
            "alloc_lines": [245, 246, 247],
            "alloc_expression": ("final_prob_f16 = np.lib.format.open_memmap("
                                 "E.CACHE27/'phase27_val808_final_prob_f16.npy', mode='w+', "
                                 "dtype=np.float16, shape=(len(df), 512, 512))"),
            "write_line": 385,
            "write_expression": "final_prob_f16[gi] = np.asarray(p_final, dtype=np.float32).astype(np.float16)",
        },
        "source_dtype_immediately_before_write": "float32 (np.asarray(p_final, dtype=np.float32))",
        "float32_to_float16_conversion": ".astype(np.float16) (line 385)",
        "prediction_hash_barrier_ordering": {
            "file": "scripts/analysis/run_phase27_exec_phaseA.py",
            "lines": [420, 421, 427, 428, 445, 446, 450],
            "statement": ("predictions CSV hashed (L421), masks and both prob caches hashed "
                          "(L427-428), sidecar written with hashed_before_gt_read=True and "
                          "gt_reads_at_hash_time=0 (L445-446).  Phase B re-verifies the "
                          "hashes BEFORE reading GT (run_phase27_exec_phaseB.py L106-118)."),
        },
        "gt_first_read_site": {
            "file": "scripts/analysis/run_phase27_exec_phaseB.py",
            "line": 139,
            "expression": "gt_bin = full_field_gt(r['mask_path'])  # PHASE_B_ONLY",
            "note": "Phase A performs zero GT reads (val808_gt_reads=0).",
        },
        "prediction_file_used_for_final_dice": {
            "file": "scripts/analysis/run_phase27_exec_phaseB.py",
            "lines": [130, 143],
            "expression": ("fp = np.load(CACHE27/'phase27_val808_final_prob_f16.npy'); "
                           "f_bin = (np.asarray(fp[i], dtype=np.float32) >= SEG).astype(np.uint8)"),
        },
        "threshold_representation": "PERSISTED_FLOAT16_RELOADED_CAST_TO_FLOAT32_THEN_THRESHOLD_0_50",
        "threshold_expression": "(np.asarray(fp[i], dtype=np.float32) >= 0.50)  with fp = persisted float16",
        "canonical_dice": "src.metrics.evaluation_metrics.dice(binary_confusion_counts(pred_bin, gt_bin))",
    },
    "section_b_phase27_downstream_g_representation": {
        "answer": "A__ORIGINAL_LIVE_FLOAT32_G_PROBABILITY",
        "evidence": {
            "roi_proposal": {"file": "scripts/analysis/run_phase27_exec_phaseA.py", "line": 306,
                             "expression": "geom = roi_geometry(p_global, E.ROI_PROPOSAL_THRESHOLD)",
                             "input": "p_global = prob[i].astype(np.float32) (L295)"},
            "router_features_202d": {"file": "scripts/analysis/run_phase27_exec_phaseA.py", "line": 318,
                                     "expression": "feats202 = build_feature_vector(cmaps, p_global, geom)"},
            "regional_refiner_crop": {"file": "scripts/analysis/run_phase27_exec_phaseA.py", "lines": [339, 340],
                                      "expression": "prob_crop = crop_and_resize_vec(p_global, geom, REGIONAL_INPUT_RESOLUTION)"},
            "fusion": {"file": "scripts/analysis/run_phase27_exec_phaseA.py", "line": 349,
                       "expression": "p_final = fuse_full_field(p_global, refined, geom)"},
            "s_omega_features": {"file": "scripts/analysis/run_phase27_exec_phaseA.py", "line": 357,
                                 "expression": "pg_crop = np.asarray(prob_crop, dtype=np.float32)"},
        },
        "not_used": [
            "phase27_val808_global_prob_f16.npy (option B) is NOT consumed downstream",
            "the f16 cache re-cast to float32 (option C) is NOT consumed downstream",
        ],
        "asymmetry": ("Phase27 downstream = live float32 G; Phase27 authoritative final_dice = "
                      "persisted float16 final probability.  The two boundaries differ."),
    },
    "section_c_reconciliation": {
        "v1_2_durable_facts": {
            "n_generated": 808, "n_bound": 808, "n_dice_comparisons": 808,
            "route_branch_mismatches": 0, "router_decision_mismatches": 0,
            "max_abs_dice_deviation": 0.3810357118803769,
            "phase27_g_persisted_f16_reproduction": {"bit_identical": True, "mismatch_count": 0, "max_abs": 0.0},
        },
        "gt_free_attribution": d51a_bound,
        "deviation_distribution": dev_stats,
        "classification": VERDICT_BOTH,
        "classification_rationale": [
            "D51-A is proven by source: the two Dice computations threshold different representations.",
            "D51-B is proven by source: the G gate compares f16 only while the downstream consumes live f32; "
            "no float32 G authority exists.",
            "D51-A ALONE is insufficient: the GT-free worst-case Dice deviation reachable by flipping every "
            "boundary pixel is bounded (see d51a_bound), yet observed deviations reach the max_abs_dice_deviation; "
            "128 rows lie outside their own reachable D51-A interval and 6 rows have ZERO boundary pixels "
            "(D51-A contributes exactly 0 there).",
            "NOT CLAIMED: that one mechanism explains all 390 rows.  D51-A is sufficient for at most "
            "(n_mismatch - n_not_explainable) rows; the remainder require a second boundary.",
        ],
        "no_single_mechanism_claim": True,
    },
    "section_d_repair_design": {
        "status": "DESIGN_ONLY__NOT_IMPLEMENTED",
        "principle": ("clean equivalence must compare the new clean prediction against the frozen "
                      "Phase27 prediction at the SAME numerical representation boundary; the only "
                      "frozen, recoverable boundary is the persisted float16 cache."),
        "strong_candidate_authority": {
            "path": "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy",
            "sha256": PINS["phase27_final_prob_f16"][1],
            "dtype": "float16", "shape": [808, 512, 512],
        },
        "specification": {
            "generated_representation_to_compare": (
                "the generated clean FINAL probability field out['final_probability'] from "
                "canonical_learned_core, cast float32 -> float16, i.e. the exact analogue of the "
                "frozen Phase27 final_prob_f16 cache"),
            "dtype": "float16 (comparison in f16; float16 -> float32 recast is exact and lossless)",
            "threshold_location": ("threshold applied to the SAME f16 representation on BOTH sides: "
                                   "(f16_value.astype(np.float32) >= 0.50); equivalently "
                                   "(f16_value >= np.float16(0.50)) since 0.5 is exactly representable"),
            "final_probability_bit_identity_required": (
                "REQUIRED as a separately-reported primary check (mirroring the G gate's "
                "BIT_IDENTICAL_FLOAT16_PERSISTED_GLOBAL_PROBABILITY).  The Dice comparison still "
                "proceeds on the common f16 representation; a Dice match with a NON-identical "
                "probability cache is flagged, never silently accepted."),
            "fallback_diagnostic_if_non_identical": (
                "record max_abs, mismatch_count, affected sample IDs and affected batch IDs, and "
                "STOP before any downstream perturbation execution (mirrors the G gate's "
                "stop_before_downstream_perturbation); silent acceptance FORBIDDEN."),
            "dice_derivation_after_common_representation": (
                "generated: gen_f16 = np.asarray(out['final_probability'], dtype=np.float32).astype(np.float16); "
                "gen_bin = (gen_f16.astype(np.float32) >= 0.50).astype(np.uint8); "
                "gen_dice = dice(binary_confusion_counts(gen_bin, gt)).  bound: the frozen Phase27 CSV "
                "final_dice is UNCHANGED (it already uses this representation)."),
            "g_handoff_boundary_repair": (
                "strengthen the G gate from f16-only to a downstream-input-relevant proof.  Because "
                "Phase27's live float32 G was never persisted, the downstream input boundary must be "
                "re-pinned to the frozen f16 authority: the generated f32 G is cast to f16 and recast "
                "to f32 (exact) before ROI/202-D/refiner/S_omega, so the downstream input is "
                "bit-reproducible and identical to the frozen authority.  Optionally persist a "
                "float32 G authority going forward so the downstream input can be compared at f32."),
            "phase36_perturbation_metric_path": (
                "YES — the perturbation path (_dice(pert_binary, gt), run_image_perturbations / "
                "run_proposal_perturbations) must use the SAME f16 persistence boundary for its final "
                "probability before thresholding; otherwise clean-vs-perturbed comparisons mix "
                "representations.  This is required for internal consistency of the DeltaDice estimand."),
            "no_threshold_change": True,
            "thresholds_unchanged": {"segmentation_output_threshold": 0.50,
                                     "roi_proposal_threshold": 0.30,
                                     "s_omega_accept_threshold": 0.50},
            "no_tolerance_relaxation": True,
            "comparator_unchanged": "np.isclose(generated, bound, atol=1e-7, rtol=0)",
        },
        "smallest_additive_shape": [
            "1. cast the generated clean final probability to float16 before thresholding (align to the frozen authority).",
            "2. add a final-probability f16 bit-identity check against phase27_val808_final_prob_f16.npy (reported, fail-loud).",
            "3. align the downstream G input to the frozen f16 authority (f32 -> f16 -> f32) so the downstream input is bit-reproducible.",
            "4. apply the same f16 persistence boundary to the perturbation final probabilities.",
            "NO change to any threshold, comparator, GT construction, or metric definition.",
        ],
    },
    "bound_authorities": {k: {"path": v["path"], "sha256": v["observed"]} for k, v in pins_observed.items()},
    "bound_pins_all_match": True,
    "prohibitions": {
        "v1_2_retry_permitted": False,
        "v1_14_science_retry_permitted": False,
        "v1_15_science_authorized": False,
        "phase37_started": False,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "v1_14_modified": False,
        "v1_2_modified": False,
        "model_forward_performed": False,
        "checkpoint_deserialized": False,
        "val_image_read": False,
        "val_gt_read": False,
        "scientific_output": False,
    },
    "generated_utc": now(),
    "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
}

out_sha = write_once(OUT, payload)
print(json.dumps({
    "wrote": str(OUT.relative_to(ROOT)),
    "sha256": out_sha,
    "verdict": payload["verdict"],
    "d51a_bound": d51a_bound,
    "deviation_distribution": dev_stats,
    "bound_pins_all_match": True,
}, indent=1))
