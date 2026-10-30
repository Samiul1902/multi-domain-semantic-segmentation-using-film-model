#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 orchestration harness (ordered gates, fresh subprocesses, fail-closed).

Classification: PRE_MEASUREMENT_WORKER_IMPORT_AND_UNTIMED_SMOKE_EXECUTION_AMENDMENT__HARNESS
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

SUPERSEDES the v1.2 harness for future execution (v1.2 preserved byte-for-byte).

Required order when eventually authorized:
  1. immutable source/hash preflight
  2. environment gate
  3. checkpoint file hash gate
  4. component smoke gate
  5. controlled-path smoke gate
  6. STOP if any smoke failure
  7. only then start measurement workers

!! ZERO-EXECUTION GUARD !!  main() requires PHASE34_EXECUTE=1. Importing this module constructs
no model, deserializes no checkpoint, runs no forward and does not time CUDA.
"""
from __future__ import annotations

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
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_3"
GATE_ENV = "PHASE34_EXECUTE"
WORKER = ROOT / "scripts" / "analysis" / "phase34_efficiency_profiling_worker_v1_3.py"

# frozen FIXED arm order (never chosen after viewing timings)
ARM_ORDER = ["GLOBAL_ONLY_C1", "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH",
             "FINAL_ROUTED_A8_C9", "G_COMPONENT", "R_PSI_COMPONENT", "B_PHI_COMPONENT",
             "S_OMEGA_COMPONENT"]
COMPONENT_SMOKE_ORDER = ["G_COMPONENT", "R_PSI_COMPONENT", "B_PHI_COMPONENT",
                         "S_OMEGA_COMPONENT"]
PATH_SMOKE_ORDER = ["SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH"]
MEASUREMENT_MODES = ["latency", "throughput", "memory"]

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")
G_MACS, B_MACS, R_MACS, S_MACS = 31551740928, 36160, 3230662656, 1168
PHASE30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def gate_1_source_and_hashes() -> dict:
    """Immutable source/hash preflight (v1.3 freeze)."""
    freeze_path = AUD / "phase34_preexecution_source_freeze_v1_3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    bad = []
    for k, v in freeze["frozen_sources"].items():
        obs = sha256_file(ROOT / v["path"])
        if obs != v["sha256"]:
            bad.append({"key": k, "path": v["path"], "expected": v["sha256"], "observed": obs})
    if bad:
        raise RuntimeError(f"FAIL-CLOSED gate 1 source mismatch: {bad}")
    return {"freeze": str(freeze_path.relative_to(ROOT)), "all_sources_match": True,
            "n_sources": len(freeze["frozen_sources"])}


def gate_2_environment() -> dict:
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
        raise RuntimeError(f"FAIL-CLOSED gate 2 environment mismatch: {env}")
    return env


def gate_3_checkpoints() -> dict:
    out = {}
    for cid, spec in C.COMPONENTS.items():
        obs = sha256_file(ROOT / spec["checkpoint"])
        if obs != spec["checkpoint_sha256"]:
            raise RuntimeError(f"FAIL-CLOSED gate 3 checkpoint mismatch {cid}")
        out[cid] = {"sha256": obs, "file_bytes": (ROOT / spec["checkpoint"]).stat().st_size}
    return out


def run_worker(arm: str, batch: int, mode: str) -> dict:
    cmd = [sys.executable, str(WORKER), "--arm", arm, "--batch", str(batch), "--mode", mode]
    env = dict(os.environ, PHASE34_EXECUTE="1")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(ROOT))
    if proc.returncode != 0:
        return {"arm": arm, "mode": mode, "status": "TECHNICAL_FAILURE",
                "returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def gate_4_component_smoke() -> dict:
    res = {}
    for arm in COMPONENT_SMOKE_ORDER:
        res[arm] = run_worker(arm, C.PRIMARY_LATENCY_BATCH_SIZE, "smoke")
    ok = all(r.get("mode") == "smoke" and r.get("status") != "TECHNICAL_FAILURE" for r in res.values())
    return {"results": res, "pass": ok}


def gate_5_path_smoke() -> dict:
    res = {}
    for arm in PATH_SMOKE_ORDER:
        res[arm] = run_worker(arm, C.PRIMARY_LATENCY_BATCH_SIZE, "smoke")
    ok = all(r.get("mode") == "smoke" and r.get("status") != "TECHNICAL_FAILURE" for r in res.values())
    return {"results": res, "pass": ok}


def conditional_weighted(latency_ms: dict) -> dict:
    skip = latency_ms.get("SKIP_CONTROLLED_PATH")
    ex = latency_ms.get("EXECUTE_CONTROLLED_PATH")
    if skip is None or ex is None:
        return {"eligible": False, "reason": "BOTH_SKIP_AND_EXECUTE_PATH_LATENCIES_REQUIRED"}
    p_skip = PHASE30["SKIP"] / PHASE30["n"]
    p_ex = (PHASE30["EXECUTE_THEN_ACCEPT"] + PHASE30["EXECUTE_THEN_REJECT"]) / PHASE30["n"]
    return {"eligible": True, "classification": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
            "weighted_mean_ms": p_skip * skip + p_ex * ex,
            "formula": "L_weighted = (635/875)*L_SKIP + (240/875)*L_EXECUTE",
            "statistic": "mean", "NOT_DIRECT_HOLDOUT_RUNTIME": True,
            "NOT_END_TO_END_PIPELINE_LATENCY": True, "phase30_qualifier": PHASE30_QUALIFIER}


def main() -> int:
    if os.environ.get(GATE_ENV) != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    report = OrderedDict([("revision", REVISION), ("repo_root", str(REPO_ROOT)),
                          ("started_utc", time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))])
    report["gate_1_source_and_hashes"] = gate_1_source_and_hashes()
    report["gate_2_environment"] = gate_2_environment()
    report["gate_3_checkpoints"] = gate_3_checkpoints()
    report["gate_4_component_smoke"] = gate_4_component_smoke()
    if not report["gate_4_component_smoke"]["pass"]:
        report["STOPPED_AT"] = "GATE_4_COMPONENT_SMOKE"
        (AUD / "phase34_efficiency_profiling_execution_results_v1_3.json").write_text(
            json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print("STOPPED at gate 4")
        return 3
    report["gate_5_path_smoke"] = gate_5_path_smoke()
    if not report["gate_5_path_smoke"]["pass"]:
        report["STOPPED_AT"] = "GATE_5_PATH_SMOKE"
        (AUD / "phase34_efficiency_profiling_execution_results_v1_3.json").write_text(
            json.dumps(report, indent=1) + "\n", encoding="utf-8")
        print("STOPPED at gate 5")
        return 3

    results, failures, latency_ms = [], [], {}
    for arm in ARM_ORDER:
        for mode in MEASUREMENT_MODES:
            batch = (C.PRIMARY_LATENCY_BATCH_SIZE if mode in ("latency", "memory")
                     else C.SECONDARY_THROUGHPUT_BATCH_SIZE)
            rec = run_worker(arm, batch, mode)
            results.append(rec)
            if rec.get("status") == "TECHNICAL_FAILURE":
                failures.append(rec)
            elif mode == "latency":
                if rec["latency"]["n_observations"] != C.TOTAL_MEASURED_ITERATIONS:
                    raise RuntimeError(f"FAIL-CLOSED invalid latency record for {arm}")
                latency_ms[arm] = rec["latency"]["mean_ms"]
    report["arm_order"] = ARM_ORDER
    report["worker_results"] = results
    report["technical_failures"] = failures
    report["conditional_weighted_runtime"] = conditional_weighted(latency_ms)
    report["analytical_macs"] = {"C1": G_MACS, "C2": G_MACS + R_MACS,
                                 "A8_C9": G_MACS + B_MACS + (240 / 875) * (R_MACS + S_MACS),
                                 "gated_C9": G_MACS + B_MACS + R_MACS + S_MACS}
    report["flop_mac_profiler_executions"] = 0
    out = AUD / "phase34_efficiency_profiling_execution_results_v1_3.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
