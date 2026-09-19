"""GT-free learned KUB heatmap-localizer inference and proposal API."""
from pathlib import Path
import numpy as np
import torch
from PIL import Image

from src.data.kub_dataset import TestAccessError
from src.data.transforms import SegmentationTransform
from src.inference.kub_predict import _check_governance_lock
from src.inference.predicted_roi import generate_predicted_rois
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint


def generate_localizer_rois(heatmap, transform_metadata, original_shape,
                            threshold, margin, top_k, nms_iou=0.30):
    """Generate proposals from a predicted heatmap; intentionally accepts no GT."""
    return generate_predicted_rois(heatmap, transform_metadata, original_shape,
                                   threshold, margin, top_k, nms_iou)


def predict_localizer(image_path, checkpoint_path, resolution, threshold,
                      margin, top_k, nms_iou=0.30, device=None):
    """Run image-only localizer inference and return heatmap plus proposals."""
    image_path = Path(image_path)
    _check_governance_lock(image_path)
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
    with Image.open(image_path) as handle:
        image = handle.convert("L")
    dummy = Image.new("L", image.size)
    tensor, _, metadata = SegmentationTransform(resolution, False)(image, dummy)
    model = create_model("kub_localizer", in_channels=1, out_channels=1,
                         base_channels=16).to(device)
    load_training_checkpoint(checkpoint_path, model, restore_rng=False,
                             map_location=device)
    model.eval()
    with torch.inference_mode():
        with torch.amp.autocast(device_type=device.type,
                                enabled=device.type == "cuda"):
            heatmap = torch.sigmoid(model(tensor.unsqueeze(0).to(device)))[0, 0]
    heatmap = heatmap.float().cpu().numpy()
    proposals = generate_localizer_rois(heatmap, metadata,
                                        (image.height, image.width), threshold,
                                        margin, top_k, nms_iou)
    return {"image_path": str(image_path.resolve()), "heatmap": heatmap,
            "proposals": proposals, "transform_metadata": metadata,
            "original_shape": (image.height, image.width),
            "GT_used_for_inference": False}
