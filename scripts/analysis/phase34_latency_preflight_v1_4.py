#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.4 static latency preflight (AST + hashing only; no model execution).

Classification: LATENCY_GRANULARITY_REPAIR__STATIC_PREFLIGHT
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_4

Writes reports/audits/phase34_latency_preflight_v1_4.json (write-once). Never constructs a
model, never deserializes a checkpoint, never forwards, never times CUDA.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_latency_preflight_v1_4.py
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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"
OUT = AUD / "phase34_latency_preflight_v1_4.json"

SOURCES = OrderedDict([
    ("latency_worker_v1_4", "scripts/analysis/phase34_latency_worker_v1_4.py"),
    ("latency_harness_v1_4", "scripts/analysis/phase34_latency_execution_v1_4.py"),
    ("latency_preflight_v1_4", "scripts/analysis/phase34_latency_preflight_v1_4.py"),
    ("worker_v1_3_frozen", "scripts/analysis/phase34_efficiency_profiling_worker_v1_3.py"),
    ("common_v1_2", "scripts/analysis/phase34_v1_2_common.py"),
])
MODEL_SOURCES = ["src/models/film/global_medfilm.py", "src/models/barr/regional_refiner.py",
                 "scripts/analysis/train_phase25d_router.py",
                 "scripts/analysis/phase25f_execution_common.py",
                 "src/analysis/multidomain_harmonization.py"]

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


def collect(src):
    tree = ast.parse(src)
    calls, withs = _walk(ast.walk(tree))
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    lits = [n.value for n in ast.walk(tree)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    return {"calls": calls, "withs": withs, "funcs": funcs, "literals": lits}


def has(coll, sub):
    return any(sub in x for x in coll)


def main():
    gen = now_utc()
    text = {k: (ROOT / v).read_text(encoding="utf-8") for k, v in SOURCES.items()}
    info = {k: collect(v) for k, v in text.items()}
    hashes = {k: sha256_file(ROOT / v) for k, v in SOURCES.items()}
    model_hashes = {p: sha256_file(ROOT / p) for p in MODEL_SOURCES}

    w = info["latency_worker_v1_4"]
    h = info["latency_harness_v1_4"]
    wc, ww = w["calls"], w["withs"]
    hc = h["calls"]
    f_tl = w["funcs"].get("time_latency_per_forward")
    tl_calls, tl_withs = _walk(ast.walk(f_tl)) if f_tl else (set(), set())
    scan_lits = w["literals"] + h["literals"] + info["common_v1_2"]["literals"]
    all_calls = set().union(*[i["calls"] for i in info.values()])
    all_withs = set().union(*[i["withs"] for i in info.values()])

    # per-forward event pairing: Event creation inside a per-observation list comprehension
    per_forward_events = (
        'for _ in range(OBSERVATIONS_PER_BLOCK)' in text["latency_worker_v1_4"]
        and "starts[i].record()" in text["latency_worker_v1_4"]
        and "ends[i].record()" in text["latency_worker_v1_4"]
        and "starts[i].elapsed_time(ends[i])" in text["latency_worker_v1_4"])

    checks = OrderedDict([
        ("exact_six_arm_registry",
         "LATENCY_ARMS = [\"GLOBAL_ONLY_C1\", \"R_PSI_COMPONENT\", \"B_PHI_COMPONENT\", "
         "\"S_OMEGA_COMPONENT\",\n                \"SKIP_CONTROLLED_PATH\", "
         "\"EXECUTE_CONTROLLED_PATH\"]" in text["latency_worker_v1_4"]),
        ("no_physical_alias_execution",
         'ALIASES = {"G_COMPONENT": "GLOBAL_ONLY_C1", "FINAL_ROUTED_A8_C9": '
         '"EXECUTE_CONTROLLED_PATH"}' in text["latency_worker_v1_4"]
         and 'ap.add_argument("--arm", required=True, choices=LATENCY_ARMS)'
         in text["latency_worker_v1_4"]),
        ("warmup_50", "WARMUP_ITERATIONS = 50" in text["latency_worker_v1_4"]),
        ("five_blocks", "MEASUREMENT_BLOCKS = 5" in text["latency_worker_v1_4"]),
        ("two_hundred_per_block", "OBSERVATIONS_PER_BLOCK = 200" in text["latency_worker_v1_4"]),
        ("one_thousand_total_observations",
         "TOTAL_OBSERVATIONS = MEASUREMENT_BLOCKS * OBSERVATIONS_PER_BLOCK"
         in text["latency_worker_v1_4"]),
        ("one_cuda_event_interval_per_forward", per_forward_events),
        ("per_iteration_observations_persisted",
         '"global_iteration_index": gi' in text["latency_worker_v1_4"]
         and "observations" in text["latency_worker_v1_4"]
         and "phase34_batch1_latency_observations_v1_4.csv" in text["latency_harness_v1_4"]),
        ("sample_std_ddof_1", "STD_DDOF = 1" in text["latency_worker_v1_4"]
         and "np.std(arr, ddof=STD_DDOF" in text["latency_worker_v1_4"]),
        ("quantile_method_linear",
         'QUANTILE_METHOD = "linear"' in text["latency_worker_v1_4"]
         and "method=QUANTILE_METHOD" in text["latency_worker_v1_4"]),
        ("no_outlier_removal",
         not any(x in text["latency_worker_v1_4"] for x in
                 ("winsor", "clip(", "drop_outlier", "trim"))),
        ("task_schedule_exact",
         "step(gi % TASK_COUNT)" in text["latency_worker_v1_4"]
         and "0=ISIC,1=BUSI,2=KVASIR,3=KUB" in text["latency_worker_v1_4"]),
        ("canonical_precision_exact",
         "W3.load_component" in text["latency_worker_v1_4"]
         and "W3.call_component" in text["latency_worker_v1_4"]),
        ("fresh_worker_subprocess_per_arm",
         has(hc, "subprocess.run") and "for arm in ARM_ORDER" in text["latency_harness_v1_4"]),
        ("throughput_not_rerun",
         '--mode", "latency' in text["latency_harness_v1_4"]
         and "throughput_invoked" in text["latency_harness_v1_4"]),
        ("memory_not_rerun", "memory_invoked" in text["latency_harness_v1_4"]),
        ("mac_profiler_not_run",
         not any(("fvcore" in x or "thop" in x or "ptflops" in x or "FlopCountAnalysis" in x)
                 for x in all_calls)),
        ("protected_data_paths_absent",
         not any("router_holdout" in x.lower()
                 and any(e in x.lower() for e in (".npy", ".csv", ".pt", ".png", ".jpg"))
                 for x in scan_lits)),
        ("TEST_absent",
         not any(("/test" in x or "\\test" in x or "test.csv" in x) for x in scan_lits)),
        ("training_absent",
         not any("optim." in x for x in all_calls)
         and not any(x.endswith(".backward") for x in all_calls)),
        ("PHASE34_EXECUTE_gate_present",
         "PHASE34_EXECUTE" in text["latency_worker_v1_4"]
         and "PHASE34_EXECUTE" in text["latency_harness_v1_4"]),
        ("preserved_v13_evidence_bound",
         "phase34_batch8_throughput_results_v1_3.csv" in text["latency_harness_v1_4"]
         and "phase34_gpu_memory_results_v1_3.csv" in text["latency_harness_v1_4"]
         and "phase34_static_resource_profile_v1_3.csv" in text["latency_harness_v1_4"]
         and "phase34_analytical_compute_summary_v1_3.csv" in text["latency_harness_v1_4"]),
    ])
    failed = [k for k, v in checks.items() if not v]

    write_json(OrderedDict([
        ("artifact", "phase34_latency_preflight_v1_4"),
        ("phase", 34), ("section", "\u00A7S"), ("method", METHOD), ("revision", REVISION),
        ("method_of_inspection", "AST_PARSE_AND_SHA256_HASHING_ONLY"),
        ("immutable_preflight_output", True),
        ("source_hashes", hashes), ("model_source_hashes", model_hashes),
        ("checks", checks), ("n_checks", len(checks)), ("n_failed", len(failed)),
        ("failed", failed), ("static_preflight_pass", len(failed) == 0),
        ("model_constructed", False), ("checkpoint_deserialized", False),
        ("forward_executed", False), ("cuda_timing_performed", False),
        ("generated_utc", gen), ("all_pass", len(failed) == 0),
    ]), OUT)

    print("=== PHASE34 v1.4 STATIC LATENCY PREFLIGHT (AST only) ===")
    print("n_checks:", len(checks), "| n_failed:", len(failed))
    for k in failed:
        print("  FAILED:", k)
    print("static_preflight_pass:", len(failed) == 0)
    print()
    for a in NEW:
        print(f"{a['sha256']}  {a['path']}")


if __name__ == "__main__":
    main()
