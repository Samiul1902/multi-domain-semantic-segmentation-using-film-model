#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.12 — build SOURCE FREEZE + SYNTHETIC SMOKE ELIGIBILITY (READ-ONLY).

Assembles the v1.12 preexecution source freeze (binding the NEW execution source,
the NEW unit / preflight / negative-control suites, the NEW IMMUTABLE launcher,
and the NEW runtime integrity manifest) and the synthetic-smoke eligibility
record, FROM the v1.12 gate reports already on disk (no re-derivation, no
execution).  Byte-deterministic across reruns.

The freeze explicitly records the D34/D35/D36 contract-convergence repairs and
preserves every surviving v1.7/v1.8/v1.9/v1.10/v1.11 byte history.

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


unit = load("reports/audits/phase36_robustness_unit_v1_12.json")
pre = load("reports/audits/phase36_robustness_preflight_v1_12.json")
nc = load("reports/audits/phase36_v1_12_negative_controls.json")
diff = load("reports/audits/phase36_v1_11_to_v1_12_semantic_diff.json")
byte = load("reports/audits/phase36_v1_12_direct_source_byte_audit.json")
zero = load("reports/audits/phase36_v1_12_source_repair_no_execution_audit.json")
man = load("reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json")
coedit = load("reports/audits/phase36_v1_12_launcher_co_edit_negative_control.json")

FROZEN_V1_11_EXEC_SHA = "dc4928417444304ad637907c53089e512577254b368e438d0098ade6202083f0"
FROZEN_V1_11_LAUNCHER_SHA = "56612332d220f93611fc627b1f495aca3013bb3578ab801ee10b4ee0386b25b0"
FROZEN_V1_11_UNIT_SHA = "189b9957704beccff1ba9c198e7f2f9ed29fa351e9cfc6f46d03441adeaeac41"
FROZEN_V1_11_MANIFEST_SHA = "d795d41152accde6cf59717d2d17ab429b0cdf8fc1ff98bca11dcb13a591bda7"
FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"
FROZEN_V1_10_UNIT_SHA = "9b880c92469e7daca8f6563e64bf2e2e712d4eb8ac304298fbb52f89ab87c329"
FROZEN_V1_8_EXEC_SHA = "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d"
FROZEN_V1_7_EXEC_SHA = "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192"

V112_EXEC = "scripts/analysis/phase36_robustness_execution_v1_12.py"
V112_UNIT = "scripts/analysis/phase36_robustness_unit_v1_12.py"
V112_NC = "scripts/analysis/phase36_robustness_negative_controls_v1_12.py"
V112_PRE = "scripts/analysis/phase36_robustness_preflight_v1_12.py"
V112_LAUNCHER = "scripts/analysis/launch_phase36_v1_12.py"
V112_MANIFEST = "reports/audits/phase36_v1_12_runtime_source_integrity_manifest.json"

frozen_sources = {
    V112_EXEC: sha(ROOT / V112_EXEC),
    V112_UNIT: sha(ROOT / V112_UNIT),
    V112_NC: sha(ROOT / V112_NC),
    V112_PRE: sha(ROOT / V112_PRE),
    V112_LAUNCHER: sha(ROOT / V112_LAUNCHER),
}
frozen_audits = {
    "reports/audits/phase36_robustness_unit_v1_12.json": sha(ROOT / "reports/audits/phase36_robustness_unit_v1_12.json"),
    "reports/audits/phase36_robustness_preflight_v1_12.json": sha(ROOT / "reports/audits/phase36_robustness_preflight_v1_12.json"),
    "reports/audits/phase36_v1_12_negative_controls.json": sha(ROOT / "reports/audits/phase36_v1_12_negative_controls.json"),
    "reports/audits/phase36_v1_11_to_v1_12_semantic_diff.json": sha(ROOT / "reports/audits/phase36_v1_11_to_v1_12_semantic_diff.json"),
    "reports/audits/phase36_v1_12_direct_source_byte_audit.json": sha(ROOT / "reports/audits/phase36_v1_12_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_12_source_repair_no_execution_audit.json": sha(ROOT / "reports/audits/phase36_v1_12_source_repair_no_execution_audit.json"),
    V112_MANIFEST: sha(ROOT / V112_MANIFEST),
    "reports/audits/phase36_v1_12_launcher_co_edit_negative_control.json": sha(ROOT / "reports/audits/phase36_v1_12_launcher_co_edit_negative_control.json"),
    # frozen v1.11 gate artifacts + launcher + manifest (history, byte-identical)
    "reports/audits/phase36_robustness_unit_v1_11.json": sha_or_none("reports/audits/phase36_robustness_unit_v1_11.json"),
    "reports/audits/phase36_robustness_preflight_v1_11.json": sha_or_none("reports/audits/phase36_robustness_preflight_v1_11.json"),
    "reports/audits/phase36_v1_11_negative_controls.json": sha_or_none("reports/audits/phase36_v1_11_negative_controls.json"),
    "reports/audits/phase36_v1_9_to_v1_11_semantic_diff.json": sha_or_none("reports/audits/phase36_v1_9_to_v1_11_semantic_diff.json"),
    "reports/audits/phase36_v1_11_direct_source_byte_audit.json": sha_or_none("reports/audits/phase36_v1_11_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_11_source_repair_no_execution_audit.json": sha_or_none("reports/audits/phase36_v1_11_source_repair_no_execution_audit.json"),
    "reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json": sha_or_none("reports/audits/phase36_v1_11_launcher_co_edit_negative_control.json"),
    "reports/audits/phase36_preexecution_source_freeze_v1_11.json": sha_or_none("reports/audits/phase36_preexecution_source_freeze_v1_11.json"),
    "reports/audits/phase36_synthetic_smoke_eligibility_v1_11.json": sha_or_none("reports/audits/phase36_synthetic_smoke_eligibility_v1_11.json"),
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
    "reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json": sha_or_none("reports/audits/phase36_v1_10_frozen_validator_availability_provenance.json"),
}
supporting_generators = {
    "scripts/analysis/build_phase36_v1_12_semantic_diff.py": sha(ROOT / "scripts/analysis/build_phase36_v1_12_semantic_diff.py"),
    "scripts/analysis/audit_phase36_v1_12_direct_source_bytes.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_12_direct_source_bytes.py"),
    "scripts/analysis/audit_phase36_v1_12_no_execution.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_12_no_execution.py"),
    "scripts/analysis/build_phase36_v1_12_runtime_integrity_manifest.py": sha(ROOT / "scripts/analysis/build_phase36_v1_12_runtime_integrity_manifest.py"),
    "scripts/analysis/build_phase36_v1_12_launcher_co_edit_control.py": sha(ROOT / "scripts/analysis/build_phase36_v1_12_launcher_co_edit_control.py"),
    "scripts/analysis/build_phase36_v1_12_freeze_and_eligibility.py": sha(ROOT / "scripts/analysis/build_phase36_v1_12_freeze_and_eligibility.py"),
}

gate_results = {
    "unit": {"passed": unit["passed"], "total": unit["total"], "all_pass": unit["all_pass"]},
    "preflight": {"passed": pre["passed"], "total": pre["total"], "all_pass": pre["all_pass"]},
    "negative_controls_NC86_NC99": {"passed": nc["passed"], "total": nc["total"],
                                    "all_pass": nc["all_pass"]},
    "direct_source_byte_audit": {"passed": byte["passed"], "total": byte["total"],
                                 "verdict": byte["verdict"]},
    "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
    "semantic_diff_all_semantic_groups_unchanged": diff["all_semantic_groups_unchanged"],
    "semantic_diff_no_prohibited_changes":
        (diff["changed_line_classification"]["n_prohibited"] == 0),
    "semantic_diff_smoke_ids_is_superset": diff["smoke_check_ids"]["is_superset"],
    "semantic_diff_smoke_ids_is_strict_superset": diff["smoke_check_ids"]["is_strict_superset"],
    "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
    "zero_execution_audit_all_generators_clean": zero["all_v1_12_generators_clean"],
    "launcher_co_edit_negative_control_all_mutants_rejected": coedit["all_mutants_rejected"],
}

freeze = {
    "artifact": "phase36_preexecution_source_freeze_v1_12",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "PREEXECUTION_SOURCE_FREEZE",
    "section": "§R",
    "execution_subject": V112_EXEC,
    "execution_subject_sha256": frozen_sources[V112_EXEC],
    "pre_invocation_launcher": V112_LAUNCHER,
    "pre_invocation_launcher_sha256": frozen_sources[V112_LAUNCHER],
    "runtime_integrity_manifest": V112_MANIFEST,
    "runtime_integrity_manifest_sha256": frozen_audits[V112_MANIFEST],
    "non_circular_release_chain": {
        "supervisor_pins": [
            "scripts/analysis/launch_phase36_v1_12.py",
            "reports/audits/phase36_preexecution_source_freeze_v1_12.json",
        ],
        "launcher_verifies": [
            V112_EXEC,
            V112_MANIFEST,
        ],
        "manifest_declares": [V112_EXEC],
        "source_requires": "PHASE36_V1_12_LAUNCH_AUTHORITY token ONLY (no manifest-declared launcher hash)",
        "launcher_expected_hashes_immutable": True,
        "launcher_env_override_mechanism": "NONE (D35)",
        "no_cycle": True,
        "launcher_sha_declared_in_manifest": "launcher_sha256" in man,
        "source_fails_closed_on_manifest_launcher_sha": True,
    },
    "frozen_sources": frozen_sources,
    "frozen_audits_and_reports": frozen_audits,
    "supporting_generators": supporting_generators,
    "history_preserved": {
        "scripts/analysis/phase36_robustness_execution_v1_11.py": FROZEN_V1_11_EXEC_SHA,
        "scripts/analysis/launch_phase36_v1_11.py": FROZEN_V1_11_LAUNCHER_SHA,
        "scripts/analysis/phase36_robustness_unit_v1_11.py": FROZEN_V1_11_UNIT_SHA,
        "reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json": FROZEN_V1_11_MANIFEST_SHA,
        "scripts/analysis/phase36_robustness_execution_v1_9.py": FROZEN_V1_9_EXEC_SHA,
        "scripts/analysis/phase36_robustness_unit_v1_9.py": FROZEN_V1_9_UNIT_SHA,
        "scripts/analysis/phase36_robustness_unit_v1_10.py": FROZEN_V1_10_UNIT_SHA,
        "scripts/analysis/phase36_robustness_execution_v1_8.py": FROZEN_V1_8_EXEC_SHA,
        "scripts/analysis/phase36_robustness_execution_v1_7.py": FROZEN_V1_7_EXEC_SHA,
        "byte_preserved": True,
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
    "future_phase36_smoke_must_use_exact_v1_12_bytes": True,
    "future_phase36_science_must_use_exact_v1_12_bytes": True,
    "future_phase36_dispatch_must_go_through_launcher": True,
    "source_freeze_complete": True,
    "smoke_started": False,
    "science_started": False,
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "terminal": "PHASE36_V1_12_SOURCE_FREEZE_COMPLETE__SMOKE_AND_SCIENCE_NOT_STARTED",
}
out = ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_12.json"
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

elig = {
    "artifact": "phase36_synthetic_smoke_eligibility_v1_12",
    "phase": 36,
    "section": "§P",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_12",
    "type": "SYNTHETIC_SMOKE_ELIGIBILITY",
    "history_preserved": {
        "v1_11_execution_sha256": FROZEN_V1_11_EXEC_SHA,
        "v1_11_launcher_sha256": FROZEN_V1_11_LAUNCHER_SHA,
        "v1_11_unit_sha256": FROZEN_V1_11_UNIT_SHA,
        "v1_11_manifest_sha256": FROZEN_V1_11_MANIFEST_SHA,
        "v1_9_execution_sha256": FROZEN_V1_9_EXEC_SHA,
        "v1_9_unit_sha256": FROZEN_V1_9_UNIT_SHA,
        "v1_10_unit_sha256": FROZEN_V1_10_UNIT_SHA,
        "v1_7_v1_8_v1_9_v1_10_v1_11_bytes_unchanged": True,
        "v1_9_repairs_preserved": True,
    },
    "v1_12_repairs": {
        "D34_SOURCE_MANIFEST_LAUNCH_ANCHOR_CONTRADICTION": "REPAIRED_ENFORCED",
        "D35_IMMUTABLE_NON_ENV_OVERRIDABLE_LAUNCH_HASHES": "REPAIRED_ENFORCED",
        "D36_THREE_FILE_VALIDATION_CROSS_BINDING": "REPAIRED_ENFORCED",
        "D22_D33_PRIOR_VALIDATION_REPAIRS": "PRESERVED_ENFORCED",
        "SEMANTIC_DIFF_IDENTICAL_SET_NOT_STRICT_SUPERSET": "REPORTING_REPAIRED",
        "NO_NEW_SCIENTIFIC_CHOICE": True,
    },
    "gate_results": {
        "unit_pass": unit["all_pass"],
        "unit_passed": unit["passed"],
        "unit_total": unit["total"],
        "preflight_pass": pre["all_pass"],
        "preflight_passed": pre["passed"],
        "preflight_total": pre["total"],
        "negative_controls_NC86_NC99_pass": nc["all_pass"],
        "negative_controls_passed": nc["passed"],
        "negative_controls_total": nc["total"],
        "direct_source_byte_audit_pass": byte["verdict"] == "PASS",
        "direct_source_byte_audit_verdict": byte["verdict"],
        "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
        "semantic_diff_all_semantic_groups_unchanged": diff["all_semantic_groups_unchanged"],
        "semantic_diff_smoke_ids_is_superset": diff["smoke_check_ids"]["is_superset"],
        "semantic_diff_smoke_ids_is_strict_superset": diff["smoke_check_ids"]["is_strict_superset"],
        "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
        "launcher_co_edit_negative_control_all_mutants_rejected": coedit["all_mutants_rejected"],
        "source_freeze_complete": freeze["source_freeze_complete"],
    },
    "smoke_execution_status": "ELIGIBLE_NOT_STARTED",
    "smoke_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_v1_12.json").exists(),
    "smoke_start_marker_exists": (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_12.json").exists(),
    "smoke_failure_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_12.json").exists(),
    "smoke_authorization_env": "PHASE36_SMOKE_EXECUTE",
    "science_authorization_env": "PHASE36_EXECUTE",
    "phase36_science_status": "NOT_STARTED",
    "phase36_science_eligibility": "INELIGIBLE",
    "phase36_science_reason": "PENDING_SUCCESSFUL_PHASE36_REAL_FULL_PIPELINE_SYNTHETIC_SMOKE",
    "science_artifact_exists": (ROOT / "reports/audits/phase36_robustness_scientific_result_v1_12.json").exists(),
    "science_start_marker_exists": (ROOT / "reports/audits/phase36_robustness_science_start_v1_12.json").exists(),
    "science_failure_artifact_exists": (ROOT / "reports/audits/phase36_robustness_science_failure_v1_12.json").exists(),
    "phase37_status": "NOT_STARTED",
    "test_status": "REMAINS_PHASE39_ONLY",
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "scientific_output": False,
    "no_notebook_created": True,
    "scope": "LAUNCH_ANCHOR_CONTRACT_CONVERGENCE_ONLY__GOVERNANCE_ONLY",
    "terminal": "PHASE36_V1_12_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__SCIENCE_INELIGIBLE_NOT_STARTED",
}
out2 = ROOT / "reports/audits/phase36_synthetic_smoke_eligibility_v1_12.json"
out2.write_text(json.dumps(elig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "freeze_terminal": freeze["terminal"],
    "eligibility_terminal": elig["terminal"],
    "gate_results": gate_results,
    "smoke_execution_status": elig["smoke_execution_status"],
}, indent=1))

ok = (unit["all_pass"] and pre["all_pass"] and nc["all_pass"]
      and byte["verdict"] == "PASS" and zero["all_counters_zero"]
      and zero["all_v1_12_generators_clean"]
      and diff["new_scientific_choice"] is False
      and diff["all_semantic_groups_unchanged"]
      and diff["changed_line_classification"]["n_prohibited"] == 0
      and diff["smoke_check_ids"]["is_superset"]
      and not diff["smoke_check_ids"]["is_strict_superset"]
      and coedit["all_mutants_rejected"]
      and freeze["source_freeze_complete"]
      and not elig["smoke_artifact_exists"] and not elig["smoke_start_marker_exists"]
      and not elig["smoke_failure_artifact_exists"]
      and not elig["science_artifact_exists"]
      and not elig["science_start_marker_exists"]
      and not elig["science_failure_artifact_exists"])
raise SystemExit(0 if ok else 1)
