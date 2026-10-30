import os

path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/phase05_validate_v3_candidate.py'
with open(path, 'r') as f:
    text = f.read()

append = '''
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
'''

text = text.replace("def main():", append + "\ndef main():")
text = text.replace("print(\"ALL HARDS GATES PASSED (v3 Candidate Validated).\")", "validate_cross_artifact_consistency(v3_data)\n    print(\"ALL HARDS GATES PASSED (v3 Candidate Validated).\")")

with open(path, 'w') as f:
    f.write(text)
