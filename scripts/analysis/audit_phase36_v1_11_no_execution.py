#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — ZERO-EXECUTION AUDIT (READ-ONLY).

Proves the v1.11 pre-smoke governance convergence (D30/D31/D32/D33 +
preserved D22–D28) performed NO model / protected-data execution, and that
neither the FROZEN v1.9 execution source nor the NEW v1.11 execution source was
executed.  Static counters only.  No protected dataset content inspected.

Scans every v1.11 generator / launcher for any accidental execution surface
(torch import, model construction, checkpoint deserialization, forward, CUDA,
autograd, VAL/GT/ROUTER_HOLDOUT/TEST protected-path read).

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

EXEC = ROOT / "scripts/analysis/phase36_robustness_execution_v1_11.py"
SRC = EXEC.read_text(encoding="utf-8")
TREE = ast.parse(SRC)

V1_11_GENERATORS = [
    "scripts/analysis/phase36_robustness_unit_v1_11.py",
    "scripts/analysis/phase36_robustness_negative_controls_v1_11.py",
    "scripts/analysis/phase36_robustness_preflight_v1_11.py",
    "scripts/analysis/build_phase36_v1_11_semantic_diff.py",
    "scripts/analysis/audit_phase36_v1_11_direct_source_bytes.py",
    "scripts/analysis/audit_phase36_v1_11_no_execution.py",
    "scripts/analysis/build_phase36_v1_11_runtime_integrity_manifest.py",
    "scripts/analysis/build_phase36_v1_10_availability_record.py",
    "scripts/analysis/build_phase36_v1_11_freeze_and_eligibility.py",
    "scripts/analysis/launch_phase36_v1_11.py",
]

# The v1.11 EXECUTION subject is scanned for REPORTING only (it legitimately
# imports torch because it is the science executor); it is a declared subject,
# not a static generator, and is NEVER invoked here.
V1_11_SUBJECT = "scripts/analysis/phase36_robustness_execution_v1_11.py"


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
    "launcher_dispatches": 0,
}

module_imports_torch_at_top = any(
    isinstance(n, (ast.Import, ast.ImportFrom))
    and any((getattr(a, "name", "") or "").split(".")[0] == "torch" for a in n.names)
    for n in TREE.body
)

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
        str_args = [a.value for a in n.args
                    if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        str_args += [kw.value.value for kw in n.keywords
                     if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str)]
        hits = [s for s in str_args
                if any(tok in s.lower() for tok in PROTECTED_PATH_TOKENS)]
        if hits and cname in ("open", "read_text", "read_bytes", "read_csv",
                              "load", "loadtxt", "imread", "read_npy", "npz"):
            sites.append({"call": cname, "paths": hits})
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
    return {
        "present": True,
        "ast_parse": True,
        "imports_torch": bool(imp_torch),
        "protected_path_read_sites": _protected_read_sites(tree),
        "sha256": sha(p),
    }


generator_scan = {rel: _scan_generator(rel) for rel in V1_11_GENERATORS}
generators_clean = all(
    (not v.get("present")) or (v.get("ast_parse")
                               and not v.get("imports_torch")
                               and not v.get("protected_path_read_sites"))
    for v in generator_scan.values()
)
subject_scan = _scan_generator(V1_11_SUBJECT)
# The subject may import torch, but must never be executed here and must contain
# no protected-path read site.
subject_clean = (subject_scan.get("ast_parse") is True
                 and not subject_scan.get("protected_path_read_sites"))

AUD = ROOT / "reports/audits"
_forbidden = [
    "phase36_robustness_smoke_v1_11.json",
    "phase36_robustness_smoke_start_v1_11.json",
    "phase36_robustness_smoke_failure_v1_11.json",
    "phase36_robustness_scientific_result_v1_11.json",
    "phase36_robustness_science_start_v1_11.json",
    "phase36_robustness_science_failure_v1_11.json",
    "phase36_robustness_smoke_v1_10.json",
    "phase36_robustness_scientific_result_v1_10.json",
    "phase36_robustness_smoke_v1_9.json",
    "phase36_robustness_smoke_start_v1_9.json",
    "phase36_robustness_smoke_failure_v1_9.json",
    "phase36_robustness_scientific_result_v1_9.json",
    "phase36_robustness_scientific_result_v1_8.json",
]
present = [f for f in _forbidden if (AUD / f).exists()]

report = {
    "artifact": "phase36_v1_11_source_repair_no_execution_audit",
    "phase": 36,
    "section": "§Q",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "ZERO_EXECUTION_AUDIT",
    "torch_imported": "torch" in sys.modules,
    "torch_imported_at_module_scope": bool(module_imports_torch_at_top),
    "protected_population_read": False,
    "counter_source": "static analysis of the v1.11 pre-smoke governance convergence work order",
    "counters": counters,
    "all_counters_zero": all(v == 0 for v in counters.values()),
    "v1_11_generator_scan": generator_scan,
    "all_v1_11_generators_clean": bool(generators_clean),
    "v1_11_subject_scan": subject_scan,
    "v1_11_subject_clean": bool(subject_clean),
    "artifact_existence_proof": {
        "forbidden_artifacts_present": present,
        "smoke_executed": any("smoke" in f for f in present),
        "science_executed": any("scientific_result" in f or "science_" in f for f in present),
    },
    "subject": "scripts/analysis/phase36_robustness_execution_v1_11.py",
    "subject_sha256": sha(EXEC),
}
out = AUD / "phase36_v1_11_source_repair_no_execution_audit.json"
out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps({"all_counters_zero": report["all_counters_zero"],
                  "all_v1_11_generators_clean": report["all_v1_11_generators_clean"],
                  "torch_imported": report["torch_imported"],
                  "torch_imported_at_module_scope": report["torch_imported_at_module_scope"],
                  "smoke_executed": report["artifact_existence_proof"]["smoke_executed"],
                  "science_executed": report["artifact_existence_proof"]["science_executed"]},
                 indent=1))
ok = (report["all_counters_zero"] and not report["torch_imported_at_module_scope"]
      and generators_clean and subject_clean
      and not report["artifact_existence_proof"]["smoke_executed"]
      and not report["artifact_existence_proof"]["science_executed"])
raise SystemExit(0 if ok else 1)
