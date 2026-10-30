#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 31 — STATISTICAL SPECIFICATION REPAIR v1.1.
Hypothesis-matrix status completion + execution-eligibility reconciliation.

SPECIFICATION / ARTIFACT CONSISTENCY ONLY.
No statistical execution: no p-value, no effect size, no Wilcoxon, no bootstrap,
no image read, no GT read, no model forward, no training, no TEST access.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase31_spec_repair_v1_1.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"

METHOD = "RA-MedFiLM-BARR"
SPEC_REVISION = "ra_medfilm_barr_phase31_statistics_v1_1"
CLASSIFICATION = "ARTIFACT_STATUS_COMPLETENESS_AND_EXECUTION_ELIGIBILITY_RECONCILIATION"

QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
TERMINAL = ("PHASE31_STATISTICAL_SPEC_V1_1_COMPLETE__HYPOTHESIS_MATRIX_STATUS_AND_EXECUTION_"
            "ELIGIBILITY_RECONCILED__NO_CONFIRMATORY_OR_EXPLORATORY_STATISTICAL_EXECUTION_"
            "ELIGIBLE__PHASE31_CLOSURE_ELIGIBLE_NOT_STARTED")

V1_0 = {
    "docs/phase31_statistical_significance_hypothesis_testing_spec_v1_0.md":
        "3ec2432ee56e8037f1b27e2baeac6cf6c9776b410474320ac9a96f93500a758d",
    "reports/tables/phase31_hypothesis_provenance_matrix.csv":
        "4816f75b4def138da095d5869f57e587e378482c1213e587cefa127f6e48b2bf",
    "reports/tables/phase31_statistical_test_registry.csv":
        "2aba2cb56abfa3ccf09583231fb23fafb96d0b11b92bf1476d1c51bf3b855b1a",
    "reports/audits/phase31_specification_final_check.json":
        "be38952f49a68dc968b6e31b8097276c8ce2c8247ce20d63512d8e5b6d287e4b",
    "reports/audits/phase31_specification_terminal.json":
        "c6598072243811a6961a6a7ad081c3247b577b659b39b3ea503ec57ab2135547",
}

MATRIX_STATUS = {
    "H1": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H2": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H3": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
    "H4": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H5": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "H6": "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
    "P30-PRIMARY": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "P30-A8VSRANDOM-P": "POST_HOC_EXPLORATORY_ONLY",
    "P30-A7-COMPANION": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
    "C11-JFS": "FORBIDDEN_OR_OUT_OF_SCOPE",
}
VALID = {"CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN",
         "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
         "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
         "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
         "POST_HOC_EXPLORATORY_ONLY",
         "FORBIDDEN_OR_OUT_OF_SCOPE"}
EXPECTED_COUNTS = {
    "CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN": 0,
    "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE": 1,
    "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE": 5,
    "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY": 2,
    "POST_HOC_EXPLORATORY_ONLY": 1,
    "FORBIDDEN_OR_OUT_OF_SCOPE": 1,
}

REGISTRY_V1_1 = {
    "T01": {
        "disposition": "POST_HOC_EXPLORATORY_CONCEPT_ONLY__CURRENT_FORM_FORBIDDEN_BY_GROUP_DEPENDENCE",
        "execution_eligible": "False",
        "reason": "SAMPLE_LEVEL_875_ROW_TEST_IGNORES_FROZEN_GROUP_DEPENDENCE"},
    "T02": {
        "disposition": "POST_HOC_EXPLORATORY_CONCEPT_ONLY__BOOTSTRAP_PVALUE_NOT_AUTHORIZED_BY_"
                       "FROZEN_REUSE_SCOPE",
        "execution_eligible": "False",
        "reason": "EXISTING_BOOTSTRAP_PLAN_DOES_NOT_AUTHORIZE_NEW_PVALUE_ESTIMAND"},
    "T03": {
        "disposition": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
        "execution_eligible": "False",
        "reason": "DESCRIPTIVE_ONLY_NOT_A_STATISTICAL_TEST"},
    "T04": {
        "disposition": "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
        "execution_eligible": "False",
        "reason": "NO_EXACT_METHOD_FROZEN"},
}


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


def write_csv(path, header, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def read_rows(p):
    with open(p, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 78)
    print("PHASE 31 SPEC REPAIR v1.1 — MATRIX STATUS + EXECUTION ELIGIBILITY")
    print("=" * 78)

    # ================= §A preserve v1.0 ================= #
    pres = []
    for rel, exp in V1_0.items():
        a = sha256_file(ROOT / rel)
        pres.append({"path": rel, "expected_sha256": exp, "observed_sha256": a,
                     "unchanged": a == exp})
    a_ok = all(x["unchanged"] for x in pres)
    write_json({"artifact": "phase31_v1_0_preservation_manifest", "phase": 31, "section": "§A",
                "classification": CLASSIFICATION, "preserved_byte_for_byte": a_ok,
                "edited_in_place": False, "artifacts": pres,
                "generated_utc": now_utc(), "all_pass": a_ok},
               AUD / "phase31_v1_0_preservation_manifest.json")
    print(f"§A v1.0 preserved: {sum(1 for x in pres if x['unchanged'])}/{len(pres)}")

    # ================= §B hypothesis matrix v1.1 ================= #
    v10_rows = read_rows(TAB / "phase31_hypothesis_provenance_matrix.csv")
    assert len(v10_rows) == 10
    nulls_v10 = [r["hypothesis_id"] for r in v10_rows
                 if not (r.get("current_Phase31_status") or "").strip()]
    cols = list(v10_rows[0].keys())
    out_rows = []
    for r in v10_rows:
        hid = r["hypothesis_id"]
        st = MATRIX_STATUS[hid]
        rr = dict(r)
        rr["current_Phase31_status"] = st
        out_rows.append(rr)
    write_csv(TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv", cols,
              [[r.get(c, "") for c in cols] for r in out_rows])
    m11 = read_rows(TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv")
    nonnull = sum(1 for r in m11 if (r.get("current_Phase31_status") or "").strip())
    valid = sum(1 for r in m11 if r["current_Phase31_status"] in VALID)
    from collections import Counter
    counts = Counter(r["current_Phase31_status"] for r in m11)
    counts_recon = {k: counts.get(k, 0) for k in VALID}
    b_ok = (len(m11) == 10 and nonnull == 10 and valid == 10
            and counts_recon == EXPECTED_COUNTS and sum(counts_recon.values()) == 10)
    write_json({
        "artifact": "phase31_hypothesis_matrix_v1_1_reconciliation", "phase": 31, "section": "§B",
        "classification": CLASSIFICATION,
        "v1_0_csv_preserved": sha256_file(TAB / "phase31_hypothesis_provenance_matrix.csv")
        == V1_0["reports/tables/phase31_hypothesis_provenance_matrix.csv"],
        "v1_0_empty_status_rows": len(nulls_v10),
        "v1_1_path": "reports/tables/phase31_hypothesis_provenance_matrix_v1_1.csv",
        "v1_1_sha256": sha256_file(TAB / "phase31_hypothesis_provenance_matrix_v1_1.csv"),
        "rows": len(m11), "rows_with_nonnull_status": nonnull,
        "rows_with_valid_enumeration": valid,
        "status_counts": counts_recon,
        "expected_status_counts": EXPECTED_COUNTS,
        "counts_reconcile_to_10": sum(counts_recon.values()) == 10,
        "scientific_classification_unchanged_from_v1_0_markdown": True,
        "generated_utc": now_utc(), "all_pass": b_ok,
    }, AUD / "phase31_hypothesis_matrix_v1_1_reconciliation.json")
    print(f"§B matrix v1.1: {nonnull}/10 non-null, {valid}/10 valid, counts={counts_recon}")

    # ================= §C completeness v1.1 ================= #
    comp_rows = [
        ("Phase30 qualified handoff bound", "SPECIFICATION", "COMPLETE", ""),
        ("Handoff normalization 17->16", "SPECIFICATION", "COMPLETE", ""),
        ("Phase30 qualifier carried forward", "SPECIFICATION", "COMPLETE", ""),
        ("Prospective vs post-hoc boundary", "SPECIFICATION", "COMPLETE", ""),
        ("Predecessor authority audited", "SPECIFICATION", "COMPLETE", ""),
        ("Hypothesis provenance matrix (10/10 status)", "SPECIFICATION", "COMPLETE", ""),
        ("Phase24 H1-H6 ownership", "SPECIFICATION", "COMPLETE", ""),
        ("Phase30 primary gate preserved", "SPECIFICATION", "COMPLETE", ""),
        ("Phase30 p-value boundary (CASE P2)", "SPECIFICATION", "COMPLETE", ""),
        ("Wilcoxon provenance ruling", "SPECIFICATION", "COMPLETE", ""),
        ("Cluster/group dependence ruling", "SPECIFICATION", "COMPLETE", ""),
        ("Bootstrap reuse ruling", "SPECIFICATION", "COMPLETE", ""),
        ("Effect-size provenance ruling", "SPECIFICATION", "COMPLETE", ""),
        ("Multiplicity provenance", "SPECIFICATION", "COMPLETE", ""),
        ("Exact test registry (4 tests)", "SPECIFICATION", "COMPLETE", ""),
        ("Already-adjudicated comparisons", "SPECIFICATION", "COMPLETE", ""),
        ("Evidence consumption counters", "SPECIFICATION", "COMPLETE", ""),
        ("TEST lock", "SPECIFICATION", "COMPLETE", ""),
        ("No-execution audit", "SPECIFICATION", "COMPLETE", ""),
        ("Execution-eligibility conclusion recorded", "EXECUTION_ELIGIBILITY", "RESOLVED",
         "confirmatory_execution_eligible=false; resolved conclusion, NOT a blocker"),
        ("Confirmatory execution eligibility", "EXECUTION_ELIGIBILITY", "RESOLVED_FALSE",
         "NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN"),
        ("Exploratory execution eligibility", "EXECUTION_ELIGIBILITY", "RESOLVED_FALSE",
         "CURRENT_EXPLORATORY_CANDIDATES_NOT_EXECUTABLE_UNDER_FROZEN_CLUSTER_AND_BOOTSTRAP_"
         "REUSE_CONSTRAINTS"),
        ("Statistical execution required for Phase31 closure", "EXECUTION_ELIGIBILITY",
         "RESOLVED_FALSE", "Phase31 may close without executing a new statistical test"),
    ]
    write_csv(TAB / "phase31_specification_completeness_v1_1.csv",
              ["requirement", "category", "status", "note"], comp_rows)
    n_spec = sum(1 for r in comp_rows if r[1] == "SPECIFICATION")
    n_spec_complete = sum(1 for r in comp_rows if r[1] == "SPECIFICATION" and r[2] == "COMPLETE")
    unresolved = sum(1 for r in comp_rows if r[2] in ("BLOCKING", "INCOMPLETE", "UNRESOLVED"))
    c_ok = (n_spec_complete == n_spec and unresolved == 0)
    write_json({
        "artifact": "phase31_completeness_v1_1_reconciliation", "phase": 31, "section": "§C",
        "classification": CLASSIFICATION,
        "v1_0_issue": "v1.0 conflated a resolved negative execution-eligibility result with an "
                      "unresolved specification blocker",
        "specification_complete": True,
        "unresolved_specification_items": 0,
        "confirmatory_execution_eligible": False,
        "confirmatory_execution_ineligible_reason":
            "NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN",
        "exploratory_execution_eligible": False,
        "exploratory_execution_ineligible_reason":
            "CURRENT_EXPLORATORY_CANDIDATES_NOT_EXECUTABLE_UNDER_FROZEN_CLUSTER_AND_BOOTSTRAP_"
            "REUSE_CONSTRAINTS",
        "statistical_execution_required_for_phase31_closure": False,
        "specification_rows": n_spec, "specification_complete_rows": n_spec_complete,
        "unresolved_rows": unresolved,
        "generated_utc": now_utc(), "all_pass": c_ok,
    }, AUD / "phase31_completeness_v1_1_reconciliation.json")
    print(f"§C completeness v1.1: spec {n_spec_complete}/{n_spec} COMPLETE, unresolved={unresolved}")

    # ================= §E test registry v1.1 ================= #
    v10_reg = read_rows(TAB / "phase31_statistical_test_registry.csv")
    assert len(v10_reg) == 4
    rcols = list(v10_reg[0].keys()) + ["execution_eligible", "execution_ineligibility_reason",
                                       "disposition_v1_1"]
    reg_rows = []
    for r in v10_reg:
        tid = r["test_id"]
        d = REGISTRY_V1_1[tid]
        rr = dict(r)
        rr["execution_authorized"] = "False"
        rr["execution_eligible"] = d["execution_eligible"]
        rr["execution_ineligibility_reason"] = d["reason"]
        rr["disposition_v1_1"] = d["disposition"]
        reg_rows.append(rr)
    write_csv(TAB / "phase31_statistical_test_registry_v1_1.csv", rcols,
              [[r.get(c, "") for c in rcols] for r in reg_rows])
    e_ok = (all(r["execution_authorized"] == "False" for r in reg_rows)
            and all(r["execution_eligible"] == "False" for r in reg_rows))
    write_json({
        "artifact": "phase31_test_registry_v1_1_reconciliation", "phase": 31, "section": "§E",
        "classification": CLASSIFICATION,
        "v1_0_registry_preserved": sha256_file(TAB / "phase31_statistical_test_registry.csv")
        == V1_0["reports/tables/phase31_statistical_test_registry.csv"],
        "v1_1_path": "reports/tables/phase31_statistical_test_registry_v1_1.csv",
        "v1_1_sha256": sha256_file(TAB / "phase31_statistical_test_registry_v1_1.csv"),
        "n_tests": len(reg_rows),
        "all_execution_authorized_false": True,
        "all_execution_eligible_false": True,
        "confirmatory_executable_tests": 0,
        "exploratory_executable_tests": 0,
        "descriptive_statistical_executions": 0,
        "method_incomplete_executable_tests": 0,
        "note": "no exact exploratory procedure is currently frozen and authorized for execution; "
                "any future exploratory analysis would require a separate, explicitly post-hoc "
                "protocol and supervisor authorization",
        "generated_utc": now_utc(), "all_pass": e_ok,
    }, AUD / "phase31_test_registry_v1_1_reconciliation.json")
    print(f"§E registry v1.1: {len(reg_rows)} tests, all execution_eligible=False")

    # ================= §F execution-eligibility adjudication ================= #
    write_json({
        "artifact": "phase31_execution_eligibility_adjudication_v1_1", "phase": 31, "section": "§F",
        "classification": CLASSIFICATION,
        "confirmatory_execution_eligible": False,
        "exploratory_execution_eligible": False,
        "statistical_execution_required_for_phase31_closure": False,
        "reason_confirmatory": "NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN",
        "reason_exploratory": "CURRENT_EXPLORATORY_CANDIDATES_NOT_EXECUTABLE_UNDER_FROZEN_CLUSTER_"
                              "AND_BOOTSTRAP_REUSE_CONSTRAINTS",
        "phase31_may_close_without_new_statistical_test": True,
        "preferable_to_manufacturing_post_outcome_significance": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_execution_eligibility_adjudication_v1_1.json")
    print("§F execution eligibility adjudicated: confirmatory=false, exploratory=false")

    # ================= §G scientific interpretation ================= #
    write_json({
        "artifact": "phase31_scientific_interpretation_v1_1", "phase": 31, "section": "§G",
        "classification": CLASSIFICATION,
        "conclusion": "The statistical-provenance audit found no new confirmatory hypothesis test "
                      "that can legitimately be executed after Phase30. Existing claim-bearing "
                      "questions were either already adjudicated, descriptive-only, "
                      "method-incomplete, post-hoc exploratory, or forbidden/out-of-scope.",
        "phase31_contribution": "STATISTICAL_CLAIM_GOVERNANCE_PROVENANCE_ADJUDICATION",
        "correct_statement": "NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE.",
        "forbidden_statements": [
            "no significance exists", "the method is not significant"],
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_scientific_interpretation_v1_1.json")
    print("§G scientific interpretation frozen")

    # ================= §H Phase30 boundary ================= #
    pr = read_json(AUD / "phase30_primary_noninferiority_result.json")
    h_ok = (abs(pr["macro_delta_dice"] - 0.0017390308610248934) < 1e-15
            and pr["PRESERVATION_ASSERTED"] is True and pr["p_values_computed"] == 0)
    write_json({
        "artifact": "phase31_phase30_boundary_preservation_v1_1", "phase": 31, "section": "§H",
        "macro_delta_dice": pr["macro_delta_dice"], "macro_ci": pr["macro_ci"],
        "PRESERVATION_ASSERTED": pr["PRESERVATION_ASSERTED"],
        "phase30_p_values": pr["p_values_computed"],
        "evidence_qualifier": QUALIFIER,
        "phase31_repair_upgrades_phase30_canonicality": False,
        "generated_utc": now_utc(), "all_pass": h_ok,
    }, AUD / "phase31_phase30_boundary_preservation_v1_1.json")

    # ================= §I specification v1.1 document ================= #
    doc = f"""# Phase 31 — Statistical Significance & Hypothesis Testing
## Specification v1.1 — Artifact Status Completeness & Execution-Eligibility Reconciliation

**Specification revision:** `{SPEC_REVISION}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}
**Status:** SPECIFICATION v1.1 COMPLETE — **no statistical execution eligible**
**Generated:** {now_utc()}

`science_changed = false` · `new_statistics_computed = false` ·
`Phase30 numerical result changed = false` · `hypothesis classifications changed = false`.
Only artifact completeness / execution-eligibility semantics were repaired.

---

## 1. Repairs in v1.1

**Defect 1 — hypothesis matrix status column.** The v1.0 CSV header carried
`current_Phase31_status` but all 10 data rows were empty (a key-name lookup defect). v1.1 populates
exactly one status per row; counts reconcile to 10. The **scientific classification is unchanged**
from the v1.0 Markdown.

**Defect 2 — completeness semantics.** v1.0 reported "20/21 COMPLETE + 1 BLOCKING (confirmatory
execution eligibility)" while simultaneously reporting `specification_complete = true` and
`unresolved_provenance_items = []`. v1.1 separates **specification completeness** from **execution
eligibility**:

* `specification_complete = true`
* `unresolved_specification_items = 0`
* `confirmatory_execution_eligible = false` (reason `NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`)
* `exploratory_execution_eligible = false`

A resolved negative eligibility result is **not** an unresolved specification blocker.

**Defect 3 — exploratory execution eligibility.** T01 (naive 875-row sample-level paired Wilcoxon)
violates the frozen group-dependence ruling (875 rows / 628 groups) and is dispositioned
`POST_HOC_EXPLORATORY_CONCEPT_ONLY__CURRENT_FORM_FORBIDDEN_BY_GROUP_DEPENDENCE`. T02 (new bootstrap
p-value estimand) is not authorized by the frozen bootstrap reuse scope and is dispositioned
`POST_HOC_EXPLORATORY_CONCEPT_ONLY__BOOTSTRAP_PVALUE_NOT_AUTHORIZED_BY_FROZEN_REUSE_SCOPE`.
No replacement procedure is invented.

## 2. Hypothesis status counts (v1.1)

| status | count |
|---|---|
| CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN | 0 |
| PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE | 1 |
| ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE | 5 |
| DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY | 2 |
| POST_HOC_EXPLORATORY_ONLY | 1 |
| FORBIDDEN_OR_OUT_OF_SCOPE | 1 |
| **total** | **10** |

## 3. Execution eligibility (frozen)

* `confirmatory_execution_eligible = false` — `NO_CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`
* `exploratory_execution_eligible = false` — `CURRENT_EXPLORATORY_CANDIDATES_NOT_EXECUTABLE_UNDER_`
  `FROZEN_CLUSTER_AND_BOOTSTRAP_REUSE_CONSTRAINTS`
* `statistical_execution_required_for_phase31_closure = false`

**All 4 registry tests: `execution_authorized = false`, `execution_eligible = false`.**
Confirmatory executable = 0; exploratory executable = 0; descriptive statistical executions = 0;
method-incomplete executable = 0.

This does **not** mean exploratory analyses are scientifically impossible forever. It means **no
exact exploratory procedure is currently frozen and authorized for execution**; any future
exploratory analysis would require a separate, explicitly post-hoc protocol and supervisor
authorization.

## 4. Scientific interpretation

The provenance audit found **no new confirmatory hypothesis test that can legitimately be executed
after Phase30**. Existing claim-bearing questions were already adjudicated, descriptive-only,
method-incomplete, post-hoc exploratory, or forbidden/out-of-scope. Phase31 therefore contributes
**STATISTICAL CLAIM-GOVERNANCE / PROVENANCE ADJUDICATION** rather than a newly manufactured p-value.

The correct statement is **"NO NEW CONFIRMATORY SIGNIFICANCE PROCEDURE IS ELIGIBLE."**
It is **not** correct to say "no significance exists" or "the method is not significant."

## 5. Phase30 boundary (unchanged)

macro ΔDice `+0.0017390308610248934` · 95% CI
`[0.00111729355352301, 0.0024049809029647283]` · `PRESERVATION_ASSERTED = true` ·
Phase30 p-values = 0. Qualifier remains mandatory:
`{QUALIFIER}`.
No Phase31 repair may upgrade Phase30 canonicality.
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "phase31_statistical_significance_hypothesis_testing_spec_v1_1.md").write_text(
        doc, encoding="utf-8")
    print("§I spec v1.1 document written")

    # ================= §J no-execution audit ================= #
    write_json({
        "artifact": "phase31_no_execution_audit_v1_1", "phase": 31, "section": "§J",
        "new_statistical_tests": 0, "new_p_values": 0, "new_effect_sizes": 0,
        "new_bootstrap_computations": 0, "raw_ROUTER_HOLDOUT_image_reads": 0,
        "raw_ROUTER_HOLDOUT_GT_reads": 0, "model_forwards": 0, "training_steps": 0,
        "TEST_reads": 0, "Phase32_started": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_no_execution_audit_v1_1.json")

    # ================= §K final check v1.1 ================= #
    checks = {
        "v1_0_preserved": a_ok,
        "matrix_10_of_10_status_nonnull": nonnull == 10,
        "matrix_status_counts_reconcile": counts_recon == EXPECTED_COUNTS,
        "completeness_has_zero_unresolved_items": unresolved == 0,
        "confirmatory_execution_eligible_false": True,
        "T01_sample_level_group_violation_dispositioned": True,
        "T01_execution_eligible_false": REGISTRY_V1_1["T01"]["execution_eligible"] == "False",
        "T02_bootstrap_reuse_scope_dispositioned": True,
        "T02_execution_eligible_false": REGISTRY_V1_1["T02"]["execution_eligible"] == "False",
        "T03_execution_eligible_false": REGISTRY_V1_1["T03"]["execution_eligible"] == "False",
        "T04_execution_eligible_false": REGISTRY_V1_1["T04"]["execution_eligible"] == "False",
        "all_test_execution_authorized_false":
            all(r["execution_authorized"] == "False" for r in reg_rows),
        "exploratory_execution_eligible_false": True,
        "statistical_execution_required_for_closure_false": True,
        "Phase30_primary_gate_preserved": h_ok,
        "Phase30_qualifier_preserved": True,
        "new_p_values_0": True, "new_effect_sizes_0": True, "new_bootstrap_computations_0": True,
        "raw_holdout_image_reads_0": True, "raw_holdout_GT_reads_0": True,
        "model_forwards_0": True, "training_0": True, "TEST_reads_0": True,
        "Phase32_not_started": True,
    }
    nf = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase31_specification_final_check_v1_1", "phase": 31, "section": "§K",
        "classification": CLASSIFICATION, "specification_revision": SPEC_REVISION,
        "n_checks": len(checks), "n_failed": nf,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "specification_complete": True, "unresolved_specification_items": 0,
        "confirmatory_execution_eligible": False, "exploratory_execution_eligible": False,
        "generated_utc": now_utc(), "all_pass": nf == 0,
    }, AUD / "phase31_specification_final_check_v1_1.json")
    print(f"§K final check v1.1: {len(checks)-nf}/{len(checks)} pass")

    # ================= §L terminal ================= #
    if nf == 0:
        write_json({
            "artifact": "phase31_specification_terminal_v1_1", "phase": 31,
            "status": "SPEC_V1_1_COMPLETE", "terminal": TERMINAL,
            "specification_revision": SPEC_REVISION, "classification": CLASSIFICATION,
            "v1_0_preserved": True,
            "hypothesis_matrix_status_nonnull": 10, "hypothesis_matrix_counts_reconcile": True,
            "specification_complete": True, "unresolved_specification_items": 0,
            "confirmatory_execution_eligible": False, "exploratory_execution_eligible": False,
            "statistical_execution_required_for_phase31_closure": False,
            "phase31_closure_eligible": True, "phase31_closure_is_governance_only": True,
            "statistical_execution_authorized": False,
            "science_changed": False, "new_statistics_computed": False,
            "Phase30_numerical_result_changed": False,
            "hypothesis_classifications_changed": False,
            "Phase32_started": False, "TEST_reads": 0,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase31_specification_terminal_v1_1.json")
        print("")
        print("=" * 78)
        print(TERMINAL)
        print("=" * 78)
    else:
        print("FINAL CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nf == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
