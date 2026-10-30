"""Project governance sync -- section 1: FAIL-CLOSED pre-repair audit.

Verifies the exact canonical predecessor state before any governance/spec edit
is allowed to proceed. Any mismatch => FAIL CLOSED (no writes beyond this audit).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
NB25A = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
         / "phase25a_dedicated_regional_refiner.ipynb")

EXPECTED = {
    "phase25a_terminal": ("PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__"
                          "SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED"),
    "phase25a_notebook_sha256": "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd",
    "phase25a_final_checkpoint_sha256": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "phase25a_refiner_params": 1276401,
    "phase25a_gmacs": 3.230663,
    "roi_proposal_threshold": 0.30,
    "segmentation_output_threshold": 0.50,
    "phase25b_terminal": "PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE",
    "phase24_v1_1_notebook_sha256": "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef",
    "phase24_v1_2_notebook_sha256_before": "97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff",
    "phase24_v1_2_terminal": "PHASE24_ROUTER_FEATURE_SPEC_V1_2_BLOCKED__SUPERVISOR_REVIEW_REQUIRED",
    "phase24_v1_2_terminal_post_closure": (
        "PHASE24_ROUTER_FEATURE_SPEC_V1_2_COMPLETE__RF1_RF2_RF3_RESOLVED__"
        "PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED"),
    "defect_ids": ["RF3-DEFECT", "ROUTER-PARAM-DISCREPANCY"],
}


def sha(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    n_fail = 0
    checks: list[dict] = []

    def chk(name: str, ok: bool, detail=None) -> None:
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    freeze = jload(AUD / "phase25a_canonical_final_freeze.json")
    p25b = jload(AUD / "phase25b_final_freeze.json")
    fc = jload(AUD / "phase24_v1_2_feature_spec_final_check.json")
    r1 = jload(AUD / "phase24_router_feature_reduction_contract_v1_2.json")
    r2 = jload(AUD / "phase24_roi_feature_mapping_contract_v1_2.json")
    r3 = jload(AUD / "phase24_scalar_feature_contract_v1_2.json")
    dim = jload(AUD / "phase24_router_feature_dimension_contract_v1_2.json")

    # -- Phase 25A canonical state
    chk("phase25a_canonical_notebook_sha_exact",
        sha(NB25A) == EXPECTED["phase25a_notebook_sha256"],
        sha(NB25A))
    chk("phase25a_canonical_final_checkpoint_sha_exact",
        freeze.get("canonical_final_checkpoint_sha256")
        == EXPECTED["phase25a_final_checkpoint_sha256"],
        freeze.get("canonical_final_checkpoint_sha256"))
    chk("phase25a_roi_proposal_threshold_0p30",
        freeze.get("roi_proposal_threshold") == EXPECTED["roi_proposal_threshold"],
        freeze.get("roi_proposal_threshold"))
    chk("phase25a_segmentation_threshold_0p50",
        freeze.get("segmentation_output_threshold") == EXPECTED["segmentation_output_threshold"],
        freeze.get("segmentation_output_threshold"))
    chk("phase25a_terminal_exact",
        freeze.get("terminal") == EXPECTED["phase25a_terminal"], freeze.get("terminal"))
    chk("phase25a_refiner_params",
        freeze.get("actual_parameter_count") == EXPECTED["phase25a_refiner_params"],
        freeze.get("actual_parameter_count"))
    chk("phase25a_gmacs",
        freeze.get("actual_gmacs") == EXPECTED["phase25a_gmacs"], freeze.get("actual_gmacs"))
    chk("phase25a_final_freeze_pass",
        freeze.get("verdict") == "PHASE25A_CANONICAL_FINAL_FREEZE_PASS"
        and freeze.get("n_failed") == 0,
        {"verdict": freeze.get("verdict"), "n_failed": freeze.get("n_failed")})

    # -- ROI-0.50 remains noncanonical + preserved
    sup = jload(AUD / "phase25a_roi050_supersession.json")
    chk("phase25a_roi050_noncanonical",
        sup.get("classification") == "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50"
        and sup.get("scientific_use_allowed") is False,
        sup.get("classification"))
    chk("phase25a_roi050_preserved", sup.get("preserved") is True, sup.get("preserved"))

    # -- Phase 25B blocked state
    chk("phase25b_blocked_artifact_exists",
        (AUD / "phase25b_final_freeze.json").exists())
    chk("phase25b_terminal_blocked",
        p25b.get("terminal") == EXPECTED["phase25b_terminal"], p25b.get("terminal"))
    chk("phase25b_feature_rows_0", p25b.get("feature_rows") == 0, p25b.get("feature_rows"))
    chk("phase25b_notebook_created_false",
        p25b.get("notebook_created") is False, p25b.get("notebook_created"))
    chk("phase25b_global_forward_replay_0",
        p25b.get("global_forward_replay_count") == 0, p25b.get("global_forward_replay_count"))
    chk("phase25b_router_training_0",
        p25b.get("router_training") == 0, p25b.get("router_training"))
    chk("phase25c_started_false", p25b.get("phase25c_started") is False)
    chk("phase25d_started_false", p25b.get("phase25d_started") is False)
    chk("phase25b_no_notebook_on_disk",
        not list((ROOT / "notebooks").rglob("*25b*")),
        [str(p) for p in (ROOT / "notebooks").rglob("*25b*")])
    chk("phase25b_no_feature_cache_on_disk",
        not list((ROOT / "data_cache").glob("*25b*")),
        [str(p) for p in (ROOT / "data_cache").glob("*25b*")])

    # -- Phase 24 provenance + v1.2 resolution state
    chk("phase24_v1_1_provenance_preserved",
        sha(ROOT / "notebooks" / "phasewise" / "phase_24_architecture_spec"
            / "phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb")
        == EXPECTED["phase24_v1_1_notebook_sha256"],
        EXPECTED["phase24_v1_1_notebook_sha256"])
    chk("phase24_v1_2_rf1_resolved", r1.get("verdict") == "RF1_RESOLVED", r1.get("verdict"))
    chk("phase24_v1_2_rf2_resolved", r2.get("verdict") == "RF2_RESOLVED", r2.get("verdict"))
    chk("phase24_v1_2_rf3_definitions_resolved",
        r3.get("unresolved_threshold_roles") == 0, r3.get("unresolved_threshold_roles"))

    # -- defects: either the PRE-REPAIR state (2 open, terminal BLOCKED) or the
    #    POST-CLOSURE state (2 resolved, terminal COMPLETE).  The gate is
    #    fail-closed on both: it must match exactly one of the two, never a
    #    third unexplained state.
    comp = jload(AUD / "phase24_router_feature_spec_completion_v1_2.json")
    failed_checks = [c["check"] for c in fc.get("checks", []) if not c["passed"]]
    expected_failed = ["RF3_predicted_roi_area_fraction_internally_consistent",
                       "router_param_count_consistent"]
    post_closure = (comp.get("verdict") == "RF1_RF2_RF3_D1_D2_RESOLVED"
                    and comp.get("fully_closed") is True)
    if post_closure:
        # defects resolved: the final check must be all-pass and the terminal COMPLETE
        chk("post_closure_no_failed_checks", failed_checks == [],
            {"failed_checks": failed_checks})
        chk("phase24_v1_2_terminal_complete",
            fc.get("terminal") == EXPECTED["phase24_v1_2_terminal_post_closure"],
            fc.get("terminal"))
        chk("post_closure_defects_remaining_0", fc.get("defects_remaining") == 0,
            fc.get("defects_remaining"))
    else:
        dr = comp.get("defects_reported", [])
        defect_ids = {d.get("id") for d in dr} if isinstance(dr, list) else set()
        chk("exactly_two_defects_D1_D2",
            sorted(failed_checks) == sorted(expected_failed),
            {"failed_checks": failed_checks, "defect_ids": sorted(defect_ids)})
        chk("phase24_v1_2_terminal_blocked",
            fc.get("terminal") == EXPECTED["phase24_v1_2_terminal"], fc.get("terminal"))
    chk("dimension_contract_present", bool(dim.get("dimension_contract")))

    # -- locks
    chk("holdout_outcome_reads_0", freeze.get("holdout_outcomes_read") == 0)
    chk("val_outcome_reads_0_for_repair", freeze.get("val_outcome_reads") == 0)
    chk("test_all_zero",
        all(freeze.get(k) == 0 for k in
            ("test_reads", "test_image_reads", "test_mask_reads", "test_inference")),
        {k: freeze.get(k) for k in
         ("test_reads", "test_image_reads", "test_mask_reads", "test_inference")})

    verdict = ("PROJECT_SYNC_PHASE24_V1_2_ENTRY_GATE_PASS" if n_fail == 0
               else "PROJECT_SYNC_PHASE24_V1_2_ENTRY_GATE_FAIL_CLOSED")

    out = {
        "artifact": "project_sync_phase24_v1_2_entry_gate",
        "phase": "24/25A/25B",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "expected": EXPECTED,
        "observed": {
            "phase25a_notebook_sha256": sha(NB25A),
            "phase25a_terminal": freeze.get("terminal"),
            "phase25b_terminal": p25b.get("terminal"),
            "phase24_v1_2_terminal": fc.get("terminal"),
            "phase24_v1_2_failed_checks": failed_checks,
        },
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": verdict,
        "fail_closed": n_fail != 0,
        "science_changed": False,
        "model_instantiations": 0,
        "training_runs": 0,
        "feature_rows_extracted": 0,
        "test_reads": 0,
    }
    (AUD / "project_sync_phase24_v1_2_entry_gate.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: "
              f"{json.dumps(c['detail'], ensure_ascii=False) if c['detail'] is not None else ''}")
    print()
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(verdict)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
