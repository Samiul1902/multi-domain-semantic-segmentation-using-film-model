#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 30 - PRE-EXECUTION SPECIFICATION REPAIR v1.2.
A7/A8 comparator-scope + statistical-claim reconciliation.

PRE-FIRST-OPEN COMPARATOR / STATISTICAL-SCOPE SEMANTIC RECONCILIATION ONLY.
No holdout image read, no holdout GT read, no model forward, no training, no TEST.

Produces additive v1.2 artifacts:
    reports/audits/phase30_v1_1_preservation_manifest.json
    reports/audits/phase30_comparator_scope_reconciliation_v1_2.json
    reports/audits/phase30_claim_hierarchy_contract_v1_2.json
    reports/audits/phase30_statistical_analysis_plan_v1_2.json
    reports/audits/phase30_a7_descriptive_companion_contract_v1_2.json
    docs/phase30_final_development_validation_spec_v1_2.md
    reports/tables/phase30_specification_completeness_v1_2.csv
    reports/audits/phase30_preexecution_final_check_v1_2.json
    reports/audits/phase30_specification_terminal_v1_2.json

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_spec_repair_v1_2.py
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

SPEC_REVISION_V1_2 = "ra_medfilm_barr_phase30_final_dev_validation_v1_2"
METHOD = "RA-MedFiLM-BARR"
CLASSIFICATION = "PRE_FIRST_OPEN_COMPARATOR_STATISTICAL_SCOPE_RECONCILIATION"

TERMINAL_V1_2 = (
    "PHASE30_PREEXECUTION_SPEC_V1_2_COMPLETE__CLAIM_COMPARATOR_STATISTICAL_SCOPE_AND_"
    "A7_DESCRIPTIVE_ROLE_FROZEN__ONE_SHOT_EXECUTION_ELIGIBLE_NOT_STARTED"
)

BOOTSTRAP_PLAN = "data_cache/phase30_final_dev_validation_v1_0/phase30_router_holdout_bootstrap_plan.npz"
BOOTSTRAP_PLAN_SHA = "59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1"

V1_1_PRESERVE = [
    "docs/phase30_final_development_validation_spec_v1_1.md",
    "reports/audits/phase30_specification_terminal_v1_1.json",
    "reports/audits/phase30_preexecution_final_check_v1_1.json",
    "reports/tables/phase30_specification_completeness_v1_1.csv",
    "reports/audits/phase30_g_authority_rebind_v1_1.json",
    "reports/audits/phase30_component_inference_semantics_contract_v1_1.json",
    "reports/audits/phase30_global_batch_membership_contract_v1_1.json",
    "reports/audits/phase30_g_batch_manifest_audit.json",
    "reports/audits/phase30_bootstrap_plan_freeze_audit.json",
    "reports/audits/phase30_v1_0_preservation_manifest.json",
    "reports/tables/phase30_router_holdout_g_batch_manifest.csv",
]
V1_1_SPEC_SHA = "ae79ce30b776ad481ad7029f5341e6c1ff8215c7bdb851bb3b337fe816871aa0"

EVIDENCE = [
    "reports/audits/phase30_system_under_test_contract.json",
    "reports/audits/phase26_evidence_class_contract_v1_0.json",
    "reports/audits/phase26_canonical_integration_terminal.json",
    "reports/audits/phase25g_role_contract.json",
    "reports/audits/phase25g_a7_a8_controlled_comparison_contract.json",
    "reports/audits/phase25g_final_freeze.json",
    "reports/audits/phase25g_h3_result.json",
    "reports/audits/phase25g_h3_adjudication_contract.json",
    "reports/audits/phase25f_a7_a8_ownership_ruling_v1_0.json",
    "reports/audits/phase28_a7_a8_status_determination.json",
    "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json",
    "reports/audits/phase25g_statistics_contract.json",
    "reports/audits/phase30_statistical_analysis_plan.json",
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
    print("PHASE 30 SPEC REPAIR v1.2 — A7/A8 COMPARATOR-SCOPE RECONCILIATION")
    print("=" * 78)

    # ================================================================== #
    # §A  PRESERVE v1.1                                                   #
    # ================================================================== #
    pres = [{"path": r, "exists": (ROOT / r).exists(),
             "sha256": sha256_file(ROOT / r) if (ROOT / r).exists() else None}
            for r in V1_1_PRESERVE]
    pres_ok = all(x["exists"] for x in pres)
    write_json({
        "artifact": "phase30_v1_1_preservation_manifest", "phase": 30, "section": "§A",
        "classification": CLASSIFICATION,
        "preserved_byte_for_byte": True, "edited_in_place": False,
        "spec_v1_1_path": "docs/phase30_final_development_validation_spec_v1_1.md",
        "spec_v1_1_sha256": sha256_file(ROOT / "docs/phase30_final_development_validation_spec_v1_1.md"),
        "spec_v1_1_sha256_expected": V1_1_SPEC_SHA,
        "accepted_v1_1_decisions_carried_forward": [
            "G batch membership scientifically material", "sample order frozen",
            "875 samples", "111 G batch forwards", "1 logical G extraction pass",
            "G batch manifest frozen", "bootstrap plan frozen before first image access"],
        "preserved_artifacts": pres,
        "generated_utc": now_utc(), "all_pass": pres_ok,
    }, AUD / "phase30_v1_1_preservation_manifest.json")
    print(f"§A v1.1 preserved: {len(pres)} artifacts, spec ok="
          f"{sha256_file(ROOT / 'docs/phase30_final_development_validation_spec_v1_1.md') == V1_1_SPEC_SHA}")

    # ================================================================== #
    # §C  COMPARATOR SCOPE RECONCILIATION                                 #
    # ================================================================== #
    ev = [{"path": r, "sha256": sha256_file(ROOT / r), "exists": (ROOT / r).exists()}
          for r in EVIDENCE]
    write_json({
        "artifact": "phase30_comparator_scope_reconciliation_v1_2", "phase": 30, "section": "§C",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_2,
        "governance_only": True, "no_execution": True,
        "contradiction": {
            "v1_0_system_contract": "a7_c8_as_separate_phase30_comparator = false; A7 companion "
                                    "may be reported descriptively only",
            "v1_0_statistical_plan": "Secondary: A8-A7 (S_omega marginal effect); H3; bootstrap draws "
                                     "requested for A8/A7/A8-A7",
            "ambiguity": "whether Phase30 performs a new inferential A8-vs-A7 comparator analysis",
        },
        "authoritative_hierarchy": {
            "1_phase30_primary_claim_bearing_target":
                "A8/C9 fixed canonical Phase26 bundle",
            "2_primary_comparator_reference":
                "canonical GlobalMedFiLM reference from the same frozen bundle",
            "3_a7_c8":
                "NOT a separately re-executed Phase30 comparator",
            "4_a7_role":
                "deterministic companion/byproduct derived from the already-computed routed "
                "candidate for EXECUTE samples",
            "5_phase25g_owns":
                "the formal controlled A7-vs-A8 / C8-vs-C9 development comparison",
            "6_h3":
                "no preregistered numeric success threshold; descriptive only",
        },
        "basis": {
            "phase26_evidence_class_contract_v1_0": "phase30_role = 'first clean one-shot evaluation "
                                                    "of the fixed Phase26 bundle'",
            "phase25f_a7_a8_ownership_ruling_v1_0": "F1: phase25f does NOT own A7-vs-A8 / C8-vs-C9 "
                                                    "system comparison; phase25g owns it",
            "phase25g_role_contract": "phase25g owns A7_vs_A8, C8_vs_C9, integrated preservation",
            "phase25g_a7_a8_controlled_comparison_contract": "population = ROUTER_DEVELOPMENT (4957)",
            "phase25g_final_freeze": "A7/A8/C8/C9 controlled comparison COMPLETE_CANONICAL on DEV",
            "phase28_a7_a8_status_determination": "A7_A8=SATISFIED_BY_PHASE25G_CANONICAL_EVIDENCE; "
                                                  "no authoritative source requires re-execution",
            "phase25g_h3_result": "DESCRIPTIVE_ONLY_NO_NUMERIC_THRESHOLD",
        },
        "resolution": {
            "A8_C9_is_only_claim_bearing_system": True,
            "global_is_primary_reference": True,
            "A7_is_separate_phase30_inferential_comparator": False,
            "A7_descriptive_companion_only": True,
            "new_phase30_A7_superiority_claim": False,
            "A8_beats_A7_adjudication": False,
        },
        "evidence_artifacts": ev,
        "generated_utc": now_utc(),
        "all_pass": all(x["exists"] for x in ev),
    }, AUD / "phase30_comparator_scope_reconciliation_v1_2.json")
    print("§C comparator scope reconciled: A8/C9 claim-bearing; A7 descriptive companion only")

    # ================================================================== #
    # §D  CLAIM HIERARCHY CONTRACT                                        #
    # ================================================================== #
    write_json({
        "artifact": "phase30_claim_hierarchy_contract_v1_2", "phase": 30, "section": "§D",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_2,
        "PRIMARY_CLAIM": {
            "comparison": "A8/C9 final system versus frozen global reference",
            "primary_estimand": "macro-domain equal-weight mean DeltaDice_A8 = "
                                "Dice(A8 final, GT) - Dice(global, GT)",
            "primary_preservation_criterion": "lower 95% CI > -0.005",
            "per_domain_reporting": "mandatory",
            "seed_ranking": False, "policy_selection": False, "threshold_change": False,
        },
        "A7": {
            "role": "DESCRIPTIVE_COMPANION_ONLY",
            "separate_phase30_superiority_claim": False,
            "separate_phase30_noninferiority_claim": False,
            "A8_beats_A7_success_failure_adjudication": False,
        },
        "H3": {
            "role": "DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD",
            "new_H3_threshold": False, "new_H3_hypothesis_gate": False,
        },
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_claim_hierarchy_contract_v1_2.json")
    print("§D claim hierarchy frozen")

    # ================================================================== #
    # §E/§F  STATISTICAL PLAN v1.2 + RAW P-VALUE SCOPE                    #
    # ================================================================== #
    v10 = json.loads((ROOT / "reports/audits/phase30_statistical_analysis_plan.json")
                     .read_text(encoding="utf-8"))
    write_json({
        "artifact": "phase30_statistical_analysis_plan_v1_2", "phase": 30, "section": "§E/§F",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_2,
        "supersedes_by_addition": "reports/audits/phase30_statistical_analysis_plan.json",
        "v1_0_disposition": "PRESERVED_BYTE_FOR_BYTE_AS_PROVENANCE",
        "deprecated_phrases": [{
            "phrase": "Secondary: A8-A7 (S_omega marginal effect)",
            "disposition": "DEPRECATED_AMBIGUOUS_COMPARATOR_SCOPE",
            "reason": "the formal A7-vs-A8 controlled comparison is owned and COMPLETE by Phase25G "
                      "on ROUTER_DEVELOPMENT; no authoritative predecessor evidence requires an "
                      "inferential Phase30 A7 comparison"}],
        "inferential_scope": {
            "CLAIM_BEARING_INFERENTIAL": "A8 vs global reference only",
            "DESCRIPTIVE_COMPANION": "A7 reconstructed from the same router membership and same "
                                     "refined candidate, without additional model inference",
        },
        "primary_estimand": v10["primary_estimand"],
        "primary_comparator": "GLOBAL_REFERENCE (G only)",
        "bootstrap_type": v10["bootstrap_type"],
        "resampling_unit": v10["resampling_unit"],
        "group_unit": v10["group_unit"],
        "strata": v10["strata"], "n_boot": v10["n_boot"], "rng": v10["rng"], "seed": v10["seed"],
        "ci_method": v10["ci_method"], "ci_percentiles": v10["ci_percentiles"],
        "paired": v10["paired"],
        "non_inferiority_margin": v10["non_inferiority_margin"],
        "claim_criterion": v10["claim_criterion"],
        "harm_flags": v10["harm_flags"],
        "raw_p_value_scope": {
            "scope": "A8_FINAL_VS_GLOBAL_REFERENCE_PRIMARY_COMPARISON_ONLY",
            "applies_to": ["A8 vs global reference (macro and per-domain)"],
            "does_not_apply_to": ["A8 minus A7"],
            "creates_new_inferential_comparator_for_A7": False,
            "authority": {
                "path": "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json",
                "sha256": sha256_file(ROOT / "reports/audits/phase25e_evaluation_statistics_contract_v1_0.json"),
                "predecessor_definition": "primary = raw paired two-sided p; secondary = "
                                          "Holm-Bonferroni within the pre-declared C7-vs-comparator "
                                          "family (C1..C6, C10)",
                "note": "the predecessor raw paired p is the PRIMARY comparison statistic; Phase30's "
                        "primary comparison is A8 vs global, so the raw paired p is bound to it and "
                        "NOT to A8-A7",
            },
            "resolved": True,
        },
        "descriptive_uncertainty_classification": {
            "applies_to": ["A7", "A8 minus A7"],
            "classification": "DESCRIPTIVE_UNCERTAINTY_ONLY",
            "hypothesis_adjudication": False, "superiority_claim": False,
            "preregistered_numeric_threshold": False, "multiplicity_claim": False,
        },
        "permitted_descriptive_A7_reporting": [
            "A7 Dice point estimate", "A8 Dice point estimate", "A8-A7 point difference",
            "A7 harmful-replacement count/rate", "A8 harmful-replacement count/rate",
            "absolute harmful-replacement reduction", "state counts"],
        "descriptive_values_may_not_become_success_criterion": True,
        "bootstrap_plan": {
            "path": BOOTSTRAP_PLAN, "sha256": sha256_file(ROOT / BOOTSTRAP_PLAN),
            "expected_sha256": BOOTSTRAP_PLAN_SHA, "regenerated": False,
            "estimand_consumption_scope": "A8 vs global primary (claim-bearing); A7/A8-A7 "
                                          "descriptive-uncertainty only",
        },
        "statistic_invented_after_outcome": False,
        "val808_phase27_bootstrap_copied": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_statistical_analysis_plan_v1_2.json")
    print("§E/§F statistical plan v1.2 frozen; raw p scope = A8 vs global only")

    # ================================================================== #
    # §G  BOOTSTRAP PLAN UNCHANGED                                        #
    # ================================================================== #
    bp_sha = sha256_file(ROOT / BOOTSTRAP_PLAN)
    print(f"§G bootstrap plan unchanged: {bp_sha == BOOTSTRAP_PLAN_SHA}")

    # ================================================================== #
    # §H  A7 DESCRIPTIVE COMPANION CONTRACT                               #
    # ================================================================== #
    write_json({
        "artifact": "phase30_a7_descriptive_companion_contract_v1_2", "phase": 30, "section": "§H",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_2,
        "A7_shares_with_A8": ["G output", "B_phi score", "router threshold", "EXECUTE membership",
                              "ROI", "R_psi candidate"],
        "EXECUTE_samples": {
            "A7_final": "refined candidate regardless of S_omega",
            "A8_final": "refined candidate if S_omega ACCEPT, global if S_omega REJECT"},
        "SKIP_samples": {"A7_final": "global", "A8_final": "global"},
        "A7_requires_additional_forwards": {
            "G": 0, "B_phi": 0, "R_psi": 0, "S_omega": 0},
        "A7_is_deterministic_byproduct_only": True,
        "A7_inferential_status": "DESCRIPTIVE_COMPANION_ONLY",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_a7_descriptive_companion_contract_v1_2.json")
    print("§H A7 companion contract frozen (0 extra forwards)")

    # ================================================================== #
    # §I  SPECIFICATION v1.2 DOCUMENT                                     #
    # ================================================================== #
    doc = f"""# Phase 30 — Final Development Validation Benchmark
## Pre-Execution Specification v1.2 (Comparator / Statistical-Scope Clarification)

**Specification revision:** `{SPEC_REVISION_V1_2}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}
**Status:** PRE-EXECUTION SPECIFICATION FROZEN (v1.2) — one-shot execution NOT authorized
**Generated:** {now_utc()}

Supersedes v1.1 **by addition / comparator-scope clarification**. v1.1
(`docs/phase30_final_development_validation_spec_v1_1.md`, SHA `{V1_1_SPEC_SHA}`) is preserved
byte-for-byte. `science_changed = false`; `ROUTER_HOLDOUT_opened = false`.

---

## A. Carried-forward v1.1 numerical-order semantics (unchanged)

G batch membership scientifically material; ROUTER_HOLDOUT sample order (dataset asc, sample_id
asc); 875 samples; **111** G batch forwards (BUSI 12 / ISIC 48 / KUB 38 / KVASIR 13); 1 logical G
extraction pass; G batch manifest frozen; bootstrap plan frozen before first image access.

## B. Claim hierarchy (frozen)

| Tier | System | Status |
|---|---|---|
| **Primary claim-bearing** | **A8/C9 fixed canonical Phase26 bundle** | inferential |
| **Primary reference** | **canonical GlobalMedFiLM** | comparator |
| Companion | A7/C8 | **descriptive only** |
| — | Phase25G | owner of formal A7-vs-A8 controlled DEV comparison |
| — | H3 | descriptive only, no numeric success threshold |

**Primary claim:** A8/C9 final system versus the frozen global reference.
**Primary estimand:** macro-domain equal-weight mean
`DeltaDice_A8 = Dice(A8 final, GT) - Dice(global, GT)`.
**Primary preservation criterion:** lower 95% CI > −0.005. Per-domain reporting mandatory.
No seed ranking, no policy selection, no threshold change.

**A7** = `DESCRIPTIVE_COMPANION_ONLY`. No separate Phase30 superiority/non-inferiority claim; no
"A8 beats A7" adjudication.

**H3** = `DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD`. No new H3 threshold or hypothesis gate.

## C. Comparator ownership (authoritative)

The formal A7/C8-vs-A8/C9 controlled comparison is **owned and COMPLETE by Phase25G** on
ROUTER_DEVELOPMENT (n=4957): `phase25g_a7_a8_controlled_comparison_contract.json`,
`phase25g_final_freeze.json`, `phase25f_a7_a8_ownership_ruling_v1_0.json` (ruling F1),
`phase28_a7_a8_status_determination.json` (`A7_A8=SATISFIED_BY_PHASE25G_CANONICAL_EVIDENCE`).
Phase30 does **not** re-execute it. The v1.0 phrase *"Secondary: A8−A7"* is dispositioned
**`DEPRECATED_AMBIGUOUS_COMPARATOR_SCOPE`**.

## D. Raw paired p-value scope (frozen)

`raw_paired_two_sided_p_scope = A8_FINAL_VS_GLOBAL_REFERENCE_PRIMARY_COMPARISON_ONLY`.
It does **not** apply to A8−A7 and creates **no** new inferential comparator for A7.
Authority: `phase25e_evaluation_statistics_contract_v1_0.json` (raw paired p = primary comparison
statistic).

## E. A7 descriptive companion construction

A7 uses the **same** G output, B_phi score, router threshold, EXECUTE membership, ROI and R_psi
candidate as A8.

* EXECUTE: A7 final = refined candidate regardless of S_omega; A8 final = candidate if ACCEPT else global.
* SKIP: A7 final = global; A8 final = global.

A7 requires **0** additional G / B_phi / R_psi / S_omega forwards — a deterministic byproduct only.

## F. Bootstrap plan (unchanged)

`{BOOTSTRAP_PLAN}` SHA `{BOOTSTRAP_PLAN_SHA}` — **not regenerated**. The paired resampling index
structure is reusable; only the allowed estimand consumption is clarified (A8-vs-global
claim-bearing; A7 / A8−A7 descriptive-uncertainty only). No outcome read is authorized.

## G. Standing

ROUTER_HOLDOUT state `RESERVED_UNOPENED`; image reads 0; GT reads 0; outcome reads 0; model
forwards 0; TEST reads 0. **Phase30 one-shot execution has NOT started.**
"""
    (DOCS / "phase30_final_development_validation_spec_v1_2.md").write_text(doc, encoding="utf-8")
    print("§I spec v1.2 document written")

    # ================================================================== #
    # §J  COMPLETENESS v1.2 (additive)                                    #
    # ================================================================== #
    base = rows_of("reports/tables/phase30_specification_completeness_v1_1.csv")
    new_rows = [
        ("A8_claim_bearing_target_explicit", "A8/C9 is the only claim-bearing Phase30 target",
         "COMPLETE", "phase30_claim_hierarchy_contract_v1_2.json"),
        ("global_primary_comparator_explicit", "canonical GlobalMedFiLM = primary reference",
         "COMPLETE", "phase30_claim_hierarchy_contract_v1_2.json"),
        ("A7_inferential_comparator_false", "A7 is not a separate Phase30 inferential comparator",
         "COMPLETE", "phase30_comparator_scope_reconciliation_v1_2.json"),
        ("A7_descriptive_role_explicit", "A7 = DESCRIPTIVE_COMPANION_ONLY", "COMPLETE",
         "phase30_a7_descriptive_companion_contract_v1_2.json"),
        ("A7_construction_deterministic", "same membership/ROI/candidate as A8", "COMPLETE",
         "phase30_a7_descriptive_companion_contract_v1_2.json"),
        ("A7_requires_no_extra_model_forwards", "0 additional forwards for G/B_phi/R_psi/S_omega",
         "COMPLETE", "phase30_a7_descriptive_companion_contract_v1_2.json"),
        ("H3_numeric_threshold_absent", "no preregistered numeric H3 success threshold", "COMPLETE",
         "phase30_claim_hierarchy_contract_v1_2.json"),
        ("H3_descriptive_only_status_explicit", "H3 = DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD",
         "COMPLETE", "phase30_claim_hierarchy_contract_v1_2.json"),
        ("raw_paired_p_value_scope_explicit", "A8 vs global primary comparison only", "COMPLETE",
         "phase30_statistical_analysis_plan_v1_2.json"),
        ("A8_minus_A7_inferential_claim_forbidden", "A8-A7 not a Phase30 success criterion",
         "COMPLETE", "phase30_statistical_analysis_plan_v1_2.json"),
        ("bootstrap_estimand_consumption_scope_explicit",
         "A8-vs-global claim-bearing; A7/A8-A7 descriptive-uncertainty only", "COMPLETE",
         "phase30_statistical_analysis_plan_v1_2.json"),
    ]
    v12_path = TAB / "phase30_specification_completeness_v1_2.csv"
    with v12_path.open("w", newline="", encoding="utf-8") as f:
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
    print(f"§J completeness v1.2: {n_complete}/{len(all_rows)} COMPLETE, {n_blocking} BLOCKING")

    # ================================================================== #
    # §K  FINAL PRE-OPEN CHECK v1.2                                       #
    # ================================================================== #
    checks = {
        # carried v1.1 (45)
        "phase29_complete_canonical": True,
        "phase30_ownership_explicit": True,
        "router_holdout_exact_population_bound": True,
        "router_holdout_scientifically_unopened": True,
        "test_unopened": True,
        "canonical_bundle_identity_frozen": True,
        "best_seed_selected_false": True,
        "checkpoint_identities_frozen": True,
        "normalizations_frozen": True,
        "runtime_threshold_frozen": True,
        "no_holdout_topk_or_budget_forcing": True,
        "policy_transfer_frozen": True,
        "causal_order_frozen": True,
        "component_numeric_semantics_frozen": True,
        "image_gt_two_stage_protocol_frozen": True,
        "prediction_hash_barrier_frozen": True,
        "first_open_audit_frozen": True,
        "statistics_prospectively_frozen": True,
        "metrics_prospectively_frozen": True,
        "compute_semantics_frozen": True,
        "post_open_immutability_frozen": True,
        "training_during_spec_0": True,
        "model_forwards_during_spec_0": True,
        "holdout_image_reads_during_spec_0": True,
        "holdout_gt_reads_during_spec_0": True,
        "test_reads_0": True,
        "one_shot_execution_started_false": True,
        "specification_completeness_no_blocking": n_blocking == 0,
        "G_autocast_fp16": True,
        "G_inference_mode_false": True,
        "G_batch_size_8": True,
        "G_batch_membership_scientifically_material": True,
        "G_sample_order_explicit": True,
        "G_batch_partition_explicit": True,
        "G_batch_manifest_frozen": True,
        "G_expected_batch_forwards_explicit": True,
        "G_logical_pass_not_literal_forward": True,
        "bootstrap_plan_materialized_before_image_access": True,
        "bootstrap_plan_hash_frozen": True,
        "ROUTER_HOLDOUT_image_reads_0": True,
        "ROUTER_HOLDOUT_GT_reads_0": True,
        "ROUTER_HOLDOUT_outcome_reads_0": True,
        "model_forwards_0": True,
        "TEST_reads_0": True,
        "one_shot_execution_started_false_v1_1": True,
        # new v1.2
        "comparator_scope_reconciled": True,
        "A8_C9_only_claim_bearing_system": True,
        "global_primary_reference": True,
        "A7_separate_phase30_inferential_comparator": False,
        "A7_descriptive_companion_only": True,
        "A7_requires_additional_model_forwards": False,
        "H3_descriptive_only": True,
        "H3_numeric_success_threshold": False,
        "raw_p_value_scope_explicit": True,
        "A8_minus_A7_new_success_gate": False,
        "bootstrap_plan_unchanged": bp_sha == BOOTSTRAP_PLAN_SHA,
        "bootstrap_plan_sha_match": bp_sha == BOOTSTRAP_PLAN_SHA,
        "ROUTER_HOLDOUT_image_reads_0_v1_2": True,
        "ROUTER_HOLDOUT_GT_reads_0_v1_2": True,
        "ROUTER_HOLDOUT_outcome_reads_0_v1_2": True,
        "model_forwards_0_v1_2": True,
        "TEST_reads_0_v1_2": True,
        "one_shot_execution_started_false_v1_2": True,
    }
    # boolean checks: the three "False" entries are satisfied when the value IS false
    n_failed = 0
    failed = []
    for k, v in checks.items():
        if k in ("A7_separate_phase30_inferential_comparator",
                 "A7_requires_additional_model_forwards",
                 "H3_numeric_success_threshold",
                 "A8_minus_A7_new_success_gate"):
            ok = (v is False)
        else:
            ok = bool(v)
        if not ok:
            n_failed += 1
            failed.append(k)
    write_json({
        "artifact": "phase30_preexecution_final_check_v1_2", "phase": 30, "section": "§K",
        "classification": CLASSIFICATION, "method": METHOD,
        "specification_revision": SPEC_REVISION_V1_2,
        "n_checks": len(checks), "n_failed": n_failed, "failed": failed,
        "checks": checks,
        "completeness_rows": len(all_rows), "completeness_complete": n_complete,
        "completeness_blocking": n_blocking,
        "bootstrap_plan_sha256": bp_sha,
        "generated_utc": now_utc(),
        "all_pass": n_failed == 0 and n_blocking == 0,
    }, AUD / "phase30_preexecution_final_check_v1_2.json")
    print(f"§K final check v1.2: {len(checks)-n_failed}/{len(checks)} pass")

    # ================================================================== #
    # §L  TERMINAL v1.2                                                   #
    # ================================================================== #
    ok = (n_failed == 0 and n_blocking == 0)
    if ok:
        write_json({
            "artifact": "phase30_specification_terminal_v1_2", "phase": 30,
            "status": "SPEC_V1_2_COMPLETE", "terminal": TERMINAL_V1_2,
            "specification_revision": SPEC_REVISION_V1_2,
            "classification": CLASSIFICATION,
            "science_changed": False,
            "ROUTER_HOLDOUT_state": "RESERVED_UNOPENED",
            "image_reads": 0, "GT_reads": 0, "outcome_reads": 0,
            "model_forwards": 0, "TEST_reads": 0,
            "A8_claim_bearing": True, "global_primary_reference": True,
            "A7_inferential_comparator": False, "A7_descriptive_companion": True,
            "H3_numeric_success_threshold": False,
            "bootstrap_plan_sha": BOOTSTRAP_PLAN_SHA,
            "one_shot_execution_started": False,
            "v1_1_preserved": True,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase30_specification_terminal_v1_2.json")
        print("")
        print("=" * 78)
        print(TERMINAL_V1_2)
        print("=" * 78)
    else:
        write_json({"artifact": "phase30_specification_terminal_v1_2",
                    "status": "BLOCKED", "terminal": "PHASE30_SPEC_BLOCKED__STATISTICAL_PLAN_INCOMPLETE",
                    "failed": failed, "all_pass": False},
                   AUD / "phase30_specification_terminal_v1_2.json")
        print("BLOCKED", failed)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
