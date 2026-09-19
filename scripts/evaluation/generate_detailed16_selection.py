import pandas as pd
import hashlib
from pathlib import Path

val_sized = pd.read_csv('reports/tables/kub_val_samples_sized.csv')
val_comps = pd.read_csv('reports/tables/kub_val_components_sized.csv')
recon_cases = pd.read_csv('reports/tables/phase14_part3d_frozen_hardcase_reconstruction.csv')

ff = val_sized[val_sized['view_type'] == 'FULL_FIELD'].copy()

# Deterministic ranking: 'phase15_detailed16_seed42|' + sample_id
def get_rank_hash(sid):
    s = f'phase15_detailed16_seed42|{sid}'
    return hashlib.sha256(s.encode('utf-8')).hexdigest()

ff['hash_rank'] = ff['sample_id'].apply(get_rank_hash)
ff_sorted = ff.sort_values('hash_rank').reset_index(drop=True)
ff_sorted['detailed_rank'] = range(1, len(ff_sorted) + 1)
selected_16 = ff_sorted.iloc[:16].copy()

hard_tiny_sids = set(recon_cases[recon_cases['case_type'] == 'HARD_TINY_COMPONENT']['sample_id'])
global_empty_sids = set(recon_cases[recon_cases['case_type'] == 'GLOBAL_EMPTY_IMAGE']['sample_id'])

rows = []
for _, r in selected_16.iterrows():
    sid = r['sample_id']
    comps = val_comps[val_comps['sample_id'] == sid]
    strata = set(comps['size_stratum']) if 'size_stratum' in comps.columns else set(comps['kub_size_v1'])
    
    rows.append({
        'detailed_rank': int(r['detailed_rank']),
        'sample_id': sid,
        'split': 'VAL',
        'fov_type': 'FULL_FIELD',
        'gt_component_count': int(r['component_count']),
        'Tiny_present': bool('TINY' in strata),
        'Small_present': bool('SMALL' in strata),
        'Medium_present': bool('MEDIUM' in strata),
        'Large_present': bool('LARGE' in strata),
        'hard_tiny_flag': bool(sid in hard_tiny_sids),
        'global_empty_flag': bool(sid in global_empty_sids),
        'selection_hash': str(r['hash_rank'])
    })

df_out = pd.DataFrame(rows)
out_path = Path('reports/tables/phase15_val_detailed16_selection.csv')
out_path.parent.mkdir(parents=True, exist_ok=True)
df_out.to_csv(out_path, index=False)
print(f"Generated {len(df_out)} rows in {out_path}")
print(df_out[['detailed_rank', 'sample_id', 'gt_component_count', 'Tiny_present', 'Small_present', 'Medium_present', 'Large_present', 'hard_tiny_flag', 'global_empty_flag']].to_string())
t_cnt = int(df_out['Tiny_present'].sum())
s_cnt = int(df_out['Small_present'].sum())
m_cnt = int(df_out['Medium_present'].sum())
l_cnt = int(df_out['Large_present'].sum())
ht_cnt = int(df_out['hard_tiny_flag'].sum())
ge_cnt = int(df_out['global_empty_flag'].sum())
print(f"Strata in 16-case cohort: Tiny={t_cnt}/16, Small={s_cnt}/16, Medium={m_cnt}/16, Large={l_cnt}/16, HardTiny={ht_cnt}/16, GlobalEmpty={ge_cnt}/16")

