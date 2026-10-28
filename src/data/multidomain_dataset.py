"""
Harmonized multi-domain segmentation dataset (Phase 19, Stage B).

This module is the single implementation of the Phase-19 harmonized sample
contract for the four target domains:

    ISIC 2018 (task_id 0, dermoscopy,      RGB)
    BUSI      (task_id 1, ultrasound,      L)
    Kvasir-SEG(task_id 2, endoscopy,       RGB)
    KUB       (task_id 3, radiograph,      L / RGB mixed)

The sample contract is:

    image : float32 tensor (C, H, W), C in {1, 3}, values in [0, 1]
    mask  : float32 tensor (1, H, W), values in {0, 1}

Foreground is defined once, canonically, by ``src.utils.targets.binarize_mask``
(``mask > 0``). Native masks use heterogeneous nonzero label vocabularies; code
must NEVER test ``mask == 1``.

Governance
----------
``split="TEST"`` is rejected at construction time and again by the loader
(``src.data.loaders.create_loader``). Phase 19 performs zero TEST reads.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image
from torch.utils.data import Dataset

from src.data.transforms import SegmentationTransform

# --------------------------------------------------------------------------- #
# Canonical identities (verified from manifests/phase4_v3/*.csv, not memory)
# --------------------------------------------------------------------------- #
TASK_ID = {"ISIC": 0, "BUSI": 1, "KVASIR": 2, "KUB": 3}
TASK_ID_TO_NAME = {v: k for k, v in TASK_ID.items()}
DATASET_ORDER = ["ISIC", "BUSI", "KVASIR", "KUB"]

#: Canonical model-input channel policy. The Phase-19 contract freezes BOTH
#: deterministic converters so a later phase can select without re-deriving:
#:   "GRAYSCALE_1CH" -> convert("L")
#:   "RGB_3CH"       -> convert("RGB") (native L replicated to 3 channels)
DEFAULT_CHANNEL_POLICY = "RGB_3CH"
CHANNEL_POLICIES = ("GRAYSCALE_1CH", "RGB_3CH")


@dataclass(frozen=True)
class HarmonizedSample:
    """A single harmonized multi-domain sample."""

    image: torch.Tensor          # (C, H, W) float32 in [0, 1]
    mask: torch.Tensor           # (1, H, W) float32 in {0, 1}
    dataset: str
    task_id: int
    sample_id: str
    split: str


def _channel_policy_to_pil_mode(policy: str) -> str:
    if policy not in CHANNEL_POLICIES:
        raise ValueError(f"Unknown channel policy {policy!r}; expected one of {CHANNEL_POLICIES}")
    return "L" if policy == "GRAYSCALE_1CH" else "RGB"


class MultiDomainDataset(Dataset):
    """
    Deterministic, split-scoped view over a harmonized multi-domain manifest.

    Parameters
    ----------
    manifest_csv : path
        One of ``manifests/phase4_v3/{train,val,test}.csv``.
    split : {"TRAIN", "VAL"}
        Only development splits are permitted. ``"TEST"`` raises.
    size : int
        Canonical spatial size; must be one of {256, 512, 768, 1024}.
    train : bool
        Enables the canonical training augmentation boundary (paired).
    datasets : sequence of str, optional
        Restrict to a subset of domains (default: all present).
    channel_policy : str
        One of ``CHANNEL_POLICIES``.
    """

    def __init__(self, manifest_csv, split, size=512, train=False,
                 datasets=None, channel_policy=DEFAULT_CHANNEL_POLICY):
        split = str(split).upper()
        if split == "TEST":
            raise RuntimeError("Phase-19 harmonized dataset rejects the TEST split (TEST reads must stay 0)")
        if split not in {"TRAIN", "VAL"}:
            raise ValueError(f"split must be TRAIN or VAL, got {split!r}")

        frame = pd.read_csv(manifest_csv)
        frame = frame[frame["split"].astype(str).str.upper() == split].copy()
        if datasets is not None:
            frame = frame[frame["dataset"].isin(list(datasets))].copy()
        frame = frame.sort_values(["dataset", "sample_id"]).reset_index(drop=True)

        self.frame = frame
        self.split = split
        self.size = int(size)
        self.train = bool(train)
        self.channel_policy = channel_policy
        self.pil_mode = _channel_policy_to_pil_mode(channel_policy)
        self.transform = SegmentationTransform(size=self.size, train=self.train,
                                               image_mode=self.pil_mode)

    # -- Dataset protocol --------------------------------------------------- #
    def __len__(self) -> int:
        return len(self.frame)

    def __getitem__(self, index: int) -> HarmonizedSample:
        row = self.frame.iloc[index]
        image = Image.open(row["image_path"]).convert(self.pil_mode)
        mask = Image.open(row["mask_path"])
        image_t, mask_t, _meta = self.transform(image, mask)
        # canonical foreground contract applied once, in the module, on the
        # already-resized mask (idempotent with the transform's own >0 rule)
        mask_bin = (mask_t > 0).to(torch.float32)
        return HarmonizedSample(
            image=image_t.contiguous(),
            mask=mask_bin.contiguous(),
            dataset=str(row["dataset"]),
            task_id=int(row["task_id"]),
            sample_id=str(row["sample_id"]),
            split=self.split,
        )

    # -- Introspection ------------------------------------------------------ #
    def class_distribution(self) -> dict:
        return {k: int(v) for k, v in self.frame["dataset"].value_counts().items()}


def harmonized_collate(batch):
    """Stack a list of :class:`HarmonizedSample` into batched tensors."""
    images = torch.stack([s.image for s in batch], dim=0)
    masks = torch.stack([s.mask for s in batch], dim=0)
    return {
        "image": images,                                   # (B, C, H, W)
        "mask": masks,                                     # (B, 1, H, W)
        "dataset": [s.dataset for s in batch],
        "task_id": torch.tensor([s.task_id for s in batch], dtype=torch.long),
        "sample_id": [s.sample_id for s in batch],
        "split": [s.split for s in batch],
    }
