import pandas as pd
import numpy as np
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import torch
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.data.kub_localizer_dataset import KUBLocalizerDataset
from torch.utils.data import DataLoader
from src.inference.predicted_roi import extract_predicted_components, non_max_suppression, apply_context_margin, union_roi_area_fraction

device = torch.device('cuda')
val_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_val_samples_sized.csv', 'VAL', 512, 3)
loader = DataLoader(val_ds, batch_size=4, shuffle=False)

def analyze_roi_burden(path, threshold, margin, top_k):
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    state = load_training_checkpoint(path, model, torch.optim.AdamW(model.parameters()), torch.optim.lr_scheduler.CosineAnnealingLR(torch.optim.AdamW(model.parameters()), 100), torch.amp.GradScaler('cuda', enabled=False), True, device)
    
    model.eval()
    areas = []
    props = []
    
    with torch.inference_mode():
        for batch in loader:
            img = batch['image'].to(device)
            logits = model(img)
            probs = torch.sigmoid(logits).float().cpu().numpy()
            for i, sid in enumerate(batch['sample_id']):
                prob = probs[i, 0]
                shape = (int(batch['original_height'][i]), int(batch['original_width'][i]))
                meta = type('Meta', (), {'scale': batch['scale'][i], 'resized_height': batch['resized_height'][i], 'resized_width': batch['resized_width'][i], 'padding': batch['padding'][i]})()
                
                comps = extract_predicted_components(prob, threshold, shape, meta)[:100]
                comps = non_max_suppression(comps, 0.3)[:top_k]
                
                proposals = []
                for rank, comp in enumerate(comps, start=1):
                    proposals.append({
                        "crop_geometry": apply_context_margin(comp["bbox"], shape, margin)
                    })
                
                area, _ = union_roi_area_fraction(proposals, shape)
                areas.append(area)
                props.append(len(proposals))
                
    areas = np.array(areas)
    props = np.array(props)
    
    print(f"--- ROI Burden for {path.name} (t={threshold}, m={margin}, k={top_k}) ---")
    print(f"mean proposals: {props.mean():.4f}")
    print(f"median proposals: {np.median(props):.4f}")
    print(f"zero-proposal: {(props == 0).sum()}")
    print(f"mean area: {areas.mean():.4f}")
    print(f"median area: {np.median(areas):.4f}")
    print(f"P90 area: {np.percentile(areas, 90):.4f}")
    print(f"max area: {areas.max():.4f}")
    print(f">= 0.10: {(areas >= 0.10).sum()}")
    print(f">= 0.25: {(areas >= 0.25).sum()}")
    print(f">= 0.50: {(areas >= 0.50).sum()}")
    print(f">= 0.90: {(areas >= 0.90).sum()}")

analyze_roi_burden(ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v2/best.pt', 0.1, 0.1, 5)
analyze_roi_burden(ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v2/latest.pt', 0.1, 0.2, 5)

