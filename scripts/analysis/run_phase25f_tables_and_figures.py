"""Phase 25F canonical execution — §31 tables (18) and §32 figures (9).

Deterministic: fixed dpi, Agg backend, no timestamps in PNG metadata.
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_execution_common as E  # noqa: E402

AUD = C.AUD
TAB = C.TAB
FIG = C.ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "figure.dpi": 110, "savefig.dpi": 110, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.3, "figure.facecolor": "white",
    "axes.facecolor": "white", "savefig.facecolor": "white",
})
DOMAIN_COLORS = {"BUSI": "#1f77b4", "ISIC": "#ff7f0e", "KUB": "#2ca02c", "KVASIR": "#d62728"}


def savefig(fig, name):
    p = FIG / name
    fig.tight_layout()
    fig.savefig(p, format="png", metadata={"Software": None})
    plt.close(fig)
    return p


def main():
    tables = []

    # 1. entry-gate summary
    gate = C.jload(AUD / "phase25f_execution_reentry_gate.json")
    E.write_csv(TAB / "phase25f_execution_entry_gate_summary.csv",
                ["check", "pass"], [[k, int(v)] for k, v in gate["checks"].items()])
    tables.append("phase25f_execution_entry_gate_summary.csv")

    # 2. contract binding summary
    binding = C.jload(AUD / "phase25f_execution_contract_binding.json")
    E.write_csv(TAB / "phase25f_contract_binding_summary.csv",
                ["contract", "path", "exists", "sha256"],
                [[k, v["path"], int(v["exists"]), v["sha256"]]
                 for k, v in binding["frozen_contracts"].items()])
    tables.append("phase25f_contract_binding_summary.csv")

    # 3. join integrity summary
    join = C.jload(AUD / "phase25f_execution_join_integrity.json")
    E.write_csv(TAB / "phase25f_join_integrity_summary.csv",
                ["item", "value"],
                [[k, str(v)] for k, v in join.items() if k not in ("artifact", "phase",
                 "stage", "method", "specification_revision")])
    tables.append("phase25f_join_integrity_summary.csv")

    # 4. split integrity summary
    split = C.jload(AUD / "phase25f_execution_split_integrity.json")
    E.write_csv(TAB / "phase25f_split_integrity_summary.csv",
                ["fold", "fit", "early_stop", "outer_target", "union"],
                [[k, v["fit"], v["early_stop"], v["outer_target"], v["union"]]
                 for k, v in split["per_fold_sizes"].items()])
    tables.append("phase25f_split_integrity_summary.csv")

    # 5. cv fold role assignments
    rows = []
    for k in range(5):
        for role in ("fit", "early_stop", "outer_target"):
            rows.append([k, role, split["per_fold_sizes"][str(k)][role]])
    E.write_csv(TAB / "phase25f_cv_fold_role_assignments.csv",
                ["fold", "role", "n"], rows)
    tables.append("phase25f_cv_fold_role_assignments.csv")

    # 6. cv normalization stats summary
    names = [r["name"] for r in E.read_csv_rows(E.FEATURE_SCHEMA_CSV)]
    rows = []
    for k in range(5):
        st = E.read_csv_rows(TAB / f"phase25f_cv_fold{k}_normalization_stats.csv")
        for r in st:
            rows.append([k, int(r["feature_index"]), r["name"], r["mu"], r["sigma"],
                         int(r["is_constant"].strip().lower() in ("true", "1"))])
    E.write_csv(TAB / "phase25f_cv_normalization_stats_summary.csv",
                ["fold", "feature_index", "name", "mu", "sigma", "is_constant"], rows)
    tables.append("phase25f_cv_normalization_stats_summary.csv")

    # 7. training run summary
    reg = C.jload(AUD / "phase25f_training_run_registry.json")
    runs = {int(k): v for k, v in reg["runs"].items()}
    rows = []
    for k in range(5):
        r = runs[k]
        rows.append([k, r["run_id"], r["seed"], r["n_fit"], r["n_early_stop"],
                     r["n_outer_target"], r["total_epochs"], r["best_epoch"],
                     repr(r["best_monitor_bce"]), r["termination"]])
    E.write_csv(TAB / "phase25f_training_run_summary.csv",
                ["fold", "run_id", "seed", "n_fit", "n_early_stop", "n_outer_target",
                 "total_epochs", "best_epoch", "best_monitor_bce", "termination"], rows)
    tables.append("phase25f_training_run_summary.csv")

    # 8. training health summary
    health = C.jload(AUD / "phase25f_training_health.json")
    E.write_csv(TAB / "phase25f_training_health_summary.csv",
                ["check", "pass"], [[k, int(v)] for k, v in health["checks"].items()])
    tables.append("phase25f_training_health_summary.csv")

    # 9. final epoch rule
    rule = C.jload(AUD / "phase25f_final_epoch_rule_execution.json")
    E.write_csv(TAB / "phase25f_final_epoch_rule.csv",
                ["item", "value"],
                [["best_epoch_fold0", rule["best_epochs_in_fold_order"][0]],
                 ["best_epoch_fold1", rule["best_epochs_in_fold_order"][1]],
                 ["best_epoch_fold2", rule["best_epochs_in_fold_order"][2]],
                 ["best_epoch_fold3", rule["best_epochs_in_fold_order"][3]],
                 ["best_epoch_fold4", rule["best_epochs_in_fold_order"][4]],
                 ["sorted_best_epochs", " ".join(map(str, rule["sorted_best_epochs"]))],
                 ["median_index", rule["median_index"]],
                 ["final_safety_epochs", rule["final_safety_epochs"]],
                 ["final_seed", rule["final_seed"]]])
    tables.append("phase25f_final_epoch_rule.csv")

    # 10. final normalization stats already written by the refit script
    tables.append("phase25f_final_normalization_stats.csv")

    # 11. OOF fold coverage
    oof = E.read_csv_rows(E.OOF_PRED_CSV)
    fold = np.array([int(r["safety_cv_fold"]) for r in oof])
    y = np.array([float(r["safety_target"]) for r in oof])
    dec = np.array([r["safety_decision_oof"] for r in oof])
    rows = []
    for k in range(5):
        m = fold == k
        rows.append([k, int(m.sum()), int((dec[m] == "ACCEPT_REFINEMENT").sum()),
                     int((dec[m] == "FALLBACK_GLOBAL").sum()),
                     int((y[m] == 1).sum()), int((y[m] == 0).sum())])
    E.write_csv(TAB / "phase25f_oof_fold_coverage.csv",
                ["fold", "n", "n_accept", "n_fallback", "n_pos", "n_neg"], rows)
    tables.append("phase25f_oof_fold_coverage.csv")

    # 12. OOF decision distribution (by domain)
    dom = np.array([r["domain"] for r in oof])
    rows = []
    for d in sorted(set(dom.tolist())):
        m = dom == d
        rows.append([d, int(m.sum()), int((dec[m] == "ACCEPT_REFINEMENT").sum()),
                     int((dec[m] == "FALLBACK_GLOBAL").sum()),
                     int((y[m] == 1).sum()), int((y[m] == 0).sum())])
    E.write_csv(TAB / "phase25f_oof_decision_distribution.csv",
                ["domain", "n", "n_accept", "n_fallback", "n_pos", "n_neg"], rows)
    tables.append("phase25f_oof_decision_distribution.csv")

    # 13-15. classifier metrics
    cm = C.jload(AUD / "phase25f_classifier_metrics.json")
    mkeys = ["n", "n_pos", "n_neg", "bce", "brier", "accuracy", "balanced_accuracy",
             "precision", "recall_sensitivity", "specificity", "f1", "roc_auc", "pr_auc",
             "tp", "fp", "tn", "fn"]
    E.write_csv(TAB / "phase25f_classifier_metrics_overall.csv",
                ["metric", "value"], [[k, cm["overall"][k]] for k in mkeys])
    tables.append("phase25f_classifier_metrics_overall.csv")
    E.write_csv(TAB / "phase25f_classifier_metrics_by_domain.csv",
                ["domain"] + mkeys, [[d] + [cm["by_domain"][d][k] for k in mkeys]
                                     for d in sorted(cm["by_domain"])])
    tables.append("phase25f_classifier_metrics_by_domain.csv")
    E.write_csv(TAB / "phase25f_classifier_metrics_by_fold.csv",
                ["fold"] + mkeys, [[f] + [cm["by_fold"][f][k] for k in mkeys]
                                   for f in sorted(cm["by_fold"])])
    tables.append("phase25f_classifier_metrics_by_fold.csv")

    # 16. C9 decision summary already written
    tables.append("phase25f_c9_decision_summary.csv")

    # 17. checkpoint registry
    rows = []
    for k in range(5):
        p = E.CKPT_ROOT / f"cv_fold{k}" / "best.pt"
        rows.append([f"{E.RUN_FAMILY}_cv_fold{k}", "cv_best", E.CV_SEEDS[k],
                     str(p.relative_to(C.ROOT)).replace("\\", "/"), C.sha256_file(p)])
    fp = E.CKPT_ROOT / "final" / "final.pt"
    rows.append([f"{E.RUN_FAMILY}_final", "final_refit", E.FINAL_SEED,
                 str(fp.relative_to(C.ROOT)).replace("\\", "/"), C.sha256_file(fp)])
    E.write_csv(TAB / "phase25f_checkpoint_registry.csv",
                ["run_id", "kind", "seed", "path", "sha256"], rows)
    tables.append("phase25f_checkpoint_registry.csv")

    # 18. scope lock summary
    guard = C.jload(AUD / "phase25f_a7_a8_execution_guard.json")
    E.write_csv(TAB / "phase25f_scope_lock_summary.csv",
                ["item", "value"],
                [["router_holdout_reads", guard["router_holdout_reads"]],
                 ["VAL808_reads", guard["VAL808_reads"]],
                 ["TEST_reads", guard["TEST_reads"]],
                 ["A7_A8_segmentation_comparison_performed",
                  int(guard["A7_A8_segmentation_comparison_performed"])],
                 ["C8_C9_system_performance_comparison_performed",
                  int(guard["C8_C9_system_performance_comparison_performed"])],
                 ["preservation_adjudication_performed",
                  int(guard["preservation_adjudication_performed"])],
                 ["threshold_tuned", 0],
                 ["new_budget_or_lambda_selected", 0]])
    tables.append("phase25f_scope_lock_summary.csv")

    assert len(tables) == 18, len(tables)

    # ================= §32 figures (9) =================================== #
    figs = []

    # history arrays
    hists = {}
    for k in range(5):
        h = E.read_csv_rows(E.EXP_ROOT / f"cv_fold{k}" / "history.csv")
        hists[k] = (np.array([int(r["epoch"]) for r in h]),
                    np.array([float(r["train_bce"]) for r in h]),
                    np.array([float(r["early_stop_bce"]) for r in h]))

    # fig 1: training curves
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.6))
    for k in range(5):
        ep, tr, es = hists[k]
        axes[0].plot(ep, tr, lw=1, label=f"fold{k}")
        axes[1].plot(ep, es, lw=1, label=f"fold{k}")
    axes[0].set_title("FIT train BCE"); axes[1].set_title("EARLY_STOP mean BCE")
    for a in axes:
        a.set_xlabel("epoch"); a.set_ylabel("BCE"); a.legend(fontsize=7)
    figs.append(savefig(fig, "p25f_training_curves.png"))

    # fig 2: best epochs
    be = [int(runs[k]["best_epoch"]) for k in range(5)]
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.bar([f"f{k}" for k in range(5)], be, color="#1f77b4")
    ax.axhline(rule["final_safety_epochs"], color="#d62728", ls="--", lw=1.2,
               label=f"median = {rule['final_safety_epochs']}")
    for i, v in enumerate(be):
        ax.text(i, v + 1, str(v), ha="center", fontsize=8)
    ax.set_ylabel("best epoch (min EARLY_STOP BCE)"); ax.legend(fontsize=8)
    ax.set_title("Per-fold selected epoch + median rule")
    figs.append(savefig(fig, "p25f_best_epochs.png"))

    # fig 3: OOF logit distribution by class
    logit = np.array([float(r["safety_logit_oof"]) for r in oof])
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.hist(logit[y == 1], bins=40, alpha=0.6, label="ACCEPT (y=1)", color="#d62728")
    ax.hist(logit[y == 0], bins=40, alpha=0.6, label="FALLBACK (y=0)", color="#1f77b4")
    ax.axvline(0.0, color="black", ls="--", lw=1, label="logit threshold 0.0")
    ax.set_xlabel("OOF safety logit"); ax.set_ylabel("count"); ax.legend(fontsize=8)
    ax.set_title("OOF logit distribution by target class")
    figs.append(savefig(fig, "p25f_oof_logit_distribution.png"))

    # fig 4: OOF probability by domain
    p = np.array([float(r["p_accept_oof"]) for r in oof])
    fig, ax = plt.subplots(figsize=(6.0, 3.2))
    data = [p[dom == d] for d in sorted(set(dom.tolist()))]
    labels = sorted(set(dom.tolist()))
    bp = ax.boxplot(data, tick_labels=labels, patch_artist=True, showfliers=False)
    for patch, d in zip(bp["boxes"], labels):
        patch.set_facecolor(DOMAIN_COLORS[d]); patch.set_alpha(0.6)
    ax.axhline(0.5, color="black", ls="--", lw=1)
    ax.set_ylabel("OOF p_accept"); ax.set_title("OOF accept probability by domain")
    figs.append(savefig(fig, "p25f_oof_prob_by_domain.png"))

    # fig 5/6: ROC and PR curves
    from sklearn.metrics import roc_curve, precision_recall_curve, roc_auc_score, average_precision_score
    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    fpr, tpr, _ = roc_curve(y.astype(int), p)
    ax.plot(fpr, tpr, color="black", lw=1.6, label=f"overall AUC={roc_auc_score(y.astype(int), p):.3f}")
    for d in sorted(set(dom.tolist())):
        m = dom == d
        f2, t2, _ = roc_curve(y[m].astype(int), p[m])
        ax.plot(f2, t2, lw=1, color=DOMAIN_COLORS[d],
                label=f"{d} AUC={roc_auc_score(y[m].astype(int), p[m]):.3f}")
    ax.plot([0, 1], [0, 1], ls=":", color="gray", lw=1)
    ax.set_xlabel("FPR"); ax.set_ylabel("TPR"); ax.legend(fontsize=7)
    ax.set_title("OOF ROC (classifier level)")
    figs.append(savefig(fig, "p25f_roc_curves.png"))

    fig, ax = plt.subplots(figsize=(4.6, 4.2))
    pr, rc, _ = precision_recall_curve(y.astype(int), p)
    ax.plot(rc, pr, color="black", lw=1.6,
            label=f"overall AP={average_precision_score(y.astype(int), p):.3f}")
    for d in sorted(set(dom.tolist())):
        m = dom == d
        p2, r2, _ = precision_recall_curve(y[m].astype(int), p[m])
        ax.plot(r2, p2, lw=1, color=DOMAIN_COLORS[d],
                label=f"{d} AP={average_precision_score(y[m].astype(int), p[m]):.3f}")
    ax.axhline(float((y == 1).mean()), ls=":", color="gray", lw=1)
    ax.set_xlabel("recall"); ax.set_ylabel("precision"); ax.legend(fontsize=7)
    ax.set_title("OOF precision-recall (classifier level)")
    figs.append(savefig(fig, "p25f_pr_curves.png"))

    # fig 7: confusion matrix
    o = cm["overall"]
    M = np.array([[o["tn"], o["fp"]], [o["fn"], o["tp"]]])
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    im = ax.imshow(M, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, str(M[i, j]), ha="center", va="center",
                    color="white" if M[i, j] > M.max() / 2 else "black")
    ax.set_xticks([0, 1], ["pred FALLBACK", "pred ACCEPT"])
    ax.set_yticks([0, 1], ["true FALLBACK", "true ACCEPT"])
    ax.set_title(f"OOF confusion @ p>=0.50")
    ax.grid(False)
    figs.append(savefig(fig, "p25f_confusion_matrix.png"))

    # fig 8: metrics by domain
    fig, ax = plt.subplots(figsize=(6.4, 3.2))
    ds = sorted(cm["by_domain"])
    x = np.arange(len(ds)); w = 0.2
    for i, mk in enumerate(["roc_auc", "pr_auc", "balanced_accuracy", "f1"]):
        vals = [cm["by_domain"][d][mk] for d in ds]
        ax.bar(x + (i - 1.5) * w, vals, w, label=mk)
    ax.set_xticks(x, ds); ax.set_ylim(0, 1); ax.legend(fontsize=7)
    ax.set_title("Classifier metrics by domain (OOF, @0.50)")
    figs.append(savefig(fig, "p25f_metrics_by_domain.png"))

    # fig 9: C9 state distribution
    c9 = C.jload(AUD / "phase25f_c9_decision_artifact.json")
    pol = c9["per_policy"]
    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    labels = [f"L{p['lambda']}B{p['budget']}" for p in pol]
    acc = [p["n_accept"] for p in pol]; rej = [p["n_reject"] for p in pol]
    skp = [p["n_skip"] for p in pol]
    ax.bar(labels, acc, label="STATE_C accept (regional-fused)", color="#2ca02c")
    ax.bar(labels, rej, bottom=acc, label="STATE_C reject (fallback)", color="#d62728")
    ax.bar(labels, skp, bottom=np.array(acc) + np.array(rej),
           label="STATE_B skip (global)", color="#7f7f7f")
    ax.set_ylabel("samples (of 4957)")
    ax.tick_params(axis="x", rotation=90, labelsize=6)
    ax.legend(fontsize=7)
    ax.set_title("C9 post-safety state distribution per frozen C8 policy")
    figs.append(savefig(fig, "p25f_c9_state_distribution.png"))

    assert len(figs) == 9, len(figs)

    # visual integrity check
    integrity = []
    for pth in figs:
        b = pth.read_bytes()
        ok_magic = b[:8] == b"\x89PNG\r\n\x1a\n"
        ok_iend = b[-8:-4] == b"IEND"
        integrity.append({"figure": pth.name, "magic_ok": ok_magic,
                          "iend_ok": ok_iend, "bytes": len(b),
                          "sha256": C.sha256_file(pth)})
    all_ok = all(i["magic_ok"] and i["iend_ok"] for i in integrity)

    C.jdump({
        "artifact": "phase25f_tables_and_figures_manifest",
        "phase": "25F",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "table_count": len(tables),
        "tables": tables,
        "figure_count": len(figs),
        "figures": [str(f.relative_to(C.ROOT)).replace("\\", "/") for f in figs],
        "visual_integrity": integrity,
        "all_pass": all_ok,
    }, AUD / "phase25f_tables_and_figures_manifest.json")

    print(f"tables={len(tables)} figures={len(figs)} visual_integrity={all_ok}")
    return tables, figs


if __name__ == "__main__":
    main()
