# Supplement

## S1. Final system specification

Frozen system RA-MedFiLM-BARR (A8/C9), total parameters 4,837,420 (wrapper trainable
parameters: 0).

| Component | Class | Parameters | Checkpoint | SHA-256 |
|---|---|---|---|---|
| G | GlobalMedFiLM | 3,523,001 | checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` |
| B_phi | BARRBenefitRouterV1 | 36,801 | checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt | `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b` |
| R_psi | BARRRegionalRefinerV1 | 1,276,401 | checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt | `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109` |
| S_omega | BARRPostSafetyV1 | 1,217 | checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt | `eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e` |

Checkpoint replacement is not permitted; the load contract fails closed on any SHA-256
mismatch, requires strict loading with zero missing/unexpected keys, all weights finite,
all modules in eval mode with `requires_grad=False`, and CUDA-only execution.

## S2. Fusion and scoring contracts

- **D61 fusion:** canonical pad-aware `fuse_full_field(p_global, refined, geom)`; accepted
  refinements are pasted back into the full-field global probability on the original raster
  geometry with correct canvas/crop padding.
- **D75/POLICY_B scoring:** live float32 probability is persisted as float16 and scored as
  float32 against threshold >= 0.50, so all reported metrics use the exact deployed
  representation.

## S3. Phase30 qualifier

Any ROUTER_HOLDOUT-derived statement preserves the exact qualifier:

ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION

## S4. Phase39 execution history

- **v1.0 (consumed):** pre-inference MODEL_LOAD failure (D98: `NameError: name 'FEATURE_DIM'
  is not defined` in the extracted S_omega class closure). `test_inference_started=false`.
  Failure artifact SHA-256 `19e8d3f5...`; process-exit `3924c407...`; journal `65c05113...`.
- **v1.1 (consumed):** pre-inference preflight failure at stage SCIENCE_LOOP (D99:
  `PHASE39_UNEXPECTED_TASK_DOMAIN: /3`; the manifest domain was read from a non-canonical
  `domain` field instead of the canonical `dataset` column). Failure artifact SHA-256
  `e0a1ebe3...`; process-exit `4c616957...`; journal `3690d1b7...`; START `77486cdf...`.
- **Post-protocol technical-recovery amendment:** a disclosed post-protocol amendment (not a
  retroactive reinterpretation of the frozen Phase38 retry policy) repaired D98 and D99 and
  bound the v1.0+v1.1 history.
- **v1.2 (successful, descriptive):** evaluated the frozen system on all 1,683 TEST samples.
  Result artifact SHA-256 `b9d5c74a316839cace0d085f3a8330f0378755687c6e0b67635371280896959d`;
  process-exit `717c065f...` (exit code 0); journal `5803fcc8...`; START `46f109ae...`.
  Per-sample table `reports/tables/phase39_final_test_v1_2/per_sample.csv`
  (`819728d4...`, 1683 rows); per-domain `per_domain.csv` (`f2ec55ca...`).

## S5. Phase39 adjudications

- **Completeness adjudication** (`reports/audits/phase39_v1_2_scientific_protocol_completeness_adjudication.json`,
  SHA-256 `78a6ead5...`): the frozen primary comparative endpoint is
  `NOT_DERIVABLE_WITHOUT_NEW_TEST_INFERENCE`; the frozen v1.2 execution emits only
  final-system Dice.
- **Publication-scope adjudication** (`reports/audits/phase39_publication_scope_adjudication.json`,
  SHA-256 `96a585aa...`): descriptive TEST only; the primary comparator endpoint remains
  missing.

## S6. Phase40 reduced-scope policy

Phase40 was manuscript assembly only under
`MANUSCRIPT_ASSEMBLY_WITH_DESCRIPTIVE_PHASE39_TEST_ONLY` (scientific_delta = 0). This
release is a read-only scientific freeze of the Phase40 manuscript (scientific_delta = 0).
No TEST access, inference, training, metric calculation, statistical calculation, bootstrap,
comparator reconstruction, endpoint reconstruction, threshold change, or claim strengthening
was performed.

## S7. Provenance anchors

- Phase37 evidence consolidation manifest: `reports/audits/phase37_sha256_manifest.json`
  (SHA-256 `221a918b...`, 28 artifacts).
- Phase38 protocol freeze manifest: `reports/audits/phase38_sha256_manifest.json`
  (SHA-256 `ebb61b9f...`, 37 artifacts).
- Phase40 terminal manifest: `reports/audits/phase40_sha256_manifest.json`
  (SHA-256 `9a7fb906...`, 17 artifacts).

The supplement is not used to hide the missing Phase39 primary comparative endpoint; the
limitation is disclosed in the main text (Section 6).
