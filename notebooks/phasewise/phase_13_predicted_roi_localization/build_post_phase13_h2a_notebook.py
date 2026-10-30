"""Build the Post-Phase-13 H2-A-B1 localizer training reviewer notebook (READ-ONLY, no training)."""
from __future__ import annotations

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(r"D:\Softfors\jup")
OUT = (ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
       / "post_phase13_h2a_localizer_training_review.ipynb")

cells = []
md = lambda t: cells.append(new_markdown_cell(t))     # noqa: E731
code = lambda t: cells.append(new_code_cell(t))       # noqa: E731

md("""# POST-PHASE-13 H2-A-B1 — LOCALIZER TRAINING REVIEW (DEPLOYMENT-BALANCED SELECTION)

**READ-ONLY.** No training, no model construction, no CUDA, no forward pass, no proposal generation,
no checkpoint writes, no TEST access. This notebook only reads the frozen H2A artifacts.

**Adaptive-development disclosure.** H2A is an **adaptive VAL-development experiment** initiated after
Phase 13 returned `REVISE_LOCALIZER` and H1 established that acceptance-only mitigation is insufficient.
The H2A selection rule was **frozen before training**. VAL remains **development data**. No H2A result
substitutes for final TEST evaluation. **TEST remains untouched.**

Experiment id: `post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3`""")

code("""import json, hashlib
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option('display.width', 300); pd.set_option('display.max_columns', 200)

ROOT = Path(r'D:\\Softfors\\jup'); A = ROOT/'reports'/'audits'; T = ROOT/'reports'/'tables'
H2A = 'post_phase13_h2a_kub_localizer_r512_h128_sigmaeq075_centernetfocal_deploymentbalance_seed42_clean_v3'
EX = ROOT/'experiments'/H2A; CK = ROOT/'checkpoints'/H2A

def sha(p):
    h = hashlib.sha256()
    with open(p,'rb') as f:
        for c in iter(lambda: f.read(1<<20), b''): h.update(c)
    return h.hexdigest()

hist = pd.read_csv(EX/'history.csv')
proto = json.loads((A/'post_phase13_h2a_protocol_frozen.json').read_text('utf-8'))
audit = json.loads((A/'post_phase13_h2a_localizer_score_path_audit.json').read_text('utf-8'))
traj  = json.loads((A/'post_phase13_h2a_training_trajectory_reproduction.json').read_text('utf-8'))
repl  = json.loads((A/'post_phase13_h2a_selection_replay_verification.json').read_text('utf-8'))
ev    = json.loads((A/'post_phase13_h2a_training_evaluation.json').read_text('utf-8'))
se    = json.loads((A/'post_phase13_h2a_best_checkpoint_standalone_evaluation.json').read_text('utf-8'))
print('loaded frozen H2A artifacts | history rows:', len(hist))""")

# 1
md("## 1. Governance / adaptive-development disclosure\n\n"
   "| item | value |\n|---|---|\n"
   "| nature | adaptive VAL-development experiment |\n"
   "| initiated after | Phase 13 `REVISE_LOCALIZER` + H1 `PARTIAL_MITIGATION_INSUFFICIENT` |\n"
   "| selection rule frozen before training | **YES** |\n"
   "| VAL role | development data |\n"
   "| substitutes for final TEST | **NO** |\n"
   "| TEST | **UNTOUCHED** |")
code("""for k,v in ev['adaptive_development_disclosure'].items(): print(f'{k:<45}', v)
print()
print('stop boundary:', json.dumps(ev['stop_boundary']))""")

# 2
md("## 2. H1 closure + H2A rationale\n\n"
   "H1 showed selective acceptance materially improves intervention precision but **no frozen policy"
   " jointly restores global preservation and retains enough regional utility**. The Phase-13 selection"
   " rule optimised recall and ROI area with **no proposal-precision term**, so the next minimum axis was"
   " **checkpoint selection only**.")
code("""h1 = json.loads((A/'post_phase13_regional_revision_r1_h1_adjudication.json').read_text('utf-8'))
print('H1 outcome      :', h1['h1_outcome'])
print('H1 closed state :', h1['continuity']['h1'])
print('H1 proves representation failure:', h1['h1_proves_representation_failure'])
print('H2 eligibility  :', h1['h2_eligibility']['h2_localizer_retraining_or_selection_redesign'])
print('H2 training     :', h1['h2_eligibility']['authorized_for_training'])""")

# 3
md("## 3. Protocol identity")
code("""print('protocol status    :', proto['status'])
print('experiment id      :', proto['experiment_id'])
print('execution mode     :', proto['execution_mode'])
print('H2 axis            :', proto['h2_axis'])
print('protocol SHA       :', sha(A/'post_phase13_h2a_protocol_frozen.json'))
print('score-path verdict :', audit['verdict'])
print('score-path SHA     :', sha(A/'post_phase13_h2a_localizer_score_path_audit.json'))
print('collision          :', proto['experiment_id_collision'])""")

# 4
md("## 4. Scientific-change register\n\n**Only one scientific axis changes.**")
code("""for c in proto['scientific_change_register']:
    print('id   :', c['id']); print('field:', c['field'])
    print('old  :', c['old']); print('new  :', c['new']); print('why  :', c['motivation'][:200], '...')
print()
for k,v in proto['selection_only_interpretation'].items(): print(f'  {k:<34}', v)""")

# 5
md("## 5. Score-path audit")
code("""print('verdict:', audit['verdict'])
print('sigmoid application:', audit['sigmoid_application'])
print('0.125065 max imposed by code:', audit['plateau_maximum_imposed_by_code'])
print('material observation:', audit['material_scientific_observation']['id'])
print()
h = audit['head_tensor_evidence']
print('head weights: range', round(h['weight_min'],6), '..', round(h['weight_max'],6),
      '| std', round(h['weight_std'],8), '| abs-max/abs-mean', round(h['weight_abs_max_over_abs_mean'],6),
      '| positive', h['weight_positive_count'], 'of 16')
print('head bias:', h['bias'], '| sigmoid(bias):', h['sigmoid_of_bias'])""")

# 6
md("## 6. Population")
code("""print('TRAIN 770 FULL_FIELD / 1161 components | VAL 103 FULL_FIELD / 152 components | ROI EXCLUDED')
print('history epochs:', len(hist), '| range', int(hist.epoch.min()), '->', int(hist.epoch.max()))
print('components per stratum:',
      pd.read_csv(T/'post_phase13_h2a_best_checkpoint_component_coverage.csv').size_stratum.value_counts().to_dict())""")

# 7
md("## 7. Frozen training contract")
code("""print(ev['training_contract'])
print()
print('loss / optimizer / scheduler / batch / seed / amp / augmentation: UNCHANGED from Phase-13')""")

# 8
md("## 8. Frozen proposal evaluation")
code("""print(json.dumps(ev['proposal_config']))
print('coverage semantics (primary):', 'HISTORICAL_EXECUTING_BBOX_COVERAGE')
print('grid:', 0, '| threshold tuning: NONE')""")

# 9
md("## 9. Deployment-balance definition\n\n"
   "`DEPLOYMENT_BALANCE_HMEAN_P_TINY90_OVERALL90 = 0.0 if any of P,T,O <= 0 else 3/(1/P + 1/T + 1/O)`\n\n"
   "**NOT** a statistical F1 score. NOT weighted. NOT clipped.")
code("""print(proto['new_primary_checkpoint_utility']['label'])
print(proto['new_primary_checkpoint_utility']['definition'])
print('is statistical F1:', proto['new_primary_checkpoint_utility']['is_statistical_f1'])""")

# 10
md("## 10. Selection tuple")
code("""for i,t in enumerate(proto['h2a_primary_checkpoint_tuple']['tuple'],1): print(f'  {i}. {t}')
print()
for k in ('comparison','ties','early_stop_patience','checkpoint','latest_pt',
          'downstream_segmentation_metric_participates','phase12_oracle_result_participates',
          'r1_segmentation_outcome_participates'):
    print(f'  {k:<45}', proto['h2a_primary_checkpoint_tuple'][k])""")

# 11
md("## 11. Training trajectory reproduction (§10)\n\n"
   "Because H2A changes checkpoint selection ONLY, gradient-update semantics must be identical, so"
   " `train_loss`/`val_loss` must agree epoch-by-epoch with the Phase-13 run.")
code("""c = traj['comparison']
for k in ('overlapping_epochs','epochs_aligned','max_abs_train_loss_diff','max_abs_val_loss_diff',
          'train_loss_exact_match','val_loss_exact_match','lr_mismatches','gradient_semantics_changed'):
    print(f'  {k:<30}', c[k])
print()
print('checkpoint model-state cross-checks:', len(traj['checkpoint_state_cross_checks']),
      '(best epoch', ev['best_epoch'], '/ latest', ev['termination']['final_epoch'],
      'are not historical 31/53/68 -> no overlap, as the protocol allows)')""")

# 12 — COMPLETE epoch table
md("## 12. COMPLETE epoch-by-epoch table\n\n"
   "**Untruncated** — exactly one completed epoch per row, every completed epoch, no ellipsis.")
code("""cols = ['epoch','train_loss','val_loss','learning_rate','proposal_pixel_hit_count',
        'proposal_total_count','proposal_pixel_any_hit_precision','tiny_recall90','overall_recall90',
        'deployment_balance_hmean','mean_roi_area_fraction','is_new_best','bad_epochs']
full = hist[cols]
print(f'rows shown: {len(full)} / {len(hist)}  (complete, no truncation)')
print(full.to_string(index=False, float_format=lambda v: f'{v:.10g}'))""")

# 13
md("## 13. Loss curves")
code("""for e in range(1, len(hist)+1, 10):
    r = hist[hist.epoch==e]
    if len(r):
        r = r.iloc[0]
        print(f'  epoch {e:>3}  train {r.train_loss:.6f}  val {r.val_loss:.6f}')
print()
print('final epoch train/val:',
      float(hist.train_loss.iloc[-1]), '/', float(hist.val_loss.iloc[-1]))""")

# 14
md("## 14. P / T / O trajectories")
code("""sub = hist[hist.epoch.isin(range(31, len(hist)+1, 5))][
    ['epoch','proposal_pixel_any_hit_precision','tiny_recall90','overall_recall90']]
print(sub.to_string(index=False))
print()
print('epochs 1-30 have P=T=O=0 (no proposals at threshold 0.10 until epoch',
      int(hist[hist.proposal_total_count>0].epoch.iloc[0]), ')')""")

# 15
md("## 15. Deployment-balance trajectory")
code("""sub = hist[['epoch','deployment_balance_hmean','val_loss']]
print('max HMean:', float(hist.deployment_balance_hmean.max()),
      'at epoch', int(hist.loc[hist.deployment_balance_hmean.idxmax(),'epoch']))
print()
print(sub[sub.epoch.isin(range(31, len(hist)+1, 5))].to_string(index=False))""")

# 16
md("## 16. Proposal count / ROI area")
code("""sub = hist[hist.epoch.isin(range(31, len(hist)+1, 10))][
    ['epoch','proposal_total_count','proposal_count_per_image','mean_roi_area_fraction']]
print(sub.to_string(index=False))""")

# 17
md("## 17. Score saturation diagnostics")
code("""sub = hist[hist.epoch.isin(range(31, len(hist)+1, 10))][
    ['epoch','proposal_score_mean','proposal_score_median','proposal_score_max',
     'proposal_score_iqr','fraction_proposals_exactly_at_epoch_max_score']]
print(sub.to_string(index=False))""")

# 18
md("## 18. Score separability diagnostics")
code("""sub = hist[hist.epoch.isin(range(31, len(hist)+1, 10))][
    ['epoch','hit_proposal_score_mean','miss_proposal_score_mean',
     'proposal_roc_auc_score_to_pixel_any_hit','proposal_pr_auc_score_to_pixel_any_hit']]
print(sub.to_string(index=False))""")

# 19
md("## 19. Best-checkpoint selection replay (§14)")
code("""print('replay result :', repl['status'])
print('mismatches    :', repl['mismatch_count'], '| max abs term diff:', repl.get('max_abs_term_diff'))
print('replayed      : best epoch', repl['replayed']['best_epoch'],
      '| final bad_epochs', repl['replayed']['final_bad_epochs'],
      '| early stop', repl['replayed']['early_stop_epoch'])
print('stored        : best epoch', repl['stored']['best_epoch'])
print('best tuple    :', repl['stored']['best_score'])""")

# 20
md("## 20. Standalone best-checkpoint proposal evaluation (§16)")
code("""m = se['metrics']
for k in ('proposal_total_count','proposal_count_per_image','proposal_pixel_any_hit_precision',
          'proposal_bbox_any_hit_precision','tiny_recall90','overall_recall90','overall_recall50',
          'any_overlap_recall','mean_coverage','mean_proposal_union_area','score_max','score_iqr',
          'fraction_exactly_at_max','roc_auc_score_to_pixel_any_hit','pr_auc_score_to_pixel_any_hit'):
    print(f'  {k:<42}', m[k])
print()
print('checkpoint:', se['checkpoint'], '| sha:', se['checkpoint_sha'])""")

# 21
md("## 21. Size-stratified results")
code("""s = pd.read_csv(T/'post_phase13_h2a_best_checkpoint_size_stratified.csv')
print(s.to_string(index=False))""")

# 22
md("## 22. Difficult cohorts (predeclared)")
code("""for k in ('hard_tiny','global_empty','multi_component'):
    print(f'  {k:<18}', json.dumps(se['metrics'][k]))""")

# 23
md("## 23. Comparison with the Phase-13 best localizer — DESCRIPTIVE ONLY")
code("""cmp = pd.read_csv(T/'post_phase13_h2a_vs_phase13_localizer_comparison.csv')
print(cmp.to_string(index=False))
print()
print(se['phase13_comparison']['language'])""")

# 24
md("## 24. Limitations\n\n"
   "- **Adaptive development.** H2A was initiated after Phase 13 failed the gate; the selection rule was"
   " frozen before training and VAL is development data.\n"
   "- **Epochs 1-30 carry no precision/coverage signal.** Proposals only appear from epoch 31, so the"
   " tuple's first five terms are zero there and selection falls back to `-val_loss`. The rule therefore"
   " cannot discriminate epochs 1-30 on precision; divergence from Phase-13 is confined to the"
   " post-epoch-31 regime.\n"
   "- **Single seed** (42); no paired significance testing was performed and none is claimed.\n"
   "- **Selection is not a causal proof.** A better-selected checkpoint does not establish that selection"
   " redesign is sufficient downstream.\n"
   "- **No downstream segmentation was run** in this part, so no regional-integration conclusion follows.\n"
   "- HD95-style fields are not part of this localizer-level contract.\n"
   "- The comparison against Phase-13 uses the **frozen** Part-1C tables (no Phase-13 re-inference); it is"
   " descriptive and makes **no superiority or significance claim**.")

# 25
md("## 25. Explicit downstream stop boundary")
code("""print('downstream regional segmentation :', ev['stop_boundary']['downstream_regional_segmentation'])
print('R1 selective acceptance applied  :', ev['stop_boundary']['r1_selective_acceptance_applied'])
print('segmentation models loaded       :', ev['stop_boundary']['segmentation_models_loaded'])
print()
print('H2A downstream segmentation :', ev['continuity']['h2a_downstream_segmentation'])
print('H2A outcome adjudication    :', ev['continuity']['h2a_outcome_adjudication'])
print('H2 loss/target redesign     :', ev['continuity']['h2_loss_target_redesign'])
print('H3                          :', ev['continuity']['h3'])
print('Phase14                     :', ev['continuity']['phase14'])
print('TEST                        :', ev['continuity']['test'])
print()
print('Not decided here: whether H2A selection redesign is sufficient. That is a supervisor step.')""")

# 26
md("## 26. Artifact SHA registry")
code("""reg = {
 'H2A protocol frozen': A/'post_phase13_h2a_protocol_frozen.json',
 'H2A score-path audit': A/'post_phase13_h2a_localizer_score_path_audit.json',
 'trajectory reproduction': A/'post_phase13_h2a_training_trajectory_reproduction.json',
 'selection replay verification': A/'post_phase13_h2a_selection_replay_verification.json',
 'standalone best-checkpoint evaluation': A/'post_phase13_h2a_best_checkpoint_standalone_evaluation.json',
 'training evaluation': A/'post_phase13_h2a_training_evaluation.json',
 'best.pt': CK/'best.pt', 'latest.pt': CK/'latest.pt', 'history.csv': EX/'history.csv',
 'best_checkpoint_proposals': T/'post_phase13_h2a_best_checkpoint_proposals.csv',
 'best_checkpoint_case_proposals': T/'post_phase13_h2a_best_checkpoint_case_proposals.csv',
 'best_checkpoint_component_coverage': T/'post_phase13_h2a_best_checkpoint_component_coverage.csv',
 'best_checkpoint_size_stratified': T/'post_phase13_h2a_best_checkpoint_size_stratified.csv',
 'phase13 comparison': T/'post_phase13_h2a_vs_phase13_localizer_comparison.csv',
}
for k,p in reg.items(): print(f'{sha(p)}  {k}')
print()
print('READ-ONLY notebook: no training, no model construction, no CUDA, no forward pass, no TEST access.')""")

code("""print('epoch table completeness check')
print('  history rows        :', len(hist))
print('  epochs contiguous   :', bool((hist.epoch.diff().dropna()==1).all()))
print('  first / last epoch  :', int(hist.epoch.iloc[0]), '/', int(hist.epoch.iloc[-1]))
print('  duplicate epochs    :', int(hist.epoch.duplicated().sum()))
print('  table rows displayed:', len(hist), '(untruncated)')""")

nb = new_notebook(cells=cells)
nb.metadata = {"kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
               "language_info": {"name": "python"}}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, str(OUT))
print("wrote", OUT)
print("cells", len(nb.cells), "code", len([c for c in nb.cells if c.cell_type == "code"]))
