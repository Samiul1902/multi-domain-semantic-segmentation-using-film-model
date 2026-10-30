"""
Phase 12 Part 1B — CLEAN-v3 four-model oracle regional inference (READ-ONLY, no training).

Implements the SUPERVISOR-FROZEN protocol in
reports/audits/phase12_clean_v3_oracle_protocol_frozen.json.

May perform inference. MUST NOT: train, instantiate an optimizer, write checkpoints,
modify frozen configs, or touch TEST.

Variants (frozen):
  PRIMARY   ORACLE_FLOAT_GLOBAL_RETAINED   P(x)=R(x) if U(x) else G(x)   FLOAT map-back
  SECONDARY ORACLE_FLOAT_CROP_ONLY         P(x)=R(x) if U(x) else 0      FLOAT map-back
  SENSITIV. ORACLE_LEGACY_UINT8_CROP_ONLY  historical PIL+uint8 map-back, crop-only
Global baseline: GLOBAL_NATIVE (native-space inversion of the EVALUATION_512 prediction).

Author: Gemini 3.8 Flash Medium
Date: 2026-09-21
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
from PIL import Image
from scipy.ndimage import label

PROJECT_ROOT = Path(r'D:\Softfors\jup')
REPORTS = PROJECT_ROOT / 'reports'
TABLES = REPORTS / 'tables'
AUDITS = REPORTS / 'audits'

TARGET = 512
THRESHOLD = 0.5
MARGIN = 0.25
BATCH = 4
STRUCT8 = np.ones((3, 3), dtype=bool)
TAXONOMY = 'kub_size_clean_v3_v1'
MANIFEST = 'phase4_v3'

MODELS = ['unet', 'attention_unet', 'unetpp', 'deeplabv3plus']
DISPLAY = {'unet': 'UNet', 'attention_unet': 'Attention U-Net',
           'unetpp': 'UNet++', 'deeplabv3plus': 'DeepLabV3+'}

# clean-v3 size taxonomy quantiles (FULL_FIELD scope)
Q25 = 0.0001497998649691358
Q50 = 0.0003401438395182292
Q75 = 0.0008279682677469136

VARIANTS = ['GLOBAL_NATIVE', 'ORACLE_FLOAT_GLOBAL_RETAINED',
            'ORACLE_FLOAT_CROP_ONLY', 'ORACLE_LEGACY_UINT8_CROP_ONLY']


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Model / data
# ---------------------------------------------------------------------------

def load_model(key: str, device: str = 'cuda'):
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise'
                        / 'phase_11_failure_analysis' / 'code'))
    from src.utils.device import get_device
    # frozen checkpoints (same paths used by Phase 10/11)
    ckpt = {
        'unet': PROJECT_ROOT / 'checkpoints/phase9_kub_unet_baseline_seed42_512_clean_v3/best.pt',
        'attention_unet': PROJECT_ROOT / 'checkpoints/phase10_kub_attention_unet_seed42_512_clean_v3/best.pt',
        'unetpp': PROJECT_ROOT / 'checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt',
        'deeplabv3plus': PROJECT_ROOT / 'checkpoints/phase10_kub_deeplabv3plus_seed42_512_clean_v3/best.pt',
    }[key]
    if key == 'unet':
        from src.models.unet import UNet as M
    elif key == 'attention_unet':
        from src.models.attention_unet import AttentionUNet as M
    elif key == 'unetpp':
        from src.models.unetpp import UNetPlusPlus as M
    else:
        from src.models.deeplabv3plus import DeepLabV3Plus as M
    ck = torch.load(ckpt, map_location='cpu', weights_only=False)
    mc = ck['configuration']['model']
    model = M(in_channels=mc['input_channels'], out_channels=mc['output_channels'],
              base_channels=mc['base_channels'])
    model.load_state_dict(ck['model_state'])
    dev = get_device(require_cuda=True)
    return model.to(dev).eval(), dev


def make_loader():
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from torch.utils.data import DataLoader
    from src.data.kub_dataset import KUBDataset
    ds = KUBDataset(manifest_path=PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv',
                    split='VAL', target_size=TARGET)
    return DataLoader(ds, batch_size=BATCH, shuffle=False, num_workers=0, pin_memory=True), ds


def full_field_frame() -> pd.DataFrame:
    """The 103 clean-v3 KUB VAL FULL_FIELD cases."""
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.data.kub_dataset import derive_acquisition_type
    df = pd.read_csv(PROJECT_ROOT / 'manifests' / 'phase4_v3' / 'val.csv')
    k = df[df['dataset'] == 'KUB'].copy().reset_index(drop=True)
    k['acquisition_type'] = k['image_path'].apply(derive_acquisition_type)
    ff = k[k['acquisition_type'] == 'FULL_FIELD'].reset_index(drop=True)
    return ff[['sample_id', 'patient_id', 'category', 'image_path', 'mask_path',
               'acquisition_type']]


def native_gt(mask_path: Path) -> np.ndarray:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask
    return binarize_mask(np.array(Image.open(mask_path).convert('L'))).astype(np.uint8)


# ---------------------------------------------------------------------------
# Geometry (frozen: per-component bbox, margin 0.25, square, clip + zero-pad)
# ---------------------------------------------------------------------------

def extract_native_components(gt: np.ndarray) -> List[Dict[str, Any]]:
    lab, n = label(gt > 0, structure=STRUCT8)
    H, W = gt.shape
    comps = []
    for cid in range(1, n + 1):
        m = lab == cid
        ys, xs = np.where(m)
        min_y, max_y = int(ys.min()), int(ys.max())
        min_x, max_x = int(xs.min()), int(xs.max())
        px = int(m.sum())
        comps.append({'native_component_id': cid,
                      'min_y': min_y, 'max_y': max_y, 'min_x': min_x, 'max_x': max_x,
                      'bbox_height': max_y - min_y + 1, 'bbox_width': max_x - min_x + 1,
                      'native_component_pixels': px,
                      'native_component_ratio': float(px / (H * W)),
                      'native_H': H, 'native_W': W})
    return comps


def size_stratum(ratio: float) -> str:
    if ratio <= Q25:
        return 'TINY'
    if ratio <= Q50:
        return 'SMALL'
    if ratio <= Q75:
        return 'MEDIUM'
    return 'LARGE'


def compute_square_crop(comp: Dict[str, Any], margin: float = MARGIN) -> Dict[str, Any]:
    """Frozen geometry: round(margin*bbox_dim) per axis; square; clip + zero-pad."""
    H, W = comp['native_H'], comp['native_W']
    min_y, max_y, min_x, max_x = comp['min_y'], comp['max_y'], comp['min_x'], comp['max_x']
    bh, bw = comp['bbox_height'], comp['bbox_width']
    m_y, m_x = round(margin * bh), round(margin * bw)
    e_min_y, e_max_y = min_y - m_y, max_y + m_y
    e_min_x, e_max_x = min_x - m_x, max_x + m_x
    e_h = e_max_y - e_min_y + 1
    e_w = e_max_x - e_min_x + 1
    side = max(e_h, e_w)
    cy = (e_min_y + e_max_y) / 2.0
    cx = (e_min_x + e_max_x) / 2.0
    y1 = round(cy - side / 2.0); y2 = y1 + side
    x1 = round(cx - side / 2.0); x2 = x1 + side
    pad_top, pad_bottom = max(0, -y1), max(0, y2 - H)
    pad_left, pad_right = max(0, -x1), max(0, x2 - W)
    clip_y1, clip_y2 = max(0, y1), min(H, y2)
    clip_x1, clip_x2 = max(0, x1), min(W, x2)
    return {'y1': y1, 'y2': y2, 'x1': x1, 'x2': x2,
            'clip_y1': clip_y1, 'clip_y2': clip_y2, 'clip_x1': clip_x1, 'clip_x2': clip_x2,
            'pad_top': pad_top, 'pad_bottom': pad_bottom, 'pad_left': pad_left,
            'pad_right': pad_right, 'crop_side': side,
            'effective_magnification': 512.0 / float(side), 'margin': margin}


def crop_tensor(image_path: Path, geom: Dict[str, Any]) -> torch.Tensor:
    """Crop the ORIGINAL grayscale image, zero-pad to square side, resize 512 BILINEAR."""
    arr = np.asarray(Image.open(image_path).convert('L'))
    valid = arr[geom['clip_y1']:geom['clip_y2'], geom['clip_x1']:geom['clip_x2']]
    padded = np.pad(valid, ((geom['pad_top'], geom['pad_bottom']),
                            (geom['pad_left'], geom['pad_right'])),
                    mode='constant', constant_values=0)
    pil = Image.fromarray(padded).resize((TARGET, TARGET), Image.Resampling.BILINEAR)
    t = torch.from_numpy(np.asarray(pil, dtype=np.float32).copy()).unsqueeze(0).unsqueeze(0) / 255.0
    return t


# ---------------------------------------------------------------------------
# Map-back
# ---------------------------------------------------------------------------

def restore_float(prob_512: np.ndarray, geom: Dict[str, Any], shape: Tuple[int, int]) -> np.ndarray:
    """PRIMARY: float bilinear restore to square side, strip pad, place at clip coords."""
    side = geom['crop_side']
    t = torch.from_numpy(prob_512.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    r = torch.nn.functional.interpolate(t, size=(side, side), mode='bilinear',
                                        align_corners=False)
    prob_crop = r.squeeze().numpy().astype(np.float32)
    p_top, p_bot = geom['pad_top'], side - geom['pad_bottom']
    p_left, p_right = geom['pad_left'], side - geom['pad_right']
    valid = prob_crop[p_top:p_bot, p_left:p_right]
    full = np.zeros(shape, dtype=np.float32)
    full[geom['clip_y1']:geom['clip_y2'], geom['clip_x1']:geom['clip_x2']] = valid
    return full


def restore_legacy_uint8(prob_512: np.ndarray, geom: Dict[str, Any],
                         shape: Tuple[int, int]) -> np.ndarray:
    """LEGACY: EXACT historical semantics (PIL + uint8 quantisation)."""
    side = geom['crop_side']
    pil = Image.fromarray((prob_512 * 255.0).astype(np.uint8)).resize(
        (side, side), Image.Resampling.BILINEAR)
    prob_crop = np.asarray(pil, dtype=np.float32) / 255.0
    p_top, p_bot = geom['pad_top'], side - geom['pad_bottom']
    p_left, p_right = geom['pad_left'], side - geom['pad_right']
    valid = prob_crop[p_top:p_bot, p_left:p_right]
    full = np.zeros(shape, dtype=np.float32)
    full[geom['clip_y1']:geom['clip_y2'], geom['clip_x1']:geom['clip_x2']] = valid
    return full


def global_native(prob_512: np.ndarray, geom: Dict[str, Any],
                  native_shape: Tuple[int, int]) -> np.ndarray:
    """Invert canonical preprocessing: strip pad, resize valid extent to native (FLOAT bilinear)."""
    H, W = native_shape
    nw, nh = geom['resized_w'], geom['resized_h']
    pl, pt = geom['pad_left'], geom['pad_top']
    valid = prob_512[pt:pt + nh, pl:pl + nw]
    t = torch.from_numpy(valid.astype(np.float32)).unsqueeze(0).unsqueeze(0)
    r = torch.nn.functional.interpolate(t, size=(H, W), mode='bilinear', align_corners=False)
    return r.squeeze().numpy().astype(np.float32)


def preprocess_geometry(native_shape: Tuple[int, int]) -> Dict[str, int]:
    H, W = native_shape
    scale = min(TARGET / W, TARGET / H)
    nw, nh = max(1, round(W * scale)), max(1, round(H * scale))
    pl, pt = (TARGET - nw) // 2, (TARGET - nh) // 2
    return {'resized_w': nw, 'resized_h': nh, 'pad_left': pl, 'pad_top': pt}


# ---------------------------------------------------------------------------
# Metrics (native space)
# ---------------------------------------------------------------------------

def native_metrics(gt: np.ndarray, pred_bool: np.ndarray) -> Dict[str, Any]:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.metrics.segmentation import hd95
    g = gt.astype(bool); p = pred_bool.astype(bool)
    tp = float((p & g).sum()); fp = float((p & ~g).sum()); fn = float((~p & g).sum())
    eps = 1e-7
    h = hd95(p, g)
    return {
        'dice': (2 * tp + eps) / (2 * tp + fp + fn + eps),
        'iou': (tp + eps) / (tp + fp + fn + eps),
        'precision': (tp + eps) / (tp + fp + eps),
        'recall': (tp + eps) / (tp + fn + eps),
        'tp_pixels': tp, 'fp_pixels': fp, 'fn_pixels': fn,
        'prediction_empty': bool(p.sum() == 0),
        'hd95': float(h['hd95']) if h['hd95_valid'] else np.nan,
        'hd95_valid': bool(h['hd95_valid']),
        'hd95_invalid_reason': h.get('invalid_reason', ''),
    }


def component_detection(gt: np.ndarray, pred_bool: np.ndarray,
                        labels: np.ndarray, n_comp: int) -> Tuple[int, int]:
    det = 0
    for cid in range(1, n_comp + 1):
        if int((pred_bool & (labels == cid)).sum()) >= 1:
            det += 1
    return det, n_comp - det


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def run(verbose: bool = True) -> Dict[str, Any]:
    import sys
    sys.path.insert(0, str(PROJECT_ROOT))
    from src.utils.targets import binarize_mask

    ff = full_field_frame()
    if verbose:
        print(f'FULL_FIELD cases: {len(ff)}')

    # ---- geometry per case (deterministic, model-independent) ----
    case_geom, geometry_rows, comp_index = {}, [], []
    for _, r in ff.iterrows():
        gt = native_gt(Path(r['mask_path']))
        comps = extract_native_components(gt)
        pg = preprocess_geometry(gt.shape)
        case_geom[r['sample_id']] = {'gt': gt, 'comps': comps, 'pre': pg,
                                     'shape': gt.shape, 'image_path': r['image_path']}
        for c in comps:
            g = compute_square_crop(c)
            geometry_rows.append({'sample_id': r['sample_id'], 'patient_id': r['patient_id'],
                                  'category': r['category'],
                                  'native_component_id': c['native_component_id'],
                                  'native_component_pixels': c['native_component_pixels'],
                                  'native_component_ratio': c['native_component_ratio'],
                                  'size_stratum': size_stratum(c['native_component_ratio']),
                                  'native_H': c['native_H'], 'native_W': c['native_W'],
                                  'bbox_min_y': c['min_y'], 'bbox_max_y': c['max_y'],
                                  'bbox_min_x': c['min_x'], 'bbox_max_x': c['max_x'],
                                  'bbox_height': c['bbox_height'], 'bbox_width': c['bbox_width'],
                                  **{f'crop_{k}': v for k, v in g.items()}})
            comp_index.append((r['sample_id'], c['native_component_id'], g))
    geom_df = pd.DataFrame(geometry_rows)
    total_comps = len(geom_df)
    if verbose:
        print(f'native GT components: {total_comps}')
        print('size strata:', geom_df['size_stratum'].value_counts().to_dict())

    # ---- global EVALUATION_512 pass (all 280, filtered to FULL_FIELD) ----
    loader, ds = make_loader()
    ff_ids = set(ff['sample_id'])
    global_eval512, global_native_prob = {}, {}
    repro_rows = []
    p11 = pd.read_csv(TABLES / 'phase11_clean_v3_per_model_case_failure_metrics.csv')
    p11_ff = p11[p11['acquisition_type'] == 'FULL_FIELD']

    for key in MODELS:
        model, dev = load_model(key)
        if verbose:
            print(f'  global pass {DISPLAY[key]} ...')
        for batch in loader:
            imgs = batch['image'].to(dev)
            with torch.no_grad():
                with torch.amp.autocast('cuda', enabled=(dev.type == 'cuda')):
                    out = model(imgs)
                probs = torch.sigmoid(out).float().cpu().numpy()[:, 0]
            masks = batch['mask'].cpu().numpy()[:, 0]
            for b in range(probs.shape[0]):
                sid = batch['sample_id'][b]
                if sid not in ff_ids:
                    continue
                gt512 = (masks[b] > 0).astype(np.uint8)
                pr512 = (probs[b] >= THRESHOLD).astype(np.uint8)
                tp = float((pr512 & gt512).sum()); fp = float((pr512 & (1 - gt512)).sum())
                fn = float(((1 - pr512) & gt512).sum()); eps = 1e-7
                global_eval512[(key, sid)] = {
                    'dice': (2 * tp + eps) / (2 * tp + fp + fn + eps),
                    'iou': (tp + eps) / (tp + fp + fn + eps),
                    'precision': (tp + eps) / (tp + fp + fn + eps),
                    'recall': (tp + eps) / (tp + fn + eps)}
                # native-space global
                cg = case_geom[sid]
                global_native_prob[(key, sid)] = global_native(probs[b], cg['pre'], cg['shape'])
        del model
        torch.cuda.empty_cache()

    # ---- reproduction gate (EVALUATION_512 vs Phase-11) ----
    for key in MODELS:
        ref = p11_ff[p11_ff['model'] == key].set_index('sample_id')
        dd, di = [], []
        for sid in ff['sample_id']:
            g = global_eval512[(key, sid)]
            dd.append(abs(g['dice'] - float(ref.loc[sid, 'dice'])))
            di.append(abs(g['iou'] - float(ref.loc[sid, 'iou'])))
        repro_rows.append({'model': DISPLAY[key], 'model_key': key, 'n_cases': len(dd),
                           'mean_abs_dice_diff': float(np.mean(dd)),
                           'max_abs_dice_diff': float(np.max(dd)),
                           'mean_abs_iou_diff': float(np.mean(di)),
                           'max_abs_iou_diff': float(np.max(di)),
                           'pass_1e4': bool(np.max(dd) <= 1e-4)})
    repro = pd.DataFrame(repro_rows)
    if verbose:
        print()
        print(repro.to_string(index=False))
    if not bool(repro['pass_1e4'].all()):
        raise RuntimeError('GLOBAL REPRODUCTION GATE FAILED (max abs Dice diff > 1e-4) '
                           '-> CHECK_REQUIRED; oracle inference NOT run')

    # ---- regional crop inference (one pass, all variants derived from it) ----
    regional_float, regional_legacy, crop_counts = {}, {}, {}
    for key in MODELS:
        model, dev = load_model(key)
        if verbose:
            print(f'  regional crop pass {DISPLAY[key]} ...')
        n = 0
        for sid, cid, g in comp_index:
            t = crop_tensor(case_geom[sid]['image_path'], g).to(dev)
            with torch.no_grad():
                with torch.amp.autocast('cuda', enabled=(dev.type == 'cuda')):
                    logits = model(t)
                prob512 = torch.sigmoid(logits).float().squeeze().cpu().numpy().astype(np.float32)
            shape = case_geom[sid]['shape']
            regional_float.setdefault((key, sid), []).append(restore_float(prob512, g, shape))
            regional_legacy.setdefault((key, sid), []).append(restore_legacy_uint8(prob512, g, shape))
            n += 1
        crop_counts[DISPLAY[key]] = n
        del model
        torch.cuda.empty_cache()
    if verbose:
        print('crop inferences:', crop_counts)

    # ---- variants + metrics ----
    case_rows, comp_rows, delta_rows = [], [], []
    for sid in ff['sample_id']:
        cg = case_geom[sid]; gt = cg['gt']; shape = cg['shape']
        labels, n_comp = label(gt > 0, structure=STRUCT8)
        for key in MODELS:
            G = global_native_prob[(key, sid)]
            rf = regional_float.get((key, sid), [])
            rl = regional_legacy.get((key, sid), [])
            R = np.maximum.reduce(rf) if rf else np.zeros(shape, dtype=np.float32)
            RL = np.maximum.reduce(rl) if rl else np.zeros(shape, dtype=np.float32)
            U = np.zeros(shape, dtype=bool)
            for g in [x[2] for x in comp_index if x[0] == sid]:
                U[g['clip_y1']:g['clip_y2'], g['clip_x1']:g['clip_x2']] = True
            variants = {
                'GLOBAL_NATIVE': G,
                'ORACLE_FLOAT_GLOBAL_RETAINED': np.where(U, R, G),
                'ORACLE_FLOAT_CROP_ONLY': np.where(U, R, 0.0),
                'ORACLE_LEGACY_UINT8_CROP_ONLY': np.where(U, RL, 0.0),
            }
            per_variant = {}
            for vname, prob in variants.items():
                pred = prob >= THRESHOLD
                m = native_metrics(gt, pred)
                det, missed = component_detection(gt, pred, labels, n_comp)
                per_variant[vname] = {**m, 'detected': det, 'missed': missed,
                                      'object_recall': float(det / n_comp) if n_comp else np.nan}
                case_rows.append({'sample_id': sid, 'patient_id': cg_row_patient(ff, sid),
                                  'category': cg_row_cat(ff, sid), 'model': key,
                                  'variant': vname, 'native_height': shape[0],
                                  'native_width': shape[1], 'native_gt_components': n_comp,
                                  **m, 'detected_native_components': det,
                                  'missed_native_components': missed,
                                  'object_recall': per_variant[vname]['object_recall'],
                                  'manifest': MANIFEST, 'taxonomy': TAXONOMY,
                                  'margin': MARGIN, 'threshold': THRESHOLD,
                                  'mapback_semantics': 'FLOAT' if 'FLOAT' in vname else
                                      ('NONE' if vname == 'GLOBAL_NATIVE' else 'LEGACY_UINT8'),
                                  'outside_crop_semantics': 'GLOBAL_RETAINED'
                                      if vname == 'ORACLE_FLOAT_GLOBAL_RETAINED' else
                                      ('NOT_APPLICABLE' if vname == 'GLOBAL_NATIVE' else 'ZERO')})
            # component-level detection per variant
            for cid in range(1, n_comp + 1):
                cm = labels == cid
                comp_rows.append({
                    'sample_id': sid, 'native_component_id': cid, 'model': key,
                    'global_detected': bool((variants['GLOBAL_NATIVE'] >= THRESHOLD)[cm].sum() >= 1),
                    'primary_oracle_detected': bool((variants['ORACLE_FLOAT_GLOBAL_RETAINED'] >= THRESHOLD)[cm].sum() >= 1),
                    'float_crop_only_detected': bool((variants['ORACLE_FLOAT_CROP_ONLY'] >= THRESHOLD)[cm].sum() >= 1),
                    'legacy_crop_only_detected': bool((variants['ORACLE_LEGACY_UINT8_CROP_ONLY'] >= THRESHOLD)[cm].sum() >= 1),
                })
            # primary paired deltas
            gv = per_variant['GLOBAL_NATIVE']; pv = per_variant['ORACLE_FLOAT_GLOBAL_RETAINED']
            delta_rows.append({
                'sample_id': sid, 'model': key,
                'global_dice': gv['dice'], 'primary_dice': pv['dice'],
                'delta_dice': pv['dice'] - gv['dice'],
                'global_iou': gv['iou'], 'primary_iou': pv['iou'],
                'delta_iou': pv['iou'] - gv['iou'],
                'global_precision': gv['precision'], 'primary_precision': pv['precision'],
                'delta_precision': pv['precision'] - gv['precision'],
                'global_recall': gv['recall'], 'primary_recall': pv['recall'],
                'delta_recall': pv['recall'] - gv['recall'],
                'global_object_recall': gv['object_recall'],
                'primary_object_recall': pv['object_recall'],
                'delta_object_recall': pv['object_recall'] - gv['object_recall'],
                'global_missed_components': gv['missed'],
                'primary_missed_components': pv['missed'],
                'recovered_components': gv['missed'] - pv['missed'],
                'empty_global': gv['prediction_empty'],
                'empty_primary': pv['prediction_empty'],
                'empty_recovered': bool(gv['prediction_empty'] and not pv['prediction_empty']),
            })

    case_df = pd.DataFrame(case_rows)
    comp_df = pd.DataFrame(comp_rows)
    delta_df = pd.DataFrame(delta_rows)
    return {'ff': ff, 'geom': geom_df, 'case': case_df, 'comp': comp_df,
            'delta': delta_df, 'repro': repro, 'crop_counts': crop_counts,
            'case_geom': case_geom}


def cg_row_patient(ff, sid):
    return ff.loc[ff['sample_id'] == sid, 'patient_id'].iloc[0]


def cg_row_cat(ff, sid):
    return ff.loc[ff['sample_id'] == sid, 'category'].iloc[0]


# ---------------------------------------------------------------------------
# Upstream frozen epoch tables (read-only appendix)
# ---------------------------------------------------------------------------
PHASE10_EPOCH_TABLES = {
    'unet': TABLES / 'phase10_final_epoch_results_unet.csv',
    'attention_unet': TABLES / 'phase10_final_epoch_results_attention_unet.csv',
    'unetpp': TABLES / 'phase10_final_epoch_results_unetpp.csv',
    'deeplabv3plus': TABLES / 'phase10_final_epoch_results_deeplabv3plus.csv',
}
EXPECTED_EPOCH_ROWS = {'unet': 59, 'attention_unet': 69, 'unetpp': 85, 'deeplabv3plus': 67}
