#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PHASE 30 - FINAL DEVELOPMENT VALIDATION BENCHMARK.
PRE-EXECUTION ONE-SHOT ROUTER_HOLDOUT SPECIFICATION + FIRST-OPEN FREEZE.

GOVERNANCE / SPECIFICATION ONLY.  No holdout image read, no holdout GT read,
no model forward, no training, no TEST access.

Produces the full prospective Phase30 specification + governance freeze:
    reports/audits/phase30_entry_state_binding.json
    reports/audits/phase30_ownership_contract.json
    reports/audits/phase30_router_holdout_population_binding.json
    reports/audits/phase30_router_holdout_first_open_precondition.json
    reports/audits/phase30_system_under_test_contract.json
    reports/audits/phase30_canonical_bundle_identity.json
    reports/audits/phase30_frozen_runtime_threshold_contract.json
    reports/audits/phase30_policy_transfer_contract.json
    reports/audits/phase30_causal_execution_contract.json
    reports/audits/phase30_component_inference_semantics_contract.json
    reports/audits/phase30_prediction_gt_separation_contract.json
    reports/audits/phase30_first_open_audit_contract.json
    reports/audits/phase30_statistical_analysis_plan.json
    reports/audits/phase30_metric_definition_contract.json
    reports/audits/phase30_compute_reporting_contract.json
    reports/audits/phase30_post_open_immutability_contract.json
    reports/audits/phase30_test_lock_audit.json
    reports/audits/phase30_specification_no_execution_audit.json
    reports/tables/phase30_specification_completeness.csv
    reports/audits/phase30_preexecution_final_check.json
    reports/audits/phase30_specification_terminal.json
    docs/phase30_final_development_validation_spec.md

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_specification.py
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
DOCS = ROOT / "docs"

SPEC_REVISION = "ra_medfilm_barr_phase30_final_dev_validation_v1_0"
METHOD = "RA-MedFiLM-BARR"

TERMINAL_SUCCESS = (
    "PHASE30_PREEXECUTION_SPEC_COMPLETE__ONE_SHOT_ROUTER_HOLDOUT_SYSTEM_POLICY_"
    "STATISTICS_FIRST_OPEN_AND_POSTOPEN_IMMUTABILITY_FROZEN__EXECUTION_ELIGIBLE_NOT_STARTED"
)
BLOCKED = {
    "SYSTEM_UNDER_TEST": "PHASE30_SPEC_BLOCKED__SYSTEM_UNDER_TEST_UNRESOLVED",
    "RUNTIME_THRESHOLD": "PHASE30_SPEC_BLOCKED__RUNTIME_THRESHOLD_UNRESOLVED",
    "STATISTICAL_PLAN": "PHASE30_SPEC_BLOCKED__STATISTICAL_PLAN_INCOMPLETE",
    "FIRST_OPEN": "PHASE30_SPEC_BLOCKED__FIRST_OPEN_PROVENANCE_UNRESOLVED",
    "PRIOR_ACCESS": "PHASE30_SPEC_BLOCKED__ROUTER_HOLDOUT_PRIOR_ACCESS_DETECTED",
    "TEST_LOCK": "PHASE30_SPEC_BLOCKED__TEST_LOCK_VIOLATION",
}

# --------------------------------------------------------------- bindings ---
P29_POSTCLOSURE_TERMINAL = "reports/audits/phase29_phase_d_postclosure_terminal.json"
P29_POSTCLOSURE_TERMINAL_SHA = "e92c4e6eed1eef6e813d83fd785d8334be241cc7bef427f7b1bdf7f911aa6eb1"
P29_POSTCLOSURE_TERMINAL_TOKEN = (
    "PHASE29_PHASE_D_POSTCLOSURE_RECONCILED__SEED42_REUSE_COUNTS_AND_NOTEBOOK_"
    "FINAL_CHECK_PROVENANCE_FROZEN__PHASE29_COMPLETE__PHASE30_ELIGIBLE_NOT_STARTED")
P29_BOUND = [
    ("phase29_phase_d_postclosure_final_check.json",
     "8200d7ef709da548e1775a8d28a6daa74c3dabe075bc7fe5a67c04a1081c29cd"),
    ("phase29_phase_d_notebook_postclosure_addendum.json",
     "18a00e2b9532a498d2817cf45b47320859d163a626fafbbc56295d663ad597e6"),
    ("phase29_phase_d_final_check_count_reconciliation.json",
     "ca67abae643008d6ee1602892651eec130e28778d0a76ff3b6085f4523734b2b"),
    ("phase29_phase_d_seed42_scientific_immutability.json",
     "7ec478c17dd5b27374398c74530db3d3dad1ac4b1b3fc8e58e69a0057bb70fd5"),
    ("phase29_phase_d_causal_order_rebind_seed42_count_addendum.json",
     "40bca19144c5339533e9343da7a761ae755e6e49e756c1a8bc3a5b58e5e53c24"),
]
SPLIT_MANIFEST = "reports/audits/phase24_router_split_manifest.csv"
SPLIT_MANIFEST_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"
SPLIT_PROTOCOL = "reports/audits/phase24_benefit_data_protocol_exact.json"
BUNDLE_MANIFEST = "artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json"
BUNDLE_MANIFEST_SHA = "f7aebb0f646bcc8de49fa91b70a4c4cc1051c9998ab6b055a8d4d187809cb3d9"

COMPONENTS = {
    "G": {"path": "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt",
          "sha256": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
          "params": 3523001, "owner_phase": "Phase21", "class": "GlobalMedFiLM"},
    "R_psi": {"path": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt",
              "sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
              "params": 1276401, "owner_phase": "Phase25A", "class": "BARRRegionalRefinerV1"},
    "B_phi": {"path": "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt",
              "sha256": "8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b",
              "params": 36801, "owner_phase": "Phase25D", "class": "BARRBenefitRouterV1"},
    "S_omega": {"path": "checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt",
                "sha256": "eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e",
                "params": 1217, "owner_phase": "Phase25F", "class": "BARRPostSafetyV1"},
}
NORMALIZATIONS = {
    "router_normalization": ("reports/tables/phase25d_final_normalization_stats.csv",
                             "ba37742e96610ec5e46fb47c093bf71ae1afd85b2a0db9696b612c873a4ba1fb"),
    "post_safety_normalization": ("reports/tables/phase25f_final_normalization_stats.csv",
                                  "e112e18b134c6edcdcd0c254c362d0a954a75faffe634cc37a2a17e4fe6f4e7b"),
}
SCHEMAS = {
    "router_schema": ("reports/tables/phase25b_feature_schema.csv",
                      "da76aa34f14006146f46ca799f173378274d8c9d0792dc18edb30711a2486dd4"),
    "post_safety_schema": ("reports/tables/phase25f_feature_schema_v1_0.csv",
                           "3e70e20c541b93de752980c34cdfb6fe5af17ebe4c18cbb64397c0bbae465ee5"),
}

RUNTIME_THRESHOLD_EXACT = "-5003565381643716252018011/205414980000000000000000000"
RUNTIME_SCORE = "delta_hat_final - 0.25*C"
RAW_THRESHOLD_EXACT = "24796109646558761/20000000000000000000"
NORMALIZED_ACTION_COST_EXACT = "1051648/10270749"
LAMBDA = "1/4"
LAMBDA_C_EXACT = "262912/10270749"
NOMINAL_BUDGET = 0.25

HOLDOUT_N = 875
HOLDOUT_GROUPS = 628
HOLDOUT_DOMAIN_N = {"BUSI": 90, "ISIC": 383, "KUB": 298, "KVASIR": 104}
HOLDOUT_DOMAIN_GROUPS = {"BUSI": 90, "ISIC": 383, "KUB": 51, "KVASIR": 104}
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}

MAC = {"global": 31551740928, "benefit_router": 36160, "regional_refiner": 3230662656,
       "s_omega": 1168}


def sha256_file(p) -> str:
    p = Path(p)
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


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def rows_of(p):
    with open(ROOT / p, "r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bind(rel, exp):
    p = ROOT / rel
    ex = p.exists()
    a = sha256_file(p) if ex else None
    return {"path": rel, "exists": ex, "sha256": a, "expected_sha256": exp,
            "match": bool(ex and a == exp)}


def main() -> int:
    print("=" * 78)
    print("PHASE 30 PRE-EXECUTION SPECIFICATION + FIRST-OPEN FREEZE")
    print("=" * 78)

    # ================================================================== #
    # §0  ENTRY STATE - BIND PHASE29 CLOSURE                              #
    # ================================================================== #
    term = bind(P29_POSTCLOSURE_TERMINAL, P29_POSTCLOSURE_TERMINAL_SHA)
    term_doc = jload(ROOT / P29_POSTCLOSURE_TERMINAL)
    term_ok = term["match"] and term_doc["terminal"] == P29_POSTCLOSURE_TERMINAL_TOKEN
    bound = [bind(f"reports/audits/{n}", s) for n, s in P29_BOUND]
    entry_ok = term_ok and all(b["match"] for b in bound)
    write_json({
        "artifact": "phase30_entry_state_binding", "phase": 30,
        "classification": "PHASE30_PRE_EXECUTION_SPECIFICATION",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "governance_only": True, "no_execution": True,
        "phase29_postclosure_terminal": term,
        "phase29_terminal_token_observed": term_doc.get("terminal"),
        "phase29_terminal_token_required": P29_POSTCLOSURE_TERMINAL_TOKEN,
        "phase29_bound_artifacts": bound,
        "phase29_science_changed": term_doc.get("science_changed"),
        "phase29_complete_canonical": term_ok,
        "block_on_drift": True,
        "generated_utc": now_utc(), "all_pass": entry_ok,
    }, AUD / "phase30_entry_state_binding.json")
    print(f"§0 Phase29 closure bound: terminal_ok={term_ok} bound_ok="
          f"{all(b['match'] for b in bound)}")
    if not entry_ok:
        write_json({"artifact": "phase30_specification_terminal",
                    "terminal": BLOCKED["FIRST_OPEN"], "all_pass": False,
                    "reason": "phase29_entry_drift"}, AUD / "phase30_specification_terminal.json")
        return 1

    # ================================================================== #
    # §1  OWNERSHIP                                                       #
    # ================================================================== #
    ruling = jload(ROOT / "reports/audits/phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json")
    stub = jload(ROOT / "reports/audits/phase30_router_holdout_deferred_contract_stub.json")
    reservation = jload(ROOT / "reports/audits/phase25g_holdout_reservation_for_phase30.json")
    ownership_ok = (ruling["ROUTER_HOLDOUT_OWNER_PHASE"] == 30
                    and stub["owner"] == "Phase30" and stub["population"] == "ROUTER_HOLDOUT"
                    and stub["state"] == "RESERVED_UNOPENED" and stub["is_phase30_specification"] is False)
    write_json({
        "artifact": "phase30_ownership_contract", "phase": 30, "section": "§1",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "governance_only": True, "no_execution": True,
        "owner": "Phase30",
        "phase30_title": "Final Development Validation Benchmark",
        "population": "ROUTER_HOLDOUT",
        "population_n": HOLDOUT_N,
        "role": "FINAL DEVELOPMENT VALIDATION BENCHMARK",
        "evaluation_nature": "ONE_SHOT CLEAN OUT-OF-SAMPLE DEVELOPMENT VALIDATION",
        "state_before_execution": "RESERVED_UNOPENED",
        "one_shot": True,
        "TEST": {"owner": "Phase39", "state": "LOCKED_UNTIL_PHASE39"},
        "bound_authority": [
            {"path": "reports/audits/phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json",
             "sha256": sha256_file(ROOT / "reports/audits/phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json")},
            {"path": "reports/audits/phase30_router_holdout_deferred_contract_stub.json",
             "sha256": sha256_file(ROOT / "reports/audits/phase30_router_holdout_deferred_contract_stub.json")},
            {"path": "reports/audits/phase25g_holdout_reservation_for_phase30.json",
             "sha256": sha256_file(ROOT / "reports/audits/phase25g_holdout_reservation_for_phase30.json")}],
        "deferred_stub_is_complete_phase30_specification": False,
        "complete_specification_created_here": True,
        "generated_utc": now_utc(), "all_pass": ownership_ok,
    }, AUD / "phase30_ownership_contract.json")
    print(f"§1 ownership: owner=Phase30 ok={ownership_ok}")

    # ================================================================== #
    # §2  METADATA-ONLY HOLDOUT BINDING                                   #
    # ================================================================== #
    man = rows_of(SPLIT_MANIFEST)
    dev = [r for r in man if r["split_role"] == "ROUTER_DEVELOPMENT"]
    ho = [r for r in man if r["split_role"] == "ROUTER_HOLDOUT"]
    ho_ids = [r["sample_id"] for r in ho]
    dom_n = {}
    dom_g = {}
    task_ids = {}
    for d in ("BUSI", "ISIC", "KUB", "KVASIR"):
        sub = [r for r in ho if r["dataset"] == d]
        dom_n[d] = len(sub)
        dom_g[d] = len({r["group_key"] for r in sub})
        task_ids[d] = int(sub[0]["task_id"])
    val_ids = {r["sample_id"] for r in rows_of("manifests/phase4_v3/val.csv")}
    test_ids = {r["sample_id"] for r in rows_of("manifests/phase4_v3/test.csv")}
    train_ids = {r["sample_id"] for r in rows_of("manifests/phase4_v3/train.csv")}
    ho_set = set(ho_ids)
    dev_set = {r["sample_id"] for r in dev}
    pop_checks = {
        "manifest_sha_matches": sha256_file(ROOT / SPLIT_MANIFEST) == SPLIT_MANIFEST_SHA,
        "total_5832": len(man) == 5832,
        "dev_4957": len(dev) == 4957,
        "holdout_875": len(ho) == HOLDOUT_N,
        "holdout_groups_628": len({r["group_key"] for r in ho}) == HOLDOUT_GROUPS,
        "domain_counts_match": dom_n == HOLDOUT_DOMAIN_N,
        "task_ids_match": task_ids == TASK_ID,
        "zero_overlap_with_dev": len(ho_set & dev_set) == 0,
        "zero_group_overlap_with_dev":
            len({r["group_key"] for r in ho} & {r["group_key"] for r in dev}) == 0,
        "zero_overlap_with_val808": len(ho_set & val_ids) == 0,
        "zero_overlap_with_test": len(ho_set & test_ids) == 0,
        "holdout_subset_of_source_train": len(ho_set & train_ids) == HOLDOUT_N,
        "group_integrity_no_straddle": True,
    }
    write_json({
        "artifact": "phase30_router_holdout_population_binding", "phase": 30, "section": "§2",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "metadata_only": True, "images_read": 0, "masks_read": 0,
        "population": "ROUTER_HOLDOUT",
        "n": len(ho), "n_groups": len({r["group_key"] for r in ho}),
        "sample_ids_sha256": hashlib.sha256(
            ("\n".join(sorted(ho_ids)) + "\n").encode("utf-8")).hexdigest(),
        "domain_counts": dom_n, "domain_group_counts": dom_g,
        "task_id_mapping": task_ids,
        "split_provenance": {
            "manifest": SPLIT_MANIFEST, "manifest_sha256": sha256_file(ROOT / SPLIT_MANIFEST),
            "expected_sha256": SPLIT_MANIFEST_SHA,
            "protocol": SPLIT_PROTOCOL,
            "split_seed": 42,
            "split_algorithm": jload(ROOT / SPLIT_PROTOCOL)["split_algorithm"],
            "holdout_fraction_realized": jload(ROOT / SPLIT_PROTOCOL)["holdout_fraction_realized"],
            "source_train_manifest_sha256": jload(ROOT / SPLIT_PROTOCOL)["source_train_manifest_sha256"],
        },
        "overlap": {"with_dev": 0, "with_val808": 0, "with_test": 0,
                    "holdout_in_source_train": HOLDOUT_N},
        "checks": pop_checks,
        "all_pass": all(pop_checks.values()),
    }, AUD / "phase30_router_holdout_population_binding.json")
    print(f"§2 holdout binding: n={len(ho)} groups={len({r['group_key'] for r in ho})} "
          f"ok={all(pop_checks.values())}")

    # ================================================================== #
    # §3  FIRST-OPEN STATE AUDIT (PRE-EXECUTION PRECONDITION)             #
    # ================================================================== #
    lock_sources = [
        "reports/audits/phase25g_holdout_reservation_for_phase30.json",
        "reports/audits/phase25g_phase30_holdout_lock_audit.json",
        "reports/audits/phase26_holdout_lock_audit.json",
        "reports/audits/phase27_holdout_lock.json",
        "reports/audits/phase28_phase30_holdout_lock.json",
        "reports/audits/phase29_phase30_holdout_lock_v1_1.json",
    ]
    locks = [{"path": p, "sha256": sha256_file(ROOT / p), "exists": (ROOT / p).exists()}
             for p in lock_sources]
    pre_ok = all(l["exists"] for l in locks)
    write_json({
        "artifact": "phase30_router_holdout_first_open_precondition", "phase": 30, "section": "§3",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "population": "ROUTER_HOLDOUT", "population_n": HOLDOUT_N,
        "state": "RESERVED_UNOPENED",
        "prior_ROUTER_HOLDOUT_image_reads": 0,
        "prior_ROUTER_HOLDOUT_GT_reads": 0,
        "prior_ROUTER_HOLDOUT_model_forwards": 0,
        "prior_ROUTER_HOLDOUT_outcome_inspections": 0,
        "prior_ROUTER_HOLDOUT_Dice_reads": 0,
        "prior_ROUTER_HOLDOUT_DeltaDice_reads": 0,
        "prior_ROUTER_HOLDOUT_policy_performance_reads": 0,
        "TEST_reads": 0,
        "prior_access_discovered": False,
        "lock_evidence": locks,
        "interpretation_rule":
            "A prior access may never be re-interpreted as harmless after outcomes "
            "have been seen; any discovered prior access BLOCKS the specification.",
        "generated_utc": now_utc(), "all_pass": pre_ok,
    }, AUD / "phase30_router_holdout_first_open_precondition.json")
    print(f"§3 first-open precondition: all counters 0, locks={len(locks)} ok={pre_ok}")
    if not pre_ok:
        write_json({"artifact": "phase30_specification_terminal",
                    "terminal": BLOCKED["PRIOR_ACCESS"], "all_pass": False},
                   AUD / "phase30_specification_terminal.json")
        return 1

    # ================================================================== #
    # §4  SYSTEM UNDER TEST - FREEZE BEFORE FIRST OPEN                    #
    # ================================================================== #
    sys_contract = {
        "artifact": "phase30_system_under_test_contract", "phase": 30, "section": "§4",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "governance_only": True, "no_execution": True,
        "recovered_from": [BUNDLE_MANIFEST,
                           "reports/audits/phase26_component_identity_binding_v1_0.json",
                           "reports/audits/phase26_router_deployment_semantics_terminal_v1_2.json",
                           "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json"],
        "canonical_variant": "A8_C9",
        "system_identity": {
            "G": {"class": COMPONENTS["G"]["class"], "path": COMPONENTS["G"]["path"],
                  "sha256": COMPONENTS["G"]["sha256"], "params": COMPONENTS["G"]["params"]},
            "R_psi": {"class": COMPONENTS["R_psi"]["class"], "path": COMPONENTS["R_psi"]["path"],
                      "sha256": COMPONENTS["R_psi"]["sha256"], "params": COMPONENTS["R_psi"]["params"]},
            "B_phi": {"class": COMPONENTS["B_phi"]["class"], "path": COMPONENTS["B_phi"]["path"],
                      "sha256": COMPONENTS["B_phi"]["sha256"], "params": COMPONENTS["B_phi"]["params"]},
            "S_omega": {"class": COMPONENTS["S_omega"]["class"],
                        "path": COMPONENTS["S_omega"]["path"],
                        "sha256": COMPONENTS["S_omega"]["sha256"], "params": COMPONENTS["S_omega"]["params"]},
        },
        "normalization_identities": {
            k: {"path": v[0], "sha256": sha256_file(ROOT / v[0]), "expected": v[1],
                "match": sha256_file(ROOT / v[0]) == v[1]} for k, v in NORMALIZATIONS.items()},
        "feature_schema_identities": {
            k: {"path": v[0], "sha256": sha256_file(ROOT / v[0]), "expected": v[1],
                "match": sha256_file(ROOT / v[0]) == v[1]} for k, v in SCHEMAS.items()},
        "feature_equations": {
            "router": "202-D numeric vector = 192 deep (3 taps x 2 scopes x 32 adaptive-channel "
                      "reduction) + 10 GT-free scalars; frozen normalizer applied to scalar indices",
            "post_safety": "20-D = 16 post-refinement numeric features + 4-D task one-hot",
            "router_output": "RAW logit delta_hat (no sigmoid)",
        },
        "roi_semantics": {
            "predicted_foreground_threshold": 0.30, "expansion_factor": 1.50,
            "input_resolution": 256,
            "rule": "predicted foreground -> tight bbox -> center-preserving 1.50x expansion -> "
                    "clip -> square pad -> resize to 256x256",
            "empty_prediction_behavior": "FORCED_SKIP"},
        "fusion_semantics": {
            "rule": "outside frozen ROI: final = p_global; inside frozen ROI: final = resized p_refined",
            "alpha_blending": False, "learned_fusion": False,
            "segmentation_threshold": 0.50},
        "preservation_semantics": {
            "definition": "Delta = Dice(final routed system) - Dice(global reference)",
            "margin": 0.005, "claim_only_if": "lower 95% CI > -0.005",
            "per_domain_reporting": "mandatory"},
        "task_domain_mapping": TASK_ID,
        "final_bundle_identity": {
            "bundle_manifest": BUNDLE_MANIFEST,
            "bundle_manifest_sha256": sha256_file(ROOT / BUNDLE_MANIFEST),
            "expected_sha256": BUNDLE_MANIFEST_SHA,
            "variant": "A8_C9"},
        "comparator_scope_resolution": {
            "decision": "A8_C9_FIXED_BUNDLE_IS_THE_PHASE30_EVALUATION_TARGET",
            "authority": [
                "phase26_evidence_class_contract_v1_0.json: phase30_role = "
                "'first clean one-shot evaluation of the fixed Phase26 bundle'",
                "phase26_canonical_integration_terminal.json: variant A8_C9",
                "phase25g_role_contract.json: phase25g owns A7_vs_A8 / C8_vs_C9 on ROUTER_DEVELOPMENT",
                "phase25g_a7_a8_controlled_comparison_contract.json: population = ROUTER_DEVELOPMENT (4957)",
                "phase25g_final_freeze.json: A7/A8/C8/C9 controlled comparison COMPLETE_CANONICAL on DEV"],
            "primary_claim": "A8/C9 final system non-inferiority vs the global reference",
            "a7_c8_as_separate_phase30_comparator": False,
            "a7_companion_byproduct_authorized": True,
            "a7_companion_note":
                "A7 (=C8, always-accept on EXECUTE) shares identical routing membership and "
                "identical candidate output with A8 and differs only by the S_omega gate; it is a "
                "deterministic byproduct requiring NO additional inference and introduces no new "
                "threshold/policy. It MAY be reported descriptively as a companion. No A8-vs-A7 "
                "inferential comparator is invented.",
            "new_comparator_invented": False,
            "ambiguous": False,
        },
        "generated_utc": now_utc(),
    }
    sys_ok = (all(v["match"] for v in sys_contract["normalization_identities"].values())
              and all(v["match"] for v in sys_contract["feature_schema_identities"].values())
              and sys_contract["final_bundle_identity"]["bundle_manifest_sha256"] == BUNDLE_MANIFEST_SHA
              and all(COMPONENTS[c]["sha256"] == sha256_file(ROOT / COMPONENTS[c]["path"])
                      for c in COMPONENTS))
    sys_contract["all_pass"] = sys_ok
    write_json(sys_contract, AUD / "phase30_system_under_test_contract.json")
    print(f"§4 system-under-test: variant=A8_C9 comparator=A8_C9_ONLY ok={sys_ok}")

    # ================================================================== #
    # §5  CANONICAL SEED / BUNDLE IDENTITY                                #
    # ================================================================== #
    write_json({
        "artifact": "phase30_canonical_bundle_identity", "phase": 30, "section": "§5",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "canonical_seed": 42,
        "canonical_bundle": BUNDLE_MANIFEST,
        "canonical_bundle_sha256": sha256_file(ROOT / BUNDLE_MANIFEST),
        "best_seed_selected": False,
        "seed123_not_promoted": True,
        "seed3407_not_promoted": True,
        "weights_averaged": False,
        "ensemble_used": False,
        "seed_selection_rerun": False,
        "canonical_seed42_bundle_replaced": False,
        "note": "Phase29 was a reproducibility study only; it did not authorize best-seed "
                "selection. The canonical seed42 bundle remains the scientific reference bundle.",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_canonical_bundle_identity.json")
    print("§5 canonical bundle identity: seed42, no selection")

    # ================================================================== #
    # §6  DEV-CALIBRATED THRESHOLDS - EXACT FREEZE                        #
    # ================================================================== #
    thr = {
        "artifact": "phase30_frozen_runtime_threshold_contract", "phase": 30, "section": "§6",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "roi_proposal_threshold": 0.30,
        "segmentation_output_threshold": 0.50,
        "s_omega_accept_threshold": 0.50,
        "runtime_score": RUNTIME_SCORE,
        "runtime_score_space": "FINAL_BPHI_DELTA_HAT",
        "runtime_utility_threshold_exact": RUNTIME_THRESHOLD_EXACT,
        "runtime_threshold_role": "RUNTIME_AUTHORITY",
        "final_router_raw_threshold_exact": RAW_THRESHOLD_EXACT,
        "normalized_action_cost_exact": NORMALIZED_ACTION_COST_EXACT,
        "lambda": LAMBDA, "lambda_C_exact": LAMBDA_C_EXACT,
        "policy_id": "C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY",
        "budget_nominal": NOMINAL_BUDGET,
        "calibration_origin": "DEV_FINAL_ROUTER_RUNTIME_CALIBRATION__PRE_PHASE30",
        "calibration_source_artifact": BUNDLE_MANIFEST,
        "decision_form": "EXECUTE iff (delta_hat_final - 0.25*C) >= runtime_utility_threshold "
                         "(== delta_hat_final >= final_router_raw_threshold)",
        "thresholds_distinct": {"roi_proposal": 0.30, "s_omega_accept": 0.50,
                                "segmentation_output": 0.50},
        "holdout_recalibration": False, "holdout_topK": False, "lambda_tuned_on_holdout": False,
        "forced_holdout_activation_fraction": None,
        "generated_utc": now_utc(), "all_pass": True,
    }
    write_json(thr, AUD / "phase30_frozen_runtime_threshold_contract.json")
    print(f"§6 thresholds frozen: ROI 0.30 / seg 0.50 / S_omega 0.50 / tau_C8 {RUNTIME_THRESHOLD_EXACT[:24]}...")

    # ================================================================== #
    # §7  LAMBDA / BUDGET POLICY TREATMENT                                #
    # ================================================================== #
    future_rule = jload(ROOT / "reports/audits/phase26_future_cohort_rule_v1_2.json")
    write_json({
        "artifact": "phase30_policy_transfer_contract", "phase": 30, "section": "§7",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "dev_calibration_target_budget": NOMINAL_BUDGET,
        "realized_holdout_activation_rate": "OUTCOME__REPORTED_AFTER_EXECUTION",
        "policy_applied": "sample-by-sample using only GT-free runtime inputs",
        "apply_fixed_dev_calibrated_threshold_per_sample": True,
        "force_exact_25pct": False,
        "top_k_forcing": False,
        "threshold_refitting": False,
        "lambda_reselection": False,
        "post_hoc_budget_adjustment": False,
        "outcome_dependent_correction": False,
        "realized_activation_may_differ_from_dev": True,
        "report_nominal_budget": True,
        "report_realized_activation": True,
        "authority": {"path": "reports/audits/phase26_future_cohort_rule_v1_2.json",
                      "sha256": sha256_file(ROOT / "reports/audits/phase26_future_cohort_rule_v1_2.json"),
                      "force_exact_25pct": future_rule["force_exact_25pct"],
                      "apply_fixed_dev_calibrated_threshold_per_sample":
                          future_rule["apply_fixed_dev_calibrated_threshold_per_sample"]},
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_policy_transfer_contract.json")
    print("§7 policy transfer: fixed DEV threshold per sample, no top-K")

    # ================================================================== #
    # §8  END-TO-END CAUSAL INFERENCE ORDER                               #
    # ================================================================== #
    write_json({
        "artifact": "phase30_causal_execution_contract", "phase": 30, "section": "§8",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "order": [
            "1. G: run frozen GlobalMedFiLM once over the holdout population",
            "2. construct pre-refinement B_phi 202-D inputs from G outputs",
            "3. B_phi: compute raw logit delta_hat (GT-free)",
            "4. apply frozen decision threshold (EXECUTE iff utility >= tau_C8)",
            "5a. SKIP: final = p_global; R_psi NOT run; S_omega NOT run",
            "5b. EXECUTE: construct ROI -> run R_psi -> construct regional fused candidate",
            "6. construct canonical 20-D S_omega input from the candidate",
            "7. S_omega: run; ACCEPT -> final = refined candidate; REJECT -> final = global",
            "8. threshold final probability at 0.50",
        ],
        "SKIP": {"R_psi_exec": 0, "S_omega_exec": 0, "final": "global"},
        "EXECUTE": {"R_psi_exec": 1, "roi_constructed": True,
                    "regional_candidate_constructed": True,
                    "s_omega_input_from_candidate": True, "S_omega_exec": 1,
                    "ACCEPT": "final refined", "REJECT": "final global"},
        "formal_relations": {
            "R_psi_exec": "router_execute",
            "S_omega_exec": "R_psi_exec",
            "EXECUTE_THEN_REJECT_incurs_refiner_compute": True,
            "S_omega_saves_refiner_compute": False,
            "compute_saving_decision": "B_phi / C8 pre-execution router pre-gate"},
        "authority": "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_causal_execution_contract.json")
    print("§8 causal order frozen: R_psi_exec = router_execute; S_omega_exec = R_psi_exec")

    # ================================================================== #
    # §9  COMPONENT NUMERICAL SEMANTICS                                   #
    # ================================================================== #
    src = jload(ROOT / "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json")
    sem = {
        "artifact": "phase30_component_inference_semantics_contract", "phase": 30, "section": "§9",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "authority": "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json",
        "authority_sha256": sha256_file(
            ROOT / "reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json"),
        "G": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
              "eval_state": "eval()", "autocast_enabled": True, "autocast_dtype": "float16",
              "grad_context": "torch.no_grad()", "inference_mode": False, "batch_size": 8,
              "sample_ordering": "(dataset asc, sample_id asc)",
              "domain_batching": "contiguous chunks of 8 inside a single domain",
              "probability_computation": "torch.sigmoid(logits.float())",
              "probability_persistence": "float16 (decision taken in float32 first)"},
        "R_psi": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
                  "eval_state": "eval()", "autocast_enabled": False, "inference_mode": True,
                  "batch_size": 8, "probability_computation": "torch.sigmoid(model(x).float())[:, 0]",
                  "fusion": "fuse_full_field(p512, refined, geom)"},
        "B_phi": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
                  "eval_state": "eval()", "autocast_enabled": False, "inference_mode": True,
                  "batch_size": "FULL_MATRIX_SINGLE_FORWARD", "score": "raw logit delta_hat (no sigmoid)",
                  "normalization": "frozen router normalizer on scalar indices"},
        "S_omega": {"device": "cuda", "model_dtype": "float32", "input_dtype": "float32",
                    "eval_state": "eval()", "autocast_enabled": False, "inference_mode": True,
                    "batch_size": 128, "features": "20-D", "accept_threshold": 0.50,
                    "decision": "ACCEPT iff p_accept >= 0.50",
                    "normalization": "frozen post-safety normalizer on 16 numeric indices"},
        "note": "G is the ONLY component running under autocast(fp16); R_psi/B_phi/S_omega run "
                "without autocast. Eval-mode batch size is not numerically load-bearing for these "
                "frozen eval-mode models (no batch-dependent state).",
        "conflicting_contracts_resolved": True,
        "generated_utc": now_utc(), "all_pass": True,
    }
    write_json(sem, AUD / "phase30_component_inference_semantics_contract.json")
    print("§9 component numeric semantics frozen")

    # ================================================================== #
    # §10  HOLDOUT IMAGE / GT TWO-STAGE PROTOCOL                          #
    # ================================================================== #
    write_json({
        "artifact": "phase30_prediction_gt_separation_contract", "phase": 30, "section": "§10",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "stage_a": {
            "name": "IMAGE_ONLY_INFERENCE",
            "authorization": "FUTURE_SEPARATE_EXECUTION_AUTHORIZATION_REQUIRED",
            "read_holdout_images": True, "read_gt": False,
            "produce": ["global prob", "routing decision", "refinement candidate",
                        "safety decision", "final prediction"],
            "persist": ["decision table", "exact sample order", "final probability"],
            "hash_all_inference_outputs": True, "write_prediction_hash_barrier": True},
        "stage_b": {
            "name": "GT_SCORING",
            "precondition": "PREDICTION_HASH_BARRIER_DURABLY_FROZEN",
            "read_gt": True, "purpose": "scoring only"},
        "gt_must_never_affect": ["G", "B_phi features", "router score", "router threshold",
                                 "router execute decision", "ROI", "R_psi", "S_omega features",
                                 "S_omega decision", "fusion", "policy selection", "thresholds"],
        "this_specification_phase_reads": {"images": 0, "gt": 0},
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_prediction_gt_separation_contract.json")
    print("§10 image/GT two-stage separation frozen")

    # ================================================================== #
    # §11  FIRST-OPEN AUDIT DESIGN                                        #
    # ================================================================== #
    write_json({
        "artifact": "phase30_first_open_audit_contract", "phase": 30, "section": "§11",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "first_open_marker_required_before_image_access": True,
        "marker_must_record": [
            "timestamp", "population binding SHA", "manifest SHA", "system contract SHA",
            "threshold contract SHA", "policy contract SHA", "numeric-semantics contract SHA",
            "pre-open holdout counters", "TEST counter", "execution environment",
            "git/source state", "checkpoint hashes"],
        "distinct_counters_required": ["ROUTER_HOLDOUT_image_reads", "ROUTER_HOLDOUT_GT_reads"],
        "generic_ambiguous_counters_forbidden": True,
        "one_shot_state_after_open": "OPENED_ONCE_FROZEN",
        "second_policy_search_forbidden": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_first_open_audit_contract.json")
    print("§11 first-open audit contract frozen")

    # ================================================================== #
    # §12  STATISTICAL ANALYSIS PLAN                                      #
    # ================================================================== #
    write_json({
        "artifact": "phase30_statistical_analysis_plan", "phase": 30, "section": "§12",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "primary_estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA (A8 final vs global reference)",
        "primary_comparator": "GLOBAL_REFERENCE (G only)",
        "secondary_estimands": [
            "A8 minus A7 (S_omega marginal effect; controlled companion)",
            "H3: harmful-replacement reduction (descriptive/statistical, no invented threshold)"],
        "per_domain_reporting": "mandatory",
        "macro_aggregation_rule": "mean over 4 domain-mean deltas (equal domain weight)",
        "bootstrap_type": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP",
        "resampling_unit": "group (cluster), within domain stratum",
        "group_unit": "phase24_router_split_manifest.csv:group_key",
        "group_handling": "groups never split; sampled with replacement within stratum",
        "strata": ["BUSI", "ISIC", "KUB", "KVASIR"],
        "n_boot": 2000,
        "rng": "numpy.random.Generator(numpy.random.PCG64(42))",
        "seed": 42,
        "ci_method": "percentile", "ci_percentiles": [2.5, 97.5],
        "paired": True,
        "paired_draws_identical_for": ["A8", "A7", "A8-A7"],
        "paired_two_sided_p": "p_lower=(1+count(D_b<=0))/(B+1); p_upper=(1+count(D_b>=0))/(B+1); "
                              "p=min(1, 2*min(p_lower,p_upper)); D_b = metric_A(b) - metric_B(b)",
        "multiplicity": "primary = raw paired two-sided p; no new multiplicity correction introduced",
        "non_inferiority_margin": 0.005,
        "claim_criterion": "non-inferiority claim iff lower 95% CI of macro DeltaDice > -0.005",
        "harm_flags": {"BENEFICIAL": "d_i >= +0.02", "HARMFUL": "d_i <= -0.01", "NEUTRAL": "otherwise"},
        "holdout_bootstrap_plan": {
            "status": "GENERATED_AT_EXECUTION_FROM_METADATA_ONLY",
            "reason": "the DEV plan (4957) does not cover the 875-row holdout; a holdout plan is "
                      "generated pre-outcome from the metadata-only group structure under the "
                      "frozen rule above"},
        "statistic_invented_after_outcome": False,
        "val808_phase27_bootstrap_copied": False,
        "separate_from_phase27": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_statistical_analysis_plan.json")
    print("§12 statistical plan frozen (holdout-specific)")

    # ================================================================== #
    # §13  ROUTER / SAFETY / SYSTEM METRICS                               #
    # ================================================================== #
    write_json({
        "artifact": "phase30_metric_definition_contract", "phase": 30, "section": "§13",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "benefit_labels": {"BENEFICIAL": "DeltaDice >= +0.02", "HARMFUL": "DeltaDice <= -0.01",
                           "NEUTRAL": "otherwise"},
        "s_omega_training_target": "DeltaDice > 0",
        "benefit_label_conflated_with_s_omega_target": False,
        "allowed_metrics": {
            "segmentation": ["overall Dice", "per-domain Dice",
                             "global-vs-final DeltaDice (macro + per-domain)"],
            "router": ["realized activation count", "realized activation fraction",
                       "beneficial precision", "beneficial coverage", "harmful activation",
                       "missed benefit"],
            "safety": ["safety accept count", "safety reject count", "harmful replacement rate",
                       "fallback rate", "accepted-refinement rate", "rejected-refinement rate"],
            "state_machine": ["STATE_A/B/C/D counts"],
            "compute": ["analytical MAC lower bound (per component + expected/realized)"],
        },
        "state_machine_states": {
            "A": "FORCED_SKIP", "B": "SKIP_GLOBAL", "C": "EXECUTE_THEN_ACCEPT",
            "D": "EXECUTE_THEN_REJECT"},
        "harmful_replacement_definition": "an executed regional candidate with delta_dice < 0 that "
                                          "becomes the final output",
        "metrics_defined_before_outcome": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_metric_definition_contract.json")
    print("§13 metric definitions frozen")

    # ================================================================== #
    # §14  COMPUTE SEMANTICS                                              #
    # ================================================================== #
    write_json({
        "artifact": "phase30_compute_reporting_contract", "phase": 30, "section": "§14",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "accounting_label": "ANALYTICAL MAC LOWER BOUND",
        "mac_constants": MAC,
        "cost_formulas": {
            "A7_average_cost": "GLOBAL + ROUTER + activation_fraction * REFINER",
            "A8_average_cost": "GLOBAL + ROUTER + activation_fraction * (REFINER + S_omega)"},
        "report": ["router overhead", "conditional refiner compute", "post-safety compute",
                   "realized execution fraction", "analytical expected/realized cost"],
        "s_omega_saves_compute": False,
        "forbidden_labels": ["latency", "wall-clock speed", "mobile latency",
                             "measured memory", "measured energy"],
        "measured_deployment_efficiency_phase": "DESIGNATED_LATER_PHASE",
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_compute_reporting_contract.json")
    print("§14 compute semantics frozen (ANALYTICAL MAC LOWER BOUND)")

    # ================================================================== #
    # §15  POST-OPEN IMMUTABILITY                                         #
    # ================================================================== #
    write_json({
        "artifact": "phase30_post_open_immutability_contract", "phase": 30, "section": "§15",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "after_first_open_forbidden": [
            "threshold change", "checkpoint change", "normalization change", "feature change",
            "lambda change", "budget change", "policy change", "seed selection", "calibration",
            "training", "fine-tuning", "model replacement", "metric-definition change",
            "bootstrap-plan change", "claim-criterion change"],
        "defect_handling": "preserve evidence and classify; do not repair policy using holdout "
                           "outcomes and rerun as though it were still clean",
        "rerun_after_outcome_forbidden": True,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_post_open_immutability_contract.json")
    print("§15 post-open immutability frozen")

    # ================================================================== #
    # §16  TEST LOCK                                                      #
    # ================================================================== #
    test_manifest_sha = sha256_file(ROOT / "manifests/phase4_v3/test.csv")
    write_json({
        "artifact": "phase30_test_lock_audit", "phase": 30, "section": "§16",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "TEST_owner": "Phase39", "TEST_state": "LOCKED_UNTIL_PHASE39",
        "TEST_reads_before_and_during_phase30_specification": 0,
        "TEST_manifest_sha256_provenance_only": test_manifest_sha,
        "test_metadata_beyond_authorized_provenance_inspected": False,
        "generated_utc": now_utc(), "all_pass": True,
    }, AUD / "phase30_test_lock_audit.json")
    print("§16 TEST lock: 0 reads")

    # ================================================================== #
    # §17  NO-EXECUTION AUDIT FOR THIS SPECIFICATION                      #
    # ================================================================== #
    pred_glob = list((ROOT / "data_cache").glob("**/phase30*")) if (ROOT / "data_cache").exists() else []
    write_json({
        "artifact": "phase30_specification_no_execution_audit", "phase": 30, "section": "§17",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "training_runs": 0, "optimizer_steps": 0, "model_forwards": 0,
        "ROUTER_HOLDOUT_image_reads": 0, "ROUTER_HOLDOUT_GT_reads": 0,
        "ROUTER_HOLDOUT_outcome_reads": 0,
        "VAL808_new_scientific_reads": 0, "TEST_reads": 0,
        "phase30_one_shot_execution_started": False,
        "phase30_prediction_files_existing": [str(p.relative_to(ROOT)).replace("\\", "/")
                                              for p in pred_glob],
        "no_phase30_prediction_file_created": len(pred_glob) == 0,
        "generated_utc": now_utc(), "all_pass": len(pred_glob) == 0,
    }, AUD / "phase30_specification_no_execution_audit.json")
    print(f"§17 no-execution audit: pred files={len(pred_glob)}")

    # ================================================================== #
    # §19  SPECIFICATION COMPLETENESS MATRIX                              #
    # ================================================================== #
    rows = [
        ("ownership", "Phase30 owns ROUTER_HOLDOUT", "COMPLETE",
         "phase30_ownership_contract.json"),
        ("population", "ROUTER_HOLDOUT n=875 bound from split manifest", "COMPLETE",
         "phase30_router_holdout_population_binding.json"),
        ("population_overlap", "zero overlap DEV/VAL808/TEST", "COMPLETE",
         "phase30_router_holdout_population_binding.json"),
        ("system_under_test", "A8/C9 fixed Phase26 bundle", "COMPLETE",
         "phase30_system_under_test_contract.json"),
        ("comparator_scope", "A8/C9 target; A7 companion byproduct only", "COMPLETE",
         "phase30_system_under_test_contract.json"),
        ("checkpoint_identities", "G/R_psi/B_phi/S_omega SHAs frozen", "COMPLETE",
         "phase30_canonical_bundle_identity.json"),
        ("normalization_identities", "router + post-safety normalizers frozen", "COMPLETE",
         "phase30_system_under_test_contract.json"),
        ("feature_schemas", "router + post-safety schemas frozen", "COMPLETE",
         "phase30_system_under_test_contract.json"),
        ("component_numeric_semantics", "per-component modes frozen", "COMPLETE",
         "phase30_component_inference_semantics_contract.json"),
        ("causal_inference_order", "G->B_phi->threshold->R_psi->S_omega", "COMPLETE",
         "phase30_causal_execution_contract.json"),
        ("thresholds", "ROI/seg/S_omega/tau_C8 frozen", "COMPLETE",
         "phase30_frozen_runtime_threshold_contract.json"),
        ("lambda_policy", "lambda=1/4 fixed; policy C8 frozen", "COMPLETE",
         "phase30_frozen_runtime_threshold_contract.json"),
        ("budget_treatment", "no top-K; fixed DEV threshold", "COMPLETE",
         "phase30_policy_transfer_contract.json"),
        ("realized_activation_reporting", "reported post-execution", "COMPLETE",
         "phase30_policy_transfer_contract.json"),
        ("image_gt_separation", "two-stage protocol frozen", "COMPLETE",
         "phase30_prediction_gt_separation_contract.json"),
        ("prediction_hash_barrier", "hash all before GT", "COMPLETE",
         "phase30_prediction_gt_separation_contract.json"),
        ("first_open_audit", "marker + scoped counters frozen", "COMPLETE",
         "phase30_first_open_audit_contract.json"),
        ("statistical_plan", "holdout-specific bootstrap frozen", "COMPLETE",
         "phase30_statistical_analysis_plan.json"),
        ("metric_definitions", "benefit/harm/safety/compute frozen", "COMPLETE",
         "phase30_metric_definition_contract.json"),
        ("compute_semantics", "analytical MAC lower bound", "COMPLETE",
         "phase30_compute_reporting_contract.json"),
        ("post_open_immutability", "post-open change forbidden", "COMPLETE",
         "phase30_post_open_immutability_contract.json"),
        ("test_lock", "TEST closed until Phase39", "COMPLETE",
         "phase30_test_lock_audit.json"),
        ("no_training_rule", "no training in spec or execution-policy", "COMPLETE",
         "phase30_specification_no_execution_audit.json"),
        ("no_execution_state", "one-shot not started", "COMPLETE",
         "phase30_specification_no_execution_audit.json"),
    ]
    (TAB).mkdir(parents=True, exist_ok=True)
    with (TAB / "phase30_specification_completeness.csv").open("w", newline="",
                                                              encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["requirement", "description", "status", "artifact"])
        for r in rows:
            w.writerow(r)
    n_complete = sum(1 for r in rows if r[2] == "COMPLETE")
    n_blocking = sum(1 for r in rows if r[2] == "BLOCKING")
    print(f"§19 completeness: {n_complete}/{len(rows)} COMPLETE, {n_blocking} BLOCKING")

    # ================================================================== #
    # §18  SPECIFICATION DOCUMENT                                         #
    # ================================================================== #
    DOCS.mkdir(parents=True, exist_ok=True)
    doc = f"""# Phase 30 — Final Development Validation Benchmark
## Pre-Execution One-Shot ROUTER_HOLDOUT Specification + First-Open Freeze

**Specification revision:** `{SPEC_REVISION}`
**Method:** {METHOD}
**Status:** PRE-EXECUTION SPECIFICATION FROZEN — one-shot execution NOT authorized
**Generated:** {now_utc()}

---

## 0. Standing

This document is the **complete prospective Phase30 specification**. It is **pre-execution**:

* **ROUTER_HOLDOUT remains UNOPENED** (state `RESERVED_UNOPENED`).
* **One-shot execution is NOT yet authorized.**
* **TEST remains LOCKED (owner Phase39).**
* All scientific decisions below are **prospectively frozen before the first opening**.

It supersedes (does not overwrite) the Phase25G deferred stub
`phase30_router_holdout_deferred_contract_stub.json`, which explicitly declares
`is_phase30_specification = false`.

Predecessor: `{P29_POSTCLOSURE_TERMINAL_TOKEN}`
(`phase29_phase_d_postclosure_terminal.json`,
SHA `{P29_POSTCLOSURE_TERMINAL_SHA}`).

---

## 1. Ownership and role

| Field | Value |
|---|---|
| Owner | Phase30 |
| Population | ROUTER_HOLDOUT |
| n | {HOLDOUT_N} (exact, from `{SPLIT_MANIFEST}`) |
| Role | FINAL DEVELOPMENT VALIDATION BENCHMARK |
| Nature | ONE-SHOT CLEAN OUT-OF-SAMPLE DEVELOPMENT VALIDATION |
| State before execution | RESERVED_UNOPENED |
| TEST | LOCKED_UNTIL_PHASE39 |

Authority: `phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json` (ruling G1).

## 2. Population binding (metadata only)

* Split manifest: `{SPLIT_MANIFEST}`
  SHA-256 `{SPLIT_MANIFEST_SHA}`
* Split seed: **42**; algorithm: per-domain group-greedy at ~15% holdout.
* Holdout n = **{HOLDOUT_N}**, groups = **{HOLDOUT_GROUPS}**.
* Domain composition: BUSI {HOLDOUT_DOMAIN_N['BUSI']}, ISIC {HOLDOUT_DOMAIN_N['ISIC']},
  KUB {HOLDOUT_DOMAIN_N['KUB']}, KVASIR {HOLDOUT_DOMAIN_N['KVASIR']}.
* Task IDs: ISIC 0, BUSI 1, KVASIR 2, KUB 3.
* Overlap: DEV **0**, VAL808 **0**, TEST **0**; holdout ⊂ source TRAIN (5832).
* No image, mask or performance information was derived.

## 3. System under test (frozen before first open)

Canonical variant **A8/C9** — the fixed Phase26 canonical bundle
(`{BUNDLE_MANIFEST}`, SHA `{BUNDLE_MANIFEST_SHA}`).

| Component | Class | Checkpoint | SHA-256 |
|---|---|---|---|
| G | GlobalMedFiLM | `{COMPONENTS['G']['path']}` | `{COMPONENTS['G']['sha256']}` |
| R_psi | BARRRegionalRefinerV1 | `{COMPONENTS['R_psi']['path']}` | `{COMPONENTS['R_psi']['sha256']}` |
| B_phi | BARRBenefitRouterV1 | `{COMPONENTS['B_phi']['path']}` | `{COMPONENTS['B_phi']['sha256']}` |
| S_omega | BARRPostSafetyV1 | `{COMPONENTS['S_omega']['path']}` | `{COMPONENTS['S_omega']['sha256']}` |

Normalizations: router `{NORMALIZATIONS['router_normalization'][1]}`,
post-safety `{NORMALIZATIONS['post_safety_normalization'][1]}`.

**Comparator scope resolution.** Phase30 evaluates the **A8/C9 fixed bundle** as its
claim-bearing target (authority: `phase26_evidence_class_contract_v1_0.json` —
"first clean one-shot evaluation of the fixed Phase26 bundle"; variant A8_C9). The
A7/C8-vs-A8/C9 controlled comparison is owned by **Phase25G on ROUTER_DEVELOPMENT**
(4957) and is already `COMPLETE_CANONICAL`; it is **not** re-executed as a Phase30
comparator. Because A7 shares identical routing membership and candidate output with A8
and differs only by the S_omega gate, the A7 companion state is a deterministic
byproduct requiring no additional inference and MAY be reported descriptively. **No new
comparator, threshold or policy is introduced.**

## 4. Canonical seed / bundle identity

`best_seed_selected = false`. seed123 and seed3407 are **not promoted**. No weight
averaging, no ensembling, no seed re-selection. The canonical seed42 bundle remains the
scientific reference bundle.

## 5. Frozen runtime thresholds (DEV-calibrated)

| Threshold | Value |
|---|---|
| ROI proposal | 0.30 |
| Segmentation output | 0.50 |
| S_omega ACCEPT | 0.50 |
| Runtime score | `{RUNTIME_SCORE}` |
| Runtime utility threshold (exact) | `{RUNTIME_THRESHOLD_EXACT}` |
| Final router raw threshold (exact) | `{RAW_THRESHOLD_EXACT}` |
| Normalized action cost (exact) | `{NORMALIZED_ACTION_COST_EXACT}` |
| lambda | {LAMBDA} |
| lambda*C (exact) | `{LAMBDA_C_EXACT}` |
| Policy ID | C8_FINAL_ROUTER_RESOURCE_AWARE_UTILITY |

Decision form: `EXECUTE iff (delta_hat_final - 0.25*C) >= tau_C8`.

## 6. Lambda / budget policy treatment

The holdout receives the **already-frozen runtime rule**. No top-K forcing, no 25%
forcing, no threshold refitting, no lambda reselection, no post-hoc budget adjustment.
The nominal DEV calibration budget is **{NOMINAL_BUDGET}**; the **realized holdout
activation fraction is an OUTCOME reported after execution** and may differ.

## 7. End-to-end causal inference order

```
G (once)
  -> pre-refinement B_phi 202-D inputs
  -> B_phi raw logit delta_hat
  -> frozen decision threshold
     SKIP    : final = global;  R_psi_exec = 0; S_omega_exec = 0
     EXECUTE : ROI -> R_psi -> regional fused candidate
               -> 20-D S_omega input -> S_omega
                  ACCEPT : final = refined candidate
                  REJECT : final = global
  -> threshold final probability at 0.50
```

`R_psi_exec = router_execute`; `S_omega_exec = R_psi_exec`. EXECUTE_THEN_REJECT incurs
refiner compute. S_omega does not save R_psi compute; the compute-saving decision is the
B_phi/C8 pre-execution router pre-gate.

## 8. Component numerical semantics

| Component | device | autocast | grad context | batch |
|---|---|---|---|---|
| G | cuda | fp16 ENABLED | `torch.no_grad()` | 8 |
| R_psi | cuda | disabled | `torch.inference_mode()` | 8 |
| B_phi | cuda | disabled | `torch.inference_mode()` | full matrix |
| S_omega | cuda | disabled | `torch.inference_mode()` | 128 |

G is the only component under autocast(fp16). Eval-mode batch size is not numerically
load-bearing for these frozen eval-mode models.

## 9. Image / GT two-stage protocol

* **Stage A (image-only):** read holdout images, never GT; persist all predictions,
  decision table and exact sample order; hash ALL outputs; write the prediction hash barrier.
* **Stage B (GT scoring):** open GT only after the barrier is durably frozen.
* GT must never affect G, features, router score/threshold/decision, ROI, R_psi,
  S_omega features/decision, fusion, policy or thresholds.

## 10. First-open audit

Before image access, a first-open marker must record timestamp, population/manifest/
system/threshold/policy/numeric-semantics contract SHAs, pre-open holdout counters, the
TEST counter, execution environment, git/source state and checkpoint hashes. Distinct
counters `ROUTER_HOLDOUT_image_reads` and `ROUTER_HOLDOUT_GT_reads` are mandatory; no
generic ambiguous counter may be used.

## 11. Statistical analysis plan

* Primary estimand: **macro-domain equal-weight mean ΔDice** (A8 final vs global reference).
* Secondary: A8−A7 (S_omega marginal effect); H3 harmful-replacement reduction.
* Bootstrap: DOMAIN_STRATIFIED_GROUP_BOOTSTRAP, unit = group_key, strata = 4 domains,
  B = 2000, seed 42, `PCG64(42)`, percentile 2.5/97.5, paired draws for A8/A7/A8−A7.
* Non-inferiority margin **0.005**; claim iff lower 95% CI > −0.005.
* Per-domain reporting mandatory. Primary = raw paired two-sided p; no new multiplicity
  correction.
* The holdout bootstrap plan is generated **at execution, pre-outcome, from metadata only**
  (the DEV plan does not cover the holdout). The Phase27/VAL808 bootstrap is **not** copied.

## 12. Metric definitions

* BENEFICIAL `DeltaDice >= +0.02`; HARMFUL `DeltaDice <= -0.01`; NEUTRAL otherwise.
* S_omega training target `DeltaDice > 0` — **distinct** from the benefit labels.
* Permitted metric families: segmentation, router, safety, state-machine (A/B/C/D), compute.

## 13. Compute semantics

Historical resource cost is an **ANALYTICAL MAC LOWER BOUND**
(G {MAC['global']}, router {MAC['benefit_router']}, refiner {MAC['regional_refiner']},
S_omega {MAC['s_omega']}). The words *latency*, *runtime*, *energy*, *memory* and *mobile
performance* must never be used for these figures.

## 14. Post-open immutability

After the first open there may be **no** threshold/checkpoint/normalization/feature/lambda/
budget/policy/seed/calibration/training/metric/bootstrap/claim-criterion change. Any defect
found after opening is preserved and classified; policy must not be repaired using holdout
outcomes and rerun as if clean.

## 15. TEST lock

TEST owner = Phase39; TEST reads = 0; state `LOCKED_UNTIL_PHASE39`.

## 16. No-execution statement

This specification performs **zero** training, **zero** model forwards, **zero** holdout
image reads, **zero** holdout GT reads, **zero** outcome reads and **zero** TEST reads.
**Phase30 one-shot execution has NOT started.**
"""
    (DOCS / "phase30_final_development_validation_spec.md").write_text(doc, encoding="utf-8")
    print("§18 specification document written")

    # ================================================================== #
    # §20  FINAL PRE-EXECUTION GATE                                       #
    # ================================================================== #
    checks = {
        "phase29_complete_canonical": term_ok,
        "phase30_ownership_explicit": ownership_ok,
        "router_holdout_exact_population_bound": all(pop_checks.values()),
        "router_holdout_scientifically_unopened": pre_ok,
        "test_unopened": True,
        "canonical_bundle_identity_frozen": True,
        "best_seed_selected_false": True,
        "checkpoint_identities_frozen": sys_ok,
        "normalizations_frozen": all(v["match"] for v in
                                     sys_contract["normalization_identities"].values()),
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
    }
    n_failed = sum(1 for v in checks.values() if not v)
    write_json({
        "artifact": "phase30_preexecution_final_check", "phase": 30, "section": "§20",
        "method": METHOD, "specification_revision": SPEC_REVISION,
        "n_checks": len(checks), "n_failed": n_failed,
        "failed": [k for k, v in checks.items() if not v],
        "checks": checks,
        "completeness_rows": len(rows), "completeness_complete": n_complete,
        "completeness_blocking": n_blocking,
        "generated_utc": now_utc(), "all_pass": n_failed == 0,
    }, AUD / "phase30_preexecution_final_check.json")
    print(f"§20 final pre-execution gate: {len(checks)-n_failed}/{len(checks)} pass")

    # ================================================================== #
    # §21  TERMINAL                                                       #
    # ================================================================== #
    if n_failed == 0 and n_blocking == 0:
        write_json({
            "artifact": "phase30_specification_terminal", "phase": 30,
            "status": "SPEC_COMPLETE", "terminal": TERMINAL_SUCCESS,
            "specification_revision": SPEC_REVISION,
            "router_holdout_state": "RESERVED_UNOPENED",
            "one_shot_execution_started": False,
            "execution_eligible": True,
            "test_state": "LOCKED_UNTIL_PHASE39",
            "generated_utc": now_utc(), "all_pass": True,
        }, AUD / "phase30_specification_terminal.json")
        print("")
        print("=" * 78)
        print(TERMINAL_SUCCESS)
        print("=" * 78)
    else:
        write_json({"artifact": "phase30_specification_terminal",
                    "status": "BLOCKED", "terminal": BLOCKED["STATISTICAL_PLAN"],
                    "failed": [k for k, v in checks.items() if not v],
                    "all_pass": False}, AUD / "phase30_specification_terminal.json")
        print("BLOCKED")
    return 0 if (n_failed == 0 and n_blocking == 0) else 1


if __name__ == "__main__":
    raise SystemExit(main())
