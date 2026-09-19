import sys
from pathlib import Path
import pandas as pd
import numpy as np
import torch
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset

def pre_fix_audit():
    print("--- PRE-FIX TARGET AUDIT ---")
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3)
    loader = DataLoader(train_ds, batch_size=4, shuffle=False, num_workers=0)
    
    total_images = len(train_ds)
    # Get actual GT components count from the metadata used by KUBLocalizerDataset
    metadata = pd.read_csv(ROOT / 'reports/tables/kub_train_samples_sized.csv')
    total_components = len(metadata)
    images_with_gt = metadata['sample_id'].nunique()
    
    exact_1_pixels = 0
    images_with_exact_1 = 0
    images_with_zero_exact_1 = 0
    
    # We will manually do the coordinate mapping to check for collisions
    # The dataset uses resized_height, resized_width, etc.
    # We can just run through the dataset metadata.
    
    collisions = 0
    canonical_centers = set()
    
    for batch in loader:
        heatmaps = batch['heatmap']
        for i in range(len(heatmaps)):
            hm = heatmaps[i].numpy()
            pos_mask = (hm == 1.0)
            n_pos = pos_mask.sum()
            exact_1_pixels += n_pos
            if n_pos > 0:
                images_with_exact_1 += 1
            else:
                images_with_zero_exact_1 += 1
                
    # Now for collisions, we look at the metadata mapping
    # Let's see how KUBLocalizerDataset calculates centers
    # Usually it's: y_center = (min_y + max_y)/2. Then scaled.
    # Let's inspect src/inference/heatmap_targets.py to see exactly what we need to fix and how it was calculated.
    print(f"TRAIN images: {total_images}")
    print(f"GT components: {total_components}")
    print(f"Images with >=1 component: {images_with_gt}")
    print(f"Exact-1 pixels BEFORE fix: {exact_1_pixels}")
    print(f"Images with >=1 exact-1 pixel: {images_with_exact_1}")
    print(f"Images with zero exact-1 pixels: {images_with_zero_exact_1}")

if __name__ == "__main__":
    pre_fix_audit()

