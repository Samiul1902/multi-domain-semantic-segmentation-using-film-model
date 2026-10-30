import os
import re

path1 = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/phase05_v3_visualization.py'
with open(path1, 'r', encoding='utf-8') as f:
    t = f.read()
t = re.sub(r'\(N=84\)', '{len(v3_qu)}', t)
t = t.replace("Quarantine Cases by Dataset and Specific Governance Reason {len(v3_qu)}", "Quarantine Cases by Dataset and Specific Governance Reason (N={len(v3_qu)})")
t = t.replace('QUARANTINED_TEST_LINKED_DUPLICATE_RISK', 'QUARANTINED_TEST_LINKED_PATIENT_OVERLAP')
with open(path1, 'w', encoding='utf-8') as f:
    f.write(t)

path2 = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py'
with open(path2, 'r', encoding='utf-8') as f:
    t = f.read()
t = t.replace('QUARANTINED_TEST_LINKED_DUPLICATE_RISK', 'QUARANTINED_TEST_LINKED_PATIENT_OVERLAP')
t = t.replace('Part 1D-R1', 'Part 1D-R4 — Final v3 Candidate Closure')
t = t.replace('Part 1D-R3', 'Part 1D-R4')
with open(path2, 'w', encoding='utf-8') as f:
    f.write(t)
