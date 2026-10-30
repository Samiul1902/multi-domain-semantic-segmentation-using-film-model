"""Execute the Phase-05 Part 1E closure notebook and report execution stats."""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

PROJECT_ROOT = Path(r'D:\Softfors\jup')
NB_PATH = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_05_leakage_audit' / \
    'phase05_manifest_v3_promotion_and_leakage_closure.ipynb'

nb = nbformat.read(str(NB_PATH), as_version=4)
client = NotebookClient(
    nb,
    timeout=1800,
    kernel_name='jup-venv',
    resources={'metadata': {'path': str(PROJECT_ROOT)}},
    allow_errors=False,
)

try:
    client.execute()
except CellExecutionError as e:
    print('EXECUTION ERROR:')
    print(e)
    nbformat.write(nb, str(NB_PATH))
    sys.exit(1)
finally:
    pass

nbformat.write(nb, str(NB_PATH))

n_code = sum(1 for c in nb.cells if c.cell_type == 'code')
executed = sum(1 for c in nb.cells if c.cell_type == 'code' and c.get('execution_count'))
errors = sum(1 for c in nb.cells if c.cell_type == 'code'
             for o in c.get('outputs', []) if o.get('output_type') == 'error')
pngs = sum(1 for c in nb.cells for o in c.get('outputs', [])
           for d in (o.get('data', {}) or {}).get('image/png', []) or [])
images = sum(1 for c in nb.cells for o in c.get('outputs', [])
             if 'image/png' in (o.get('data', {}) or {}))

print('=' * 60)
print('CLOSURE NOTEBOOK EXECUTION REPORT')
print('=' * 60)
print('notebook      :', NB_PATH.name)
print('code cells    :', n_code)
print('executed      :', executed)
print('unexecuted    :', n_code - executed)
print('errors        :', errors)
print('embedded PNG  :', images)
print('=' * 60)

# Re-hash 3 times for stability
import hashlib
def sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()

h1 = sha(NB_PATH)
h2 = sha(NB_PATH)
h3 = sha(NB_PATH)
print('SHA PASS1:', h1)
print('SHA PASS2:', h2)
print('SHA PASS3:', h3)
print('SHA STABLE:', h1 == h2 == h3)
