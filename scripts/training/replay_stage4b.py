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
from scripts.training.train_phase13b_localizer import evaluate

device = torch.device('cuda')
val_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_val_samples_sized.csv', 'VAL', 512, 3)
loader = DataLoader(val_ds, batch_size=4, shuffle=False)

def analyze_feasibility(path):
    print(f"\n--- Replaying {path.name} ---")
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    state = load_training_checkpoint(path, model, torch.optim.AdamW(model.parameters()), torch.optim.lr_scheduler.CosineAnnealingLR(torch.optim.AdamW(model.parameters()), 100), torch.amp.GradScaler('cuda', enabled=False), True, device)
    
    phase13_components = pd.read_csv(ROOT / 'reports/tables/phase13_predicted_roi_per_component.csv')
    phase13_images = pd.read_csv(ROOT / 'reports/tables/phase13_predicted_roi_per_image.csv')
    hard_keys = set(zip(phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].sample_id, phase13_components[(phase13_components.kub_size_v1=='TINY')&~phase13_components.global_detected].component_id))
    empty_ids = set(phase13_images[phase13_images.global_empty_prediction].sample_id)
    component_table = phase13_components[['sample_id','component_id','min_y','max_y','min_x','max_x','kub_size_v1','global_detected']].copy()
    component_table['hard_tiny'] = [(sid,cid) in hard_keys for sid,cid in zip(component_table.sample_id, component_table.component_id)]
    component_table['global_empty_image'] = component_table.sample_id.isin(empty_ids)

    # Need a dummy criterion for evaluate
    class DummyCriterion(torch.nn.Module):
        def forward(self, logits, target):
            return torch.tensor(0.0, device=logits.device, requires_grad=True)

    val_loss, search, _ = evaluate(model, loader, DummyCriterion(), device, 512, component_table)
    
    feasible = search[search.feasible]
    print(f"Feasible configs out of 20: {len(feasible)}")
    
    if len(feasible) > 0:
        best_cfg = feasible.sort_values(['tiny_recall90','overall_recall90','mean_roi_area_fraction','mean_proposals_per_image','threshold','top_k','margin'],ascending=[False,False,True,True,False,True,True]).iloc[0]
        print("BEST FEASIBLE CONFIG:")
        print(f"Threshold: {best_cfg.threshold}")
        print(f"Margin: {best_cfg.margin}")
        print(f"Top-K: {best_cfg.top_k}")
        print(f"Tiny recall90: {best_cfg.tiny_recall90}")
        print(f"Overall recall90: {best_cfg.overall_recall90}")
        print(f"Hard Tiny /16: {best_cfg.hard_tiny_recovered90}")
        print(f"Global Empty /7: {best_cfg.global_empty_images_covered90}")
        print(f"Mean ROI Area: {best_cfg.mean_roi_area_fraction}")
        print(f"Mean Proposals: {best_cfg.mean_proposals_per_image}")
    else:
        print("NO FEASIBLE CONFIGS.")
        best_infeasible = search.sort_values(['tiny_recall90','overall_recall90','mean_proposals_per_image','mean_roi_area_fraction','threshold','top_k','margin'],ascending=[False,False,True,True,False,True,True]).iloc[0]
        print(f"The old rule would have selected config with area {best_infeasible.mean_roi_area_fraction:.4f} and recall {best_infeasible.tiny_recall90:.4f}, but it is now INFEASIBLE.")

analyze_feasibility(ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v2/best.pt')
analyze_feasibility(ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v2/latest.pt')

