#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Phase 29 — PHASE D STAGE 2: shared fixed-G VAL808 cache (§6–§10).

Builds the shared fixed-G cache EXACTLY ONCE.  The canonical global model G is
FIXED (never retrained, never tuned) and is the ONLY learned component that
sees the VAL808 images in this phase.  The cache is seed-INDEPENDENT: it holds

    val808_global_prob_f16.npy        [808, 512, 512] float16
    val808_router_deep_features_f32.npy  [808, 192]  float32
    val808_router_scalars_f32.npy     [808, 10]      float32   (GT-free)
    val808_roi_geometry.json          per-sample ROI-0.30 geometry (from G only)

GT masks are NEVER opened here.  The cache is reused by all three seeds.

§7  shared_G_logical_passes = 1, shared_G_samples = 808,
    runs_once_not_per_seed = true, G_retrained = false
§8  exact cache schema (above)
§9  gt_derived_information_persisted = false
§10 cache integrity audit -> phase29_val808_shared_cache_integrity.json

Run: D:/Softfors/jup/.venv/Scripts/python.exe scripts/analysis/phase29_phase_d_cache.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase29_phase_d_common as D  # noqa: E402

sys.path.insert(0, str(D.ROOT))  # so `src.*` imports resolve

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import torch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from src.data.barr_roi import (  # noqa: E402
    REGIONAL_CANVAS_RESOLUTION,
    roi_geometry,
    threshold_probability,
)
from src.features.barr_pre_refinement_features import (  # noqa: E402
    DEEP_DIM,
    SCALAR_DIM,
    build_feature_vector,
)
from src.models.film.global_medfilm import GlobalMedFiLM  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

say = print

TAPS = ("bridge", "decoder2", "decoder1")
TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}


# --------------------------------------------------------------------------- #
class TapRecorder:
    """Inference-only forward hooks on the three frozen G taps (read outputs)."""

    def __init__(self, model: torch.nn.Module):
        self.store = {}
        self.handles = []
        for tap in TAPS:
            module = getattr(model, TAP_MODULES[tap])
            self.handles.append(module.register_forward_hook(self._make(tap)))

    def _make(self, tap):
        def hook(_m, _i, out):
            self.store[tap] = out
        return hook

    def close(self):
        for h in self.handles:
            h.remove()
        self.handles.clear()


def image_only_transform(image, size: int = REGIONAL_CANVAS_RESOLUTION) -> torch.Tensor:
    """Image-side of SegmentationTransform(train=False, image_mode='RGB').

    Reproduces EXACTLY the canonical image path (aspect-preserving bilinear
    resize + centre pad + permute(2,0,1) / 255.0) WITHOUT opening the paired GT
    mask, so this stage performs ZERO GT/mask-file reads.
    """
    image = image.convert("RGB")
    width, height = image.size
    scale = min(size / width, size / height)
    rw, rh = max(1, round(width * scale)), max(1, round(height * scale))
    image = image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (size - rw) // 2, (size - rh) // 2
    right, bottom = size - rw - left, size - rh - top
    image = ImageOps.expand(image, (left, top, right, bottom))
    arr = np.asarray(image, dtype=np.float32).copy()
    return torch.from_numpy(arr).permute(2, 0, 1) / 255.0


# --------------------------------------------------------------------------- #
def load_global_G(device):
    import json
    cfg = json.loads(
        (D.ROOT / D.G_EXPERIMENT_CONFIG).read_text(encoding="utf-8"))
    g = GlobalMedFiLM(
        task_count=cfg["model"]["task_count"],
        in_channels=cfg["model"]["in_channels"],
        out_channels=cfg["model"]["out_channels"],
        channels=tuple(cfg["model"]["channels"]),
        task_embedding_dim=cfg["model"]["task_embedding_dim"],
        film_hidden_dim=cfg["model"]["film_hidden_dim"],
    )
    st = torch.load(D.ROOT / D.G_CHECKPOINT, map_location="cpu", weights_only=False)
    g.load_state_dict(st["model_state"])
    g.eval()
    g.requires_grad_(False)
    g.to(device)
    n = sum(p.numel() for p in g.parameters())
    say(f"  GlobalMedFiLM params={n}")
    return g, n


# --------------------------------------------------------------------------- #
def main() -> int:
    t0 = time.time()
    say("=" * 78)
    say("PHASE 29 -- PHASE D STAGE 2: shared fixed-G VAL808 cache")
    say("=" * 78)

    verify_test_lock(str(D.ROOT))
    say("TEST lock verified")

    # mask the ROUTER_HOLDOUT + TEST populations at the source level: neither is
    # named anywhere in this stage, and the only population read is VAL808.
    assert abs(D.ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12
    assert abs(D.SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12

    # ---- re-verify immutability inside execution -------------------------- #
    rh = D.rehash_predecessors()
    assert rh["drift_count"] == 0, f"predecessor drift: {rh['drift']}"
    gp_sha = D.sha256_file(D.ROOT / D.PHASE27_GLOBAL_PROB)
    assert gp_sha == D.PHASE27_GLOBAL_PROB_SHA, gp_sha
    say("immutability re-verified (no drift)")

    device = get_device(require_cuda=True)
    assert str(device).startswith("cuda"), device
    say(f"device={device} torch={torch.__version__} cuda={torch.version.cuda}")

    g, g_params = load_global_G(device)

    # ---- population (VAL808 only) ----------------------------------------- #
    rows = D.canonical_val808_order()
    df = pd.DataFrame(rows)
    df["sample_id"] = df["sample_id"].astype(str)
    df = df.sort_values(["dataset", "sample_id"]).reset_index(drop=True)
    assert len(df) == D.VAL808_N, len(df)
    dom_n = df["dataset"].value_counts().to_dict()
    assert dom_n == D.VAL808_DOMAIN_N, dom_n
    sample_ids = df["sample_id"].tolist()
    assert len(set(sample_ids)) == len(sample_ids), "duplicate sample ids"
    pos = {sid: i for i, sid in enumerate(sample_ids)}
    say(f"VAL808 n={len(df)} domains={dom_n}")

    # ---- allocate cache --------------------------------------------------- #
    D.CACHE29D.mkdir(parents=True, exist_ok=True)
    global_prob_f16 = np.lib.format.open_memmap(
        D.CACHE29D / D.SHARED_CACHE_FILES["global_prob"], mode="w+",
        dtype=np.float16,
        shape=(len(df), REGIONAL_CANVAS_RESOLUTION, REGIONAL_CANVAS_RESOLUTION))
    deep_f32 = np.lib.format.open_memmap(
        D.CACHE29D / D.SHARED_CACHE_FILES["router_deep_features"], mode="w+",
        dtype=np.float32, shape=(len(df), DEEP_DIM))
    scal_f32 = np.lib.format.open_memmap(
        D.CACHE29D / D.SHARED_CACHE_FILES["router_scalars"], mode="w+",
        dtype=np.float32, shape=(len(df), SCALAR_DIM))

    roi_geom: dict[str, dict | None] = {}
    n_deep_written = 0
    n_scalar_written = 0
    n_no_roi = 0
    domain_batches: dict[str, dict] = {}
    global_forwards = 0

    for dom in D.domain_order():
        sub = df[df["dataset"] == dom].reset_index(drop=True)
        n = len(sub)
        nb = (n + 7) // 8
        sizes = [8] * nb
        sizes[-1] = n - 8 * (nb - 1)
        domain_batches[dom] = {
            "n": n, "batches": nb, "last_batch_size": sizes[-1],
            "total_batches": nb, "canonical_order": "(dataset asc, sample_id asc)",
        }
        say(f"\n[{dom}] n={n} batches={nb} last={sizes[-1]}")
        for start in range(0, n, 8):
            chunk = sub.iloc[start:start + 8]
            imgs, tasks = [], []
            for _, row in chunk.iterrows():
                # IMAGE ONLY.  No mask path is ever opened in this stage.
                with Image.open(row["image_path"]) as image:
                    it = image_only_transform(image, REGIONAL_CANVAS_RESOLUTION)
                imgs.append(it)
                tasks.append(D.VAL808_TASK_ID[row["dataset"]])
            batch_img = torch.stack(imgs).to(device)
            batch_task = torch.tensor(tasks, dtype=torch.long, device=device)

            rec = TapRecorder(g)
            try:
                # canonical frozen G path: FP32 eval, inference_mode, no autocast
                with torch.inference_mode():
                    logits = g(batch_img, batch_task)
                prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
                cmaps_batch = {t: rec.store[t].float().cpu().numpy() for t in TAPS}
            finally:
                rec.close()
            global_forwards += int(batch_img.shape[0])

            for i in range(batch_img.shape[0]):
                row = chunk.iloc[i]
                sid = str(row["sample_id"])
                gi = pos[sid]
                p_global = prob[i].astype(np.float32)
                # decision in float32 BEFORE any float16 storage cast
                _ = threshold_probability(p_global, D.SEGMENTATION_OUTPUT_THRESHOLD)
                global_prob_f16[gi] = p_global.astype(np.float16)

                geom = roi_geometry(p_global, D.ROI_PROPOSAL_THRESHOLD)
                if geom is None:
                    n_no_roi += 1
                    roi_geom[sid] = None
                    deep_f32[gi] = 0.0
                    scal_f32[gi] = 0.0
                    continue

                roi_geom[sid] = {
                    k: (int(v) if isinstance(v, (int, np.integer)) else
                        (float(v) if isinstance(v, (float, np.floating)) else v))
                    for k, v in geom.items()
                }
                cmaps = {t: cmaps_batch[t][i] for t in TAPS}
                vec202 = build_feature_vector(cmaps, p_global, geom)
                assert vec202.shape == (D.ROUTER_NUMERIC_DIM,), vec202.shape
                deep_f32[gi] = vec202[:D.ROUTER_DEEP_DIM].astype(np.float32)
                scal_f32[gi] = vec202[D.ROUTER_DEEP_DIM:].astype(np.float32)
                n_deep_written += 1
                n_scalar_written += 1

            say(f"   {start + batch_img.shape[0]:4d}/{n}  "
                f"global_fwd={global_forwards} elapsed={time.time()-t0:.0f}s")

    global_prob_f16.flush()
    deep_f32.flush()
    scal_f32.flush()

    D.write_json({
        "artifact": "phase29_val808_roi_geometry",
        "phase": 29, "stage": "SHARED_FIXED_G_CACHE",
        "method": D.METHOD,
        "population": "VAL808", "population_n": len(df),
        "sample_id_order": sample_ids,
        "roi_proposal_threshold": D.ROI_PROPOSAL_THRESHOLD,
        "roi_expansion": 1.50,
        "geometry_source": "regenerated_from_stored_global_probability__NOT_GT",
        "gt_derived_information_persisted": False,
        "n_no_roi": n_no_roi,
        "geometry": roi_geom,
    }, D.CACHE29D / D.SHARED_CACHE_FILES["roi_geometry"])

    assert global_forwards == D.SHARED_G_SAMPLES, global_forwards
    assert n_scalar_written + n_no_roi == D.SHARED_G_SAMPLES

    summary = {
        "artifact": "phase29_val808_shared_cache_build_summary",
        "phase": 29, "stage": "SHARED_FIXED_G_CACHE",
        "method": D.METHOD, "specification_revision": D.SPEC_REVISION,
        "generated_utc": D.now_utc(),
        "population": "VAL808", "population_n": len(df),
        "domain_counts": {k: int(v) for k, v in dom_n.items()},
        "domain_task_id": D.VAL808_TASK_ID,
        "shared_G_logical_passes": D.SHARED_G_LOGICAL_PASSES,
        "shared_G_samples": D.SHARED_G_SAMPLES,
        "runs_once_not_per_seed": D.RUNS_ONCE_NOT_PER_SEED,
        "G_retrained": D.G_RETRAINED,
        "global_forward_count": global_forwards,
        "deep_feature_rows_written": n_deep_written,
        "scalar_rows_written": n_scalar_written,
        "n_no_roi": n_no_roi,
        "domain_batches": domain_batches,
        "val808_images_read": len(df),
        "val808_gt_reads": 0,
        "gt_derived_information_persisted": False,
        "device": str(device),
        "autocast_enabled": False,
        "inference_mode": True,
        "numeric_mode": "FP32 eval, torch.inference_mode(), no autocast",
        "batch_size": 8,
        "global_params": g_params,
        "G_checkpoint_sha256": D.G_CHECKPOINT_SHA,
        "elapsed_seconds": round(time.time() - t0, 1),
        "all_pass": True,
    }
    D.write_json(summary, D.AUD / "phase29_val808_shared_cache_build_summary.json")

    say("")
    say("=" * 78)
    say(f"CACHE BUILT  n={len(df)} global_forwards={global_forwards} "
        f"wrote deep={n_deep_written} scalars={n_scalar_written} "
        f"no_roi={n_no_roi}")
    say(f"elapsed={time.time()-t0:.0f}s")
    say("=" * 78)
    say("PHASE29_PHASE_D_SHARED_G_CACHE_BUILT")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
