"""Synthetic population generator for integration testing.

The point is to drive the REAL code path -- the real dataset class, the real
loader, the real model, the real fold derivation, the real refiner dataset, the
real OOF label computation -- over a population small enough to finish in seconds.

Nothing here is used by a real run.  A synthetic run is stamped
``synthetic: true`` and ``protocol_faithful: false`` in its manifest, so it can
never be cited as evidence.

Layout produced under ``root``::

    images/<sample_id>.png      128 x 128 RGB
    masks/<sample_id>.png       128 x 128 binary
    train.csv                   ROUTER_DEVELOPMENT + ROUTER_HOLDOUT
    val.csv                     VAL
    router_split.csv            sample_id, dataset, task_id, group_key, split_role

The synthetic masks are a filled ellipse per image, so a global model has a
non-trivial target and the ROI proposal finds foreground.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw

from . import recipe as R
from .population import PopulationSpec

__all__ = ["SyntheticBundle", "build_synthetic_population"]

IMAGE_SIZE = 128


@dataclass
class SyntheticBundle:
    root: Path
    spec: PopulationSpec
    train_csv: Path
    val_csv: Path
    router_split_csv: Path
    n_dev: int
    n_val: int
    n_holdout: int


def _sample_id(domain: str, i: int) -> str:
    return hashlib.sha256(f"SYNTH::{domain}::{i}".encode()).hexdigest()[:32]


def _make_image(rng: np.random.Generator, task_id: int) -> tuple:
    """One deterministic synthetic image + ellipse mask."""
    size = IMAGE_SIZE
    base = rng.integers(20, 200, size=3)
    arr = np.ones((size, size, 3), dtype=np.uint8) * base[None, None, :]
    arr = np.clip(arr.astype(np.int16) + rng.integers(-15, 15, size=(size, size, 3)),
                  0, 255).astype(np.uint8)
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    cy, cx = int(rng.integers(size // 3, 2 * size // 3)), int(rng.integers(size // 3, 2 * size // 3))
    ry = int(rng.integers(size // 8, size // 4))
    rx = int(rng.integers(size // 8, size // 4))
    draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=255)
    m = np.asarray(mask) > 0
    arr[m] = np.clip(arr[m].astype(np.int16) + 60, 0, 255).astype(np.uint8)
    return arr, (m.astype(np.uint8) * 255)


def build_synthetic_population(root: Path, *, per_domain_dev: int = 9,
                               per_domain_val: int = 3, per_domain_holdout: int = 3,
                               groups_per_domain: int = 3, seed: int = 20261103,
                               force: bool = False) -> SyntheticBundle:
    root = Path(root)
    img_dir = root / "images"
    mask_dir = root / "masks"
    img_dir.mkdir(parents=True, exist_ok=True)
    mask_dir.mkdir(parents=True, exist_ok=True)

    train_rows, val_rows, split_rows = [], [], []
    rng = np.random.default_rng(seed)

    for domain in R.DATASET_ORDER:
        tid = R.TASK_ID[domain]
        n_dev = per_domain_dev
        n_val = per_domain_val
        n_hold = per_domain_holdout
        for i in range(n_dev + n_val + n_hold):
            sid = _sample_id(domain, i)
            ipath = img_dir / f"{sid}.png"
            mpath = mask_dir / f"{sid}.png"
            if force or not (ipath.exists() and mpath.exists()):
                arr, mask = _make_image(rng, tid)
                Image.fromarray(arr, mode="RGB").save(ipath)
                Image.fromarray(mask, mode="L").save(mpath)
            g = i % groups_per_domain
            row = {
                "dataset": domain, "task_id": tid,
                "image_path": str(ipath), "mask_path": str(mpath),
                "patient_id": f"patient-{domain}-{g:02d}",
                "case_id": f"case-{domain}-{g:02d}",
                "category": "SYNTHETIC",
                "sample_id": sid,
            }
            if i < n_dev:
                split_role = "ROUTER_DEVELOPMENT"
                train_rows.append({**row, "split": "TRAIN"})
            elif i < n_dev + n_hold:
                split_role = "ROUTER_HOLDOUT"
                train_rows.append({**row, "split": "TRAIN"})
            else:
                split_role = "VAL"
                val_rows.append({**row, "split": "VAL"})
            if split_role != "VAL":
                split_rows.append({"sample_id": sid, "dataset": domain, "task_id": tid,
                                   "group_key": f"GROUP::{domain}::{g:02d}",
                                   "split_role": split_role})

    train_csv = root / "train.csv"
    val_csv = root / "val.csv"
    split_csv = root / "router_split.csv"
    pd.DataFrame(train_rows).to_csv(train_csv, index=False)
    pd.DataFrame(val_rows).to_csv(val_csv, index=False)
    split_df = pd.DataFrame(split_rows)
    split_df.to_csv(split_csv, index=False)

    dev = split_df[split_df["split_role"] == "ROUTER_DEVELOPMENT"].copy()
    paths = pd.DataFrame(train_rows)[["sample_id", "image_path", "mask_path", "patient_id",
                                      "case_id", "category"]]
    dev = dev.merge(paths, on="sample_id", how="left", validate="one_to_one")
    dev = dev.sort_values(["dataset", "sample_id"]).reset_index(drop=True)

    spec = PopulationSpec(development=dev, train_manifest=train_csv, val_manifest=val_csv,
                          router_split_manifest=split_csv, source="SYNTHETIC",
                          holdout_ids=frozenset(
                              split_df[split_df["split_role"] == "ROUTER_HOLDOUT"]
                              ["sample_id"].astype(str)))
    return SyntheticBundle(root=root, spec=spec, train_csv=train_csv, val_csv=val_csv,
                           router_split_csv=split_csv, n_dev=len(dev), n_val=len(val_rows),
                           n_holdout=len(split_rows) - len(dev))
