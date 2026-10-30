"""Build + execute notebooks/phasewise/post_phase14_h3_proposal_supply/07_h3_adjudication.ipynb.

28 required sections, Tables A-F, figures A-G, full assertion suite.
Artifact-driven: reads saved artifacts only. No training, no inference, no TEST access.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply" / "07_h3_adjudication.ipynb"
NB_PATH.parent.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))
cells = []

cells.append(md(r"""
# 07 — Formal H3 Adjudication (Target-Support Redesign)

**Scope.** This is the FINAL adjudication of the already-completed H3
`A_TARGET_SUPPORT_REDESIGN` intervention against the prospectively frozen H3
criteria. It is a **disk-only** adjudication: no training, no inference, no new
experiment, no TEST access, no threshold/checkpoint/gate change.

**Predecessor state:** `H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`

**This notebook produces the frozen scientific verdict — it does not create one.**
The verdict is read from the prospectively frozen criteria artifact and applied to
the authoritative observed values.

**Governance.** TEST and external TEST remain CLOSED. Phase 15 remains
`NOT_STARTED_AND_NOT_AUTHORIZED`. Options B and C are future-only and are NOT
started here.
"""))

# ── 1 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 1. Scope and governance"))
cells.append(code(r"""
import json, hashlib, sys
from fractions import Fraction
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('D:/Softfors/jup')
AUDITS = ROOT / 'reports' / 'audits'
TABLES = ROOT / 'reports' / 'tables'
FIGDIR = ROOT / 'reports' / 'figures' / 'h3_adjudication'
FIGDIR.mkdir(parents=True, exist_ok=True)

def load(p): return json.loads((ROOT / p).read_text(encoding='utf-8'))
def sha(p):
    h = hashlib.sha256()
    with open(ROOT / p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''): h.update(c)
    return h.hexdigest()

ADJ = load('reports/audits/h3_formal_adjudication.json')
print('adjudication artifact :', ADJ['artifact'])
print('status                :', ADJ['status'])
print('scientific label      :', ADJ['scientific_label'])
print('adjudication sha256   :', sha('reports/audits/h3_formal_adjudication.json'))
print()
print('This notebook performs no training, no inference and no TEST access.')
"""))

# ── 2 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 2. H3 scientific question"))
cells.append(code(r"""
q = ADJ['scientific_question']
for k in ['axis', 'intervention_family', 'mechanistic_hypothesis', 'frozen_mapping']:
    print(f'{k:26s}: {q[k]}')
print(f"{'A_ref (authoritative)':26s}: {q['A_ref_authoritative']}")
print()
print(q['A_ref_note'])
"""))

# ── 3 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 3. Frozen intervention"))
cells.append(code(r"""
proto = load('reports/audits/h3_proposal_supply_design_protocol.json')
print('design status       :', proto['design_status'])
print('selected axis       :', proto['selected_axis'])
print('priority rule fired :', proto['axis_priority_rule_fired'])
print('intervention        :', proto['intervention']['selected_option'])
print()
print(proto['intervention']['definition'])
"""))

# ── 4 ───────────────────────────────────────────────────────────────────────
cells.append(md(r"""
## 4. H3 evidence chain

### Table A — H3 evidence timeline
"""))
cells.append(code(r"""
chain = [
    ('01 root cause', 'reports/audits/phase14_diag_root_cause.json', 'COMPLETE', 'F_MIXED_BOTTLENECK'),
    ('02 axis priority', 'reports/audits/post_phase14_h3_axis_priority_results.json', 'COMPLETE', 'A_PRIORITY (R_A=1.0, R_C=0.0)'),
    ('03 design/binding', 'reports/audits/h3_proposal_supply_final_pretraining_binding_v2.json', 'COMPLETE', 'H3_FINAL_PRETRAINING_BINDING_COMPLETE'),
    ('04 training', 'reports/audits/h3_proposal_supply_training_closure.json', 'COMPLETE', 'best epoch 54; replay PASS'),
    ('05 supply', 'reports/audits/h3_supply_axis_evaluation.json', 'COMPLETE', 'zero-prop GT 79->27; TINY 57->22'),
    ('05b reconciliation', 'reports/audits/h3_supply_axis_metric_domain_reconciliation.json', 'RECONCILED', 'proxy -0.60 INVALID for formal use'),
    ('06 downstream', 'reports/audits/h3_downstream_evaluation.json', 'COMPLETE', 'TinyRecall_H3 59/72; R_H3 2/15'),
    ('06b correction', 'reports/audits/h3_downstream_metric_domain_correction.json', 'CORRECTED', 'detection domain formal'),
    ('07 adjudication', 'reports/audits/h3_formal_adjudication.json', 'COMPLETE', 'H3_SUPPLY_REDESIGN_INSUFFICIENT'),
]
rows = []
for step, path, state, key in chain:
    rows.append({'step': step, 'artifact': Path(path).name, 'state': state,
                 'key result': key, 'sha256': (sha(path)[:16] + '...') if (ROOT / path).exists() else 'MISSING'})
display(pd.DataFrame(rows))
"""))

# ── 5 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 5. Selected checkpoint binding"))
cells.append(code(r"""
sc = ADJ['selected_checkpoint']
print('experiment id      :', ADJ['experiment_id'])
print('path               :', sc['path'])
print('sha256             :', sc['sha256'])
print('expected sha256    :', sc['sha256_expected'])
print('sha matches        :', sc['sha256_matches_expected'])
print('selected epoch     :', sc['selected_epoch'])
print('heatmap resolution :', sc['heatmap_resolution'])
print('replay verdict     :', ADJ['checkpoint_selection_replay_verdict'])
print('closure status     :', ADJ['training_closure_status'])
"""))

# ── 6 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 6. Trainer multi-SHA provenance"))
cells.append(code(r"""
tl = ADJ['provenance_caveats']['trainer_lineage']
for k in ['design_era_trainer', 'epochs_1_2_trainer', 'epochs_3_69_trainer']:
    print(f'{k:20s}: {tl[k]}')
print()
print(tl['note'])
print('single-SHA claim   :', tl['single_sha_claim'])
print('classification     :', tl['classification'])
"""))

# ── 7 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 7. Frozen success criteria\n\n### Table B — Frozen criteria"))
cells.append(code(r"""
fc = ADJ['frozen_criteria']; cr = ADJ['criterion_results']
tb = pd.DataFrame([
    {'criterion': 'A', 'frozen threshold': fc['criterion_A']['rule'],
     'observed': cr['criterion_A']['observed'], 'result': cr['criterion_A']['result'],
     'role': 'NECESSARY (supply)'},
    {'criterion': 'B', 'frozen threshold': fc['criterion_B']['rule'],
     'observed': cr['criterion_B']['observed'], 'result': cr['criterion_B']['result'],
     'role': 'NECESSARY (supply)'},
    {'criterion': 'C', 'frozen threshold': fc['criterion_C']['rule'],
     'observed': f"{ADJ['observed']['formal_R_H3']:.10f}", 'result': cr['criterion_C']['result'],
     'role': 'ADJUDICATION GATE (downstream)'},
])
display(tb)
print('contamination policy:', fc['contamination'])
"""))

# ── 8 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 8. Frozen failure boundary\n\n### Table C — Failure boundary"))
cells.append(code(r"""
fb = ADJ['failure_boundary']
tc = pd.DataFrame([
    {'clause': '1', 'rule': fb['clause_1']['rule'], 'observed': fb['clause_1']['observed'],
     'fired': fb['clause_1']['fired']},
    {'clause': '2', 'rule': fb['clause_2']['rule'], 'observed': f"{fb['clause_2']['observed']:.10f}",
     'fired': fb['clause_2']['fired']},
])
display(tc)
print('overall failure fired:', fb['fired'])
print('intermediate zone    :', fb['intermediate_zone_active'])
"""))

# ── 9 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 9. Supply Criterion A"))
cells.append(code(r"""
o = ADJ['observed']
print(f"PRE-H3 zero-proposal TINY : {o['pre_h3_zero_proposal_tiny']}/{72}")
print(f"H3     zero-proposal TINY : {o['zero_proposal_tiny']}/72")
print(f"TINY components recovered : {o['tiny_supply_recovered']}")
print()
print(f"Criterion A: zero_proposal_TINY <= 20/72  ->  observed {o['zero_proposal_tiny']}/72  ->  {ADJ['criterion_results']['criterion_A']['result']}")
"""))

# ── 10 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 10. Supply Criterion B"))
cells.append(code(r"""
print(f"PRE-H3 zero-proposal GT   : {o['pre_h3_zero_proposal_gt']}/152")
print(f"H3     zero-proposal GT   : {o['zero_proposal_gt']}/152")
print(f"GT components recovered   : {o['gt_supply_recovered']}")
print()
print(f"Criterion B: zero_proposal_GT <= 35/152  ->  observed {o['zero_proposal_gt']}/152  ->  {ADJ['criterion_results']['criterion_B']['result']}")
"""))

# ── 11 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 11. Combined supply result"))
cells.append(code(r"""
print('Combined primary supply result:', ADJ['criterion_results']['combined_primary_supply_result'])
print('Criterion A:', ADJ['criterion_results']['criterion_A']['result'])
print('Criterion B:', ADJ['criterion_results']['criterion_B']['result'])
print()
print('The primary supply criteria are NECESSARY but NOT sufficient alone;')
print('the downstream R_H3 is the adjudication gate.')
"""))

# ── 12 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 12. Proposal-domain metric reconciliation\n\n### Table E — Metric-domain reconciliation"))
cells.append(code(r"""
ps = ADJ['proxy_and_sensitivity_status']
te = pd.DataFrame([
    {'quantity': 'H3_PROPOSAL_TINY_COVERAGE90', 'domain': 'PROPOSAL_LOCALIZER',
     'value': ps['proposal_domain_proxy']['value'], 'formal?': 'NO',
     'status': ps['proposal_domain_proxy']['status']},
    {'quantity': 'proxy R_H3 (proposal domain)', 'domain': 'PROPOSAL_LOCALIZER',
     'value': ps['proposal_domain_proxy']['proxy_R_H3'], 'formal?': 'NO',
     'status': 'LOCALIZER-ONLY PROXY - NOT FORMAL DOWNSTREAM R_H3'},
    {'quantity': 'strict cov90 TinyRecall', 'domain': 'SEGMENTATION (strict >=90%)',
     'value': ps['strict_cov90_sensitivity']['TinyRecall_H3_cov90'], 'formal?': 'NO',
     'status': ps['strict_cov90_sensitivity']['status']},
    {'quantity': 'formal TinyRecall_H3', 'domain': 'DETECTION (overlap >=1px)',
     'value': ADJ['observed']['formal_TinyRecall_H3'], 'formal?': 'YES',
     'status': 'FROZEN FORMAL DOMAIN'},
    {'quantity': 'formal R_H3', 'domain': 'DETECTION (overlap >=1px)',
     'value': ADJ['observed']['formal_R_H3'], 'formal?': 'YES',
     'status': 'FROZEN FORMAL GATE'},
])
display(te)
"""))

# ── 13 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 13. Downstream metric-domain reconciliation"))
cells.append(code(r"""
corr = load('reports/audits/h3_downstream_metric_domain_correction.json')
print('nature     :', corr['nature'])
print('as-run     :', corr['defect']['asrun_metric'], '->', corr['defect']['consequence_in_asrun'])
print('frozen     :', corr['defect']['frozen_metric'])
print('authority  :', corr['defect']['frozen_authority'])
print()
print('corrected formal:', json.dumps(corr['corrected_formal'], indent=2))
"""))

# ── 14 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 14. Formal downstream TinyRecall_H3"))
cells.append(code(r"""
print('formal TinyRecall_H3 :', ADJ['observed']['formal_TinyRecall_H3'])
print('fraction             :', ADJ['observed']['formal_TinyRecall_H3_fraction'])
print('metric domain        :', ADJ['observed']['metric_domain'])
"""))

# ── 15 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 15. Formal R_H3"))
cells.append(code(r"""
o = ADJ['observed']
print(f"Tg = {o['formal_Tg']:.16f}  ({o['formal_Tg_fraction']})")
print(f"G  = {o['formal_G']:.16f}  ({o['formal_G_fraction']})")
print(f"TinyRecall_H3 = {o['formal_TinyRecall_H3']:.16f}")
print()
print(f"R_H3 = (TinyRecall_H3 - Tg) / G = {o['formal_R_H3']:.16f}  ({o['formal_R_H3_fraction']})")
print(f"re-derived                     = {o['formal_R_H3_rederived']:.16f}")
print('interpretation band            :', o['R_H3_band'])
"""))

# ── 16 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 16. Clause-by-clause success table"))
cells.append(code(r"""
sc = ADJ['frozen_criteria']; cr = ADJ['criterion_results']
display(pd.DataFrame([
    {'success clause': 'A', 'requirement': sc['criterion_A']['rule'], 'observed': cr['criterion_A']['observed'], 'met?': cr['criterion_A']['result']},
    {'success clause': 'B', 'requirement': sc['criterion_B']['rule'], 'observed': cr['criterion_B']['observed'], 'met?': cr['criterion_B']['result']},
    {'success clause': 'C', 'requirement': sc['criterion_C']['rule'], 'observed': f"{ADJ['observed']['formal_R_H3']:.6f}", 'met?': cr['criterion_C']['result']},
]))
print('formal success (ALL clauses):', cr['formal_success'])
"""))

# ── 17 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 17. Clause-by-clause failure table"))
cells.append(code(r"""
fb = ADJ['failure_boundary']
display(pd.DataFrame([
    {'failure clause': '1', 'rule': fb['clause_1']['rule'], 'observed': fb['clause_1']['observed'], 'fired?': fb['clause_1']['fired']},
    {'failure clause': '2', 'rule': fb['clause_2']['rule'], 'observed': f"{fb['clause_2']['observed']:.10f}", 'fired?': fb['clause_2']['fired']},
]))
print('failure boundary overall FIRED:', fb['fired'])
print('frozen failure label          :', fb['label'])
"""))

# ── 18 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 18. Supporting advanced metrics (DESCRIPTIVE ONLY)"))
cells.append(code(r"""
pol = ADJ['post_hoc_supporting_metrics_policy']
for k, v in pol.items():
    print(f'{k:20s}: {v}')
print()
backfill = load('reports/audits/project_evaluation_metrics_backfill.json')
summ = pd.read_csv(TABLES / 'project_evaluation_segmentation_summary.csv')
h3 = summ[summ['arm'] == 'H3_DOWNSTREAM'].iloc[0]
cols = ['arm', 'pooled_dice', 'pooled_iou', 'pooled_precision', 'pooled_recall', 'pooled_specificity',
        'pooled_mcc', 'image_mean_hd95', 'image_mean_assd', 'image_mean_surface_dice',
        'brier', 'ece', 'roc_auc', 'average_precision']
display(summ[summ['arm'] == 'H3_DOWNSTREAM'][cols])
print('These metrics are SUPPORTING EVIDENCE ONLY and do NOT change the formal verdict.')
"""))

# ── 19 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 19. Oracle / GLOBAL / PREDICTED / H3 comparison\n\n### Table D — Main arm comparison"))
cells.append(code(r"""
ct = load('reports/audits/h3_downstream_evaluation.json')['contrast_table']
ARM_KEYS = [('GLOBAL', 'GLOBAL'), ('PREDICTED', 'PREDICTED_REGIONAL'),
            ('H3', 'H3_DOWNSTREAM'), ('ORACLE_REGIONAL', 'ORACLE_REGIONAL')]
rows = []
for key, label in ARM_KEYS:
    d = ct[key]
    rows.append({'arm': label, 'mean_dice': d['mean_dice'], 'median_dice': d['median_dice'],
                 'tiny_recall90_det': d['tiny_recall90_det'],
                 'hard_tiny_recovered': f"{d['hard_tiny_recovered']}/15",
                 'fp_components_per_image': d['mean_fp_components_per_image']})
display(pd.DataFrame(rows).round(6))
print('ORACLE_REGIONAL is a DIAGNOSTIC UPPER BOUND (GT bboxes), not deployable performance.')
"""))

# ── 20 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 20. What improved"))
cells.append(code(r"""
for s in ADJ['scientific_interpretation']['improved']:
    print(' -', s)
"""))

# ── 21 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 21. What remained insufficient"))
cells.append(code(r"""
for s in ADJ['scientific_interpretation']['insufficient']:
    print(' -', s)
"""))

# ── 22 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 22. Formal H3 verdict"))
cells.append(code(r"""
print('FROZEN SCIENTIFIC LABEL:', ADJ['final_frozen_H3_label'])
print()
print(ADJ['scientific_interpretation']['statement'])
print()
print('This verdict is the prospectively frozen rule applied to the authoritative observed values.')
print('It is NOT converted into PASS / PARTIAL SUCCESS / NEAR PASS / PROMOTE.')
"""))

# ── 23 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 23. Regional-gate implication"))
cells.append(code(r"""
rh = ADJ['regional_hypothesis_preserved']
for k, v in rh.items():
    print(f'{k:46s}: {v}')
"""))

# ── 24 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 24. Phase-15 lock"))
cells.append(code(r"""
print('Phase-15 status:', ADJ['governance']['phase_15_status'])
print()
print('The frozen criteria specify that when the H3 failure boundary fires:')
print('  - the target-support redesign is insufficient;')
print('  - Phase 15 remains NOT_STARTED_AND_NOT_AUTHORIZED;')
print('  - the H3 checkpoint must NOT be promoted as the solved deployable regional localizer;')
print('  - further localizer work requires fresh authorization.')
"""))

# ── 25 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 25. TEST lock"))
cells.append(code(r"""
g = ADJ['governance']
print('TEST reads          :', g['test_reads'])
print('external TEST reads :', g['external_test_reads'])
print('TEST status         : CLOSED')
"""))

# ── 26 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 26. Future options (NOT AUTHORIZED)"))
cells.append(code(r"""
fo = ADJ['recommended_governance_next_state']['future_options']
for k, v in fo.items():
    print(f'{k:46s}: {v}')
print()
print('Option B and Option C are FUTURE OPTIONS ONLY. They are NOT implemented or trained here.')
"""))

# ── 27 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 27. Complete provenance table\n\n### Table F — Provenance"))
cells.append(code(r"""
rows = []
for name, rel in ADJ['evidence_chain_sha256'].items():
    rows.append({'artifact': name, 'path': rel if rel.endswith(('.json', '.csv', '.yaml', '.pt')) else rel,
                 'sha256': rel, 'role': 'EVIDENCE_CHAIN'})
prov = pd.DataFrame([{'artifact': k, 'sha256': v} for k, v in ADJ['evidence_chain_sha256'].items()])
prov['exists'] = prov['sha256'] != 'MISSING'
display(prov)
print()
print('adjudication artifact sha256:', sha('reports/audits/h3_formal_adjudication.json'))
"""))

# ── 28 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 28. Final terminal state"))
cells.append(code(r"""
print('adjudication state :', ADJ['status'])
print('scientific label   :', ADJ['scientific_label'])
print()
print('H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED')
"""))

# ── Figures ─────────────────────────────────────────────────────────────────
cells.append(md(r"""
## Figures (saved data only, no model forward pass)

### Figure A — Supply improvement (zero-proposal GT / TINY, PRE-H3 vs H3)
"""))
cells.append(code(r"""
o = ADJ['observed']
fig, ax = plt.subplots(figsize=(8, 4.6))
x = np.arange(2); w = 0.36
pre = [o['pre_h3_zero_proposal_gt'], o['pre_h3_zero_proposal_tiny']]
post = [o['zero_proposal_gt'], o['zero_proposal_tiny']]
ax.bar(x - w/2, pre, w, label='PRE-H3', color='#95a5a6')
ax.bar(x + w/2, post, w, label='H3', color='#2980b9')
for i, (a, b) in enumerate(zip(pre, post)):
    ax.text(i - w/2, a + 1, str(a), ha='center', fontsize=10)
    ax.text(i + w/2, b + 1, str(b), ha='center', fontsize=10)
ax.set_xticks(x); ax.set_xticklabels(['zero-proposal GT (of 152)', 'zero-proposal TINY (of 72)'])
ax.set_ylabel('count'); ax.set_title('H3 supply improvement (descriptive)'); ax.legend()
plt.tight_layout(); p = FIGDIR / 'figA_supply_improvement.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

cells.append(md("### Figure B — Formal Tiny Recall across arms"))
cells.append(code(r"""
ct = load('reports/audits/h3_downstream_evaluation.json')['contrast_table']
ARM_KEYS = [('GLOBAL', 'GLOBAL'), ('PREDICTED', 'PREDICTED_REGIONAL'),
            ('H3', 'H3_DOWNSTREAM'), ('ORACLE_REGIONAL', 'ORACLE_REGIONAL')]
arms = [label for _, label in ARM_KEYS]
vals = [ct[key]['tiny_recall90_det'] for key, _ in ARM_KEYS]
fig, ax = plt.subplots(figsize=(8.5, 4.6))
bars = ax.bar(arms, vals, color=['#7f8c8d', '#e67e22', '#2980b9', '#27ae60'])
ax.axhline(ADJ['observed']['formal_Tg'], color='black', ls='--', lw=1, label=f"Tg={ADJ['observed']['formal_Tg']:.4f}")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 0.01, f'{v:.4f}', ha='center', fontsize=9)
ax.set_ylim(0, 1.08); ax.set_ylabel('TINY recall (detection domain)')
ax.set_title('Formal Tiny Recall by arm (detection: overlap >= 1 px)'); ax.legend()
plt.tight_layout(); p = FIGDIR / 'figB_tiny_recall_by_arm.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

cells.append(md("### Figure C — Formal R_H3 gauge"))
cells.append(code(r"""
R = ADJ['observed']['formal_R_H3']
fig, ax = plt.subplots(figsize=(9, 3.4))
ax.axvspan(-1.6, 0.15, color='#f5b7b1', alpha=0.6, label='insufficient (< 0.15)')
ax.axvspan(0.15, 0.30, color='#fdebd0', alpha=0.8, label='intermediate [0.15, 0.30)')
ax.axvspan(0.30, 1.2, color='#abebc6', alpha=0.6, label='success (>= 0.30)')
ax.axvline(R, color='red', lw=3)
ax.text(R, 0.55, f'R_H3 = {R:.4f}', color='red', ha='center', fontsize=11, fontweight='bold')
ax.axvline(0.15, color='black', ls='--', lw=1); ax.axvline(0.30, color='black', ls='--', lw=1)
ax.set_xlim(-1.6, 1.2); ax.set_yticks([]); ax.set_xlabel('formal R_H3')
ax.set_title('Formal R_H3 against the frozen thresholds (0.15 / 0.30)'); ax.legend(fontsize=8, loc='upper left')
plt.tight_layout(); p = FIGDIR / 'figC_rh3_gauge.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

cells.append(md("### Figure D — Success-gate panel"))
cells.append(code(r"""
cr = ADJ['criterion_results']
gates = ['Criterion A\n(TINY <= 20/72)', 'Criterion B\n(GT <= 35/152)', 'Criterion C\n(R_H3 >= 0.30)']
res = [cr['criterion_A']['result'], cr['criterion_B']['result'], cr['criterion_C']['result']]
fig, ax = plt.subplots(figsize=(8, 4.2))
colors = ['#27ae60' if r == 'PASS' else '#c0392b' for r in res]
ax.bar(gates, [1, 1, 1], color=colors)
for i, r in enumerate(res):
    ax.text(i, 0.5, r, ha='center', va='center', color='white', fontsize=13, fontweight='bold')
ax.set_yticks([]); ax.set_title('Frozen success-gate panel (ALL clauses required)')
plt.tight_layout(); p = FIGDIR / 'figD_success_gates.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

cells.append(md("### Figure E — Failure-boundary panel"))
cells.append(code(r"""
fb = ADJ['failure_boundary']
cl = ['Clause 1\nTINY >= 45/72', 'Clause 2\nR_H3 < 0.15']
fired = [fb['clause_1']['fired'], fb['clause_2']['fired']]
fig, ax = plt.subplots(figsize=(7.5, 4.2))
ax.bar(cl, [1, 1], color=['#27ae60' if not f else '#c0392b' for f in fired])
for i, f in enumerate(fired):
    ax.text(i, 0.5, 'FIRED' if f else 'not fired', ha='center', va='center', color='white', fontsize=12, fontweight='bold')
ax.set_yticks([]); ax.set_title(f"Frozen failure boundary (overall FIRED = {fb['fired']})")
plt.tight_layout(); p = FIGDIR / 'figE_failure_boundary.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

cells.append(md("### Figure F — Downstream Dice comparison (descriptive only)"))
cells.append(code(r"""
ct = load('reports/audits/h3_downstream_evaluation.json')['contrast_table']
ARM_KEYS = [('GLOBAL', 'GLOBAL'), ('PREDICTED', 'PREDICTED_REGIONAL'),
            ('H3', 'H3_DOWNSTREAM'), ('ORACLE_REGIONAL', 'ORACLE_REGIONAL')]
arms = [label for _, label in ARM_KEYS]
dice = [ct[key]['mean_dice'] for key, _ in ARM_KEYS]
fig, ax = plt.subplots(figsize=(8.5, 4.6))
bars = ax.bar(arms, dice, color=['#7f8c8d', '#e67e22', '#2980b9', '#27ae60'])
for b, v in zip(bars, dice):
    ax.text(b.get_x() + b.get_width()/2, v + 0.01, f'{v:.4f}', ha='center', fontsize=9)
ax.set_ylabel('mean Dice'); ax.set_ylim(0, 0.95)
ax.set_title('Mean Dice by arm (DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE)')
plt.tight_layout(); p = FIGDIR / 'figF_dice_by_arm.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

cells.append(md("### Figure G — Evidence-flow / decision diagram"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(11, 6.2))
ax.axis('off')
steps = [
    (0.5, 0.92, 'Root cause: F_MIXED_BOTTLENECK'),
    (0.5, 0.78, 'Axis priority: A_PRIORITY (R_A=1.0, R_C=0.0)'),
    (0.5, 0.64, 'H3 design: size-adaptive target support (A_ref=13.0)'),
    (0.5, 0.50, 'H3 training: 69 ep, best epoch 54, replay PASS'),
    (0.5, 0.36, 'Supply: zero-prop TINY 57->22 (A FAIL) / GT 79->27 (B PASS)'),
    (0.5, 0.22, 'Downstream: TinyRecall_H3 59/72 -> R_H3 = 2/15'),
]
for x, y, t in steps:
    ax.add_patch(plt.Rectangle((0.1, y - 0.05), 0.8, 0.1, facecolor='#d6eaf8', edgecolor='#2874a6'))
    ax.text(x, y, t, ha='center', va='center', fontsize=10)
    if y > 0.22:
        ax.annotate('', xy=(0.5, y - 0.06), xytext=(0.5, y - 0.10),
                    arrowprops=dict(arrowstyle='-|>', color='#2874a6'))
ax.add_patch(plt.Rectangle((0.1, 0.03), 0.8, 0.1, facecolor='#f5b7b1', edgecolor='#c0392b'))
ax.text(0.5, 0.08, 'VERDICT: H3_SUPPLY_REDESIGN_INSUFFICIENT (failure boundary FIRED)',
        ha='center', va='center', fontsize=10, fontweight='bold')
ax.set_title('H3 evidence flow and decision path')
plt.tight_layout(); p = FIGDIR / 'figG_evidence_flow.png'
plt.savefig(str(p), dpi=150, bbox_inches='tight'); plt.show(); print('saved', p.name)
"""))

# ── Assertions ──────────────────────────────────────────────────────────────
cells.append(md("## Assertions"))
cells.append(code(r"""
# ── Checkpoint binding ───────────────────────────────────────────────────────
assert ADJ['selected_checkpoint']['selected_epoch'] == 54
assert ADJ['selected_checkpoint']['sha256'] == 'd875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e'
assert ADJ['selected_checkpoint']['sha256_matches_expected'] is True
assert ADJ['checkpoint_selection_replay_verdict'] == 'H3_CHECKPOINT_SELECTION_REPLAY_PASS'

# ── Supply values from the frozen supply artifact ────────────────────────────
sup = load('reports/audits/h3_supply_axis_evaluation.json')
assert sup['primary_criteria']['criterion_a']['value'] == 22
assert sup['primary_criteria']['criterion_b']['value'] == 27
assert ADJ['observed']['zero_proposal_tiny'] == 22
assert ADJ['observed']['zero_proposal_gt'] == 27

# ── Criteria results ─────────────────────────────────────────────────────────
assert ADJ['criterion_results']['criterion_A']['result'] == 'FAIL'
assert ADJ['criterion_results']['criterion_B']['result'] == 'PASS'
assert ADJ['criterion_results']['combined_primary_supply_result'] == 'FAIL'

# ── Formal downstream metric domain ─────────────────────────────────────────
assert abs(ADJ['observed']['formal_TinyRecall_H3'] - 59/72) < 1e-12
assert abs(ADJ['observed']['formal_R_H3'] - 2/15) < 1e-12
assert ADJ['observed']['formal_R_H3'] < 0.15
assert 'DETECTION' in ADJ['observed']['metric_domain'].upper()

# ── Proxy and strict-cov90 are NOT formal ────────────────────────────────────
assert ADJ['proxy_and_sensitivity_status']['proposal_domain_proxy']['status'] == 'INVALID_FOR_FORMAL_ADJUDICATION__PROPOSAL_DOMAIN_ONLY'
assert ADJ['proxy_and_sensitivity_status']['strict_cov90_sensitivity']['status'] == 'DESCRIPTIVE_SENSITIVITY_ONLY__NOT_FORMAL_H3_GATE'

# ── Failure boundary and frozen label ────────────────────────────────────────
assert ADJ['failure_boundary']['clause_1']['fired'] is False
assert ADJ['failure_boundary']['clause_2']['fired'] is True
assert ADJ['failure_boundary']['fired'] is True
assert ADJ['final_frozen_H3_label'] == 'H3_SUPPLY_REDESIGN_INSUFFICIENT'
assert ADJ['scientific_label'] == 'H3_SUPPLY_REDESIGN_INSUFFICIENT'

# ── Governance ───────────────────────────────────────────────────────────────
g = ADJ['governance']
assert g['test_reads'] == 0
assert g['external_test_reads'] == 0
assert g['training_runs_this_task'] == 0
assert g['inference_runs_this_task'] == 0
assert g['checkpoint_changed'] is False
assert g['threshold_changed'] is False
assert g['frozen_gate_changed'] is False
assert g['phase_15_status'] == 'NOT_STARTED_AND_NOT_AUTHORIZED'
assert g['phase_15_status'] != 'STARTED'
assert g['option_b_started'] is False
assert g['option_c_started'] is False

# ── Verdict is not softened ──────────────────────────────────────────────────
assert ADJ['final_frozen_H3_label'] not in ('PASS', 'PARTIAL_SUCCESS', 'NEAR_PASS', 'PROMOTE')

print('✓ All H3 formal adjudication assertions passed.')
print('FROZEN LABEL: H3_SUPPLY_REDESIGN_INSUFFICIENT')
print('State: H3_FORMAL_ADJUDICATION_COMPLETE__TARGET_SUPPORT_INSUFFICIENT__PHASE15_LOCKED')
"""))

nb = nbformat.v4.new_notebook(cells=cells)
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=900,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()
# Normalize volatile execution artifacts so the notebook SHA-256 is a stable content address:
#   (1) drop per-cell execution timing metadata;
#   (2) coalesce adjacent stream outputs (ZMQ may split one stdout burst into several chunks).
for _c in nb.cells:
    if isinstance(_c.get("metadata"), dict):
        _c["metadata"].pop("execution", None)
    _outs = _c.get("outputs")
    if _outs:
        _merged = []
        for _o in _outs:
            if (_o.get("output_type") == "stream" and _merged
                    and _merged[-1].get("output_type") == "stream"
                    and _merged[-1].get("name") == _o.get("name")):
                _p = _merged[-1]
                _pt, _ct = _p.get("text", ""), _o.get("text", "")
                if isinstance(_pt, list):
                    _pt = "".join(_pt)
                if isinstance(_ct, list):
                    _ct = "".join(_ct)
                _p["text"] = _pt + _ct
            else:
                _merged.append(_o)
        _c["outputs"] = _merged
nbformat.write(nb, str(NB_PATH))

errors = 0
for i, c in enumerate(nb.cells):
    if c.cell_type == "code":
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                errors += 1
                print(f"  ERROR cell {i}: {o.get('ename')}: {o.get('evalue')}")
counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
mono = all(counts[i] == i + 1 for i in range(len(counts)))
md_n = sum(1 for c in nb.cells if c.cell_type == "markdown")
print(f"Cells: {len(nb.cells)} | markdown: {md_n} | code: {len(counts)}")
print(f"Zero tracebacks: {'PASS' if errors == 0 else 'FAIL'}")
print(f"Monotonic exec counts (1..{len(counts)}): {'PASS' if mono else 'CHECK'}")
print("Notebook 07 SHA:", hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
