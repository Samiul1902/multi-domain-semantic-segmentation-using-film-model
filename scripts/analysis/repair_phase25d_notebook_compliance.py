"""Audit-only repair. Never imports training/model code or loads model weights.

Run with .venv/Scripts/python.exe scripts/analysis/repair_phase25d_notebook_compliance.py.
Frozen scientific inputs are read only; the original notebook is archived verbatim.
"""
import base64
import hashlib
import io
import json
import re
import struct
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
NB = ROOT / 'notebooks/phasewise/phase_25d_benefit_router/phase25d_benefit_router.ipynb'
EXP = ROOT / 'experiments/phase25d_barr_benefit_router_v1_2_1_seed42'
OLD = '29518fc13f3de60113e1110a12a3f38bac5f54c246751503fe29e595f6dbe997'
ARCHIVE = AUD / 'phase25d_notebook_compliance_pre_repair.ipynb'
COUNTS = [57, 54, 159, 200, 100]
BEST = [37, 34, 139, 199, 80]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(name, value):
    (AUD / (name + '.json')).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def main():
    gate = json.loads((AUD / 'phase25d_notebook_compliance_repair_entry_gate.json').read_text())
    assert gate['all_pass']
    for key, record in gate['checks'].items():
        if key != 'notebook':
            assert sha(ROOT / record['path']) == record['expected_sha256'], 'SCIENTIFIC_ARTIFACT_DRIFT'
    if not ARCHIVE.exists():
        assert sha(NB) == OLD
        ARCHIVE.write_bytes(NB.read_bytes())
    assert sha(ARCHIVE) == OLD
    original = nbformat.read(ARCHIVE, as_version=4)
    tables = []
    for cell in original.cells:
        if cell.cell_type == 'markdown' and 'complete epoch table' in cell.source:
            rows = [line for line in cell.source.splitlines() if line.startswith('|')]
            tables.append({'title': cell.source.splitlines()[0], 'embedded_rows': len(rows)-2})
    codes = [{'cell_id': c.id, 'source': c.source, 'execution_count': c.execution_count,
              'comment_only': all(not l.strip() or l.lstrip().startswith('#') for l in c.source.splitlines()),
              'png_outputs': sum('image/png' in o.get('data', {}) for o in c.outputs)}
             for c in original.cells if c.cell_type == 'code']
    assert [t['embedded_rows'] for t in tables] == [10]*5+[15]
    write('phase25d_existing_notebook_compliance_audit', {
        'classification': 'PHASE25D_REVIEWER_NOTEBOOK_PRESENT_BUT_NOT_FULL_EPOCH_AUDIT_COMPLIANT',
        'defect_scope': 'NOTEBOOK / EVIDENCE PRESENTATION ONLY', 'science_changed': False,
        'old_notebook_sha256': OLD, 'archive': str(ARCHIVE.relative_to(ROOT)),
        'tables': tables, 'all_code_cells': codes,
        'fold3_physical_closure': json.loads((EXP/'fold3/training_closure.json').read_text()),
        'summary_discrepancy': 'CHAT_OR_SUMMARY_TRANSCRIPTION_DEFECT_ONLY'})

    # Bind every frozen input used in analysis, including all original rendered tables.
    inputs = {v['path']: v['expected_sha256'] for k,v in gate['checks'].items() if k != 'notebook'}
    for path in [*EXP.glob('fold*/history.csv'), *EXP.glob('fold*/training_closure.json'),
                 * (ROOT/'reports/tables').glob('phase25d_*.csv'),
                 AUD/'phase25d_final_freeze.json', AUD/'phase25d_final_refit_epoch_rule_execution.json']:
        inputs[path.relative_to(ROOT).as_posix()] = sha(path)
    setup = '''from pathlib import Path
import hashlib, json, io
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import display, HTML, Image
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'reports/audits/phase25d_final_freeze.json').exists())
INPUTS = __INPUTS__
for relative, expected in INPUTS.items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == expected, relative
def read_csv(relative):
    assert relative in INPUTS
    return pd.read_csv(ROOT / relative)
def read_json(relative):
    assert relative in INPUTS
    return json.loads((ROOT / relative).read_text())
def full_table(df, name):
    display(HTML('<h3>' + name + '</h3>' + df.to_html(index=False, max_rows=None, max_cols=None)))
def figure(fig):
    data = io.BytesIO()
    fig.savefig(data, format='png', dpi=110, metadata={'Software': 'Phase25D frozen artifact audit'})
    plt.close(fig)
    display(Image(data=data.getvalue(), format='png'))
EXP = 'experiments/phase25d_barr_benefit_router_v1_2_1_seed42/'
def history(name, count, best=None):
    df = read_csv(EXP + name + '/history.csv')
    assert len(df) == count and not df.epoch.duplicated().any()
    assert df.epoch.tolist() == list(range(1, count + 1))
    assert np.isfinite(df.select_dtypes(include='number').to_numpy()).all()
    if best is not None:
        closure = read_json(EXP + name + '/training_closure.json')
        assert closure['total_epochs'] == count and closure['best_epoch'] == best
        assert ((df.epoch == best) & df.is_best).sum() == 1
        assert int(df.loc[df.is_best, 'epoch'].iloc[-1]) == best
        # Persisted is_best means a running improvement, not only the selected checkpoint.
        assert {'epoch','train_huber','early_stop_huber','learning_rate','bad_epochs','is_best','elapsed_seconds'} <= set(df.columns)
        if name == 'fold3':
            assert len(df) == 200 and df.epoch.min() == 1 and df.epoch.max() == 200
            assert best == 199 and closure['termination'] == 'max_epochs'
        print(name, json.dumps(closure, sort_keys=True))
    full_table(df, name + ' complete immutable epoch history')
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(df.epoch, df.train_huber, label='train Huber')
    if 'early_stop_huber' in df:
        ax.plot(df.epoch, df.early_stop_huber, label='early-stop Huber')
        ax.axvline(best, color='gray', linestyle='--', label='selected best epoch')
    ax.set(xlabel='Completed epoch', ylabel='Huber loss', title=name + ' frozen training history', yscale='log')
    ax.legend(); fig.tight_layout(); figure(fig)
    return df
print('Frozen input SHA checks passed:', len(INPUTS))
print('Audit-only execution: no training, model construction, model forwards, or prediction regeneration.')
'''.replace('__INPUTS__', repr(dict(sorted(inputs.items()))))
    cells = [nbformat.v4.new_markdown_cell('# Phase25D canonical reviewer audit — notebook compliance repair\n\n'
        'Analysis of frozen artifacts only. Scientific execution is accepted and unchanged. '
        'Phase25E remains ELIGIBLE_NOT_STARTED. No holdout, VAL808 or TEST outcomes are read.\n\n'
        'PRE_NOTEBOOK_COMPLIANCE_REPAIR_PROVENANCE = `' + OLD + '`\n\n'
        'All code cells execute during each build; execution counts are retained. No output is preattached. '
        'Only execution timing metadata is disabled. Tables include every persisted column and every epoch. '
        'Persisted `is_best` marks running improvements; the last improvement is the canonical selected best.\n\n'
        'Fold3: 200 completed epochs, selected best 199, termination `max_epochs`. '
        'The earlier 199-total summary was CHAT_OR_SUMMARY_TRANSCRIPTION_DEFECT_ONLY.'),
        nbformat.v4.new_code_cell(setup)]
    # Preserve the existing scientific narrative; replace its table/figure presentation.
    for old in original.cells:
        if old.cell_type == 'code':
            continue
        source = old.source
        if 'complete epoch table' in source:
            title = source.splitlines()[0]
            cells.append(nbformat.v4.new_markdown_cell(title))
            match = re.search(r'Fold (\d)', title)
            if match:
                k = int(match[1])
                source = f"fold{k} = history('fold{k}', {COUNTS[k]}, {BEST[k]})"
            else:
                source = """final = history('final', 80)
freeze = read_json('reports/audits/phase25d_final_freeze.json')
rule = read_json('reports/audits/phase25d_final_refit_epoch_rule_execution.json')
assert rule['best_epochs'] == [37, 34, 139, 199, 80]
assert rule['final_router_epochs'] == freeze['final_router_epochs'] == int(final.epoch.iloc[-1]) == 80
assert sorted(rule['best_epochs'])[2] == 80
print('checkpoint rule = LAST_FIXED_EPOCH; checkpoint epoch = 80; final history rows = 80')"""
            cells.append(nbformat.v4.new_code_cell(source))
            continue
        if source.startswith('## 2. Predecessor'):
            source = source.replace('Predecessor terminal', 'Historical predecessor terminal')
        if source.startswith('## 36.'):
            source += '\n\nThese checkpoint integrity and synthetic-inference results are historical frozen audit evidence; this notebook performs no model loading or inference.'
        cells.append(nbformat.v4.new_markdown_cell(source))
        if source.startswith('## 25.'):
            cells.append(nbformat.v4.new_code_cell("""oof = read_csv('data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv')
assert len(oof) == 4957 and oof.sample_id.nunique() == 4957
assert np.isfinite(oof.select_dtypes(include='number').to_numpy()).all()
fig, ax = plt.subplots(figsize=(6, 5))
ax.scatter(oof.delta_dice, oof.delta_hat_oof, s=8, alpha=0.35)
ax.set(xlabel='Frozen true DeltaDice', ylabel='Frozen OOF predicted DeltaDice', title='OOF predicted vs true (4957 rows)')
fig.tight_layout(); figure(fig)
freeze = read_json('reports/audits/phase25d_final_freeze.json')
assert freeze['oof_r2'] == 0.087657630443573
print('Authoritative frozen OOF R2 = 0.087657630443573 (3 decimals: 0.088; 4: 0.0877; 6: 0.087658)')"""))
        if source.startswith('## 29.'):
            cells.append(nbformat.v4.new_code_cell("""fig, ax = plt.subplots(figsize=(7, 4))
ax.hist(oof.residual, bins=60)
ax.set(xlabel='Persisted residual (true minus predicted)', ylabel='OOF rows', title='Frozen OOF residual distribution')
fig.tight_layout(); figure(fig)"""))
    cells.append(nbformat.v4.new_code_cell("""assert [len(fold0), len(fold1), len(fold2), len(fold3), len(fold4)] == [57,54,159,200,100]
assert len(final) == 80
for key in ['lambda_selected', 'routing_threshold_selected', 'resource_gate_calibrated', 'phase25e_started']:
    assert freeze[key] is False
for key in ['router_holdout_reads', 'val808_reads', 'test_reads']:
    assert freeze[key] == 0
print('RUN_ALL_COMPLETE: all frozen-artifact, full-history and scope assertions passed.')
print('Phase25D COMPLETE_CANONICAL / TRAINED_FROZEN; Phase25E ELIGIBLE_NOT_STARTED')"""))
    for i, cell in enumerate(cells):
        cell.id = f'p25d-repair-{i:03d}'
    runs = []
    output_bytes = []
    for build in range(1, 4):
        nb = nbformat.v4.new_notebook(cells=cells)
        nb.metadata.kernelspec = {'display_name':'Python 3', 'language':'python', 'name':'python3'}
        client = NotebookClient(nb, timeout=180, kernel_name='python3', record_timing=False,
                                resources={'metadata': {'path': str(ROOT)}})
        client.execute()
        code_cells = [c for c in nb.cells if c.cell_type == 'code']
        assert [c.execution_count for c in code_cells] == list(range(1, len(code_cells)+1))
        errors = [o for c in code_cells for o in c.outputs if o.output_type == 'error']
        assert not errors
        assert 'RUN_ALL_COMPLETE' in str(code_cells[-1].outputs)
        data = nbformat.writes(nb).encode('utf-8') + b'\n'
        output_bytes.append(data)
        runs.append({'build': build, 'sha256': hashlib.sha256(data).hexdigest(),
                     'executed_code_cells': len(code_cells), 'execution_counts': [c.execution_count for c in code_cells],
                     'errors': len(errors), 'completion_marker_present': True})
        print('Executed build', build, runs[-1]['sha256'], flush=True)
    assert output_bytes[0] == output_bytes[1] == output_bytes[2]
    images = []
    for cell in nb.cells:
        for output in cell.get('outputs', []):
            if 'image/png' not in output.get('data', {}):
                continue
            png = base64.b64decode(output.data['image/png'], validate=True)
            assert png[:8] == b'\x89PNG\r\n\x1a\n'
            offset = 8
            chunks = []
            while offset < len(png):
                size = struct.unpack('>I', png[offset:offset+4])[0]
                kind = png[offset+4:offset+8]
                chunks.append(kind.decode('ascii'))
                offset += 12+size
            assert offset == len(png) and chunks[-1] == 'IEND' and png[-12:-8] == b'\x00'*4
            with Image.open(io.BytesIO(png)) as im:
                dims = im.size
                im.verify()
            images.append({'cell_id': cell.id, 'sha256': hashlib.sha256(png).hexdigest(),
                           'dimensions': dims, 'png_magic_valid': True, 'trailing_iend_valid': True, 'pil_verify': True})
    assert len(images) == 8
    # Confirm the displayed HTML physically contains exactly one data row per epoch.
    rendered = []
    for cell in nb.cells:
        if cell.cell_type == 'code' and re.search(r"= history\('", cell.source):
            html = ''.join(o.get('data', {}).get('text/html', '') for o in cell.outputs)
            rendered.append(len(re.findall(r'<tr>', html)))
    assert rendered == COUNTS + [80], rendered
    for relative, expected in inputs.items():
        assert sha(ROOT/relative) == expected, 'SCIENTIFIC_ARTIFACT_DRIFT'
    NB.write_bytes(output_bytes[0])
    new = sha(NB)
    common = {'old_canonical_notebook_sha': OLD, 'new_canonical_notebook_sha': new}
    write('phase25d_notebook_compliance_repair_determinism', {
        **common, 'runs': runs, 'notebook_3x_byte_identical': True, 'execution_counts_removed': False,
        'normalization': 'No output normalization; record_timing=False disables transient execution timestamps only.',
        'frozen_inputs': inputs, 'rendered_epoch_row_counts': rendered, 'all_pass': True})
    write('phase25d_notebook_compliance_repair_visual_integrity', {**common, 'images': images,
        'image_count': len(images), 'image_base64_normalized': False, 'all_pass': True})
    print('Notebook audit repair complete:', new)


if __name__ == '__main__':
    main()
