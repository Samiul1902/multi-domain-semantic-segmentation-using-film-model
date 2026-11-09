# Phase 23 — Literature & Methodological Novelty Audit

**A systematic prior-art audit of the provisional candidate contribution, conducted BEFORE architecture freeze or any implementation.**

No training. No model modification. No segmentation inference. No TEST access. No Phase-24 implementation.

| Item | Value |
|---|---|
| Phase | 23 — Literature & Methodological Novelty Audit |
| Search date | 2026-09-29 |
| Predecessor terminal state | `PHASE22_CANONICAL_IPYNB_MATERIALIZED__VISUAL_INTEGRITY_PASS__SCIENCE_UNCHANGED__PHASE23_ELIGIBLE_NOT_STARTED` |
| Entry gate | `PHASE23_ENTRY_GATE_PASS` (21/21) |
| Search families run | A–M (13 families, 63 logged queries) |
| Records screened | ~401 |
| Papers retained (authoritative) | 30 in the matrix; 16 deep-compared; 22 logged exclusions |
| **Overall novelty label** | **`PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE`** |
| Maximum defensible claim level | **Level 2**, scoped strictly to the unoccupied combination (Level 3 **not** defensible) |
| Provisional method name | `RENAME` — "Counterfactual Benefit-Certified Refinement" is **TOO_STRONG** on two words |
| Phase 24 | **ELIGIBLE, NOT STARTED** — narrowed architecture specification only |
| TEST | CLOSED — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Terminal state | `PHASE23_NOVELTY_AUDIT_COMPLETE__PARTIALLY_OCCUPIED__PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED` |

---

## 1. Scope and the question asked

Phase 23 asks a single question, and deliberately does **not** ask a weaker one.

It is **not** "has uncertainty-guided refinement existed?" — that has existed for years and is treated as occupied from the outset.

It asks: **has the expected paired benefit of an *optional* segmentation intervention been explicitly *learned* BEFORE that intervention is executed, and used for performance-preserving, resource-aware routing?**

The provisional candidate ("Counterfactual Benefit-Certified Refinement") was decomposed into seven testable factors:

1. a frozen/global pathway produces an initial result;
2. an **optional** refinement exists;
3. **before** executing it, the system predicts its expected improvement;
4. the target is the **paired** quantity `DeltaQ = Q(refined, GT) − Q(global, GT)`;
5. the prediction gates **execute vs skip**;
6. a **harmful** refined output can be rejected so the global prediction is preserved;
7. routing may include compute/device/resource cost, in shared multi-domain medical segmentation, with deployment efficiency as a design objective.

## 2. Entry gate (fail-closed)

`reports/audits/phase23_entry_gate.json` — **21/21 PASS**. Verified before anything else ran:

- `phase22_final_freeze.json` byte-identical (`9a0aa2f8…`);
- `phase22_diagnostic_protocol.json` byte-identical (`9d620d6c…`);
- Phase-21 `best.pt` byte-identical (`286689fdd…`);
- Phase-21 macro VAL Dice unchanged (`0.8350794169575282`);
- combined audit `74/74`, all four historical terminal states present;
- GT-free and GT-aware evidence tables present;
- the future-benefit-label contract is `CONTRACT_PROPOSED_NOT_IMPLEMENTED` and **not** a training artifact;
- canonical Phase-22 notebook at `cca76123…`;
- **no** pre-existing `phase23_*`/`phase24_*` artifacts; Phase-22 figure root intact (15 PNG).

One gate bug was found and fixed during development (the TEST-lock field lives under `governance.test_locks` in the freeze, and the gate's own output file tripped the clean-start check); the gate is now self-consistent.

## 3. Search protocol and reproducibility

Thirteen query families were run (A–J per the brief, plus **K falsification-first**, **L general-CV precedence**, **M patent scan**), logged in `phase23_search_log.json` (63 queries) and summarised in `phase23_search_query_summary.csv`.

Two families were purpose-built to **falsify** the novelty claim and were run *after* the affirmative families, so any close equivalent would surface rather than be hidden. Databases reachable in-session: arXiv, CVF Open Access, SpringerLink, ACM DL, IEEE records, Google Scholar via the search provider, and a limited Google Patents scan. Semantic Scholar / Crossref / ScienceDirect / IEEE **full text** were **not** directly reachable (no API keys / paywalls) — this limitation is recorded in the search log, and unverifiable items were excluded rather than cited.

## 4. The four novelty axes

### AXIS A — Problem formulation — **OCCUPIED**

The exact question *"was the refinement worth it, or should we keep the coarse mask?"* is explicitly posed and answered in segmentation by **JFS** (Moon et al., ICIP 2025, arXiv:2407.04519), whose abstract states it addresses the gap that *"no method has been developed that can determine the success of segmentation refinement."* The abstract form of the same question is formalised in **metareasoning** (Russell & Wefald, 1991). **No residual novelty at the level of problem formulation.**

### AXIS B — Learning target — **NOT OCCUPIED as a learned segmentation target**

No verified segmentation paper trains a supervised regressor on the paired, GT-derived Dice gain of a refinement. JFS performs a *paired comparison* but only as an untrained decision; LFPC optimises an **implicit RL reward**, not a supervised paired regression. **However**, the *formal* target `E[Y(1) − Y(0) | x]` is textbook causal-inference machinery (**CATE meta-learners**, Künzel et al., PNAS 2019). The formal target is not novel; the segmentation instantiation is the residual.

### AXIS C — Decision mechanism — **PARTIALLY OCCUPIED**

Execute/skip before an expensive stage, with a cost term, is established: **cascades** (Viola–Jones 2001; Latotzke et al. 2021), **metareasoning** (1991), **learned deferral** (Mozannar & Sontag 2020), and in medicine **Med-DANet V2** (WACV 2024) decides per-slice *before* running the model. What none of these does is gate on a **learned GT-derived `DeltaQ` of a refinement** while preserving a refined output via rejection. The gate mechanism is not novel; the decision variable is the residual.

### AXIS D — System integration — **APPARENTLY UNOCCUPIED**

Each pillar is individually occupied: shared multi-domain models (**UniverSeg**, **MedSAM**, MedUniSeg), learned routing in medical segmentation (**M4oE**), predict-then-route over a second pathway (**DeferredSeg**), pre-computation medical compute allocation (**Adaptive Patching**, **Med-DANet V2**), resource-awareness (**MobileSAM**), tiny-lesion zoom (**scale-aware SR**), and post-hoc refined-vs-coarse acceptance (**JFS**). **No verified work unifies all of them.** This is the strongest residual — and it is an **integration** novelty, not an algorithmic one.

## 5. Highest-risk prior art

`reports/tables/phase23_prior_art_matrix.csv` (30 rows, full column set) and `phase23_closest_prior_work.csv` (16 deep comparisons). The eleven HIGH-risk works:

| # | Work | Year | Why it is a threat | Our residual |
|---|---|---|---|---|
| 1 | **JFS** (Moon et al.) | 2024 | Same framing ("was the refinement worth it?") + paired comparison + revert-on-failure | **POST-HOC** (runs refinement first → saves no compute); no learned predictor; no cost |
| 2 | **Metareasoning** (Russell & Wefald) | 1991 | Defines *value of computation* = expected benefit − cost, decided **before** acting | abstract, analytic, non-learned, non-segmentation |
| 3 | **Cascaded classifiers** (Latotzke et al.) | 2021 | Optimal **execute/skip pass-on criteria** before the expensive stage, with cost | classification; criterion from score statistics, not learned `DeltaQ` |
| 4 | **Viola–Jones cascade** | 2001 | Canonical cheap-gates-expensive with early rejection | detection; hand-designed scores |
| 5 | **CATE meta-learners** (Künzel et al.) | 2019 | The **identical formal target** (paired outcome difference) | not imaging; no compute action |
| 6 | **Med-DANet V2** | 2024 | Medical, per-sample compute decision **before** the model, efficiency objective | decision = crop/quantization policy, not a refinement gain; no fallback |
| 7 | **Med-DANet** (ECCV) | 2022 | Predecessor; dynamic model selection per slice | selects a model, not whether to refine |
| 8 | **M4oE** | 2024 | Multi-domain medical segmentation with **learned routing** | routes experts, not execute/skip on a refinement |
| 9 | **Adaptive Patching** | 2024 | Medical, decides **before** expensive attention where to spend compute | detail heuristic, not a learned gain |
| 10 | **LFPC "Information Gap"** | 2026 | Optimises an **information-gain** signal for a regional action | VQA; gain is an implicit RL reward; no supervised pairwise target; no gate/fallback |
| 11 | **Learning to Defer** (Mozannar & Sontag) | 2020 | Learned pre-action deferral with cost and preservation | human expert; classification; no `DeltaQ` |

**The single closest functional analogue is JFS.** The margin to JFS is precise: JFS is a **post-hoc verifier** (it decides *after* refinement, so it saves no compute, and it is untrained), whereas the candidate is a **pre-execution, learned, GT-free gate**. That margin is real but narrow, and it must be stated explicitly and up front.

## 6. Falsification-first result

Family K (8 queries aimed directly at disproving novelty) produced the most damaging find: **JFS**. Family L established that the mechanism has 1970s–2000s antecedents (**Chow reject rule 1970**, **Viola–Jones 2001**, **RPN 2015**). The honest reading: **the mechanism is not algorithmically novel.** The search did *not* locate a single work combining a **supervised, GT-derived paired-gain regression** with a **pre-execution execute/skip gate** on a **segmentation refinement** inside a **shared multi-domain** system with **preservation-fallback** and **cost** — but the absence of one paper is a weaker statement than the presence of the many that occupy the pieces.

## 7. Terminology audits

### 7.1 Counterfactual language — `PREFER_PAIRED_REFINEMENT_GAIN`

`phase23_counterfactual_terminology_audit.json`. Both potential outcomes are **fully observed** for every development image (the system can simply run the refinement during development). There is therefore **no missing-data problem and no identification strategy is needed** — the defining feature that makes an estimand "causal" is absent. Moreover the refinement is **deterministic** given `(x, frozen model, frozen ROI rule)` (per the frozen Phase-22 label contract), so the "effect" is a deterministic paired contrast. **Recommendation:** use *paired refinement gain*; a single caveated sentence may note the formal analogy to CATE but must state that the estimand is a deterministic paired contrast.

### 7.2 "Certified" — `USE_BENEFIT_AWARE_ONLY`

`phase23_certification_terminology_audit.json`. "Certified" implies a **guarantee** (conformal coverage, risk control). None is available:

- **conformal guarantee** — requires an exchangeability argument that the refinement/ROI rules break; **not earned**;
- **empirical risk threshold** — requires a held-out, never-inspected population; Phase 22's policies were all evaluated on the population they were inspected on (post-hoc, optimistically biased); **not earned**;
- **calibrated bound** — Phase 22 showed the GT-free proxies are near-chance (best \|ρ\| = 0.0689, AUC ≈ 0.5), so calibration is unproven; **not yet earned**.

**Recommendation:** drop "certified"; use **"benefit-aware"** (or "gain-gated"). A conditional upgrade path exists if a conformal/risk-control construction is later validated on held-out data — that is a Phase-24+ decision and is **not** authorized here.

## 8. Lightweight/device and tiny-object audits

- **Device/resource awareness** (`phase23_*`, family I): lightweight/mobile/edge segmentation is a crowded, generic area (MobileSAM and many edge-adaptive nets). On its own it contributes **ENGINEERING VALUE**, not algorithmic novelty. It becomes a *defensible* contribution only as an **explicit term in the decision utility** (constraint C6).
- **Tiny-object** (family J): the tiny-lesion problem is already a reviewed field ("From single to universal: tiny lesion detection", AI Review 2024) and regional zoom/super-resolution for small structures is prior art (scale-aware SR). **The tiny-object problem itself must never be claimed as novel**; the potential contribution is only *how optional computation is allocated*.

## 9. Patent/prior-art scan (non-legal)

A light Google Patents / Justia / USPTO scan surfaced only general medical-segmentation documents (e.g. **US 2026/0155254 A1**). **None identified in this limited search** explicitly claims "predict-benefit-before-refining an optional expensive segmentation stage with a resource-cost-aware gate." This is **not a legal conclusion**; academic novelty and patentability are separate, and a professional FTO search would be required before any patentability statement.

## 10. Verdict

**`PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE`.**

- **Algorithmic novelty:** occupied at the mechanism level.
- **Problem formulation:** occupied (JFS).
- **Learning target:** the *formal* target is standard (CATE); the *segmentation instantiation* is not occupied.
- **System integration:** apparently unoccupied — the strongest residual.
- **Evaluation methodology:** partially unoccupied (oracle-ceiling + routing-regret reporting), but a methodology contribution, not a new metric.

**Maximum defensible claim level: Level 2 ("We introduce a novel …"), scoped strictly to the unoccupied combination.** Level 3 ("first to …") is **not** defensible.

**Required reframing:** drop *certified*; drop or caveat *counterfactual*; do not claim the gate, the paired target, multi-domain modelling, or resource-awareness individually; position the work as a **system/integration** contribution explicitly downstream of metareasoning, cascades, CATE and JFS; and lead with the **pre-execution** property as the primary mechanical difference from JFS.

**Recommended method name:** **`RENAME`** — "Counterfactual Benefit-Certified Refinement" is **TOO_STRONG** on two words. Provisional alternative: *Benefit-Aware Refinement Routing* (BARR) or *Gain-Gated Refinement* (GGR). Provisional only.

## 11. Phase-24 constraints (summary)

`phase23_phase24_design_constraints.json` — twelve high-level constraints; no architecture is specified. The load-bearing ones: the predictor must be **pre-refinement** (C1) and **GT-free** (C2), trained on the **paired gain** (C3), without requiring the refinement to compute the gate (C4), with a **preservation-fallback** (C5), an **explicit cost term** if resource-awareness is retained (C6), labels from **TRAIN only** (C7), the **Phase-22 VAL 808 population must not be reused as training data** (C8), a **held-out population designated in advance** (C9), and the closest prior art **cited and differentiated** (C12).

**Phase 24 is eligible to produce a *narrowed* architecture specification only — not implementation, training, or TEST access.**

## 12. Limitations

1. Single working session; a subset of databases reachable (no Semantic Scholar/Crossref API, no paywalled full text). Some 2026 preprints were verifiable only at the abstract/record level and were consequently **excluded** from the authoritative matrix (9 items in `phase23_excluded_nearby_works.csv`).
2. The patent scan is **light and non-legal**.
3. "Not found in the audited scope" is **not** "does not exist." The verdict is deliberately phrased as `NO_..._FOUND_IN_AUDITED_SCOPE`-style language and the overall label is `PARTIALLY_OCCUPIED`, never "unique."
4. Phase-22 evidence is used **only as motivation**; no Phase-22 result is reinterpreted and no new experiment was run.

## 13. TEST lock and no-training attestation

- TEST image reads **0**, mask reads **0**, inference **0**, visualization **0**.
- `training_jobs_started = 0`, optimizers constructed **0**, backward calls **0**, model parameters changed **false**, new checkpoints written **0**.
- No Phase-24 artifact exists; Phase 24 **NOT STARTED**.

## 14. Terminal state

```
PHASE23_NOVELTY_AUDIT_COMPLETE__PARTIALLY_OCCUPIED__PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED
```

Then STOP. DO NOT START PHASE 24.
