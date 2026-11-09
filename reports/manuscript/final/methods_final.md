## 3. Methods

### 3.1 Final frozen system

The final system is a frozen four-component conditional-refinement pipeline. No component was trained,
selected, or tuned in the release process (scientific_delta = 0).

| Component | Class | Parameters | Execution role |
|---|---|---|---|
| G | GlobalMedFiLM | 3,523,001 | always executed |
| B_phi | BARRBenefitRouterV1 | 36,801 | pre-gate, always executed |
| R_psi | BARRRegionalRefinerV1 | 1,276,401 | EXECUTE branch only |
| S_omega | BARRPostSafetyV1 | 1,217 | EXECUTE branch only |
| — | assembly wrapper | 0 trainable | assembly only |

The total parameter count is 4,837,420, of which 0 are trainable in the wrapper.

### 3.2 Task identity and segmentation semantics

Four domains carry frozen task IDs: task 0 = ISIC, task 1 = BUSI, task 2 = KVASIR, and task 3 = KUB.
All tasks are binary foreground/background segmentation. The KUB subgroups (Kidney_Stone,
Bladder_Stone, Ureteric_Stone) are REPORTING-ONLY metadata; they are never segmentation classes, task
IDs, model inputs, routing inputs, or conditioning variables.

### 3.3 Global stage (G)

Global GPU inference takes a [3, 512, 512] input on CUDA with fp32 model and input, autocast fp16
enabled, `torch.no_grad()`, and domain-local contiguous batches of 8. FiLM task conditioning is applied
through the task-ID embedding. The canonical probability operator is `sigmoid(logits.float())`, and the
final scoring uses the frozen D75/POLICY_B representation (live float32, persisted float16, scored
float32, threshold >= 0.50).

### 3.4 Region-of-interest proposal

A region of interest is proposed from the global probability with a p_global threshold of 0.30, a
fractional margin of 0.25, and a 1.5x expansion, rasterised on a 512 canvas with a 256 crop. An empty
region yields ACTION_UNAVAILABLE and the FORCED_SKIP state, in which the router, refiner, and safety
stage are not executed.

### 3.5 Routing, refinement, and post-safety

A canonical 202-D feature vector is assembled from G feature taps, the global probability, and the ROI
geometry. The benefit router B_phi consumes this vector and a task embedding and produces a canonical
utility that is compared with the frozen tau (TAU_C8_FINAL_FLOAT) to yield EXECUTE (score >= tau) or
SKIP. On EXECUTE, R_psi refines the regional crop (RGB crop plus the global-probability channel), and
S_omega then accepts or rejects the refinement at threshold 0.50.

### 3.6 Fusion and state machine

Accepted refinements are fused by the canonical D61 pad-aware `fuse_full_field(p_global, refined,
geom)`. The pipeline emits exactly one of four states: FORCED_SKIP, SKIP_GLOBAL, EXECUTE_THEN_ACCEPT,
or EXECUTE_THEN_REJECT. Metrics use the canonical scorer (Dice; HD95 boundary; IoU secondary).

### 3.7 Phase39 (TEST) execution scope

The frozen scripted Phase39 protocol prespecified a comparison of the final system against the frozen
global reference C-gGLOBAL, with a macro-domain Dice-difference primary endpoint, a confidence-interval
decision rule, and per-domain harm rules. See Results (Section 4, R12) and Limitations (Section 6).
