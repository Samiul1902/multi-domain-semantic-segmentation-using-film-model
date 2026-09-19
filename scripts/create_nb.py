import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import json
import codecs
import os
from pathlib import Path

nb = new_notebook()

nb.cells.extend([
    new_markdown_cell("# Phase 14 Regional Refiner Diagnostic - Part 1 Implementation\n**PHASE 14 TRAINING NOT YET EXECUTED**"),
    
    new_markdown_cell("## 1. Phase-14 Diagnostic Rationale\nThis branch investigates three questions:\n1. Upper Bound Capability (Oracle ROI)\n2. Proposal Bottleneck Quantification (Predicted ROI)\n3. Degradation Ratio."),
    
    new_markdown_cell("## 2. Original Confirmatory Gate History\n**UNCHANGED**: The confirmatory Phase-14 entry gate was NOT PASSED. Phase-14 remains closed as COMPLETE_CLOSED_NOT_RUN for the confirmatory path."),
    
    new_markdown_cell("## 3. Frozen Protocol Summary\n- Margin: 0.20\n- TopK: 5\n- Resolution: 256x256\n- Threshold: 0.50\n- Loss: 0.5 BCE + 0.5 SoftDice\n- Optim: AdamW, LR 1e-4\n- Fusion: DIRECT_REPLACEMENT_IN_PROPOSAL_UNION\n- Overlap: MAX\n- Zero-proposal: P_global everywhere."),
    
    new_markdown_cell("## 4. Population\n- KUB FULL_FIELD only\n- TRAIN: 771 images, 1162 components\n- VAL: 106 images, 156 components"),
    
    new_markdown_cell("## 5. A3 Training Dataset Composition\n- Base positives: 1162 (1 per GT component)\n- Perturbed positives: 2324 (2 per component, +/-10% translation/scale)\n- Background negatives: 1542 (2 per image, zero GT)\n- Total epoch examples: 5028\n- Oracle Budget: Top 5 GT components by area for TRAIN images > 5 components."),
    
    new_markdown_cell("## 6. Geometry Rules & Fusion Rule\n- Geometry: margin=0.20 applied exactly once. Predicted proposals use crop_geometry directly.\n- Fusion: P_final(x) = P_regional_union(x) inside union of ROIs, P_global(x) outside. Aggregation uses MAX."),
    
    new_markdown_cell("## 7. Implementation Inventory & Unit Tests\nImplemented src/data/regional_dataset.py, src/inference/regional_evaluator.py, 	ests/test_phase14_part1.py."),
    
    new_code_cell("import sys, os\nsys.path.insert(0, os.path.abspath('..'))\n!pytest ../tests/test_phase14_part1.py -v"),
    
    new_markdown_cell("## 8. CUDA Environment & Batch-8 Smoke Test"),
    new_code_cell("import sys, os, torch\nsys.path.insert(0, os.path.abspath('..'))\nprint('Python:', sys.version.split()[0])\nprint('PyTorch:', torch.__version__)\nprint('CUDA:', torch.version.cuda)\nprint('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')\n\nfrom src.models.unet import UNet\nfrom src.losses.segmentation import BCEDiceLoss\n\nif torch.cuda.is_available():\n    device = torch.device('cuda')\n    model = UNet(in_channels=1, out_channels=1, base_channels=32).to(device)\n    loss_fn = BCEDiceLoss(0.5, 0.5)\n    \n    batch_img = torch.randn(8, 1, 256, 256, device=device)\n    batch_target = torch.ones(8, 1, 256, 256, device=device)\n    \n    torch.cuda.reset_peak_memory_stats()\n    with torch.amp.autocast('cuda'):\n        logits = model(batch_img)\n        loss = loss_fn(logits, batch_target)\n        \n    alloc = torch.cuda.memory_allocated() / (1024**2)\n    res = torch.cuda.memory_reserved() / (1024**2)\n    peak = torch.cuda.max_memory_allocated() / (1024**2)\n    print(f'Allocated VRAM: {alloc:.2f} MB')\n    print(f'Reserved VRAM: {res:.2f} MB')\n    print(f'Peak VRAM: {peak:.2f} MB')\n    print(f'Loss finite: {torch.isfinite(loss).item()}')"),
    
    new_markdown_cell("## 9. Mini Pipeline Preflight"),
    new_code_cell("import sys, os\nsys.path.insert(0, os.path.abspath('..'))\nfrom src.data.regional_dataset import RegionalCropDataset, crop_and_preprocess\nfrom src.inference.regional_evaluator import restore_regional_probability, aggregate_and_fuse\nimport numpy as np\nfrom PIL import Image\n\nval_ds = RegionalCropDataset('../manifests/val.csv', 'VAL')\nitem = val_ds.items[0]\nraw_img = Image.open(str(item['sample']['image_path'])).convert('L')\nraw_mask = Image.open(str(item['sample']['mask_path'])).convert('L')\ngeom = item['crop_geometry']\nimg_256, mask_256 = crop_and_preprocess(raw_img, raw_mask, geom, 256)\nprob_map = np.ones((256, 256), dtype=np.float32) * 0.95\ncanvas, support = restore_regional_probability(prob_map, geom, raw_img.size[::-1])\nglobal_prob = np.zeros(raw_img.size[::-1], dtype=np.float32)\nfused = aggregate_and_fuse(global_prob, [canvas], [support])\nprint('Fusion complete. Foreground pixels:', (fused >= 0.50).sum())\nprint('Mini pipeline succeeded.')"),
    
    new_markdown_cell("## 10. Artifact Provenance\n- Global Checkpoint: phase10_kub_unetpp_seed42_512/best.pt\n- Stage-4D Checkpoint: phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt\n\n**PHASE 14 TRAINING NOT YET EXECUTED**")
])

with open('notebooks/13_phase14_regional_refiner_diagnostic.ipynb', 'w', encoding='utf-8') as f:
    nbf.write(nb, f)
