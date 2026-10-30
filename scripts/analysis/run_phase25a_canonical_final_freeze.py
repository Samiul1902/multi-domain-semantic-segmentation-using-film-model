"""Phase 25A (CANONICAL RERUN) — CANONICAL FINAL FREEZE.

Assembles ``reports/audits/phase25a_canonical_final_freeze.json`` for the
ROI-0.30 canonical execution and verifies every deliverable is present and
internally consistent. Fails closed.

Also writes an ADDITIVE governance pointer update. The old ROI-0.50 final freeze
is NOT deleted and NOT overwritten.

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25a_canonical_final_freeze.py
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
FIG = ROOT / "reports" / "figures" / "phase25a_regional_refiner"
CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1_roi030"
OLD_CKPT = ROOT / "checkpoints" / "phase25a_barr_regional_refiner_v1_1"
EXP = ROOT / "experiments" / "phase25a_barr_regional_refiner_v1_1_roi030"
NB = (ROOT / "notebooks" / "phasewise" / "phase_25a_regional_refiner"
      / "phase25a_dedicated_regional_refiner.ipynb")

SUPERSEDED_NB_SHA = "7dfcf50540ee531e330c0338ea9326cdb73c24c9f8254b920c022598dd74733f"
TERMINAL = ("PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__"
            "SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED")

from src.data.barr_roi import ROI_PROPOSAL_THRESHOLD, SEGMENTATION_OUTPUT_THRESHOLD  # noqa: E402
from src.models.barr import BARR_REFINER_EXPECTED_PARAMETERS  # noqa: E402


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def jload(p: Path) -> dict:
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def main() -> int:
    checks: list[dict] = []

    def chk(name, ok, detail=None):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})
        return bool(ok)

    cm = jload(ROOT / "data_cache" / "phase25a_barr_roi030_cache" / "cache_manifest.json")
    prov = jload(AUD / "phase25a_roi030_cache_provenance.json")
    rule = jload(AUD / "phase25a_roi030_final_refit_epoch_rule.json")
    ts = jload(AUD / "phase25a_threshold_semantics_audit.json")
    vi = jload(AUD / "phase25a_roi030_notebook_visual_integrity.json")
    det = jload(AUD / "phase25a_roi030_notebook_determinism.json")
    post = jload(AUD / "phase25a_post_threshold_repair_final_check.json")
    ra = jload(AUD / "phase25a_resource_accounting.json")
    scope = jload(AUD / "phase25a_scope_guard.json")
    adj = jload(AUD / "phase24_phase25_roi_threshold_adjudication.json")
    sup = jload(AUD / "phase25a_roi050_supersession.json")

    fold_runs = {d: jload(EXP / d / "run.json") for d in ("fold0", "fold1", "fold2", "final_refit")}
    fold_bests = {d: fold_runs[d].get("best_epoch") for d in ("fold0", "fold1", "fold2")}

    # ---- canonical identity ------------------------------------------- #
    chk("roi_proposal_threshold_0p30", abs(ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12,
        ROI_PROPOSAL_THRESHOLD)
    chk("segmentation_output_threshold_0p50",
        abs(SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12, SEGMENTATION_OUTPUT_THRESHOLD)
    chk("adjudication_present", adj.get("classification") ==
        "FROZEN_SPEC_CLARIFICATION__NOT_SCIENCE_CHANGE", adj.get("classification"))
    chk("supersession_present", sup.get("classification") ==
        "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50", sup.get("classification"))

    # ---- cache / population -------------------------------------------- #
    chk("canonical_cache_present", abs(float(cm.get("roi_proposal_threshold", -1)) - 0.30) < 1e-12
        and cm.get("prob512_dtype") == "float32", str(cm.get("roi_proposal_threshold")))
    chk("cache_provenance_pass",
        prov.get("verdict") == "PHASE25A_ROI030_CACHE_PROVENANCE_PASS", prov.get("verdict"))
    chk("population_4957", cm.get("population_n") == 4957, cm.get("population_n"))

    # ---- folds ---------------------------------------------------------- #
    three_trained = all(fold_runs[d].get("stop_reason") for d in ("fold0", "fold1", "fold2"))
    chk("three_folds_trained", three_trained, fold_bests)
    chk("canonical_best_epochs_persisted", all(v is not None for v in fold_bests.values()),
        fold_bests)
    e = sorted(v for v in fold_bests.values() if v is not None)
    chk("refit_rule_derived_from_roi030_folds",
        len(e) == 3 and rule.get("final_refit_epochs") == e[1]
        and rule.get("source_best_epochs") == e,
        {"source": e, "final_refit_epochs": rule.get("final_refit_epochs")})
    chk("final_refiner_trained",
        (CKPT / "final" / "final.pt").exists()
        and fold_runs["final_refit"].get("epochs_completed") == rule.get("final_refit_epochs"),
        {"epochs": fold_runs["final_refit"].get("epochs_completed")})

    # ---- checkpoints ---------------------------------------------------- #
    ckpt_shas = {str(f.relative_to(ROOT)).replace("\\", "/"): sha(f)
                 for f in sorted(CKPT.rglob("*.pt"))}
    chk("checkpoints_all_present",
        all((CKPT / d / f).exists() for d in ("fold0", "fold1", "fold2")
            for f in ("best.pt", "latest.pt"))
        and (CKPT / "final" / "final.pt").exists(),
        sorted(ckpt_shas))
    old_ckpt = sorted(str(f.relative_to(ROOT)).replace("\\", "/") for f in OLD_CKPT.rglob("*.pt"))
    chk("old_roi050_checkpoints_preserved", len(old_ckpt) == 8, len(old_ckpt))

    # ---- tables / figures ----------------------------------------------- #
    req_tables = ["phase25a_roi030_population_accounting.csv",
                  "phase25a_roi030_action_availability_by_domain.csv",
                  "phase25a_roi030_fold0_training_history.csv",
                  "phase25a_roi030_fold1_training_history.csv",
                  "phase25a_roi030_fold2_training_history.csv",
                  "phase25a_roi030_refiner_selected_epochs.csv",
                  "phase25a_roi030_final_refit_history.csv",
                  "phase25a_roi030_checkpoint_inventory.csv",
                  "phase25a_roi030_crop_geometry_summary.csv"]
    missing_t = [t for t in req_tables if not (TAB / t).exists()]
    chk("nine_canonical_tables", not missing_t, missing_t or f"{len(req_tables)}/9")

    req_figs = ["p25a_roi030_fold0_loss_curve.png", "p25a_roi030_fold1_loss_curve.png",
                "p25a_roi030_fold2_loss_curve.png", "p25a_roi030_fold_training_comparison.png",
                "p25a_roi030_best_epoch_summary.png", "p25a_roi030_final_refit_training_curve.png",
                "p25a_roi030_action_availability_by_domain.png",
                "p25a_roi030_crop_geometry_distribution.png",
                "p25a_roi030_refiner_architecture_summary.png"]
    missing_f = [f for f in req_figs if not (FIG / f).exists()]
    chk("nine_canonical_figures", not missing_f, missing_f or f"{len(req_figs)}/9")

    # ---- architecture / resource ---------------------------------------- #
    chk("parameters_1276401", ra.get("trainable_parameters") == BARR_REFINER_EXPECTED_PARAMETERS
        == 1276401, ra.get("trainable_parameters"))
    chk("macs_present", ra.get("analytical_macs") is not None, ra.get("analytical_gmacs"))

    # ---- audits --------------------------------------------------------- #
    chk("threshold_semantics_audit_pass",
        ts.get("verdict") == "PHASE25A_THRESHOLD_SEMANTICS_AUDIT_PASS", ts.get("verdict"))
    chk("notebook_visual_integrity_pass",
        vi.get("verdict") == "PHASE25A_ROI030_NOTEBOOK_VISUAL_INTEGRITY_PASS", vi.get("verdict"))
    chk("notebook_3x_deterministic",
        det.get("byte_identical_three_builds") is True and det.get("retrained") is False,
        det.get("sha256_per_build"))

    # ---- scope / locks --------------------------------------------------- #
    # The authoritative lock evidence is the CANONICAL ROI-0.30 leakage audit.
    lk30 = jload(AUD / "phase25a_roi030_no_outcome_leakage_audit.json")
    _ho = lk30.get("router_holdout", {})
    _val = lk30.get("existing_val", {})
    _tst = lk30.get("test", {})
    chk("no_paired_gain_labels",
        scope.get("not_started", {}).get("paired_gain_labels") is True
        and scope.get("not_started", {}).get("delta_dice") is True
        and lk30.get("paired_gain_labels_created") is False
        and lk30.get("deltadice_computed") is False,
        {"not_started.paired_gain_labels": scope.get("not_started", {}).get("paired_gain_labels"),
         "not_started.delta_dice": scope.get("not_started", {}).get("delta_dice"),
         "leakage.paired_gain_labels_created": lk30.get("paired_gain_labels_created"),
         "leakage.deltadice_computed": lk30.get("deltadice_computed")})
    chk("no_benefit_router_trained",
        scope.get("not_started", {}).get("benefit_router") is True
        and lk30.get("benefit_router_training_runs") == 0
        and lk30.get("benefit_router_instantiated") is False,
        {"not_started.benefit_router": scope.get("not_started", {}).get("benefit_router"),
         "leakage.benefit_router_training_runs": lk30.get("benefit_router_training_runs"),
         "leakage.benefit_router_instantiated": lk30.get("benefit_router_instantiated")})
    chk("holdout_outcomes_read_zero",
        _ho.get("holdout_outcomes_inspected") is False
        and all(_ho.get(k, -1) == 0 for k in
                ("images_used_for_outcome_evaluation", "gt_masks_read_for_evaluation",
                 "refiner_inference", "dice", "deltadice", "holdout_sample_ids_in_cache")),
        {k: _ho.get(k) for k in
         ("holdout_outcomes_inspected", "images_used_for_outcome_evaluation",
          "gt_masks_read_for_evaluation", "refiner_inference", "dice", "deltadice",
          "holdout_sample_ids_in_cache")})
    chk("val_outcome_reads_zero",
        all(_val.get(k, -1) == 0 for k in
            ("outcome_evaluation", "refiner_inference", "val_sample_ids_in_cache"))
        and scope.get("val_808_evaluated", True) is False,
        {**{k: _val.get(k) for k in
            ("outcome_evaluation", "refiner_inference", "val_sample_ids_in_cache")},
         "scope.val_808_evaluated": scope.get("val_808_evaluated")})
    chk("test_all_zero",
        scope.get("test_reads", 1) == 0 and cm.get("test_reads") == 0
        and all(_tst.get(k, -1) == 0 for k in
                ("image_reads", "mask_reads", "inference", "visualization",
                 "test_sample_ids_in_cache")),
        {"scope.test_reads": scope.get("test_reads"),
         "cache_manifest.test_reads": cm.get("test_reads"),
         "leakage.test": _tst})

    # ---- notebook -------------------------------------------------------- #
    chk("canonical_notebook_present", NB.exists(), sha(NB) if NB.exists() else None)
    nb_txt = NB.read_text(encoding="utf-8", errors="replace") if NB.exists() else ""
    chk("notebook_states_both_roles",
        "ROI PROPOSAL THRESHOLD = **0.30**" in nb_txt
        and "SEGMENTATION OUTPUT THRESHOLD = **0.50**" in nb_txt,
        {"roi_role_str_present": "ROI PROPOSAL THRESHOLD = **0.30**" in nb_txt,
         "seg_role_str_present": "SEGMENTATION OUTPUT THRESHOLD = **0.50**" in nb_txt})
    chk("notebook_preserves_superseded_sha", SUPERSEDED_NB_SHA in nb_txt,
        {"superseded_sha_present": SUPERSEDED_NB_SHA in nb_txt})
    # A concrete, non-tautological assertion: the notebook must positively assert that
    # NO paired-gain / DeltaDice / router artefact was produced, and must contain the
    # canonical terminal lock wording.
    _no_delta_markers = ["canonical paired-gain labels NOT created",
                         "canonical DeltaDice NOT computed",
                         "canonical benefit router NOT trained"]
    chk("notebook_asserts_no_deltadice_or_router",
        all(m in nb_txt for m in _no_delta_markers),
        {m: (m in nb_txt) for m in _no_delta_markers})

    # ---- phases not started --------------------------------------------- #
    _p25b = sorted(p.name for p in (ROOT / "experiments").glob("phase25b*"))
    _p25c = sorted(p.name for p in (ROOT / "experiments").glob("phase25c*"))
    chk("phase25b_not_started", len(_p25b) == 0 and len(_p25c) == 0,
        {"phase25b_dirs": _p25b, "phase25c_dirs": _p25c,
         "scope.not_started.phase25b_started":
             scope.get("not_started", {}).get("phase25b_started"),
         "scope.not_started.phase25c_started":
             scope.get("not_started", {}).get("phase25c_started")})
    chk("phase25c_not_started",
        scope.get("not_started", {}).get("phase25c_started") is False,
        {"scope.not_started.phase25c_started":
             scope.get("not_started", {}).get("phase25c_started"),
         "phase25c_dirs": _p25c})

    chk("post_repair_check_pass",
        post.get("verdict") == "PHASE25A_POST_THRESHOLD_REPAIR_FINAL_CHECK_PASS", post.get("verdict"))

    n_fail = sum(1 for c in checks if not c["ok"])
    artifact = {
        "artifact": "phase25a_canonical_final_freeze",
        "phase": "25A",
        "classification": "CANONICAL_PHASE25A_AFTER_THRESHOLD_ADJUDICATION",
        "method": "RA-MedFiLM-BARR",
        "architecture": "ra_medfilm_barr_narrowed_v1_1",
        "roi_proposal_threshold": ROI_PROPOSAL_THRESHOLD,
        "segmentation_output_threshold": SEGMENTATION_OUTPUT_THRESHOLD,
        "roi_vs_segmentation_threshold_roles_separated": True,
        "superseded_phase25a_notebook_sha": SUPERSEDED_NB_SHA,
        "superseded_run_status": "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50",
        "superseded_run_scientific_use_allowed": False,
        "canonical_action_availability": {
            "population_n": cm.get("population_n"),
            "action_available_n": cm.get("action_available_n"),
            "action_unavailable_global_empty_n": cm.get("action_unavailable_global_empty_n"),
            "by_domain": cm.get("by_domain"),
        },
        "canonical_fold_best_epochs": fold_bests,
        "canonical_fold_checkpoint_sha256": {
            f"{d}/{f.name}": sha(f)
            for d in ("fold0", "fold1", "fold2")
            for f in sorted((CKPT / d).glob("best.pt"))
        },
        "canonical_final_refit_epoch_count": rule.get("final_refit_epochs"),
        "canonical_final_refit_epoch_rule_source": rule.get("source_best_epochs"),
        "canonical_final_checkpoint_sha256": (sha(CKPT / "final" / "final.pt")
                                              if (CKPT / "final" / "final.pt").exists() else None),
        "canonical_checkpoint_inventory": ckpt_shas,
        "actual_parameter_count": ra.get("trainable_parameters"),
        "actual_macs": ra.get("analytical_macs"),
        "actual_gmacs": ra.get("analytical_gmacs"),
        "trainer_hardening_provenance": {
            "trainer": "scripts/training/train_phase25a_refiner.py",
            "sha256": sha(ROOT / "scripts" / "training" / "train_phase25a_refiner.py"),
            "atomic_writes": True,
            "history_persisted_before_checkpoint": True,
            "rng_restore_on_resume": True,
            "change_class": "EXECUTION_MECHANISM_ONLY",
        },
        "roi050_execution_preserved": True,
        "roi050_supersession_artifact": "reports/audits/phase25a_roi050_supersession.json",
        "paired_gain_labels_generated": False,
        "benefit_router_trained": False,
        "holdout_outcomes_read": 0,
        "val_outcome_reads": 0,
        "test_reads": 0,
        "test_image_reads": 0,
        "test_mask_reads": 0,
        "test_inference": 0,
        "phase25b_started": False,
        "phase25c_started": False,
        "canonical_notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "canonical_notebook_sha256": sha(NB) if NB.exists() else None,
        "notebook_determinism": {"byte_identical_three_builds": det.get("byte_identical_three_builds"),
                                 "sha256_per_build": det.get("sha256_per_build"),
                                 "retrained": det.get("retrained")},
        "checks": checks,
        "n_checks": len(checks),
        "n_passed": len(checks) - n_fail,
        "n_failed": n_fail,
        "failed": [c["check"] for c in checks if not c["ok"]],
        "science_changed": False,
        "phase24_science_changed": False,
        "terminal": TERMINAL if n_fail == 0 else None,
        "verdict": "PHASE25A_CANONICAL_FINAL_FREEZE_PASS" if n_fail == 0
                   else "PHASE25A_CANONICAL_FINAL_FREEZE_FAIL",
    }
    (AUD / "phase25a_canonical_final_freeze.json").write_text(
        json.dumps(artifact, indent=1) + "\n", encoding="utf-8")

    # ---- additive governance pointer ------------------------------------- #
    ptr = {
        "artifact": "phase25a_canonical_governance_pointer",
        "phase": "25A",
        "canonical": {
            "classification": "CANONICAL_PHASE25A_AFTER_THRESHOLD_ADJUDICATION",
            "roi_proposal_threshold": 0.30,
            "segmentation_output_threshold": 0.50,
            "cache_root": "data_cache/phase25a_barr_roi030_cache",
            "checkpoint_root": "checkpoints/phase25a_barr_regional_refiner_v1_1_roi030",
            "experiment_root": "experiments/phase25a_barr_regional_refiner_v1_1_roi030",
            "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
            "notebook_sha256": sha(NB) if NB.exists() else None,
            "final_freeze": "reports/audits/phase25a_canonical_final_freeze.json",
        },
        "superseded": {
            "classification": "NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50",
            "roi_proposal_threshold": 0.50,
            "checkpoint_root": "checkpoints/phase25a_barr_regional_refiner_v1_1",
            "notebook_sha256": SUPERSEDED_NB_SHA,
            "scientific_use_allowed": False,
            "allowed_role": "PROVENANCE / DEBUGGING / PROTOCOL-DEVIATION RECORD ONLY",
            "preserved": True,
            "deleted_or_disguised": False,
        },
        "additive_only": True,
        "previous_pointer_retained": "reports/audits/phase25a_final_freeze.json",
        "terminal": TERMINAL if n_fail == 0 else None,
    }
    (AUD / "phase25a_canonical_governance_pointer.json").write_text(
        json.dumps(ptr, indent=1) + "\n", encoding="utf-8")

    for c in checks:
        print(f"[{'PASS' if c['ok'] else 'FAIL'}] {c['check']} :: {c['detail']}")
    print(f"\n{len(checks) - n_fail}/{len(checks)} PASS")
    print(artifact["verdict"])
    if n_fail == 0:
        print()
        print(TERMINAL)
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
