import os
path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py'
with open(path, 'r') as f:
    text = f.read()

target = '''display(Markdown("**Figure 5**: Dataset split proportions across v2 vs v3. Maximum observed drift is limited to -1.36% in BUSI VAL, preserving representative multi-domain balance."))'''

replacement = '''
# Programmatic drift calculation
v2_val = v2_all[v2_all['split'] == 'VAL']
v3_val = v3_data['val']
datasets = ['KUB', 'ISIC', 'BUSI', 'KVASIR']
max_drift = 0
max_d_name = ""

for d in datasets:
    count_v2 = len(v2_val[v2_val['dataset'] == d])
    count_v3 = len(v3_val[v3_val['dataset'] == d])
    
    p_v2 = (count_v2 / len(v2_val)) * 100
    p_v3 = (count_v3 / len(v3_val)) * 100
    
    drift = p_v3 - p_v2
    if abs(drift) > abs(max_drift):
        max_drift = drift
        max_d_name = d

display(Markdown(f"**Figure 5**: Dataset split proportions across v2 vs v3. Maximum observed drift is limited to {max_drift:+.2f} percentage points in {max_d_name} VAL, preserving representative multi-domain balance."))
'''

text = text.replace(target, replacement.strip())
with open(path, 'w') as f:
    f.write(text)
