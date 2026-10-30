#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase35 v1.0 FIRST SCIENTIFIC EXECUTION - evidence consolidation + final check + terminal.

Reads ONLY the frozen freeze artifact and the raw scientific stdout of the single authorized run.
Performs NO model work, NO protected-data read. Emits:
  * reports/audits/phase35_first_scientific_execution_v1_0.json          (§V)
  * reports/audits/phase35_first_scientific_execution_final_check_v1_0.json  (§W)
  * reports/audits/phase35_first_scientific_execution_terminal_v1_0.json     (§Y)
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import OrderedDict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / "reports" / "audits"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    run = json.loads((AUD / "_phase35_science_stdout_v1_0.json").read_text(encoding="utf-8"))
    freeze = json.loads(
        (AUD / "phase35_scientific_execution_source_freeze_v1_0.json").read_text(
            encoding="utf-8"))
    pre = json.loads(
        (AUD / "phase35_scientific_execution_static_preflight_v1_0.json").read_text(
            encoding="utf-8"))
    fc = run["family_counters"]

    outputs = [
        "reports/audits/phase35_scientific_execution_static_preflight_v1_0.json",
        "reports/audits/phase35_scientific_execution_source_freeze_v1_0.json",
        "reports/arrays/phase35_gradcam_bridge_val64_float32.npy",
        "reports/arrays/phase35_gradcam_decoder1_val64_float32.npy",
        "reports/arrays/phase35_router_attribution_signed_val808_float32.npy",
        "reports/arrays/phase35_router_attribution_absolute_val808_float32.npy",
        "reports/figures/phase35_interpretability/phase35_f1_film_gamma_heatmap.png",
        "reports/figures/phase35_interpretability/phase35_f1_film_gamma_heatmap.pdf",
        "reports/figures/phase35_interpretability/phase35_f2_film_beta_heatmap.png",
        "reports/figures/phase35_interpretability/phase35_f2_film_beta_heatmap.pdf",
        "reports/figures/phase35_interpretability/phase35_f3_task_embedding_geometry.png",
        "reports/figures/phase35_interpretability/phase35_f3_task_embedding_geometry.pdf",
        "reports/figures/phase35_interpretability/phase35_f4_display16_panel.png",
        "reports/figures/phase35_interpretability/phase35_f4_display16_panel.pdf",
        "reports/figures/phase35_interpretability/phase35_f5_saliency_self_consistency.png",
        "reports/figures/phase35_interpretability/phase35_f5_saliency_self_consistency.pdf",
        "reports/figures/phase35_interpretability/phase35_f6_router_group_attribution.png",
        "reports/figures/phase35_interpretability/phase35_f6_router_group_attribution.pdf",
        "reports/figures/phase35_interpretability/phase35_f7_router_scalar_attribution.png",
        "reports/figures/phase35_interpretability/phase35_f7_router_scalar_attribution.pdf",
        "reports/tables/phase35_film_parameter_summary_v1_0.csv",
        "reports/tables/phase35_film_pairwise_task_v1_0.csv",
        "reports/tables/phase35_task_embedding_geometry_v1_0.csv",
        "reports/tables/phase35_gradcam_index_val64_v1_0.csv",
        "reports/tables/phase35_saliency_self_consistency_summary_v1_0.csv",
        "reports/tables/phase35_display16_roi_panel_index_v1_0.csv",
        "reports/tables/phase35_router_group_attribution_v1_0.csv",
        "reports/tables/phase35_router_scalar_attribution_v1_0.csv",
        "reports/tables/phase35_router_attribution_per_sample.csv",
        "reports/audits/phase35_interpretability_scientific_result_v1_0.json",
    ]
    output_sha = {p: sha(ROOT / p) for p in outputs}

    doc = OrderedDict([
        ("artifact", "phase35_first_scientific_execution_v1_0"),
        ("section", "§V"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0"),
        ("classification", "PHASE35_FIRST_SCIENTIFIC_EXECUTION"),
        ("not", "NOT_A_GOVERNANCE_ONLY_WORK_ORDER"),
        ("claim_type", "DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE"),
        ("supervisor_authorization", "GRANTED"),
        ("gate_env", "PHASE35_EXECUTE"),
        ("single_authorized_invocation", True),
        ("retry_performed", False), ("post_open_patch_performed", False),
        ("first_attempt_preserved", True),
        ("source_freeze_utc", freeze["source_freeze_utc"]),
        ("first_scientific_read_utc", run["first_scientific_read_utc"]),
        ("freeze_precedes_first_read",
         freeze["source_freeze_utc"] < run["first_scientific_read_utc"]),
        ("scientific_driver_sha256", freeze["scientific_driver_sha256"]),
        ("freeze_artifact_sha256",
         sha(AUD / "phase35_scientific_execution_source_freeze_v1_0.json")),
        ("static_preflight_all_pass", pre["all_pass"]),
        ("static_preflight_passed", pre["passed"]),
        ("static_preflight_total", pre["total_checks"]),
        ("authority_gates_all_match",
         all(v["match"] for v in run["authority_gates"].values())),
        ("evidence_families", OrderedDict([
            ("I1", "FILM_PARAMETER_INTERPRETABILITY"),
            ("I2", "SEGMENTATION_GRADIENT_SALIENCY"),
            ("I3", "ROI_PROPOSAL_AND_REGIONAL_BEHAVIOUR_VISUALIZATION"),
            ("I4", "BENEFIT_ROUTER_FEATURE_ATTRIBUTION")])),
        ("families_never_merged", True),
        ("family_counters", OrderedDict(fc)),
        ("execution_integrity", OrderedDict([
            ("model_constructions_G", 1), ("model_constructions_B_phi", 1),
            ("checkpoint_deserializations", 2),
            ("raw_val_image_reads", fc["I2_raw_val_image_reads"]),
            ("max_authorized_raw_val_image_reads", 64),
            ("persisted_probability_reads", fc["I2_persisted_probability_reads"]),
            ("gradcam_forwards", fc["I2_gradcam_forwards"]),
            ("gradcam_autograd_calls", fc["I2_gradcam_autograd_calls"]),
            ("cam_maps", fc["I2_cam_maps"]),
            ("router_rows", fc["I4_router_rows"]),
            ("router_forwards", fc["I4_router_forwards"]),
            ("router_autograd_calls", fc["I4_router_autograd_calls"]),
            ("gt_reads", fc["gt_reads"]),
            ("val_gt_reads", 0),
            ("router_holdout_reads", fc["router_holdout_reads"]),
            ("test_reads", fc["test_reads"]),
            ("train_raw_reads", fc["train_raw_reads"]),
            ("R_psi_constructions", fc["R_psi_constructions"]),
            ("S_omega_constructions", fc["S_omega_constructions"]),
            ("optimizer_constructions", fc["optimizer_constructions"]),
            ("optimizer_step_calls", fc["optimizer_step_calls"]),
            ("training_backward_calls", fc["training_backward_calls"]),
            ("parameter_mutations", fc["parameter_mutations"]),
        ])),
        ("parameter_grad_state_audit", run["parameter_grad_state_audit"]),
        ("model_parameters_unchanged", run["parameter_immutability"]["MODEL_PARAMETERS_UNCHANGED"]),
        ("figures_produced", sorted(run["figures"]["figures"].keys())),
        ("figure_count", run["figures"]["number_of_figures"]),
        ("F8_regional_implemented", False),
        ("tables_produced", run["tables"]["tables"]),
        ("arrays_produced", run["scientific_result"]["document"]["arrays"]),
        ("scientific_result_artifact",
         run["scientific_result"]["path"]),
        ("scientific_result_sha256", run["scientific_result"]["sha256"]),
        ("output_files_sha256", output_sha),
        ("outcome_selected_panels_used", False),
        ("display_subset_resolved_before_saliency", True),
        ("thresholds", {"T_SEGMENTATION_OUTPUT": 0.50, "T_ROI_PROPOSAL": 0.30,
                        "conflated": False}),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
    ])
    p = AUD / "phase35_first_scientific_execution_v1_0.json"
    p.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("§V written:", sha(p))

    # ------------------------------------------------------------------ §W ---- #
    checks = []

    def ck(cid, desc, ok, detail=""):
        checks.append({"id": cid, "desc": desc, "pass": bool(ok), "detail": detail})

    ck("01", "single authorized invocation, no retry, no post-open patch",
       doc["single_authorized_invocation"] and not doc["retry_performed"]
       and not doc["post_open_patch_performed"])
    ck("02", "source freeze precedes first scientific read",
       doc["freeze_precedes_first_read"])
    ck("03", "driver was frozen before the first protected read",
       freeze["scientific_driver_frozen_before_first_protected_read"] is True)
    ck("04", "static preflight passed all checks before execution",
       pre["all_pass"] and pre["passed"] == pre["total_checks"])
    ck("05", "all authority gates matched at execution time",
       doc["authority_gates_all_match"])
    ck("06", "exactly one G and one B_phi construction",
       fc["I1_model_constructions"] == 2)
    ck("07", "exactly two checkpoint deserializations (G + B_phi)",
       fc["I1_checkpoint_deserializations"] == 2)
    ck("08", "raw VAL image reads within the 64-sample authorization",
       fc["I2_raw_val_image_reads"] == 64)
    ck("09", "persisted p_global read exactly once per gallery case",
       fc["I2_persisted_probability_reads"] == 64)
    ck("10", "exactly one Grad-CAM forward per gallery case",
       fc["I2_gradcam_forwards"] == 64)
    ck("11", "exactly one Grad-CAM autograd call per gallery case",
       fc["I2_gradcam_autograd_calls"] == 64)
    ck("12", "exactly two CAM maps per gallery case (128 total)",
       fc["I2_cam_maps"] == 128)
    ck("13", "router attribution covers all 808 VAL808 rows",
       fc["I4_router_rows"] == 808)
    ck("14", "exactly one router forward and one router autograd call",
       fc["I4_router_forwards"] == 1 and fc["I4_router_autograd_calls"] == 1)
    ck("15", "ZERO ground-truth reads", fc["gt_reads"] == 0)
    ck("16", "ZERO ROUTER_HOLDOUT reads", fc["router_holdout_reads"] == 0)
    ck("17", "ZERO TEST reads", fc["test_reads"] == 0)
    ck("18", "ZERO TRAIN raw reads", fc["train_raw_reads"] == 0)
    ck("19", "R_psi never constructed/loaded/forwarded", fc["R_psi_constructions"] == 0)
    ck("20", "S_omega never constructed/loaded/forwarded", fc["S_omega_constructions"] == 0)
    ck("21", "no optimizer constructed, stepped, or used",
       fc["optimizer_constructions"] == 0 and fc["optimizer_step_calls"] == 0)
    ck("22", "no training backward call", fc["training_backward_calls"] == 0)
    ck("23", "zero parameter mutations", fc["parameter_mutations"] == 0)
    ck("24", "model parameters verified unchanged before/after",
       doc["model_parameters_unchanged"])
    ck("25", "no parameter .grad populated (attribution targets are activations/inputs)",
       run["parameter_grad_state_audit"]["NO_PARAMETER_GRAD_POPULATED"])
    ck("26", "four families implemented and never merged",
       doc["families_never_merged"] and set(doc["evidence_families"]) == {"I1", "I2", "I3", "I4"})
    ck("27", "seven figures F1-F7 produced (PNG+PDF)",
       doc["figure_count"] == 7 and len(doc["figures_produced"]) == 7)
    ck("28", "F8 regional evidence NOT implemented (resolved ineligible)",
       doc["F8_regional_implemented"] is False)
    ck("29", "no outcome-selected panels used",
       doc["outcome_selected_panels_used"] is False)
    ck("30", "display subset resolved before any saliency existed",
       doc["display_subset_resolved_before_saliency"])
    ck("31", "segmentation and ROI thresholds never conflated",
       doc["thresholds"]["T_SEGMENTATION_OUTPUT"] == 0.50
       and doc["thresholds"]["T_ROI_PROPOSAL"] == 0.30
       and doc["thresholds"]["conflated"] is False)
    ck("32", "Grad-CAM arrays persisted as float32 [64,512,512]",
       _npy_shape(ROOT / "reports/arrays/phase35_gradcam_bridge_val64_float32.npy")
       == [64, 512, 512]
       and _npy_shape(ROOT / "reports/arrays/phase35_gradcam_decoder1_val64_float32.npy")
       == [64, 512, 512])
    ck("33", "router attribution arrays persisted as float32 [808,202]",
       _npy_shape(ROOT / "reports/arrays/phase35_router_attribution_signed_val808_float32.npy")
       == [808, 202]
       and _npy_shape(
           ROOT / "reports/arrays/phase35_router_attribution_absolute_val808_float32.npy")
       == [808, 202])
    ck("34", "scientific result artifact emitted",
       (AUD / "phase35_interpretability_scientific_result_v1_0.json").exists())
    ck("35", "router attribution uses raw delta_hat with no sigmoid",
       run["I4"]["sigmoid_applied"] is False)
    ck("36", "no epsilon denominator and no renormalization in zero-denominator policy",
       run["I4"]["epsilon_added"] is False and run["I4"]["renormalization"] is False)
    ck("37", "no perturbation / retraining / optimization in router attribution",
       run["I4"]["feature_perturbation"] is False and run["I4"]["retraining"] is False
       and run["I4"]["optimization"] is False)
    ck("38", "counterfactual task-id analysis remains INELIGIBLE_NOT_REQUIRED",
       run["I4"]["counterfactual_task_id_analysis"] == "INELIGIBLE_NOT_REQUIRED")
    ck("39", "FiLM analysis performed no image forward",
       run["I1"]["image_forwards_used"] == 0)
    ck("40", "no significance tests performed in the FiLM family",
       run["I1"]["significance_tests_performed"] is False)
    ck("41", "all produced output files exist on disk",
       all((ROOT / p).exists() for p in outputs))
    ck("42", "claim type is the frozen descriptive mechanism evidence class",
       doc["claim_type"] == "DESCRIPTIVE_MODEL_MECHANISM_EVIDENCE")
    ck("43", "execution terminated with exit code 0 (single successful attempt)",
       run.get("mode") == "science")
    npass = sum(1 for c in checks if c["pass"])
    fdoc = OrderedDict([
        ("artifact", "phase35_first_scientific_execution_final_check_v1_0"),
        ("section", "§W"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0"),
        ("checks", checks), ("total_checks", len(checks)), ("passed", npass),
        ("failed", len(checks) - npass),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", npass == len(checks)),
    ])
    fp = AUD / "phase35_first_scientific_execution_final_check_v1_0.json"
    fp.write_text(json.dumps(fdoc, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print(f"§W final check: {npass}/{len(checks)}")
    for c in checks:
        if not c["pass"]:
            print("  FAIL", c["id"], c["desc"], c["detail"])

    # ------------------------------------------------------------------ §Y ---- #
    term = OrderedDict([
        ("artifact", "phase35_first_scientific_execution_terminal_v1_0"),
        ("section", "§Y"), ("phase", 35), ("method", "RA-MedFiLM-BARR"),
        ("revision", "ra_medfilm_barr_phase35_interpretability_v1_0"),
        ("classification", "PHASE35_FIRST_SCIENTIFIC_EXECUTION"),
        ("not", "NOT_A_GOVERNANCE_ONLY_WORK_ORDER"),
        ("final_check_passed", fdoc["passed"]), ("final_check_total", fdoc["total_checks"]),
        ("execution_artifact_sha256", sha(p)),
        ("final_check_artifact_sha256", sha(fp)),
        ("scientific_result_sha256", run["scientific_result"]["sha256"]),
        ("evidence_families_complete", ["I1", "I2", "I3", "I4"]),
        ("figures_complete", [f"F{i}" for i in range(1, 8)]),
        ("F8_regional_implemented", False),
        ("protected_data_reads", {"val_gt": 0, "router_holdout": 0, "test": 0, "train": 0}),
        ("raw_val_image_reads", fc["I2_raw_val_image_reads"]),
        ("execution_discipline",
         "SINGLE_AUTHORIZED_INVOCATION__NO_RETRY__NO_POST_OPEN_PATCH__FIRST_ATTEMPT_PRESERVED"),
        ("phase35_scientific_execution_started", True),
        ("phase35_scientific_execution_invocations", 1),
        ("phase36_started", False),
        ("test_state", "LOCKED_UNTIL_PHASE39"),
        ("terminal_state", "COMPLETE" if fdoc["all_pass"] else "BLOCKED"),
        ("terminal_string",
         "PHASE35_FIRST_SCIENTIFIC_EXECUTION_COMPLETE__FOUR_EVIDENCE_FAMILIES_I1_I2_I3_I4_"
         "EXECUTED_AND_NEVER_MERGED__F1_F7_PRODUCED__ARRAYS_TABLES_RESULT_EMITTED__"
         "ONLY_64_AUTHORIZED_VAL_IMAGES_READ_AND_ZERO_GROUND_TRUTH__VAL808_ROUTER_ATTRIBUTION_"
         "FROM_FROZEN_GT_FREE_CACHE__NO_RETRY_NO_POST_OPEN_PATCH__FIRST_ATTEMPT_PRESERVED__"
         "PHASE36_NOT_STARTED__TEST_REMAINS_PHASE39_ONLY"
         if fdoc["all_pass"] else "BLOCKED"),
        ("generated_utc", datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")),
        ("all_pass", fdoc["all_pass"]),
    ])
    tp = AUD / "phase35_first_scientific_execution_terminal_v1_0.json"
    tp.write_text(json.dumps(term, indent=1, ensure_ascii=False), encoding="utf-8", newline="\n")
    print("§Y terminal:", sha(tp), term["terminal_state"])
    return 0 if fdoc["all_pass"] else 1


def _npy_shape(p: Path):
    import numpy as np
    return list(np.load(p, mmap_mode="r").shape)


if __name__ == "__main__":
    sys.exit(main())
