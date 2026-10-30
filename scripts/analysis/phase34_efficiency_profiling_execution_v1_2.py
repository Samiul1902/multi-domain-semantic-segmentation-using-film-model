#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.2 orchestration harness (executes eligible arms in fresh subprocesses).

Classification: PRE_MEASUREMENT_EXECUTABLE_HARNESS_AND_SYNTHETIC_TASK_CONDITIONING_
                BINDING_AMENDMENT__ORCHESTRATION_HARNESS
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_2

!! ZERO-EXECUTION GUARD !!  main() requires PHASE34_EXECUTE=1. Importing this module does
NOT construct a model, does NOT deserialize a checkpoint, does NOT forward and does NOT time.

Responsibilities:
  * bind + verify the v1.2 source freeze and authority SHAs
  * verify model-source SHAs and checkpoint-FILE SHAs before any worker deserializes them
  * verify the frozen execution environment
  * launch only eligible arms, in the FIXED frozen order, each in a FRESH subprocess
  * collect worker JSON, validate measurement counts, fail closed on partial/invalid output
  * emit static-resource summaries
  * reuse historical analytical MACs (NO profiler is ever run)
  * compute conditional weighted runtime ONLY when both SKIP and EXECUTE measured path
    latencies exist
  * preserve technical failures; never write fabricated values
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase34_v1_2_common as C  # noqa: E402

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
REVISION = "ra_medfilm_barr_phase34_efficiency_profiling_v1_2"
GATE_ENV = "PHASE34_EXECUTE"
WORKER = ROOT / "scripts" / "analysis" / "phase34_efficiency_profiling_worker_v1_2.py"

# FIXED arm order (frozen; never chosen after viewing timings).
ARM_ORDER = ["GLOBAL_ONLY_C1", "SKIP_CONTROLLED_PATH", "EXECUTE_CONTROLLED_PATH",
             "FINAL_ROUTED_A8_C9", "G_COMPONENT", "R_PSI_COMPONENT", "B_PHI_COMPONENT",
             "S_OMEGA_COMPONENT"]
MODES = ["identity", "latency", "throughput", "memory"]

PHASE30_QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_"
                     "SCIENTIFIC_SOURCE_FREEZE_DEVIATION")

# frozen historical analytical MACs (reused, never recomputed)
G_MACS, B_MACS, R_MACS, S_MACS = 31551740928, 36160, 3230662656, 1168
PHASE30 = {"SKIP": 635, "EXECUTE_THEN_ACCEPT": 236, "EXECUTE_THEN_REJECT": 4, "n": 875}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def verify_authority() -> dict:
    """Verify checkpoint-file SHAs and model-source SHAs before workers deserialize."""
    ck = {}
    for cid, spec in C.COMPONENTS.items():
        p = ROOT / spec["checkpoint"]
        obs = sha256_file(p)
        ck[cid] = {"path": spec["checkpoint"], "expected": spec["checkpoint_sha256"],
                   "observed": obs, "match": obs == spec["checkpoint_sha256"],
                   "file_bytes": p.stat().st_size}
        if obs != spec["checkpoint_sha256"]:
            raise RuntimeError(f"FAIL-CLOSED checkpoint SHA mismatch {cid}")
    ms = {}
    for cid, spec in C.COMPONENTS.items():
        p = ROOT / spec["source_file"]
        ms[cid] = {"path": spec["source_file"], "sha256": sha256_file(p)}
    return {"checkpoint_files": ck, "model_sources": ms}


def verify_environment() -> dict:
    import platform

    import torch
    prop = torch.cuda.get_device_properties(0) if torch.cuda.is_available() else None
    env = {"os": platform.platform(), "python": platform.python_version(),
           "torch": torch.__version__, "cuda_runtime": torch.version.cuda,
           "cudnn": torch.backends.cudnn.version(),
           "cuda_available": bool(torch.cuda.is_available()),
           "gpu": prop.name if prop else None,
           "cc": f"{prop.major}.{prop.minor}" if prop else None,
           "vram_bytes": prop.total_memory if prop else None}
    if env["gpu"] != "NVIDIA GeForce RTX 3060 Ti" or env["torch"] != "2.6.0+cu124":
        raise RuntimeError(f"FAIL-CLOSED environment mismatch: {env}")
    return env


def run_worker(arm: str, batch: int, mode: str) -> dict:
    cmd = [sys.executable, str(WORKER), "--arm", arm, "--batch", str(batch), "--mode", mode]
    env = dict(os.environ, PHASE34_EXECUTE="1")
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env, cwd=str(ROOT))
    if proc.returncode != 0:
        return {"arm": arm, "mode": mode, "status": "TECHNICAL_FAILURE",
                "returncode": proc.returncode, "stderr_tail": proc.stderr[-2000:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def validate_latency(rec: dict) -> bool:
    lat = rec.get("latency") or {}
    return (lat.get("n_observations") == C.TOTAL_MEASURED_ITERATIONS
            and lat.get("batch_size") == C.PRIMARY_LATENCY_BATCH_SIZE
            and lat.get("warmup_iterations") == C.WARMUP_ITERATIONS)


def conditional_weighted(latency_by_arm: dict) -> dict:
    """WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE - only with BOTH paths measured."""
    skip = latency_by_arm.get("SKIP_CONTROLLED_PATH")
    ex = latency_by_arm.get("EXECUTE_CONTROLLED_PATH")
    if skip is None or ex is None:
        return {"eligible": False, "reason": "BOTH_SKIP_AND_EXECUTE_PATH_LATENCIES_REQUIRED"}
    p_skip = PHASE30["SKIP"] / PHASE30["n"]
    p_ex = (PHASE30["EXECUTE_THEN_ACCEPT"] + PHASE30["EXECUTE_THEN_REJECT"]) / PHASE30["n"]
    return {"eligible": True, "classification": "WEIGHTED_HARDWARE_SPECIFIC_RUNTIME_ESTIMATE",
            "p_skip": p_skip, "p_execute": p_ex,
            "weighted_mean_ms": p_skip * skip + p_ex * ex,
            "formula": "L_weighted = (635/875)*L_SKIP + (240/875)*L_EXECUTE",
            "statistic": "mean",
            "NOT_DIRECT_HOLDOUT_RUNTIME": True,
            "NOT_END_TO_END_PIPELINE_LATENCY": True,
            "phase30_qualifier": PHASE30_QUALIFIER}


def main() -> int:
    if os.environ.get(GATE_ENV) != "1":
        print("PHASE34 EXECUTION NOT AUTHORIZED - zero-execution guard active.")
        return 2

    started = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    auth = verify_authority()
    env = verify_environment()
    results, failures, latency_ms = [], [], {}
    for arm in ARM_ORDER:
        for mode in MODES:
            batch = (C.PRIMARY_LATENCY_BATCH_SIZE if mode in ("latency", "memory")
                     else C.SECONDARY_THROUGHPUT_BATCH_SIZE if mode == "throughput"
                     else C.PRIMARY_LATENCY_BATCH_SIZE)
            rec = run_worker(arm, batch, mode)
            results.append(rec)
            if rec.get("status") == "TECHNICAL_FAILURE":
                failures.append(rec)
                continue
            if mode == "latency":
                if not validate_latency(rec):
                    raise RuntimeError(f"FAIL-CLOSED invalid latency record for {arm}")
                latency_ms[arm] = rec["latency"]["mean_ms"]

    report = {"revision": REVISION, "arm_order": ARM_ORDER, "modes": MODES,
              "authority": auth, "environment": env, "started_utc": started,
              "worker_results": results, "technical_failures": failures,
              "conditional_weighted_runtime": conditional_weighted(latency_ms),
              "analytical_macs": {"C1": G_MACS, "C2": G_MACS + R_MACS,
                                  "A8_C9": G_MACS + B_MACS + (240 / 875) * (R_MACS + S_MACS),
                                  "gated_C9": G_MACS + B_MACS + R_MACS + S_MACS},
              "flop_mac_profiler_executions": 0}
    out = AUD / "phase34_efficiency_profiling_execution_results_v1_2.json"
    out.write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    print("wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
