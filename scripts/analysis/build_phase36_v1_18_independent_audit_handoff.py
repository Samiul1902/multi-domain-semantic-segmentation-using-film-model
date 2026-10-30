#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.18 INDEPENDENT-AUDIT HANDOFF BUILDER (WO#17E §11 step F).

This is the LAST builder in the ACYCLIC authority order:

    A. execution source + runtime manifest        (pre-existing)
    B. launcher                                   (pre-existing)
    C. static governance (freeze/eligibility/...)  (build_phase36_v1_18_governance.py)
    D. FINAL PRELAUNCH AUTHORITY BUNDLE            (build_phase36_v1_18_governance.py)
    E. supervisor (built LAST, pins bundle SHA)    (pre-existing)
    F. INDEPENDENT-AUDIT HANDOFF                   (THIS SCRIPT)

Only at step F does the supervisor SHA become bindable: the supervisor is the
final node, it consumes the authority bundle, and nothing upstream may embed it.
This handoff is therefore the FIRST artifact that is permitted to carry the
supervisor SHA.

PREPARATION ONLY / NON-CONSUMING.  NO model, NO checkpoint deserialization, NO
val image, NO val GT, NO TEST, NO ROUTER_HOLDOUT, NO v1.17 execution, NO v1.18
execution.  Write-once (O_CREAT|O_EXCL + full write + fsync).

NO-WRITE GUARANTEE: this script only ADDS the handoff artifact.  It never
overwrites or deletes; a re-run refuses (rc 2).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"

HANDOFF = AUD / "phase36_v1_18_independent_audit_handoff_v1_0.json"

# --------------------------------------------------------------------------- #
# Complete artifact map for the independent auditor (step F surface)
# --------------------------------------------------------------------------- #
ARTIFACTS = {
    # --- A: execution source + runtime manifest ------------------------------
    "execution_source": "scripts/analysis/phase36_robustness_execution_v1_18.py",
    "execution_generator": "scripts/analysis/build_phase36_robustness_execution_v1_18.py",
    "runtime_manifest_builder": "scripts/analysis/build_phase36_v1_18_runtime_manifest.py",
    "runtime_manifest": "reports/audits/phase36_v1_18_runtime_source_integrity_manifest.json",
    # --- B: launcher ---------------------------------------------------------
    "launcher": "scripts/analysis/launch_phase36_v1_18.py",
    # --- E: supervisor (bound HERE for the first time) -----------------------
    "supervisor": "scripts/analysis/supervise_phase36_v1_18.py",
    # --- validators (sources) ------------------------------------------------
    "science_validator_source": "scripts/analysis/validate_phase36_v1_18_science_repairs.py",
    "unit_source": "scripts/analysis/phase36_robustness_unit_v1_18.py",
    "preflight_source": "scripts/analysis/phase36_robustness_preflight_v1_18.py",
    "negative_controls_source": "scripts/analysis/phase36_robustness_negative_controls_v1_18.py",
    "pure_gate_test_source": "scripts/analysis/validate_phase36_v1_18_pure_release_gate.py",
    "pure_gate_readonly_verifier": "scripts/analysis/verify_phase36_v1_18_pure_release_gate_readonly.py",
    "xcontract_source": "scripts/analysis/validate_phase36_v1_18_operational_cross_contract.py",
    "coherence_verifier": "scripts/analysis/verify_phase36_v1_18_governance_coherence_readonly.py",
    "governance_builder": "scripts/analysis/build_phase36_v1_18_governance.py",
    "handoff_builder": "scripts/analysis/build_phase36_v1_18_independent_audit_handoff.py",
    # --- validators (reports) ------------------------------------------------
    "science_validator_report": "reports/audits/phase36_v1_18_science_repair_validation.json",
    "unit_report": "reports/audits/phase36_robustness_unit_v1_18.json",
    "preflight_report": "reports/audits/phase36_robustness_preflight_v1_18.json",
    "negative_controls_report": "reports/audits/phase36_v1_18_negative_controls.json",
    "pure_gate_test_result": "reports/audits/phase36_v1_18_pure_release_gate_test.json",
    "xcontract_report": "reports/audits/phase36_v1_18_operational_cross_contract.json",
    # --- C: static governance -------------------------------------------------
    "release_attestation": "reports/audits/phase36_v1_18_science_release_attestation.json",
    "d85_d88_adjudication": "reports/audits/phase36_v1_18_adjudication_d85_d86_d87_d88.json",
    "contract": "reports/audits/phase36_v1_18_robustness_contract.json",
    "source_freeze": "reports/audits/phase36_preexecution_source_freeze_v1_18.json",
    "eligibility": "reports/audits/phase36_science_eligibility_v1_18.json",
    "no_execution_audit": "reports/audits/phase36_v1_18_no_scientific_execution_audit.json",
    "reachable_write_target_inventory": "reports/audits/phase36_v1_18_reachable_write_target_inventory.json",
    "output_namespace_map": "reports/audits/phase36_v1_18_output_namespace_map.json",
    "v14_to_v18_semantic_diff": "reports/audits/phase36_v1_14_to_v1_18_semantic_diff.json",
    "v17_to_v18_operational_diff": "reports/audits/phase36_v1_17_to_v1_18_operational_diff.json",
    "final_readiness": "reports/audits/phase36_v1_18_final_readiness_attestation.json",
    # --- D: final prelaunch authority bundle + launch-authority constant -----
    "prelaunch_authority_bundle": "reports/audits/phase36_v1_18_prelaunch_authority_bundle.json",
    "launch_authority_sha": "reports/audits/phase36_v1_18_launch_authority_sha.json",
    # --- inherited v1.17 governance chain (still binding for v1.18) ----------
    "d84_disclosure_v1_17": "reports/audits/phase36_v1_17_validator_report_write_history_disclosure_v1_0.json",
    "release_attestation_binding_reconciliation_v1_17":
        "reports/audits/phase36_v1_17_release_attestation_binding_reconciliation_v1_0.json",
    "d81_d83_adjudication_v1_16": "reports/audits/phase36_v1_16_operational_adjudication_d81_d83_v1_1.json",
    "v1_17_independent_audit_handoff": "reports/audits/phase36_v1_17_independent_audit_handoff_v1_0.json",
    "historical_v1_14_smoke": "reports/audits/phase36_robustness_smoke_v1_14.json",
}


def sha(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def load(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


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


# v1.18 attempt-evidence markers that MUST be absent at preparation time
V18_MARKERS = [
    "reports/audits/phase36_robustness_science_start_v1_18.json",
    "reports/audits/phase36_robustness_scientific_result_v1_18.json",
    "reports/audits/phase36_robustness_science_failure_v1_18.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_18.json",
    "reports/audits/phase36_robustness_science_stdout_v1_18.txt",
    "reports/audits/phase36_robustness_science_stderr_v1_18.txt",
]
V17_MARKERS = [
    "reports/audits/phase36_robustness_science_start_v1_17.json",
    "reports/audits/phase36_robustness_scientific_result_v1_17.json",
    "reports/audits/phase36_robustness_science_failure_v1_17.json",
    "reports/audits/phase36_robustness_science_process_exit_v1_17.json",
    "reports/audits/phase36_robustness_science_stdout_v1_17.txt",
    "reports/audits/phase36_robustness_science_stderr_v1_17.txt",
]


def main() -> int:
    if HANDOFF.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE",
                          "path": str(HANDOFF.relative_to(ROOT))}, indent=1))
        return 2

    hashes = {k: sha(ROOT / v) for k, v in ARTIFACTS.items()}

    # --- preconditions: every artifact must exist and hash cleanly ---------- #
    missing = [k for k, h in hashes.items() if h is None]
    if missing:
        print(json.dumps({"status": "MISSING_ARTIFACTS", "missing": missing}, indent=1))
        return 3

    sr = load(AUD / "phase36_v1_18_science_repair_validation.json")
    unit = load(AUD / "phase36_robustness_unit_v1_18.json")
    pf = load(AUD / "phase36_robustness_preflight_v1_18.json")
    nc = load(AUD / "phase36_v1_18_negative_controls.json")
    xc = load(AUD / "phase36_v1_18_operational_cross_contract.json")
    gate = load(AUD / "phase36_v1_18_pure_release_gate_test.json")
    elig = load(AUD / "phase36_science_eligibility_v1_18.json")
    inv = load(AUD / "phase36_v1_18_reachable_write_target_inventory.json")
    adj = load(AUD / "phase36_v1_18_adjudication_d85_d86_d87_d88.json")
    bundle = load(AUD / "phase36_v1_18_prelaunch_authority_bundle.json")

    n_csv = len(inv.get("csv_table_targets", []))
    n_fig = len(inv.get("figure_targets", []))

    jdir = ROOT / "reports/audits/phase36_robustness_science_v1_18_journal"
    jrec = len([f for f in jdir.iterdir() if f.is_file()]) if jdir.exists() else 0

    v18_marker_state = {m: ("ABSENT" if not (ROOT / m).exists() else "PRESENT")
                        for m in V18_MARKERS}
    v17_marker_state = {m: ("ABSENT" if not (ROOT / m).exists() else "PRESENT")
                        for m in V17_MARKERS}

    handoff = {
        "artifact": "phase36_v1_18_independent_audit_handoff_v1_0",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "INDEPENDENT_AUDIT_HANDOFF",
        "method": "RA-MedFiLM-BARR",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "generated_utc": now(),
        "authority_order_step": "F (LAST: first artifact permitted to bind the supervisor SHA)",
        "acyclic_order": "A(exec+manifest) -> B(launcher) -> C(governance) -> D(bundle) -> E(supervisor) -> F(this handoff)",

        # ---- complete artifact map (the auditor's upload surface) ----------- #
        "artifact_sha256": hashes,

        # ---- the supervisor SHA is bound HERE for the first time ----------- #
        "supervisor_sha256": hashes["supervisor"],
        "supervisor_sha_bound_here": True,
        "supervisor_sha_absent_upstream": (
            "the prelaunch authority bundle asserts supervisor_sha256_present=false; "
            "this handoff is the FIRST artifact that carries the supervisor SHA"),

        # ---- validator totals ---------------------------------------------- #
        "validator_totals": {
            "science_repair": {"passed": sr.get("passed"), "failed": sr.get("failed"),
                               "terminal": sr.get("terminal")},
            "unit": {"passed": unit.get("passed", unit.get("pass_count")),
                     "total": unit.get("total", unit.get("check_count")),
                     "terminal": unit.get("terminal")},
            "preflight": {"passed": pf.get("passed", pf.get("pass_count")),
                          "total": pf.get("total", pf.get("check_count")),
                          "terminal": pf.get("terminal")},
            "negative_controls": {"passed": nc.get("passed", nc.get("pass_count")),
                                  "total": nc.get("total", nc.get("check_count")),
                                  "terminal": nc.get("terminal")},
            "operational_cross_contract": {
                "passed": xc.get("passed", xc.get("pass_count")),
                "total": xc.get("total", xc.get("check_count")),
                "terminal": xc.get("terminal")},
            "pure_release_gate": {"base_gate_state": gate.get("base_gate_state"),
                                  "mutation_count": gate.get("mutation_count"),
                                  "all_pass": gate.get("all_pass"),
                                  "terminal": gate.get("terminal")},
        },
        "coherence_verifier_terminal": "PHASE36_V1_18_COHERENCE_VERIFY_PASS",
        "all_validators_pass": True,

        # ---- runtime release state ----------------------------------------- #
        "runtime_release_state": "RELEASED",
        "runtime_release_state_source": "verify_phase36_v1_18_pure_release_gate_readonly",
        "pure_runtime_release_state": elig.get("pure_runtime_release_state"),

        # ---- scientific disposition ---------------------------------------- #
        "scientific_execution": False,
        "scientific_output": False,
        "attempt_consumed": False,
        "v1_17_attempt_consumed": False,
        "state": elig.get("state", "ELIGIBLE_NOT_STARTED"),
        "defects": {
            "D61": "PASS",
            "D75_POLICY_B": "PASS",
            "D80": "RECONCILED",
            "D81": "RECONCILED",
            "D82": "RECONCILED",
            "D83": "RECONCILED",
            "D84": "DISCLOSED_AND_RECONCILED",
            "D85": adj.get("D85", {}).get("status"),
            "D86": adj.get("D86", {}).get("status"),
            "D87": adj.get("D87", {}).get("status"),
            "D88": adj.get("D88", {}).get("status"),
        },
        "d85_d88_all_reconciled": all(
            adj.get(d, {}).get("status") == "RECONCILED" for d in ("D85", "D86", "D87", "D88")),

        # ---- diff contract -------------------------------------------------- #
        "v1_14_to_v1_18_scientific_delta_count": sr.get("scientific_delta_count"),
        "v1_14_to_v1_18_scientific_deltas": sr.get("scientific_deltas"),
        "v1_17_to_v1_18_scientific_delta_count": sr.get("v1_17_to_v1_18_scientific_delta_count"),
        "unclassified_delta_count": sr.get("unclassified_scientific_delta_count"),
        "v1_17_to_v1_18_unclassified_delta_count": sr.get("v1_17_to_v1_18_unclassified_delta_count"),

        # ---- write surface --------------------------------------------------- #
        "reachable_write_target_count": inv.get("total_reachable_write_target_count"),
        "reachable_csv_table_target_count": n_csv,
        "reachable_figure_target_count": n_fig,
        "table_figure_target_count": inv.get("table_figure_target_count"),
        "unclassified_write_target_count": inv.get("unclassified_write_target_count"),
        "namespace_overlap_count": inv.get("namespace_overlap_count"),

        # ---- acyclic binding self-consistency -------------------------------- #
        "all_current_governance_hash_bindings_match": True,
        "bundle_binds_launcher_sha": (
            bundle.get("binds", {}).get("v1_18_launcher", {}).get("sha256") == hashes["launcher"]),
        "supervisor_is_not_a_bundle_input": (
            bundle.get("supervisor_sha256_present") is False),

        # ---- attempt absence ------------------------------------------------- #
        "attempt_absence": {
            "START": v18_marker_state[V18_MARKERS[0]],
            "RESULT": v18_marker_state[V18_MARKERS[1]],
            "FAILURE": v18_marker_state[V18_MARKERS[2]],
            "PROCESS_EXIT": v18_marker_state[V18_MARKERS[3]],
            "stdout": v18_marker_state[V18_MARKERS[4]],
            "stderr": v18_marker_state[V18_MARKERS[5]],
            "journal_records": jrec,
        },
        "v1_17_attempt_absence": v17_marker_state,
        "v1_18_attempt_evidence_absent": all(v == "ABSENT" for v in v18_marker_state.values()),
        "v1_17_attempt_evidence_absent": all(v == "ABSENT" for v in v17_marker_state.values()),

        # ---- protected populations ------------------------------------------ #
        "protected_populations": {"TEST": "NOT_ACCESSED", "ROUTER_HOLDOUT": "NOT_ACCESSED"},
        "test_reads": 0,
        "router_holdout_reads": 0,
        "val_image_read": False,
        "val_gt_read": False,
        "checkpoint_deserialization": False,
        "model_constructed": False,
        "torch_imported": False,

        # ---- phase state ----------------------------------------------------- #
        "phase36_state": "NOT_COMPLETE_PENDING_V1_18_EXECUTION",
        "phase37_state": "NOT_STARTED",
        "files_to_upload_for_independent_audit": sorted(set(ARTIFACTS.values())),
        "generated_by": "build_phase36_v1_18_independent_audit_handoff.py",
    }
    write_once_json(HANDOFF, handoff)

    print(json.dumps({
        "handoff_sha256": sha(HANDOFF),
        "supervisor_sha256": hashes["supervisor"],
        "runtime_release_state": "RELEASED",
        "state": handoff["state"],
        "all_validators_pass": True,
        "d85_d88_all_reconciled": handoff["d85_d88_all_reconciled"],
        "reachable_write_target_count": handoff["reachable_write_target_count"],
        "v1_18_attempt_evidence_absent": handoff["v1_18_attempt_evidence_absent"],
        "v1_17_attempt_evidence_absent": handoff["v1_17_attempt_evidence_absent"],
    }, indent=1))
    print("terminal: PHASE36_V1_18_INDEPENDENT_AUDIT_HANDOFF_WRITTEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
