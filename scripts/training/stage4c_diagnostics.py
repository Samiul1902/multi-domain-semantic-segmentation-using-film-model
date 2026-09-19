import sys
from pathlib import Path
import torch
from torch.utils.data import DataLoader
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data.kub_localizer_dataset import KUBLocalizerDataset
from src.losses.localization import SoftFocalDiceLoss, CenterNetFocalLoss
from src.models.factory import create_model

def validate_targets():
    print("--- TARGET VALIDATION ---")
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3)
    loader = DataLoader(train_ds, batch_size=4, shuffle=False, num_workers=0)
    
    total_images = 0
    total_comps = 0
    zero_pos_images = 0
    pos_centers = []
    all_exact_1 = True
    
    for batch in loader:
        heatmaps = batch['heatmap']
        for i in range(len(heatmaps)):
            hm = heatmaps[i].numpy()
            total_images += 1
            # Check exactly 1.0
            pos_mask = (hm == 1.0)
            n_pos = pos_mask.sum()
            pos_centers.append(n_pos)
            
            if hm.max() > 0 and hm.max() < 1.0:
                print(f"WARNING: Image {batch['sample_id'][i]} has max {hm.max()} != 1.0")
                all_exact_1 = False
            if hm.max() > 1.0 or hm.min() < 0.0:
                print(f"WARNING: Image {batch['sample_id'][i]} out of [0, 1] range: min {hm.min()} max {hm.max()}")
                all_exact_1 = False
            
            if n_pos == 0 and hm.max() > 0:
                print(f"WARNING: Image {batch['sample_id'][i]} has positive pixels but no exactly 1.0 center")
                all_exact_1 = False
                
            if hm.max() == 0:
                zero_pos_images += 1
            else:
                total_comps += n_pos

    print(f"TRAIN images: {total_images}")
    print(f"TRAIN components: {total_comps}")
    print(f"mean positive centers/image: {np.mean(pos_centers):.4f}")
    print(f"max positive centers/image: {np.max(pos_centers)}")
    print(f"number images with zero positive centers: {zero_pos_images}")
    print(f"target peaks exactly 1: {all_exact_1}")
    
    if not all_exact_1:
        print("CHECK_REQUIRED and STOP.")
        sys.exit(1)

def check_gradients():
    print("\n--- GRADIENT DIAGNOSTIC ---")
    train_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3)
    loader = DataLoader(train_ds, batch_size=4, shuffle=False, num_workers=0)
    batch = next(iter(loader))
    
    device = torch.device('cuda')
    img = batch['image'].to(device)
    target = batch['heatmap'].to(device)
    
    # Old Loss
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    model.train()
    torch.manual_seed(42)
    logits = model(img)
    logits.retain_grad()
    
    old_loss_fn = SoftFocalDiceLoss()
    loss_old = old_loss_fn(logits, target)
    loss_old.backward()
    
    old_grad_norm = sum(p.grad.norm().item() for p in model.parameters() if p.grad is not None)
    old_head_grad_norm = logits.grad.norm().item()
    old_finite = torch.isfinite(loss_old).item() and np.isfinite(old_grad_norm)
    
    # New Loss
    model.zero_grad(set_to_none=True)
    logits = model(img)
    logits.retain_grad()
    
    new_loss_fn = CenterNetFocalLoss()
    loss_new = new_loss_fn(logits, target)
    loss_new.backward()
    
    new_grad_norm = sum(p.grad.norm().item() for p in model.parameters() if p.grad is not None)
    new_head_grad_norm = logits.grad.norm().item()
    new_finite = torch.isfinite(loss_new).item() and np.isfinite(new_grad_norm)
    
    # Contribution split
    with torch.no_grad():
        p = torch.sigmoid(logits)
        p = torch.clamp(p, min=1e-6, max=1.0 - 1e-6)
        pos_inds = target.eq(1.0)
        neg_inds = target.lt(1.0)
        
        pos_loss = -torch.pow(1.0 - p, 2.0) * torch.log(p)
        neg_loss = -torch.pow(1.0 - target, 4.0) * torch.pow(p, 2.0) * torch.log(1.0 - p)
        
        pos_sum = pos_loss[pos_inds].sum().item()
        neg_sum = neg_loss[neg_inds].sum().item()
    
    print(f"Old Loss value: {loss_old.item():.4f}")
    print(f"Old Loss gradient finite: {old_finite}")
    print(f"Old Loss gradient norm: {old_grad_norm:.4f}")
    print(f"Old Loss output-head grad norm: {old_head_grad_norm:.4f}")
    
    print(f"\nNew Loss value: {loss_new.item():.4f}")
    print(f"New Loss gradient finite: {new_finite}")
    print(f"New Loss gradient norm: {new_grad_norm:.4f}")
    print(f"New Loss output-head grad norm: {new_head_grad_norm:.4f}")
    print(f"New Loss positive-center contribution: {pos_sum:.4f}")
    print(f"New Loss negative contribution: {neg_sum:.4f}")

if __name__ == "__main__":
    check_gradients()
    validate_targets()
