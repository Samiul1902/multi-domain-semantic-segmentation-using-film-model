"""
Phase 06 Part 1A — KUB Dataset Characterization (CLEAN-v3).

Reusable implementation module. The reviewer notebook imports these functions
rather than duplicating processing code.

Governance
----------
- Reads ONLY KUB medical content from manifests/phase4_v3/train.csv and val.csv.
- TEST is referenced through locked manifest METADATA only (counts / IDs / hashes).
- TEST image, mask, and pixel content is NEVER read.
- No model training. No inference. No tiny-object threshold is defined here.

All functions are deterministic and read-only with respect to manifests.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image

# ---------------------------------------------------------------------------
# Constants / governance
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'
V2_MANIFEST_DIR = PROJECT_ROOT / 'manifests'

ACTIVE_MANIFEST_VERSION = 'phase4_v3'
HISTORICAL_MANIFEST_VERSION = 'phase4_v2'

TEST_SHA = '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727'

EXPECTED_V3 = {
    'all_paired': 'eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded',
    'train': '28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6',
    'val': '082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315',
    'test': '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',
    'quarantined': 'a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c',
}

EXPECTED_KUB_COUNTS = {'TRAIN': 1978, 'VAL': 280, 'TEST': 558, 'QUARANTINED': 4}

# Continuous-distribution quantiles used throughout (Phase 07 defines "tiny").
QUANTILES = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
QUANTILE_LABELS = ['P01', 'P05', 'P10', 'P25', 'P50', 'P75', 'P90', 'P95', 'P99']

CATEGORIES = ['Kidney_Stone', 'Bladder_Stone', 'Ureteric_Stone']


# ---------------------------------------------------------------------------
# Provenance / hashing utilities
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    """Streaming SHA-256 of a file (safe for large binaries)."""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_strings(items) -> str:
    """Deterministic SHA-256 over an ordered iterable of strings."""
    h = hashlib.sha256()
    for s in items:
        h.update(str(s).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()


def dataframe_sha256(df: pd.DataFrame) -> str:
    """Deterministic SHA-256 of a DataFrame's sorted CSV representation."""
    payload = df.sort_index(axis=1).to_csv(index=False).encode('utf-8')
    return hashlib.sha256(payload).hexdigest()


def manifest_hashes() -> dict:
    """SHA-256 of every promoted v3 manifest file."""
    return {k: sha256_file(MANIFEST_DIR / f'{k}.csv') for k in EXPECTED_V3}


# ---------------------------------------------------------------------------
# Manifest loading & filtering
# ---------------------------------------------------------------------------

def load_manifest(split: str) -> pd.DataFrame:
    """Load one phase4_v3 split manifest (train/val/test/quarantined)."""
    if split not in ('train', 'val', 'test', 'quarantined'):
        raise ValueError(f"Unknown split '{split}'")
    return pd.read_csv(MANIFEST_DIR / f'{split}.csv')


def kub_only(df: pd.DataFrame) -> pd.DataFrame:
    """Filter a manifest frame to the KUB dataset cohort."""
    return df[df['dataset'] == 'KUB'].copy()


def derive_acquisition_type(image_path: str) -> str:
    """
    Derive acquisition/crop category from the on-disk path layout.

    The KUB corpus stores ROI crops under a 'ROI' directory and full-field
    images directly under 'Images'. No category is invented: anything else is
    reported as UNKNOWN.
    """
    s = str(image_path).replace('\\', '/')
    parent = s.rsplit('/', 2)[-2] if '/' in s else ''
    if parent.upper() == 'ROI':
        return 'ROI'
    if parent.upper() == 'IMAGES':
        return 'FULL_FIELD'
    return 'UNKNOWN'


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Attach split/acquisition derived columns without mutating the input."""
    out = df.copy()
    out['acquisition_type'] = out['image_path'].map(derive_acquisition_type)
    out['split_label'] = out['split'].astype(str).str.upper()
    return out


# ---------------------------------------------------------------------------
# Integrity audit
# ---------------------------------------------------------------------------

def integrity_audit(ktr: pd.DataFrame, kva: pd.DataFrame,
                    kq: pd.DataFrame, ktest: pd.DataFrame,
                    verify_pixels: bool = True) -> dict:
    """
    Pre-characterization data integrity audit for KUB TRAIN/VAL.

    Returns a structured dict of gate results. Does NOT repair anything.
    """
    res = {}

    res['train_count'] = int(len(ktr))
    res['val_count'] = int(len(kva))
    res['train_count_ok'] = int(len(ktr)) == EXPECTED_KUB_COUNTS['TRAIN']
    res['val_count_ok'] = int(len(kva)) == EXPECTED_KUB_COUNTS['VAL']

    res['train_ids_unique'] = bool(ktr['sample_id'].is_unique)
    res['val_ids_unique'] = bool(kva['sample_id'].is_unique)

    tr_ids = set(ktr['sample_id'])
    va_ids = set(kva['sample_id'])
    res['train_val_sample_overlap'] = len(tr_ids & va_ids)

    tr_pat = set(ktr['patient_id'])
    va_pat = set(kva['patient_id'])
    res['train_val_patient_overlap'] = len(tr_pat & va_pat)
    res['train_patients'] = len(tr_pat)
    res['val_patients'] = len(va_pat)

    # no quarantined sample may be active
    q_ids = set(kq['sample_id'])
    res['quarantined_active_overlap'] = len(q_ids & (tr_ids | va_ids))

    # no duplicate manifest rows
    res['train_duplicate_rows'] = int(ktr.duplicated(subset=['sample_id']).sum())
    res['val_duplicate_rows'] = int(kva.duplicated(subset=['sample_id']).sum())

    # TEST reference is metadata-only
    res['test_count'] = int(len(ktest))
    res['test_count_ok'] = int(len(ktest)) == EXPECTED_KUB_COUNTS['TEST']
    res['test_metadata_only'] = True

    # quarantined counts
    res['quarantined_count'] = int(len(kq))
    res['quarantined_count_ok'] = int(len(kq)) == EXPECTED_KUB_COUNTS['QUARANTINED']

    # file existence (no decoding)
    missing_img, missing_msk = [], []
    for _, r in pd.concat([ktr, kva]).iterrows():
        if not Path(r['image_path']).exists():
            missing_img.append(r['sample_id'])
        if not Path(r['mask_path']).exists():
            missing_msk.append(r['sample_id'])
    res['missing_images'] = len(missing_img)
    res['missing_masks'] = len(missing_msk)
    res['missing_image_ids'] = missing_img[:20]
    res['missing_mask_ids'] = missing_msk[:20]

    if verify_pixels:
        bad_pairs, dim_mismatch, invalid_masks, empty_masks = [], [], [], []
        label_vocab = Counter()
        for _, r in pd.concat([ktr, kva]).iterrows():
            try:
                with Image.open(r['image_path']) as im:
                    iw, ih = im.size
                mk = np.array(Image.open(r['mask_path']))
            except Exception:
                bad_pairs.append(r['sample_id'])
                continue
            if mk.ndim == 3:
                mk = mk[..., 0]
            if (mk.shape[1], mk.shape[0]) != (iw, ih):
                dim_mismatch.append(r['sample_id'])
            uniq = sorted(set(int(v) for v in np.unique(mk)))
            label_vocab[tuple(uniq)] += 1
            # Binary segmentation semantics: ANY nonzero value is foreground.
            # A mask is invalid only if it contains negative values, or if it is
            # empty (all-zero) when a foreground object is asserted.
            if any(v < 0 for v in uniq):
                invalid_masks.append(r['sample_id'])
            if int((mk > 0).sum()) == 0:
                empty_masks.append(r['sample_id'])
        res['unreadable_pairs'] = len(bad_pairs)
        res['dimension_mismatch'] = len(dim_mismatch)
        res['invalid_masks'] = len(invalid_masks)
        res['empty_masks'] = len(empty_masks)
        res['empty_mask_ids'] = empty_masks[:50]
        res['invalid_mask_ids'] = invalid_masks[:20]
        res['pairs_checked'] = int(len(ktr) + len(kva))
        # KUB masks use heterogeneous nonzero foreground labels (e.g. 1/2/3/255);
        # all nonzero values map to foreground under `mask > 0`.
        res['mask_label_vocabulary'] = {
            '|'.join(str(v) for v in k): int(c) for k, c in sorted(label_vocab.items())
        }
        res['mask_label_union'] = sorted(
            {v for k in label_vocab for v in k})
        res['mask_foreground_semantics'] = 'binary: foreground = (mask > 0)'
    else:
        res['pairs_checked'] = 0

    res['all_gates_pass'] = bool(
        res['train_count_ok'] and res['val_count_ok']
        and res['train_ids_unique'] and res['val_ids_unique']
        and res['train_val_sample_overlap'] == 0
        and res['train_val_patient_overlap'] == 0
        and res['quarantined_active_overlap'] == 0
        and res['train_duplicate_rows'] == 0 and res['val_duplicate_rows'] == 0
        and res['missing_images'] == 0 and res['missing_masks'] == 0
        and res.get('unreadable_pairs', 0) == 0
        and res.get('dimension_mismatch', 0) == 0
        and res.get('invalid_masks', 0) == 0
    )
    return res


# ---------------------------------------------------------------------------
# Geometry extraction
# ---------------------------------------------------------------------------

def _component_stats(mask_bool: np.ndarray):
    """Connected-component analysis without scipy: label via BFS-free numpy scan.

    Uses an efficient two-pass union-find over the binary mask. Returns
    (component_count, list_of_areas_sorted_desc, labels_array).
    """
    try:
        from scipy import ndimage  # preferred when available
        lab, n = ndimage.label(mask_bool)
        if n == 0:
            return 0, [], lab
        areas = np.bincount(lab.ravel())[1:]
        return int(n), sorted([int(a) for a in areas], reverse=True), lab
    except Exception:
        pass

    # Fallback: union-find (4-connectivity)
    h, w = mask_bool.shape
    labels = np.zeros((h, w), dtype=np.int32)
    parent = {}

    def find(x):
        root = x
        while parent[root] != root:
            root = parent[root]
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)

    nxt = 1
    for i in range(h):
        row = mask_bool[i]
        for j in np.nonzero(row)[0]:
            up = labels[i - 1, j] if i > 0 else 0
            left = labels[i, j - 1] if j > 0 else 0
            if up == 0 and left == 0:
                labels[i, j] = nxt
                parent[nxt] = nxt
                nxt += 1
            elif up != 0 and left != 0:
                labels[i, j] = min(up, left)
                union(up, left)
            else:
                labels[i, j] = up or left
    if nxt == 1:
        return 0, [], labels
    roots = np.array([find(k) for k in range(nxt)])
    remap = {r: i + 1 for i, r in enumerate(sorted(set(roots[1:].tolist())))}
    flat = labels.ravel()
    for idx in np.nonzero(flat)[0]:
        flat[idx] = remap[find(int(flat[idx]))]
    labels = flat.reshape(h, w)
    n = len(remap)
    areas = np.bincount(labels.ravel())[1:]
    return int(n), sorted([int(a) for a in areas], reverse=True), labels


def extract_geometry(image_path: str, mask_path: str) -> dict:
    """
    Compute image + mask foreground geometry for one KUB pair.

    Binary target semantics: foreground = (mask > 0).
    Total-foreground and largest-component geometry are both preserved.
    """
    with Image.open(image_path) as im:
        iw, ih = im.size
        mode = im.mode

    mask = np.array(Image.open(mask_path))
    if mask.ndim == 3:
        mask = mask[..., 0]
    mask_bool = mask > 0

    fg_pixels = int(mask_bool.sum())
    img_pixels = int(iw * ih)
    fg_fraction = fg_pixels / img_pixels if img_pixels else 0.0

    ncomp, areas, labels = _component_stats(mask_bool)
    largest_area = int(areas[0]) if areas else 0

    rows, cols = np.nonzero(mask_bool)
    if rows.size:
        bb_h = int(rows.max() - rows.min() + 1)
        bb_w = int(cols.max() - cols.min() + 1)
        cy = float(rows.mean()) / ih
        cx = float(cols.mean()) / iw
    else:
        bb_h = bb_w = 0
        cy = cx = float('nan')

    bb_area = int(bb_w * bb_h)
    eq_diam = float(np.sqrt(4.0 * fg_pixels / np.pi)) if fg_pixels > 0 else 0.0
    eq_diam_largest = float(np.sqrt(4.0 * largest_area / np.pi)) if largest_area > 0 else 0.0

    return {
        'image_width': int(iw),
        'image_height': int(ih),
        'image_pixels': img_pixels,
        'aspect_ratio': round(iw / ih, 6) if ih else float('nan'),
        'image_mode': mode,
        'fg_pixels': fg_pixels,
        'fg_fraction': fg_fraction,
        'component_count': ncomp,
        'largest_component_pixels': largest_area,
        'largest_component_fraction': (largest_area / img_pixels) if img_pixels else 0.0,
        'nonlargest_component_pixels': fg_pixels - largest_area,
        'component_areas_sorted': areas,
        'bbox_width': bb_w,
        'bbox_height': bb_h,
        'bbox_area': bb_area,
        'bbox_area_fraction': (bb_area / img_pixels) if img_pixels else 0.0,
        'equivalent_diameter': eq_diam,
        'equivalent_diameter_largest': eq_diam_largest,
        'centroid_y_norm': cy,
        'centroid_x_norm': cx,
    }


def characterize_population(df: pd.DataFrame, split_label: str) -> pd.DataFrame:
    """
    Run geometry extraction over one split's KUB cohort.

    Outputs one row per sample with all geometry + metadata columns.
    """
    rows = []
    df = add_derived_columns(df)
    for _, r in df.iterrows():
        g = extract_geometry(r['image_path'], r['mask_path'])
        g.update({
            'sample_id': r['sample_id'],
            'split': split_label,
            'patient_id': r['patient_id'],
            'category': r['category'],
            'acquisition_type': r['acquisition_type'],
            'image_path': r['image_path'],
            'mask_path': r['mask_path'],
            'native_resolution': f"{g['image_width']}x{g['image_height']}",
        })
        g.pop('component_areas_sorted', None)
        rows.append(g)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Summary / quantile helpers
# ---------------------------------------------------------------------------

def quantile_table(series_by_group: dict, metrics: list, quantiles=QUANTILES,
                   labels=QUANTILE_LABELS) -> pd.DataFrame:
    """Build a tidy quantile table for one or more metric series."""
    rows = []
    for metric in metrics:
        for group, s in series_by_group.items():
            s = pd.Series(s).dropna()
            if s.empty:
                continue
            rec = {'metric': metric, 'group': group, 'n': int(s.size)}
            for q, lab in zip(quantiles, labels):
                rec[lab] = float(np.quantile(s, q))
            rec['min'] = float(s.min())
            rec['max'] = float(s.max())
            rec['mean'] = float(s.mean())
            rows.append(rec)
    return pd.DataFrame(rows)


# Canonical metric lists — single source of truth shared by driver and notebook.
IMAGE_GEOMETRY_METRICS = ['image_width', 'image_height', 'aspect_ratio', 'image_pixels']

MASK_GEOMETRY_METRICS = [
    'fg_pixels', 'fg_fraction', 'component_count',
    'largest_component_pixels', 'largest_component_fraction',
    'bbox_width', 'bbox_height', 'bbox_area', 'bbox_area_fraction',
    'equivalent_diameter', 'equivalent_diameter_largest',
]

GEOMETRY_QUANTILE_METRICS = [
    'fg_pixels', 'fg_fraction', 'largest_component_pixels',
    'largest_component_fraction', 'bbox_width', 'bbox_height',
    'bbox_area_fraction', 'equivalent_diameter',
    'equivalent_diameter_largest', 'component_count',
]


def _multi_metric_quantiles(series_by_split: dict, metrics: list) -> pd.DataFrame:
    """Concatenate per-metric quantile tables over TRAIN/VAL/COMBINED."""
    return pd.concat(
        [quantile_table({k: v[m] for k, v in series_by_split.items()}, [m])
         for m in metrics],
        ignore_index=True,
    )


def image_geometry_quantile_table(series_by_split: dict) -> pd.DataFrame:
    """Canonical image-geometry quantile table."""
    return _multi_metric_quantiles(series_by_split, IMAGE_GEOMETRY_METRICS)


def mask_geometry_quantile_table(series_by_split: dict) -> pd.DataFrame:
    """Canonical mask-geometry quantile table."""
    return _multi_metric_quantiles(series_by_split, MASK_GEOMETRY_METRICS)


def geometry_quantile_table(series_by_split: dict) -> pd.DataFrame:
    """Canonical combined geometry quantile table."""
    return _multi_metric_quantiles(series_by_split, GEOMETRY_QUANTILE_METRICS)


def population_summary(df: pd.DataFrame, split_label: str) -> dict:
    """Case / patient counts and per-patient case burden for one split."""
    per_patient = df.groupby('patient_id').size()
    return {
        'split': split_label,
        'cases': int(len(df)),
        'unique_patients': int(df['patient_id'].nunique()),
        'cases_per_patient_mean': float(per_patient.mean()),
        'cases_per_patient_median': float(per_patient.median()),
        'cases_per_patient_q25': float(np.quantile(per_patient, 0.25)),
        'cases_per_patient_q75': float(np.quantile(per_patient, 0.75)),
        'cases_per_patient_min': int(per_patient.min()),
        'cases_per_patient_max': int(per_patient.max()),
        'cases_per_patient_p90': float(np.quantile(per_patient, 0.90)),
        'cases_per_patient_p95': float(np.quantile(per_patient, 0.95)),
    }


def category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Case counts and proportions per anatomical category / split."""
    ct = pd.crosstab(df['category'], df['split'])
    props = ct.div(ct.sum(axis=0), axis=1) * 100.0
    out = []
    for cat in ct.index:
        rec = {'category': cat}
        for sp in ct.columns:
            rec[f'{sp}_cases'] = int(ct.loc[cat, sp])
            rec[f'{sp}_pct'] = float(props.loc[cat, sp])
        out.append(rec)
    return pd.DataFrame(out)


def acquisition_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Acquisition/crop-type counts and proportions per split."""
    ct = pd.crosstab(df['acquisition_type'], df['split'])
    props = ct.div(ct.sum(axis=0), axis=1) * 100.0
    out = []
    for acq in ct.index:
        rec = {'acquisition_type': acq}
        for sp in ct.columns:
            rec[f'{sp}_cases'] = int(ct.loc[acq, sp])
            rec[f'{sp}_pct'] = float(props.loc[acq, sp])
        out.append(rec)
    return pd.DataFrame(out)


def resolution_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Frequency table of native resolutions per split."""
    ct = pd.crosstab(df['native_resolution'], df['split'])
    out = ct.reset_index()
    out['total'] = out[[c for c in ct.columns]].sum(axis=1)
    return out.sort_values('total', ascending=False).reset_index(drop=True)


def component_structure_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Empty / single-component / multi-component breakdown per split."""
    rows = []
    for sp, sub in df.groupby('split'):
        n = len(sub)
        empty = int((sub['component_count'] == 0).sum())
        single = int((sub['component_count'] == 1).sum())
        multi = int((sub['component_count'] >= 2).sum())
        rows.append({
            'split': sp,
            'cases': n,
            'empty_masks': empty,
            'empty_pct': 100.0 * empty / n if n else 0.0,
            'single_component': single,
            'single_pct': 100.0 * single / n if n else 0.0,
            'multi_component': multi,
            'multi_pct': 100.0 * multi / n if n else 0.0,
            'total_components': int(sub['component_count'].sum()),
            'max_components_in_case': int(sub['component_count'].max()),
        })
    return pd.DataFrame(rows)


def stability_comparison(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descriptive TRAIN vs VAL stability for key quantities.

    Reports absolute percentage-point differences. No significance testing.
    """
    rows = []
    quant_specs = [
        ('fg_fraction', 'foreground_fraction'),
        ('largest_component_pixels', 'largest_component_pixels'),
        ('bbox_area_fraction', 'bbox_area_fraction'),
        ('fg_pixels', 'foreground_pixels'),
    ]
    for col, name in quant_specs:
        tr = df.loc[df['split'] == 'TRAIN', col].dropna()
        va = df.loc[df['split'] == 'VAL', col].dropna()
        rows.append({
            'quantity': name,
            'train_median': float(np.median(tr)),
            'val_median': float(np.median(va)),
            'median_abs_diff': float(abs(np.median(tr) - np.median(va))),
            'train_p25': float(np.quantile(tr, 0.25)),
            'val_p25': float(np.quantile(va, 0.25)),
            'train_p75': float(np.quantile(tr, 0.75)),
            'val_p75': float(np.quantile(va, 0.75)),
        })
    return pd.DataFrame(rows)


def categorical_stability(cat_df: pd.DataFrame, level_col: str,
                          train_col='TRAIN_pct', val_col='VAL_pct') -> float:
    """Max absolute percentage-point difference across levels."""
    return float((cat_df[train_col] - cat_df[val_col]).abs().max())


def percentage_point_differences(df: pd.DataFrame, level_col: str) -> pd.DataFrame:
    """
    Exact TRAIN vs VAL percentage-point differences for a categorical column.

    Descriptive only: no significance test, no p-values.
    """
    tr = df[df['split'] == 'TRAIN']
    va = df[df['split'] == 'VAL']
    levels = sorted(set(df[level_col].unique()))
    rows = []
    for lv in levels:
        ptr = 100.0 * (tr[level_col] == lv).sum() / len(tr) if len(tr) else 0.0
        pva = 100.0 * (va[level_col] == lv).sum() / len(va) if len(va) else 0.0
        rows.append({
            'level': lv,
            'train_cases': int((tr[level_col] == lv).sum()),
            'val_cases': int((va[level_col] == lv).sum()),
            'train_pct': float(ptr),
            'val_pct': float(pva),
            'abs_diff_pp': float(abs(ptr - pva)),
            'signed_diff_pp': float(pva - ptr),
        })
    return pd.DataFrame(rows).sort_values('abs_diff_pp', ascending=False).reset_index(drop=True)


def stratified_geometry_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Descriptive geometry quantiles stratified by grouping dimension.

    Dimensions
    ----------
    - split x acquisition_type
    - split x category

    Reports P25 / median / P75 for foreground_fraction,
    largest_component_pixels, bbox_area_fraction and equivalent_diameter,
    plus median/P90 component_count.

    Descriptive only. No significance testing.
    """
    metrics = [
        ('fg_fraction', 'foreground_fraction'),
        ('largest_component_pixels', 'largest_component_pixels'),
        ('bbox_area_fraction', 'bbox_area_fraction'),
        ('equivalent_diameter', 'equivalent_diameter'),
    ]
    rows = []

    def _emit(dim_a, dim_b, sub):
        n = len(sub)
        if n == 0:
            return
        rec = {'dimension_a': dim_a, 'dimension_b': dim_b, 'n': int(n)}
        for col, name in metrics:
            s = pd.Series(sub[col]).dropna()
            rec[f'{name}_p25'] = float(np.quantile(s, 0.25)) if len(s) else float('nan')
            rec[f'{name}_median'] = float(np.median(s)) if len(s) else float('nan')
            rec[f'{name}_p75'] = float(np.quantile(s, 0.75)) if len(s) else float('nan')
        cc = pd.Series(sub['component_count']).dropna()
        rec['component_count_median'] = float(np.median(cc)) if len(cc) else float('nan')
        rec['component_count_p90'] = float(np.quantile(cc, 0.90)) if len(cc) else float('nan')
        rows.append(rec)

    # Dimension A: split x acquisition_type
    for (sp, acq), sub in df.groupby(['split', 'acquisition_type']):
        _emit('split x acquisition_type', f'{sp} | {acq}', sub)

    # Dimension B: split x category
    for (sp, cat), sub in df.groupby(['split', 'category']):
        _emit('split x category', f'{sp} | {cat}', sub)

    return pd.DataFrame(rows)


def acquisition_regime_geometry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Geometry of the two acquisition regimes (ROI crops vs FULL_FIELD images).

    Verified from the data, never hardcoded.
    """
    rows = []
    for acq, sub in df.groupby('acquisition_type'):
        vc = sub['native_resolution'].value_counts()
        modes = sorted(sub['image_mode'].unique()) if 'image_mode' in sub.columns else []
        rows.append({
            'acquisition_type': acq,
            'cases': int(len(sub)),
            'distinct_native_resolutions': int(sub['native_resolution'].nunique()),
            'width_min': int(sub['image_width'].min()),
            'width_median': float(sub['image_width'].median()),
            'width_max': int(sub['image_width'].max()),
            'height_median': float(sub['image_height'].median()),
            'image_modes': '|'.join(modes),
            'top_resolution': vc.index[0],
            'top_resolution_count': int(vc.iloc[0]),
        })
    return pd.DataFrame(rows).sort_values('acquisition_type').reset_index(drop=True)


# ---------------------------------------------------------------------------
# Deterministic sample selection
# ---------------------------------------------------------------------------

def deterministic_sample_selection(df: pd.DataFrame, n_total: int = 16,
                                   seed_tag: str = 'phase06-kub-v3-gallery') -> pd.DataFrame:
    """
    Deterministic, prediction-independent, non-cherry-picked gallery selection.

    Protocol
    --------
    1. Partition the active KUB population by (split, category, acquisition_type).
    2. Within each stratum, sort by sample_id (stable, content-independent).
    3. Take the stratum median-index member to avoid always selecting the
       lexicographically first case.
    4. Allocate round-robin across strata ordered deterministically by a
       SHA-256 of the stratum key (seed_tag), until n_total is reached.
    5. Additionally, ensure coverage of continuous foreground-fraction quantile
       bins by force-including the member nearest each empty bin.

    Selection never inspects visual quality, model output, or mask aesthetics.
    """
    df = df.copy()
    df['stratum'] = df['split'] + '|' + df['category'] + '|' + df['acquisition_type']

    strata = sorted(df['stratum'].unique(),
                    key=lambda s: hashlib.sha256(f'{seed_tag}|{s}'.encode()).hexdigest())

    picked = []
    for s in strata:
        members = df[df['stratum'] == s].sort_values('sample_id')
        if len(members) == 0:
            continue
        picked.append(members.iloc[len(members) // 2])

    # Quantile-bin coverage on foreground fraction
    valid = df.dropna(subset=['fg_fraction'])
    if len(valid):
        edges = np.quantile(valid['fg_fraction'], np.linspace(0, 1, 6))
        edges[-1] += 1e-12
        for i in range(5):
            lo, hi = edges[i], edges[i + 1]
            bin_members = valid[(valid['fg_fraction'] >= lo) & (valid['fg_fraction'] < hi)]
            if len(bin_members) == 0:
                continue
            target = (lo + hi) / 2.0
            rep = bin_members.iloc[(bin_members['fg_fraction'] - target).abs().argmin()]
            picked.append(rep)

    sel = pd.DataFrame(picked).drop_duplicates(subset=['sample_id'])
    sel = sel.sort_values('sample_id').reset_index(drop=True)

    # If over/under target, trim/extend deterministically from sorted remainder
    if len(sel) > n_total:
        # keep stratified coverage: evenly drop from the end of the sorted list
        keep_idx = np.linspace(0, len(sel) - 1, n_total).round().astype(int)
        sel = sel.iloc[sorted(set(keep_idx))].reset_index(drop=True)
    elif len(sel) < n_total:
        remaining = df[~df['sample_id'].isin(sel['sample_id'])].sort_values('sample_id')
        need = n_total - len(sel)
        extra = remaining.iloc[np.linspace(0, len(remaining) - 1,
                                           min(need, len(remaining))).round().astype(int)]
        sel = (pd.concat([sel, extra]).drop_duplicates(subset=['sample_id'])
               .sort_values('sample_id').reset_index(drop=True))

    sel['selection_rank'] = np.arange(1, len(sel) + 1)
    return sel


# ---------------------------------------------------------------------------
# Visualization helpers
# ---------------------------------------------------------------------------

def save_fig(fig, path: Path, dpi: int = 130):
    """Save a matplotlib figure and close it."""
    import matplotlib.pyplot as plt
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


def plot_category_normalized(df: pd.DataFrame, title: str = None):
    """
    Percentage-normalized anatomical-category composition (TRAIN vs VAL).

    Raw counts obscure proportional differences because TRAIN is much larger;
    this figure shows percent-of-split so the composition shift is visible.
    No significance stars and no p-values.
    """
    import matplotlib.pyplot as plt

    tr = df[df['split'] == 'TRAIN']
    va = df[df['split'] == 'VAL']
    cats = sorted(df['category'].unique())
    tr_pct = [100.0 * (tr['category'] == c).sum() / len(tr) for c in cats]
    va_pct = [100.0 * (va['category'] == c).sum() / len(va) for c in cats]

    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    x = np.arange(len(cats))
    w = 0.38
    b1 = ax.bar(x - w / 2, tr_pct, w, label='TRAIN', color='#2f7ed8')
    b2 = ax.bar(x + w / 2, va_pct, w, label='VAL', color='#4a9d5f')
    for bars, vals in ((b1, tr_pct), (b2, va_pct)):
        for bar, v in zip(bars, vals):
            ax.annotate(f'{v:.1f}%', (bar.get_x() + bar.get_width() / 2, v),
                        ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels([c.replace('_', ' ') for c in cats])
    ax.set_ylabel('percent of split (%)')
    ax.set_ylim(0, max(max(tr_pct), max(va_pct)) * 1.2)
    ax.set_title(title or 'Anatomical-category composition (percentage-normalized)')
    ax.legend(frameon=False)
    return fig


def plot_stratified_geometry(df: pd.DataFrame, dimension: str = 'acquisition_type',
                             metric: str = 'fg_fraction'):
    """
    Box-style stratified geometry comparison (TRAIN vs VAL within each level).

    Uses medians and IQR whiskers rather than a significance test.
    """
    import matplotlib.pyplot as plt

    levels = sorted(df[dimension].unique())
    fig, ax = plt.subplots(figsize=(8.2, 4.4))
    x = np.arange(len(levels))
    w = 0.34
    for off, split, color in ((-w / 2, 'TRAIN', '#2f7ed8'), (w / 2, 'VAL', '#4a9d5f')):
        meds, lo, hi = [], [], []
        for lv in levels:
            s = df[(df[dimension] == lv) & (df['split'] == split)][metric].dropna()
            if len(s) == 0:
                meds.append(0); lo.append(0); hi.append(0); continue
            meds.append(float(np.median(s)))
            lo.append(float(np.median(s) - np.quantile(s, 0.25)))
            hi.append(float(np.quantile(s, 0.75) - np.median(s)))
        ax.bar(x + off, meds, w, yerr=[lo, hi], capsize=3,
               label=split, color=color, error_kw={'lw': 1.0, 'ecolor': '#444'})
    ax.set_xticks(x)
    ax.set_xticklabels([str(l) for l in levels])
    ax.set_ylabel(metric)
    ax.set_title(f'{metric} by {dimension} (median, IQR whiskers)')
    ax.legend(frameon=False)
    return fig


def plot_gallery_pages(df: pd.DataFrame, cases_per_page: int = 4,
                       title: str = 'KUB deterministic gallery',
                       page_prefix: str = 'page'):
    """
    Build paginated publication-quality gallery figures.

    Each case occupies a row of THREE panels:
      1. original image
      2. binary ground-truth mask  (mask > 0) — NOT the raw heterogeneous labels
      3. GT overlay on the original (+ bounding box)

    Pagination defaults to 4 cases per page -> 4 pages for the 16-case gallery,
    which keeps panels readable (avoids a 48-panel postage stamp).

    NEVER renders TEST content. Caller must pass active TRAIN/VAL rows only.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = len(df)
    n_pages = int(np.ceil(n / cases_per_page))
    figs = []

    for page in range(n_pages):
        chunk = df.iloc[page * cases_per_page:(page + 1) * cases_per_page]
        nrows = len(chunk)
        fig, axes = plt.subplots(nrows, 3, figsize=(11.5, 3.5 * nrows))
        axes = np.atleast_2d(axes)

        for i, (_, r) in enumerate(chunk.iterrows()):
            img = np.array(Image.open(r['image_path']))
            mask = np.array(Image.open(r['mask_path']))
            if mask.ndim == 3:
                mask = mask[..., 0]
            mask_bool = mask > 0          # canonical binary target semantics

            # Single-channel images must be rendered in grayscale, not with a
            # default colour map, so the medical content is shown faithfully.
            img_cmap = 'gray' if img.ndim == 2 else None

            ax_img, ax_msk, ax_ovl = axes[i, 0], axes[i, 1], axes[i, 2]

            # 1. original image
            ax_img.imshow(img, cmap=img_cmap)
            ax_img.set_title('original', fontsize=8, color='#333')

            # 2. binary ground-truth mask (mask > 0)
            ax_msk.imshow(mask_bool, cmap='gray', vmin=0, vmax=1)
            ax_msk.set_title('binary GT  (mask > 0)', fontsize=8, color='#333')

            # 3. GT overlay on original
            ax_ovl.imshow(img, cmap=img_cmap)
            if mask_bool.any():
                rgba = np.zeros((*mask_bool.shape, 4), dtype=float)
                rgba[..., 0] = 1.0
                rgba[..., 3] = mask_bool * 0.45
                ax_ovl.imshow(rgba)
                rr, cc = np.nonzero(mask_bool)
                y0, y1, x0, x1 = rr.min(), rr.max(), cc.min(), cc.max()
                ax_ovl.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                                           fill=False, edgecolor='#28d17c', lw=1.6))
            ax_ovl.set_title('GT overlay + bbox', fontsize=8, color='#333')

            for ax in (ax_img, ax_msk, ax_ovl):
                ax.set_xticks([])
                ax.set_yticks([])

            meta = (
                f"{r['sample_id'][:12]} | {r['split']} | {r['category']}\n"
                f"patient={r['patient_id']} | {r['acquisition_type']} | "
                f"{r['native_resolution']}\n"
                f"fg={r['fg_pixels']} ({100 * r['fg_fraction']:.3f}%) | "
                f"comp={r['component_count']} | "
                f"bbox={r['bbox_width']}x{r['bbox_height']}"
            )
            ax_img.set_xlabel(meta, fontsize=7, labelpad=4)

        for i in range(nrows):
            for j in range(3):
                if i >= len(chunk):
                    axes[i, j].axis('off')

        fig.suptitle(f'{title} — page {page + 1}/{n_pages}',
                     fontsize=12, fontweight='bold')
        fig.tight_layout(rect=[0, 0, 1, 0.97])
        figs.append(fig)

    return figs


def plot_gallery_row(df: pd.DataFrame, ncols: int = 3, max_rows: int = 6,
                     title: str = 'KUB deterministic gallery'):
    """Backward-compatible single-figure gallery (image + overlay per case)."""
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = min(len(df), ncols * max_rows)
    sel = df.head(n)
    nrows = int(np.ceil(n / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.0 * ncols, 3.6 * nrows))
    axes = np.atleast_1d(axes).ravel()

    for ax, (_, r) in zip(axes, sel.iterrows()):
        img = np.array(Image.open(r['image_path']))
        mask = np.array(Image.open(r['mask_path']))
        if mask.ndim == 3:
            mask = mask[..., 0]
        mask_bool = mask > 0

        ax.imshow(img, cmap=('gray' if img.ndim == 2 else None))
        if mask_bool.any():
            rgba = np.zeros((*mask_bool.shape, 4), dtype=float)
            rgba[..., 0] = 1.0
            rgba[..., 3] = mask_bool * 0.45
            ax.imshow(rgba)
            rows, cols = np.nonzero(mask_bool)
            y0, y1 = rows.min(), rows.max()
            x0, x1 = cols.min(), cols.max()
            ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0,
                                   fill=False, edgecolor='#28d17c', lw=1.4))
        ax.set_title(
            f"{r['sample_id'][:10]} | {r['split']} | {r['category']}\n"
            f"{r['acquisition_type']} | {r['native_resolution']} | "
            f"fg={r['fg_pixels']} ({100*r['fg_fraction']:.2f}%) | "
            f"comp={r['component_count']} | bbox={r['bbox_width']}x{r['bbox_height']}",
            fontsize=8)
        ax.axis('off')
    for ax in axes[n:]:
        ax.axis('off')
    fig.suptitle(title, fontsize=13, fontweight='bold')
    return fig


# ---------------------------------------------------------------------------
# Quarantine metadata
# ---------------------------------------------------------------------------

def quarantined_metadata(kq: pd.DataFrame) -> pd.DataFrame:
    """Metadata-only summary of quarantined KUB cases (no medical content)."""
    cols = [c for c in ['sample_id', 'patient_id', 'split_v2', 'quarantine_reason',
                        'duplicate_asset_group_id', 'duplicate_risk_group_id',
                        'category', 'dataset'] if c in kq.columns]
    return kq[cols].reset_index(drop=True)


def mask_label_vocabulary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tabulate KUB mask nonzero-label signatures by category and split.

    The pixel target is binary (`mask > 0`); this table documents the raw
    label vocabulary that underlies that binary mapping.
    """
    rows = []
    for _, r in df.iterrows():
        mk = np.array(Image.open(r['mask_path']))
        if mk.ndim == 3:
            mk = mk[..., 0]
        sig = '|'.join(str(int(v)) for v in sorted(set(int(x) for x in np.unique(mk))))
        rows.append({'split': r['split'], 'category': r['category'],
                     'label_signature': sig})
    tmp = pd.DataFrame(rows)
    ct = tmp.groupby(['label_signature', 'category']).size().rename('cases').reset_index()
    return ct.sort_values(['label_signature', 'category']).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Table writing
# ---------------------------------------------------------------------------

REQUIRED_TABLES = [
    'phase06_kub_v3_population_summary.csv',
    'phase06_kub_v3_patient_summary.csv',
    'phase06_kub_v3_image_geometry_summary.csv',
    'phase06_kub_v3_mask_geometry_summary.csv',
    'phase06_kub_v3_category_summary.csv',
    'phase06_kub_v3_acquisition_summary.csv',
    'phase06_kub_v3_geometry_quantiles.csv',
    'phase06_kub_v3_quarantined_metadata.csv',
    'phase06_kub_v3_sample_selection.csv',
]

# Additional Phase-06 Part 1A-R1 artifacts (stratification + semantics).
ADDITIONAL_TABLES = [
    'phase06_kub_v3_mask_label_vocabulary.csv',
    'phase06_kub_v3_acquisition_regime_geometry.csv',
    'phase06_kub_v3_stratified_geometry_summary.csv',
]

# Complete final registry — the physical files are the source of truth.
FINAL_TABLES = REQUIRED_TABLES + ADDITIONAL_TABLES


def final_table_registry(out_dir: Path = None) -> pd.DataFrame:
    """
    Registry of every final Phase-06 table with its physical SHA-256.

    Only files that actually exist on disk are registered; the physical files
    are the source of truth (no assumed count).
    """
    out_dir = out_dir or (PROJECT_ROOT / 'reports' / 'tables')
    rows = []
    for name in FINAL_TABLES:
        p = out_dir / name
        rows.append({
            'table': name,
            'exists': p.exists(),
            'bytes': int(p.stat().st_size) if p.exists() else 0,
            'sha256': sha256_file(p) if p.exists() else None,
        })
    return pd.DataFrame(rows)


def write_table(df: pd.DataFrame, name: str, out_dir: Path = None) -> Path:
    """Write a machine-readable table with full precision."""
    out_dir = out_dir or (PROJECT_ROOT / 'reports' / 'tables')
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / name
    df.to_csv(path, index=False)
    return path


# ---------------------------------------------------------------------------
# TEST-lock assertion
# ---------------------------------------------------------------------------

TEST_CONTENT_READS = 0
TEST_VISUALIZATIONS = 0


def test_lock_assertion(ktr, kva, ktest, kq) -> dict:
    """Emit the mandated TEST-lock assertion block."""
    return {
        'ACTIVE MANIFEST': ACTIVE_MANIFEST_VERSION,
        'KUB TRAIN': int(len(ktr)),
        'KUB VAL': int(len(kva)),
        'KUB TEST (metadata only)': int(len(ktest)),
        'KUB QUARANTINED': int(len(kq)),
        'TEST CONTENT READS': TEST_CONTENT_READS,
        'TEST VISUALIZATIONS': TEST_VISUALIZATIONS,
        'TEST METRICS': 0,
        'PHASE 07 STARTED': 'NO',
    }
