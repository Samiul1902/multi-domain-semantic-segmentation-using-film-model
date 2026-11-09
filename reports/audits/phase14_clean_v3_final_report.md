# PHASE 14 clean-v3 — SUPERVISOR RULING (OPTION B) — FINAL REPORT

**Generated (UTC):** 2026-09-25T00:12:45Z
**Authoring mode:** Prospective ADDITIVE clean-v3 diagnostic amendment (ruling OPTION B).
**Status:** Phase-14 adjudication complete. **Phase 15 = NOT_STARTED (honored; not started in this task).**

---

## §1 — Preservation of all existing frozen evidence (ADDITIVE ONLY)
- No pre-existing frozen artifact was modified in value. All prior evidence — protocol amendment, freeze manifest, training artifacts, checkpoint-selection replay, v2-era references, prior audits — is preserved.
- TEST and external TEST remain **CLOSED**. Governance locks in the §8 audit: `test_split_reads = 0`, `external_data_used = false`, `training_executed = false`.
- This amendment is strictly additive: new clean-v3 population, bindings, references, evaluator, and diagnostic artifacts were *added*; nothing executable from prior phases was overwritten.

## §2 — Frozen clean-v3 diagnostic population
- **Executable population:** 103 FULL_FIELD images / 152 authoritative components / size strata TINY 72 · SMALL 28 · MEDIUM 36 · LARGE 16.
- **Frozen special sets:** hard-tiny = **15 components (13 unique images)**; global-empty = **5 images**.
- **Manifest/table SHAs bound** in `phase14_clean_v3_population_freeze.json`; ordered identifiers recorded.
- **Provenance note (transparent discrepancy):** the ruling text cited hard-tiny 16 / global-empty 7. Those are the **v2-era** values and are recorded as `PRESERVED_FOR_PROVENANCE_ONLY — NOT the executable population`. The executable clean-v3 denominators are **15 / 5**, derived from the clean-v3 GLOBAL UNet++ checkpoint + `kub_size_clean_v3_v1` thresholds (verified independently; 0 of the 16 v2 hard-tiny and 0 of the 7 v2 global-empty fell in the 3 dropped images, so the difference is model/threshold redefinition, not a drop artifact). The classification verdict is denominator-independent (see §9).

## §3 — Prospective checkpoint binding by path + SHA
- **GLOBAL:** `checkpoints/phase10_kub_unetpp_seed42_512_clean_v3/best.pt` — SHA `ec7eb13f…`
- **REGIONAL refiner (epoch 56):** `checkpoints/phase14_kub_refiner_unet_a3_256_seed42_clean_v3/best.pt` — SHA `2e09e3a9…` (matches ruling; checkpoint file stores `epoch: 56`).
- **LOCALIZER (Stage-4D):** `checkpoints/phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3/best.pt` — SHA `7673c34a…`
- All three SHAs are **re-verified by the evaluator before inference** (`assert sha == expected`, lines 92–94). No alternate checkpoint/epoch used.

## §4 — Gate algebra preserved
- Step 1: `G >= 0.05 AND Do >= 0.632776` (Refiner Potential)
- Step 2: `R >= 0.50` (Proposal Retention, if G > 0)
- Step 3: `Tp >= 0.780822 AND Dp >= 0.632776 AND Hard-Tiny >= 2/N AND Global-Empty >= 1/M` (Practical Net Benefit)
- Only the **population-dependent GLOBAL references** (Tg/Dg) were remeasured, as §4 permits. Hard-tiny/global-empty clause denominators are the executable clean-v3 values 15 / 5.

## §5 — Prospective Tg_clean_v3 / Dg_clean_v3 derivation (frozen BEFORE Oracle/Predicted)
- Procedure frozen in `phase14_clean_v3_reference_procedure_freeze.json` **before** any Oracle/Predicted inference.
- Identical metric definitions, threshold, matching, strata, and preprocessing as the original. **NOT** `val_macro_dice = 0.764160…`.
- Oracle/Predicted results were **not** inspected first.

## §6 — GLOBAL references generated ONCE and FROZEN
- `phase14_clean_v3_global_reference_freeze.json` — `status: FROZEN`.
- `Tg_clean_v3 = 0.7916666666666666`, `Dg_clean_v3 = 0.6359172411726776`.
- Full precision, counts (103 forwards), checkpoint SHA, evaluator SHA, `TEST = 0`, `external TEST = 0`.
- **Transparent post-freeze amendment:** the recorded `evaluator_sha256.main_evaluator` was updated to the corrected evaluator SHA (`53958eb1…`) after the §7 governance correction; **Tg/Dg values are unchanged**. No favorability-driven rerun.

## §7 — Evaluator frozen & hashed prospectively
- `phase14_clean_v3_evaluator_binding.json` — `status: BOUND_PROSPECTIVE`.
- Evaluator SHA `53958eb1…` + 12 dependency SHAs + frozen operational config (oracle margin 0.20; predicted threshold 0.10, margin 0.20, top_k 5, NMS 0.30; fusion MAX `DIRECT_REPLACEMENT_IN_PROPOSAL_UNION` at 0.50; global threshold 0.50). Metric/fusion semantics unchanged from v2.

## §8 — Frozen three contrasts run (exactly once, + one transparent governance re-run)
- The frozen evaluator `evaluate_phase14_clean_v3_diagnostic.py` was executed once (2026-09-25T00:10:56Z, EXIT=0, ~2m17s). No search/grid/sweep/alternate checkpoint/rerun/post-hoc edit/TEST.
- **One corrective re-run was performed** after discovering two stale v2-era constants in the adapted source: the audit `regional_unet.epoch` (14 → 56, to match the §3 binding) and console/comment denominators (16/7 → 15/5, to match the executable special-set denominators). The numeric verdict is **denominator-independent and unchanged** (DIAGNOSTIC_PROPOSAL_BOTTLENECK). This is documented as a governance correction, not a favorability rerun.

## §9 — Formal adjudication (per-clause; see `phase14_clean_v3_formal_adjudication.json`)
| Step | Clause | Numerator / Denominator | Delta | Threshold | Result |
|------|--------|------------------------|-------|-----------|--------|
| 1 | G = To − Tg | To 72/72, Tg 57/72 | +0.208333 | ≥ 0.05 | **PASS** |
| 1 | Do (Oracle FULL_FIELD Dice) | 0.802416 | +0.169640 | ≥ 0.632776 | **PASS** |
| 2 | R = (Tp − Tg)/G | (0.791667−0.791667)/0.208333 = 0.0 | 0.0 | ≥ 0.50 | **FAIL** |
| 3 | Tp | 0.791667 | +0.010845 | ≥ 0.780822 | **PASS** |
| 3 | Dp (Predicted FULL_FIELD Dice) | 0.418531 | −0.214245 | ≥ 0.632776 | **FAIL** |
| 3 | Hard-Tiny | 0 / 15 | — | ≥ 2 | **FAIL** |
| 3 | Global-Empty | 1 / 5 | — | ≥ 1 | **PASS** |

- **Overall:** Step 1 PASS, Step 2 FAIL, Step 3 FAIL.
- **Classification:** `DIAGNOSTIC_PROPOSAL_BOTTLENECK` — the refiner potential exists (Oracle is perfect: To=1.0, Do=0.8024, hard-tiny 15/15, global-empty 5/5) but the frozen Stage-4D PREDICTED proposal pipeline yields **zero net Tiny-recall gain** (R = 0), so proposals are the bottleneck.
- **Phase 15 status:** `NOT_AUTHORIZED` (Phase 15 requires a passing gate chain / `DIAGNOSTIC_PROMISING_SUPPORTING_REFINER`).

## §10 — Descriptive v2 cross-population comparison (NOT formal adjudication)
- Artifact: `phase14_clean_v3_v2_cross_population_descriptive.json`, labelled `DESCRIPTIVE_CROSS_POPULATION_ONLY__NOT_FORMAL_ADJUDICATION`.
- v2-era (106/156, 73/29/36/18, hard-tiny 16, global-empty 7): To=1.0, Tp=0.8904, Do=0.8152, Dp=0.3839, G=0.2192, **R=0.50**, Step 2 PASS, Step 3 FAIL → `DIAGNOSTIC_PRACTICAL_SIGNAL_INSUFFICIENT`.
- clean-v3 (103/152, 72/28/36/16, hard-tiny 15, global-empty 5): To=1.0, Tp=0.7917, Do=0.8024, Dp=0.4185, G=0.2083, **R=0.0**, Step 2 FAIL, Step 3 FAIL → `DIAGNOSTIC_PROPOSAL_BOTTLENECK`.
- Both populations: Oracle mode identical; Predicted mode is the divergent axis; both yield `phase15_status = NOT_AUTHORIZED`. The clean-v3 shift (R 0.5→0.0) reflects a proposal-supply bottleneck, not a refiner regression.

## §11 — Required final report + Phase 15 status
1. All frozen evidence preserved; TEST/external TEST CLOSED. ✅
2. clean-v3 population frozen (103/152; 15/5 special sets; 16/7 v2 preserved for provenance). ✅
3. Checkpoints bound by path+SHA; all verified before inference. ✅
4. Gate algebra preserved; only population-dependent GLOBAL refs remeasured. ✅
5. Tg/Dg derivation frozen prospectively before Oracle/Predicted. ✅
6. GLOBAL references generated once, FROZEN. ✅
7. Evaluator frozen & hashed prospectively. ✅
8. Three contrasts run (once, + transparent governance re-run). ✅
9. Formal per-clause adjudication → `DIAGNOSTIC_PROPOSAL_BOTTLENECK`, `NOT_AUTHORIZED`. ✅
10. Descriptive v2 cross-population comparison provided, explicitly non-adjudicative. ✅
11. This 11-item report returned. ✅

**PHASE 15:** remains **NOT_STARTED**. Per the ruling's closing constraint ("Stop after Phase-14 adjudication. Phase 15 must remain NOT_STARTED." and "Do NOT start Phase 15 in this task."), **no Phase 15 work was performed** in this task.
