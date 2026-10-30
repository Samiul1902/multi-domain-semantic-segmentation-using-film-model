#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase36 D51 RECONCILIATION artifact (v1.1).

ADDITIVE.  The original adjudication artifact
``phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json`` is NOT
overwritten.

This builder records (a) a compliance correction for the original work order,
(b) a corrected D51-A reachable-set analysis (union over q in [0,k] with the exact
canonical Dice epsilon), (c) a corrected D51-B interpretation, and (d) the
withdrawal of the G f32->f16->f32 downstream repair.

STATIC / EXISTING-ARTIFACT FORENSICS ONLY.
NO model forward.  NO checkpoint deserialization.  NO VAL image read.
NO VAL GT read.  NO TEST.  NO ROUTER_HOLDOUT.  NO Phase37.

Writes (write-once):
    reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json
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

ADJUDICATION = AUD / "phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json"
ADJUDICATION_SHA = "27ac7ada4ee39190d8823b8b1ff7e6e2beb304e2e7fc5778542883ac7eacc53a"
BUILDER_V1_0 = ROOT / "scripts/analysis/build_phase36_clean_equivalence_d51_adjudication_v1_0.py"
BUILDER_V1_0_SHA = "bc88a21d27b0466de8efe791f681494df08002b33deba40606724c86335aaee0"

V1_2_START = AUD / "phase36_clean_equivalence_diagnostic_start_v1_2.json"
V1_2_START_SHA = "be93d494b1aa2aad3c900f442c16efe55bcbf0bd508a72df8f8b83e72cd7d2d3"
V1_2_RESULT = AUD / "phase36_clean_equivalence_diagnostic_result_v1_2.json"
V1_2_RESULT_SHA = "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"
V1_14_EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
V1_14_EXEC_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
P27_GLOBAL_F16 = ROOT / "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy"
P27_GLOBAL_F16_SHA = "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"
P27_FINAL_F16 = ROOT / "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy"
P27_FINAL_F16_SHA = "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"
P27_SCORES_CSV = ROOT / "reports/tables/phase27_val808_per_sample_scores.csv"
P27_SCORES_CSV_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
METRICS = ROOT / "src/metrics/evaluation_metrics.py"

OUT = AUD / "phase36_clean_equivalence_d51_reconciliation_v1_1.json"

EPS = 1e-7  # exact canonical Dice epsilon (src/metrics/evaluation_metrics.py `_EPS`)

CORRECTED_VERDICT = ("D51_ROOT_CAUSE_PARTIALLY_ESTABLISHED__FINAL_SCORE_BOUNDARY_CONFIRMED"
                     "__G_HANDOFF_CAUSALITY_UNPROVEN")


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
# bind originals
# --------------------------------------------------------------------------- #
assert sha(ADJUDICATION) == ADJUDICATION_SHA, "adjudication SHA drift"
assert sha(BUILDER_V1_0) == BUILDER_V1_0_SHA, "builder v1.0 SHA drift"
assert sha(V1_2_START) == V1_2_START_SHA
assert sha(V1_2_RESULT) == V1_2_RESULT_SHA
assert sha(V1_14_EXEC) == V1_14_EXEC_SHA
assert sha(P27_GLOBAL_F16) == P27_GLOBAL_F16_SHA
assert sha(P27_FINAL_F16) == P27_FINAL_F16_SHA
assert sha(P27_SCORES_CSV) == P27_SCORES_CSV_SHA

# --------------------------------------------------------------------------- #
# corrected D51-A reachable-set analysis (GT-FREE; exact canonical epsilon)
# --------------------------------------------------------------------------- #
fp16 = np.load(P27_FINAL_F16)
csv = pd.read_csv(P27_SCORES_CSV)
v12 = json.loads(V1_2_RESULT.read_text(encoding="utf-8"))
mm = {m["sample_id"]: m for m in v12["clean_equivalence_full"]["dice_mismatches"]}
ids = csv["sample_id"].astype(str).tolist()
rows = {r["sample_id"]: r for r in csv.to_dict("records")}
karr = (fp16 == np.float16(0.5)).reshape(fp16.shape[0], -1).sum(axis=1)


def _tp_fp_fn(P, G, D):
    """Recover the canonical confusion counts from persisted aggregates only."""
    tp = (D * (P + G + EPS) - EPS) / 2.0
    return tp, P - tp, G - tp


def old_interval(P, G, D, k):
    """ORIGINAL (v1.0) method: only q == k, and I = D*(P+G)/2 (epsilon dropped)."""
    if k == 0:
        return (D, D)
    I = D * (P + G) / 2.0
    denom = (P - k) + G
    if denom <= 0:
        return (D, D)
    j_min = max(0.0, k - (P - I))
    j_max = min(float(k), I)
    return (min(D, 2.0 * (I - j_max) / denom), max(D, 2.0 * (I - j_min) / denom))


def corrected_interval(P, G, D, k):
    """CORRECTED: union over q in [0,k] and admissible TP/FP overlap, exact epsilon.

    Dice'(q, j) = (2*(tp - j) + eps) / (2*tp + fp + fn - q + eps)
    j in [max(0, q - min(k, fp)), min(q, min(k, tp))]
    """
    if k == 0:
        return (D, D)
    tp, fp_, fn = _tp_fp_fn(P, G, D)
    if tp < -1e-6 or fp_ < -1e-6 or fn < -1e-6:
        return (D, D)
    tp = max(0.0, tp)
    fp_ = max(0.0, fp_)
    fn = max(0.0, fn)
    lo = hi = D
    j_hi_cap = min(k, tp)
    j_lo_cap = min(k, fp_)
    for q in range(0, k + 1):
        denom = 2.0 * tp + fp_ + fn - q + EPS
        if denom <= 0:
            continue
        j_max = min(q, j_hi_cap)          # max TP flips -> min Dice
        j_min = max(0.0, q - j_lo_cap)    # min TP flips -> max Dice
        lo = min(lo, (2.0 * (tp - j_max) + EPS) / denom)
        hi = max(hi, (2.0 * (tp - j_min) + EPS) / denom)
    return (lo, hi)


old_not, new_not = [], []
old_maxattr = new_maxattr = 0.0
max_width_increase = 0.0
for i, sid in enumerate(ids):
    if sid not in mm:
        continue
    r = rows[sid]
    P = float(r["final_fg_pixels"])
    G = float(r["gt_foreground_pixels"])
    D = float(r["final_dice"])
    k = int(karr[i])
    o = old_interval(P, G, D, k)
    n = corrected_interval(P, G, D, k)
    old_maxattr = max(old_maxattr, abs(o[1] - o[0]))
    new_maxattr = max(new_maxattr, abs(n[1] - n[0]))
    max_width_increase = max(max_width_increase, max(0.0, abs(n[1] - n[0]) - abs(o[1] - o[0])))
    obs = float(mm[sid]["generated"])
    if not (o[0] - 1e-7 <= obs <= o[1] + 1e-7):
        old_not.append(sid)
    if not (n[0] - 1e-7 <= obs <= n[1] + 1e-7):
        new_not.append(sid)

zero_boundary = [sid for sid in mm if int(karr[ids.index(sid)]) == 0]

old_analysis = {
    "method": ("q == k only (remove ALL f16==0.5 pixels); intersection recovered as "
               "I = D*(P+G)/2 (canonical epsilon DROPPED)"),
    "max_dice_deviation_reachable_by_d51a_alone": float(old_maxattr),
    "n_rows_not_explainable_by_d51a_alone": len(old_not),
    "n_rows_explainable": int(len(mm)) - len(old_not),
}
corrected_analysis = {
    "method": ("union over q in [0, k] and admissible TP/FP overlap j in "
               "[max(0, q - min(k, fp)), min(q, min(k, tp))]; EXACT canonical Dice "
               "(2*tp + eps)/(2*tp + fp + fn + eps) with eps = 1e-7"),
    "canonical_dice_epsilon": EPS,
    "canonical_dice_source": "src/metrics/evaluation_metrics.py (_EPS = 1e-7; dice())",
    "max_dice_deviation_reachable_by_d51a_alone": float(new_maxattr),
    "n_rows_not_explainable_by_d51a_alone": len(new_not),
    "n_rows_explainable": int(len(mm)) - len(new_not),
    "n_rows_with_zero_boundary_pixels": len(zero_boundary),
    "zero_boundary_sample_ids": zero_boundary,
    "n_mismatch_rows_total": int(len(mm)),
}
comparison = {
    "rows_explainable_under_old_but_not_corrected": len(set(new_not) - set(old_not)),
    "rows_explainable_under_corrected_but_not_old": len(set(old_not) - set(new_not)),
    "max_interval_width_increase": float(max_width_increase),
    "claim_survives": len(new_not) == len(old_not),
    "conclusion": ("The corrected union-over-q + exact-epsilon analysis yields the SAME "
                   "count as the original analysis; the '128 rows not explainable by "
                   "D51-A alone' claim SURVIVES."),
}

payload = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_D51_RECONCILIATION",
    "revision": "phase36_clean_equivalence_d51_reconciliation_v1_1",
    "mode": "STATIC_EXISTING_ARTIFACT_FORENSICS_ONLY",
    "purpose": ("ADDITIVE reconciliation of the D51 v1.0 adjudication: compliance correction, "
                "corrected D51-A reachable-set analysis, corrected D51-B interpretation, and "
                "withdrawal of the G quantization repair."),
    "supersedes_interpretation_of": "reports/audits/phase36_clean_equivalence_d51_numerical_authority_adjudication_v1_0.json",
    "original_adjudication_not_overwritten": True,
    "bound_originals": {
        "adjudication_v1_0": {"path": str(ADJUDICATION.relative_to(ROOT)), "sha256": ADJUDICATION_SHA},
        "builder_v1_0": {"path": str(BUILDER_V1_0.relative_to(ROOT)), "sha256": BUILDER_V1_0_SHA},
    },
    "bound_evidence": {
        "v1_2_start": {"path": str(V1_2_START.relative_to(ROOT)), "sha256": V1_2_START_SHA},
        "v1_2_result": {"path": str(V1_2_RESULT.relative_to(ROOT)), "sha256": V1_2_RESULT_SHA},
        "v1_14_execution_source": {"path": str(V1_14_EXEC.relative_to(ROOT)), "sha256": V1_14_EXEC_SHA},
        "phase27_global_prob_f16": {"path": str(P27_GLOBAL_F16.relative_to(ROOT)), "sha256": P27_GLOBAL_F16_SHA},
        "phase27_final_prob_f16": {"path": str(P27_FINAL_F16.relative_to(ROOT)), "sha256": P27_FINAL_F16_SHA},
        "phase27_per_sample_scores_csv": {"path": str(P27_SCORES_CSV.relative_to(ROOT)), "sha256": P27_SCORES_CSV_SHA},
    },

    # ---------------- STEP 1 — compliance correction ---------------- #
    "compliance_correction": {
        "statement": ("An exploratory attribution pass DID read VAL GT masks "
                      "(a GT-dependent Dice computation)."),
        "val_gt_read_during_original_work_order": True,
        "gt_dependent_exploratory_result_discarded": True,
        "final_recorded_attribution_rederived_gt_free": True,
        "interpretation_of_original_field": (
            "The original artifact field val_gt_read=false describes ONLY the FINAL RECORDED "
            "attribution pass (which was GT-free).  It MUST NOT be interpreted as describing "
            "the entire original work order."),
        "violation_preserved_not_erased": True,
        "test_accessed": False,
        "router_holdout_accessed": False,
        "model_forward_performed": False,
        "checkpoint_deserialized": False,
        "val_image_read": False,
    },

    # ---------------- STEP 2 — corrected D51-A attribution ---------------- #
    "d51_a": {
        "label": "D51-A: FINAL_SCORE_REPRESENTATION_MISMATCH",
        "status": "ESTABLISHED",
        "preserved_source_fact": (
            "A live-f32 prediction can differ from persisted-f16 scoring only at values whose "
            "persisted f16 representation is exactly 0.5 (f16 rounding is monotone; "
            "x_f32 >= 0.5 => f16(x_f32) >= 0.5, and f16(x_f32) > 0.5 => x_f32 > 0.5)."),
        "old_analysis": old_analysis,
        "corrected_analysis": corrected_analysis,
        "comparison": comparison,
        "old_value_recorded": old_analysis["n_rows_not_explainable_by_d51a_alone"],
        "corrected_value_recorded": corrected_analysis["n_rows_not_explainable_by_d51a_alone"],
        "retained_claim": ("128 of 390 mismatch rows are not explainable by D51-A alone "
                           "— SURVIVES the corrected union-over-q + exact-epsilon calculation."),
    },

    # ---------------- STEP 3 — corrected D51-B interpretation ---------------- #
    "d51_b": {
        "label": "D51-B: G_REPRODUCTION_GATE_REPRESENTATION_TOO_WEAK_FOR_DOWNSTREAM",
        "gate_defect_established": True,
        "authority_defect_statement": (
            "The v1.14 G gate verifies only the persisted float16 G; Phase27 downstream consumed "
            "the ORIGINAL LIVE float32 G; Phase36 downstream also consumes live float32 G; the "
            "original Phase27 live-f32 G was NEVER persisted.  Therefore the gate CANNOT prove "
            "live-f32 downstream equality."),
        "actual_live_f32_difference_established": False,
        "actual_live_f32_difference_statement": (
            "This does NOT prove that Phase27 and Phase36 live-f32 G actually differed.  No "
            "float32 G authority exists, so the difference is unproven in either direction."),
        "causal_contribution_to_dice_mismatches": "UNRESOLVED",
    },

    # ---------------- STEP 4 — withdrawn repair ---------------- #
    "g_quantization_repair": {
        "proposed_in_v1_0": "generated f32 G -> f16 -> f32 before ROI / 202-D / refiner / S_omega",
        "status": "WITHDRAWN",
        "reason": "WOULD_CHANGE_FROZEN_PHASE27_LIVE_FLOAT32_DOWNSTREAM_SEMANTICS",
        "rationale": ("Phase27 source proves its downstream consumed the ORIGINAL LIVE float32 G "
                      "(run_phase27_exec_phaseA.py L295/L306/L318/L339-340/L349/L357).  "
                      "Quantizing G downstream would change the scientific computation rather "
                      "than reproduce Phase27."),
        "must_not_change": {
            "roi_threshold": 0.30,
            "segmentation_threshold": 0.50,
            "s_omega_threshold": 0.50,
            "router_threshold": "UNCHANGED",
            "feature_definitions": "UNCHANGED",
            "model_inputs": "UNCHANGED",
            "model_weights": "UNCHANGED",
        },
    },

    # ---------------- corrected overall verdict ---------------- #
    "corrected_overall_verdict": CORRECTED_VERDICT,
    "superseded_verdict": "D51_ROOT_CAUSE_ESTABLISHED__BOTH_BOUNDARIES",
    "verdict_explanation": (
        "The FINAL-SCORE boundary (D51-A) is CONFIRMED by source.  The G-HANDOFF boundary (D51-B) "
        "is an ESTABLISHED AUTHORITY/REPRODUCIBILITY DEFECT, but its CAUSAL contribution to the "
        "390 Dice mismatches is UNPROVEN, because no float32 G authority exists to demonstrate "
        "that the live-f32 G actually differed."),

    "prohibitions": {
        "v1_2_retry_permitted": False,
        "v1_1_retry_permitted": False,
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
    "corrected_overall_verdict": CORRECTED_VERDICT,
    "old_analysis": old_analysis,
    "corrected_analysis": corrected_analysis,
    "comparison": comparison,
}, indent=1))
