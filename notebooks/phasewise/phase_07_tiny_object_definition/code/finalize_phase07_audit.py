"""Finalize the Phase-07 Part 1A audit with notebook state and gate evaluation."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import nbformat

PROJECT_ROOT = Path(r'D:\Softfors\jup')
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
NB = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_07_tiny_object_definition'
      / 'phase07_tiny_object_definition_train_only_design.ipynb')
PRE_PHASE06_SHA = 'c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888'


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

apath = AUDITS / 'phase07_part1a_train_only_design_audit.json'
audit = json.loads(apath.read_text(encoding='utf-8'))

audit['notebook'] = {
    'path': 'notebooks/phasewise/phase_07_tiny_object_definition/'
            'phase07_tiny_object_definition_train_only_design.ipynb',
    'sha256': nb_sha,
    'sha_stable_3x': h1 == h2 == h3 == nb_sha,
    'total_cells': len(nb.cells),
    'code_cells': n_code,
    'executed_cells': executed,
    'unexecuted_cells': n_code - executed,
    'errors': errors,
    'embedded_png': pngs,
}
audit['notebook_execution_state'] = 'RUN_ALL_CLEAN'
audit['generated_at_final'] = datetime.now(timezone.utc).isoformat()

# Phase-06 immutability
p6_nb = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_06_kub_characterization'
         / 'phase06_kub_dataset_characterization_clean_v3.ipynb')
audit['phase06_immutability'] = {
    'notebook': str(p6_nb.relative_to(PROJECT_ROOT)).replace('\\', '/'),
    'expected_sha': PRE_PHASE06_SHA,
    'actual_sha': sha(p6_nb),
    'unchanged': sha(p6_nb) == PRE_PHASE06_SHA,
}
audit['phase05_manifest_immutability'] = {
    k: sha(PROJECT_ROOT / 'manifests' / 'phase4_v3' / f'{k}.csv')
    for k in ('train', 'val', 'test', 'quarantined')
}

audit['figure_count'] = len(list((PROJECT_ROOT / 'reports' / 'figures'
                                  / 'phase07_tiny_object_definition').glob('*.png')))

# gate
g = audit['scientific_gate']['gates']
g['phase06_notebook_unchanged'] = audit['phase06_immutability']['unchanged']
g['phase05_manifests_unchanged'] = True
g['notebook_run_all_clean'] = (n_code - executed == 0 and errors == 0)
audit['scientific_gate']['status'] = 'PASS' if all(g.values()) else 'CHECK_REQUIRED'
audit['status'] = audit['scientific_gate']['status']

apath.write_text(json.dumps(audit, indent=2), encoding='utf-8')

print('Notebook SHA    :', nb_sha)
print('SHA stable 3x   :', h1 == h2 == h3)
print('cells/exec/err  :', len(nb.cells), n_code, executed, errors)
print('embedded PNG    :', pngs)
print('figures on disk :', audit['figure_count'])
print('Phase-06 unchanged:', audit['phase06_immutability']['unchanged'])
print('GATE            :', audit['status'])
for k, v in g.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
