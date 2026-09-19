import numpy as np
import torch
from PIL import Image

def restore_regional_probability(prob_map: np.ndarray, crop_geometry: dict, original_shape: tuple) -> tuple:
    """
    Restore regional probability map to original scale using bilinear interpolation.
    Returns (restored_probability_canvas, regional_support_mask).
    """
    h_img, w_img = original_shape
    side = crop_geometry['crop_side_pixels']
    
    # Bilinear resize to crop side
    prob_crop_pil = Image.fromarray((prob_map * 255.0).astype(np.uint8)).resize(
        (side, side), Image.Resampling.BILINEAR
    )
    prob_crop_arr = np.asarray(prob_crop_pil, dtype=np.float32) / 255.0
    
    # Remove padding to get valid clip
    p_top = crop_geometry['pad_top']
    p_bot = side - crop_geometry['pad_bottom']
    p_left = crop_geometry['pad_left']
    p_right = side - crop_geometry['pad_right']
    
    valid_prob = prob_crop_arr[p_top:p_bot, p_left:p_right]
    
    # Place in original canvas
    canvas = np.zeros((h_img, w_img), dtype=np.float32)
    support = np.zeros((h_img, w_img), dtype=bool)
    
    c_y1, c_y2 = crop_geometry['clip_y1'], crop_geometry['clip_y2']
    c_x1, c_x2 = crop_geometry['clip_x1'], crop_geometry['clip_x2']
    
    canvas[c_y1:c_y2, c_x1:c_x2] = valid_prob
    support[c_y1:c_y2, c_x1:c_x2] = True
    
    return canvas, support

def aggregate_and_fuse(global_prob: np.ndarray, regional_probs: list, regional_supports: list) -> np.ndarray:
    """
    Aggregate overlapping regional proposals using MAX, then fuse with global probability.
    Pfinal(x) = Pregional_union(x) inside ROI union, Pglobal(x) otherwise.
    """
    if not regional_probs:
        return global_prob.copy()
        
    union_support = np.zeros_like(global_prob, dtype=bool)
    max_regional = np.zeros_like(global_prob, dtype=np.float32)
    
    for r_prob, r_supp in zip(regional_probs, regional_supports):
        union_support = union_support | r_supp
        max_regional = np.maximum(max_regional, r_prob)
        
    # Direct replacement inside union_support
    final_prob = np.where(union_support, max_regional, global_prob)
    return final_prob

def binarize(prob: np.ndarray, threshold: float = 0.50) -> np.ndarray:
    return (prob >= threshold).astype(np.uint8)

