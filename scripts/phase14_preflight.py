import sys
import torch
import numpy as np
from PIL import Image
from pathlib import Path

from src.data.regional_dataset import RegionalCropDataset, crop_and_preprocess
from src.inference.regional_evaluator import restore_regional_probability, aggregate_and_fuse
from src.models.unet import UNet
from src.losses.segmentation import BCEDiceLoss

def run_cuda_preflight():
    print("--- CUDA PREFLIGHT ---")
    print("Python:", sys.version.split()[0])
    print("PyTorch:", torch.__version__)
    print("CUDA version (torch):", torch.version.cuda)
    is_cuda = torch.cuda.is_available()
    print("CUDA available:", is_cuda)
    if is_cuda:
        print("GPU Name:", torch.cuda.get_device_name(0))
    else:
        print("GPU Name: N/A")
        
    print("\n--- BATCH 8 MEMORY SMOKE TEST ---")
    if not is_cuda:
        print("Skipping CUDA memory test because CUDA is not available.")
        return
        
    device = torch.device('cuda')
    model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)
    loss_fn = BCEDiceLoss(0.5, 0.5)
    
    # 8 random crops 256x256
    batch_img = torch.randn(8, 1, 256, 256, device=device)
    batch_target = torch.ones(8, 1, 256, 256, device=device)
    
    torch.cuda.reset_peak_memory_stats()
    
    with torch.amp.autocast('cuda'):
        logits = model(batch_img)
        loss = loss_fn(logits, batch_target)
        
    alloc = torch.cuda.memory_allocated() / (1024**2)
    res = torch.cuda.memory_reserved() / (1024**2)
    peak = torch.cuda.max_memory_allocated() / (1024**2)
    
    print(f"Allocated VRAM: {alloc:.2f} MB")
    print(f"Reserved VRAM: {res:.2f} MB")
    print(f"Peak VRAM: {peak:.2f} MB")
    print(f"Loss finite: {torch.isfinite(loss).item()}")
    
def run_mini_pipeline():
    print("\n--- END-TO-END MINI PIPELINE PREFLIGHT ---")
    val_ds = RegionalCropDataset('manifests/val.csv', 'VAL')
    if len(val_ds.items) == 0:
        print("No items to test.")
        return
        
    item = val_ds.items[0]
    sample = item['sample']
    raw_img = Image.open(sample['image_path']).convert('L')
    raw_mask = Image.open(sample['mask_path']).convert('L')
    
    print(f"1. Raw Image loaded: {raw_img.size}")
    
    geom = item['crop_geometry']
    print(f"2. Crop Geometry defined: side={geom['crop_side_pixels']}")
    
    img_256, mask_256 = crop_and_preprocess(raw_img, raw_mask, geom, 256)
    print(f"3. 256 Crop created: {img_256.size}")
    
    # Mock regional forward
    prob_map = np.ones((256, 256), dtype=np.float32) * 0.95
    print("4. Regional Forward probability generated.")
    
    canvas, support = restore_regional_probability(prob_map, geom, raw_img.size[::-1])
    print(f"5. Probability restored to canvas: {canvas.shape}, Support sum={support.sum()}")
    
    global_prob = np.zeros(raw_img.size[::-1], dtype=np.float32)
    fused = aggregate_and_fuse(global_prob, [canvas], [support])
    print(f"6. Fusion complete. Fused max: {fused.max()}")
    
    final_mask = (fused >= 0.50).astype(np.uint8)
    print(f"7. Final Thresholded mask generated. Foreground pixels: {final_mask.sum()}")
    print("Mini pipeline succeeded.")

if __name__ == '__main__':
    run_cuda_preflight()
    run_mini_pipeline()

