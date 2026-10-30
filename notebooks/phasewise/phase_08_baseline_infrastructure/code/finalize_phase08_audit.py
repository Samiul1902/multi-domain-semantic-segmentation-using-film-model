"""Finalize the Phase-08 Part 1A audit with notebook state, tests and immutability."""

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import nbformat

PROJECT_ROOT = Path(r'D:\Softfors\jup')
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
NB = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_08_baseline_infrastructure'
      / 'phase08_clean_v3_training_infrastructure_validation.ipynb')

EXPECT = {
    'phase06_notebook': ('notebooks/phasewise/phase_06_kub_characterization/'
                         'phase06_kub_dataset_characterization_clean_v3.ipynb',
                         'c2164345d80843c6116093cc5c58bebfa3792b8becce0d887e6c379ab8069888'),
    'phase07_part1a_notebook': ('notebooks/phasewise/phase_07_tiny_object_definition/'
                                'phase07_tiny_object_definition_train_only_design.ipynb',
                                'f2ff7969d4c446c5c7fa737c7cbf36925123c97db1ca86593dbddea842a31eb9'),
    'phase07_part1b_notebook': ('notebooks/phasewise/phase_07_tiny_object_definition/'
                                'phase07_tiny_object_taxonomy_freeze_clean_v3.ipynb',
                                '9d9ebf3684523a7b85df4b6fc52c4f0e970857e80f05d366445a50b6a7dfde85'),
    'frozen_taxonomy_artifact': ('reports/audits/kub_size_clean_v3_v1_thresholds.json',
                                 '89031c51a35c24f6f939fd6206fde6002a019d4bda24ce8cb21988f04db0f0d6'),
    'phase4_v3_train': ('manifests/phase4_v3/train.csv',
                        '28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6'),
    'phase4_v3_val': ('manifests/phase4_v3/val.csv',
                      '082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315'),
    'phase4_v3_test': ('manifests/phase4_v3/test.csv',
                       '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727'),
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

proc = subprocess.run(
    [str(PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'), '-m', 'pytest',
     'tests/test_phase08_infrastructure.py', '-q', '--no-header'],
    cwd=str(PROJECT_ROOT), capture_output=True, text=True)
tests_ok = proc.returncode == 0
tests_tail = (proc.stdout or proc.stderr).strip().splitlines()[-1] if (proc.stdout or proc.stderr) else ''

apath = AUDITS / 'phase08_clean_v3_infrastructure_audit.json'
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
audit['generated_at_final'] = datetime.now(timezone.utc).isoformat()
audit['unit_tests'] = {'file': 'tests/test_phase08_infrastructure.py',
                       'result': 'PASS' if tests_ok else 'FAIL', 'summary': tests_tail}

audit['immutability'] = {}
for key, (rel, exp) in EXPECT.items():
    actual = sha(PROJECT_ROOT / rel)
    audit['immutability'][key] = {'path': rel, 'expected': exp, 'actual': actual,
                                  'unchanged': actual == exp}

g = audit['scientific_gate']['gates']
g['unit_tests_pass'] = tests_ok
g['notebook_run_all_clean'] = (n_code - executed == 0 and errors == 0)
g['embedded_png_ge_4'] = pngs >= 4
g['previous_phases_unchanged'] = all(v['unchanged'] for v in audit['immutability'].values())
audit['scientific_gate']['status'] = 'PASS' if all(g.values()) else 'CHECK_REQUIRED'
audit['status'] = audit['scientific_gate']['status']

apath.write_text(json.dumps(audit, indent=2, default=str), encoding='utf-8')

print('Notebook SHA   :', nb_sha)
print('SHA stable 3x  :', h1 == h2 == h3)
print('cells/exec/err :', len(nb.cells), n_code, executed, errors)
print('embedded PNG   :', pngs)
print('unit tests     :', audit['unit_tests']['result'], '|', tests_tail)
print('GATE           :', audit['status'])
for k, v in g.items():
    print(f"  {'PASS' if v else 'FAIL'}  {k}")
