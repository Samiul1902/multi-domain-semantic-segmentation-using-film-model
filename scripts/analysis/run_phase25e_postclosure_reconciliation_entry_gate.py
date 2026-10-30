"""Phase25E POST-CLOSURE STATISTICAL-ADJUDICATION + GOVERNANCE RECONCILIATION
ENTRY GATE (fail-closed).

This gate opens the reconciliation work order on top of the FROZEN Phase25E
closure. It is read-only with respect to science: it binds the exact SHA-256 of
every frozen Phase25E scientific artifact (audits, tables, plan, memberships,
figures, notebooks, cache) as the RECONCILIATION BASELINE, and re-verifies that
the closure itself is at its canonical frozen terminal.

If any bound artifact has drifted from the frozen record -> FAIL CLOSED with
terminal PHASE25E_RECONCILIATION_BLOCKED__SCIENTIFIC_ARTIFACT_DRIFT.

No training, no inference, no bootstrap, no membership regeneration, no outcome
recomputation, no new lambda/budget/threshold. ROUTER_HOLDOUT / VAL808 / TEST
remain unopened.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
FIG = ROOT / 'reports/figures'
NB = ROOT / 'notebooks/phasewise/phase_25e_resource_gate'
CACHE = ROOT / 'data_cache/phase25e_barr_resource_gate_v1_0'

REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'
STAGE = 'POSTCLOSURE_RECONCILIATION_ENTRY_GATE'

# Frozen closure identity (recorded in phase25e_final_freeze.json).
FINAL_FREEZE_REL = 'reports/audits/phase25e_final_freeze.json'
FINAL_FREEZE_SHA = 'e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e'
CLOSURE_TERMINAL = ('PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL'
                    '_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED')
NOTEBOOK_REL = 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb'
NOTEBOOK_SHA = 'e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718'
SPEC_NOTEBOOK_REL = 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate_specification.ipynb'
SPEC_NOTEBOOK_SHA = 'a431b3604021c0f4ffaaa6153302d674a38167b1792ab55d09a58a8ad2a5c41c'
PLAN_REL = 'data_cache/phase25e_barr_resource_gate_v1_0/phase25e_bootstrap_plan_v1_0.npz'
PLAN_SHA = '241ed5232b35709494adbf230151cec21259f86f88e1f06e5b2881a6d88f9b63'
DEV_SCORES_REL = 'data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv'
DEV_SCORES_SHA = '2d23e11090a5b3164d5b125c633bbccfbe307ecdc717d0f5689bf401bd849f9d'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def rel(p):
    return Path(p).resolve().relative_to(ROOT).as_posix()


def main():
    failures = []
    bindings = {}

    def bind(relpath, expected=None, source='baseline'):
        p = ROOT / relpath
        if not p.exists():
            failures.append(f'MISSING:{relpath}')
            return
        actual = sha(p)
        rec = {'sha256': actual, 'binding_source': source}
        if expected is not None:
            rec['expected_sha256'] = expected
            rec['match'] = (actual == expected)
            if actual != expected:
                failures.append(f'SHA_MISMATCH:{relpath}')
        bindings[relpath] = rec

    # --- 1. Closure identity -----------------------------------------------------
    bind(FINAL_FREEZE_REL, FINAL_FREEZE_SHA, 'frozen_closure')
    freeze = json.loads((AUD / 'phase25e_final_freeze.json').read_text(encoding='utf-8'))
    closure_terminal_ok = freeze.get('terminal') == CLOSURE_TERMINAL
    if not closure_terminal_ok:
        failures.append('CLOSURE_TERMINAL_MISMATCH')
    closure_all_pass = bool(freeze.get('all_pass'))
    if not closure_all_pass:
        failures.append('CLOSURE_NOT_ALL_PASS')
    closure_no_drift = (freeze.get('predecessor_drift') == []
                        and freeze.get('scientific_predecessors_unchanged') is True)
    if not closure_no_drift:
        failures.append('CLOSURE_PREDECESSOR_DRIFT_RECORDED')

    # --- 2. Re-verify every audit SHA recorded in the frozen closure --------------
    audit_bindings = {}
    for name, rec in freeze['audits'].items():
        p = AUD / (name + '.json')
        if not p.exists():
            failures.append(f'MISSING_AUDIT:{name}')
            continue
        actual = sha(p)
        ok = (actual == rec['sha256'])
        audit_bindings[name] = {'frozen_sha256': rec['sha256'], 'sha256': actual, 'match': ok}
        if not ok:
            failures.append(f'CLOSURE_AUDIT_DRIFT:{name}')

    # --- 3. Notebooks ------------------------------------------------------------
    bind(NOTEBOOK_REL, NOTEBOOK_SHA, 'frozen_closure')
    bind(SPEC_NOTEBOOK_REL, SPEC_NOTEBOOK_SHA, 'frozen_closure')

    # --- 4. Cache (plan + dev scores) --------------------------------------------
    bind(PLAN_REL, PLAN_SHA, 'frozen_closure')
    bind(DEV_SCORES_REL, DEV_SCORES_SHA, 'frozen_closure')

    # --- 5. All Phase25E tables (baseline) ---------------------------------------
    table_files = sorted(p for p in TABLE.glob('phase25e_*.csv'))
    for p in table_files:
        bind(rel(p), None, 'reconciliation_baseline')
    # 45 membership CSVs
    manifest = pd.read_csv(TABLE / 'phase25e_policy_membership_manifest.csv', dtype=str)
    membership_bindings = []
    for _, row in manifest.iterrows():
        relp = row['membership_path']
        expected = row['membership_sha256']
        p = ROOT / relp
        actual = sha(p) if p.exists() else None
        ok = (actual == expected)
        membership_bindings.append({'policy_id': row['policy_id'], 'path': relp,
                                    'expected_sha256': expected, 'sha256': actual, 'match': ok})
        if not ok:
            failures.append(f'MEMBERSHIP_SHA_MISMATCH:{row["policy_id"]}')
    if len(manifest) != 45:
        failures.append(f'MEMBERSHIP_POLICY_COUNT:{len(manifest)}')

    # --- 6. All 10 figures (baseline) --------------------------------------------
    fig_files = sorted(FIG.glob('p25e_*.png'))
    if len(fig_files) != 10:
        failures.append(f'FIGURE_COUNT:{len(fig_files)}')
    for p in fig_files:
        bind(rel(p), None, 'reconciliation_baseline')

    # --- 7. Locks (hard scope) ---------------------------------------------------
    locks = {
        'router_holdout_reads': freeze.get('router_holdout_reads'),
        'VAL808_reads': freeze.get('VAL808_reads'),
        'TEST_reads': freeze.get('TEST_reads'),
        'lambda_selected': freeze.get('lambda_selected'),
        'phase25f_status': freeze.get('phase25f_status'),
        'phase25g_status': freeze.get('phase25g_status'),
    }
    lock_checks = {
        'router_holdout_reads_zero': int(locks['router_holdout_reads'] or 0) == 0,
        'VAL808_reads_zero': int(locks['VAL808_reads'] or 0) == 0,
        'TEST_reads_zero': int(locks['TEST_reads'] or 0) == 0,
        'lambda_not_selected': locks['lambda_selected'] is False,
        'phase25f_not_started': locks['phase25f_status'] == 'NOT_STARTED',
        'phase25g_not_started': locks['phase25g_status'] == 'NOT_STARTED',
        'test_lock_until_phase39': freeze.get('test_lock') == 'LOCKED UNTIL PHASE39',
    }
    for k, ok in lock_checks.items():
        if not ok:
            failures.append(f'LOCK_VIOLATION:{k}')

    checks = {
        'closure_sha_exact': bindings[FINAL_FREEZE_REL].get('match', False),
        'closure_terminal_exact': closure_terminal_ok,
        'closure_all_pass': closure_all_pass,
        'closure_no_recorded_drift': closure_no_drift,
        'all_closure_audit_shas_match': all(v['match'] for v in audit_bindings.values()),
        'notebook_shas_exact': (bindings[NOTEBOOK_REL].get('match', False)
                                and bindings[SPEC_NOTEBOOK_REL].get('match', False)),
        'cache_shas_exact': (bindings[PLAN_REL].get('match', False)
                             and bindings[DEV_SCORES_REL].get('match', False)),
        'all_45_membership_shas_match': all(r['match'] for r in membership_bindings),
        'ten_figures_present': len(fig_files) == 10,
        'all_phase25e_tables_bound': len(table_files) >= 14,
        'locks_zero_and_not_started': all(lock_checks.values()),
    }

    gate = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': STAGE,
        'purpose': ('Open the post-closure statistical-adjudication + governance reconciliation work order '
                    'on the FROZEN Phase25E closure; bind the reconciliation baseline; verify no science drift.'),
        'frozen_closure_terminal': CLOSURE_TERMINAL,
        'frozen_closure_sha256': FINAL_FREEZE_SHA,
        'baseline_bindings': bindings,
        'baseline_binding_count': len(bindings),
        'closure_audit_bindings': audit_bindings,
        'membership_bindings': membership_bindings,
        'locks': locks,
        'lock_checks': lock_checks,
        'checks': checks,
        'read_only_declaration': {
            'training': False, 'new_model_inference': False, 'new_bootstrap': False,
            'membership_regeneration': False, 'outcome_recomputation': False,
            'new_lambda_or_budget_or_threshold': False,
        },
        'failures': failures,
        'all_pass': all(checks.values()) and not failures,
        'blocked_terminal': 'PHASE25E_RECONCILIATION_BLOCKED__SCIENTIFIC_ARTIFACT_DRIFT',
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'phase25f_started': False,
    }
    (AUD / 'phase25e_postclosure_reconciliation_entry_gate.json').write_text(
        json.dumps(gate, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Baseline bindings: {len(bindings)} artifacts; {len(membership_bindings)} memberships; '
          f'{len(fig_files)} figures; {len(audit_bindings)} closure audits.', flush=True)
    print(f'Failures: {failures}', flush=True)
    if not gate['all_pass']:
        print('PHASE25E_RECONCILIATION_BLOCKED__SCIENTIFIC_ARTIFACT_DRIFT', flush=True)
        sys.exit(1)
    print('PHASE25E_POSTCLOSURE_RECONCILIATION_ENTRY_GATE_PASS', flush=True)


if __name__ == '__main__':
    main()
