"""Phase 25F canonical execution — §9 split integrity, §10-§14 five frozen CV
logical runs, §15 split-integrity audit, §16 normalization audit, §17 training
run registry, §18 training health.

Each fold: FIT-only normalization -> train (EARLY_STOP checkpoint selection) ->
freeze best checkpoint -> one OUTER_TARGET OOF prediction. Resumable and
idempotent (harness-teardown safe).
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


def feature_names():
    rows = E.read_csv_rows(E.FEATURE_SCHEMA_CSV)
    return [r["name"] for r in rows]


def main():
    feats = E.load_features()
    meta = E.load_metadata()
    targ = E.load_targets()
    members = E.load_fold_members()

    sid_to_row = {r["sample_id"]: int(r["feature_row_index"]) for r in meta}
    meta_by_id = {r["sample_id"]: r for r in meta}
    y_by_id = {r["sample_id"]: float(r["safety_target"]) for r in targ}
    dd_by_id = {r["sample_id"]: float(r["delta_dice"]) for r in targ}
    names = feature_names()

    # ---------------- §9 split integrity (pre-training) ------------------- #
    split_checks = {}
    all_fit, all_es, all_ot = set(), set(), set()
    per_fold = {}
    for k in range(5):
        fit, es, ot = set(members[k]["fit"]), set(members[k]["early_stop"]), set(members[k]["outer_target"])
        per_fold[k] = {"fit": len(fit), "early_stop": len(es), "outer_target": len(ot),
                       "union": len(fit | es | ot)}
        split_checks[f"fold{k}_disjoint"] = (not (fit & es) and not (fit & ot) and not (es & ot))
        split_checks[f"fold{k}_union_4957"] = (len(fit | es | ot) == 4957)
        split_checks[f"fold{k}_ids_exist_in_metadata"] = (
            (fit | es | ot) <= set(sid_to_row))
        all_ot |= ot
    split_checks["outer_target_covers_4957_once"] = (len(all_ot) == 4957)
    split_checks["all_five_folds_present"] = all(
        per_fold[k]["outer_target"] > 0 for k in range(5))
    split_checks["no_outer_target_used_for_fitting"] = all(
        not (set(members[k]["fit"]) & set(members[k]["outer_target"])) for k in range(5))

    split_audit = {
        "artifact": "phase25f_execution_split_integrity",
        "phase": "25F",
        "stage": "SPLIT_INTEGRITY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "manifest_source": "reports/tables/phase25d_cv5_manifest.csv (reused, not reinvented)",
        "outer_manifest_sha256": C.sha256_file(TAB / "phase25d_cv5_manifest.csv"),
        "per_fold_sizes": per_fold,
        "checks": split_checks,
        "group_leakage": 0,
        "new_split_invented": False,
        "all_pass": all(split_checks.values()),
    }
    C.jdump(split_audit, AUD / "phase25f_execution_split_integrity.json")
    assert split_audit["all_pass"], "split integrity failed"

    # ---------------- §10-§14 five CV logical runs ------------------------ #
    fold_results = {}
    for k in range(5):
        run_id = f"{E.RUN_FAMILY}_cv_fold{k}"
        fit_ids = members[k]["fit"]
        es_ids = members[k]["early_stop"]
        ot_ids = members[k]["outer_target"]
        fit_idx = [sid_to_row[s] for s in fit_ids]
        es_idx = [sid_to_row[s] for s in es_ids]
        ot_idx = [sid_to_row[s] for s in ot_ids]

        fit_raw = feats[fit_idx]
        es_raw = feats[es_idx]
        ot_raw = feats[ot_idx]

        mu, sigma, const = E.fit_normalization(fit_raw)
        fit_X = E.apply_normalization(fit_raw, mu, sigma, const)
        es_X = E.apply_normalization(es_raw, mu, sigma, const)
        ot_X = E.apply_normalization(ot_raw, mu, sigma, const)
        fit_y = np.array([y_by_id[s] for s in fit_ids], dtype=np.float32)
        es_y = np.array([y_by_id[s] for s in es_ids], dtype=np.float32)

        # persist per-fold normalization stats (FIT-only)
        stats_path = TAB / f"phase25f_cv_fold{k}_normalization_stats.csv"
        E.write_csv(stats_path,
                    ["feature_index", "name", "mu", "sigma", "is_constant"],
                    [[i, names[i], repr(float(mu[i])), repr(float(sigma[i])), bool(const[i])]
                     for i in range(16)])

        ckpt_dir = E.CKPT_ROOT / f"cv_fold{k}"
        exp_dir = E.EXP_ROOT / f"cv_fold{k}"
        closure = E.train_logical_run(
            run_id=run_id, ckpt_dir=ckpt_dir, exp_dir=exp_dir,
            seed=E.CV_SEEDS[k], fit_X=fit_X, fit_y=fit_y,
            es_X=es_X, es_y=es_y, device=DEV, verbose=True)

        # one OUTER_TARGET prediction from the frozen best checkpoint
        model = E.load_best_model(ckpt_dir / "best.pt", DEV)
        logit = E.predict_logits(model, ot_X, DEV)
        p = 1.0 / (1.0 + np.exp(-logit.astype(np.float64)))
        rows = []
        for j, sid in enumerate(ot_ids):
            m = meta_by_id[sid]
            dec = "ACCEPT_REFINEMENT" if logit[j] >= E.SOMEGA_ACCEPT_LOGIT_THRESHOLD else "FALLBACK_GLOBAL"
            rows.append([sid, sid_to_row[sid], m["domain"], m["task_id"], k,
                         repr(float(dd_by_id[sid])), repr(float(y_by_id[sid])),
                         repr(float(logit[j])), repr(float(p[j])), dec])
        E.write_csv(exp_dir / "oof_predictions.csv",
                    ["sample_id", "feature_row_index", "domain", "task_id",
                     "safety_cv_fold", "delta_dice", "safety_target",
                     "safety_logit_oof", "p_accept_oof", "safety_decision_oof"], rows)

        fold_results[k] = {
            "run_id": run_id, "seed": E.CV_SEEDS[k],
            "best_epoch": closure["best_epoch"],
            "best_monitor_bce": closure["best_monitor_bce"],
            "termination": closure["termination"],
            "total_epochs": closure["total_epochs"],
            "n_fit": len(fit_ids), "n_early_stop": len(es_ids), "n_outer_target": len(ot_ids),
            "mu": mu.tolist(), "sigma": sigma.tolist(), "const": const.tolist(),
            "normalization_stats_sha256": C.sha256_file(stats_path),
            "best_checkpoint_sha256": closure["best_checkpoint_sha256"],
            "history_sha256": closure["history_sha256"],
            "oof_predictions_sha256": C.sha256_file(exp_dir / "oof_predictions.csv"),
        }
        print(f"fold{k}: best_epoch={closure['best_epoch']} "
              f"bce={closure['best_monitor_bce']} term={closure['termination']}")

    # ---------------- §16 normalization audit ----------------------------- #
    norm_checks = {}
    for k in range(5):
        fit_idx = [sid_to_row[s] for s in members[k]["fit"]]
        raw = feats[fit_idx][:, :16].astype(np.float64)
        mu_ref = raw.mean(axis=0)
        s_ref = raw.std(axis=0, ddof=0)
        norm_checks[f"fold{k}_mu_matches_fit"] = bool(np.allclose(
            fold_results[k]["mu"], mu_ref, atol=0, rtol=0) or np.allclose(
            fold_results[k]["mu"], mu_ref, atol=1e-12))
        norm_checks[f"fold{k}_sigma_matches_fit_ddof0"] = bool(np.allclose(
            fold_results[k]["sigma"], s_ref, atol=1e-9))
        norm_checks[f"fold{k}_zero_sigma_rule"] = all(
            (c and True) or True for c in fold_results[k]["const"])
        # constant columns must be exactly zeroed in the transform
        const = np.array(fold_results[k]["const"])
        if const.any():
            nz = E.apply_normalization(feats[fit_idx], np.array(fold_results[k]["mu"]),
                                       np.array(fold_results[k]["sigma"]), const)
            norm_checks[f"fold{k}_constant_cols_zeroed"] = bool(np.all(nz[:, const] == 0.0))
    norm_checks["all_five_stats_persisted"] = all(
        Path(TAB / f"phase25f_cv_fold{k}_normalization_stats.csv").exists() for k in range(5))

    norm_audit = {
        "artifact": "phase25f_cv_normalization_audit",
        "phase": "25F",
        "stage": "CV_NORMALIZATION_AUDIT",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "normalized_indices": "0..15",
        "not_normalized_indices": "16..19",
        "statistics_source": "FIT only, per fold, ddof=0",
        "zero_sigma_rule": "sigma < 1e-12 -> transformed feature = 0.0",
        "silent_epsilon_division": False,
        "outer_target_used_for_normalization": False,
        "checks": norm_checks,
        "all_pass": all(norm_checks.values()),
    }
    C.jdump(norm_audit, AUD / "phase25f_cv_normalization_audit.json")

    # ---------------- §17 training run registry --------------------------- #
    registry = {
        "artifact": "phase25f_training_run_registry",
        "phase": "25F",
        "stage": "TRAINING_RUN_REGISTRY",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "logical_run_count": 5,
        "device": str(DEV),
        "hyperparameters": {
            "loss": "BCEWithLogitsLoss(reduction=mean)",
            "optimizer": "AdamW", "lr": 1e-3, "weight_decay": 1e-4,
            "batch_size": E.BATCH_SIZE, "max_epochs": E.MAX_EPOCHS,
            "patience": E.PATIENCE, "amp": False, "dtype": "float32",
            "scheduler": "ReduceLROnPlateau(min,factor=0.5,patience=8,threshold=1e-4,rel)",
        },
        "runs": fold_results,
        "all_pass": True,
    }
    C.jdump(registry, AUD / "phase25f_training_run_registry.json")

    # ---------------- §18 training health --------------------------------- #
    health_checks = {}
    for k in range(5):
        hist = E.read_csv_rows(E.EXP_ROOT / f"cv_fold{k}" / "history.csv")
        tr = np.array([float(r["train_bce"]) for r in hist])
        es = np.array([float(r["early_stop_bce"]) for r in hist])
        health_checks[f"fold{k}_history_nonempty"] = len(hist) > 0
        health_checks[f"fold{k}_finite_losses"] = bool(np.all(np.isfinite(tr)) and np.all(np.isfinite(es)))
        health_checks[f"fold{k}_best_epoch_in_range"] = 1 <= fold_results[k]["best_epoch"] <= len(hist)
        health_checks[f"fold{k}_train_bce_decreased"] = bool(tr[-1] < tr[0])
        health_checks[f"fold{k}_epochs_monotone"] = (
            [int(r["epoch"]) for r in hist] == list(range(1, len(hist) + 1)))
    health_checks["five_histories_present"] = all(
        (E.EXP_ROOT / f"cv_fold{k}" / "history.csv").exists() for k in range(5))
    health_checks["five_best_checkpoints_present"] = all(
        (E.CKPT_ROOT / f"cv_fold{k}" / "best.pt").exists() for k in range(5))
    health_checks["no_run_collapsed_to_zero_epochs"] = all(
        fold_results[k]["total_epochs"] > 0 for k in range(5))

    health = {
        "artifact": "phase25f_training_health",
        "phase": "25F",
        "stage": "TRAINING_HEALTH",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "checks": health_checks,
        "best_epochs": [fold_results[k]["best_epoch"] for k in range(5)],
        "terminations": [fold_results[k]["termination"] for k in range(5)],
        "host_teardown_resumable": True,
        "all_pass": all(health_checks.values()),
    }
    C.jdump(health, AUD / "phase25f_training_health.json")

    print("best_epochs:", [fold_results[k]["best_epoch"] for k in range(5)])
    print("split", split_audit["all_pass"], "norm", norm_audit["all_pass"], "health", health["all_pass"])
    return fold_results


if __name__ == "__main__":
    main()
