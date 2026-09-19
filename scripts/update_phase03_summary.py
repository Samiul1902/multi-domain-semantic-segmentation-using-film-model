import pandas as pd
import json
from pathlib import Path

with open('manifests/manifest_metadata.json', 'r', encoding='utf-8') as f:
    meta = json.load(f)

summary = [
    {
        'dataset': 'ISIC 2018',
        'domain': 'Dermoscopy',
        'pixel_target': 'Skin lesion vs background',
        'mask_type': 'Binary',
        'subclass_metadata': 'Melanoma / Nevus / Keratosis (image-level diagnostic)',
        'used_as_pixel_class': 'NO',
        'paired_count': meta['dataset_counts']['ISIC'],
        'train_count': meta['dataset_split_counts']['ISIC']['TRAIN'],
        'val_count': meta['dataset_split_counts']['ISIC']['VAL'],
        'test_count': meta['dataset_split_counts']['ISIC']['TEST'],
        'sample_visualization_count': 12,
        'channel_summary': 'RGB (3 channels)',
        'pairing_status': 'PASS (100% paired)'
    },
    {
        'dataset': 'BUSI',
        'domain': 'Breast Ultrasound',
        'pixel_target': 'Breast lesion vs background',
        'mask_type': 'Binary',
        'subclass_metadata': 'Benign / Malignant / Normal (image-level category)',
        'used_as_pixel_class': 'NO',
        'paired_count': meta['dataset_counts']['BUSI'],
        'train_count': meta['dataset_split_counts']['BUSI']['TRAIN'],
        'val_count': meta['dataset_split_counts']['BUSI']['VAL'],
        'test_count': meta['dataset_split_counts']['BUSI']['TEST'],
        'sample_visualization_count': 12,
        'channel_summary': 'RGB/Grayscale (3 channels)',
        'pairing_status': 'PASS (100% paired)'
    },
    {
        'dataset': 'Kvasir-SEG',
        'domain': 'GI Endoscopy',
        'pixel_target': 'Polyp vs background',
        'mask_type': 'Binary',
        'subclass_metadata': 'NOT ESTABLISHED (single-target polyp segmentation)',
        'used_as_pixel_class': 'NO',
        'paired_count': meta['dataset_counts']['KVASIR'],
        'train_count': meta['dataset_split_counts']['KVASIR']['TRAIN'],
        'val_count': meta['dataset_split_counts']['KVASIR']['VAL'],
        'test_count': meta['dataset_split_counts']['KVASIR']['TEST'],
        'sample_visualization_count': 12,
        'channel_summary': 'RGB (3 channels)',
        'pairing_status': 'PASS (100% paired)'
    },
    {
        'dataset': 'KUB-Stone',
        'domain': 'Plain Radiography (X-Ray)',
        'pixel_target': 'Stone vs background',
        'mask_type': 'Binary',
        'subclass_metadata': 'Kidney / Bladder / Ureteric (case-level anatomical location)',
        'used_as_pixel_class': 'NO',
        'paired_count': meta['dataset_counts']['KUB'],
        'train_count': meta['dataset_split_counts']['KUB']['TRAIN'],
        'val_count': meta['dataset_split_counts']['KUB']['VAL'],
        'test_count': meta['dataset_split_counts']['KUB']['TEST'],
        'sample_visualization_count': 12,
        'channel_summary': 'Grayscale/RGB (3 channels)',
        'pairing_status': 'PASS (100% paired)'
    }
]

df_sum = pd.DataFrame(summary)
df_sum.to_csv('reports/tables/phase03_dataset_discovery_summary.csv', index=False)
print('Updated reports/tables/phase03_dataset_discovery_summary.csv with precise pixel-level targets and metadata distinctions.')

