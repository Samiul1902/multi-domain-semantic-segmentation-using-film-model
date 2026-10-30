"""
Materialize Phase25D 5-fold outer + 10-fold inner nested CV manifests.
Identity metadata ONLY — no feature or label inspection.
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

ROOT = Path("D:/Softfors/jup")
SPLIT_MANIFEST = ROOT / "reports/audits/phase24_router_split_manifest.csv"
OUTDIR_TABLES = ROOT / "reports/tables"
OUTDIR_AUDITS = ROOT / "reports/audits"
OUTDIR_TABLES.mkdir(parents=True, exist_ok=True)
OUTDIR_AUDITS.mkdir(parents=True, exist_ok=True)

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

# ------------------------------------------------------------------
# 1. Load ROUTER_DEVELOPMENT identity rows
# ------------------------------------------------------------------
rows = []
with open(SPLIT_MANIFEST, "r", newline="") as f:
    reader = csv.DictReader(f)
    for r in reader:
        if r["split_role"] == "ROUTER_DEVELOPMENT":
            rows.append(r)

assert len(rows) == 4957, f"Expected 4957 ROUTER_DEVELOPMENT rows, got {len(rows)}"

# Sort deterministically by domain, group_key, sample_id
rows.sort(key=lambda r: (r["dataset"], r["group_key"], r["sample_id"]))

sample_ids = [r["sample_id"] for r in rows]
domains = np.array([r["dataset"] for r in rows])
group_keys = np.array([r["group_key"] for r in rows])

# Dummy X (row indices only)
X = np.arange(len(rows))

# ------------------------------------------------------------------
# 2. Outer 5-fold StratifiedGroupKFold
# ------------------------------------------------------------------
outer_cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
outer_folds = {}
for fold_idx, (source_idx, target_idx) in enumerate(outer_cv.split(X, domains, group_keys)):
    outer_folds[fold_idx] = {
        "source_idx": source_idx.tolist(),
        "target_idx": target_idx.tolist(),
    }

# Verify: each sample exactly once as target
all_target_idx = set()
for fold_idx in range(5):
    all_target_idx.update(outer_folds[fold_idx]["target_idx"])
assert all_target_idx == set(range(4957)), "Outer target indices must cover all 4957 samples exactly once"

# Verify: no group straddles outer folds
for fold_idx in range(5):
    target_groups = set(group_keys[outer_folds[fold_idx]["target_idx"]])
    for other_fold in range(5):
        if other_fold == fold_idx:
            continue
        other_target_groups = set(group_keys[outer_folds[other_fold]["target_idx"]])
        overlap = target_groups & other_target_groups
        assert len(overlap) == 0, f"Group straddles outer folds {fold_idx} and {other_fold}: {overlap}"

# ------------------------------------------------------------------
# 3. Inner 10-fold StratifiedGroupKFold per outer fold
# ------------------------------------------------------------------
inner_folds = {}
for fold_idx in range(5):
    source_idx = np.array(outer_folds[fold_idx]["source_idx"])
    source_domains = domains[source_idx]
    source_groups = group_keys[source_idx]
    source_X = np.arange(len(source_idx))

    inner_cv = StratifiedGroupKFold(n_splits=10, shuffle=True, random_state=4200 + fold_idx)
    inner_splits = list(inner_cv.split(source_X, source_domains, source_groups))

    # inner fold 0 = EARLY_STOP, inner folds 1-9 = FIT
    early_stop_source_idx = source_idx[inner_splits[0][1]].tolist()
    fit_source_idx = []
    for i in range(1, 10):
        fit_source_idx.extend(source_idx[inner_splits[i][1]].tolist())

    inner_folds[fold_idx] = {
        "fit_idx": fit_source_idx,
        "early_stop_idx": early_stop_source_idx,
    }

    # Verify: no group straddles FIT / EARLY_STOP
    fit_groups = set(group_keys[fit_source_idx])
    es_groups = set(group_keys[early_stop_source_idx])
    overlap = fit_groups & es_groups
    assert len(overlap) == 0, f"Group straddles FIT/ES in outer fold {fold_idx}: {overlap}"

    # Verify: no overlap with outer target
    target_idx_set = set(outer_folds[fold_idx]["target_idx"])
    fit_set = set(fit_source_idx)
    es_set = set(early_stop_source_idx)
    assert len(target_idx_set & fit_set) == 0, f"FIT overlaps outer target in fold {fold_idx}"
    assert len(target_idx_set & es_set) == 0, f"EARLY_STOP overlaps outer target in fold {fold_idx}"
    assert len(fit_set & es_set) == 0, f"FIT overlaps EARLY_STOP in fold {fold_idx}"

# ------------------------------------------------------------------
# 4. Materialize main CV5 manifest
# ------------------------------------------------------------------
cv_manifest_path = OUTDIR_TABLES / "phase25d_cv5_manifest.csv"
with open(cv_manifest_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["sample_id", "dataset", "task_id", "group_key", "router_cv_fold"])
    for fold_idx in range(5):
        for idx in outer_folds[fold_idx]["target_idx"]:
            r = rows[idx]
            writer.writerow([r["sample_id"], r["dataset"], r["task_id"], r["group_key"], fold_idx])

cv_manifest_sha = sha256_file(cv_manifest_path)

# ------------------------------------------------------------------
# 5. Materialize per-fold identity split manifests
# ------------------------------------------------------------------
per_fold_shas = {}
for fold_idx in range(5):
    # FIT
    fit_path = OUTDIR_TABLES / f"phase25d_cv_fold{fold_idx}_fit_ids.csv"
    with open(fit_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "dataset", "task_id", "group_key"])
        for idx in inner_folds[fold_idx]["fit_idx"]:
            r = rows[idx]
            writer.writerow([r["sample_id"], r["dataset"], r["task_id"], r["group_key"]])
    per_fold_shas[f"fold{fold_idx}_fit"] = sha256_file(fit_path)

    # EARLY_STOP
    es_path = OUTDIR_TABLES / f"phase25d_cv_fold{fold_idx}_early_stop_ids.csv"
    with open(es_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "dataset", "task_id", "group_key"])
        for idx in inner_folds[fold_idx]["early_stop_idx"]:
            r = rows[idx]
            writer.writerow([r["sample_id"], r["dataset"], r["task_id"], r["group_key"]])
    per_fold_shas[f"fold{fold_idx}_early_stop"] = sha256_file(es_path)

    # OUTER_TARGET
    ot_path = OUTDIR_TABLES / f"phase25d_cv_fold{fold_idx}_outer_target_ids.csv"
    with open(ot_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["sample_id", "dataset", "task_id", "group_key"])
        for idx in outer_folds[fold_idx]["target_idx"]:
            r = rows[idx]
            writer.writerow([r["sample_id"], r["dataset"], r["task_id"], r["group_key"]])
    per_fold_shas[f"fold{fold_idx}_outer_target"] = sha256_file(ot_path)

# ------------------------------------------------------------------
# 6. Fold statistics
# ------------------------------------------------------------------
fold_stats = []
for fold_idx in range(5):
    target_idx = outer_folds[fold_idx]["target_idx"]
    fit_idx = inner_folds[fold_idx]["fit_idx"]
    es_idx = inner_folds[fold_idx]["early_stop_idx"]
    fold_stats.append({
        "outer_fold": fold_idx,
        "outer_target_n": len(target_idx),
        "fit_n": len(fit_idx),
        "early_stop_n": len(es_idx),
        "source_n": len(fit_idx) + len(es_idx),
        "outer_target_domains": {d: int((domains[target_idx] == d).sum()) for d in np.unique(domains[target_idx])},
        "fit_domains": {d: int((domains[fit_idx] == d).sum()) for d in np.unique(domains[fit_idx])},
        "early_stop_domains": {d: int((domains[es_idx] == d).sum()) for d in np.unique(domains[es_idx])},
    })

# ------------------------------------------------------------------
# 7. Write nested CV split contract
# ------------------------------------------------------------------
nested_contract = {
    "artifact": "phase25d_nested_cv_split_contract_v1_2_1",
    "phase": "25D",
    "classification": "PRE_EXECUTION_SPECIFICATION_COMPLETENESS_REPAIR",
    "router_training_spec_revision": "ra_medfilm_barr_router_training_v1_2_1",
    "outer_cv_name": "BARR_ROUTER_CV5_GROUP_SAFE_DOMAIN_STRATIFIED_V1",
    "outer_cv_algorithm": "sklearn.model_selection.StratifiedGroupKFold",
    "outer_cv_params": {
        "n_splits": 5,
        "shuffle": True,
        "random_state": 42
    },
    "outer_cv_group_key": "canonical composite group_key from phase24_router_split_manifest.csv",
    "outer_cv_stratification": "domain only",
    "sort_before_split": ["domain", "group_key", "sample_id"],
    "inner_cv_algorithm": "sklearn.model_selection.StratifiedGroupKFold",
    "inner_cv_params": {
        "n_splits": 10,
        "shuffle": True,
        "random_state_per_fold": "4200 + outer_fold_index"
    },
    "inner_split_rule": "inner fold index 0 = EARLY_STOP_k; inner folds 1-9 = FIT_k",
    "inner_fitting_fraction_approx": 0.90,
    "inner_early_stop_fraction_approx": 0.10,
    "population": "ROUTER_DEVELOPMENT only (n=4957)",
    "library_versions": {
        "python": "3.11.9",
        "numpy": "2.4.6",
        "scikit-learn": "1.9.1"
    },
    "fold_statistics": fold_stats,
    "cv_manifest_path": str(cv_manifest_path.relative_to(ROOT)),
    "cv_manifest_sha256": cv_manifest_sha,
    "per_fold_manifest_shas": per_fold_shas,
    "audits": {
        "total_samples": 4957,
        "outer_target_coverage": "all 4957 samples exactly once",
        "outer_group_straddling": 0,
        "inner_group_straddling": 0,
        "fit_outer_target_overlap": 0,
        "early_stop_outer_target_overlap": 0,
        "fit_early_stop_overlap": 0
    },
    "generated_utc": "2026-10-01T02:01:22+00:00"
}

with open(OUTDIR_AUDITS / "phase25d_nested_cv_split_contract_v1_2_1.json", "w") as f:
    json.dump(nested_contract, f, indent=1)

print("CV5 manifest materialized.")
print(f"Main manifest: {cv_manifest_path} SHA {cv_manifest_sha}")
print("Fold stats:")
for s in fold_stats:
    print(f"  fold{s['outer_fold']}: target={s['outer_target_n']} fit={s['fit_n']} es={s['early_stop_n']}")
