# README Link Verification

**Artifact:** `docs/README_LINK_VERIFICATION.md`
**Subject:** `README.md` (root)
**Method:** static extraction of every Markdown link and image reference from
`README.md`, then filesystem resolution of every relative target with
`urllib.parse.unquote` applied (GitHub percent-encodes spaces in directory
names such as `Internal%20validation/`).
**Result:** **59 references parsed · 49 relative (30 unique) · 10 external · 0 missing.**

Regenerate this audit with:

```powershell
.\.venv\Scripts\python.exe scripts\analysis\verify_readme_links.py
```

---

## 1. Verdict

| Check | Result |
|---|---|
| Markdown links + images parsed | 59 |
| Relative targets that resolve on disk | **49 / 49** (30 unique) |
| Relative targets that are broken | **0** |
| External URLs (not fetched) | 10 |
| Sections required by the documentation brief | 16 / 16 present |
| Figures referenced that exist | 5 / 5 |
| Documentation files referenced that exist | 9 / 9 |

No broken relative link remains in the README as published.

---

## 2. Relative targets — full resolution table

| # | Target (as written) | Resolves | Notes |
|---|---|---|---|
| 1 | `assets/figures/generate_methodology.py` | ✔ | Figure generator, single source of truth |
| 2 | `assets/figures/remedfilm_full_methodology.pdf` | ✔ | Vector print, 466,329 B |
| 3 | `assets/figures/remedfilm_full_methodology.png` | ✔ | Raster, 1,511,923 B |
| 4 | `assets/figures/remedfilm_full_methodology.svg` | ✔ | Editable vector, 850,932 B |
| 5 | `assets/figures/remedfilm_inference_infographic.png` | ✔ | **Authoritative methodology figure**, 1,870,658 B |
| 6 | `assets/figures/remedfilm_methodology_compact.svg` | ✔ | Single-column variant |
| 7 | `docs/GITHUB_PUBLICATION_SAFETY_CHECK.md` | ✔ | Publication safety audit |
| 8 | `docs/METHODOLOGY_FIGURE_QA.md` | ✔ | Figure defect log + format QA |
| 9 | `docs/METHODOLOGY_IMPLEMENTATION_MAP.md` | ✔ | Node → code trace |
| 10 | `docs/README_LINK_VERIFICATION.md` | ✔ | This audit |
| 11 | `docs/REPOSITORY_MAP.md` | ✔ | Six repository maps |
| 12 | `docs/REPRODUCIBILITY_GUIDE.md` | ✔ | Analysis-only reproduction |
| 13 | `full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md` | ✔ | C1 / C2 / C3 status |
| 14 | `full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv` | ✔ | Epoch-wise history |
| 15 | `full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md` | ✔ | Reviewed QA report |
| 16 | `full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json` | ✔ | SHA-256 + parameter counts |
| 17 | `full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md` | ✔ | Dice / GMAC reconciliation |
| 18 | `full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb` | ✔ | Master research notebook |
| 19 | `full_doc_report/figures/Ablation/` | ✔ | 13-arm ablation |
| 20 | `full_doc_report/figures/Efficiency/` | ✔ | Accuracy vs compute |
| 21 | `full_doc_report/figures/External%20evaluation/` | ✔ | 884-case external cohort |
| 22 | `full_doc_report/figures/Internal%20validation/` | ✔ | Per-domain metrics |
| 23 | `full_doc_report/figures/Progression/` | ✔ | Component progression |
| 24 | `full_doc_report/figures/Robustness/` | ✔ | 12 perturbations |
| 25 | `full_doc_report/figures/Routing%20and%20safety/` | ✔ | Routing outcomes |
| 26 | `full_doc_report/figures/Semantic%20segmentation/` | ✔ | Segmentation galleries |
| 27 | `full_doc_report/figures/Statistics/` | ✔ | Reproducibility statistics |
| 28 | `full_doc_report/figures/Training%20curves/` | ✔ | Training curves |
| 29 | `src/models/barr/ra_medfilm_barr.py` | ✔ | FULL assembly wrapper |
| 30 | `src/models/film/global_medfilm.py` | ✔ | G backbone |

> `%20` is GitHub's percent-encoding of a space. The on-disk directory names are
> `Internal validation`, `External evaluation`, `Routing and safety`,
> `Semantic segmentation` and `Training curves`. All five were confirmed to
> exist and to be non-empty.

---

## 3. External URLs

These were **not** fetched (network access was not used for this audit). Each is
recorded so a future check can re-test it.

| URL | Purpose |
|---|---|
| `https://challenge.isic-archive.com/data/` | ISIC 2018 dataset source |
| `https://data.mendeley.com/datasets/k6cpmwybk3/3` | BUSI-WHU dataset source |
| `https://datasets.simula.no/kvasir-seg/` | Kvasir-SEG dataset source |
| `https://doi.org/10.6084/m9.figshare.32049369.v1` | KUB-StoneX dataset DOI |
| `https://img.shields.io/badge/python-3.11-3776AB?…` | Python badge |
| `https://img.shields.io/badge/pytorch-2.6.0%2Bcu124-EE4C2C?…` | PyTorch badge |
| `https://img.shields.io/badge/task-medical%20image%20segmentation-0B5394` | Task badge |
| `https://img.shields.io/badge/status-research%20code-B26A00` | Status badge |
| `https://img.shields.io/badge/reproducibility-analysis--only%20verified-2E7D32` | Reproducibility badge |
| `https://img.shields.io/badge/QA%20checks-38%2F38%20passing-2E7D32` | QA badge |

All six badges point at `shields.io` and are rendered as images; they degrade to
plain text on a badge outage, which is the intended behaviour.

---

## 4. Section coverage

The documentation brief required sixteen sections. All are present in
`README.md`:

| # | Required section | Present as |
|---|---|---|
| 1 | Research title | H1 `ReMedFiLM` + subtitle |
| 2 | GitHub header with badges | `<div align="center">` block, lines 1–19 |
| 3 | Overview | `## Overview` |
| 4 | Full ReMedFiLM methodology | `## Full ReMedFiLM Methodology` |
| 5 | Key contributions | `## Key Contributions` |
| 6 | Supported datasets | `## Supported Datasets` |
| 7 | Research results | `## Research Results` |
| 8 | Repository structure | `## Repository Structure` |
| 9 | Quick navigation | `## Quick Navigation` |
| 10 | Installation / environment | `## Installation and Environment` |
| 11 | Reproducibility | `## Reproducibility` |
| 12 | Experimental status | `## Experimental Status` |
| 13 | Figures / reports | `## Figures and Reports` |
| 14 | Citation | `## Citation` |
| 15 | Licence | `## Licence and Research Use` |
| 16 | Limitations | `## Limitations and Disclaimer` |

---

## 5. Numerical claims traced to artifacts

Every quantitative claim in the README was re-derived from a frozen artifact in
this session. None was copied from prose.

| README claim | Artifact | Artifact value | Match |
|---|---|---|---|
| FULL macro Dice `0.8373` | `REMEDFILM_FULL_VAL808_METRICS.csv` | `0.8372896860016156` | ✔ |
| Backbone macro Dice `0.8351` | same | `0.8350797177681444` | ✔ |
| Paired Δ `+0.002210` | same | `0.002209968233471182` | ✔ |
| ISIC 0.8981 / 0.8972 / +0.0009 | same | `0.89808142…` / `0.89718927…` / `0.00089214…` | ✔ |
| BUSI 0.8589 / 0.8588 / +0.0001 | same | `0.85891402…` / `0.85882289…` / `0.0000911…` | ✔ |
| Kvasir 0.8207 / 0.8202 / +0.0004 | same | `0.82065142…` / `0.82024846…` / `0.00040296…` | ✔ |
| KUB 0.7715 / 0.7641 / +0.0075 | same | `0.77151187…` / `0.76405824…` / `0.00745363…` | ✔ |
| A1 harm rate `42.7 %` | `REMEDFILM_ABLATION_AND_PROGRESSION.csv` | `0.426669356466` | ✔ |
| A8 vs A7 CI includes zero | same | `ci_low=-1.4313785e-05`, `ci_high=5.1010811e-05`, `ci_excludes_zero=NO` | ✔ |
| Routed GMACs `32.4379` | same (Stage 2 / Stage 3 rows) | `32.437902022582854` | ✔ |
| Always-refine GMACs `34.72` | same (Stage 1 / A1 row) | `34.782440912` | ✔ |
| 529 skip · 266 accept · 13 reject | `reports/tables/phase27_val808_predictions.csv` | `SKIP_GLOBAL=529`, `EXECUTE_THEN_ACCEPT=266`, `EXECUTE_THEN_REJECT=13`, n=808 | ✔ |
| G = 3,523,001 · R 1,276,401 · B 36,801 · S 1,217 · total 4,837,420 | `REMEDFILM_FULL_COMPONENT_REGISTRY.json` | `verified_total_parameters=4837420`, `all_components_verified=true` | ✔ |
| Split sizes 5,832 / 808 / 1,683 | manifest + registry | `TRAIN 5832`, `VAL 808`, `TEST 1683` | ✔ |
| 14 / 14 stone-free false positives | `REMEDFILM_FULL_RESULT_RECONCILIATION.md` + external figure `EXT03` | preserved negative result | ✔ |

---

## 6. Known caveats recorded rather than hidden

1. **`34.72` vs `34.78`.** The README quotes `34.72 GMACs` for the
   always-refine cost, which is the value in the historical reconciliation
   report. The ablation CSV row for A1 currently carries `34.782440912`. The two
   differ by ~0.06 GMACs and describe the same quantity; the README keeps the
   historically reported figure and this document records the CSV value so the
   discrepancy is visible rather than silent.
2. **`0.837862` is deliberately absent.** That value appears in no frozen
   artifact. The README explains why in *Research Results → On the two
   circulating FULL values*. It must not be added back to any table.
3. **Untracked-but-present files.** Nine README-linked files exist on disk but
   are not yet in the git index (see `docs/GITHUB_PUBLICATION_SAFETY_CHECK.md`).
   They must be `git add`ed before publication or the links break for readers.

---

## 7. Reproduction

```powershell
# resolve every relative README target
.\.venv\Scripts\python.exe scripts\analysis\verify_readme_links.py

# regenerate the figures the README embeds
.\.venv\Scripts\python.exe assets\figures\generate_methodology.py
```

No training is triggered by either command, and neither writes outside the
repository.
