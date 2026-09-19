import os
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path

SEED = 42
RAW_ROOT = Path(r'D:\Softfors\omni_seg\data_raw')
KUB_PAIRS = Path(r'D:\Softfors\jup\reports\audits\kub_image_mask_pairs.csv')
MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')
MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

def get_sample_id(row):
    return hashlib.md5((row['image_path'] + row['mask_path']).encode()).hexdigest()

# 1. KUB Pairs
kub_df = pd.read_csv(KUB_PAIRS)
kub_df = kub_df[kub_df['pair_status'] == 'PAIRED'].copy()
kub_df['dataset'] = 'KUB'
kub_df['task_id'] = 3
kub_df['case_id'] = 'NOT_AVAILABLE'
kub_df = kub_df.rename(columns={'path_img': 'image_path', 'path_mask': 'mask_path', 'category': 'category'})
kub_df['patient_id'] = kub_df['image_path'].apply(lambda p: 'patient-' + Path(p).name.split('-')[0])

# 2. ISIC Pairs (3694)
isic_root = RAW_ROOT / 'isic2018'
isic_imgs = {f.name.replace('.jpg', ''): f for f in isic_root.rglob('*.jpg') if 'segmentation' not in f.name}
isic_masks = {f.name.replace('_segmentation.png', ''): f for f in isic_root.rglob('*_segmentation.png')}
isic_data = []
for k in isic_imgs:
    if k in isic_masks:
        isic_data.append({
            'dataset': 'ISIC', 'task_id': 0, 'image_path': str(isic_imgs[k]), 'mask_path': str(isic_masks[k]),
            'patient_id': 'NOT_AVAILABLE', 'case_id': 'NOT_AVAILABLE', 'category': 'NOT_AVAILABLE'
        })
isic_df = pd.DataFrame(isic_data)

# 3. BUSI Pairs (927)
busi_root = RAW_ROOT / 'BUSI_WHU Breast Cancer Ultrasound Image  Dataset' / 'BUSI-WHU'
busi_imgs = {f.name.replace('.bmp', ''): f for f in (busi_root / 'img').glob('*.bmp')}
busi_masks = {f.name.replace('_anno.bmp', ''): f for f in (busi_root / 'gt').glob('*_anno.bmp')}
busi_data = []
for k in busi_imgs:
    if k in busi_masks:
        busi_data.append({
            'dataset': 'BUSI', 'task_id': 1, 'image_path': str(busi_imgs[k]), 'mask_path': str(busi_masks[k]),
            'patient_id': 'NOT_AVAILABLE', 'case_id': 'NOT_AVAILABLE', 'category': 'NOT_AVAILABLE'
        })
busi_df = pd.DataFrame(busi_data)

# 4. KVASIR Pairs (1000)
kv_root = RAW_ROOT / 'Kvasir-SEG'
kv_imgs = {f.name.replace('.jpg', ''): f for f in (kv_root / 'images').glob('*.jpg')}
kv_masks = {f.name.replace('.jpg', ''): f for f in (kv_root / 'masks').glob('*.jpg')}
kv_data = []
for k in kv_imgs:
    if k in kv_masks:
        kv_data.append({
            'dataset': 'KVASIR', 'task_id': 2, 'image_path': str(kv_imgs[k]), 'mask_path': str(kv_masks[k]),
            'patient_id': 'NOT_AVAILABLE', 'case_id': 'NOT_AVAILABLE', 'category': 'NOT_AVAILABLE'
        })
kv_df = pd.DataFrame(kv_data)

cols = ['dataset','task_id','image_path','mask_path','patient_id','case_id','category']

all_paired = pd.concat([kub_df[cols], isic_df[cols], busi_df[cols], kv_df[cols]]).reset_index(drop=True)
all_paired['sample_id'] = all_paired.apply(get_sample_id, axis=1)
all_paired['split'] = 'TEST'

# 5. Deterministic Splitting
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

# Rest (Sample-level deterministic split with SEED 42)
rest = rest.sample(frac=1, random_state=SEED).copy()
n_r = len(rest)
rest.iloc[:int(0.7 * n_r), rest.columns.get_loc('split')] = 'TRAIN'
rest.iloc[int(0.7 * n_r):int(0.8 * n_r), rest.columns.get_loc('split')] = 'VAL'

full = pd.concat([kub, rest]).reset_index(drop=True)

# Save
full.to_csv(MANIFEST_DIR / 'all_paired.csv', index=False)
full[full['split']=='TRAIN'].to_csv(MANIFEST_DIR / 'train.csv', index=False)
full[full['split']=='VAL'].to_csv(MANIFEST_DIR / 'val.csv', index=False)
full[full['split']=='TEST'].to_csv(MANIFEST_DIR / 'test.csv', index=False)

print("SAVED MANIFESTS:")
print(full.groupby(['dataset', 'split']).size().unstack(fill_value=0))
