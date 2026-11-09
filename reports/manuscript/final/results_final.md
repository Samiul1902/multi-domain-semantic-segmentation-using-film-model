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
