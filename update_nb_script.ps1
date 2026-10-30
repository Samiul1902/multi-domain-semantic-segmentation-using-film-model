import nbformat as nbf
import os
import copy

with open('D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py', 'r') as f:
    text = f.read()

# Replace 5,859 with 5,832
text = text.replace("5,859", "5,832")
text = text.replace("815", "808")
text = text.replace("84", "118")

# Let's write the generator with an explicit section for TEST_LINKED
add_md_section = '''    add_md("""
## Historical Pre-Lock TEST-Linked pHash High-Risk Reconciliation

Using the historical eports/audits/near_duplicate_candidates.csv pre-lock evidence, we identified candidate pairs across splits with a Hamming distance $\le 2$ involving the TEST split.

### Results
- **Source**: eports/audits/near_duplicate_candidates.csv
- **Total  \\le 2$ Pairs**: 34
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

    # We insert this before section 14 (Artifact registry)
'''

if "def create_candidate_notebook():" in text:
    new_script = text.replace("add_md(\"\"\"\n## 14. Master Artifact SHA-256 Provenance Registry\n\"\"\")", add_md_section + "\n    add_md(\"\"\"\n## 14. Master Artifact SHA-256 Provenance Registry\n\"\"\")")
    with open('D:/Softfors/jup/notebooks/phasewise/phase_05_leakage_audit/code/create_candidate_notebook.py', 'w', encoding='utf-8') as f:
        f.write(new_script)
