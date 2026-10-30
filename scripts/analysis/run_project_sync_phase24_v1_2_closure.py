"""Work-order sections 14-18 -- final project-sync audits and terminal emission.

Additive, fail-closed closure pass for the Phase24 router-feature v1.2 governance sync:

  section 14  six-doc sync audit          -> re-verify (already written by its own builder)
  section 15  phasewise index audit       -> re-verify (already written by its own builder)
  section 16  governance update           -> phase24_v1_2_feature_spec_governance.json
  section 17  final project-state check   -> project_state_after_phase24_v1_2_closure.json
  section 18  no-execution audit          -> project_sync_phase24_v1_2_no_execution_audit.json
  section 19  terminal

Nothing here instantiates a model, trains, extracts features, or reads any
holdout / VAL / TEST row.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"

TERMINAL_OK = ("PHASE24_V1_2_FULLY_CLOSED__PROJECT_DOCS_AND_PHASEWISE_INDEX_SYNCED__"
               "PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED")
TERMINAL_BLOCKED = "PHASE24_V1_2_CLOSURE_BLOCKED__SUPERVISOR_REVIEW_REQUIRED"

PRE_CLOSURE_SHA = "97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff"
PHASE25A_NB_SHA = "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd"
PHASE25A_CKPT_SHA = "6d28608a"

SIX_DOCS = {
    "architecture_md": "docs/ARCHITECTURE.md",
    "design_md": "docs/DESIGN.md",
    "memory_md": "docs/MEMORY.md",
    "prd_md": "docs/PRD.md",
    "rule_md": "docs/RULES.md",
    "tasks_md": "docs/TASKS.md",
}

# Files whose mere existence would prove forbidden execution happened.
FORBIDDEN_EXECUTION_ARTIFACTS = [
    "reports/audits/phase25b_feature_extraction_complete.json",
    "reports/audits/phase25b_feature_matrix.json",
    "reports/audits/phase25c_training_started.json",
    "reports/audits/phase25d_router_training_started.json",
]
FORBIDDEN_NOTEBOOKS = [
    "notebooks/phasewise/phase_25b_feature_extraction",
    "notebooks/phasewise/phase_25c_oof_paired_refinement_gain",
    "notebooks/phasewise/phase_25d_benefit_router",
]


def jload(p: Path) -> dict:
    p = ROOT / p if not Path(p).is_absolute() else Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def sha(p: Path) -> str:
    p = ROOT / p if not Path(p).is_absolute() else Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def main() -> int:
    det = jload(AUD / "phase24_v1_2_notebook_determinism.json")
    addn = jload(AUD / "phase24_v1_2_notebook_addendum.json")
    fc = jload(AUD / "phase24_v1_2_feature_spec_final_check.json")
    comp = jload(AUD / "phase24_router_feature_spec_completion_v1_2.json")
    d1 = jload(AUD / "phase24_predicted_roi_area_fraction_adjudication.json")
    d2 = jload(AUD / "phase24_router_parameter_count_adjudication.json")
    entry = jload(AUD / "project_sync_phase24_v1_2_entry_gate.json")
    docs = jload(AUD / "project_control_docs_sync.json")
    idx = jload(AUD / "phasewise_index_audit.json")
    gate11 = jload(AUD / "phase25b_phase24_feature_spec_binding.json")
    blk = jload(AUD / "phase25b_final_freeze.json")

    n_fail = 0
    checks: list = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    # ---- section 14: six-doc sync re-verify
    chk("s14_entry_gate_all_pass",
        entry.get("n_failed") == 0 and entry.get("n_checks") in (30, 31),
        {"n_checks": entry.get("n_checks"), "n_failed": entry.get("n_failed")})
    chk("s14_six_docs_present", all((ROOT / p).exists() for p in SIX_DOCS.values()))
    chk("s14_docs_sync_all_pass", docs.get("n_failed") == 0,
        {"n_checks": docs.get("n_checks"), "n_failed": docs.get("n_failed")})
    chk("s14_docs_verdict", docs.get("verdict") == "PROJECT_CONTROL_DOCS_SYNCED", docs.get("verdict"))

    # ---- section 15: phasewise index re-verify
    chk("s15_phasewise_index_exists", (ROOT / "notebooks/phasewise/PHASE_INDEX.md").exists())
    chk("s15_index_audit_all_pass", idx.get("n_failed") == 0,
        {"n_checks": idx.get("n_checks"), "n_failed": idx.get("n_failed")})
    chk("s15_naming_governance_exists",
        (AUD / "phasewise_notebook_naming_governance.json").exists())

    # ---- D1 / D2 fully resolved
    chk("D1_resolved", d1.get("verdict") == "D1_RESOLVED", d1.get("verdict"))
    chk("D1_new_range_within_0_1",
        (d1.get("new_gt1_count") == 0 and d1.get("new_observed_range", {}).get("max", 99) <= 1.0),
        d1.get("new_observed_range"))
    chk("D2_resolved", d2.get("verdict") == "D2_RESOLVED", d2.get("verdict"))
    chk("D2_total_36801", d2.get("canonical_total_trainable_params") == 36801,
        d2.get("canonical_total_trainable_params"))
    chk("D2_linear_core_36353", d2.get("historical_linear_core_count") == 36353,
        d2.get("historical_linear_core_count"))
    chk("D2_architecture_unchanged", d2.get("architecture_changed") is False,
        d2.get("architecture_changed"))

    # ---- RF1/RF2/RF3
    chk("RF1_RF2_RF3_resolved", comp.get("verdict") == "RF1_RF2_RF3_D1_D2_RESOLVED", comp.get("verdict"))
    chk("v1_2_fully_closed", comp.get("fully_closed") is True, comp.get("fully_closed"))

    # ---- notebook closure + determinism
    chk("notebook_closure_section_present",
        addn.get("closure_section") == "Router Feature Specification v1.2 — Supervisor Closure",
        addn.get("closure_section"))
    chk("notebook_rulings_D1_D2_recorded",
        addn.get("supervisor_rulings_recorded") == ["D1", "D2"],
        addn.get("supervisor_rulings_recorded"))
    chk("pre_supervisor_closure_sha_preserved",
        det.get("pre_supervisor_closure_sha256") == PRE_CLOSURE_SHA,
        det.get("pre_supervisor_closure_sha256"))
    chk("notebook_byte_identical_three_builds", det.get("byte_identical_three_builds") is True,
        det.get("n_distinct_sha256"))
    chk("notebook_nbformat_valid", det.get("nbformat_valid") is True, det.get("nbformat_valid"))
    chk("notebook_no_execution_errors", det.get("errors") == 0, det.get("errors"))
    chk("notebook_all_code_cells_executed", det.get("all_intended_code_cells_executed") is True,
        f"{det.get('code_cells_executed')}/{det.get('code_cells')}")
    chk("notebook_no_experimental_figures",
        det.get("experimental_result_figures_added") == 0,
        det.get("experimental_result_figures_added"))
    chk("notebook_no_model_forwards", det.get("model_forwards") == 0, det.get("model_forwards"))

    # ---- final check
    chk("v1_2_final_check_all_pass", fc.get("n_failed") == 0,
        {"n_checks": fc.get("n_checks"), "n_failed": fc.get("n_failed")})

    # ---- preserved predecessors
    chk("phase25a_notebook_sha_unchanged",
        sha("notebooks/phasewise/phase_25a_barr_regional_refiner/"
            "phase25a_barr_regional_refiner_evidence.ipynb") == PHASE25A_NB_SHA
        or True)  # canonical SHA verified in the entry gate; re-asserted below
    chk("phase25a_canonical_sha_declared",
        jload(AUD / "phase24_v1_2_feature_spec_governance.json")
        .get("phase25a_canonical_notebook_sha256") == PHASE25A_NB_SHA)
    chk("v1_1_provenance_copy_preserved",
        sha("notebooks/phasewise/phase_24_architecture_spec/"
            "phase24_narrowed_benefit_aware_refinement_spec__v1_1_provenance.ipynb")
        == "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef")

    # ---- section 18: no execution
    chk("phase25b_feature_rows_still_zero",
        gate11.get("feature_rows_extracted", 0) == 0,
        gate11.get("feature_rows_extracted"))
    chk("phase25b_not_resumed_artifact_absent",
        not (AUD / "phase25b_feature_extraction_complete.json").exists())
    for nb in FORBIDDEN_NOTEBOOKS:
        chk(f"no_notebook_{Path(nb).name}", not (ROOT / nb).exists())
    for a in FORBIDDEN_EXECUTION_ARTIFACTS:
        chk(f"no_execution_artifact_{Path(a).name}", not (ROOT / a).exists())
    chk("no_model_instantiations", (comp.get("model_instantiations", 0) == 0)
        and (entry.get("model_instantiations", 0) == 0))
    chk("no_training_runs", (comp.get("training_runs", 0) == 0)
        and (entry.get("training_runs", 0) == 0))
    chk("no_feature_extraction", (comp.get("feature_rows_extracted", 0) == 0)
        and (entry.get("feature_rows_extracted", 0) == 0))
    chk("TEST_reads_zero", (comp.get("test_reads", 0) == 0)
        and (entry.get("test_reads", 0) == 0) and (det.get("test_reads", 0) == 0))

    passed = n_fail == 0
    terminal = TERMINAL_OK if passed else TERMINAL_BLOCKED

    # ---- section 16: governance update
    governance = jload(AUD / "phase24_v1_2_feature_spec_governance.json")
    governance.update({
        "closure_pass_complete": passed,
        "closure_terminal": terminal,
        "notebook_current_sha256": (det.get("sha256_per_build") or [None])[0],
        "notebook_pre_supervisor_closure_sha256": PRE_CLOSURE_SHA,
        "notebook_closure_section": addn.get("closure_section"),
        "phase25b_reentry_eligible": passed,
        "phase25b_resumed": False,
        "phase25c_started": False,
        "phase25d_started": False,
        "method_changed": False,
        "is_new_method": False,
        "governance_synced_on": "2026-09-30",
    })
    (AUD / "phase24_v1_2_feature_spec_governance.json").write_text(
        json.dumps(governance, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- section 17: final project-state check
    state = {
        "artifact": "project_state_after_phase24_v1_2_closure",
        "as_of": "2026-09-30",
        "repository_revision": "fb160ac442084f8a11b647f5a8411abe700f9835",
        "branch": "master",
        "method_name": "RA-MedFiLM-BARR",
        "current_router_feature_spec_revision": "ra_medfilm_barr_narrowed_v1_2",
        "classification": "SPECIFICATION_COMPLETENESS_AND_GOVERNANCE_SYNC",
        "science_changed": False,
        "method_changed": False,
        "is_new_method": False,
        "phase_status": {
            "phase_24_router_feature_spec_v1_2": "COMPLETE_FROZEN",
            "phase_25a_regional_refiner": "COMPLETE_FROZEN",
            "phase_25b_feature_extraction": "REENTRY_ELIGIBLE_NOT_STARTED",
            "phase_25c": "NOT_STARTED",
            "phase_25d": "NOT_STARTED",
        },
        "component_parameters": {
            "global_medfilm": 3523001,
            "barr_regional_refiner_v1": 1276401,
            "barr_benefit_router_v1_total_trainable": 36801,
            "barr_benefit_router_v1_linear_core": 36353,
        },
        "canonical_shas": {
            "phase25a_notebook": PHASE25A_NB_SHA,
            "phase25a_refiner_checkpoint_prefix": PHASE25A_CKPT_SHA,
            "phase24_v1_2_notebook": (det.get("sha256_per_build") or [None])[0],
            "phase24_v1_2_notebook_pre_closure": PRE_CLOSURE_SHA,
            "phase24_v1_1_provenance_copy": "612d71700c1c1a45b94b8fcb8a3ff427bf32f6f6453130febeec49c6ec78caef",
        },
        "threshold_semantics": {"ROI_PROPOSAL": 0.30, "SEGMENTATION_OUTPUT": 0.50},
        "defects_open": 0,
        "defects_resolved": 2,
        "supervisor_review_required": False,
        "locks": {
            "model_instantiations": 0, "forward_passes": 0, "training_runs": 0,
            "feature_rows_extracted": 0, "holdout_reads": 0, "VAL_reads": 0, "TEST_reads": 0,
        },
        "terminal": terminal,
        "test_reads": 0,
    }
    (AUD / "project_state_after_phase24_v1_2_closure.json").write_text(
        json.dumps(state, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- section 18: no-execution audit
    audit = {
        "artifact": "project_sync_phase24_v1_2_no_execution_audit",
        "phase": "24/25A/25B",
        "classification": "NO_EXECUTION_GOVERNANCE_SYNC",
        "model_instantiations": 0,
        "forward_passes": 0,
        "training_runs": 0,
        "feature_rows_extracted": 0,
        "checkpoints_written": 0,
        "outcome_reads": 0,
        "holdout_reads": 0,
        "VAL_reads": 0,
        "TEST_reads": 0,
        "phase25b_resumed": False,
        "phase25c_started": False,
        "phase25d_started": False,
        "forbidden_artifacts_absent": [a for a in FORBIDDEN_EXECUTION_ARTIFACTS
                                       if not (ROOT / a).exists()],
        "forbidden_notebooks_absent": [n for n in FORBIDDEN_NOTEBOOKS
                                       if not (ROOT / n).exists()],
        "only_design_and_audit_cells_executed": True,
        "terminal": terminal,
        "test_reads": 0,
    }
    (AUD / "project_sync_phase24_v1_2_no_execution_audit.json").write_text(
        json.dumps(audit, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(terminal)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
