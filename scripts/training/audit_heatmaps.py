import torch
import numpy as np
import sys
from pathlib import Path
import pandas as pd
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from src.models.factory import create_model
from src.utils.checkpointing import load_training_checkpoint
from src.data.kub_localizer_dataset import KUBLocalizerDataset
from torch.utils.data import DataLoader

device = torch.device('cuda')
val_ds = KUBLocalizerDataset(ROOT / 'reports/tables/kub_val_samples_sized.csv', 'VAL', 512, 3)
loader = DataLoader(val_ds, batch_size=4, shuffle=False)

def analyze_checkpoint(path):
    print(f"--- Analyzing {path.name} ---")
    model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
    # fake optimizer for load
    opt = torch.optim.AdamW(model.parameters())
    sch = torch.optim.lr_scheduler.CosineAnnealingLR(opt, 100)
    sc = torch.amp.GradScaler('cuda')
    state = load_training_checkpoint(path, model, opt, sch, sc, True, device)
    print(f"Epoch loaded: {state['epoch']}")
    
    model.eval()
    all_probs = []
    with torch.inference_mode():
        for batch in loader:
            img = batch['image'].to(device)
            logits = model(img)
            probs = torch.sigmoid(logits).float().cpu().numpy()
            all_probs.append(probs)
    
    all_probs = np.concatenate(all_probs, axis=0) # (106, 1, 512, 512)
    
    print(f"Min: {all_probs.min():.4f}")
    print(f"Max: {all_probs.max():.4f}")
    print(f"Mean: {all_probs.mean():.4f}")
    print(f"Std: {all_probs.std():.4f}")
    
    for t in [0.1]:
        fg_fraction = (all_probs >= t).mean()
        print(f"Foreground fraction at {t}: {fg_fraction:.4f}")

analyze_checkpoint(ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v2/best.pt')
analyze_checkpoint(ROOT / 'checkpoints/phase13b_kub_localizer_r512_s3_seed42_v2/latest.pt')

