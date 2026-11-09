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
