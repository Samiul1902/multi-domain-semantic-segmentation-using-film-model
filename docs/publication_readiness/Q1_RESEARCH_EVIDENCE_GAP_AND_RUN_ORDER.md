# Q1 Research Evidence Gap and Run Order

**Status:** `DECISION_MATERIAL__PLANNING_ONLY__NO_EXECUTION_AUTHORISED`
**Revision:** `RA_MEDFILM_BARR_PUB_READINESS_EVIDENCE_V1_0`
**Repository HEAD:** `45b85c1`
**Frozen protocol SHA-256:** `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61`

---

## 1. Preserved historical evidence (immutable)

| Phase | Evidence | Population | Status |
|---|---|---|---|
| 21 | Six-model comparison (Dice/IoU, per-domain, paired bootstrap) | VAL808 | COMPLETE |
| 27 | Multi-domain preservation (Δ +0.00221 [+0.00113, +0.00330]) | VAL808 | COMPLETE |
| 28 | 13-arm ablation + paired contrasts with 95% CI | ROUTER_DEVELOPMENT 4,957 | COMPLETE |
| 29 | Three-seed descriptive reproducibility | VAL808 | COMPLETE (no pass/fail gate) |
| 30 | ROUTER_HOLDOUT one-shot (Δ +0.00174 [+0.00112, +0.00240]) | 875 | COMPLETE WITH DISCLOSED DEVIATION |
| 33 | Failure and boundary analysis | 875 | COMPLETE |
| 34 | Efficiency and memory (SYNTHETIC_BENCHMARK) | fixture | COMPLETE |
| 35 | Interpretability (descriptive mechanism) | VAL808 | COMPLETE |
| 36 | Robustness (synthetic perturbations) | VAL808 | COMPLETE |
| 39 | Descriptive TEST1683 (macro Dice 0.8314) | TEST 1,683 | CONSUMED, ONE-SHOT |

None of these is rewritten, reclassified or retroactively declared preregistered.

---

## 2. Evidence gaps that block a Q1/A* submission

| Claim | Current evidence | Missing | Status |
|---|---|---|---|
| **C1 FiLM attribution** | Design + matched-arm constructor + synthetic chain | 6 genuine C1-T/C1-C runs | `NOT_ESTABLISHED` |
| **C2 router/safety/refiner attribution** | 13-arm ablation, in-sample | A causal/pre-registered framing and publication packaging; the frozen matrix is a policy comparison | `PARTIAL__IN_SAMPLE` |
| **C3 protocol-faithful baselines** | Six PROTOCOL_INCOMPARABLE historical records | 24 protocol-matched cells (8 models × 3 seeds) | `NOT_ESTABLISHED` |
| **Independent external test** | 884-case retrospective, prior-used cohorts | A genuinely independent, subject-nonoverlapping cohort | `NOT_ESTABLISHED` |
| **Data permissions** | Manuscript claim only | Licence/ethics determination per cohort | `HUMAN_DETERMINATION_REQUIRED` |

---

## 3. Execution order (gated, no automatic progression)

```
GATE 0  Authorization satisfied (protocol approved + policy + execution surface)
  │
  ├─ C1  six runs (2 arms × 3 seeds)        ← publication-critical #1
  │     seed 42 first; 123/3407 only after 42 passes QC
  │
  ├─ C2  frozen 13-arm re-aggregation       ← publication-critical #2 (0 new runs if artifacts accepted)
  │
  ├─ C3  24 protocol-matched cells          ← publication-critical #3
  │
  └─ EXT independent external cohort        ← publication-critical #4 (protocol frozen before opening images)
```

Each gate requires a human sign-off. Failure at any gate stops the sequence; no recipe change, no restart for score, no best-seed substitution.

---

## 4. C1 — FiLM attribution (six genuine runs)

| Item | Specification |
|---|---|
| **Hypothesis** | Learned task-conditioned FiLM (C1-T) improves macro-domain Dice over a frozen identity-FiLM control (C1-C) at identical initial backbone weights. |
| **Population / dependencies** | TRAIN5832 for optimisation, VAL808 for checkpoint selection and evaluation. TEST1683, ROUTER_HOLDOUT875, EXTERNAL884 and QUARANTINE are prohibited. Depends on the frozen GlobalMedFiLM architecture (`a04ff3e6…`) and the frozen protocol. |
| **Comparator / estimand** | C1-C is the comparator. Primary estimand: **seed average of the paired equal-domain macro Dice (T − C) on selected VAL**. Secondary: per-domain Dice and IoU. |
| **Required independent runs** | **6**: C1-T and C1-C × seeds 42, 123, 3407. Seed 42 first; seeds 123/3407 only after seed 42 completes and passes QC. |
| **Metrics** | Per-epoch train/val loss; best-epoch per-image Dice, IoU, precision, recall; per-domain and macro-domain Dice/IoU; HD95 (see output gap). |
| **Paired statistics** | 10,000 domain-stratified paired cluster percentile bootstrap, seed `20261027`, 95% CI; KUB clustered by `patient_id`, non-KUB image-level with unavailability disclosed. Report all three paired seed effects (mean, sample SD, range); **no population seed inference**. |
| **Failure handling** | STOP on failure; no recipe change; resume the **same** run only after a recovery review; `no_primary_claim_until_all_six_runs_complete`. |
| **Exact entry point** | **No authorized production CLI exists.** The RC4 draft preflight is `scripts/analysis/run_c1_campaign_launch_rc4_draft.py` (no `--execute`). The RC3 CLI `scripts/analysis/run_c1_campaign_launch.py --execute` is **defective and must not be used**. The RC4 library entry is `src/research/c1_film_launch_rc4/launch_driver_rc4.py::launch(arm, seed, ...)`. |
| **Outputs for the paper** | Epoch history; best epoch; train/val loss curves; Dice-vs-epoch; per-domain T vs C; paired ΔDice forest; checkpoint SHA-256; run identity and provenance; parameter/trainable counts. |

### 4.1 Output-schema gap (must be fixed prospectively, not after outcomes)

The frozen trainer persists **per-epoch history** and **best-epoch per-image Dice/IoU/precision/recall only**. It does **not** persist:

- predicted masks,
- HD95 / ASSD,
- per-image metrics at non-best epochs,
- explicit resume events,
- per-epoch wall-clock or GPU memory,
- the launching release identity.

**Minimum compatible prospective amendment (PROPOSED_NOT_APPROVED, not implemented):** an append-only `events.jsonl` written by the launcher, plus a pre-specified best-checkpoint re-inference pass on VAL808 to produce masks and boundary metrics. This changes **outputs**, not the training recipe, populations or endpoint. It must be frozen **before** training to avoid post-hoc metric selection.

---

## 5. C2 — component progression / ablation

| Item | Specification |
|---|---|
| **Hypothesis** | Each of regional refinement, routing and post-safety contributes to the accuracy/harm trade-off; the p_global channel is functionally necessary; A8 reduces harm relative to always-refine at a matched budget. |
| **Population / dependencies** | ROUTER_DEVELOPMENT (4,957), fixed budget K = 1,239. Frozen canonical bundle `f7aebb0f…`; A0–A8 reused from frozen artifacts; R1–R3 and F1 are Phase-28 trained variants. |
| **Comparator / estimand** | A0 (global-only) and A1 (always-refine) endpoints; A2–A5 routing-signal comparators; A6→A7→A8 component progression; R1–R3 and F1 variants. Estimand: mean routed ΔDice, harmful activation share, paired difference with 95% CI. |
| **Required independent runs** | **0 new runs** if the frozen Phase-28 artifacts are accepted. If regenerated: 15 router folds (R1–R3 × 5) + 3 F1 folds = **18 folds**. |
| **Metrics** | ΔDice (routed), sum ΔDice, beneficial/harmful counts, harmful share, benefit capture, paired differences, analytical compute. |
| **Paired statistics** | Paired bootstrap, 2,000 replicates, seed 42; **only A7_vs_A8 is a frozen matched contrast**; R1–R3/F1 are descriptive, no post-hoc correction. |
| **Failure handling** | No policy retuning; membership fixed; no threshold change; frozen bundle unchanged. |
| **Exact entry point** | `scripts/analysis/train_phase28_router_variant.py --variant R1/R2/R3`; `scripts/analysis/eval_phase28_f1.py`; `scripts/analysis/eval_phase28_f1_integrated.py`; `scripts/analysis/build_phase28_matrix.py`; `scripts/analysis/build_phase28_tables_stats.py`; `scripts/analysis/c2_barr_aggregator.py`. |
| **Outputs for the paper** | 13-arm table; paired-contrast forest with CIs; harmful-share panel; compute accounting; explicit statement that this is in-sample relative to TRAIN and is a **policy comparison, not a causal ablation**. |

**Budget nuance:** A8 has `n_routed = 1,205` because 34 executed rows were rejected by S_ω; the K = 1,239 match is nominal for A8 and must be disclosed.

**Non-pooling rule:** C2 must never pool VAL808 (selection-consumed), ROUTER_DEVELOPMENT (in-sample), ROUTER_HOLDOUT875 (disclosed deviation) or the 884 external cohort. The 14/14 stone-free false-positive failure is retained.

---

## 6. C3 — eight configurations × three seeds

| Item | Specification |
|---|---|
| **Hypothesis** | Under one protocol, the multi-domain FiLM/BARR family is competitive with conventional baselines; FULL and Lite expose a defensible accuracy–cost trade-off. |
| **Population / dependencies** | TRAIN5832 for training, VAL808 for selection. Eight configurations: `FULL`, `LITE`, `GLOBAL`, `UNET`, `ATTENTION_UNET`, `UNETPP`, `DEEPLABV3PLUS`, `TRANSFORMER_MIT_UNET`. Seeds 42, 123, 3407. |
| **Comparator / estimand** | `GLOBAL` as the same-family reference; conventional baselines as architectural comparators. Estimand: macro-domain Dice difference (paired, domain-stratified); descriptive for baselines. |
| **Required independent runs** | **24 cells** (8 × 3). All real comparative cells are currently missing. |
| **Metrics** | Dice, IoU, precision, recall, HD95; parameters; analytical GMACs. |
| **Paired statistics** | Per-seed paired domain-stratified bootstrap; report all three seeds (mean, SD, range); no best-seed headline; no leaderboard. |
| **Failure handling** | Fails closed without a launch grant; `--resume` only; no protocol change. |
| **Exact entry point** | `scripts/analysis/stage6_eight_model.py baseline-run --model <M> --seed <S> [--resume] [--grant-provider MODULE:CALLABLE]`. Inspection: `cells`, `aggregate`, `audit-inference`. |
| **Outputs for the paper** | 24-cell matrix with per-cell checkpoint SHA; aggregate results; accuracy-vs-cost figure; explicit comparability labels. |

**Current reporter behaviour:** the C3 reporter emits **six `PROTOCOL_INCOMPARABLE` historical records**, an **empty protocol-matched section** and **no leaderboard**. Historical single-run baseline scores must never be relabelled as protocol-matched.

---

## 7. Independent external testing (replaces the consumed TEST)

TEST1683 is **consumed**; it is not "untouched" and must not be reopened or reclassified. A new external cohort must satisfy all of the following **before any image is opened**:

1. **Source independence** — a dataset not used in the prior MedFiLM-Seg programme and not overlapping TRAIN/VAL/TEST/ROUTER_DEVELOPMENT/ROUTER_HOLDOUT.
2. **Subject-level nonoverlap** — hash-level file comparison plus patient/case/source-group key comparison; report the overlap audit.
3. **Reference-standard policy** — one frozen annotation semantics (binary foreground), frozen empty-mask rule (both-empty Dice/IoU = 1.0; one-empty = 0.0), HD95 undefined unless both non-empty.
4. **Permissions** — a licence/DUA that permits evaluation and publication; recorded before inference.
5. **Fixed preprocessing and thresholds** — the frozen V1 pipeline (`phase36_robustness_execution_v1_23.py`, SHA `2287cc78…`, `_load_clean_image_tensor`/`_load_val_gt`); segmentation 0.50, ROI 0.30, safety 0.50; no recalibration.
6. **Zero test-guided tuning** — no model selection, threshold tuning, prompt/architecture change or recalibration after seeing external outcomes; a single evaluation pass per frozen model.
7. **Clinical domain-shift evaluation** — report each cohort separately; no combined "independent" macro across mixed provenance; disclose modality and acquisition differences.
8. **Negative-case false-positive analysis** — stone-free / `Normal_NoStone` and other negative cases reported explicitly, including the historical 14/14 stone-free failure pattern.
9. **Per-domain and subgroup CIs** — cluster-aware bootstrap (10,000 replicates), subject-level clusters where linkage exists, image-level otherwise, with the unit disclosed.
10. **Pre-registration** — cohort, exclusions, selection rule and metrics frozen and hashed **before** access; deterministic ID-based or GT-morphology case selection, never best/worst after outcomes.

**Access rule:** no candidate external image may be opened, listed or previewed until items 1–10 are frozen. This document does not open any.

---

## 8. CLAIM 2024-aligned manuscript evidence checklist

Reference: CLAIM 2024 update (Tejani, Klontzas, Gatti et al., *Radiology: Artificial Intelligence* 2024;6:e240300). The 2026 explanation referenced in the brief could not be independently verified in this environment; the checklist below follows CLAIM 2024 item domains and the eleven areas requested, and should be re-checked against the official checklist before submission.

| # | Requirement | Status | Evidence / blocker |
|---|---|---|---|
| 1 | Clearly defined contribution and novelty | **PARTIAL** | Architecture and matched-arm design documented; the causal FiLM claim is pending C1. |
| 2 | Fair baselines | **PENDING** | C3 has 0/24 protocol-matched cells; historical baselines are `PROTOCOL_INCOMPARABLE`. |
| 3 | FiLM attribution | **PENDING** | C1 has 0/6 runs; authorization unsatisfied. |
| 4 | Router and safety attribution | **PARTIAL** | 13-arm in-sample policy comparison; only A7_vs_A8 pre-registered; not causal. |
| 5 | Reproducibility | **PARTIAL** | Three seeds vary downstream only (shared frozen backbone); no pass/fail gate; no public code/DOI. |
| 6 | External testing | **PARTIAL** | 884-case retrospective, prior-used cohorts; no independent cohort. |
| 7 | Negative results | **ESTABLISHED** | 14/14 stone-free foreground failure and 390 harmful refinements retained. |
| 8 | Failure cases | **ESTABLISHED** | Phase 33 low-overlap 10.06%, harmful 12.92%, missed benefit 0%; qualitative gallery INELIGIBLE. |
| 9 | Computational cost | **PARTIAL** | Analytical MACs and synthetic latency; no real training cost; BARR A8 ≈1.028× Global analytical cost. |
| 10 | Data permissions | **PENDING** | No licence/DUA record; manuscript admits licence verification not satisfied; KUB conflict. |
| 11 | Reproducible model/code documentation | **PARTIAL** | Frozen manifests/checkpoints/SHAs exist; no public repository, DOI, licence or data/code availability statement. |

---

## 9. What must not happen

- Do not retroactively label the historical six-model comparison, the 13-arm ablation or the Phase-30 holdout as preregistered confirmatory tests.
- Do not reopen TEST1683 or call it untouched.
- Do not pool VAL808, ROUTER_DEVELOPMENT, ROUTER_HOLDOUT and EXTERNAL.
- Do not select the best seed for the headline.
- Do not tune on external or TEST outcomes.
- Do not change the recipe, seeds, splits or endpoint to improve a result.
- Do not create another coding phase to work around the authorization or output-schema gaps.

---

## 10. Stop conditions

The sequence stops at **GATE 0** until the human decisions in `SUPERVISOR_ACTION_REQUEST.md` are made. No training, no external access and no protocol edit occur before that gate.
