# Targeted manuscript v0.2 errata — claims reconciliation

**Additive correction only; no manuscript bytes or scientific measurements changed.** Applies to `D:\Softfors\jup\reports\manuscript_draft\RA_MedFiLM_BARR_manuscript_v0_2.md`, SHA-256 `E0BF9954B2BBF8A38EBC5394A434446D8CA9689D958443D2CEABC747FE6E704E`. Exact passages/section anchors below refer to that immutable file. This is not a new manuscript version, evaluation or authorization.

## Residual passages requiring correction

### E-01 — Abstract, Evidence-qualified results (C-14)

**Passage:** “its paired mean difference was 1.5717229e-05 with a 95% bootstrap interval crossing zero.”

**Required qualification:** State “original all-case paired **pooled** mean difference on ROUTER_DEVELOPMENT, with zero fallback contributions; recorded **case-resampled** percentile interval crossing zero.” It is not equal-domain macro and not patient-clustered/domain-stratified. The current body correctly supplies this distinction; the abstract's proximity to the macro A8 value risks assigning the pooled interval to that macro endpoint. No positive effect or equivalence is established.

**Authority:** `reports/tables/phase28_table_07_matched_paired_contrasts.csv` and `reports/tables/phase28_table_08_bootstrap_statistics.csv`, row A8_vs_A7; `scripts/analysis/build_phase28_tables_stats.py`, matched-loop lines 287–337.

### E-02 — Results 5.4, opening sentence (C-16)

**Passage:** “Phase-28 executed 13 arms and 18 new training runs ... fixed at nominal budget 0.25 and K=1,239”.

**Required qualification:** The selective nondegenerate operating point is 0.25/K=1,239; A0 is the no-refinement endpoint, A1 is all 4,957 candidate applications, and A8 accepts 1,205 of 1,239 executions. The matrix combines constructed/prior rows with new R1/R2/R3/F1 variants; it does not represent thirteen freshly trained full systems. Adjacent per-arm details do not make the phase-wide shorthand uniform.

**Authority:** `reports/tables/phase28_table_02_arm_primary_metrics.csv`, arm/evidence_class rows; `reports/audits/barr_m1_v1_0b_phase28_chronology_audit.json`, A0_A1_A8_provenance; `reports/audits/barr_m1_v1_0c_precision_audit.json`, clarifications.4_execution_vs_acceptance.

### E-03 — Results 5.5, first sentence (C-17)

**Passage:** “Phase-29 retrained downstream ... stacks for seeds 42, 123, and 3407”.

**Required correction:** Say “Phase-29 **represents three trained/retrained downstream stacks**; the seed-42 canonical replicate was reused, while the new downstream seeds were 123 and 3407. All use the same frozen G seed-42 checkpoint.” Do not imply a fresh Phase-29 seed-42 training or full-system three-seed replication. Fixed-G caveat is already correct in the passage and remains mandatory.

**Authority:** `reports/audits/phase29_execution_entry_gate.json`, seed42_role=REUSE_EXISTING_CANONICAL_REPLICATE; `reports/audits/phase29_fixed_global_reference_binding.json`, global_checkpoint_identical_across_seeds/G_trained.

### E-04 — Discussion 7.4, second sentence (C-13/C-14)

**Passage:** “the matched bootstrap contrast is inconclusive and its metric is segmentation harm, not patient safety.”

**Required correction:** The matched interval's metric is **pooled paired Dice change**. Separate it from the descriptive count of strict harmful replacements. Suggested wording: “The pooled paired Dice interval is inconclusive; the separately reported harm counts concern Dice decreases, not patient safety.” The first part of the section correctly identifies an existing matched decision-stage design; do not erase it or claim none exists.

**Authority:** Table08 A8_vs_A7, mean_difference; `reports/audits/phase25g_final_freeze.json`, budget 0.25 harm counts.

### E-05 — Section 12 and opening evidence-boundary ledger reference

**Passage:** original `claims_to_evidence.md` and the critical audit are named as the claim ledger, but the newly adjudicated matrix is not yet named.

**Required additive reference:** Use `reports/manuscript_draft/claims_to_evidence_v0_2_adjudicated.md` plus this errata as the reconciled interpretation. Preserve the original matrix as provenance, not as endorsement of C-14/C-17 affirmative claim text. No manuscript overwrite or v0.3 is needed to record this update.

## Consistency disposition for the rest of v0.2

- Contribution statements are scoped to implementation/provenance and do not establish novelty or causal benefit.
- The existing A0/A1/A7/A8 harm-count table distinguishes selected/executed from accepted, strict from tolerance-adjusted harm and denominators; its values are recorded descriptive audits, not an executed BARR-M1 result.
- Methods disclose canonical ROI030 authority, TRAIN-fitted G, non-nested selector hierarchy, constant-cost fixed-budget redundancy and wrapper-equivalence limitation. Do not upgrade those caveats.
- F1 primary/secondary outcomes remain descriptive; the secondary membership-label inconsistency already noted in v0.2 is not resolved by a new computation here.
- Discussion, Limitations and Conclusion correctly keep C1/C2/C3 NOT_ESTABLISHED, AS-08 UNRESOLVED, independent generalization and clinical safety unestablished, and BARR-M1 not approved/unexecuted.

**Scope of closure:** The ledger inconsistency is reconciled by new additive records. The five identified passage qualifications remain documented errata in the preserved manuscript; this does not repair scientific evidence gaps. Manuscript iteration stops and experimental priorities pass to `experimental_research_handoff_v0_2.md`. No new scientific execution is authorized.
