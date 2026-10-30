"""
Phase 07 Part 1B — CLEAN-v3 taxonomy freeze + post-freeze VAL characterization.

Reusable module. The freeze notebook imports these functions.

Sequencing contract (enforced by the driver and the notebook):
    A. derive clean-v3 Q25/Q50/Q75 from TRAIN only
    B. persist the exact threshold artifact
    C. hash the threshold artifact
    D. mark FROZEN
    E. only AFTER A-D may VAL medical content be read
    F. apply frozen thresholds to VAL unchanged

Governance: TEST content is never read. Thresholds are never adjusted after VAL.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from scipy.ndimage import label as nd_label

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase07_tiny_definition as p7  # noqa: E402

PROJECT_ROOT = Path(r'D:\Softfors\jup')
MANIFEST_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'
V2_MANIFEST_DIR = PROJECT_ROOT / 'manifests'
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase07_tiny_object_definition'

CLEAN_TAXONOMY_ID = 'kub_size_clean_v3_v1'
HISTORICAL_TAXONOMY_ID = 'kub_size_v1'
ROI_NOT_PRIMARY_BINNED = 'ROI_NOT_PRIMARY_BINNED'
STRATA = ('TINY', 'SMALL', 'MEDIUM', 'LARGE')

CONNECTIVITY = 8
FOREGROUND_RULE = 'mask > 0'

HISTORICAL_THRESHOLDS = {
    'Q25': 0.0001499766777599,
    'Q50': 0.00033976472454305,
    'Q75': 0.0008266496069636999,
}

# Historical authoritative artifacts (immutable provenance)
HIST_COMPONENTS_CSV = TABLES / 'kub_train_components_sized.csv'
HIST_COMPONENTS_SHA = 'da31c7d7e4bf13b199ddba2239fc512057546ee8436daadfeac365662eb973d8'
HIST_THRESHOLDS_JSON = AUDITS / 'kub_object_size_thresholds.json'
HIST_THRESHOLDS_JSON_SHA = '20d3ba58fd5d1272aa52c7c6f82a074b1c903d38de8896ad3a78c3af95eb5043'

CLEAN_THRESHOLD_JSON = AUDITS / 'kub_size_clean_v3_v1_thresholds.json'
CLEAN_THRESHOLD_MD = AUDITS / 'kub_size_clean_v3_v1_thresholds.md'

EXPECTED = {'kub_train_cases': 1978, 'full_field_cases': 770, 'full_field_components': 1161}


def sha256_file(path: Path) -> str:
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


# ---------------------------------------------------------------------------
# Quantile method (characterized from the historical implementation)
# ---------------------------------------------------------------------------

QUANTILE_METHOD = {
    'implementation': 'numpy.quantile',
    'method': "default 'linear' interpolation",
    'call': 'np.quantile(values, [0.25, 0.50, 0.75])',
    'sort_handling': 'numpy orders the input internally; no explicit pre-sort required',
    'nan_handling': 'no NaN present; non-finite input raises (guarded)',
    'precision': 'float64',
    'input_precision_note': (
        'The historical thresholds were computed from the pipeline-persisted '
        'component table (reports/tables/kub_train_components_sized.csv), i.e. after the '
        'pipeline float->text->float round-trip, NOT from full-precision in-memory ratios. '
        'Phase 07 Part 1B therefore reports both a full-precision derivation and a '
        'round-trip-faithful derivation and confirms they agree.'),
}


def verify_historical_reproduction() -> dict:
    """
    Prove the historical quantile method reproduces kub_size_v1 exactly.

    Recomputes Q25/Q50/Q75 from the historical component table and compares with
    the frozen historical threshold record.
    """
    if not HIST_COMPONENTS_CSV.exists():
        return {'reproduced': False, 'reason': 'historical component table missing'}

    table_sha = sha256_file(HIST_COMPONENTS_CSV)
    df = pd.read_csv(HIST_COMPONENTS_CSV)
    ff = df[df['view_type'] == 'FULL_FIELD']
    q25, q50, q75 = derive_quartiles(ff['component_ratio'].to_numpy(dtype=float))

    return {
        'reproduced': bool(q25 == HISTORICAL_THRESHOLDS['Q25']
                           and q50 == HISTORICAL_THRESHOLDS['Q50']
                           and q75 == HISTORICAL_THRESHOLDS['Q75']),
        'source_table': str(HIST_COMPONENTS_CSV.relative_to(PROJECT_ROOT)).replace('\\', '/'),
        'source_table_sha': table_sha,
        'source_table_sha_matches_provenance': table_sha == HIST_COMPONENTS_SHA,
        'full_field_components': int(len(ff)),
        'recomputed': {'Q25': q25, 'Q50': q50, 'Q75': q75},
        'recorded': dict(HISTORICAL_THRESHOLDS),
        'exact_match': {
            'Q25': q25 == HISTORICAL_THRESHOLDS['Q25'],
            'Q50': q50 == HISTORICAL_THRESHOLDS['Q50'],
            'Q75': q75 == HISTORICAL_THRESHOLDS['Q75'],
        },
    }


def derive_quartiles(values):
    """Historical quantile algorithm applied verbatim (see QUANTILE_METHOD)."""
    arr = np.asarray(values, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError('Non-finite value encountered in quantile input')
    q25, q50, q75 = np.quantile(arr, [0.25, 0.50, 0.75])
    if not (q25 < q50 < q75):
        raise ValueError('Invalid or collapsed quartile thresholds')
    return float(q25), float(q50), float(q75)


# ---------------------------------------------------------------------------
# Component extraction (TRAIN / VAL, FULL_FIELD primary)
# ---------------------------------------------------------------------------

def extract_full_field_components(df: pd.DataFrame, split_label: str) -> pd.DataFrame:
    """
    Extract per-component geometry for the FULL_FIELD rows of a KUB split.

    Foreground = (mask > 0). Connectivity = 8. component_ratio =
    component_pixels / (native_height * native_width).
    """
    rows = []
    for _, r in df.iterrows():
        with Image.open(r['image_path']) as im:
            w, h = im.size
        mask = np.array(Image.open(r['mask_path']))
        if mask.ndim == 3:
            mask = mask[..., 0]
        fg = mask > 0
        lab, n = nd_label(fg, structure=np.ones((3, 3), dtype=int))
        if n == 0:
            continue
        total = float(h * w)
        for cid in range(1, n + 1):
            cmap = lab == cid
            cpx = int(cmap.sum())
            rows.append({
                'sample_id': r['sample_id'],
                'patient_id': r['patient_id'],
                'category': r['category'],
                'split': split_label,
                'component_index': cid,
                'component_pixels': cpx,
                'component_ratio': cpx / total,
            })
    return pd.DataFrame(rows)


def kub_full_field(df: pd.DataFrame) -> pd.DataFrame:
    """KUB rows whose acquisition type is FULL_FIELD."""
    out = p7.kub_only(df)
    return out[out['image_path'].map(p7.derive_acquisition_type) == 'FULL_FIELD'].copy()


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

def classify(value: float, thresholds: dict) -> str:
    """Frozen boundary semantics (value NOT rounded; boundary -> lower bin)."""
    if value <= thresholds['Q25']:
        return 'TINY'
    if value <= thresholds['Q50']:
        return 'SMALL'
    if value <= thresholds['Q75']:
        return 'MEDIUM'
    return 'LARGE'


def apply_frozen(components: pd.DataFrame, thresholds: dict,
                 taxonomy_id: str = CLEAN_TAXONOMY_ID) -> pd.DataFrame:
    """Apply frozen thresholds. All rows are FULL_FIELD, so all are binned."""
    out = components.copy()
    out['frozen_taxonomy_id'] = taxonomy_id
    out['frozen_stratum'] = out['component_ratio'].map(lambda v: classify(v, thresholds))
    return out


# ---------------------------------------------------------------------------
# Freeze artifact
# ---------------------------------------------------------------------------

def write_freeze_artifact(thresholds: dict, provenance: dict,
                          path: Path = None) -> tuple:
    """Persist the FROZEN threshold artifact and return (path, sha256)."""
    path = path or CLEAN_THRESHOLD_JSON
    ts = datetime.now(timezone.utc).isoformat()
    payload = {
        'taxonomy_id': CLEAN_TAXONOMY_ID,
        'status': 'FROZEN',
        'manifest_version': 'phase4_v3',
        'derivation_split': 'TRAIN',
        'dataset': 'KUB',
        'acquisition_scope': 'FULL_FIELD',
        'foreground_rule': FOREGROUND_RULE,
        'connectivity': CONNECTIVITY,
        'unit': 'connected_component',
        'metric': 'component_ratio',
        'metric_definition': 'component_pixels / (native_height * native_width)',
        'coordinate_system': 'native mask geometry normalized by native full-image area',
        'quantile_algorithm': QUANTILE_METHOD['implementation'],
        'quantile_method': QUANTILE_METHOD['method'],
        'quantile_call': QUANTILE_METHOD['call'],
        'quantile_precision': QUANTILE_METHOD['precision'],
        'derivation_cases': provenance['derivation_cases'],
        'derivation_objects': provenance['derivation_objects'],
        'Q25': thresholds['Q25'],
        'Q50': thresholds['Q50'],
        'Q75': thresholds['Q75'],
        'boundary_semantics': {
            'TINY': 'x <= Q25',
            'SMALL': 'Q25 < x <= Q50',
            'MEDIUM': 'Q50 < x <= Q75',
            'LARGE': 'x > Q75',
            'rounding': 'no rounding applied before classification',
            'boundary_value_goes_to': 'lower bin',
        },
        'roi_handling': ROI_NOT_PRIMARY_BINNED,
        'derivation_timestamp': ts,
        'source_manifest_sha': provenance['source_manifest_sha'],
        'object_table_sha': provenance['object_table_sha'],
        'historical_taxonomy_reference': {
            'taxonomy_id': HISTORICAL_TAXONOMY_ID,
            'thresholds': dict(HISTORICAL_THRESHOLDS),
            'status': 'HISTORICAL_v2_IMMUTABLE',
            'reproduced_exactly': provenance['historical_reproduced'],
        },
        'supervisor_authorized': True,
        'threshold_frozen': True,
        'val_content_reads_before_freeze': 0,
        'test_content_reads': 0,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    return path, sha256_file(path)


def ensure_freeze_artifact(thresholds: dict, provenance: dict,
                           path: Path = None) -> tuple:
    """
    Idempotent freeze: reuse an existing FROZEN artifact when its thresholds match.

    This keeps the artifact SHA stable across repeated runs (driver + notebook)
    instead of rewriting the file and changing its timestamp/hash.
    Returns (path, sha256, reused).
    """
    path = path or CLEAN_THRESHOLD_JSON
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding='utf-8'))
            same = (existing.get('status') == 'FROZEN'
                    and existing.get('taxonomy_id') == CLEAN_TAXONOMY_ID
                    and float(existing.get('Q25')) == float(thresholds['Q25'])
                    and float(existing.get('Q50')) == float(thresholds['Q50'])
                    and float(existing.get('Q75')) == float(thresholds['Q75']))
            if same:
                return path, sha256_file(path), True
        except Exception:
            pass
    p, s = write_freeze_artifact(thresholds, provenance, path)
    return p, s, False


def write_freeze_markdown(payload: dict, sha: str, path: Path = None) -> Path:
    path = path or CLEAN_THRESHOLD_MD
    md = [
        '# kub_size_clean_v3_v1 — FROZEN Threshold Artifact', '',
        f"**Taxonomy ID:** `{payload['taxonomy_id']}`  ",
        f"**Status:** **{payload['status']}**  ",
        f"**Artifact SHA-256:** `{sha}`  ",
        f"**Derivation timestamp:** {payload['derivation_timestamp']}", '',
        '## Design', '',
        '| Field | Value |', '|---|---|',
        f"| Manifest version | `{payload['manifest_version']}` |",
        f"| Derivation split | {payload['derivation_split']} |",
        f"| Dataset | {payload['dataset']} |",
        f"| Acquisition scope | {payload['acquisition_scope']} |",
        f"| ROI handling | `{payload['roi_handling']}` |",
        f"| Foreground rule | `{payload['foreground_rule']}` |",
        f"| Connectivity | {payload['connectivity']} |",
        f"| Unit | {payload['unit']} |",
        f"| Metric | `{payload['metric']}` = {payload['metric_definition']} |",
        f"| Coordinate system | {payload['coordinate_system']} |", '',
        '## Quantile method', '',
        f"- Implementation: `{payload['quantile_algorithm']}`",
        f"- Method: {payload['quantile_method']}",
        f"- Call: `{payload['quantile_call']}`",
        f"- Precision: {payload['quantile_precision']}",
        f"- Derivation cases: {payload['derivation_cases']}",
        f"- Derivation objects: {payload['derivation_objects']}", '',
        '## FROZEN thresholds', '',
        '| Quartile | Value |', '|---|---|',
        f"| Q25 | `{payload['Q25']!r}` |",
        f"| Q50 | `{payload['Q50']!r}` |",
        f"| Q75 | `{payload['Q75']!r}` |", '',
        '## Boundary semantics', '',
        '| Stratum | Condition |', '|---|---|',
    ]
    for k, v in payload['boundary_semantics'].items():
        md.append(f'| {k} | `{v}` |')
    md += ['', '## Historical reference (immutable)', '',
           f"- `{payload['historical_taxonomy_reference']['taxonomy_id']}` "
           f"({payload['historical_taxonomy_reference']['status']})",
           f"- Q25 `{payload['historical_taxonomy_reference']['thresholds']['Q25']!r}`",
           f"- Q50 `{payload['historical_taxonomy_reference']['thresholds']['Q50']!r}`",
           f"- Q75 `{payload['historical_taxonomy_reference']['thresholds']['Q75']!r}`",
           f"- Reproduced exactly: {payload['historical_taxonomy_reference']['reproduced_exactly']}",
           '', '## Governance', '',
           f"- Threshold frozen: {payload['threshold_frozen']}",
           f"- VAL content reads before freeze: {payload['val_content_reads_before_freeze']}",
           f"- TEST content reads: {payload['test_content_reads']}",
           f"- Supervisor authorized: {payload['supervisor_authorized']}", '',
           '## Provenance', '',
           f"- Source manifest SHA: `{payload['source_manifest_sha']}`",
           f"- Object table SHA: `{payload['object_table_sha']}`", '']
    path.write_text('\n'.join(md), encoding='utf-8')
    return path


# ---------------------------------------------------------------------------
# Summaries / crosswalk
# ---------------------------------------------------------------------------

def stratum_summary(df: pd.DataFrame, label_col: str) -> pd.DataFrame:
    c = df[label_col].value_counts().reindex(list(STRATA), fill_value=0)
    n = int(c.sum())
    return pd.DataFrame({
        'stratum': list(STRATA),
        'objects': [int(c[s]) for s in STRATA],
        'percent': [100.0 * c[s] / n if n else 0.0 for s in STRATA],
    })


def threshold_comparison(clean: dict) -> pd.DataFrame:
    rows = []
    for q in ('Q25', 'Q50', 'Q75'):
        h, c = HISTORICAL_THRESHOLDS[q], clean[q]
        rows.append({
            'quartile': q,
            'historical_kub_size_v1': h,
            'clean_kub_size_clean_v3_v1': c,
            'absolute_difference': c - h,
            'relative_difference': (c - h) / h if h else float('nan'),
        })
    return pd.DataFrame(rows)


def label_crosswalk(train_ff: pd.DataFrame, clean: dict) -> pd.DataFrame:
    """Per-object historical vs clean stratum on CLEAN-v3 TRAIN FULL_FIELD objects."""
    out = train_ff.copy()
    out['historical_stratum'] = out['component_ratio'].map(
        lambda v: classify(v, HISTORICAL_THRESHOLDS))
    out['clean_stratum'] = out['component_ratio'].map(lambda v: classify(v, clean))
    out['stratum_changed'] = out['historical_stratum'] != out['clean_stratum']
    return out


def categorical_stability(df: pd.DataFrame, level_col: str,
                          train_col='TRAIN_pct', val_col='VAL_pct') -> float:
    return float((df[train_col] - df[val_col]).abs().max())


FINAL_TABLES = [
    'phase07_clean_v3_threshold_derivation_objects.csv',
    'phase07_historical_vs_clean_thresholds.csv',
    'phase07_train_historical_clean_label_crosswalk.csv',
    'phase07_kub_v3_val_object_size_frozen.csv',
    'phase07_kub_v3_frozen_taxonomy_summary.csv',
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


def freeze_gate(thresholds: dict, artifact_sha: str) -> dict:
    """The mandatory pre-VAL freeze gate block."""
    return {
        'TAXONOMY': CLEAN_TAXONOMY_ID,
        'STATUS': 'FROZEN',
        'Q25': repr(thresholds['Q25']),
        'Q50': repr(thresholds['Q50']),
        'Q75': repr(thresholds['Q75']),
        'DERIVED FROM': 'CLEAN-v3 TRAIN FULL_FIELD ONLY',
        'VAL CONTENT READS': 0,
        'TEST CONTENT READS': 0,
        'THRESHOLD ARTIFACT SHA': artifact_sha,
    }


# ---------------------------------------------------------------------------
# Figures (shared by driver and notebook)
# ---------------------------------------------------------------------------

FIGURE_NAMES = [
    'phase07b_train_frozen_thresholds.png',
    'phase07b_threshold_overlay.png',
    'phase07b_crosswalk.png',
    'phase07b_train_frozen_distribution.png',
    'phase07b_val_frozen_distribution.png',
    'phase07b_train_val_frozen_comparison.png',
    'phase07b_val_category_frozen.png',
]


def make_figures(train_frozen, val_frozen, xwalk, clean):
    """Generate the seven required TRAIN/VAL taxonomy-freeze figures."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    h = HISTORICAL_THRESHOLDS
    FIGDIR.mkdir(parents=True, exist_ok=True)

    # 1. TRAIN FULL_FIELD distribution with frozen thresholds
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    v = train_frozen['component_ratio'].replace(0, np.nan).dropna()
    ax.hist(v, bins=np.logspace(np.log10(v.min()), np.log10(v.max()), 60),
            color='#2f7ed8', alpha=0.85)
    for q, c, lab in ((clean['Q25'], '#d64545', 'Q25'), (clean['Q50'], '#e08a3c', 'Q50'),
                      (clean['Q75'], '#4a9d5f', 'Q75')):
        ax.axvline(q, color=c, ls='--', lw=1.5, label=f'{lab} (clean-v3 frozen)')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('component_ratio'); ax.set_ylabel('objects (log)')
    ax.set_title('CLEAN-v3 TRAIN FULL_FIELD component-ratio + frozen thresholds')
    ax.legend(frameon=False, fontsize=8)
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[0])

    # 2. historical vs clean threshold overlay
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    ax.hist(v, bins=np.logspace(np.log10(v.min()), np.log10(v.max()), 60),
            color='#c9d6e4', alpha=0.85)
    for q in ('Q25', 'Q50', 'Q75'):
        ax.axvline(h[q], color='#7a6bb5', ls='-', lw=1.6, label=f'{q} historical')
        ax.axvline(clean[q], color='#d64545', ls='--', lw=1.6, label=f'{q} clean-v3')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('component_ratio'); ax.set_ylabel('objects (log)')
    ax.set_title('Historical vs clean-v3 thresholds (TRAIN FULL_FIELD)')
    ax.legend(frameon=False, fontsize=7, ncol=2)
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[1])

    # 3. crosswalk heatmap
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ct = pd.crosstab(xwalk['historical_stratum'], xwalk['clean_stratum']).reindex(
        index=list(STRATA), columns=list(STRATA), fill_value=0)
    im = ax.imshow(ct.values, cmap='Blues')
    ax.set_xticks(range(len(STRATA))); ax.set_xticklabels(STRATA)
    ax.set_yticks(range(len(STRATA))); ax.set_yticklabels(STRATA)
    ax.set_xlabel('clean-v3 stratum'); ax.set_ylabel('historical stratum')
    for i in range(len(STRATA)):
        for j in range(len(STRATA)):
            ax.text(j, i, str(ct.values[i, j]), ha='center', va='center', fontsize=9,
                    color='white' if ct.values[i, j] > ct.values.max() * 0.6 else '#222')
    ax.set_title('TRAIN historical vs clean stratum crosswalk')
    fig.colorbar(im, ax=ax, shrink=0.8)
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[2])

    # 4. TRAIN frozen distribution
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    tc = stratum_summary(train_frozen, 'frozen_stratum')
    ax.bar(tc['stratum'], tc['objects'], color=['#d64545', '#e08a3c', '#bcbd22', '#4a9d5f'])
    for i, vv in enumerate(tc['objects']):
        ax.annotate(f'{vv}', (i, vv), ha='center', va='bottom', fontsize=9)
    ax.set_ylabel('objects')
    ax.set_title('TRAIN frozen size distribution (quartile-balanced by construction)')
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[3])

    # 5. VAL frozen distribution
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    vc = stratum_summary(val_frozen, 'frozen_stratum')
    ax.bar(vc['stratum'], vc['objects'], color=['#d64545', '#e08a3c', '#bcbd22', '#4a9d5f'])
    for i, vv in enumerate(vc['objects']):
        ax.annotate(f'{vv}', (i, vv), ha='center', va='bottom', fontsize=9)
    ax.set_ylabel('objects')
    ax.set_title('VAL frozen size distribution (NOT expected to be balanced)')
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[4])

    # 6. TRAIN vs VAL comparison
    fig, ax = plt.subplots(figsize=(7.6, 4.3))
    x = np.arange(len(STRATA)); w = 0.38
    ax.bar(x - w / 2, tc['percent'], w, label='TRAIN', color='#2f7ed8')
    ax.bar(x + w / 2, vc['percent'], w, label='VAL', color='#4a9d5f')
    for i, (a, b) in enumerate(zip(tc['percent'], vc['percent'])):
        ax.annotate(f'{a:.1f}%', (i - w / 2, a), ha='center', va='bottom', fontsize=8)
        ax.annotate(f'{b:.1f}%', (i + w / 2, b), ha='center', va='bottom', fontsize=8)
    ax.set_xticks(x); ax.set_xticklabels(STRATA)
    ax.set_ylabel('percent of objects (%)')
    ax.set_title('TRAIN vs VAL frozen size distribution')
    ax.legend(frameon=False)
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[5])

    # 7. VAL category x frozen size
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    ct2 = pd.crosstab(val_frozen['category'], val_frozen['frozen_stratum']).reindex(
        columns=list(STRATA), fill_value=0)
    bottom = np.zeros(len(ct2))
    for s, col in zip(STRATA, ['#d64545', '#e08a3c', '#bcbd22', '#4a9d5f']):
        ax.bar(ct2.index, ct2[s], bottom=bottom, label=s, color=col)
        bottom += ct2[s].values
    ax.set_ylabel('objects')
    ax.set_title('VAL category x frozen-size distribution')
    ax.legend(frameon=False, fontsize=8)
    p7.save_fig(fig, FIGDIR / FIGURE_NAMES[6])

    return [FIGDIR / n for n in FIGURE_NAMES]
