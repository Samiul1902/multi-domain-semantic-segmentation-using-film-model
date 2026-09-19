import nbformat as nbf
from pathlib import Path

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "jup-venv",
        "language": "python",
        "name": "jup-venv"
    },
    "language_info": {
        "name": "python",
        "version": "3.11.9"
    }
}

cells = []

# Section 1: Title
cells.append(nbf.v4.new_markdown_cell("""# Phase 03 — Multi-Domain Dataset Discovery and Pairing Integrity

**Scientific Purpose:**
Catalog raw medical imaging cohorts, audit image/mask pairing integrity, verify spatial geometry alignment, and visually introduce the four target clinical modalities across 48 deterministic training cases ($12$ cases per dataset) under strict test isolation governance.

**Phase ID:** `phase_03_dataset_discovery`  
**Phase Status:** `COMPLETE`  
**Relation to Phase 02:** Operates on the certified PyTorch/CUDA hardware stack verified in Phase 02.  
**Current Overall Research Phase:** Phase 15 (`CURRENT_PROTOCOL_DESIGN` / `AWAITING_SUPERVISOR_AUTHORIZATION`)
"""))

# Section 2: Scientific Question
cells.append(nbf.v4.new_markdown_cell("""## Section 2: Core Scientific Question

*What medical image datasets are genuinely available to the research project, how are images and segmentation masks paired, what are their modalities and spatial geometries, and does the paired population reconcile with canonical project records?*
"""))

# Section 3: Why These Four Datasets
cells.append(nbf.v4.new_markdown_cell("""## Section 3: Rationale for the Multi-Domain Portfolio

The project ultimately investigates regional scale-aware segmentation across four diverse clinical tasks:
1. **ISIC 2018 (Dermoscopy):** Unimodal color photography with variable lesion pigmentation, hair artifacts, and ambiguous lesion boundaries.
2. **BUSI (Breast Ultrasound):** Acoustic shadowing, speckle noise, and low contrast between tumor margins and fibroglandular tissue.
3. **Kvasir-SEG (GI Endoscopy):** High specular reflection, complex mucosal folds, and variable polyp morphologies.
4. **KUB-Stone (Plain Radiography):** High-difficulty radiological task where urinary calculi frequently present as very small, sparse foreground targets superimposed over complex pelvic bone structures and bowel gas.
"""))

# Section 4: Governance & Test Lock
cells.append(nbf.v4.new_markdown_cell("""## Section 4: Governance & Strict Test Isolation Enforcement

In accordance with Phase 00 governance protocols:
- **Zero Test Access:** No images from the frozen test split ($1,683$ cases) are opened, analyzed, or displayed (`TEST reads = 0`, `TEST visualizations = 0`, `TEST metrics = NONE`).
- **TRAIN-Only Qualitative Cohort:** All 48 visual cases presented in this notebook are selected exclusively from the authorized training split (`split == TRAIN`).
- **Cryptographic Independence:** No external test sets (`HAM10000`, `CVC-ClinicDB`) are accessed during discovery (`EXTERNAL reads = 0`).
"""))

# Section 5: Raw/Canonical Dataset Locations
cells.append(nbf.v4.new_markdown_cell("""## Section 5: Discovered Dataset Locations & File Hierarchy

Inspection of internal data roots confirms the presence of all four imaging collections:
"""))

# Section 5 Code: Path inspection
cells.append(nbf.v4.new_code_cell("""from pathlib import Path
import json
import pandas as pd
from IPython.display import display, HTML, Image

def find_root():
    p = Path.cwd()
    for _ in range(6):
        if (p / 'reports').exists() and (p / 'manifests').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')

ROOT = find_root()

inv_path = ROOT / 'reports/audits/dataset_inventory.json'
with open(inv_path, 'r', encoding='utf-8') as f:
    inv = json.load(f)

loc_data = []
for ds_name, info in inv.get('datasets', {}).items():
    loc_data.append({
        "Dataset Identifier": ds_name,
        "Discovery Status": info.get("status"),
        "Raw Source Root": info.get("root")
    })

df_loc = pd.DataFrame(loc_data)
display(HTML("<h4>Discovered Raw Dataset Storage Hierarchy</h4>"))
display(df_loc)
"""))

# Section 6: Pairing Discovery & Reconciled Population
cells.append(nbf.v4.new_markdown_cell("""## Section 6: Pairing Discovery & Population Reconciliation

The authoritative paired inventory reconciles to **8,441** paired cases across the four domains:
- **Historical Note on 8,159:** A historical count of 8,159 cases is recorded in early project provenance as unresolved exploratory evidence. In accordance with Phase 03 directives, this count was **not artificially forced**, and the certified manifest population of 8,441 is preserved.
"""))

# Section 7: Canonical Paired Counts Table & Figure
cells.append(nbf.v4.new_markdown_cell("""## Section 7: Canonical Paired Dataset Counts
"""))

# Section 7 Code: Paired counts table & chart
cells.append(nbf.v4.new_code_cell("""sum_csv = ROOT / 'reports/tables/phase03_dataset_discovery_summary.csv'
df_sum = pd.read_csv(sum_csv)

display(HTML("<h4>Authoritative Multi-Domain Dataset Summary Table</h4>"))
display(df_sum[['dataset', 'domain', 'pixel_target', 'paired_count', 'train_count', 'val_count', 'test_count', 'channel_summary']])

chart_path = ROOT / 'reports/figures/phase03_dataset_discovery/aggregate/phase03_paired_dataset_counts.png'
if chart_path.exists():
    display(Image(filename=str(chart_path), width=850))
"""))

# Section 8: Label Taxonomy & Metadata Separation
cells.append(nbf.v4.new_markdown_cell("""## Section 8: Segmentation Class Semantics & Metadata Taxonomy

### Critical Distinction: Pixel-Level Segmentation vs. Case-Level Metadata
A vital scientific principle of the RA-MedFiLM-Seg++ framework is distinguishing between:
1. **Pixel-Level Segmentation Target:** The physical binary foreground delineated by the segmentation mask (`foreground` vs. `background`).
2. **Dataset / Clinical Domain:** The imaging modality and anatomical setting (e.g., KUB radiograph vs. Dermoscopy).
3. **Image-Level / Case-Level Subclass Metadata:** Clinical diagnostic or anatomical categories (e.g., `Melanoma`, `Benign`, `Kidney_Stone`).

> [!IMPORTANT]
> **Subclass metadata are NOT pixel classes.** None of the four datasets use multiclass segmentation masks. All masks are strictly binary foreground targets. Diagnostic or anatomical labels reside exclusively in image-level tabular metadata. Subgroup evaluations (e.g., performance on Kidney vs. Bladder stones) evaluate binary segmentation across patient cohorts, not multiclass pixel segmentation.

| Dataset | Clinical Domain | Pixel-Level Segmentation Target | Mask Type | Available Subclass / Metadata | Metadata Level | Used as Pixel Class? | Future Subgroup Analysis? |
| :--- | :--- | :--- | :---: | :--- | :---: | :---: | :---: |
| **ISIC 2018** | Dermoscopy | Skin lesion vs. background | Binary | Melanoma / Nevus / Keratosis | Image-level diagnostic | **NO** | YES |
| **BUSI** | Breast Ultrasound | Breast lesion vs. background | Binary | Benign / Malignant / Normal | Image-level category | **NO** | YES |
| **Kvasir-SEG** | GI Endoscopy | Polyp vs. background | Binary | *NOT ESTABLISHED* | N/A | **NO** | TO_AUDIT |
| **KUB-Stone** | Plain Radiography | Stone vs. background | Binary | Kidney / Bladder / Ureteric | Case-level anatomical | **NO** | YES |
"""))

# Section 9: TRAIN-Only Visualization Selection
cells.append(nbf.v4.new_markdown_cell("""## Section 9: Deterministic TRAIN-Only Sample Selection

To guarantee impartial, reviewer-verifiable visualization, cases were chosen deterministically via:
$$\\text{Rank} = \\text{Sort}\\left(\\text{SHA256}\\left(\\text{\"phase03_dataset_sample_seed42|\"} + \\text{dataset} + \\text{\"|\"} + \\text{sample\\_id}\\right)\\right)$$
The first 12 cases per dataset (48 total) were selected from `split == TRAIN`.
"""))

# Section 9 Code: Display selection head
cells.append(nbf.v4.new_code_cell("""sel_csv = ROOT / 'reports/tables/phase03_train_sample_selection.csv'
df_sel = pd.read_csv(sel_csv)

print(f"Loaded {len(df_sel)} selected training cases:")
print(df_sel['dataset'].value_counts())
display(df_sel[['dataset', 'sample_rank', 'sample_id', 'image_width', 'image_height', 'channels', 'foreground_fraction', 'category']].head(10))
"""))

# Section 10: ISIC — 12 Real Samples
cells.append(nbf.v4.new_markdown_cell("""## Section 10: ISIC 2018 — 12 Deterministic Training Cases

Visualizing 12 dermoscopy cases across 3 panels (4 cases/panel). Each row displays the original dermoscopic photograph, the ground-truth binary mask, and the high-contrast green contour overlay.
"""))

# Section 10 Code: ISIC figures
cells.append(nbf.v4.new_code_cell("""for p in range(1, 4):
    f_p = ROOT / f'reports/figures/phase03_dataset_discovery/sample_data/isic_samples_page{p:02d}.png'
    if f_p.exists():
        display(Image(filename=str(f_p), width=950))
"""))

# Section 10 Markdown: ISIC Interpretation
cells.append(nbf.v4.new_markdown_cell("""### ISIC 2018 Qualitative Observations
- **Visual Heterogeneity:** Substantial variance in lesion size, pigmentation gradients, illumination vignetting, and skin furrows.
- **Boundary Semantics:** High-contrast contour overlays clearly delineate the transition from pathological pigment to surrounding healthy epidermis.
"""))

# Section 11: BUSI — 12 Real Samples
cells.append(nbf.v4.new_markdown_cell("""## Section 11: BUSI — 12 Deterministic Training Cases

Visualizing 12 breast ultrasound cases across 3 panels (4 cases/panel).
"""))

# Section 11 Code: BUSI figures
cells.append(nbf.v4.new_code_cell("""for p in range(1, 4):
    f_p = ROOT / f'reports/figures/phase03_dataset_discovery/sample_data/busi_samples_page{p:02d}.png'
    if f_p.exists():
        display(Image(filename=str(f_p), width=950))
"""))

# Section 11 Markdown: BUSI Interpretation
cells.append(nbf.v4.new_markdown_cell("""### BUSI Qualitative Observations
- **Acoustic Characteristics:** Pronounced speckle texture, posterior acoustic shadowing, and low-contrast boundaries between hypoechoic lesions and glandular parenchyma.
- **Grayscale Integrity:** Images are rendered in authentic grayscale, avoiding artificial colorization.
"""))

# Section 12: Kvasir-SEG — 12 Real Samples
cells.append(nbf.v4.new_markdown_cell("""## Section 12: Kvasir-SEG — 12 Deterministic Training Cases

Visualizing 12 endoscopic polyp cases across 3 panels (4 cases/panel).
"""))

# Section 12 Code: Kvasir figures
cells.append(nbf.v4.new_code_cell("""for p in range(1, 4):
    f_p = ROOT / f'reports/figures/phase03_dataset_discovery/sample_data/kvasir_samples_page{p:02d}.png'
    if f_p.exists():
        display(Image(filename=str(f_p), width=950))
"""))

# Section 12 Markdown: Kvasir Interpretation
cells.append(nbf.v4.new_markdown_cell("""### Kvasir-SEG Qualitative Observations
- **Endoscopic Artifacts:** Strong specular highlights from mucosal fluid, instrument edges, and varying camera viewing angles.
- **Polyp Morphology:** Lesions range from flat sessile plaques to pedunculated protruding polyps.
"""))

# Section 13: KUB-Stone — 12 Real Samples
cells.append(nbf.v4.new_markdown_cell("""## Section 13: KUB-Stone — 12 Deterministic Training Cases

Visualizing 12 plain radiograph calculus cases across 3 panels (4 cases/panel).
"""))

# Section 13 Code: KUB figures
cells.append(nbf.v4.new_code_cell("""for p in range(1, 4):
    f_p = ROOT / f'reports/figures/phase03_dataset_discovery/sample_data/kub_samples_page{p:02d}.png'
    if f_p.exists():
        display(Image(filename=str(f_p), width=950))
"""))

# Section 13 Markdown: KUB Interpretation
cells.append(nbf.v4.new_markdown_cell("""### KUB-Stone Qualitative Observations
- **Target Scale Sparsity:** Calculi present as very small, sparse foreground targets, motivating later formal object-size taxonomy (Phase 07).
- **Anatomical Background Clutter:** Radio-opaque stones are superimposed upon complex bony pelvic architecture, spine, and intestinal gas shadows.
- **Category Labels:** Annotations such as `Kidney_Stone` or `Bladder_Stone` represent patient case metadata / anatomical origin, not separate pixel classes.
"""))

# Section 14: Image Geometry & Channel Overview
cells.append(nbf.v4.new_markdown_cell("""## Section 14: Spatial Geometry & Resolution Distribution

Descriptive summary of spatial dimensions observed across the 48 training sample cases:
"""))

# Section 14 Code: Geometry summary
cells.append(nbf.v4.new_code_cell("""geom_summary = df_sel.groupby('dataset').agg(
    min_width=('image_width', 'min'),
    max_width=('image_width', 'max'),
    min_height=('image_height', 'min'),
    max_height=('image_height', 'max'),
    channels=('channels', 'first'),
    mean_fg_frac=('foreground_fraction', 'mean')
).reset_index()

display(HTML("<h4>Selected Training Cohort Spatial Geometry Summary</h4>"))
display(geom_summary)
"""))

# Section 15: Pairing Integrity Summary
cells.append(nbf.v4.new_markdown_cell("""## Section 15: Pairing Integrity & Spatial Alignment Audit

Across all 48 selected cases:
- **File Existence:** 48/48 images exist, 48/48 masks exist.
- **Dimension Matching:** 100% of image-mask pairs share identical pixel dimensions (`image.size == mask.size`).
- **Binary Semantics:** Masks evaluate to binary foreground/background sets after thresholding.
"""))

# Section 16: Limitations
cells.append(nbf.v4.new_markdown_cell("""## Section 16: Scientific Limitations of Discovery Phase

- **Introductory Scope:** Phase 03 is restricted to data discovery, pairing verification, and qualitative inspection.
- **No Split Modeling:** Patient-level vs. sample-level partitioning and leakage prevention are formalized in Phase 04 and Phase 05.
- **No Stone Burden Taxonomy:** Detailed object size categorization is formalized in Phase 07.
"""))

# Section 17: What Was Learned
cells.append(nbf.v4.new_markdown_cell("""## Section 17: What Was Established in Phase 03

1. **Reconciled Inventory:** Verified $8,441$ paired cases across four clinical domains (ISIC: 3,694, BUSI: 927, Kvasir: 1,000, KUB: 2,820).
2. **Deterministic Qualitative Verification:** Displayed 48 real cases ($12$ per dataset) across $12$ structured figure pages with zero test leakage.
3. **Class vs. Metadata Clarity:** Established that all segmentation targets are binary foreground/background masks, with clinical categories treated strictly as case-level metadata.
4. **Verified Pairing:** Confirmed 100% geometric spatial alignment between raw images and ground-truth segmentation masks.
5. **Standalone Audit Automation:** Deployed `phase03_dataset_discovery_audit.py` and `phase03_sample_visualization.py`.
"""))

# Section 18: Why Phase 04 is Needed
cells.append(nbf.v4.new_markdown_cell("""## Section 18: Why Phase 04 is Required Next

- **Phase 04 (Canonical Manifest & Patient Splits):** Establishes the authoritative patient-leakage-free data partition (`train.csv`, `val.csv`, `test.csv`), ensuring zero cross-split subject overlap in KUB radiographs.
"""))

# Section 19: Artifact Hashes
cells.append(nbf.v4.new_markdown_cell("""## Section 19: Provenance Artifacts & Cryptographic Signatures
"""))

# Section 19 Code: Hash table with FULL SHA-256 strings
cells.append(nbf.v4.new_code_cell("""import hashlib

def get_hash(rel_path):
    p = ROOT / rel_path
    if not p.exists():
        return "FILE_NOT_FOUND"
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

art_hashes = [
    {"Artifact File": "reports/tables/phase03_dataset_discovery_summary.csv", "Full SHA-256 Hash": get_hash("reports/tables/phase03_dataset_discovery_summary.csv")},
    {"Artifact File": "reports/tables/phase03_train_sample_selection.csv", "Full SHA-256 Hash": get_hash("reports/tables/phase03_train_sample_selection.csv")},
    {"Artifact File": "reports/audits/phase03_figure_manifest.json", "Full SHA-256 Hash": get_hash("reports/audits/phase03_figure_manifest.json")},
    {"Artifact File": "reports/figures/phase03_dataset_discovery/aggregate/phase03_paired_dataset_counts.png", "Full SHA-256 Hash": get_hash("reports/figures/phase03_dataset_discovery/aggregate/phase03_paired_dataset_counts.png")}
]

for item in art_hashes:
    print(f"{item['Artifact File']:65s} : {item['Full SHA-256 Hash']}")

df_art = pd.DataFrame(art_hashes)
display(HTML("<h4>Phase 03 Authoritative Artifact Cryptographic Hashes</h4>"))
display(df_art)
"""))

nb.cells = cells

target_nb = Path("notebooks/phasewise/phase_03_dataset_discovery/phase03_multidomain_dataset_discovery_and_pairing_integrity.ipynb")
target_nb.parent.mkdir(parents=True, exist_ok=True)
nbf.write(nb, str(target_nb))
print(f"Created Phase 03 reviewer notebook at: {target_nb}")
