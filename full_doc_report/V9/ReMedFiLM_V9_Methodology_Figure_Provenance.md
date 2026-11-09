# ReMedFiLM V9 Methodology Figure Provenance and Divergence Register

**Artifact:** `full_doc_report/V9/figures/ReMedFiLM_V9_Conceptual_Infographic.png`
**Report placement:** Figure 3, Section 2.6 of `ReMedFiLM_Complete_Scientific_Report_V9`
**Status:** `CONCEPTUAL_NOT_CODE_VERIFIED`
**Purpose of this file:** record exactly where the operator-supplied diagram came from, and exactly where it departs from the frozen implementation, so the figure can never be cited as implementation evidence.

---

## 1. Provenance

| Item | Value |
| :--- | :--- |
| Original supplied path | `C:\Users\user\Downloads\ReMedFiLM Full Inference Methodology Infographic.png` |
| Repository copy | `full_doc_report/V9/figures/ReMedFiLM_V9_Conceptual_Infographic.png` |
| Copy operation | byte-identical file copy (no re-encoding, no retouching) |
| Pixel geometry | 1672 x 941, RGB |
| SHA-256 | recorded in `V9_FINAL_REPORT_MANIFEST.json` (`conceptual_infographic.sha256`) |
| Supplied by | report operator, as the requested methodology diagram |
| Role in report | conceptual schematic of the intended four-component design |

The figure is **not** a renderer output and **not** a verification artifact. It was not produced by `v9_figure_methodology.py`, and no arrow in it was machine-checked.

## 2. Authority order

1. `full_doc_report/V9/figures/ReMedFiLM_Methodology_Manuscript.png` (Figure 2) — arrow-by-arrow code-verified diagram. **Authoritative.**
2. `src/models/barr/ra_medfilm_barr.py`, `src/models/film/global_medfilm.py`, `src/models/barr/phase25_models.py` — source of truth.
3. This infographic (Figure 3) — illustrative only.

Where Figure 2 and Figure 3 disagree, Figure 2 governs. Section 2.6 of the report states this explicitly, and the caption of Figure 3 states that Panel B is aspirational with respect to the frozen code.

## 3. Divergence register (Figure 3 versus verified code)

| ID | Visual claim in Figure 3 | Verified implementation | Disposition |
| :--- | :--- | :--- | :--- |
| **D1** | One shared task embedding `E(t)` feeds the whole chain | Three separate task representations: `G` uses a 32-D learned embedding, `B_phi` a separate 16-D learned embedding, `S_omega` a 4-D one-hot | Retained in Figure 3 as a simplification; stated in the register |
| **D2** | `B_phi` consumes "global features `F_g`" | `B_phi` consumes a 202-D ground-truth-free numeric feature vector plus its own 16-D embedding (218-D input); it never sees a global feature tensor or the ROI crop | Corrected in Figure 2; disclosed here |
| **D3** | `R_psi` emits `dP`, a correction *added* to the global map | `R_psi` emits a refined crop probability map; fusion is deterministic window **replacement** inside the expanded ROI, with no addition and no alpha blending | Corrected in Figure 2; disclosed here |
| **D4** | `R_psi` is invoked online inside the inference path | The canonical wrapper never calls the refiner module; a cached out-of-fold refined crop probability is supplied by the caller | **Material** deviation, disclosed in Sections 2.6 and 2.7 |
| **D5** | One `SKIP` route | Two distinct skip states: `FORCED_SKIP` (no available action) and `SKIP_GLOBAL` (router utility below `tau_C8`) | Corrected in Figure 2; disclosed here |
| **D6** | "ROI composition" drawn as `+` | Replacement of `p_global` inside the expanded ROI only; `p_global` is retained everywhere outside it | Corrected in Figure 2; disclosed here |
| **D7** | Training panel implies a uniform staged objective | Three different losses across stages (0.5 BCE + 0.5 soft Dice for `R_psi`; Huber for `B_phi`; BCE-with-logits for `S_omega`); no joint end-to-end objective exists | Directionally correct, not literal; disclosed in Section 2.5 |

## 4. Why the figure is retained anyway

1. The operator explicitly requested this diagram in the V9 report and documentation.
2. It communicates the **intended** four-component system (`G + R_psi + B_phi + S_omega`) more legibly than any renderer output at page width.
3. Its three-panel layout matches the report narrative: multi-domain inputs, conditional inference, staged training.
4. The risk it creates — being mistaken for a working end-to-end pipeline — is neutralised by the caption, the Section 2.6 divergence register, Section 2.7 (implementation class), and this file, all of which state the opposite in unambiguous terms.

## 5. Mandatory citation rule

Any downstream use (slides, thesis chapter, supervisor package, README) that reproduces Figure 3 **must** carry the qualifier:

> Conceptual schematic of the intended ReMedFiLM FULL inference design. The frozen implementation is a cached-candidate replay harness, not a deployable end-to-end online pipeline; see the divergence register.

Figure 3 must never be used to support a claim of online deployability, real-time clinical readiness, or verified end-to-end dataflow.

## 6. Non-actions

No model was trained, no inference was run, no checkpoint was read or written, and no TEST1683 image, mask or manifest was opened in producing or documenting this figure.