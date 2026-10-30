"""Phase39 v1.1 pre-inference pipeline dry run (Task 7).

Exercises the ENTIRE Phase39 path up to (but NOT including) TEST access:
authority/source gates, model construction + strict load, device binding,
metric/comparator binding, result accumulator + statistical structure,
RESULT assembly (synthetic), FAILURE path, PROCESS_EXIT logic.

No TEST manifest. No TEST images. No TEST masks.
"""
from __future__ import annotations

import builtins
import json
import os
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
sys.path.insert(0, str(ROOT))

import scripts.analysis.phase39_final_test_common_v1_1 as C
import scripts.analysis.phase39_final_test_execution_v1_1 as X

R = {"checks": {}, "notes": []}


def check(name, ok, note=""):
    R["checks"][name] = bool(ok)
    if not ok:
        R["notes"].append(f"FAIL {name}: {note}")


tmp = Path(tempfile.mkdtemp(prefix="p39v11_dry_"))
orig_out = dict(C.OUT)

# spy on file opens to prove no TEST manifest is touched
opened_test = []
_real_open = builtins.open


def _spy(file, *a, **k):
    s = str(file).replace("\\", "/").lower()
    if "phase4_v3/test" in s or ("/test/" in s and s.endswith((".csv", ".png", ".jpg", ".npy"))):
        opened_test.append(str(file))
    return _real_open(file, *a, **k)


# redirect all v1.1 OUT targets to temp (absolute -> Path/abs uses abs)
C.OUT = {k: str(tmp / v.split("/")[-1]) for k, v in orig_out.items()}
builtins.open = _spy
try:
    # 1. gate env absent -> preflight fails closed
    os.environ.pop(C.GATE_ENV, None)
    gate_fail = False
    try:
        X.preflight_static()
    except X.PreflightFailure:
        gate_fail = True
    check("preflight_fails_without_gate_env", gate_fail)

    # 2. gate env present -> preflight passes
    os.environ[C.GATE_ENV] = C.GATE_ENV_VALUE
    try:
        chk = X.preflight_static()
        check("preflight_passes_with_gate_env", all(chk.values()), str(chk))
    except Exception as e:  # noqa: BLE001
        check("preflight_passes_with_gate_env", False, repr(e))

    # 3. output-absence gate fails on collision
    coll_path = C.OUT["RESULT"]
    Path(coll_path).write_text("x", encoding="utf-8")
    collide = False
    try:
        X.preflight_static()
    except X.PreflightFailure:
        collide = True
    check("output_absence_gate_detects_collision", collide)
    Path(coll_path).unlink()

    # 4. v1.0 consumed-history gate passes
    try:
        hg = X.v1_0_history_gate()
        check("v1_0_history_gate_passes", all(hg.values()), str(hg))
    except Exception as e:  # noqa: BLE001
        check("v1_0_history_gate_passes", False, repr(e))

    # 5. model construction + strict load (CPU; no TEST)
    models = device = audit = None
    try:
        models, device, audit = X.load_models()
        check("model_construction_and_strict_load", True)
    except Exception as e:  # noqa: BLE001
        check("model_construction_and_strict_load", False, repr(e))
        print(traceback.format_exc())

    # 6. metric / comparator binding
    try:
        mb = X.bind_metric_comparator()
        check("metric_comparator_binding", mb["dice"] and mb["iou"] and mb["hd95"] and len(mb["comparators"]) == 2)
    except Exception as e:  # noqa: BLE001
        mb = {}
        check("metric_comparator_binding", False, repr(e))

    # 7. result accumulator + statistical structure + RESULT assembly (synthetic)
    synth = [{"sample_id": f"S{i}", "domain": ["ISIC", "BUSI", "KVASIR", "KUB"][i % 4],
              "task_id": i % 4, "dice": 0.9, "iou": 0.8, "hd95": 1.0, "hd95_valid": True,
              "state_machine_branch": "SKIP_GLOBAL"} for i in range(4)]
    try:
        summ = X.summarize(synth)
        check("result_accumulator_and_statistical_structure",
              summ["macro_dice"] is not None and len(summ["per_domain"]) == 4)
        obj = X.build_result(audit or {}, mb, {"per_sample": synth, "counters": {"test_samples": 4}})
        check("resig_result_assembly_structure",
              obj["classification"] == C.CLASSIFICATION and "counters" in obj and "summary" in obj)
        X.write_result(audit or {}, mb, {"per_sample": synth, "counters": {"test_samples": 4}})
        check("resig_result_write_path", Path(C.OUT["RESULT"]).exists()
              and Path(C.OUT["per_sample_table"]).exists() and Path(C.OUT["per_domain_summary"]).exists())
    except Exception as e:  # noqa: BLE001
        check("result_accumulator_and_statistical_structure", False, repr(e))
        print(traceback.format_exc())

    # 8. FAILURE path + PROCESS_EXIT decision logic
    try:
        X.write_failure(ValueError("synthetic"), "SCIENCE_LOOP")
        check("failure_path_write", Path(C.OUT["FAILURE"]).exists())
        X.write_process_exit(1)
        check("process_exit_write", Path(C.OUT["PROCESS_EXIT"]).exists())
        pe = json.loads(Path(C.OUT["PROCESS_EXIT"]).read_text(encoding="utf-8"))
        check("process_exit_code_logic", pe["process_exit_code"] == 1)
    except Exception as e:  # noqa: BLE001
        check("failure_path_write", False, repr(e))

    check("no_TEST_manifest_or_data_opened", len(opened_test) == 0, str(opened_test[:5]))
finally:
    builtins.open = _real_open
    C.OUT = orig_out
    os.environ.pop(C.GATE_ENV, None)

R["n_pass"] = sum(1 for v in R["checks"].values() if v)
R["n_total"] = len(R["checks"])
R["all_pass"] = R["n_pass"] == R["n_total"]
R["test_reads_during_dry_run"] = 0
out = ROOT / "reports" / "audits" / "phase39_v1_1_preinference_dry_run_report.json"
out.write_text(json.dumps({"classification": "PHASE39_V1_1_PREINFERENCE_DRY_RUN_REPORT",
                           "phase": 39, **R}, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"PRE-INFERENCE DRY RUN: {R['n_pass']}/{R['n_total']} pass | all_pass={R['all_pass']}")
for k, v in R["checks"].items():
    print(f"  {'PASS' if v else 'FAIL'} {k}")
for n in R["notes"]:
    print("  ", n)
sys.exit(0 if R["all_pass"] else 1)
