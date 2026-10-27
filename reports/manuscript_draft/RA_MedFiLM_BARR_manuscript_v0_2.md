# RA-MedFiLM-BARR: Task-Conditioned Global Segmentation with Benefit-Aware Regional Refinement Routing

**Manuscript draft v0.2 — critically audited, evidence-bound working document**  
**Repository:** `D:\Softfors\jup`  
**Status:** manuscript preparation only; publication readiness is not established.

> **Evidence boundary.** This draft uses recorded implementation, protocol, audit, and result artifacts. It does not report new training, inference, TEST access, ROUTER_HOLDOUT access, or protected-data access. Quantitative statements are tied to `reports/manuscript_draft/claims_to_evidence.md` using claim identifiers C-01–C-22. `FROZEN_AUTHORITY` identifies binding architecture/protocol/scope records; `EXECUTED_DESCRIPTIVE` identifies completed measurements whose population and estimand are stated; `EXPLORATORY`, `PROSPECTIVE`, `UNRESOLVED`, and `SUPERSEDED` are retained as evidence classes.

## Abstract

### Background
Medical-image segmentation across heterogeneous domains may benefit from a shared global representation and local high-resolution processing. However, regional refinement is not uniformly beneficial. In a frozen Phase-22 diagnostic analysis, a ground-truth-defined oracle regional arm reduced Dice for 536 of 808 validation cases and produced a negative net executed Dice change. This is a GT-informed diagnostic, not a deployable policy or a mathematical upper bound for other refiner architectures. It motivates examining selective refinement without demonstrating that a learned policy will help.

### Objective
This manuscript documents RA-MedFiLM-BARR (Resource-Aware MedFiLM with Benefit-Aware Refinement Routing), a shared multi-domain segmentation system combining GlobalMedFiLM with optional regional refinement. The objective is to describe the implemented system and organize existing evidence, not to assert clinical efficacy, causal mechanism, or publication readiness.

### Methods
GlobalMedFiLM is a shared residual encoder-decoder with a 32-dimensional task embedding and five FiLM modulation sites. A predicted ROI defines an optional 256-by-256 regional crop for `BARRRegionalRefinerV1`. `BARRBenefitRouterV1` predicts an out-of-fold paired refinement gain from GT-free pre-refinement features and a learned task embedding. A resource-aware utility subtracts a fixed normalized action cost before execution. `BARRPostSafetyV1` runs only after refinement and either accepts the fused regional candidate or returns the global prediction. The Phase-26 bundle is a manifest binding four previously trained and frozen components; it introduces no trainable parameters. The repository wrapper defines the state-machine contract but receives precomputed router features, refined crop probabilities, and post-refinement features; the wrapper source alone is not evidence of a self-contained end-to-end forward path.

### Evidence-qualified results
Phase-21 provides a frozen VAL808 GlobalMedFiLM reference with macro-domain Dice 0.8350794169575282. Phase-25 provides refiner-stage cross-fitted development labels and meta-level router/selector predictions on ROUTER_DEVELOPMENT (`n=4957`). The global checkpoint was trained on the enclosing TRAIN population; the upstream refiner and downstream selector folds are not a fully nested hierarchy. These results are development-selected, globally in-sample evidence rather than independent end-to-end OOF evaluation. At the nominal 25% development budget, A8 selected and executed 1,239 candidates, accepted 1,205 refinements, rejected 34 after S_omega, and had an A8 equal-domain macro delta versus global of 0.0013053960890669644. The 1,205 count is accepted output replacements, not the number of refiner executions. The pre-registered A7-versus-A8 contrast is descriptive and inconclusive: its paired mean difference was 1.5717229e-05 with a 95% bootstrap interval crossing zero. Phase-29 varies downstream stacks while fixing the global backbone at seed 42; these are not independent full-system replications. EXT-03 cannot provide protocol-faithful baseline evidence, and BARR-M1 RC1 remains not approved and unexecuted.

### Conclusion
The frozen record supports a technically specified global-fallback selective-refinement design and bounded, development-only observations. It does not establish that FiLM caused the GlobalMedFiLM result, that BARR modules improve a fixed backbone, that post-safety provides clinical safety, that BARR generalizes independently, or that BARR is superior to protocol-faithful baselines. **EVIDENCE PENDING:** C1, C2, C3/AS-08, independent generalization, and end-to-end wrapper equivalence.

## 1. Introduction

Medical-image segmentation across domains must accommodate differences in modality, appearance, target scale, and object context. A global model can provide a stable whole-image prediction, while a regional branch can allocate additional capacity to a predicted area of interest. The difficulty is that the regional branch can also remove context, amplify false positives, or reduce segmentation quality. The relevant question is therefore whether expected refinement benefit can be estimated before paying for computation and whether the global prediction can be preserved when refinement is not useful.

RA-MedFiLM-BARR was developed around this systems question. Its global component, GlobalMedFiLM, is a four-domain task-conditioned reference model. Its regional component is a crop-trained refiner. Its benefit router is trained against leakage-safe paired refinement-gain targets, and its post-refinement selector provides a preservation fallback after the expensive branch has executed. The architecture therefore combines **pre-execution routing** with **post-execution selection**.

The motivation comes from the Phase-22 gap analysis rather than from a claim that refinement is inherently useful. On VAL808, harm was defined as a Dice reduction after applying an oracle regional arm. The record gives `n_executed=808`, `n_harmed=536`, conditional harm rate `0.663366`, and `net_gain_executed=-34.32211179901265` (`reports/audits/phase22_harm_analysis.json`; C-06). The ROI was defined from ground-truth geometry, so this does not estimate a deployable predicted-ROI system. The report's historical 'upper bound' wording applies only to its GT-informed diagnostic/selection framing, not a guarantee about arbitrary future refiners. Its future predicted-ROI benefit-label contract was not implemented in that phase (`reports/phase22_resource_gap_report.md`).

The contribution is stated narrowly. FiLM, regional processing, gating, resource penalties, paired gain labels, global fallback, and post-refinement rejection are not claimed here as individually novel. The defensible subject is the integrated design of a GT-free, pre-execution paired-gain router coupled to optional regional refinement and an explicit fallback. Even that integrated contribution remains bounded by development selection, missing controls, and lack of independent evaluation.

### 1.1 Contributions claimed in this draft

1. A precise description of the frozen GlobalMedFiLM and BARR implementation, including tensor dimensions, thresholds, state transitions, and resource accounting.
2. A provenance-separated organization of Phase-21, Phase-22, Phase-25, Phase-28, and Phase-29 evidence.
3. A conservative analysis of selective refinement, including unfavorable oracle-refinement findings and the inconclusive A7/A8 contrast.
4. An explicit statement of what is not established: FiLM attribution (C1), mechanism/clinical-safety claims (C2), protocol-faithful baseline comparison (C3), AS-08, independent generalization, and BARR-M1 execution.

### 1.2 Claims deliberately not made

This draft does not claim that the system is clinically safe, validated, superior, causal, certified, real-time, mobile-ready, globally resource-optimal, or accepted by a Q1/A* venue. The Phase-21 authority forbids “FiLM caused +X” because no architecture-matched plain control exists (C-04). The BARR-M1 RC1 handoff states that the proposed study is an in-sample descriptive policy comparison and that no independent-generalization, clinical-safety, or superiority claim is permitted.

## 2. Related Work

### 2.1 Task and domain conditioning

FiLM-style feature-wise modulation is a recognized mechanism for conditioning intermediate representations on an auxiliary task or context signal. **[CITATION NEEDED: primary FiLM reference and domain-conditioned medical-segmentation references.]** This manuscript does not use the existence of prior FiLM methods to claim novelty. It reports the repository implementation: task identity enters through a learned embedding and five modulation sites, not through a separate head or concatenated image channel (C-02).

### 2.2 Global and regional segmentation

Global encoder-decoder segmentation and ROI/crop refinement are established design families. **[CITATION NEEDED: representative global-to-local, coarse-to-fine, and ROI-refinement methods.]** The evidence supports describing R_psi as an implemented crop-trained regional refiner, not as a newly invented refinement primitive.

### 2.3 Conditional computation and benefit prediction

Adaptive computation and learned routing allocate expensive computation selectively. BARR’s target is a paired image-level refinement gain: candidate refined Dice minus global Dice. **[CITATION NEEDED: representative conditional-computation and expected-benefit prediction methods.]** The router’s integrated role is a development-supported hypothesis, not a general guarantee.

### 2.4 Safety terminology

“Post-safety” is the repository name for a segmentation preservation selector. It must not be interpreted as clinical safety. Clinical safety would require clinical endpoints, an appropriate clinical population and design, and regulatory context; none is present in the frozen evidence. This manuscript therefore uses “segmentation-harm mitigation” or “post-refinement preservation selection.”


## 3. Proposed Method

### 3.1 System overview

The canonical integration composes four frozen modules: `G = GlobalMedFiLM`, `R_psi = BARRRegionalRefinerV1`, `B_phi = BARRBenefitRouterV1`, and `S_omega = BARRPostSafetyV1`. The Phase-26 wrapper adds zero trainable parameters and defines no joint loss, optimizer, backward graph, or policy-learning function (`src/models/barr/ra_medfilm_barr.py`). Its `forward_inference` contract accepts precomputed 202-D router features, an optional ROI, a refined crop probability, and 16 post-refinement features; it does not itself demonstrate the complete R_psi/feature-extraction driver. The component inventory binds checkpoint identities for all four modules (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/component_inventory.json`).

The processing order is: run G once; construct a GT-free predicted ROI; extract frozen router features; evaluate B_phi and resource utility; skip to the global output if unavailable or below threshold; otherwise execute R_psi; evaluate S_omega; then accept fused output or return the global output. This sequence is the implemented contract, not proof that every component materially improves segmentation.

### 3.2 GlobalMedFiLM architecture

The Phase-21 architecture is one shared residual encoder-decoder across ISIC, BUSI, KVASIR, and KUB. It has 3 input channels, a single foreground-logit output, channel widths `(24, 48, 96, 192, 256)`, GroupNorm, SiLU activations, max pooling, and bilinear upsampling to skip-connection sizes (`reports/audits/phase21_global_medfilm_architecture_binding.json`; C-01). Squeeze-and-Excitation, deep supervision, dataset-specific heads, ROI proposal, regional refinement, fusion, benefit routing, and adaptive computation are absent from this global reference.

Task identity is represented by `t` through `nn.Embedding(task_count, 32)`. For intermediate feature tensor `F`, FiLM is `F_hat = (1 + gamma(t)) * F + beta(t)`, with `gamma = tanh(gamma_raw)` and `beta = tanh(beta_raw)`. The five sites are `bridge`, `decoder4`, `decoder3`, `decoder2`, and `decoder1`, with channel widths 256, 192, 96, 48, and 24. Each FiLM output projection is zero initialized, making each site an exact identity at initialization. Task identity is not concatenated to the input or represented by a task-specific head (`src/models/film/global_medfilm.py`; C-02).

### 3.3 Global prediction

The architecture-level notation separates global probabilities and intermediate features, but `GlobalMedFiLM.forward(x,t)` actually returns logits with shape `[B,1,H,W]`, not a `(probability, features)` tuple. The global extraction contract computes `p_global = sigmoid(logits.float())`; tapped intermediate maps are collected by stage-specific extraction code, not returned by this forward signature (`src/models/film/global_medfilm.py`; `reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json`). The model interpolates logits to input spatial dimensions when required. Phase-21 evaluated 808 samples at segmentation threshold 0.50 without TTA, threshold tuning, or morphology (`reports/audits/phase21_val_evaluation.json`).

### 3.4 Regional refiner and ROI

The regional branch is `R_psi = BARRRegionalRefinerV1`. The canonical authority is `reports/audits/phase25a_canonical_final_freeze.json`; the older `phase25a_final_freeze.json` is retained as a superseded ROI-0.50 protocol-deviation record. The canonical refiner has 1,276,401 parameters, a four-channel crop input (RGB plus cropped global probability), 256-by-256 crop resolution, ROI threshold 0.30, and expansion factor 1.50 (`reports/audits/phase25a_canonical_final_freeze.json`; `reports/audits/barr_m1_v1_0c_scope_freeze.json`; C-07).

Action availability is determined by the predicted ROI. An unavailable/empty ROI produces `FORCED_SKIP` and returns `p_global`. The predicted ROI is GT-free at inference under the frozen contract. Ground truth is used in Phase-25C only for generating and scoring paired gain labels, not as a router input (C-08). The canonical Phase-25A authority records all 4,957 DEV rows as action-available. Ground-truth geometry belongs only to the Phase-22 oracle diagnostic, not this canonical ROI path.

### 3.5 Benefit router

The router input contains 202 numeric pre-refinement features and a 16-dimensional learned task embedding, giving 218 dimensions. The feature schema includes deep feature summaries and scalar descriptors for uncertainty/boundary behavior, predicted foreground and ROI state, predicted ROI area, and side length. Exact names and operations are frozen in `reports/tables/phase25b_feature_schema.csv` and the Phase-25 design records.

B_phi is trained against the raw out-of-fold target. These labels are cross-fitted for the refiner-stage target construction, but the global checkpoint and cached global features come from TRAIN, and ROUTER_DEVELOPMENT is a subset of TRAIN. Therefore this is not fully independent end-to-end OOF evidence:

`DeltaDice_i = Dice(p_candidate,i, y_i) - Dice(p_global,i, y_i)`,

where the candidate uses fold-specific refiner predictions. Phase-25C froze 4,957 leakage-safe OOF labels in ROUTER_DEVELOPMENT. Phase-25D trained B_phi with five outer folds and a final refit using Huber loss and AdamW. Its recorded OOF MAE was 0.006642347667366266 and Pearson correlation was 0.29962822794914246 (`reports/audits/phase25d_final_freeze.json`). These describe development prediction of the target; they do not prove unbiased deployment utility, causal routing benefit, or clinical value (C-09).


### 3.6 Resource-aware policy

The canonical runtime utility is `U_i = delta_hat_final,i - lambda * C_i`, where `lambda = 0.25` and normalized incremental action cost is `C_i = 1051648 / 10270749`. The wrapper uses exact rational constants. The canonical threshold is fixed from development calibration and is not refit by future-cohort ranking. The manifest forbids holdout threshold fitting, holdout quantile recalibration, and exact top-K forcing (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json`).

The fixed-budget development policy and later fixed-threshold application are different operations. DEV top-K selection used K=1,239 at the nominal 25% operating point; the fixed threshold does not enforce a 25% ceiling on later cohorts. Action cost is constant for eligible cases, so subtracting `lambda*C` preserves ordering and ties: C7/A6 and C8/A7 have identical fixed-budget memberships. This is an explicit utility formulation, not experimentally demonstrated improvement from the resource term (`reports/audits/phase25e_cost_variability_and_policy_redundancy_audit.json`).

Resource values are **ANALYTICAL MAC LOWER BOUND** only: global 31,551,740,928; router 36,160; refiner 3,230,662,656; S_omega 1,168 (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/resource_contract.json`). They are not latency, runtime, energy, or mobile-performance measurements.

### 3.7 Post-refinement selection

S_omega receives 16 numeric post-refinement features plus a four-way one-hot task representation, for 20 inputs. It is `Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)`, with 1,217 parameters and raw-logit output (`reports/audits/phase25f_final_freeze.json`). Acceptance is `sigmoid(logit) >= 0.50`. Since S_omega runs after R_psi, it cannot save the already-spent refiner computation; it is post-execution selection, not the compute router.

### 3.8 Fusion and state machine

The four frozen states are `FORCED_SKIP`, `SKIP_GLOBAL`, `EXECUTE_THEN_ACCEPT`, and `EXECUTE_THEN_REJECT`. The first two return `p_global`; acceptance returns the fused regional candidate; rejection returns `p_global` after the refiner has already executed. Fusion uses global probability outside the frozen ROI and resized regional probability inside the ROI, with no alpha blending. The final binary mask uses threshold 0.50 (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/state_machine_contract.json`).

### 3.9 Algorithm

```text
Algorithm 1: Logical state-machine contract with supplied stage artifacts
Input: preprocessed x, task t, frozen G/B_phi/S_omega,
       externally supplied pre-features, ROI geometry, regional crop, post-features
1: logits <- G(x, t); p_global <- sigmoid(logits.float())
2: roi <- supplied frozen geometry (or wrapper's GT-free proposal at 0.30)
3: if action unavailable: return p_global, FORCED_SKIP
4: z <- supplied 202-D features, normalized using the frozen router schema
5: delta_hat <- B_phi(z, t)  [B_phi appends its own 16-D task embedding]
6: U <- delta_hat - 0.25 * (1051648 / 10270749)
7: if U < frozen tau_C8_final: return p_global, SKIP_GLOBAL
8: candidate_crop <- supplied regional probability crop from R_psi lineage
9: q <- supplied 16-D post-features, normalized using frozen selector statistics
10: q20 <- concatenate(q, four-way one_hot(t))
11: accept_prob <- sigmoid(S_omega(q20))
12: if accept_prob >= 0.50: return ROI-fused candidate, EXECUTE_THEN_ACCEPT
13: else: return p_global, EXECUTE_THEN_REJECT
```

**Implementation boundary.** This is a logical contract across stage-specific implementations, not evidence of a self-contained wrapper forward. `GlobalMedFiLM.forward` returns logits; `B_phi.forward` takes numeric features and task IDs; `S_omega.forward` takes a single 20-D input. In the Phase-26 wrapper, the regional crop and post-features must be supplied, and the refiner counter increment does not call R_psi. Stage-specific probability precision, feature normalization, padding/inverse ROI mapping and fusion must be preserved rather than inferred from this pseudocode (`src/models/barr/ra_medfilm_barr.py`; `scripts/analysis/train_phase25d_router.py`; `scripts/analysis/phase25f_execution_common.py`; `reports/audits/phase29_phase_d_component_inference_semantics_contract_v1_1.json`). **[EVIDENCE PENDING: end-to-end wrapper equivalence.]** No model was invoked for this manuscript audit.



## 4. Experimental Setup

### 4.1 Domains and populations

The four task/domain partitions are ISIC dermoscopy, BUSI ultrasound, KVASIR endoscopy, and KUB radiographs. Phase-21 and Phase-22 validation comprise VAL808 (`n=808`) across these domains. The active clean-v3 training partition is 5,832 samples and validation is 808; protected TEST data are outside this manuscript’s evidence scope. ROUTER_DEVELOPMENT has 4,957 rows. The BARR-M1 RC1 identity record lists domain counts BUSI 512, ISIC 2,173, KUB 1,680, and KVASIR 592; these are in-sample development records, not independent test cohorts.

Patient grouping is available for KUB in the proposed reanalysis protocol (267 KUB patients); ISIC, BUSI, and KVASIR use per-case resampling because patient identifiers are not available in those domains (`reports/audits/barr_m1_v1_0c_scope_freeze.json`). This limitation affects claims about patient-level uncertainty and generalization.

### 4.2 Preprocessing and metrics

This draft reports the frozen source’s preprocessing and metric definitions only. Phase-21 validation uses a 0.50 segmentation threshold, no TTA, no threshold tuning, and no morphology. The primary global metric is equal-domain macro Dice when the cited artifact names that estimand. Pooled mean Dice and equal-domain macro Dice are not interchangeable. Paired changes use referenced paired case outcomes; bootstrap intervals appear only where an artifact reports them.

For harm, the event rule and denominator must both be stated. Strict harm is `delta < 0`; tolerance-adjusted harm is `delta < -1e-9`. These differ from Phase-25C's reporting categories (beneficial cutoff +0.02; harmful cutoff -0.01) and from S_omega's binary training target `1[delta > 0]`, for which zero maps to fallback (`reports/audits/phase25c_final_freeze.json`; `reports/audits/phase25f_target_contract_v1_0.json`). All-population, conditional-on-execution and conditional-on-acceptance rates answer different questions. None is clinical risk.

Existing audit counts, transcribed without recomputation, are:

| Policy | Refiner executions | Accepted replacements | Strict harmed cases | Tolerance-adjusted harmed cases | All-population denominator | Conditional denominator for applied-output harm |
|---|---:|---:|---:|---:|---:|---:|
| A0 | 0 | 0 | 0 | 0 | 4,957 | Not applicable |
| A1 | 4,957 | 4,957 | 2,115 | 2,107 | 4,957 | 4,957 |
| A7 | 1,239 | 1,239 | 412 | 412 | 4,957 | 1,239 |
| A8 | 1,239 | 1,205 | 390 | 390 | 4,957 | 1,205 |

Source: `reports/audits/barr_m1_v1_0c_precision_audit.json` and `reports/audits/barr_m1_v1_0b_harm_denominator_audit.json`. For A8, applied-output harm conditions on acceptance, not merely execution. The 34 rejected cases still incurred refiner computation but contribute zero final-output delta under global fallback. These are existing descriptive counts, not outputs of a newly executed BARR-M1 study.

### 4.3 Training and model selection

GlobalMedFiLM was a single logical seed-42 run, with checkpoint selection by macro-domain mean Dice and best epoch 66. It had no architecture or hyperparameter sweep and no independent duplicate run (`reports/audits/phase21_final_freeze.json`). The global checkpoint is reused across later BARR stages.

R_psi was trained as a dedicated crop refiner and frozen in Phase-25A. Phase-25C formed leakage-safe outer-fold candidate outcomes from fold-specific refiner checkpoints. Phase-25D trained B_phi using five outer folds, FIT/EARLY_STOP roles, OOF prediction, and a final refit; the frozen target is raw `delta_dice`. Phase-25F trained S_omega using five folds and a final refit; its OOF predictions are meta-level development predictions. Phase-25G evaluated frozen policies on ROUTER_DEVELOPMENT. The Phase-26 bundle binds these components and performed no additional parameter optimization.

### 4.4 Evidence populations and contamination

The Phase-25 and Phase-28 principal development evidence uses ROUTER_DEVELOPMENT (`n=4,957`). The A8 operating point was selected after Phase-25 development and before Phase-30 holdout evaluation, but development-selection contamination still applies to development evidence. No metric in this paper should be framed as external validation on the basis of these records.

### 4.5 Baseline protocol status

EXT-03 trained 15 baseline runs, but its executed recipe diverged from the frozen Phase-09/10 authority in optimizer class, learning rate, loss, augmentation, and input channels. The v1.1 D6 analysis, retained in the v1.2 disposition, records a post-outcome SegFormer-specific learning-rate repair, so all five families did not share one learning-rate recipe. Checkpoint attestation verifies 15 checkpoint hashes against the registry but does not restore protocol fidelity. The adjudication classifies it `PROTOCOL_DIVERGENT` and states that it cannot supply AS-08 primary evidence or a protocol-faithful comparator to RA-MedFiLM-BARR (`reports/audits/ext03_disposition_v1_1/ext03_scientific_adjudication_addendum_v1_1.md`; v1.2 addenda). It can be cited only as disclosed reduced-protocol context. AS-08 remains unresolved.


## 5. Results

### 5.1 Phase-21 GlobalMedFiLM reference

Phase-21 is a frozen global reference, not the final BARR system. It used one logical run with seed 42, selected epoch 66, and an 808-sample validation evaluation at threshold 0.50, without TTA, threshold tuning, or morphology (`reports/audits/phase21_final_freeze.json`; C-05). The canonical scored macro-domain Dice was 0.8350794169575282; the separately recorded checkpoint-selection macro was 0.8350791259413984. The canonical scored per-domain values were ISIC 0.8971891751747457, BUSI 0.8588228931389639, KVASIR 0.8202473579060531, and KUB 0.7640582416103505. The pooled descriptive Dice was 0.8784243406054913 and is not interchangeable with macro Dice. VAL808 was used for checkpoint selection and later development continuity, so this is not pristine independent validation. These are descriptive reference values, not evidence that FiLM caused the result.

The task-conditioning diagnostic reused an unchanged 64-case gallery with 16 cases per domain. Incorrect task IDs changed Dice by a mean absolute amount of 0.18419164050715645, with maximum absolute change 0.9270517063993946; correct-task mean Dice was 0.859145553979417 (`reports/audits/phase21_task_conditioning_diagnostic.json`; C-03). This demonstrates sensitivity to task input in the trained reference, but does not isolate FiLM from the rest of the architecture. FiLM attribution remains **NOT_ESTABLISHED**.

### 5.2 Phase-22 refinement-harm analysis

Phase-22 is a diagnostic gap analysis on VAL808, with no new training and no TEST access. Its oracle regional arm used ground-truth geometry and cannot be presented as a deployable policy. Harm was defined as a Dice reduction. The analysis reports 536 harmed cases among 808 executed cases, strict harm rate 0.663366 over all 808 executions, mean delta among the 536 harmed cases -0.09574212905848825, worst per-case delta -0.8334218445650708, and sum of deltas over all executed cases -34.32211179901265 (Dice units, not a mean or percentage) (`reports/audits/phase22_harm_analysis.json`; C-06).

Phase-22 reruns the same frozen global model on native-image ROI crops resampled to its 512 input contract; it is not the later dedicated 256 crop-trained R_psi (`src/analysis/phase22_regional.py`). The report proposes context removal and background re-segmentation as explanations for degradation, but these mechanisms were not independently tested. Its oracle acceptance ceiling concerns selection among its own fixed candidates only. Neither oracle geometry nor its observed net loss supplies an upper bound or a result for the later BARR refiner. Its proposed benefit-label contract was not yet implemented in Phase-22 (`reports/phase22_resource_gap_report.md`).

### 5.3 Phase-25 component and integrated development evidence

Phase-25C froze 4,957 OOF paired-gain labels in ROUTER_DEVELOPMENT: 282 beneficial, 335 harmful, and 4,340 neutral under frozen thresholds, with primary target raw `delta_dice` (`reports/audits/phase25c_final_freeze.json`; C-08). Phase-25D trained the router and produced 4,957 OOF predictions. OOF MAE was 0.006642347667366266, Pearson correlation 0.29962822794914246, Spearman correlation 0.21394063290695958, and R2 0.087657630443573 (`reports/audits/phase25d_final_freeze.json`; C-09). These values measure prediction of a development target, not independent policy utility.

Phase-25F produced 4,957 **meta-level OOF development predictions**, not a fully nested end-to-end OOF evaluation. Its three-fold upstream refiner features were not cross-fitted with respect to the five-fold downstream selector partitions (`reports/audits/phase25f_upstream_crossfit_dependency_note.json`). The OOF predictions and the all-DEV final selector refit are separate artifacts. Classifier-level OOF accuracy was 0.5715150292515635, balanced accuracy 0.5365500697764676, ROC AUC 0.5944726302838127, and F1 0.6841165972635336 at threshold 0.50 (`reports/audits/phase25f_final_freeze.json`). These are target-classification metrics, not segmentation preservation proof or clinical-safety metrics.

Phase-25G evaluated 20 frozen policies on ROUTER_DEVELOPMENT (`n=4957`). At budget 0.25, A8 selected/executed 1,239 candidates, accepted 1,205, rejected 34, and had equal-domain macro delta versus global 0.0013053960890669644. A7 selected/executed the same 1,239 candidates and always accepted; its equal-domain macro delta was 0.001290064701772837 (`reports/audits/phase25g_final_freeze.json`). The table-02 `mean_true_delta_dice_routed` values (A7 0.007246629237; A8 0.007515754298) are different pooled conditional means over applied sets, not the macro deltas. These are in-sample development policy measurements, not independent validation or superiority evidence.


### 5.4 Phase-28 comprehensive ablations

Phase-28 executed 13 arms and 18 new training runs on ROUTER_DEVELOPMENT, fixed at nominal budget 0.25 and K=1,239 (`reports/audits/phase28_final_freeze.json`; C-16). The primary arm table reports A0 as global-only, A1 as always-refine, A6/A7 as router-based always-accept policies, A8 as router plus post-safety, R1–R3 as trained router variants, and F1 as a trained refiner variant (`reports/tables/phase28_table_02_arm_primary_metrics.csv`).

The table illustrates both favorable and unfavorable outcomes, but its `mean_true_delta_dice_routed` and `harmful_activation_share` columns are pooled conditional summaries over each arm’s applied set. A1’s pooled mean routed delta was 0.001658079789, with 2,115 harmful routed cases out of 4,957 (harmful activation share 0.426669356466). A6/A7 had pooled mean routed delta 0.007246629237 and harmful activation share 0.332526230831. A8 had pooled mean routed delta 0.007515754298 and harmful activation share 0.323651452282, based on 1,205 accepted replacements in that table. The separate Phase25G A8 macro delta is 0.0013053960890669644. R2 and R3 had lower pooled routed means than A6/A7, while F1's integrated secondary row was unfavorable with pooled mean routed delta -0.032585339607 and harmful activation share 0.688458434221. These rows are descriptive and do not identify causal router or refiner effects.

The frozen contrast map lists A0, A1, R1, R2, R3, and F1 as descriptive rows without formal pairwise references and lists only `A7_vs_A8` as a frozen matched contrast (`reports/audits/phase28_core_contrast_map.json`; C-13). A0/A1/A8 differ in multiple fields, including router, resource term, post-safety, and budget semantics, so their endpoint differences cannot be attributed uniquely to one component. The F1 primary refiner-level comparison is on the common A7/C8 execution membership (`n=1239`) and is strongly negative; its integrated secondary analysis uses 1,239 A7 executions, frozen S_omega decisions, 1,109 F1 accepts and 130 fallbacks, and is a distinct estimand. **EVIDENCE PENDING:** an authorized, fully matched mechanism study.

### 5.5 Phase-29 three-seed descriptive findings

Phase-29 retrained downstream R_psi, B_phi, and S_omega stacks for seeds 42, 123, and 3407 while holding the GlobalMedFiLM checkpoint fixed at seed 42 (`reports/audits/phase29_fixed_global_reference_binding.json`; C-17). The global macro Dice was identical across seeds, so this is not replication of global-backbone training.

On VAL808, downstream-stack macro DeltaDice was 0.0022101452700813433 for seed 42, 0.003387940558448247 for seed 123, and 0.002868801269949678 for seed 3407. The mean was 0.0028222956994930896 and sample SD was 0.0005902732514585419 (`reports/audits/phase29_phase_d_three_seed_descriptive_summary.json`; C-18). The summary explicitly has no numeric reproducibility pass/fail gate and no best-seed ranking. The seed-evidence audit separately cautions that no confidence interval or significance test may be derived from that three-seed SD (`reports/audits/barr_m1_three_seed_evidence_audit_v1_0a.json`). These findings are descriptive downstream reproducibility evidence only.


## 6. Ablation Analysis

### 6.1 A7 versus A8 matched contrast

The only frozen single-component matched contrast is A7 versus A8. Both use ROUTER_DEVELOPMENT `n=4957`, the same 25% budget (`K=1239`), the same selected membership, GT-free predicted ROI, B_phi, and fusion rule. A7 always accepts its executed regional candidate; A8 applies S_omega after execution. The contrast isolates the post-refinement selector within the frozen development policy, not clinical safety or the full routing policy.

The paired contrast reported 1.5717229e-05 mean A8-minus-A7 difference, bootstrap standard error 1.6292351e-05, and 95% interval [-1.4313785e-05, 5.1010811e-05] from 2,000 direct case-index resamples with seed 42 (`reports/tables/phase28_table_08_bootstrap_statistics.csv`; C-14). This is an all-case paired pooled mean with zero fallback outside each policy’s applied set, not an equal-domain macro-Dice interval or patient-clustered interval. The interval crosses zero. This is an inconclusive descriptive measurement, not proof that S_omega improves Dice. Crossing zero also does not establish equivalence or prove absence of an effect. The pooled interval must not be assigned to the separate equal-domain macro point.

Phase-25G accounting at budget 0.25 lists 412 harmful applied cases for A7 and 390 for A8, with 22 fewer harmful applied replacements under A8 (`reports/audits/phase25g_final_freeze.json`). A7’s 412/1,239 is conditional on execution; A8’s 390/1,205 is conditional on accepted replacement, while the all-population A8 rate is 390/4,957. These are segmentation-harm accounting under a development population and frozen scoring rule; they are not clinical-safety measures.

### 6.2 Why A0/A1/A8 is not a causal router ablation

A0 is global-only, A1 refines all cases, and A8 combines routing, a resource penalty, reduced nominal budget, and post-safety. The arm identity audit records that A8 versus A1 changes multiple factors simultaneously. The v1.0c erratum corrects causal wording and states that BARR-M1 is a descriptive comparison of complete policies, not attribution uniquely to the router, safety stage, or computation budget. **[EVIDENCE PENDING: an authorized isolated-router control.]**

### 6.3 Negative refiner and router findings

Phase-28 retained unfavorable arms rather than reporting only favorable results. F1’s primary refiner-level comparison on 1,239 common A7/C8 executions had canonical candidate mean delta 0.007246629236765178, F1 candidate mean delta -0.04417994631626067, paired difference -0.05142657555302585, and 95% bootstrap interval [-0.0554756492900591, -0.047574470112445366] (`reports/audits/phase28_f1_refiner_level_comparison.json`). Its distinct integrated secondary analysis, using frozen S_omega rather than retraining it, had mean delta -0.032585339606785245 over 1,239 selected execution rows, with 1,109 accepts and 130 fallbacks (`reports/audits/phase28_f1_integrated_secondary.json`). That artifact also labels membership as 'EXACT_CANONICAL_A8_25PCT_OOF' and records 1,205 A8 members, creating an internal membership-label inconsistency with its 1,239-row denominator. The original secondary conditional comparison cannot be promoted to a fully matched comparison merely because it is frozen. It is also sensitive to applying the original selector to altered candidate inputs. R2 and R3 also had lower pooled routed means than A6/A7. These are descriptive variant findings, not causal refiner or router effects.

## 7. Discussion

### 7.1 What selective refinement appears to achieve

The development evidence is consistent with a small positive integrated macro-Dice delta relative to the frozen global reference at the frozen operating point. At 25% nominal budget, the Phase-25G A8 macro delta was 0.0013053960890669644 on ROUTER_DEVELOPMENT. Phase-29’s three downstream stacks produced positive descriptive VAL808 macro deltas, with mean 0.0028222956994930896. These observations are compatible with selective processing, but do not establish superiority or generalization beyond the recorded development/validation setup.

### 7.2 Refinement degradation and fallback

The Phase-22 oracle result warns that even GT-defined geometry does not make regional processing uniformly beneficial; it is not an upper bound for every later refiner architecture. Phase-28’s F1 refiner variant also shows unfavorable candidate and integrated outcomes on the DEV population. BARR’s global fallback is an implementation safeguard against substituting a rejected candidate, not evidence of clinical protection. Harm accounting concerns segmentation Dice only.

### 7.3 Benefit-router evidence

B_phi predicts paired gain with modest OOF association metrics on development labels (C-09). This supports describing a trained predictor, not asserting accurate patient-level benefit estimation in independent populations. The target depends on the frozen refiner, ROI, scoring metric, and data partition; changing these changes the estimand. A future study should assess calibration, utility, and benefit capture under an external protocol without post-hoc threshold adjustment.

### 7.4 Post-refinement selector evidence

A7/A8 is the proper frozen component-isolation contrast. Its 95% interval crosses zero, so this evidence does not resolve a positive mean-Dice effect. Although recorded harmful replacement counts are lower under A8 at the development operating point, the matched bootstrap contrast is inconclusive and its metric is segmentation harm, not patient safety. Since S_omega runs after refinement, it cannot save pre-execution compute.

### 7.5 FiLM attribution, baseline validity, and novelty

C1 remains NOT_ESTABLISHED: the model has task-conditioned architecture and a task-ID diagnostic, but no architecture-matched FiLM-off control. The task perturbation diagnostic does not replace that control. C2 remains NOT_ESTABLISHED: A7/A8 does isolate S_omega's decision mechanically within a frozen development policy, but its pooled Dice interval is inconclusive and the evidence is not independent. A0/A1/A8 cannot isolate B_phi because router, selector, cost and budget vary together. Existing matched design must not be confused with a demonstrated positive mechanism effect. C3 and AS-08 remain unresolved because EXT-03 diverged on five protocol dimensions and the v1.1 D6 analysis, carried forward in v1.2, records a post-outcome SegFormer learning-rate repair. Its matrix may be described only as disclosed reduced-protocol context; it cannot serve as a same-protocol comparator against GlobalMedFiLM/BARR.

No causal or first-ever novelty claim is warranted. The mechanism and paired-gain target are precedented; the proposed contribution is only a bounded system-level integration hypothesis. A source-checked literature review remains necessary. **EVIDENCE PENDING:** independent mechanism and protocol-faithful benchmark evidence.

### 7.6 Statistical and reproducibility limitations

Phase-28 intervals are descriptive development intervals with no post-hoc multiplicity correction. The Table08 matched-loop implementation resamples case indices directly; despite summary prose calling the procedure group/domain-aware, the executed loop does not implement KUB patient clustering or equal-domain stratification. Therefore the A7/A8 interval is not a patient-clustered macro interval. Phase-29’s sample SD over three downstream seeds has two degrees of freedom, does not represent sampling uncertainty or variation in G, and is explicitly not a pass/fail gate. BARR-M1’s proposed paired bootstrap design is not executed; its RC1 handoff reports synthetic software tests only and no real-data contrast or bootstrap estimate.

## 8. Limitations

1. **FiLM attribution (C1): NOT_ESTABLISHED.** There is no architecture-matched FiLM-off model; Phase-21 reports a single global run and forbids causal attribution.
2. **Mechanism and clinical-safety claims (C2): NOT_ESTABLISHED.** Segmentation harm is measured, but clinical outcomes, patient-safety endpoints, prospective clinical evidence, and regulatory validation are absent.
3. **Protocol-faithful baseline comparison (C3): NOT_ESTABLISHED.** EXT-03 is protocol-divergent and cannot support AS-08 primary evidence or a direct same-protocol comparison.
4. **AS-08: UNRESOLVED.** A prospective, authorized protocol-faithful baseline study remains necessary.
5. **Development-selection contamination.** Principal BARR development results and operating-point selection use ROUTER_DEVELOPMENT, a subset of TRAIN; these are not pristine independent evaluations. Phase25F also documents a non-nested upstream/downstream OOF hierarchy.
6. **Fixed global backbone in Phase-29.** Only downstream components vary across seeds; global model training variability is unmeasured.
7. **Missing patient identifiers.** Several domains lack patient IDs, limiting patient-clustered uncertainty analysis.
8. **No independent mechanism confirmation or independent generalization.** No external evidence in the cited records establishes the learned routing mechanism in new cohorts.
9. **Protected evaluation restrictions.** This manuscript preparation did not access TEST or ROUTER_HOLDOUT. It reports no new protected-set result or external outcome.
10. **BARR-M1 status.** The v1.0d RC1 handoff says NOT APPROVED, production inactive, and no scientific execution. BARR-M1 must not be reported as performed.
11. **Resource claims.** MAC figures are analytical lower bounds only; no hardware latency, energy, or mobile readiness is established.
12. **Related work remains incomplete.** Citation-needed markers are retained rather than replaced with invented bibliographic references.

## 9. Conclusion

RA-MedFiLM-BARR is a frozen staged system design combining task-conditioned global segmentation, conditional regional refinement, a learned pre-execution paired-gain router, resource-aware selection, and a post-refinement global fallback. Its record includes implementation contracts and descriptive development findings, including negative regional outcomes, a strongly negative F1 refiner variant, and an inconclusive matched A7/A8 pooled paired contrast. The evidence does not establish causal FiLM benefit, BARR mechanism benefit, clinical safety, protocol-faithful baseline superiority, independent generalization, or self-contained wrapper equivalence. Further authorized controls and independent evaluations are required before confirmatory claims or submission. **EVIDENCE PENDING:** C1, C2, C3/AS-08, independent generalization, and end-to-end equivalence.



## 10. References and citation placeholders

No external bibliographic records were verified during this manuscript task. Replace placeholders only after a source-checked literature review and citation verification.

1. **[CITATION NEEDED]** Original FiLM/feature-wise modulation method.
2. **[CITATION NEEDED]** Multi-domain or task-conditioned medical-image segmentation studies.
3. **[CITATION NEEDED]** Global-to-local, ROI-based, or cascaded medical segmentation methods.
4. **[CITATION NEEDED]** Conditional computation/resource-aware routing methods.
5. **[CITATION NEEDED]** Learned expected-benefit or gain-prediction methods.
6. **[CITATION NEEDED]** Selective prediction, post-hoc rejection, or fallback methods; distinguish from clinical safety.

## 11. Planned Figures and Tables

### Figures

- **Figure 1.** GlobalMedFiLM shared encoder-decoder and five task-conditioned FiLM sites. Caption must note C1 attribution is not established.
- **Figure 2.** BARR inference state machine: GT-free predicted ROI, B_phi utility, conditional R_psi, S_omega accept/reject, and global fallback.
- **Figure 3.** Evidence timeline and populations for Phases 21, 22, 25, 28, and 29; distinguish VAL808 and ROUTER_DEVELOPMENT.
- **Figure 4.** A7/A8 matched contrast and interval; label development population and interval crossing zero.

### Tables

- **Table 1.** GlobalMedFiLM/BARR components, architecture, parameter counts, checkpoint roles, and freeze status.
- **Table 2.** Domains, split/population roles, and patient-identifier availability.
- **Table 3.** Phase-21 global validation results, equal-domain macro metric, and per-domain values.
- **Table 4.** Phase-22 oracle refinement harm results, marked GT-defined ROI and diagnostic-only.
- **Table 5.** Phase-25 router/safety development metrics, separating target prediction from segmentation metrics.
- **Table 6.** Phase-28 arm results with evidence class and descriptive-comparison restrictions.
- **Table 7.** A7/A8 matched paired contrast, bootstrap method, and interval.
- **Table 8.** Phase-29 downstream seeds, fixed-global qualifier, and descriptive-only status.
- **Table 9.** EXT-03 protocol divergences; no same-protocol comparison claim.

## 12. Evidence-to-claim trace and submission gate

The preserved preparation matrix `reports/manuscript_draft/claims_to_evidence.md` contains 22 claim rows. Its claim text is not uniformly endorsed: C-14's definitive selector-benefit wording and C-17's independent-backbone wording are contradicted by their cited results, while their original negative statuses are retained. The new `reports/manuscript_draft/critical_evidence_reviewer_audit_v0_2.md` records all dispositions, controlling source corrections, reviewer risks and proposed experiments. It governs the revised interpretation without modifying that matrix or v0.1. Bibliographic citations remain incomplete. Additional studies remain **EVIDENCE PENDING** and require separate authorization.

**Submission-gating evidence still missing:** an authorized architecture-matched FiLM-off control; an authorized isolated-router study; independent external/generalization evaluation; protocol-faithful baselines to resolve C3/AS-08; independent confirmation of the routing mechanism; and clinical endpoints/design if clinical-safety language is ever considered. None is represented as complete here.

**BARR-M1 notice:** The BARR-M1 v1.0d RC1 handoff remains NOT APPROVED, production inactive, and not scientifically executed. No approval, launch order, or authorization is implied by this manuscript.
