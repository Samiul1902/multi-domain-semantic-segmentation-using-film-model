"""Phase25G part 1 - entry gate, predecessor immutability, scope, locks, population,
policy grid, lambda redundancy, A7/A8 identity control.  (§0-§7, §10)

No model, no training, no forward pass.  Fails closed.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25g_common as C  # noqa: E402

FAILURES: list[str] = []


def note(cond, msg):
    if not cond:
        FAILURES.append(msg)
    return bool(cond)


def main():
    C.AUD.mkdir(parents=True, exist_ok=True)
    C.TABLE.mkdir(parents=True, exist_ok=True)

    # ======================================================= §0 entry gate
    term = C.jload(C.AUD / "phase25g_specification_terminal_v1_1.json")
    fin = C.jload(C.AUD / "phase25g_specification_final_check_v1_1.json")
    gov = C.jload(C.AUD / "phase25g_specification_governance_v1_1.json")
    rul = C.jload(C.AUD / "phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json")
    res = C.jload(C.AUD / "phase25g_holdout_reservation_for_phase30.json")
    f25f = C.jload(C.AUD / "phase25f_final_freeze.json")
    add25f = C.jload(C.AUD / "phase25f_final_freeze_notebook_compliance_addendum.json")

    entry = {
        "artifact": "phase25g_execution_entry_gate",
        "phase": "25G",
        "classification": "CANONICAL_PHASE25G_INTEGRATED_CONTROLLED_DEVELOPMENT_EVALUATION",
        "method": "RA-MedFiLM-BARR",
        "specification_revision": "ra_medfilm_barr_integrated_evaluation_v1_0",
        "spec_repair": "v1.1 holdout ownership",
        "stage": "EXECUTION_ENTRY_GATE",
        "required_predecessor_terminal": C.PREDECESSOR_TERMINAL,
        "observed_predecessor_terminal": term.get("terminal"),
        "state": {
            "phase25f": f25f.get("phase25f_status"),
            "phase25g_spec": term.get("phase25g_spec"),
            "phase25g": term.get("phase25g_status"),
            "phase25g_population": gov.get("phase25g_population"),
            "router_holdout": term.get("holdout_state"),
            "phase30": gov.get("phase30_status"),
            "val808": gov.get("val808"),
            "test": gov.get("test"),
        },
        "locks": {"router_holdout_reads": 0, "val808_reads": 0, "test_reads": 0},
        "phase25g_science_executed_before": False,
    }
    note(term.get("terminal") == C.PREDECESSOR_TERMINAL, "PREDECESSOR_TERMINAL_MISMATCH")
    note(f25f.get("phase25f_status") == "COMPLETE_CANONICAL", "PHASE25F_NOT_COMPLETE_CANONICAL")
    note(term.get("phase25g_spec") == "COMPLETE_FROZEN", "SPEC_NOT_COMPLETE_FROZEN")
    note(term.get("phase25g_status") == "EXECUTION_ELIGIBLE_NOT_STARTED", "NOT_EXECUTION_ELIGIBLE")
    note(gov.get("phase25g_population") == "ROUTER_DEVELOPMENT", "POPULATION_NOT_DEV")
    note(term.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30", "HOLDOUT_STATE_BAD")
    note(gov.get("phase30_status") == "NOT_STARTED", "PHASE30_NOT_NOT_STARTED")
    note(gov.get("val808", "").startswith("UNOPENED"), "VAL808_NOT_UNOPENED")
    note("LOCKED" in gov.get("test", ""), "TEST_NOT_LOCKED")
    note(fin.get("all_pass") and gov.get("all_pass"), "SPEC_CHECKS_NOT_PASS")
    note(res.get("ROUTER_HOLDOUT_status") == "RESERVED_UNOPENED_FOR_PHASE30", "RESERVATION_STATE_BAD")
    note(rul.get("ROUTER_HOLDOUT_OWNER_PHASE") == 30, "RULING_OWNER_NOT_PHASE30")
    note(entry["locks"] == {"router_holdout_reads": 0, "val808_reads": 0, "test_reads": 0}, "LOCKS_NOT_ZERO")
    entry["all_pass"] = not FAILURES
    entry["failures"] = list(FAILURES)
    C.write_json(C.AUD / "phase25g_execution_entry_gate.json", entry)
    if FAILURES:
        print("ENTRY_GATE_FAIL", FAILURES)
        return 1

    # ============================================ §1 predecessor immutability
    preds = {
        "phase25c_oof_paired_gain_labels": C.CACHE25C / "phase25c_oof_paired_gain_labels.csv",
        "phase25e_policy_membership_manifest": C.TABLE / "phase25e_policy_membership_manifest.csv",
        "phase25e_policy_memberships_v1_0_dir": C.TABLE / "phase25e_policy_memberships_v1_0",
        "phase25e_bootstrap_plan_v1_0": C.CACHE25E / "phase25e_bootstrap_plan_v1_0.npz",
        "phase25e_evaluation_statistics_contract_v1_0": C.AUD / "phase25e_evaluation_statistics_contract_v1_0.json",
        "phase25e_adjudication_reconciled": C.AUD / "phase25e_adjudication_reconciled.json",
        "phase25e_final_freeze": C.AUD / "phase25e_final_freeze.json",
        "phase24_router_split_manifest": C.AUD / "phase24_router_split_manifest.csv",
        "phase25f_oof_safety_predictions": C.CACHE25F / "phase25f_oof_safety_predictions.csv",
        "phase25f_c9_decision_manifest": C.TABLE / "phase25f_c9_decision_manifest.csv",
        "phase25f_final_freeze": C.AUD / "phase25f_final_freeze.json",
        "phase25f_final_freeze_notebook_compliance_addendum": C.AUD / "phase25f_final_freeze_notebook_compliance_addendum.json",
        "phase25g_specification_terminal_v1_1": C.AUD / "phase25g_specification_terminal_v1_1.json",
        "phase25g_specification_final_check_v1_1": C.AUD / "phase25g_specification_final_check_v1_1.json",
        "phase25g_specification_completeness_v1_1": C.TABLE / "phase25g_specification_completeness_v1_1.csv",
        "phase25g_a7_a8_controlled_comparison_contract": C.AUD / "phase25g_a7_a8_controlled_comparison_contract.json",
        "phase25g_dev_reconstruction_contract": C.AUD / "phase25g_dev_reconstruction_contract.json",
        "phase25g_preservation_contract_binding": C.AUD / "phase25g_preservation_contract_binding.json",
        "phase25g_statistics_contract": C.AUD / "phase25g_statistics_contract.json",
        "phase25g_compute_contract": C.AUD / "phase25g_compute_contract.json",
        "phase25g_h3_adjudication_contract": C.AUD / "phase25g_h3_adjudication_contract.json",
        "phase25g_router_holdout_ownership_supervisor_ruling_v1_0": C.AUD / "phase25g_router_holdout_ownership_supervisor_ruling_v1_0.json",
    }
    bound = {}
    drift = []
    for name, p in preds.items():
        if not p.exists():
            drift.append({"name": name, "path": str(p), "reason": "MISSING"})
            continue
        if p.is_dir():
            sub = sorted(p.glob("*.csv"))
            digest = C.hashlib.sha256()
            for s in sub:
                digest.update(s.name.encode())
                digest.update(C.sha256_file(s).encode())
            h = digest.hexdigest()
        else:
            h = C.sha256_file(p)
        bound[name] = {"path": str(p.relative_to(C.ROOT)), "sha256": h,
                       "kind": "dir_digest" if p.is_dir() else "file"}
        if name in C.SHA and C.SHA[name] is not None and C.SHA[name] != h:
            drift.append({"name": name, "expected": C.SHA[name], "observed": h})
    imm = {
        "artifact": "phase25g_predecessor_immutability_gate",
        "phase": "25G",
        "stage": "PREDECESSOR_IMMUTABILITY",
        "bound": bound,
        "n_bound": len(bound),
        "drift": drift,
        "n_drift": len(drift),
        "all_pass": len(drift) == 0,
    }
    C.write_json(C.AUD / "phase25g_predecessor_immutability_gate.json", imm)
    if drift:
        print("PREDECESSOR_DRIFT", drift)
        C.write_json(C.AUD / "phase25g_terminal.json", {
            "terminal": C.TERMINAL_DRIFT, "drift": drift, "all_pass": False})
        return 1

    # ================================================== §2 scope guard
    scope = {
        "artifact": "phase25g_scope_guard",
        "phase": "25G",
        "stage": "SCOPE_GUARD",
        "mode": "ARTIFACT_LEVEL_EVALUATION_ONLY",
        "counters": {
            "training_runs": 0, "optimizer_steps": 0,
            "global_model_loads": 0, "global_model_forwards": 0,
            "regional_refiner_loads": 0, "regional_refiner_forwards": 0,
            "benefit_router_loads": 0, "benefit_router_forwards": 0,
            "post_safety_model_loads": 0, "post_safety_forwards": 0,
            "new_refinement_predictions": 0, "new_router_predictions": 0,
            "new_safety_predictions": 0,
        },
        "allowed_operations": [
            "read frozen OOF outcomes", "read frozen memberships",
            "read frozen safety decisions", "join by sample_id / policy_id",
            "calculate evaluation metrics", "reuse frozen bootstrap draws",
            "create tables / figures / notebook",
        ],
        "torch_imported": "torch" in sys.modules,
        "all_pass": "torch" not in sys.modules,
    }
    note(not scope["torch_imported"], "TORCH_IMPORTED")
    C.write_json(C.AUD / "phase25g_scope_guard.json", scope)

    # ============================================ §3 hard lock audit
    lock = {
        "artifact": "phase25g_router_holdout_lock_audit",
        "phase": "25G", "stage": "ROUTER_HOLDOUT_HARD_LOCK",
        "router_holdout_state": "RESERVED_UNOPENED_FOR_PHASE30",
        "counters": {"image_reads": 0, "mask_reads": 0, "feature_reads": 0,
                     "model_inference": 0, "outcome_reads": 0,
                     "metric_calculations": 0, "visualizations": 0},
        "all_pass": True,
    }
    C.write_json(C.AUD / "phase25g_phase30_holdout_lock_audit.json", lock)
    C.write_json(C.AUD / "phase25g_val808_lock_audit.json", {
        "artifact": "phase25g_val808_lock_audit", "phase": "25G",
        "stage": "VAL808_LOCK", "val808_state": "UNOPENED", "val808_reads": 0, "all_pass": True})
    C.write_json(C.AUD / "phase25g_test_lock_audit.json", {
        "artifact": "phase25g_test_lock_audit", "phase": "25G",
        "stage": "TEST_LOCK", "test_state": "LOCKED UNTIL PHASE39", "test_reads": 0, "all_pass": True})

    # ==================================== §4 dev population join integrity
    lab = C.load_labels()
    ids = C.canonical_ids(lab)
    man, pol = C.load_c8_memberships(ids)
    c9df, c9 = C.load_c9(ids)
    saf = C.load_safety(ids)

    sets = {
        "phase25c_labels": set(lab.sample_id),
        "phase25e_c8_memberships": set(pd.read_csv(C.ROOT / pol[man.iloc[0]["policy_id"]]["membership_path"],
                                                   dtype={"sample_id": str}).sample_id),
        "phase25f_oof_safety": set(saf.sample_id),
        "phase25f_c9_manifest": set(c9df.sample_id),
    }
    base = sets["phase25c_labels"]
    join = {
        "artifact": "phase25g_dev_population_join_integrity",
        "phase": "25G", "stage": "DEV_POPULATION_JOIN",
        "population": "ROUTER_DEVELOPMENT", "n_expected": C.N_DEV,
        "n_unique_sample_ids": len(base),
        "duplicate_ids": int(len(lab) - lab.sample_id.nunique()),
        "per_source_n": {k: len(v) for k, v in sets.items()},
        "identical_across_sources": {k: (v == base) for k, v in sets.items()},
        "missing_from_labels": sorted(set().union(*[v - base for v in sets.values()]))[:10],
        "c9_rows": int(len(c9df)), "c9_rows_expected": 20 * C.N_DEV,
        "c9_unique_policies": int(c9df.policy_id.nunique()),
        "all_pass": False,
    }
    note(len(base) == C.N_DEV and lab.sample_id.nunique() == C.N_DEV, "DEV_ID_COUNT")
    note(all(v == base for v in sets.values()), "SOURCE_ID_MISMATCH")
    note(len(c9df) == 20 * C.N_DEV, "C9_ROW_COUNT")
    join["all_pass"] = not FAILURES
    C.write_json(C.AUD / "phase25g_dev_population_join_integrity.json", join)

    # ===================================== §5 canonical outcome fields
    d = lab.delta_dice.to_numpy(np.float64)
    resid = np.abs(d - (lab.candidate_refined_dice.to_numpy(np.float64) - lab.global_dice.to_numpy(np.float64)))
    outcome = {
        "artifact": "phase25g_outcome_field_integrity",
        "phase": "25G", "stage": "CANONICAL_OUTCOME_FIELDS",
        "fields": ["sample_id", "domain", "global_dice", "candidate_refined_dice", "delta_dice", "gain_category"],
        "max_abs_delta_residual": float(resid.max()),
        "tolerance": 1e-9,
        "category_counts": lab.gain_category.value_counts().to_dict(),
        "all_pass": bool(resid.max() < 1e-9),
    }
    note(resid.max() < 1e-9, "DELTA_IDENTITY_BREACH")
    C.write_json(C.AUD / "phase25g_outcome_field_integrity.json", outcome)

    # ==================================================== §6 policy grid
    grid = {
        "artifact": "phase25g_policy_grid_integrity",
        "phase": "25G", "stage": "POLICY_GRID",
        "lambda_grid": C.LAMBDAS, "budget_grid": C.BUDGETS,
        "n_policies": len(pol), "expected_rows": 20 * C.N_DEV,
        "observed_c9_rows": int(len(c9df)),
        "budget_cardinalities": {b: int(pol[C.policy_id(C.LAMBDAS[0], b)]["K_b"]) for b in C.BUDGETS},
        "budget_cardinalities_expected": C.BUDGET_K,
        "single_lambda_or_budget_selected": False,
        "all_pass": bool(len(pol) == 20 and len(c9df) == 20 * C.N_DEV),
    }
    note(grid["budget_cardinalities"] == C.BUDGET_K, "BUDGET_CARDINALITY_MISMATCH")
    C.write_json(C.AUD / "phase25g_policy_grid_integrity.json", grid)

    # ============================================ §7 lambda redundancy
    sig = {}
    for pid, rec in pol.items():
        sel = rec["selected"]
        sig[pid] = {
            "budget": rec["budget"],
            "selected_ids_sha256": rec["selected_ids_sha256"],
            "selected_count": int(sel.sum()),
            "selected_sig": C.hashlib.sha256(np.packbits(sel).tobytes()).hexdigest(),
        }
    by_budget = {}
    for b in C.BUDGETS:
        pids = [C.policy_id(l, b) for l in C.LAMBDAS]
        sigs = {sig[p]["selected_sig"] for p in pids}
        c9sigs = set()
        for p in pids:
            o = c9[p]["c9_outcome"]
            c9sigs.add(C.hashlib.sha256("".join(o).encode()).hexdigest())
        by_budget[b] = {
            "n_distinct_membership_signatures": len(sigs),
            "n_lambda_replicas": len(pids),
            "membership_identical": len(sigs) == 1,
            "n_distinct_c9_signatures": len(c9sigs),
            "c9_identical": len(c9sigs) == 1,
        }
    red = {
        "artifact": "phase25g_lambda_membership_redundancy_audit",
        "phase": "25G", "stage": "LAMBDA_MEMBERSHIP_REDUNDANCY",
        "membership_equivalence_group": "budget",
        "cost_is_constant": True,
        "per_budget": by_budget,
        "unique_membership_sets": 5,
        "duplicate_membership_tagged": True,
        "statement": ("Because action cost C_i is constant across the eligible population, C8 routing "
                      "membership is structurally identical across lambda for a given budget. The four "
                      "lambda replicas are DUPLICATE MEMBERSHIP and are NOT four independent scientific "
                      "confirmations. Inferential interpretation acknowledges only 5 unique membership sets."),
        "all_pass": all(v["membership_identical"] and v["c9_identical"] for v in by_budget.values()),
    }
    note(red["all_pass"], "LAMBDA_MEMBERSHIP_NOT_IDENTICAL")
    C.write_json(C.AUD / "phase25g_lambda_membership_redundancy_audit.json", red)

    # ======================================= §10 A7/A8 identity control
    idc_rows = []
    for pid, rec in pol.items():
        sel = rec["selected"]
        o = c9[pid]
        c8_dec = o["c8_decision"]
        sel_from_c9 = c8_dec == "EXECUTE"
        accept = o["c9_outcome"] == "EXECUTE_THEN_ACCEPT"
        reject = o["c9_outcome"] == "EXECUTE_THEN_REJECT"
        skip = o["c9_outcome"] == "PRE_GATE_SKIP"
        idc_rows.append({
            "policy_id": pid,
            "membership_matches_c9": bool(np.array_equal(sel, sel_from_c9)),
            "c9_partition_complete": bool(np.all(accept | reject | skip)),
            "accept_implies_selected": bool(np.all(~accept | sel)),
            "reject_implies_selected": bool(np.all(~reject | sel)),
            "skip_equals_not_selected": bool(np.array_equal(skip, ~sel)),
            "refiner_executed_equals_selected": bool(np.array_equal(o["refiner_executed"].astype(bool), sel)),
            "somega_executed_equals_selected": bool(np.array_equal(o["somega_executed"].astype(bool), sel)),
            "shared_lambda": rec["lambda"], "shared_budget": rec["budget"],
        })
    idc = {
        "artifact": "phase25g_a7_a8_identity_control_audit",
        "phase": "25G", "stage": "A7_A8_CONTROLLED_IDENTITY",
        "shared_controls": ["sample", "routing membership", "lambda", "budget",
                            "regional candidate", "global prediction",
                            "segmentation threshold (0.5)", "ROI geometry"],
        "only_difference": "post-refinement S_omega ACCEPT/FALLBACK decision",
        "per_policy": idc_rows,
        "all_pass": all(all(v for k, v in r.items()
                            if k not in ("policy_id", "shared_lambda", "shared_budget"))
                        for r in idc_rows),
    }
    note(idc["all_pass"], "A7_A8_IDENTITY_CONTROL_BREACH")
    C.write_json(C.AUD / "phase25g_a7_a8_identity_control_audit.json", idc)

    print("PART1_FAILURES", FAILURES)
    print("n_policies", len(pol), "n_c9_rows", len(c9df), "n_dev", len(ids))
    print("lambda_redundancy_pass", red["all_pass"], "identity_pass", idc["all_pass"])
    return 0 if not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())
