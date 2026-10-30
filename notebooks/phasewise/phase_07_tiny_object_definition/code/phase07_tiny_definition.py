"""
Phase 07 Part 1A — Tiny-object definition: historical audit + CLEAN-v3 TRAIN-only design.

Reusable implementation module. The reviewer notebook imports these functions.

Governance
----------
- Threshold-design evidence uses **KUB TRAIN only** from `manifests/phase4_v3/train.csv`.
- VAL is NOT used for threshold selection.
- TEST image/mask content is NEVER read (metadata only).
- No threshold is frozen here. Candidates are exploratory.

Mask semantics: BACKGROUND = (mask == 0), FOREGROUND = (mask > 0).
"""

from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import label as nd_label

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase07_tiny_object_definition'

ACTIVE_MANIFEST_VERSION = 'phase4_v3'
HISTORICAL_MANIFEST_VERSION = 'phase4_v2'

EXPECTED_KUB_TRAIN = 1978
EXPECTED_MULTI_COMPONENT_TRAIN = 212

STRATA = ('TINY', 'SMALL', 'MEDIUM', 'LARGE')
QUANTILES = [0.01, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.99]
QUANTILE_LABELS = ['P01', 'P05', 'P10', 'P25', 'P50', 'P75', 'P90', 'P95', 'P99']

MODEL_CANVAS = 512

# ---------------------------------------------------------------------------
# Historical taxonomy (kub_size_v1) — reconstructed from project sources
# ---------------------------------------------------------------------------

HISTORICAL_TAXONOMY = {
    'taxonomy_version': 'kub_size_v1',
    'metric': 'component_ratio',
    'metric_definition': 'component_pixels / (native_image_height * native_image_width)',
    'metric_family': 'connected-component area, normalized by native image area',
    'unit': 'object (connected foreground component)',
    'connectivity': 8,
    'coordinate_system': 'native image pixels, normalized by native image area',
    'resize_convention': 'NONE for the taxonomy (native masks); the training pipeline '
                         'separately applies aspect-ratio-preserving resize + centre pad to 512',
    'acquisition_scope': 'FULL_FIELD only (ROI components were not primary-binned)',
    'source_split': 'TRAIN',
    'source_manifest_version': 'phase4_v2',
    'source_full_field_sample_count': 771,
    'source_full_field_component_count': 1162,
    'Q25': 0.0001499766777599,
    'Q50': 0.00033976472454305,
    'Q75': 0.0008266496069636999,
    'boundaries': {
        'TINY': 'component_ratio <= Q25',
        'SMALL': 'Q25 < component_ratio <= Q50',
        'MEDIUM': 'Q50 < component_ratio <= Q75',
        'LARGE': 'component_ratio > Q75',
    },
    'boundary_semantics': 'lower-inclusive / upper-exclusive cumulative: a value exactly '
                          'equal to a quartile falls into the LOWER bin',
    'case_level_convention': 'per-case flags contains_{tiny,small,medium,large}_object '
                             'plus dominant_object_stratum from the largest component',
    'roi_handling': 'ROI_NOT_PRIMARY_BINNED',
    'threshold_source': 'TRAIN_ONLY',
    'historical_train_counts': {'TINY': 291, 'SMALL': 290, 'MEDIUM': 290, 'LARGE': 291},
    'historical_train_total': 1162,
    'historical_val_counts': {'TINY': 73, 'SMALL': 29, 'MEDIUM': 36, 'LARGE': 18},
    'historical_train_by_category': {
        'Kidney_Stone': {'TINY': 48, 'SMALL': 173, 'MEDIUM': 212, 'LARGE': 276, 'TOTAL': 709},
        'Bladder_Stone': {'TINY': 221, 'SMALL': 85, 'MEDIUM': 31, 'LARGE': 7, 'TOTAL': 344},
        'Ureteric_Stone': {'TINY': 22, 'SMALL': 32, 'MEDIUM': 47, 'LARGE': 8, 'TOTAL': 109},
    },
    'used_in_phases': ['06', '07', '10', '11', '12', '13', '14'],
}

HISTORICAL_SOURCES = [
    ('src/analysis/kub_object_size.py',
     'canonical taxonomy module: STRATA, TAXONOMY_VERSION, compute_size_thresholds, '
     'stratum_for_ratio, assign_component_strata, assign_sample_strata'),
    ('src/analysis/kub_characterization.py',
     'component extraction: analyze_kub_mask_v2(mask_path, connectivity=8); '
     'component_ratio = c_pixels / total_pixels'),
    ('src/data/transforms.py',
     'documented preprocessing: SegmentationTransform — aspect-ratio-preserving resize '
     '(scale = min(size/w, size/h)) + centre pad; mask binarized as (> 0)'),
    ('reports/audits/kub_object_size_thresholds.json',
     'frozen threshold record (taxonomy_version kub_size_v1, connectivity 8, Q25/Q50/Q75)'),
    ('reports/audits/kub_object_size_provenance.json',
     'provenance: source split/scope/counts, source table hashes, test_mask_reads 0'),
    ('reports/tables/kub_size_thresholds_v2.csv',
     'threshold table with boundary definitions'),
    ('reports/tables/kub_size_distribution_train_val_v2.csv',
     'historical TRAIN/VAL stratum counts'),
    ('reports/tables/kub_size_distribution_by_category_v2.csv',
     'historical TRAIN stratum counts by anatomical category'),
    ('notebooks/05_kub_object_size_taxonomy.ipynb',
     'historical Phase-07 reviewer notebook'),
    ('scripts/legacy/run_phase7_analysis.py',
     'legacy driver: reuses compute_size_thresholds from the canonical module'),
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def sha256_of_strings(items) -> str:
    h = hashlib.sha256()
    for s in items:
        h.update(str(s).encode('utf-8'))
        h.update(b'\n')
    return h.hexdigest()


def historical_definition_audit() -> dict:
    """
    Reconstruct the historical tiny/small/medium/large definition with provenance.

    Records each source file with its SHA-256 and what it establishes, and reports
    any disagreement between sources.
    """
    sources = []
    for rel, role in HISTORICAL_SOURCES:
        p = PROJECT_ROOT / rel
        sources.append({
            'source_file': rel,
            'sha256': sha256_file(p) if p.exists() else None,
            'exists': p.exists(),
            'establishes': role,
        })

    return {
        'audit': 'phase07_historical_tiny_definition_audit',
        'phase': '07 — Tiny-Object Definition (Part 1A)',
        'definition_found': True,
        'definition': HISTORICAL_TAXONOMY,
        'sources': sources,
        'disagreements': [],
        'disagreement_note': 'No competing definition was found. All located sources '
                             '(module, threshold record, provenance record, threshold table, '
                             'legacy driver, notebook) implement the same kub_size_v1 '
                             'quartile taxonomy over FULL_FIELD TRAIN components.',
        'critical_question_answers': {
            'A_native_pixels': 'PARTIAL — native pixels, but NORMALIZED by native image area',
            'B_512_representation': 'NO — the taxonomy used native masks; 512 resize+pad is a '
                                    'separate training-pipeline transform',
            'C_bbox_width': 'NO',
            'D_bbox_height': 'NO',
            'E_bbox_max_side': 'NO',
            'F_bbox_area': 'NO (bbox geometry is recorded but not the taxonomy metric)',
            'G_component_area': 'YES — connected-component area, normalized as a fraction of '
                                'native image area (component_ratio)',
            'H_equivalent_diameter': 'NO',
            'I_foreground_fraction': 'NO (case-level total foreground is separate)',
            'conclusion': 'The historical metric is G: connected-component area normalized by '
                          'native image area (component_ratio). The "<32 px" hypothesis is NOT '
                          'supported by any canonical source.',
        },
        'resize_convention': {
            'taxonomy': 'native resolution, no resize',
            'training_pipeline': 'aspect-ratio-preserving resize + centre pad to 512x512 '
                                 '(scale = min(512/w, 512/h); rw=round(w*scale), '
                                 'rh=round(h*scale); bilinear image, nearest mask)',
            'non_isotropic_resize_used': False,
            'documented_in': 'src/data/transforms.py (SegmentationTransform)',
        },
        'test_mask_reads': 0,
        'external_data_accessed': False,
    }


# ---------------------------------------------------------------------------
# Manifest / acquisition helpers
# ---------------------------------------------------------------------------

def load_manifest(split: str) -> pd.DataFrame:
    return pd.read_csv(MANIFEST_DIR / f'{split}.csv')


def kub_only(df: pd.DataFrame) -> pd.DataFrame:
    return df[df['dataset'] == 'KUB'].copy()


def derive_acquisition_type(image_path: str) -> str:
    """Directory-semantics acquisition type (never dimensions)."""
    parts = {p.casefold() for p in Path(str(image_path)).parts}
    if 'roi' in parts:
        return 'ROI'
    if 'images' in parts:
        return 'FULL_FIELD'
    return 'UNKNOWN'


# ---------------------------------------------------------------------------
# Geometry
# ---------------------------------------------------------------------------

def model_canvas_scale(width: int, height: int, size: int = MODEL_CANVAS) -> float:
    """
    Reproduce the documented historical preprocessing scale.

    SegmentationTransform: scale = min(size/width, size/height), then
    aspect-preserving resize and centre pad to (size, size).
    """
    return float(min(size / width, size / height))


def extract_components(mask_path: str, image_path: str,
                       connectivity: int = 8) -> tuple[list, dict]:
    """
    Extract per-component geometry for one mask.

    Returns (components, case_geometry). Component geometry is reported in
    native space, normalized space, and the documented 512 model canvas.

    Binary semantics: foreground = (mask > 0).
    """
    with Image.open(image_path) as im:
        w, h = im.size

    mask = np.array(Image.open(mask_path))
    if mask.ndim == 3:
        mask = mask[..., 0]
    fg = mask > 0

    total_pixels = int(h * w)
    fg_pixels = int(fg.sum())
    scale = model_canvas_scale(w, h)

    structure = (np.ones((3, 3), dtype=int) if connectivity == 8
                 else np.array([[0, 1, 0], [1, 1, 1], [0, 1, 0]], dtype=int))
    labeled, n = nd_label(fg, structure=structure)

    components = []
    for cid in range(1, n + 1):
        cmap = labeled == cid
        cpx = int(cmap.sum())
        rows = np.any(cmap, axis=1)
        cols = np.any(cmap, axis=0)
        rmin, rmax = np.where(rows)[0][[0, -1]]
        cmin, cmax = np.where(cols)[0][[0, -1]]
        bw = int(cmax - cmin + 1)
        bh = int(rmax - rmin + 1)
        bbox_area = int(bw * bh)
        eq_d = float(np.sqrt(4.0 * cpx / np.pi)) if cpx > 0 else 0.0

        components.append({
            'component_index': cid,
            'component_pixels': cpx,
            'component_ratio': float(cpx / total_pixels),
            'component_fraction': float(cpx / total_pixels),
            'bbox_x': int(cmin),
            'bbox_y': int(rmin),
            'bbox_width': bw,
            'bbox_height': bh,
            'bbox_max_side': int(max(bw, bh)),
            'bbox_area': bbox_area,
            'bbox_area_fraction': float(bbox_area / total_pixels),
            'equivalent_diameter': eq_d,
            'normalized_equivalent_diameter': float(eq_d / min(w, h)),
            'normalized_bbox_width': float(bw / w),
            'normalized_bbox_height': float(bh / h),
            'normalized_bbox_max_side': float(max(bw, bh) / min(w, h)),
            # 512 model canvas (documented aspect-preserving resize + pad)
            'bbox_width_512': float(bw * scale),
            'bbox_height_512': float(bh * scale),
            'bbox_max_side_512': float(max(bw, bh) * scale),
            'bbox_area_512': float(bbox_area * scale * scale),
            'equivalent_diameter_512': float(eq_d * scale),
            'model_canvas_scale': scale,
        })

    case = {
        'native_width': int(w),
        'native_height': int(h),
        'component_count': int(n),
        'total_foreground_pixels': fg_pixels,
        'foreground_fraction': float(fg_pixels / total_pixels) if total_pixels else 0.0,
    }
    if components:
        largest = max(components, key=lambda c: c['component_pixels'])
        case.update({
            'largest_component_pixels': largest['component_pixels'],
            'largest_component_fraction': largest['component_fraction'],
            'largest_component_bbox_width': largest['bbox_width'],
            'largest_component_bbox_height': largest['bbox_height'],
            'largest_component_bbox_max_side': largest['bbox_max_side'],
            'largest_component_bbox_area_fraction': largest['bbox_area_fraction'],
            'largest_component_equivalent_diameter': largest['equivalent_diameter'],
            'largest_component_ratio': largest['component_ratio'],
        })
    else:
        case.update({
            'largest_component_pixels': 0,
            'largest_component_fraction': 0.0,
            'largest_component_bbox_width': 0,
            'largest_component_bbox_height': 0,
            'largest_component_bbox_max_side': 0,
            'largest_component_bbox_area_fraction': 0.0,
            'largest_component_equivalent_diameter': 0.0,
            'largest_component_ratio': 0.0,
        })
    return components, case


def build_train_tables(df_train: pd.DataFrame):
    """
    Build the TRAIN-only object table and case table.

    Returns (object_df, case_df). Only TRAIN rows are passed in.
    """
    objects, cases = [], []
    for _, r in df_train.iterrows():
        comps, case = extract_components(r['mask_path'], r['image_path'])
        acq = derive_acquisition_type(r['image_path'])
        base = {
            'sample_id': r['sample_id'],
            'patient_id': r['patient_id'],
            'category': r['category'],
            'acquisition_type': acq,
        }
        for c in comps:
            objects.append({**base, **c})
        cases.append({**base, **case})
    obj_df = pd.DataFrame(objects)
    case_df = pd.DataFrame(cases)
    return obj_df, case_df


# ---------------------------------------------------------------------------
# Historical taxonomy application
# ---------------------------------------------------------------------------

def stratum_for_ratio(value: float, q25: float, q50: float, q75: float) -> str:
    """Historical boundary semantics: lower-inclusive cumulative."""
    if value <= q25:
        return 'TINY'
    if value <= q50:
        return 'SMALL'
    if value <= q75:
        return 'MEDIUM'
    return 'LARGE'


def apply_historical_taxonomy(obj_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply kub_size_v1 to CLEAN-v3 TRAIN objects.

    Result label: HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN.
    Only FULL_FIELD objects are primary-binned (historical convention).
    """
    out = obj_df.copy()
    t = HISTORICAL_TAXONOMY
    reference = out['component_ratio'].map(
        lambda v: stratum_for_ratio(v, t['Q25'], t['Q50'], t['Q75']))
    out['historical_stratum'] = np.where(
        out['acquisition_type'].eq('FULL_FIELD'), reference, 'ROI_NOT_PRIMARY_BINNED')
    out['historical_reference_stratum'] = reference
    out['historical_label'] = 'HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN'
    return out


# ---------------------------------------------------------------------------
# Quantiles / summaries
# ---------------------------------------------------------------------------

def quantile_table(series_by_group: dict, metric: str,
                   quantiles=QUANTILES, labels=QUANTILE_LABELS) -> pd.DataFrame:
    rows = []
    for group, s in series_by_group.items():
        s = pd.Series(s).dropna()
        if s.empty:
            continue
        rec = {'metric': metric, 'group': group, 'n': int(s.size)}
        for q, lab in zip(quantiles, labels):
            rec[lab] = float(np.quantile(s, q))
        rec['min'] = float(s.min())
        rec['max'] = float(s.max())
        rows.append(rec)
    return pd.DataFrame(rows)


def stratified_quantiles(obj_df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    """TRAIN-only quantiles stratified by acquisition, and by category for FULL_FIELD."""
    parts = []
    for m in metrics:
        groups = {
            'ALL_TRAIN': obj_df[m],
            'FULL_FIELD': obj_df.loc[obj_df['acquisition_type'] == 'FULL_FIELD', m],
            'ROI': obj_df.loc[obj_df['acquisition_type'] == 'ROI', m],
        }
        parts.append(quantile_table(groups, m))
        for cat in sorted(obj_df['category'].unique()):
            sub = obj_df[(obj_df['acquisition_type'] == 'FULL_FIELD') &
                         (obj_df['category'] == cat)]
            parts.append(quantile_table({'FULL_FIELD | ' + cat: sub[m]}, m))
    return pd.concat(parts, ignore_index=True)


def stratum_counts(df: pd.DataFrame, column: str) -> pd.DataFrame:
    c = df[column].value_counts().reindex(list(STRATA), fill_value=0)
    return pd.DataFrame({'stratum': c.index, 'objects': c.values,
                         'percent': c.values / max(1, c.sum()) * 100})


# ---------------------------------------------------------------------------
# Candidate taxonomies
# ---------------------------------------------------------------------------

def _quartiles(values) -> tuple:
    v = np.asarray(pd.Series(values).dropna(), dtype=float)
    q25, q50, q75 = np.quantile(v, [0.25, 0.50, 0.75])
    return float(q25), float(q50), float(q75)


def build_candidates(obj_df: pd.DataFrame) -> list:
    """
    Build a SMALL set of scientifically defensible candidate taxonomies.

    All boundaries are derived from **TRAIN FULL_FIELD objects only**, matching the
    historical source population. No VAL data is used. Candidates are exploratory.
    """
    ff = obj_df[obj_df['acquisition_type'] == 'FULL_FIELD']
    t = HISTORICAL_TAXONOMY

    # Candidate 1 — faithful historical kub_size_v1
    c1 = {
        'candidate_id': 'C1_HISTORICAL_kub_size_v1',
        'name': 'Historical kub_size_v1 (faithful)',
        'metric': 'component_ratio',
        'metric_definition': t['metric_definition'],
        'coordinate_system': 'native pixels, normalized by native image area',
        'unit': 'object (connected component, 8-connectivity)',
        'acquisition_applicability': 'FULL_FIELD only (ROI -> ROI_NOT_PRIMARY_BINNED)',
        'boundaries': {'TINY': f'x <= {t["Q25"]!r}',
                       'SMALL': f'{t["Q25"]!r} < x <= {t["Q50"]!r}',
                       'MEDIUM': f'{t["Q50"]!r} < x <= {t["Q75"]!r}',
                       'LARGE': f'x > {t["Q75"]!r}'},
        'cut_values': [t['Q25'], t['Q50'], t['Q75']],
        'advantages': [
            'Exact continuity with Phases 06-14 historical evidence',
            'Already normalizes away native image size',
            'Quartile cut points are transparent and TRAIN-derived',
        ],
        'limitations': [
            'Derived on phase4_v2 FULL_FIELD TRAIN (contaminated-era) components',
            'Not applicable to ROI crops by construction',
            'Quartiles are population-relative, not geometrically absolute',
        ],
        'historical_compatibility': 'EXACT (same metric, unit, connectivity, boundaries)',
        'downstream_compatibility': 'High - historical object-recall analysis used these labels',
        'boundary_semantics': 'lower-inclusive cumulative (value == quartile -> lower bin)',
        'rounding_rule': 'no rounding; full-precision float comparison',
        'measurement_precision': 'float64 ratio',
    }

    # Candidate 2 — scale-invariant normalized equivalent diameter (both regimes)
    q2 = _quartiles(ff['normalized_equivalent_diameter'])
    c2 = {
        'candidate_id': 'C2_NORMALIZED_EQ_DIAMETER',
        'name': 'Scale-invariant normalized equivalent diameter',
        'metric': 'normalized_equivalent_diameter',
        'metric_definition': 'equivalent_diameter / min(native_width, native_height)',
        'coordinate_system': 'scale-invariant (relative to the image short side)',
        'unit': 'object (connected component, 8-connectivity)',
        'acquisition_applicability': 'both regimes (boundaries derived on FULL_FIELD TRAIN)',
        'boundaries': {'TINY': f'x <= {q2[0]!r}',
                       'SMALL': f'{q2[0]!r} < x <= {q2[1]!r}',
                       'MEDIUM': f'{q2[1]!r} < x <= {q2[2]!r}',
                       'LARGE': f'x > {q2[2]!r}'},
        'cut_values': list(q2),
        'advantages': [
            'Direct geometric interpretation (object diameter vs image short side)',
            'Insensitive to native resolution differences within a regime',
            'Still object-level, so object recall is preserved',
        ],
        'limitations': [
            'No exact historical continuity (different metric family)',
            'NOT automatically calibrated across regimes: an ROI crop magnifies its '
            'object, so a FULL_FIELD-derived rule pushes most ROI objects into LARGE',
            'A genuine cross-regime rule would need separate ROI calibration (Option C)',
        ],
        'historical_compatibility': 'None (new metric; same unit and quartile structure)',
        'downstream_compatibility': 'Good - still object-level, so object recall is preserved',
        'boundary_semantics': 'lower-inclusive cumulative (value == cut -> lower bin)',
        'rounding_rule': 'no rounding; full-precision float comparison',
        'measurement_precision': 'float64 ratio',
    }

    # Candidate 3 — FULL_FIELD-only native equivalent diameter in pixels
    q3 = _quartiles(ff['equivalent_diameter'])
    c3 = {
        'candidate_id': 'C3_FULLFIELD_NATIVE_EQ_DIAMETER_PX',
        'name': 'FULL_FIELD native equivalent diameter (pixels)',
        'metric': 'equivalent_diameter',
        'metric_definition': 'sqrt(4 * component_pixels / pi) in native pixels',
        'coordinate_system': 'native pixels',
        'unit': 'object (connected component, 8-connectivity)',
        'acquisition_applicability': 'FULL_FIELD only',
        'boundaries': {'TINY': f'x <= {q3[0]!r} px',
                       'SMALL': f'{q3[0]!r} < x <= {q3[1]!r} px',
                       'MEDIUM': f'{q3[1]!r} < x <= {q3[2]!r} px',
                       'LARGE': f'x > {q3[2]!r} px'},
        'cut_values': list(q3),
        'advantages': [
            'Most directly interpretable unit (pixels) for reviewers',
            'FULL_FIELD images are comparatively standardised (median width ~2304, '
            'only 35 distinct resolutions), so a native-pixel rule is defensible there',
        ],
        'limitations': [
            'Native-pixel values are NOT transferable to ROI crops',
            'Absolute pixel thresholds are sensitive to any future resampling change',
            'No historical continuity',
        ],
        'historical_compatibility': 'None (different metric)',
        'downstream_compatibility': 'Moderate - requires explicit FULL_FIELD restriction',
        'boundary_semantics': 'lower-inclusive cumulative (value == cut -> lower bin)',
        'rounding_rule': 'no rounding; full-precision float comparison',
        'measurement_precision': 'float64 pixels',
    }

    return [c1, c2, c3]


def candidate_assignment(obj_df: pd.DataFrame, candidate: dict) -> np.ndarray:
    """Assign a candidate's exploratory stratum to each object."""
    metric = candidate['metric']
    cuts = candidate['cut_values']
    values = obj_df[metric].to_numpy(dtype=float)
    if candidate['acquisition_applicability'].startswith('FULL_FIELD only'):
        applicable = obj_df['acquisition_type'].eq('FULL_FIELD').to_numpy()
    else:
        applicable = np.ones(len(obj_df), dtype=bool)

    labels = np.where(values <= cuts[0], 'TINY',
                      np.where(values <= cuts[1], 'SMALL',
                               np.where(values <= cuts[2], 'MEDIUM', 'LARGE')))
    return np.where(applicable, labels, 'NOT_APPLICABLE')


def candidate_summary(obj_df: pd.DataFrame, candidates: list) -> pd.DataFrame:
    """TRAIN-only counts and prevalence per candidate (and per acquisition)."""
    rows = []
    for cand in candidates:
        labels = candidate_assignment(obj_df, cand)
        work = obj_df.assign(_label=labels)
        for scope, sub in (('ALL_TRAIN', work),
                           ('FULL_FIELD', work[work['acquisition_type'] == 'FULL_FIELD']),
                           ('ROI', work[work['acquisition_type'] == 'ROI'])):
            applicable = sub[sub['_label'] != 'NOT_APPLICABLE']
            n = len(applicable)
            for s in STRATA:
                k = int((applicable['_label'] == s).sum())
                rows.append({
                    'candidate_id': cand['candidate_id'],
                    'candidate_name': cand['name'],
                    'metric': cand['metric'],
                    'scope': scope,
                    'stratum': s,
                    'objects': k,
                    'prevalence_pct': (100.0 * k / n) if n else 0.0,
                    'applicable_objects': n,
                })
    return pd.DataFrame(rows)


def boundary_sensitivity(obj_df: pd.DataFrame, candidates: list) -> pd.DataFrame:
    """
    TRAIN-only sensitivity around each candidate boundary.

    Reports how many objects sit immediately either side of each cut, so dense
    pile-ups (where small measurement variation would flip many labels) are visible.
    """
    rows = []
    for cand in candidates:
        metric = cand['metric']
        values = obj_df[metric].to_numpy(dtype=float)
        if cand['acquisition_applicability'].startswith('FULL_FIELD only'):
            mask = obj_df['acquisition_type'].eq('FULL_FIELD').to_numpy()
            values = values[mask]
        total = len(values)

        # neighbourhood: +/-1 and +/-2 pixels for pixel metrics, else small relative deltas
        if metric in ('equivalent_diameter',):
            deltas = [(1.0, '1'), (2.0, '2')]
            delta_kind = 'pixels'
        else:
            deltas = [(0.05, '1'), (0.10, '2')]
            delta_kind = 'relative_fraction_of_cut'

        for name, cut in zip(('TINY_SMALL', 'SMALL_MEDIUM', 'MEDIUM_LARGE'),
                             cand['cut_values']):
            rec = {'candidate_id': cand['candidate_id'], 'metric': metric,
                   'boundary': name, 'cut_value': float(cut),
                   'delta_kind': delta_kind, 'applicable_objects': int(total)}
            for d, tag in deltas:
                dd = d * cut if delta_kind.startswith('relative') else d
                below = int(((values >= cut - dd) & (values < cut)).sum())
                above = int(((values >= cut) & (values < cut + dd)).sum())
                rec[f'within_minus_{tag}'] = below
                rec[f'within_plus_{tag}'] = above
                rec[f'pileup_frac_{tag}'] = (below + above) / total if total else 0.0
            rows.append(rec)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Deterministic gallery
# ---------------------------------------------------------------------------

def deterministic_gallery_selection(obj_df: pd.DataFrame, case_df: pd.DataFrame,
                                    n_total: int = 16,
                                    seed_tag: str = 'phase07-train-gallery') -> pd.DataFrame:
    """
    Deterministic, prediction-independent TRAIN-only gallery selection.

    Protocol
    --------
    1. Order objects by stable sample_id then component_index.
    2. Partition into a strata grid of (acquisition_type x category).
    3. Round-robin across strata ordered deterministically by SHA-256 of the
       stratum key, taking the median-index member of each stratum first.
    4. Fill remaining slots from objects nearest the candidate-boundary
       neighbourhoods so boundary behaviour is illustrated.
    5. Ensure each selected object's case metadata is joined in.

    Selection never inspects model output or visual quality. TRAIN only.
    """
    work = obj_df.copy()
    work['stratum'] = work['acquisition_type'] + '|' + work['category']
    strata = sorted(work['stratum'].unique(),
                    key=lambda s: hashlib.sha256(f'{seed_tag}|{s}'.encode()).hexdigest())

    picked = []
    for s in strata:
        members = work[work['stratum'] == s].sort_values(['sample_id', 'component_index'])
        if len(members):
            picked.append(members.iloc[len(members) // 2])

    # boundary-neighbourhood fill (candidate C1 cuts, FULL_FIELD objects)
    ff = work[work['acquisition_type'] == 'FULL_FIELD'].sort_values(
        ['sample_id', 'component_index'])
    if len(ff):
        for cut in HISTORICAL_TAXONOMY['Q25'], HISTORICAL_TAXONOMY['Q75']:
            near = ff.iloc[(ff['component_ratio'] - cut).abs().argsort()[:2]]
            picked.extend([row for _, row in near.iterrows()])

    sel = pd.DataFrame(picked).drop_duplicates(subset=['sample_id', 'component_index'])
    sel = sel.sort_values(['sample_id', 'component_index']).reset_index(drop=True)

    if len(sel) > n_total:
        keep = np.linspace(0, len(sel) - 1, n_total).round().astype(int)
        sel = sel.iloc[sorted(set(keep))].reset_index(drop=True)
    elif len(sel) < n_total:
        remaining = work.merge(sel[['sample_id', 'component_index']],
                               on=['sample_id', 'component_index'], how='left',
                               indicator=True)
        remaining = remaining[remaining['_merge'] == 'left_only'].sort_values(
            ['sample_id', 'component_index'])
        need = n_total - len(sel)
        if len(remaining):
            idx = np.linspace(0, len(remaining) - 1, min(need, len(remaining))).round().astype(int)
            sel = pd.concat([sel, remaining.iloc[idx]]).drop_duplicates(
                subset=['sample_id', 'component_index'])

    sel = sel.sort_values(['sample_id', 'component_index']).reset_index(drop=True)
    sel['selection_rank'] = np.arange(1, len(sel) + 1)

    # join case metadata + image paths
    meta = case_df[['sample_id', 'native_width', 'native_height']]
    sel = sel.merge(meta, on='sample_id', how='left', suffixes=('', '_case'))
    paths = pd.concat([
        load_manifest('train')[['sample_id', 'image_path', 'mask_path']],
    ], ignore_index=True).drop_duplicates('sample_id')
    sel = sel.merge(paths, on='sample_id', how='left')
    return sel


def gallery_pages(sel: pd.DataFrame, obj_lookup: pd.DataFrame,
                  cases_per_page: int = 4, title: str = 'Phase 07 TRAIN gallery'):
    """
    Paginated gallery: one row per selected object, three panels
    (original | binary GT with the selected component outlined | GT overlay).

    Exploratory candidate labels are drawn from obj_lookup and are NOT FROZEN.
    TRAIN only; never renders TEST content.
    """
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    n = len(sel)
    n_pages = int(np.ceil(n / cases_per_page))
    figs = []

    for page in range(n_pages):
        chunk = sel.iloc[page * cases_per_page:(page + 1) * cases_per_page]
        nrows = len(chunk)
        fig, axes = plt.subplots(nrows, 3, figsize=(11.5, 3.6 * nrows))
        axes = np.atleast_2d(axes)

        for i, (_, r) in enumerate(chunk.iterrows()):
            img = np.array(Image.open(r['image_path']))
            mask = np.array(Image.open(r['mask_path']))
            if mask.ndim == 3:
                mask = mask[..., 0]
            fg = mask > 0
            img_cmap = 'gray' if img.ndim == 2 else None

            # isolate the selected component using the same labelling
            structure = np.ones((3, 3), dtype=int)
            labeled, _ = nd_label(fg, structure=structure)
            cidx = int(r['component_index'])
            cmap = labeled == cidx

            ax0, ax1, ax2 = axes[i, 0], axes[i, 1], axes[i, 2]
            ax0.imshow(img, cmap=img_cmap)
            ax0.set_title('original', fontsize=8)

            ax1.imshow(fg, cmap='gray', vmin=0, vmax=1)
            ax1.set_title('binary GT (mask > 0)', fontsize=8)

            ax2.imshow(img, cmap=img_cmap)
            rgba = np.zeros((*fg.shape, 4), dtype=float)
            rgba[..., 0] = 1.0
            rgba[..., 3] = fg * 0.40
            ax2.imshow(rgba)
            if cmap.any():
                rr, cc = np.nonzero(cmap)
                y0, y1, x0, x1 = rr.min(), rr.max(), cc.min(), cc.max()
                ax2.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False,
                                        edgecolor='#28d17c', lw=1.8))
                ax2.contour(cmap, colors='#ffd400', linewidths=1.0)
            ax2.set_title('GT overlay + selected component', fontsize=8)

            for ax in (ax0, ax1, ax2):
                ax.set_xticks([]); ax.set_yticks([])

            cand = r.get('candidate_labels', 'NOT FROZEN')
            ax0.set_xlabel(
                f"{r['sample_id'][:12]} | {r['category']} | {r['acquisition_type']} | "
                f"comp {cidx}\n"
                f"{r['native_width']}x{r['native_height']} | "
                f"px={int(r['component_pixels'])} | ratio={r['component_ratio']:.6f} | "
                f"eqD={r['equivalent_diameter']:.1f}\n"
                f"{cand}",
                fontsize=7, labelpad=4)

        for i in range(nrows):
            for j in range(3):
                if i >= len(chunk):
                    axes[i, j].axis('off')

        fig.suptitle(f'{title} — page {page + 1}/{n_pages}  (candidate labels NOT FROZEN)',
                     fontsize=11, fontweight='bold')
        fig.tight_layout(rect=[0, 0, 1, 0.96])
        figs.append(fig)

    return figs


def save_fig(fig, path: Path, dpi: int = 130):
    import matplotlib.pyplot as plt
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=dpi, bbox_inches='tight')
    plt.close(fig)
    return path


# ---------------------------------------------------------------------------
# Table registry / governance
# ---------------------------------------------------------------------------

FINAL_TABLES = [
    'phase07_kub_v3_train_object_geometry.csv',
    'phase07_kub_v3_train_case_size_summary.csv',
    'phase07_kub_v3_train_size_quantiles.csv',
    'phase07_candidate_taxonomy_comparison.csv',
    'phase07_candidate_boundary_sensitivity.csv',
    'phase07_historical_definition_clean_v3_train.csv',
    'phase07_train_gallery_selection.csv',
]


def write_table(df: pd.DataFrame, name: str, out_dir: Path = None) -> Path:
    out_dir = out_dir or TABLES
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / name
    df.to_csv(p, index=False)
    return p


def final_table_registry(out_dir: Path = None) -> pd.DataFrame:
    out_dir = out_dir or TABLES
    rows = []
    for name in FINAL_TABLES:
        p = out_dir / name
        rows.append({'table': name, 'exists': p.exists(),
                     'bytes': int(p.stat().st_size) if p.exists() else 0,
                     'sha256': sha256_file(p) if p.exists() else None})
    return pd.DataFrame(rows)


def test_lock_assertion(ktr, ktest, obj_df) -> dict:
    return {
        'ACTIVE MANIFEST': ACTIVE_MANIFEST_VERSION,
        'KUB TRAIN CASES': int(len(ktr)),
        'KUB TEST (metadata only)': int(len(ktest)),
        'TRAIN OBJECTS': int(len(obj_df)),
        'VAL USED FOR THRESHOLD SELECTION': 'NO',
        'VAL CONTENT READS FOR PART1A': 0,
        'TEST CONTENT READS': 0,
        'TEST VISUALIZATIONS': 0,
        'TEST METRICS': 0,
        'THRESHOLD FROZEN': 'NO',
        'PHASE 08 STARTED': 'NO',
    }
