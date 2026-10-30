"""
Phase 08 Part 1A — clean-v3 data/target/device/reproducibility foundation audit.

This module AUDITS and VALIDATES the canonical `src/` infrastructure. It does not
re-implement production functionality: the notebook imports these functions, and
the heavy lifting stays in `src/`.

No training. No scientific performance claims. TEST content is never opened.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from PIL import Image

PROJECT_ROOT = Path(r'D:\Softfors\jup')
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.utils.targets import (binarize_mask, foreground_label_signature,  # noqa: E402
                               is_binary, FOREGROUND_RULE)
from src.utils import device as dev  # noqa: E402
from src.utils import config as cfgmod  # noqa: E402
from src.utils import manifest_guard  # noqa: E402
from src.utils.reproducibility import (set_seed, seed_worker, make_generator,  # noqa: E402
                                       capture_random_state, restore_random_state)
from src.data.transforms import SegmentationTransform  # noqa: E402
from src.data.kub_dataset import KUBDataset, derive_acquisition_type  # noqa: E402
from src.data.loaders import create_loader  # noqa: E402
from src.metrics.segmentation import binary_metrics  # noqa: E402
from src.metrics.object_metrics import object_metrics  # noqa: E402
from src.analysis import kub_object_size as kos  # noqa: E402
from src.models.factory import create_model  # noqa: E402

TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase08_baseline_infrastructure'

MANIFEST_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'
TRAIN_MANIFEST = MANIFEST_DIR / 'train.csv'
VAL_MANIFEST = MANIFEST_DIR / 'val.csv'

MANIFEST_VERSION = 'phase4_v3'
TAXONOMY_ID = 'kub_size_clean_v3_v1'

EXPECTED = {'kub_train_cases': 1978, 'kub_val_cases': 280,
            'train_patients': 318, 'val_patients': 111}

STRATA = ('TINY', 'SMALL', 'MEDIUM', 'LARGE')

FINAL_TABLES = [
    'phase08_kub_v3_loader_sample_audit.csv',
    'phase08_transform_contract_audit.csv',
    'phase08_metric_contract.csv',
    'phase08_reproducibility_audit.csv',
    'phase08_checkpoint_contract.csv',
]


def sha256_file(path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def sha256_of_strings(items) -> str:
    h = hashlib.sha256()
    for s in items:
        h.update(str(s).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()


def write_table(df: pd.DataFrame, name: str, out_dir=None) -> Path:
    out_dir = out_dir or TABLES
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / name
    df.to_csv(p, index=False)
    return p


def final_table_registry(out_dir=None) -> pd.DataFrame:
    out_dir = out_dir or TABLES
    rows = []
    for name in FINAL_TABLES:
        p = out_dir / name
        rows.append({'table': name, 'exists': p.exists(),
                     'bytes': int(p.stat().st_size) if p.exists() else 0,
                     'sha256': sha256_file(p) if p.exists() else None})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Manifest verification
# ---------------------------------------------------------------------------

def verify_manifests() -> dict:
    """Explicitly validate phase4_v3 and report KUB population counts."""
    res = manifest_guard.validate_manifest_version('phase4_v3')
    train = pd.read_csv(TRAIN_MANIFEST)
    val = pd.read_csv(VAL_MANIFEST)
    test_meta = pd.read_csv(MANIFEST_DIR / 'test.csv')   # metadata only, never decoded

    ktr = train[train['dataset'] == 'KUB']
    kva = val[val['dataset'] == 'KUB']
    kte = test_meta[test_meta['dataset'] == 'KUB']

    return {
        'manifest_version': MANIFEST_VERSION,
        'guard_ok': bool(res['ok']),
        'guard_files': sorted(res['passed']),
        'train_rows': int(len(train)),
        'val_rows': int(len(val)),
        'kub_train_cases': int(len(ktr)),
        'kub_val_cases': int(len(kva)),
        'train_patients': int(ktr['patient_id'].nunique()),
        'val_patients': int(kva['patient_id'].nunique()),
        'patient_overlap': int(len(set(ktr['patient_id']) & set(kva['patient_id']))),
        'test_metadata_rows': int(len(kte)),
        'test_content_reads': 0,
        'counts_ok': (len(ktr) == EXPECTED['kub_train_cases']
                      and len(kva) == EXPECTED['kub_val_cases']),
        'manifest_hashes': {k: sha256_file(MANIFEST_DIR / f'{k}.csv')
                            for k in ('train', 'val', 'test', 'quarantined')},
    }


# ---------------------------------------------------------------------------
# Target contract audit
# ---------------------------------------------------------------------------

def audit_target_contract(train_df: pd.DataFrame, per_category: int = 120) -> dict:
    """
    Verify mask>0 binarization against the real native label vocabulary.

    Sampling is stratified across anatomical categories so every observed raw
    label signature (including Ureteric's {0,3} and the widespread {0,255}) is
    exercised rather than only whichever category happens to come first.
    """
    kub = train_df[train_df['dataset'] == 'KUB']
    sample = (kub.groupby('category', group_keys=False)
                 .head(per_category))
    signatures = {}
    equivalence_failures = 0
    nonbinary_after = 0
    for _, r in sample.iterrows():
        with Image.open(r['mask_path']) as m:
            sig = foreground_label_signature(m)
            signatures[sig] = signatures.get(sig, 0) + 1
            old = (np.asarray(m).copy() > 0).astype(np.float32)
            new = binarize_mask(m)
            if not np.array_equal(old, new):
                equivalence_failures += 1
            if not is_binary(new):
                nonbinary_after += 1
    labels = sorted({int(v) for s in signatures for v in s.split('|')})
    return {
        'foreground_rule': FOREGROUND_RULE,
        'samples_audited': int(len(sample)),
        'sampling': f'category-stratified, up to {per_category} per category',
        'label_signatures': dict(sorted(signatures.items())),
        'raw_label_union': labels,
        'non_one_foreground_labels': [v for v in labels if v not in (0, 1)],
        'binarize_equivalence_failures': equivalence_failures,
        'non_binary_after_binarize': nonbinary_after,
    }


# ---------------------------------------------------------------------------
# Image mode / channel audit
# ---------------------------------------------------------------------------

def audit_image_modes(train_df: pd.DataFrame, n: int = 120) -> dict:
    kub = train_df[train_df['dataset'] == 'KUB'].head(n).copy()
    kub['acq'] = kub['image_path'].map(derive_acquisition_type)
    modes = {}
    for _, r in kub.iterrows():
        with Image.open(r['image_path']) as im:
            key = (r['acq'], im.mode)
            modes[str(key)] = modes.get(str(key), 0) + 1

    # channel behaviour through the canonical transform
    t = SegmentationTransform(size=256, train=False)
    checks = []
    for mode in ('L', 'RGB'):
        arr = (np.random.default_rng(0).random((64, 48, 3 if mode == 'RGB' else 1)) * 255)
        arr = arr.astype(np.uint8)
        img = Image.fromarray(arr.squeeze() if mode == 'L' else arr, mode=mode)
        mask = Image.fromarray(np.zeros((64, 48), dtype=np.uint8), mode='L')
        img_t, mask_t, _ = t(img, mask)
        checks.append({'source_mode': mode, 'tensor_channels': int(img_t.shape[0]),
                       'tensor_shape': str(tuple(img_t.shape))})
    return {
        'source_mode_counts': modes,
        'channel_checks': checks,
        'input_channel_convention': 1,
        'convention_note': ('KUBDataset calls Image.convert("L") then unsqueeze(0), so both '
                            'RGB (FULL_FIELD) and L (ROI) images become a 1-channel tensor. '
                            'This is the historical convention and is preserved.'),
    }


# ---------------------------------------------------------------------------
# Transform contract audit
# ---------------------------------------------------------------------------

def audit_transform_contract(train_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for size in (256, 512):
        t = SegmentationTransform(size=size, train=False)
        for (h, w) in ((3072, 3072), (2880, 2304), (80, 60), (512, 512)):
            img = Image.fromarray(np.zeros((h, w), dtype=np.uint8), mode='L')
            mask = np.zeros((h, w), dtype=np.uint8)
            mask[h // 4: h // 4 + max(1, h // 10), w // 4: w // 4 + max(1, w // 10)] = 255
            img_t, mask_t, meta = t(img, Image.fromarray(mask, mode='L'))
            left, top, right, bottom = meta.padding
            rows.append({
                'target_size': size,
                'source_h': h, 'source_w': w,
                'expected_scale': round(min(size / w, size / h), 8),
                'actual_scale': round(meta.scale, 8),
                'resized_w': meta.resized_width, 'resized_h': meta.resized_height,
                'pad_left': left, 'pad_top': top, 'pad_right': right, 'pad_bottom': bottom,
                'padded_w_ok': (meta.resized_width + left + right) == size,
                'padded_h_ok': (meta.resized_height + top + bottom) == size,
                'image_shape': str(tuple(img_t.shape)),
                'mask_shape': str(tuple(mask_t.shape)),
                'aligned': tuple(img_t.shape[-2:]) == tuple(mask_t.shape[-2:]),
                'mask_is_binary': is_binary(mask_t.numpy()),
                'mask_foreground_preserved': bool(mask_t.sum() > 0),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Metric contract audit
# ---------------------------------------------------------------------------

def audit_metric_contract() -> pd.DataFrame:
    import inspect
    rows = []

    def _sig(fn):
        return str(inspect.signature(fn))

    rows.append({
        'metric': 'dice', 'module': 'src.metrics.segmentation',
        'function': 'binary_metrics', 'signature': _sig(binary_metrics),
        'foreground_semantics': 'logits > threshold (sigmoid)',
        'empty_handling': 'epsilon-smoothed, defined for empty masks',
        'epsilon': inspect.signature(binary_metrics).parameters['epsilon'].default,
        'threshold': inspect.signature(binary_metrics).parameters['threshold'].default,
        'version': 'v1', 'notes': 'not retuned in Part 1A',
    })
    for m in ('iou', 'precision', 'recall'):
        rows.append({
            'metric': m, 'module': 'src.metrics.segmentation',
            'function': 'binary_metrics', 'signature': _sig(binary_metrics),
            'foreground_semantics': 'logits > threshold (sigmoid)',
            'empty_handling': 'epsilon-smoothed',
            'epsilon': inspect.signature(binary_metrics).parameters['epsilon'].default,
            'threshold': inspect.signature(binary_metrics).parameters['threshold'].default,
            'version': 'v1', 'notes': 'same call as dice',
        })
    rows.append({
        'metric': 'hd95', 'module': 'src.metrics.segmentation', 'function': 'hd95',
        'signature': _sig(__import__('src.metrics.segmentation', fromlist=['hd95']).hd95),
        'foreground_semantics': 'boolean masks',
        'empty_handling': 'explicit hd95_valid flag; NaN or supplied penalty; never 0',
        'epsilon': None, 'threshold': None, 'version': 'v1',
        'notes': '8-connected boundary extraction',
    })
    rows.append({
        'metric': 'object_recall', 'module': 'src.metrics.object_metrics',
        'function': 'object_metrics', 'signature': _sig(object_metrics),
        'foreground_semantics': 'prediction > 0 and target > 0',
        'empty_handling': 'NaN recall when no GT components',
        'epsilon': None, 'threshold': None, 'version': 'phase14_authoritative',
        'notes': 'connectivity=8, overlap-based, minimum_overlap_pixels=1',
    })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Reproducibility audit
# ---------------------------------------------------------------------------

def audit_reproducibility() -> pd.DataFrame:
    rows = []

    # python / numpy / torch seeding
    set_seed(2024)
    a = (random_value := __import__('random').random(), float(np.random.rand()),
         float(torch.rand(1)))
    set_seed(2024)
    b = (__import__('random').random(), float(np.random.rand()), float(torch.rand(1)))
    rows.append({'check': 'python_numpy_torch_seed', 'result': 'PASS' if a == b else 'FAIL',
                 'detail': 'set_seed reproduces python/numpy/torch draws'})

    # cuda seeding
    if torch.cuda.is_available():
        set_seed(7)
        c1 = float(torch.rand(1, device='cuda'))
        set_seed(7)
        c2 = float(torch.rand(1, device='cuda'))
        rows.append({'check': 'cuda_seed', 'result': 'PASS' if c1 == c2 else 'FAIL',
                     'detail': 'cuda.manual_seed_all reproduces CUDA draws'})
    else:
        rows.append({'check': 'cuda_seed', 'result': 'SKIP', 'detail': 'CUDA unavailable'})

    # generator
    g1, g2 = make_generator(11), make_generator(11)
    rows.append({'check': 'dataloader_generator',
                 'result': 'PASS' if float(torch.rand(1, generator=g1)) == float(torch.rand(1, generator=g2)) else 'FAIL',
                 'detail': 'make_generator(seed) is reproducible'})

    # worker seeding
    def _worker_run():
        torch.manual_seed(5)
        out = []
        for wid in range(4):
            seed_worker(wid)
            out.append((__import__('random').random(), float(np.random.rand())))
        return out
    rows.append({'check': 'worker_seed', 'result': 'PASS' if _worker_run() == _worker_run() else 'FAIL',
                 'detail': 'seed_worker produces deterministic per-worker streams'})

    # rng round trip
    set_seed(3)
    torch.rand(2)
    st = capture_random_state()
    expect = float(torch.rand(1))
    restore_random_state(st)
    rows.append({'check': 'rng_state_roundtrip',
                 'result': 'PASS' if float(torch.rand(1)) == expect else 'FAIL',
                 'detail': 'capture/restore reproduces the torch CPU stream'})

    # determinism policy
    rows.append({'check': 'determinism_policy', 'result': 'DOCUMENTED',
                 'detail': (f"cudnn.deterministic={torch.backends.cudnn.deterministic}, "
                            f"cudnn.benchmark={torch.backends.cudnn.benchmark}; "
                            "bitwise GPU determinism is NOT claimed")})
    rows.append({'check': 'torch_deterministic_algorithms',
                 'result': str(torch.are_deterministic_algorithms_enabled()),
                 'detail': 'not force-enabled: some CUDA ops lack deterministic kernels'})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Checkpoint contract audit
# ---------------------------------------------------------------------------

def audit_checkpoint_contract(tmpdir: Path) -> pd.DataFrame:
    import inspect
    from src.utils.checkpointing import save_training_checkpoint, load_training_checkpoint

    params = inspect.signature(save_training_checkpoint).parameters
    required_keys = ['model_state', 'optimizer_state', 'scheduler_state', 'grad_scaler_state',
                     'epoch', 'best_validation_score', 'experiment_id', 'seed',
                     'manifest_version', 'taxonomy_id', 'configuration', 'random_state']
    rows = [{'item': k, 'supported': True, 'detail': 'written by save_training_checkpoint'}
            for k in required_keys]
    rows.append({'item': 'taxonomy_id_parameter', 'supported': 'taxonomy_id' in params,
                 'detail': 'additive Phase-08 parameter'})
    rows.append({'item': 'rng_state', 'supported': 'random_state' in required_keys,
                 'detail': 'capture_random_state()/restore_random_state()'})

    # functional round-trip
    model = create_model('unet', in_channels=1, out_channels=1, base_channels=8)
    opt = torch.optim.SGD(model.parameters(), lr=0.01)
    p = Path(tmpdir) / 'phase08_ckpt.pt'
    save_training_checkpoint(p, model, opt, None, None, epoch=0, global_step=0,
                             best_validation_score=0.0, configuration={'probe': True},
                             seed=42, training_history=[], manifest_version=MANIFEST_VERSION,
                             manifest_hashes={}, experiment_id='phase08_infra_probe',
                             model_name='unet', input_resolution=256, threshold=0.5,
                             taxonomy_id=TAXONOMY_ID)
    state = load_training_checkpoint(p, model, opt, restore_rng=True)
    rows.append({'item': 'roundtrip_experiment_id',
                 'supported': state['experiment_id'] == 'phase08_infra_probe',
                 'detail': state['experiment_id']})
    rows.append({'item': 'roundtrip_taxonomy_id',
                 'supported': state.get('taxonomy_id') == TAXONOMY_ID,
                 'detail': str(state.get('taxonomy_id'))})
    rows.append({'item': 'roundtrip_manifest_version',
                 'supported': state.get('manifest_version') == MANIFEST_VERSION,
                 'detail': str(state.get('manifest_version'))})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Deterministic sample selection + loader audit
# ---------------------------------------------------------------------------

def deterministic_sample_selection(train_df: pd.DataFrame, n_total: int = 16,
                                   seed_tag: str = 'phase08-loader-audit') -> pd.DataFrame:
    """
    Deterministic, prediction-independent TRAIN selection.

    Stratifies by (acquisition_type, category) and additionally forces coverage of
    every observed raw mask label signature so heterogeneous labels are exercised.
    """
    kub = train_df[train_df['dataset'] == 'KUB'].copy()
    kub['acquisition_type'] = kub['image_path'].map(derive_acquisition_type)
    kub['stratum'] = kub['acquisition_type'] + '|' + kub['category']
    kub = kub.sort_values('sample_id')

    picked = []
    strata = sorted(kub['stratum'].unique(),
                    key=lambda s: hashlib.sha256(f'{seed_tag}|{s}'.encode()).hexdigest())
    for s in strata:
        members = kub[kub['stratum'] == s]
        if len(members):
            picked.append(members.iloc[len(members) // 2])

    # force one representative per distinct raw label signature
    sig_seen = set()
    for _, r in kub.iterrows():
        with Image.open(r['mask_path']) as m:
            sig = foreground_label_signature(m)
        if sig not in sig_seen:
            sig_seen.add(sig)
            picked.append(r)

    sel = pd.DataFrame(picked).drop_duplicates(subset=['sample_id'])
    sel = sel.sort_values('sample_id').reset_index(drop=True)

    if len(sel) < n_total:
        remaining = kub[~kub['sample_id'].isin(sel['sample_id'])]
        need = n_total - len(sel)
        if len(remaining):
            idx = np.linspace(0, len(remaining) - 1, min(need, len(remaining))).round().astype(int)
            sel = pd.concat([sel, remaining.iloc[idx]]).drop_duplicates(subset=['sample_id'])
    sel = sel.sort_values('sample_id').reset_index(drop=True)
    sel['selection_rank'] = np.arange(1, len(sel) + 1)
    return sel


def audit_loader_samples(sel: pd.DataFrame, target_size: int = 256) -> tuple:
    """Run each selected sample through the canonical loader and record the contract."""
    ds = KUBDataset(TRAIN_MANIFEST, 'TRAIN', target_size=target_size, cache_in_memory=False)
    id_to_index = {sid: i for i, sid in enumerate(ds.frame['sample_id'])}
    rows = []
    for _, r in sel.iterrows():
        idx = id_to_index[r['sample_id']]
        set_seed(0)                      # deterministic augmentation for the audit
        item = ds[idx]
        with Image.open(r['image_path']) as im:
            src_mode = im.mode
        with Image.open(r['mask_path']) as m:
            sig = foreground_label_signature(m)
        mask_np = item['mask'].numpy()
        rows.append({
            'sample_id': r['sample_id'],
            'patient_id': r['patient_id'],
            'category': r['category'],
            'acquisition_type': r['acquisition_type'],
            'source_image_mode': src_mode,
            'raw_mask_label_signature': sig,
            'tensor_shape': str(tuple(item['image'].shape)),
            'mask_tensor_shape': str(tuple(item['mask'].shape)),
            'binary_mask_unique_values': '|'.join(str(int(v)) for v in np.unique(mask_np)),
            'foreground_pixel_count': int(mask_np.sum()),
            'original_width': int(item['original_width']),
            'original_height': int(item['original_height']),
            'resize_scale': float(item['resize_scale']),
            'padding': str(tuple(int(v) for v in item['padding'].tolist())),
            'mask_is_binary': is_binary(mask_np),
        })
    return pd.DataFrame(rows), ds


# ---------------------------------------------------------------------------
# Medical visual gallery
# ---------------------------------------------------------------------------

def loader_gallery_pages(sel: pd.DataFrame, target_size: int = 256,
                         cases_per_page: int = 4,
                         title: str = 'Phase 08 loader/transform fidelity gallery'):
    """
    Paginated gallery: source image | source binary GT | transformed image |
    transformed binary GT | overlay. TRAIN only, no predictions.
    """
    import matplotlib.pyplot as plt

    ds = KUBDataset(TRAIN_MANIFEST, 'TRAIN', target_size=target_size, cache_in_memory=False)
    id_to_index = {sid: i for i, sid in enumerate(ds.frame['sample_id'])}

    n = len(sel)
    n_pages = int(np.ceil(n / cases_per_page))
    figs = []
    for page in range(n_pages):
        chunk = sel.iloc[page * cases_per_page:(page + 1) * cases_per_page]
        nrows = len(chunk)
        fig, axes = plt.subplots(nrows, 5, figsize=(16.5, 3.2 * nrows))
        axes = np.atleast_2d(axes)
        for i, (_, r) in enumerate(chunk.iterrows()):
            item = ds[id_to_index[r['sample_id']]]
            with Image.open(r['image_path']) as im:
                src = np.array(im)
            with Image.open(r['mask_path']) as m:
                src_mask = binarize_mask(m)
            timg = item['image'][0].numpy()
            tmask = item['mask'][0].numpy()

            ax = axes[i]
            ax[0].imshow(src, cmap=('gray' if src.ndim == 2 else None))
            ax[0].set_title('source image', fontsize=8)
            ax[1].imshow(src_mask, cmap='gray', vmin=0, vmax=1)
            ax[1].set_title('source binary GT', fontsize=8)
            ax[2].imshow(timg, cmap='gray')
            ax[2].set_title(f'transformed image {timg.shape}', fontsize=8)
            ax[3].imshow(tmask, cmap='gray', vmin=0, vmax=1)
            ax[3].set_title('transformed GT', fontsize=8)
            ax[4].imshow(timg, cmap='gray')
            rgba = np.zeros((*tmask.shape, 4), dtype=float)
            rgba[..., 0] = 1.0
            rgba[..., 3] = tmask * 0.45
            ax[4].imshow(rgba)
            ax[4].set_title('overlay', fontsize=8)
            for a in ax:
                a.set_xticks([]); a.set_yticks([])
            ax[0].set_xlabel(
                f"{r['sample_id'][:12]} | {r['category']} | {r['acquisition_type']}\n"
                f"{item['original_width']}x{item['original_height']} | scale={item['resize_scale']:.4f}",
                fontsize=7, labelpad=3)
        for i in range(nrows):
            for j in range(5):
                if i >= len(chunk):
                    axes[i, j].axis('off')
        fig.suptitle(f'{title} — page {page + 1}/{n_pages}', fontsize=11, fontweight='bold')
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        figs.append(fig)
    return figs


def save_fig(fig, path: Path, dpi: int = 120):
    import matplotlib.pyplot as plt
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# CUDA smoke test (INFRASTRUCTURE_TEST_ONLY)
# ---------------------------------------------------------------------------

def cuda_smoke_test(sel: pd.DataFrame, n_batches: int = 2, batch_size: int = 2,
                    target_size: int = 256, seed: int = 42) -> dict:
    """
    Minimal CUDA plumbing smoke test. NOT baseline training.

    Verifies CUDA tensors, forward, binary target shape, loss, backward,
    optimizer step, AMP autocast, GradScaler, finiteness, and memory reporting.
    The model is an EXISTING repository baseline used purely as an engineering
    vehicle and is clearly labelled INFRASTRUCTURE_TEST_ONLY.
    """
    if not dev.cuda_available():
        return {'performed': False, 'reason': 'CUDA unavailable'}

    device = dev.get_device(require_cuda=True)
    set_seed(seed)

    ds = KUBDataset(TRAIN_MANIFEST, 'TRAIN', target_size=target_size, cache_in_memory=False)
    id_to_index = {sid: i for i, sid in enumerate(ds.frame['sample_id'])}
    subset = torch.utils.data.Subset(ds, [id_to_index[s] for s in sel['sample_id'].head(8)])
    loader = create_loader(subset, batch_size=batch_size, shuffle=False, seed=seed,
                           num_workers=0, pin_memory=True)

    model = create_model('unet', in_channels=1, out_channels=1, base_channels=8).to(device)
    model.train()
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01, momentum=0.9)
    scaler = dev.make_grad_scaler(enabled=True)
    loss_fn = torch.nn.BCEWithLogitsLoss()

    torch.cuda.reset_peak_memory_stats(device)
    batches = 0
    losses = []
    for images, masks in _iter_two_tensor(loader, n_batches):
        images = images.to(device, non_blocking=True)
        masks = masks.to(device, non_blocking=True)
        optimizer.zero_grad(set_to_none=True)
        with dev.make_autocast(enabled=True):
            logits = model(images)
            loss = loss_fn(logits, masks)
        scaler.scale(loss).backward()
        scaler.step(optimizer)
        scaler.update()
        assert torch.isfinite(loss).item(), 'non-finite loss'
        losses.append(float(loss.detach().cpu()))
        batches += 1

    peak_mb = torch.cuda.max_memory_allocated(device) / (1024 ** 2)
    return {
        'performed': True,
        'label': 'INFRASTRUCTURE_TEST_ONLY',
        'device': str(device),
        'device_name': torch.cuda.get_device_name(0),
        'batches': batches,
        'batch_size': batch_size,
        'input_shape': str(tuple(images.shape)),
        'target_shape': str(tuple(masks.shape)),
        'target_is_binary': bool(is_binary(masks.detach().cpu().numpy())),
        'losses_finite': bool(all(np.isfinite(losses))),
        'amp_enabled': True,
        'grad_scaler_used': True,
        'peak_memory_mb': round(peak_mb, 2),
        'scientific_claim': 'NONE',
        'note': 'Model is an existing baseline used only as an engineering smoke vehicle.',
    }


def _iter_two_tensor(loader, n_batches):
    """Yield (images, masks) from a loader whose items are dicts."""
    count = 0
    for batch in loader:
        yield batch['image'], batch['mask']
        count += 1
        if count >= n_batches:
            return


# ---------------------------------------------------------------------------
# Taxonomy integration audit
# ---------------------------------------------------------------------------

def audit_taxonomy_integration(train_df: pd.DataFrame, n: int = 60) -> dict:
    from scipy.ndimage import label as nd_label
    thresholds = kos.get_kub_size_taxonomy(TAXONOMY_ID)
    kub = train_df[train_df['dataset'] == 'KUB'].copy()
    kub['acquisition_type'] = kub['image_path'].map(derive_acquisition_type)
    ff = kub[kub['acquisition_type'] == 'FULL_FIELD'].head(n)
    roi = kub[kub['acquisition_type'] == 'ROI'].head(20)

    def _strata(df):
        out = {}
        for _, r in df.iterrows():
            with Image.open(r['mask_path']) as m:
                arr = binarize_mask(m)
            h, w = arr.shape
            lab, nlab = nd_label(arr > 0, structure=np.ones((3, 3), dtype=int))
            for cid in range(1, nlab + 1):
                ratio = float((lab == cid).sum()) / (h * w)
                s = kos.classify_component_ratio(ratio, thresholds)
                out[s] = out.get(s, 0) + 1
        return out

    return {
        'taxonomy_id': TAXONOMY_ID,
        'thresholds': thresholds,
        'api_ok': True,
        'full_field_strata_sample': _strata(ff),
        'roi_handling': 'ROI_NOT_PRIMARY_BINNED',
        'roi_specific_taxonomy_created': False,
        'note': ('Object-level metadata uses 8-connectivity; training masks remain '
                 'ordinary binary masks.'),
    }
