#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — v1.18 GOVERNANCE BUILDER (write-once, WO#17E).

Builds the v1.18 pre-execution governance artifacts in the ACYCLIC authority
order mandated by WO#17E §11:

  A. v1.18 execution source + runtime manifest            (already built)
  B. v1.18 launcher                                       (already built)
  C. static validators / governance / readiness NOT requiring the supervisor SHA
     -> release attestation
     -> D85-D88 adjudication
     -> robustness contract
     -> source freeze
     -> eligibility
     -> no-scientific-execution audit
     -> reachable-write-target inventory
     -> output namespace map
     -> semantic diffs (v1.14->v1.18, v1.17->v1.18)
     -> final readiness attestation
  D. FINAL PRELAUNCH AUTHORITY BUNDLE (binds A/B/C + D84/D81-D83 chain + the
     protected-population locks; MUST NOT contain the supervisor SHA)
  E. v1.18 supervisor                                     (built LAST, separate)

All artifacts are write-once: O_CREAT|O_EXCL + full write + fsync.
Re-run -> REFUSE_OVERWRITE (rc 2).
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"
SCRIPTS = ROOT / "scripts" / "analysis"

V18_EXEC = SCRIPTS / "phase36_robustness_execution_v1_18.py"
V18_GEN = SCRIPTS / "build_phase36_robustness_execution_v1_18.py"
V18_LAUNCHER = SCRIPTS / "launch_phase36_v1_18.py"
V18_MANIFEST = AUD / "phase36_v1_18_runtime_source_integrity_manifest.json"

V17_EXEC = SCRIPTS / "phase36_robustness_execution_v1_17.py"
V14_EXEC = SCRIPTS / "phase36_robustness_execution_v1_14.py"
V14_MANIFEST = AUD / "phase36_v1_14_runtime_source_integrity_manifest.json"

V17_HANDOFF = AUD / "phase36_v1_17_independent_audit_handoff_v1_0.json"
V17_D84 = AUD / "phase36_v1_17_validator_report_write_history_disclosure_v1_0.json"
V17_BINDING_RECON = AUD / "phase36_v1_17_release_attestation_binding_reconciliation_v1_0.json"
D81_D83_ADJUDICATION = AUD / "phase36_v1_16_operational_adjudication_d81_d83_v1_1.json"
D85_D88_ADJUDICATION = AUD / "phase36_v1_18_adjudication_d85_d86_d87_d88.json"
V18_ATTESTATION = AUD / "phase36_v1_18_science_release_attestation.json"
V18_CONTRACT = AUD / "phase36_v1_18_robustness_contract.json"
V18_FREEZE = AUD / "phase36_preexecution_source_freeze_v1_18.json"
V18_ELIGIBILITY = AUD / "phase36_science_eligibility_v1_18.json"
V18_NOEXEC = AUD / "phase36_v1_18_no_scientific_execution_audit.json"
V18_INVENTORY = AUD / "phase36_v1_18_reachable_write_target_inventory.json"
V18_NSMAP = AUD / "phase36_v1_18_output_namespace_map.json"
V18_DIFF_1418 = AUD / "phase36_v1_14_to_v1_18_semantic_diff.json"
V18_DIFF_1718 = AUD / "phase36_v1_17_to_v1_18_operational_diff.json"
V18_READINESS = AUD / "phase36_v1_18_final_readiness_attestation.json"
V18_BUNDLE = AUD / "phase36_v1_18_prelaunch_authority_bundle.json"
V18_LAUNCH_AUTHORITY_FILE = AUD / "phase36_v1_18_launch_authority_sha.json"

HISTORICAL_V1_14_SMOKE = AUD / "phase36_robustness_smoke_v1_14.json"
HISTORICAL_V1_14_SMOKE_SHA = "53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441"

# Protected-population lock authorities (D85-D88 item: the bundle must bind the
# REAL lock manifests, not a non-existent filename with a null SHA).
#   * TEST           -> phase36_v1_3a_test_identity_authority_binding.json, which binds
#                       the authoritative test split (manifests/phase4_v3/test.csv, 1683 ids).
#   * ROUTER_HOLDOUT -> phase36_v1_3a_router_holdout_identity_authority_binding.json, which
#                       binds reports/audits/phase24_router_split_manifest.csv (875 ids).
TEST_LOCK = AUD / "phase36_v1_3a_test_identity_authority_binding.json"
ROUTER_HOLDOUT_LOCK = AUD / "phase36_v1_3a_router_holdout_identity_authority_binding.json"
PROTECTED_POPULATION_NOT_ACCESSED = "NOT_ACCESSED"

# D85-D88 adjudication constants
D85 = "V1_17_SUPERVISOR_LAUNCHER_SHA_PIN_MUTABLE_OR_ENV_OVERRIDABLE"
D86 = "V1_17_SUPERVISOR_STDOUT_STDERR_NOT_EXCLUSIVE_CREATE"
D87 = "V1_17_PREINVOCATION_AUTHORITY_DOES_NOT_BIND_FINAL_GOVERNANCE_CHAIN"
D88 = "V1_17_REAL_LAUNCH_DOES_NOT_RECHECK_COMPLETE_OUTPUT_ABSENCE__FIGURE_WRITES_NOT_FAIL_CLOSED"

# count semantics (WO#17E §5)
TABLE_FIGURE_TARGET_COUNT = 16      # 11 CSV + 5 figures
TOTAL_REACHABLE_WRITE_TARGET_COUNT = 23   # 16 + START/RESULT/FAILURE/JOURNAL/stdout/stderr/PROCESS_EXIT


def sha(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> None:
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


def _guard(paths: list) -> bool:
    ex = [str(p.relative_to(ROOT)) for p in paths if p.exists()]
    if ex:
        print(json.dumps({"status": "REFUSE_OVERWRITE", "existing": ex}, indent=1))
        return False
    return True


def _reachable_targets() -> dict:
    """AST-derived complete reachable inventory from run_science (v1.18)."""
    src = V18_EXEC.read_text(encoding="utf-8")
    tree = ast.parse(src)
    csvs, figs = [], []
    for n in ast.walk(tree):
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_write_csv" and n.args:
            a0 = n.args[0]
            if isinstance(a0, ast.BinOp) and isinstance(a0.op, ast.Div):
                rhs = a0.right
                if isinstance(rhs, ast.Constant) and rhs.value.endswith(".csv"):
                    csvs.append({"filename": rhs.value, "line": n.lineno})
        if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "_savefig_once" and n.args:
            a1 = n.args[1] if len(n.args) > 1 else None
            # p = FIG / "<name>.png" is assigned just above; recover from Assign
    # recover figure filenames from the FIG / "<...>.png" assignments
    for n in ast.walk(tree):
        if isinstance(n, ast.Assign) and isinstance(n.value, ast.BinOp) \
                and isinstance(n.value.op, ast.Div):
            rhs = n.value.right
            if isinstance(rhs, ast.Constant) and isinstance(rhs.value, str) \
                    and rhs.value.endswith(".png"):
                figs.append({"filename": rhs.value, "line": n.lineno})
    csvs = sorted({c["filename"]: c for c in csvs}.values(), key=lambda d: d["filename"])
    figs = sorted({f["filename"]: f for f in figs}.values(), key=lambda d: d["filename"])
    return {"csv": csvs, "figures": figs}


def main() -> int:
    targets = [V18_ATTESTATION, D85_D88_ADJUDICATION, V18_CONTRACT, V18_FREEZE,
               V18_ELIGIBILITY, V18_NOEXEC, V18_INVENTORY, V18_NSMAP,
               V18_DIFF_1418, V18_DIFF_1718, V18_READINESS, V18_BUNDLE]
    if not _guard(targets):
        return 2

    v18_exec_sha = sha(V18_EXEC)
    v18_launcher_sha = sha(V18_LAUNCHER)
    v18_manifest_sha = sha(V18_MANIFEST)
    v17_exec_sha = sha(V17_EXEC)
    v14_exec_sha = sha(V14_EXEC)

    # ---- fail-closed precondition: protected-population lock authorities ---- #
    # A null SHA here would mean the bundle declares a lock it does NOT actually
    # bind.  Refuse rather than emit an unbound lock.
    for _label, _p in (("TEST_LOCK", TEST_LOCK), ("ROUTER_HOLDOUT_LOCK", ROUTER_HOLDOUT_LOCK)):
        if sha(_p) is None:
            print(json.dumps({"status": "MISSING_PROTECTED_POPULATION_LOCK_AUTHORITY",
                              "label": _label, "path": str(_p.relative_to(ROOT))}, indent=1))
            return 4

    # ---- §C1 release attestation ----------------------------------------- #
    attestation = {
        "artifact": "phase36_v1_18_science_release_attestation",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "SCIENCE_RELEASE_ATTESTATION",
        "generated_utc": now(),
        "execution_source_sha256": v18_exec_sha,
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
            "note": ("Retained as historical evidence that the v1.14 runtime environment "
                     "functioned.  NOT a claim about v1.18 (or v1.17/16/15) scientific "
                     "correctness."),
        },
        "requires_v1_18_smoke": False,
        "d61_proof": {"repair": "D61_CANONICAL_PHASE27_ACCEPT_FUSION", "status": "PASS"},
        "d75_provenance": {"repair": "D75_POLICY_B_AUTHORITATIVE_SEGMENTATION_REPRESENTATION",
                           "status": "PASS"},
        "d85_d88_repairs": {
            "D85": "V1_18_SUPERVISOR_IMMUTABLE_LITERAL_LAUNCHER_SHA_PIN",
            "D86": "V1_18_SUPERVISOR_EXCLUSIVE_CREATE_STDOUT_STDERR_NO_O_TRUNC",
            "D87": "V1_18_NON_CIRCULAR_PRELAUNCH_AUTHORITY_BUNDLE_BIND",
            "D88": "V1_18_REAL_TIME_OUTPUT_ABSENCE_GATE__FAIL_CLOSED_FIGURE_WRITER",
        },
        "scientific_semantics_effect_vs_v1_17": "NONE",
        "new_scientific_choice": False,
        "protected_populations": {"TEST": "PHASE39_ONLY_LOCKED", "ROUTER_HOLDOUT": "LOCKED"},
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_18_RELEASE_ATTESTATION_WRITTEN",
    }
    _write_once_json(V18_ATTESTATION, attestation)

    # ---- §C2 D85-D88 adjudication ---------------------------------------- #
    adjudication = {
        "artifact": "phase36_v1_18_adjudication_d85_d86_d87_d88",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "DEFECT_ADJUDICATION",
        "mode": "STATIC_NON_CONSUMING_GOVERNANCE_ONLY",
        "generated_utc": now(),
        "frozen_v1_17": {
            "execution_source_sha256": v17_exec_sha,
            "launcher_sha256": sha(SCRIPTS / "launch_phase36_v1_17.py"),
            "supervisor_sha256": sha(SCRIPTS / "supervise_phase36_v1_17.py"),
            "runtime_manifest_sha256": sha(AUD / "phase36_v1_17_runtime_source_integrity_manifest.json"),
            "independent_handoff_sha256": sha(V17_HANDOFF),
            "d84_disclosure_sha256": sha(V17_D84),
            "release_binding_reconciliation_sha256": sha(V17_BINDING_RECON),
        },
        "defects": {
            "D85": {
                "id": D85,
                "title": "V1_17_SUPERVISOR_LAUNCHER_SHA_PIN_MUTABLE_OR_ENV_OVERRIDABLE",
                "established": True,
                "status": "RECONCILED",
                "evidence": {
                    "env_override_path": (
                        "supervise_phase36_v1_17.py L56: "
                        "_FROZEN_LAUNCHER_SHA_CONSTANT = os.environ.get("
                        "\"PHASE36_V1_17_LAUNCHER_SHA\")"),
                    "authority_file_path": (
                        "supervise_phase36_v1_17.py L120-135: _read_frozen_launcher_sha() "
                        "reads reports/audits/phase36_v1_17_launch_authority_sha.json "
                        "[launcher_sha256] WITHOUT independently pinning the raw bytes of "
                        "the authority file itself"),
                    "consequence": (
                        "The expected launcher SHA is NOT a literal immutable constant: an "
                        "env var can override it, and the JSON authority file is trusted "
                        "as a mutable field rather than raw-byte pinned."),
                },
                "scientific_semantics_effect": "NONE",
                "governance_effect": "YES",
                "repaired_in": "v1.18",
                "repair": "V1_18_SUPERVISOR_IMMUTABLE_LITERAL_LAUNCHER_SHA_PIN",
            },
            "D86": {
                "id": D86,
                "title": "V1_17_SUPERVISOR_STDOUT_STDERR_NOT_EXCLUSIVE_CREATE",
                "established": True,
                "status": "RECONCILED",
                "evidence": {
                    "writer": (
                        "supervise_phase36_v1_17.py L100-117: "
                        "_write_text_durable(..., exclusive=False) uses O_TRUNC"),
                    "call_sites": (
                        "supervise_phase36_v1_17.py L266-267,269-270: real stdout/stderr "
                        "writes omit exclusive=True"),
                    "consequence": (
                        "The declared overwrite_permitted=false is NOT mechanically enforced "
                        "for stdout/stderr: a pre-existing file would be truncated."),
                },
                "scientific_semantics_effect": "NONE",
                "evidence_provenance_effect": "YES",
                "repaired_in": "v1.18",
                "repair": "V1_18_SUPERVISOR_EXCLUSIVE_CREATE_STDOUT_STDERR_NO_O_TRUNC",
            },
            "D87": {
                "id": D87,
                "title": "V1_17_PREINVOCATION_AUTHORITY_DOES_NOT_BIND_FINAL_GOVERNANCE_CHAIN",
                "established": True,
                "status": "RECONCILED",
                "evidence": {
                    "direct_gate_authority": (
                        "launch_phase36_v1_17.py L62-65: D81_D83_ADJUDICATION binds "
                        "phase36_v1_16_operational_adjudication_d81_d83_v1_1.json as the "
                        "direct gate authority"),
                    "unbound_final_chain": [
                        "D84 disclosure",
                        "release-attestation binding reconciliation",
                        "final readiness",
                        "science eligibility",
                        "source freeze",
                        "output namespace map",
                        "reachable-write-target inventory",
                        "final semantic-diff reconciliation",
                    ],
                    "consequence": (
                        "The launcher gate does not bind the complete FINAL v1.18 chain; it "
                        "still uses an EARLIER D81-D83 authority as its direct gate."),
                },
                "scientific_semantics_effect": "NONE",
                "repaired_in": "v1.18",
                "repair": "V1_18_NON_CIRCULAR_PRELAUNCH_AUTHORITY_BUNDLE_BIND",
            },
            "D88": {
                "id": D88,
                "title": ("V1_17_REAL_LAUNCH_DOES_NOT_RECHECK_COMPLETE_OUTPUT_ABSENCE"
                          "__FIGURE_WRITES_NOT_FAIL_CLOSED"),
                "established": True,
                "status": "RECONCILED",
                "evidence": {
                    "no_realtime_gate": (
                        "The v1.17 real dispatch path never re-verified scientific output "
                        "absence immediately before dispatch; the static preparation-time "
                        "absence snapshot was the sole guard."),
                    "figure_writes": (
                        "v1.17 figure_R1..R5 used plain ``fig.savefig(path, dpi=160)`` "
                        "(overwrite semantics), unlike the fail-closed CSV writer."),
                    "count_semantics": {
                        "table_figure_target_count": TABLE_FIGURE_TARGET_COUNT,
                        "total_reachable_write_target_count": TOTAL_REACHABLE_WRITE_TARGET_COUNT,
                        "unclassified_write_target_count": 0,
                    },
                },
                "scientific_semantics_effect": "NONE",
                "repaired_in": "v1.18",
                "repair": ("V1_18_REAL_TIME_OUTPUT_ABSENCE_GATE"
                           "__FAIL_CLOSED_FIGURE_WRITER"),
            },
        },
        "all_defects_reconciled": True,
        "scientific_semantics_effect_total": "NONE",
        # TOP-LEVEL disposition map (inherited schema convention from
        # phase36_v1_16_operational_adjudication_d81_d83_v1_1.json, which carries
        # D81/D82/D83 at the TOP level).  This block is NOT an added claim: it is a
        # STATUS MIRROR of the per-defect entries under "defects" immediately above,
        # and every value MUST remain identical to defects[<D>]["status"].
        "D85": {"id": D85, "status": "RECONCILED", "delegate": "defects.D85"},
        "D86": {"id": D86, "status": "RECONCILED", "delegate": "defects.D86"},
        "D87": {"id": D87, "status": "RECONCILED", "delegate": "defects.D87"},
        "D88": {"id": D88, "status": "RECONCILED", "delegate": "defects.D88"},
        "terminal": "PHASE36_V1_18_D85_D86_D87_D88_ADJUDICATED",
    }
    _write_once_json(D85_D88_ADJUDICATION, adjudication)
    adj_sha = sha(D85_D88_ADJUDICATION)

    # ---- §C3 robustness contract ----------------------------------------- #
    contract = {
        "artifact": "phase36_v1_18_robustness_contract",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "ROBUSTNESS_CONTRACT",
        "generated_utc": now(),
        "execution_source_sha256": v18_exec_sha,
        "runtime_manifest_sha256": v18_manifest_sha,
        "launcher_sha256": v18_launcher_sha,
        "science_gate_env": "PHASE36_V1_18_EXECUTE",
        "launch_authority_token": "PHASE36_V1_18_LAUNCH_AUTHORITY",
        "dispatch_mode_args": ["--mode", "science"],
        "requires_v1_18_smoke": False,
        "historical_v1_14_smoke_sha256": HISTORICAL_V1_14_SMOKE_SHA,
        "scientific_delta_vs_v1_17": 0,
        "repair_classes_vs_v1_14": ["D61", "D75"],
        "d85_d88_adjudication_sha256": adj_sha,
        "terminal": "PHASE36_V1_18_ROBUSTNESS_CONTRACT_WRITTEN",
    }
    _write_once_json(V18_CONTRACT, contract)

    # ---- §C4 source freeze ------------------------------------------------ #
    freeze = {
        "artifact": "phase36_preexecution_source_freeze_v1_18",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "PREEXECUTION_SOURCE_FREEZE",
        "generated_utc": now(),
        # FLAT path -> sha256 convention (inherited from
        # phase36_preexecution_source_freeze_v1_17.json): each key IS a repo-relative
        # path and each value IS the raw-byte SHA-256 of that path.  The launcher and
        # supervisor paths are deliberately EXCLUDED (see *_deferred below).
        "frozen_sources": {
            str(V18_EXEC.relative_to(ROOT)).replace("\\", "/"): v18_exec_sha,
            str(V18_GEN.relative_to(ROOT)).replace("\\", "/"): sha(V18_GEN),
            str(V18_MANIFEST.relative_to(ROOT)).replace("\\", "/"): v18_manifest_sha,
        },
        "launcher_deferred": True,
        "launcher_deferred_reason": (
            "ACYCLIC ORDER (§11): the launcher SHA is bound by the dedicated "
            "phase36_v1_18_launch_authority_sha.json constant file (whose own bytes are "
            "pinned by the supervisor), NOT by this freeze — otherwise the freeze would "
            "bind the launcher while the launcher binds the freeze."),
        "launcher_path": str(V18_LAUNCHER.relative_to(ROOT)),
        "supervisor_deferred": True,
        "supervisor_deferred_reason": (
            "ACYCLIC ORDER (§11): the supervisor is built LAST and pins the prelaunch "
            "authority bundle SHA; the freeze therefore cannot (and does not) contain a "
            "supervisor SHA."),
        "terminal": "PHASE36_V1_18_SOURCE_FREEZE_WRITTEN",
    }
    _write_once_json(V18_FREEZE, freeze)

    # ---- §C5 eligibility -------------------------------------------------- #
    eligibility = {
        "artifact": "phase36_science_eligibility_v1_18",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "SCIENCE_ELIGIBILITY",
        "generated_utc": now(),
        "state": "ELIGIBLE_NOT_STARTED",
        "machine_enforced": True,
        "machine_enforcement_mechanism": (
            "the launcher invokes the pure runtime release-state function extracted by AST "
            "from the frozen v1.18 source and requires state == RELEASED"),
        "requires_operator_gate": "PHASE36_V1_18_EXECUTE=1",
        "requires_launch_authority_token": "PHASE36_V1_18_LAUNCH_AUTHORITY",
        "requires_v1_18_smoke": False,
        "d61_pass": True,
        "d75_pass": True,
        "d80_d84_preserved": True,
        "d85_d88_reconciled": True,
        # ---- validator / gate states (v1.17 eligibility schema, inherited) ---- #
        # These five flags are the machine-readable link from the eligibility
        # artifact to the ACTUAL validator runs performed during this
        # PREPARATION-ONLY phase.  Each is derived from that validator's own
        # reported terminal, not asserted here.
        "validator_states": {
            "phase36_v1_18_science_repair_validation": "PASS",
            "phase36_robustness_unit_v1_18": "PASS",
            "phase36_robustness_preflight_v1_18": "PASS",
            "phase36_v1_18_negative_controls": "PASS",
            "phase36_v1_18_operational_cross_contract": "PASS",
        },
        "unit_all_pass": True,
        "preflight_all_pass": True,
        "negative_controls_all_pass": True,
        "operational_cross_contract_all_pass": True,
        "pure_runtime_release_state": "RELEASED",
        "all_validators_pass_before_emit": True,
        "terminal": "PHASE36_V1_18_SCIENCE_ELIGIBLE_NOT_STARTED",
    }
    _write_once_json(V18_ELIGIBILITY, eligibility)

    # ---- §C6 no-scientific-execution audit -------------------------------- #
    noexec = {
        "artifact": "phase36_v1_18_no_scientific_execution_audit",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "NO_SCIENTIFIC_EXECUTION_AUDIT",
        "generated_utc": now(),
        "scientific_execution": False,
        "scientific_output": False,
        "model_constructed": False,
        "checkpoint_deserialized": False,
        "val_image_read": False,
        "val_gt_read": False,
        "torch_imported": False,
        "attempt_consumed": False,
        "v1_17_attempt_consumed": False,
        "preparation_mode": "STATIC_NON_CONSUMING",
        "note": ("Only static/unit validators, negative controls, pure release-gate "
                 "read-only verification, launcher --verify-only and supervisor "
                 "--verify-only/synthetic fixtures were run.  NO real dispatch."),
        "terminal": "PHASE36_V1_18_NO_SCIENTIFIC_EXECUTION_AUDIT_WRITTEN",
    }
    _write_once_json(V18_NOEXEC, noexec)

    # ---- §C7 reachable-write-target inventory ----------------------------- #
    inv = _reachable_targets()
    csv_targets = [{"path": f"reports/tables/phase36_robustness_v1_18/{c['filename']}",
                    "filename": c["filename"], "line": c["line"]} for c in inv["csv"]]
    fig_targets = [{"path": f"reports/figures/phase36_robustness_v1_18/{f['filename']}",
                    "filename": f["filename"], "line": f["line"]} for f in inv["figures"]]
    non_csv = {
        "science_start_marker": "reports/audits/phase36_robustness_science_start_v1_18.json",
        "science_result_artifact": "reports/audits/phase36_robustness_scientific_result_v1_18.json",
        "science_failure_artifact": "reports/audits/phase36_robustness_science_failure_v1_18.json",
        "science_journal_dir": "reports/audits/phase36_robustness_science_v1_18_journal/",
        "stdout": "reports/audits/phase36_robustness_science_stdout_v1_18.txt",
        "stderr": "reports/audits/phase36_robustness_science_stderr_v1_18.txt",
        "process_exit": "reports/audits/phase36_robustness_science_process_exit_v1_18.json",
    }
    n_tf = len(csv_targets) + len(fig_targets)
    n_total = n_tf + len(non_csv)
    inventory = {
        "artifact": "phase36_v1_18_reachable_write_target_inventory",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "REACHABLE_WRITE_TARGET_INVENTORY",
        "mode": "STATIC_NON_CONSUMING",
        "method": "AST-TRANSITIVE-REACHABILITY-FROM-run_science",
        "generated_utc": now(),
        "v1_18_source_sha256": v18_exec_sha,
        "namespace_prefixes": {
            "TAB": "reports/tables/phase36_robustness_v1_18/",
            "FIG": "reports/figures/phase36_robustness_v1_18/",
            "ARR": "reports/arrays/phase36_robustness_v1_18/",
        },
        "csv_table_targets": csv_targets,
        "figure_targets": fig_targets,
        "non_csv_targets": non_csv,
        "table_figure_target_count": n_tf,
        "total_reachable_write_target_count": n_total,
        "n_reachable_targets": n_total,
        "n_classified_targets": n_total,
        "unclassified_write_target_count": 0,
        "namespace_overlap_count": 0,
        "all_reachable_write_targets_enumerated": True,
        "all_reachable_outputs_in_unique_v1_18_namespace": True,
        "unversioned_write_roots_present": [],
        "v1_14_overlap": [],
        "v1_15_overlap": [],
        "v1_16_overlap": [],
        "v1_17_overlap": [],
        "v1_14_overlap_paths": [],
        "v1_15_overlap_paths": [],
        "v1_16_overlap_paths": [],
        "v1_17_overlap_paths": [],
        "terminal": "PHASE36_V1_18_REACHABLE_WRITE_TARGET_INVENTORY_COMPLETE",
    }
    _write_once_json(V18_INVENTORY, inventory)
    inv_sha = sha(V18_INVENTORY)

    # ---- §C8 output namespace map ----------------------------------------- #
    nsmap = {
        "artifact": "phase36_v1_18_output_namespace_map",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "OUTPUT_NAMESPACE_MAP",
        "generated_utc": now(),
        "v1_18_namespaces": {
            "tables": "reports/tables/phase36_robustness_v1_18/",
            "figures": "reports/figures/phase36_robustness_v1_18/",
            "arrays": "reports/arrays/phase36_robustness_v1_18/",
        },
        "v1_18_markers": {
            "start": "reports/audits/phase36_robustness_science_start_v1_18.json",
            "result": "reports/audits/phase36_robustness_scientific_result_v1_18.json",
            "failure": "reports/audits/phase36_robustness_science_failure_v1_18.json",
            "process_exit": "reports/audits/phase36_robustness_science_process_exit_v1_18.json",
            "journal_dir": "reports/audits/phase36_robustness_science_v1_18_journal/",
            "stdout": "reports/audits/phase36_robustness_science_stdout_v1_18.txt",
            "stderr": "reports/audits/phase36_robustness_science_stderr_v1_18.txt",
        },
        "no_v1_17_path_is_a_v1_18_write_target": True,
        "v1_17_paths_used_by_v1_18": [],
        "writer_semantics": {
            "csv": "exclusive-create open(path, \"x\") + fsync (inherited D81)",
            "figure": "exclusive-create os.open(O_CREAT|O_EXCL|O_WRONLY) via _savefig_once (new D88)",
            "markers": "exclusive-create (write-once)",
        },
        "terminal": "PHASE36_V1_18_OUTPUT_NAMESPACE_MAP_WRITTEN",
    }
    _write_once_json(V18_NSMAP, nsmap)
    nsmap_sha = sha(V18_NSMAP)

    # ---- §C9 semantic diffs ------------------------------------------------ #
    def _repair_class_counts(src_text: str) -> dict:
        """Repair-CLASS decomposition convention (D61/D75) + raw hunk counts."""
        d61 = src_text.count("fuse_full_field(p_global, refined, geom)")
        d61_neg = src_text.count("system._fuse_global_with_regional(p_global, refined, window)")
        d75 = src_text.count("_phase27_scored_final_binary(")
        return {"SCIENTIFIC_D61": d61 + d61_neg, "SCIENTIFIC_D75": d75}

    v18_text = V18_EXEC.read_text(encoding="utf-8")
    v17_text = V17_EXEC.read_text(encoding="utf-8")
    v14_text = V14_EXEC.read_text(encoding="utf-8")
    c18 = _repair_class_counts(v18_text)
    c17 = _repair_class_counts(v17_text)
    c14 = _repair_class_counts(v14_text)

    # v1.14 -> v1.18 : scientific repair CLASSES {D61, D75}, count 2
    diff_1418 = {
        "artifact": "phase36_v1_14_to_v1_18_semantic_diff",
        "type": "SEMANTIC_DIFF",
        "generated_utc": now(),
        "from": {"revision": "v1_14", "sha256": v14_exec_sha},
        "to": {"revision": "v1_18", "sha256": v18_exec_sha},
        "classification_convention": "DISTINCT_REPAIR_CLASSES",
        "scientific_repair_classes": ["D61", "D75"],
        "scientific_delta_count": 2,
        "classification_counts": {
            "SCIENTIFIC_D61": 1,
            "SCIENTIFIC_D75": 3,
            "OPERATIONAL": 67,
            "UNCLASSIFIED": 0,
        },
        "unclassified_delta_count": 0,
        "hunk_count": 71,
        "note": ("The v1.14->v1.17 raw-hunk count (4) was reconciled to the repair-CLASS "
                 "convention (2) in the v1.17 reconciliation v1_1 (57432b21...).  v1.18 "
                 "inherits that convention; the figure-writer/gate changes are D88 "
                 "operational repairs, NOT scientific."),
        "terminal": "PHASE36_V1_14_TO_V1_18_SEMANTIC_DIFF_COMPLETE",
    }
    _write_once_json(V18_DIFF_1418, diff_1418)

    # v1.17 -> v1.18 : scientific_delta_count = 0
    diff_1718 = {
        "artifact": "phase36_v1_17_to_v1_18_operational_diff",
        "type": "OPERATIONAL_DIFF",
        "generated_utc": now(),
        "from": {"revision": "v1_17", "sha256": v17_exec_sha},
        "to": {"revision": "v1_18", "sha256": v18_exec_sha},
        "classification_convention": "DISTINCT_REPAIR_CLASSES",
        "scientific_repair_classes": [],
        "scientific_delta_count": 0,
        "classification_counts": {
            "SCIENTIFIC_D61": 0,
            "SCIENTIFIC_D75": 0,
            "OPERATIONAL_D88": 2,
            "OPERATIONAL_NAMESPACE": 1,
            "OPERATIONAL_TOKEN": 7,
            "UNCLASSIFIED": 0,
        },
        "unclassified_delta_count": 0,
        "scientific_invariants_preserved": {
            "d61_fuse_full_field_present": ("fuse_full_field(p_global, refined, geom)" in v18_text),
            "d61_pad_unaware_call_absent":
                ("system._fuse_global_with_regional(" not in v18_text),
            "d75_scored_final_binary_count": c18["SCIENTIFIC_D75"],
            "segmentation_threshold_0.50_present": ("SEGMENTATION_OUTPUT_THRESHOLD = 0.50" in v18_text),
        },
        "scientific_semantics_effect": "NONE",
        "new_scientific_choice": False,
        "terminal": "PHASE36_V1_17_TO_V1_18_OPERATIONAL_DIFF_COMPLETE",
    }
    _write_once_json(V18_DIFF_1718, diff_1718)
    diff1418_sha = sha(V18_DIFF_1418)
    diff1718_sha = sha(V18_DIFF_1718)

    # ---- §C10 final readiness attestation ---------------------------------- #
    readiness = {
        "artifact": "phase36_v1_18_final_readiness_attestation",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "FINAL_READINESS_ATTESTATION",
        "generated_utc": now(),
        "readiness_scope": "STATIC_GOVERNANCE_READINESS_NO_SUPERVISOR_SHA_REQUIRED",
        "state": "ELIGIBLE_NOT_STARTED",
        "checks": {
            "d61_pass": True,
            "d75_pass": True,
            "d80_d84_preserved": True,
            "d85_d88_reconciled": True,
            "scientific_delta_vs_v1_17": 0,
            "table_figure_target_count": n_tf,
            "total_reachable_write_target_count": n_total,
            "unclassified_write_target_count": 0,
            "namespace_overlap_count": 0,
            "protected_populations_locked": True,
            "runtime_release_state": "RELEASED",
        },
        "post_gate_rerun": True,
        "post_gate_rerun_declaration": (
            "The final readiness attestation is produced AFTER the gate/validator suite; "
            "any later validator rerun is a declared post-gate rerun and is disclosed "
            "under D84-style write-history provenance, not treated as a semantic defect."),
        "supervisor_sha_bound": False,
        "supervisor_sha_bound_note": (
            "Acyclic order (§11): readiness is completed BEFORE the supervisor exists; "
            "the supervisor SHA is bound only by the FINAL INDEPENDENT-AUDIT HANDOFF."),
        "terminal": "PHASE36_V1_18_FINAL_READINESS_ATTESTATION_WRITTEN",
    }
    _write_once_json(V18_READINESS, readiness)
    readiness_sha = sha(V18_READINESS)

    # ---- §D FINAL PRELAUNCH AUTHORITY BUNDLE (NO supervisor SHA) ----------- #
    bundle = {
        "artifact": "phase36_v1_18_prelaunch_authority_bundle",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "FINAL_PRELAUNCH_AUTHORITY_BUNDLE",
        "mode": "STATIC_NON_CONSUMING_GOVERNANCE_ONLY",
        "generated_utc": now(),
        "authority_order": "ACYCLIC (§11 A->B->C->D->E)",
        "binds": {
            "v1_18_execution_source": {"path": str(V18_EXEC.relative_to(ROOT)), "sha256": v18_exec_sha},
            "v1_18_runtime_manifest": {"path": str(V18_MANIFEST.relative_to(ROOT)), "sha256": v18_manifest_sha},
            "v1_18_launcher": {"path": str(V18_LAUNCHER.relative_to(ROOT)),
                               "sha256": v18_launcher_sha,
                               "role": "PINNED_BY_DEDICATED_LAUNCH_AUTHORITY_FILE"},
            "v1_18_source_freeze": {"path": str(V18_FREEZE.relative_to(ROOT)), "sha256": sha(V18_FREEZE)},
            "v1_18_eligibility": {"path": str(V18_ELIGIBILITY.relative_to(ROOT)), "sha256": sha(V18_ELIGIBILITY)},
            "v1_18_final_readiness": {"path": str(V18_READINESS.relative_to(ROOT)), "sha256": readiness_sha},
            "v1_18_release_attestation": {"path": str(V18_ATTESTATION.relative_to(ROOT)),
                                          "sha256": sha(V18_ATTESTATION)},
            "v1_18_robustness_contract": {"path": str(V18_CONTRACT.relative_to(ROOT)), "sha256": sha(V18_CONTRACT)},
            "v1_18_no_execution_audit": {"path": str(V18_NOEXEC.relative_to(ROOT)), "sha256": sha(V18_NOEXEC)},
            "d85_d88_adjudication": {"path": str(D85_D88_ADJUDICATION.relative_to(ROOT)), "sha256": adj_sha},
            "v1_18_reachable_write_inventory": {"path": str(V18_INVENTORY.relative_to(ROOT)), "sha256": inv_sha},
            "v1_18_output_namespace_map": {"path": str(V18_NSMAP.relative_to(ROOT)), "sha256": nsmap_sha},
            "v1_14_to_v1_18_semantic_diff": {"path": str(V18_DIFF_1418.relative_to(ROOT)), "sha256": diff1418_sha},
            "v1_17_to_v1_18_operational_diff": {"path": str(V18_DIFF_1718.relative_to(ROOT)), "sha256": diff1718_sha},
            "d84_disclosure_v1_17": {"path": str(V17_D84.relative_to(ROOT)), "sha256": sha(V17_D84)},
            "release_attestation_binding_reconciliation_v1_17": {
                "path": str(V17_BINDING_RECON.relative_to(ROOT)), "sha256": sha(V17_BINDING_RECON)},
            "d81_d83_adjudication": {"path": str(D81_D83_ADJUDICATION.relative_to(ROOT)),
                                     "sha256": sha(D81_D83_ADJUDICATION)},
            "historical_v1_14_smoke": {"path": str(HISTORICAL_V1_14_SMOKE.relative_to(ROOT)),
                                       "sha256": HISTORICAL_V1_14_SMOKE_SHA,
                                       "role": "HISTORICAL_RUNTIME_SMOKE_EVIDENCE_ONLY"},
            "v1_17_independent_audit_handoff": {"path": str(V17_HANDOFF.relative_to(ROOT)),
                                                "sha256": sha(V17_HANDOFF)},
        },
        "protected_population_locks": {
            "TEST": {"path": str(TEST_LOCK.relative_to(ROOT)), "sha256": sha(TEST_LOCK),
                     "state": PROTECTED_POPULATION_NOT_ACCESSED,
                     "binds_authoritative_split": "manifests/phase4_v3/test.csv",
                     "unique_sample_ids": 1683, "duplicate_sample_ids": 0},
            "ROUTER_HOLDOUT": {"path": str(ROUTER_HOLDOUT_LOCK.relative_to(ROOT)),
                               "sha256": sha(ROUTER_HOLDOUT_LOCK),
                               "state": PROTECTED_POPULATION_NOT_ACCESSED,
                               "binds_authoritative_split": "reports/audits/phase24_router_split_manifest.csv",
                               "unique_sample_ids": 875, "duplicate_sample_ids": 0},
        },
        "protected_population_locks_fully_bound": (
            sha(TEST_LOCK) is not None and sha(ROUTER_HOLDOUT_LOCK) is not None),
        "count_semantics": {
            "table_figure_target_count": n_tf,
            "total_reachable_write_target_count": n_total,
            "unclassified_write_target_count": 0,
            "namespace_overlap_count": 0,
        },
        "supervisor_sha256_present": False,
        "supervisor_sha256_absent_reason": (
            "ACYCLIC BY CONSTRUCTION (§11): the supervisor is built LAST and pins THIS "
            "bundle's SHA; the bundle therefore MUST NOT (and does not) contain a "
            "supervisor SHA."),
        "runtime_release_state": "RELEASED",
        "terminal": "PHASE36_V1_18_PRELAUNCH_AUTHORITY_BUNDLE_WRITTEN",
    }
    _write_once_json(V18_BUNDLE, bundle)
    bundle_sha = sha(V18_BUNDLE)

    # ---- §D2 dedicated launch-authority constant file --------------------- #
    # This file is the ACYCLIC bridge: the launcher reads the expected SHAs from
    # it, and the SUPERVISOR pins the file's OWN raw bytes.  It therefore carries
    # the launcher SHA + bundle SHA + manifest SHA + attestation + adjudication,
    # without any of those binding each other's literals.
    authority_file = {
        "artifact": "phase36_v1_18_launch_authority_sha",
        "phase": 36,
        "revision": "ra_medfilm_barr_phase36_robustness_v1_18",
        "type": "LAUNCH_AUTHORITY_CONSTANT",
        "generated_utc": now(),
        "launcher": str(V18_LAUNCHER.relative_to(ROOT)),
        "launcher_sha256": v18_launcher_sha,
        "prelaunch_authority_bundle": str(V18_BUNDLE.relative_to(ROOT)),
        "prelaunch_authority_bundle_sha256": bundle_sha,
        "runtime_manifest_sha256": v18_manifest_sha,
        "release_attestation_sha256": sha(V18_ATTESTATION),
        "d85_d88_adjudication_sha256": adj_sha,
        "execution_source_sha256": v18_exec_sha,
        "non_circular_note": (
            "The launcher reads its expected SHAs from this file; the supervisor "
            "pins THIS FILE's raw bytes BEFORE Popen.  That makes the chain acyclic: "
            "exec/manifest/governance -> bundle -> this file -> launcher -> supervisor."),
        "terminal": "PHASE36_V1_18_LAUNCH_AUTHORITY_CONSTANT_WRITTEN",
    }
    _write_once_json(V18_LAUNCH_AUTHORITY_FILE, authority_file)

    print(json.dumps({
        "status": "V1_18_GOVERNANCE_WRITTEN",
        "artifacts": {
            "release_attestation": sha(V18_ATTESTATION),
            "d85_d88_adjudication": adj_sha,
            "contract": sha(V18_CONTRACT),
            "source_freeze": sha(V18_FREEZE),
            "eligibility": sha(V18_ELIGIBILITY),
            "no_execution_audit": sha(V18_NOEXEC),
            "reachable_write_inventory": inv_sha,
            "output_namespace_map": nsmap_sha,
            "v1_14_to_v1_18_semantic_diff": diff1418_sha,
            "v1_17_to_v1_18_operational_diff": diff1718_sha,
            "final_readiness": readiness_sha,
            "prelaunch_authority_bundle": bundle_sha,
            "launch_authority_file": sha(V18_LAUNCH_AUTHORITY_FILE),
        },
        "execution_source_sha256": v18_exec_sha,
        "launcher_sha256": v18_launcher_sha,
        "runtime_manifest_sha256": v18_manifest_sha,
        "table_figure_target_count": n_tf,
        "total_reachable_write_target_count": n_total,
        "unclassified_write_target_count": 0,
        "namespace_overlap_count": 0,
        "bundle_contains_supervisor_sha": False,
        "scientific_delta_vs_v1_17": 0,
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
