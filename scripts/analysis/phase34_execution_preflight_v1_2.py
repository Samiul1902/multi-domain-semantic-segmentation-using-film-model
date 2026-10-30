#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.2 STATIC source preflight (AST + filesystem hashing only).

Classification: PRE_MEASUREMENT_EXECUTABLE_HARNESS_AND_SYNTHETIC_TASK_CONDITIONING_
                BINDING_AMENDMENT__STATIC_PREFLIGHT
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_2

This preflight NEVER constructs a model, NEVER deserializes a checkpoint, NEVER runs a
forward, NEVER initialises CUDA model execution, NEVER times CUDA and NEVER measures
inference memory. It parses source with `ast` and hashes files.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_execution_preflight_v1_2.py
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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_2"

SOURCES = OrderedDict([
    ("common", "scripts/analysis/phase34_v1_2_common.py"),
    ("worker", "scripts/analysis/phase34_efficiency_profiling_worker_v1_2.py"),
    ("harness", "scripts/analysis/phase34_efficiency_profiling_execution_v1_2.py"),
    ("preflight", "scripts/analysis/phase34_execution_preflight_v1_2.py"),
])
MODEL_SOURCES = ["src/models/film/global_medfilm.py", "src/models/barr/regional_refiner.py",
                 "src/models/barr/router_variants.py", "src/models/barr/ra_medfilm_barr.py"]

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


def _walk_collect(nodes) -> tuple:
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
    calls, withs = _walk_collect(ast.walk(tree))
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    literals = [n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    assigns = {t.id for n in ast.walk(tree) if isinstance(n, ast.Assign)
               for t in n.targets if isinstance(t, ast.Name)}
    return {"calls": calls, "withs": withs, "funcs": funcs, "literals": literals,
            "assigns": assigns}


def has(coll, sub: str) -> bool:
    return any(sub in x for x in coll)


def fn_context(func_node) -> tuple:
    """Calls + with-contexts inside a single function body."""
    return _walk_collect(ast.walk(func_node))


def main():
    gen = now_utc()
    src_text = {k: (ROOT / v).read_text(encoding="utf-8") for k, v in SOURCES.items()}
    info = {k: collect(v) for k, v in src_text.items()}
    hashes = {k: sha256_file(ROOT / v) for k, v in SOURCES.items()}
    model_hashes = {p: sha256_file(ROOT / p) for p in MODEL_SOURCES}

    all_calls = set().union(*[i["calls"] for i in info.values()])
    all_withs = set().union(*[i["withs"] for i in info.values()])
    # Prohibited-path scan excludes this preflight's own source (it legitimately names the
    # forbidden patterns as check strings).
    scan_lits = (info["worker"]["literals"] + info["harness"]["literals"]
                 + info["common"]["literals"])
    w_calls, w_withs = info["worker"]["calls"], info["worker"]["withs"]
    c_calls, c_withs = info["common"]["calls"], info["common"]["withs"]
    wc = w_calls | w_withs
    cc = c_calls | c_withs
    h_lits = info["harness"]["literals"]

    fG = info["worker"]["funcs"].get("forward_G")
    g_calls, g_withs = fn_context(fG) if fG else (set(), set())
    fB = info["worker"]["funcs"].get("forward_B_phi")
    b_calls, b_withs = fn_context(fB) if fB else (set(), set())
    fS = info["worker"]["funcs"].get("forward_S_omega")
    s_calls, s_withs = fn_context(fS) if fS else (set(), set())
    fR = info["worker"]["funcs"].get("forward_R_psi")
    r_calls, r_withs = fn_context(fR) if fR else (set(), set())

    checks = OrderedDict([
        # --- real executable model path ---
        ("actual_model_constructor_code_present",
         has(all_calls, "GlobalMedFiLM") and has(all_calls, "BARRRegionalRefinerV1")
         and has(all_calls, "BARRPostSafetyV1")),
        ("actual_strict_checkpoint_load_code_present",
         has(all_calls, "torch.load") and has(all_calls, "load_state_dict")),
        ("strict_true_present", "strict=True" in src_text["worker"]),
        ("strict_missing_and_unexpected_keys_checked",
         "missing_keys" in src_text["worker"] and "unexpected_keys" in src_text["worker"]),
        ("model_eval_calls_present", has(all_calls, ".eval")),
        ("parameter_count_verification_present",
         "expected_parameters" in src_text["worker"]
         and "PARAMETER COUNT MISMATCH" in src_text["worker"]),
        # --- G canonical semantics ---
        ("G_autocast_enabled", has(g_withs, "torch.amp.autocast")),
        ("G_autocast_dtype_float16", "float16" in src_text["worker"]),
        ("G_no_grad", has(g_withs, "torch.no_grad")),
        ("G_not_wrapped_in_inference_mode_in_primary_path",
         fG is not None and not has(g_calls | g_withs, "inference_mode")),
        # --- non-G components ---
        ("R_psi_inference_mode_no_autocast",
         has(r_withs, "torch.inference_mode") and not has(r_withs, "autocast")),
        ("B_phi_inference_mode_no_autocast",
         fB is not None and has(b_withs, "torch.inference_mode")
         and not has(b_withs, "autocast")),
        ("S_omega_inference_mode_no_autocast",
         fS is not None and has(s_withs, "torch.inference_mode")
         and not has(s_withs, "autocast")),
        ("G_autocast_does_not_wrap_other_components",
         not has(r_withs | b_withs | s_withs, "autocast")),
        # --- task conditioning binding ---
        ("task_ids_accepted_by_G_builder", has(wc, "build_G_task_ids")),
        ("domain_task_registry_explicitly_encoded",
         "DOMAIN_TASK_ID" in info["common"]["assigns"]),
        ("batch1_task_schedule_present", has(cc, "task_id_for_iteration")),
        ("batch8_balanced_task_ids_present",
         "BATCH8_TASK_VECTOR" in info["common"]["assigns"]),
        ("S_omega_valid_onehot_construction_present",
         has(cc, "torch.zeros") and has(cc, "torch.cat")),
        ("B_phi_structured_fields_bound",
         "build_Bphi_features" in info["common"]["funcs"]
         and has(wc, "build_Bphi_features")),
        # --- timing / throughput / memory ---
        ("cuda_events_timing_present", has(all_calls, "torch.cuda.Event")),
        ("cuda_synchronization_present", has(all_calls, "torch.cuda.synchronize")),
        ("throughput_denominator_implemented",
         "processed_samples / synchronized_wall_seconds" in src_text["worker"]
         and "processed / wall" in src_text["worker"]),
        ("peak_memory_operations_present",
         has(all_calls, "torch.cuda.reset_peak_memory_stats")
         and has(all_calls, "torch.cuda.max_memory_allocated")),
        ("preconstructed_inputs_outside_timed_region",
         "per_task" in src_text["worker"]),
        # --- orchestration ---
        ("fresh_subprocess_orchestration_present",
         has(all_calls, "subprocess.run") and "sys.executable" in src_text["harness"]),
        ("PHASE34_EXECUTE_gate_present",
         has(all_calls, "os.environ.get") and "PHASE34_EXECUTE" in src_text["harness"]),
        ("fixed_arm_order_present", "ARM_ORDER" in info["harness"]["assigns"]),
        ("conditional_weighting_requires_both_paths",
         "BOTH_SKIP_AND_EXECUTE_PATH_LATENCIES_REQUIRED" in src_text["harness"]),
        # --- prohibited behaviour absent ---
        ("no_optimizer_backward_training_path",
         not any("optim." in x for x in all_calls)
         and not any(x.endswith(".backward") for x in all_calls)),
        ("no_router_holdout_raw_data_path",
         not any("router_holdout" in x.lower()
                 and any(e in x.lower() for e in (".npy", ".csv", ".pt", ".png", ".jpg",
                                                  ".jpeg", ".bmp"))
                 for x in scan_lits)),
        ("no_TEST_data_path",
         not any(("/test" in x or "\\test" in x or "test.csv" in x) for x in scan_lits)),
        ("no_flop_mac_profiler_execution",
         not any(("fvcore" in x or "thop" in x or "ptflops" in x
                  or "FlopCountAnalysis" in x) for x in all_calls)),
    ])
    failed = [k for k, v in checks.items() if not v]

    write_json(OrderedDict([
        ("artifact", "phase34_execution_source_preflight_v1_2"),
        ("phase", 34), ("section", "\u00a7W"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_AND_SHA256_HASHING_ONLY"),
        ("source_hashes", hashes), ("model_source_hashes", model_hashes),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed), ("static_preflight_pass", len(failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("cuda_model_execution_initialized", False),
        ("cuda_timing_performed", False), ("inference_memory_measured", False),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), AUD / "phase34_execution_source_preflight_v1_2.json")

    print("=== PHASE34 v1.2 STATIC PREFLIGHT (AST only) ===")
    print("n_checks:", len(checks), "| n_failed:", len(failed))
    if failed:
        for k in failed:
            print("  FAILED:", k)
    print("static_preflight_pass:", len(failed) == 0)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
