"""Phase 25B -- project status sync + FINAL FREEZE + terminal (sections 29-31).

Assembles the canonical Phase25B completion freeze from every audit/table/figure
artifact, syncs the project-control documents, and emits the success terminal.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIGD = ROOT / "reports" / "figures" / "phase25b_gt_free_features"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
NB = (ROOT / "notebooks" / "phasewise" / "phase_25b_gt_free_features"
      / "phase25b_gt_free_pre_refinement_features.ipynb")
UTC = datetime.now(timezone.utc).isoformat()

TERMINAL = ("PHASE25B_GT_FREE_PRE_REFINEMENT_FEATURES_COMPLETE__"
            "202D_CANONICAL_FEATURE_CACHE_FROZEN__PHASE25C_ELIGIBLE_NOT_STARTED")

PREDECESSOR = ("PHASE24_V1_2_FULLY_CLOSED__PROJECT_DOCS_AND_PHASEWISE_INDEX_SYNCED__"
               "PHASE25B_REENTRY_ELIGIBLE_NOT_STARTED")
# SHA of reports/audits/phase25b_final_freeze.json BEFORE the handoff-semantics repair
PRE_REPAIR_FREEZE_SHA = "4ed102e9dd53390c832d7396f42c25396093febb16925a6cb18fafbc2fb5ad01"
PHASE24_NB_SHA = "9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027"
PHASE25A_NB_SHA = "fd2bab0168eb3477125c655ada1bd5eb4b060f41a5b354fdbaaf6fd621dfb2dd"
PHASE21_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
REFINER_SHA = "6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"


def sha(p: Path) -> str:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    rg = jload(AUD / "phase25b_reentry_gate.json")
    eq = jload(AUD / "phase25b_global_forward_equivalence.json")
    ci = jload(AUD / "phase25b_feature_cache_integrity.json")
    det = jload(AUD / "phase25b_feature_determinism.json")
    ts = jload(AUD / "phase25b_implementation_test_suite.json")
    sg = jload(AUD / "phase25b_scope_guard.json")
    tl = jload(AUD / "phase25b_test_lock_audit.json")
    tz = jload(AUD / "phase25b_threshold_semantics_audit.json")
    ng = jload(AUD / "phase25b_no_gt_leakage_audit.json")
    nvi = jload(AUD / "phase25b_notebook_visual_integrity.json")
    ndet = jload(AUD / "phase25b_notebook_determinism.json")
    hs = jload(AUD / "phase25b_phase25c_handoff_schema.json")
    fm = jload(FIGD / "phase25b_figure_manifest.json")

    n_tables = len(list(TAB.glob("phase25b_*.csv")))
    n_figures = int(fm.get("n_figures") or 0)

    checks_all = [
        rg.get("verdict") == "PHASE25B_REENTRY_GATE_PASS",
        eq.get("verdict") == "PHASE25B_GLOBAL_FORWARD_EQUIVALENCE_PASS",
        ci.get("verdict") == "PHASE25B_FEATURE_CACHE_INTEGRITY_PASS",
        det.get("verdict") == "PHASE25B_FEATURE_DETERMINISM_PASS",
        ts.get("verdict") == "PHASE25B_IMPLEMENTATION_TESTS_PASS",
        sg.get("verdict") == "PHASE25B_SCOPE_GUARD_PASS",
        tl.get("verdict") == "PHASE25B_TEST_LOCK_PASS",
        tz.get("verdict") == "PHASE25B_THRESHOLD_SEMANTICS_COMPLETE",
        ng.get("verdict") == "PHASE25B_NO_GT_LEAKAGE_PASS",
        nvi.get("verdict") == "PHASE25B_NOTEBOOK_VISUAL_INTEGRITY_PASS",
        ndet.get("byte_identical") is True,
        hs.get("verdict") == "PHASE25B_PHASE25C_OOF_GAIN_HANDOFF_READY",
        n_tables >= 8,
        n_figures >= 6,
        NB.exists(),
    ]
    all_pass = all(checks_all)

    freeze = {
        "artifact": "phase25b_final_freeze",
        "phase": "25B",
        "method": "RA-MedFiLM-BARR",
        "architecture_revision": "ra_medfilm_barr_narrowed_v1_2",
        "master_development_seed": 42,
        "classification": "COMPLETE_FROZEN",
        "predecessor_terminal": PREDECESSOR,
        "phase24_notebook_sha256": PHASE24_NB_SHA,
        "phase25a_notebook_sha256": PHASE25A_NB_SHA,
        "phase25a_refiner_checkpoint_sha256": REFINER_SHA,
        "phase21_global_checkpoint_sha256": PHASE21_SHA,
        "split_manifest_sha256": SPLIT_SHA,
        "canonical_roi_proposal_threshold": 0.30,
        "canonical_segmentation_output_threshold": 0.50,
        "population": "ROUTER_DEVELOPMENT",
        "router_development_n": 4957,
        "router_holdout_n": 875,
        "feature_rows": int(ci.get("feature_rows") or 0),
        "numeric_feature_dimensions": int(ci.get("columns") or 0),
        "deep_dimensions": 192,
        "scalar_descriptors": 10,
        "task_embedding_generated": False,
        "future_router_dimensions": 218,
        "matrix_sha256": ci.get("matrix_sha256"),
        "metadata_sha256": ci.get("metadata_sha256"),
        "schema_sha256": ci.get("schema_sha256"),
        "feature_cache_dir": str(CACHE.relative_to(ROOT)).replace("\\", "/"),
        "global_forward_replay_count": eq.get("n_samples_compared"),
        "global_forward_equivalence": {"verdict": eq.get("verdict"),
                                       "max_abs": eq.get("max_abs_difference"),
                                       "byte_identical": eq.get("byte_identical_achieved")},
        "feature_determinism": {"verdict": det.get("verdict"),
                                "subset_size": det.get("subset_size"),
                                "run1_vs_run2_max_abs": det.get("run1_vs_run2", {}).get("max_abs"),
                                "run1_vs_frozen_max_abs": det.get("run1_vs_frozen_cache", {}).get("max_abs")},
        "nan": ci.get("nan_count"), "inf": ci.get("inf_count"),
        "gt_derived_features": 0,
        "refiner_forwards": 0,
        "paired_gain_labels": 0,
        "router_training": 0,
        "post_safety_training": 0,
        "holdout_feature_extraction": 0,
        "holdout_outcomes": 0,
        "val_feature_extraction": 0,
        "val_outcomes": 0,
        "test_reads": 0,
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "notebook_sha256": sha(NB),
        "notebook_3x_deterministic": ndet.get("byte_identical"),
        "notebook_cells": nvi.get("n_cells"),
        "notebook_code_cells": nvi.get("n_code"),
        "figures_created": n_figures,
        "tables_created": n_tables,
        "audits_total": len(list(AUD.glob("phase25b_*.json"))),
        "scope_guard_verdict": sg.get("verdict"),
        "test_lock_verdict": tl.get("verdict"),
        "implementation_tests_verdict": ts.get("verdict"),
        "threshold_semantics_verdict": tz.get("verdict"),
        "no_gt_leakage_verdict": ng.get("verdict"),
        "phase25c_handoff_verdict": hs.get("verdict"),
        "phase25b_complete": all_pass,
        "phase25c_started": False,
        "phase25d_started": False,
        "terminal": TERMINAL if all_pass else "PHASE25B_FREEZE_INCOMPLETE",
        "downstream_stage_ownership": {
            "phase_25c": "OOF paired refinement-gain label generation",
            "phase_25d": "benefit-router training",
            "task_embedding_owner": "PHASE25D",
            "benefit_router_owner": "PHASE25D",
            "paired_gain_label_owner": "PHASE25C",
        },
        "handoff_semantics_repaired": True,
        "pre_repair_final_freeze_sha256": PRE_REPAIR_FREEZE_SHA,
        "resumption_condition": ("Phase25C may begin leak-age-safe OOF paired refinement-gain "
                                 "label generation using the frozen fold-specific canonical "
                                 "ROI-0.30 refiners; benefit-router training remains Phase25D."),
        "next_authorized_phase": ("PHASE25C — OOF paired refinement-gain label generation — "
                                  "eligible, NOT started"),
        "generated_utc": UTC,
    }
    (AUD / "phase25b_final_freeze.json").write_text(
        json.dumps(freeze, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---------------- project status sync ---------------- #
    sync = {
        "artifact": "phase25b_project_status_sync",
        "phase": "25B",
        "terminal": freeze["terminal"],
        "generated_utc": UTC,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "phase_status": {
            "phase_24_router_feature_spec_v1_2": "COMPLETE_FROZEN",
            "phase_25a_regional_refiner_roi030": "COMPLETE_FROZEN",
            "phase_25b_gt_free_features": "COMPLETE_FROZEN",
            "phase_25c_oof_paired_gain_labels": "ELIGIBLE_NOT_STARTED",
            "phase_25d_benefit_router": "NOT_STARTED",
            "phase_25e_resource_gate": "NOT_STARTED",
            "phase_25f_post_safety_and_fusion": "NOT_STARTED",
            "phase_25g_controlled_validation": "NOT_STARTED",
        },
        "retired_phase_keys": [],
        "retired_stage_aliases": [
            {"alias": "router training mapped to phase 25C", "status": "RETIRED",
             "corrected_to": "phase_25d_benefit_router"},
        ],
        "stage_semantics_note": ("router training and the 16-D task embedding belong to "
                                "Phase25D; Phase25C generates OOF paired-gain labels only"),
        "stage_semantics_repair": {
            "classification": "DOCUMENTATION_AND_GOVERNANCE_REPAIR_ONLY",
            "science_changed": False,
            "feature_cache_changed": False,
            "model_execution_required": False,
        },
        "phase25b_terminal": TERMINAL,
        "frozen_artifacts": {
            "feature_cache": str(CACHE.relative_to(ROOT)).replace("\\", "/"),
            "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
            "notebook_sha256": sha(NB),
            "figures_dir": "reports/figures/phase25b_gt_free_features",
        },
        "all_gates_pass": all_pass,
        "locks": {"test_reads": 0, "holdout_feature_extraction": 0,
                  "holdout_outcomes": 0, "val_feature_extraction": 0,
                  "val_outcomes": 0, "router_training": 0,
                  "refiner_forwards": 0, "paired_gain_labels": 0},
        "next_authorized_phase": "PHASE25C -- eligible, NOT started",
    }
    (AUD / "phase25b_project_status_sync.json").write_text(
        json.dumps(sync, indent=1, ensure_ascii=False), encoding="utf-8")

    print("=== Phase 25B final freeze ===")
    for k in ("feature_rows", "numeric_feature_dimensions", "notebook_cells",
              "figures_created", "tables_created", "audits_total"):
        print(f"  {k:28s}: {freeze[k]}")
    print(f"  {'equivalence':28s}: {freeze['global_forward_equivalence']}")
    print(f"  {'determinism':28s}: {freeze['feature_determinism']['verdict']}")
    print(f"  {'notebook 3x det':28s}: {freeze['notebook_3x_deterministic']}")
    print(f"  all_pass: {all_pass}")
    print()
    print(freeze["terminal"])
    return 0 if all_pass else 2


if __name__ == "__main__":
    sys.exit(main())
