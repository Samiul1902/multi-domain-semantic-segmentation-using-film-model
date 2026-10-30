"""Builder: Phase36 v1.4 result-adjudication RECONCILIATION WRITE-HISTORY DISCLOSURE v1.0 (D79).

STATIC / GOVERNANCE-ONLY / NON-CONSUMING.

Additive provenance disclosure for the D76/D77/D78 reconciliation build history.
The final reconciliation content is substantively accepted, but its PATH was not
historically write-once from first creation: an earlier artifact was written, its
builder was modified, the artifact was deleted, and the same output path was
recreated with the updated builder.

This builder NEVER modifies the final reconciliation or final builder.  It re-hashes
all ancestors, attempts a durable first-write recovery (from static evidence only;
no recreation), and writes ONE write-once disclosure at a NEW path.

Fail-closed: if any required ancestor check fails, it aborts (nonzero, NO artifact).
Prohibitions: NO model execution / checkpoint load / VAL image / VAL GT / TEST /
ROUTER_HOLDOUT / perturbation / metric / v1.4 retry / v1.15 / Phase37.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

AUDIT_DIR = ROOT / "reports" / "audits"
OUT_PATH = (
    AUDIT_DIR
    / "phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_write_history_v1_0.json"
)
MEMORY_DIR = ROOT / ".workbuddy-ai" / "memory"

FROZEN_V1_0_ADJ = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.json",
    "912cb24e4b27dcc7d66310b36db2154180411ec52d79d19c767aa708220b9b36",
)
FROZEN_V1_0_BLD = (
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_v1_0.py",
    "8c95a6f6c3d9f3735169256d9c6f06bd538ed5ebbba8afb8a96ed72b2e81baf7",
)
CURRENT_RECON = (
    "reports/audits/phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.json",
    "7f0957695939a03feca7d9909c47f56e6644a4f3b800664c9bb61f02486dbd9b",
)
CURRENT_RECON_BLD = (
    "scripts/analysis/build_phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.py",
    "4788f7eb758f4927582a7fb5f6f3b623ba4192b8f5e3515b3025d70505c59ee7",
)
CURRENT_TEST = (
    "scripts/analysis/test_phase36_final_probability_authority_diagnostic_v1_4_result_adjudication_reconciliation_v1_1.py",
    "ee9742f43a979cddb0d82dcc0a0e3b1bb31a2277625c3c4bb869dbd7f810536d",
)
ATTEMPT_ARTIFACTS = {
    "START": (
        "reports/audits/phase36_final_probability_authority_diagnostic_start_v1_4.json",
        "298f56414eaa39281e8dfaf33faa5e1260d6e7708ae5bfe5f850bcf04520caca",
    ),
    "RESULT": (
        "reports/audits/phase36_final_probability_authority_diagnostic_result_v1_4.json",
        "046a1e3c3053fb00b97895d8d1834d0011f8b190209daa01795e6915b7fd5284",
    ),
    "PROCESS_EXIT": (
        "reports/audits/phase36_final_probability_authority_diagnostic_process_exit_v1_4.json",
        "7475ce8c8a6abfc7f8697a1682ec3a93f22178503bb342ef52569175ca8061e2",
    ),
    "STDOUT": (
        "reports/audits/phase36_final_probability_authority_diagnostic_stdout_v1_4.txt",
        "822adf6b61ff8b4cdec307d5d755cb83b3cc583dcf2de4dd94f3fb9be548b393",
    ),
    "STDERR": (
        "reports/audits/phase36_final_probability_authority_diagnostic_stderr_v1_4.txt",
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    ),
}
FAILURE_REL = "reports/audits/phase36_final_probability_authority_diagnostic_failure_v1_4.json"

# Known abbreviated first-write prefixes (operator-observed; NOT expanded by guessing).
FIRST_WRITE_RECON_PREFIX = "3af908c8"
FIRST_WRITE_BUILDER_PREFIX = "eb2e6400"
FIRST_WRITE_RECON_PREFIX_LEN = 8
FIRST_WRITE_BUILDER_PREFIX_LEN = 8

# Static evidence sources searched for durable first-write hashes.
FIRST_WRITE_SEARCH_SOURCES = [
    ".workbuddy-ai/memory/2026-10-10.md",
    ".workbuddy-ai/memory/MEMORY.md",
    ".workbuddy-ai/memory/NOTES_ARCHIVE.md",
]
# Terminal transcripts / shell history are transient and not durably present.
FIRST_WRITE_SEARCH_INCONCLUSIVE = [
    "terminal_transcripts:not_durably_present",
    "shell_history:not_durably_present",
    "git_reflog:single_initial_commit_path_untracked",
]


def sha256_file(p: Path) -> str | None:
    if not p.exists():
        return None
    return hashlib.sha256(p.read_bytes()).hexdigest()


def check(rel: str, exp: str) -> dict:
    actual = sha256_file(ROOT / rel)
    return {"path": rel, "sha256_expected": exp, "sha256_actual": actual, "match": actual == exp}


def search_durable_first_write() -> dict:
    """Search ONLY static evidence for the full first-write hashes (no recreation)."""
    found_recon = False
    found_builder = False
    searched = []
    for rel in FIRST_WRITE_SEARCH_SOURCES:
        p = ROOT / rel
        if not p.exists():
            searched.append({"path": rel, "present": False})
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        has_r = FIRST_WRITE_RECON_PREFIX in text
        has_b = FIRST_WRITE_BUILDER_PREFIX in text
        found_recon = found_recon or has_r
        found_builder = found_builder or has_b
        searched.append(
            {
                "path": rel,
                "present": True,
                "contains_recon_prefix": has_r,
                "contains_builder_prefix": has_b,
            }
        )
    return {
        "searched_sources": searched,
        "inconclusive_sources": FIRST_WRITE_SEARCH_INCONCLUSIVE,
        "full_reconciliation_hash_found": found_recon,
        "full_builder_hash_found": found_builder,
    }


def write_once(path: Path, payload: bytes) -> None:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags)
    try:
        written = 0
        while written < len(payload):
            n = os.write(fd, payload[written:])
            if n <= 0:
                raise IOError("short write")
            written += n
        os.fsync(fd)
    finally:
        os.close(fd)
    st = os.stat(str(path))
    if st.st_size != len(payload):
        raise IOError(f"post-write size mismatch {st.st_size} != {len(payload)}")


def main() -> int:
    if OUT_PATH.exists():
        print(f"REFUSE_OVERWRITE: {OUT_PATH} already exists")
        print("STOP: do NOT delete/recreate. Create a new additive revision instead.")
        return 2

    # ---- Section 8: ancestor verification (fail-closed) ----------------- #
    checks = {
        "frozen_v1_0_adjudication_exact": check(*FROZEN_V1_0_ADJ)["match"],
        "frozen_v1_0_builder_exact": check(*FROZEN_V1_0_BLD)["match"],
        "current_reconciliation_exact": check(*CURRENT_RECON)["match"],
        "current_reconciliation_builder_exact": check(*CURRENT_RECON_BLD)["match"],
        "current_validation_test_exact": check(*CURRENT_TEST)["match"],
    }
    att = {k: check(*v) for k, v in ATTEMPT_ARTIFACTS.items()}
    for k, v in att.items():
        checks[f"attempt_{k}_exact"] = v["match"]
    checks["FAILURE_absent"] = not (ROOT / FAILURE_REL).exists()

    if not all(checks.values()):
        print("FAIL_CLOSED: one or more required ancestor checks failed; NO artifact written.")
        for k, v in checks.items():
            if not v:
                print(f"  FAILED_CHECK {k}")
        return 3

    # ---- Section 3: verify accepted conclusions (read-only) ------------- #
    recon = json.loads((ROOT / CURRENT_RECON[0]).read_text(encoding="utf-8"))
    builder_sha_on_disk = sha256_file(ROOT / CURRENT_RECON_BLD[0])
    pair_self_consistent = recon.get("builder_source_sha256") == builder_sha_on_disk
    fg = recon.get("fail_closed_gate", {})
    gate_pass = (
        fg.get("all_required_checks_pass") is True
        and fg.get("n_checks") == 22
        and fg.get("n_checks_pass") == 22
    )
    accepted = {
        "D61": recon.get("D61"),
        "D75": recon.get("D75"),
        "D76_status": recon.get("D76_status"),
        "D77_status": recon.get("D77_status"),
        "D78": recon.get("D78"),
        "v1_15_repair_policy": recon.get("v1_15_repair_policy"),
        "phase27_historical_scored_representation": recon.get("phase27_historical_scored_representation"),
        "v1_14_clean_scored_representation": recon.get("v1_14_clean_scored_representation"),
        "journal_result_snapshot_records": recon.get("journal_result_snapshot_records"),
        "journal_final_on_disk_records": recon.get("journal_final_on_disk_records"),
    }
    accepted_ok = (
        accepted["D61"] == "PRESERVED"
        and accepted["D75"] == "PRESERVED"
        and accepted["D76_status"] == "RECONCILED"
        and accepted["D77_status"] == "RECONCILED"
        and accepted["D78"] == "D75_SCORING_SOURCE_PROVENANCE_BOUND"
        and accepted["v1_15_repair_policy"] == "POLICY_B"
        and accepted["phase27_historical_scored_representation"] == "PERSISTED_F16__RECAST_F32__THRESHOLD_0_50"
        and accepted["v1_14_clean_scored_representation"] == "LIVE_F32__THRESHOLD_0_50"
        and accepted["journal_result_snapshot_records"] == 29
        and accepted["journal_final_on_disk_records"] == 31
        and pair_self_consistent
        and gate_pass
    )
    if not accepted_ok:
        print("FAIL_CLOSED: accepted conclusions not verified; NO artifact written.")
        return 3

    # ---- Section 5: first-write recovery attempt ------------------------ #
    rec = search_durable_first_write()
    first_recon = "NOT_DURABLY_RECOVERED"
    first_builder = "NOT_DURABLY_RECOVERED"

    payload = {
        "artifact_kind": (
            "PHASE36_FINAL_PROBABILITY_AUTHORITY_DIAGNOSTIC_V1_4_RESULT_ADJUDICATION_"
            "RECONCILIATION_WRITE_HISTORY_DISCLOSURE"
        ),
        "revision": "v1.0",
        "decision_id": "D79",
        "purpose": (
            "Additive provenance disclosure for the D76/D77/D78 reconciliation build "
            "history, which was not historically write-once from its first successful "
            "creation. STATIC / governance-only / non-consuming."
        ),
        "execution_scope": "STATIC_GOVERNANCE_ONLY_NON_CONSUMING",

        # ---- Section 4: D79 --------------------------------------------- #
        "D79": "D76_D77_D78_RECONCILIATION_WRITE_ONCE_HISTORY_VIOLATED_DURING_REBUILD",
        "D79_status": "DISCLOSED_AND_RECONCILED",
        "scientific_semantics_effect": "NONE",
        "current_final_reconciliation_content_effect": "NONE",
        "current_builder_content_effect": "NONE",
        "governance_provenance_effect": "YES",
        "D79_reason": (
            "The same intended write-once output path was successfully created once, then "
            "deleted and recreated after the builder changed.  The final artifact is "
            "internally coherent and independently hash-bound, but its path history was "
            "not strictly first-write immutable."
        ),
        "D79_sequence": [
            "1. an earlier reconciliation artifact was successfully written",
            "2. its builder was subsequently modified",
            "3. the already-written reconciliation artifact was deleted",
            "4. the same output path was recreated using the updated builder",
        ],

        # ---- Section 5: first-write recovery ---------------------------- #
        "first_write_recovery": {
            "attempted": True,
            "method": "STATIC_EVIDENCE_SEARCH_ONLY (no recreation)",
            "searched_sources": rec["searched_sources"],
            "inconclusive_sources": rec["inconclusive_sources"],
            "full_reconciliation_hash_found": rec["full_reconciliation_hash_found"],
            "full_builder_hash_found": rec["full_builder_hash_found"],
        },
        "first_written_reconciliation_sha256": first_recon,
        "first_generator_builder_sha256": first_builder,
        "first_written_reconciliation_sha256_prefix_known": FIRST_WRITE_RECON_PREFIX,
        "first_written_reconciliation_sha256_prefix_len": FIRST_WRITE_RECON_PREFIX_LEN,
        "first_generator_builder_sha256_prefix_known": FIRST_WRITE_BUILDER_PREFIX,
        "first_generator_builder_sha256_prefix_len": FIRST_WRITE_BUILDER_PREFIX_LEN,
        "first_write_timestamp": "NOT_DURABLY_RECOVERED",
        "first_write_hash_expanded_by_guessing": False,

        # ---- Section 6: final artifact status --------------------------- #
        "current_final_reconciliation_sha256": CURRENT_RECON[1],
        "current_final_builder_sha256": CURRENT_RECON_BLD[1],
        "current_final_test_sha256": CURRENT_TEST[1],
        "current_final_pair_self_consistent": pair_self_consistent,
        "current_final_reconciliation_records_builder_sha256_correctly": pair_self_consistent,
        "current_final_fail_closed_gate": "PASS" if gate_pass else "FAIL",
        "current_final_fail_closed_gate_detail": {
            "n_checks": fg.get("n_checks"),
            "n_checks_pass": fg.get("n_checks_pass"),
            "all_required_checks_pass": fg.get("all_required_checks_pass"),
        },
        "D76_D77_D78_substantive_conclusions_remain_valid": True,

        # ---- Section 3: preserved accepted conclusions ------------------ #
        "preserved_accepted_conclusions": accepted,
        "preserved_accepted_conclusions_ok": accepted_ok,

        # ---- Section 8: ancestor verification --------------------------- #
        "ancestor_verification": {
            "frozen_v1_0_adjudication": check(*FROZEN_V1_0_ADJ),
            "frozen_v1_0_builder": check(*FROZEN_V1_0_BLD),
            "current_reconciliation": check(*CURRENT_RECON),
            "current_reconciliation_builder": check(*CURRENT_RECON_BLD),
            "current_validation_test": check(*CURRENT_TEST),
            "attempt_artifacts": att,
            "FAILURE_absent": checks["FAILURE_absent"],
            "all_required_checks_pass": True,
            "no_ancestor_modified": True,
        },

        # ---- Section 9: required final state ---------------------------- #
        "final_state": {
            "D61": "PRESERVED",
            "D75": "PRESERVED",
            "D76": "RECONCILED",
            "D77": "RECONCILED",
            "D78": "RECONCILED",
            "D79": "DISCLOSED_AND_RECONCILED",
            "v1_15_repair_policy": "POLICY_B",
            "v1_4_retry_permitted": False,
            "v1_15_created": False,
            "v1_15_executed": False,
            "Phase36": "NOT_COMPLETE_PENDING_V1_15",
            "Phase37": "NOT_STARTED",
            "TEST_accessed": False,
            "ROUTER_HOLDOUT_accessed": False,
        },

        "prohibitions_observed": {
            "no_model_execution": True, "no_checkpoint_load": True,
            "no_val_image_read": True, "no_val_gt_read": True, "no_test": True,
            "no_router_holdout": True, "no_perturbation": True,
            "no_metric_execution": True, "no_v1_4_retry": True,
            "no_v1_15_implementation": True, "no_v1_15_execution": True,
            "no_phase37": True,
            "no_modification_of_final_reconciliation": True,
            "no_modification_of_final_builder": True,
            "no_recreation_of_first_write_artifact": True,
        },

        "builder_source_sha256": sha256_file(Path(__file__).resolve()),
        "write_semantics": "WRITE_ONCE_O_CREAT_O_EXCL_FSYNC_FAIL_CLOSED",
    }

    payload_bytes = (json.dumps(payload, indent=2, ensure_ascii=False) + "\n").encode("utf-8")

    if not all(checks.values()):
        print("FAIL_CLOSED_AT_WRITE: refusing to write")
        return 3

    write_once(OUT_PATH, payload_bytes)
    out_sha = sha256_file(OUT_PATH)

    print("DISCLOSURE_WRITTEN")
    print(f"path={OUT_PATH.relative_to(ROOT)}")
    print(f"bytes={len(payload_bytes)}")
    print(f"sha256={out_sha}")
    print(f"builder_sha256={payload['builder_source_sha256']}")
    print(f"D79={payload['D79']}")
    print(f"D79_status={payload['D79_status']}")
    print(f"first_written_reconciliation_sha256={first_recon}")
    print(f"first_generator_builder_sha256={first_builder}")
    print(f"current_final_pair_self_consistent={pair_self_consistent}")
    print(f"accepted_conclusions_ok={accepted_ok}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
