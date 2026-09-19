import os
import json
import hashlib
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw

from src.analysis.kub_characterization import analyze_kub_mask

# Set up paths
PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests'
TABLES_DIR = PROJECT_ROOT / 'reports' / 'tables'
FIGURES_DIR = PROJECT_ROOT / 'reports' / 'figures' / 'kub_characterization'
QUAL_DIR = PROJECT_ROOT / 'reports' / 'qualitative' / 'kub_characterization'
AUDIT_DIR = PROJECT_ROOT / 'reports' / 'audits'

TABLES_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)
QUAL_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

train_df = pd.read_csv(MANIFEST_DIR / 'train.csv')
val_df = pd.read_csv(MANIFEST_DIR / 'val.csv')

kub_train = train_df[train_df['dataset'] == 'KUB'].copy()
kub_val = val_df[val_df['dataset'] == 'KUB'].copy()

print(f"KUB Train samples: {len(kub_train)}, KUB Val samples: {len(kub_val)}")

# Analyze Train Samples
sample_records = []
component_records = []

for _, row in kub_train.iterrows():
    res = analyze_kub_mask(row['mask_path'], connectivity=8)
    
    comp_list = res.pop('components')
    
    # Store component stats in sample record
    c_pixels = [c['component_pixels'] for c in comp_list]
    largest_c_pixels = max(c_pixels) if c_pixels else 0
    smallest_c_pixels = min(c_pixels) if c_pixels else 0
    median_c_pixels = float(np.median(c_pixels)) if c_pixels else 0.0
    
    sample_rec = {
        'sample_id': row['sample_id'],
        'patient_id': row['patient_id'],
        'category': row['category'],
        'image_path': row['image_path'],
        'mask_path': row['mask_path'],
        'width': res['width'],
        'height': res['height'],
        'aspect_ratio': res['aspect_ratio'],
        'foreground_pixels': res['foreground_pixels'],
        'foreground_ratio': res['foreground_ratio'],
        'bbox_width': res['bbox_width'],
        'bbox_height': res['bbox_height'],
        'bbox_area': res['bbox_area'],
        'bbox_ratio': res['bbox_ratio'],
        'component_count': res['component_count'],
        'largest_component_pixels': largest_c_pixels,
        'largest_component_ratio': largest_c_pixels / (res['width'] * res['height']),
        'smallest_component_pixels': smallest_c_pixels,
        'median_component_pixels': median_c_pixels
    }
    sample_records.append(sample_rec)
    
    for c in comp_list:
        c_rec = {
            'sample_id': row['sample_id'],
            'patient_id': row['patient_id'],
            'category': row['category'],
            **c
        }
        component_records.append(c_rec)

df_samples = pd.DataFrame(sample_records)
df_components = pd.DataFrame(component_records)

df_samples.to_csv(TABLES_DIR / 'kub_train_sample_characteristics.csv', index=False)
df_components.to_csv(TABLES_DIR / 'kub_train_components.csv', index=False)

print("Saved sample & component characteristics tables.")
