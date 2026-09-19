"""Oracle ROI / Zoom upper-bound analysis module for KUB segmentation."""
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageOps
from scipy.ndimage import label

from src.data.kub_dataset import TestAccessError
from src.metrics.object_metrics import object_metrics
from src.metrics.segmentation import binary_metrics, hd95

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _check_governance_lock(image_path):
    """Verify that the image path is not locked under TEST or external data."""
    resolved_path = Path(image_path).resolve()
    path_str = str(resolved_path).lower()
    if "external_test_ds" in path_str or "external" in path_str:
        raise TestAccessError(f"Development access to external test data is blocked: {image_path}")

    test_manifest_path = PROJECT_ROOT / "manifests" / "test.csv"
    if test_manifest_path.exists():
        df_test = pd.read_csv(test_manifest_path)
        test_paths = {Path(p).resolve() for p in df_test["image_path"].dropna()}
        if resolved_path in test_paths:
            raise TestAccessError(f"Image is in the locked TEST set; development prediction is blocked: {image_path}")


def extract_gt_components(gt_mask):
    """Extract original-space 8-connected components and bounding boxes from a binary GT mask."""
    gt = (np.asarray(gt_mask) > 0).astype(np.uint8)
    structure = np.ones((3, 3), dtype=int)
    labeled, n_components = label(gt, structure=structure)
    h_img, w_img = gt.shape

    components = []
    for c_id in range(1, n_components + 1):
        c_mask = labeled == c_id
        ys, xs = np.where(c_mask)
        min_y, max_y = int(ys.min()), int(ys.max())
        min_x, max_x = int(xs.min()), int(xs.max())
        pixel_count = int(c_mask.sum())
        component_ratio = float(pixel_count / (h_img * w_img))

        components.append({
            "component_id": c_id,
            "min_y": min_y, "max_y": max_y,
            "min_x": min_x, "max_x": max_x,
            "bbox_height": max_y - min_y + 1,
            "bbox_width": max_x - min_x + 1,
            "component_pixels": pixel_count,
            "component_ratio": component_ratio,
        })
    return components, labeled


def compute_square_crop(bbox, image_shape, margin=0.25):
    """Determine square crop coordinates with context margin, safely handling boundaries."""
    h_img, w_img = image_shape
    min_y, max_y = bbox["min_y"], bbox["max_y"]
    min_x, max_x = bbox["min_x"], bbox["max_x"]

    bbox_h = max_y - min_y + 1
    bbox_w = max_x - min_x + 1

    m_y = round(margin * bbox_h)
    m_x = round(margin * bbox_w)

    exp_min_y = min_y - m_y
    exp_max_y = max_y + m_y
    exp_min_x = min_x - m_x
    exp_max_x = max_x + m_x

    exp_h = exp_max_y - exp_min_y + 1
    exp_w = exp_max_x - exp_min_x + 1

    side = max(exp_h, exp_w)
    center_y = (exp_min_y + exp_max_y) / 2.0
    center_x = (exp_min_x + exp_max_x) / 2.0

    y1 = round(center_y - side / 2.0)
    y2 = y1 + side
    x1 = round(center_x - side / 2.0)
    x2 = x1 + side

    pad_top = max(0, -y1)
    pad_bottom = max(0, y2 - h_img)
    pad_left = max(0, -x1)
    pad_right = max(0, x2 - w_img)

    clip_y1 = max(0, y1)
    clip_y2 = min(h_img, y2)
    clip_x1 = max(0, x1)
    clip_x2 = min(w_img, x2)

    effective_magnification = 512.0 / float(side)

    return {
        "y1": y1, "y2": y2, "x1": x1, "x2": x2,
        "clip_y1": clip_y1, "clip_y2": clip_y2,
        "clip_x1": clip_x1, "clip_x2": clip_x2,
        "pad_top": pad_top, "pad_bottom": pad_bottom,
        "pad_left": pad_left, "pad_right": pad_right,
        "crop_side_pixels": side,
        "effective_magnification": effective_magnification,
        "margin": margin,
    }


def crop_and_preprocess(raw_image, crop_geom, target_size=512):
    """Crop original image and resize to target_size using bilinear interpolation."""
    img_arr = np.asarray(raw_image.convert("L"))
    c_y1, c_y2 = crop_geom["clip_y1"], crop_geom["clip_y2"]
    c_x1, c_x2 = crop_geom["clip_x1"], crop_geom["clip_x2"]

    valid_crop = img_arr[c_y1:c_y2, c_x1:c_x2]
    padded_crop = np.pad(
        valid_crop,
        ((crop_geom["pad_top"], crop_geom["pad_bottom"]),
         (crop_geom["pad_left"], crop_geom["pad_right"])),
        mode="constant",
        constant_values=0
    )

    crop_pil = Image.fromarray(padded_crop).resize((target_size, target_size), Image.Resampling.BILINEAR)
    tensor = torch.from_numpy(np.asarray(crop_pil, dtype=np.float32).copy()).unsqueeze(0).unsqueeze(0) / 255.0
    assert tensor.shape == (1, 1, target_size, target_size)
    return tensor


def restore_crop_probability(prob_512, crop_geom, original_shape):
    """Resize 512x512 crop probability map back to crop side and place in original image space."""
    h_img, w_img = original_shape
    side = crop_geom["crop_side_pixels"]

    prob_crop_pil = Image.fromarray((prob_512 * 255.0).astype(np.uint8)).resize(
        (side, side), Image.Resampling.BILINEAR
    )
    prob_crop_arr = np.asarray(prob_crop_pil, dtype=np.float32) / 255.0

    p_top, p_bot = crop_geom["pad_top"], side - crop_geom["pad_bottom"]
    p_left, p_right = crop_geom["pad_left"], side - crop_geom["pad_right"]
    valid_prob = prob_crop_arr[p_top:p_bot, p_left:p_right]

    prob_full = np.zeros((h_img, w_img), dtype=np.float32)
    c_y1, c_y2 = crop_geom["clip_y1"], crop_geom["clip_y2"]
    c_x1, c_x2 = crop_geom["clip_x1"], crop_geom["clip_x2"]

    prob_full[c_y1:c_y2, c_x1:c_x2] = valid_prob
    return prob_full


def fuse_probability_maps(probability_maps, output_shape):
    """Fuse restored component maps by deterministic pixelwise maximum."""
    if not probability_maps:
        return np.zeros(output_shape, dtype=np.float32)
    for probability in probability_maps:
        if np.asarray(probability).shape != tuple(output_shape):
            raise ValueError("All probability maps must match output_shape")
    return np.maximum.reduce(probability_maps).astype(np.float32, copy=False)


def run_oracle_roi_image(image_path, mask_path, model, device, margin=0.25, threshold=0.5):
    """Run component-wise Oracle ROI inference on a single image and fuse outputs via pixelwise MAX."""
    image_path = Path(image_path)
    _check_governance_lock(image_path)

    with Image.open(image_path) as img_file, Image.open(mask_path) as mask_file:
        raw_image = img_file.convert("L")
        raw_mask = mask_file.convert("L")

    gt_mask = (np.asarray(raw_mask) > 0).astype(np.uint8)
    h_img, w_img = gt_mask.shape
    components, _ = extract_gt_components(gt_mask)

    if not components:
        prob_combined = np.zeros((h_img, w_img), dtype=np.float32)
        mask_combined = np.zeros((h_img, w_img), dtype=np.uint8)
        return {
            "prob_combined": prob_combined,
            "mask_combined": mask_combined,
            "component_results": [],
            "components": [],
        }

    component_probs = []
    component_results = []

    for comp in components:
        crop_geom = compute_square_crop(comp, (h_img, w_img), margin=margin)
        crop_tensor = crop_and_preprocess(raw_image, crop_geom, target_size=512).to(device)

        # Assert GT pixel mask is NOT concatenated as model input
        assert crop_tensor.shape == (1, 1, 512, 512)

        with torch.no_grad():
            if device.type == "cuda":
                with torch.amp.autocast("cuda", enabled=True):
                    logits = model(crop_tensor)
            else:
                logits = model(crop_tensor)

        prob_512 = torch.sigmoid(logits).squeeze().cpu().numpy().astype(np.float32)
        prob_restored = restore_crop_probability(prob_512, crop_geom, (h_img, w_img))

        component_probs.append(prob_restored)
        component_results.append({
            "component_id": comp["component_id"],
            "crop_geom": crop_geom,
            "prob_512": prob_512,
            "prob_restored": prob_restored,
        })

    prob_combined = fuse_probability_maps(component_probs, (h_img, w_img))
    mask_combined = (prob_combined >= threshold).astype(np.uint8)

    return {
        "prob_combined": prob_combined,
        "mask_combined": mask_combined,
        "component_results": component_results,
        "components": components,
    }

    x1 = round(center_x - side / 2.0)
    x2 = x1 + side

    pad_top = max(0, -y1)
    pad_bottom = max(0, y2 - h_img)
    pad_left = max(0, -x1)
    pad_right = max(0, x2 - w_img)

    clip_y1 = max(0, y1)
    clip_y2 = min(h_img, y2)
    clip_x1 = max(0, x1)
    clip_x2 = min(w_img, x2)

    effective_magnification = 512.0 / float(side)

    return {
        "y1": y1, "y2": y2, "x1": x1, "x2": x2,
        "clip_y1": clip_y1, "clip_y2": clip_y2,
        "clip_x1": clip_x1, "clip_x2": clip_x2,
        "pad_top": pad_top, "pad_bottom": pad_bottom,
        "pad_left": pad_left, "pad_right": pad_right,
        "crop_side_pixels": side,
        "effective_magnification": effective_magnification,
        "margin": margin,
    }
