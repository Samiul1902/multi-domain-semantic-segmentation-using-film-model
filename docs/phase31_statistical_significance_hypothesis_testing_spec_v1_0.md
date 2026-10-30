# Phase 31 — Statistical Significance & Hypothesis Testing
## Entry Gate + Hypothesis Provenance + Exact Statistical Specification (v1.0)

**Specification revision:** `ra_medfilm_barr_phase31_statistics_v1_0`
**Method:** RA-MedFiLM-BARR
**Status:** SPECIFICATION COMPLETE — **statistical execution NOT authorized**
**Generated:** 2026-10-04T05:37:39+00:00

> **Phase30 qualifier carried forward:**
> `ONE_SHOT_ROUTER_HOLDOUT_RESULT_WITH_DISCLOSED_POST_FIRST_OPEN_SCIENTIFIC_SOURCE_FREEZE_DEVIATION`
> Phase30 must **never** be described as `COMPLETE_CANONICAL`, "fully preregistered execution",
> "perfectly source-frozen validation", "no protocol deviations", or "strictly protocol-perfect
> holdout".

---

## 1. The roadmap phrase is a toolbox description, not a preregistration

The historical roadmap describes Phase31 as *paired Wilcoxon / bootstrap 95% CIs / Cohen effect
sizes*. That is a **toolbox description only**. It is **not** an exact preregistration of which
comparison, metric, population, null, alternative, tail, zero-difference handling, multiplicity
family, alpha, clustering unit, or effect-size definition. Those details must be recovered from
pre-outcome authority, and are **not** inferred from the roadmap phrase.

## 2. Prospective vs post-hoc boundary

Phase30 outcomes are known. Phase31 therefore classifies every candidate analysis as one of:

1. `CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`
2. `PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE`
3. `ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE`
4. `DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY`
5. `POST_HOC_EXPLORATORY_ONLY`

**No new confirmatory procedure may be created merely because it is conventional.**

## 3. Hypothesis provenance (summary)

| id | status |
|---|---|
| H1 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25E/25G) |
| H2 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25E) |
| H3 | DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY (Phase25G) |
| H4 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25A/Phase28) |
| H5 | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase25E/25G) |
| H6 | PREOUTCOME_HYPOTHESIS_METHOD_INCOMPLETE |
| P30-PRIMARY | ALREADY_ADJUDICATED_BY_PREDECESSOR_PHASE (Phase30, CI gate) |
| P30-A8VSRANDOM-P | POST_HOC_EXPLORATORY_ONLY |
| P30-A7-COMPANION | DESCRIPTIVE_ONLY_BY_PREDECESSOR_AUTHORITY |
| C11-JFS | FORBIDDEN_OR_OUT_OF_SCOPE |

**Zero candidates are `CONFIRMATORY_PREOUTCOME_EXACT_METHOD_FROZEN`.**

## 4. Phase30 primary result must not be redefined

Frozen: macro ΔDice `+0.0017390308610248934`, 95% CI
`[0.00111729355352301, 0.0024049809029647283]`, margin 0.005, gate lower 95% CI > −0.005,
`PRESERVATION_ASSERTED = true`, Phase30 p-values computed = 0. Phase31 must not replace this gate
nor claim a new p-value was required. A test against `DeltaDice = 0` is **different** from the frozen
non-inferiority claim.

## 5. Phase30 p-value boundary (CASE P2)

`GENERIC_PAIRED_P_REPORTING_ALLOWED_BUT_EXACT_PHASE30_PROCEDURE_NOT_FROZEN`. The Phase25E
C7-vs-comparator raw paired p-value **must not** be transferred. Any Phase31 A8-vs-global
significance test is **POST_HOC_EXPLORATORY_ONLY** and may never upgrade or downgrade
`PRESERVATION_ASSERTED`.

## 6. Wilcoxon provenance ruling

The roadmap phrase "paired Wilcoxon" is insufficient. No predecessor authority freezes all required
fields (comparison, metric, unit, pairing key, null, alternative, tail, alpha, zero handling,
implementation, exact/approx, continuity, NaN, ties, cluster dependence). **No Phase31 paired
Wilcoxon may be confirmatory** — exploratory only or omitted.

## 7. Cluster / group dependence (load-bearing)

ROUTER_HOLDOUT has 875 rows in **628 groups** (`group_key`). A naive sample-level test over 875 rows
is **forbidden**. No exact cluster-aware inferential test was prospectively frozen; none may be
invented as confirmatory after outcomes. Any cluster-aware test is exploratory only. The frozen
Phase30 domain-stratified group bootstrap already handles groups.

## 8. Bootstrap reuse

The Phase30 plan (`59c97ccf6fbea823d38a1fba12d5e81b7e5fb103f31bc7fdfe443fd4971faab1`) must **not** be regenerated. Only the already-frozen
Phase30 macro/per-domain A8-vs-global CI is authorized to reuse the plan, and only as frozen output.
The existence of bootstrap indices does **not** authorize arbitrary new estimands.

## 9. Effect-size provenance

"Cohen effect sizes" is insufficient. No exact definition (d / dz / dav / drm / other) was frozen
pre-outcome. Any newly chosen effect size is **POST_HOC_EXPLORATORY_ONLY** and must not become a
success gate; no definition may be selected for favorable magnitude.

## 10. Multiplicity

No automatic Holm/Bonferroni/BH. The Phase25E Holm authority belonged to its pre-declared C7
comparator family and must not be generalized. No confirmatory multiplicity family exists for
Phase31 → no confirmatory multiplicity claim is permitted.

## 11. Test registry

`reports/tables/phase31_statistical_test_registry.csv` — 4 candidate tests, of which
**0 confirmatory** and **2 exploratory**. `execution_authorized = false`
for **every** test pending supervisor review.

## 12. Evidence consumption

Phase31 may consume only the frozen Phase30 tables/audits authorized by the qualified handoff.
Counters: raw holdout image reads 0, raw holdout GT reads 0, model forwards 0, training steps 0,
TEST reads 0.

## 13. TEST lock

TEST owner = Phase39; state `LOCKED_UNTIL_PHASE39`; Phase31 TEST reads = 0.
