# RA-MedFiLM-BARR — Manuscript (Phase40 assembly, descriptive Phase39 TEST scope)


# Abstract

**Background / motivation.** Multi-domain medical image segmentation often uses a single global model; conditional
regional refinement may preserve global performance while improving selected cases, but demands careful evaluation.

**Method.** We present RA-MedFiLM-BARR (A8/C9): a frozen four-component pipeline combining a global FiLM-conditioned
segmenter (GlobalMedFiLM), a learned benefit router (BARRBenefitRouterV1), a regional refiner (BARRRegionalRefinerV1),
and a post-safety accept/reject stage (BARRPostSafetyV1), with a pad-aware fusion and a four-state decision machine.

**Frozen development / holdout evidence.** On the development set (VAL808) the system preserved macro-domain Dice
(difference 0.002210, 95% CI [0.001133, 0.003298]). On a one-shot held-out evaluation (ROUTER_HOLDOUT, n=875) it was
non-inferior to the global reference (difference 0.001739, 95% CI [0.001117, 0.002405]) under a disclosed source-freeze
protocol deviation.

**Descriptive TEST performance.** The frozen system was subsequently evaluated descriptively on all 1,683 TEST cases;
the descriptive macro-domain Dice was 0.83144. This is descriptive final-system performance, not a comparative endpoint.

**Conclusion.** The architecture and its development/holdout evidence are reported with all protocol history disclosed.
The frozen comparative TEST endpoint against the global reference was not produced; no TEST superiority, non-inferiority,
preservation, or harm-free claim is made. This work must not be represented as an untouched one-shot TEST result.



# Introduction and contributions

**Method contribution (architecture).** RA-MedFiLM-BARR couples a shared global segmenter with a learned benefit
router and an on-demand regional refiner plus a post-safety stage, under an explicit conditional-compute policy and a
four-state decision machine. Contribution is claimed as the specification and evaluation of this frozen conditional
architecture, only where supported by frozen evidence.

**Empirical evidence (frozen).** Multi-domain development preservation (Phase27); a 13-arm module ablation (Phase28,
including a reported negative result for the F1 integrated refiner); three-seed reproducibility (Phase29); the one-shot
ROUTER_HOLDOUT evaluation with its qualifier (Phase30); descriptive statistical governance (Phase31); an external
cohort eligibility negative result (Phase32); a failure analysis (Phase33); an efficiency profile (Phase34);
descriptive mechanism evidence (Phase35); and synthetic robustness studies (Phase36).

**Limitations.** The frozen Phase39 TEST primary comparative endpoint against the global reference was not produced and
is disclosed as a principal limitation. No novelty is claimed merely because a component exists.



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



# Results

Values are frozen; no new computation was performed in Phase40. Every number maps to a frozen artifact
(see manuscript_number_provenance.json).

**R1. Development multi-domain performance (VAL808, n=808; Phase27).** Macro-domain Dice difference of the final
system vs the global reference = 0.002210 (95% bootstrap CI [0.001133, 0.003298]). Per-domain point differences:
BUSI 0.000091, ISIC 0.000891, KUB 0.007454, KVASIR 0.000404. No domain harm flag.

**R2. Module contribution / ablation (ROUTER_DEVELOPMENT, n=4957, K=1239; Phase28).** 13 arms. A8/C9 mean routed true
DeltaDice 0.007516 (benefit capture 0.597, harmful-activation share 0.324). The F1 integrated refiner did **not**
improve the pipeline (negative result; mean -0.000433). No deployment winner was selected.

**R3. Reproducibility (seeds 42/123/3407; Phase29).** Descriptive, sign-consistent: ROUTER_DEVELOPMENT macro DeltaDice
3-seed mean 0.001215; VAL808 three-seed mean 0.002822 (all seeds positive). No numeric pass/fail gate; no best-seed
selection.

**R4. One-shot ROUTER_HOLDOUT evidence (n=875; Phase30).** Final-system macro Dice 0.930287 vs global 0.928548;
macro DeltaDice 0.001739 (95% domain-stratified bootstrap CI [0.001117, 0.002405]). **Mandatory qualifier:**
ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION.

**R5. Statistical / governance evidence (Phase31).** No new confirmatory significance procedure is eligible; the
evidence is descriptive.

**R6. Failure modes (ROUTER_HOLDOUT, n=875; Phase33).** LOW_OVERLAP 10.06%; harmful router activation 12.92% of the
240 EXECUTE rows; missed-benefit 0; empty-prediction 0; execute-then-reject 1.67%.

**R7. Efficiency (Phase34).** A8/C9 expected analytical MAC lower bound 3.244e10 (ratio 1.028 vs global-only; saving
2.345e9 MACs vs always-refine). Measured hardware-specific latency on an RTX 3060 Ti: SKIP 15.72 ms, EXECUTE 18.89 ms,
weighted 16.59 ms. Not an end-to-end pipeline latency.

**R8. Interpretability (Phase35).** Descriptive model-mechanism evidence (FiLM task modulation; router feature-group
attribution). No causal claims.

**R9. Image robustness (VAL808; Phase36).** 12,928 synthetic image-perturbation paired rows across 16 conditions x 4
domains; clean G reproduction bit-identical; clean equivalence all-pass.

**R10. Proposal robustness (VAL808; Phase36).** 4,848 synthetic proposal-perturbation paired rows across 6 conditions.

**R11. KUB reporting-only subgroup observations (Phase36).** Reported as metadata only.

**R12. Descriptive final TEST performance (TEST, n=1683; Phase39).** RA-MedFiLM-BARR was evaluated descriptively on
all 1,683 TEST samples; no post-hoc sample exclusion. Descriptive final-system Dice by domain: ISIC n=735 mean 0.88693;
BUSI n=174 mean 0.85042; KVASIR n=216 mean 0.85071; KUB n=558 mean 0.73769. Descriptive macro-domain Dice
0.8314368385956257.

**R12a. What was successfully observed (TEST).** All 1,683 TEST samples were evaluated and descriptive final-system
segmentation performance was obtained.

**R12b. What was NOT established (TEST).** The frozen protocol's comparative quantities against `C-gGLOBAL` were not
produced: the global-reference TEST Dice, the paired/macro DeltaDice, the comparative confidence interval, the
per-domain harm-gate decision, and the frozen primary comparative decision are all **NOT PRODUCED BY THE FROZEN
PHASE39 EXECUTION**. They are not derivable without new TEST inference, and none was performed. **Evidence class:**
POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES.



# Discussion

The central contribution described here is architectural: a frozen global segmenter augmented with a learned benefit
router, an on-demand regional refiner, and a post-safety accept/reject stage, operating under a conditional-compute
policy. The supporting empirical evidence is drawn from frozen development-set analyses (Phase27), a comprehensive
ablation (Phase28), three-seed reproducibility (Phase29), the one-shot ROUTER_HOLDOUT evaluation (Phase30), a failure
analysis (Phase33), an efficiency profile (Phase34), mechanism evidence (Phase35), and synthetic robustness studies
(Phase36).

Domain variability was observed across development analyses (e.g., larger final-vs-global differences on KUB; the
highest failure prevalence on KUB). Robustness to synthetic image perturbations was characterised; the KUB domain
showed the largest worst-case sensitivity. Efficiency characterisation indicates a modest analytical compute reduction
under the conditional policy. Mechanism evidence indicates task-modulated FiLM parameters and router attribution
concentrated on decoder1 feature groups.

The descriptive TEST evaluation provides an indication of final-system segmentation performance on 1,683 held-out
samples. It is **descriptive only** and must not be reinterpreted as evidence of comparative benefit: the frozen
primary comparative endpoint against C-gGLOBAL was not produced, so no TEST superiority, non-inferiority, preservation,
or harm-free conclusion is asserted.



# Limitations

**Protocol limitations.** The original Phase39 one-shot TEST protocol was not completed as intended. Two pre-outcome
technical attempts were consumed before a post-protocol technical-recovery execution successfully evaluated the frozen
system on all 1,683 TEST samples. No TEST image, label, prediction, metric, or scientific outcome had been observed
before the recovery amendment. The successful recovery produced descriptive final-system segmentation performance but
did not emit the prespecified C-gGLOBAL comparative quantities required to evaluate the frozen macro-domain Dice-
difference endpoint and associated per-domain harm rules. We therefore do not claim TEST-confirmed superiority,
non-inferiority, preservation, or harm-free refinement, and no additional TEST inference was performed to reconstruct
the missing endpoint.

**Evidence limitations.** The one-shot ROUTER_HOLDOUT result (Phase30) carries a disclosed post-first-open scientific
source-freeze protocol deviation: ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION. No prospective clean external cohort was eligible (Phase32); external
validation was not performed. The statistical evidence is descriptive only (Phase31). Efficiency results are
hardware-specific (RTX 3060 Ti) analytical/measured estimates, not end-to-end pipeline latency. Interpretability
results are descriptive model-mechanism evidence, not causal claims. Robustness results are on synthetic perturbations
of the development set, not real-world acquisition shift. KUB subgroups are REPORTING-ONLY metadata.

**Phase39 evidence class.** POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES.
