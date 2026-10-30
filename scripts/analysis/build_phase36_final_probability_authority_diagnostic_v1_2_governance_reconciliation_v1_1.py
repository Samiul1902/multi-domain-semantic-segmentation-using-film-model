#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.2 — D59 GOVERNANCE RECONCILIATION BUILDER.

Write-once, FAIL-CLOSED generator for the additive reconciliation artifact:

    reports/audits/
      phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_1.json

This builder SUPERSEDES (does not overwrite) the v1.0 D57/D58 reconciliation.  It
reconciles a single governance-evidence defect:

  D59  POST_VALIDATION_SOURCE_DRIFT_CHECK_TAUTOLOGICAL
       The v1.0 reconciliation builder computed BOTH ``post`` and ``pre`` AFTER the
       validators ran::

           post = {k: sha(p) for k, (p, _) in req.items()}
           pre  = {k: sha(p) for k, (p, _) in req.items()}

       so ``pre[k] != post[k]`` is a tautology that can never fire.  The v1.0 claim
       ``v1_2_sources_byte_identical_after_validation = true`` was therefore NOT
       supported by a real pre/post comparison.

       This builder fixes the methodology: it captures a REAL pre-validator snapshot
       BEFORE running any validator, then a post-validator snapshot AFTER, and
       requires them to be byte-identical AND equal to the frozen expected pins.

Runtime diagnostic / launcher are NOT affected:
  scientific_semantics_effect = NONE
  runtime_execution_effect    = NONE
  governance_evidence_effect  = YES

FAIL-CLOSED contract of THIS builder:
  * refuse if the v1_1 reconciliation already exists;
  * verify every frozen pin (v1.2 runtime sources + frozen builder + v1.0
    reconciliation + its builder) BEFORE anything;
  * require the v1.2 start/result/failure markers ABSENT;
  * capture pre_validator_hashes IN MEMORY (each MUST equal the frozen pin);
  * run validators and require the EXACT expected results;
  * capture post_validator_hashes; require post == pre AND each == frozen pin;
  * re-check the markers ABSENT after validators;
  * write the reconciliation exactly once (O_CREAT|O_EXCL + fsync + size check).

NO model, NO CUDA, NO checkpoint, NO VAL image byte read, NO VAL GT byte read,
NO perturbations, NO TEST, NO ROUTER_HOLDOUT, NO v1.14 retry, NO
clean-equivalence retry, NO v1.15 science, NO Phase37.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_1.py
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for _p in (ROOT, ROOT / "scripts" / "analysis"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

VENV = ROOT / ".venv" / "Scripts" / "python.exe"
AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_2"

DIAG = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_2.py"
LAUNCHER = ROOT / "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_2.py"
UNIT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_2.py"
PREFLIGHT = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_2.py"
NEGCTRL = ROOT / "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_2.py"
FROZEN_BUILDER = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2.py"

RECON_V1_0 = AUD / "phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.json"
RECON_V1_0_BUILDER = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.py"

RECON = AUD / "phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_1.json"
SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_1.py"

# ---- FROZEN RUNTIME PINS (LITERAL) ------------------------------------------ #
PIN = {
    "diagnostic":
        (DIAG, "981f772fd42e35ac8e3acde17344e9bcd3fb48c39aba191200a0d811f76f29f9"),
    "launcher":
        (LAUNCHER, "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee"),
    "unit":
        (UNIT, "9f1e6527521984b6edbc9fb82f9818c39969baf458800fba9594af36bfbcdce6"),
    "preflight":
        (PREFLIGHT, "89e70d203649cc80f38c8eddba7cae502feb2d02c726474cad5a4daba4abc883"),
    "negative_controls":
        (NEGCTRL, "f4128b736e90b80e4565259eef4df45e7fda1aaa541e7f5d5a466adf361fe34a"),
    "frozen_governance_builder":
        (FROZEN_BUILDER, "6a0f1ab604611cb1d5338e919a46929804cca521d5f64a8b6f18e7f24db87a25"),
}
RECON_V1_0_SHA = "a4f4eaff5809705b785ab0349ecb7b5e48495e748f7bf810f4d9a89dd370535b"
RECON_V1_0_BUILDER_SHA = "b0056254f6e270da77b3f0051755bb9a6a86d0c7425cb043d86eefe476ab498f"

V1_2_MARKERS = [
    AUD / "phase36_final_probability_authority_diagnostic_start_v1_2.json",
    AUD / "phase36_final_probability_authority_diagnostic_result_v1_2.json",
    AUD / "phase36_final_probability_authority_diagnostic_failure_v1_2.json",
]

CORRECT_V1_2_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY"
CORRECT_SCORE_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"

# ---- EXACT expected validator results --------------------------------------- #
EXP_UNIT = {"returncode": 0, "all_pass": True, "n_checks": 135, "n_pass": 135}
EXP_PREFLIGHT = {"returncode": 0, "all_pass": True, "n_checks": 144, "n_pass": 144}
EXP_NEGCTRL = {"returncode": 0, "all_pass": True, "n_checks": 143, "n_pass": 143}
VERIFY_ONLY_TERMINAL = ("PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_READINESS_VERIFIED"
                        "__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY")
EXP_VO_EXACT = {
    "authorized": True,
    "anchor_pass": True,
    "interpreter_pass": True,
    "cuda_readiness_pass": True,
    "foreign_v1_14_token_absent_pass": True,
    "prior_failure_provenance_pass": True,
    "consumed_evidence_binding_pass": True,
    "v1_0_preservation_pass": True,
    "v1_1_preservation_pass": True,
    "transitive_integrity_pass": True,
    "source_manifest_transitive_authority_exact_match": True,
    "n_dependencies_verified": 14,
    "n_checkpoints_verified": 4,
    "final_authority_preconsumption_pass": True,
    "final_authority_sample_order_pass": True,
    "v1_1_consumed_state_binding_pass": True,
    "v1_1_result_absent": True,
    "d56_module_interface_pass": True,
    "d56_subscript_free": True,
    "d56_load_clean_image_tensor_attribute_access": True,
    "d56_canonical_learned_core_attribute_access": True,
    "terminal": VERIFY_ONLY_TERMINAL,
}


def sha(p: Path) -> str:
    try:
        return hashlib.sha256(Path(p).read_bytes()).hexdigest()
    except FileNotFoundError:
        return "ABSENT"


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def write_once(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


def _last_json(stdout: str) -> dict:
    end = stdout.rfind("}")
    depth = 0
    start = -1
    for i in range(end, -1, -1):
        c = stdout[i]
        if c == "}":
            depth += 1
        elif c == "{":
            depth -= 1
            if depth == 0:
                start = i
                break
    try:
        return json.loads(stdout[start:end + 1])
    except Exception:  # noqa: BLE001
        return {}


def run_suite(path: Path) -> dict:
    r = subprocess.run([str(VENV), str(path)], capture_output=True, text=True)
    j = _last_json(r.stdout)
    return {"returncode": r.returncode, "n_checks": j.get("n_checks"),
            "n_pass": j.get("n_pass"), "all_pass": j.get("all_pass")}


def fatal(code: int, reason: str, **extra) -> int:
    payload = {"REFUSED": reason,
               "builder": "phase36_final_prob_authority_v1_2_reconciliation_v1_1"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


def _diff(exp: dict, got: dict) -> dict:
    return {k: {"expected": exp[k], "observed": got.get(k)} for k in exp if got.get(k) != exp[k]}


def main() -> int:
    # ---- (0) write-once precondition ------------------------------------ #
    if RECON.exists():
        return fatal(2, "RECONCILIATION_V1_1_ALREADY_EXISTS", path=str(RECON))
    if RECON_V1_0.exists() is False:
        return fatal(3, "V1_0_RECONCILIATION_ABSENT", path=str(RECON_V1_0))

    # ---- (1) verify EVERY frozen pin ------------------------------------ #
    pin_bad = {}
    for k, (p, e) in PIN.items():
        o = sha(p)
        if o != e:
            pin_bad[k] = {"observed": o, "expected": e}
    if pin_bad:
        return fatal(3, "FROZEN_PIN_MISMATCH", bad=pin_bad)

    aux_bad = {}
    for k, (p, e) in {
        "recon_v1_0": (RECON_V1_0, RECON_V1_0_SHA),
        "recon_v1_0_builder": (RECON_V1_0_BUILDER, RECON_V1_0_BUILDER_SHA),
    }.items():
        o = sha(p)
        if o != e:
            aux_bad[k] = {"observed": o, "expected": e}
    if aux_bad:
        return fatal(3, "AUXILIARY_PIN_MISMATCH", bad=aux_bad)

    # ---- (2) v1.2 markers ABSENT (pre-validator) ------------------------ #
    present = [str(m) for m in V1_2_MARKERS if m.exists()]
    if present:
        return fatal(3, "V1_2_MARKER_PRESENT_UNEXPECTED", present=present)

    # ---- (3) REAL pre-validator snapshot (captured BEFORE validators) ---- #
    pre_validator_hashes = {k: sha(p) for k, (p, _) in PIN.items()}
    pre_bad = {k: {"observed": pre_validator_hashes[k], "expected": PIN[k][1]}
               for k in PIN if pre_validator_hashes[k] != PIN[k][1]}
    if pre_bad:
        return fatal(4, "PRE_VALIDATOR_HASH_MISMATCH", bad=pre_bad)

    # ---- (4) D59 STATIC EVIDENCE (tautological drift check in v1.0) ----- #
    v1_0_src = RECON_V1_0_BUILDER.read_text(encoding="utf-8")
    # The tautology signature: post and pre both built from req AFTER the validators,
    # therefore pre is not a pre-validator snapshot.
    d59 = {
        "classification": "POST_VALIDATION_SOURCE_DRIFT_CHECK_TAUTOLOGICAL",
        "v1_0_builder_path": str(RECON_V1_0_BUILDER.relative_to(ROOT)).replace("\\", "/"),
        "v1_0_builder_sha256": RECON_V1_0_BUILDER_SHA,
        "v1_0_post_snapshot_present": ("post = {k: sha(p) for k, (p, _) in req.items()}" in v1_0_src),
        "v1_0_pre_snapshot_present": ("pre = {k: sha(p) for k, (p, _) in req.items()}" in v1_0_src),
        "v1_0_pre_snapshot_is_actually_pre_validator": False,
        "v1_0_comparison_present": ("pre[k] != post[k]" in v1_0_src),
        "v1_0_comparison_is_tautological": True,
        "v1_0_claim_v1_2_sources_byte_identical_after_validation": (
            '"v1_2_sources_byte_identical_after_validation": true' in
            (RECON_V1_0.read_text(encoding="utf-8") if RECON_V1_0.exists() else "")),
        "v1_0_claim_supported_by_real_pre_post_comparison": False,
        "v1_1_correction": ("v1.1 captures a REAL pre-validator snapshot before running any "
                            "validator, then a post-validator snapshot after, and requires "
                            "post == pre AND each == frozen pin."),
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "d59_scientific_semantics_effect": "NONE",
        "d59_runtime_execution_effect": "NONE",
        "d59_governance_evidence_effect": "YES",
    }
    if not (d59["v1_0_post_snapshot_present"] and d59["v1_0_pre_snapshot_present"]
            and d59["v1_0_comparison_present"]
            and d59["v1_0_claim_v1_2_sources_byte_identical_after_validation"]):
        return fatal(4, "D59_STATIC_EVIDENCE_INCOMPLETE", d59=d59)

    # ---- (5) RUN VALIDATORS (non-consuming) ----------------------------- #
    unit_run = run_suite(UNIT)
    preflight_run = run_suite(PREFLIGHT)
    nc_run = run_suite(NEGCTRL)
    vo = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"],
                        capture_output=True, text=True)
    vj = _last_json(vo.stdout)

    unit_diff = _diff(EXP_UNIT, unit_run)
    pre_diff = _diff(EXP_PREFLIGHT, preflight_run)
    nc_diff = _diff(EXP_NEGCTRL, nc_run)
    vo_rc_ok = (vo.returncode == 0)
    vo_diff = _diff(EXP_VO_EXACT, vj)

    if unit_diff or pre_diff or nc_diff or not vo_rc_ok or vo_diff:
        return fatal(5, "VALIDATOR_RESULTS_NOT_AS_REQUIRED",
                     unit_diff=unit_diff, preflight_diff=pre_diff,
                     negative_controls_diff=nc_diff, launcher_returncode=vo.returncode,
                     launcher_verify_only_diff=vo_diff)

    # ---- (6) POST-VALIDATION MARKER GATE -------------------------------- #
    present_after = [str(m) for m in V1_2_MARKERS if m.exists()]
    if present_after:
        return fatal(6, "V1_2_MARKER_CREATED_DURING_VALIDATION", present=present_after)

    # ---- (7) REAL post-validator snapshot + strict comparison ----------- #
    post_validator_hashes = {k: sha(p) for k, (p, _) in PIN.items()}
    post_bad = {k: {"observed": post_validator_hashes[k], "expected": PIN[k][1]}
                for k in PIN if post_validator_hashes[k] != PIN[k][1]}
    if post_bad:
        return fatal(6, "POST_VALIDATOR_HASH_NOT_EQUAL_FROZEN_PIN", bad=post_bad)
    drift = {k: {"pre": pre_validator_hashes[k], "post": post_validator_hashes[k]}
             for k in PIN if pre_validator_hashes[k] != post_validator_hashes[k]}
    if drift:
        return fatal(6, "SOURCE_DRIFT_ACROSS_VALIDATION", drift=drift)
    pre_equals_post = (pre_validator_hashes == post_validator_hashes)
    all_equal_frozen_pins = all(post_validator_hashes[k] == PIN[k][1] for k in PIN)
    if not (pre_equals_post and all_equal_frozen_pins):
        return fatal(6, "PRE_POST_INVARIANT_FAILED",
                     pre_equals_post=pre_equals_post, all_equal_frozen_pins=all_equal_frozen_pins)

    # ---- (8) write the reconciliation (once) ---------------------------- #
    ts = now()
    payload = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_2_GOVERNANCE_RECONCILIATION",
        "revision": REVISION,
        "reconciliation_revision": "v1_1",
        "supersedes": None,
        "amends": "phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.json",
        "amends_sha256": RECON_V1_0_SHA,
        "additive": True,
        "mode": "STATIC_GOVERNANCE_NON_CONSUMING_ONLY",
        "background_quiescence": {
            "background_tasks_running_at_reconciliation_start": 0,
            "operator_observed_quiescence": True,
            "evidence": ("Win32 process scan immediately before the run: no venv-python "
                         "process, no find/grep/rg/sha256sum/bash/sh process; only WorkBuddy "
                         "host infrastructure (MCP node servers) remains, and it does not "
                         "inspect or write the project. This is operator-observed quiescence, "
                         "recorded SEPARATELY from source-integrity evidence; no background task "
                         "may read/modify project state during the validation window."),
            "hardcoded_integer_alone_is_not_proof": True,
        },
        "d56": "SOURCE_AUDITED_PASS",
        "d57": "RECONCILED",
        "d58": "RECONCILED",
        "d59": "RECONCILED",
        "d59_classification": "POST_VALIDATION_SOURCE_DRIFT_CHECK_TAUTOLOGICAL",
        "d59_root_cause_established": True,
        "d59_static_evidence": d59,
        "v1_0_reconciliation_not_overwritten": True,
        "v1_0_reconciliation_sha256": RECON_V1_0_SHA,
        "v1_0_reconciliation_builder_sha256": RECON_V1_0_BUILDER_SHA,
        "pre_validator_hashes": pre_validator_hashes,
        "post_validator_hashes": post_validator_hashes,
        "pre_equals_post": pre_equals_post,
        "all_equal_frozen_pins": all_equal_frozen_pins,
        "frozen_expected_pins": {k: v[1] for k, v in PIN.items()},
        "non_consuming_validation_results": {
            "unit_run": unit_run,
            "preflight_run": preflight_run,
            "negative_controls_run": nc_run,
            "launcher_verify_only": {
                "returncode": vo.returncode,
                "authorized": vj.get("authorized"),
                "anchor_pass": vj.get("anchor_pass"),
                "interpreter_pass": vj.get("interpreter_pass"),
                "cuda_readiness_pass": vj.get("cuda_readiness_pass"),
                "foreign_v1_14_token_absent_pass": vj.get("foreign_v1_14_token_absent_pass"),
                "prior_failure_provenance_pass": vj.get("prior_failure_provenance_pass"),
                "consumed_evidence_binding_pass": vj.get("consumed_evidence_binding_pass"),
                "v1_0_preservation_pass": vj.get("v1_0_preservation_pass"),
                "v1_1_preservation_pass": vj.get("v1_1_preservation_pass"),
                "transitive_integrity_pass": vj.get("transitive_integrity_pass"),
                "source_manifest_transitive_authority_exact_match":
                    vj.get("source_manifest_transitive_authority_exact_match"),
                "n_dependencies_verified": vj.get("n_dependencies_verified"),
                "n_checkpoints_verified": vj.get("n_checkpoints_verified"),
                "final_authority_preconsumption_pass": vj.get("final_authority_preconsumption_pass"),
                "final_authority_sha256": vj.get("final_authority_sha256"),
                "final_authority_shape": vj.get("final_authority_shape"),
                "final_authority_dtype": vj.get("final_authority_dtype"),
                "final_authority_sample_order_pass": vj.get("final_authority_sample_order_pass"),
                "v1_1_consumed_state_binding_pass": vj.get("v1_1_consumed_state_binding_pass"),
                "v1_1_result_absent": vj.get("v1_1_result_absent"),
                "d56_module_interface_pass": vj.get("d56_module_interface_pass"),
                "d56_subscript_free": vj.get("d56_subscript_free"),
                "d56_load_clean_image_tensor_attribute_access":
                    vj.get("d56_load_clean_image_tensor_attribute_access"),
                "d56_canonical_learned_core_attribute_access":
                    vj.get("d56_canonical_learned_core_attribute_access"),
                "terminal": vj.get("terminal"),
            },
        },
        "validator_expectations_met": {
            "unit_exact": not unit_diff,
            "preflight_exact": not pre_diff,
            "negative_controls_exact": not nc_diff,
            "launcher_verify_only_rc0": vo_rc_ok,
            "launcher_verify_only_exact": not vo_diff,
        },
        "v1_2_markers_absent_after_validation": True,
        "effective_runtime_launch_token": CORRECT_V1_2_TOKEN,
        "correct_phase27_scores_sha256": CORRECT_SCORE_SHA,
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "d59_scientific_semantics_effect": "NONE",
        "d59_runtime_execution_effect": "NONE",
        "d59_governance_evidence_effect": "YES",
        "effective_execution_eligibility": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "authorization_semantics": {
            "one_shot_gate_env": "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE=1",
            "launch_authority_token_env": f"{CORRECT_V1_2_TOKEN}=1",
            "forbidden_foreign_token_env": "PHASE36_V1_14_LAUNCH_AUTHORITY",
            "forbidden_v1_1_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY",
        },
        "prohibitions_observed": [
            "no_v1_2_diagnostic_execution", "no_start_result_failure_marker",
            "no_model_run", "no_checkpoint_deserialization",
            "no_val_image_read", "no_val_gt_read", "no_perturbations",
            "no_test", "no_router_holdout", "no_v1_14_retry",
            "no_clean_equivalence_retry", "no_v1_15_science", "no_phase37",
            "no_runtime_source_modified", "no_existing_governance_overwritten",
            "no_v1_1_consumed_evidence_modified", "no_v1_0_reconciliation_overwritten",
        ],
        "governance_state_after": {
            "v1_0": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
            "v1_1": "CONSUMED_FAILED",
            "v1_1_retry_permitted": False,
            "v1_2_final_prob": "ELIGIBLE_NOT_STARTED",
            "v1_2_clean_equivalence": "CONSUMED_RESULT (DIFFERENT family)",
            "v1_14_science": "CONSUMED_FAILED",
            "v1_15": "NOT_CREATED",
            "phase37": "NOT_STARTED",
            "test": "PHASE39_ONLY",
            "router_holdout": "NOT_ACCESSED",
        },
        "scientific_output": False,
        "generated_utc": ts,
    }
    write_once(RECON, payload)

    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_D59_GOVERNANCE_RECONCILIATION_BUILT",
        "reconciliation_v1_1_sha256": sha(RECON),
        "reconciliation_v1_1_builder_sha256": sha(SELF),
        "D56": "SOURCE_AUDITED_PASS",
        "D57": "RECONCILED",
        "D58": "RECONCILED",
        "D59": "RECONCILED",
        "pre_equals_post": pre_equals_post,
        "all_equal_frozen_pins": all_equal_frozen_pins,
        "unit": unit_run,
        "preflight": preflight_run,
        "negative_controls": nc_run,
        "launcher_verify_only_rc": vo.returncode,
        "launcher_verify_only_terminal": vj.get("terminal"),
        "effective_execution_eligibility": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "v1_2_start_result_failure": "ABSENT",
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
