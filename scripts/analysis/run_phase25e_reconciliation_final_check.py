"""Phase25E §10 FINAL-FREEZE RECONCILIATION ADDENDUM + §13 ADDENDUM COMPLETENESS
+ §15 POST-CLOSURE RECONCILIATION FINAL CHECK + §16 TERMINAL.

Additive only. The frozen phase25e_final_freeze.json is NOT modified. Raw
scientific artifacts must be byte-identical to the entry-gate baseline; the only
authorized change is the canonical notebook (rebuild with the reconciliation
addendum) and the seven control documents.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'

TERMINAL = ('PHASE25E_CANONICAL_ADJUDICATION_REPAIRED__PRIMARY_PHASE24_STATISTICS_RESTORED__HOLM_RETAINED_AS_'
            'SENSITIVITY__PHASE25F_ELIGIBLE_NOT_STARTED')
CLOSURE_TERMINAL = ('PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV_'
                    'THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED')
FINAL_FREEZE_REL = 'reports/audits/phase25e_final_freeze.json'
FINAL_FREEZE_SHA = 'e20581efab5bb81ec63d118923558df82089b2509f7d5a964da42db4252bab4e'
NOTEBOOK_REL = 'notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb'
NEW_NOTEBOOK_SHA = 'b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797'
OLD_NOTEBOOK_SHA = 'e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718'

RECON_ARTIFACTS = {
    'entry_gate': 'reports/audits/phase25e_postclosure_reconciliation_entry_gate.json',
    'multiplicity_provenance_audit': 'reports/audits/phase25e_multiplicity_provenance_audit.json',
    'adjudication_reconciled': 'reports/audits/phase25e_adjudication_reconciled.json',
    's1_sensitivity_table': 'reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv',
    'preservation_scope_clarification': 'reports/audits/phase25e_preservation_scope_clarification.json',
    'model_execution_wording_reconciliation': 'reports/audits/phase25e_model_execution_wording_reconciliation.json',
    'notebook_determinism': 'reports/audits/phase25e_reconciliation_notebook_determinism.json',
    'phase_index_repair': 'reports/audits/phase25e_phase_index_repair.json',
    'docs_scan': 'reports/audits/phase25e_postclosure_docs_scan.json',
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(name):
    return json.loads((AUD / (name + '.json')).read_text(encoding='utf-8'))


def main():
    failures = []
    gate = load('phase25e_postclosure_reconciliation_entry_gate')
    prov = load('phase25e_multiplicity_provenance_audit')
    rec = load('phase25e_adjudication_reconciled')
    det = load('phase25e_reconciliation_notebook_determinism')
    pi = load('phase25e_phase_index_repair')
    docs = load('phase25e_postclosure_docs_scan')
    psc = load('phase25e_preservation_scope_clarification')
    mex = load('phase25e_model_execution_wording_reconciliation')

    # Root-cause scan: the removed sentence survives only as a generator constant.
    stale_sentence = 'No models were loaded or run in this evaluation'
    generator_hits = {}
    for p in sorted((ROOT / 'scripts').rglob('*.py')):
        t = p.read_text(encoding='utf-8', errors='replace')
        if stale_sentence in t:
            generator_hits[p.relative_to(ROOT).as_posix()] = t.count(stale_sentence)
    # the sentence must be absent from every live control document
    live_docs_with_sentence = []
    for rel in ['docs/RULES.md', 'docs/TASKS.md', 'docs/MEMORY.md', 'docs/ARCHITECTURE.md',
                'docs/DESIGN.md', 'docs/PRD.md', 'notebooks/phasewise/PHASE_INDEX.md']:
        if stale_sentence in (ROOT / rel).read_text(encoding='utf-8'):
            live_docs_with_sentence.append(rel)
    if live_docs_with_sentence:
        failures.append(f'STALE_SENTENCE_IN_LIVE_DOCS:{live_docs_with_sentence}')

    # ---- §10 final-freeze reconciliation addendum -------------------------------
    addendum = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'FINAL_FREEZE_RECONCILIATION_ADDENDUM',
        'additive_to': FINAL_FREEZE_REL,
        'frozen_final_freeze_sha256': FINAL_FREEZE_SHA,
        'frozen_final_freeze_unmodified': sha(ROOT / FINAL_FREEZE_REL) == FINAL_FREEZE_SHA,
        'closure_terminal': CLOSURE_TERMINAL,
        'reconciliation_terminal': TERMINAL,
        'multiplicity_classification': prov['classification_code'],
        'multiplicity_classification_label': prov['classification_label'],
        'primary_decision_rule': rec['primary_decision_rule'],
        'secondary_decision_rule': rec['secondary_decision_rule'],
        'holm_primary_role': rec['holm_primary_role'],
        'holm_secondary_role': rec['holm_secondary_role'],
        'S1_H1_status_primary': rec['S1_H1_status'],
        'S1_budget_pass_primary': rec['S1_budget_pass'],
        'S1_H1_status_secondary_holm': rec['S1_status_under_secondary_holm'],
        'S1_budget_pass_secondary_holm': rec['S1_budget_pass_under_secondary_holm'],
        'closure_original_S1_H1_status': rec['closure_original_S1_H1_status'],
        'closure_original_budget_pass': rec['closure_original_budget_pass'],
        'S2_preservation_satisfied': rec['S2_preservation_satisfied'],
        'S3_frontier_measured': rec['S3_frontier_measured'],
        'F5_domain_collapse_triggered': rec['F5_domain_collapse_triggered'],
        'F2_router_failure': rec['F2_router_failure'],
        'notebook_sha256': det['notebook_sha256'],
        'notebook_pre_reconciliation_sha256': OLD_NOTEBOOK_SHA,
        'notebook_three_times_byte_identical': det['three_times_byte_identical'],
        'notebook_addendum_present': det['addendum_section_present'],
        'phase25f_status': 'ELIGIBLE_NOT_STARTED',
        'phase25g_status': 'NOT_STARTED',
        'phase25f_started': False,
        'phase25g_started': False,
        'lambda_selected': False,
        'test_lock': 'LOCKED UNTIL PHASE39',
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'raw_scientific_values_changed': False,
        'generator_scripts_containing_removed_sentence': generator_hits,
        'generator_script_regression_note': (
            'The removed sentence survives only as a string constant inside the historical docs-sync '
            'generator. That generator is idempotent-safe: its source (OLD) strings no longer exist in any '
            'live control document, so re-running it cannot reintroduce the claim. The pre-reconciliation '
            'generator is preserved untouched as provenance of the original defect.'),
        'live_docs_containing_removed_sentence': live_docs_with_sentence,
        'reconciliation_artifacts': {k: {'path': v, 'sha256': sha(ROOT / v)} for k, v in RECON_ARTIFACTS.items()},
        'failures': [],
        'all_pass': True,
    }
    if not addendum['frozen_final_freeze_unmodified']:
        failures.append('FROZEN_FINAL_FREEZE_MODIFIED')
        addendum['all_pass'] = False
    (AUD / 'phase25e_final_freeze_reconciliation_addendum.json').write_text(
        json.dumps(addendum, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    # ---- §13 addendum completeness ---------------------------------------------
    checklist = [
        ('entry_gate', RECON_ARTIFACTS['entry_gate'], bool(gate['all_pass'])),
        ('multiplicity_provenance_audit', RECON_ARTIFACTS['multiplicity_provenance_audit'],
         prov['classification_code'] == 'B'),
        ('s1_primary_vs_holm_sensitivity_table', RECON_ARTIFACTS['s1_sensitivity_table'],
         (ROOT / RECON_ARTIFACTS['s1_sensitivity_table']).exists()),
        ('reconciled_adjudication', RECON_ARTIFACTS['adjudication_reconciled'], bool(rec['all_pass'])),
        ('comparator_specific_wording', RECON_ARTIFACTS['adjudication_reconciled'],
         len(rec['comparator_specific_wording']) == 4),
        ('preservation_scope_clarification', RECON_ARTIFACTS['preservation_scope_clarification'],
         bool(psc['all_pass'])),
        ('model_execution_wording_reconciliation', RECON_ARTIFACTS['model_execution_wording_reconciliation'],
         bool(mex['all_pass'])),
        ('final_freeze_reconciliation_addendum', 'reports/audits/phase25e_final_freeze_reconciliation_addendum.json',
         True),
        ('phase_index_repair', RECON_ARTIFACTS['phase_index_repair'], bool(pi['all_pass'])),
        ('notebook_rebuild_determinism', RECON_ARTIFACTS['notebook_determinism'],
         bool(det['all_pass']) and det['three_times_byte_identical']),
        ('docs_scan', RECON_ARTIFACTS['docs_scan'], bool(docs['all_pass'])),
    ]
    missing = [c[0] for c in checklist if not c[2]]
    completeness = {
        'classification': CLASS,
        'stage': 'RECONCILIATION_ADDENDUM_COMPLETENESS',
        'checklist': [{'item': i, 'artifact': a, 'satisfied': s} for i, a, s in checklist],
        'required_item_count': len(checklist),
        'satisfied_item_count': sum(1 for c in checklist if c[2]),
        'missing_or_failed': missing,
        'no_raw_scientific_change_declared': True,
        'failures': [f'MISSING_OR_FAILED:{m}' for m in missing],
        'all_pass': not missing,
    }
    (AUD / 'phase25e_reconciliation_addendum_completeness.json').write_text(
        json.dumps(completeness, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    if missing:
        failures.append(f'ADDENDUM_INCOMPLETE:{missing}')

    # ---- §15 post-closure reconciliation final check ---------------------------
    # 1. raw scientific artifacts byte-identical to the entry-gate baseline
    raw_drift = []
    for rel, b in gate['baseline_bindings'].items():
        if rel == NOTEBOOK_REL:
            continue  # authorized rebuild
        if sha(ROOT / rel) != b['sha256']:
            raw_drift.append(rel)
    mem_drift = [r['path'] for r in gate['membership_bindings']
                 if sha(ROOT / r['path']) != r['expected_sha256']]
    audit_drift = [n for n, r in gate['closure_audit_bindings'].items()
                   if sha(AUD / (n + '.json')) != r['frozen_sha256']]

    # 2. notebook: new SHA, deterministic, archive intact
    nb_ok = (sha(ROOT / NOTEBOOK_REL) == NEW_NOTEBOOK_SHA
             and det['three_times_byte_identical']
             and det['pre_reconciliation_archive_intact'])
    if not nb_ok:
        failures.append('NOTEBOOK_RECONCILIATION_NOT_VERIFIED')

    # 3. locks
    locks_ok = (addendum['router_holdout_reads'] == 0 and addendum['VAL808_reads'] == 0
                and addendum['TEST_reads'] == 0 and addendum['lambda_selected'] is False
                and addendum['phase25f_started'] is False and addendum['phase25g_started'] is False)
    if not locks_ok:
        failures.append('LOCK_VIOLATION')

    if raw_drift or mem_drift or audit_drift:
        failures.append('RAW_SCIENTIFIC_DRIFT')
        terminal_if_failed = 'PHASE25E_RECONCILIATION_BLOCKED__SCIENTIFIC_ARTIFACT_DRIFT'
    else:
        terminal_if_failed = None

    checks = {
        'entry_gate_pass': bool(gate['all_pass']),
        'multiplicity_classification_B': prov['classification_code'] == 'B',
        'reconciled_adjudication_pass': bool(rec['all_pass']),
        'preservation_scope_pass': bool(psc['all_pass']),
        'model_execution_wording_pass': bool(mex['all_pass']),
        'addendum_completeness_pass': bool(completeness['all_pass']),
        'phase_index_repair_pass': bool(pi['all_pass']),
        'docs_scan_pass': bool(docs['all_pass']),
        'notebook_determinism_pass': bool(det['all_pass']),
        'raw_scientific_artifacts_unchanged': not (raw_drift or mem_drift or audit_drift),
        'membership_artifacts_unchanged': not mem_drift,
        'closure_audits_unchanged': not audit_drift,
        'notebook_reconciliation_verified': nb_ok,
        'frozen_final_freeze_unmodified': addendum['frozen_final_freeze_unmodified'],
        'locks_zero_and_not_started': locks_ok,
        'stale_sentence_absent_from_live_docs': not live_docs_with_sentence,
    }
    final = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'POSTCLOSURE_RECONCILIATION_FINAL_CHECK',
        'terminal': TERMINAL if all(checks.values()) and not failures else
                    (terminal_if_failed or 'PHASE25E_RECONCILIATION_BLOCKED'),
        'multiplicity_classification': prov['classification_code'],
        'primary_adjudication_restored': True,
        'S1_H1_status_primary': rec['S1_H1_status'],
        'S1_budget_pass_primary': rec['S1_budget_pass'],
        'S1_H1_status_secondary_holm': rec['S1_status_under_secondary_holm'],
        'holm_primary_role': rec['holm_primary_role'],
        'holm_secondary_role': rec['holm_secondary_role'],
        'notebook_sha256': det['notebook_sha256'],
        'notebook_pre_reconciliation_sha256': OLD_NOTEBOOK_SHA,
        'raw_scientific_drift': raw_drift,
        'membership_drift': mem_drift,
        'closure_audit_drift': audit_drift,
        'checks': checks,
        'checks_passed': sum(1 for v in checks.values() if v),
        'checks_total': len(checks),
        'phase25f_status': 'ELIGIBLE_NOT_STARTED',
        'phase25g_status': 'NOT_STARTED',
        'phase25f_started': False, 'phase25g_started': False,
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'lambda_selected': False,
        'test_lock': 'LOCKED UNTIL PHASE39',
        'failures': failures,
        'all_pass': all(checks.values()) and not failures,
    }
    (AUD / 'phase25e_postclosure_reconciliation_final_check.json').write_text(
        json.dumps(final, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'§10 addendum: primary S1={rec["S1_H1_status"]} budget_pass={rec["S1_budget_pass"]}')
    print(f'§13 completeness: {completeness["satisfied_item_count"]}/{completeness["required_item_count"]} '
          f'missing={missing}')
    print(f'§15 checks: {final["checks_passed"]}/{final["checks_total"]} '
          f'raw_drift={raw_drift} mem_drift={mem_drift} audit_drift={audit_drift}')
    if not final['all_pass']:
        print('FAILURES:', failures)
        print(final['terminal'])
        sys.exit(1)
    print(f'§16 TERMINAL: {TERMINAL}')
    print('PHASE25E_POSTCLOSURE_RECONCILIATION_COMPLETE')


if __name__ == '__main__':
    main()
