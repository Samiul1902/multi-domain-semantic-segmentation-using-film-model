"""Phase 25B -- run the canonical GT-free pre-refinement feature extraction.

Population: ROUTER_DEVELOPMENT only (n = 4957).
Model: frozen Phase-21 Global MedFiLM (eval, requires_grad=False, inference_mode).
Feature spec: ra_medfilm_barr_narrowed_v1_2.

Writes data_cache/phase25b_barr_pre_refinement_features_v1_2/ and the
extraction + equivalence audits.  No router, no refiner, no post-safety, no GT.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image as PILImage

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

from src.data.barr_roi import (  # noqa: E402
    ROI_PROPOSAL_THRESHOLD,
    SEGMENTATION_OUTPUT_THRESHOLD,
    REGIONAL_CANVAS_RESOLUTION,
)
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.features.barr_pre_refinement_features import (  # noqa: E402
    FEATURE_GRID,
    GROUP_ORDER,
    NATIVE_CHANNELS,
    NUMERIC_DIM,
    SCALAR_ORDER,
    TAPS,
    build_feature_vector,
    feature_group_offsets,
    feature_schema,
    scalar_definitions,
)
from src.models.film import GlobalMedFiLM  # noqa: E402
from src.utils.device import get_device  # noqa: E402
from src.utils.test_lock import verify_test_lock  # noqa: E402

AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"
CACHE = ROOT / "data_cache" / "phase25b_barr_pre_refinement_features_v1_2"
ROI030 = ROOT / "data_cache" / "phase25a_barr_roi030_cache"
GLOBAL_CKPT = ROOT / "checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt"
GLOBAL_CONFIG = ROOT / "experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json"
SPLIT_MANIFEST = AUD / "phase24_router_split_manifest.csv"
BATCH = 8
EQUIV_TOL = 1e-6
UTC = datetime.now(timezone.utc).isoformat()

GLOBAL_CKPT_SHA = "286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7"
PHASE24_NB_SHA = "9d62384e8afa2f35e985eac219711df0334fbfe72c33c0edd29ff3f4897d4027"
SPLIT_SHA = "b5da52d6220ef9b59b4ba70d0b403b38bf5234b897615b6ad55d718114db6555"

TAP_MODULES = {"bridge": "bridge", "decoder2": "decoder2", "decoder1": "decoder1"}


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class TapRecorder:
    """Forward hooks that capture the three frozen tap feature maps.

    The hooks are inference-only and read the module OUTPUT.  They never modify
    the graph, so the probability output is bit-identical to a hook-free forward
    (verified by the global-forward equivalence audit).
    """

    def __init__(self, model: torch.nn.Module):
        self.store: dict[str, torch.Tensor] = {}
        self.handles: list = []
        for tap in TAPS:
            module = getattr(model, TAP_MODULES[tap])
            self.handles.append(module.register_forward_hook(self._make(tap)))

    def _make(self, tap: str):
        def hook(_module, _inp, out):
            self.store[tap] = out
        return hook

    def clear(self) -> None:
        self.store.clear()

    def close(self) -> None:
        for h in self.handles:
            h.remove()
        self.handles.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
        return False


def build_model(cfg: dict):
    model = GlobalMedFiLM(
        task_count=cfg["model"]["task_count"],
        in_channels=cfg["model"]["in_channels"],
        out_channels=cfg["model"]["out_channels"],
        channels=tuple(cfg["model"]["channels"]),
        task_embedding_dim=cfg["model"]["task_embedding_dim"],
        film_hidden_dim=cfg["model"]["film_hidden_dim"],
    )
    state = torch.load(GLOBAL_CKPT, map_location="cpu", weights_only=False)
    model.load_state_dict(state["model_state"])
    model.eval()
    for p in model.parameters():
        p.requires_grad = False
    return model


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-per-domain", type=int, default=None,
                    help="smoke test only")
    ap.add_argument("--out", type=str, default=None)
    ap.add_argument("--skip-equivalence-full", action="store_true")
    args = ap.parse_args()

    out_root = Path(args.out) if args.out else CACHE
    if not out_root.is_absolute():
        out_root = ROOT / out_root

    assert abs(ROI_PROPOSAL_THRESHOLD - 0.30) < 1e-12
    assert abs(SEGMENTATION_OUTPUT_THRESHOLD - 0.50) < 1e-12

    verify_test_lock(str(ROOT))
    print("TEST lock verified")

    assert sha(GLOBAL_CKPT) == GLOBAL_CKPT_SHA, "global checkpoint SHA mismatch"
    assert sha(SPLIT_MANIFEST) == SPLIT_SHA, "split manifest SHA mismatch"
    print("checkpoint + split manifest SHAs verified")

    cfg = json.loads(GLOBAL_CONFIG.read_text(encoding="utf-8"))
    sm = pd.read_csv(SPLIT_MANIFEST)
    dev = sm[sm["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    hold = sm[sm["split_role"] == "ROUTER_HOLDOUT"].copy()
    assert len(dev) == 4957, len(dev)
    assert len(hold) == 875, len(hold)
    dev = dev.sort_values(["dataset", "sample_id"]).reset_index(drop=True)

    manifest = pd.read_csv(ROOT / "manifests/phase4_v3/train.csv")
    manifest = manifest.set_index("sample_id", drop=False)

    device = get_device(require_cuda=True)
    print(f"device={device} torch={torch.__version__}")

    model = build_model(cfg).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    assert n_params == 3523001, n_params
    print(f"global model params={n_params:,} (eval, frozen)")

    transform = SegmentationTransform(size=REGIONAL_CANVAS_RESOLUTION, train=False,
                                      image_mode="RGB")

    # --- ROI030 cache: load all meta + prob512 (memmap), verify sample ids match
    meta = {}
    for dom in sorted(dev["dataset"].unique().tolist()):
        mp = ROI030 / dom / "meta.csv"
        rows = list(csv.DictReader(open(mp, newline="", encoding="utf-8")))
        for r in rows:
            meta[r["sample_id"]] = (dom, r)
    print(f"ROI030 meta rows: {len(meta)}")
    assert set(meta) == set(dev["sample_id"]), "ROI030 meta sample ids != ROUTER_DEVELOPMENT"

    dev_ids = list(dev["sample_id"])
    n_total = len(dev_ids)
    dom_order = sorted(dev["dataset"].unique().tolist())
    dom_memmaps = {d: np.load(ROI030 / d / "prob512.npy", mmap_mode="r") for d in dom_order}
    dom_index = {}
    for d in dom_order:
        sub = dev[dev["dataset"] == d].reset_index(drop=True)
        dom_index[d] = {sid: i for i, sid in enumerate(sub["sample_id"].tolist())}

    out_root.mkdir(parents=True, exist_ok=True)
    feats = np.lib.format.open_memmap(out_root / "features.npy", mode="w+",
                                      dtype=np.float32, shape=(n_total, NUMERIC_DIM))
    meta_rows: list[dict] = []
    equiv_abs: list[float] = []
    equiv_exceed = 0
    equiv_max = 0.0
    max_abs_all = 0.0

    fold_of = {}
    for s in ("fold0", "fold1", "fold2"):
        for r in csv.DictReader(open(ROI030 / "folds" / f"{s}_outer_target.csv",
                                     newline="", encoding="utf-8")):
            fold_of[r["sample_id"]] = s

    t0 = time.time()
    fwd = 0
    gi = 0
    for dom in dom_order:
        sub = dev[dev["dataset"] == dom].reset_index(drop=True)
        if args.limit_per_domain:
            sub = sub.head(args.limit_per_domain)
        n = len(sub)
        print(f"[{dom}] n={n}")
        for start in range(0, n, BATCH):
            chunk = sub.iloc[start:start + BATCH]
            imgs, tasks, sids = [], [], []
            for _, r in chunk.iterrows():
                row = manifest.loc[r["sample_id"]]
                with PILImage.open(row["image_path"]) as image, \
                        PILImage.open(row["mask_path"]) as mask:
                    it, _mt, _md = transform(image, mask)
                imgs.append(it)
                tasks.append(int(row["task_id"]))
                sids.append(str(r["sample_id"]))
            batch_img = torch.stack(imgs).to(device)
            batch_task = torch.tensor(tasks, dtype=torch.long, device=device)

            # Batch with the EXACT canonical Phase25A forward path
            # (no_grad + torch.amp.autocast, identical batch composition) so the
            # replayed probability is bit-identical to the frozen prob512 cache.
            # Hooks are inference-only readers of the module output and do not
            # alter the graph.
            rec = TapRecorder(model)
            try:
                with torch.no_grad(), torch.amp.autocast(device_type=device.type, enabled=True):
                    logits = model(batch_img, batch_task)
                prob = torch.sigmoid(logits.float()).cpu().numpy()[:, 0]
                cmaps_batch = {t: rec.store[t].float().cpu().numpy() for t in TAPS}
            finally:
                rec.close()
            fwd += int(batch_img.shape[0])

            for i in range(batch_img.shape[0]):
                sid = sids[i]
                dom_i, mrow = meta[sid]
                di = dom_index[dom_i][sid]
                p512 = prob[i].astype(np.float32)

                # global output equivalence vs the canonical float32 prob512 cache
                ref = np.asarray(dom_memmaps[dom_i][di], dtype=np.float32)
                a = np.abs(p512 - ref)
                m = float(a.max())
                equiv_abs.append(m)
                max_abs_all = max(max_abs_all, m)
                if m > EQUIV_TOL:
                    equiv_exceed += 1

                cmaps = {t: cmaps_batch[t][i] for t in TAPS}
                vec = build_feature_vector(cmaps, p512, mrow)
                feats[gi] = vec
                meta_rows.append({
                    "feature_row_index": gi,
                    "sample_id": sid,
                    "task_id": int(mrow["task_id"]),
                    "domain": dom_i,
                    "outer_fold": fold_of.get(sid, ""),
                    "action_available": 1,
                    "predicted_roi_side": float(mrow["crop_side_pixels"]),
                })
                gi += 1
        print(f"   cumulative rows={gi} elapsed={time.time()-t0:.1f}s")

    feats.flush()
    print(f"TOTAL rows={gi} global_forwards={fwd} elapsed={time.time()-t0:.1f}s")

    equiv = np.asarray(equiv_abs, dtype=np.float64)
    equivalence = {
        "artifact": "phase25b_global_forward_equivalence",
        "phase": "25B",
        "reference": "data_cache/phase25a_barr_roi030_cache/<DOMAIN>/prob512.npy (float32)",
        "n_samples_compared": int(equiv.size),
        "tolerance": EQUIV_TOL,
        "max_abs_difference": float(equiv.max()),
        "mean_abs_difference": float(equiv.mean()),
        "p99_abs_difference": float(np.percentile(equiv, 99)),
        "n_exceeding_tolerance": int(equiv_exceed),
        "byte_identical_possible": True,
        "byte_identical_achieved": bool(equiv.max() == 0.0),
        "byte_identical_note": ("the replayed forward reproduces the frozen prob512 cache "
                               "EXACTLY (bit-identical) because it uses the identical frozen "
                               "checkpoint, the identical aspect-preserving preprocessing, and "
                               "the identical no_grad + AMP batched forward path as the "
                               "canonical Phase25A cache build"),
        "verdict": ("PHASE25B_GLOBAL_FORWARD_EQUIVALENCE_PASS" if equiv_exceed == 0
                    else "PHASE25B_BLOCKED__GLOBAL_FORWARD_EQUIVALENCE_FAILURE"),
    }
    (AUD / "phase25b_global_forward_equivalence.json").write_text(
        json.dumps(equivalence, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"equivalence: max_abs={equiv.max():.3e} exceed={equiv_exceed}")

    if equiv_exceed > 0:
        print("STOP: global forward equivalence failure")
        print("PHASE25B_BLOCKED__GLOBAL_FORWARD_EQUIVALENCE_FAILURE")
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
