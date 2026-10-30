"""
Phase 06 Part 1A — Characterization driver.

Runs the CLEAN-v3 KUB characterization end-to-end, writes the required tables,
and emits the audit JSON/MD. The reviewer notebook imports this module and
re-invokes the same functions, so notebook and driver stay consistent.

TEST content is never read: TEST is touched only through manifest metadata.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

import phase06_kub_characterization as p6  # noqa: E402

PROJECT_ROOT = p6.PROJECT_ROOT
TABLES = PROJECT_ROOT / 'reports' / 'tables'
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
FIGDIR = PROJECT_ROOT / 'reports' / 'figures' / 'phase06_kub_characterization'


def main():
    now = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Load manifests (TEST metadata only)
    # ------------------------------------------------------------------
    train = p6.load_manifest('train')
    val = p6.load_manifest('val')
    test = p6.load_manifest('test')
    quar = p6.load_manifest('quarantined')

    ktr = p6.kub_only(train)
    kva = p6.kub_only(val)
    ktest = p6.kub_only(test)
    kq = p6.kub_only(quar)

    # ------------------------------------------------------------------
    # Integrity audit
    # ------------------------------------------------------------------
    integ = p6.integrity_audit(ktr, kva, kq, ktest, verify_pixels=True)

    # ------------------------------------------------------------------
    # Geometry characterization (TRAIN + VAL only)
    # ------------------------------------------------------------------
    geo_tr = p6.characterize_population(ktr, 'TRAIN')
    geo_va = p6.characterize_population(kva, 'VAL')
    geo = pd.concat([geo_tr, geo_va], ignore_index=True)

    # ------------------------------------------------------------------
    # Population summaries
    # ------------------------------------------------------------------
    pop_tr = p6.population_summary(geo_tr, 'TRAIN')
    pop_va = p6.population_summary(geo_va, 'VAL')
    pop_all = p6.population_summary(geo, 'COMBINED')
    pop_df = pd.DataFrame([pop_tr, pop_va, pop_all])
    p6.write_table(pop_df, 'phase06_kub_v3_population_summary.csv', TABLES)

    # ------------------------------------------------------------------
    # Patient summary (per patient burden, split-aware)
    # ------------------------------------------------------------------
    pat_rows = []
    for sp, sub in geo.groupby('split'):
        per = sub.groupby('patient_id').size()
        for pid, n in per.items():
            pat_rows.append({
                'split': sp,
                'patient_id': pid,
                'cases': int(n),
                'categories': '|'.join(sorted(sub[sub.patient_id == pid]['category'].unique())),
                'acquisitions': '|'.join(sorted(sub[sub.patient_id == pid]['acquisition_type'].unique())),
            })
    pat_df = pd.DataFrame(pat_rows).sort_values(['split', 'patient_id']).reset_index(drop=True)
    p6.write_table(pat_df, 'phase06_kub_v3_patient_summary.csv', TABLES)

    # ------------------------------------------------------------------
    # Image geometry summary (quantiles + frequency table)
    # ------------------------------------------------------------------
    series = {'TRAIN': geo_tr, 'VAL': geo_va, 'COMBINED': geo}
    img_q = p6.image_geometry_quantile_table(series)
    p6.write_table(img_q, 'phase06_kub_v3_image_geometry_summary.csv', TABLES)

    # ------------------------------------------------------------------
    # Mask geometry summary (quantiles of all mask metrics)
    # ------------------------------------------------------------------
    mask_q = p6.mask_geometry_quantile_table(series)
    p6.write_table(mask_q, 'phase06_kub_v3_mask_geometry_summary.csv', TABLES)

    # ------------------------------------------------------------------
    # Category + acquisition summaries
    # ------------------------------------------------------------------
    cat_df = p6.category_summary(geo)
    p6.write_table(cat_df, 'phase06_kub_v3_category_summary.csv', TABLES)

    acq_df = p6.acquisition_summary(geo)
    p6.write_table(acq_df, 'phase06_kub_v3_acquisition_summary.csv', TABLES)

    # ------------------------------------------------------------------
    # Combined geometry quantiles table
    # ------------------------------------------------------------------
    geo_q = p6.geometry_quantile_table(series)
    p6.write_table(geo_q, 'phase06_kub_v3_geometry_quantiles.csv', TABLES)

    # ------------------------------------------------------------------
    # Quarantined metadata
    # ------------------------------------------------------------------
    qmeta = p6.quarantined_metadata(kq)
    p6.write_table(qmeta, 'phase06_kub_v3_quarantined_metadata.csv', TABLES)

    # ------------------------------------------------------------------
    # Deterministic sample selection
    # ------------------------------------------------------------------
    sel = p6.deterministic_sample_selection(geo, n_total=16)
    # attach geometry for gallery
    sel_cols = ['selection_rank', 'sample_id', 'split', 'patient_id', 'category',
                'acquisition_type', 'native_resolution', 'fg_pixels', 'fg_fraction',
                'component_count', 'largest_component_pixels', 'bbox_width', 'bbox_height',
                'bbox_area_fraction', 'equivalent_diameter', 'image_path', 'mask_path']
    sel_out = sel[[c for c in sel_cols if c in sel.columns]]
    p6.write_table(sel_out, 'phase06_kub_v3_sample_selection.csv', TABLES)
    selection_sha = p6.sha256_of_strings(sel_out['sample_id'].tolist())

    # ------------------------------------------------------------------
    # Figures (embedded in notebook later; also saved here)
    # ------------------------------------------------------------------
    FIGDIR.mkdir(parents=True, exist_ok=True)
    _make_figures(geo, geo_tr, geo_va, cat_df, acq_df)

    # Normalized category + stratified geometry figures
    p6.save_fig(p6.plot_category_normalized(geo),
                FIGDIR / 'phase06_kub_v3_category_normalized.png')
    p6.save_fig(p6.plot_stratified_geometry(geo, 'acquisition_type', 'fg_fraction'),
                FIGDIR / 'phase06_kub_v3_stratified_acquisition_fg.png')
    p6.save_fig(p6.plot_stratified_geometry(geo, 'category', 'fg_fraction'),
                FIGDIR / 'phase06_kub_v3_stratified_category_fg.png')

    # Deterministic paginated medical gallery (3 panels per case: image/GT/overlay)
    gal_figs = p6.plot_gallery_pages(
        sel_out, cases_per_page=4,
        title='Phase 06 — KUB clean-v3 deterministic gallery (TRAIN/VAL only)')
    for i, f in enumerate(gal_figs, 1):
        p6.save_fig(f, FIGDIR / f'phase06_kub_v3_medical_gallery_page{i:02d}.png')

    # ------------------------------------------------------------------
    # Resolution summary
    # ------------------------------------------------------------------
    res_df = p6.resolution_summary(geo)
    comp_df = p6.component_structure_summary(geo)
    stab_df = p6.stability_comparison(geo)

    # Mask label vocabulary (documents the raw labels behind binary `mask > 0`)
    label_vocab_df = p6.mask_label_vocabulary(geo[['split', 'category', 'mask_path']])
    p6.write_table(label_vocab_df, 'phase06_kub_v3_mask_label_vocabulary.csv', TABLES)

    # Acquisition-regime geometry (bimodal: ROI crops vs FULL_FIELD images)
    regime_df = p6.acquisition_regime_geometry(geo)
    p6.write_table(regime_df, 'phase06_kub_v3_acquisition_regime_geometry.csv', TABLES)

    # Stratified geometry (split x acquisition_type, split x category)
    strat_df = p6.stratified_geometry_summary(geo)
    p6.write_table(strat_df, 'phase06_kub_v3_stratified_geometry_summary.csv', TABLES)

    # Exact percentage-point differences (descriptive, no significance test).
    # These are displayed in the notebook and recorded in the audit JSON;
    # they are not separate table artifacts, keeping the registry at 12.
    cat_pp = p6.percentage_point_differences(geo, 'category')
    acq_pp = p6.percentage_point_differences(geo, 'acquisition_type')
    max_cat_pp = float(cat_pp['abs_diff_pp'].max())
    max_acq_pp = float(acq_pp['abs_diff_pp'].max())

    # ------------------------------------------------------------------
    # Summary metrics for the note
    # ------------------------------------------------------------------
    def qs(col, split=None):
        s = geo if split is None else geo[geo.split == split]
        return {lab: float(np.quantile(s[col].dropna(), q)) for q, lab in zip(p6.QUANTILES, p6.QUANTILE_LABELS)}

    note = {
        'ff': qs('fg_fraction'),
        'lc': qs('largest_component_pixels'),
        'bb': qs('bbox_area_fraction'),
        'resolutions': res_df.to_dict('records'),
        'components': comp_df.to_dict('records'),
        'cat': cat_df.to_dict('records'),
        'acq': acq_df.to_dict('records'),
    }

    # ------------------------------------------------------------------
    # Audit artifact
    # ------------------------------------------------------------------
    audit = {
        'audit': 'phase06_kub_v3_characterization_audit',
        'phase': '06 — KUB Dataset Characterization (Part 1A)',
        'model': 'Gemini 3.8 Flash Medium',
        'generated_at': now,
        'manifest_version': p6.ACTIVE_MANIFEST_VERSION,
        'historical_manifest_version': p6.HISTORICAL_MANIFEST_VERSION,
        'manifest_hashes': p6.manifest_hashes(),
        'test_sha': p6.TEST_SHA,
        'kub_counts': {
            'TRAIN': int(len(ktr)),
            'VAL': int(len(kva)),
            'TEST': int(len(ktest)),
            'QUARANTINED': int(len(kq)),
        },
        'patient_counts': {
            'TRAIN': int(ktr['patient_id'].nunique()),
            'VAL': int(kva['patient_id'].nunique()),
            'train_val_overlap': integ['train_val_patient_overlap'],
        },
        'integrity_gates': integ,
        'images_read_from_train': int(len(ktr)),
        'images_read_from_val': int(len(kva)),
        'images_read_total': int(len(ktr) + len(kva)),
        'test_content_reads': 0,
        'test_visualizations': 0,
        'test_metrics': 0,
        'test_metadata_only': True,
        'sample_selection_sha': selection_sha,
        'table_hashes': {name: p6.sha256_file(TABLES / name)
                         for name in p6.FINAL_TABLES if (TABLES / name).exists()},
        'table_count': sum(1 for n in p6.FINAL_TABLES if (TABLES / n).exists()),
        'mask_foreground_rule': 'mask > 0',
        'mask_label_vocabulary_table': 'reports/tables/phase06_kub_v3_mask_label_vocabulary.csv',
        'mask_label_vocabulary_sha': p6.sha256_file(TABLES / 'phase06_kub_v3_mask_label_vocabulary.csv'),
        'acquisition_regime_table': 'reports/tables/phase06_kub_v3_acquisition_regime_geometry.csv',
        'acquisition_regime_sha': p6.sha256_file(TABLES / 'phase06_kub_v3_acquisition_regime_geometry.csv'),
        'stratified_geometry_table': 'reports/tables/phase06_kub_v3_stratified_geometry_summary.csv',
        'stratified_geometry_sha': p6.sha256_file(TABLES / 'phase06_kub_v3_stratified_geometry_summary.csv'),
        'max_category_pp_difference': max_cat_pp,
        'max_acquisition_pp_difference': max_acq_pp,
        'multi_component_train_pct': float(100.0 * (geo_tr['component_count'] >= 2).sum() / len(geo_tr)),
        'multi_component_val_pct': float(100.0 * (geo_va['component_count'] >= 2).sum() / len(geo_va)),
        'category_pp_table': cat_pp.to_dict('records'),
        'acquisition_pp_table': acq_pp.to_dict('records'),
        'figures': sorted(p.name for p in FIGDIR.glob('*.png')),
        'figure_count': len(list(FIGDIR.glob('*.png'))),
        'tiny_threshold_defined': False,
        'phase07_started': False,
        'phase07_governance_rule': (
            'Phase 07 must NOT choose a tiny-object threshold by optimizing against VAL. '
            'The prospective tiny-object definition must be frozen using TRAIN-only empirical '
            'geometry and/or predeclared domain/geometric rationale before examining VAL '
            'prevalence/results under that threshold.'),
        'notebook_execution_state': 'SEE CLOSURE NOTEBOOK',
        'summary': note,
    }
    AUDITS.mkdir(parents=True, exist_ok=True)
    (AUDITS / 'phase06_kub_v3_characterization_audit.json').write_text(
        json.dumps(audit, indent=2), encoding='utf-8')

    md = [
        '# Phase 06 Part 1A — KUB v3 Characterization Audit', '',
        f"**Generated:** {now}  ",
        f"**Model:** Gemini 3.8 Flash Medium  ",
        f"**Active manifest:** `{p6.ACTIVE_MANIFEST_VERSION}`  ",
        f"**Historical manifest:** `{p6.HISTORICAL_MANIFEST_VERSION}`", '',
        '## KUB Counts', '',
        '| Split | Count |', '|---|---|',
        f"| TRAIN | {len(ktr)} |", f"| VAL | {len(kva)} |",
        f"| TEST (metadata only) | {len(ktest)} |", f"| QUARANTINED | {len(kq)} |", '',
        '## Patient Counts', '',
        f"- KUB TRAIN unique patients: {ktr['patient_id'].nunique()}",
        f"- KUB VAL unique patients: {kva['patient_id'].nunique()}",
        f"- TRAIN/VAL patient overlap: {integ['train_val_patient_overlap']}", '',
        '## Integrity Gates', '',
        '| Gate | Result |', '|---|---|',
    ]
    for k, v in integ.items():
        if isinstance(v, (bool, int, float, str)):
            md.append(f'| {k} | {v} |')
    md += ['', '## TEST Lock', '',
           '- TEST content reads: 0',
           '- TEST visualizations: 0',
           '- TEST metrics: 0',
           '- TEST referenced via manifest metadata only: YES', '',
           '## Artifacts', '',
           f'- Sample selection SHA: `{selection_sha}`',
           f'- Tables written: {len(audit["table_hashes"])}',
           f'- Figures: {audit["figure_count"]}', '',
           '## Gates', '',
           '- Tiny threshold defined: NO',
           '- Phase 07 started: NO', '']
    (AUDITS / 'phase06_kub_v3_characterization_audit.md').write_text('\n'.join(md), encoding='utf-8')

    # ------------------------------------------------------------------
    # Console report
    # ------------------------------------------------------------------
    print('=' * 70)
    print('PHASE 06 PART 1A — CHARACTERIZATION DRIVER')
    print('=' * 70)
    print('KUB TRAIN / VAL / TEST / QUAR     :', len(ktr), len(kva), len(ktest), len(kq))
    print('TRAIN patients / VAL patients     :', ktr['patient_id'].nunique(), kva['patient_id'].nunique())
    print('TRAIN-VAL patient overlap         :', integ['train_val_patient_overlap'])
    print('pairs checked                     :', integ.get('pairs_checked'))
    print('missing img/msk / invalid / empty :', integ['missing_images'], integ['missing_masks'],
          integ.get('invalid_masks'), integ.get('empty_masks'))
    print('dimension mismatch / unreadable   :', integ.get('dimension_mismatch'), integ.get('unreadable_pairs'))
    print('all integrity gates pass          :', integ['all_gates_pass'])
    print('multi-component cases             :', int((geo['component_count'] >= 2).sum()))
    print('category counts                   :', geo['category'].value_counts().to_dict())
    print('acquisition counts                :', geo['acquisition_type'].value_counts().to_dict())
    print('selection SHA                     :', selection_sha)
    print('gallery cases                     :', len(sel_out))
    print('gallery pages                     :', len(gal_figs))
    print('figures written                   :', audit['figure_count'])
    print('tables registered                 :', audit['table_count'])
    print('max category pp diff              :', round(max_cat_pp, 4))
    print('max acquisition pp diff           :', round(max_acq_pp, 4))
    print('multi-component TRAIN / VAL %     :',
          round(audit['multi_component_train_pct'], 4),
          '/', round(audit['multi_component_val_pct'], 4))
    print('NOTE: tiny threshold defined = NO | Phase 07 started = NO')
    print('=' * 70)

    return audit


def _make_figures(geo, geo_tr, geo_va, cat_df, acq_df):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from PIL import Image

    # 1. population composition
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    comp = pd.DataFrame({
        'split': ['TRAIN', 'VAL', 'COMBINED'],
        'cases': [len(geo_tr), len(geo_va), len(geo)],
        'patients': [geo_tr.patient_id.nunique(), geo_va.patient_id.nunique(), geo.patient_id.nunique()],
    })
    x = np.arange(len(comp))
    ax.bar(x - 0.2, comp['cases'], 0.4, label='cases', color='#2f7ed8')
    ax.bar(x + 0.2, comp['patients'], 0.4, label='unique patients', color='#e08a3c')
    for i, (c, p) in enumerate(zip(comp['cases'], comp['patients'])):
        ax.annotate(str(c), (i - 0.2, c), ha='center', va='bottom', fontsize=9)
        ax.annotate(str(p), (i + 0.2, p), ha='center', va='bottom', fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(comp['split'])
    ax.set_title('KUB v3 population composition (CLEAN-v3)')
    ax.legend(frameon=False)
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_population_composition.png')

    # 2. category distribution
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    cats = p6.CATEGORIES
    tr_c = [int((geo_tr.category == c).sum()) for c in cats]
    va_c = [int((geo_va.category == c).sum()) for c in cats]
    x = np.arange(len(cats))
    ax.bar(x - 0.2, tr_c, 0.4, label='TRAIN', color='#2f7ed8')
    ax.bar(x + 0.2, va_c, 0.4, label='VAL', color='#4a9d5f')
    ax.set_xticks(x); ax.set_xticklabels([c.replace('_', ' ') for c in cats])
    ax.set_title('Anatomical category distribution (metadata, not pixel classes)')
    ax.legend(frameon=False)
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_category_distribution.png')

    # 3. acquisition distribution
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    acqs = sorted(geo['acquisition_type'].unique())
    tr_a = [int((geo_tr.acquisition_type == a).sum()) for a in acqs]
    va_a = [int((geo_va.acquisition_type == a).sum()) for a in acqs]
    x = np.arange(len(acqs))
    ax.bar(x - 0.2, tr_a, 0.4, label='TRAIN', color='#2f7ed8')
    ax.bar(x + 0.2, va_a, 0.4, label='VAL', color='#4a9d5f')
    ax.set_xticks(x); ax.set_xticklabels(acqs)
    ax.set_title('Acquisition / crop-type distribution')
    ax.legend(frameon=False)
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_acquisition_distribution.png')

    # 4. native resolution
    fig, ax = plt.subplots(figsize=(7.2, 4.0))
    res = geo['native_resolution'].value_counts()
    ax.bar(range(len(res)), res.values, color='#7a6bb5')
    ax.set_xticks(range(len(res))); ax.set_xticklabels(res.index, rotation=30, ha='right')
    for i, v in enumerate(res.values):
        ax.annotate(str(v), (i, v), ha='center', va='bottom', fontsize=9)
    ax.set_title('Native resolution distribution')
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_native_resolution.png')

    # 5. foreground fraction distribution
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    ax.hist(geo_tr['fg_fraction'], bins=60, alpha=0.6, label='TRAIN', color='#2f7ed8')
    ax.hist(geo_va['fg_fraction'], bins=60, alpha=0.6, label='VAL', color='#e08a3c')
    ax.set_yscale('log')
    ax.set_xlabel('foreground fraction'); ax.set_ylabel('cases (log)')
    ax.set_title('Foreground-fraction distribution (log scale)')
    ax.legend(frameon=False)
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_fg_fraction_distribution.png')

    # 6. largest-component size
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    tr = geo_tr['largest_component_pixels'].replace(0, np.nan).dropna()
    va = geo_va['largest_component_pixels'].replace(0, np.nan).dropna()
    ax.hist(tr, bins=np.logspace(0, 6, 60), alpha=0.6, label='TRAIN', color='#2f7ed8')
    ax.hist(va, bins=np.logspace(0, 6, 60), alpha=0.6, label='VAL', color='#e08a3c')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('largest-component pixels'); ax.set_ylabel('cases (log)')
    ax.set_title('Largest-component size distribution (log-log)')
    ax.legend(frameon=False)
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_largest_component_distribution.png')

    # 7. bbox size
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.scatter(geo['bbox_width'], geo['bbox_height'], s=6, alpha=0.35, c='#2f7ed8')
    ax.set_xscale('symlog'); ax.set_yscale('symlog')
    ax.set_xlabel('bbox width (px)'); ax.set_ylabel('bbox height (px)')
    ax.set_title('Foreground bounding-box dimensions (TRAIN + VAL)')
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_bbox_size_distribution.png')

    # 8. component count
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    cc = geo['component_count'].value_counts().sort_index()
    ax.bar(cc.index.astype(str), cc.values, color='#4a9d5f')
    for i, v in enumerate(cc.values):
        ax.annotate(str(v), (i, v), ha='center', va='bottom', fontsize=9)
    ax.set_xlabel('connected components per mask'); ax.set_ylabel('cases')
    ax.set_title('Connected-component count distribution')
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_component_count_distribution.png')

    # 9. TRAIN vs VAL geometry comparison (quantile curves)
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    qs = np.linspace(0.01, 0.99, 99)
    for label, df, color in [('TRAIN', geo_tr, '#2f7ed8'), ('VAL', geo_va, '#e08a3c')]:
        s = df['fg_fraction'].dropna()
        ax.plot(qs, np.quantile(s, qs), label=label, color=color, lw=2)
    ax.set_xlabel('quantile'); ax.set_ylabel('foreground fraction')
    ax.set_title('TRAIN vs VAL foreground-fraction quantile curves')
    ax.legend(frameon=False)
    p6.save_fig(fig, FIGDIR / 'phase06_kub_v3_train_val_geometry_comparison.png')


if __name__ == '__main__':
    main()
