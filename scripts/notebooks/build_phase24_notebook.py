"""Phase 24 — build the Narowed Benefit-Aware Refinement Architecture spec notebook.

DESIGN ONLY. This notebook performs NO training, NO segmentation model forward calls,
NO benefit-router forward calls, and inspects NO router-holdout outcomes. Every number
is rebuilt from persisted Phase-24 design artifacts (audits + tables) and from the
frozen Phase-21/22/23 predecessor SHAs.

Determinism contract (identical to the Phase-21/22/23 builders)
--------------------------------------------------------------
deterministic cell ids (``p24NNN``) + stripped ``metadata.execution`` + coalesced
stream outputs + fixed pandas Styler uuids (``set_uuid``) + normalised object memory
addresses (``0x...`` -> ``0xADDR``). Three consecutive builds must be byte-identical.

Usage
-----
    ./.venv/Scripts/python.exe scripts/notebooks/build_phase24_notebook.py
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_DIR = ROOT / "notebooks/phasewise/phase_24_architecture_spec"
NB_PATH = NB_DIR / "phase24_narrowed_benefit_aware_refinement_spec.ipynb"
NB_DIR.mkdir(parents=True, exist_ok=True)

md = lambda s: nbformat.v4.new_markdown_cell(s.strip("\n"))     # noqa: E731
code = lambda s: nbformat.v4.new_code_cell(s.strip("\n"))       # noqa: E731

cells: list = []

# ---------------------------------------------------------------------------
# §1. TITLE / SCOPE
# ---------------------------------------------------------------------------
cells.append(md("""
# Phase 24 — Narrowed Benefit-Aware Refinement Architecture + Pre-Registered Development Protocol

### A DESIGN-ONLY specification, written BEFORE any implementation, training or evaluation

| Item | Value |
|---|---|
| Phase | 24 — Narrowed Benefit-Aware Refinement Architecture |
| Canonical folder | `notebooks/phasewise/phase_24_architecture_spec/` |
| Method name (frozen, provisional) | `RA-MedFiLM-BARR` — Resource-Aware MedFiLM with Benefit-Aware Refinement Routing |
| Architecture id | `ra_medfilm_barr_narrowed_v1` |
| Purpose | Answer **"what exactly will we build, train and evaluate later?"** — nothing more |
| Predecessor terminal | `PHASE23_REVIEWER_VISUALS_COMPLETE__SCIENCE_UNCHANGED__PHASE24_NARROWED_SPEC_ELIGIBLE_NOT_STARTED` |
| Phase-23 novelty basis | `PARTIALLY_OCCUPIED__NARROWER_NOVELTY_POSSIBLE` (max claim **Level 2**; strongest residual = axis **D**) |
| New training | **NONE** |
| Segmentation inference | **NONE** |
| Benefit-router inference | **NONE** |
| Router-holdout outcomes read | **0** |
| TEST | **CLOSED** — 0 image reads, 0 mask reads, 0 inference, 0 visualizations |
| Phase 25 | **ELIGIBLE, NOT STARTED** |
| Terminal state | `PHASE24_NARROWED_BENEFIT_AWARE_REFINEMENT_SPEC_COMPLETE__PHASE25_ELIGIBLE_NOT_STARTED` |

**What Phase 24 is.** A *pre-registration specification*. It fixes the architecture, the
contracts, the data protocol, the comparator set, the ablations, the statistics and the
success/failure criteria **before** anything is built, so that later experiments cannot
be retro-fitted to a convenient narrative.

**What Phase 24 is NOT.** It is **NOT** an implementation, **NOT** a training phase, and it
does **NOT** produce any experimental result. Every numeric target below is a **DESIGN
TARGET** and is explicitly marked **unmeasured**. The frozen method name may not be used to
assert a finding.
"""))

# ---------------------------------------------------------------------------
# §2. ENTRY GATE
# ---------------------------------------------------------------------------
cells.append(md("""
## 2. Entry gate (fail-closed)

Before writing any Phase-24 artifact, every predecessor identity and governance lock is
verified. The gate is **fail-closed**: a single failed check aborts with
`PHASE24_NARROWED_SPEC_BLOCKED__REDESIGN_REQUIRED`. It never repairs frozen science.
"""))

cells.append(code("""
import json, hashlib, pathlib
import pandas as pd

ROOT = pathlib.Path(r"D:/Softfors/jup")
AUD = ROOT / "reports" / "audits"
TAB = ROOT / "reports" / "tables"

from IPython.display import Image, Markdown, display

def _j(p):
    p = pathlib.Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}

def sty(df, uid, fmt=None):
    \"\"\"Deterministic pandas Styler (fixed uuid so builds are byte-identical).\"\"\"
    s = df.style
    if fmt:
        s = s.format(fmt)
    return s.set_uuid(uid)

FIG = ROOT / "reports" / "figures" / "phase24_architecture_spec"

def fig(name, caption=None):
    \"\"\"Embed a Phase-24 DESIGN figure as a REAL inline image output.

    FAIL-CLOSED: raises if the figure is missing, empty, or not a valid PNG.
    Figures are built by scripts/analysis/build_phase24_figures.py from the frozen
    Phase-24 design tables/audits only.
    \"\"\"
    p = FIG / name
    if not p.exists():
        raise FileNotFoundError(f"FAIL-CLOSED: required Phase-24 figure missing: {p}")
    raw = p.read_bytes()
    if not raw.startswith(b"\\x89PNG\\r\\n\\x1a\\n"):
        raise ValueError(f"FAIL-CLOSED: not a PNG: {p}")
    if len(raw) < 2048:
        raise ValueError(f"FAIL-CLOSED: suspiciously small PNG ({len(raw)}B): {p}")
    _img = Image(data=raw, format="png", embed=True)
    return display(_img) if caption is None else display(Markdown(f"**{caption}**"), _img)

gate = _j(AUD / "phase24_entry_gate.json")
print("entry gate verdict  :", gate.get("verdict"))
print("checks              :", f"{gate.get('n_passed')}/{gate.get('n_checks')}")
print("no training         :", gate.get("no_training"))
print("no segmentation inf :", gate.get("no_segmentation_inference"))
print("no router inf       :", gate.get("no_router_inference"))
print("TEST reads          :", gate.get("test_reads"))
print("phase24 started     :", gate.get("phase24_started"))
print("phase25 started     :", gate.get("phase25_started"))
print()
for k, v in gate.get("bindings", {}).items():
    print(f"  {k:34s} {str(v)[:24]}")
"""))

# ---------------------------------------------------------------------------
# §3. HARD BOUNDARIES
# ---------------------------------------------------------------------------
cells.append(md("""
## 3. Hard boundaries respected by this notebook

| Boundary | Status in Phase 24 |
|---|---|
| NO TRAINING | respected — 0 optimizers, 0 backward passes, 0 checkpoint writes |
| NO SEGMENTATION INFERENCE | respected — 0 model forward calls |
| NO BENEFIT-ROUTER FORWARD CALL | respected — the router does not exist yet |
| NO REFINEMENT EXECUTION | respected — `R_psi` does not exist yet |
| NO HOLDOUT OUTCOME INSPECTION | respected — `ROUTER_HOLDOUT` outcomes read = 0 |
| NO TEST ACCESS | respected — TEST remains CLOSED |
| NO SUPERVISED RESULT CHANGE | respected — the 808-case VAL stays `SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK` |
| NO LITERATURE RERUN | respected — the prior-art table is a design input, not a new search |
| DO NOT START PHASE 25 | respected — 0 modules of 25A–25G started |
"""))

# ---------------------------------------------------------------------------
# §4. NARROWED CONTRIBUTION
# ---------------------------------------------------------------------------
cells.append(md("""
## 4. The narrowed contribution (Phase-23 residual, adopted verbatim)

Phase 23 found the individual primitives **occupied**. Adopted without re-litigation:

| Axis | Phase-23 status |
|---|---|
| A — problem formulation | `OCCUPIED` |
| B — learning target | `NOT_OCCUPIED_AS_A_LEARNED_SEGMENTATION_TARGET` |
| C — decision mechanism | `PARTIALLY_OCCUPIED` |
| D — system integration | `NOT_OCCUPIED_AS_A_COMBINATION` — **strongest residual** |

**The single novelty-bearing component** is therefore, and only:

> a **learned, GT-free, pre-refinement** predictor of the **paired refinement gain**, used to
> route an **optional** regional refinement, with a **preservation fallback** and an
> **explicit resource-cost term**, inside **one shared multi-domain medical-segmentation system**.
"""))

cells.append(code("""
nov = _j(AUD / "phase24_novelty_boundary.json")
print("overall label      :", nov.get("phase23_overall_label"))
print("max claim level    :", nov.get("phase23_maximum_defensible_claim_level"))
print("strongest residual :", nov.get("phase23_axes", {}).get("strongest_residual"))
print("claim level now    :", nov.get("claim_level_permitted_now"))
print("level 3 status     :", nov.get("level_3_status"))
print()
print("novelty-bearing component:")
print("  ", nov.get("novelty_bearing_component"))
print()
print("explicit non-claims:")
for c in nov.get("explicit_non_claims", []):
    print("   -", c)
"""))

# ---------------------------------------------------------------------------
# §5. METHOD NAME + TERMINOLOGY
# ---------------------------------------------------------------------------
cells.append(md("""
## 5. Frozen method name and terminology

Two candidates were evaluated against five criteria. `RA-MedFiLM-BARR` was selected.

| Candidate | Verdict | Decisive reason |
|---|---|---|
| **`RA-MedFiLM-BARR`** — Resource-Aware MedFiLM with Benefit-Aware Refinement Routing | **SELECTED** | Encodes both load-bearing facts: routing is **benefit-aware** *and* **resource-aware**; "Benefit-Aware … Routing" signals **pre-execution**, which is exactly the JFS axis |
| `RA-MedFiLM-GGR` — Resource-Aware MedFiLM with Gain-Gated Refinement | `NOT_SELECTED` | "Gating" is overloaded **and** names the method after the primitive Phase 23 classified as `OCCUPIED` |

**Retired name:** `Counterfactual Benefit-Certified Refinement / CBCR` — *Counterfactual* is
unsupported (both potential outcomes are fully observed during development ⇒ no identification
problem ⇒ `PREFER_PAIRED_REFINEMENT_GAIN`); *Certified* is unsupported (no conformal, risk-control
or calibration guarantee is earned ⇒ `USE_BENEFIT_AWARE_ONLY`).
"""))

cells.append(code("""
nm = _j(AUD / "phase24_method_naming_decision.json")
print("frozen method name :", nm.get("frozen_method_name"))
print("expansion          :", nm.get("frozen_method_name_expansion"))
print("short form         :", nm.get("short_form"))
print("frozen for phases  :", nm.get("frozen_for_phases"))
print("retired name       :", nm.get("retired_name"))
print("forbidden tokens   :", nm.get("forbidden_tokens_in_name"))
print("forbidden check    :", nm.get("forbidden_tokens_check"))
print("binding            :", nm.get("binding"))
print()
rows = []
for c in nm.get("candidates_evaluated", []):
    rows.append({
        "candidate": c.get("candidate"),
        "verdict": c.get("verdict"),
        "acronym_ambiguity": c.get("acronym_ambiguity", "").split(" \\u2014 ")[0],
        "terminology_collision": c.get("terminology_collision", "").split(" \\u2014 ")[0],
    })
display(sty(pd.DataFrame(rows), "p24-naming"))
"""))

# ---------------------------------------------------------------------------
# §6. SYSTEM ARCHITECTURE OVERVIEW
# ---------------------------------------------------------------------------
cells.append(md("""
## 6. System architecture — overview

Seven components. Only **two** are novelty-bearing (the router `B_phi` and the gate, together,
inside the integration).

| id | Component | Symbol | Role | Novelty-bearing |
|---|---|---|---|---|
| GLOBAL | Frozen Global MedFiLM reference | `G` | fallback output + reusable features | no |
| ROI | GT-free region proposal | `P_roi` | propose the refinement region | no |
| R | Dedicated regional refiner | `R_psi` | produce the optional refinement | no |
| B | Benefit router | `B_phi` | predict paired gain BEFORE refinement | **YES** |
| GATE | Pre-execution resource-aware gate | `U_hat > tau` | EXECUTE / SKIP | **YES (with B)** |
| S | Post-refinement safety selector | `S_omega` | preserve quality AFTER refinement | no |
| FUSE | Fusion rule | `F` | compose the final mask | no |
"""))

cells.append(code("""
fig("p24_full_system_architecture.png",
    "Figure 1 — Full system architecture (DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS)")
"""))

cells.append(code("""
ms = pd.read_csv(TAB / "phase24_module_spec.csv")
print(f"module spec: {len(ms)} rows x {len(ms.columns)} cols")
display(sty(ms, "p24-modules"))
"""))

# ---------------------------------------------------------------------------
# §7. GLOBAL REFERENCE (FROZEN ANCHOR)
# ---------------------------------------------------------------------------
cells.append(md("""
## 7. Global reference — the frozen anchor

The Phase-21 Global MedFiLM is bound by SHA and **must not be modified** during the initial
controlled Phase-25 experiments. It supplies the fallback output and — critically — the
reusable features `F_global`.

**Feature-reuse requirement.** The router MUST reuse `F_global`. A *second* full Global MedFiLM
forward purely to make the routing decision is **FORBIDDEN**: it would destroy the
compute-saving claim (Phase-23 constraint C4).
"""))

cells.append(code("""
arch = _j(AUD / "phase24_architecture_spec.json")
g = arch.get("global_reference", {})
print("role               :", g.get("role"))
print("signature          :", g.get("signature"))
print("architecture       :", g.get("architecture"))
print("parameters         :", f"{g.get('parameters'):,}")
print("sha256             :", str(g.get("sha256"))[:32], "...")
print("modification policy:", g.get("modification_policy"))
print()
print("feature reuse rule :", g.get("feature_reuse_requirement"))
print()
prev = gate.get("bindings", {})
print("checkpoint SHA matches entry gate:",
      g.get("sha256") == prev.get("phase21_best_pt_sha256"))
"""))

# ---------------------------------------------------------------------------
# §8. GT-FREE REGION PROPOSAL
# ---------------------------------------------------------------------------
cells.append(md("""
## 8. GT-free region proposal `P_roi`

Frozen rule: predicted foreground → tight bounding box → fixed context expansion → clip →
square pad → resize to the refiner resolution.

- Constants derived from **TRAIN only**; tuning on VAL **forbidden**; GT rescue **forbidden**.
- `empty_global_prediction` primary behaviour = **`A_SKIP_REFINEMENT`**: the minimal, GT-free,
  zero-extra-cost rule. If the global model predicts no foreground there is no region to refine
  and the fallback preserves the global output.
- A deterministic cheap uncertainty rescue is retained **only** as a pre-registered controlled
  ablation, with constants from TRAIN only and frozen before Phase 25.
"""))

cells.append(code("""
rp = arch.get("region_proposal", {})
print("gt_free            :", rp.get("gt_free"))
print("frozen rule        :", rp.get("frozen_rule"))
print("constants source   :", rp.get("constants_source"))
print("val tuning forbidden:", rp.get("tuning_on_val_forbidden"))
print("empty-pred primary :", rp.get("empty_global_prediction_primary_behavior"))
print("gt rescue forbidden:", rp.get("gt_rescue_forbidden"))
"""))

# ---------------------------------------------------------------------------
# §9. DEDICATED REGIONAL REFINER
# ---------------------------------------------------------------------------
cells.append(md("""
## 9. Dedicated regional refiner `R_psi`

**Must not be** the frozen Global MedFiLM checkpoint reused on resampled crops — Phase 22 showed
that reuse was **harmful in aggregate** (−0.0425 macro, negative in every domain).

| Property | Value |
|---|---|
| Class | dedicated crop-trained lightweight residual U-Net / encoder–decoder |
| Input contract | `[R, G, B, p_global_crop]`; task/domain conditioning permitted |
| Forbidden inputs | GT mask, GT geometry, GT size category, any GT-derived score |
| Parameter envelope (DESIGN TARGET, **unmeasured**) | 0.5M–1.5M recommended; **hard ceiling 2.0M** |
| Output role | a **candidate**, never a replacement, until the final selection |
| Novelty claimed | **False** |
"""))

cells.append(code("""
rr = arch.get("regional_refiner", {})
print("must_not_be        :", rr.get("must_not_be"))
print("class              :", rr.get("class"))
print("input contract     :", rr.get("input_contract", {}).get("conceptual"))
print("forbidden inputs   :", rr.get("input_contract", {}).get("forbidden_inputs"))
env = rr.get("target_parameter_envelope", {})
print("param envelope     :", f"{env.get('recommended_min'):,} - {env.get('recommended_max'):,}"
      f"  (hard ceiling {env.get('hard_ceiling'):,})")
print("measured?          :", env.get("measured"), " <- DESIGN TARGET ONLY")
print("novelty claimed    :", rr.get("novelty_claimed"))
"""))

# ---------------------------------------------------------------------------
# §10. BENEFIT ROUTER (NOVELTY-BEARING)
# ---------------------------------------------------------------------------
cells.append(md("""
## 10. Benefit router `B_phi` — the novelty-bearing component

Its job is to estimate the expected **paired refinement gain** *before* `R_psi` executes. It is
**not** an uncertainty predictor.

- `pre_refinement = True`, `gt_free = True`.
- Output: primary `Delta_hat_Dice`; optional auxiliary `p_harm`.
- Architecture family: small MLP / shallow feature-fusion network. Forbidden: transformer router,
  foundation model, a second image encoder.
- Envelopes (**DESIGN TARGETS, unmeasured**): ≤ **250,000** params; ≤ **2%** of one global
  forward's analytical MACs, preferred **1%**.
"""))

cells.append(code("""
br = arch.get("benefit_router", {})
print("symbol / pre_refine:", br.get("symbol"), "/", br.get("pre_refinement"))
print("gt_free            :", br.get("gt_free"))
print("job                :", br.get("job"))
print("output (primary)   :", br.get("output", {}).get("primary"))
print("architecture family:", br.get("architecture_family"))
print("forbidden arch     :", br.get("forbidden_architecture"))
pe = br.get("target_parameter_envelope", {})
ce = br.get("compute_envelope", {})
print("max params         :", f"{pe.get('max_parameters'):,}", " measured?", pe.get("measured"))
print("max MACs fraction  :", ce.get("max_analytical_macs_fraction_of_one_global_forward"),
      " preferred:", ce.get("preferred_fraction"), " measured?", ce.get("measured"))
"""))

# ---------------------------------------------------------------------------
# §11. ROUTER INPUT CONTRACT
# ---------------------------------------------------------------------------
cells.append(md("""
## 11. Router input contract

Every router input must satisfy **all three** fail-closed properties:
`uses_GT = false` **AND** `available_pre_refinement = true` **AND** `inference_available = true`.

A GT-derived feature would make the router unavailable at deployment; a post-refinement feature
would break the pre-execution gate (Phase-23 constraints C1 and C4).
"""))

cells.append(code("""
ric = pd.read_csv(TAB / "phase24_router_input_contract.csv")

def _b(series):
    \"\"\"Robust bool dtype: accepts real bools and the literal strings true/false/yes/no.

    Always returns a genuine bool dtype, because ~ on an object-dtype Series of Python
    bools performs an INTEGER bitwise NOT (~True == -2, truthy) instead of a logical not.
    \"\"\"
    if series.dtype == bool:
        return series
    return (series.astype(str).str.lower()
            .map({"true": True, "false": False, "yes": True, "no": False})
            .fillna(False).astype(bool))

ric["_allowed"] = _b(ric["allowed"])
ric["_uses_gt"] = _b(ric["uses_GT"])
ric["_pre"] = _b(ric["available_pre_refinement"])
ric["_inf"] = _b(ric["inference_available"])

allowed = ric[ric["_allowed"]]
forbidden = ric[~ric["_allowed"]]
print(f"router input contract: {len(ric)} rows ({len(allowed)} allowed / {len(forbidden)} forbidden)")

# FAIL-CLOSED: every allowed row must be GT-free, pre-refinement and inference-available
bad = allowed[allowed["_uses_gt"] | (~allowed["_pre"]) | (~allowed["_inf"])]
print("allowed rows violating the GT-free contract:", len(bad))
assert len(bad) == 0, "FAIL-CLOSED: an allowed router input is not GT-free/pre-refinement"
print("all allowed inputs are GT-free, pre-refinement and inference-available: PASS")
display(sty(allowed[["feature", "source", "primary_or_optional"]], "p24-ric-allowed"))
display(sty(forbidden[["feature", "reason"]], "p24-ric-forbidden"))
"""))

# ---------------------------------------------------------------------------
# §12. PAIRED REFINEMENT GAIN CONTRACT
# ---------------------------------------------------------------------------
cells.append(md("""
## 12. Paired refinement gain contract

$$\\Delta\\mathrm{Dice}_i = \\mathrm{Dice}(R_i, y_i) - \\mathrm{Dice}(G_i, y_i)$$

This is a **supervised paired contrast**. During development both arms are fully observed — the
system may simply run the refinement. There is **no missing arm and therefore no identification
problem**, and the refinement is deterministic given `(x, frozen model, frozen ROI rule)`. It
**must not** be described as a causal / counterfactual / individual treatment effect.

The CATE analogy may be stated **at most once**, with the clarification that the estimand is a
deterministic paired contrast.
"""))

cells.append(code("""
pg = _j(AUD / "phase24_paired_refinement_gain_contract.json")
print("primary term       :", pg.get("primary_term"))
print("definition         :", pg.get("definition"))
print("nature             :", pg.get("nature"))
print("must_not_describe  :", pg.get("must_not_be_described_as"))
print("why not causal     :", pg.get("why_not_causal"))
print()
print("uses_GT_for_labels :", pg.get("uses_GT_for_labels"))
print("uses_GT_for_inputs :", pg.get("uses_GT_for_inputs"), " <- labels only")
print("used as router input:", pg.get("computation_used_as_router_input"))
print("training population:", pg.get("training_population"))
"""))

# ---------------------------------------------------------------------------
# §13. TRAIN-ONLY DATA PROTOCOL
# ---------------------------------------------------------------------------
cells.append(md("""
## 13. TRAIN-only data protocol

**Critical leakage constraint:** benefit-router training labels may **never** be generated from the
existing Phase-22 VAL population. Only original TRAIN may be used.

| Population | n | Role |
|---|---|---|
| Original TRAIN | **5832** | source of the two router splits |
| `ROUTER_DEVELOPMENT` (85%) | **≈4957** | cross-fitted gain labels + router fitting + threshold calibration |
| `ROUTER_HOLDOUT` (15%) | **≈875** | clean out-of-sample routing evaluation |
| VAL (existing) | **808** | `SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK` |
| TEST | 1683 | **CLOSED** |
"""))

cells.append(code("""
dp = _j(AUD / "phase24_benefit_data_protocol.json")
tr = dp.get("original_train", {})
sp = dp.get("split", {})
print("manifest           :", tr.get("manifest"))
print("n_cases            :", tr.get("n_cases"))
print("domains            :", tr.get("domains"))
print("grouping key       :", tr.get("grouping_key"))
print()
for k in ("ROUTER_HOLDOUT", "ROUTER_DEVELOPMENT"):
    s = sp.get(k, {})
    print(f"{k:20s} {s.get('fraction')}  ~{s.get('approx_cases')}  {s.get('status')}")
print("domain_stratified  :", sp.get("domain_stratified"))
print("group_safe         :", sp.get("group_safe"))
print("overlap            :", sp.get("overlap"))
print("uses_phase22_val   :", sp.get("uses_phase22_val"))
print("uses_test          :", sp.get("uses_test"))
"""))

cells.append(code("""
fig("p24_train_router_holdout_flow.png",
    "Figure 2 — TRAIN-only router development protocol (DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS)")
"""))

# ---------------------------------------------------------------------------
# §14. HOLDOUT DISCIPLINE
# ---------------------------------------------------------------------------
cells.append(md("""
## 14. `ROUTER_HOLDOUT` discipline

The holdout is designated **before** any refiner-performance inspection, benefit-router fitting,
feature selection, lambda selection or threshold fitting. In Phase 24 only **structural** facts
were inspected.
"""))

cells.append(code("""
rh = arch.get("router_holdout_contract", {})
print("designated_before  :")
for x in rh.get("designated_before", []):
    print("   -", x)
print()
print("inspected_in_phase24 (allowed):", rh.get("inspected_in_phase24"))
print("must_not_inspect_in_phase24   :")
for x in rh.get("must_not_inspect_in_phase24", []):
    print("   -", x)
print()
print("outcomes_read_in_phase24:", rh.get("outcomes_read_in_phase24"))
assert rh.get("outcomes_read_in_phase24") == 0
"""))

# ---------------------------------------------------------------------------
# §15. VAL RECLASSIFICATION + TEST LOCK
# ---------------------------------------------------------------------------
cells.append(md("""
## 15. VAL reclassification and TEST lock

The existing frozen Phase-22 808-case VAL is reclassified as a
**`SECONDARY / CONTINUITY DEVELOPMENT BENCHMARK`**. It is **not** router training data and
**not** an untouched routing holdout. This reclassification is stated in every protocol artifact.
"""))

cells.append(code("""
vr = arch.get("VAL_role", {})
print("population         :", vr.get("population"))
print("role               :", vr.get("role"))
print("is_router_train    :", vr.get("is_router_training_data"))
print("is_untouched_holdout:", vr.get("is_untouched_routing_holdout"))
print("explicit everywhere:", vr.get("explicit_in_all_protocol_artifacts"))
print()
tl = arch.get("TEST_lock", {})
print("TEST lock          :", tl)
assert all(v == 0 for k, v in tl.items() if k != "status")
print()
drc = pd.read_csv(TAB / "phase24_data_role_contract.csv")
display(sty(drc, "p24-datarole"))
"""))

# ---------------------------------------------------------------------------
# §16. CROSS-FITTING
# ---------------------------------------------------------------------------
cells.append(md("""
## 16. Out-of-fold 3-fold cross-fitting

Within `ROUTER_DEVELOPMENT`: for fold *k*, train `R_psi` on folds ≠ *k*, infer `R_psi` on fold *k*,
and compute `DeltaDice_i` for fold-*k* samples. The concatenation yields **out-of-fold** gain labels.

Purpose: prevent refiner-overfit gain labels from entering the router target. The refiner must be
**cross-fitted**, never fit and evaluated on the same samples.
"""))

cells.append(code("""
fig("p24_crossfit_gain_label_generation.png",
    "Figure 3 — Out-of-fold paired-gain label generation (DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS)")
"""))

cells.append(code("""
cf = arch.get("crossfit_contract", {})
print("folds              :", cf.get("folds"))
print("within             :", cf.get("within"))
print("procedure          :", cf.get("procedure"))
print("output             :", cf.get("output"))
print("executed_in_phase24:", cf.get("executed_in_phase24"))
assert cf.get("executed_in_phase24") is False
"""))

# ---------------------------------------------------------------------------
# §17. RESOURCE UTILITY
# ---------------------------------------------------------------------------
cells.append(md("""
## 17. Pre-execution resource utility

$$\\hat{U}_i = \\hat{\\Delta}_i - \\lambda C_i \\quad\\Rightarrow\\quad \\hat{U}_i > \\tau \\;\\Rightarrow\\; \\text{EXECUTE, else SKIP}$$

A **single universal lambda is forbidden**. A small set of lambda values is pre-registered with a
fixed-budget sweep: **0% / 10% / 25% / 50% / 100%** (0% = global-only, 100% = always-refine).

**Cost terminology.** Cost is **normalized analytical incremental MACs**. Analytical MACs is **not**
latency and must never be described as CPU/mobile latency; device measurement belongs to Phase 34.
The cost term is required by Phase-23 constraint **C6**.
"""))

cells.append(code("""
ru = _j(AUD / "phase24_resource_utility_contract.json")
print("utility            :", ru.get("utility"))
print("decision rule      :", ru.get("decision_rule"))
print("single lambda forbidden:", ru.get("single_universal_lambda_forbidden"))
print("fixed budget points:", ru.get("fixed_budget_evaluation", {}).get("points"))
print("cost proxy         :", ru.get("cost_proxy", {}).get("primary_for_phase25"))
print("kept separate      :", ru.get("cost_proxy", {}).get("terminology_kept_separate"))
print("analytical != latency:", ru.get("cost_proxy", {}).get("analytical_macs_is_not_latency"))
print("device measurement phase:", ru.get("cost_proxy", {}).get("device_measurement_phase"))
print("required by        :", ru.get("cost_term_required_by"))
print("measured in phase24:", ru.get("measured_in_phase24"))
"""))

cells.append(code("""
fig("p24_resource_budget_evaluation.png",
    "Figure 4 — Pre-registered fixed-budget evaluation grid (DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS)")
"""))

# ---------------------------------------------------------------------------
# §18. PRE-EXECUTION GATE + POST-REFINEMENT SAFETY
# ---------------------------------------------------------------------------
cells.append(md("""
## 18. The pivotal separation: pre-execution gate vs post-refinement safety

This separation is the **load-bearing structural claim** of the narrowed specification.

| | Pre-execution gate | Post-refinement safety `S_omega` |
|---|---|---|
| Rule | `if U_hat > tau then EXECUTE else SKIP` | accept or reject the refinement output |
| When | **before** `R_psi` executes | **after** `R_psi` has executed |
| Saves compute? | **YES** | **NO** |
| Novelty | part of the residual | `CONTROLLED_CORE_EXTENSION`, closest to JFS |
| Mandated ablation | — | A7 (no post-safety) vs A8 (with post-safety) |

`S_omega` must **NEVER** be presented as the compute-saving mechanism, because JFS already occupies
the post-hoc decision. Post-hoc selection ≠ pre-execution routing.
"""))

cells.append(code("""
fig("p24_pre_gate_vs_post_safety.png",
    "Figure 5 — Pre-execution gate vs post-refinement safety (DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS)")
"""))

cells.append(code("""
pg2 = arch.get("pre_execution_gate", {})
ps = arch.get("post_safety", {})
print("pre-execution gate :", pg2.get("rule"), "| evaluates", pg2.get("evaluated_before"))
print("fixed budget points:", pg2.get("fixed_budget_points"))
print()
print("post-safety symbol :", ps.get("symbol"))
print("post-safety role   :", ps.get("role"))
print("saves compute      :", ps.get("saves_compute"), " <- NOT the compute saver")
print("classification     :", ps.get("classification"))
print("mandatory ablation :", ps.get("mandatory_ablation"))
print("novelty claimed    :", ps.get("novelty_claimed"))
"""))

# ---------------------------------------------------------------------------
# §19. PRESERVATION FALLBACK
# ---------------------------------------------------------------------------
cells.append(md("""
## 19. Preservation fallback and non-inferiority

The global output must remain **available** until the final selection. **No destructive replacement**
may occur before the final decision.

| Outcome | Final output |
|---|---|
| `SKIP` | global |
| `EXECUTE_THEN_REJECT` | global |
| `EXECUTE_THEN_ACCEPT` | regional-fused |

**Non-inferiority test (frozen before Phase 25):** `Delta = Dice(final routed) − Dice(global)`;
margin **0.005**; the claim is permitted **only if** the lower confidence bound of `Delta > −0.005`.
Per-domain reporting is **mandatory** — the macro average may not hide domain-specific harm.
"""))

cells.append(code("""
pc = _j(AUD / "phase24_preservation_contract.json")
print("principle          :", pc.get("principle"))
for k, v in pc.get("outcomes", {}).items():
    print(f"  {k:22s} -> {v}")
print("destructive replacement before decision:", pc.get("destructive_replacement_before_final_decision"))
print()
ni = pc.get("non_inferiority", {})
print("metric             :", ni.get("metric"))
print("margin             :", ni.get("margin"))
print("claim only if      :", ni.get("claim_only_if"))
print("per-domain report  :", ni.get("per_domain_reporting"))
print("macro may not hide :", ni.get("macro_may_not_hide_domain_harm"))
"""))

# ---------------------------------------------------------------------------
# §20. FUSION + TASK CONDITIONING
# ---------------------------------------------------------------------------
cells.append(md("""
## 20. Fusion and task conditioning

- Fusion primary rule: **outside ROI retain `p_global`; inside ROI replace with `p_refined`.**
  **No learned fusion in the primary design** — it would confound the benefit-routing hypothesis.
  Learned fusion is a future controlled ablation only.
- Task conditioning: **ONE shared router**, task/domain conditioning allowed. Separate per-domain
  routers are **forbidden** in the primary design (this preserves the shared multi-domain
  contribution); they are later controlled ablations only.
"""))

cells.append(code("""
fr = arch.get("fusion_rule", {})
tc = arch.get("task_conditioning", {})
print("fusion primary     :", fr.get("primary"))
print("learned fusion pri.:", fr.get("learned_fusion_in_primary"))
print("reason             :", fr.get("reason"))
print("future             :", fr.get("learned_fusion"))
print()
print("task conditioning  :", tc.get("primary_design"))
print("per-domain routers :", tc.get("separate_per_domain_routers"))
print("reason             :", tc.get("reason"))
"""))

# ---------------------------------------------------------------------------
# §21. HYPOTHESES
# ---------------------------------------------------------------------------
cells.append(md("""
## 21. Hypotheses — PRE-REGISTERED, NOT RESULTS

**H1 is load-bearing.** If H1 fails, the narrowed contribution has no empirical support.
"""))

cells.append(code("""
hy = arch.get("hypotheses", {})
print("status             :", hy.get("status"))
print("load-bearing       :", hy.get("load_bearing"))
print()
for k in ("H1", "H2", "H3", "H4", "H5", "H6"):
    print(f"{k}: {hy.get(k)}")
    print()
"""))

# ---------------------------------------------------------------------------
# §22. COMPARATORS
# ---------------------------------------------------------------------------
cells.append(md("""
## 22. Pre-registered comparators (11 rows, **no ranking**)

`C7 LEARNED_PAIRED_GAIN_ROUTING` is the load-bearing comparator. `C10 ORACLE_BENEFIT_ROUTING`
is an upper bound only — it uses GT, is **not deployable**, and is never a result.
`C11 JFS_LIKE_POST_HOC_SELECTOR` is optional; if included it must record **full** refinement compute,
because the expensive operation already occurred.
"""))

cells.append(code("""
cp = pd.read_csv(TAB / "phase24_comparator_plan.csv")
print(f"comparators: {len(cp)} rows x {len(cp.columns)} cols")
display(sty(cp, "p24-comparators"))
"""))

# ---------------------------------------------------------------------------
# §23. METRICS
# ---------------------------------------------------------------------------
cells.append(md("""
## 23. Metrics

Grouped exactly as pre-registered. No metric is added or removed after seeing a result.
"""))

cells.append(code("""
m = arch.get("metrics", {})
for k, v in m.items():
    print(f"{k:18s} {', '.join(v)}")
"""))

# ---------------------------------------------------------------------------
# §24. STATISTICS
# ---------------------------------------------------------------------------
cells.append(md("""
## 24. Statistics — paired bootstrap, pre-registered

`n_boot = 2000`, `seed = 42`, domain-stratified for macro-domain metrics. Report the point
estimate, 95% CI, and paired p-value where appropriate. TEST is never used.
"""))

cells.append(code("""
st = arch.get("statistics", {})
print("method             :", st.get("method"))
print("n_boot             :", st.get("n_boot"))
print("seed               :", st.get("seed"))
print("domain-stratified  :", st.get("domain_stratified_for"))
print("report             :", st.get("report"))
print("test used          :", st.get("test_used"))
"""))

# ---------------------------------------------------------------------------
# §25. SUCCESS / FAILURE CRITERIA
# ---------------------------------------------------------------------------
cells.append(md("""
## 25. Success and failure criteria — frozen before Phase 25

**Failures (F1–F5):** `REFINER_FAILURE`, `ROUTER_FAILURE`, `PRESERVATION_FAILURE`,
`RESOURCE_FAILURE`, `DOMAIN_COLLAPSE`.
**Successes (S1–S3):** `H1_SUPPORTED`, `PRESERVATION_SATISFIED`, `FRONTIER_MEASURED`.
"""))

cells.append(code("""
sfc = pd.read_csv(TAB / "phase24_success_failure_criteria.csv")
print(f"criteria: {len(sfc)} rows x {len(sfc.columns)} cols")
display(sty(sfc, "p24-criteria"))
"""))

cells.append(code("""
_fr = _b(sfc["frozen_before_phase25"])
assert _fr.all(), "FAIL: a criterion is not frozen"
print("all criteria frozen before Phase 25: PASS")
"""))

# ---------------------------------------------------------------------------
# §26. ABLATIONS
# ---------------------------------------------------------------------------
cells.append(md("""
## 26. Ablation plan — core A0–A8, router R1–R3, refiner F1

None executed in Phase 24; all pre-registered.
"""))

cells.append(code("""
ab = pd.read_csv(TAB / "phase24_ablation_plan.csv")
print(f"ablations: {len(ab)} rows x {len(ab.columns)} cols")
_exec = _b(ab["executed_in_phase24"])
assert (~_exec).all(), "FAIL: an ablation claims execution"
print("none executed in Phase 24: PASS")
display(sty(ab, "p24-ablations"))
"""))

# ---------------------------------------------------------------------------
# §27. PHASE-25 MODULE PLAN
# ---------------------------------------------------------------------------
cells.append(md("""
## 27. Phase-25 module plan — PRE-REGISTERED, NOT STARTED

Ordering constraint: the router may only be fitted **after** out-of-fold gain labels exist
(25C precedes 25D).
"""))

cells.append(code("""
pp = _j(AUD / "phase24_phase25_module_plan.json")
print("status             :", pp.get("status"))
print("phase25_started    :", pp.get("phase25_started"))
print("no_module_started  :", pp.get("no_module_started"))
print()
for mm in pp.get("modules", []):
    dep = ", ".join(mm.get("starts_after") or []) or "-"
    print(f"  {mm.get('id')}  {mm.get('name'):52s} depends on: {dep}")
assert pp.get("no_module_started") is True and pp.get("phase25_started") is False
"""))

# ---------------------------------------------------------------------------
# §28. TINY-STRUCTURE ROLE
# ---------------------------------------------------------------------------
cells.append(md("""
## 28. Tiny-structure role — reporting only

Tiny structures are a **stratification of the analysis**, never a tuning target, never a routing
input, and they cannot be used to select lambda or thresholds. This follows the frozen Phase-22
finding that benefit is strongly heterogeneous but not deployably predictable, and the
`kub_size_clean_v3_v1` taxonomy's rule that `<32 px = tiny` is **not** a project definition.
"""))

cells.append(code("""
print("tiny-structure role: REPORTING_ONLY")
print("  - not a tuning target")
print("  - not a routing input")
print("  - cannot select lambda or thresholds")
print("  - '<32 px = tiny' is NOT a project definition")
print()
print("KUB taxonomy (frozen):", "kub_size_clean_v3_v1")
print("  Q25/50/75 ratios   :",
      "0.0001497998649691358 / 0.0003401438395182292 / 0.0008279682677469136 (lower-inclusive)")
"""))

# ---------------------------------------------------------------------------
# §29. FEATURE REUSE
# ---------------------------------------------------------------------------
cells.append(md("""
## 29. Feature reuse — bridge / decoder2 / decoder1

The router reads *pooled summaries* of features the global forward has **already produced**. This is
a hard requirement, not an optimisation: re-running the global model to make the routing decision
would erase the compute saving that justifies the whole design.
"""))

cells.append(code("""
ric2 = pd.read_csv(TAB / "phase24_router_input_contract.csv")
_ok = _b(ric2["allowed"])
src = ric2[_ok]["source"].value_counts().to_dict()
for k, v in src.items():
    print(f"  {v:2d}  {k}")
print()
print("requirement:", g.get("feature_reuse_requirement"))
"""))

# ---------------------------------------------------------------------------
# §30. PRIOR-ART DIFFERENTIATION
# ---------------------------------------------------------------------------
cells.append(md("""
## 30. Prior-art differentiation (12 rows, 14 cols, **unranked**)

The closest analogue is JFS, which shares the framing and a paired revert-on-failure comparison but
decides **after** the refinement has run (zero compute saved) with an **untrained** rule. The formal
antecedent is Russell & Wefald's *value of computation*. No row carries a novelty score.
"""))

cells.append(code("""
pa = pd.read_csv(TAB / "phase24_prior_art_differentiation.csv")
print(f"prior art: {len(pa)} rows x {len(pa.columns)} cols (no ranking column)")
assert not any(c in pa.columns for c in ("rank", "score", "novelty_score")), "FAIL: ranking present"
display(sty(pa[["citation_key", "year", "pre_execution", "learned_gain",
                 "compute_saved_by_gate"]], "p24-priorart"))
"""))

# ---------------------------------------------------------------------------
# §31. NOVELTY BOUNDARY FIGURE
# ---------------------------------------------------------------------------
cells.append(md("""
## 31. Novelty boundary (visual)

What is claimed versus what is explicitly **not** claimed.
"""))

cells.append(code("""
fig("p24_novelty_boundary.png",
    "Figure 6 — Novelty boundary (DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS)")
"""))

# ---------------------------------------------------------------------------
# §32. FORBIDDEN CLAIMS
# ---------------------------------------------------------------------------
cells.append(md("""
## 32. Forbidden claims

No document produced under this specification may use any of the following until the corresponding
preregistered criterion is actually met.
"""))

cells.append(code("""
fc = arch.get("forbidden_claims", [])
print(f"forbidden claims ({len(fc)}):")
for c in fc:
    print("   -", c)
print()
print("current allowed wording:", arch.get("current_allowed_wording"))
print("level-2 condition     :", arch.get("level_2_wording_condition"))
"""))

# ---------------------------------------------------------------------------
# §33. DESIGN FIGURES
# ---------------------------------------------------------------------------
cells.append(md("""
## 33. Design figures — all marked "DESIGN SPECIFICATION — NOT EXPERIMENTAL RESULTS"

Six figures, all declared in `phase24_figure_manifest.json` with
`contains_experimental_results: False` and `contains_hypothetical_performance_curves: False`.
"""))

cells.append(code("""
fm = _j(FIG / "phase24_figure_manifest.json")
print("classification     :", fm.get("classification"))
print("contains_experimental_results:", fm.get("contains_experimental_results"))
print("contains_hypothetical_curves :", fm.get("contains_hypothetical_performance_curves"))
print("n_figures          :", fm.get("n_figures"))
print()
for name, meta in fm.get("figures", {}).items():
    print(f"  {name:44s} {meta.get('bytes'):>7}B  {meta.get('sha256')[:16]}")
"""))

# ---------------------------------------------------------------------------
# §34. NO-EXECUTION AUDIT (IN NOTEBOOK)
# ---------------------------------------------------------------------------
cells.append(md("""
## 34. No-execution audit, verified from inside the notebook

The counters below are asserted to be zero. If any counter were non-zero the notebook would fail.
"""))

cells.append(code("""
ne = _j(AUD / "phase24_no_execution_audit.json")
counters = {k: v for k, v in ne.items()
            if isinstance(v, int) and ("count" in k or "reads" in k or "runs" in k
                                       or "calls" in k or "passes" in k or "inference" in k
                                       or "training" in k)}
print("no-execution counters:")
for k, v in sorted(counters.items()):
    print(f"  {k:34s} {v}")
print()
nonzero = {k: v for k, v in counters.items() if v != 0}
print("non-zero counters  :", nonzero)
assert not nonzero, f"FAIL-CLOSED: non-zero execution counters: {nonzero}"
print("ALL COUNTERS ZERO: PASS")
print()
print("verdict:", ne.get("verdict"))
"""))

# ---------------------------------------------------------------------------
# §34A. EXACT IMPLEMENTATION PRE-REGISTRATION ADDENDUM
# ---------------------------------------------------------------------------
cells.append(md("""
---
# Exact implementation pre-registration addendum

### POST-PHASE24 SPECIFICATION-COMPLETENESS REPAIR

**DESIGN SPECIFICATION — NO TRAINING PERFORMED**

This addendum closes the remaining implementation degrees of freedom **before** Phase 25, so
Phase 25 cannot silently choose architecture or protocol based on observed performance. It is
a `SPECIFICATION_COMPLETENESS_REPAIR` — **not** an architecture search and **not** a Phase-25
implementation.

| Item | Value |
|---|---|
| Architecture revision | `ra_medfilm_barr_narrowed_v1_1` (supersedes `…_v1`; **SPECIFICATION_COMPLETENESS_ONLY**) |
| Method name | `RA-MedFiLM-BARR` — **unchanged**, not a new method |
| Science changed | **NO** |
| Split seed | `MASTER_DEVELOPMENT_SEED = 42` |
| Training | **NONE** · Module instantiation: **NONE** · Forward passes: **NONE** |
| Holdout outcomes read | **0** · VAL outcome reads: **0** · TEST: **CLOSED** |
"""))

cells.append(md("""
## A.1 Frozen split seed and materialized split

**`MASTER_DEVELOPMENT_SEED = 42`** is frozen now. No pre-existing repository split with a
different seed was found, so the default applies and no superseding seed is recorded. Seed 42
drives the development/holdout split, the 3-fold refiner cross-fitting, the router-internal
ordering and the pre-registered bootstrap. It matches the project-wide
`configs/research_protocol.json` seed policy and the Phase-21 seed42 `clean_v3` run.

**Group key.** `patient_id` is a *real* identifier only for KUB (318 patients). BUSI, ISIC and
KVASIR carry `patient_id == "NOT_AVAILABLE"`, so for them the group key falls back to the
leakage-safe duplicate ledger, else a per-sample singleton. This composite key is the only
defensible leakage-safe grouping available.
"""))

cells.append(code("""
pe = _j(AUD / "phase24_benefit_data_protocol_exact.json")
print("master development seed :", pe.get("split_seed"))
print("split algorithm         :", pe.get("split_algorithm")[:110], "...")
print("stratification key      :", pe.get("stratification_key"))
print()
print("development n           :", pe.get("development_n"))
print("holdout n               :", pe.get("holdout_n"))
print("total n                 :", pe.get("total_n"))
print("holdout fraction        :", pe.get("holdout_fraction_realized"))
print()
print("domain counts (dev/hold/total):")
for dom, c in (pe.get("domain_counts") or {}).items():
    print(f"   {dom:8s} {c['development']:5d} / {c['holdout']:4d} / {c['total']:5d}")
print()
print("zero overlap (dev & hold):", pe.get("zero_overlap"))
print("zero overlap (group)     :", pe.get("zero_overlap_group_level"))
print("VAL overlap zero         :", pe.get("phase22_val_overlap_zero"))
print("TEST overlap zero        :", pe.get("test_overlap_zero"))
print("deterministic recheck    :", pe.get("deterministic_recheck"))
print("split manifest sha256    :", pe.get("manifest_sha256"))
print("holdout outcomes read    :", pe.get("holdout_outcomes_read"))
assert pe.get("zero_overlap") and pe.get("phase22_val_overlap_zero") and pe.get("test_overlap_zero")
assert pe.get("holdout_outcomes_read") == 0
"""))

cells.append(md("""
## A.2 Exact primary ROI rule

| Constant | Frozen value |
|---|---|
| Predicted-foreground threshold | `0.30` |
| Expansion factor | **`1.50`** (≡ fractional margin `0.25`, the inherited `ORACLE_DERIVED_REFINER_MARGIN`) |
| Regional input resolution | **`256 × 256`** |
| Image / probability resize | bilinear |
| GT mask resize (training target only) | nearest |
| Empty global prediction | **`FORCED_SKIP`** (no GT rescue) |

The 1.50× factor is inherited from the already-declared Phase-22 regional geometry, preserving
comparability. `256` is a **prospective design choice**, not a claim that 256 is optimal. No
TRAIN/VAL sweep over ROI scale is permitted in the primary method.
"""))

cells.append(code("""
ex = _j(AUD / "phase24_exact_implementation_spec.json")
roi = ex.get("roi", {})
print("expansion factor        :", roi.get("expansion_factor"))
print("fractional margin       :", roi.get("fractional_margin_equivalent"),
      f"({roi.get('margin_constant_name')} = {roi.get('margin_constant_value')})")
print("margin constant source  :", roi.get("margin_constant_source"))
print("input resolution        :", roi.get("input_resolution"))
print("resize modes            :", roi.get("resize_modes"))
print("empty prediction        :", roi.get("empty_prediction_behavior"))
print("gt rescue               :", roi.get("gt_rescue"))
print("roi scale sweep primary :", roi.get("train_val_sweep_over_roi_scale_in_primary"))
"""))

cells.append(md("""
## A.3 Exact regional refiner architecture — `BARRRegionalRefinerV1`

| Property | Value |
|---|---|
| Input | 4 channels `[R, G, B, p_global_crop]` |
| Output | 1-channel logits |
| Resolution | 256 × 256 |
| Encoder/bridge channels (**declared**) | `[16, 32, 64, 128, 192]` |
| Encoder/bridge channels (**active**) | `[16, 32, 64, 96, 128]` |
| Downsample | max-pool 2×2 · Upsample: bilinear ×2 · Skip: concatenate |
| Norm / activation | GroupNorm (≤8 groups) / SiLU · conv `bias=False` before GroupNorm |
| Forbidden | dropout, attention, SE, transformer, deep supervision, pretrained weights |
| Task conditioning (FiLM) | **NO** — keeps `R_psi` simple; future ablation only |

**Deterministic envelope resolution (declared BEFORE training).** The declared channels compute
to **2,317,553** parameters — which **exceeds** the 2,000,000 hard ceiling. Without consulting
any outcome, the pre-declared deterministic reduction `[16,32,64,96,128]` is adopted, giving
**1,276,401** parameters, inside the recommended 0.5M–1.5M envelope. Channels may **not** be
changed after observing performance.
"""))

cells.append(code("""
rf = ex.get("refiner", {})
print("name                    :", rf.get("name"))
print("input / output          :", rf.get("input_channels"), "->", rf.get("output_channels"),
      rf.get("output_kind"))
print("declared channels       :", rf.get("encoder_bridge_channels_declared"))
print("active channels         :", rf.get("encoder_bridge_channels_active"))
print("declared closed-form    :", f"{rf.get('expected_parameter_count_declared_channels'):,}")
print("active closed-form      :", f"{rf.get('expected_parameter_count_closed_form'):,}")
print("hard ceiling            :", f"{rf.get('hard_ceiling'):,}")
print("within hard ceiling     :", rf.get("envelope_within_ceiling"))
print("within recommended band :", rf.get("envelope_within_recommended"))
print("envelope reduction?     :", rf.get("envelope_reduction_applied"))
print()
print("alternatives considered:")
for k, v in (rf.get("envelope_reduction_alternatives_considered") or {}).items():
    print(f"   {k:34s} {v:,}")
print()
print("forbidden components    : dropout", rf.get("dropout"), "| attention", rf.get("attention"),
      "| SE", rf.get("se_blocks"), "| transformer", rf.get("transformer"),
      "| deep-sup", rf.get("deep_supervision"), "| pretrained", rf.get("pretrained_weights"))
print("task conditioning FiLM  :", rf.get("task_conditioning_film"))
"""))

cells.append(md("""
## A.4 Exact refiner training protocol and nested cross-fit roles

| Setting | Value |
|---|---|
| Loss | `0.5 * BCEWithLogits + 0.5 * soft Dice` |
| Optimizer / LR / WD | AdamW / `1e-4` / `1e-4` |
| Scheduler | cosine annealing |
| Max epochs / patience | 100 / 15 |
| Batch size / AMP | 8 / enabled when supported |
| Seed | 42 |
| Checkpoint selection | **lowest validation loss** (Dice = secondary diagnostic) |

**The nested role is the decisive point.** The held-out (OOF target) fold may be used **only**
for OOF prediction/label creation, **never** for checkpoint selection. Early stopping therefore
runs against a deterministic **TRAIN-INTERNAL 90/10 fitting/early-stop split** created inside
each refiner-training portion — group-safe, domain-stratified, seed 42. The OOF target fold
stays untouched until prediction.
"""))

cells.append(code("""
cf = ex.get("crossfit", {})
print("outer folds            :", cf.get("outer_folds"))
print("within                 :", cf.get("within"))
print("inner fitting fraction :", cf.get("inner_fitting_fraction"))
print("inner early-stop frac  :", cf.get("inner_early_stop_fraction"))
print("inner split rules      :", cf.get("inner_split_rules"))
print("oof fold role          :", cf.get("oof_fold_role"))
print("infer once per fold    :", cf.get("infer_once_per_fold"))
print("no training on fold before OOF:", cf.get("no_training_on_fold_before_oof_produced"))
print()
print("refiner training protocol:")
for k in ("loss", "optimizer", "lr", "weight_decay", "scheduler", "max_epochs",
          "early_stopping_patience", "batch_size", "seed", "checkpoint_selection"):
    print(f"   {k:24s} {rf.get(k)}")
"""))

cells.append(md("""
## A.5 Final deployment refiner rule — `R_psi_final`

This was previously underspecified. It is now frozen:

1. The three OOF refiner runs produce gain labels.
2. Determine the final training duration prospectively as the **median integer best epoch** of
   the three OOF refiner runs.
3. **Reinitialize** `BARRRegionalRefinerV1` from **seed 42**.
4. Train on **all executable-action `ROUTER_DEVELOPMENT` samples** for **exactly** that many
   epochs, using the frozen optimizer/loss/scheduler.

**No early stopping on `ROUTER_HOLDOUT`.** `R_psi_final` is the **only** regional refiner used
for ROUTER_HOLDOUT evaluation, later continuity VAL evaluation, and future Phase 26+ development.
This prevents arbitrary selection among the three fold refiners.
"""))

cells.append(code("""
fr = ex.get("final_refiner", {})
print("name                   :", fr.get("name"))
print("refit rule             :", fr.get("refit_rule"))
print("data allowed           :", fr.get("data_allowed"))
print("holdout forbidden      :", fr.get("holdout_forbidden"))
print("holdout for ckpt sel   :", fr.get("holdout_for_checkpoint_selection"))
print("epoch rule             :", fr.get("epoch_rule"))
print("early stop on holdout  :", fr.get("early_stopping_on_holdout"))
print("arbitrary fold pick    :", fr.get("arbitrary_fold_refiner_selection_forbidden"))
"""))

cells.append(md("""
## A.6 Frozen global feature taps and primary router feature set

**Taps** (from the frozen Phase-21 Global MedFiLM, reusing the *same* forward — a second global
forward is forbidden):

`bridge` · `decoder2` · `decoder1` — each summarised by a **global average pool** and an
**ROI-aware average pool** mapped to that feature grid. No trainable convolutional projection
before pooling.

Every requested scalar name is mapped to its **exact authoritative** feature in the frozen
contract (`phase24_router_input_contract.csv`). No literal is silently invented.
"""))

cells.append(code("""
fs = pd.read_csv(TAB / "phase24_router_primary_feature_set.csv")
print(f"primary feature set: {len(fs)} rows")
print("mapping kinds:", fs["mapping_kind"].value_counts().to_dict())
print()
# FAIL-CLOSED: no mapped feature may use GT or be post-refinement
_bad = fs[(fs["uses_GT"].astype(str).str.lower() != "false")
          | (fs["available_pre_refinement"].astype(str).str.lower() != "true")
          | (fs["inference_available"].astype(str).str.lower() != "true")]
print("rows violating GT-free/pre-refinement:", len(_bad))
assert len(_bad) == 0, "FAIL-CLOSED: a primary feature is not GT-free/pre-refinement"
assert (fs["resource_cost_enters_delta_hat"].astype(str).str.lower() == "false").all()
display(sty(fs[["requested_literal", "group", "contract_feature", "mapping_kind"]],
            "p24-primary-features"))
"""))

cells.append(md("""
## A.7 Exact router architecture — `BARRBenefitRouterV1`

| Property | Value |
|---|---|
| Input | concatenated fixed feature vector (`§A.6`) |
| Task embedding | 4 tasks → dim **16** |
| Scalar normalisation | mean/std from **ROUTER_DEVELOPMENT only** |
| Hidden dims (declared → active) | `[128, 64]` → `[128, 64]` (no reduction needed) |
| Architecture | `Linear(in,128) → LayerNorm → SiLU → Dropout(0.10) → Linear(128,64) → LayerNorm → SiLU → Dropout(0.10) → Linear(64,1)` |
| Output | `Delta_hat_Dice` (single continuous scalar) |
| Harm head | **NOT** in the primary router (pre-registered extension only) |

Keeping the primary router single-head prevents the scientific hypothesis from being confounded
by multi-task training. Resource cost **must not** enter `Delta_hat`; it enters `U_hat` separately.
"""))

cells.append(code("""
rt = ex.get("router", {})
print("name                     :", rt.get("name"))
print("feature taps             :", rt.get("feature_taps"))
print("input dim (closed form)  :", rt.get("input_dim_closed_form"))
print("breakdown                :", rt.get("input_dim_breakdown"))
print("task embedding           :", rt.get("task_conditioning"))
print("normalisation            :", rt.get("normalization"))
print("norm from holdout?       :", rt.get("normalization_from_holdout_val_test"))
print("hidden declared -> active:", rt.get("hidden_dimensions_declared"), "->",
      rt.get("hidden_dimensions_active"))
print("closed-form params       :", f"{rt.get('expected_parameter_count_closed_form'):,}")
print("max parameters           :", f"{rt.get('max_parameters'):,}")
print("within ceiling           :", rt.get("envelope_within_ceiling"))
print("reduction applied        :", rt.get("envelope_reduction_applied"))
print("harm head                :", rt.get("harm_head"))
print("resource cost in Delta   :", rt.get("resource_cost_enters_delta_hat"))
"""))

cells.append(md("""
## A.8 Router training protocol, routing thresholds and lambda grid

| Setting | Value |
|---|---|
| Target | continuous OOF `DeltaDice` |
| Loss | **Huber, delta = 0.05** (robust to extreme harmed/improved cases) |
| Optimizer / LR / WD | AdamW / `1e-3` / `1e-4` |
| Batch / max epochs / patience | 128 / 200 / 20 |
| Scheduler | `ReduceLROnPlateau(factor=0.5, patience=8, min_lr=1e-6)` |
| Epoch selection | deterministic **5-fold** group-safe CV inside `ROUTER_DEVELOPMENT` OOF rows |

**Routing.** Primary score `score_i = Delta_hat_Dice_i`. Fixed-budget thresholds (10 / 25 / 50%)
come from **`ROUTER_DEVELOPMENT` score quantiles only**. 0% = global-only; 100% = all
action-available samples refine.

**Utility.** `U_hat = Delta_hat − λ·C`, with a **frozen prospective λ grid `{0.0, 0.25, 0.5, 1.0}`**
and `C` the normalized incremental *analytical* MAC cost. λ is never searched on holdout outcomes.
"""))

cells.append(code("""
print("router training protocol:")
for k in ("loss", "loss_reason", "optimizer", "lr", "weight_decay", "batch_size",
          "max_epochs", "early_stopping_patience", "scheduler", "seed", "epoch_selection"):
    print(f"   {k:26s} {rt.get(k)}")
print()
rg = ex.get("routing", {})
print("routing score            :", rg.get("score"))
print("budgets                  :", rg.get("budgets"))
print("threshold source         :", rg.get("threshold_source"))
print("lambda grid              :", rg.get("lambda_grid"))
print("cost definition          :", rg.get("cost_definition"))
print("cost scale derivation    :", rg.get("cost_scale_derivation"))
print("single universal lambda  :", rg.get("single_universal_lambda_forbidden"))
"""))

cells.append(md("""
## A.9 Cross-fit / refit diagram and addendum figure

The design below shows the full nested procedure: three outer OOF folds (each with its own
internal 90/10 early-stop split), the gain-label concat, and the single final refit on all
`ROUTER_DEVELOPMENT` data at the median selected epoch count.
"""))

cells.append(code("""
# deterministic inline ASCII diagram of the cross-fit / refit procedure (no figure asset needed)
print(\"\"\"
ROUTER_DEVELOPMENT (4957, group-safe, domain-stratified, seed 42)
├── OUTER FOLD 0 ──► fit R_psi on folds {1,2}   ├─ internal 90/10 fit/early-stop
│                     infer ONCE on fold 0  ────► OOF DeltaDice (fold 0)
├── OUTER FOLD 1 ──► fit R_psi on folds {0,2}   ├─ internal 90/10 fit/early-stop
│                     infer ONCE on fold 1  ────► OOF DeltaDice (fold 1)
└── OUTER FOLD 2 ──► fit R_psi on folds {0,1}   ├─ internal 90/10 fit/early-stop
                      infer ONCE on fold 2  ────► OOF DeltaDice (fold 2)
                     │
   concat executable-action OOF rows ──► B_phi fitted on OOF DeltaDice
                     │
   median best epoch of the 3 OOF runs = N_median
                     │
   R_psi_final : reinit seed 42, train on ALL ROUTER_DEVELOPMENT, exactly N_median epochs
                     │
   ROUTER_HOLDOUT (875) : integrated evaluation ONLY, never for fitting or epoch selection
\"\"\")
"""))

cells.append(md("""
## A.10 Post-safety, fusion and action availability

**`BARRPostSafetyV1`** is a `CONTROLLED_CORE_EXTENSION` used **only** in A8. The primary novelty
evaluation is A7 — the benefit + resource gate **without** post-safety. It saves **zero** compute
and must never be presented as the compute-saving mechanism (JFS differentiation remains
mandatory). Architecture `input → 32 → 16 → 1` small MLP, BCE loss, target *ACCEPT iff
`DeltaDice > 0`*, features from already-computed post-refinement quantities only, no GT at
inference, no second image encoder.

**Fusion** is exact and unlearned: outside the frozen ROI use `p_global`; inside use the resized
`p_refined`. No alpha blending, no learned fusion, segmentation threshold **`0.5`** inherited,
no threshold tuning.

**Action availability** `definition = predicted ROI exists`. When the global prediction is empty:
`action_available = false`, pre-gate is `FORCED_SKIP`, final is `global`. Such samples stay in the
integrated evaluation, receive **no** synthetic GT ROI and **no** fabricated gain target, and are
excluded from regression training rows, reported as `ACTION_UNAVAILABLE_GLOBAL_EMPTY`. This
separates *"predicted negative benefit"* from *"no legal refinement action exists."*
"""))

cells.append(code("""
ps = ex.get("post_safety", {})
fu = ex.get("fusion", {})
aa = ex.get("action_availability", {})
print("post-safety name         :", ps.get("name"))
print("extension status         :", ps.get("extension_status"))
print("primary evaluation       :", ps.get("primary_evaluation"))
print("saves compute            :", ps.get("saves_compute"))
print("architecture             :", ps.get("architecture"))
print("gt at inference          :", ps.get("gt_at_inference"))
print()
print("fusion rule              :", fu.get("rule"))
print("alpha blending           :", fu.get("alpha_blending"))
print("learned fusion           :", fu.get("learned_fusion"))
print("segmentation threshold   :", fu.get("segmentation_threshold"),
      f\"({fu.get('segmentation_threshold_source')})\")
print()
print("action_available         :", aa.get("definition"))
print("global-empty pre-gate    :", aa.get("global_empty_pre_gate"))
print("global-empty final       :", aa.get("global_empty_final"))
print("global-empty report label:", aa.get("global_empty_report_label"))
assert ps.get("saves_compute") is False
assert fu.get("segmentation_threshold") == 0.5
assert aa.get("global_empty_pre_gate") == "FORCED_SKIP"
"""))

cells.append(md("""
## A.11 Module envelope and specification-integrity checks

Closed-form architecture arithmetic only — **no module is instantiated** to count parameters.
"""))

cells.append(code("""
me = pd.read_csv(TAB / "phase24_spec_module_envelope.csv")
display(sty(me, "p24-spec-envelopes"))
print()
sch = pd.read_csv(TAB / "phase25_future_oof_gain_schema.csv")
print(f"OOF gain schema: {len(sch)} columns, SCHEMA ONLY (0 data rows)")
display(sty(sch[["column", "role", "uses_GT", "available_pre_refinement"]], "p24-oof-schema"))
print()
rp = rt.get("expected_parameter_count_closed_form")
rr = rf.get("expected_parameter_count_closed_form")
assert rr <= 2_000_000, "refiner exceeds hard ceiling"
assert rp <= 250_000, "router exceeds hard ceiling"
print(f"SPEC INTEGRITY: refiner {rr:,} <= 2,000,000  and router {rp:,} <= 250,000 : PASS")
print("DESIGN SPECIFICATION — NO TRAINING PERFORMED")
"""))


cells.append(md("""
## 35. Notebook determinism contract

This notebook is built with the same determinism contract as Phases 21–23:

- fixed cell ids (`p24NNN`),
- stripped `metadata.execution`,
- coalesced stream outputs,
- fixed pandas Styler uuids,
- normalised object memory addresses (`0x…` → `0xADDR`).

The determinism *proof* (three byte-identical builds) is established by
`scripts/analysis/run_phase24_determinism.py` **after** the notebook is written — it cannot be
read from inside the notebook without creating a circular dependency. What the notebook asserts
here is that the contract *machinery* is present and that this build executed cleanly.
"""))

cells.append(code("""
import nbformat as _nbf

_nb_path = pathlib.Path(
    r"D:/Softfors/jup/notebooks/phasewise/phase_24_architecture_spec/"
    r"phase24_narrowed_benefit_aware_refinement_spec.ipynb")
_nb = _nbf.read(str(_nb_path), as_version=4) if _nb_path.exists() else None
print("notebook path      :", _nb_path.name)
print("exists             :", _nb_path.exists())
print("determinism contract:")
for _c in ["fixed cell ids (p24NNN)",
           "stripped metadata.execution",
           "coalesced stream outputs",
           "fixed pandas Styler uuids (set_uuid)",
           "normalised 0x addresses"]:
    print("   -", _c)
print()
print("proof location     : scripts/analysis/run_phase24_determinism.py")
print("required builds    : 3 byte-identical")
"""))

# ---------------------------------------------------------------------------
# §36. TERMINAL ASSERTIONS
# ---------------------------------------------------------------------------
cells.append(md("""
## 36. Terminal state

The spec's terminal state is emitted only if every assertion below holds. Any single failure would
produce `PHASE24_NARROWED_SPEC_BLOCKED__REDESIGN_REQUIRED` instead.

Every assertion below reads an artifact that exists **before** the notebook executes — no
circular dependency. The determinism proof and the final freeze are established afterwards by
`run_phase24_determinism.py` and `run_phase24_final_check.py`.
"""))

cells.append(code("""
import re as _re

nb_here = pathlib.Path(
    r"D:/Softfors/jup/notebooks/phasewise/phase_24_architecture_spec/"
    r"phase24_narrowed_benefit_aware_refinement_spec.ipynb")
sha_here = hashlib.sha256(nb_here.read_bytes()).hexdigest() if nb_here.exists() else "n/a"

arch_f = _j(AUD / "phase24_architecture_spec.json")
ne_f = _j(AUD / "phase24_no_execution_audit.json")
fm_f = _j(FIG / "phase24_figure_manifest.json")

assertions = []

def chk(name, cond):
    assertions.append((name, bool(cond)))

chk("entry gate 27/27", gate.get("n_passed") == 27 and gate.get("n_failed") == 0)
chk("gate verdict pass", gate.get("verdict") == "PHASE24_ENTRY_GATE_PASS")
chk("arch status design-only", arch_f.get("status") == "DESIGN_ONLY_NOT_IMPLEMENTED")
chk("architecture id", arch_f.get("architecture_id") == "ra_medfilm_barr_narrowed_v1")
chk("method name frozen", arch_f.get("method_name") == "RA-MedFiLM-BARR")
chk("global params measured = 3523001", arch_f["global_reference"]["parameters"] == 3523001)
chk("refiner env unmeasured", arch_f["regional_refiner"]["target_parameter_envelope"]["measured"] is False)
chk("router env unmeasured", arch_f["benefit_router"]["target_parameter_envelope"]["measured"] is False)
chk("refiner hard ceiling 2.0M",
    arch_f["regional_refiner"]["target_parameter_envelope"]["hard_ceiling"] == 2_000_000)
chk("router pre_refinement", arch_f["benefit_router"]["pre_refinement"] is True)
chk("router gt_free", arch_f["benefit_router"]["gt_free"] is True)
chk("router max params <= 250k",
    arch_f["benefit_router"]["target_parameter_envelope"]["max_parameters"] <= 250_000)
chk("router MACs fraction <= 2%",
    arch_f["benefit_router"]["compute_envelope"]
    ["max_analytical_macs_fraction_of_one_global_forward"] <= 0.02)
chk("post-safety saves no compute", arch_f["post_safety"]["saves_compute"] is False)
chk("post-safety novelty false", arch_f["post_safety"]["novelty_claimed"] is False)
chk("post-safety controlled ext",
    arch_f["post_safety"]["classification"] == "CONTROLLED_CORE_EXTENSION")
chk("VAL reclassified secondary", "SECONDARY" in arch_f["VAL_role"]["role"])
chk("VAL not router training", arch_f["VAL_role"]["is_router_training_data"] is False)
chk("VAL not untouched holdout", arch_f["VAL_role"]["is_untouched_routing_holdout"] is False)
chk("TEST lock all zero",
    all(v == 0 for k, v in arch_f["TEST_lock"].items() if k != "status"))
chk("holdout outcomes read 0", arch_f["router_holdout_contract"]["outcomes_read_in_phase24"] == 0)
chk("router holdout ~875", arch_f["router_holdout_contract"]["approx_cases"] == 875)
chk("preservation margin 0.005",
    arch_f["preservation_margin"]["absolute_macro_domain_dice_margin"] == 0.005)
chk("statistics n_boot 2000", arch_f["statistics"]["n_boot"] == 2000)
chk("statistics seed 42", arch_f["statistics"]["seed"] == 42)
chk("statistics test not used", arch_f["statistics"]["test_used"] is False)
chk("crossfit 3 folds", arch_f["crossfit_contract"]["folds"] == 3)
chk("crossfit not executed", arch_f["crossfit_contract"]["executed_in_phase24"] is False)
chk("H1 load-bearing", arch_f["hypotheses"]["load_bearing"] == "H1")
chk("hypotheses not results", arch_f["hypotheses"]["status"] == "HYPOTHESES_NOT_RESULTS")
chk("single lambda forbidden",
    arch_f["pre_execution_gate"]["single_universal_lambda_forbidden"] is True)
chk("no training", arch_f.get("no_training") is True)
chk("no inference", arch_f.get("no_inference") is True)
chk("no implementation", arch_f.get("no_implementation") is True)
chk("phase25 not started", arch_f.get("phase25_started") is False)
chk("no-notebook-training", ne_f.get("training_runs") == 0)
chk("no-notebook-seg-inference", ne_f.get("segmentation_inference_calls") == 0)
chk("no-notebook-router-inference", ne_f.get("benefit_router_inference_calls") == 0)
chk("no-notebook-refinement", ne_f.get("refinement_forward_passes") == 0)
chk("no-notebook-models-instantiated", ne_f.get("models_instantiated") == 0)
chk("no-notebook-test", ne_f.get("test_image_reads") == 0 and ne_f.get("test_mask_reads") == 0)
chk("no-notebook-holdout-outcomes", ne_f.get("router_holdout_outcomes_read") == 0)
chk("no-execution verdict pass", ne_f.get("verdict") == "PHASE24_NO_EXECUTION_AUDIT_PASS")
chk("no-execution script scan clean",
    ne_f.get("static_scan", {}).get("total_training_constructs") == 0
    and ne_f.get("static_scan", {}).get("total_inference_constructs") == 0
    and ne_f.get("static_scan", {}).get("total_test_constructs") == 0)
chk("6 design figures", fm_f.get("n_figures") == 6)
chk("figures no results", fm_f.get("contains_experimental_results") is False)
chk("figures no hypothetical curves",
    fm_f.get("contains_hypothetical_performance_curves") is False)
chk("no phase25 artifact", not list(AUD.glob("phase25_*")))
chk("comparator C7 present",
    "C7" in pd.read_csv(TAB / "phase24_comparator_plan.csv")["comparator_id"].values)
chk("11 comparators", len(pd.read_csv(TAB / "phase24_comparator_plan.csv")) == 11)
chk("13 ablations", len(pd.read_csv(TAB / "phase24_ablation_plan.csv")) == 13)
chk("8 success/failure criteria (F1-F5, S1-S3)",
    len(pd.read_csv(TAB / "phase24_success_failure_criteria.csv")) == 8)
chk("7 modules 25A-25G",
    len(_j(AUD / "phase24_phase25_module_plan.json").get("modules", [])) == 7)
chk("module plan not started",
    _j(AUD / "phase24_phase25_module_plan.json").get("no_module_started") is True)
chk("forbidden tokens absent from name",
    _j(AUD / "phase24_method_naming_decision.json").get("forbidden_tokens_check", "").startswith("PASS"))

# ---- specification-completeness repair addendum ----
_ex = _j(AUD / "phase24_exact_implementation_spec.json")
_pe = _j(AUD / "phase24_benefit_data_protocol_exact.json")
_fs = pd.read_csv(TAB / "phase24_router_primary_feature_set.csv")
_sch = pd.read_csv(TAB / "phase25_future_oof_gain_schema.csv")
chk("ADDENDUM revision v1.1",
    _ex.get("architecture_id") == "ra_medfilm_barr_narrowed_v1_1")
chk("ADDENDUM science changed = false", _ex.get("science_changed") is False)
chk("ADDENDUM method name unchanged", _ex.get("method_name") == "RA-MedFiLM-BARR")
chk("ADDENDUM split seed frozen 42", _ex.get("split_seed") == 42)
chk("ADDENDUM split dev/hold counts",
    _pe.get("development_n") == 4957 and _pe.get("holdout_n") == 875)
chk("ADDENDUM split zero overlap",
    _pe.get("zero_overlap") and _pe.get("phase22_val_overlap_zero")
    and _pe.get("test_overlap_zero"))
chk("ADDENDUM split determinism", _pe.get("deterministic_recheck") is True)
chk("ADDENDUM holdout outcomes 0", _pe.get("holdout_outcomes_read") == 0)
chk("ADDENDUM ROI expansion 1.50", _ex["roi"]["expansion_factor"] == 1.50)
chk("ADDENDUM ROI resolution 256", _ex["roi"]["input_resolution"] == 256)
chk("ADDENDUM ROI forced skip", _ex["roi"]["empty_prediction_behavior"] == "FORCED_SKIP")
chk("ADDENDUM ROI no gt rescue", _ex["roi"]["gt_rescue"] is False)
chk("ADDENDUM refiner within ceiling", _ex["refiner"]["envelope_within_ceiling"] is True)
chk("ADDENDUM refiner closed-form params",
    _ex["refiner"]["expected_parameter_count_closed_form"] == 1_276_401)
chk("ADDENDUM refiner no FiLM", _ex["refiner"]["task_conditioning_film"] is False)
chk("ADDENDUM refiner no attention/SE/transformer",
    _ex["refiner"]["attention"] is False and _ex["refiner"]["se_blocks"] is False
    and _ex["refiner"]["transformer"] is False)
chk("ADDENDUM crossfit nested 90/10",
    _ex["crossfit"]["inner_fitting_fraction"] == 0.90
    and _ex["crossfit"]["inner_early_stop_fraction"] == 0.10)
chk("ADDENDUM oof never for ckpt selection",
    _ex["crossfit"]["oof_target_fold_never_used_for_checkpoint_selection"] is True)
chk("ADDENDUM final refiner no holdout",
    _ex["final_refiner"]["holdout_forbidden"] is True
    and _ex["final_refiner"]["early_stopping_on_holdout"] is False)
chk("ADDENDUM final refiner median epoch",
    "median" in _ex["final_refiner"]["epoch_rule"])
chk("ADDENDUM router taps frozen",
    _ex["router"]["feature_taps"] == ["bridge", "decoder2", "decoder1"])
chk("ADDENDUM router no second forward",
    _ex["router"]["second_global_forward"] is False)
chk("ADDENDUM router single head",
    "NOT part of the primary router" in _ex["router"]["harm_head"])
chk("ADDENDUM router within 250k", _ex["router"]["envelope_within_ceiling"] is True)
chk("ADDENDUM router Huber 0.05",
    "Huber" in _ex["router"]["loss"] and "0.05" in _ex["router"]["loss"])
chk("ADDENDUM router norm holdout forbidden",
    _ex["router"]["normalization_from_holdout_val_test"] == "FORBIDDEN")
chk("ADDENDUM lambda grid frozen",
    _ex["routing"]["lambda_grid"] == [0.0, 0.25, 0.5, 1.0])
chk("ADDENDUM thresholds from dev only",
    _ex["routing"]["threshold_source"] == "ROUTER_DEVELOPMENT quantiles only")
chk("ADDENDUM post-safety A8 only",
    _ex["post_safety"]["included_in"] == "A8"
    and _ex["post_safety"]["saves_compute"] is False)
chk("ADDENDUM fusion threshold 0.5",
    _ex["fusion"]["segmentation_threshold"] == 0.5
    and _ex["fusion"]["alpha_blending"] is False)
chk("ADDENDUM action availability frozen",
    _ex["action_availability"]["global_empty_pre_gate"] == "FORCED_SKIP")
chk("ADDENDUM augmentation inherited",
    _ex["augmentation"]["inherited_from"].startswith("src.data.transforms"))
chk("ADDENDUM feature set 17 rows", len(_fs) == 17)
chk("ADDENDUM feature set all GT-free",
    all(_fs["uses_GT"].astype(str).str.lower() == "false")
    and all(_fs["available_pre_refinement"].astype(str).str.lower() == "true"))
chk("ADDENDUM resource cost not in Delta",
    all(_fs["resource_cost_enters_delta_hat"].astype(str).str.lower() == "false"))
chk("ADDENDUM OOF schema 11 cols", len(_sch) == 11)
chk("ADDENDUM no architecture search", _ex.get("no_architecture_search_allowed") is True)
chk("ADDENDUM no training", _ex.get("training_runs") == 0
    and _ex.get("module_instantiations") == 0 and _ex.get("forward_passes") == 0)
chk("ADDENDUM v1.1 revision artifact",
    _j(AUD / "phase24_architecture_revision_v1_1.json")
    .get("architecture_id") == "ra_medfilm_barr_narrowed_v1_1")

n_fail = sum(1 for _, ok in assertions if not ok)
for name, ok in assertions:
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
print()
print(f"{len(assertions) - n_fail}/{len(assertions)} terminal assertions passed")
print()
print("Notebook SHA (pre-determinism-proof):", sha_here)
print()
print("PHASE24_NARROWED_BENEFIT_AWARE_REFINEMENT_SPEC_COMPLETE__PHASE25_ELIGIBLE_NOT_STARTED")
assert n_fail == 0, f"{n_fail} terminal assertion(s) failed"
"""))

# ---------------------------------------------------------------------------
# write + execute (deterministic)
# ---------------------------------------------------------------------------
nb = nbformat.v4.new_notebook(cells=cells)
for _i, _c in enumerate(nb.cells):
    _c["id"] = f"p24{_i:03d}"
nbformat.write(nb, str(NB_PATH))
print(f"Wrote {NB_PATH} ({len(nb.cells)} cells)")
print("Executing ...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=3600,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()

# deterministic post-processing
for _c in nb.cells:
    if isinstance(_c.get("metadata"), dict):
        _c["metadata"].pop("execution", None)
    _outs = _c.get("outputs")
    if _outs:
        _merged = []
        for _o in _outs:
            if (_o.get("output_type") == "stream" and _merged
                    and _merged[-1].get("output_type") == "stream"
                    and _merged[-1].get("name") == _o.get("name")):
                _p = _merged[-1]
                _pt, _ct = _p.get("text", ""), _o.get("text", "")
                if isinstance(_pt, list):
                    _pt = "".join(_pt)
                if isinstance(_ct, list):
                    _ct = "".join(_ct)
                _p["text"] = _pt + _ct
            else:
                _merged.append(_o)
        _c["outputs"] = _merged

_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
for _c in nb.cells:
    for _o in _c.get("outputs", []) or []:
        _d = _o.get("data")
        if isinstance(_d, dict):
            for _k, _v in list(_d.items()):
                if isinstance(_v, str):
                    _d[_k] = _ADDR.sub("0xADDR", _v)
                elif isinstance(_v, list):
                    _d[_k] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s
                              for _s in _v]
        _t = _o.get("text")
        if isinstance(_t, str):
            _o["text"] = _ADDR.sub("0xADDR", _t)
        elif isinstance(_t, list):
            _o["text"] = [_ADDR.sub("0xADDR", _s) if isinstance(_s, str) else _s
                          for _s in _t]
nbformat.write(nb, str(NB_PATH))

code_cells = [c for c in nb.cells if c.cell_type == "code"]
errors = sum(1 for c in code_cells for o in c.get("outputs", [])
             if o.get("output_type") == "error")
counts = [c.get("execution_count") for c in code_cells]
monotonic = all(counts[i] == i + 1 for i in range(len(counts)))
htmls = sum(1 for c in code_cells for o in c.get("outputs", [])
            if "text/html" in (o.get("data", {}) or {}))
imgs = sum(1 for c in code_cells for o in c.get("outputs", [])
           if "image/png" in (o.get("data", {}) or {}))
sha_nb = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"Cells: {len(nb.cells)} | markdown: "
      f"{sum(1 for c in nb.cells if c.cell_type == 'markdown')} | code: {len(code_cells)}")
print("Zero tracebacks:", "PASS" if errors == 0 else f"FAIL ({errors})")
print("Monotonic exec counts:", "PASS" if monotonic else "FAIL")
print("html table outputs:", htmls)
print("embedded PNG outputs:", imgs)
print("Notebook SHA:", sha_nb)
