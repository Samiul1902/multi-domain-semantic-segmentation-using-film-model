"""Build remaining Phase25D tables."""
import csv
import json
from pathlib import Path

import numpy as np

ROOT = Path("D:/Softfors/jup")
TABLES = ROOT / "reports/tables"
EXP = ROOT / "experiments/phase25d_barr_benefit_router_v1_2_1_seed42"
CKPT = ROOT / "checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42"
OUT = ROOT / "data_cache/phase25d_barr_benefit_router_v1_2_1"
AUDITS = ROOT / "reports/audits"

# 1. Joined population summary
oof_rows = []
with open(OUT / "phase25d_oof_router_predictions.csv", "r", newline="") as f:
    for r in csv.DictReader(f):
        oof_rows.append(r)

domains = {}
for r in oof_rows:
    d = r["domain"]
    if d not in domains:
        domains[d] = {"count": 0, "beneficial": 0, "neutral": 0, "harmful": 0}
    domains[d]["count"] += 1
    domains[d][r["gain_category"].lower()] += 1

with open(TABLES / "phase25d_joined_population_summary.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["domain", "count", "beneficial", "neutral", "harmful"])
    for d in sorted(domains):
        writer.writerow([d, domains[d]["count"], domains[d]["beneficial"], domains[d]["neutral"], domains[d]["harmful"]])

# 2. CV5 manifest summary
cv_manifest = []
with open(TABLES / "phase25d_cv5_manifest.csv", "r", newline="") as f:
    for r in csv.DictReader(f):
        cv_manifest.append(r)

fold_counts = {}
for r in cv_manifest:
    k = int(r["router_cv_fold"])
    d = r["dataset"]
    if k not in fold_counts:
        fold_counts[k] = {}
    fold_counts[k][d] = fold_counts[k].get(d, 0) + 1

with open(TABLES / "phase25d_cv5_manifest_summary.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["fold", "total", "BUSI", "ISIC", "KUB", "KVASIR"])
    for k in range(5):
        writer.writerow([k, sum(fold_counts[k].values())] + [fold_counts[k].get(d, 0) for d in ["BUSI", "ISIC", "KUB", "KVASIR"]])

# 3. CV selected epochs
registry = json.load(open(AUDITS / "phase25d_training_run_registry.json"))
with open(TABLES / "phase25d_cv_selected_epochs.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["fold", "best_epoch", "best_es_huber", "total_epochs", "termination"])
    for run in registry["runs"]:
        writer.writerow([run["fold"], run["best_epoch"], run["best_es_huber"], run["total_epochs"], run["termination"]])

# 4. OOF regression metrics
metrics = json.load(open(AUDITS / "phase25d_oof_metric_audit.json"))
with open(TABLES / "phase25d_oof_regression_metrics_overall.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["metric", "value"])
    for k, v in metrics["overall"].items():
        writer.writerow([k, v])

with open(TABLES / "phase25d_oof_regression_metrics_by_domain.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["domain", "huber", "mae", "rmse", "pearson", "spearman", "r2"])
    for d, vals in metrics["by_domain"].items():
        writer.writerow([d, vals["huber"], vals["mae"], vals["rmse"], vals["pearson"], vals["spearman"], vals["r2"]])

with open(TABLES / "phase25d_oof_regression_metrics_by_fold.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["fold", "huber", "mae", "rmse", "pearson", "spearman", "r2"])
    for fold, vals in metrics["by_fold"].items():
        writer.writerow([fold, vals["huber"], vals["mae"], vals["rmse"], vals["pearson"], vals["spearman"], vals["r2"]])

# 5. Secondary discrimination
disc = json.load(open(AUDITS / "phase25d_oof_secondary_discrimination.json"))
with open(TABLES / "phase25d_oof_secondary_discrimination_metrics.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["comparison", "roc_auc", "pr_auc"])
    writer.writerow(["beneficial_vs_rest", disc["beneficial_vs_rest"]["roc_auc"], disc["beneficial_vs_rest"]["pr_auc"]])
    writer.writerow(["harmful_vs_rest", disc["harmful_vs_rest"]["roc_auc"], disc["harmful_vs_rest"]["pr_auc"]])

# 6. Checkpoint inventory
with open(TABLES / "phase25d_checkpoint_inventory.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["fold", "best_checkpoint_path", "latest_checkpoint_path", "history_path", "closure_path"])
    for k in range(5):
        writer.writerow([
            k,
            str(CKPT / f"fold{k}" / "best.pt"),
            str(CKPT / f"fold{k}" / "latest.pt"),
            str(EXP / f"fold{k}" / "history.csv"),
            str(EXP / f"fold{k}" / "training_closure.json"),
        ])
    writer.writerow([
        "final",
        str(CKPT / "final" / "final.pt"),
        "",
        str(EXP / "final" / "history.csv"),
        "",
    ])

print("All Phase25D tables created.")
