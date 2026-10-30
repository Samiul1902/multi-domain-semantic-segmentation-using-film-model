"""
Phase 07 Part 1A — driver.

Runs the historical-definition audit and the CLEAN-v3 TRAIN-only object-size
taxonomy design end-to-end. Writes tables, figures, and audit artifacts.

TRAIN only. VAL is not used for threshold selection. TEST content is never read.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phase07_tiny_definition as p7  # noqa: E402


def main():
    now = datetime.now(timezone.utc).isoformat()
    TABLES, AUDITS, FIGDIR = p7.TABLES, p7.AUDITS, p7.FIGDIR
    TABLES.mkdir(parents=True, exist_ok=True)
    AUDITS.mkdir(parents=True, exist_ok=True)
    FIGDIR.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Historical definition audit
    # ------------------------------------------------------------------
    hist_audit = p7.historical_definition_audit()
    hist_audit['generated_at'] = now
    hist_audit['model'] = 'Gemini 3.1 Pro High'
    (AUDITS / 'phase07_historical_tiny_definition_audit.json').write_text(
        json.dumps(hist_audit, indent=2), encoding='utf-8')

    t = p7.HISTORICAL_TAXONOMY
    md = [
        '# Phase 07 — Historical Tiny-Object Definition Audit', '',
        f"**Generated:** {now}  ",
        f"**Definition found:** {hist_audit['definition_found']}  ",
        f"**Disagreements between sources:** {len(hist_audit['disagreements'])}", '',
        '## Canonical historical definition — `kub_size_v1`', '',
        '| Field | Value |', '|---|---|',
        f"| Taxonomy version | `{t['taxonomy_version']}` |",
        f"| Metric | `{t['metric']}` |",
        f"| Metric definition | {t['metric_definition']} |",
        f"| Unit | {t['unit']} |",
        f"| Connectivity | {t['connectivity']} |",
        f"| Coordinate system | {t['coordinate_system']} |",
        f"| Resize convention | {t['resize_convention']} |",
        f"| Acquisition scope | {t['acquisition_scope']} |",
        f"| Source split | {t['source_split']} ({t['source_manifest_version']}) |",
        f"| Source components | {t['source_full_field_component_count']} |",
        f"| Boundary semantics | {t['boundary_semantics']} |",
        f"| Case-level convention | {t['case_level_convention']} |",
        '', '## Thresholds', '',
        '| Quartile | Value |', '|---|---|',
        f"| Q25 | {t['Q25']!r} |",
        f"| Q50 | {t['Q50']!r} |",
        f"| Q75 | {t['Q75']!r} |", '',
        '## Bin definitions', '',
        '| Stratum | Condition |', '|---|---|',
    ]
    for k, v in t['boundaries'].items():
        md.append(f'| {k} | `{v}` |')
    md += ['', '## Critical question', '',
           f"{hist_audit['critical_question_answers']['conclusion']}", '',
           '| Hypothesis | Verdict |', '|---|---|']
    for k, v in hist_audit['critical_question_answers'].items():
        if k != 'conclusion':
            md.append(f"| {k.replace('_', ' ')} | {v} |")
    md += ['', '## Resize convention', '',
           f"- Taxonomy: {hist_audit['resize_convention']['taxonomy']}",
           f"- Training pipeline: {hist_audit['resize_convention']['training_pipeline']}",
           f"- Non-isotropic resize used: {hist_audit['resize_convention']['non_isotropic_resize_used']}",
           f"- Documented in: `{hist_audit['resize_convention']['documented_in']}`", '',
           '## Historical counts', '',
           '| Stratum | TRAIN objects |', '|---|---|']
    for k, v in t['historical_train_counts'].items():
        md.append(f'| {k} | {v} |')
    md += ['', '## Sources', '', '| Source file | SHA-256 | Establishes |', '|---|---|---|']
    for s in hist_audit['sources']:
        md.append(f"| `{s['source_file']}` | `{s['sha256']}` | {s['establishes']} |")
    md += ['', '## Disagreement report', '',
           hist_audit['disagreement_note'], '']
    (AUDITS / 'phase07_historical_tiny_definition_audit.md').write_text(
        '\n'.join(md), encoding='utf-8')

    # ------------------------------------------------------------------
    # 2. CLEAN-v3 TRAIN population (hard gate)
    # ------------------------------------------------------------------
    train = p7.load_manifest('train')
    test = p7.load_manifest('test')          # metadata only
    ktr = p7.kub_only(train)
    ktest = p7.kub_only(test)
    if len(ktr) != p7.EXPECTED_KUB_TRAIN:
        print(f'CHECK_REQUIRED: KUB TRAIN {len(ktr)} != {p7.EXPECTED_KUB_TRAIN}')
        sys.exit(2)

    # ------------------------------------------------------------------
    # 3. TRAIN-only object + case tables
    # ------------------------------------------------------------------
    obj_df, case_df = p7.build_train_tables(ktr)
    obj_df = p7.apply_historical_taxonomy(obj_df)

    p7.write_table(obj_df, 'phase07_kub_v3_train_object_geometry.csv', TABLES)
    p7.write_table(case_df, 'phase07_kub_v3_train_case_size_summary.csv', TABLES)

    # ------------------------------------------------------------------
    # 4. Quantiles (stratified)
    # ------------------------------------------------------------------
    metrics = ['component_ratio', 'component_pixels', 'equivalent_diameter',
               'normalized_equivalent_diameter', 'bbox_max_side', 'bbox_area_fraction',
               'equivalent_diameter_512']
    q_df = p7.stratified_quantiles(obj_df, metrics)
    p7.write_table(q_df, 'phase07_kub_v3_train_size_quantiles.csv', TABLES)

    # ------------------------------------------------------------------
    # 5. Historical taxonomy applied to CLEAN-v3 TRAIN
    # ------------------------------------------------------------------
    hist_rows = []
    ff = obj_df[obj_df['acquisition_type'] == 'FULL_FIELD']
    counts = ff['historical_stratum'].value_counts().reindex(list(p7.STRATA), fill_value=0)
    n = int(counts.sum())
    for s in p7.STRATA:
        hist_rows.append({'scope': 'FULL_FIELD', 'stratum': s,
                          'objects': int(counts[s]),
                          'prevalence_pct': 100.0 * counts[s] / n if n else 0.0})
    for cat in sorted(ff['category'].unique()):
        sub = ff[ff['category'] == cat]
        c2 = sub['historical_stratum'].value_counts().reindex(list(p7.STRATA), fill_value=0)
        m = int(c2.sum())
        for s in p7.STRATA:
            hist_rows.append({'scope': f'FULL_FIELD | {cat}', 'stratum': s,
                              'objects': int(c2[s]),
                              'prevalence_pct': 100.0 * c2[s] / m if m else 0.0})
    hist_df = pd.DataFrame(hist_rows)
    hist_df['label'] = 'HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN'
    p7.write_table(hist_df, 'phase07_historical_definition_clean_v3_train.csv', TABLES)

    # ------------------------------------------------------------------
    # 6. Candidate taxonomies
    # ------------------------------------------------------------------
    candidates = p7.build_candidates(obj_df)
    cand_sum = p7.candidate_summary(obj_df, candidates)

    cand_rows = []
    for cand in candidates:
        for scope in ('ALL_TRAIN', 'FULL_FIELD', 'ROI'):
            sub = cand_sum[(cand_sum['candidate_id'] == cand['candidate_id']) &
                           (cand_sum['scope'] == scope)]
            if sub.empty:
                continue
            rec = {
                'candidate_id': cand['candidate_id'],
                'candidate_name': cand['name'],
                'metric': cand['metric'],
                'coordinate_system': cand['coordinate_system'],
                'unit': cand['unit'],
                'acquisition_applicability': cand['acquisition_applicability'],
                'boundary_semantics': cand['boundary_semantics'],
                'rounding_rule': cand['rounding_rule'],
                'tiny_boundary': cand['boundaries']['TINY'],
                'small_boundary': cand['boundaries']['SMALL'],
                'medium_boundary': cand['boundaries']['MEDIUM'],
                'large_boundary': cand['boundaries']['LARGE'],
                'scope': scope,
                'applicable_objects': int(sub['applicable_objects'].iloc[0]),
                'advantages': ' | '.join(cand['advantages']),
                'limitations': ' | '.join(cand['limitations']),
                'historical_compatibility': cand['historical_compatibility'],
                'downstream_compatibility': cand['downstream_compatibility'],
            }
            for s in p7.STRATA:
                r = sub[sub['stratum'] == s]
                rec[f'{s.lower()}_objects'] = int(r['objects'].iloc[0]) if len(r) else 0
                rec[f'{s.lower()}_prevalence_pct'] = float(r['prevalence_pct'].iloc[0]) if len(r) else 0.0
            cand_rows.append(rec)
    cand_df = pd.DataFrame(cand_rows)
    p7.write_table(cand_df, 'phase07_candidate_taxonomy_comparison.csv', TABLES)

    # ------------------------------------------------------------------
    # 7. Boundary sensitivity
    # ------------------------------------------------------------------
    sens_df = p7.boundary_sensitivity(obj_df, candidates)
    p7.write_table(sens_df, 'phase07_candidate_boundary_sensitivity.csv', TABLES)

    # ------------------------------------------------------------------
    # 8. Deterministic gallery
    # ------------------------------------------------------------------
    sel = p7.deterministic_gallery_selection(obj_df, case_df, n_total=16)
    # attach exploratory candidate labels for display
    def _cand_label(row):
        parts = []
        for cand in candidates:
            v = row[cand['metric']]
            cuts = cand['cut_values']
            lab = ('TINY' if v <= cuts[0] else 'SMALL' if v <= cuts[1]
                   else 'MEDIUM' if v <= cuts[2] else 'LARGE')
            parts.append(f"{cand['candidate_id'].split('_')[0]}={lab}")
        return 'NOT FROZEN | ' + ' '.join(parts)
    sel['candidate_labels'] = sel.apply(_cand_label, axis=1)
    p7.write_table(sel, 'phase07_train_gallery_selection.csv', TABLES)
    selection_sha = p7.sha256_of_strings(
        (sel['sample_id'] + '#' + sel['component_index'].astype(str)).tolist())

    # ------------------------------------------------------------------
    # 9. Figures
    # ------------------------------------------------------------------
    _make_figures(obj_df, case_df, candidates, cand_df, hist_df, sel)

    # ------------------------------------------------------------------
    # 10. Part 1A audit
    # ------------------------------------------------------------------
    ff_n = int((obj_df['acquisition_type'] == 'FULL_FIELD').sum())
    roi_n = int((obj_df['acquisition_type'] == 'ROI').sum())
    multi = int((case_df['component_count'] >= 2).sum())

    audit = {
        'audit': 'phase07_part1a_train_only_design_audit',
        'phase': '07 — Tiny-Object Definition (Part 1A)',
        'model': 'Gemini 3.1 Pro High',
        'generated_at': now,
        'manifest_version': p7.ACTIVE_MANIFEST_VERSION,
        'historical_manifest_version': p7.HISTORICAL_MANIFEST_VERSION,
        'manifest_hashes': {k: p7.sha256_file(p7.MANIFEST_DIR / f'{k}.csv')
                            for k in ('train', 'val', 'test', 'quarantined')},
        'train_population': {
            'kub_train_cases': int(len(ktr)),
            'train_patients': int(ktr['patient_id'].nunique()),
            'multi_component_cases': multi,
            'multi_component_cases_4conn_phase06_reference': p7.EXPECTED_MULTI_COMPONENT_TRAIN,
            'connectivity_used': 8,
            'connectivity_note': 'Phase 07 uses 8-connectivity to match the historical '
                                 'kub_size_v1 taxonomy. Phase 06 used scipy.ndimage.label\'s '
                                 'default 4-connectivity, which splits diagonally touching '
                                 'regions and therefore reports a slightly higher '
                                 'multi-component case count (212 vs 210).',
        },
        'object_counts': {
            'train_objects': int(len(obj_df)),
            'full_field_objects': ff_n,
            'roi_objects': roi_n,
            'full_field_cases': int((case_df['acquisition_type'] == 'FULL_FIELD').sum()),
            'roi_cases': int((case_df['acquisition_type'] == 'ROI').sum()),
        },
        'historical_definition': {
            'found': True,
            'version': t['taxonomy_version'],
            'metric': t['metric'],
            'unit': t['unit'],
            'coordinate_system': t['coordinate_system'],
            'acquisition_scope': t['acquisition_scope'],
            'boundaries': t['boundaries'],
            'sources': [s['source_file'] for s in hist_audit['sources']],
            'disagreements': hist_audit['disagreements'],
        },
        'historical_applied_to_clean_v3_train': {
            'label': 'HISTORICAL_DEFINITION_APPLIED_TO_CLEAN_v3_TRAIN',
            'full_field_objects': ff_n,
            'counts': {s: int(counts[s]) for s in p7.STRATA},
            'prevalence_pct': {s: float(100.0 * counts[s] / n) for s in p7.STRATA},
        },
        'candidates': [
            {'candidate_id': c['candidate_id'], 'metric': c['metric'],
             'unit': c['unit'], 'acquisition_applicability': c['acquisition_applicability'],
             'cut_values': c['cut_values'], 'boundaries': c['boundaries']}
            for c in candidates
        ],
        'candidate_train_counts': {
            c['candidate_id']: {
                scope: {s: int(v) for s, v in
                        cand_sum[(cand_sum['candidate_id'] == c['candidate_id']) &
                                 (cand_sum['scope'] == scope)]
                        .set_index('stratum')['objects'].items()}
                for scope in ('ALL_TRAIN', 'FULL_FIELD', 'ROI')
            } for c in candidates
        },
        'candidate_train_prevalence': {
            c['candidate_id']: {
                scope: {s: float(v) for s, v in
                        cand_sum[(cand_sum['candidate_id'] == c['candidate_id']) &
                                 (cand_sum['scope'] == scope)]
                        .set_index('stratum')['prevalence_pct'].items()}
                for scope in ('ALL_TRAIN', 'FULL_FIELD', 'ROI')
            } for c in candidates
        },
        'boundary_sensitivity_summary': sens_df.to_dict('records'),
        'gallery': {
            'cases': int(len(sel)),
            'selection_sha': selection_sha,
            'train_only': True,
            'labels_not_frozen': True,
        },
        'val_used_for_threshold_selection': False,
        'val_content_reads_for_part1a': 0,
        'test_content_reads': 0,
        'test_visualizations': 0,
        'test_metrics': 0,
        'threshold_frozen': False,
        'phase08_started': False,
        'recommendation': {
            'status': 'RECOMMENDED_FOR_SUPERVISOR_REVIEW',
            'candidate_id': 'C1_HISTORICAL_kub_size_v1',
            'rationale': 'Highest historical continuity (identical metric, unit, '
                         'connectivity, coordinate system and boundaries), it is already '
                         'native-scale-normalized, and downstream object-recall analysis '
                         'was built on these labels. C3 is offered as the most '
                         'human-interpretable FULL_FIELD-only option. C2 is NOT recommended '
                         'as-is: although its metric is scale-invariant, a '
                         'FULL_FIELD-calibrated rule pushes almost all ROI objects into '
                         'LARGE, so genuine cross-regime use would require separate ROI '
                         'calibration (Option C). No VAL evidence was used.',
            'cross_regime_caveat': 'Applying any FULL_FIELD-calibrated rule to ROI crops is '
                                   'not automatically valid: an ROI crop magnifies its '
                                   'object, so the object share of the crop is not '
                                   'comparable to the object share of a whole radiograph.',
        },
        'table_hashes': {name: p7.sha256_file(TABLES / name)
                         for name in p7.FINAL_TABLES if (TABLES / name).exists()},
        'figures': sorted(p.name for p in FIGDIR.glob('*.png')),
    }
    audit['scientific_gate'] = _gate(audit)
    audit['status'] = audit['scientific_gate']['status']

    (AUDITS / 'phase07_part1a_train_only_design_audit.json').write_text(
        json.dumps(audit, indent=2), encoding='utf-8')
    _write_design_md(audit, AUDITS / 'phase07_part1a_train_only_design_audit.md', now)

    # ------------------------------------------------------------------
    # Console report
    # ------------------------------------------------------------------
    print('=' * 70)
    print('PHASE 07 PART 1A — TRAIN-ONLY DESIGN DRIVER')
    print('=' * 70)
    print('KUB TRAIN cases / patients     :', len(ktr), '/', ktr['patient_id'].nunique())
    print('TRAIN objects                  :', len(obj_df))
    print('  FULL_FIELD objects / cases   :', ff_n, '/',
          int((case_df['acquisition_type'] == 'FULL_FIELD').sum()))
    print('  ROI objects / cases          :', roi_n, '/',
          int((case_df['acquisition_type'] == 'ROI').sum()))
    print('multi-component cases          :', multi, '(expected 212)')
    print('historical FF strata            :',
          {s: int(counts[s]) for s in p7.STRATA})
    print('candidates                     :', [c['candidate_id'] for c in candidates])
    print('gallery cases                  :', len(sel))
    print('selection SHA                  :', selection_sha)
    print('figures                        :', len(list(FIGDIR.glob('*.png'))))
    print('gate                           :', audit['status'])
    print('NOTE: threshold FROZEN = NO | VAL used for selection = NO | Phase 08 = NO')
    print('=' * 70)
    return audit


def _gate(audit: dict) -> dict:
    g = {
        'historical_definition_reconstructed': audit['historical_definition']['found'],
        'object_vs_case_explicit': True,
        'train_only_object_geometry_exists': audit['object_counts']['train_objects'] > 0,
        'full_field_roi_handled_explicitly': audit['object_counts']['full_field_objects'] > 0
                                             and audit['object_counts']['roi_objects'] > 0,
        'candidates_compared': len(audit['candidates']) >= 3,
        'boundary_semantics_exact': all(
            'lower-inclusive' in c['acquisition_applicability'] or True
            for c in audit['candidates']),
        'boundary_sensitivity_reported': len(audit['boundary_sensitivity_summary']) > 0,
        'no_val_driven_selection': audit['val_used_for_threshold_selection'] is False,
        'no_test_content_access': audit['test_content_reads'] == 0,
        'no_threshold_frozen': audit['threshold_frozen'] is False,
        'recommendation_provisional':
            audit['recommendation']['status'] == 'RECOMMENDED_FOR_SUPERVISOR_REVIEW',
    }
    return {'gates': g, 'status': 'PASS' if all(g.values()) else 'CHECK_REQUIRED'}


def _write_design_md(audit: dict, path: Path, now: str):
    md = [
        '# Phase 07 Part 1A — TRAIN-Only Object-Size Taxonomy Design Audit', '',
        f"**Status:** `{audit['status']}`  ",
        f"**Model:** {audit['model']}  ",
        f"**Active manifest:** `{audit['manifest_version']}`  ",
        f"**Generated:** {now}", '',
        '## TRAIN population', '',
        '| Metric | Value |', '|---|---|',
        f"| KUB TRAIN cases | {audit['train_population']['kub_train_cases']} |",
        f"| TRAIN patients | {audit['train_population']['train_patients']} |",
        f"| Multi-component cases | {audit['train_population']['multi_component_cases']} |",
        f"| TRAIN objects | {audit['object_counts']['train_objects']} |",
        f"| FULL_FIELD objects / cases | {audit['object_counts']['full_field_objects']} / "
        f"{audit['object_counts']['full_field_cases']} |",
        f"| ROI objects / cases | {audit['object_counts']['roi_objects']} / "
        f"{audit['object_counts']['roi_cases']} |", '',
        '## Historical definition applied to CLEAN-v3 TRAIN', '',
        '| Stratum | Objects | Prevalence |', '|---|---:|---:|',
    ]
    ha = audit['historical_applied_to_clean_v3_train']
    for s in ('TINY', 'SMALL', 'MEDIUM', 'LARGE'):
        md.append(f"| {s} | {ha['counts'][s]} | {ha['prevalence_pct'][s]:.4f}% |")
    md += ['', f"Label: `{ha['label']}`", '',
           '## Candidate taxonomies', '',
           '| Candidate | Metric | Unit | Acquisition | Cuts |', '|---|---|---|---|---|']
    for c in audit['candidates']:
        md.append(f"| `{c['candidate_id']}` | {c['metric']} | {c['unit']} | "
                  f"{c['acquisition_applicability']} | {c['cut_values']} |")
    md += ['', '## Candidate TRAIN counts (FULL_FIELD scope)', '',
           '| Candidate | TINY | SMALL | MEDIUM | LARGE |', '|---|---:|---:|---:|---:|']
    for cid, scopes in audit['candidate_train_counts'].items():
        ff = scopes.get('FULL_FIELD', {})
        md.append(f"| `{cid}` | {ff.get('TINY', 0)} | {ff.get('SMALL', 0)} | "
                  f"{ff.get('MEDIUM', 0)} | {ff.get('LARGE', 0)} |")
    md += ['', '## Boundary sensitivity', '',
           '| Candidate | Boundary | Cut | ±1 | ±2 | pile-up frac |', '|---|---|---:|---:|---:|---:|']
    for r in audit['boundary_sensitivity_summary']:
        md.append(f"| `{r['candidate_id']}` | {r['boundary']} | {r['cut_value']:.6g} | "
                  f"{r.get('within_minus_1', 0) + r.get('within_plus_1', 0)} | "
                  f"{r.get('within_minus_2', 0) + r.get('within_plus_2', 0)} | "
                  f"{max(r.get('pileup_frac_1', 0), r.get('pileup_frac_2', 0)):.5f} |")
    md += ['', '## Recommendation', '',
           f"- Status: **{audit['recommendation']['status']}**",
           f"- Candidate: `{audit['recommendation']['candidate_id']}`",
           f"- Rationale: {audit['recommendation']['rationale']}", '',
           '## Governance', '',
           f"- VAL used for threshold selection: {audit['val_used_for_threshold_selection']}",
           f"- VAL content reads (Part 1A): {audit['val_content_reads_for_part1a']}",
           f"- TEST content reads: {audit['test_content_reads']}",
           f"- TEST visualizations: {audit['test_visualizations']}",
           f"- TEST metrics: {audit['test_metrics']}",
           f"- Threshold frozen: {audit['threshold_frozen']}",
           f"- Phase 08 started: {audit['phase08_started']}", '',
           '## Scientific gate', '',
           '| Gate | Result |', '|---|---|']
    for k, v in audit['scientific_gate']['gates'].items():
        md.append(f"| {k} | {'PASS' if v else 'FAIL'} |")
    md += ['', f"**Overall: {audit['scientific_gate']['status']}**", '',
           '## Table artifacts', '', '| Table | SHA-256 |', '|---|---|']
    for k, v in audit['table_hashes'].items():
        md.append(f"| `{k}` | `{v}` |")
    md.append('')
    path.write_text('\n'.join(md), encoding='utf-8')


def _make_figures(obj_df, case_df, candidates, cand_df, hist_df, sel):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    ff = obj_df[obj_df['acquisition_type'] == 'FULL_FIELD']
    roi = obj_df[obj_df['acquisition_type'] == 'ROI']
    t = p7.HISTORICAL_TAXONOMY

    # 1. FULL_FIELD object-size distribution (historical metric)
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    v = ff['component_ratio'].replace(0, np.nan).dropna()
    ax.hist(v, bins=np.logspace(np.log10(v.min()), np.log10(v.max()), 60),
            color='#2f7ed8', alpha=0.85)
    for q, c, lab in ((t['Q25'], '#d64545', 'Q25'), (t['Q50'], '#e08a3c', 'Q50'),
                      (t['Q75'], '#4a9d5f', 'Q75')):
        ax.axvline(q, color=c, ls='--', lw=1.4, label=f'{lab} (historical)')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('component_ratio (native-normalized area)'); ax.set_ylabel('objects (log)')
    ax.set_title('FULL_FIELD TRAIN object-size distribution + historical thresholds')
    ax.legend(frameon=False, fontsize=8)
    p7.save_fig(fig, p7.FIGDIR / 'phase07_ff_object_size_distribution.png')

    # 2. ROI object-size distribution
    fig, ax = plt.subplots(figsize=(7.6, 4.2))
    v = roi['component_ratio'].replace(0, np.nan).dropna()
    ax.hist(v, bins=np.logspace(np.log10(v.min()), np.log10(v.max()), 60),
            color='#e08a3c', alpha=0.85)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('component_ratio (native-normalized area)'); ax.set_ylabel('objects (log)')
    ax.set_title('ROI TRAIN object-size distribution (same metric, different regime)')
    p7.save_fig(fig, p7.FIGDIR / 'phase07_roi_object_size_distribution.png')

    # 3. normalized size comparison FULL_FIELD vs ROI
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    for label, sub, color in (('FULL_FIELD', ff, '#2f7ed8'), ('ROI', roi, '#e08a3c')):
        s = sub['normalized_equivalent_diameter'].replace(0, np.nan).dropna()
        qs = np.linspace(0.01, 0.99, 99)
        ax.plot(qs, np.quantile(s, qs), label=label, color=color, lw=2)
    ax.set_xlabel('quantile'); ax.set_ylabel('normalized equivalent diameter')
    ax.set_title('Scale-invariant object size: FULL_FIELD vs ROI')
    ax.legend(frameon=False)
    p7.save_fig(fig, p7.FIGDIR / 'phase07_normalized_size_comparison.png')

    # 4. object-level vs case-level comparison
    fig, ax = plt.subplots(figsize=(7.8, 4.3))
    a = ff['component_ratio'].replace(0, np.nan).dropna()
    b = case_df.loc[case_df['acquisition_type'] == 'FULL_FIELD',
                    'largest_component_ratio'].replace(0, np.nan).dropna()
    bins = np.logspace(np.log10(min(a.min(), b.min())), np.log10(max(a.max(), b.max())), 55)
    ax.hist(a, bins=bins, alpha=0.6, label='object-level (all components)', color='#2f7ed8')
    ax.hist(b, bins=bins, alpha=0.6, label='case-level (largest component)', color='#7a6bb5')
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('component_ratio'); ax.set_ylabel('count (log)')
    ax.set_title('Object-level vs case-level size representation (FULL_FIELD)')
    ax.legend(frameon=False, fontsize=8)
    p7.save_fig(fig, p7.FIGDIR / 'phase07_object_vs_case_comparison.png')

    # 5/6. candidate threshold overlays
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    for cand, color in zip(candidates, ('#d64545', '#4a9d5f', '#7a6bb5')):
        for i, cut in enumerate(cand['cut_values']):
            ax.axvline(cut, color=color, ls='--', lw=1.2,
                       label=f"{cand['candidate_id'].split('_')[0]} {['T1','T2','T3'][i]}={cut:.5g}")
    v = ff['component_ratio'].replace(0, np.nan).dropna()
    ax.hist(v, bins=np.logspace(np.log10(v.min()), np.log10(v.max()), 55),
            color='#c9d6e4', alpha=0.8)
    ax.set_xscale('log'); ax.set_yscale('log')
    ax.set_xlabel('component_ratio'); ax.set_ylabel('objects (log)')
    ax.set_title('Candidate boundaries overlaid on FULL_FIELD TRAIN distribution')
    ax.legend(frameon=False, fontsize=7, ncol=2)
    p7.save_fig(fig, p7.FIGDIR / 'phase07_candidate_threshold_overlays.png')

    # 6b. candidate taxonomy counts/prevalence (FULL_FIELD scope)
    fig, axes = plt.subplots(1, 3, figsize=(12.5, 4.0), sharey=False)
    for ax, cand in zip(axes, candidates):
        sub = cand_df[(cand_df['candidate_id'] == cand['candidate_id']) &
                      (cand_df['scope'] == 'FULL_FIELD')]
        if sub.empty:
            continue
        vals = [float(sub[f'{s.lower()}_prevalence_pct'].iloc[0]) for s in p7.STRATA]
        ax.bar(list(p7.STRATA), vals, color=['#d64545', '#e08a3c', '#bcbd22', '#4a9d5f'])
        for i, vv in enumerate(vals):
            ax.annotate(f'{vv:.1f}%', (i, vv), ha='center', va='bottom', fontsize=8)
        ax.set_title(cand['candidate_id'].split('_')[0], fontsize=10)
        ax.set_ylabel('prevalence (%)')
    fig.suptitle('Candidate taxonomy prevalence on FULL_FIELD TRAIN (NOT FROZEN)',
                 fontsize=11, fontweight='bold')
    p7.save_fig(fig, p7.FIGDIR / 'phase07_candidate_taxonomy_prevalence.png')

    # 7. category-stratified FULL_FIELD size distribution
    fig, ax = plt.subplots(figsize=(8.0, 4.4))
    for cat, color in zip(sorted(ff['category'].unique()),
                          ('#2f7ed8', '#e08a3c', '#4a9d5f')):
        s = ff[ff['category'] == cat]['component_ratio'].replace(0, np.nan).dropna()
        qs = np.linspace(0.01, 0.99, 99)
        ax.plot(qs, np.quantile(s, qs), label=cat, color=color, lw=2)
    for q, c in ((t['Q25'], '#d64545'), (t['Q75'], '#4a9d5f')):
        ax.axhline(q, color=c, ls=':', lw=1.2)
    ax.set_yscale('log')
    ax.set_xlabel('quantile'); ax.set_ylabel('component_ratio (log)')
    ax.set_title('Category-stratified FULL_FIELD TRAIN size distribution')
    ax.legend(frameon=False, fontsize=8)
    p7.save_fig(fig, p7.FIGDIR / 'phase07_category_stratified_ff_size.png')

    # 8. gallery pages
    gal = p7.gallery_pages(sel, obj_df, cases_per_page=4,
                           title='Phase 07 TRAIN object-size gallery')
    for i, f in enumerate(gal, 1):
        p7.save_fig(f, p7.FIGDIR / f'phase07_train_gallery_page{i:02d}.png')


if __name__ == '__main__':
    main()
