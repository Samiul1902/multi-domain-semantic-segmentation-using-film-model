"""Build Phase 11 Part 1A protocol-freeze notebook."""
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

md("""# Phase 11 Part 1A — Historical Protocol Reconstruction + CLEAN-v3 Failure-Definition Freeze

**Model:** Gemini 3.1 Pro High · **Date:** 2026-09-21
**Manifest:** `phase4_v3` · **Taxonomy:** `kub_size_clean_v3_v1`
**Phase:** 11 (Part 1A) — Baseline Failure Analysis

---

> **PROTOCOL / DEFINITION PHASE ONLY.** Part 1A does **not** execute the full Phase-11
> failure analysis. It reconstructs the historical Phase-11 methodology and freezes the
> clean-v3 failure-analysis definitions *before* any detailed inspection.
>
> Forbidden here: training, checkpoint/history modification, threshold tuning, winner or
> reference-model selection, Phase 12, TEST access.
>
> **No model is called a winner. No reference model is selected.**
""")

md("""## 2. Scope and Governance

| Rule | Status |
|---|---|
| Training epochs | **0** |
| Optimizer steps | **0** |
| Checkpoint writes | **0** |
| TEST image/mask/content reads | **0** |
| TEST metrics / visualizations | **0** |
| Winner declared | **NO** |
| Reference model selected | **NO** |
| New numerical thresholds introduced | **0** |
| Phase 12 started | **NO** |
| Full Phase-11 failure analysis | **NOT STARTED** |
""")

md("""## 3. Phase-10 Frozen Evidence (inputs)

Four frozen clean-v3 baselines. Values are single-seed descriptive VAL evidence.
""")
co("""%matplotlib inline
import sys, json
from pathlib import Path
import numpy as np, pandas as pd
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)

PROJECT_ROOT = Path(r'D:\\Softfors\\jup')
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'notebooks' / 'phasewise' / 'phase_11_failure_analysis' / 'code'))
import phase11_failure_protocol as p

rows=[]
for k in p.CLEAN_V3_MODELS:
    m = p.CLEAN_V3_METRICS[k]
    rows.append({'model': p.MODEL_DISPLAY[k], 'best_epoch': m['best_epoch'],
                 'dice': m['dice'], 'iou': m['iou'],
                 'precision': m['precision'], 'recall': m['recall']})
P10 = pd.DataFrame(rows)
display(P10)
print('Manifest: phase4_v3 | Taxonomy: kub_size_clean_v3_v1')
print('These are descriptive single-seed VAL results - NOT a ranking, NO winner.')
""")

co("""# Phase-10 paired VAL evidence is reused READ-ONLY (no re-inference in Part 1A)
pv = p.verify_paired_table()
print('=== Phase-10 paired VAL table (read-only) ===')
for k,v in pv.items(): print(f'  {k}: {v}')
assert pv['rows']==280 and pv['all_model_columns'] and not pv['any_nan']
assert pv['acquisition_counts']=={'ROI':177,'FULL_FIELD':103}
print('\\nPAIRED EVIDENCE REUSED - PASS (280 cases, all four models, no rerun needed)')
""")

md("""## 4. Historical Phase-11 Source Inventory
""")
co("""inv = p.build_source_inventory()
display(inv[['precedence','source_kind','path','exists']])
print('\\nAll sources present:', bool(inv.exists.all()))
""")

md("""## 5. Historical Model / Split Scope
""")
co("""hist = json.loads((p.AUDITS/'phase11_historical_failure_protocol_reconstruction.json').read_text(encoding='utf-8'))
print('Historical Phase 11 found:', hist['historical_phase11_found'])
print('Primary model   :', hist['historical_model_scope']['primary_model'],
      f"({hist['historical_model_scope']['primary_experiment']})")
print('Comparator      :', hist['historical_model_scope']['secondary_comparator'])
print('Split           :', hist['historical_split'])
print('Threshold       :', hist['historical_threshold'])
print('Units           :', ', '.join(hist['historical_failure_units']))
print()
print('NOTE: historical was UNet++-PRIMARY. Part 1A does NOT adopt a clean-v3 reference model;')
print('      that decision is deferred to the supervisor (single-seed VAL is insufficient).')
""")

md("""## 6. Historical Failure Definitions

The failure-definition matrix uses `VERIFIED` / `NOT_FOUND` / `AMBIGUOUS`.
""")
co("""mx = p.build_failure_matrix()
display(mx[['concept','unit','metric','threshold','status']])
print()
print('Status counts:', mx.status.value_counts().to_dict())
print()
print('Historical failure labels:', ', '.join(hist['historical_failure_definitions']['labels']))
""")

co("""print('=== Historical numeric thresholds (DESCRIPTIVE strata, NOT tuning thresholds) ===')
for k,v in hist['historical_numeric_thresholds'].items():
    if k=='caveat': continue
    print(f"  {k}: cutoff={v['cutoff']} ({v['comparison']}), n={v['n']}")
print()
print('Caveat:', hist['historical_numeric_thresholds']['caveat'])
print()
print('These cutoffs are HISTORICAL (phase4_v2, 283 VAL cases). They are NOT carried over')
print('as clean-v3 numbers; only the METHOD (own-distribution bottom decile) is inherited.')
""")

md("""## 7. Historical Qualitative-Selection Protocol
""")
co("""hc = p.build_hard_case_protocol()
display(hc)
print()
print('Key point: this cohort IS selected by failure status (prediction-dependent), unlike the')
print('Phase-10 qualitative gallery which is prediction-independent. That is intentional for')
print('failure analysis, but it must never be presented as a representative sample.')
print()
print('Part 1A freezes the PROCEDURE only - NO clean-v3 cases are selected here.')
""")

md("""## 8. Historical Phase-11 → Phase-12 Rationale
""")
co("""br = p.build_phase12_bridge()
display(br)
print()
print('HISTORICAL RATIONALE (recorded verbatim from the audit):')
print(' >', hist['historical_phase11_to_phase12_rationale'])
print()
print('This is the HISTORICAL justification. It is NOT rewritten from clean-v3 results.')
print('Part 1B must test cleanly whether the same pattern holds across all four clean-v3 models.')
""")

md("""## 9. Clean-v3 Invariant Contracts
""")
co("""print('=== CLEAN-v3 INVARIANT CONTRACTS ===')
print('Foreground rule        :', p.FOREGROUND_RULE, '(never mask == 1)')
print('Connectivity           :', p.CONNECTIVITY)
print('Minimum overlap pixels :', p.MINIMUM_OVERLAP_PIXELS)
print('Prediction threshold   : 0.5 (fixed, no tuning)')
print('Taxonomy               :', p.TAXONOMY_ID)
print('Taxonomy quantiles     :', p.TAXONOMY_QUANTILES)
print('Taxonomy scope         : FULL_FIELD only; ROI = ROI_NOT_PRIMARY_BINNED')
print('Split                  : KUB VAL, 280 cases')
print()
print('These come from frozen repository contracts:')
print('  - src/utils/targets.py (binarize_mask -> mask > 0)')
print('  - src/metrics/object_metrics.py (8-conn, overlap-based, min 1 px)')
print('  - reports/audits/kub_size_clean_v3_v1_thresholds.json')
assert p.TAXONOMY_SHA == p.sha256_file(p.AUDITS/'kub_size_clean_v3_v1_thresholds.json')
print('\\nTaxonomy artifact SHA verified:', p.TAXONOMY_SHA)
""")

md("""## 10. Acquisition-Regime Contract

FULL_FIELD and ROI are **different acquisition regimes**; object scale differs radically.
They must never be pooled without showing both.
""")
co("""print('Regime counts (clean-v3 KUB VAL):', p.REGIME_COUNTS)
print('Historical (v2)            : ROI_CROP 177 / FULL_FIELD 106')
print()
print('Rule: any failure rate must be reported per regime. A pooled number alone is invalid.')
""")

md("""## 11. Size-Taxonomy Contract
""")
co("""print('Taxonomy:', p.TAXONOMY_ID)
for k,v in p.TAXONOMY_QUANTILES.items(): print(f'  {k} = {v}')
print()
print('Bins (lower-inclusive): TINY <= Q25 < SMALL <= Q50 < MEDIUM <= Q75 < LARGE')
print('Scope: FULL_FIELD only. ROI cases are ROI_NOT_PRIMARY_BINNED.')
print('HISTORICAL taxonomy kub_size_v1 is retained for provenance only and must NOT be')
print('applied to clean-v3 data (different quantiles / different population).')
""")

md("""## 12. Object / Connectivity Contract
""")
co("""print('=== OBJECT CONTRACT ===')
print('Foreground            : mask > 0')
print('Connectivity          : 8 (src/metrics/object_metrics.py)')
print('Matching              : overlap-based, minimum_overlap_pixels = 1')
print('Component space       : original space = identity + size + single/multi grouping')
print('                        evaluation 512 space = prediction components, object recall, FP components')
print()
print('The two spaces must never be silently mixed (resize/padding can merge components).')
print('Connectivity MUST be declared in any object-level output (4- vs 8-connectivity differ).')
""")

md("""## 13. Candidate Clean-v3 Failure Dimensions
""")
co("""dim = p.build_dimensions()
display(dim)
print()
print('VERIFIED_CONTRACT = already frozen by existing repository contracts')
print('HISTORICAL_VERIFIED / _PROPOSED_EXTENSION = inherited or proposed, see status column')
print('CANDIDATE_FOR_SUPERVISOR_REVIEW = NOT frozen; requires a supervisor decision')
""")

md("""## 14. Shared-Failure Governance

Historical concept exists: `ALL_FOUR_LOW` (low in all four models, each by its own bottom
Dice decile). Clean-v3 candidate formulas are prepared but **not adopted**.
""")
co("""print('=== SHARED-FAILURE GOVERNANCE ===')
print('Historical concept : ALL_FOUR_LOW (each model own bottom Dice decile)')
print('Historical status  :', 'VERIFIED (historical, v2)')
print()
print('Clean-v3 candidate definitions (CANDIDATE_FOR_SUPERVISOR_REVIEW - NOT adopted):')
for c in ['mean Dice across the four models','median Dice across models',
          'number of models below the (recomputed) low-Dice stratum']:
    print('  -', c)
print()
print('No shared-failure formula is frozen in Part 1A.')
""")

md("""## 15. Architecture-Disagreement Governance
""")
co("""print('=== ARCHITECTURE-DISAGREEMENT GOVERNANCE ===')
print('Historical concept : ARCHITECTURE_DISAGREEMENT / *_UNIQUELY_* categories')
print('Historical status  : VERIFIED (historical, v2)')
print()
print('Clean-v3 candidate measures (CANDIDATE_FOR_SUPERVISOR_REVIEW - NOT adopted):')
for c in ['max Dice - min Dice','standard deviation of per-model Dice']:
    print('  -', c)
print()
print('No disagreement threshold is frozen in Part 1A.')
""")

md("""## 16. Hard-Case-Selection Freeze Proposal

Selection procedure is frozen here; **no cases are selected** until Part 1B.
""")
co("""print('=== HARD-CASE SELECTION FREEZE (proposal) ===')
print('Selection metric : failure-stratum membership (historical 4-strata family)')
print('Cohort size      : 16 (4 strata x 4 cases) - historical precedent')
print('Stratification   : by failure stratum AND acquisition regime')
print('Tie-break        : deterministic sort by sample_id (low-dice stratum: ascending dice)')
print('Exclusion        : later strata exclude earlier-selected samples')
print()
print('STATUS: PROCEDURE_FROZEN_NO_CASES_SELECTED')
print()
print('Governance: the selector is defined BEFORE looking at qualitative outputs, so no')
print('cherry-picking is possible. Selection depends on failure status by design.')
""")

md("""## 17. Open Methodological Questions (returned to supervisor)

These require a scientific decision and are **not** resolved here.
""")
co("""qs = [
 ('Low-Dice stratum numeric value',
  'Historical cutoff 0.5461 is v2-specific. Clean-v3 value must be recomputed on clean-v3 VAL. Should the METHOD (bottom decile) be adopted, with value recomputed?'),
 ('Shared-failure formula',
  'Which definition (mean / median / count-below-stratum) should be adopted for clean-v3?'),
 ('Disagreement measure + threshold',
  'max-min Dice or SD, and whether any threshold may be set?'),
 ('FP-burden threshold',
  'Historical used >=4 fp components (comment said >=5). Which for clean-v3?'),
 ('Pixel error decomposition',
  'TP/FP/FN and under/over-segmentation were NOT historically defined - adopt as extension?'),
 ('Multi-component subgroup',
  'Historically analysed; retain as descriptive clean-v3 subgroup? (PROPOSED_EXTENSION)'),
 ('Reference model for Phase 12',
  'Historical was UNet++-primary. Clean-v3 reference must be a separate supervisor decision.'),
]
for i,(q,d) in enumerate(qs,1): print(f'{i}. {q}\\n   {d}\\n')
print('None of these are decided in Part 1A.')
""")

# 18-21 upstream epoch tables
for i, k in enumerate(['unet','attention_unet','unetpp','deeplabv3plus'], start=18):
    d = {'unet':'UNet','attention_unet':'Attention U-Net','unetpp':'UNet++','deeplabv3plus':'DeepLabV3+'}[k]
    md(f"""## {i}. Upstream Complete Epoch Table — {d}

Read-only, from the frozen Phase-10 normalized epoch table. **Every epoch row is shown.**
""")
    co(f"""t = p.load_upstream_epoch_table('{k}')
v = p.verify_upstream_epoch_tables().query("model == '{d}'").iloc[0]
print('=== UPSTREAM INTEGRITY: {d} ===')
for kk in ['rows','expected_rows','row_count_matches','first_epoch','last_epoch',
           'missing_epochs','duplicate_epochs','contiguous']:
    print(f'  {{kk}}: {{v[kk]}}')
print()
assert v['row_count_matches'] and v['contiguous']
print(f"Rendering ALL {{len(t)}} epoch rows for {d}:")
display(t)
""")

md("""## 22. Proposed Part-1B Execution Plan

Part 1B (not started) should:
1. Apply the frozen definitions to the four clean-v3 baselines using the existing paired table.
2. Report failure rates **per regime** (FULL_FIELD 103 / ROI 177) and per category.
3. Report object-level detection using 8-conn / >=1 px, in declared component space.
4. Compute the shared-failure and disagreement views **once the supervisor picks a formula**.
5. Select the hard-case cohort using the frozen procedure only after the above.
6. Preserve full epoch-table visibility for any newly created notebook.
""")

md("""## 23. Artifact Hashes
""")
co("""def _sh(rel):
    q = PROJECT_ROOT / rel
    return p.sha256_file(q) if q.exists() else 'N/A'
arts = [
 ('notebooks/phasewise/phase_11_failure_analysis/code/phase11_failure_protocol.py',),
 ('reports/tables/phase11_historical_source_inventory.csv',),
 ('reports/tables/phase11_historical_failure_definition_matrix.csv',),
 ('reports/tables/phase11_clean_v3_failure_analysis_dimensions.csv',),
 ('reports/tables/phase11_clean_v3_hard_case_selection_protocol.csv',),
 ('reports/tables/phase11_phase12_bridge_reconstruction.csv',),
 ('reports/audits/phase11_preflight_state_consistency_audit.json',),
 ('reports/audits/phase11_historical_failure_protocol_reconstruction.json',),
 ('reports/audits/phase11_clean_v3_failure_analysis_protocol_candidate.json',),
 ('reports/audits/antigravity_current_state.json',),
]
REG = pd.DataFrame([{'artifact': Path(a[0]).name, 'path': a[0], 'sha256': _sh(a[0])} for a in arts])
rp = p.TABLES / 'phase11_part1a_artifact_registry.csv'
REG.to_csv(rp, index=False)
print(f'Saved registry: {{rp.name}}')
display(REG)
""")

md("""## 24. Stop Boundary
""")
co("""print('=== PHASE-11 PART-1A BOUNDARY ===')
print('Training epochs                 : 0')
print('Optimizer steps                 : 0')
print('Checkpoint writes               : 0')
print('Histories / configs modified    : 0')
print('TEST image/mask/content reads   : 0')
print('TEST metrics / visualizations   : 0')
print('New unauthorized thresholds     : 0')
print('Winner declared                 : NO')
print('Reference model selected        : NO')
print('Full Phase-11 analysis started  : NO')
print('Phase 12 started                : NO')
print()
print('FAILURE PROTOCOL STATUS: READY_FOR_SUPERVISOR_FREEZE')
print('NEXT: WAIT_FOR_SUPERVISOR_PHASE11_PROTOCOL_FREEZE_DECISION')
""")

out = Path(r'D:\Softfors\jup\notebooks\phasewise\phase_11_failure_analysis\phase11_clean_v3_failure_analysis_protocol_freeze.ipynb')
with open(out,'w',encoding='utf-8') as f:
    nbf.write(nb,f)
print(f'Notebook written: {out}')
print(f'Total cells: {len(nb.cells)}')
