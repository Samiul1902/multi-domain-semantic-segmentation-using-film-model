import sys
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from scipy.ndimage import label
from torch.utils.data import DataLoader
import math

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.models.factory import create_model
from src.losses.localization import CenterNetFocalLoss
from src.utils.reproducibility import set_seed, make_generator

def run_component_identity_audit():
    print("--- COMPONENT IDENTITY AUDIT ---")
    metadata = pd.read_csv(ROOT / 'reports/tables/kub_train_samples_sized.csv')
    ff = metadata[metadata['view_type'] == 'FULL_FIELD'].reset_index(drop=True)
    
    rows = []
    total_original = 0
    total_mapped = 0
    total_outside = 0
    zero_center_samples = 0
    
    # We will simulate the dataset WITHOUT random augmentation
    for idx, row in ff.iterrows():
        sid = row['sample_id']
        mask_path = ROOT / row['mask_path']
        mask_orig = np.asarray(Image.open(mask_path).convert('L')) > 0
        labeled_orig, n_orig = label(mask_orig, structure=np.ones((3,3), int))
        
        width, height = int(row['width']), int(row['height'])
        resolution = 512
        scale = min(resolution / width, resolution / height)
        rw, rh = max(1, round(width*scale)), max(1, round(height*scale))
        left, top = (resolution-rw)//2, (resolution-rh)//2
        
        canonical_centers = set()
        img_collisions = 0
        
        for cid in range(1, n_orig+1):
            ys, xs = np.where(labeled_orig == cid)
            orig_area = len(ys)
            cy_orig, cx_orig = float(ys.mean()), float(xs.mean())
            
            # map
            cy = cy_orig * scale + top
            cx = cx_orig * scale + left
            
            icy = max(0, min(511, int(round(cy))))
            icx = max(0, min(511, int(round(cx))))
            
            visible = True
            reason = ""
            collision = False
            if (icy, icx) in canonical_centers:
                collision = True
                img_collisions += 1
            else:
                canonical_centers.add((icy, icx))
            
            rows.append({
                'image_id': sid,
                'original_component_id': cid,
                'original_area': orig_area,
                'original_center_x': cx_orig,
                'original_center_y': cy_orig,
                'mapped_center_x_float': cx,
                'mapped_center_y_float': cy,
                'canonical_x': icx,
                'canonical_y': icy,
                'visible': visible,
                'collision': collision,
                'reason_if_not_visible': reason
            })
            
        total_original += n_orig
        total_mapped += n_orig
        
        if n_orig > 0 and len(canonical_centers) == 0:
            zero_center_samples += 1
            
    df = pd.DataFrame(rows)
    out_dir = ROOT / 'reports/tables'
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / 'phase13b_stage4c_r3_component_mapping.csv', index=False)
    
    unique_canonical = df[~df.collision].shape[0]
    total_collisions = df.collision.sum()
    
    print(f"original authoritative components: {total_original}")
    print(f"components mapped into target space: {total_mapped}")
    print(f"components legitimately outside visible field: {total_outside}")
    print(f"unique canonical center pixels: {unique_canonical}")
    print(f"center collisions: {total_collisions}")
    print(f"zero-center TRAIN samples: {zero_center_samples}")
    
    # 8. VERIFY THE 11 DISCREPANCY IMAGES
    print("\n--- 11 DISCREPANCY IMAGES AUDIT ---")
    discrepancy_df = pd.read_csv(out_dir / 'phase13b_stage4c_component_reconciliation.csv')
    sids = discrepancy_df.sample_id.tolist()
    for sid in sids:
        img_rows = df[df.image_id == sid]
        print(f"Image: {sid} - Original: {len(img_rows)} | Mapped Unique: {img_rows[~img_rows.collision].shape[0]}")

def run_determinism_audit():
    print("\n--- DETERMINISM AUDIT ---")
    set_seed(42, True)
    
    # Test A: No stochastic augmentation
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'VAL', 512, 3, cache_in_memory=False)
    hm1 = train_ds[0]['heatmap']
    hm2 = train_ds[0]['heatmap']
    print(f"Deterministic without augmentation (repeated exact): {torch.equal(hm1, hm2)}")
    
    # Test B: Stochastic augmentation with fixed RNG seed
    set_seed(42, True)
    train_ds_aug = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3, cache_in_memory=False)
    import random
    
    # Run once
    state1 = random.getstate()
    hm_aug1 = train_ds_aug[0]['heatmap']
    
    # Run again from same state
    random.setstate(state1)
    hm_aug2 = train_ds_aug[0]['heatmap']
    
    print(f"Deterministic with fixed augmentation realization: {torch.equal(hm_aug1, hm_aug2)}")

def eval_initialization(model, image, target, criterion):
    logits = model(image)
    probs = torch.sigmoid(logits.float())
    loss = criterion(logits, target)
    
    model.zero_grad()
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), float('inf')).item()
    head_grad_norm = torch.nn.utils.clip_grad_norm_(model.head.parameters(), float('inf')).item()
    
    target_f = target.float()
    pos_inds = target.eq(1.0)
    neg_inds = target.lt(1.0)
    p = torch.clamp(probs, min=1e-6, max=1.0 - 1e-6)
    
    pos_loss = -torch.pow(1.0 - p, 2.0) * torch.log(p)
    neg_loss = -torch.pow(1.0 - target_f, 4.0) * torch.pow(p, 2.0) * torch.log(1.0 - p)
    
    pos_sum = pos_loss[pos_inds].sum().item()
    neg_sum = neg_loss[neg_inds].sum().item()
    num_pos = pos_inds.float().sum().item()
    
    return {
        'logit_mean': logits.mean().item(), 'logit_std': logits.std().item(),
        'logit_min': logits.min().item(), 'logit_max': logits.max().item(),
        'prob_mean': probs.mean().item(), 'prob_std': probs.std().item(),
        'prob_min': probs.min().item(), 'prob_max': probs.max().item(),
        'p10': torch.quantile(probs, 0.10).item(), 'p90': torch.quantile(probs, 0.90).item(),
        'p99': torch.quantile(probs, 0.99).item(), 'median': torch.median(probs).item(),
        'frac_01': (probs >= 0.1).float().mean().item(),
        'frac_02': (probs >= 0.2).float().mean().item(),
        'frac_05': (probs >= 0.5).float().mean().item(),
        'pos_sum': pos_sum, 'neg_sum': neg_sum,
        'loss': loss.item(), 'grad_norm': grad_norm, 'head_grad_norm': head_grad_norm,
        'norm_pos': pos_sum / max(1.0, num_pos), 'norm_neg': neg_sum / max(1.0, num_pos)
    }

def run_initialization_audit():
    print("\n--- INITIALIZATION AUDIT ---")
    set_seed(42, True)
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3, cache_in_memory=False)
    loader = DataLoader(train_ds, batch_size=4, shuffle=False, num_workers=0, generator=make_generator(42))
    batch = next(iter(loader))
    
    device = torch.device('cuda')
    image = batch['image'].to(device)
    target = batch['heatmap'].to(device)
    
    criterion = CenterNetFocalLoss(alpha=2.0, beta=4.0)
    
    # A. Current
    model_a = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    res_a = eval_initialization(model_a, image, target, criterion)
    
    # B. Bias only
    model_b = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    model_b.load_state_dict(model_a.state_dict())
    nn.init.constant_(model_b.head.bias, math.log(0.1 / 0.9))
    res_b = eval_initialization(model_b, image, target, criterion)
    
    # C. Zero Final Weight + Bias
    model_c = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    model_c.load_state_dict(model_a.state_dict())
    nn.init.constant_(model_c.head.weight, 0.0)
    nn.init.constant_(model_c.head.bias, math.log(0.1 / 0.9))
    res_c = eval_initialization(model_c, image, target, criterion)
    
    # Print results
    pd.DataFrame([res_a, res_b, res_c], index=['A', 'B', 'C']).to_csv(ROOT / 'reports/tables/phase13b_stage4c_r3_initialization_diagnostic.csv')
    
    for name, res in zip(['A', 'B', 'C'], [res_a, res_b, res_c]):
        print(f"\nInitialization {name}:")
        for k, v in res.items():
            print(f"  {k}: {v:.6f}")
            
    print("\nRATIOS:")
    print(f"B/A loss: {res_b['loss'] / res_a['loss']:.6f}")
    print(f"B/A grad: {res_b['grad_norm'] / res_a['grad_norm']:.6f}")
    print(f"C/A loss: {res_c['loss'] / res_a['loss']:.6f}")
    print(f"C/A grad: {res_c['grad_norm'] / res_a['grad_norm']:.6f}")
    print(f"C/B loss: {res_c['loss'] / res_b['loss']:.6f}")
    print(f"C/B grad: {res_c['grad_norm'] / res_b['grad_norm']:.6f}")

if __name__ == '__main__':
    run_component_identity_audit()
    run_determinism_audit()
    run_initialization_audit()

