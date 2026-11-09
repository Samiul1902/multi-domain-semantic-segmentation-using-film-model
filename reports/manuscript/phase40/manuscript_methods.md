# Methods

## Final frozen system (RA-MedFiLM-BARR), A8/C9

The final system is a frozen four-component conditional-refinement pipeline. No component was trained,
selected, or tuned in Phase40 (scientific_delta = 0).

| Component | Class | Parameters | Role |
|---|---|---|---|
| G | GlobalMedFiLM | 3,523,001 | global segmenter (always executed) |
| B_phi | BARRBenefitRouterV1 | 36,801 | learned benefit router (pre-gate, always executed) |
| R_psi | BARRRegionalRefinerV1 | 1,276,401 | regional refiner (EXECUTE branch only) |
| S_omega | BARRPostSafetyV1 | 1,217 | post-safety accept/reject (EXECUTE branch only) |
| — | assembly wrapper | 0 trainable | assembly only |

Total parameters: **4,837,420** (wrapper trainable parameters: 0).

## Task identity and segmentation semantics

Four domains with frozen task IDs: task 0 = ISIC, task 1 = BUSI, task 2 = KVASIR, task 3 = KUB. All tasks are
binary foreground/background segmentation. KUB subgroups (Kidney_Stone, Bladder_Stone, Ureteric_Stone) are
REPORTING-ONLY metadata and are never segmentation classes, task IDs, model inputs, routing inputs, or
conditioning variables.

## Global stage (G)

Global GPU inference: input [3, 512, 512]; CUDA required; fp32 model/input; autocast fp16 enabled; `torch.no_grad()`;
`inference_mode` off; domain-local contiguous batches of 8; canonical probability operator `sigmoid(logits.float())`.
FiLM task conditioning is applied via the task-ID embedding. Final scoring uses the frozen D75/POLICY_B representation
(live float32 -> persisted float16 -> scored float32 -> threshold >= 0.50).

## ROI proposal

A region-of-interest is proposed from the global probability with p_global threshold 0.30, fractional margin 0.25,
and a 1.5x expansion, rasterised on a 512 canvas with a 256 crop. An empty ROI yields ACTION_UNAVAILABLE -> FORCED_SKIP
(no router/refiner/safety execution).

## Learned routing (B_phi), refinement (R_psi), post-safety (S_omega)

A canonical 202-D feature vector is assembled from G feature taps, the global probability, and the ROI geometry. The
benefit router B_phi consumes the 202-D vector and a task embedding and produces a canonical utility whose comparison
against the frozen tau (TAU_C8_FINAL_FLOAT) yields EXECUTE (score >= tau) or SKIP. On EXECUTE, R_psi refines the
regional crop (RGB crop + global-probability channel) and S_omega then accepts or rejects the refinement at
threshold 0.50.

## Fusion and state machine

Accepted refinements are fused by the canonical D61 pad-aware `fuse_full_field(p_global, refined, geom)`. The pipeline
emits exactly one of four states: FORCED_SKIP, SKIP_GLOBAL, EXECUTE_THEN_ACCEPT, EXECUTE_THEN_REJECT. Metrics use the
canonical scorer (Dice; HD95 boundary; IoU secondary).

## Phase39 (TEST) execution scope

The frozen scripted Phase39 protocol prespecified a comparison of the final system against the frozen global reference
`C-gGLOBAL` (macro-domain Dice difference; CI; per-domain harm rules). See Results R12 and Limitations.
