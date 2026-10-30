"""Phase25E control-document status sync (deterministic, additive).

Replaces the Phase25E specification-freeze state block with the completed
policy-evaluation state across the seven core control documents, updates
secondary status lines, and records a before/after SHA audit.
"""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
DOCS = ['docs/ARCHITECTURE.md', 'docs/DESIGN.md', 'docs/MEMORY.md', 'docs/PRD.md',
        'docs/RULES.md', 'docs/TASKS.md', 'notebooks/phasewise/PHASE_INDEX.md']

OLD_TITLE = '## Phase25E specification freeze — current state (2026-10-01)'
NEW_TITLE = '## Phase25E policy evaluation complete — current state (2026-10-01)'

OLD_P1 = ('Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: '
          '**COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: '
          '**ELIGIBLE_NOT_STARTED**. Phase25F: **NOT_STARTED**. Phase25G: **NOT_STARTED**. Phase25E is not fully complete.')
NEW_P1 = ('Phase25D: **COMPLETE_CANONICAL / TRAINED / FROZEN**. Phase25E resource-gate specification: '
          '**COMPLETE_FROZEN** (`ra_medfilm_barr_resource_gate_v1_0`). Phase25E scientific policy evaluation: '
          '**COMPLETE_FROZEN**. Phase25F: **NOT_STARTED**. Phase25G: **NOT_STARTED**.')

OLD_P4 = ('No models were loaded or run, no outcomes were joined, and no policy metrics were calculated. '
          'ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39. Final-router DEV '
          'threshold calibration and policy outcome evaluation require separate execution authorization.')
NEW_P4 = ('The 45 frozen OOF memberships were joined to the frozen Phase25C paired-gain outcomes on '
          'ROUTER_DEVELOPMENT only (4957). Statistics (domain-stratified group bootstrap, 2000 replicates, seed 42) '
          'and final-router DEV thresholds were frozen **before** the outcome join. Result: C7 **significantly beats '
          'every simple GT-free proxy on precision@budget at 10%** (Holm-adjusted p<0.05), the advantage shrinking to '
          'non-significance at 25%/50%; preservation holds; a usable accuracy-compute frontier exists. H1 is scoped to '
          'tight budgets.\n\nNo models were loaded or run in this evaluation; no lambda was selected; C9 post-safety '
          'was not evaluated. ROUTER_HOLDOUT and VAL808 remain untouched; TEST remains locked until Phase39.')

OLD_P5 = ('Executed DESIGN/AUDIT notebook: `notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate_specification.ipynb`; '
          'SHA-256 `a431b3604021c0f4ffaaa6153302d674a38167b1792ab55d09a58a8ad2a5c41c` (3× byte-identical). Evidence: '
          '`reports/audits/phase25e_spec_final_check.json`, `reports/audits/phase25e_spec_governance.json`, and '
          '`reports/tables/phase25e_policy_membership_manifest.csv`.')
NEW_P5 = ('Executed scientific notebook: `notebooks/phasewise/phase_25e_resource_gate/phase25e_resource_gate.ipynb`; '
          'SHA-256 `e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718` (3× byte-identical). Evidence: '
          '`reports/audits/phase25e_policy_evaluation_summary.json`, `reports/audits/phase25e_adjudication.json`, '
          '`reports/audits/phase25e_final_freeze.json`.')

OLD_TERM = ('Specification terminal: `PHASE25E_RESOURCE_GATE_SPEC_V1_0_COMPLETE__COST_BUDGET_LAMBDA_TIE_AND_COMPARATOR'
            '_RULES_FROZEN__PHASE25E_POLICY_EVALUATION_ELIGIBLE_NOT_STARTED`.')
NEW_TERM = ('Terminal: `PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV'
            '_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED`.')

OLD_LV = '**Last verified:** 2026-10-01 — Phase25D canonical reviewer-notebook compliance repair complete'
NEW_LV = '**Last verified:** 2026-10-01 — Phase25E scientific policy evaluation COMPLETE_FROZEN'

# Secondary, doc-specific replacements
SECONDARY = {
    'docs/TASKS.md': [
        ('## 3. Current focus — Phase 24 v1.2 CLOSED · Phase 25B COMPLETE · Phase 25C COMPLETE · Phase25D COMPLETE · Phase25E ELIGIBLE_NOT_STARTED',
         '## 3. Current focus — Phase 24 v1.2 CLOSED · Phase 25B COMPLETE · Phase 25C COMPLETE · Phase25D COMPLETE · Phase25E COMPLETE_FROZEN'),
    ],
    'docs/ARCHITECTURE.md': [
        ('> **Phase25B and Phase25C are COMPLETE canonical**. Phase25E is **ELIGIBLE_NOT_STARTED**.',
         '> **Phase25B and Phase25C are COMPLETE canonical**. Phase25E scientific policy evaluation is **COMPLETE_FROZEN**.'),
    ],
    'docs/DESIGN.md': [
        ('> Phase25E is **ELIGIBLE_NOT_STARTED**. The bullets below retain the original design intent.',
         '> Phase25E scientific policy evaluation is **COMPLETE_FROZEN**. The bullets below retain the original design intent.'),
    ],
    'docs/PRD.md': [
        ('Phase25B and Phase25C are COMPLETE canonical; Phase25E is **ELIGIBLE_NOT_STARTED**.',
         'Phase25B and Phase25C are COMPLETE canonical; Phase25E scientific policy evaluation is **COMPLETE_FROZEN**.'),
        ('benefit router have since been trained and frozen through Phase25D. The resource-aware gate\nand complete integrated routing system remain unvalidated; Phase25E is ELIGIBLE_NOT_STARTED.',
         'benefit router have since been trained and frozen through Phase25D. The resource-gate policy evaluation\nis now COMPLETE_FROZEN (Phase25E); the complete integrated routing system remains to be validated in\nlater phases (Phase25F post-safety onward).'),
    ],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    failures = []
    records = {}
    for rel in DOCS:
        p = ROOT / rel
        before = sha(p)
        text = p.read_text(encoding='utf-8')
        original = text
        for old, new in [(OLD_TITLE, NEW_TITLE), (OLD_P1, NEW_P1), (OLD_P4, NEW_P4),
                         (OLD_P5, NEW_P5), (OLD_TERM, NEW_TERM), (OLD_LV, NEW_LV)]:
            if old in text:
                text = text.replace(old, new)
        for old, new in SECONDARY.get(rel, []):
            if old in text:
                text = text.replace(old, new)
            else:
                failures.append(f'SECONDARY_NOT_FOUND:{rel}')
        if text != original:
            p.write_text(text, encoding='utf-8')
        after = sha(p)
        records[rel] = {'before_sha256': before, 'after_sha256': after, 'changed': before != after}
        # no residual stale markers
        residual = text.count('Phase25E is **ELIGIBLE_NOT_STARTED**') + text.count('Phase25E scientific policy evaluation: **ELIGIBLE_NOT_STARTED**')
        records[rel]['residual_stale_markers'] = residual
        if residual:
            failures.append(f'RESIDUAL_STALE:{rel}')

    audit = {
        'classification': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION',
        'stage': 'STATUS_SYNC',
        'documents': records,
        'new_terminal': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE__OOF_FIXED_BUDGET_FRONTIER_AND_FINAL_DEV_THRESHOLDS_FROZEN__PHASE25F_ELIGIBLE_NOT_STARTED',
        'phase25f_status': 'NOT_STARTED', 'phase25g_status': 'NOT_STARTED',
        'failures': failures,
        'all_pass': not failures,
    }
    (AUD / 'phase25e_status_sync.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v['changed'] for k, v in records.items()}, indent=2))
    print(f'Failures: {failures}')
    if failures:
        sys.exit(1)
    print('PHASE25E_STATUS_SYNC_PASS')


if __name__ == '__main__':
    main()
