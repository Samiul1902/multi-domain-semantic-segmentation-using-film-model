# ReMedFiLM — Complete Dataset Guide, Split Governance and Redistribution Register

**Package:** ReMedFiLM supervisor submission
**Scope:** 4 primary internal development benchmarks + 3 evaluated external EXTERNAL884 cohorts + 1 audited-but-unevaluated HAM10000 skin cohort
**Authority:** `manifests/phase4_v3/` (canonical, leakage-safe, `CANONICAL_ACTIVE_DEVELOPMENT`); `docs/publication_readiness/FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md` (verified licences); `reports/audits/phase19_preprocessing_contract.json` (preprocessing); `reports/external_extension/ext01_external_dataset_inventory.json` and `ext02_*.json` (external cohorts)
**This document supersedes:** `full_doc_report/V9/ReMedFiLM_V9_Dataset_Guide.md`, whose per-dataset split counts (e.g. ISIC TRAIN 1,816 / VAL 259 / TEST 519) do **not** match the canonical frozen manifests and must not be cited.

> **No TEST1683 pixels were opened to produce this guide.** TEST figures below come from split-assignment metadata only. Only `train.csv` and `val.csv` are shipped in this package; `test.csv` and `quarantined.csv` are deliberately **not** included.

---

## 1. Dataset resource table

| # | Dataset | Role | Official URL / DOI | Modality | Segmentation target | Original release size | Project rows (all_paired) | TRAIN / VAL / TEST / QUARANTINED | Licence (verified authority) | Redistribution in this ZIP |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | ISIC 2018 Task 1 | Internal primary | https://challenge.isic-archive.com/data/ · challenge arXiv:1902.03368 · data paper doi:10.1038/sdata.2018.161 | Dermoscopy, RGB | Cutaneous lesion boundary | 2,594 train / 100 val / 1,000 test (official Task 1 partitions) | 3,694 | 2,556 / 357 / 735 / 46 | **CC0 1.0** (Task 1 only; Task 3 is CC BY-NC — do not conflate) | Metadata manifests only; no images/masks |
| 2 | BUSI-WHU V3 | Internal primary | https://data.mendeley.com/datasets/k6cpmwybk3/3 · doi:10.17632/k6cpmwybk3.3 | B-mode breast ultrasound, greyscale | Breast lesion / tumour contour | 927 images + 927 masks | 927 | 602 / 84 / 174 / 67 | **CC BY 4.0**; ethics WDRY2022-K217 | Metadata manifests only; patient workbook excluded |
| 3 | Kvasir-SEG | Internal primary | https://datasets.simula.no/kvasir-seg/ · doi:10.1007/978-3-030-37734-2_37 | Colonoscopy endoscopy, RGB | Colorectal polyp | 1,000 images + 1,000 masks | 1,000 | 696 / 87 / 216 / 1 | **Custom Simula research/education terms**; commercial use forbidden without written permission. NOT Creative Commons | Metadata manifests only |
| 4 | KUB-StoneX (Figshare v1) | Internal primary | https://doi.org/10.6084/m9.figshare.32049369.v1 | KUB abdominal radiograph, mixed L/RGB | Urinary calculus / stone instance (ROI) | 2,570 images / 1,703 patients (432 bladder + 573 kidney + 177 ureteric + 1,388 normal) | 2,820 | 1,978 / 280 / 558 / 4 | **CC BY 4.0**; IRB REC-FSIT-2025/No: 12732 | Metadata manifests only; ROI derivative disclosed |
| 5 | CVC-ClinicDB | External EXTERNAL884 | https://polyp.grand-challenge.org/CVCClinicDB/ · Bernal et al., *Comput Med Imaging Graph* 43:99–111 (2015) | Colonoscopy endoscopy, RGB | Polyp boundary | 612 frames + 612 masks | n/a — external only | 612 evaluated, 0 excluded | `CHECK_REQUIRED` in ext01 inventory; **no licence file present locally — redistribution NOT cleared** | Result tables/audits only |
| 6 | BrEaST-Lesions-USG | External EXTERNAL884 | https://www.cancerimagingarchive.net/collection/breast-lesions-usg/ · Pawłowska et al. (TCIA, 2024) | Breast ultrasound | Breast lesion (tumour mask) | 256 images; 252 tumour masks | n/a — external only | 252 evaluated; 4 excluded pre-inference (`GT_UNAVAILABLE__no_tumour_mask`) | `CHECK_REQUIRED` in ext01 inventory; **redistribution NOT cleared** | Result tables/audits only |
| 7 | Stones_where_are_you (Roboflow COCO-seg v3) | External EXTERNAL884 | https://universe.roboflow.com/xray-abdomen-to-identify-stones/stones_where_are_you | Abdominal X-ray | Urinary stone (COCO polygon → binary) | 460 images / 456 masks / 10 categories; 384 train + 56 valid + **20 test** | n/a — external only | 20 evaluated (test split only); 6 stone-positive + 14 stone-free | `CC0_PUBLIC_DOMAIN` as recorded in ext01 inventory (not independently re-verified in this packaging task) | Result tables/audits only |
| 8 | HAM10000 (ISIC-2018 Task 3 training input) | **Audited, NOT evaluated** | **https://doi.org/10.7910/DVN/DBW86T** · Tschandl et al., *Sci Data* 5:180161 (2018) · arXiv:1803.10417 | Dermoscopy, RGB | **No expert segmentation masks in the official release**; 7-class diagnostic labels | 10,015 images (classification) | n/a — candidate external | **0 evaluated**; excluded from EXTERNAL884 | **CC BY-NC 4.0** (local `images/LICENSE.txt` + `images/ATTRIBUTION.txt`); non-commercial, attribution to ViDIR Group, Medical University of Vienna | **No images or masks.** Metadata-level manifest, counts and audit only |

The machine-readable equivalent is `DATASET_RESOURCE_TABLE.csv` in this directory.

---

## 2. Canonical split governance (`manifests/phase4_v3/`)

| Split | Rows | Status | Included in ZIP |
|---|---:|---|---|
| TRAIN | 5,832 | Active training | `manifests/train.csv` |
| VAL (VAL808) | 808 | Active validation; all headline internal metrics | `manifests/val.csv` |
| TEST (TEST1683) | 1,683 | **Protected, immutable, not opened** | **NO** |
| QUARANTINED | 118 | Leakage remediation (62 test-linked patient overlap, 34 pHash risk, 13 same acquisition, 5 BUSI patient overlap, 3 conservative grouping, 1 exact duplicate) | **NO** |
| ALL_PAIRED | 8,441 | All of the above with split assignment | **NO** (counts derived metadata-only) |

- `ROUTER_DEVELOPMENT` 4,957 + locked `ROUTER_HOLDOUT` 875 = 5,832 (TRAIN), recorded in `manifests/router_dev_holdout_split.csv`.
- VAL808 domain composition: ISIC 357, BUSI 84, KVASIR 87, KUB 280.
- `ROI_PROPOSAL_THRESHOLD = 0.30` (bbox/action) is **not** the segmentation output threshold `0.50` (final mask/Dice); `S_OMEGA_ACCEPT_THRESHOLD = 0.50`. These must never be conflated.
- Manifests carry **pseudonymous** `patient_id` / `case_id` grouping keys and absolute *local* paths. They contain no names, contact data or clinical records. The BUSI-WHU `Patient_infos_BUSI-WHU.xlsx` workbook is explicitly excluded from the ZIP and was never opened.

### 2.1 ISIC 2018: project splits ≠ official partitions

The project re-partitioned the ISIC archive after the Phase-05 leakage audit. VAL808's 357 ISIC images consist of **231 official-train + 14 official-validation + 112 official-test** images. Project TRAIN/VAL/TEST are strictly disjoint by path and image ID (0 shared), but the phrase "ISIC validation set" in this work means the **project's** VAL808, **not** the official ISIC validation partition. Any comparison with literature using official splits must disclose this.

### 2.2 KUB-StoneX: full-field radiographs vs ROI instance patches

The KUB rows are a **mixed unit of analysis**, not whole-radiograph segmentation:

| Population | Full-field radiographs | ROI instance patches | Total |
|---|---:|---:|---:|
| Active splits (TRAIN+VAL+TEST) | **1,146** | **1,670** | **2,816** |
| TRAIN+VAL only | 873 | 1,385 | 2,258 |
| VAL808 only | 103 | 177 | 280 |

- The 1,385 TRAIN+VAL ROI patches derive from 893 unique source radiographs.
- `all_paired.csv` additionally contains 4 quarantined full-field KUB rows → 2,820 total KUB rows.
- The local mirror of Figshare v1 has **32 missing masks** (1 kidney, 31 ureteric); those images are never used as full-image rows, though 16 contribute ROI patches whose masks do exist.
- **No full-field KUB case was ever ACCEPTED by the router.** Combined-gallery KUB rows are therefore ROI patches and are labelled as such.
- The KUB task must be described as **ROI-instance segmentation on a derived subset**.

---

## 3. Preprocessing (frozen contracts)

**Internal — `phase19_preprocessing_contract_v1` (`05_Datasets/phase19_preprocessing_contract.json`)**

- Image: uint8 → float32, `/255.0` → `[0,1]`; default `RGB_3CH` (native-L domains replicated to 3 identical channels, lossless).
- Mask: `mask > 0` foreground (never test `mask == 1`); 3-D masks reduced to first channel; NEAREST interpolation.
- Spatial: aspect-preserving resize with `scale = min(512/w, 512/h)`, symmetric centre pad to **512×512**, fill 0; image BILINEAR, mask NEAREST.
- Augmentation: TRAIN only, paired — horizontal mirror p=0.5, rotation ±5°, brightness ±0.10, contrast ±0.10; disabled for VAL.
- Scope is **TRAIN and VAL only**; `test_image_reads = 0`, `test_mask_reads = 0`, `test_inference = 0`.

**External — `ext02_preprocessing_freeze.json` (EXT02, no tuning)**

- RGB 3-channel; same 512 aspect-preserving resize + symmetric pad; image BILINEAR, mask NEAREST.
- BrEaST: RGBA → drop alpha → RGB (deterministic).
- Stones: COCO polygon rasterised to binary at native resolution, then NEAREST resize; binary rule `stone → foreground` on the frozen test split.
- HAM10000 / CVC: already RGB; external padding excluded from ROI area; `mask > 0` binarisation.

---

## 4. Per-dataset cards

### 4.1 ISIC 2018 Task 1 (task_id 0)
Dermoscopic RGB images with expert pixel-level lesion-boundary masks. Native widths 576–6,828 px, heights 480–4,519 px; median 3,008×2,000; median foreground fraction 0.143. **Licence CC0 1.0**, established from the official 2018 challenge table plus the locally stored full CC0 legal code — **not** CC BY-NC (that applies to Task 3). Citation: Codella et al., arXiv:1902.03368; Tschandl et al., doi:10.1038/sdata.2018.161. Project rows 3,694.

### 4.2 BUSI-WHU V3 (task_id 1)
Wuhan University / Renmin Hospital release — **not** the separate Cairo `BUSI` collection. 927 greyscale `.bmp` images with 927 `_anno.bmp` contour masks (927/927 paired, 0 unpaired); native 243–957 × 233–693 px, median 433×398.5; median foreground 0.0473. Normal/clean scans are excluded from segmentation training. CC BY 4.0, Mendeley Data V3 (2025-07-23), ethics WDRY2022-K217. Citation: Al-Dhabyani et al., *Data in Brief* 28:104863 (2020), doi:10.17632/k6cpmwybk3.3. **The patient workbook `Patient_infos_BUSI-WHU.xlsx` is never opened, joined to outputs, or redistributed.**

### 4.3 Kvasir-SEG (task_id 2)
1,000 expert-verified polyp images/masks, RGB; native 332–1,920 × 352–1,072 px, median 621×530. The archive also ships `kavsir_bboxes.json`. Simula's terms restrict use to **research and education** and forbid commercial use without written permission; citation of Jha et al. (MMM 2020, pp. 451–462) is mandatory. This is a custom permission, **not** a Creative Commons licence.

### 4.4 KUB-StoneX (task_id 3)
Figshare v1 (2026-04-30), CC BY 4.0, 2,570 images / 1,703 patients, IRB REC-FSIT-2025/No: 12732. Local per-class counts match the release exactly; the mirror is partial (32 missing masks plus absent `ROI_Metadata/`, `Radiomic_Features/`, `annotations.json`). Native sizes span 41–3,096 × 45–3,528 px because full radiographs and small ROI crops coexist. Mixed L/RGB acquisition. Must be reported with the full-field/ROI decomposition in §2.2.

### 4.5 CVC-ClinicDB (external, domain analogue KVASIR)
612 colonoscopy frames with 612 binary polyp masks (`PNG/{Original,Ground Truth}` plus TIF copies); `metadata.csv` maps frame → sequence. Used as an external out-of-distribution endoscopic stress test. **Licence not verified** (`CHECK_REQUIRED`, no local licence file), so no CVC image or mask is redistributed. Patient/sequence-level independence is captured by cluster-bootstrap (`n_clusters = 29`), not by assuming independent frames.

### 4.6 BrEaST-Lesions-USG (external, domain analogue BUSI)
256 images; 252 `case*_tumor.png` lesion masks; 14 `case*_otherN.png` other-structure masks (reporting only, excluded from GT). Four cases (`case045`, `case061`, `case209`, `case213`) were excluded **pre-inference** for absent tumour masks, giving 252 evaluated cases and `n_post_hoc_drops = 0`. **Patient-level independence is NOT verifiable** from the supplied metadata, and the licence is `CHECK_REQUIRED`; both are recorded limitations.

### 4.7 Stones_where_are_you (external, domain analogue KUB)
Roboflow COCO-segmentation v3: 460 images, 456 masks, 10 annotated categories; only the **20-image test split** was used, filtered by the frozen manifest. 6 stone-positive, 14 stone-free negative controls. Roboflow-augmented `.rf.` filenames imply duplicate-source risk. **All 14 stone-free scans receive a false-positive stone mask in BOTH the `global` and `barr` arms** (`empty_prediction_rate = 0.0`, specificity 0.0). For these empty-GT cases Dice / IoU / Precision are **mathematically defined and equal 0** (`n_defined = 20`) because the prediction is non-empty; **Recall and HD95/ASSD are undefined** and are reported only for the `n = 6` stone-positive subset. The `20`-case cohort means (FULL Dice 0.082126, HD95 169.90 px) therefore mix two different denominators and must not be read as a homogeneous segmentation score. Stone-positive `n = 6`: Dice 0.273755 (FULL) / 0.269468 (G), HD95 169.90 px / 166.90 px.

### 4.8 HAM10000 — audited, classification-oriented, NOT an evaluated segmentation benchmark

See `HAM10000_AUDIT_REPORT.md` and `08_Verification/HAM10000_AUDIT.json` for the full read-only audit. Summary:

| Item | Verified value |
|---|---|
| Local `.jpg` images | **10,015** |
| Local `.png` masks | **10,015** |
| `metadata.csv` rows / columns | **10,015** / `image,MEL,NV,BCC,AKIEC,BKL,DF,VASC` (7-class one-hot) |
| Sidecar files | `images/ATTRIBUTION.txt`, `images/LICENSE.txt` |
| Three-way stem match (image ↔ mask ↔ metadata) | **10,015 / 10,015 = 100 %**, 0 unmatched |
| Patient / lesion IDs in metadata | **None** — lesion-level independence cannot be verified |
| Duplicate image hash groups | **2**: `ISIC_0024366`/`ISIC_0029861`; `ISIC_0024777`/`ISIC_0029938` (10,013 unique hashes) |
| Duplicate mask hash groups | **1**: `ISIC_0026042`/`ISIC_0029819` |
| Exact ID overlap with frozen ISIC splits | **0** across 2,556 TRAIN, 357 VAL, and all 3,694 ISIC IDs in `all_paired.csv` (which includes TEST IDs). HAM ID range `ISIC_0024306 … ISIC_0034320`; project `ISIC_0000000 … ISIC_0036347`. |
| Byte-identical SHA-256 overlap vs ISIC TRAIN+VAL | **0** exact matches out of 28 byte-size candidates among 2,913 TRAIN+VAL ISIC rows; TEST bytes never opened |
| Mask provenance | **UNDOCUMENTED.** Official Task 3 ships no segmentation masks. Deterministic 512-mask sample: 98.63 % single connected component, median centroid offset 0.053 from image centre, 15.82 % touch an image edge, 100 % have value signature `[0,255]`, fg fraction median 0.227 (min 0.009, max 0.919) — consistent with coarse algorithmic proxy blobs, not expert lesion boundaries. |
| Controlling verdict | `HAM10000_EXCLUDED__MASK_PROVENANCE_UNVERIFIED` (`c1_cohort_construction.json`: 10,015 manifest rows, **0 rows analysed**) |
| Saved ReMedFiLM FULL predictions | **None.** The single historical `F5 HAM10000 ISIC_0024306` number (Dice 79.15, IoU 65.50) is **GlobalMedFiLM only**, single-case, checkpoint `286689fd…5ba1b7` (3,523,001 params) — see `c1_claim_provenance.json` EXT-06/EXT-07 notes. |
| Part of EXTERNAL884? | **No.** EXTERNAL884 = 612 + 252 + 20 = 884; HAM10000 must remain separate. |
| Scientific status | `EXTERNAL_SKIN_DATASET_AVAILABLE__SEGMENTATION_EVALUATION_NOT_ESTABLISHED` |

**Licence / redistribution:** CC BY-NC 4.0, attribution to ViDIR Group, Department of Dermatology, Medical University of Vienna. Non-commercial only. Because the masks have no provenance and the licence is non-commercial, **no HAM10000 image, mask or representative segmentation panel is included in this ZIP**. `ext02_ham10000_manifest.csv` is metadata-only (IDs and paths) and its `evaluable=True` flag is **superseded** by the later C1 exclusion; it is retained solely as historical evidence of the candidate inventory.

An earlier `ext01_external_dataset_inventory.json` describes the masks as "ISIC-2018 Task-3 lesion-boundary masks" and marks the cohort `SECONDARY_EXTERNAL_BENCHMARK_ELIGIBLE`. That description is **incorrect** and is overruled by the later C1 evidence audit. HAM10000 was also recorded as `EXTERNAL_OUTCOME_EXPOSED_HISTORICALLY` / `TRACK_B` in Phase 32, and `BLOCKED_NO_ELIGIBLE_COHORT` in the Phase 32 task mapping — historical exposure is **not** equivalent to a valid segmentation evaluation. Semantic leakage risk remains **HIGH** because HAM10000 and ISIC 2018 share the ISIC ID namespace and Task-3 lineage.

**Consequently:** no HAM10000 Dice/IoU/Precision/Recall/HD95 or paired difference is reported. `EXTERNAL_SKIN_EVALUATION_MATRIX.csv` records the *status* of each requested quantity instead of fabricating a number. Producing a quantitative HAM10000 segmentation benchmark requires (a) documented expert masks or a validated annotation protocol, (b) a written licence/ethics determination, and (c) an authorised prospective evaluation — none of which exists.

---

## 5. Redistribution and publication safety register

| Material | In ZIP? | Reason |
|---|---|---|
| `train.csv`, `val.csv`, `router_dev_holdout_split.csv` | Yes | Metadata-only, pseudonymous grouping keys, explicitly permitted frozen development manifests |
| `test.csv`, `quarantined.csv`, `all_paired.csv` | **No** | Protected / leakage-remediation metadata; aggregate counts quoted instead |
| `ext02_ham10000_manifest.csv` | Yes | Metadata-only candidate inventory; flagged as superseded |
| Raw images, masks, `.npz`/`.npy` arrays | **No** | Medical data, licence restrictions, package size |
| Checkpoints (`.pt`, `.pth`, `.ckpt`) | **No** | Large binary weights; hashes are supplied in `REMEDFILM_FULL_COMPONENT_REGISTRY.json` / V8 results registry |
| BUSI patient workbook, credentials, signed approvals | **No** | Sensitive / not cleared |
| Generated figures, tables, reports, audit prose | Yes | Derived, non-sensitive, redistribution-safe |
| Absolute Windows paths in published prose | **No** | Only inside copied frozen manifests (historical provenance); all new documents use relative paths |

**Unresolved human gate (unchanged):** all four primary licences are verified, but the institutional ethics/data-use determination, the explicit `DECISION_I` vs `DECISION_R` policy choice, and a reviewed execution surface remain **PENDING**. Status remains `C1_EXECUTION_BLOCKED__HUMAN_AUTHORIZATION_ACTION_REQUIRED`. See `FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md`.

---

## 6. Evidence index for this guide

| Claim | Frozen source (in ZIP unless noted) |
|---|---|
| Split counts, quarantine reasons | `manifests/phase4_v3/README.md`, `manifests/train.csv`, `manifests/val.csv` |
| Per-dataset native sizes / modes / foreground fractions | `phase19_dataset_inventory.csv` |
| Licences, DOIs, ethics IDs, local mirror gaps | `FINAL_DATASET_PERMISSION_AND_EXECUTION_DECISION.md` |
| Internal preprocessing | `phase19_preprocessing_contract.json` |
| External cohort construction / exclusions | `03_Experimental_Results/external/c1_cohort_construction.json`, `05_Datasets/ext02_dataset_cohort_freeze.json` |
| External preprocessing | `ext02_preprocessing_freeze.json`, `ext02_1_preprocessing_authority_reconciliation.json` |
| External inventory / licences / pairing | `ext01_external_dataset_inventory.json`, `ext01_external_overlap_audit.json` |
| HAM10000 forensic audit | `08_Verification/HAM10000_AUDIT.json`, `HAM10000_AUDIT_REPORT.md` |
| HAM10000 exclusion / single-case metric provenance | `03_Experimental_Results/external/c1_cohort_construction.json`, `c1_claim_provenance.json` |
| Phase 32 HAM exposure status | `phase32_external_dataset_discovery.csv` (in ZIP); `reports/tables/phase32_external_task_mapping.csv`, `phase32_external_prior_exposure_matrix.csv` (repository, metadata only) |
