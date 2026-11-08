<div align="center">

# ReMedFiLM

### Risk-Averse Task-Conditioned Medical Image Segmentation with Selective Regional Refinement

**FULL RA-MedFiLM-BARR** — a task-conditioned global backbone (G) coupled to a learned
benefit router (B<sub>φ</sub>), a regional residual refiner (R<sub>ψ</sub>) and a post-safety gate (S<sub>ω</sub>).

[![Python](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)](docs/REPRODUCIBILITY_GUIDE.md)
[![PyTorch](https://img.shields.io/badge/pytorch-2.6.0%2Bcu124-EE4C2C?logo=pytorch&logoColor=white)](docs/REPRODUCIBILITY_GUIDE.md)
[![Task](https://img.shields.io/badge/task-medical%20image%20segmentation-0B5394)](docs/REPOSITORY_MAP.md)
[![Status](https://img.shields.io/badge/status-research%20code-B26A00)](docs/REPOSITORY_MAP.md)
[![Reproducibility](https://img.shields.io/badge/reproducibility-analysis--only%20verified-2E7D32)](docs/REPRODUCIBILITY_GUIDE.md)
[![Tests](https://img.shields.io/badge/QA%20checks-38%2F38%20passing-2E7D32)](full_doc_report/REMEDFILM_FINAL_QA_CHECKS.json)

**Research code. Not clinically validated. No publication acceptance is claimed.**

</div>

---

## Overview

Medical image segmentation models are usually trained per anatomy. One shared model
must instead cope with lesions that differ by orders of magnitude — a dermoscopy lesion
may fill most of the frame, while a kidney stone is a few hundred pixels inside a
512 × 512 radiograph.

ReMedFiLM addresses this with **selective** extra computation:

1. **One task-conditioned global network** segments all four domains cheaply. The task
   identity enters only through a learned embedding and FiLM modulation, so the
   backbone and the single foreground head are shared.
2. A **learned router** scores each candidate region and predicts whether refining it
   will actually help. Most regions are skipped.
3. A **regional refiner** re-segments only the selected regions.
4. A **post-safety gate** can veto a refinement that looks harmful, falling back to the
   global prediction.

The design premise is that *unconditional* refinement is unsafe: in the historical
ablation, refining every candidate harmed **42.7 %** of them. Routing and a safety gate
are the response to that measurement.

> **GlobalMedFiLM is the backbone of ReMedFiLM, not ReMedFiLM.** A GlobalMedFiLM
> checkpoint, prediction or score is never presented here as a FULL-system result.

---

## Full ReMedFiLM Methodology

<div align="center">

<a href="assets/figures/remedfilm_inference_infographic.png">
  <img src="assets/figures/remedfilm_inference_infographic.png"
       alt="ReMedFiLM full inference methodology infographic. Panel A: four multi-domain inputs (ISIC 2018 dermoscopy, BUSI-WHU breast ultrasound, Kvasir-SEG endoscopy, KUB-StoneX radiography) feed a task-identity node and a task embedding E(t). Panel B: the FULL proposed inference system — the task-conditioned GlobalMedFiLM backbone G produces a global probability map Pg and global features Fg; a GT-free ROI proposal extracts a candidate region; the benefit router B_phi decides Refine?; the regional residual refiner R_psi yields a corrected local mask delta-P; the post-safety gate S_omega decides Accept?, giving three legitimate inference outcomes — skip to the global output, refine plus accept, or refine plus reject with global fallback. Panel C: the staged training strategy, six separate stages in progressive dependency order G, then predictions and ROIs, then R_psi, then gain labels, then B_phi, then S_omega, with inference using the frozen trained modules."
       width="100%">
</a>

*ReMedFiLM methodology — the authoritative figure. Click for the full-resolution
raster ([PNG](assets/figures/remedfilm_inference_infographic.png)) or open the
editable vector source
([SVG](assets/figures/remedfilm_full_methodology.svg) ·
[PDF](assets/figures/remedfilm_full_methodology.pdf)) ·
[high-resolution PNG](assets/figures/remedfilm_full_methodology.png) ·
[single-column version](assets/figures/remedfilm_methodology_compact.svg)*

</div>

> **What the figure does and does not show.** Panel C depicts *separate training
> with progressive dependency* — six stages, each fitted against a frozen
> upstream. **No joint end-to-end backpropagation is drawn, because none is
> implemented.** No ground-truth mask appears on any inference path: the ROI
> proposal is GT-free, and every sample tile shown comes from the frozen Phase 27
> / Phase 29 validation caches.

### The four trained components

| | Component | Role | Parameters |
|---|---|---|---|
| **G** | Task-conditioned GlobalMedFiLM backbone | FiLM modulation at `bridge, decoder4…1`; one shared foreground head | 3,523,001 |
| **B<sub>φ</sub>** | Learned benefit router | scores GT-free candidate features, decides `REFINE` or `SKIP` | 36,801 |
| **R<sub>ψ</sub>** | Regional residual refiner | refines the selected ROI crops (4-channel input) | 1,276,401 |
| **S<sub>ω</sub>** | Post-safety gate | accepts or vetoes each refinement | 1,217 |
| | **ReMedFiLM FULL** | assembled inference system | **4,837,420** |

Parameter counts were **re-derived by loading each checkpoint and summing its state
dict** — see [`REMEDFILM_FULL_COMPONENT_REGISTRY.json`](full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json).

### Three legitimate outcomes

| Outcome | Condition | Result |
|---|---|---|
| **(a) SKIP** | router utility < τ<sub>C8</sub> | global mask kept; refiner never runs |
| **(b) REFINE + ACCEPT** | router selects, safety accepts | refined ROI composed into the global mask |
| **(c) REFINE + REJECT** | router selects, safety vetoes | global fallback |

On the 808-image validation set: **529 skip · 266 accept · 13 reject**.

A node-by-node trace from this diagram to the implementing class, function and
configuration is in [`docs/METHODOLOGY_IMPLEMENTATION_MAP.md`](docs/METHODOLOGY_IMPLEMENTATION_MAP.md).
Figure construction, defect log and format checks:
[`docs/METHODOLOGY_FIGURE_QA.md`](docs/METHODOLOGY_FIGURE_QA.md).

---

## Key Contributions

1. **A task-conditioned shared backbone for four heterogeneous modalities.** FiLM
   modulation with a zero-initialised output projection means every modulation site
   starts as the identity, so the network begins as a plain U-Net-shaped segmenter and
   learns its conditioning.
2. **Selective rather than unconditional refinement.** A learned router spends compute
   only where a benefit is predicted; unconditional refinement was measured at a 42.7 %
   harm rate, which motivates the selection step.
3. **A post-safety veto with an explicit fallback.** The system can decline its own
   refinement and return the backbone mask, which is what makes "refine and reject" a
   first-class outcome rather than a failure.
4. **An honest evidence base.** Every reported number traces to a frozen artifact;
   negative results (14/14 stone-free false positives, an inconclusive safety
   contrast, severe external domain shift) are reported rather than smoothed.

**Not claimed:** causal FiLM attribution (C1, 0/6 runs), causal component attribution
(C2, not established), an independent multi-seed benchmark (C3, 0/24 cells), or any
safety guarantee.

---

## Supported Datasets

Four domains, **four separate binary foreground/background tasks** — not four output
channels of one network.

| Domain | Modality | Foreground | Source | Terms |
|---|---|---|---|---|
| **ISIC 2018** | Dermoscopy | Skin lesion | [challenge.isic-archive.com](https://challenge.isic-archive.com/data/) | Task 1 data is **CC0** |
| **BUSI-WHU** | Breast ultrasound | Breast lesion | [Mendeley, v3](https://data.mendeley.com/datasets/k6cpmwybk3/3) | **CC BY 4.0**, attribution required |
| **Kvasir-SEG** | Endoscopy | Gastrointestinal polyp | [datasets.simula.no](https://datasets.simula.no/kvasir-seg/) | Research/educational use; **commercial use requires written permission** |
| **KUB-StoneX** | Radiography (KUB) | Kidney / ureteric / bladder stone | [figshare DOI](https://doi.org/10.6084/m9.figshare.32049369.v1) | **CC BY 4.0**, attribution required |

Split sizes: **TRAIN 5,832 · VAL 808 · TEST 1,683**. Training data further divides into
ROUTER_DEVELOPMENT 4,957 and ROUTER_HOLDOUT 875.

**No medical images, patient spreadsheets or dataset copies are stored in this
repository.** Only derived masks and metrics are referenced. Any reuse must satisfy the
terms above independently.

> **KUB grouping caveat.** The KUB manifest contains 873 full-field radiographs **and**
> 1,385 ROI instance patches. They are not interchangeable image units, and analyses
> distinguish them.

---

## Research Results

Historical, single-seed (42) development results on the identical 808-image validation
set, re-scored from saved masks:

| Model | Parameters | VAL808 macro Dice | Notes |
|---|---|---|---|
| U-Net | 7,763,041 | 0.7878 | conventional baseline |
| Attention U-Net | 7,851,285 | 0.7890 | conventional baseline |
| U-Net++ | 9,159,681 | 0.7920 | conventional baseline |
| Transformer / MiT-style U-Net | 16,347,777 | 0.8224 | conventional baseline |
| DeepLabV3+ | 40,347,041 | 0.8277 | conventional baseline |
| **GlobalMedFiLM (G)** | 3,523,001 | 0.8351 | **backbone, not the full model** |
| **ReMedFiLM FULL** | **4,837,420** | **0.8373** | **proposed system** |

**Paired improvement, FULL − backbone:** `+0.002210`, 95 % CI `[+0.001147, +0.003292]`
(10,000-replicate domain-stratified bootstrap, CI excludes zero).

| Domain | n | GlobalMedFiLM | ReMedFiLM FULL | Δ |
|---|---|---|---|---|
| ISIC | 357 | 0.8972 | 0.8981 | +0.0009 |
| BUSI | 84 | 0.8588 | 0.8589 | +0.0001 |
| Kvasir | 87 | 0.8202 | 0.8207 | +0.0004 |
| KUB | 280 | 0.7641 | 0.7715 | **+0.0075** |

### Retrospective external evaluation (884 cases, separate cohorts)

| Cohort | n | GlobalMedFiLM | ReMedFiLM FULL | HD95 (px) |
|---|---|---|---|---|
| CVC-ClinicDB | 612 | 0.6866 | 0.6897 | 109.6 → 108.5 |
| BrEaST-Lesions-USG | 252 | 0.7078 | 0.7081 | 74.0 → 73.3 |
| Stones-Where-Are-You | 20 | 0.0808 | 0.0821 | 166.9 → 169.9 *(n = 6)* |

**Preserved negative results.** The Stones cohort collapses under domain shift
(Dice ≈ 0.08), and **14 / 14 stone-free images receive a foreground prediction** in both
arms — the safety gate scores refinement benefit, not lesion presence, so it cannot fix
negative studies. These are reported as failures, not outliers.

### On the two circulating FULL values

An earlier report quoted `0.837862` and `34.72 GMACs`. Both are wrong:

- **`0.837290`** is reproducible from the saved masks and matches Phase 27 and Phase 29
  to `1.8 × 10⁻⁷`.
- **`0.837862`** appears in no frozen artifact. It is the mean of three hardcoded numbers
  in the report generator, printed both as the seed-42 row and as the three-seed mean.
  No routing policy expressible from the saved masks reproduces it.
- **`34.72 GMACs`** is the *always-refine* cost. The deployed system routes 24.3 % of
  cases, so its expected conditional cost is **32.4379 GMACs**.

Full analysis: [`REMEDFILM_FULL_RESULT_RECONCILIATION.md`](full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md).

---

## Repository Structure

```text
jup/
├── README.md                     ← you are here
├── assets/figures/               methodology diagrams (SVG / PDF / PNG) + generator
├── docs/                         repository map, method→code trace, reproducibility
├── src/
│   ├── models/film/              GlobalMedFiLM backbone (G)
│   ├── models/barr/              router, refiner, safety gate, FULL wrapper
│   ├── models/                   conventional baselines
│   ├── data/                     ROI transforms and datasets
│   ├── metrics/                  Dice / IoU / HD95
│   └── research/                 C1 / C2 / C3 and pipeline code
├── scripts/
│   ├── training/                 training entry points (gated)
│   └── analysis/                 evaluation and report builders
├── notebooks/phasewise/          57 phase directories of research history
├── manifests/phase4_v3/          TRAIN / VAL / TEST splits
├── experiments/                  82 per-epoch history.csv records
├── checkpoints/                  weights (git-ignored, not distributed)
├── reports/                      audits and tables
├── full_doc_report/              verified consolidation: notebooks, tables, figures
└── tests/                        automated tests
```

Full navigation: **[`docs/REPOSITORY_MAP.md`](docs/REPOSITORY_MAP.md)** — six maps
covering all 57 phase directories, model locations, training evidence, results and
reproduction tooling.

---

## Quick Navigation

| I want to… | Go to |
|---|---|
| Understand the architecture | [`docs/METHODOLOGY_IMPLEMENTATION_MAP.md`](docs/METHODOLOGY_IMPLEMENTATION_MAP.md) |
| Read the full research record | [`full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb`](full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb) |
| See the full model code | [`src/models/barr/ra_medfilm_barr.py`](src/models/barr/ra_medfilm_barr.py) |
| See the backbone code | [`src/models/film/global_medfilm.py`](src/models/film/global_medfilm.py) |
| Understand staged assembly | master §06 · [`registry`](full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json) |
| Inspect trained checkpoints | [`REMEDFILM_FULL_COMPONENT_REGISTRY.json`](full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json) |
| Analyse epoch-wise training | master §05 · [`REMEDFILM_COMPONENT_TRAINING_HISTORY.csv`](full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv) |
| View internal validation | master §07 · [`figures/Internal validation/`](full_doc_report/figures/Internal%20validation/) |
| View segmentation predictions | master §08 · [`figures/Semantic segmentation/`](full_doc_report/figures/Semantic%20segmentation/) |
| View external evaluation | master §10 · [`figures/External evaluation/`](full_doc_report/figures/External%20evaluation/) |
| Inspect the 13-arm ablation | master §12 · [`figures/Ablation/`](full_doc_report/figures/Ablation/) |
| View component progression | master §11 · [`figures/Progression/`](full_doc_report/figures/Progression/) |
| Study routing and safety | master §13 · [`figures/Routing and safety/`](full_doc_report/figures/Routing%20and%20safety/) |
| Study robustness | master §15 · [`figures/Robustness/`](full_doc_report/figures/Robustness/) |
| Study efficiency | master §16 · [`figures/Efficiency/`](full_doc_report/figures/Efficiency/) |
| Review historical TEST results | master §17 |
| Run the safe analyses | [`docs/REPRODUCIBILITY_GUIDE.md`](docs/REPRODUCIBILITY_GUIDE.md) |
| See what is still missing | [`PENDING_CONTROLLED_EXPERIMENTS.md`](full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md) |

---

## Installation and Environment

```powershell
git clone https://github.com/Samiul1902/multi-domain-semantic-segmentation-using-film-simulation.git
cd multi-domain-semantic-segmentation-using-film-simulation

py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Verified stack: **Python 3.11.9 · PyTorch 2.6.0+cu124 · CUDA 12.4**.

```powershell
.\.venv\Scripts\python.exe -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

> `requirements.txt` currently omits **`scipy`** (used for HD95) — if
> `build_metrics.py` raises `ModuleNotFoundError: scipy`, install it explicitly.
> Details in the [reproducibility guide](docs/REPRODUCIBILITY_GUIDE.md).

---

## Reproducibility

**Analysis-only reproduction is fully supported and verified. Training is not.**

```powershell
# 1. execute the whole verified notebook family (analysis-only, guard-enforced)
.\.venv\Scripts\python.exe full_doc_report\Scripts\execute_notebooks.py
#    -> TOTAL 22 notebooks | 292/292 cells | OK

# 2. rebuild the research figures
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_figures.py

# 3. rebuild the methodology diagrams
.\.venv\Scripts\python.exe assets\figures\generate_methodology.py

# 4. re-score the saved masks and rebuild every table
.\.venv\Scripts\python.exe full_doc_report\Scripts\build_metrics.py

# 5. verify
.\.venv\Scripts\python.exe full_doc_report\Scripts\verify_verified.py   # 38/38
```

`ANALYSIS_ONLY` is enforced by an installed `sys.addaudithook`: process launches, writes
outside the report directory and reads of the protected TEST manifest are blocked, and
`torch.optim.*` / `Module.train(True)` are replaced by raising callables. Four negative
controls must print `blocked` or the notebook aborts.

The strongest available check is `build_metrics.py`, which reproduces the frozen
Phase 27 paired macro Δ Dice to **1.8 × 10⁻⁷** from masks alone.

No command above launches an unapproved experiment.

---

## Experimental Status

| Item | Status |
|---|---|
| Conventional baselines (5 models, VAL808) | **available** |
| ReMedFiLM modular implementation (G/R/B/S) | **implemented, verified** |
| Historical FULL validation (VAL808, seed 42) | **available** |
| Historical 13-arm ablation | **available** |
| Historical external evaluation (884 cases) | **available** |
| Robustness (12 perturbations, 12,928 instances) | **available** |
| Historical TEST1683 (descriptive only) | **available — access consumed, not reopenable** |
| **C1** controlled learned-vs-identity FiLM | **pending — 0 / 6 runs** |
| **C2** fully causal component attribution | **not established** (A8 vs A7 CI includes zero) |
| **C3** independent 8-model × 3-seed benchmark | **pending — 0 / 24 cells** |
| New untouched prospective external cohort | **pending** |

Synthetic unit tests are never presented as evidence that an experiment ran.
Details: [`PENDING_CONTROLLED_EXPERIMENTS.md`](full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md).

---

## Figures and Reports

| Figure | Link |
|---|---|
| **Methodology infographic** (authoritative) | [PNG](assets/figures/remedfilm_inference_infographic.png) |
| Full methodology, editable vector | [SVG](assets/figures/remedfilm_full_methodology.svg) · [PDF](assets/figures/remedfilm_full_methodology.pdf) · [PNG](assets/figures/remedfilm_full_methodology.png) |
| Methodology, single column | [SVG](assets/figures/remedfilm_methodology_compact.svg) |
| Methodology generator (source of truth) | [`assets/figures/generate_methodology.py`](assets/figures/generate_methodology.py) |
| Per-domain metrics | [Internal validation](full_doc_report/figures/Internal%20validation/) |
| Segmentation galleries | [Semantic segmentation](full_doc_report/figures/Semantic%20segmentation/) |
| External evaluation | [External evaluation](full_doc_report/figures/External%20evaluation/) |
| 13-arm ablation | [Ablation](full_doc_report/figures/Ablation/) |
| Component progression | [Progression](full_doc_report/figures/Progression/) |
| Routing and safety | [Routing and safety](full_doc_report/figures/Routing%20and%20safety/) |
| Training curves | [Training curves](full_doc_report/figures/Training%20curves/) |
| Robustness | [Robustness](full_doc_report/figures/Robustness/) |
| Accuracy vs compute | [Efficiency](full_doc_report/figures/Efficiency/) |
| Reproducibility statistics | [Statistics](full_doc_report/figures/Statistics/) |

All methodology figures are regenerated by one command:

```powershell
.\.venv\Scripts\python.exe assets\figures\generate_methodology.py
```

Reviewed report: [`REMEDFILM_FINAL_SCIENTIFIC_QA.md`](full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md)

Documentation audits:
[link verification](docs/README_LINK_VERIFICATION.md) ·
[publication safety check](docs/GITHUB_PUBLICATION_SAFETY_CHECK.md) ·
[methodology figure QA](docs/METHODOLOGY_FIGURE_QA.md).

---

## Citation

No paper has been published and no DOI exists for this work. **Do not cite it as a
publication.** If you need to reference the code, use:

```bibtex
@misc{remedfilm2026,
  title  = {ReMedFiLM: Risk-Averse Task-Conditioned Medical Image Segmentation
            with Selective Regional Refinement (FULL RA-MedFiLM-BARR)},
  author = {{ReMedFiLM research project}},
  year   = {2026},
  note   = {Research code, not peer-reviewed; no publication status claimed},
  url    = {https://github.com/Samiul1902/multi-domain-semantic-segmentation-using-film-simulation}
}
```

Author identities are intentionally left generic — no verified author list or
affiliation is recorded in the repository. Update this block only when a real
publication record exists.

---

## Licence and Research Use

- **Source code: no licence file is present in this repository.** Absent an explicit
  licence, the default is all rights reserved. Add a `LICENSE` file before distributing
  or reusing the code.
- **Dataset licences are separate and are not inherited by the code.** ISIC 2018 Task 1
  is CC0; BUSI-WHU and KUB-StoneX are CC BY 4.0 (attribution required); **Kvasir-SEG
  permits research/educational use and requires written permission for commercial use.**
- **No dataset is redistributed here.** Any reuse must independently satisfy the terms
  of each provider.
- The repository contains no patient-identifiable material. A patient-information
  workbook shipped with BUSI-WHU is deliberately excluded and must never be published.

---

## Limitations and Disclaimer

- **Research only.** No clinical validation, no regulatory clearance, no deployment.
- **Backbone ≠ full model.** GlobalMedFiLM results are labelled as backbone results
  throughout; only the four-component assembly is ReMedFiLM.
- **Domain shift is severe.** External Stones Dice is ≈ 0.08, and every stone-free case
  is a false positive.
- **The safety gate's own contribution is inconclusive.** The only pre-specified matched
  contrast (A8 vs A7) has a 95 % CI that includes zero: `+1.57 × 10⁻⁵ [−1.43 × 10⁻⁵, +5.11 × 10⁻⁵]`.
- **"Three seeds" are not three independent runs.** Seeds 42/123/3407 re-fit the
  downstream components on one **shared frozen backbone**; the identical backbone score
  across seeds (SD ≈ 1.4 × 10⁻¹⁶) proves it.
- **C1/C2/C3 remain unexecuted.** The central causal claims about FiLM modulation and
  component contribution are untested.
- **Historical TEST access is consumed.** The single permitted evaluation has been used;
  no comparative endpoint exists on TEST.

---

<div align="center">
<sub>Documentation verified against source artifacts · 38/38 QA checks · no training performed</sub>
</div>
