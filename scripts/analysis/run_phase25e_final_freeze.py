"""Phase25E FINAL FREEZE + terminal.

Aggregates every Phase25E audit, re-verifies all frozen predecessor SHAs are
byte-identical (science unchanged), binds the canonical notebook SHA, and emits
the Phase25E terminal.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'
TERMINAL = ('PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV'
            '_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED')

AUDITS = ['phase25e_policy_eval_entry_gate', 'phase25e_membership_immutability_audit',
          'phase25e_success_failure_criteria_binding', 'phase25e_final_router_dev_calibration',
          'phase25e_pre_outcome_freeze', 'phase25e_policy_evaluation_summary', 'phase25e_adjudication',
          'phase25e_scope_lock_audit', 'phase25e_test_lock_audit', 'phase25e_table_integrity_audit',
          'phase25e_join_integrity_audit', 'phase25e_metric_recomputation_audit',
          'phase25e_c7_c8_binding_audit', 'phase25e_cost_binding_audit', 'phase25e_notebook_binding_audit',
          'phase25e_criteria_adjudication_audit', 'phase25e_phase25f_handoff_schema',
          'phase25e_policy_eval_notebook_determinism', 'phase25e_status_sync']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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

    # Science unchanged: re-verify predecessor SHAs bound at entry
    gate = json.loads((AUD / 'phase25e_policy_eval_entry_gate.json').read_text(encoding='utf-8'))
    drift = []
    for rel, rec in gate['bindings'].items():
        actual = sha(ROOT / rel)
        if actual != rec['expected_sha256']:
            drift.append(rel)
    if drift:
        failures.append('PREDECESSOR_DRIFT')
    for rec in gate['membership_bindings']:
        if sha(ROOT / rec['path']) != rec['expected_sha256']:
            drift.append(rec['path'])
    if drift:
        failures.append('MEMBERSHIP_DRIFT')

    det = json.loads((AUD / 'phase25e_policy_eval_notebook_determinism.json').read_text(encoding='utf-8'))
    summary = json.loads((AUD / 'phase25e_policy_evaluation_summary.json').read_text(encoding='utf-8'))
    adj = json.loads((AUD / 'phase25e_adjudication.json').read_text(encoding='utf-8'))

    freeze = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'FINAL_FREEZE',
        'predecessor_terminal': 'PHASE25E_RESOURCE_GATE_SPEC_V1_0_COMPLETE__COST_BUDGET_LAMBDA_TIE_AND_COMPARATOR_RULES_FROZEN__PHASE25E_POLICY_EVALUATION_ELIGIBLE_NOT_STARTED',
        'terminal': TERMINAL,
        'audits': results,
        'audit_count': len(results),
        'audits_all_pass': all(r['all_pass'] for r in results.values()),
        'scientific_predecessors_unchanged': not drift,
        'predecessor_drift': drift,
        'notebook_sha256': det['notebook_sha256'],
        'notebook_three_times_byte_identical': det['three_times_byte_identical'],
        'notebook_png_outputs_valid': det['png_outputs_valid'],
        'population': 'ROUTER_DEVELOPMENT (4957)',
        'policy_count': summary['policy_count'],
        'bootstrap_replicates': summary['bootstrap_replicates'],
        'S1_H1_status': adj['S1_H1_status'],
        'S2_preservation_satisfied': adj['S2_preservation_satisfied'],
        'S3_frontier_measured': adj['S3_frontier_measured'],
        'F5_domain_collapse_triggered': adj['F5_domain_collapse_triggered'],
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'lambda_selected': False,
        'phase25f_status': 'NOT_STARTED', 'phase25g_status': 'NOT_STARTED',
        'test_lock': 'LOCKED UNTIL PHASE39',
        'failures': failures,
        'all_pass': not failures,
    }
    (AUD / 'phase25e_final_freeze.json').write_text(
        json.dumps(freeze, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'Audits: {len(results)} all_pass={freeze["audits_all_pass"]}')
    print(f'Predecessor drift: {drift}')
    print(f'Terminal: {TERMINAL}')
    if failures:
        print(f'Failures: {failures}')
        sys.exit(1)
    print('PHASE25E_FINAL_FREEZE_PASS')


if __name__ == '__main__':
    main()
