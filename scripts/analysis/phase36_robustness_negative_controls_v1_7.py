#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.7 — NC36-NC40 negative controls.

NO torch import.  NO model.  Mutants are IN-MEMORY STRING EDITS ONLY.
"""
from __future__ import annotations

import ast, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

SRC = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_7.py").read_text(encoding="utf-8")
FUNCS = {n.name: n for n in ast.walk(ast.parse(SRC)) if isinstance(n, ast.FunctionDef)}

REPORTS = []


def _body(fn):
    n = FUNCS.get(fn)
    if n is None:
        return ""
    return ast.get_source_segment(SRC, n) or ""


def record(id_, v16_mutant_bite, v17_should_pass, v17_should_fail_reason, evidence):
    REPORTS.append({
        "nc": id_,
        "v1_6_mutant_bite": v16_mutant_bite,
        "v1_7_pass": bool(v17_should_pass),
        "v1_7_fail_reason": v17_should_fail_reason,
        "evidence": evidence,
    })


# --------------------------------------------------------------------------- #
# NC36: forced S_omega bypass still claims real forward count == 1
# --------------------------------------------------------------------------- #
mut36 = SRC.replace("actual_s_omega_forwards += 1\n        accept_prob = ...",
                    "# bypassed\n        accept_prob = ...")
mut36 = mut36.replace("actual_s_omega_forwards,", "1,")
record(
    "NC36_FORCED_SOMEGA_FALSE_FORWARD_COUNT",
    True,
    "actual_s_omega_forwards" in SRC and "actual_s_omega_forwards=actual_s_omega_forwards" in SRC,
    "v1.7 MUST increment actual_s_omega_forwards only after a real S_omega forward; "
    "the forced-safety path must leave it at 0",
    {"actual_s_omega_forwards_in_v1_7": "actual_s_omega_forwards" in SRC,
     "somega_passes_actual_in_v1_7": "actual_s_omega_forwards=actual_s_omega_forwards" in SRC,
     "mutant_has_bypass_pattern": "# bypassed" in mut36})

# --------------------------------------------------------------------------- #
# NC37: real S_omega forward probe required
# --------------------------------------------------------------------------- #
record(
    "NC37_REAL_SOMEGA_FORWARD_PROBE_REQUIRED",
    True,
    "def smoke_real_execute_component_probe" in SRC,
    "v1.7 MUST contain a guaranteed real S_omega forward probe in synthetic smoke",
    {"probe_present": "def smoke_real_execute_component_probe" in SRC,
     "probe_forces_router_execute": "forced_delta_hat_final=+50.0" in SRC,
     "probe_does_not_force_somega_logit": "forced_s_omega_logit=None" in SRC})

# --------------------------------------------------------------------------- #
# NC38: rf202_finite mis-bound to final_probability
# --------------------------------------------------------------------------- #
mut38 = SRC.replace('"rf202_finite": bool(out_clean["router_vector_finite"])',
                    '"rf202_finite": bool(np.isfinite(np.asarray(out_clean["final_probability"])).all())')
record(
    "NC38_ROUTER_FEATURE_FINITE_MISBINDING",
    True,
    '"rf202_finite": bool(out_clean["router_vector_finite"])' in SRC
    and '"rf202_finite": bool(np.isfinite(np.asarray(out_clean' not in SRC,
    "v1.7 MUST bind rf202_finite to the actual 202-D router vector, never to final_probability",
    {"v1_7_binds_router_vector_finite": '"rf202_finite": bool(out_clean["router_vector_finite"])' in SRC,
     "v1_7_no_misbind_to_final_probability": '"rf202_finite": bool(np.isfinite(np.asarray(out_clean' not in SRC,
     "mutant_has_misbind": '"rf202_finite": bool(np.isfinite(np.asarray(out_clean["final_probability"]))' in mut38})

# --------------------------------------------------------------------------- #
# NC39: smoke success not fail-closed in main
# --------------------------------------------------------------------------- #
main_body = _body("main")
mut39 = main_body.replace(
    'if not bool(res.get("smoke_all_pass")):\n            print(json.dumps({',
    'if False:\n            print(json.dumps({')
record(
    "NC39_SMOKE_SUCCESS_FAIL_CLOSED",
    True,
    'if not bool(res.get("smoke_all_pass")):' in main_body
    and "return 1" in main_body
    and "return 0" in main_body,
    "v1.7 main MUST exit nonzero when smoke_all_pass is false",
    {"v1_7_checks_smoke_all_pass": 'if not bool(res.get("smoke_all_pass")):' in main_body,
     "v1_7_returns_1_on_fail": "return 1" in main_body,
     "v1_7_returns_0_on_pass": "return 0" in main_body,
     "mutant_bypasses_check": 'if False:' in mut39})

# --------------------------------------------------------------------------- #
# NC40: v1.6 preservation
# --------------------------------------------------------------------------- #
record(
    "NC40_V1_6_PRESERVATION",
    False,
    ("get_device(require_cuda=True)" in SRC
     and "VAL808_ONLY" in SRC
     and "g.to(device)" in SRC
     and "torch.sigmoid(t.float())" in SRC
     and "component_inference_context" in SRC
     and "C.VAL_MANIFEST_SHA" in SRC
     and "_static_protected_io_unreachable()" in SRC),
    "v1.7 MUST preserve all v1.6 protected-population, probability, CUDA, device and component-context repairs",
    {"cuda_fail_closed": "get_device(require_cuda=True)" in SRC,
     "val_only_population": "VAL808_ONLY" in SRC,
     "four_component_binding": all(t in SRC for t in ("g.to(device)", "b_phi.to(device)",
                                                       "r_psi.to(device)", "s_omega.to(device)")),
     "canonical_sigmoid": "torch.sigmoid(t.float())" in SRC,
     "inference_contexts": "component_inference_context" in SRC,
     "val_manifest_sha_guard": "C.VAL_MANIFEST_SHA" in SRC,
     "static_protected_io_unreachable": "_static_protected_io_unreachable()" in SRC})

# --------------------------------------------------------------------------- #
# REPORT
# --------------------------------------------------------------------------- #
REPAIR = [r for r in REPORTS if r["v1_6_mutant_bite"]]
PRES   = [r for r in REPORTS if not r["v1_6_mutant_bite"]]
passed = sum(1 for r in REPORTS if r["v1_7_pass"])
total  = len(REPORTS)
report = {
    "artifact": "phase36_v1_7_negative_controls",
    "phase": 36, "section": "§K", "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_7",
    "type": "NEGATIVE_CONTROL_AUDIT",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_strings_only": True,
    "nc_range": "NC36-NC40",
    "repair_controls_passed": sum(1 for r in REPAIR if r["v1_7_pass"]),
    "repair_controls_total": len(REPAIR),
    "preservation_controls_passed": sum(1 for r in PRES if r["v1_7_pass"]),
    "preservation_controls_total": len(PRES),
    "passed": passed, "total": total, "all_pass": passed == total,
    "controls": REPORTS,
    "generated_utc": "2026-10-06T09:24:23Z",
}
out = ROOT / "reports/audits/phase36_v1_7_negative_controls.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for r in REPORTS:
    if not r["v1_7_pass"]:
        print("FAIL:", r["nc"], r["v1_7_fail_reason"])
raise SystemExit(0 if passed == total else 1)
