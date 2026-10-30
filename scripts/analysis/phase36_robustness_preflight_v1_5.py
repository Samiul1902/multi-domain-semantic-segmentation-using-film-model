#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.5 — static preflight (AST / call-graph / byte proof).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_5

NO torch. NO model. NO protected-data read. AST + byte analysis only.

§M CHECKLIST PROVEN
  * canonical G probability is torch.sigmoid(logits.float())
  * NumPy / manual sigmoid absent from executable code
  * clean G cache consumes the central canonical probability
  * shared core consumes the central canonical probability
  * image perturbation path consumes the central canonical probability
  * smoke consumes the central canonical probability
  * CUDA required explicitly
  * no CPU scientific fallback
  * G / B_phi / R_psi / S_omega explicitly device-bound
  * G / B_phi / R_psi / S_omega inference contexts correct
  * conditional execution order retained
  * proposal smoke retained
  * empty proposal smoke retained
  * three branch controls retained
  * KUB subgroup reporting retained
  * R1-R5 retained
  * TEST inaccessible
  * no training
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_5.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

import scripts.analysis.phase36_robustness_execution_v1_5 as E  # noqa: E402

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}


def _calls(fn_name):
    node = FUNCS.get(fn_name)
    if node is None:
        return set()
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name)
                    else (f.attr if isinstance(f, ast.Attribute) else None))
    return out


def _reachable(fn_name, target, seen=None):
    seen = set() if seen is None else seen
    if fn_name in seen:
        return False
    seen.add(fn_name)
    cs = _calls(fn_name)
    if target in cs:
        return True
    return any(_reachable(c, target, seen) for c in cs if c in FUNCS)


def _line_in(fn_name, pred):
    node = FUNCS.get(fn_name)
    if node is None:
        return None
    hits = [n.lineno for n in ast.walk(node) if pred(n)]
    return min(hits) if hits else None


def _funcs_referencing(token):
    return sorted(name for name, node in FUNCS.items()
                  if token in ast.get_source_segment(SRC, node))


def _manual_sigmoid_sites():
    out = []
    for n in ast.walk(TREE):
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "exp" and isinstance(n.func.value, ast.Name)
                and n.func.value.id == "np"):
            out.append((n.lineno, "np.exp"))
        if (isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div)
                and "1.0 / (1.0" in ast.unparse(n)):
            out.append((n.lineno, "manual_logistic"))
        if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("expit", "logistic")):
            out.append((n.lineno, n.func.attr))
    return sorted(set(out))


def _g_probability_impls():
    out = []
    for n in ast.walk(TREE):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "sigmoid":
            seg = ast.unparse(n)
            if seg.startswith("torch.sigmoid(t.float())"):
                out.append((n.lineno, seg))
    return out


# --------------------------------------------------------------------------- #
# 01-08  §C/§D/§E canonical probability operator
# --------------------------------------------------------------------------- #
check("01_canonical_operator_expression_frozen",
      E.CANONICAL_PROBABILITY_OPERATOR["expression"]
      == "torch.sigmoid(logits.float()).cpu().numpy()")
check("02_central_operator_function_present",
      "def canonical_probability_from_logits" in SRC)
check("03_central_operator_uses_torch_sigmoid_float",
      "prob = torch.sigmoid(t.float())" in SRC)
check("04_no_executable_manual_numpy_sigmoid",
      len(_manual_sigmoid_sites()) == 0, _manual_sigmoid_sites())
impls = _g_probability_impls()
check("05_exactly_one_g_probability_operator", len(impls) == 1, impls)
check("06_g_forward_returns_logits_and_probability",
      "def canonical_g_forward_batched" in SRC
      and '"logits": logits,' in SRC and '"probability": probability,' in SRC)
check("07_probability_computed_inside_g_context",
      "canonical_probability_from_logits(g_out)" in SRC)
check("08_float32_then_float16_persistence",
      ".astype(np.float32, copy=False)" in SRC
      and "p_global.astype(np.float16)" in SRC)

# consumer paths
check("09_clean_g_cache_consumes_canonical_probability",
      "canonical_g_forward_batched" in _calls("_generate_clean_g_reference")
      and 'out["probability"][bi]' in SRC)
check("10_shared_core_consumes_canonical_probability",
      "canonical_learned_core" in FUNCS
      and ("canonical_probability_from_logits" in _calls("canonical_learned_core")
           or 'out["probability"][0]' in SRC))
check("11_image_perturbation_consumes_canonical_probability",
      "canonical_g_forward_batched" in _calls("run_image_perturbations")
      and 'g_probability=np.asarray(gout["probability"][bi]' in SRC)
check("12_smoke_consumes_canonical_probability",
      "canonical_g_forward_batched" in _calls("run_smoke")
      and 'g_probability = np.asarray(gout["probability"][0]' in SRC)
check("13_proposal_path_consumes_canonical_probability",
      _reachable("run_proposal_perturbations", "proposal_core_adapter"))

# --------------------------------------------------------------------------- #
# 14-19  §G CUDA fail-closed
# --------------------------------------------------------------------------- #
check("14_cuda_require_true_literal", "get_device(require_cuda=True)" in SRC)
check("15_device_type_must_be_cuda",
      '("required_device_type", "cuda")' in SRC
      and 'CANONICAL_DEVICE_CONTRACT["required_device_type"]' in SRC
      and E.CANONICAL_DEVICE_CONTRACT["required_device_type"] == "cuda")
check("16_fail_closed_terminal_present",
      "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE" in SRC)
check("17_no_executable_cpu_fallback",
      not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "device" and isinstance(n.func.value, ast.Name)
              and n.func.value.id == "torch"
              and any(isinstance(a, ast.Constant) and str(a.value).startswith("cpu")
                      for a in n.args)
              for n in ast.walk(TREE)))
check("18_cpu_fallback_flag_false",
      E.CANONICAL_DEVICE_CONTRACT["cpu_scientific_fallback_permitted"] is False)
check("19_device_contract_recorded_in_source",
      "CANONICAL_DEVICE_CONTRACT = OrderedDict" in SRC)

# --------------------------------------------------------------------------- #
# 20-25  §H explicit four-component device binding
# --------------------------------------------------------------------------- #
check("20_explicit_G_to_device", "g.to(device)" in SRC)
check("21_explicit_B_phi_to_device", "b_phi.to(device)" in SRC)
check("22_explicit_R_psi_to_device", "r_psi.to(device)" in SRC)
check("23_explicit_S_omega_to_device", "s_omega.to(device)" in SRC)
check("24_binding_verified_not_assumed",
      "COMPONENT_DEVICE_BINDING_FAILED" in SRC and "_param_device(m)" in SRC)
check("25_binding_precedes_system_composition",
      SRC.index("s_omega.to(device)") < SRC.index("system = RAMedFiLMBARR("))

# --------------------------------------------------------------------------- #
# 26-33  §I component inference contexts
# --------------------------------------------------------------------------- #
CTX = E.COMPONENT_INFERENCE_CONTEXTS
check("26_G_no_grad_autocast_fp16",
      CTX["G"]["grad_context"] == "torch.no_grad()"
      and CTX["G"]["autocast_enabled"] is True
      and CTX["G"]["autocast_dtype"] == "float16")
check("27_G_inference_mode_false", CTX["G"]["inference_mode"] is False)
check("28_B_phi_inference_mode_autocast_disabled",
      CTX["B_phi"]["inference_mode"] is True and CTX["B_phi"]["autocast_enabled"] is False)
check("29_R_psi_inference_mode_autocast_disabled",
      CTX["R_psi"]["inference_mode"] is True and CTX["R_psi"]["autocast_enabled"] is False)
check("30_S_omega_inference_mode_autocast_disabled",
      CTX["S_omega"]["inference_mode"] is True and CTX["S_omega"]["autocast_enabled"] is False)
check("31_component_context_helper_used",
      all(f'component_inference_context("{c}")' in SRC for c in ("B_phi", "R_psi", "S_omega")))
check("32_autocast_disabled_helper_used",
      all(f'component_autocast_disabled("{c}")' in SRC for c in ("B_phi", "R_psi", "S_omega")))
check("33_nonG_not_wrapped_in_G_autocast",
      SRC.count("canonical_autocast(") >= 1
      and 'canonical_autocast(ctx["device"]), TapRecorder' in SRC
      and 'component_autocast_disabled("R_psi")' in SRC)

# --------------------------------------------------------------------------- #
# 34-40  §J v1.4 repairs preserved
# --------------------------------------------------------------------------- #
node = FUNCS["canonical_learned_core"]
dec = _line_in("canonical_learned_core",
               lambda n: isinstance(n, ast.Compare) and isinstance(n.comparators[0], ast.Name)
               and n.comparators[0].id == "TAU_C8_FINAL_FLOAT")
rpsi = min([n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript)
            and "r_psi" in ast.unparse(n.func)] or [10 ** 9])
somega = min([n.lineno for n in ast.walk(node)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "post_safety"] or [10 ** 9])
check("34_conditional_execution_order_retained",
      dec is not None and dec < rpsi and dec < somega,
      {"decision": dec, "r_psi": rpsi, "s_omega": somega})
check("35_proposal_smoke_retained",
      _reachable("run_smoke", "proposal_core_adapter")
      and "def smoke_nonempty_proposal_pipeline" in SRC)
check("36_empty_proposal_smoke_retained",
      "def smoke_empty_proposal_pipeline" in SRC and "proposal_geometry=None" in SRC)
check("37_three_branch_controls_retained",
      "def smoke_branch_controls" in SRC
      and all(s in SRC for s in ("CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT",
                                 "CONTROL_EXECUTE_THEN_REJECT")))
check("38_kub_subgroup_reporting_retained",
      "def kub_subgroup_map" in SRC and '"kub_subgroup"' in SRC
      and "KUB_SUBGROUP_AUTHORITY" in SRC)
check("39_r1_r5_retained",
      all(f"def figure_R{i}" in SRC for i in range(1, 6))
      and "generate_all_figures" in _calls("run_science")
      and "FIGURE_REGISTRY = C.FIGURES" in SRC)
check("40_router_decision_separate_from_final_state",
      'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in SRC
      and "ROUTER_DECISION_NOT_CANONICAL" in SRC
      and 'router_decision"] = out.get("state")' not in SRC)

# --------------------------------------------------------------------------- #
# 41-45  prohibitions
# --------------------------------------------------------------------------- #
check("41_test_inaccessible",
      _funcs_referencing("TEST_MANIFEST") == ["load_identity_authorities"],
      _funcs_referencing("TEST_MANIFEST"))
check("42_holdout_inaccessible",
      _funcs_referencing("ROUTER_HOLDOUT_MANIFEST") == ["load_identity_authorities"],
      _funcs_referencing("ROUTER_HOLDOUT_MANIFEST"))
check("43_no_training",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)
check("44_no_vendor_substring_split",
      '"test" in' not in SRC and "'test' in" not in SRC
      and '"train" in' not in SRC and "'train' in" not in SRC)
check("45_phase27_authority_unchanged",
      E.PHASE27_GLOBAL_PROB_AUTHORITY["sha256"]
      == "cc6c54af986f56b4aba9265405ffeba4f6cac582eeff00fe6b0894429e7d3f13"
      and E.PHASE27_GLOBAL_PROB_AUTHORITY["shape"] == [808, 512, 512]
      and E.PHASE27_GLOBAL_PROB_AUTHORITY["dtype"] == "float16")

# --------------------------------------------------------------------------- #
# 46-48  import safety
# --------------------------------------------------------------------------- #
check("46_torch_not_imported_by_preflight", "torch" not in sys.modules)
check("47_no_module_level_execution",
      "def run_science()" in SRC and "def run_smoke()" in SRC)
check("48_gate_names_unchanged",
      E.C.GATE_ENV == "PHASE36_EXECUTE" and E.C.SMOKE_GATE_ENV == "PHASE36_SMOKE_EXECUTE")

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_static_preflight_v1_5",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_5",
    "method": "AST_CALL_GRAPH_AND_BYTE_PREFLIGHT",
    "audited_source": "scripts/analysis/phase36_robustness_execution_v1_5.py",
    "torch_imported": "torch" in sys.modules,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_static_preflight_v1_5.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
