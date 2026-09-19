import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import os

nb = new_notebook()

nb.cells.extend([
    new_markdown_cell("# Phase 14 Regional Refiner Diagnostic - Part 1B Implementation\n**PHASE 14 TRAINING NOT YET EXECUTED**"),
    
    new_markdown_cell("## 1. Environment Certification"),
    new_code_cell("""import sys, os, torch
from pathlib import Path

# Verify interpreter
assert Path(sys.executable).resolve() == Path(r"D:\Softfors\jup\.venv\Scripts\python.exe").resolve(), "Wrong interpreter!"

print("Python executable:", sys.executable)
print("Python version:", sys.version.split()[0])
print("PyTorch:", torch.__version__)
print("CUDA Available:", torch.cuda.is_available())
print("torch.version.cuda:", torch.version.cuda)
if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
"""),
    
    new_markdown_cell("## 2. Parameter Count Verification\nAuthoritative KUB convention: grayscale (in_channels=1). Provenance: Phase 10 / Stage 4D inputs use grayscale (1-channel)."),
    new_code_cell("""sys.path.insert(0, os.path.abspath('..'))
from src.models.unet import UNet
model = UNet(in_channels=1, out_channels=1, base_channels=32)
params = sum(p.numel() for p in model.parameters() if p.requires_grad)
print("Model: UNet(in_channels=1, out_channels=1, base_channels=32)")
print(f"Trainable Params: {params}")
assert params == 7762465
"""),

    new_markdown_cell("## 3. Pytest Execution"),
    new_code_cell("""import subprocess
result = subprocess.run([sys.executable, "-m", "pytest", "tests/test_phase14_part1.py", "-v"], cwd=os.path.abspath('..'), capture_output=True, text=True)
print(result.stdout)
if result.stderr: print("STDERR:", result.stderr)
assert result.returncode == 0, "Pytest failed!"
"""),

    new_markdown_cell("## 4. CUDA Batch-8 AMP Preflight"),
    new_code_cell("""import torch
from src.losses.segmentation import BCEDiceLoss

device = torch.device('cuda')
model = model.to(device)
loss_fn = BCEDiceLoss(0.5, 0.5)

batch_img = torch.randn(8, 1, 256, 256, device=device)
batch_target = torch.ones(8, 1, 256, 256, device=device)

torch.cuda.reset_peak_memory_stats()
with torch.amp.autocast('cuda'):
    logits = model(batch_img)
    loss = loss_fn(logits, batch_target)

alloc = torch.cuda.memory_allocated() / (1024**2)
res = torch.cuda.memory_reserved() / (1024**2)
peak = torch.cuda.max_memory_allocated() / (1024**2)

print(f'Allocated VRAM: {alloc:.2f} MB')
print(f'Reserved VRAM: {res:.2f} MB')
print(f'Peak VRAM: {peak:.2f} MB')
print(f'Loss finite: {torch.isfinite(loss).item()}')
assert torch.isfinite(loss).item()
"""),

    new_markdown_cell("## 5. Real Oracle Mini-Pipeline"),
    new_code_cell("""from src.data.regional_dataset import RegionalCropDataset, crop_and_preprocess
from src.inference.regional_evaluator import restore_regional_probability, aggregate_and_fuse
import numpy as np
from PIL import Image

val_ds = RegionalCropDataset('../manifests/val.csv', 'VAL')
item = val_ds.items[0]
raw_img = Image.open(str(item['sample']['image_path'])).convert('L')
raw_mask = Image.open(str(item['sample']['mask_path'])).convert('L')
geom = item['crop_geometry']

print(f"Sample ID: {item['sample']['row']['sample_id']}, Split: VAL")
print(f"GT Component Count: {len(item['sample']['components'])}")
print(f"Raw Image Shape: {raw_img.size[::-1]}")
print(f"Oracle Proposal Geometry: {geom}")

img_256, mask_256 = crop_and_preprocess(raw_img, raw_mask, geom, 256)
img_t = torch.from_numpy(np.asarray(img_256, dtype=np.float32).copy()).unsqueeze(0).unsqueeze(0) / 255.0

print(f"Regional crop tensor shape: {img_t.shape}")
with torch.amp.autocast('cuda'), torch.inference_mode():
    logits = model(img_t.to(device))
    prob_map = torch.sigmoid(logits)[0, 0].cpu().numpy()

print(f"Regional model output shape: {prob_map.shape}")
canvas, support = restore_regional_probability(prob_map, geom, raw_img.size[::-1])
print(f"Restored probability shape: {canvas.shape}, Support pixels: {support.sum()}")

global_prob = np.zeros(raw_img.size[::-1], dtype=np.float32)
fused = aggregate_and_fuse(global_prob, [canvas], [support])
print(f"Fused probability shape: {fused.shape}")
final_mask = (fused >= 0.50).astype(np.uint8)
print(f"Final binary mask shape: {final_mask.shape}")
"""),

    new_markdown_cell("## 6. Real Frozen Stage-4D Predicted Mini-Pipeline\nUsing checkpoint: phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt\nGlobal Baseline Checkpoint: phase10_kub_unetpp_seed42_512/best.pt"),
    new_code_cell("""from src.inference.learned_roi import predict_localizer
from src.inference.kub_predict import predict_kub

image_path = str(item['sample']['image_path'])
stage4d_ckpt = '../checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt'
global_ckpt = '../checkpoints/phase10_kub_unetpp_seed42_512/best.pt'

print("Generating proposals deterministically from Stage-4D checkpoint...")
localizer_res = predict_localizer(image_path, stage4d_ckpt, 512, 0.10, 0.20, 5, 0.30)
proposals = localizer_res['proposals']

print(f"Sample ID: {item['sample']['row']['sample_id']}, Split: VAL")
print(f"Real Predicted Proposal Count: {len(proposals)}")
print(f"Raw Image Shape: {raw_img.size[::-1]}")

regional_canvases, regional_supports = [], []
for prop in proposals:
    geom = prop['crop_geometry']
    print(f"Predicted Crop Geometry: {geom}")
    img_256, _ = crop_and_preprocess(raw_img, raw_mask, geom, 256)
    img_t = torch.from_numpy(np.asarray(img_256, dtype=np.float32).copy()).unsqueeze(0).unsqueeze(0) / 255.0
    with torch.amp.autocast('cuda'), torch.inference_mode():
        logits = model(img_t.to(device))
        prob_map = torch.sigmoid(logits)[0, 0].cpu().numpy()
    canvas, support = restore_regional_probability(prob_map, geom, raw_img.size[::-1])
    regional_canvases.append(canvas)
    regional_supports.append(support)
    print(f"  Crop tensor shape: {img_t.shape}, Support pixels: {support.sum()}")

print("Generating global baseline probability deterministically...")
global_res = predict_kub(image_path, checkpoint_path=global_ckpt, return_original_space=True)
global_prob = global_res['probability_original']

fused = aggregate_and_fuse(global_prob, regional_canvases, regional_supports)
print(f"Final fused shape: {fused.shape}")
print("Real predicted pipeline succeeded.")
""")
])

with open('notebooks/13_phase14_regional_refiner_diagnostic.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
