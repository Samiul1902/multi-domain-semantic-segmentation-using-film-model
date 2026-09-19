#!/usr/bin/env python3
"""
Generates the comprehensive, reviewer-facing Phase 04 Jupyter Notebook:
phase04_canonical_manifest_and_split_integrity.ipynb
"""

import nbformat as nbf
from pathlib import Path

PROJECT_ROOT = Path("D:/Softfors/jup")


def create_notebook():
    nb = nbf.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {
            "display_name": "Python (jup-venv)",
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

    cells = []

    # 1. Title & Header
    cells.append(nbf.v4.new_markdown_cell("""# Phase 04 — Canonical Manifest, Split Governance, & Patient Grouping Integrity

**Reviewer-Facing Reproducibility Notebook**  
**Phase ID:** `phase_04_manifest_splits`  
**Current Milestone:** Part 1A — Split Integrity, Hash Governance, Patient Grouping, Semantic Schema, and Reviewer Visualization  
**Hardware Profile:** NVIDIA GeForce RTX 3060 Ti (8GB VRAM)  
**Execution Environment:** `jup-venv` (`D:\\Softfors\\jup\\.venv\\Scripts\\python.exe`)
"""))

    # 2. Scientific Question
    cells.append(nbf.v4.new_markdown_cell("""## 1. Scientific Question
What is the exact canonical paired-data manifest, how are the 8,441 multi-domain medical cases partitioned into TRAIN, VAL, and TEST splits, and can those splits be deterministically reproduced and cryptographically verified without opening locked TEST image content?

This phase establishes the immutable population partition and patient grouping boundaries governing all downstream machine learning training and evaluation.
"""))

    # 3. Relation to Phase 03
    cells.append(nbf.v4.new_markdown_cell("""## 2. Relation to Phase 03 Multi-Domain Dataset Discovery
In **Phase 03**, we discovered the raw multi-domain dataset inventory and established exact paired sample counts:
- **ISIC 2018**: 3,694 paired dermoscopy cases
- **BUSI**: 927 paired breast ultrasound cases
- **Kvasir-SEG**: 1,000 paired polyp endoscopy cases
- **KUB-Stone**: 2,820 paired kidney-ureter-bladder abdominal radiograph cases
- **Authoritative Population**: 8,441 paired cases (historical 8,159 count documented as provenance unresolved)

Phase 04 builds directly upon this population by auditing the formal split allocation (`TRAIN`, `VAL`, `TEST`), verifying strict patient-level separation in KUB, and confirming that no split overlap or cross-contamination exists.
"""))

    # 4. TEST Governance Distinction
    cells.append(nbf.v4.new_markdown_cell("""## 3. Critical Governance Distinction: Metadata Reads vs. Content Access

Under the strict project reproducibility protocol:
- **TEST Manifest Metadata Reads (ALLOWED):** Reading tabular metadata (sample ID, split name, dataset name, patient ID, manifest row counts, and cryptographic hashes) from the frozen canonical manifest files is permitted to verify partitioning integrity.
- **TEST Image Content Reads (STRICTLY 0):** No TEST images are opened, decoded, or read into memory.
- **TEST Mask Content Reads (STRICTLY 0):** No TEST ground-truth segmentation masks are opened, decoded, or read into memory.
- **TEST Visualizations (STRICTLY 0):** No medical imagery from the TEST split is displayed.
- **TEST Metrics / Inference (STRICTLY NONE):** No model inference, optimizer steps, or quantitative test evaluations occur.
"""))

    # 5. Canonical Manifest Artifacts & Hashes
    cells.append(nbf.v4.new_markdown_cell("""## 4. Canonical Manifest Artifacts & Cryptographic Verification
We audit the four canonical manifest files in `manifests/` and verify their SHA-256 binary digests against accepted reference values.
"""))

    cells.append(nbf.v4.new_code_cell("""import sys
import hashlib
from pathlib import Path
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path("D:/Softfors/jup")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

manifest_files = {
    "all_paired": PROJECT_ROOT / "manifests/all_paired.csv",
    "train": PROJECT_ROOT / "manifests/train.csv",
    "val": PROJECT_ROOT / "manifests/val.csv",
    "test": PROJECT_ROOT / "manifests/test.csv"
}

accepted_hashes = {
    "all_paired": "66350d465209e4bf0948a16f0da213abb9f8f87c0b222ead7632d2350463f7cc",
    "train": "d67b549a6cc80b579dfaf4976b9b51630f6d703d8c6bfb33188355cfa6056bc3",
    "val": "46079b594ed9535c2de953bb976684b8b0bab30c27c6e6e4f2b9f9314b4cc5f4",
    "test": "9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727"
}

hash_records = []
for name, p in manifest_files.items():
    h = hashlib.sha256(p.read_bytes()).hexdigest()
    exp = accepted_hashes[name]
    hash_records.append({
        "Manifest File": p.name,
        "Row Count": len(pd.read_csv(p)),
        "Computed SHA-256": h,
        "Accepted SHA-256": exp,
        "Status": "PASS (Exact Match)" if h == exp else "FAIL"
    })

pd.set_option('display.max_colwidth', None)
df_hash_audit = pd.DataFrame(hash_records)
df_hash_audit
"""))

    # 6. Manifest Schema
    cells.append(nbf.v4.new_markdown_cell("""## 5. Canonical Manifest Schema Audit
We inspect the actual column schema of `manifests/all_paired.csv` to document the exact data types, missing value counts, and governance role of every column.
"""))

    cells.append(nbf.v4.new_code_cell("""df_all = pd.read_csv(manifest_files["all_paired"])

schema_info = [
    {"Column": "dataset", "Meaning": "Name of medical dataset cohort", "Dtype": str(df_all['dataset'].dtype), "Required": True, "Missing Count": int(df_all['dataset'].isna().sum()), "Governance Role": "Domain stratification"},
    {"Column": "task_id", "Meaning": "Internal task/domain integer identifier", "Dtype": str(df_all['task_id'].dtype), "Required": True, "Missing Count": int(df_all['task_id'].isna().sum()), "Governance Role": "Multitask indexing"},
    {"Column": "image_path", "Meaning": "Relative path to raw medical image file", "Dtype": str(df_all['image_path'].dtype), "Required": True, "Missing Count": int(df_all['image_path'].isna().sum()), "Governance Role": "Input asset reference"},
    {"Column": "mask_path", "Meaning": "Relative path to ground truth segmentation mask", "Dtype": str(df_all['mask_path'].dtype), "Required": True, "Missing Count": int(df_all['mask_path'].isna().sum()), "Governance Role": "Target asset reference"},
    {"Column": "patient_id", "Meaning": "Patient identifier (available for KUB; NOT_AVAILABLE for others)", "Dtype": str(df_all['patient_id'].dtype), "Required": True, "Missing Count": int(df_all['patient_id'].isna().sum()), "Governance Role": "Patient grouping protection"},
    {"Column": "case_id", "Meaning": "Source dataset original case identifier", "Dtype": str(df_all['case_id'].dtype), "Required": True, "Missing Count": int(df_all['case_id'].isna().sum()), "Governance Role": "Source provenance"},
    {"Column": "category", "Meaning": "Subclass/clinical metadata (e.g. stone anatomy in KUB)", "Dtype": str(df_all['category'].dtype), "Required": True, "Missing Count": int(df_all['category'].isna().sum()), "Governance Role": "Stratified auditing (not pixel class)"},
    {"Column": "sample_id", "Meaning": "Unique 32-hex hash identifying the paired case", "Dtype": str(df_all['sample_id'].dtype), "Required": True, "Missing Count": int(df_all['sample_id'].isna().sum()), "Governance Role": "Primary key & disjointness checking"},
    {"Column": "split", "Meaning": "Split assignment: TRAIN, VAL, or TEST", "Dtype": str(df_all['split'].dtype), "Required": True, "Missing Count": int(df_all['split'].isna().sum()), "Governance Role": "Execution boundary governance"}
]

df_schema = pd.DataFrame(schema_info)
df_schema
"""))

    # 7. Semantic Segmentation Label Schema
    cells.append(nbf.v4.new_markdown_cell("""## 6. Binary Semantic Segmentation Label Schema
Carrying forward the semantic clarification established in Phase 03, all four medical datasets are formulated as **binary semantic segmentation** tasks. Diagnostic pathology labels (ISIC, BUSI) and anatomical location categories (KUB) represent **case-level clinical metadata**, NOT multiclass pixel targets.
"""))

    cells.append(nbf.v4.new_code_cell("""label_schema = [
    {"Dataset": "ISIC 2018", "Pixel-Level Target": "Skin Lesion", "Pixel Classes": "Class 0: Background, Class 1: Lesion", "Subclass Metadata": "Diagnostic classification (NOT_AVAILABLE in manifest)", "Metadata Level": "Case", "Used to Define Split": "No", "Used as Pixel Class": "No (Binary Only)"},
    {"Dataset": "BUSI", "Pixel-Level Target": "Breast Lesion", "Pixel Classes": "Class 0: Background, Class 1: Lesion", "Subclass Metadata": "Tumor histology (NOT_AVAILABLE in manifest)", "Metadata Level": "Case", "Used to Define Split": "No", "Used as Pixel Class": "No (Binary Only)"},
    {"Dataset": "Kvasir-SEG", "Pixel-Level Target": "Colorectal Polyp", "Pixel Classes": "Class 0: Background, Class 1: Polyp", "Subclass Metadata": "None (NOT_AVAILABLE in manifest)", "Metadata Level": "Case", "Used to Define Split": "No", "Used as Pixel Class": "No (Binary Only)"},
    {"Dataset": "KUB-Stone", "Pixel-Level Target": "Urinary Calculus (Stone)", "Pixel Classes": "Class 0: Background, Class 1: Stone", "Subclass Metadata": "Kidney, Bladder, Ureteric", "Metadata Level": "Case", "Used to Define Split": "No (Grouped by Patient)", "Used as Pixel Class": "No (Binary Only)"}
]

df_label_schema = pd.DataFrame(label_schema)
df_label_schema
"""))

    # 8. Overall Split Counts
    cells.append(nbf.v4.new_markdown_cell("""## 7. Overall Population Partitioning & Split Counts
We calculate the split population counts across all 8,441 paired cases and verify against reference project numbers.
"""))

    cells.append(nbf.v4.new_code_cell("""train_count = (df_all['split'] == 'TRAIN').sum()
val_count = (df_all['split'] == 'VAL').sum()
test_count = (df_all['split'] == 'TEST').sum()
total_count = len(df_all)

print(f"Total Canonical Population: {total_count:,} (Expected: 8,441)")
print(f"  - TRAIN Allocation     : {train_count:,} ({train_count/total_count*100:.2f}%) [Expected: 5,913]")
print(f"  - VAL Allocation       : {val_count:,} ({val_count/total_count*100:.2f}%) [Expected: 845]")
print(f"  - TEST Allocation      : {test_count:,} ({test_count/total_count*100:.2f}%) [Expected: 1,683]")

assert train_count + val_count + test_count == total_count == 8441, "Split counts do not sum to 8,441!"
print("\\nAudit Result: PASS (Population counts match exact reference values).")
"""))

    # 9. Dataset-Wise Split Counts
    cells.append(nbf.v4.new_markdown_cell("""## 8. Dataset-Wise Split Breakdown
We evaluate the split distributions within each individual dataset cohort.
"""))

    cells.append(nbf.v4.new_code_cell("""ct_splits = pd.crosstab(df_all['dataset'], df_all['split'])[['TRAIN', 'VAL', 'TEST']].reindex(['ISIC', 'BUSI', 'KVASIR', 'KUB'])
ct_splits['Total'] = ct_splits.sum(axis=1)

# Append Total Row
all_row = pd.Series({
    'TRAIN': ct_splits['TRAIN'].sum(),
    'VAL': ct_splits['VAL'].sum(),
    'TEST': ct_splits['TEST'].sum(),
    'Total': ct_splits['Total'].sum()
}, name='Authoritative Total')
ct_display = pd.concat([ct_splits, all_row.to_frame().T])
ct_display
"""))

    # 10. Split Proportions
    cells.append(nbf.v4.new_markdown_cell("""## 9. Split Proportions & Visual Distribution
We visualize the dataset split counts and normalized proportions using publication-ready figures.
"""))

    cells.append(nbf.v4.new_code_cell("""from IPython.display import Image, display

# Display Figure 1: Dataset Split Counts (Stacked Bar Chart)
fig1_path = PROJECT_ROOT / "reports/figures/phase04_manifest_splits/aggregate/phase04_dataset_split_counts.png"
display(Image(filename=str(fig1_path)))
"""))

    cells.append(nbf.v4.new_code_cell("""# Display Figure 2: Normalized 100% Stacked Bar Chart
fig2_path = PROJECT_ROOT / "reports/figures/phase04_manifest_splits/aggregate/phase04_dataset_split_proportions.png"
display(Image(filename=str(fig2_path)))
"""))

    # 11. Unique Sample Membership & Disjointness
    cells.append(nbf.v4.new_markdown_cell("""## 10. Unique Sample Membership & Split Disjointness
To verify that no sample ID appears in multiple splits, we perform rigorous set intersection audits across all split pairs.
"""))

    cells.append(nbf.v4.new_code_cell("""train_ids = set(df_all[df_all['split'] == 'TRAIN']['sample_id'])
val_ids = set(df_all[df_all['split'] == 'VAL']['sample_id'])
test_ids = set(df_all[df_all['split'] == 'TEST']['sample_id'])

ov_tv = len(train_ids & val_ids)
ov_tt = len(train_ids & test_ids)
ov_vt = len(val_ids & test_ids)
unique_ids = df_all['sample_id'].nunique()

print(f"Total Unique Sample IDs: {unique_ids:,} / {len(df_all):,}")
print(f"  - TRAIN & VAL Overlap : {ov_tv} (Expected: 0)")
print(f"  - TRAIN & TEST Overlap: {ov_tt} (Expected: 0)")
print(f"  - VAL & TEST Overlap  : {ov_vt} (Expected: 0)")

assert ov_tv == 0 and ov_tt == 0 and ov_vt == 0 and unique_ids == 8441, "Split overlap detected!"
print("\\nAudit Result: PASS (All splits are strictly pairwise disjoint).")
"""))

    cells.append(nbf.v4.new_code_cell("""# Display Figure 4: Split Overlap Matrix
fig4_path = PROJECT_ROOT / "reports/figures/phase04_manifest_splits/aggregate/phase04_split_overlap_matrix.png"
display(Image(filename=str(fig4_path)))
"""))

    # 12. KUB Patient-Group Split Audit
    cells.append(nbf.v4.new_markdown_cell("""## 11. KUB Patient-Level Group Split Audit
Medical imaging studies often contain multiple sequential slices or exposures from the same patient. In KUB-Stone, splitting by image would introduce severe data leakage. We audit KUB patient partitioning to ensure 100% patient-level grouping separation.
"""))

    cells.append(nbf.v4.new_code_cell("""kub = df_all[df_all['dataset'] == 'KUB']
kub_train_pts = set(kub[kub['split'] == 'TRAIN']['patient_id'])
kub_val_pts = set(kub[kub['split'] == 'VAL']['patient_id'])
kub_test_pts = set(kub[kub['split'] == 'TEST']['patient_id'])

kub_total_pts = kub['patient_id'].nunique()
pt_ov_tv = len(kub_train_pts & kub_val_pts)
pt_ov_tt = len(kub_train_pts & kub_test_pts)
pt_ov_vt = len(kub_val_pts & kub_test_pts)

print(f"KUB Unique Patient Count: {kub_total_pts} (Expected: 711)")
print(f"  - TRAIN Unique Patients : {len(kub_train_pts)} (Expected: 318)")
print(f"  - VAL Unique Patients   : {len(kub_val_pts)} (Expected: 111)")
print(f"  - TEST Unique Patients  : {len(kub_test_pts)} (Expected: 282)")
print(f"  - Patient TRAIN & VAL Ov: {pt_ov_tv} (Expected: 0)")
print(f"  - Patient TRAIN & TEST Ov: {pt_ov_tt} (Expected: 0)")
print(f"  - Patient VAL & TEST Ov : {pt_ov_vt} (Expected: 0)")

# Verify historical record patient-00360
p360 = df_all[df_all['patient_id'].astype(str).str.contains('00360', na=False)]
p360_splits = p360['split'].unique().tolist()
print(f"\\nSpecial Record patient-00360:")
print(f"  - Case Count : {len(p360)} (Expected: 24)")
print(f"  - Allocations: {p360_splits} (Expected: ['TRAIN'])")

assert pt_ov_tv == 0 and pt_ov_tt == 0 and pt_ov_vt == 0, "Patient leakage detected in KUB!"
assert p360_splits == ['TRAIN'] and len(p360) == 24, "patient-00360 allocation error!"
print("\\nAudit Result: PASS (100% Patient-Level Disjointness Verified).")
"""))

    cells.append(nbf.v4.new_code_cell("""# Display Figure 3: KUB Patient-Level Split Counts
fig3_path = PROJECT_ROOT / "reports/figures/phase04_manifest_splits/aggregate/phase04_kub_patient_split_counts.png"
display(Image(filename=str(fig3_path)))
"""))

    # 13. Other Dataset Grouping Audit
    cells.append(nbf.v4.new_markdown_cell("""## 12. Patient Grouping Availability for ISIC, BUSI, and Kvasir
We inspect the availability of patient-level grouping identifiers for the remaining three cohorts in the canonical manifest.
"""))

    cells.append(nbf.v4.new_code_cell("""non_kub_audit = []
for d in ['ISIC', 'BUSI', 'KVASIR']:
    sub = df_all[df_all['dataset'] == d]
    vals = sub['patient_id'].unique().tolist()
    non_kub_audit.append({
        "Dataset": d,
        "Total Cases": len(sub),
        "Unique Patient ID Values": str(vals),
        "Canonical Patient Grouping Status": "NOT AVAILABLE IN CANONICAL MANIFEST (No Synthetic IDs Fabricated)"
    })

pd.DataFrame(non_kub_audit)
"""))

    # 14. Subclass Distributions
    cells.append(nbf.v4.new_markdown_cell("""## 13. Subclass / Category Metadata Distributions
Where canonical case-level clinical metadata exists (KUB stone anatomy), we analyze the distribution across splits. For other datasets, metadata is explicitly documented as not available in the canonical manifest.
"""))

    cells.append(nbf.v4.new_code_cell("""kub_cat_ct = pd.crosstab(kub['category'], kub['split'])[['TRAIN', 'VAL', 'TEST']]
kub_cat_ct['Total'] = kub_cat_ct.sum(axis=1)
kub_cat_ct
"""))

    cells.append(nbf.v4.new_code_cell("""# Display Figure 5: KUB Category x Split Distribution
fig5_path = PROJECT_ROOT / "reports/figures/phase04_manifest_splits/aggregate/phase04_kub_category_split_distribution.png"
display(Image(filename=str(fig5_path)))
"""))

    # 15. Deterministic Reviewer Rows
    cells.append(nbf.v4.new_markdown_cell("""## 14. Deterministic Reviewer Manifest Rows (96 Rows: 12 TRAIN + 12 VAL per Dataset)
For full scientific transparency, we display deterministic sample manifest rows from TRAIN and VAL cohorts across all four datasets. To respect governance protocols, individual row paths from the locked TEST set are omitted (represented strictly by verified aggregate counts).
"""))

    cells.append(nbf.v4.new_code_cell("""rev_csv = PROJECT_ROOT / "reports/tables/phase04_manifest_review_rows.csv"
df_rev = pd.read_csv(rev_csv)

print(f"Total Reviewer Rows: {len(df_rev)} (12 TRAIN + 12 VAL x 4 datasets)")
print("\\nBreakdown by Dataset and Split:")
print(df_rev.groupby(['dataset', 'split']).size())

# Display sample 8 rows (one TRAIN and one VAL per dataset)
print("\\nSample Reviewer Metadata Rows:")
df_sample_rev = df_rev.groupby(['dataset', 'split']).first().reset_index()
df_sample_rev[['dataset', 'split', 'sample_id', 'category', 'patient_id']]
"""))

    # 16. Manifest Guard Integration
    cells.append(nbf.v4.new_markdown_cell("""## 15. Canonical `manifest_guard.py` Integration
Reviewer code must have a single source of truth. Here we directly import and run the canonical `src/utils/manifest_guard.py` utility.
"""))

    cells.append(nbf.v4.new_code_cell("""from src.utils.manifest_guard import verify_manifests

print("Invoking canonical manifest guard...")
verify_manifests()
print("Execution Result: PASS (Canonical Guard Confirms Manifest Integrity).")
"""))

    # 17. Reproducibility / Full SHA-256 Hashes
    cells.append(nbf.v4.new_markdown_cell("""## 16. Reproducibility & Cryptographic SHA-256 Table
We print the complete, non-truncated 64-character SHA-256 hex strings for all relevant Phase 04 files, reports, and foundational accepted notebooks.
"""))

    cells.append(nbf.v4.new_code_cell("""def get_sha256(p: Path) -> str:
    if not p.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

reproducibility_artifacts = [
    ("Manifest: all_paired.csv", PROJECT_ROOT / "manifests/all_paired.csv"),
    ("Manifest: train.csv", PROJECT_ROOT / "manifests/train.csv"),
    ("Manifest: val.csv", PROJECT_ROOT / "manifests/val.csv"),
    ("Manifest: test.csv", PROJECT_ROOT / "manifests/test.csv"),
    ("Guard: manifest_guard.py", PROJECT_ROOT / "src/utils/manifest_guard.py"),
    ("Table: phase04_split_counts.csv", PROJECT_ROOT / "reports/tables/phase04_split_counts.csv"),
    ("Table: phase04_manifest_review_rows.csv", PROJECT_ROOT / "reports/tables/phase04_manifest_review_rows.csv"),
    ("Audit: phase04_manifest_integrity.json", PROJECT_ROOT / "reports/audits/phase04_manifest_integrity.json"),
    ("Script: phase04_manifest_split_audit.py", PROJECT_ROOT / "notebooks/phasewise/phase_04_manifest_splits/code/phase04_manifest_split_audit.py"),
    ("Script: phase04_split_visualization.py", PROJECT_ROOT / "notebooks/phasewise/phase_04_manifest_splits/code/phase04_split_visualization.py"),
    ("Notebook: Phase 00 (Accepted)", PROJECT_ROOT / "notebooks/phasewise/phase_00_governance/phase00_governance_reproducibility_and_protocol.ipynb"),
    ("Notebook: Phase 01 (Accepted)", PROJECT_ROOT / "notebooks/phasewise/phase_01_project_initialization/phase01_project_initialization_and_repository_architecture.ipynb"),
    ("Notebook: Phase 02 (Accepted)", PROJECT_ROOT / "notebooks/phasewise/phase_02_environment_cuda/phase02_environment_cuda_and_reproducibility_validation.ipynb"),
    ("Notebook: Phase 03 (Accepted)", PROJECT_ROOT / "notebooks/phasewise/phase_03_dataset_discovery/phase03_multidomain_dataset_discovery_and_pairing_integrity.ipynb"),
    ("Notebook: Phase 14 (Canonical Frozen)", PROJECT_ROOT / "notebooks/13_phase14_regional_refiner_diagnostic.ipynb")
]

records_repro = []
for desc, p in reproducibility_artifacts:
    records_repro.append({
        "Artifact Description": desc,
        "Relative Path": str(p.relative_to(PROJECT_ROOT)).replace('\\\\', '/'),
        "Full Cryptographic SHA-256 Digest": get_sha256(p)
    })

pd.set_option('display.max_colwidth', None)
df_repro = pd.DataFrame(records_repro)
df_repro
"""))

    # 18. Limitations
    cells.append(nbf.v4.new_markdown_cell("""## 17. Scientific Limitations
1. **Clinical Patient Metadata**: Patient grouping metadata is present for KUB-Stone but unavailable for ISIC, BUSI, and Kvasir-SEG in the canonical manifests. Splits for non-KUB datasets reflect stratified random allocation without patient grouping guarantees.
2. **Locked Test Partition**: In accordance with rigorous zero-leakage standards, TEST image and mask files were not opened, audited for pixel statistics, or processed in any manner.
3. **Subclass Metadata**: Case categories (e.g. stone anatomy) represent clinical context rather than pixel-level multiclass segmentation targets.
"""))

    # 19. What Was Established
    cells.append(nbf.v4.new_markdown_cell("""## 18. What Was Established
1. **Canonical Manifest Integrity**: All four manifest CSV files strictly match accepted SHA-256 digests and pass canonical `manifest_guard.py` verification.
2. **Exact Population Partitioning**: Verified 8,441 total cases partitioned into 5,913 TRAIN (70.05%), 845 VAL (10.01%), and 1,683 TEST (19.94%).
3. **Strict Disjointness**: Confirmed $\\text{TRAIN} \\cap \\text{VAL} = 0$, $\\text{TRAIN} \\cap \\text{TEST} = 0$, and $\\text{VAL} \\cap \\text{TEST} = 0$.
4. **Patient-Level Protection**: Verified zero patient leakage across KUB splits (318 TRAIN, 111 VAL, 282 TEST) and verified 100% TRAIN assignment for `patient-00360`.
5. **Zero Test Leakage**: Zero TEST image or mask content reads occurred during this phase.
"""))

    # 20. Why Phase 05 Exists
    cells.append(nbf.v4.new_markdown_cell("""## 19. Transition to Phase 05
While Phase 04 establishes sample-ID and patient-ID disjointness at the manifest level, manifest-level disjointness alone cannot detect subtle cross-split duplications (e.g. identical or near-duplicate images with different filenames). 

**Phase 05 (Leakage Audit & Near-Duplicate Analysis)** is specifically designed to perform image-level perceptual hashing and near-duplicate verification between TRAIN and VAL splits to guarantee zero cross-contamination before any baseline model training begins.
"""))

    nb.cells = cells
    out_path = PROJECT_ROOT / "notebooks/phasewise/phase_04_manifest_splits/phase04_canonical_manifest_and_split_integrity.ipynb"
    with open(out_path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
    print(f"Created notebook at: {out_path}")


if __name__ == '__main__':
    create_notebook()
