import os

path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('(84)', '(118)')
text = text.replace('(N=84)', '(N=118)')
text = text.replace('The 84 quarantined', 'The 118 quarantined')
text = text.replace('the 84 Quarantined', 'the 118 Quarantined')

text = text.replace('eports/audits/near_duplicate_candidates.csv', 'reports/audits/near_duplicate_candidates.csv')
text = text.replace('Part 1D-R1', 'Part 1D-R3')

with open(path, 'w') as f:
    f.write(text)
