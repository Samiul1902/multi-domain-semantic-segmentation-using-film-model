"""Phase25E notebook determinism + visual-integrity audit.

Rebuilds the canonical notebook 3x and requires byte-identical SHAs, then
validates every embedded PNG (magic, IEND, PIL verify) and cell structure.
"""
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import nbformat
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
NB = ROOT / 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb'
BUILDER = ROOT / 'scripts/analysis/build_phase25e_notebook.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    failures = []
    shas = []
    for i in range(3):
        subprocess.run([str(ROOT / '.venv/Scripts/python.exe'), str(BUILDER)],
                       check=True, capture_output=True)
        shas.append(sha(NB))
    deterministic = len(set(shas)) == 1
    if not deterministic:
        failures.append(f'NONDETERMINISTIC:{shas}')

    nb = nbformat.read(NB, as_version=4)
    png_ok = 0
    png_bad = []
    counts = []
    for idx, cell in enumerate(nb.cells):
        if cell.cell_type != 'code':
            continue
        counts.append(cell.get('execution_count'))
        for out in cell.get('outputs', []):
            data = out.get('data', {})
            if 'image/png' in data:
                raw = data['image/png']
                if isinstance(raw, str):
                    import base64
                    raw = base64.b64decode(raw)
                ok_magic = raw[:8] == b'\x89PNG\r\n\x1a\n'
                ok_iend = b'IEND' in raw[-12:]
                try:
                    Image.open(io.BytesIO(raw)).verify()
                    ok_pil = True
                except Exception as exc:  # noqa: BLE001
                    ok_pil = False
                    png_bad.append(f'{idx}:{exc}')
                if ok_magic and ok_iend and ok_pil:
                    png_ok += 1
                else:
                    png_bad.append(f'cell{idx}')
    audit = {
        'classification': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION',
        'stage': 'NOTEBOOK_DETERMINISM',
        'notebook_path': NB.relative_to(ROOT).as_posix(),
        'notebook_sha256': shas[-1],
        'rebuild_sha256': shas,
        'three_times_byte_identical': deterministic,
        'cell_count': len(nb.cells),
        'code_cell_count': len(counts),
        'execution_counts': counts,
        'png_outputs_valid': png_ok,
        'png_outputs_bad': png_bad,
        'no_stored_execution_metadata': all('execution' not in c.get('metadata', {}) for c in nb.cells),
        'failures': failures,
        'all_pass': not failures and not png_bad,
    }
    (AUD / 'phase25e_policy_eval_notebook_determinism.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'SHA: {shas[-1]}')
    print(f'3x identical: {deterministic}; cells: {len(nb.cells)}; valid PNG: {png_ok}; bad: {png_bad}')
    if not audit['all_pass']:
        sys.exit(1)
    print('PHASE25E_NOTEBOOK_DETERMINISM_PASS')


if __name__ == '__main__':
    main()
