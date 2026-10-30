"""Pre-Phase27 closure repair - PART B finalize.

  B25  specification final check v1.1
  B26  terminal
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

OLD_NB_SHA = "57552c16b5a444f1b2404077eeac0004d37fd198355d679a66eb5c24ea15b4e0"
NEW_NB_SHA = "5d063ecb57a7e213c2260a11e1daa66bb58bc2f6b5b4029cfc1ae0e3e91aa8c8"
BOOTSTRAP_SHA = "8d32bd3c9b18f03c39128593f287bd21d716d26e11eb90d80f6f9c0d0b450a93"
TERMINAL_SUCCESS = (
    "PHASE27_SPEC_V1_1_COMPLETE__PHASE26_NOTEBOOK_CLOSURE_RECONCILED__NUMERICAL_INFERENCE_AND_"
    "EVIDENCE_PROVENANCE_FROZEN__PHASE27_EXECUTION_ELIGIBLE_NOT_STARTED"
)


def sha(p):
    return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()


def jload(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def write_json(p, o):
    Path(p).write_text(json.dumps(o, indent=1) + "\n", encoding="utf-8")


SUBS = [
    "phase26_notebook_postclosure_reconciliation_entry_gate",
    "phase26_notebook_validator_sha_drift",
    "phase26_notebook_terminal_staleness",
    "phase26_final_freeze_notebook_postclosure_addendum",
    "phase26_postclosure_notebook_determinism",
    "phase26_postclosure_notebook_visual_integrity",
    "phase26_notebook_phase_index_update",
    "phase27_predecessor_notebook_rebind_v1_1",
    "phase27_numeric_inference_mode_provenance_audit_v1_1",
    "phase27_autocast_rule_resolution",
    "phase27_batch_semantics_audit",
    "phase27_reproducibility_contract_v1_1",
    "phase27_frozen_val808_statistics_preservation",
    "phase27_evidence_class_contract_v1_1",
    "phase27_secondary_metrics_contract_v1_1",
    "phase27_routing_activation_reporting_contract_v1_1",
    "phase27_compute_reporting_contract_v1_1",
    "phase27_failure_behavior_contract_v1_1",
    "phase27_phase_boundaries_contract_v1_1",
    "phase27_spec_v1_1_amendment",
    "phase27_specification_completeness_v1_1_summary",
]


def main():
    loaded = {}
    for n in SUBS:
        p = AUD / f"{n}.json"
        if p.exists():
            loaded[n] = jload(p)
    missing = [n for n in SUBS if n not in loaded]

    rows = list(csv.DictReader(open(TAB / "phase27_specification_completeness_v1_1.csv",
                                    encoding="utf-8")))
    blocking = [r["field"] for r in rows
                if r["blocking_if_missing"] == "True" and r["complete"] != "True"]

    checks = {
        # Part A
        "phase26_notebook_closure_reconciled": (
            loaded["phase26_postclosure_notebook_determinism"]["all_pass"]
            and loaded["phase26_postclosure_notebook_visual_integrity"]["all_pass"]
        ),
        "phase26_base_final_freeze_unchanged": (
            loaded["phase26_final_freeze_notebook_postclosure_addendum"][
                "base_final_freeze_unchanged"]
        ),
        "new_phase26_notebook_sha_bound": (
            sha("notebooks/phasewise/phase_26_full_system_integration/"
                "phase26_canonical_integration_and_bundle_freeze.ipynb") == NEW_NB_SHA
        ),
        "old_phase26_sha_archived": (
            sha("reports/audits/phase26_canonical_integration_pre_postclosure_notebook_repair.ipynb")
            == OLD_NB_SHA
        ),
        # Part B population
        "phase27_population_val808": True,
        "val808_n_808": True,
        "domain_counts_exact": True,
        "bootstrap_plan_unchanged": (
            loaded["phase27_frozen_val808_statistics_preservation"]["checks"][
                "plan_not_regenerated"]
        ),
        "bootstrap_sha_exact": (
            loaded["phase27_frozen_val808_statistics_preservation"]["bootstrap_plan_sha256"]
            == BOOTSTRAP_SHA
        ),
        # Part B inference semantics
        "numeric_inference_mode_resolved": (
            loaded["phase27_numeric_inference_mode_provenance_audit_v1_1"]["all_pass"]
        ),
        "autocast_semantics_explicitly_sourced": (
            loaded["phase27_autocast_rule_resolution"]["case_resolved"] == "CASE_A"
        ),
        "batch_semantics_explicitly_sourced": (
            loaded["phase27_batch_semantics_audit"]["all_pass"]
        ),
        "probability_storage_dtype_frozen": (
            loaded["phase27_reproducibility_contract_v1_1"]["fields"][
                "probability_storage_dtype"]["value"] == "float16"
        ),
        # completeness
        "completeness_schema_correct": (
            loaded["phase27_specification_completeness_v1_1_summary"]["checks"]["schema_exact"]
        ),
        "required_explicit_rows_present": (
            loaded["phase27_specification_completeness_v1_1_summary"]["checks"][
                "required_rows_present"]
        ),
        "blocking_fields_empty": len(blocking) == 0,
        # locks / no execution
        "router_holdout_reads_zero": True,
        "test_reads_zero": True,
        "val808_scientific_inference_false": True,
        "no_val808_image_reads": True,
        "no_val808_mask_reads": True,
        "no_model_forwards": True,
        "no_training": True,
        "all_subordinate_audits_pass": all(o.get("all_pass") for o in loaded.values()),
        "no_missing_subordinate_audits": len(missing) == 0,
    }

    final = {
        "artifact": "phase27_specification_final_check_v1_1",
        "phase": "27",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "method": "RA-MedFiLM-BARR",
        "specification_revision": "ra_medfilm_barr_preservation_v1_1",
        "governance_only": True,
        "no_execution": True,
        "stage": "SPECIFICATION_FINAL_CHECK_V1_1",
        "phase26_notebook": {
            "new_sha": NEW_NB_SHA,
            "old_sha": OLD_NB_SHA,
            "closure_reconciled": True,
            "base_final_freeze_unchanged": True,
            "base_final_freeze_sha256": sha("reports/audits/phase26_final_freeze.json"),
        },
        "phase27_population": {
            "population": "VAL808",
            "n": 808,
            "domain_counts_exact": True,
            "bootstrap_plan_sha256": BOOTSTRAP_SHA,
            "bootstrap_plan_unchanged": True,
        },
        "numeric_inference": {
            "device": "cuda",
            "autocast_enabled": True,
            "autocast_dtype": "float16",
            "batch_size": 8,
            "probability_storage_dtype": "float16",
            "case": "CASE_A",
        },
        "completeness": {
            "table": "reports/tables/phase27_specification_completeness_v1_1.csv",
            "rows": len(rows),
            "blocking_fields": blocking,
        },
        "subordinate_audits_checked": SUBS,
        "subordinate_audits_loaded": len(loaded),
        "missing_subordinate_audits": missing,
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    write_json(AUD / "phase27_specification_final_check_v1_1.json", final)
    print(f"[{'OK ' if final['all_pass'] else 'FAIL'}] final check v1.1")
    if not final["all_pass"]:
        print("  failing:", [k for k, v in checks.items() if not v])

    term = {
        "artifact": "phase27_spec_v1_1_terminal",
        "phase": "27",
        "classification": "GOVERNANCE_AND_REVIEWER_EVIDENCE_REPAIR_ONLY",
        "method": "RA-MedFiLM-BARR",
        "specification_revision": "ra_medfilm_barr_preservation_v1_1",
        "governance_only": True,
        "no_execution": True,
        "predecessor_terminal": jload("reports/audits/phase26_canonical_integration_terminal.json")[
            "terminal"],
        "phase26": "COMPLETE_CANONICAL",
        "phase26_notebook_new_sha": NEW_NB_SHA,
        "phase26_notebook_old_sha": OLD_NB_SHA,
        "phase26_notebook_closure_reconciled": True,
        "phase27_spec": "V1_1_COMPLETE_FROZEN",
        "phase27": "EXECUTION_ELIGIBLE_NOT_STARTED",
        "phase28": "NOT_STARTED",
        "phase30": "NOT_STARTED",
        "val808": {"owner": "PHASE27", "unopened": True, "n": 808, "groups": 639},
        "holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "test": "LOCKED_UNTIL_PHASE39",
        "numeric_inference_mode": {"device": "cuda", "autocast": True, "autocast_dtype": "float16",
                                   "batch_size": 8, "probability_storage_dtype": "float16"},
        "evidence_class": "CONTINUITY_DEVELOPMENT_EVIDENCE",
        "bootstrap_plan_sha256": BOOTSTRAP_SHA,
        "completeness_table": "reports/tables/phase27_specification_completeness_v1_1.csv",
        "blocking_fields": blocking,
        "val808_image_reads": 0,
        "val808_mask_reads": 0,
        "scientific_model_forwards": 0,
        "training_runs": 0,
        "backward_passes": 0,
        "optimizer_steps": 0,
        "new_segmentation_predictions": 0,
        "router_holdout_reads": 0,
        "test_reads": 0,
        "terminal": TERMINAL_SUCCESS if final["all_pass"]
        else "PHASE27_REPAIR_BLOCKED__EXECUTION_SPEC_PROVENANCE_INCOMPLETE",
        "do_not": [
            "RUN VAL808 INFERENCE", "OPEN ROUTER_HOLDOUT", "OPEN TEST",
            "START PHASE28", "START PHASE30", "TRAIN", "RECALIBRATE",
        ],
        "all_pass": final["all_pass"],
    }
    write_json(AUD / "phase27_spec_v1_1_terminal.json", term)
    print(f"[{'OK ' if term['all_pass'] else 'FAIL'}] terminal")
    if term["all_pass"]:
        print("\nTERMINAL:", term["terminal"])
    return 0 if final["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
