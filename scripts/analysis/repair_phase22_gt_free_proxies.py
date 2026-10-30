"""Post-Phase22 repair — Part B: GT-free benefit-proxy semantic repair.

PROBLEM (verified in the frozen package)
---------------------------------------
``reports/audits/phase22_uncertainty_vs_benefit.json`` ranked GT-derived
quantities alongside genuinely deployable, GT-free ones, and the rendered report
then stated: **"Best deployable uncertainty signal (ranked by |Spearman|):
recall"**. ``recall`` requires the ground truth, so calling it deployable is
semantically invalid: a deployment cannot compute it.

WHAT THIS SCRIPT DOES (no training, no inference, no TEST)
---------------------------------------------------------
B1  Classify EVERY candidate signal with:
        signal, uses_GT, available_before_refinement, available_at_inference,
        deployable_candidate, reason
    and FAIL CLOSED if any ``uses_GT=true`` signal is marked deployable.

B2  Recompute the DEPLOYABLE-proxy ranking using ONLY strictly GT-free,
    pre-refinement signals drawn from already-persisted Phase-22 tables. The
    TARGET may use ground truth (this is development analysis); the INPUT /
    routing signal must not.

B3  Emit TWO SEPARATE tables:
        reports/tables/phase22_gt_free_proxy_vs_benefit.csv
        reports/tables/phase22_gt_aware_posthoc_associations.csv

B4  Re-verify that every routing policy labelled deployable / predicted /
    GT-free / inference-time uses only ``uses_GT=false`` signals. The frozen
    routing-regret table is audited, not overwritten.

B6  Write ``reports/audits/phase22_postfreeze_semantic_repair.json``.

Everything is derived from persisted artifacts. NO npz probability map is
re-read here (the four boundary/entropy proxies are already persisted as columns
in ``phase22_uncertainty_vs_benefit.csv``).

Usage
-----
    ./.venv/Scripts/python.exe scripts/analysis/repair_phase22_gt_free_proxies.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

T_UNC = ROOT / "reports/tables/phase22_uncertainty_vs_benefit.csv"
T_ROI = ROOT / "reports/tables/phase22_prediction_derived_roi.csv"
T_PERIMG = ROOT / "reports/tables/phase22_regional_intervention_per_image.csv"
T_REGRET = ROOT / "reports/tables/phase22_routing_regret.csv"

OUT_CLASS = ROOT / "reports/audits/phase22_benefit_proxy_feature_classification.json"
OUT_GTFREE = ROOT / "reports/tables/phase22_gt_free_proxy_vs_benefit.csv"
OUT_GTAWARE = ROOT / "reports/tables/phase22_gt_aware_posthoc_associations.csv"
OUT_REPAIR = ROOT / "reports/audits/phase22_postfreeze_semantic_repair.json"


def _sha_file(p: Path) -> str | None:
    import hashlib
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


# --------------------------------------------------------------------------- #
# B1 — classification of every candidate signal
# --------------------------------------------------------------------------- #
# reason strings are the reviewer-facing justification.
CLASSIFICATION = [
    # ---- GT-FREE, available BEFORE refinement (deployable candidates) ---- #
    dict(signal="entropy_proxy_mean", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="binary entropy of the model's own global probability map; needs only the prediction"),
    dict(signal="frac_prob_within_0p05_of_boundary", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="fraction of predicted pixels within 0.05 of p=0.5; prediction-only boundary-band uncertainty"),
    dict(signal="frac_prob_within_0p02_of_boundary", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="fraction of predicted pixels within 0.02 of p=0.5; prediction-only boundary-band uncertainty"),
    dict(signal="mean_boundary_margin", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="mean |p-0.5| over predicted pixels; prediction-only confidence margin"),
    dict(signal="pred_foreground_pixels", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="number of foreground pixels in the model's own prediction; GT-free size proxy"),
    dict(signal="pred_foreground_fraction", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="predicted foreground pixels / image pixels; GT-free normalised size proxy"),
    dict(signal="predicted_roi_area_fraction", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="area fraction of the ROI derived from the model's own PREDICTION "
                "(predicted_roi_side/native canvas); no ground truth is consulted"),
    dict(signal="pred_roi_exists", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="whether the model's own prediction yields a non-empty ROI; GT-free"),
    dict(signal="pred_empty", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="whether the model predicted an empty mask; GT-free"),
    dict(signal="task_id", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="dataset/task identifier from the frozen Phase-19 metadata contract; known before inference"),
    dict(signal="predicted_roi_side", uses_GT=False,
         available_before_refinement=True, available_at_inference=True,
         deployable_candidate=True,
         reason="side length of the ROI derived from the model's own prediction; GT-free geometry"),

    # ---- GT-DERIVED (must NEVER be called deployable) ---- #
    dict(signal="predicted_delta_dice", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="MEASURED: predicted_delta_dice == predicted_dice - global_dice (max residual "
                "3.1e-16) and BOTH operands are Dice against the GROUND-TRUTH mask. The "
                "quantity is therefore GT-DERIVED even though its name says 'predicted'; "
                "INVALID as a deployable routing signal"),
    dict(signal="predicted_dice", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="Dice of the predicted-ROI arm against ground truth; GT-derived"),
    dict(signal="baseline_global_dice_predicted", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="dice of the global prediction against ground truth; GT-derived. NOTE: a "
                "pseudo-Dice between two PREDICTIONS would be GT-free, but no such quantity "
                "is persisted here, so this name must not be used."),
    dict(signal="recall", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="sensitivity requires the ground-truth mask; INVALID as a deployable routing signal"),
    dict(signal="precision", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="precision requires the ground-truth mask; not computable at deployment"),
    dict(signal="dice", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="Dice is an overlap with ground truth; not computable at deployment"),
    dict(signal="iou", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="IoU is an overlap with ground truth; not computable at deployment"),
    dict(signal="specificity", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="specificity requires the ground-truth negatives; not computable at deployment"),
    dict(signal="balanced_accuracy", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="balanced accuracy requires ground-truth labels"),
    dict(signal="mcc", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="Matthews correlation requires all four confusion-matrix cells, hence ground truth"),
    dict(signal="ece", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="expected calibration error is measured against ground-truth correctness; GT-derived"),
    dict(signal="brier", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="Brier score is measured against ground-truth labels; GT-derived"),
    dict(signal="mce", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="maximum calibration error is measured against ground-truth correctness; GT-derived"),
    dict(signal="oracle_roi_area_fraction", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="area of the GROUND-TRUTH-derived ROI; oracle quantity, not deployable"),
    dict(signal="gt_foreground_pixels", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="ground-truth foreground size; oracle quantity"),
    dict(signal="oracle_delta_dice", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="the true oracle regional gain; this is the TARGET, never an input"),
    dict(signal="gt_size_label", uses_GT=True, available_before_refinement=False,
         available_at_inference=False, deployable_candidate=False,
         reason="any GT-derived size stratum label (e.g. KUB TINY) requires ground-truth geometry"),
]


# strictly GT-free, pre-refinement inputs used for the deployable ranking.
# NOTE: `predicted_delta_dice` is deliberately ABSENT — it is a difference of two
# ground-truth Dice scores and is therefore GT-derived (verified empirically).
GT_FREE_SIGNALS = [
    "entropy_proxy_mean",
    "frac_prob_within_0p05_of_boundary",
    "frac_prob_within_0p02_of_boundary",
    "mean_boundary_margin",
    "pred_foreground_fraction",
    "predicted_roi_area_fraction",
    "predicted_roi_side",
    "task_id",
]

# GT-aware post-hoc associations (diagnostic only)
GT_AWARE_SIGNALS = [
    "dice", "iou", "precision", "recall", "specificity", "balanced_accuracy",
    "mcc", "ece", "brier", "mce", "gt_foreground_pixels",
    "oracle_roi_area_fraction", "oracle_delta_dice", "predicted_delta_dice",
]

TARGET = "oracle_delta_dice"


def _corr(x: pd.Series, y: pd.Series) -> dict:
    ok = x.notna() & y.notna()
    x, y = x[ok].astype(float), y[ok].astype(float)
    if len(x) < 3 or x.std() == 0 or y.std() == 0:
        return {"n": int(len(x)), "pearson_r": None, "spearman_r": None}
    return {
        "n": int(len(x)),
        "pearson_r": float(np.corrcoef(x, y)[0, 1]),
        "spearman_r": float(x.corr(y, method="spearman")),
    }


def _auc(x: pd.Series, y_bin: pd.Series) -> dict:
    """ROC-AUC and PR-AUC of a GT-free score against a binary GT-derived target."""
    from sklearn.metrics import roc_auc_score, average_precision_score
    ok = x.notna() & y_bin.notna()
    x, yb = x[ok].astype(float).to_numpy(), y_bin[ok].astype(int).to_numpy()
    if len(np.unique(yb)) < 2:
        return {"n": int(len(x)), "roc_auc": None, "pr_auc": None,
                "positive_rate": float(yb.mean()) if len(yb) else None}
    return {
        "n": int(len(x)),
        "roc_auc": float(roc_auc_score(yb, x)),
        "pr_auc": float(average_precision_score(yb, x)),
        "positive_rate": float(yb.mean()),
    }


def main() -> int:
    unc = pd.read_csv(T_UNC)
    roi = pd.read_csv(T_ROI)

    # ---- derived GT-free feature: predicted foreground fraction -------------- #
    # `pred_foreground_pixels` is already persisted; the fraction needs an
    # image-pixel denominator. The Phase-19 canvas is 512x512 for the RGB path,
    # but per-sample native area is not persisted here, so the fraction is taken
    # against the canonical 512x512 inference canvas, which is a CONSTANT and
    # therefore a monotone transform of the pixel count. Both are reported.
    unc["pred_foreground_fraction"] = unc["pred_foreground_pixels"] / (512.0 * 512.0)

    # merge the persisted predicted-ROI geometry (prediction-only quantities)
    if "predicted_roi_area_fraction" not in unc.columns:
        unc = unc.merge(
            roi[["sample_id", "predicted_roi_area_fraction", "pred_roi_exists"]],
            on="sample_id", how="left")
    if "predicted_roi_side" not in unc.columns:
        perimg = pd.read_csv(T_PERIMG, usecols=["sample_id", "predicted_roi_side"])
        unc = unc.merge(perimg, on="sample_id", how="left")

    # ---- B1: classification + fail-closed check ----------------------------- #
    by_name = {c["signal"]: c for c in CLASSIFICATION}
    violations = [c["signal"] for c in CLASSIFICATION
                  if c["uses_GT"] and c["deployable_candidate"]]
    missing_live = [s for s in GT_FREE_SIGNALS if s not in unc.columns]
    # any live column not classified?
    live_signal_like = [c for c in unc.columns if c in by_name]
    unclassified = [c for c in GT_FREE_SIGNALS + GT_AWARE_SIGNALS if c not in by_name]

    # Empirical proof that `predicted_delta_dice` is GT-derived: it is exactly the
    # difference of two ground-truth Dice scores.
    perimg = pd.read_csv(T_PERIMG)
    dd_residual = float(
        (perimg["predicted_delta_dice"]
         - (perimg["predicted_dice"] - perimg["global_dice"])).abs().max())
    predicted_delta_groundtruth_evidence = {
        "identity_checked": "predicted_delta_dice == predicted_dice - global_dice",
        "max_abs_residual": dd_residual,
        "predicted_dice_is_a_dice_against_ground_truth": True,
        "global_dice_is_a_dice_against_ground_truth": True,
        "predicted_dice_range": [float(perimg["predicted_dice"].min()),
                                 float(perimg["predicted_dice"].max())],
        "conclusion": ("predicted_delta_dice is GT-DERIVED and must NOT be used as a "
                       "deployable signal, despite the name."),
    }

    class_payload = {
        "artifact": "phase22_benefit_proxy_feature_classification",
        "phase": 22,
        "classification": "GT_FREE_VS_GT_AWARE_SIGNAL_SEPARATION",
        "problem": ("the frozen Phase-22 uncertainty-benefit analysis ranked "
                    "GT-derived quantities alongside deployable ones and reported "
                    "`recall` as the best DEPLOYABLE signal, which is invalid: "
                    "recall cannot be computed without ground truth."),
        "deployable_definition": ("a signal is deployable only if uses_GT=false and "
                                  "available_before_refinement=true and "
                                  "available_at_inference=true"),
        "signals": CLASSIFICATION,
        "n_signals_classified": len(CLASSIFICATION),
        "deployable_candidates": sorted(c["signal"] for c in CLASSIFICATION
                                        if c["deployable_candidate"]),
        "gt_derived_signals": sorted(c["signal"] for c in CLASSIFICATION if c["uses_GT"]),
        "fail_closed_violations": violations,
        "fail_closed_ok": len(violations) == 0,
        "unclassified_requested_signals": unclassified,
        "gt_free_signals_missing_from_persisted_table": missing_live,
        "predicted_delta_dice_groundtruth_evidence": predicted_delta_groundtruth_evidence,
        "test_reads": 0,
        "training_performed": False,
        "inference_performed": False,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT_CLASS.write_text(json.dumps(class_payload, indent=2), encoding="utf-8")

    if violations:
        print("FAIL-CLOSED VIOLATION: GT-derived signal marked deployable:", violations)
        return 2

    # ---- B2: GT-free ranking ------------------------------------------------ #
    y = unc[TARGET].astype(float)
    ybin = (y > 0).astype(int)     # diagnostic true-benefit label (may use GT)

    gtfree_rows = []
    for s in GT_FREE_SIGNALS:
        if s not in unc.columns:
            continue
        x = unc[s]
        row = {"signal": s, "uses_GT": False,
               "available_before_refinement": True, "available_at_inference": True,
               "target": TARGET, "target_uses_GT": True}
        row.update(_corr(x, y))
        row.update(_auc(x, ybin))
        gtfree_rows.append(row)
    gtf = pd.DataFrame(gtfree_rows)
    gtf["abs_spearman"] = gtf["spearman_r"].abs()
    gtf = gtf.sort_values("abs_spearman", ascending=False, na_position="last")

    # ---- B3a: GT-free table ------------------------------------------------- #
    gtf_out = gtf[[
        "signal", "uses_GT", "available_before_refinement", "available_at_inference",
        "target", "target_uses_GT", "n", "pearson_r", "spearman_r", "abs_spearman",
        "roc_auc", "pr_auc", "positive_rate"]]
    gtf_out.to_csv(OUT_GTFREE, index=False)

    # ---- B3b: GT-aware post-hoc table --------------------------------------- #
    gt_rows = []
    for s in GT_AWARE_SIGNALS:
        if s not in unc.columns:
            continue
        row = {"signal": s, "uses_GT": True,
               "available_before_refinement": False, "available_at_inference": False,
               "target": TARGET,
               "diagnostic_role": "POST_HOC_GT_ASSOCIATION_DIAGNOSTIC"}
        row.update(_corr(unc[s], y))
        gt_rows.append(row)
    gta = pd.DataFrame(gt_rows)
    gta["abs_spearman"] = gta["spearman_r"].abs()
    gta = gta.sort_values("abs_spearman", ascending=False, na_position="last")
    gta.to_csv(OUT_GTAWARE, index=False)

    best = gtf.iloc[0].to_dict() if len(gtf) else None

    # ---- B4: routing-policy deployability re-verification ------------------- #
    regret = pd.read_csv(T_REGRET)
    pol_rows = []
    for r in regret.itertuples(index=False):
        labelled_deployable = bool(r.deployable_shape)
        gt = bool(r.uses_ground_truth)
        ok = (not labelled_deployable) or (not gt)
        pol_rows.append({
            "policy": r.policy,
            "deployable_shape": labelled_deployable,
            "uses_ground_truth": gt,
            "consistent": ok,
            "verdict": ("OK" if ok else "INCONSISTENT__DEPLOYABLE_BUT_USES_GT"),
        })
    pol_ok = all(p["consistent"] for p in pol_rows)

    # ---- B6: repair record -------------------------------------------------- #
    repair_payload = {
        "artifact": "phase22_postfreeze_semantic_repair",
        "phase": 22,
        "classification": "POST_FREEZE_SEMANTIC_REPAIR",
        "reason": ("the executed uncertainty-benefit analysis reported a GT-derived "
                   "metric (`recall`) as the best DEPLOYABLE routing signal, and the "
                   "rendered report repeated the claim. A deployment cannot compute "
                   "recall, so the claim was semantically invalid. GT-derived and "
                   "GT-free quantities are now separated into two tables and the "
                   "deployable ranking is recomputed from GT-free signals only."),
        "original_freeze_artifact": "reports/audits/phase22_final_freeze.json",
        "original_freeze_sha256": _sha_file(
            ROOT / "reports/audits/phase22_final_freeze.json"),
        "scientific_inference_rerun": False,
        "training_rerun": False,
        "checkpoint_changed": False,
        "roi_protocol_changed": False,
        "scale_protocol_changed": False,
        "segmentation_thresholds_changed": False,
        "gt_free_proxy_analysis_corrected": True,
        "wording_corrected": True,
        "new_inference_performed": False,
        "npz_probability_maps_reread": False,
        "router_trained": False,
        "threshold_fitted": False,
        "model_selected_on_val": False,
        "invalid_claim_removed": "Best deployable uncertainty signal: recall",
        "wording_repairs": {
            "scale_512_optimal": {
                "removed_claim": "512 is optimal / implied globally optimal resolution",
                "required_replacement": (
                    "For the frozen checkpoint trained at 512, 512 had the highest observed "
                    "performance among the tested diagnostic resolutions (256/512/768/1024); "
                    "all tested off-canonical sizes were worse. This does not establish a "
                    "globally optimal inference resolution."),
                "applied_in": ["reports/phase22_resource_gap_report.md",
                               "notebooks/phasewise/phase_22_resource_gap/"
                               "phase22_resource_gap_analysis.ipynb"],
            },
            "kub_tiny_significance": {
                "removed_claim": "KUB TINY improves under regional processing",
                "required_replacement": (
                    "KUB TINY was the only frozen size stratum with a positive observed mean "
                    "oracle regional gain (+0.013197 Dice), but the paired 95% CI "
                    "[-0.084062, +0.105133] includes zero (p=0.763); therefore the TINY "
                    "effect is descriptive and not statistically established."),
                "preserved_finding": (
                    "regional benefit is strongly heterogeneous and always-on regional "
                    "processing is harmful in aggregate"),
                "applied_in": ["reports/phase22_resource_gap_report.md",
                               "notebooks/phasewise/phase_22_resource_gap/"
                               "phase22_resource_gap_analysis.ipynb"],
            },
            "deployable_recall": {
                "removed_claim": "Best deployable uncertainty signal: recall",
                "replacement": ("GT-derived and GT-free signals separated into two tables; "
                                "no GT-derived signal is called deployable; the GT-free "
                                "ranking is recomputed from prediction-only signals"),
            },
        },
        "gt_free_deployable_ranking": [
            {"rank": i + 1, "signal": r["signal"],
             "spearman_r": r["spearman_r"], "pearson_r": r["pearson_r"],
             "abs_spearman": r["abs_spearman"], "roc_auc": r.get("roc_auc"),
             "pr_auc": r.get("pr_auc"), "n": r["n"]}
            for i, r in enumerate(gtf.to_dict("records"))
        ],
        "best_gt_free_signal": ({"signal": best["signal"],
                                 "spearman_r": best["spearman_r"],
                                 "pearson_r": best["pearson_r"],
                                 "roc_auc": best.get("roc_auc"),
                                 "pr_auc": best.get("pr_auc"),
                                 "n": best["n"]} if best else None),
        "best_gt_free_signal_interpretation": (
            "these are DESCRIPTIVE post-hoc correlations on the same frozen VAL "
            "population; they are weak in magnitude and no threshold was fitted and "
            "no policy was selected. The GT-free ranking does not establish a "
            "deployable router."),
        "routing_policy_deployability_audit": pol_rows,
        "routing_policy_deployability_all_consistent": bool(pol_ok),
        "tables": {
            "gt_free_proxy_vs_benefit": str(OUT_GTFREE.relative_to(ROOT)).replace("\\", "/"),
            "gt_aware_posthoc_associations": str(OUT_GTAWARE.relative_to(ROOT)).replace("\\", "/"),
        },
        "classification_artifact": str(OUT_CLASS.relative_to(ROOT)).replace("\\", "/"),
        "test_image_reads": 0,
        "test_mask_reads": 0,
        "test_inference": 0,
        "test_visualization": 0,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
    }
    OUT_REPAIR.write_text(json.dumps(repair_payload, indent=2), encoding="utf-8")

    print(f"WROTE {OUT_CLASS}")
    print(f"WROTE {OUT_GTFREE}")
    print(f"WROTE {OUT_GTAWARE}")
    print(f"WROTE {OUT_REPAIR}")
    print(f"  classified signals        : {len(CLASSIFICATION)}")
    print(f"  deployable candidates     : {len(class_payload['deployable_candidates'])}")
    print(f"  GT-derived signals        : {len(class_payload['gt_derived_signals'])}")
    print(f"  fail-closed violations    : {violations}")
    print(f"  GT-free ranking (top 5)   :")
    for i, r in enumerate(gtf.to_dict("records")[:5]):
        print(f"    {i + 1}. {r['signal']:<36} spearman={r['spearman_r']:+.4f} "
              f"pearson={r['pearson_r']:+.4f} auc={r.get('roc_auc')}")
    print(f"  routing policies consistent: {pol_ok}")
    ok = (not violations) and pol_ok and (best is not None)
    print("  RESULT                    :", "PASS" if ok else "FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
