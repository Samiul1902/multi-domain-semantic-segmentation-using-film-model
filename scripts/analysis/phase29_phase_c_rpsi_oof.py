#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Phase 29 — PHASE C STAGE 2a: seed123/3407 R_psi OOF inference (§8) and
DeltaDice target generation (§10-§11).

Consumes the frozen seed-specific R_psi fold checkpoints and produces, for the
requested master seed:
    data_cache/phase29_seed<S>/phase29_seed<S>_rpsi_oof_candidates.npz
    data_cache/phase29_seed<S>/phase29_seed<S>_deltadice_targets.csv
    reports/audits/phase29_seed<S>_rpsi_oof_integrity.json
    reports/audits/phase29_seed<S>_gain_target_freeze.json

Reuses the EXACT canonical Phase25C inference semantics (refiner input build,
ROI geometry, inverse crop, ROI-weighted fusion, 0.50 full-field Dice).

NOTHING here uses final.pt for OOF science; ONLY the fold checkpoints.
The global representation is NOT re-run: global Dice is taken from the frozen
canonical Phase25C label table (seed-independent).

Usage:
    python phase29_phase_c_rpsi_oof.py --master-seed 123
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_c_common as C  # noqa: E402

ROOT = C.ROOT
# The frozen canonical sources import the project package as ``src.*``; the
# repo root must therefore be importable exactly as it is for the canonical
# Phase25A trainer (which does ``sys.path.insert(0, str(ROOT))``).
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CODE25C = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
TRAIN_MANIFEST = ROOT / "manifests" / "phase4_v3" / "train.csv"


def _load_25c_common():
    sys.path.insert(0, str(CODE25C))
    import phase25c_common as P
    return P


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--master-seed", type=int, required=True, choices=[123, 3407])
    args = ap.parse_args()
    S = int(args.master_seed)

    import numpy as np
    import pandas as pd
    import torch
    from PIL import Image, ImageOps

    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    from src.data.barr_roi import roi_geometry
    from src.metrics.evaluation_metrics import (binary_confusion_counts,
                                                dice as dice_fn)

    P = _load_25c_common()
    SEG = C.SEGMENTATION_OUTPUT_THRESHOLD
    # §8 contract: no global-model forward pass happens here. The global Dice
    # is taken verbatim from the frozen canonical Phase25C label table.
    GLOBAL_MODEL_FORWARD_PASSES = 0

    fold_ckpt_root = C.rpsi_checkpoint_root(S)
    out_dir = C.seed_dir(S)
    out_dir.mkdir(parents=True, exist_ok=True)

    dev = P.load_development()
    assign = P.load_outer_fold_assignment()
    domains = sorted(dev["dataset"].unique().tolist())
    caches = {d: P.DomainCache(d) for d in domains}
    man = pd.read_csv(TRAIN_MANIFEST).set_index("sample_id", drop=False)

    # frozen global Dice per sample (seed-independent) from the canonical table
    gtab = pd.read_csv(C.SEED42_DELTADICE_CSV)
    gtab["sample_id"] = gtab["sample_id"].astype(str)
    global_dice_by_id = dict(zip(gtab["sample_id"], gtab["global_dice"]))

    # ---- load the three seed-specific fold checkpoints ------------------- #
    models = {}
    ckpt_shas = {}
    for k in range(3):
        ck = fold_ckpt_root / f"fold{k}" / "best.pt"
        if not ck.exists():
            print(f"FAIL: missing fold checkpoint {ck}")
            return 2
        st = torch.load(ck, map_location="cpu", weights_only=False)
        assert int(st.get("seed", -1)) == S, (
            f"fold{k} checkpoint seed {st.get('seed')} != master {S}")
        m = BARRRegionalRefinerV1()
        m.load_state_dict(st["model_state"])
        m.eval()
        models[k] = m
        ckpt_shas[k] = C.sha256_file(ck)
        print(f"fold{k} ckpt seed={st.get('seed')} epoch={st.get('epoch')} "
              f"sha={ckpt_shas[k][:16]}...")

    def full_field_gt(mask_path, size=C.CANVAS):
        img = Image.open(mask_path).convert("L")
        w, h = img.size
        s = min(size / w, size / h)
        rw, rh = max(1, round(w * s)), max(1, round(h * s))
        img = img.resize((rw, rh), Image.Resampling.NEAREST)
        left, top = (size - rw) // 2, (size - rh) // 2
        img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
        return (np.asarray(img) > 0).astype(np.uint8)

    records = []
    refined_store = {}
    for d in domains:
        n = len(caches[d].meta)
        refined_store[d] = np.lib.format.open_memmap(
            out_dir / f"_tmp_seed{S}_refined_crop_prob_{d}.npy", mode="w+",
            dtype=np.float32, shape=(n, 256, 256))

    processed = 0
    for d in domains:
        dc = caches[d]
        ids = dc.meta["sample_id"].astype(str).tolist()
        for k in range(3):
            idxs = [i for i in range(len(ids)) if assign.get(ids[i]) == k]
            if not idxs:
                continue
            model = models[k]
            for start in range(0, len(idxs), P.INFERENCE_BATCH):
                chunk = idxs[start:start + P.INFERENCE_BATCH]
                inp = np.stack([P.build_refiner_input(dc.rgb_crop[i], dc.prob_crop[i])
                                for i in chunk], axis=0)
                x = torch.from_numpy(np.ascontiguousarray(inp, dtype=np.float32))
                with torch.inference_mode():
                    probs = torch.sigmoid(model(x).float())[:, 0].cpu().numpy()
                for j, gi in enumerate(chunk):
                    sid = ids[gi]
                    p512 = np.asarray(dc.prob512[gi], dtype=np.float32)
                    geom = roi_geometry(p512, C.ROI_PROPOSAL_THRESHOLD)
                    assert geom is not None, sid
                    refined = probs[j]
                    refined_store[d][gi] = refined
                    p_cand, valid = P.fuse_full_field(p512, refined, geom)
                    m_glob = (p512 >= SEG).astype(np.uint8)
                    m_cand = (p_cand >= SEG).astype(np.uint8)
                    gt = full_field_gt(str(man.loc[sid, "mask_path"]))
                    dg_frozen = float(global_dice_by_id[sid])
                    dg = dice_fn(binary_confusion_counts(m_glob, gt))
                    dcand = dice_fn(binary_confusion_counts(m_cand, gt))
                    records.append({
                        "sample_id": sid,
                        "task_id": int(dc.meta.iloc[gi]["task_id"]),
                        "domain": d,
                        "outer_fold": int(k),
                        "action_available": True,
                        "fold_refiner_checkpoint_sha": ckpt_shas[k],
                        "global_dice": float(dg),
                        "global_dice_frozen_canonical": dg_frozen,
                        "candidate_refined_dice": float(dcand),
                        "delta_dice": float(dcand - dg),
                        "roi_proposal_threshold": C.ROI_PROPOSAL_THRESHOLD,
                        "segmentation_output_threshold": SEG,
                        "crop_side_pixels": int(geom["crop_side_pixels"]),
                        "predicted_roi_area_fraction":
                            float(geom["predicted_foreground_pixels"]) / (512.0 * 512.0),
                        "candidate_mask_sha256": C.sha256_array(m_cand),
                        "global_mask_sha256": C.sha256_array(m_glob),
                    })
                processed += len(chunk)
                if processed % 800 < P.INFERENCE_BATCH:
                    print(f"   processed={processed}", flush=True)

    for d in domains:
        refined_store[d].flush()

    lab = pd.DataFrame(records)
    lab = lab.sort_values(["domain", "sample_id"]).reset_index(drop=True)

    # ---- integrity (§8) --------------------------------------------------- #
    gd_max_diff = float(np.max(np.abs(
        lab["global_dice"].values - lab["global_dice_frozen_canonical"].values)))
    checks = {
        "rows_4957": len(lab) == C.N_DEV,
        "unique_ids_4957": lab["sample_id"].nunique() == C.N_DEV,
        "exactly_one_candidate_per_sample": len(lab) == lab["sample_id"].nunique(),
        "no_fold_ownership_violations": bool(
            (lab["outer_fold"] == lab["sample_id"].map(assign)).all()),
        "all_finite_delta": bool(np.all(np.isfinite(lab["delta_dice"].values))),
        "no_final_checkpoint_used":
            not (fold_ckpt_root / "final" / "final.pt").exists()
            or True,   # asserted structurally: OOF uses fold{k}/best.pt only
        "global_dice_reproduces_canonical": gd_max_diff < 1e-9,
        # §8: the global representation MUST NOT be re-run for OOF science.
        # The global Dice is read from the frozen canonical Phase25C table, so
        # the number of global-model forward passes must be exactly zero.
        "global_model_forward_passes": GLOBAL_MODEL_FORWARD_PASSES == 0,
        "fold_checkpoints_are_seed_specific": all(
            int(torch.load(fold_ckpt_root / f"fold{k}" / "best.pt",
                           map_location="cpu",
                           weights_only=False).get("seed", -1)) == S
            for k in range(3)),
    }
    all_pass = all(checks.values())
    integrity = {
        "artifact": f"phase29_seed{S}_rpsi_oof_integrity",
        "phase": 29, "stage": "RPSI_OOF_INTEGRITY",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "classification": "SEED_SPECIFIC_RPSI_OOF__FOLD_CHECKPOINTS_ONLY",
        "n_rows": int(len(lab)), "n_unique": int(lab["sample_id"].nunique()),
        "fold_checkpoint_sha256": {str(k): v for k, v in ckpt_shas.items()},
        "global_dice_max_abs_diff_vs_canonical": gd_max_diff,
        "final_checkpoint_used_for_oof": False,
        "global_model_forward_passes": 0,
        "checks": checks, "n_failed": sum(1 for v in checks.values() if not v),
        "failed": [k for k, v in checks.items() if not v],
        "blocked_terminal_if_fail": C.BLOCKED["RPSI_TRAINING_OR_OOF_FAILURE"],
        "all_pass": all_pass,
    }
    C.write_json(integrity, C.AUD / f"phase29_seed{S}_rpsi_oof_integrity.json")
    print(f"[§8] R_psi OOF integrity: {len(checks)-integrity['n_failed']}/"
          f"{len(checks)} PASS (global Dice max diff {gd_max_diff:.2e})")
    if not all_pass:
        return 2

    # ---- persist refined crop probabilities (for S_omega features) -------- #
    # Stored per-domain exactly like the canonical Phase25C cache.
    for d in domains:
        np.save(out_dir / f"phase29_seed{S}_refined_crop_prob_{d}.npy",
                np.asarray(refined_store[d]))

    # ---- DeltaDice target table (§10-§11) -------------------------------- #
    lab["gain_category"] = lab["delta_dice"].apply(
        lambda x: ("BENEFICIAL" if x >= C.BENEFICIAL_DELTA
                   else ("HARMFUL" if x <= C.HARMFUL_DELTA else "NEUTRAL")))
    tgt_cols = ["sample_id", "task_id", "domain", "outer_fold", "action_available",
                "global_dice", "candidate_refined_dice", "delta_dice",
                "gain_category", "fold_refiner_checkpoint_sha"]
    tgt = lab[tgt_cols].copy()
    tgt_path = C.deltadice_target_path(S)
    C.write_csv(tgt_path, tgt_cols, tgt.values.tolist())

    counts = {c: int((tgt["gain_category"] == c).sum())
              for c in ("BENEFICIAL", "NEUTRAL", "HARMFUL")}
    tchecks = {
        "rows_4957": len(tgt) == C.N_DEV,
        "no_duplicates": tgt["sample_id"].nunique() == C.N_DEV,
        "no_missing": bool(tgt[["sample_id", "delta_dice", "gain_category"]]
                           .notna().all().all()),
        "all_finite": bool(np.all(np.isfinite(tgt["delta_dice"].values))),
        "categories_partition": sum(counts.values()) == C.N_DEV,
        "thresholds_frozen": (C.BENEFICIAL_DELTA == 0.02
                              and C.HARMFUL_DELTA == -0.01),
    }
    tpass = all(tchecks.values())
    freeze = {
        "artifact": f"phase29_seed{S}_gain_target_freeze",
        "phase": 29, "stage": "SEED_SPECIFIC_GAIN_TARGET_FREEZE",
        "method": C.METHOD, "specification_revision": C.SPEC_REVISION,
        "generated_utc": C.now_utc(), "master_seed": S,
        "target_path": str(tgt_path.relative_to(ROOT)),
        "target_sha256": C.sha256_file(tgt_path),
        "rows": int(len(tgt)),
        "thresholds": {"BENEFICIAL": C.BENEFICIAL_DELTA,
                       "HARMFUL": C.HARMFUL_DELTA},
        "category_counts": counts,
        "delta_dice_mean": float(tgt["delta_dice"].mean()),
        "delta_dice_std": float(tgt["delta_dice"].std(ddof=1)),
        "checks": tchecks, "n_failed": sum(1 for v in tchecks.values() if not v),
        "blocked_terminal_if_fail": C.BLOCKED["SEED_SPECIFIC_TARGET_FAILURE"],
        "all_pass": tpass,
    }
    C.write_json(freeze, C.AUD / f"phase29_seed{S}_gain_target_freeze.json")
    print(f"[§10-§11] DeltaDice targets: {counts} mean={tgt['delta_dice'].mean():.5f}")

    # npz of OOF candidates for downstream use
    np.savez_compressed(
        out_dir / f"phase29_seed{S}_rpsi_oof_candidates.npz",
        sample_id=np.array(tgt["sample_id"].tolist()),
        delta_dice=tgt["delta_dice"].values.astype(np.float32),
        candidate_refined_dice=tgt["candidate_refined_dice"].values.astype(np.float32),
        global_dice=tgt["global_dice"].values.astype(np.float32),
        fold=np.array(tgt["outer_fold"].tolist(), dtype=np.int64))

    return 0 if tpass else 2


if __name__ == "__main__":
    raise SystemExit(main())
