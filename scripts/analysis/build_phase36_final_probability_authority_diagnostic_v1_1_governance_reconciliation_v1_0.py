#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 36 — FINAL-PROBABILITY AUTHORITY DIAGNOSTIC v1.1 — D55 GOVERNANCE RECONCILIATION BUILDER.

Write-once generator for ONE additive reconciliation artifact:

    reports/audits/phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json

D55 = GOVERNANCE_BUILDER_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR.

The PRODUCTION launcher holds the CORRECT Phase27 score authority; the frozen
v1.1 governance BUILDER mistyped one hex character (``...17b17d...`` -> ``...17a17d...``),
and that incorrect metadata propagated into the frozen contract + eligibility
JSONs (metadata only).  It did NOT reach the launcher, the diagnostic source or
the scientific path.

This builder performs the full preservation check FIRST and fails closed (writing
NOTHING) if any pin mismatches.  It NEVER executes the diagnostic, NEVER loads a
model / checkpoint, NEVER reads VAL image or GT bytes, NEVER touches TEST or
ROUTER_HOLDOUT.

Run:  .venv\\Scripts\\python.exe scripts\\analysis\\build_phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.py
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"

REVISION = "ra_medfilm_barr_phase36_final_probability_authority_diagnostic_v1_1"
RECONCILIATION_REVISION = "v1_0"

# ---- authoritative Phase27 score authority -------------------------------- #
PHASE27_SCORES_CSV = "reports/tables/phase27_val808_per_sample_scores.csv"
CORRECT_SHA = "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12"
INCORRECT_SHA = "702133930ce14ac9513c992833396e3e250d08417a17d1032cbd260a405cfb12"

# ---- frozen v1.1 runtime source pins -------------------------------------- #
V1_1_PINS = {
    "scripts/analysis/phase36_final_probability_authority_diagnostic_v1_1.py":
        "b9f6a449445d8ac5edd1dafe30e2f0b5005d487be314011bd2ff9162db770672",
    "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py":
        "4c9737362fcf01f0ef8ef629f489cdff07c72e63b46f34e4ea508b7ba0df83ae",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_unit_v1_1.py":
        "0358ed115dcedea612aae1b7f0311ea08b97ba212b893a10c51ddae606fbabea",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_preflight_v1_1.py":
        "7ba8899b25fbddbcebd42971eedd1bca4b2ca8d06d33629cec7a286e01227925",
    "scripts/analysis/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.py":
        "ef7a7d8c5b7d9699fa375b2bcfccc3c482ac9e4d1b4ce9a1c3807142100a6950",
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_1.py":
        "498c7460c3e588317f3741da8fbcbf4886a660aec5ba0aa880422f8d7f6200f8",
}

# ---- frozen v1.1 governance pins ------------------------------------------ #
GOVERNANCE_PINS = {
    "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_1.json":
        "84398af09ad814c8d1d326bac20aaee9ee1400e09d1a18baf12b8448b543967c",
    "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_1.json":
        "bd2fd129f59848faaaed9fa7c400eca0ce693d2d3cb25beaa18d8c0488210aac",
    "reports/audits/phase36_final_probability_authority_diagnostic_source_freeze_v1_1.json":
        "a93a9aaa7e22b96d42c80a64d08f2576fcdfcf08e947643c7272d593ab967b0b",
    "reports/audits/phase36_final_probability_authority_diagnostic_preflight_v1_1.json":
        "0bfc783b342a5c9f9e1ae7473240c80b442a27e85ed4a0b61af3c80652c42819",
    "reports/audits/phase36_final_probability_authority_diagnostic_negative_controls_v1_1.json":
        "a8ff8347fc0a54ebfb4ffefadfe8d94163f8026186c4c51224dee24f2aa7fb34",
    "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json":
        "6394c88552ef9a1ebd57de2e023466a256596f09affd20582b95db8b119e2a29",
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_0_to_v1_1_diff.json":
        "3c88a2173854774f9d8bba242ce84d83d4984c66eb4f34f5ec7b26cfbfc37a17",
}

D51_RECONCILIATION_SHA = "d8e3e83e6c31004e610faef9d93c221c026eb8974c033f47fbff91106836758b"
D51_RECONCILIATION_PATH = "reports/audits/phase36_clean_equivalence_d51_reconciliation_v1_1.json"

V1_2_RESULT_PATH = "reports/audits/phase36_clean_equivalence_diagnostic_result_v1_2.json"
V1_2_RESULT_SHA = "b64f7e6282f9abb864a5d5bc438a22e1096aaf56e0a4e94fe53ba7c9bab6fa4a"
STATIC_AUDIT_PATH = "reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json"

MARKERS_V1_1 = [
    "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_1.json",
    "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_1.json",
    "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_1.json",
]

OUT = AUD / "phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.json"


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


def main() -> int:
    if OUT.exists():
        print(json.dumps({"REFUSED": "RECONCILIATION_ALREADY_EXISTS", "path": str(OUT)}, indent=1))
        return 2

    # ---------------- preservation check (fail closed) --------------------- #
    bad: dict = {}

    for p, exp in V1_1_PINS.items():
        got = sha(ROOT / p)
        if got != exp:
            bad[p] = {"expected": exp, "observed": got}
    for p, exp in GOVERNANCE_PINS.items():
        got = sha(ROOT / p)
        if got != exp:
            bad[p] = {"expected": exp, "observed": got}

    d51_got = sha(ROOT / D51_RECONCILIATION_PATH)
    if d51_got != D51_RECONCILIATION_SHA:
        bad[D51_RECONCILIATION_PATH] = {"expected": D51_RECONCILIATION_SHA, "observed": d51_got}

    csv_got = sha(ROOT / PHASE27_SCORES_CSV)
    if csv_got != CORRECT_SHA:
        bad[PHASE27_SCORES_CSV] = {"expected": CORRECT_SHA, "observed": csv_got}

    v1_2_got = sha(ROOT / V1_2_RESULT_PATH)
    if v1_2_got != V1_2_RESULT_SHA:
        bad[V1_2_RESULT_PATH] = {"expected": V1_2_RESULT_SHA, "observed": v1_2_got}

    marker_present = [m for m in MARKERS_V1_1 if (ROOT / m).exists()]
    if marker_present:
        bad["v1_1_markers_present"] = marker_present

    if bad:
        print(json.dumps({"REFUSED": "PRESERVATION_CHECK_FAILED__FAIL_CLOSED__NO_WRITE",
                          "bad": bad}, indent=1))
        return 3

    # ---------------- defect evidence (static, no execution) -------------- #
    launcher_path = "scripts/analysis/launch_phase36_final_probability_authority_diagnostic_v1_1.py"
    builder_path = "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_1.py"
    contract_path = "reports/audits/phase36_final_probability_authority_diagnostic_contract_v1_1.json"
    eligibility_path = "reports/audits/phase36_final_probability_authority_diagnostic_eligibility_v1_1.json"

    launcher_src = (ROOT / launcher_path).read_text(encoding="utf-8")
    builder_src = (ROOT / builder_path).read_text(encoding="utf-8")
    contract_src = (ROOT / contract_path).read_text(encoding="utf-8")
    eligibility_src = (ROOT / eligibility_path).read_text(encoding="utf-8")

    launcher_literal_ok = f'PHASE27_SCORES_CSV_SHA = "{CORRECT_SHA}"' in launcher_src
    builder_has_incorrect = INCORRECT_SHA in builder_src
    contract_has_incorrect = INCORRECT_SHA in contract_src
    eligibility_has_incorrect = INCORRECT_SHA in eligibility_src

    # v1.2 consumed result binding (expected == observed == correct)
    v1_2 = json.loads((ROOT / V1_2_RESULT_PATH).read_text(encoding="utf-8"))
    ps = v1_2["reference_authority_paths_and_sha256"]["per_sample_scores"]
    v1_2_expected = ps.get("expected_sha256")
    v1_2_observed = ps.get("observed_sha256")
    v1_2_bound = (v1_2_expected == CORRECT_SHA and v1_2_observed == CORRECT_SHA
                  and ps.get("path") == PHASE27_SCORES_CSV)

    # secondary bookkeeping field-name typo
    no_exec = json.loads(
        (ROOT / "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json")
        .read_text(encoding="utf-8"))
    no_exec_has_typo_field = "v1_11_artifacts_modified" in no_exec

    # defensive: the reconciliation must only be written when the defect is
    # actually present and the launcher is actually correct.
    if not (launcher_literal_ok and builder_has_incorrect and contract_has_incorrect
            and eligibility_has_incorrect and v1_2_bound and no_exec_has_typo_field):
        print(json.dumps({"REFUSED": "D55_EVIDENCE_INCONSISTENT__FAIL_CLOSED__NO_WRITE",
                          "launcher_literal_ok": launcher_literal_ok,
                          "builder_has_incorrect": builder_has_incorrect,
                          "contract_has_incorrect": contract_has_incorrect,
                          "eligibility_has_incorrect": eligibility_has_incorrect,
                          "v1_2_bound": v1_2_bound,
                          "no_exec_has_typo_field": no_exec_has_typo_field}, indent=1))
        return 4

    builder_self_sha = sha(Path(__file__))
    ts = now()

    payload = {
        "artifact_kind":
            "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_1_GOVERNANCE_RECONCILIATION",
        "revision": REVISION,
        "reconciliation_revision": RECONCILIATION_REVISION,
        "d55_classification": "GOVERNANCE_BUILDER_PHASE27_SCORE_SHA_TRANSCRIPTION_ERROR",
        "d55_root_cause_established": True,
        "incorrect_transcribed_sha256": INCORRECT_SHA,
        "correct_authoritative_sha256": CORRECT_SHA,
        "phase27_scores_csv_path": PHASE27_SCORES_CSV,
        "affected_artifacts": [
            {"path": builder_path,
             "role": "frozen_v1_1_governance_builder",
             "sha256": V1_1_PINS[builder_path],
             "contains_incorrect_sha256": True,
             "source_of_error": True},
            {"path": contract_path,
             "role": "frozen_v1_1_contract",
             "sha256": GOVERNANCE_PINS[contract_path],
             "contains_incorrect_sha256": True,
             "source_of_error": False},
            {"path": eligibility_path,
             "role": "frozen_v1_1_eligibility",
             "sha256": GOVERNANCE_PINS[eligibility_path],
             "contains_incorrect_sha256": True,
             "source_of_error": False},
        ],
        "runtime_launcher_affected": False,
        "diagnostic_source_affected": False,
        "scientific_path_affected": False,
        "scientific_semantics_effect": "NONE",
        "runtime_execution_effect": "NONE",
        "governance_provenance_effect": "YES",
        "D52_runtime_gate_uses_correct_sha": True,
        "launcher_evidence": {
            "path": launcher_path,
            "sha256": V1_1_PINS[launcher_path],
            "literal": f'PHASE27_SCORES_CSV_SHA = "{CORRECT_SHA}"',
            "literal_present": launcher_literal_ok,
            "uses_correct_sha": True,
        },
        "consumed_evidence_binding": {
            "source": V1_2_RESULT_PATH,
            "source_sha256": V1_2_RESULT_SHA,
            "field_path": "reference_authority_paths_and_sha256.per_sample_scores",
            "path": ps.get("path"),
            "expected_sha256": v1_2_expected,
            "observed_sha256": v1_2_observed,
            "expected_equals_observed": v1_2_expected == v1_2_observed,
            "both_equal_correct_authoritative": v1_2_bound,
            "prior_static_evidence": {
                "path": STATIC_AUDIT_PATH,
                "phase27_scores_sha256":
                    "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
                "phase27_scores_expected":
                    "702133930ce14ac9513c992833396e3e250d08417b17d1032cbd260a405cfb12",
            },
        },
        "secondary_bookkeeping_correction": {
            "original_no_execution_field": "v1_11_artifacts_modified=false",
            "correct_interpretation": "v1_1_artifacts_modified=false",
            "classification": "NON_SCIENTIFIC_FIELD_NAME_TYPO",
            "artifact": "reports/audits/phase36_final_probability_authority_diagnostic_no_execution_audit_v1_1.json",
            "field_present_in_frozen_artifact": no_exec_has_typo_field,
            "overwritten": False,
        },
        "preservation_check": {
            "all_pass": True,
            "v1_1_runtime_source_sha256": {p: sha(ROOT / p) for p in V1_1_PINS},
            "frozen_v1_1_governance_sha256": {p: sha(ROOT / p) for p in GOVERNANCE_PINS},
            "d51_reconciliation": {"path": D51_RECONCILIATION_PATH,
                                   "sha256": d51_got},
            "phase27_scores_csv_raw_byte_sha256": csv_got,
            "phase27_scores_csv_matches_correct": csv_got == CORRECT_SHA,
            "v1_1_start_marker_absent": not (ROOT / MARKERS_V1_1[0]).exists(),
            "v1_1_result_marker_absent": not (ROOT / MARKERS_V1_1[1]).exists(),
            "v1_1_failure_marker_absent": not (ROOT / MARKERS_V1_1[2]).exists(),
        },
        "no_execution": {
            "model_forward": False,
            "checkpoint_deserialization": False,
            "val_image_read": False,
            "val_gt_read": False,
            "VAL_GT_READ": 0,
            "test_accessed": False,
            "router_holdout_accessed": False,
            "diagnostic_attempt_consumed": False,
        },
        "end_state": {
            "D52": "REPAIRED / SOURCE-AUDITED PASS",
            "D53": "REPAIRED / SOURCE-AUDITED PASS",
            "D54": "REPAIRED / SOURCE-AUDITED PASS",
            "D55": "RECONCILED",
            "diagnostic_v1_0": "FROZEN_NEVER_CONSUMED_NOT_AUTHORIZED",
            "diagnostic_v1_1": "ELIGIBLE_NOT_STARTED",
            "v1_1_start_result_failure": "ABSENT",
            "v1_2_clean_equivalence": "CONSUMED_RESULT__RETRY_FORBIDDEN",
            "v1_14_science": "CONSUMED_FAILED__RETRY_FORBIDDEN",
            "v1_15": "NOT_CREATED",
            "phase37": "NOT_STARTED",
            "test": "PHASE39_ONLY",
            "router_holdout": "NOT_ACCESSED",
        },
        "reconciliation_builder": {
            "path": "scripts/analysis/"
                    "build_phase36_final_probability_authority_diagnostic_v1_1_governance_reconciliation_v1_0.py",
            "sha256": builder_self_sha,
        },
        "original_artifacts_overwritten": False,
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync (exclusive-create, write-once)",
        "generated_utc": ts,
    }

    write_once(OUT, payload)
    print(json.dumps({
        "status": "PHASE36_FINAL_PROB_AUTHORITY_DIAGNOSTIC_V1_1_D55_GOVERNANCE_RECONCILIATION_WRITTEN",
        "reconciliation_path": str(OUT.relative_to(ROOT)),
        "reconciliation_sha256": sha(OUT),
        "reconciliation_builder_sha256": builder_self_sha,
        "correct_authoritative_sha256": CORRECT_SHA,
        "incorrect_transcribed_sha256": INCORRECT_SHA,
        "runtime_launcher_uses_correct_sha": True,
        "runtime_scientific_path_affected": False,
        "diagnostic_v1_1": "ELIGIBLE_NOT_STARTED",
        "attempt_consumed": False,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
