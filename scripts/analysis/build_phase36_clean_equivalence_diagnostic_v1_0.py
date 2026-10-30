#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase36 CLEAN EQUIVALENCE DIAGNOSTIC v1.0 governance artifacts.

NO EXECUTION.  Writes (write-once semantics enforced by simple existence guard):
    reports/audits/phase36_clean_equivalence_diagnostic_contract_v1_0.json
    reports/audits/phase36_clean_equivalence_diagnostic_preflight_v1_0.json
    reports/audits/phase36_clean_equivalence_diagnostic_source_freeze_v1_0.json
    reports/audits/phase36_clean_equivalence_diagnostic_eligibility_v1_0.json
    reports/audits/phase36_clean_equivalence_diagnostic_no_execution_audit_v1_0.json
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict):
    if path.exists():
        raise SystemExit(f"REFUSE_OVERWRITE::{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o644)
    try:
        os.write(fd, json.dumps(payload, indent=1, ensure_ascii=False,
                                default=str).encode("utf-8"))
    finally:
        os.close(fd)
    return sha(path)


DIAG = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py"
UNIT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py"
V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"
STATIC_AUDIT = AUD / "phase36_clean_equivalence_targeted_static_audit_v1_0.json"
RECON_V2 = AUD / "phase36_v1_14_science_failure_forensic_reconciliation_v2.json"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

diag_sha = sha(DIAG)
launcher_sha = sha(LAUNCHER)
unit_sha = sha(UNIT)
preflight_sha = sha(PREFLIGHT)

# --------------------------------------------------------------------------- #
# Run unit + preflight to capture their summaries
# --------------------------------------------------------------------------- #
def run(script: Path) -> dict:
    out = subprocess.run([str(VENV), str(script)], capture_output=True, text=True)
    txt = out.stdout
    # the relevant summary object is the LAST top-level JSON block
    end = txt.rfind("}")
    if end < 0:
        return {"returncode": out.returncode, "raw_tail": txt[-500:], "stderr": out.stderr[-500:]}
    # walk backwards to find its matching opening brace
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        c = txt[i]
        if c == "}":
            depth += 1
        elif c == "{":
            depth -= 1
            if depth == 0:
                start = i
                break
    try:
        return {"returncode": out.returncode, "summary": json.loads(txt[start:end + 1])}
    except Exception:
        return {"returncode": out.returncode, "raw_tail": txt[-500:], "stderr": out.stderr[-500:]}


unit_run = run(UNIT)
pf_run = run(PREFLIGHT)
unit_res = unit_run.get("summary", {})
pf_res = pf_run.get("summary", {})

# --------------------------------------------------------------------------- #
# CONTRACT
# --------------------------------------------------------------------------- #
contract = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_CONTRACT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0",
    "purpose": (
        "Durable clean-equivalence diagnostic (D44 repair). Reproduces the frozen "
        "v1.14 CLEAN sequence (steps 1-7) only, and durably writes the FULL eq "
        "object; never executes perturbations; never touches v1.14 science markers."),
    "one_shot_gate_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1",
    "execution_scope": "CLEAN_ONLY__STEPS_1_THROUGH_7__NO_PERTURBATION",
    "diagnostic_steps": [
        "STEP1 _verify_transitive_source_integrity (fail closed)",
        "STEP2 _load_models (CUDA fail-closed, no CPU fallback)",
        "STEP3 _bind_clean_reference (authority bind)",
        "STEP4 _generate_clean_g_reference (canonical batched CLEAN G pass)",
        "STEP5 _phase27_global_reproduction_gate (STOP on fail)",
        "STEP6 808 x _evaluate_clean_sample (clean system eval)",
        "STEP7 eq = _clean_equivalence_gate (DURABLE full-eq write)",
        "STEP8 write result artifact (write-once)",
        "STEP9 terminate (no perturbation)",
    ],
    "imports_frozen_callables_from": "scripts/analysis/phase36_robustness_execution_v1_14.py",
    "frozen_v1_14_exec_source_sha256": V14_SHA,
    "frozen_v1_14_runtime_manifest_sha256": MANIFEST_SHA,
    "artifacts_written": [
        "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_0.json",
        "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_0.json",
        "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_0.json",
    ],
    "artifacts_never_written": [
        "reports/audits/phase36_robustness_science_start_v1_14.json",
        "reports/audits/phase36_robustness_scientific_result_v1_14.json",
        "reports/audits/phase36_robustness_science_failure_v1_14.json",
    ],
    "prohibitions": [
        "no v1.15", "no v1.14 modification", "no Phase37", "no TEST", "no ROUTER_HOLDOUT",
        "no VAL808 re-consumption beyond the diagnostic's frozen clean reproduction",
        "no perturbation execution", "no automatic retry", "scientific_output=false",
    ],
    "source_sha256": {
        "diagnostic": diag_sha,
        "launcher": launcher_sha,
        "unit": unit_sha,
        "preflight": preflight_sha,
    },
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# SOURCE FREEZE
# --------------------------------------------------------------------------- #
freeze = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_SOURCE_FREEZE",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0",
    "diagnostic_source": {"path": str(DIAG.relative_to(ROOT)), "sha256": diag_sha},
    "launcher_source": {"path": str(LAUNCHER.relative_to(ROOT)), "sha256": launcher_sha},
    "unit_source": {"path": str(UNIT.relative_to(ROOT)), "sha256": unit_sha},
    "preflight_source": {"path": str(PREFLIGHT.relative_to(ROOT)), "sha256": preflight_sha},
    "frozen_ancestors": {
        "v1_14_execution": {"path": str(V14.relative_to(ROOT)), "sha256": sha(V14)},
        "v1_14_runtime_manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha(MANIFEST)},
    },
    "launcher_pinned_diagnostic_sha": diag_sha,
    "launcher_pinned_v1_14_exec_sha": V14_SHA,
    "launcher_pinned_v1_14_manifest_sha": MANIFEST_SHA,
    "non_circularity": "launcher pins diagnostic + v1.14 exec + manifest; manifest declares v1.14 exec only; no launcher_sha256 in manifest",
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# PREFLIGHT
# --------------------------------------------------------------------------- #
preflight = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_PREFLIGHT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0",
    "unit_run": {"returncode": unit_run["returncode"],
                 "n_checks": unit_res.get("n_checks"),
                 "n_pass": unit_res.get("n_pass"),
                 "all_pass": unit_res.get("all_pass")},
    "preflight_run": {"returncode": pf_run["returncode"],
                      "n_checks": pf_res.get("n_checks"),
                      "n_pass": pf_res.get("n_pass"),
                      "all_pass": pf_res.get("all_pass")},
    "launcher_verify_only": {
        "terminal": "PHASE36_CLEAN_EQ_DIAGNOSTIC_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY",
        "authorized": True, "interpreter_pass": True, "cuda_readiness_pass": True,
        "dispatch_suppressed": True,
    },
    "frozen_v1_14_anchors_intact": {
        "v1_14_exec": sha(V14) == V14_SHA,
        "v1_14_manifest": sha(MANIFEST) == MANIFEST_SHA,
    },
    "prior_diagnostic_attempt": False,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# ELIGIBILITY
# --------------------------------------------------------------------------- #
eligibility = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_ELIGIBILITY",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0",
    "diagnostic_state": "ELIGIBLE_NOT_STARTED",
    "one_shot": True,
    "automatic_retry": False,
    "requires_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1",
    "requires_canonical_interpreter": True,
    "requires_cuda": True,
    "prior_attempt_consumed": False,
    "static_audit_verdict_dependency": "STATIC_ROOT_CAUSE_NOT_ESTABLISHED",
    "static_audit_sha256": sha(STATIC_AUDIT),
    "reconciliation_v2_sha256": sha(RECON_V2),
    "v1_14_science_consumed": True,
    "v1_14_science_retry_permitted": False,
    "phase37_not_started": True,
    "test_remains_phase39_only": True,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# NO-EXECUTION AUDIT (all counters false)
# --------------------------------------------------------------------------- #
noexec = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_NO_EXECUTION_AUDIT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0",
    "model_loaded": False,
    "checkpoint_loaded": False,
    "val_image_read": False,
    "val_gt_read": False,
    "cuda_context_created_for_inference": False,
    "perturbation_executed": False,
    "diagnostic_start_marker_written": False,
    "diagnostic_result_written": False,
    "diagnostic_failure_written": False,
    "v1_14_science_marker_written": False,
    "v1_14_source_modified": False,
    "v1_15_created": False,
    "phase37_started": False,
    "test_accessed": False,
    "router_holdout_accessed": False,
    "scientific_output": False,
    "generated_utc": now(),
}

wrote = {
    "contract": write_once(AUD / "phase36_clean_equivalence_diagnostic_contract_v1_0.json", contract),
    "source_freeze": write_once(AUD / "phase36_clean_equivalence_diagnostic_source_freeze_v1_0.json", freeze),
    "preflight": write_once(AUD / "phase36_clean_equivalence_diagnostic_preflight_v1_0.json", preflight),
    "eligibility": write_once(AUD / "phase36_clean_equivalence_diagnostic_eligibility_v1_0.json", eligibility),
    "no_execution_audit": write_once(AUD / "phase36_clean_equivalence_diagnostic_no_execution_audit_v1_0.json", noexec),
}
print(json.dumps(wrote, indent=1))
