# ReMedFiLM Architecture-to-Code Mapping & Inference Implementation Status

**Model Identity:** ReMedFiLM FULL (RA-MedFiLM-BARR)  
$$\text{ReMedFiLM} = G + B_\phi + R_\psi + S_\omega \quad (4,837,420 \text{ parameters})$$

---

## 1. Actual Repository Implementation Classification: Mode B

### Classification:
**Mode B — Historical Offline / Cached Candidate Replay Harness**

### Technical Evidence (`src/models/barr/ra_medfilm_barr.py`):
In `RAMedFiLMBARR.forward_inference(image, task_id, ...)`:
```python
def forward_inference(self, image: torch.Tensor, task_id: int,
                      router_features_202: Optional[np.ndarray] = None,
                      roi_window: Optional[tuple] = None,
                      action_available: Optional[bool] = None,
                      oof_refined_crop_prob: Optional[np.ndarray] = None,
                      safety_post_features_16: Optional[np.ndarray] = None) -> Dict[str, Any]:
    ...
    # Line 275:
    if router_features_202 is None:
        raise ValueError("router_features_202 is required for the canonical path")
    ...
    # Line 295:
    if oof_refined_crop_prob is None:
        raise ValueError("oof_refined_crop_prob is required on the EXECUTE branch")
    ...
    # Line 305:
    if safety_post_features_16 is None:
        raise ValueError("safety_post_features_16 is required on the EXECUTE branch")
```

### Scientific Implications:
1. **No Standalone Online Refinement Pipeline:** An arbitrary medical image $X$ cannot be passed into `forward_inference(X, task_id)` without externally supplying:
   - 202-dimensional GT-free pre-refinement feature vector (`router_features_202`).
   - 256×256 regional refiner probability crop (`oof_refined_crop_prob`).
   - 16-dimensional post-refinement safety feature vector (`safety_post_features_16`).
2. **Execution Semantics:** The code functions as a **deterministic decision, state-machine verification, and mask-composition engine** that evaluates whether cached out-of-fold refiner outputs should be accepted or rejected in favor of the backbone global fallback.
3. **Manuscript & Thesis Disclosure:** The missing online feature extractors and online crop generator represent an **engineering implementation gap**, not a failure of the mathematical concept. This distinction is transparently disclosed throughout the V9 report.

---

## 2. Component-by-Component Architectural Code Mapping

| Symbol | Mathematical Component | Parameter Count | Source File & Class | Actual Input / Output Semantics |
| :--- | :--- | :--- | :--- | :--- |
| **$G$** | GlobalMedFiLM Backbone | 3,523,001 | `src/models/global_medfilm.py` (`GlobalMedFiLM`) | Input: $1 \times C \times 512 \times 512$ image + 32-D task embedding ($\text{task\_id} \in \{0, 1, 2, 3\}$). Output: $1 \times 1 \times 512 \times 512$ base probability map $P_{\text{global}}$. Five FiLM modulation layers. |
| **ROI** | ROI Proposal & Window Generator | 0 (algorithmic) | `src/models/barr/ra_medfilm_barr.py` (`_roi_window_from_probability`) | Thresholds $P_{\text{global}} \ge 0.10$. Finds largest bounding box, expands by $1.20\times$, clamps to canvas, crops square $256 \times 256$ window. If no foreground, signals `FORCED_SKIP`. |
| **$B_\phi$** | Benefit-Aware Router | 36,801 | `src/models/barr/benefit_router.py` (`BenefitRouter`) | Input: 202-D pre-computed GT-free numeric features + 16-D learned task embedding. Output: scalar predicted Dice improvement $\hat{\Delta}_{\text{Dice}}$. Utility $U = \hat{\Delta}_{\text{Dice}} - \lambda C$. If $U < 0.005$, takes `SKIP_GLOBAL`. |
| **$R_\psi$** | Regional Boundary Refiner | 1,276,401 | `src/models/barr/refiner.py` (`RegionalRefinerUNet`) | Input: $4 \times 256 \times 256$ crop (RGB image + $P_{\text{global}}$ crop). Output: $1 \times 256 \times 256$ refined probability map. *Note: In `forward_inference`, this is provided via cached `oof_refined_crop_prob`.* |
| **$S_\omega$** | Post-Refinement Safety Gate | 1,217 | `src/models/barr/safety_gate.py` (`PostSafetyClassifier`) | Input: 16-D numeric post-candidate features + 4-D task one-hot. Output: scalar logit / acceptance probability $P_{\text{accept}} = \sigma(z)$. If $P_{\text{accept}} \ge 0.50$, accepts candidate; otherwise reverts to $P_{\text{global}}$ fallback (`EXECUTE_THEN_REJECT`). |
| **Fusion**| Canvas Mask Composition | 0 (deterministic) | `src/models/barr/ra_medfilm_barr.py` (`_fuse_global_with_regional`) | Deterministic spatial window replacement of $P_{\text{global}}$ with resized refined crop. No heuristic alpha-blending is used. |

---

## 3. Disclosures for Supervisor and Reviewers
1. The mathematical formulation represents an interactive four-stage clinical decision flow.
2. The empirical results presented on VAL808 ($0.837290$ Dice) are verified from actual frozen out-of-fold prediction masks produced by this staged architecture.
3. Deploying ReMedFiLM into real-time clinical workstations will require connecting the online feature calculation pipelines into a single unified Python wrapper.

---

## 4. Relationship to the report's methodology figures

The V9 report carries **two** methodology figures whose authority is deliberately unequal:

| Report figure | Artifact | Status | Use |
| :--- | :--- | :--- | :--- |
| **Figure 2** | `V9/figures/ReMedFiLM_Methodology_Manuscript.png` | `CODE_VERIFIED` — every arrow checked against source | **Authoritative.** Cite this figure for all architecture claims. |
| **Figure 6** | `V9/figures/ReMedFiLM_V9_Conceptual_Infographic.png` | `CONCEPTUAL_NOT_CODE_VERIFIED` — operator-supplied | **Illustrative only.** Communicates the intended design; not evidence of a working pipeline. |

The infographic's Panel B depicts `R_psi` being invoked online and a `ΔP` additive correction. Neither is implemented: the canonical wrapper never calls the refiner module, and fusion is deterministic window replacement. The section-by-section correspondence, the seven-item divergence register (D1–D7), and the mandatory citation qualifier are recorded in `ReMedFiLM_V9_Methodology_Figure_Provenance.md`.

This mapping is consistent with Section 1 above: the frozen code is a **Mode B** cached-candidate replay harness, and the online candidate-generation path shown in the infographic remains the disclosed engineering gap.
