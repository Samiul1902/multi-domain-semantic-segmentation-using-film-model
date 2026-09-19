import pandas as pd
import hashlib
import os

PROJECT_ROOT = r'D:\Softfors\jup'

def get_path(rel_path):
    return os.path.join(PROJECT_ROOT, rel_path)

def load_v2_manifests():
    return {
        'all': pd.read_csv(get_path('manifests/all_paired.csv')),
        'train': pd.read_csv(get_path('manifests/train.csv')),
        'val': pd.read_csv(get_path('manifests/val.csv')),
        'test': pd.read_csv(get_path('manifests/test.csv'))
    }

def load_v3_candidate():
    out_dir = get_path('manifests/phase4_v3_candidate')
    return {
        'all': pd.read_csv(os.path.join(out_dir, 'all_paired_v3_candidate.csv')),
        'train': pd.read_csv(os.path.join(out_dir, 'train_v3_candidate.csv')),
        'val': pd.read_csv(os.path.join(out_dir, 'val_v3_candidate.csv')),
        'test': pd.read_csv(os.path.join(out_dir, 'test_v3_candidate.csv')),
        'quarantined': pd.read_csv(os.path.join(out_dir, 'quarantined_v3_candidate.csv')),
        'duplicate_groups': pd.read_csv(os.path.join(out_dir, 'duplicate_groups_v3_candidate.csv')),
        'provenance': pd.read_csv(os.path.join(out_dir, 'grouping_provenance_v3_candidate.csv'))
    }

def validate_population_accounting(v2_data, v3_data):
    s_v2 = set(v2_data['all']['sample_id'])
    s_v3_all = set(v3_data['all']['sample_id'])
    
    s_tr = set(v3_data['train']['sample_id'])
    s_va = set(v3_data['val']['sample_id'])
    s_te = set(v3_data['test']['sample_id'])
    s_qu = set(v3_data['quarantined']['sample_id'])
    
    assert len(s_v2) == 8441, "v2 total mismatch"
    assert len(s_v3_all) == 8441, "v3 total mismatch"
    assert s_v2 == s_v3_all, "v2 and v3 sample sets differ"
    
    assert len(s_tr & s_va) == 0, "TRAIN-VAL sample overlap"
    assert len(s_tr & s_te) == 0, "TRAIN-TEST sample overlap"
    assert len(s_tr & s_qu) == 0, "TRAIN-QUARANTINED sample overlap"
    assert len(s_va & s_te) == 0, "VAL-TEST sample overlap"
    assert len(s_va & s_qu) == 0, "VAL-QUARANTINED sample overlap"
    assert len(s_te & s_qu) == 0, "TEST-QUARANTINED sample overlap"
    
    assert (s_tr | s_va | s_te | s_qu) == s_v2, "Partition does not cover all v2 samples"
    
    return {
        'total_v2': len(s_v2),
        'active_train': len(s_tr),
        'active_val': len(s_va),
        'active_test': len(s_te),
        'quarantined': len(s_qu),
        'sum_reconciliation': len(s_tr) + len(s_va) + len(s_te) + len(s_qu),
        'missing_sample_ids': len(s_v2 - (s_tr | s_va | s_te | s_qu)),
        'duplicate_provenance': len(v3_data['all']) - len(s_v3_all),
        'unexpected_sample_ids': len(s_v3_all - s_v2)
    }

def validate_test_identity():
    v2_p = get_path('manifests/test.csv')
    v3_p = get_path('manifests/phase4_v3_candidate/test_v3_candidate.csv')
    with open(v2_p, 'rb') as f: v2_bytes = f.read()
    with open(v3_p, 'rb') as f: v3_bytes = f.read()
    
    v2_sha = hashlib.sha256(v2_bytes).hexdigest()
    v3_sha = hashlib.sha256(v3_bytes).hexdigest()
    
    assert v2_sha == v3_sha, "TEST SHA mismatch"
    assert v2_bytes == v3_bytes, "TEST bytes not identical"
    
    df_v2 = pd.read_csv(v2_p)
    df_v3 = pd.read_csv(v3_p)
    assert list(df_v2['sample_id']) == list(df_v3['sample_id']), "TEST sample ordering altered"
    
    return {
        'test_sha': v3_sha,
        'byte_identical': True,
        'sample_ids_identical': True,
        'sample_order_identical': True,
        'count': len(df_v3)
    }

def get_busi_patient(image_path):
    """
    LEGACY HELPER — superseded by validate_patient_disjointness_v2 which uses
    the canonical BUSI group mapping recovered from Patient_infos_BUSI-WHU.xlsx.
    Retained for reference only.
    """
    base = os.path.basename(image_path)
    name = os.path.splitext(base)[0]
    return name.split('-')[0]

def _load_busi_group_map():
    """
    Load the canonical BUSI patient group mapping recovered from
    Patient_infos_BUSI-WHU.xlsx via phase05_busi_patient_group_mapping.csv.

    ORIGINAL MANIFEST BUSI patient_id FIELD:
        NOT AVAILABLE (stored as 'NOT_AVAILABLE' in canonical manifests)

    RECOVERED BUSI PATIENT/GROUP METADATA SOURCE:
        D:\\Softfors\\omni_seg\\data_raw\\
        BUSI_WHU Breast Cancer Ultrasound Image Dataset\\
        Patient_infos_BUSI-WHU.xlsx

    MAPPING RULE:
        img_names column == basename(image_path), deterministic 1-to-1 match.
        patient_index column is the patient group ID (816 unique groups / 927 images).

    Returns dict: sample_id -> busi_patient_group_id
    """
    mapping_path = get_path('reports/tables/phase05_busi_patient_group_mapping.csv')
    df = pd.read_csv(mapping_path)
    assert len(df) == 927, f"Expected 927 BUSI mapping rows, got {len(df)}"
    assert df['mapping_status'].eq('MAPPED').all(), "Unmapped BUSI samples found — check phase05_busi_patient_group_mapping.csv"
    return dict(zip(df['sample_id'], df['busi_patient_group_id']))

def validate_patient_disjointness(v3_data):
    # --- KUB: patient_id field is available in canonical manifest ---
    kub_tr = set(v3_data['train'][v3_data['train']['dataset'] == 'KUB']['patient_id'])
    kub_va = set(v3_data['val'][v3_data['val']['dataset'] == 'KUB']['patient_id'])
    kub_te = set(v3_data['test'][v3_data['test']['dataset'] == 'KUB']['patient_id'])

    assert len(kub_tr & kub_va) == 0, "KUB TRAIN-VAL patient overlap"
    assert len(kub_tr & kub_te) == 0, "KUB TRAIN-TEST patient overlap"
    assert len(kub_va & kub_te) == 0, "KUB VAL-TEST patient overlap"

    # --- BUSI: patient_id = 'NOT_AVAILABLE' in canonical manifest.
    #     Use recovered group IDs from Patient_infos_BUSI-WHU.xlsx via
    #     phase05_busi_patient_group_mapping.csv (all 927 cases mapped). ---
    busi_group_map = _load_busi_group_map()

    def _busi_group(sid):
        return busi_group_map.get(sid, 'UNKNOWN')

    busi_tr_df = v3_data['train'][v3_data['train']['dataset'] == 'BUSI']
    busi_va_df = v3_data['val'][v3_data['val']['dataset'] == 'BUSI']
    busi_te_df = v3_data['test'][v3_data['test']['dataset'] == 'BUSI']

    busi_tr_groups = set(busi_tr_df['sample_id'].apply(_busi_group))
    busi_va_groups = set(busi_va_df['sample_id'].apply(_busi_group))
    busi_te_groups = set(busi_te_df['sample_id'].apply(_busi_group))

    tv_overlap = busi_tr_groups & busi_va_groups
    tt_overlap = busi_tr_groups & busi_te_groups
    vt_overlap = busi_va_groups & busi_te_groups

    assert len(tv_overlap) == 0, f"BUSI TRAIN-VAL patient/group overlap: {tv_overlap}"
    assert len(tt_overlap) == 0, f"BUSI TRAIN-TEST patient/group overlap: {tt_overlap}"
    assert len(vt_overlap) == 0, f"BUSI VAL-TEST patient/group overlap: {vt_overlap}"

    return {
        'kub_overlaps': {'train_val': 0, 'train_test': 0, 'val_test': 0},
        'busi_overlaps': {
            'train_val': len(tv_overlap),
            'train_test': len(tt_overlap),
            'val_test': len(vt_overlap)
        },
        'busi_group_source': 'phase05_busi_patient_group_mapping.csv (recovered from Patient_infos_BUSI-WHU.xlsx)',
        'busi_original_patient_id_field': 'NOT_AVAILABLE'
    }

def validate_duplicate_groups(v3_data):
    df_all = v3_data['all']
    active_df = df_all[df_all['split'].isin(['TRAIN', 'VAL', 'TEST'])]
    
    # Check duplicate_risk_group_id
    risk_cross = 0
    if 'duplicate_risk_group_id' in active_df.columns:
        rg = active_df[active_df['duplicate_risk_group_id'].notnull()].groupby('duplicate_risk_group_id')['split'].unique()
        risk_cross = len(rg[rg.apply(len) > 1])
        
    # Check duplicate_asset_group_id
    asset_cross = 0
    if 'duplicate_asset_group_id' in active_df.columns:
        ag = active_df[active_df['duplicate_asset_group_id'].notnull()].groupby('duplicate_asset_group_id')['split'].unique()
        asset_cross = len(ag[ag.apply(len) > 1])
        
    assert risk_cross == 0, "Active splits contain cross-split duplicate_risk_group_id"
    assert asset_cross == 0, "Active splits contain cross-split duplicate_asset_group_id"
    
    return {
        'active_risk_groups_cross_split': risk_cross,
        'active_asset_groups_cross_split': asset_cross
    }

def validate_quarantine_reasons(v3_data):
    q_df = v3_data['quarantined']
    counts = q_df['quarantine_reason'].value_counts().to_dict()
    expected = {
        'QUARANTINED_TEST_LINKED_PATIENT_OVERLAP': 62,
        'QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK': 34,
        'QUARANTINED_SAME_ACQUISITION': 13,
        'QUARANTINED_BUSI_PATIENT_OVERLAP': 5,
        'CONSERVATIVE_HIGH_RISK_GROUPING': 3,
        'QUARANTINED_EXACT_DUPLICATE': 1
    }
    assert counts == expected, f"Quarantine counts mismatch. Expected {expected}, got {counts}"
    return counts

def recheck_active_train_val_exact_duplicates(v3_data):
    train_df = v3_data['train']
    val_df = v3_data['val']
    
    train_hashes = {}
    for idx, row in train_df.iterrows():
        with open(row['image_path'], 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        train_hashes[h] = row['sample_id']
        
    val_collisions = []
    for idx, row in val_df.iterrows():
        with open(row['image_path'], 'rb') as f:
            h = hashlib.sha256(f.read()).hexdigest()
        if h in train_hashes:
            val_collisions.append((row['sample_id'], train_hashes[h]))
            
    assert len(val_collisions) == 0, f"Found {len(val_collisions)} exact raw byte collisions between active TRAIN and VAL!"
    return len(val_collisions)


def validate_cross_artifact_consistency(v3_data):
    import json
    quar_list = pd.read_csv(get_path('reports/tables/phase05_v3_quarantine_list.csv'))
    assert set(quar_list['sample_id']) == set(v3_data['quarantined']['sample_id']), "Quarantine list sample IDs don't match manifest."
    assert len(quar_list) == len(v3_data['quarantined']), "Quarantine list length doesn't match manifest."

    audit_json = json.load(open(get_path('reports/audits/phase05_v3_candidate_manifest_audit.json')))
    assert audit_json['active_splits']['TRAIN'] == len(v3_data['train']), "JSON train count mismatch"
    assert audit_json['active_splits']['VAL'] == len(v3_data['val']), "JSON val count mismatch"
    assert audit_json['quarantined_total'] == len(v3_data['quarantined']), "JSON quarantine count mismatch"

    cmp = pd.read_csv(get_path('reports/tables/phase05_v3_dataset_split_comparison.csv'))
    assert cmp['v3_train'].sum() == len(v3_data['train']), "dataset comparison train mismatch"
    assert cmp['v3_val'].sum() == len(v3_data['val']), "dataset comparison val mismatch"
    assert cmp['test_immutable'].sum() == len(v3_data['test']), "dataset comparison test mismatch"

    print("Cross-artifact consistency PASS")

def main():
    print("Executing master validation library...")
    v2_data = load_v2_manifests()
    v3_data = load_v3_candidate()
    
    pop_res = validate_population_accounting(v2_data, v3_data)
    print("Population accounting:", pop_res)
    
    test_res = validate_test_identity()
    print("Test identity:", test_res)
    
    patient_res = validate_patient_disjointness(v3_data)
    print("Patient disjointness:", patient_res)
    
    grp_res = validate_duplicate_groups(v3_data)
    print("Duplicate groups:", grp_res)
    
    q_res = validate_quarantine_reasons(v3_data)
    print("Quarantine reasons:", q_res)
    
    dup_res = recheck_active_train_val_exact_duplicates(v3_data)
    print("Active TRAIN-VAL exact raw byte duplicates:", dup_res)
    
    validate_cross_artifact_consistency(v3_data)
    print("ALL HARDS GATES PASSED (v3 Candidate Validated).")

if __name__ == '__main__':
    main()
