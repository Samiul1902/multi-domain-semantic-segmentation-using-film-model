"""``CACHE_LITE`` -- per-seed Lite crop cache and 202-D pre-refinement features.

Reuses the frozen FULL cache producer wholesale: the same ROI rule
(threshold 0.30 -> tight bbox -> 1.50 centre-preserving expansion -> clip ->
square pad -> bilinear RGB / bilinear p_global / nearest GT -> 256x256), the same
memmap layout, the same FORCED_SKIP accounting, the same ``meta.csv`` geometry
columns -- because :class:`src.data.barr_refiner_dataset.BARRRefinerCropDataset`
and :func:`src.data.barr_roi.extract_roi_triplet` are the shared consumers and
must keep reading the same thing.

Two substitutions only
----------------------
``model_loader``
    loads the **Lite** G checkpoint and refuses any other architecture.
``feature_builder``
    the Lite 202-D builder, which enforces the Lite tap widths (128/24/12).

The tap capture itself needs no change: ``TapRecorder`` installs forward hooks on
``model.bridge`` / ``model.decoder2`` / ``model.decoder1``, and the Lite backbone
exposes modules with exactly those names whose outputs are the same three
pre-FiLM maps the FULL backbone exposes.
"""
from __future__ import annotations

from src.models.lite.ra_medfilm_barr_lite import LiteGlobalMedFiLM
from src.research.full_pipeline.context import RunContext, StageRecord
from src.research.full_pipeline.provenance import load_checkpoint
from src.research.full_pipeline.stages import cache_stage

from .. import recipe as L
from ..features import lite_feature_builder, lite_feature_schema

STAGE = "CACHE"


def load_lite_global(ctx: RunContext, device):
    """Load the Lite G checkpoint for this family, refusing any other architecture."""
    ck = load_checkpoint(ctx.g_checkpoint(), map_location="cpu", component="G",
                         seed=ctx.seed, family="LITE")
    expected_id = ctx.g_architecture_id()                      # type: ignore[attr-defined]
    expected_sha = ctx.architecture_sha256                     # type: ignore[attr-defined]
    if ck.get("architecture_id") != expected_id:
        raise ValueError(
            f"G checkpoint architecture {ck.get('architecture_id')!r} != {expected_id!r}; "
            "a FULL or differently-configured checkpoint cannot seed a Lite cache")
    stamped = L.checkpoint_architecture_sha256(ck, block="g")
    if stamped != expected_sha:
        raise ValueError(
            f"G checkpoint architecture digest {stamped} does not match the variant "
            f"spec {expected_sha}")

    model = LiteGlobalMedFiLM(ctx.spec)                        # type: ignore[attr-defined]
    model.load_state_dict(ck["model_state"])
    return model.to(device).eval()


def run(ctx: RunContext, *, resume: bool = False, log=print) -> StageRecord:
    record = cache_stage.run(ctx, resume=resume, log=log,
                             model_loader=load_lite_global,
                             feature_builder=lite_feature_builder)
    record.detail = dict(record.detail or {})
    record.detail.update({
        "model_identity": "RA-MedFiLM-BARR-Lite",
        "variant": ctx.variant,                                # type: ignore[attr-defined]
        "feature_schema": lite_feature_schema(),
    })
    return record


def is_complete(ctx: RunContext) -> bool:
    return cache_stage.is_complete(ctx)


def verify(ctx: RunContext) -> dict:
    out = cache_stage.verify(ctx)
    out["family"] = "LITE"
    out["verdict"] = "CACHE_LITE_VERIFIED"
    return out
