"""
DO_NOT_RUN_AFTER_PHASE4_FREEZE
Legacy script for building phase4_v2 manifests.
Authoritative manifests are frozen under manifests/
"""

import os
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path
import json

SEED = 42
RAW_ROOT = Path(r'D:\Softfors\omni_seg\data_raw')
KUB_PAIRS = Path(r'D:\Softfors\jup\reports\audits\kub_image_mask_pairs.csv')
MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')

def get_sample_id(row):
    return hashlib.md5((row['image_path'] + row['mask_path']).encode()).hexdigest()

# KUB Pairs
kub_df = pd.read_csv(KUB_PAIRS)
kub_df = kub_df[kub_df['pair_status'] == 'PAIRED'].copy()
kub_df['dataset'] = 'KUB'
kub_df['task_id'] = 3
kub_df['case_id'] = 'NOT_AVAILABLE'
kub_df = kub_df.rename(columns={'path_img': 'image_path', 'path_mask': 'mask_path', 'category': 'category'})
kub_df['patient_id'] = kub_df['image_path'].apply(lambda p: 'patient-' + Path(p).name.split('-')[0])

# ISIC, BUSI, KVASIR
def get_inventory(root, img_ext, mask_func, mask_ext='_anno.png'):
    d = []
    for f in root.rglob('*' + img_ext):
        if 'segmentation' in str(f) or 'ann' in str(f) or 'mask' in str(f): continue
        m = mask_func(f)
        if not m.exists() and mask_ext == '_anno.png':
            m = f.with_name(f.name.replace('.bmp', '_anno.bmp'))
        if m.exists():
            d.append({'image_path': str(f), 'mask_path': str(m)})
    return pd.DataFrame(d)

isic = get_inventory(RAW_ROOT / 'isic2018', '.jpg', lambda f: f.with_name(f.name.replace('.jpg', '_segmentation.png')), '_segmentation.png')
isic['dataset'] = 'ISIC'; isic['task_id'] = 0

busi_root = RAW_ROOT / 'BUSI_WHU Breast Cancer Ultrasound Image  Dataset' / 'BUSI-WHU'
busi = get_inventory(busi_root / 'img', '.bmp', lambda f: busi_root / 'gt' / f.name.replace('.bmp', '_anno.bmp'), '_anno.bmp')
busi['dataset'] = 'BUSI'; busi['task_id'] = 1

kvasir = get_inventory(RAW_ROOT / 'Kvasir-SEG' / 'images', '.jpg', lambda f: RAW_ROOT / 'Kvasir-SEG' / 'masks' / f.name, '.jpg')
kvasir['dataset'] = 'KVASIR'; kvasir['task_id'] = 2

cols = ['dataset','task_id','image_path','mask_path','patient_id','case_id','category']
for df in [isic, busi, kvasir]:
    df['patient_id'] = 'NOT_AVAILABLE'
    df['case_id'] = 'NOT_AVAILABLE'
    df['category'] = 'NOT_AVAILABLE'

all_paired = pd.concat([kub_df[cols], isic[cols], busi[cols], kvasir[cols]])
all_paired['sample_id'] = all_paired.apply(get_sample_id, axis=1)
all_paired['split'] = 'TEST'

# Splitting
kub = all_paired[all_paired['dataset'] == 'KUB'].copy()
rest = all_paired[all_paired['dataset'] != 'KUB'].copy()

pats = kub.groupby('patient_id').size().reset_index(name='count')
pats = pats.sort_values(by='count', ascending=False)

train_p, val_p, test_p = [], [], []
train_c, val_c = 0, 0
for _, row in pats.iterrows():
    pid = row['patient_id']
    cnt = row['count']
    if train_c + cnt <= 1979:
        train_p.append(pid)
        train_c += cnt
    elif val_c + cnt <= 283:
        val_p.append(pid)
        val_c += cnt
    else:
        test_p.append(pid)

kub.loc[kub['patient_id'].isin(train_p), 'split'] = 'TRAIN'
kub.loc[kub['patient_id'].isin(val_p), 'split'] = 'VAL'
kub.loc[kub['patient_id'].isin(test_p), 'split'] = 'TEST'

rest = rest.sample(frac=1, random_state=SEED).copy()
n_r = len(rest)
rest.iloc[:int(0.7 * n_r), rest.columns.get_loc('split')] = 'TRAIN'
rest.iloc[int(0.7 * n_r):int(0.8 * n_r), rest.columns.get_loc('split')] = 'VAL'

full = pd.concat([kub, rest]).reset_index(drop=True)
print("Dry-run build complete for manifest_builder_final_v2.py")
