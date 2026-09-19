import os
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
from scipy.ndimage import label

def analyze_kub_mask_v2(mask_path, connectivity=8):
    img = Image.open(mask_path).convert('L')
    arr = np.array(img)
    w, h = img.size
    total_pixels = h * w
    
    # Semantic foreground definition: any positive pixel value > 0
    fg_mask = (arr > 0).astype(np.uint8)
    fg_pixels = int(np.sum(fg_mask))
    fg_ratio = float(fg_pixels / total_pixels)
    
    if fg_pixels > 0:
        rows = np.any(fg_mask, axis=1)
        cols = np.any(fg_mask, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        bbox_h = int(rmax - rmin + 1)
        bbox_w = int(cmax - cmin + 1)
        bbox_area = int(bbox_h * bbox_w)
        bbox_ratio = float(bbox_area / total_pixels)
    else:
        bbox_h, bbox_w, bbox_area, bbox_ratio = 0, 0, 0, 0.0

    # 8-connectivity component labeling
    structure = np.ones((3, 3), dtype=int) if connectivity == 8 else np.array([[0,1,0],[1,1,1],[0,1,0]], dtype=int)
    labeled_mask, num_features = label(fg_mask, structure=structure)
    
    components = []
    comp_pixel_sum = 0
    for c_id in range(1, num_features + 1):
        c_map = (labeled_mask == c_id)
        c_pixels = int(np.sum(c_map))
        comp_pixel_sum += c_pixels
        c_ratio = float(c_pixels / total_pixels)
        
        c_rows = np.any(c_map, axis=1)
        c_cols = np.any(c_map, axis=0)
        c_rmin, c_rmax = np.where(c_rows)[0][[0, -1]]
        c_cmin, c_cmax = np.where(c_cols)[0][[0, -1]]
        c_bbox_h = int(c_rmax - c_rmin + 1)
        c_bbox_w = int(c_cmax - c_cmin + 1)
        c_bbox_area = int(c_bbox_h * c_bbox_w)
        c_bbox_ratio = float(c_bbox_area / total_pixels)
        
        cy, cx = np.mean(np.where(c_map), axis=1)
        cx_norm = float(cx / w)
        cy_norm = float(cy / h)
        
        components.append({
            'component_id': c_id,
            'component_pixels': c_pixels,
            'component_ratio': c_ratio,
            'bbox_width': c_bbox_w,
            'bbox_height': c_bbox_h,
            'bbox_area': c_bbox_area,
            'bbox_ratio': c_bbox_ratio,
            'centroid_x': float(cx),
            'centroid_y': float(cy),
            'centroid_x_norm': cx_norm,
            'centroid_y_norm': cy_norm
        })

    # Conservation assertion
    assert comp_pixel_sum == fg_pixels, f"Component area sum {comp_pixel_sum} != fg_pixels {fg_pixels}"
        
    return {
        'width': w,
        'height': h,
        'aspect_ratio': float(w / h),
        'foreground_pixels': fg_pixels,
        'foreground_ratio': fg_ratio,
        'bbox_width': bbox_w,
        'bbox_height': bbox_h,
        'bbox_area': bbox_area,
        'bbox_ratio': bbox_ratio,
        'component_count': num_features,
        'components': components
    }
