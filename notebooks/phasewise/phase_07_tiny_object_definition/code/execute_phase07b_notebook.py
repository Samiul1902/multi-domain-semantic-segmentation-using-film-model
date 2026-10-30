"""Execute the Phase-07 Part 1A notebook and report execution stats."""

import hashlib
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_PATH = (PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_07_tiny_object_definition'
           / 'phase07_tiny_object_taxonomy_freeze_clean_v3.ipynb')

nb = nbformat.read(str(NB_PATH), as_version=4)
client = NotebookClient(nb, timeout=3600, kernel_name='jup-venv',
                        resources={'metadata': {'path': str(PROJECT_ROOT)}},
                        allow_errors=False)
try:
    client.execute()
except CellExecutionError as e:
    print('EXECUTION ERROR:')
    print(e)
    nbformat.write(nb, str(NB_PATH))
    sys.exit(1)

nbformat.write(nb, str(NB_PATH))


def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


n_code = sum(1 for c in nb.cells if c.cell_type == 'code')
executed = sum(1 for c in nb.cells if c.cell_type == 'code' and c.get('execution_count'))
errors = sum(1 for c in nb.cells if c.cell_type == 'code'
             for o in c.get('outputs', []) if o.get('output_type') == 'error')
pngs = sum(1 for c in nb.cells if c.cell_type == 'code'
           for o in c.get('outputs', []) if 'image/png' in (o.get('data', {}) or {}))

print('=' * 64)
print('PHASE 07 PART 1B — NOTEBOOK EXECUTION REPORT')
print('=' * 64)
print('notebook     :', NB_PATH.name)
print('total cells  :', len(nb.cells))
print('code cells   :', n_code)
print('executed     :', executed)
print('unexecuted   :', n_code - executed)
print('errors       :', errors)
print('embedded PNG :', pngs)
h1, h2, h3 = sha(NB_PATH), sha(NB_PATH), sha(NB_PATH)
print('SHA PASS1    :', h1)
print('SHA PASS2    :', h2)
print('SHA PASS3    :', h3)
print('SHA STABLE   :', h1 == h2 == h3)
print('=' * 64)
