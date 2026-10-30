"""Run read-only paired 280-case KUB VAL inference for all four clean-v3 baselines.

Writes:
  reports/tables/phase10_clean_v3_paired_val_case_metrics.csv
  reports/tables/phase10_clean_v3_overall_baseline_comparison.csv
  reports/tables/phase10_clean_v3_category_stratified_metrics.csv
  reports/tables/phase10_clean_v3_acquisition_stratified_metrics.csv
  reports/tables/phase10_clean_v3_pairwise_descriptive_deltas.csv
  reports/tables/phase10_clean_v3_pairwise_case_disagreement_summary.csv

READ-ONLY: no training, no checkpoint writes, no TEST access.
"""
import sys
from pathlib import Path

ROOT = Path(r'D:\Softfors\jup')
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'notebooks' / 'phasewise' / 'phase_10_baseline_comparison' / 'code'))

import pandas as pd
import phase10_final_comparison as fc

TABLES = fc.TABLES
TABLES.mkdir(parents=True, exist_ok=True)

print('=== PAIRED 280-CASE KUB VAL INFERENCE (4 models) ===')
paired = fc.build_paired_table(verbose=True)
assert len(paired) == 280, f'expected 280 paired rows, got {len(paired)}'
for k in fc.MODEL_ORDER:
    assert paired[f'{k}_dice'].notna().all(), f'missing predictions for {k}'

p = TABLES / 'phase10_clean_v3_paired_val_case_metrics.csv'
paired.to_csv(p, index=False)
print(f'Saved paired table: {p} ({len(paired)} rows)')

# Overall
epochs = {k: int(fc.load_history(k)['epoch'].iloc[-1]) for k in fc.MODEL_ORDER}
overall = fc.overall_comparison(paired, epochs)
op = TABLES / 'phase10_clean_v3_overall_baseline_comparison.csv'
overall.to_csv(op, index=False)
print(f'Saved overall comparison: {op}')
print(overall[['model', 'val_macro_dice', 'authoritative_dice', 'reproduction_abs_diff']].to_string(index=False))

# Reproduction gate
print()
print('=== AGGREGATE REPRODUCTION GATE (tol 1e-6) ===')
for _, r in overall.iterrows():
    ok = r['reproduction_abs_diff'] < 1e-6
    print(f"  {r['model']}: recomputed={r['val_macro_dice']:.10f} authoritative={r['authoritative_dice']:.10f} "
          f"diff={r['reproduction_abs_diff']:.3e} -> {'PASS' if ok else 'FAIL'}")

# Stratified
cat = fc.stratified(paired, 'category')
cp = TABLES / 'phase10_clean_v3_category_stratified_metrics.csv'
cat.to_csv(cp, index=False)
print(f'\nSaved category-stratified: {cp}')
print(cat.to_string(index=False))

acq = fc.stratified(paired, 'acquisition_type')
ap = TABLES / 'phase10_clean_v3_acquisition_stratified_metrics.csv'
acq.to_csv(ap, index=False)
print(f'\nSaved acquisition-stratified: {ap}')
print(acq.to_string(index=False))

# Deltas + disagreement
deltas = fc.pairwise_deltas(paired)
dp = TABLES / 'phase10_clean_v3_pairwise_descriptive_deltas.csv'
deltas.to_csv(dp, index=False)
print(f'\nSaved pairwise deltas: {dp}')

dis = fc.disagreement_summary(paired)
gp = TABLES / 'phase10_clean_v3_pairwise_case_disagreement_summary.csv'
dis.to_csv(gp, index=False)
print(f'Saved disagreement summary: {gp}')

print('\nDONE')
