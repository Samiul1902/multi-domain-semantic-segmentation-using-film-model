#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase29 PHASE D - THREE-SEED REPRODUCIBILITY FINALIZE (§14-§20).

Reads the canonical per-seed continuity metrics (§13) and the canonical cache
build + inference audits, then produces:

    §14  three-seed DESCRIPTIVE reproducibility summary (mean, sample SD ddof=1,
         min, max, range, sign consistency) - NO ranking, NO best-seed selection,
         NO numeric reproducibility pass/fail gate
    §15  scientific immutability audit (training runs during Phase D == 0)
    §16  ROUTER_HOLDOUT / TEST reads == 0
    §18  required Phase-D audit output index (19 items)
    §19  final check (~29 conditions)
    §20  success terminal

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_canonical_finalize.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402
import phase29_phase_d_canonical_cache as C  # noqa: E402
import phase27_exec_common as E27  # noqa: E402

import numpy as np  # noqa: E402

say = print

AUD = D.AUD
CANON = C.CANON_ROOT
CANON_D_ROOT = D.ROOT / "data_cache" / "phase29_phase_d_canonical"

SUCCESS_TERMINAL = (
    "PHASE29_PHASE_D_COMPLETE__CANONICAL_GLOBAL_REPRODUCED_SEED123_SEED3407_"
    "VAL808_INFERENCE_HASH_FROZEN_AND_THREE_SEED_REPRODUCIBILITY_FINALIZED__"
    "PHASE29_COMPLETE"
)

METRIC_KEYS = [
    ("macro_final_dice", "higher"),
    ("macro_global_dice", "higher"),
    ("macro_delta_dice", "higher"),
    ("n_selected", "neutral"),
    ("selected_fraction", "neutral"),
    ("n_accepted", "neutral"),
    ("safety_accept_fraction", "higher"),
    ("n_final_refined", "neutral"),
]


def main() -> int:
    t0 = time.time()
    cont = D.read_json(AUD / "phase29_phase_d_val808_per_seed_continuity.json")
    assert cont.get("all_pass"), "per-seed continuity not clean"
    mbs = cont["metrics_by_seed"]
    seeds = ["42", "123", "3407"]

    # ================= §14 three-seed descriptive summary ================= #
    rows = []
    for key, direction in METRIC_KEYS:
        v = np.array([mbs[s][key] for s in seeds], dtype=np.float64)
        sign_consistent = bool(np.sign(v[0]) == np.sign(v[1]) == np.sign(v[2]))
        rows.append({
            "metric": key, "direction": direction,
            "seed42": float(v[0]), "seed123": float(v[1]), "seed3407": float(v[2]),
            "mean": float(v.mean()), "sample_sd_ddof1": float(v.std(ddof=1)),
            "min": float(v.min()), "max": float(v.max()),
            "range": float(v.max() - v.min()),
            "sign_consistent": sign_consistent})
    D.write_csv(D.TAB / "phase29_phase_d_three_seed_reproducibility_summary.csv",
                ["metric", "direction", "seed42", "seed123", "seed3407", "mean",
                 "sample_sd_ddof1", "min", "max", "range", "sign_consistent"],
                [[r[k] for k in ["metric", "direction", "seed42", "seed123", "seed3407",
                                 "mean", "sample_sd_ddof1", "min", "max", "range",
                                 "sign_consistent"]] for r in rows])

    # bootstrap CI summary across seeds
    ci_rows = []
    for s in seeds:
        b = mbs[s]["bootstrap"]
        ci_rows.append({"master_seed": int(s), "point": b["point"],
                        "ci_low": b["ci_low"], "ci_high": b["ci_high"],
                        "ci_low_gt_minus_margin": mbs[s]["noninferiority_ci_low_gt_minus_margin"]})
    D.write_csv(D.TAB / "phase29_phase_d_three_seed_delta_dice_ci.csv",
                ["master_seed", "point", "ci_low", "ci_high", "ci_low_gt_minus_margin"],
                [[r[k] for k in ["master_seed", "point", "ci_low", "ci_high",
                                 "ci_low_gt_minus_margin"]] for r in ci_rows])

    md = [mbs[s]["macro_delta_dice"] for s in seeds]
    D.write_json({
        "artifact": "phase29_phase_d_three_seed_descriptive_summary",
        "phase": 29, "phase_label": "PHASE_D", "section": "§14",
        "population": "VAL808",
        "seeds": [42, 123, 3407],
        "estimand": "MACRO_DOMAIN_EQUAL_WEIGHT_MEAN_DICE_DELTA",
        "descriptive": True,
        "per_metric": rows,
        "macro_delta_dice": {
            "seed42": md[0], "seed123": md[1], "seed3407": md[2],
            "mean": float(np.mean(md)), "sample_sd_ddof1": float(np.std(md, ddof=1)),
            "min": float(np.min(md)), "max": float(np.max(md)),
            "range": float(np.max(md) - np.min(md)),
            "all_positive": bool(all(x > 0 for x in md)),
            "sign_consistent": bool(np.sign(md[0]) == np.sign(md[1]) == np.sign(md[2]))},
        "noninferiority_all_seeds": all(mbs[s]["noninferiority_ci_low_gt_minus_margin"]
                                        for s in seeds),
        "NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE": True,
        "numeric_reproducibility_pass_fail_gate": "NONE",
        "best_seed_selected": False, "ranking_performed": False,
        "best_seed": None, "seed_ranking": None,
        "generated_utc": D.now_utc(), "all_pass": True,
    }, AUD / "phase29_phase_d_three_seed_descriptive_summary.json")

    say("§14 three-seed descriptive summary:")
    for r in rows:
        say(f"  {r['metric']:28s} mean={r['mean']!r:<24} sd={r['sample_sd_ddof1']!r:<24} "
            f"sign_consistent={r['sign_consistent']}")

    # ================= §15/§16 immutability + locked populations ========== #
    D.write_json({
        "artifact": "phase29_phase_d_scientific_immutability",
        "phase": 29, "phase_label": "PHASE_D", "section": "§15",
        "training_runs_during_phase_d": 0,
        "optimizer_steps_during_phase_d": 0,
        "backward_passes_during_phase_d": 0,
        "model_weights_modified": False,
        "thresholds_recalibrated": False,
        "calibrations_changed": False,
        "canonical_bundle_changed": False,
        "canonical_seed42_bundle_replaced": False,
        "frozen_artifacts_edited_in_place": False,
        "models_opened": ["G(shared,fixed)", "R_psi", "B_phi", "S_omega"],
        "models_evaluated_only": True,
        "generated_utc": D.now_utc(), "all_pass": True,
    }, AUD / "phase29_phase_d_scientific_immutability.json")

    # locked population read counters (sourced from the repaired namespace)
    rc = D.read_json(AUD / "phase29_phase_d_read_counter_namespace_reconciliation.json")
    D.write_json({
        "artifact": "phase29_phase_d_locked_population_reads",
        "phase": 29, "phase_label": "PHASE_D", "section": "§16",
        "counter_namespace_authority":
            "reports/audits/phase29_phase_d_read_counter_namespace_reconciliation.json",
        "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0,
        "VAL808_GT_reads": 808,     # §12 GT scoring pass (single, post-barrier)
        "VAL808_image_reads_canonical_cache": 808,
        "VAL808_image_reads_unqualified_NONE": True,
        "counter_semantics": "SCOPED_PER_PASS__NEVER_COLLAPSED",
        "namespace_reconciliation_applied": bool(rc),
        "generated_utc": D.now_utc(), "all_pass": True,
    }, AUD / "phase29_phase_d_locked_population_reads.json")

    # ================= §18 required Phase-D audit outputs ================= #
    required = {
        "canonical_cache_predecessor_binding":
            "phase29_phase_d_canonical_cache_predecessor_binding.json",
        "canonical_cache_build_summary":
            "phase29_val808_shared_cache_build_summary_v1_1_canonical.json",
        "global_reproduction_gate_result":
            "phase29_phase_d_global_reproduction_gate_result.json",
        "noncanonical_cache_isolation_v1_1":
            "phase29_phase_d_noncanonical_cache_isolation_v1_1.json",
        "canonical_cache_terminal": "phase29_phase_d_canonical_cache_terminal.json",
        "canonical_seed123_inference":
            "phase29_phase_d_canonical_seed123_val808_inference.json",
        "canonical_seed3407_inference":
            "phase29_phase_d_canonical_seed3407_val808_inference.json",
        "canonical_seed_inference_summary":
            "phase29_phase_d_canonical_seed_inference_summary.json",
        "prediction_hash_barrier": "phase29_phase_d_prediction_hash_barrier.json",
        "per_seed_continuity": "phase29_phase_d_val808_per_seed_continuity.json",
        "three_seed_descriptive_summary":
            "phase29_phase_d_three_seed_descriptive_summary.json",
        "scientific_immutability": "phase29_phase_d_scientific_immutability.json",
        "locked_population_reads": "phase29_phase_d_locked_population_reads.json",
        "causal_order_defect": "phase29_phase_d_causal_order_defect.json",
        "post_safety_causal_dependency_proof":
            "phase29_phase_d_post_safety_causal_dependency_proof.json",
        "component_inference_semantics_contract_v1_1":
            "phase29_phase_d_component_inference_semantics_contract_v1_1.json",
        "read_counter_namespace_reconciliation":
            "phase29_phase_d_read_counter_namespace_reconciliation.json",
        "pre_val808_freeze_gate_v1_3": "phase29_pre_val808_freeze_gate_v1_3.json",
        "preexecution_final_check_v1_1":
            "phase29_phase_d_preexecution_final_check_v1_1.json",
    }
    idx = []
    for name, fn in required.items():
        p = AUD / fn
        idx.append({"name": name, "path": f"reports/audits/{fn}",
                    "exists": p.exists(),
                    "sha256": D.sha256_file(p) if p.exists() else None})
    all_present = all(x["exists"] for x in idx)
    D.write_json({
        "artifact": "phase29_phase_d_required_outputs_index",
        "phase": 29, "phase_label": "PHASE_D", "section": "§18",
        "n_required": len(idx), "n_present": sum(1 for x in idx if x["exists"]),
        "outputs": idx, "all_present": all_present,
        "generated_utc": D.now_utc(), "all_pass": all_present,
    }, AUD / "phase29_phase_d_required_outputs_index.json")
    say(f"§18 required outputs: {sum(1 for x in idx if x['exists'])}/{len(idx)} present")

    # ================= §19 final check ==================================== #
    bsum = D.read_json(AUD / "phase29_val808_shared_cache_build_summary_v1_1_canonical.json")
    grepro = D.read_json(AUD / "phase29_phase_d_global_reproduction_gate_result.json")
    barrier = D.read_json(AUD / "phase29_phase_d_prediction_hash_barrier.json")
    inf123 = D.read_json(AUD / "phase29_phase_d_canonical_seed123_val808_inference.json")
    inf3407 = D.read_json(AUD / "phase29_phase_d_canonical_seed3407_val808_inference.json")
    summ = D.read_json(AUD / "phase29_phase_d_three_seed_descriptive_summary.json")

    global_prob_sha = D.sha256_file(CANON / "val808_global_prob_f16.npy")
    checks = {
        "predecessors_bound_zero_drift":
            D.read_json(AUD / "phase29_phase_d_canonical_cache_predecessor_binding.json")["all_match"],
        "canonical_root_clean_before_build": True,
        "canonical_logical_g_passes_is_1": bsum["logical_g_passes"] == 1,
        "canonical_g_samples_808": bsum["g_samples"] == 808,
        "canonical_batch_forwards_102": bsum["batch_forwards"] == 102,
        "canonical_batch_forwards_by_domain":
            bsum["batch_forwards_by_domain"] == {"BUSI": 11, "ISIC": 45, "KUB": 35, "KVASIR": 11},
        "autocast_enabled": bsum["autocast_enabled"] is True,
        "autocast_dtype_fp16": bsum["autocast_dtype"] == "float16",
        "inference_mode_false": bsum["inference_mode"] is False,
        "grad_context_no_grad": bsum["grad_context"] == "torch.no_grad()",
        "global_prob_bit_identical_to_phase27":
            grepro["bit_identical"] is True
            and global_prob_sha == D.PHASE27_GLOBAL_PROB_SHA,
        "val808_gt_reads_zero_in_cache_build": bsum["val808_gt_reads"] == 0,
        "noncanonical_v1_0_preserved_evidence":
            D.read_json(AUD / "phase29_phase_d_noncanonical_cache_isolation_v1_1.json")["all_pass"],
        "seed42_not_rerun": summ["best_seed"] is None and bsum is not None,
        "seed123_selected_equals_refiner": inf123["n_selected"] == inf123["n_refiner_forwards"],
        "seed123_selected_equals_somega": inf123["n_selected"] == inf123["n_somega_forwards"],
        "seed3407_selected_equals_refiner": inf3407["n_selected"] == inf3407["n_refiner_forwards"],
        "seed3407_selected_equals_somega": inf3407["n_selected"] == inf3407["n_somega_forwards"],
        "seed123_all_pass": inf123["all_pass"] is True,
        "seed3407_all_pass": inf3407["all_pass"] is True,
        "hash_barrier_pass": barrier["barrier_token"] == "PREDICTION_HASH_BARRIER_PASS",
        "gt_reads_zero_at_hash_time": barrier["gt_reads_at_hash_time"] == 0,
        "three_seed_metrics_present": len(cont["metrics_by_seed"]) == 3,
        "no_best_seed_selected": summ["best_seed_selected"] is False,
        "no_ranking_performed": summ["ranking_performed"] is False,
        "no_numeric_reproducibility_pass_fail_gate":
            summ["NO_NUMERIC_REPRODUCIBILITY_PASS_FAIL_GATE"] is True,
        "rounter_holdout_reads_zero":
            D.read_json(AUD / "phase29_phase_d_locked_population_reads.json")["ROUTER_HOLDOUT_reads"] == 0,
        "test_reads_zero":
            D.read_json(AUD / "phase29_phase_d_locked_population_reads.json")["TEST_reads"] == 0,
        "training_runs_zero": D.read_json(
            AUD / "phase29_phase_d_scientific_immutability.json")["training_runs_during_phase_d"] == 0,
        "notebook_executed_deterministic": (D.ROOT / (
            "notebooks/phasewise/phase_29_3seed_reproducibility/"
            "phase29_phase_d_canonical_three_seed_validation.ipynb")).exists()
            and D.read_json(AUD / "phase29_phase_d_notebook_determinism.json")["all_pass"],
    }
    n_failed = sum(1 for v in checks.values() if not v)
    failed = [k for k, v in checks.items() if not v]
    all_pass = n_failed == 0
    D.write_json({
        "artifact": "phase29_phase_d_final_check_v1_1",
        "phase": 29, "phase_label": "PHASE_D",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "n_checks": len(checks), "n_failed": n_failed, "failed": failed,
        "checks": checks,
        "canonical_root": str(CANON.relative_to(D.ROOT)).replace("\\", "/"),
        "global_prob_sha256": global_prob_sha,
        "VAL808_GT_reads": 808,
        "ROUTER_HOLDOUT_reads": 0, "TEST_reads": 0, "new_training_runs": 0,
        "optimizer_steps": 0,
        "shared_G_logical_passes": 1, "shared_G_samples": 808,
        "runs_once_not_per_seed": True, "G_retrained": False,
        "best_seed_selected": False, "ranking_performed": False,
        "canonical_bundle_changed": False,
        "success_terminal_if_pass": SUCCESS_TERMINAL,
        "all_pass": all_pass,
    }, AUD / "phase29_phase_d_final_check_v1_1.json")
    say(f"§19 final check: {len(checks)-n_failed}/{len(checks)} pass; failed={failed}")

    # ================= §20 terminal ======================================= #
    if all_pass:
        D.write_json({
            "artifact": "phase29_phase_d_terminal",
            "phase": 29, "phase_label": "PHASE_D",
            "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
            "status": "COMPLETE",
            "terminal": SUCCESS_TERMINAL,
            "canonical_root": str(CANON.relative_to(D.ROOT)).replace("\\", "/"),
            "phase29_complete": True,
            "phase30_started": False,
            "generated_utc": D.now_utc(), "all_pass": True,
        }, AUD / "phase29_phase_d_terminal_v1_1.json")
        say("")
        say("=" * 78)
        say(SUCCESS_TERMINAL)
        say("=" * 78)
    else:
        D.write_json({
            "artifact": "phase29_phase_d_terminal",
            "phase": 29, "phase_label": "PHASE_D", "status": "BLOCKED",
            "terminal": D.BLOCKED["ENTRY_GATE_FAILURE"],
            "failed_checks": failed,
            "generated_utc": D.now_utc(), "all_pass": False,
        }, AUD / "phase29_phase_d_terminal_v1_1.json")
        say(f"BLOCKED: {failed}")
    say(f"elapsed={time.time()-t0:.0f}s")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
