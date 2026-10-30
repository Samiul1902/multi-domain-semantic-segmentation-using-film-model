"""Execute the Phase25E DESIGN/AUDIT notebook three times; no model or outcome access."""
import hashlib
import json
from pathlib import Path
import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT/'reports/audits'
NB = ROOT/'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate_specification.ipynb'


def main():
    inputs = {}
    for p in sorted(AUD.glob('phase25e_*.json')):
        if p.name not in ['phase25e_spec_final_check.json','phase25e_spec_governance.json','phase25e_spec_notebook_determinism.json']:
            inputs[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    for p in sorted((ROOT/'reports/tables').glob('phase25e_*.csv')):
        inputs[p.relative_to(ROOT).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    cells=[]

    def md(source):
        cells.append(nbformat.v4.new_markdown_cell(source))

    def code(source):
        cells.append(nbformat.v4.new_code_cell(source))

    md('# Phase25E resource-gate specification v1.0\n\n'
       '**DESIGN / AUDIT ONLY — no scientific policy outcome evaluation.**\n\n'
       'Revision: `ra_medfilm_barr_resource_gate_v1_0`. Phase25D remains COMPLETE_CANONICAL / TRAINED / FROZEN. '
       'This subphase freezes resource costs, budgets, lambda, tie rules, comparator directions and prospective memberships. '
       'Phase25E policy evaluation remains ELIGIBLE_NOT_STARTED; Phase25F and Phase25G remain NOT_STARTED.\n\n'
       'Every code cell is actually executed; execution counts remain present. Only transient execution timing metadata is disabled. '
       'No model imports or model loads, no forwards, no training, no outcome joins, no routing or segmentation metric calculations.')
    code('''from pathlib import Path
from fractions import Fraction
import csv, hashlib, json
from IPython.display import display, HTML
import pandas as pd
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'reports/audits/phase25e_spec_entry_gate.json').exists())
INPUTS = __INPUTS__
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''): h.update(block)
    return h.hexdigest()
for path, expected in INPUTS.items(): assert sha(ROOT/path)==expected,path
def audit(name):
    path='reports/audits/'+name+'.json'
    assert path in INPUTS
    return json.loads((ROOT/path).read_text(encoding='utf-8'))
def show_contract(name):
    obj=audit(name)
    print(json.dumps(obj,indent=2))
    return obj
def table(name):
    path='reports/tables/'+name+'.csv'
    assert path in INPUTS
    return pd.read_csv(ROOT/path,keep_default_na=False)
def show_table(df):
    display(HTML(df.to_html(index=False,max_rows=None,max_cols=None)))
print('Specification input hashes verified:',len(INPUTS))
'''.replace('__INPUTS__',repr(inputs)))
    md('## Predecessor binding\n\nThe entry gate binds the repaired Phase25D closure, final checkpoint, OOF table, final normalization, canonical notebook, Phase25B cache, Phase25C labels, compute artifacts and Phase24 contracts. Checkpoint and label bytes are hashed only; no weights or outcomes are deserialized.')
    code("""entry=show_contract('phase25e_spec_entry_gate')
assert entry['all_pass'] and all(entry['checks'].values())
for path,binding in entry['bindings'].items():
    assert sha(ROOT/path)==binding['sha256'],path
print('Predecessor and frozen input bindings PASS')""")
    md('## Phase24 resource contract\n\n$\\hat U_i=\\hat\\Delta_i-\\lambda C_i$. Calibration uses ROUTER_DEVELOPMENT only. No universal lambda may be promoted as the sole result. No frozen contract conflicts were found.')
    code("contract=show_contract('phase25e_phase24_resource_contract_binding')\nassert contract['all_pass'] and contract['single_universal_lambda_forbidden']")
    md('## Incremental resource cost and pre-gate overhead\n\n'
       '$C_i=\\mathrm{REGIONAL\\_REFINER\\_MACS}/\\mathrm{GLOBAL\\_MACS}$ for eligible actions; otherwise $C_i=0$ and FORCED_SKIP. '
       'Global and router costs are already incurred before the decision. Router overhead stays separate.\n\n'
       'All compute fields are **ANALYTICAL MAC LOWER BOUND**. These are not latency, energy, memory or measured device costs. '
       'ROI bookkeeping, normalization, LayerNorm/GroupNorm, SiLU, embedding lookup, interpolation and other non-Conv/Linear operations are excluded. '
       'For the gated system, average cost is global + router + activation fraction × refiner. Literal global-only and always-refine anchors bypass the router and are labeled separately.')
    code("""cost=show_contract('phase25e_resource_cost_contract_v1_0')
assert Fraction(cost['regional_refiner_macs'],cost['global_macs'])==Fraction(cost['cost_exact_ratio'])
assert cost['router_macs']==218*128+128*64+64*1==36160
assert cost['action_unavailable_cost']==0 and cost['router_macs_excluded_from_C_i']
show_table(table('phase25e_analytical_compute_contract'))""")
    md('## Constant-cost audit and structural policy redundancy\n\n'
       'For any eligible pair $i,j$, $\\hat U_i(\\lambda)-\\hat U_j(\\lambda)=\\hat\\Delta_i-\\hat\\Delta_j$. '
       'Subtracting one common constant preserves ordering and ties. The same sample-ID tie rule therefore gives identical C7 and C8 top-K membership. '
       '**STRUCTURAL_POLICY_REDUNDANCY_UNDER_CONSTANT_ACTION_COST** is reported explicitly; duplicate memberships are not independent statistical evidence. Lambda still changes absolute utility values.')
    code("""redundancy=show_contract('phase25e_cost_variability_and_policy_redundancy_audit')
assert redundancy['unique_eligible_costs']==1 and redundancy['same_membership']
assert all(x['same_membership'] for x in redundancy['comparisons'])
show_table(pd.DataFrame(redundancy['comparisons']))""")
    md('## Lambda grid and exact budget cardinalities\n\nNo interpolation, new lambda, or performance-based lambda selection. For budget $b<1$, $K_b=\\lfloor bN_{eligible}\\rfloor$; for $b=1$, $K_b=N_{eligible}$. Forced skips never consume eligible action slots.')
    code("""grid=show_contract('phase25e_lambda_grid_contract_v1_0')
assert grid['lambda_grid']==['0.00','0.25','0.50','1.00'] and not grid['lambda_selected']
budget_contract=show_contract('phase25e_fixed_budget_contract_v1_0')
cards=table('phase25e_fixed_budget_cardinalities')
assert cards.K_b.tolist()==[0,495,1239,2478,4957]
show_table(cards)""")
    md('## Deterministic rank, ties and tau\n\nEligible score DESCENDING, then sample_id ASCENDING; select the first K. Outcome fields cannot break ties. '
       'Untied boundaries use an exact rational midpoint strictly between ranks K and K+1. Tied boundaries require deterministic tie breaking and have no scalar-only equivalent. '
       'Budget endpoints use EXECUTE_NONE and EXECUTE_ALL_ELIGIBLE. Exact rational fields avoid arithmetic-induced changes in ranking; displayed decimal scores are approximate.')
    code("ties=show_contract('phase25e_tie_break_contract_v1_0')\nassert ties['outcome_tiebreak_forbidden']")
    md('## Comparator definitions and label-blind random freeze\n\nC3 uses one PCG64 seed-42 priority per sorted sample ID, persisted before OOF prediction projection. '
       'C4 entropy is higher-first; C5 uses negative boundary margin; C6 uses negative predicted ROI area as a simple prospective geometry heuristic. '
       'C7 uses frozen OOF predicted gain; C8 subtracts lambda times cost. C9 is excluded until Phase25F. C10 is a later nondeployable oracle only; C11 needs separate authorization.')
    code("""directions=show_contract('phase25e_comparator_direction_contract_v1_0')
random=table('phase25e_random_routing_priority_seed42')
assert list(random.columns)==['sample_id','random_priority'] and len(random)==4957
assert random.sample_id.nunique()==4957
assert sha(ROOT/'reports/tables/phase25e_random_routing_priority_seed42.csv')==directions['comparators']['C3']['random_priority_sha256']
print('Random priorities: 4957 unique IDs; frozen SHA verified; no outcome columns.')""")
    md('## Prospective membership verification and complete summaries\n\nAll 45 policies are hashed individually. This checks identities, ranks, cardinalities, tie handling and score thresholds only. It computes no outcome-based metric.')
    code("""manifest=table('phase25e_policy_membership_manifest')
assert len(manifest)==45
selections={}
for row in manifest.to_dict('records'):
    path=ROOT/row['membership_path']
    assert sha(path)==row['membership_sha256']
    with path.open(encoding='utf-8',newline='') as f:
        records=list(csv.DictReader(f))
    assert len(records)==4957 and len({r['sample_id'] for r in records})==4957
    assert not {'delta_dice','gain_category','global_dice','candidate_dice'} & set(records[0])
    eligible=[r for r in records if r['action_available']=='1']
    ranked=sorted(eligible,key=lambda r:(-Fraction(r['routing_score_exact']),r['sample_id']))
    assert [int(r['rank']) for r in ranked]==list(range(1,len(ranked)+1))
    k=int(row['K_b'])
    selected={r['sample_id'] for r in records if r['selected']=='1'}
    assert selected=={r['sample_id'] for r in ranked[:k]} and len(selected)==k
    assert hashlib.sha256(('\\n'.join(sorted(selected))+'\\n').encode()).hexdigest()==row['selected_ids_sha256']
    selections[(row['comparator'],str(row['lambda']),float(row['budget']))]=selected
    if 0<k<len(ranked):
        high=Fraction(ranked[k-1]['routing_score_exact']); low=Fraction(ranked[k]['routing_score_exact'])
        assert low==Fraction(row['tau_low']) and high==Fraction(row['tau_high'])
        if low<high:
            tau=Fraction(row['tau'])
            assert low<tau<high
            assert {r['sample_id'] for r in eligible if Fraction(r['routing_score_exact'])>tau}==selected
        else:
            assert row['threshold_policy']=='EXACT_BUDGET_REQUIRES_DETERMINISTIC_TIE_BREAK' and row['tau']==''
    else:
        assert row['tau']=='' and row['threshold_policy'] in ['EXECUTE_NONE','EXECUTE_ALL_ELIGIBLE']
for (comp,lam,budget),selected in selections.items():
    if comp=='C8': assert selected==selections[('C7','',budget)]
show_table(manifest[['policy_id','comparator','lambda','budget','N_eligible','K_b','selected_count','boundary_tied','threshold_policy']])
print('All 223065 membership rows verified; all exact ranks, cardinalities, thresholds and 20 C7/C8 equalities PASS.')""")
    md('## Later final-router deployment calibration\n\nOOF predictions support later development performance analysis. Final deployment thresholds require a separately authorized pass of the frozen final router over DEV only, using its frozen normalization. No GT is needed for quantile calibration. That pass is not performed here.')
    code("calibration=show_contract('phase25e_final_router_threshold_calibration_contract_v1_0')\nassert not calibration['model_pass_allowed_in_this_task'] and not calibration['outcomes_needed']")
    md('## Prospective evaluation metric definitions\n\nThe following formulas are frozen for later evaluation only. BENEFICIAL ≥ +0.02 and HARMFUL ≤ −0.01 remain unchanged; NEUTRAL is otherwise. Oracle regret uses a later true-DeltaDice top-K nondeployable upper bound. Undefined zero-denominator ratios remain null with a reason.')
    code("metrics=show_contract('phase25e_execution_metrics_contract_v1_0')\nassert metrics['computed_in_spec_task'] is False")
    md('## No-outcome assertion and locked populations\n\nROUTER_HOLDOUT outcomes and feature inference: 0. VAL808 reads: 0. TEST reads: 0; TEST remains locked until Phase39. No one-shot holdout evaluation. No models loaded or executed. '
       'SHA verification streams raw bytes but does not parse outcome values. The OOF source was projected to sample_id and delta_hat_oof only; Phase25C labels were hash-only.')
    code("""scope=show_contract('phase25e_no_execution_audit')
for key in ['router_model_loads','router_forwards','refiner_forwards','global_forwards','training_runs','optimizer_steps','DeltaDice_outcomes_read','DeltaDice_outcome_joins','routing_metric_calculations','segmentation_metric_calculations','router_holdout_reads','router_holdout_feature_inference','VAL808_reads','TEST_reads']:
    assert scope[key]==0
assert scope['scientific_artifacts_byte_identical'] and not scope['Phase25F_started']
assert scope['parsed_oof_columns']==['sample_id','delta_hat_oof']
print('RUN_ALL_COMPLETE: Phase25E specification audit PASS; no policy outcome evaluation.')""")
    md('## Execution handoff\n\nPhase25E resource-gate specification: **COMPLETE_FROZEN**. Phase25E scientific policy evaluation: **ELIGIBLE_NOT_STARTED**. '
       'A separate authorization is required before joining any outcome to these frozen memberships or running the final router for DEV threshold calibration. '
       'Preserve all membership hashes and report C7/C8 redundancy. Do not access ROUTER_HOLDOUT, VAL808 or TEST. Do not start Phase25F.')
    for i,c in enumerate(cells): c.id=f'p25e-spec-{i:03d}'
    builds=[]; data=[]
    for run in range(1,4):
        nb=nbformat.v4.new_notebook(cells=cells)
        nb.metadata.kernelspec={'name':'python3','display_name':'Python 3','language':'python'}
        NotebookClient(nb,timeout=180,kernel_name='python3',record_timing=False,
                       resources={'metadata':{'path':str(ROOT)}}).execute()
        nbformat.validate(nb)
        codes=[c for c in nb.cells if c.cell_type=='code']
        counts=[c.execution_count for c in codes]
        assert counts==list(range(1,len(codes)+1))
        assert not [o for c in codes for o in c.outputs if o.output_type=='error']
        assert 'RUN_ALL_COMPLETE' in str(codes[-1].outputs)
        raw=nbformat.writes(nb).encode('utf-8')+b'\n'
        data.append(raw)
        builds.append(dict(build=run,sha256=hashlib.sha256(raw).hexdigest(),execution_counts=counts,execution_errors=0,completion_marker=True))
        print('Executed spec notebook build',run,builds[-1]['sha256'],flush=True)
    assert data[0]==data[1]==data[2]
    NB.parent.mkdir(parents=True,exist_ok=True)
    NB.write_bytes(data[0])
    report=dict(notebook_path=NB.relative_to(ROOT).as_posix(),notebook_sha256=builds[0]['sha256'],
        inputs=inputs,builds=builds,three_times_byte_identical=True,execution_counts_retained=True,
        normalization='record_timing=False only; outputs and execution counts preserved',all_pass=True)
    (AUD/'phase25e_spec_notebook_determinism.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__': main()
