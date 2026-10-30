#!/usr/bin/env python3
"""
WO#19A  -  D93/D94 TERMINAL-HISTORY RECONCILIATION  (STATIC / ADDITIVE /
GOVERNANCE ONLY / NON-CONSUMING).

This builder:
  * performs NO scientific execution, NO model load, NO checkpoint deserialization,
    NO VAL_GT read, NO VAL image read, NO TEST read, NO ROUTER_HOLDOUT read,
    NO validator rerun, NO v1.19/v1.20 execution, NO source/launcher/supervisor edit.
  * READS frozen authorities and re-verifies their raw-byte SHA-256 (FAIL-CLOSED);
    it never writes to them and never touches the canonical terminal artifact.
  * writes TWO new additive artifacts with write-once semantics
    (O_CREAT|O_EXCL|O_WRONLY{+O_BINARY} + full-write loop + os.fsync + st_size check):
        - reports/audits/phase36_v1_19_terminal_history_disclosure_v1_0.json
        - reports/audits/phase36_v1_19_terminal_success_state_reconciliation_v1_0.json
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
from datetime import datetime, timezone

REPO = pathlib.Path(__file__).resolve().parents[2]

CANONICAL_TERMINAL = REPO / "reports/audits/phase36_v1_19_terminal_success_state.json"
V1_18_ADJUDICATION = REPO / "reports/audits/phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json"
SUPERSEDED_TERMINAL = REPO / "reports/audits/_v1_19_terminal_superseded_v1/phase36_v1_19_terminal_success_state.json"

OUT_DISCLOSURE = REPO / "reports/audits/phase36_v1_19_terminal_history_disclosure_v1_0.json"
OUT_RECON = REPO / "reports/audits/phase36_v1_19_terminal_success_state_reconciliation_v1_0.json"

# ---------------------------------------------------------------------------
# Frozen authorities that MUST verify byte-for-byte before we emit anything.
# ---------------------------------------------------------------------------
FROZEN: dict[str, str] = {
    "reports/audits/phase36_v1_19_terminal_success_state.json":
        "7eba2b45c619973c29bdca99f50eb94d9ab01497c66011d058c0110db08cc1a0",
    "reports/audits/phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json":
        "41c6d79790f302e0863b0646b659729594cdc15834b3697169d5503907d809f9",
    "scripts/analysis/phase36_robustness_execution_v1_19.py":
        "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd",
    "scripts/analysis/launch_phase36_v1_19.py":
        "c2b81f8d7d65dc44fba6ee58ba74ea59815d46c415a052ea4aff86005167c9c5",
    "scripts/analysis/supervise_phase36_v1_19.py":
        "8a33c6facbef13a7792fc0de968ec06257cb591890c13204aaad3d337e1d8cf4",
    "reports/audits/phase36_v1_19_runtime_source_integrity_manifest.json":
        "06f7d0368b1f1f7e02ca950fe54c375d8d2d7e0f97800c8318d4451f408a1301",
    "reports/audits/phase36_v1_19_prelaunch_authority_bundle.json":
        "9d14991f0a7fa979484246e70868ed23ac41663c1ba2a27ee08c075a7f2bacd3",
    "reports/audits/phase36_v1_19_launch_authority_sha.json":
        "d44a91a683233972439ccce4f40e70cf10a28f354cbee1d6876af31b3027b2e9",
    "reports/audits/phase36_v1_19_science_release_attestation.json":
        "c3f5068f51693c8441965255d55821c35e583c6d60d9ab5cbbbe5c43ed476b0e",
    # frozen v1.15/v1.16/v1.17 history authorities (READ-ONLY evidence for D93)
    "reports/audits/phase36_science_eligibility_v1_15.json": None,   # hashed below
    "reports/audits/phase36_v1_15_no_scientific_execution_audit.json": None,
    "reports/audits/phase36_science_eligibility_v1_16.json": None,
    "reports/audits/phase36_v1_16_no_scientific_execution_audit.json": None,
    "reports/audits/phase36_science_eligibility_v1_17.json": None,
    "reports/audits/phase36_v1_17_no_scientific_execution_audit.json": None,
}

D93_EVIDENCE_PATHS = [
    "reports/audits/phase36_science_eligibility_v1_15.json",
    "reports/audits/phase36_v1_15_no_scientific_execution_audit.json",
    "reports/audits/phase36_science_eligibility_v1_16.json",
    "reports/audits/phase36_v1_16_no_scientific_execution_audit.json",
    "reports/audits/phase36_science_eligibility_v1_17.json",
    "reports/audits/phase36_v1_17_no_scientific_execution_audit.json",
]

V1_19_ABSENCE_PATHS = {
    "START": "reports/audits/phase36_robustness_science_start_v1_19.json",
    "RESULT": "reports/audits/phase36_robustness_scientific_result_v1_19.json",
    "FAILURE": "reports/audits/phase36_robustness_science_failure_v1_19.json",
    "PROCESS_EXIT": "reports/audits/phase36_robustness_science_process_exit_v1_19.json",
    "stdout": "reports/audits/phase36_robustness_science_stdout_v1_19.txt",
    "stderr": "reports/audits/phase36_robustness_science_stderr_v1_19.txt",
}
V1_19_JOURNAL_DIR = REPO / "reports/audits/phase36_robustness_science_v1_19_journal"


def sha256_file(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_frozen() -> tuple[dict[str, str], dict[str, str]]:
    """FAIL-CLOSED: any pinned-authority SHA mismatch aborts the build.

    Returns (pinned_verified, d93_evidence_hashes)."""
    pinned: dict[str, str] = {}
    for rel, expect in FROZEN.items():
        p = REPO / rel
        if not p.exists():
            sys.stderr.write(f"FATAL: frozen authority MISSING: {rel}\n")
            raise SystemExit(2)
        got = sha256_file(p)
        if expect is not None:
            if got != expect:
                sys.stderr.write(
                    f"FATAL: frozen authority SHA mismatch: {rel}\n"
                    f"  expected {expect}\n  observed {got}\n"
                )
                raise SystemExit(2)
            pinned[rel] = got
    d93 = {rel: sha256_file(REPO / rel) for rel in D93_EVIDENCE_PATHS}
    return pinned, d93


def write_once(path: pathlib.Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        mv = memoryview(payload)
        off = 0
        while off < len(payload):
            off += os.write(fd, mv[off:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(payload):
        sys.stderr.write("FATAL: post-write size check failed\n")
        raise SystemExit(3)


def main() -> int:
    # refuse to clobber (write-once) --------------------------------------------------
    for out in (OUT_DISCLOSURE, OUT_RECON):
        if out.exists():
            sys.stderr.write(f"REFUSE_OVERWRITE: {out} already exists (write-once)\n")
            return 1

    pinned, d93_ev = verify_frozen()

    canonical_sha = pinned["reports/audits/phase36_v1_19_terminal_success_state.json"]
    canonical_bytes = CANONICAL_TERMINAL.read_bytes()
    canonical_size = len(canonical_bytes)
    canonical_json = json.loads(canonical_bytes)

    # ---- D93: reconcile exact historical facts from frozen evidence ----
    elig_15 = json.loads((REPO / D93_EVIDENCE_PATHS[0]).read_text())
    nose_15 = json.loads((REPO / D93_EVIDENCE_PATHS[1]).read_text())
    elig_16 = json.loads((REPO / D93_EVIDENCE_PATHS[2]).read_text())
    nose_16 = json.loads((REPO / D93_EVIDENCE_PATHS[3]).read_text())
    elig_17 = json.loads((REPO / D93_EVIDENCE_PATHS[4]).read_text())
    nose_17 = json.loads((REPO / D93_EVIDENCE_PATHS[5]).read_text())

    v1_15_src = REPO / "scripts/analysis/phase36_robustness_execution_v1_15.py"
    v1_15_src_present = v1_15_src.exists()

    # ---- D94: durably recover the superseded terminal draft ----
    if SUPERSEDED_TERMINAL.exists():
        st = SUPERSEDED_TERMINAL.stat()
        d94 = {
            "durably_recovered": True,
            "superseded_path":
                "_v1_19_terminal_superseded_v1/phase36_v1_19_terminal_success_state.json",
            "superseded_path_full":
                "reports/audits/_v1_19_terminal_superseded_v1/"
                "phase36_v1_19_terminal_success_state.json",
            "raw_sha256": sha256_file(SUPERSEDED_TERMINAL),
            "size": st.st_size,
            "mtime_local": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%dT%H:%M:%S%z"),
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "mtime_epoch": st.st_mtime,
            "recovery_method": "DIRECT_STAT_OF_PRESERVED_SUPERSEDED_FILE",
        }
    else:
        d94 = {
            "durably_recovered": False,
            "superseded_path": None,
            "raw_sha256": None,
            "size": None,
            "mtime_local": None,
            "mtime_utc": None,
            "recovery_method": "NOT_DURABLY_RECOVERED",
        }

    # ---- v1.19 attempt absence (READ ONLY; no validator executed) ----
    absence = {}
    for label, rel in V1_19_ABSENCE_PATHS.items():
        absence[label] = (REPO / rel).exists()
    journal_records = (
        len(list(V1_19_JOURNAL_DIR.glob("*"))) if V1_19_JOURNAL_DIR.exists() else 0
    )

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # =====================================================================
    # Artifact 1 — ADDITIVE DISCLOSURE
    # =====================================================================
    disclosure = {
        "artifact": "phase36_v1_19_terminal_history_disclosure",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_19",
        "type": "TERMINAL_HISTORY_DISCLOSURE",
        "work_order": "WO#19A",
        "section": "\u00a72 D93 + \u00a73 D94",
        "mode": "STATIC_ADDITIVE_GOVERNANCE_ONLY_NON_CONSUMING",
        "generated_utc": now,

        "bindings": {
            "canonical_terminal_artifact": {
                "path": "reports/audits/phase36_v1_19_terminal_success_state.json",
                "sha256": canonical_sha,
                "size": canonical_size,
                "modified_by_this_artifact": False,
            },
            "v1_18_consumed_adjudication": {
                "path": "reports/audits/phase36_v1_18_consumed_prestart_failure_adjudication_v1_0.json",
                "sha256":
                    "41c6d79790f302e0863b0646b659729594cdc15834b3697169d5503907d809f9",
                "modified_by_this_artifact": False,
            },
            "v1_19_execution": {
                "path": "scripts/analysis/phase36_robustness_execution_v1_19.py",
                "sha256":
                    "3ec5ea920af2b6d66864b3bbc7e5362f0756777512c29be70d3e5453e18693cd",
            },
            "v1_19_launcher": {
                "path": "scripts/analysis/launch_phase36_v1_19.py",
                "sha256":
                    "c2b81f8d7d65dc44fba6ee58ba74ea59815d46c415a052ea4aff86005167c9c5",
            },
            "v1_19_supervisor": {
                "path": "scripts/analysis/supervise_phase36_v1_19.py",
                "sha256":
                    "8a33c6facbef13a7792fc0de968ec06257cb591890c13204aaad3d337e1d8cf4",
            },
        },
        "frozen_authorities_all_match": True,
        "frozen_authorities_verified": pinned,

        "D93": {
            "defect_id": "D93",
            "defect_code":
                "V1_19_TERMINAL_SUCCESS_STATE_MISCLASSIFIES_V1_15_V1_16_V1_17_HISTORY",
            "status": "DISCLOSED_AND_RECONCILED",
            "root_cause_established": True,
            "root_cause_statement": (
                "The frozen v1.19 terminal artifact's `revisions` block carried "
                "placeholder/incorrect historical labels for v1.15 (NOT_CREATED), "
                "v1.16 (CONSUMED_RESULT) and v1.17 (CONSUMED_RESULT). Frozen evidence "
                "shows none of these revisions ever consumed a scientific attempt; "
                "v1.15's source/revision EXISTED and all three were eligible-not-started."
            ),
            "frozen_artifact_stated_labels": {
                "v1_15": canonical_json["revisions"]["v1_15"]["state"],
                "v1_16": canonical_json["revisions"]["v1_16"]["state"],
                "v1_17": canonical_json["revisions"]["v1_17"]["state"],
            },
            "corrected_history": {
                "v1_15": {
                    "source_or_revision_existed": True,
                    "source_path": "scripts/analysis/phase36_robustness_execution_v1_15.py",
                    "science_eligibility_artifact":
                        "reports/audits/phase36_science_eligibility_v1_15.json",
                    "scientific_execution": False,
                    "scientific_attempt_consumed": False,
                    "attempt_state_from_frozen_evidence": elig_15.get("attempt_state"),
                    "execution_source_sha256": elig_15.get("execution_source_sha256"),
                    "existing_frozen_state_label": None,
                    "note": (
                        "No stronger frozen state label supplied; explicit booleans used. "
                        "`NOT_CREATED` (as stated in the frozen terminal artifact) is FALSE."
                    ),
                },
                "v1_16": {
                    "source_or_revision_existed": True,
                    "scientific_execution": False,
                    "scientific_attempt_consumed": False,
                    "state_from_frozen_evidence": elig_16.get("state"),
                    "existing_frozen_state_label": elig_16.get("state"),
                    "no_scientific_execution_audit_sha256": d93_ev[D93_EVIDENCE_PATHS[3]],
                    "note": "`CONSUMED_RESULT` (as stated) is FALSE.",
                },
                "v1_17": {
                    "source_or_revision_existed": True,
                    "scientific_execution": False,
                    "scientific_output": False,
                    "scientific_attempt_consumed": False,
                    "state": elig_17.get("state"),
                    "existing_frozen_state_label": elig_17.get("state"),
                    "no_scientific_execution_audit_sha256": d93_ev[D93_EVIDENCE_PATHS[5]],
                    "note": "`CONSUMED_RESULT` (as stated) is FALSE.",
                },
            },
            "frozen_evidence": {
                "phase36_science_eligibility_v1_15.json": {
                    "sha256": d93_ev[D93_EVIDENCE_PATHS[0]],
                    "attempt_state": elig_15.get("attempt_state"),
                    "attempt_consumed": elig_15.get("attempt_consumed"),
                },
                "phase36_v1_15_no_scientific_execution_audit.json": {
                    "sha256": d93_ev[D93_EVIDENCE_PATHS[1]],
                    "v1_15_execution_performed": nose_15.get("v1_15_execution_performed"),
                    "model_inference_performed": nose_15.get("model_inference_performed"),
                },
                "phase36_science_eligibility_v1_16.json": {
                    "sha256": d93_ev[D93_EVIDENCE_PATHS[2]],
                    "state": elig_16.get("state"),
                    "v1_16_attempt_consumed": elig_16.get("v1_16_attempt_consumed"),
                },
                "phase36_v1_16_no_scientific_execution_audit.json": {
                    "sha256": d93_ev[D93_EVIDENCE_PATHS[3]],
                    "scientific_execution": nose_16.get("scientific_execution"),
                    "scientific_output": nose_16.get("scientific_output"),
                },
                "phase36_science_eligibility_v1_17.json": {
                    "sha256": d93_ev[D93_EVIDENCE_PATHS[4]],
                    "state": elig_17.get("state"),
                    "v1_17_attempt_consumed": elig_17.get("v1_17_attempt_consumed"),
                },
                "phase36_v1_17_no_scientific_execution_audit.json": {
                    "sha256": d93_ev[D93_EVIDENCE_PATHS[5]],
                    "scientific_execution": nose_17.get("scientific_execution"),
                    "scientific_output": nose_17.get("scientific_output"),
                },
            },
            "scientific_semantics_effect": "NONE",
            "runtime_semantics_effect": "NONE",
            "v1_19_runtime_family_effect": "NONE",
            "governance_history_accuracy_effect": "YES",
        },

        "D94": {
            "defect_id": "D94",
            "defect_code":
                "V1_19_TERMINAL_SUCCESS_STATE_CANONICAL_PATH_REEMITTED_AFTER_SUPERSESSION",
            "status": "DISCLOSED_AND_RECONCILED",
            "root_cause_established": d94["durably_recovered"],
            "root_cause_statement": (
                "During WO#19 the canonical terminal-state path was emitted twice: an "
                "initial draft was written, then MOVED into a superseded directory and "
                "the canonical path re-emitted. The preserved superseded copy is "
                "enumerated below; the current canonical artifact is NOT rewritten or "
                "moved by WO#19A."
            ),
            "superseded_draft": d94,
            "current_canonical_path":
                "reports/audits/phase36_v1_19_terminal_success_state.json",
            "current_canonical_sha256": canonical_sha,
            "current_canonical_rewritten_now": False,
            "scientific_semantics_effect": "NONE",
            "runtime_semantics_effect": "NONE",
            "current_final_bytes_effect": "NONE",
            "governance_provenance_effect": "YES",
        },

        "v1_19_attempt_absence": {
            "START_absent": not absence["START"],
            "RESULT_absent": not absence["RESULT"],
            "FAILURE_absent": not absence["FAILURE"],
            "PROCESS_EXIT_absent": not absence["PROCESS_EXIT"],
            "stdout_absent": not absence["stdout"],
            "stderr_absent": not absence["stderr"],
            "journal_records": journal_records,
            "established_by": "READ_ONLY_PATH_EXISTENCE_CHECK__NO_VALIDATOR_EXECUTED",
        },

        "write_semantics":
            "O_CREAT|O_EXCL|O_WRONLY + O_BINARY (Windows) + full-write loop + "
            "os.fsync + post-write st_size check. Write-once; never overwritten.",
        "provenance": {
            "derived_from": "frozen authorities on disk (read-only)",
            "val_gt_read": False,
            "val_image_read": False,
            "checkpoint_deserialization": False,
            "test_reads": 0,
            "router_holdout_reads": 0,
            "model_loaded": False,
            "validator_rerun": False,
            "new_scientific_output": False,
        },
        "terminal": "PHASE36_V1_19_D93_D94_DISCLOSURE_WRITTEN",
    }

    # =====================================================================
    # Artifact 2 — ADDITIVE TERMINAL RECONCILIATION
    # (corrects ONLY the historical revision-state fields; preserves everything else)
    # =====================================================================
    reconciliation = {
        "artifact": "phase36_v1_19_terminal_success_state_reconciliation",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_19",
        "type": "TERMINAL_SUCCESS_STATE_RECONCILIATION",
        "work_order": "WO#19A",
        "section": "\u00a75",
        "mode": "STATIC_ADDITIVE_GOVERNANCE_ONLY_NON_CONSUMING",
        "generated_utc": now,

        "amends": "reports/audits/phase36_v1_19_terminal_success_state.json",
        "amended_artifact_sha256": canonical_sha,
        "amended_artifact_size": canonical_size,
        "amended_artifact_modified_by_this_artifact": False,
        "supersedes": None,
        "amendment_kind": "HISTORICAL_REVISION_STATE_CORRECTION_ONLY",

        "preserved_unchanged": {
            "v1_18": "CONSUMED_PRE_START_RUNTIME_FAILURE",
            "v1_19": "ELIGIBLE_NOT_STARTED",
            "phase36": "NOT_COMPLETE_PENDING_V1_19_EXECUTION",
            "phase37": "NOT_STARTED",
            "D92": "REPAIRED",
            "v1_18_to_v1_19_scientific_delta_count": 0,
            "v1_14_to_v1_19_scientific_delta_count": 2,
            "scientific_delta_classes": ["D61", "D75"],
            "unclassified_scientific_delta_count": 0,
            "TEST_accessed": False,
            "ROUTER_HOLDOUT_accessed": False,
        },

        "corrected_revision_states": {
            "v1_14": {
                "as_stated_in_amended_artifact": canonical_json["revisions"]["v1_14"]["state"],
                "corrected_state": canonical_json["revisions"]["v1_14"]["state"],
                "correction_applied": False,
                "agrees_with_frozen_evidence": True,
            },
            "v1_15": {
                "as_stated_in_amended_artifact": "NOT_CREATED",
                "corrected_state": None,
                "corrected_booleans": {
                    "source_or_revision_existed": True,
                    "scientific_execution": False,
                    "scientific_attempt_consumed": False,
                },
                "correction_applied": True,
                "superseded_label_was_incorrect": True,
                "justification": "prefer explicit booleans; no stronger frozen label supplied",
            },
            "v1_16": {
                "as_stated_in_amended_artifact": "CONSUMED_RESULT",
                "corrected_state": elig_16.get("state"),
                "corrected_booleans": {
                    "scientific_execution": False,
                    "scientific_attempt_consumed": False,
                },
                "correction_applied": True,
                "superseded_label_was_incorrect": True,
            },
            "v1_17": {
                "as_stated_in_amended_artifact": "CONSUMED_RESULT",
                "corrected_state": elig_17.get("state"),
                "corrected_booleans": {
                    "scientific_execution": False,
                    "scientific_output": False,
                    "scientific_attempt_consumed": False,
                },
                "correction_applied": True,
                "superseded_label_was_incorrect": True,
            },
            "v1_18": {
                "as_stated_in_amended_artifact":
                    canonical_json["revisions"]["v1_18"]["state"],
                "corrected_state": canonical_json["revisions"]["v1_18"]["state"],
                "correction_applied": False,
                "agrees_with_frozen_evidence": True,
            },
            "v1_19": {
                "as_stated_in_amended_artifact":
                    canonical_json["revisions"]["v1_19"]["state"],
                "corrected_state": canonical_json["revisions"]["v1_19"]["state"],
                "correction_applied": False,
                "agrees_with_frozen_evidence": True,
            },
        },

        "historical_revision_state_corrections": {
            "v1_15": {
                "superseded_label": "NOT_CREATED",
                "corrected_booleans": {
                    "source_or_revision_existed": True,
                    "scientific_execution": False,
                    "scientific_attempt_consumed": False,
                },
            },
            "v1_16": {
                "superseded_label": "CONSUMED_RESULT",
                "corrected_state": elig_16.get("state"),
                "corrected_booleans": {
                    "scientific_execution": False,
                    "scientific_attempt_consumed": False,
                },
            },
            "v1_17": {
                "superseded_label": "CONSUMED_RESULT",
                "corrected_state": elig_17.get("state"),
                "corrected_booleans": {
                    "scientific_execution": False,
                    "scientific_output": False,
                    "scientific_attempt_consumed": False,
                },
            },
        },

        "D93_status": "DISCLOSED_AND_RECONCILED",
        "D94_status": "DISCLOSED_AND_RECONCILED",
        "disclosure_artifact":
            "reports/audits/phase36_v1_19_terminal_history_disclosure_v1_0.json",

        "scientific_semantics_effect": "NONE",
        "runtime_semantics_effect": "NONE",
        "v1_19_runtime_family_effect": "NONE",

        "write_semantics":
            "O_CREAT|O_EXCL|O_WRONLY + O_BINARY (Windows) + full-write loop + "
            "os.fsync + post-write st_size check. Write-once; never overwritten.",
        "provenance": {
            "derived_from": "frozen authorities on disk (read-only)",
            "val_gt_read": False,
            "val_image_read": False,
            "checkpoint_deserialization": False,
            "test_reads": 0,
            "router_holdout_reads": 0,
            "model_loaded": False,
            "validator_rerun": False,
            "new_scientific_output": False,
        },
        "terminal": "PHASE36_V1_19_TERMINAL_SUCCESS_STATE_RECONCILIATION_WRITTEN",
    }

    write_once(OUT_DISCLOSURE,
               (json.dumps(disclosure, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))
    write_once(OUT_RECON,
               (json.dumps(reconciliation, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))

    for out in (OUT_DISCLOSURE, OUT_RECON):
        print(f"WROTE {out}")
        print(f"SHA256 {sha256_file(out)}")
        print(f"SIZE {out.stat().st_size}")
    print("D93 DISCLOSED_AND_RECONCILED")
    print("D94 DISCLOSED_AND_RECONCILED")
    print("TERMINAL PHASE36_V1_19_D93_D94_ADDITIVE_RECONCILIATION_COMPLETE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
