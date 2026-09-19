import os
import pandas as pd
import numpy as np
import hashlib
from pathlib import Path

# Settings
SEED = 42
RAW_ROOT = Path(r'D:\Softfors\omni_seg\data_raw')
KUB_PAIRS = Path(r'D:\Softfors\jup\reports\audits\kub_image_mask_pairs.csv')
MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')

def get_sample_id(row):
    return hashlib.md5(f"{row['image_path']}{row['mask_path']}".encode()).hexdigest()

# 1. Collect KUB Pairs
kub_df = pd.read_csv(KUB_PAIRS)
kub_df = kub_df[kub_df['pair_status'] == 'PAIRED'].copy()
kub_df['dataset'] = 'KUB'
kub_df['task_id'] = 3
kub_df['case_id'] = 'NOT_AVAILABLE'
kub_df = kub_df.rename(columns={'path_img': 'image_path', 'path_mask': 'mask_path', 'category': 'category'})
# Robust patient ID extraction
def extract_pid(path_str):                
    parts = Path(path_str).parts
    for part in parts:
        if 'patient-' in part.lower():                
            return part
    return 'NOT_AVAILABLE'
kub_df['patient_id'] = kub_df['image_path'].apply(extract_pid)

# 2. Collect Others
def get_inventory(root, img_ext, mask_func):
    d = []                
    for f in root.rglob('*' + img_ext):
        m = mask_func(f)
        if m.exists():
            d.append({'image_path': str(f), 'mask_path': str(m)})
    return pd.DataFrame(d)

isic = get_inventory(RAW_ROOT / 'isic2018', '.jpg', lambda f: f.with_name(f.name.replace('.jpg', '_segmentation.png')))
isic['dataset'] = 'ISIC'; isic['task_id'] = 0

busi_root = RAW_ROOT / 'BUSI_WHU Breast Cancer Ultrasound Image  Dataset' / 'BUSI-WHU'
busi = get_inventory(busi_root / 'img', '.bmp', lambda f: busi_root / 'gt' / f.name.replace('.bmp', '_anno.png'))
busi['dataset'] = 'BUSI'; busi['task_id'] = 1

kvasir = get_inventory(RAW_ROOT / 'Kvasir-SEG' / 'images', '.jpg', lambda f: RAW_ROOT / 'Kvasir-SEG' / 'masks' / f.name)
kvasir['dataset'] = 'KVASIR'; kvasir['task_id'] = 2

# Concatenate
cols = ['dataset','task_id','image_path','mask_path','patient_id','case_id','category']
for df in [isic, busi, kvasir]:
    # ISIC/BUSI/Kvasir didn't have these, add them
    df['patient_id'] = 'NOT_AVAILABLE'
    df['case_id'] = 'NOT_AVAILABLE'
    df['category'] = 'NOT_AVAILABLE'
                
all_paired = pd.concat([kub_df[cols], isic[cols], busi[cols], kvasir[cols]])                
all_paired['split'] = 'TEST' 

# 3. Splitting
kub = all_paired[all_paired['dataset']=='KUB'].copy()
rest = all_paired[all_paired['dataset']!='KUB'].sample(frac=1, random_state=SEED).copy()

# KUB Patient split 
rng = np.random.default_rng(42)
pats = kub['patient_id'].unique()
rng.shuffle(pats)
train_p, val_p = [], []
train_s, val_s = 0, 0
for pid in pats:
    count = len(kub[kub['patient_id'] == pid])
    if train_s < 1974:
        train_p.append(pid)
        train_s += count
    elif val_s < 282:                
        val_p.append(pid)
        val_s += count
kub.loc[kub['patient_id'].isin(train_p), 'split'] = 'TRAIN'
kub.loc[kub['patient_id'].isin(val_p), 'split'] = 'VAL'

# Rest split
n_r = len(rest)
rest.iloc[:int(0.7 * n_r), rest.columns.get_loc('split')] = 'TRAIN'
rest.iloc[int(0.7 * n_r):int(0.8 * n_r), rest.columns.get_loc('split')] = 'VAL'

full = pd.concat([kub, rest])
full['sample_id'] = full.apply(lambda row: hashlib.md5((row['image_path']+row['mask_path']).encode()).hexdigest(), axis=1)

full.to_csv(MANIFEST_DIR / 'all_paired.csv', index=False)
full[full['split']=='TRAIN'].to_csv(MANIFEST_DIR / 'train.csv', index=False)
full[full['split']=='VAL'].to_csv(MANIFEST_DIR / 'val.csv', index=False)
full[full['split']=='TEST'].to_csv(MANIFEST_DIR / 'test.csv', index=False)
print('Splits saved.')
print(full.groupby(['dataset', 'split']).size())
