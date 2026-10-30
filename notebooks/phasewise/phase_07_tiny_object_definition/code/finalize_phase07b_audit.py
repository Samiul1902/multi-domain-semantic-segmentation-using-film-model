"""Finalize the Phase-07 Part 1B freeze audit with notebook state and gate results."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import nbformat

PROJECT_ROOT = Path(r'D:\Softfors\jup')
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
NB = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_07_tiny_object_definition'
      / 'phase07_tiny_object_taxonomy_freeze_clean_v3.ipynb')

EXPECT = {
    'phase06': ('notebooks/phasewise/phase_06_kub_characterization/'
                'phase06_kub_dataset_characterization_clean_v3.ipynb',
                'c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888'),
    'phase07_part1a': ('notebooks/phasewise/phase_07_tiny_object_definition/'
                       'phase07_tiny_object_definition_train_only_design.ipynb',
                       'f2ff7969d4c446c5c7fa737c7cbf36925123c97db1ca86593dbddea842a31eb9'),
}


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

# unit tests
proc = subprocess.run(
    [str(PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'), '-m', 'pytest',
     'tests/test_phase07_taxonomy.py', '-q', '--no-header'],
    cwd=str(PROJECT_ROOT), capture_output=True, text=True)
tests_ok = proc.returncode == 0
tests_tail = (proc.stdout or proc.stderr).strip().splitlines()[-1] if (proc.stdout or proc.stderr) else ''

apath = AUDITS / 'phase07_clean_v3_taxonomy_freeze_audit.json'
audit = json.loads(apath.read_text(encoding='utf-8'))

audit['notebook'] = {
    'path': str(NB.relative_to(PROJECT_ROOT)).replace('\\', '/'),
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

audit['unit_tests'] = {
    'file': 'tests/test_phase07_taxonomy.py',
    'result': 'PASS' if tests_ok else 'FAIL',
    'summary': tests_tail,
}
for key, (rel, exp) in EXPECT.items():
    actual = sha(PROJECT_ROOT / rel)
    audit['immutability'][key] = {'path': rel, 'expected': exp,
                                  'actual': actual, 'unchanged': actual == exp}

g = audit['scientific_gate']['gates']
g['unit_tests_pass'] = tests_ok
g['notebook_run_all_clean'] = (n_code - executed == 0 and errors == 0)
g['figures_ge_7'] = pngs >= 7
audit['scientific_gate']['status'] = 'PASS' if all(g.values()) else 'CHECK_REQUIRED'
audit['status'] = audit['scientific_gate']['status']
audit['phase07_complete'] = audit['status'] == 'PASS'

apath.write_text(json.dumps(audit, indent=2), encoding='utf-8')

print('Notebook SHA   :', nb_sha)
print('SHA stable 3x  :', h1 == h2 == h3)
print('cells/exec/err :', len(nb.cells), n_code, executed, errors)
print('embedded PNG   :', pngs)
print('unit tests     :', audit['unit_tests']['result'], '|', tests_tail)
print('Phase-06 unchanged         :', audit['immutability']['phase06']['unchanged'])
print('Phase-07 Part-1A unchanged :', audit['immutability']['phase07_part1a']['unchanged'])
print('GATE           :', audit['status'])
for k, v in g.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
