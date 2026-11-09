# BARR-M1 — Supervisor Authorization Request

**Revision:** `RA_MEDFILM_BARR_BARR_M1_V1_0C__FINAL_APPROVAL_PACKAGE`
**Status:** request only. **Nothing is authorized by this document.**

---

## 1. Research question and limited claim class

**Question.** Under one frozen fusion rule, on one frozen development population, how do three
complete frozen segmentation policies differ in macro-domain Dice and in harmful-refinement
behaviour — and how much of the difference is attributable to refining everywhere versus to
routing with a post-safety gate?

**Claim class: `DESCRIPTIVE_DEV` only.**

Permitted:
> "On a governed development population that also participated in component selection, policies
> A0/A1/A8 differed in macro-domain Dice by X; the all-population harmed-case rate was Y for
> refine-all and Z for the routed, safety-gated policy."

Prohibited: held-out performance · confirmatory inference · generalisation · clinical safety ·
superiority of BARR · an isolated causal router effect.

## 2. Exact frozen component and population identities

| Component | Class | SHA-256 | Params |
|---|---|---|---|
| G | `GlobalMedFiLM` | `286689fdd5c63ad75a383151d267af8b476e7a98327632de292ce6ed5b5ba1b7` | 3,523,001 |
| R_psi | `BARRRegionalRefinerV1` | `6d28608a669df497740b6594ab346136f4efdf3f66002a868a1f1a3ec6689109` | 1,276,401 |
| B_phi | `BARRBenefitRouterV1` | `8a412b2fe82f225f844fda07379a6436c1d73d435f885b26a1d88d5b2f9fc43b` | 36,801 |
| S_omega | `BARRPostSafetyV1` | `eee9b97b9921e53fc07eac9281dce64ba518c6e1659916b97b0b3bec21ec6d2e` | 1,217 |

**Population:** `ROUTER_DEVELOPMENT`, n = **4,957**; metadata digest
`ee8c304350d28d907c053a355da1f878ff7f9dd137761034283459aeed071093`.

**Frozen inputs (SHA-bound):**

| Input | SHA-256 |
|---|---|
| Phase-25C OOF gain labels | `fd6ca32c33a3bddb75f986b1350d54ec35b11d3bf5cb0fdc029962a5aa94865f` |
| Phase-25E C8 membership (λ0.25 / budget 0.25) | `4c411d589866434b824245d3c940bc09873f3cbc096ddc8a44776cd56273393b` |
| Phase-25F OOF safety predictions | `a9f63edd6d58a9a1d78a052a3e4539c6e0dd4d68bfb1c09c4c36789c441ebdee` |
| Phase-28 arm table 02 | `171168f973d0a210913b567c4b743f134b1918f3d22be55a6e7046890400e3fc` |

**Frozen constants:** ROI 0.30 / expansion 1.50 / resolution 256; segmentation output 0.50;
safety accept 0.50; budget 0.25 (K = 1239); λ 0.25; bootstrap 2000 / seed 42; harm tolerance 1e-9.

## 3. Scope and execution exclusions

**In scope.** Arms **A0, A1, A8** only. `CPU_ONLY_RE_ANALYSIS_ONLY` over preserved arrays.
Paired A8−A0, A8−A1, A1−A0 with the frozen bootstrap.

**Excluded.** Any arm outside A0/A1/A8 · **A7** · any new factor · any new model construction ·
any forward pass · any training · TEST · ROUTER_HOLDOUT · external data · any new scientific
contrast beyond the three declared paired contrasts.

## 4. Existing evidence and methodological limitations

**Already established (frozen, not re-derived here):**
- A0/A1/A7/A8 reproduce **exactly** from frozen per-case arrays (9/9 checks at 1e-9) with zero
  inference — so this study is a re-analysis, not an inference run.
- Frozen Phase-28 aggregates: A1 Σ = 8.219101516 (2115/4957 harmed, strict); A7 Σ = 8.9785736244
  (1239 executed, 412 harmed); A8 Σ = 9.0564839294 (1205 executed, 390 harmed).

**Limitations that must appear in every caption:**
1. **The primary population is the training population** of `B_phi` and `S_omega` (5-fold CV plus
   an all-DEV final refit) and a subset of TRAIN for `G` and `R_psi`. **No pristine independent
   population remains** — ROUTER_HOLDOUT was consumed by Phase30, TEST is locked.
2. **G is in-sample**; `R_psi`, `B_phi` and `S_omega` per-case predictions are cross-fitted. This
   limits but does not eliminate optimistic bias.
3. **Patient clustering is available only for KUB** (267). ISIC/BUSI/KVASIR have no patient
   identifier, so within-source correlation is unmodelled.
4. **Harm rates are reported on two denominators** — all-population and conditional-on-execution —
   and both must appear. The all-population A8 rate (390/4957 = 7.8677 %) is **not** comparable to
   a conditional rate, and vice versa.
5. **Pooled and macro means differ** on this unbalanced population; each must be labelled.
6. **No safety metric exists** and there is no `S_omega`-absent arm, so the safety contribution is
   **not measurable within Phase-28** (C2b remains `NOT_ESTABLISHED`).

## 5. Expected CPU-only workload

| Item | Estimate |
|---|---|
| Model constructions / forwards / autograd | **0 / 0 / 0** |
| GPU time | **0 s** |
| CPU wall time | **minutes** (deterministic array arithmetic + 3 × 2000 bootstrap resamples) |
| Disk | per-case outputs for 3 arms × 4957 rows (CSV, a few MB) |
| Restartable | yes — per-arm idempotent completion markers |

## 6. Separate, optional future proposal — BARR-M2

**Not requested here.** A7 vs A8 is the **only** pre-registered single-component isolation in the
frozen design (`frozen_matched_contrasts = ["A7_vs_A8"]`). Frozen paired result: mean
**+1.5717229e-05**, 95 % CI **[−1.4313785e-05, +5.1010811e-05]** — crosses zero.

A separate study (`BARR-M2`, provisional) would decompose the `S_omega` contribution descriptively,
also with zero inference. **It must not be folded into BARR-M1**, because that would change the
study from a three-policy comparison to a component-isolation analysis with a different claim class.

## 7. Supervisor authorization block — **EMPTY**

```
AUTHORIZATION REQUEST — BARR-M1 (v1.0c)

Study identifier      : BARR-M1
Classification        : DESCRIPTIVE POLICY_COMPARISON (not a router causal ablation)
Arms                  : A0, A1, A8 ONLY
Population            : ROUTER_DEVELOPMENT n=4957  (IN_SAMPLE_DEVELOPMENT — acknowledged)
Execution mode        : CPU_ONLY_RE_ANALYSIS_ONLY (0 model constructions, 0 forwards)
Endpoint              : paired A8-A0 / A8-A1 / A1-A0; equal-domain MACRO Dice
                        (pooled reported separately and labelled)
Harm rates            : BOTH strict (delta<0) and tolerance-adjusted (delta<-1e-9)
Bootstrap             : 2000 resamples, seed 42, paired common indices, domain-stratified
Gate                  : R1-R10 re-analysis gate validated (harness e82ecdb781a56355…)

EXPLICITLY NOT AUTHORISED
  A7 or any arm outside A0/A1/A8 · any new factor · any model construction or forward
  pass · any training · TEST · ROUTER_HOLDOUT · external data · clinical-safety,
  held-out, superiority or confirmatory claims · BARR-M2 (separate request)

AUTHORIZED BY : ______________________   DATE : ____________
AUTHORIZATION ID : ____________________   [ ] APPROVED   [ ] REJECTED
```

**Completion of this work order does not constitute authorization.**
