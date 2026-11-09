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
