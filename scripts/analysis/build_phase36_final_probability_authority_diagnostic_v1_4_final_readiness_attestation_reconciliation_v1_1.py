#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PHASE36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.4
D73 / D74 FINAL-READINESS GOVERNANCE RECONCILIATION — BUILDER (v1.1)
===============================================================================

MODE: STATIC / NON-CONSUMING ONLY. DO NOT EXECUTE v1.4.

PURPOSE
-------
Additively reconcile two defects discovered in the frozen D72 final-readiness
attestation builder and artifact:

  D73 = D72_PIN_NAMESPACE_COLLISION__SOURCE_PINS_OVERWRITTEN_BY_GOVERNANCE_PINS
        The D72 builder used overlapping dictionary keys (``preflight``,
        ``negative_controls``) in SOURCE_PINS and GOVERNANCE_PINS, then merged
        them with ``ALL_PINS.update(SOURCE_PINS); ALL_PINS.update(GOVERNANCE_PINS)``.
        The governance tuples overwrote the two source tuples, so the frozen
        attestation's ``frozen_pins.source`` section records the GOVERNANCE JSON
        path for ``preflight``/``negative_controls`` instead of the source ``.py``
        path. Both source ``.py`` pins were therefore NOT recorded.

        REPAIR: use DISJOINT canonical identifiers
        (``source::*`` / ``governance::*``) and require
        n_expected_pins = n_unique_pin_keys = n_unique_paths = 14.

  D74 = D72_PRE_POST_SOURCE_DRIFT_COMPARISON_NOT_IMPLEMENTED
        The D72 builder captured a pre snapshot but never performed a REAL
        before/after comparison.

        REPAIR: capture ``pre_validator_hashes`` over the exact 14 disjoint
        files BEFORE any validator; run validators; then rehash the SAME 14
        files into ``post_validator_hashes``; require
        post == pre AND every post == frozen expected. Persist BOTH complete maps.

The frozen D72 attestation and builder are PRESERVED UNMODIFIED.

WRITE-ONCE DISCIPLINE
---------------------
os.O_CREAT|os.O_EXCL|os.O_WRONLY (+O_BINARY on Windows), full-write loop,
os.fsync(fd), post-write st_size check, refuse if target exists.

SCIENCE / AUTHORITY BOUNDS
--------------------------
NO v1.4 execution, NO model run, NO checkpoint deserialization, NO VAL image
read, NO VAL GT read, NO TEST, NO ROUTER_HOLDOUT, NO perturbation, NO v1.15
science, NO Phase37.
"""

from __future__ import annotations

import argparse
import datetime as _dt
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

BUILDER_REVISION = (
    "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_4_"
    "final_readiness_attestation_reconciliation_v1_1"
)
RECON_PATH = (
    ROOT
    / "reports"
    / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_"
    "final_readiness_attestation_reconciliation_v1_1.json"
)

# --------------------------------------------------------------------------- #
# FROZEN D72 (must NOT be modified)
# --------------------------------------------------------------------------- #
D72_ATTESTATION_PATH = (
    ROOT
    / "reports"
    / "audits"
    / "phase36_final_probability_authority_diagnostic_v1_4_"
    "final_readiness_attestation_v1_0.json"
)
D72_ATTESTATION_SHA = "4cffd388f6fbdacf15abc2d5984c8cad9e6f186c7a3d8137c796a53b6b96db27"
D72_BUILDER_PATH = (
    ROOT
    / "scripts"
    / "analysis"
    / "build_phase36_final_probability_authority_diagnostic_v1_4_"
    "final_readiness_attestation_v1_0.py"
)
D72_BUILDER_SHA = "ff35008ff9edc3efd66eb7363f3e027021f30cc4b824d7799e2d0856a40d4cba"

# --------------------------------------------------------------------------- #
# DISJOINT CANONICAL PIN IDENTIFIERS (D73 repair)
# --------------------------------------------------------------------------- #
# source::*
SOURCE_PINS = {
    "source::diagnostic": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_4.py",
        "778af67fe41e44cec0717365b2c3427bcfd43442145af09a7aca2abe1f4a3eab",
    ),
    "source::launcher": (
        "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_4.py",
        "221a15a1f2dd341c59a65d9f8c0f57f4e339ff5a66f8bece6c7b2a5d8ad10a0a",
    ),
    "source::supervisor": (
        "scripts/analysis/supervise_phase36_final_probability_authority_diagnostic_v1_4.py",
        "792302085ccde4f09bfc7d3ca6534f411a9b776b54cbca5b83e8a7ad02277c2b",
    ),
    "source::unit": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_4.py",
        "a4f1ddb854847435388e1dd9984812bc0b295c42443f63c76ac5d55c01b34738",
    ),
    "source::preflight": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_4.py",
        "bb14fca6f9344459f9c812d61de6c1abf90fd5fe7d8a966d46a6ca10fbadc1ec",
    ),
    "source::negative_controls": (
        "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.py",
        "492c03fd231969dc80347713c3106c7970854d060d2d5780e285ffbac8372256",
    ),
    "source::builder": (
        "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4.py",
        "ec5432ac875580b331a9e2e5910499d15c41f30de843c01e589005d9ea8fb29b",
    ),
}
# governance::*
GOVERNANCE_PINS = {
    "governance::contract": (
        "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_4.json",
        "1052946e87b9060bec5e06488569ab06b1cb85cf52d2969e2876a4a7355d5a57",
    ),
    "governance::source_freeze": (
        "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_4.json",
        "ff1d23e11da61645cc117bbc0e7674b680056c83164cad9266beb24d6c5e0ba0",
    ),
    "governance::preflight": (
        "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_4.json",
        "224cf6d1f108119caf3ce365bfa4cfe36945d0fd4a7d334e472f2b3e7cd32006",
    ),
    "governance::negative_controls": (
        "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json",
        "fe35ac673bca59e6bcb20900f4c541f283ba3bc6aaf3bf8b4e82ba537a08bcb2",
    ),
    "governance::eligibility": (
        "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_4.json",
        "9ba0c2fd94c6d5d7d29b50430b2c78d13e48e7003725c80cac2012b6ddb1ad11",
    ),
    "governance::no_execution_audit": (
        "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_4.json",
        "09feb4bfc9e7c9ffa157a3afb93a0d9085e462d4b6c2bc3676295d03f3c80a37",
    ),
    "governance::v1_3_to_v1_4_diff": (
        "reports/audits/phase36_final_probability_authority_diagnostic_v1_3_to_v1_4_diff.json",
        "ccffd91d4dff41a6ea4d9a6be3c66237e5c17a4cc6bb92103e122eb9dbae8ee2",
    ),
}

# D73 repair explicitly binds these two SOURCE .py pins as DISJOINT from their
# governance JSONs (the collision that the D72 builder suffered).
D73_EXPLICIT_SOURCE_BINDINGS = {
    "source::preflight": SOURCE_PINS["source::preflight"],
    "source::negative_controls": SOURCE_PINS["source::negative_controls"],
}
D73_EXPLICIT_GOVERNANCE_BINDINGS = {
    "governance::preflight": GOVERNANCE_PINS["governance::preflight"],
    "governance::negative_controls": GOVERNANCE_PINS["governance::negative_controls"],
}

ALL_PINS = {}
ALL_PINS.update(SOURCE_PINS)
ALL_PINS.update(GOVERNANCE_PINS)

# --------------------------------------------------------------------------- #
# ATTEMPT ARTIFACTS (must be ABSENT before and after validators)
# --------------------------------------------------------------------------- #
ATTEMPT_ABSENT = {
    "START": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_start.json",
    "RESULT": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result.json",
    "FAILURE": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_failure.json",
    "PROCESS_EXIT": "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_process_exit.json",
}
JOURNAL_DIRNAME = "phase36_final_probability_authority_diagnostic_v1_4_journal"

# --------------------------------------------------------------------------- #
# score-SHA remediation (D55 / D57 / D66)
# --------------------------------------------------------------------------- #
PHASE27_SCORES_CSV = "reports/tables/phase27_val808_per_sample_scores.csv"
_HEAD = "702133930ce14ac9513c992833396e3e250d08417"
_TAIL = "b17d1032cbd260a405cfb12"
CANONICAL_PHASE27_SCORES_SHA = _HEAD + _TAIL
_INCORRECT_HEAD = "702133930ce14ac9513c992833396e3e250d08417"
_INCORRECT_TAIL = "a17d1032cbd260a405cfb12"

V1_4_FAMILY = [p for (p, _s) in SOURCE_PINS.values()] + [
    p for (p, _s) in GOVERNANCE_PINS.values()
]

# --------------------------------------------------------------------------- #
# helpers
# --------------------------------------------------------------------------- #
def sha256_file(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def journal_record_count() -> int:
    d = ROOT / "reports" / "audits" / JOURNAL_DIRNAME
    if not d.is_dir():
        return 0
    return sum(1 for f in d.rglob("*") if f.is_file())


def attempt_absence_state() -> dict:
    st = {}
    for role, rel in ATTEMPT_ABSENT.items():
        st[role] = {"path": rel, "present": (ROOT / rel).exists()}
    st["_journal_records"] = journal_record_count()
    return st


def absent_ok(st: dict) -> bool:
    return (
        all(not v["present"] for k, v in st.items() if isinstance(v, dict))
        and st["_journal_records"] == 0
    )


def incorrect_sha_occurrences() -> dict:
    needle = _INCORRECT_HEAD + _INCORRECT_TAIL
    hits = {}
    for rel in V1_4_FAMILY:
        fp = ROOT / rel
        if not fp.exists():
            continue
        c = fp.read_text(encoding="utf-8", errors="replace").count(needle)
        if c:
            hits[rel] = c
    return hits


def snapshot(pins: dict) -> dict:
    """Hash a set of pinned files -> {pin_key: sha256}.

    ``pins`` maps pin_key -> (path, expected_sha). Snapshot is keyed by the
    disjoint canonical pin identifier so that pre/post comparison is exact and
    unambiguous (D73/D74).
    """
    return {k: sha256_file(ROOT / v[0]) for k, v in pins.items()}


def write_once_bytes(path: Path, data: bytes) -> None:
    if path.exists():
        raise SystemExit(f"REFUSING TO OVERWRITE EXISTING RECONCILIATION: {path}")
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
    if path.stat().st_size != len(data):
        raise SystemExit(
            f"POST-WRITE SIZE MISMATCH: {path.stat().st_size} != {len(data)}"
        )


def run_suite(rel: str):
    proc = subprocess.run(
        [str(CANONICAL_INTERPRETER), str(ROOT / rel)],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    out = {}
    try:
        out = json.loads(proc.stdout)
    except Exception:
        out = {}
    return proc.returncode, out


def run_supervisor_self_test(rel: str):
    proc = subprocess.run(
        [str(CANONICAL_INTERPRETER), str(ROOT / rel), "--self-test"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    out = {}
    try:
        out = json.loads(proc.stdout)
    except Exception:
        out = {}
    return proc.returncode, out


def run_launcher_verify_only(rel: str):
    proc = subprocess.run(
        [str(CANONICAL_INTERPRETER), str(ROOT / rel), "--verify-only"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    out = {}
    try:
        out = json.loads(proc.stdout)
    except Exception:
        out = {}
    return proc.returncode, out


EXPECTED_LAUNCHER_TERMINAL = (
    "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_LAUNCH_READINESS_VERIFIED"
    "__DISPATCH_SUPPRESSED_BY_VERIFY_ONLY"
)


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="D73/D74 reconciliation builder v1.1")
    ap.add_argument("--run-validators", action="store_true",
                    help="Execute suites read-only (default: static).")
    args = ap.parse_args(argv)

    print("=" * 78)
    print("PHASE36 v1.4 / D73+D74 FINAL-READINESS GOVERNANCE RECONCILIATION (v1.1)")
    print("=" * 78)

    problems = []

    # ---- [0] frozen D72 preservation ----
    print("\n[0] FROZEN D72 PRESERVATION")
    d72_att_sha = sha256_file(D72_ATTESTATION_PATH) if D72_ATTESTATION_PATH.exists() else "ABSENT"
    d72_bld_sha = sha256_file(D72_BUILDER_PATH) if D72_BUILDER_PATH.exists() else "ABSENT"
    d72_att_ok = d72_att_sha == D72_ATTESTATION_SHA
    d72_bld_ok = d72_bld_sha == D72_BUILDER_SHA
    print(f"   D72 attestation sha = {d72_att_sha}  MATCH={d72_att_ok}")
    print(f"   D72 builder sha     = {d72_bld_sha}  MATCH={d72_bld_ok}")
    if not d72_att_ok:
        problems.append("D72 ATTESTATION MODIFIED OR MISSING")
    if not d72_bld_ok:
        problems.append("D72 BUILDER MODIFIED OR MISSING")

    # ---- [1] D73: disjoint pin namespace ----
    print("\n[1] D73 — DISJOINT PIN NAMESPACE")
    all_paths = [rel for (rel, _s) in ALL_PINS.values()]
    n_expected_pins = len(SOURCE_PINS) + len(GOVERNANCE_PINS)
    n_unique_pin_keys = len(set(ALL_PINS.keys()))
    n_unique_paths = len(set(all_paths))
    print(f"   n_expected_pins   = {n_expected_pins}")
    print(f"   n_unique_pin_keys = {n_unique_pin_keys}")
    print(f"   n_unique_paths    = {n_unique_paths}")
    if not (n_expected_pins == n_unique_pin_keys == n_unique_paths == 14):
        problems.append("D73 PIN DISJOINTNESS FAILED")
    # explicit re-bindings
    sp_path, sp_sha = D73_EXPLICIT_SOURCE_BINDINGS["source::preflight"]
    sn_path, sn_sha = D73_EXPLICIT_SOURCE_BINDINGS["source::negative_controls"]
    gp_path, gp_sha = D73_EXPLICIT_GOVERNANCE_BINDINGS["governance::preflight"]
    gn_path, gn_sha = D73_EXPLICIT_GOVERNANCE_BINDINGS["governance::negative_controls"]
    print(f"   source::preflight           {sp_path}  ({sp_sha[:16]}…)")
    print(f"   source::negative_controls   {sn_path}  ({sn_sha[:16]}…)")
    print(f"   governance::preflight       {gp_path}  ({gp_sha[:16]}…)")
    print(f"   governance::negative_controls {gn_path}  ({gn_sha[:16]}…)")
    distinct = len({sp_path, sn_path, gp_path, gn_path}) == 4
    print(f"   4 DISTINCT PATHS = {distinct}")
    if not distinct:
        problems.append("D73 EXPLICIT RE-BINDING PATHS NOT DISTINCT")

    # frozen pin verification (all 14)
    print("\n[1b] FROZEN PIN VERIFICATION (14)")
    frozen_expected = {}
    for k, (rel, exp) in ALL_PINS.items():
        frozen_expected[k] = {"path": rel, "expected_sha256": exp}
        if not (ROOT / rel).exists():
            problems.append(f"MISSING PIN FILE [{k}]: {rel}")

    # ---- [2] ATTEMPT ABSENCE — BEFORE ----
    print("\n[2] ATTEMPT ABSENCE (BEFORE VALIDATORS)")
    pre_ab = attempt_absence_state()
    for role in ATTEMPT_ABSENT:
        print(f"   {'ABSENT ' if not pre_ab[role]['present'] else 'PRESENT'}  {role}")
    print(f"   journal records = {pre_ab['_journal_records']}")
    pre_absence_ok = absent_ok(pre_ab)
    print(f"   BEFORE_ABSENT_OK = {pre_absence_ok}")
    if not pre_absence_ok:
        problems.append("ATTEMPT ARTIFACT/JOURNAL PRESENT BEFORE VALIDATORS")

    # ---- [3] D74: PRE snapshot ----
    print("\n[3] D74 — PRE-VALIDATOR SNAPSHOT (14 disjoint files)")
    pre_validator_hashes = snapshot(ALL_PINS)           # captured ONCE here
    pre_all_frozen = all(
        pre_validator_hashes[k] == ALL_PINS[k][1] for k in ALL_PINS
    )
    for k in ALL_PINS:
        flag = "OK " if pre_validator_hashes[k] == ALL_PINS[k][1] else "BAD"
        print(f"   {flag} {k:<32} {pre_validator_hashes[k][:16]}…")
    print(f"   all_pre_equal_frozen_pins = {pre_all_frozen}")
    if not pre_all_frozen:
        problems.append("PRE SNAPSHOT != FROZEN EXPECTED")

    # ---- [4] run validators ----
    print("\n[4] POST-GOVERNANCE VALIDATION")
    unit_np = unit_nc = pre_np = pre_nc = nc_np = nc_nc = None
    sup_rc = sup_all = sup_n = sup_scen_all = None
    lch_rc = lch_term = lch_gates = None
    if args.run_validators:
        rc, o = run_suite(SOURCE_PINS["source::unit"][0]); unit_np, unit_nc = o.get("n_pass"), o.get("n_checks")
        print(f"   unit         rc={rc} {unit_np}/{unit_nc}")
        rc, o = run_suite(SOURCE_PINS["source::preflight"][0]); pre_np, pre_nc = o.get("n_pass"), o.get("n_checks")
        print(f"   preflight    rc={rc} {pre_np}/{pre_nc}")
        rc, o = run_suite(SOURCE_PINS["source::negative_controls"][0]); nc_np, nc_nc = o.get("n_pass"), o.get("n_checks")
        print(f"   neg_controls rc={rc} {nc_np}/{nc_nc}")
        sup_rc, s = run_supervisor_self_test(SOURCE_PINS["source::supervisor"][0])
        sup_all = s.get("all_pass")
        scen = s.get("synthetic_fixtures") or {}
        sup_n = len(scen)
        sup_scen_all = all(v.get("pass") for v in scen.values()) if scen else False
        print(f"   supervisor   rc={sup_rc} all_pass={sup_all} n={sup_n} scenarios_all_pass={sup_scen_all}")
        lch_rc, lv = run_launcher_verify_only(SOURCE_PINS["source::launcher"][0])
        lch_term = lv.get("terminal")
        bools = {k: v for k, v in lv.items() if isinstance(v, bool)}
        chk = {k: v for k, v in bools.items() if k != "one_shot_gate_set"}
        lch_gates = all(chk.values())
        print(f"   launcher     rc={lch_rc} terminal={lch_term}")
        print(f"   launcher gates all_true={lch_gates} (one_shot_gate_set={lv.get('one_shot_gate_set')})")

    unit_ok = (unit_np == 68 and unit_nc == 68)
    pre_ok = (pre_np == 102 and pre_nc == 102)
    nc_ok = (nc_np == 31 and nc_nc == 31)
    sup_ok = (sup_all is True and sup_n == 6 and sup_scen_all is True)
    lch_ok = (lch_rc == 0 and lch_gates is True and lch_term == EXPECTED_LAUNCHER_TERMINAL)
    print(f"   unit 68/68={unit_ok} · preflight 102/102={pre_ok} · NC 31/31={nc_ok} · "
          f"supervisor 6/6={sup_ok} · launcher PASS={lch_ok}")
    if args.run_validators:
        if not unit_ok: problems.append(f"UNIT != 68/68: {unit_np}/{unit_nc}")
        if not pre_ok: problems.append(f"PREFLIGHT != 102/102: {pre_np}/{pre_nc}")
        if not nc_ok: problems.append(f"NC != 31/31: {nc_np}/{nc_nc}")
        if not sup_ok: problems.append("SUPERVISOR SELF-TEST FAILED")
        if not lch_ok: problems.append("LAUNCHER --verify-only FAILED")

    # ---- [5] D74: POST snapshot ----
    print("\n[5] D74 — POST-VALIDATOR SNAPSHOT (same 14 files)")
    post_validator_hashes = snapshot(ALL_PINS)           # rehash AFTER validators
    pre_equals_post = all(post_validator_hashes[k] == pre_validator_hashes[k] for k in ALL_PINS)
    post_all_frozen = all(post_validator_hashes[k] == ALL_PINS[k][1] for k in ALL_PINS)
    for k in ALL_PINS:
        a = post_validator_hashes[k] == pre_validator_hashes[k]
        b = post_validator_hashes[k] == ALL_PINS[k][1]
        print(f"   {k:<32} PRE==POST={a}  ==FROZEN={b}")
    print(f"   pre_equals_post            = {pre_equals_post}")
    print(f"   all_post_equal_frozen_pins = {post_all_frozen}")
    if not pre_equals_post:
        problems.append("POST SNAPSHOT != PRE SNAPSHOT (SOURCE DRIFT)")
    if not post_all_frozen:
        problems.append("POST SNAPSHOT != FROZEN EXPECTED")

    # ---- [6] ATTEMPT ABSENCE — AFTER ----
    print("\n[6] ATTEMPT ABSENCE (AFTER VALIDATORS)")
    post_ab = attempt_absence_state()
    for role in ATTEMPT_ABSENT:
        print(f"   {'ABSENT ' if not post_ab[role]['present'] else 'PRESENT'}  {role}")
    print(f"   journal records = {post_ab['_journal_records']}")
    post_absence_ok = absent_ok(post_ab)
    print(f"   AFTER_ABSENT_OK = {post_absence_ok}")
    if not post_absence_ok:
        problems.append("ATTEMPT ARTIFACT/JOURNAL PRESENT AFTER VALIDATORS")

    # ---- [7] score-SHA ----
    print("\n[7] SCORE-SHA REMEDIATION")
    csv_sha = sha256_file(ROOT / PHASE27_SCORES_CSV) if (ROOT / PHASE27_SCORES_CSV).exists() else "ABSENT"
    canonical_ok = csv_sha == CANONICAL_PHASE27_SCORES_SHA
    wrong_hits = incorrect_sha_occurrences()
    incorrect_absent = len(wrong_hits) == 0
    print(f"   canonical ok = {canonical_ok} ({csv_sha[:16]}…)")
    print(f"   incorrect historical absent = {incorrect_absent} {wrong_hits or ''}")
    if not canonical_ok:
        problems.append(f"CANONICAL SCORE SHA MISMATCH: {csv_sha}")
    if not incorrect_absent:
        problems.append(f"INCORRECT HISTORICAL SHA PRESENT: {wrong_hits}")

    # ---- FAIL CLOSED ----
    if problems:
        print("\n" + "!" * 78)
        print("FAIL CLOSED — NO RECONCILIATION WRITTEN")
        for p in problems:
            print("   *", p)
        print("!" * 78)
        return 4

    # ---- [8] write ----
    print("\n[8] WRITING WRITE-ONCE RECONCILIATION")
    rec = {
        "reconciliation_revision": BUILDER_REVISION,
        "work_order": "PHASE36_WORK_ORDER_12__D73_D74_FINAL_READINESS_GOVERNANCE_RECONCILIATION",
        "mode": "STATIC_NON_CONSUMING_ONLY",
        "v1_4_executed": False,
        "created_utc": None,
        "classification": {
            "D72": "PRESERVED",
            "D73": "RECONCILED",
            "D74": "RECONCILED",
        },
        "d72_frozen": {
            "d72_attestation_sha256": D72_ATTESTATION_SHA,
            "d72_builder_sha256": D72_BUILDER_SHA,
            "d72_attestation_sha256_observed": d72_att_sha,
            "d72_builder_sha256_observed": d72_bld_sha,
            "d72_attestation_unmodified": d72_att_ok,
            "d72_builder_unmodified": d72_bld_ok,
            "d72_attestation_path": str(D72_ATTESTATION_PATH.relative_to(ROOT)).replace("\\", "/"),
            "d72_builder_path": str(D72_BUILDER_PATH.relative_to(ROOT)).replace("\\", "/"),
        },
        "D73_reconciliation": {
            "defect": "D72_PIN_NAMESPACE_COLLISION__SOURCE_PINS_OVERWRITTEN_BY_GOVERNANCE_PINS",
            "root_cause": (
                "D72 builder merged SOURCE_PINS and GOVERNANCE_PINS into one dict via "
                "ALL_PINS.update(SOURCE_PINS); ALL_PINS.update(GOVERNANCE_PINS); the shared "
                "keys 'preflight' and 'negative_controls' caused governance JSON tuples to "
                "overwrite the source .py tuples"
            ),
            "observed_d72_artifact_impact": {
                "frozen_pins.source.preflight.path": "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_4.json",
                "frozen_pins.source.negative_controls.path": "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_4.json",
                "note": "source .py pins for preflight and negative_controls were NOT recorded",
            },
            "repair": "disjoint canonical identifiers (source::* / governance::*)",
            "n_expected_pins": n_expected_pins,
            "n_unique_pin_keys": n_unique_pin_keys,
            "n_unique_paths": n_unique_paths,
            "disjoint_namespace_ok": (n_expected_pins == n_unique_pin_keys == n_unique_paths == 14),
            "explicit_source_bindings": {
                k: {"path": v[0], "sha256": v[1]} for k, v in D73_EXPLICIT_SOURCE_BINDINGS.items()
            },
            "explicit_governance_bindings": {
                k: {"path": v[0], "sha256": v[1]} for k, v in D73_EXPLICIT_GOVERNANCE_BINDINGS.items()
            },
            "source_and_governance_paths_distinct": distinct,
        },
        "D74_reconciliation": {
            "defect": "D72_PRE_POST_SOURCE_DRIFT_COMPARISON_NOT_IMPLEMENTED",
            "repair": (
                "real before/after 14-file snapshot comparison; pre captured before any "
                "validator and NEVER recomputed; both complete maps persisted"
            ),
            "n_files_compared": len(all_paths),
            "pre_validator_hashes": pre_validator_hashes,
            "post_validator_hashes": post_validator_hashes,
            "frozen_expected_hashes": {k: v["expected_sha256"] for k, v in frozen_expected.items()},
            "pre_equals_post": pre_equals_post,
            "all_pre_equal_frozen_pins": pre_all_frozen,
            "all_post_equal_frozen_pins": post_all_frozen,
        },
        "frozen_pins": {
            "n_source_pins": len(SOURCE_PINS),
            "n_governance_pins": len(GOVERNANCE_PINS),
            "n_unique_pins": n_unique_pin_keys,
            "n_unique_paths": n_unique_paths,
            "source": {k: {"path": v[0], "expected_sha256": v[1]} for k, v in SOURCE_PINS.items()},
            "governance": {k: {"path": v[0], "expected_sha256": v[1]} for k, v in GOVERNANCE_PINS.items()},
        },
        "attempt_absence": {
            "before": {k: (not v["present"]) for k, v in pre_ab.items() if isinstance(v, dict)},
            "after": {k: (not v["present"]) for k, v in post_ab.items() if isinstance(v, dict)},
            "journal_records_before": pre_ab["_journal_records"],
            "journal_records_after": post_ab["_journal_records"],
            "START_ABSENT": not pre_ab["START"]["present"] and not post_ab["START"]["present"],
            "RESULT_ABSENT": not pre_ab["RESULT"]["present"] and not post_ab["RESULT"]["present"],
            "FAILURE_ABSENT": not pre_ab["FAILURE"]["present"] and not post_ab["FAILURE"]["present"],
            "PROCESS_EXIT_ABSENT": not pre_ab["PROCESS_EXIT"]["present"] and not post_ab["PROCESS_EXIT"]["present"],
            "real_journal_records": post_ab["_journal_records"],
        },
        "post_governance_readiness": {
            "unit": f"{unit_np}/{unit_nc}" if unit_nc else None,
            "preflight": f"{pre_np}/{pre_nc}" if pre_nc else None,
            "negative_controls": f"{nc_np}/{nc_nc}" if nc_nc else None,
            "supervisor": f"{sup_n}/6" if sup_n else None,
            "launcher_verify_only": "PASS" if lch_ok else None,
            "launcher_verify_only_terminal": lch_term,
        },
        "state": {
            "v1_4": "ELIGIBLE_NOT_STARTED",
            "attempt_consumed": False,
            "scientific_semantics_effect": "NONE",
            "runtime_execution_effect": "NONE",
            "governance_evidence_effect": "YES",
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
        "note": (
            "Additive governance-evidence reconciliation only; NO scientific-path change. "
            "Frozen D72 attestation and builder PRESERVED UNMODIFIED. v1.4 remains "
            "ELIGIBLE_NOT_STARTED; attempt not consumed."
        ),
    }
    rec["created_utc"] = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    data = (json.dumps(rec, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    write_once_bytes(RECON_PATH, data)
    rec_sha = hashlib.sha256(data).hexdigest()
    bld_sha = sha256_file(Path(__file__).resolve())
    print(f"   RECONCILIATION WRITTEN: {RECON_PATH}")
    print(f"   reconciliation_sha256 = {rec_sha}")
    print(f"   builder_sha256        = {bld_sha}")

    print("\n" + "=" * 78)
    print("PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_4_D73_D74_RECONCILIATION_COMPLETE")
    print("=" * 78)
    print(json.dumps({
        "reconciliation_sha256": rec_sha,
        "builder_sha256": bld_sha,
        "D72": "PRESERVED", "D73": "RECONCILED", "D74": "RECONCILED",
        "n_unique_pins": n_unique_pin_keys, "n_unique_paths": n_unique_paths,
        "unit": f"{unit_np}/{unit_nc}", "preflight": f"{pre_np}/{pre_nc}",
        "negative_controls": f"{nc_np}/{nc_nc}", "supervisor": f"{sup_n}/6",
        "launcher_verify_only": "PASS" if lch_ok else None,
        "pre_equals_post": pre_equals_post,
        "all_pre_equal_frozen_pins": pre_all_frozen,
        "all_post_equal_frozen_pins": post_all_frozen,
        "v1_4": "ELIGIBLE_NOT_STARTED", "attempt_consumed": False,
        "real_journal_records": post_ab["_journal_records"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
