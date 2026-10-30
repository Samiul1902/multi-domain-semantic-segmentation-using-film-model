"""Phase25E §11 PHASE_INDEX repair + §14 post-closure docs scan/repair.

Applies targeted wording repairs to the seven project-control documents so they
match the RECONCILED primary adjudication (raw paired p primary; Holm retained as
a secondary sensitivity) and the corrected model-execution inventory. No number
is changed; only wording and the canonical notebook SHA reference.

§11 -> reports/audits/phase25e_phase_index_repair.json
§14 -> reports/audits/phase25e_postclosure_docs_scan.json
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'

OLD_NB_SHA = 'e5d8f5657b43a18fd87e50bcf6f4834bcdd94dcbb2def0ef02ce720f0f1d7718'
NEW_NB_SHA = 'b587cc925fa178f1a0eaaa986caa3cb77dbc71ecd9fd520312af7f2097091797'

DOCS = ['docs/RULES.md', 'docs/TASKS.md', 'docs/MEMORY.md', 'docs/ARCHITECTURE.md',
        'docs/DESIGN.md', 'docs/PRD.md', 'notebooks/phasewise/PHASE_INDEX.md']

# (old, new, applies_to_or_None, label) - applied in order, per file.
RULES_STATS_OLD = ('Result: the learned paired-gain router (C7) **significantly beats every simple GT-free '
                   'proxy on precision@budget at 10%** (Holm-adjusted p<0.05), with the advantage shrinking '
                   'to statistical non-significance at 25%/50%; preservation holds')
RULES_STATS_NEW = ('Result: under the frozen PRIMARY statistic (raw paired two-sided p), the learned '
                   'paired-gain router (C7) **significantly beats every simple GT-free proxy on '
                   'precision@budget at the 10% and 25% budgets**, with the advantage shrinking to '
                   'statistical non-significance at 50% (Holm-Bonferroni retained only as a secondary '
                   'sensitivity: 10%); preservation holds')

OTHERS_STATS_OLD = ('Result: C7 **significantly beats every simple GT-free proxy on precision@budget at 10%** '
                    '(Holm-adjusted p<0.05), the advantage shrinking to non-significance at 25%/50%; '
                    'preservation holds')
OTHERS_STATS_NEW = ('Result: under the frozen PRIMARY statistic (raw paired two-sided p), C7 '
                    '**significantly beats every simple GT-free proxy on precision@budget at the 10% and 25% '
                    'budgets**, the advantage shrinking to non-significance at 50% (Holm-Bonferroni retained '
                    'only as a secondary sensitivity: 10%); preservation holds')

REPLACEMENTS = [
    # 1. canonical notebook SHA (global, per file)
    (OLD_NB_SHA, NEW_NB_SHA, None, 'notebook_sha'),
    # 2. RULES statistics wording
    (RULES_STATS_OLD, RULES_STATS_NEW, 'docs/RULES.md', 's1_stats_wording_rules'),
    # 3. other docs statistics wording
    (OTHERS_STATS_OLD, OTHERS_STATS_NEW, None, 's1_stats_wording'),
    # 4. model-execution wording
    ('No models were loaded or run in this evaluation; no lambda was selected;',
     'The frozen final benefit-router checkpoint was loaded once and run in a single outcome-blind forward '
     'pass over the 4,957 ROUTER_DEVELOPMENT feature rows (no global-model forward, no regional-refiner '
     'forward, no training); no lambda was selected;', None, 'model_execution_wording'),
    # 5. H1 scope
    ('H1 is scoped to tight budgets', 'H1 is scoped to the tight and medium budgets (10%/25%)',
     None, 'h1_scope'),
    # 6. evidence line
    ('Evidence: `reports/audits/phase25e_policy_evaluation_summary.json`, '
     '`reports/audits/phase25e_adjudication.json`, `reports/audits/phase25e_final_freeze.json`.',
     'Evidence: `reports/audits/phase25e_policy_evaluation_summary.json`, '
     '`reports/audits/phase25e_adjudication.json` (original closure), '
     '`reports/audits/phase25e_adjudication_reconciled.json` (PRIMARY adjudication, raw paired p), '
     '`reports/audits/phase25e_multiplicity_provenance_audit.json`, '
     '`reports/audits/phase25e_final_freeze.json`.', None, 'evidence_line'),
    # 7a. MEMORY.md S1 summary
    ('(significant vs all simple\nGT-free proxies at 10% budget, non-significant at 25%/50%)',
     '(significant vs all simple\nGT-free proxies at 10% and 25% budgets under the frozen primary raw '
     'paired p; non-significant at 50%)', 'docs/MEMORY.md', 'memory_s1_summary'),
    # 7b. MEMORY.md model-loaded claim
    ('No lambda selected; no model loaded; holdout/VAL808/TEST untouched.',
     'No lambda selected; exactly one outcome-blind forward pass of the frozen final router over the DEV '
     'rows (no global-model or refiner forward, no training); holdout/VAL808/TEST untouched.',
     'docs/MEMORY.md', 'memory_model_execution'),
    # 8. TASKS.md status table note
    (f'frontier and adjudication frozen; notebook `{NEW_NB_SHA}`',
     f'frontier and adjudication frozen (PRIMARY adjudication reconciled: raw paired p; Holm retained as a '
     f'secondary sensitivity); notebook `{NEW_NB_SHA}`', 'docs/TASKS.md', 'tasks_status_note'),
    # 9a. PHASE_INDEX 25E-EVAL Supersedes column
    ('| **COMPLETE_FROZEN** | **Canonical** | — | `PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE',
     f'| **COMPLETE_FROZEN** | **Canonical** | pre-reconciliation build (SHA `{OLD_NB_SHA}`, archived) | '
     f'`PHASE25E_RESOURCE_GATE_POLICY_EVALUATION_COMPLETE',
     'notebooks/phasewise/PHASE_INDEX.md', 'phase_index_supersedes'),
    # 9b. PHASE_INDEX 25E-EVAL Notes column
    ('| 0 | S1/H1 PARTIAL (sig. at 10% budget); S2 satisfied; no domain collapse; bootstrap 2000 seed 42; '
     '3× byte-identical; 8/8 PNG valid |',
     '| 0 | S1/H1 PARTIAL (primary raw paired p significant at the 10% and 25% budgets; not at 50%); '
     'S2 satisfied; no domain collapse; bootstrap 2000 seed 42; 3× byte-identical; 8/8 PNG valid |',
     'notebooks/phasewise/PHASE_INDEX.md', 'phase_index_notes'),
    # 10. provenance expansion on the notebook description
    ('(3× byte-identical)', f'(3× byte-identical; post-reconciliation rebuild superseding the archived '
     f'pre-reconciliation build SHA `{OLD_NB_SHA}`)', None, 'notebook_provenance'),
]

STALE_MARKERS = [
    'Holm-adjusted p<0.05',
    'No models were loaded or run in this evaluation',
    'no model loaded',
    'H1 is scoped to tight budgets',
    'non-significance at 25%/50%',
    'non-significant at 25%/50%',
    'sig. at 10% budget',
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    results = {}
    all_failures = []

    for rel in DOCS:
        p = ROOT / rel
        before_sha = sha(p)
        text = p.read_text(encoding='utf-8')
        applied = []
        for old, new, only, label in REPLACEMENTS:
            if only is not None and only != rel:
                continue
            n = text.count(old)
            if n > 0:
                text = text.replace(old, new)
            applied.append({'label': label, 'occurrences_replaced': n})
        p.write_text(text, encoding='utf-8')
        after_sha = sha(p)

        residual = {m: text.count(m) for m in STALE_MARKERS}
        # the OLD notebook SHA may appear ONLY as recorded provenance
        total_old = text.count(OLD_NB_SHA)
        prov_old = (text.count(f'pre-reconciliation build SHA `{OLD_NB_SHA}`')
                    + text.count(f'pre-reconciliation build (SHA `{OLD_NB_SHA}`'))
        if total_old != prov_old:
            residual[f'STALE_OLD_NOTEBOOK_SHA (total={total_old}, provenance={prov_old})'] = \
                total_old - prov_old
        residual = {m: c for m, c in residual.items() if c > 0}
        if residual:
            all_failures.append(f'{rel}:RESIDUAL_STALE:{list(residual)}')

        results[rel] = {
            'before_sha256': before_sha,
            'after_sha256': after_sha,
            'changed': before_sha != after_sha,
            'replacements_applied': applied,
            'residual_stale_markers': residual,
        }

    # §11 PHASE_INDEX repair artifact
    pi = results['notebooks/phasewise/PHASE_INDEX.md']
    phase_index_repair = {
        'classification': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION',
        'stage': 'PHASE_INDEX_REPAIR',
        'document': 'notebooks/phasewise/PHASE_INDEX.md',
        'before_sha256': pi['before_sha256'],
        'after_sha256': pi['after_sha256'],
        'changed': pi['changed'],
        'repairs': [a for a in pi['replacements_applied'] if a['label'].startswith('phase_index')],
        'notebook_sha_updated_to': NEW_NB_SHA,
        'pre_reconciliation_notebook_sha': OLD_NB_SHA,
        'residual_stale_markers': pi['residual_stale_markers'],
        's1_wording_now': ('S1/H1 PARTIAL (primary raw paired p significant at the 10% and 25% budgets; '
                           'not at 50%)'),
        'failures': [f for f in all_failures if 'PHASE_INDEX' in f],
        'all_pass': not [f for f in all_failures if 'PHASE_INDEX' in f],
    }
    (AUD / 'phase25e_phase_index_repair.json').write_text(
        json.dumps(phase_index_repair, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    docs_scan = {
        'classification': 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION',
        'stage': 'POSTCLOSURE_DOCS_SCAN',
        'documents_scanned': DOCS,
        'document_count': len(DOCS),
        'results': results,
        'reconciled_adjudication_source': 'reports/audits/phase25e_adjudication_reconciled.json',
        'multiplicity_provenance_source': 'reports/audits/phase25e_multiplicity_provenance_audit.json',
        'stale_marker_checklist': STALE_MARKERS,
        'all_stale_markers_cleared': not all_failures,
        'documents_changed': [rel for rel, r in results.items() if r['changed']],
        'failures': all_failures,
        'all_pass': not all_failures,
    }
    (AUD / 'phase25e_postclosure_docs_scan.json').write_text(
        json.dumps(docs_scan, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    for rel, r in results.items():
        print(f'{rel}: changed={r["changed"]} residual={r["residual_stale_markers"]}')
    if all_failures:
        print('FAILURES:', all_failures)
        raise SystemExit(1)
    print('PHASE25E_DOCS_REPAIR_PASS')


if __name__ == '__main__':
    main()
