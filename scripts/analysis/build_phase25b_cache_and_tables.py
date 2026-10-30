"""Phase 25B -- build the canonical feature cache metadata/schema/manifest and
the required tables from the frozen feature matrix.  Pure post-processing: reads
the cache, writes tables + audits.  No model, no forward, no GT.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.features.barr_pre_refinement_features import (  # noqa: E402
    FEATURE_GRID,
    GROUP_ORDER,
    NATIVE_CHANNELS,
    NUMERIC_DIM,
    REDUCTION_K,
    REDUCTION_OP,
    SCALAR_ORDER,
    TAPS,
    feature_group_offsets,
    feature_schema,
    scalar_definitions,
)

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
UTC = datetime.now(timezone.utc).isoformat()


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main() -> int:
    feats = np.load(CACHE / "features.npy")
    assert feats.shape == (4957, NUMERIC_DIM), feats.shape
    assert feats.dtype == np.float32, feats.dtype

    # ---- metadata.csv (built from the frozen per-domain meta + fold files)
    fold_of = {}
    for s in ("fold0", "fold1", "fold2"):
        for r in csv.DictReader(open(ROI030 / "folds" / f"{s}_outer_target.csv",
                                     newline="", encoding="utf-8")):
            fold_of[r["sample_id"]] = s

    rows = []
    for dom in ("BUSI", "ISIC", "KUB", "KVASIR"):
        for r in csv.DictReader(open(ROI030 / dom / "meta.csv", newline="",
                                     encoding="utf-8")):
            rows.append({
                "feature_row_index": "",
                "sample_id": r["sample_id"],
                "task_id": int(r["task_id"]),
                "domain": dom,
                "outer_fold": fold_of.get(r["sample_id"], ""),
                "action_available": int(str(r["action_available"]).strip().lower()
                                        in ("1", "true")),
                "predicted_roi_side": float(r["crop_side_pixels"]),
            })
    meta = pd.DataFrame(rows).sort_values(["domain", "sample_id"]).reset_index(drop=True)
    meta["feature_row_index"] = np.arange(len(meta), dtype=int)
    assert len(meta) == 4957, len(meta)
    meta.to_csv(CACHE / "metadata.csv", index=False, lineterminator="\n")

    # ---- feature_schema.csv
    schema = pd.DataFrame(feature_schema())
    schema.to_csv(CACHE / "feature_schema.csv", index=False, lineterminator="\n")
    schema.to_csv(TAB / "phase25b_feature_schema.csv", index=False, lineterminator="\n")

    # ---- feature_group_offsets.json
    (CACHE / "feature_group_offsets.json").write_text(
        json.dumps(feature_group_offsets(), indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- scalar definitions table
    pd.DataFrame(scalar_definitions()).to_csv(
        TAB / "phase25b_scalar_feature_definitions.csv", index=False, lineterminator="\n")

    # ---- summary statistics
    names = [r["feature_name"] for r in feature_schema()]
    df = pd.DataFrame(feats, columns=names)
    stats = []
    for c in names:
        v = df[c].to_numpy(dtype=np.float64)
        stats.append({
            "feature_name": c, "mean": v.mean(), "std": v.std(ddof=1),
            "min": v.min(), "max": v.max(), "median": np.median(v),
            "p01": np.percentile(v, 1), "p05": np.percentile(v, 5),
            "p95": np.percentile(v, 95), "p99": np.percentile(v, 99),
        })
    pd.DataFrame(stats).to_csv(TAB / "phase25b_feature_summary_statistics.csv",
                               index=False, lineterminator="\n")

    # ---- by-domain summary (per scalar + per group mean/std)
    bydom = []
    for dom, sub in df.groupby(meta["domain"].to_numpy()):
        idx = np.where(meta["domain"].to_numpy() == dom)[0]
        for gname, tap, scope, start in GROUP_ORDER:
            block = feats[idx, start:start + REDUCTION_K].astype(np.float64)
            bydom.append({"domain": dom, "n": len(idx), "feature_group": gname,
                          "mean": block.mean(), "std": block.std(ddof=1),
                          "min": block.min(), "max": block.max(),
                          "p05": np.percentile(block, 5), "p95": np.percentile(block, 95)})
    pd.DataFrame(bydom).to_csv(TAB / "phase25b_feature_summary_by_domain.csv",
                               index=False, lineterminator="\n")

    # ---- feature group summary
    gs = []
    for gname, tap, scope, start in GROUP_ORDER:
        block = feats[:, start:start + REDUCTION_K].astype(np.float64)
        norms = np.linalg.norm(block, axis=1)
        gs.append({"feature_group": gname, "source_tap": tap, "scope": scope,
                   "start": start, "dim": REDUCTION_K,
                   "native_channels": NATIVE_CHANNELS[tap],
                   "feature_grid": FEATURE_GRID[tap],
                   "reduction_op": REDUCTION_OP,
                   "mean": block.mean(), "std": block.std(ddof=1),
                   "l2_norm_mean": norms.mean(), "l2_norm_std": norms.std(ddof=1)})
    pd.DataFrame(gs).to_csv(TAB / "phase25b_feature_group_summary.csv",
                            index=False, lineterminator="\n")

    # ---- extraction population
    pop = meta.groupby(["domain"]).size().reset_index(name="n")
    pop.loc[len(pop)] = ["TOTAL", int(len(meta))]
    pop.to_csv(TAB / "phase25b_extraction_population.csv", index=False, lineterminator="\n")

    # ---- cache inventory
    inv = []
    for f in sorted(CACHE.rglob("*")):
        if f.is_file():
            inv.append({"artifact": str(f.relative_to(ROOT)).replace("\\", "/"),
                        "bytes": f.stat().st_size, "sha256": sha(f)})
    pd.DataFrame(inv).to_csv(TAB / "phase25b_feature_cache_inventory.csv",
                             index=False, lineterminator="\n")

    # ---- cache manifest
    manifest = {
        "artifact": "phase25b_feature_cache_manifest",
        "phase": "25B",
        "classification": "CANONICAL_PHASE25B_GT_FREE_FEATURES",
        "method": "RA-MedFiLM-BARR",
        "feature_spec_revision": "ra_medfilm_barr_narrowed_v1_2",
        "population": "ROUTER_DEVELOPMENT only",
        "population_n": 4957,
        "matrix_shape": [4957, NUMERIC_DIM],
        "matrix_dtype": "float32",
        "deep_dim": 192, "scalar_dim": 10, "numeric_dim": NUMERIC_DIM,
        "task_id_persisted": True,
        "task_embedding_generated": False,
        "feature_spec_reduction_op": REDUCTION_OP,
        "threshold_semantics": {"ROI_PROPOSAL": 0.30, "SEGMENTATION_OUTPUT": 0.50},
        "phase24_notebook_sha256":
            "9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027",
        "phase21_global_checkpoint_sha256":
            "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7",
        "phase25a_roi030_cache_manifest_sha256": sha(ROI030 / "cache_manifest.json"),
        "split_manifest_sha256":
            "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555",
        "feature_matrix_sha256": sha(CACHE / "features.npy"),
        "metadata_sha256": sha(CACHE / "metadata.csv"),
        "schema_sha256": sha(CACHE / "feature_schema.csv"),
        "source_code_sha256":
            sha(ROOT / "src/features/barr_pre_refinement_features.py"),
        "extraction_driver_sha256":
            sha(ROOT / "scripts/analysis/run_phase25b_feature_extraction.py"),
        "contains_gt_derived_features": False,
        "contains_post_refinement_features": False,
        "contains_refiner_features": False,
        "router_holdout_feature_rows": 0,
        "val_feature_rows": 0,
        "test_reads": 0,
        "generated_utc": UTC,
    }
    (CACHE / "cache_manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")

    # ---- extraction provenance
    prov = {
        "artifact": "phase25b_extraction_provenance",
        "phase": "25B",
        "device": "cuda:0",
        "amp": True,
        "forward_path": "no_grad + torch.amp.autocast (identical to canonical Phase25A)",
        "batch_size": 8,
        "global_forward_replay_count": 4957,
        "global_model_eval": True,
        "global_model_requires_grad_false": True,
        "hook_lifecycle": "registered per batch, removed in finally block",
        "regional_refiner_forward_passes": 0,
        "benefit_router_instantiated": False,
        "benefit_router_training_runs": 0,
        "benefit_router_inference_runs": 0,
        "post_safety_instantiated": False,
        "post_safety_training_runs": 0,
        "post_safety_inference_runs": 0,
        "DeltaDice_computed": False,
        "paired_gain_labels_generated": False,
        "gt_derived_features": 0,
        "generated_utc": UTC,
    }
    (CACHE / "extraction_provenance.json").write_text(
        json.dumps(prov, indent=1, ensure_ascii=False), encoding="utf-8")

    print("cache manifest + provenance written")
    print("matrix", feats.shape, feats.dtype)
    return 0


if __name__ == "__main__":
    sys.exit(main())
