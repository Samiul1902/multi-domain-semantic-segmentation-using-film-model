"""Phase25E policy-evaluation ENTRY GATE (fail-closed).

Binds exact SHA-256 for every frozen predecessor artifact, re-hashes all 45
prospective membership CSVs against the frozen manifest, verifies the
predecessor terminal and every hard lock. Writes
reports/audits/phase25e_policy_eval_entry_gate.json and FAILS CLOSED on any
mismatch.

Outcome-blind: the Phase25C label CSV and the Phase25D OOF prediction CSV are
read as raw bytes for SHA verification only. No outcome column is parsed.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'
REQUIRED_PREDECESSOR = ('PHASE25E_RESOURCE_GATE_SPEC_V1_0_COMPLETE__COST_BUDGET_LAMBDA_TIE_AND_COMPARATOR'
                        '_RULES_FROZEN__PHASE25E_POLICY_EVALUATION_ELIGIBLE_NOT_STARTED')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def load(name):
    return json.loads((AUD / (name + '.json')).read_text(encoding='utf-8'))


def main():
    spec_gate = load('phase25e_spec_entry_gate')
    governance = load('phase25e_spec_governance')
    final_check = load('phase25e_spec_final_check')
    no_exec = load('phase25e_no_execution_audit')
    p25d_freeze = load('phase25d_final_freeze')

    failures = []

    # --- 1. Predecessor terminal -------------------------------------------------
    predecessor_terminal = spec_gate.get('terminal') or governance.get('terminal') or final_check.get('terminal')
    predecessor_ok = (
        predecessor_terminal == REQUIRED_PREDECESSOR
        and bool(spec_gate.get('all_pass'))
        and bool(governance.get('all_pass'))
        and bool(final_check.get('all_pass'))
    )
    if not predecessor_ok:
        failures.append('PREDECESSOR_TERMINAL_OR_ALL_PASS_MISMATCH')

    # Phase25D must be COMPLETE / FROZEN
    p25d_terminal = p25d_freeze.get('terminal')
    phase25d_complete = (p25d_terminal ==
                         'PHASE25D_BENEFIT_ROUTER_COMPLETE__OOF_DELTA_PREDICTIONS_AND_FINAL_ROUTER_FROZEN'
                         '__PHASE25E_ELIGIBLE_NOT_STARTED')
    if not phase25d_complete:
        failures.append('PHASE25D_NOT_AT_FROZEN_TERMINAL')

    # --- 2. Bind exact SHAs of all frozen predecessors ---------------------------
    canonical = governance['canonical_artifact_sha256']
    bindings = {}
    for rel, expected in canonical.items():
        actual = sha(ROOT / rel)
        bindings[rel] = {'expected_sha256': expected, 'sha256': actual,
                         'match': actual == expected, 'binding_source': 'phase25e_spec_governance'}
        if actual != expected:
            failures.append(f'SHA_MISMATCH:{rel}')

    # Scientific predecessor data products (from the spec entry gate bindings)
    for rel, rec in spec_gate['bindings'].items():
        expected = rec.get('expected_sha256', rec.get('sha256'))
        actual = sha(ROOT / rel)
        bindings[rel] = {'expected_sha256': expected, 'sha256': actual,
                         'match': actual == expected, 'binding_source': 'phase25e_spec_entry_gate'}
        if actual != expected:
            failures.append(f'SHA_MISMATCH:{rel}')

    # Phase25E membership manifest + all 45 membership CSVs re-hashed
    manifest_path = TABLE / 'phase25e_policy_membership_manifest.csv'
    manifest = pd.read_csv(manifest_path, dtype=str)
    if len(manifest) != 45:
        failures.append(f'MEMBERSHIP_POLICY_COUNT:{len(manifest)}')
    membership_rows = []
    for _, row in manifest.iterrows():
        rel = row['membership_path']
        expected = row['membership_sha256']
        actual = sha(ROOT / rel)
        membership_rows.append({'policy_id': row['policy_id'], 'path': rel,
                                'expected_sha256': expected, 'sha256': actual,
                                'match': actual == expected,
                                'selected_count': int(row['selected_count']),
                                'K_b': int(row['K_b'])})
        if actual != expected:
            failures.append(f'MEMBERSHIP_SHA_MISMATCH:{row["policy_id"]}')
    bindings['reports/tables/phase25e_policy_membership_manifest.csv'] = {
        'expected_sha256': canonical.get('reports/tables/phase25e_policy_membership_manifest.csv'),
        'sha256': sha(manifest_path),
        'match': sha(manifest_path) == canonical.get('reports/tables/phase25e_policy_membership_manifest.csv'),
        'binding_source': 'phase25e_spec_governance'}

    # --- 3. Locks ----------------------------------------------------------------
    locks = {
        'router_holdout_reads': 0,
        'router_holdout_feature_inference': 0,
        'VAL808_reads': 0,
        'TEST_reads': 0,
        'Phase25F_started': False,
        'Phase25G_started': False,
        'DeltaDice_outcomes_read': 0,
        'DeltaDice_outcome_joins': 0,
    }
    lock_checks = {
        'router_holdout_reads': int(no_exec.get('router_holdout_reads', -1)) == 0,
        'router_holdout_feature_inference': int(no_exec.get('router_holdout_feature_inference', -1)) == 0,
        'VAL808_reads': int(no_exec.get('VAL808_reads', -1)) == 0,
        'TEST_reads': int(no_exec.get('TEST_reads', -1)) == 0,
        'Phase25F_started': no_exec.get('Phase25F_started') is False,
        'Phase25G_started': no_exec.get('Phase25G_started') is False,
        'DeltaDice_outcomes_read': int(no_exec.get('DeltaDice_outcomes_read', -1)) == 0,
        'DeltaDice_outcome_joins': int(no_exec.get('DeltaDice_outcome_joins', -1)) == 0,
        'policy_outcome_evaluation_started': no_exec.get('policy_outcome_evaluation_started') is False,
    }
    for k, ok in lock_checks.items():
        if not ok:
            failures.append(f'LOCK_VIOLATION:{k}')

    # Control-doc Phase25F/G not-started markers
    rules = (ROOT / 'docs/RULES.md').read_text(encoding='utf-8')
    phase_markers = {f'Phase25{x} = NOT_STARTED': (f'**Phase25{x} = NOT_STARTED**' in rules)
                     for x in ['F', 'G']}
    if not all(phase_markers.values()):
        failures.append('PHASE25F_G_MARKERS_MISSING')

    checks = {
        'predecessor_terminal_exact': predecessor_ok,
        'phase25d_frozen_terminal': phase25d_complete,
        'all_bound_shas_match': all(v['match'] for v in bindings.values()),
        'all_45_membership_shas_match': all(r['match'] for r in membership_rows),
        'membership_policy_count_45': len(manifest) == 45,
        'locks_zero': all(lock_checks.values()),
        'phase25f_g_not_started': all(phase_markers.values()),
        'outcome_blind_entry': True,
    }

    gate = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'ENTRY_GATE',
        'required_predecessor_terminal': REQUIRED_PREDECESSOR,
        'predecessor_terminal_found': predecessor_terminal,
        'bindings': bindings,
        'membership_bindings': membership_rows,
        'locks': locks,
        'lock_checks': lock_checks,
        'phase_markers': phase_markers,
        'checks': checks,
        'failures': failures,
        'all_pass': all(checks.values()) and not failures,
        'outcome_access_semantics': ('Entry gate hashes raw bytes only. Phase25C label CSV and Phase25D OOF CSV '
                                     'are never parsed for outcome columns in this stage.'),
        'router_holdout_reads': 0,
        'VAL808_reads': 0,
        'TEST_reads': 0,
        'Phase25F_started': False,
    }
    (AUD / 'phase25e_policy_eval_entry_gate.json').write_text(
        json.dumps(gate, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Bound {len(bindings)} artifacts; {len(membership_rows)} membership CSVs re-hashed.', flush=True)
    print(f'Failures: {failures}', flush=True)
    if not gate['all_pass']:
        print('PHASE25E_POLICY_EVAL_ENTRY_GATE_FAIL_CLOSED', flush=True)
        sys.exit(1)
    print('PHASE25E_POLICY_EVAL_ENTRY_GATE_PASS', flush=True)


if __name__ == '__main__':
    main()
