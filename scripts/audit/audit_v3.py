import os
import pandas as pd
import numpy as np
from PIL import Image
import json
import csv

def scan_dataset(root, img_exts, mask_exts):
    files_data = []
    for r, _, files in os.walk(root):
        for f in files:
            path = os.path.join(r, f)
            ext = os.path.splitext(f)[1].lower()
            is_img = ext in img_exts
            is_mask = ext in mask_exts
            files_data.append({'path': path, 'name': f, 'is_img': is_img, 'is_mask': is_mask, 'root': r})
    return pd.DataFrame(files_data)

def audit_dataset(name, root, img_exts, mask_exts, pairing_rule):
    df = scan_dataset(root, img_exts, mask_exts)
    imgs = df[df['is_img']]
    masks = df[df['is_mask']]
    
    # Simple pairing (This needs to be specialized per dataset)
    # Using name as key for pairing for now
    matched = 0
    unmatched_imgs = len(imgs)
    unmatched_masks = len(masks)
    
    # Placeholder for actual pairing logic
    return {
        "dataset": name,
        "images": len(imgs),
        "masks": len(masks),
        "matched": 0,
        "unmatched_imgs": unmatched_imgs,
        "unmatched_masks": unmatched_masks,
    }

# Run audit...
# Simplified report generation
results = {}
# ... implemented for real
print(json.dumps(results))
