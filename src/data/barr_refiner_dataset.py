"""Phase 25A — BARR regional-refiner crop dataset.

Reads the frozen TRAIN-only global cache and yields the 4-channel refiner input
``[R, G, B, p_global_crop]`` plus the 256x256 ground-truth training target.

Cache root
----------
``DEFAULT_CACHE_ROOT`` is the **canonical ROI-0.30** cache
(``data_cache/phase25a_barr_roi030_cache``), which is built with the
repository-authoritative Phase-24 v1.1 ROI proposal threshold 0.30. The earlier
``data_cache/phase25a_global_cache`` (ROI-0.50) is preserved as
``NONCANONICAL_PROTOCOL_DEVIATION__ROI_THRESHOLD_0P50`` and must only be passed
explicitly for provenance/debugging, never for canonical science.

Augmentation is the EXACT augmentation inherited from the frozen Phase-20/21
pipeline (``src.data.transforms.SegmentationTransform(train=True)``):

    horizontal mirror p=0.5  -> ImageOps.mirror
    rotation uniform(-5,+5)  -> Image.rotate (bilinear image / nearest mask)
    brightness uniform(0.9,1.1) -> ImageEnhance.Brightness
    contrast   uniform(0.9,1.1) -> ImageEnhance.Contrast

applied consistently to the RGB crop, the p_global crop and the GT geometry.

Vertical flip and 90-degree rotation are **NOT_INHERITED** and are never applied.

Determinism
-----------
Per-sample augmentation is a pure function of ``(base_seed, epoch, sample_id)``,
so a resumed run reproduces every epoch bit-exactly and is independent of worker
count and of how many epochs preceded it.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageEnhance, ImageOps
from torch.utils.data import Dataset

from src.data.barr_roi import REGIONAL_INPUT_RESOLUTION

__all__ = [
    "BARRRefinerCropDataset",
    "barr_refiner_collate",
    "derive_sample_seed",
    "DEFAULT_CACHE_ROOT",
    "NONCANONICAL_CACHE_ROOT",
    "FLIP_PROBABILITY",
    "ROTATION_DEGREES",
    "BRIGHTNESS",
    "CONTRAST",
]

# inherited constants (asserted against src/data/transforms.py by the binding audit)
FLIP_PROBABILITY = 0.5
ROTATION_DEGREES = 5.0
BRIGHTNESS = 0.1
CONTRAST = 0.1

# canonical: built with the ROI proposal threshold 0.30
DEFAULT_CACHE_ROOT = Path(r"D:/Softfors/jup/data_cache/phase25a_barr_roi030_cache")
# superseded: built with the noncanonical ROI threshold 0.50 — provenance/debugging only
NONCANONICAL_CACHE_ROOT = Path(r"D:/Softfors/jup/data_cache/phase25a_global_cache")
# backwards-compatible alias for the canonical root
CACHE_ROOT = DEFAULT_CACHE_ROOT


def derive_sample_seed(base_seed: int, epoch: int, sample_id: str) -> int:
    """Deterministic per-sample augmentation seed."""
    key = f"{base_seed}:{int(epoch)}:{sample_id}".encode()
    return int(hashlib.sha256(key).hexdigest()[:16], 16)


class BARRRefinerCropDataset(Dataset):
    """Crop dataset over one fold manifest, restricted to action-available samples."""

    def __init__(self, manifest_csv, cache_root: Path = DEFAULT_CACHE_ROOT, train: bool = True,
                 base_seed: int = 42, out_size: int = REGIONAL_INPUT_RESOLUTION,
                 epoch: int = 0):
        self.train = bool(train)
        self.base_seed = int(base_seed)
        self.epoch = int(epoch)
        self.out_size = int(out_size)
        self.cache_root = Path(cache_root)

        frame = pd.read_csv(manifest_csv)
        self._arrays: dict[str, dict] = {}
        self._index: dict[str, tuple[str, int]] = {}
        kept: list[dict] = []

        for domain in sorted(frame["dataset"].unique()):
            ddir = self.cache_root / domain
            meta = pd.read_csv(ddir / "meta.csv")
            pos = {str(s): i for i, s in enumerate(meta["sample_id"].astype(str))}
            self._arrays[domain] = {
                "rgb_crop": np.load(ddir / "rgb_crop.npy", mmap_mode="r"),
                "prob_crop": np.load(ddir / "prob_crop.npy", mmap_mode="r"),
                "gt_crop": np.load(ddir / "gt_crop.npy", mmap_mode="r"),
                "action": np.load(ddir / "action.npy"),
                "meta": meta,
            }
            for _, row in frame[frame["dataset"] == domain].iterrows():
                sid = str(row["sample_id"])
                if sid not in pos:
                    continue
                idx = pos[sid]
                if int(self._arrays[domain]["action"][idx]) != 1:
                    continue          # FORCED_SKIP: global-empty, never enters refiner training
                self._index[sid] = (domain, idx)
                kept.append({"sample_id": sid, "dataset": domain,
                             "task_id": int(row["task_id"])})

        self.samples = pd.DataFrame(kept).reset_index(drop=True)
        self.split = "TRAIN"

    def __len__(self) -> int:
        return len(self.samples)

    def class_distribution(self) -> dict:
        return {k: int(v) for k, v in self.samples["dataset"].value_counts().items()}

    def set_epoch(self, epoch: int) -> None:
        self.epoch = int(epoch)

    # ------------------------------------------------------------------ #
    def _augment(self, rgb, prob, gt, rng):
        """Apply the inherited augmentation to the crop triplet."""
        # 1. horizontal mirror (p=0.5) — exact, no resampling
        if rng.random() < FLIP_PROBABILITY:
            rgb = rgb[:, :, ::-1]
            prob = prob[:, :, ::-1]
            gt = gt[:, :, ::-1]
        # 2. rotation, continuous uniform(-5, +5) degrees
        angle = rng.uniform(-ROTATION_DEGREES, ROTATION_DEGREES)
        rgb_u8 = np.clip(np.rint(rgb * 255.0), 0, 255).astype(np.uint8).transpose(1, 2, 0)
        img = Image.fromarray(np.ascontiguousarray(rgb_u8), mode="RGB")
        img = img.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=0)
        prb = Image.fromarray(np.ascontiguousarray(prob[0], dtype=np.float32), mode="F")
        prb = prb.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
        tgt = Image.fromarray(np.ascontiguousarray(gt[0], dtype=np.float32), mode="F")
        tgt = tgt.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
        # 3. brightness then contrast (RGB only), exactly as inherited
        img = ImageEnhance.Brightness(img).enhance(
            rng.uniform(1.0 - BRIGHTNESS, 1.0 + BRIGHTNESS))
        img = ImageEnhance.Contrast(img).enhance(
            rng.uniform(1.0 - CONTRAST, 1.0 + CONTRAST))
        rgb_out = np.asarray(img, dtype=np.float32).transpose(2, 0, 1) / 255.0
        prob_out = np.asarray(prb, dtype=np.float32)[None, ...]
        gt_out = np.asarray(tgt, dtype=np.float32)[None, ...]
        return rgb_out, prob_out, gt_out

    def __getitem__(self, index: int) -> dict:
        row = self.samples.iloc[index]
        sid = str(row["sample_id"])
        domain, idx = self._index[sid]
        arrs = self._arrays[domain]

        rgb = np.asarray(arrs["rgb_crop"][idx], dtype=np.float32) / 255.0
        prob = np.asarray(arrs["prob_crop"][idx], dtype=np.float32)
        gt = (np.asarray(arrs["gt_crop"][idx], dtype=np.float32) > 0.5).astype(np.float32)

        if self.train:
            rng = __import__("random").Random(derive_sample_seed(self.base_seed, self.epoch, sid))
            rgb, prob, gt = self._augment(rgb, prob, gt, rng)

        inputs = np.concatenate([rgb, prob], axis=0)          # (4, 256, 256)
        # order="C" + copy=True is REQUIRED: the ufunc in _augment preserves the
        # input memory layout, so a transposed HWC array would otherwise yield a
        # non-contiguous tensor (stride (1,1024,4)) that forces a hidden copy in
        # every conv. It also makes the PIL-backed read-only target writable.
        return {
            "input": torch.from_numpy(np.array(inputs, dtype=np.float32, order="C", copy=True)),
            "target": torch.from_numpy(np.array(gt, dtype=np.float32, order="C", copy=True)),
            "sample_id": sid,
            "dataset": domain,
            "task_id": int(row["task_id"]),
        }


def barr_refiner_collate(batch):
    return {
        "input": torch.stack([b["input"] for b in batch], dim=0),
        "target": torch.stack([b["target"] for b in batch], dim=0),
        "sample_id": [b["sample_id"] for b in batch],
        "dataset": [b["dataset"] for b in batch],
        "task_id": torch.tensor([b["task_id"] for b in batch], dtype=torch.long),
    }
