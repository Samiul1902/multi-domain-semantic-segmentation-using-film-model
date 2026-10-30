# Phase 33 — Final System Failure & Boundary Error Analysis
## Specification v1.2 — Additive Prospective Clarification of the LOW_OVERLAP Realization Rule

**Revision:** `ra_medfilm_barr_phase33_failure_boundary_v1_2`
**Classification:** `ADDITIVE_PROSPECTIVE_AMENDMENT__PRE_OUTCOME__NO_CUTOFF_NO_DISTRIBUTION_INSPECTED`
**Method:** RA-MedFiLM-BARR
**Generated:** 2026-10-04T08:56:12+00:00

---

## 1. What changed in v1.2

v1.2 is an **additive, prospective (pre-outcome) amendment** that makes the **LOW_OVERLAP
realization rule fully explicit**. It changes **no** scientific definition, no family eligibility,
no population, and no metric.

The v1.1 specification (`docs/phase33_final_system_failure_boundary_spec_v1_1.md`, SHA
`c3020db76b1c6f75db13c894406f5c955c7e7431b5c6f5a2082818f2958afc38`, preserved byte-for-byte) left
the LOW_OVERLAP realization rule **not exactly frozen**: three of the eight elements required to
realize the cutoff were unresolved. Two independent fail-closed adjudications —
`phase33_low_overlap_realization_adjudication.json` (SHA `a3fe87c19d0377ad7188a7a36c6d78305e24d69
1569350cb5683484c8cdbfc18`) and `phase33_low_overlap_rule_element_adjudication_v2.json` (SHA
`73123ce1554d52bccfe87d75ec240d941712a3ddaaa88ed711470a9b2e7978a8`) — both returned `BLOCK` with
terminal `PHASE33_TIER0_TIER1_EXECUTION_BLOCKED_PREANALYSIS__LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN__NO_RESULTS_COMPUTED`.

Defect classification:
`PROSPECTIVE_SPECIFICATION_INCOMPLETENESS__LOW_OVERLAP_REALIZATION_RULE_NOT_EXACTLY_FROZEN__NO_SCIENTIFIC_CLASSIFICATION_CHANGE`.

## 2. The three resolved elements

| # | element | v1.1 status | v1.2 resolution |
|---|---|---|---|
| 1 | target Dice field | DETERMINABLE_BY_TEXT_NOT_EXPLICIT | **`a8_dice`** (final A8/C9 system; `global_dice` is reference-only) |
| 5 | inclusive/exclusive comparison rule | DETERMINABLE_BY_TEXT_NOT_EXPLICIT | **`<=`** (inclusive) |
| 7 | missing/NaN handling | ABSENT | **`REQUIRE_ALL_FINITE_NO_EXCLUSION`** (else BLOCK) |

## 3. The 8-element LOW_OVERLAP realization rule (fully explicit)

| # | element | frozen value |
|---|---|---|
| 1 | target Dice field | `a8_dice` |
| 2 | population | frozen ROUTER_HOLDOUT scored table, n = 875 |
| 3 | quantile probability | `0.10` |
| 4 | quantile algorithm | `np.quantile(float64_values, 0.10, method='linear')` |
| 5 | comparison operator | `<=` (inclusive) |
| 6 | tie handling | ties at the cutoff are LOW_OVERLAP |
| 7 | missing/NaN policy | `REQUIRE_ALL_FINITE_NO_EXCLUSION` |
| 8 | scope | single GLOBAL cutoff over all 875 rows (NOT per-domain) |

Canonical realization: `LOW_OVERLAP ⇔ a8_dice <= np.quantile(a8_dice[float64], 0.10, 'linear')`.

The numeric cutoff is **NOT** frozen now; it is realized deterministically at execution from the
frozen table.

## 4. Disclosure — structural finiteness check already performed

The `REQUIRE_ALL_FINITE_NO_EXCLUSION` precondition concerns the **structural** presence/absence of
non-finite values in the `a8_dice` column. That structural property was **already** recorded in the
v1.1 preflight (`phase33_tier0_tier1_preflight.json`, SHA `8cac456a7ead35a6956a14b693782de041f16a2
874b5fac82ad4d428f09c25e7`, `non_finite_a8_dice_rows = 0`). For the frozen 875-row
ROUTER_HOLDOUT population the structural precondition holds: **0 non-finite `a8_dice` values,
0 empty `a8_dice` values**.

This disclosure is made in the interest of full transparency. A structural finiteness check is
**not** a distributional summary. To date **no** distribution, quantile, cutoff, failure
prevalence, or Phase33 descriptive result has been inspected or computed:

| prohibited item | status |
|---|---|
| cutoff computed | **false** |
| quantile computed | **false** |
| distributional statistics computed | **false** |
| a8_dice distribution inspected | **false** |
| a8_dice min/max inspected | **false** |
| failure prevalence computed | **false** |
| Phase33 descriptive results computed | **false** |

## 5. Preservation

All v1.1 authority artifacts, all blocked-execution artifacts, the blocked reviewer notebook, and
the frozen inputs are preserved byte-for-byte
(`reports/audits/phase33_v1_2_preservation_manifest.json`).

## 6. Execution eligibility

table-only **true** · derived non-pixel **true** · prediction-pixel false · raw image false ·
raw GT false · qualitative gallery false · boundary metric false · component metric false ·
model rerun false.

With the LOW_OVERLAP realization rule now **fully explicit**, **TIER_0 / TIER_1 execution is
ELIGIBLE** — but **NOT STARTED** in this task (`execution_started = false`, `Phase34_started =
false`). The prior blocked terminal remains preserved as historical evidence.

`science_changed = false`; `execution_eligibility_changed = false` (the execution gate is unchanged
from v1.1; only the blocking *rule incompleteness* has been prospectively resolved).
