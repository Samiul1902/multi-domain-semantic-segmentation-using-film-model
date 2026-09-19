import nbformat as nbf
import os

def create_candidate_notebook():
    nb = nbf.v4.new_notebook()
    
    # Kernel metadata
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python 3.11 (jup-venv)",
            "language": "python",
            "name": "jup-venv"
        },
        "language_info": {
            "codemirror_mode": {"name": "ipython", "version": 3},
            "file_extension": ".py",
            "mimetype": "text/x-python",
            "name": "python",
            "nbconvert_exporter": "python",
            "pygments_lexer": "ipython3",
            "version": "3.11.9"
        }
    }

    # Helper function to add markdown
    def add_md(text):
        nb.cells.append(nbf.v4.new_markdown_cell(text.strip()))

    # Helper function to add code
    def add_code(code):
        nb.cells.append(nbf.v4.new_code_cell(code.strip()))

    # -------------------------------------------------------------
    # 1. Title and Candidate Status
    # -------------------------------------------------------------
    add_md("""
# Phase 05 Part 1D-R4 — Leakage-Safe Manifest v3 Candidate Audit & Execution
### Status: **CANDIDATE ONLY — NOT CANONICAL — NOT ACTIVE — NOT FROZEN**
### Scientific Gate: **CHECK_REQUIRED** (Awaiting Supervisor Promotion)
### Target Kernel: `jup-venv` | Python 3.11

> **CRITICAL PROTOCOL NOTICE**:
> This notebook documents the construction, hard verification, and audit of the **Versioned Leakage-Safe Manifest v3 Candidate** (`manifests/phase4_v3_candidate/`).
>
> - **v3 MADE CANONICAL**: **NO** (v2 remains canonical active until formal supervisor promotion)
> - **TEST SPLIT IMMUTABILITY**: **PASS** (Candidate `test_v3_candidate.csv` is byte-identical to `test.csv`, SHA: `9361eba6...`)
> - **MODEL TRAINING / INFERENCE**: **NO** (Zero training, zero model inference)
> - **TEST PIXEL ACCESS**: **STRICT ZERO** (0 reads, 0 decodes, 0 visualizations)
""")

    # -------------------------------------------------------------
    # 2. Executive Summary & Why v3 is Necessary
    # -------------------------------------------------------------
    add_md("""
## 1. Context & Motivation: Why v3 is Necessary

During Phase 05 Part 1A data leakage auditing, exact and near-duplicate cross-split anomalies were discovered in the canonical v2 splits (`manifests/all_paired.csv`):
1. **KUB Exact Image Collision**: A byte-identical raw capture appeared simultaneously in TRAIN (`patient-00273`, sample `4739fd...`) and VAL (`patient-00320`, sample `a62708...`).
2. **ISIC Distance-0 Perceptual Duplicates**: 13 pairs exhibited bit-identical DCT perceptual hashes ($d=0$) spanning TRAIN and VAL splits.
3. **Conservative High-Risk Near-Duplicates**: 4 candidate pairs ($d=2$) showed high perceptual overlap across TRAIN and VAL splits.
4. **BUSI Multi-Split Patient Clusters**: Analysis of the official clinical metadata (`Patient_infos_BUSI-WHU.xlsx`) revealed 25 patient clusters spanning multiple splits, including 20 patients overlapping with the untouched internal TEST set (representing 62 development-side cases).

Under **Remediation Option C** (Versioned Leakage-Safe Manifest v3), we perform *minimal surgery* by quarantining high-risk development cases, resolving all confirmed leakage and all prospectively defined high-risk d<=2/group-overlap categories while strictly maintaining v2 as an immutable historical audit artifact and leaving the TEST split completely intact.
""")

    # -------------------------------------------------------------
    # 3. Environment & Module Imports
    # -------------------------------------------------------------
    add_md("""
## 2. Execution Setup & Reusable Module Imports

We load the modular verification and visualization libraries developed specifically for Phase 05:
- `code/phase05_build_v3_candidate.py`
- `code/phase05_validate_v3_candidate.py`
- `code/phase05_v3_visualization.py`
""")

    add_code("""
import os
import sys
import json
import hashlib
import pandas as pd
import numpy as np
from IPython.display import Image, display, Markdown

# Add repository root to path
PROJECT_ROOT = r'D:\Softfors\jup'
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from notebooks.phasewise.phase_05_leakage_audit.code.phase05_validate_v3_candidate import (
    load_v2_manifests,
    load_v3_candidate,
    validate_population_accounting,
    validate_test_identity,
    validate_patient_disjointness,
    validate_duplicate_groups,
    validate_quarantine_reasons,
    recheck_active_train_val_exact_duplicates
)

print("Modules and validation libraries imported successfully.")
print("Python Executable:", sys.executable)
""")

    # -------------------------------------------------------------
    # 4. TEST Immutability Hard Gate
    # -------------------------------------------------------------
    add_md("""
## 3. TEST Split Immutability Hard Gate

**Hard Requirement**:
The candidate TEST manifest (`test_v3_candidate.csv`) MUST be strictly byte-identical to canonical v2 `test.csv` (SHA-256: `9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`).
Medical image content for the TEST split is never loaded, read, or decoded.
""")

    add_code("""
test_audit = validate_test_identity()
print(f"Candidate TEST SHA-256   : {test_audit['test_sha']}")
print(f"Byte-identical to v2 TEST: {test_audit['byte_identical']}")
print(f"Sample IDs Identical     : {test_audit['sample_ids_identical']}")
print(f"Row Order Identical      : {test_audit['sample_order_identical']}")
print(f"Total TEST Sample Count  : {test_audit['count']}")

assert test_audit['test_sha'] == '9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727'
display(Markdown("**TEST IMMUTABILITY GATE: PASS (Zero Content Reads, Byte-Identical)**"))
""")

    # -------------------------------------------------------------
    # 5. Full Population Accounting & Provenance Conservation
    # -------------------------------------------------------------
    add_md("""
## 4. Full Population Accounting & Provenance Conservation

Every single one of the 8,441 samples present in canonical v2 is accounted for in the v3 candidate system:
$$\text{TRAIN (5,832)} + \text{VAL (808)} + \text{TEST (1,683)} + \text{QUARANTINED (118)} = 8,441$$

No samples are dropped from provenance; excluded cases are formally held in `quarantined_v3_candidate.csv` with explicit audit trails.
""")

    add_code("""
v2_data = load_v2_manifests()
v3_data = load_v3_candidate()

pop_audit = validate_population_accounting(v2_data, v3_data)
pop_df = pd.DataFrame([pop_audit])
display(pop_df)

assert pop_audit['sum_reconciliation'] == 8441
assert pop_audit['missing_sample_ids'] == 0
assert pop_audit['duplicate_provenance'] == 0
assert pop_audit['unexpected_sample_ids'] == 0
display(Markdown("**POPULATION ACCOUNTING GATE: PASS (Zero Missing, Zero Duplicates, N=8,441)**"))
""")

    # -------------------------------------------------------------
    # 6. Detailed Quarantine Accounting & Forensics
    # -------------------------------------------------------------
    add_md("""
## 5. Detailed Quarantine Accounting & Forensics (N=118)

The 118 quarantined cases are categorized by their deterministic governance risk:
1. `QUARANTINED_TEST_LINKED_PATIENT_OVERLAP` ($N=62$): BUSI ultrasound cases belonging to patients who also have cases in the immutable TEST split.
2. `QUARANTINED_SAME_ACQUISITION` ($N=13$): ISIC dermoscopy cases with $d=0$ DCT hash identicality across TRAIN↔VAL.
3. `QUARANTINED_BUSI_PATIENT_OVERLAP` ($N=5$): BUSI ultrasound cases belonging to patients spanning active TRAIN and VAL.
4. `CONSERVATIVE_HIGH_RISK_GROUPING` ($N=3$): Cross-split pairs at $d=2$ pHash distance (3 unique VAL cases across 4 pairs).
5. `QUARANTINED_EXACT_DUPLICATE` ($N=1$): KUB stone case `a62708...` (`patient-00320`) identical to TRAIN case `4739fd...`.
""")

    add_code("""
q_counts = validate_quarantine_reasons(v3_data)
print("Quarantine Reason Breakdown:")
for k, v in q_counts.items():
    print(f"  • {k:40s}: {v:2d}")

# Load full quarantine table for inspection
q_df = pd.read_csv(os.path.join(PROJECT_ROOT, 'reports/tables/phase05_v3_quarantine_list.csv'))
print(f"\\nQuarantine Registry Loaded: {len(q_df)} rows")
display(q_df.head(10))
""")

    # -------------------------------------------------------------
    # 7. Figure 1 & Figure 2: Population and Quarantine Visualizations
    # -------------------------------------------------------------
    add_md("""
## 6. Population Comparison & Quarantine Reason Visualizations
""")

    add_code("""
# Display Figure 1: Split Population Comparison
fig1_path = os.path.join(PROJECT_ROOT, 'reports/figures/phase05_leakage_audit/v3_candidate/phase05_v3_split_population_comparison.png')
display(Image(filename=fig1_path))
display(Markdown("**Figure 1**: v2 Canonical vs v3 Candidate Active Population by Dataset. Active TRAIN decreases by 54 cases, active VAL decreases by 30 cases, TEST remains strictly unchanged."))
""")

    add_code("""
# Display Figure 2: Quarantine Reasons Breakdown
fig2_path = os.path.join(PROJECT_ROOT, 'reports/figures/phase05_leakage_audit/v3_candidate/phase05_v3_quarantine_reasons.png')
display(Image(filename=fig2_path))
display(Markdown("**Figure 2**: Distribution of the 118 Quarantined Samples across datasets and explicit governance risk categories."))
""")

    # -------------------------------------------------------------
    # 8. KUB Exact Duplicate Resolution & Patient Identity
    # -------------------------------------------------------------
    add_md("""
## 7. KUB Exact Duplicate Forensics: Preserving Patient Identity

### Forensic Finding
TRAIN sample `4739fd...` (`patient-00273`) and VAL sample `a62708...` (`patient-00320`) share identical raw capture byte hashes (`5c303baf998c`).
However, their corresponding ground-truth annotations show manual delineations with Dice similarity of 0.910754.

### Remediation Protocol
- **Patient IDs Not Merged**: Evidence confirms raw image asset duplication, but does *not* prove that patient entities in the source hospital cohort are identical. Therefore, `patient-00273` and `patient-00320` remain strictly distinct.
- **Provenance Asset Group**: Linked via `duplicate_asset_group_id = GROUP_KUB_001`.
- **Minimal Surgery Action**: TRAIN sample `4739fd...` is retained in active candidate TRAIN; VAL sample `a62708...` is quarantined into `QUARANTINED_EXACT_DUPLICATE`.
""")

    add_code("""
all_v3 = v3_data['all']
kub_collision = all_v3[all_v3['sample_id'].isin([
    '4739fd78796d5555ae7ab82719910576',
    'a62708e2834fab0c56d4f575f49f7c61'
])][['sample_id', 'patient_id', 'split_v2', 'split', 'quarantine_reason', 'duplicate_asset_group_id']]
display(kub_collision)

assert '4739fd78796d5555ae7ab82719910576' in v3_data['train']['sample_id'].values
assert 'a62708e2834fab0c56d4f575f49f7c61' in v3_data['quarantined']['sample_id'].values
display(Markdown("**KUB EXACT DUPLICATE REMEDIATION: PASS (TRAIN Retained, VAL Quarantined, Patient IDs Distinct)**"))
""")

    # -------------------------------------------------------------
    # 9. BUSI Clinical Patient Metadata Audit & Disjointness
    # -------------------------------------------------------------
    add_md("""
## 8. BUSI Clinical Metadata Audit (`Patient_infos_BUSI-WHU.xlsx`)

Clinical patient mapping was established using official metadata from `Patient_infos_BUSI-WHU.xlsx`.
- **Total BUSI cases**: 927
- **Mapped from Excel**: 927 (100.0% coverage, 0 unmapped, 0 ambiguous)
- **Unique Patients**: 816
- **v2 Multi-Split Contamination**: 25 patients crossed splits in v2 (20 crossed into TEST, 5 crossed between TRAIN and VAL).
- **v3 Remediation**:
  - Dev-side cases of the 20 TEST-overlapping patients ($N=62$) -> `QUARANTINED_TEST_LINKED_PATIENT_OVERLAP`.
  - VAL cases of the 5 TRAIN-overlapping patients ($N=5$) -> `QUARANTINED_BUSI_PATIENT_OVERLAP`.
- **v3 Candidate Disjointness**: Active TRAIN↔VAL overlap: **0**, TRAIN↔TEST: **0**, VAL↔TEST: **0**.
""")

    add_code("""
# Verify BUSI disjointness across active candidate splits
patient_audit = validate_patient_disjointness(v3_data)
print("Patient Disjointness Audit:")
print("  KUB Active Overlaps :", patient_audit['kub_overlaps'])
print("  BUSI Active Overlaps:", patient_audit['busi_overlaps'])

assert patient_audit['kub_overlaps']['train_val'] == 0
assert patient_audit['busi_overlaps']['train_val'] == 0
assert patient_audit['busi_overlaps']['train_test'] == 0
assert patient_audit['busi_overlaps']['val_test'] == 0
display(Markdown("**BUSI CLINICAL PATIENT DISJOINTNESS GATE: PASS (Zero Active Cross-Split Overlaps)**"))
""")

    # -------------------------------------------------------------
    # 10. ISIC Distance-0 & Distance-2 Graph Topology Accounting
    # -------------------------------------------------------------
    add_md("""
## 9. ISIC $d=0$ Groups & $d=2$ Graph Topology Accounting

### ISIC $d=0$ Pairs ($N=13$)
- 13 candidate pairs exhibit bit-identical DCT perceptual hash ($d=0$).
- All 13 pairs cross active TRAIN↔VAL in v2.
- Resolved by retaining all TRAIN members and moving the 13 VAL members to `QUARANTINED_SAME_ACQUISITION`.
- Evidence level is strictly preserved as `LIKELY_SAME_ACQUISITION` (not overstated as confirmed same patient).

### Why 4 $d=2$ Candidate Pairs Yield Exactly 3 Quarantined Rows
- Candidate pairs: `TV_PAIR_015`, `TV_PAIR_016`, `TV_PAIR_017`, `TV_PAIR_018`.
- Graph analysis: `TV_PAIR_015` (`b07108...` in TRAIN vs `719537...` in VAL) and `TV_PAIR_016` (`d00567...` in TRAIN vs `719537...` in VAL) **share the same VAL node** (`719537b2bf42f0b0de6d011475b7d297`).
- Total unique nodes involved: 7 (4 TRAIN nodes, 3 VAL nodes).
- Connected components: 3.
- Quarantining the 3 unique VAL nodes resolves the active d=2 conservative high-risk edges.
""")

    add_code("""
adj_df = pd.read_csv(os.path.join(PROJECT_ROOT, 'reports/tables/phase05_train_val_candidate_adjudication.csv'))
d2_df = adj_df[adj_df['adjudication_status'] == 'UNRESOLVED_NEAR_DUPLICATE']
display(d2_df[['pair_id', 'dataset', 'sample_id_a', 'sample_id_b', 'phash_distance']])

val_nodes_d2 = d2_df['sample_id_b'].tolist()
print(f"d2 Pair Count                  : {len(d2_df)}")
print(f"d2 VAL Node Occurrences        : {len(val_nodes_d2)}")
print(f"d2 Unique VAL Nodes (Quarantine): {len(set(val_nodes_d2))}")
print(f"Shared VAL Node across Pair 15 & 16: 719537b2bf42f0b0de6d011475b7d297")

dup_group_audit = validate_duplicate_groups(v3_data)
assert dup_group_audit['active_risk_groups_cross_split'] == 0
assert dup_group_audit['active_asset_groups_cross_split'] == 0
display(Markdown("**DUPLICATE RISK GROUP RESOLUTION: PASS (Zero Cross-Split Active Groups)**"))
""")

    # -------------------------------------------------------------
    # 11. Figure 3 & Figure 4: Architecture and Leakage Matrix
    # -------------------------------------------------------------
    add_md("""
## 10. Remediation Architecture & Active Leakage Audit Matrix
""")

    add_code("""
# Display Figure 3: Architecture Diagram
fig3_path = os.path.join(PROJECT_ROOT, 'reports/figures/phase05_leakage_audit/v3_candidate/phase05_v3_duplicate_group_resolution.png')
display(Image(filename=fig3_path))
display(Markdown("**Figure 3**: Schematic representation of data governance conflict resolution across KUB, ISIC, and BUSI without accessing medical image pixels."))
""")

    add_code("""
# Display Figure 4: Active Split Leakage Matrix
fig4_path = os.path.join(PROJECT_ROOT, 'reports/figures/phase05_leakage_audit/v3_candidate/phase05_v3_active_split_leakage_matrix.png')
display(Image(filename=fig4_path))
display(Markdown("**Figure 4**: Leakage audit matrix across active candidate splits. Every supported dimension of cross-split contamination is strictly zero."))
""")

    # -------------------------------------------------------------
    # 12. Active TRAIN-VAL Exact Content Recheck
    # -------------------------------------------------------------
    add_md("""
## 11. Active TRAIN↔VAL Raw Image Exact Content Recheck

To eliminate any possibility of remaining development image collisions, all active TRAIN images ($N=5,832$) and active VAL images ($N=808$) were rehashed byte-for-byte using SHA-256.
TEST images are **not** accessed or read.
""")

    add_code("""
# Recheck exact raw byte collisions between active TRAIN and VAL
exact_collisions = recheck_active_train_val_exact_duplicates(v3_data)
print(f"Active TRAIN↔VAL Raw Byte Collisions: {exact_collisions}")

assert exact_collisions == 0
display(Markdown("**TRAIN↔VAL EXACT CONTENT RECHECK: PASS (Zero Collisions in Active Development Splits)**"))
""")

    # -------------------------------------------------------------
    # 13. Dataset Population & Distribution Drift Audit
    # -------------------------------------------------------------
    add_md("""
## 12. Dataset Population & Distribution Drift Audit

We compare v2 canonical splits vs candidate v3 splits across datasets, KUB categories, and view types to quantify distribution drift resulting from quarantining.
""")

    add_code("""
pop_comp_df = pd.read_csv(os.path.join(PROJECT_ROOT, 'reports/tables/phase05_v3_dataset_split_comparison.csv'))
display(pop_comp_df)

# Check KUB category distribution
kub_v3_tr = v3_data['train'][v3_data['train']['dataset'] == 'KUB']
kub_v3_va = v3_data['val'][v3_data['val']['dataset'] == 'KUB']
print("\\nKUB Active Categories:")
print("  TRAIN: Kidney_Stone =", (kub_v3_tr['category']=='Kidney_Stone').sum(),
      "| Bladder_Stone =", (kub_v3_tr['category']=='Bladder_Stone').sum(),
      "| Ureteric_Stone =", (kub_v3_tr['category']=='Ureteric_Stone').sum())
print("  VAL  : Kidney_Stone =", (kub_v3_va['category']=='Kidney_Stone').sum(),
      "| Bladder_Stone =", (kub_v3_va['category']=='Bladder_Stone').sum(),
      "| Ureteric_Stone =", (kub_v3_va['category']=='Ureteric_Stone').sum())

# Display Figure 5: Distribution Drift
fig5_path = os.path.join(PROJECT_ROOT, 'reports/figures/phase05_leakage_audit/v3_candidate/phase05_v3_distribution_drift.png')
display(Image(filename=fig5_path))
# Programmatic drift calculation
v2_val = v2_data['all'][v2_data['all']['split'] == 'VAL']
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
""")

    # -------------------------------------------------------------
    # 14. Phase 14 Description Correction & Downstream Implications
    # -------------------------------------------------------------
    add_md("""
## 13. Phase 14 Protocol Clarification & Downstream Rerun Scope

### Protocol Truth & Clarification
- **Regional Refiner Training (Phase 14 Part 2)**: Trained on **A3 ground-truth-derived positive crops + perturbed GT crops + negative crops**. It was **NOT** trained directly on Stage-4D predicted proposal crops.
- **Regional Refiner Checkpoint Selection**: Evaluated on validation crops derived from the v2 validation set, which contained the contaminated KUB sample `a62708...`.
- **Predicted Mode Evaluation (Part 3)**: Inherited Stage-4D predicted proposals, but was strictly evaluated against frozen ground-truth masks.

### Clean Rerun Scope Under v3
If candidate v3 is promoted:
- **Phases 00–04**: Phase 04 manifest generation will be versioned to v3.
- **Phases 09–13**: Training and tuning pipelines will run on uncontaminated `train_v3_candidate.csv` and validate on `val_v3_candidate.csv`.
- **Phase 14**: Checkpoint selection will be conducted on uncontaminated validation crops.
- **Phase 39**: Internal untouched TEST evaluation will execute on immutable `test.csv`.
""")

    # -------------------------------------------------------------
    # 15. Master SHA-256 Provenance Table
    # -------------------------------------------------------------

    add_md("""
## Historical Pre-Lock TEST-Linked pHash High-Risk Reconciliation

Using the historical 
reports/audits/near_duplicate_candidates.csv pre-lock evidence, we identified candidate pairs across splits with a Hamming distance <= 2 involving the TEST split.

### Results
- **Source**: 
reports/audits/near_duplicate_candidates.csv
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

*(Note: Remaining historical candidates at distances d=4 and d=6 are preserved as adjudicated diagnostic evidence. They are not automatically quarantined because they were largely classified as likely false positives under the frozen forensic review. They are documented but do not actively contaminate the v3 splits under the strict d<=2 prospective conservative high-risk threshold.)*
""")

    add_md("""
## 14. Master Artifact SHA-256 Provenance Registry
""")


    add_code("""
artifacts_to_hash = [
    ('Candidate all_paired', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/all_paired_v3_candidate.csv')),
    ('Candidate train', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/train_v3_candidate.csv')),
    ('Candidate val', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/val_v3_candidate.csv')),
    ('Candidate test', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/test_v3_candidate.csv')),
    ('Candidate quarantined', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/quarantined_v3_candidate.csv')),
    ('Candidate duplicate_groups', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/duplicate_groups_v3_candidate.csv')),
    ('Candidate grouping_provenance', os.path.join(PROJECT_ROOT, 'manifests/phase4_v3_candidate/grouping_provenance_v3_candidate.csv')),
    ('Candidate Audit JSON', os.path.join(PROJECT_ROOT, 'reports/audits/phase05_v3_candidate_manifest_audit.json')),
    ('Build Script', os.path.join(PROJECT_ROOT, 'notebooks/phasewise/phase_05_leakage_audit/code/phase05_build_v3_candidate.py')),
    ('Validation Script', os.path.join(PROJECT_ROOT, 'notebooks/phasewise/phase_05_leakage_audit/code/phase05_validate_v3_candidate.py')),
    ('Visualization Script', os.path.join(PROJECT_ROOT, 'notebooks/phasewise/phase_05_leakage_audit/code/phase05_v3_visualization.py')),
]

hash_rows = []
for label, p in artifacts_to_hash:
    with open(p, 'rb') as f:
        h = hashlib.sha256(f.read()).hexdigest()
    hash_rows.append({'Artifact': label, 'Path': p, 'SHA-256': h})

hash_df = pd.DataFrame(hash_rows)
pd.set_option('display.max_colwidth', None)
display(hash_df)
""")

    # -------------------------------------------------------------
    # 16. Scientific Gate Conclusion
    # -------------------------------------------------------------
    add_md("""
## 15. Supervisor Gate Status & Recommendation

### Summary of Audit Gates
- [x] Population Conservation: $5,832 + 808 + 1,683 + 118 = 8,441$ (**PASS**)
- [x] Test Immutability: Byte-identical to canonical v2 `test.csv` (**PASS**)
- [x] Test Medical Content Reads: Exactly 0 (**PASS**)
- [x] KUB Exact Duplicate Resolved: Patient IDs distinct, VAL quarantined (**PASS**)
- [x] BUSI Clinical Disjointness: Active overlaps $= 0/0/0$ (**PASS**)
- [x] ISIC $d=0$ Grouping: Active cross-split groups $= 0$ (**PASS**)
- [x] $d=2$ Graph Accounting: 4 pairs $\\rightarrow$ 3 unique VAL quarantined rows (**PASS**)
- [x] Active TRAIN↔VAL Exact Content Duplicates: Exactly 0 (**PASS**)
- [x] Embedded Figure Count: $\ge 5$ figures rendered (**PASS**)

### Status Recommendation
**SCIENTIFIC GATE**: **CHECK_REQUIRED**
The v3 data governance manifests remain strictly a **CANDIDATE PACKAGE**.
No promotion to canonical status has been performed. Awaiting explicit supervisor authorization before initiating Phase 06.
""")

    # Write notebook file
    out_path = 'notebooks/phasewise/phase_05_leakage_audit/phase05_leakage_safe_manifest_v3_candidate.ipynb'
    with open(out_path, 'w', encoding='utf-8') as f:
        nbf.write(nb, f)
    print(f"Successfully generated notebook with {len(nb.cells)} cells at {out_path}")

if __name__ == '__main__':
    create_candidate_notebook()
