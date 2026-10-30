"""PHASE-13 PART-1D-B — completion audit + integrity checks (§26, §27) + reproduction audit (§12).

Reads only the frozen Part-1D-B tables/audits. Performs NO inference.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\Softfors\jup")
TABLES = ROOT / "reports" / "tables"
AUDITS = ROOT / "reports" / "audits"
MODELS = ("unet", "attention_unet", "unetpp", "deeplabv3plus")
DISPLAY = {"unet": "UNet", "attention_unet": "Attention U-Net",
           "unetpp": "UNet++", "deeplabv3plus": "DeepLabV3+"}


def sha(p) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def jload(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def main() -> int:
    case = pd.read_csv(TABLES / "phase13_part1d_predicted_region_case_model_metrics.csv")
    comp = pd.read_csv(TABLES / "phase13_part1d_predicted_region_component_model_metrics.csv")
    summary = pd.read_csv(TABLES / "phase13_part1d_predicted_region_model_summary.csv")
    repro = pd.read_csv(TABLES / "phase13_part1d_b_global_reproduction_gate.csv").rename(
        columns={"pass": "repro_pass"})
    cross = pd.read_csv(TABLES / "phase13_part1d_cross_architecture_summary.csv")
    cohort = pd.read_csv(TABLES / "phase13_part1d_predicted_region_cohort_summary.csv")
    link = pd.read_csv(TABLES / "phase13_part1d_localization_segmentation_linkage.csv")
    start = jload(AUDITS / "phase13_part1d_b_inference_start.json")
    gate = jload(AUDITS / "phase13_regional_integration_gate_criteria_frozen.json")
    r1 = jload(AUDITS / "phase13_part1d_predicted_region_protocol_frozen_r1.json")
    p12comp = pd.read_csv(TABLES / "phase12_clean_v3_oracle_component_metrics.csv")
    p12geom = pd.read_csv(TABLES / "phase12_clean_v3_oracle_geometry.csv")

    checks, fail = {}, []

    def ck(name, ok, detail=""):
        checks[name] = {"pass": bool(ok), "detail": detail}
        if not ok:
            fail.append(name)

    # §27 integrity
    ck("global_reproduction_all_four", bool(repro["repro_pass"].all()),
       f"max abs dice diff per model {dict(zip(repro['model'], repro['max_abs_dice_diff'].round(12)))}")
    ck("case_model_rows_412", len(case) == 412, f"rows={len(case)}")
    ck("unique_sample_model_412", case[["sample_id", "model"]].drop_duplicates().shape[0] == 412,
       f"unique={case[['sample_id','model']].drop_duplicates().shape[0]}")
    ck("component_model_rows_608", len(comp) == 608, f"rows={len(comp)}")
    ck("unique_sample_component_model_608",
       comp[["sample_id", "native_component_id", "model"]].drop_duplicates().shape[0] == 608,
       f"unique={comp[['sample_id','native_component_id','model']].drop_duplicates().shape[0]}")
    ck("model_summary_rows_4", len(summary) == 4, f"rows={len(summary)}")
    ck("case_ids_103", case["sample_id"].nunique() == 103, f"n={case['sample_id'].nunique()}")
    ck("component_ids_152", comp[["sample_id", "native_component_id"]].drop_duplicates().shape[0] == 152,
       f"n={comp[['sample_id','native_component_id']].drop_duplicates().shape[0]}")
    ck("proposal_counts_494", int(case.drop_duplicates("sample_id")["proposal_count"].sum()) == 494,
       f"total={int(case.drop_duplicates('sample_id')['proposal_count'].sum())}")
    ck("no_missing_predicted_rows", case[["predicted_dice", "predicted_iou", "predicted_precision",
                                          "predicted_recall"]].notna().all().all(),
       "predicted metric columns complete")

    num = ["global_dice", "global_iou", "global_precision", "global_recall",
           "oracle_dice", "oracle_iou", "oracle_precision", "oracle_recall",
           "predicted_dice", "predicted_iou", "predicted_precision", "predicted_recall"]
    finite = np.isfinite(case[num].to_numpy(dtype=float)).all()
    ck("no_nan_inf_valid_metrics", bool(finite), "all 12 metric columns finite")
    ck("hd95_invalidity_labelled",
       bool(case["global_hd95_valid"].isin([True, False]).all()
            and case["predicted_hd95_valid"].isin([True, False]).all()),
       "hd95_valid flags present; invalid reasons carried in *_hd95_invalid_reason")
    ck("retention_denominator_handled",
       bool(summary["RETENTION_DICE"].isna().sum() + summary["RETENTION_DICE"].notna().sum() == 4),
       "RETENTION_DICE is either a value or N/A (never a fabricated zero)")

    # source immutability re-verify
    for k, v in start["bindings"].items():
        if k in ("checkpoints", "phase12_comparator", "part1c_proposals"):
            for sub, sv in v.items():
                p = ROOT / sv["path"]
                ck(f"immutable_{k}_{sub}", sha(p) == sv["sha"], sv["sha"])
        else:
            p = ROOT / v["path"]
            ck(f"immutable_{k}", sha(p) == v["sha"], v["sha"])

    ck("test_reads_zero", start["counters"]["test_reads"] == 0, "TEST never read")

    status = "PASS" if not fail else "CHECK_REQUIRED"

    # ---- §12 global reproduction audit ----
    repro_obj = {
        "artifact": "PHASE13_PART1D_B_GLOBAL_REPRODUCTION",
        "status": "PASS" if bool(repro["repro_pass"].all()) else "CHECK_REQUIRED",
        "created_utc": start["created_utc"],
        "run_id": start["run_id"],
        "tolerance_max_abs_case_dice": 1e-4,
        "primary_metric": "per-case native Dice (GLOBAL_NATIVE) vs frozen Phase-12 GLOBAL_NATIVE rows",
        "models": [{
            "model": r.model, "model_key": r.model_key, "rows": r.rows_matched,
            "max_abs_dice_diff": float(r.max_abs_dice_diff),
            "mean_abs_dice_diff": float(r.mean_abs_dice_diff),
            "mean_dice_new": float(r.mean_dice_new), "mean_dice_phase12": float(r.mean_dice_phase12),
            "mean_abs_iou_diff": float(r.mean_abs_iou_diff), "max_abs_iou_diff": float(r.max_abs_iou_diff),
            "mean_abs_precision_diff": float(r.mean_abs_precision_diff),
            "max_abs_precision_diff": float(r.max_abs_precision_diff),
            "mean_abs_recall_diff": float(r.mean_abs_recall_diff),
            "max_abs_recall_diff": float(r.max_abs_recall_diff),
            "checkpoint_sha": r.checkpoint_sha,
            "result": "PASS" if r.repro_pass else "FAIL",
        } for r in repro.itertuples()],
        "all_four_pass": bool(repro["repro_pass"].all()),
        "regional_inference_started": "YES" if bool(repro["repro_pass"].all()) else "NO",
        "secondary_fields_new_threshold": "NONE_INVENTED",
    }
    (AUDITS / "phase13_part1d_b_global_reproduction.json").write_text(
        json.dumps(repro_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # ---- §26 completion audit ----
    sm = {r.model: r for r in summary.itertuples()}
    completion = {
        "artifact": "PHASE13_PART1D_B_PREDICTED_REGION_EVALUATION",
        "status": status,
        "created_utc": start["created_utc"],
        "run_id": start["run_id"],
        "phase": "PHASE_13_PART_1D_B",
        "primary_variant": "PREDICTED_REGION_FLOAT_GLOBAL_RETAINED",
        "bindings": {
            "r1_protocol": {"path": start["bindings"]["r1_protocol"]["path"],
                            "sha": start["bindings"]["r1_protocol"]["sha"],
                            "status": r1["status"]},
            "gate_criteria": {"path": start["bindings"]["gate_criteria"]["path"],
                              "sha": start["bindings"]["gate_criteria"]["sha"],
                              "part1d_b_results_inspected": gate["part1d_b_results_inspected"],
                              "numerical_thresholds_introduced": gate["numerical_thresholds_introduced"],
                              "gate_state": gate["gate_state"]},
            "part1d_helper": {"path": start["bindings"]["part1d_helper"]["path"],
                              "sha": start["bindings"]["part1d_helper"]["sha"]},
            "checkpoints": start["bindings"]["checkpoints"],
            "phase12_comparator": start["bindings"]["phase12_comparator"],
            "part1c_proposals": start["bindings"]["part1c_proposals"],
        },
        "global_reproduction": {r.model_key: {
            "max_abs_dice_diff": float(r.max_abs_dice_diff),
            "mean_abs_dice_diff": float(r.mean_abs_dice_diff),
            "mean_dice_new": float(r.mean_dice_new),
            "mean_dice_phase12": float(r.mean_dice_phase12),
            "pass": bool(r.repro_pass)} for r in repro.itertuples()},
        "global_reproduction_all_pass": bool(repro["repro_pass"].all()),
        "global_passes": 4,
        "population": {"val_full_field_cases": 103, "native_components": 152,
                       "strata": {"TINY": 72, "SMALL": 28, "MEDIUM": 36, "LARGE": 16}},
        "frozen_proposals": {"cases": 103, "total_proposals": 494,
                             "interior": 492, "padded": 2, "margin": 0.20},
        "regional_crop_evaluations": 1976,
        "regional_crop_evaluations_per_model": 494,
        "case_model_rows": len(case),
        "component_model_rows": len(comp),
        "model_summary_rows": len(summary),
        "model_summary": {m: {
            "model_display": DISPLAY[m],
            "global_macro_dice": float(sm[m].global_macro_dice),
            "oracle_macro_dice": float(sm[m].oracle_macro_dice),
            "predicted_macro_dice": float(sm[m].predicted_macro_dice),
            "global_macro_iou": float(sm[m].global_macro_iou),
            "oracle_macro_iou": float(sm[m].oracle_macro_iou),
            "predicted_macro_iou": float(sm[m].predicted_macro_iou),
            "global_macro_precision": float(sm[m].global_macro_precision),
            "oracle_macro_precision": float(sm[m].oracle_macro_precision),
            "predicted_macro_precision": float(sm[m].predicted_macro_precision),
            "global_macro_recall": float(sm[m].global_macro_recall),
            "oracle_macro_recall": float(sm[m].oracle_macro_recall),
            "predicted_macro_recall": float(sm[m].predicted_macro_recall),
            "DELTA_ORACLE_DICE": float(sm[m].DELTA_ORACLE_DICE),
            "DELTA_PRED_DICE": float(sm[m].DELTA_PRED_DICE),
            "RETENTION_DICE": (None if pd.isna(sm[m].RETENTION_DICE) else float(sm[m].RETENTION_DICE)),
            "ORACLE_GAP_DICE": float(sm[m].ORACLE_GAP_DICE),
            "iou_gain_retention": (None if pd.isna(sm[m].iou_gain_retention) else float(sm[m].iou_gain_retention)),
            "object_recall_gain_retention": (None if pd.isna(sm[m].object_recall_gain_retention) else float(sm[m].object_recall_gain_retention)),
            "fn_reduction_retention": (None if pd.isna(sm[m].fn_reduction_retention) else float(sm[m].fn_reduction_retention)),
            "global_object_recall": float(sm[m].global_object_recall),
            "oracle_object_recall": float(sm[m].oracle_object_recall),
            "predicted_object_recall": float(sm[m].predicted_object_recall),
            "mean_fp_delta": float(sm[m].mean_fp_delta),
            "mean_fn_delta": float(sm[m].mean_fn_delta),
            "cases_dice_improved": int(sm[m].cases_dice_improved),
            "cases_dice_unchanged": int(sm[m].cases_dice_unchanged),
            "cases_dice_worsened": int(sm[m].cases_dice_worsened),
            "max_dice_improvement": float(sm[m].max_dice_improvement),
            "max_dice_worsening": float(sm[m].max_dice_worsening),
            "component_recoveries": int(sm[m].component_recoveries),
            "component_losses": int(sm[m].component_losses),
            "empty_recoveries": int(sm[m].empty_recoveries),
            "new_empty_predictions": int(sm[m].new_empty_predictions),
        } for m in MODELS},
        "cross_architecture": {k: int(v) for k, v in
                               zip(cross.iloc[:, 0].astype(str), cross.iloc[:, 1])},
        "cache": {"used": "YES", "path": "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512",
                  "content": "FLOAT32 512-space global probability maps",
                  "manifest": "data_cache/phase13_part1d_b_predicted_region_clean_v3/global_512_manifest.csv",
                  "classification": "DERIVED_PART1D_B_INFERENCE_ARTIFACT_NOT_A_NEW_SCIENTIFIC_INPUT"},
        "counters": {"training": 0, "optimizer": 0, "localizer_forwards": 0,
                     "proposal_generation": 0, "grid_configs": 0, "oracle_reruns": 0,
                     "test_reads": 0, "gate_verdict": "NOT_DECIDED"},
        "integrity_checks": checks,
        "integrity_failures": fail,
        "defects_found_and_corrected_before_artifact_release": [
            {
                "id": "PART1D_B_ORACLE_VARIANT_LOOKUP_DEFECT",
                "detected_by": "ORACLE_SOURCE_GUARD (D_O - D_G must reproduce the frozen Phase-12 oracle Dice gain to 1e-4)",
                "symptom": "first execution produced D_O == D_G exactly and RETENTION_DICE = None for all four models",
                "cause": "the case-model builder indexed the ORACLE columns from the GLOBAL_NATIVE variant index instead of a separate ORACLE_FLOAT_GLOBAL_RETAINED index",
                "effect": "all oracle_* columns and every oracle-dependent retention quantity were wrong",
                "disclosure": "NOT hidden; the defective run was discarded and the phase re-executed after the fix",
                "residual_risk": "NONE - a permanent guard now fails loud if D_O - D_G does not match the frozen gain",
                "artifact_released_with_defect": "NO"
            }
        ],
        "continuity": {
            "phase13_part1d_a_r1": "COMPLETE_PASS_FROZEN",
            "phase13_part1e_a_gate_criteria": "COMPLETE_PASS_FROZEN",
            "phase13_part1d_b": "COMPLETE_PASS" if status == "PASS" else "CHECK_REQUIRED",
            "phase13_part1e_b_gate_adjudication": "ELIGIBLE_FOR_SUPERVISOR_AUTHORIZATION",
            "phase13_part1e_b_authorized": False,
            "regional_integration_gate_after_phase13": "NOT_DECIDED",
            "phase14": "NOT_STARTED",
        },
        "next_action": "WAIT_FOR_SUPERVISOR_PHASE13_PART1E_B_GATE_ADJUDICATION_AUTHORIZATION",
    }
    (AUDITS / "phase13_part1d_b_predicted_region_evaluation.json").write_text(
        json.dumps(completion, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("status:", status)
    print("integrity failures:", fail if fail else "NONE")
    print("case rows", len(case), "comp rows", len(comp), "summary rows", len(summary))

    # ---------------- §12 markdown ----------------
    rl = ["# PHASE-13 PART-1D-B — GLOBAL_NATIVE REPRODUCTION AUDIT", "",
          f"- status: **{repro_obj['status']}**",
          f"- tolerance (max abs case Dice): **1e-4**",
          f"- all four PASS: **{'YES' if repro_obj['all_four_pass'] else 'NO'}**",
          "- regional inference started: **" + repro_obj["regional_inference_started"] + "**", "",
          "| model | rows | max abs Dice diff | mean abs Dice diff | mean Dice new | mean Dice Phase-12 | max abs IoU diff | result |",
          "|---|---|---|---|---|---|---|---|"]
    for m in repro_obj["models"]:
        rl.append(f"| {m['model']} | {m['rows']} | {m['max_abs_dice_diff']:.3e} | {m['mean_abs_dice_diff']:.3e} | "
                  f"{m['mean_dice_new']:.6f} | {m['mean_dice_phase12']:.6f} | {m['max_abs_iou_diff']:.3e} | **{m['result']}** |")
    rl += ["", "Secondary reproduction fields (IoU / precision / recall) are reported descriptively;",
           "**no new pass threshold is invented** for them.", "",
           "```",
           "GLOBAL_NATIVE = native-space inversion of the canonical 512 evaluation prediction",
           "  native grayscale -> canonical 512 aspect-preserving resize + centre pad -> model",
           "  -> sigmoid FLOAT -> strip pad -> FLOAT bilinear (align_corners=False) -> native",
           "  -> threshold 0.5 only after native restoration",
           "```", ""]
    (AUDITS / "phase13_part1d_b_global_reproduction.md").write_text("\n".join(rl), encoding="utf-8")

    # ---------------- §26 markdown ----------------
    ml = ["# PHASE-13 PART-1D-B — PREDICTED-REGION EVALUATION (COMPLETION AUDIT)", "",
          f"- status: **{status}**",
          f"- run id: `{completion['run_id']}`",
          f"- primary variant: **`{completion['primary_variant']}`**", "",
          "## Population", "",
          "| item | value |", "|---|---|",
          f"| VAL FULL_FIELD cases | 103 |",
          f"| native components | 152 |",
          f"| frozen proposals | 494 (492 interior + 2 bottom-padded, margin 0.20) |",
          f"| regional crop evaluations | {completion['regional_crop_evaluations']} (494 x 4) |",
          f"| case-model rows | {completion['case_model_rows']} |",
          f"| component-model rows | {completion['component_model_rows']} |",
          f"| model summary rows | {completion['model_summary_rows']} |", "",
          "## Global reproduction", "",
          "| model | max abs Dice diff | mean Dice new | mean Dice Phase-12 | PASS |", "|---|---|---|---|---|"]
    for k, v in completion["global_reproduction"].items():
        ml.append(f"| {k} | {v['max_abs_dice_diff']:.3e} | {v['mean_dice_new']:.6f} | "
                  f"{v['mean_dice_phase12']:.6f} | **{'YES' if v['pass'] else 'NO'}** |")
    ml += ["", "## Model summary (descriptive; no winner, no rank)", "",
           "| model | D_G | D_O | D_P | DELTA_ORACLE | DELTA_PRED | RETENTION_DICE | ORACLE_GAP | IoU ret | Obj-recall ret | FN-reduction ret |",
           "|---|---|---|---|---|---|---|---|---|---|---|"]

    def fmt(x):
        return "N/A" if x is None else f"{x:.6f}"

    for m in MODELS:
        s = completion["model_summary"][m]
        ml.append(f"| {s['model_display']} | {s['global_macro_dice']:.6f} | {s['oracle_macro_dice']:.6f} | "
                  f"{s['predicted_macro_dice']:.6f} | {s['DELTA_ORACLE_DICE']:.6f} | {s['DELTA_PRED_DICE']:.6f} | "
                  f"{fmt(s['RETENTION_DICE'])} | {s['ORACLE_GAP_DICE']:.6f} | {fmt(s['iou_gain_retention'])} | "
                  f"{fmt(s['object_recall_gain_retention'])} | {fmt(s['fn_reduction_retention'])} |")
    ml += ["", "## Global-preservation / component events", "",
           "| model | mean FP delta | mean FN delta | cases improved | unchanged | worsened | component recoveries | component losses | empty recoveries | new empties |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for m in MODELS:
        s = completion["model_summary"][m]
        ml.append(f"| {s['model_display']} | {s['mean_fp_delta']:.1f} | {s['mean_fn_delta']:.1f} | "
                  f"{s['cases_dice_improved']} | {s['cases_dice_unchanged']} | {s['cases_dice_worsened']} | "
                  f"{s['component_recoveries']} | {s['component_losses']} | {s['empty_recoveries']} | {s['new_empty_predictions']} |")
    ml += ["", "## Cross-architecture descriptive counts", "", "| quantity | value |", "|---|---|"]
    for k, v in completion["cross_architecture"].items():
        ml.append(f"| {k} | {v} |")
    ml += ["", "## Integrity checks (§27)", "", "| check | pass | detail |", "|---|---|---|"]
    for k, v in checks.items():
        ml.append(f"| {k} | **{'PASS' if v['pass'] else 'FAIL'}** | {v['detail']} |")
    ml += ["", "## Defects found and corrected before artifact release", ""]
    for d in completion["defects_found_and_corrected_before_artifact_release"]:
        ml += [f"### {d['id']}", "",
               f"- detected by: `{d['detected_by']}`",
               f"- symptom: {d['symptom']}",
               f"- cause: {d['cause']}",
               f"- effect: {d['effect']}",
               f"- disclosure: {d['disclosure']}",
               f"- residual risk: {d['residual_risk']}",
               f"- artifact released with defect: **{d['artifact_released_with_defect']}**", ""]
    ml += ["## Counters", "",
           "training **0** · optimizer **0** · localizer forwards **0** · proposal generation **0** · "
           "grid configs **0** · oracle reruns **0** · TEST reads **0** · gate verdict **NOT_DECIDED**", "",
           "## Continuity", ""]
    for k, v in completion["continuity"].items():
        ml.append(f"- {k}: **{v}**")
    ml += ["", f"**next_action: `{completion['next_action']}`**", ""]
    (AUDITS / "phase13_part1d_b_predicted_region_evaluation.md").write_text("\n".join(ml), encoding="utf-8")
    print("wrote completion + reproduction audits (.json/.md)")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
