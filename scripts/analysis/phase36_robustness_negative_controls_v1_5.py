#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.5 — negative controls NC25-NC30 (model-free, static/unit).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_5

NC25-NC29 each prove a KNOWN-BAD pattern is BOTH (a) demonstrably present in the
frozen v1.4 source bytes / call graph and (b) ABSENT from / correctly repaired by
the v1.5 source bytes / call graph.  A control PASSES only when v1.4 FAILS it and
v1.5 PASSES it.

  NC25_NUMPY_OR_MANUAL_SIGMOID
       v1.4 reconstructs the canonical G probability with a NumPy float64
       logistic; v1.5 uses only the frozen torch.sigmoid(logits.float()).
  NC26_DUPLICATE_G_PROBABILITY_OPERATOR
       more than one executable implementation converts canonical G logits to
       probability.
  NC27_CUDA_NOT_FAIL_CLOSED
       a source using plain get_device() without proving canonical
       require_cuda=True, or permitting a CPU fallback.
  NC28_COMPONENT_DEVICE_BINDING
       the four learned components are not explicitly moved/verified on the
       canonical CUDA device.
  NC29_COMPONENT_INFERENCE_CONTEXTS
       G must be no_grad + fp16 autocast + NOT inference_mode;
       B_phi / R_psi / S_omega must be inference_mode + autocast disabled.

NC30_V1_4_VALID_REPAIRS_PRESERVED is a PRESERVATION control: it verifies every
v1.4 conditional-execution / smoke / KUB / figure repair remains present in v1.5.

NO torch. NO model. NO protected-data read.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_5 as E  # noqa: E402

V14 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_4.py").read_text(encoding="utf-8")
V15 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_5.py").read_text(encoding="utf-8")
T14 = ast.parse(V14)
T15 = ast.parse(V15)
F14 = {n.name: n for n in ast.walk(T14) if isinstance(n, ast.FunctionDef)}
F15 = {n.name: n for n in ast.walk(T15) if isinstance(n, ast.FunctionDef)}

results = []


def record(name, v14_fails, v15_passes, note, evidence=None, kind="REPAIR_CONTROL"):
    results.append({
        "control": name,
        "kind": kind,
        "v1_4_fails_control": bool(v14_fails),
        "v1_5_passes_control": bool(v15_passes),
        "pass": bool(v14_fails and v15_passes),
        "note": note,
        "evidence": evidence or {},
    })


def _manual_sites(tree):
    out = []
    for n in ast.walk(tree):
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


def _canonical_sites(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "sigmoid":
            seg = ast.unparse(n)
            if seg.startswith("torch.sigmoid(t.float())") or \
               seg.startswith("torch.sigmoid(g_out.float())"):
                out.append((n.lineno, seg))
    return out


def _cpu_device_calls(tree):
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == "device" and isinstance(n.func.value, ast.Name) \
                and n.func.value.id == "torch":
            for a in n.args:
                if isinstance(a, ast.Constant) and str(a.value).startswith("cpu"):
                    out.append((n.lineno, ast.unparse(n)))
    return out


def _get_device_calls(tree):
    """Executable get_device(...) calls with their keyword arguments."""
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id == "get_device":
            kwargs = {k.arg: ast.unparse(k.value) for k in n.keywords}
            out.append({"line": n.lineno, "kwargs": kwargs})
    return out


def _has(src, token):
    return token in src


# --------------------------------------------------------------------------- #
# NC25 — NumPy / manual sigmoid for the canonical G probability
# --------------------------------------------------------------------------- #
m14 = _manual_sites(T14)
m15 = _manual_sites(T15)
record(
    "NC25_NUMPY_OR_MANUAL_SIGMOID",
    len(m14) > 0,
    (len(m15) == 0 and "prob = torch.sigmoid(t.float())" in V15
     and "CANONICAL_PROBABILITY_OPERATOR" in V15),
    "v1.4 reconstructed the canonical G probability with a NumPy float64 logistic at 3 "
    "sites; v1.5 has zero manual/NumPy sigmoid sites and uses only the frozen "
    "torch.sigmoid(logits.float()) operator.",
    {"v1_4_manual_sites": m14, "v1_5_manual_sites": m15})

# --------------------------------------------------------------------------- #
# NC26 — duplicate canonical G probability operator
# --------------------------------------------------------------------------- #
c14 = _canonical_sites(T14)
c15 = _canonical_sites(T15)
n14_impls = len(m14) + len(c14)
n15_impls = len(m15) + len(c15)
record(
    "NC26_DUPLICATE_G_PROBABILITY_OPERATOR",
    n14_impls != 1,
    n15_impls == 1,
    "v1.4 contains %d independent executable conversions of canonical G logits to "
    "probability (all divergent manual logits); v1.5 contains exactly ONE "
    "(the central torch.sigmoid authority)." % n14_impls,
    {"v1_4_implementation_count": n14_impls, "v1_5_implementation_count": n15_impls,
     "v1_4_manual": len(m14), "v1_4_canonical": len(c14),
     "v1_5_manual": len(m15), "v1_5_canonical": len(c15)})

# --------------------------------------------------------------------------- #
# NC27 — CUDA not fail-closed
# --------------------------------------------------------------------------- #
v14_cpu = _cpu_device_calls(T14)
v15_cpu = _cpu_device_calls(T15)
gd14 = _get_device_calls(T14)
gd15 = _get_device_calls(T15)
v14_not_fail_closed = bool(gd14) and all(
    c["kwargs"].get("require_cuda") != "True" for c in gd14)
v15_fail_closed = (bool(gd15)
                   and all(c["kwargs"].get("require_cuda") == "True" for c in gd15)
                   and len(v15_cpu) == 0
                   and _has(V15, "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE"))
record(
    "NC27_CUDA_NOT_FAIL_CLOSED",
    v14_not_fail_closed,
    v15_fail_closed,
    "v1.4 resolved the device with a plain get_device() and carried an executable "
    "torch.device('cpu') fallback; v1.5 uses the literal get_device(require_cuda=True), "
    "asserts device.type == 'cuda', and has no CPU fallback.",
    {"v1_4_get_device_calls": gd14, "v1_5_get_device_calls": gd15,
     "v1_4_cpu_device_calls": v14_cpu, "v1_5_cpu_device_calls": v15_cpu})

# --------------------------------------------------------------------------- #
# NC28 — component device binding
# --------------------------------------------------------------------------- #
bind15 = {c: _has(V15, f"{c}.to(device)") for c in ("g", "b_phi", "r_psi", "s_omega")}
bind14 = {c: _has(V14, f"{c}.to(device)") for c in ("g", "b_phi", "r_psi", "s_omega")}
record(
    "NC28_COMPONENT_DEVICE_BINDING",
    not all(bind14.values()),
    (all(bind15.values())
     and _has(V15, "COMPONENT_DEVICE_BINDING_FAILED")
     and _has(V15, "_param_device")),
    "v1.4 relied on system.to(device) only (which cannot move G through the plain-Python "
    "_WrapG adapter) and never explicitly bound the four components; v1.5 moves and "
    "VERIFIES G / B_phi / R_psi / S_omega on the canonical CUDA device.",
    {"v1_4_explicit_binding": bind14, "v1_5_explicit_binding": bind15})

# --------------------------------------------------------------------------- #
# NC29 — component-specific inference contexts
# --------------------------------------------------------------------------- #
def _grad_contexts(src):
    """Map each non-G component forward site to its enclosing `with torch.*` line."""
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    node = funcs.get("canonical_learned_core")
    if node is None:
        return {}
    lines = src.splitlines()
    out = {}
    for i in range(node.lineno, node.end_lineno + 1):
        L = lines[i - 1]
        target = None
        if "system.benefit_router(" in L:
            target = "B_phi"
        elif 'ctx["r_psi"](' in L:
            target = "R_psi"
        elif "system.post_safety(" in L:
            target = "S_omega"
        if target and target not in out:
            for j in range(i - 1, node.lineno - 1, -1):
                stripped = lines[j - 1].strip()
                if stripped.startswith("with ") and (
                        "torch." in stripped
                        or "component_inference_context(" in stripped):
                    out[target] = {"forward_line": i, "context_line": j,
                                   "context": stripped}
                    break
    return out


ctx14 = _grad_contexts(V14)
ctx15 = _grad_contexts(V15)
v14_all_nograd = bool(ctx14) and all("no_grad" in v["context"] for v in ctx14.values())
v15_all_inference = (bool(ctx15)
                     and all('component_inference_context(' in v["context"]
                             for v in ctx15.values())
                     and all('component_autocast_disabled(' in v["context"]
                             for v in ctx15.values()))
CTX = E.COMPONENT_INFERENCE_CONTEXTS
record(
    "NC29_COMPONENT_INFERENCE_CONTEXTS",
    v14_all_nograd,
    (v15_all_inference
     and CTX["G"]["inference_mode"] is False and CTX["G"]["autocast_enabled"] is True
     and all(CTX[c]["inference_mode"] is True and CTX[c]["autocast_enabled"] is False
             for c in ("B_phi", "R_psi", "S_omega"))),
    "v1.4 ran B_phi / R_psi / S_omega under torch.no_grad(); v1.5 runs them under "
    "torch.inference_mode() with autocast explicitly disabled, while G keeps "
    "no_grad + fp16 autocast + inference_mode FALSE.",
    {"v1_4_contexts": ctx14, "v1_5_contexts": ctx15})

# --------------------------------------------------------------------------- #
# NC30 — v1.4 valid repairs preserved (PRESERVATION control)
# --------------------------------------------------------------------------- #
REPAIRS = {
    "conditional_execution_order": ("TAU_C8_FINAL_FLOAT" in V15
                                    and "refiner=0, somega=0" in V15),
    "router_decision_separate": ('ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in V15
                                 and "ROUTER_DECISION_NOT_CANONICAL" in V15),
    "exact_branch_comparator": ("n_state_machine_branch_comparisons_808" in V15
                                and "accept_reject_collapse_prohibited" in V15),
    "real_proposal_smoke": "def smoke_nonempty_proposal_pipeline" in V15,
    "real_empty_proposal_smoke": ("def smoke_empty_proposal_pipeline" in V15
                                  and "proposal_geometry=None" in V15),
    "three_branch_controls": all(s in V15 for s in (
        "CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT", "CONTROL_EXECUTE_THEN_REJECT")),
    "sample_level_image_loop": "def run_image_perturbations" in V15,
    "sample_level_proposal_loop": "def run_proposal_perturbations" in V15,
    "case_b_manifest_authority": "EXACT_VAL808_MANIFEST_MEMBERSHIP_PLUS_EXACT_ROW_PATHS" in V15,
    "holdout_875_deny": "ROUTER_HOLDOUT_IDENTITY_EXPECTED_N = 875" in V15,
    "test_1683_deny": "TEST_MANIFEST" in V15,
    "kub_subgroup_reporting": ("def kub_subgroup_map" in V15 and '"kub_subgroup"' in V15),
    "r1_r5_figure_path": all(f"def figure_R{i}" in V15 for i in range(1, 6)),
    "canonical_batch_partition": "def canonical_batch_partition" in V15,
    "clean_g_reproduction_gate": "CLEAN_G_NOT_BIT_IDENTICAL_TO_PHASE27_AUTHORITY" in V15,
}
present14 = {
    "conditional_execution_order": "TAU_C8_FINAL_FLOAT" in V14,
    "router_decision_separate": 'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in V14,
    "exact_branch_comparator": "n_state_machine_branch_comparisons_808" in V14,
    "real_proposal_smoke": "def smoke_nonempty_proposal_pipeline" in V14,
    "real_empty_proposal_smoke": "def smoke_empty_proposal_pipeline" in V14,
    "three_branch_controls": all(s in V14 for s in (
        "CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT", "CONTROL_EXECUTE_THEN_REJECT")),
    "sample_level_image_loop": "def run_image_perturbations" in V14,
    "sample_level_proposal_loop": "def run_proposal_perturbations" in V14,
    "case_b_manifest_authority": "EXACT_VAL808_MANIFEST_MEMBERSHIP_PLUS_EXACT_ROW_PATHS" in V14,
    "holdout_875_deny": "ROUTER_HOLDOUT_IDENTITY_EXPECTED_N = 875" in V14,
    "test_1683_deny": "TEST_MANIFEST" in V14,
    "kub_subgroup_reporting": "def kub_subgroup_map" in V14,
    "r1_r5_figure_path": all(f"def figure_R{i}" in V14 for i in range(1, 6)),
    "canonical_batch_partition": "def canonical_batch_partition" in V14,
    "clean_g_reproduction_gate": "CLEAN_G_NOT_BIT_IDENTICAL_TO_PHASE27_AUTHORITY" in V14,
}
results.append({
    "control": "NC30_V1_4_VALID_REPAIRS_PRESERVED",
    "kind": "PRESERVATION_CONTROL",
    "v1_4_fails_control": False,
    "v1_5_passes_control": bool(all(REPAIRS.values())),
    "pass": bool(all(REPAIRS.values()) and all(present14.values())),
    "note": "Preservation control (not a v1.4-fails control): every v1.4 "
            "conditional-execution / smoke / KUB / figure repair is present in v1.5.",
    "evidence": {"repairs_present_in_v1_5": REPAIRS, "repairs_present_in_v1_4": present14},
})

repair_controls = [r for r in results if r["kind"] == "REPAIR_CONTROL"]
passed = sum(1 for r in results if r["pass"])
report = {
    "artifact": "phase36_robustness_negative_controls_v1_5",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_5",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "subject_v1_4_sha256":
        "96ebc36256e5d812949e1f1859d4f41f332f81607e562dbff7cfb2bce6483fbe",
    "controls": results,
    "repair_controls_passed": sum(1 for r in repair_controls if r["pass"]),
    "repair_controls_total": len(repair_controls),
    "passed": passed,
    "total": len(results),
    "all_pass": passed == len(results),
    "nc_range": "NC25-NC30",
    "each_repair_control_requires": "v1_4_fails_control AND v1_5_passes_control",
}
out = ROOT / "reports/audits/phase36_v1_5_negative_controls.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": len(results),
                  "repair_controls": f"{report['repair_controls_passed']}/"
                                     f"{report['repair_controls_total']}",
                  "all_pass": passed == len(results)}, indent=1))
for r in results:
    if not r["pass"]:
        print("FAIL:", r["control"], json.dumps(r, default=str))
raise SystemExit(0 if passed == len(results) else 1)
