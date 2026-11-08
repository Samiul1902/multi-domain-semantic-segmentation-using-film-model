# Methodology Figure QA

**Artifact:** `docs/METHODOLOGY_FIGURE_QA.md`
**Subject:** `assets/figures/remedfilm_inference_infographic.png` (authoritative) and
the vector family regenerated from `assets/figures/generate_methodology.py`
**Verdict:** **PASS** — layout defects found in the first generator pass were
repaired; all outputs are valid, editable and scientifically consistent with the
code.

---

## 1. Deliverables

| File | Format | Size | SHA-256 (first 16) | Role |
|---|---|---|---|---|
| `remedfilm_inference_infographic.png` | PNG 1672 × 941 RGB | 1,870,658 B | `a5a5b1457efa51de` | **Authoritative methodology figure**, supplied by the project owner and embedded in `README.md` |
| `remedfilm_full_methodology.svg` | SVG, `viewBox="0 0 1203.84 677.52"`, 2,671 elements | 850,932 B | `cb57d56bd44e0d56` | Editable vector primary |
| `remedfilm_full_methodology.pdf` | PDF-1.4, valid `%%EOF` | 466,329 B | `8f7a1ebc3a7f08ac` | Vector print |
| `remedfilm_full_methodology.png` | PNG 6688 × 3764 RGBA (400 dpi, exactly 4 × board) | 1,511,923 B | `0e34932a0e6f22f5` | Raster preview |
| `remedfilm_methodology_compact.svg` | SVG, `viewBox="0 0 720 504"`, 709 elements | 349,635 B | `da25a3f103ad7f81` | Single-column variant |
| `remedfilm_methodology_compact.png` | PNG 4000 × 2800 RGBA | 524,209 B | `6e4a62b2dfbe916f` | Compact raster |
| `generate_methodology.py` | Python source | 44,522 B | `3cecb83c4edd8bcc` | Single source of truth for the vector family |

Aspect ratio is preserved: `1672 / 941 = 1.7768` and `6688 / 3764 = 1.7768`.
The board uses a pixel coordinate system with `set_aspect("equal")`, so no
`mutation_aspect` distortion is possible.

The authoritative PNG was copied byte-for-byte from
`C:\Users\user\Downloads\ReMedFiLM Full Inference Methodology Infographic.png`;
the source and repository copy have identical SHA-256
`a5a5b1457efa51ded03de52518bfdc3812e0d5d0e191aa8a5793cb97c4dc3223`.

---

## 2. Three-panel content

### Panel A — Multi-domain inputs and task conditioning
Four rows, each with a provenance-verified frozen VAL808 sample thumbnail:

| Row | Domain | Modality label |
|---|---|---|
| 1 | ISIC 2018 | (Dermoscopy) |
| 2 | BUSI-WHU | (Breast Ultrasound) |
| 3 | Kvasir-SEG | (Endoscopy) |
| 4 | KUB-StoneX | (KUB Radiography) |

A convergence bracket leads to **Task identity / domain label `t`**, then to the
**task embedding `E(t)`**, which is drawn entering the G backbone in Panel B.

### Panel B — ReMedFiLM FULL Proposed Inference System
Ribbon: `ReMedFiLM (G + Bφ + Rψ + Sω)`.

Flow, in the order drawn:

1. Input `x` → **G: Task-conditioned GlobalMedFiLM Backbone**, conditioned by `E(t)`.
2. G emits **global probability map `Pg`** and **global features `Fg`**.
3. `Pg` → **ROI proposal / candidate region extraction** (input + red GT-free ROI box, and the cropped ROI mask).
4. `Fg` and the **cropped candidate ROI `xroi`** → **Bφ: Benefit Router**.
5. Router → **Refine?** decision → `SKIP (no useful ROI)` or `REFINE (beneficial)`.
6. `REFINE` → **Rψ: Regional Residual Refiner** → **`ΔP` (corrected local mask)**.
7. `ΔP` → **Sω: Post-Safety Gate** → **Accept?** decision → `ACCEPT (use refinement)` or `REJECT (fallback to Pg)`.
8. `ACCEPT` → **ROI composition (insert refined local mask)** → **ReMedFiLM Final Segmentation `P̂`**.
9. `REJECT` and `SKIP` both route to the final output as the **global fallback / global output**.

A bottom strip spells out the **three legitimate inference outcomes**:
(a) No useful ROI / Skip → global output (`Pg`);
(b) Refine + Accept → composed refined output;
(c) Refine + Reject → global fallback (`Pg`).

### Panel C — Staged training strategy
Subtitle: *separate training with progressive dependency*. Six numbered stages
joined by dashed (training-only) arrows:

`1 Train G` → `2 Generate predictions & ROIs` → `3 Train Rψ` →
`4 Create gain labels (g = M(P_refine) − M(Pg))` → `5 Train Bφ` → `6 Train Sω`.

Two footer bars: *Staged training (G → Rψ → Bφ → Sω)* and *Inference uses the
frozen trained modules: G, Bφ, Rψ and Sω* (snowflake = frozen).

### Legend
Inference flow (solid) · training-only dependency (dashed) · global backbone ·
task conditioning / ROI · routing / decision (Bφ, Sω) · accepted refinement path ·
rejected fallback path.

---

## 3. Scientific consistency checks

| Check | Result |
|---|---|
| G = backbone, not the FULL model | ✔ G is one box inside the FULL system ribbon |
| Four trained components all drawn | ✔ G, Bφ, Rψ, Sω |
| Three legitimate outcomes drawn | ✔ SKIP / REFINE+ACCEPT / REFINE+REJECT |
| **No ground-truth mask on any inference path** | ✔ ROI proposal reads `05_roi_proposal` GT-free geometry; no `02_ground_truth` tile used |
| **No joint end-to-end backpropagation** | ✔ Panel C shows six separate stages with frozen upstream; dashed arrows labelled training-only |
| No teacher–student / distillation drawn | ✔ the model is FiLM, not distillation |
| `E(t)` is the only conditioning input | ✔ single arrow into G |
| Refiner runs **before** Sω | ✔ `ΔP → Sω → Accept?` order |
| ROI proposal threshold ≠ segmentation threshold | ✔ not encoded in the figure; see `docs/METHODOLOGY_IMPLEMENTATION_MAP.md` |
| Sample tiles provenance | ✔ `reports/figures/methodology_diagram_package/representative_samples/`, `source_provenance.json`, `sample_metadata.json` |
| No new inference performed | ✔ generator only reads existing PNG caches; `new_inference_performed: false` in metadata |

**Node → implementation trace:** `docs/METHODOLOGY_IMPLEMENTATION_MAP.md`.
Canonical sources are `src/models/film/global_medfilm.py` (G),
`src/models/barr/regional_refiner.py` (Rψ),
`src/models/barr/phase25_models.py` (Bφ and Sω), and
`src/models/barr/ra_medfilm_barr.py` (assembly).

> **Registry discrepancy (pre-existing, documented not hidden).**
> `full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json` lists Bφ as
> `router_variants.py` and Sω as `ra_medfilm_barr.py`. Checkpoint state-dict
> prefixes were loaded and matched against the classes in this session: the
> canonical implementations are in `phase25_models.py` (`net` / `task_embedding`
> for Bφ, `fc1` / `fc2` / `fc3` for Sω). `router_variants.py` holds Phase-28
> ablation variants R1/R2/R3/F1, not the canonical components. The figure and
> `METHODOLOGY_IMPLEMENTATION_MAP.md` use the verified sources. The JSON was
> **not** edited because it is a frozen artifact.

---

## 4. Defects found and repaired

The first generator pass produced a layout with several collisions. Each was
fixed and re-verified visually.

| # | Defect | Repair | Status |
|---|---|---|---|
| 1 | Figure-fraction coordinates + `mutation_aspect` distorted the aspect ratio and overflowed the canvas | Rewrote onto a 1672 × 941 **pixel** `Board` with `set_aspect("equal")` | FIXED |
| 2 | `Refine?` diamond overlapped the Bφ router box | Lifted the decision row to `iy + 232` and moved Bφ/Sω to `iy + 300` | FIXED |
| 3 | `Accept?` diamond overlapped the `ACCEPT` chip | Re-spaced the ACCEPT / REJECT chips around `ix + 778 / 1054` | FIXED |
| 4 | ROI composition green box collided with the outcomes strip and the blue final bar | Three separate vertical bands: composition at `iy + 108`, final at `iy + 134`, outcomes at `iy + 8` | FIXED |
| 5 | Final-segmentation bar overlapped outcome cells (b) and (c) | Final bar moved above the outcomes strip; outcomes given full width | FIXED |
| 6 | ROI-crop mask tile rendered invisible (RGB overlay treated as a binary mask) | Added `roi_mask_tile()` which crops the frozen ROI window out of the probability map | FIXED |
| 7 | Red ROI box lost on the second ROI tile | `bbox_overlay()` applied to both tiles | FIXED |
| 8 | `Pg` label clipped by the ROI proposal box; `Fg` buried | Both columns shifted to `ix + 276`; label stacks tightened; arrows re-anchored | FIXED |
| 9 | Panel C subtitle overlapped the "Staged training strategy" title | Subtitle right-aligned at `X + W - 16` inside the header band | FIXED |
| 10 | Panel A multi-line modality labels rendered incorrectly | Replaced `"\n" in mod` branching with explicit list-of-strings rows | FIXED |
| 11 | Missing glyph warning for MATHEMATICAL SCRIPT SMALL X | Replaced with plain `xroi` (no glyph substitution) | FIXED |
| 12 | SVG/PDF bytes differed on every regeneration (auto `<dc:date>` timestamp + random clip-path IDs), producing meaningless git diffs | Set `rcParams["svg.hashsalt"]` and per-format `metadata` (`Date: None` for SVG, `CreationDate: None` for PDF); no timestamp is hand-authored | FIXED |

**Final visual QA:** no box-on-box overlaps, no diamond/chip collisions, no
arrows crossing box interiors, no clipped text. All four panel headers, all six
training stages and all seven legend rows are legible.

---

## 5. File-format validity

| Check | Result |
|---|---|
| Full SVG parses as XML | ✔ root `<svg>`, 2,671 elements |
| Compact SVG parses as XML | ✔ root `<svg>`, 709 elements |
| PDF header / trailer | ✔ `%PDF-1.4`, ends with `%%EOF` |
| PNG dimensions | ✔ 1672×941 / 6688×3764 / 4000×2800 |
| Aspect ratio undistorted | ✔ 1.7768 in both board and raster |
| Vector text is real text (not rasterised) | ✔ matplotlib native SVG export; text elements present |
| Byte-level regeneration determinism | ✔ two consecutive runs produced identical SHA-256 for all five outputs |
| Editable source shipped | ✔ `generate_methodology.py`, one code path for all five outputs |
| Regeneration is deterministic and training-free | ✔ no checkpoint load, no GPU, no optimiser |

No `cairosvg`, `svglib` or Inkscape was available, so SVG/PDF are exported
natively by matplotlib. This is recorded so a future reader does not assume an
external conversion step.

---

## 6. Journal suitability

The figure is suitable as a **two-column-spanning** composite for IEEE TMI /
*Medical Image Analysis* style submission:

- Vector SVG + PDF primary, 400 dpi raster fallback.
- DejaVu Serif headings / DejaVu Sans labels, minimum ~7.2 pt at native board
  scale (scales with the figure, so keep at ≥ 1-column width).
- Colour is redundant with text labels and line styles (solid vs dashed), so it
  survives greyscale printing.
- All panel letters (A/B/C), the legend and the outcome labels are explicit.

**Caveats for a real submission:** the four input thumbnails are derived from
frozen validation samples and each dataset's licence must be satisfied
independently (see `README.md` § Supported Datasets). The figure is a schematic
of a research system, **not** a clinically validated workflow, and no
publication acceptance is claimed.

---

## 7. Regenerate

```powershell
.\.venv\Scripts\python.exe assets\figures\generate_methodology.py
```

Expected console output: five lines beginning `wrote assets\figures\...`, then
`done.` No glyph warnings, no training, no writes outside `assets/figures/`.
Regeneration is byte-stable: SVG/PDF carry no creation timestamp and the SVG
clip-path IDs use a fixed salt, so a rebuild does not create a spurious diff.
