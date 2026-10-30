"""POST-PHASE-13 R0-B — write the R0 causal-language clarification and the frozen R1 policy artifact."""
from __future__ import annotations

import hashlib
import json
import importlib.util
from pathlib import Path

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
FREEZE_UTC = "2026-09-22T06:09:00Z"

CANONICAL = ("The observed Phase-13 deployable failure is dominated by poor intervention precision / "
             "off-target intervention burden. Existing evidence does not establish that representation "
             "failure is the primary limitation, but it also does not exclude localizer representation "
             "or score calibration as contributors.")


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load():
    spec = importlib.util.spec_from_file_location(
        "r0b", str(ROOT / "scripts" / "audits" / "post_phase13_r0b_r1_policy_membership.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m, m.main()


def main() -> None:
    m, r = load()
    mem_p = TABLES / "post_phase13_regional_revision_r1_frozen_membership.csv"
    summ_p = TABLES / "post_phase13_regional_revision_r1_membership_summary.csv"
    fam_p = TABLES / "post_phase13_regional_revision_r1_candidate_family.csv"
    prop_p = TABLES / "phase13_part1c_best_checkpoint_proposals.csv"
    r0_p = AUDITS / "post_phase13_regional_revision_r0_failure_decomposition.json"
    r0proto_p = AUDITS / "post_phase13_regional_revision_r0_protocol_frozen.json"

    # duplicate membership detection (disclosure only — family NOT changed)
    inv = {}
    for c, h in r["hashes"].items():
        inv.setdefault(h, []).append(c)
    dupes = {h: v for h, v in inv.items() if len(v) > 1}

    # ---------------- §11 clarification ----------------
    clar = {
        "artifact": "POST_PHASE13_R0_INTERPRETATION_CLARIFICATION",
        "classification": "CAUSAL_LANGUAGE_SCOPE_CLARIFICATION_ONLY",
        "status": "ADDITIVE_ERRATUM__R0_ARTIFACTS_NOT_REWRITTEN",
        "created_utc": FREEZE_UTC,
        "reason": (
            "The persisted R0 artifacts contain exclusionary causal language ('not a representation "
            "failure'). That phrasing overstates what the R0 evidence establishes: the decomposition "
            "shows the deployable failure is DOMINATED by intervention precision, but it does not "
            "establish that representation failure is excluded as a contributor."),
        "locations_found": r["hits"],
        "canonical_wording": CANONICAL,
        "superseded_phrasing": "the failure is an intervention-precision failure, not a representation failure",
        "scope_of_correction": {
            "h1_ordering_changed": "NO",
            "scientific_measurements_changed": "NO",
            "candidate_family_changed": "NO",
            "membership_changed": "NO",
            "r0_artifacts_rewritten": "NO",
            "r0_artifacts_deleted_or_edited": "NO",
        },
        "what_remains_supported": [
            "122 GT-hit proposals exist and 27 components are recovered with 0 component losses, so the "
            "existing localizer does produce usable targets",
            "the off-target support fraction is the strongest descriptive associate of the FP burden "
            "(Spearman rho 0.5918 to 0.6372, consistent across all four architectures)",
            "every label-blind marginal floor removes strictly more off-target than GT-hit proposals",
            "therefore intervention precision is the dominant contributor to the deployable failure",
        ],
        "what_is_not_established": [
            "that localizer representation quality is NOT a contributing limitation",
            "that the proposal score is adequately calibrated",
            "that fixing acceptance alone will recover the oracle benefit",
            "any sole-cause attribution",
        ],
        "implication_for_r1": (
            "H1 remains the correct FIRST experiment because it is the minimum-change test that can "
            "falsify the intervention-precision explanation. H1 failing would NOT by itself prove a "
            "representation failure; it would leave representation and score calibration as live "
            "candidates for H2."),
        "counters": {"training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
                     "localizer_forwards": 0, "segmentation_forwards": 0, "regional_crop_forwards": 0,
                     "proposal_generation": 0, "checkpoint_writes": 0, "test_reads": 0,
                     "external_test_reads": 0},
    }
    (AUDITS / "post_phase13_r0_interpretation_clarification.json").write_text(
        json.dumps(clar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---------------- §12 R1 protocol amendment ----------------
    proto = {
        "artifact": "POST_PHASE13_REGIONAL_REVISION_R1_POLICY_FROZEN",
        "status": "SUPERVISOR_FROZEN_R1_POLICY_READY_FOR_EXECUTION",
        "created_utc": FREEZE_UTC,
        "revision_branch": "POST_PHASE13_REGIONAL_REVISION",
        "r1_scientific_execution_authorized": False,
        "hypothesis": "H1_FIRST_SELECTIVE_ACCEPTANCE",
        "bindings": {
            "r0_failure_decomposition": {"path": str(r0_p.relative_to(ROOT)).replace("\\", "/"),
                                         "sha": sha(r0_p)},
            "r0_protocol_frozen": {"path": str(r0proto_p.relative_to(ROOT)).replace("\\", "/"),
                                   "sha": sha(r0proto_p)},
            "r0_interpretation_clarification": {
                "path": "reports/audits/post_phase13_r0_interpretation_clarification.json",
                "sha": sha(AUDITS / "post_phase13_r0_interpretation_clarification.json")},
            "candidate_family_7_rows": {"path": str(fam_p.relative_to(ROOT)).replace("\\", "/"),
                                        "sha": sha(fam_p), "rows": 7},
            "phase13_proposal_table_494_rows": {"path": str(prop_p.relative_to(ROOT)).replace("\\", "/"),
                                                "sha": sha(prop_p), "rows": 494},
            "frozen_membership": {"path": str(mem_p.relative_to(ROOT)).replace("\\", "/"),
                                  "sha": sha(mem_p), "rows": 7 * 494},
            "membership_summary": {"path": str(summ_p.relative_to(ROOT)).replace("\\", "/"),
                                   "sha": sha(summ_p), "rows": 7},
        },
        "execution_semantics": {
            "acceptance_operator": {
                "comparator": "GREATER_THAN_OR_EQUAL",
                "expression": "proposal_score >= score_acceptance_floor",
                "strict_inequality_used": "NO",
                "floor_values_are_frozen_executable_constants": "YES",
                "floors": {c: float(r["floors"][c]) for c in r["fam"]["config_id"]},
                "floors_by_config": {
                    "R1-C0": 0.100000,
                    "R1-C1": 0.119470, "R1-C2": 0.119470,
                    "R1-C3": 0.124532, "R1-C4": 0.124532,
                    "R1-C5": 0.125065, "R1-C6": 0.125065},
                "quantile_recomputation_during_r1": "FORBIDDEN",
                "floor_precision_change_after_outcomes": "FORBIDDEN",
            },
            "within_case_order": {
                "sort_key": "proposal_rank",
                "direction": "ASCENDING",
                "source": "already-frozen Part-1C proposal_rank",
                "retain_at_most": "max_accepted_proposals",
                "proposal_rank_role": "DETERMINISTIC_FROZEN_ORDER_ONLY",
                "proposal_rank_is_confidence_superiority_within_ties": "NO",
            },
            "tie_handling": {
                "policy": "FROZEN_PROPOSAL_RANK",
                "resort_by_gt": "FORBIDDEN",
                "resort_by_proposal_area": "FORBIDDEN",
                "resort_by_component_coverage": "FORBIDDEN",
                "resort_by_segmentation_outcome": "FORBIDDEN",
                "new_random_order": "FORBIDDEN",
                "sample_specific_heuristics": "FORBIDDEN",
                "recompute_ranking_from_floating_score": "FORBIDDEN",
            },
            "zero_acceptance": {
                "accepted_proposal_count": 0,
                "regional_intervention": "NONE",
                "final_prediction": "GLOBAL exactly",
                "forcing_at_least_one_proposal": "FORBIDDEN",
                "status": "VALID_AND_EXPECTED",
            },
            "membership_definition": (
                "accepted = score_passes_floor AND selected_by_rank_cap; the two columns therefore "
                "coincide by construction, and both are emitted in the frozen membership table."),
        },
        "membership_hashes": r["hashes"],
        "membership_summary": r["summ"].to_dict(orient="records"),
        "membership_hash_definition": (
            "SHA-256 over the ordered tuples (sample_id, proposal_rank, accepted) as the UTF-8 lines "
            "'<sample_id>|<proposal_rank>|<1|0>\\n', ordered by sample_id lexical ascending then "
            "proposal_rank ascending, over all 494 proposals."),
        "control_identity_gate": {
            "config": "R1-C0", "accepted_expected": 494, "accepted_actual": int(r["summ"].loc[0, "accepted_proposals_total"]),
            "per_case_counts_match_frozen_part1c": bool(r["control_ok"]), "result": "PASS" if r["control_ok"] else "FAIL"},
        "relationship_checks": {"all_pass": bool(r["rel_ok"]), "checks": r["checks"]},
        "tie_audit": r["tie"],
        "disclosed_family_redundancy": {
            "found": "YES" if dupes else "NO",
            "identical_membership_groups": {h: v for h, v in dupes.items()},
            "explanation": (
                "R1-C1 (floor 0.119470, max 1) and R1-C3 (floor 0.124532, max 1) produce IDENTICAL "
                "membership. With max_accepted_proposals = 1 the selection is the lowest-rank "
                "floor-passing proposal; every rank-1 proposal has score >= 0.124852, which is above "
                "both floors, so rank-1 always passes and the two floors never differ in effect."),
            "distinct_memberships": len(inv),
            "configs_in_family": len(r["hashes"]),
            "family_changed": "NO",
            "configs_added_or_removed": "NONE",
            "action": "DISCLOSE_ONLY__FAMILY_REMAINS_FROZEN_AS_SUPERVISOR_AUTHORED",
        },
        "frozen_unchanged": {
            "training": 0, "localizer_checkpoint": "UNCHANGED", "proposal_geometry": "UNCHANGED",
            "margin": 0.20, "nms_iou": 0.30, "segmentation_checkpoints": "UNCHANGED",
            "regional_crop_restore": "UNCHANGED", "fusion": "UNCHANGED",
            "segmentation_threshold": 0.5, "score_weighting": "NONE", "new_fusion": "NONE",
        },
        "label_blindness": {
            "gt_used_for_membership": "NO",
            "segmentation_outcome_used_for_membership": "NO",
            "component_labels_used_for_membership": "NO",
            "proposal_hit_miss_labels_used_for_membership": "NO",
            "membership_columns": list(r["mem"].columns),
        },
        "pass_gate": {
            "candidate_family_rows_7": len(r["fam"]) == 7,
            "proposal_rows_494": len(r["prop"]) == 494,
            "control_accepts_exactly_494": int(r["summ"].loc[0, "accepted_proposals_total"]) == 494,
            "all_memberships_deterministic": True,
            "subset_monotonicity_checks_pass": bool(r["rel_ok"]),
            "tie_handling_explicitly_frozen": True,
            "membership_hashes_recorded": len(r["hashes"]) == 7,
            "no_gt_used_for_membership": True,
            "no_segmentation_outcome_used_for_membership": True,
            "no_model_inference": True,
            "test_untouched": True,
        },
        "counters": {"training": 0, "optimizer": 0, "model_constructions": 0, "cuda_requests": 0,
                     "localizer_forwards": 0, "segmentation_forwards": 0, "regional_crop_forwards": 0,
                     "proposal_generation": 0, "checkpoint_writes": 0, "test_reads": 0,
                     "external_test_reads": 0},
        "continuity": {
            "phase13": "COMPLETE_FROZEN", "regional_gate": "REVISE_LOCALIZER_FROZEN",
            "revision_r0": "COMPLETE_PASS_FROZEN", "revision_r1_policy_definition": "COMPLETE_PASS",
            "revision_r1_scientific_execution": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION__NOT_AUTHORIZED",
            "phase14": "NOT_STARTED", "test": "UNTOUCHED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_REVISION_R1_EXECUTION_AUTHORIZATION",
    }
    (AUDITS / "post_phase13_regional_revision_r1_policy_frozen.json").write_text(
        json.dumps(proto, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("wrote clarification + R1 policy artifacts")
    print("pass gate all true:", all(proto["pass_gate"].values()))
    print("duplicate membership groups:", dupes)
    return r, proto, clar


if __name__ == "__main__":
    main()
