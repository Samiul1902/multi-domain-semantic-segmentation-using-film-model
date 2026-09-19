import os
import pandas as pd

def get_stats(dataset_name, root, img_ext, mask_ext):
    images = []
    masks = []
    for r, _, files in os.walk(root):
        for f in files:
            if f.endswith(img_ext): images.append(os.path.join(r, f))
            if f.endswith(mask_ext): masks.append(os.path.join(r, f))
    return len(images), len(masks)
