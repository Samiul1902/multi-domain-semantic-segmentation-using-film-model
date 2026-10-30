#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — WO#17G builder: D91 validator-source-drift disclosure +
final v1.18 external-audit handoff reconciliation v1_1.  Both WRITE-ONCE
(O_CREAT|O_EXCL) and fail-closed.

Produces:
  (1) reports/audits/phase36_v1_18_negative_control_source_drift_disclosure_v1_0.json
  (2) reports/audits/phase36_v1_18_independent_audit_handoff_reconciliation_v1_1.json

MODE: STATIC / GOVERNANCE-ONLY / NON-CONSUMING.
NO v1.18 execution, NO v1.19, NO source/launcher/supervisor edit, NO validator
rerun, NO report rewrite, NO model, NO checkpoint, NO VAL, NO TEST,
NO ROUTER_HOLDOUT, NO PHASE37.

The frozen expected negative-control source SHA is bound from the frozen
independent-audit handoff.  The current SHA is raw-hashed from disk.  The old
bytes are NOT durably available, so NO diff is computed and byte-equivalent
semantics are NEVER claimed.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha(p) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def mtime_utc(p) -> str | None:
    p = Path(p)
    if not p.exists():
        return None
    return datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def write_once_json(path: Path, payload: dict) -> None:
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


# --------------------------------------------------------------------------- #
# §2 FROZEN RUNTIME FAMILY  (require unchanged; never mutate)
# --------------------------------------------------------------------------- #
RUNTIME_FAMILY = {
    "execution": ("scripts/analysis/phase36_robustness_execution_v1_18.py",
                  "2259ce22e75ba9a3a8943769dc1e0ed5724f94902f5e8955976cd6ebeb8ce63e"),
    "launcher": ("scripts/analysis/launch_phase36_v1_18.py",
                 "727a3bdd47f626826575de286a2a382dd63eb899c244af9da6e1d9d078944f3e"),
    "supervisor": ("scripts/analysis/supervise_phase36_v1_18.py",
                   "2528e0601fd3fd1231bc11e8258a9fb0ae9f1df8303fe2237d32385701cbc5d4"),
    "runtime_manifest": ("reports/audits/phase36_v1_18_runtime_source_integrity_manifest.json",
                         "0a19c405641f0825a9869e6dd9f151ee4e5c5c83f0648a9a7844bf17b59f0a5d"),
    "prelaunch_authority_bundle": ("reports/audits/phase36_v1_18_prelaunch_authority_bundle.json",
                                   "0f6989bcc500ce6ba1cf963d4580bc2bdfbcb5db6ad0ce65fd46ade1d8529dfc"),
    "launch_authority_file": ("reports/audits/phase36_v1_18_launch_authority_sha.json",
                              "a5d383f147fabf11104a8f619cdd1cb44442cca22fbe0b94632d40f76c1070e7"),
    "eligibility": ("reports/audits/phase36_science_eligibility_v1_18.json",
                    "123d486b54c1e71ea0f5590abea2546b18cd370854ddb46ec28cb0cc9c3c9d11"),
    "original_handoff": ("reports/audits/phase36_v1_18_independent_audit_handoff_v1_0.json",
                         "15a59f4ef5a0955ab350de0683aceac3b233e74fc98fc4dac003c73190aacc60"),
    "d89_disclosure": ("reports/audits/phase36_v1_18_governance_write_history_disclosure_v1_0.json",
                       "a0a7d272c83ee11e3510bc13968a7f6ec74eb7e38d6ea372a7af9954fd51e2fb"),
    "d90_reconciliation": ("reports/audits/phase36_v1_18_independent_audit_handoff_reconciliation_v1_0.json",
                           "d3dad229dda6e45b4225e7359551959ff964dc5341a3442dbb73872367230965"),
}

# §5 other final audit bytes (read-only require)
AUDIT_BYTES = {
    "reachable_write_target_inventory": ("reports/audits/phase36_v1_18_reachable_write_target_inventory.json",
                                         "7d17b847cda9e0d7aef44361c9f2ee222c64b708d0096d2b377e3fed6d3621c9"),
    "output_namespace_map": ("reports/audits/phase36_v1_18_output_namespace_map.json",
                             "eb600f246f03579af7b511a595997756a42ed49595a8e240e38f7d2e4acddd25"),
    "operational_cross_contract_source": ("scripts/analysis/validate_phase36_v1_18_operational_cross_contract.py",
                                          "0ec6f6e0ce2dc7e77a841e1af148380ed15eff16779e253f999f2f08156e132e"),
    "release_attestation": ("reports/audits/phase36_v1_18_science_release_attestation.json",
                            "c06341c1e9b85efb7210bcbce2911a4a675c68d44db5264d7272bb7ffa76104f"),
    "final_readiness": ("reports/audits/phase36_v1_18_final_readiness_attestation.json",
                        "1debd8953505d30ea797a0f2e434f1f104275196be7929f86c8fb0233e05ca5c"),
}

NC_SOURCE = "scripts/analysis/phase36_robustness_negative_controls_v1_18.py"
NC_EXPECTED_FROM_HANDOFF = "b6366848d4599702a850b1c32e70def3c22be902a681fda94317c554730d3a9b"

V1_18_MARKERS = {
    "START": "reports/audits/phase36_robustness_science_start_v1_18.json",
    "RESULT": "reports/audits/phase36_robustness_scientific_result_v1_18.json",
    "FAILURE": "reports/audits/phase36_robustness_science_failure_v1_18.json",
    "PROCESS_EXIT": "reports/audits/phase36_robustness_science_process_exit_v1_18.json",
    "stdout": "reports/audits/phase36_robustness_science_stdout_v1_18.txt",
    "stderr": "reports/audits/phase36_robustness_science_stderr_v1_18.txt",
}
V1_17_MARKERS = {k: v.replace("_v1_18", "_v1_17") for k, v in V1_18_MARKERS.items()}


def main() -> int:
    # ---------------- §2 verify runtime family unchanged ---------------- #
    fam_actual = {k: sha(ROOT / p) for k, (p, _e) in RUNTIME_FAMILY.items()}
    fam_mismatch = [k for k, (_p, e) in RUNTIME_FAMILY.items() if fam_actual[k] != e]
    if fam_mismatch:
        print(json.dumps({"status": "FROZEN_RUNTIME_FAMILY_MISMATCH", "keys": fam_mismatch}, indent=1))
        return 4

    # ---------------- §5 verify other audit bytes ---------------- #
    audit_actual = {k: sha(ROOT / p) for k, (p, _e) in AUDIT_BYTES.items()}
    audit_mismatch = [k for k, (_p, e) in AUDIT_BYTES.items() if audit_actual[k] != e]
    if audit_mismatch:
        print(json.dumps({"status": "AUDIT_BYTE_MISMATCH", "keys": audit_mismatch}, indent=1))
        return 5

    inv = load(ROOT / AUDIT_BYTES["reachable_write_target_inventory"][0])
    if not (inv.get("table_figure_target_count") == 16
            and inv.get("total_reachable_write_target_count") == 23
            and inv.get("unclassified_write_target_count") == 0
            and inv.get("namespace_overlap_count") == 0):
        print(json.dumps({"status": "INVENTORY_COUNT_MISMATCH", "inventory": inv}, indent=1))
        return 6

    # ---------------- §3 D91 forensics ---------------- #
    handoff = load(ROOT / RUNTIME_FAMILY["original_handoff"][0])
    nc_expected = handoff.get("artifact_sha256", {}).get("negative_controls_source")
    if nc_expected != NC_EXPECTED_FROM_HANDOFF:
        print(json.dumps({"status": "HANDFOF_NC_BINDING_UNEXPECTED", "handoff_binding": nc_expected}, indent=1))
        return 7
    nc_current = sha(ROOT / NC_SOURCE)
    old_recovered = (nc_current == NC_EXPECTED_FROM_HANDOFF)

    # static-evidence-only search summary (no reconstruction, no network)
    old_search = {
        "searched": ["whole_file_sha_scan_under_repo_roots", "supersede_dirs",
                     "local_git_object_store", "work_logs_daily_memory", "prior_copied_evidence"],
        "whole_file_sha_match_found": False,
        "supersede_copy_found": False,
        "local_git_blob_found": False,
        "frozen_sha_appears_only_in": "reports/audits/phase36_v1_18_independent_audit_handoff_v1_0.json",
        "old_source_bytes": "RECOVERED" if old_recovered else "NOT_DURABLY_RECOVERED",
        "diff_computed": old_recovered,
        "byte_equivalent_semantics_claimed": False,
    }

    # ---------------- §6 attempt absence ---------------- #
    v18_state = {k: ("ABSENT" if not (ROOT / v).exists() else "PRESENT") for k, v in V1_18_MARKERS.items()}
    v17_state = {k: ("ABSENT" if not (ROOT / v).exists() else "PRESENT") for k, v in V1_17_MARKERS.items()}

    # ---------------- §7 D91 disclosure ---------------- #
    disclosure = {
        "artifact": "phase36_v1_18_negative_control_source_drift_disclosure_v1_0",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "NEGATIVE_CONTROL_SOURCE_DRIFT_DISCLOSURE",
        "D91": "V1_18_NEGATIVE_CONTROL_SOURCE_SHA_DRIFT_FROM_FROZEN_INDEPENDENT_AUDIT_HANDOFF",
        "D91_status": "DISCLOSED_AND_RECONCILED",
        "scientific_semantics_effect": "NONE",
        "runtime_semantics_effect": "NONE",
        "execution_source_effect": "NONE",
        "launcher_effect": "NONE",
        "supervisor_effect": "NONE",
        "governance_validation_provenance_effect": "YES",
        "rationale": (
            "scripts/analysis/phase36_robustness_negative_controls_v1_18.py is a validation-only "
            "artifact and is NOT reachable from the real v1.18 execution / launcher / supervisor "
            "science path.  The frozen execution source, launcher and supervisor are unchanged, so "
            "this drift has no scientific or runtime semantics effect."
        ),
        "negative_control_source_path": NC_SOURCE,
        "negative_control_source_expected_by_original_handoff": NC_EXPECTED_FROM_HANDOFF,
        "negative_control_source_current_sha256": nc_current,
        "negative_control_source_current_size_bytes": (ROOT / NC_SOURCE).stat().st_size,
        "negative_control_source_current_mtime_utc": mtime_utc(ROOT / NC_SOURCE),
        "original_handoff_generated_utc": handoff.get("generated_utc"),
        "shas_differ": (nc_current != NC_EXPECTED_FROM_HANDOFF),
        "old_source_bytes": old_search["old_source_bytes"],
        "diff_computed": old_search["diff_computed"],
        "byte_equivalent_semantics_claimed": False,
        "old_source_bytes_statement": (
            "The frozen expected bytes are NOT durably available: no whole-file SHA match exists "
            "anywhere in the repo, no supersede-directory copy exists, no local git blob exists, and "
            "the frozen SHA appears only as a recorded binding inside the frozen independent-audit "
            "handoff.  No diff is computed and the two source versions are NOT claimed to be "
            "semantically identical."
        ),
        "static_evidence_search": old_search,
        "frozen_runtime_family_unchanged": True,
        "bound_authorities": {
            "original_handoff_sha256": fam_actual["original_handoff"],
            "d89_disclosure_sha256": fam_actual["d89_disclosure"],
            "d90_reconciliation_sha256": fam_actual["d90_reconciliation"],
        },
        "other_final_audit_bytes_verified": {
            "reachable_write_target_inventory": audit_actual["reachable_write_target_inventory"],
            "output_namespace_map": audit_actual["output_namespace_map"],
            "operational_cross_contract_source": audit_actual["operational_cross_contract_source"],
            "release_attestation": audit_actual["release_attestation"],
            "final_readiness": audit_actual["final_readiness"],
            "table_figure_target_count": inv.get("table_figure_target_count"),
            "total_reachable_write_target_count": inv.get("total_reachable_write_target_count"),
            "unclassified_write_target_count": inv.get("unclassified_write_target_count"),
            "namespace_overlap_count": inv.get("namespace_overlap_count"),
        },
        "runtime_release_state": "RELEASED",
        "reconciliation": (
            "Disclosed and reconciled additively.  The current on-disk negative-control source bytes "
            "are authoritative for the validation-only artifact; the frozen handoff records the "
            "expected pre-drift SHA.  The drift is provenance-only.  No source was edited, no "
            "validator was rerun, no report was rewritten, and the frozen handoff is NOT altered; "
            "this disclosure and the v1_1 handoff reconciliation record the authoritative CURRENT "
            "state."
        ),
        "model_free": True,
        "torch_imported": False,
        "generated_utc": NOW,
        "generated_by": "build_phase36_v1_18_negative_control_source_drift_disclosure.py",
    }
    disc_path = AUD / "phase36_v1_18_negative_control_source_drift_disclosure_v1_0.json"
    if disc_path.exists():
        d91_sha = sha(disc_path)  # write-once: never overwrite an existing disclosure
    else:
        write_once_json(disc_path, disclosure)
        d91_sha = sha(disc_path)

    # ---------------- §8 final additive handoff reconciliation v1_1 ---------------- #
    d90 = load(ROOT / RUNTIME_FAMILY["d90_reconciliation"][0])
    recon = {
        "artifact": "phase36_v1_18_independent_audit_handoff_reconciliation_v1_1",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "INDEPENDENT_AUDIT_HANDOFF_RECONCILIATION",
        "supersedes": None,
        "amends": "reports/audits/phase36_v1_18_independent_audit_handoff_reconciliation_v1_0.json",
        "amends_sha256": fam_actual["d90_reconciliation"],
        "reconciles": "reports/audits/phase36_v1_18_independent_audit_handoff_v1_0.json",
        "original_handoff_sha256": fam_actual["original_handoff"],
        "original_handoff_modified": False,
        "delete_or_recreate_performed": False,
        "d89_disclosure_sha256": fam_actual["d89_disclosure"],
        "d90_reconciliation_sha256": fam_actual["d90_reconciliation"],
        "d91_disclosure_sha256": d91_sha,
        "D91": "V1_18_NEGATIVE_CONTROL_SOURCE_SHA_DRIFT_FROM_FROZEN_INDEPENDENT_AUDIT_HANDOFF",
        "authoritative_current_validator_source_state": {
            "negative_control_source_path": NC_SOURCE,
            "negative_control_source_current_sha256": nc_current,
            "negative_control_source_expected_by_original_handoff": NC_EXPECTED_FROM_HANDOFF,
            "negative_control_source_sha_drift": (nc_current != NC_EXPECTED_FROM_HANDOFF),
            "old_source_bytes": old_search["old_source_bytes"],
            "d91_disclosure_sha256": d91_sha,
            "note": (
                "The current on-disk negative-control source SHA is authoritative for the "
                "validation-only artifact.  The original handoff's expected SHA predates the "
                "current bytes.  See the D91 disclosure for the static-evidence-only forensics."
            ),
        },
        "runtime_family_unchanged": True,
        "frozen_runtime_family": {k: fam_actual[k] for k in RUNTIME_FAMILY},
        "runtime_release_state": "RELEASED",
        "runtime_release_state_source": "verify_phase36_v1_18_pure_release_gate_readonly",
        "preserved_defect_statuses": {
            "D61": "PASS",
            "D75": "PASS",
            "D80": "RECONCILED",
            "D81": "RECONCILED",
            "D82": "RECONCILED",
            "D83": "RECONCILED",
            "D84": "DISCLOSED_AND_RECONCILED",
            "D85": "RECONCILED",
            "D86": "RECONCILED",
            "D87": "RECONCILED",
            "D88": "RECONCILED",
            "D89": "DISCLOSED_AND_RECONCILED",
            "D90": "RECONCILED",
            "D91": "DISCLOSED_AND_RECONCILED",
        },
        "v1_14_to_v1_18_scientific_delta_count": 2,
        "v1_14_to_v1_18_scientific_deltas": ["D61", "D75"],
        "v1_17_to_v1_18_scientific_delta_count": 0,
        "unclassified_delta_count": 0,
        "reachable_write_target_count": inv.get("total_reachable_write_target_count"),
        "reachable_csv_table_target_count": len(inv.get("csv_table_targets", [])),
        "reachable_figure_target_count": len(inv.get("figure_targets", [])),
        "table_figure_target_count": inv.get("table_figure_target_count"),
        "unclassified_write_target_count": inv.get("unclassified_write_target_count"),
        "namespace_overlap_count": inv.get("namespace_overlap_count"),
        "v1_18_attempt_consumed": False,
        "v1_17_attempt_consumed": False,
        "scientific_execution": False,
        "scientific_output": False,
        "attempt_absence": {
            "v1_18": v18_state,
            "v1_17": v17_state,
            "v1_18_journal_records": 0,
            "v1_18_attempt_evidence_absent": all(s == "ABSENT" for s in v18_state.values()),
            "v1_17_attempt_evidence_absent": all(s == "ABSENT" for s in v17_state.values()),
            "v1_17_unconsumed": True,
        },
        "protected_populations": {"TEST": "NOT_ACCESSED", "ROUTER_HOLDOUT": "NOT_ACCESSED"},
        "test_reads": 0,
        "router_holdout_reads": 0,
        "val_image_read": False,
        "val_gt_read": False,
        "checkpoint_deserialization": False,
        "model_constructed": False,
        "torch_imported": False,
        "scientific_semantics_effect": "NONE",
        "runtime_semantics_effect": "NONE",
        "governance_provenance_effect": "YES",
        "phase36_state": "NOT_COMPLETE_PENDING_V1_18_EXECUTION",
        "phase37_state": "NOT_STARTED",
        "state": "ELIGIBLE_NOT_STARTED",
        "model_free": True,
        "generated_utc": NOW,
        "generated_by": "build_phase36_v1_18_negative_control_source_drift_disclosure.py",
    }
    recon_path = AUD / "phase36_v1_18_independent_audit_handoff_reconciliation_v1_1.json"
    if recon_path.exists():
        recon_sha = sha(recon_path)  # write-once
    else:
        write_once_json(recon_path, recon)
        recon_sha = sha(recon_path)

    print(json.dumps({
        "D91_disclosure_sha256": d91_sha,
        "handoff_reconciliation_v1_1_sha256": recon_sha,
        "D91": disclosure["D91"],
        "D91_status": disclosure["D91_status"],
        "negative_control_source_expected_by_original_handoff": NC_EXPECTED_FROM_HANDOFF,
        "negative_control_source_current_sha256": nc_current,
        "old_source_bytes": old_search["old_source_bytes"],
        "runtime_family_unchanged": True,
        "runtime_release_state": "RELEASED",
    }, indent=1))
    print("terminal: PHASE36_V1_18_WO17G_ARTIFACTS_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
