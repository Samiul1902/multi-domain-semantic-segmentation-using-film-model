#!/usr/bin/env python3
"""
WO#20 §6 — v1.20 D93A REGRESSION TEST (exercise the ACTUAL failed code path).

The v1.19 failure was a NameError raised from the real journal writer chain:

    main -> _run_science_with_durable_evidence -> _ScienceJournal.begin("START")
         -> _journal_record("START", "BEGIN", attempt_id)
         -> _write_once_json(path, payload)          # <-- NameError (undefined)

This test does NOT merely grep for a string.  It:

  1. Imports each revision's module in isolation (journal DISABLED, no execute
     gate, no model, no torch needed for this path).
  2. Calls the ACTUAL `_journal_record(...)` function with the journal REDIRECTED
     into a temporary directory (write-once), which is EXACTLY the function that
     crashed.  This exercises the real call graph
     `_journal_record -> _write_once_json`.
  3. Asserts the behavior:
       - v1.19: raises NameError('_write_once_json' is not defined)   -> DEFECT REPRODUCED
       - v1.20: writes the record successfully, returns the filename  -> REPAIR HOLDS
  4. Additionally calls `_ScienceJournal.begin("START")` end-to-end on v1.20.

No scientific tensor is produced; no model is loaded; no checkpoint is touched.
"""

from __future__ import annotations

import importlib.util
import os
import pathlib
import sys
import tempfile
import traceback

REPO = pathlib.Path(__file__).resolve().parents[2]
V119 = REPO / "scripts/analysis/phase36_robustness_execution_v1_19.py"
V120 = REPO / "scripts/analysis/phase36_robustness_execution_v1_20.py"

results: list[dict] = []


def _load_module_isolated(path: pathlib.Path, modname: str):
    """Import a revision module WITHOUT running its __main__ block.

    ``__name__`` is forced to a non-"__main__" value so the module-level
    ``if __name__ == "__main__"`` guard never fires; the journal is disabled via
    env so no real journal directory is touched on import.
    """
    os.environ["PHASE36_ROBUSTNESS_V1_19_DISABLE_JOURNAL"] = "1"
    os.environ["PHASE36_ROBUSTNESS_V1_20_DISABLE_JOURNAL"] = "1"
    spec = importlib.util.spec_from_file_location(modname, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[modname] = mod
    spec.loader.exec_module(mod)   # module-level defs only; __main__ NOT executed
    return mod


def check(name: str, ok: bool, detail: str = ""):
    results.append({"check": name, "pass": bool(ok), "detail": detail})


# --------------------------------------------------------------------------- #
# 1) v1.19 — the actual failing function chain MUST raise NameError.
# --------------------------------------------------------------------------- #
write_once_json_defined_v119 = None
try:
    m119 = _load_module_isolated(V119, "phase36_exec_v1_19_for_test")
    write_once_json_defined_v119 = hasattr(m119, "_write_once_json")
    with tempfile.TemporaryDirectory() as td:
        m119.V1_19_JOURNAL_DIR = pathlib.Path(td)
        try:
            m119._journal_record("START", "BEGIN", "v1_19_regression_probe")
            v119_raised = None
        except NameError as e:
            v119_raised = str(e)
        except Exception as e:  # noqa: BLE001
            v119_raised = f"{type(e).__name__}: {e}"
except Exception as e:  # noqa: BLE001
    check("v1_19_module_import", False, f"{type(e).__name__}: {e}")
    v119_raised = None
    write_once_json_defined_v119 = None

check("v1_19_module_import", True)
check("v1_19_write_once_json_undefined",
      write_once_json_defined_v119 is False,
      f"_write_once_json present={write_once_json_defined_v119}")
check("v1_19_journal_record_raises_nameerror",
      isinstance(v119_raised, str) and "_write_once_json" in v119_raised,
      f"raised={v119_raised!r}")

# --------------------------------------------------------------------------- #
# 2) v1.20 — the SAME function chain MUST succeed.
# --------------------------------------------------------------------------- #
try:
    m120 = _load_module_isolated(V120, "phase36_exec_v1_20_for_test")
    check("v1_20_module_import", True)
    check("v1_20_write_once_json_defined",
          callable(getattr(m120, "_write_once_json", None)),
          f"_write_once_json present={hasattr(m120, '_write_once_json')}")

    wrote_ok = False
    fname = None
    detail = ""
    with tempfile.TemporaryDirectory() as td:
        m120.V1_20_JOURNAL_DIR = pathlib.Path(td)
        try:
            fname = m120._journal_record("START", "BEGIN", "v1_20_regression_probe")
            wrote_ok = True
            # the record must actually exist on disk (write-once semantics)
            on_disk = (pathlib.Path(td) / fname).exists()
            check("v1_20_journal_record_wrote_file", on_disk, f"fname={fname}")
        except Exception as e:  # noqa: BLE001
            detail = f"{type(e).__name__}: {e}"
    check("v1_20_journal_record_succeeds", wrote_ok, detail or f"fname={fname}")

    # full driver entry point: _ScienceJournal.begin("START") — the exact v1.19 crash site
    begin_ok = False
    detail2 = ""
    with tempfile.TemporaryDirectory() as td:
        m120.V1_20_JOURNAL_DIR = pathlib.Path(td)
        j = m120._ScienceJournal(attempt_id="v1_20_regression_begin", enabled=True)
        try:
            j.begin("START")
            begin_ok = True
        except Exception as e:  # noqa: BLE001
            detail2 = f"{type(e).__name__}: {e}"
    check("v1_20_science_journal_begin_start_succeeds", begin_ok, detail2)

    # write-once: a second identical record must NOT overwrite (seq increments)
    with tempfile.TemporaryDirectory() as td:
        m120.V1_20_JOURNAL_DIR = pathlib.Path(td)
        f1 = m120._journal_record("START", "BEGIN", "probeA")
        f2 = m120._journal_record("START", "BEGIN", "probeB")
        check("v1_20_write_once_distinct_records", f1 != f2,
              f"f1={f1} f2={f2}")

except Exception as e:  # noqa: BLE001
    check("v1_20_module_import", False, f"{type(e).__name__}: {e}")

# --------------------------------------------------------------------------- #
# Summary
# --------------------------------------------------------------------------- #
passed = sum(1 for r in results if r["pass"])
failed = len(results) - passed
for r in results:
    print(("PASS " if r["pass"] else "FAIL ") + r["check"] + (f"  [{r['detail']}]" if r["detail"] else ""))
print(f"RESULT: {passed} passed, {failed} failed")
print("TERMINAL " + ("PHASE36_V1_20_D93A_REGRESSION_PASS" if failed == 0 else "PHASE36_V1_20_D93A_REGRESSION_FAIL"))
sys.exit(0 if failed == 0 else 1)
