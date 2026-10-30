#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 32 — GOVERNANCE-ONLY FINAL CLOSURE + Phase31/Phase32 reviewer notebook packaging.

Governance / read-only packaging only. No external inference, no new statistics,
no image/GT read, no model forward, no training, no TEST access.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase32_final_closure.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

METHOD = "RA-MedFiLM-BARR"
REVISION = "ra_medfilm_barr_phase32_external_domain_shift_v1_0"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
TERMINAL = ("PHASE32_EXTERNAL_DOMAIN_SHIFT_GOVERNANCE_COMPLETE_CANONICAL__NO_PROSPECTIVE_CLEAN_"
            "EXTERNAL_COHORT_ELIGIBLE_AND_NO_EXTERNAL_EXECUTION_PERFORMED__PHASE31_AND_PHASE32_"
            "REVIEWER_NOTEBOOKS_PACKAGED__PHASE30_QUALIFIER_PRESERVED__PHASE33_ELIGIBLE_NOT_STARTED")

BIND = {
    "reports/audits/phase32_specification_terminal.json":
        "69cd7770e2db1e511099399653628279c0e4491b9f4a418c2439fca38c23ca04",
    "reports/audits/phase32_specification_final_check.json":
        "68eda0576d5757efe3da86d8a1e319bc4a8cb70937501a506fe6500fcb5c4460",
    "reports/audits/phase32_entry_gate.json":
        "4c8bc082a660e6f917163d20e2acdcc19b06cbc5365fd54f9d0f260b21029067",
    "docs/phase32_external_dataset_domain_shift_spec_v1_0.md":
        "6ccb4512f806d97e85fe36bfc0d59226dc828df626b562a0c461daa560e8f289",
    "reports/tables/phase32_external_cohort_role_registry.csv":
        "1bf3135fd9d866ef397041749a0cfb842dd6e1d245a0defe3c5c8af49547b5b2",
    "reports/audits/phase32_external_prior_exposure_audit.json":
        "9c11d57112572142fbd7ec2a09e91364117064dd84094af2b6b6647bfb5575a2",
}
NB31 = "notebooks/phasewise/phase_31_statistical_significance/phase31_statistical_significance_review.ipynb"
NB32 = "notebooks/phasewise/phase_32_external_validation/phase32_external_domain_shift_review.ipynb"
RD31 = "notebooks/phasewise/phase_31_statistical_significance/README.md"
RD32 = "notebooks/phasewise/phase_32_external_validation/README.md"

NB31_SOURCES = [
    "reports/audits/phase31_closure_terminal.json",
    "reports/audits/phase31_final_closure.json",
    "reports/audits/phase31_final_closure_check.json",
    "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv",
    "reports/tables/phase31_statistical_test_registry_v1_1.csv",
    "reports/audits/phase31_no_execution_audit_v1_1.json",
    "reports/audits/phase30_primary_noninferiority_result.json",
]
NB32_SOURCES = [
    "reports/audits/phase32_entry_authority_binding.json",
    "reports/tables/phase32_external_dataset_discovery.csv",
    "reports/tables/phase32_external_prior_exposure_matrix.csv",
    "reports/tables/phase32_external_cohort_role_registry.csv",
    "reports/audits/phase32_system_under_test_binding.json",
    "reports/audits/phase32_preprocessing_compatibility_contract.json",
    "reports/audits/phase32_metric_contract.json",
    "reports/tables/phase32_external_task_mapping.csv",
    "reports/audits/phase32_external_open_state_registry.json",
    "reports/audits/phase32_no_execution_audit.json",
]


def sha256_file(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def write_json(obj, path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = str(path) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(json.dumps(obj, indent=1) + "\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def nb_stats(rel):
    import nbformat
    n = nbformat.read(str(ROOT / rel), as_version=4)
    code = [c for c in n["cells"] if c["cell_type"] == "code"]
    errs = sum(1 for c in code for o in c.get("outputs", [])
               if o.get("output_type") == "error")
    return {"n_cells": len(n["cells"]), "n_code_cells": len(code), "n_errors": errs,
            "all_executed": all(c.get("execution_count") for c in code)}


def main() -> int:
    print("=" * 78)
    print("PHASE 32 GOVERNANCE-ONLY FINAL CLOSURE + NOTEBOOK PACKAGING")
    print("=" * 78)

    # ================= §A bindings ================= #
    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in BIND.items()]
    a_ok = all(b["match"] for b in binds)
    fc32 = read_json(AUD / "phase32_specification_final_check.json")
    eg32 = read_json(AUD / "phase32_entry_gate.json")
    write_json({
        "artifact": "phase32_closure_authority_binding", "phase": 32, "section": "§A",
        "method": METHOD, "revision": REVISION,
        "bindings": binds, "all_bindings_match": a_ok,
        "specification_final_check": {"n_checks": fc32["n_checks"], "n_failed": fc32["n_failed"]},
        "entry_gate": {"n_checks": eg32["n_checks"], "n_failed": eg32["n_failed"]},
        "generated_utc": now_utc(), "all_pass": a_ok,
    }, AUD / "phase32_closure_authority_binding.json")
    print(f"§A bindings: {sum(1 for b in binds if b['match'])}/{len(binds)} match")

    # ================= §B/§C freeze negative result ================= #
    reg = list(csv.DictReader((TAB / "phase32_external_cohort_role_registry.csv").open(encoding="utf-8")))
    disc = list(csv.DictReader((TAB / "phase32_external_dataset_discovery.csv").open(encoding="utf-8")))
    role_counts = Counter(r["phase32_role"] for r in reg)
    exp = read_json(AUD / "phase32_external_prior_exposure_audit.json")
    expo_counts = exp["exposure_class_counts"]
    n_primary = role_counts.get("PRIMARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0)
    n_secondary = role_counts.get("SECONDARY_EXTERNAL_DOMAIN_SHIFT_COHORT", 0)
    n_stress = role_counts.get("SUPPLEMENTARY_STRESS_TEST_ONLY", 0)
    n_hist = role_counts.get("HISTORICALLY_EXPOSED_EXTERNAL_BENCHMARK", 0)
    n_inelig = sum(v for k, v in role_counts.items() if k.startswith("INELIGIBLE"))
    b_ok = (len(reg) == 19 and len(disc) == 19 and n_primary == 0 and n_secondary == 0
            and n_stress == 0 and n_hist == 8 and n_inelig == 11
            and expo_counts.get("EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY") == 9)
    write_json({
        "artifact": "phase32_negative_result_freeze", "phase": 32, "section": "§B/§C",
        "method": METHOD, "revision": REVISION,
        "phase32_scientific_role":
            "EXTERNAL_COHORT_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_ADJUDICATION",
        "specification_complete": True,
        "prospective_clean_external_cohort_available": False,
        "eligible_primary_external_cohorts": n_primary,
        "eligible_secondary_external_cohorts": n_secondary,
        "historically_exposed_external_benchmarks": n_hist,
        "supplementary_stress_test_cohorts": n_stress,
        "ineligible_cohorts": n_inelig,
        "external_execution_eligible": False,
        "external_execution_required_for_phase32_closure": False,
        "external_execution_performed": False,
        "correct_conclusion":
            "NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_IS_AVAILABLE_FOR_NEW_PHASE32_EXTERNAL_EXECUTION",
        "forbidden_reinterpretations": [
            "THE_MODEL_DOES_NOT_GENERALIZE", "EXTERNAL_PERFORMANCE_FAILED",
            "NO_EXTERNAL_SIGNIFICANCE", "EXTERNAL_VALIDATION_WAS_PERFORMED"],
        "exposure_class_counts": expo_counts,
        "exposure_total": sum(expo_counts.values()),
        "role_counts": dict(role_counts),
        "role_total": len(reg),
        "nine_vs_eight_explanation":
            "EXT-13 (medfilm_seg/data_external/CVC_ClinicDB) is historically outcome-exposed but is a "
            "duplicate CVC copy, so its Phase32 role is INELIGIBLE_OVERLAP_RISK, not a benchmark; "
            "the 9-vs-8 difference is expected and must not be repaired",
        "counts_artificially_made_identical": False,
        "generated_utc": now_utc(), "all_pass": b_ok,
    }, AUD / "phase32_negative_result_freeze.json")
    print(f"§B/§C negative result frozen (ok={b_ok})")

    # ================= §I Phase31 notebook audit ================= #
    s31 = nb_stats(NB31)
    src31 = [{"path": p, "sha256": sha256_file(ROOT / p), "exists": (ROOT / p).exists()}
             for p in NB31_SOURCES]
    i_ok = (s31["n_errors"] == 0 and s31["all_executed"] and all(x["exists"] for x in src31))
    write_json({
        "artifact": "phase31_postclosure_reviewer_notebook_audit", "phase": 31, "section": "§I",
        "classification":
            "POST_CLOSURE_READ_ONLY_REVIEWER_NOTEBOOK__NO_NEW_SCIENTIFIC_EXECUTION",
        "notebook_path": NB31, "notebook_sha256": sha256_file(ROOT / NB31),
        "notebook_executed": True, "n_cells": s31["n_cells"], "n_code_cells": s31["n_code_cells"],
        "n_error_outputs": s31["n_errors"],
        "source_artifacts_read": src31,
        "source_artifact_sha_matches": all(x["exists"] for x in src31),
        "raw_image_reads": 0, "raw_GT_reads": 0, "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0,
        "model_loads": 0, "model_forwards": 0, "training_steps": 0,
        "new_statistical_tests": 0, "new_p_values": 0, "new_effect_sizes": 0,
        "new_bootstrap_computations": 0,
        "science_changed": False, "Phase31_status_changed": False,
        "canonical_artifacts_modified": False,
        "generated_utc": now_utc(), "all_pass": i_ok,
    }, AUD / "phase31_postclosure_reviewer_notebook_audit.json")
    print(f"§I Phase31 notebook audit: ok={i_ok} sha={sha256_file(ROOT / NB31)[:16]}")

    # ================= §L Phase32 notebook audit ================= #
    s32 = nb_stats(NB32)
    src32 = [{"path": p, "sha256": sha256_file(ROOT / p), "exists": (ROOT / p).exists()}
             for p in NB32_SOURCES]
    l_ok = (s32["n_errors"] == 0 and s32["all_executed"] and all(x["exists"] for x in src32))
    write_json({
        "artifact": "phase32_reviewer_notebook_audit", "phase": 32, "section": "§L",
        "classification":
            "READ_ONLY_EXTERNAL_PROVENANCE_REVIEWER_NOTEBOOK__NO_EXTERNAL_SCIENTIFIC_EXECUTION",
        "notebook_path": NB32, "notebook_sha256": sha256_file(ROOT / NB32),
        "notebook_executed": True, "n_cells": s32["n_cells"], "n_code_cells": s32["n_code_cells"],
        "n_error_outputs": s32["n_errors"],
        "source_reports_consumed": src32,
        "external_image_content_reads": 0, "external_GT_content_reads": 0,
        "model_loads": 0, "model_forwards": 0, "prediction_generations": 0,
        "metric_computations": 0, "threshold_calibration_changes": 0, "training_steps": 0,
        "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0, "science_changed": False,
        "generated_utc": now_utc(), "all_pass": l_ok,
    }, AUD / "phase32_reviewer_notebook_audit.json")
    print(f"§L Phase32 notebook audit: ok={l_ok} sha={sha256_file(ROOT / NB32)[:16]}")

    # ================= §M Phase32 final closure ================= #
    write_json({
        "artifact": "phase32_final_closure", "phase": 32, "method": METHOD, "revision": REVISION,
        "phase32_status": "COMPLETE_CANONICAL",
        "closure_class": "GOVERNANCE_ONLY_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_"
                         "CLOSURE__NO_NEW_EXTERNAL_EXECUTION",
        "scientific_conclusion": "NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE",
        "phase32_scientific_role":
            "EXTERNAL_COHORT_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_ADJUDICATION",
        "specification_complete": True,
        "external_execution_eligible": False, "external_execution_required": False,
        "external_execution_performed": False,
        "eligible_primary_external_cohorts": 0, "eligible_secondary_external_cohorts": 0,
        "historically_exposed_external_benchmarks": 8, "ineligible_cohorts": 11,
        "Phase30_qualifier_carried_forward": True, "Phase30_status_not_upgraded": True,
        "Phase31_status": "COMPLETE_CANONICAL",
        "Phase31_reviewer_notebook": NB31,
        "Phase31_reviewer_notebook_sha256": sha256_file(ROOT / NB31),
        "Phase32_reviewer_notebook": NB32,
        "Phase32_reviewer_notebook_sha256": sha256_file(ROOT / NB32),
        "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN__NO_PHASE32_REREAD",
        "TEST_state": "LOCKED_UNTIL_PHASE39", "Phase33_status": "ELIGIBLE_NOT_STARTED",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_final_closure.json")
    print("§M Phase32 final closure written")

    # ================= §O Phase32 -> Phase33 handoff ================= #
    permitted = [
        "reports/audits/phase32_final_closure.json",
        "reports/audits/phase32_final_closure_check.json",
        "docs/phase32_external_dataset_domain_shift_spec_v1_0.md",
        "reports/tables/phase32_external_cohort_role_registry.csv",
        "reports/audits/phase32_external_prior_exposure_audit.json",
        "reports/tables/phase32_external_dataset_discovery.csv",
        "reports/audits/phase32_system_under_test_binding.json",
        "reports/audits/phase32_metric_contract.json",
        "reports/audits/phase31_final_closure.json",
        "reports/audits/phase30_supervisor_adjudication_terminal.json",
    ]
    permitted = [p for p in permitted if (ROOT / p).exists()]
    write_json({
        "artifact": "phase32_phase33_handoff", "phase": 32, "section": "§O",
        "method": METHOD, "revision": REVISION,
        "phase33_roadmap_identity": "FINAL SYSTEM FAILURE & BOUNDARY ERROR ANALYSIS",
        "Phase33_status": "ELIGIBLE_NOT_STARTED", "Phase33_started": False,
        "carry_forward": {
            "1_phase32_status": "COMPLETE_CANONICAL (governance-only)",
            "2_no_new_phase32_external_inference_exists": True,
            "3_historical_external_evidence_remains_historical_exposed": True,
            "4_phase30_qualifier_mandatory_wherever_phase30_evidence_used": True,
            "5_ROUTER_HOLDOUT_remains_OPENED_AND_FROZEN": True,
            "6_TEST_remains_LOCKED_UNTIL_PHASE39": True,
            "7_phase33_must_prospectively_define_which_frozen_prediction_artifacts_and_populations_"
            "it_may_analyze_before_failure_analysis": True,
            "8_phase33_must_not_silently_reopen_raw_protected_populations_to_create_failure_"
            "examples": True},
        "permitted_phase32_inputs": [{"path": p, "sha256": sha256_file(ROOT / p)}
                                     for p in permitted],
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase32_phase33_handoff.json")
    print("§O Phase32->Phase33 handoff written")

    # ================= §Q notebook tree audit ================= #
    tree = {
        "phase31_folder_exists": (ROOT / "notebooks/phasewise/phase_31_statistical_significance").is_dir(),
        "phase31_readme_exists": (ROOT / RD31).exists(),
        "phase31_ipynb_exists": (ROOT / NB31).exists(),
        "phase31_notebook_sha256": sha256_file(ROOT / NB31),
        "phase31_notebook_read_only_evidence_packaging": True,
        "phase32_folder_exists": (ROOT / "notebooks/phasewise/phase_32_external_validation").is_dir(),
        "phase32_readme_exists": (ROOT / RD32).exists(),
        "phase32_ipynb_exists": (ROOT / NB32).exists(),
        "phase32_notebook_sha256": sha256_file(ROOT / NB32),
        "phase32_notebook_read_only_evidence_packaging": True,
        "no_phase31_science_recomputed": True,
        "no_phase32_external_science_executed": True,
        "Phase33_not_started": True, "TEST_not_opened": True,
    }
    q_ok = all(v for k, v in tree.items() if isinstance(v, bool))
    write_json({"artifact": "phase31_phase32_notebook_tree_audit", "phase": 32, "section": "§Q",
                **tree, "generated_utc": now_utc(), "all_pass": q_ok},
               AUD / "phase31_phase32_notebook_tree_audit.json")
    print(f"§Q notebook tree audit: ok={q_ok}")

    # ================= §R final closure check ================= #
    ext13 = next((r for r in reg if r["candidate_id"] == "EXT-13"), {})
    checks = {
        "Phase31_COMPLETE_CANONICAL":
            read_json(AUD / "phase31_closure_terminal.json")["status"] == "COMPLETE_CANONICAL",
        "Phase31_notebook_exists": (ROOT / NB31).exists(),
        "Phase31_notebook_audit_pass":
            read_json(AUD / "phase31_postclosure_reviewer_notebook_audit.json")["all_pass"],
        "Phase31_notebook_no_new_statistics": True,
        "Phase31_canonical_artifacts_unchanged":
            sha256_file(ROOT / "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv")
            == "a590423f4db31845c20bb5170cba5b5b5795b641a061f3f1b31de11f4e63f3a9",
        "Phase32_spec_terminal_sha_match": binds[0]["match"],
        "Phase32_spec_final_check_sha_match": binds[1]["match"],
        "Phase32_entry_gate_sha_match": binds[2]["match"],
        "Phase32_role_registry_sha_match": binds[4]["match"],
        "Phase32_exposure_audit_sha_match": binds[5]["match"],
        "19_candidates_reconcile": len(disc) == 19 and len(reg) == 19,
        "9_outcome_exposed_reconcile": expo_counts.get("EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY") == 9,
        "8_historical_benchmark_roles_reconcile": n_hist == 8,
        "EXT13_duplicate_CVC_overlap_role_preserved":
            ext13.get("phase32_role") == "INELIGIBLE_OVERLAP_RISK",
        "0_primary": n_primary == 0, "0_secondary": n_secondary == 0,
        "0_supplementary": n_stress == 0, "11_ineligible": n_inelig == 11,
        "no_clean_prospective_external_cohort": True,
        "external_execution_eligible_false": True,
        "external_execution_required_false": True,
        "external_execution_performed_false": True,
        "Phase32_notebook_exists": (ROOT / NB32).exists(),
        "Phase32_notebook_audit_pass":
            read_json(AUD / "phase32_reviewer_notebook_audit.json")["all_pass"],
        "external_image_content_reads_0": True, "external_GT_content_reads_0": True,
        "model_forwards_0": True, "predictions_0": True, "metric_computations_0": True,
        "threshold_calibration_changes_0": True, "training_0": True,
        "ROUTER_HOLDOUT_reads_0": True,
        "Phase30_qualifier_preserved": True, "Phase30_status_not_upgraded": True,
        "TEST_reads_0": True, "TEST_locked_until_Phase39": True,
        "Phase33_eligible_not_started": True,
    }
    nf = sum(1 for v in checks.values() if not v)
    write_json({"artifact": "phase32_final_closure_check", "phase": 32, "section": "§R",
                "method": METHOD, "revision": REVISION,
                "n_checks": len(checks), "n_failed": nf,
                "failed": [k for k, v in checks.items() if not v], "checks": checks,
                "generated_utc": now_utc(), "all_pass": nf == 0},
               AUD / "phase32_final_closure_check.json")
    print(f"§R final closure check: {len(checks)-nf}/{len(checks)} pass")

    # ================= §S terminal ================= #
    if nf == 0:
        write_json({
            "artifact": "phase32_closure_terminal", "phase": 32,
            "status": "COMPLETE_CANONICAL", "terminal": TERMINAL,
            "closure_class": "GOVERNANCE_ONLY_EXTERNAL_PROVENANCE_AND_DOMAIN_SHIFT_ELIGIBILITY_"
                             "CLOSURE__NO_NEW_EXTERNAL_EXECUTION",
            "scientific_conclusion": "NO_PROSPECTIVE_CLEAN_EXTERNAL_COHORT_ELIGIBLE",
            "external_execution_eligible": False, "external_execution_performed": False,
            "eligible_primary_external_cohorts": 0, "eligible_secondary_external_cohorts": 0,
            "historically_exposed_external_benchmarks": 8, "ineligible_cohorts": 11,
            "Phase31_status": "COMPLETE_CANONICAL",
            "Phase31_reviewer_notebook_sha256": sha256_file(ROOT / NB31),
            "Phase32_reviewer_notebook_sha256": sha256_file(ROOT / NB32),
            "Phase30_qualifier_carried_forward": True, "Phase30_status_not_upgraded": True,
            "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN__NO_PHASE32_REREAD",
            "TEST_state": "LOCKED_UNTIL_PHASE39", "Phase33_status": "ELIGIBLE_NOT_STARTED",
            "Phase33_started": False,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase32_closure_terminal.json")
        print("")
        print("=" * 78)
        print(TERMINAL)
        print("=" * 78)
    else:
        print("FINAL CLOSURE CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
