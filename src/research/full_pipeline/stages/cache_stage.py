"""CROP CACHE -- per-seed ROI-0.30 crop cache over ROUTER_DEVELOPMENT.

The refiner cannot be trained without crops, and the crops are a function of the
global probability map, which is a function of the G checkpoint.  A per-seed family
therefore needs its own cache; reusing the seed-42 cache for seed 123 would train
R_123 on G_42's geometry, which is precisely the kind of cross-family reuse the
controlled experiment forbids.

Frozen rule (unchanged from Phase-25A)
-------------------------------------
1. threshold ``p_global`` at 0.30  (ROI PROPOSAL role only)
2. tight bbox of the predicted foreground
3. centre-preserving expansion by 1.50
4. clip to the canvas
5. square-pad deterministically
6. RGB crop (bilinear), p_global crop (bilinear), GT crop (nearest)
7. 256 x 256

The GT crop is a training TARGET.  It never influences the geometry: ``roi_geometry``
takes no ground-truth argument, and the crop window is fixed before the mask is read.

Storage
-------
Written through ``np.lib.format.open_memmap`` so a real 4957-sample family does not
need ~11 GB of resident memory, and so an interrupted build leaves a file whose
length is still the pre-allocated one.  Completion is recorded separately in
``cache/manifest.json`` only after every domain array is flushed.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import torch
from PIL import Image

from .. import recipe as R
from ..context import RunContext, StageRecord
from ..provenance import (atomic_write_json, load_checkpoint, read_json, relpath_str,
                          sha256_file, utc_now)
from ..seeds import seed_everything
from src.data.barr_roi import (REGIONAL_INPUT_RESOLUTION, extract_roi_triplet,
                               roi_geometry)
from src.features.barr_pre_refinement_features import build_feature_vector
from src.models.film import GlobalMedFiLM
from src.utils.device import get_device

STAGE = "CACHE"

GEOM_KEYS = ("y1", "y2", "x1", "x2", "clip_y1", "clip_y2", "clip_x1", "clip_x2",
             "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels",
             "effective_magnification", "margin", "bbox_min_y", "bbox_min_x",
             "bbox_max_y", "bbox_max_x")


# --------------------------------------------------------------------------- #
def _load_g(ctx: RunContext, device) -> GlobalMedFiLM:
    ck = load_checkpoint(ctx.g_checkpoint(), map_location="cpu", component="G", seed=ctx.seed)
    m = R.G_MODEL
    model = GlobalMedFiLM(task_count=m["task_count"], in_channels=m["in_channels"],
                          out_channels=m["out_channels"], channels=tuple(m["channels"]),
                          task_embedding_dim=m["task_embedding_dim"],
                          film_hidden_dim=m["film_hidden_dim"])
    model.load_state_dict(ck["model_state"])
    return model.to(device).eval()


def _read_image_512(path: str, size: int = R.REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    """Native image -> float32 RGB (3, size, size) in [0, 1]."""
    img = Image.open(path).convert("RGB")
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.BILINEAR)
    return np.asarray(img, dtype=np.float32).transpose(2, 0, 1) / 255.0


def _read_mask_512(path: str, size: int = R.REGIONAL_CANVAS_RESOLUTION) -> np.ndarray:
    img = Image.open(path).convert("L")
    if img.size != (size, size):
        img = img.resize((size, size), Image.Resampling.NEAREST)
    return (np.asarray(img, dtype=np.float32) > 0).astype(np.float32)


@torch.inference_mode()
def _forward(model, image_chw: np.ndarray, task_id: int, device, amp: bool):
    """One G forward returning ``(p512, tap_maps)``.

    The taps are captured with the verified Stage-6 recorder so that the 202-D
    router feature vector is built from exactly the same tensors the inference
    adapter sees.  ``bridge`` / ``decoder2`` / ``decoder1`` are the three frozen
    taps; nothing else is exported.
    """
    from src.research.stage6.end_to_end import TAPS, TapRecorder

    x = torch.from_numpy(np.ascontiguousarray(image_chw))[None].to(device)
    t = torch.tensor([int(task_id)], device=device)
    rec = TapRecorder(model)
    try:
        with torch.amp.autocast(device_type=device.type, enabled=amp):
            logits = model(x, t)
        cmaps = {tap: rec.store[tap].float().cpu().numpy()[0] for tap in TAPS}
    finally:
        rec.close()
    p512 = torch.sigmoid(logits.float())[0, 0].cpu().numpy().astype(np.float32)
    return p512, cmaps


# --------------------------------------------------------------------------- #
def run(ctx: RunContext, *, resume: bool = False, log=print,
        model_loader=None, feature_builder=None) -> StageRecord:
    """Build the per-seed crop cache and 202-D pre-refinement features.

    ``model_loader(ctx, device)`` and ``feature_builder(cmaps, p512, geom)`` are
    injection points so a different backbone family (Lite) reuses this producer
    instead of duplicating the frozen ROI rule, the memmap layout and the
    FORCED_SKIP accounting.  Both default to the FULL implementations.
    """
    device = get_device(require_cuda=(ctx.bounds.device == "cuda"))
    amp = bool(ctx.bounds.amp) and device.type == "cuda"
    g_sha = ctx.g_sha()
    seed_everything(ctx.family.run_seed("CACHE", "main"))
    build_features = feature_builder or build_feature_vector

    dev = ctx.population.development
    root = ctx.cache_dir
    root.mkdir(parents=True, exist_ok=True)
    log(f"[CACHE/{ctx.tag}] population={len(dev)} G={g_sha[:16]} device={device}")

    model = (model_loader or _load_g)(ctx, device)
    manifest_path = root / "manifest.json"
    prev = read_json(manifest_path)
    if resume and prev.get("g_checkpoint_sha256") == g_sha and prev.get("complete"):
        log(f"[CACHE/{ctx.tag}] already complete for this G ({g_sha[:16]}); skipping")
        return StageRecord(stage=STAGE, status="COMPLETE",
                           artifacts={"manifest": str(manifest_path)}, detail=prev)

    by_domain: Dict[str, pd.DataFrame] = {
        d: dev[dev["dataset"] == d].sort_values("sample_id").reset_index(drop=True)
        for d in R.DATASET_ORDER
    }

    # ---- allocate every array up front (memmap) ----------------------- #
    shapes = {
        "prob512": (None, 512, 512), "rgb_crop": (None, 3, REGIONAL_INPUT_RESOLUTION,
                                                 REGIONAL_INPUT_RESOLUTION),
        "prob_crop": (None, 1, REGIONAL_INPUT_RESOLUTION, REGIONAL_INPUT_RESOLUTION),
        "gt_crop": (None, 1, REGIONAL_INPUT_RESOLUTION, REGIONAL_INPUT_RESOLUTION),
        "action": (None,),
        # 202-D pre-refinement router features, produced by the SAME forward pass
        "router_features": (None, R.B_NUMERIC_DIM),
    }
    dtypes = {"prob512": np.float32, "rgb_crop": np.uint8, "prob_crop": np.float16,
              "gt_crop": np.uint8, "action": np.uint8, "router_features": np.float32}

    arrays: Dict[str, Dict[str, np.ndarray]] = {}
    for d, frame in by_domain.items():
        (root / d).mkdir(parents=True, exist_ok=True)
        arrays[d] = {}
        n = len(frame)
        for name, tail in shapes.items():
            shape = (n,) + tuple(s for s in tail if s is not None)
            arrays[d][name] = np.lib.format.open_memmap(
                root / d / f"{name}.npy", mode="w+", dtype=dtypes[name], shape=shape)

    t0 = time.time()
    totals = {"action_available": 0, "action_unavailable": 0}
    by_domain_counts: Dict[str, dict] = {}

    for d, frame in by_domain.items():
        meta_rows: List[dict] = []
        n_avail = 0
        for i, row in frame.iterrows():
            sid = str(row["sample_id"])
            tid = int(row["task_id"])
            image = _read_image_512(row["image_path"])
            p512, cmaps = _forward(model, image, tid, device, amp)
            arrays[d]["prob512"][i] = p512

            geom = roi_geometry(p512, R.ROI_PROPOSAL_THRESHOLD, R.ROI_FRACTIONAL_MARGIN)
            base = {
                "sample_id": sid, "dataset": d, "task_id": tid,
                "group_key": str(row.get("group_key", f"SINGLETON::{d}::{sid}")),
                "global_checkpoint_sha256": g_sha,
                "roi_proposal_threshold": R.ROI_PROPOSAL_THRESHOLD,
                "segmentation_output_threshold": R.SEGMENTATION_OUTPUT_THRESHOLD,
                "canvas_resolution": R.REGIONAL_CANVAS_RESOLUTION,
                "regional_input_resolution": REGIONAL_INPUT_RESOLUTION,
            }
            if geom is None:
                arrays[d]["action"][i] = 0
                arrays[d]["rgb_crop"][i] = 0
                arrays[d]["prob_crop"][i] = 0
                arrays[d]["gt_crop"][i] = 0
                # no ROI -> the router is never consulted (FORCED_SKIP); record NaN so
                # a zero vector can never be mistaken for a real feature row
                arrays[d]["router_features"][i] = np.nan
                meta_rows.append({**base, "predicted_foreground_pixels": 0,
                                  "action_available": False,
                                  "action_unavailable_reason": "GLOBAL_EMPTY_AT_ROI_THRESHOLD",
                                  **{k: np.nan for k in GEOM_KEYS}})
                totals["action_unavailable"] += 1
                continue

            gt = _read_mask_512(row["mask_path"])
            rgb_c, prob_c, gt_c = extract_roi_triplet(image, p512, gt, geom,
                                                      REGIONAL_INPUT_RESOLUTION)
            arrays[d]["action"][i] = 1
            arrays[d]["rgb_crop"][i] = np.clip(rgb_c * 255.0 + 0.5, 0, 255).astype(np.uint8)
            arrays[d]["prob_crop"][i] = prob_c.astype(np.float16)
            arrays[d]["gt_crop"][i] = (gt_c[0] > 0.5).astype(np.uint8)
            arrays[d]["router_features"][i] = build_features(cmaps, p512, geom)
            n_avail += 1
            totals["action_available"] += 1
            meta_rows.append({**base,
                              "predicted_foreground_pixels": int(geom["predicted_foreground_pixels"]),
                              "action_available": True,
                              "action_unavailable_reason": "",
                              **{k: geom[k] for k in GEOM_KEYS}})

        for arr in arrays[d].values():
            arr.flush()
        pd.DataFrame(meta_rows).to_csv(root / d / "meta.csv", index=False)
        by_domain_counts[d] = {"total": len(frame), "action_available": n_avail,
                               "action_unavailable": len(frame) - n_avail}
        log(f"[CACHE/{ctx.tag}] {d}: n={len(frame)} available={n_avail} "
            f"({time.time() - t0:.1f}s)")

    if len(dev) != sum(v["total"] for v in by_domain_counts.values()):
        raise RuntimeError("cache domain partition does not cover ROUTER_DEVELOPMENT")

    manifest = {
        "artifact": f"{ctx.family_name.lower()}_barr_crop_cache_manifest",
        "stage": STAGE, "seed": ctx.seed, "tag": ctx.tag,
        "population": "ROUTER_DEVELOPMENT",
        "population_n": int(len(dev)),
        "action_available_n": totals["action_available"],
        "action_unavailable_global_empty_n": totals["action_unavailable"],
        "by_domain": by_domain_counts,
        "g_checkpoint": relpath_str(ctx.g_checkpoint()),
        "g_checkpoint_sha256": g_sha,
        "roi_proposal_threshold": R.ROI_PROPOSAL_THRESHOLD,
        "segmentation_output_threshold": R.SEGMENTATION_OUTPUT_THRESHOLD,
        "roi_expansion": R.ROI_EXPANSION_FACTOR,
        "canvas_resolution": R.REGIONAL_CANVAS_RESOLUTION,
        "regional_input_resolution": REGIONAL_INPUT_RESOLUTION,
        "array_dtypes": {k: np.dtype(v).name for k, v in dtypes.items()},
        "complete": True,
        "elapsed_seconds": round(time.time() - t0, 3),
        "test_reads": 0, "router_holdout_reads": 0,
        "completed_utc": utc_now(),
    }
    atomic_write_json(manifest, manifest_path)
    log(f"[CACHE/{ctx.tag}] complete: available={totals['action_available']} "
        f"forced_skip={totals['action_unavailable']}")
    return StageRecord(stage=STAGE, status="COMPLETE",
                       artifacts={"manifest": str(manifest_path)}, detail=manifest)


def is_complete(ctx: RunContext) -> bool:
    m = read_json(ctx.cache_dir / "manifest.json")
    if not m.get("complete"):
        return False
    try:
        return m.get("g_checkpoint_sha256") == ctx.g_sha()
    except FileNotFoundError:
        return False


def verify(ctx: RunContext) -> dict:
    m = read_json(ctx.cache_dir / "manifest.json")
    if not m.get("complete"):
        raise RuntimeError(f"cache for {ctx.tag} is incomplete")
    if m.get("g_checkpoint_sha256") != ctx.g_sha():
        raise RuntimeError(f"cache for {ctx.tag} was built from a different G checkpoint")
    files = {}
    for d in R.DATASET_ORDER:
        for name in ("prob512", "rgb_crop", "prob_crop", "gt_crop", "action",
                     "router_features"):
            p = ctx.cache_dir / d / f"{name}.npy"
            if not p.exists():
                raise FileNotFoundError(p)
            files[f"{d}/{name}"] = sha256_file(p)
    return {"component": "CACHE", "seed": ctx.seed, "population_n": m["population_n"],
            "action_available_n": m["action_available_n"],
            "g_checkpoint_sha256": m["g_checkpoint_sha256"],
            "array_sha256": files, "verdict": "CACHE_VERIFIED"}
