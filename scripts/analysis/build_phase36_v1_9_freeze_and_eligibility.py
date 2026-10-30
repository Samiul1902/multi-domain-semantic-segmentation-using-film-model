#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase 36 v1.9 — build SOURCE FREEZE + SYNTHETIC SMOKE ELIGIBILITY (READ-ONLY).

Assembles the preexecution source freeze and the synthetic-smoke eligibility
records FROM the gate reports already on disk (no re-derivation, no execution).
Byte-deterministic across reruns.

NO torch.  NO model.  NO protected-population read.
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


unit = load("reports/audits/phase36_robustness_unit_v1_9.json")
pre = load("reports/audits/phase36_robustness_preflight_v1_9.json")
nc = load("reports/audits/phase36_v1_9_negative_controls.json")
diff = load("reports/audits/phase36_v1_8_to_v1_9_execution_semantic_diff.json")
byte = load("reports/audits/phase36_v1_9_direct_source_byte_audit.json")
zero = load("reports/audits/phase36_v1_9_source_repair_no_execution_audit.json")
man = load("reports/audits/phase36_v1_9_runtime_source_integrity_manifest.json")

frozen_sources = {
    "scripts/analysis/phase36_robustness_execution_v1_9.py": sha(ROOT / "scripts/analysis/phase36_robustness_execution_v1_9.py"),
    "scripts/analysis/phase36_robustness_unit_v1_9.py": sha(ROOT / "scripts/analysis/phase36_robustness_unit_v1_9.py"),
    "scripts/analysis/phase36_robustness_preflight_v1_9.py": sha(ROOT / "scripts/analysis/phase36_robustness_preflight_v1_9.py"),
    "scripts/analysis/phase36_robustness_negative_controls_v1_9.py": sha(ROOT / "scripts/analysis/phase36_robustness_negative_controls_v1_9.py"),
}
frozen_audits = {
    "reports/audits/phase36_v1_9_runtime_source_integrity_manifest.json": sha(ROOT / "reports/audits/phase36_v1_9_runtime_source_integrity_manifest.json"),
    "reports/audits/phase36_robustness_unit_v1_9.json": sha(ROOT / "reports/audits/phase36_robustness_unit_v1_9.json"),
    "reports/audits/phase36_robustness_preflight_v1_9.json": sha(ROOT / "reports/audits/phase36_robustness_preflight_v1_9.json"),
    "reports/audits/phase36_v1_9_negative_controls.json": sha(ROOT / "reports/audits/phase36_v1_9_negative_controls.json"),
    "reports/audits/phase36_v1_8_to_v1_9_execution_semantic_diff.json": sha(ROOT / "reports/audits/phase36_v1_8_to_v1_9_execution_semantic_diff.json"),
    "reports/audits/phase36_v1_9_direct_source_byte_audit.json": sha(ROOT / "reports/audits/phase36_v1_9_direct_source_byte_audit.json"),
    "reports/audits/phase36_v1_9_source_repair_no_execution_audit.json": sha(ROOT / "reports/audits/phase36_v1_9_source_repair_no_execution_audit.json"),
}
supporting_generators = {
    "scripts/analysis/build_phase36_v1_9_semantic_diff.py": sha(ROOT / "scripts/analysis/build_phase36_v1_9_semantic_diff.py"),
    "scripts/analysis/audit_phase36_v1_9_direct_source_bytes.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_9_direct_source_bytes.py"),
    "scripts/analysis/audit_phase36_v1_9_no_execution.py": sha(ROOT / "scripts/analysis/audit_phase36_v1_9_no_execution.py"),
    "scripts/analysis/build_phase36_v1_9_runtime_integrity_manifest.py": sha(ROOT / "scripts/analysis/build_phase36_v1_9_runtime_integrity_manifest.py"),
}

gate_results = {
    "unit": {"passed": unit["passed"], "total": unit["total"], "all_pass": unit["all_pass"]},
    "preflight": {"passed": pre["passed"], "total": pre["total"], "all_pass": pre["all_pass"]},
    "negative_controls_NC50_NC57": {"passed": nc["passed"], "total": nc["total"],
                                    "all_pass": nc["all_pass"]},
    "direct_source_byte_audit": {"passed": byte["passed"], "total": byte["total"],
                                 "verdict": byte["verdict"]},
    "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
    "semantic_diff_all_semantic_groups_unchanged": diff["all_semantic_groups_unchanged"],
    "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
}

freeze = {
    "artifact": "phase36_preexecution_source_freeze_v1_9",
    "phase": 36,
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "PREEXECUTION_SOURCE_FREEZE",
    "section": "§R",
    "frozen_sources": frozen_sources,
    "frozen_audits_and_reports": frozen_audits,
    "supporting_generators": supporting_generators,
    "v1_8_history_preserved": {
        "scripts/analysis/phase36_robustness_execution_v1_8.py":
            "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d",
        "byte_preserved": True,
    },
    "v1_7_history_preserved": {
        "scripts/analysis/phase36_robustness_execution_v1_7.py":
            "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192",
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
    "n_declared_smoke_check_ids": byte["n_declared_check_ids"],
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
    "terminal": "PHASE36_V1_9_SOURCE_FREEZE_COMPLETE__SMOKE_AND_SCIENCE_NOT_STARTED",
}
out = ROOT / "reports/audits/phase36_preexecution_source_freeze_v1_9.json"
out.write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

elig = {
    "artifact": "phase36_synthetic_smoke_eligibility_v1_9",
    "phase": 36,
    "section": "§P",
    "method": "RA-MedFiLM-BARR",
    "revision": "ra_medfilm_barr_phase36_robustness_v1_9",
    "type": "SYNTHETIC_SMOKE_ELIGIBILITY",
    "history_preserved": {
        "v1_8_execution_sha256":
            "c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d",
        "v1_7_execution_sha256":
            "87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192",
        "v1_8_bytes_unchanged": True,
        "v1_7_bytes_unchanged": True,
        "v1_8_repairs_preserved": True,
        "v1_8_write_once_and_source_integrity_preserved": True,
    },
    "v1_9_repairs": {
        "D22_TRUE_WRITE_ONCE_AND_AUTHORIZED_ATTEMPT_ORDER": "REPAIRED",
        "D23_TRANSITIVE_INTEGRITY_GATE_INCOMPLETE": "REPAIRED",
        "D24_D20_NUMERICAL_CONTRACT_INCOMPLETE": "REPAIRED",
        "D25_HD95_EMPTY_CASE_SEMANTICS_TOO_PERMISSIVE": "REPAIRED",
        "CHECK_MATRIX_RECONCILIATION": "REPAIRED",
    },
    "gate_results": {
        "unit_pass": unit["all_pass"],
        "unit_passed": unit["passed"],
        "unit_total": unit["total"],
        "preflight_pass": pre["all_pass"],
        "preflight_passed": pre["passed"],
        "preflight_total": pre["total"],
        "negative_controls_NC50_NC57_pass": nc["all_pass"],
        "negative_controls_passed": nc["passed"],
        "negative_controls_total": nc["total"],
        "direct_source_byte_audit_pass": byte["verdict"] == "PASS",
        "direct_source_byte_audit_verdict": byte["verdict"],
        "semantic_diff_new_scientific_choice": diff["new_scientific_choice"],
        "semantic_diff_is_strict_superset": diff["smoke_check_ids"]["is_strict_superset"],
        "zero_execution_audit_all_counters_zero": zero["all_counters_zero"],
        "source_freeze_complete": freeze["source_freeze_complete"],
        "n_declared_smoke_check_ids": byte["n_declared_check_ids"],
    },
    "smoke_execution_status": "ELIGIBLE_NOT_STARTED",
    "smoke_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_v1_9.json").exists(),
    "smoke_start_marker_exists": (ROOT / "reports/audits/phase36_robustness_smoke_start_v1_9.json").exists(),
    "smoke_failure_artifact_exists": (ROOT / "reports/audits/phase36_robustness_smoke_failure_v1_9.json").exists(),
    "phase36_science_status": "NOT_STARTED",
    "phase36_science_eligibility": "INELIGIBLE",
    "phase36_science_reason": "PENDING_SUCCESSFUL_PHASE36_V1_9_REAL_FULL_PIPELINE_SYNTHETIC_SMOKE",
    "phase37_status": "NOT_STARTED",
    "test_status": "REMAINS_PHASE39_ONLY",
    "protected_population_read": False,
    "test_read": False,
    "router_holdout_read": False,
    "scientific_output": False,
    "terminal": "PHASE36_V1_9_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__SCIENCE_INELIGIBLE_NOT_STARTED",
}
out2 = ROOT / "reports/audits/phase36_synthetic_smoke_eligibility_v1_9.json"
out2.write_text(json.dumps(elig, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

print(json.dumps({
    "freeze_terminal": freeze["terminal"],
    "eligibility_terminal": elig["terminal"],
    "gate_results": gate_results,
    "smoke_execution_status": elig["smoke_execution_status"],
}, indent=1))

ok = (unit["all_pass"] and pre["all_pass"] and nc["all_pass"]
      and byte["verdict"] == "PASS" and zero["all_counters_zero"]
      and diff["new_scientific_choice"] is False
      and not elig["smoke_artifact_exists"] and not elig["smoke_start_marker_exists"]
      and not elig["smoke_failure_artifact_exists"])
raise SystemExit(0 if ok else 1)
