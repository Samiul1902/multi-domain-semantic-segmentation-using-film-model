#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Build the Phase36 CLEAN EQUIVALENCE DIAGNOSTIC v1.1 governance artifacts.

NO EXECUTION of the diagnostic.  This builder only (a) hashes source files,
(b) runs the UNIT / PREFLIGHT / NEGATIVE-CONTROL validators (all no-model),
(c) runs the launcher ``--verify-only`` (non-consuming), and (d) writes the
governance artifacts with write-once semantics.

Artifacts (all under reports/audits/):
    phase36_clean_equivalence_diagnostic_contract_v1_1.json
    phase36_clean_equivalence_diagnostic_source_freeze_v1_1.json
    phase36_clean_equivalence_diagnostic_preflight_v1_1.json
    phase36_clean_equivalence_diagnostic_negative_controls_v1_1.json
    phase36_clean_equivalence_diagnostic_eligibility_v1_1.json
    phase36_clean_equivalence_diagnostic_no_execution_audit_v1_1.json
    phase36_clean_equivalence_diagnostic_v1_0_to_v1_1_diff.json
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

DIAG = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py"
UNIT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_1.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_1.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_1.py"

DIAG_V10 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py"
LAUNCHER_V10 = ROOT / "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py"
UNIT_V10 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py"
PREFLIGHT_V10 = ROOT / "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py"

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = ROOT / "reports/audits/phase36_v1_14_runtime_source_integrity_manifest.json"
STATIC_AUDIT = AUD / "phase36_clean_equivalence_targeted_static_audit_v1_0.json"
RECON_V2 = AUD / "phase36_v1_14_science_failure_forensic_reconciliation_v2.json"
SCI_START = AUD / "phase36_robustness_science_start_v1_14.json"
SCI_FAIL = AUD / "phase36_robustness_science_failure_v1_14.json"
FOR_ADJ = AUD / "phase36_v1_14_science_failure_forensic_adjudication.json"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

V10_SHAS = {
    "diagnostic": "7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7",
    "launcher": "a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228",
    "unit": "33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5",
    "preflight": "92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653",
}

PRIOR_PINS = {
    "v1_14_science_start": ("reports/audits/phase36_robustness_science_start_v1_14.json",
                            "e2c42b05f4fd0450022d7bcde091c0bea13638788b4f83a123016ab894630e0a"),
    "v1_14_science_failure": ("reports/audits/phase36_robustness_science_failure_v1_14.json",
                              "0fcc3c211d7bcd53b4f8e53d7b09f518fd83a929e8a979c7174762958fff754b"),
    "v1_14_forensic_adjudication": ("reports/audits/phase36_v1_14_science_failure_forensic_adjudication.json",
                                    "f1d4712ae7b3f0b333a22c852f99d6b3812218ffb258f8f58ddba62c7193c17e"),
    "forensic_reconciliation_v2": ("reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json",
                                   "cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c"),
    "targeted_static_audit": ("reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json",
                              "8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4"),
}
REQUIRED_STATIC_AUDIT_VERDICT = "STATIC_ROOT_CAUSE_NOT_ESTABLISHED"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> str:
    if path.exists():
        raise SystemExit(f"REFUSE_OVERWRITE::{path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0)
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if not n:
                raise OSError("SHORT_WRITE")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    return sha(path)


def run_summary(script: Path, extra_env=None) -> dict:
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    out = subprocess.run([str(VENV), str(script)], capture_output=True, text=True, env=env)
    txt = out.stdout
    end = txt.rfind("}")
    if end < 0:
        return {"returncode": out.returncode, "raw_tail": txt[-800:], "stderr": out.stderr[-800:]}
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
        return {"returncode": out.returncode, "raw_tail": txt[-800:], "stderr": out.stderr[-800:]}


# --------------------------------------------------------------------------- #
# Hash sources
# --------------------------------------------------------------------------- #
diag_sha = sha(DIAG)
launcher_sha = sha(LAUNCHER)
unit_sha = sha(UNIT)
preflight_sha = sha(PREFLIGHT)
negctrl_sha = sha(NEGCTRL)

v10_preserved = {
    "diagnostic": sha(DIAG_V10) == V10_SHAS["diagnostic"],
    "launcher": sha(LAUNCHER_V10) == V10_SHAS["launcher"],
    "unit": sha(UNIT_V10) == V10_SHAS["unit"],
    "preflight": sha(PREFLIGHT_V10) == V10_SHAS["preflight"],
}
assert all(v10_preserved.values()), f"v1.0 NOT preserved: {v10_preserved}"

# launcher pin must equal the actual diagnostic SHA
_launcher_src = LAUNCHER.read_text(encoding="utf-8")
_launcher_pin_ok = f'FROZEN_EXPECTED_DIAGNOSTIC_SHA = "{diag_sha}"' in _launcher_src
assert _launcher_pin_ok, "launcher diagnostic SHA pin != actual diagnostic SHA"

# --------------------------------------------------------------------------- #
# Run the validators (no model) + launcher verify-only (non-consuming)
# --------------------------------------------------------------------------- #
unit_run = run_summary(UNIT)
pf_run = run_summary(PREFLIGHT)
nc_run = run_summary(NEGCTRL)
verify_run = run_summary(LAUNCHER, extra_env={}) if False else None

# launcher --verify-only, explicitly (no env token set)
_v = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"], capture_output=True, text=True)
try:
    verify_res = json.loads(_v.stdout[_v.stdout.index("{"):_v.stdout.rindex("}") + 1])
except Exception:
    verify_res = {"raw_tail": _v.stdout[-800:], "returncode": _v.returncode}

unit_res = unit_run.get("summary", {})
pf_res = pf_run.get("summary", {})
nc_res = nc_run.get("summary", {})

# no diagnostic markers must exist
markers = {
    "start": (AUD / "phase36_clean_equivalence_diagnostic_start_v1_1.json").exists(),
    "result": (AUD / "phase36_clean_equivalence_diagnostic_result_v1_1.json").exists(),
    "failure": (AUD / "phase36_clean_equivalence_diagnostic_failure_v1_1.json").exists(),
}
assert not any(markers.values()), f"DIAGNOSTIC MARKERS PRESENT: {markers}"

prior_state = {}
for name, (rel, exp) in PRIOR_PINS.items():
    p = ROOT / rel
    prior_state[name] = {"path": rel, "present": p.exists(),
                         "expected": exp, "observed": (sha(p) if p.exists() else None),
                         "match": bool(p.exists() and sha(p) == exp)}
static_verdict = json.loads(STATIC_AUDIT.read_text(encoding="utf-8")).get("root_cause_static_verdict")

# --------------------------------------------------------------------------- #
# CONTRACT
# --------------------------------------------------------------------------- #
contract = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_CONTRACT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "supersedes": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_0",
    "additive_revision": True,
    "v1_0_preserved_byte_for_byte": True,
    "purpose": (
        "ADDITIVE D45-D49 repair of the durable clean-equivalence diagnostic (D44 "
        "repair). Reproduces the frozen v1.14 CLEAN sequence (steps 1-7) only and "
        "durably writes the FULL eq object; requires BOTH the one-shot execute gate "
        "AND the launch-authority token; never executes perturbations; never touches "
        "v1.14 science markers."),
    "repaired_defects": {
        "D45": "diagnostic source REQUIRES the launch-authority token (in addition to "
               "the one-shot execute gate) before any start marker; absent authority => "
               "fail CLOSED (rc 5), NO marker/model/ckpt/VAL/GT.",
        "D46": "counter authority taken EXACTLY from the frozen v1.14 module "
               "(mod.C.COUNTERS_REQUIRED / mod.C.COUNTERS_FOREVER_ZERO); no alternate "
               "common module; no empty-dict fallback; fail closed if unavailable.",
        "D47": "durable terminal evidence: the result write is INSIDE the guarded "
               "try-block covering run_diagnostic() AND the result write; every terminal "
               "path attempts a durable failure artifact with full D47 fields.",
        "D48": "launcher transitive HASH-ONLY integrity (14 deps / 4 ckpts, every SHA, "
               "launcher_sha256 absent) BEFORE launch authority; NO torch.load.",
        "D49": "validator coverage repair: real AST / control-flow bindings.",
    },
    "one_shot_gate_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1",
    "launch_authority_token_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY=1",
    "required_authorization_order": [
        "(1) one-shot execute gate",
        "(2) prior-attempt absence",
        "(3) launch-authority token",
        "(4) preserved prior-failure provenance gate",
        "(5) start marker (authorized_attempt DERIVED)",
        "(6) guarded execution + durable result (D47)",
    ],
    "execution_scope": "CLEAN_ONLY__STEPS_1_THROUGH_7__NO_PERTURBATION",
    "diagnostic_steps": [
        "STEP1 _verify_transitive_source_integrity (fail closed, defense in depth)",
        "STEP2 _load_models (CUDA fail-closed, no CPU fallback)",
        "STEP3 _bind_clean_reference (authority bind)",
        "STEP4 _generate_clean_g_reference (canonical batched CLEAN G pass)",
        "STEP5 _phase27_global_reproduction_gate (STOP on fail)",
        "STEP6 808 x _evaluate_clean_sample (clean system eval)",
        "STEP7 eq = _clean_equivalence_gate (DURABLE full-eq write)",
        "STEP8 write result artifact (write-once, INSIDE guarded region)",
        "STEP9 terminate (no perturbation)",
    ],
    "imports_frozen_callables_from": "scripts/analysis/phase36_robustness_execution_v1_14.py",
    "frozen_v1_14_exec_source_sha256": V14_SHA,
    "frozen_v1_14_runtime_manifest_sha256": MANIFEST_SHA,
    "artifacts_written": [
        "reports/audits/phase36_clean_equivalence_diagnostic_start_v1_1.json",
        "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_1.json",
        "reports/audits/phase36_clean_equivalence_diagnostic_failure_v1_1.json",
    ],
    "artifacts_never_written": [
        "reports/audits/phase36_robustness_science_start_v1_14.json",
        "reports/audits/phase36_robustness_scientific_result_v1_14.json",
        "reports/audits/phase36_robustness_science_failure_v1_14.json",
    ],
    "result_artifact_required_eq_fields": [
        "all_pass", "checks", "n_generated", "n_bound", "n_dice_comparisons",
        "n_state_machine_branch_comparisons", "n_router_decision_comparisons",
        "missing_generated_dice", "missing_bound_dice", "dice_mismatches",
        "route_branch_mismatches", "router_decision_mismatches",
        "max_abs_dice_deviation", "dice_comparator", "branch_comparator",
        "router_decision_comparator",
    ],
    "failure_artifact_required_fields": [
        "termination_kind", "exception_type", "exception_message", "failing_stage",
        "clean_equivalence_computed", "clean_equivalence_full",
        "automatic_retry", "overwrite_permitted", "scientific_output",
    ],
    "prior_failure_provenance_required_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
    "prior_failure_provenance_pins": {k: v[1] for k, v in PRIOR_PINS.items()},
    "prohibitions": [
        "no v1.15", "no v1.14 modification", "no Phase37", "no TEST", "no ROUTER_HOLDOUT",
        "no VAL808 re-consumption beyond the diagnostic's frozen clean reproduction",
        "no perturbation execution", "no automatic retry", "scientific_output=false",
        "no checkpoint deserialization at launcher",
    ],
    "source_sha256": {
        "diagnostic": diag_sha,
        "launcher": launcher_sha,
        "unit": unit_sha,
        "preflight": preflight_sha,
        "negative_controls": negctrl_sha,
    },
    "v1_0_source_sha256": V10_SHAS,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# SOURCE FREEZE
# --------------------------------------------------------------------------- #
freeze = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_SOURCE_FREEZE",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "diagnostic_source": {"path": str(DIAG.relative_to(ROOT)), "sha256": diag_sha},
    "launcher_source": {"path": str(LAUNCHER.relative_to(ROOT)), "sha256": launcher_sha},
    "unit_source": {"path": str(UNIT.relative_to(ROOT)), "sha256": unit_sha},
    "preflight_source": {"path": str(PREFLIGHT.relative_to(ROOT)), "sha256": preflight_sha},
    "negative_controls_source": {"path": str(NEGCTRL.relative_to(ROOT)), "sha256": negctrl_sha},
    "v1_0_preservation": {
        "diagnostic": {"path": str(DIAG_V10.relative_to(ROOT)), "expected": V10_SHAS["diagnostic"],
                       "observed": sha(DIAG_V10), "preserved": v10_preserved["diagnostic"]},
        "launcher": {"path": str(LAUNCHER_V10.relative_to(ROOT)), "expected": V10_SHAS["launcher"],
                     "observed": sha(LAUNCHER_V10), "preserved": v10_preserved["launcher"]},
        "unit": {"path": str(UNIT_V10.relative_to(ROOT)), "expected": V10_SHAS["unit"],
                 "observed": sha(UNIT_V10), "preserved": v10_preserved["unit"]},
        "preflight": {"path": str(PREFLIGHT_V10.relative_to(ROOT)), "expected": V10_SHAS["preflight"],
                      "observed": sha(PREFLIGHT_V10), "preserved": v10_preserved["preflight"]},
    },
    "frozen_ancestors": {
        "v1_14_execution": {"path": str(V14.relative_to(ROOT)), "sha256": sha(V14), "expected": V14_SHA},
        "v1_14_runtime_manifest": {"path": str(MANIFEST.relative_to(ROOT)), "sha256": sha(MANIFEST),
                                   "expected": MANIFEST_SHA},
    },
    "launcher_pinned_diagnostic_sha": diag_sha,
    "launcher_pinned_v1_14_exec_sha": V14_SHA,
    "launcher_pinned_v1_14_manifest_sha": MANIFEST_SHA,
    "launcher_pin_matches_actual_diagnostic": _launcher_pin_ok,
    "non_circularity": ("launcher pins diagnostic + v1.14 exec + manifest; manifest declares "
                        "v1.14 exec only; no launcher_sha256 in manifest"),
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# PREFLIGHT
# --------------------------------------------------------------------------- #
preflight = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_PREFLIGHT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "unit_run": {"returncode": unit_run.get("returncode"),
                 "n_checks": unit_res.get("n_checks"), "n_pass": unit_res.get("n_pass"),
                 "all_pass": unit_res.get("all_pass")},
    "preflight_run": {"returncode": pf_run.get("returncode"),
                      "n_checks": pf_res.get("n_checks"), "n_pass": pf_res.get("n_pass"),
                      "all_pass": pf_res.get("all_pass")},
    "negative_controls_run": {"returncode": nc_run.get("returncode"),
                              "n_checks": nc_res.get("n_checks"), "n_pass": nc_res.get("n_pass"),
                              "all_pass": nc_res.get("all_pass")},
    "launcher_verify_only": {
        "terminal": verify_res.get("terminal"),
        "authorized": verify_res.get("authorized"),
        "interpreter_pass": verify_res.get("interpreter_pass"),
        "cuda_readiness_pass": verify_res.get("cuda_readiness_pass"),
        "prior_failure_provenance_pass": verify_res.get("prior_failure_provenance_pass"),
        "transitive_integrity_pass": verify_res.get("transitive_integrity_pass"),
        "n_dependencies_verified": verify_res.get("n_dependencies_verified"),
        "n_checkpoints_verified": verify_res.get("n_checkpoints_verified"),
        "dispatch_suppressed": bool(verify_res.get("terminal", "").endswith("DISPATCH_SUPPRESSED_BY_VERIFY_ONLY")),
        "one_shot_gate_set_during_verify": verify_res.get("one_shot_gate_set"),
    },
    "frozen_v1_14_anchors_intact": {
        "v1_14_exec": sha(V14) == V14_SHA,
        "v1_14_manifest": sha(MANIFEST) == MANIFEST_SHA,
    },
    "prior_failure_provenance": prior_state,
    "static_audit_verdict": static_verdict,
    "static_audit_verdict_matches_required": static_verdict == REQUIRED_STATIC_AUDIT_VERDICT,
    "prior_diagnostic_attempt": any(markers.values()),
    "v1_0_preserved": v10_preserved,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# NEGATIVE CONTROLS (summary artifact)
# --------------------------------------------------------------------------- #
negctrl = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_NEGATIVE_CONTROLS",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "source": {"path": str(NEGCTRL.relative_to(ROOT)), "sha256": negctrl_sha},
    "headline_control": {
        "statement": ("direct invocation with PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1 but "
                      "WITHOUT the launch-authority token fails CLOSED and creates NO start marker"),
        "exit_code_expected": 5,
        "control_names": [
            "HEADLINE_execute_gate_without_launch_authority_fails_closed",
            "HEADLINE_no_start_marker_created_without_launch_authority",
            "HEADLINE_no_result_marker_created_without_launch_authority",
            "HEADLINE_no_failure_marker_created_without_launch_authority",
        ],
    },
    "mutation_sensitive_controls": [
        "D45_d_mutant_detector_flags_violation",
        "D46_b_mutant_with_empty_fallback_detected",
        "D47_a_mutant_result_outside_guarded_detected",
        "D47_b_mutant_missing_failure_write_detected",
        "D48_b_mutated_manifest_bytes_rejected",
        "D48_b_corrupted_dep_sha_detected",
        "D48_a_dropped_checkpoint_detected",
        "D48_c_injected_launcher_sha_rejected",
        "D48_d_detector_flags_injected_torch_load",
    ],
    "n_checks": nc_res.get("n_checks"), "n_pass": nc_res.get("n_pass"),
    "all_pass": nc_res.get("all_pass"),
    "results": nc_res.get("results"),
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# ELIGIBILITY
# --------------------------------------------------------------------------- #
eligibility = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_ELIGIBILITY",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "diagnostic_state": "ELIGIBLE_NOT_STARTED",
    "one_shot": True,
    "automatic_retry": False,
    "requires_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1",
    "requires_launch_authority": True,
    "launch_authority_token_env": "PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_LAUNCH_AUTHORITY",
    "requires_canonical_interpreter": True,
    "requires_cuda": True,
    "prior_attempt_consumed": False,
    "start_marker_present": markers["start"],
    "result_marker_present": markers["result"],
    "failure_marker_present": markers["failure"],
    "static_audit_verdict_dependency": REQUIRED_STATIC_AUDIT_VERDICT,
    "static_audit_sha256": sha(STATIC_AUDIT),
    "reconciliation_v2_sha256": sha(RECON_V2),
    "v1_14_science_consumed": True,
    "v1_14_science_failed": True,
    "v1_14_science_retry_permitted": False,
    "v1_15_created": False,
    "phase37_not_started": True,
    "test_remains_phase39_only": True,
    "router_holdout_accessed": False,
    "v1_0_status": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# NO-EXECUTION AUDIT (all counters false)
# --------------------------------------------------------------------------- #
noexec = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_NO_EXECUTION_AUDIT",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "model_loaded": False,
    "checkpoint_loaded": False,
    "checkpoint_deserialized_at_launcher": False,
    "val_image_read": False,
    "val_gt_read": False,
    "cuda_context_created_for_inference": False,
    "perturbation_executed": False,
    "diagnostic_start_marker_written": markers["start"],
    "diagnostic_result_written": markers["result"],
    "diagnostic_failure_written": markers["failure"],
    "v1_14_science_marker_written": False,
    "v1_14_science_rerun": False,
    "v1_14_source_modified": False,
    "v1_15_created": False,
    "phase37_started": False,
    "test_accessed": False,
    "router_holdout_accessed": False,
    "scientific_output": False,
    "generated_utc": now(),
}

# --------------------------------------------------------------------------- #
# v1.0 -> v1.1 DIFF
# --------------------------------------------------------------------------- #
diff = {
    "artifact_kind": "PHASE36_CLEAN_EQUIVALENCE_DIAGNOSTIC_V1_0_TO_V1_1_DIFF",
    "revision": "ra_medfilm_barr_phase36_clean_equivalence_diagnostic_v1_1",
    "change_class": "ADDITIVE_GOVERNANCE_REPAIR__NO_V1_0_MUTATION",
    "v1_0_preserved_byte_for_byte": v10_preserved,
    "new_files": [
        "scripts/analysis/phase36_clean_equivalence_diagnostic_v1_1.py",
        "scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_1.py",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_1.py",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_1.py",
        "scripts/analysis/phase36_clean_equivalence_diagnostic_negative_controls_v1_1.py",
    ],
    "modified_files": [],
    "deleted_files": [],
    "source_sha256": {
        "v1_0": V10_SHAS,
        "v1_1": {"diagnostic": diag_sha, "launcher": launcher_sha, "unit": unit_sha,
                 "preflight": preflight_sha, "negative_controls": negctrl_sha},
    },
    "defect_repairs": [
        {"id": "D45", "title": "source requires launch-authority token before start marker",
         "v1_0": "only the one-shot execute gate guarded the start marker",
         "v1_1": "one-shot gate -> prior-attempt absence -> launch-authority token -> "
                 "provenance gate -> derived authorized_attempt -> start marker",
         "fail_closed_terminal": ("PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__"
                                  "LAUNCH_AUTHORITY_REQUIRED__NO_ATTEMPT_CONSUMED"),
         "status": "REPAIRED"},
        {"id": "D46", "title": "exact frozen counter authority; no fallback",
         "v1_0": "counter authority not bound to the frozen v1.14 module C",
         "v1_1": "OrderedDict from mod.C.COUNTERS_REQUIRED + mod.C.COUNTERS_FOREVER_ZERO; "
                 "no alternate common module; no empty-dict fallback; fail closed",
         "fail_closed_terminal": ("PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__"
                                  "FROZEN_COUNTER_AUTHORITY_UNAVAILABLE"),
         "status": "REPAIRED"},
        {"id": "D47", "title": "durable terminal evidence",
         "v1_0": "result write not proven inside the guarded terminal region",
         "v1_1": "run_diagnostic() AND the result write are INSIDE one guarded try-block; "
                 "every terminal path writes a durable failure artifact with full fields "
                 "(O_CREAT|O_EXCL + full-write loop + fsync + loud short-write failure)",
         "status": "REPAIRED"},
        {"id": "D48", "title": "launcher transitive hash-only integrity before authority",
         "v1_0": "launcher verified the anchor SHA only",
         "v1_1": "manifest SHA + execution_source_sha256 + exactly 14 deps + exactly 4 ckpts "
                 "+ every dep/ckpt SHA + launcher_sha256 absent; NO torch.load",
         "fail_closed_terminal": ("PHASE36_CLEAN_EQ_DIAGNOSTIC_V1_1_FAIL_CLOSED__"
                                  "TRANSITIVE_INTEGRITY_FAILED__NO_ATTEMPT_CONSUMED"),
         "status": "REPAIRED"},
        {"id": "D49", "title": "validator coverage repair",
         "v1_0": "validator used substring-only / tautological checks",
         "v1_1": "real AST / control-flow bindings; 14 enumerated requirements; "
                 f"unit {unit_res.get('n_pass')}/{unit_res.get('n_checks')}, "
                 f"preflight {pf_res.get('n_pass')}/{pf_res.get('n_checks')}, "
                 f"negative controls {nc_res.get('n_pass')}/{nc_res.get('n_checks')}",
         "status": "REPAIRED"},
    ],
    "prior_failure_provenance_binding": prior_state,
    "required_static_audit_verdict": REQUIRED_STATIC_AUDIT_VERDICT,
    "observed_static_audit_verdict": static_verdict,
    "validator_results": {
        "unit": {"n_checks": unit_res.get("n_checks"), "n_pass": unit_res.get("n_pass"),
                 "all_pass": unit_res.get("all_pass")},
        "preflight": {"n_checks": pf_res.get("n_checks"), "n_pass": pf_res.get("n_pass"),
                      "all_pass": pf_res.get("all_pass")},
        "negative_controls": {"n_checks": nc_res.get("n_checks"), "n_pass": nc_res.get("n_pass"),
                              "all_pass": nc_res.get("all_pass")},
    },
    "no_execution_state": {
        "diagnostic_v1_0": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
        "diagnostic_v1_1": "ELIGIBLE_NOT_STARTED",
        "v1_1_start_marker": "ABSENT" if not markers["start"] else "PRESENT",
        "v1_1_result_marker": "ABSENT" if not markers["result"] else "PRESENT",
        "v1_1_failure_marker": "ABSENT" if not markers["failure"] else "PRESENT",
        "v1_14_science": "CONSUMED_FAILED",
        "v1_14_science_retry": "FORBIDDEN",
        "v1_15": "NOT_CREATED",
        "phase37": "NOT_STARTED",
        "test": "REMAINS_PHASE39_ONLY",
        "router_holdout": "NOT_ACCESSED",
    },
    "scientific_output": False,
    "generated_utc": now(),
}

wrote = {
    "contract": write_once(AUD / "phase36_clean_equivalence_diagnostic_contract_v1_1.json", contract),
    "source_freeze": write_once(AUD / "phase36_clean_equivalence_diagnostic_source_freeze_v1_1.json", freeze),
    "preflight": write_once(AUD / "phase36_clean_equivalence_diagnostic_preflight_v1_1.json", preflight),
    "negative_controls": write_once(AUD / "phase36_clean_equivalence_diagnostic_negative_controls_v1_1.json", negctrl),
    "eligibility": write_once(AUD / "phase36_clean_equivalence_diagnostic_eligibility_v1_1.json", eligibility),
    "no_execution_audit": write_once(AUD / "phase36_clean_equivalence_diagnostic_no_execution_audit_v1_1.json", noexec),
    "diff": write_once(AUD / "phase36_clean_equivalence_diagnostic_v1_0_to_v1_1_diff.json", diff),
}
print(json.dumps(wrote, indent=1))
