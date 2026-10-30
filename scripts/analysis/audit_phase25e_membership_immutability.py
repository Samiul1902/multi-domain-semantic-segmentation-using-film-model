"""Phase25E MEMBERSHIP IMMUTABILITY AUDIT (outcome-blind).

Verifies the 45 prospective membership CSVs are internally consistent and
structurally immutable before any outcome join:
  - SHA matches the frozen manifest for every policy
  - exactly N_DEV rows, identity == frozen DEV sample_id set
  - selected_count == K_b; selected set == top-K of the frozen rank order
  - rank is a total order consistent with routing_score DESC, sample_id ASC
  - ineligible rows are FORCED_SKIP and never selected
  - C8(lambda,budget) membership == C7(budget) membership for every lambda
Writes reports/audits/phase25e_membership_immutability_audit.json.
"""
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
MEM_DIR = TABLE / 'phase25e_policy_memberships_v1_0'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    failures = []
    manifest = pd.read_csv(TABLE / 'phase25e_policy_membership_manifest.csv', dtype=str)
    meta = pd.read_csv(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv',
                       usecols=['sample_id', 'action_available'], dtype={'sample_id': str})
    frozen_ids = set(meta.sample_id)
    eligible_ids = set(meta.loc[meta.action_available.astype(bool), 'sample_id'])
    n_dev = len(frozen_ids)

    per_policy = []
    c7_membership = {}
    c8_membership = {}
    for _, row in manifest.iterrows():
        pid = row['policy_id']
        comp = row['comparator']
        lam = row['lambda'] if isinstance(row['lambda'], str) else ''
        budget = row['budget']
        k_b = int(row['K_b'])
        path = ROOT / row['membership_path']
        actual_sha = sha(path)
        sha_ok = actual_sha == row['membership_sha256']

        df = pd.read_csv(path, dtype={'sample_id': str})
        ids = set(df.sample_id)
        identity_ok = ids == frozen_ids and len(df) == n_dev
        # selected set
        sel = set(df.loc[df.selected.astype(int) == 1, 'sample_id'])
        count_ok = len(sel) == k_b == int(row['selected_count'])
        # forced skip discipline
        ineligible = df.loc[df.action_available.astype(int) == 0]
        forced_skip_ok = bool((ineligible.decision == 'FORCED_SKIP').all()) and \
            int(ineligible.selected.astype(int).sum()) == 0
        # rank order consistency (eligible only)
        elig = df.loc[df.action_available.astype(int) == 1].copy()
        elig['rkey'] = elig.routing_score_exact.map(lambda s: Fraction(s))
        elig = elig.sort_values('sample_id', kind='stable')
        order = sorted(elig.to_dict('records'),
                       key=lambda r: (-r['rkey'], r['sample_id']))
        topk = set(r['sample_id'] for r in order[:k_b])
        topk_ok = topk == sel
        # rank field consistency
        rank_ok = True
        for pos, r in enumerate(order, start=1):
            if str(r['rank']) != str(pos):
                rank_ok = False
                break
        # ineligible rows must have blank rank
        blank_rank_ok = bool((ineligible['rank'].isna() | (ineligible['rank'].astype(str) == '')).all())
        # decision consistency
        dec_ok = bool((df.apply(
            lambda r: (r['decision'] == 'EXECUTE') if int(r['selected']) == 1
            else ('FORCED_SKIP' if int(r['action_available']) == 0 else 'SKIP'), axis=1)).all())

        per_policy.append({
            'policy_id': pid, 'comparator': comp, 'lambda': lam, 'budget': budget,
            'K_b': k_b, 'rows': len(df), 'selected_count': len(sel),
            'sha_match': sha_ok, 'identity_match': identity_ok, 'count_match': count_ok,
            'forced_skip_discipline': forced_skip_ok, 'topk_equals_selected': topk_ok,
            'rank_consistent': rank_ok, 'ineligible_rank_blank': blank_rank_ok,
            'decision_consistent': dec_ok,
        })
        for cond, label in [
            (sha_ok, 'SHA'), (identity_ok, 'IDENTITY'), (count_ok, 'COUNT'),
            (forced_skip_ok, 'FORCED_SKIP'), (topk_ok, 'TOPK'), (rank_ok, 'RANK'),
            (blank_rank_ok, 'BLANK_RANK'), (dec_ok, 'DECISION')]:
            if not cond:
                failures.append(f'{label}:{pid}')
        if comp == 'C7':
            c7_membership[budget] = sel
        if comp == 'C8':
            c8_membership[(lam, budget)] = sel

    # C8 == C7 structural equivalence
    equivalence = []
    for (lam, budget), sel in sorted(c8_membership.items()):
        same = sel == c7_membership[budget]
        equivalence.append({'lambda': lam, 'budget': budget, 'same_membership': same,
                            'selected_count': len(sel)})
        if not same:
            failures.append(f'C8_NE_C7:lambda{lam}_budget{budget}')

    audit = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'MEMBERSHIP_IMMUTABILITY',
        'n_dev': n_dev,
        'n_eligible': len(eligible_ids),
        'policy_count': len(per_policy),
        'per_policy': per_policy,
        'c8_equals_c7': equivalence,
        'checks': {
            'all_45_shas_exact': all(p['sha_match'] for p in per_policy),
            'all_identities_match': all(p['identity_match'] for p in per_policy),
            'all_counts_match_Kb': all(p['count_match'] for p in per_policy),
            'all_topk_equals_selected': all(p['topk_equals_selected'] for p in per_policy),
            'all_ranks_consistent': all(p['rank_consistent'] for p in per_policy),
            'all_forced_skip_discipline': all(p['forced_skip_discipline'] for p in per_policy),
            'c8_redundant_with_c7': all(e['same_membership'] for e in equivalence),
        },
        'failures': failures,
        'outcome_access': False,
        'all_pass': not failures,
    }
    (AUD / 'phase25e_membership_immutability_audit.json').write_text(
        json.dumps(audit, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(f'Policies audited: {len(per_policy)}; N_DEV={n_dev}; N_eligible={len(eligible_ids)}', flush=True)
    print(f'Failures: {failures}', flush=True)
    if not audit['all_pass']:
        sys.exit(1)
    print('PHASE25E_MEMBERSHIP_IMMUTABILITY_PASS', flush=True)


if __name__ == '__main__':
    main()
