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
