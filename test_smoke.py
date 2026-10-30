import time, torch, numpy as np, pandas as pd, pathlib, sys
ROOT = pathlib.Path(r'D:\Softfors\jup')
sys.path.insert(0, str(ROOT))
from src.models.factory import create_model
from src.losses.localization import SoftFocalDiceLoss
from src.data.kub_localizer_dataset import KUBLocalizerDataset
from torch.utils.data import DataLoader
from src.inference.predicted_roi import extract_predicted_components

print("--- SMOKE TEST ---")
device = torch.device('cuda')
model = create_model('kub_localizer', in_channels=1, out_channels=1, base_channels=16).to(device)
criterion = SoftFocalDiceLoss()
opt = torch.optim.AdamW(model.parameters(), lr=1e-4)
scaler = torch.amp.GradScaler('cuda')

dataset = KUBLocalizerDataset(ROOT/'reports/tables/kub_train_samples_sized.csv', 'TRAIN', 512, 3)
loader = DataLoader(dataset, batch_size=4, num_workers=0)

model.train()
opt.zero_grad()
for i, batch in enumerate(loader):
    if i >= 3: break
    image, target = batch['image'].to(device), batch['heatmap'].to(device)
    with torch.amp.autocast('cuda'):
        logits = model(image)
        loss = criterion(logits, target)
    scaler.scale(loss).backward()
    scaler.step(opt)
    scaler.update()
    opt.zero_grad()
    
    # Sparse loss diagnostic
    prob = torch.sigmoid(logits)
    pos_mask = target > 0.01
    neg_mask = ~pos_mask
    print(f"Step {i}: Loss={loss.item():.4f}, Target min/max/mean={target.min().item():.3f}/{target.max().item():.3f}/{target.mean().item():.5f}, Pos frac={(pos_mask.sum()/pos_mask.numel()).item():.4f}")
    print(f"         Logits min/max/mean={logits.min().item():.3f}/{logits.max().item():.3f}/{logits.mean().item():.3f}")
    print(f"         Probs min/max={prob.min().item():.3f}/{prob.max().item():.3f}")
    
    grad_norm = torch.nn.utils.clip_grad_norm_(model.parameters(), float('inf')).item()
    print(f"         Grad norm={grad_norm:.4f}, finite={np.isfinite(grad_norm)}")

print("--- VALIDATION PROFILING ---")
class DummyMeta:
    scale = 0.166; resized_height = 512; resized_width = 512; padding = (0,0,0,0)
prob = np.random.rand(512, 512).astype(np.float32)
start = time.perf_counter()
comps = extract_predicted_components(prob, 0.10, (3072, 3072), DummyMeta())
print(f"extract_predicted_components random noise th=0.10: {len(comps)} comps in {time.perf_counter()-start:.4f}s")

prob_ones = np.ones((512, 512), dtype=np.float32)
start = time.perf_counter()
comps = extract_predicted_components(prob_ones, 0.10, (3072, 3072), DummyMeta())
print(f"extract_predicted_components all ones th=0.10: {len(comps)} comps in {time.perf_counter()-start:.4f}s")
