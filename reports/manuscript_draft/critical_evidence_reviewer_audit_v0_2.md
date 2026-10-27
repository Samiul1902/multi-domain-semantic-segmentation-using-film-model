# RA-MedFiLM-BARR — Critical Evidence and Reviewer-Risk Audit v0.2

## Scope and verdict

This is a read-only source-inspection audit of `RA_MedFiLM_BARR_manuscript_v0_1.md`, all 22 rows in `claims_to_evidence.md`, the implementation, frozen result artifacts, and later governance corrections. No model import, checkpoint deserialization, training, inference, protected-data access, TEST/ROUTER_HOLDOUT access, bootstrap rerun, outcome join, or new scientific calculation occurred. v0.1 and the claims matrix are unchanged.

**Verdict: not publication-ready as a confirmatory method paper.** The implementation and descriptive development findings are real, but the evidence does not identify causal FiLM benefit, independent BARR mechanism benefit, clinical safety, protocol-faithful superiority, or independent generalization. Numerical agreement with a frozen JSON does not by itself validate the estimand, independence, or provenance.

All **22 claim rows** were reviewed against actual source contents. The matrix mixes proposed positive claim text with negative dispositions; review does not endorse those propositions. **Nine distinct rows are flagged:** eight need qualification/source repair (C-05, C-07, C-08, C-10, C-12, C-14, C-16, C-19), plus C-17, whose independent-backbone wording is false. C-14's definitive-positive wording is also contradicted by its interval. **Thirteen other bounded/negative dispositions are retained.** C-04, C-15, C-20, C-21 and C-22 correctly deny unsupported claims. Neither this count nor a frozen artifact constitutes independent scientific confirmation.

## 1. Severity-ranked discrepancies

| ID | Severity | Affected area | Finding | Required correction |
|---|---|---|---|---|
| D-01 | CRITICAL | Abstract, Methods, Algorithm; C-01/C-10/C-11 | GlobalMedFiLM.forward returns logits, not `(probability, features)`. The wrapper accepts precomputed router features, refined crop probabilities and post-features; its execute branch increments a refiner counter but does not call R_psi. | Describe a staged cross-artifact pipeline, not a validated self-contained wrapper. End-to-end equivalence is EVIDENCE PENDING. |
| D-02 | HIGH | Refiner source; C-07 | `phase25a_final_freeze.json` is the superseded ROI-0.50 run. Canonical authority is `phase25a_canonical_final_freeze.json`; canonical refit is 25 epochs, not old 27. | Cite canonical ROI030 authority and supersession record. |
| D-03 | HIGH | OOF and Results; C-08/C-12 | DEV is a subset of TRAIN. Refiner labels are cross-fitted, but G and cached features are TRAIN-in-sample; Phase25F upstream/downstream OOF is explicitly not fully nested. | Call this module-specific/meta-level development OOF, not independent end-to-end OOF. |
| D-04 | HIGH | A8 counts; C-13/C-14 | A8’s 1,205 is accepted output replacements; R_psi executes on 1,239 and S_omega rejects 34. | Separate selected/executed, accepted, and rejected counts. |
| D-05 | HIGH | A7/A8 interval; C-14 | Table02 means condition on each arm’s applied set; Table08 A8-A7 uses all 4,957 cases with zeros. Its interval is pooled case-level, not equal-domain macro or patient-clustered. | State the estimator and denominator exactly; do not call it a macro interval. |
| D-06 | HIGH | Bootstrap | The table-builder matched loop uses direct case-index resampling with `RandomState(42).randint`; it does not implement KUB patient clustering or equal-domain stratification despite summary prose. | Report a recorded descriptive case bootstrap and provenance conflict; do not recalculate without authorization. |
| D-07 | HIGH | EXT-03; C-19/C-20 | The v1.1 D6 analysis carried forward by v1.2 describes a post-outcome SegFormer-specific learning-rate repair, distinct from the five frozen-vs-executed deviations. | Use v1.2 disposition; classify EXT-03 protocol-divergent context only and keep AS-08 unresolved. |
| D-08 | HIGH | Resource policy; C-10/C-16 | Eligible action cost is constant; C7/A6 and C8/A7 have identical fixed-K membership. The resource term does not change fixed-budget rankings. | Do not claim demonstrated resource benefit from the lambda term. |
| D-09 | MEDIUM | Phase-21; C-05 | Checkpoint-selection macro is 0.8350791259413984; canonical scored macro is 0.8350794169575282. | Separate selection from scoring and disclose VAL consumption. |
| D-10 | MEDIUM | Phase-22; C-06 | Phase-22 uses GT-defined ROI and reruns frozen G on oracle crops; it is not the trained 256 crop refiner and is not an upper bound for every later architecture. | Call it a GT-informed diagnostic only. |
| D-11 | MEDIUM | Harm labels | Phase25C reporting bins (+0.02/-0.01) differ from S_omega’s strict target `delta_dice > 0` and BARR-M1 strict/tolerance harm rules. | Keep reporting categories, model target, and harm denominators distinct. |
| D-12 | MEDIUM | F1; C-16 | F1 primary candidate comparison uses 1,239 common executions; integrated secondary uses frozen S_omega with 1,109 accepts/130 fallbacks. | Keep primary and secondary estimands separate; neither is causal. |

## 2. Claim-by-claim verification

| ID range | Disposition |
|---|---|
| C-01 | Shared backbone, one foreground head and parameter inventory supported as implementation, not outcome attribution. |
| C-02 | 32-D task embedding, five sites, tanh gamma/beta and identity-at-initialization FiLM equation supported as implementation, not a trained-model identity or attribution claim. |
| C-03 | Numeric 64-case task perturbation diagnostic supported; descriptive sensitivity only. |
| C-04 | Correctly NOT_ESTABLISHED; no FiLM-off control and authority forbids causal wording. |
| C-05 | Numeric macro result supported; use canonical scored value, distinguish pooled Dice, and disclose VAL selection/consumption. |
| C-06 | Numeric harm counts/sum supported for VAL808 GT-oracle diagnostic; not deployable or transferable to DEV refiner. |
| C-07 | Architecture/parameter/cost supported only by canonical ROI030 authority, not the old ROI050 freeze cited in v0.1. |
| C-08 | 4,957 cross-fitted refiner-label rows and category counts supported; not fully independent end-to-end labels because G/features are TRAIN-in-sample. |
| C-09 | Router dimensions and OOF metrics supported as DEV target-prediction metrics; no causal or external utility. |
| C-10 | Formula and analytical MAC contract supported; fixed cost makes lambda ranking-redundant at fixed K; no measured latency. |
| C-11 | S_omega architecture/state/fallback supported; no clinical safety and no pre-execution saving. |
| C-12 | Phase25G counts and macro value supported; DEV-selected, in-sample, meta-level OOF only. |
| C-13 | A7/A8 matched design supported; isolates post-safety decision, not clinical safety or full BARR mechanism. |
| C-14 | Numeric interval supported but “positive, definitive” is false; pooled case-bootstrap CI crosses zero. |
| C-15 | Non-identification of A0/A1/A8 router causality supported by audit and erratum. |
| C-16 | 13 arms/18 runs/DEV population supported; not all rows are newly trained or formally paired. |
| C-17 | Claim is false as written; Phase-29 has one fixed G and three downstream stacks. |
| C-18 | Per-seed values supported; descriptive fixed-G result, n=3, no numeric reproducibility gate. |
| C-19 | Protocol-faithful claim unsupported; v1.1 D6 identifies the post-outcome LR intervention and v1.2 retains it while documenting additional provenance defects. |
| C-20 | AS-08 correctly UNRESOLVED. |
| C-21 | Independent generalization/clinical safety correctly NOT_ESTABLISHED. |
| C-22 | BARR-M1 correctly NOT_EXECUTED; RC1 approval false, production inactive, launch order absent. |

## 3. Critical experimental interpretation

### Phase-21

Phase-21 used one seed-42 logical run, selected epoch 66, and VAL808 at threshold 0.50 without TTA/tuning/morphology. Canonical macro Dice is 0.8350794169575282; checkpoint-selection macro is 0.8350791259413984; pooled descriptive Dice is 0.8784243406054913. These are different statistics. VAL was used for selection and later continuity; this is not pristine independent validation. The 64-case task diagnostic does not identify FiLM causality.

### Phase-22

The oracle regional arm uses GT geometry and reruns frozen G on a GT-defined crop. Harm is `oracle_delta_dice < 0`: 536/808, rate 0.663366. `mean_harm` is mean among harmed cases, while `net_gain_executed` is an executed-case delta sum. The result is not the Phase-25 256 crop-trained refiner and cannot be transported to Phase-28 DEV.

### Phase-28

A0 is global-only; A1 always-refine; A6 learned paired-gain routing; A7 adds resource utility; A8 adds S_omega. The only frozen matched contrast is A7/A8. Table02 conditional routed means differ from Phase25G equal-domain macro deltas. A8 selects/executes 1,239, accepts 1,205, rejects 34. A7/A8 Table08 is a pooled all-case zero-fallback contrast, not a macro or patient-cluster interval. F1 has a negative primary candidate comparison and a separate frozen-S_omega integrated secondary analysis. The secondary JSON inconsistently labels A8 membership (1,205) while reporting 1,239 integrated rows. Frozen metadata are not automatically internally consistent, and the secondary comparison should not be treated as fully matched.

### Phase-29

G and cached features are identical across all seeds; only downstream stacks vary. n=3 and two degrees of freedom do not support full-system replication or population uncertainty. VAL808 is disjoint from TRAIN but consumed by prior development/continuity work.

### EXT-03 and BARR-M1

EXT-03 checkpoint hashes are attested, but protocol fidelity is not restored. v1.2 records five deviations plus a post-outcome SegFormer LR repair and provenance defects. Permitted use is disclosed reduced-protocol context; AS-08 remains unresolved. BARR-M1 RC1 is not approved, inactive, and unexecuted; synthetic tests are not scientific results.

## 4. Novelty and contribution audit

| Component | Classification | Evidence status | Defensible claim requirement |
|---|---|---|---|
| GlobalMedFiLM | Implemented architectural element; not established novel | Shared residual encoder-decoder, task embedding, five FiLM sites, one head. | Literature comparison and architecture-matched control for any FiLM-effect claim. |
| Task embedding/FiLM | Implemented element; attribution hypothesis | Task perturbation changes trained-model predictions; no FiLM-off control. | Same-protocol FiLM-off training; result speaks to C1 only. |
| R_psi | Implemented, explicitly non-novel refiner | Canonical ROI030 refiner, 1,276,401 parameters, 256 crop. | Controlled refiner comparison only if refiner design is the question. |
| B_phi | Plausible methodological instantiation; development-supported | 218-D input, paired-gain target, DEV OOF metrics. | Independent calibration/utility and router-off matched controls. |
| Cost routing | Implemented utility; mechanism precedented and fixed-cost redundant at fixed K | `delta_hat-lambda*C`, constant eligible cost. | Literature comparison and variable-cost/non-fixed-budget evidence for resource claims. |
| S_omega | Implemented post-refinement selector; no clinical-safety novelty | 20-D MLP, fixed threshold, A7/A8 inconclusive. | Authorized matched selector study and separate safety endpoint study. |
| Integrated pipeline | Plausible system/integration contribution; descriptive evidence only | Four frozen modules and state-machine contract. | Protocol-faithful comparison, independent validation, mechanism attribution, and end-to-end equivalence. |

The Phase-23 novelty audit classifies benefit-aware pre-execution routing, paired-gain targets, cost-aware gating, and fallback as occupied mechanisms; only a narrow system-integration hypothesis remains. No first-ever claim is justified before literature review.

## 5. Statistical validity audit

ROUTER_DEVELOPMENT (`n=4957`) is a subset of TRAIN. G was trained on the enclosing TRAIN population; the refiner has cross-fitted DEV candidates, and B_phi/S_omega have module-specific OOF predictions plus separate all-DEV final refits. The final refits must not be described as the producers of the OOF development predictions. Operating-point selection and non-nested upstream/downstream folds remain limitations. VAL808 is disjoint from TRAIN but consumed for checkpoint selection and later continuity; it is not pristine independent evaluation.

Table02 conditions on each arm's applied set, whereas Table08 includes all-population fallback zeros. The matched-loop case bootstrap does not implement KUB patient clustering or domain stratification despite its summary label. Available KUB patient IDs do not make an existing case-bootstrap interval cluster-aware; non-KUB patient identifiers are missing. Multiple contrasts are descriptive without multiplicity correction. A7/A8's interval crossing zero is not evidence of equivalence, non-inferiority, clinical safety, or zero effect. The proposed BARR-M1 clustered macro bootstrap has not been executed and cannot repair the existing interval retrospectively.

## 6. Ten most significant reviewer concerns

1. **CRITICAL — Methods:** the wrapper is not a demonstrated self-contained end-to-end model; it accepts precomputed stage inputs. Correct in writing and authorize equivalence validation if needed.
2. **CRITICAL — Results:** principal BARR findings are DEV/in-sample and operating-point selected. Label all as DESCRIPTIVE_DEV.
3. **CRITICAL — Discussion:** no C1 FiLM, C2 mechanism, or C3 baseline control identifies proposed causal claims. New authorized experiments required.
4. **HIGH — A7/A8:** interval crosses zero and is pooled case-bootstrap, not macro/patient-clustered. Correct wording; new clustered analysis only if authorized.
5. **HIGH — OOF:** Phase25F is not fully nested with upstream refined-probability features. Correct evidence class in writing.
6. **HIGH — Counts:** 1,205 accepted is not 1,239 executed. Correct tables/captions in writing.
7. **HIGH — EXT-03:** v1.2 adds post-outcome SegFormer LR repair and provenance defects. Do not call it common frozen protocol.
8. **HIGH — Novelty:** mechanism/paired gain/value-of-computation/fallback are precedented. Remove firstness and complete literature review.
9. **HIGH — Clinical language:** “safety” can imply patient safety despite Dice-only evidence. Use preservation/segmentation-harm language.
10. **HIGH — Reproducibility:** Phase29 varies downstream modules with fixed G and n=3. Report fixed-G downstream observations only.

## 7. Ranked experiment priorities — proposals only

### Priority 1: C1 FiLM attribution

Question: does task-conditioned FiLM change equal-domain macro Dice versus an identical unconditioned backbone? Train an identity-F1 control from scratch under the same protocol, selection rule, data and seeds; do not zero the trained checkpoint. Use TRAIN for fitting and VAL808 for the predeclared comparison, acknowledging VAL selection contamination. Prefer at least three seeds. This settles C1 only. Requires explicit authorization and protocol freeze.

### Priority 2: C2 mechanism attribution

Question: do B_phi and S_omega improve a fixed G+R stack? Use router-off/always-refine, router-only/A7, router+S_omega/A8, and a predeclared resource policy with one-factor contrasts. Use frozen development arrays for descriptive work and an independent eligible cohort for confirmatory work. Report execution, acceptance, rejection, strict/tolerance harm, pooled and macro estimands separately. Requires separate BARR-M2-style approval; Dice cannot support clinical safety.

### Priority 3: C3 / AS-08 protocol-faithful baseline study

Question: how do BARR and named baselines compare under one genuinely frozen protocol? Predeclare optimizer, loss, LR, augmentation, channels, resolution, seeds, selection and metrics; all arms must load the same authority without post-outcome recipe changes. This is a new matrix, provisionally EXT-03B, requiring explicit authorization and compute allocation.

### Priority 4: BARR-M1 descriptive reanalysis

Question: under frozen A0/A1/A8 policy definitions, what are descriptive equal-domain macro Dice and harm contrasts? Use preserved arrays only; no A7, new arms, forward passes, training or threshold changes. Use predeclared KUB clustering. RC1 remains inactive until real supervisor authorization, trusted key/time services, and a separate launch order. Synthetic tests are not scientific outcomes.


## 8. Final audit conclusion

The defensible current paper is an evidence-bound system/integration manuscript with descriptive development results and explicit non-claims. It is not a causal FiLM paper, clinical-safety paper, protocol-faithful benchmark paper, or independent-validation paper. Publication blockers are C1/C2/C3, AS-08, a genuinely independent eligible evaluation population, patient-level dependence limitations, non-nested OOF, incomplete source-checked literature, and end-to-end implementation equivalence. Future evidence remains `EVIDENCE PENDING`; RC1 authorization and launch are separate unresolved gates.

<!-- AUDIT_SOURCE_REGISTER -->
