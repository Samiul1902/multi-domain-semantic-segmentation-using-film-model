"""Build the Phase 11 CLEAN-v3 failure-analysis companion VISUAL dashboard notebook."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(r'D:\Softfors\jup')))
import nbformat as nbf
from nbformat.v4 import new_notebook, new_markdown_cell, new_code_cell

nb = new_notebook()
nb.metadata['kernelspec'] = {'display_name': 'jup-venv', 'language': 'python', 'name': 'jup-venv'}
nb.metadata['language_info'] = {'name': 'python', 'version': '3.13.12'}
def md(t): nb.cells.append(new_markdown_cell(t))
def co(t): nb.cells.append(new_code_cell(t))

# 1 Title
md("""# Phase 11 CLEAN-v3 KUB Failure Analysis — Visual Comparison Dashboard

**DESCRIPTIVE SINGLE-SEED FAILURE ANALYSIS**
**NO WINNER**
**NO SIGNIFICANCE TESTING**

---

**Model:** Gemini 3.8 Flash Medium · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1` · **Split:** KUB VAL (280)

> **READ-ONLY VISUALIZATION COMPANION.** This notebook exists to make the four-model KUB
> failure comparison easy to understand visually. It is sourced **only** from already-frozen
> Phase-11 tables and audits.
>
> No training · no inference · no threshold changes · no scientific recomputation ·
> no TEST access · no winner/rank/superiority claim · Phase 12 not started.
>
> **Fixed model order everywhere (descriptive, NOT a ranking):**
> **UNet → Attention U-Net → UNet++ → DeepLabV3+**
""")

# 2 Scope / governance
md("""## 2. Scope and Governance

| Rule | Status |
|---|---|
| Source | frozen Phase-11 tables/audits only |
| Training epochs | **0** |
| Inference passes | **0** |
| Optimizer steps | **0** |
| Threshold changes | **0** |
| Scientific parameter changes | **0** |
| Winner / rank / best-model claim | **NONE** |
| Statistical significance testing | **NONE** |
| TEST image/mask/content reads | **0** |
| Phase 12 | **NOT STARTED** |

Model ordering is fixed and identical in every figure — the dashboard is descriptive, not a
ranking.
""")

co("""%matplotlib inline
import sys
from pathlib import Path
import pandas as pd
from IPython.display import Image as IPImage, display

pd.set_option('display.max_rows', None); pd.set_option('display.max_columns', None)
pd.set_option('display.width', None); pd.set_option('display.max_colwidth', None)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_11_failure_analysis' / 'code'))
import phase11_failure_visual_dashboard as dv

print('Fixed model order:', dv.MODELS)
print('Figure directory :', dv.FIGDIR)
print()
print(dv.SUBTITLE)
""")

# 3 Dashboard summary table
md("""## 3. Dashboard Summary Table

Compact descriptive overview. **No `rank` / `winner` / `best_model` / `score` / `tier`
columns exist by design.**
""")
co("""summary_tbl = dv.dashboard_summary_table()
display(summary_tbl)
print()
print('Overall Phase-10 VAL Dice is the single-seed descriptive Phase-10 value.')
print('FULL_FIELD / ROI Dice are Phase-11 regime-stratified means (FULL_FIELD n=103, ROI n=177).')
""")

# 4 Plot 1
md("""## 4. Plot 1 — Empty Predictions by Model
""")
co("""p = dv.plot_empty_predictions()
print('saved:', p.name)
display(IPImage(filename=str(p)))
print()
print('Values (from phase11_clean_v3_failure_summary_by_model.csv):')
print(dv.load_summary().set_index('model').loc[dv.MODELS, 'empty_predictions'].to_string())
""")

# 5 Plot 2
md("""## 5. Plot 2 — Object Recall by Model

`EVALUATION_512` component space · 8-connectivity · `>= 1 px` overlap.
The tallest bar is **not** called "best model" — only
"highest observed object recall in this single-seed analysis".
""")
co("""p = dv.plot_object_recall()
print('saved:', p.name)
display(IPImage(filename=str(p)))
print()
print(dv.load_summary().set_index('model').loc[dv.MODELS, ['object_recall']].to_string())
""")

# 6 Plot 3
md("""## 6. Plot 3 — ROI vs FULL_FIELD Dice

One of the most important plots. Caption: **FULL_FIELD n=103 · ROI n=177**.

> The regime gap is **observed across all four models**.
> This does **not** mean "ROI is superior", and it is **not** evidence that "regional
> processing solves the problem" — existing ROI samples and oracle regional processing are
> **not** the same experiment.
""")
co("""p = dv.plot_roi_vs_fullfield()
print('saved:', p.name)
display(IPImage(filename=str(p)))
reg = dv.load_regime()
tbl = pd.DataFrame({'Model': dv.MODELS,
                    'FULL_FIELD Dice': [reg['FULL_FIELD'][m] for m in dv.MODELS],
                    'ROI Dice': [reg['ROI'][m] for m in dv.MODELS]})
display(tbl)
""")

# 7 Plot 4
md("""## 7. Plot 4 — ROI–FULL_FIELD Dice Gap

**DESCRIPTIVE ACQUISITION-REGIME GAP — NOT an oracle-ROI treatment effect.**
""")
co("""p = dv.plot_regime_gap()
print('saved:', p.name)
display(IPImage(filename=str(p)))
reg = dv.load_regime()
gaps = pd.DataFrame({'Model': dv.MODELS,
                     'ROI minus FULL_FIELD': [reg['ROI'][m] - reg['FULL_FIELD'][m] for m in dv.MODELS]})
display(gaps)
print('mean gap across models: %.6f' % gaps['ROI minus FULL_FIELD'].mean())
""")

# 8 Plot 5
md("""## 8. Plot 5 — Multi-Component Case Detection Outcomes

native GT membership · 8-connectivity.
""")
co("""p = dv.plot_multicomponent()
print('saved:', p.name)
display(IPImage(filename=str(p)))
m = dv.load_multi()
display(m[['model','multicomponent_cases','COMPLETE_DETECTION','PARTIAL_DETECTION','COMPLETE_MISS']])
""")

# 9 Plot 6
md("""## 9. Plot 6 — Missed GT Components by Model

`EVALUATION_512` space · 8-connectivity · `>= 1 px` minimum overlap.
""")
co("""p = dv.plot_missed_components()
print('saved:', p.name)
display(IPImage(filename=str(p)))
s = dv.load_summary().set_index('model')
display(pd.DataFrame({'Model': dv.MODELS,
                      'missed_components': [int(s.loc[m,'missed_components']) for m in dv.MODELS],
                      'gt_eval_components': [int(s.loc[m,'gt_eval_components']) for m in dv.MODELS]}))
""")

# 10 Plot 7
md("""## 10. Plot 7 — Model-Specific Low-Dice Q10 Cutoffs

Each cutoff is defined from **that model's own** Dice distribution (bottom decile,
`np.quantile(..., 0.10)` linear, float64). **A larger cutoff does NOT mean a better model.**
""")
co("""p = dv.plot_low_dice_q10()
print('saved:', p.name)
display(IPImage(filename=str(p)))
q10 = dv.load_low_dice_q10(); cnt = dv.load_low_dice_counts()
display(pd.DataFrame({'Model': dv.MODELS,
                      'q10_cutoff': [q10[m] for m in dv.MODELS],
                      'count_le_cutoff': [cnt[m] for m in dv.MODELS]}))
print()
print('This is NOT a model-performance ranking.')
""")

# 11 Plot 8
md("""## 11. Plot 8 — Shared Failure Distribution

`low_model_count` = how many of the four models flag the case as bottom-decile Dice.
`low_model_count = 4` corresponds to **ALL_FOUR_LOW = 12 / 280**.
""")
co("""p = dv.plot_shared_failure()
print('saved:', p.name)
display(IPImage(filename=str(p)))
d = dv.load_paired()
dist = pd.DataFrame({'low_model_count': list(range(5)),
                     'cases': [int((d['low_model_count']==i).sum()) for i in range(5)]})
display(dist)
print('ALL_FOUR_LOW:', int(d['ALL_FOUR_LOW'].sum()), '/ 280')
""")

# 12 Plot 9
md("""## 12. Plot 9 — False-Positive Component Burden

`EVALUATION_512` component space. **UNet++ CLEAN-v3 Q90 = 5.0** is the
`HIGH_FP_DECILE` **anchor-only** cutoff — it is **not** a universal FP threshold; the other
models are descriptive.
""")
co("""p = dv.plot_fp_burden()
print('saved:', p.name)
display(IPImage(filename=str(p)))
display(dv.load_fp()[['model','mean','median','q90','max']])
""")

# 13 Plot 10
md("""## 13. Plot 10 — HD95 Validity / Boundary Burden

Invalid HD95 cases (empty prediction / empty GT) are **flagged, never silently dropped**.
""")
co("""p = dv.plot_hd95()
print('saved:', p.name)
display(IPImage(filename=str(p)))
display(dv.load_hd95()[['model','n_valid','n_invalid','valid_rate','median_hd95','q90_hd95_valid']])
""")

# 14 Plot 11
md("""## 14. Plot 11 — Architecture Disagreement

`dice_range = max model Dice − min model Dice` — **continuous, no binary threshold.**
Top-4 cases labelled `DESCRIPTIVE_DISAGREEMENT_DIAGNOSTIC_ONLY`.
""")
co("""p = dv.plot_disagreement()
print('saved:', p.name)
display(IPImage(filename=str(p)))
d = dv.load_disagreement()
print('dice_range mean %.6f · median %.6f · max %.6f' % (d.dice_range.mean(), d.dice_range.median(), d.dice_range.max()))
display(dv.load_top_disagreement(4)[['sample_id','dice_min','dice_max','dice_range']])
""")

# 15 Plot 12
md("""## 15. Plot 12 — Hard-Case Cohort Composition

Deterministic historical-style diagnostic cohort (UNet++ anchor). **Prediction-dependent
diagnostic cohort — NOT a prevalence estimate.**
""")
co("""p = dv.plot_hard_case_composition()
print('saved:', p.name)
display(IPImage(filename=str(p)))
h = dv.load_hard_case()
display(h['stratum'].value_counts().rename_axis('stratum').reset_index(name='cases'))
display(h['acquisition'].value_counts().rename_axis('acquisition').reset_index(name='cases'))
""")

# 16 Optional bridge summary (table only for qualitative)
md("""## 16. Phase-11 → Phase-12 Bridge Summary

Dimensions with a **qualitative / MIXED** verdict are shown **as a table**, not as a
fabricated bar height. No qualitative label is converted into an arbitrary numeric score.
""")
co("""display(dv.bridge_summary_table())
print()
print('Verdict counts:', dv.load_bridge()['verdict'].value_counts().to_dict())
print('Qualitative/MIXED dimensions remain tabular only.')
""")

# 17 Overall composite dashboard
md("""## 17. Composite Failure Dashboard (reviewer overview)
""")
co("""p = dv.plot_overall_dashboard()
print('saved:', p.name)
display(IPImage(filename=str(p)))
""")

# 18 Interpretation box
md("""## 18. Interpretation

**What this dashboard supports (descriptive):**

- All four models show **lower FULL_FIELD mean Dice than ROI mean Dice** — the regime gap is
  observed across all four.
- **Failure burden differs by architecture** (empty predictions, missed components, and FP
  component burden are not uniform).
- **Some difficult cases are shared across all four models** — `ALL_FOUR_LOW = 12 / 280`.
- **Some cases show large architecture disagreement** (up to `dice_range ≈ 0.84`).
- **Empty predictions and missed components motivate testing regional resolution explicitly
  in Phase 12** — as a hypothesis to be tested, not an established result.

**What this dashboard does NOT support (and does not claim):**

- ✗ a winner or best model
- ✗ "statistically better" / "significant" (no significance testing has been performed)
- ✗ "ROI solves KUB"
- ✗ "the regional model will definitely work"

The existing ROI samples and the future oracle regional processing are **not** the same
experiment.
""")

# 19 Artifact registry
md("""## 19. Artifact Registry
""")
co("""produced = {
 'overall_failure_dashboard.png': dv.FIGDIR/'overall_failure_dashboard.png',
 'empty_predictions_by_model.png': dv.FIGDIR/'empty_predictions_by_model.png',
 'object_recall_by_model.png': dv.FIGDIR/'object_recall_by_model.png',
 'roi_vs_fullfield_dice.png': dv.FIGDIR/'roi_vs_fullfield_dice.png',
 'roi_fullfield_gap.png': dv.FIGDIR/'roi_fullfield_gap.png',
 'multicomponent_outcomes.png': dv.FIGDIR/'multicomponent_outcomes.png',
 'missed_components_by_model.png': dv.FIGDIR/'missed_components_by_model.png',
 'low_dice_q10_by_model.png': dv.FIGDIR/'low_dice_q10_by_model.png',
 'shared_failure_low_model_count.png': dv.FIGDIR/'shared_failure_low_model_count.png',
 'fp_component_burden.png': dv.FIGDIR/'fp_component_burden.png',
 'hd95_validity.png': dv.FIGDIR/'hd95_validity.png',
 'architecture_disagreement_top4.png': dv.FIGDIR/'architecture_disagreement_top4.png',
 'hard_case_composition.png': dv.FIGDIR/'hard_case_composition.png',
}
missing = [k for k,v in produced.items() if not v.exists()]
assert not missing, f'missing figures: {missing}'
REG = dv.build_registry(produced)
rp = dv.save_registry(REG)
print(f'Saved registry: {rp.name} ({len(REG)} entries)')
display(REG)
""")

# 20 Stop boundary
md("""## 20. Stop Boundary
""")
co("""print('=== DASHBOARD BOUNDARY ===')
print('Training epochs            : 0')
print('Inference passes           : 0')
print('Optimizer steps            : 0')
print('Threshold changes          : 0')
print('Scientific recomputation   : NONE (frozen tables only)')
print('Source tables modified     : NONE')
print('TEST image/mask/content    : 0 / 0 / 0')
print('Winner declared            : NO')
print('Statistical testing        : NO')
print('Phase 12 started           : NO')
print()
print('Accepted Phase-10 final notebook  : b9f5812e... (unchanged)')
print('Accepted Phase-11 Part-1A notebook: aaf1d86e... (unchanged)')
print('Accepted Phase-11 Part-1B notebook: 4c78815d... (unchanged)')
print()
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE12_AUTHORIZATION')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_11_failure_analysis\phase11_clean_v3_failure_visual_dashboard.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
