"""Build the Phase-13 Part-1D-B reviewer notebook (READ-ONLY, no inference).

Reads only the frozen Part-1D-B tables and audit artifacts. Executes no model code.
"""
from __future__ import annotations

import json
from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(r"D:\Softfors\jup")
OUT = (ROOT / "notebooks" / "phasewise" / "phase_13_predicted_roi_localization"
       / "phase13_clean_v3_predicted_region_segmentation_analysis.ipynb")

cells = []


def md(t):
    cells.append(new_markdown_cell(t))


def code(t):
    cells.append(new_code_cell(t))


# ---------------------------------------------------------------- 1
md("""# PHASE-13 PART-1D-B — PREDICTED-REGION SEGMENTATION ANALYSIS (REVIEWER)

**READ-ONLY.** This notebook performs **no inference**, constructs **no model**, requests **no CUDA**,
creates **no optimizer**, and **never touches TEST**. It reads only the frozen Part-1D-B tables and
audit artifacts produced by the authorized Part-1D-B inference run.

- run id: `phase13_part1d_b_predicted_region_clean_v3`
- manifest `phase4_v3` · taxonomy `kub_size_clean_v3_v1` · TEST **LOCKED**
- primary variant: **`PREDICTED_REGION_FLOAT_GLOBAL_RETAINED`**
- comparators: `GLOBAL_NATIVE` (reproduced in Part-1D-B) and `ORACLE_FLOAT_GLOBAL_RETAINED`
  (frozen Phase-12 authoritative table — **not** rerun)

> **Claim discipline.** This notebook reports *descriptive* gain/loss, retention, recovery/loss and
> cross-architecture consistency/heterogeneity. It does **not** issue `GO`, `REVISE_LOCALIZER` or
> `NO_GO`, does not declare a winner / best model / superiority, and makes no statistical or clinical
> superiority claim. The Part-1E-B supervisor gate comes later.""")

code("""import json
import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

pd.set_option('display.width', 220)
pd.set_option('display.max_columns', 200)

ROOT = Path(r'D:\\Softfors\\jup')
TABLES = ROOT / 'reports' / 'tables'
AUDITS = ROOT / 'reports' / 'audits'


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()


def show(df, n=None):
    d = df if n is None else df.head(n)
    print(d.to_string(index=False))
    print(f'[rows shown {len(d)} / {len(df)}]')


case = pd.read_csv(TABLES / 'phase13_part1d_predicted_region_case_model_metrics.csv')
comp = pd.read_csv(TABLES / 'phase13_part1d_predicted_region_component_model_metrics.csv')
summary = pd.read_csv(TABLES / 'phase13_part1d_predicted_region_model_summary.csv')
repro = pd.read_csv(TABLES / 'phase13_part1d_b_global_reproduction_gate.csv')
cohort = pd.read_csv(TABLES / 'phase13_part1d_predicted_region_cohort_summary.csv')
link = pd.read_csv(TABLES / 'phase13_part1d_localization_segmentation_linkage.csv')
cross = pd.read_csv(TABLES / 'phase13_part1d_cross_architecture_summary.csv')
gate = json.loads((AUDITS / 'phase13_regional_integration_gate_criteria_frozen.json').read_text('utf-8'))
r1 = json.loads((AUDITS / 'phase13_part1d_predicted_region_protocol_frozen_r1.json').read_text('utf-8'))
completion = json.loads((AUDITS / 'phase13_part1d_b_predicted_region_evaluation.json').read_text('utf-8'))
print('loaded frozen Part-1D-B artifacts')""")

# ---------------------------------------------------------------- 2
md("""## 2. R1 protocol identity

The Part-1D-B inference executed the **frozen R1** predicted-region protocol. The R1 revision repaired
square/padding crop-restore semantics **before** any inference (material pre-inference implementation
repair); no protocol semantics changed.""")

code("""print('R1 artifact          :', r1['artifact'])
print('R1 status            :', r1['status'])
print('R1 revision          :', r1.get('revision'))
print('primary variant      :', r1['primary_variant'])
print('Part-1D helper SHA   :', r1['static_preflight']['module_sha256'])
print('static tests passed  :', r1['static_preflight']['tests_passed'])
print('R1 protocol SHA-256  :', sha256_file(AUDITS / 'phase13_part1d_predicted_region_protocol_frozen_r1.json'))""")

# ---------------------------------------------------------------- 3
md("""## 3. Prospective gate-criteria identity

The gate criteria were frozen in Part-1E-A **before** any Part-1D-B result existed. They are not
edited by this phase; Part-1D-B only generates evidence for later Part-1E-B adjudication.""")

code("""print('gate artifact                  :', gate['artifact'])
print('gate status                    :', gate['status'])
print('part1d_b_results_inspected     :', gate['part1d_b_results_inspected'])
print('numerical_thresholds_introduced:', gate['numerical_thresholds_introduced'])
print('gate_state                     :', gate['gate_state'])
print('gate dimensions                :', list(gate['dimensions']))
print('gate outcomes                  :', list(gate['outcomes']))
print('gate criteria SHA-256          :', sha256_file(AUDITS / 'phase13_regional_integration_gate_criteria_frozen.json'))""")

# ---------------------------------------------------------------- 4
md("""## 4. Population and checkpoint bindings""")

code("""print('VAL FULL_FIELD cases      :', case['sample_id'].nunique())
print('case-model rows           :', len(case))
print('unique sample x model     :', case[['sample_id', 'model']].drop_duplicates().shape[0])
print('native components         :', comp[['sample_id', 'native_component_id']].drop_duplicates().shape[0])
print('component-model rows      :', len(comp))
print('unique sample/comp/model  :', comp[['sample_id', 'native_component_id', 'model']].drop_duplicates().shape[0])
print('model summary rows        :', len(summary))
print()
print('size strata (component level):')
print(comp.drop_duplicates(['sample_id', 'native_component_id'])['size_stratum'].value_counts().to_string())
print()
print('proposal counts (frozen Part-1C):', sorted(case['proposal_count'].unique()))
print('total frozen proposals           :', int(case.drop_duplicates('sample_id')['proposal_count'].sum()))
print()
for k, v in completion['bindings']['checkpoints'].items():
    print(f'checkpoint {k:<16} {v[\"sha\"]}  best_epoch={v[\"historical_best_epoch\"]}')""")

# ---------------------------------------------------------------- 5
md("""## 5. Global reproduction gate

Stage G reproduced `GLOBAL_NATIVE` for all four architectures before any regional crop inference.
The integrity criterion is the **per-case native Dice** difference against the frozen Phase-12
`GLOBAL_NATIVE` rows; the frozen tolerance is **1e-4** (max absolute). Secondary reproduction fields
(IoU / precision / recall) are reported descriptively — **no new pass threshold is invented** for them.""")

code("""print(repro[['model', 'rows_matched', 'max_abs_dice_diff', 'mean_abs_dice_diff',
             'mean_dice_new', 'mean_dice_phase12', 'mean_abs_iou_diff', 'max_abs_iou_diff',
             'mean_abs_precision_diff', 'mean_abs_recall_diff', 'pass']].to_string(index=False))
print()
print('ALL FOUR PASS :', bool(repro['pass'].all()))
print('tolerance     : 1e-4 (max abs case Dice)')""")

# ---------------------------------------------------------------- 6
md("""## 6. Predicted-region fusion semantics

```
P(x) = R(x)   if U_pred(x)
     = G(x)   otherwise
```

- regional crops compose by **maximum regional probability only**
- `U_pred` = union of the clipped native frozen Part-1C proposal rectangles (never GT-derived)
- **regional REPLACEMENT** inside the support; `max(G, R)` inside the support is **forbidden**
- threshold **0.5** applied only after complete native fusion
- zero-proposal image → `P = G` exactly
- regional crop input/output uses the **R1** square/padding path
  (valid → zero-pad to full `crop_side` → 512 BILINEAR → model → sigmoid → 512 → full square → strip pad → native clip)""")

code("""print('regional crop evaluations per model (frozen):', 494)
print('expected total 494 x 4                       :', 494 * 4)
print('recorded in completion audit                 :', completion['regional_crop_evaluations'])
print('regional_crop_evaluations == 1976            :', completion['regional_crop_evaluations'] == 1976)
print('zero-proposal cases (P = G exactly)          :', int((case.drop_duplicates('sample_id')['proposal_count'] == 0).sum()))""")

# ---------------------------------------------------------------- 7
md("""## 7. GLOBAL / ORACLE / PREDICTED macro results

Descriptive macro means over the 103 VAL FULL_FIELD cases. ORACLE values come from the **frozen
Phase-12 authoritative table** (no oracle rerun). **No winner, no rank.**""")

code("""cols = ['model_display', 'global_macro_dice', 'oracle_macro_dice', 'predicted_macro_dice',
        'global_macro_iou', 'oracle_macro_iou', 'predicted_macro_iou',
        'global_macro_precision', 'oracle_macro_precision', 'predicted_macro_precision',
        'global_macro_recall', 'oracle_macro_recall', 'predicted_macro_recall']
show(summary[cols])""")

# ---------------------------------------------------------------- 8
md("""## 8. Dice oracle-benefit retention

`DELTA_ORACLE_DICE = D_O - D_G` · `DELTA_PRED_DICE = D_P - D_G` ·
`RETENTION_DICE = (D_P - D_G)/(D_O - D_G)` when the denominator > 0.
**Never clipped**; negative / 0..1 / >1 preserved. `ORACLE_GAP_DICE = D_P - D_O`.
Label: `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION` — a descriptive retention quantity, not a gate cutoff.""")

code("""show(summary[['model_display', 'global_macro_dice', 'oracle_macro_dice', 'predicted_macro_dice',
              'DELTA_ORACLE_DICE', 'DELTA_PRED_DICE', 'RETENTION_DICE', 'ORACLE_GAP_DICE']])
print()
print('denominator invalid (RETENTION_DICE is None) :',
      summary['RETENTION_DICE'].isna().sum())""")

# ---------------------------------------------------------------- 9
md("""## 9. IoU / object-recall / FN-reduction retention

All three use `(P - G)/(O - G)`-style gain retention with `N/A` on an invalid denominator.
**An invalid denominator is reported as `N/A` — never a fabricated zero.**""")

code("""show(summary[['model_display', 'iou_gain_retention', 'object_recall_gain_retention',
              'fn_reduction_retention', 'global_object_recall', 'oracle_object_recall',
              'predicted_object_recall']])""")

# ---------------------------------------------------------------- 10
md("""## 10. Global-preservation FP / FN cost

Target recovery must always be read together with the FP / precision cost.""")

code("""show(summary[['model_display', 'mean_fp_delta', 'mean_fn_delta',
              'mean_global_fn_pixels', 'mean_oracle_fn_pixels', 'mean_predicted_fn_pixels']])""")

# ---------------------------------------------------------------- 11
md("""## 11. Case improvement / worsening

Exact deterministic comparison with tolerance `1e-12` (**numerical equality handling only — not a gate
threshold**): improved `> +1e-12` · unchanged `<= 1e-12` · worsened `< -1e-12`.""")

code("""show(summary[['model_display', 'cases_dice_improved', 'cases_dice_unchanged', 'cases_dice_worsened',
              'max_dice_improvement', 'max_dice_worsening']])""")

# ---------------------------------------------------------------- 12
md("""## 12. Component recovery / loss

A component is *detected* iff the binary prediction overlaps the native component by >= 1 pixel.
`GLOBAL_TO_PREDICTED_RECOVERY` = GLOBAL missed AND PREDICTED detected;
`GLOBAL_TO_PREDICTED_LOSS` = GLOBAL detected AND PREDICTED missed.
GLOBAL detection is the Part-1D-B reproduced GLOBAL; the Phase-12 frozen GLOBAL detection flag is also
carried for the ORACLE pairing.""")

code("""show(summary[['model_display', 'component_recoveries', 'component_losses',
              'empty_recoveries', 'new_empty_predictions']])
print()
print('GLOBAL detection flag agreement with frozen Phase-12:',
      int(comp['global_detection_matches_phase12'].sum()), '/', len(comp))
if not comp['global_detection_matches_phase12'].all():
    d = comp[~comp['global_detection_matches_phase12']]
    print('disagreeing rows (reported, not hidden):')
    show(d[['sample_id', 'native_component_id', 'model', 'size_stratum',
            'global_detected', 'global_detected_phase12']])""")

# ---------------------------------------------------------------- 13
md("""## 13. Size-stratified component outcomes

Predeclared strata only: TINY / SMALL / MEDIUM / LARGE.""")

code("""s = cohort[cohort['cohort_dimension'] == 'size_stratum']
show(s[['cohort_value', 'model_display', 'n_components', 'global_detected', 'oracle_detected',
        'predicted_detected', 'GLOBAL_TO_PREDICTED_RECOVERIES', 'GLOBAL_TO_PREDICTED_LOSSES']])""")

# ---------------------------------------------------------------- 14
md("""## 14. hard-Tiny cohort (predeclared)""")

code("""h = cohort[cohort['cohort_dimension'] == 'hard_tiny']
show(h[['model_display', 'n_components', 'global_detected', 'oracle_detected', 'predicted_detected',
        'GLOBAL_TO_PREDICTED_RECOVERIES', 'GLOBAL_TO_PREDICTED_LOSSES']])""")

# ---------------------------------------------------------------- 15
md("""## 15. global-empty cohort (predeclared)""")

code("""ge = cohort[cohort['cohort_dimension'] == 'global_empty_image']
show(ge[['model_display', 'n_components', 'global_detected', 'oracle_detected', 'predicted_detected',
        'GLOBAL_TO_PREDICTED_RECOVERIES', 'GLOBAL_TO_PREDICTED_LOSSES']])""")

# ---------------------------------------------------------------- 16
md("""## 16. multi-component cohort (predeclared)""")

code("""mc = cohort[cohort['cohort_dimension'] == 'multi_component_image']
show(mc[['model_display', 'n_components', 'global_detected', 'oracle_detected', 'predicted_detected',
        'GLOBAL_TO_PREDICTED_RECOVERIES', 'GLOBAL_TO_PREDICTED_LOSSES']])""")

# ---------------------------------------------------------------- 17
md("""## 17. Localization → segmentation linkage

Descriptive association between frozen Part-1C localization coverage and downstream component recovery.
**Not causal proof.** Proposal settings are not tuned here.""")

code("""show(link[['field', 'value', 'model_display', 'n_components', 'recovered', 'recovery_rate',
           'lost', 'lost_rate']])""")

# ---------------------------------------------------------------- 18
md("""## 18. Cross-architecture descriptive consistency

Descriptive counts only — **no model ranking, no winner**.""")

code("""show(cross)
print()
imp = case.pivot_table(index='sample_id', columns='model', values='case_dice_improved', aggfunc='first')
wor = case.pivot_table(index='sample_id', columns='model', values='case_dice_worsened', aggfunc='first')
print('cases where PREDICTED Dice > GLOBAL for all four :', int((imp.sum(axis=1) == 4).sum()))
print('cases non-worse for all four                     :', int((wor.sum(axis=1) == 0).sum()))
print('cases worse for all four                         :', int((wor.sum(axis=1) == 4).sum()))""")

# ---------------------------------------------------------------- 19
md("""## 19. 16-case deterministic gallery (REVIEW ONLY)

The gallery is the **frozen Part-1C selection** — not reselected. Predictions for these cases were
preserved during the same Part-1D-B inference execution, so **no second inference pass** was needed.

`GT = EVALUATION / REVIEW ONLY` · `PROPOSALS = GT-FREE FROZEN PART1C`.
**The gallery cannot determine the gate.**""")

code("""gal = pd.read_csv(TABLES / 'phase13_part1c_gallery_selection.csv')
show(gal)
gdir = ROOT / 'data_cache' / 'phase13_part1d_b_predicted_region_clean_v3' / 'gallery'
print()
print('gallery cases with preserved Part-1D-B outputs:', len([d for d in gdir.iterdir()]) if gdir.exists() else 0)
if gdir.exists():
    print('per-case files:', sorted(p.name for p in (gdir / sorted(d.name for d in gdir.iterdir())[0]).iterdir()))
print()
print('ORACLE visual/prediction artifacts: none regenerated (no oracle rerun authorized).')
print('A valid frozen Phase-12 visual artifact is NOT present in this repository for these 16 cases,')
print('so the ORACLE panel is reported as NOT_AVAILABLE rather than fabricated.')""")

# ---------------------------------------------------------------- 20
md("""## 20. Limitations

- **Oracle is an upper bound, not deployable.** Phase-12 oracle geometry uses GT-derived component
  locations; the predicted path uses frozen GT-free Part-1C proposals at margin 0.20 (oracle used 0.25).
  `PRACTICAL_GT_FREE_ORACLE_BENEFIT_RETENTION` is therefore **not** a pure mechanism-retention measure.
- Single seed (42) per architecture; no paired significance testing was performed, and none is claimed.
- Retention quantities are descriptive; no numerical gate threshold exists by design.
- Component detection uses a >= 1 native pixel overlap rule under 8-connectivity, applied to the frozen
  Phase-12 component identities.
- HD95 invalid entries are explicitly labelled with their reason rather than fabricated.
- `GLOBAL_NATIVE` in this phase is a Part-1D-B reproduction (verified to <= 1e-4 max abs case Dice);
  the ORACLE comparator is the frozen Phase-12 authoritative table.
- The gallery is review-only and carries no gate authority.""")

# ---------------------------------------------------------------- 21
md("""## 21. Explicit gate boundary

| item | state |
|---|---|
| `GO` | **NOT ISSUED** |
| `REVISE_LOCALIZER` | **NOT ISSUED** |
| `NO_GO` | **NOT ISSUED** |
| `REGIONAL_INTEGRATION_GATE_AFTER_PHASE13` | **NOT_DECIDED** |
| regional mechanism promoted | **NO** |
| Phase 14 | **NOT_STARTED** |
| TEST reads | **0** |

The regional-integration gate belongs to a separate supervisor-reviewed **Part 1E-B**. Retrofit
criteria after results are **forbidden**.""")

code("""print('gate_state                        :', gate['gate_state'])
print('gate verdict issued by Part-1D-B  : NOT_ISSUED')
print('regional mechanism promoted       : NO')
print('Part1E-B gate adjudication        :', completion['continuity']['phase13_part1e_b_gate_adjudication'])
print('Phase14                           :', completion['continuity']['phase14'])
print('TEST reads                        :', completion['counters']['test_reads'])""")

# ---------------------------------------------------------------- 22
md("""## 22. Artifact SHA registry""")

code("""reg = {
    'phase13_part1d_predicted_region_protocol_frozen_r1.json': AUDITS / 'phase13_part1d_predicted_region_protocol_frozen_r1.json',
    'phase13_regional_integration_gate_criteria_frozen.json': AUDITS / 'phase13_regional_integration_gate_criteria_frozen.json',
    'phase13_part1d_b_inference_start.json': AUDITS / 'phase13_part1d_b_inference_start.json',
    'phase13_part1d_b_global_reproduction.json': AUDITS / 'phase13_part1d_b_global_reproduction.json',
    'phase13_part1d_b_predicted_region_evaluation.json': AUDITS / 'phase13_part1d_b_predicted_region_evaluation.json',
    'phase13_part1d_predicted_region_case_model_metrics.csv': TABLES / 'phase13_part1d_predicted_region_case_model_metrics.csv',
    'phase13_part1d_predicted_region_component_model_metrics.csv': TABLES / 'phase13_part1d_predicted_region_component_model_metrics.csv',
    'phase13_part1d_predicted_region_model_summary.csv': TABLES / 'phase13_part1d_predicted_region_model_summary.csv',
    'phase13_part1d_b_global_reproduction_gate.csv': TABLES / 'phase13_part1d_b_global_reproduction_gate.csv',
    'phase13_part1d_cross_architecture_summary.csv': TABLES / 'phase13_part1d_cross_architecture_summary.csv',
    'phase13_part1d_predicted_region_cohort_summary.csv': TABLES / 'phase13_part1d_predicted_region_cohort_summary.csv',
    'phase13_part1d_localization_segmentation_linkage.csv': TABLES / 'phase13_part1d_localization_segmentation_linkage.csv',
}
for k, p in reg.items():
    print(f'{sha256_file(p)}  {k}' if p.exists() else f'MISSING  {k}')""")

# ---------------------------------------------------------------- appendix
md("""## Appendix — complete frozen tables

Deterministic text rendering of the complete frozen tables (all rows visible). The CSV artifacts remain
the machine-readable authority.""")

code("""print('=' * 100)
print('MODEL SUMMARY — 4 / 4 rows')
print('=' * 100)
print(summary.to_string(index=False))
print()
print('=' * 100)
print('CASE-MODEL TABLE — %d / %d rows' % (len(case), len(case)))
print('=' * 100)
cc = case[['sample_id', 'model_display', 'global_dice', 'oracle_dice', 'predicted_dice',
           'predicted_minus_global_dice', 'oracle_minus_global_dice', 'predicted_minus_oracle_dice',
           'proposal_count', 'proposal_union_area_fraction']]
print(cc.to_string(index=False))""")

code("""print('=' * 100)
print('COMPONENT-MODEL TABLE — %d / %d rows' % (len(comp), len(comp)))
print('=' * 100)
cp = comp[['sample_id', 'native_component_id', 'model_display', 'size_stratum',
           'global_detected', 'oracle_detected', 'predicted_detected',
           'GLOBAL_TO_PREDICTED_RECOVERY', 'GLOBAL_TO_PREDICTED_LOSS',
           'part1c_bbox_covered90', 'part1c_pixel_covered90']]
print(cp.to_string(index=False))""")

code("""print('READ-ONLY notebook — no model construction, no CUDA request, no inference, no TEST access.')
print('case rows  :', len(case))
print('comp rows  :', len(comp))
print('summary    :', len(summary))""")

nb = new_notebook(cells=cells)
nb.metadata = {
    "kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
    "language_info": {"name": "python"},
}
OUT.parent.mkdir(parents=True, exist_ok=True)
nbformat.write(nb, str(OUT))
print("wrote", OUT)
print("cells", len(nb.cells), "code", len([c for c in nb.cells if c.cell_type == "code"]))
