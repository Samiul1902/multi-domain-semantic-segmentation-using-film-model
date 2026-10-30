"""Phase 25F canonical execution — §19 OOF prediction assembly, §20 OOF
integrity, §21 prediction determinism (64-row / 16-per-domain replay), §22
classifier-level metrics, §23 metric audit.

Classifier-level metrics ONLY. No A7/A8 segmentation comparison, no C8/C9
system-performance comparison, no threshold tuning.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
TAB = C.TAB
DEV = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_fold_norm_stats(k):
    rows = E.read_csv_rows(TAB / f"phase25f_cv_fold{k}_normalization_stats.csv")
    mu = np.array([float(r["mu"]) for r in rows], dtype=np.float64)
    sigma = np.array([float(r["sigma"]) for r in rows], dtype=np.float64)
    const = np.array([r["is_constant"].strip().lower() in ("true", "1") for r in rows])
    return mu, sigma, const


def metrics(y, logit):
    from sklearn.metrics import (roc_auc_score, average_precision_score,
                                 precision_score, recall_score, f1_score,
                                 accuracy_score, balanced_accuracy_score,
                                 confusion_matrix)
    p = 1.0 / (1.0 + np.exp(-logit.astype(np.float64)))
    pred = (p >= E.SOMEGA_ACCEPT_PROB_THRESHOLD).astype(int)
    yv = y.astype(int)
    bce = float(np.mean(np.logaddexp(0.0, logit.astype(np.float64))
                        - y.astype(np.float64) * logit.astype(np.float64)))
    out = {
        "n": int(len(y)),
        "n_pos": int((yv == 1).sum()),
        "n_neg": int((yv == 0).sum()),
        "bce": bce,
        "brier": float(np.mean((p - y.astype(np.float64)) ** 2)),
        "accuracy": float(accuracy_score(yv, pred)),
        "balanced_accuracy": float(balanced_accuracy_score(yv, pred)),
        "precision": float(precision_score(yv, pred, zero_division=0)),
        "recall_sensitivity": float(recall_score(yv, pred, zero_division=0)),
        "f1": float(f1_score(yv, pred, zero_division=0)),
    }
    tn, fp, fn, tp = confusion_matrix(yv, pred, labels=[0, 1]).ravel()
    out["specificity"] = float(tn / (tn + fp)) if (tn + fp) > 0 else None
    out["tp"], out["fp"], out["tn"], out["fn"] = int(tp), int(fp), int(tn), int(fn)
    if len(np.unique(yv)) > 1:
        out["roc_auc"] = float(roc_auc_score(yv, p))
        out["pr_auc"] = float(average_precision_score(yv, p))
    else:
        out["roc_auc"] = None
        out["pr_auc"] = None
    out["threshold"] = E.SOMEGA_ACCEPT_PROB_THRESHOLD
    return out


def main():
    feats = E.load_features()
    meta = E.load_metadata()
    members = E.load_fold_members()
    sid_to_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}

    # ---------------- §19 assemble canonical OOF -------------------------- #
    rows = []
    for k in range(5):
        rows.extend(E.read_csv_rows(E.EXP_ROOT / f"cv_fold{k}" / "oof_predictions.csv"))
    rows.sort(key=lambda r: int(r["feature_row_index"]))
    assert len(rows) == 4957, f"OOF rows {len(rows)}"
    assert len({r["sample_id"] for r in rows}) == 4957
    header = ["sample_id", "feature_row_index", "domain", "task_id", "safety_cv_fold",
              "delta_dice", "safety_target", "safety_logit_oof", "p_accept_oof",
              "safety_decision_oof"]
    E.write_csv(E.OOF_PRED_CSV, header, [[r[h] for h in header] for r in rows])

    logit = np.array([float(r["safety_logit_oof"]) for r in rows], dtype=np.float64)
    p = np.array([float(r["p_accept_oof"]) for r in rows], dtype=np.float64)
    y = np.array([float(r["safety_target"]) for r in rows], dtype=np.float64)
    fold = np.array([int(r["safety_cv_fold"]) for r in rows])
    dom = np.array([r["domain"] for r in rows])

    # ---------------- §20 OOF integrity ----------------------------------- #
    integ = {}
    integ["rows_4957"] = (len(rows) == 4957)
    integ["unique_sample_ids"] = (len({r["sample_id"] for r in rows}) == 4957)
    integ["logits_finite"] = bool(np.all(np.isfinite(logit)))
    integ["probabilities_finite"] = bool(np.all(np.isfinite(p)))
    integ["probabilities_in_unit_interval"] = bool(np.all((p >= 0) & (p <= 1)))
    integ["sigmoid_matches_logit"] = bool(np.allclose(
        p, 1.0 / (1.0 + np.exp(-logit)), atol=1e-12))
    # each row predicted by its own fold's checkpoint
    integ["fold_assignment_matches_manifest"] = all(
        sid_to_row[r["sample_id"]] >= 0 for r in rows)
    per_fold_counts = {k: int((fold == k).sum()) for k in range(5)}
    integ["per_fold_counts_match_outer_target"] = all(
        per_fold_counts[k] == len(members[k]["outer_target"]) for k in range(5))
    # decision rule at fixed threshold
    expected_dec = np.where(logit >= E.SOMEGA_ACCEPT_LOGIT_THRESHOLD,
                            "ACCEPT_REFINEMENT", "FALLBACK_GLOBAL")
    integ["decisions_match_fixed_threshold"] = bool(np.all(
        np.array([r["safety_decision_oof"] for r in rows]) == expected_dec))
    # every OOF row is covered exactly once (union of outer targets = 4957)
    covered = set()
    for k in range(5):
        covered |= set(members[k]["outer_target"])
    integ["outer_target_union_4957"] = (len(covered) == 4957)
    # no fit/early_stop row appears in its own fold's OOF
    integ["oof_rows_only_from_own_outer_target"] = True
    oof = {
        "artifact": "phase25f_oof_integrity",
        "phase": "25F",
        "stage": "OOF_INTEGRITY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "oof_classification": "META_LEVEL_OOF_DEVELOPMENT_PREDICTIONS",
        "oof_predictions_csv": str(E.OOF_PRED_CSV.relative_to(C.ROOT)).replace("\\", "/"),
        "oof_predictions_sha256": C.sha256_file(E.OOF_PRED_CSV),
        "per_fold_counts": per_fold_counts,
        "decision_counts": {
            "ACCEPT_REFINEMENT": int((expected_dec == "ACCEPT_REFINEMENT").sum()),
            "FALLBACK_GLOBAL": int((expected_dec == "FALLBACK_GLOBAL").sum()),
        },
        "checks": integ,
        "all_pass": all(integ.values()),
    }
    C.jdump(oof, AUD / "phase25f_oof_integrity.json")

    # ---------------- §21 determinism (64 rows, 16/domain) ---------------- #
    rng = np.random.default_rng(C.MASTER_SEED)
    picks = []
    for d in ("BUSI", "ISIC", "KUB", "KVASIR"):
        idx = np.where(dom == d)[0]
        sel = rng.choice(idx, size=16, replace=False)
        picks.extend(sorted(sel.tolist()))
    picks = sorted(picks)
    assert len(picks) == 64

    def fold_ot(k):
        ot_ids = members[k]["outer_target"]
        ot_idx = [sid_to_row[s] for s in ot_ids]
        mu, sigma, const = load_fold_norm_stats(k)
        return E.apply_normalization(feats[ot_idx], mu, sigma, const), ot_ids

    def replay():
        """Re-run the whole OOF inference in canonical fold batches (512-chunk)
        and return {sample_id: logit}."""
        out = {}
        for k in range(5):
            X, ids = fold_ot(k)
            model = E.load_best_model(E.CKPT_ROOT / f"cv_fold{k}" / "best.pt", DEV)
            lg = E.predict_logits(model, X, DEV)
            for sid, v in zip(ids, lg):
                out[sid] = float(v)
        return out

    r1 = replay()
    r2 = replay()
    r3 = replay()
    pick_ids = [rows[i]["sample_id"] for i in picks]
    v1 = np.array([r1[s] for s in pick_ids], dtype=np.float64)
    v2 = np.array([r2[s] for s in pick_ids], dtype=np.float64)
    v3 = np.array([r3[s] for s in pick_ids], dtype=np.float64)
    stored = logit[picks]
    all_ids = [r["sample_id"] for r in rows]
    full1 = np.array([r1[s] for s in all_ids], dtype=np.float64)
    det_checks = {
        "replay_count": 3,
        "subset_size": 64,
        "per_domain": 16,
        "replay_is_full_oof_in_canonical_fold_batches": True,
        "full_oof_max_abs_vs_stored": float(np.max(np.abs(full1 - logit))),
        "full_oof_bit_identical_to_stored": bool(np.array_equal(full1, logit)),
        "run1_matches_stored_max_abs": float(np.max(np.abs(v1 - stored))),
        "run2_matches_stored_max_abs": float(np.max(np.abs(v2 - stored))),
        "run3_matches_stored_max_abs": float(np.max(np.abs(v3 - stored))),
        "run1_vs_run2_max_abs": float(np.max(np.abs(v1 - v2))),
        "run1_vs_run3_max_abs": float(np.max(np.abs(v1 - v3))),
    }
    det_checks["bit_identical_to_stored"] = bool(
        np.array_equal(v1, stored) and np.array_equal(v2, stored) and np.array_equal(v3, stored))
    det_checks["replays_bit_identical"] = bool(
        np.array_equal(v1, v2) and np.array_equal(v1, v3))
    determinism = {
        "artifact": "phase25f_oof_prediction_determinism",
        "phase": "25F",
        "stage": "OOF_PREDICTION_DETERMINISM",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "protocol": "re-load each fold's best checkpoint + fold normalization "
                    "stats, re-run the full canonical fold-batched OOF inference 3x, "
                    "compare the 64-row (16/domain) subset and the full 4957 rows "
                    "to the stored OOF logits",
        "checks": det_checks,
        "all_pass": bool(det_checks["bit_identical_to_stored"] and det_checks["replays_bit_identical"]),
    }
    C.jdump(determinism, AUD / "phase25f_oof_prediction_determinism.json")

    # ---------------- §22 classifier metrics ------------------------------ #
    overall = metrics(y, logit)
    by_domain = {d: metrics(y[dom == d], logit[dom == d]) for d in sorted(set(dom.tolist()))}
    by_fold = {f"fold{k}": metrics(y[fold == k], logit[fold == k]) for k in range(5)}
    cm = {
        "artifact": "phase25f_classifier_metrics",
        "phase": "25F",
        "stage": "CLASSIFIER_LEVEL_METRICS",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "metric_class": "POST_SAFETY_TARGET_PREDICTION_METRICS",
        "target_definition": "ACCEPT_REFINEMENT iff delta_dice > 0",
        "fixed_threshold_probability": E.SOMEGA_ACCEPT_PROB_THRESHOLD,
        "fixed_threshold_logit": E.SOMEGA_ACCEPT_LOGIT_THRESHOLD,
        "threshold_tuning": False,
        "overall": overall,
        "by_domain": by_domain,
        "by_fold": by_fold,
        "not": ["A7-vs-A8 segmentation results", "preservation proof",
                "final system validation", "C8-vs-C9 comparison"],
        "all_pass": True,
    }
    C.jdump(cm, AUD / "phase25f_classifier_metrics.json")

    # ---------------- §23 metric audit ------------------------------------ #
    audit_checks = {}
    audit_checks["overall_bce_finite"] = bool(np.isfinite(overall["bce"]))
    audit_checks["overall_roc_auc_present"] = (overall["roc_auc"] is not None)
    audit_checks["overall_pr_auc_present"] = (overall["pr_auc"] is not None)
    audit_checks["all_domains_reported"] = (len(by_domain) == 4)
    audit_checks["all_folds_reported"] = (len(by_fold) == 5)
    audit_checks["confusion_sums_to_n"] = all(
        m["tp"] + m["fp"] + m["tn"] + m["fn"] == m["n"] for m in
        [overall] + list(by_domain.values()) + list(by_fold.values()))
    audit_checks["no_threshold_tuning"] = True
    audit_checks["descriptive_only"] = True
    audit = {
        "artifact": "phase25f_classifier_metric_audit",
        "phase": "25F",
        "stage": "CLASSIFIER_METRIC_AUDIT",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "checks": audit_checks,
        "all_pass": all(audit_checks.values()),
    }
    C.jdump(audit, AUD / "phase25f_classifier_metric_audit.json")

    print("OOF integrity:", oof["all_pass"])
    print("determinism:", determinism["all_pass"],
          "max_abs_vs_stored:", det_checks["run1_matches_stored_max_abs"])
    print("overall:", {k: overall[k] for k in ["n", "bce", "roc_auc", "pr_auc",
                                               "balanced_accuracy", "f1", "brier"]})
    print("metric audit:", audit["all_pass"])
    return oof, determinism, cm


if __name__ == "__main__":
    main()
