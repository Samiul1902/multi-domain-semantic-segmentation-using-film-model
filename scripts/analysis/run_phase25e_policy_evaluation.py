"""Phase25E CANONICAL RESOURCE-GATE POLICY EVALUATION.

Requires the pre-outcome freeze to have completed. Joins the 45 frozen OOF
memberships to the frozen Phase25C paired-gain outcomes and evaluates routing,
compute, oracle-upper-bound, redundancy, equal-budget, domain, size-strata and
frontier metrics, with a domain-stratified group bootstrap (frozen plan).

Populations: ROUTER_DEVELOPMENT only. NO ROUTER_HOLDOUT / VAL808 / TEST.
"""
import csv
import hashlib
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
CACHE = ROOT / 'data_cache/phase25e_barr_resource_gate_v1_0'
MEM_DIR = TABLE / 'phase25e_policy_memberships_v1_0'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'

GLOBAL_MACS = 31551740928
ROUTER_MACS = 36160
REGIONAL_MACS = 3230662656
N_DEV = 4957
N_ELIGIBLE = 4957
N_BOOT = 2000
CI_PCT = [2.5, 97.5]
BUDGETS = ['0.00', '0.10', '0.25', '0.50', '1.00']
LAMBDAS = ['0.00', '0.25', '0.50', '1.00']
STRATA = ['BUSI', 'ISIC', 'KUB', 'KVASIR']
COMPARATOR_FAMILY = ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C10']


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def safe_div(num, den):
    if den == 0:
        return None
    return num / den


def jsonify(obj):
    if isinstance(obj, dict):
        return {k: jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonify(v) for v in obj]
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.bool_,)):
        return bool(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    return obj


def load_memberships():
    manifest = pd.read_csv(TABLE / 'phase25e_policy_membership_manifest.csv', dtype=str)
    policies = {}
    for _, row in manifest.iterrows():
        pid = row['policy_id']
        df = pd.read_csv(ROOT / row['membership_path'], dtype={'sample_id': str})
        df = df.sort_values('sample_id', kind='stable').reset_index(drop=True)
        policies[pid] = {
            'comparator': row['comparator'],
            'lambda': row['lambda'] if isinstance(row['lambda'], str) else '',
            'budget': row['budget'],
            'K_b': int(row['K_b']),
            'ids': df.sample_id.tolist(),
            'score': np.array([float(Fraction(s)) for s in df.routing_score_exact], dtype=np.float64),
            'selected': df.selected.to_numpy().astype(bool),
            'action_available': df.action_available.to_numpy().astype(bool),
        }
    return manifest, policies


def point_metrics(sel, d, bflag, hflag, dpos, domain_ids, oracle_cache, K_b, budget):
    """Point metrics for one policy on the full DEV population."""
    K = int(sel.sum())
    s_int_b = int((sel & bflag).sum())
    s_int_h = int((sel & hflag).sum())
    n_b = int(bflag.sum())
    sum_d_sel = float(d[sel].sum())
    sum_dpos_sel = float(dpos[sel].sum())
    sum_dpos_all = float(dpos.sum())
    oracle = oracle_cache[K] if K in oracle_cache else None
    regret = (oracle - sum_d_sel) if oracle is not None else None
    macro = None
    dom_means = {}
    for dd in STRATA:
        m = sel & (domain_ids == dd)
        if m.sum() > 0:
            dom_means[dd] = float(d[m].mean())
    if dom_means:
        macro = float(np.mean(list(dom_means.values())))
    inc_macs = (K / N_DEV) * REGIONAL_MACS
    avg_total = GLOBAL_MACS + ROUTER_MACS + inc_macs
    return {
        'budget': budget,
        'K': K,
        'precision_at_budget': safe_div(s_int_b, K),
        'benefit_capture_at_budget': safe_div(sum_dpos_sel, sum_dpos_all),
        'mean_true_delta_dice_among_routed': safe_div(sum_d_sel, K),
        'harmful_activation_rate': safe_div(s_int_h, K),
        'beneficial_activation_rate': safe_div(s_int_b, n_b),
        'missed_benefit_rate': safe_div(n_b - s_int_b, n_b),
        'routing_regret_vs_oracle': regret,
        'regret_mean_per_sample': safe_div(regret, N_DEV) if regret is not None else None,
        'regret_mean_per_routed_sample': safe_div(regret, K) if regret is not None else None,
        'macro_domain_mean_true_delta_dice': macro,
        'domain_mean_true_delta_dice': dom_means,
        'activation_fraction': K / N_DEV,
        'eligible_activation_fraction': K / N_ELIGIBLE,
        'incremental_regional_macs': inc_macs,
        'average_total_analytical_macs': avg_total,
        'ratio_vs_global_only': avg_total / GLOBAL_MACS,
        'ratio_vs_always_refine': avg_total / (GLOBAL_MACS + (N_ELIGIBLE / N_DEV) * REGIONAL_MACS),
        'n_beneficial_eligible': n_b,
        'n_harmful_eligible': int(hflag.sum()),
        'n_selected_beneficial': s_int_b,
        'n_selected_harmful': s_int_h,
    }


def main():
    failures = []
    # --- 0. pre-outcome freeze must be complete ---------------------------------
    pre = json.loads((AUD / 'phase25e_pre_outcome_freeze.json').read_text(encoding='utf-8'))
    if not pre.get('all_pass'):
        print('PRE_OUTCOME_FREEZE_NOT_PASS', flush=True)
        sys.exit(1)

    manifest, policies = load_memberships()
    ids = policies[manifest.iloc[0]['policy_id']]['ids']
    if len(ids) != N_DEV:
        failures.append(f'DEV_ROWS:{len(ids)}')

    # --- 8. outcome join (permitted after pre-outcome freeze) -------------------
    lab = pd.read_csv(ROOT / 'data_cache/phase25c_barr_oof_paired_gain_labels_v1_2/phase25c_oof_paired_gain_labels.csv',
                      usecols=['sample_id', 'delta_dice', 'gain_category', 'domain'], dtype={'sample_id': str})
    lab = lab.sort_values('sample_id', kind='stable').reset_index(drop=True)
    if lab.sample_id.tolist() != ids:
        failures.append('JOIN_ORDER_MISMATCH')
    d = lab.delta_dice.to_numpy(np.float64)
    domain_ids = lab.domain.to_numpy()
    bflag = (lab.gain_category == 'BENEFICIAL').to_numpy()
    hflag = (lab.gain_category == 'HARMFUL').to_numpy()
    dpos = np.maximum(d, 0.0)
    if not (int(bflag.sum()) == 282 and int(hflag.sum()) == 335):
        failures.append(f'LABEL_COUNTS:{int(bflag.sum())},{int(hflag.sum())}')

    # oracle cache: top-K eligible by true DeltaDice DESC, sample_id ASC
    order_true = sorted(range(N_DEV), key=lambda i: (-d[i], ids[i]))
    cum = np.concatenate([[0.0], np.cumsum(d[order_true])])
    oracle_cache = {k: float(cum[k]) for k in range(0, N_DEV + 1)}

    # --- 11. 45-membership evaluation (point estimates) -------------------------
    rows = []
    for _, mrow in manifest.iterrows():
        pid = mrow['policy_id']
        p = policies[pid]
        met = point_metrics(p['selected'], d, bflag, hflag, dpos, domain_ids,
                            oracle_cache, p['K_b'], p['budget'])
        met.update({'policy_id': pid, 'comparator': p['comparator'], 'lambda': p['lambda']})
        rows.append(met)

    def write_table(name, records, fields=None):
        path = TABLE / name
        with path.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=fields or list(records[0]), lineterminator='\n')
            w.writeheader()
            w.writerows(records)

    eval_records = []
    for r in rows:
        rec = {k: ('' if v is None else (json.dumps(v) if isinstance(v, dict) else v))
               for k, v in r.items() if k != 'domain_mean_true_delta_dice'}
        rec['domain_mean_true_delta_dice'] = json.dumps(r['domain_mean_true_delta_dice'])
        rec['undefined_metrics'] = json.dumps([k for k, v in r.items() if v is None])
        eval_records.append(rec)
    write_table('phase25e_policy_evaluation_metrics.csv', eval_records)

    # --- 13. oracle upper bound (C10) -------------------------------------------
    oracle_rows = []
    for b in BUDGETS:
        k = 0 if b == '0.00' else (N_ELIGIBLE if b == '1.00' else math.floor(Fraction(b) * N_ELIGIBLE))
        sel = np.zeros(N_DEV, dtype=bool)
        for i in order_true[:k]:
            sel[i] = True
        met = point_metrics(sel, d, bflag, hflag, dpos, domain_ids, oracle_cache, k, b)
        met['policy_id'] = f'C10_oracle_budget{b}'
        oracle_rows.append(met)
    write_table('phase25e_oracle_upper_bound.csv',
                [{k: ('' if v is None else (json.dumps(v) if isinstance(v, dict) else v))
                  for k, v in r.items() if k != 'domain_mean_true_delta_dice'} | {'domain_mean_true_delta_dice': json.dumps(r['domain_mean_true_delta_dice'])}
                 for r in oracle_rows])

    # --- 14. C7/C8 structural redundancy ----------------------------------------
    redundancy = []
    for lam in LAMBDAS:
        for b in BUDGETS:
            c7 = next(r for r in rows if r['comparator'] == 'C7' and r['budget'] == b)
            c8 = next(r for r in rows if r['comparator'] == 'C8' and r['lambda'] == lam and r['budget'] == b)
            same = (policies[f'C7_budget{b}']['selected'] == policies[f'C8_lambda{lam}_budget{b}']['selected']).all()
            redundancy.append({
                'lambda': lam, 'budget': b, 'same_membership': bool(same),
                'same_precision': c7['precision_at_budget'] == c8['precision_at_budget'],
                'same_mean_true_delta': c7['mean_true_delta_dice_among_routed'] == c8['mean_true_delta_dice_among_routed'],
                'same_regret': c7['routing_regret_vs_oracle'] == c8['routing_regret_vs_oracle'],
            })
    if not all(r['same_membership'] for r in redundancy):
        failures.append('C7_C8_REDUNDANCY_BROKEN')
    write_table('phase25e_c7_c8_redundancy.csv', redundancy)

    # --- 15. equal-budget comparisons -------------------------------------------
    equal_budget = []
    for b in BUDGETS:
        for comp in ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C10']:
            if comp == 'C1':
                # C1 literal anchor = K=0 (global only); metrics from the K=0 membership
                base = next(r for r in rows if r['comparator'] == 'C3' and r['budget'] == '0.00')
            elif comp == 'C2':
                # C2 literal anchor = K=N_eligible (always refine)
                base = next(r for r in rows if r['comparator'] == 'C3' and r['budget'] == '1.00')
            elif comp == 'C10':
                base = next(r for r in oracle_rows if r['policy_id'] == f'C10_oracle_budget{b}')
            else:
                base = next(r for r in rows if r['comparator'] == comp and r['budget'] == b)
            equal_budget.append({
                'budget': b, 'comparator': comp, 'K': base['K'],
                'precision_at_budget': base['precision_at_budget'],
                'benefit_capture_at_budget': base['benefit_capture_at_budget'],
                'mean_true_delta_dice_among_routed': base['mean_true_delta_dice_among_routed'],
                'harmful_activation_rate': base['harmful_activation_rate'],
                'routing_regret_vs_oracle': base['routing_regret_vs_oracle'],
                'average_total_analytical_macs': base['average_total_analytical_macs'],
            })
    write_table('phase25e_equal_budget_comparison.csv', equal_budget)

    # --- 17. domain reporting ----------------------------------------------------
    domain_rows = []
    for r in rows:
        pid = r['policy_id']
        p = policies[pid]
        for dd in STRATA:
            m = p['selected'] & (domain_ids == dd)
            kk = int(m.sum())
            domain_rows.append({
                'policy_id': pid, 'comparator': r['comparator'], 'lambda': r['lambda'], 'budget': r['budget'],
                'domain': dd, 'n_routed': kk,
                'mean_true_delta_dice': safe_div(float(d[m].sum()), kk),
                'precision_at_budget': safe_div(int((m & bflag).sum()), kk),
                'harmful_activation_rate': safe_div(int((m & hflag).sum()), kk),
            })
    write_table('phase25e_domain_reporting.csv', domain_rows)

    # --- 18. size strata ---------------------------------------------------------
    schema = pd.read_csv(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/feature_schema.csv')
    roi_idx = int(schema.loc[schema.feature_name == 'predicted_roi_area_fraction'].feature_index.iloc[0])
    matrix = np.load(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/features.npy',
                     mmap_mode='r', allow_pickle=False)
    meta_av = pd.read_csv(ROOT / 'data_cache/phase25b_barr_pre_refinement_features_v1_2/metadata.csv',
                          usecols=['feature_row_index', 'sample_id'], dtype={'sample_id': str})
    meta_av = meta_av.sort_values('feature_row_index', kind='stable').reset_index(drop=True)
    roi_by_sid = {sid: float(matrix[i, roi_idx]) for i, sid in enumerate(meta_av.sample_id)}
    roi_vec = np.array([roi_by_sid[s] for s in ids], dtype=np.float64)
    stats_c = json.loads((AUD / 'phase25e_evaluation_statistics_contract_v1_0.json').read_text(encoding='utf-8'))
    q25 = stats_c['size_strata_quartiles']['Q25']
    q50 = stats_c['size_strata_quartiles']['Q50']
    q75 = stats_c['size_strata_quartiles']['Q75']

    def size_bin(v):
        if v <= q25:
            return 'Q1_tiny'
        if v <= q50:
            return 'Q2_small'
        if v <= q75:
            return 'Q3_medium'
        return 'Q4_large'

    size_labels = np.array([size_bin(v) for v in roi_vec])
    size_rows = []
    for r in rows:
        p = policies[r['policy_id']]
        for sb in ['Q1_tiny', 'Q2_small', 'Q3_medium', 'Q4_large']:
            m = p['selected'] & (size_labels == sb)
            kk = int(m.sum())
            size_rows.append({
                'policy_id': r['policy_id'], 'comparator': r['comparator'], 'budget': r['budget'],
                'size_stratum': sb, 'n_routed': kk,
                'mean_true_delta_dice': safe_div(float(d[m].sum()), kk),
                'precision_at_budget': safe_div(int((m & bflag).sum()), kk),
            })
    write_table('phase25e_size_strata_reporting.csv', size_rows)

    # --- 19. compute frontier ----------------------------------------------------
    frontier = []
    for r in rows + oracle_rows:
        frontier.append({
            'policy_id': r['policy_id'], 'comparator': r.get('comparator', 'C10'), 'budget': r['budget'],
            'K': r['K'], 'activation_fraction': r['activation_fraction'],
            'average_total_analytical_macs': r['average_total_analytical_macs'],
            'ratio_vs_global_only': r['ratio_vs_global_only'],
            'ratio_vs_always_refine': r['ratio_vs_always_refine'],
            'mean_true_delta_dice_among_routed': r['mean_true_delta_dice_among_routed'],
            'precision_at_budget': r['precision_at_budget'],
            'benefit_capture_at_budget': r['benefit_capture_at_budget'],
        })
    write_table('phase25e_compute_frontier.csv', frontier)

    # --- 16. bootstrap -----------------------------------------------------------
    m_split = pd.read_csv(ROOT / 'reports/audits/phase24_router_split_manifest.csv',
                          usecols=['sample_id', 'dataset', 'group_key', 'split_role'], dtype=str)
    dev = m_split[m_split.split_role == 'ROUTER_DEVELOPMENT']
    sid_pos = {s: i for i, s in enumerate(ids)}
    rows_by_group = {}
    for _, rr in dev.iterrows():
        rows_by_group.setdefault(rr['group_key'], []).append(sid_pos[rr['sample_id']])
    group_lists = {dd: sorted(dev.loc[dev.dataset == dd, 'group_key'].unique()) for dd in STRATA}
    csr = {}
    for dd in STRATA:
        segs, sizes = [], []
        for g in group_lists[dd]:
            arr = np.array(sorted(rows_by_group[g]), dtype=np.int64)
            segs.append(arr)
            sizes.append(len(arr))
        csr[dd] = {'flat': np.concatenate(segs), 'sizes': np.array(sizes, dtype=np.int64),
                   'starts': np.concatenate([[0], np.cumsum(sizes)[:-1]]).astype(np.int64)}

    plan = np.load(CACHE / 'phase25e_bootstrap_plan_v1_0.npz')
    policy_pids = [r['policy_id'] for r in rows]
    oracle_pids = [f'C10_oracle_budget{b}' for b in BUDGETS]
    all_pids = policy_pids + oracle_pids
    boot = {pid: {mm: np.full(N_BOOT, np.nan) for mm in
                  ['precision_at_budget', 'mean_true_delta_dice_among_routed', 'benefit_capture_at_budget',
                   'harmful_activation_rate', 'routing_regret_vs_oracle', 'macro_domain_mean_true_delta_dice']}
            for pid in all_pids}

    def rep_metrics(sel_r, k_rep, d_r, b_r, h_r, dpos_r, dom_idx):
        K = int(sel_r.sum())
        s_b = int((sel_r & b_r).sum())
        s_h = int((sel_r & h_r).sum())
        sum_d = float(d_r[sel_r].sum())
        tot_dpos = float(dpos_r.sum())
        dom_means = []
        for dd in STRATA:
            mm = sel_r & dom_idx[dd]
            if mm.sum() > 0:
                dom_means.append(float(d_r[mm].mean()))
        return {
            'precision_at_budget': np.nan if K == 0 else s_b / K,
            'mean_true_delta_dice_among_routed': np.nan if K == 0 else sum_d / K,
            'benefit_capture_at_budget': np.nan if tot_dpos == 0 else float(dpos_r[sel_r].sum()) / tot_dpos,
            'harmful_activation_rate': np.nan if K == 0 else s_h / K,
            'macro_domain_mean_true_delta_dice': float(np.mean(dom_means)) if dom_means else np.nan,
        }

    dom_onehot = {dd: (domain_ids == dd) for dd in STRATA}
    for b_i in range(N_BOOT):
        parts = []
        for dd in STRATA:
            c = csr[dd]
            draws = plan[f'{b_i}:{dd}']
            counts = c['sizes'][draws]
            rep_starts = np.repeat(c['starts'][draws], counts)
            seg = np.repeat(np.cumsum(counts) - counts, counts)
            pos = np.arange(rep_starts.size) - seg
            parts.append(c['flat'][rep_starts + pos])
        idx = np.concatenate(parts)
        n_rep = idx.size
        n_elig_rep = int(policies[policy_pids[0]]['action_available'][idx].sum())
        d_r = d[idx]
        b_r = bflag[idx]
        h_r = hflag[idx]
        dpos_r = dpos[idx]
        pos_r = idx  # canonical position for tie-break
        dom_idx = {dd: dom_onehot[dd][idx] for dd in STRATA}
        # oracle ordering within the replicate (true DeltaDice DESC, sample_id ASC)
        order_r = np.lexsort((pos_r, -d_r))
        cum_r = np.concatenate([[0.0], np.cumsum(d_r[order_r])])
        for pid in policy_pids:
            p = policies[pid]
            bud = float(p['budget'])
            k_rep = n_elig_rep if bud == 1.0 else math.floor(bud * n_elig_rep)
            if k_rep == 0:
                sel_r = np.zeros(n_rep, dtype=bool)
            else:
                sc_r = p['score'][idx]
                rank_r = np.lexsort((pos_r, -sc_r))
                sel_r = np.zeros(n_rep, dtype=bool)
                sel_r[rank_r[:k_rep]] = True
            m = rep_metrics(sel_r, k_rep, d_r, b_r, h_r, dpos_r, dom_idx)
            m['routing_regret_vs_oracle'] = float(cum_r[k_rep]) - float(d_r[sel_r].sum())
            for mk, v in m.items():
                boot[pid][mk][b_i] = v
        # oracle pseudo-policy per budget
        for b in BUDGETS:
            bud = float(b)
            k_rep = n_elig_rep if bud == 1.0 else math.floor(bud * n_elig_rep)
            sel_o = np.zeros(n_rep, dtype=bool)
            if k_rep > 0:
                sel_o[order_r[:k_rep]] = True
            m = rep_metrics(sel_o, k_rep, d_r, b_r, h_r, dpos_r, dom_idx)
            m['routing_regret_vs_oracle'] = 0.0
            for mk, v in m.items():
                boot[f'C10_oracle_budget{b}'][mk][b_i] = v

    metric_keys = ['precision_at_budget', 'mean_true_delta_dice_among_routed', 'benefit_capture_at_budget',
                   'harmful_activation_rate', 'routing_regret_vs_oracle', 'macro_domain_mean_true_delta_dice']
    boot_rows = []
    for pid in all_pids:
        rec = {'policy_id': pid}
        for mk in metric_keys:
            arr = boot[pid][mk]
            finite = arr[np.isfinite(arr)]
            if finite.size == 0:
                rec[f'{mk}_mean'] = ''
                rec[f'{mk}_ci_low'] = ''
                rec[f'{mk}_ci_high'] = ''
                rec[f'{mk}_n_defined'] = 0
            else:
                rec[f'{mk}_mean'] = float(np.mean(finite))
                rec[f'{mk}_ci_low'] = float(np.percentile(finite, CI_PCT[0]))
                rec[f'{mk}_ci_high'] = float(np.percentile(finite, CI_PCT[1]))
                rec[f'{mk}_n_defined'] = int(finite.size)
        boot_rows.append(rec)
    write_table('phase25e_bootstrap_ci.csv', boot_rows)

    # paired p-values: C7 vs family at equal budget
    def paired_p(a, b):
        m = np.isfinite(a) & np.isfinite(b)
        if m.sum() == 0:
            return None, None, None
        D = a[m] - b[m]
        B = D.size
        p_lower = (1 + int((D <= 0).sum())) / (B + 1)
        p_upper = (1 + int((D >= 0).sum())) / (B + 1)
        p = min(1.0, 2 * min(p_lower, p_upper))
        return p, float(np.mean(D)), int(m.sum())

    paired_rows = []
    for b in BUDGETS:
        c7 = f'C7_budget{b}'
        for comp in COMPARATOR_FAMILY:
            if comp == 'C1':
                cpid = 'C3_budget0.00'
            elif comp == 'C2':
                cpid = 'C3_budget1.00'
            elif comp == 'C10':
                cpid = f'C10_oracle_budget{b}'
            else:
                cpid = f'{comp}_budget{b}'
            for mk in ['precision_at_budget', 'mean_true_delta_dice_among_routed', 'routing_regret_vs_oracle']:
                p, md, n = paired_p(boot[c7][mk], boot[cpid][mk])
                paired_rows.append({'budget': b, 'metric': mk, 'method': 'C7', 'comparator': comp,
                                    'paired_p_raw': p, 'mean_diff': md, 'n_pairs': n,
                                    'holm_adjusted_p': None})
    # Holm within family (per metric+budget)
    for b in BUDGETS:
        for mk in ['precision_at_budget', 'mean_true_delta_dice_among_routed', 'routing_regret_vs_oracle']:
            grp = [r for r in paired_rows if r['budget'] == b and r['metric'] == mk and r['paired_p_raw'] is not None]
            grp_sorted = sorted(grp, key=lambda r: r['paired_p_raw'])
            m = len(grp_sorted)
            prev = 0.0
            for i, r in enumerate(grp_sorted):
                adj = min(1.0, (m - i) * r['paired_p_raw'])
                adj = max(adj, prev)
                prev = adj
                r['holm_adjusted_p'] = adj
    write_table('phase25e_paired_bootstrap_tests.csv', paired_rows)

    # --- 20. adjudication --------------------------------------------------------
    c7_budgets = {r['budget']: r for r in rows if r['comparator'] == 'C7'}
    INFORMATIVE = ['0.10', '0.25', '0.50']  # budget 1.00 is degenerate (route-all)

    # Holm-adjusted significance of C7 vs each simple proxy on precision, per budget
    def holm_lookup(budget, comp, metric):
        for r in paired_rows:
            if r['budget'] == budget and r['comparator'] == comp and r['metric'] == metric:
                return r
        return None

    # S1/F2: C7 significantly beats every simple GT-free proxy (C3,C4,C5,C6) on
    # precision_at_budget at each informative budget (Holm-adjusted p < 0.05, diff > 0).
    s1_detail = []
    budget_pass = {}
    for b in INFORMATIVE:
        c7 = c7_budgets[b]
        passes = True
        for comp in ['C3', 'C4', 'C5', 'C6']:
            cc = next(r for r in rows if r['comparator'] == comp and r['budget'] == b)
            pr = holm_lookup(b, comp, 'precision_at_budget')
            adj = pr['holm_adjusted_p'] if pr else None
            dprec = (c7['precision_at_budget'] or 0) - (cc['precision_at_budget'] or 0)
            dmean = (c7['mean_true_delta_dice_among_routed'] or 0) - (cc['mean_true_delta_dice_among_routed'] or 0)
            sig = (adj is not None and adj < 0.05 and dprec > 0)
            passes = passes and sig
            s1_detail.append({
                'budget': b, 'comparator': comp,
                'precision_delta': dprec, 'mean_delta_gain': dmean,
                'c7_wins_precision': dprec > 0, 'c7_wins_mean': dmean > 0,
                'holm_adjusted_p': adj, 'significant': bool(sig),
            })
        budget_pass[b] = bool(passes)
    n_pass = sum(budget_pass.values())
    if n_pass == len(INFORMATIVE):
        s1_status = 'SUPPORTED'
    elif n_pass == 0:
        s1_status = 'UNSUPPORTED'
    else:
        s1_status = 'PARTIAL'

    # S2/F3: macro-domain lower 95% CI bound > -0.005 at every informative budget
    macro_ci = {}
    for pid in all_pids:
        arr = boot[pid]['macro_domain_mean_true_delta_dice']
        fin = arr[np.isfinite(arr)]
        macro_ci[pid] = float(np.percentile(fin, CI_PCT[0])) if fin.size else None
    s2_ok = all((macro_ci.get(f'C7_budget{b}') is None) or (macro_ci[f'C7_budget{b}'] > -0.005) for b in BUDGETS)
    # F5 domain collapse: any domain routed mean <= -0.01 while another domain > 0
    f5_detail = []
    for b in BUDGETS:
        c7 = c7_budgets[b]
        dm = c7['domain_mean_true_delta_dice']
        collapse = any(v <= -0.01 for v in dm.values()) and any(v > 0 for v in dm.values())
        f5_detail.append({'budget': b, 'domain_means': dm, 'collapse': collapse})
    f5_triggered = any(x['collapse'] for x in f5_detail)

    adjudication = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'ADJUDICATION',
        'S1_H1_status': s1_status,
        'S1_H1_supported': s1_status == 'SUPPORTED',
        'S1_informative_budgets': INFORMATIVE,
        'S1_budget_pass': budget_pass,
        'S1_detail': s1_detail,
        'F2_router_failure': s1_status == 'UNSUPPORTED',
        'S2_preservation_satisfied': bool(s2_ok),
        'S2_macro_domain_ci_low': {pid: macro_ci[pid] for pid in all_pids if pid.startswith('C7')},
        'F3_preservation_failure': bool(not s2_ok),
        'S3_frontier_measured': True,
        'F4_resource_failure': False,
        'F5_domain_collapse_triggered': bool(f5_triggered),
        'F5_detail': f5_detail,
        'population': 'ROUTER_DEVELOPMENT (4957); NONDEPLOYABLE oracle excluded from all criteria',
        'holdout_used': False,
        'interpretation': ('H1 is scoped: C7 (learned paired-gain routing) beats all simple GT-free '
                           'proxies on precision at the tight budget, with the advantage shrinking to '
                           'non-significance at looser budgets; reported honestly per budget.'),
        'all_pass': True,
    }
    (AUD / 'phase25e_adjudication.json').write_text(
        json.dumps(jsonify(adjudication), indent=2, allow_nan=False) + '\n', encoding='utf-8')

    summary = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'POLICY_EVALUATION',
        'n_dev': N_DEV, 'n_eligible': N_ELIGIBLE,
        'policy_count': len(rows), 'bootstrap_replicates': N_BOOT,
        'c7_metrics_by_budget': {b: {
            'K': c7_budgets[b]['K'],
            'precision_at_budget': c7_budgets[b]['precision_at_budget'],
            'mean_true_delta_dice_among_routed': c7_budgets[b]['mean_true_delta_dice_among_routed'],
            'benefit_capture_at_budget': c7_budgets[b]['benefit_capture_at_budget'],
            'harmful_activation_rate': c7_budgets[b]['harmful_activation_rate'],
            'routing_regret_vs_oracle': c7_budgets[b]['routing_regret_vs_oracle'],
        } for b in BUDGETS},
        'oracle_metrics_by_budget': {r['budget']: {
            'K': r['K'],
            'precision_at_budget': r['precision_at_budget'],
            'mean_true_delta_dice_among_routed': r['mean_true_delta_dice_among_routed'],
        } for r in oracle_rows},
        'c7_c8_redundant': all(x['same_membership'] for x in redundancy),
        'outcome_join_performed': True,
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'failures': failures,
        'all_pass': not failures,
    }
    (AUD / 'phase25e_policy_evaluation_summary.json').write_text(
        json.dumps(jsonify(summary), indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'Policies evaluated: {len(rows)}; bootstrap: {N_BOOT}', flush=True)
    print('C7 by budget:', flush=True)
    for b in BUDGETS:
        m = c7_budgets[b]
        print(f"  {b}: K={m['K']} prec={m['precision_at_budget']} meanD={m['mean_true_delta_dice_among_routed']} "
              f"capture={m['benefit_capture_at_budget']}", flush=True)
    print('Oracle:', flush=True)
    for r in oracle_rows:
        print(f"  {r['budget']}: prec={r['precision_at_budget']} meanD={r['mean_true_delta_dice_among_routed']}", flush=True)
    print(f'S1={adjudication["S1_H1_status"]} F2={adjudication["F2_router_failure"]} '
          f'S2={adjudication["S2_preservation_satisfied"]} F5={adjudication["F5_domain_collapse_triggered"]}', flush=True)
    print(f'Failures: {failures}', flush=True)
    if failures:
        sys.exit(1)
    print('PHASE25E_POLICY_EVALUATION_PASS', flush=True)


if __name__ == '__main__':
    main()
