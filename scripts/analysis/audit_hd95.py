import pandas as pd
import numpy as np
import pathlib
import sys

ROOT = pathlib.Path(r'D:\Softfors\jup')
sys.path.insert(0, str(ROOT))

from PIL import Image
from scipy.ndimage import binary_erosion, distance_transform_edt

from src.data.transforms import SegmentationTransform
from src.metrics.segmentation import hd95

t = ROOT / 'reports' / 'tables'

p12 = pd.read_csv(t / 'phase12_oracle_roi_per_image.csv')
samples = pd.read_csv(t / 'kub_val_samples_sized.csv')
samples = samples[samples['view_type'] == 'FULL_FIELD'].set_index('sample_id')

transform = SegmentationTransform(512, train=False)
cache_dir = ROOT / 'data_cache' / 'phase12_oracle_roi'

# Compute 512x512 space HD95 for all margins so summary is perfectly consistent
margins = [10, 25, 50]
for m in margins:
    hlist, vlist, elist = [], [], []
    for _, row in p12.iterrows():
        sid = row['sample_id']
        srow = samples.loc[sid]
        img_pil = Image.open(srow['image_path'])
        mask_pil = Image.open(srow['mask_path'])
        _, gt_512, _ = transform(img_pil, mask_pil)
        gt_arr = (gt_512.squeeze().numpy() > 0)
        
        mask_orig = np.load(cache_dir / sid / f'mask_margin{m}.npy').astype(bool)
        mask_pil_small = Image.fromarray(mask_orig.astype(np.uint8) * 255).resize((512, 512), Image.Resampling.NEAREST)
        mask_512 = np.asarray(mask_pil_small) > 0
        
        res = hd95(mask_512, gt_arr)
        hlist.append(res['hd95'])
        vlist.append(res['hd95_valid'])
        elist.append(res['empty_prediction'])
    
    # Overwrite the original columns so everything downstream uses 512x512 space consistently
    p12[f'oracle{m}_hd95'] = hlist
    p12[f'oracle{m}_hd95_valid'] = vlist
    p12[f'oracle{m}_empty_prediction'] = elist

# Drop the temporary 512 tracking columns if they exist
p12 = p12.loc[:, ~p12.columns.str.contains('_512$')]
p12.to_csv(t / 'phase12_oracle_roi_per_image.csv', index=False)
print("Saved corrected HD95 values in 512x512 space for Oracle ROI.")
