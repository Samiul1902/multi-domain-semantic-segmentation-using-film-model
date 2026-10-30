"""Phase25E protocol freeze: hashes, analytical arithmetic, label-blind memberships only.

No model imports, checkpoint deserialization, outcome joins, or policy evaluation.
OOF CSV is parsed with a strict two-column projection; label CSV is hash-only.
"""
import csv
import hashlib
import json
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT/'reports/audits'
TABLE = ROOT/'reports/tables'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_PRE_EXECUTION_RESOURCE_GATE_SPECIFICATION_FREEZE'
PRE = 'PHASE25D_CANONICAL_CLOSURE_REPAIRED__FULL_EPOCH_NOTEBOOK_AND_PROJECT_STATE_SYNCED__SCIENTIFIC_ARTIFACTS_UNCHANGED__PHASE25E_ELIGIBLE_NOT_STARTED'
TERMINAL = 'PHASE25E_RESOURCE_GATE_SPEC_V1_0_COMPLETE__COST_BUDGET_LAMBDA_TIE_AND_COMPARATOR_RULES_FROZEN__PHASE25E_POLICY_EVALUATION_ELIGIBLE_NOT_STARTED'
BUDGETS = ['0.00','0.10','0.25','0.50','1.00']
LAMBDAS = ['0.00','0.25','0.50','1.00']
SCOPE = dict(science_results_changed=False, router_changed=False, refiner_changed=False,
             features_changed=False, labels_changed=False, training_required=False,
             model_inference_required=False, holdout_outcomes_required=False,
             router_model_loads=0, router_forwards=0, refiner_forwards=0, global_forwards=0,
             training_runs=0, optimizer_steps=0, DeltaDice_outcomes_read=0,
             DeltaDice_outcome_joins=0, routing_metric_calculations=0,
             segmentation_metric_calculations=0, router_holdout_reads=0,
             router_holdout_feature_inference=0, VAL808_reads=0, TEST_reads=0,
             Phase25F_started=False, Phase25G_started=False, policy_outcome_evaluation_started=False)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def read(name):
    return json.loads((AUD/(name+'.json')).read_text(encoding='utf-8'))


def write(name, data):
    value = {'classification': CLASS, 'specification_revision': REV, **data}
    (AUD/(name+'.json')).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def table(path, rows, fields=None):
    rows = list(rows)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer = csv.DictWriter(f,fieldnames=fields or list(rows[0]),lineterminator='\n')
        writer.writeheader(); writer.writerows(rows)


def rational(x):
    return str(x.numerator)+'/'+str(x.denominator)


def main():
    prior = read('phase25d_postrepair_final_compliance_check')
    repaired = read('phase25d_notebook_compliance_repair_entry_gate')
    frozen = read('phase25d_final_freeze')
    spec = read('phase24_exact_implementation_spec')
    resource = read('phase24_resource_utility_contract')
    p24freeze = read('phase24_spec_repair_freeze')
    refiner = read('phase25a_resource_accounting')
    canonical = read('phase25a_canonical_final_freeze')
    global_cost = read('phase21_analytical_mac_count')
    bindings = {}
    for name,rec in repaired['checks'].items():
        expected = prior['new_notebook_sha'] if name == 'notebook' else rec['expected_sha256']
        bindings[rec['path']] = {'expected_sha256':expected,'sha256':sha(ROOT/rec['path'])}
    norm = 'reports/tables/phase25d_final_normalization_stats.csv'
    bindings[norm] = {'expected_sha256':frozen['final_normalization_sha256'],'sha256':sha(ROOT/norm)}
    extras = ['phase25d_final_freeze','phase25d_postrepair_final_compliance_check',
              'phase25d_final_freeze_notebook_compliance_addendum','phase25d_project_control_docs_sync',
              'phase24_resource_utility_contract','phase24_exact_implementation_spec',
              'phase24_spec_repair_freeze','phase25a_resource_accounting',
              'phase25a_canonical_final_freeze','phase21_analytical_mac_count',
              'phase24_paired_refinement_gain_contract']
    for name in extras:
        p = f'reports/audits/{name}.json'
        bindings[p] = {'sha256':sha(ROOT/p),'binding_mode':'frozen physical artifact SHA captured at spec entry'}
    for p in ['reports/tables/phase24_comparator_plan.csv','src/models/barr/regional_refiner.py']:
        bindings[p] = {'sha256':sha(ROOT/p)}
    bindings['src/models/barr/regional_refiner.py']['expected_sha256'] = refiner['source_sha256']
    bindings['reports/audits/phase25d_final_freeze.json']['expected_sha256'] = repaired['original_final_freeze_sha256']
    bindings['reports/audits/phase25d_final_freeze_notebook_compliance_addendum.json']['expected_sha256'] = prior['final_freeze_addendum_sha256']
    routing = spec['routing']
    checks = {
        'phase25d_complete':prior['all_pass'] and prior['router_status']=='TRAINED_FROZEN',
        'phase25e_eligible_not_started':prior['phase25e_status']=='ELIGIBLE_NOT_STARTED' and not prior['phase25e_started'],
        'prior_scope_zero':all(prior[k]==0 for k in ['router_holdout_reads','val808_reads','test_reads']),
        'all_bound_shas_match':all(v.get('expected_sha256',v['sha256'])==v['sha256'] for v in bindings.values()),
        'utility_exact':routing['utility']==resource['utility']=='U_hat_i = Delta_hat_i - lambda * C_i',
        'lambda_grid_exact':routing['lambda_grid']==p24freeze['bindings']['router_lambda_grid']==[0.0,0.25,0.5,1.0],
        'budgets_exact':routing['budgets']==resource['fixed_budget_evaluation']['points']==['0%','10%','25%','50%','100%'],
        'development_only_calibration':routing['threshold_source']=='ROUTER_DEVELOPMENT quantiles only',
        'single_universal_lambda_forbidden':routing['single_universal_lambda_forbidden'] and resource['single_universal_lambda_forbidden'],
        'canonical_refiner_compute_equal':canonical['actual_macs']==refiner['analytical_macs'],
        'fixed_crop_256':refiner['input_shape']==[1,4,256,256] and spec['roi']['input_resolution']==spec['refiner']['input_resolution']==256,
        'benefit_labels_unchanged':read('phase24_paired_refinement_gain_contract')['optional_development_labels']=={'beneficial':'DeltaDice >= +0.02','harmful':'DeltaDice <= -0.01','neutral':'otherwise'},
        'global_analytical_count_consistent':global_cost['total_macs']==sum(v['macs'] for v in global_cost['by_layer_type'].values()),
    }
    rules = (ROOT/'docs/RULES.md').read_text(encoding='utf-8')
    checks['phase25f_and_g_not_started'] = all(f'**Phase25{x} = NOT_STARTED**' in rules for x in ['F','G'])
    gate = dict(required_predecessor_terminal=PRE,
                predecessor_terminal_basis='User-authorized prior closure terminal; bound physical postrepair all-pass audit and freeze addendum substantiate it.',
                bindings=bindings, checks=checks, all_pass=all(checks.values()), **SCOPE)
    write('phase25e_spec_entry_gate',gate)
    if not gate['all_pass']:
        raise SystemExit('PHASE25E_RESOURCE_GATE_SPEC_BLOCKED__FROZEN_CONTRACT_CONFLICT')
    print('Entry gate PASS: scientific hashes and Phase24 contracts match.',flush=True)
    write('phase25e_phase24_resource_contract_binding',dict(
        utility=resource['utility'], fixed_budgets=BUDGETS, lambda_grid=LAMBDAS,
        lambda_source='phase24_exact_implementation_spec.json:routing.lambda_grid; phase24_spec_repair_freeze.json:bindings.router_lambda_grid',
        calibration_population='ROUTER_DEVELOPMENT',single_universal_lambda_forbidden=True,
        comparator_source='reports/tables/phase24_comparator_plan.csv',
        roi_direction_previously_frozen=False,
        orientation_review='Phase24 comparator CSV, architecture spec, exact implementation spec and resource contract specify geometry comparator but no sign/orientation. E4 comparator ruling freezes negative ROI area prospectively.',
        frozen_contract_conflicts=[],all_pass=True))

    b = ROOT/'data_cache/phase25b_barr_pre_refinement_features_v1_2'
    # Only identity and GT-free action availability are projected from metadata.
    meta = pd.read_csv(b/'metadata.csv',usecols=['sample_id','feature_row_index','action_available'],dtype={'sample_id':str})
    assert len(meta)==4957 and meta.sample_id.nunique()==4957
    assert set(meta.action_available.unique()) <= {0,1}
    assert sorted(meta.feature_row_index.tolist())==list(range(4957))
    meta = meta.sort_values('sample_id',kind='stable').reset_index(drop=True)
    ids = meta.sample_id.tolist()
    eligible = meta.action_available.to_numpy().astype(bool)
    n = len(ids); ne = int(eligible.sum())
    assert ne == canonical['canonical_action_availability']['action_available_n']
    # Freeze exactly one label-blind priority draw before any OOF score projection.
    rng = np.random.Generator(np.random.PCG64(42))
    priorities = rng.random(n)
    random_path = TABLE/'phase25e_random_routing_priority_seed42.csv'
    random_rows = [{'sample_id':sid,'random_priority':format(float(v),'.17g')} for sid,v in zip(ids,priorities)]
    if random_path.exists():
        existing = list(csv.DictReader(random_path.open(encoding='utf-8')))
        assert existing == random_rows, 'Frozen random priority conflict'
    else:
        table(random_path,random_rows)
    random_sha = sha(random_path)

    g = int(global_cost['total_macs']); r = int(refiner['analytical_macs'])
    dims = [spec['router']['input_dim_closed_form'],*spec['router']['hidden_dimensions_active'],1]
    router_macs = sum(a*b for a,b in zip(dims,dims[1:]))
    assert dims == [218,128,64,1] and router_macs == 36160
    cost = Fraction(r,g)
    costs = [cost if ok else Fraction(0) for ok in eligible]
    unique = set(c for c,ok in zip(costs,eligible) if ok)
    assert len(unique)==1
    exclusions = ['ROI bookkeeping','feature normalization','LayerNorm','GroupNorm', 'SiLU',
                  'embedding lookup','interpolation','pooling','FiLM elementwise modulation','sigmoid','bias additions']
    write('phase25e_resource_cost_contract_v1_0',dict(
        equation='C_i = REGIONAL_REFINER_ANALYTICAL_MACS / GLOBAL_MEDFILM_ANALYTICAL_MACS if action_available == 1 else 0',
        global_macs=g,regional_refiner_macs=r,cost_exact_ratio=rational(cost),cost_decimal=float(cost),
        cost_units='NORMALIZED_ANALYTICAL_MAC_RATIO',global_cost_already_sunk=True,
        router_cost_already_sunk=True,router_macs_excluded_from_C_i=True,
        router_macs=router_macs,router_formula='218*128 + 128*64 + 64*1',
        action_unavailable_cost=0,action_unavailable_decision='FORCED_SKIP',
        development_rows=n,eligible_rows=ne,forced_skip_rows=n-ne,
        analytical_accounting_label='ANALYTICAL MAC LOWER BOUND',excluded_operations=exclusions,
        average_system_cost='GLOBAL_MACS + ROUTER_MACS + (K / N_DEV) * REGIONAL_REFINER_MACS',
        not_latency=True,not_energy=True,not_memory=True,not_measured_device_cost=True,
        denominator_source='reports/audits/phase21_analytical_mac_count.json:total_macs',
        numerator_source='reports/audits/phase25a_resource_accounting.json:analytical_macs; canonical_final_freeze.json:actual_macs'))
    table(TABLE/'phase25e_analytical_compute_contract.csv',[
        dict(component='GLOBAL_MEDFILM',analytical_macs=g,role='sunk before decision',units='ANALYTICAL MAC LOWER BOUND'),
        dict(component='BARRBenefitRouterV1',analytical_macs=router_macs,role='pre-gate overhead; excluded from C_i',units='ANALYTICAL MAC LOWER BOUND'),
        dict(component='BARRRegionalRefinerV1',analytical_macs=r,role='avoidable incremental action',units='ANALYTICAL MAC LOWER BOUND')])
    cardinalities = [dict(budget=b,N_eligible=ne,K_b=int(Fraction(b)*ne) if b!='1.00' else ne,
                          denominator='eligible action-available rows',rounding='floor except 1.00 = N_eligible') for b in BUDGETS]
    table(TABLE/'phase25e_fixed_budget_cardinalities.csv',cardinalities)
    write('phase25e_fixed_budget_contract_v1_0',dict(budgets=BUDGETS,cardinalities=cardinalities,
        rule='K_b = N_eligible if b == 1 else floor(b * N_eligible)',
        exact_decimal_arithmetic=True,forced_skip_excluded=True,realized_fraction_never_exceeds_budget=True))
    write('phase25e_lambda_grid_contract_v1_0',dict(lambda_grid=LAMBDAS,interpolation_allowed=False,
        new_lambda_allowed=False,lambda_selected=False,utility='delta_hat_oof - lambda * C_i',
        development_prediction_source='Phase25D frozen OOF delta_hat_oof; never final-router in-sample predictions',
        no_performance_selection=True))
    tie_rule = 'routing_score DESCENDING, sample_id ASCENDING (case-sensitive ASCII identifiers)'
    write('phase25e_tie_break_contract_v1_0',dict(rank_rule=tie_rule,selection='first K_b eligible rows',
        outcome_tiebreak_forbidden=True,forbidden_tiebreaks=['delta_dice','gain_category','global_dice','candidate_dice','mask property','domain performance'],
        score_precision='Exact rational arithmetic from persisted decimal score strings and exact integer MAC ratio; routing_score decimal is a display approximation. routing_score_exact is authoritative.',
        conceptual_rule='U_hat_i > tau => EXECUTE else SKIP',
        exact_budget_membership_authority='deterministic ranked top-K',
        tau_low='score at rank K+1',tau_high='score at rank K',
        untied_tau='exact rational midpoint (tau_low + tau_high)/2, strictly between boundary scores',
        tied_boundary='EXACT_BUDGET_REQUIRES_DETERMINISTIC_TIE_BREAK; tau null; scalar alone insufficient',
        budget_zero_sentinel='EXECUTE_NONE',budget_one_sentinel='EXECUTE_ALL_ELIGIBLE',
        tie_break_applied='true for eligible rows in a score group of size >1; boundary_tied separately identifies a split tie group'))
    comparators = {
        'C1':dict(name='GLOBAL_ONLY',score=None,rule='K=0'),
        'C2':dict(name='ALWAYS_REFINE',score=None,rule='K=N_eligible'),
        'C3':dict(name='RANDOM_ROUTING',score='random_priority',orientation='higher first',seed=42,
                  algorithm='numpy Generator(PCG64(42)).random(N_DEV) in sample_id ascending order',
                  random_priority_sha256=random_sha,random_search_allowed=False),
        'C4':dict(name='ENTROPY_ROUTING',score='entropy_proxy_mean',orientation='higher first'),
        'C5':dict(name='MARGIN_ROUTING',score='-mean_boundary_margin',orientation='smaller raw margin first'),
        'C6':dict(name='PREDICTED_ROI_SIZE_ROUTING',score='-predicted_roi_area_fraction',orientation='smaller ROI first',
                  classification='SIMPLE_GEOMETRY_HEURISTIC',orientation_optimized=False),
        'C7':dict(name='LEARNED_PAIRED_GAIN_ROUTING',score='delta_hat_oof',orientation='higher first'),
        'C8':dict(name='LEARNED_GAIN_PLUS_RESOURCE_COST',score='delta_hat_oof - lambda*C_i',orientation='higher first'),
        'C9':dict(name='POST_SAFETY',scope='Phase25F only; excluded'),
        'C10':dict(name='ORACLE_BENEFIT_ROUTING',scope='later evaluation only; NONDEPLOYABLE DEVELOPMENT UPPER BOUND'),
        'C11':dict(name='JFS_LIKE_POST_HOC_SELECTOR',scope='excluded unless separately authorized')}
    write('phase25e_comparator_direction_contract_v1_0',dict(comparators=comparators,
        tie_rule=tie_rule,outcome_based_orientation_selection=False,random_frozen_before_score_projection=True))
    write('phase25e_final_router_threshold_calibration_contract_v1_0',dict(
        development_performance_analysis='frozen delta_hat_oof',
        final_deployment_calibration='frozen final Phase25D checkpoint on 4957 ROUTER_DEVELOPMENT feature rows only; later separately authorized execution',
        final_checkpoint_sha256=frozen['final_checkpoint_sha256'],normalization_sha256=frozen['final_normalization_sha256'],
        model_pass_allowed_in_this_task=False,outcomes_needed=False,
        prohibited_populations=['ROUTER_HOLDOUT','VAL808','TEST'],
        frozen_policies='same lambda, budgets, eligibility and tie contract',
        calibration='derive rank boundaries and tau from final-router DEV scores, not OOF thresholds transferred blindly',
        boundary_tie='persist score boundary and sample_id cutoff; scalar tau alone does not reproduce DEV exact K',
        endpoints=['EXECUTE_NONE','EXECUTE_ALL_ELIGIBLE'],
        deployment_caveat='Quantile calibration fixes membership/cardinality on DEV only; future cohort activation fraction is not guaranteed. Exact cohort budgets require authorized cohort ranking.',
        holdout_feature_inference_in_this_task=0))

    # Project only the permitted OOF identity and prediction columns. No labels are parsed or joined.
    oof_path = ROOT/'data_cache/phase25d_barr_benefit_router_v1_2_1/phase25d_oof_router_predictions.csv'
    oof = pd.read_csv(oof_path,usecols=['sample_id','delta_hat_oof'],dtype=str)
    assert list(oof.columns)==['sample_id','delta_hat_oof']
    assert len(oof)==n and oof.sample_id.nunique()==n and set(oof.sample_id)==set(ids)
    predictions = oof.set_index('sample_id').delta_hat_oof.to_dict()
    schema = pd.read_csv(b/'feature_schema.csv')
    matrix = np.load(b/'features.npy',mmap_mode='r',allow_pickle=False)
    assert matrix.shape==(4957,202)
    features = {}
    for name in ['entropy_proxy_mean','mean_boundary_margin','predicted_roi_area_fraction']:
        row = schema.loc[schema.feature_name==name]
        assert len(row)==1 and not bool(row.uses_GT.iloc[0]) and bool(row.pre_refinement.iloc[0])
        values = matrix[meta.feature_row_index.to_numpy(),int(row.feature_index.iloc[0])]
        assert np.isfinite(values).all()
        features[name] = [Fraction(str(float(v))) for v in values]
    scores = {'C3':[Fraction(row['random_priority']) for row in random_rows],
              'C4':features['entropy_proxy_mean'],
              'C5':[-v for v in features['mean_boundary_margin']],
              'C6':[-v for v in features['predicted_roi_area_fraction']],
              'C7':[Fraction(predictions[sid]) for sid in ids]}
    membership_dir = TABLE/'phase25e_policy_memberships_v1_0'
    membership_dir.mkdir(exist_ok=True)
    manifest=[]; selected_sets={}; equivalence=[]
    variants=[(c,'',scores[c]) for c in ['C3','C4','C5','C6','C7']]
    variants += [('C8',l,[v-Fraction(l)*c for v,c in zip(scores['C7'],costs)]) for l in LAMBDAS]
    c7_order = sorted([i for i in range(n) if eligible[i]],key=lambda i:(-scores['C7'][i],ids[i]))
    for comp,lam,score in variants:
        order=sorted([i for i in range(n) if eligible[i]],key=lambda i:(-score[i],ids[i]))
        rank={i:k+1 for k,i in enumerate(order)}
        frequency={}
        for i in order: frequency[score[i]]=frequency.get(score[i],0)+1
        if comp=='C8': assert order==c7_order
        for item in cardinalities:
            budget=item['budget']; k=item['K_b']
            policy=f'{comp}_'+(f'lambda{lam}_' if lam else '')+f'budget{budget}'
            selected=set(order[:k])
            assert len(selected)==k and all(eligible[i] for i in selected)
            selected_sets[(comp,lam,budget)]=selected
            if k==0 or k==ne:
                tied=False; low=high=tau=''; label='EXECUTE_NONE' if k==0 else 'EXECUTE_ALL_ELIGIBLE'
            else:
                high=score[order[k-1]]; low=score[order[k]]; tied=high==low
                tau='' if tied else (high+low)/2
                if not tied: assert low<tau<high
                label='EXACT_BUDGET_REQUIRES_DETERMINISTIC_TIE_BREAK' if tied else 'SCALAR_TAU_EQUIVALENT'
            path=membership_dir/(policy+'.csv')
            table(path,(dict(policy_id=policy,comparator=comp,**{'lambda':lam},budget=budget,
                sample_id=sid,action_available=int(eligible[i]),routing_score=format(float(score[i]),'.17g'),
                routing_score_exact=rational(score[i]),rank=rank.get(i,''),selected=int(i in selected),
                tie_break_applied=int(eligible[i] and frequency.get(score[i],0)>1),
                decision='EXECUTE' if i in selected else ('SKIP' if eligible[i] else 'FORCED_SKIP')) for i,sid in enumerate(ids)))
            selected_sha=hashlib.sha256(('\n'.join(sorted(ids[i] for i in selected))+'\n').encode()).hexdigest()
            manifest.append(dict(policy_id=policy,comparator=comp,**{'lambda':lam},budget=budget,
                N_DEV=n,N_eligible=ne,K_b=k,selected_count=len(selected),membership_path=path.relative_to(ROOT).as_posix(),
                membership_sha256=sha(path),selected_ids_sha256=selected_sha,
                tau_low=rational(low) if low!='' else '',tau_high=rational(high) if high!='' else '',
                tau=rational(tau) if tau!='' else '',boundary_tied=tied,tie_rule=tie_rule,threshold_policy=label))
            if comp=='C8':
                equal=selected==selected_sets[('C7','',budget)]
                assert equal
                equivalence.append(dict(lambda_value=lam,budget=budget,same_membership=equal,selected_count=k))
    table(TABLE/'phase25e_policy_membership_manifest.csv',manifest)
    write('phase25e_cost_variability_and_policy_redundancy_audit',dict(
        cost_classification='CONSTANT_INCREMENTAL_ACTION_COST',
        redundancy_classification='STRUCTURAL_POLICY_REDUNDANCY_UNDER_CONSTANT_ACTION_COST',
        unique_eligible_costs=len(unique),cost_exact_ratio=rational(cost),eligible_rows=ne,
        same_membership=all(x['same_membership'] for x in equivalence),comparisons=equivalence,
        reason='CONSTANT_NORMALIZED_INCREMENTAL_MAC_COST',
        proof='For eligible i,j, U_i(lambda)-U_j(lambda) = Delta_hat_i-Delta_hat_j. Subtracting the same constant preserves strict ordering and ties; identical sample_id tie breaking therefore preserves every top-K set.',
        full_rank_orders_equal=True,independent_statistical_evidence=False,
        retained_role='C8 remains the explicit resource-utility formulation; lambda changes absolute utility values, not fixed-budget rankings.',
        outcome_evaluation_performed=False))
    metrics = {
        'population':'eligible ROUTER_DEVELOPMENT; memberships frozen before any outcome join',
        'notation':'S=frozen routed set; E=eligible set; d_i=true DeltaDice; B={i in E:d_i>=0.02}; H={i in E:d_i<=-0.01}; K=|S|',
        'precision_at_budget':'|S intersect B| / K',
        'benefit_capture_at_budget':'sum(max(d_i,0) for i in S) / sum(max(d_i,0) for i in E)',
        'mean_true_delta_dice_among_routed':'sum(d_i for i in S) / K',
        'harmful_activation_rate':'|S intersect H| / K (harmful share among routed)',
        'beneficial_activation_rate':'|S intersect B| / |B| (coverage of beneficial eligible rows)',
        'missed_benefit_rate':'|B minus S| / |B|',
        'routing_regret_vs_oracle':'sum(d_i for i in oracle top-K) - sum(d_i for i in S)',
        'regret_mean_per_sample':'routing_regret_vs_oracle / N_DEV',
        'regret_mean_per_routed_sample':'routing_regret_vs_oracle / K',
        'zero_denominator':'null with reason UNDEFINED_ZERO_DENOMINATOR; sums over empty sets are zero',
        'benefit_labels':{'BENEFICIAL':'d_i >= +0.02','HARMFUL':'d_i <= -0.01','NEUTRAL':'otherwise'},
        'oracle':'top-K eligible TRUE DeltaDice DESC, sample_id ASC; NONDEPLOYABLE DEVELOPMENT UPPER BOUND; later evaluation only',
        'oracle_prohibitions':['deployable membership','comparator orientation','lambda selection','threshold selection'],
        'activation_fraction':'K / N_DEV; also report eligible_activation_fraction=K/N_eligible separately',
        'incremental_regional_macs':'(K / N_DEV) * REGIONAL_REFINER_MACS per DEV sample',
        'average_total_analytical_macs':'GLOBAL_MACS + ROUTER_MACS + (K / N_DEV) * REGIONAL_REFINER_MACS for pre-gate pipeline',
        'ratio_vs_global_only':'average_total_analytical_macs / GLOBAL_MACS (literal C1 anchor excludes router)',
        'ratio_vs_always_refine':'average_total_analytical_macs / (GLOBAL_MACS + (N_eligible/N_DEV)*REGIONAL_REFINER_MACS) (literal C2 no-routing anchor)',
        'anchor_clarification':'C1 and C2 bypass routing; gated K=0 and gated K=N_eligible retain router overhead and must be labeled separately.',
        'units':'ANALYTICAL MAC LOWER BOUND; never measured latency',
        'computed_in_spec_task':False}
    write('phase25e_execution_metrics_contract_v1_0',metrics)
    # Rehash every bound input after membership construction; labels were never parsed.
    assert all(sha(ROOT/p)==v['sha256'] for p,v in bindings.items())
    write('phase25e_no_execution_audit',dict(**SCOPE,
        outcome_access_semantics='Raw file bytes streamed only for required SHA verification; no outcome column parsed, materialized, inspected, joined or evaluated. OOF parser usecols is exactly sample_id and delta_hat_oof. Phase25C label CSV hash-only.',
        parsed_metadata_columns=['sample_id','feature_row_index','action_available'],
        parsed_oof_columns=['sample_id','delta_hat_oof'],
        feature_columns=list(features),random_priority_frozen_before_oof_projection=True,
        random_priority_sha256=random_sha,membership_policy_count=len(manifest),
        membership_row_count=sum(m['N_DEV'] for m in manifest),
        scientific_artifacts_byte_identical=True,script_sha256=sha(Path(__file__)),all_pass=True))
    print(f'Frozen {len(manifest)} policies; N_eligible={ne}; K={[x["K_b"] for x in cardinalities]}; router MACs={router_macs}; all 20 C7/C8 pairs equal.',flush=True)


if __name__=='__main__':
    main()
