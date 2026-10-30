"""
Phase 05 Part 1E — Update the phasewise execution manifest and notebook map
with the closure notebook and v3 governance annotations.

Writes:
  reports/audits/phasewise_notebook_execution_manifest.json / .csv / .md
  reports/audits/phasewise_notebook_map.json / .csv / .md

Preserves all existing entries; only appends/annotates. Historical SHAs untouched.
"""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import nbformat
import pandas as pd

PROJECT_ROOT = Path(r'D:\Softfors\jup')
AUDITS = PROJECT_ROOT / 'reports' / 'audits'
now = datetime.now(timezone.utc).isoformat()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def nb_stats(rel_path):
    p = PROJECT_ROOT / rel_path
    nb = nbformat.read(str(p), as_version=4)
    code = [c for c in nb.cells if c.cell_type == 'code']
    executed = [c for c in code if c.get('execution_count')]
    errs = sum(1 for c in code for o in c.get('outputs', []) if o.get('output_type') == 'error')
    pngs = sum(1 for c in code for o in c.get('outputs', []) if 'image/png' in (o.get('data', {}) or {}))
    return {
        'notebook_path': rel_path,
        'total_cells': len(nb.cells),
        'executed_cells': len(executed),
        'error_count': errs,
        'png_figures': pngs,
        'sha256': sha256_file(p),
        'status': 'ACCEPTED_PASS' if errs == 0 else 'FAIL',
    }


# ---------------------------------------------------------------------------
# 1. Execution manifest — append closure notebook if absent
# ---------------------------------------------------------------------------
exec_json = AUDITS / 'phasewise_notebook_execution_manifest.json'
entries = json.loads(exec_json.read_text(encoding='utf-8'))

CLOSURE_REL = ('notebooks/phasewise/phase_05_leakage_audit/'
               'phase05_manifest_v3_promotion_and_leakage_closure.ipynb')

existing_paths = {e['notebook_path'] for e in entries}
if CLOSURE_REL not in existing_paths:
    entries.append(nb_stats(CLOSURE_REL))
else:
    for i, e in enumerate(entries):
        if e['notebook_path'] == CLOSURE_REL:
            entries[i] = nb_stats(CLOSURE_REL)

# v2/v3 governance annotation block
annotations = {
    'active_development_manifest_version': 'phase4_v3',
    'historical_manifest_version': 'phase4_v2',
    'phase05_status': 'COMPLETE',
    'phase05_part': '1E — manifest v3 promotion + governance closure',
    'phase05_scientific_gate': 'PASS',
    'clean_v3_revalidation_required_for': [f'{i:02d}' for i in range(6, 16)],
    'clean_rerun_scope': 'reports/tables/phase05_clean_rerun_scope.csv',
    'historical_evidence_leakage_status':
        'KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY',
    'updated_at': now,
    'note': 'Historical notebook SHAs (Phases 00-05) are unchanged. '
            'The closure notebook is the final Phase-05 Part-1E artifact.',
}
out = {'notebooks': entries, 'governance_annotations': annotations}
exec_json.write_text(json.dumps(out, indent=2), encoding='utf-8')

# CSV (notebooks only, preserving original flat schema)
pd.DataFrame(entries).to_csv(AUDITS / 'phasewise_notebook_execution_manifest.csv', index=False)

# Markdown
md = ['# Phasewise Notebook Execution Manifest', '',
      f'- **Generated At:** {now}',
      '- **Execution Environment:** `D:\\Softfors\\jup\\.venv\\Scripts\\python.exe` (Kernel: `jup-venv`)',
      '- **Active development manifest:** `phase4_v3`',
      '- **Historical manifest:** `phase4_v2`',
      '- **Phase 05:** COMPLETE (scientific gate PASS)',
      '',
      '| Notebook | Cells | Executed | Errors | PNG | SHA-256 | Status |',
      '| :--- | ---: | ---: | ---: | ---: | :--- | :--- |']
for e in entries:
    md.append(f"| `{Path(e['notebook_path']).name}` | {e['total_cells']} | "
              f"{e['executed_cells']} | {e['error_count']} | {e['png_figures']} | "
              f"`{e['sha256']}` | `{e['status']}` |")
md.append('')
md.append('> Clean-v3 revalidation is required for Phases 06-15. See '
          '`reports/tables/phase05_clean_rerun_scope.csv`.')
(AUDITS / 'phasewise_notebook_execution_manifest.md').write_text('\n'.join(md), encoding='utf-8')

# ---------------------------------------------------------------------------
# 2. Notebook map — annotate phase 05 / 06 entries
# ---------------------------------------------------------------------------
map_json = AUDITS / 'phasewise_notebook_map.json'
mapping = json.loads(map_json.read_text(encoding='utf-8'))

for entry in mapping:
    phase = str(entry.get('phase', entry.get('phase_id', ''))).lstrip('0') or '0'
    if phase == '5':
        entry['status'] = 'COMPLETE'
        entry['active_development_manifest_version'] = 'phase4_v3'
        entry['historical_manifest_version'] = 'phase4_v2'
        entry['scientific_gate'] = 'PASS'
        entry['closure_notebook'] = CLOSURE_REL
        entry['closure_notebook_sha256'] = sha256_file(PROJECT_ROOT / CLOSURE_REL)
    if phase in {'6', '7', '8', '9', '10', '11', '12', '13', '14', '15'}:
        entry['historical_v2_status'] = entry.get('status', 'COMPLETE')
        entry['clean_v3_revalidation_status'] = (
            'PARTIAL_RERUN_REQUIRED' if phase == '8' else 'REVALIDATION_REQUIRED')
        entry['manifest_version_of_historical_evidence'] = 'phase4_v2'

map_json.write_text(json.dumps(mapping, indent=2), encoding='utf-8')

# CSV mirror if the existing one is tabular
try:
    map_df = pd.DataFrame(mapping)
    map_df.to_csv(AUDITS / 'phasewise_notebook_map.csv', index=False)
except Exception as exc:  # pragma: no cover
    print('map csv skipped:', exc)

# Markdown: annotate the Phase 05 / Phase 06 rows textually
map_md = AUDITS / 'phasewise_notebook_map.md'
text = map_md.read_text(encoding='utf-8')
if 'Phase-05 Part-1E closure' not in text:
    header_note = (
        '\n> **Governance (Phase-05 Part 1E):** Active development manifest is `phase4_v3`; '
        'historical manifest is `phase4_v2`.\n'
        '> Phase 05 is COMPLETE (scientific gate PASS). Clean-v3 revalidation is required for '
        'Phases 06-15.\n'
        '> Phase-05 Part-1E closure notebook: '
        '`notebooks/phasewise/phase_05_leakage_audit/'
        'phase05_manifest_v3_promotion_and_leakage_closure.ipynb` '
        f'(`{sha256_file(PROJECT_ROOT / CLOSURE_REL)}`).\n\n')
    lines = text.split('\n')
    # insert after the title line
    if lines and lines[0].startswith('# '):
        lines.insert(1, header_note)
    else:
        lines.insert(0, header_note)
    map_md.write_text('\n'.join(lines), encoding='utf-8')

print('Execution manifest entries:', len(entries))
print('Closure notebook stat:', entries[-1])
print('Map phases annotated:', len(mapping))
print('Wrote execution manifest (.json/.csv/.md) and map (.json/.csv/.md)')
