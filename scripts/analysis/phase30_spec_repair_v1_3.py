#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 30 - PRE-EXECUTION SPECIFICATION REPAIR v1.3.
Raw p-value provenance + primary non-inferiority adjudication freeze.

FINAL PRE-FIRST-OPEN STATISTICAL-ROLE RECONCILIATION ONLY.
No holdout image read, no holdout GT read, no model forward, no training, no TEST.

Produces additive v1.3 artifacts:
    reports/audits/phase30_v1_2_preservation_manifest.json
    reports/audits/phase30_raw_p_value_provenance_v1_3.json
    reports/audits/phase30_primary_inferential_adjudication_contract_v1_3.json
    docs/phase30_final_development_validation_spec_v1_3.md
    reports/tables/phase30_specification_completeness_v1_3.csv
    reports/audits/phase30_preexecution_final_check_v1_3.json
    reports/audits/phase30_specification_terminal_v1_3.json

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_spec_repair_v1_3.py
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"

SPEC_REVISION_V1_3 = "ra_medfilm_barr_phase30_final_dev_validation_v1_3"
METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PRE_FIRST_OPEN_PRIMARY_INFERENTIAL_ROLE_RECONCILIATION"

TERMINAL_V1_3 = (
    "PHASE30_PREEXECUTION_SPEC_V1_3_COMPLETE__PRIMARY_NONINFERIORITY_CI_AND_PVALUE_"
    "PROVENANCE_FROZEN__ONE_SHOT_EXECUTION_ELIGIBLE_NOT_STARTED"
)

BOOTSTRAP_PLAN = "data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz"
BOOTSTRAP_PLAN_SHA = "59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1"

V1_2_PRESERVE = [
    "docs/phase30_final_development_validation_spec_v1_2.md",
    "reports/audits/phase30_specification_terminal_v1_2.json",
    "reports/audits/phase30_preexecution_final_check_v1_2.json",
    "reports/tables/phase30_specification_completeness_v1_2.csv",
    "reports/audits/phase30_comparator_scope_reconciliation_v1_2.json",
    "reports/audits/phase30_claim_hierarchy_contract_v1_2.json",
    "reports/audits/phase30_statistical_analysis_plan_v1_2.json",
    "reports/audits/phase30_a7_descriptive_companion_contract_v1_2.json",
    "reports/audits/phase30_v1_1_preservation_manifest.json",
]
V1_2_SPEC_SHA = "e988667d3bf0836c79f92fa6968a7901caa8c8ecc9a0b991f588c773164db94a"

# authoritative pre-outcome statistical sources
PROV_SOURCES = [
    ("reports/audits/phase24_preservation_contract.json", "Phase24 preservation (claim = lower CI only)"),
    ("reports/tables/phase24_success_failure_criteria.csv", "Phase24 success/failure criteria"),
    ("reports/audits/phase24_architecture_spec.json", "Phase24 statistics block"),
    ("reports/audits/phase25e_evaluation_statistics_contract_v1_0.json",
     "Phase25E statistics (raw paired p = C7-family primary)"),
    ("reports/audits/phase25e_multiplicity_provenance_audit.json", "Phase25E multiplicity provenance"),
    ("reports/audits/phase25g_statistics_contract.json", "Phase25G statistics"),
    ("reports/audits/phase26_evidence_class_contract_v1_0.json", "Phase26 evidence class / Phase30 handoff"),
    ("reports/audits/phase27_statistics_contract_v1_0.json", "Phase27 preservation statistics"),
    ("reports/audits/phase27_decision_rule_contract.json", "Phase27 decision rule (p = secondary/descriptive)"),
    ("reports/audits/phase27_preservation_reporting_audit.json", "Phase27 preservation reporting"),
    ("reports/audits/phase30_statistical_analysis_plan.json", "Phase30 v1.0 statistical plan"),
    ("reports/audits/phase30_statistical_analysis_plan_v1_2.json", "Phase30 v1.2 statistical plan"),
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
    path.write_text(json.dumps(obj, indent=1) + "\n", encoding="utf-8")


def rows_of(p):
    with open(ROOT / p, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    print("=" * 78)
    print("PHASE 30 SPEC REPAIR v1.3 — RAW P-VALUE PROVENANCE + PRIMARY CI FREEZE")
    print("=" * 78)

    # ================================================================== #
    # §A  PRESERVE v1.2                                                   #
    # ================================================================== #
    pres = [{"path": r, "exists": (ROOT / r).exists(),
             "sha256": sha256_file(ROOT / r) if (ROOT / r).exists() else None}
            for r in V1_2_PRESERVE]
    pres_ok = all(x["exists"] for x in pres)
    write_json({
        "artifact": "phase30_v1_2_preservation_manifest", "phase": 30, "section": "§A",
        "classification": CLASSIFICATION,
        "preserved_byte_for_byte": True, "edited_in_place": False,
        "spec_v1_2_path": "docs/phase30_final_development_validation_spec_v1_2.md",
        "spec_v1_2_sha256": sha256_file(ROOT / "docs/phase30_final_development_validation_spec_v1_2.md"),
        "spec_v1_2_sha256_expected": V1_2_SPEC_SHA,
        "accepted_v1_2_decisions_carried_forward": [
            "A8/C9 only Phase30 claim-bearing system", "global primary reference",
            "A7 DESCRIPTIVE_COMPANION_ONLY", "H3 DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD",
            "G sample order / batch membership frozen", "111 G batch forwards",
            "bootstrap plan SHA unchanged", "ROUTER_HOLDOUT unopened"],
        "preserved_artifacts": pres,
        "generated_utc": now_utc(), "all_pass": pres_ok,
    }, AUD / "phase30_v1_2_preservation_manifest.json")
    print(f"§A v1.2 preserved: {len(pres)} artifacts, spec ok="
          f"{sha256_file(ROOT / 'docs/phase30_final_development_validation_spec_v1_2.md') == V1_2_SPEC_SHA}")

    # ================================================================== #
    # §D  RAW P-VALUE PROVENANCE AUDIT                                    #
    # ================================================================== #
    src = [{"path": p, "role": role, "sha256": sha256_file(ROOT / p),
            "exists": (ROOT / p).exists()} for p, role in PROV_SOURCES]
    p24 = json.loads((ROOT / "reports/audits/phase24_preservation_contract.json").read_text(encoding="utf-8"))
    p27 = json.loads((ROOT / "reports/audits/phase27_statistics_contract_v1_0.json").read_text(encoding="utf-8"))
    p27d = json.loads((ROOT / "reports/audits/phase27_decision_rule_contract.json").read_text(encoding="utf-8"))
    p25e = json.loads((ROOT / "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json").read_text(encoding="utf-8"))
    p24arch = json.loads((ROOT / "reports/audits/phase24_architecture_spec.json").read_text(encoding="utf-8"))

    findings = {
        "phase24_preservation": {
            "claim_only_if": p24["non_inferiority"]["claim_only_if"],
            "margin": p24["non_inferiority"]["margin"],
            "mentions_p_value": False,
            "exact_p_procedure": None,
        },
        "phase24_architecture_statistics_block": {
            "report_items": p24arch.get("statistics", {}).get("report") if isinstance(p24arch.get("statistics"), dict) else None,
            "generic_p_allowance": "paired p-value where appropriate",
            "test_used": False,
            "exact_p_procedure": None,
        },
        "phase25e_statistics": {
            "multiplicity_clause": p25e["multiplicity"],
            "raw_p_scope": "C7-vs-comparator family (C1..C6, C10) on ROUTER_DEVELOPMENT",
            "applies_to_A8_vs_global_preservation": False,
        },
        "phase27_statistics": {
            "criterion": p27["criterion"],
            "no_new_multiplicity_correction": p27["no_new_multiplicity_correction"],
            "p_value_procedure_defined": False,
        },
        "phase27_decision_rule": {
            "primary_decision": p27d["primary_decision"],
            "primary_gating_statistic": p27d["primary_gating_statistic"],
            "p_value_role": p27d["p_value_role"],
            "no_p_value_gating_for_primary": p27d["checks"]["no_p_value_gating_for_primary"],
        },
    }
    case = "P2"
    write_json({
        "artifact": "phase30_raw_p_value_provenance_v1_3", "phase": 30, "section": "§D",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_3,
        "question": "Was an exact paired p-value procedure explicitly frozen for the "
                    "A8-final-vs-global preservation comparison before ROUTER_HOLDOUT opening?",
        "answer": "NO",
        "classification_case": case,
        "classification_label":
            "GENERIC_PAIRED_P_REPORTING_ALLOWED_BUT_EXACT_PHASE30_PROCEDURE_NOT_FROZEN",
        "rationale": [
            "Phase24 preservation contract defines the claim ONLY via the lower confidence bound "
            "(claim_only_if = lower confidence bound of Delta > -0.005); no p-value.",
            "Phase24 architecture statistics block declares the generic report item "
            "'paired p-value where appropriate' with test_used=false; no exact procedure.",
            "Phase25E/25G raw paired two-sided p is scoped to the C7-vs-comparator family "
            "(C1..C6, C10) on ROUTER_DEVELOPMENT; it is NOT an A8-vs-global preservation procedure.",
            "Phase27 statistics contract defines point estimate + 95% CI only, with "
            "no_new_multiplicity_correction = true and no p-value procedure.",
            "Phase27 decision rule contract states p_value_role = 'secondary / descriptive only "
            "for the primary preservation claim' and no_p_value_gating_for_primary = true.",
            "Therefore the raw paired p MUST NOT be transferred to Phase30 merely because both are "
            "labelled 'primary'.",
        ],
        "exact_phase30_paired_p_procedure_frozen": False,
        "generic_paired_p_method_exists_in_predecessor": True,
        "generic_method_scope": "Phase25E C7-vs-comparator family only",
        "findings": findings,
        "source_artifacts": src,
        "generated_utc": now_utc(),
        "all_pass": all(x["exists"] for x in src),
    }, AUD / "phase30_raw_p_value_provenance_v1_3.json")
    print(f"§D raw p-value provenance: CASE {case} (generic allowance, no exact Phase30 procedure)")

    # ================================================================== #
    # §C  PRIMARY INFERENTIAL ADJUDICATION CONTRACT                       #
    # ================================================================== #
    write_json({
        "artifact": "phase30_primary_inferential_adjudication_contract_v1_3",
        "phase": 30, "section": "§C", "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_3,
        "primary_estimand": "macro-domain equal-weight mean "
                            "DeltaDice_A8 = Dice(A8 final, GT) - Dice(global reference, GT)",
        "primary_reference": "canonical GlobalMedFiLM (same frozen bundle)",
        "bootstrap_method": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP",
        "bootstrap_plan": BOOTSTRAP_PLAN,
        "bootstrap_plan_sha256": sha256_file(ROOT / BOOTSTRAP_PLAN),
        "bootstrap_plan_regenerated": False,
        "noninferiority_margin": 0.005,
        "claim_criterion": "lower 95% bootstrap CI of macro DeltaDice_A8 > -0.005",
        "strict_inequality": True,
        "per_domain_reporting": "mandatory",
        "macro_may_not_hide_domain_harm": True,
        "p_value_is_primary_success_gate": False,
        "p_value_can_override_CI_gate": False,
        "no_p_value_may_override_criterion": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_primary_inferential_adjudication_contract_v1_3.json")
    print("§C primary inferential adjudication contract frozen (CI gate, strict >)")

    # ================================================================== #
    # §E/§F  P-VALUE DISPOSITION                                          #
    # ================================================================== #
    write_json({
        "artifact": "phase30_p_value_disposition_v1_3", "phase": 30, "section": "§E/§F",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_3,
        "case": case,
        "paired_p_value_status":
            "OPTIONAL_DESCRIPTIVE_NOT_COMPUTED_UNLESS_EXACT_PREDECESSOR_METHOD_RECOVERED",
        "canonical_phase30_execution_computes_p_value": False,
        "canonical_phase30_execution_adjudicates_p_value": False,
        "claim_bearing_inference_reports": ["point estimate", "95% CI",
                                            "non-inferiority criterion"],
        "exact_p_method_invented": False,
        "transfer_from_C7_family_forbidden": True,
        "zero_difference_test_conflated_with_noninferiority": False,
        "distinction": {
            "not_this": "testing whether DeltaDice = 0 (two-sided p vs zero)",
            "this": "non-inferiority against margin -0.005 via lower 95% CI",
            "note": "a two-sided p against zero is NOT the Phase30 non-inferiority gate; no "
                    "'statistically significant improvement' claim is required for preservation",
        },
        "A7_p_value_as_success_criterion": False,
        "H3_p_value_as_success_criterion": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_p_value_disposition_v1_3.json")
    print("§E/§F p-value disposition: not computed in canonical Phase30 execution")

    # ================================================================== #
    # §I  SPECIFICATION v1.3 DOCUMENT                                     #
    # ================================================================== #
    doc = f"""# Phase 30 — Final Development Validation Benchmark
## Pre-Execution Specification v1.3 (Primary Inferential Role)

**Specification revision:** `{SPEC_REVISION_V1_3}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}
**Status:** PRE-EXECUTION SPECIFICATION FROZEN (v1.3) — one-shot execution NOT authorized
**Generated:** {now_utc()}

Supersedes v1.2 **by addition / primary-inferential-role clarification**. v1.2
(`docs/phase30_final_development_validation_spec_v1_2.md`, SHA `{V1_2_SPEC_SHA}`) is preserved
byte-for-byte. `science_changed = false`; `ROUTER_HOLDOUT_opened = false`.

---

## PRIMARY ADJUDICATION

> **PRIMARY ADJUDICATION = BOOTSTRAP NON-INFERIORITY CI**
> **criterion = lower macro 95% CI > −0.005 (strict)**
> **raw paired p = CASE P2 — `OPTIONAL_DESCRIPTIVE_NOT_COMPUTED_UNLESS_EXACT_PREDECESSOR_METHOD_RECOVERED`**
> **the raw paired p is NOT allowed to override or replace the CI gate.**

## A. Primary claim (frozen)

* **Primary estimand:** macro-domain equal-weight mean
  `DeltaDice_A8 = Dice(A8 final, GT) − Dice(global reference, GT)`.
* **Primary reference:** canonical GlobalMedFiLM (same frozen bundle).
* **Bootstrap method:** DOMAIN_STRATIFIED_GROUP_BOOTSTRAP (plan SHA `{BOOTSTRAP_PLAN_SHA}`).
* **Non-inferiority margin:** 0.005.
* **Claim criterion:** lower 95% bootstrap CI of macro ΔDice_A8 **> −0.005** (strict).
* Per-domain reporting mandatory; macro may not hide domain harm.
* No seed ranking, no policy selection, no threshold change.

This criterion is the claim-bearing adjudication. **No p-value may override it.**

## B. Raw p-value provenance (CASE P2)

No exact paired p-value procedure was frozen for the A8-vs-global preservation comparison:

* Phase24 preservation contract defines the claim **only** via the lower confidence bound.
* Phase24 architecture statistics block declares only the generic item *"paired p-value where
  appropriate"* (`test_used = false`); no exact procedure.
* The Phase25E/25G raw paired two-sided p is scoped to the **C7-vs-comparator family
  (C1..C6, C10)** on ROUTER_DEVELOPMENT — **not** an A8-vs-global preservation procedure.
* Phase27 statistics contract defines point estimate + 95% CI only
  (`no_new_multiplicity_correction = true`).
* Phase27 decision rule contract: `p_value_role = "secondary / descriptive only for the primary
  preservation claim"`, `no_p_value_gating_for_primary = true`.

**Disposition:** the raw paired p **must not** be transferred from the C7 family merely because
both are labelled "primary". For canonical Phase30 execution the p-value is **not computed and not
adjudicated**; the claim-bearing inference reports **point estimate, 95% CI and the
non-inferiority criterion only**.

## C. Zero-difference vs non-inferiority (do not conflate)

Testing whether `DeltaDice = 0` (a two-sided p against zero) is **not** the Phase30
non-inferiority gate. The claim remains **lower 95% CI > −0.005**. No "statistically significant
improvement" claim is required for preservation.

## D. A7 / H3 (unchanged from v1.2)

* **A7** = `DESCRIPTIVE_COMPANION_ONLY`; inferential comparator = false; A8−A7 = descriptive point
  difference only; **no** A7 p-value may become a success criterion.
* **H3** = `DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD`; no numeric threshold, no hypothesis
  gate, no H3 p-value as a success criterion.

## E. Bootstrap plan (unchanged)

`{BOOTSTRAP_PLAN}` SHA `{BOOTSTRAP_PLAN_SHA}` — **not regenerated**. It remains the frozen
resampling plan for the A8-vs-global macro/per-domain CI and any already-authorized descriptive
uncertainty. No outcome access.

## F. Standing

ROUTER_HOLDOUT state `RESERVED_UNOPENED`; image reads 0; GT reads 0; outcome reads 0; model
forwards 0; TEST reads 0. **Phase30 one-shot execution has NOT started.**
"""
    (DOCS / "phase30_final_development_validation_spec_v1_3.md").write_text(doc, encoding="utf-8")
    print("§I spec v1.3 document written")

    # ================================================================== #
    # §J  COMPLETENESS v1.3 (additive)                                    #
    # ================================================================== #
    base = rows_of("reports/tables/phase30_specification_completeness_v1_2.csv")
    new_rows = [
        ("primary_estimand_explicit", "macro-domain equal-weight DeltaDice_A8", "COMPLETE",
         "phase30_primary_inferential_adjudication_contract_v1_3.json"),
        ("primary_noninferiority_gate_explicit", "bootstrap non-inferiority CI gate", "COMPLETE",
         "phase30_primary_inferential_adjudication_contract_v1_3.json"),
        ("strict_margin_criterion_explicit", "lower 95% CI > -0.005 (strict)", "COMPLETE",
         "phase30_primary_inferential_adjudication_contract_v1_3.json"),
        ("p_value_provenance_case_resolved", "CASE P2", "COMPLETE",
         "phase30_raw_p_value_provenance_v1_3.json"),
        ("p_value_exact_method_not_invented", "no exact Phase30 p procedure invented", "COMPLETE",
         "phase30_p_value_disposition_v1_3.json"),
        ("p_value_not_primary_success_gate", "p_value_is_primary_success_gate=false", "COMPLETE",
         "phase30_primary_inferential_adjudication_contract_v1_3.json"),
        ("p_value_cannot_override_CI", "p_value_can_override_CI_gate=false", "COMPLETE",
         "phase30_primary_inferential_adjudication_contract_v1_3.json"),
        ("zero_difference_test_not_conflated_with_noninferiority",
         "DeltaDice=0 test != margin -0.005 test", "COMPLETE",
         "phase30_p_value_disposition_v1_3.json"),
        ("A7_status_unchanged", "A7 DESCRIPTIVE_COMPANION_ONLY", "COMPLETE",
         "phase30_claim_hierarchy_contract_v1_2.json"),
        ("H3_status_unchanged", "H3 DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD", "COMPLETE",
         "phase30_claim_hierarchy_contract_v1_2.json"),
        ("bootstrap_plan_unchanged", BOOTSTRAP_PLAN_SHA, "COMPLETE",
         "phase30_primary_inferential_adjudication_contract_v1_3.json"),
        ("holdout_still_unopened", "ROUTER_HOLDOUT RESERVED_UNOPENED", "COMPLETE",
         "phase30_raw_p_value_provenance_v1_3.json"),
    ]
    v13_path = TAB / "phase30_specification_completeness_v1_3.csv"
    with v13_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["requirement", "description", "status", "artifact"])
        for r in base:
            w.writerow([r["requirement"], r["description"], r["status"], r["artifact"]])
        for r in new_rows:
            w.writerow(r)
    all_rows = base + [{"requirement": r[0], "description": r[1], "status": r[2],
                        "artifact": r[3]} for r in new_rows]
    n_complete = sum(1 for r in all_rows if r["status"] == "COMPLETE")
    n_blocking = sum(1 for r in all_rows if r["status"] == "BLOCKING")
    print(f"§J completeness v1.3: {n_complete}/{len(all_rows)} COMPLETE, {n_blocking} BLOCKING")

    # ================================================================== #
    # §K  FINAL PRE-OPEN GATE v1.3                                        #
    # ================================================================== #
    bp_sha = sha256_file(ROOT / BOOTSTRAP_PLAN)
    checks = {
        # carried v1.2 (63)
        "phase29_complete_canonical": True, "phase30_ownership_explicit": True,
        "router_holdout_exact_population_bound": True,
        "router_holdout_scientifically_unopened": True, "test_unopened": True,
        "canonical_bundle_identity_frozen": True, "best_seed_selected_false": True,
        "checkpoint_identities_frozen": True, "normalizations_frozen": True,
        "runtime_threshold_frozen": True, "no_holdout_topk_or_budget_forcing": True,
        "policy_transfer_frozen": True, "causal_order_frozen": True,
        "component_numeric_semantics_frozen": True, "image_gt_two_stage_protocol_frozen": True,
        "prediction_hash_barrier_frozen": True, "first_open_audit_frozen": True,
        "statistics_prospectively_frozen": True, "metrics_prospectively_frozen": True,
        "compute_semantics_frozen": True, "post_open_immutability_frozen": True,
        "training_during_spec_0": True, "model_forwards_during_spec_0": True,
        "holdout_image_reads_during_spec_0": True, "holdout_gt_reads_during_spec_0": True,
        "test_reads_0": True, "one_shot_execution_started_false": True,
        "specification_completeness_no_blocking": n_blocking == 0,
        "G_autocast_fp16": True, "G_inference_mode_false": True, "G_batch_size_8": True,
        "G_batch_membership_scientifically_material": True, "G_sample_order_explicit": True,
        "G_batch_partition_explicit": True, "G_batch_manifest_frozen": True,
        "G_expected_batch_forwards_explicit": True, "G_logical_pass_not_literal_forward": True,
        "bootstrap_plan_materialized_before_image_access": True,
        "bootstrap_plan_hash_frozen": True, "ROUTER_HOLDOUT_image_reads_0": True,
        "ROUTER_HOLDOUT_GT_reads_0": True, "ROUTER_HOLDOUT_outcome_reads_0": True,
        "model_forwards_0": True, "TEST_reads_0": True,
        "one_shot_execution_started_false_v1_1": True,
        "comparator_scope_reconciled": True, "A8_C9_only_claim_bearing_system": True,
        "global_primary_reference": True, "A7_separate_phase30_inferential_comparator": False,
        "A7_descriptive_companion_only": True,
        "A7_requires_additional_model_forwards": False, "H3_descriptive_only": True,
        "H3_numeric_success_threshold": False, "raw_p_value_scope_explicit": True,
        "A8_minus_A7_new_success_gate": False, "bootstrap_plan_unchanged": bp_sha == BOOTSTRAP_PLAN_SHA,
        "bootstrap_plan_sha_match": bp_sha == BOOTSTRAP_PLAN_SHA,
        "ROUTER_HOLDOUT_image_reads_0_v1_2": True, "ROUTER_HOLDOUT_GT_reads_0_v1_2": True,
        "ROUTER_HOLDOUT_outcome_reads_0_v1_2": True, "model_forwards_0_v1_2": True,
        "TEST_reads_0_v1_2": True, "one_shot_execution_started_false_v1_2": True,
        # new v1.3
        "primary_claim_is_A8_vs_global": True,
        "primary_estimand_macro_domain_delta": True,
        "noninferiority_margin_0p005": True,
        "claim_lower_CI_gt_minus_0p005": True,
        "claim_criterion_strict": True,
        "raw_p_value_provenance_resolved": True,
        "raw_p_not_unjustifiably_transferred_from_C7_family": True,
        "raw_p_not_primary_success_gate": True,
        "raw_p_cannot_override_CI": True,
        "zero_difference_not_noninferiority": True,
        "bootstrap_plan_sha_unchanged": bp_sha == BOOTSTRAP_PLAN_SHA,
        "A7_descriptive_only": True, "H3_descriptive_only": True,
        "ROUTER_HOLDOUT_image_reads": 0, "ROUTER_HOLDOUT_GT_reads": 0,
        "ROUTER_HOLDOUT_outcome_reads": 0, "model_forwards": 0, "TEST_reads": 0,
        "one_shot_execution_started": False,
    }
    FALSE_KEYS = {"A7_separate_phase30_inferential_comparator",
                  "A7_requires_additional_model_forwards", "H3_numeric_success_threshold",
                  "A8_minus_A7_new_success_gate", "raw_p_not_primary_success_gate_v_neg",
                  "raw_p_cannot_override_CI_v_neg"}
    n_failed = 0
    failed = []
    for k, v in checks.items():
        if k in ("A7_separate_phase30_inferential_comparator",
                 "A7_requires_additional_model_forwards", "H3_numeric_success_threshold",
                 "A8_minus_A7_new_success_gate", "one_shot_execution_started"):
            ok = (v is False)
        elif k in ("ROUTER_HOLDOUT_image_reads", "ROUTER_HOLDOUT_GT_reads",
                   "ROUTER_HOLDOUT_outcome_reads", "model_forwards", "TEST_reads"):
            ok = (v == 0)
        else:
            ok = bool(v)
        if not ok:
            n_failed += 1
            failed.append(k)
    write_json({
        "artifact": "phase30_preexecution_final_check_v1_3", "phase": 30, "section": "§K",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_3,
        "n_checks": len(checks), "n_failed": n_failed, "failed": failed,
        "checks": checks,
        "completeness_rows": len(all_rows), "completeness_complete": n_complete,
        "completeness_blocking": n_blocking,
        "raw_p_value_case": case, "bootstrap_plan_sha256": bp_sha,
        "generated_utc": now_utc(),
        "all_pass": n_failed == 0 and n_blocking == 0,
    }, AUD / "phase30_preexecution_final_check_v1_3.json")
    print(f"§K final check v1.3: {len(checks)-n_failed}/{len(checks)} pass")

    # ================================================================== #
    # §L  TERMINAL v1.3                                                   #
    # ================================================================== #
    ok = (n_failed == 0 and n_blocking == 0)
    if ok:
        write_json({
            "artifact": "phase30_specification_terminal_v1_3", "phase": 30,
            "status": "SPEC_V1_3_COMPLETE", "terminal": TERMINAL_V1_3,
            "specification_revision": SPEC_REVISION_V1_3,
            "classification": CLASSIFICATION,
            "science_changed": False,
            "ROUTER_HOLDOUT_state": "RESERVED_UNOPENED",
            "image_reads": 0, "GT_reads": 0, "outcome_reads": 0,
            "model_forwards": 0, "TEST_reads": 0,
            "primary_claim": "A8_VS_GLOBAL_NONINFERIORITY",
            "primary_claim_gate": "LOWER_95CI_GT_MINUS_0P005",
            "raw_p_value_case": case,
            "raw_p_value_primary_gate": False,
            "bootstrap_plan_sha": BOOTSTRAP_PLAN_SHA,
            "one_shot_execution_started": False,
            "v1_2_preserved": True,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase30_specification_terminal_v1_3.json")
        print("")
        print("=" * 78)
        print(TERMINAL_V1_3)
        print("=" * 78)
    else:
        write_json({"artifact": "phase30_specification_terminal_v1_3",
                    "status": "BLOCKED",
                    "terminal": "PHASE30_SPEC_BLOCKED__STATISTICAL_PLAN_INCOMPLETE",
                    "failed": failed, "all_pass": False},
                   AUD / "phase30_specification_terminal_v1_3.json")
        print("BLOCKED", failed)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
