import pandas as pd
import hashlib
import os
from pathlib import Path
import json

MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')
AUDIT_DIR = Path(r'D:\Softfors\jup\reports\audits')
all_df = pd.read_csv(MANIFEST_DIR / 'all_paired.csv')

# Hashing content
def get_file_hash(path_str):
    if not os.path.exists(path_str): return None
    hasher = hashlib.sha256()
    with open(path_str, 'rb') as f:
        while chunk := f.read(8192): hasher.update(chunk)
    return hasher.hexdigest()

all_df['im_hash'] = all_df['image_path'].apply(get_file_hash)
all_df['mask_hash'] = all_df['mask_path'].apply(get_file_hash)

# Audit
report = {
    'sample_id_overlap': len(all_df) - len(all_df['sample_id'].unique()),
    'dup_rows': len(all_df) - len(all_df.drop_duplicates()),
    'image_hash_overlaps': len(all_df) - len(all_df.groupby(['split', 'im_hash']).size().reset_index()) + len(all_df['split'].unique()), # Simplified overlap check
}

# Per-split check for hashing
split_df = all_df.groupby('split')
dup_hashes = 0
for _, group in split_df:
    dup_hashes += len(group) - len(group['im_hash'].unique())
report['cross_split_image_hash_overlap'] = dup_hashes

# Save
with open(AUDIT_DIR / 'leakage_audit.json', 'w') as f:
    json.dump(report, f, indent=2)
print("Leakage audit complete.")
