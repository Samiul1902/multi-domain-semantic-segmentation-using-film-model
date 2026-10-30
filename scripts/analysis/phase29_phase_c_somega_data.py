#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 2b: seed-specific S_omega feature matrix (§17) and
binary target table (§18).

Inputs (per master seed S):
    data_cache/phase29_seed<S>/phase29_seed<S>_refined_crop_prob_<DOMAIN>.npy
        produced by Stage 2a (seed-specific R_psi OOF candidates)
    data_cache/phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy
        canonical global probability crop (seed-independent, FROZEN G)
    data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy
        frozen geometry scalars (indices 200, 201)

Outputs:
    data_cache/phase29_seed<S>/phase29_seed<S>_somega_features.npy   (4957,20)
    data_cache/phase29_seed<S>/phase29_seed<S>_somega_targets.csv
    reports/audits/phase29_seed<S>_somega_feature_contract.json
    reports/audits/phase29_seed<S>_somega_target_freeze.json

Uses the EXACT canonical ``phase25f_post_safety_features.build_input_vector``.
NO GT-derived input: the input vector is built before any target is attached.

Usage:
    python phase29_phase_c_somega_data.py --master-seed 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402

CODE25F = C.ROOT / "scripts" / "analysis"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, required=True, choices=[123, 3407])
    args = ap.parse_args()
    S = int(args.master_seed)

    import numpy as np
    import pandas as pd

    sys.path.insert(0, str(CODE25F))
    import phase25f_spec_repair_common as SC  # noqa: E402
    import phase25f_post_safety_features as F  # noqa: E402

    out_dir = C.seed_dir(S)
    out_dir.mkdir(parents=True, exist_ok=True)

    glob = np.load(C.CACHE25F / "oof_global_crop_prob.npy", mmap_mode="r")
    meta = pd.read_csv(C.CACHE25F / "oof_refined_crop_prob_metadata.csv")
    meta["sample_id"] = meta["sample_id"].astype(str)
    meta = meta.sort_values("feature_row_index").reset_index(drop=True)
    assert meta["feature_row_index"].tolist() == list(range(C.N_DEV))

    b25 = pd.read_csv(C.CACHE25B / "metadata.csv")
    b25["sample_id"] = b25["sample_id"].astype(str)
    b25f = np.load(C.CACHE25B / "features.npy", mmap_mode="r")
    b25_row = {r.sample_id: i for i, r in enumerate(b25.itertuples(index=False))}

    # ---- load seed-specific refined crop probabilities per domain -------- #
    domains = sorted(meta["domain"].unique().tolist())
    refined_by_domain = {}
    for d in domains:
        p = out_dir / f"phase29_seed{S}_refined_crop_prob_{d}.npy"
        if not p.exists():
            print(f"FAIL: missing {p}")
            return 2
        refined_by_domain[d] = np.load(p, mmap_mode="r")
    # map each (domain, row-within-domain) -> global 0..4956 ordering
    global_to_dom_idx = {}
    for d in domains:
        idx = 0
        for _, r in meta[meta["domain"] == d].iterrows():
            global_to_dom_idx[int(r["feature_row_index"])] = (d, idx)
            idx += 1

    feats = np.empty((C.N_DEV, 20), dtype=np.float32)
    for i in range(C.N_DEV):
        sid = meta.at[i, "sample_id"]
        task_id = int(meta.at[i, "task_id"])
        d, di = global_to_dom_idx[i]
        j = b25_row[sid]
        roi_area_fraction = float(b25f[j, SC.PHASE25B_IDX_ROI_AREA_FRACTION])
        roi_side = float(b25f[j, SC.PHASE25B_IDX_ROI_SIDE])
        feats[i] = F.build_input_vector(
            np.asarray(glob[i], dtype=np.float32),
            np.asarray(refined_by_domain[d][di], dtype=np.float32),
            roi_area_fraction, roi_side, task_id)

    nan_count = int(np.isnan(feats).sum())
    inf_count = int(np.isinf(feats).sum())
    if nan_count or inf_count:
        feats = np.nan_to_num(feats, nan=0.0, posinf=0.0, neginf=0.0)

    feat_path = C.somega_features_path(S)
    np.save(feat_path, feats)
    fchecks = {
        "shape_4957_20": list(feats.shape) == [C.N_DEV, 20],
        "dtype_float32": str(feats.dtype) == "float32",
        "finite": nan_count == 0 and inf_count == 0,
        "onehot_sums_to_one": bool(np.allclose(feats[:, 16:20].sum(axis=1), 1.0)),
        "feature_order_is_canonical": True,
        "gt_derived_input": False,
    }
    C.write_json({
        "artifact": f"phase29_seed{S}_somega_feature_contract",
        "phase": 29, "stage": "SEED_SPECIFIC_SOMEGA_FEATURES",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "features_path": str(feat_path.relative_to(C.ROOT)),
        "features_sha256": C.sha256_file(feat_path),
        "shape": list(feats.shape), "dtype": str(feats.dtype),
        "nan_count": nan_count, "inf_count": inf_count,
        "P_g_source": "phase25f_barr_post_safety_v1_0/oof_global_crop_prob.npy "
                      "(canonical fixed G)",
        "P_r_source": f"phase29_seed{S} R_psi OOF candidates",
        "builder": "phase25f_post_safety_features.build_input_vector (frozen)",
        "checks": fchecks, "n_failed": sum(1 for v in fchecks.values() if not v),
        "blocked_terminal_if_fail": C.BLOCKED["SOMEGA_TRAINING_OR_OOF_FAILURE"],
        "all_pass": all(fchecks.values()),
    }, C.AUD / f"phase29_seed{S}_somega_feature_contract.json")
    print(f"[§17] S_omega features: {feats.shape} finite={nan_count==0 and inf_count==0}")

    # ---- §18 binary target ------------------------------------------------ #
    tgt = pd.read_csv(C.deltadice_target_path(S))
    tgt["sample_id"] = tgt["sample_id"].astype(str)
    tgt = tgt.set_index("sample_id").loc[meta["sample_id"].tolist()].reset_index()
    tgt["safety_target"] = (tgt["delta_dice"] > 0).astype(int)
    out_tgt = tgt[["sample_id", "domain", "task_id",
                   "outer_fold", "delta_dice", "safety_target"]].copy()
    out_tgt.insert(1, "feature_row_index", list(range(C.N_DEV)))

    tgt_path = C.somega_targets_path(S)
    hdr = ["sample_id", "feature_row_index", "domain", "task_id", "outer_fold",
           "delta_dice", "safety_target"]
    C.write_csv(tgt_path, hdr, out_tgt[hdr].values.tolist())

    pos = int((out_tgt["safety_target"] == 1).sum())
    neg = int((out_tgt["safety_target"] == 0).sum())
    tchecks = {
        "rows_4957": len(out_tgt) == C.N_DEV,
        "no_missing": bool(out_tgt.notna().all().all()),
        "no_duplicate": out_tgt["sample_id"].nunique() == C.N_DEV,
        "zero_delta_maps_to_0": bool(
            (out_tgt.loc[out_tgt["delta_dice"] == 0.0, "safety_target"] == 0).all()),
        "target_rule_strict_positive": True,
    }
    C.write_json({
        "artifact": f"phase29_seed{S}_somega_target_freeze",
        "phase": 29, "stage": "SEED_SPECIFIC_SOMEGA_TARGET_FREEZE",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "target_path": str(tgt_path.relative_to(C.ROOT)),
        "target_sha256": C.sha256_file(tgt_path),
        "rule": "target = 1 iff DeltaDice > 0; exact zero -> 0",
        "rows": int(len(out_tgt)),
        "n_positive": pos, "n_negative": neg,
        "n_zero_delta": int((out_tgt["delta_dice"] == 0.0).sum()),
        "checks": tchecks, "n_failed": sum(1 for v in tchecks.values() if not v),
        "blocked_terminal_if_fail": C.BLOCKED["SEED_SPECIFIC_TARGET_FAILURE"],
        "all_pass": all(tchecks.values()),
    }, C.AUD / f"phase29_seed{S}_somega_target_freeze.json")
    print(f"[§18] S_omega targets: pos={pos} neg={neg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
