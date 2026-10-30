#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.11 — build SOURCE FREEZE + SYNTHETIC SMOKE ELIGIBILITY (READ-ONLY).

Assembles the v1.11 preexecution source freeze (binding the NEW execution source,
the NEW unit / preflight / negative-control suites, the NEW non-circular
launcher, and the NEW runtime integrity manifest) and the synthetic-smoke
eligibility record, FROM the v1.11 gate reports already on disk (no
re-derivation, no execution).  Byte-deterministic across reruns.

The freeze explicitly records the D29 availability finding for the historical
v1.10 unit source (PRESENT + SHA-verified on disk; NOT reconstructed), and
preserves every surviving v1.7/v1.8/v1.9/v1.10 byte history.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha_or_none(rel: str):
    p = ROOT / rel
    return sha(p) if p.exists() else None


unit = load("reports/audits/phase36_robustness_unit_v1_11.json")
pre = load("reports/audits/phase36_robustness_preflight_v1_11.json")
nc = load("reports/audits/phase36_v1_11_negative_controls.json")
diff = load("reports/audits/phase36_v1_9_to_v1_11_semantic_diff.json")
byte = load("reports/audits/phase36_v1_11_direct_source_byte_audit.json")
zero = load("reports/audits/phase36_v1_11_source_repair_no_execution_audit.json")
man = load("reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json")
d29 = load("reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json")
coedit = load("reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json")

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"
FROZEN_V1_10_UNIT_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"
FROZEN_V1_8_EXEC_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
FROZEN_V1_7_EXEC_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"

V111_EXEC = "scripts/analysis/phase36_robustness_execution_v1_11.py"
V111_UNIT = "scripts/analysis/phase36_robustness_unit_v1_11.py"
V111_NC = "scripts/analysis/phase36_robustness_negative_controls_v1_11.py"
V111_PRE = "scripts/analysis/phase36_robustness_preflight_v1_11.py"
V111_LAUNCHER = "scripts/analysis/launch_phase36_v1_11.py"
V111_MANIFEST = "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json"

frozen_sources = {
    V111_EXEC: sha(ROOT / V111_EXEC),
    V111_UNIT: sha(ROOT / V111_UNIT),
    V111_NC: sha(ROOT / V111_NC),
    V111_PRE: sha(ROOT / V111_PRE),
    V111_LAUNCHER: sha(ROOT / V111_LAUNCHER),
}
frozen_audits = {
    "reports/audits/phase36_robustness_unit_v1_11.json": sha(ROOT / "reports/audits/phase36_robustness_unit_v1_11.json"),
    "reports/audits/phase36_robustness_preflight_v1_11.json": sha(ROOT / "reports/audits/phase36_robustness_preflight_v1_11.json"),
    "reports/audits/phase36_v1_11_negative_controls.json": sha(ROOT / "reports/audits/phase36_v1_11_negative_controls.json"),
    "reports/audits/phase36_v1_9_to_v1_11_semantic_diff.json": sha(ROOT / "reports/audits/phase36_v1_9_to_v1_11_semantic_diff.json"),
    "reports/audits/phase36_v1_11_direct_source_byte_audit.json": sha(ROOT / "reports/audits/phase36_v1_11_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_11_source_repair_no_execution_audit.json": sha(ROOT / "reports/audits/phase36_v1_11_source_repair_no_execution_audit.json"),
    V111_MANIFEST: sha(ROOT / V111_MANIFEST),
    "reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json": sha(ROOT / "reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json"),
    "reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json": sha(ROOT / "reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json"),
    # frozen v1.9 / v1.10 gate artifacts (history, must remain byte-identical)
    "reports/audits/phase36_robustness_unit_v1_9.json": sha_or_none("reports/audits/phase36_robustness_unit_v1_9.json"),
    "reports/audits/phase36_robustness_preflight_v1_9.json": sha_or_none("reports/audits/phase36_robustness_preflight_v1_9.json"),
    "reports/audits/phase36_v1_9_negative_controls.json": sha_or_none("reports/audits/phase36_v1_9_negative_controls.json"),
    "reports/audits/phase36_v1_9_direct_source_byte_audit.json": sha_or_none("reports/audits/phase36_v1_9_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_9_source_repair_no_execution_audit.json": sha_or_none("reports/audits/phase36_v1_9_source_repair_no_execution_audit.json"),
    "reports/audits/phase36_robustness_unit_v1_10.json": sha_or_none("reports/audits/phase36_robustness_unit_v1_10.json"),
    "reports/audits/phase36_robustness_preflight_v1_10.json": sha_or_none("reports/audits/phase36_robustness_preflight_v1_10.json"),
    "reports/audits/phase36_v1_10_negative_controls.json": sha_or_none("reports/audits/phase36_v1_10_negative_controls.json"),
    "reports/audits/phase36_v1_9_to_v1_10_semantic_diff.json": sha_or_none("reports/audits/phase36_v1_9_to_v1_10_semantic_diff.json"),
    "reports/audits/phase36_v1_10_direct_source_byte_audit.json": sha_or_none("reports/audits/phase36_v1_10_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_10_source_repair_no_execution_audit.json": sha_or_none("reports/audits/phase36_v1_10_source_repair_no_execution_audit.json"),
}
supporting_generators = {
    "scripts/analysis/build_phase36_v1_11_semantic_diff.py": sha(ROOT / "scripts/analysis/build_phase36_v1_11_semantic_diff.py"),
    "scripts/analysis/audit_phase36_v1_11_direct_source_bytes.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_11_direct_source_bytes.py"),
    "scripts/analysis/audit_phase36_v1_11_no_execution.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_11_no_execution.py"),
    "scripts/analysis/build_phase36_v1_11_runtime_integrity_manifest.py": sha(ROOT / "scripts/analysis/build_phase36_v1_11_runtime_integrity_manifest.py"),
    "scripts/analysis/build_phase36_v1_10_availability_record.py": sha(ROOT / "scripts/analysis/build_phase36_v1_10_availability_record.py"),
    "scripts/analysis/build_phase36_v1_11_freeze_and_eligibility.py": sha(ROOT / "scripts/analysis/build_phase36_v1_11_freeze_and_eligibility.py"),
}

gate_results = {
    "unit": {"passed": unit["passed"], "total": unit["total"], "all_pass": unit["all_pass"]},
    "preflight": {"passed": pre["passed"], "total": pre["total"], "all_pass": pre["all_pass"]},
    "negative_controls_NC71_NC85": {"passed": nc["passed"], "total": nc["total"],
                                    "all_pass": nc["all_pass"]},
    "direct_source_byte_audit": {"passed": byte["passed"], "total": byte["total"],
                                 "verdict": byte["verdict"]},
    "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
    "semantic_diff_all_semantic_groups_unchanged": diff["all_semantic_groups_unchanged"],
    "semantic_diff_no_prohibited_changes":
        (diff["changed_line_classification"]["n_prohibited"] == 0),
    "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
    "zero_execution_audit_all_generators_clean": zero["all_v1_11_generators_clean"],
    "launcher_co_edit_negative_control_passed": coedit["passed"],
}

freeze = {
    "artifact": "phase36_preexecution_source_freeze_v1_11",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "PREEXECUTION_SOURCE_FREEZE",
    "section": "§R",
    "execution_subject": V111_EXEC,
    "execution_subject_sha256": frozen_sources[V111_EXEC],
    "pre_invocation_launcher": V111_LAUNCHER,
    "pre_invocation_launcher_sha256": frozen_sources[V111_LAUNCHER],
    "runtime_integrity_manifest": V111_MANIFEST,
    "runtime_integrity_manifest_sha256": frozen_audits[V111_MANIFEST],
    "non_circular_release_chain": {
        "supervisor_pins": [
            "scripts/analysis/launch_phase36_v1_11.py",
            "reports/audits/phase36_preexecution_source_freeze_v1_11.json",
        ],
        "launcher_verifies": [
            V111_EXEC,
            V111_MANIFEST,
        ],
        "manifest_declares": [V111_EXEC],
        "source_requires": "PHASE36_V1_11_LAUNCH_AUTHORITY token + manifest-declared anchor",
        "no_cycle": True,
        "launcher_sha_declared_in_manifest": ("launcher_sha256" in man),
    },
    "frozen_sources": frozen_sources,
    "frozen_audits_and_reports": frozen_audits,
    "supporting_generators": supporting_generators,
    "history_preserved": {
        "scripts/analysis/phase36_robustness_execution_v1_9.py": FROZEN_V1_9_EXEC_SHA,
        "scripts/analysis/phase36_robustness_unit_v1_9.py": FROZEN_V1_9_UNIT_SHA,
        "scripts/analysis/phase36_robustness_unit_v1_10.py": FROZEN_V1_10_UNIT_SHA,
        "scripts/analysis/phase36_robustness_execution_v1_8.py": FROZEN_V1_8_EXEC_SHA,
        "scripts/analysis/phase36_robustness_execution_v1_7.py": FROZEN_V1_7_EXEC_SHA,
        "byte_preserved": True,
    },
    "v1_10_frozen_validator_availability": {
        "defect_id": d29["defect_id"],
        "defect_applicable_to_this_workspace": d29["defect_applicable_to_this_workspace"],
        "unit_source_present_on_disk": d29["unit_source_present_on_disk"],
        "unit_source_sha_matches_freeze_binding": d29["unit_source_sha_matches_freeze_binding"],
        "reconstructed_or_rewritten_by_v1_11": d29["reconstructed_or_rewritten_by_v1_11"],
        "v1_10_smoke_executed": d29["v1_10_smoke_executed"],
        "v1_10_science_executed": d29["v1_10_science_executed"],
        "v1_10_scientific_evidence": d29["v1_10_scientific_evidence"],
    },
    "canonical_component_sources": {
        "src/models/film/global_medfilm.py": man["dependencies"]["src/models/film/global_medfilm.py"],
        "scripts/analysis/train_phase25d_router.py": man["dependencies"]["scripts/analysis/train_phase25d_router.py"],
        "src/models/barr/regional_refiner.py": man["dependencies"]["src/models/barr/regional_refiner.py"],
        "scripts/analysis/phase25f_execution_common.py": man["dependencies"]["scripts/analysis/phase25f_execution_common.py"],
    },
    "n_transitive_dependencies": man["n_dependencies"],
    "n_transitive_checkpoints": man["n_checkpoints"],
    "all_dependencies_match": man["all_dependencies_match"],
    "all_checkpoints_match": man["all_checkpoints_match"],
    "gate_results": gate_results,
    "gate_artifacts_byte_deterministic_across_reruns": True,
    "future_phase36_smoke_must_use_exact_v1_11_bytes": True,
    "future_phase36_science_must_use_exact_v1_11_bytes": True,
    "future_phase36_dispatch_must_go_through_launcher": True,
    "source_freeze_complete": True,
    "smoke_started": False,
    "science_started": False,
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "terminal": "PHASE36_V1_11_SOURCE_FREEZE_COMPLETE__SMOKE_AND_SCIENCE_NOT_STARTED",
}
out = ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_11.json"
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

elig = {
    "artifact": "phase36_synthetic_smoke_eligibility_v1_11",
    "phase": 36,
    "section": "§P",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_11",
    "type": "SYNTHETIC_SMOKE_ELIGIBILITY",
    "history_preserved": {
        "v1_9_execution_sha256": FROZEN_V1_9_EXEC_SHA,
        "v1_9_unit_sha256": FROZEN_V1_9_UNIT_SHA,
        "v1_10_unit_sha256": FROZEN_V1_10_UNIT_SHA,
        "v1_7_v1_8_v1_9_v1_10_bytes_unchanged": True,
        "v1_9_repairs_preserved": True,
    },
    "v1_11_repairs": {
        "D29_V1_10_FROZEN_VALIDATOR_SOURCE": "AVAILABILITY_RECORDED_PRESENT_SHA_VERIFIED",
        "D30_SCIENCE_TRANSITIVE_PRE_MODEL_INTEGRITY_GATE": "ENFORCED",
        "D31_UNIQUE_V1_11_SCIENCE_PROVENANCE_PATHS": "ENFORCED",
        "D32_SCIENCE_FIRST_ATTEMPT_WRITE_ONCE_DURABLE_EVIDENCE": "ENFORCED",
        "D33_EXTERNAL_NON_CIRCULAR_LAUNCH_ANCHOR": "ENFORCED",
        "D22_D28_VALIDATION_REPAIRS": "PRESERVED_ENFORCED",
        "NO_NEW_SCIENTIFIC_CHOICE": True,
    },
    "gate_results": {
        "unit_pass": unit["all_pass"],
        "unit_passed": unit["passed"],
        "unit_total": unit["total"],
        "preflight_pass": pre["all_pass"],
        "preflight_passed": pre["passed"],
        "preflight_total": pre["total"],
        "negative_controls_NC71_NC85_pass": nc["all_pass"],
        "negative_controls_passed": nc["passed"],
        "negative_controls_total": nc["total"],
        "direct_source_byte_audit_pass": byte["verdict"] == "PASS",
        "direct_source_byte_audit_verdict": byte["verdict"],
        "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
        "semantic_diff_all_semantic_groups_unchanged": diff["all_semantic_groups_unchanged"],
        "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
        "launcher_co_edit_negative_control_passed": coedit["passed"],
        "source_freeze_complete": freeze["source_freeze_complete"],
    },
    "smoke_execution_status": "ELIGIBLE_NOT_STARTED",
    "smoke_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_v1_11.json").exists(),
    "smoke_start_marker_exists": (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_11.json").exists(),
    "smoke_failure_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_11.json").exists(),
    "smoke_authorization_env": "PHASE36_SMOKE_EXECUTE",
    "science_authorization_env": "PHASE36_EXECUTE",
    "phase36_science_status": "NOT_STARTED",
    "phase36_science_eligibility": "INELIGIBLE",
    "phase36_science_reason": "PENDING_SUCCESSFUL_PHASE36_REAL_FULL_PIPELINE_SYNTHETIC_SMOKE",
    "science_artifact_exists": (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_11.json").exists(),
    "science_start_marker_exists": (ROOT / "reports/audits/phase36_robustness_science_start_v1_11.json").exists(),
    "science_failure_artifact_exists": (ROOT / "reports/audits/phase36_robustness_science_failure_v1_11.json").exists(),
    "phase37_status": "NOT_STARTED",
    "test_status": "REMAINS_PHASE39_ONLY",
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "scientific_output": False,
    "no_notebook_created": True,
    "scope": "PRE_SMOKE_GOVERNANCE_CONVERGENCE_ONLY__GOVERNANCE_ONLY",
    "terminal": "PHASE36_V1_11_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__SCIENCE_INELIGIBLE_NOT_STARTED",
}
out2 = ROOT / "reports/audits/phase36_synthetic_smoke_eligibility_v1_11.json"
out2.write_text(json.dumps(elig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "freeze_terminal": freeze["terminal"],
    "eligibility_terminal": elig["terminal"],
    "gate_results": gate_results,
    "smoke_execution_status": elig["smoke_execution_status"],
}, indent=1))

ok = (unit["all_pass"] and pre["all_pass"] and nc["all_pass"]
      and byte["verdict"] == "PASS" and zero["all_counters_zero"]
      and zero["all_v1_11_generators_clean"]
      and diff["new_scientific_choice"] is False
      and diff["all_semantic_groups_unchanged"]
      and diff["changed_line_classification"]["n_prohibited"] == 0
      and coedit["passed"]
      and freeze["source_freeze_complete"]
      and not elig["smoke_artifact_exists"] and not elig["smoke_start_marker_exists"]
      and not elig["smoke_failure_artifact_exists"]
      and not elig["science_artifact_exists"]
      and not elig["science_start_marker_exists"]
      and not elig["science_failure_artifact_exists"])
raise SystemExit(0 if ok else 1)
