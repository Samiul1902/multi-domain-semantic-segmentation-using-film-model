import pandas as pd
import os
import json

def get_busi_patient(image_path):
    base = os.path.basename(image_path)
    name = os.path.splitext(base)[0]
    return name.split('-')[0]

def main():
    print("Loading v2 manifests...")
    df_all = pd.read_csv('manifests/all_paired.csv')
    
    df_v3 = df_all.copy()
    df_v3['candidate_split_v3'] = df_v3['split']
    df_v3['quarantine_reason'] = None
    df_v3['duplicate_asset_group_id'] = None
    df_v3['duplicate_risk_group_id'] = None
    
    # -------------------------------------------------------------------------
    # RULE 2: Exact Duplicate
    # -------------------------------------------------------------------------
    train_kub = '4739fd78796d5555ae7ab82719910576'
    val_kub = 'a62708e2834fab0c56d4f575f49f7c61'
    df_v3.loc[df_v3['sample_id'] == val_kub, 'candidate_split_v3'] = 'QUARANTINED'
    df_v3.loc[df_v3['sample_id'] == val_kub, 'quarantine_reason'] = 'QUARANTINED_EXACT_DUPLICATE'
    df_v3.loc[df_v3['sample_id'].isin([train_kub, val_kub]), 'duplicate_asset_group_id'] = 'GROUP_KUB_001'
    print(f"Rule 2: Quarantined {val_kub}")
    
    adj_df = pd.read_csv('reports/tables/phase05_train_val_candidate_adjudication.csv')
    
    # RULE 3
    d0_pairs = adj_df[adj_df['adjudication_status'] == 'LIKELY_SAME_ACQUISITION']
    group_idx = 1
    for _, row in d0_pairs.iterrows():
        val_id = row['sample_id_b']
        df_v3.loc[df_v3['sample_id'] == val_id, 'candidate_split_v3'] = 'QUARANTINED'
        df_v3.loc[df_v3['sample_id'] == val_id, 'quarantine_reason'] = 'QUARANTINED_SAME_ACQUISITION'
        group_name = f'RISK_GROUP_ISIC_d0_{group_idx:03d}'
        df_v3.loc[df_v3['sample_id'].isin([row['sample_id_a'], val_id]), 'duplicate_risk_group_id'] = group_name
        group_idx += 1
    
    # RULE 4
    d2_pairs = adj_df[adj_df['adjudication_status'] == 'UNRESOLVED_NEAR_DUPLICATE']
    for _, row in d2_pairs.iterrows():
        val_id = row['sample_id_b']
        df_v3.loc[df_v3['sample_id'] == val_id, 'candidate_split_v3'] = 'QUARANTINED'
        df_v3.loc[df_v3['sample_id'] == val_id, 'quarantine_reason'] = 'CONSERVATIVE_HIGH_RISK_GROUPING'
        group_name = f'RISK_GROUP_d2_{group_idx:03d}'
        df_v3.loc[df_v3['sample_id'].isin([row['sample_id_a'], val_id]), 'duplicate_risk_group_id'] = group_name
        group_idx += 1
        
    # RULE 6
    busi_mask = df_v3['dataset'] == 'BUSI'
    df_v3.loc[busi_mask, 'busi_patient_id'] = df_v3.loc[busi_mask, 'image_path'].apply(get_busi_patient)
    
    patient_splits = df_v3[busi_mask].groupby('busi_patient_id')['split'].unique()
    test_linked_quarantined = 0
    val_overlap_quarantined = 0
    
    for patient, splits in patient_splits.items():
        if len(splits) > 1:
            patient_mask = (df_v3['dataset'] == 'BUSI') & (df_v3['busi_patient_id'] == patient)
            if 'TEST' in splits:
                dev_mask = patient_mask & (df_v3['split'] != 'TEST')
                test_linked_quarantined += dev_mask.sum()
                df_v3.loc[dev_mask, 'candidate_split_v3'] = 'QUARANTINED'
                df_v3.loc[dev_mask, 'quarantine_reason'] = 'QUARANTINED_TEST_LINKED_PATIENT_OVERLAP'
                df_v3.loc[dev_mask, 'duplicate_risk_group_id'] = f"GROUP_BUSI_PATIENT_{patient}"
            elif 'TRAIN' in splits and 'VAL' in splits:
                val_mask = patient_mask & (df_v3['split'] == 'VAL')
                val_overlap_quarantined += val_mask.sum()
                df_v3.loc[val_mask, 'candidate_split_v3'] = 'QUARANTINED'
                df_v3.loc[val_mask, 'quarantine_reason'] = 'QUARANTINED_BUSI_PATIENT_OVERLAP'
                df_v3.loc[val_mask, 'duplicate_risk_group_id'] = f"GROUP_BUSI_PATIENT_{patient}"
                
    if 'busi_patient_id' in df_v3.columns:
        df_v3 = df_v3.drop(columns=['busi_patient_id'])
        
    # RULE 7: Historical TEST_LINKED
    test_phash_df = pd.read_csv('reports/tables/phase05_test_linked_high_risk_phash_pairs.csv')
    test_phash_newly = test_phash_df[test_phash_df['action_required'] == 'QUARANTINE_CONSERVATIVE']
    new_quarantined_count = 0
    
    test_phash_group_idx = 1
    for _, row in test_phash_newly.iterrows():
        dev_id = row['development_sample_id']
        test_id = row['test_sample_id']
        mask = df_v3['sample_id'] == dev_id
        if df_v3.loc[mask, 'candidate_split_v3'].values[0] != 'QUARANTINED':
            df_v3.loc[mask, 'candidate_split_v3'] = 'QUARANTINED'
            df_v3.loc[mask, 'quarantine_reason'] = 'QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK'
            grp = f"RISK_GROUP_TEST_PHASH_{test_phash_group_idx:03d}"
            df_v3.loc[df_v3['sample_id'].isin([dev_id, test_id]), 'duplicate_risk_group_id'] = grp
            test_phash_group_idx += 1
            new_quarantined_count += 1
        
    out_dir = 'manifests/phase4_v3_candidate'
    os.makedirs(out_dir, exist_ok=True)
    
    df_v3.rename(columns={'split': 'split_v2'}, inplace=True)
    df_v3['split'] = df_v3['candidate_split_v3']
    df_v3.to_csv(os.path.join(out_dir, 'all_paired_v3_candidate.csv'), index=False)
    
    orig_cols = df_all.columns.tolist()
    df_v3[df_v3['split'] == 'TRAIN'][orig_cols].to_csv(os.path.join(out_dir, 'train_v3_candidate.csv'), index=False)
    df_v3[df_v3['split'] == 'VAL'][orig_cols].to_csv(os.path.join(out_dir, 'val_v3_candidate.csv'), index=False)
    
    import shutil
    shutil.copyfile('manifests/test.csv', os.path.join(out_dir, 'test_v3_candidate.csv'))
    
    df_v3[df_v3['split'] == 'QUARANTINED'].drop(columns=['candidate_split_v3']).to_csv(os.path.join(out_dir, 'quarantined_v3_candidate.csv'), index=False)
    
    groups_df = df_v3[df_v3['duplicate_risk_group_id'].notnull() | df_v3['duplicate_asset_group_id'].notnull()][['sample_id', 'dataset', 'duplicate_risk_group_id', 'duplicate_asset_group_id', 'split', 'quarantine_reason']]
    groups_df.to_csv(os.path.join(out_dir, 'duplicate_groups_v3_candidate.csv'), index=False)
    
    provenance = pd.DataFrame({
        'rule': ['Rule 2: Exact KUB', 'Rule 3: ISIC d=0', 'Rule 4: d=2 Unresolved', 'Rule 6: BUSI TEST-link', 'Rule 6: BUSI TRAIN/VAL-link', 'Rule 7: TEST-linked pHash'],
        'items_quarantined': [1, len(d0_pairs), len(d2_pairs), test_linked_quarantined, val_overlap_quarantined, new_quarantined_count]
    })
    provenance.to_csv(os.path.join(out_dir, 'grouping_provenance_v3_candidate.csv'), index=False)
    print("Successfully built v3 candidate manifests.")

if __name__ == "__main__":
    main()
