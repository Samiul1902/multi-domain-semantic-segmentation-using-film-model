"""
Phase 05 Part 1E — Closure figure generation.

Generates the four required closure figures into:
  reports/figures/phase05_leakage_audit/closure/

  A. phase05_closure_v2_vs_v3_population.png
  B. phase05_closure_quarantine_breakdown.png
  C. phase05_closure_leakage_gate_matrix.png
  D. phase05_closure_governance_flow.png

NO TEST medical imagery is read or displayed.
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

PROJECT_ROOT = Path(r'D:\Softfors\jup')
OUT = PROJECT_ROOT / 'reports' / 'figures' / 'phase05_leakage_audit' / 'closure'
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'figure.dpi': 130,
    'savefig.dpi': 130,
    'font.size': 10,
    'axes.titlesize': 12,
    'axes.titleweight': 'bold',
    'axes.grid': True,
    'grid.alpha': 0.25,
    'axes.axisbelow': True,
    'figure.facecolor': 'white',
    'axes.facecolor': 'white',
})

# ---------------------------------------------------------------------------
# Figure A — v2 vs canonical-v3 population comparison
# ---------------------------------------------------------------------------
pop = pd.read_csv(PROJECT_ROOT / 'reports/tables/phase05_v3_population_changes.csv')
splits = ['TRAIN', 'VAL', 'TEST', 'QUARANTINED']
v2 = {s: int(pop.loc[pop['split'] == s, 'v2_count'].iloc[0]) for s in splits}
v3 = {s: int(pop.loc[pop['split'] == s, 'v3_count'].iloc[0]) for s in splits}

fig, ax = plt.subplots(figsize=(8.6, 4.6))
x = np.arange(len(splits))
w = 0.36
b1 = ax.bar(x - w / 2, [v2[s] for s in splits], w, label='phase4_v2 (historical)',
            color='#9aa5b1', edgecolor='#5b6673')
b2 = ax.bar(x + w / 2, [v3[s] for s in splits], w, label='phase4_v3 (canonical)',
            color='#2f7ed8', edgecolor='#1c518c')
for bars, vals in ((b1, [v2[s] for s in splits]), (b2, [v3[s] for s in splits])):
    for bar, v in zip(bars, vals):
        ax.annotate(f'{v}', (bar.get_x() + bar.get_width() / 2, v),
                    ha='center', va='bottom', fontsize=9)
ax.set_xticks(x)
ax.set_xticklabels(splits)
ax.set_ylabel('Sample count')
ax.set_title('Phase 05 Closure (A): v2 vs canonical-v3 active population')
ax.legend(frameon=False)
ax.annotate('TEST unchanged\n(byte-identical)', xy=(2, v3['TEST']),
            xytext=(2.35, v3['TEST'] * 0.62), fontsize=9, color='#1c518c',
            arrowprops=dict(arrowstyle='->', color='#1c518c'))
fig.tight_layout()
fig.savefig(OUT / 'phase05_closure_v2_vs_v3_population.png')
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure B — final quarantine breakdown (118)
# ---------------------------------------------------------------------------
q = pd.read_csv(PROJECT_ROOT / 'manifests/phase4_v3/quarantined.csv')
reason_counts = q['quarantine_reason'].value_counts()
labels = [r.replace('QUARANTINED_', '').replace('CONSERVATIVE_', 'CONSERVATIVE ')
          for r in reason_counts.index]
labels = [l.replace('_', ' ').title() for l in labels]
colors = ['#d64545', '#e08a3c', '#e0c33c', '#4a9d5f', '#3c7fa8', '#7a6bb5'][:len(labels)]

fig, ax = plt.subplots(figsize=(9.2, 4.8))
y = np.arange(len(labels))[::-1]
ax.barh(y, reason_counts.values, color=colors, edgecolor='#333', height=0.62)
for yi, v in zip(y, reason_counts.values):
    ax.annotate(f'{v}', (v, yi), xytext=(4, 0), textcoords='offset points',
                va='center', fontsize=9)
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlabel('Quarantined samples')
ax.set_title('Phase 05 Closure (B): final quarantine breakdown (118 development samples)')
ax.set_xlim(0, reason_counts.max() * 1.18)
fig.tight_layout()
fig.savefig(OUT / 'phase05_closure_quarantine_breakdown.png')
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure C — final active leakage-gate matrix
# ---------------------------------------------------------------------------
gates = [
    ('Sample ID disjointness\n(TRAIN/VAL/TEST)', 'PASS'),
    ('KUB patient disjointness', 'PASS'),
    ('BUSI patient-group disjointness\n(recovered)', 'PASS'),
    ('Exact image duplicate\nremediation', 'PASS'),
    ('Exact mask duplicate\n(TRAIN<->VAL)', 'PASS'),
    ('TRAIN<->VAL d0 high-risk\n(ISIC same-acquisition)', 'PASS'),
    ('TRAIN<->VAL d2 conservative\nremediation', 'PASS'),
    ('TEST-linked d<=2 development\nquarantine', 'PASS'),
    ('TEST membership invariance', 'PASS'),
    ('Cross-artifact consistency', 'PASS'),
    ('BUSI provenance\nreconciliation', 'PASS'),
    ('Population accounting\n(8441 conserved)', 'PASS'),
]
fig, ax = plt.subplots(figsize=(9.6, 5.6))
n = len(gates)
ys = np.arange(n)[::-1]
for yi, (label, status) in zip(ys, gates):
    ok = status == 'PASS'
    ax.barh(yi, 1, color='#dff0dc' if ok else '#f8d7da', edgecolor='#4a9d5f' if ok else '#d64545', height=0.7)
    ax.annotate(label, (0.02, yi), va='center', ha='left', fontsize=8.7)
    ax.annotate('PASS' if ok else 'FAIL', (0.98, yi), va='center', ha='right',
                fontsize=9.5, fontweight='bold', color='#2f6b3a' if ok else '#a12626')
ax.set_xlim(0, 1)
ax.set_ylim(-0.7, n - 0.3)
ax.set_yticks([])
ax.set_xticks([])
ax.grid(False)
ax.set_title('Phase 05 Closure (C): final active leakage-gate matrix — v3 canonical')
fig.tight_layout()
fig.savefig(OUT / 'phase05_closure_leakage_gate_matrix.png')
plt.close(fig)

# ---------------------------------------------------------------------------
# Figure D — governance flow: historical-v2 -> remediation -> canonical-v3
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10.4, 4.4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis('off')

def box(x, y, w, h, text, fc, ec, fs=9.5, tc='#1a1a1a'):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
                                boxstyle='round,pad=0.08,rounding_size=0.12',
                                linewidth=1.4, facecolor=fc, edgecolor=ec))
    ax.text(x + w / 2, y + h / 2, text, ha='center', va='center',
            fontsize=fs, color=tc, wrap=True)

box(0.15, 2.15, 2.4, 1.3,
    'HISTORICAL\nphase4_v2\n5913 / 845 / 1683\nKNOWN_SPLIT_CONTAMINATION',
    '#e9edf1', '#5b6673')
box(3.55, 2.15, 2.9, 1.3,
    'PHASE-05 REMEDIATION\nParts 1A-1D-R6\nforensic adjudication +\nleakage-safe reconstruction',
    '#fdf3d8', '#c9a227')
box(7.45, 2.15, 2.4, 1.3,
    'CANONICAL\nphase4_v3\n5832 / 808 / 1683\n+118 quarantined',
    '#dcebfb', '#2f7ed8')

ax.add_patch(FancyArrowPatch((2.6, 2.8), (3.5, 2.8), arrowstyle='-|>',
                             mutation_scale=18, linewidth=1.8, color='#5b6673'))
ax.add_patch(FancyArrowPatch((6.5, 2.8), (7.4, 2.8), arrowstyle='-|>',
                             mutation_scale=18, linewidth=1.8, color='#c9a227'))

box(0.15, 0.35, 9.7, 1.05,
    'GOVERNANCE RULE:  future development uses phase4_v3 only  |  '
    'historical Phases 06-15 retain phase4_v2 provenance  |  TEST locked & byte-identical',
    '#eef7ee', '#4a9d5f', fs=9.2)

ax.set_title('Phase 05 Closure (D): historical-v2 -> remediation -> canonical-v3 governance flow',
             fontsize=12, fontweight='bold', pad=10)
fig.tight_layout()
fig.savefig(OUT / 'phase05_closure_governance_flow.png')
plt.close(fig)

print('Closure figures written to:', OUT)
for p in sorted(OUT.glob('*.png')):
    print(' ', p.name, p.stat().st_size, 'bytes')
