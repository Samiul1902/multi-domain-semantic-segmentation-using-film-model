#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.3 — D66 GOVERNANCE RECONCILIATION BUILDER.

Write-once, FAIL-CLOSED generator for the additive reconciliation artifact:

    reports/audits/
      phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json

D66 = V1_3_GOVERNANCE_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED.

The PRODUCTION launcher still holds the CORRECT Phase27 score authority (it reuses
the frozen v1.2 launcher's ``check_final_authority_preconsumption`` which pins
``PHASE27_SCORES_CSV_SHA = "...17b17d..."``); the frozen v1.3 governance BUILDER
mistyped one hex character (``...17b17d...`` -> ``...17a17d...``), and that incorrect
metadata propagated into the frozen v1.3 contract + eligibility JSONs (metadata only).
It did NOT reach the launcher, the diagnostic source, or the scientific path.

This is the THIRD re-introduction of the identical transcription error along the
additive line (D55 -> v1.1 governance, D57 -> v1.2 governance, D66 -> v1.3 governance);
each time the frozen governance was repaired additively, and each time the error was
re-inherited by the next ``build_...vX_Y.py`` that copied the literal.

This builder performs the full preservation check FIRST and fails closed (writing
NOTHING) if any pin mismatches, then captures a REAL pre-validator snapshot BEFORE
running any validator, runs the non-consuming suites, requires the EXACT expected
results, captures a post-validator snapshot, and requires byte-identical.

It NEVER executes the diagnostic, NEVER loads a model / checkpoint, NEVER reads VAL
image or GT bytes, NEVER touches TEST or ROUTER_HOLDOUT, NEVER retries v1.14 or the
clean-equivalence diagnostic, and NEVER overwrites any existing artifact.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.py
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
AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_3"
RECONCILIATION_REVISION = "v1_0"

VENV = ROOT / ".venv" / "Scripts" / "python.exe"

# ---- authoritative Phase27 score authority -------------------------------- #
PHASE27_SCORES_CSV = "reports/tables/phase27_val808_per_sample_scores.csv"
CORRECT_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
INCORRECT_SHA = "702133930ce14ac9513c992833396e3e250d08417a17d1032cbd260a405cfb12"

# ---- frozen v1.3 runtime source pins (LITERAL) ---------------------------- #
DIAG = "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_3.py"
LAUNCHER = "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_3.py"
UNIT = "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_3.py"
PREFLIGHT = "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_3.py"
NEGCTRL = "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_3.py"
FROZEN_BUILDER = "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3.py"

RUNTIME_PINS = {
    DIAG: "b32a9db41a53b5007c6b9989bdbee22a0b7ea14587d222a3399980142dd9621e",
    LAUNCHER: "d5f9cd3dff302c849d195d909f6f2c9a59fbbbaaf359d859e69442d9fe05b504",
    UNIT: "f6ada4fc4fea22b5deba85fe4c5873f315fde96cb56f351e9710c6027a364ad0",
    PREFLIGHT: "8ce14b6dbc05829850906446a4b107f9fe060843bde0ffa21515cdb22075954b",
    NEGCTRL: "0ebd28e8fd2f3544eee7680a290a97063f73afcadab5eea74608569a00abb265",
    FROZEN_BUILDER: "058371ecf367348dcb1bb9ed11e683d1c0c564da90b4aab47d976ac8ba4416fa",
}

# ---- frozen v1.3 governance pins (LITERAL) -------------------------------- #
CONTRACT = "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_3.json"
SOURCE_FREEZE = "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_3.json"
PREFLIGHT_GOV = "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_3.json"
NEGCTRL_GOV = "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_3.json"
ELIGIBILITY = "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_3.json"
NO_EXEC = "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_3.json"
DIFF_V1_2_TO_V1_3 = "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_to_v1_3_diff.json"

GOVERNANCE_PINS = {
    CONTRACT: "8023962b59e6ffdeab75823315fa195025dac163777e24bff335038c3e138518",
    SOURCE_FREEZE: "73bf1f6e881c5df31c48ba13b6633b7c4d7b1c9a8cf86da9ada21e823a937584",
    PREFLIGHT_GOV: "a192b1af5891d962e9ecde23b1265a6c7fbc4c03732634cd390dcac1e368fa6a",
    NEGCTRL_GOV: "a00b6c7abdc29460a33a442b3666a14e677df464c6e21bc336a5433fc7da7e98",
    ELIGIBILITY: "30c666cfea5fb414aec5e8c003d431c9874477e1dfb83c574fa0a3ccb2e70618",
    NO_EXEC: "81c185dc9624c1bb27fef3d9372f5dae603ee9edc54f5541b49c322985442305",
    DIFF_V1_2_TO_V1_3: "97d142d41add34ac2e1c5021abf032d3a537cac7ed97f34a86c7a77ffd0ff762",
}

# ---- frozen predecessor pins (verified but NOT overwritten) --------------- #
FROZEN_V1_2_LAUNCHER = "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_2.py"
FROZEN_V1_2_LAUNCHER_SHA = "de916786f8237d6f04a4deebde4186a5120164bce073ffa1d0343cf6e265aaee"

V1_3_MARKERS = [
    "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_3.json",
    "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_3.json",
    "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_3.json",
]

# frozen forensic authorities (verified by verify-only; recorded for provenance)
FINAL_AUTHORITY_SHA = "506ab6c4e715a9106889e186c146b73903493c80a63258007954cf5deb3ea9cf"

CORRECT_V1_3_TOKEN = "PHASE36_FINAL_PROB_AUTHORITY_V1_3_LAUNCH_AUTHORITY"
ONE_SHOT_GATE = "PHASE36_FINAL_PROB_AUTHORITY_EXECUTE"
FORBIDDEN_FOREIGN_TOKEN = "PHASE36_V1_14_LAUNCH_AUTHORITY"

# ---- EXACT expected validator results ------------------------------------- #
EXP_UNIT = {"returncode": 0, "all_pass": True, "n_checks": 42, "n_pass": 42}
EXP_PREFLIGHT = {"returncode": 0, "all_pass": True, "n_checks": 47, "n_pass": 47}
EXP_NEGCTRL = {"returncode": 0, "all_pass": True, "n_checks": 21, "n_pass": 21}
VERIFY_ONLY_TERMINAL = ("PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_LAUNCH_READINESS_VERIFIED"
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
    "v1_2_consumed_state_binding_pass": True,
    "v1_2_failure_absent": True,
    "d61_classification_bound": "ACCEPT_FINAL_FUSION_SEMANTICS_DIVERGE_FROM_PHASE27",
    "d60_reconciled_bound": "FINAL_AUTHORITY_MISMATCH_EXACTLY_LOCALIZED_TO_PHASE27_ACCEPT_FINAL_SOURCE",
    "d56_module_interface_pass": True,
    "d56_subscript_free": True,
    "d56_load_clean_image_tensor_attribute_access": True,
    "d56_canonical_learned_core_attribute_access": True,
    "d61_has_fuse_full_field_call": True,
    "d61_absent_model_fusion_call": True,
    "terminal": VERIFY_ONLY_TERMINAL,
}

OUT = AUD / "phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.json"
SELF = ROOT / "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_3_governance_reconciliation_v1_0.py"


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


def run_suite(path: str) -> dict:
    r = subprocess.run([str(VENV), str(ROOT / path)], capture_output=True, text=True)
    j = _last_json(r.stdout)
    return {"returncode": r.returncode, "n_checks": j.get("n_checks"),
            "n_pass": j.get("n_pass"), "all_pass": j.get("all_pass")}


def fatal(code: int, reason: str, **extra) -> int:
    payload = {"REFUSED": reason,
               "builder": "phase36_final_prob_authority_v1_3_reconciliation_v1_0"}
    payload.update(extra)
    print(json.dumps(payload, indent=1))
    return code


def _diff(exp: dict, got: dict) -> dict:
    return {k: {"expected": exp[k], "observed": got.get(k)} for k in exp if got.get(k) != exp[k]}


def _occurrences(path: str, needle: str) -> list:
    p = ROOT / path
    if not p.exists():
        return []
    out = []
    for i, line in enumerate(p.read_text(encoding="utf-8").splitlines(), start=1):
        if needle in line:
            out.append({"line": i, "text": line.strip()})
    return out


def main() -> int:
    # ---- (0) write-once precondition ------------------------------------ #
    if OUT.exists():
        return fatal(2, "RECONCILIATION_V1_0_ALREADY_EXISTS", path=str(OUT))

    # ---- (1) verify EVERY frozen v1.3 pin ------------------------------- #
    pin_bad = {}
    for k, (p, e) in {**{f"runtime::{a}": (a, b) for a, b in RUNTIME_PINS.items()},
                      **{f"governance::{a}": (a, b) for a, b in GOVERNANCE_PINS.items()}}.items():
        o = sha(ROOT / p)
        if o != e:
            pin_bad[k] = {"observed": o, "expected": e}
    if pin_bad:
        return fatal(3, "FROZEN_PIN_MISMATCH", bad=pin_bad)

    aux_bad = {}
    for k, (p, e) in {"frozen_v1_2_launcher": (FROZEN_V1_2_LAUNCHER, FROZEN_V1_2_LAUNCHER_SHA)}.items():
        o = sha(ROOT / p)
        if o != e:
            aux_bad[k] = {"observed": o, "expected": e}
    if aux_bad:
        return fatal(3, "AUXILIARY_PIN_MISMATCH", bad=aux_bad)

    # ---- (2) v1.3 markers ABSENT (pre-validator) ------------------------ #
    present = [m for m in V1_3_MARKERS if (ROOT / m).exists()]
    if present:
        return fatal(3, "V1_3_MARKER_PRESENT_UNEXPECTED", present=present)

    # ---- (3) REAL pre-validator snapshot (captured BEFORE validators) ---- #
    all_pins = {**RUNTIME_PINS, **GOVERNANCE_PINS}
    pre_validator_hashes = {k: sha(ROOT / k) for k in all_pins}
    pre_bad = {k: {"observed": pre_validator_hashes[k], "expected": all_pins[k]}
               for k in all_pins if pre_validator_hashes[k] != all_pins[k]}
    if pre_bad:
        return fatal(4, "PRE_VALIDATOR_HASH_MISMATCH", bad=pre_bad)

    # ---- (4) D66 STATIC EVIDENCE ---------------------------------------- #
    csv_got = sha(ROOT / PHASE27_SCORES_CSV)
    if csv_got != CORRECT_SHA:
        return fatal(4, "ACTUAL_PHASE27_SCORES_SHA_NOT_CORRECT",
                     observed=csv_got, expected=CORRECT_SHA)

    builder_src = (ROOT / FROZEN_BUILDER).read_text(encoding="utf-8")
    contract_src = (ROOT / CONTRACT).read_text(encoding="utf-8")
    eligibility_src = (ROOT / ELIGIBILITY).read_text(encoding="utf-8")
    launcher_src = (ROOT / LAUNCHER).read_text(encoding="utf-8")
    diag_src = (ROOT / DIAG).read_text(encoding="utf-8")

    # exact per-file occurrences of the WRONG literal
    occ_builder = _occurrences(FROZEN_BUILDER, INCORRECT_SHA)
    occ_contract = _occurrences(CONTRACT, INCORRECT_SHA)
    occ_eligibility = _occurrences(ELIGIBILITY, INCORRECT_SHA)

    # exact per-file occurrences of the CORRECT literal in the affected artifacts
    corr_in_builder = _occurrences(FROZEN_BUILDER, CORRECT_SHA)
    corr_in_contract = _occurrences(CONTRACT, CORRECT_SHA)
    corr_in_eligibility = _occurrences(ELIGIBILITY, CORRECT_SHA)

    # runtime unaffected: neither literal in launcher or diagnostic source
    launcher_has_wrong = INCORRECT_SHA in launcher_src
    launcher_has_correct_literal = CORRECT_SHA in launcher_src
    diag_has_wrong = INCORRECT_SHA in diag_src
    diag_has_correct_literal = CORRECT_SHA in diag_src

    # runtime gate authority: the frozen v1.2 launcher (reused verbatim) pins CORRECT
    v12_launcher_src = (ROOT / FROZEN_V1_2_LAUNCHER).read_text(encoding="utf-8")
    v12_runtime_gate_correct = f'PHASE27_SCORES_CSV_SHA = "{CORRECT_SHA}"' in v12_launcher_src
    v12_runtime_gate_has_wrong = INCORRECT_SHA in v12_launcher_src

    # predecessor reconciliation chain (D55 -> D57 -> D66)
    recon_v1_1_path = "reports/audits/phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json"
    recon_v1_2_path = "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_0.json"
    recon_v1_2_v1_1_path = "reports/audits/phase36_final_probability_authority_diagnostic_v1_2_governance_reconciliation_v1_1.json"

    d66 = {
        "classification": "V1_3_GOVERNANCE_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED",
        "root_cause_established": True,
        "incorrect_transcribed_sha256": INCORRECT_SHA,
        "correct_authoritative_sha256": CORRECT_SHA,
        "phase27_scores_csv_path": PHASE27_SCORES_CSV,
        "phase27_scores_csv_raw_byte_sha256": csv_got,
        "phase27_scores_csv_matches_correct": True,
        "transcription_delta": {
            "position_from_literal_start_0_based": 41,
            "correct_char": "b",
            "incorrect_char": "a",
            "note": ("the ONLY delta between the two phase27 score SHAs is a single hex "
                     "character at 0-based index 41 of the 64-char digest: 'b' (correct) vs "
                     "'a' (incorrect)"),
        },
        "propagation": {
            "frozen_v1_3_governance_builder": {
                "path": FROZEN_BUILDER,
                "sha256": RUNTIME_PINS[FROZEN_BUILDER],
                "contains_incorrect_sha256": bool(occ_builder),
                "contains_correct_sha256": bool(corr_in_builder),
                "occurrences_incorrect": occ_builder,
                "occurrences_correct": corr_in_builder,
                "source_of_error": True,
            },
            "frozen_v1_3_contract": {
                "path": CONTRACT,
                "sha256": GOVERNANCE_PINS[CONTRACT],
                "contains_incorrect_sha256": bool(occ_contract),
                "contains_correct_sha256": bool(corr_in_contract),
                "occurrences_incorrect": occ_contract,
                "occurrences_correct": corr_in_contract,
                "source_of_error": False,
            },
            "frozen_v1_3_eligibility": {
                "path": ELIGIBILITY,
                "sha256": GOVERNANCE_PINS[ELIGIBILITY],
                "contains_incorrect_sha256": bool(occ_eligibility),
                "contains_correct_sha256": bool(corr_in_eligibility),
                "occurrences_incorrect": occ_eligibility,
                "occurrences_correct": corr_in_eligibility,
                "source_of_error": False,
            },
            "runtime_launcher": {
                "path": LAUNCHER,
                "sha256": RUNTIME_PINS[LAUNCHER],
                "contains_incorrect_sha256": launcher_has_wrong,
                "contains_correct_sha256_literal": launcher_has_correct_literal,
            },
            "diagnostic_source": {
                "path": DIAG,
                "sha256": RUNTIME_PINS[DIAG],
                "contains_incorrect_sha256": diag_has_wrong,
                "contains_correct_sha256_literal": diag_has_correct_literal,
            },
        },
        "runtime_authority": {
            "frozen_v1_2_launcher_reused_verbatim": True,
            "frozen_v1_2_launcher_path": FROZEN_V1_2_LAUNCHER,
            "frozen_v1_2_launcher_sha256": FROZEN_V1_2_LAUNCHER_SHA,
            "runtime_gate_pins_correct_sha": v12_runtime_gate_correct,
            "runtime_gate_contains_wrong_sha": v12_runtime_gate_has_wrong,
            "runtime_launcher_uses_correct_sha": not launcher_has_wrong,
        },
        "recidivism_chain": [
            {"defect": "D55", "target_family": "v1_1",
             "reconciliation": recon_v1_1_path,
             "reconciliation_sha256": sha(ROOT / recon_v1_1_path)},
            {"defect": "D57", "target_family": "v1_2",
             "reconciliation": recon_v1_2_path,
             "reconciliation_sha256": sha(ROOT / recon_v1_2_path)},
            {"defect": "D59", "target_family": "v1_2",
             "reconciliation": recon_v1_2_v1_1_path,
             "reconciliation_sha256": sha(ROOT / recon_v1_2_v1_1_path)},
            {"defect": "D66", "target_family": "v1_3",
             "reconciliation": str(OUT.relative_to(ROOT)).replace("\\", "/"),
             "reconciliation_sha256": "SELF"},
        ],
        "recidivism_note": ("The identical single-hex transcription error has now been "
                            "re-introduced three times along the additive governance line "
                            "(v1.1 builder -> v1.2 builder -> v1.3 builder), each time by a "
                            "new build_...vX_Y.py that copied the previous literal. This "
                            "reconciliation records the third occurrence; the remediation "
                            "recommendation is that future builders derive the literal from "
                            "the launcher runtime authority constant rather than retyping it."),
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "scientific_semantics_effect": "NONE",
        "runtime_execution_effect": "NONE",
        "governance_provenance_effect": "YES",
    }
    if not (d66["propagation"]["frozen_v1_3_governance_builder"]["contains_incorrect_sha256"]
            and d66["propagation"]["frozen_v1_3_contract"]["contains_incorrect_sha256"]
            and d66["propagation"]["frozen_v1_3_eligibility"]["contains_incorrect_sha256"]
            and d66["runtime_authority"]["runtime_gate_pins_correct_sha"]
            and not d66["runtime_authority"]["runtime_gate_contains_wrong_sha"]):
        return fatal(4, "D66_EVIDENCE_INCONSISTENT__FAIL_CLOSED__NO_WRITE", d66=d66)

    # ---- (5) RUN VALIDATORS (non-consuming) ----------------------------- #
    unit_run = run_suite(UNIT)
    preflight_run = run_suite(PREFLIGHT)
    nc_run = run_suite(NEGCTRL)
    vo = subprocess.run([str(VENV), str(ROOT / LAUNCHER), "--verify-only"],
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
    present_after = [m for m in V1_3_MARKERS if (ROOT / m).exists()]
    if present_after:
        return fatal(6, "V1_3_MARKER_CREATED_DURING_VALIDATION", present=present_after)

    # ---- (7) REAL post-validator snapshot + strict comparison ----------- #
    post_validator_hashes = {k: sha(ROOT / k) for k in all_pins}
    post_bad = {k: {"observed": post_validator_hashes[k], "expected": all_pins[k]}
                for k in all_pins if post_validator_hashes[k] != all_pins[k]}
    if post_bad:
        return fatal(6, "POST_VALIDATOR_HASH_NOT_EQUAL_FROZEN_PIN", bad=post_bad)
    drift = {k: {"pre": pre_validator_hashes[k], "post": post_validator_hashes[k]}
             for k in all_pins if pre_validator_hashes[k] != post_validator_hashes[k]}
    if drift:
        return fatal(6, "SOURCE_DRIFT_ACROSS_VALIDATION", drift=drift)
    pre_equals_post = (pre_validator_hashes == post_validator_hashes)
    all_equal_frozen_pins = all(post_validator_hashes[k] == all_pins[k] for k in all_pins)
    if not (pre_equals_post and all_equal_frozen_pins):
        return fatal(6, "PRE_POST_INVARIANT_FAILED",
                     pre_equals_post=pre_equals_post, all_equal_frozen_pins=all_equal_frozen_pins)

    # ---- (8) write the reconciliation (once) ---------------------------- #
    ts = now()
    payload = {
        "artifact_kind":
            "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_3_GOVERNANCE_RECONCILIATION",
        "revision": REVISION,
        "reconciliation_revision": RECONCILIATION_REVISION,
        "supersedes": None,
        "amends": None,
        "additive": True,
        "mode": "STATIC_GOVERNANCE_NON_CONSUMING_ONLY",
        "D66": "RECONCILED",
        "d66_classification":
            "V1_3_GOVERNANCE_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED",
        "d66_root_cause_established": True,
        "d66_static_evidence": d66,
        "incorrect_transcribed_sha256": INCORRECT_SHA,
        "correct_phase27_scores_sha256": CORRECT_SHA,
        "phase27_scores_csv_path": PHASE27_SCORES_CSV,
        "actual_phase27_scores_csv_raw_byte_sha256": csv_got,
        "actual_phase27_scores_sha_matches_correct": (csv_got == CORRECT_SHA),
        "affected_artifacts": [
            {"path": FROZEN_BUILDER,
             "role": "frozen_v1_3_governance_builder",
             "sha256": RUNTIME_PINS[FROZEN_BUILDER],
             "contains_incorrect_sha256": True,
             "source_of_error": True},
            {"path": CONTRACT,
             "role": "frozen_v1_3_contract",
             "sha256": GOVERNANCE_PINS[CONTRACT],
             "contains_incorrect_sha256": True,
             "source_of_error": False},
            {"path": ELIGIBILITY,
             "role": "frozen_v1_3_eligibility",
             "sha256": GOVERNANCE_PINS[ELIGIBILITY],
             "contains_incorrect_sha256": True,
             "source_of_error": False},
        ],
        "runtime_launcher_uses_correct_sha": not launcher_has_wrong,
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "scientific_semantics_effect": "NONE",
        "runtime_execution_effect": "NONE",
        "governance_provenance_effect": "YES",
        "original_artifacts_overwritten": False,
        "frozen_v1_3_preservation": {
            "all_intact": True,
            "runtime_source_sha256": {p: sha(ROOT / p) for p in RUNTIME_PINS},
            "governance_sha256": {p: sha(ROOT / p) for p in GOVERNANCE_PINS},
            "contract_sha256": sha(ROOT / CONTRACT),
            "frozen_v1_2_launcher": {"path": FROZEN_V1_2_LAUNCHER,
                                     "sha256": sha(ROOT / FROZEN_V1_2_LAUNCHER)},
        },
        "pre_validator_hashes": pre_validator_hashes,
        "post_validator_hashes": post_validator_hashes,
        "pre_equals_post": pre_equals_post,
        "all_equal_frozen_pins": all_equal_frozen_pins,
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
                "v1_2_consumed_state_binding_pass": vj.get("v1_2_consumed_state_binding_pass"),
                "v1_2_failure_absent": vj.get("v1_2_failure_absent"),
                "d61_classification_bound": vj.get("d61_classification_bound"),
                "d60_reconciled_bound": vj.get("d60_reconciled_bound"),
                "d56_module_interface_pass": vj.get("d56_module_interface_pass"),
                "d56_subscript_free": vj.get("d56_subscript_free"),
                "d56_load_clean_image_tensor_attribute_access":
                    vj.get("d56_load_clean_image_tensor_attribute_access"),
                "d56_canonical_learned_core_attribute_access":
                    vj.get("d56_canonical_learned_core_attribute_access"),
                "d61_has_fuse_full_field_call": vj.get("d61_has_fuse_full_field_call"),
                "d61_absent_model_fusion_call": vj.get("d61_absent_model_fusion_call"),
                "diagnostic_source_observed_sha256": vj.get("diagnostic_source_observed_sha256"),
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
        "v1_3_markers_absent_after_validation": True,
        "effective_runtime_launch_token": CORRECT_V1_3_TOKEN,
        "effective_execution_eligibility": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "authorization_semantics": {
            "one_shot_gate_env": f"{ONE_SHOT_GATE}=1",
            "launch_authority_token_env": f"{CORRECT_V1_3_TOKEN}=1",
            "forbidden_foreign_token_env": FORBIDDEN_FOREIGN_TOKEN,
            "forbidden_v1_1_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_1_LAUNCH_AUTHORITY",
            "forbidden_v1_2_token_reuse": "PHASE36_FINAL_PROB_AUTHORITY_V1_2_LAUNCH_AUTHORITY",
        },
        "prohibitions_observed": [
            "no_v1_3_diagnostic_execution", "no_start_result_failure_marker",
            "no_model_run", "no_checkpoint_deserialization",
            "no_val_image_read", "no_val_gt_read", "no_perturbations",
            "no_test", "no_router_holdout", "no_v1_14_retry",
            "no_clean_equivalence_retry", "no_v1_15_science", "no_phase37",
            "no_runtime_source_modified", "no_existing_governance_overwritten",
            "no_v1_3_frozen_artifact_modified", "no_v1_2_reconciliation_overwritten",
        ],
        "governance_state_after": {
            "v1_0": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
            "v1_1": "CONSUMED_FAILED",
            "v1_1_retry_permitted": False,
            "v1_2_final_prob": "CONSUMED_RESULT",
            "v1_2_retry_permitted": False,
            "v1_3_final_prob": "ELIGIBLE_NOT_STARTED",
            "v1_14_science": "CONSUMED_FAILED",
            "v1_15": "NOT_CREATED",
            "phase37": "NOT_STARTED",
            "test": "PHASE39_ONLY",
            "router_holdout": "NOT_ACCESSED",
        },
        "scientific_output": False,
        "generated_utc": ts,
    }
    write_once(OUT, payload)

    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_3_D66_GOVERNANCE_RECONCILIATION_BUILT",
        "reconciliation_sha256": sha(OUT),
        "reconciliation_builder_sha256": sha(SELF),
        "D66": "RECONCILED",
        "d66_classification": "V1_3_GOVERNANCE_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR_REINTRODUCED",
        "correct_phase27_scores_sha256": CORRECT_SHA,
        "incorrect_transcribed_sha256": INCORRECT_SHA,
        "actual_phase27_scores_csv_raw_byte_sha256": csv_got,
        "actual_phase27_scores_sha_matches_correct": (csv_got == CORRECT_SHA),
        "runtime_launcher_uses_correct_sha": not launcher_has_wrong,
        "affected_artifacts": [FROZEN_BUILDER, CONTRACT, ELIGIBILITY],
        "pre_equals_post": pre_equals_post,
        "all_equal_frozen_pins": all_equal_frozen_pins,
        "unit": unit_run,
        "preflight": preflight_run,
        "negative_controls": nc_run,
        "launcher_verify_only_rc": vo.returncode,
        "launcher_verify_only_terminal": vj.get("terminal"),
        "effective_execution_eligibility": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
        "v1_3_start_result_failure": "ABSENT",
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
