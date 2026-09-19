import os
import json
import hashlib
import time
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
from scipy.fftpack import dct
from concurrent.futures import ThreadPoolExecutor

MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')
AUDIT_DIR = Path(r'D:\Softfors\jup\reports\audits')
CACHE_PATH = AUDIT_DIR / 'phash_cache.npz'
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

df_all = pd.read_csv(MANIFEST_DIR / 'all_paired.csv')
df_tr = pd.read_csv(MANIFEST_DIR / 'train.csv')
df_va = pd.read_csv(MANIFEST_DIR / 'val.csv')
df_te = pd.read_csv(MANIFEST_DIR / 'test.csv')

expected_hashes = {
    'all_paired.csv': '66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc',
    'train.csv': 'd67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3',
    'val.csv': '46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4',
    'test.csv': '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727'
}

def get_file_sha256(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192): h.update(chunk)
    return h.hexdigest()

current_hashes = {f: get_file_sha256(MANIFEST_DIR / f) for f in expected_hashes}
all_match = all(current_hashes[f] == expected_hashes[f] for f in expected_hashes)
print("Manifest SHA-256 match:", all_match)

def compute_phash_single(path_str):
    try:
        with Image.open(path_str) as img:
            img = img.convert('L').resize((32, 32), Image.Resampling.LANCZOS)
            pixels = np.asarray(img, dtype=np.float32)
            dct_low = dct(dct(pixels, axis=0, norm='ortho'), axis=1, norm='ortho')[:8, :8]
            med = np.median(dct_low)
            return (dct_low > med).flatten()
    except Exception:
        return np.zeros(64, dtype=bool)

if CACHE_PATH.exists():
    print("Loading cached pHashes...")
    data = np.load(CACHE_PATH)
    hashes = data['hashes']
else:
    print("Computing 64-bit pHashes for 8441 images...")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=8) as ex:
        hashes_list = list(ex.map(compute_phash_single, df_all['image_path']))
    hashes = np.array(hashes_list, dtype=bool)
    np.savez_compressed(CACHE_PATH, hashes=hashes)
    print(f"Computed in {time.time()-t0:.2f}s")

packed_hashes = np.packbits(hashes, axis=1).view(np.uint64).flatten()

tr_indices = df_all[df_all['split'] == 'TRAIN'].index.values
va_indices = df_all[df_all['split'] == 'VAL'].index.values
te_indices = df_all[df_all['split'] == 'TEST'].index.values

pairs_to_check = [
    ('TRAIN', 'VAL', tr_indices, va_indices),
    ('TRAIN', 'TEST', tr_indices, te_indices),
    ('VAL', 'TEST', va_indices, te_indices)
]

candidate_records = []
distance_counts = {d: 0 for d in range(7)}

t0 = time.time()
for split_a, split_b, idx_a, idx_b in pairs_to_check:
    print(f"Searching {split_a} vs {split_b}...")
    chunk_size = 500
    for i in range(0, len(idx_a), chunk_size):
        chunk_a = idx_a[i:i+chunk_size]
        h_a = packed_hashes[chunk_a]
        h_b = packed_hashes[idx_b]
        xor_matrix = h_a[:, None] ^ h_b[None, :]
        
        for ca_idx_local, a_global_idx in enumerate(chunk_a):
            xor_row = xor_matrix[ca_idx_local]
            dists = np.array([bin(int(x)).count('1') for x in xor_row])
            valid_indices = np.where(dists <= 6)[0]
            for zb_local_idx in valid_indices:
                dist = int(dists[zb_local_idx])
                b_global_idx = idx_b[zb_local_idx]
                row_a = df_all.iloc[a_global_idx]
                row_b = df_all.iloc[b_global_idx]
                
                if row_a['dataset'] == row_b['dataset']:
                    distance_counts[dist] += 1
                    cls = 'EXACT_DUPLICATE' if dist == 0 else ('LIKELY_NEAR_DUPLICATE' if dist <= 2 else ('POSSIBLE_NEAR_DUPLICATE' if dist <= 4 else 'SIMILAR_BUT_DISTINCT'))
                    candidate_records.append({
                        'sample_id_a': row_a['sample_id'],
                        'sample_id_b': row_b['sample_id'],
                        'dataset_a': row_a['dataset'],
                        'dataset_b': row_b['dataset'],
                        'patient_id_a': row_a['patient_id'],
                        'patient_id_b': row_b['patient_id'],
                        'split_a': row_a['split'],
                        'split_b': row_b['split'],
                        'phash_a': ''.join(hashes[a_global_idx].astype(int).astype(str)),
                        'phash_b': ''.join(hashes[b_global_idx].astype(int).astype(str)),
                        'hamming_distance': dist,
                        'image_path_a': row_a['image_path'],
                        'image_path_b': row_b['image_path'],
                        'exact_sha256_same': False,
                        'classification': cls,
                        'notes': f'Distance {dist} pHash match'
                    })

print(f"Search completed in {time.time()-t0:.2f}s")
print("Distance counts (Cross-split within-dataset):", distance_counts)

cand_df = pd.DataFrame(candidate_records)
if len(cand_df) > 0:
    cand_df.sort_values(by='hamming_distance', inplace=True)
cand_df.to_csv(AUDIT_DIR / 'near_duplicate_candidates.csv', index=False)
print(f"Saved {len(cand_df)} candidates to near_duplicate_candidates.csv")

kub_cand = cand_df[(cand_df['dataset_a'] == 'KUB') & (cand_df['dataset_b'] == 'KUB')] if len(cand_df) > 0 else pd.DataFrame()
same_pat = (kub_cand['patient_id_a'] == kub_cand['patient_id_b']).sum() if len(kub_cand) > 0 else 0
print("KUB Same-patient cross-split candidates:", same_pat)
