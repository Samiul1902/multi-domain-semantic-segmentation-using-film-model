"""Shared heatmap target generation utilities for Phase 13B."""
import math
import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import label

def make_gaussian_heatmap(image_size: int, centroids, sigma: float, component_areas=None,
                          sigma_min: float = 0.35, sigma_max: float = 0.75,
                          A_ref: float = 14.0) -> np.ndarray:
    """Create a soft heatmap by summing Gaussians at component centroids.

    Backward-compatible: when ``component_areas`` is None (the historical call
    path), every component uses the single fixed ``sigma`` and the output is
    byte-identical to the pre-change behaviour.

    When ``component_areas`` is provided (one scalar foreground-pixel count in
    *heatmap space* per centroid, aligned by index), each component gets a
    size-adaptive sigma via the frozen H3 monotonic mapping:

        sigma_i = clip(sigma_min + (sigma_max - sigma_min) * sqrt(A_i / A_ref),
                       sigma_min, sigma_max)

    Small components (small A_i) get a tighter, higher-contrast peak; large
    components cap at sigma_max. ``A_ref`` is calibrated from TRAIN-only geometry
    (see reports/tables/h3_aref_code_exact.json) so the mapping is fixed at
    training time and never depends on VAL/TEST.
    """
    heatmap = np.zeros((image_size, image_size), dtype=np.float32)
    if not centroids:
        return heatmap
    ys = np.arange(image_size, dtype=np.float32).reshape(-1, 1)
    xs = np.arange(image_size, dtype=np.float32).reshape(1, -1)
    for i, (cy, cx) in enumerate(centroids):
        if component_areas is None:
            s = float(sigma)
        else:
            A_i = float(component_areas[i]) if component_areas[i] is not None else 0.0
            s = min(sigma_max, max(sigma_min,
                                   sigma_min + (sigma_max - sigma_min) * math.sqrt(A_i / A_ref)))
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
        comp_hm = np.exp(-((ys - cy)**2 + (xs - cx)**2) / (2 * s**2)).astype(np.float32)

        # Explicitly set the canonical center pixel value to exactly 1.0
        comp_hm[icy, icx] = 1.0

        # Combine components using pixelwise maximum
        heatmap = np.maximum(heatmap, comp_hm)
    return heatmap


def heatmap_space_component_areas(padded_mask, image_resolution: int, heatmap_resolution: int):
    """Count foreground pixels per connected component in heatmap space.

    ``padded_mask`` is an (image_resolution x image_resolution) 0/1 or bool array
    (the mask after resize + centre padding, in localizer INPUT resolution). The
    heatmap-space mask is obtained by integer-stride subsampling
    ``padded_mask[::factor, ::factor]`` with factor = image_resolution //
    heatmap_resolution, faithfully mirroring KUBLocalizerDataset's centroid
    mapping (cx / factor, cy / factor).

    Returns
    -------
    label_map : np.ndarray
        (heatmap_resolution x heatmap_resolution) int label map (0 = background).
    areas : np.ndarray
        int array of length (n_components + 1); areas[label] = foreground pixel
        count in heatmap space (areas[0] == 0).
    """
    factor = int(image_resolution // heatmap_resolution)
    m_hm = (np.asarray(padded_mask)[::factor, ::factor] > 0)
    labeled, n = label(m_hm, structure=np.ones((3, 3), int))
    areas = np.zeros(n + 1, dtype=np.int64)
    for cid in range(1, n + 1):
        areas[cid] = int((labeled == cid).sum())
    return labeled, areas

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
