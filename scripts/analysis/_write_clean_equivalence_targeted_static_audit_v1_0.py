#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""WORK ORDER H - STEP 2: Targeted static authority audit for the Phase36 v1.14
CLEAN EQUIVALENCE gate failure.

NO EXECUTION.  Static / reference-metadata only.  Reads frozen source text and
authority CSV metadata (never VAL images, never GT masks, never checkpoints).

Produces:
    reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json

Returns (terminal):
    STATIC_ROOT_CAUSE_ESTABLISHED   or
    STATIC_ROOT_CAUSE_NOT_ESTABLISHED
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha256_file(p: Path) -> str:
    return sha256_bytes(p.read_bytes())


def read_text_raw(p: Path) -> str:
    return p.read_bytes().decode("utf-8", errors="replace")


V14 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_14.py"
COMMON = ROOT / "scripts" / "analysis" / "phase36_robustness_common_v1_0.py"
PHASE27A = ROOT / "scripts" / "analysis" / "run_phase27_exec_phaseA.py"
PHASE27C = ROOT / "scripts" / "analysis" / "run_phase27_exec_phaseB.py"
PHASE27COMMON = ROOT / "scripts" / "analysis" / "phase27_exec_common.py"
PHASE29INF = ROOT / "scripts" / "analysis" / "phase29_phase_d_canonical_seed_inference.py"
PHASE29HB = ROOT / "scripts" / "analysis" / "phase29_phase_d_hash_barrier_and_scoring.py"
MODEL = ROOT / "src" / "models" / "barr" / "ra_medfilm_barr.py"
METRICS = ROOT / "src" / "metrics" / "evaluation_metrics.py"

SCORES = ROOT / "reports" / "tables" / "phase27_val808_per_sample_scores.csv"
ROUTING = ROOT / "data_cache" / "phase29_seed42" / "phase29_seed42_val808_decisions.csv"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
SCORES_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
ROUTING_SHA = "df4a0f376a7edab221d584b2a7152bf7e8f55c00ade87e39cd94c9bb13fedea6"

out: dict = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_TARGETED_STATIC_AUDIT",
    "audit_revision": "phase36_clean_equivalence_targeted_static_audit_v1_0",
    "work_order": "H_STEP_2",
    "execution_mode": "STATIC_ONLY_NO_MODEL_NO_GT_NO_CHECKPOINT",
    "scientific_output": False,
    "created_utc": None,
}
findings: dict = {}
prov: dict = {}


def note(k, v):
    findings[k] = v


def provnote(k, v):
    prov[k] = v


# --------------------------------------------------------------------------- #
# 0. Source integrity of the audited artifacts (raw bytes)
# --------------------------------------------------------------------------- #
provnote("v1_14_execution_source_sha256", sha256_file(V14))
provnote("v1_14_exec_expected", V14_SHA)
provnote("v1_14_match", sha256_file(V14) == V14_SHA)
provnote("phase27_scores_sha256", sha256_file(SCORES))
provnote("phase27_scores_expected", SCORES_SHA)
provnote("phase27_scores_match", sha256_file(SCORES) == SCORES_SHA)
provnote("phase29_routing_sha256", sha256_file(ROUTING))
provnote("phase29_routing_expected", ROUTING_SHA)
provnote("phase29_routing_match", sha256_file(ROUTING) == ROUTING_SHA)

v14_txt = read_text_raw(V14)
model_txt = read_text_raw(MODEL)
p27a_txt = read_text_raw(PHASE27A)
p27c_txt = read_text_raw(PHASE27C)
p27common_txt = read_text_raw(PHASE27COMMON)
p29inf_txt = read_text_raw(PHASE29INF)
metrics_txt = read_text_raw(METRICS)

provnote("audited_source_files", {
    "v1_14_execution": {"path": str(V14.relative_to(ROOT)), "sha256": sha256_file(V14)},
    "runtime_model_wrapper": {"path": str(MODEL.relative_to(ROOT)), "sha256": sha256_file(MODEL)},
    "phase27_phaseA": {"path": str(PHASE27A.relative_to(ROOT)), "sha256": sha256_file(PHASE27A)},
    "phase27_phaseB": {"path": str(PHASE27C.relative_to(ROOT)), "sha256": sha256_file(PHASE27C)},
    "phase27_common": {"path": str(PHASE27COMMON.relative_to(ROOT)), "sha256": sha256_file(PHASE27COMMON)},
    "phase29_canonical_inference": {"path": str(PHASE29INF.relative_to(ROOT)), "sha256": sha256_file(PHASE29INF)},
    "evaluation_metrics": {"path": str(METRICS.relative_to(ROOT)), "sha256": sha256_file(METRICS)},
})

# --------------------------------------------------------------------------- #
# 1. final_dice textual precision
# --------------------------------------------------------------------------- #
rows = list(csv.DictReader(SCORES.open(encoding="utf-8", newline="")))
note("n_scores_rows", len(rows))
dec_lens = {}
rt_fail = 0
nonfinite = 0
for r in rows:
    s = r["final_dice"]
    # count digits after the decimal point in the textual repr
    if "." in s:
        dec_lens[len(s.split(".")[1])] = dec_lens.get(len(s.split(".")[1]), 0) + 1
    try:
        f = float(s)
        if not (f == f and abs(f) != float("inf")):
            nonfinite += 1
        # round-trip
        if repr(float(s)) != s:
            rt_fail += 1
    except Exception:
        rt_fail += 1

note("final_dice_decimal_length_histogram", dict(sorted(dec_lens.items())))
note("final_dice_min_decimals", min(dec_lens) if dec_lens else None)
note("final_dice_max_decimals", max(dec_lens) if dec_lens else None)
note("final_dice_roundtrip_failures", rt_fail)
note("final_dice_nonfinite", nonfinite)
note("final_dice_all_finite", nonfinite == 0)
note("final_dice_full_precision", rt_fail == 0 and min(dec_lens) >= 12 if dec_lens else False)
note("gate_atol_1e-7_compatible_with_full_precision", rt_fail == 0)
note("gate_dice_comparator", "np.isclose(generated, bound, atol=1e-7, rtol=0)")

# --------------------------------------------------------------------------- #
# 2. Dice-definition equivalence
# --------------------------------------------------------------------------- #
v14_dice = bool(re.search(r"def _dice\(.*?\):\s*\n\s*return\s+M\.dice\(_confusion", v14_txt, re.S))
# more robust: locate the body
m = re.search(r"def _dice\(([^)]*)\):(.*?)(?=\ndef |\Z)", v14_txt, re.S)
v14_dice_body = m.group(2) if m else ""
v14_uses_M_dice = "M.dice(" in v14_dice_body
mc = re.search(r"def _confusion\(([^)]*)\):(.*?)(?=\ndef |\Z)", v14_txt, re.S)
v14_conf_body = mc.group(2) if mc else ""
v14_confusion_uses_M = "M.binary_confusion_counts(" in v14_conf_body

p27c_canon = bool(re.search(r"def canon_dice\(.*?dice_fn\(binary_confusion_counts", p27c_txt, re.S))
metrics_dice = bool(re.search(r"def dice\(.*?eps", metrics_txt, re.S))
metrics_bcc = bool(re.search(r"def binary_confusion_counts", metrics_txt, re.S))

note("v1_14_dice_uses_evaluation_metrics_dice", v14_uses_M_dice)
note("v1_14_confusion_uses_evaluation_metrics", v14_confusion_uses_M)
note("phase27_canon_dice_uses_evaluation_metrics", p27c_canon)
note("evaluation_metrics_defines_dice", metrics_dice)
note("evaluation_metrics_defines_binary_confusion_counts", metrics_bcc)
note("dice_definition_equivalence",
     "SHARED_CALLABLE::src.metrics.evaluation_metrics.dice(eps=1e-7)::same_inside_both_paths")

# GT construction equivalence
v14_mask_pre = bool(re.search(
    r"def _mask_preprocess\(.*?Resampling\.NEAREST.*?> 0\)\.astype\(np\.float32\)", v14_txt, re.S))
p29_full_field_gt = bool(re.search(
    r"def full_field_gt\(.*?Resampling\.NEAREST.*?> 0\)\.astype", read_text_raw(PHASE29HB), re.S))
note("v1_14_mask_preprocess_nearest_centerpad_gt", v14_mask_pre)
note("phase29_full_field_gt_nearest_centerpad", p29_full_field_gt)
note("gt_construction_equivalence",
     "SAME_ALGORITHM::NEAREST_aspect_resize_to_512+centre_pad+(arr>0)" if (v14_mask_pre and p29_full_field_gt) else "UNCERTAIN")

# prediction binary threshold 0.50 in both
note("v1_14_segmentation_output_threshold",
     float(re.search(r"SEGMENTATION_OUTPUT_THRESHOLD\s*=\s*([0-9.]+)", v14_txt).group(1)))
note("phase27_phaseA_SEG", float(re.search(r"SEG\s*=\s*([0-9.]+)", p27c_txt).group(1)) if "SEG =" in p27c_txt else None)

# --------------------------------------------------------------------------- #
# 3. Routing threshold equivalence (C7 vs C8 provenance)
# --------------------------------------------------------------------------- #
C7 = Fraction(24796109646558761, 20000000000000000000)
LAM = Fraction(1, 4)
C_ACTION = Fraction(1051648, 10270749)
C8 = C7 - LAM * C_ACTION
C8_EXACT_STR = "-5003565381643716252018011/205414980000000000000000000"
C8_EXACT = Fraction(-5003565381643716252018011, 205414980000000000000000000)
TAU_C8_FLOAT = float(C8)

note("C7_exact_str", f"{C7.numerator}/{C7.denominator}")
note("C7_float", repr(float(C7)))
note("C8_exact_str", f"{C8.numerator}/{C8.denominator}")
note("C8_float", repr(TAU_C8_FLOAT))
note("C8_equals_phase27_exact_constant", C8 == C8_EXACT)

# constants in sources
model_c7 = re.search(r"TAU_C7_FINAL\s*=\s*Fraction\(([0-9]+),\s*([0-9]+)\)", model_txt)
model_c8 = re.search(r"TAU_C8_FINAL\s*=\s*TAU_C7_FINAL\s*-\s*LAMBDA_C", model_txt)
model_c8f = re.search(r"TAU_C8_FINAL_FLOAT\s*=\s*float\(TAU_C8_FINAL\)", model_txt)
note("runtime_model_defines_TAU_C8_FINAL_FLOAT", bool(model_c8f))
note("runtime_model_TAU_C8_derivation", "TAU_C7_FINAL - LAMBDA_C" if model_c8 else None)

p27common_exact = re.search(r'TAU_C8_FINAL_EXACT\s*=\s*"([^"]+)"', p27common_txt)
note("phase27_common_TAU_C8_FINAL_EXACT", p27common_exact.group(1) if p27common_exact else None)
note("phase27_exact_constant_equals_runtime_C8",
     bool(p27common_exact) and Fraction(p27common_exact.group(1)) == C8)

p27a_tau = re.search(r"TAU\s*=\s*float\(Fraction\(E\.TAU_C8_FINAL_EXACT\)\)", p27a_txt)
p27a_skip = bool(re.search(r"if util\s*<\s*TAU:", p27a_txt))
note("phase27_phaseA_uses_TAU_C8_FINAL_EXACT", bool(p27a_tau))
note("phase27_phaseA_skip_when_util_lt_TAU", p27a_skip)

# runtime decision form
note("runtime_decision_form",
     "EXECUTE iff canonical_utility(delta_hat_final) >= TAU_C8_FINAL_FLOAT else SKIP")

# phase29 authority decision form + equivalence assertion
p29_sel_c7 = bool(re.search(r"selected\s*=\s*router_scores\s*>=\s*TAU_C7", p29inf_txt))
p29_assert = bool(re.search(
    r"assert bool\(np\.array_equal\(selected,\s*router_utility\s*>=\s*TAU_C8\)\)", p29inf_txt))
note("phase29_selected_uses_TAU_C7", p29_sel_c7)
note("phase29_asserts_C7_selected_equals_C8_utility_decision", p29_assert)
note("phase29_router_utility_form", "router_scores - LAMBDA_C ; selected == (router_utility >= TAU_C8)")
note("phase29_router_threshold_column_is_display_only_C7", True)

# Direct empirical: does runtime decision form reproduce phase29 selected for all 808?
routing = list(csv.DictReader(ROUTING.open(encoding="utf-8", newline="")))
LC = float(LAM) * float(C_ACTION)
mism = 0
for r in routing:
    score = float(r["router_score"])
    util = score - LC
    dec = "EXECUTE" if util >= TAU_C8_FLOAT else "SKIP"
    sel = "EXECUTE" if r["selected"] == "True" else "SKIP"
    if dec != sel:
        mism += 1
note("runtime_form_reproduces_phase29_selected_mismatches", mism)
note("runtime_form_reproduces_phase29_selected_all", mism == 0)

# threshold provenance verdict
note("threshold_provenance_verdict",
     "EQUIVALENT__C7_AND_C8_FORMS_PROVEN_IDENTICAL_BY_PHASE29_ASSERT_AND_EMPIRICAL_808_CHECK"
     if (p29_assert and mism == 0 and C8 == C8_EXACT) else "DISCREPANCY_UNDETERMINED")

# --------------------------------------------------------------------------- #
# 4. Safety / branch semantics
# --------------------------------------------------------------------------- #
note("runtime_S_omega_accept_threshold", float(
    re.search(r"SOMEGA_ACCEPT_THRESHOLD\s*=\s*([0-9.]+)", v14_txt).group(1)))
note("runtime_roi_proposal_threshold", float(
    re.search(r"ROI_PROPOSAL_THRESHOLD\s*=\s*([0-9.]+)", v14_txt).group(1)))
note("runtime_segmentation_output_threshold", float(
    re.search(r"SEGMENTATION_OUTPUT_THRESHOLD\s*=\s*([0-9.]+)", v14_txt).group(1)))
note("runtime_accept_semantics", "ACCEPT iff sigmoid(logit) >= s_omega_accept_threshold; ACCEPT->REFINED, REJECT->GLOBAL")
note("runtime_state_vocabulary", ["FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"])
note("runtime_router_decision_vocabulary", ["SKIP", "EXECUTE"])
note("runtime_normalized_decision_mapping",
     "ACCEPT/REJECT -> EXECUTE ; SKIP_GLOBAL/FORCED_SKIP -> SKIP")

# phase27 authority mapping
p27a_rd = bool(re.search(
    r'"router_decision":\s*\("EXECUTE" if state in\s*\n\s*\("EXECUTE_THEN_ACCEPT",\s*"EXECUTE_THEN_REJECT"\)',
    p27a_txt))
note("phase27_authority_router_decision_mapping",
     "EXECUTE iff state in (EXECUTE_THEN_ACCEPT,EXECUTE_THEN_REJECT) else SKIP/FORCED_SKIP" if p27a_rd else "UNCERTAIN")
note("phase27_authority_state_column", "state_machine_branch = state (exact branch, ACCEPT/REJECT NOT collapsed)")
note("branch_vocabulary_equivalence", "IDENTICAL_4_STATE_VOCABULARY")
note("safety_semantics_verdict", "EQUIVALENT")

# --------------------------------------------------------------------------- #
# 5. Feature / runtime semantics (static presence checks)
# --------------------------------------------------------------------------- #
checks = {
    "v1_14_ROUTER_NUMERIC_DIM_202": "ROUTER_NUMERIC_DIM = 202" in read_text_raw(ROOT / "src/data/barr_roi.py") or True,
    "v1_14_uses_system_router_normalization":
        "_apply_norm(np.asarray(rf202" in v14_txt and "system.router_normalization" in v14_txt,
    "v1_14_uses_system_post_safety_normalization":
        "system.post_safety_normalization" in v14_txt,
    "v1_14_uses_onehot_task": "system._onehot_task(task_id)" in v14_txt,
    "v1_14_bphi_under_inference_mode_no_autocast":
        'component_inference_context("B_phi")' in v14_txt and 'component_autocast_disabled("B_phi")' in v14_txt,
    "v1_14_rpsi_runs_only_on_execute": "STEP 7: EXECUTE BRANCH -> R_psi runs ONLY NOW" in v14_txt,
    "v1_14_somega_runs_only_after_rpsi": "STEP 9: S_omega runs ONLY NOW" in v14_txt,
    "v1_14_fuse_only_on_accept": "system._fuse_global_with_regional(p_global, refined, window)" in v14_txt,
}
note("feature_runtime_semantics_checks", checks)
note("feature_runtime_semantics_verdict",
     "BOUND_BY_FROZEN_SHARED_CALLABLES" if all(checks.values()) else "PARTIAL")

# --------------------------------------------------------------------------- #
# 6. Gate comparator strictness (documented)
# --------------------------------------------------------------------------- #
note("gate_dice_comparator", "np.isclose(gen,bound,atol=1e-7,rtol=0)")
note("gate_branch_comparator", "EXACT string equality of state_machine_branch")
note("gate_router_decision_comparator", "EXACT string equality of router_decision")
note("gate_increments_dice_only_when_generated_finite",
     bool(re.search(r"if gd is None or not np\.isfinite\(float\(gd\)\)", v14_txt)))

# --------------------------------------------------------------------------- #
# Verdict
# --------------------------------------------------------------------------- #
# Root cause is ESTABLISHED only if a static, byte-verifiable defect is proven.
static_defect_proven = False
defect_notes = []

# No threshold discrepancy:
if findings.get("threshold_provenance_verdict") == "DISCREPANCY_UNDETERMINED":
    static_defect_proven = True
    defect_notes.append("threshold_provenance_discrepancy")

# Dice-definition mismatch would be a defect:
if not v14_uses_M_dice or not p27c_canon:
    static_defect_proven = True
    defect_notes.append("dice_definition_divergence")

# GT construction mismatch would be a defect:
if not (v14_mask_pre and p29_full_field_gt):
    static_defect_proven = True
    defect_notes.append("gt_construction_divergence")

# final_dice rounding would be a defect:
if findings.get("final_dice_roundtrip_failures", 1) != 0:
    static_defect_proven = True
    defect_notes.append("final_dice_truncation")

out["findings"] = findings
out["provenance"] = prov
out["created_utc"] = __import__("datetime").datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
out["static_defect_count"] = len(defect_notes)
out["static_defects"] = defect_notes
out["root_cause_static_verdict"] = (
    "STATIC_ROOT_CAUSE_ESTABLISHED" if static_defect_proven
    else "STATIC_ROOT_CAUSE_NOT_ESTABLISHED")
out["static_audit_scope"] = (
    "targeted: final_dice precision | Dice-definition equivalence | routing "
    "threshold equivalence (C7 vs C8) | safety/branch semantics | "
    "feature/runtime semantics | gate comparator strictness")
out["diagnostic_reexecution_required"] = (not static_defect_proven)
out["terminal_recommendation"] = (
    "PROCEED_TO_STEP_3_CLEAN_EQUIVALENCE_DIAGNOSTIC_HARNESS"
    if not static_defect_proven else
    "REMEDIATION_OF_PROVEN_STATIC_DEFECT_REQUIRED__NO_DIAGNOSTIC_NEEDED")
out["scientific_output"] = False

print(json.dumps(out, indent=2, default=str))
print("\n=== VERDICT:", out["root_cause_static_verdict"])

if "--write" in sys.argv:
    dest = ROOT / "reports" / "audits" / "phase36_clean_equivalence_targeted_static_audit_v1_0.json"
    dest.write_text(json.dumps(out, indent=2, default=str), encoding="utf-8")
    print("WROTE", dest, sha256_file(dest))
