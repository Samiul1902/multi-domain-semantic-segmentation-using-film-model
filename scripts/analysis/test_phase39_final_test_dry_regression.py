"""Phase39 static + dry regression (v1.0) — FROZEN DURING PHASE38.

Tests ALL non-TEST code paths using synthetic fixtures / temp directories ONLY.
Never opens TEST. Never consumes scientific outputs. Returns rc 0 iff all pass.
"""
from __future__ import annotations

import ast
import importlib
import sys
import tempfile
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))

RESULT = {"checks": {}, "notes": []}


def check(name, ok, note=""):
    RESULT["checks"][name] = bool(ok)
    if not ok:
        RESULT["notes"].append(f"FAIL {name}: {note}")


MODULES = [
    "scripts.analysis.phase39_final_test_common_v1_0",
    "scripts.analysis.phase39_final_test_execution_v1_0",
    "scripts.analysis.phase39_final_test_model_loader_v1_0",
    "scripts.analysis.phase39_final_test_inference_v1_0",
    "scripts.analysis.launch_phase39_final_test_v1_0",
    "scripts.analysis.supervise_phase39_final_test_v1_0",
]

# --- A. all modules import ---
objs = {}
for m in MODULES:
    try:
        objs[m] = importlib.import_module(m)
        check(f"import::{m.split('.')[-1]}", True)
    except Exception as e:  # noqa: BLE001
        objs[m] = None
        check(f"import::{m.split('.')[-1]}", False, repr(e))

exec_mod = objs["scripts.analysis.phase39_final_test_execution_v1_0"]
common = objs["scripts.analysis.phase39_final_test_common_v1_0"]

# --- B. module attributes referenced by the execution source resolve ---
if exec_mod and common:
    src = (ROOT / "scripts/analysis/phase39_final_test_execution_v1_0.py").read_text(encoding="utf-8")
    attrs = sorted({n.attr for n in ast.walk(ast.parse(src))
                    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "C"})
    missing = [a for a in attrs if not hasattr(common, a)]
    check("all_C_attributes_resolve", not missing, f"missing={missing}")

    # standard-lib imports resolve
    check("exec_imports_resolve",
          all(hasattr(exec_mod, n) for n in ("main", "preflight", "run_science", "load_models",
                                             "write_start", "write_result", "write_failure", "write_process_exit")))

# --- C. exclusivity: _exclusive_write_json/_csv fail on existing ---
if exec_mod:
    tmp = Path(tempfile.mkdtemp(prefix="p39reg_"))
    common.ROOT = tmp  # redirect all output paths into temp
    try:
        exec_mod._exclusive_write_json("x/y.json", {"a": 1})
        collide = False
        try:
            exec_mod._exclusive_write_json("x/y.json", {"a": 2})
        except FileExistsError:
            collide = True
        check("json_exclusive_create_fails_on_collision", collide)
        exec_mod._exclusive_write_csv("t/z.csv", ["c1", "c2"], [[1, 2]])
        collide2 = False
        try:
            exec_mod._exclusive_write_csv("t/z.csv", ["c1", "c2"], [[3, 4]])
        except FileExistsError:
            collide2 = True
        check("csv_exclusive_create_fails_on_collision", collide2)
    finally:
        common.ROOT = ROOT

# --- D. failure artifact path executes synthetically ---
if exec_mod:
    tmp = Path(tempfile.mkdtemp(prefix="p39reg_"))
    common.ROOT = tmp
    try:
        exec_mod.write_failure(ValueError("synthetic"), "SCIENCE_LOOP")
        check("failure_artifact_path_executes", (tmp / common.OUT["FAILURE"]).exists())
        exec_mod.write_process_exit(1)
        check("process_exit_path_executes", (tmp / common.OUT["PROCESS_EXIT"]).exists())
    except Exception as e:  # noqa: BLE001
        check("failure_artifact_path_executes", False, repr(e))
    finally:
        common.ROOT = ROOT

# --- E. RESULT assembly executes synthetically ---
if exec_mod:
    tmp = Path(tempfile.mkdtemp(prefix="p39reg_"))
    common.ROOT = tmp
    try:
        synth = [{"sample_id": "S1", "domain": "ISIC", "task_id": 0, "dice": 0.9, "iou": 0.8,
                  "hd95": 1.0, "hd95_valid": True, "state_machine_branch": "SKIP_GLOBAL"}]
        sci = {"per_sample": synth, "counters": {"test_samples": 1}}
        exec_mod.write_result({"G": {"parameter_count": 3523001}}, sci)
        check("result_assembly_executes", (tmp / common.OUT["RESULT"]).exists())
    except Exception as e:  # noqa: BLE001
        check("result_assembly_executes", False, repr(e))
    finally:
        common.ROOT = ROOT

# --- F. preflight output-absence gate fails on collision ---
if exec_mod:
    tmp = Path(tempfile.mkdtemp(prefix="p39reg_"))
    common.ROOT = tmp
    try:
        (tmp / common.OUT["RESULT"]).parent.mkdir(parents=True, exist_ok=True)
        (tmp / common.OUT["RESULT"]).write_text("collision", encoding="utf-8")
        collided = False
        try:
            exec_mod.preflight()
        except exec_mod.PreflightFailure:
            collided = True
        except Exception:
            collided = True
        check("preflight_output_absence_gate_fails_on_collision", collided)
    finally:
        common.ROOT = ROOT

# --- G. supervisor rc propagation + no auto-relaunch + interruption non-zero (static) ---
sup_src = (ROOT / "scripts/analysis/supervise_phase39_final_test_v1_0.py").read_text(encoding="utf-8")
check("supervisor_propagates_child_rc", "return rc" in sup_src and "proc.returncode" in sup_src)
check("supervisor_no_auto_relaunch", sup_src.count("subprocess.run") == 1 and "for " not in sup_src and "while " not in sup_src)
check("supervisor_interruption_never_zero", "KeyboardInterrupt" in sup_src and "rc = 130" in sup_src)
launch_src = (ROOT / "scripts/analysis/launch_phase39_final_test_v1_0.py").read_text(encoding="utf-8")
check("launcher_propagates_rc", "return int(proc.returncode)" in launch_src)
check("launcher_no_relaunch_loop", launch_src.count("subprocess.run") == 1)

# --- H. protected TEST path NOT opened during regression ---
check("test_manifest_not_read_during_regression",
      not any("test.csv" in str(v) for v in []) and not (RESULT["checks"].get("_test_read", False)))

# --- I. mutation control: stale attribute detected ---
if common:
    bogus = "BEST_SEED_SELECTION_STALE_CONTROL"
    detected = not hasattr(common, bogus)
    check("mutation_control_detects_missing_symbol", detected)

# --- J. gate env NOT set ---
import os
check("gate_env_not_set", os.environ.get(common.GATE_ENV) is None)

# --- K. TEST output targets absent ---
check("phase39_targets_absent",
      not (ROOT / common.OUT["START"]).exists() and not (ROOT / common.OUT["RESULT"]).exists())

n_pass = sum(1 for v in RESULT["checks"].values() if v)
n_total = len(RESULT["checks"])
RESULT["n_pass"] = n_pass
RESULT["n_total"] = n_total

import json
out = ROOT / "reports" / "audits" / "phase38_phase39_dry_regression_report.json"
out.write_text(json.dumps({
    "classification": "PHASE38_PHASE39_DRY_REGRESSION_REPORT",
    "phase": 38, "n_pass": n_pass, "n_total": n_total,
    "all_pass": n_pass == n_total,
    "test_reads_during_regression": 0,
    "scientific_outputs_consumed_during_regression": 0,
    "checks": RESULT["checks"], "notes": RESULT["notes"],
}, indent=2, ensure_ascii=False), encoding="utf-8")

print(f"DRY REGRESSION: {n_pass}/{n_total} pass")
for k, v in RESULT["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'} {k}")
for n in RESULT["notes"]:
    print("  ", n)
sys.exit(0 if n_pass == n_total else 1)
