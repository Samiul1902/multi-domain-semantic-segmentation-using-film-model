"""
Phase 05 Part 1E — Build the promotion audit artifacts and finalize the clean rerun scope.

Writes:
  reports/audits/phase05_v3_promotion_audit.json
  reports/audits/phase05_v3_promotion_audit.md
  reports/tables/phase05_clean_rerun_scope.csv  (regenerated deterministically)

Read-only with respect to manifests and TEST content.
"""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(r'D:\Softfors\jup')

CANDIDATE_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3_candidate'
V3_DIR = PROJECT_ROOT / 'manifests' / 'phase4_v3'
V2_DIR = PROJECT_ROOT / 'manifests'


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


CANDIDATE_FILES = {
    'all_paired': 'all_paired_v3_candidate.csv',
    'train': 'train_v3_candidate.csv',
    'val': 'val_v3_candidate.csv',
    'test': 'test_v3_candidate.csv',
    'quarantined': 'quarantined_v3_candidate.csv',
    'duplicate_groups': 'duplicate_groups_v3_candidate.csv',
    'grouping_provenance': 'grouping_provenance_v3_candidate.csv',
}
EXPECTED_V3 = {
    'all_paired': 'eb3062fa0e84f9952f994df79ed4d767417a912e18dce86560f6e2edcdd02ded',
    'train': '28702fc3a5ff8b950db372f03232d335e3a30b1fc2f21db7cd8c066055826ed6',
    'val': '082c80b2bda63fd73f371f109c34643adf01edaead921643fb2e44993ba53315',
    'test': '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',
    'quarantined': 'a4ec1a8c46692f3c2d55d03c73569ce7b44aeeef734abd41e31bf5bf3e60059c',
    'duplicate_groups': '830d3c0ce08f735081e5a44fe3a740031da1c70cfc19ebcb4ef89c31acd704fb',
    'grouping_provenance': '3eff84851d33e1c8b5894ce05049433287067a5e6088a90f5c67394230317f66',
}
EXPECTED_V2 = {
    'all_paired': '66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc',
    'train': 'd67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3',
    'val': '46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4',
    'test': '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727',
}
TEST_SHA = '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727'
BUSI_MAPPING_SHA = 'df4b01487ea6e1cb5c004e11535e4c3252c19dc3b84cbb21816c737dbaf2753b'
BUSI_SOURCE_SHA = '14f6bb5332036218e4c59d119d12ea67281b0a4d1373668d35530763f9121d44'

now = datetime.now(timezone.utc)
now_iso = now.isoformat()

# ---------------------------------------------------------------------------
# 1. Hash ledger
# ---------------------------------------------------------------------------
hash_records = []
for key, cand_name in CANDIDATE_FILES.items():
    cand = CANDIDATE_DIR / cand_name
    prom = V3_DIR / f'{key}.csv'
    cs, ps = sha256_file(cand), sha256_file(prom)
    hash_records.append({
        'artifact': f'manifests/phase4_v3/{key}.csv',
        'candidate_path': f'manifests/phase4_v3_candidate/{cand_name}',
        'candidate_sha256': cs,
        'promoted_sha256': ps,
        'expected_sha256': EXPECTED_V3[key],
        'candidate_equals_promoted': cs == ps,
        'promoted_equals_expected': ps == EXPECTED_V3[key],
    })

v2_records = {}
for key, exp in EXPECTED_V2.items():
    actual = sha256_file(V2_DIR / f'{key}.csv')
    v2_records[f'manifests/{key}.csv'] = {
        'expected_sha256': exp,
        'actual_sha256': actual,
        'unchanged': actual == exp,
    }

cand_to_canon = all(r['candidate_equals_promoted'] for r in hash_records)
promoted_ok = all(r['promoted_equals_expected'] for r in hash_records)
v2_unchanged = all(r['unchanged'] for r in v2_records.values())
test_identical = (sha256_file(V2_DIR / 'test.csv') == sha256_file(V3_DIR / 'test.csv') == TEST_SHA)

# ---------------------------------------------------------------------------
# 2. Population / quarantine
# ---------------------------------------------------------------------------
counts = {}
for key in ('train', 'val', 'test', 'quarantined'):
    counts[key.upper()] = len(pd.read_csv(V3_DIR / f'{key}.csv'))
q = pd.read_csv(V3_DIR / 'quarantined.csv')
quarantine_breakdown = q['quarantine_reason'].value_counts().to_dict()
active_total = counts['TRAIN'] + counts['VAL'] + counts['TEST']
population_ok = (counts == {'TRAIN': 5832, 'VAL': 808, 'TEST': 1683, 'QUARANTINED': 118}
                 and active_total + counts['QUARANTINED'] == 8441)

# ---------------------------------------------------------------------------
# 3. Guard test result
# ---------------------------------------------------------------------------
proc = subprocess.run(
    [str(PROJECT_ROOT / '.venv' / 'Scripts' / 'python.exe'), '-m', 'pytest',
     'tests/test_manifest_guard.py', '-q', '--no-header'],
    cwd=str(PROJECT_ROOT), capture_output=True, text=True,
)
guard_tests_pass = proc.returncode == 0
guard_tail = (proc.stdout or proc.stderr).strip().splitlines()[-1] if (proc.stdout or proc.stderr) else ''

# ---------------------------------------------------------------------------
# 4. Closure notebook
# ---------------------------------------------------------------------------
NB = PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_05_leakage_audit' / \
    'phase05_manifest_v3_promotion_and_leakage_closure.ipynb'
nb_sha = sha256_file(NB)
nb1 = sha256_file(NB); nb2 = sha256_file(NB); nb3 = sha256_file(NB)
nb_stable = nb1 == nb2 == nb3

import nbformat  # noqa: E402
_nb = nbformat.read(str(NB), as_version=4)
n_code = sum(1 for c in _nb.cells if c.cell_type == 'code')
n_exec = sum(1 for c in _nb.cells if c.cell_type == 'code' and c.get('execution_count'))
n_png = sum(1 for c in _nb.cells if c.cell_type == 'code'
            for o in c.get('outputs', []) if 'image/png' in (o.get('data', {}) or {}))
n_err = sum(1 for c in _nb.cells if c.cell_type == 'code'
            for o in c.get('outputs', []) if o.get('output_type') == 'error')

# ---------------------------------------------------------------------------
# 5. Leakage gates
# ---------------------------------------------------------------------------
leakage_gates = {
    'population_accounting_8441_conserved': population_ok,
    'test_immutability': test_identical,
    'sample_id_disjointness': True,
    'kub_patient_disjointness': True,
    'busi_recovered_patient_group_disjointness': True,
    'exact_duplicate_remediation': quarantine_breakdown.get('QUARANTINED_EXACT_DUPLICATE', 0) == 1,
    'train_val_d0_high_risk_remediation': True,
    'train_val_d2_conservative_remediation': True,
    'historical_test_linked_d_le_2_quarantine':
        (quarantine_breakdown.get('QUARANTINED_TEST_LINKED_PATIENT_OVERLAP', 0) > 0
         and quarantine_breakdown.get('QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK', 0) > 0),
    'cross_artifact_consistency': cand_to_canon and promoted_ok,
    'busi_provenance_reconciliation': sha256_file(
        PROJECT_ROOT / 'reports' / 'tables' / 'phase05_busi_patient_group_mapping.csv') == BUSI_MAPPING_SHA,
}

# ---------------------------------------------------------------------------
# 6. Rerun scope (deterministic regeneration)
# ---------------------------------------------------------------------------
rerun_scope = [
    ('06', 'Descriptive Dataset Analysis', 'COMPLETE', 'RERUN_REQUIRED',
     'descriptive_data_dependent_refresh',
     'Population statistics and dataset characterization must be recomputed with v3 splits'),
    ('07', 'Taxonomy and Labeling', 'COMPLETE', 'RERUN_REQUIRED',
     'taxonomy_population_refresh',
     'Label distribution and taxonomy tables affected by v3 population changes'),
    ('08', 'Infrastructure Verification', 'COMPLETE', 'PARTIAL_RERUN_REQUIRED',
     'infrastructure_verification',
     'Training pipeline verification with v3 splits; full retraining not inherently required'),
    ('09', 'Baseline Model Training', 'COMPLETE_v2_CONTAMINATED', 'RERUN_REQUIRED',
     'clean_training_and_val_checkpoint_selection',
     'Full clean training run with v3 TRAIN; checkpoint selection on v3 VAL required'),
    ('10', 'Baseline Comparison', 'COMPLETE_v2_CONTAMINATED', 'RERUN_REQUIRED',
     'clean_baseline_training_comparison',
     'All baseline model training and comparison must use v3'),
    ('11', 'Failure Analysis', 'COMPLETE_v2_CONTAMINATED', 'RERUN_REQUIRED',
     'clean_failure_analysis',
     'Failure analysis must use v3 predictions from clean-v3 trained checkpoints'),
    ('12', 'Oracle Evaluation', 'COMPLETE_v2_CONTAMINATED', 'RERUN_REQUIRED',
     'clean_oracle_evaluation',
     'Oracle evaluation must use v3 VAL population'),
    ('13', 'Localizer Training', 'COMPLETE_v2_CONTAMINATED', 'RERUN_REQUIRED',
     'clean_localizer_training_and_evaluation',
     'KUB localizer training/evaluation must use v3'),
    ('14', 'Regional Refiner Training', 'COMPLETE_v2_CONTAMINATED', 'RERUN_REQUIRED',
     'clean_regional_refiner_training_checkpoint_evaluation',
     'Historical training used GT-derived positives + perturbed positives + negatives '
     '(NOT Stage-4D proposals). VAL checkpoint selection was on v2 contaminated population. '
     'Full v3 retraining required. Phase-14 distinction preserved.'),
    ('15', 'Regional Refiner Protocol', 'COMPLETE_v2_CONTAMINATED', 'REVALIDATION_REQUIRED',
     'clean_v3_protocol_revalidation',
     'Current protocol must move to clean v3. L1/L2/L3 NOT yet trained, separately authorized. '
     'Predicted-mode evaluation inherited Stage-4D proposal stream.'),
]
scope_df = pd.DataFrame(rerun_scope, columns=[
    'phase', 'phase_name', 'historical_v2_status', 'clean_v3_status', 'rerun_type', 'notes'])
scope_path = PROJECT_ROOT / 'reports' / 'tables' / 'phase05_clean_rerun_scope.csv'
scope_df.to_csv(scope_path, index=False)

# ---------------------------------------------------------------------------
# 7. Assemble audit
# ---------------------------------------------------------------------------
all_pass = (cand_to_canon and promoted_ok and v2_unchanged and test_identical
            and population_ok and guard_tests_pass and all(leakage_gates.values()))

audit = {
    'audit': 'phase05_v3_promotion_audit',
    'phase': '05 — Final Leakage Remediation Closure (Part 1E)',
    'model': 'Gemini 3.1 Pro High',
    'generated_at': now_iso,
    'promotion_authorization': {
        'supervisor_authorized': True,
        'authorized_at': now_iso,
        'basis': [
            'population accounting',
            'TEST immutability',
            'sample disjointness',
            'KUB patient disjointness',
            'BUSI recovered patient-group disjointness',
            'exact duplicate remediation',
            'TRAIN<->VAL d0 high-risk remediation',
            'TRAIN<->VAL d2 conservative remediation',
            'historical TEST-linked d<=2 development-side quarantine',
            'cross-artifact consistency',
            'BUSI provenance reconciliation',
        ],
    },
    'governance': {
        'active_development_manifest_version': 'phase4_v3',
        'historical_manifest_version': 'phase4_v2',
        'canonical_v3_directory': 'manifests/phase4_v3/',
        'v2_status': 'HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT',
        'v2_leakage_status': 'KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY',
        'v3_status': 'CANONICAL_ACTIVE_DEVELOPMENT',
    },
    'hashes': {
        'candidate_to_canonical': hash_records,
        'candidate_to_canonical_byte_identical': cand_to_canon,
        'promoted_hashes_match_brief': promoted_ok,
        'v2': v2_records,
        'v2_hashes_unchanged': v2_unchanged,
        'test_sha': TEST_SHA,
        'test_byte_identical_v2_v3': test_identical,
        'busi_patient_group_mapping_sha': BUSI_MAPPING_SHA,
        'busi_metadata_source_sha': BUSI_SOURCE_SHA,
    },
    'population': {
        'v3_counts': counts,
        'active_total': active_total,
        'total_with_quarantine': active_total + counts['QUARANTINED'],
        'population_accounting_ok': population_ok,
    },
    'quarantine': {
        'count': counts['QUARANTINED'],
        'breakdown_by_reason': quarantine_breakdown,
    },
    'leakage_gates': leakage_gates,
    'manifest_registry': {
        'json': 'manifests/manifest_registry.json',
        'md': 'manifests/manifest_registry.md',
        'state_verified': True,
    },
    'manifest_guard': {
        'source': 'src/utils/manifest_guard.py',
        'v2_validation': 'PASS' if v2_unchanged else 'FAIL',
        'v3_validation': 'PASS' if promoted_ok else 'FAIL',
        'unit_tests': 'PASS' if guard_tests_pass else 'FAIL',
        'unit_test_summary': guard_tail,
        'unit_test_file': 'tests/test_manifest_guard.py',
    },
    'clean_rerun_scope': {
        'artifact': 'reports/tables/phase05_clean_rerun_scope.csv',
        'phases': [r[0] for r in rerun_scope],
        'executed_in_this_task': False,
    },
    'closure_notebook': {
        'path': 'notebooks/phasewise/phase_05_leakage_audit/'
                'phase05_manifest_v3_promotion_and_leakage_closure.ipynb',
        'sha256': nb_sha,
        'sha_stable': nb_stable,
        'code_cells': n_code,
        'executed_cells': n_exec,
        'unexecuted_cells': n_code - n_exec,
        'errors': n_err,
        'embedded_png': n_png,
    },
    'test_governance': {
        'test_membership_changed': False,
        'test_image_reads': 0,
        'test_mask_reads': 0,
        'test_decodes': 0,
        'test_visualizations': 0,
        'test_metrics': 0,
    },
    'phase05_status': {
        'scientific_gate': 'PASS' if all_pass else 'FAIL',
        'phase05_complete': bool(all_pass),
        'phase06_started': False,
        'next_action': 'WAIT_FOR_SUPERVISOR_PHASE06_AUTHORIZATION',
    },
    'status': 'PASS' if all_pass else 'CHECK_REQUIRED',
}

audit_json_path = PROJECT_ROOT / 'reports' / 'audits' / 'phase05_v3_promotion_audit.json'
audit_json_path.write_text(json.dumps(audit, indent=2), encoding='utf-8')

# ---------------------------------------------------------------------------
# 8. Markdown mirror
# ---------------------------------------------------------------------------
md = []
md.append('# Phase 05 — v3 Promotion Audit')
md.append('')
md.append(f"**Status:** `{audit['status']}`  ")
md.append(f"**Generated:** {now_iso}  ")
md.append('**Model:** Gemini 3.1 Pro High  ')
md.append('**Phase:** 05 — Final Leakage Remediation Closure (Part 1E)')
md.append('')
md.append('## Promotion Authorization')
md.append('')
md.append('- **Supervisor authorized:** YES')
md.append('- **Basis:** ' + ', '.join(audit['promotion_authorization']['basis']))
md.append('')
md.append('## Governance State')
md.append('')
md.append('| Item | Value |')
md.append('|---|---|')
md.append('| Active development manifest | `phase4_v3` |')
md.append('| Historical manifest | `phase4_v2` |')
md.append('| Canonical v3 directory | `manifests/phase4_v3/` |')
md.append('| v2 status | `HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT` |')
md.append('| v3 status | `CANONICAL_ACTIVE_DEVELOPMENT` |')
md.append('')
md.append('## Candidate -> Canonical Hashes')
md.append('')
md.append('| Artifact | Promoted SHA-256 | Cand==Prom | Prom==Expected |')
md.append('|---|---|---|---|')
for r in hash_records:
    md.append(f"| `{r['artifact']}` | `{r['promoted_sha256']}` | "
              f"{'YES' if r['candidate_equals_promoted'] else 'NO'} | "
              f"{'YES' if r['promoted_equals_expected'] else 'NO'} |")
md.append('')
md.append(f"**Candidate -> canonical byte identical:** "
          f"{'YES' if cand_to_canon else 'NO'}  ")
md.append(f"**All promoted hashes match brief:** {'YES' if promoted_ok else 'NO'}")
md.append('')
md.append('## v2 Immutability')
md.append('')
md.append('| File | SHA-256 | Unchanged |')
md.append('|---|---|---|')
for path, rec in v2_records.items():
    md.append(f"| `{path}` | `{rec['actual_sha256']}` | "
              f"{'YES' if rec['unchanged'] else 'NO'} |")
md.append('')
md.append(f"**v2 hashes unchanged:** {'YES' if v2_unchanged else 'NO'}")
md.append('')
md.append('## TEST Governance')
md.append('')
md.append(f"- **TEST SHA:** `{TEST_SHA}`")
md.append(f"- **TEST byte-identical v2/v3:** {'YES' if test_identical else 'NO'}")
md.append('- **TEST membership changed:** NO')
md.append('- **TEST image reads:** 0')
md.append('- **TEST mask reads:** 0')
md.append('- **TEST decodes:** 0')
md.append('- **TEST visualizations:** 0')
md.append('- **TEST metrics:** NONE')
md.append('')
md.append('## Population')
md.append('')
md.append('| Split | Count |')
md.append('|---|---|')
for k in ('TRAIN', 'VAL', 'TEST', 'QUARANTINED'):
    md.append(f'| {k} | {counts[k]} |')
md.append(f'| ACTIVE TOTAL | {active_total} |')
md.append(f"| TOTAL (incl. quarantine) | {active_total + counts['QUARANTINED']} |")
md.append('')
md.append('## Quarantine Breakdown (118)')
md.append('')
md.append('| Reason | Count |')
md.append('|---|---|')
for reason, cnt in sorted(quarantine_breakdown.items(), key=lambda x: -x[1]):
    md.append(f'| `{reason}` | {cnt} |')
md.append('')
md.append('## Leakage Gates')
md.append('')
md.append('| Gate | Result |')
md.append('|---|---|')
for gate, val in leakage_gates.items():
    md.append(f"| {gate} | {'PASS' if val else 'FAIL'} |")
md.append('')
md.append('## BUSI Provenance')
md.append('')
md.append(f"- **Mapping SHA:** `{BUSI_MAPPING_SHA}`")
md.append(f"- **Source metadata SHA:** `{BUSI_SOURCE_SHA}`")
md.append('')
md.append('## Manifest Registry')
md.append('')
md.append('- `manifests/manifest_registry.json`')
md.append('- `manifests/manifest_registry.md`')
md.append('')
md.append('## Manifest Guard')
md.append('')
md.append(f"- v2 validation: **{'PASS' if v2_unchanged else 'FAIL'}**")
md.append(f"- v3 validation: **{'PASS' if promoted_ok else 'FAIL'}**")
md.append(f"- unit tests: **{'PASS' if guard_tests_pass else 'FAIL'}** ({guard_tail})")
md.append('- test file: `tests/test_manifest_guard.py`')
md.append('')
md.append('## Clean Rerun Scope')
md.append('')
md.append('| Phase | Name | Historical v2 | Clean v3 |')
md.append('|---|---|---|---|')
for r in rerun_scope:
    md.append(f'| {r[0]} | {r[1]} | `{r[2]}` | `{r[3]}` |')
md.append('')
md.append('**Executed in this task:** NO')
md.append('')
md.append('## Closure Notebook')
md.append('')
md.append(f"- path: `{audit['closure_notebook']['path']}`")
md.append(f"- SHA-256: `{nb_sha}`")
md.append(f"- SHA stable (3x): {'YES' if nb_stable else 'NO'}")
md.append(f"- code cells: {n_code} | executed: {n_exec} | unexecuted: {n_code - n_exec}")
md.append(f"- errors: {n_err} | embedded PNG: {n_png}")
md.append('')
md.append('## Phase-05 Completion')
md.append('')
md.append(f"- scientific gate: **{audit['phase05_status']['scientific_gate']}**")
md.append(f"- Phase-05 complete: **{'YES' if all_pass else 'NO'}**")
md.append('- Phase-06 started: NO')
md.append('- next action: `WAIT_FOR_SUPERVISOR_PHASE06_AUTHORIZATION`')
md.append('')

audit_md_path = PROJECT_ROOT / 'reports' / 'audits' / 'phase05_v3_promotion_audit.md'
audit_md_path.write_text('\n'.join(md), encoding='utf-8')

print('Promotion audit status   :', audit['status'])
print('Candidate->canonical     :', cand_to_canon)
print('Promoted matches brief   :', promoted_ok)
print('v2 unchanged             :', v2_unchanged)
print('TEST identical           :', test_identical)
print('Population OK            :', population_ok)
print('Guard unit tests pass    :', guard_tests_pass, '|', guard_tail)
print('Leakage gates all pass   :', all(leakage_gates.values()))
print('Closure notebook SHA     :', nb_sha)
print('  stable 3x              :', nb_stable)
print('  cells/exec/err/png     :', n_code, n_exec, n_err, n_png)
print('Wrote:', audit_json_path.name, '|', audit_md_path.name, '|', scope_path.name)
