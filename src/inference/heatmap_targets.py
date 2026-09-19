"""Shared heatmap target generation utilities for Phase 13B."""
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import label

def make_gaussian_heatmap(image_size: int, centroids, sigma: float) -> np.ndarray:
    """Create a soft heatmap by summing Gaussians at component centroids."""
    heatmap = np.zeros((image_size, image_size), dtype=np.float32)
    if not centroids:
        return heatmap
    ys = np.arange(image_size, dtype=np.float32).reshape(-1, 1)
    xs = np.arange(image_size, dtype=np.float32).reshape(1, -1)
    for cy, cx in centroids:
        # Determine the canonical integer center pixel
        # Round half to even is standard, but simple int(round()) is fine.
        # We'll use round()
        icy = int(round(cy))
        icx = int(round(cx))
        
        # Clamp to valid image boundaries
        icy = max(0, min(image_size - 1, icy))
        icx = max(0, min(image_size - 1, icx))
        
        # Generate the Gaussian target around the original subpixel center
        # (This preserves the exact Gaussian geometry outside the peak as requested)
        comp_hm = np.exp(-((ys - cy)**2 + (xs - cx)**2) / (2 * sigma**2)).astype(np.float32)
        
        # Explicitly set the canonical center pixel value to exactly 1.0
        comp_hm[icy, icx] = 1.0
        
        # Combine components using pixelwise maximum
        heatmap = np.maximum(heatmap, comp_hm)
    return heatmap

def get_component_centroids_in_localizer_space(mask_path, scale, resized_h, resized_w, left_pad, top_pad):
    """Extract original-space component centroids and map them to localizer input space."""
    with Image.open(mask_path) as f:
        gt_orig = np.asarray(f.convert('L')) > 0
    labeled, n = label(gt_orig, structure=np.ones((3, 3), int))
    centroids = []
    for cid in range(1, n + 1):
        ys, xs = np.where(labeled == cid)
        cy_orig, cx_orig = ys.mean(), xs.mean()
        cy_resized = cy_orig * scale + top_pad
        cx_resized = cx_orig * scale + left_pad
        centroids.append((cy_resized, cx_resized))
    return centroids
