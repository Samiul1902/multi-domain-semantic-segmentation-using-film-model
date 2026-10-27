# RA-MedFiLM-BARR — Final experimental research handoff

## Stop boundary and decision gates

Repository: `D:\Softfors\jup`. Manuscript iteration ends with this handoff. No new manuscript version, scientific execution, model import, training, inference, protected TEST/ROUTER_HOLDOUT access, statistical reanalysis or authorization provisioning is permitted by these documents.

**None of the studies below is currently authorized by this handoff.** In particular, “approved CPU-only BARR-M1” is not the present state: RC1 `release_identity.json` says `approval_granted=false`, `production_activated=false`, trust anchor not configured, trusted time not established and separate launch work order absent. CPU-only reanalysis is the requested scope, not an approval. Do not change RC1 to make it executable.

The priority order is scientific, not a claim of operational permission. A low-compute descriptive task may be authorized independently without changing the priority of the next prospective experiment.

Common gates: accountable scientific authority -> explicit scoped approval -> eligibility/protocol/estimand freeze -> verified implementation and input identities -> separate execution work order. Freeze failure handling, selection, missingness, clustering, multiplicity and all outcomes before launch. Missing patient identifiers must be disclosed, not replaced by invented patients. Existing DEV and VAL are consumed development populations; a new independent cohort cannot be presumed eligible. No use of protected outcomes to choose hyperparameters, population, thresholds or arms.

## Priority 1 — C1: matched FiLM-off attribution

- **Hypothesis:** Activating learned task conditioning improves the predeclared multi-domain segmentation endpoint relative to an otherwise architecture-identical identity-modulation control. C1 remains NOT_ESTABLISHED today.
- **Primary estimand (proposal):** within-seed paired treatment-minus-control equal-domain macro Dice difference, averaged across a predeclared matched seed set; zero difference remains a legitimate result. Separate VAL-selected model comparison from independent evaluation if later authorized.
- **Secondary estimands:** domain-specific Dice deltas, ordinary per-case mean deltas separately, variability across matched training seeds, and total/trainable parameter accounting. Do not infer C2 or C3 from C1.
- **Treatment/control:** Freshly initialize the same GlobalMedFiLM backbone for both arms. Treatment trains task embedding and FiLM; control retains the same modules but freezes task embedding and FiLM so the zero-initialized output projections keep gamma=beta=0. Preserve matched backbone initialization, data order/augmentation randomness where feasible, preprocessing, optimizer, loss, scheduler, stopping, selection and scoring. Verify identity without using protected pixels. Do not zero a trained treatment checkpoint as a substitute for control training.
- **Naming safeguard:** This is a proposed matched FiLM-off/identity-modulation control. It is **not Phase-28 F1**, which removes the refiner's p_global input channel. The old memorandum's “Design F1” freeze-at-initialization label is a different namespace; use explicit descriptive names to prevent conflation.
- **Eligibility:** Existing TRAIN may be proposed for fitting and VAL808 for declared selection/descriptive decomposition. VAL808 is not independent confirmation. A genuinely independent prospective endpoint needs its own audited cohort/protocol. TEST and ROUTER_HOLDOUT remain excluded here.
- **Statistics:** Predeclare seed count and paired estimands; at least three matched seeds is preferable to single-seed attribution but is not a powered design by itself. Plan uncertainty separating patient/case sampling and training seeds; cluster real patient IDs within domains, disclose unavailable IDs, and define multiplicity for domain/secondary outcomes. Predeclare missingness, empty-mask rules and checkpoints.
- **Confounders:** Architecture removal changes capacity; matched total parameters do not mean matched trainable parameters. Identity control retains 3,523,001 total parameters but has 3,432,233 trainable per the recorded design. Also control initialization/order, model selection, precision and augmentation. No claim of independent generalization from a VAL-selected comparison.
- **Resources:** New global training for both arms across the approved seed set; substantially more compute than frozen-array analysis. No measured prospective wall-time or power estimate is established; obtain a resource plan before authorization, not an unsupported hour forecast.
- **Dependencies/testable claim:** Scientific approval naming C1 only, immutable new experiment namespace and resolved protocol. A completed controlled study would make task-conditioning attribution testable within that protocol, not prove clinical safety, BARR mechanism or superiority.

## Priority 2 — C2: prospective BARR mechanism attribution

- **Hypothesis:** Learned routing allocates refinement computation more usefully than matched GT-free controls; the post-refinement selector changes quality/harm under identical executed candidates. These are separate subquestions, not a clinical-safety test.
- **Primary estimands (proposal):** router study: paired equal-domain macro Dice difference with fallback zeros at common execution budget and fixed G/R/candidate protocol; selector study: paired macro A8-minus-A7 effect on identical executed candidates. Freeze direction/margin and endpoint family first; Table08's pooled CI is not a macro CI.
- **Secondary estimands:** pooled all-case paired delta; strict/tolerance final-output harm over all eligible, executed and accepted cases separately; positive-gain capture, missed benefit, execution/acceptance/rejection; analytical versus measured compute separately.
- **Treatments/controls:** Hold G, R, crop geometry, fusion, precision and threshold constant. Compare learned B_phi with predeclared random and prediction-only proxy routers at equal K, holding S_omega fixed or absent. For S_omega, compare A7 always-accept with A8 on the same executions. A0/A1/A8 is confounded. Constant eligible cost cannot identify a cost-term effect at fixed K; variable-cost testing would be a separate approved extension.
- **Eligibility:** Authorized DEV frozen arrays can support descriptive decomposition, not prospective confirmation. Independent claims require a new eligible cohort or approved nested design; G must not be fitted on evaluation cases. TEST and ROUTER_HOLDOUT excluded here. Resolve upstream/downstream cross-fitting.
- **Statistics:** Freeze keyed case alignment, eligible denominator, paired macro estimator, patient/source clusters, seed replication, effect-size/precision rationale and multiplicity. Use real KUB IDs; disclose missing non-KUB IDs. Separate within-model paired effects from training-seed variation. Retain negative/inconclusive outcomes.
- **Confounders:** TRAIN-fitted G, non-nested folds, selection/calibration, distribution shift into frozen S_omega, unequal applied sets, conditional denominator changes and post-hoc policy tuning. Do not choose a favorable label from inconsistent F1 metadata.
- **Resources:** Separately approved A7/A8 frozen-array decomposition is CPU-only/no inference. Prospective mechanism work needs independent inference and possibly fresh nested downstream training; no verified runtime or powered sample size is available.
- **Dependencies/testable claim:** New C2 protocol/approval (BARR-M2 provisional), implementation/provenance checks and cohort eligibility. BARR-M1 excludes A7. A completed controlled study tests component-specific segmentation quality/harm, not patient safety; generalization needs priority 5.

## Priority 3 — C3 / AS-08: protocol-faithful baseline benchmarking

- **Hypothesis:** BARR differs from named standard baselines under one matched recipe and scoring population; superiority is a testable hypothesis, not a predicted result. C3 remains NOT_ESTABLISHED and AS-08 UNRESOLVED.
- **Primary estimand (proposal):** paired equal-domain macro Dice contrasts between BARR and each required baseline, with model selection and training-seed aggregation fixed before execution. Show G-only separately to expose downstream incremental effect.
- **Secondary estimands:** per-domain Dice, IoU/boundary metrics if predeclared and valid, seed variation, final-output harm against G, and measured compute/quality if separately instrumented.
- **Treatments/controls:** Bind U-Net, Attention U-Net, UNet++, DeepLabV3+, SegFormer-B0 and proposed-model identities/initialization in a new protocol. Freeze the actual executed loss, optimizer, LR/schedule, augmentation, channels, resolution, sampling, splits, seeds, stopping, selection and scorer. Phase09/10 one-channel and Phase21 RGB recipes cannot silently be called identical; resolve that authority conflict before launch. Any architecture exception must be prospective and change the allowed comparison label. Preserve failures, not outcome-driven family patches.
- **Eligibility:** TRAIN/VAL can be proposed for a matched but selection-consumed development benchmark. Independent performance requires separate untouched-cohort eligibility and authorization. No protected pixels or outcomes may be used to select a recipe/cohort here.
- **Statistics:** Pair cases; equal domain weights; predeclare seeds, patient/source clustering, sample-size/precision rationale, multiplicity across baselines/endpoints, missingness and empty-mask rules. Single-seed treatment versus multi-seed baseline means is not symmetric replication.
- **Confounders:** EXT-03 D1–D5 deviations, D6 post-outcome LR repair, missing logs and self-referential gates. Hash-matched checkpoints do not establish recipe fidelity; a new study cannot relabel old EXT-03 SAME_PROTOCOL.
- **Resources:** GPU training matrix and possibly new matched treatment training if the approved recipe differs from V1. No reliable future GPU-hour estimate available; approve budget and failure policy before launch.
- **Dependencies/testable claim:** Explicit approval, loaded immutable protocol and provenance checks. EXT-03B is provisional, not authorized; EXT-04 already names progression/scaling. This tests within-protocol C3/AS-08, not independent validation by itself.

## Priority 4 — BARR-M1: CPU-only descriptive reanalysis, not approved

- **Question:** How do complete A0/A1/A8 policies differ on fixed in-sample DEV? Descriptive accounting, not isolated mechanism attribution or prospective training experiment.
- **Primary estimands (frozen request):** paired equal-domain macro Dice contrasts A8-A0, A8-A1, A1-A0 over all 4,957 DEV cases with zeros on skip/reject.
- **Secondary estimands:** strict delta<0 and tolerance delta<-1e-9 counts/rates, all-population and applied-case conditional rates separately; execution/acceptance/rejection; domain/pooled summaries separate from macro. A8 accepts 1,205 after 1,239 executions and 34 rejections.
- **Treatment/control:** Exactly preserved A0 global-only, A1 always-refine, A8 canonical policy. One-to-one sample_id join, frozen scoring/fusion and input identities. No A7/new arms, model construction, forward, training, threshold fitting or checkpoint opening. RC1 source/dependencies remain frozen.
- **Eligibility:** Only digest-bound ROUTER_DEVELOPMENT n=4,957. No VAL addition, TEST, ROUTER_HOLDOUT or external data. CPU-only does not make the evidence independent.
- **Statistics (frozen request):** 2,000 paired domain-stratified resamples, seed 42; KUB patient clusters (267), per-case non-KUB because IDs unavailable; equal-domain macro in point estimator and bootstrap; strict/tolerance rates side by side; no confirmatory multiplicity claim. Abort on missing/duplicate/NaN. Unexecuted RC1 cannot repair historical Phase28 intervals.
- **Confounders:** In-sample G, selected DEV policy, multiple policy factors, missing patient grouping and conditional denominator changes. Positional joins can silently misassign membership.
- **Resources:** CPU-only frozen numeric-array aggregation/bootstrap, no GPU or model execution; no verified elapsed-time forecast.
- **Dependencies/testable claim:** Current approval=false, production inactive, anchor/time/launch absent. Independent supervisor signature plus administrator-provisioned trust/time services must precede a separate signed launch order binding exact artifacts. Eventually tests DESCRIPTIVE_DEV policy accounting only, not C1/C2/C3, patient safety or generalization.

## Priority 5 — independent generalization, separately authorized

- **Hypothesis:** Predeclared frozen G and BARR policies preserve or improve a specified segmentation endpoint on a genuinely independent, relevant cohort. Define superiority/non-inferiority/preservation and any margin prospectively; this handoff chooses none from protected outcomes.
- **Primary estimand (proposal):** paired BARR-minus-G Dice, equal-domain macro only if the approved cohort supports that target; otherwise a declared domain-specific endpoint. Never change domain weights after observing results.
- **Secondary estimands:** overlap/boundary outcomes with valid units, strict/tolerance final-output harm with explicit denominators, realized routing/acceptance, calibration, and prospectively defined subgroups. Clinical safety requires a separate patient-endpoint study.
- **Treatments/controls:** Identity-bind checkpoints, task/modality mapping, features/normalization, thresholds, precision, crop/inverse geometry and fusion; G same-protocol reference. Additional baselines require compatibility, not score-based inclusion. End-to-end inference-equivalence validation is a separate prerequisite authorization, not permission to run here.
- **Eligibility:** Audit license/consent/ethics as applicable, annotations, units, training/selection overlap, patient/source/asset duplicates, task mapping and evaluability before outcome access. An external label alone is not independence. No consumed internal population becomes pristine by relabelling; no TEST/HOLDOUT reopening from this handoff.
- **Statistics:** Freeze inclusion/exclusion, clustering, domain weights, missing/empty/undefined-boundary rules, precision/power, primary contrast/margin, multiplicity and reporting before access. Missing IDs must limit the independence claim, not be treated as distinct patients by assumption.
- **Confounders:** Domain/annotation shift, incomplete labels, target-definition mismatch, duplicate subjects/assets, referral selection, conditioning mismatch, post-outcome exclusions or recalibration.
- **Resources:** Cohort/annotation audit plus authorized frozen-model inference and scoring, no model training in the frozen evaluation track. Workload depends on cohort/hardware; no verified throughput forecast here.
- **Dependencies/testable claim:** Separate dataset/protocol/ethics and scientific approval, locked model/output identities and explicit launch order. Tests generalization only to the audited target cohort; does not retroactively clean DEV bias or establish patient safety.

## Decision-ready next step and manuscript stop

**Highest-priority next prospective question:** Does matched task-conditioned GlobalMedFiLM differ from the from-scratch identity-modulation control in the predeclared equal-domain macro endpoint? This is C1. Do not use the Phase-28 RGB-only refiner F1 as its control. Next action is real-authority review, protocol resolution and approval—not training.

Scientific priority is C1 -> C2 -> C3/AS-08 -> blocked BARR-M1 descriptive accounting -> independent generalization. This is not a strict execution dependency chain: BARR-M1 may be approved separately as lower-compute work, and independent-cohort eligibility must be established before any claim needing confirmation. It remains impossible for one approval or one successful study to settle all claims.

No experiment starts from this handoff; no manuscript v0.3. Outstanding textual corrections are in `manuscript_v0_2_targeted_errata.md`, with v0.2 byte-identical.

## Authority locators

- `reports/audits/ext03_disposition_v1_2/ext03_supervisor_memorandum_addendum_v1_2.md`: separate C1/C2/C3, matched identity control and total/trainable counts; no authorization.
- `reports/audits/ext03_disposition_v1_2/ext03_study_identifier_namespace_reconciliation_v1_2.md`: provisional EXT-03B, not EXT-04; naming is not permission.
- `reports/planning/barr_m1_approval_v1_0c/barr_m1_v1_0c_erratum.md`: component-vs-policy attribution; A7 exclusion from BARR-M1.
- `reports/planning/barr_m1_v1_0d_rc1_handoff/release_identity.json` and `reports/planning/barr_m1_v1_0d_rc1_handoff/SUPERVISOR_AUTHORIZATION_REQUEST.md`: exact pending RC1 scope, exclusions and approval/launch gates.

**All five items are proposals or blocked requests. Scientific authorization remains pending.**