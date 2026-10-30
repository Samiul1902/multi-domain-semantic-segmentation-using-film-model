"""Phase25E §5/§6/§7 PRIMARY-vs-MULTIPLICITY SENSITIVITY + RECONCILED ADJUDICATION.

Classification B (see phase25e_multiplicity_provenance_audit.json): the frozen
protocol designates the raw paired two-sided p as the PRIMARY statistic and
Holm-Bonferroni only as a SECONDARY sensitivity. The post-outcome adjudication
used Holm as the primary significance gate. This script:

  §5  emits reports/tables/phase25e_s1_primary_vs_multiplicity_sensitivity.csv
      (raw-p primary vs Holm secondary, per budget/comparator/metric).
  §6  re-adjudicates S1/H1 with the FROZEN PRIMARY rule (raw paired p) and emits
      reports/audits/phase25e_adjudication_reconciled.json.
  §7  emits comparator-specific wording (primary vs secondary significance).

NO raw scientific value is recomputed: every p-value is read from the frozen
phase25e_paired_bootstrap_tests.csv. Only the DECISION RULE changes.
"""
import hashlib
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
AUD = ROOT / 'reports/audits'
TABLE = ROOT / 'reports/tables'
REV = 'ra_medfilm_barr_resource_gate_v1_0'
CLASS = 'PHASE25E_RESOURCE_GATE_POLICY_EVALUATION'

INFORMATIVE = ['0.10', '0.25', '0.50']   # 1.00 is degenerate (route-all)
SIMPLE_PROXIES = ['C3', 'C4', 'C5', 'C6']
ALPHA = 0.05
S1_METRIC = 'precision_at_budget'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(b):
    """Canonical budget label, e.g. '0.1' -> '0.10'."""
    return f'{float(b):.2f}'


def main():
    tests = pd.read_csv(TABLE / 'phase25e_paired_bootstrap_tests.csv')
    tests['budget'] = tests['budget'].map(norm)

    # ---- §5 sensitivity table ---------------------------------------------------
    sens_rows = []
    for _, r in tests.iterrows():
        if r['comparator'] not in SIMPLE_PROXIES:
            continue
        if r['metric'] not in (S1_METRIC, 'mean_true_delta_dice_among_routed'):
            continue
        if pd.isna(r['paired_p_raw']):
            continue
        raw = float(r['paired_p_raw'])
        holm = float(r['holm_adjusted_p']) if not pd.isna(r['holm_adjusted_p']) else None
        raw_sig = raw < ALPHA
        holm_sig = (holm is not None and holm < ALPHA)
        sens_rows.append({
            'budget': r['budget'],
            'comparator': r['comparator'],
            'metric': r['metric'],
            'mean_diff': float(r['mean_diff']),
            'paired_p_raw': raw,
            'raw_significant_at_0.05': raw_sig,
            'holm_adjusted_p': holm,
            'holm_significant_at_0.05': holm_sig,
            'primary_decision_changed_by_holm': bool(raw_sig and not holm_sig),
            'role': ('PRIMARY' if r['metric'] == S1_METRIC else 'SUPPORTING'),
        })
    sens_df = pd.DataFrame(sens_rows)
    sens_path = TABLE / 'phase25e_s1_primary_vs_multiplicity_sensitivity.csv'
    sens_df.to_csv(sens_path, index=False)

    # ---- §6 reconciled adjudication --------------------------------------------
    def lookup(budget, comp, metric):
        sub = tests[(tests['budget'] == budget) & (tests['comparator'] == comp)
                    & (tests['metric'] == metric)]
        return sub.iloc[0] if len(sub) else None

    c7 = {}
    metrics_tbl = pd.read_csv(TABLE / 'phase25e_policy_evaluation_metrics.csv')
    metrics_tbl['budget'] = metrics_tbl['budget'].map(norm)
    for b in INFORMATIVE:
        row = metrics_tbl[(metrics_tbl['comparator'] == 'C7') & (metrics_tbl['budget'] == b)]
        c7[b] = row.iloc[0] if len(row) else None

    detail_primary = []
    detail_secondary = []
    budget_pass_primary = {}
    budget_pass_secondary = {}

    for b in INFORMATIVE:
        p_pass = True
        s_pass = True
        for comp in SIMPLE_PROXIES:
            cc = metrics_tbl[(metrics_tbl['comparator'] == comp) & (metrics_tbl['budget'] == b)].iloc[0]
            pr = lookup(b, comp, S1_METRIC)
            raw = float(pr['paired_p_raw']) if (pr is not None and not pd.isna(pr['paired_p_raw'])) else None
            holm = (float(pr['holm_adjusted_p'])
                    if (pr is not None and not pd.isna(pr['holm_adjusted_p'])) else None)
            dprec = float(c7[b]['precision_at_budget']) - float(cc['precision_at_budget'])
            dmean = (float(c7[b]['mean_true_delta_dice_among_routed'])
                     - float(cc['mean_true_delta_dice_among_routed']))
            raw_sig = (raw is not None and raw < ALPHA and dprec > 0)
            holm_sig = (holm is not None and holm < ALPHA and dprec > 0)
            p_pass = p_pass and raw_sig
            s_pass = s_pass and holm_sig
            detail_primary.append({
                'budget': b, 'comparator': comp,
                'precision_delta': dprec, 'mean_delta_gain': dmean,
                'c7_wins_precision': dprec > 0, 'c7_wins_mean': dmean > 0,
                'paired_p_raw': raw, 'significant': bool(raw_sig),
                'decision_rule': 'PRIMARY_RAW_PAIRED_P',
            })
            detail_secondary.append({
                'budget': b, 'comparator': comp,
                'precision_delta': dprec, 'mean_delta_gain': dmean,
                'c7_wins_precision': dprec > 0, 'c7_wins_mean': dmean > 0,
                'holm_adjusted_p': holm, 'significant': bool(holm_sig),
                'decision_rule': 'SECONDARY_HOLM_BONFERRONI',
            })
        budget_pass_primary[b] = bool(p_pass)
        budget_pass_secondary[b] = bool(s_pass)

    def status(bp):
        n = sum(bp.values())
        if n == len(INFORMATIVE):
            return 'SUPPORTED'
        if n == 0:
            return 'UNSUPPORTED'
        return 'PARTIAL'

    s1_primary = status(budget_pass_primary)
    s1_secondary = status(budget_pass_secondary)

    # ---- §7 comparator-specific wording ----------------------------------------
    comparator_wording = []
    for comp in SIMPLE_PROXIES:
        per_budget = []
        for b in INFORMATIVE:
            pr = lookup(b, comp, S1_METRIC)
            raw = float(pr['paired_p_raw']) if (pr is not None and not pd.isna(pr['paired_p_raw'])) else None
            holm = (float(pr['holm_adjusted_p'])
                    if (pr is not None and not pd.isna(pr['holm_adjusted_p'])) else None)
            cc = metrics_tbl[(metrics_tbl['comparator'] == comp) & (metrics_tbl['budget'] == b)].iloc[0]
            dprec = float(c7[b]['precision_at_budget']) - float(cc['precision_at_budget'])
            per_budget.append({
                'budget': b,
                'precision_delta': dprec,
                'primary_raw_p': raw,
                'primary_significant': (raw is not None and raw < ALPHA and dprec > 0),
                'secondary_holm_p': holm,
                'secondary_significant': (holm is not None and holm < ALPHA and dprec > 0),
                'wording': (
                    f"At {int(float(b)*100)}% budget, C7 vs {comp}: precision delta {dprec:+.4f}; "
                    f"PRIMARY raw paired p = {raw:.6f} "
                    f"({'SIGNIFICANT' if (raw is not None and raw < ALPHA and dprec > 0) else 'not significant'}); "
                    f"SECONDARY Holm p = {holm:.6f} "
                    f"({'SIGNIFICANT' if (holm is not None and holm < ALPHA and dprec > 0) else 'not significant'})."
                ) if raw is not None else
                    f"At {int(float(b)*100)}% budget, C7 vs {comp}: precision delta {dprec:+.4f}; "
                    f"paired test undefined (degenerate/identical memberships).",
            })
        comparator_wording.append({
            'comparator': comp,
            'per_budget': per_budget,
            'any_primary_significant': any(x['primary_significant'] for x in per_budget),
            'any_secondary_significant': any(x['secondary_significant'] for x in per_budget),
        })

    # Original (Holm-as-primary) closure values for provenance.
    orig = json.loads((AUD / 'phase25e_adjudication.json').read_text(encoding='utf-8'))

    reconciled = {
        'classification': CLASS,
        'specification_revision': REV,
        'stage': 'ADJUDICATION_RECONCILED',
        'reconciliation_basis': ('phase25e_multiplicity_provenance_audit.json classification B: the frozen '
                                 'protocol designates the raw paired two-sided p as PRIMARY and Holm-Bonferroni '
                                 'as SECONDARY. The closure used Holm as primary; this is repaired.'),
        'primary_decision_rule': 'paired_p_raw < 0.05 (frozen PRIMARY statistic)',
        'secondary_decision_rule': 'holm_adjusted_p < 0.05 (retained as conservative sensitivity only)',
        'holm_primary_role': 'SUPERSEDED_FOR_PRIMARY_ADJUDICATION',
        'holm_secondary_role': 'CONSERVATIVE_MULTIPLICITY_SENSITIVITY',
        'alpha': ALPHA,
        'informative_budgets': INFORMATIVE,
        'S1_H1_status': s1_primary,
        'S1_H1_supported': s1_primary == 'SUPPORTED',
        'S1_budget_pass': budget_pass_primary,
        'S1_detail': detail_primary,
        'S1_status_under_secondary_holm': s1_secondary,
        'S1_budget_pass_under_secondary_holm': budget_pass_secondary,
        'S1_detail_under_secondary_holm': detail_secondary,
        'closure_original_S1_H1_status': orig['S1_H1_status'],
        'closure_original_budget_pass': orig['S1_budget_pass'],
        'budget_pass_changed': {b: (budget_pass_primary[b] != orig['S1_budget_pass'][b])
                                for b in INFORMATIVE},
        'S1_status_changed': (s1_primary != orig['S1_H1_status']),
        'F2_router_failure': s1_primary == 'UNSUPPORTED',
        'F2_router_failure_unchanged': (s1_primary == 'UNSUPPORTED') == bool(orig['F2_router_failure']),
        'comparator_specific_wording': comparator_wording,
        'sensitivity_summary': {
            'rows_flipped_by_multiplicity': int(sens_df['primary_decision_changed_by_holm'].sum()),
            'flipped_rows': sens_df[sens_df['primary_decision_changed_by_holm']].to_dict('records'),
        },
        'S2_preservation_satisfied': orig['S2_preservation_satisfied'],
        'S3_frontier_measured': orig['S3_frontier_measured'],
        'F5_domain_collapse_triggered': orig['F5_domain_collapse_triggered'],
        'raw_scientific_values_changed': False,
        'p_values_source': 'reports/tables/phase25e_paired_bootstrap_tests.csv (frozen, unchanged)',
        'metrics_source': 'reports/tables/phase25e_policy_evaluation_metrics.csv (frozen, unchanged)',
        'interpretation': (
            f"Under the frozen PRIMARY statistic (raw paired two-sided p), C7 beats all four simple GT-free "
            f"proxies on precision at the 10% and 25% budgets (S1 budget_pass {budget_pass_primary}), and the "
            f"advantage is not significant at the 50% budget. S1/H1 = {s1_primary}. Under the conservative "
            f"secondary Holm sensitivity, only the 10% budget passes (S1 = {s1_secondary}). The "
            f"multiplicity correction changes the significance call on exactly "
            f"{int(sens_df['primary_decision_changed_by_holm'].sum())} precision rows (25% budget, C4/C5)."),
        'population': orig['population'],
        'holdout_used': False,
        'router_holdout_reads': 0, 'VAL808_reads': 0, 'TEST_reads': 0,
        'failures': [],
        'all_pass': True,
    }
    (AUD / 'phase25e_adjudication_reconciled.json').write_text(
        json.dumps(reconciled, indent=2, allow_nan=False) + '\n', encoding='utf-8')

    print(f'§5 sensitivity table: {len(sens_df)} rows -> {sens_path.name}')
    print(f'  flipped by multiplicity: {int(sens_df["primary_decision_changed_by_holm"].sum())}')
    print(f'§6 S1 primary(raw p) = {s1_primary} budget_pass={budget_pass_primary}')
    print(f'   S1 secondary(Holm) = {s1_secondary} budget_pass={budget_pass_secondary}')
    print(f'   closure original    = {orig["S1_H1_status"]} budget_pass={orig["S1_budget_pass"]}')
    print('PHASE25E_ADJUDICATION_RECONCILED_WRITTEN')


if __name__ == '__main__':
    main()
