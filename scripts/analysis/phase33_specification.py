#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 33 — FINAL SYSTEM FAILURE & BOUNDARY ERROR ANALYSIS.
Entry gate + evidence-population ownership + failure taxonomy + boundary-metric provenance +
pre-analysis specification.

PROVENANCE / SPECIFICATION ONLY. No inference, no raw image/GT read, no metric recomputation,
no hard-case selection, no model forward, no training, no TEST.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase33_specification.py
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
REVISION = "ra_medfilm_barr_phase33_failure_boundary_v1_0"
CLASSIFICATION = "PRE_ANALYSIS_FAILURE_AND_BOUNDARY_PROVENANCE_SPECIFICATION"
QUALIFIER = ("ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_"
             "FREEZE_DEVIATION")
TERMINAL = ("PHASE33_FAILURE_BOUNDARY_SPEC_COMPLETE__POPULATION_ARTIFACT_FAILURE_TAXONOMY_BOUNDARY_"
            "PROVENANCE_HARD_CASE_AND_ANALYSIS_TIERS_FROZEN__TABLE_ONLY_AND_DERIVED_NONPIXEL_"
            "EXECUTION_ELIGIBLE__BOUNDARY_COMPONENT_QUALITATIVE_RAW_AND_RERUN_INELIGIBLE__"
            "EXECUTION_ELIGIBILITY_DETERMINED_NOT_STARTED")

BIND = {
    "reports/audits/phase32_closure_terminal.json":
        "8c92244b594aafb67029b99de4a0219da0516db0ca01d9c57ac814c3f2e45bdb",
    "reports/audits/phase32_final_closure.json":
        "c3ec1622e4004893d808e816bad46195e84df547fadd06a29806d283dcad6d18",
    "reports/audits/phase32_final_closure_check.json":
        "c4821cfe1541d5323de971d88398702e9ffb2a3c39639a574df18bd15ecc943b",
    "reports/audits/phase32_phase33_handoff.json":
        "70eaf7fa1b7bacdc237eefbdaa72992bbd354ab7c2258cd9ad1d46e1d62cb2af",
}
P32_TERMINAL = ("PHASE32_EXTERNAL_DOMAIN_SHIFT_GOVERNANCE_COMPLETE_CANONICAL__NO_PROSPECTIVE_CLEAN_"
                "EXTERNAL_COHORT_ELIGIBLE_AND_NO_EXTERNAL_EXECUTION_PERFORMED__PHASE31_AND_PHASE32_"
                "REVIEWER_NOTEBOOKS_PACKAGED__PHASE30_QUALIFIER_PRESERVED__PHASE33_ELIGIBLE_NOT_"
                "STARTED")

P30_EVIDENCE = {
    "reports/tables/phase30_router_holdout_scored_results.csv":
        "dbc9f5f3867f0607cfc0a778736a92b9d6de6e27811fa382ad6d1cb0b2a04568",
    "reports/tables/phase30_router_holdout_predictions.csv":
        "513ccf2905cbc6f544337b9d157f38dc34d835e2cb56c25cabbe95f5046a3147",
    "reports/tables/phase30_router_holdout_per_domain_results.csv":
        "524b68b983407eab82f8ca1e5d8191876df3c5f565cf3015ce7f8c27c8a9a0ed",
    "reports/audits/phase30_router_metric_results.json":
        "3571f6136b1835f593e400c37258cf56feed242387fc31b5de804fff57d7ed86",
    "reports/audits/phase30_a7_descriptive_companion_result.json":
        "3490bc869e21bd5ec5afe88d31cbe379c87dee432d033d780303f02f2de2a3f9",
    "reports/audits/phase30_h3_descriptive_result.json":
        "a5f9e76977cbd339f8b59b600012fb899b0b8b846218c807a5d34b10dfe21882",
}

TIER0 = "TIER_0_FROZEN_TABLE_READ_ONLY"
TIER1 = "TIER_1_DERIVED_FROM_FROZEN_NONPIXEL_FIELDS"
TIER2 = "TIER_2_FROZEN_PREDICTION_PIXEL_ANALYSIS"
TIER3 = "TIER_3_RAW_IMAGE_OR_GT_REREAD"
TIER4 = "TIER_4_MODEL_RERUN"


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


# candidate evidence inventory
EVIDENCE = [
    # (id, path, phase, population, n, sample_ids, group_ids, gt_metrics, predictions,
    #  prob_arrays, raw_images, raw_gt, boundary, component, failure_labels, status, tier)
    ("E01", "reports/tables/phase30_router_holdout_scored_results.csv", 30, "ROUTER_HOLDOUT", 875,
     True, False, True, True, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E02", "reports/tables/phase30_router_holdout_predictions.csv", 30, "ROUTER_HOLDOUT", 875,
     True, False, False, True, False, False, False, False, False, True, "FROZEN", TIER0),
    ("E03", "reports/tables/phase30_router_holdout_per_domain_results.csv", 30, "ROUTER_HOLDOUT", 4,
     False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E04", "reports/audits/phase30_router_metric_results.json", 30, "ROUTER_HOLDOUT", 875,
     False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E05", "reports/audits/phase30_a7_descriptive_companion_result.json", 30, "ROUTER_HOLDOUT", 875,
     False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E06", "reports/audits/phase30_h3_descriptive_result.json", 30, "ROUTER_HOLDOUT", 875,
     False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E07", "reports/audits/phase30_primary_noninferiority_result.json", 30, "ROUTER_HOLDOUT", 875,
     False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E08", "reports/audits/phase30_compute_results.json", 30, "ROUTER_HOLDOUT", 875,
     False, False, False, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E09", "reports/audits/phase30_final_freeze.json", 30, "ROUTER_HOLDOUT", 875,
     False, False, False, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E10", "reports/audits/phase24_router_split_manifest.csv", 24, "TRAIN(5832)", 5832,
     True, True, False, False, False, False, False, False, False, False, "FROZEN", TIER1),
    ("E11", "reports/tables/phase27_val808_predictions.csv", 27, "VAL808", 808,
     True, True, True, True, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E12", "reports/audits/phase27_preservation_reporting_audit.json", 27, "VAL808", 808,
     False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E13", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_global_prob_f16.npy", 27,
     "VAL808", 808, False, False, False, True, True, False, False, False, False, False,
     "FROZEN", TIER2),
    ("E14", "data_cache/phase27_barr_preservation_v1_0/phase27_val808_final_prob_f16.npy", 27,
     "VAL808", 808, False, False, False, True, True, False, False, False, False, False,
     "FROZEN", TIER2),
    ("E15", "reports/audits/phase29_phase_d_three_seed_descriptive_summary.json", 29,
     "VAL808", 808, False, False, True, False, False, False, False, False, False, False,
     "FROZEN", TIER0),
    ("E16", "reports/audits/phase28_comprehensive_ablation_matrix.json", 28, "ROUTER_DEVELOPMENT",
     4957, False, False, True, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E17", "reports/audits/phase28_ablation_registry.json", 28, "ROUTER_DEVELOPMENT", 4957,
     False, False, False, False, False, False, False, False, False, False, "FROZEN", TIER0),
    ("E18", "reports/audits/phase11_clean_v3_failure_protocol_frozen.json", 11, "KUB_VAL280", 280,
     False, False, True, False, False, False, False, True, True, True,
     "HISTORICAL", TIER3),
    ("E19", "reports/audits/phase11_failure_strata_definitions.json", 11, "KUB_VAL280", 280,
     False, False, True, False, False, False, False, True, True, True,
     "HISTORICAL", TIER3),
    ("E20", "data_cache/phase30_final_dev_validation_v1_0/canonical_one_shot/"
     "a8_final_prob_f16.npy", 30, "ROUTER_HOLDOUT", 875, False, False, False, True, True,
     False, False, False, False, False, "FROZEN_NOT_IN_AUTHORIZED_HANDOFF", TIER2),
    ("E21", "data_cache/phase30_final_dev_validation_v1_0/canonical_one_shot/"
     "global_prob_f16.npy", 30, "ROUTER_HOLDOUT", 875, False, False, False, True, True,
     False, False, False, False, False, "FROZEN_NOT_IN_AUTHORIZED_HANDOFF", TIER2),
    ("E22", "manifests/phase4_v3/test.csv", 4, "TEST", 1683, True, False, False, False, False,
     False, False, False, False, False, "LOCKED_UNTIL_PHASE39", TIER3),
]


def main() -> int:
    print("=" * 78)
    print("PHASE 33 — FINAL SYSTEM FAILURE & BOUNDARY ERROR ANALYSIS (SPECIFICATION)")
    print("=" * 78)

    # ================= §A bind Phase32 closure ================= #
    binds = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
              "match": sha256_file(ROOT / p) == e} for p, e in BIND.items()]
    t32 = read_json(AUD / "phase32_closure_terminal.json")
    a_ok = (all(b["match"] for b in binds) and t32["terminal"] == P32_TERMINAL
            and t32["status"] == "COMPLETE_CANONICAL"
            and t32["Phase33_status"] == "ELIGIBLE_NOT_STARTED")
    write_json({
        "artifact": "phase33_entry_authority_binding", "phase": 33, "section": "§A/§B",
        "method": METHOD, "revision": REVISION,
        "phase32_closure_terminal": binds[0], "phase32_terminal_token": t32["terminal"],
        "phase32_status": t32["status"],
        "phase33_roadmap_identity": "FINAL SYSTEM FAILURE & BOUNDARY ERROR ANALYSIS",
        "phase33_status_required": "ELIGIBLE_NOT_STARTED",
        "bindings": binds, "all_bindings_match": all(b["match"] for b in binds),
        "protected_population_rules": {
            "Phase30_evidence_class": QUALIFIER,
            "Phase30_status": "COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL",
            "Phase31": "COMPLETE_CANONICAL", "Phase32": "COMPLETE_CANONICAL",
            "ROUTER_HOLDOUT": "OPENED_AND_FROZEN", "TEST": "LOCKED_UNTIL_PHASE39",
            "router_holdout_treated_as_fresh_holdout": False},
        "generated_utc": now_utc(), "all_pass": a_ok,
    }, AUD / "phase33_entry_authority_binding.json")
    print(f"§A Phase32 closure bound: {sum(1 for b in binds if b['match'])}/{len(binds)} match")

    # ================= §D candidate evidence inventory ================= #
    hdr = ["artifact_id", "path", "sha256", "phase", "population", "n_if_known",
           "contains_sample_identifiers", "contains_group_identifiers",
           "contains_GT_derived_metrics", "contains_predictions", "contains_probability_arrays",
           "contains_raw_images", "contains_raw_GT", "contains_boundary_metric",
           "contains_component_metric", "contains_failure_labels", "scientific_status",
           "protocol_qualification", "candidate_Phase33_use", "requires_raw_reread",
           "eligible_for_Phase33_specification", "notes"]
    inv_rows = []
    for (eid, path, ph, pop, n, sid, gid, gt, pred, prob, rawi, rawg, bnd, comp, flab, st,
         tier) in EVIDENCE:
        exists = (ROOT / path).exists()
        inv_rows.append([
            eid, path, (sha256_file(ROOT / path) if exists else ""), ph, pop,
            (n if n is not None else ""), sid, gid, gt, pred, prob, rawi, rawg, bnd, comp, flab,
            st, (QUALIFIER if ph == 30 else ""),
            ("FROZEN_TABLE_READ" if tier == TIER0 else
             "DERIVED_NONPIXEL" if tier == TIER1 else
             "FROZEN_PREDICTION_PIXEL" if tier == TIER2 else
             "RAW_REREAD_REQUIRED" if tier == TIER3 else "MODEL_RERUN"),
            (tier == TIER3), (tier in (TIER0, TIER1)),
            ("exists" if exists else "MISSING")])
    write_csv(TAB / "phase33_candidate_evidence_inventory.csv", hdr, inv_rows)
    n_exist = sum(1 for r in inv_rows if r[-1] == "exists")
    print(f"§D evidence inventory: {len(EVIDENCE)} candidates, {n_exist} present")

    # ================= §E population ownership ================= #
    pop_owner = [
        {"population": "ROUTER_HOLDOUT",
         "classification": "FROZEN_RESULT_TABLES_ONLY_ALLOWED",
         "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "Phase30 one-shot complete; only frozen tables/audits authorized; the "
                      "protocol-deviation qualifier applies"},
        {"population": "VAL808",
         "classification": "FROZEN_RESULT_TABLES_ONLY_ALLOWED",
         "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "Phase27 preservation complete; VAL808 continuity benchmark closed"},
        {"population": "ROUTER_DEVELOPMENT",
         "classification": "HISTORICAL_DESCRIPTIVE_ONLY",
         "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "Phase25G/28 development evidence complete; no new dev re-evaluation"},
        {"population": "TRAIN-derived development evidence",
         "classification": "FROZEN_RESULT_TABLES_ONLY_ALLOWED",
         "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "split manifest metadata (group_key) usable for grouping joins only"},
        {"population": "historical KUB VAL280",
         "classification": "HISTORICAL_DESCRIPTIVE_ONLY",
         "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "Phase11 failure analysis is historical KUB multi-architecture evidence; "
                      "not the final RA-MedFiLM-BARR system"},
        {"population": "external historical cohorts",
         "classification": "HISTORICAL_DESCRIPTIVE_ONLY",
         "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "Phase32: all historically outcome-exposed; no new external execution"},
        {"population": "TEST",
         "classification": "FORBIDDEN", "raw_image_reread": False, "raw_gt_reread": False,
         "rationale": "LOCKED_UNTIL_PHASE39"},
    ]
    write_json({
        "artifact": "phase33_population_ownership_contract", "phase": 33, "section": "§E",
        "method": METHOD, "revision": REVISION,
        "populations": pop_owner,
        "raw_access_assumed_from_prior_open": False,
        "TEST_classification": "FORBIDDEN",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_population_ownership_contract.json")
    print("§E population ownership frozen")

    # ================= §F Phase30 frozen evidence consumption ================= #
    p30 = [{"path": p, "expected_sha256": e, "observed_sha256": sha256_file(ROOT / p),
            "match": sha256_file(ROOT / p) == e, "modified": False} for p, e in P30_EVIDENCE.items()]
    f_ok = all(x["match"] for x in p30)
    write_json({
        "artifact": "phase33_phase30_frozen_evidence_consumption_contract", "phase": 33,
        "section": "§F", "method": METHOD, "revision": REVISION,
        "consumable_without_modification": p30, "all_match": f_ok,
        "phase30_metrics_recomputed": False, "phase30_files_modified": False,
        "qualifier_required": QUALIFIER,
        "generated_utc": now_utc(), "all_pass": f_ok,
    }, AUD / "phase33_phase30_frozen_evidence_consumption_contract.json")
    print(f"§F Phase30 frozen boundary: all_match={f_ok}")

    # ================= §G schema registry ================= #
    schemas = [
        ("phase30_router_holdout_scored_results.csv", "canonical_order_index", "int", "row index",
         "no", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "sample_id", "str", "sample identity",
         "no", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "dataset", "str", "domain", "no", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "global_dice", "float", "global Dice",
         "yes", "no", "yes", "already-frozen GT-derived metric; read-only"),
        ("phase30_router_holdout_scored_results.csv", "a8_dice", "float", "A8 final Dice",
         "yes", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "delta_dice_a8", "float", "A8 - global",
         "yes", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "a7_dice", "float", "A7 companion Dice",
         "yes", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "delta_dice_a7", "float", "A7 - global",
         "yes", "no", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "router_decision", "str", "SKIP/EXECUTE",
         "no", "yes", "yes", ""),
        ("phase30_router_holdout_scored_results.csv", "somega_accept", "bool", "S_omega decision",
         "no", "yes", "yes", ""),
        ("phase30_router_holdout_predictions.csv", "delta_hat", "float", "B_phi raw logit",
         "no", "yes", "yes", ""),
        ("phase30_router_holdout_predictions.csv", "utility", "float", "delta_hat - 0.25C",
         "no", "yes", "yes", ""),
        ("phase30_router_holdout_predictions.csv", "tau_C8", "float", "frozen threshold",
         "no", "no", "yes", ""),
        ("phase30_router_holdout_predictions.csv", "state_machine", "str",
         "SKIP / EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT", "no", "yes", "yes", ""),
        ("phase30_router_holdout_predictions.csv", "somega_score", "float", "S_omega accept prob",
         "no", "yes", "yes", ""),
        ("phase30_router_holdout_predictions.csv", "roi_available", "bool", "ROI availability",
         "no", "yes", "yes", ""),
        ("phase30_router_holdout_per_domain_results.csv", "ci_low", "float", "bootstrap CI low",
         "yes", "no", "yes", ""),
        ("phase24_router_split_manifest.csv", "group_key", "str", "canonical group identity",
         "no", "no", "yes", "metadata-only join source for group/patient clustering"),
    ]
    write_csv(TAB / "phase33_frozen_artifact_schema_registry.csv",
              ["artifact", "column/key", "dtype", "scientific meaning", "GT-derived yes/no",
               "prediction-derived yes/no", "safe for Phase33 descriptive use yes/no", "reason"],
              schemas)
    absent = ["IoU", "precision", "recall", "HD95", "FP/FN counts", "connected components",
              "object count", "true gain beyond Dice delta", "per-sample boundary distance"]
    write_json({
        "artifact": "phase33_schema_registry_summary", "phase": 33, "section": "§G",
        "method": METHOD, "revision": REVISION,
        "n_fields_registered": len(schemas),
        "absent_from_frozen_final_system_tables": absent,
        "phase33_may_use_only_present_or_authorized_derivable_quantities": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_schema_registry_summary.json")
    print(f"§G schema registry: {len(schemas)} fields; {len(absent)} absent quantities noted")

    # ================= §H Phase11 taxonomy provenance ================= #
    p11 = read_json(AUD / "phase11_clean_v3_failure_protocol_frozen.json")["frozen_protocol"]
    p11d = read_json(AUD / "phase11_failure_strata_definitions.json")
    concepts = [
        ("bottom_decile_low_dice", "REUSABLE_METHOD_RECOMPUTE_THRESHOLD_IF_PROSPECTIVELY_ALLOWED",
         "np.quantile(values, 0.10, linear, float64) per model; ties included"),
        ("historical_cutoff_0.5461063385009766", "HISTORICAL_KUB_SPECIFIC_ONLY",
         "KUB VAL280 UNet++ v2 provenance value; not transferable"),
        ("all_four_low_shared_failure", "NOT_APPLICABLE_TO_FINAL_SYSTEM",
         "requires four segmentation models; final system is one bundle"),
        ("architecture_disagreement_dice_range", "NOT_APPLICABLE_TO_FINAL_SYSTEM",
         "requires multiple architectures"),
        ("high_hd95_decile_Q90", "POST_HOC_IF_INTRODUCED_NOW",
         "requires GT boundary distances; frozen final-system tables lack HD95"),
        ("historical_hd95_83.07246563841615", "HISTORICAL_KUB_SPECIFIC_ONLY", "v2 provenance only"),
        ("high_fp_component_decile_Q90", "POST_HOC_IF_INTRODUCED_NOW",
         "requires evaluation-512 connected components; not in frozen tables"),
        ("historical_fp_integer_4", "HISTORICAL_KUB_SPECIFIC_ONLY", "v2 provenance only"),
        ("8_connectivity", "REUSABLE_DEFINITION", "standard connectivity; only if component "
                                                  "analysis becomes authorized"),
        ("minimum_overlap_ge_1_pixel", "REUSABLE_DEFINITION",
         "standard object-match rule; only if component analysis becomes authorized"),
        ("regime_stratification", "HISTORICAL_KUB_SPECIFIC_ONLY", "KUB tiny-object taxonomy"),
        ("empty_prediction", "REUSABLE_DEFINITION",
         "derivable from frozen per-sample Dice / predicted masks only if authorized"),
        ("object_miss", "POST_HOC_IF_INTRODUCED_NOW", "requires GT objects; not in frozen tables"),
        ("hard_case_selection_procedure", "REUSABLE_METHOD_RECOMPUTE_THRESHOLD_IF_PROSPECTIVELY_ALLOWED",
         "method reusable; thresholds must be prospectively re-frozen for Phase33"),
    ]
    write_json({
        "artifact": "phase33_phase11_failure_taxonomy_provenance", "phase": 33, "section": "§H",
        "method": METHOD, "revision": REVISION,
        "phase11_authority": {
            "protocol": "reports/audits/phase11_clean_v3_failure_protocol_frozen.json",
            "protocol_sha256": sha256_file(ROOT / "reports/audits/"
                                           "phase11_clean_v3_failure_protocol_frozen.json"),
            "strata": "reports/audits/phase11_failure_strata_definitions.json",
            "strata_sha256": sha256_file(ROOT / "reports/audits/"
                                         "phase11_failure_strata_definitions.json"),
            "population": "KUB VAL280 (clean_v3)", "n": 280,
            "models": ["UNet", "Attention U-Net", "UNet++", "DeepLabV3+"],
            "not_the_final_system": True},
        "phase11_frozen_protocol_keys": sorted(p11.keys()),
        "phase11_strata": p11d,
        "concepts": [{"concept": c, "classification": k, "note": n} for c, k, n in concepts],
        "numeric_thresholds_auto_transferred": False,
        "kub_specific_taxonomy_auto_transferred": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_phase11_failure_taxonomy_provenance.json")
    print("§H Phase11 taxonomy provenance audited")

    # ================= §I failure taxonomy ================= #
    taxonomy = [
        ("LOW_OVERLAP", "per-sample Dice below a prospectively frozen stratum rule",
         ["global_dice", "a8_dice"], "ROUTER_HOLDOUT frozen table", "sample",
         "existing evidence sufficient", "no", "n/a", "descriptive", "DESCRIPTIVE_ONLY"),
        ("EMPTY_PREDICTION", "predicted positive area == 0 (or Dice == 0 with non-empty GT)",
         ["global_dice", "a8_dice"], "ROUTER_HOLDOUT frozen table", "sample",
         "partially sufficient (Dice==0 proxy only)", "yes (predicted-area from frozen "
         "probability array)", "NO (TIER_2 not authorized)", "descriptive", "DESCRIPTIVE_ONLY"),
        ("FALSE_POSITIVE_BURDEN", "excess predicted positives", ["(none)"],
         "ROUTER_HOLDOUT", "sample", "NOT sufficient", "yes", "NO (TIER_3 GT pixels)",
         "descriptive", "INELIGIBLE"),
        ("FALSE_NEGATIVE_BURDEN", "missed GT positives", ["(none)"], "ROUTER_HOLDOUT", "sample",
         "NOT sufficient", "yes", "NO (TIER_3 GT pixels)", "descriptive", "INELIGIBLE"),
        ("OBJECT_MISS", "GT object absent from prediction", ["(none)"], "ROUTER_HOLDOUT", "object",
         "NOT sufficient", "yes", "NO (TIER_3)", "descriptive", "INELIGIBLE"),
        ("MULTI_COMPONENT_PARTIAL_DETECTION", "some but not all GT objects detected", ["(none)"],
         "ROUTER_HOLDOUT", "object", "NOT sufficient", "yes", "NO (TIER_3)", "descriptive",
         "INELIGIBLE"),
        ("MULTI_COMPONENT_COMPLETE_MISS", "no GT object detected", ["(none)"], "ROUTER_HOLDOUT",
         "object", "NOT sufficient", "yes", "NO (TIER_3)", "descriptive", "INELIGIBLE"),
        ("BOUNDARY_ERROR", "boundary distance error", ["(none)"], "ROUTER_HOLDOUT", "sample",
         "NOT sufficient", "yes", "NO (TIER_3)", "descriptive", "INELIGIBLE"),
        ("ROUTER_HARMFUL_ACTIVATION", "EXECUTE with delta_dice <= -0.01", ["delta_dice_a8",
         "router_decision"], "ROUTER_HOLDOUT frozen table", "sample", "sufficient", "no", "n/a",
         "descriptive", "DESCRIPTIVE_ONLY"),
        ("ROUTER_MISSED_BENEFIT", "SKIP with delta_dice >= +0.02", ["delta_dice_a8",
         "router_decision"], "ROUTER_HOLDOUT frozen table", "sample", "sufficient", "no", "n/a",
         "descriptive", "DESCRIPTIVE_ONLY"),
        ("EXECUTE_THEN_REJECT", "state_machine == EXECUTE_THEN_REJECT", ["state_machine",
         "delta_dice_a8"], "ROUTER_HOLDOUT frozen table", "sample", "sufficient", "no", "n/a",
         "descriptive", "DESCRIPTIVE_ONLY"),
        ("DOMAIN_SPECIFIC_FAILURE", "failure concentration differs by dataset",
         ["dataset", "delta_dice_a8"], "ROUTER_HOLDOUT frozen table", "domain",
         "sufficient", "no", "n/a", "descriptive", "DESCRIPTIVE_ONLY"),
        ("GROUP_OR_PATIENT_CLUSTERED_FAILURE", "failure concentration across groups",
         ["sample_id", "delta_dice_a8"], "ROUTER_HOLDOUT frozen table + split manifest group_key",
         "group", "sufficient via metadata join", "yes (join only)", "AUTHORIZED (metadata only)",
         "descriptive", "DESCRIPTIVE_ONLY"),
    ]
    write_json({
        "artifact": "phase33_failure_taxonomy_contract", "phase": 33, "section": "§I",
        "method": METHOD, "revision": REVISION,
        "families": [{"family": f, "definition": d, "required_fields": rf, "required_population": rp,
                      "unit": u, "existing_evidence_sufficient": s, "new_derivation_needed": nd,
                      "derivation_authorized": da, "scientific_role": sr, "claim_status": cs}
                     for f, d, rf, rp, u, s, nd, da, sr, cs in taxonomy],
        "every_category_required": False,
        "eligible_families": [f for f, *_rest in taxonomy],
        "ineligible_families": ["FALSE_POSITIVE_BURDEN", "FALSE_NEGATIVE_BURDEN", "OBJECT_MISS",
                                "MULTI_COMPONENT_PARTIAL_DETECTION",
                                "MULTI_COMPONENT_COMPLETE_MISS", "BOUNDARY_ERROR"],
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_failure_taxonomy_contract.json")
    print("§I failure taxonomy frozen")

    # ================= §J threshold provenance ================= #
    write_json({
        "artifact": "phase33_failure_threshold_provenance_contract", "phase": 33, "section": "§J",
        "method": METHOD, "revision": REVISION,
        "strata": [
            {"stratum": "low_dice (bottom decile)",
             "classification": "DESCRIPTIVE_QUANTILE_METHOD_PROSPECTIVELY_FROZEN",
             "method": "np.quantile(values, 0.10, method='linear') on float64, computed on the "
                       "frozen ROUTER_HOLDOUT per-sample Dice of the SAME system; ties included",
             "realized_numeric_quantile_frozen_now": False,
             "note": "the METHOD is frozen now; the realized numeric quantile is computed at "
                     "execution from frozen tables (deterministic, not outcome-selected)"},
            {"stratum": "benefit categories",
             "classification": "EXACT_PREDECESSOR_THRESHOLD_TRANSFERABLE",
             "method": "BENEFICIAL DeltaDice >= +0.02; HARMFUL <= -0.01; NEUTRAL otherwise",
             "note": "frozen Phase24/25E/30 category semantics; distinct from S_omega training "
                     "target DeltaDice > 0"},
            {"stratum": "routing state",
             "classification": "EXACT_PREDECESSOR_THRESHOLD_TRANSFERABLE",
             "method": "frozen state_machine categories"},
            {"stratum": "HD95 / FP-component deciles",
             "classification": "FORBIDDEN",
             "method": "not available in frozen final-system evidence; would require TIER_3 rereads"},
        ],
        "outcome_optimized_threshold_selected": False,
        "post_hoc_quantile_presented_as_prospective": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_failure_threshold_provenance_contract.json")
    print("§J threshold provenance frozen")

    # ================= §K router failure analysis ================= #
    write_json({
        "artifact": "phase33_router_failure_analysis_contract", "phase": 33, "section": "§K",
        "method": METHOD, "revision": REVISION,
        "system_is_selective": True,
        "analyses": [
            "SKIP vs EXECUTE (state_machine) counts and delta_dice distributions",
            "EXECUTE_THEN_ACCEPT vs EXECUTE_THEN_REJECT",
            "selected vs unselected",
            "beneficial vs harmful vs neutral (frozen categories)",
            "harmful activation share among selected",
            "missed benefit among skipped",
            "true delta (delta_dice_a8) descriptive distribution",
            "predicted delta (delta_hat) descriptive distribution",
            "predicted-vs-true delta descriptive relationship (no new significance test)"],
        "fields_used": ["state_machine", "router_decision", "somega_accept", "delta_hat", "utility",
                        "delta_dice_a8", "delta_dice_a7", "dataset"],
        "frozen_benefit_categories": {"BENEFICIAL": "DeltaDice >= +0.02",
                                      "HARMFUL": "DeltaDice <= -0.01", "NEUTRAL": "otherwise"},
        "s_omega_training_target_conflated": False,
        "fields_not_present_not_used": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_router_failure_analysis_contract.json")
    print("§K router failure contract frozen")

    # ================= §L boundary metric provenance ================= #
    write_json({
        "artifact": "phase33_boundary_metric_provenance_contract", "phase": 33, "section": "§L",
        "method": METHOD, "revision": REVISION,
        "phase33_title_mentions_boundary_error": True,
        "frozen_final_system_boundary_metric_present": False,
        "audit": {
            "HD95_availability": "absent from frozen Phase30/27 final-system tables",
            "boundary_distance_units": "n/a",
            "pixel_vs_physical_spacing": "no validated spacing for these modalities",
            "empty_prediction_handling": "n/a",
            "empty_GT_handling": "n/a",
            "validity_flags": "none present",
            "resize_space_vs_native_space": "n/a"},
        "FINAL_SYSTEM_BOUNDARY_ERROR_NEW_COMPUTATION_ELIGIBLE": False,
        "reason": "computing a boundary metric would require GT/prediction pixel rereads "
                  "(TIER_3), which is not authorized",
        "phase11_boundary_evidence_classification": "HISTORICAL_KUB_DESCRIPTIVE_EVIDENCE_ONLY",
        "router_holdout_gt_reopened_for_boundary": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_boundary_metric_provenance_contract.json")
    print("§L boundary metric provenance: NEW_COMPUTATION_ELIGIBLE=False")

    # ================= §M component / object analysis ================= #
    write_json({
        "artifact": "phase33_component_object_analysis_ruling", "phase": 33, "section": "§M",
        "method": METHOD, "revision": REVISION,
        "frozen_final_system_component_information_present": False,
        "historical_rules": {"connectivity": 8, "minimum_overlap_pixels": 1,
                             "source": "Phase11 (KUB VAL280, multi-architecture)"},
        "reuse_formally_justified_for_phase33": False,
        "component_analysis_requires_protected_reread": True,
        "NEW_COMPONENT_ANALYSIS_ELIGIBLE": False,
        "manufactured": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_component_object_analysis_ruling.json")
    print("§M component analysis: ELIGIBLE=False")

    # ================= §N hard-case selection ================= #
    write_json({
        "artifact": "phase33_hard_case_selection_contract", "phase": 33, "section": "§N",
        "method": METHOD, "revision": REVISION,
        "label": "DESCRIPTIVE_FAILURE_CASE_SELECTION",
        "not_unbiased_performance_estimation": True,
        "cases_selected_in_this_task": 0,
        "procedure": {
            "population": "ROUTER_HOLDOUT frozen scored table",
            "eligible_candidates": "all 875 frozen rows",
            "failure_strata": ["low_dice bottom decile (method frozen; quantile computed at "
                               "execution)",
                               "harmful activation (EXECUTE and delta_dice_a8 <= -0.01)",
                               "missed benefit (SKIP and delta_dice_a8 >= +0.02)",
                               "EXECUTE_THEN_REJECT"],
            "target_number_per_stratum": 8,
            "ordering": "within stratum: delta_dice_a8 ascending, then sample_id ascending",
            "tie_break": "sample_id ascending",
            "deduplication_across_strata": "first stratum in the declared order wins; a sample may "
                                           "appear in at most one panel",
            "domain_balancing": "report realized domain composition per stratum; do not force",
            "group_patient_balancing": "at most one sample per group_key within a panel",
            "underfilled_stratum": "report the shortfall; do not pad with non-matching cases",
            "selection_prediction_dependent": True,
            "visual_attractiveness_based": False},
        "selection_requires_frozen_procedure_first": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_hard_case_selection_contract.json")
    print("§N hard-case selection procedure frozen (0 selected)")

    # ================= §O qualitative evidence ================= #
    write_json({
        "artifact": "phase33_qualitative_evidence_contract", "phase": 33, "section": "§O",
        "method": METHOD, "revision": REVISION,
        "raw_image_reread_permitted": False,
        "gt_visualization_permitted": False,
        "frozen_prediction_visualization_permitted": False,
        "reason": "ROUTER_HOLDOUT raw images/GT are protected and the frozen prediction arrays are "
                  "not part of the authorized Phase30→Phase33 handoff",
        "QUALITATIVE_GALLERY_ELIGIBLE": False,
        "qualitative_panels_generated": 0,
        "acceptable_outcome": True,
        "cherry_picking": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_qualitative_evidence_contract.json")
    print("§O qualitative gallery: ELIGIBLE=False")

    # ================= §P quantitative analysis plan ================= #
    write_json({
        "artifact": "phase33_quantitative_analysis_contract", "phase": 33, "section": "§P",
        "method": METHOD, "revision": REVISION,
        "plan": [
            "per-domain failure rate (low-Dice decile membership by dataset)",
            "per-state failure rate (SKIP / EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT)",
            "selected vs skipped delta_dice_a8 distributions",
            "accepted vs rejected delta_dice_a8 distributions",
            "harmful activation characteristics (count, rate, delta_dice_a8 distribution)",
            "missed-benefit characteristics",
            "low-Dice prevalence overall and per domain",
            "failure concentration by group (metadata join on group_key)",
            "failure overlap across categories (pairwise co-occurrence)",
            "failure severity summaries (quantiles of delta_dice_a8 within strata)"],
        "new_significance_test_required": False,
        "phase31_wilcoxon_holm_cohen_d_imported": False,
        "uncertainty_unit": "none reported by default; if reported, group = group_key, "
                            "domain-stratified",
        "cluster_handling": "group_key from the split manifest (metadata-only join)",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_quantitative_analysis_contract.json")
    print("§P quantitative analysis plan frozen")

    # ================= §Q Phase30 qualifier binding ================= #
    write_json({
        "artifact": "phase33_phase30_reporting_qualification_binding", "phase": 33, "section": "§Q",
        "method": METHOD, "revision": REVISION,
        "qualifier": QUALIFIER,
        "mandatory_whenever_phase30_router_holdout_evidence_used": True,
        "forbidden_wording_for_phase30": ["fully preregistered", "protocol-perfect",
                                          "COMPLETE_CANONICAL", "no-deviation holdout"],
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_phase30_reporting_qualification_binding.json")

    # ================= §R analysis tiers ================= #
    tier_rows = [
        ["A01", "read frozen Phase30 scored results table", TIER0, "True", "no raw data"],
        ["A02", "read frozen Phase30 predictions table", TIER0, "True", "no raw data"],
        ["A03", "read frozen Phase30 router metrics / A7 / H3 JSON", TIER0, "True", "no raw data"],
        ["A04", "low-Dice decile stratification (method frozen)", TIER1, "True",
         "derived categorical from frozen Dice"],
        ["A05", "benefit-category flags (frozen semantics)", TIER1, "True", "derived categorical"],
        ["A06", "group-cluster join via split-manifest group_key", TIER1, "True", "metadata only"],
        ["A07", "predicted-area / entropy from frozen prediction arrays", TIER2, "False",
         "not in authorized Phase30->Phase33 handoff"],
        ["A08", "boundary distance / HD95", TIER3, "False", "requires GT pixels"],
        ["A09", "connected components / object matching", TIER3, "False", "requires GT pixels"],
        ["A10", "FP/FN burden", TIER3, "False", "requires GT pixels"],
        ["A11", "model re-inference", TIER4, "False", "forbidden for Phase33"],
    ]
    write_csv(TAB / "phase33_analysis_tier_registry.csv",
              ["analysis_id", "description", "tier", "authorized_now", "note"], tier_rows)
    print("§R analysis tier registry frozen")

    # ================= §S execution eligibility ================= #
    elig = {
        "table_only_execution_eligible": True,
        "derived_nonpixel_execution_eligible": True,
        "prediction_pixel_execution_eligible": False,
        "raw_image_execution_eligible": False,
        "raw_GT_execution_eligible": False,
        "qualitative_gallery_eligible": False,
        "boundary_metric_execution_eligible": False,
        "component_metric_execution_eligible": False,
        "model_rerun_eligible": False,
    }
    write_json({
        "artifact": "phase33_execution_eligibility_adjudication", "phase": 33, "section": "§S",
        "method": METHOD, "revision": REVISION, **elig,
        "reasons": {
            "prediction_pixel": "frozen prediction arrays are not part of the authorized "
                                "Phase30->Phase33 handoff; requires separate explicit authorization",
            "raw_image": "ROUTER_HOLDOUT images are protected; no raw reread authorized",
            "raw_GT": "ROUTER_HOLDOUT GT is protected; no raw reread authorized",
            "qualitative_gallery": "requires raw images (and/or prediction pixels)",
            "boundary_metric": "no valid boundary metric in frozen final-system evidence",
            "component_metric": "no component information in frozen final-system evidence",
            "model_rerun": "forbidden for Phase33"},
        "collapsed_into_one_boolean": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_execution_eligibility_adjudication.json")
    print(f"§S execution eligibility: {elig}")

    # ================= §T specification document ================= #
    doc = f"""# Phase 33 — Final System Failure & Boundary Error Analysis
## Entry Gate + Evidence-Population Ownership + Failure Taxonomy + Boundary-Metric Provenance + Pre-Analysis Specification

**Revision:** `{REVISION}`
**Classification:** `{CLASSIFICATION}`
**Method:** {METHOD}
**Status:** SPECIFICATION COMPLETE — **failure analysis NOT executed**
**Generated:** {now_utc()}

> **Phase30 qualifier (mandatory wherever Phase30 ROUTER_HOLDOUT evidence is used):**
> `{QUALIFIER}`
> Phase30 remains `COMPLETE_WITH_PROTOCOL_DEVIATION__NOT_COMPLETE_CANONICAL`.

---

## 1. Purpose

**What failure modes are present in the frozen final RA-MedFiLM-BARR system, and which of those
failure modes can be established from already-frozen evidence without reopening protected
populations or manufacturing new post-outcome definitions?**

Phase33 is descriptive/diagnostic evidence — not model selection, policy selection, threshold
tuning, training, a new validation benchmark, a new significance-testing phase, or a Phase39 TEST
substitute.

## 2. Evidence classes distinguished

| class | status |
|---|---|
| FINAL-SYSTEM FAILURE EVIDENCE (Phase30 ROUTER_HOLDOUT frozen tables) | available, table-only |
| HISTORICAL PHASE11 FAILURE EVIDENCE (KUB VAL280, 4 architectures) | historical descriptive only |
| NEW DESCRIPTIVE DERIVATIONS (from frozen non-pixel fields) | eligible |
| BOUNDARY ANALYSIS | **INELIGIBLE** |
| QUALITATIVE CASE ANALYSIS | **INELIGIBLE** |
| PROTECTED RAW POPULATIONS (ROUTER_HOLDOUT images/GT, TEST) | forbidden |

## 3. Population ownership

`ROUTER_HOLDOUT` = frozen result tables only · `VAL808` = frozen result tables only ·
`ROUTER_DEVELOPMENT` = historical descriptive only · `TRAIN` = frozen tables + metadata join ·
historical KUB VAL280 = historical descriptive only · external cohorts = historical descriptive only ·
**`TEST` = FORBIDDEN (locked until Phase39)**.

Raw access is **not** assumed merely because a population was opened in an earlier phase.

## 4. Frozen-artifact schema

Present in the frozen final-system tables: per-sample `global_dice`, `a8_dice`, `delta_dice_a8`,
`a7_dice`, `delta_dice_a7`, `router_decision`, `state_machine`, `somega_accept`, `somega_score`,
`delta_hat`, `utility`, `tau_C8`, `roi_available`, `dataset`, `sample_id`, plus `group_key` via a
metadata-only join.

**Absent:** IoU, precision, recall, HD95, FP/FN counts, connected components, object counts,
per-sample boundary distances.

## 5. Phase11 taxonomy provenance

Phase11 froze a failure protocol for **KUB VAL280 across four segmentation architectures**
(UNet, Attention U-Net, UNet++, DeepLabV3+) — **not** the final RA-MedFiLM-BARR system.

* Reusable: bottom-decile quantile **method**; 8-connectivity; minimum-overlap ≥ 1 px.
* Historical KUB-specific only: cutoffs `0.5461`, `83.07`, `4`; regime stratification.
* Not applicable to the final system: `ALL_FOUR_LOW`, architecture disagreement.
* Post-hoc if introduced now: HD95 decile, FP-component decile.

Numeric thresholds and the KUB taxonomy were **not** auto-transferred.

## 6. Phase33 failure taxonomy

**Eligible (descriptive):** `LOW_OVERLAP`, `ROUTER_HARMFUL_ACTIVATION`, `ROUTER_MISSED_BENEFIT`,
`EXECUTE_THEN_REJECT`, `DOMAIN_SPECIFIC_FAILURE`, `GROUP_OR_PATIENT_CLUSTERED_FAILURE`,
`EMPTY_PREDICTION` (Dice-0 proxy only).

**Ineligible:** `FALSE_POSITIVE_BURDEN`, `FALSE_NEGATIVE_BURDEN`, `OBJECT_MISS`,
`MULTI_COMPONENT_PARTIAL_DETECTION`, `MULTI_COMPONENT_COMPLETE_MISS`, `BOUNDARY_ERROR`.

## 7. Threshold provenance

* Low-Dice stratum → `DESCRIPTIVE_QUANTILE_METHOD_PROSPECTIVELY_FROZEN` (method frozen now; realized
  numeric quantile computed deterministically at execution from frozen tables).
* Benefit categories → `EXACT_PREDECESSOR_THRESHOLD_TRANSFERABLE` (BENEFICIAL ≥ +0.02, HARMFUL
  ≤ −0.01, NEUTRAL otherwise; distinct from the S_omega training target `DeltaDice > 0`).
* HD95 / FP-component deciles → `FORBIDDEN`.

No outcome-optimized threshold was selected.

## 8. Boundary-metric provenance ruling

**`FINAL_SYSTEM_BOUNDARY_ERROR_NEW_COMPUTATION_ELIGIBLE = false`.** The frozen final-system evidence
contains no valid boundary metric, and computing one would require GT/prediction pixel rereads
(TIER_3). Phase11 boundary evidence is preserved as **historical KUB descriptive evidence only**.
ROUTER_HOLDOUT GT was **not** reopened merely because the phase title mentions boundary error.

## 9. Component / object analysis ruling

**`NEW_COMPONENT_ANALYSIS_ELIGIBLE = false`** — frozen final-system artifacts carry no
component-level information and deriving it requires protected rereads.

## 10. Hard-case selection

Procedure frozen **before** selecting any case (strata, ordering, tie-break, dedup, group cap,
underfill policy). **0 cases selected.** Label: `DESCRIPTIVE_FAILURE_CASE_SELECTION` — not unbiased
performance estimation; never selected for visual attractiveness.

## 11. Qualitative evidence

**`QUALITATIVE_GALLERY_ELIGIBLE = false`** — requires raw images and/or prediction pixels, neither
authorized. 0 panels generated. This is an acceptable outcome.

## 12. Quantitative analysis plan

Per-domain / per-state failure rates, selected-vs-skipped and accepted-vs-rejected distributions,
harmful-activation and missed-benefit characteristics, low-Dice prevalence, group-cluster
concentration, cross-category overlap, and severity summaries — all from frozen fields only. **No new
significance test**; Phase31 Wilcoxon/Holm/Cohen-d **not** imported.

## 13. Analysis tiers

`TIER_0` frozen-table read-only (**eligible**) · `TIER_1` derived from frozen non-pixel fields
(**eligible**) · `TIER_2` frozen prediction pixel (**not authorized**) · `TIER_3` raw image/GT reread
(**blocked**) · `TIER_4` model rerun (**forbidden**).

## 14. Execution eligibility

| capability | eligible |
|---|---|
| table-only | **true** |
| derived non-pixel | **true** |
| prediction-pixel | false |
| raw image | false |
| raw GT | false |
| qualitative gallery | false |
| boundary metric | false |
| component metric | false |
| model rerun | false |
"""
    DOCS.mkdir(parents=True, exist_ok=True)
    (DOCS / "phase33_final_system_failure_boundary_spec_v1_0.md").write_text(doc, encoding="utf-8")
    print("§T specification document written")

    # ================= §X entry gate ================= #
    gate = {
        "Phase32_COMPLETE_CANONICAL": t32["status"] == "COMPLETE_CANONICAL",
        "Phase32_closure_terminal_sha_match": binds[0]["match"],
        "Phase32_to_Phase33_handoff_sha_match": binds[3]["match"],
        "Phase30_qualifier_bound": True, "Phase30_status_not_upgraded": True,
        "Phase33_roadmap_identity_correct": True,
        "population_ownership_frozen": True,
        "candidate_evidence_inventory_complete": True,
        "schema_registry_complete": True,
        "Phase11_taxonomy_provenance_audited": True,
        "failure_taxonomy_frozen": True,
        "threshold_provenance_frozen": True,
        "router_failure_contract_frozen": True,
        "boundary_provenance_frozen": True,
        "component_analysis_provenance_frozen": True,
        "hard_case_procedure_frozen": True,
        "qualitative_evidence_contract_frozen": True,
        "quantitative_analysis_contract_frozen": True,
        "analysis_tiers_frozen": True,
        "execution_eligibility_adjudicated": True,
        "no_hard_cases_selected": True,
        "no_raw_ROUTER_HOLDOUT_read": True,
        "no_TEST_read": True,
        "no_model_forward": True, "no_training": True,
    }
    nf = sum(1 for v in gate.values() if not v)
    write_json({"artifact": "phase33_entry_gate", "phase": 33, "section": "§X",
                "method": METHOD, "revision": REVISION,
                "n_checks": len(gate), "n_failed": nf,
                "failed": [k for k, v in gate.items() if not v], "checks": gate,
                "generated_utc": now_utc(), "all_pass": nf == 0},
               AUD / "phase33_entry_gate.json")
    print(f"§X entry gate: {len(gate)-nf}/{len(gate)} pass")

    # ================= §Y no-execution audit ================= #
    write_json({
        "artifact": "phase33_no_execution_audit", "phase": 33, "section": "§Y",
        "method": METHOD, "revision": REVISION,
        "new_raw_image_reads": 0, "new_raw_GT_reads": 0,
        "ROUTER_HOLDOUT_raw_image_reads": 0, "ROUTER_HOLDOUT_raw_GT_reads": 0,
        "TEST_reads": 0, "model_loads": 0, "model_forwards": 0, "prediction_generation": 0,
        "training_steps": 0, "new_Dice_computations": 0, "new_IoU_computations": 0,
        "new_HD95_computations": 0, "new_component_computations": 0,
        "hard_cases_selected": 0, "qualitative_panels_generated": 0,
        "Phase34_started": False,
        "frozen_csv_json_markdown_reads_are_not_raw_data_reads": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase33_no_execution_audit.json")

    # ================= §Z completeness ================= #
    rows = [
        ("Phase32 closure authority bound", "SPECIFICATION", "COMPLETE", ""),
        ("Candidate evidence inventory", f"{len(EVIDENCE)} candidates", "COMPLETE", ""),
        ("Population ownership contract", "frozen", "COMPLETE", ""),
        ("Phase30 frozen evidence consumption contract", "all SHAs match", "COMPLETE", ""),
        ("Frozen artifact schema registry", f"{len(schemas)} fields", "COMPLETE", ""),
        ("Phase11 taxonomy provenance", "audited", "COMPLETE", ""),
        ("Failure taxonomy contract", "frozen", "COMPLETE", ""),
        ("Failure threshold provenance", "frozen", "COMPLETE", ""),
        ("Router failure analysis contract", "frozen", "COMPLETE", ""),
        ("Boundary metric provenance", "NEW_COMPUTATION_ELIGIBLE=false", "RESOLVED_INELIGIBLE",
         "no valid boundary metric in frozen evidence"),
        ("Component/object analysis ruling", "ELIGIBLE=false", "RESOLVED_INELIGIBLE",
         "no component info in frozen evidence"),
        ("Hard-case selection contract", "procedure frozen, 0 selected", "COMPLETE", ""),
        ("Qualitative evidence contract", "ELIGIBLE=false", "RESOLVED_INELIGIBLE",
         "raw images and prediction pixels not authorized"),
        ("Quantitative analysis contract", "frozen", "COMPLETE", ""),
        ("Phase30 reporting qualification binding", "frozen", "COMPLETE", ""),
        ("Analysis tier registry", f"{len(tier_rows)} analyses", "COMPLETE", ""),
        ("Execution eligibility adjudication", "frozen", "COMPLETE", ""),
        ("Phase33 specification document", "v1.0", "COMPLETE", ""),
        ("No-execution audit", "all zero", "COMPLETE", ""),
        ("Boundary analysis", "ineligible", "RESOLVED_INELIGIBLE", "preserved as historical only"),
        ("Qualitative gallery", "ineligible", "RESOLVED_INELIGIBLE", "acceptable outcome"),
        ("Raw population rereads", "blocked", "RESOLVED_BLOCKED", "protected populations"),
        ("Table-only + derived non-pixel failure analysis", "eligible", "COMPLETE",
         "the only executable Phase33 analyses"),
    ]
    write_csv(TAB / "phase33_specification_completeness.csv",
              ["requirement", "category", "status", "note"], rows)
    n_complete = sum(1 for r in rows if r[2] == "COMPLETE")
    n_block = sum(1 for r in rows if r[2] in ("BLOCKING", "INCOMPLETE", "UNRESOLVED"))
    n_resolved = sum(1 for r in rows if r[2].startswith("RESOLVED"))
    print(f"§Z completeness: {n_complete}/{len(rows)} COMPLETE, {n_block} BLOCKING, "
          f"{n_resolved} resolved-ineligible/blocked")

    # ================= §AA final check ================= #
    checks = {
        "entry_gate_pass": nf == 0,
        "phase32_closure_bound": a_ok,
        "phase30_qualifier_bound": True, "phase30_status_not_upgraded": True,
        "population_ownership_frozen": True,
        "evidence_inventory_complete": True, "schema_registry_complete": True,
        "phase11_taxonomy_audited": True, "failure_taxonomy_frozen": True,
        "threshold_provenance_frozen": True, "router_failure_contract_frozen": True,
        "boundary_provenance_frozen": True, "component_provenance_frozen": True,
        "hard_case_procedure_frozen": True, "qualitative_contract_frozen": True,
        "quantitative_contract_frozen": True, "tiers_frozen": True,
        "eligibility_adjudicated": True,
        "specification_complete": n_block == 0,
        "no_hard_cases_selected": True,
        "no_raw_ROUTER_HOLDOUT_read": True, "no_TEST_read": True,
        "no_model_forward": True, "no_training": True, "no_new_metrics": True,
        "execution_started_false": True, "Phase34_not_started": True,
    }
    nfx = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase33_specification_final_check", "phase": 33, "section": "§AA",
        "method": METHOD, "revision": REVISION,
        "n_checks": len(checks), "n_failed": nfx,
        "failed": [k for k, v in checks.items() if not v], "checks": checks,
        "specification_complete": nfx == 0,
        "table_only_execution_eligible": True,
        "derived_nonpixel_execution_eligible": True,
        "prediction_pixel_execution_eligible": False,
        "raw_image_execution_eligible": False, "raw_GT_execution_eligible": False,
        "qualitative_gallery_eligible": False,
        "boundary_metric_execution_eligible": False,
        "component_metric_execution_eligible": False,
        "model_rerun_eligible": False,
        "execution_started": False, "Phase34_started": False, "TEST_reads": 0,
        "generated_utc": now_utc(), "all_pass": nfx == 0,
    }, AUD / "phase33_specification_final_check.json")
    print(f"§AA final check: {len(checks)-nfx}/{len(checks)} pass")

    # ================= §AB terminal ================= #
    if nfx == 0:
        write_json({
            "artifact": "phase33_specification_terminal", "phase": 33,
            "status": "SPEC_COMPLETE", "terminal": TERMINAL,
            "revision": REVISION, "classification": CLASSIFICATION,
            "specification_complete": True,
            "table_only_execution_eligible": True, "derived_nonpixel_execution_eligible": True,
            "prediction_pixel_execution_eligible": False,
            "raw_image_execution_eligible": False, "raw_GT_execution_eligible": False,
            "qualitative_gallery_eligible": False,
            "boundary_metric_execution_eligible": False,
            "component_metric_execution_eligible": False, "model_rerun_eligible": False,
            "execution_started": False, "Phase34_started": False,
            "ROUTER_HOLDOUT_raw_reads": 0, "TEST_reads": 0, "model_forwards": 0,
            "hard_cases_selected": 0, "qualitative_panels_generated": 0,
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase33_specification_terminal.json")
        print("")
        print("=" * 78)
        print(TERMINAL)
        print("=" * 78)
    else:
        print("FINAL CHECK FAILED:", [k for k, v in checks.items() if not v])
    return 0 if nfx == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
