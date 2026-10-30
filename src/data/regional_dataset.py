import torch
import numpy as np
from PIL import Image, ImageOps, ImageEnhance
from torch.utils.data import Dataset
import pandas as pd
from pathlib import Path
from scipy.ndimage import label
import random
import sys

from src.inference.predicted_roi import apply_context_margin

# --- Phase-14 clean-v3 ROI margin role constants -------------------------------
# These constants exist so that no ambiguous bare scalar can conflate the
# distinct margin roles resolved in:
#   reports/audits/phase14_roi_margin_role_resolution.json
#
# ORACLE_DERIVED_REFINER_MARGIN governs CROP CONSTRUCTION for refiner TRAIN and
# crop-level VAL crops derived from ground-truth (oracle) component ROIs.
# It is deliberately NOT shared with the predicted-proposal margin (0.20), which
# is frozen by the Phase-13B clean-v3 proposal contract and applied downstream.
ORACLE_DERIVED_REFINER_MARGIN = 0.25
PREDICTED_PROPOSAL_MARGIN = 0.20


class TestAccessError(RuntimeError):
    pass

def crop_and_preprocess(raw_image: Image.Image, raw_mask: Image.Image, crop_geom: dict, target_size=256):
    """Crop raw image and mask, pad to square, and resize to target_size."""
    img_arr = np.asarray(raw_image.convert('L'))
    mask_arr = np.asarray(raw_mask.convert('L')) > 0
    
    c_y1, c_y2 = crop_geom['clip_y1'], crop_geom['clip_y2']
    c_x1, c_x2 = crop_geom['clip_x1'], crop_geom['clip_x2']
    
    valid_img = img_arr[c_y1:c_y2, c_x1:c_x2]
    valid_mask = mask_arr[c_y1:c_y2, c_x1:c_x2].astype(np.uint8) * 255
    
    padded_img = np.pad(
        valid_img,
        ((crop_geom['pad_top'], crop_geom['pad_bottom']), (crop_geom['pad_left'], crop_geom['pad_right'])),
        mode='constant', constant_values=0
    )
    padded_mask = np.pad(
        valid_mask,
        ((crop_geom['pad_top'], crop_geom['pad_bottom']), (crop_geom['pad_left'], crop_geom['pad_right'])),
        mode='constant', constant_values=0
    )
    
    img_pil = Image.fromarray(padded_img)
    mask_pil = Image.fromarray(padded_mask)
    
    # Image resize bilinear, Mask resize nearest
    img_resized = img_pil.resize((target_size, target_size), Image.Resampling.BILINEAR)
    mask_resized = mask_pil.resize((target_size, target_size), Image.Resampling.NEAREST)
    
    return img_resized, mask_resized


class RegionalCropDataset(Dataset):
    def __init__(self, manifest_path, split, target_size=256, margin=ORACLE_DERIVED_REFINER_MARGIN, seed=42):
        self.split = split.upper()
        if self.split == 'TEST':
            raise TestAccessError('TEST is frozen')
        if self.split not in {'TRAIN', 'VAL'}:
            raise ValueError('split must be TRAIN or VAL')
            
        self.target_size = target_size
        self.margin = margin
        self.seed = seed
        self.rng = random.Random(seed)
        
        df = pd.read_csv(manifest_path)
        self.manifest = df[(df['dataset'] == 'KUB') & (df['split'].str.upper() == self.split)].copy().reset_index(drop=True)
        
        # Load View Type from inventory (resolve from project root via __file__)
        proj_root = Path(__file__).resolve().parent.parent.parent
        vt_df = pd.read_csv(proj_root / 'reports/tables/kub_view_type_inventory.csv')
        self.manifest = pd.merge(self.manifest, vt_df[['sample_id', 'view_type']], on='sample_id', how='left')
        self.manifest = self.manifest[self.manifest['view_type'] == 'FULL_FIELD'].copy().reset_index(drop=True)
        
        self.samples = []
        for idx, row in self.manifest.iterrows():
            mask_path = Path(row['image_path'].replace('Images', 'Masks').replace('.png', '_mask.png'))
            if not mask_path.exists():
                mask_path = Path(row['image_path'].replace('Images', 'Masks'))
            if not mask_path.exists(): continue
            
            mask = np.array(Image.open(mask_path).convert('L')) > 0
            h, w = mask.shape
            labeled, count = label(mask, structure=np.ones((3,3), dtype=int))
            components = []
            for cid in range(1, count + 1):
                ys, xs = np.where(labeled == cid)
                components.append({
                    'component_id': cid,
                    'min_y': int(ys.min()), 'max_y': int(ys.max()),
                    'min_x': int(xs.min()), 'max_x': int(xs.max())
                })
            self.samples.append({
                'row': row,
                'mask_path': mask_path,
                'image_path': Path(row['image_path']),
                'shape': (h, w),
                'components': components
            })
            
        # Build A3 dataset items
        self.items = []
        for sample in self.samples:
            row = sample['row']
            h, w = sample['shape']
            
            if self.split == 'TRAIN':
                for comp in sample['components']:
                    bbox = (comp['min_y'], comp['min_x'], comp['max_y'], comp['max_x'])
                    geom = apply_context_margin(bbox, (h, w), self.margin)
                    self.items.append({
                        'sample': sample, 'crop_type': 'base_positive', 'crop_geometry': geom, 
                        'trigger_component_id': comp['component_id'], 'augment': True
                    })
                    
                    for _ in range(2): # 2 perturbed positive
                        bh = comp['max_y'] - comp['min_y'] + 1
                        bw = comp['max_x'] - comp['min_x'] + 1
                        side = max(bh, bw) * (1.0 + 2.0 * self.margin)
                        
                        # Apply jitter
                        tx = self.rng.uniform(-0.10, 0.10) * side
                        ty = self.rng.uniform(-0.10, 0.10) * side
                        scale_jitter = self.rng.uniform(0.90, 1.10)
                        
                        new_side = side * scale_jitter
                        new_side = max(new_side, 16.0) # min extent 16
                        
                        center_y = (comp['min_y'] + comp['max_y'])/2.0 + ty
                        center_x = (comp['min_x'] + comp['max_x'])/2.0 + tx
                        
                        y1 = round(center_y - new_side / 2.0)
                        x1 = round(center_x - new_side / 2.0)
                        y2 = y1 + round(new_side)
                        x2 = x1 + round(new_side)
                        
                        pgeom = {
                            'y1': y1, 'y2': y2, 'x1': x1, 'x2': x2,
                            'clip_y1': max(0, y1), 'clip_y2': min(h, y2),
                            'clip_x1': max(0, x1), 'clip_x2': min(w, x2),
                            'pad_top': max(0, -y1), 'pad_bottom': max(0, y2 - h),
                            'pad_left': max(0, -x1), 'pad_right': max(0, x2 - w),
                            'crop_side_pixels': int(new_side),
                            'effective_magnification': 512.0 / new_side,
                            'margin': self.margin
                        }
                        self.items.append({
                            'sample': sample, 'crop_type': 'perturbed_positive', 'crop_geometry': pgeom,
                            'trigger_component_id': comp['component_id'], 'augment': True
                        })
                
                # 2 background negative
                for _ in range(2):
                    valid = False
                    mask_arr = np.array(Image.open(sample['mask_path']).convert('L')) > 0
                    for _retry in range(10):
                        nside = self.rng.uniform(64, 256)
                        cy = self.rng.uniform(nside/2.0, h - nside/2.0)
                        cx = self.rng.uniform(nside/2.0, w - nside/2.0)
                        y1, x1 = round(cy - nside/2.0), round(cx - nside/2.0)
                        y2, x2 = y1 + round(nside), x1 + round(nside)
                        
                        cy1, cy2 = max(0, y1), min(h, y2)
                        cx1, cx2 = max(0, x1), min(w, x2)
                        
                        if mask_arr[cy1:cy2, cx1:cx2].sum() == 0:
                            ngeom = {
                                'y1': y1, 'y2': y2, 'x1': x1, 'x2': x2,
                                'clip_y1': cy1, 'clip_y2': cy2,
                                'clip_x1': cx1, 'clip_x2': cx2,
                                'pad_top': max(0, -y1), 'pad_bottom': max(0, y2 - h),
                                'pad_left': max(0, -x1), 'pad_right': max(0, x2 - w),
                                'crop_side_pixels': int(nside),
                                'effective_magnification': 512.0 / nside,
                                'margin': 0.0
                            }
                            self.items.append({
                                'sample': sample, 'crop_type': 'background_negative', 'crop_geometry': ngeom,
                                'trigger_component_id': -1, 'augment': True
                            })
                            valid = True
                            break
                    if not valid:
                        pass # Skip
            else:
                # VAL -> Top5 oracle crops by area
                comps = sample['components']
                if len(comps) > 5:
                    # Deterministic tie-breaking by max_y if areas are equal
                    comps = sorted(comps, key=lambda c: ((c['max_y']-c['min_y']+1)*(c['max_x']-c['min_x']+1), c['max_y']), reverse=True)[:5]
                for comp in comps:
                    bbox = (comp['min_y'], comp['min_x'], comp['max_y'], comp['max_x'])
                    geom = apply_context_margin(bbox, (h, w), self.margin)
                    self.items.append({
                        'sample': sample, 'crop_type': 'base_positive', 'crop_geometry': geom, 
                        'trigger_component_id': comp['component_id'], 'augment': False
                    })
                    
    def __len__(self):
        return len(self.items)

    def apply_augmentation(self, img_pil, mask_pil):
        # H flip
        if self.rng.random() < 0.5:
            img_pil, mask_pil = ImageOps.mirror(img_pil), ImageOps.mirror(mask_pil)
        # V flip
        if self.rng.random() < 0.5:
            img_pil, mask_pil = ImageOps.flip(img_pil), ImageOps.flip(mask_pil)
        # Rotation +/- 45
        angle = self.rng.uniform(-45.0, 45.0)
        img_pil = img_pil.rotate(angle, resample=Image.Resampling.BILINEAR, fillcolor=0)
        mask_pil = mask_pil.rotate(angle, resample=Image.Resampling.NEAREST, fillcolor=0)
        # Brightness/Contrast +/- 0.2
        img_pil = ImageEnhance.Brightness(img_pil).enhance(self.rng.uniform(0.8, 1.2))
        img_pil = ImageEnhance.Contrast(img_pil).enhance(self.rng.uniform(0.8, 1.2))
        return img_pil, mask_pil

    def __getitem__(self, idx):
        item = self.items[idx]
        sample = item['sample']
        
        raw_img = Image.open(sample['image_path']).convert('L')
        raw_mask = Image.open(sample['mask_path']).convert('L')
        
        img_pil, mask_pil = crop_and_preprocess(raw_img, raw_mask, item['crop_geometry'], self.target_size)
        
        if item['augment']:
            img_pil, mask_pil = self.apply_augmentation(img_pil, mask_pil)
            
        img_t = torch.from_numpy(np.asarray(img_pil, dtype=np.float32).copy()).unsqueeze(0) / 255.0
        mask_t = torch.from_numpy((np.asarray(mask_pil).copy() > 0).astype(np.float32)).unsqueeze(0)
        
        return {
            'image': img_t, 'mask': mask_t,
            'sample_id': sample['row']['sample_id'], 'patient_id': sample['row']['patient_id'],
            'crop_type': item['crop_type'], 'trigger_component_id': item['trigger_component_id'],
            'crop_geometry': item['crop_geometry'], 'contains_foreground': float(mask_t.sum() > 0)
        }

