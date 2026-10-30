"""Read-only scientific verification and additive Phase25D repair closure audits."""
import ast
import csv
import hashlib
import json
import re
from pathlib import Path
import nbformat

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT/'reports/audits'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read(name):
    return json.loads((AUD/(name+'.json')).read_text(encoding='utf-8'))


def write(name, data):
    (AUD/(name+'.json')).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def main():
    entry = read('phase25d_notebook_compliance_repair_entry_gate')
    det = read('phase25d_notebook_compliance_repair_determinism')
    vis = read('phase25d_notebook_compliance_repair_visual_integrity')
    docs = read('phase25d_project_control_docs_sync')
    freeze = read('phase25d_final_freeze')
    r2 = read('phase25d_oof_r2_reporting_reconciliation')
    scientific = {k:sha(ROOT/v['path']) == v['expected_sha256']
                  for k,v in entry['checks'].items() if k != 'notebook'}
    scientific.update({p:sha(ROOT/p) == h for p,h in det['frozen_inputs'].items()})
    assert all(scientific.values()), 'SCIENTIFIC_ARTIFACT_DRIFT'
    assert sha(AUD/'phase25d_final_freeze.json') == entry['original_final_freeze_sha256']
    nbpath = ROOT/entry['checks']['notebook']['path']
    new = sha(nbpath)
    old = entry['checks']['notebook']['expected_sha256']
    assert sha(AUD/'phase25d_notebook_compliance_pre_repair.ipynb') == old
    assert new == det['new_canonical_notebook_sha'] == vis['new_canonical_notebook_sha']
    nb = nbformat.read(nbpath, as_version=4)
    nbformat.validate(nb)
    codes = [c for c in nb.cells if c.cell_type == 'code']
    counts = [c.execution_count for c in codes]
    assert counts == list(range(1,len(codes)+1))
    errors = [o for c in codes for o in c.outputs if o.output_type == 'error']
    assert not errors
    imports = set()
    for cell in codes:
        tree = ast.parse(cell.source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module)
    allowed = {'pathlib','hashlib','json','io','numpy','pandas','matplotlib','matplotlib.pyplot','IPython.display'}
    assert imports <= allowed
    assert all(not re.search(r'\.(?:fit|backward|step|forward)\s*\(',c.source) for c in codes)
    # All scientific reads are explicit SHA checks or allowlisted frozen CSV/JSON reads.
    assert all(not re.search(r'(?:holdout|val808|test)', p, re.I) for p in det['frozen_inputs'])
    epoch_rows = []
    for c in codes:
        if re.search(r"= history\('",c.source):
            html = ''.join(o.get('data',{}).get('text/html','') for o in c.outputs)
            assert '...' not in html and 'display: none' not in html and 'display:none' not in html
            epoch_rows.append(len(re.findall(r'<tr>',html)))
    assert epoch_rows == [57,54,159,200,100,80]
    exp = ROOT/'experiments/phase25d_barr_benefit_router_v1_2_1_seed42'
    f3 = json.loads((exp/'fold3/training_closure.json').read_text())
    assert (f3['best_epoch'], f3['total_epochs'], f3['termination']) == (199,200,'max_epochs')
    index = (ROOT/'notebooks/phasewise/PHASE_INDEX.md').read_text(encoding='utf-8')
    assert index.count(new) == 2 and old in index
    for d in docs['documents']:
        assert sha(ROOT/d['path']) == d['after_sha256']
    assert docs['current_stale_phase25d_state_count'] == 0 and docs['all_pass']
    assert r2['remaining_r2_0_089'] == 0 and r2['r2_exact'] == freeze['oof_r2'] == 0.087657630443573
    assert vis['all_pass'] and vis['image_count'] == 8
    assert len(det['runs']) == 3 and all(r['sha256'] == new and r['errors'] == 0 for r in det['runs'])
    assert 'RUN_ALL_COMPLETE' in str(codes[-1].outputs)
    scope = {'science_changed':False, 'training_runs':0, 'optimizer_steps':0, 'model_forwards':0,
             'OOF_recomputed':False, 'features_recomputed':False, 'labels_recomputed':False,
             'router_holdout_reads':0, 'val808_reads':0, 'test_reads':0, 'phase25e_started':False}
    evidence = {'scope_basis':'Reviewed audit-only builder and all executed cell ASTs; allowlisted frozen input paths; no model/training imports, model loading, training or inference calls.',
                'executed_notebook_imports':sorted(imports), 'execution_counts':counts,
                'frozen_inputs_byte_checks':scientific,
                'builder_sha256':sha(ROOT/'scripts/analysis/repair_phase25d_notebook_compliance.py'),
                'canonical_builder_sha256':sha(ROOT/'scripts/analysis/build_phase25d_notebook.py')}
    addendum = {
        'classification':'NOTEBOOK_AND_GOVERNANCE_COMPLIANCE_REPAIR_ONLY', **scope,
        'old_notebook_sha':old, 'new_notebook_sha':new,
        'original_final_freeze_path':'reports/audits/phase25d_final_freeze.json',
        'original_final_freeze_sha256':entry['original_final_freeze_sha256'],
        'original_final_freeze_byte_identical':True,
        'oof_sha256':freeze['oof_sha256'], 'oof_sha_unchanged':scientific['oof'],
        'final_checkpoint_sha256':freeze['final_checkpoint_sha256'],
        'final_checkpoint_sha_unchanged':scientific['final_checkpoint'],
        'final_history_sha256':freeze['final_history_sha256'],
        'final_history_sha_unchanged':scientific['final_history'],
        'fold3_completed_epochs':f3['total_epochs'], 'fold3_best_epoch':f3['best_epoch'],
        'fold3_termination':f3['termination'], 'final_refit_rows':epoch_rows[-1],
        'final_checkpoint_epoch':freeze['final_router_epochs'], 'checkpoint_rule':'LAST_FIXED_EPOCH',
        'checkpoint_epoch_evidence':'Frozen final_refit_epoch_rule_execution and scientific final freeze; immutable 80-row final history. Checkpoint bytes hash-verified only; weights not loaded.',
        'Phase25E_started':False, 'phase25e_status':'ELIGIBLE_NOT_STARTED',
        'scientific_terminal_preserved':freeze['terminal'], 'scope_evidence':evidence}
    write('phase25d_final_freeze_notebook_compliance_addendum',addendum)
    result = {
        'classification':'NOTEBOOK_AND_GOVERNANCE_COMPLIANCE_REPAIR_ONLY', **scope,
        'scientific_artifacts_byte_identical':all(scientific.values()),
        **{f'fold{k}_epoch_rows':v for k,v in enumerate(epoch_rows[:5])},
        'final_refit_epoch_rows':epoch_rows[-1], 'all_epoch_tables_untruncated':True,
        'fold3_best_epoch':f3['best_epoch'], 'fold3_completed_epochs':f3['total_epochs'],
        'fold3_maxepoch_contract_pass':True, 'notebook_run_all_clean':True,
        'notebook_execution_errors':len(errors), 'notebook_failed_assertions':0,
        'notebook_tracebacks':0, 'notebook_visual_integrity_pass':vis['all_pass'],
        'notebook_3x_byte_identical':True, 'phase_index_exact_sha_present':True,
        'current_project_docs_phase25d_consistent':docs['all_pass'],
        'router_status':'TRAINED_FROZEN','phase25e_status':'ELIGIBLE_NOT_STARTED',
        'r2_exact':freeze['oof_r2'], 'lambda_selected':freeze['lambda_selected'],
        'routing_threshold_selected':freeze['routing_threshold_selected'],
        'resource_gate_evaluated':freeze['resource_gate_calibrated'],
        'old_notebook_sha':old,'new_notebook_sha':new,
        'final_freeze_addendum_sha256':sha(AUD/'phase25d_final_freeze_notebook_compliance_addendum.json'),
        'evidence':evidence, 'all_pass':True}
    write('phase25d_postrepair_final_compliance_check',result)
    print(json.dumps({k:v for k,v in result.items() if k != 'evidence'},indent=2))


if __name__ == '__main__':
    main()
