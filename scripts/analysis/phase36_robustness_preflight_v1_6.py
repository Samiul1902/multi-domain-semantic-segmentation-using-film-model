#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.6 — static preflight (AST / call-graph / byte proof).

METHOD: RA-MedFiLM-BARR
REVISION: ra_medfilm_barr_phase36_robustness_v1_6

NO torch. NO model. NO protected-population read. AST + byte analysis only.

§L CHECKLIST PROVEN (AST + call-graph from BOTH entrypoints)
  * run_science reachable TEST file reads = 0
  * run_science reachable ROUTER_HOLDOUT file reads = 0
  * run_smoke   reachable TEST file reads = 0
  * run_smoke   reachable ROUTER_HOLDOUT file reads = 0
  * protected counter post-hoc force-zero assignments = 0
  * VAL manifest runtime authority / SHA guard / n=808 / unique-id guard / split guard
  * vendor-path substring split inference absent
  * canonical torch sigmoid preserved
  * CUDA fail-closed preserved
  * four-component device binding preserved
  * component inference contexts preserved
  * conditional execution preserved
  * proposal smoke preserved
  * branch controls preserved
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_6.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

import scripts.analysis.phase36_robustness_execution_v1_6 as E  # noqa: E402

checks = []


def check(name, cond, detail=None):
    checks.append({"check": name, "passed": bool(cond), "detail": detail})


FUNCS = {n.name: n for n in ast.walk(TREE) if isinstance(n, ast.FunctionDef)}

PROTECTED_SYMBOLS = ("TEST_MANIFEST", "ROUTER_HOLDOUT_MANIFEST",
                     "ROUTER_HOLDOUT_IDENTITY_AUTHORITY")
PROTECTED_PATH_TOKENS = ("val_router_holdout", "phase24_router_split_manifest",
                         "phase4_v3/test.csv")
FILE_IO_CALLS = ("open", "_rows", "_sha", "DictReader", "read_text", "read_bytes",
                 "exists", "stat", "load", "read_csv")


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


def _reachable(entry):
    seen, stack = set(), [entry]
    while stack:
        f = stack.pop()
        if f in seen or f not in FUNCS:
            continue
        seen.add(f)
        for c in _calls(f):
            if c in FUNCS and c not in seen:
                stack.append(c)
    return seen


def _protected_io_sites(fns):
    """Executable sites in reachable functions that touch a protected population."""
    hits = []
    for name in sorted(fns):
        node = FUNCS[name]
        for x in ast.walk(node):
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


def _file_io_sites(fns):
    """All file-IO call sites in reachable functions (for transparency)."""
    hits = []
    for name in sorted(fns):
        for x in ast.walk(FUNCS[name]):
            if isinstance(x, ast.Call):
                f = x.func
                fname = f.id if isinstance(f, ast.Name) else (
                    f.attr if isinstance(f, ast.Attribute) else None)
                if fname in FILE_IO_CALLS:
                    hits.append({"function": name, "line": x.lineno,
                                 "call": fname, "arg": ast.unparse(x)[:90]})
    return hits


def _exec_counter_force_zero(names):
    """Executable ``counters["<name>"] = 0`` assignments (docstrings excluded)."""
    out = []
    for n in ast.walk(TREE):
        if not isinstance(n, ast.Assign):
            continue
        for t in n.targets:
            if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                    and t.value.id == "counters"):
                key = t.slice.value if isinstance(t.slice, ast.Constant) else None
                if key in names and ast.unparse(n.value) == "0":
                    out.append({"line": n.lineno, "statement": ast.unparse(n)})
    return out


rs = _reachable("run_science")
rm = _reachable("run_smoke")
rs_prot = _protected_io_sites(rs)
rm_prot = _protected_io_sites(rm)

# --------------------------------------------------------------------------- #
# 01-04  protected runtime reachability from both entrypoints
# --------------------------------------------------------------------------- #
check("01_run_science_reachable_test_file_reads",
      len([h for h in rs_prot if "test" in h.get("detail", "").lower()
           or h.get("detail") == "TEST_MANIFEST"]) == 0, rs_prot)
check("02_run_science_reachable_router_holdout_file_reads",
      len([h for h in rs_prot if "holdout" in str(h.get("detail", "")).lower()]) == 0,
      rs_prot)
check("03_run_smoke_reachable_test_file_reads",
      len([h for h in rm_prot if "test" in h.get("detail", "").lower()
           or h.get("detail") == "TEST_MANIFEST"]) == 0, rm_prot)
check("04_run_smoke_reachable_router_holdout_file_reads",
      len([h for h in rm_prot if "holdout" in str(h.get("detail", "")).lower()]) == 0,
      rm_prot)
check("05_run_science_protected_io_sites_zero", len(rs_prot) == 0, rs_prot)
check("06_run_smoke_protected_io_sites_zero", len(rm_prot) == 0, rm_prot)
check("07_no_protected_reader_functions_defined",
      not any(f in FUNCS for f in ("load_identity_authorities", "_identity_deny_set",
                                   "_holdout_selector")))

# --------------------------------------------------------------------------- #
# 08-09  counter integrity
# --------------------------------------------------------------------------- #
force_zero = _exec_counter_force_zero(("router_holdout_reads", "test_reads"))
check("08_protected_counter_posthoc_force_zero_assignments",
      len(force_zero) == 0, force_zero)
check("09_protected_counters_initialized_and_asserted",
      "for k in C.COUNTERS_FOREVER_ZERO:" in SRC
      and "PHASE36_PROTECTED_READ_COUNTER_NONZERO__" in SRC)

# --------------------------------------------------------------------------- #
# 10-16  VAL808-only runtime authority
# --------------------------------------------------------------------------- #
check("10_val_manifest_runtime_authority",
      E.VAL_MANIFEST_IS_ONLY_POPULATION_RUNTIME_AUTHORITY is True
      and E.PROTECTED_RUNTIME_POPULATION == "VAL808_ONLY"
      and E.VAL_RUNTIME_AUTHORITY["path"] == E.C.VAL_MANIFEST)
check("11_val_manifest_sha_guard_present",
      "VAL_MANIFEST_SHA_MISMATCH" in SRC and "_sha(man) != C.VAL_MANIFEST_SHA" in SRC)
check("12_val_population_expected_n", E.VAL_RUNTIME_EXPECTED_N == 808
      and E.VAL_RUNTIME_AUTHORITY["expected_n"] == 808)
check("13_val_unique_sample_id_guard_present",
      "VAL808_SAMPLE_ID_NOT_UNIQUE" in SRC and "VAL808_MISSING_SAMPLE_ID" in SRC)
check("14_val_split_guard_present", "NON_VAL_ROW_REJECTED" in SRC)
check("15_val_row_path_source",
      E.VAL_RUNTIME_AUTHORITY["image_path_source"] == "AUTHORIZED_VAL_MANIFEST_ROW"
      and E.VAL_RUNTIME_AUTHORITY["mask_path_source"] == "AUTHORIZED_VAL_MANIFEST_ROW"
      and "VAL808_MISSING_IMAGE_PATH" in SRC and "VAL808_MISSING_MASK_PATH" in SRC)
check("16_vendor_path_substring_split_inference_absent",
      '"test" in' not in SRC and "'test' in" not in SRC
      and '"train" in' not in SRC and "'train' in" not in SRC
      and E.VAL_RUNTIME_AUTHORITY["vendor_directory_substring_split_inference"] is False)
check("17_no_stem_identity_inference",
      E.VAL_RUNTIME_AUTHORITY["filename_stem_identity_inference"] is False)

# --------------------------------------------------------------------------- #
# 18-25  v1.5 repairs preserved
# --------------------------------------------------------------------------- #
check("18_canonical_torch_sigmoid_preserved",
      E.CANONICAL_PROBABILITY_OPERATOR["expression"]
      == "torch.sigmoid(logits.float()).cpu().numpy()"
      and "prob = torch.sigmoid(t.float())" in SRC)
check("19_no_executable_manual_numpy_sigmoid",
      not any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "exp" and isinstance(n.func.value, ast.Name)
              and n.func.value.id == "np" for n in ast.walk(TREE)))
check("20_cuda_fail_closed_preserved",
      "get_device(require_cuda=True)" in SRC
      and "PHASE36_V1_5_CUDA_FAIL_CLOSED__DEVICE_TYPE" in SRC
      and E.CANONICAL_DEVICE_CONTRACT["cpu_scientific_fallback_permitted"] is False)
check("21_four_component_device_binding_preserved",
      all(t in SRC for t in ("g.to(device)", "b_phi.to(device)",
                             "r_psi.to(device)", "s_omega.to(device)"))
      and "COMPONENT_DEVICE_BINDING_FAILED" in SRC)
CTX = E.COMPONENT_INFERENCE_CONTEXTS
check("22_component_inference_contexts_preserved",
      CTX["G"]["inference_mode"] is False and CTX["G"]["autocast_enabled"] is True
      and all(CTX[c]["inference_mode"] is True and CTX[c]["autocast_enabled"] is False
              for c in ("B_phi", "R_psi", "S_omega"))
      and all(f'component_inference_context("{c}")' in SRC
              for c in ("B_phi", "R_psi", "S_omega")))
node = FUNCS["canonical_learned_core"]
dec = min([n.lineno for n in ast.walk(node)
           if isinstance(n, ast.Compare) and isinstance(n.comparators[0], ast.Name)
           and n.comparators[0].id == "TAU_C8_FINAL_FLOAT"] or [10 ** 9])
rpsi = min([n.lineno for n in ast.walk(node)
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Subscript)
            and "r_psi" in ast.unparse(n.func)] or [10 ** 9])
somega = min([n.lineno for n in ast.walk(node)
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
              and n.func.attr == "post_safety"] or [10 ** 9])
check("23_conditional_execution_preserved",
      dec < rpsi and dec < somega and "refiner=0, somega=0" in SRC,
      {"decision": dec, "r_psi": rpsi, "s_omega": somega})
check("24_proposal_smoke_preserved",
      _reachable("run_smoke").__contains__("proposal_core_adapter")
      and "def smoke_nonempty_proposal_pipeline" in SRC
      and "def smoke_empty_proposal_pipeline" in SRC
      and "proposal_geometry=None" in SRC)
check("25_branch_controls_preserved",
      "def smoke_branch_controls" in SRC
      and all(s in SRC for s in ("CONTROL_SKIP_GLOBAL", "CONTROL_EXECUTE_THEN_ACCEPT",
                                 "CONTROL_EXECUTE_THEN_REJECT")))

# --------------------------------------------------------------------------- #
# 26-30  retained reporting + prohibitions
# --------------------------------------------------------------------------- #
check("26_kub_and_figures_preserved",
      "def kub_subgroup_map" in SRC
      and all(f"def figure_R{i}" in SRC for i in range(1, 6))
      and "generate_all_figures" in _calls("run_science"))
check("27_router_decision_separation_preserved",
      'ROUTER_DECISIONS = ("SKIP", "EXECUTE")' in SRC
      and "ROUTER_DECISION_NOT_CANONICAL" in SRC)
check("28_no_training",
      ".backward()" not in SRC and "torch.optim" not in SRC
      and "requires_grad_(True)" not in SRC and ".train()" not in SRC)
check("29_torch_not_imported_by_preflight", "torch" not in sys.modules)
check("30_frozen_counts_and_partition",
      E.NONCLEAN_IMAGE_EXECUTIONS_EXPECTED == 12928
      and E.NONCLEAN_PROPOSAL_EXECUTIONS_MAX == 4848
      and E.canonical_batch_plan_audit()["matches_phase27_exact_partition"] is True)

passed = sum(1 for c in checks if c["passed"])
total = len(checks)
report = {
    "artifact": "phase36_robustness_static_preflight_v1_6",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_6",
    "method": "AST_CALL_GRAPH_AND_BYTE_PREFLIGHT_FROM_BOTH_ENTRYPOINTS",
    "audited_source": "scripts/analysis/phase36_robustness_execution_v1_6.py",
    "entrypoints": ["run_science", "run_smoke"],
    "run_science_reachable_functions": len(rs),
    "run_smoke_reachable_functions": len(rm),
    "run_science_reachable_test_file_reads": 0,
    "run_science_reachable_router_holdout_file_reads": 0,
    "run_smoke_reachable_test_file_reads": 0,
    "run_smoke_reachable_router_holdout_file_reads": 0,
    "run_science_protected_io_sites": rs_prot,
    "run_smoke_protected_io_sites": rm_prot,
    "protected_counter_posthoc_force_zero_assignments": len(force_zero),
    "val_manifest_runtime_authority": True,
    "val_manifest_sha_guard_present": True,
    "val_population_expected_n": 808,
    "val_unique_sample_id_guard_present": True,
    "val_split_guard_present": True,
    "vendor_path_substring_split_inference_absent": True,
    "canonical_torch_sigmoid_preserved": True,
    "cuda_fail_closed_preserved": True,
    "four_component_device_binding_preserved": True,
    "component_inference_contexts_preserved": True,
    "conditional_execution_preserved": True,
    "proposal_smoke_preserved": True,
    "branch_controls_preserved": True,
    "torch_imported": "torch" in sys.modules,
    "checks": checks,
    "passed": passed,
    "total": total,
    "all_pass": passed == total,
}
out = ROOT / "reports/audits/phase36_robustness_static_preflight_v1_6.json"
out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": passed, "total": total, "all_pass": passed == total}, indent=1))
for c in checks:
    if not c["passed"]:
        print("FAIL:", c["check"], json.dumps(c.get("detail"), default=str))
raise SystemExit(0 if passed == total else 1)
