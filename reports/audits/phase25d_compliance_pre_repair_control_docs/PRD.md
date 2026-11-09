# PRD — Product / Research Requirements

**Purpose:** Define *what* this project is trying to achieve and *why* — the goal,
motivation, task definition, scope, phase roadmap, success criteria, and non-goals.
It is the "why" document; see [ARCHITECTURE.md](ARCHITECTURE.md) for "how it is built",
[RULES.md](RULES.md) for constraints, [DESIGN.md](DESIGN.md) for experimental design,
[TASKS.md](TASKS.md) for roadmap status, [MEMORY.md](MEMORY.md) for operational handoff.

**Last verified:** 2026-09-30 (Phase-24 router-feature v1.2 closure + governance sync)
**Strategy revision:** **SR-1** (Regional-Aware Multi-Domain FiLM) — status **ADOPTED**;
method name **RA-MedFiLM-BARR**

**Canonical source paths (this document is derived from these, never from memory):**
- `PROJECT_MASTER_PLAN.md` — goal, domains, governance, 41-phase progression
- `PROJECT_CONTEXT.md` — historical handoff context (see conflict warning below)
- `ANTIGRAVITY_WORKFLOW.md` — agent operating contract
- `manifests/manifest_registry.md` / `.json` — manifest versions
- `reports/audits/antigravity_current_state.json` — live phase/run state
- `reports/audits/phase11_clean_v3_failure_analysis_audit.*` — Phase-11 evidence
- `reports/tables/phase11_clean_v3_phase12_bridge_evidence.csv` — Phase-11 → Phase-12 bridge

> **Fact / proposal classification is mandatory in this pack.** Every substantial claim is
> one of: `VERIFIED_CURRENT_FACT` · `HISTORICAL_PROVENANCE` ·
> `SUPERVISOR_ADOPTED_STRATEGIC_DIRECTION` · `PROPOSED_FUTURE_DESIGN` · `FUTURE_EXPERIMENT`.
> A proposed design **MUST NOT** be written as a verified fact.

---

## 1. Goal and Motivation

Build a **rigorous, publication-quality medical image segmentation framework** suitable for
a top-tier Q1/A* paper.

**Current research system: `RA-MedFiLM-BARR`** — Regional-Aware, Multi-Domain,
FiLM-Conditioned **binary** semantic segmentation with **Benefit-Aware Regional Refinement**.
The global model and the regional refiner are **implemented, trained and frozen**
(Phase-21 / Phase-25A); the benefit router is **specified, NOT trained**.

### Primary objective

Develop and evaluate a **shared multi-domain medical segmentation system that predicts the
expected benefit of OPTIONAL regional refinement BEFORE paying for the refinement
computation.**

### Key desired properties

- **GT-free routing at inference** (the router never sees ground truth).
- **Global fallback** — the global path is always available as a safety net.
- **Explicit compute-awareness** — refinement cost is modelled, not ignored.
- **Shared multi-domain design** (one backbone conditioned by task/domain).
- A **measurable segmentation-vs-compute frontier.**
- A **preservation criterion** (regional machinery must not degrade per-domain performance).
- **Reproducible methodology** (frozen artifacts, hashed manifests/checkpoints).

### Explicit non-promises

Not certified · not causal · not guaranteed · not "first-ever" · not mobile-ready yet ·
not real-time yet · not globally resource-optimal · not guaranteed performance-preserving
until non-inferiority evidence exists.

### Scientific hypothesis (SR-1) — a hypothesis to be validated

> A single global segmentation scale may be insufficient across heterogeneous medical
> domains and object scales, and **adaptive regional processing may recover small/local
> difficult targets while preserving global performance.**

This is a **hypothesis**, not an established result. Phase-22 evidence already shows the
regional benefit is **strongly heterogeneous**, and **always-on regional HURTS in
aggregate** — which is precisely why benefit-aware routing (rather than always-on
refinement) is the research object.

Motivation is scientific credibility: every claim must be traceable to frozen artifacts,
reproducible from hashed manifests/checkpoints, and free of leakage or TEST contamination.

## 2. Task Definition

**Binary semantic segmentation.** For every domain the model predicts a single
foreground/background mask.

| Domain | Foreground | Background |
|---|---|---|
| ISIC 2018 | lesion | background |
| BUSI | breast lesion | background |
| Kvasir-SEG | polyp | background |
| KUB-StoneX | stone | background |

### KUB foreground rule (canonical, non-negotiable)

```
BACKGROUND : mask == 0
FOREGROUND : mask > 0
```

Native KUB masks use a heterogeneous, category-correlated nonzero label vocabulary —
`{0,255}`, `{0,1}`, `{0,2}`, `{0,3}`, `{0,1,2}` all occur. **Every nonzero value is
foreground.** Code must NEVER test `mask == 1`. Defined once in `src/utils/targets.py`
(`binarize_mask`, `FOREGROUND_RULE = "mask > 0"`).

### Kidney / Bladder / Ureteric are METADATA, not classes

`PROJECT_MASTER_PLAN.md` §2: *"Kidney, Bladder, and Ureteric are subgroup metadata, not
semantic classes."* They are used for **stratified reporting** — never as pixel class
channels. The model has **1 output channel**. **Do NOT manufacture multiclass masks.**

## 3. Domains / Tasks

| Task ID | Domain | Modality | Target |
|---|---|---|---|
| 0 | ISIC 2018 | Dermatology / skin | Skin lesion |
| 1 | BUSI | Breast ultrasound | Breast lesion |
| 2 | Kvasir-SEG | GI endoscopy | Polyp |
| 3 | KUB-StoneX | Urinary radiography | Stone |

Initial experiments use **true task IDs**. Automatic domain routing is a separate future
module and must not contaminate the core segmentation study. Manual prediction is KUB-only
(`predict_kub`); `predict(..., task='auto')` raises `NotImplementedError` — **automatic
routing is NOT operational**.

## 4. Strategy Revision SR-1 — adopted direction

**Original roadmap (historical):** standalone KUB regional development, followed later by a
separate multi-domain FiLM architecture.

**Strategy Revision SR-1 (supervisor-adopted):** reinterpret the KUB regional work as
**reusable regional-mechanism development** intended for eventual integration into
`RA-MedFiLM-Seg++`. Existing completed phases remain valid; history is **not** rewritten as
though SR-1 always existed.

**KUB is reframed as the REGIONAL-MECHANISM DISCOVERY AND VALIDATION LABORATORY** — not
wasted work. The scientific chain:

```
clean data
  -> KUB characterization
  -> tiny-object taxonomy
  -> global baselines
  -> four-model failure analysis
  -> oracle regional-resolution test
  -> GT-free localization feasibility
  -> regional integration gate
  -> regional mechanism development
  -> multi-domain global model
  -> global MedFiLM
  -> regional-aware MedFiLM
  -> RA-MedFiLM-Seg++
```

The final paper should present a **causal development story**, not two unrelated systems.

### Proposed future architecture (SR-1) — `PROPOSED_NOT_IMPLEMENTED`

Intended components: modality/input adaptation · shared global segmentation representation ·
task/domain FiLM conditioning · GT-free region proposal/localization ·
higher-effective-resolution regional processing · regional/refinement representation ·
scale/region-aware FiLM conditioning · adaptive global-regional fusion/routing ·
final binary segmentation output.

This is the **official future direction**, but it is **NOT IMPLEMENTED, NOT TRAINED, NOT
VALIDATED, NOT FROZEN**.

## 5. Phase Roadmap (00–40)

41 phases in four stages (`PROJECT_MASTER_PLAN.md` §7), with SR-1 reinterpretations:

- **Stage A — KUB Regional & Tiny-Object Development (00–18)** — Phases 14–18 are
  `PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE` (conditional, not automatic)
- **Stage B — Multi-Domain Harmonization & RA-MedFiLM Architecture (19–26)**
- **Stage C — Multi-Domain Rigor, Ablation, Reproducibility & Clinical Evidence (27–37)**
- **Stage D — Protocol Freeze, Single-Pass Test Benchmark & Publication (38–40)**

Per-status detail in [TASKS.md](TASKS.md). The three most important gates:

- **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** (§7) — decides whether the regional
  mechanism is promoted, revised, or dropped.
- **Phase 38** — manuscript protocol & checkpoint freeze.
- **Phase 39** — the **only** phase in which the untouched TEST cohort is evaluated.
- **Phase 40** — publication package & reproducibility audit.

## 6. Success Criteria

1. **Leakage-free evidence** — all development results traceable to `phase4_v3`
   (leakage status `REMEDIATED`, Phase-05 Part 1E).
2. **Reproducibility** — unique experiment IDs with hashed config / history / `best.pt` /
   `latest.pt`, and deterministic review notebooks.
3. **Evidence-gated regional mechanism** — the regional mechanism is promoted **only** if
   Phase 12/13 evidence passes the gate; a negative result is a legitimate outcome.
4. **Multi-domain preservation** — adding FiLM/regional machinery must not degrade
   per-domain performance (Phase 27).
5. **Statistical honesty** — no superiority claim from a single seed; significance only when
   actually tested with paired tests, CIs, effect sizes (`PROJECT_MASTER_PLAN.md` §10).
6. **Single-pass TEST** — TEST evaluated exactly once, in Phase 39, after Phase 38 freeze.
   No tuning after TEST access.

## 7. REGIONAL_INTEGRATION_GATE_AFTER_PHASE13

Formal governance gate occurring **after Phase 12 and Phase 13**.

| Outcome | Meaning | Action |
|---|---|---|
| **GO** | Oracle regional processing helps **AND** predicted localization retains meaningful practical utility | Promote the regional mechanism toward RA-MedFiLM-Seg++ |
| **REVISE_LOCALIZER** | Oracle helps **BUT** predicted localization loses too much benefit | Do **not** abandon the regional hypothesis; redesign/localizer work first |
| **NO_GO** | Even oracle regional processing provides insufficient meaningful benefit | Do **not** force regional complexity into the final FiLM architecture; proceed with global multi-domain MedFiLM and document the negative regional evidence |

> **No numerical GO/NO-GO thresholds are defined in this documentation pack.** Those
> criteria must be **prospectively frozen** before inspecting the relevant Phase-12/13
> results ([RULES.md](RULES.md) §12).

## 8. Non-Goals

- **No multi-class KUB segmentation.** Kidney/Bladder/Ureteric are not classes.
- **No TEST usage before Phase 39** — not for training, validation, threshold, architecture,
  loss, preprocessing, proposal, fusion, FiLM-design, or checkpoint selection.
- **No automatic domain routing yet** (future work).
- **No clinical mm-scale size claims** — the size taxonomy is dataset-relative
  (`component_ratio`), not clinical millimetres.
- **No silent migration of historical v2 results into clean-v3 claims.**
- **No claiming the system as validated, frozen, or novel** before the corresponding
  evidence phases. Specifically: **no claim that the benefit router works, that routing
  helps, or that refinement is worth its cost** until the router is trained and evaluated.
- **No "certified / causal / guaranteed / counterfactual / first-ever" claims.**
- **No "mobile-ready", "real-time", or "globally resource-optimal" claims.**
- **No deployment-unavailable metadata as model conditioning.** Every metadata field used in
  future multi-domain work **MUST** be classified as `CONDITIONING_ALLOWED`,
  `REPORTING_ONLY`, or `FORBIDDEN_AS_INPUT` ([RULES.md](RULES.md) §13). Kidney/Bladder/
  Ureteric remain `REPORTING_ONLY`.

## 9. HISTORICAL_v2 vs CLEAN_v3 separation (mandatory framing)

| Aspect | HISTORICAL_v2 | CLEAN_v3 |
|---|---|---|
| Manifest | `phase4_v2` (root `manifests/*.csv`) | `phase4_v3` (`manifests/phase4_v3/`) |
| Status | `HISTORICAL_SUPERSEDED_FOR_FUTURE_DEVELOPMENT` | `CANONICAL_ACTIVE_DEVELOPMENT` |
| Leakage | `KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY` | `REMEDIATED` |
| Global split | TRAIN 5913 / VAL 845 / TEST 1683 | TRAIN 5832 / VAL 808 / TEST 1683 / QUAR 118 |
| KUB split | TRAIN 1979 / VAL 283 / TEST 558 | TRAIN 1978 / VAL 280 / TEST 558 / QUAR 4 |
| Taxonomy | `kub_size_v1` (IMMUTABLE) | `kub_size_clean_v3_v1` (FROZEN) |
| Use | Reproduce historical Phases 06–15 only | All future scientific development |

> TEST is **byte-identical** between v2 and v3
> (`9361eba61c91c034a9aa4988a4df229bba591a5cbd553c98689ac7915da29727`).
> **No v2 result may be silently presented as a clean-v3 result**, and no v3 result may be
> compared to v2 as if the splits matched.

## 10. ⚠ Material source conflicts (recorded)

Detected while deriving this pack; recorded, not silently resolved:

| # | Source | Conflicting claim | Evidence-based reality | Material? |
|---|---|---|---|---|
| C1 | `PROJECT_CONTEXT.md` | "No clean-rerun phase has been executed." | Clean-v3 **Phases 05–12 are COMPLETE**; **Phase 13 Part 1A (protocol/definition) is COMPLETE**; Part 1B is not authorized | **YES** |
| C2 | `PROJECT_CONTEXT.md` | "The strongest global KUB baseline is **UNet++**" — a winner declaration | `phase10_winner_declared = False`; that is a **historical v2** statement | **YES** |
| C3 | `PROJECT_MASTER_PLAN.md` | Phase 09 clean-v3 "**NOT started**" | Completed 2026-09-20; best ep 44, Dice 0.7406133413314819 | **YES** |
| C4 | `ANTIGRAVITY_WORKFLOW.md` | "CURRENT PHASE: 13B"; "NEXT AUTHORIZED ACTION: NONE" | Live state: **Phase 12 COMPLETE / PASS**; **Phase 13 Part 1A COMPLETE** (protocol/definition only); Part 1B not authorized | **YES** |
| C5 | `antigravity_current_state.json` | Earlier `phase10_unetpp_started: False` | **Repaired 2026-09-21** (Phase-11 preflight audit); now consistent | Resolved |
| C6 | `antigravity_current_state.json` | Attention U-Net `val_precision_at_best = None` | Resolved as **HISTORY_NATIVE**: `0.7729140812402236` / `0.7922248481868364` | Minor |
| C7 | `src/utils/test_lock.py` | Lock `manifest_version` labelled `phase4_v2` | TEST is byte-identical v2↔v3, so the lock is valid | No |

**Disposition:** C1–C4 remain material. Treat
`reports/audits/antigravity_current_state.json` + per-run audits as the live authority.
Do not "fix" stale top-level files without authorization.

---

**Cross-links:** [ARCHITECTURE.md](ARCHITECTURE.md) · [RULES.md](RULES.md) ·
[DESIGN.md](DESIGN.md) · [TASKS.md](TASKS.md) · [MEMORY.md](MEMORY.md)
