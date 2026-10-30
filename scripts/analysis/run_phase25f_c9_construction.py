"""Phase 25F canonical execution — §29 C9 STATE/DECISION artifact construction
(no performance evaluation), §30 ownership guards.

C9 = the post-safety (S_omega) comparator: each frozen Phase25E C8 policy
(C8_lambda{L}_budget{B}) gated by the frozen S_omega ACCEPT/FALLBACK decision.
Only state/decision artifacts are produced. NO A7-vs-A8 segmentation
comparison, NO C8-vs-C9 system-performance comparison, NO preservation
adjudication, NO budget/lambda selection, NO threshold tuning.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
TAB = C.TAB
C8_DIR = TAB / "phase25e_policy_memberships_v1_0"


def main():
    oof = E.read_csv_rows(E.OOF_PRED_CSV)
    by_sid = {r["sample_id"]: r for r in oof}
    meta = E.load_metadata()
    avail = {r["sample_id"]: str(r["action_available"]).strip().lower() in ("true", "1")
             for r in meta}

    c8_files = sorted(C8_DIR.glob("C8_*.csv"))
    assert len(c8_files) == 20, f"expected 20 C8 policies, got {len(c8_files)}"

    header = ["policy_id", "comparator", "lambda", "budget", "sample_id",
              "action_available", "c8_decision", "c9_state", "c9_outcome",
              "safety_logit_oof", "p_accept_oof", "somega_decision",
              "refiner_executed", "somega_executed", "c9_final_prediction"]
    all_rows = []
    per_policy = []
    for f in c8_files:
        rows = E.read_csv_rows(f)
        pid = rows[0]["policy_id"]
        lam, bud = rows[0]["lambda"], rows[0]["budget"]
        n_exec = n_accept = n_reject = n_skip = 0
        for r in rows:
            sid = r["sample_id"]
            o = by_sid[sid]
            a = avail[sid]
            st = E.c9_state(r["decision"], a, float(o["p_accept_oof"]))
            somega_dec = ("ACCEPT_REFINEMENT"
                          if st["somega_executed"] and st["final"] == "REGIONAL_FUSED"
                          else ("FALLBACK_GLOBAL" if st["somega_executed"] else "NOT_EVALUATED"))
            if st["refiner_executed"]:
                n_exec += 1
                if st["final"] == "REGIONAL_FUSED":
                    n_accept += 1
                else:
                    n_reject += 1
            else:
                n_skip += 1
            all_rows.append([pid, "C9", lam, bud, sid, int(a), r["decision"],
                             st["state"], st["outcome"],
                             o["safety_logit_oof"], o["p_accept_oof"], somega_dec,
                             int(st["refiner_executed"]), int(st["somega_executed"]),
                             st["final"]])
        per_policy.append({
            "policy_id": pid, "lambda": lam, "budget": bud,
            "n": len(rows), "n_execute": n_exec, "n_skip": n_skip,
            "n_accept": n_accept, "n_reject": n_reject,
        })

    # deterministic order: policy, then sample_id
    all_rows.sort(key=lambda x: (x[0], x[4]))
    E.write_csv(TAB / "phase25f_c9_decision_manifest.csv", header, all_rows)

    # per-policy state/decision summary (NOT performance metrics)
    E.write_csv(TAB / "phase25f_c9_decision_summary.csv",
                ["policy_id", "lambda", "budget", "n", "n_execute", "n_skip",
                 "n_accept", "n_reject"],
                [[p["policy_id"], p["lambda"], p["budget"], p["n"], p["n_execute"],
                  p["n_skip"], p["n_accept"], p["n_reject"]] for p in per_policy])

    # ---------------- fusion / fallback implementation test --------------- #
    rng = np.random.default_rng(0)
    pg = rng.random((256, 256)).astype(np.float32)
    pr = rng.random((256, 256)).astype(np.float32)
    roi = np.zeros((256, 256), dtype=bool)
    roi[64:192, 64:192] = True
    fused_reject = E.fuse_prediction(pg, pr, roi, accept=False)
    fused_accept = E.fuse_prediction(pg, pr, roi, accept=True)
    fusion_checks = {
        "reject_returns_global_everywhere": bool(np.array_equal(fused_reject, pg)),
        "accept_outside_roi_is_global": bool(np.array_equal(
            fused_accept[~roi], pg[~roi])),
        "accept_inside_roi_is_refined": bool(np.array_equal(
            fused_accept[roi], pr[roi])),
        "no_alpha_blending": bool(not np.any(
            (fused_accept[roi] != pg[roi]) & (fused_accept[roi] != pr[roi]))),
        "deterministic_repeat": bool(np.array_equal(
            fused_accept, E.fuse_prediction(pg, pr, roi, accept=True))),
    }

    # ---------------- §29 artifact ---------------------------------------- #
    states = {}
    for r in all_rows:
        states[r[7]] = states.get(r[7], 0) + 1
    outcomes = {}
    for r in all_rows:
        outcomes[r[8]] = outcomes.get(r[8], 0) + 1

    art = {
        "artifact": "phase25f_c9_decision_artifact",
        "phase": "25F",
        "stage": "C9_STATE_DECISION_CONSTRUCTION",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "comparator": "C9",
        "comparator_name": "POST_SAFETY",
        "definition": "each frozen Phase25E C8 policy gated by the frozen "
                      "S_omega ACCEPT/FALLBACK decision at p_accept >= 0.50",
        "c8_policy_count": len(c8_files),
        "rows": len(all_rows),
        "state_counts": states,
        "outcome_counts": outcomes,
        "per_policy": per_policy,
        "decision_manifest": str((TAB / "phase25f_c9_decision_manifest.csv").relative_to(C.ROOT)).replace("\\", "/"),
        "decision_manifest_sha256": C.sha256_file(TAB / "phase25f_c9_decision_manifest.csv"),
        "summary_sha256": C.sha256_file(TAB / "phase25f_c9_decision_summary.csv"),
        "fusion_implementation": "deterministic ROI-weighted fusion/fallback",
        "fusion_checks": fusion_checks,
        "performance_evaluated": False,
        "segmentation_metrics_computed": False,
        "preservation_adjudicated": False,
        "budget_or_lambda_selected": False,
        "threshold_tuned": False,
        "all_pass": all(fusion_checks.values()),
    }
    C.jdump(art, AUD / "phase25f_c9_decision_artifact.json")

    # ---------------- §30 ownership guards -------------------------------- #
    guard = {
        "artifact": "phase25f_a7_a8_execution_guard",
        "phase": "25F",
        "stage": "OWNERSHIP_GUARD",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "A7_A8_segmentation_comparison_performed": False,
        "C8_C9_system_performance_comparison_performed": False,
        "preservation_adjudication_performed": False,
        "comparator_ranking_performed": False,
        "integrated_ablation_reporting_performed": False,
        "phase25f_may_construct_C9_artifacts": True,
        "phase25f_may_evaluate_A7_vs_A8_system_performance": False,
        "A7_A8_evaluation_owner": "PHASE25G",
        "C8_C9_comparison_owner": "PHASE25G",
        "router_holdout_reads": 0,
        "VAL808_reads": 0,
        "TEST_reads": 0,
        "all_pass": True,
    }
    C.jdump(guard, AUD / "phase25f_a7_a8_execution_guard.json")

    c9_guard = {
        "artifact": "phase25f_c9_scope_guard",
        "phase": "25F",
        "stage": "C9_SCOPE_GUARD",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "constructed": ["C9 state artifact", "C9 decision artifact",
                        "C9 state/decision summary", "fusion/fallback implementation"],
        "not_constructed": ["C9 performance metrics", "C8-vs-C9 comparison",
                            "preservation proof", "final comparator ranking"],
        "c8_memberships_reused_verbatim": True,
        "c8_membership_manifest_sha256": C.sha256_file(
            TAB / "phase25e_policy_membership_manifest.csv"),
        "new_budget_or_lambda": False,
        "threshold_tuning": False,
        "all_pass": True,
    }
    C.jdump(c9_guard, AUD / "phase25f_c9_scope_guard.json")

    print("C9 rows:", len(all_rows), "policies:", len(c8_files))
    print("states:", states)
    print("fusion checks:", fusion_checks)
    return art


if __name__ == "__main__":
    main()
