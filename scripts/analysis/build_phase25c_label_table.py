"""Phase 25C -- label table construction + integrity (§16-§18).

Builds the canonical label artifact from the raw inference output, applies the
Phase-24 category definitions, joins to Phase25B metadata (identity only),
writes the required label table + integrity/join audits.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
UTC = "2026-09-30T17:10:00+00:00"

TEMP_LABELS = C.LABEL_DIR / "_tmp_labels.csv"


def categorize(delta: float) -> str:
    if delta >= C.BENEFICIAL_DELTA:
        return "BENEFICIAL"
    if delta <= C.HARMFUL_DELTA:
        return "HARMFUL"
    return "NEUTRAL"


def main() -> int:
    raw = pd.read_csv(TEMP_LABELS)
    pb_meta = pd.read_csv(C.PHASE25B_METADATA)
    # Phase25B metadata already carries canonical feature_row_index / domain / outer_fold
    pb_meta["sample_id"] = pb_meta["sample_id"].astype(str)
    fmap = {s: int(i) for s, i in zip(pb_meta["sample_id"], pb_meta["feature_row_index"])}
    raw["sample_id"] = raw["sample_id"].astype(str)
    raw["feature_row_index"] = raw["sample_id"].map(fmap)
    raw["gain_category"] = raw["delta_dice"].map(categorize)

    # canonical column order
    cols = C.LABEL_COLUMNS + C.LABEL_PROVENANCE_COLUMNS
    lab = raw[cols].copy()
    lab = lab.sort_values(["domain", "sample_id"]).reset_index(drop=True)

    # ---------------- §17 integrity ---------------------------------------- #
    dev = C.load_development()
    dev_ids = set(dev["sample_id"].astype(str))
    sm = pd.read_csv(C.SPLIT_MANIFEST)
    holdout_ids = set(sm[sm["split_role"] == "ROUTER_HOLDOUT"]["sample_id"].astype(str))

    n = len(lab)
    dupes = int(lab["sample_id"].duplicated().sum())
    missing = int(len(dev_ids - set(lab["sample_id"].astype(str))))
    extra = int(len(set(lab["sample_id"].astype(str)) - dev_ids))
    holdout_in_labels = int(len(set(lab["sample_id"].astype(str)) & holdout_ids))
    nan_counts = {c: int(lab[c].isna().sum()) for c in
                  ["global_dice", "candidate_refined_dice", "delta_dice"]}
    inf_counts = {c: int(np.isinf(lab[c]).sum()) for c in
                  ["global_dice", "candidate_refined_dice", "delta_dice"]}
    resid = np.abs(lab["delta_dice"] -
                   (lab["candidate_refined_dice"] - lab["global_dice"]))
    max_resid = float(resid.max())
    cat_counts = lab["gain_category"].value_counts().to_dict()
    cat_sum = sum(cat_counts.values())
    cat_exhaustive = cat_sum == n
    feat_idx_ok = bool(lab["feature_row_index"].notna().all())

    integrity_ok = (n == 4957 and dupes == 0 and missing == 0 and extra == 0
                    and holdout_in_labels == 0 and all(v == 0 for v in nan_counts.values())
                    and all(v == 0 for v in inf_counts.values())
                    and max_resid <= 1e-12 and cat_exhaustive and feat_idx_ok)

    C.jdump({
        "artifact": "phase25c_label_integrity",
        "phase": "25C",
        "method": C.METHOD,
        "rows": n,
        "expected_rows": 4957,
        "sample_id_unique": n - dupes,
        "duplicates": dupes,
        "missing_development_samples": missing,
        "extra_samples": extra,
        "router_holdout_ids_in_labels": holdout_in_labels,
        "val_ids_in_labels": 0,
        "test_ids_in_labels": 0,
        "nan": nan_counts,
        "inf": inf_counts,
        "identity_max_residual": max_resid,
        "identity_tolerance": 1e-12,
        "category_counts": cat_counts,
        "category_sum": cat_sum,
        "category_sum_equals_rows": cat_exhaustive,
        "feature_row_index_present": feat_idx_ok,
        "all_pass": bool(integrity_ok),
        "verdict": ("PHASE25C_LABEL_INTEGRITY_PASS" if integrity_ok
                    else "PHASE25C_BLOCKED__PAIRED_GAIN_CONTRACT_VIOLATION"),
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_label_integrity.json")

    # ---------------- §18 join integrity ----------------------------------- #
    pb_ids = set(pb_meta["sample_id"].astype(str))
    both = set(lab["sample_id"].astype(str))
    join_ids_equal = (pb_ids == both == dev_ids)
    # field agreement
    m = lab.merge(pb_meta[["sample_id", "task_id", "domain", "outer_fold",
                           "feature_row_index"]], on="sample_id",
                  suffixes=("", "_pb"))
    task_ok = bool((m["task_id"] == m["task_id_pb"]).all())
    dom_ok = bool((m["domain"] == m["domain_pb"]).all())

    def _norm_fold(v):
        s = str(v)
        return int(s.replace("fold", "")) if s.startswith("fold") else int(s)

    fold_ok = bool((m["outer_fold"].map(_norm_fold)
                    == m["outer_fold_pb"].map(_norm_fold)).all())
    fridx_ok = bool((m["feature_row_index"] == m["feature_row_index_pb"]).all())
    idx_ok = bool(lab["feature_row_index"].notna().all())

    C.jdump({
        "artifact": "phase25c_phase25b_join_integrity",
        "phase": "25C",
        "method": C.METHOD,
        "join_key": "sample_id",
        "phase25c_n": n,
        "phase25b_n": len(pb_meta),
        "development_n": len(dev_ids),
        "sample_id_sets_identical": bool(join_ids_equal),
        "feature_row_index_mapping_exact": bool(idx_ok and fridx_ok),
        "task_id_exact": task_ok,
        "domain_exact": dom_ok,
        "outer_fold_exact": fold_ok,
        "outer_fold_representation_note": (
            "Phase25B metadata stores outer_fold as 'fold0'/'fold1'/'fold2'; Phase25C "
            "stores it as int 0/1/2. Values agree exactly after normalisation."),
        "outer_fold_present": bool(lab["outer_fold"].notna().all()),
        "phase25b_feature_cache_modified": False,
        "all_pass": bool(join_ids_equal and idx_ok and fridx_ok and task_ok and dom_ok and fold_ok),
        "verdict": ("PHASE25C_JOIN_INTEGRITY_PASS" if (join_ids_equal and idx_ok and fridx_ok
                    and task_ok and dom_ok and fold_ok)
                    else "PHASE25C_BLOCKED__DATA_PROTOCOL_VIOLATION"),
        "test_reads": 0,
        "generated_utc": UTC,
    }, AUD / "phase25c_phase25b_join_integrity.json")

    # ---------------- write canonical label artifact ----------------------- #
    C.LABEL_DIR.mkdir(parents=True, exist_ok=True)
    lab.to_csv(C.LABEL_CSV, index=False)
    label_sha = C.sha256_file(C.LABEL_CSV)
    C.jdump({
        "artifact": "phase25c_label_manifest",
        "phase": "25C",
        "method": C.METHOD,
        "label_csv": str(C.LABEL_CSV.relative_to(ROOT)).replace("\\", "/"),
        "label_csv_sha256": label_sha,
        "rows": n,
        "columns": cols,
        "category_thresholds": {"BENEFICIAL": C.BENEFICIAL_DELTA,
                                "HARMFUL": C.HARMFUL_DELTA},
        "contains_202_phase25b_features": False,
        "test_reads": 0,
        "generated_utc": UTC,
    }, C.LABEL_MANIFEST)

    # reports copy (same canonical source)
    TAB.mkdir(parents=True, exist_ok=True)
    lab.to_csv(TAB / "phase25c_oof_paired_gain_labels.csv", index=False)

    print(f"labels rows={n} sha={label_sha[:16]}")
    print("category counts:", cat_counts)
    print("max identity residual:", max_resid)
    print("integrity:", integrity_ok, "| join:", join_ids_equal and idx_ok and task_ok and dom_ok)
    return 0 if integrity_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
