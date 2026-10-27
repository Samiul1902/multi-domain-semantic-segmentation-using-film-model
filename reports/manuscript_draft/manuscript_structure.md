# RA-MedFiLM-BARR: Evidence-Grounded Manuscript Structure

## Document purpose and evidence boundary

This is a non-frozen drafting workspace, not a revision of any scientific record. It organizes only already recorded evidence for **RA-MedFiLM-BARR (Resource-Aware MedFiLM with Benefit-Aware Refinement Routing)**. Evidence labels used below are: **FROZEN_AUTHORITY** for a binding architecture, protocol, manifest, or scope record; **EXECUTED_DESCRIPTIVE** for completed measurements with stated population and protocol; **EXPLORATORY** for observations that are not confirmatory; **PROSPECTIVE** for a frozen future plan; **UNRESOLVED** for a claim that has not been supported; and **SUPERSEDED** for a record corrected by a later identified authority. No TEST, ROUTER_HOLDOUT, training, model inference, or new statistical reanalysis was performed while drafting this document.

## 1. Working title

**RA-MedFiLM-BARR: Task-Conditioned Global Segmentation with Benefit-Aware Regional Refinement Routing**

Alternative conservative title: **An Evidence-Grounded Study of Selective Regional Refinement in a Shared Multi-Domain Segmentation System**.

The title should not promise clinical safety, causal FiLM benefit, protocol-faithful superiority over external baselines, or deployment readiness.

## 2. Abstract outline

**Background.** A shared segmentation model may face heterogeneous regional-refinement outcomes across medical-image domains. Phase-22 diagnostic evidence found that an oracle, ground-truth-defined regional arm could reduce Dice on many validation cases; it therefore motivates selective refinement rather than establishing a deployable regional policy.

**Method.** GlobalMedFiLM is a single shared residual encoder-decoder conditioned by task identity through five FiLM sites. The BARR stack pairs this global prediction with a predicted ROI, a conditional regional refiner, a learned pre-execution benefit router, and a post-refinement accept/reject selector with global fallback. The canonical Phase-26 manifest binds four frozen checkpoints and thresholds; it is a manifest of existing components, not a new learned model.

**Evidence reported.** The manuscript can report frozen Phase-21 validation results, Phase-25 OOF development records, Phase-28 development ablations, and Phase-29 three-seed descriptive observations with their exact populations. It must label all development-selected and in-sample results. EXT-03 is protocol-divergent and cannot support protocol-faithful baseline claims. BARR-M1 RC1 is inactive and not approved.

**Conclusion.** The appropriate conclusion is that frozen evidence supports a well-specified selective-refinement system and descriptive development observations, while FiLM attribution, clinical safety, protocol-faithful benchmarking, independent generalization, and BARR-M1 execution remain unestablished.

## 3. Introduction and research motivation

The research question is not whether refinement is always beneficial. The Phase-22 analysis evaluated the frozen Phase-21 reference on VAL808 and defined harm as a Dice decrease after applying an oracle regional arm. It recorded 536 harmed cases among 808 executed cases and a net executed gain of -34.32211179901265 Dice units (`reports/audits/phase22_harm_analysis.json`, keys `n_harmed`, `n_executed`, and `net_gain_executed`). Because this arm used ground-truth ROI geometry, it is an upper-bound diagnostic rather than a deployable method (`reports/phase22_resource_gap_report.md`, Interpretation guard 1). These observations motivate the need to predict whether optional refinement is worthwhile before incurring its cost.

The scientific gap should be framed narrowly: a frozen integrated system is available for learned, GT-free, pre-execution routing of an optional regional branch, but the evidence is restricted to specified development protocols. The introduction must distinguish that system-level integration from individual primitives. The architecture authority explicitly classifies the regional refiner, ordinary gate, resource penalty, post-safety, fusion, global fallback, and paired supervised gain estimand as non-novel/prior-art or ordinary engineering; the scoped contribution is the integrated learned GT-free paired-gain routing design (`docs/ARCHITECTURE.md`, novelty accounting).

## 4. Related-work requirements

The completed manuscript needs a literature review that separates: (a) FiLM and domain/task conditioning; (b) shared multi-domain medical segmentation; (c) ROI/crop-based refinement; (d) conditional computation and routing; (e) prediction of expected benefit or improvement; and (f) global fallback or post-refinement rejection. Citations must be added only after a source-checked literature review. The review must not assert firstness or causal novelty. It should explicitly state that the manuscript's defensible contribution, if any, is a bounded system/integration contribution rather than invention of its individual primitives.

## 5. GlobalMedFiLM methodology

### 5.1 Architecture and task conditioning

GlobalMedFiLM is the Phase-21 global reference, with one shared parameter set and a shared 1x1 foreground-logit head. The architecture binding records 3,523,001 parameters, a residual encoder-decoder with channel widths 24, 48, 96, 192, and 256, GroupNorm, SiLU, max pooling, bilinear decoder upsampling, and no dataset-specific output head (`reports/audits/phase21_global_medfilm_architecture_binding.json`). It is explicitly global-only: it contains no ROI proposal, refiner, router, fusion, or post-safety component.

For task identifier t and intermediate feature F, its FiLM operation is

`F_hat = (1 + gamma(t)) * F + beta(t)`,

where `gamma = tanh(gamma_raw)` and `beta = tanh(beta_raw)`. A learned 32-dimensional task embedding is the sole task signal; task identity is not concatenated to the image, inserted as an image channel, or represented by a task-specific head. FiLM is applied at the bridge and decoder stages decoder4, decoder3, decoder2, and decoder1 (`src/models/film/global_medfilm.py`; `reports/audits/phase21_global_medfilm_architecture_binding.json`). The FiLM output projections are zero initialized, making all sites exact identities at initialization. This is an implementation fact, not evidence that FiLM caused a measured performance difference.

### 5.2 Global prediction and Phase-21 evidence

The frozen Phase-21 reference used seed 42, selected epoch 66 using macro-domain mean Dice, and evaluated 808 validation samples at threshold 0.5 without TTA, threshold tuning, or morphology (`reports/audits/phase21_final_freeze.json`; `reports/audits/phase21_val_evaluation.json`). Its frozen macro-domain Dice result was 0.8350794169575282. This is an executed validation measurement, not external validation or a causal FiLM estimate. The Phase-21 interpretation guard explicitly forbids “FiLM caused +X” because no architecture-matched plain-model control was trained (`reports/audits/phase21_final_freeze.json`, `interpretation`).

The 64-case wrong-task diagnostic shows predictions respond to supplied task identity: mean absolute Dice difference under incorrect task IDs was 0.18419164050715645 (`reports/audits/phase21_task_conditioning_diagnostic.json`). It is a diagnostic gallery, not an architecture-matched attribution experiment. Accordingly, **C1 FiLM attribution remains NOT_ESTABLISHED**.

## 6. BARR methodology

### 6.1 Regional refinement and ROI construction

The canonical regional refiner R_psi is `BARRRegionalRefinerV1`, a conditional component with 1,276,401 trainable parameters and an analytical cost of 3,230,662,656 MACs. It accepts a four-channel 256-by-256 crop comprising RGB plus the global-probability crop; its input and output contracts are frozen in the Phase-25/26 records (`reports/audits/phase25a_final_freeze.json`; `artifacts/phase26_ra_medfilm_barr_bundle_v1_0/component_inventory.json`). The canonical ROI proposal threshold is 0.30, expansion factor is 1.50, and the crop resolution is 256 (`reports/audits/barr_m1_v1_0c_scope_freeze.json`). When no action is available, the state machine forces global fallback.

The Phase-25C target is out-of-fold paired refinement gain, `DeltaDice = Dice(candidate_refined) - Dice(global)`, generated for 4,957 ROUTER_DEVELOPMENT rows using cross-fitted refiner predictions. Ground truth was used to construct labels and score outcomes, not as a router inference input (`reports/audits/phase25c_final_freeze.json`). These labels are development evidence and do not establish performance on independent cohorts.

### 6.2 Benefit-aware pre-execution routing

B_phi is `BARRBenefitRouterV1`. It receives 202 frozen GT-free numeric pre-refinement features plus a learned 16-dimensional task embedding, for 218 inputs, and predicts raw paired `delta_dice`. The Phase-25D final freeze documents 36,801 parameters, five CV folds, a final refit of 80 epochs, and 4,957 OOF predictions; OOF MAE was 0.006642347667366266 and OOF Pearson correlation was 0.29962822794914246 (`reports/audits/phase25d_final_freeze.json`). Those are model-development measurements, not proof that routing provides a causal or clinically useful benefit.

For the canonical bundle, the runtime score is `U = delta_hat_final - 0.25*C`; `C` is normalized incremental regional cost. The Phase-26 manifest fixes the threshold from development calibration and explicitly forbids holdout threshold fitting and exact 25% forcing on future cohorts (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/canonical_bundle_manifest.json`). Router overhead is 36,160 analytical Conv/Linear MACs, while the refiner is conditional (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/resource_contract.json`). These are analytical MAC lower bounds, not latency, runtime, energy, or mobile-performance measurements.

### 6.3 Post-refinement safety filtering and fusion

S_omega is `BARRPostSafetyV1`: a 20-input MLP, `Linear(20,32) -> SiLU -> Linear(32,16) -> SiLU -> Linear(16,1)`, with 1,217 parameters and a raw-logit output (`reports/audits/phase25f_final_freeze.json`). It runs only after a router-selected refiner execution and does not save the refiner computation. Its final decision accepts when `sigmoid(logit) >= 0.50`; the final segmentation threshold is separately 0.50.

The canonical state machine has four states: FORCED_SKIP, SKIP_GLOBAL, EXECUTE_THEN_ACCEPT, and EXECUTE_THEN_REJECT. In the reject state the refiner has already run and the final probability returns to `p_global`. In an accepted execution, fusion uses global probability outside the frozen ROI and resized refined probability inside it, without alpha blending (`artifacts/phase26_ra_medfilm_barr_bundle_v1_0/state_machine_contract.json`). This is a segmentation-preservation design, not a clinical-safety intervention. **C2 mechanism and clinical-safety claims remain NOT_ESTABLISHED.**

## 7. Mathematical methodology to report

The Methods section can define the global function as `p_global, F_global = G(x,t)`, the paired label as `DeltaDice_i = Dice(p_candidate,i, y_i) - Dice(p_global,i, y_i)`, the router prediction as `delta_hat_i = B_phi(z_i,t_i)`, and the canonical resource-aware score as `U_i = delta_hat_i - lambda*C_i` with lambda fixed at 0.25 in the bundle. Selection is threshold-based against a frozen development-calibrated threshold, not future-cohort top-K forcing. The safety decision is `a_i = 1[sigmoid(S_omega(q_i,t_i)) >= 0.5]`. The output is `p_global` for forced skip, router skip, or post-safety rejection; otherwise it replaces the ROI with the refined candidate. These equations describe frozen code/manifest semantics and must not be expanded into unverified losses or features beyond their cited sources.

## 8. Datasets, splits, preprocessing, and experimental setup

The verified Phase-21/22 validation population contains 808 samples across ISIC, BUSI, KVASIR, and KUB. Phase-25 ROUTER_DEVELOPMENT contains 4,957 rows; the RC1 identity record gives domain counts BUSI 512, ISIC 2173, KUB 1680, and KVASIR 592 (`reports/planning/barr_m1_v1_0d_rc1_handoff/release_identity.json`). The active clean-v3 global split is TRAIN 5,832, VAL 808, TEST 1,683, and QUAR 118 in the historical protocol documentation; any final manuscript must cite its current split authority precisely and keep TEST results separate. Several domains lack patient identifiers; the frozen BARR-M1 protocol uses KUB patient clusters but per-case grouping for ISIC/BUSI/KVASIR because patient IDs are unavailable (`reports/audits/barr_m1_v1_0c_scope_freeze.json`).

The experimental section must disclose that Phase-25 and Phase-28 are development/in-sample evidence. Phase-29 retrained downstream R_psi, B_phi, and S_omega for seeds 42, 123, and 3407 while holding the Phase-21 global model fixed at seed 42 (`reports/audits/phase29_fixed_global_reference_binding.json`; `reports/audits/barr_m1_three_seed_evidence_audit_v1_0a.json`). It is not three independent replications of the entire system.

## 9. Existing results and interpretation

Report results in separate evidence-class tables: (1) Phase-21 frozen VAL808 global reference; (2) Phase-22 oracle-ROI diagnostic harm analysis; (3) Phase-25 OOF ROUTER_DEVELOPMENT component and integrated evidence; (4) Phase-28 fixed-budget development ablations; and (5) Phase-29 three-seed descriptive VAL808 findings. Do not pool them as if they share the same ROI source, population, or statistical role.

At Phase-25G’s 25% development budget, 1,239 candidates were selected and 1,205 were accepted after post-safety. The A8 macro delta versus global was 0.0013053960890669644 on ROUTER_DEVELOPMENT (`reports/audits/phase25g_final_freeze.json`). This is controlled meta-level OOF development evidence, not an independent confirmation. The sole pre-registered matched component contrast is A7 versus A8. Its 4,957-case paired mean difference was 1.5717229e-05 with a 95% bootstrap interval from -1.4313785e-05 to 5.1010811e-05, which crosses zero (`reports/tables/phase28_table_08_bootstrap_statistics.csv`). It can be reported as descriptive and inconclusive for a positive segmentation effect of S_omega; it cannot establish clinical safety.

Phase-29’s VAL808 descriptive summary reported macro DeltaDice values of 0.0022101452700813433, 0.003387940558448247, and 0.002868801269949678 for downstream seeds 42, 123, and 3407, respectively, with mean 0.0028222956994930896 and sample SD 0.0005902732514585419 (`reports/audits/phase29_phase_d_three_seed_descriptive_summary.json`). The source explicitly has no numeric reproducibility pass/fail gate and prohibits a best-seed ranking. The global reference was identical across seeds, so this variation reflects only downstream-stack retraining under this protocol.

## 10. Ablations, baselines, novelty, and limitations

Phase-28 has 13 arms and 18 new training runs on ROUTER_DEVELOPMENT, fixed at budget 0.25 and K=1,239 (`reports/audits/phase28_final_freeze.json`). The contrast map specifies that A0, A1, R1–R3, and F1 are descriptive matrix rows without a formal pairwise reference; only A7_vs_A8 is a frozen matched contrast (`reports/audits/phase28_core_contrast_map.json`). A0/A1/A8 change multiple factors, so their differences cannot identify the router’s isolated causal effect (`reports/audits/barr_m1_arm_identity_audit_v1_0a.json`).

EXT-03 is complete but protocol-divergent. Its five documented divergences from the frozen phase09/10 authority are optimizer, learning rate, loss, augmentation, and input channels (`reports/audits/ext03_disposition_v1_1/ext03_scientific_adjudication_addendum_v1_1.md`). It may be described only as a reduced-protocol, common-protocol architecture-ranking record, not as AS-08 primary evidence or a protocol-faithful comparison against BARR. Thus **C3 protocol-faithful baseline comparison and AS-08 remain UNRESOLVED**.

The discussion must state development-selection contamination; fixed G across Phase-29 downstream seeds; lack of a FiLM-off control; missing patient IDs in multiple domains; no independent mechanism confirmation; no external/generalization confirmation; no clinical endpoints; protected evaluation restrictions; and no claim of Q1/A* acceptance or publication readiness.

## 11. Conclusion and missing experiments before submission

The conclusion should state only that a frozen, reproducible implementation and bounded development evidence exist for a global-fallback selective-refinement system. It should not claim superiority, clinical safety, or causal attribution.

Required future work before a confirmatory submission includes: an independently authorized architecture-matched FiLM-off control; a prospective same-protocol baseline study replacing EXT-03’s divergent recipe; independent external and/or held-out evaluation under predeclared rules; patient-level grouping where available; mechanism-focused evaluation separating router, cost, and safety factors; and an explicit clinical-safety study if clinical claims are desired. BARR-M1 is not an executed study: v1.0d RC1 is frozen, NOT APPROVED, production inactive, and requires independent authorization plus a separate signed launch work order (`reports/planning/barr_m1_v1_0d_rc1_handoff/HANDOFF.md`; `release_identity.json`).
