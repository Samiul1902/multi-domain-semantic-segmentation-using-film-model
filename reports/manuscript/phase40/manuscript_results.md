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
