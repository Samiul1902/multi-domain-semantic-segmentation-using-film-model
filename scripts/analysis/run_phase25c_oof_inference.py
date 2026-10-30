"""Phase 25C -- OOF refiner inference (§10) + full-field reconstruction (§11)
+ paired DeltaDice label computation (§12-§14).

For every action-available ROUTER_DEVELOPMENT sample:
    * use ONLY the fold-specific canonical ROI-0.30 refiner whose outer target
      fold contains the sample (never final.pt)
    * exact canonical 4x256x256 refiner input from the frozen cache
    * one FP32 forward (eval, inference_mode) -> sigmoid -> 256x256 refined crop
    * inverse-crop to the 512 canvas; frozen fusion: replace inside the valid
      canonical ROI, leave p_global unchanged outside
    * full-field segmentation at 0.50 and canonical Dice vs full-field GT

Global MedFiLM is NEVER re-run (global_model_forward_passes = 0).

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/run_phase25c_oof_inference.py
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))
CODE = ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
sys.path.insert(0, str(CODE))
import phase25c_common as C  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image  # noqa: E402

from src.models.barr.regional_refiner import BARRRegionalRefinerV1  # noqa: E402
from src.data.barr_roi import roi_geometry  # noqa: E402
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_fn  # noqa: E402

AUD = ROOT / "reports" / "audits"
TRAIN_MANIFEST = ROOT / "manifests" / "phase4_v3" / "train.csv"
UTC = "2026-09-30T17:05:00+00:00"
SEG = C.SEGMENTATION_OUTPUT_THRESHOLD


def full_field_gt(mask_path: str, size: int = C.REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    """Canonical full-field GT on the 512 canvas (nearest-neighbour, centre padded)."""
    img = Image.open(mask_path).convert("L")
    w, h = img.size
    scale = min(size / w, size / h)
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    img = img.resize((rw, rh), Image.Resampling.NEAREST)
    left, top = (size - rw) // 2, (size - rh) // 2
    from PIL import ImageOps
    img = ImageOps.expand(img, (left, top, size - rw - left, size - rh - top))
    return (np.asarray(img) > 0).astype(np.uint8)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-domain", type=int, default=None)
    ap.add_argument("--out-dir", type=str, default=None)
    args = ap.parse_args()

    out_dir = Path(args.out_dir) if args.out_dir else C.LABEL_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    dev = C.load_development()
    assign = C.load_outer_fold_assignment()
    domains = sorted(dev["dataset"].unique().tolist())
    caches = {d: C.DomainCache(d) for d in domains}

    man = pd.read_csv(TRAIN_MANIFEST).set_index("sample_id", drop=False)

    models = {}
    for k in C.OUTER_FOLDS:
        m = BARRRegionalRefinerV1()
        st = torch.load(C.FOLD_CKPT[k], map_location="cpu", weights_only=False)
        m.load_state_dict(st["model_state"])
        m.eval()
        models[k] = m

    records: list[dict] = []
    fold_counts = {0: 0, 1: 0, 2: 0}
    batches = 0
    processed = 0
    t0 = time.time()
    global_forwards = 0

    refined_store = {}
    for d in domains:
        n = len(caches[d].meta)
        refined_store[d] = np.lib.format.open_memmap(
            out_dir / f"_tmp_refined_crop_prob_{d}.npy", mode="w+",
            dtype=np.float32, shape=(n, 256, 256))

    for d in domains:
        dc = caches[d]
        sub = dc.meta.copy()
        ids = sub["sample_id"].astype(str).tolist()
        if args.limit_per_domain:
            ids = ids[:args.limit_per_domain]
        print(f"\n[{d}] n={len(ids)}")
        for k in C.OUTER_FOLDS:
            idxs = [i for i in range(len(ids)) if assign.get(ids[i]) == k]
            if not idxs:
                continue
            model = models[k]
            for start in range(0, len(idxs), C.INFERENCE_BATCH):
                chunk = idxs[start:start + C.INFERENCE_BATCH]
                batches += 1
                inp = np.stack([C.build_refiner_input(dc.rgb_crop[i], dc.prob_crop[i])
                                for i in chunk], axis=0)
                x = torch.from_numpy(np.ascontiguousarray(inp, dtype=np.float32))
                with torch.inference_mode():
                    logits = model(x)                     # FP32, no autocast
                    probs = torch.sigmoid(logits.float())[:, 0].cpu().numpy()
                for j, gi in enumerate(chunk):
                    sid = ids[gi]
                    p512 = np.asarray(dc.prob512[gi], dtype=np.float32)
                    geom = roi_geometry(p512, C.ROI_PROPOSAL_THRESHOLD)
                    assert geom is not None, sid
                    refined = probs[j]
                    refined_store[d][gi] = refined
                    p_cand, valid = C.fuse_full_field(p512, refined, geom)

                    m_glob = (p512 >= SEG).astype(np.uint8)
                    m_cand = (p_cand >= SEG).astype(np.uint8)
                    gt = full_field_gt(str(man.loc[sid, "mask_path"]))

                    dg = dice_fn(binary_confusion_counts(m_glob, gt))
                    dcand = dice_fn(binary_confusion_counts(m_cand, gt))
                    delta = dcand - dg

                    records.append({
                        "sample_id": sid,
                        "task_id": int(sub.iloc[gi]["task_id"]),
                        "domain": d,
                        "outer_fold": int(k),
                        "action_available": True,
                        "fold_refiner_checkpoint_sha": C.EXPECTED[f"fold{k}_checkpoint_sha256"],
                        "global_dice": float(dg),
                        "candidate_refined_dice": float(dcand),
                        "delta_dice": float(delta),
                        "roi_proposal_threshold": C.ROI_PROPOSAL_THRESHOLD,
                        "segmentation_output_threshold": SEG,
                        "crop_side_pixels": int(geom["crop_side_pixels"]),
                        "predicted_roi_area_fraction":
                            float(geom["predicted_foreground_pixels"]) / (512.0 * 512.0),
                        "candidate_mask_sha256": C.sha256_array(m_cand),
                        "global_mask_sha256": C.sha256_array(m_glob),
                        "_valid_pixels": int(valid.sum()),
                    })
                processed += len(chunk)
                fold_counts[k] += len(chunk)
                if (processed % 800) < C.INFERENCE_BATCH:
                    print(f"   processed={processed} elapsed={time.time()-t0:.0f}s", flush=True)

    for d in domains:
        refined_store[d].flush()

    lab = pd.DataFrame(records).sort_values(["domain", "sample_id"]).reset_index(drop=True)
    lab["feature_row_index"] = -1   # filled by join with Phase25B metadata
    lab.to_csv(out_dir / "_tmp_labels.csv", index=False)

    print(f"\nDONE processed={processed} batches={batches} elapsed={time.time()-t0:.0f}s")
    print("fold counts:", fold_counts, "global_forwards:", global_forwards)
    print("mean delta_dice:", float(lab["delta_dice"].mean()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
