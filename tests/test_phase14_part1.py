import pytest
import torch
import numpy as np
from PIL import Image
from pathlib import Path
import hashlib
import sys
import os

from src.data.regional_dataset import RegionalCropDataset, crop_and_preprocess
from src.inference.regional_evaluator import restore_regional_probability, aggregate_and_fuse, binarize
from src.models.unet import UNet
from src.losses.segmentation import BCEDiceLoss
from src.inference.predicted_roi import apply_context_margin

def get_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            h.update(chunk)
    return h.hexdigest()

def test_population_counts():
    train_ds = RegionalCropDataset('manifests/train.csv', 'TRAIN')
    val_ds = RegionalCropDataset('manifests/val.csv', 'VAL')
    
    assert len(train_ds.samples) == 771
    assert len(val_ds.samples) == 106
    
    train_comps = sum(len(s['components']) for s in train_ds.samples)
    assert train_comps == 1162
    val_comps = sum(len(s['components']) for s in val_ds.samples)
    assert val_comps == 156

def test_crop_dataset_composition():
    train_ds = RegionalCropDataset('manifests/train.csv', 'TRAIN')
    
    bases = sum(1 for i in train_ds.items if i['crop_type'] == 'base_positive')
    perts = sum(1 for i in train_ds.items if i['crop_type'] == 'perturbed_positive')
    negs = sum(1 for i in train_ds.items if i['crop_type'] == 'background_negative')
    
    assert bases == 1162
    assert perts == 2324
    assert negs == 1542
    assert len(train_ds) == 5028
    
    for item in train_ds.items:
        if item['crop_type'] == 'background_negative':
            sample = item['sample']
            mask_arr = np.array(Image.open(sample['mask_path']).convert('L')) > 0
            geom = item['crop_geometry']
            cy1, cy2 = geom['clip_y1'], geom['clip_y2']
            cx1, cx2 = geom['clip_x1'], geom['clip_x2']
            assert mask_arr[cy1:cy2, cx1:cx2].sum() == 0

def test_invariants():
    train_ds = RegionalCropDataset('manifests/train.csv', 'TRAIN')
    item = train_ds[0]
    mask_uniq = torch.unique(item['mask'])
    assert all(val in [0.0, 1.0] for val in mask_uniq)

def test_geometry_and_resize():
    bbox = (10, 10, 20, 20)
    geom = apply_context_margin(bbox, (100, 100), 0.20)
    assert geom['margin'] == 0.20
    
    val_ds = RegionalCropDataset('manifests/val.csv', 'VAL')
    assert val_ds.margin == 0.20

def test_restoration_and_fusion():
    original_shape = (100, 100)
    prob_map = np.ones((256, 256), dtype=np.float32)
    geom = apply_context_margin((10, 10, 20, 20), original_shape, 0.20)
    
    canvas, support = restore_regional_probability(prob_map, geom, original_shape)
    assert canvas.shape == original_shape
    assert support.sum() > 0
    
    global_prob = np.zeros(original_shape, dtype=np.float32)
    global_prob[5, 5] = 0.9 
    global_prob[15, 15] = 0.9 
    
    fused_zero = aggregate_and_fuse(global_prob, [], [])
    assert np.array_equal(fused_zero, global_prob)
    
    geom2 = apply_context_margin((15, 15, 25, 25), original_shape, 0.20)
    canvas2, support2 = restore_regional_probability(np.ones((256, 256), dtype=np.float32)*0.8, geom2, original_shape)
    
    fused = aggregate_and_fuse(global_prob, [canvas, canvas2], [support, support2])
    
    assert fused[18, 18] == 1.0 
    assert fused[5, 5] == 0.9 

def test_model_and_loss():
    model = UNet(in_channels=1, out_channels=1, base_channels=32)
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    assert params == 7762465
    
    loss_fn = BCEDiceLoss(0.5, 0.5)
    logits = torch.randn(2, 1, 64, 64)
    empty_target = torch.zeros(2, 1, 64, 64)
    pos_target = torch.ones(2, 1, 64, 64)
    
    assert torch.isfinite(loss_fn(logits, empty_target))
    assert torch.isfinite(loss_fn(logits, pos_target))

def test_checkpoint_shas():
    global_pt = 'checkpoints/phase10_kub_unetpp_seed42_512/best.pt'
    assert get_sha256(global_pt) == '4bffcf926227fb11029ead6bcd8e7dd8ed246e0f1678e3efb2ce4297439a3f2d'
    stage4d_pt = 'checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1/best.pt'
    assert get_sha256(stage4d_pt).lower() == 'ece906df6c73f2e93c3f873661490bf3cb1a6b82be2d2d93b58c25bc967cbace'.lower()

def test_explicit_split_isolation():
    train_ds = RegionalCropDataset('manifests/train.csv', 'TRAIN')
    val_ds = RegionalCropDataset('manifests/val.csv', 'VAL')
    
    train_ids = set(s['row']['sample_id'] for s in train_ds.samples)
    val_ids = set(s['row']['sample_id'] for s in val_ds.samples)
    
    assert len(train_ids.intersection(val_ids)) == 0, "Leakage between TRAIN and VAL!"
    
    # Check no TEST access via test reading
    import pandas as pd
    if Path('manifests/test.csv').exists():
        test_df = pd.read_csv('manifests/test.csv')
        test_ids = set(test_df['sample_id'])
        assert len(train_ids.intersection(test_ids)) == 0, "Leakage of TEST into TRAIN!"
