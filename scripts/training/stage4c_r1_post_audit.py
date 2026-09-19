import sys
from pathlib import Path
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.inference.heatmap_targets import get_component_centroids_in_localizer_space

def post_fix_audit():
    print("--- POST-FIX TARGET AUDIT ---")
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3)
    loader = DataLoader(train_ds, batch_size=1, shuffle=False, num_workers=0)
    
    metadata = pd.read_csv(ROOT / 'reports/tables/kub_train_samples_sized.csv')
    total_components = len(metadata)
    
    unique_center_pixels = set()
    zero_pos_images = 0
    in_range = True
    deterministic = True
    
    collisions = 0
    affected_images = set()
    affected_components = set()
    
    for idx, batch in enumerate(loader):
        hm = batch['heatmap'][0].numpy()
        hm2 = train_ds[idx]['heatmap'].numpy()
        
        if not np.array_equal(hm, hm2):
            deterministic = False
        
        if hm.max() > 1.0 or hm.min() < 0.0:
            in_range = False
            
        pos_mask = (hm == 1.0)
        n_pos = pos_mask.sum()
        
        if hm.max() == 0:
            zero_pos_images += 1
        
        # Calculate collisions based on canonical centers
        sid = batch['sample_id'][0]
        row = metadata[metadata.sample_id == sid].iloc[0]
        
        if not pd.isna(row.mask_path):
            centroids = get_component_centroids_in_localizer_space(
                ROOT / row.mask_path, float(batch['scale'][0]), int(batch['resized_height'][0]), int(batch['resized_width'][0]), int(batch['padding'][0][0]), int(batch['padding'][0][1])
            )
            canonical_centers = set()
            for cy, cx in centroids:
                icy = max(0, min(511, int(round(cy))))
                icx = max(0, min(511, int(round(cx))))
                if (icy, icx) in canonical_centers:
                    collisions += 1
                    affected_images.add(sid)
                else:
                    canonical_centers.add((icy, icx))
                    unique_center_pixels.add((sid, icy, icx))
        
    print(f"GT components: {total_components}")
    print(f"unique center pixels: {len(unique_center_pixels)}")
    print(f"zero-positive images: {zero_pos_images}")
    print(f"target range [0,1]: {in_range}")
    print(f"deterministic: {deterministic}")
    print(f"collisions: {collisions}")
    if collisions > 0:
        print(f"affected images: {len(affected_images)}")
        
def diff_audit():
    print("\n--- CHANGE MAGNITUDE ---")
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3)
    loader = DataLoader(train_ds, batch_size=1, shuffle=False, num_workers=0)
    
    pixels_changed = []
    max_diffs = []
    
    # We need to compute the pre-fix heatmap to compare.
    # Pre-fix was just sum of gaussians, wait, maximum of gaussians without the center forced to 1.0
    for idx, batch in enumerate(loader):
        hm_post = batch['heatmap'][0].numpy()
        
        # Manually compute pre-fix
        sid = batch['sample_id'][0]
        row = pd.read_csv(ROOT / 'reports/tables/kub_train_samples_sized.csv').query(f"sample_id == '{sid}'").iloc[0]
        
        if pd.isna(row.mask_path):
            hm_pre = np.zeros((512, 512), dtype=np.float32)
        else:
            centroids = get_component_centroids_in_localizer_space(
                ROOT / row.mask_path, float(batch['scale'][0]), int(batch['resized_height'][0]), int(batch['resized_width'][0]), int(batch['padding'][0][0]), int(batch['padding'][0][1])
            )
            heatmap = np.zeros((512, 512), dtype=np.float32)
            ys = np.arange(512, dtype=np.float32).reshape(-1, 1)
            xs = np.arange(512, dtype=np.float32).reshape(1, -1)
            for cy, cx in centroids:
                comp_hm = np.exp(-((ys - cy)**2 + (xs - cx)**2) / (2 * 3**2)).astype(np.float32)
                heatmap = np.maximum(heatmap, comp_hm)
            hm_pre = heatmap
            
        diff = hm_post - hm_pre
        pixels_changed.append(np.count_nonzero(diff))
        max_diffs.append(np.max(np.abs(diff)))
        
    print(f"pixels changed total: {np.sum(pixels_changed)}")
    print(f"mean changed pixels/image: {np.mean(pixels_changed):.2f}")
    print(f"max changed pixels/image: {np.max(pixels_changed)}")
    print(f"max absolute difference: {np.max(max_diffs):.4f}")

if __name__ == "__main__":
    post_fix_audit()
    diff_audit()
