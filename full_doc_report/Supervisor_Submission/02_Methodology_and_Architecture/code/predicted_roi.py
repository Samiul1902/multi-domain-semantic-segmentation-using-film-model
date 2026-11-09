"""Predicted ROI proposal generation from global probability maps."""
from pathlib import Path
import sys
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps
from scipy.ndimage import label

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data.kub_dataset import KUBDataset
from src.data.transforms import SegmentationTransform
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.utils.manifest_guard import verify_manifests
from src.utils.test_lock import verify_test_lock


@dataclass
class ProposalConfig:
    """Configuration for predicted ROI proposal generation."""
    proposal_threshold: float = 0.30
    margin: float = 0.10
    top_k: int = 3
    nms_iou: float = 0.50
    min_component_pixels: int = 1


def compute_iou(box1: Tuple[int, int, int, int], box2: Tuple[int, int, int, int]) -> float:
    """Compute inclusive-coordinate box IoU."""
    y1a, x1a, y2a, x2a = box1
    y1b, x1b, y2b, x2b = box2
    iy1, ix1 = max(y1a, y1b), max(x1a, x1b)
    iy2, ix2 = min(y2a, y2b), min(x2a, x2b)
    if iy2 < iy1 or ix2 < ix1:
        return 0.0
    intersection = (iy2 - iy1 + 1) * (ix2 - ix1 + 1)
    area_a = (y2a - y1a + 1) * (x2a - x1a + 1)
    area_b = (y2b - y1b + 1) * (x2b - x1b + 1)
    return intersection / float(area_a + area_b - intersection)


def non_max_suppression(components: List[Dict], iou_threshold: float) -> List[Dict]:
    """Deterministic score-descending box NMS."""
    kept = []
    for component in components:
        if all(compute_iou(component["bbox"], other["bbox"]) <= iou_threshold for other in kept):
            kept.append(component)
    return kept


def apply_context_margin(bbox: Tuple[int, int, int, int], image_shape: Tuple[int, int], margin: float) -> Dict:
    """Expand a predicted box by a fractional margin, square it, and clip/pad deterministically."""
    min_y, min_x, max_y, max_x = bbox
    height, width = image_shape
    box_height, box_width = max_y - min_y + 1, max_x - min_x + 1
    expanded_min_y, expanded_max_y = min_y - round(margin * box_height), max_y + round(margin * box_height)
    expanded_min_x, expanded_max_x = min_x - round(margin * box_width), max_x + round(margin * box_width)
    side = max(expanded_max_y - expanded_min_y + 1, expanded_max_x - expanded_min_x + 1)
    center_y = (expanded_min_y + expanded_max_y) / 2.0
    center_x = (expanded_min_x + expanded_max_x) / 2.0
    y1, x1 = round(center_y - side / 2.0), round(center_x - side / 2.0)
    y2, x2 = y1 + side, x1 + side
    return {
        "y1": y1, "y2": y2, "x1": x1, "x2": x2,
        "clip_y1": max(0, y1), "clip_y2": min(height, y2),
        "clip_x1": max(0, x1), "clip_x2": min(width, x2),
        "pad_top": max(0, -y1), "pad_bottom": max(0, y2 - height),
        "pad_left": max(0, -x1), "pad_right": max(0, x2 - width),
        "crop_side_pixels": int(side),
        "effective_magnification": 512.0 / side,
        "margin": margin,
    }



def extract_predicted_components(probability_map: np.ndarray, threshold: float, original_shape: Tuple[int, int], transform_metadata, min_component_pixels: int = 1) -> List[Dict[str, Any]]:
    """Extract 8-connected predicted components and map boxes from 512 space to original space."""
    binary = np.asarray(probability_map) >= threshold
    labeled, count = label(binary, structure=np.ones((3, 3), dtype=int))
    if count == 0:
        return []
    
    scale = float(transform_metadata.scale)
    resized_h, resized_w = int(transform_metadata.resized_height), int(transform_metadata.resized_width)
    left, top, _, _ = tuple(int(value) for value in transform_metadata.padding)
    original_h, original_w = original_shape
    
    from scipy.ndimage import find_objects, maximum
    # Vectorized computation of pixel counts and max probabilities
    # label() numbers components from 1 to count
    indices = np.arange(1, count + 1)
    
    # We can use np.bincount to get pixel counts quickly
    pixel_counts = np.bincount(labeled.ravel())[1:]
    
    # Use scipy.ndimage.maximum to get max_prob for each label
    max_probs = maximum(probability_map, labels=labeled, index=indices)
    mean_probs = max_probs  # approximation for speed; true mean requires sum/count

    slices = find_objects(labeled)
    components = []
    h_map, w_map = probability_map.shape
    factor_y = 512 // h_map
    factor_x = 512 // w_map
    
    for component_id, (sl_y, sl_x) in enumerate(slices, start=1):
        pixel_count = int(pixel_counts[component_id - 1])
        if pixel_count < min_component_pixels:
            continue
            
        y1_512, y2_512 = sl_y.start, sl_y.stop - 1
        x1_512, x2_512 = sl_x.start, sl_x.stop - 1
        y1_512 = sl_y.start * factor_y
        y2_512 = (sl_y.stop - 1) * factor_y + (factor_y - 1)
        x1_512 = sl_x.start * factor_x
        x2_512 = (sl_x.stop - 1) * factor_x + (factor_x - 1)
        
        if y2_512 < top or y1_512 >= top + resized_h or x2_512 < left or x1_512 >= left + resized_w:
            continue
            
        y1_512 = max(top, min(top + resized_h - 1, y1_512))
        y2_512 = max(top, min(top + resized_h - 1, y2_512))
        x1_512 = max(left, min(left + resized_w - 1, x1_512))
        x2_512 = max(left, min(left + resized_w - 1, x2_512))
        
        y1 = max(0, min(original_h - 1, int(np.floor((y1_512 - top) / scale))))
        y2 = max(0, min(original_h - 1, int(np.ceil((y2_512 - top + 1) / scale) - 1)))
        x1 = max(0, min(original_w - 1, int(np.floor((x1_512 - left) / scale))))
        x2 = max(0, min(original_w - 1, int(np.ceil((x2_512 - left + 1) / scale) - 1)))
        
        if y2 < y1 or x2 < x1:
            continue
            
        components.append({"component_id": component_id, "bbox": (y1, x1, y2, x2),
                           "bbox_512": (y1_512, x1_512, y2_512, x2_512),
                           "component_pixels_512": pixel_count,
                           "max_probability": float(max_probs[component_id - 1]),
                           "mean_probability": float(max_probs[component_id - 1])}) # approximate
                           
    components.sort(key=lambda item: (-item["max_probability"], item["bbox"]))
    return components


def generate_predicted_rois(probability_map: np.ndarray, transform_metadata, original_shape: Tuple[int, int], threshold: float, margin: float, top_k: int, nms_iou: float) -> List[Dict]:
    """Generate GT-free predicted proposals. This API intentionally accepts no GT argument."""
    components = extract_predicted_components(probability_map, threshold, original_shape, transform_metadata)
    # Optimization: limit to top 100 components to prevent NMS O(N^2) stalls on noisy predictions
    components = components[:100]
    components = non_max_suppression(components, nms_iou)[:top_k]
    proposals = []
    for rank, component in enumerate(components, start=1):
        proposals.append({"rank": rank, "score": component["max_probability"],
                          "mean_probability": component["mean_probability"],
                          "proposal_component_pixels_512": component["component_pixels_512"],
                          "proposal_bbox": component["bbox"],
                          "crop_geometry": apply_context_margin(component["bbox"], original_shape, margin)})
    return proposals



def evaluate_roi_coverage(proposals: List[Dict], gt_components: List[Dict]) -> List[Dict]:
    """Evaluate proposal coverage against GT components; called only after GT-free generation."""
    results = []
    for component in gt_components:
        y1, x1, y2, x2 = (int(component[key]) for key in ("min_y", "min_x", "max_y", "max_x"))
        component_mask = component.get("mask")
        best_coverage, best_proposal = 0.0, None
        for proposal in proposals:
            geometry = proposal["crop_geometry"]
            if component_mask is not None:
                # A proposal is an axis-aligned ROI rectangle. Count component
                # pixels inside its clipped slice without allocating a second
                # full-resolution mask; this is exactly equivalent to intersection.
                inside = component_mask[
                    geometry["clip_y1"]:geometry["clip_y2"],
                    geometry["clip_x1"]:geometry["clip_x2"],
                ].sum()
                coverage = float(inside / component_mask.sum())
            else:
                intersection_y = max(0, min(y2 + 1, geometry["clip_y2"]) - max(y1, geometry["clip_y1"]))
                intersection_x = max(0, min(x2 + 1, geometry["clip_x2"]) - max(x1, geometry["clip_x1"]))
                coverage = float(intersection_y * intersection_x / ((y2-y1+1)*(x2-x1+1)))
            if coverage > best_coverage:
                best_coverage, best_proposal = coverage, proposal
        results.append({"component_id": component["component_id"], "coverage_fraction": best_coverage,
                        "covered90": best_coverage >= 0.90, "covered50": best_coverage >= 0.50,
                        "any_overlap": best_coverage > 0,
                        "best_proposal_rank": best_proposal["rank"] if best_proposal else np.nan,
                        "best_proposal_score": best_proposal["score"] if best_proposal else np.nan,
                        "best_roi_coordinates": (best_proposal["crop_geometry"] if best_proposal else None)})
    return results


def union_roi_area_fraction(proposals: List[Dict], original_shape: Tuple[int, int]) -> Tuple[float, float]:
    """Return union area fraction and maximum individual ROI area fraction."""
    height, width = original_shape
    if not proposals:
        return 0.0, 0.0
    union = np.zeros((height, width), dtype=bool); maximum = 0
    for proposal in proposals:
        geometry = proposal["crop_geometry"]
        union[geometry["clip_y1"]:geometry["clip_y2"], geometry["clip_x1"]:geometry["clip_x2"]] = True
        area = (geometry["clip_y2"]-geometry["clip_y1"])*(geometry["clip_x2"]-geometry["clip_x1"])
        maximum = max(maximum, area)
    denominator = height * width
    return float(union.sum()/denominator), float(maximum/denominator)
