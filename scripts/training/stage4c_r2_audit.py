import sys
from pathlib import Path
import pandas as pd
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from scipy.ndimage import label
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.models.factory import create_model
from src.losses.localization import CenterNetFocalLoss
from src.inference.heatmap_targets import get_component_centroids_in_localizer_space
from src.utils.reproducibility import set_seed, make_generator

def run_component_reconciliation():
    print("--- COMPONENT RECONCILIATION ---")
    metadata = pd.read_csv(ROOT / 'reports/tables/kub_train_samples_sized.csv')
    ff = metadata[metadata['view_type'] == 'FULL_FIELD'].reset_index(drop=True)
    
    rows = []
    total_original = 0
    total_heatmap = 0
    total_canonical = 0
    total_collisions = 0
    
    for idx, row in ff.iterrows():
        sid = row['sample_id']
        mask_path = ROOT / row['mask_path']
        mask_orig = np.asarray(Image.open(mask_path).convert('L')) > 0
        labeled_orig, n_orig = label(mask_orig, structure=np.ones((3,3), int))
        
        # authoritative original-space component count
        # heatmap-source component count
        # In KUBLocalizerDataset.__getitem__, components are counted AFTER resize and padding
        # Let's reproduce what the dataset does WITHOUT random augmentations
        # Dataset logic for validation/no aug:
        image = Image.open(ROOT / row['image_path']).convert('L')
        mask = Image.open(mask_path).convert('L')
        width, height = int(row['width']), int(row['height'])
        resolution = 512
        scale = min(resolution / width, resolution / height)
        rw, rh = max(1, round(width*scale)), max(1, round(height*scale))
        image = image.resize((rw, rh), Image.Resampling.BILINEAR)
        mask = mask.resize((rw, rh), Image.Resampling.NEAREST)
        left, top = (resolution-rw)//2, (resolution-rh)//2
        right, bottom = resolution-rw-left, resolution-rh-top
        mask = ImageOps.expand(mask, (left, top, right, bottom))
        mask_array = np.asarray(mask) > 0
        labeled_resize, n_resize = label(mask_array, np.ones((3,3), int))
        
        # canonical centers via coordinate mapping
        centroids_mapped = get_component_centroids_in_localizer_space(
            mask_path, scale, rh, rw, left, top
        )
        n_mapped = len(centroids_mapped)
        
        canonical_centers = set()
        for cy, cx in centroids_mapped:
            icy = max(0, min(511, int(round(cy))))
            icx = max(0, min(511, int(round(cx))))
            canonical_centers.add((icy, icx))
        
        n_canonical = len(canonical_centers)
        collisions = n_mapped - n_canonical
        
        total_original += n_orig
        total_heatmap += n_resize
        total_canonical += n_canonical
        total_collisions += collisions
        
        if n_orig != n_resize or collisions > 0:
            rows.append({
                'sample_id': sid,
                'original_count': n_orig,
                'heatmap_source_count': n_resize,
                'canonical_count': n_canonical,
                'collisions': collisions,
                'missing_components': n_orig - n_resize
            })
            
    print(f"Total Original (Phase 7 authoritative): {total_original}")
    print(f"Total Heatmap-Source (after resize): {total_heatmap}")
    print(f"Total Canonical (unique integer centers): {total_canonical}")
    print(f"Total Collisions: {total_collisions}")
    
    if len(rows) > 0:
        df = pd.DataFrame(rows)
        out_dir = ROOT / 'reports/tables'
        out_dir.mkdir(parents=True, exist_ok=True)
        df.to_csv(out_dir / 'phase13b_stage4c_component_reconciliation.csv', index=False)
        print("Discrepancies found in images:")
        print(df)
    else:
        print("No discrepancies found.")
        
    return total_original, total_heatmap, total_collisions

def run_loss_diagnostic():
    print("\n--- LOSS DECOMPOSITION & INITIALIZATION DIAGNOSTIC ---")
    set_seed(42, True)
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3, cache_in_memory=False)
    loader = DataLoader(train_ds, batch_size=4, shuffle=False, num_workers=0, generator=make_generator(42))
    batch = next(iter(loader))
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    image = batch['image'].to(device)
    target = batch['heatmap'].to(device)
    
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    criterion = CenterNetFocalLoss(alpha=2.0, beta=4.0)
    
    # Current initialization
    with torch.no_grad():
        head_weight = model.head.weight.data
        head_bias = model.head.bias.data
        logits = model(image)
        probs = torch.sigmoid(logits.float())
        
        print("CURRENT INITIALIZATION:")
        print(f"Weight initialization (mean, std): {head_weight.mean().item():.6f}, {head_weight.std().item():.6f}")
        print(f"Bias initialization: {head_bias.mean().item():.6f}")
        print(f"Initial logits (min, max, mean, std): {logits.min().item():.4f}, {logits.max().item():.4f}, {logits.mean().item():.4f}, {logits.std().item():.4f}")
        print(f"Initial probabilities (min, max, mean, std): {probs.min().item():.4f}, {probs.max().item():.4f}, {probs.mean().item():.4f}, {probs.std().item():.4f}")
        
    model.zero_grad()
    with torch.amp.autocast('cuda'):
        logits = model(image)
        loss = criterion(logits, target)
    
    loss.backward()
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), float('inf')).item()
    head_grad_norm = torch.nn.utils.clip_grad_norm_(model.head.parameters(), float('inf')).item()
    
    pos_inds = target.eq(1.0)
    neg_inds = target.lt(1.0)
    
    p = torch.sigmoid(logits.float())
    p = torch.clamp(p, min=1e-6, max=1.0 - 1e-6)
    target_f = target.float()
    
    pos_loss = -torch.pow(1.0 - p, 2.0) * torch.log(p)
    neg_loss = -torch.pow(1.0 - target_f, 4.0) * torch.pow(p, 2.0) * torch.log(1.0 - p)
    
    pos_sum = pos_loss[pos_inds].sum().item()
    neg_sum = neg_loss[neg_inds].sum().item()
    num_pos = pos_inds.float().sum().item()
    num_neg = neg_inds.float().sum().item()
    
    print(f"\nBatch images: {image.shape[0]}")
    print(f"Positive-center pixels: {num_pos}")
    print(f"Negative pixels: {num_neg}")
    print(f"Raw positive sum: {pos_sum:.4f}")
    print(f"Raw negative sum: {neg_sum:.4f}")
    print(f"Normalized positive contribution: {pos_sum / max(1.0, num_pos):.4f}")
    print(f"Normalized negative contribution: {neg_sum / max(1.0, num_pos):.4f}")
    print(f"Final normalized loss: {loss.item():.4f}")
    print(f"Gradient norm: {grad_norm:.4f}")
    print(f"Output-head gradient: {head_grad_norm:.4f}")
    
    # Temporary p=0.1 bias diagnostic
    print("\nTEMPORARY p=0.1 BIAS DIAGNOSTIC:")
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    import math
    bias_val = math.log(0.1 / 0.9)
    nn.init.constant_(model.head.bias, bias_val)
    
    with torch.no_grad():
        logits_temp = model(image)
        probs_temp = torch.sigmoid(logits_temp.float())
        print(f"Bias: {bias_val:.6f}")
        print(f"Initial probability mean: {probs_temp.mean().item():.6f}")
        
    model.zero_grad()
    with torch.amp.autocast('cuda'):
        logits_temp = model(image)
        loss_temp = criterion(logits_temp, target)
        
    loss_temp.backward()
    grad_norm_temp = torch.nn.utils.clip_grad_norm_(model.parameters(), float('inf')).item()
    head_grad_norm_temp = torch.nn.utils.clip_grad_norm_(model.head.parameters(), float('inf')).item()
    
    p_temp = torch.sigmoid(logits_temp.float())
    p_temp = torch.clamp(p_temp, min=1e-6, max=1.0 - 1e-6)
    pos_loss_temp = -torch.pow(1.0 - p_temp, 2.0) * torch.log(p_temp)
    neg_loss_temp = -torch.pow(1.0 - target_f, 4.0) * torch.pow(p_temp, 2.0) * torch.log(1.0 - p_temp)
    
    pos_sum_temp = pos_loss_temp[pos_inds].sum().item()
    neg_sum_temp = neg_loss_temp[neg_inds].sum().item()
    
    print(f"Normalized positive contribution: {pos_sum_temp / max(1.0, num_pos):.4f}")
    print(f"Normalized negative contribution: {neg_sum_temp / max(1.0, num_pos):.4f}")
    print(f"Final normalized loss: {loss_temp.item():.4f}")
    print(f"Gradient norm: {grad_norm_temp:.4f}")
    print(f"Output-head gradient: {head_grad_norm_temp:.4f}")

if __name__ == '__main__':
    from PIL import ImageOps
    run_component_reconciliation()
    run_loss_diagnostic()
