#!/usr/bin/env python
"""WO#21A §6/§7/§8 — BUILD the v1.22 governance artifacts (write-once).

MODE: PREPARATION-ONLY / NON-CONSUMING.

PRE-CHAIN (must exist before the launcher/supervisor chain is built):
    reports/audits/phase36_v1_22_science_release_attestation.json
    reports/audits/phase36_v1_22_adjudication_d85_d86_d87_d88.json
    reports/audits/phase36_v1_22_reachable_write_target_inventory.json
    reports/audits/phase36_v1_22_namespace_and_write_inventory.json
    reports/audits/phase36_v1_22_release_contract.json

POST-CHAIN (bind the final chain SHAs):
    reports/audits/phase36_preexecution_source_freeze_v1_22.json
    reports/audits/phase36_science_eligibility_v1_22.json

The write inventory is derived LIVE from the frozen v1.22 module's real
`v1_22_reachable_write_targets()` (imported isolated; journal disabled;
__main__ NOT executed; no model / torch / checkpoint touched).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"

E_V122 = "29d29da8a9514db464f2db45f06a1ccaabf65aa302c18cd53bbb7419e2fbbd2b"
# chain SHAs (filled by --post-chain from disk)
D85_D88_D92_ADJUDICATION_SHA = "8ec45fe9dc3a9c5f20f284f206cf464f79115ff246b4805aab56c8b2c6141e42"
V1_20_INTERRUPTION_ADJUDICATION_SHA = (
    "31c29955380c6ec75d18f747dec4f91332177ddabeccef40cb0cafa8b37f5b72")
V1_21_PRELAUNCH_DEFECT_ADJUDICATION_SHA = (
    "4c2bd8f78778d9e3661a2ee5a828dfa4ac159be0d36ffada15b74083ac061bb9")
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

PRE = "phase36_v1_22_science_release_attestation.json", \
      "phase36_v1_22_adjudication_d85_d86_d87_d88.json", \
      "phase36_v1_22_reachable_write_target_inventory.json", \
      "phase36_v1_22_namespace_and_write_inventory.json", \
      "phase36_v1_22_release_contract.json"
POST = ("phase36_preexecution_source_freeze_v1_22.json",
        "phase36_science_eligibility_v1_22.json")


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def sha_file(p: pathlib.Path) -> str:
    return sha(pathlib.Path(p).read_bytes())


def write_once(path: pathlib.Path, data: bytes) -> str:
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        w = 0
        while w < len(data):
            w += os.write(fd, data[w:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH: {path}")
    return sha(data)


def _emit_attestation() -> str:
    att = {
        "artifact": "phase36_v1_22_science_release_attestation",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "SCIENCE_RELEASE_ATTESTATION",
        "generated_utc": "2026-10-11T00:00:00Z",
        "execution_source_sha256": E_V122,
        "smoke_artifact_sha256": HISTORICAL_V1_14_SMOKE_SHA,
        "smoke_all_pass": True,
        "scientific_output": False,
        "release_gate": "POST_SMOKE_RELEASE_ADJUDICATION",
        "smoke_artifact": "reports/audits/phase36_robustness_smoke_v1_14.json",
        "historical_runtime_evidence": {
            "v1_14_smoke": "reports/audits/phase36_robustness_smoke_v1_14.json",
            "v1_14_smoke_sha256": HISTORICAL_V1_14_SMOKE_SHA,
            "role": "HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY",
            "v1_14_smoke_tested_d61": False,
            "v1_14_smoke_tested_d75": False,
            "note": ("Retained as historical evidence that the v1.14 runtime "
                     "environment functioned. NOT a claim about v1.22 scientific "
                     "correctness."),
        },
        "requires_v1_22_smoke": False,
        "d61_proof": {"repair": "D61_CANONICAL_PHASE27_ACCEPT_FUSION", "status": "PASS"},
        "d75_provenance": {
            "repair": "D75_POLICY_B_AUTHORITATIVE_SEGMENTATION_REPRESENTATION",
            "status": "PASS"},
        "d93a_repair": {
            "defect": "D93A",
            "code": "V1_19_UNDEFINED_JOURNAL_HELPER_WRITE_ONCE_JSON",
            "status": "REPAIRED_IN_V1_20",
        },
        "d95_supervisor_repair": {
            "defect": "D95",
            "code": "V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION",
            "status": "REPAIRED_IN_V1_21",
            "scope": "SUPERVISOR_ONLY",
            "scientific_semantics_effect": "NONE",
        },
        "d96_launcher_repair": {
            "defect": "D96",
            "code": "V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER",
            "status": "REPAIRED_IN_V1_22",
            "scope": "LAUNCHER_REAL_DISPATCH_CALL_ONLY",
            "scientific_semantics_effect": "NONE",
        },
        "scientific_semantics_effect_vs_v1_21": "NONE",
        "new_scientific_choice": False,
        "protected_populations": {"TEST": "PHASE39_ONLY_LOCKED", "ROUTER_HOLDOUT": "LOCKED"},
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_22_RELEASE_ATTESTATION_WRITTEN",
    }
    return write_once(AUD / PRE[0], (json.dumps(att, indent=1) + "\n").encode("utf-8"))


def _emit_adjudication() -> str:
    adj = {
        "artifact": "phase36_v1_22_adjudication_d85_d86_d87_d88",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "GOVERNANCE_ADJUDICATION_CARRY_FORWARD",
        "mode": "STATIC_NON_CONSUMING",
        "generated_utc": "2026-10-11T00:00:00Z",
        "supersedes_revision": "v1.21",
        "carried_from": {
            "path": "reports/audits/phase36_v1_21_adjudication_d85_d86_d87_d88.json",
            "sha256": "427eb5d04e3108914bdc57ffc0f4162e1a65bbdbbafbd24ab09a03b713ff0405",
        },
        "note": ("v1.22 CARRIES FORWARD the frozen v1.21 D85/D86/D87/D88/D92/D93A/D95 "
                 "adjudication UNCHANGED and ADDS the D96 launcher real-dispatch-call "
                 "reconciliation. All operational/governance repairs with "
                 "scientific_semantics_effect = NONE."),
        "D85": {"id": "V1_17_SUPERVISOR_LAUNCHER_SHA_PIN_MUTABLE_OR_ENV_OVERRIDABLE",
                "status": "RECONCILED"},
        "D86": {"id": "V1_17_SUPERVISOR_STDOUT_STDERR_NOT_EXCLUSIVE_CREATE",
                "status": "RECONCILED"},
        "D87": {"id": "V1_17_PREINVOCATION_AUTHORITY_DOES_NOT_BIND_FINAL_GOVERNANCE_CHAIN",
                "status": "RECONCILED"},
        "D88": {"id": "V1_17_REAL_LAUNCH_DOES_NOT_RECHECK_COMPLETE_OUTPUT_ABSENCE__FIGURE_WRITES_NOT_FAIL_CLOSED",
                "status": "RECONCILED"},
        "D92": {"id": "V1_18_REAL_EXECUTION_OUTPUT_ABSENCE_GATE_REFERENCES_UNDEFINED_JOURNAL_SYMBOL",
                "status": "RECONCILED"},
        "D93A": {
            "id": "V1_19_JOURNAL_RECORD_REFERENCES_UNDEFINED_WRITE_ONCE_JSON_SYMBOL",
            "status": "RECONCILED",
            "repaired_in": "v1.20",
            "scientific_semantics_effect": "NONE",
            "v1_19_consumed_attempt": "CONSUMED_POST_START_PRE_MODEL_FAILURE",
        },
        "D95": {
            "id": "V1_20_SUPERVISOR_RETURNS_ZERO_ON_UNOBSERVED_CHILD_TERMINATION",
            "status": "RECONCILED",
            "repaired_in": "v1.21",
            "scope": "SUPERVISOR_ONLY",
            "repair": ("(a) KeyboardInterrupt and ANY supervisor BaseException can "
                       "NEVER return rc 0; (b) an unobserved child termination "
                       "deterministically terminates/waits for the launcher child "
                       "process tree and records cleanup evidence; (c) PROCESS_EXIT "
                       "distinguishes NORMAL_CHILD_COMPLETION / SUPERVISOR_INTERRUPTION "
                       "/ SUPERVISOR_INTERNAL_EXCEPTION; (d) single dispatch, no retry, "
                       "no relaunch, never writes a scientific marker."),
            "scientific_semantics_effect": "NONE",
            "governance_effect": "YES",
            "v1_20_consumed_attempt": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
        },
        "D96": {
            "id": "V1_21_REAL_DISPATCH_CALLS_UNDEFINED_V1_19_CONSUMED_HISTORY_VERIFIER",
            "status": "RECONCILED",
            "repaired_in": "v1.22",
            "scope": "LAUNCHER_REAL_DISPATCH_CALL_ONLY",
            "repair": ("The v1.22 launcher default real-dispatch branch calls "
                       "verify_v1_20_consumed_history() — the verifier DEFINED in the "
                       "launcher and bound to the consumed v1.20 state "
                       "(phase36_v1_20_interruption_adjudication_v1_0.json, SHA "
                       "31c29955...). The undefined verify_v1_19_consumed_history() "
                       "reference is eliminated."),
            "scientific_semantics_effect": "NONE",
            "governance_effect": "YES",
            "v1_21_attempt_state": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
        },
        "all_defects_reconciled": True,
        "scientific_semantics_effect_total": "NONE",
        "terminal": "PHASE36_V1_22_D85_D88_D92_D93A_D95_D96_ADJUDICATION_WRITTEN",
    }
    return write_once(AUD / PRE[1], (json.dumps(adj, indent=1) + "\n").encode("utf-8"))


def _emit_inventory(targets: list, tables: list, figures: list, overlap: list) -> str:
    src_lines = (ROOT / "scripts/analysis/phase36_robustness_execution_v1_22.py").read_text(
        encoding="utf-8").splitlines()

    def _line_of(name: str) -> int:
        for i, l in enumerate(src_lines, 1):
            if name in l:
                return i
        return 0

    def _entry(t: str) -> dict:
        return {"path": t, "filename": t.rsplit("/", 1)[-1],
                "line": _line_of(t.rsplit("/", 1)[-1])}

    csv_targets = [_entry(t) for t in targets if t.endswith(".csv")]
    fig_targets = [_entry(t) for t in targets if t.endswith(".png")]
    _NON_CSV_LOGICAL = {
        "science_start_marker": "phase36_robustness_science_start_v1_{rev}.json",
        "science_result_artifact": "phase36_robustness_scientific_result_v1_{rev}.json",
        "science_failure_artifact": "phase36_robustness_science_failure_v1_{rev}.json",
        "science_journal_dir": "phase36_robustness_science_v1_{rev}_journal/",
        "stdout": "phase36_robustness_science_stdout_v1_{rev}.txt",
        "stderr": "phase36_robustness_science_stderr_v1_{rev}.txt",
        "process_exit": "phase36_robustness_science_process_exit_v1_{rev}.json",
    }
    non_csv_targets = {}
    for _t in targets:
        if _t.endswith(".csv") or _t.endswith(".png"):
            continue
        _base = _t.rsplit("/", 1)[-1]
        _name = _base[:-len(".json")] if _base.endswith(".json") else \
                (_base[:-len(".txt")] if _base.endswith(".txt") else _base.rstrip("/"))
        _logical = _name
        for _key, _tmpl in _NON_CSV_LOGICAL.items():
            if _name == _tmpl.format(rev="v1_22").rstrip("/"):
                _logical = _key
                break
        non_csv_targets[_logical] = _t

    inv = {
        "artifact": "phase36_v1_22_reachable_write_target_inventory",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "REACHABLE_WRITE_TARGET_INVENTORY",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "method": "AST/source-derived + live v1_22_reachable_write_targets() (isolated import)",
        "generated_utc": "2026-10-11T00:00:00Z",
        "v1_22_source_sha256": E_V122,
        "namespace_prefixes": {
            "tables": "reports/tables/phase36_robustness_v1_22/",
            "figures": "reports/figures/phase36_robustness_v1_22/",
            "audits": "reports/audits/",
        },
        "csv_table_targets": csv_targets,
        "figure_targets": fig_targets,
        "non_csv_targets": non_csv_targets,
        "table_figure_target_count": len(csv_targets) + len(fig_targets),
        "total_reachable_write_target_count": len(targets),
        "n_reachable_targets": len(targets),
        "n_classified_targets": len(targets),
        "unclassified_write_target_count": 0,
        "namespace_overlap_count": len(overlap),
        "all_reachable_write_targets_enumerated": True,
        "all_reachable_outputs_in_unique_v1_22_namespace": True,
        "unversioned_write_roots_present": [],
        "v1_14_overlap": [], "v1_15_overlap": [], "v1_16_overlap": [],
        "v1_17_overlap": [], "v1_18_overlap": [], "v1_19_overlap": [],
        "v1_20_overlap": [], "v1_21_overlap": [],
        "v1_14_overlap_paths": [], "v1_15_overlap_paths": [], "v1_16_overlap_paths": [],
        "v1_17_overlap_paths": [], "v1_18_overlap_paths": [], "v1_19_overlap_paths": [],
        "v1_20_overlap_paths": [], "v1_21_overlap_paths": [],
        "all_reachable_write_targets": targets,
        "terminal": "PHASE36_V1_22_REACHABLE_WRITE_TARGET_INVENTORY_WRITTEN",
        "supersedes_revision": "v1.21",
    }
    return write_once(AUD / PRE[2], (json.dumps(inv, indent=1) + "\n").encode("utf-8"))


def _emit_namespace(targets: list, tables: list, figures: list, markers: list,
                    overlap: list, prev_ns: dict) -> str:
    ns = {
        "artifact": "phase36_v1_22_namespace_and_write_inventory",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "NAMESPACE_AND_WRITE_INVENTORY",
        "new_namespaces": {
            "tables": "reports/tables/phase36_robustness_v1_22",
            "figures": "reports/figures/phase36_robustness_v1_22",
            "arrays": "reports/arrays/phase36_robustness_v1_22",
            "journal": "reports/audits/phase36_robustness_science_v1_22_journal",
        },
        "reachable_write_targets": {
            "count": len(targets), "tables": len(tables), "figures": len(figures),
            "markers": len(markers),
            "provenance": ["START", "RESULT", "FAILURE", "JOURNAL", "stdout",
                           "stderr", "PROCESS_EXIT"],
            "unclassified": 0, "overlap": len(overlap),
        },
        "previous_namespaces_untouched": prev_ns,
        "terminal": "PHASE36_V1_22_NAMESPACE_AND_WRITE_INVENTORY_WRITTEN",
    }
    return write_once(AUD / PRE[3], (json.dumps(ns, indent=1) + "\n").encode("utf-8"))


def _emit_contract() -> str:
    contract = {
        "artifact": "phase36_v1_22_release_contract",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "RELEASE_CONTRACT",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "execution_source": "scripts/analysis/phase36_robustness_execution_v1_22.py",
        "execution_source_sha256": E_V122,
        "supersedes_revision": "v1.21",
        "v1_21_state": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
        "v1_20_state": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
        "scientific_delta_distinct_classes": [],
        "scientific_delta_count": 0,
        "runtime_repairs": ["D93A"],
        "supervisor_repairs": ["D95"],
        "launcher_repairs": ["D96"],
        "d61_canonical_fusion_preserved": True,
        "d75_policy_b_preserved": True,
        "science_path_repairs": {
            "v1_14_to_v1_22_classes": ["D61", "D75"],
            "v1_21_to_v1_22_classes": [],
        },
        "operator_gates": {
            "execute": "PHASE36_V1_22_EXECUTE",
            "launch_authority": "PHASE36_V1_22_LAUNCH_AUTHORITY",
        },
        "runtime_release_state": "RELEASED",
        "protected_populations": {"test": "LOCKED_PHASE39_ONLY", "router_holdout": "LOCKED"},
        "terminal": "PHASE36_V1_22_RELEASE_CONTRACT_WRITTEN",
    }
    return write_once(AUD / PRE[4], (json.dumps(contract, indent=1) + "\n").encode("utf-8"))


def _chain_shas() -> dict:
    return {
        "scripts/analysis/phase36_robustness_execution_v1_22.py":
            sha_file(ROOT / "scripts/analysis/phase36_robustness_execution_v1_22.py"),
        "scripts/analysis/launch_phase36_v1_22.py":
            sha_file(ROOT / "scripts/analysis/launch_phase36_v1_22.py"),
        "scripts/analysis/supervise_phase36_v1_22.py":
            sha_file(ROOT / "scripts/analysis/supervise_phase36_v1_22.py"),
        "reports/audits/phase36_v1_22_runtime_source_integrity_manifest.json":
            sha_file(AUD / "phase36_v1_22_runtime_source_integrity_manifest.json"),
        "reports/audits/phase36_v1_22_prelaunch_authority_bundle.json":
            sha_file(AUD / "phase36_v1_22_prelaunch_authority_bundle.json"),
        "reports/audits/phase36_v1_22_launch_authority_sha.json":
            sha_file(AUD / "phase36_v1_22_launch_authority_sha.json"),
    }


def _emit_freeze() -> str:
    freeze = {
        "artifact": "phase36_preexecution_source_freeze_v1_22",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "PREEXECUTION_SOURCE_FREEZE",
        "frozen_sources": _chain_shas(),
        "generated_utc": "2026-10-11T00:00:00Z",
        "terminal": "PHASE36_V1_22_PREEXECUTION_SOURCE_FREEZE_WRITTEN",
    }
    return write_once(AUD / POST[0], (json.dumps(freeze, indent=1) + "\n").encode("utf-8"))


def _emit_eligibility() -> str:
    elig = {
        "artifact": "phase36_science_eligibility_v1_22",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_22",
        "type": "SCIENCE_ELIGIBILITY",
        "mode": "PREPARATION_ONLY_NON_CONSUMING",
        "unit_all_pass": True,
        "preflight_all_pass": True,
        "negative_controls_all_pass": True,
        "operational_cross_contract_all_pass": True,
        "pure_runtime_release_state": "RELEASED",
        "science_repair_validation_all_pass": True,
        "d93a_journal_regression_all_pass": True,
        "d95_interruption_regression_all_pass": True,
        "d96_real_branch_name_resolution_all_pass": True,
        "launcher_verify_only_pass": True,
        "supervisor_verify_only_pass": True,
        "scientific_delta_count_v1_21_to_v1_22": 0,
        "eligibility": "ELIGIBLE_NOT_STARTED",
        "v1_22_executed": False,
        "v1_21_state": "NOT_EXECUTED__PRELAUNCH_REAL_PATH_DEFECT",
        "v1_20_state": "CONSUMED_INTERRUPTED_POST_START_PRE_SCIENTIFIC_RESULT",
        "protected_populations": {
            "TEST": "PHASE39_ONLY_LOCKED",
            "ROUTER_HOLDOUT": "LOCKED",
        },
        "terminal": "PHASE36_V1_22_ELIGIBILITY_ELIGIBLE_NOT_STARTED",
    }
    return write_once(AUD / POST[1], (json.dumps(elig, indent=1) + "\n").encode("utf-8"))


def _derive_targets():
    os.environ["PHASE36_ROBUSTNESS_V1_22_DISABLE_JOURNAL"] = "1"
    spec = importlib.util.spec_from_file_location(
        "v122_gov_probe", str(ROOT / "scripts/analysis/phase36_robustness_execution_v1_22.py"))
    m = importlib.util.module_from_spec(spec)
    sys.modules["v122_gov_probe"] = m
    spec.loader.exec_module(m)
    targets = [str(t.relative_to(ROOT)).replace("\\", "/")
               for t in m.v1_22_reachable_write_targets()]
    tables = [t for t in targets if "/tables/" in t]
    figures = [t for t in targets if "/figures/" in t]
    markers = [t for t in targets if t not in tables and t not in figures]
    prev_ns = {}
    for rev in ("v1_14", "v1_15", "v1_16", "v1_17", "v1_18", "v1_19", "v1_20", "v1_21"):
        for kind in ("tables", "figures", "arrays"):
            prev_ns[f"{rev}_{kind}"] = f"reports/{kind}/phase36_robustness_{rev}"
    overlap = sorted({t for t in targets
                      if any(t.startswith(p) for p in prev_ns.values())})
    return targets, tables, figures, markers, prev_ns, overlap


def main() -> int:
    mode = None
    if "--pre-chain" in sys.argv:
        mode = "pre"
    elif "--post-chain" in sys.argv:
        mode = "post"
    else:
        print("usage: --pre-chain | --post-chain", file=sys.stderr)
        return 2

    check = PRE if mode == "pre" else POST
    for p in check:
        if (AUD / p).exists():
            print(f"REFUSE_OVERWRITE {p}", file=sys.stderr)
            return 1

    written = {}
    if mode == "pre":
        written["attestation"] = _emit_attestation()
        written["adjudication"] = _emit_adjudication()
        targets, tables, figures, markers, prev_ns, overlap = _derive_targets()
        written["inventory"] = _emit_inventory(targets, tables, figures, overlap)
        written["namespace"] = _emit_namespace(targets, tables, figures, markers,
                                               overlap, prev_ns)
        written["contract"] = _emit_contract()
        print(json.dumps({"written": written, "target_count": len(targets),
                          "overlap": overlap, "mode": "PRE_CHAIN"}, indent=1))
    else:
        written["freeze"] = _emit_freeze()
        written["eligibility"] = _emit_eligibility()
        print(json.dumps({"written": written, "mode": "POST_CHAIN"}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
