"""Phase25F §0-§1: predecessor bindings + FROZEN-SPEC ENTRY GATE (fail-closed).

AUDIT / GOVERNANCE ONLY. No model construction, no training, no forward pass, no
refinement, no DeltaDice recomputation, no lambda/budget/threshold selection, no
ROUTER_HOLDOUT / VAL808 / TEST access.

Binds the exact SHA-256 of every authoritative Phase24/25 artifact relevant to the
post-safety selector, then re-verifies the Phase25E predecessor state.

Writes: reports/audits/phase25f_frozen_spec_entry_gate.json
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
CACHE = ROOT / 'data_cache'

REQUIRED_TERMINAL = ('PHASE25E_CANONICAL_ADJUDICATION_REPAIRED__PRIMARY_PHASE24_STATISTICS_RESTORED__HOLM_'
                     'RETAINED_AS_SENSITIVITY__PHASE25F_ELIGIBLE_NOT_STARTED')
REQUIRED_NOTEBOOK_SHA = 'b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797'
REQUIRED_FINAL_FREEZE_SHA = 'e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e'

BLOCKED = 'PHASE25F_BLOCKED__PREDECESSOR_BINDING_FAILURE'

# Authoritative frozen sources relevant to post-safety (Phase24/25).
AUTHORITATIVE = [
    'reports/audits/phase24_architecture_spec.json',
    'reports/audits/phase24_exact_implementation_spec.json',
    'reports/audits/phase24_preservation_contract.json',
    'reports/audits/phase24_paired_refinement_gain_contract.json',
    'reports/audits/phase24_phase25_module_plan.json',
    'reports/audits/phase24_resource_utility_contract.json',
    'reports/audits/phase24_novelty_boundary.json',
    'reports/audits/phase24_final_freeze.json',
    'reports/audits/phase24_final_check.json',
    'reports/audits/phase24_spec_repair_freeze.json',
    'reports/audits/phase24_spec_completeness_repair.json',
    'reports/audits/phase24_benefit_data_protocol.json',
    'reports/audits/phase24_benefit_data_protocol_exact.json',
    'reports/audits/phase24_architecture_revision_v1_1.json',
    'reports/audits/phase24_v1_2_feature_spec_governance.json',
    'reports/audits/phase24_router_feature_spec_completion_v1_2.json',
    'reports/tables/phase24_ablation_plan.csv',
    'reports/tables/phase24_comparator_plan.csv',
    'reports/tables/phase24_data_role_contract.csv',
    'reports/tables/phase24_module_spec.csv',
    'reports/tables/phase24_success_failure_criteria.csv',
    'reports/tables/phase24_prior_art_differentiation.csv',
    # Phase25 canonical freezes
    'reports/audits/phase25a_canonical_final_freeze.json',
    'reports/audits/phase25b_final_freeze.json',
    'reports/audits/phase25c_final_freeze.json',
    'reports/audits/phase25d_final_freeze.json',
    'reports/audits/phase25c_crossfit_leakage_audit.json',
    'reports/audits/phase25c_fullfield_reconstruction_audit.json',
    'reports/audits/phase25c_refiner_inference_execution_binding.json',
    'reports/audits/phase25c_global_cache_binding.json',
    'reports/audits/phase25c_phase25d_handoff_schema.json',
    'reports/audits/phase25c_scope_guard.json',
    'reports/audits/phase25c_test_lock_audit.json',
    'reports/audits/phase25d_phase25e_handoff_schema.json',
    'reports/audits/phase25e_phase25f_handoff_schema.json',
    'reports/audits/phase25e_comparator_direction_contract_v1_0.json',
    # Phase25C persisted label artifacts
    'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv',
    'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/label_manifest.json',
    'reports/tables/phase25c_oof_paired_gain_labels.csv',
    # Phase25B GT-free pre-refinement features (contrast: PRE-refinement)
    'data_cache/phase25b_barr_pre_refinement_features_v1_2/cache_manifest.json',
    'data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_group_offsets.json',
    'data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_schema.csv',
]

# Optional / may be absent -> recorded, not fatal
OPTIONAL = [
    'reports/audits/phase25e_phase25f_handoff_schema.json',
]

PREDECESSOR_RECON = [
    'reports/audits/phase25e_postclosure_reconciliation_final_check.json',
    'reports/audits/phase25e_final_freeze_reconciliation_addendum.json',
    'reports/audits/phase25e_adjudication_reconciled.json',
    'reports/audits/phase25e_multiplicity_provenance_audit.json',
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def main():
    failures = []
    bindings = {}

    def bind(rel):
        p = ROOT / rel
        if not p.exists():
            failures.append(f'MISSING_AUTHORITATIVE:{rel}')
            bindings[rel] = {'exists': False}
            return
        bindings[rel] = {'exists': True, 'sha256': sha(p), 'bytes': p.stat().st_size}

    for rel in AUTHORITATIVE:
        bind(rel)
    for rel in OPTIONAL:
        p = ROOT / rel
        bindings[rel] = ({'exists': True, 'sha256': sha(p), 'optional': True} if p.exists()
                         else {'exists': False, 'optional': True})

    # --- predecessor state --------------------------------------------------------
    fc = json.loads((AUD / 'phase25e_postclosure_reconciliation_final_check.json').read_text(encoding='utf-8'))
    ad = json.loads((AUD / 'phase25e_final_freeze_reconciliation_addendum.json').read_text(encoding='utf-8'))
    ff_path = AUD / 'phase25e_final_freeze.json'
    nb_path = ROOT / 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb'

    checks = {
        'terminal_matches': fc.get('terminal') == REQUIRED_TERMINAL,
        'final_check_all_pass': bool(fc.get('all_pass')),
        'final_check_checks_16_of_16': fc.get('checks_passed') == fc.get('checks_total') == 16,
        'addendum_terminal_matches': ad.get('reconciliation_terminal') == REQUIRED_TERMINAL,
        'phase25e_final_freeze_immutable': sha(ff_path) == REQUIRED_FINAL_FREEZE_SHA,
        'reconciled_notebook_sha_matches': sha(nb_path) == REQUIRED_NOTEBOOK_SHA,
        'phase25f_status_eligible_not_started': ad.get('phase25f_status') == 'ELIGIBLE_NOT_STARTED',
        'phase25f_not_started': ad.get('phase25f_started') is False,
        'phase25g_not_started': ad.get('phase25g_started') is False,
        'router_holdout_reads_zero': int(fc.get('router_holdout_reads', -1)) == 0,
        'val808_reads_zero': int(fc.get('VAL808_reads', -1)) == 0,
        'test_reads_zero': int(fc.get('TEST_reads', -1)) == 0,
        'lambda_not_selected': fc.get('lambda_selected') is False,
        'all_reconciliation_artifacts_present': all((ROOT / r).exists() for r in PREDECESSOR_RECON),
        'all_authoritative_sources_present': all(b.get('exists') for b in bindings.values()
                                                 if not b.get('optional')),
    }
    for k, ok in checks.items():
        if not ok:
            failures.append(f'CHECK_FAIL:{k}')

    gate = {
        'classification': 'PHASE25F_POST_SAFETY_SPEC_COMPLETENESS_AUDIT',
        'stage': 'FROZEN_SPEC_ENTRY_GATE',
        'method': 'RA-MedFiLM-BARR',
        'audit_only': True,
        'required_predecessor_terminal': REQUIRED_TERMINAL,
        'predecessor_terminal_found': fc.get('terminal'),
        'authoritative_sources': bindings,
        'authoritative_source_count': len([b for b in bindings.values() if b.get('exists')]),
        'predecessor_reconciliation_artifacts': {
            r: sha(ROOT / r) for r in PREDECESSOR_RECON if (ROOT / r).exists()},
        'checks': checks,
        'locks': {
            'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
            'lambda_selected': False, 'budget_selected': False,
            'phase25f_started': False, 'phase25g_started': False,
            'model_constructed': False, 'training_runs': 0, 'forward_passes': 0,
        },
        'blocked_terminal': BLOCKED,
        'failures': failures,
        'all_pass': all(checks.values()) and not failures,
    }
    (AUD / 'phase25f_frozen_spec_entry_gate.json').write_text(
        json.dumps(gate, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Authoritative sources bound: {gate["authoritative_source_count"]}')
    print(f'Failures: {failures}')
    if not gate['all_pass']:
        print(BLOCKED)
        sys.exit(1)
    print('PHASE25F_FROZEN_SPEC_ENTRY_GATE_PASS')


if __name__ == '__main__':
    main()
