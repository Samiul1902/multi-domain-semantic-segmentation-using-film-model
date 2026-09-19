import os
import json
import hashlib
import time
from pathlib import Path
import pandas as pd
import numpy as np
from PIL import Image
from scipy.fftpack import dct

MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')
AUDIT_DIR = Path(r'D:\Softfors\jup\reports\audits')
CACHE_PATH = AUDIT_DIR / 'phash_cache.npz'
AUDIT_DIR.mkdir(parents=True, exist_ok=True)

df_all = pd.read_csv(MANIFEST_DIR / 'all_paired.csv')

def compute_phash_fast(path_str):
    try:
        with Image.open(path_str) as img:
            img = img.convert('L').resize((32, 32), Image.Resampling.BOX)
            pixels = np.asarray(img, dtype=np.float32)
            dct_low = dct(dct(pixels, axis=0, norm='ortho'), axis=1, norm='ortho')[:8, :8]
            med = np.median(dct_low)
            return (dct_low > med).flatten()
    except Exception:
        return np.zeros(64, dtype=bool)

if CACHE_PATH.exists():
    print("Loading cached pHashes...")
    hashes = np.load(CACHE_PATH)['hashes']
else:
    print(f"Computing pHashes for {len(df_all)} images...")
    t0 = time.time()
    hashes = np.array([compute_phash_fast(p) for p in df_all['image_path']], dtype=bool)
    np.savez_compressed(CACHE_PATH, hashes=hashes)
    print(f"Computed in {time.time()-t0:.2f}s")

# Pack hashes to uint64 for fast bitwise XOR
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
                
                # We check within dataset and cross dataset near-duplicates
                if row_a['dataset'] == row_b['dataset']:
                    distance_counts[dist] += 1
                    cls = 'EXACT_DUPLICATE' if dist == 0 and row_a['image_path'] == row_b['image_path'] else ('PERCEPTUALLY_IDENTICAL' if dist == 0 else ('LIKELY_NEAR_DUPLICATE' if dist <= 2 else ('POSSIBLE_NEAR_DUPLICATE' if dist <= 4 else 'SIMILAR_BUT_DISTINCT')))
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
                        'exact_sha256_same': (row_a['image_path'] == row_b['image_path']),
                        'classification': cls,
                        'notes': f'Cross-split distance {dist} pHash match'
                    })

print(f"Cross-split search finished in {time.time()-t0:.2f}s")
print("Cross-split Hamming distance counts (0-6):", distance_counts)

cand_df = pd.DataFrame(candidate_records)
if len(cand_df) > 0:
    cand_df.sort_values(by='hamming_distance', inplace=True)
cand_df.to_csv(AUDIT_DIR / 'near_duplicate_candidates.csv', index=False)
print(f"Saved {len(cand_df)} candidates to near_duplicate_candidates.csv")

kub_cand = cand_df[(cand_df['dataset_a'] == 'KUB') & (cand_df['dataset_b'] == 'KUB')] if len(cand_df) > 0 else pd.DataFrame()
same_pat = (kub_cand['patient_id_a'] == kub_cand['patient_id_b']).sum() if len(kub_cand) > 0 else 0
print("KUB Same-patient cross-split candidates:", same_pat)
