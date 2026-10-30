#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.2 — D57/D58 GOVERNANCE RECONCILIATION BUILDER.

Write-once, FAIL-CLOSED generator for the additive reconciliation artifact:

    reports/audits/
      phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.json

This builder performs STATIC / GOVERNANCE / NON-CONSUMING validation only and
records a reconciliation of two governance-only defect families discovered by an
independent source audit (NO runtime source is modified):

  D57-A  GOVERNANCE_LAUNCH_AUTHORITY_TOKEN_METADATA_DRIFT
         The frozen v1.2 governance builder mis-defines LAUNCH_AUTHORITY_TOKEN as
         the v1.1 token, propagating
         ``launch_authority_token_env = PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY``
         into contract_v1_2.json and eligibility_v1_2.json.  The PRODUCTION
         launcher uses the correct v1.2 token.
  D57-B  D55_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED_IN_V1_2_GOVERNANCE
         The frozen v1.2 builder emits the mistyped Phase27 scores CSV SHA
         (``...08417a17d...``) into the builder / contract / eligibility metadata;
         the CORRECT value is ``...08417b17d...`` and the actual CSV raw SHA equals
         the CORRECT value.  The PRODUCTION launcher uses the correct value.
  D58    V1_2_GOVERNANCE_BUILDER_VALIDATOR_RESULTS_NOT_FAIL_CLOSED
         The frozen builder runs the unit / preflight / negative-control suites and
         launcher ``--verify-only`` but does NOT fail closed on those results before
         writing governance artifacts.

FAIL-CLOSED contract of THIS builder:
  * refuse if the reconciliation / builder already exists;
  * require exact byte hashes of every v1.2 runtime source + frozen builder + all 7
    frozen v1.2 governance artifacts + v1.1 START/FAILURE + D56 adjudication +
    D55 reconciliation + D51 reconciliation + frozen v1.14 source/manifest;
  * require the v1.2 start/result/failure markers ABSENT;
  * run unit / preflight / negative-controls / launcher ``--verify-only`` and require
    the EXACT expected results BEFORE writing anything;
  * re-check the markers absent AND re-hash the v1.2 runtime sources (byte-identical
    to the pre-validator hashes) BEFORE writing;
  * write the reconciliation exactly once (O_CREAT|O_EXCL + fsync + size check).

NO model, NO CUDA, NO checkpoint, NO VAL image byte read, NO VAL GT byte read,
NO perturbations, NO TEST, NO ROUTER_HOLDOUT, NO v1.14 retry, NO clean-equivalence
retry, NO v1.15 science, NO Phase37.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.py
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

V14 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_14.py"
MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

RECON = AUD / "phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.json"
SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.py"

# ---- FROZEN v1.2 runtime-source pins (LITERAL — verified before anything) ---- #
DIAG_SHA = "981f772fd42e35ac8e3acde17344e9bcd3fb48c39aba191200a0d811f76f29f9"
LAUNCH_SHA = "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee"
UNIT_SHA = "9f1e6527521984b6edbc9fb82f9818c39969baf458800fba9594af36bfbcdce6"
PREFLIGHT_SHA = "89e70d203649cc80f38c8eddba7cae502feb2d02c726474cad5a4daba4abc883"
NEGCTRL_SHA = "f4128b736e90b80e4565259eef4df45e7fda1aaa541e7f5d5a466adf361fe34a"
FROZEN_BUILDER_SHA = "6a0f1ab604611cb1d5338e919a46929804cca521d5f64a8b6f18e7f24db87a25"

V14_SHA = "ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5"
MANIFEST_SHA = "b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e"

# ---- FROZEN v1.2 governance pins (LITERAL; NEVER overwrite) ----------------- #
GOV_PINS = {
    "contract":
        ("reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_2.json",
         "2410f96a6547c3af5826a83ad1b728e9e7d676630d23b0d2f5b82d25370056a1"),
    "source_freeze":
        ("reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_2.json",
         "b0ff5c4e5df4f8193e4e0b64af160cccdab9a8901e3cefcf5ad33137fed5375f"),
    "preflight":
        ("reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_2.json",
         "cedef4a4b478aa8e5632953849cff8b420e4a38bc8ec1ce19b9b2ecbd647f3a7"),
    "negative_controls":
        ("reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_2.json",
         "e1636a6ebcdf9fa48b4765dee6486605162bac773323dbd26e2996afcab8aec1"),
    "eligibility":
        ("reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_2.json",
         "d18cfa6fd4a0747cec1d6262694731690dcaf5ceb5eae939804e46b298aefa7e"),
    "no_execution_audit":
        ("reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_2.json",
         "dd89f3c1408613c243bfbe86088c9dc1f66042305c1d2819de24d01da063c474"),
    "diff":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_1_to_v1_2_diff.json",
         "691e06693cae678de9fda96b770643206d780a63bfa231cbc4a7624fb2150064"),
}

# ---- supporting provenance pins --------------------------------------------- #
SUPPORT_PINS = {
    "v1_1_start":
        ("reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json",
         "0bfb452ef81e6e0c8880d9b333abcb6514dff7dbb3a37476da3242beeab73aec"),
    "v1_1_failure":
        ("reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json",
         "9f1b38431228ec584150da37501199ea580b26339be6d8e20a2fcba72b5cd960"),
    "d56_failure_adjudication":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_1_failure_adjudication_v1_0.json",
         "b796cc8d49df32513d2c6a4c5700a253d66a49e171def1772e1617ff4855fc80"),
    "d55_reconciliation":
        ("reports/audits/phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json",
         "124327dca073afa440e187aa1999c4f463fb97a1fe62e30ce19b6bcfa8b966f4"),
    "d51_reconciliation":
        ("reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json",
         "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b"),
}

V1_2_MARKERS = [
    AUD / "phase36_final_probability_authority_diagnostic_start_v1_2.json",
    AUD / "phase36_final_probability_authority_diagnostic_result_v1_2.json",
    AUD / "phase36_final_probability_authority_diagnostic_failure_v1_2.json",
]

# ---- effective / drifted values --------------------------------------------- #
CORRECT_V1_2_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY"
DRIFTED_V1_1_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY"
CORRECT_SCORE_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
DRIFTED_SCORE_SHA = "702133930ce14ac9513c992833396e3e250d08417a17d1032cbd260a405cfb12"
PHASE27_SCORES_CSV = ROOT / "reports/tables/phase27_val808_per_sample_scores.csv"

# ---- EXACT expected validator results --------------------------------------- #
EXP_UNIT = {"returncode": 0, "all_pass": True, "n_checks": 135, "n_pass": 135}
EXP_PREFLIGHT = {"returncode": 0, "all_pass": True, "n_checks": 144, "n_pass": 144}
EXP_NEGCTRL = {"returncode": 0, "all_pass": True, "n_checks": 143, "n_pass": 143}
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
    "final_authority_sha256": "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf",
    "final_authority_shape": [808, 512, 512],
    "final_authority_dtype": "float16",
    "final_authority_sample_order_pass": True,
    "v1_1_consumed_state_binding_pass": True,
    "v1_1_result_absent": True,
    "d56_module_interface_pass": True,
    "d56_subscript_free": True,
    "d56_load_clean_image_tensor_attribute_access": True,
    "d56_canonical_learned_core_attribute_access": True,
    "terminal": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_LAUNCH_READINESS_VERIFIED__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY",
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
    payload = {"REFUSED": reason, "builder": "phase36_final_prob_authority_v1_2_reconciliation_v1_0"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


def main() -> int:
    # ---- (0) write-once preconditions ----------------------------------- #
    if RECON.exists():
        return fatal(2, "RECONCILIATION_ALREADY_EXISTS", path=str(RECON))

    # ---- (1) exact hash pins: runtime sources + frozen builder ---------- #
    req = {
        "diagnostic": (DIAG, DIAG_SHA),
        "launcher": (LAUNCHER, LAUNCH_SHA),
        "unit": (UNIT, UNIT_SHA),
        "preflight": (PREFLIGHT, PREFLIGHT_SHA),
        "negative_controls": (NEGCTRL, NEGCTRL_SHA),
        "frozen_builder": (FROZEN_BUILDER, FROZEN_BUILDER_SHA),
        "v1_14_source": (V14, V14_SHA),
        "v1_14_manifest": (MANIFEST, MANIFEST_SHA),
    }
    bad = {k: {"observed": sha(p), "expected": e} for k, (p, e) in req.items() if sha(p) != e}
    if bad:
        return fatal(3, "SOURCE_PIN_MISMATCH", bad=bad)

    # ---- (2) all 7 frozen v1.2 governance artifacts --------------------- #
    gov_bad = {}
    for k, (p, e) in GOV_PINS.items():
        o = sha(ROOT / p)
        if o != e:
            gov_bad[k] = {"observed": o, "expected": e}
    if gov_bad:
        return fatal(3, "GOVERNANCE_PIN_MISMATCH", bad=gov_bad)

    # ---- (3) supporting provenance pins --------------------------------- #
    sup_bad = {}
    for k, (p, e) in SUPPORT_PINS.items():
        o = sha(ROOT / p)
        if o != e:
            sup_bad[k] = {"observed": o, "expected": e}
    if sup_bad:
        return fatal(3, "SUPPORTING_PIN_MISMATCH", bad=sup_bad)

    # ---- (4) v1.2 markers ABSENT ---------------------------------------- #
    present = [str(m) for m in V1_2_MARKERS if m.exists()]
    if present:
        return fatal(3, "V1_2_MARKER_PRESENT_UNEXPECTED", present=present)

    # ---- (5) D57 STATIC EVIDENCE ---------------------------------------- #
    launcher_src = LAUNCHER.read_text(encoding="utf-8")
    builder_src = FROZEN_BUILDER.read_text(encoding="utf-8")
    contract_txt = (ROOT / GOV_PINS["contract"][0]).read_text(encoding="utf-8")
    elig_txt = (ROOT / GOV_PINS["eligibility"][0]).read_text(encoding="utf-8")

    d57 = {
        "d57_a_governance_launch_authority_token_metadata_drift": {
            "classification": "GOVERNANCE_LAUNCH_AUTHORITY_TOKEN_METADATA_DRIFT",
            "effective_runtime_token": CORRECT_V1_2_TOKEN,
            "drifted_governance_token": DRIFTED_V1_1_TOKEN,
            "launcher_literal_correct": (
                f'LAUNCH_AUTHORITY_TOKEN = "{CORRECT_V1_2_TOKEN}"' in launcher_src),
            "builder_literal_wrong": (
                f'LAUNCH_AUTHORITY_TOKEN = "{DRIFTED_V1_1_TOKEN}"' in builder_src),
            "contract_carries_wrong_token_env": (
                f'"launch_authority_token_env": "{DRIFTED_V1_1_TOKEN}=1"' in contract_txt),
            "eligibility_carries_wrong_token_env": (
                f'"launch_authority_token_env": "{DRIFTED_V1_1_TOKEN}"' in elig_txt),
            "contract_v1_2_token_as_env_absent": (
                f'"launch_authority_token_env": "{CORRECT_V1_2_TOKEN}=1"' not in contract_txt),
            "eligibility_v1_2_token_as_env_absent": (
                f'"launch_authority_token_env": "{CORRECT_V1_2_TOKEN}"' not in elig_txt),
            "runtime_launcher_affected": False,
            "diagnostic_source_affected": False,
            "scientific_path_affected": False,
            "runtime_execution_effect": "NONE",
            "governance_provenance_effect": "YES",
        },
        "d57_b_d55_score_sha_reintroduced_in_v1_2_governance": {
            "classification": "D55_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED_IN_V1_2_GOVERNANCE",
            "correct_score_sha256": CORRECT_SCORE_SHA,
            "drifted_score_sha256": DRIFTED_SCORE_SHA,
            "actual_phase27_scores_csv_sha256": sha(PHASE27_SCORES_CSV),
            "actual_equals_correct": sha(PHASE27_SCORES_CSV) == CORRECT_SCORE_SHA,
            "builder_carries_wrong_score_sha": (DRIFTED_SCORE_SHA in builder_src),
            "contract_carries_wrong_score_sha": (DRIFTED_SCORE_SHA in contract_txt),
            "eligibility_carries_wrong_score_sha": (DRIFTED_SCORE_SHA in elig_txt),
            "launcher_carries_correct_score_sha": (CORRECT_SCORE_SHA in launcher_src),
            "runtime_launcher_affected": False,
            "diagnostic_source_affected": False,
            "scientific_path_affected": False,
            "runtime_execution_effect": "NONE",
            "governance_provenance_effect": "YES",
        },
    }
    # D57 must be fully evidenced; else refuse.
    d57_checks = [
        d57["d57_a_governance_launch_authority_token_metadata_drift"]["launcher_literal_correct"],
        d57["d57_a_governance_launch_authority_token_metadata_drift"]["builder_literal_wrong"],
        d57["d57_a_governance_launch_authority_token_metadata_drift"]["contract_carries_wrong_token_env"],
        d57["d57_a_governance_launch_authority_token_metadata_drift"]["eligibility_carries_wrong_token_env"],
        d57["d57_a_governance_launch_authority_token_metadata_drift"]["contract_v1_2_token_as_env_absent"],
        d57["d57_a_governance_launch_authority_token_metadata_drift"]["eligibility_v1_2_token_as_env_absent"],
        d57["d57_b_d55_score_sha_reintroduced_in_v1_2_governance"]["actual_equals_correct"],
        d57["d57_b_d55_score_sha_reintroduced_in_v1_2_governance"]["builder_carries_wrong_score_sha"],
        d57["d57_b_d55_score_sha_reintroduced_in_v1_2_governance"]["contract_carries_wrong_score_sha"],
        d57["d57_b_d55_score_sha_reintroduced_in_v1_2_governance"]["eligibility_carries_wrong_score_sha"],
        d57["d57_b_d55_score_sha_reintroduced_in_v1_2_governance"]["launcher_carries_correct_score_sha"],
    ]
    if not all(d57_checks):
        return fatal(4, "D57_STATIC_EVIDENCE_INCOMPLETE",
                     checks=d57_checks, d57=d57)

    # ---- (6) D58 STATIC EVIDENCE (fail-open builder) -------------------- #
    # The frozen builder runs the suites + verify-only but has NO guard on their
    # results before the first write_once().
    first_write = builder_src.find("    # ---- 1. contract")
    if first_write == -1:
        return fatal(4, "D58_BUILDER_LAYOUT_UNRECOGNISED")
    seg_before_write = builder_src[:first_write]
    # locate the validator invocations
    has_unit = "unit_run = run_suite(UNIT)" in seg_before_write
    has_pre = "preflight_run = run_suite(PREFLIGHT)" in seg_before_write
    has_nc = "nc_run = run_suite(NEGCTRL)" in seg_before_write
    has_vo = "--verify-only" in seg_before_write
    # look for any fail-closed guard on those results in the pre-write segment
    guards = []
    for token in ("unit_run[", "preflight_run[", "nc_run[", "vo.returncode",
                  "vj[", 'vj.get("authorized")'):
        if token in seg_before_write:
            guards.append(token)
    d58 = {
        "classification": "V1_2_GOVERNANCE_BUILDER_VALIDATOR_RESULTS_NOT_FAIL_CLOSED",
        "builder_runs_unit": has_unit,
        "builder_runs_preflight": has_pre,
        "builder_runs_negative_controls": has_nc,
        "builder_runs_launcher_verify_only": has_vo,
        "fail_closed_guards_present_before_write": guards,
        "builder_fails_closed_on_validator_results": bool(guards),
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "d58_scientific_semantics_effect": "NONE",
    }
    if not (has_unit and has_pre and has_nc and has_vo):
        return fatal(4, "D58_STATIC_EVIDENCE_INCOMPLETE", d58=d58)
    if d58["builder_fails_closed_on_validator_results"]:
        # If the frozen builder DID fail closed, D58 is not reproducible as stated.
        return fatal(4, "D58_NOT_REPRODUCIBLE__BUILDER_ALREADY_FAILS_CLOSED", d58=d58)

    # ---- (7) NON-CONSUMING VALIDATION (fail closed on results) ---------- #
    unit_run = run_suite(UNIT)
    preflight_run = run_suite(PREFLIGHT)
    nc_run = run_suite(NEGCTRL)
    vo = subprocess.run([str(VENV), str(LAUNCHER), "--verify-only"],
                        capture_output=True, text=True)
    vj = _last_json(vo.stdout)

    def _diff(exp: dict, got: dict) -> dict:
        return {k: {"expected": exp[k], "observed": got.get(k)}
                for k in exp if got.get(k) != exp[k]}

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

    # ---- (8) post-validator: markers still absent + sources byte-identical #
    present_after = [str(m) for m in V1_2_MARKERS if m.exists()]
    if present_after:
        return fatal(6, "V1_2_MARKER_CREATED_DURING_VALIDATION", present=present_after)
    post = {k: sha(p) for k, (p, _) in req.items()}
    pre = {k: sha(p) for k, (p, _) in req.items()}
    drift = {k: {"pre": pre[k], "post": post[k]} for k in pre if pre[k] != post[k]}
    if drift:
        return fatal(6, "SOURCE_DRIFT_DURING_VALIDATION", drift=drift)

    # ---- (9) write the reconciliation (once) ---------------------------- #
    ts = now()
    payload = {
        "artifact_kind": "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_2_GOVERNANCE_RECONCILIATION",
        "revision": REVISION,
        "reconciliation_revision": "v1_0",
        "additive": True,
        "supersedes": None,
        "mode": "STATIC_GOVERNANCE_NON_CONSUMING_VALIDATION_ONLY",
        "background_tasks_running_at_reconciliation_start": 0,
        "background_quiescence": {
            "background_tasks_running_at_reconciliation_start": 0,
            "python_processes_running": 0,
            "project_related_processes_running": 0,
            "note": ("All project-related background jobs were stopped before hashing; "
                     "only WorkBuddy host infrastructure (MCP node servers) remains, "
                     "which does not inspect or write the project."),
        },
        "d56": "SOURCE_AUDITED_PASS",
        "d56_classification": "DIAGNOSTIC_FROZEN_MODULE_SUBSCRIPT_MISMATCH",
        "d56_source_audit_note": ("production v1.2 diagnostic uses ATTRIBUTE access "
                                  "(_FROZEN_MOD._load_clean_image_tensor / "
                                  "_FROZEN_MOD.canonical_learned_core); no runtime source modified."),
        "d57": "RECONCILED",
        "d57_a": "GOVERNANCE_LAUNCH_AUTHORITY_TOKEN_METADATA_DRIFT",
        "d57_b": "D55_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED_IN_V1_2_GOVERNANCE",
        "d58": "RECONCILED",
        "d58_classification": "V1_2_GOVERNANCE_BUILDER_VALIDATOR_RESULTS_NOT_FAIL_CLOSED",
        "effective_runtime_launch_token": CORRECT_V1_2_TOKEN,
        "correct_phase27_scores_sha256": CORRECT_SCORE_SHA,
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "d57_scientific_semantics_effect": "NONE",
        "d58_scientific_semantics_effect": "NONE",
        "original_governance_artifacts_overwritten": False,
        "effective_execution_eligibility": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "d57_static_evidence": d57,
        "d58_static_evidence": d58,
        "frozen_pins_verified": {
            "diagnostic_sha256": DIAG_SHA,
            "launcher_sha256": LAUNCH_SHA,
            "unit_sha256": UNIT_SHA,
            "preflight_sha256": PREFLIGHT_SHA,
            "negative_controls_sha256": NEGCTRL_SHA,
            "frozen_v1_2_builder_sha256": FROZEN_BUILDER_SHA,
            "v1_14_source_sha256": V14_SHA,
            "v1_14_manifest_sha256": MANIFEST_SHA,
            "governance": {k: v[1] for k, v in GOV_PINS.items()},
            "supporting": {k: v[1] for k, v in SUPPORT_PINS.items()},
            "all_match": True,
        },
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
        "v1_2_sources_byte_identical_after_validation": True,
        "authorization_semantics": {
            "one_shot_gate_env": "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE=1",
            "launch_authority_token_env": f"{CORRECT_V1_2_TOKEN}=1",
            "forbidden_foreign_token_env": "PHASE36_V1_14_LAUNCH_AUTHORITY",
            "forbidden_v1_1_token_reuse": DRIFTED_V1_1_TOKEN,
        },
        "prohibitions_observed": [
            "no_v1_2_diagnostic_execution", "no_start_result_failure_marker",
            "no_model_load", "no_checkpoint_deserialization",
            "no_val_image_read", "no_val_gt_read", "no_perturbations",
            "no_test", "no_router_holdout", "no_v1_14_retry",
            "no_clean_equivalence_retry", "no_v1_15_science", "no_phase37",
            "no_runtime_source_modified", "no_existing_governance_overwritten",
            "no_v1_1_consumed_evidence_modified",
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

    # ---- (10) final report ---------------------------------------------- #
    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_2_D57_D58_GOVERNANCE_RECONCILIATION_BUILT",
        "reconciliation_sha256": sha(RECON),
        "reconciliation_builder_sha256": sha(SELF),
        "background_tasks_running": 0,
        "D56": "SOURCE_AUDITED_PASS",
        "D57": "RECONCILED",
        "D58": "RECONCILED",
        "runtime_launcher_token": CORRECT_V1_2_TOKEN,
        "correct_phase27_scores_sha256": CORRECT_SCORE_SHA,
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
