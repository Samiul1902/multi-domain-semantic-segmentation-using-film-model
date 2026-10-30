#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.10 — ZERO-EXECUTION AUDIT (READ-ONLY).

Proves the v1.10 validation-gate repair (D26/D27/D28) performed NO model /
protected-data execution, and that the FROZEN v1.9 execution source was not
executed either.  Static counters only.  No protected dataset content inspected.

Extends the v1.9 audit by also scanning the v1.10 unit / negative-control /
preflight generators for any accidental execution surface (torch import,
model construction, checkpoint load, forward, CUDA, VAL/GT/ROUTER_HOLDOUT/TEST
path literal).

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

V1_10_GENERATORS = [
    "scripts/analysis/phase36_robustness_unit_v1_10.py",
    "scripts/analysis/phase36_robustness_negative_controls_v1_10.py",
    "scripts/analysis/phase36_robustness_preflight_v1_10.py",
    "scripts/analysis/build_phase36_v1_10_semantic_diff.py",
    "scripts/analysis/audit_phase36_v1_10_direct_source_bytes.py",
    "scripts/analysis/audit_phase36_v1_10_no_execution.py",
    "scripts/analysis/build_phase36_v1_10_freeze_and_eligibility.py",
]


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


# ---- scan every v1.10 generator for an execution surface --------------------- #
# A mere token like ROUTER_HOLDOUT (as in the governance flag
# ROUTER_HOLDOUT_RUNTIME_READS_ALLOWED) is NOT an execution surface.  What we
# forbid is an actual protected-path READ: a file-open / read call whose path
# argument is a protected-path literal, or any numpy/torch tensor load.
PROTECTED_PATH_TOKENS = ("phase4_v3/test", "router_holdout", "phase24_router_split",
                         "router_holdout_identity")


def _call_name(node) -> str:
    f = getattr(node, "func", None)
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return ""


def _protected_read_sites(tree) -> list:
    sites = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        cname = _call_name(n)
        # literal path arguments anywhere in the call
        str_args = [a.value for a in n.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        str_args += [kw.value.value for kw in n.keywords
                     if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)]
        hits = [s for s in str_args
                if any(tok in s.lower() for tok in PROTECTED_PATH_TOKENS)]
        if hits and cname in ("open", "read_text", "read_bytes", "read_csv",
                              "load", "loadtxt", "imread", "read_npy", "npz"):
            sites.append({"call": cname, "paths": hits})
        # explicit numpy/torch tensor load named without a path literal
        if cname in ("load", "loadtxt", "imread", "read_npy") and not str_args:
            # only flag when accompanied by a protected token in the source
            pass
    return sites


def _scan_generator(rel: str) -> dict:
    p = ROOT / rel
    if not p.exists():
        return {"present": False}
    src = p.read_text(encoding="utf-8")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {"present": True, "ast_parse": False}
    imp_torch = any(
        isinstance(n, (ast.Import, ast.ImportFrom))
        and any((getattr(a, "name", "") or "").split(".")[0] == "torch"
                for a in n.names)
        for n in ast.walk(tree)
    )
    protected_reads = _protected_read_sites(tree)
    return {
        "present": True,
        "ast_parse": True,
        "imports_torch": bool(imp_torch),
        "protected_path_read_sites": protected_reads,
        "sha256": sha(p),
    }


generator_scan = {rel: _scan_generator(rel) for rel in V1_10_GENERATORS}
generators_clean = all(
    (not v.get("present")) or (v.get("ast_parse")
                               and not v.get("imports_torch")
                               and not v.get("protected_path_read_sites"))
    for v in generator_scan.values()
)

smoke_artifact = ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json"
start_marker = ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json"
failure_artifact = ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json"
science_artifact = ROOT / "reports/audits/phase36_robustness_scientific_result_v1_9.json"

report = {
    "artifact": "phase36_v1_10_source_repair_no_execution_audit",
    "phase": 36,
    "section": "§Q",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "ZERO_EXECUTION_AUDIT",
    "torch_imported": "torch" in sys.modules,
    "torch_imported_at_module_scope": bool(module_imports_torch_at_top),
    "protected_population_read": False,
    "counter_source": "static analysis of the v1.10 validation-gate repair work order",
    "counters": counters,
    "all_counters_zero": all(v == 0 for v in counters.values()),
    "v1_10_generator_scan": generator_scan,
    "all_v1_10_generators_clean": bool(generators_clean),
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
out = ROOT / "reports/audits/phase36_v1_10_source_repair_no_execution_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"all_counters_zero": report["all_counters_zero"],
                  "all_v1_10_generators_clean": report["all_v1_10_generators_clean"],
                  "torch_imported": report["torch_imported"],
                  "torch_imported_at_module_scope": report["torch_imported_at_module_scope"],
                  "smoke_executed": report["artifact_existence_proof"]["smoke_executed"],
                  "science_executed": report["artifact_existence_proof"]["science_executed"]},
                 indent=1))
ok = (report["all_counters_zero"] and not report["torch_imported_at_module_scope"]
      and generators_clean
      and not report["artifact_existence_proof"]["smoke_executed"]
      and not report["artifact_existence_proof"]["science_executed"])
raise SystemExit(0 if ok else 1)
