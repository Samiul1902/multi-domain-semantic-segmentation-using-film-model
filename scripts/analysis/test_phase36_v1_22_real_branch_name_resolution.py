#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WO#21A §4 — v1.22 D96 REAL-BRANCH NAME-RESOLUTION REGRESSION TEST.

The v1.21 defect (D96) was:

    the default REAL-dispatch branch of main() called

        verify_v1_19_consumed_history()

    which is NOT defined anywhere in the launcher, while the launcher actually
    DEFINES ``verify_v1_20_consumed_history()`` (the correct verifier for the
    consumed v1.20 state).  The defect escaped ``--verify-only`` because
    verify-only RETURNS before the real-dispatch branch.

This test proves (WO#21A §4):

  1. every global function referenced from the default real-dispatch branch
     RESOLVES in the v1.22 launcher;
  2. ``verify_v1_19_consumed_history`` is ABSENT from the executable v1.22 real
     path (source text + real-dispatch branch);
  3. ``verify_v1_20_consumed_history`` exists EXACTLY ONCE (definition);
  4. the default real-dispatch branch calls it EXACTLY ONCE;
  5. a mutation BACK to ``verify_v1_19_consumed_history`` is DETECTED;
  6. ``--verify-only`` ALONE is NOT sufficient evidence for this check;
  7. the REAL main() control path executes the consumed-history call
     successfully BEFORE dispatch (final subprocess dispatch stubbed).

No model, no checkpoint, no VAL image, no GT, no TEST, no ROUTER_HOLDOUT.
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
LAUNCHER_V122 = REPO / "scripts/analysis/launch_phase36_v1_22.py"

UNDEFINED = "verify_v1_19_consumed_history"
DEFINED = "verify_v1_20_consumed_history"

results: list[dict] = []


def check(name: str, ok: bool, detail: str = ""):
    results.append({"check": name, "pass": bool(ok), "detail": detail})


def _load_isolated(path: pathlib.Path, modname: str):
    spec = importlib.util.spec_from_file_location(modname, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)   # module-level defs only; __main__ NOT executed
    return mod


def _real_branch_statements(src: str, tree: ast.Module):
    """Return main() body statements AFTER the --verify-only/--self-test early returns."""
    main = next(n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name == "main")
    branch = []
    for st in main.body:
        seg = ast.get_source_segment(src, st) or ""
        if isinstance(st, ast.If) and ("--verify-only" in seg or "--self-test" in seg):
            continue
        branch.append(st)
    return branch


def _called_global_names(stmts) -> set[str]:
    """Names used as plain-name CALL targets inside the given statements."""
    names = set()
    for st in stmts:
        for n in ast.walk(st):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name):
                names.add(n.func.id)
    return names


def _unresolved(src: str, namespace: set[str]) -> list[str]:
    """Global function names referenced from the real branch that do NOT resolve."""
    tree = ast.parse(src)
    branch = _real_branch_statements(src, tree)
    called = _called_global_names(branch)
    resolvable = namespace | set(dir(builtins))
    return sorted(n for n in called if n not in resolvable)


def _count_defs(src: str, name: str) -> int:
    return sum(1 for n in ast.walk(ast.parse(src))
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)


def _count_branch_calls(src: str, name: str) -> int:
    tree = ast.parse(src)
    branch = _real_branch_statements(src, tree)
    cnt = 0
    for st in branch:
        for n in ast.walk(st):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == name:
                cnt += 1
    return cnt


# --------------------------------------------------------------------------- #
# Load the v1.22 launcher isolated.
# --------------------------------------------------------------------------- #
SRC = LAUNCHER_V122.read_text(encoding="utf-8")
try:
    mod = _load_isolated(LAUNCHER_V122, "phase36_launcher_v1_22_for_d96_test")
    check("v1_22_launcher_import", True)
except Exception as e:  # noqa: BLE001
    check("v1_22_launcher_import", False, f"{type(e).__name__}: {e}")
    mod = None

if mod is None:
    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + r["check"])
    print("RESULT: 0 passed, 1 failed")
    print("TERMINAL PHASE36_V1_22_D96_REAL_BRANCH_REGRESSION_FAIL")
    sys.exit(1)

NAMESPACE = set(dir(mod))

# --------------------------------------------------------------------------- #
# 1. Every global function referenced from the real branch RESOLVES.
# --------------------------------------------------------------------------- #
unresolved = _unresolved(SRC, NAMESPACE)
check("1_real_branch_globals_all_resolve", not unresolved,
      f"unresolved={unresolved}")

# --------------------------------------------------------------------------- #
# 2. verify_v1_19_consumed_history ABSENT from the executable v1.22 real path.
# --------------------------------------------------------------------------- #
check("2a_undefined_symbol_absent_source", UNDEFINED not in SRC,
      f"occurrences in source={SRC.count(UNDEFINED)}")
check("2b_undefined_symbol_not_defined", _count_defs(SRC, UNDEFINED) == 0)
check("2c_undefined_symbol_not_called_in_branch", _count_branch_calls(SRC, UNDEFINED) == 0)
check("2d_undefined_symbol_not_in_namespace", UNDEFINED not in NAMESPACE)

# --------------------------------------------------------------------------- #
# 3. verify_v1_20_consumed_history exists EXACTLY ONCE (definition).
# --------------------------------------------------------------------------- #
check("3_defined_symbol_defined_exactly_once", _count_defs(SRC, DEFINED) == 1,
      f"defs={_count_defs(SRC, DEFINED)}")
check("3b_defined_symbol_callable", callable(getattr(mod, DEFINED, None)))

# --------------------------------------------------------------------------- #
# 4. The default real-dispatch branch calls it EXACTLY ONCE.
# --------------------------------------------------------------------------- #
check("4_branch_calls_defined_symbol_exactly_once",
      _count_branch_calls(SRC, DEFINED) == 1,
      f"branch_calls={_count_branch_calls(SRC, DEFINED)}")

# --------------------------------------------------------------------------- #
# 5. Mutation BACK to the undefined symbol is DETECTED.
# --------------------------------------------------------------------------- #
mutated = SRC.replace(f"{DEFINED}()", f"{UNDEFINED}()")
check("5a_mutation_applied", UNDEFINED in mutated and mutated != SRC)
mut_unresolved = _unresolved(mutated, NAMESPACE)
check("5b_mutation_detected_as_unresolved", UNDEFINED in mut_unresolved,
      f"mut_unresolved={mut_unresolved}")
# The v1.21 launcher (which contains the defect) must ALSO be flagged.
V121 = REPO / "scripts/analysis/launch_phase36_v1_21.py"
if V121.exists():
    v121_src = V121.read_text(encoding="utf-8")
    v121_unresolved = _unresolved(v121_src, NAMESPACE)
    check("5c_v1_21_defect_flagged", UNDEFINED in v121_unresolved,
          f"v1_21_unresolved={v121_unresolved}")

# --------------------------------------------------------------------------- #
# 6. --verify-only ALONE is NOT sufficient evidence for this check.
# --------------------------------------------------------------------------- #
gate_calls = {"n": 0}
_real_gate = mod.verify_v1_20_consumed_history


def _spy_gate(*a, **k):
    gate_calls["n"] += 1
    return _real_gate(*a, **k)


mod.verify_v1_20_consumed_history = _spy_gate
_real_run_all = mod.run_all_gates
mod.run_all_gates = lambda *a, **k: (True, {
    "pure_release_state": {"state": "RELEASED"},
    "dispatch_output_absence": {"terminal": "STUB_ABSENCE_OK"},
})

_stdout = io.StringIO()
with contextlib.redirect_stdout(_stdout):
    rc_vo = mod.main(["--verify-only"])
check("6a_verify_only_returns_0", rc_vo == 0, f"rc={rc_vo}")
check("6b_verify_only_does_not_exercise_real_branch_gate", gate_calls["n"] == 0,
      f"gate_calls={gate_calls['n']} (verify-only must NOT be treated as evidence)")
check("6c_verify_only_printed_return_before_token",
      "RETURN_BEFORE_TOKEN_SET" in _stdout.getvalue())

# --------------------------------------------------------------------------- #
# 7. REAL main() control path: consumed-history call executes BEFORE dispatch.
# --------------------------------------------------------------------------- #
class _StubSubprocess:
    PIPE = __import__("subprocess").PIPE
    DEVNULL = __import__("subprocess").DEVNULL
    TimeoutExpired = __import__("subprocess").TimeoutExpired
    captured: list = []

    @staticmethod
    def run(cmd, *a, **k):
        _StubSubprocess.captured.append(list(cmd))

        class _R:
            returncode = 0
        return _R()


mod.subprocess = _StubSubprocess()
os.environ[mod.TOKEN_ENV] = "1"
gate_calls["n"] = 0

dispatch_seen_after_gate = {"ok": False}


def _spy_gate2(*a, **k):
    gate_calls["n"] += 1
    r = _real_gate(*a, **k)
    dispatch_seen_after_gate["gate_ok"] = bool(r.get("ok"))
    return r


mod.verify_v1_20_consumed_history = _spy_gate2

_stdout2 = io.StringIO()
try:
    with contextlib.redirect_stdout(_stdout2):
        rc_real = mod.main([])
except Exception as e:  # noqa: BLE001
    rc_real = None
    check("7a_real_main_no_exception", False, f"{type(e).__name__}: {e}")

if rc_real is not None:
    check("7a_real_main_no_exception", True)
check("7b_real_branch_gate_executed", gate_calls["n"] == 1,
      f"gate_calls={gate_calls['n']}")
check("7c_gate_returned_ok_true", dispatch_seen_after_gate.get("gate_ok") is True,
      f"gate_ok={dispatch_seen_after_gate.get('gate_ok')!r}")
check("7d_dispatch_reached_after_gate", len(_StubSubprocess.captured) == 1,
      f"n_dispatches={len(_StubSubprocess.captured)}")
if _StubSubprocess.captured:
    cmd = _StubSubprocess.captured[0]
    check("7e_dispatch_targets_v1_22_execution",
          any(str(x).endswith("phase36_robustness_execution_v1_22.py") for x in cmd),
          f"cmd={cmd}")
    check("7f_dispatch_mode_science", "--mode" in cmd and "science" in cmd, f"cmd={cmd}")
check("7g_real_main_returned_child_rc", rc_real == 0, f"rc={rc_real}")

# The runtime gate must be bound to the consumed v1.20 state.
runtime_gate = _real_gate()
check("8_gate_binds_v1_20_adjudication_sha",
      mod.V1_20_CONSUMED_ADJUDICATION_SHA
      == "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
check("8b_gate_ok_on_real_consumed_state", runtime_gate.get("ok") is True,
      f"gate={runtime_gate}")
check("8c_gate_classification_bound",
      mod.V1_20_CONSUMED_EXPECTED_CLASSIFICATION
      == "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT")

# cleanup
os.environ.pop(mod.TOKEN_ENV, None)
os.environ.pop(mod.LAUNCH_AUTHORITY, None)

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
passed = sum(1 for r in results if r["pass"])
failed = len(results) - passed
for r in results:
    print(("PASS " if r["pass"] else "FAIL ") + r["check"] +
          (f"  [{r['detail']}]" if r["detail"] else ""))
print(f"RESULT: {passed} passed, {failed} failed")
print("TERMINAL " + ("PHASE36_V1_22_D96_REAL_BRANCH_REGRESSION_PASS"
                     if failed == 0 else
                     "PHASE36_V1_22_D96_REAL_BRANCH_REGRESSION_FAIL"))
sys.exit(0 if failed == 0 else 1)
