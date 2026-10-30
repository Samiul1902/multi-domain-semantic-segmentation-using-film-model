import nbformat as nbf

nb = nbf.v4.new_notebook()

text = '''# Phase 05 Part 1D: Leakage-Safe Manifest v3 Candidate

This notebook presents the execution and validation of the versioned leakage-safe manifest candidate (v3). 

**Rule 1 (TEST Immutable)**: TEST items are untouched.
**Rule 2 (Exact Duplicate)**: KUB `patient-00273` vs `patient-00320` is resolved.
**Rule 3/4 (Near Duplicates)**: ISIC d=0 and d=2 cross-split pairs are resolved.
**Rule 6 (BUSI Overlaps)**: Cross-split BUSI patient clusters are resolved.

All resolutions follow a minimal surgery approach: offending members are moved to a `QUARANTINED` split rather than broadly reshuffling the dataset.
'''
nb.cells.append(nbf.v4.new_markdown_cell(text))

code1 = '''import pandas as pd
df_quar = pd.read_csv('../../../manifests/phase4_v3_candidate/quarantined_v3_candidate.csv')
print("Quarantine Summary:")
print(df_quar['quarantine_reason'].value_counts())
'''
nb.cells.append(nbf.v4.new_code_cell(code1))

code2 = '''from IPython.display import Image, display
display(Image(filename='outputs/v3_candidate/v3_split_sizes.png'))
'''
nb.cells.append(nbf.v4.new_code_cell(code2))

code3 = '''display(Image(filename='outputs/v3_candidate/v3_quarantine_reasons.png'))
'''
nb.cells.append(nbf.v4.new_code_cell(code3))

code4 = '''df_train = pd.read_csv('../../../manifests/phase4_v3_candidate/train_v3_candidate.csv')
df_val = pd.read_csv('../../../manifests/phase4_v3_candidate/val_v3_candidate.csv')
df_test = pd.read_csv('../../../manifests/phase4_v3_candidate/test_v3_candidate.csv')
print(f"Final splits -> TRAIN: {len(df_train)}, VAL: {len(df_val)}, TEST: {len(df_test)}")
'''
nb.cells.append(nbf.v4.new_code_cell(code4))

with open('notebooks/phasewise/phase_05_leakage_audit/phase05_leakage_safe_manifest_v3_candidate.ipynb', 'w') as f:
    nbf.write(nb, f)
print('Notebook created.')

