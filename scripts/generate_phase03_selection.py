import pandas as pd
import hashlib
from PIL import Image
import numpy as np
from pathlib import Path

df_train = pd.read_csv('manifests/train.csv')
datasets = ['ISIC', 'BUSI', 'KVASIR', 'KUB']
records = []

for ds in datasets:
    ds_df = df_train[df_train['dataset'] == ds].copy()
    ds_df['hash'] = ds_df['sample_id'].apply(lambda sid: hashlib.sha256(f'phase03_dataset_sample_seed42|{ds}|{sid}'.encode('utf-8')).hexdigest())
    ds_df = ds_df.sort_values('hash').reset_index(drop=True)
    selected = ds_df.iloc[:12].copy()
    for rank, (_, row) in enumerate(selected.iterrows(), 1):
        img_p = row['image_path']
        mask_p = row['mask_path']
        
        with Image.open(img_p) as im:
            iw, ih = im.size
            mode = im.mode
            channels = len(im.getbands())
        with Image.open(mask_p) as m:
            mw, mh = m.size
            m_arr = np.array(m)
            fg_px = int((m_arr > 127).sum())
            fg_frac = fg_px / (mw * mh)
            
        assert (iw, ih) == (mw, mh), f"Geometry mismatch for {row['sample_id']}: {iw}x{ih} vs {mw}x{mh}"
        
        records.append({
            'dataset': ds,
            'sample_rank': rank,
            'sample_id': row['sample_id'],
            'split': row['split'],
            'image_path_or_canonical_reference': row['image_path'].replace('\\', '/'),
            'mask_path_or_canonical_reference': row['mask_path'].replace('\\', '/'),
            'image_width': iw,
            'image_height': ih,
            'channels': channels,
            'image_mode': mode,
            'mask_width': mw,
            'mask_height': mh,
            'foreground_pixels': fg_px,
            'foreground_fraction': round(fg_frac, 6),
            'category': row.get('category', 'N/A')
        })

df_out = pd.DataFrame(records)
print(f"Successfully inspected {len(df_out)} cases with perfect geometry alignment!")
out_p = Path('reports/tables/phase03_train_sample_selection.csv')
out_p.parent.mkdir(parents=True, exist_ok=True)
df_out.to_csv(out_p, index=False)
print(f"Saved {out_p}")

