"""Phase25E reconciliation notebook determinism + visual-integrity audit.

Rebuilds the reconciled canonical notebook 3x with the reconciliation builder and
requires byte-identical SHAs; validates every embedded PNG and cell structure.
"""
import base64
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
BUILDER = ROOT / 'scripts/analysis/build_phase25e_reconciliation_notebook.py'
ARCHIVE = AUD / 'phase25e_reconciliation_archive/phase25e_resource_gate__pre_reconciliation.ipynb'
PRE_RECON_SHA = 'e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    failures = []
    shas = []
    for _ in range(3):
        subprocess.run([str(ROOT / '.venv/Scripts/python.exe'), str(BUILDER)],
                       check=True, capture_output=True)
        shas.append(sha(NB))
    deterministic = len(set(shas)) == 1
    if not deterministic:
        failures.append(f'NONDETERMINISTIC:{shas}')

    archive_ok = ARCHIVE.exists() and sha(ARCHIVE) == PRE_RECON_SHA
    if not archive_ok:
        failures.append('PRE_RECONCILIATION_ARCHIVE_MISSING_OR_DRIFTED')

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

    # addendum must be present
    md_text = '\n'.join(c.source for c in nb.cells if c.cell_type == 'markdown')
    has_addendum = 'Post-closure statistical-adjudication reconciliation (addendum)' in md_text
    has_superseded = 'SUPERSEDED' in md_text
    if not has_addendum:
        failures.append('ADDENDUM_SECTION_MISSING')
    if not has_superseded:
        failures.append('SUPERSEDED_STATEMENTS_SECTION_MISSING')

    audit = {
        'classification': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION',
        'stage': 'RECONCILIATION_NOTEBOOK_DETERMINISM',
        'notebook_path': NB.relative_to(ROOT).as_posix(),
        'notebook_sha256': shas[-1],
        'rebuild_sha256': shas,
        'three_times_byte_identical': deterministic,
        'pre_reconciliation_notebook_sha256': PRE_RECON_SHA,
        'pre_reconciliation_archive_path': ARCHIVE.relative_to(ROOT).as_posix(),
        'pre_reconciliation_archive_sha256': sha(ARCHIVE) if ARCHIVE.exists() else None,
        'pre_reconciliation_archive_intact': archive_ok,
        'cell_count': len(nb.cells),
        'code_cell_count': len(counts),
        'execution_counts': counts,
        'png_outputs_valid': png_ok,
        'png_outputs_bad': png_bad,
        'addendum_section_present': has_addendum,
        'superseded_statements_section_present': has_superseded,
        'no_stored_execution_metadata': all('execution' not in c.get('metadata', {}) for c in nb.cells),
        'failures': failures,
        'all_pass': not failures and not png_bad,
    }
    (AUD / 'phase25e_reconciliation_notebook_determinism.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'SHA: {shas[-1]}')
    print(f'3x identical: {deterministic}; cells: {len(nb.cells)}; valid PNG: {png_ok}; '
          f'archive intact: {archive_ok}; addendum: {has_addendum}')
    if not audit['all_pass']:
        print('failures:', failures, png_bad)
        sys.exit(1)
    print('PHASE25E_RECONCILIATION_NOTEBOOK_DETERMINISM_PASS')


if __name__ == '__main__':
    main()
