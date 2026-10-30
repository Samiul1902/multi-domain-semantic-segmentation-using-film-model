import os

path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("QUARANTINED_TEST_LINKED_DUPLICATE_RISK", "QUARANTINED_TEST_LINKED_PATIENT_OVERLAP")
text = text.replace("Phase 05 Part 1D-R1", "Phase 05 Part 1D-R4 — Final v3 Candidate Closure")
text = text.replace("Phase 05 Part 1D-R3", "Phase 05 Part 1D-R4")

with open(path, 'w', encoding='utf-8') as f:
    f.write(text)
