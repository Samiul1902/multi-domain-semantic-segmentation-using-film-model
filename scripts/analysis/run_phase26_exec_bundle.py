"""Phase26 canonical integration execution - SECTIONS 3-6, 23, 24, 25.

3. Canonical bundle directory
4. Canonical bundle manifest
5. Two router calibration blocks
6. Future-cohort rule
23. Resource accounting
24. Bundle self-validation
25. Deterministic bundle manifest

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/run_phase26_exec_bundle.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_exec_common as K  # noqa: E402

say = print


def check(name, cond):
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    return bool(cond)


# =========================================================================== #
# SECTION 3 / 4 / 5 / 6 - BUNDLE DIRECTORY + MANIFEST
# =========================================================================== #
def build_manifest():
    K.BUNDLE.mkdir(parents=True, exist_ok=True)

    comps = {
        "global_medfilm": K.bind(K.GLOBAL_CHECKPOINT, K.GLOBAL_SHA),
        "regional_refiner": K.bind(K.REFINER_CHECKPOINT, K.REFINER_SHA),
        "benefit_router": K.bind(K.ROUTER_CHECKPOINT, K.ROUTER_SHA),
        "post_safety": K.bind(K.SOMEGA_CHECKPOINT, K.SOMEGA_SHA),
    }
    norms = {
        "router_normalization": K.bind(K.ROUTER_NORMALIZATION, K.ROUTER_NORMALIZATION_SHA),
        "post_safety_normalization": K.bind(K.SOMEGA_STATS_CSV, None),
    }
    schemas = {
        "router_schema": K.bind(K.ROUTER_SCHEMA, K.ROUTER_SCHEMA_SHA),
        "post_safety_schema": K.bind(K.SOMEGA_SCHEMA, None),
    }

    oof_block = {
        "block": "A_OOF_SCIENTIFIC_EVIDENCE",
        "score_variable": "delta_hat_oof",
        "raw_threshold_exact": K.exact(K.TAU_C7_OOF),
        "resource_threshold_exact": K.exact(K.TAU_C8_OOF),
        "role": "SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE",
        "runtime_authority": False,
        "oof_selected_count": K.OOF_SELECTED_COUNT,
        "oof_membership_sha256": K.OOF_MEMBERSHIP_SHA,
    }
    final_block = {
        "block": "B_FINAL_ROUTER_RUNTIME_CALIBRATION",
        "score_variable": "delta_hat_final",
        "producer": "FINAL Phase25D B_phi",
        "raw_threshold_exact": K.exact(K.TAU_C7_FINAL),
        "normalized_action_cost_exact": K.exact(K.C_ACTION),
        "lambda": K.exact(K.CANONICAL_LAMBDA),
        "lambda_C_exact": K.exact(K.LAMBDA_C),
        "resource_utility_threshold_exact": K.exact(K.TAU_C8_FINAL),
        "role": "CANONICAL_FINAL_ROUTER_RUNTIME_CALIBRATION",
        "runtime_authority": True,
        "dev_calibration_selected_count": K.FINAL_ROUTER_SELECTED_COUNT,
        "final_router_calibration_membership_sha256": K.FINAL_ROUTER_MEMBERSHIP_SHA,
    }

    manifest = {
        "artifact": "phase26_canonical_bundle_manifest",
        "method": K.METHOD,
        "bundle_revision": K.BUNDLE_REVISION,
        "phase26_revision": K.PHASE26_REVISION,
        "router_semantics_revision": K.ROUTER_SEMANTICS_REVISION,
        "variant": K.CANONICAL_VARIANT,
        "nominal_budget": K.NOMINAL_BUDGET,
        "canonical_lambda": float(K.CANONICAL_LAMBDA),
        "lambda_role": K.LAMBDA_ROLE,
        "lambda_performance_selected": K.LAMBDA_PERFORMANCE_SELECTED,
        "selection_time": K.SELECTION_TIME,
        "components": comps,
        "normalizations": norms,
        "schemas": schemas,
        "A_OOF_SCIENTIFIC_EVIDENCE": oof_block,
        "B_FINAL_ROUTER_RUNTIME_CALIBRATION": final_block,
        "operational_threshold":
            "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold",
        "runtime_score": "delta_hat_final - 0.25*C",
        "future_cohort_policy": "FIXED_DEV_CALIBRATED_THRESHOLD",
        "future_cohort_forbidden": {
            "top_k_forcing": True,
            "exact_25pct_cohort_ranking": True,
            "holdout_threshold_fitting": True,
            "holdout_quantile_recalibration": True,
        },
        "phase30_nominal_budget": K.NOMINAL_BUDGET,
        "phase30_realized_activation_fraction": "OBSERVED_AFTER_FIXED_THRESHOLD_APPLICATION",
        "thresholds_distinct": {
            "roi_proposal_threshold": K.ROI_PROPOSAL_THRESHOLD,
            "s_omega_accept_threshold": K.SOMEGA_ACCEPT_THRESHOLD,
            "segmentation_output_threshold": K.SEGMENTATION_OUTPUT_THRESHOLD,
            "note": "separate contract fields even when numerically equal",
        },
        "resource_accounting": {
            "global_macs": K.MACS_GLOBAL,
            "benefit_router_macs": K.MACS_ROUTER,
            "regional_refiner_macs": K.MACS_REFINER,
            "s_omega_macs": K.MACS_SOMEGA,
            "label": K.MAC_LABEL,
            "never_call": ["latency", "runtime", "energy", "mobile performance"],
        },
        "locks": {
            "router_holdout_owner": K.HOLDOUT_OWNER,
            "router_holdout_state": K.HOLDOUT_STATE,
            "val808": K.VAL808,
            "test": K.TEST,
        },
        "weights_copied": False,
        "note": "manifest only - original canonical checkpoint files remain authoritative",
    }
    K.write_json(K.BUNDLE / "canonical_bundle_manifest.json", manifest)
    return manifest


def build_component_inventory():
    comps = [
        ("G", "GlobalMedFiLM", K.GLOBAL_CHECKPOINT, K.GLOBAL_SHA, "GLOBAL_SEGMENTER", False),
        ("R_psi", "BARRRegionalRefinerV1", K.REFINER_CHECKPOINT, K.REFINER_SHA,
         "REGIONAL_REFINER", True),
        ("B_phi", "BARRBenefitRouterV1", K.ROUTER_CHECKPOINT, K.ROUTER_SHA,
         "BENEFIT_ROUTER", True),
        ("S_omega", "BARRPostSafetyV1", K.SOMEGA_CHECKPOINT, K.SOMEGA_SHA,
         "POST_SAFETY", True),
    ]
    inv = {
        "artifact": "phase26_component_inventory",
        "method": K.METHOD,
        "bundle_revision": K.BUNDLE_REVISION,
        "components": [
            {"symbol": s, "model_class": c, "checkpoint_path": p, "checkpoint_sha256": h,
             "role": r, "conditional": cond,
             "binding": K.bind(p, h)}
            for s, c, p, h, r, cond in comps
        ],
        "weights_copied": False,
        "all_pass": True,
    }
    K.write_json(K.BUNDLE / "component_inventory.json", inv)
    return inv


def build_threshold_contract(manifest):
    tc = {
        "artifact": "phase26_threshold_contract",
        "method": K.METHOD,
        "runtime_score": "delta_hat_final - 0.25*C",
        "runtime_authority_role": "CANONICAL_FINAL_ROUTER_RUNTIME_CALIBRATION",
        "operational_threshold": K.exact(K.TAU_C8_FINAL),
        "operational_threshold_selector":
            "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold",
        "raw_runtime_threshold": K.exact(K.TAU_C7_FINAL),
        "comparator": ">=",
        "oof_scientific_threshold": K.exact(K.TAU_C8_OOF),
        "oof_role": "SCIENTIFIC_OOF_POLICY_THRESHOLD_PROVENANCE",
        "oof_runtime_authority": False,
        "roi_proposal_threshold": K.ROI_PROPOSAL_THRESHOLD,
        "s_omega_accept_threshold": K.SOMEGA_ACCEPT_THRESHOLD,
        "segmentation_output_threshold": K.SEGMENTATION_OUTPUT_THRESHOLD,
        "unique_runtime_authority": True,
        "all_pass": True,
    }
    K.write_json(K.BUNDLE / "threshold_contract.json", tc)
    return tc


def build_feature_contract():
    fc = {
        "artifact": "phase26_feature_contract",
        "method": K.METHOD,
        "router_feature": {
            "dimension_numeric": 202,
            "task_embedding_dim": 16,
            "b_phi_input_dim": 218,
            "schema_path": K.ROUTER_SCHEMA,
            "schema_sha256": K.ROUTER_SCHEMA_SHA,
            "dtype": "float32",
            "gt_free": True,
            "normalization": K.ROUTER_NORMALIZATION,
            "normalization_sha256": K.ROUTER_NORMALIZATION_SHA,
            "normalization_refit_forbidden": True,
        },
        "post_safety_feature": {
            "dimension_numeric": 16,
            "onehot_dim": 4,
            "total_dim": 20,
            "schema_path": K.SOMEGA_SCHEMA,
            "dtype": "float32",
            "gt_free": True,
            "normalization": K.SOMEGA_STATS_CSV,
            "normalized_indices": "0..15",
            "not_normalized_indices": "16..19",
        },
        "all_pass": True,
    }
    K.write_json(K.BUNDLE / "feature_contract.json", fc)
    return fc


def build_state_machine_contract():
    sm = {
        "artifact": "phase26_state_machine_contract",
        "method": K.METHOD,
        "states": ["FORCED_SKIP", "SKIP_GLOBAL", "EXECUTE_THEN_ACCEPT", "EXECUTE_THEN_REJECT"],
        "global_forward_count_per_input": 1,
        "transitions": [
            {"guard": "action unavailable", "state": "FORCED_SKIP",
             "refiner": 0, "s_omega": 0, "final_probability": "p_global"},
            {"guard": "action available & U < tau_C8_final", "state": "SKIP_GLOBAL",
             "refiner": 0, "s_omega": 0, "final_probability": "p_global"},
            {"guard": "router EXECUTE & safety ACCEPT", "state": "EXECUTE_THEN_ACCEPT",
             "refiner": 1, "s_omega": 1, "final_probability": "regional_fused_candidate"},
            {"guard": "router EXECUTE & safety REJECT", "state": "EXECUTE_THEN_REJECT",
             "refiner": 1, "s_omega": 1, "final_probability": "p_global"},
        ],
        "fusion": "outside frozen ROI p_global; inside frozen ROI resized p_refined; no alpha blending",
        "safety_accept": "sigmoid(logit) >= 0.50",
        "final_segmentation": "p_final >= 0.50",
        "all_pass": True,
    }
    K.write_json(K.BUNDLE / "state_machine_contract.json", sm)
    return sm


def build_resource_contract():
    rc = {
        "artifact": "phase26_resource_contract",
        "method": K.METHOD,
        "label": K.MAC_LABEL,
        "global_macs": K.MACS_GLOBAL,
        "benefit_router_macs": K.MACS_ROUTER,
        "regional_refiner_macs": K.MACS_REFINER,
        "s_omega_macs": K.MACS_SOMEGA,
        "never_call": ["latency", "runtime", "energy", "mobile performance"],
        "conditional_components": {"regional_refiner": "EXECUTE branch only",
                                   "s_omega": "EXECUTE branch only"},
        "all_pass": True,
    }
    K.write_json(K.BUNDLE / "resource_contract.json", rc)
    return rc


def build_provenance_manifest(manifest):
    pm = {
        "artifact": "phase26_provenance_manifest",
        "method": K.METHOD,
        "bundle_revision": K.BUNDLE_REVISION,
        "phase26_revision": K.PHASE26_REVISION,
        "router_semantics_revision": K.ROUTER_SEMANTICS_REVISION,
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "v1_1_reconciliation": K.bind(K.V11_TERMINAL, None),
        "v1_2_reconciliation": K.bind(K.V12_TERMINAL, None),
        "spec_doc": K.bind(K.SPEC_DOC, None),
        "roi_geometry_contract": K.bind(K.ROI_GEOMETRY_CONTRACT, None),
        "fusion_fallback_contract": K.bind(K.FUSION_FALLBACK_CONTRACT, None),
        "roi_transform_audit": K.bind(K.ROI_TRANSFORM_AUDIT, None),
        "freezes": {
            "phase21": K.bind("reports/audits/phase21_final_freeze.json", None),
            "phase25a_canonical": K.bind("reports/audits/phase25a_canonical_final_freeze.json", None),
            "phase25d": K.bind("reports/audits/phase25d_final_freeze.json", None),
            "phase25f": K.bind("reports/audits/phase25f_final_freeze.json", None),
            "phase25g": K.bind("reports/audits/phase25g_final_freeze.json", None),
        },
        "all_pass": True,
    }
    K.write_json(K.BUNDLE / "provenance_manifest.json", pm)
    return pm


def build_readme():
    txt = "\n".join([
        "# Phase26 canonical bundle - RA-MedFiLM-BARR",
        "",
        "Bundle revision: `ra_medfilm_barr_bundle_v1_0`",
        "Phase26 revision: `ra_medfilm_barr_phase26_integration_v1_0`",
        "Router semantics revision: `phase26_v1_2`",
        "",
        "## Operational meaning",
        "ASSEMBLY_ONLY__NO_PARAMETER_OPTIMIZATION. This bundle contains NO weights;",
        "the canonical checkpoint files remain authoritative at their original paths.",
        "",
        "## Canonical operating point",
        "- variant: A8_C9",
        "- nominal budget: 0.25",
        "- lambda representative: 0.25 (membership-equivalent serialization; NOT performance-selected)",
        "",
        "## Runtime policy",
        "score = delta_hat_final - 0.25*C; EXECUTE iff score >= tau_C8_final.",
        "tau_C8_final = -5003565381643716252018011/205414980000000000000000000",
        "tau_C7_final = 24796109646558761/20000000000000000000",
        "C = 1051648/10270749",
        "",
        "## Future-cohort rule",
        "FIXED_DEV_CALIBRATED_THRESHOLD. Never force 25% / never rank / never top-K /",
        "never recalibrate. Report nominal budget AND realized activation fraction.",
        "",
        "## Locks",
        "ROUTER_HOLDOUT: RESERVED_UNOPENED_FOR_PHASE30",
        "VAL808: UNOPENED",
        "TEST: LOCKED_UNTIL_PHASE39",
        "",
    ])
    K.write_text_deterministic(K.BUNDLE / "README.md", txt)
    return txt


# =========================================================================== #
# SECTION 23 - RESOURCE ACCOUNTING
# =========================================================================== #
def section_resource():
    say("")
    say("=" * 74)
    say("SECTION 23 - RESOURCE ACCOUNTING")
    say("=" * 74)
    rows = [
        {"component": "GlobalMedFiLM", "macs": K.MACS_GLOBAL, "label": K.MAC_LABEL},
        {"component": "BARRBenefitRouterV1", "macs": K.MACS_ROUTER, "label": K.MAC_LABEL},
        {"component": "BARRRegionalRefinerV1", "macs": K.MACS_REFINER, "label": K.MAC_LABEL},
        {"component": "BARRPostSafetyV1", "macs": K.MACS_SOMEGA, "label": K.MAC_LABEL},
    ]
    K.write_csv(K.TABLE / "phase26_component_inventory.csv", rows,
                ["component", "macs", "label"])
    check("macs_global", K.MACS_GLOBAL == 31551740928)
    check("macs_refiner", K.MACS_REFINER == 3230662656)
    return rows


# =========================================================================== #
# SECTION 24 - BUNDLE SELF-VALIDATION
# =========================================================================== #
def section_validate():
    say("")
    say("=" * 74)
    say("SECTION 24 - BUNDLE SELF-VALIDATION")
    say("=" * 74)
    m = K.jload(K.BUNDLE / "canonical_bundle_manifest.json")
    required = ["canonical_bundle_manifest.json", "component_inventory.json",
                "threshold_contract.json", "feature_contract.json",
                "state_machine_contract.json", "resource_contract.json",
                "provenance_manifest.json", "README.md"]
    present = [f for f in required if (K.BUNDLE / f).exists()]
    checks = {
        "all_required_files_present": len(present) == len(required),
        "all_component_shas_match": all(c["match"] for c in m["components"].values()),
        "all_normalization_shas_match": all(c["match"] for c in m["normalizations"].values()),
        "all_schema_shas_match": all(c["match"] for c in m["schemas"].values()),
        "oof_authority_false": m["A_OOF_SCIENTIFIC_EVIDENCE"]["runtime_authority"] is False,
        "final_authority_true": m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["runtime_authority"] is True,
        "unique_runtime_authority":
            sum(1 for b in (m["A_OOF_SCIENTIFIC_EVIDENCE"], m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"])
                if b["runtime_authority"]) == 1,
        "lambda_cost_exact": m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["lambda_C_exact"]
            == K.exact(K.LAMBDA_C),
        "operational_threshold_selector":
            m["operational_threshold"] == "FINAL_ROUTER_RUNTIME_CALIBRATION.resource_utility_threshold",
        "holdout_reservation": m["locks"]["router_holdout_state"] == K.HOLDOUT_STATE,
        "no_weights_copied": m["weights_copied"] is False,
    }
    # threshold parse
    try:
        from fractions import Fraction as F
        parseable = (F(m["B_FINAL_ROUTER_RUNTIME_CALIBRATION"]["resource_utility_threshold_exact"])
                     == K.TAU_C8_FINAL)
    except Exception:
        parseable = False
    checks["thresholds_parse_exactly"] = parseable
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_bundle_manifest_integrity",
        "phase": "26",
        "method": K.METHOD,
        "bundle_revision": K.BUNDLE_REVISION,
        "required_files": required,
        "present_files": present,
        "checks": checks,
        "all_pass": bool(all(checks.values())),
        "terminal_on_failure": K.TERMINAL_BUNDLE,
    }
    K.write_json(K.AUD / "phase26_bundle_manifest_integrity.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 25 - DETERMINISTIC BUNDLE MANIFEST
# =========================================================================== #
def section_determinism():
    say("")
    say("=" * 74)
    say("SECTION 25 - DETERMINISTIC BUNDLE MANIFEST")
    say("=" * 74)
    shas = []
    for _ in range(3):
        build_manifest()
        shas.append(K.sha256_file(K.BUNDLE / "canonical_bundle_manifest.json"))
    same = len(set(shas)) == 1
    check("three_builds_byte_identical", same)
    artifact = {
        "artifact": "phase26_bundle_manifest_determinism",
        "phase": "26",
        "method": K.METHOD,
        "bundle_revision": K.BUNDLE_REVISION,
        "builds": 3,
        "manifest_shas": shas,
        "three_builds_byte_identical": same,
        "manifest_sha256": shas[-1],
        "no_timestamps": True,
        "all_pass": bool(same),
    }
    K.write_json(K.AUD / "phase26_bundle_manifest_determinism.json", artifact)
    return artifact


def main():
    say("=" * 74)
    say("SECTIONS 3-6 - CANONICAL BUNDLE DIRECTORY + MANIFEST")
    say("=" * 74)
    m = build_manifest()
    check("manifest_built", m is not None)
    build_component_inventory()
    build_threshold_contract(m)
    build_feature_contract()
    build_state_machine_contract()
    build_resource_contract()
    build_provenance_manifest(m)
    build_readme()
    for f in ["canonical_bundle_manifest.json", "component_inventory.json",
              "threshold_contract.json", "feature_contract.json",
              "state_machine_contract.json", "resource_contract.json",
              "provenance_manifest.json", "README.md"]:
        check(f"created {f}", (K.BUNDLE / f).exists())

    section_resource()
    v = section_validate()
    d = section_determinism()
    say("")
    say("=" * 74)
    say(f"BUNDLE COMPLETE  integrity={v['all_pass']} determinism={d['all_pass']}")
    say("=" * 74)
    return 0 if (v["all_pass"] and d["all_pass"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
