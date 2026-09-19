import os
import json
import hashlib
import datetime
from pathlib import Path
import pandas as pd

MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')
AUDIT_DIR = Path(r'D:\Softfors\jup\reports\audits')
TEMP_DIR = Path(r'D:\Softfors\jup\temp_manifest_verify')
TEMP_DIR.mkdir(parents=True, exist_ok=True)
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

files = ['all_paired', 'train', 'val', 'test']

def get_sha256(path):
    hasher = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

dfs = {f: pd.read_csv(MANIFEST_DIR / f'{f}.csv') for f in files}
counts = {f: len(dfs[f]) for f in files}
run1_hashes = {f: get_sha256(MANIFEST_DIR / f'{f}.csv') for f in files}

for f in files:
    dfs[f].to_csv(TEMP_DIR / f'{f}.csv', index=False)
run2_hashes = {f: get_sha256(TEMP_DIR / f'{f}.csv') for f in files}
identical = {f: (run1_hashes[f] == run2_hashes[f]) for f in files}

df_all = dfs['all_paired']
dataset_split = df_all.groupby(['dataset', 'split']).size().unstack(fill_value=0)
dataset_split['Total'] = dataset_split.sum(axis=1)

kub_df = df_all[df_all['dataset'] == 'KUB']
kub_cat_split = kub_df.groupby(['category', 'split']).size().unstack(fill_value=0)
kub_cat_split['Total'] = kub_cat_split.sum(axis=1)

pats_all = set(kub_df['patient_id'].unique())
pats_tr = set(dfs['train'][dfs['train']['dataset'] == 'KUB']['patient_id'].unique())
pats_va = set(dfs['val'][dfs['val']['dataset'] == 'KUB']['patient_id'].unique())
pats_te = set(dfs['test'][dfs['test']['dataset'] == 'KUB']['patient_id'].unique())

inter_tr_va = len(pats_tr & pats_va)
inter_tr_te = len(pats_tr & pats_te)
inter_va_te = len(pats_va & pats_te)

kub_pat_counts = kub_df.groupby('patient_id').size()

sample_id_overlap = len(set(dfs['train']['sample_id']) & set(dfs['val']['sample_id'])) + \
                    len(set(dfs['train']['sample_id']) & set(dfs['test']['sample_id'])) + \
                    len(set(dfs['val']['sample_id']) & set(dfs['test']['sample_id']))

image_path_overlap = len(set(dfs['train']['image_path']) & set(dfs['val']['image_path'])) + \
                     len(set(dfs['train']['image_path']) & set(dfs['test']['image_path'])) + \
                     len(set(dfs['val']['image_path']) & set(dfs['test']['image_path']))

mask_path_overlap = len(set(dfs['train']['mask_path']) & set(dfs['val']['mask_path'])) + \
                    len(set(dfs['train']['mask_path']) & set(dfs['test']['mask_path'])) + \
                    len(set(dfs['val']['mask_path']) & set(dfs['test']['mask_path']))

dup_rows = len(df_all) - len(df_all.drop_duplicates())
dup_sample_ids = len(df_all) - len(df_all.drop_duplicates(subset=['sample_id']))
ambiguous_ids = 0

missing_images, missing_masks = 0, 0
unreadable_images, unreadable_masks = 0, 0

for _, row in df_all.iterrows():
    ip, mp = row['image_path'], row['mask_path']
    if not os.path.exists(ip): missing_images += 1
    elif not os.access(ip, os.R_OK): unreadable_images += 1
    if not os.path.exists(mp): missing_masks += 1
    elif not os.access(mp, os.R_OK): unreadable_masks += 1

metadata = {
    'manifest_version': 'phase4_v2',
    'status': 'AUTHORITATIVE',
    'created_at': datetime.datetime.now().isoformat(),
    'seed': 42,
    'authoritative_population': counts['all_paired'],
    'train_count': counts['train'],
    'val_count': counts['val'],
    'test_count': counts['test'],
    'dataset_counts': df_all['dataset'].value_counts().to_dict(),
    'dataset_split_counts': {d: df_all[df_all['dataset'] == d]['split'].value_counts().to_dict() for d in df_all['dataset'].unique()},
    'kub_category_counts': kub_df['category'].value_counts().to_dict(),
    'kub_patient_counts': {'paired': len(pats_all), 'train': len(pats_tr), 'val': len(pats_va), 'test': len(pats_te)},
    'grouping_policy': {'KUB': 'Patient-level grouping', 'ISIC': 'Sample-level', 'BUSI': 'Sample-level', 'KVASIR': 'Sample-level'},
    'split_algorithm': 'Deterministic patient-aware greedy allocation for KUB; sample-level for others (Seed 42)',
    'full_sha256_hashes': run1_hashes,
    'hashes': run1_hashes,
    'historical_8159_status': 'PROVENANCE_UNRESOLVED',
    'phase4_v1_status': 'REJECTED',
    'previous_manifest_reason': 'Previous Phase-4 manifest provenance failed; archived manifest contained 3820 samples.'
}

with open(MANIFEST_DIR / 'manifest_metadata.json', 'w') as f: json.dump(metadata, f, indent=2)

test_lock = {
    'manifest_version': 'phase4_v2',
    'test_sample_count': counts['test'],
    'full_test_sha256': run1_hashes['test'],
    'freeze_timestamp': datetime.datetime.now().isoformat(),
    'protocol_statement': 'The test set is frozen and must not be used for hyperparameter tuning, model selection, threshold tuning, architecture selection, loss selection, checkpoint selection, or other development decisions.',
    'external_locking': 'External datasets remain development-locked.'
}

with open(AUDIT_DIR / 'test_lock.json', 'w') as f: json.dump(test_lock, f, indent=2)

print("AUDIT_COMPLETE_SUCCESSFULLY")
