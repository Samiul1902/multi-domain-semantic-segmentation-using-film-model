"""Phase25E PRE-OUTCOME FREEZE.

Binds the SHAs of every frozen evaluation input (statistics contract, criteria
binding, final-router DEV calibration + thresholds, bootstrap plan, membership
immutability audit, entry gate, and all 45 membership CSVs) and asserts that
NO outcome column has been accessed yet. Must complete BEFORE the outcome join.

Writes reports/audits/phase25e_pre_outcome_freeze.json.
"""
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
CACHE = ROOT / 'data_cache/phase25e_barr_resource_gate_v1_0'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    frozen_inputs = [
        'reports/audits/phase25e_policy_eval_entry_gate.json',
        'reports/audits/phase25e_membership_immutability_audit.json',
        'reports/audits/phase25e_evaluation_statistics_contract_v1_0.json',
        'reports/audits/phase25e_success_failure_criteria_binding.json',
        'reports/audits/phase25e_final_router_dev_calibration.json',
        'reports/tables/phase25e_final_router_dev_thresholds.csv',
        'reports/tables/phase25e_policy_membership_manifest.csv',
        'reports/tables/phase24_success_failure_criteria.csv',
        'reports/audits/phase24_router_split_manifest.csv',
        'data_cache/phase25e_barr_resource_gate_v1_0/phase25e_bootstrap_plan_v1_0.npz',
        'data_cache/phase25e_barr_resource_gate_v1_0/phase25e_final_router_dev_scores.csv',
    ]
    bindings = {p: sha(ROOT / p) for p in frozen_inputs}

    manifest = pd.read_csv(TABLE / 'phase25e_policy_membership_manifest.csv', dtype=str)
    membership_shas = {r['policy_id']: sha(ROOT / r['membership_path']) for _, r in manifest.iterrows()}

    stats = json.loads((AUD / 'phase25e_evaluation_statistics_contract_v1_0.json').read_text(encoding='utf-8'))
    calib = json.loads((AUD / 'phase25e_final_router_dev_calibration.json').read_text(encoding='utf-8'))
    imm = json.loads((AUD / 'phase25e_membership_immutability_audit.json').read_text(encoding='utf-8'))
    gate = json.loads((AUD / 'phase25e_policy_eval_entry_gate.json').read_text(encoding='utf-8'))

    checks = {
        'entry_gate_pass': bool(gate['all_pass']),
        'membership_immutability_pass': bool(imm['all_pass']),
        'statistics_contract_frozen': stats['frozen_before_outcome_access'] is True,
        'bootstrap_plan_persisted': (CACHE / 'phase25e_bootstrap_plan_v1_0.npz').exists(),
        'final_router_calibration_pass': bool(calib['all_pass']),
        'outcome_access_zero': (stats['DeltaDice_outcomes_read'] == 0
                                and calib['DeltaDice_outcomes_read'] == 0),
        'membership_count_45': len(membership_shas) == 45,
    }

    audit = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'PRE_OUTCOME_FREEZE',
        'frozen_inputs': bindings,
        'membership_sha256': membership_shas,
        'bootstrap_plan_sha256': stats['bootstrap_plan_sha256'],
        'criteria_source_sha256': json.loads(
            (AUD / 'phase25e_success_failure_criteria_binding.json').read_text(encoding='utf-8')
        )['criteria_source_sha256'],
        'checks': checks,
        'outcome_access_before_freeze': 0,
        'outcome_join_permitted_after_this_artifact': True,
        'router_holdout_reads': 0,
        'VAL808_reads': 0,
        'TEST_reads': 0,
        'Phase25F_started': False,
        'all_pass': all(checks.values()),
    }
    (AUD / 'phase25e_pre_outcome_freeze.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'Frozen inputs bound: {len(bindings)}; membership SHAs: {len(membership_shas)}', flush=True)
    print(f'Checks: {checks}', flush=True)
    if not audit['all_pass']:
        sys.exit(1)
    print('PHASE25E_PRE_OUTCOME_FREEZE_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
