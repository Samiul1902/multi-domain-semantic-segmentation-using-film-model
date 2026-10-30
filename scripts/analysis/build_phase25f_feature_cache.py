"""Phase 25F — POST-SAFETY SPECIFICATION REPAIR  §8 / §9.

§8 materialise the 20-D GT-free S_omega feature cache:
      features.npy (4957x20 float32) + metadata.csv + feature_schema.csv
§9 build the cache independently 3 times and require byte-identical SHAs.

The feature cache is built BEFORE any target label. Feature construction never
inspects DeltaDice / gain category / global Dice / candidate Dice.

No model construction / training / forward pass / refinement / DeltaDice.

Outputs (canonical):
  data_cache/phase25f_barr_post_safety_v1_0/features.npy
  data_cache/phase25f_barr_post_safety_v1_0/metadata.csv
  data_cache/phase25f_barr_post_safety_v1_0/feature_schema.csv
  reports/audits/phase25f_feature_cache_contract_v1_0.json
  reports/audits/phase25f_feature_cache_determinism.json
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT / "scripts" / "analysis"))
import phase25f_spec_repair_common as C  # noqa: E402
import phase25f_post_safety_features as F  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


def _schema_df() -> pd.DataFrame:
    rows = []
    for idx, name, formula, source, units, norm in F.NUMERIC_FEATURES:
        rows.append({"feature_index": idx, "name": name, "formula": formula,
                     "source": source, "dtype": "float32", "units": units,
                     "normalization_role": norm, "GT_free": True, "group": "numeric"})
    for idx, name, formula in F.ONEHOT_FEATURES:
        rows.append({"feature_index": idx, "name": name, "formula": formula,
                     "source": "frozen Phase25C label table task_id "
                               "(ISIC=0, BUSI=1, KVASIR=2, KUB=3)",
                     "dtype": "float32", "units": "one-hot indicator in {0,1}",
                     "normalization_role": "NONE", "GT_free": True, "group": "task_onehot"})
    return pd.DataFrame(rows)


def build(out_dir: Path) -> dict:
    """Build the cache into out_dir. Returns SHA + verification info."""
    out_dir.mkdir(parents=True, exist_ok=True)

    refined = np.load(C.CACHE25F / "oof_refined_crop_prob.npy", mmap_mode="r")
    glob = np.load(C.CACHE25F / "oof_global_crop_prob.npy", mmap_mode="r")
    meta = pd.read_csv(C.CACHE25F / "oof_refined_crop_prob_metadata.csv")
    meta["sample_id"] = meta["sample_id"].astype(str)
    meta = meta.sort_values("feature_row_index").reset_index(drop=True)
    assert meta["feature_row_index"].tolist() == list(range(4957))

    b25 = pd.read_csv(C.PHASE25B_METADATA)
    b25["sample_id"] = b25["sample_id"].astype(str)
    b25f = np.load(C.PHASE25B_FEATURES, mmap_mode="r")
    b25_by_sid = {r.sample_id: int(r.feature_row_index)
                  for r in b25.itertuples(index=False)}
    b25_row = {r.sample_id: i for i, r in enumerate(b25.itertuples(index=False))}

    feats = np.empty((4957, 20), dtype=np.float32)
    for i in range(4957):
        sid = meta.at[i, "sample_id"]
        task_id = int(meta.at[i, "task_id"])
        j = b25_row[sid]
        roi_area_fraction = float(b25f[j, C.PHASE25B_IDX_ROI_AREA_FRACTION])
        roi_side = float(b25f[j, C.PHASE25B_IDX_ROI_SIDE])
        feats[i] = F.build_input_vector(
            np.asarray(glob[i], dtype=np.float32),
            np.asarray(refined[i], dtype=np.float32),
            roi_area_fraction, roi_side, task_id)

    nan_count = int(np.isnan(feats).sum())
    inf_count = int(np.isinf(feats).sum())
    if nan_count or inf_count:
        feats = np.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)

    np.save(out_dir / "features.npy", feats)
    meta_out = meta[["sample_id", "feature_row_index", "domain", "task_id",
                     "phase25c_outer_fold", "action_available"]].copy()
    (out_dir / "metadata.csv").write_text(C.csv_text(meta_out), encoding="utf-8", newline="")
    (out_dir / "feature_schema.csv").write_text(C.csv_text(_schema_df()),
                                                encoding="utf-8", newline="")

    return {
        "features_sha256": C.sha256_file(out_dir / "features.npy"),
        "metadata_sha256": C.sha256_file(out_dir / "metadata.csv"),
        "schema_sha256": C.sha256_file(out_dir / "feature_schema.csv"),
        "shape": list(feats.shape),
        "dtype": str(feats.dtype),
        "nan_count": nan_count,
        "inf_count": inf_count,
        "sample_ids_exact": set(meta_out["sample_id"]) == set(b25_by_sid.keys()),
        "feature_row_index_0_to_4956": meta_out["feature_row_index"].tolist() == list(range(4957)),
        "onehot_dims_sum_to_one": bool(np.allclose(feats[:, 16:20].sum(axis=1), 1.0)),
        "feature_min": float(feats.min()),
        "feature_max": float(feats.max()),
    }


def main() -> int:
    # ---- §9: 3 independent builds ------------------------------------------ #
    det_root = C.CACHE25F / "_det"
    if det_root.exists():
        shutil.rmtree(det_root)
    runs = []
    for r in (1, 2, 3):
        runs.append(build(det_root / f"run{r}"))

    feats_shas = [x["features_sha256"] for x in runs]
    meta_shas = [x["metadata_sha256"] for x in runs]
    schema_shas = [x["schema_sha256"] for x in runs]
    three_x = (len(set(feats_shas)) == 1 and len(set(meta_shas)) == 1
               and len(set(schema_shas)) == 1)

    # ---- canonical copy ----------------------------------------------------- #
    for name in ("features.npy", "metadata.csv", "feature_schema.csv"):
        shutil.copyfile(det_root / "run1" / name, C.CACHE25F / name)
    shutil.rmtree(det_root)

    info = runs[0]
    canon = {
        "features.npy": C.bind(C.CACHE25F / "features.npy"),
        "metadata.csv": C.bind(C.CACHE25F / "metadata.csv"),
        "feature_schema.csv": C.bind(C.CACHE25F / "feature_schema.csv"),
    }

    # ---- feature-cache contract (§8) --------------------------------------- #
    contract = {
        "artifact": "phase25f_feature_cache_contract_v1_0",
        "phase": "25F",
        "stage": "MATERIALIZE_20D_GT_FREE_FEATURE_CACHE",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "cache_root": "data_cache/phase25f_barr_post_safety_v1_0",
        "features_shape": [4957, 20],
        "features_dtype": "float32",
        "rows": 4957,
        "feature_row_index_range": [0, 4956],
        "nan_count": info["nan_count"],
        "inf_count": info["inf_count"],
        "all_sample_ids_exact": info["sample_ids_exact"],
        "onehot_dims_are_valid_one_hot": info["onehot_dims_sum_to_one"],
        "feature_value_range_observed": [info["feature_min"], info["feature_max"]],
        "feature_schema_fields": ["feature_index", "name", "formula", "source",
                                  "dtype", "units", "normalization_role", "GT_free"],
        "built_before_targets": True,
        "construction_never_inspected": ["DeltaDice", "gain category",
                                         "global Dice", "candidate Dice"],
        "inputs_used": {
            "P_g": "data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy",
            "P_r": "data_cache/phase25f_barr_post_safety_v1_0/oof_refined_crop_prob.npy",
            "roi_area_fraction": "data_cache/phase25b_barr_pre_refinement_features_v1_2 "
                                 "(scalar index 200)",
            "roi_side": "data_cache/phase25b_barr_pre_refinement_features_v1_2 "
                        "(scalar index 201)",
            "task_id": "data_cache/phase25f_barr_post_safety_v1_0/"
                       "oof_refined_crop_prob_metadata.csv",
        },
        "canonical_artifacts": canon,
        "feature_equation_contract": C.bind(C.AUD / "phase25f_feature_equation_contract_v1_0.json"),
        "model_forwards": 0,
        "test_reads": 0,
        "all_pass": bool(info["sample_ids_exact"] and info["onehot_dims_sum_to_one"]
                         and info["feature_row_index_0_to_4956"]),
    }
    C.jdump(contract, C.AUD / "phase25f_feature_cache_contract_v1_0.json")

    # ---- determinism audit (§9) -------------------------------------------- #
    det = {
        "artifact": "phase25f_feature_cache_determinism",
        "phase": "25F",
        "stage": "FEATURE_CACHE_3X_DETERMINISM",
        "method": C.METHOD,
        "specification_revision": C.REVISION,
        "builds": 3,
        "features_npy_sha256": feats_shas,
        "metadata_sha256": meta_shas,
        "feature_schema_sha256": schema_shas,
        "features_3x_identical": len(set(feats_shas)) == 1,
        "metadata_3x_identical": len(set(meta_shas)) == 1,
        "schema_3x_identical": len(set(schema_shas)) == 1,
        "three_times_byte_identical": three_x,
        "canonical_features_sha256": canon["features.npy"]["sha256"],
        "canonical_metadata_sha256": canon["metadata.csv"]["sha256"],
        "canonical_schema_sha256": canon["feature_schema.csv"]["sha256"],
        "canonical_matches_run1": (
            canon["features.npy"]["sha256"] == feats_shas[0]
            and canon["metadata.csv"]["sha256"] == meta_shas[0]
            and canon["feature_schema.csv"]["sha256"] == schema_shas[0]),
        "model_forwards": 0,
        "test_reads": 0,
        "all_pass": three_x,
    }
    C.jdump(det, C.AUD / "phase25f_feature_cache_determinism.json")

    print("features sha:", feats_shas[0])
    print("3x identical:", three_x, "| nan:", info["nan_count"], "inf:", info["inf_count"])
    print("shape:", info["shape"], "range:", info["feature_min"], info["feature_max"])
    return 0 if three_x else 1


if __name__ == "__main__":
    raise SystemExit(main())
