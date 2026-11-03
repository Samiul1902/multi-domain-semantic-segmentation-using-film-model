"""OOF paired-gain labels and the derived safety targets.

For every ROUTER_DEVELOPMENT sample exactly one refiner produces the candidate, and
it is the refiner of the outer fold that sample belongs to.  That is what makes the
labels *out-of-fold*: the refiner that labels a sample never saw it during fit or
early stopping.  Using the deployed refit instead would leak, because the refit saw
the whole development population.

Per sample
----------
``global_dice``      Dice(p_global >= 0.50, GT) on the 512 canvas
``candidate_dice``   Dice(fused candidate >= 0.50, GT) on the 512 canvas
``delta_dice``       candidate - global
``gain_category``    BENEFICIAL (>= +0.02) / HARMFUL (<= -0.01) / NEUTRAL
``safety_target``    1 iff delta_dice > 0   (the S_omega label)

Samples whose global prediction is empty at the ROI threshold are FORCED_SKIP: no
refinement is executed, the candidate equals the global map, and the delta is 0 by
construction rather than by an imputation.

Leakage
-------
The GT mask is read only to *score* the two predictions.  It never reaches a feature
vector: the router's 202-D vector and the safety module's 16-D vector are built from
predictions and geometry only.

The out-of-fold guarantee is *partial* and ``oof_contract()`` records exactly where it
stops.  R_psi is genuinely cross-fitted, but G is fitted once on all 5,832 TRAIN
samples -- which includes every ROUTER_DEVELOPMENT sample -- so ``p_global`` and the
feature vectors are in-sample for the backbone.  The labels are therefore
refiner-OOF / backbone-in-sample, and the absolute harm rate they induce is
optimistic rather than a held-out estimate.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch

from .. import recipe as R
from ..context import RunContext, StageRecord
from ..provenance import (atomic_write_json, atomic_write_text, load_checkpoint, read_json,
                          relpath_str, sha256_file, utc_now)
from ..seeds import seed_everything
from src.data.barr_refiner_dataset import BARRRefinerCropDataset
from src.metrics.evaluation_metrics import binary_confusion_counts, dice as dice_from_counts
from src.models.barr import BARRRegionalRefinerV1
from src.utils.device import get_device

_SCRIPTS_ANALYSIS = R.ROOT / "scripts" / "analysis"
if str(_SCRIPTS_ANALYSIS) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_SCRIPTS_ANALYSIS))
from phase25f_post_safety_features import compute_numeric_features  # noqa: E402

STAGE = "L"

#: inverse-crop + deterministic fusion, reused verbatim from the frozen Phase-25C module
_NB_CODE = R.ROOT / "notebooks" / "phasewise" / "phase_25c_paired_gain_labels" / "code"
if str(_NB_CODE) not in __import__("sys").path:
    __import__("sys").path.insert(0, str(_NB_CODE))
from phase25c_common import fuse_full_field  # noqa: E402


def categorize(delta: float) -> str:
    if delta >= R.LABEL_BENEFICIAL_DELTA:
        return "BENEFICIAL"
    if delta <= R.LABEL_HARMFUL_DELTA:
        return "HARMFUL"
    return "NEUTRAL"


def _mask_512(path: str) -> np.ndarray:
    from PIL import Image

    img = Image.open(path).convert("L")
    if img.size != (R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION):
        img = img.resize((R.REGIONAL_CANVAS_RESOLUTION, R.REGIONAL_CANVAS_RESOLUTION),
                         Image.Resampling.NEAREST)
    return (np.asarray(img, dtype=np.float32) > 0).astype(np.uint8)


def _geometry_from_meta(row) -> dict:
    return {k: (float(row[k]) if k in ("effective_magnification", "margin") else int(row[k]))
            for k in ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
                      "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels",
                      "effective_magnification", "margin")}


@torch.inference_mode()
def _refine_fold(ctx: RunContext, fold: int, device, amp: bool) -> Dict[str, dict]:
    """Run fold ``fold``'s refiner over that fold's outer target. Returns id -> row."""
    ck = load_checkpoint(ctx.r_dir / f"fold{fold}" / "best.pt", map_location="cpu",
                         component="R", seed=ctx.seed)
    model = BARRRegionalRefinerV1()
    model.load_state_dict(ck["model_state"])
    model = model.to(device).eval()

    target_csv = ctx.cache_dir / "folds" / f"fold{fold}_outer_target.csv"
    ds = BARRRefinerCropDataset(target_csv, cache_root=ctx.cache_dir, train=False,
                               base_seed=ctx.seed, epoch=0)
    if len(ds) == 0:
        raise RuntimeError(f"[L/{ctx.tag}] fold{fold} outer target is empty")

    metas = {}
    for domain in R.DATASET_ORDER:
        p = ctx.cache_dir / domain / "meta.csv"
        if p.exists():
            m = pd.read_csv(p)
            for _, r in m.iterrows():
                metas[str(r["sample_id"])] = r

    out: Dict[str, dict] = {}
    for i in range(len(ds)):
        item = ds[i]
        sid = item["sample_id"]
        x = item["input"][None].to(device)
        with torch.amp.autocast(device_type=device.type, enabled=amp):
            logits = model(x)
        refined = torch.sigmoid(logits.float())[0, 0].cpu().numpy().astype(np.float32)
        out[sid] = {"refined_crop": refined, "meta": metas[sid]}
    return out


def oof_contract(ctx: RunContext) -> dict:
    """Exactly which parts of the label are out-of-fold, and which are not.

    The refiner is genuinely cross-fitted: fold-k's ``best.pt`` labels fold-k's
    ``outer_target`` and never trained on it.  The **backbone is not**: G is fitted
    once on the whole TRAIN population (5,832), which contains every
    ROUTER_DEVELOPMENT sample, so ``p_global`` and both feature vectors are
    *in-sample* for G.

    That asymmetry is inherited from the frozen Phase-25D/25F producers and is kept
    deliberately: changing the G training population would break comparability with
    the historical labels.  It is recorded here, in machine-readable form, so the
    OOF claim can never be overstated as "fully out-of-fold".
    """
    return {
        "refiner_out_of_fold": True,
        "backbone_out_of_fold": False,
        "router_out_of_fold": True,
        "safety_out_of_fold": True,
        "backbone_training_population": "TRAIN",
        "backbone_training_n": int(R.TRAIN_N),
        "backbone_sees_target_sample": True,
        "refiner_cross_fit_folds": len(R.R_OUTER_FOLDS),
        "router_cross_fit_folds": int(R.B_CV_FOLDS),
        "consequence": (
            "delta_dice measures what a fold-k refiner does to the output of a G that "
            "already memorised the sample, so it is refiner-OOF but backbone-in-sample; "
            "absolute harm rates are therefore optimistic and must not be read as "
            "held-out generalisation"),
        "provenance": "inherited from the frozen Phase-25D/25F label construction",
    }


def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    device = get_device(require_cuda=(ctx.bounds.device == "cuda"))
    amp = bool(ctx.bounds.amp) and device.type == "cuda"
    seed_everything(ctx.family.run_seed("L", "main"))

    cache_manifest = read_json(ctx.cache_dir / "manifest.json")
    if not cache_manifest.get("complete"):
        raise RuntimeError(f"[L/{ctx.tag}] crop cache is incomplete")
    if cache_manifest.get("g_checkpoint_sha256") != ctx.g_sha():
        raise RuntimeError(f"[L/{ctx.tag}] crop cache was built from a different G")

    folds = ctx.folds("outer3")
    dev = ctx.population.development
    path_by_id = {str(s): (str(ip), str(mp)) for s, ip, mp in
                  zip(dev["sample_id"], dev["image_path"], dev["mask_path"])}

    # ---- open each domain's cache exactly once ---------------------------- #
    meta_by_id: Dict[str, object] = {}
    prob512_by_domain: Dict[str, np.ndarray] = {}
    pos_by_domain: Dict[str, Dict[str, int]] = {}
    for domain in R.DATASET_ORDER:
        p = ctx.cache_dir / domain / "meta.csv"
        if not p.exists():
            continue
        m = pd.read_csv(p)
        pos_by_domain[domain] = {str(s): i for i, s in enumerate(m["sample_id"].astype(str))}
        prob512_by_domain[domain] = np.load(ctx.cache_dir / domain / "prob512.npy", mmap_mode="r")
        for _, r in m.iterrows():
            meta_by_id[str(r["sample_id"])] = r

    import hashlib

    t0 = time.time()
    rows: List[dict] = []
    safety_rows: List[dict] = []
    safety_feats: List[np.ndarray] = []
    refined_crops: List[np.ndarray] = []
    for k in sorted(folds.folds):
        log(f"[L/{ctx.tag}] fold{k}: refining {len(folds.folds[k]['outer_target'])} samples")
        refined = _refine_fold(ctx, k, device, amp)
        fold_ck_sha = sha256_file(ctx.r_dir / f"fold{k}" / "best.pt")
        for sid in folds.folds[k]["outer_target"]:
            meta = meta_by_id[sid]
            domain = str(meta["dataset"])
            p512 = np.asarray(
                prob512_by_domain[domain][pos_by_domain[domain][sid]], dtype=np.float32)
            gt = _mask_512(path_by_id[sid][1])

            g_bin = (p512 >= np.float32(R.SEGMENTATION_OUTPUT_THRESHOLD)).astype(np.uint8)
            g_dice = dice_from_counts(binary_confusion_counts(g_bin, gt))

            available = int(meta["action_available"]) == 1 and sid in refined
            if available:
                geom = _geometry_from_meta(meta)
                cand, _valid = fuse_full_field(p512, refined[sid]["refined_crop"], geom)
                c_bin = (cand >= np.float32(R.SEGMENTATION_OUTPUT_THRESHOLD)).astype(np.uint8)
                c_dice = dice_from_counts(binary_confusion_counts(c_bin, gt))
                cand_sha = hashlib.sha256(np.ascontiguousarray(c_bin).tobytes()).hexdigest()

                # ---- 16-D post-refinement safety features (GT-free) -------- #
                p_crop = np.load(ctx.cache_dir / domain / "prob_crop.npy",
                                 mmap_mode="r")[pos_by_domain[domain][sid]]
                p_crop = np.asarray(p_crop, dtype=np.float32)
                if p_crop.ndim == 3:
                    p_crop = p_crop[0]
                x0, x1 = int(meta["clip_x1"]), int(meta["clip_x2"])
                y0, y1 = int(meta["clip_y1"]), int(meta["clip_y2"])
                w_in = max(0, min(R.REGIONAL_CANVAS_RESOLUTION, x1) - max(0, x0))
                h_in = max(0, min(R.REGIONAL_CANVAS_RESOLUTION, y1) - max(0, y0))
                sf = np.asarray(compute_numeric_features(
                    p_crop, refined[sid]["refined_crop"],
                    (w_in * h_in) / float(R.REGIONAL_CANVAS_RESOLUTION ** 2),
                    float(meta["crop_side_pixels"])), dtype=np.float32)
                if sf.shape != (R.S_NUMERIC_DIM,):
                    raise RuntimeError(f"safety feature shape {sf.shape} != ({R.S_NUMERIC_DIM},)")
                safety_rows.append({"sample_id": sid, "task_id": int(meta["task_id"]),
                                    "domain": domain, "outer_fold": int(k)})
                safety_feats.append(sf)
                refined_crops.append(refined[sid]["refined_crop"].astype(np.float16))
            else:
                c_dice = g_dice
                cand_sha = "FORCED_SKIP_NO_REFINEMENT"

            delta = float(c_dice - g_dice)
            rows.append({
                "sample_id": sid,
                "task_id": int(meta["task_id"]),
                "domain": str(meta["dataset"]),
                "outer_fold": int(k),
                "action_available": bool(available),
                "fold_refiner_checkpoint_sha": fold_ck_sha,
                "global_dice": float(g_dice),
                "candidate_refined_dice": float(c_dice),
                "delta_dice": delta,
                "gain_category": categorize(delta),
                "safety_target": int(delta > 0.0),
                "roi_proposal_threshold": R.ROI_PROPOSAL_THRESHOLD,
                "segmentation_output_threshold": R.SEGMENTATION_OUTPUT_THRESHOLD,
                "crop_side_pixels": int(meta["crop_side_pixels"]) if available else 0,
                "predicted_roi_area_fraction": (
                    float((min(512, int(meta["clip_x2"])) - max(0, int(meta["clip_x1"])))
                          * (min(512, int(meta["clip_y2"])) - max(0, int(meta["clip_y1"])))
                          / (512.0 * 512.0)) if available else 0.0),
                "candidate_mask_sha256": cand_sha,
            })

    labels = pd.DataFrame(rows)
    expected = set(dev["sample_id"].astype(str))
    got = set(labels["sample_id"].astype(str))
    if got != expected:
        raise RuntimeError(
            f"[L/{ctx.tag}] label population mismatch: missing {len(expected - got)}, "
            f"extra {len(got - expected)}")
    if labels["sample_id"].duplicated().any():
        raise RuntimeError(f"[L/{ctx.tag}] duplicate sample_id in label table")

    ctx.l_dir.mkdir(parents=True, exist_ok=True)
    label_path = ctx.l_dir / "labels.csv"
    atomic_write_text(labels.to_csv(index=False), label_path)
    safety_path = ctx.l_dir / "safety_targets.csv"
    atomic_write_text(labels[["sample_id", "task_id", "domain", "outer_fold",
                              "delta_dice", "safety_target"]].to_csv(index=False), safety_path)

    # ---- 16-D safety features + OOF refined crops ---------------------- #
    if not safety_feats:
        raise RuntimeError(f"[L/{ctx.tag}] no action-available samples; safety stage cannot train")
    feats_arr = np.stack(safety_feats).astype(np.float32)
    crops_arr = np.stack(refined_crops).astype(np.float16)
    sf_path = ctx.l_dir / "safety_features.npy"
    np.save(sf_path, feats_arr)
    rc_path = ctx.l_dir / "refined_crop_oof.npy"
    np.save(rc_path, crops_arr)
    sf_meta_path = ctx.l_dir / "safety_features_meta.csv"
    sf_meta = pd.DataFrame(safety_rows)
    sf_meta["delta_dice"] = labels.set_index("sample_id").loc[
        sf_meta["sample_id"], "delta_dice"].to_numpy()
    sf_meta["safety_target"] = labels.set_index("sample_id").loc[
        sf_meta["sample_id"], "safety_target"].to_numpy()
    atomic_write_text(sf_meta.to_csv(index=False), sf_meta_path)

    cats = labels["gain_category"].value_counts().to_dict()
    manifest = {
        "artifact": "full_barr_oof_paired_gain_labels", "stage": STAGE,
        "seed": ctx.seed, "tag": ctx.tag,
        "population_n": int(len(labels)),
        "population_source": "ROUTER_DEVELOPMENT",
        "action_available_n": int(labels["action_available"].sum()),
        "forced_skip_n": int((~labels["action_available"]).sum()),
        "categories": {k: int(v) for k, v in cats.items()},
        "safety_target_positive_n": int(labels["safety_target"].sum()),
        "safety_target_rule": R.LABEL_SAFETY_TARGET_RULE,
        "category_thresholds": {"BENEFICIAL": R.LABEL_BENEFICIAL_DELTA,
                                "HARMFUL": R.LABEL_HARMFUL_DELTA},
        "cross_fit": "fold-k refiner labels fold-k outer target only",
        "oof_contract": oof_contract(ctx),
        "labels_sha256": sha256_file(label_path),
        "safety_targets_sha256": sha256_file(safety_path),
        "safety_features_path": relpath_str(sf_path),
        "safety_features_sha256": sha256_file(sf_path),
        "safety_features_meta_sha256": sha256_file(sf_meta_path),
        "refined_crop_oof_path": relpath_str(rc_path),
        "refined_crop_oof_sha256": sha256_file(rc_path),
        "safety_feature_rows": int(feats_arr.shape[0]),
        "safety_feature_dim": int(feats_arr.shape[1]),
        "cache_manifest_sha256": sha256_file(ctx.cache_dir / "manifest.json"),
        "elapsed_seconds": round(time.time() - t0, 3),
        "test_reads": 0, "router_holdout_reads": 0,
        "completed_utc": utc_now(),
    }
    atomic_write_json(manifest, ctx.l_dir / "manifest.json")
    log(f"[L/{ctx.tag}] labels={len(labels)} categories={cats} "
        f"pos={manifest['safety_target_positive_n']}")
    return StageRecord(stage=STAGE, status="COMPLETE",
                       artifacts={"labels": str(label_path), "safety": str(safety_path),
                                  "manifest": str(ctx.l_dir / "manifest.json")},
                       detail=manifest)


def is_complete(ctx: RunContext) -> bool:
    m = read_json(ctx.l_dir / "manifest.json")
    lp = ctx.l_dir / "labels.csv"
    if not lp.exists():
        return False
    return m.get("labels_sha256") == sha256_file(lp)


def verify(ctx: RunContext) -> dict:
    m = read_json(ctx.l_dir / "manifest.json")
    df = pd.read_csv(ctx.l_dir / "labels.csv")
    resid = float(np.abs(df["delta_dice"] -
                         (df["candidate_refined_dice"] - df["global_dice"])).max())
    return {"component": "L", "seed": ctx.seed, "population_n": int(len(df)),
            "delta_identity_max_residual": resid,
            "categories": m.get("categories"),
            "verdict": "LABELS_VERIFIED" if resid < 1e-9 else "LABELS_INCONSISTENT"}
