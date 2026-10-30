#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.6 — negative controls NC31-NC35 (model-free, static/unit).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_6

NC31-NC33 each prove a KNOWN-BAD pattern is BOTH (a) demonstrably present in a
mutant source and (b) ABSENT from / correctly repaired by v1.6.  A control PASSES
only when the mutant FAILS the detector and v1.6 PASSES it.

  NC31_TEST_RUNTIME_READ_REACHABILITY
       a source in which run_science can reach an open/read/hash/stat/exists
       operation on the TEST manifest MUST FAIL.
  NC32_ROUTER_HOLDOUT_RUNTIME_READ_REACHABILITY
       a source in which run_science can reach such an operation on the
       ROUTER_HOLDOUT manifest or the Phase24 holdout identity authority MUST FAIL.
  NC33_PROTECTED_COUNTER_POSTHOC_FORCE_ZERO
       a source containing a post-execution ``counters["test_reads"] = 0`` or
       ``counters["router_holdout_reads"] = 0`` MUST FAIL.
       Initialization at counter construction is allowed.

NC34_VAL808_ONLY_RUNTIME_AUTHORITY and
NC35_V1_5_NUMERICAL_DEVICE_CONTEXT_PRESERVATION are PRESERVATION controls.

Mutant sources are used as IN-MEMORY STRINGS only.  No TEST or ROUTER_HOLDOUT
artifact content is inspected (source/AST reasoning only).

NO torch. NO model. NO protected-population read.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

import scripts.analysis.phase36_robustness_execution_v1_6 as E  # noqa: E402
import scripts.analysis.phase36_robustness_common_v1_1 as C  # noqa: E402

V16 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_6.py").read_text(encoding="utf-8")
V15 = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_5.py").read_text(encoding="utf-8")

PROTECTED_SYMBOLS = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST",
                     "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROTECTED_PATH_TOKENS = ("val_router_holdout", "phase24_router_split_manifest",
                         "phase4_v3/test.csv")

# ---- synthesized mutants (in-memory only; never written to disk) ------------ #
MUTANT_TEST_DIRECT = '''
import csv
TEST_MANIFEST = "manifests/phase4_v3/test.csv"

def _rows(p):
    return list(csv.DictReader(open(p)))

def _load_protected():
    return _rows(TEST_MANIFEST)

def run_science():
    return _load_protected()
'''

MUTANT_HOLDOUT_DIRECT = '''
import csv
ROUTER_HOLDOUT_MANIFEST = "manifests/phase4_v3/val_router_holdout.csv"
ROUTER_HOLDOUT_IDENTITY_AUTHORITY = "reports/audits/phase24_router_split_manifest.csv"

def _identity_deny_set(path_rel):
    return set(open(path_rel))

def load_identity_authorities():
    return _identity_deny_set(ROUTER_HOLDOUT_MANIFEST) | _identity_deny_set(ROUTER_HOLDOUT_IDENTITY_AUTHORITY)

def _load_population():
    return load_identity_authorities()

def run_science():
    return _load_population()
'''

MUTANT_TEST_PATH_LITERAL = '''
import os

def _probe():
    return os.path.exists("manifests/phase4_v3/test.csv")

def run_science():
    return _probe()
'''

MUTANT_POSTHOC_COUNTER = '''
def run_science():
    counters = {}
    counters["test_reads"] = 0
    counters["router_holdout_reads"] = 0
    return counters
'''

results = []


def _parse(src):
    tree = ast.parse(src)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    return tree, funcs


def _calls(funcs, fn):
    node = funcs.get(fn)
    if node is None:
        return set()
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            f = n.func
            out.add(f.id if isinstance(f, ast.Name)
                    else (f.attr if isinstance(f, ast.Attribute) else None))
    return out


def _reachable(funcs, entry):
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen or f not in funcs:
            continue
        seen.add(f)
        for c in _calls(funcs, f):
            if c in funcs and c not in seen:
                stack.append(c)
    return seen


def _protected_sites(src, entry="run_science"):
    """Detector: protected-population IO reachable from ``entry``."""
    tree, funcs = _parse(src)
    hits = []
    for name in sorted(_reachable(funcs, entry)):
        for x in ast.walk(funcs[name]):
            if isinstance(x, ast.Name) and x.id in PROTECTED_SYMBOLS:
                hits.append({"function": name, "line": x.lineno,
                             "kind": "protected_symbol", "detail": x.id})
            if isinstance(x, ast.Constant) and isinstance(x.value, str):
                for t in PROTECTED_PATH_TOKENS:
                    if t in x.value:
                        hits.append({"function": name, "line": x.lineno,
                                     "kind": "protected_path_literal",
                                     "detail": x.value[:70]})
    return hits


def _posthoc_force_zero(src):
    tree, _ = _parse(src)
    out = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "counters"):
                key = t.slice.value if isinstance(t.slice, ast.Constant) else None
                if key in ("router_holdout_reads", "test_reads") \
                        and ast.unparse(n.value) == "0":
                    out.append({"line": n.lineno, "statement": ast.unparse(n)})
    return out


def record(name, mutant_fails, v16_passes, note, evidence=None, kind="REPAIR_CONTROL"):
    results.append({
        "control": name, "kind": kind,
        "mutant_fails_control": bool(mutant_fails),
        "v1_6_passes_control": bool(v16_passes),
        "pass": bool(mutant_fails and v16_passes),
        "note": note, "evidence": evidence or {},
    })


# --------------------------------------------------------------------------- #
# NC31 — TEST runtime read reachability
# --------------------------------------------------------------------------- #
m_test_a = _protected_sites(MUTANT_TEST_DIRECT)
m_test_b = _protected_sites(MUTANT_TEST_PATH_LITERAL)
m_test_hist = _protected_sites(V15)          # the real historical v1.5 mutant
v16_test = _protected_sites(V16)
record(
    "NC31_TEST_RUNTIME_READ_REACHABILITY",
    (len(m_test_a) > 0 and len(m_test_b) > 0 and len(m_test_hist) > 0),
    len([h for h in v16_test if h["detail"] == "TEST_MANIFEST"
         or "test" in str(h["detail"]).lower()]) == 0,
    "A source in which run_science can reach a TEST-manifest open/read/exists "
    "operation is detected and FAILS.  v1.6 has zero reachable TEST references.",
    {"mutant_direct_open_sites": m_test_a,
     "mutant_path_literal_sites": m_test_b,
     "v1_5_historical_sites": len(m_test_hist),
     "v1_6_sites": v16_test})

# --------------------------------------------------------------------------- #
# NC32 — ROUTER_HOLDOUT runtime read reachability
# --------------------------------------------------------------------------- #
m_hold_a = _protected_sites(MUTANT_HOLDOUT_DIRECT)
m_hold_hist = [h for h in _protected_sites(V15) if "holdout" in str(h["detail"]).lower()]
v16_hold = [h for h in v16_test if "holdout" in str(h["detail"]).lower()]
record(
    "NC32_ROUTER_HOLDOUT_RUNTIME_READ_REACHABILITY",
    (len(m_hold_a) > 0 and len(m_hold_hist) > 0),
    len(v16_hold) == 0,
    "A source in which run_science can reach a ROUTER_HOLDOUT / Phase24 holdout "
    "identity-authority open/read operation is detected and FAILS.  v1.6 has zero "
    "reachable ROUTER_HOLDOUT references.",
    {"mutant_direct_sites": m_hold_a,
     "v1_5_historical_sites": m_hold_hist,
     "v1_6_sites": v16_hold})

# --------------------------------------------------------------------------- #
# NC33 — protected counter post-hoc force-zero
# --------------------------------------------------------------------------- #
m_counter = _posthoc_force_zero(MUTANT_POSTHOC_COUNTER)
v16_counter = _posthoc_force_zero(V16)
v15_counter = _posthoc_force_zero(V15)
record(
    "NC33_PROTECTED_COUNTER_POSTHOC_FORCE_ZERO",
    (len(m_counter) > 0 and len(v15_counter) > 0),
    len(v16_counter) == 0,
    "A source containing a post-execution counters['test_reads'] = 0 or "
    "counters['router_holdout_reads'] = 0 assignment is detected and FAILS.  v1.6 "
    "has zero such assignments; protected counters are only initialized to zero at "
    "run start.",
    {"mutant_sites": m_counter, "v1_5_historical_sites": v15_counter,
     "v1_6_sites": v16_counter})

# --------------------------------------------------------------------------- #
# NC34 — VAL808-only runtime authority (PRESERVATION control)
# --------------------------------------------------------------------------- #
n34 = {
    "val_manifest_sha_guard": "VAL_MANIFEST_SHA_MISMATCH" in V16,
    "expected_n_808": E.VAL_RUNTIME_EXPECTED_N == 808,
    "unique_sample_id_guard": "VAL808_SAMPLE_ID_NOT_UNIQUE" in V16,
    "split_val_guard": "NON_VAL_ROW_REJECTED" in V16,
    "manifest_row_paths": ("VAL808_MISSING_IMAGE_PATH" in V16
                           and "VAL808_MISSING_MASK_PATH" in V16),
    "no_vendor_substring_rule": ('"test" in' not in V16 and "'test' in" not in V16),
    "no_protected_deny_set_io": (len(_protected_sites(V16)) == 0
                                 and "def load_identity_authorities" not in V16),
    "only_population_authority": (E.VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY
                                  is True
                                  and E.VAL_RUNTIME_AUTHORITY["path"] == C.VAL_MANIFEST),
}
results.append({
    "control": "NC34_VAL808_ONLY_RUNTIME_AUTHORITY",
    "kind": "PRESERVATION_CONTROL",
    "mutant_fails_control": False,
    "v1_6_passes_control": bool(all(n34.values())),
    "pass": bool(all(n34.values())),
    "note": "v1.6 runtime population authority is exactly the frozen VAL808 manifest "
            "(SHA guard, n=808, unique sample_id, split==VAL, manifest-row paths, no "
            "vendor substring rule, no protected deny-set IO).",
    "evidence": n34,
})

# --------------------------------------------------------------------------- #
# NC35 — v1.5 numerical / device / context preservation (PRESERVATION control)
# --------------------------------------------------------------------------- #
n35 = {
    "canonical_torch_sigmoid": ("prob = torch.sigmoid(t.float())" in V16
                                and E.CANONICAL_PROBABILITY_OPERATOR["expression"]
                                == "torch.sigmoid(logits.float()).cpu().numpy()"),
    "single_probability_authority": "def canonical_probability_from_logits" in V16,
    "no_manual_numpy_sigmoid": not any(
        isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
        and n.func.attr == "exp" and isinstance(n.func.value, ast.Name)
        and n.func.value.id == "np" for n in ast.walk(ast.parse(V16))),
    "cuda_fail_closed": ("get_device(require_cuda=True)" in V16
                         and "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE" in V16),
    "four_component_binding": all(t in V16 for t in (
        "g.to(device)", "b_phi.to(device)", "r_psi.to(device)", "s_omega.to(device)")),
    "G_context": (E.COMPONENT_INFERENCE_CONTEXTS["G"]["inference_mode"] is False
                  and E.COMPONENT_INFERENCE_CONTEXTS["G"]["autocast_enabled"] is True),
    "B_phi_context": (E.COMPONENT_INFERENCE_CONTEXTS["B_phi"]["inference_mode"] is True
                      and E.COMPONENT_INFERENCE_CONTEXTS["B_phi"]["autocast_enabled"] is False),
    "R_psi_context": (E.COMPONENT_INFERENCE_CONTEXTS["R_psi"]["inference_mode"] is True
                      and E.COMPONENT_INFERENCE_CONTEXTS["R_psi"]["autocast_enabled"] is False),
    "S_omega_context": (E.COMPONENT_INFERENCE_CONTEXTS["S_omega"]["inference_mode"] is True
                        and E.COMPONENT_INFERENCE_CONTEXTS["S_omega"]["autocast_enabled"] is False),
    "conditional_execution": "refiner=0, somega=0" in V16,
    "proposal_paths": ("def proposal_core_adapter" in V16
                       and "def smoke_empty_proposal_pipeline" in V16),
    "branch_controls": "def smoke_branch_controls" in V16,
}
results.append({
    "control": "NC35_V1_5_NUMERICAL_DEVICE_CONTEXT_PRESERVATION",
    "kind": "PRESERVATION_CONTROL",
    "mutant_fails_control": False,
    "v1_6_passes_control": bool(all(n35.values())),
    "pass": bool(all(n35.values())),
    "note": "All canonical v1.5 repairs (probability operator, CUDA fail-closed, "
            "four-component device binding, per-component inference contexts, "
            "conditional execution, proposal paths, branch controls) are unchanged.",
    "evidence": n35,
})

repair_controls = [r for r in results if r["kind"] == "REPAIR_CONTROL"]
passed = sum(1 for r in results if r["pass"])
report = {
    "artifact": "phase36_robustness_negative_controls_v1_6",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_6",
    "model_free": True,
    "torch_imported": "torch" in sys.modules,
    "protected_population_read": False,
    "mutants_are_in_memory_strings_only": True,
    "controls": results,
    "repair_controls_passed": sum(1 for r in repair_controls if r["pass"]),
    "repair_controls_total": len(repair_controls),
    "passed": passed,
    "total": len(results),
    "all_pass": passed == len(results),
    "nc_range": "NC31-NC35",
}
out = ROOT / "reports/audits/phase36_v1_6_negative_controls.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": len(results),
                  "repair_controls": f"{report['repair_controls_passed']}/"
                                     f"{report['repair_controls_total']}",
                  "all_pass": passed == len(results)}, indent=1))
for r in results:
    if not r["pass"]:
        print("FAIL:", r["control"], json.dumps(r, default=str))
raise SystemExit(0 if passed == len(results) else 1)
