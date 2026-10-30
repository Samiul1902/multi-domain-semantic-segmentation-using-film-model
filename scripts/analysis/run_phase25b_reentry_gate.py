"""Phase 25B RE-ENTRY -- fail-closed gate (work-order section 1).

Verifies all pre-conditions before any global forward replay or feature
extraction.  Any disagreement -> STOP, no extraction.

Emits reports/audits/phase25b_reentry_gate.json
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

EXPECTED = {
    "predecessor_terminal": ("PHASE24_V1_2_FULLY_CLOSED__PROJECT_DOCS_AND_PHASEWISE_INDEX_SYNCED__"
                             "PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED"),
    "method": "RA-MedFiLM-BARR",
    "feature_spec_revision": "ra_medfilm_barr_narrowed_v1_2",
    "phase24_notebook_sha": "9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027",
    "phase25a_notebook_sha": "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd",
    "phase25a_refiner_ckpt_sha": "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109",
    "phase21_global_ckpt_sha": "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
    "master_seed": 42,
    "router_development_n": 4957,
    "router_holdout_n": 875,
    "roi_proposal_threshold": 0.30,
    "segmentation_output_threshold": 0.50,
    "split_manifest_sha": "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
    "linear_core_params": 36353,
    "total_trainable_params": 36801,
    "deep_dim": 192,
    "scalar_dim": 10,
    "numeric_dim": 202,
    "task_emb_dim": 16,
    "router_input_dim": 218,
}

PHASE24_V1_2_NB = (ROOT / "notebooks" / "phasewise" / "phase_24_architecture_spec"
                   / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
PHASE25A_NB = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
               / "phase25a_dedicated_regional_refiner.ipynb")
PHASE21_CKPT = (ROOT / "checkpoints" / "phase21_global_medfilm_fourdomain_seed42_clean_v3"
                / "best.pt")
REFINER_CKPT = (ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
                / "final" / "final.pt")
ROI030_CACHE = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
ROI050_CACHE = ROOT / "data_cache" / "phase25a_global_cache"
PHASE25B_CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
PHASE25B_NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_25b_gt_free_features"
PHASE25B_NB = PHASE25B_NB_DIR / "phase25b_gt_free_pre_refinement_features.ipynb"


def sha(p: Path):
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    n_fail = 0
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        nonlocal n_fail
        checks.append({"check": name, "passed": bool(ok), "detail": detail})
        if not ok:
            n_fail += 1

    state = jload(AUD / "project_state_after_phase24_v1_2_closure.json")
    fc = jload(AUD / "phase24_v1_2_feature_spec_final_check.json")
    comp = jload(AUD / "phase24_router_feature_spec_completion_v1_2.json")
    d1 = jload(AUD / "phase24_predicted_roi_area_fraction_adjudication.json")
    d2 = jload(AUD / "phase24_router_parameter_count_adjudication.json")
    dim = jload(AUD / "phase24_router_feature_dimension_contract_v1_2.json")
    blk = jload(AUD / "phase25b_final_freeze.json")
    roi030_manifest = jload(ROI030_CACHE / "cache_manifest.json")

    # -- 1 project-state terminal exact
    chk("project_state_terminal_exact",
        state.get("terminal") == EXPECTED["predecessor_terminal"], state.get("terminal"))

    # -- 2/3 Phase24 v1.2 status + final check
    ps = (state.get("phase_status") or {})
    chk("phase24_v1_2_status_complete_frozen",
        ps.get("phase_24_router_feature_spec_v1_2") == "COMPLETE_FROZEN",
        ps.get("phase_24_router_feature_spec_v1_2"))
    chk("phase24_v1_2_final_check_pass",
        fc.get("final_check_pass") is True and fc.get("n_failed") == 0,
        {"n_checks": fc.get("n_checks"), "n_failed": fc.get("n_failed")})

    # -- 4..11 resolution flags
    chk("RF1_RESOLVED", fc.get("RF1_RESOLVED") is True)
    chk("RF2_RESOLVED", fc.get("RF2_RESOLVED") is True)
    chk("RF3_FULLY_RESOLVED", fc.get("RF3_FULLY_RESOLVED") is True)
    chk("D1_RESOLVED", fc.get("D1_RESOLVED") is True and d1.get("verdict") == "D1_RESOLVED",
        d1.get("verdict"))
    chk("D2_RESOLVED", fc.get("D2_RESOLVED") is True and d2.get("verdict") == "D2_RESOLVED",
        d2.get("verdict"))
    summ = fc.get("summary") or {}
    chk("unresolved_feature_definitions_0", summ.get("unresolved_feature_definitions") == 0,
        summ.get("unresolved_feature_definitions"))
    chk("unresolved_threshold_roles_0", summ.get("unresolved_threshold_roles") == 0,
        summ.get("unresolved_threshold_roles"))
    chk("unresolved_supervisor_decisions_0", summ.get("unresolved_supervisor_decisions") == 0,
        summ.get("unresolved_supervisor_decisions"))

    # -- 12..15 SHAs
    chk("phase24_notebook_sha_exact",
        sha(PHASE24_V1_2_NB) == EXPECTED["phase24_notebook_sha"], sha(PHASE24_V1_2_NB))
    chk("phase25a_notebook_sha_exact",
        sha(PHASE25A_NB) == EXPECTED["phase25a_notebook_sha"], sha(PHASE25A_NB))
    chk("phase25a_refiner_checkpoint_sha_exact",
        sha(REFINER_CKPT) == EXPECTED["phase25a_refiner_ckpt_sha"], sha(REFINER_CKPT))
    chk("phase21_global_checkpoint_sha_exact",
        sha(PHASE21_CKPT) == EXPECTED["phase21_global_ckpt_sha"], sha(PHASE21_CKPT))

    # -- 16/17 thresholds
    chk("roi_proposal_threshold_0p30",
        abs(roi030_manifest.get("roi_proposal_threshold", -1) - 0.30) < 1e-12,
        roi030_manifest.get("roi_proposal_threshold"))
    chk("segmentation_output_threshold_0p50",
        abs(roi030_manifest.get("segmentation_output_threshold", -1) - 0.50) < 1e-12,
        roi030_manifest.get("segmentation_output_threshold"))

    # -- 18/19 population
    split_sha = sha(AUD / "phase24_router_split_manifest.csv")
    rows = list(csv.DictReader(open(AUD / "phase24_router_split_manifest.csv",
                                    newline="", encoding="utf-8")))
    from collections import Counter
    roles = Counter(r["split_role"] for r in rows)
    chk("router_development_n_4957",
        roles.get("ROUTER_DEVELOPMENT") == EXPECTED["router_development_n"],
        roles.get("ROUTER_DEVELOPMENT"))
    chk("router_holdout_n_875",
        roles.get("ROUTER_HOLDOUT") == EXPECTED["router_holdout_n"],
        roles.get("ROUTER_HOLDOUT"))
    chk("split_manifest_sha_exact", split_sha == EXPECTED["split_manifest_sha"], split_sha)

    # -- 20 old ROI-0.50 run noncanonical
    pointer = jload(AUD / "phase25a_canonical_governance_pointer.json")
    sup = pointer.get("superseded") or {}
    chk("old_roi050_phase25a_noncanonical",
        ROI050_CACHE.exists()
        and sup.get("classification") == "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50"
        and sup.get("scientific_use_allowed") is False
        and sup.get("preserved") is True,
        {"superseded_classification": sup.get("classification"),
         "scientific_use_allowed": sup.get("scientific_use_allowed"),
         "roi050_cache_exists": ROI050_CACHE.exists()})

    # -- 21 blocked attempt preserved
    chk("phase25b_blocked_attempt_preserved",
        blk.get("terminal") == "PHASE25B_BLOCKED__FROZEN_FEATURE_SPEC_INCOMPLETE"
        and blk.get("classification") == "BLOCKED_PRE_EXECUTION__FROZEN_FEATURE_SPEC_INCOMPLETE",
        blk.get("terminal"))

    # -- 22/23 successful cache + notebook not present
    chk("phase25b_successful_cache_absent", not PHASE25B_CACHE.exists(),
        str(PHASE25B_CACHE))
    chk("canonical_phase25b_notebook_absent", not PHASE25B_NB.exists(), str(PHASE25B_NB))

    # -- 24/25 Phase25C / 25D not started
    chk("phase25c_started_false", ps.get("phase_25c") == "NOT_STARTED", ps.get("phase_25c"))
    chk("phase25d_started_false", ps.get("phase_25d") == "NOT_STARTED", ps.get("phase_25d"))

    # -- 26..28 locks
    locks = state.get("locks") or {}
    chk("holdout_outcome_reads_0", locks.get("holdout_reads") == 0, locks.get("holdout_reads"))
    chk("VAL_reads_for_phase25b_0", locks.get("VAL_reads") == 0, locks.get("VAL_reads"))
    chk("TEST_all_zero", locks.get("TEST_reads") == 0, locks.get("TEST_reads"))
    chk("no_25c_25d_artifact",
        not (AUD / "phase25c_training_started.json").exists()
        and not (AUD / "phase25d_router_training_started.json").exists())

    # -- dimension + parameter contract
    dc = dim.get("dimension_contract") or {}
    chk("dimension_contract_202_16_218",
        dc.get("phase25b_numeric_matrix") == 202
        and dc.get("future_phase25d_task_embedding") == 16
        and dc.get("future_router_input") == 218, dc)
    pcon = dim.get("trainable_parameter_contract") or {}
    chk("router_param_36801_36353",
        pcon.get("router_total_trainable_parameters") == 36801
        and pcon.get("router_linear_core_parameters") == 36353, pcon)
    chk("roi030_action_available_4957",
        roi030_manifest.get("action_available_n") == 4957
        and roi030_manifest.get("action_unavailable_global_empty_n") == 0,
        {"action_available_n": roi030_manifest.get("action_available_n"),
         "unavail": roi030_manifest.get("action_unavailable_global_empty_n")})

    passed = n_fail == 0
    verdict = ("PHASE25B_REENTRY_GATE_PASS" if passed
               else "PHASE25B_REENTRY_GATE_FAIL_CLOSED")

    out = {
        "artifact": "phase25b_reentry_gate",
        "phase": "25B",
        "classification": "FAIL_CLOSED_PRE_EXTRACTION_GATE",
        "method": EXPECTED["method"],
        "feature_spec_revision": EXPECTED["feature_spec_revision"],
        "predecessor_terminal": state.get("terminal"),
        "expected": EXPECTED,
        "observed": {
            "phase24_notebook_sha": sha(PHASE24_V1_2_NB),
            "phase25a_notebook_sha": sha(PHASE25A_NB),
            "phase25a_refiner_ckpt_sha": sha(REFINER_CKPT),
            "phase21_global_ckpt_sha": sha(PHASE21_CKPT),
            "split_manifest_sha": split_sha,
            "router_development_n": roles.get("ROUTER_DEVELOPMENT"),
            "router_holdout_n": roles.get("ROUTER_HOLDOUT"),
        },
        "checks": checks,
        "n_checks": len(checks),
        "n_failed": n_fail,
        "verdict": verdict,
        "fail_closed": True,
        "model_instantiations": 0,
        "forward_passes": 0,
        "training_runs": 0,
        "feature_rows_extracted": 0,
        "test_reads": 0,
    }
    (AUD / "phase25b_reentry_gate.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['passed'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print()
    print(f"{len(checks) - n_fail}/{len(checks)} PASS")
    print(verdict)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
