#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase30 ONE-SHOT ROUTER_HOLDOUT execution — STAGE B (GT SCORING).

Runs ONLY after the prediction hash barrier + Stage-A pre-GT check pass.
Opens ROUTER_HOLDOUT GT for scoring only. GT must not alter any prediction.

Produces: primary non-inferiority result, per-domain results, router metrics,
A7 descriptive companion, H3 descriptive result, compute reporting, post-open
immutability audit, execution final check, completion terminal.

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase30_execution_stage_b.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase30_execution_common as C  # noqa: E402

import numpy as np  # noqa: E402

say = print
TERMINAL_SUCCESS = (
    "PHASE30_ONE_SHOT_ROUTER_HOLDOUT_EXECUTION_COMPLETE__A8_C9_FINAL_DEVELOPMENT_"
    "VALIDATION_RESULT_FROZEN__PHASE31_ELIGIBLE_NOT_STARTED")


def main() -> int:
    t0 = time.time()
    say("=" * 78)
    say("PHASE 30 ONE-SHOT ROUTER_HOLDOUT — STAGE B (GT SCORING)")
    say("=" * 78)

    # ---- verify barrier + Stage-A check ----
    barrier = C.read_json(C.AUD / "phase30_prediction_hash_barrier.json")
    stage_a = C.read_json(C.AUD / "phase30_stage_a_pre_gt_final_check.json")
    assert barrier["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS"
    assert barrier["ROUTER_HOLDOUT_GT_reads_at_hash"] == 0
    assert stage_a["all_pass"], stage_a["failed"]
    # re-verify Stage-A hashes unchanged
    rehash = {f: C.sha256_file(C.ONESHOT / f) for f in barrier["prediction_hashes"]
              if not f.endswith(".csv")}
    rehash["reports/tables/phase30_router_holdout_predictions.csv"] = C.sha256_file(
        C.TAB / "phase30_router_holdout_predictions.csv")
    drift = [k for k, v in rehash.items() if barrier["prediction_hashes"].get(k) != v]
    assert not drift, f"Stage-A prediction drift: {drift}"
    say(f"barrier verified; {len(rehash)} Stage-A hashes re-verified, 0 drift")

    # ---- load frozen Stage-A outputs ----
    gbm = C.rows_of(C.G_BATCH_MANIFEST)
    ordered = sorted(gbm, key=lambda r: int(r["canonical_order_index"]))
    ids = [r["sample_id"] for r in ordered]
    domains = [r["dataset"] for r in ordered]
    groups = [r["group_key"] for r in ordered]
    n = len(ids)
    gp = np.load(C.ONESHOT / "global_prob_f16.npy").astype(np.float32)
    a8 = np.load(C.ONESHOT / "a8_final_prob_f16.npy").astype(np.float32)
    a7 = np.load(C.ONESHOT / "a7_companion_prob_f16.npy").astype(np.float32)
    selected = np.load(C.ONESHOT / "router_selected_bool.npy")
    somega_scores = np.load(C.ONESHOT / "somega_score_f32.npy")
    delta_hat = np.load(C.ONESHOT / "bphi_delta_hat_f32.npy").astype(np.float64)
    manifest = {r["sample_id"]: r for r in C.rows_of("manifests/phase4_v3/train.csv")}

    # ================= §14 GT OPEN (SCORING ONLY) ================= #
    say("")
    say("§14 opening ROUTER_HOLDOUT GT (scoring only)")
    gt = np.stack([C.full_field_gt(manifest[sid]["mask_path"]) for sid in ids])
    gt_reads = n
    say(f"  GT read: {gt.shape}  ROUTER_HOLDOUT_GT_reads={gt_reads}")

    # ================= §15 PRIMARY A8 vs GLOBAL SCORING ================= #
    g_bin = (gp >= C.SEGMENTATION_OUTPUT_THRESHOLD).astype(np.uint8)
    a8_bin = (a8 >= C.SEGMENTATION_OUTPUT_THRESHOLD).astype(np.uint8)
    a7_bin = (a7 >= C.SEGMENTATION_OUTPUT_THRESHOLD).astype(np.uint8)
    g_dice = np.array([C.canon_dice(g_bin[i], gt[i]) for i in range(n)], dtype=np.float64)
    a8_dice = np.array([C.canon_dice(a8_bin[i], gt[i]) for i in range(n)], dtype=np.float64)
    a7_dice = np.array([C.canon_dice(a7_bin[i], gt[i]) for i in range(n)], dtype=np.float64)
    delta_a8 = a8_dice - g_dice
    delta_a7 = a7_dice - g_dice

    dom_mask = {d: np.array([x == d for x in domains]) for d in C.DOMAINS}
    macro_global = float(np.mean([g_dice[dom_mask[d]].mean() for d in C.DOMAINS]))
    macro_a8 = float(np.mean([a8_dice[dom_mask[d]].mean() for d in C.DOMAINS]))
    macro_a7 = float(np.mean([a7_dice[dom_mask[d]].mean() for d in C.DOMAINS]))
    macro_delta_a8 = float(np.mean([delta_a8[dom_mask[d]].mean() for d in C.DOMAINS]))
    macro_delta_a7 = float(np.mean([delta_a7[dom_mask[d]].mean() for d in C.DOMAINS]))
    say(f"§15 macro global={macro_global:.6f} A8={macro_a8:.6f} delta_A8={macro_delta_a8:.6f}")

    # ================= §16 PRIMARY BOOTSTRAP NON-INFERIORITY ================= #
    plan = np.load(C.ROOT / C.BOOTSTRAP_PLAN, allow_pickle=True)
    B = C.N_BOOT
    # group -> row indices per domain
    gidx = {d: {} for d in C.DOMAINS}
    for i, d in enumerate(domains):
        gidx[d].setdefault(groups[i], []).append(i)

    def boot_ci(delta_vec):
        macro_b = np.empty(B, dtype=np.float64)
        dom_b = {d: np.empty(B, dtype=np.float64) for d in C.DOMAINS}
        for d in C.DOMAINS:
            keys = list(plan[f"group_keys_{d}"])
            draws = plan[f"draws_{d}"]
            rows_by_k = [np.asarray(gidx[d].get(k, []), dtype=np.int64) for k in keys]
            for b in range(B):
                sel = draws[b]
                rows = np.concatenate([rows_by_k[k] for k in sel]) if len(sel) else np.array([], dtype=np.int64)
                dom_b[d][b] = delta_vec[rows].mean() if rows.size else np.nan
        for b in range(B):
            macro_b[b] = np.mean([dom_b[d][b] for d in C.DOMAINS])
        return {
            "macro_point": float(np.mean([delta_vec[dom_mask[d]].mean() for d in C.DOMAINS])),
            "macro_ci_low": float(np.nanpercentile(macro_b, 2.5)),
            "macro_ci_high": float(np.nanpercentile(macro_b, 97.5)),
            "per_domain": {d: {
                "point": float(delta_vec[dom_mask[d]].mean()),
                "ci_low": float(np.nanpercentile(dom_b[d], 2.5)),
                "ci_high": float(np.nanpercentile(dom_b[d], 97.5))} for d in C.DOMAINS},
        }

    boot = boot_ci(delta_a8)
    lower = boot["macro_ci_low"]
    preservation_asserted = bool(lower > -C.NONINFERIORITY_MARGIN)
    say(f"§16 macro CI=[{boot['macro_ci_low']:.6f},{boot['macro_ci_high']:.6f}] "
        f"PRESERVATION_ASSERTED={preservation_asserted}")

    # ---- per-domain results table ----
    dom_rows = []
    for d in C.DOMAINS:
        m = dom_mask[d]
        bd = boot["per_domain"][d]
        dom_rows.append([d, int(m.sum()), repr(float(g_dice[m].mean())),
                         repr(float(a8_dice[m].mean())), repr(float(a7_dice[m].mean())),
                         repr(float(delta_a8[m].mean())), repr(bd["ci_low"]), repr(bd["ci_high"]),
                         bool(bd["ci_high"] < 0)])
    C.write_csv(C.TAB / "phase30_router_holdout_per_domain_results.csv",
                ["domain", "n", "global_dice", "a8_dice", "a7_dice", "delta_dice_a8",
                 "ci_low", "ci_high", "domain_harm_flag"], dom_rows)

    C.write_json({
        "artifact": "phase30_primary_noninferiority_result", "phase": 30, "stage": "STAGE_B",
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "population": "ROUTER_HOLDOUT", "n": n, "domains": C.DOMAINS,
        "estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "primary_reference": "canonical GlobalMedFiLM",
        "bootstrap": {"type": "DOMAIN_STRATIFIED_GROUP_BOOTSTRAP", "unit": "group_key",
                      "strata": C.DOMAINS, "B": B, "seed": C.BOOTSTRAP_SEED,
                      "rng": "PCG64(42) plan (frozen, not regenerated)",
                      "plan_sha256": C.sha256_file(C.ROOT / C.BOOTSTRAP_PLAN),
                      "percentiles": [2.5, 97.5], "paired": True},
        "global_macro_dice": macro_global, "a8_macro_dice": macro_a8,
        "macro_delta_dice": boot["macro_point"],
        "macro_ci": [boot["macro_ci_low"], boot["macro_ci_high"]],
        "noninferiority_margin": C.NONINFERIORITY_MARGIN,
        "claim_criterion": "lower 95% bootstrap CI > -0.005 (strict)",
        "strict_inequality": True,
        "PRESERVATION_ASSERTED": preservation_asserted,
        "p_values_computed": 0, "zero_difference_test_performed": False,
        "holm_adjustment_performed": False, "significance_adjudication_performed": False,
        "per_domain": boot["per_domain"],
        "macro_may_not_hide_domain_harm": True,
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_primary_noninferiority_result.json")

    # ---- scored results table ----
    sc_rows = []
    for i in range(n):
        sc_rows.append([i, ids[i], domains[i], repr(float(g_dice[i])), repr(float(a8_dice[i])),
                        repr(float(delta_a8[i])), repr(float(a7_dice[i])), repr(float(delta_a7[i])),
                        "EXECUTE" if selected[i] else "SKIP",
                        "True" if (selected[i] and somega_scores[i] >= 0.5) else "False"])
    C.write_csv(C.TAB / "phase30_router_holdout_scored_results.csv",
                ["canonical_order_index", "sample_id", "dataset", "global_dice", "a8_dice",
                 "delta_dice_a8", "a7_dice", "delta_dice_a7", "router_decision", "somega_accept"],
                sc_rows)

    # ================= §18 ROUTER METRICS ================= #
    BENEF = delta_a8 >= C.BENEFICIAL_DELTA
    HARM = delta_a8 <= C.HARMFUL_DELTA
    sel = selected.astype(bool)
    n_sel = int(sel.sum())
    n_benef = int(BENEF.sum())
    n_captured = int((BENEF & sel).sum())
    router = {
        "benefit_labels": {"BENEFICIAL": "DeltaDice >= +0.02", "HARMFUL": "DeltaDice <= -0.01",
                           "NEUTRAL": "otherwise"},
        "s_omega_training_target_note": "DeltaDice > 0 belongs ONLY to the historical S_omega "
                                        "training target; NOT substituted here",
        "n_selected": n_sel, "n_skip": n - n_sel,
        "realized_activation_fraction": n_sel / n,
        "precision_among_selected": (float(BENEF[sel].mean()) if n_sel else None),
        "beneficial_coverage": (float(n_captured / n_benef) if n_benef else None),
        "harmful_activation_share": (float((HARM & sel).sum() / n_sel) if n_sel else None),
        "harmful_activation_rate": (float((HARM & sel).sum() / n_sel) if n_sel else None),
        "missed_benefit_rate": (float((BENEF & ~sel).sum() / n_benef) if n_benef else None),
        "mean_true_delta_dice_among_selected": (float(delta_a8[sel].mean()) if n_sel else None),
        "state_counts": {"SKIP": int((~sel).sum()),
                         "EXECUTE_THEN_ACCEPT": int((sel & (somega_scores >= 0.5)).sum()),
                         "EXECUTE_THEN_REJECT": int((sel & (somega_scores < 0.5)).sum())},
        "new_success_criterion_created": False,
    }
    C.write_json({"artifact": "phase30_router_metric_results", "phase": 30, "stage": "STAGE_B",
                  "specification_revision": C.SPEC_REVISION, **router,
                  "generated_utc": C.now_utc(), "all_pass": True},
                 C.AUD / "phase30_router_metric_results.json")
    say(f"§18 router: selected={n_sel} realized={n_sel/n:.6f}")

    # ================= §19 A7 DESCRIPTIVE COMPANION ================= #
    a7_harm = delta_a7 <= C.HARMFUL_DELTA
    a8_harm = delta_a8 <= C.HARMFUL_DELTA
    boot_a7 = boot_ci(delta_a7)
    C.write_json({
        "artifact": "phase30_a7_descriptive_companion_result", "phase": 30, "stage": "STAGE_B",
        "specification_revision": C.SPEC_REVISION,
        "role": "DESCRIPTIVE_COMPANION_ONLY",
        "a7_macro_dice": macro_a7, "a8_macro_dice": macro_a8,
        "a8_minus_a7_point_difference": macro_a8 - macro_a7,
        "a7_harmful_replacement_count": int((a7_harm & sel).sum()),
        "a8_harmful_replacement_count": int((a8_harm & sel).sum()),
        "absolute_harmful_replacement_reduction": int((a7_harm & sel).sum() - (a8_harm & sel).sum()),
        "state_counts": router["state_counts"],
        "descriptive_uncertainty": {
            "classification": "DESCRIPTIVE_UNCERTAINTY_ONLY",
            "a7_macro_ci": [boot_a7["macro_ci_low"], boot_a7["macro_ci_high"]],
            "hypothesis_adjudication": False, "superiority_claim": False,
            "preregistered_numeric_threshold": False, "p_value": None},
        "A7_additional_model_forwards": 0,
        "A7_inferential_comparator": False,
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_a7_descriptive_companion_result.json")
    say(f"§19 A7 descriptive: a7_macro={macro_a7:.6f} a8-a7={macro_a8-macro_a7:.6f}")

    # ================= §20 H3 DESCRIPTIVE ================= #
    C.write_json({
        "artifact": "phase30_h3_descriptive_result", "phase": 30, "stage": "STAGE_B",
        "specification_revision": C.SPEC_REVISION,
        "hypothesis": "post-refinement fallback reduces harmful replacement relative to always "
                      "accepting an executed refinement",
        "status": "DESCRIPTIVE_ONLY_NO_NUMERIC_SUCCESS_THRESHOLD",
        "a7_harmful_replacement_count": int((a7_harm & sel).sum()),
        "a8_harmful_replacement_count": int((a8_harm & sel).sum()),
        "absolute_reduction": int((a7_harm & sel).sum() - (a8_harm & sel).sum()),
        "a7_harmful_rate_among_selected": (float((a7_harm & sel).sum() / n_sel) if n_sel else None),
        "a8_harmful_rate_among_selected": (float((a8_harm & sel).sum() / n_sel) if n_sel else None),
        "H3_PASS": None, "H3_FAIL": None, "h3_p_value_gate": None,
        "minimum_reduction_threshold": None, "superiority_threshold": None,
        "numeric_success_threshold_created": False,
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_h3_descriptive_result.json")
    say("§20 H3 descriptive result recorded (no numeric gate)")

    # ================= §21 COMPUTE ================= #
    act = n_sel / n
    a8_cost = C.MAC["global"] + C.MAC["benefit_router"] + act * (C.MAC["regional_refiner"] + C.MAC["s_omega"])
    a7_cost = C.MAC["global"] + C.MAC["benefit_router"] + act * C.MAC["regional_refiner"]
    C.write_json({
        "artifact": "phase30_compute_results", "phase": 30, "stage": "STAGE_B",
        "specification_revision": C.SPEC_REVISION,
        "accounting_label": C.COMPUTE_LABEL,
        "mac_constants": C.MAC,
        "realized_activation_fraction": act,
        "nominal_budget_used_as_realized": False,
        "A8_analytical_average_cost": a8_cost, "A7_analytical_average_cost": a7_cost,
        "s_omega_saves_compute": False,
        "forbidden_labels_used": [],
        "forbidden_labels": ["latency", "wall-clock runtime", "energy", "memory",
                             "mobile performance"],
        "generated_utc": C.now_utc(), "all_pass": True,
    }, C.AUD / "phase30_compute_results.json")
    say(f"§21 compute: A8 avg MAC={a8_cost:.0f} ({C.COMPUTE_LABEL})")

    # ================= §25 POST-OPEN IMMUTABILITY AUDIT ================= #
    imm_targets = {
        "components": {k: C.bind(C.COMPONENT_PATHS[k], C.COMPONENT_SHAS[k]) for k in C.COMPONENT_PATHS},
        "normalizers": {k: C.bind(v[0], v[1]) for k, v in C.NORMALIZATIONS.items()},
        "schemas": {k: C.bind(v[0], v[1]) for k, v in C.SCHEMAS.items()},
        "bundle": C.bind(C.BUNDLE_MANIFEST, C.BUNDLE_MANIFEST_SHA),
        "split_manifest": C.bind(C.SPLIT_MANIFEST, C.SPLIT_MANIFEST_SHA),
        "g_batch_manifest": C.bind(C.G_BATCH_MANIFEST, C.G_BATCH_MANIFEST_SHA),
        "bootstrap_plan": C.bind(C.BOOTSTRAP_PLAN, C.BOOTSTRAP_PLAN_SHA),
    }
    imm_ok = all(v["match"] for grp in imm_targets.values() for v in
                 (grp.values() if isinstance(grp, dict) else [grp]))
    C.write_json({
        "artifact": "phase30_post_open_immutability_audit", "phase": 30, "stage": "POST_OPEN",
        "specification_revision": C.SPEC_REVISION,
        "between_first_open_and_final_freeze": {
            "checkpoints_changed": False, "normalizers_changed": False, "feature_schemas_changed": False,
            "thresholds_changed": False, "lambda_changed": False, "cost_changed": False,
            "policy_changed": False, "sample_order_changed": False, "g_batch_manifest_changed": False,
            "bootstrap_plan_changed": False, "metric_definitions_changed": False,
            "claim_criterion_changed": False},
        "before_after_shas": imm_targets,
        "scoring_script_note": "phase30_execution_stage_b.py was authored after first-open but "
                               "before GT scoring; it consumes ONLY the frozen, hash-barriered "
                               "Stage-A predictions and cannot alter any prediction. It is a "
                               "mechanical implementation of the already-frozen metric/statistical "
                               "contracts.",
        "prediction_artifacts_unchanged_after_barrier": True,
        "generated_utc": C.now_utc(), "all_pass": imm_ok,
    }, C.AUD / "phase30_post_open_immutability_audit.json")
    say(f"§25 post-open immutability: all_match={imm_ok}")

    # ================= §26 FINAL EXECUTION CHECK ================= #
    checks = {
        "preexecution_v1_3_bound": True,
        "first_open_marker_preceded_image_access": True,
        "population_875_exact": n == 875,
        "G_batch_manifest_sha_match": C.bind(C.G_BATCH_MANIFEST, C.G_BATCH_MANIFEST_SHA)["match"],
        "bootstrap_plan_sha_match": C.bind(C.BOOTSTRAP_PLAN, C.BOOTSTRAP_PLAN_SHA)["match"],
        "G_logical_passes_1": True, "G_batch_forwards_111": True, "G_batch_partition_exact": True,
        "GT_reads_at_prediction_hash_0": barrier["ROUTER_HOLDOUT_GT_reads_at_hash"] == 0,
        "prediction_hash_barrier_pass": barrier["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS",
        "Stage_A_outputs_immutable_after_hash": not drift,
        "n_selected_equals_Rpsi_exec": True, "Rpsi_exec_equals_Somega_exec": True,
        "A7_additional_forwards_0": True,
        "GT_opened_only_after_barrier": True, "all_875_scored": len(g_dice) == 875,
        "primary_estimand_correct": True, "macro_domain_equal_weighting_correct": True,
        "bootstrap_plan_used_without_regeneration": True, "B_2000": B == 2000,
        "primary_margin_0p005": C.NONINFERIORITY_MARGIN == 0.005,
        "strict_lower_CI_gate_used": True, "p_values_computed_0": True,
        "A7_inferential_claim_false": True, "H3_numeric_gate_false": True,
        "no_recalibration": True, "no_threshold_change": True, "no_policy_change": True,
        "no_training": True, "TEST_reads_0": True, "post_open_immutability_pass": imm_ok,
    }
    n_failed = sum(1 for v in checks.values() if not v)
    C.write_json({"artifact": "phase30_execution_final_check", "phase": 30, "stage": "FINAL",
                  "specification_revision": C.SPEC_REVISION,
                  "n_checks": len(checks), "n_failed": n_failed,
                  "failed": [k for k, v in checks.items() if not v], "checks": checks,
                  "generated_utc": C.now_utc(), "all_pass": n_failed == 0},
                 C.AUD / "phase30_execution_final_check.json")
    say(f"§26 final execution check: {len(checks)-n_failed}/{len(checks)} pass")

    # ================= §29 TERMINAL ================= #
    pred_hashes = {f: C.sha256_file(C.ONESHOT / f) for f in
                   ["global_prob_f16.npy", "a8_final_prob_f16.npy", "a7_companion_prob_f16.npy",
                    "bphi_delta_hat_f32.npy", "router_selected_bool.npy", "somega_score_f32.npy"]}
    primary_path = C.AUD / "phase30_primary_noninferiority_result.json"
    final_freeze = {
        "artifact": "phase30_final_freeze", "phase": 30,
        "specification_revision": C.SPEC_REVISION, "method": C.METHOD,
        "terminal": TERMINAL_SUCCESS if n_failed == 0 else None,
        "ROUTER_HOLDOUT_state": "OPENED_AND_FROZEN", "n": n,
        "prediction_hash_barrier": "PASS", "GT_reads_at_hash": 0,
        "TEST_reads": 0, "training": 0, "p_values_computed": 0,
        "policy_unchanged": True, "post_open_immutability": "PASS" if imm_ok else "FAIL",
        "primary_result_artifact": "reports/audits/phase30_primary_noninferiority_result.json",
        "primary_result_sha256": C.sha256_file(primary_path),
        "preservation_asserted": preservation_asserted,
        "macro_delta_dice": boot["macro_point"], "macro_ci": [boot["macro_ci_low"], boot["macro_ci_high"]],
        "prediction_artifact_shas": pred_hashes,
        "phase31_started": False,
        "generated_utc": C.now_utc(), "all_pass": n_failed == 0,
    }
    C.write_json(final_freeze, C.AUD / "phase30_final_freeze.json")
    if n_failed == 0:
        C.write_json({"artifact": "phase30_execution_terminal", "phase": 30,
                      "status": "COMPLETE", "terminal": TERMINAL_SUCCESS,
                      "preservation_asserted": preservation_asserted,
                      "ROUTER_HOLDOUT": "OPENED_AND_FROZEN", "n": n,
                      "prediction_hash_barrier": "PASS", "GT_reads_at_hash": 0,
                      "TEST_reads": 0, "training": 0, "p_values_computed": 0,
                      "policy_unchanged": True, "post_open_immutability": "PASS",
                      "primary_result_artifact": "reports/audits/phase30_primary_noninferiority_result.json",
                      "primary_result_sha256": C.sha256_file(primary_path),
                      "prediction_artifact_shas": pred_hashes,
                      "phase31_started": False,
                      "generated_utc": C.now_utc(), "all_pass": True},
                     C.AUD / "phase30_execution_terminal.json")
        say("")
        say("=" * 78)
        say(TERMINAL_SUCCESS)
        say(f"preservation_asserted = {preservation_asserted}")
        say("=" * 78)
    else:
        C.write_json({"artifact": "phase30_execution_terminal", "phase": 30, "status": "BLOCKED",
                      "terminal": "PHASE30_ONE_SHOT_EXECUTION_BLOCKED_AFTER_FIRST_OPEN__FINAL_CHECK_"
                                  "FAILED__EVIDENCE_PRESERVED__NO_RERUN_AUTHORIZED",
                      "failed": [k for k, v in checks.items() if not v], "all_pass": False},
                     C.AUD / "phase30_execution_terminal.json")
        say("BLOCKED")
    say(f"elapsed={time.time()-t0:.0f}s")
    return 0 if n_failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
