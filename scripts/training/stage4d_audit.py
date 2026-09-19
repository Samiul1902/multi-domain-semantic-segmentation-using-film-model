import sys
from pathlib import Path
import pandas as pd
import numpy as np
from collections import defaultdict
import json
import math
from scipy.ndimage import label
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def compute_collisions(components, output_res, original_res=512):
    """
    components: list of (cy, cx) in 512-space
    output_res: target resolution (e.g., 256)
    """
    factor = original_res / output_res
    mapped = []
    for cy, cx in components:
        my = int(round(cy / factor))
        mx = int(round(cx / factor))
        # Ensure within bounds
        my = max(0, min(my, output_res - 1))
        mx = max(0, min(mx, output_res - 1))
        mapped.append((my, mx))
        
    unique_centers = set(mapped)
    collisions = len(mapped) - len(unique_centers)
    
    # max components in one pixel
    counts = defaultdict(int)
    for p in mapped:
        counts[p] += 1
    max_in_pixel = max(counts.values()) if counts else 0
    
    return len(mapped), len(unique_centers), collisions, max_in_pixel

def run_audit():
    train_df = pd.read_csv(ROOT / "reports/tables/kub_train_samples_sized.csv")
    train_df = train_df[train_df["view_type"] == "FULL_FIELD"]
    val_df = pd.read_csv(ROOT / "reports/tables/kub_val_samples_sized.csv")
    val_df = val_df[val_df["view_type"] == "FULL_FIELD"]
    
    results = {}
    
    for split_name, df in [("TRAIN", train_df), ("VAL", val_df)]:
        samples_with_collision = {r: 0 for r in [512, 256, 128, 64]}
        total_collisions = {r: 0 for r in [512, 256, 128, 64]}
        max_per_pixel = {r: 0 for r in [512, 256, 128, 64]}
        total_components = 0
        total_unique = {r: 0 for r in [512, 256, 128, 64]}
        
        for _, row in df.iterrows():
            with Image.open(row.mask_path) as mask_file:
                mask = mask_file.convert("L")
            orig_mask_array = np.asarray(mask) > 0
            labels, count = label(orig_mask_array, np.ones((3, 3), int))
            orig_centroids = []
            for component_id in range(1, count+1):
                ys, xs = np.where(labels == component_id)
                orig_centroids.append((float(ys.mean()), float(xs.mean())))
                
            width, height = int(row.width), int(row.height)
            scale = min(512 / width, 512 / height)
            rw, rh = max(1, round(width*scale)), max(1, round(height*scale))
            left, top = (512-rw)//2, (512-rh)//2
            
            sample_components_512 = []
            for cy, cx in orig_centroids:
                cx = cx * scale + left
                cy = cy * scale + top
                sample_components_512.append((cy, cx))
            total_components += count
            
            for res in [512, 256, 128, 64]:
                n_map, n_unq, col, max_pix = compute_collisions(sample_components_512, res)
                total_collisions[res] += col
                total_unique[res] += n_unq
                max_per_pixel[res] = max(max_per_pixel[res], max_pix)
                if col > 0:
                    samples_with_collision[res] += 1
                    
        res_stats = {}
        for res in [512, 256, 128, 64]:
            res_stats[str(res)] = {
                "authoritative_components": total_components,
                "mapped_centers": total_components,
                "unique_centers": total_unique[res],
                "collisions": total_collisions[res],
                "samples_with_collision": samples_with_collision[res],
                "max_centers_per_pixel": max_per_pixel[res],
                "pixels": res * res,
                "pixels_per_positive": (res * res) / max(1, total_components / len(df))
            }
            
        results[split_name] = res_stats
        
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    run_audit()
