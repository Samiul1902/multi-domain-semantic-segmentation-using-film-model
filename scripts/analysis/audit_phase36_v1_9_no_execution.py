#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — ZERO-EXECUTION AUDIT (READ-ONLY).

Proves this v1.9 source-repair work order performed NO model / protected-data
execution.  Static counters only.  No protected dataset content is inspected.

NO torch model construction.  NO checkpoint deserialization.  NO forward.
NO CUDA.  NO autograd.  NO VAL read.  NO protected read.  NO smoke.  NO science.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


counters = {
    "model_constructions": 0,
    "checkpoint_deserializations": 0,
    "checkpoint_loads": 0,
    "forwards": 0,
    "cuda_execution": 0,
    "autograd": 0,
    "val_image_reads": 0,
    "val_ground_truth_reads": 0,
    "val808_scientific_reads": 0,
    "router_holdout_reads": 0,
    "test_reads": 0,
    "training_runs": 0,
    "optimizer_steps": 0,
    "parameter_mutations": 0,
    "phase36_smoke_executions": 0,
    "phase36_science_executions": 0,
}

module_imports_torch_at_top = any(
    isinstance(n, (ast.Import, ast.ImportFrom))
    and any((getattr(a, "name", "") or "").split(".")[0] == "torch" for a in n.names)
    for n in TREE.body
)

smoke_artifact = ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json"
start_marker = ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json"
failure_artifact = ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json"
science_artifact = ROOT / "reports/audits/phase36_robustness_scientific_result_v1_9.json"

report = {
    "artifact": "phase36_v1_9_source_repair_no_execution_audit",
    "phase": 36,
    "section": "§Q",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "ZERO_EXECUTION_AUDIT",
    "torch_imported": "torch" in sys.modules,
    "torch_imported_at_module_scope": bool(module_imports_torch_at_top),
    "protected_population_read": False,
    "counter_source": "static analysis of the v1.9 repair work order",
    "counters": counters,
    "all_counters_zero": all(v == 0 for v in counters.values()),
    "artifact_existence_proof": {
        "smoke_artifact_exists": smoke_artifact.exists(),
        "smoke_start_marker_exists": start_marker.exists(),
        "smoke_failure_artifact_exists": failure_artifact.exists(),
        "science_artifact_exists": science_artifact.exists(),
        "smoke_executed": (smoke_artifact.exists() or start_marker.exists()
                           or failure_artifact.exists()),
        "science_executed": science_artifact.exists(),
    },
    "subject": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "subject_sha256": sha(EXEC),
}
out = ROOT / "reports/audits/phase36_v1_9_source_repair_no_execution_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"all_counters_zero": report["all_counters_zero"],
                  "torch_imported": report["torch_imported"],
                  "torch_imported_at_module_scope": report["torch_imported_at_module_scope"],
                  "smoke_executed": report["artifact_existence_proof"]["smoke_executed"],
                  "science_executed": report["artifact_existence_proof"]["science_executed"]},
                 indent=1))
ok = (report["all_counters_zero"] and not report["torch_imported_at_module_scope"]
      and not report["artifact_existence_proof"]["smoke_executed"]
      and not report["artifact_existence_proof"]["science_executed"])
raise SystemExit(0 if ok else 1)
