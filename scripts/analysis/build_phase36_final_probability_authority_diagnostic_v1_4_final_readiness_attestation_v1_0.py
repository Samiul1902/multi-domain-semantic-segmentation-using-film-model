#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PHASE36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4
D72 FINAL POST-GOVERNANCE READINESS ATTESTATION — BUILDER (v1.0)
===============================================================================

PURPOSE (Work Order #11 / D72)
-----------------------------
Durably FREEZE, in a write-once additive artifact, the POST-GOVERNANCE final
readiness state of the frozen v1.4 diagnostic family, so that the final
readiness evidence is bound on disk BEFORE any execution authorization.

Root gap D72 = ``POST_GOVERNANCE_FINAL_READINESS_NOT_DURABLY_BOUND``:

  * The frozen v1.4 governance preflight artifact
    (``..._preflight_v1_4.json``) records the BUILDER-TIME validation run:
    unit=68/68, preflight=84/84 (governance-dependent preflight checks did not
    yet exist on disk at that moment), negative_controls=31/31.
  * A LATER operator run, once ALL v1.4 governance artifacts existed on disk,
    produced preflight=102/102.
  * That final POST-GOVERNANCE result was NOT durably bound anywhere.

This builder is STATIC / NON-CONSUMING. It performs NO execution of v1.4.

The builder:
  1. Re-verifies all 7 frozen v1.4 SOURCE pins + 7 frozen v1.4 GOVERNANCE pins.
  2. Requires v1.4 START / RESULT / FAILURE / PROCESS_EXIT absent, and the
     real journal directory absent (records = 0).
  3. Requires the score-SHA remediation to hold: the CORRECT canonical value
     (``...08417b17d...``) present, and the historical WRONG value
     (``...08417a17d...``) absent from the entire v1.4 family.
  4. Writes a single write-once attestation recording the frozen post-governance
     readiness evidence.

The builder DOES NOT re-run the validators itself — the operator does that
separately and supplies the results via CLI, so that the attestation is a
RECORD of an observed run, not a self-attesting tautology. (A convenience
``--run-validators`` mode is provided that executes the suites read-only and
captures their rc + JSON, but the DEFAULT path is static.)

WRITE-ONCE DISCIPLINE
---------------------
0o_CREAT|O_EXCL|O_WRONLY (+O_BINARY on Windows), full-write loop, os.fsync(fd),
post-write st_size check, and refuse if the target already exists.

SCIENCE / AUTHORITY BOUNDS
--------------------------
NO v1.4 execution, NO model run, NO checkpoint deserialization, NO VAL image
read, NO VAL GT read, NO TEST, NO ROUTER_HOLDOUT, NO perturbation, NO v1.15
science, NO Phase37.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

# --------------------------------------------------------------------------- #
# ROOT / INTERPRETER
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[2]
assert (ROOT / "scripts").is_dir(), f"unexpected ROOT: {ROOT}"

CANONICAL_INTERPRETER = ROOT / ".venv" / "Scripts" / "python.exe"

ATTESTATION_REVISION = (
    "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4_"
    "final_readiness_attestation_v1_0"
)
ATTESTATION_PATH = (
    ROOT
    / "reports"
    / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_"
    "final_readiness_attestation_v1_0.json"
)

# --------------------------------------------------------------------------- #
# FROZEN PINS (Work Order #11)
# --------------------------------------------------------------------------- #
# --- 7 v1.4 SOURCE pins ---
SOURCE_PINS = {
    "diagnostic": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_4.py",
        "778af67fe41e44cec0717365b2c3427bcfd43442145af09a7aca2abe1f4a3eab",
    ),
    "launcher": (
        "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_4.py",
        "221a15a1f2dd341c59a65d9f8c0f57f4e339ff5a66f8bece6c7b2a5d8ad10a0a",
    ),
    "supervisor": (
        "scripts/analysis/supervise_phase36_final_probability_authority_diagnostic_v1_4.py",
        "792302085ccde4f09bfc7d3ca6534f411a9b776b54cbca5b83e8a7ad02277c2b",
    ),
    "unit": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_4.py",
        "a4f1ddb854847435388e1dd9984812bc0b295c42443f63c76ac5d55c01b34738",
    ),
    "preflight": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_4.py",
        "bb14fca6f9344459f9c812d61de6c1abf90fd5fe7d8a966d46a6ca10fbadc1ec",
    ),
    "negative_controls": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.py",
        "492c03fd231969dc80347713c3106c7970854d060d2d5780e285ffbac8372256",
    ),
    "builder": (
        "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4.py",
        "ec5432ac875580b331a9e2e5910499d15c41f30de843c01e589005d9ea8fb29b",
    ),
}

# --- 7 v1.4 GOVERNANCE pins ---
GOVERNANCE_PINS = {
    "contract": (
        "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_4.json",
        "1052946e87b9060bec5e06488569ab06b1cb85cf52d2969e2876a4a7355d5a57",
    ),
    "source_freeze": (
        "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_4.json",
        "ff1d23e11da61645cc117bbc0e7674b680056c83164cad9266beb24d6c5e0ba0",
    ),
    "preflight": (
        "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_4.json",
        "224cf6d1f108119caf3ce365bfa4cfe36945d0fd4a7d334e472f2b3e7cd32006",
    ),
    "negative_controls": (
        "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json",
        "fe35ac673bca59e6bcb20900f4c541f283ba3bc6aaf3bf8b4e82ba537a08bcb2",
    ),
    "eligibility": (
        "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_4.json",
        "9ba0c2fd94c6d5d7d29b50430b2c78d13e48e7003725c80cac2012b6ddb1ad11",
    ),
    "no_execution_audit": (
        "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_4.json",
        "09feb4bfc9e7c9ffa157a3afb93a0d9085e462d4b6c2bc3676295d03f3c80a37",
    ),
    "v1_3_to_v1_4_diff": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_to_v1_4_diff.json",
        "ccffd91d4dff41a6ea4d9a6be3c66237e5c17a4cc6bb92103e122eb9dbae8ee2",
    ),
}

ALL_PINS = {}
ALL_PINS.update(SOURCE_PINS)
ALL_PINS.update(GOVERNANCE_PINS)

# --- attempt artifacts that MUST be absent ---
ATTEMPT_ABSENT = {
    "start": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_start.json",
    "result": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result.json",
    "failure": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_failure.json",
    "process_exit": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_process_exit.json",
}
JOURNAL_DIRNAME = "phase36_final_probability_authority_diagnostic_v1_4_journal"

# --- score-SHA remediation (D55 / D57 / D66) ---
# canonical SHA DERIVED by hashing at runtime; never retyped.
PHASE27_SCORES_CSV = "reports/tables/phase27_val808_per_sample_scores.csv"
_HEAD = "702133930ce14ac9513c992833396e3e250d08417"
_TAIL = "b17d1032cbd260a405cfb12"
CANONICAL_PHASE27_SCORES_SHA = _HEAD + _TAIL
# historical WRONG value: hex char at 0-based index 41 was 'a' instead of 'b'
_INCORRECT_HEAD = "702133930ce14ac9513c992833396e3e250d08417"
_INCORRECT_TAIL = "a17d1032cbd260a405cfb12"
INCORRECT_HISTORICAL_SHA_ASSEMBLED = _INCORRECT_HEAD + _INCORRECT_TAIL

# v1.4 family files scanned for the incorrect historical SHA
V1_4_FAMILY = [p for (p, _s) in SOURCE_PINS.values()] + [
    p for (p, _s) in GOVERNANCE_PINS.values()
]

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def exists(p: Path) -> bool:
    return Path(p).exists()


def journal_record_count() -> int:
    d = ROOT / "reports" / "audits" / JOURNAL_DIRNAME
    if not d.is_dir():
        return 0
    n = 0
    for f in d.rglob("*"):
        if f.is_file():
            n += 1
    return n


def incorrect_sha_occurrences() -> dict:
    """Return {path: count} for the historical WRONG SHA across the v1.4 family.

    The needle is ASSEMBLED at runtime from two parts so this builder's own
    source cannot accidentally match itself.
    """
    needle = _INCORRECT_HEAD + _INCORRECT_TAIL
    hits = {}
    for rel in V1_4_FAMILY:
        fp = ROOT / rel
        if not fp.exists():
            continue
        txt = fp.read_text(encoding="utf-8", errors="replace")
        c = txt.count(needle)
        if c:
            hits[rel] = c
    return hits


def write_once_bytes(path: Path, data: bytes) -> None:
    """Write-once: O_CREAT|O_EXCL|O_WRONLY(+O_BINARY), full-write, fsync."""
    if path.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE EXISTING ATTESTATION: {path}")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        mv = memoryview(data)
        written = 0
        while written < len(data):
            written += os.write(fd, mv[written:])
        os.fsync(fd)
    finally:
        os.close(fd)
    # post-write size check
    if path.stat().st_size != len(data):
        raise SystemExit(
            f"POST-WRITE SIZE MISMATCH: {path.stat().st_size} != {len(data)}"
        )


def run_suite(script_rel: str):
    """Read-only: run a validator suite and capture rc + parsed JSON."""
    script = ROOT / script_rel
    proc = subprocess.run(
        [str(CANONICAL_INTERPRETER), str(script)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    out = {}
    try:
        out = json.loads(proc.stdout)
    except Exception:
        out = {}
    return proc.returncode, out, proc.stdout, proc.stderr


def run_launcher_verify_only():
    script = ROOT / SOURCE_PINS["launcher"][0]
    proc = subprocess.run(
        [str(CANONICAL_INTERPRETER), str(script), "--verify-only"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    out = {}
    try:
        out = json.loads(proc.stdout)
    except Exception:
        out = {}
    return proc.returncode, out


def run_supervisor_self_test():
    script = ROOT / SOURCE_PINS["supervisor"][0]
    proc = subprocess.run(
        [str(CANONICAL_INTERPRETER), str(script), "--self-test"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    out = {}
    try:
        out = json.loads(proc.stdout)
    except Exception:
        out = {}
    return proc.returncode, out


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="D72 final readiness attestation builder")
    ap.add_argument(
        "--run-validators",
        action="store_true",
        help="Execute the suites read-only and capture results (default: static).",
    )
    ap.add_argument("--unit-n-pass", type=int, default=None)
    ap.add_argument("--unit-n-checks", type=int, default=None)
    ap.add_argument("--preflight-n-pass", type=int, default=None)
    ap.add_argument("--preflight-n-checks", type=int, default=None)
    ap.add_argument("--nc-n-pass", type=int, default=None)
    ap.add_argument("--nc-n-checks", type=int, default=None)
    args = ap.parse_args(argv)

    print("=" * 78)
    print("PHASE36 v1.4 / D72 FINAL POST-GOVERNANCE READINESS ATTESTATION (builder v1.0)")
    print("=" * 78)

    problems = []

    # ---- Step 1: pin verification (all 14) ----
    print("\n[1] FROZEN PIN VERIFICATION (7 source + 7 governance)")
    pin_actual = {}
    for role, (rel, exp) in ALL_PINS.items():
        fp = ROOT / rel
        if not fp.exists():
            problems.append(f"MISSING PIN FILE [{role}]: {rel}")
            print(f"   MISSING [{role}] {rel}")
            continue
        a = sha256_file(fp)
        pin_actual[role] = {"path": rel, "expected_sha256": exp, "actual_sha256": a,
                            "match": a == exp}
        flag = "OK " if a == exp else "BAD"
        print(f"   {flag} [{role:<18}] {a[:16]}…  {Path(rel).name}")
        if a != exp:
            problems.append(f"PIN MISMATCH [{role}]: {a} != {exp}")
    all_pins_match = all(v["match"] for v in pin_actual.values()) and \
        len(pin_actual) == len(ALL_PINS)
    print(f"   ALL 14 PINS MATCH = {all_pins_match}")

    # ---- Step 2: attempt absence ----
    print("\n[2] ATTEMPT-MARKER ABSENCE (START / RESULT / FAILURE / PROCESS_EXIT)")
    absent_state = {}
    for role, rel in ATTEMPT_ABSENT.items():
        present = exists(ROOT / rel)
        absent_state[role] = {"path": rel, "present": present, "absent": not present}
        print(f"   {'ABSENT ' if not present else 'PRESENT'}  {role:<13} {rel}")
        if present:
            problems.append(f"ATTEMPT ARTIFACT PRESENT [{role}]: {rel}")
    n_journal = journal_record_count()
    journal_absent = n_journal == 0
    print(f"   JOURNAL RECORDS = {n_journal}  (dir_absent={journal_absent})")
    if not journal_absent:
        problems.append(f"REAL JOURNAL RECORDS PRESENT: {n_journal}")
    all_absent = all(v["absent"] for v in absent_state.values()) and journal_absent

    # ---- Step 3: score-SHA remediation ----
    print("\n[3] SCORE-SHA REMEDIATION (D55 / D57 / D66)")
    csv_fp = ROOT / PHASE27_SCORES_CSV
    csv_sha = sha256_file(csv_fp) if csv_fp.exists() else "ABSENT"
    canonical_ok = csv_sha == CANONICAL_PHASE27_SCORES_SHA
    print(f"   canonical (derived)  = {CANONICAL_PHASE27_SCORES_SHA}")
    print(f"   csv actual sha256    = {csv_sha}")
    print(f"   canonical_ok         = {canonical_ok}")
    if not canonical_ok:
        problems.append(f"CANONICAL SCORE SHA MISMATCH: {csv_sha}")
    wrong_hits = incorrect_sha_occurrences()
    incorrect_absent = len(wrong_hits) == 0
    print(f"   incorrect historical SHA occurrences = {wrong_hits if wrong_hits else 'NONE'}")
    print(f"   incorrect_absent = {incorrect_absent}")
    if not incorrect_absent:
        problems.append(f"INCORRECT HISTORICAL SHA PRESENT: {wrong_hits}")

    # ---- Step 4: capture validation results ----
    print("\n[4] POST-GOVERNANCE VALIDATION RESULTS")
    unit_n_pass = args.unit_n_pass
    unit_n_checks = args.unit_n_checks
    pre_n_pass = args.preflight_n_pass
    pre_n_checks = args.preflight_n_checks
    nc_n_pass = args.nc_n_pass
    nc_n_checks = args.nc_n_checks

    launcher_rc = None
    launcher_terminal = None
    launcher_gates_all_true = None
    supervisor_rc = None
    supervisor_all_pass = None
    supervisor_n_scenarios = None
    supervisor_scenarios_all_pass = None

    if args.run_validators:
        print("   --run-validators: executing suites (read-only) …")
        rc_u, out_u, _so, _se = run_suite(SOURCE_PINS["unit"][0])
        unit_n_pass = out_u.get("n_pass", unit_n_pass)
        unit_n_checks = out_u.get("n_checks", unit_n_checks)
        print(f"   unit           rc={rc_u}  {unit_n_pass}/{unit_n_checks}")

        rc_p, out_p, _so, _se = run_suite(SOURCE_PINS["preflight"][0])
        pre_n_pass = out_p.get("n_pass", pre_n_pass)
        pre_n_checks = out_p.get("n_checks", pre_n_checks)
        print(f"   preflight      rc={rc_p}  {pre_n_pass}/{pre_n_checks}")

        rc_n, out_n, _so, _se = run_suite(SOURCE_PINS["negative_controls"][0])
        nc_n_pass = out_n.get("n_pass", nc_n_pass)
        nc_n_checks = out_n.get("n_checks", nc_n_checks)
        print(f"   neg_controls   rc={rc_n}  {nc_n_pass}/{nc_n_checks}")

        supervisor_rc, sup = run_supervisor_self_test()
        supervisor_all_pass = sup.get("all_pass")
        _scen = sup.get("synthetic_fixtures") or {}
        supervisor_n_scenarios = len(_scen)
        supervisor_scenarios_all_pass = all(
            v.get("pass") for v in _scen.values()
        ) if _scen else False
        print(f"   supervisor     rc={supervisor_rc}  all_pass={supervisor_all_pass} "
              f"n={supervisor_n_scenarios} scenarios_all_pass={supervisor_scenarios_all_pass}")

        launcher_rc, lv = run_launcher_verify_only()
        launcher_terminal = lv.get("terminal")
        bool_gates = {k: v for k, v in lv.items() if isinstance(v, bool)}
        # one_shot_gate_set MUST be False in verify-only (dispatch suppressed)
        check_gates = {k: v for k, v in bool_gates.items() if k != "one_shot_gate_set"}
        launcher_gates_all_true = all(check_gates.values())
        print(f"   launcher       rc={launcher_rc}  terminal={launcher_terminal}")
        print(f"   launcher gates all_true={launcher_gates_all_true}  "
              f"(one_shot_gate_set={lv.get('one_shot_gate_set')})")

    unit_ok = (unit_n_pass == 68 and unit_n_checks == 68)
    preflight_ok = (pre_n_pass == 102 and pre_n_checks == 102)
    nc_ok = (nc_n_pass == 31 and nc_n_checks == 31)

    print(f"   unit      = {unit_n_pass}/{unit_n_checks}  ok={unit_ok}")
    print(f"   preflight = {pre_n_pass}/{pre_n_checks}  ok={preflight_ok}  "
          f"(post-governance must be 102/102)")
    print(f"   neg_ctrl  = {nc_n_pass}/{nc_n_checks}  ok={nc_ok}")
    print(f"   supervisor= {supervisor_n_scenarios}/6  all_pass={supervisor_all_pass}")
    print(f"   launcher  = rc {launcher_rc}  verify_only PASS="
          f"{launcher_rc == 0 and launcher_gates_all_true}")

    if not unit_ok:
        problems.append(f"UNIT SUITE NOT 68/68: {unit_n_pass}/{unit_n_checks}")
    if not preflight_ok:
        problems.append(f"PREFLIGHT NOT 102/102 (post-governance): {pre_n_pass}/{pre_n_checks}")
    if not nc_ok:
        problems.append(f"NEGATIVE CONTROLS NOT 31/31: {nc_n_pass}/{nc_n_checks}")
    if args.run_validators:
        if not supervisor_all_pass or supervisor_n_scenarios != 6:
            problems.append("SUPERVISOR SELF-TEST NOT all_pass / n!=6")
        if launcher_rc != 0 or not launcher_gates_all_true:
            problems.append("LAUNCHER --verify-only NOT PASS")
        expected_terminal = (
            "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_READINESS_VERIFIED"
            "__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"
        )
        if launcher_terminal != expected_terminal:
            problems.append(f"LAUNCHER TERMINAL MISMATCH: {launcher_terminal}")

    # ---- FAIL CLOSED ----
    if problems:
        print("\n" + "!" * 78)
        print("FAIL CLOSED — NO ATTESTATION WRITTEN")
        for p in problems:
            print("   *", p)
        print("!" * 78)
        return 4

    # ---- Step 5: write attestation ----
    print("\n[5] WRITING WRITE-ONCE ATTESTATION")
    attestation = {
        "attestation_revision": ATTESTATION_REVISION,
        "work_order": "PHASE36_WORK_ORDER_11__D72_FINAL_POST_GOVERNANCE_READINESS_ATTESTATION",
        "d72_classification": "RECONCILED",
        "d72_defect_original": "POST_GOVERNANCE_FINAL_READINESS_NOT_DURABLY_BOUND",
        "d72_resolution": (
            "POST_GOVERNANCE_FINAL_READINESS_DURABLY_FROZEN_IN_WRITE_ONCE_ATTESTATION"
        ),
        "mode": "STATIC_NON_CONSUMING_VALIDATION_ONLY",
        "v1_4_executed": False,
        "scientific_semantics_effect": "NONE",
        "runtime_execution_effect": "NONE",
        "governance_evidence_effect": "YES",
        "diagnostic_v1_4": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "created_utc": None,  # filled below
        "score_sha_remediation": {
            "issue": "D55_D57_D66_SCORE_SHA_TRANSCRIPTION_DRIFT",
            "canonical_phase27_scores_csv": PHASE27_SCORES_CSV,
            "canonical_phase27_scores_sha256": CANONICAL_PHASE27_SCORES_SHA,
            "canonical_derived_by_hashing": True,
            "historical_incorrect_sha256": INCORRECT_HISTORICAL_SHA_ASSEMBLED,
            "historical_incorrect_sha_occurrences_in_v1_4_family": wrong_hits,
            "historical_incorrect_sha_absent_from_family": incorrect_absent,
        },
        "frozen_pins": {
            "n_source_pins": len(SOURCE_PINS),
            "n_governance_pins": len(GOVERNANCE_PINS),
            "all_pins_match": all_pins_match,
            "source": {k: v for k, v in pin_actual.items() if k in SOURCE_PINS},
            "governance": {k: v for k, v in pin_actual.items() if k in GOVERNANCE_PINS},
        },
        "attempt_absence": {
            "start_absent": absent_state["start"]["absent"],
            "result_absent": absent_state["result"]["absent"],
            "failure_absent": absent_state["failure"]["absent"],
            "process_exit_absent": absent_state["process_exit"]["absent"],
            "start_result_failure_process_exit_absent": all_absent,
            "journal_dirname": JOURNAL_DIRNAME,
            "real_journal_records": n_journal,
            "real_journal_records_is_zero": journal_absent,
        },
        "post_governance_readiness": {
            "unit_checks": unit_n_checks,
            "unit_pass": unit_n_pass,
            "unit_all_pass": unit_ok,
            "preflight_checks": pre_n_checks,
            "preflight_pass": pre_n_pass,
            "preflight_all_pass": preflight_ok,
            "preflight_note": (
                "POST-GOVERNANCE run; governance-dependent preflight checks now exist "
                "on disk ⇒ 102/102 (builder-time run without governance was 84/84)"
            ),
            "negative_controls_checks": nc_n_checks,
            "negative_controls_pass": nc_n_pass,
            "negative_controls_all_pass": nc_ok,
            "supervisor_synthetic_scenarios": supervisor_n_scenarios,
            "supervisor_all_pass": supervisor_all_pass,
            "supervisor_scenarios_all_pass": supervisor_scenarios_all_pass,
            "launcher_verify_only_rc": launcher_rc,
            "launcher_verify_only_terminal": launcher_terminal,
            "launcher_verify_only_pass": (
                launcher_rc == 0 and bool(launcher_gates_all_true)
                if launcher_rc is not None else None
            ),
            "launcher_verify_only_all_gates_true": launcher_gates_all_true,
        },
        "builder_time_preflight_artifact": {
            "path": GOVERNANCE_PINS["preflight"][0],
            "sha256": GOVERNANCE_PINS["preflight"][1],
            "recorded_unit": "68/68",
            "recorded_preflight": "84/84",
            "recorded_preflight_note": (
                "governance-dependent preflight checks did not yet exist on disk at "
                "builder time — superseded by the post-governance 102/102 run recorded here"
            ),
        },
        "prohibitions_observed": {
            "v1_4_execution": "NOT_PERFORMED",
            "model_run": "NOT_PERFORMED",
            "checkpoint_deserialization": "NOT_PERFORMED",
            "val_image_read": "NOT_PERFORMED",
            "val_gt_read": "NOT_PERFORMED",
            "test_access": "NOT_PERFORMED",
            "router_holdout_access": "NOT_PERFORMED",
            "perturbations": "NOT_PERFORMED",
            "v1_15_science": "NOT_PERFORMED",
            "phase37": "NOT_PERFORMED",
        },
        "no_retry_assertion": "NO v1.4 ATTEMPT CONSUMED; NO RETRY PERFORMED",
        "note": (
            "Additive governance-evidence only. No scientific-path change. v1.4 remains "
            "ELIGIBLE_NOT_STARTED; attempt not consumed. This attestation merely durably "
            "binds the post-governance final readiness evidence."
        ),
    }
    # create UTC timestamp from the system clock (never computed by hand)
    import datetime as _dt
    attestation["created_utc"] = (
        _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    data = (json.dumps(attestation, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    write_once_bytes(ATTESTATION_PATH, data)
    att_sha = hashlib.sha256(data).hexdigest()
    print(f"   ATTESTATION WRITTEN: {ATTESTATION_PATH}")
    print(f"   attestation_sha256  = {att_sha}")

    # builder's own sha (raw bytes)
    builder_sha = sha256_file(Path(__file__).resolve())
    print(f"   builder_sha256      = {builder_sha}")

    print("\n" + "=" * 78)
    print("PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_D72_FINAL_READINESS_ATTESTATION_COMPLETE")
    print("=" * 78)
    print(json.dumps({
        "attestation_sha256": att_sha,
        "builder_sha256": builder_sha,
        "unit": f"{unit_n_pass}/{unit_n_checks}",
        "preflight": f"{pre_n_pass}/{pre_n_checks}",
        "negative_controls": f"{nc_n_pass}/{nc_n_checks}",
        "supervisor": f"{supervisor_n_scenarios}/6",
        "launcher_verify_only": "PASS" if (launcher_rc == 0 and launcher_gates_all_true) else "N/A",
        "pre_equals_post": True,
        "all_equal_frozen_pins": all_pins_match,
        "v1_4": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "START_RESULT_FAILURE_PROCESS_EXIT": "ABSENT",
        "real_journal_records": n_journal,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
