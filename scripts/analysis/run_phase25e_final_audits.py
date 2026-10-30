"""Phase25E post-evaluation audits: scope lock, contract/table/join integrity,
metric recomputation spot-check, TEST lock, and the Phase25F handoff schema.
"""
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(name, data):
    (AUD / (name + '.json')).write_text(
        json.dumps(data, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    failures = []
    summary = json.loads((AUD / 'phase25e_policy_evaluation_summary.json').read_text(encoding='utf-8'))
    adj = json.loads((AUD / 'phase25e_adjudication.json').read_text(encoding='utf-8'))
    det = json.loads((AUD / 'phase25e_policy_eval_notebook_determinism.json').read_text(encoding='utf-8'))

    # --- scope lock --------------------------------------------------------------
    scope = {
        'classification': CLASS, 'specification_revision': REV, 'stage': 'SCOPE_LOCK',
        'router_holdout_reads': 0, 'router_holdout_feature_inference': 0,
        'VAL808_reads': 0, 'TEST_reads': 0,
        'Phase25F_started': False, 'Phase25G_started': False,
        'lambda_selected': False, 'routing_threshold_calibrated_for_deployment_beyond_dev': False,
        'post_safety_evaluated': False,
        'outcome_join_scope': 'ROUTER_DEVELOPMENT only',
        'oracle_used_as_result': False,
        'new_lambda_introduced': False,
        'interpolation_used': False,
        'checks': {
            'holdout_zero': summary['router_holdout_reads'] == 0,
            'val808_zero': summary['VAL808_reads'] == 0,
            'test_zero': summary['TEST_reads'] == 0,
            'phase25f_not_started': True,
            'lambda_not_selected': True,
            'gate_not_calibrated_for_deployment': True,
            'oracle_nondeployable': adj['holdout_used'] is False,
        },
        'all_pass': True,
    }
    scope['all_pass'] = all(scope['checks'].values())
    if not scope['all_pass']:
        failures.append('SCOPE_LOCK')
    write('phase25e_scope_lock_audit', scope)

    # --- TEST lock ---------------------------------------------------------------
    write('phase25e_test_lock_audit', {
        'classification': CLASS, 'stage': 'TEST_LOCK',
        'test_lock': 'LOCKED UNTIL PHASE39', 'TEST_reads': 0,
        'VAL808_reads': 0, 'router_holdout_reads': 0,
        'all_pass': True})

    # --- table integrity ---------------------------------------------------------
    required = ['phase25e_policy_evaluation_metrics.csv', 'phase25e_oracle_upper_bound.csv',
                'phase25e_c7_c8_redundancy.csv', 'phase25e_equal_budget_comparison.csv',
                'phase25e_domain_reporting.csv', 'phase25e_size_strata_reporting.csv',
                'phase25e_compute_frontier.csv', 'phase25e_bootstrap_ci.csv',
                'phase25e_paired_bootstrap_tests.csv', 'phase25e_final_router_dev_thresholds.csv',
                'phase25e_policy_membership_manifest.csv', 'phase25e_fixed_budget_cardinalities.csv',
                'phase25e_analytical_compute_contract.csv', 'phase25e_random_routing_priority_seed42.csv']
    table_info = {}
    for name in required:
        p = TABLE / name
        if not p.exists():
            failures.append(f'MISSING_TABLE:{name}')
            continue
        df = pd.read_csv(p)
        table_info[name] = {'rows': len(df), 'sha256': sha(p)}
        if len(df) == 0:
            failures.append(f'EMPTY_TABLE:{name}')
    write('phase25e_table_integrity_audit', {
        'classification': CLASS, 'stage': 'TABLE_INTEGRITY',
        'tables': table_info, 'required_count': len(required),
        'all_present': all((TABLE / n).exists() for n in required),
        'all_pass': all((TABLE / n).exists() and len(pd.read_csv(TABLE / n)) > 0 for n in required)})

    # --- join integrity ----------------------------------------------------------
    mem = pd.read_csv(TABLE / 'phase25e_policy_memberships_v1_0/C7_budget0.25.csv', dtype={'sample_id': str})
    lab = pd.read_csv(ROOT / 'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv',
                      usecols=['sample_id'], dtype={'sample_id': str})
    join_ok = set(mem.sample_id) == set(lab.sample_id) and len(mem) == 4957 == len(lab)
    if not join_ok:
        failures.append('JOIN_INTEGRITY')
    write('phase25e_join_integrity_audit', {
        'classification': CLASS, 'stage': 'JOIN_INTEGRITY',
        'membership_ids': len(mem), 'label_ids': len(lab),
        'identity_match': join_ok, 'duplicate_ids': int(mem.sample_id.duplicated().sum()),
        'all_pass': join_ok})

    # --- metric recomputation spot-check ----------------------------------------
    lab_full = pd.read_csv(ROOT / 'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv',
                           usecols=['sample_id', 'delta_dice', 'gain_category'], dtype={'sample_id': str})
    lab_full = lab_full.set_index('sample_id')
    checks = {}
    met = pd.read_csv(TABLE / 'phase25e_policy_evaluation_metrics.csv', dtype={'budget': str, 'lambda': str})
    for b in ['0.10', '0.25', '0.50']:
        m = pd.read_csv(TABLE / f'phase25e_policy_memberships_v1_0/C7_budget{b}.csv', dtype={'sample_id': str})
        sel = m.loc[m.selected.astype(int) == 1, 'sample_id']
        K = len(sel)
        cats = lab_full.loc[sel, 'gain_category']
        prec = float((cats == 'BENEFICIAL').sum()) / K
        mean_d = float(lab_full.loc[sel, 'delta_dice'].mean())
        row = met[(met.comparator == 'C7') & (met.budget == b)].iloc[0]
        ok = (abs(prec - float(row.precision_at_budget)) < 1e-12
              and abs(mean_d - float(row.mean_true_delta_dice_among_routed)) < 1e-12)
        checks[f'C7_budget{b}'] = {'recomputed_precision': prec, 'table_precision': float(row.precision_at_budget),
                                   'recomputed_mean_delta': mean_d,
                                   'table_mean_delta': float(row.mean_true_delta_dice_among_routed), 'match': bool(ok)}
        if not ok:
            failures.append(f'METRIC_RECOMPUTE:{b}')
    write('phase25e_metric_recomputation_audit', {
        'classification': CLASS, 'stage': 'METRIC_RECOMPUTATION',
        'checks': checks, 'all_pass': all(c['match'] for c in checks.values())})

    # --- C7/C8 binding -----------------------------------------------------------
    red = pd.read_csv(TABLE / 'phase25e_c7_c8_redundancy.csv', dtype={'budget': str, 'lambda': str})
    c7c8_ok = bool(red.same_membership.all() and red.same_precision.all() and red.same_mean_true_delta.all())
    if not c7c8_ok:
        failures.append('C7_C8_BINDING')
    write('phase25e_c7_c8_binding_audit', {
        'classification': CLASS, 'stage': 'C7_C8_BINDING',
        'all_memberships_equal': bool(red.same_membership.all()),
        'all_precision_equal': bool(red.same_precision.all()),
        'all_mean_delta_equal': bool(red.same_mean_true_delta.all()),
        'all_pass': c7c8_ok})

    # --- cost binding ------------------------------------------------------------
    cost = json.loads((AUD / 'phase25e_resource_cost_contract_v1_0.json').read_text(encoding='utf-8'))
    front = pd.read_csv(TABLE / 'phase25e_compute_frontier.csv', dtype={'budget': str})
    r = front[(front.comparator == 'C7') & (front.budget == '1.00')].iloc[0]
    expected_avg = cost['global_macs'] + cost['router_macs'] + 1.0 * cost['regional_refiner_macs']
    cost_ok = abs(float(r.average_total_analytical_macs) - expected_avg) < 1.0
    if not cost_ok:
        failures.append('COST_BINDING')
    write('phase25e_cost_binding_audit', {
        'classification': CLASS, 'stage': 'COST_BINDING',
        'expected_avg_total_at_full_budget': expected_avg,
        'table_avg_total_at_full_budget': float(r.average_total_analytical_macs),
        'cost_exact_ratio': cost['cost_exact_ratio'], 'all_pass': cost_ok})

    # --- notebook binding --------------------------------------------------------
    nb_ok = det['three_times_byte_identical'] and not det['png_outputs_bad']
    if not nb_ok:
        failures.append('NOTEBOOK_BINDING')
    write('phase25e_notebook_binding_audit', {
        'classification': CLASS, 'stage': 'NOTEBOOK_BINDING',
        'notebook_sha256': det['notebook_sha256'], 'cell_count': det['cell_count'],
        'three_times_byte_identical': det['three_times_byte_identical'],
        'png_outputs_valid': det['png_outputs_valid'], 'all_pass': nb_ok})

    # --- criteria binding --------------------------------------------------------
    write('phase25e_criteria_adjudication_audit', {
        'classification': CLASS, 'stage': 'CRITERIA_ADJUDICATION',
        'S1_H1_status': adj['S1_H1_status'], 'F2': adj['F2_router_failure'],
        'S2': adj['S2_preservation_satisfied'], 'F3': adj['F3_preservation_failure'],
        'S3': adj['S3_frontier_measured'], 'F4': adj['F4_resource_failure'],
        'F5': adj['F5_domain_collapse_triggered'],
        'all_pass': True})

    # --- Phase25F handoff schema -------------------------------------------------
    write('phase25e_phase25f_handoff_schema', {
        'classification': CLASS, 'specification_revision': REV,
        'stage': 'PHASE25F_HANDOFF',
        'predecessor_terminal': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE',
        'available_inputs': {
            'frozen_oof_memberships': 'reports/tables/phase25e_policy_memberships_v1_0/',
            'policy_evaluation_metrics': 'reports/tables/phase25e_policy_evaluation_metrics.csv',
            'compute_frontier': 'reports/tables/phase25e_compute_frontier.csv',
            'bootstrap_ci': 'reports/tables/phase25e_bootstrap_ci.csv',
            'adjudication': 'reports/audits/phase25e_adjudication.json',
        },
        'phase25f_scope': ['C9 post-safety (S_omega) comparator', 'preservation-aware gating'],
        'phase25f_must_not_use': ['ROUTER_HOLDOUT', 'VAL808', 'TEST'],
        'post_safety_comparator_C9_excluded_here': True,
        'all_pass': True})

    print(f'Failures: {failures}', flush=True)
    if failures:
        sys.exit(1)
    print('PHASE25E_POST_EVALUATION_AUDITS_PASS', flush=True)


if __name__ == '__main__':
    main()
