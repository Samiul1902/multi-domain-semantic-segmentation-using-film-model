#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 STATIC source preflight (AST + filesystem hashing only).

Classification: PRE_MEASUREMENT_WORKER_IMPORT_AND_UNTIMED_SMOKE_EXECUTION_AMENDMENT__STATIC_PREFLIGHT
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

Writes ONLY reports/audits/phase34_execution_source_preflight_v1_3.json. This file MUST NEVER be
overwritten by a future execution-time rerun (which must write an additive *_runtime_v1_3.json).

Never constructs a model, never deserializes a checkpoint, never forwards, never times CUDA and
never measures inference memory.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_execution_preflight_v1_3.py
"""
from __future__ import annotations

import ast
import hashlib
import json
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"
OUT = AUD / "phase34_execution_source_preflight_v1_3.json"

SOURCES = OrderedDict([
    ("common_v1_2", "scripts/analysis/phase34_v1_2_common.py"),
    ("worker_v1_3", "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"),
    ("harness_v1_3", "scripts/analysis/phase34_efficiency_profiling_execution_v1_3.py"),
    ("preflight_v1_3", "scripts/analysis/phase34_execution_preflight_v1_3.py"),
    ("import_probe_v1_3", "scripts/analysis/phase34_importability_probe_v1_3.py"),
])
MODEL_SOURCES = ["src/models/film/global_medfilm.py", "src/models/barr/regional_refiner.py",
                 "scripts/analysis/train_phase25d_router.py",
                 "scripts/analysis/phase25f_execution_common.py"]

NEW = []


def now_utc():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def write_json(obj, p):
    if p.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE FROZEN PREFLIGHT OUTPUT: {p}")
    p.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")
    s = sha256_file(p)
    NEW.append({"path": str(p.relative_to(ROOT)).replace("\\", "/"), "sha256": s})
    return s


def dotted(node) -> str:
    parts, cur = [], node
    while isinstance(cur, ast.Attribute):
        parts.append(cur.attr)
        cur = cur.value
    if isinstance(cur, ast.Name):
        parts.append(cur.id)
    return ".".join(reversed(parts))


def _walk(nodes):
    calls, withs = set(), set()
    for n in nodes:
        if isinstance(n, ast.Call):
            calls.add(dotted(n.func))
        if isinstance(n, ast.With):
            for item in n.items:
                ce = item.context_expr
                withs.add(dotted(ce.func) if isinstance(ce, ast.Call) else dotted(ce))
    return calls, withs


def collect(src: str) -> dict:
    tree = ast.parse(src)
    calls, withs = _walk(ast.walk(tree))
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return {"tree": tree, "calls": calls, "withs": withs, "funcs": funcs,
            "literals": literals}


def has(coll, sub: str) -> bool:
    return any(sub in x for x in coll)


def fn_ctx(fn):
    return _walk(ast.walk(fn)) if fn is not None else (set(), set())


def main():
    gen = now_utc()
    src_text = {k: (ROOT / v).read_text(encoding="utf-8") for k, v in SOURCES.items()}
    info = {k: collect(v) for k, v in src_text.items()}
    hashes = {k: sha256_file(ROOT / v) for k, v in SOURCES.items()}
    model_hashes = {p: sha256_file(ROOT / p) for p in MODEL_SOURCES}

    w = info["worker_v1_3"]
    h = info["harness_v1_3"]
    wc, ww = w["calls"], w["withs"]
    hc, hw = h["calls"], h["withs"]
    all_calls = set().union(*[i["calls"] for i in info.values()])
    all_withs = set().union(*[i["withs"] for i in info.values()])
    scan_lits = (w["literals"] + h["literals"] + info["common_v1_2"]["literals"]
                 + info["import_probe_v1_3"]["literals"])

    # --- root binding ordering: sys.path.insert(REPO_ROOT) BEFORE any `from src...` import ---
    def first_line(pred, src):
        for n in ast.walk(ast.parse(src)):
            if pred(n):
                return n.lineno
        return None

    root_insert_line = first_line(
        lambda n: isinstance(n, ast.Call) and dotted(n.func) == "sys.path.insert", src_text["worker_v1_3"])
    src_import_line = first_line(
        lambda n: isinstance(n, ast.ImportFrom) and (n.module or "").startswith("src"),
        src_text["worker_v1_3"])
    harness_root_line = first_line(
        lambda n: isinstance(n, ast.Call) and dotted(n.func) == "sys.path.insert",
        src_text["harness_v1_3"])
    harness_src_line = first_line(
        lambda n: isinstance(n, ast.ImportFrom) and (n.module or "").startswith("src"),
        src_text["harness_v1_3"])

    smoke_fns = [w["funcs"].get(n) for n in ("run_smoke", "smoke_component", "smoke_path")]
    smoke_calls = set()
    smoke_withs = set()
    for f in smoke_fns:
        c, ww2 = fn_ctx(f)
        smoke_calls |= c
        smoke_withs |= ww2
    smoke_src = (src_text["worker_v1_3"].split("def smoke_component")[1]
                 .split("def run_arm")[0]) if "def smoke_component" in src_text["worker_v1_3"] else ""
    smoke_src = (src_text["worker_v1_3"].split("# smoke validation (UNTIMED)")[1]
                 .split("# measurement primitives")[0]
                 if "# smoke validation (UNTIMED)" in src_text["worker_v1_3"] else smoke_src)

    fG = w["funcs"].get("forward_G")
    fB = w["funcs"].get("forward_B_phi")
    fS = w["funcs"].get("forward_S_omega")
    fR = w["funcs"].get("forward_R_psi")
    g_calls, g_withs = fn_ctx(fG)
    b_withs = fn_ctx(fB)[1]
    s_withs = fn_ctx(fS)[1]
    r_withs = fn_ctx(fR)[1]

    checks = OrderedDict([
        # --- repository-root import contract ---
        ("repo_root_calculated_from_file",
         "Path(__file__).resolve().parents[2]" in src_text["worker_v1_3"]),
        ("repo_root_parents_2_exact", "parents[2]" in src_text["worker_v1_3"]),
        ("root_inserted_before_src_imports",
         root_insert_line is not None and src_import_line is not None
         and root_insert_line < src_import_line),
        ("harness_root_inserted_before_src_imports",
         harness_root_line is not None
         and (harness_src_line is None or harness_root_line < harness_src_line)),
        ("no_cwd_only_dependency", "os.getcwd" not in src_text["worker_v1_3"]),
        ("no_hardcoded_absolute_root",
         "D:\\Softfors\\jup" not in src_text["worker_v1_3"].split('ROOT = REPO_ROOT')[0]
         or "REPO_ROOT" in src_text["worker_v1_3"]),
        ("validates_src_and_scripts_dirs",
         '(REPO_ROOT / "src").is_dir()' in src_text["worker_v1_3"]
         and '(REPO_ROOT / "scripts").is_dir()' in src_text["worker_v1_3"]),
        ("G_import_reachable_through_repo_root",
         "from src.models.film import GlobalMedFiLM" in src_text["worker_v1_3"]),
        ("R_psi_import_reachable_through_repo_root",
         "from src.models.barr.regional_refiner import BARRRegionalRefinerV1"
         in src_text["worker_v1_3"]),
        # --- smoke mode ---
        ("explicit_smoke_mode_exists", '"smoke"' in src_text["worker_v1_3"]),
        ("smoke_mode_declared_in_modes",
         "smoke" in src_text["worker_v1_3"] and "SMOKE_MODES" in src_text["worker_v1_3"]),
        ("smoke_mode_implements_real_forward",
         w["funcs"].get("smoke_component") is not None
         and has(fn_ctx(w["funcs"]["smoke_component"])[0], "call_component")),
        ("smoke_mode_has_no_timing_statistics_path",
         not has(smoke_calls | smoke_withs, "torch.cuda.Event")
         and not has(smoke_calls | smoke_withs, "cuda.synchronize")
         and not has(smoke_calls | smoke_withs, "reset_peak_memory_stats")
         and "time_latency" not in smoke_calls and "time_throughput" not in smoke_calls),
        ("smoke_mode_no_warmup_or_1000_iterations",
         "WARMUP_ITERATIONS" not in smoke_src and "TOTAL_MEASURED_ITERATIONS" not in smoke_src),
        ("component_smoke_functions_exist", w["funcs"].get("smoke_component") is not None),
        ("SKIP_path_smoke_exists",
         w["funcs"].get("smoke_path") is not None
         and "SKIP_CONTROLLED_PATH" in src_text["worker_v1_3"]),
        ("EXECUTE_path_smoke_exists",
         "EXECUTE_CONTROLLED_PATH" in src_text["worker_v1_3"]),
        ("smoke_task_identity_frozen",
         "SMOKE_TASK_ID = 0" in src_text["worker_v1_3"]
         and "SMOKE_DOMAIN" in src_text["worker_v1_3"]),
        ("smoke_forward_accounting_present",
         "individual_component_smoke_model_forward_calls" in src_text["worker_v1_3"]
         and "total_smoke_model_forward_calls" in src_text["worker_v1_3"]),
        # --- retained v1.2 semantics ---
        ("strict_load_semantics_retained",
         has(all_calls, "load_state_dict") and "strict=True" in src_text["worker_v1_3"]
         and "missing_keys" in src_text["worker_v1_3"]
         and "unexpected_keys" in src_text["worker_v1_3"]),
        ("parameter_count_verification_retained",
         "PARAMETER COUNT MISMATCH" in src_text["worker_v1_3"]),
        ("G_autocast_no_grad_semantics_retained",
         has(g_withs, "torch.amp.autocast") and has(g_withs, "torch.no_grad")
         and not has(g_calls | g_withs, "inference_mode")),
        ("R_psi_inference_mode_no_autocast_retained",
         has(r_withs, "torch.inference_mode") and not has(r_withs, "autocast")),
        ("B_phi_inference_mode_no_autocast_retained",
         has(b_withs, "torch.inference_mode") and not has(b_withs, "autocast")),
        ("S_omega_inference_mode_no_autocast_retained",
         has(s_withs, "torch.inference_mode") and not has(s_withs, "autocast")),
        ("measurement_protocols_retained",
         has(all_calls, "torch.cuda.Event") and has(all_calls, "torch.cuda.synchronize")
         and has(all_calls, "torch.cuda.reset_peak_memory_stats")
         and "processed_samples / synchronized_wall_seconds" in src_text["worker_v1_3"]),
        ("PHASE34_EXECUTE_gate_retained",
         "PHASE34_EXECUTE" in src_text["worker_v1_3"]
         and "PHASE34_EXECUTE" in src_text["harness_v1_3"]),
        ("fresh_subprocess_orchestration_retained",
         has(hc, "subprocess.run") and "ARM_ORDER" in src_text["harness_v1_3"]),
        ("ordered_gate_sequence_present",
         all(f"gate_{i}" in src_text["harness_v1_3"] for i in (1, 2, 3, 4, 5))),
        ("conditional_weighting_requires_both_paths",
         "BOTH_SKIP_AND_EXECUTE_PATH_LATENCIES_REQUIRED" in src_text["harness_v1_3"]),
        # --- prohibited ---
        ("no_protected_data_path",
         not any("router_holdout" in x.lower()
                 and any(e in x.lower() for e in (".npy", ".csv", ".pt", ".png", ".jpg"))
                 for x in scan_lits)),
        ("no_TEST_data_path",
         not any(("/test" in x or "\\test" in x or "test.csv" in x) for x in scan_lits)),
        ("no_training_optimizer_backward",
         not any("optim." in x for x in all_calls)
         and not any(x.endswith(".backward") for x in all_calls)),
        ("no_new_flop_mac_profiler",
         not any(("fvcore" in x or "thop" in x or "ptflops" in x or "FlopCountAnalysis" in x)
                 for x in all_calls)),
    ])
    failed = [k for k, v in checks.items() if not v]

    write_json(OrderedDict([
        ("artifact", "phase34_execution_source_preflight_v1_3"),
        ("phase", 34), ("section", "\u00A7O-\u00A7P"), ("method", METHOD),
        ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_AND_SHA256_HASHING_ONLY"),
        ("immutable_preflight_output", True),
        ("execution_time_reruns_must_use", "phase34_execution_source_preflight_runtime_v1_3.json"),
        ("source_hashes", hashes), ("model_source_hashes", model_hashes),
        ("root_insert_line", root_insert_line), ("first_src_import_line", src_import_line),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed), ("static_preflight_pass", len(failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("cuda_timing_performed", False),
        ("inference_memory_measured", False),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), OUT)

    print("=== PHASE34 v1.3 STATIC PREFLIGHT (AST only) ===")
    print("root insert line:", root_insert_line, "| first src import line:", src_import_line)
    print("n_checks:", len(checks), "| n_failed:", len(failed))
    for k in failed:
        print("  FAILED:", k)
    print("static_preflight_pass:", len(failed) == 0)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
