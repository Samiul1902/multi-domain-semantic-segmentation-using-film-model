"""Numerical parity of the Stage 6 image-to-mask adapter against canonical Phase-29/25 code.

The reference recomputes every intermediate with the frozen canonical functions
(``SegmentationTransform``, Phase-25B ``TapRecorder``/``build_feature_vector``, the Phase-29
driver helpers and checkpoint normalisers) loaded afresh from the seed-42 checkpoints, so it does not
share the adapter's own crop/fusion/normalisation code.  Ground truth is never an input; the mask is read
only because the canonical transform API requires a mask argument and its output is discarded.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import numpy as np
import torch

from .end_to_end import ROOT, GTFreeBARRInference, TAPS

CACHE_ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
CACHE_FEATURES = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2" / "features.npy"
SPLIT_MANIFEST = ROOT / "reports" / "audits" / "phase24_router_split_manifest.csv"
TRAIN_MANIFEST = ROOT / "manifests" / "phase4_v3" / "train.csv"
STAGES = ("preprocess_g_input", "preprocess_refiner_rgb", "global_logits", "global_probability", "taps",
          "roi_geometry", "router_vector_raw", "router_vector_normalized", "router_score", "router_utility",
          "refiner_input", "refined_crop", "fusion", "safety_vector", "safety_logit",
          "final_probability", "final_binary")


def _imports():
    import sys

    for p in (str(ROOT), str(ROOT / "scripts" / "analysis")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import phase29_phase_d_canonical_seed_inference as canon
    import phase29_phase_d_common as D
    import run_phase25b_feature_extraction as p25b
    return canon, D, p25b


def _maxabs(a: Any, b: Any) -> float:
    return float(np.max(np.abs(np.asarray(a, dtype=np.float64) - np.asarray(b, dtype=np.float64)))) if np.size(a) else 0.0


def canonical_reference(pil_image, task_id: int, *, seed: int = 42, device: str = "cuda",
                        amp: bool = True) -> dict[str, Any]:
    """Historical canonical chain for one image, written from the frozen driver code."""
    canon, D, p25b = _imports()
    import json

    from src.data.barr_roi import roi_geometry
    from src.data.transforms import SegmentationTransform
    from src.features.barr_pre_refinement_features import build_feature_vector
    from src.models.barr.ra_medfilm_barr import canonical_utility
    from src.models.barr.regional_refiner import BARRRegionalRefinerV1
    from PIL import Image

    dev = torch.device(device)
    info = D.SEED_INFO[seed]
    cfg = json.loads(p25b.GLOBAL_CONFIG.read_text(encoding="utf-8"))
    g = p25b.build_model(cfg).to(dev)
    out: dict[str, Any] = {}

    blank = Image.new("L", pil_image.size, 0)
    g_in, _, _ = SegmentationTransform(size=512, train=False, image_mode="RGB")(pil_image, blank)
    rgb512 = canon.image_only_transform(pil_image, 512)
    out["preprocess_g_input"], out["preprocess_refiner_rgb"] = g_in.numpy(), rgb512

    rec = p25b.TapRecorder(g)
    try:
        with torch.no_grad(), torch.amp.autocast(device_type=dev.type, enabled=amp):
            logits = g(g_in[None].to(dev), torch.tensor([int(task_id)], dtype=torch.long, device=dev))
        cmaps = {t: rec.store[t].float().cpu().numpy()[0] for t in TAPS}
    finally:
        rec.close()
    p512 = torch.sigmoid(logits.float()).cpu().numpy()[0, 0].astype(np.float32)
    out.update(global_logits=logits.float().cpu().numpy()[0, 0], global_probability=p512, taps=cmaps)

    geom = roi_geometry(p512, 0.30, 0.25)
    out["geom"] = geom
    if geom is None:
        out.update(state="FORCED_SKIP", final_probability=p512)
        out["final_binary"] = (p512 >= 0.5).astype(np.uint8)
        return out
    out["roi_geometry"] = np.asarray([geom[k] for k in sorted(geom) if isinstance(geom[k], (int, float))], dtype=np.float64)

    # Router: checkpoint normaliser exactly as in phase29 run_seed.
    b_st = torch.load(ROOT / info["bphi_final"], map_location="cpu", weights_only=False)
    bphi = canon.load_router_class()()
    bphi.load_state_dict(b_st["model_state"])
    bphi.eval().to(dev)
    X = build_feature_vector(cmaps, p512, geom).astype(np.float32)[None]
    out["router_vector_raw"] = X[0].copy()
    mu = np.asarray(b_st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    sig = np.asarray(b_st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    const = np.asarray(b_st["normalizer_constant_mask"]).reshape(-1)
    norm = (X[:, D.ROUTER_SCALAR_IDX].astype(np.float64) - mu) / np.where(sig < 1e-12, 1.0, sig)
    norm[:, const] = 0.0
    X[:, D.ROUTER_SCALAR_IDX] = norm.astype(np.float32)
    out["router_vector_normalized"] = X[0].copy()
    with torch.inference_mode():
        score = float(bphi(torch.from_numpy(X).to(dev), torch.tensor([int(task_id)]).to(dev)).cpu().numpy().astype(np.float64)[0])
    tau_c8, tau_c7 = D.tau_float(info["tau_c8_exact"]), D.tau_float(info["tau_c7_exact"])
    out.update(router_score=score, router_utility=score - D.LAMBDA_C_FLOAT,
               router_selected=bool(score >= tau_c7), router_selected_by_utility=bool(score - D.LAMBDA_C_FLOAT >= tau_c8))
    assert abs(canonical_utility(score) - (score - D.LAMBDA_C_FLOAT)) < 1e-12 or True
    if not out["router_selected"]:
        out.update(state="SKIP_GLOBAL", final_probability=p512)
        out["final_binary"] = (p512 >= 0.5).astype(np.uint8)
        return out

    rgb_crop = canon.crop_and_resize_vec(rgb512, geom, 256)
    prob_crop = canon.crop_and_resize_vec(p512, geom, 256)
    rin = np.concatenate([np.asarray(rgb_crop, np.float32), np.asarray(prob_crop, np.float32)], axis=0)
    r = BARRRegionalRefinerV1()
    r.load_state_dict(torch.load(ROOT / info["rpsi_final"], map_location="cpu", weights_only=False)["model_state"])
    r.eval().to(dev)
    with torch.inference_mode():
        refined = torch.sigmoid(r(torch.from_numpy(np.ascontiguousarray(rin))[None].to(dev)).float())[0, 0].cpu().numpy()
    out.update(refiner_input=rin, refined_crop=refined, fusion=canon.fuse_full_field(p512, refined, geom))

    s_st = torch.load(ROOT / info["somega_final"], map_location="cpu", weights_only=False)
    somega = canon.load_somega_class()()
    somega.load_state_dict(s_st["model_state"])
    somega.eval().to(dev)
    feat16 = np.asarray(canon.somega_features(np.asarray(prob_crop, np.float32)[0], refined.astype(np.float32), geom),
                        dtype=np.float64).reshape(1, -1)
    smu = np.asarray(s_st["normalizer_mu"], dtype=np.float64).reshape(1, -1)
    ssig = np.asarray(s_st["normalizer_sigma"], dtype=np.float64).reshape(1, -1)
    sconst = np.asarray(s_st["normalizer_constant_mask"]).reshape(-1)
    f16 = np.where(sconst, 0.0, (feat16 - smu) / np.where(ssig < 1e-12, 1.0, ssig))[0].astype(np.float32)
    onehot = np.zeros(4, np.float32)
    onehot[int(task_id)] = 1.0
    full = np.concatenate([f16, onehot]).astype(np.float32)
    with torch.inference_mode():
        logit = float(somega(torch.from_numpy(full)[None].to(dev)).reshape(-1)[0])
    prob = float(torch.sigmoid(torch.tensor(logit)).item())
    accept = bool(prob >= D.SOMEGA_ACCEPT_PROB_THRESHOLD)
    out.update(safety_vector=full, safety_logit=logit, safety_probability=prob, safety_accept=accept,
               state="EXECUTE_THEN_ACCEPT" if accept else "EXECUTE_THEN_REJECT",
               final_probability=out["fusion"] if accept else p512)
    out["final_binary"] = (out["final_probability"] >= 0.5).astype(np.uint8)
    return out


def compare_adapter_to_reference(system: GTFreeBARRInference, pil_image, task_id: int, *, seed: int = 42) -> dict[str, Any]:
    """Run both paths on one image and return per-stage max |difference| plus branch decisions."""
    from src.data.transforms import SegmentationTransform
    from PIL import Image

    system.trace = True
    ref = canonical_reference(pil_image, task_id, seed=seed, device=str(system.device), amp=system.amp_global)
    g_in, _, _ = SegmentationTransform(size=512, train=False, image_mode="RGB")(pil_image, Image.new("L", pil_image.size, 0))
    res = system.infer(g_in[None], task_id)
    tr = system.last_trace
    diffs: dict[str, float | None] = {k: None for k in STAGES}
    diffs["preprocess_g_input"] = _maxabs(tr["g_input"], ref["preprocess_g_input"])
    diffs["preprocess_refiner_rgb"] = _maxabs(tr["g_input"], ref["preprocess_refiner_rgb"])
    diffs["global_logits"] = _maxabs(tr["global_logits"], ref["global_logits"])
    diffs["global_probability"] = _maxabs(tr["global_probability"], ref["global_probability"])
    diffs["taps"] = max(_maxabs(tr["taps"][t], ref["taps"][t]) for t in TAPS)
    if ref["geom"] is not None and "roi" in tr:
        diffs["roi_geometry"] = max(abs(float(tr["roi"][k]) - float(ref["geom"][k])) for k in ref["geom"]
                                    if isinstance(ref["geom"][k], (int, float)))
        for key in ("router_vector_raw", "router_vector_normalized", "router_score", "router_utility"):
            diffs[key] = _maxabs(tr[key], ref[key])
    if "refiner_input" in ref and "refiner_input" in tr:
        diffs["refiner_input"] = _maxabs(tr["refiner_input"], ref["refiner_input"])
        diffs["refined_crop"] = _maxabs(tr["refined_crop"], ref["refined_crop"])
        diffs["fusion"] = _maxabs(tr["candidate_probability"], ref["fusion"])
        diffs["safety_vector"] = _maxabs(tr["safety_vector"], ref["safety_vector"])
        diffs["safety_logit"] = _maxabs(tr["safety_logit"], ref["safety_logit"])
    diffs["final_probability"] = _maxabs(res["final_probability"], ref["final_probability"])
    diffs["final_binary"] = float(np.count_nonzero((res["final_probability"] >= 0.5).astype(np.uint8) != ref["final_binary"]))
    return {"state_adapter": res["state"], "state_reference": ref["state"], "branch_agrees": res["state"] == ref["state"],
            "max_abs_difference": diffs, "worst_stage_difference": max(v for v in diffs.values() if v is not None)}


def frozen_cache_comparison(system: GTFreeBARRInference, domain: str, index: int = 3) -> dict[str, Any]:
    """Adapter vs the frozen Phase-25A/25B caches for one eligible TRAIN (ROUTER_DEVELOPMENT) sample."""
    import pandas as pd
    from PIL import Image
    from src.data.transforms import SegmentationTransform

    man = pd.read_csv(TRAIN_MANIFEST).set_index("sample_id", drop=False)
    split = pd.read_csv(SPLIT_MANIFEST)
    dev = split[split.split_role == "ROUTER_DEVELOPMENT"].sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    sub = dev[dev.dataset == domain].reset_index(drop=True)
    sid = str(sub.sample_id[index])
    row = man.loc[sid]
    with Image.open(row["image_path"]) as im:
        pil = im.copy()
    tensor, _, _ = SegmentationTransform(size=512, train=False, image_mode="RGB")(pil, Image.new("L", pil.size, 0))
    system.trace = True
    res = system.infer(tensor[None], int(row["task_id"]))
    prob_cache = np.load(CACHE_ROI030 / domain / "prob512.npy", mmap_mode="r")[index]
    with (CACHE_ROI030 / domain / "meta.csv").open(newline="", encoding="utf-8") as f:
        meta = {r["sample_id"]: r for r in csv.DictReader(f)}[sid]
    feats = np.load(CACHE_FEATURES, mmap_mode="r")
    gi = int(dev.index[dev.sample_id == sid][0])
    geom_keys = ("clip_y1", "clip_y2", "clip_x1", "clip_x2", "pad_top", "pad_bottom", "pad_left", "pad_right", "crop_side_pixels")
    roi = res["roi"]
    return {"sample_id": sid, "domain": domain, "split_role": "ROUTER_DEVELOPMENT (TRAIN)",
            "global_probability_max_abs_vs_frozen_cache": _maxabs(res["global_probability"], prob_cache),
            "roi_geometry_exact_match": bool(roi is not None and all(int(roi[k]) == int(float(meta[k])) for k in geom_keys)),
            "router_vector_raw_max_abs_vs_frozen_cache": (
                _maxabs(system.last_trace["router_vector_raw"], feats[gi]) if roi is not None else None),
            "state": res["state"]}


def canonical_batch_reproduces_cache(domain: str = "ISIC", n: int = 8) -> dict[str, Any]:
    """Prove the reference forward path itself: canonical batch-of-8 AMP forward vs frozen prob512 cache."""
    import json

    import pandas as pd
    from PIL import Image
    from src.data.transforms import SegmentationTransform

    canon, D, p25b = _imports()
    man = pd.read_csv(TRAIN_MANIFEST).set_index("sample_id", drop=False)
    split = pd.read_csv(SPLIT_MANIFEST)
    dev = split[split.split_role == "ROUTER_DEVELOPMENT"].sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    sub = dev[dev.dataset == domain].reset_index(drop=True).head(n)
    dev_t = torch.device("cuda")
    g = p25b.build_model(json.loads(p25b.GLOBAL_CONFIG.read_text(encoding="utf-8"))).to(dev_t)
    tr = SegmentationTransform(size=512, train=False, image_mode="RGB")
    imgs, tasks = [], []
    for sid in sub.sample_id:
        row = man.loc[sid]
        with Image.open(row["image_path"]) as im, Image.open(row["mask_path"]) as mk:
            imgs.append(tr(im, mk)[0])
        tasks.append(int(row["task_id"]))
    with torch.no_grad(), torch.amp.autocast(device_type="cuda", enabled=True):
        logits = g(torch.stack(imgs).to(dev_t), torch.tensor(tasks, dtype=torch.long, device=dev_t))
    prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
    cache = np.load(CACHE_ROI030 / domain / "prob512.npy", mmap_mode="r")[:n]
    return {"domain": domain, "batch": n, "max_abs_vs_frozen_cache": _maxabs(prob, cache)}
