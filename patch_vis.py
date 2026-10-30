import os

path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/phase05_v3_visualization.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("'Quarantine Cases by Dataset and Specific Governance Reason (N=84)'", "f'Quarantine Cases by Dataset and Specific Governance Reason (N={len(v3_qu)})'")
text = text.replace("QUARANTINED_TEST_LINKED_DUPLICATE_RISK", "QUARANTINED_TEST_LINKED_PATIENT_OVERLAP")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
