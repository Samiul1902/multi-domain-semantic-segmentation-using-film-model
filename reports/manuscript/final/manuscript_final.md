# RA-MedFiLM-BARR: A Conditional Regional-Refinement Pipeline for Multi-Domain Medical Image Segmentation

## Abstract

**Background.** Multi-domain medical image segmentation is usually served by a single global model.
Conditional regional refinement can preserve global performance while improving selected cases, but
only if the decision to refine is made before the expensive computation and is governed by a
preservation constraint.

**Method.** We present RA-MedFiLM-BARR (system A8/C9): a frozen four-component pipeline that couples
a global FiLM-conditioned segmenter (GlobalMedFiLM, G) with a learned benefit router
(BARRBenefitRouterV1, B_phi), an on-demand regional refiner (BARRRegionalRefinerV1, R_psi), and a
post-safety accept/reject stage (BARRPostSafetyV1, S_omega), assembled by a pad-aware fusion with a
four-state decision machine and a preserved-output fallback.

**Frozen development and holdout evidence.** On the development set (VAL808, n=808) the system
preserved macro-domain Dice relative to the global reference (difference 0.002210, 95% bootstrap CI
[0.001133, 0.003298]). On a one-shot held-out evaluation (ROUTER_HOLDOUT, n=875) it was
non-inferior to the global reference (difference 0.001739, 95% CI [0.001117, 0.002405]) under a
disclosed post-first-open scientific source-freeze protocol deviation.

**Descriptive test performance.** The frozen system was subsequently evaluated descriptively on all
1,683 TEST cases; the descriptive macro-domain Dice was 0.83144. This is descriptive final-system
performance, not a comparative endpoint.

**Conclusion.** The architecture and its development and holdout evidence are reported with the full
protocol history disclosed. The prespecified comparative TEST endpoint against the global reference
was not produced; we make no claim of TEST superiority, non-inferiority, preservation, or
harm-free refinement, and this work must not be represented as an untouched one-shot TEST result.

## 1. Introduction

Medical image segmentation models are typically deployed as a single global network that processes
every input at a fixed cost. For multi-domain clinical use, an alternative is to keep a strong global
segmenter and add a conditional regional refinement that runs only when it is expected to help. The
difficulty is that the decision to refine must be made *before* the refinement is computed, must be
learned from paired outcomes, and must be constrained so that global performance is preserved.

We present RA-MedFiLM-BARR (system A8/C9), a frozen conditional-refinement pipeline for multi-domain
binary medical segmentation. The contribution is separated into method novelty, empirical support, and
limitations.

**Method novelty.** The defensible novelty is at the level of the *system integration*, not the
individual mechanisms, which are established prior art. Specifically, the integration combines: (i) a
pre-execution, learned regression of the paired ground-truth-derived Dice gain of an *optional*
regional refinement, used as an execute/skip gate; (ii) a post-safety accept/reject stage with a
preserved-output fallback; and (iii) this combination applied to multi-domain medical binary
segmentation under an explicit preservation constraint. We do not claim novelty for the gate concept,
the paired-gain target formulation, conditional compute, or multi-domain segmentation individually.

**Empirical support (frozen, descriptive).** Multi-domain development preservation (Phase27); a
13-arm module ablation including a reported negative result (Phase28); three-seed reproducibility
(Phase29); the one-shot ROUTER_HOLDOUT evaluation with its qualifier (Phase30); descriptive statistical
governance (Phase31); an external-cohort eligibility negative result (Phase32); a failure analysis
(Phase33); an efficiency profile (Phase34); descriptive mechanism evidence (Phase35); and synthetic
robustness studies (Phase36).

**Limitations.** The frozen Phase39 TEST primary comparative endpoint against the global reference was
not produced and is disclosed as a principal limitation (Section 6). No claim of TEST-confirmed
comparative benefit is made.

## 2. Related Work

The idea of spending computation only when it is expected to improve a decision originates in
metareasoning, where a computation is executed only if its expected value exceeds its cost
[russell1991metareasoning], and is formalised for adaptive inference by the theory of achievable
performance-preserving efficiency gains [hor2024adaptiveinference]. Learned, differentiable allocation
of computation with an explicit cost penalty appears in adaptive computation time [graves2016act].

The architectural pattern of a cheap stage gating an expensive one is canonical: boosted cascades
reject easy cases early [viola2001cascade], optimal pass-on criteria decide whether to escalate to a
more expensive cascade stage [latotzke2021cascade], and region proposals gate an expensive
per-region head [ren2015fasterrcnn]. Learned per-input execute/skip of computation appears in SkipNet
[wang2018skipnet] and mixture-of-depths routing [raposo2024mod], and modality-specific mixture-of-experts
routing in medical segmentation is occupied by M4oE [jiang2024m4oe].

Our decision target is a paired difference of outcomes under two conditions, estimated per unit before
deciding, which is the standard causal-inference structure of conditional average treatment effects
[kunzel2019metalearners]. The closest general formulation is learning to defer to a costlier expert
with an explicit cost and a preservation structure [mozannar2020defer], and its dense medical
segmentation analogue routes to a human expert before finalising [tian2026deferredseg].

Within segmentation, unconditional refinement primitives are established [wang2023segrefiner], and the
always-run coarse-to-fine cascade is the canonical baseline [isensee2021nnunet]. The single closest
functional analogue judges whether a refinement was worth it *after* running it and may revert, so it
saves no compute [moon2024jfs]; acting on the region that provides the most gain is also explored for
cropping in vision-language models [zhao2026lfpc], and regional zoom/refinement for small structures
is prior art [bouzid2023scaleaware, chou2024tinylessurvey]. In medical imaging, deciding compute
allocation *before* running the model is occupied by Med-DANet and Med-DANet V2, which select a crop
and a quantization level rather than a refinement gain [shen2022meddanet, shen2024meddanetv2], and by
adaptive patching that allocates attention by image detail [zhang2024adaptivepatching].

A shared multi-domain medical segmentor is not a novel component, as shown by universal few-shot
segmentation [butoi2023universeg] and promptable universal medical segmentation [ma2024medsam].
Ground-truth-free estimation of the quality of a *current* prediction is solved [laves2018qualitypred,
borges2024sdc, huang2024evanyseg], and is distinct from predicting the gain of a *future* action.
Rejection and abstention mechanisms preserve reliability at the pixel or decision level
[sanisoglu2026abstain, chow1970reject], and conformal methods control the risk of a single output
[tan2026cls]; none of these bounds the gain of an optional refinement. Device-aware lightweight
segmentation is likewise crowded [zhang2023mobilesam].

In summary, the mechanism level is occupied; the defensible novelty is the specific integration of a
pre-execution, learned, ground-truth-derived paired-Dice-gain gate for an optional regional refinement
with a post-safety accept/reject and a preserved-output fallback, applied to multi-domain medical
binary segmentation.

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

## 4. Results

All values are frozen; no new computation was performed in the release. Every number maps to a frozen
artifact (see final_number_provenance.json).

**R1. Development multi-domain performance (VAL808, n=808; Phase27).** The macro-domain Dice
difference of the final system versus the global reference was 0.002210 (95% bootstrap CI
[0.001133, 0.003298]). Per-domain point differences were BUSI 0.000091, ISIC 0.000891, KUB 0.007454,
and KVASIR 0.000404. No domain harm flag was raised.

**R2. Module contribution / ablation (ROUTER_DEVELOPMENT, n=4957, K=1239; Phase28).** Across 13 arms,
the A8/C9 routing-plus-post-safety policy achieved a mean routed true DeltaDice of 0.007516 (benefit
capture 0.597; harmful-activation share 0.324). The F1 integrated refiner did *not* improve the
pipeline (negative result; mean -0.000433). No deployment winner was selected.

**R3. Reproducibility (seeds 42/123/3407; Phase29).** The policy reproduced descriptively and
sign-consistently: the ROUTER_DEVELOPMENT macro DeltaDice three-seed mean was 0.001215 and the VAL808
three-seed mean was 0.002822 (all seeds positive). There was no numeric pass/fail gate and no
best-seed selection.

**R4. One-shot ROUTER_HOLDOUT evidence (n=875; Phase30).** The final-system macro Dice was 0.930287
versus 0.928548 for the global reference, a macro DeltaDice of 0.001739 (95% domain-stratified
bootstrap CI [0.001117, 0.002405]). **Mandatory qualifier:** ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION.

**R5. Statistical / governance evidence (Phase31).** No new confirmatory significance procedure is
eligible; the statistical evidence is descriptive.

**R6. Failure modes (ROUTER_HOLDOUT, n=875; Phase33).** LOW_OVERLAP accounted for 10.06% of samples;
harmful router activation occurred in 12.92% of the 240 EXECUTE rows; missed-benefit and
empty-prediction counts were 0; and execute-then-reject occurred in 1.67%.

**R7. Efficiency (Phase34).** The A8/C9 expected analytical MAC lower bound was 3.244e10 (ratio 1.028
versus global-only; a saving of 2.345e9 MACs versus always-refine). Measured hardware-specific latency
on an RTX 3060 Ti was 15.72 ms (SKIP), 18.89 ms (EXECUTE), and 16.59 ms (weighted). These are not
end-to-end pipeline latencies.

**R8. Interpretability (Phase35).** Descriptive model-mechanism evidence indicated task-modulated FiLM
parameters and router attribution concentrated on decoder1 feature groups. No causal claims are made.

**R9. Image robustness (VAL808; Phase36).** 12,928 synthetic image-perturbation paired rows were
emitted across 16 conditions and 4 domains; the clean G reproduction was bit-identical and the clean
equivalence check passed for all.

**R10. Proposal robustness (VAL808; Phase36).** 4,848 synthetic proposal-perturbation paired rows were
emitted across 6 conditions.

**R11. KUB reporting-only subgroup observations (Phase36).** Reported as metadata only.

**R12. Descriptive final TEST performance (TEST, n=1683; Phase39).** RA-MedFiLM-BARR was evaluated
descriptively on all 1,683 TEST samples, with no post-hoc sample exclusion. Descriptive final-system
Dice by domain was: ISIC n=735, mean 0.88693; BUSI n=174, mean 0.85042; KVASIR n=216, mean 0.85071;
KUB n=558, mean 0.73769. The descriptive macro-domain Dice was 0.8314368385956257.

**R12a. What was successfully observed (TEST).** All 1,683 TEST samples were evaluated and descriptive
final-system segmentation performance was obtained.

**R12b. What was NOT established (TEST).** The frozen protocol's comparative quantities against
C-gGLOBAL were not produced: the global-reference TEST Dice, the paired and macro DeltaDice, the
comparative confidence interval, the per-domain harm-gate decision, and the frozen primary comparative
decision are all **NOT PRODUCED BY THE FROZEN PHASE39 EXECUTION**. They are not derivable without new
TEST inference, and none was performed. **Evidence class:** POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES.

## 5. Discussion

The central contribution described here is the specification and frozen evaluation of a conditional
regional-refinement architecture for multi-domain medical segmentation. Its supporting empirical
evidence is drawn from frozen development-set analyses (Phase27), a comprehensive ablation (Phase28),
three-seed reproducibility (Phase29), the one-shot ROUTER_HOLDOUT evaluation (Phase30), a failure
analysis (Phase33), an efficiency profile (Phase34), descriptive mechanism evidence (Phase35), and
synthetic robustness studies (Phase36).

Domain variability was observed across the development analyses, with larger final-versus-global
differences on KUB and the highest failure prevalence on KUB. Robustness to synthetic image
perturbations was characterised, with the KUB domain showing the largest worst-case sensitivity. The
efficiency characterisation indicates a modest analytical compute reduction under the conditional
policy. The mechanism evidence indicates task-modulated FiLM parameters and router attribution
concentrated on decoder1 feature groups.

The descriptive TEST evaluation provides an indication of final-system segmentation performance on
1,683 held-out samples. It is descriptive only and must not be reinterpreted as evidence of
comparative benefit: the frozen primary comparative endpoint against C-gGLOBAL was not produced, so no
TEST superiority, non-inferiority, preservation, or harm-free conclusion is asserted.

## 6. Limitations

**Protocol limitations.** The original Phase39 one-shot TEST protocol was not completed as intended.
Two pre-outcome technical attempts were consumed before a post-protocol technical-recovery execution
successfully evaluated the frozen system on all 1,683 TEST samples. No TEST image, label, prediction,
metric, or scientific outcome had been observed before the recovery amendment. The successful recovery
produced descriptive final-system segmentation performance but did not emit the prespecified C-gGLOBAL
comparative quantities required to evaluate the frozen macro-domain Dice-difference endpoint and the
associated per-domain harm rules. We therefore do not claim TEST-confirmed superiority, non-inferiority,
preservation, or harm-free refinement, and no additional TEST inference was performed to reconstruct the
missing endpoint.

**Evidence limitations.** The one-shot ROUTER_HOLDOUT result (Phase30) carries a disclosed
post-first-open scientific source-freeze protocol deviation: ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION. No prospective clean external
cohort was eligible (Phase32), so external validation was not performed. The statistical evidence is
descriptive only (Phase31). Efficiency results are hardware-specific (RTX 3060 Ti) analytical and
measured estimates, not end-to-end pipeline latency. Interpretability results are descriptive
model-mechanism evidence, not causal claims. Robustness results are on synthetic perturbations of the
development set, not real-world acquisition shift. KUB subgroups are REPORTING-ONLY metadata.

**Phase39 evidence class.** POST_PROTOCOL_TECHNICAL_RECOVERY_TEST_RESULT_WITH_TWO_DISCLOSED_PREOUTCOME_TECHNICAL_FAILURES.

# References

[russell1991metareasoning] Russell, S.; Wefald, E. (1991). Principles of Metareasoning. Artificial Intelligence 49(1-3). 10.1016/0004-3702(91)90015-C

[hor2024adaptiveinference] Hor, S.; Qian, Y.; Pilanci, M.; Arbabian, A. (2024). Adaptive Inference: Theoretical Limits and Unexplored Opportunities. arXiv preprint (cs.LG). 10.48550/arXiv.2402.04359

[graves2016act] Graves, A. (2016). Adaptive Computation Time for Recurrent Neural Networks. arXiv preprint. 10.48550/arXiv.1603.08983

[viola2001cascade] Viola, P.; Jones, M. (2001). Rapid Object Detection Using a Boosted Cascade of Simple Features. CVPR 2001. 10.1109/CVPR.2001.990517

[latotzke2021cascade] Latotzke, C.; Loh, J.; Gemmeke, T. (2021). Cascaded Classifier for Pareto-Optimal Accuracy-Cost Trade-Off Using off-the-Shelf ANNs. LOD 2021 (Springer LNCS). 10.1007/978-3-030-95470-3_32

[ren2015fasterrcnn] Ren, S.; He, K.; Girshick, R.; Sun, J. (2015). Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks. NeurIPS 2015. 10.48550/arXiv.1506.01497

[wang2018skipnet] Wang, X.; Yu, F.; Dou, Z.-Y.; Darrell, T.; Gonzalez, J. E. (2018). SkipNet: Learning Dynamic Routing in Convolutional Networks. ECCV 2018. 10.48550/arXiv.1711.09485

[raposo2024mod] Raposo, D.; Ritter, S.; Richards, B.; Lillicrap, T.; Humphreys, P. C.; Santoro, A. (2024). Mixture-of-Depths: Dynamically Allocating Compute in Transformer-Based Language Models. arXiv preprint. 10.48550/arXiv.2404.02258

[jiang2024m4oe] Jiang, Y.; Shen, Y. (2024). M4oE: A Foundation Model for Medical Multimodal Image Segmentation with Mixture of Experts. MICCAI 2024 (arXiv:2405.09446). 10.48550/arXiv.2405.09446

[kunzel2019metalearners] Kunzel, S. R.; Sekhon, J. S.; Bickel, P. J.; Yu, B. (2019). Metalearners for Estimating Heterogeneous Treatment Effects Using Machine Learning. PNAS 116(10). 10.1073/pnas.1804597116

[mozannar2020defer] Mozannar, H.; Sontag, D. (2020). Consistent Estimators for Learning to Defer to an Expert. ICML 2020. https://proceedings.mlr.press/v119/mozannar20b.html

[tian2026deferredseg] Tian, Z.; Sun, Y.; Wang, Y.; Shi, Y.; Yin, Y. (2026). DeferredSeg: A Multi-Expert Deferral Framework for Medical Image Segmentation. Pattern Recognition (arXiv:2604.12411). 10.48550/arXiv.2604.12411

[wang2023segrefiner] Wang, M.; Ding, H.; Wang, M.; et al. (2023). SegRefiner: Towards Model-Agnostic Segmentation Refinement with Discrete Diffusion Process. NeurIPS 2023. 10.48550/arXiv.2312.12425

[isensee2021nnunet] Isensee, F.; Jaeger, P. F.; Kohl, S. A. A.; Petersen, J.; Maier-Hein, K. H. (2021). nnU-Net: a self-configuring method for deep learning-based biomedical image segmentation. Nature Methods 18:203-211. 10.1038/s41592-020-01008-z

[moon2024jfs] Moon, S.; Liu, Q. (T.); Kong, H.; Khan, M. H. (2024). Judging from Support-set: A New Way to Utilize Few-Shot Segmentation for Segmentation Refinement Process. ICIP 2025 (arXiv:2407.04519). 10.48550/arXiv.2407.04519

[zhao2026lfpc] Zhao, X.; Tan, Z.; Sheng, D.; Chen, T.; Liu, Y.; Wu, Y.; Gong, T.; Chu, Q.; Yu, N. (2026). Learning to Focus and Precise Cropping: A Reinforcement Learning Framework with Information Gaps and Grounding Loss for MLLMs. CVPR 2026 (arXiv:2603.27494). 10.48550/arXiv.2603.27494

[bouzid2023scaleaware] (arXiv:2305.19063, scale-aware SR for lesions) (2023). Scale-aware Super-resolution Network with Dual Affinity learning for lesion segmentation. arXiv preprint. 10.48550/arXiv.2305.19063

[chou2024tinylessurvey] Chou, P.-H.; et al. (2024). From single to universal: tiny lesion detection in medical imaging. Artificial Intelligence Review 57. 10.1007/s10462-024-10762-x

[shen2022meddanet] Shen, H.; Zhang, Y.; Wang, W.; Chen, C.; Liu, J.; Song, S.; Li, J. (2022). Med-DANet: Dynamic Architecture Network for Efficient Medical Volumetric Segmentation. ECCV 2022 (Springer LNCS). 10.1007/978-3-031-19803-8_30

[shen2024meddanetv2] Shen, H.; Zhang, Y.; Wang, W.; Chen, C.; Liu, J.; Song, S.; Li, J. (2024). Med-DANet V2: A Flexible Dynamic Architecture for Efficient Medical Volumetric Segmentation. WACV 2024, pp. 7871-7881. https://openaccess.thecvf.com/content/WACV2024/html/Shen_Med-DANet_V2_A_Flexible_Dynamic_Architecture_for_Efficient_Medical_Volumetric_WACV_2024_paper.html

[zhang2024adaptivepatching] Zhang, E.; Lyngaas, I.; Chen, Q.; Wang, X.; Igarashi, K.; Huo, Z.; Wahib, M.; Munetomo, M. (2024). Adaptive Patching for High-resolution Image Segmentation with Transformers. arXiv preprint (cs.CV). 10.48550/arXiv.2404.09707

[butoi2023universeg] Butoi, V. I.; Gonzalez Ortiz, J. J.; Ma, T.; Sabuncu, M. R.; Guttag, J.; Dalca, A. V. (2023). UniverSeg: Universal Medical Image Segmentation. ICCV 2023, pp. 21438-21451. 10.1109/ICCV51070.2023.01960

[ma2024medsam] Ma, J.; He, Y.; Li, F.; Han, L.; et al. (2024). Segment Anything in Medical Images. Nature Communications 15:654. 10.1038/s41467-024-44824-z

[laves2018qualitypred] Laves, M.-H.; Ihler, S.; Ortmaier, T. (2018). Real-time Prediction of Segmentation Quality. MICCAI 2018. 10.1007/978-3-030-00937-3_18

[borges2024sdc] Borges, B. L. C.; Pacheco, B. M.; Silva, D. (2024). Soft Dice Confidence: A Near-Optimal Confidence Estimator for Selective Prediction in Semantic Segmentation. Machine Learning (2026) / arXiv:2402.10665. 10.1007/s10994-026-07096-w

[huang2024evanyseg] Huang, S.; et al. (EvanySeg) (2024). Towards Ground-truth-free Evaluation of Any Segmentation in Medical Images. arXiv preprint (eess.IV). 10.48550/arXiv.2409.14874

[sanisoglu2026abstain] Sanisoglu, N.; Navab, N.; Kim, S. T. (2026). Learning to Abstain: Reliable Medical Image Segmentation With Rejection Option. IEEE Access vol. 14, pp. 32655-32665. 10.1109/ACCESS.2026.3669004

[chow1970reject] Chow, C. K. (1970). On Optimum Recognition Error and Reject Tradeoff. IEEE Transactions on Information Theory 16(1). 10.1109/TIT.1970.1054406

[tan2026cls] Tan, B.; et al. (CLS) (2026). Conformal 3D Lesion Segmentation with Balanced Risk Control. Springer LNCS (MICCAI-adjacent). 10.1007/978-3-032-38085-2_11

[zhang2023mobilesam] Zhang, C.; Han, D.; Qiao, Y.; Kim, J. U.; Bae, S.-H.; Lee, S.; Hong, C. S. (2023). Faster Segment Anything: Towards Lightweight SAM for Mobile Applications (MobileSAM). arXiv preprint. 10.48550/arXiv.2306.14289
