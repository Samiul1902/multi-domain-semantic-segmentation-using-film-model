"""Build deterministic Phase25E figures (Agg, fixed DPI, no timestamps)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path("D:/Softfors/jup")
TAB = ROOT / "reports/tables"
FIG = ROOT / "reports/figures"
FIG.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({"figure.dpi": 150, "savefig.dpi": 150})

BUDGETS = ['0.00', '0.10', '0.25', '0.50', '1.00']
STRATA = ['BUSI', 'ISIC', 'KUB', 'KVASIR']
COLORS = {'C3': 'gray', 'C4': 'tab:orange', 'C5': 'tab:green', 'C6': 'tab:purple',
          'C7': 'tab:red', 'C8': 'tab:blue', 'C10': 'black'}

eq = pd.read_csv(TAB / 'phase25e_equal_budget_comparison.csv', dtype={'budget': str})
met = pd.read_csv(TAB / 'phase25e_policy_evaluation_metrics.csv', dtype={'budget': str, 'lambda': str})
boot = pd.read_csv(TAB / 'phase25e_bootstrap_ci.csv')
front = pd.read_csv(TAB / 'phase25e_compute_frontier.csv', dtype={'budget': str})
dom = pd.read_csv(TAB / 'phase25e_domain_reporting.csv', dtype={'budget': str})
size = pd.read_csv(TAB / 'phase25e_size_strata_reporting.csv', dtype={'budget': str})
red = pd.read_csv(TAB / 'phase25e_c7_c8_redundancy.csv', dtype={'budget': str, 'lambda': str})
adj = __import__('json').loads((ROOT / 'reports/audits/phase25e_adjudication.json').read_text())


def series(comp, metric):
    sub = eq[eq.comparator == comp].set_index('budget')
    return [float(sub.loc[b, metric]) if b in sub.index and pd.notna(sub.loc[b, metric]) else np.nan for b in BUDGETS]


def line_vs_budget(metric, ylabel, title, fname, comps=('C3', 'C4', 'C5', 'C6', 'C7', 'C10')):
    fig, ax = plt.subplots(figsize=(9, 6))
    x = np.arange(len(BUDGETS))
    for c in comps:
        y = series(c, metric)
        ax.plot(x, y, marker='o', label=c, color=COLORS.get(c))
    ax.set_xticks(x)
    ax.set_xticklabels(BUDGETS)
    ax.set_xlabel('Budget fraction of eligible rows')
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    fig.savefig(FIG / fname, bbox_inches='tight')
    plt.close(fig)


line_vs_budget('precision_at_budget', 'Precision@budget',
               'Phase25E precision@budget vs budget', 'p25e_precision_vs_budget.png')
line_vs_budget('mean_true_delta_dice_among_routed', 'Mean true DeltaDice among routed',
               'Phase25E mean routed gain vs budget', 'p25e_mean_delta_vs_budget.png')
line_vs_budget('benefit_capture_at_budget', 'Benefit capture@budget',
               'Phase25E benefit capture vs budget', 'p25e_benefit_capture_vs_budget.png')
line_vs_budget('harmful_activation_rate', 'Harmful activation rate',
               'Phase25E harmful activation vs budget', 'p25e_harmful_rate_vs_budget.png')

# 5. regret vs budget
fig, ax = plt.subplots(figsize=(9, 6))
x = np.arange(len(BUDGETS))
for c in ('C3', 'C4', 'C5', 'C6', 'C7'):
    y = series(c, 'routing_regret_vs_oracle')
    ax.plot(x, y, marker='o', label=c, color=COLORS.get(c))
ax.set_xticks(x); ax.set_xticklabels(BUDGETS)
ax.set_xlabel('Budget fraction'); ax.set_ylabel('Routing regret vs oracle (sum DeltaDice)')
ax.set_title('Phase25E routing regret vs oracle upper bound'); ax.legend()
fig.savefig(FIG / 'p25e_regret_vs_budget.png', bbox_inches='tight')
plt.close(fig)

# 6. compute frontier
fig, ax = plt.subplots(figsize=(9, 6))
for c in ('C3', 'C4', 'C5', 'C6', 'C7'):
    sub = front[front.comparator == c].sort_values('activation_fraction')
    ax.plot(sub.activation_fraction, sub.mean_true_delta_dice_among_routed, marker='o',
            label=c, color=COLORS.get(c))
sub = front[front.comparator == 'C10'].sort_values('activation_fraction')
ax.plot(sub.activation_fraction, sub.mean_true_delta_dice_among_routed, marker='s',
        linestyle='--', label='C10 oracle (nondeployable)', color='black')
ax.set_xlabel('Activation fraction K / N_DEV')
ax.set_ylabel('Mean true DeltaDice among routed')
ax.set_title('Phase25E accuracy-compute frontier')
ax.legend()
fig.savefig(FIG / 'p25e_compute_frontier.png', bbox_inches='tight')
plt.close(fig)

# 7. domain breakdown at budget 0.10 / 0.25 / 0.50
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
for ax, b in zip(axes, ['0.10', '0.25', '0.50']):
    sub = dom[(dom.comparator == 'C7') & (dom.budget == b)].set_index('domain')
    vals = [float(sub.loc[d, 'mean_true_delta_dice']) if d in sub.index and pd.notna(sub.loc[d, 'mean_true_delta_dice']) else 0.0
            for d in STRATA]
    ax.bar(STRATA, vals, color='steelblue')
    ax.axhline(0, color='black', lw=0.8)
    ax.set_title(f'C7 routed mean DeltaDice by domain (budget {b})')
    ax.set_ylabel('Mean true DeltaDice')
fig.suptitle('Phase25E domain breakdown')
fig.savefig(FIG / 'p25e_domain_breakdown.png', bbox_inches='tight')
plt.close(fig)

# 8. size strata (C7) across budgets
fig, ax = plt.subplots(figsize=(10, 6))
strata_names = ['Q1_tiny', 'Q2_small', 'Q3_medium', 'Q4_large']
x = np.arange(len(strata_names))
width = 0.15
for i, b in enumerate(['0.10', '0.25', '0.50', '1.00']):
    sub = size[(size.comparator == 'C7') & (size.budget == b)].set_index('size_stratum')
    vals = [float(sub.loc[s, 'mean_true_delta_dice']) if s in sub.index and pd.notna(sub.loc[s, 'mean_true_delta_dice']) else 0.0
            for s in strata_names]
    ax.bar(x + i * width, vals, width, label=f'budget {b}')
ax.set_xticks(x + 1.5 * width)
ax.set_xticklabels(strata_names)
ax.set_ylabel('Mean true DeltaDice among routed')
ax.set_title('Phase25E C7 routed gain by GT-free ROI-size stratum')
ax.legend()
fig.savefig(FIG / 'p25e_size_strata.png', bbox_inches='tight')
plt.close(fig)

# 9. bootstrap CI precision (C7 + proxies)
fig, ax = plt.subplots(figsize=(10, 6))
x = np.arange(len(BUDGETS))
for i, c in enumerate(('C3', 'C4', 'C5', 'C6', 'C7')):
    pid = f'{c}_budget'
    lo, hi, mid = [], [], []
    for b in BUDGETS:
        row = boot[boot.policy_id == f'{c}_budget{b}']
        if len(row):
            lo.append(float(row['precision_at_budget_ci_low'].iloc[0]))
            hi.append(float(row['precision_at_budget_ci_high'].iloc[0]))
            mid.append(float(row['precision_at_budget_mean'].iloc[0]))
        else:
            lo.append(np.nan); hi.append(np.nan); mid.append(np.nan)
    ax.errorbar(x + i * 0.04, mid, yerr=[np.array(mid) - np.array(lo), np.array(hi) - np.array(mid)],
                fmt='o', capsize=3, label=c, color=COLORS.get(c))
ax.set_xticks(x); ax.set_xticklabels(BUDGETS)
ax.set_xlabel('Budget fraction'); ax.set_ylabel('Precision@budget (95% CI)')
ax.set_title('Phase25E bootstrap precision@budget with 95% CI')
ax.legend()
fig.savefig(FIG / 'p25e_bootstrap_ci_precision.png', bbox_inches='tight')
plt.close(fig)

# 10. C7/C8 redundancy
fig, ax = plt.subplots(figsize=(9, 5))
lams = ['0.00', '0.25', '0.50', '1.00']
x = np.arange(len(BUDGETS))
for i, lam in enumerate(lams):
    sub = met[(met.comparator == 'C8') & (met['lambda'] == lam)].set_index('budget')
    y = [float(sub.loc[b, 'precision_at_budget']) if b in sub.index and pd.notna(sub.loc[b, 'precision_at_budget']) else np.nan
         for b in BUDGETS]
    ax.plot(x + i * 0.01, y, marker='o', label=f'C8 lambda={lam}', alpha=0.8)
c7 = met[met.comparator == 'C7'].set_index('budget')
ax.plot(x, [float(c7.loc[b, 'precision_at_budget']) if pd.notna(c7.loc[b, 'precision_at_budget']) else np.nan for b in BUDGETS],
        marker='x', linestyle='--', color='black', label='C7')
ax.set_xticks(x); ax.set_xticklabels(BUDGETS)
ax.set_xlabel('Budget fraction'); ax.set_ylabel('Precision@budget')
ax.set_title('Phase25E C7/C8 structural redundancy under constant action cost')
ax.legend()
fig.savefig(FIG / 'p25e_c7_c8_redundancy.png', bbox_inches='tight')
plt.close(fig)

print('All Phase25E figures created.')
