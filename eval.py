import pandas as pd
import hashlib

# 34 counts:
raw = pd.read_csv('D:/Softfors/jup/reports/tables/phase05_test_linked_high_risk_phash_pairs_RAW.csv')
t_t = len(raw[((raw['split_a'] == 'TRAIN') & (raw['split_b'] == 'TEST')) | ((raw['split_b'] == 'TRAIN') & (raw['split_a'] == 'TEST'))])
v_t = len(raw[((raw['split_a'] == 'VAL') & (raw['split_b'] == 'TEST')) | ((raw['split_b'] == 'VAL') & (raw['split_a'] == 'TEST'))])

print(f"TRAIN-TEST: {t_t}")
print(f"VAL-TEST: {v_t}")

# Check distances again:
d0 = len(raw[raw['hamming_distance'] == 0])
d1 = len(raw[raw['hamming_distance'] == 1])
d2 = len(raw[raw['hamming_distance'] == 2])
print(f"d0={d0}, d1={d1}, d2={d2}")

# Datasets
print(raw['dataset_a'].value_counts())

# Notebook SHA
with open('D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/phase05_leakage_safe_manifest_v3_candidate.ipynb', 'rb') as f:
    nb_sha = hashlib.sha256(f.read()).hexdigest()
print(f"NB SHA: {nb_sha}")

# Test SHA (should remain same)
with open('D:/Softfors/jup/manifests/phase4_v3_candidate/test_v3_candidate.csv', 'rb') as f:
    test_sha = hashlib.sha256(f.read()).hexdigest()

print(f"Test SHA: {test_sha}")

v3_all = pd.read_csv('D:/Softfors/jup/manifests/phase4_v3_candidate/all_paired_v3_candidate.csv')
active_tr = len(v3_all[v3_all['split'] == 'TRAIN'])
active_va = len(v3_all[v3_all['split'] == 'VAL'])
q_multi = len(v3_all[(v3_all['split'] == 'QUARANTINED')])
print(f"TR: {active_tr}, VA: {active_va}, MULTI (Q): {q_multi}")
