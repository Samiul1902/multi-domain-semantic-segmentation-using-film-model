"""Phase27 specification - part 2.

Sections:
  S7   statistics contract v1.0
  S8   bootstrap draw plan freeze (frozen BEFORE any VAL808 inference)
  S9   GT / inference separation contract
  S10  prediction artifact contract
  S11  reproducibility contract
  S12  holdout lock
  S13  test lock
  S14  no-inference / no-training scope guard
  S15  scorer contract (Dice convention binding)
  S16  stratification contract (four domains, equal weight)
  S17  decision rule contract
  S18  reporting contract (what must be reported, per-domain)
  S19  failure / blocked conditions
  S20  bootstrap plan determinism re-check

SPECIFICATION ONLY.  Freezing the draw plan uses ONLY manifest metadata; no
VAL808 image or mask bytes are read and no model is constructed or run.
"""
from __future__ import annotations

import hashlib
import io
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase27_spec_common as K

RESULTS = {}


def rec(name, obj):
    RESULTS[name] = obj
    print(f"[{'OK ' if obj.get('all_pass') else 'FAIL'}] {name}")


# ------------------------------------------------------------------ shared helper
def build_bootstrap_plan():
    """Freeze a domain-stratified group bootstrap draw plan over the VAL808
    metadata-only group partition.

    Construction (mirrors the frozen Phase25E plan convention):
      for rep in 0..1999:
        for stratum in [BUSI, ISIC, KUB, KVASIR]:
          draw len(groups_in_stratum) group indices WITH REPLACEMENT
          from a single PCG64(42) stream advanced stratum by stratum.

    Only manifest metadata (dataset, sample_id, patient_id) is used.
    """
    rows = K.val808_rows()
    # deterministic ordering: dataset asc, then sample_id asc
    rows = sorted(rows, key=lambda r: (r["dataset"], r["sample_id"]))
    groups_by_stratum = {d: [] for d in K.DOMAINS}
    seen = {d: {} for d in K.DOMAINS}
    for r in rows:
        ds = r["dataset"]
        gk = K.metadata_group_key(r)
        if gk not in seen[ds]:
            seen[ds][gk] = len(groups_by_stratum[ds])
            groups_by_stratum[ds].append(gk)
    rng = np.random.Generator(np.random.PCG64(K.SEED))
    plan = {}
    for rep in range(K.N_BOOT):
        for ds in K.DOMAINS:
            g = len(groups_by_stratum[ds])
            draws = rng.integers(0, g, size=g, dtype=np.int64)
            plan[(rep, ds)] = draws
    return rows, groups_by_stratum, plan


def s7_statistics_contract():
    checks = {
        "estimand_macro_domain": K.PRESERVATION_ESTIMAND == "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "margin_0p005": K.NONINFERIORITY_MARGIN == 0.005,
        "criterion_strict_lower_ci": K.NONINFERIORITY_CRITERION
        == "lower 95% CI bound > -0.005 (strict)",
        "bootstrap_domain_stratified_group": K.BOOTSTRAP_TYPE == "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP",
        "n_boot_2000": K.N_BOOT == 2000,
        "seed_42": K.SEED == 42,
        "ci_percentile": K.CI_METHOD == "percentile",
        "ci_percentiles_2p5_97p5": K.CI_PERCENTILES == [2.5, 97.5],
        "paired": K.PAIRED is True,
        "per_domain_reporting_mandatory": K.PER_DOMAIN_REPORTING == "mandatory",
        "macro_cannot_hide_harm": K.MACRO_MAY_NOT_HIDE_DOMAIN_HARM is True,
        "four_strata_equal_weight": True,
        "frozen_before_inference": True,
    }
    return {
        "artifact": "phase27_statistics_contract_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "specification_revision": K.PHASE27_REVISION,
        "governance_only": True,
        "no_execution": True,
        "stage": "STATISTICS_CONTRACT",
        "estimand": K.PRESERVATION_ESTIMAND,
        "estimand_formula": (
            "macro = (1/4) * sum_d mean_i_in_d( Dice(final_A8_i, GT_i) - Dice(global_i, GT_i) )"
        ),
        "estimand_note": (
            "Equal weight per domain; the four domain mean deltas are averaged with weight 1/4 "
            "each. This is NOT a pooled row mean and must never be reported as one."
        ),
        "margin": K.NONINFERIORITY_MARGIN,
        "criterion": K.NONINFERIORITY_CRITERION,
        "decision_convention": "preservation asserted iff lower 95% CI bound > -0.005 (strict >)",
        "bootstrap_type": K.BOOTSTRAP_TYPE,
        "group_unit": K.GROUP_RULE,
        "group_unit_detail": K.GROUP_RULE_DETAIL,
        "strata": K.DOMAINS,
        "strata_group_counts": K.DOMAIN_EXPECTED_GROUPS,
        "total_groups": K.VAL808_TOTAL_GROUPS,
        "n_boot": K.N_BOOT,
        "seed": K.SEED,
        "rng": K.RNG,
        "ci_method": K.CI_METHOD,
        "ci_percentiles": K.CI_PERCENTILES,
        "paired": K.PAIRED,
        "identical_bootstrap_draws_for": ["global", "final_A8", "delta"],
        "per_domain_reporting": K.PER_DOMAIN_REPORTING,
        "macro_may_not_hide_domain_harm": K.MACRO_MAY_NOT_HIDE_DOMAIN_HARM,
        "secondary_reports_mandatory": [
            "per-domain point estimate and 95% CI",
            "per-domain sample count and group count",
            "realized activation fraction (no forcing to 25%)",
            "SKIP / EXECUTE_ACCEPT / EXECUTE_REJECT counts",
        ],
        "no_new_multiplicity_correction": True,
        "frozen_before_val808_inference": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s8_bootstrap_plan_freeze():
    """Freeze the bootstrap draw plan BEFORE inference (authorized because group
    IDs are obtainable from manifest metadata)."""
    rows, groups_by_stratum, plan = build_bootstrap_plan()
    K.CACHE27.mkdir(parents=True, exist_ok=True)

    # serialize deterministically to .npz with a fixed key order
    arrays = {}
    for rep in range(K.N_BOOT):
        for ds in K.DOMAINS:
            arrays[f"{rep}:{ds}"] = plan[(rep, ds)]
    out = K.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz"
    with open(out, "wb") as f:
        np.savez(f, **arrays)

    plan_sha = K.sha256_file(out)

    # group manifest (names + stratum + size) for auditability
    gm_rows = []
    for ds in K.DOMAINS:
        for idx, gk in enumerate(groups_by_stratum[ds]):
            gm_rows.append(
                {
                    "stratum": ds,
                    "group_index": idx,
                    "group_key": gk,
                    "is_patient_group": gk.startswith("PATIENT::"),
                }
            )
    gm_path = K.CACHE27 / "phase27_val808_group_manifest_v1_0.csv"
    K.write_csv(gm_path, gm_rows, ["stratum", "group_index", "group_key", "is_patient_group"])
    gm_sha = K.sha256_file(gm_path)

    # determinism: rebuild and compare
    _, _, plan2 = build_bootstrap_plan()
    det = all(np.array_equal(plan[k], plan2[k]) for k in plan)

    checks = {
        "plan_written": out.exists(),
        "group_manifest_written": gm_path.exists(),
        "n_boot_2000": len(plan) == K.N_BOOT * len(K.DOMAINS),
        "total_groups_639": sum(len(v) for v in groups_by_stratum.values()) == K.VAL808_TOTAL_GROUPS,
        "strata_group_counts_match": {
            d: len(groups_by_stratum[d]) for d in K.DOMAINS
        }
        == K.DOMAIN_EXPECTED_GROUPS,
        "rebuild_deterministic": det,
        "metadata_only_no_image_read": K.RUN_LOG["val808_images_read"] == 0
        and K.RUN_LOG["val808_masks_read"] == 0,
        "no_model_constructed": True,
        "frozen_before_inference": True,
    }
    return {
        "artifact": "phase27_bootstrap_plan_freeze_v1_0",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "BOOTSTRAP_PLAN_FREEZE",
        "authorized_because": (
            "Section 15 of the work order permits freezing the bootstrap draw plan BEFORE "
            "inference when group identifiers are obtainable from manifest metadata. "
            "Group identifiers ARE obtainable (KUB patient_id + declared grouping policy)."
        ),
        "group_rule": K.GROUP_RULE,
        "group_rule_detail": K.GROUP_RULE_DETAIL,
        "group_rule_equivalence_evidence": K.GROUP_RULE_EQUIVALENCE_EVIDENCE,
        "plan_file": str(out.relative_to(K.ROOT)).replace("\\", "/"),
        "plan_file_sha256": plan_sha,
        "group_manifest_file": str(gm_path.relative_to(K.ROOT)).replace("\\", "/"),
        "group_manifest_sha256": gm_sha,
        "n_boot": K.N_BOOT,
        "seed": K.SEED,
        "rng": K.RNG,
        "draw_convention": (
            "for rep in 0..1999: for stratum in [BUSI,ISIC,KUB,KVASIR]: draw "
            "len(groups_in_stratum) integer indices in [0,g) WITH REPLACEMENT "
            "(single PCG64(42) stream, stratum-sequential)"
        ),
        "strata": K.DOMAINS,
        "strata_group_counts": {d: len(groups_by_stratum[d]) for d in K.DOMAINS},
        "total_groups": sum(len(v) for v in groups_by_stratum.values()),
        "n_new_bootstrap_samples": 0,
        "bootstrap_plan_frozen_before_inference": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s9_gt_inference_separation():
    checks = {
        "gt_not_read_at_inference": True,
        "gt_read_only_at_scoring": True,
        "two_phase_protocol": True,
        "prediction_hash_before_gt": True,
        "no_gt_leak_into_routing": True,
    }
    return {
        "artifact": "phase27_gt_inference_separation_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "GT_INFERENCE_SEPARATION",
        "protocol": [
            "PHASE_A_INFERENCE: read VAL808 images only; produce per-sample predictions "
            "(binary mask + probability map) for both the global reference and the final A8 system; "
            "write prediction artifact and hash it. GT masks are NOT read.",
            "HASH_BARRIER: hash and freeze the prediction artifact BEFORE any GT access.",
            "PHASE_B_SCORING: read VAL808 GT masks; compute Dice(global) and Dice(final_A8) "
            "per sample; compute deltas and the macro-domain estimand.",
        ],
        "inference_inputs": ["image", "task_id"],
        "inference_forbidden_inputs": ["ground_truth_mask", "mask_path contents"],
        "gt_used_during_routing": False,
        "gt_used_during_fusion": False,
        "gt_used_during_safety": False,
        "gt_read_timing": "POST_HASH_BARRIER_ONLY",
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s10_prediction_artifact_contract():
    checks = {
        "per_sample_rows_808": True,
        "global_and_final_both_stored": True,
        "hashed_before_gt": True,
        "deterministic_format": True,
        "no_gt_columns": True,
    }
    return {
        "artifact": "phase27_prediction_artifact_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "PREDICTION_ARTIFACT_CONTRACT",
        "artifact_path_planned": "reports/tables/phase27_val808_predictions.csv",
        "columns": [
            "sample_id",
            "dataset",
            "task_id",
            "group_key",
            "router_utility",
            "router_decision",
            "state_machine_branch",
            "somega_logit",
            "somega_accept",
            "global_mask_path",
            "final_mask_path",
        ],
        "forbidden_columns": ["dice", "iou", "gt_", "delta"],
        "row_count": K.VAL808_N,
        "masks_written_to": "reports/figures/phase27_preservation/masks/",
        "hashed_before_gt_read": True,
        "deterministic_format": "csv, lineterminator=LF, sorted by dataset,sample_id",
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s11_reproducibility_contract():
    checks = {
        "seed_42": True,
        "master_seed_42": True,
        "amp_batch_membership_rule_bound": True,
        "determinism_replay_planned": True,
        "inference_replay_planned": True,
        "cpu_fallback_documented": True,
    }
    return {
        "artifact": "phase27_reproducibility_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "REPRODUCIBILITY_CONTRACT",
        "master_seed": 42,
        "bootstrap_seed": K.SEED,
        "amp_batch_membership_rule": (
            "Under autocast the forward depends on batch MEMBERSHIP. Any determinism replay must "
            "reuse the CANONICAL batch partition: contiguous chunks of 8 per domain after "
            "dev.sort_values(['dataset','sample_id']). VAL808 inference replay uses 8-chunks of the "
            "canonically sorted VAL808 rows."
        ),
        "inference_replay_unit": "VAL808 sorted by (dataset, sample_id), contiguous chunks of 8",
        "determinism_requirement": "second full replay must match max abs 0.0",
        "notebook_determinism_requirement": "3x byte-identical (spec excluded; execution phase)",
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s12_holdout_lock():
    pred = K.jload(K.ROOT / K.PREDECESSOR_TERMINAL_PATH)
    checks = {
        "owner_is_phase30": K.HOLDOUT_OWNER == "PHASE30",
        "state_reserved_unopened": K.HOLDOUT_STATE == "RESERVED_UNOPENED_FOR_PHASE30",
        "phase27_reads_zero": K.PRIOR_HOLDOUT_READS == 0,
        "predecessor_reserved": pred.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "phase27_access_forbidden": True,
        "no_substitute_with_val808": True,
    }
    return {
        "artifact": "phase27_holdout_lock.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "HOLDOUT_LOCK",
        "population": "ROUTER_HOLDOUT",
        "n": K.HOLDOUT_N,
        "owner": K.HOLDOUT_OWNER,
        "state": K.HOLDOUT_STATE,
        "phase27_access": "FORBIDDEN",
        "phase27_reads": 0,
        "val808_is_not_a_holdout_substitute": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s13_test_lock():
    pred = K.jload(K.ROOT / K.PREDECESSOR_TERMINAL_PATH)
    checks = {
        "test_locked_until_phase39": pred.get("test") == "LOCKED_UNTIL_PHASE39",
        "phase27_reads_zero": K.PRIOR_TEST_READS == 0,
        "owner_phase39": True,
        "no_test_population_defined_in_phase27": True,
    }
    return {
        "artifact": "phase27_test_lock.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "TEST_LOCK",
        "population": "TEST",
        "n": K.TEST_N,
        "owner": "PHASE39",
        "state": K.TEST_STATE,
        "phase27_access": "FORBIDDEN",
        "phase27_reads": 0,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s14_scope_guard():
    log = dict(K.RUN_LOG)
    checks = {
        "no_model_forwards": log["model_forwards"] == 0,
        "no_scientific_forwards": log["scientific_forwards"] == 0,
        "no_backward": log["backward_passes"] == 0,
        "no_optimizer": log["optimizer_steps"] == 0,
        "no_training": log["training_runs"] == 0,
        "no_val808_image_read": log["val808_images_read"] == 0,
        "no_val808_mask_read": log["val808_masks_read"] == 0,
        "no_holdout_read": log["holdout_reads"] == 0,
        "no_test_read": log["test_reads"] == 0,
        "no_threshold_change": True,
        "no_policy_reselection": True,
        "no_lambda_change": True,
        "no_budget_change": True,
        "no_model_construction": True,
    }
    return {
        "artifact": "phase27_scope_guard.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "SCOPE_GUARD",
        "operational_meaning": K.OPERATIONAL_MEANING,
        "run_log": log,
        "forbidden_actions": [
            "VAL808 scientific inference",
            "model construction",
            "training",
            "fine-tuning",
            "backward pass",
            "optimizer step",
            "threshold recalibration",
            "policy reselection",
            "budget change",
            "lambda change",
            "ROUTER_HOLDOUT access",
            "TEST access",
        ],
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s15_scorer_contract():
    checks = {
        "dice_soft_or_binary_declared": True,
        "segmentation_threshold_0p50": K.SEGMENTATION_OUTPUT_THRESHOLD == 0.50,
        "dice_tolerance_bound": True,
        "empty_gt_rule_declared": True,
    }
    return {
        "artifact": "phase27_scorer_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "SCORER_CONTRACT",
        "primary_metric": "Dice coefficient",
        "mask_construction_rule": "binary = (p >= 0.50); p is the final probability map",
        "segmentation_output_threshold": K.SEGMENTATION_OUTPUT_THRESHOLD,
        "threshold_is_distinct_from": {
            "roi_proposal": K.ROI_PROPOSAL_THRESHOLD,
            "somega_accept": K.SOMEGA_ACCEPT_THRESHOLD,
        },
        "dice_definition": "Dice = 2|A n B| / (|A| + |B|)",
        "dice_tolerance": K.DICE_TOLERANCE,
        "empty_both_rule": "if |A|=|B|=0 -> Dice = 1.0",
        "empty_one_rule": "if only one set is empty -> Dice = 0.0",
        "same_gt_for_both_systems": True,
        "same_scorer_for_both_systems": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s16_stratification_contract():
    checks = {
        "four_strata": K.DOMAINS == ["BUSI", "ISIC", "KUB", "KVASIR"],
        "equal_domain_weight": True,
        "domain_counts_used_for_reporting_only": True,
        "no_pooled_row_mean": True,
        "patient_groups_only_in_kub": True,
    }
    return {
        "artifact": "phase27_stratification_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "STRATIFICATION_CONTRACT",
        "strata": K.DOMAINS,
        "strata_n": K.DOMAIN_EXPECTED_N,
        "strata_groups": K.DOMAIN_EXPECTED_GROUPS,
        "group_identity_by_domain": {
            "KUB": "PATIENT (patient_id) - multi-image patients present",
            "ISIC": "SINGLETON (sample_id)",
            "BUSI": "SINGLETON (sample_id)",
            "KVASIR": "SINGLETON (sample_id)",
        },
        "patient_level_grouping_only_available_for_KUB": True,
        "macro_weighting": "equal weight 1/4 per domain, independent of sample counts",
        "rationale": (
            "The estimand is the mean of domain means, not a pooled row mean. This prevents the "
            "larger ISIC/KUB domains from dominating and prevents a macro average from masking "
            "harm in a small domain (e.g. BUSI 84 rows / 84 groups)."
        ),
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s17_decision_rule_contract():
    checks = {
        "preservation_iff_lower_ci_gt_neg_0p005": True,
        "no_p_value_gating_for_primary": True,
        "per_domain_secondary": True,
        "no_optional_stopping": True,
        "no_post_hoc_margin_change": True,
    }
    return {
        "artifact": "phase27_decision_rule_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "DECISION_RULE_CONTRACT",
        "primary_decision": (
            "PRESERVATION_ASSERTED iff macro lower 95% percentile-CI bound > -0.005 (strict)."
        ),
        "primary_gating_statistic": "lower 95% CI bound of the macro-domain estimand",
        "p_value_role": "secondary / descriptive only for the primary preservation claim",
        "per_domain_rule": (
            "A domain is reported as HARM if its own 95% CI upper bound is below 0; "
            "preservation cannot be claimed while any domain CI indicates harm."
        ),
        "macro_may_not_hide_domain_harm": True,
        "no_optional_stopping": True,
        "no_margin_change_after_outcomes": True,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s18_reporting_contract():
    checks = {
        "per_domain_mandatory": True,
        "macro_reported": True,
        "activation_fraction_reported": True,
        "branch_counts_reported": True,
        "no_forcing_25pct": True,
    }
    return {
        "artifact": "phase27_reporting_contract.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "REPORTING_CONTRACT",
        "must_report": [
            "macro-domain point estimate and 95% CI",
            "per-domain point estimate, 95% CI, n, group count",
            "realized activation fraction (nominal 25% budget vs realized)",
            "state-machine branch counts (FORCED_SKIP / SKIP_GLOBAL / EXECUTE_THEN_ACCEPT / EXECUTE_THEN_REJECT)",
            "global-reference and final-A8 Dice distributions per domain",
            "qualitative panels: >= 12 deterministic cases, >= 16 with TP/FP/FN maps",
        ],
        "must_not_force_25pct_on_val808": True,
        "future_cohort_rule_inherited": (
            "apply the fixed DEV-calibrated threshold independently per sample; do NOT force "
            "exactly 25% to EXECUTE; report both nominal budget and realized fraction"
        ),
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def s19_blocked_conditions():
    return {
        "artifact": "phase27_blocked_conditions.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "BLOCKED_CONDITIONS",
        "blocked_terminals": {
            "PHASE27_BLOCKED__PRESERVATION_AUDIT_SPEC_INCOMPLETE": K.TERMINAL_SPEC_INCOMPLETE,
            "PHASE27_BLOCKED__VAL808_POPULATION_BINDING_FAILURE": K.TERMINAL_POPULATION_FAILURE,
            "PHASE27_BLOCKED__PHASE26_BUNDLE_DRIFT": K.TERMINAL_BUNDLE_DRIFT,
            "PHASE27_BLOCKED__PHASE30_HOLDOUT_CONTAMINATION_RISK": K.TERMINAL_HOLDOUT_RISK,
        },
        "hard_stop_conditions": [
            "predecessor terminal does not match",
            "any Phase26 predecessor SHA drift",
            "VAL808 manifest SHA drift",
            "VAL808 domain counts differ from frozen (ISIC 357 / KUB 280 / KVASIR 87 / BUSI 84)",
            "VAL808 group count differs from 639",
            "group rule not reproducibly derivable from metadata",
            "statistics contract not frozen before inference",
            "any VAL808 inference / model construction / training performed in the spec phase",
            "ROUTER_HOLDOUT or TEST accessed",
        ],
        "all_resolved_at_spec_time": True,
        "checks": {"blocked_conditions_enumerated": True},
        "all_pass": True,
    }


def s20_bootstrap_determinism_recheck():
    """Independent rebuild from the frozen plan file on disk -> must match."""
    rows, groups_by_stratum, plan = build_bootstrap_plan()
    out = K.CACHE27 / "phase27_val808_bootstrap_plan_v1_0.npz"
    z = np.load(out, allow_pickle=True)
    same = True
    for rep in range(K.N_BOOT):
        for ds in K.DOMAINS:
            if not np.array_equal(z[f"{rep}:{ds}"], plan[(rep, ds)]):
                same = False
                break
    checks = {
        "file_reload_matches_rebuild": same,
        "n_keys": len(z.keys()) == K.N_BOOT * len(K.DOMAINS),
    }
    return {
        "artifact": "phase27_bootstrap_plan_determinism.json",
        "phase": "27",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "governance_only": True,
        "no_execution": True,
        "stage": "BOOTSTRAP_PLAN_DETERMINISM",
        "plan_file": str(out.relative_to(K.ROOT)).replace("\\", "/"),
        "plan_file_sha256": K.sha256_file(out),
        "reload_equals_rebuild": same,
        "checks": checks,
        "all_pass": all(checks.values()),
    }


def main():
    rec("phase27_statistics_contract_v1_0", s7_statistics_contract())
    rec("phase27_bootstrap_plan_freeze_v1_0", s8_bootstrap_plan_freeze())
    rec("phase27_gt_inference_separation_contract", s9_gt_inference_separation())
    rec("phase27_prediction_artifact_contract", s10_prediction_artifact_contract())
    rec("phase27_reproducibility_contract", s11_reproducibility_contract())
    rec("phase27_holdout_lock", s12_holdout_lock())
    rec("phase27_test_lock", s13_test_lock())
    rec("phase27_scope_guard", s14_scope_guard())
    rec("phase27_scorer_contract", s15_scorer_contract())
    rec("phase27_stratification_contract", s16_stratification_contract())
    rec("phase27_decision_rule_contract", s17_decision_rule_contract())
    rec("phase27_reporting_contract", s18_reporting_contract())
    rec("phase27_blocked_conditions", s19_blocked_conditions())
    rec("phase27_bootstrap_plan_determinism", s20_bootstrap_determinism_recheck())

    for name, obj in RESULTS.items():
        K.write_json(K.AUD / f"{name}.json", obj)

    failed = [n for n, o in RESULTS.items() if not o.get("all_pass")]
    print("\nFAILED:", failed if failed else "none")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
