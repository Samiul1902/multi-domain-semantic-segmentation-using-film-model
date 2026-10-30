import os
import textwrap

path = 'D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py'
with open(path, 'r') as f:
    text = f.read()

text = text.replace('5,859', '5,832').replace('815', '808').replace('84 = 8,441', '118 = 8,441')

append = '''
    add_md("""
## Historical Pre-Lock TEST-Linked pHash High-Risk Reconciliation

Using the historical eports/audits/near_duplicate_candidates.csv pre-lock evidence, we identified candidate pairs across splits with a Hamming distance <= 2 involving the TEST split.

### Results
- **Source**: eports/audits/near_duplicate_candidates.csv
- **Total d<= 2 pairs**: 34
- **Unique development nodes linked to TEST**: 34
- **ISIC**: 31
- **KUB**: 2
- **KVASIR**: 1
- **BUSI**: 0
- **Already quarantined**: 0
- **Newly quarantined**: 34
- **Final remaining active**: 0

The 34 newly identified development samples are formally quarantined under QUARANTINED_TEST_LINKED_PHASH_HIGH_RISK.
TEST imagery remains absolutely intact (0 image reads).
""")

    add_md("""
## 14. Master Artifact SHA-256 Provenance Registry
""")
'''

target_str = '    add_md("""\n## 14. Master Artifact SHA-256 Provenance Registry\n""")'
text = text.replace(target_str, append)

with open(path, 'w') as f:
    f.write(text)
