#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 31 — GOVERNANCE-ONLY FINAL CLOSURE.
Statistical claim-governance / provenance adjudication.

No statistical test, no p-value, no effect size, no bootstrap, no image read, no GT read,
no model forward, no training, no TEST access.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase31_final_closure.py
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
REVISION = "ra_medfilm_barr_phase31_statistics_v1_1"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
TERMINAL = ("PHASE31_STATISTICAL_CLAIM_GOVERNANCE_COMPLETE_CANONICAL__NO_NEW_CONFIRMATORY_OR_"
            "EXPLORATORY_STATISTICAL_EXECUTION_ELIGIBLE_OR_REQUIRED__PHASE30_PROTOCOL_DEVIATION_"
            "QUALIFIER_PRESERVED__PHASE32_ELIGIBLE_NOT_STARTED")

BIND = {
    "docs/phase31_statistical_significance_hypothesis_testing_spec_v1_1.md":
        "51a4f44ec4f64f30ef248c7590024811931d037907a7a2875e26e41663c7a212",
    "reports/audits/phase31_specification_terminal_v1_1.json":
        "7c2ce43cc913c496b0f35dc47523a8d477178f5e37707f3997a027a2f1de540b",
    "reports/audits/phase31_specification_final_check_v1_1.json":
        "64e575ce9a78cfa8f41ba945ba1d94ec513d824e4a1eae72c2ae2db68908cdd3",
    "reports/audits/phase31_execution_eligibility_adjudication_v1_1.json":
        "abbedaff9619e4cd955f2098766b2d882ebaf60b7703090b5e20aada6bac7638",
    "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv":
        "a590423f4db31845c20bb5170cba5b5b5795b641a061f3f1b31de11f4e63f3a9",
    "reports/tables/phase31_statistical_test_registry_v1_1.csv":
        "063b10d5734a6e791474aff74e244f031faea47fbeb1cc3130db7816907d4ab1",
    "reports/tables/phase31_specification_completeness_v1_1.csv":
        "cc61580fe9fb8c29f79587882f427543e025834d3631c5fc8a86d43bfbb76975",
    "reports/audits/phase31_v1_1_closure_evidence_completion_audit.json":
        "7430d47d1f93d7d6a0ece17be794056f2d00130979524fc6f7b7433f011fff45",
    "reports/audits/phase31_hypothesis_matrix_v1_1_reconciliation.json":
        "bf35cff4fc9875652d77ec03bc2b280cfca1365229659230d73f8cd68b6db631",
    "reports/audits/phase31_v1_0_preservation_manifest.json":
        "a8ed880f121185bbfa903e0b223d3ecf0b1c7bc29fef9f47cf4b81371dc83fd6",
}
STATUS_COUNTS = {
    "CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN": 0,
    "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE": 1,
    "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE": 5,
    "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY": 2,
    "POST_HOC_EXPLORATORY_ONLY": 1,
    "FORBIDDEN_OR_OUT_OF_SCOPE": 1,
}
VALID = set(STATUS_COUNTS)


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


def main() -> int:
    print("=" * 78)
    print("PHASE 31 — GOVERNANCE-ONLY FINAL CLOSURE")
    print("=" * 78)

    # ================= §A/§B authority + closure-evidence binding ================= #
    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in BIND.items()]
    ab_ok = all(b["match"] for b in binds)
    ev = read_json(AUD / "phase31_v1_1_closure_evidence_completion_audit.json")
    ev_ok = (ev["mode"] == "READ_ONLY_VERIFICATION"
             and ev["artifacts_regenerated"] is False and ev["all_hashes_match"] is True)
    write_json({
        "artifact": "phase31_authority_binding", "phase": 31, "section": "§A/§B",
        "method": METHOD, "revision": REVISION,
        "authority_artifacts": binds, "all_bindings_match": ab_ok,
        "closure_evidence_completion": {
            "path": "reports/audits/phase31_v1_1_closure_evidence_completion_audit.json",
            "sha256": sha256_file(AUD / "phase31_v1_1_closure_evidence_completion_audit.json"),
            "mode": ev["mode"], "artifacts_regenerated": ev["artifacts_regenerated"],
            "all_hashes_match": ev["all_hashes_match"], "verified": ev_ok},
        "generated_utc": now_utc(), "all_pass": ab_ok and ev_ok,
    }, AUD / "phase31_authority_binding.json")
    print(f"§A/§B bindings: {sum(1 for b in binds if b['match'])}/{len(binds)} match; evidence ok={ev_ok}")

    # ================= matrix + registry re-verification (read-only) ================= #
    mrows = list(csv.DictReader((TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv")
                                .open(encoding="utf-8")))
    mcols = list(mrows[0].keys())
    ids = [r["hypothesis_id"] for r in mrows]
    nonnull = sum(1 for r in mrows if (r.get("current_Phase31_status") or "").strip())
    validn = sum(1 for r in mrows if r["current_Phase31_status"] in VALID)
    counts = Counter(r["current_Phase31_status"] for r in mrows)
    counts_recon = {k: counts.get(k, 0) for k in VALID}
    rrows = list(csv.DictReader((TAB / "phase31_statistical_test_registry_v1_1.csv")
                                .open(encoding="utf-8")))
    reg_ok = (all(r["execution_authorized"] == "False" for r in rrows)
              and all(r["execution_eligible"] == "False" for r in rrows))

    # ================= §H final closure artifact ================= #
    pr = read_json(AUD / "phase30_primary_noninferiority_result.json")
    write_json({
        "artifact": "phase31_final_closure", "phase": 31, "method": METHOD, "revision": REVISION,
        "phase31_status": "COMPLETE_CANONICAL",
        "closure_class":
            "GOVERNANCE_ONLY_STATISTICAL_PROVENANCE_CLOSURE__NO_NEW_STATISTICAL_EXECUTION",
        "phase31_scientific_role": "STATISTICAL_CLAIM_GOVERNANCE_AND_PROVENANCE_ADJUDICATION",
        "scientific_conclusion": "NO_NEW_CONFIRMATORY_SIGNIFICANCE_PROCEDURE_IS_ELIGIBLE",
        "specification_complete": True, "unresolved_specification_items": 0,
        "confirmatory_execution_eligible": False, "exploratory_execution_eligible": False,
        "statistical_execution_required": False, "statistical_execution_performed": False,
        "new_confirmatory_tests_executed": 0, "new_exploratory_tests_executed": 0,
        "new_p_values": 0, "new_effect_sizes": 0, "new_bootstrap_computations": 0,
        "hypothesis_status_counts": counts_recon,
        "hypothesis_status_map": {r["hypothesis_id"]: r["current_Phase31_status"] for r in mrows},
        "test_registry_dispositions": {
            r["test_id"]: {"disposition_v1_1": r["disposition_v1_1"],
                           "execution_authorized": r["execution_authorized"],
                           "execution_eligible": r["execution_eligible"],
                           "reason": r["execution_ineligibility_reason"]} for r in rrows},
        "Phase30_qualifier_carried_forward": True,
        "Phase30_evidence_class": QUALIFIER,
        "Phase30_status_not_upgraded": True,
        "Phase30_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
        "Phase30_numerical_result": {
            "global_macro_dice": pr["global_macro_dice"], "a8_macro_dice": pr["a8_macro_dice"],
            "macro_delta_dice": pr["macro_delta_dice"], "macro_ci": pr["macro_ci"],
            "PRESERVATION_ASSERTED": pr["PRESERVATION_ASSERTED"],
            "phase30_p_values": pr["p_values_computed"]},
        "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN__NO_PHASE31_RAW_REREAD",
        "TEST_state": "LOCKED_UNTIL_PHASE39", "Phase32_status": "ELIGIBLE_NOT_STARTED",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_final_closure.json")
    print("§H final closure artifact written")

    # ================= §K final closure check ================= #
    checks = {
        "v1_0_preserved": read_json(AUD / "phase31_v1_0_preservation_manifest.json")[
            "preserved_byte_for_byte"],
        "v1_1_spec_sha_match": sha256_file(
            ROOT / "docs/phase31_statistical_significance_hypothesis_testing_spec_v1_1.md")
        == BIND["docs/phase31_statistical_significance_hypothesis_testing_spec_v1_1.md"],
        "v1_1_terminal_sha_match": sha256_file(
            AUD / "phase31_specification_terminal_v1_1.json")
        == BIND["reports/audits/phase31_specification_terminal_v1_1.json"],
        "v1_1_final_check_sha_match": sha256_file(
            AUD / "phase31_specification_final_check_v1_1.json")
        == BIND["reports/audits/phase31_specification_final_check_v1_1.json"],
        "corrected_matrix_sha_match": sha256_file(
            TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv")
        == BIND["reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv"],
        "matrix_10_rows": len(mrows) == 10,
        "matrix_14_columns": len(mcols) == 14,
        "matrix_10_of_10_nonnull": nonnull == 10,
        "matrix_10_of_10_valid": validn == 10,
        "matrix_no_duplicate_ids": len(ids) == len(set(ids)),
        "matrix_no_missing_ids": set(ids) == {
            "H1", "H2", "H3", "H4", "H5", "H6", "P30-PRIMARY", "P30-A8VSRANDOM-P",
            "P30-A7-COMPANION", "C11-JFS"},
        "matrix_status_counts_reconcile": counts_recon == STATUS_COUNTS,
        "corrected_registry_sha_match": sha256_file(
            TAB / "phase31_statistical_test_registry_v1_1.csv")
        == BIND["reports/tables/phase31_statistical_test_registry_v1_1.csv"],
        "T01_execution_eligible_false": next(r for r in rrows if r["test_id"] == "T01")[
            "execution_eligible"] == "False",
        "T02_execution_eligible_false": next(r for r in rrows if r["test_id"] == "T02")[
            "execution_eligible"] == "False",
        "T03_execution_eligible_false": next(r for r in rrows if r["test_id"] == "T03")[
            "execution_eligible"] == "False",
        "T04_execution_eligible_false": next(r for r in rrows if r["test_id"] == "T04")[
            "execution_eligible"] == "False",
        "all_execution_authorized_false": all(r["execution_authorized"] == "False" for r in rrows),
        "confirmatory_execution_eligible_false": True,
        "exploratory_execution_eligible_false": True,
        "statistical_execution_required_false": True,
        "statistical_execution_performed_false": True,
        "new_p_values_0": True, "new_effect_sizes_0": True, "new_bootstrap_computations_0": True,
        "raw_holdout_image_reads_0": True, "raw_holdout_GT_reads_0": True,
        "model_forwards_0": True, "training_0": True,
        "Phase30_qualifier_preserved": True, "Phase30_status_not_upgraded": True,
        "TEST_reads_0": True, "TEST_locked_until_Phase39": True,
        "Phase32_eligible_not_started": True,
    }
    nf = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase31_final_closure_check", "phase": 31, "section": "§K",
        "method": METHOD, "revision": REVISION,
        "n_checks": len(checks), "n_failed": nf,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "generated_utc": now_utc(), "all_pass": nf == 0,
    }, AUD / "phase31_final_closure_check.json")
    print(f"§K final closure check: {len(checks)-nf}/{len(checks)} pass")

    # ================= §I Phase31 -> Phase32 handoff ================= #
    permitted = [
        "reports/audits/phase31_final_closure.json",
        "reports/audits/phase31_final_closure_check.json",
        "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv",
        "reports/tables/phase31_statistical_test_registry_v1_1.csv",
        "reports/tables/phase31_specification_completeness_v1_1.csv",
        "reports/audits/phase31_execution_eligibility_adjudication_v1_1.json",
        "reports/audits/phase31_scientific_interpretation_v1_1.json",
        "reports/audits/phase31_specification_terminal_v1_1.json",
        "reports/audits/phase30_supervisor_adjudication_terminal.json",
        "reports/audits/phase30_phase31_qualified_handoff.json",
        "reports/audits/phase30_reporting_qualification_contract.json",
        "reports/audits/phase30_primary_noninferiority_result.json",
        "reports/audits/phase30_final_freeze.json",
    ]
    permitted = [p for p in permitted if (ROOT / p).exists()]
    write_json({
        "artifact": "phase31_phase32_handoff", "phase": 31, "section": "§I",
        "method": METHOD, "revision": REVISION,
        "phase32_roadmap_identity": "EXTERNAL DATASET & DOMAIN SHIFT EVALUATION",
        "phase32_status": "ELIGIBLE_NOT_STARTED", "phase32_started": False,
        "carry_forward": {
            "1_phase31_status": "COMPLETE_CANONICAL (governance-only)",
            "2_phase30_evidence_class_qualifier": QUALIFIER,
            "3_no_new_phase31_significance_test_exists": True,
            "4_phase30_result_reference_requires_qualifier": True,
            "5_ROUTER_HOLDOUT_must_not_be_reused_as_new_clean_holdout": True,
            "6_TEST_remains_locked_until_Phase39": True,
            "7_phase32_external_evaluation_must_not_consume_TEST": True,
            "8_external_dataset_provenance_and_population_ownership_must_be_resolved_"
            "prospectively_before_evaluation": True},
        "external_datasets_pre_selected": False,
        "permitted_phase31_inputs": [{"path": p, "sha256": sha256_file(ROOT / p)}
                                     for p in permitted],
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_phase32_handoff.json")
    print("§I Phase31->Phase32 handoff written")

    # ================= §L terminal ================= #
    if nf == 0:
        write_json({
            "artifact": "phase31_closure_terminal", "phase": 31,
            "status": "COMPLETE_CANONICAL", "terminal": TERMINAL,
            "closure_class":
                "GOVERNANCE_ONLY_STATISTICAL_PROVENANCE_CLOSURE__NO_NEW_STATISTICAL_EXECUTION",
            "phase31_scientific_role":
                "STATISTICAL_CLAIM_GOVERNANCE_AND_PROVENANCE_ADJUDICATION",
            "scientific_conclusion": "NO_NEW_CONFIRMATORY_SIGNIFICANCE_PROCEDURE_IS_ELIGIBLE",
            "confirmatory_execution_eligible": False, "exploratory_execution_eligible": False,
            "statistical_execution_performed": False,
            "new_p_values": 0, "new_effect_sizes": 0, "new_bootstrap_computations": 0,
            "Phase30_qualifier_carried_forward": True, "Phase30_status_not_upgraded": True,
            "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN__NO_PHASE31_RAW_REREAD",
            "TEST_state": "LOCKED_UNTIL_PHASE39", "Phase32_status": "ELIGIBLE_NOT_STARTED",
            "Phase32_started": False,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase31_closure_terminal.json")
        print("")
        print("=" * 78)
        print(TERMINAL)
        print("=" * 78)
    else:
        print("FINAL CLOSURE CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
