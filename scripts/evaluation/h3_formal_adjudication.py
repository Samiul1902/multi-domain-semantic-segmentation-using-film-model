"""Formal H3 adjudication (disk-only).

Reads the authoritative H3 artifacts, SHA-binds the evidence chain, evaluates the
prospectively frozen success criteria and failure boundary clause-by-clause, and
writes reports/audits/h3_formal_adjudication.json.

No training. No inference. No TEST access. No threshold/checkpoint/gate change.
No Option B/C. Phase 15 is NOT started.

Usage:  python scripts/evaluation/h3_formal_adjudication.py
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any, Dict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

AUDITS = PROJECT_ROOT / "reports" / "audits"
TABLES = PROJECT_ROOT / "reports" / "tables"

EXPECTED_CKPT_SHA = "d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e"
SELECTED_EPOCH = 54
FROZEN_LABEL = "H3_SUPPLY_REDESIGN_INSUFFICIENT"

CHAIN = {
    "design_protocol": "reports/audits/h3_proposal_supply_design_protocol.json",
    "success_failure_criteria": "reports/audits/h3_proposal_supply_success_failure_criteria.json",
    "design_correction": "reports/audits/h3_proposal_supply_design_correction.json",
    "final_pretraining_binding_v2": "reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json",
    "training_closure": "reports/audits/h3_proposal_supply_training_closure.json",
    "checkpoint_selection_replay": "reports/audits/h3_checkpoint_selection_replay.json",
    "training_launch_binding": "reports/audits/h3_training_launch_binding.json",
    "supply_axis_evaluation": "reports/audits/h3_supply_axis_evaluation.json",
    "supply_metric_domain_reconciliation": "reports/audits/h3_supply_axis_metric_domain_reconciliation.json",
    "downstream_evaluation": "reports/audits/h3_downstream_evaluation.json",
    "downstream_metric_domain_correction": "reports/audits/h3_downstream_metric_domain_correction.json",
    "downstream_asrun_v1": "reports/audits/h3_downstream_evaluation_v1_asrun.json",
    "axis_priority_results": "reports/audits/post_phase14_h3_axis_priority_results.json",
    "project_evaluation_metrics_backfill": "reports/audits/project_evaluation_metrics_backfill.json",
    "phasewise_evaluation_visualization_sha_updates": "reports/audits/phasewise_evaluation_visualization_sha_updates.json",
    "h3_config": "configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml",
    "h3_downstream_per_component": "reports/tables/h3_downstream_per_component.csv",
    "h3_downstream_per_image": "reports/tables/h3_downstream_per_image.csv",
    "h3_supply_eval_per_component": "reports/tables/h3_supply_eval_per_component.csv",
    "h3_supply_eval_per_image": "reports/tables/h3_supply_eval_per_image.csv",
    "h3_best_checkpoint": "checkpoints/h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3/best.pt",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load(rel: str) -> Dict[str, Any]:
    return json.loads((PROJECT_ROOT / rel).read_text(encoding="utf-8"))


def frac(x: float, denom: int) -> str:
    """Express a RATIO x (in [0,1]) as 'k/denom' using nearest integer numerator."""
    k = round(x * denom)
    return f"{k}/{denom}"


def frac_count(k: int, denom: int) -> str:
    """Express an ABSOLUTE count k as 'k/denom' (numerator is the count itself)."""
    return f"{int(k)}/{int(denom)}"


def main() -> Dict[str, Any]:
    criteria = load(CHAIN["success_failure_criteria"])
    supply = load(CHAIN["supply_axis_evaluation"])
    downstream = load(CHAIN["downstream_evaluation"])
    recon = load(CHAIN["supply_metric_domain_reconciliation"])
    correction = load(CHAIN["downstream_metric_domain_correction"])
    closure = load(CHAIN["training_closure"])
    replay = load(CHAIN["checkpoint_selection_replay"])

    ckpt = PROJECT_ROOT / CHAIN["h3_best_checkpoint"]
    ckpt_sha = sha256_file(ckpt)

    # ── Frozen references ───────────────────────────────────────────────────
    Tg = criteria["frozen_references"]["Tg"]
    G = criteria["frozen_references"]["G"]
    Dg = criteria["frozen_references"]["Dg"]
    val_tiny_total = criteria["frozen_references"]["val_tiny_total"]
    val_comp_total = criteria["frozen_references"]["val_components_total"]

    # ── Observed supply values (frozen supply artifact) ─────────────────────
    pre_gt = supply["baseline_values"]["zero_proposal_gt"]        # 79
    pre_tiny = supply["baseline_values"]["zero_proposal_tiny"]    # 57
    post_gt = supply["size_stratified_results"]["TINY"] and None  # placeholder
    post_gt = supply["primary_criteria"]["criterion_b"]["value"]  # 27
    post_tiny = supply["primary_criteria"]["criterion_a"]["value"]  # 22
    gt_recovered = pre_gt - post_gt
    tiny_recovered = pre_tiny - post_tiny

    # ── Criterion A / B (evaluated from the frozen artifact, re-derived) ────
    a_thr = criteria["primary_supply_criteria"]["zero_proposal_tiny_target_max"]   # "20/72"
    b_thr = criteria["primary_supply_criteria"]["zero_proposal_gt_target_max"]     # "35/152"
    a_limit = int(a_thr.split("/")[0])
    b_limit = int(b_thr.split("/")[0])
    crit_a_pass = post_tiny <= a_limit
    crit_b_pass = post_gt <= b_limit
    combined_supply_pass = crit_a_pass and crit_b_pass

    # ── Formal downstream metric domain ─────────────────────────────────────
    fd = downstream["formal_downstream"]
    TinyRecall_H3 = fd["TinyRecall_H3"]
    R_H3 = fd["R_H3"]
    R_H3_frac = fd["R_H3_exact_fraction"]
    band = fd["interpretation_band"]
    meaningful_threshold = fd["meaningful_threshold"]     # 0.30
    insufficient_threshold = fd["insufficient_threshold"]  # 0.15
    formal_domain = downstream["primary_metric_definition"]["frozen_domain"]

    # Independent re-derivation of R_H3
    R_H3_rederived = (TinyRecall_H3 - Tg) / G
    assert abs(R_H3_rederived - R_H3) < 1e-12, (R_H3_rederived, R_H3)
    assert abs(R_H3_rederived - 2.0 / 15.0) < 1e-12

    # ── Failure boundary, clause by clause ──────────────────────────────────
    fb = criteria["failure_boundary"]
    fail_tiny_limit = 45
    clause_tiny_fired = post_tiny >= fail_tiny_limit
    clause_rh3_fired = R_H3 < insufficient_threshold
    failure_fired = clause_tiny_fired or clause_rh3_fired

    # ── Success definition (all clauses) ────────────────────────────────────
    success_rh3_gate = R_H3 >= meaningful_threshold
    formal_success = combined_supply_pass and success_rh3_gate
    intermediate_zone = (not failure_fired) and (insufficient_threshold <= R_H3 < meaningful_threshold)

    # ── Final frozen label ──────────────────────────────────────────────────
    if failure_fired:
        final_label = FROZEN_LABEL
    elif formal_success:
        final_label = "H3_SUPPLY_REDESIGN_SUCCESSFUL"
    elif intermediate_zone:
        final_label = "H3_SUPPLY_REDESIGN_PARTIAL__SUPERVISOR_ADJUDICATION_REQUIRED"
    else:
        final_label = "H3_SUPPLY_REDESIGN_UNDETERMINED"

    # ── Proxy / sensitivity status ──────────────────────────────────────────
    proxy = recon["misused_quantity"]
    strict = downstream["h3_downstream_metrics"]["descriptive_strict_cov90"]
    formal_rh3_block = downstream["formal_downstream"]["sensitivity_strict_cov90"]

    # ── Provenance caveats ──────────────────────────────────────────────────
    lineage = supply["trainer_lineage_provenance"]

    artifact: Dict[str, Any] = {
        "artifact": "h3_formal_adjudication",
        "artifact_type": "FORMAL_SCIENTIFIC_ADJUDICATION__DISK_ONLY__NO_NEW_EXPERIMENT",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": "H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED",
        "scientific_label": final_label,
        "governance_wrapper_state":
            "H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED",

        "experiment_id": "h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3",
        "selected_checkpoint": {
            "path": CHAIN["h3_best_checkpoint"],
            "sha256": ckpt_sha,
            "sha256_expected": EXPECTED_CKPT_SHA,
            "sha256_matches_expected": ckpt_sha == EXPECTED_CKPT_SHA,
            "selected_epoch": SELECTED_EPOCH,
            "heatmap_resolution": 128,
            "construction": "build_clean_v3_localizer (explicit heatmap_resolution=128)",
        },
        "checkpoint_selection_replay_verdict": replay.get("verdict"),
        "checkpoint_selection_replay_sha256": sha256_file(PROJECT_ROOT / CHAIN["checkpoint_selection_replay"]),
        "training_closure_sha256": sha256_file(PROJECT_ROOT / CHAIN["training_closure"]),
        "training_closure_status": closure.get("status"),

        "scientific_question": {
            "axis": "A_PROPOSAL_SUPPLY_RECALL_LIMITATION",
            "intervention_family": "A_TARGET_SUPPORT_REDESIGN",
            "mechanistic_hypothesis": "FIXED_TARGET_SUPPORT_MAY_BE_MISMATCHED_TO_COMPONENT_SCALE",
            "frozen_mapping": "sigma_i = clip(0.35 + 0.40 * sqrt(A128_i / A_ref), 0.35, 0.75)",
            "A_ref_authoritative": 13.0,
            "A_ref_note": "A_ref = 13.0 is the AUTHORITATIVE executing value: it is bound in the "
                          "final pretraining binding v2, the training launch binding, and the frozen "
                          "H3 config (configs/kub/phase13b_localizer_h3_size_adaptive_sigma.yaml). "
                          "The earlier design-correction artifact froze A_ref = 14.0 (p75 of the "
                          "code-exact 128-space TRAIN area distribution); that value was SUPERSEDED "
                          "before training by the v2 calibration (770 images / 1161 components) and "
                          "is retained only as provenance.",
            "A_ref_superseded_values": [14.0, 12.0],
        },

        "frozen_criteria": {
            "source": CHAIN["success_failure_criteria"],
            "source_sha256": sha256_file(PROJECT_ROOT / CHAIN["success_failure_criteria"]),
            "criterion_A": {"rule": "zero_proposal_TINY <= 20/72", "limit": a_limit, "denominator": val_tiny_total},
            "criterion_B": {"rule": "zero_proposal_GT <= 35/152", "limit": b_limit, "denominator": val_comp_total},
            "criterion_C": {"rule": "formal downstream R_H3 >= 0.30", "limit": meaningful_threshold},
            "contamination": "OBSERVATIONAL_ONLY__NOT_GATED",
        },
        "observed": {
            "zero_proposal_tiny": post_tiny, "zero_proposal_tiny_fraction": frac_count(post_tiny, val_tiny_total),
            "zero_proposal_gt": post_gt, "zero_proposal_gt_fraction": frac_count(post_gt, val_comp_total),
            "pre_h3_zero_proposal_tiny": pre_tiny, "pre_h3_zero_proposal_gt": pre_gt,
            "tiny_supply_recovered": tiny_recovered, "gt_supply_recovered": gt_recovered,
            "formal_TinyRecall_H3": TinyRecall_H3, "formal_TinyRecall_H3_fraction": fd["TinyRecall_H3_fraction"],
            "formal_Tg": Tg, "formal_Tg_fraction": frac(Tg, val_tiny_total),
            "formal_G": G, "formal_G_fraction": frac(G, val_tiny_total),
            "formal_Dg": Dg,
            "formal_R_H3": R_H3, "formal_R_H3_fraction": R_H3_frac,
            "formal_R_H3_rederived": R_H3_rederived,
            "R_H3_band": band,
            "metric_domain": formal_domain,
        },
        "criterion_results": {
            "criterion_A": {"observed": f"{post_tiny}/{val_tiny_total}", "limit": f"<= {a_limit}/{val_tiny_total}",
                            "result": "PASS" if crit_a_pass else "FAIL"},
            "criterion_B": {"observed": f"{post_gt}/{val_comp_total}", "limit": f"<= {b_limit}/{val_comp_total}",
                            "result": "PASS" if crit_b_pass else "FAIL"},
            "criterion_C": {"observed": R_H3, "limit": f">= {meaningful_threshold}",
                            "result": "PASS" if success_rh3_gate else "FAIL"},
            "combined_primary_supply_result": "PASS" if combined_supply_pass else "FAIL",
            "formal_success": bool(formal_success),
        },
        "failure_boundary": {
            "label": FROZEN_LABEL,
            "source": CHAIN["success_failure_criteria"],
            "clause_1": {"rule": "zero_proposal_TINY >= 45/72",
                         "observed": f"{post_tiny}/{val_tiny_total}", "fired": bool(clause_tiny_fired)},
            "clause_2": {"rule": f"R_H3 < {insufficient_threshold}",
                         "observed": R_H3, "fired": bool(clause_rh3_fired)},
            "fired": bool(failure_fired),
            "intermediate_zone_active": bool(intermediate_zone),
        },
        "final_frozen_H3_label": final_label,

        "scientific_interpretation": {
            "improved": [
                f"zero-proposal GT components fell {pre_gt} -> {post_gt} (recovered {gt_recovered})",
                f"zero-proposal TINY components fell {pre_tiny} -> {post_tiny} (recovered {tiny_recovered})",
                "raw proposal supply improved substantially on both the overall and TINY strata",
            ],
            "insufficient": [
                f"Criterion A (zero-proposal TINY <= {a_limit}/{val_tiny_total}) FAILED at {post_tiny}/{val_tiny_total} (missed by {post_tiny - a_limit})",
                f"formal downstream R_H3 = {R_H3_frac} = {R_H3:.10f} < {insufficient_threshold} -> failure boundary FIRED",
            ],
            "statement": "The size-adaptive target-support intervention materially improved proposal "
                         "supply, but the recovered supply did not translate into sufficient downstream "
                         "Tiny-recall gain under the frozen Stage-4D pipeline. The intervention is "
                         "therefore formally insufficient under the prospective H3 criteria.",
            "must_not_say": ["the intervention did nothing", "the intervention succeeded"],
        },
        "regional_hypothesis_preserved": {
            "h3_intervention_failed_its_frozen_criteria": True,
            "oracle_regional_processing_has_no_value": False,
            "oracle_evidence_retained": "Phase-12/Phase-14 ORACLE_REGIONAL remains a valid diagnostic "
                                        "upper bound (mean Dice 0.8024158112932394; TINY detection 1.0)",
            "predicted_localization_path": "still fails to retain enough practical regional benefit "
                                           "(PREDICTED_REGIONAL mean Dice 0.4185309062818487; H3 downstream 0.38862753520437243)",
            "regional_gate_state": "REVISE_LOCALIZER (unresolved)",
        },

        "proxy_and_sensitivity_status": {
            "proposal_domain_proxy": {
                "term": "H3_PROPOSAL_TINY_COVERAGE90",
                "value": proxy["proposal_level_value"],
                "proxy_R_H3": proxy["previously_reported_proxy_R_H3"],
                "status": "INVALID_FOR_FORMAL_ADJUDICATION__PROPOSAL_DOMAIN_ONLY",
                "role": "LOCALIZER-ONLY PROXY - NOT FORMAL DOWNSTREAM R_H3",
            },
            "strict_cov90_sensitivity": {
                "TinyRecall_H3_cov90": strict["tiny_cov90"],
                "R_H3_cov90": formal_rh3_block["R_H3_cov90"],
                "status": "DESCRIPTIVE_SENSITIVITY_ONLY__NOT_FORMAL_H3_GATE",
            },
            "formal_domain_used": "DETECTION (component overlap >= 1 px)",
        },

        "post_hoc_supporting_metrics_policy": {
            "role": "SUPPORTING_EVIDENCE_ONLY",
            "label": "DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE",
            "statistical_label": "DESCRIPTIVE_POST_HOC_STATISTICAL_SUPPORT",
            "promoted_to_gate": False,
            "note": "Project-wide advanced metrics (confusion matrices, Dice/IoU, precision/recall/"
                    "specificity/MCC, HD95/ASSD/surface Dice, calibration, bootstrap CIs, paired "
                    "statistics) are used in Notebook 07 only as supporting evidence and do NOT "
                    "become new prospective H3 criteria.",
        },

        "provenance_caveats": {
            "trainer_lineage": {
                "design_era_trainer": lineage["design_era_trainer"],
                "epochs_1_2_trainer": lineage["epochs_1_2_trainer"],
                "epochs_3_69_trainer": lineage["epochs_3_69_trainer"],
                "note": lineage["note"],
                "single_sha_claim": False,
                "classification": "PROVENANCE_NOT_A_POST_HOC_SCIENTIFIC_GATE",
            },
            "localizer_construction_nuance": downstream["provenance_caveats"][2],
            "supply_off_by_one": {
                "expected": {"gt": 27, "tiny": 22},
                "recomputed": {"gt": 26, "tiny": 21},
                "status": "DESCRIPTIVE_ONLY__FROZEN_SUPPLY_ARTIFACT_NOT_REPLACED",
                "note": "GT bbox provenance difference (phase13_predicted_roi_per_component.csv vs "
                        "extract_gt_components(raw_mask)); SMALL/MEDIUM/LARGE agree exactly.",
            },
        },

        "evidence_chain_sha256": {k: (sha256_file(PROJECT_ROOT / v) if (PROJECT_ROOT / v).exists() else "MISSING")
                                  for k, v in CHAIN.items()},

        "governance": {
            "test_reads": 0,
            "external_test_reads": 0,
            "training_runs_this_task": 0,
            "inference_runs_this_task": 0,
            "checkpoint_changed": False,
            "threshold_changed": False,
            "proposal_policy_changed": False,
            "frozen_gate_changed": False,
            "option_b_started": False,
            "option_c_started": False,
            "phase_15_status": "NOT_STARTED_AND_NOT_AUTHORIZED",
            "phase_16_plus_started": False,
            "h3_adjudication_performed": True,
        },

        "recommended_governance_next_state": {
            "h3_target_support_intervention": "FORMALLY ADJUDICATED - INSUFFICIENT",
            "regional_practical_signal": "STILL UNRESOLVED UNDER PREDICTED LOCALIZATION",
            "regional_gate": "REVISE_LOCALIZER (persists)",
            "phase_15": "NOT_STARTED_AND_NOT_AUTHORIZED",
            "test": "CLOSED",
            "future_options": {
                "option_B_positive_objective_reweighting": "FUTURE_ONLY__REQUIRES_FRESH_SUPERVISOR_AUTHORIZATION",
                "option_C_recall_oriented_output_head": "FUTURE_ONLY__REQUIRES_FRESH_SUPERVISOR_AUTHORIZATION",
                "authorized_now": False,
            },
        },

        "inference_counters": downstream.get("inference_counters", {}),
    }

    # ── Hard consistency gates before writing ───────────────────────────────
    assert ckpt_sha == EXPECTED_CKPT_SHA, "checkpoint SHA mismatch"
    assert SELECTED_EPOCH == 54
    assert replay.get("verdict") == "H3_CHECKPOINT_SELECTION_REPLAY_PASS"
    assert post_tiny == 22 and post_gt == 27
    assert crit_a_pass is False and crit_b_pass is True
    assert abs(TinyRecall_H3 - 59 / 72) < 1e-12
    assert abs(R_H3 - 2 / 15) < 1e-12
    assert R_H3 < insufficient_threshold
    assert "DETECTION" in formal_domain.upper()
    assert clause_tiny_fired is False and clause_rh3_fired is True
    assert failure_fired is True
    assert final_label == FROZEN_LABEL

    out = AUDITS / "h3_formal_adjudication.json"
    out.write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    print("Wrote", out.relative_to(PROJECT_ROOT), "| sha256:", sha256_file(out))
    print("  scientific label :", final_label)
    print("  Criterion A      :", artifact["criterion_results"]["criterion_A"])
    print("  Criterion B      :", artifact["criterion_results"]["criterion_B"])
    print("  R_H3             :", R_H3, "->", band)
    print("  failure fired    :", failure_fired)
    return artifact


if __name__ == "__main__":
    main()
