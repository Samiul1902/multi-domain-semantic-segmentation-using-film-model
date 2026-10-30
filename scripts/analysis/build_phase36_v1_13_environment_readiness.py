#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.13 — ENVIRONMENT READINESS ARTIFACT builder.

DEVICE/ENVIRONMENT EVIDENCE ONLY.  Records the exact interpreter identity and
the CUDA readiness state observed under the canonical project interpreter:

    D:\\Softfors\\jup\\.venv\\Scripts\\python.exe

It calls ONLY the v1.13 launcher's ``check_interpreter_identity`` and
``check_cuda_readiness`` — both of which are DEVICE-ONLY.

NO torch.load.  NO checkpoint.  NO model construction.  NO forward.  NO smoke.
NO science.  NO VAL/GT read.  NO ROUTER_HOLDOUT.  NO TEST.

The builder REFUSES to run under any interpreter other than the canonical venv
(so the recorded evidence is always the canonical environment).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_v1_13.py"
CANONICAL = ROOT / ".venv" / "Scripts" / "python.exe"


def _sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def _load():
    spec = importlib.util.spec_from_file_location("phase36_v1_13_launcher_env", LAUNCHER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    mod = _load()

    interp = mod.check_interpreter_identity()
    if not interp["ok"]:
        print(json.dumps({
            "artifact": "phase36_v1_13_environment_readiness",
            "terminal": "PHASE36_V1_13_ENV_READINESS_REFUSED__WRONG_INTERPRETER",
            "interpreter": interp,
        }, indent=1))
        return 2

    cuda = mod.check_cuda_readiness()

    report = {
        "artifact": "phase36_v1_13_environment_readiness",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_13",
        "type": "ENVIRONMENT_READINESS_EVIDENCE",
        "governance": {
            "device_environment_only": True,
            "torch_load": False,
            "checkpoint_read": False,
            "model_construction": False,
            "model_forward": False,
            "smoke": False,
            "science": False,
            "val_image_read": False,
            "gt_read": False,
            "test_read": False,
            "router_holdout_read": False,
            "training": False,
        },
        "python_executable": sys.executable,
        "canonical_interpreter": str(CANONICAL),
        "interpreter_exact_match": bool(interp["ok"]),
        "interpreter_evidence": interp,
        "python_version": sys.version,
        "python_version_info": list(sys.version_info[:3]),
        "platform": platform.platform(),
        "torch_version": cuda["torch_version"],
        "torch_version_cuda": cuda["torch_version_cuda"],
        "cuda_is_available": cuda["cuda_is_available"],
        "cuda_device_count": cuda["cuda_device_count"],
        "current_device": cuda["current_device"],
        "device_name": cuda["device_name_0"],
        "get_device_require_cuda_success": cuda["get_device_require_cuda_success"],
        "get_device_resolved": cuda["get_device_resolved"],
        "readiness_conditions": cuda["conditions"],
        "ready_for_dispatch": bool(interp["ok"] and cuda["ok"]),
        "launcher_sha256": _sha(LAUNCHER),
        "new_scientific_choice": False,
        "note": "DEVICE/ENVIRONMENT EVIDENCE ONLY — no model/checkpoint/data execution.",
    }
    out = ROOT / "reports/audits/phase36_v1_13_environment_readiness.json"
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")

    print(f"interpreter  : {sys.executable}")
    print(f"exact match  : {report['interpreter_exact_match']}")
    print(f"torch        : {report['torch_version']} (cuda {report['torch_version_cuda']})")
    print(f"cuda avail   : {report['cuda_is_available']}  devices: {report['cuda_device_count']}")
    print(f"device name  : {report['device_name']}")
    print(f"get_device   : {report['get_device_resolved']}")
    print(f"READY        : {report['ready_for_dispatch']}")
    print("terminal: PHASE36_V1_13_ENV_READINESS_COMPLETE"
          if report["ready_for_dispatch"] else
          "terminal: PHASE36_V1_13_ENV_READINESS_INCOMPLETE")
    return 0 if report["ready_for_dispatch"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
