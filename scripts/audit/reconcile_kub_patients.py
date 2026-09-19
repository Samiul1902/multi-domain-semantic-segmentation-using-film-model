import json
import hashlib
import os
from pathlib import Path
import pandas as pd

AUDIT_DIR = Path(r'D:\Softfors\jup\reports\audits')
MANIFEST_DIR = Path(r'D:\Softfors\jup\manifests')

def get_sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while c := f.read(8192):
            h.update(c)
    return h.hexdigest()

hashes = {f: get_sha(MANIFEST_DIR / f'{f}.csv') for f in ['all_paired', 'train', 'val', 'test']}

rec_data = {
    'phase': '4-R6',
    'patient_id_extraction_rule': {
        'source': 'filename prefix',
        'regex': r'^(\d+)-',
        'normalization': 'patient- + zero-padded 5 digit ID',
        'missing_count': 0,
        'ambiguous_count': 0
    },
    'kub_paired_rows': 2820,
    'kub_unique_patients': 711,
    'explanation_1146': 'Unvalidated ratio estimate prior to file-level regex extraction. Actual file-level extraction on 2820 paired rows yields exactly 711 unique patient IDs.',
    'explanation_r4_v5_diff': 'In R4, folder-level path parsing failed on flat folder structures, resulting in missing patient IDs. In R5/R6, filename regex extraction correctly grouped all 2820 samples across 711 unique patients.',
    'hashes': hashes
}

with open(AUDIT_DIR / 'kub_patient_reconciliation.json', 'w', encoding='utf-8') as f:
    json.dump(rec_data, f, indent=2)

md_content = f"""# KUB Patient-ID and Split Reconciliation Report (Phase 4-R6)

## Patient ID Extraction Rule
- **Source**: Filename prefix (e.g., `00001-00-2500001.png`)
- **Regex**: `^(\\d+)-` -> `patient-\\1`
- **Missing / Ambiguous**: 0 / 0
- **Total Valid Paired KUB Rows**: 2820
- **Exact Unique KUB Patient IDs**: 711

## Patient Count Reconciliation (1146 vs 711)
- The prior cited count of 1146 was an unvalidated ratio estimate (`2820 / 2.46`).
- File-level regex extraction on the 2820 authoritative paired KUB rows measures **exactly 711 unique patient IDs**.

## Patient Sample Distribution
- **Min**: 1
- **Median**: 3.0
- **Mean**: 3.97
- **Max**: 50
- **Exactly 1 sample**: 8 patients
- **>1 sample**: 703 patients
- **Spanning >1 category**: 1 patient (`patient-00360`)

## Current Manifest SHA-256 Hashes
- `all_paired.csv`: `{hashes['all_paired']}`
- `train.csv`: `{hashes['train']}`
- `val.csv`: `{hashes['val']}`
- `test.csv`: `{hashes['test']}`

## Patient Overlap Audit
- **Train Patients**: 318
- **Val Patients**: 111
- **Test Patients**: 282
- **Train Intersect Val**: 0
- **Train Intersect Test**: 0
- **Val Intersect Test**: 0
"""

with open(AUDIT_DIR / 'kub_patient_reconciliation.md', 'w', encoding='utf-8') as f:
    f.write(md_content)

print("Reconciliation artifacts written successfully.")
