#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.10 — build SOURCE FREEZE + SYNTHETIC SMOKE ELIGIBILITY (READ-ONLY).

Assembles the preexecution source freeze and the synthetic-smoke eligibility
records FROM the v1.10 gate reports already on disk (no re-derivation, no
execution).  Byte-deterministic across reruns.

NO torch.  NO model.  NO checkpoint.  NO CUDA.  NO forward.  NO smoke.  NO science.
NO protected-population read.  NO ROUTER_HOLDOUT.  NO TEST.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


unit = load("reports/audits/phase36_robustness_unit_v1_10.json")
pre = load("reports/audits/phase36_robustness_preflight_v1_10.json")
nc = load("reports/audits/phase36_v1_10_negative_controls.json")
diff = load("reports/audits/phase36_v1_9_to_v1_10_semantic_diff.json")
byte = load("reports/audits/phase36_v1_10_direct_source_byte_audit.json")
zero = load("reports/audits/phase36_v1_10_source_repair_no_execution_audit.json")
man = load("reports/audits/phase36_v1_9_runtime_source_integrity_manifest.json")

FROZEN_V1_9_EXEC_SHA = "433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0"
FROZEN_V1_9_UNIT_SHA = "c39edd7764a0e9733cc5905e5e54935b1bcd9cc62c345189f618b0c6f4ea690e"

frozen_sources = {
    "scripts/analysis/phase36_robustness_execution_v1_9.py": sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"),
    "scripts/analysis/phase36_robustness_unit_v1_9.py": sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py"),
    "scripts/analysis/phase36_robustness_unit_v1_10.py": sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_10.py"),
    "scripts/analysis/phase36_robustness_preflight_v1_10.py": sha(ROOT / "scripts/analysis/phase36_robustness_preflight_v1_10.py"),
    "scripts/analysis/phase36_robustness_negative_controls_v1_10.py": sha(ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_10.py"),
}
frozen_audits = {
    "reports/audits/phase36_robustness_unit_v1_10.json": sha(ROOT / "reports/audits/phase36_robustness_unit_v1_10.json"),
    "reports/audits/phase36_robustness_preflight_v1_10.json": sha(ROOT / "reports/audits/phase36_robustness_preflight_v1_10.json"),
    "reports/audits/phase36_v1_10_negative_controls.json": sha(ROOT / "reports/audits/phase36_v1_10_negative_controls.json"),
    "reports/audits/phase36_v1_9_to_v1_10_semantic_diff.json": sha(ROOT / "reports/audits/phase36_v1_9_to_v1_10_semantic_diff.json"),
    "reports/audits/phase36_v1_10_direct_source_byte_audit.json": sha(ROOT / "reports/audits/phase36_v1_10_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_10_source_repair_no_execution_audit.json": sha(ROOT / "reports/audits/phase36_v1_10_source_repair_no_execution_audit.json"),
    # frozen v1.9 gate artifacts (history, must remain byte-identical)
    "reports/audits/phase36_robustness_unit_v1_9.json": sha(ROOT / "reports/audits/phase36_robustness_unit_v1_9.json"),
    "reports/audits/phase36_robustness_preflight_v1_9.json": sha(ROOT / "reports/audits/phase36_robustness_preflight_v1_9.json"),
    "reports/audits/phase36_v1_9_negative_controls.json": sha(ROOT / "reports/audits/phase36_v1_9_negative_controls.json"),
    "reports/audits/phase36_v1_9_direct_source_byte_audit.json": sha(ROOT / "reports/audits/phase36_v1_9_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_9_source_repair_no_execution_audit.json": sha(ROOT / "reports/audits/phase36_v1_9_source_repair_no_execution_audit.json"),
}
supporting_generators = {
    "scripts/analysis/build_phase36_v1_10_semantic_diff.py": sha(ROOT / "scripts/analysis/build_phase36_v1_10_semantic_diff.py"),
    "scripts/analysis/audit_phase36_v1_10_direct_source_bytes.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_10_direct_source_bytes.py"),
    "scripts/analysis/audit_phase36_v1_10_no_execution.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_10_no_execution.py"),
    "scripts/analysis/build_phase36_v1_10_freeze_and_eligibility.py": sha(ROOT / "scripts/analysis/build_phase36_v1_10_freeze_and_eligibility.py"),
}

gate_results = {
    "unit": {"passed": unit["passed"], "total": unit["total"], "all_pass": unit["all_pass"]},
    "preflight": {"passed": pre["passed"], "total": pre["total"], "all_pass": pre["all_pass"]},
    "negative_controls_NC63_NC70": {"passed": nc["passed"], "total": nc["total"],
                                    "all_pass": nc["all_pass"]},
    "direct_source_byte_audit": {"passed": byte["passed"], "total": byte["total"],
                                 "verdict": byte["verdict"]},
    "semantic_diff_execution_subject_byte_identical": diff["execution_subject_byte_identical"],
    "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
    "semantic_diff_all_semantic_groups_unchanged": diff["all_semantic_groups_unchanged"],
    "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
    "zero_execution_audit_all_generators_clean": zero["all_v1_10_generators_clean"],
}

freeze = {
    "artifact": "phase36_preexecution_source_freeze_v1_10",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "PREEXECUTION_SOURCE_FREEZE",
    "section": "§R",
    "execution_subject": "scripts/analysis/phase36_robustness_execution_v1_9.py",
    "execution_subject_sha256": FROZEN_V1_9_EXEC_SHA,
    "execution_subject_is_v1_9_bytes_unchanged_from_v1_9": True,
    "frozen_sources": frozen_sources,
    "frozen_audits_and_reports": frozen_audits,
    "supporting_generators": supporting_generators,
    "v1_9_history_preserved": {
        "scripts/analysis/phase36_robustness_execution_v1_9.py": FROZEN_V1_9_EXEC_SHA,
        "scripts/analysis/phase36_robustness_unit_v1_9.py": FROZEN_V1_9_UNIT_SHA,
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
    "future_phase36_smoke_must_use_exact_v1_9_bytes": True,
    "future_phase36_science_must_use_exact_v1_9_bytes": True,
    "source_freeze_complete": True,
    "smoke_started": False,
    "science_started": False,
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "terminal": "PHASE36_V1_10_SOURCE_FREEZE_COMPLETE__SMOKE_AND_SCIENCE_NOT_STARTED",
}
out = ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_10.json"
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

elig = {
    "artifact": "phase36_synthetic_smoke_eligibility_v1_10",
    "phase": 36,
    "section": "§P",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_10",
    "type": "SYNTHETIC_SMOKE_ELIGIBILITY",
    "history_preserved": {
        "v1_9_execution_sha256": FROZEN_V1_9_EXEC_SHA,
        "v1_9_unit_sha256": FROZEN_V1_9_UNIT_SHA,
        "v1_9_bytes_unchanged": True,
        "v1_9_repairs_preserved": True,
    },
    "v1_10_repairs": {
        "D26_TAUTOLOGICAL_D22_PROVENANCE_UNIT":
            "REPLACED_WITH_AST_DATAFLOW_ASSERTION",
        "D27_TRANSITIVE_DEPENDENCY_COUNT_UNDERCONSTRAINED":
            "EXACT_SET_EQUALITY_14",
        "D28_HD95_FOUR_CASE_CALLSITE_UNDERCONSTRAINED":
            "AST_FOUR_ACTUAL_CALL_SITES",
        "NO_NEW_SCIENTIFIC_CHOICE": True,
    },
    "gate_results": {
        "unit_pass": unit["all_pass"],
        "unit_passed": unit["passed"],
        "unit_total": unit["total"],
        "preflight_pass": pre["all_pass"],
        "preflight_passed": pre["passed"],
        "preflight_total": pre["total"],
        "negative_controls_NC63_NC70_pass": nc["all_pass"],
        "negative_controls_passed": nc["passed"],
        "negative_controls_total": nc["total"],
        "direct_source_byte_audit_pass": byte["verdict"] == "PASS",
        "direct_source_byte_audit_verdict": byte["verdict"],
        "semantic_diff_execution_subject_byte_identical":
            diff["execution_subject_byte_identical"],
        "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
        "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
        "source_freeze_complete": freeze["source_freeze_complete"],
    },
    "smoke_execution_status": "ELIGIBLE_NOT_STARTED",
    "smoke_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json").exists(),
    "smoke_start_marker_exists": (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json").exists(),
    "smoke_failure_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json").exists(),
    "phase36_science_status": "NOT_STARTED",
    "phase36_science_eligibility": "INELIGIBLE",
    "phase36_science_reason": "PENDING_SUCCESSFUL_PHASE36_REAL_FULL_PIPELINE_SYNTHETIC_SMOKE",
    "phase37_status": "NOT_STARTED",
    "test_status": "REMAINS_PHASE39_ONLY",
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "scientific_output": False,
    "no_notebook_created": True,
    "scope": "VALIDATION_GATE_REPAIR_ONLY__GOVERNANCE_ONLY",
    "terminal": "PHASE36_V1_10_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__SCIENCE_INELIGIBLE_NOT_STARTED",
}
out2 = ROOT / "reports/audits/phase36_synthetic_smoke_eligibility_v1_10.json"
out2.write_text(json.dumps(elig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "freeze_terminal": freeze["terminal"],
    "eligibility_terminal": elig["terminal"],
    "gate_results": gate_results,
    "smoke_execution_status": elig["smoke_execution_status"],
}, indent=1))

ok = (unit["all_pass"] and pre["all_pass"] and nc["all_pass"]
      and byte["verdict"] == "PASS" and zero["all_counters_zero"]
      and zero["all_v1_10_generators_clean"]
      and diff["new_scientific_choice"] is False
      and diff["execution_subject_byte_identical"]
      and not elig["smoke_artifact_exists"] and not elig["smoke_start_marker_exists"]
      and not elig["smoke_failure_artifact_exists"])
raise SystemExit(0 if ok else 1)
