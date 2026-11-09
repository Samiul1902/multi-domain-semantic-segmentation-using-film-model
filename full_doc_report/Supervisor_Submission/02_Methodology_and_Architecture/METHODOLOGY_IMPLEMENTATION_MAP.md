# Methodology ↔ Implementation Map

Every node in `assets/figures/remedfilm_full_methodology.svg` is traced to real
code here. If an operation could not be verified in the source, it was removed
from the diagram.

**Verified parameter budget**

| Symbol | Class | Source | Parameters | Checkpoint SHA-256 (prefix) |
|---|---|---|---|---|
| G | `GlobalMedFiLM` | `src/models/film/global_medfilm.py` | 3,523,001 | `286689fd…` |
| R_psi | `BARRRegionalRefinerV1` | `src/models/barr/regional_refiner.py` | 1,276,401 | `6d28608a…` |
| B_phi | `BARRBenefitRouterV1` | `src/models/barr/phase25_models.py` | 36,801 | `8a412b2f…` |
| S_omega | `BARRPostSafetyV1` | `src/models/barr/phase25_models.py` | 1,217 | `eee9b97b…` |
| **FULL** | `RAMedFiLMBARR` (wrapper, **0 own parameters**) | `src/models/barr/ra_medfilm_barr.py` | **4,837,420** | assembled |

`RAMedFiLMBARR` adds no parameters of its own — it holds four frozen modules.
Parameter counts were re-derived by loading each checkpoint and summing
`model_state` (see `full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json`).

---

## Panel A — Multi-domain inputs and task conditioning

| Node | Code | Detail |
|---|---|---|
| `x` image | `RAMedFiLMBARR.forward_inference(image, task_id, …)` | `image` is `[1, C, H, W]`, already preprocessed to 512×512 |
| task id `t` | same signature | `task_id ∈ {0: ISIC, 1: BUSI, 2: KVASIR, 3: KUB}` |
| `E(t)` | `GlobalMedFiLM` task embedding | `nn.Embedding(task_count, 32)`; FiLM hidden dim 64 |
| four modalities | `manifests/phase4_v3/{train,val}.csv` | one shared network, four binary foreground tasks |

**Task conditioning enters only through the embedding and the FiLM sites.** No
dataset-specific head exists; there is one shared 1×1 foreground head.

---

## Panel B — FULL inference system

### G — task-conditioned global backbone

| Property | Verified value |
|---|---|
| Class | `GlobalMedFiLM` |
| FiLM sites (5) | `bridge`, `decoder4`, `decoder3`, `decoder2`, `decoder1` |
| FiLM equation | `F_hat = (1 + γ(t)) · F + β(t)` with `γ = tanh(γ_raw)`, `β = tanh(β_raw)` |
| Output projection | zero-initialised → every site starts as identity |
| Outputs | `P_g` foreground probability `[1,1,512,512]`; `F_g` decoder features |

### ROI proposal

| Property | Verified value |
|---|---|
| Module | `src/data/barr_roi.py` |
| Threshold | `ROI_PROPOSAL_THRESHOLD = 0.30` |
| Window | `RAMedFiLMBARR._roi_window_from_probability(...)` |
| Output | candidate region(s) + the cropped ROI fed to R_psi |

`SEGMENTATION_OUTPUT_THRESHOLD = 0.50` is the *final mask* threshold and is a
different quantity from the ROI proposal threshold.

### B_phi — benefit router

| Property | Verified value |
|---|---|
| Class | `BARRBenefitRouterV1` (`phase25_models.py:52`) |
| Input | 202 GT-free numeric features + 32-D task embedding = `ROUTER_TOTAL_DIM = 218` |
| Architecture | `Linear(218,128) → LN → SiLU → Drop(0.10) → Linear(128,64) → LN → SiLU → Drop → Linear(64,1)` |
| Output | one raw scalar per candidate (no activation) |
| Decision | `canonical_utility(Δ̂) = Δ̂ − λ·C`; `router_decision(Δ̂)` returns `EXECUTE` iff utility ≥ `TAU_C8_FINAL_FLOAT` |
| Frozen threshold | `τ_C8 = −0.024358327623641256` |
| GT usage | **none** — the router consumes only ground-truth-free features |

On VAL808 with `τ_C8` this selects **279 / 808** cases.

### R_psi — regional residual refiner

| Property | Verified value |
|---|---|
| Class | `BARRRegionalRefinerV1` (`regional_refiner.py:121`) |
| Input channels | **4** = `[R, G, B, p_global_crop]` |
| Channel schedule | `(16, 32, 64, 96, 128)` |
| Output | single-channel residual/logit for the crop → `ΔP` |
| Trained on | ROI crops from frozen G (3 cross-fitted folds + final refit) |

### S_omega — post-safety gate

| Property | Verified value |
|---|---|
| Class | `BARRPostSafetyV1` (`phase25_models.py:96`) |
| Input dim | `SAFETY_FEATURE_DIM = 20` |
| Architecture | `Linear(20,32) → SiLU → Linear(32,16) → SiLU → Linear(16,1)` |
| Output | one **raw logit**; the sigmoid belongs to the caller's threshold rule |
| Role | veto a refined candidate before it can reach the final mask |

### Composition and final output

| Property | Verified value |
|---|---|
| Composition | `RAMedFiLMBARR._fuse_global_with_regional(p_global, p_refined_crop, …)` |
| Final mask | thresholded at `SEGMENTATION_OUTPUT_THRESHOLD = 0.50` |
| Return | `forward_inference(...) -> Dict[str, Any]` including `final_prob`, state, counters |

### The three outcome branches (all verified)

| Branch | Condition | Result |
|---|---|---|
| (a) SKIP | `router_decision == "SKIP"` (no valid ROI) | final = `P_g`, refiner **never executed** |
| (b) REFINE + ACCEPT | `EXECUTE` and safety accepts | refined ROI composed into `P_g` |
| (c) REFINE + REJECT | `EXECUTE` and safety vetoes | fall back to `P_g` |

VAL808 counts: 529 skip · 266 accept · 13 reject (n = 808).

---

## Panel C — Staged training

| Step | What actually happened | Evidence |
|---|---|---|
| 1 Train G | TRAIN5832, VAL808 selection, 81 epochs, best 66, early stopping patience 15 | `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/closure.json` |
| 2 Predict + propose | frozen G generates `P_g` and ROI candidates | `experiments/phase25a_*/fold*/history.csv` |
| 3 Train R_psi | ROI crops, 3 cross-fitted folds + final refit (25 epochs) | `experiments/phase25a_barr_regional_refiner_v1_1_roi030/` |
| 4 Gain labels | `g = M(P_refined) − M(P_g)` out-of-fold | `reports/tables/phase25c_*` |
| 5 Train B_phi | GT-free features, 5 CV folds + final (80 epochs) | `experiments/phase25d_barr_benefit_router_v1_2_1_seed42/` |
| 6 Train S_omega | routed candidates, 5 CV folds + final (23 epochs) | `experiments/phase25f_barr_post_safety_v1_0_seed42/` |

**This is sequential staged training, not joint end-to-end training.** Each
downstream module consumed a *frozen* upstream output. The diagram therefore
shows training dependencies as dashed links and never depicts a single
backpropagation path through all four modules.

---

## Naming inconsistencies found

The repository uses more than one convention for the same objects. This table is
the single authoritative mapping.

| Concept | Canonical (used here) | Also appears as | Where |
|---|---|---|---|
| Regional refiner | `R_psi` | `R_ρ`, `R_psi`, "regional refiner" | user infographic uses `R_ρ`; repo code/CSV use `R_psi` |
| Benefit router | `B_phi` | `B_φ` | infographic `B_φ`, repo `B_phi` |
| Post-safety gate | `S_omega` | `S_ω` | infographic `S_ω`, repo `S_omega` |
| Full system | `ReMedFiLM` / `FULL RA-MedFiLM-BARR` | `RA-MedFiLM-BARR`, `ReMedFiLM FULL` | reports, code |
| Backbone | `GlobalMedFiLM` | `G`, `Global MedFiLM` | code, tables |
| Project title | `RA-MedFiLM-Seg++` (legacy README) | `ReMedFiLM` (current) | `docs/archive/README_legacy_2026-11-08.md` |

### One genuine code defect (cosmetic, fail-closed)

`RAMedFiLMBARR.forward_inference` names a parameter `safety_post_features_16`,
but `SAFETY_FEATURE_DIM = 20` and `BARRPostSafetyV1` expects 20 inputs. Passing
16 features raises a shape error at the `Linear(20,32)` layer — it fails closed,
so this is a **naming defect, not a silent correctness bug**. It is recorded
here rather than "fixed", because changing the frozen wrapper signature is out
of scope for a documentation task.

`router_features_202` is correctly named: it is the 202 numeric features, and the
32-D task embedding is concatenated inside the model to reach `ROUTER_TOTAL_DIM = 218`.

---

## What the diagram deliberately does **not** show

| Omitted | Why |
|---|---|
| Ground-truth masks at inference | GT is never an inference input; it appears only in training (Panel C step 4) |
| Joint end-to-end backpropagation | Not implemented |
| Loss equations | The implementation uses BCE+Dice for G and component-specific losses; no single unified objective exists to draw |
| Deployment/clinical path | No clinical validation exists |
| C1/C2/C3 experiments | Not executed — see `PENDING_CONTROLLED_EXPERIMENTS.md` |
