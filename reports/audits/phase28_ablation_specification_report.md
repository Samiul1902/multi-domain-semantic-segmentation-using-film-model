# PHASE 28 — Comprehensive System Ablation Matrix
## Pre-Execution Specification Audit — Report

**Method:** RA-MedFiLM-BARR
**Classification:** `PHASE28_PRE_EXECUTION_SPECIFICATION_AUDIT`
**Governance only:** true · **Execution:** NONE
**Population:** ROUTER_DEVELOPMENT (n = 4957)
**Terminal:** `PHASE28_ABLATION_SPEC_COMPLETE__FROZEN_MATRIX_POPULATION_EXECUTABILITY_AND_STATISTICS_BOUND__PHASE28_EXECUTION_ELIGIBLE_NOT_STARTED`

---

### §0 Entry gate
- Phase27 scientific terminal confirmed: `...PHASE28_ELIGIBLE_NOT_STARTED` (freeze SHA `42e51a67…` unchanged).
- Phase27 visual-repair terminal confirmed: `...SCIENTIFIC_FREEZE_UNCHANGED__PHASE28_ELIGIBLE_NOT_STARTED`.
- Phase27 = `COMPLETE_CANONICAL` · ROUTER_HOLDOUT = `RESERVED_UNOPENED_FOR_PHASE30` · TEST = `LOCKED_UNTIL_PHASE39`.
- Phase26 canonical bundle manifest SHA `f7aebb0f…` unchanged. **predecessor_drift = 0.**

### §1 Authoritative source binding
29 sources SHA-256-bound, including the three frozen Phase24 plan tables, the Phase24 architecture + exact-implementation specs, the Phase25G/26/27 freezes, and the canonical bundle manifest. Rule enforced: **no ablation meaning may be inferred from a label alone.**

### §2 Canonical title
**`Comprehensive System Ablation Matrix`** (from Phase27 boundary contract v1.1 + the phase-28 reviewer README).
The alternate title `Full Architecture Ablation Matrix` (TASKS.md slate, Phase26 boundary audit) is **preserved as provenance** and flagged *superseded by the latest authoritative boundary contract*. TASKS.md was **not** overwritten.

### §3 Ablation registry
All **13** ablation IDs recovered verbatim from `reports/tables/phase24_ablation_plan.csv`:
`A0–A8` (core), `R1–R3` (router), `F1` (refiner).

### §4 R1 / R2 / R3 / F1 — exact recovery
| ID | Exact frozen definition | Purpose | Single controlled factor |
|----|------------------------|---------|--------------------------|
| **R1** | router without deep global features | does depth matter? | `ROUTER_FEATURE_DEPTH` |
| **R2** | router without task_id | does conditioning matter? | `ROUTER_TASK_CONDITIONING` |
| **R3** | router with scalar-only features | minimal-feature control | `ROUTER_FEATURE_SET__SCALAR_ONLY` |
| **F1** | refiner without p_global channel | is the global map useful? | `REFINER_INPUT_P_GLOBAL_CHANNEL` |

**Label-inference trap avoided:** R1/R2/R3 are *router* ablations — **not** "rescue". The empty-prediction rescue is a pre-registered `region_proposal` Option-B behaviour with **no ablation ID**.

### §5 A7 / A8 status
`A7_A8 = SATISFIED_BY_PHASE25G_CANONICAL_EVIDENCE` — no source requires a re-run; frozen C8/C9 membership + bootstrap plan already exist on the same population.

### §6 Canonical baseline arm
Frozen Phase26 **A8/C9**, budget **0.25**, lambda **0.25** (not performance-selected), runtime score `delta_hat_final − 0.25·C`, runtime threshold `-5003565381643716252018011/205414980000000000000000000`, ROI 0.30, S_omega 0.50, seg 0.50.

### §7 Population ownership (HARD BLOCKER — RESOLVED)
**Phase28 ablation population = ROUTER_DEVELOPMENT (n = 4957).**
Split manifest verified: 4957 + 875 = 5832, zero overlap. ROUTER_HOLDOUT (875, Phase30) and TEST (1683, Phase39) are **FORBIDDEN**.

### §8–§9 Reuse rules
- VAL808 → `DEVELOPMENT_ABLATION_EVIDENCE` (continuity only, not primary).
- Per-ablation classification: **6** `ARTIFACT_RECONSTRUCTABLE` (A0–A5) · **3** `SATISFIED_BY_PRIOR_CANONICAL_EVIDENCE` (A6–A8) · **4** `NEW_FROZEN_MODEL_INFERENCE_REQUIRED` (R1–R3, F1) · **0** training-required.

### §10–§11 Training + one-factor control
**NO_TRAINING.** One-factor-at-a-time contract frozen: every arm differs from A8/C9 in exactly one controlled factor; multiple-factor change and post-hoc factor addition forbidden.

### §12–§18 Ablation families
Global/FiLM (§12), regional refiner (§13), router (§14), post-safety (§15) recovered with exact architecture/checkpoint SHAs.
**Fusion (§16), rescue (§17), shared-vs-domain router (§18)** → `NOT_APPLICABLE__NO_FROZEN_ABLATION_ID`. Also disambiguated the `F1` namespace collision: `F1` = **ablation arm** (ablation-plan namespace) vs `F1` = **REFINER_FAILURE** (criteria namespace).

### §19–§27 Metrics, statistics, compute, guards, locks
Metrics (5 families), paired bootstrap (n=2000, seed=42), compute = `ANALYTICAL MAC LOWER BOUND` (measured efficiency → Phase34), no performance selection, negative results valid, ROUTER_HOLDOUT locked, TEST locked, Phase29/Phase31 boundaries consistent.

### §28–§31 Completeness & terminal
- `phase28_specification_completeness.csv` — 35 fields, all `complete = true`.
- `phase28_ablation_executability.csv` — 13 arms classified.
- `phase28_no_execution_audit.json` — **all counters zero**; bundle and Phase27 freeze untouched.
- 29 audit artifacts present; `all_pass = true`.

**STOP — Phase28 specification audit complete. Phase28 execution is ELIGIBLE but NOT STARTED.**
