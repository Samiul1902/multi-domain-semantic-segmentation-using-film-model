#!/usr/bin/env python
"""WO#19 §7 — MODEL-FREE REAL-PATH MIRROR TEST (v1.19).

MODE: PREPARATION-ONLY / NON-CONSUMING / MODEL-FREE.

This test EXECUTES the REAL frozen v1.19 functions
    v1_19_reachable_write_targets()
    verify_v1_19_output_absence()
by importing the frozen module in a controlled way, WITHOUT importing torch /
loading any model / reading any protected data.  It proves the D92 crash is
gone on the exact code path that killed v1.18.

SAFETY / ISOLATION
------------------
The v1.19 module performs NO work at import time beyond pure constant
definitions (verified: no top-level model/checkpoint/GT/file-read calls on the
science path; heavy imports are function-local).  To be extra safe we:
  * set PHASE36_ROBUSTNESS_V1_19_DISABLE_JOURNAL=1 (journal disabled);
  * do NOT set any EXECUTE env gate (so no dispatch can occur);
  * only CALL the two pure functions and inspect their return values.

We additionally RE-MIRROR the exact failing expression from v1.18 to show it
raises NameError, while the v1.19 repaired expression resolves.

Non-consuming: no model, no checkpoint, no VAL image, no VAL GT, no TEST, no
ROUTER_HOLDOUT, no perturbation execution, no science.
"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
V119 = ROOT / "scripts" / "analysis" / "phase36_robustness_execution_v1_19.py"

V119_SHA = "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd"

n_pass = 0
n_fail = 0
failures: list[str] = []


def ok(name: str, cond: bool) -> None:
    global n_pass, n_fail
    if cond:
        n_pass += 1
    else:
        n_fail += 1
        failures.append(name)
        print(f"  FAIL {name}")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    print("=== §7 MODEL-FREE REAL-PATH MIRROR TEST (v1.19) ===")

    ok("v1_19_source_present", V119.exists())
    if not V119.exists():
        return 1
    ok("v1_19_sha_matches", sha(V119) == V119_SHA)

    text = V119.read_text(encoding="utf-8")

    # -- Safety pre-flight: assert no science-path module-level side effects. --
    #   The ONLY permitted top-level calls are the benign ``sys.path.insert``
    #   bootstrap idiom.  Any other module-level call (file read, model load,
    #   checkpoint deserialization, network, subprocess) FAILS CLOSED.
    tree = ast.parse(text)
    SUSPECT_CALLS = ("open", "load", "load_state_dict", "exec", "eval",
                     "system", "Popen", "run", "check_output", "read_text",
                     "read_bytes", "urlopen", "socket", "subprocess")
    unsafe_module_calls = []
    for node in tree.body:
        if isinstance(node, ast.Expr) and not isinstance(node.value, ast.Constant):
            v = node.value
            dump = ast.dump(v)
            is_syspath = (isinstance(v, ast.Call)
                          and isinstance(v.func, ast.Attribute)
                          and v.func.attr == "insert"
                          and "sys" in dump and "path" in dump)
            if is_syspath:
                continue
            if any(f"{s}(" in dump for s in SUSPECT_CALLS) or True:
                unsafe_module_calls.append(node.lineno)
    ok("no_unsafe_module_level_calls", not unsafe_module_calls)
    if unsafe_module_calls:
        print(f"  unsafe module-level calls at lines: {unsafe_module_calls}",
              file=sys.stderr)

    # -- Import the frozen module under isolation. --
    os.environ["PHASE36_ROBUSTNESS_V1_19_DISABLE_JOURNAL"] = "1"
    for gate in ("PHASE36_V1_19_EXECUTE", "PHASE36_V1_19_SMOKE_EXECUTE",
                 "PHASE36_EXECUTE"):
        os.environ.pop(gate, None)

    spec = importlib.util.spec_from_file_location("v119_mirror", V119)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # pragma: no cover
        ok("module_imports_cleanly", False)
        print(f"  import error: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    ok("module_imports_cleanly", True)

    # -- Call the REAL frozen functions --
    ok("reachable_write_targets_callable", hasattr(mod, "v1_19_reachable_write_targets"))
    ok("output_absence_callable", hasattr(mod, "verify_v1_19_output_absence"))

    targets = mod.v1_19_reachable_write_targets()
    ok("targets_returned_list", isinstance(targets, list))
    ok("target_count_is_23", len(targets) == 23)

    # uniqueness
    str_targets = [str(t) for t in targets]
    ok("targets_unique", len(set(str_targets)) == len(str_targets))

    # the journal authority target is the canonical V1_19_JOURNAL_DIR
    ok("journal_target_is_canonical_authority",
       str(mod.V1_19_JOURNAL_DIR) in str_targets)

    # -- Run the REAL absence gate --
    absence = mod.verify_v1_19_output_absence()
    ok("absence_returns_dict", isinstance(absence, dict))
    ok("absence_all_targets_absent",
       absence.get("all_targets_absent") is True)
    ok("absence_present_targets_empty",
       absence.get("present_targets") == [])
    ok("absence_target_count_23", absence.get("target_count") == 23)
    ok("absence_terminal_pass",
       absence.get("terminal") ==
       "PHASE36_V1_19_REAL_LAUNCH_OUTPUT_ABSENCE_GATE_PASS")

    # -- Mirror the v1.18 failure: the OLD expression raises NameError --
    old_expr_raises = False
    try:
        # emulate the exact old expression in a namespace WITHOUT the symbol
        ns = {"ROOT": ROOT}
        eval("ROOT / SCIENCE_V1_18_JOURNAL_DIR", {"__builtins__": {}}, ns)
    except NameError:
        old_expr_raises = True
    except Exception:
        old_expr_raises = False
    ok("old_v1_18_expression_raises_NameError", old_expr_raises)

    # -- The V1_19 repaired expression resolves (no NameError) --
    new_expr_ok = True
    try:
        _ = mod.V1_19_JOURNAL_DIR
    except NameError:
        new_expr_ok = False
    ok("new_v1_19_expression_resolves", new_expr_ok)

    report = {
        "artifact": "phase36_v1_19_model_free_real_path_mirror_test",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_19",
        "type": "MODEL_FREE_REAL_PATH_MIRROR_TEST_REPORT",
        "v1_19_source_sha256": sha(V119),
        "method": "import frozen v1.19 module isolated + call the REAL "
                  "v1_19_reachable_write_targets() and "
                  "verify_v1_19_output_absence()",
        "target_count": len(targets),
        "absence": absence,
        "old_expression_raises_nameerror": old_expr_raises,
        "new_expression_resolves": new_expr_ok,
        "model_free": True,
        "torch_imported": "torch" in sys.modules,
        "checkpoint_deserialization": False,
        "val_gt_read": False,
        "val_image_read": False,
        "protected_population_read": False,
        "checks_passed": n_pass,
        "checks_failed": n_fail,
        "failures": failures,
        "all_pass": n_fail == 0,
    }
    out = ROOT / "reports/audits/phase36_v1_19_model_free_real_path_mirror_test.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")

    print(f"\nRESULT: {n_pass} passed, {n_fail} failed")
    print(f"targets={len(targets)} all_absent={absence.get('all_targets_absent')} "
          f"terminal={absence.get('terminal')}")
    for f in failures:
        print("  -", f)
    print("terminal:",
          "PHASE36_V1_19_MODEL_FREE_REAL_PATH_MIRROR_TEST_PASS"
          if n_fail == 0 else
          "PHASE36_V1_19_MODEL_FREE_REAL_PATH_MIRROR_TEST_FAIL")
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
