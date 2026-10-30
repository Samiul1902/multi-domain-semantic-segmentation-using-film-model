#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.4 LATENCY-ONLY orchestration harness (six canonical arms, fresh subprocesses).

Classification: LATENCY_GRANULARITY_REPAIR__ORCHESTRATION_HARNESS
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_4

Scope: LATENCY ONLY. This harness NEVER invokes throughput or memory worker modes, NEVER
invokes alias arms physically, and NEVER runs a MAC/FLOP profiler.

!! ZERO-EXECUTION GUARD !!  main() requires PHASE34_EXECUTE=1. Importing this module constructs
no model, deserializes no checkpoint, runs no forward and does not time CUDA.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from collections import OrderedDict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if not ((REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()):
    raise RuntimeError(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))

import phase34_v1_2_common as C  # noqa: E402

ROOT = REPO_ROOT
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_4"
GATE_ENV = "PHASE34_EXECUTE"
WORKER = ROOT / "scripts" / "analysis" / "phase34_latency_worker_v1_4.py"

ARM_ORDER = ["GLOBAL_ONLY_C1", "R_PSI_COMPONENT", "B_PHI_COMPONENT", "S_OMEGA_COMPONENT",
             "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]
ALIASES = {"G_COMPONENT": "GLOBAL_ONLY_C1", "FINAL_ROUTED_A8_C9": "EXECUTE_CONTROLLED_PATH"}
WARMUP = 50
BLOCKS = 5
PER_BLOCK = 200
TOTAL = BLOCKS * PER_BLOCK

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
PHASE30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}

PRESERVED_V13 = OrderedDict([
    ("reports/tables/phase34_batch8_throughput_results_v1_3.csv",
     "ac2b21aa89086870af59cd341ac51122568a871981fc9df9a4f323ae58c84c6c"),
    ("reports/tables/phase34_gpu_memory_results_v1_3.csv",
     "6df4e0941dcd33ab90196f7572528afbc7848d9329c6bcb6940978813dd02979"),
    ("reports/tables/phase34_static_resource_profile_v1_3.csv",
     "f4c36efd4fedb07778cf8b752a1e54ec91b19b78d9d1c6f4ef300cb5bdb73343"),
    ("reports/tables/phase34_analytical_compute_summary_v1_3.csv",
     "bbe1d933c24e297454ec7afee0f64d00bc79dbcf815d747df2ec2f742c93f71f"),
    ("reports/audits/phase34_model_identity_and_smoke_gate_v1_3.json",
     "8e398f9c405e4a9bcdfb52ed60fdadd03c8d348807b87fab1801839fe45873c6"),
    ("reports/audits/phase34_smoke_execution_terminal_v1_3.json",
     "4336b7b96d1b3874745feb52af6738e52174be644673f63642cd2feb6e542511"),
    ("reports/audits/phase34_preexecution_source_freeze_v1_3.json",
     "c7ee684c24d3ddaf4af3eeca6eed3bd44c856c9152b6eccaec0443e6df14c742"),
])


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def gate_preserved() -> dict:
    out = {}
    for rel, exp in PRESERVED_V13.items():
        obs = sha256_file(ROOT / rel)
        out[rel] = {"expected": exp, "observed": obs, "match": obs == exp}
        if obs != exp:
            raise RuntimeError(f"FAIL-CLOSED preserved-evidence mismatch: {rel}")
    return out


def gate_environment() -> dict:
    import platform

    import torch
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    env = {"os": platform.platform(), "python": platform.python_version(),
           "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
           "cudnn": torch.backends.cudnn.version(),
           "gpu": prop.name if prop else None,
           "cc": f"{prop.major}.{prop.minor}" if prop else None,
           "vram_bytes": prop.total_memory if prop else None}
    if env["gpu"] != "NVIDIA GeForce RTX 3060 Ti" or env["torch"] != "2.6.0+cu124":
        raise RuntimeError(f"FAIL-CLOSED environment mismatch: {env}")
    return env


def gate_checkpoints() -> dict:
    out = {}
    for cid, spec in C.COMPONENTS.items():
        obs = sha256_file(ROOT / spec["checkpoint"])
        if obs != spec["checkpoint_sha256"]:
            raise RuntimeError(f"FAIL-CLOSED checkpoint mismatch {cid}")
        out[cid] = {"sha256": obs}
    return out


def run_worker(arm: str) -> dict:
    cmd = [sys.executable, str(WORKER), "--arm", arm, "--mode", "latency"]
    env = dict(os.environ, PHASE34_EXECUTE="1")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(ROOT))
    if proc.returncode != 0:
        return {"arm": arm, "status": "TECHNICAL_FAILURE", "returncode": proc.returncode,
                "stderr_tail": proc.stderr[-2500:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> int:
    if os.environ.get(GATE_ENV) != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    report = OrderedDict([("revision", REVISION), ("repo_root", str(REPO_ROOT)),
                          ("scope", "LATENCY_ONLY"),
                          ("started_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))])
    report["preserved_v13_evidence"] = gate_preserved()
    report["environment"] = gate_environment()
    report["checkpoints"] = gate_checkpoints()
    report["arm_order"] = ARM_ORDER
    report["aliases_not_executed"] = ALIASES
    report["physical_latency_worker_runs"] = len(ARM_ORDER)

    summaries, obs_rows, failures = [], [], []
    for arm in ARM_ORDER:
        rec = run_worker(arm)
        if rec.get("status") == "TECHNICAL_FAILURE":
            failures.append(rec)
            continue
        summaries.append(rec["summary"])
        obs_rows.extend(rec["observations"])

    # ---- raw observation artifact (§O) ----
    obs_path = TAB / "phase34_batch1_latency_observations_v1_4.csv"
    with open(obs_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arm", "block_id", "iteration_within_block", "global_iteration_index",
                    "task_id", "latency_ms"])
        for r in obs_rows:
            w.writerow([r["arm"], r["block_id"], r["iteration_within_block"],
                        r["global_iteration_index"], r["task_id"], repr(r["latency_ms"])])

    pairs = [(r["arm"], r["global_iteration_index"]) for r in obs_rows]
    vals = [r["latency_ms"] for r in obs_rows]
    obs_checks = {
        "rows": len(obs_rows), "expected_rows": len(ARM_ORDER) * TOTAL,
        "duplicate_arm_iteration_pairs": len(pairs) - len(set(pairs)),
        "missing_observations": len(ARM_ORDER) * TOTAL - len(obs_rows),
        "non_finite": sum(1 for v in vals if not (v == v and abs(v) != float("inf"))),
        "non_positive": sum(1 for v in vals if v <= 0),
        "observations_per_arm": {a: sum(1 for r in obs_rows if r["arm"] == a)
                                 for a in ARM_ORDER},
    }

    # ---- summary table (§P) ----
    sum_path = TAB / "phase34_batch1_latency_results_v1_4.csv"
    with open(sum_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["arm", "n", "batch_size", "warmup_count", "mean_ms", "std_ms", "p50_ms",
                    "p90_ms", "p95_ms", "p99_ms", "min_ms", "max_ms", "timer_type",
                    "precision_semantics", "task_schedule", "hardware"])
        for s in summaries:
            w.writerow([s["arm"], s["n"], s["batch_size"], s["warmup_count"], repr(s["mean_ms"]),
                        repr(s["std_ms"]), repr(s["p50_ms"]), repr(s["p90_ms"]),
                        repr(s["p95_ms"]), repr(s["p99_ms"]), repr(s["min_ms"]),
                        repr(s["max_ms"]), s["timer_type"], s["precision_semantics"],
                        s["task_schedule"], "NVIDIA GeForce RTX 3060 Ti"])

    # ---- conditional runtime (§Q) ----
    by_arm = {s["arm"]: s for s in summaries}
    cond = None
    if "SKIP_CONTROLLED_PATH" in by_arm and "EXECUTE_CONTROLLED_PATH" in by_arm:
        p_skip = PHASE30["SKIP"] / PHASE30["n"]
        p_ex = (PHASE30["EXECUTE_THEN_ACCEPT"] + PHASE30["EXECUTE_THEN_REJECT"]) / PHASE30["n"]
        l_skip = by_arm["SKIP_CONTROLLED_PATH"]["mean_ms"]
        l_ex = by_arm["EXECUTE_CONTROLLED_PATH"]["mean_ms"]
        cond = {"L_SKIP_mean_ms": l_skip, "L_EXECUTE_mean_ms": l_ex,
                "L_weighted_ms": p_skip * l_skip + p_ex * l_ex,
                "formula": "L_weighted_v1_4 = (635/875)*mean(SKIP) + (240/875)*mean(EXECUTE)",
                "classification": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
                "NOT_DIRECT_HOLDOUT_RUNTIME": True,
                "NOT_END_TO_END_PIPELINE_LATENCY": True,
                "phase30_qualifier": PHASE30_QUALIFIER}
        with open(TAB / "phase34_conditional_runtime_estimate_v1_4.csv", "w", newline="",
                  encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["quantity", "value", "unit", "note"])
            w.writerow(["L_SKIP_mean", l_skip, "ms", "SKIP = G + B_phi"])
            w.writerow(["L_EXECUTE_mean", l_ex, "ms", "EXECUTE = G + B_phi + R_psi + S_omega"])
            w.writerow(["L_weighted", cond["L_weighted_ms"], "ms",
                        "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE; "
                        "NOT_DIRECT_HOLDOUT_RUNTIME; NOT_END_TO_END_PIPELINE_LATENCY; "
                        + PHASE30_QUALIFIER])

    report["latency_summaries"] = summaries
    report["observation_checks"] = obs_checks
    report["conditional_runtime"] = cond
    report["technical_failures"] = failures
    report["throughput_invoked"] = False
    report["memory_invoked"] = False
    report["mac_flop_profiler_executions"] = 0
    out = AUD / "phase34_latency_execution_results_v1_4.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
