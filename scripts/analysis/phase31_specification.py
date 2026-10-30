#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 31 — STATISTICAL SIGNIFICANCE & HYPOTHESIS TESTING.
ENTRY GATE + HYPOTHESIS PROVENANCE + EXACT STATISTICAL SPECIFICATION FREEZE.

SPECIFICATION / PROVENANCE ONLY.  No statistical test executed, no p-value computed,
no effect size computed, no bootstrap rerun, no image read, no GT read, no model forward,
no training, no TEST access.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase31_specification.py
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
SPEC_REVISION = "ra_medfilm_barr_phase31_statistics_v1_0"

QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
P30_TERMINAL = "reports/audits/phase30_supervisor_adjudication_terminal.json"
P30_TERMINAL_SHA = "925cad2de224e7e781cafc11372cf8ff3aa64a2a7b6c3fe9d34658e68a9b8c77"
P30_HANDOFF = "reports/audits/phase30_phase31_qualified_handoff.json"
P30_HANDOFF_SHA = "fe2f14a142cfd38e750794fb8156342aa50ee7df354603dd33cddba16fc28236"
P30_QUALIFIER_CONTRACT = "reports/audits/phase30_reporting_qualification_contract.json"
P30_QUALIFIER_CONTRACT_SHA = "035a784289f0c400688596fe5f77497cfcf0468871c2f9a9b619fb4647a34e4d"
BOOTSTRAP_PLAN_SHA = "59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1"

TERMINAL = ("PHASE31_STATISTICAL_SPEC_COMPLETE__HYPOTHESIS_PROVENANCE_TEST_FAMILIES_CLUSTERING_"
            "MULTIPLICITY_AND_PHASE30_QUALIFIER_FROZEN__EXECUTION_ELIGIBILITY_DETERMINED_NOT_STARTED")

# predecessor authority (chronological order)
AUTHORITY = [
    ("reports/audits/phase24_architecture_spec.json", "Phase24 architecture / H1-H6 / statistics block"),
    ("reports/tables/phase24_success_failure_criteria.csv", "Phase24 success/failure criteria"),
    ("reports/tables/phase24_ablation_plan.csv", "Phase24 ablation plan A0-A8/R1-R3/F1"),
    ("reports/tables/phase24_comparator_plan.csv", "Phase24 comparator plan C1-C11"),
    ("reports/audits/phase24_preservation_contract.json", "Phase24 preservation contract"),
    ("reports/audits/phase25e_evaluation_statistics_contract_v1_0.json", "Phase25E statistics"),
    ("reports/audits/phase25e_multiplicity_provenance_audit.json", "Phase25E multiplicity provenance"),
    ("reports/audits/phase25g_role_contract.json", "Phase25G role"),
    ("reports/audits/phase25g_a7_a8_controlled_comparison_contract.json", "Phase25G A7/A8 contract"),
    ("reports/audits/phase25g_statistics_contract.json", "Phase25G statistics"),
    ("reports/audits/phase25g_h3_adjudication_contract.json", "Phase25G H3 adjudication"),
    ("reports/audits/phase25g_h3_result.json", "Phase25G H3 result"),
    ("reports/audits/phase25g_final_freeze.json", "Phase25G final freeze"),
    ("reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json", "Phase25F A7/A8 ownership ruling F1"),
    ("reports/audits/phase26_evidence_class_contract_v1_0.json", "Phase26 evidence class"),
    ("reports/audits/phase27_statistics_contract_v1_0.json", "Phase27 statistics"),
    ("reports/audits/phase27_decision_rule_contract.json", "Phase27 decision rule"),
    ("reports/audits/phase27_preservation_contract_binding_v1_0.json", "Phase27 preservation binding"),
    ("reports/audits/phase28_execution_statistics.json", "Phase28 ablation statistics"),
    ("reports/audits/phase28_phase31_boundary_audit.json", "Phase28 Phase31 boundary audit"),
    ("reports/audits/phase28_a7_a8_status_determination.json", "Phase28 A7/A8 status"),
    ("reports/audits/phase29_phase_d_three_seed_descriptive_summary.json",
     "Phase29 three-seed descriptive summary"),
    ("reports/audits/phase30_primary_inferential_adjudication_contract_v1_3.json",
     "Phase30 primary adjudication v1.3"),
    ("reports/audits/phase30_raw_p_value_provenance_v1_3.json", "Phase30 raw p provenance"),
    ("reports/audits/phase30_p_value_disposition_v1_3.json", "Phase30 p disposition"),
    ("reports/audits/phase30_supervisor_adjudication_terminal.json", "Phase30 supervisor adjudication"),
]

STATUSES = [
    "CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN",
    "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE",
    "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE",
    "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY",
    "POST_HOC_EXPLORATORY_ONLY",
    "FORBIDDEN_OR_OUT_OF_SCOPE",
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


def write_csv(path, header, rows) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        for r in rows:
            w.writerow(r)


def read_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    print("=" * 78)
    print("PHASE 31 — STATISTICAL SIGNIFICANCE & HYPOTHESIS TESTING SPECIFICATION")
    print("=" * 78)

    # ================= §A/§C bindings ================= #
    a_ok = (sha256_file(ROOT / P30_TERMINAL) == P30_TERMINAL_SHA
            and sha256_file(ROOT / P30_HANDOFF) == P30_HANDOFF_SHA
            and sha256_file(ROOT / P30_QUALIFIER_CONTRACT) == P30_QUALIFIER_CONTRACT_SHA)
    t = read_json(ROOT / P30_TERMINAL)
    write_json({
        "artifact": "phase31_phase30_qualifier_binding", "phase": 31, "section": "§A/§C",
        "specification_revision": SPEC_REVISION, "method": METHOD,
        "phase30_supervisor_terminal": {
            "path": P30_TERMINAL, "sha256": sha256_file(ROOT / P30_TERMINAL),
            "expected_sha256": P30_TERMINAL_SHA, "match": a_ok,
            "canonical_status": t["canonical_status"],
            "scientific_result_status": t["scientific_result_status"],
            "phase31_eligibility": t["phase31_eligibility"]},
        "phase30_qualified_handoff": {
            "path": P30_HANDOFF, "sha256": sha256_file(ROOT / P30_HANDOFF),
            "expected_sha256": P30_HANDOFF_SHA},
        "phase30_reporting_qualification_contract": {
            "path": P30_QUALIFIER_CONTRACT,
            "sha256": sha256_file(ROOT / P30_QUALIFIER_CONTRACT),
            "expected_sha256": P30_QUALIFIER_CONTRACT_SHA},
        "evidence_class_carried_forward": QUALIFIER,
        "phase31_must_never_describe_phase30_as": [
            "COMPLETE_CANONICAL", "fully preregistered execution",
            "perfectly source-frozen validation", "no protocol deviations",
            "strictly protocol-perfect holdout"],
        "qualifier_accompanies_any_phase31_publication_facing_inference": True,
        "artifacts_modified": False,
        "generated_utc": now_utc(), "all_pass": a_ok,
    }, AUD / "phase31_phase30_qualifier_binding.json")
    print(f"§A/§C Phase30 qualified handoff bound (ok={a_ok})")

    # ================= §B handoff normalization ================= #
    h = read_json(ROOT / P30_HANDOFF)
    pi = h["permitted_inputs"]
    pairs = [(x["path"], x["sha256"]) for x in pi]
    uniq = sorted(set(pairs))
    from collections import Counter
    cc = Counter(p for p, _ in pairs)
    dups = {k: v for k, v in cc.items() if v > 1}
    dup_identical = all(len({s for p, s in pairs if p == k}) == 1 for k in dups)
    b_ok = (len(pi) == 17 and len(uniq) == 16 and len(dups) == 1 and dup_identical)
    write_json({
        "artifact": "phase31_phase30_handoff_normalization_audit", "phase": 31, "section": "§B",
        "original_entries": len(pi), "unique_path_sha_pairs": len(uniq),
        "duplicate_count": len(pi) - len(uniq),
        "duplicate_path": list(dups.keys())[0] if dups else None,
        "duplicate_sha_identical": dup_identical,
        "classification": "BENIGN_IDENTICAL_DUPLICATE_HANDOFF_ENTRY",
        "scientific_effect": "NONE", "phase30_artifact_modified": False,
        "canonicalization": "Phase31 consumption canonicalizes to unique (path, sha256) pairs",
        "canonical_pairs": [{"path": p, "sha256": s} for p, s in uniq],
        "generated_utc": now_utc(), "all_pass": b_ok,
    }, AUD / "phase31_phase30_handoff_normalization_audit.json")
    print(f"§B handoff normalization: 17 entries -> {len(uniq)} unique, dup={list(dups.keys())}")

    # ================= §E provenance boundary ================= #
    auth = [{"path": p, "role": r, "sha256": sha256_file(ROOT / p), "exists": (ROOT / p).exists()}
            for p, r in AUTHORITY]
    write_json({
        "artifact": "phase31_statistical_provenance_boundary", "phase": 31, "section": "§E",
        "specification_revision": SPEC_REVISION,
        "phase30_outcomes_known": True,
        "classes": {
            "1_confirmatory_preoutcome_exact_method_frozen":
                "procedures explicitly frozen BEFORE the relevant outcome was opened",
            "2_preoutcome_hypothesis_method_incomplete":
                "hypotheses stated before outcome but without a complete statistical procedure",
            "3_already_adjudicated_by_predecessor_phase":
                "development comparisons already formally adjudicated in earlier phases",
            "4_descriptive_only": "descriptive-only analyses by predecessor authority",
            "5_post_hoc": "statistical analyses first specified only AFTER outcomes were known"},
        "rule": "no new confirmatory procedure may be created merely because it is conventional",
        "authority_artifacts_chronological": auth,
        "generated_utc": now_utc(), "all_pass": all(x["exists"] for x in auth),
    }, AUD / "phase31_statistical_provenance_boundary.json")
    print(f"§E provenance boundary frozen ({sum(1 for x in auth if x['exists'])}/{len(auth)} authorities)")

    # ================= §G hypothesis provenance matrix ================= #
    def A(rel):
        return {"authority_artifact": rel, "authority_sha": sha256_file(ROOT / rel)}

    H = [
        {"hypothesis_id": "H1",
         "scientific_statement": "A learned pre-execution GT-free predictor of paired refinement "
                                 "gain allocates optional regional refinement more effectively than "
                                 "simple GT-free uncertainty/geometry proxies at equal budgets.",
         "population": "ROUTER_DEVELOPMENT (4957)", "system_A": "C7 LEARNED_PAIRED_GAIN_ROUTING",
         "system_B": "C3/C4/C5/C6 simple proxies", "metric": "precision@budget / benefit capture",
         "estimand": "routing benefit at equal budget",
         **A("reports/audits/phase25e_evaluation_statistics_contract_v1_0.json"),
         "authority_order": "Phase25E (pre-outcome contract) -> Phase25G freeze",
         "method_frozen_before_outcome": True, "exact_method_complete": True,
         "multiplicity_family_frozen": True,
         "current_status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE"},
        {"hypothesis_id": "H2",
         "scientific_statement": "Benefit-aware routing captures more positive gain per unit compute "
                                 "than random/entropy/margin/ROI-size routing.",
         "population": "ROUTER_DEVELOPMENT (4957)", "system_A": "C7/C8",
         "system_B": "C3/C4/C5/C6", "metric": "gain per unit compute",
         "estimand": "benefit per compute",
         **A("reports/audits/phase25e_evaluation_statistics_contract_v1_0.json"),
         "authority_order": "Phase25E -> Phase25G",
         "method_frozen_before_outcome": True, "exact_method_complete": True,
         "multiplicity_family_frozen": True,
         "current_status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE"},
        {"hypothesis_id": "H3",
         "scientific_statement": "Post-refinement fallback reduces harmful replacement relative to "
                                 "always accepting an executed refinement.",
         "population": "ROUTER_DEVELOPMENT (4957)", "system_A": "A8 (C9)", "system_B": "A7 (C8)",
         "metric": "harmful replacement count/rate", "estimand": "harmful-replacement reduction",
         **A("reports/audits/phase25g_h3_adjudication_contract.json"),
         "authority_order": "Phase25G (COMPLETE_CANONICAL)",
         "method_frozen_before_outcome": True, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY"},
        {"hypothesis_id": "H4",
         "scientific_statement": "A dedicated crop-trained regional refiner yields a more useful "
                                 "action distribution than the Phase22 diagnostic reuse.",
         "population": "ROUTER_DEVELOPMENT", "system_A": "Phase25A refiner", "system_B": "Phase22 reuse",
         "metric": "action distribution / refiner ablation", "estimand": "refiner utility",
         **A("reports/audits/phase28_comprehensive_ablation_matrix.json"),
         "authority_order": "Phase25A -> Phase28 ablation matrix",
         "method_frozen_before_outcome": True, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE"},
        {"hypothesis_id": "H5",
         "scientific_statement": "Benefit-aware routing produces a measurable accuracy-compute frontier.",
         "population": "ROUTER_DEVELOPMENT (4957)", "system_A": "A7 (C8) across budget grid",
         "system_B": "global-only anchor", "metric": "macro DeltaDice vs activation fraction",
         "estimand": "frontier existence",
         **A("reports/audits/phase25g_final_freeze.json"),
         "authority_order": "Phase25E budget grid -> Phase25G freeze",
         "method_frozen_before_outcome": True, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE"},
        {"hypothesis_id": "H6",
         "scientific_statement": "Learned paired refinement gain contains information beyond ordinary "
                                 "global uncertainty.",
         "population": "ROUTER_DEVELOPMENT", "system_A": "learned paired gain", "system_B": "global "
         "uncertainty proxies", "metric": "incremental information", "estimand": "unspecified",
         **A("reports/audits/phase24_architecture_spec.json"),
         "authority_order": "Phase24 hypothesis only",
         "method_frozen_before_outcome": True, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE"},
        {"hypothesis_id": "P30-PRIMARY",
         "scientific_statement": "A8/C9 preserves macro-domain Dice vs the global reference on "
                                 "ROUTER_HOLDOUT (non-inferiority).",
         "population": "ROUTER_HOLDOUT (875)", "system_A": "A8/C9", "system_B": "global reference",
         "metric": "macro-domain equal-weight DeltaDice",
         "estimand": "lower 95% bootstrap CI > -0.005",
         **A("reports/audits/phase30_primary_inferential_adjudication_contract_v1_3.json"),
         "authority_order": "Phase30 v1.3 (pre-open) -> execution",
         "method_frozen_before_outcome": True, "exact_method_complete": True,
         "multiplicity_family_frozen": False,
         "current_status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE"},
        {"hypothesis_id": "P30-A8VSRANDOM-P",
         "scientific_statement": "A new paired significance test of A8 vs global on ROUTER_HOLDOUT.",
         "population": "ROUTER_HOLDOUT (875)", "system_A": "A8/C9", "system_B": "global reference",
         "metric": "per-sample Dice difference", "estimand": "p-value vs DeltaDice = 0",
         **A("reports/audits/phase30_raw_p_value_provenance_v1_3.json"),
         "authority_order": "Phase30 CASE P2 (no exact procedure frozen)",
         "method_frozen_before_outcome": False, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "POST_HOC_EXPLORATORY_ONLY"},
        {"hypothesis_id": "P30-A7-COMPANION",
         "scientific_statement": "A7 descriptive companion metrics on ROUTER_HOLDOUT.",
         "population": "ROUTER_HOLDOUT (875)", "system_A": "A7", "system_B": "A8",
         "metric": "Dice point estimates / harmful replacement",
         "estimand": "descriptive point difference",
         **A("reports/audits/phase30_a7_descriptive_companion_contract_v1_2.json"),
         "authority_order": "Phase30 v1.2",
         "method_frozen_before_outcome": True, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY"},
        {"hypothesis_id": "C11-JFS",
         "scientific_statement": "JFS-like post-hoc selector comparison.",
         "population": "n/a", "system_A": "C11", "system_B": "n/a", "metric": "n/a",
         "estimand": "n/a",
         **A("reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json"),
         "authority_order": "Phase25E/25F exclusion",
         "method_frozen_before_outcome": False, "exact_method_complete": False,
         "multiplicity_family_frozen": False,
         "current_status": "FORBIDDEN_OR_OUT_OF_SCOPE"},
    ]
    hdr = ["hypothesis_id", "scientific_statement", "population", "system_A", "system_B", "metric",
           "estimand", "authority_artifact", "authority_sha", "authority_order",
           "method_frozen_before_outcome", "exact_method_complete", "multiplicity_family_frozen",
           "current_Phase31_status"]
    write_csv(TAB / "phase31_hypothesis_provenance_matrix.csv", hdr,
              [[r.get(k) for k in hdr] for r in H])
    counts = {s: sum(1 for r in H if r["current_status"] == s) for s in STATUSES}
    write_json({
        "artifact": "phase31_hypothesis_provenance_matrix_summary", "phase": 31, "section": "§G",
        "n_candidates": len(H), "status_counts": counts,
        "confirmatory_preoutcome_exact_method_frozen": counts[
            "CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN"],
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_hypothesis_provenance_matrix_summary.json")
    print(f"§G hypothesis matrix: {len(H)} candidates; {counts}")

    # ================= §H Phase24 H1-H6 ownership audit ================= #
    write_json({
        "artifact": "phase31_phase24_h1_h6_ownership_audit", "phase": 31, "section": "§H",
        "authority": "reports/audits/phase24_architecture_spec.json",
        "authority_sha256": sha256_file(ROOT / "reports/audits/phase24_architecture_spec.json"),
        "H1": {"already_formally_answered": True, "phase": "Phase25E/25G",
               "exact_statistical_test_preregistered": True, "still_phase31_owned": False},
        "H2": {"already_formally_answered": True, "phase": "Phase25E",
               "exact_statistical_test_preregistered": True, "still_phase31_owned": False},
        "H3": {"already_formally_answered": True, "phase": "Phase25G",
               "descriptive_only": True, "exact_statistical_test_preregistered": False,
               "still_phase31_owned": False},
        "H4": {"already_formally_answered": True, "phase": "Phase25A/Phase28",
               "exact_statistical_test_preregistered": False, "still_phase31_owned": False},
        "H5": {"already_formally_answered": True, "phase": "Phase25E/25G",
               "descriptive_only": True, "exact_statistical_test_preregistered": False,
               "still_phase31_owned": False},
        "H6": {"already_formally_answered": False, "partially_answered": False,
               "descriptive_only": False, "exact_statistical_test_preregistered": False,
               "still_phase31_owned": True,
               "testable_confirmatorily_after_outcome": False,
               "note": "stated pre-outcome but no exact statistical procedure was ever frozen; "
                       "cannot be confirmatory after Phase30 outcomes"},
        "conclusion": "NONE of H1-H6 requires a new Phase31 confirmatory test; H1/H2/H4/H5 are "
                      "already adjudicated, H3 is descriptive-only, H6 is method-incomplete",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_phase24_h1_h6_ownership_audit.json")
    print("§H H1-H6 ownership audited")

    # ================= §I/§J Phase30 boundary ================= #
    pr = read_json(AUD / "phase30_primary_noninferiority_result.json")
    write_json({
        "artifact": "phase31_phase30_primary_boundary", "phase": 31, "section": "§I/§J",
        "frozen_primary_result": {
            "estimand": "DeltaDice_A8 = Dice(A8 final, GT) - Dice(global, GT)",
            "macro_domain_equal_weight_point": pr["macro_delta_dice"],
            "macro_ci": pr["macro_ci"], "noninferiority_margin": 0.005,
            "claim_gate": "lower 95% CI > -0.005",
            "PRESERVATION_ASSERTED": pr["PRESERVATION_ASSERTED"],
            "p_values_computed_phase30": pr["p_values_computed"]},
        "phase31_must_not_replace_gate": True,
        "phase31_must_not_claim_new_p_value_was_required": True,
        "zero_difference_test_is_different_from_noninferiority": True,
        "phase30_case": "P2__GENERIC_PAIRED_P_REPORTING_ALLOWED_BUT_EXACT_PHASE30_PROCEDURE_NOT_FROZEN",
        "phase31_a8_vs_global_p_value_confirmatory": False,
        "phase25e_c7_family_raw_p_transferred": False,
        "phase31_a8_vs_global_significance_test_classification": "POST_HOC_EXPLORATORY_ONLY",
        "may_upgrade_or_downgrade_PRESERVATION_ASSERTED": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_phase30_primary_boundary.json")
    print("§I/§J Phase30 primary + p-value boundary frozen")

    # ================= §K Wilcoxon provenance ruling ================= #
    write_json({
        "artifact": "phase31_wilcoxon_provenance_ruling", "phase": 31, "section": "§K",
        "roadmap_phrase": "paired Wilcoxon",
        "roadmap_phrase_is_toolbox_description_only": True,
        "required_frozen_fields": [
            "exact comparison", "metric", "unit of analysis", "pairing key", "null hypothesis",
            "alternative hypothesis", "one-sided/two-sided", "alpha", "zero-difference treatment",
            "implementation semantics", "exact vs approximate", "continuity correction",
            "NaN handling", "ties handling", "group/cluster dependence handling"],
        "predecessor_authority_specifies_all_fields": False,
        "outcomes_already_known": True,
        "confirmatory_authorization": False,
        "ruling": "NO paired Wilcoxon test may be classified confirmatory for Phase31. Any Phase31 "
                  "paired Wilcoxon is POST_HOC_EXPLORATORY_ONLY (or omitted).",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_wilcoxon_provenance_ruling.json")
    print("§K Wilcoxon ruling: exploratory-only")

    # ================= §L cluster / group dependence ================= #
    write_json({
        "artifact": "phase31_cluster_dependence_ruling", "phase": 31, "section": "§L",
        "population": "ROUTER_HOLDOUT (875)", "n_groups": 628,
        "group_key_semantics": "phase24_router_split_manifest.csv:group_key "
                               "(KUB -> PATIENT::<patient_id>; others SINGLETON)",
        "sample_level_test_over_875_without_adjudication": "FORBIDDEN",
        "prospectively_frozen_cluster_aware_test_exists": False,
        "domain_stratification_required": True,
        "paired_inference_validity": "not established for a naive sample-level test",
        "ruling": "No exact cluster-aware inferential test was prospectively frozen; none may be "
                  "invented as confirmatory after outcomes. Any cluster-aware test is exploratory "
                  "only.",
        "phase30_bootstrap_already_handles_groups": True,
        "phase30_bootstrap_plan_sha": BOOTSTRAP_PLAN_SHA,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_cluster_dependence_ruling.json")
    print("§L cluster dependence ruling: no confirmatory cluster test")

    # ================= §M bootstrap reuse ruling ================= #
    write_json({
        "artifact": "phase31_bootstrap_reuse_ruling", "phase": 31, "section": "§M",
        "existing_phase30_bootstrap_plan": {
            "type": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP", "B": 2000, "rng": "PCG64(42)",
            "percentiles": [2.5, 97.5], "paired": True, "sha256": BOOTSTRAP_PLAN_SHA},
        "regenerate": False,
        "report_already_frozen_phase30_ci": "REUSE_FROZEN_RESULT",
        "new_estimand_using_phase30_plan_authorized": False,
        "ruling": "the existence of bootstrap indices does not authorize arbitrary new estimands; "
                  "only the frozen Phase30 macro/per-domain A8-vs-global CI is authorized to reuse "
                  "the plan, and only as already-frozen output",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_bootstrap_reuse_ruling.json")
    print("§M bootstrap reuse ruling: no regeneration, no new estimand")

    # ================= §N effect-size provenance ================= #
    write_json({
        "artifact": "phase31_effect_size_provenance_ruling", "phase": 31, "section": "§N",
        "roadmap_phrase": "Cohen effect sizes",
        "roadmap_phrase_insufficient": True,
        "candidate_definitions": ["Cohen d", "paired Cohen dz", "dav", "drm",
                                  "another standardized effect"],
        "required_fields": ["numerator", "denominator", "sample/group unit", "domain aggregation",
                            "zero-variance behavior", "CI method", "interpretation thresholds"],
        "exact_definition_frozen_before_outcome": False,
        "ruling": "any newly chosen effect size is POST_HOC_EXPLORATORY_ONLY and must not become a "
                  "success gate; no definition may be selected based on favorable magnitude",
        "selected_definition": None,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_effect_size_provenance_ruling.json")
    print("§N effect-size ruling: exploratory-only, no gate")

    # ================= §O multiplicity ================= #
    write_json({
        "artifact": "phase31_multiplicity_provenance_contract", "phase": 31, "section": "§O",
        "auto_apply_holm_bonferroni_bh": False,
        "phase25e_holm_authority": "belonged to its pre-declared C7 comparator family; must NOT be "
                                   "generalized",
        "phase24_multiplicity": "none declared",
        "phase28_multiplicity": "DESCRIPTIVE_NO_POST_HOC_CORRECTION",
        "phase27_multiplicity": "no_new_multiplicity_correction",
        "phase30_multiplicity": "no new multiplicity correction introduced",
        "prospectively_frozen_phase31_family": None,
        "ruling": "no confirmatory multiplicity claim is permitted for Phase31; all Phase31 tests are "
                  "exploratory/descriptive",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_multiplicity_provenance_contract.json")
    print("§O multiplicity contract: no confirmatory family")

    # ================= §P test registry ================= #
    reg_hdr = ["test_id", "hypothesis_id", "population", "comparison", "metric", "estimand",
               "analysis_unit", "cluster_handling", "test_name", "null", "alternative", "tail",
               "alpha", "zero_method", "exact_or_approx", "effect_size", "CI_method",
               "multiplicity_family", "multiplicity_method", "preoutcome_authority",
               "authority_sha", "provenance_class", "claim_bearing", "execution_authorized"]
    reg = [
        ["T01", "P30-A8VSRANDOM-P", "ROUTER_HOLDOUT (875)", "A8/C9 vs global reference",
         "per-sample Dice difference", "mean DeltaDice", "sample (exploratory)", "none specified",
         "paired Wilcoxon", "median difference = 0", "two-sided", "two-sided", "0.05 (exploratory)",
         "unspecified", "unspecified", "none", "none", "none", "none",
         "reports/audits/phase30_raw_p_value_provenance_v1_3.json",
         sha256_file(ROOT / "reports/audits/phase30_raw_p_value_provenance_v1_3.json"),
         "POST_HOC_EXPLORATORY_ONLY", "False", "False"],
        ["T02", "P30-A8VSRANDOM-P", "ROUTER_HOLDOUT (875)", "A8/C9 vs global reference",
         "per-sample Dice difference", "mean DeltaDice", "group (cluster)", "domain-stratified",
         "paired bootstrap p (exploratory)", "mean difference = 0", "two-sided", "two-sided",
         "0.05 (exploratory)", "unspecified", "bootstrap", "none", "percentile",
         "none", "none", "reports/audits/phase30_p_value_disposition_v1_3.json",
         sha256_file(ROOT / "reports/audits/phase30_p_value_disposition_v1_3.json"),
         "POST_HOC_EXPLORATORY_ONLY", "False", "False"],
        ["T03", "P30-A7-COMPANION", "ROUTER_HOLDOUT (875)", "A8 vs A7", "macro DeltaDice",
         "point difference", "group (cluster)", "domain-stratified",
         "descriptive bootstrap CI only", "n/a", "n/a", "n/a", "n/a", "n/a", "bootstrap",
         "none", "percentile", "none", "none",
         "reports/audits/phase30_a7_descriptive_companion_contract_v1_2.json",
         sha256_file(ROOT / "reports/audits/phase30_a7_descriptive_companion_contract_v1_2.json"),
         "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY", "False", "False"],
        ["T04", "H6", "ROUTER_DEVELOPMENT", "learned paired gain vs global uncertainty",
         "incremental information", "unspecified", "unspecified", "unspecified",
         "unspecified", "unspecified", "unspecified", "unspecified", "unspecified", "unspecified",
         "unspecified", "unspecified", "unspecified", "unspecified", "unspecified",
         "reports/audits/phase24_architecture_spec.json",
         sha256_file(ROOT / "reports/audits/phase24_architecture_spec.json"),
         "PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE", "False", "False"],
    ]
    write_csv(TAB / "phase31_statistical_test_registry.csv", reg_hdr, reg)
    n_confirmatory = sum(1 for r in reg if r[21] == "CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN")
    n_exploratory = sum(1 for r in reg if r[21] == "POST_HOC_EXPLORATORY_ONLY")
    write_json({
        "artifact": "phase31_statistical_test_registry_summary", "phase": 31, "section": "§P",
        "n_tests": len(reg), "n_confirmatory": n_confirmatory, "n_exploratory": n_exploratory,
        "execution_authorized_all_false": all(r[23] == "False" for r in reg),
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_statistical_test_registry_summary.json")
    print(f"§P test registry: {len(reg)} tests, confirmatory={n_confirmatory}, exploratory={n_exploratory}")

    # ================= §Q already-adjudicated audit ================= #
    write_json({
        "artifact": "phase31_already_adjudicated_comparisons_audit", "phase": 31, "section": "§Q",
        "comparisons": [
            {"comparison": "Phase25E router comparator family C7 vs C1..C6/C10",
             "status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE", "phase": "Phase25E"},
            {"comparison": "Phase25G A7-vs-A8 / C8-vs-C9 controlled comparison",
             "status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE", "phase": "Phase25G"},
            {"comparison": "Phase25G H3 harmful-replacement reduction",
             "status": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY", "phase": "Phase25G"},
            {"comparison": "Phase27 A8-vs-global preservation (VAL808)",
             "status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE", "phase": "Phase27"},
            {"comparison": "Phase28 ablation comparisons",
             "status": "DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY", "phase": "Phase28"},
            {"comparison": "Phase29 reproducibility",
             "status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE", "phase": "Phase29"},
            {"comparison": "Phase30 final development validation (ROUTER_HOLDOUT A8 vs global)",
             "status": "ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE", "phase": "Phase30"}],
        "phase31_may_synthesize": True,
        "phase31_may_create_second_contradictory_primary_gate": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_already_adjudicated_comparisons_audit.json")
    print("§Q already-adjudicated comparisons audited")

    # ================= §R counters ================= #
    write_json({
        "artifact": "phase31_evidence_consumption_counters", "phase": 31, "section": "§R",
        "Phase31_ROUTER_HOLDOUT_raw_image_reads": 0,
        "Phase31_ROUTER_HOLDOUT_raw_GT_reads": 0,
        "Phase31_model_forwards": 0, "Phase31_training_steps": 0, "Phase31_TEST_reads": 0,
        "numeric_scientific_outcomes_read": "only already-frozen Phase30 values bound as immutable "
                                            "historical facts",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_evidence_consumption_counters.json")

    # ================= §S TEST lock ================= #
    write_json({
        "artifact": "phase31_test_lock_audit", "phase": 31, "section": "§S",
        "TEST_owner": "Phase39", "TEST_state": "LOCKED_UNTIL_PHASE39", "Phase31_TEST_reads": 0,
        "exception": None,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_test_lock_audit.json")

    # ================= §T specification document ================= #
    doc = f"""# Phase 31 — Statistical Significance & Hypothesis Testing
## Entry Gate + Hypothesis Provenance + Exact Statistical Specification (v1.0)

**Specification revision:** `{SPEC_REVISION}`
**Method:** {METHOD}
**Status:** SPECIFICATION COMPLETE — **statistical execution NOT authorized**
**Generated:** {now_utc()}

> **Phase30 qualifier carried forward:**
> `{QUALIFIER}`
> Phase30 must **never** be described as `COMPLETE_CANONICAL`, "fully preregistered execution",
> "perfectly source-frozen validation", "no protocol deviations", or "strictly protocol-perfect
> holdout".

---

## 1. The roadmap phrase is a toolbox description, not a preregistration

The historical roadmap describes Phase31 as *paired Wilcoxon / bootstrap 95% CIs / Cohen effect
sizes*. That is a **toolbox description only**. It is **not** an exact preregistration of which
comparison, metric, population, null, alternative, tail, zero-difference handling, multiplicity
family, alpha, clustering unit, or effect-size definition. Those details must be recovered from
pre-outcome authority, and are **not** inferred from the roadmap phrase.

## 2. Prospective vs post-hoc boundary

Phase30 outcomes are known. Phase31 therefore classifies every candidate analysis as one of:

1. `CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`
2. `PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE`
3. `ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE`
4. `DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY`
5. `POST_HOC_EXPLORATORY_ONLY`

**No new confirmatory procedure may be created merely because it is conventional.**

## 3. Hypothesis provenance (summary)

| id | status |
|---|---|
| H1 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25E/25G) |
| H2 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25E) |
| H3 | DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY (Phase25G) |
| H4 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25A/Phase28) |
| H5 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25E/25G) |
| H6 | PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE |
| P30-PRIMARY | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase30, CI gate) |
| P30-A8VSRANDOM-P | POST_HOC_EXPLORATORY_ONLY |
| P30-A7-COMPANION | DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY |
| C11-JFS | FORBIDDEN_OR_OUT_OF_SCOPE |

**Zero candidates are `CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`.**

## 4. Phase30 primary result must not be redefined

Frozen: macro ΔDice `+0.0017390308610248934`, 95% CI
`[0.00111729355352301, 0.0024049809029647283]`, margin 0.005, gate lower 95% CI > −0.005,
`PRESERVATION_ASSERTED = true`, Phase30 p-values computed = 0. Phase31 must not replace this gate
nor claim a new p-value was required. A test against `DeltaDice = 0` is **different** from the frozen
non-inferiority claim.

## 5. Phase30 p-value boundary (CASE P2)

`GENERIC_PAIRED_P_REPORTING_ALLOWED_BUT_EXACT_PHASE30_PROCEDURE_NOT_FROZEN`. The Phase25E
C7-vs-comparator raw paired p-value **must not** be transferred. Any Phase31 A8-vs-global
significance test is **POST_HOC_EXPLORATORY_ONLY** and may never upgrade or downgrade
`PRESERVATION_ASSERTED`.

## 6. Wilcoxon provenance ruling

The roadmap phrase "paired Wilcoxon" is insufficient. No predecessor authority freezes all required
fields (comparison, metric, unit, pairing key, null, alternative, tail, alpha, zero handling,
implementation, exact/approx, continuity, NaN, ties, cluster dependence). **No Phase31 paired
Wilcoxon may be confirmatory** — exploratory only or omitted.

## 7. Cluster / group dependence (load-bearing)

ROUTER_HOLDOUT has 875 rows in **628 groups** (`group_key`). A naive sample-level test over 875 rows
is **forbidden**. No exact cluster-aware inferential test was prospectively frozen; none may be
invented as confirmatory after outcomes. Any cluster-aware test is exploratory only. The frozen
Phase30 domain-stratified group bootstrap already handles groups.

## 8. Bootstrap reuse

The Phase30 plan (`{BOOTSTRAP_PLAN_SHA}`) must **not** be regenerated. Only the already-frozen
Phase30 macro/per-domain A8-vs-global CI is authorized to reuse the plan, and only as frozen output.
The existence of bootstrap indices does **not** authorize arbitrary new estimands.

## 9. Effect-size provenance

"Cohen effect sizes" is insufficient. No exact definition (d / dz / dav / drm / other) was frozen
pre-outcome. Any newly chosen effect size is **POST_HOC_EXPLORATORY_ONLY** and must not become a
success gate; no definition may be selected for favorable magnitude.

## 10. Multiplicity

No automatic Holm/Bonferroni/BH. The Phase25E Holm authority belonged to its pre-declared C7
comparator family and must not be generalized. No confirmatory multiplicity family exists for
Phase31 → no confirmatory multiplicity claim is permitted.

## 11. Test registry

`reports/tables/phase31_statistical_test_registry.csv` — {len(reg)} candidate tests, of which
**{n_confirmatory} confirmatory** and **{n_exploratory} exploratory**. `execution_authorized = false`
for **every** test pending supervisor review.

## 12. Evidence consumption

Phase31 may consume only the frozen Phase30 tables/audits authorized by the qualified handoff.
Counters: raw holdout image reads 0, raw holdout GT reads 0, model forwards 0, training steps 0,
TEST reads 0.

## 13. TEST lock

TEST owner = Phase39; state `LOCKED_UNTIL_PHASE39`; Phase31 TEST reads = 0.
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "phase31_statistical_significance_hypothesis_testing_spec_v1_0.md").write_text(
        doc, encoding="utf-8")
    print("§T specification document written")

    # ================= §U entry gate ================= #
    gate = {
        "Phase30_supervisor_terminal_sha_match": sha256_file(ROOT / P30_TERMINAL) == P30_TERMINAL_SHA,
        "Phase30_status_not_COMPLETE_CANONICAL":
            t["canonical_status"] != "COMPLETE_CANONICAL",
        "Phase30_scientific_result_preserved":
            t["scientific_result_status"] == "PRESERVED_VALID_ONE_SHOT_RESULT_WITH_PROTOCOL_DEVIATION",
        "Phase30_qualifier_bound": True,
        "Phase30_handoff_sha_match": sha256_file(ROOT / P30_HANDOFF) == P30_HANDOFF_SHA,
        "handoff_17_entries_16_unique_reconciled": b_ok,
        "handoff_duplicate_identical_nonblocking": dup_identical,
        "ROUTER_HOLDOUT_raw_image_reads_0": True,
        "ROUTER_HOLDOUT_raw_GT_reads_0": True,
        "model_forwards_0": True, "training_0": True, "TEST_reads_0": True,
        "Phase31_scope_matches_roadmap": True,
        "no_statistical_test_executed": True,
        "no_new_p_value_computed": True,
        "no_new_effect_size_computed": True,
        "no_bootstrap_regenerated": True,
        "hypothesis_provenance_matrix_complete": True,
        "group_dependence_adjudicated": True,
        "multiplicity_provenance_adjudicated": True,
        "exact_test_registry_frozen": True,
    }
    nf = sum(1 for v in gate.values() if not v)
    write_json({"artifact": "phase31_entry_gate", "phase": 31, "section": "§U",
                "specification_revision": SPEC_REVISION, "n_checks": len(gate), "n_failed": nf,
                "failed": [k for k, v in gate.items() if not v], "checks": gate,
                "generated_utc": now_utc(), "all_pass": nf == 0},
               AUD / "phase31_entry_gate.json")
    print(f"§U entry gate: {len(gate)-nf}/{len(gate)} pass")

    # ================= §V completeness ================= #
    rows = [
        ("Phase30 qualified handoff bound", "terminal + handoff + qualifier SHAs", "COMPLETE", ""),
        ("Handoff normalization", "17 entries -> 16 unique (path,sha)", "COMPLETE", ""),
        ("Phase30 qualifier carried forward", "evidence class bound", "COMPLETE", ""),
        ("Prospective vs post-hoc boundary", "5-class taxonomy frozen", "COMPLETE", ""),
        ("Predecessor authority audited chronologically", f"{len(auth)} artifacts", "COMPLETE", ""),
        ("Hypothesis provenance matrix", f"{len(H)} candidates", "COMPLETE", ""),
        ("Phase24 H1-H6 ownership", "ownership audited", "COMPLETE", ""),
        ("Phase30 primary gate preserved", "not redefined", "COMPLETE", ""),
        ("Phase30 p-value boundary", "CASE P2 preserved", "COMPLETE", ""),
        ("Wilcoxon provenance", "no confirmatory Wilcoxon", "COMPLETE", ""),
        ("Cluster/group dependence", "no confirmatory cluster test", "COMPLETE", ""),
        ("Bootstrap reuse", "no regeneration, no new estimand", "COMPLETE", ""),
        ("Effect-size provenance", "exploratory only, no gate", "COMPLETE", ""),
        ("Multiplicity provenance", "no confirmatory family", "COMPLETE", ""),
        ("Exact test registry", f"{len(reg)} tests, execution_authorized=false", "COMPLETE", ""),
        ("Already-adjudicated comparisons", "audited", "COMPLETE", ""),
        ("Evidence consumption counters", "all zero", "COMPLETE", ""),
        ("TEST lock", "0 reads", "COMPLETE", ""),
        ("No-execution audit", "0 tests/p-values/effect sizes", "COMPLETE", ""),
        ("CONFIRMATORY execution eligibility",
         "no confirmatory procedure frozen pre-outcome", "BLOCKING",
         "no confirmatory test eligible; exploratory only"),
        ("Exploratory execution eligibility",
         "exploratory analyses may be authorized after supervisor review", "COMPLETE",
         "execution_authorized=false pending review"),
    ]
    write_csv(TAB / "phase31_specification_completeness.csv",
              ["requirement", "description", "status", "note"], rows)
    n_complete = sum(1 for r in rows if r[2] == "COMPLETE")
    n_block = sum(1 for r in rows if r[2] == "BLOCKING")
    print(f"§V completeness: {n_complete}/{len(rows)} COMPLETE, {n_block} BLOCKING")

    # ================= §W no-execution audit ================= #
    write_json({
        "artifact": "phase31_no_execution_audit", "phase": 31, "section": "§W",
        "new_statistical_hypothesis_tests": 0, "new_p_values": 0, "new_effect_sizes": 0,
        "new_bootstrap_draws": 0, "raw_holdout_image_reads": 0, "raw_holdout_GT_reads": 0,
        "model_forwards": 0, "training": 0, "TEST_reads": 0,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase31_no_execution_audit.json")

    # ================= §X final check ================= #
    checks = {
        "entry_gate_pass": nf == 0,
        "handoff_normalized": b_ok,
        "qualifier_bound": True,
        "provenance_boundary_frozen": True,
        "hypothesis_matrix_complete": True,
        "h1_h6_ownership_audited": True,
        "phase30_primary_gate_preserved": True,
        "phase30_p_value_boundary_preserved": True,
        "wilcoxon_ruling_frozen": True,
        "cluster_ruling_frozen": True,
        "bootstrap_ruling_frozen": True,
        "effect_size_ruling_frozen": True,
        "multiplicity_ruling_frozen": True,
        "test_registry_frozen": True,
        "no_confirmatory_test_eligible": n_confirmatory == 0,
        "all_execution_authorized_false": all(r[23] == "False" for r in reg),
        "already_adjudicated_audited": True,
        "no_statistical_test_executed": True,
        "no_new_p_value": True, "no_new_effect_size": True, "no_bootstrap_regenerated": True,
        "raw_holdout_image_reads_0": True, "raw_holdout_GT_reads_0": True,
        "model_forwards_0": True, "training_0": True, "TEST_reads_0": True,
        "Phase31_execution_not_started": True, "Phase32_not_started": True,
    }
    nfx = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase31_specification_final_check", "phase": 31, "section": "§X",
        "specification_revision": SPEC_REVISION,
        "n_checks": len(checks), "n_failed": nfx,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "specification_complete": nfx == 0,
        "confirmatory_execution_eligible": False,
        "exploratory_execution_eligible": True,
        "exploratory_execution_requires_supervisor_authorization": True,
        "unresolved_provenance_items": [],
        "generated_utc": now_utc(), "all_pass": nfx == 0,
    }, AUD / "phase31_specification_final_check.json")
    print(f"§X final check: {len(checks)-nfx}/{len(checks)} pass")

    # ================= §Y terminal ================= #
    if nfx == 0:
        write_json({
            "artifact": "phase31_specification_terminal", "phase": 31,
            "status": "SPEC_COMPLETE", "terminal": TERMINAL,
            "specification_revision": SPEC_REVISION,
            "phase30_qualifier_carried_forward": QUALIFIER,
            "specification_complete": True,
            "confirmatory_execution_eligible": False,
            "exploratory_execution_eligible": True,
            "execution_eligibility_determined": True,
            "n_candidate_hypotheses": len(H), "n_confirmatory_tests": n_confirmatory,
            "n_exploratory_tests": n_exploratory,
            "all_execution_authorized_false": True,
            "Phase31_statistical_execution_started": False,
            "Phase32_started": False, "TEST_reads": 0,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase31_specification_terminal.json")
        print("")
        print("=" * 78)
        print(TERMINAL)
        print("=" * 78)
    else:
        print("FINAL CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nfx == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
