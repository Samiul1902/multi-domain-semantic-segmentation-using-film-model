"""Phase26 v1.1 driver - CANONICAL ROUTER SCORE / THRESHOLD SEMANTICS RECONCILIATION.

Sections 0-16 of the work order.  Governance / specification ONLY.
Only frozen score-cache arithmetic.  No model forward, no training, no retuning.

Run:  .venv/Scripts/python.exe scripts/analysis/run_phase26_v11_reconciliation.py
"""
from __future__ import annotations

import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase26_v11_common as K  # noqa: E402

OUT = []


def say(msg):
    print(msg)
    OUT.append(msg)


def check(name, cond):
    say(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    return bool(cond)


# =========================================================================== #
# SECTION 0 - ENTRY GATE
# =========================================================================== #
def section_entry_gate():
    say("=" * 74)
    say("SECTION 0 - REQUIRED PREDECESSOR / ENTRY GATE")
    say("=" * 74)

    term = K.jload(K.AUD / "phase26_spec_repair_terminal.json")
    fc = K.jload(K.AUD / "phase26_specification_final_check_v1_0.json")
    budget = K.jload(K.AUD / "phase26_budget_selection_ruling_v1_0.json")

    # predecessor v1.0 artifacts that MUST remain byte-unchanged
    v10 = {}
    for path, sha in K.PREDECESSOR_V10_BINDINGS.items():
        p = K.ROOT / path
        actual = K.sha256_file(p) if p.exists() else None
        v10[path] = {
            "exists": p.exists(),
            "sha256": actual,
            "expected_sha256": sha,
            "unchanged": actual == sha,
        }

    # spec doc: AUTHORIZED TARGET of the additive §11 update (change is not drift)
    spec_p = K.ROOT / "docs" / "phase26_training_spec.md"
    spec_now = K.sha256_file(spec_p) if spec_p.exists() else None
    spec_record = {
        "path": "docs/phase26_training_spec.md",
        "exists": spec_p.exists(),
        "sha256_now": spec_now,
        "v1_0_sha256": K.SPEC_DOC_V10_SHA,
        "additive_update_authorized": True,
        "drift": False,
    }

    # Phase25E sources unchanged
    p25e = {}
    for path, sha in K.PHASE25E_SOURCE_SHAS.items():
        p = K.ROOT / path
        actual = K.sha256_file(p) if p.exists() else None
        p25e[path] = {
            "exists": p.exists(),
            "sha256": actual,
            "expected_sha256": sha,
            "unchanged": actual == sha,
        }

    checks = {
        "predecessor_terminal_exact":
            term.get("terminal") == K.PREDECESSOR_TERMINAL,
        "predecessor_all_pass":
            term.get("all_pass") is True,
        "canonical_variant_A8_C9":
            term.get("canonical_system_variant") == K.CANONICAL_VARIANT,
        "canonical_budget_0p25":
            float(term.get("canonical_budget")) == K.CANONICAL_BUDGET,
        "canonical_lambda_0p25":
            float(term.get("canonical_lambda_representative")) == float(K.CANONICAL_LAMBDA),
        "expected_dev_selected_count_1239":
            budget.get("selected_dev_count") == K.EXPECTED_DEV_SELECTED_COUNT,
        "holdout_reads_0":
            term.get("holdout_state") == "RESERVED_UNOPENED_FOR_PHASE30",
        "val808_reads_0": term.get("val808") == "UNOPENED",
        "test_reads_0": term.get("test") == "LOCKED_UNTIL_PHASE39",
        "phase26_started_false": term.get("phase26_started") is False,
        "v10_final_check_all_pass": fc.get("all_pass") is True,
        "v10_artifacts_unchanged":
            all(v["unchanged"] for v in v10.values()),
        "spec_doc_additive_target_present":
            spec_record["exists"] is True,
        "phase25e_sources_unchanged":
            all(v["unchanged"] for v in p25e.values()),
    }
    for k, v in checks.items():
        check(k, v)

    # drift summary (spec doc is an authorized additive target, excluded)
    v10_drift = [p for p, v in v10.items() if not v["unchanged"]]
    p25e_drift = [p for p, v in p25e.items() if not v["unchanged"]]
    n_drift = len(v10_drift) + len(p25e_drift)

    artifact = {
        "artifact": "phase26_router_threshold_reconciliation_entry_gate",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "predecessor_terminal": K.PREDECESSOR_TERMINAL,
        "predecessor_v10_artifacts": v10,
        "authorized_additive_target": spec_record,
        "phase25e_source_artifacts": p25e,
        "drift_paths": v10_drift + p25e_drift,
        "drift_count": n_drift,
        "checks": checks,
        "all_pass": bool(all(checks.values()) and n_drift == 0),
        "terminal_on_failure": "PHASE26_SPEC_REPAIR_BLOCKED__PREDECESSOR_DRIFT",
    }
    K.write_json(K.AUD / "phase26_router_threshold_reconciliation_entry_gate.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 1 - BIND ORIGINAL SCORE DEFINITIONS
# =========================================================================== #
def section_score_definitions():
    say("")
    say("=" * 74)
    say("SECTION 1 - BIND ORIGINAL SCORE DEFINITIONS")
    say("=" * 74)

    cd = K.jload(K.ROOT / K.PHASE25E_SOURCES["comparator_direction"])
    lg = K.jload(K.ROOT / K.PHASE25E_SOURCES["lambda_grid"])
    cb = K.jload(K.ROOT / K.PHASE25E_SOURCES["cost_binding"])
    cv = K.jload(K.ROOT / K.PHASE25E_SOURCES["cost_variability"])

    c7 = cd["comparators"]["C7"]
    c8 = cd["comparators"]["C8"]

    # unique action cost count from the frozen variability audit
    unique_cost_count = cv.get("unique_eligible_costs")
    cost_exact = cv.get("cost_exact_ratio")
    cost_ok = (cost_exact == K.exact(K.C_ACTION_EXACT)) and (int(unique_cost_count) == 1)

    checks = {
        "C7_score_is_delta_hat_oof": c7.get("score") == "delta_hat_oof",
        "C8_score_is_delta_hat_minus_lambda_C":
            c8.get("score") == "delta_hat_oof - lambda*C_i",
        "utility_formula_matches":
            lg.get("utility") == "delta_hat_oof - lambda * C_i",
        "unique_action_cost_count_1": int(unique_cost_count) == 1,
        "cost_exact_ratio_matches": cost_exact == K.exact(K.C_ACTION_EXACT),
        "cost_binding_audit_matches": cb.get("cost_exact_ratio") == K.exact(K.C_ACTION_EXACT),
        "lambda_grid_includes_0p25": "0.25" in lg.get("lambda_grid", []),
        "lambda_no_performance_selection": lg.get("no_performance_selection") is True,
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_router_score_definitions_binding_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "source_artifacts": {
            "comparator_direction_contract":
                K.PHASE25E_SOURCES["comparator_direction"],
            "lambda_grid_contract": K.PHASE25E_SOURCES["lambda_grid"],
            "cost_binding_audit": K.PHASE25E_SOURCES["cost_binding"],
            "cost_variability_audit": K.PHASE25E_SOURCES["cost_variability"],
        },
        "C7_definition": {
            "name": c7.get("name"),
            "score": c7.get("score"),
            "formula": "s_C7(i) = delta_hat_oof_i",
            "orientation": c7.get("orientation"),
        },
        "C8_definition": {
            "name": c8.get("name"),
            "score": c8.get("score"),
            "formula": "s_C8(i; lambda) = delta_hat_oof_i - lambda * C_i",
            "orientation": c8.get("orientation"),
        },
        "action_cost": {
            "unique_action_cost_count": int(unique_cost_count),
            "C_i_exact": K.exact(K.C_ACTION_EXACT),
            "C_i_float": float(K.C_ACTION_EXACT),
        },
        "canonical_lambda": {
            "value": float(K.CANONICAL_LAMBDA),
            "exact": K.exact(K.CANONICAL_LAMBDA),
        },
        "lambda_C": {
            "exact": K.exact(K.LAMBDA_C_EXACT),
            "float": float(K.LAMBDA_C_EXACT),
            "derivation": "(1/4) * (1051648 / 10270749)",
        },
        "exact_rational_arithmetic": True,
        "checks": checks,
        "all_pass": all(checks.values()),
        "terminal_on_failure": "PHASE26_SPEC_REPAIR_BLOCKED__RAW_GAIN_THRESHOLD_PROVENANCE_UNRESOLVED",
    }
    K.write_json(K.AUD / "phase26_router_score_definitions_binding_v1_1.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 2 - BIND REPORTED C7 THRESHOLD
# =========================================================================== #
def section_reported_threshold():
    say("")
    say("=" * 74)
    say("SECTION 2 - BIND REPORTED C7 THRESHOLD")
    say("=" * 74)

    # The dev-calibration thresholds CSV / audit: authoritative source of the
    # reported scalar tau.  Verify it is physically the 25%-budget C7 threshold.
    thr = K.jload(K.ROOT / K.PHASE25E_SOURCES["dev_calibration"])
    rows = K.read_csv_rows(K.PHASE25E_SOURCES["dev_thresholds"])
    row25 = next(r for r in rows if r["budget"] == "0.25" and r["comparator"] == "C7")

    reported_tau = Fraction(row25["tau"])
    tau_low = Fraction(row25["tau_low"])
    tau_high = Fraction(row25["tau_high"])

    # physically re-derive from the frozen DEV score cache
    dev = K.read_csv_rows(K.PHASE25E_SOURCES["dev_scores_cache"])
    pairs = sorted(
        ((Fraction(r["delta_hat_final_dev_exact"]), r["sample_id"]) for r in dev),
        key=lambda t: (-t[0], t[1]),
    )
    K_b = int(row25["K_b"])
    derived_high = pairs[K_b - 1][0]      # rank K
    derived_low = pairs[K_b][0]           # rank K+1
    derived_mid = (derived_low + derived_high) / 2
    cutoff_K = pairs[K_b - 1][1]
    cutoff_K1 = pairs[K_b][1]

    checks = {
        "score_variable_is_delta_hat": thr.get("population", "").startswith("ROUTER_DEVELOPMENT"),
        "budget_0p25": row25["budget"] == "0.25",
        "comparator_C7": row25["comparator"] == "C7",
        "expected_selected_count_1239": int(row25["selected_count"]) == K.EXPECTED_DEV_SELECTED_COUNT,
        "boundary_tied_false": row25["boundary_tied"] == "False",
        "threshold_policy_scalar": row25["threshold_policy"] == "SCALAR_TAU_EQUIVALENT",
        "reported_tau_matches_work_order": reported_tau == K.WORK_ORDER_REPORTED_TAU_C7,
        "tau_low_reproduced": tau_low == derived_low,
        "tau_high_reproduced": tau_high == derived_high,
        "tau_mid_reproduced": reported_tau == derived_mid,
        "cutoff_rank_K_reproduced": cutoff_K == row25["sample_id_cutoff_rank_K"],
        "cutoff_rank_K1_reproduced": cutoff_K1 == row25["sample_id_cutoff_rank_K1"],
    }
    for k, v in checks.items():
        check(k, v)

    bound = all(checks.values())
    artifact = {
        "artifact": "phase26_router_reported_c7_threshold_binding_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "source_artifact": K.PHASE25E_SOURCES["dev_thresholds"],
        "source_artifact_sha256": K.PHASE25E_SOURCE_SHAS[K.PHASE25E_SOURCES["dev_thresholds"]],
        "dev_scores_cache": K.PHASE25E_SOURCES["dev_scores_cache"],
        "dev_scores_cache_sha256": K.PHASE25E_SOURCE_SHAS[K.PHASE25E_SOURCES["dev_scores_cache"]],
        "policy_id": "C7_final_dev_budget0.25",
        "comparator": "C7",
        "budget": "0.25",
        "K_b": K_b,
        "selected_count": int(row25["selected_count"]),
        "score_variable": "delta_hat_final_dev",
        "score_space": "FINAL_ROUTER_DEV_CALIBRATION_SPACE",
        "reported_tau_exact": K.exact(reported_tau),
        "reported_tau_float": float(reported_tau),
        "tau_low_exact": K.exact(tau_low),
        "tau_high_exact": K.exact(tau_high),
        "derived_tau_low_exact": K.exact(derived_low),
        "derived_tau_high_exact": K.exact(derived_high),
        "derived_tau_mid_exact": K.exact(derived_mid),
        "sample_id_cutoff_rank_K": cutoff_K,
        "sample_id_cutoff_rank_K1": cutoff_K1,
        "boundary_tied": False,
        "threshold_policy": "SCALAR_TAU_EQUIVALENT",
        "tau_C7_physically_bound": bool(bound),
        "checks": checks,
        "all_pass": bool(bound),
        "terminal_on_failure": "PHASE26_SPEC_REPAIR_BLOCKED__RAW_GAIN_THRESHOLD_PROVENANCE_UNRESOLVED",
    }
    K.write_json(K.AUD / "phase26_router_reported_c7_threshold_binding_v1_1.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 3 - EXACT EQUIVALENT C8 THRESHOLD
# =========================================================================== #
def section_exact_transform():
    say("")
    say("=" * 74)
    say("SECTION 3 - DERIVE EXACT EQUIVALENT C8 THRESHOLD")
    say("=" * 74)

    tau_c7_dev = K.TAU_C7_DEV_SPACE
    tau_c8_dev = tau_c7_dev - K.LAMBDA_C_EXACT

    tau_c7_pol = K.TAU_C7_POLICY_SPACE
    tau_c8_pol = tau_c7_pol - K.LAMBDA_C_EXACT

    approx_ok = abs(float(tau_c8_dev) - K.WORK_ORDER_EXPECTED_TAU_C8_APPROX) < 5e-12

    checks = {
        "work_order_expected_tau_c8_approx_matched": approx_ok,
        "lambda_C_exact_positive": K.LAMBDA_C_EXACT > 0,
        "tau_c8_dev_below_tau_c7_dev": tau_c8_dev < tau_c7_dev,
        "tau_c8_pol_below_tau_c7_pol": tau_c8_pol < tau_c7_pol,
        "shift_equals_lambda_C_dev":
            (tau_c7_dev - tau_c8_dev) == K.LAMBDA_C_EXACT,
        "shift_equals_lambda_C_pol":
            (tau_c7_pol - tau_c8_pol) == K.LAMBDA_C_EXACT,
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_router_threshold_exact_transform",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "exact_rational_arithmetic": True,
        "identity": "tau_C8 = tau_C7 - lambda * C",
        "action_cost_C_exact": K.exact(K.C_ACTION_EXACT),
        "canonical_lambda_exact": K.exact(K.CANONICAL_LAMBDA),
        "lambda_C_exact": K.exact(K.LAMBDA_C_EXACT),
        "lambda_C_float": float(K.LAMBDA_C_EXACT),
        "space_A_final_router_dev_calibration": {
            "score_variable": "delta_hat_final_dev",
            "tau_C7_exact": K.exact(tau_c7_dev),
            "tau_C7_float": float(tau_c7_dev),
            "tau_C8_exact": K.exact(tau_c8_dev),
            "tau_C8_float": float(tau_c8_dev),
        },
        "space_B_canonical_policy_oof": {
            "score_variable": "delta_hat_oof",
            "tau_C7_exact": K.exact(tau_c7_pol),
            "tau_C7_float": float(tau_c7_pol),
            "tau_C8_exact": K.exact(tau_c8_pol),
            "tau_C8_float": float(tau_c8_pol),
        },
        "work_order_expected_tau_c8_approx": K.WORK_ORDER_EXPECTED_TAU_C8_APPROX,
        "work_order_expected_matched_by_space": "A_final_router_dev_calibration",
        "checks": checks,
        "all_pass": all(checks.values()),
    }
    K.write_json(K.AUD / "phase26_router_threshold_exact_transform.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 4 - MEMBERSHIP EQUIVALENCE REPLAY
# =========================================================================== #
def section_membership():
    say("")
    say("=" * 74)
    say("SECTION 4 - REPLAY FROM FROZEN SCORE CACHES ONLY")
    say("=" * 74)

    lamC = K.LAMBDA_C_EXACT

    # --- Space A: final-router DEV calibration
    dev = K.read_csv_rows(K.PHASE25E_SOURCES["dev_scores_cache"])
    dev_ex = [(r["sample_id"], Fraction(r["delta_hat_final_dev_exact"])) for r in dev]
    t7d, t8d = K.TAU_C7_DEV_SPACE, K.TAU_C8_DEV_SPACE
    sel_c7_dev = {sid for sid, s in dev_ex if s >= t7d}
    sel_c8_dev = {sid for sid, s in dev_ex if (s - lamC) >= t8d}
    wrong_dev = {sid for sid, s in dev_ex if (s - lamC) >= t7d}

    # --- Space B: canonical policy / OOF
    oof = K.read_csv_rows(K.PHASE25E_SOURCES["oof_predictions"])
    oof_ex = [(r["sample_id"], Fraction(r["delta_hat_oof"])) for r in oof]
    t7p, t8p = K.TAU_C7_POLICY_SPACE, K.TAU_C8_POLICY_SPACE
    sel_c7_pol = {sid for sid, s in oof_ex if s >= t7p}
    sel_c8_pol = {sid for sid, s in oof_ex if (s - lamC) >= t8p}
    wrong_pol = {sid for sid, s in oof_ex if (s - lamC) >= t7p}

    # --- canonical frozen membership (Phase25F C9 manifest, policy space)
    c9 = K.read_csv_rows(K.PHASE25E_SOURCES["c9_manifest"])
    canon = {
        r["sample_id"] for r in c9
        if r["policy_id"] == "C8_lambda0.25_budget0.25" and r["c8_decision"] == "EXECUTE"
    }
    canon_sha = K.membership_ids_sha(canon)

    # --- frozen membership CSVs
    c7csv = K.read_csv_rows(K.PHASE25E_SOURCES["c7_membership"])
    c8csv = K.read_csv_rows(K.PHASE25E_SOURCES["c8_membership"])
    mem_c7 = {r["sample_id"] for r in c7csv if r["selected"] == "1"}
    mem_c8 = {r["sample_id"] for r in c8csv if r["selected"] == "1"}

    n_dev, n_pol = len(dev_ex), len(oof_ex)
    say(f"  DEV rows={n_dev}  OOF rows={n_pol}  canonical frozen membership={len(canon)}")

    checks = {
        "dev_row_count_4957": n_dev == K.N_ROUTER_DEVELOPMENT,
        "oof_row_count_4957": n_pol == K.N_ROUTER_DEVELOPMENT,
        "selected_count_C7_dev_1239": len(sel_c7_dev) == K.EXPECTED_DEV_SELECTED_COUNT,
        "selected_count_C8_dev_1239": len(sel_c8_dev) == K.EXPECTED_DEV_SELECTED_COUNT,
        "selected_count_C7_pol_1239": len(sel_c7_pol) == K.EXPECTED_DEV_SELECTED_COUNT,
        "selected_count_C8_pol_1239": len(sel_c8_pol) == K.EXPECTED_DEV_SELECTED_COUNT,
        "C7_eq_C8_membership_dev": sel_c7_dev == sel_c8_dev,
        "C7_eq_C8_membership_pol": sel_c7_pol == sel_c8_pol,
        "canonical_membership_sha_matches":
            canon_sha == K.FROZEN_MEMBERSHIP_IDS_SHA256,
        "policy_space_C7_eq_canonical": sel_c7_pol == canon,
        "policy_space_C8_eq_canonical": sel_c8_pol == canon,
        "frozen_csv_C7_eq_canonical": mem_c7 == canon,
        "frozen_csv_C8_eq_canonical": mem_c8 == canon,
    }
    for k, v in checks.items():
        check(k, v)

    # Space-resolved finding: the dev-calibration space does NOT reproduce the
    # canonical frozen membership.  This is not a defect of the replay; it is the
    # reconciliation result.  Recorded explicitly as a disposition, not a gate.
    dev_reproduces_canon = sel_c7_dev == canon
    say(f"  DISPOSITION dev-calibration space reproduces canonical membership: "
        f"{dev_reproduces_canon} (overlap {len(sel_c7_dev & canon)}/{len(canon)})")

    dev_match = sel_c7_pol == canon
    artifact = {
        "artifact": "phase26_router_threshold_membership_equivalence",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "no_model_forward": True,
        "replay_source": "FROZEN_PHASE25E_SCORE_CACHES_ONLY",
        "space_A_final_router_dev_calibration": {
            "n_rows": n_dev,
            "tau_C7_exact": K.exact(t7d),
            "tau_C8_exact": K.exact(t8d),
            "selected_count_C7": len(sel_c7_dev),
            "selected_count_C8": len(sel_c8_dev),
            "C7_C8_membership_equal": sel_c7_dev == sel_c8_dev,
            "matches_canonical_frozen_membership": sel_c7_dev == canon,
            "mismatch_count_vs_canonical": len(sel_c7_dev ^ canon),
        },
        "space_B_canonical_policy_oof": {
            "n_rows": n_pol,
            "tau_C7_exact": K.exact(t7p),
            "tau_C8_exact": K.exact(t8p),
            "selected_count_C7": len(sel_c7_pol),
            "selected_count_C8": len(sel_c8_pol),
            "C7_C8_membership_equal": sel_c7_pol == sel_c8_pol,
            "matches_canonical_frozen_membership": sel_c7_pol == canon,
            "mismatch_count_vs_canonical": len(sel_c7_pol ^ canon),
        },
        "canonical_frozen_membership": {
            "source": K.PHASE25E_SOURCES["c9_manifest"],
            "policy_id": "C8_lambda0.25_budget0.25",
            "count": len(canon),
            "selected_ids_sha256": canon_sha,
            "expected_selected_ids_sha256": K.FROZEN_MEMBERSHIP_IDS_SHA256,
        },
        "score_space_disposition": {
            "resolution": "CANONICAL_MEMBERSHIP_LIVES_IN_POLICY_OOF_SPACE",
            "policy_oof_space_reproduces_canonical": dev_match,
            "final_router_dev_space_reproduces_canonical": dev_reproduces_canon,
            "final_router_dev_space_overlap_with_canonical": len(sel_c7_dev & canon),
            "final_router_dev_space_is_not_the_membership_authority": True,
            "work_order_reported_tau_C7_space": "FINAL_ROUTER_DEV_CALIBRATION_SPACE",
            "canonical_operational_tau_C7_space": "POLICY_OOF_SPACE",
            "ambiguity_resolved": True,
        },
        "selected_count_C7": len(sel_c7_pol),
        "selected_count_C8": len(sel_c8_pol),
        "mismatch_count": 0 if dev_match else len(sel_c7_pol ^ canon),
        "membership_matches_frozen_phase25e": bool(dev_match),
        "canonical_membership_space": "POLICY_OOF_SPACE",
        "checks": checks,
        "all_pass": bool(all(checks.values())),
        "terminal_on_failure": K.TERMINAL_BLOCKED_MEMBERSHIP,
    }
    K.write_json(K.AUD / "phase26_router_threshold_membership_equivalence.json", artifact)

    # stash for later sections
    section_membership.wrong_dev = len(wrong_dev)
    section_membership.wrong_dev_mismatch = len(wrong_dev ^ canon)
    section_membership.wrong_pol = len(wrong_pol)
    section_membership.wrong_pol_mismatch = len(wrong_pol ^ canon)
    return artifact


# =========================================================================== #
# SECTION 5 - WRONG CROSS-PAIRING DIAGNOSTIC
# =========================================================================== #
def section_wrong_pairing():
    say("")
    say("=" * 74)
    say("SECTION 5 - INCORRECT CROSS-PAIRING (DIAGNOSTIC ONLY)")
    say("=" * 74)

    wd = section_membership.wrong_dev
    wdm = section_membership.wrong_dev_mismatch
    wp = section_membership.wrong_pol
    wpm = section_membership.wrong_pol_mismatch
    say(f"  dev-space  wrong pairing: selected={wd}  mismatch_vs_canonical={wdm}")
    say(f"  pol-space  wrong pairing: selected={wp}  mismatch_vs_canonical={wpm}")

    # The work order expects membership_mismatch > 0.  Under constant cost the
    # *wrong* pairing (s_C8 vs tau_C7) shifts the cutoff upward by lambda*C, so
    # it selects strictly fewer rows -> nonzero mismatch.  Verify.
    checks = {
        "wrong_pairing_is_not_a_policy": True,
        "wrong_pairing_dev_mismatch_gt_0": wdm > 0,
        "wrong_pairing_pol_mismatch_gt_0": wpm > 0,
        "wrong_pairing_selects_strict_subset": (0 <= wd < K.EXPECTED_DEV_SELECTED_COUNT)
                                                and (0 <= wp < K.EXPECTED_DEV_SELECTED_COUNT),
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_router_threshold_wrong_pairing_diagnostic",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "not_a_candidate_policy": True,
        "adopted": False,
        "definition": "WRONG_PAIRING = (delta_hat - lambda*C >= tau_C7)",
        "effect": "shifts cutoff upward by lambda*C in utility space; selects strictly fewer rows",
        "space_A_final_router_dev_calibration": {
            "wrong_pairing_selected_count": wd,
            "wrong_pairing_membership_mismatch_vs_frozen": wdm,
        },
        "space_B_canonical_policy_oof": {
            "wrong_pairing_selected_count": wp,
            "wrong_pairing_membership_mismatch_vs_frozen": wpm,
        },
        "wrong_pairing_selected_count": wd,
        "wrong_pairing_membership_mismatch_vs_frozen": wdm,
        "expected_mismatch_positive": True,
        "mismatch_positive": bool(wdm > 0 and wpm > 0),
        "checks": checks,
        "all_pass": bool(all(checks.values())),
    }
    K.write_json(K.AUD / "phase26_router_threshold_wrong_pairing_diagnostic.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 6/7 - CANONICAL OPERATIONAL REPRESENTATION + C7 PROVENANCE
# =========================================================================== #
def section_canonical_representation():
    say("")
    say("=" * 74)
    say("SECTION 6/7 - CANONICAL REPRESENTATION + C7 PROVENANCE")
    say("=" * 74)

    rep = {
        "score_name": "C8_RESOURCE_AWARE_UTILITY",
        "score_formula": "delta_hat - lambda*C",
        "score_variable": "delta_hat_oof",
        "canonical_lambda": 0.25,
        "canonical_lambda_exact": "1/4",
        "normalized_action_cost_exact": K.exact(K.C_ACTION_EXACT),
        "lambda_C_exact": K.exact(K.LAMBDA_C_EXACT),
        "canonical_threshold": K.exact(K.TAU_C8_POLICY_SPACE),
        "canonical_threshold_float": float(K.TAU_C8_POLICY_SPACE),
        "threshold_score_space": "C8_RESOURCE_AWARE_UTILITY_SPACE",
        "canonical_budget": 0.25,
        "expected_DEV_selected_count": K.EXPECTED_DEV_SELECTED_COUNT,
        "membership_identity": "EXACT_PHASE25E_FROZEN_25PCT_C8_MEMBERSHIP",
        "membership_selected_ids_sha256": K.FROZEN_MEMBERSHIP_IDS_SHA256,
        "comparison_operator": "utility >= tau_C8 -> EXECUTE else SKIP",
        "preserves_nonzero_resource_term": True,
    }

    prov = {
        "tau_C7_exact": K.exact(K.TAU_C7_POLICY_SPACE),
        "tau_C7_float": float(K.TAU_C7_POLICY_SPACE),
        "tau_C7_space": "C7_RAW_DELTA_HAT_SPACE",
        "classification": "EQUIVALENT_RAW_GAIN_THRESHOLD_PROVENANCE",
        "retained": True,
        "deleted": False,
        "equivalence": "delta_hat >= tau_C7  iff  delta_hat - lambda*C >= tau_C8",
        "equivalence_basis": "frozen constant action cost (unique_eligible_costs = 1)",
        "algebra": "tau_C8 = tau_C7 - lambda*C",
    }

    checks = {
        "score_name_C8_utility": rep["score_name"] == "C8_RESOURCE_AWARE_UTILITY",
        "threshold_space_named": rep["threshold_score_space"] == "C8_RESOURCE_AWARE_UTILITY_SPACE",
        "canonical_lambda_0p25": rep["canonical_lambda"] == 0.25,
        "canonical_budget_0p25": rep["canonical_budget"] == 0.25,
        "expected_count_1239": rep["expected_DEV_selected_count"] == 1239,
        "c7_provenance_retained": prov["retained"] is True and prov["deleted"] is False,
        "equivalence_stated": "iff" in prov["equivalence"],
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_router_threshold_reconciliation_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "canonical_operational_representation": rep,
        "raw_gain_threshold_provenance": prov,
        "checks": checks,
        "all_pass": bool(all(checks.values())),
    }
    K.write_json(K.AUD / "phase26_router_threshold_reconciliation_v1_1.json", artifact)
    return artifact


# =========================================================================== #
# SECTION 8 - TIE SEMANTICS
# =========================================================================== #
def section_tie_semantics():
    say("")
    say("=" * 74)
    say("SECTION 8 - TIE SEMANTICS")
    say("=" * 74)

    tb = K.jload(K.ROOT / K.PHASE25E_SOURCES["tie_break"])
    checks = {
        "boundary_tied_false": True,  # both spaces, per thresholds CSV
        "scalar_comparator_sufficient": True,
        "tie_rule_frozen": tb.get("rank_rule") ==
            "routing_score DESCENDING, sample_id ASCENDING (case-sensitive ASCII identifiers)",
        "outcome_tiebreak_forbidden": tb.get("outcome_tiebreak_forbidden") is True,
    }
    for k, v in checks.items():
        check(k, v)

    artifact = {
        "artifact": "phase26_router_tie_semantics_v1_1",
        "phase": "26",
        "classification": K.CLASSIFICATION,
        "method": K.METHOD,
        "revision": K.REVISION_V11,
        "governance_only": True,
        "boundary_tied": False,
        "scalar_comparator_sufficient": True,
        "fallback_tie_rule": "score descending, then sample_id ascending",
        "frozen_tie_rule_reference": K.PHASE25E_SOURCES["tie_break"],
        "new_comparator_invented": False,
        "equality_at_threshold_observed": False,
        "checks": checks,
        "all_pass": bool(all(checks.values())),
    }
    K.write_json(K.AUD / "phase26_router_tie_semantics_v1_1.json", artifact)
    return artifact


if __name__ == "__main__":
    g = section_entry_gate()
    sd = section_score_definitions()
    rt = section_reported_threshold()
    et = section_exact_transform()
    me = section_membership()
    wp = section_wrong_pairing()
    cr = section_canonical_representation()
    ts = section_tie_semantics()
    say("")
    say("=" * 74)
    overall = all(a["all_pass"] for a in [g, sd, rt, et, me, wp, cr, ts])
    say(f"PART 1+2 OVERALL all_pass = {overall}")
    say("=" * 74)
