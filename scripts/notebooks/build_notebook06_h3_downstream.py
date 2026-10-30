"""Build + execute Notebook 06 — H3 Frozen Downstream Evaluation.

29 numbered sections, 8 figures (A-H), governance assertions.

Reads only frozen/saved artifacts; performs NO training and NO inference.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply" / "06_h3_downstream_evaluation.ipynb"

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))

cells = []

# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
# Notebook 06 — H3 Frozen Downstream Evaluation

Prospective, single-run frozen downstream evaluation of the selected H3 localizer
(epoch 54) through the frozen Stage-4D proposal policy and the frozen Phase-14
regional refiner (epoch 56), producing the **formal downstream R_H3**.

This notebook performs **no training and no inference**. It reads the frozen
downstream evaluation artifact and its saved per-component / per-image tables,
re-derives all aggregates, and asserts governance invariants.

**Final state:** `H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`
"""))

# ── 1 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 1. Executive Summary"))
cells.append(code(r"""
import json, hashlib, sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path('D:/Softfors/jup')
sys.path.insert(0, str(ROOT))
AUDITS = ROOT / 'reports' / 'audits'
TABLES = ROOT / 'reports' / 'tables'
FIGDIR = ROOT / 'reports' / 'figures'
FIGDIR.mkdir(parents=True, exist_ok=True)

def load_json(p): return json.loads((ROOT / p).read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()

down = load_json('reports/audits/h3_downstream_evaluation.json')
asrun = load_json('reports/audits/h3_downstream_evaluation_v1_asrun.json')
corr = load_json('reports/audits/h3_downstream_metric_domain_correction.json')
binding = load_json('reports/audits/h3_downstream_evaluator_binding.json')
supply = load_json('reports/audits/h3_supply_axis_evaluation.json')
recon = load_json('reports/audits/h3_supply_axis_metric_domain_reconciliation.json')
closure = load_json('reports/audits/h3_proposal_supply_training_closure.json')
replay = load_json('reports/audits/h3_checkpoint_selection_replay.json')

comp_df = pd.read_csv(TABLES / 'h3_downstream_per_component.csv')
img_df = pd.read_csv(TABLES / 'h3_downstream_per_image.csv')
frozen_summary = pd.read_csv(TABLES / 'phase14_clean_v3_mode_summary.csv').set_index('mode')

fd = down['formal_downstream']
print('STATUS                        :', down['status'])
print('TinyRecall_H3 (formal, det)   :', fd['TinyRecall_H3'], '=', fd['TinyRecall_H3_fraction'])
print('Tg / G                        :', fd['Tg'], '/', fd['G'])
print('R_H3 (formal, detection)      :', fd['R_H3'], '->', fd['interpretation_band'])
print('R_H3 (strict cov90 sensitivity):', fd['sensitivity_strict_cov90']['R_H3_cov90'])
print('Formal adjudication performed :', down['formal_adjudication_performed'])
print('TEST reads / external reads   :', down['test_reads'], '/', down['external_test_reads'])
print('Phase 15                      :', down['phase_15_status'])
"""))

# ── 2 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 2. Current Governance State"))
cells.append(code(r"""
rows = [
    ('H3 training (Notebook 04)', closure['status'], f"epochs={closure['total_epochs']} best_epoch={closure['best_epoch']}"),
    ('Checkpoint-selection replay', replay['verdict'], 'deterministic re-derivation'),
    ('H3 supply-axis evaluation (NB05)', supply['status'], 'localizer/proposal supply only'),
    ('NB05 metric-domain reconciliation', recon['status'], 'proxy relabelled; downstream R_H3 was PENDING'),
    ('H3 downstream evaluation (NB06)', down['status'], 'this notebook'),
    ('Formal H3 adjudication (NB07)', 'NOT_STARTED', 'requires separate supervisor authorization'),
    ('Phase 15', down['phase_15_status'], 'not authorized'),
    ('TEST split', 'CLOSED', '0 content reads'),
]
display(pd.DataFrame(rows, columns=['item', 'state', 'detail']))
print('Notebook 06 is the frozen downstream evaluation record. It is NOT the formal adjudication.')
"""))

# ── 3 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 3. H3 Checkpoint Binding"))
cells.append(code(r"""
ck = down['selected_h3_checkpoint']
ck_path = ROOT / ck['path']
ck_sha_disk = hashlib.sha256(ck_path.read_bytes()).hexdigest()
print('path            :', ck['path'])
print('selected epoch  :', ck['selected_epoch'])
print('heatmap res     :', ck['heatmap_resolution'])
print('construction    :', ck['construction'])
print('sha (artifact)  :', ck['sha256'])
print('sha (disk)      :', ck_sha_disk)
print('match           :', ck_sha_disk == ck['sha256'])
print()
print('refiner :', down['refiner_checkpoint']['sha256'], 'epoch', down['refiner_checkpoint']['epoch'])
print('global  :', down['global_checkpoint']['sha256'])
"""))

# ── 4 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 4. Frozen Downstream Pipeline Definition"))
cells.append(code(r"""
pipeline = [
    'H3 localizer (epoch 54) -> 128-space heatmap (heatmap_resolution=128)',
    'frozen Stage-4D proposal policy: threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30',
    'Phase-14 regional refiner (epoch 56) applied per proposal crop (256)',
    'MAX-probability replacement inside the proposal union (aggregate_and_fuse)',
    'FULL_FIELD segmentation at threshold 0.50',
    'per-component / per-size downstream metrics',
    'formal R_H3 = (TinyRecall_H3 - Tg) / G',
]
for i, step in enumerate(pipeline, 1):
    print(f'{i}. {step}')
print()
print('fusion semantics :', down['evaluator_binding']['fusion_semantics'])
print('fusion threshold :', down['evaluator_binding']['final_fusion_threshold'])
print('global threshold :', down['evaluator_binding']['global_threshold'])
print('proposal configs evaluated:', down['proposal_configurations_evaluated'])
"""))

# ── 5 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 5. Frozen Proposal Policy"))
cells.append(code(r"""
policy = down['frozen_proposal_policy']
print('frozen proposal policy:', policy)
assert policy == {'threshold': 0.10, 'margin': 0.20, 'top_k': 5, 'nms_iou': 0.30}
print('Exactly ONE policy was evaluated (no search):', down['proposal_configurations_evaluated'] == 1)
"""))

# ── 6 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 6. Refiner & Fusion Rules"))
cells.append(code(r"""
print('refiner checkpoint epoch :', down['refiner_checkpoint']['epoch'])
print('refiner crop target size :', down['evaluator_binding']['refiner_crop_target_size'])
print('fusion                   :', down['evaluator_binding']['fusion_semantics'])
print('final fusion threshold   :', down['evaluator_binding']['final_fusion_threshold'])
print()
print('These are byte-identical to the bound Phase-14 clean-v3 evaluator; only the')
print('localizer checkpoint (and its training-faithful 128 heatmap construction) changed.')
"""))

# ── 7 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 7. Evaluator Prospective Binding"))
cells.append(code(r"""
eb = binding['evaluator']
print('binding status      :', binding['status'])
print('evaluator path      :', eb['path'])
print('evaluator sha (bind):', eb['sha256'])
print('evaluator sha (disk):', sha(eb['path']))
print('binding intact      :', sha(eb['path']) == eb['sha256'])
print()
print('bound checkpoints   :', json.dumps(binding['bound_checkpoints'], indent=1))
print('h3_heatmap_resolution:', binding['h3_heatmap_resolution'])
print('formal_R_H3_source  :', binding['formal_R_H3_source'])
print()
print('NOTE: the binding recorded the metric as', repr(binding['metric_definitions']['downstream_recall90']))
print('      which is the strict-coverage definition. Section 11 reconciles the domain.')
"""))

# ── 8 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 8. Reused Frozen References"))
cells.append(code(r"""
ref = down['frozen_references']
print('Frozen downstream references:', ref)
gref = load_json('reports/audits/phase14_clean_v3_global_reference_freeze.json')
print()
print('GLOBAL reference freeze status:', gref['status'])
print('Tg definition (authoritative) :', gref['derivation']['Tg_definition'])
print('Dg definition                 :', gref['derivation']['Dg_definition'])
print()
print('GLOBAL / PREDICTED / ORACLE rows are REUSED verbatim from')
print('reports/tables/phase14_clean_v3_mode_summary.csv (frozen Phase-14 artifact).')
"""))

# ── 9 ───────────────────────────────────────────────────────────────────────
cells.append(md("## 9. Evaluation Population"))
cells.append(code(r"""
pop = down['population']
print('population:', json.dumps(pop, indent=1))
print()
print('per-component table rows :', len(comp_df))
print('per-image table rows     :', len(img_df))
print('size stratum counts      :', comp_df['size_stratum'].value_counts().to_dict())
"""))

# ── 10 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 10. Primary Downstream Metric Definition"))
cells.append(code(r"""
pm = down['primary_metric_definition']
print('name              :', pm['name'])
print('frozen domain     :', pm['frozen_domain'])
print('formal value      :', pm['formal_TinyRecall_H3'], '=', pm['formal_TinyRecall_H3_fraction'])
print()
print('definition        :', pm['definition'])
print()
print('explicitly NOT    :', pm['not_the_proposal_coverage'])
"""))

# ── 11 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 11. Metric-Domain Reconciliation (cov90 vs detection)"))
cells.append(code(r"""
mdc = down['metric_domain_correction']
print('correction nature :', mdc['nature'])
print('inference re-run  :', mdc['inference_rerun'])
print()
print('AUTHORITATIVE SOURCE:')
print('  ', mdc['authoritative_source']['path'])
print('  ', mdc['authoritative_source']['Tg_definition'])
print('  ', mdc['authoritative_source']['numeric_confirmation'])
print()
print('DEFECT ORIGIN:')
print('  ', mdc['defect_origin'])
print()
print('WHY DETECTION IS FORMAL:')
print('  ', mdc['why_detection_is_formal'])
print()
print('AS-RUN (superseded) artifact:')
asr = mdc['asrun_artifact_preserved']
print('   path  :', asr['path'])
print('   R_H3  :', asr['formal_R_H3_asrun_cov90'])
print('   status:', asr['status_of_asrun_formal_block'])
"""))

# ── 12 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 12. H3 Downstream Aggregate Metrics"))
cells.append(code(r"""
m = down['h3_downstream_metrics']
rows = [
    ('mean Dice', m['mean_dice']),
    ('median Dice', m['median_dice']),
    ('overall recall@90 (detection)', m['overall_recall90_det']),
    ('TINY recall@90 (detection)', m['tiny_recall90_det']),
    ('SMALL recall@90 (detection)', m['small_recall90_det']),
    ('MEDIUM recall@90 (detection)', m['medium_recall90_det']),
    ('LARGE recall@90 (detection)', m['large_recall90_det']),
    ('hard-Tiny recovered', f"{m['hard_tiny_recovered']}/{m['hard_tiny_total']}"),
    ('global-empty recovered', f"{m['global_empty_recovered']}/{m['global_empty_total']}"),
    ('mean FP components/image', m['mean_fp_components_per_image']),
]
display(pd.DataFrame(rows, columns=['metric', 'value']))
print('Strict cov90 (descriptive only):')
c = m['descriptive_strict_cov90']
print('   overall', c['overall_cov90'], '| TINY', c['tiny_cov90'], '| SMALL', c['small_cov90'],
      '| MEDIUM', c['medium_cov90'], '| LARGE', c['large_cov90'])
"""))

# ── 13 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 13. Complete Per-Component Table (152 rows)"))
cells.append(code(r"""
print('Per-component table:', len(comp_df), 'rows')
det = comp_df['h3_downstream_overlap_pixels'].astype(int) >= 1
comp_view = comp_df.assign(h3_det_success=det)
display(comp_view.head(20))
print('...')
print('columns:', list(comp_df.columns))
"""))

# ── 14 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 14. Complete Per-Image Table (103 rows)"))
cells.append(code(r"""
print('Per-image table:', len(img_df), 'rows')
display(img_df.head(20))
print('...')
print('columns:', list(img_df.columns))
"""))

# ── 15 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 15. Size-Stratified Downstream Recall"))
cells.append(code(r"""
det = comp_df['h3_downstream_overlap_pixels'].astype(int) >= 1
cov = comp_df['h3_downstream_coverage_ratio'].astype(float) >= 0.90
rows = []
for g in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']:
    s = comp_df['size_stratum'].eq(g)
    rows.append({
        'size': g,
        'n': int(s.sum()),
        'det_count': int(det[s].sum()),
        'det_recall': float(det[s].mean()),
        'cov90_count': int(cov[s].sum()),
        'cov90_recall': float(cov[s].mean()),
    })
strat = pd.DataFrame(rows)
display(strat)
print('detection domain = frozen formal domain; cov90 = descriptive strict sensitivity.')
"""))

# ── 16 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 16. Contrast Table (GLOBAL / PREDICTED / H3 / ORACLE)"))
cells.append(code(r"""
ct = down['contrast_table']
rows = []
for key in ['GLOBAL', 'PREDICTED', 'H3', 'ORACLE_REGIONAL']:
    r = ct[key]
    rows.append({
        'arm': key,
        'source': r['source'],
        'mean_dice': r['mean_dice'],
        'overall_det': r['overall_recall90_det'],
        'tiny_det': r['tiny_recall90_det'],
        'small_det': r['small_recall90_det'],
        'medium_det': r['medium_recall90_det'],
        'large_det': r['large_recall90_det'],
        'hard_tiny': r['hard_tiny_recovered'],
        'global_empty': r['global_empty_recovered'],
        'mean_fp_img': r['mean_fp_components_per_image'],
    })
contrast_df = pd.DataFrame(rows)
display(contrast_df)
print()
print('H3 strict cov90 (descriptive): TINY', ct['H3']['tiny_cov90'], '| overall', ct['H3']['overall_cov90'])
"""))

# ── 17 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 17. Formal TinyRecall_H3"))
cells.append(code(r"""
fd = down['formal_downstream']
print('TinyRecall_H3 :', fd['TinyRecall_H3'])
print('fraction      :', fd['TinyRecall_H3_fraction'])
print('metric domain :', fd['metric_domain'])
print()
print('Definition: mean over the 72 TINY components of (fused FULL_FIELD mask')
print('overlap >= 1 px) -- identical semantics to the frozen GLOBAL/PREDICTED/ORACLE rows.')
"""))

# ── 18 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 18. Formal R_H3"))
cells.append(code(r"""
print('R_H3 = (TinyRecall_H3 - Tg) / G')
print(f"     = ({fd['TinyRecall_H3']} - {fd['Tg']}) / {fd['G']}")
print(f"     = {fd['R_H3']}")
print('exact fraction:', fd['R_H3_exact_fraction'])
print('band          :', fd['interpretation_band'])
print()
sens = fd['sensitivity_strict_cov90']
print('SENSITIVITY (strict cov90, NOT formal):')
print('   TinyRecall_H3_cov90 =', sens['TinyRecall_H3_cov90'])
print('   R_H3_cov90          =', sens['R_H3_cov90'], '->', sens['interpretation_band_cov90'])
"""))

# ── 19 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 19. Interpretation Band"))
cells.append(code(r"""
bands = [
    ('meaningful', 'R_H3 >= 0.30', fd['R_H3'] >= 0.30),
    ('intermediate', '0.15 <= R_H3 < 0.30', 0.15 <= fd['R_H3'] < 0.30),
    ('insufficient', 'R_H3 < 0.15', fd['R_H3'] < 0.15),
]
for name, rule, hit in bands:
    print(f"  {name:14s} {rule:24s} -> {'ACTIVE' if hit else ''}")
print()
print('Formal band:', fd['interpretation_band'])
"""))

# ── 20 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 20. Supply-Agreement Check"))
cells.append(code(r"""
sa = down['supply_agreement_check']
print('expected  zero-proposal GT / TINY :', sa['expected_zero_proposal_gt'], '/', sa['expected_zero_proposal_tiny'])
print('recomputed zero-proposal GT / TINY:', sa['recomputed_zero_proposal_gt'], '/', sa['recomputed_zero_proposal_tiny'])
print('by size (recomputed):', sa['recomputed_zero_proposal_by_size'])
print('deterministic agreement:', sa['deterministic_agreement'])
print()
print('Discrepancy note:')
print(' ', sa['discrepancy'])
"""))

# ── 21 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 21. Hard-Tiny Recovery"))
cells.append(code(r"""
m = down['h3_downstream_metrics']
print('hard-Tiny recovered (detection) :', m['hard_tiny_recovered'], '/', m['hard_tiny_total'])
print('hard-Tiny recovered (cov90)     :', m['descriptive_strict_cov90']['hard_tiny_recovered_cov90'], '/ 15')
print()
ht = comp_df[comp_df['hard_tiny_flag'].astype(bool)]
print('hard-Tiny components:', len(ht))
display(ht[['sample_id', 'component_id', 'component_area', 'h3_downstream_overlap_pixels', 'h3_downstream_coverage_ratio']])
"""))

# ── 22 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 22. Global-Empty Recovery"))
cells.append(code(r"""
m = down['h3_downstream_metrics']
print('global-empty recovered (detection) :', m['global_empty_recovered'], '/', m['global_empty_total'])
print('global-empty recovered (cov90)     :', m['descriptive_strict_cov90']['global_empty_recovered_cov90'], '/ 5')
ge = img_df[img_df['global_empty'].astype(bool)]
display(ge[['sample_id', 'global_dice', 'h3_downstream_dice', 'h3_proposals', 'h3_empty_pred_flag']])
"""))

# ── 23 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 23. Proposal Burden"))
cells.append(code(r"""
pb = down['h3_downstream_metrics']['proposal_burden']
display(pd.DataFrame(list(pb.items()), columns=['metric', 'value']))
print()
print('H3 proposal counts vs frozen PREDICTED (phase14 mode summary):')
print('  H3 mean proposals/image        :', pb['mean_proposals_per_image'])
print('  PREDICTED mean proposals/image :', float(frozen_summary.loc['PREDICTED_REGIONAL', 'mean_proposals_per_image']))
"""))

# ── 24 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 24. Inference Counters"))
cells.append(code(r"""
ic = down['inference_counters']
display(pd.DataFrame(list(ic.items()), columns=['counter', 'value']))
print()
print('Binding-time counters (prospective):', json.dumps(binding['inference_counters_at_binding']))
print()
print('Governance: exactly ONE H3 downstream inference run; the metric correction')
print('performed ZERO additional inference.')
"""))

# ── 25 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 25. Artifact Provenance"))
cells.append(code(r"""
prov = [
    ('h3_downstream_evaluation.json', 'reports/audits/h3_downstream_evaluation.json', sha('reports/audits/h3_downstream_evaluation.json')),
    ('h3_downstream_evaluation_v1_asrun.json', 'reports/audits/h3_downstream_evaluation_v1_asrun.json', sha('reports/audits/h3_downstream_evaluation_v1_asrun.json')),
    ('h3_downstream_metric_domain_correction.json', 'reports/audits/h3_downstream_metric_domain_correction.json', sha('reports/audits/h3_downstream_metric_domain_correction.json')),
    ('h3_downstream_evaluator_binding.json', 'reports/audits/h3_downstream_evaluator_binding.json', sha('reports/audits/h3_downstream_evaluator_binding.json')),
    ('h3_downstream_per_component.csv', 'reports/tables/h3_downstream_per_component.csv', sha('reports/tables/h3_downstream_per_component.csv')),
    ('h3_downstream_per_image.csv', 'reports/tables/h3_downstream_per_image.csv', sha('reports/tables/h3_downstream_per_image.csv')),
    ('h3_supply_axis_metric_domain_reconciliation.json', 'reports/audits/h3_supply_axis_metric_domain_reconciliation.json', sha('reports/audits/h3_supply_axis_metric_domain_reconciliation.json')),
]
display(pd.DataFrame(prov, columns=['artifact', 'path', 'sha256']))
"""))

# ── 26 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 26. Scientific Interpretation"))
cells.append(code(r"""
print('DOWNSTREAM AXIS (formal, detection domain):')
print(f"  TinyRecall_H3 = {fd['TinyRecall_H3']:.6f} ({fd['TinyRecall_H3_fraction']})")
print(f"  Tg            = {fd['Tg']:.6f} (frozen GLOBAL)")
print(f"  R_H3          = {fd['R_H3']:.6f}  [{fd['interpretation_band']}]")
print()
print('Reading: in the frozen detection domain the H3 downstream pipeline recovers')
print('slightly more TINY components than the frozen GLOBAL baseline (59/72 vs 57/72).')
print('Relative to the ORACLE gap (G = 15/72), H3 closes 2/15 = 13.33% of the gap,')
print('which is below the 0.15 insufficiency boundary. The strict >=90%-coverage')
print('domain tells a stricter story and is reported separately for transparency.')
print()
print('This notebook does NOT issue an H3 verdict. It records the frozen measurement.')
"""))

# ── 27 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 27. Formal-Adjudication Boundary"))
cells.append(code(r"""
print('formal_adjudication_performed :', down['formal_adjudication_performed'])
print('h3_verdict_issued             :', down['h3_verdict_issued'])
print()
print('The formal H3 adjudication (Notebook 07) is NOT performed here and requires')
print('separate supervisor authorization. Notebook 06 only records the frozen')
print('downstream evaluation and the metric-domain reconciliation.')
"""))

# ── 28 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 28. Phase-15 & TEST State"))
cells.append(code(r"""
print('Phase 15 status :', down['phase_15_status'])
print('TEST reads      :', down['test_reads'])
print('External reads  :', down['external_test_reads'])
print('Supply gates    : preserved and INVALID_FOR_FORMAL_ADJUDICATION (unchanged)')
"""))

# ── 29 ──────────────────────────────────────────────────────────────────────
cells.append(md("## 29. Visualizations"))

cells.append(md("### Figure A — Downstream TINY Recall@90 (detection): arm contrast"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(8, 5))
keys = ['GLOBAL', 'PREDICTED', 'H3', 'ORACLE_REGIONAL']
arms = ['GLOBAL', 'PREDICTED', 'H3', 'ORACLE']
vals = [ct[k]['tiny_recall90_det'] for k in keys]
colors = ['#95a5a6', '#3498db', '#e67e22', '#2ecc71']
bars = ax.bar(arms, vals, color=colors, edgecolor='black', linewidth=0.5)
ax.axhline(fd['Tg'], color='red', linestyle='--', linewidth=1.5, label=f"Tg = {fd['Tg']:.4f}")
ax.set_ylabel('TINY recall@90 (detection, >=1px)')
ax.set_title('Downstream TINY Recall@90 by arm (frozen detection domain)')
ax.set_ylim(0, 1.05)
for b, v in zip(bars, vals):
    ax.text(b.get_x()+b.get_width()/2, v+0.02, f'{v:.4f}', ha='center', fontweight='bold')
ax.legend()
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figA_tiny_recall_arms.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure A saved.')
"""))

cells.append(md("### Figure B — Size-stratified downstream recall (detection): GLOBAL vs PREDICTED vs H3"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(10, 6))
sizes = ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
x = np.arange(len(sizes)); w = 0.25
g = [ct['GLOBAL'][f'{s.lower()}_recall90_det'] for s in sizes]
p = [ct['PREDICTED'][f'{s.lower()}_recall90_det'] for s in sizes]
h = [ct['H3'][f'{s.lower()}_recall90_det'] for s in sizes]
ax.bar(x-w, g, w, label='GLOBAL', color='#95a5a6', edgecolor='black', linewidth=0.5)
ax.bar(x,   p, w, label='PREDICTED', color='#3498db', edgecolor='black', linewidth=0.5)
ax.bar(x+w, h, w, label='H3', color='#e67e22', edgecolor='black', linewidth=0.5)
ax.set_xticks(x); ax.set_xticklabels(sizes)
ax.set_ylabel('recall@90 (detection)'); ax.set_ylim(0, 1.05)
ax.set_title('Size-stratified downstream recall@90 (detection domain)')
ax.legend()
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figB_size_recall.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure B saved.')
"""))

cells.append(md("### Figure C — Strict cov90 sensitivity by size (H3)"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(8, 5))
cov_vals = [comp_df[comp_df['size_stratum'].eq(s)]['h3_downstream_coverage_ratio'].astype(float).ge(0.90).mean() for s in sizes]
bars = ax.bar(sizes, cov_vals, color='#9b59b6', edgecolor='black', linewidth=0.5)
ax.set_ylabel('recall@>=90% coverage'); ax.set_ylim(0, 1.0)
ax.set_title('H3 strict cov90 by size (descriptive sensitivity, NOT formal)')
for b, v in zip(bars, cov_vals):
    ax.text(b.get_x()+b.get_width()/2, v+0.02, f'{v:.4f}', ha='center', fontweight='bold')
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figC_cov90_by_size.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure C saved.')
"""))

cells.append(md("### Figure D — R_H3 gauge: formal (detection) vs sensitivity (cov90)"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(9, 4))
vals = [fd['R_H3'], sens['R_H3_cov90']]
labels = ['R_H3 formal\n(detection)', 'R_H3 sensitivity\n(cov90)']
colors = ['#e67e22', '#9b59b6']
bars = ax.barh(labels, vals, color=colors, edgecolor='black', linewidth=0.5)
ax.axvline(0.15, color='red', linestyle='--', linewidth=1.2, label='insufficient < 0.15')
ax.axvline(0.30, color='green', linestyle='--', linewidth=1.2, label='meaningful >= 0.30')
ax.axvline(0.0, color='black', linewidth=1.0)
ax.set_xlabel('R_H3')
ax.set_title('R_H3: formal frozen domain vs strict-coverage sensitivity')
for b, v in zip(bars, vals):
    ax.text(v, b.get_y()+b.get_height()/2, f' {v:.4f}', va='center', fontweight='bold')
ax.legend(loc='lower right')
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figD_rh3_gauge.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure D saved.')
"""))

cells.append(md("### Figure E — Per-image downstream Dice: H3 vs GLOBAL"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(img_df['global_dice'], bins=25, alpha=0.6, label='GLOBAL', color='#95a5a6')
ax.hist(img_df['h3_downstream_dice'], bins=25, alpha=0.6, label='H3 downstream', color='#e67e22')
ax.axvline(img_df['global_dice'].mean(), color='#7f8c8d', linestyle='--', linewidth=1.5)
ax.axvline(img_df['h3_downstream_dice'].mean(), color='#d35400', linestyle='--', linewidth=1.5)
ax.set_xlabel('Dice'); ax.set_ylabel('images')
ax.set_title('Per-image FULL_FIELD Dice: GLOBAL vs H3 downstream')
ax.legend()
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figE_dice_hist.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure E saved.')
"""))

cells.append(md("### Figure F — Proposal burden (H3)"))
cells.append(code(r"""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
vc = img_df['h3_proposals'].value_counts().sort_index()
ax1.bar(vc.index, vc.values, color='#16a085', edgecolor='black', linewidth=0.5)
ax1.set_xlabel('proposals per image'); ax1.set_ylabel('images')
ax1.set_title('H3 proposals per image')
ax2.hist(img_df['h3_roi_area_fraction'], bins=25, color='#2980b9', edgecolor='black', linewidth=0.5)
ax2.set_xlabel('ROI union area fraction'); ax2.set_ylabel('images')
ax2.set_title('H3 ROI area fraction')
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figF_proposal_burden.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure F saved.')
"""))

cells.append(md("### Figure G — Zero-proposal GT/TINY: pre-H3 vs H3 (preserved supply evidence)"))
cells.append(code(r"""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
ax1.bar(['PRE-H3', 'H3'], [79, sa['recomputed_zero_proposal_gt']], color=['#e74c3c', '#2ecc71'], edgecolor='black', linewidth=0.5)
ax1.set_ylabel('zero-proposal GT components'); ax1.set_title('Zero-proposal GT (of 152)')
ax2.bar(['PRE-H3', 'H3'], [57, sa['recomputed_zero_proposal_tiny']], color=['#e74c3c', '#2ecc71'], edgecolor='black', linewidth=0.5)
ax2.set_ylabel('zero-proposal TINY components'); ax2.set_title('Zero-proposal TINY (of 72)')
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figG_zero_proposal.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure G saved.')
"""))

cells.append(md("### Figure H — Downstream detection outcomes by size (H3)"))
cells.append(code(r"""
fig, ax = plt.subplots(figsize=(9, 5))
det_counts = [int((det & comp_df['size_stratum'].eq(s)).sum()) for s in sizes]
miss_counts = [int(((~det) & comp_df['size_stratum'].eq(s)).sum()) for s in sizes]
x = np.arange(len(sizes))
ax.bar(x, det_counts, label='detected (>=1px)', color='#27ae60', edgecolor='black', linewidth=0.5)
ax.bar(x, miss_counts, bottom=det_counts, label='not detected', color='#c0392b', edgecolor='black', linewidth=0.5)
for i, s in enumerate(sizes):
    tot = det_counts[i] + miss_counts[i]
    ax.text(i, tot+0.5, f'{det_counts[i]}/{tot}', ha='center', fontweight='bold')
ax.set_xticks(x); ax.set_xticklabels(sizes)
ax.set_ylabel('components'); ax.set_title('H3 downstream detection outcomes by size')
ax.legend()
plt.tight_layout(); plt.savefig(str(FIGDIR/'h3_downstream_figH_outcomes.png'), dpi=150, bbox_inches='tight'); plt.show()
print('Figure H saved.')
"""))

# ── Assertions ──────────────────────────────────────────────────────────────
cells.append(md("## Assertions\n\nAll assertions verify governance and data-integrity constraints. Derived values are recomputed from saved tables, not hardcoded."))
cells.append(code(r"""
# ── Checkpoint / binding ─────────────────────────────────────────────────────
assert ck_sha_disk == 'd875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e', 'H3 checkpoint SHA mismatch'
assert down['refiner_checkpoint']['sha256'] == '2e09e3a9c39c731687db1a9fef0c80881ed6235e4cda070bb4b8b382caa45daa', 'refiner SHA mismatch'
assert down['global_checkpoint']['sha256'] == 'ec7eb13f32e43af27eab7fc617bd1a2a8fcce1d6651a1b4a3653f3e4d1283269', 'global SHA mismatch'
assert binding['status'] == 'BOUND_PROSPECTIVE__BEFORE_RESULTS'
assert binding['h3_heatmap_resolution'] == 128

# ── Population ───────────────────────────────────────────────────────────────
assert len(comp_df) == 152
assert len(img_df) == 103
assert comp_df['size_stratum'].value_counts().to_dict() == {'TINY': 72, 'SMALL': 28, 'MEDIUM': 36, 'LARGE': 16}

# ── Frozen proposal policy: exactly one ──────────────────────────────────────
assert down['proposal_configurations_evaluated'] == 1
assert down['frozen_proposal_policy'] == {'threshold': 0.10, 'margin': 0.20, 'top_k': 5, 'nms_iou': 0.30}

# ── Formal metric recomputed from saved table ────────────────────────────────
det = comp_df['h3_downstream_overlap_pixels'].astype(int) >= 1
tiny_det = float(det[comp_df['size_stratum'].eq('TINY')].mean())
assert abs(tiny_det - down['formal_downstream']['TinyRecall_H3']) < 1e-12, 'TinyRecall_H3 mismatch'
assert down['formal_downstream']['TinyRecall_H3_fraction'] == '59/72'

# ── R_H3 recomputed ──────────────────────────────────────────────────────────
Tg = 0.7916666666666666
G = 0.20833333333333337
r_h3 = (tiny_det - Tg) / G
assert abs(r_h3 - down['formal_downstream']['R_H3']) < 1e-12, 'R_H3 mismatch'
assert abs(r_h3 - 2/15) < 1e-12, 'R_H3 should equal 2/15'
assert down['formal_downstream']['interpretation_band'] == 'insufficient'

# ── Metric-domain reconciliation present ─────────────────────────────────────
assert down['metric_domain_corrected'] is True
assert down['metric_domain_correction']['inference_rerun'] is False
assert abs(asrun['formal_downstream']['R_H3'] - (-1.4)) < 1e-9
assert corr['status'] == 'H3_DOWNSTREAM_METRIC_DOMAIN_CORRECTED__FORMAL_ADJUDICATION_PENDING'
assert corr['governance']['inference_executed_by_correction'] is False

# ── Contrast table internal consistency ──────────────────────────────────────
assert abs(ct['GLOBAL']['tiny_recall90_det'] - Tg) < 1e-12
assert abs(ct['ORACLE_REGIONAL']['tiny_recall90_det'] - 1.0) < 1e-12
assert abs((ct['ORACLE_REGIONAL']['tiny_recall90_det'] - ct['GLOBAL']['tiny_recall90_det']) - G) < 1e-12

# ── Governance locks ─────────────────────────────────────────────────────────
assert down['formal_adjudication_performed'] is False
assert down['h3_verdict_issued'] is False
assert down['test_reads'] == 0
assert down['external_test_reads'] == 0
assert down['phase_15_status'] == 'NOT_STARTED_AND_NOT_AUTHORIZED'
assert down['status'] == 'H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING'

print('\n✓ All Notebook 06 assertions passed.')
print('Final state:', down['status'])
"""))

nb = nbformat.v4.new_notebook(cells=cells)
nbformat.write(nb, str(NB_PATH))
print(f'Wrote {NB_PATH} with {len(nb.cells)} cells')

print('Executing Notebook 06...')
client = NotebookClient(nb, kernel_name='jup-venv', timeout=900,
                        resources={'metadata': {'path': str(ROOT)}})
client.execute()
nbformat.write(nb, str(NB_PATH))

errors = 0
for i, cell in enumerate(nb.cells):
    if cell.cell_type == 'code':
        for out in cell.get('outputs', []):
            if out.get('output_type') == 'error':
                errors += 1
                print(f'  ERROR cell {i}: {out.get("ename")}: {out.get("evalue")}')
counts = [c.get('execution_count') for c in nb.cells if c.cell_type == 'code']
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
print(f'Cells: {len(nb.cells)} | code cells: {len(counts)}')
print(f'Zero tracebacks: {"PASS" if errors == 0 else "FAIL"}')
print(f'Monotonic exec counts (1..{len(counts)}): {"PASS" if monotonic else "CHECK"}')
print('Notebook 06 SHA:', hashlib.sha256(NB_PATH.read_bytes()).hexdigest())
