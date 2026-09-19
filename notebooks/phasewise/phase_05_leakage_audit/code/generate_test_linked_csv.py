import pandas as pd
import json

raw_df = pd.read_csv('D:/Softfors/jup/reports/tables/phase05_test_linked_high_risk_phash_pairs_RAW.csv')

v3_all = pd.read_csv('D:/Softfors/jup/manifests/phase4_v3_candidate/all_paired_v3_candidate.csv')
sample_info = v3_all.set_index('sample_id')[['split_v2', 'split', 'quarantine_reason']].to_dict('index')

out_rows = []
for idx, row in raw_df.iterrows():
    s_a = row['sample_id_a']
    s_b = row['sample_id_b']
    
    if row['split_a'] == 'TEST':
        test_id = s_a
        dev_id = s_b
        dev_split = row['split_b']
    else:
        test_id = s_b
        dev_id = s_a
        dev_split = row['split_a']
        
    dev_info = sample_info.get(dev_id, {})
    current_split = dev_info.get('split', dev_split)
    already_quarantined = (current_split == 'QUARANTINED')
    
    existing_reason = dev_info.get('quarantine_reason', None)
    if pd.isna(existing_reason):
        existing_reason = None
        
    action = 'QUARANTINE_CONSERVATIVE' if not already_quarantined else 'PRESERVE_EXISTING_QUARANTINE'
    
    out_rows.append({
        'pair_id': f"TEST_PHASH_{row['dataset_a']}_{idx:03d}",
        'dataset': row['dataset_a'],
        'development_split': dev_split,
        'development_sample_id': dev_id,
        'test_sample_id': test_id,
        'phash_distance': row['hamming_distance'],
        'historical_evidence_source': 'reports/audits/near_duplicate_candidates.csv',
        'development_already_quarantined': already_quarantined,
        'existing_quarantine_reason': existing_reason,
        'action_required': action
    })

out_df = pd.DataFrame(out_rows)
out_df.to_csv('D:/Softfors/jup/reports/tables/phase05_test_linked_high_risk_phash_pairs.csv', index=False)
print("Saved final CSV. Unique development nodes:", out_df['development_sample_id'].nunique())
print("Newly quarantined:", len(out_df[out_df['action_required'] == 'QUARANTINE_CONSERVATIVE']))
