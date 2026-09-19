"""Manual KUB-Stone segmentation prediction utility with research governance protection."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import torch
from PIL import Image, ImageOps

from src.data.kub_dataset import TestAccessError
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _check_governance_lock(image_path):
    """Verify that the image path is not locked under TEST or external data."""
    resolved_path = Path(image_path).resolve()

    # 1. External dataset path check
    path_str = str(resolved_path).lower()
    if "external_test_ds" in path_str or "external" in path_str:
        raise TestAccessError(f"Development access to external test data is blocked: {image_path}")

    # 2. Manifest test.csv check
    test_manifest_path = PROJECT_ROOT / "manifests" / "test.csv"
    if test_manifest_path.exists():
        df_test = pd.read_csv(test_manifest_path)
        test_paths = {Path(p).resolve() for p in df_test["image_path"].dropna()}
        if resolved_path in test_paths:
            raise TestAccessError(f"Image is in the locked TEST set; development prediction is blocked: {image_path}")


def _preprocess_image(raw_image, target_size=512):
    """Apply aspect-ratio-preserving resize and symmetric square padding."""
    original_width, original_height = raw_image.size
    scale = min(target_size / original_width, target_size / original_height)
    rw, rh = max(1, round(original_width * scale)), max(1, round(original_height * scale))

    proc_img = raw_image.resize((rw, rh), Image.Resampling.BILINEAR)
    left, top = (target_size - rw) // 2, (target_size - rh) // 2
    right, bottom = target_size - rw - left, target_size - rh - top
    padding = (left, top, right, bottom)

    padded_img = ImageOps.expand(proc_img, padding)
    tensor = torch.from_numpy(np.asarray(padded_img, dtype=np.float32).copy()).unsqueeze(0).unsqueeze(0) / 255.0
    metadata = {
        "original_width": original_width,
        "original_height": original_height,
        "scale": scale,
        "resized_width": rw,
        "resized_height": rh,
        "padding": padding,
    }
    return tensor, padded_img, metadata


def _restore_original_coordinates(prob_512, mask_512, metadata):
    """Remove symmetric padding and resize back to original image dimensions."""
    left, top, right, bottom = metadata["padding"]
    orig_w, orig_h = metadata["original_width"], metadata["original_height"]

    crop_top = top
    crop_bottom = 512 - bottom
    crop_left = left
    crop_right = 512 - right

    cropped_prob = prob_512[crop_top:crop_bottom, crop_left:crop_right]
    cropped_mask = mask_512[crop_top:crop_bottom, crop_left:crop_right]

    prob_pil = Image.fromarray((cropped_prob * 255.0).astype(np.uint8)).resize(
        (orig_w, orig_h), Image.Resampling.BILINEAR
    )
    prob_orig = np.asarray(prob_pil, dtype=np.float32) / 255.0

    mask_pil = Image.fromarray((cropped_mask * 255).astype(np.uint8)).resize(
        (orig_w, orig_h), Image.Resampling.NEAREST
    )
    mask_orig = (np.asarray(mask_pil) > 0).astype(np.uint8)

    return prob_orig, mask_orig


def _create_overlay(image_gray, mask_binary):
    """Create an RGB overlay of the binary mask on the grayscale image."""
    img_arr = np.asarray(image_gray, dtype=np.uint8)
    rgb = np.stack([img_arr] * 3, axis=-1)
    mask_bool = mask_binary > 0

    overlay = rgb.copy()
    overlay[mask_bool, 0] = np.clip(overlay[mask_bool, 0].astype(np.int32) + 120, 0, 255).astype(np.uint8)
    overlay[mask_bool, 1] = (overlay[mask_bool, 1] * 0.4).astype(np.uint8)
    overlay[mask_bool, 2] = (overlay[mask_bool, 2] * 0.4).astype(np.uint8)
    return overlay


def predict_kub(
    image_path,
    model_name="unetpp",
    checkpoint_path=None,
    threshold=0.5,
    device=None,
    return_original_space=True,
    save_dir=None,
):
    """Predict stone segmentation on a single KUB image using a trained model."""
    image_path = Path(image_path)
    _check_governance_lock(image_path)

    if not image_path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")

    if checkpoint_path is None:
        if model_name.lower() == "unet":
            checkpoint_path = PROJECT_ROOT / "checkpoints" / "phase9_kub_unet_baseline_seed42_512" / "best.pt"
        else:
            checkpoint_path = PROJECT_ROOT / "checkpoints" / f"phase10_kub_{model_name.lower()}_seed42_512" / "best.pt"
    else:
        checkpoint_path = Path(checkpoint_path)

    if not checkpoint_path.exists():
        raise FileNotFoundError(f"Checkpoint file not found: {checkpoint_path}")

    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    elif isinstance(device, str):
        device = torch.device(device)

    with Image.open(image_path) as img_file:
        raw_image = img_file.convert("L")

    tensor_512, padded_img, metadata = _preprocess_image(raw_image, target_size=512)

    model = create_model(model_name, in_channels=1, out_channels=1, base_channels=32).to(device)
    load_training_checkpoint(checkpoint_path, model, restore_rng=False, map_location=device)
    model.eval()

    tensor_512 = tensor_512.to(device)
    with torch.no_grad():
        if device.type == "cuda":
            with torch.amp.autocast("cuda", enabled=True):
                logits = model(tensor_512)
        else:
            logits = model(tensor_512)

    prob_512 = torch.sigmoid(logits).squeeze().cpu().numpy().astype(np.float32)
    mask_512 = (prob_512 >= threshold).astype(np.uint8)

    prob_orig, mask_orig = _restore_original_coordinates(prob_512, mask_512, metadata)
    overlay_orig = _create_overlay(raw_image, mask_orig)

    result = {
        "image_path": str(image_path.resolve()),
        "model_name": model_name,
        "checkpoint_path": str(checkpoint_path.resolve()),
        "threshold": float(threshold),
        "original_shape": (metadata["original_height"], metadata["original_width"]),
        "probability_512": prob_512,
        "mask_512": mask_512,
        "probability_original": prob_orig,
        "mask_original": mask_orig,
        "preprocessing_metadata": metadata,
        "overlay_original": overlay_orig,
        "domain": "KUB",
        "task_id": 3,
        "domain_source": "fixed_by_model_scope",
    }

    if save_dir is not None:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)
        stem = image_path.stem

        prob_img = Image.fromarray((prob_orig * 255.0).astype(np.uint8))
        prob_img.save(save_dir / f"{stem}_probability.png")

        mask_img = Image.fromarray((mask_orig * 255).astype(np.uint8))
        mask_img.save(save_dir / f"{stem}_mask.png")

        overlay_img = Image.fromarray(overlay_orig)
        overlay_img.save(save_dir / f"{stem}_overlay.png")

        json_meta = {
            "image_path": str(image_path.resolve()),
            "model_name": model_name,
            "checkpoint_path": str(checkpoint_path.resolve()),
            "threshold": float(threshold),
            "domain": "KUB",
            "task_id": 3,
            "domain_source": "fixed_by_model_scope",
            "original_height": metadata["original_height"],
            "original_width": metadata["original_width"],
            "preprocessing_metadata": metadata,
            "positive_pixel_count_512": int(np.sum(mask_512)),
            "positive_pixel_count_original": int(np.sum(mask_orig)),
        }
        with open(save_dir / f"{stem}_prediction.json", "w", encoding="utf-8") as f:
            json.dump(json_meta, f, indent=2)

    return result


def show_kub_prediction(result):
    """Display 4-panel prediction visualization: Image, Probability, Mask, Overlay."""
    fig, axes = plt.subplots(1, 4, figsize=(16, 4))

    with Image.open(result["image_path"]) as img_file:
        raw_img = np.asarray(img_file.convert("L"))

    axes[0].imshow(raw_img, cmap="gray")
    axes[0].set_title(f"Original Image\n{result['original_shape'][1]}x{result['original_shape'][0]}")
    axes[0].axis("off")

    axes[1].imshow(result["probability_original"], cmap="magma", vmin=0.0, vmax=1.0)
    axes[1].set_title("Probability Map")
    axes[1].axis("off")

    axes[2].imshow(result["mask_original"], cmap="gray", vmin=0, vmax=1)
    axes[2].set_title(f"Stone Mask (Thresh={result['threshold']})")
    axes[2].axis("off")

    axes[3].imshow(result["overlay_original"])
    axes[3].set_title("Red Mask Overlay")
    axes[3].axis("off")

    fig.suptitle(
        f"KUB Stone Prediction | Model: {result['model_name']} | Domain: {result['domain']} (Task {result['task_id']})",
        fontsize=12,
        fontweight="bold",
    )
    plt.tight_layout()
    return fig, axes


    overlay = rgb.copy()
    overlay[mask_bool, 0] = np.clip(overlay[mask_bool, 0].astype(np.int32) + 120, 0, 255).astype(np.uint8)
    overlay[mask_bool, 1] = (overlay[mask_bool, 1] * 0.4).astype(np.uint8)
    overlay[mask_bool, 2] = (overlay[mask_bool, 2] * 0.4).astype(np.uint8)
    return overlay
