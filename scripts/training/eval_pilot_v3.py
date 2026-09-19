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
from src.inference.predicted_roi import evaluate_roi_coverage

device = torch.device('cuda')
val_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_val_samples_sized.csv', 'VAL', 512, 3)
loader = DataLoader(val_ds, batch_size=4, shuffle=False)

def analyze_best_epoch():
    path = ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v3/best.pt'
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    state = load_training_checkpoint(path, model, torch.optim.AdamW(model.parameters()), torch.optim.lr_scheduler.CosineAnnealingLR(torch.optim.AdamW(model.parameters()), 100), torch.amp.GradScaler('cuda', enabled=False), True, device)
    
    phase13_components = pd.read_csv(ROOT / 'reports/tables/phase13_predicted_roi_per_component.csv')
    phase13_images = pd.read_csv(ROOT / 'reports/tables/phase13_predicted_roi_per_image.csv')
    hard_keys = set(zip(phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].sample_id, phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].component_id))
    empty_ids = set(phase13_images[phase13_images.global_empty_prediction].sample_id)
    phase13_components['hard_tiny'] = [(sid,cid) in hard_keys for sid,cid in zip(phase13_components.sample_id, phase13_components.component_id)]
    phase13_components['global_empty_image'] = phase13_components.sample_id.isin(empty_ids)
    
    from scripts.training.train_phase13b_localizer import gt_components
    
    threshold = 0.2
    margin = 0.1
    top_k = 3
    
    model.eval()
    cover = []
    image_metrics = []
    areas = []
    
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
                        "rank": rank,
                        "score": comp["max_probability"],
                        "mean_probability": comp["mean_probability"],
                        "proposal_component_pixels_512": comp["component_pixels_512"],
                        "proposal_bbox": comp["bbox"],
                        "crop_geometry": apply_context_margin(comp["bbox"], shape, margin)
                    })
                
                metadata = phase13_components[phase13_components.sample_id == sid]
                gt = gt_components(batch['mask_path'][i], metadata)
                out = evaluate_roi_coverage(proposals, gt)
                
                area, _ = union_roi_area_fraction(proposals, shape)
                
                for result, component in zip(out, gt):
                    res = {**result, 'sample_id': sid}
                    for key in ('kub_size_v1',): res[key] = component[key]
                    res['hard_tiny'] = (sid, component['component_id']) in hard_keys
                    res['global_empty_image'] = sid in empty_ids
                    cover.append(res)
                
                image_metrics.append((len(proposals), area))
                areas.append(area)

    frame = pd.DataFrame(cover)
    hard = frame[frame.hard_tiny]
    empty = frame[frame.global_empty_image]
    multi_ids = set(phase13_components.groupby('sample_id').size().loc[lambda values: values > 1].index)
    multi = frame[frame.sample_id.isin(multi_ids)]
    areas = np.array(areas)
    
    print("--- HARD TINY ---")
    print(f"recovered90: {hard.covered90.sum()}")
    print(f"recovered50: {hard.covered50.sum()}")
    print(f"any-overlap: {hard.any_overlap.sum()}")
    
    print("\n--- GLOBAL EMPTY ---")
    print(f"covered90 (images): {empty.groupby('sample_id').covered90.any().sum()}")
    print(f"covered50 (images): {empty.groupby('sample_id').covered50.any().sum()}")
    print(f"any-overlap (images): {empty.groupby('sample_id').any_overlap.any().sum()}")
    
    print("\n--- LOCALIZATION ---")
    for size in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']:
        sz = frame[frame.kub_size_v1 == size]
        if len(sz) > 0:
            print(f"{size} recall90: {sz.covered90.mean():.4f}")
        else:
            print(f"{size} recall90: N/A")
    print(f"overall recall90: {frame.covered90.mean():.4f}")
    print(f"recall50: {frame.covered50.mean():.4f}")
    print(f"any-overlap: {frame.any_overlap.mean():.4f}")
    
    print("\n--- MULTI-COMPONENT ---")
    print(f"images: {len(multi_ids)}")
    print(f"components: {len(multi)}")
    print(f"recall90: {multi.covered90.mean():.4f}")
    
    # all localized, partial, none
    multi_grouped = multi.groupby('sample_id').covered90.mean()
    print(f"all localized: {(multi_grouped == 1.0).sum()}")
    print(f"partial: {((multi_grouped > 0) & (multi_grouped < 1.0)).sum()}")
    print(f"none: {(multi_grouped == 0.0).sum()}")
    
    print("\n--- ROI BURDEN ---")
    print(f"P95 ROI area: {np.percentile(areas, 95):.4f}")
    
    print("\n--- PROPOSALS ---")
    props = np.array([x[0] for x in image_metrics])
    print(f"zero proposal images: {(props == 0).sum()}")
    
    import hashlib
    with open(path, 'rb') as f:
        print(f"SHA-256: {hashlib.sha256(f.read()).hexdigest()}")

analyze_best_epoch()
