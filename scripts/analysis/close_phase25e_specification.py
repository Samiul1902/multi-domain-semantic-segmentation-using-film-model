"""Additive governance sync and final verification for the Phase25E spec only."""
import ast
import csv
import hashlib
import json
import re
from pathlib import Path
import nbformat

from freeze_phase25e_resource_gate_spec import ROOT, AUD, TABLE, REV, CLASS, SCOPE, TERMINAL, sha, read, write

DOCS = [f'docs/{n}.md' for n in ['ARCHITECTURE','DESIGN','MEMORY','PRD','RULES','TASKS']] + ['notebooks/phasewise/PHASE_INDEX.md']


def main():
    entry=read('phase25e_spec_entry_gate')
    det=read('phase25e_spec_notebook_determinism')
    assert entry['all_pass'] and det['all_pass'] and det['three_times_byte_identical']
    assert all(sha(ROOT/p)==v['sha256'] for p,v in entry['bindings'].items())
    assert all(sha(ROOT/p)==s for p,s in det['inputs'].items())
    nbpath=ROOT/det['notebook_path']; nbsha=sha(nbpath)
    assert nbsha==det['notebook_sha256']
    nb=nbformat.read(nbpath,as_version=4); nbformat.validate(nb)
    codes=[c for c in nb.cells if c.cell_type=='code']
    assert [c.execution_count for c in codes]==list(range(1,len(codes)+1))
    assert not [o for c in codes for o in c.outputs if o.output_type=='error']
    assert 'RUN_ALL_COMPLETE' in str(codes[-1].outputs)
    imports=set()
    for c in codes:
        for node in ast.walk(ast.parse(c.source)):
            if isinstance(node,ast.Import): imports.update(a.name for a in node.names)
            elif isinstance(node,ast.ImportFrom): imports.add(node.module)
    assert imports <= {'pathlib','fractions','csv','hashlib','json','IPython.display','pandas'}
    for source in ['freeze_phase25e_resource_gate_spec.py','build_phase25e_specification_notebook.py']:
        text=(ROOT/'scripts/analysis'/source).read_text(encoding='utf-8')
        assert not re.search(r'\b(?:import torch|from torch|torch\.load|\.backward\(|optimizer\.step\()',text)

    backup=AUD/'phase25e_spec_pre_sync_control_docs'
    backup.mkdir(exist_ok=True)
    bindings=[]
    block=(
        '## Phase25E specification freeze — current state (2026-10-01)\n\n'
        'Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. '
        'Phase25E resource-gate specification: **COMPLETE_FROZEN** '
        f'(`{REV}`). Phase25E scientific policy evaluation: **ELIGIBLE_NOT_STARTED**. '
        'Phase25F: **NOT_STARTED**. Phase25G: **NOT_STARTED**. Phase25E is not fully complete.\n\n'
        'The normalized incremental action cost is exactly `3,230,662,656 / 31,551,740,928` '
        '(`1051648/10270749`, approximately `0.10239253242387678`) for available actions; '
        'unavailable actions cost zero and are FORCED_SKIP. Pre-gate router overhead is '
        '`36,160` Conv/Linear MACs, separate from action cost. All compute is '
        '**ANALYTICAL MAC LOWER BOUND**, never measured latency.\n\n'
        'Lambdas `{0.00, 0.25, 0.50, 1.00}` and budgets `{0%, 10%, 25%, 50%, 100%}` are frozen. '
        'All 4,957 DEV rows are action-available; exact top-K counts are `{0, 495, 1239, 2478, 4957}`. '
        'Rank by score descending, sample_id ascending. C6 uses negative predicted ROI area, '
        'a prospective geometry heuristic. Random priorities (PCG64 seed 42) and 45 label-blind '
        'memberships are frozen before outcomes. Under constant action cost, C7 and C8 have '
        '**identical membership at every fixed budget and lambda**; they are not independent evidence.\n\n'
        'No models were loaded or run, no outcomes were joined, and no policy metrics were calculated. '
        'ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39. '
        'Final-router DEV threshold calibration and policy outcome evaluation require separate execution authorization.\n\n'
        f'Executed DESIGN/AUDIT notebook: `{det["notebook_path"]}`; SHA-256 `{nbsha}` (3× byte-identical). '
        'Evidence: `reports/audits/phase25e_spec_final_check.json`, '
        '`reports/audits/phase25e_spec_governance.json`, and '
        '`reports/tables/phase25e_policy_membership_manifest.csv`.\n\n'
        f'Specification terminal: `{TERMINAL}`.\n\n')
    for rel in DOCS:
        path=ROOT/rel; archived=backup/path.name
        if not archived.exists(): archived.write_bytes(path.read_bytes())
        before=archived.read_text(encoding='utf-8'); text=before
        # Preserve complete original documents; add the new subphase state, not a replacement scientific history.
        first,rest=text.split('\n',1)
        text=first+'\n\n'+block+rest.lstrip('\n')
        if rel=='docs/RULES.md':
            text=text.replace('- **Phase25E = ELIGIBLE_NOT_STARTED**.',
                '- **Phase25E resource-gate specification = COMPLETE_FROZEN**.\n'
                '- **Phase25E scientific policy evaluation = ELIGIBLE_NOT_STARTED**.')
            assert text.split('## 15.')[1]==before.split('## 15.')[1]
        elif rel=='docs/TASKS.md':
            text=text.replace('| 25E | Resource-aware pre-execution gate | **ELIGIBLE_NOT_STARTED** |',
                '| 25E | Resource-aware pre-execution gate | Specification **COMPLETE_FROZEN**; scientific policy evaluation **ELIGIBLE_NOT_STARTED** |')
            text=text.replace('| Phase 25E | **ELIGIBLE_NOT_STARTED** | Phase25D canonical completion; no gate execution |',
                '| Phase25E specification | **COMPLETE_FROZEN** | `phase25e_spec_final_check.json`; notebook SHA `'+nbsha+'` |\n'
                '| Phase25E scientific policy evaluation | **ELIGIBLE_NOT_STARTED** | Frozen memberships; no outcome evaluation |')
            text=text.replace('Phase **25E** is **ELIGIBLE_NOT_STARTED**.',
                'Phase **25E specification** is **COMPLETE_FROZEN**; **scientific policy evaluation** is **ELIGIBLE_NOT_STARTED**.')
            marker='### Historical (retained as provenance — Phase-13 era)'
            assert text.split(marker)[1]==before.split(marker)[1]
        elif rel=='docs/MEMORY.md':
            text=text.replace('**Phase 25E\nELIGIBLE_NOT_STARTED**',
                '**Phase25E specification COMPLETE_FROZEN** · **Phase25E scientific policy evaluation ELIGIBLE_NOT_STARTED**')
        elif rel.endswith('PHASE_INDEX.md'):
            lines=text.splitlines()
            idx=next(i for i,l in enumerate(lines) if l.startswith('| **25D** |'))
            lines.insert(idx+1,
                f'| **25E-SPEC** | **Resource-gate specification** | Prospective cost/lambda/budget/tie/comparator and membership freeze | `{det["notebook_path"]}` | `{nbsha}` | **COMPLETE_FROZEN** | **Canonical DESIGN/AUDIT** | — | `{TERMINAL}` | 0 | 45 policies; no outcome evaluation; 3× byte-identical; Phase25E scientific policy evaluation ELIGIBLE_NOT_STARTED |')
            text='\n'.join(lines)+'\n'
            text=text.replace('phase_25e_resource_gate/\n',
                'phase_25e_resource_gate/\n  phase25e_resource_gate_specification.ipynb                  # COMPLETE_FROZEN DESIGN/AUDIT\n')
            text=text.replace('The list above covers every frozen notebook from Phase 21 through Phase 25D.',
                f'- **Phase25E specification notebook** (`phase25e_resource_gate_specification.ipynb`) — SHA-256 `{nbsha}`\n\n'
                'The list above covers every frozen notebook from Phase21 through the Phase25E specification subphase.')
        path.write_text(text,encoding='utf-8',newline='')
        assert 'Phase25E resource-gate specification: **COMPLETE_FROZEN**' in text
        assert 'Phase25E scientific policy evaluation: **ELIGIBLE_NOT_STARTED**' in text
        bindings.append(dict(path=rel,before_sha256=sha(archived),after_sha256=sha(path),original_preserved_at=archived.relative_to(ROOT).as_posix()))

    # Independently check all physical policy file hashes and cardinalities.
    with (TABLE/'phase25e_policy_membership_manifest.csv').open(encoding='utf-8',newline='') as f:
        manifest=list(csv.DictReader(f))
    assert len(manifest)==45 and len({r['policy_id'] for r in manifest})==45
    for row in manifest:
        path=ROOT/row['membership_path']
        assert sha(path)==row['membership_sha256']
        with path.open(encoding='utf-8',newline='') as f:
            rows=list(csv.DictReader(f))
        assert len(rows)==4957 and sum(int(r['selected']) for r in rows)==int(row['K_b'])
        assert not {'delta_dice','gain_category','global_dice','candidate_dice'} & set(rows[0])
    cost=read('phase25e_resource_cost_contract_v1_0')
    redundancy=read('phase25e_cost_variability_and_policy_redundancy_audit')
    scope=read('phase25e_no_execution_audit')
    assert scope['all_pass'] and all(scope[k]==v for k,v in SCOPE.items())
    assert scope['script_sha256']==sha(ROOT/'scripts/analysis/freeze_phase25e_resource_gate_spec.py')
    artifacts={}
    for p in sorted(AUD.glob('phase25e_*.json')):
        if p.name not in ['phase25e_spec_governance.json','phase25e_spec_final_check.json']:
            artifacts[p.relative_to(ROOT).as_posix()]=sha(p)
    for p in sorted(TABLE.glob('phase25e_*.csv')): artifacts[p.relative_to(ROOT).as_posix()]=sha(p)
    artifacts[det['notebook_path']]=nbsha
    checks={
        'phase25d_complete':entry['checks']['phase25d_complete'],
        'cost_equation_exact':cost['cost_exact_ratio']=='1051648/10270749',
        'cost_normalization_denominator_exact':cost['global_macs']==read('phase21_analytical_mac_count')['total_macs'],
        'action_unavailable_cost_zero':cost['action_unavailable_cost']==0,
        'router_overhead_separate':cost['router_macs_excluded_from_C_i'],
        'lambda_grid_frozen':read('phase25e_lambda_grid_contract_v1_0')['lambda_grid']==['0.00','0.25','0.50','1.00'],
        'budget_grid_frozen':read('phase25e_fixed_budget_contract_v1_0')['budgets']==['0.00','0.10','0.25','0.50','1.00'],
        'budget_cardinality_rounding_frozen':read('phase25e_fixed_budget_contract_v1_0')['exact_decimal_arithmetic'],
        'tie_break_frozen':read('phase25e_tie_break_contract_v1_0')['outcome_tiebreak_forbidden'],
        'tau_semantics_frozen':all(r['threshold_policy'] in ['EXECUTE_NONE','EXECUTE_ALL_ELIGIBLE','SCALAR_TAU_EQUIVALENT','EXACT_BUDGET_REQUIRES_DETERMINISTIC_TIE_BREAK'] for r in manifest),
        'random_comparator_frozen':sha(TABLE/'phase25e_random_routing_priority_seed42.csv')==scope['random_priority_sha256'],
        'entropy_direction_frozen':read('phase25e_comparator_direction_contract_v1_0')['comparators']['C4']['score']=='entropy_proxy_mean',
        'margin_direction_frozen':read('phase25e_comparator_direction_contract_v1_0')['comparators']['C5']['score']=='-mean_boundary_margin',
        'roi_size_direction_frozen':read('phase25e_comparator_direction_contract_v1_0')['comparators']['C6']['score']=='-predicted_roi_area_fraction',
        'learned_gain_direction_frozen':read('phase25e_comparator_direction_contract_v1_0')['comparators']['C7']['score']=='delta_hat_oof',
        'constant_cost_redundancy_tested':redundancy['same_membership'] and len(redundancy['comparisons'])==20,
        'membership_frozen_before_outcomes':scope['DeltaDice_outcome_joins']==scope['DeltaDice_outcomes_read']==0,
        'scientific_artifacts_byte_identical':all(sha(ROOT/p)==v['sha256'] for p,v in entry['bindings'].items()),
        'notebook_run_all_clean':all(r['execution_errors']==0 for r in det['builds']),
        'notebook_3x_byte_identical':all(r['sha256']==nbsha for r in det['builds']),
        'seven_core_control_docs_synchronized':len(bindings)==7,
    }
    assert all(checks.values()),checks
    write('phase25e_spec_governance',dict(**SCOPE,
        phase25d_status='COMPLETE_CANONICAL / TRAINED / FROZEN',
        phase25e_specification_status='COMPLETE_FROZEN',
        phase25e_scientific_policy_evaluation_status='ELIGIBLE_NOT_STARTED',
        phase25e_fully_complete=False,phase25f_status='NOT_STARTED',phase25g_status='NOT_STARTED',
        test_lock='LOCKED UNTIL PHASE39',documents=bindings,
        historical_provenance_preserved=True,hard_governance_rules_unchanged=True,
        canonical_artifact_sha256=artifacts,membership_manifest_sha256=sha(TABLE/'phase25e_policy_membership_manifest.csv'),
        notebook_sha256=nbsha,required_next_authorization='Separate Phase25E policy execution authorization before outcome joins or final-router DEV inference.',
        terminal=TERMINAL,all_pass=True))
    write('phase25e_spec_final_check',dict(**SCOPE,**checks,
        cost_units='NORMALIZED_ANALYTICAL_MAC_RATIO',
        eligible_rows=cost['eligible_rows'],router_analytical_macs=cost['router_macs'],
        policy_count=len(manifest),notebook_sha256=nbsha,
        notebook_execution_counts=[c.execution_count for c in codes],notebook_imports=sorted(imports),
        spec_governance_sha256=sha(AUD/'phase25e_spec_governance.json'),terminal=TERMINAL,all_pass=True))
    print(json.dumps(dict(all_pass=True,notebook_sha256=nbsha,policies=len(manifest),
                         eligible_rows=cost['eligible_rows'],same_membership=redundancy['same_membership'],
                         phase25e_scientific_policy_evaluation='ELIGIBLE_NOT_STARTED',terminal=TERMINAL),indent=2))


if __name__=='__main__': main()
