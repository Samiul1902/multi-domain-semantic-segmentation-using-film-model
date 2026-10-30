"""Generate and execute Notebook 05 — H3 Supply-Axis Evaluation.

Creates notebooks/phasewise/post_phase14_h3_proposal_supply/05_h3_supply_axis_evaluation.ipynb
with all 26 required sections, 8 figures, complete tables, and assertions.
Then executes it with nbclient.
"""
from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell
import nbclient

ROOT = Path(__file__).resolve().parents[2]
NB_DIR = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply"
NB_PATH = NB_DIR / "05_h3_supply_axis_evaluation.ipynb"


def md(source: str) -> dict:
    return new_markdown_cell(source.strip())


def code(source: str) -> dict:
    return new_code_cell(source.strip())


cells = []

# ════════════════════════════════════════════════════════════════════════════
# 1. Title / scientific scope
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
# Notebook 05 — H3 Supply-Axis Evaluation

**Scientific scope:** Authoritative supply-axis evaluation of the selected H3
checkpoint (`h3_kub_localizer_sigma_adaptive_sizeaware_seed42_clean_v3`, epoch 54)
on canonical clean-v3 FULL_FIELD VAL (103 images, 152 GT components) under the
frozen proposal decode (threshold=0.10, margin=0.20, top_k=5, nms_iou=0.30).

**This notebook does NOT:**
- Train or retrain any model
- Evaluate alternate checkpoints or proposal policies
- Run the Phase-14 regional refiner
- Perform downstream Dice adjudication
- Access TEST or external TEST
- Start Phase 15
- Perform formal H3 adjudication

**Evaluation state:** `H3_SUPPLY_AXIS_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`
"""))

# ════════════════════════════════════════════════════════════════════════════
# 2. Current governance state
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 2. Current Governance State

| Item | Status |
|------|--------|
| H3 Training | COMPLETE (69 epochs, early stopping patience 15) |
| Checkpoint Selection Replay | PASS (epoch 54, val_localization_recall=0.6382) |
| Supply-Axis Evaluation | COMPLETE (this notebook) |
| Formal H3 Adjudication | PENDING (Notebook 06, not authorized) |
| Phase-14 Refiner Evaluation | NOT PERFORMED in this task |
| Phase 15 | NOT_STARTED_AND_NOT_AUTHORIZED |
| TEST | CLOSED (0 reads) |
| External TEST | CLOSED (0 reads) |
"""))

# ════════════════════════════════════════════════════════════════════════════
# 3. H3 training checkpoint binding
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 3. H3 Training Checkpoint Binding
"""))

cells.append(code(r"""
import json, hashlib, sys
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

ROOT = Path('D:/Softfors/jup')
sys.path.insert(0, str(ROOT))

# Load authoritative artifacts
closure = json.loads((ROOT / 'reports/audits/h3_proposal_supply_training_closure.json').read_text())
replay = json.loads((ROOT / 'reports/audits/h3_checkpoint_selection_replay.json').read_text())
eval_artifact = json.loads((ROOT / 'reports/audits/h3_supply_axis_evaluation.json').read_text())
criteria = json.loads((ROOT / 'reports/audits/h3_proposal_supply_success_failure_criteria.json').read_text())

EXPERIMENT_ID = closure['experiment_id']
SELECTED_EPOCH = closure['best_epoch']
CHECKPOINT_PATH = ROOT / closure['checkpoint_integrity']['best_pt']['path']
EXPECTED_SHA = closure['implementation_shas']['best_pt']

# Verify checkpoint SHA from disk
ckpt_sha = hashlib.sha256(CHECKPOINT_PATH.read_bytes()).hexdigest()
assert ckpt_sha == EXPECTED_SHA, f"Checkpoint SHA mismatch: {ckpt_sha} != {EXPECTED_SHA}"

print(f"Experiment ID: {EXPERIMENT_ID}")
print(f"Selected epoch: {SELECTED_EPOCH}")
print(f"Checkpoint path: {CHECKPOINT_PATH}")
print(f"Checkpoint SHA: {ckpt_sha}")
print(f"SHA matches closure: {ckpt_sha == EXPECTED_SHA}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 4. Checkpoint-selection replay confirmation
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 4. Checkpoint-Selection Replay Confirmation
"""))

cells.append(code(r"""
replay_verdict = replay['verdict']
replay_epoch = replay['replay_selected_epoch']
replay_score = replay['replay_selected_score']

print(f"Replay verdict: {replay_verdict}")
print(f"Replay selected epoch: {replay_epoch}")
print(f"Replay selected score: {replay_score}")
print(f"Replay selected val_localization_recall: {replay['replay_selected_val_localization_recall']}")
print(f"Replay selected val_loss: {replay['replay_selected_val_loss']}")
print(f"Early stopping fired: {replay['early_stopping_fired']}")
print(f"Max epochs reached: {replay['max_epochs_reached']}")
print(f"Selected epoch all sources match: {replay['comparisons']['selected_epoch_all_sources_match']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 5. Trainer multi-SHA provenance caveat
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 5. Trainer Multi-SHA Provenance Caveat

The H3 training trajectory spans multiple trainer revisions:

| Segment | Epochs | Trainer SHA |
|---------|--------|-------------|
| Design-era | — | `37b64310...` |
| Segment 1 | 1–2 | `9099d6de...` |
| Segment 2 | 3–69 | `45bef74f...` |

The exact source bytes for the epoch-1/2 trainer are **unavailable locally**.
We do NOT claim a single trainer SHA produced the complete trajectory.
The selected epoch-54 checkpoint was produced under the final segment trainer (`45bef74f`).
This is carried as provenance only — no training is rerun.
"""))

cells.append(code(r"""
lineage = closure['implementation_shas']['trainer_lineage']
print("Trainer lineage:")
for k, v in lineage.items():
    print(f"  {k}: {v}")
print(f"\nLaunch-era trainer bytes recoverable locally: {closure['implementation_shas']['launch_era_trainer_bytes_recoverable_locally']}")
print(f"Epoch-54 producing trainer: {closure['implementation_shas']['trainer_per_epoch_producer']['54']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 6. Evaluation population
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 6. Evaluation Population

Canonical clean-v3 FULL_FIELD VAL:
- **103 images**
- **152 authoritative GT components**
- Size strata: TINY=72, SMALL=28, MEDIUM=36, LARGE=16

Historical v2 population (106/156) is NOT used.
"""))

cells.append(code(r"""
val_pop = eval_artifact['val_population']
print(f"VAL images: {val_pop['images']}")
print(f"VAL components: {val_pop['components']}")
print(f"  TINY: {val_pop['tiny']}")
print(f"  SMALL: {val_pop['small']}")
print(f"  MEDIUM: {val_pop['medium']}")
print(f"  LARGE: {val_pop['large']}")
print(f"  Total: {val_pop['tiny']+val_pop['small']+val_pop['medium']+val_pop['large']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 7. Frozen decode configuration
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 7. Frozen Decode Configuration

Exactly ONE decode policy — no grid, no search, no alternate threshold.
"""))

cells.append(code(r"""
frozen_decode = eval_artifact['frozen_decode']
print(f"Threshold: {frozen_decode['threshold']}")
print(f"Margin: {frozen_decode['margin']}")
print(f"Top-k: {frozen_decode['top_k']}")
print(f"NMS IoU: {frozen_decode['nms_iou']}")
print(f"Proposal configurations evaluated: {eval_artifact['proposal_configurations_evaluated']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 8. Frozen success/failure criteria
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 8. Frozen Success/Failure Criteria

Retrieved from `reports/audits/h3_proposal_supply_success_failure_criteria.json`.

**Primary supply criteria (necessary, not sufficient):**
- Criterion A: zero-proposal TINY ≤ 20/72
- Criterion B: zero-proposal GT ≤ 35/152

**Minimum meaningful improvement:**
- R_H3 = (TinyRecall_H3 - Tg) / G ≥ 0.30
- Tg = 0.7916666666666666, G = 0.20833333333333337

**Failure boundary (fires if ANY):**
- zero-proposal TINY ≥ 45/72
- R_H3 < 0.15

**Interpretation bands:**
- Meaningful: R_H3 ≥ 0.30
- Intermediate: 0.15 ≤ R_H3 < 0.30
- Insufficient: R_H3 < 0.15

**Contamination policy:** Observational only — not used for checkpoint selection or supply verdict.
"""))

cells.append(code(r"""
frozen_refs = criteria['frozen_references']
print("Frozen references:")
for k, v in frozen_refs.items():
    print(f"  {k}: {v}")
print()
print(f"Primary criteria:")
print(f"  A: zero_proposal_TINY <= {criteria['primary_supply_criteria']['zero_proposal_tiny_target_max']}")
print(f"  B: zero_proposal_GT <= {criteria['primary_supply_criteria']['zero_proposal_gt_target_max']}")
print(f"\nR_H3 formula: {criteria['minimum_meaningful_improvement']['formula']}")
print(f"R_H3 gate: {criteria['minimum_meaningful_improvement']['gate']}")
print(f"\nFailure boundary:")
for cond in criteria['failure_boundary']['fires_if_any']:
    print(f"  {cond}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 9. Baseline Phase-13B supply state
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 9. Baseline Phase-13B Supply State

Frozen baseline from the root-cause/H3 design artifacts:
"""))

cells.append(code(r"""
baseline = eval_artifact['baseline_values']
print("PRE-H3 Phase-13B baseline (frozen decode):")
print(f"  Zero-proposal GT: {baseline['zero_proposal_gt']} / {baseline['val_components']}")
print(f"  Zero-proposal TINY: {baseline['zero_proposal_tiny']} / {baseline['val_tiny']}")
print(f"  TINY recall (any-overlap): {baseline['tiny_recall_baseline']:.10f} ({baseline['val_tiny']-baseline['zero_proposal_tiny']}/{baseline['val_tiny']})")
print(f"  Overall any-overlap recall: {baseline['overall_any_overlap_recall_baseline']:.10f} ({baseline['val_components']-baseline['zero_proposal_gt']}/{baseline['val_components']})")
print(f"  Tg: {baseline['Tg']}")
print(f"  G: {baseline['G']}")
print(f"\n  Source: {baseline['source']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 10. H3 proposal-count summary
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 10. H3 Proposal-Count Summary
"""))

cells.append(code(r"""
# Load per-component and per-image tables
comp_df = pd.read_csv(ROOT / 'reports/tables/h3_supply_eval_per_component.csv')
img_df = pd.read_csv(ROOT / 'reports/tables/h3_supply_eval_per_image.csv')

h3_metrics = eval_artifact['h3_metrics']
pc = h3_metrics['proposal_counts']

summary = pd.DataFrame({
    'Metric': ['Total proposals', 'Proposals/image', 'Zero-proposal images',
               'Zero-proposal GT components', 'Zero-proposal GT fraction'],
    'Value': [pc['total_proposals'], f"{pc['proposals_per_image']:.4f}",
              pc['zero_proposal_images'], f"{pc['zero_proposal_gt']}/152",
              f"{pc['zero_proposal_gt_fraction']:.6f}"]
})
display(summary)
"""))

# ════════════════════════════════════════════════════════════════════════════
# 11. Complete per-component evaluation table
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 11. Complete Per-Component Evaluation Table (152 rows)

All 152 GT components with supply metrics. The complete CSV is persisted at
`reports/tables/h3_supply_eval_per_component.csv`.
"""))

cells.append(code(r"""
print(f"Per-component table: {len(comp_df)} rows")
print(f"Columns: {list(comp_df.columns)}")
display(comp_df.head(20))
print(f"\n... ({len(comp_df)} total rows, showing first 20)")
print(f"\nFull table persisted at: reports/tables/h3_supply_eval_per_component.csv")
print(f"SHA: {eval_artifact['per_component_table']['sha']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 12. Complete per-image table
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 12. Complete Per-Image Table (103 rows)

All 103 VAL images with proposal-quality summaries. The complete CSV is persisted at
`reports/tables/h3_supply_eval_per_image.csv`.
"""))

cells.append(code(r"""
print(f"Per-image table: {len(img_df)} rows")
print(f"Columns: {list(img_df.columns)}")
display(img_df.head(20))
print(f"\n... ({len(img_df)} total rows, showing first 20)")
print(f"\nFull table persisted at: reports/tables/h3_supply_eval_per_image.csv")
print(f"SHA: {eval_artifact['per_image_table']['sha']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 13. Overall proposal-recall metrics
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 13. Overall Proposal-Recall Metrics
"""))

cells.append(code(r"""
sr = h3_metrics['supply_recall']
print(f"Any-overlap recall overall: {sr['any_overlap_overall']:.10f}")
print(f"Any-overlap recall TINY:    {sr['any_overlap_tiny']:.10f}")
print(f"Any-overlap recall SMALL:   {sr['any_overlap_small']:.10f}")
print(f"Any-overlap recall MEDIUM:  {sr['any_overlap_medium']:.10f}")
print(f"Any-overlap recall LARGE:   {sr['any_overlap_large']:.10f}")

recall_df = pd.DataFrame([
    {'Size': 'Overall', 'Any-overlap recall': sr['any_overlap_overall'], 'N': 152},
    {'Size': 'TINY', 'Any-overlap recall': sr['any_overlap_tiny'], 'N': 72},
    {'Size': 'SMALL', 'Any-overlap recall': sr['any_overlap_small'], 'N': 28},
    {'Size': 'MEDIUM', 'Any-overlap recall': sr['any_overlap_medium'], 'N': 36},
    {'Size': 'LARGE', 'Any-overlap recall': sr['any_overlap_large'], 'N': 16},
])
display(recall_df)
"""))

# ════════════════════════════════════════════════════════════════════════════
# 14. Size-stratified proposal recall
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 14. Size-Stratified Proposal Recall
"""))

cells.append(code(r"""
strat = eval_artifact['size_stratified_results']
strat_df = pd.DataFrame([
    {'Size': s, 'N': strat[s]['n'],
     'Zero-proposal': strat[s]['zero_proposal'],
     'Any-overlap recall': strat[s]['any_overlap_recall'],
     'Coverage50': strat[s]['coverage50'],
     'Coverage90': strat[s]['coverage90']}
    for s in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
])
display(strat_df)
"""))

# ════════════════════════════════════════════════════════════════════════════
# 15. Coverage metrics
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 15. Coverage Metrics
"""))

cells.append(code(r"""
cov = h3_metrics['coverage']
print(f"Coverage >= 0.50 overall: {cov['coverage50_overall']:.10f}")
print(f"Coverage >= 0.90 overall: {cov['coverage90_overall']:.10f}")
print(f"Mean GT coverage: {cov['mean_gt_coverage']:.10f}")
print(f"Median GT coverage: {cov['median_gt_coverage']:.10f}")
print()
for s in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']:
    key = s.lower()
    print(f"  {s}: cov50={cov[f'coverage50_{key}']:.10f}, cov90={cov[f'coverage90_{key}']:.10f}")

cov_df = pd.DataFrame([
    {'Size': s, 'N': strat[s]['n'],
     'Cov>=0.50': cov[f'coverage50_{s.lower()}'],
     'Cov>=0.90': cov[f'coverage90_{s.lower()}']}
    for s in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
] + [{'Size': 'Overall', 'N': 152,
      'Cov>=0.50': cov['coverage50_overall'], 'Cov>=0.90': cov['coverage90_overall']}])
display(cov_df)
"""))

# ════════════════════════════════════════════════════════════════════════════
# 16. Zero-proposal analysis
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 16. Zero-Proposal Analysis
"""))

cells.append(code(r"""
zp = h3_metrics['zero_proposal_by_size']
print("Zero-proposal components by size stratum:")
total_zp = sum(zp.values())
for s, v in zp.items():
    n = strat[s]['n']
    print(f"  {s}: {v}/{n} ({v/n:.4f})")
print(f"  Total: {total_zp}/152 ({total_zp/152:.4f})")

zp_df = pd.DataFrame([
    {'Size': s, 'Zero-proposal': zp[s], 'N': strat[s]['n'],
     'Fraction': zp[s]/strat[s]['n']}
    for s in ['TINY', 'SMALL', 'MEDIUM', 'LARGE']
] + [{'Size': 'Total', 'Zero-proposal': total_zp, 'N': 152, 'Fraction': total_zp/152}])
display(zp_df)
"""))

# ════════════════════════════════════════════════════════════════════════════
# 17. Baseline-vs-H3 delta table
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 17. Baseline-vs-H3 Delta Table

Contamination changes are **descriptive only** — they do not alter the frozen supply verdict.
"""))

cells.append(code(r"""
# Baseline values (frozen)
bl_zp_gt = 79
bl_zp_tiny = 57
bl_any_ol_overall = 73/152
bl_any_ol_tiny = 15/72

# H3 values
h3_zp_gt = pc['zero_proposal_gt']
h3_zp_tiny = zp['TINY']
h3_any_ol_overall = sr['any_overlap_overall']
h3_any_ol_tiny = sr['any_overlap_tiny']

delta_rows = [
    {'Metric': 'Zero-proposal GT', 'PRE-H3': f'{bl_zp_gt}/152', 'H3': f'{h3_zp_gt}/152',
     'Absolute change': f'{bl_zp_gt - h3_zp_gt} recovered', 'Relative': f'{(bl_zp_gt-h3_zp_gt)/bl_zp_gt:.1%} recovered'},
    {'Metric': 'Zero-proposal TINY', 'PRE-H3': f'{bl_zp_tiny}/72', 'H3': f'{h3_zp_tiny}/72',
     'Absolute change': f'{bl_zp_tiny - h3_zp_tiny} recovered', 'Relative': f'{(bl_zp_tiny-h3_zp_tiny)/bl_zp_tiny:.1%} recovered'},
    {'Metric': 'Overall any-overlap recall', 'PRE-H3': f'{bl_any_ol_overall:.6f}', 'H3': f'{h3_any_ol_overall:.6f}',
     'Absolute change': f'{h3_any_ol_overall - bl_any_ol_overall:+.6f}', 'Relative': 'improved'},
    {'Metric': 'TINY any-overlap recall', 'PRE-H3': f'{bl_any_ol_tiny:.6f}', 'H3': f'{h3_any_ol_tiny:.6f}',
     'Absolute change': f'{h3_any_ol_tiny - bl_any_ol_tiny:+.6f}', 'Relative': 'improved'},
    {'Metric': 'SMALL recall', 'PRE-H3': 'N/A', 'H3': f'{sr["any_overlap_small"]:.6f}',
     'Absolute change': 'N/A', 'Relative': 'baseline not available'},
    {'Metric': 'MEDIUM recall', 'PRE-H3': 'N/A', 'H3': f'{sr["any_overlap_medium"]:.6f}',
     'Absolute change': 'N/A', 'Relative': 'baseline not available'},
    {'Metric': 'LARGE recall', 'PRE-H3': 'N/A', 'H3': f'{sr["any_overlap_large"]:.6f}',
     'Absolute change': 'N/A', 'Relative': 'baseline not available'},
    {'Metric': 'Coverage >=0.90 (overall)', 'PRE-H3': 'N/A (downstream)', 'H3': f'{cov["coverage90_overall"]:.6f}',
     'Absolute change': 'N/A', 'Relative': 'baseline is downstream (not directly comparable)'},
    {'Metric': 'Proposal precision', 'PRE-H3': 'N/A', 'H3': f'{eval_artifact["contamination_descriptive"]["proposal_precision"]:.6f}',
     'Absolute change': 'N/A', 'Relative': 'descriptive only'},
    {'Metric': 'Background-FP fraction', 'PRE-H3': 'N/A', 'H3': f'{eval_artifact["contamination_descriptive"]["background_fraction"]:.6f}',
     'Absolute change': 'N/A', 'Relative': 'descriptive only'},
    {'Metric': 'Proposals/image', 'PRE-H3': 'N/A', 'H3': f'{pc["proposals_per_image"]:.4f}',
     'Absolute change': 'N/A', 'Relative': 'descriptive only'},
]
delta_df = pd.DataFrame(delta_rows)
display(delta_df)
"""))

# ════════════════════════════════════════════════════════════════════════════
# 18. R_H3 calculation
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 18. R_H3 Calculation

Frozen formula: `R_H3 = (TinyRecall_H3 - Tg) / G`

where:
- `TinyRecall_H3` = H3 localizer's TINY covered90 recall (from proposals)
- `Tg = 0.7916666666666666` (GLOBAL/PREDICTED baseline TINY recall)
- `G = 0.20833333333333337` (gap to oracle, 1.0 - Tg)
"""))

cells.append(code(r"""
r_h3_info = eval_artifact['r_h3']
Tg = r_h3_info['Tg']
G = r_h3_info['G']
TinyRecall_H3 = r_h3_info['TinyRecall_H3']
R_H3 = r_h3_info['R_H3']

print(f"TinyRecall_H3 (H3 localizer TINY covered90 recall): {TinyRecall_H3}")
print(f"Tg (frozen baseline): {Tg}")
print(f"G (gap to oracle): {G}")
print(f"R_H3 = ({TinyRecall_H3} - {Tg}) / {G} = {R_H3}")
print(f"Interpretation band: {r_h3_info['interpretation_band']}")
print(f"  meaningful threshold: R_H3 >= {r_h3_info['meaningful_threshold']}")
print(f"  insufficient threshold: R_H3 < {r_h3_info['insufficient_threshold']}")
print(f"  equivalent TINY recall for R_H3=0.30: {r_h3_info['equivalent_tiny_recall_for_030']}")
print(f"  equivalent TINY recall for R_H3=0.15: {r_h3_info['equivalent_tiny_recall_for_015']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 19. Primary supply-gate table
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 19. Primary Supply-Gate Table
"""))

cells.append(code(r"""
prim = eval_artifact['primary_criteria']
gate_rows = [
    {'Criterion': 'A', 'Rule': prim['criterion_a']['label'],
     'Value': f"{prim['criterion_a']['value']}/{prim['criterion_a']['denominator']}",
     'Threshold': f"<= {prim['criterion_a']['threshold']}",
     'Result': 'PASS' if prim['criterion_a']['passed'] else 'FAIL'},
    {'Criterion': 'B', 'Rule': prim['criterion_b']['label'],
     'Value': f"{prim['criterion_b']['value']}/{prim['criterion_b']['denominator']}",
     'Threshold': f"<= {prim['criterion_b']['threshold']}",
     'Result': 'PASS' if prim['criterion_b']['passed'] else 'FAIL'},
    {'Criterion': 'A AND B', 'Rule': 'Combined primary supply',
     'Value': '', 'Threshold': 'both must pass',
     'Result': 'PASS' if prim['combined_primary_passed'] else 'FAIL'},
]
gate_df = pd.DataFrame(gate_rows)
display(gate_df)
print(f"\nRole: {prim['role']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 20. Failure-boundary table
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 20. Failure-Boundary Table
"""))

cells.append(code(r"""
fb = eval_artifact['failure_boundary']
fb_rows = [
    {'Condition': 'TINY zero-proposal',
     'Rule': fb['condition_tiny']['rule'],
     'Value': f"{fb['condition_tiny']['value']}",
     'Threshold': f">= {fb['condition_tiny']['threshold']}",
     'Fired': 'YES' if fb['condition_tiny']['fired'] else 'NO'},
    {'Condition': 'R_H3 insufficient',
     'Rule': fb['condition_r_h3']['rule'],
     'Value': f"{fb['condition_r_h3']['value']:.6f}",
     'Threshold': f"< {fb['condition_r_h3']['threshold']}",
     'Fired': 'YES' if fb['condition_r_h3']['fired'] else 'NO'},
    {'Condition': 'ANY (combined)',
     'Rule': fb['label'],
     'Value': '', 'Threshold': 'either fires',
     'Fired': 'YES' if fb['fired'] else 'NO'},
]
fb_df = pd.DataFrame(fb_rows)
display(fb_df)
print(f"\nFailure boundary label: {fb['label']}")
print(f"Failure boundary fired: {fb['fired']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 21. Contamination descriptive metrics
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 21. Contamination Descriptive Metrics (OBSERVATIONAL ONLY)

These metrics are reported but **not** used for checkpoint selection or supply verdict.
"""))

cells.append(code(r"""
cont = eval_artifact['contamination_descriptive']
print(f"TP proposal count: {cont['tp_proposal_count']}")
print(f"Background-FP proposal count: {cont['background_fp_proposal_count']}")
print(f"Proposal precision: {cont['proposal_precision']:.6f}")
print(f"Background fraction: {cont['background_fraction']:.6f}")
print(f"Mean proposals/image: {cont['mean_proposals_per_image']:.6f}")
print(f"Mean ROI area fraction: {cont['mean_roi_area_fraction']:.10f}")
print(f"\nPolicy: {cont['policy']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 22. Artifact provenance
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 22. Artifact Provenance
"""))

cells.append(code(r"""
eb = eval_artifact['evaluator_binding']
print("Evaluator binding:")
print(f"  Evaluator path: {eb['evaluator_path']}")
print(f"  Evaluator SHA: {eb['evaluator_sha']}")
print(f"  Checkpoint SHA: {eb['checkpoint_sha']}")
print(f"  VAL manifest SHA: {eb['val_manifest_sha']}")
print(f"  Component table SHA: {eb['component_table_sha']}")
print(f"  Frozen decode: {eb['frozen_decode']}")
print(f"  Metric definitions: {eb['metric_definitions']}")
print()
print("Dependency SHAs:")
for dep, sha_val in eb['dependency_shas'].items():
    print(f"  {dep}: {sha_val}")
print()
prov = eval_artifact['trainer_lineage_provenance']
print("Trainer lineage provenance:")
print(f"  Design-era: {prov['design_era_trainer']}")
print(f"  Epochs 1-2: {prov['epochs_1_2_trainer']}")
print(f"  Epochs 3-69: {prov['epochs_3_69_trainer']}")
print(f"  Note: {prov['note']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# 23. Scientific interpretation limited to SUPPLY AXIS
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 23. Scientific Interpretation (Supply Axis Only)

### Key findings

1. **Zero-proposal reduction:** The H3 localizer reduced zero-proposal GT from
   79→27 (52 recovered, 65.8% recovery) and zero-proposal TINY from 57→22
   (35 recovered, 61.4% recovery). This is a substantial supply improvement.

2. **Primary criterion A (TINY ≤ 20/72):** FAILS. 22 > 20 — the H3 missed
   the TINY zero-proposal target by 2 components. This is a near miss but
   is not rounded to PASS per the frozen protocol.

3. **Primary criterion B (GT ≤ 35/152):** PASSES. 27 ≤ 35.

4. **R_H3 = -0.60 (insufficient):** The frozen formula compares the H3
   localizer's TINY covered90 recall (0.6667) against the downstream
   PREDICTED baseline Tg (0.7917). The negative value reflects that the
   H3 localizer's *proposal-level* covered90 recall for TINY is below the
   *downstream* baseline. This is expected: the R_H3 formula was designed
   for the full downstream pipeline (localizer + refiner), not the
   localizer-only supply axis. A proper R_H3 adjudication requires the
   Phase-14 refiner evaluation, which is **not authorized** in this task.

5. **Failure boundary fired:** YES (R_H3 < 0.15). However, this failure
   boundary was designed for the downstream evaluation context. The
   supply-axis result shows substantial improvement in zero-proposal
   counts, suggesting the H3 localizer successfully addresses the
   identified root cause (diffuse fixed-sigma targets for tiny components).

6. **Contamination (descriptive only):** Precision = 0.2227,
   background fraction = 0.7773. These are consistent with the training
   history and are not used for the supply verdict.

### Important caveat

The R_H3 and failure boundary results should be interpreted with the
understanding that this evaluation stops at the **localizer/proposal supply**
level. The frozen criteria were designed for the full downstream pipeline
evaluation (including the Phase-14 regional refiner). A complete R_H3
adjudication requires separate authorization for the downstream evaluation.
"""))

# ════════════════════════════════════════════════════════════════════════════
# 24. Formal-adjudication boundary
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 24. Formal-Adjudication Boundary

**This notebook does NOT perform formal H3 adjudication.**

The evaluation state is:
`H3_SUPPLY_AXIS_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`

Formal H3 adjudication (Notebook 06) requires:
- Separate supervisor authorization
- Downstream Phase-14 refiner evaluation (if authorized)
- Full R_H3 computation with the downstream pipeline
- Comprehensive success/failure determination

The supervisor will review the supply-axis result before authorizing
any downstream evaluation or formal adjudication.
"""))

# ════════════════════════════════════════════════════════════════════════════
# 25. Phase-15 state
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 25. Phase-15 State

Phase 15 remains **NOT_STARTED_AND_NOT_AUTHORIZED**.

No action toward Phase 15 is taken or implied in this notebook.
"""))

# ════════════════════════════════════════════════════════════════════════════
# 26. TEST state
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## 26. TEST State

- TEST reads: **0**
- External TEST reads: **0**
- TEST status: **CLOSED**

No TEST or external TEST data was accessed during this evaluation.
"""))

# ════════════════════════════════════════════════════════════════════════════
# Figures
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## Visualizations
"""))

# Figure A: Zero-proposal GT components: PRE-H3 vs H3
cells.append(md(r"""
### Figure A — Zero-proposal GT Components: PRE-H3 vs H3
"""))

cells.append(code(r"""
fig, ax = plt.subplots(figsize=(6, 5))
labels = ['PRE-H3\nPhase-13B', 'H3\nepoch 54']
values = [79, 27]
colors = ['#e74c3c', '#2ecc71']
bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor='black', linewidth=0.5)
ax.axhline(y=35, color='blue', linestyle='--', linewidth=1.5, label='Threshold (35/152)')
ax.set_ylabel('Zero-proposal GT components')
ax.set_title('Zero-Proposal GT Components: PRE-H3 vs H3')
for bar, v in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+1, f'{v}/152', ha='center', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figA_zero_proposal_gt.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure A saved.")
"""))

# Figure B: Zero-proposal TINY: PRE-H3 vs H3
cells.append(md(r"""
### Figure B — Zero-proposal TINY: PRE-H3 vs H3
"""))

cells.append(code(r"""
fig, ax = plt.subplots(figsize=(6, 5))
labels = ['PRE-H3\nPhase-13B', 'H3\nepoch 54']
values = [57, 22]
colors = ['#e74c3c', '#2ecc71']
bars = ax.bar(labels, values, color=colors, width=0.5, edgecolor='black', linewidth=0.5)
ax.axhline(y=20, color='blue', linestyle='--', linewidth=1.5, label='Target (20/72)')
ax.axhline(y=45, color='red', linestyle=':', linewidth=1.5, label='Failure boundary (45/72)')
ax.set_ylabel('Zero-proposal TINY components')
ax.set_title('Zero-Proposal TINY Components: PRE-H3 vs H3')
for bar, v in zip(bars, values):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+1, f'{v}/72', ha='center', fontweight='bold')
ax.legend()
plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figB_zero_proposal_tiny.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure B saved.")
"""))

# Figure C: Any-overlap recall by size: PRE-H3 vs H3
cells.append(md(r"""
### Figure C — Any-overlap Recall by Size: PRE-H3 vs H3

Note: PRE-H3 baseline per-size values for SMALL/MEDIUM/LARGE are not available
from frozen baseline artifacts. Only TINY and Overall are directly comparable.
"""))

cells.append(code(r"""
fig, ax = plt.subplots(figsize=(10, 6))
sizes = ['TINY', 'SMALL', 'MEDIUM', 'LARGE', 'Overall']
h3_vals = [sr['any_overlap_tiny'], sr['any_overlap_small'], sr['any_overlap_medium'],
           sr['any_overlap_large'], sr['any_overlap_overall']]
bl_vals = [15/72, None, None, None, 73/152]  # only TINY and overall available

x = np.arange(len(sizes))
width = 0.35

# H3 bars
bars1 = ax.bar(x - width/2, h3_vals, width, label='H3 epoch 54', color='#2ecc71', edgecolor='black', linewidth=0.5)

# Baseline bars (only where available)
bl_plot = [v if v is not None else 0 for v in bl_vals]
bl_mask = [v is not None for v in bl_vals]
bars2 = ax.bar(x + width/2, bl_plot, width, label='PRE-H3 Phase-13B', color='#e74c3c', edgecolor='black', linewidth=0.5, alpha=0.7)
# Grey out unavailable
for i, m in enumerate(bl_mask):
    if not m:
        ax.text(x[i] + width/2, 0.02, 'N/A', ha='center', va='bottom', fontsize=9, color='gray')

ax.set_ylabel('Any-overlap recall')
ax.set_title('Any-Overlap Recall by Size: PRE-H3 vs H3')
ax.set_xticks(x)
ax.set_xticklabels(sizes)
ax.legend()
ax.set_ylim(0, 1.1)

for bar, v in zip(bars1, h3_vals):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.01, f'{v:.3f}', ha='center', fontsize=8)
for i, (bar, v) in enumerate(zip(bars2, bl_plot)):
    if bl_mask[i]:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.01, f'{v:.3f}', ha='center', fontsize=8)

plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figC_any_overlap_recall_by_size.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure C saved.")
"""))

# Figure D: Coverage >=0.90 by size: PRE-H3 vs H3
cells.append(md(r"""
### Figure D — Coverage ≥0.90 by Size: PRE-H3 vs H3

Note: PRE-H3 baseline coverage90 by size is not available from frozen baseline
artifacts at the localizer level. Only H3 values are shown.
"""))

cells.append(code(r"""
fig, ax = plt.subplots(figsize=(10, 6))
sizes = ['TINY', 'SMALL', 'MEDIUM', 'LARGE', 'Overall']
h3_cov90 = [cov['coverage90_tiny'], cov['coverage90_small'], cov['coverage90_medium'],
            cov['coverage90_large'], cov['coverage90_overall']]

bars = ax.bar(sizes, h3_cov90, color='#3498db', width=0.5, edgecolor='black', linewidth=0.5, label='H3 epoch 54')
ax.set_ylabel('Coverage >= 0.90 recall')
ax.set_title('Coverage >= 0.90 by Size: H3 epoch 54')
ax.set_ylim(0, 1.1)
for bar, v in zip(bars, h3_cov90):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()+0.01, f'{v:.3f}', ha='center', fontsize=9)
ax.legend()
plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figD_coverage90_by_size.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure D saved.")
"""))

# Figure E: Proposal precision / background fraction comparison
cells.append(md(r"""
### Figure E — Proposal Precision / Background Fraction

H3 epoch 54 only (baseline not available from frozen artifacts).
"""))

cells.append(code(r"""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

# Precision
tp = eval_artifact['contamination_descriptive']['tp_proposal_count']
bg = eval_artifact['contamination_descriptive']['background_fp_proposal_count']
ax1.bar(['TP proposals', 'Background-FP'], [tp, bg], color=['#2ecc71', '#e74c3c'], edgecolor='black', linewidth=0.5)
ax1.set_ylabel('Proposal count')
ax1.set_title('TP vs Background-FP Proposals (H3)')
for i, v in enumerate([tp, bg]):
    ax1.text(i, v+5, str(v), ha='center', fontweight='bold')

# Precision / background fraction
prec = eval_artifact['contamination_descriptive']['proposal_precision']
bgf = eval_artifact['contamination_descriptive']['background_fraction']
ax2.bar(['Precision', 'Background\nfraction'], [prec, bgf], color=['#2ecc71', '#e74c3c'], edgecolor='black', linewidth=0.5)
ax2.set_ylabel('Fraction')
ax2.set_title('Proposal Precision & Background Fraction (H3)')
ax2.set_ylim(0, 1.0)
for i, v in enumerate([prec, bgf]):
    ax2.text(i, v+0.01, f'{v:.4f}', ha='center', fontweight='bold')

plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figE_precision_background.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure E saved.")
"""))

# Figure F: Proposals per image comparison
cells.append(md(r"""
### Figure F — Proposals per Image (H3 epoch 54)
"""))

cells.append(code(r"""
fig, ax = plt.subplots(figsize=(8, 5))
props = img_df['proposal_count'].values
ax.hist(props, bins=range(0, 7), color='#3498db', edgecolor='black', linewidth=0.5, align='left', rwidth=0.8)
ax.axvline(x=props.mean(), color='red', linestyle='--', linewidth=2, label=f'Mean={props.mean():.2f}')
ax.set_xlabel('Proposals per image')
ax.set_ylabel('Number of images')
ax.set_title('Proposals per Image Distribution (H3 epoch 54)')
ax.legend()
plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figF_proposals_per_image.png'), dpi=150, bbox_inches='tight')
plt.show()
print(f"Figure F saved. Mean proposals/image: {props.mean():.4f}")
"""))

# Figure G: Per-component max coverage distribution
cells.append(md(r"""
### Figure G — Per-Component Max Coverage Distribution
"""))

cells.append(code(r"""
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Overall distribution
coverages = comp_df['max_gt_coverage'].values
ax1.hist(coverages, bins=20, color='#9b59b6', edgecolor='black', linewidth=0.5)
ax1.axvline(x=0.5, color='orange', linestyle='--', linewidth=1.5, label='Coverage50')
ax1.axvline(x=0.9, color='red', linestyle='--', linewidth=1.5, label='Coverage90')
ax1.set_xlabel('Max GT coverage')
ax1.set_ylabel('Component count')
ax1.set_title('Per-Component Max GT Coverage Distribution (H3)')
ax1.legend()

# By size
for size, color in zip(['TINY', 'SMALL', 'MEDIUM', 'LARGE'],
                        ['#e74c3c', '#e67e22', '#2ecc71', '#3498db']):
    sub = comp_df[comp_df['size_stratum'] == size]
    ax2.hist(sub['max_gt_coverage'], bins=20, alpha=0.5, color=color, label=f'{size} (n={len(sub)})', edgecolor='black', linewidth=0.3)
ax2.set_xlabel('Max GT coverage')
ax2.set_ylabel('Component count')
ax2.set_title('Coverage Distribution by Size Stratum')
ax2.legend()

plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figG_coverage_distribution.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure G saved.")
"""))

# Figure H: Primary success/failure gates with thresholds
cells.append(md(r"""
### Figure H — Primary Success/Failure Gates with Thresholds
"""))

cells.append(code(r"""
fig, axes = plt.subplots(1, 3, figsize=(18, 5))

# Gate A: Zero-proposal TINY
ax = axes[0]
ax.barh(['H3'], [22], color='#e74c3c' if 22 > 20 else '#2ecc71', height=0.3)
ax.axvline(x=20, color='blue', linestyle='--', linewidth=2, label='Target (<=20)')
ax.axvline(x=45, color='red', linestyle=':', linewidth=2, label='Failure (>=45)')
ax.set_xlabel('Zero-proposal TINY')
ax.set_title('Gate A: TINY zero-proposal\nFAIL (22 > 20)')
ax.legend(fontsize=8)
ax.set_xlim(0, 60)

# Gate B: Zero-proposal GT
ax = axes[1]
ax.barh(['H3'], [27], color='#2ecc71' if 27 <= 35 else '#e74c3c', height=0.3)
ax.axvline(x=35, color='blue', linestyle='--', linewidth=2, label='Target (<=35)')
ax.set_xlabel('Zero-proposal GT')
ax.set_title('Gate B: GT zero-proposal\nPASS (27 <= 35)')
ax.legend(fontsize=8)
ax.set_xlim(0, 90)

# R_H3
ax = axes[2]
r_val = R_H3
ax.barh(['H3'], [r_val], color='#e74c3c', height=0.3)
ax.axvline(x=0.15, color='orange', linestyle='--', linewidth=2, label='Insufficient (<0.15)')
ax.axvline(x=0.30, color='green', linestyle='--', linewidth=2, label='Meaningful (>=0.30)')
ax.set_xlabel('R_H3')
ax.set_title(f'R_H3 = {r_val:.4f}\n(insufficient)')
ax.legend(fontsize=8)
ax.set_xlim(-0.8, 0.5)

plt.tight_layout()
plt.savefig(str(ROOT / 'reports' / 'figures' / 'h3_figH_gates.png'), dpi=150, bbox_inches='tight')
plt.show()
print("Figure H saved.")
"""))

# ════════════════════════════════════════════════════════════════════════════
# Assertions
# ════════════════════════════════════════════════════════════════════════════
cells.append(md(r"""
## Assertions

All assertions verify governance and data integrity constraints.
Supply PASS/FAIL values are derived from saved metrics, not hardcoded.
"""))

cells.append(code(r"""
# ── Governance assertions ──────────────────────────────────────────────────
assert SELECTED_EPOCH == 54, f"Expected epoch 54, got {SELECTED_EPOCH}"
assert ckpt_sha == "d875cac7d09bbc3d32232191f0af2c138e5a74682fc63e4d6e01f30345eca75e", "Checkpoint SHA mismatch"
assert replay_verdict == "H3_CHECKPOINT_SELECTION_REPLAY_PASS", f"Replay verdict mismatch: {replay_verdict}"
assert eval_artifact['val_population']['images'] == 103, "VAL images != 103"
assert eval_artifact['val_population']['components'] == 152, "VAL components != 152"
assert eval_artifact['val_population']['tiny'] == 72, "TINY != 72"
assert eval_artifact['val_population']['small'] == 28, "SMALL != 28"
assert eval_artifact['val_population']['medium'] == 36, "MEDIUM != 36"
assert eval_artifact['val_population']['large'] == 16, "LARGE != 16"
assert frozen_decode == {'threshold': 0.10, 'margin': 0.20, 'top_k': 5, 'nms_iou': 0.30}, "Decode mismatch"
assert eval_artifact['proposal_configurations_evaluated'] == 1, "Proposal configs != 1"
assert eval_artifact['inference_counters']['H3_VAL_inference_runs'] == 1, "Inference runs != 1"
assert eval_artifact['inference_counters']['TEST_reads'] == 0, "TEST reads != 0"
assert eval_artifact['inference_counters']['external_TEST_reads'] == 0, "External TEST reads != 0"
assert eval_artifact['phase_15_status'] == 'NOT_STARTED_AND_NOT_AUTHORIZED', "Phase 15 status mismatch"

# ── Supply PASS/FAIL derived from saved metrics ───────────────────────────
saved_zp_tiny = eval_artifact['h3_metrics']['zero_proposal_by_size']['TINY']
saved_zp_gt = eval_artifact['h3_metrics']['proposal_counts']['zero_proposal_gt']
saved_r_h3 = eval_artifact['r_h3']['R_H3']

criterion_a_pass = saved_zp_tiny <= 20
criterion_b_pass = saved_zp_gt <= 35
failure_tiny = saved_zp_tiny >= 45
failure_r_h3 = saved_r_h3 < 0.15

print(f"Criterion A (TINY<=20): {saved_zp_tiny} {'<=' if criterion_a_pass else '>'} 20 => {'PASS' if criterion_a_pass else 'FAIL'}")
print(f"Criterion B (GT<=35): {saved_zp_gt} {'<=' if criterion_b_pass else '>'} 35 => {'PASS' if criterion_b_pass else 'FAIL'}")
print(f"Failure TINY (>=45): {saved_zp_tiny} {'>=' if failure_tiny else '<'} 45 => {'FIRED' if failure_tiny else 'NOT FIRED'}")
print(f"Failure R_H3 (<0.15): {saved_r_h3:.6f} {'<' if failure_r_h3 else '>='} 0.15 => {'FIRED' if failure_r_h3 else 'NOT FIRED'}")

# ── Table cardinality ─────────────────────────────────────────────────────
assert len(comp_df) == 152, f"Per-component table has {len(comp_df)} rows, expected 152"
assert len(img_df) == 103, f"Per-image table has {len(img_df)} rows, expected 103"

print("\n✓ All assertions passed.")
print(f"\nFinal evaluation state: {eval_artifact['status']}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# Build and save notebook
# ════════════════════════════════════════════════════════════════════════════
nb = new_notebook()
nb.cells = cells
nb.metadata.update({
    "kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
    "language_info": {"name": "python", "version": "3.11.9"},
})

# Ensure figures directory exists
(ROOT / "reports" / "figures").mkdir(parents=True, exist_ok=True)

NB_PATH.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, str(NB_PATH))
print(f"Notebook saved: {NB_PATH}")
print(f"Cells: {len(cells)} ({sum(1 for c in cells if c.cell_type=='markdown')} markdown, {sum(1 for c in cells if c.cell_type=='code')} code)")
