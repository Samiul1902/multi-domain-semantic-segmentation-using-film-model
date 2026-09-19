import os
import json
import hashlib
from pathlib import Path
import pandas as pd

MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')
AUDIT_DIR = Path(r'D:\Softfors\jup\reports\audits')
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

df_all = pd.read_csv(MANIFEST_DIR / 'all_paired.csv')

print("all_paired split counts:")
print(df_all['split'].value_counts())

def hash_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(65536): h.update(chunk)
    return h.hexdigest()

df_all['img_hash'] = df_all['image_path'].apply(hash_file)

hash_counts = df_all.groupby('img_hash').size()
dup_hashes = hash_counts[hash_counts > 1].index

print(f"Total duplicate image hashes globally: {len(dup_hashes)}")

candidates = []
for h in dup_hashes:
    sub = df_all[df_all['img_hash'] == h]
    splits = sub['split'].unique()
    print(f"Hash {h[:10]} appears in splits: {splits}, datasets: {sub['dataset'].unique()}")
    rows = sub.to_dict('records')
    for i in range(len(rows)):
        for j in range(i + 1, len(rows)):
            r1, r2 = rows[i], rows[j]
            candidates.append({
                'sample_id_a': r1['sample_id'],
                'sample_id_b': r2['sample_id'],
                'dataset_a': r1['dataset'],
                'dataset_b': r2['dataset'],
                'patient_id_a': r1['patient_id'],
                'patient_id_b': r2['patient_id'],
                'split_a': r1['split'],
                'split_b': r2['split'],
                'image_path_a': r1['image_path'],
                'image_path_b': r2['image_path'],
                'hash': h,
                'is_cross_split': (r1['split'] != r2['split']),
                'classification': 'exact_image_content_duplicate'
            })

cand_df = pd.DataFrame(candidates)
cand_df.to_csv(AUDIT_DIR / 'exact_image_duplicate_candidates.csv', index=False)
print(f"Saved {len(cand_df)} image content duplicate pairs to exact_image_duplicate_candidates.csv.")
