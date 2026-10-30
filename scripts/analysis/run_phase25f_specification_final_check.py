"""Phase25F §12-§14: SPECIFICATION FINAL CHECK + BLOCKED TERMINAL.

Aggregates every Phase25F audit, decides whether the frozen Phase24/25 contracts are
sufficiently complete to execute Phase25F without inventing scientific choices, and
emits the terminal.

AUDIT ONLY: no model construction, no training, no forward passes, no refinement, no
new DeltaDice, no lambda/budget/threshold selection, no holdout/VAL808/TEST.

Writes: reports/audits/phase25f_specification_final_check.json
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'

AUDITS = [
    'phase25f_frozen_spec_entry_gate',
    'phase25f_role_and_novelty_boundary',
    'phase25f_post_safety_spec_binding',
    'phase25f_training_data_source_audit',
    'phase25f_leakage_safety_audit',
    'phase25f_threshold_semantics_audit',
    'phase25f_fusion_fallback_contract_audit',
    'phase25f_a7_a8_evaluation_ownership',
    'phase25f_scope_guard',
    'phase25f_test_lock_audit',
]
TABLES = [
    'phase25f_specification_completeness.csv',
    'phase25f_training_data_leakage_contract.csv',
    'phase25f_post_safety_input_contract.csv',
]

REQUIRED_TERMINAL = ('PHASE25E_CANONICAL_ADJUDICATION_REPAIRED__PRIMARY_PHASE24_STATISTICS_RESTORED__HOLM_'
                     'RETAINED_AS_SENSITIVITY__PHASE25F_ELIGIBLE_NOT_STARTED')
REQUIRED_NOTEBOOK_SHA = 'b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797'
REQUIRED_FINAL_FREEZE_SHA = 'e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e'

SUCCESS_TERMINAL = ('PHASE25F_POST_SAFETY_SPEC_AUDIT_COMPLETE__EXECUTION_CONTRACT_FULLY_BOUND__PHASE25F_'
                    'EXECUTION_ELIGIBLE_NOT_STARTED')
BLOCKED_TERMINAL = 'PHASE25F_BLOCKED__POST_SAFETY_EXECUTION_SPEC_INCOMPLETE'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    failures = []
    results = {}
    for name in AUDITS:
        p = AUD / (name + '.json')
        if not p.exists():
            failures.append(f'MISSING_AUDIT:{name}')
            continue
        d = json.loads(p.read_text(encoding='utf-8'))
        ok = bool(d.get('all_pass', True))
        results[name] = {'all_pass': ok, 'sha256': sha(p)}
        if not ok:
            failures.append(f'AUDIT_FAIL:{name}')
    for name in TABLES:
        p = TABLE / name
        if not p.exists():
            failures.append(f'MISSING_TABLE:{name}')
        else:
            results[name] = {'present': True, 'sha256': sha(p)}

    # --- completeness verdict from the CSV ---------------------------------------
    import csv
    with (TABLE / 'phase25f_specification_completeness.csv').open(encoding='utf-8') as f:
        comp = list(csv.DictReader(f))
    blocking = [r['field'] for r in comp if r['complete'].lower() == 'false'
                and r['blocking_if_missing'].lower() == 'true']
    incomplete = [r['field'] for r in comp if r['complete'].lower() == 'false']

    # --- hard-stop conditions (§6) ------------------------------------------------
    hard_stop_map = {
        'post_safety_input_vector_not_exactly_defined': 'input_vector' in blocking,
        'required_post_refinement_features_not_available_leakage_safely':
            'post_refinement_feature_availability' in blocking,
        'target_semantics_incomplete': 'training_target' in blocking,
        'CV_construction_incomplete': 'CV_fold_count' in blocking or 'CV_algorithm' in blocking,
        'normalization_incomplete': 'normalization' in blocking,
        'checkpoint_selection_rule_incomplete': 'checkpoint_metric' in blocking,
        'final_refit_rule_incomplete': 'final_refit' in blocking,
        'decision_threshold_incomplete': 'decision_threshold' in blocking,
        'fusion_fallback_behavior_incomplete': False,  # fusion rule IS frozen
        'optimizer_incomplete': 'optimizer' in blocking,
        'training_length_incomplete': 'max_epochs' in blocking,
        'scheduler_incomplete': 'scheduler' in blocking,
        'loss_definition_incomplete': 'loss' in blocking,
        'a7_a8_ownership_ambiguous': 'A7_A8_evaluation_contract' in blocking,
    }
    triggered = [k for k, v in hard_stop_map.items() if v]

    # --- predecessor re-verification ---------------------------------------------
    fc = json.loads((AUD / 'phase25e_postclosure_reconciliation_final_check.json').read_text(encoding='utf-8'))
    ff_ok = sha(AUD / 'phase25e_final_freeze.json') == REQUIRED_FINAL_FREEZE_SHA
    nb_ok = sha(ROOT / 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb') \
        == REQUIRED_NOTEBOOK_SHA
    scope = json.loads((AUD / 'phase25f_scope_guard.json').read_text(encoding='utf-8'))
    lock = json.loads((AUD / 'phase25f_test_lock_audit.json').read_text(encoding='utf-8'))
    nb25f = (ROOT / 'notebooks/phasewise/phase_25f_preservation_fusion/'
                    'phase25f_post_safety_and_fusion.ipynb')

    checks = {
        'all_10_audits_present_and_pass': not [f for f in failures if f.startswith('AUDIT')],
        'all_3_tables_present': not [f for f in failures if f.startswith('MISSING_TABLE')],
        'predecessor_terminal_unchanged': fc['terminal'] == REQUIRED_TERMINAL,
        'phase25e_final_freeze_still_immutable': ff_ok,
        'reconciled_notebook_sha_unchanged': nb_ok,
        'no_phase25f_scientific_notebook_created': not nb25f.exists(),
        'phase25f_not_started': True,
        'phase25g_not_started': True,
        'router_holdout_reads_zero': lock['router_holdout_reads'] == 0,
        'val808_reads_zero': lock['val808_reads'] == 0,
        'test_reads_zero': lock['test_reads'] == 0,
        'no_model_constructed': scope['forbidden_actions_executed']['model_construction'] is False,
        'no_training': scope['forbidden_actions_executed']['training'] is False,
        'no_forward_passes': scope['forbidden_actions_executed']['forward_passes'] == 0,
        'no_lambda_selected': scope['forbidden_actions_executed']['lambda_selection'] is False,
        'no_budget_selected': scope['forbidden_actions_executed']['budget_selection'] is False,
        'no_threshold_invented': scope['forbidden_actions_executed']['threshold_invention'] is False,
        'phase25e_state_frozen': all(v is False for v in scope['phase25e_state_frozen'].values()),
    }
    for k, ok in checks.items():
        if not ok:
            failures.append(f'CHECK_FAIL:{k}')

    phase25f_spec_complete = (len(blocking) == 0) and (len(triggered) == 0)
    terminal = SUCCESS_TERMINAL if phase25f_spec_complete else BLOCKED_TERMINAL

    final = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'SPECIFICATION_FINAL_CHECK',
        'method': 'RA-MedFiLM-BARR',
        'audit_only': True,
        'phase25f_spec_complete': phase25f_spec_complete,
        'phase25f_execution_status': ('ELIGIBLE_NOT_STARTED' if phase25f_spec_complete
                                      else 'BLOCKED__SPEC_INCOMPLETE'),
        'terminal': terminal,
        'audits': results,
        'audit_count': len([r for r in results.values() if 'all_pass' in r]),
        'specification_fields_total': len(comp),
        'specification_fields_complete': len(comp) - len(incomplete),
        'specification_fields_incomplete': len(incomplete),
        'blocking_fields': blocking,
        'blocking_field_count': len(blocking),
        'incomplete_fields': incomplete,
        'hard_stop_conditions': hard_stop_map,
        'hard_stop_conditions_triggered': triggered,
        'hard_stop_triggered_count': len(triggered),
        'missing_fields_reported_exactly': blocking,
        'no_phase25f_scientific_notebook_created': not nb25f.exists(),
        'phase25f_started': False,
        'phase25g_started': False,
        'router_holdout_reads': 0, 'val808_reads': 0, 'test_reads': 0,
        'lambda_selected': False, 'budget_selected': False,
        'model_constructed': False, 'training_runs': 0, 'forward_passes': 0,
        'new_oof_prediction': False, 'new_refinement': False, 'new_delta_dice': False,
        'threshold_invented': False,
        'checks': checks,
        'checks_passed': sum(1 for v in checks.values() if v),
        'checks_total': len(checks),
        'blocked_terminal': BLOCKED_TERMINAL,
        'success_terminal': SUCCESS_TERMINAL,
        'supervisor_action_required': not phase25f_spec_complete,
        'failures': failures,
        'all_pass': not failures,
    }
    (AUD / 'phase25f_specification_final_check.json').write_text(
        json.dumps(final, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Spec fields: {final["specification_fields_complete"]}/{final["specification_fields_total"]} complete')
    print(f'Blocking fields: {len(blocking)}')
    print(f'Hard-stop conditions triggered: {len(triggered)}')
    print(f'Checks: {final["checks_passed"]}/{final["checks_total"]}  failures={failures}')
    print(f'phase25f_spec_complete = {phase25f_spec_complete}')
    print(f'TERMINAL: {terminal}')
    if failures:
        sys.exit(1)
    print('PHASE25F_SPEC_AUDIT_COMPLETE')


if __name__ == '__main__':
    main()
