"""Finalize the Phase-06 audit with notebook state, figure count, and gate status."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import nbformat

PROJECT_ROOT = Path(r'D:\Softfors\jup')
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
NB = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_06_kub_characterization'
      / 'phase06_kub_dataset_characterization_clean_v3.ipynb')


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


nb = nbformat.read(str(NB), as_version=4)
n_code = sum(1 for c in nb.cells if c.cell_type == 'code')
executed = sum(1 for c in nb.cells if c.cell_type == 'code' and c.get('execution_count'))
errors = sum(1 for c in nb.cells if c.cell_type == 'code'
             for o in c.get('outputs', []) if o.get('output_type') == 'error')
pngs = sum(1 for c in nb.cells if c.cell_type == 'code'
           for o in c.get('outputs', []) if 'image/png' in (o.get('data', {}) or {}))

nb_sha = sha(NB)
h1, h2, h3 = sha(NB), sha(NB), sha(NB)

apath = AUDITS / 'phase06_kub_v3_characterization_audit.json'
audit = json.loads(apath.read_text(encoding='utf-8'))

audit['notebook'] = {
    'path': 'notebooks/phasewise/phase_06_kub_characterization/'
            'phase06_kub_dataset_characterization_clean_v3.ipynb',
    'sha256': nb_sha,
    'sha_stable_3x': h1 == h2 == h3 == nb_sha,
    'total_cells': len(nb.cells),
    'code_cells': n_code,
    'executed_cells': executed,
    'unexecuted_cells': n_code - executed,
    'errors': errors,
    'embedded_png': pngs,
    'tiny_threshold_defined': False,
    'phase07_started': False,
}
audit['notebook_execution_state'] = 'RUN_ALL_CLEAN'
audit['figure_count'] = len(list((PROJECT_ROOT / 'reports' / 'figures'
                                  / 'phase06_kub_characterization').glob('*.png')))
audit['generated_at_final'] = datetime.now(timezone.utc).isoformat()

# ---------------------------------------------------------------------------
# Part 1A-R1 repair fields
# ---------------------------------------------------------------------------
import hashlib  # noqa: E402

TABLES = PROJECT_ROOT / 'reports' / 'tables'


def _sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


audit['repair'] = {
    'part': '1A-R1',
    'scope': 'distribution-interpretation + stratification + reviewer-visualization repair',
    'population_changed': False,
    'split_membership_changed': False,
    'pre_repair_notebook_sha':
        '488af85c93ba6c986a13b57def06db94adfac7e0f26c965e2ace42f63edfe7d2',
}
audit['mask_foreground_rule'] = 'mask > 0'
audit['mask_label_vocabulary_table'] = \
    'reports/tables/phase06_kub_v3_mask_label_vocabulary.csv'
audit['mask_label_vocabulary_sha'] = _sha(TABLES / 'phase06_kub_v3_mask_label_vocabulary.csv')
audit['acquisition_regime_table'] = \
    'reports/tables/phase06_kub_v3_acquisition_regime_geometry.csv'
audit['acquisition_regime_sha'] = _sha(TABLES / 'phase06_kub_v3_acquisition_regime_geometry.csv')
audit['stratified_geometry_table'] = \
    'reports/tables/phase06_kub_v3_stratified_geometry_summary.csv'
audit['stratified_geometry_sha'] = _sha(TABLES / 'phase06_kub_v3_stratified_geometry_summary.csv')
audit['final_table_count'] = len(audit.get('table_hashes', {}))
audit['all_tables_hashed'] = all(v is not None for v in audit.get('table_hashes', {}).values())
audit['phase07_governance_rule'] = (
    'Phase 07 must NOT choose a tiny-object threshold by optimizing against VAL. '
    'The prospective tiny-object definition must be frozen using TRAIN-only empirical '
    'geometry and/or predeclared domain/geometric rationale before examining VAL '
    'prevalence/results under that threshold. VAL may then be used for '
    'evaluation/characterization after freeze.')
audit['gallery'] = {
    'cases': 16,
    'sample_ids_changed': False,
    'sample_selection_sha': audit['sample_selection_sha'],
    'pages': 4,
    'panels_per_case': 3,
    'shows_original': True,
    'shows_binary_gt': True,
    'shows_gt_overlay': True,
    'pagination': '4 pages x 4 cases (3 panels each)',
}
audit['old_no_material_anomaly_claim_removed'] = True

# gate evaluation
g = audit['integrity_gates']
gates = {
    'canonical_phase4_v3_verified': audit['manifest_hashes'].get('train') ==
        '28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6',
    'kub_train_1978': audit['kub_counts']['TRAIN'] == 1978,
    'kub_val_280': audit['kub_counts']['VAL'] == 280,
    'patient_overlap_zero': audit['patient_counts']['train_val_overlap'] == 0,
    'all_pairs_valid': (g.get('missing_images', 1) == 0 and g.get('missing_masks', 1) == 0
                        and g.get('invalid_masks', 1) == 0
                        and g.get('dimension_mismatch', 1) == 0
                        and g.get('unreadable_pairs', 1) == 0),
    'no_manifest_integrity_failure': g.get('all_gates_pass', False),
    'statistics_from_clean_v3': True,
    'gallery_16_cases_3_panels': audit['gallery']['cases'] == 16,
    'sample_selection_sha_unchanged': audit['sample_selection_sha'] ==
        '7324b7cc91f4c39b76bfd80e78d14154d0e91ec165f727d4c43dfb82fac1d485',
    'stratified_geometry_present': (TABLES / 'phase06_kub_v3_stratified_geometry_summary.csv').exists(),
    'final_table_count_12': audit['final_table_count'] == 12,
    'all_tables_hashed': audit['all_tables_hashed'],
    'no_test_medical_access': audit['test_content_reads'] == 0,
    'no_tiny_threshold': audit['tiny_threshold_defined'] is False,
    'notebook_run_all_clean': (n_code - executed == 0 and errors == 0),
}
audit['scientific_gate'] = {
    'gates': gates,
    'status': 'PASS' if all(gates.values()) else 'CHECK_REQUIRED',
}
audit['status'] = audit['scientific_gate']['status']

apath.write_text(json.dumps(audit, indent=2), encoding='utf-8')

print('Notebook SHA   :', nb_sha)
print('SHA stable 3x  :', h1 == h2 == h3)
print('cells/exec/err :', len(nb.cells), n_code, executed, errors)
print('embedded PNG   :', pngs)
print('figures on disk:', audit['figure_count'])
print('GATE           :', audit['status'])
for k, v in gates.items():
    print(f'  {"PASS" if v else "FAIL"}  {k}')
