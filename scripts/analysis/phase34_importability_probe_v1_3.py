#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase34 v1.3 IMPORT-ONLY probe (no model construction, no checkpoint deserialization).

Classification: PRE_MEASUREMENT_WORKER_IMPORT_AND_UNTIMED_SMOKE_EXECUTION_AMENDMENT__IMPORT_PROBE
Revision: ra_medfilm_barr_phase34_efficiency_profiling_v1_3

Resolves the repository root from THIS FILE's location (never from cwd / PYTHONPATH / IDE), inserts
it on sys.path, then imports the canonical model classes. It NEVER constructs a model, NEVER
deserializes a checkpoint and NEVER runs a forward.

Run from repository root AND from a different cwd:
  D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase34_importability_probe_v1_3.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
_ROOT_OK = (REPO_ROOT / "src").is_dir() and (REPO_ROOT / "scripts").is_dir()
if not _ROOT_OK:
    raise SystemExit(f"repository root resolution failed: {REPO_ROOT}")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def probe() -> dict:
    import os
    results = {"cwd": os.getcwd(), "repo_root": str(REPO_ROOT),
               "repo_root_from_file": True, "imports": {}}

    def try_import(label, fn):
        try:
            obj = fn()
            results["imports"][label] = {"pass": True, "object": getattr(obj, "__name__", str(obj))}
        except Exception as e:  # noqa: BLE001
            results["imports"][label] = {"pass": False, "error": f"{type(e).__name__}: {e}"}

    try_import("G", lambda: __import__("src.models.film.global_medfilm",
                                       fromlist=["GlobalMedFiLM"]).GlobalMedFiLM)
    try_import("R_psi", lambda: __import__("src.models.barr.regional_refiner",
                                           fromlist=["BARRRegionalRefinerV1"]).BARRRegionalRefinerV1)

    def b_phi():
        import re
        import torch
        from torch import nn
        src = (REPO_ROOT / "scripts/analysis/train_phase25d_router.py").read_text(
            encoding="utf-8")
        m = re.search(r"class BARRBenefitRouterV1\(nn\.Module\):.*?(?=\ndef count_params)", src,
                      re.S)
        if m is None:
            raise RuntimeError("canonical BARRBenefitRouterV1 class block not found")
        ns = {"__name__": "phase34_probe_bphi", "torch": torch, "nn": nn,
              "F": torch.nn.functional}
        exec("import torch\nimport torch.nn as nn\nimport torch.nn.functional as F\n"
             + m.group(0), ns)
        return ns["BARRBenefitRouterV1"]

    try_import("B_phi", b_phi)

    def s_omega():
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "analysis"))
        from phase25f_execution_common import BARRPostSafetyV1
        return BARRPostSafetyV1

    try_import("S_omega", s_omega)

    results["model_constructions"] = 0
    results["checkpoint_deserializations"] = 0
    results["forwards"] = 0
    results["all_pass"] = all(v["pass"] for v in results["imports"].values())
    return results


if __name__ == "__main__":
    r = probe()
    print(json.dumps(r, indent=1))
    raise SystemExit(0 if r["all_pass"] else 1)
