"""Clean-v3-safe GT-free localizer inference wrapper (Phase 13 Part 1B-R0).

WHY THIS MODULE EXISTS
----------------------
``src/inference/learned_roi.predict_localizer`` constructs the localizer WITHOUT
passing ``heatmap_resolution``. Because the final ``logit_downsample`` layer is
parameter-free, loading a 128-output checkpoint into a 512-output model succeeds
SILENTLY and the wrapper then returns a 512-space heatmap whose geometry does not
match the trained checkpoint. The frozen R2 protocol requires the explicit
128-resolution argument on every inference path
(R2 ``heatmap_contract.explicit_argument_required = true``) and selected
remediation option B for clean-v3 work.

This module is the option-B wrapper. It ALWAYS passes
``heatmap_resolution=128`` explicitly and asserts the output geometry loudly.

The historical helper is intentionally left UNMODIFIED. This module does not
import or monkeypatch it.

R0 STATUS
---------
This file is CREATED by Phase 13 Part 1B-R0. It is NOT executed in R0:
no image is read, no checkpoint is loaded, no model is constructed, no forward
pass is performed.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import torch

# --- Frozen clean-v3 constants (single source of truth for this module) -------
HEATMAP_RESOLUTION: int = 128
INPUT_RESOLUTION: int = 512
BASE_CHANNELS: int = 16
IN_CHANNELS: int = 1
OUT_CHANNELS: int = 1

# Frozen primary proposal configuration (R2 proposal_configuration).
PRIMARY_PROPOSAL_CONFIG: Dict[str, float] = {
    "threshold": 0.10,
    "margin": 0.20,
    "top_k": 5,
    "nms_iou": 0.30,
}


class CleanV3GeometryError(RuntimeError):
    """Raised when the predicted heatmap geometry violates the 128x128 contract."""


def _assert_heatmap_geometry(heatmap: np.ndarray, context: str) -> None:
    """Fail loudly unless ``heatmap`` is a 2-D (128, 128) array."""
    if not isinstance(heatmap, np.ndarray):
        raise CleanV3GeometryError(
            f"{context}: expected np.ndarray heatmap, got {type(heatmap)!r}"
        )
    if heatmap.ndim != 2:
        raise CleanV3GeometryError(
            f"{context}: expected a 2-D heatmap, got shape {heatmap.shape!r}"
        )
    expected = (HEATMAP_RESOLUTION, HEATMAP_RESOLUTION)
    if heatmap.shape != expected:
        raise CleanV3GeometryError(
            f"{context}: heatmap spatial shape {heatmap.shape!r} != required "
            f"{expected!r}. The localizer must be constructed with "
            f"heatmap_resolution={HEATMAP_RESOLUTION} explicitly."
        )


def build_clean_v3_localizer(device: Optional[torch.device] = None):
    """Construct ``KUBLocalizer`` with the 128 heatmap resolution passed EXPLICITLY.

    Never relies on the constructor default (which is 512).
    """
    from src.models.factory import create_model

    model = create_model(
        "kub_localizer",
        in_channels=IN_CHANNELS,
        out_channels=OUT_CHANNELS,
        base_channels=BASE_CHANNELS,
        heatmap_resolution=HEATMAP_RESOLUTION,
    )
    if device is not None:
        model = model.to(device)
    return model


def load_clean_v3_localizer(checkpoint_path, device: Optional[torch.device] = None):
    """Build the explicitly-128 localizer and load a clean-v3 checkpoint into it."""
    from src.utils.checkpointing import load_training_checkpoint

    checkpoint_path = Path(checkpoint_path)
    if not checkpoint_path.exists():
        raise FileNotFoundError(checkpoint_path)
    model = build_clean_v3_localizer(device=device)
    state = load_training_checkpoint(
        checkpoint_path, model, restore_rng=False,
        map_location=device if device is not None else "cpu",
    )
    model.eval()
    return model, state


def predict_localizer_clean_v3(
    image_path,
    checkpoint_path,
    resolution: int = INPUT_RESOLUTION,
    threshold: float = PRIMARY_PROPOSAL_CONFIG["threshold"],
    margin: float = PRIMARY_PROPOSAL_CONFIG["margin"],
    top_k: int = PRIMARY_PROPOSAL_CONFIG["top_k"],
    nms_iou: float = PRIMARY_PROPOSAL_CONFIG["nms_iou"],
    device: Optional[torch.device] = None,
) -> Dict[str, Any]:
    """GT-free clean-v3 localizer inference with enforced 128x128 geometry.

    Not executed in R0. Provided so that the clean-v3 validation / proposal path
    has a defect-free entry point once the supervisor authorizes it.

    The proposal API accepts NO ground truth. GT may only be used AFTER proposals
    are generated, for evaluation.
    """
    from PIL import Image

    from src.data.transforms import SegmentationTransform
    from src.inference.kub_predict import _check_governance_lock
    from src.inference.predicted_roi import generate_predicted_rois

    image_path = Path(image_path)
    _check_governance_lock(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)

    device = torch.device(
        device or ("cuda" if torch.cuda.is_available() else "cpu")
    )

    with Image.open(image_path) as handle:
        image = handle.convert("L")
    dummy = Image.new("L", image.size)
    tensor, _, metadata = SegmentationTransform(resolution, False)(image, dummy)

    model, _state = load_clean_v3_localizer(checkpoint_path, device=device)

    # Fail-loud: the model really does emit 128x128, not the constructor default.
    if getattr(model, "heatmap_resolution", None) != HEATMAP_RESOLUTION:
        raise CleanV3GeometryError(
            "clean-v3 localizer was built with heatmap_resolution="
            f"{getattr(model, 'heatmap_resolution', None)!r}, expected "
            f"{HEATMAP_RESOLUTION}. Refusing to continue."
        )

    with torch.inference_mode():
        with torch.amp.autocast(
            device_type=device.type, enabled=device.type == "cuda"
        ):
            logits = model(tensor.unsqueeze(0).to(device))

    # Fail-loud output-shape assertions (R2 heatmap_contract.fail_loud_assertions)
    logit_shape = tuple(int(value) for value in logits.shape)
    expected_logit_shape = (1, OUT_CHANNELS, HEATMAP_RESOLUTION, HEATMAP_RESOLUTION)
    if logit_shape != expected_logit_shape:
        raise CleanV3GeometryError(
            f"model output shape {logit_shape!r} != required "
            f"{expected_logit_shape!r}"
        )

    heatmap = torch.sigmoid(logits)[0, 0].float().cpu().numpy()
    _assert_heatmap_geometry(heatmap, "predict_localizer_clean_v3")

    proposals = generate_predicted_rois(
        heatmap, metadata, (image.height, image.width),
        threshold, margin, top_k, nms_iou,
    )

    return {
        "image_path": str(image_path.resolve()),
        "heatmap": heatmap,
        "heatmap_shape": tuple(int(v) for v in heatmap.shape),
        "heatmap_resolution": HEATMAP_RESOLUTION,
        "heatmap_resolution_explicit": True,
        "proposals": proposals,
        "proposal_configuration": {
            "threshold": threshold,
            "margin": margin,
            "top_k": top_k,
            "nms_iou": nms_iou,
        },
        "transform_metadata": metadata,
        "original_shape": (image.height, image.width),
        "GT_used_for_inference": False,
    }


__all__ = [
    "HEATMAP_RESOLUTION",
    "INPUT_RESOLUTION",
    "PRIMARY_PROPOSAL_CONFIG",
    "CleanV3GeometryError",
    "build_clean_v3_localizer",
    "load_clean_v3_localizer",
    "predict_localizer_clean_v3",
]
