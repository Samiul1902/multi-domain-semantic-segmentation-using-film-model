#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""WO#21 §6 — v1.21 D95 SUPERVISOR INTERRUPTION REGRESSION TEST.

The v1.20 defect (D95) was:

    supervise_once() fell through to ``return {"rc": 0, ...}`` whenever
    termination_observed was False — e.g. when a KeyboardInterrupt interrupted
    ``proc.communicate()``.  An UNOBSERVED child state was masked as SUCCESS.

This test exercises the EXACT real ``supervise_once()`` code path (imported
isolated; NO ``__main__``), with:

  * PROCESS_EXIT / stdout / stderr / START / RESULT / FAILURE redirected into a
    temporary directory (so nothing real is ever written), and
  * a synthetic subprocess injected via the module's ``_POPEN`` seam.

It proves (WO#21 §6):
  A. a simulated KeyboardInterrupt during communicate() cannot return rc 0
  B. termination_observed = false cannot return rc 0
  C. a normal child exit 0 still returns 0
  D. a normal child nonzero returns that nonzero code
  E. an interruption records durable PROCESS_EXIT evidence
  F. the supervisor never creates the real scientific START/RESULT/FAILURE

It ALSO reproduces the v1.20 defect (v1.20 supervisor returns rc 0 under the
same simulated interruption) to prove the test is discriminating.

No model, no checkpoint, no VAL image, no GT, no TEST, no ROUTER_HOLDOUT.
"""

from __future__ import annotations

import ast
import importlib.util
import json
import pathlib
import sys
import tempfile

REPO = pathlib.Path(__file__).resolve().parents[2]
SUP_V120 = REPO / "scripts/analysis/supervise_phase36_v1_20.py"
SUP_V121 = REPO / "scripts/analysis/supervise_phase36_v1_21.py"

results: list[dict] = []


def check(name: str, ok: bool, detail: str = ""):
    results.append({"check": name, "pass": bool(ok), "detail": detail})


def _load_isolated(path: pathlib.Path, modname: str):
    spec = importlib.util.spec_from_file_location(modname, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)   # module-level defs only; __main__ NOT executed
    return mod


class _FakeProc:
    """Synthetic child process.  ``mode`` selects communicate() behaviour."""

    def __init__(self, mode: str, exit_code: int = 0, pid: int = 4242):
        self.pid = pid
        self.returncode = None
        self._mode = mode
        self._exit_code = exit_code
        self.terminated = False
        self.killed = False
        self.waited = False

    def communicate(self, timeout=None):
        if self._mode == "keyboard_interrupt":
            raise KeyboardInterrupt("simulated-supervisor-interrupt")
        if self._mode == "internal_error":
            raise RuntimeError("simulated-supervisor-internal-error")
        self.returncode = self._exit_code
        return ("OUT", "ERR")

    def terminate(self):
        self.terminated = True
        self.returncode = -15

    def wait(self, timeout=None):
        self.waited = True
        if self.returncode is None:
            self.returncode = -15
        return self.returncode

    def kill(self):
        self.killed = True
        self.returncode = -9


def _make_popen(mode: str, exit_code: int = 0):
    def _factory(cmd, **kw):
        return _FakeProc(mode, exit_code=exit_code)
    return _factory


def _redirect(sup, tmp: pathlib.Path):
    """Redirect ALL supervisor write/read targets into a temporary directory."""
    sup.PROCESS_EXIT = tmp / "process_exit.json"
    sup.STDOUT_PATH = tmp / "stdout.txt"
    sup.STDERR_PATH = tmp / "stderr.txt"
    sup.V1_21_START = tmp / "start.json"
    sup.V1_21_RESULT = tmp / "result.json"
    sup.V1_21_FAILURE = tmp / "failure.json"


def _run_sup(sup, mode: str, exit_code: int = 0) -> tuple[dict, pathlib.Path]:
    """Run the REAL supervise_once() with a synthetic child in a fresh tempdir."""
    td = pathlib.Path(tempfile.mkdtemp(prefix="p36_v121_sup_reg_"))
    _redirect(sup, td)
    sup._POPEN = _make_popen(mode, exit_code=exit_code)
    res = sup.supervise_once()
    return res, td


# --------------------------------------------------------------------------- #
# Load modules isolated.
# --------------------------------------------------------------------------- #
try:
    sup121 = _load_isolated(SUP_V121, "phase36_sup_v1_21_for_test")
    check("v1_21_supervisor_import", True)
except Exception as e:  # noqa: BLE001
    check("v1_21_supervisor_import", False, f"{type(e).__name__}: {e}")
    sup121 = None

try:
    sup120 = _load_isolated(SUP_V120, "phase36_sup_v1_20_for_test")
    check("v1_20_supervisor_import", True)
except Exception as e:  # noqa: BLE001
    check("v1_20_supervisor_import", False, f"{type(e).__name__}: {e}")
    sup120 = None

if sup121 is None:
    for r in results:
        print(("PASS " if r["pass"] else "FAIL ") + r["check"])
    print("RESULT: 0 passed, 1 failed")
    print("TERMINAL PHASE36_V1_21_D95_INTERRUPTION_REGRESSION_FAIL")
    sys.exit(1)

# --------------------------------------------------------------------------- #
# A + E: simulated KeyboardInterrupt during communicate() -> rc != 0 + durable evidence
# --------------------------------------------------------------------------- #
res_ki, td_ki = _run_sup(sup121, "keyboard_interrupt")
check("A_keyboard_interrupt_rc_nonzero", res_ki.get("rc") not in (0, None),
      f"rc={res_ki.get('rc')!r}")
check("A_keyboard_interrupt_rc_is_2", res_ki.get("rc") == 2, f"rc={res_ki.get('rc')!r}")
check("A_keyboard_interrupt_reason_unobserved",
      res_ki.get("reason") == "UNOBSERVED_CHILD_TERMINATION",
      f"reason={res_ki.get('reason')!r}")

pe_path = td_ki / "process_exit.json"
pe = None
try:
    pe = json.loads(pe_path.read_text(encoding="utf-8"))
except Exception as e:  # noqa: BLE001
    check("E_process_exit_written", False, f"{type(e).__name__}: {e}")
if pe is not None:
    check("E_process_exit_written", True)
    check("E_termination_kind_supervisor_interruption",
          pe.get("termination_kind") == "SUPERVISOR_INTERRUPTION",
          f"kind={pe.get('termination_kind')!r}")
    check("E_child_exit_code_null", pe.get("child_exit_code") is None,
          f"child_exit_code={pe.get('child_exit_code')!r}")
    check("E_termination_observed_false", pe.get("termination_observed") is False,
          f"termination_observed={pe.get('termination_observed')!r}")
    check("E_cleanup_attempted_true", pe.get("cleanup_attempted") is True,
          f"cleanup_attempted={pe.get('cleanup_attempted')!r}")
    check("E_cleanup_termination_observed_true",
          pe.get("cleanup_termination_observed") is True,
          f"cleanup_termination_observed={pe.get('cleanup_termination_observed')!r}")
    check("E_supervisor_exception_type_recorded",
          pe.get("supervisor_exception_type") == "KeyboardInterrupt",
          f"type={pe.get('supervisor_exception_type')!r}")
    check("E_supervisor_return_rc_nonzero", pe.get("supervisor_return_rc") not in (0, None),
          f"supervisor_return_rc={pe.get('supervisor_return_rc')!r}")
    check("E_rc_zero_not_permitted", pe.get("rc_zero_permitted") is False,
          f"rc_zero_permitted={pe.get('rc_zero_permitted')!r}")
    check("E_unobserved_not_masked",
          pe.get("unobserved_state_masked_as_success") is False,
          f"unobserved_state_masked_as_success={pe.get('unobserved_state_masked_as_success')!r}")
    # durable exception marker in the (redirected) stderr
    check("E_stderr_exception_marker",
          "SUPERVISOR_EXCEPTION::KeyboardInterrupt::" in (td_ki / "stderr.txt").read_text(
              encoding="utf-8"),
          "stderr marker present")

# --------------------------------------------------------------------------- #
# B: termination_observed = false can NEVER return rc 0
# --------------------------------------------------------------------------- #
for code in (None, 0, 7):
    rc = sup121._decide_return_code(termination_observed=False, child_exit_code=code)
    check(f"B_unobserved_rc_nonzero[{code}]", rc != 0, f"rc={rc}")
check("B_observed_zero_is_zero",
      sup121._decide_return_code(termination_observed=True, child_exit_code=0) == 0)

# --------------------------------------------------------------------------- #
# C: normal child exit 0 -> rc 0
# --------------------------------------------------------------------------- #
res_c, _ = _run_sup(sup121, "normal", exit_code=0)
check("C_normal_exit0_rc0", res_c.get("rc") == 0, f"rc={res_c.get('rc')!r}")

# --------------------------------------------------------------------------- #
# D: normal child nonzero -> that nonzero code
# --------------------------------------------------------------------------- #
res_d, _ = _run_sup(sup121, "normal", exit_code=7)
check("D_normal_exit7_rc7", res_d.get("rc") == 7, f"rc={res_d.get('rc')!r}")
res_d2, _ = _run_sup(sup121, "normal", exit_code=3)
check("D_normal_exit3_rc3", res_d2.get("rc") == 3, f"rc={res_d2.get('rc')!r}")

# --------------------------------------------------------------------------- #
# D2: supervisor INTERNAL exception also never returns rc 0
# --------------------------------------------------------------------------- #
res_ie, td_ie = _run_sup(sup121, "internal_error")
check("D2_internal_exception_rc_nonzero", res_ie.get("rc") not in (0, None),
      f"rc={res_ie.get('rc')!r}")
try:
    pe_ie = json.loads((td_ie / "process_exit.json").read_text(encoding="utf-8"))
    check("D2_internal_exception_kind",
          pe_ie.get("termination_kind") == "SUPERVISOR_INTERNAL_EXCEPTION",
          f"kind={pe_ie.get('termination_kind')!r}")
except Exception as e:  # noqa: BLE001
    check("D2_internal_exception_kind", False, f"{type(e).__name__}: {e}")

# --------------------------------------------------------------------------- #
# F: the supervisor never writes the REAL scientific START/RESULT/FAILURE
# --------------------------------------------------------------------------- #
src = SUP_V121.read_text(encoding="utf-8")
tree = ast.parse(src)
writes_marker = []
for n in ast.walk(tree):
    if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_write_once_json" and n.args:
        nm = getattr(n.args[0], "id", None)
        if nm in ("V1_21_START", "V1_21_RESULT", "V1_21_FAILURE"):
            writes_marker.append(nm)
check("F_ast_no_science_marker_writes", not writes_marker,
      f"writes={writes_marker}")

real_start = REPO / "reports/audits/phase36_robustness_science_start_v1_21.json"
real_result = REPO / "reports/audits/phase36_robustness_scientific_result_v1_21.json"
real_failure = REPO / "reports/audits/phase36_robustness_science_failure_v1_21.json"
check("F_real_science_markers_absent",
      not real_start.exists() and not real_result.exists() and not real_failure.exists(),
      "no real v1.21 START/RESULT/FAILURE created by the supervisor")

# --------------------------------------------------------------------------- #
# Discriminating power: reproduce the v1.20 DEFECT (rc 0 under interruption)
# --------------------------------------------------------------------------- #
if sup120 is not None:
    class _StubSubprocess:
        PIPE = __import__("subprocess").PIPE
        DEVNULL = __import__("subprocess").DEVNULL
        TimeoutExpired = __import__("subprocess").TimeoutExpired
        Popen = staticmethod(_make_popen("keyboard_interrupt"))

        @staticmethod
        def run(*a, **k):
            return None

    td120 = pathlib.Path(tempfile.mkdtemp(prefix="p36_v120_sup_reg_"))
    # v1.20 uses str(PATH.relative_to(ROOT)) directly, so point its ROOT at the
    # temporary directory too (its launcher/bundle/authfile pins are absolute).
    sup120.ROOT = td120
    sup120.PROCESS_EXIT = td120 / "process_exit.json"
    sup120.STDOUT_PATH = td120 / "stdout.txt"
    sup120.STDERR_PATH = td120 / "stderr.txt"
    sup120.V1_20_START = td120 / "start.json"
    sup120.V1_20_RESULT = td120 / "result.json"
    sup120.V1_20_FAILURE = td120 / "failure.json"
    sup120.subprocess = _StubSubprocess()
    try:
        res120 = sup120.supervise_once()
        check("DEFECT_v1_20_returns_zero_on_interruption",
              res120.get("rc") == 0, f"v1.20 rc={res120.get('rc')!r} (expected 0 = defect)")
    except Exception as e:  # noqa: BLE001
        check("DEFECT_v1_20_returns_zero_on_interruption", False,
              f"{type(e).__name__}: {e}")

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
passed = sum(1 for r in results if r["pass"])
failed = len(results) - passed
for r in results:
    print(("PASS " if r["pass"] else "FAIL ") + r["check"] +
          (f"  [{r['detail']}]" if r["detail"] else ""))
print(f"RESULT: {passed} passed, {failed} failed")
print("TERMINAL " + ("PHASE36_V1_21_D95_INTERRUPTION_REGRESSION_PASS"
                     if failed == 0 else
                     "PHASE36_V1_21_D95_INTERRUPTION_REGRESSION_FAIL"))
sys.exit(0 if failed == 0 else 1)
