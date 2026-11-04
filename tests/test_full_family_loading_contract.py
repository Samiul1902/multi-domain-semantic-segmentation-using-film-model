"""FULL must reject a differently stamped family before constructing models."""
from types import SimpleNamespace

import pytest
import torch

from src.research.full_pipeline.inference import FamilyBundle
from src.research.full_pipeline.provenance import CHECKPOINT_SCHEMA, FamilyCompatibilityError


def test_full_loader_rejects_lite_stamp_before_model_construction(tmp_path):
    ctx = SimpleNamespace(seed=42, tag="synthetic", **{
        f"{c.lower()}_dir": tmp_path / c for c in "GRBS"})
    for c in "GRBS":
        path = getattr(ctx, f"{c.lower()}_dir") / ("best.pt" if c == "G" else "final/final.pt")
        path.parent.mkdir(parents=True)
        torch.save({"schema": CHECKPOINT_SCHEMA, "family": "LITE", "component": c,
                    "seed": 42, "upstream": {}}, path)
    with pytest.raises(FamilyCompatibilityError, match="family"):
        FamilyBundle.load(ctx)
