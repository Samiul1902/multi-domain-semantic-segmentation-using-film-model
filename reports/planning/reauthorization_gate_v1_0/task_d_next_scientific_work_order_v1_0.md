# Task D — Recommended Next Scientific Work Order

**Classification:** `RA_MEDFILM_BARR_NEXT_SCIENTIFIC_WORK_ORDER`
**Version:** 1.0
**Prepared local:** 2026-10-26T22:52 (+06:00)
**Mode:** recommendation and readiness. **Not authorised. Not launched.**

---

## 1. Recommendation

**Adopt the benefit-router mechanism ablation (C2a) as the next scientific work order.**

Provisional identifier: **`BARR-M1`** — *Benefit-router mechanism ablation, phase 1*.

It is deliberately **not** an `EXT-` identifier. It is a BARR mechanism study, not a baseline benchmark; EXT-04 stays reserved and EXT-03B stays untouched.

---

## 2. Why this path, and not the other two

The governing question is: *which available path best supports the eventual BARR paper without relying on unsupported novelty or superiority claims?*

**C2a wins on four independent grounds.**

**(a) It is the only path that needs no training — and therefore no host remediation.**
Every component is frozen and **all four are present on disk with matching digests** (verified this session):

| Component | Digest (prefix) | Path |
|---|---|---|
| GlobalMedFiLM | `286689fd…` | `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt` |
| Phase-25A refiner | `6d28608a…` | `checkpoints/phase25a_barr_regional_refiner_v1_1_roi030/final/final.pt` |
| Phase-25D `B_phi` | `8a412b2f…` | `checkpoints/phase25d_barr_benefit_router_v1_2_1_seed42/final/final.pt` |
| Phase-25F `S_omega` | `eee9b97b…` | `checkpoints/phase25f_barr_post_safety_v1_0_seed42/final/final.pt` |

Because nothing is trained, the study is **immune to the host's two blocking faults**: 87 unexpected shutdowns in event-log retention and a dead RTC (Task A). C1 and C3 both require 1–18 days of continuous unattended compute on a host with no UPS. **C2a can run today.**

**(b) It is cheaper by two orders of magnitude.**

| Study | Compute | Host exposure |
|---|---|---|
| **C2a** | **~2–6 GPU-hours** (inference only, 3 arms × ~4,957 cases) | hours, restartable |
| C1 | ~57.6 h (2 arms × 3 seeds, measured 9.61 h/seed) | days, at risk |
| C3 | ~250 h ≈ 12–18 days wall | weeks, at risk |

**(c) It converts an unexplained joint delta into a mechanism claim.**
Today the paper's BARR evidence is a single undecomposed number: +0.00282 over the frozen backbone, three seeds, sign-consistent. Nobody can say which component produced it. C2a decomposes it into *router present* vs *router absent*, which is the difference between "our stack is slightly better" and "here is the mechanism and here is what it prevents."

**(d) It supports a claim the project can actually defend: harm avoidance, not superiority.**
This is the strongest scientific position available, and it is already latent in existing evidence:

- **Phase-22 harm analysis** (oracle ROI, n = 808): a case is *harmed* when the regional arm reduces Dice. **536 of 808 harmed (66.3%)**, mean harm −0.0957, worst −0.833, **net gain −34.32**. Refining everywhere, even with a perfect ROI, is **net harmful**.
- **Phase-29** (VAL808, 3 seeds): the **routed** integrated system is **+0.00282**, sign-consistent, while routing only **32.8%** of cases (mean 265 of 808).

Read together, these suggest the router's value is **avoiding the harm that refine-all causes**, not creating gain. That is a defensible, non-superiority, mechanism-level claim — exactly what the objective asks for — and it reframes a weak result into a meaningful one.

**Why not C1 now.** C1 answers the central FiLM question and is the natural *second* study, but it needs ~57.6 h of training on an unremediated host and answers nothing about BARR. Running it first risks losing the run to a power event and still leaving the BARR story empty.

**Why not C3 now.** C3 repairs AS-08, which matters for the baseline table, but it is the most expensive path (~250 h), needs a rebuilt gate plus physical remediation, and cannot isolate FiLM or BARR. It should follow, not lead.

---

## 3. The work order

### WO-BARR-M1 — Benefit-router mechanism ablation, phase 1

**Objective.** On one frozen development population with one frozen fusion rule, determine whether benefit routing changes macro Dice relative to global-only and refine-all, and quantify the harm avoided by routing rather than by refinement.

**Arms (exactly three, from the frozen Phase-28 contract).**

| Arm | Contract definition | Role |
|---|---|---|
| **A0** | `ROUTING_ABSENT (global only)` | lower bound — no refinement at all |
| **A1** | `ROUTING_ABSENT (refine all)` | the counterfactual that Phase-22 shows is net harmful |
| **A8** | `POST_SAFETY = S_omega present` (baseline) | the routed system |

**Authorisation note — an important distinction.** Executing A0/A1/A8 is **not** adding a factor to a frozen study. The contract forbids `post_hoc_factor_addition`; it does not forbid executing arms it already defines. Authorisation is nonetheless required because the contract declares `execution: "NONE"` and `governance_only: true`. **No arm outside A0/A1/A8 may be run**, and no new factor may be introduced.

**Explicitly excluded.**
- **C2b (safety) is out of scope.** The frozen 13-arm design contains **no `S_omega`-absent arm** — A8 is *"S_omega present (baseline)"* and every other arm varies routing or router features. The safety contribution is therefore **unmeasurable within Phase-28**, and adding an arm is forbidden by the contract. C2b needs its own prospective study with a safety metric that does not currently exist anywhere in this repository.
- No training. No FiLM control. No baseline matrix. No TEST. No ROUTER_HOLDOUT. No external inference.

**Population — a conflict that must be resolved before the gate is built.**
The Phase-28 contract fixes `population = ROUTER_DEVELOPMENT (n=4957)`. The Phase-22 harm analysis and the Phase-29 summary both use **VAL808 (n=808)**. These are different populations and must not be silently mixed.
- **Primary:** `ROUTER_DEVELOPMENT` (n = 4,957), per the contract's `held_constant`.
- **Secondary, clearly labelled:** VAL808, reported only as a descriptive continuity decomposition against the Phase-22/29 numbers.
Both must be frozen by manifest digest **before launch**, and the primary/secondary roles declared in the authorization.

**Held constant (per contract).** Preprocessing/ROI rule (threshold 0.30, expansion 1.50, resolution 256); fusion rule (outside ROI `p_global`; inside ROI `p_refined`; threshold 0.50); budget 0.25; λ 0.25; bootstrap n_boot 2000, seed 42; segmentation threshold 0.50; all four component digests above.

**Primary endpoint.** Macro-domain equal-weight mean Dice delta, paired per case, with bootstrap CI (n_boot 2000, seed 42), for A8 − A0, A8 − A1, and A1 − A0.

**Secondary endpoints.** Harm rate and mean harm per arm (reusing the Phase-22 *definition* verbatim: a case is harmed when the regional arm reduces Dice); `n_selected` and `selected_fraction`; per-domain breakdown.

**Expected compute.** ~3 arms × ~4,957 cases of forward passes through frozen models, plus bootstrap. **Estimated 2–6 GPU-hours** on the RTX 3060 Ti (8 GB). Restartable per arm; no long unattended window.

**Deliverables.** Per-arm per-case prediction persistence (so harm is independently recomputable); a paired comparison table; a harm-avoidance decomposition; an explicit claim-boundary statement.

**Claim boundary (pre-declared).** All results are `DESCRIPTIVE_DEV` on a development population that is also used for selection. **Permitted:** "under the frozen fusion rule on the development population, routing changed macro Dice by X and reduced the harmed-case rate from Y to Z." **Prohibited:** held-out performance, confirmatory inference, clinical safety, generalisation, or any statement that BARR is superior.

---

## 4. Prerequisites

| # | Prerequisite | Status |
|---|---|---|
| 1 | Four frozen components present with matching digests | **MET** — verified this session |
| 2 | Frozen Phase-28 contract available and intact | **MET** — `phase28_one_factor_control_contract.json` |
| 3 | Population resolved and frozen (ROUTER_DEVELOPMENT vs VAL808 roles declared) | **NOT MET** — requires supervisor decision |
| 4 | Authorization to execute a contract declared `execution: "NONE"` | **NOT MET** |
| 5 | R1–R10 prelaunch contract satisfied for an inference-only study | **NOT MET** — gate not built |
| 6 | Negative-control battery demonstrating the gate can fail | **NOT MET** |
| 7 | Claim-boundary block frozen pre-launch | **NOT MET** |
| 8 | Host remediation P1–P3 | **NOT REQUIRED for this study** (hours, restartable) — but still required before C1 or C3 |

Prerequisites 1–2 being met is what makes this the right next step: the expensive, irreversible work is already done and frozen.

---

## 5. Supervisor authorization required

The following, and nothing broader, is what the supervisor must approve:

```
AUTHORIZATION REQUEST — BARR-M1

Study identifier      : BARR-M1 (provisional; not an EXT- study)
Scope                 : execute frozen Phase-28 arms A0, A1, A8 ONLY
Execution mode        : INFERENCE ONLY — no training, no weight updates
Population (primary)  : ROUTER_DEVELOPMENT n=4957   [ ] approve  [ ] substitute: ________
Population (secondary): VAL808 n=808, descriptive continuity only   [ ] approve  [ ] drop
Fusion rule           : frozen (thr 0.30 / exp 1.50 / res 256; outside p_global, inside
                        p_refined; threshold 0.50)
Bootstrap             : n_boot 2000, seed 42
Components            : GlobalMedFiLM 286689fd / refiner 6d28608a / B_phi 8a412b2f /
                        S_omega eee9b97b — all SHA-verified present
Expected compute      : 2-6 GPU-hours, restartable
Claim class           : DESCRIPTIVE_DEV only

EXPLICITLY NOT AUTHORISED BY THIS REQUEST
  C2b / any S_omega-absent arm  ·  any Phase-28 arm outside A0/A1/A8  ·  any new
  factor added to Phase-28  ·  C1 FiLM-off control  ·  C3 / EXT-03B baseline matrix
  ·  EXT-04  ·  TEST access  ·  ROUTER_HOLDOUT access  ·  external inference  ·
  training of any kind  ·  any upgrade of C1/C2/C3 or resolution of AS-08

AUTHORIZED BY: ______________________   DATE: ____________
AUTHORIZATION ID: ____________________
```

**Nothing in this document constitutes that authorization.** Until the block above is completed and a work order is issued, the state remains:

`RA_MEDFILM_BARR_NEXT_SCIENTIFIC_WORK_ORDER_READY__AWAITING_SUPERVISOR_APPROVAL`

---

## 6. What this recommendation does not claim

- It does not upgrade **C1**, **C2** or **C3** — all remain `NOT_ESTABLISHED`.
- It does not resolve **AS-08** — that requires C3.
- It does not establish FiLM attribution — that requires C1.
- It does not establish safety — **C2b has no metric and no arm**, and this work order deliberately excludes it.
- It does not assert that BARR is superior to anything. It tests whether routing changes an outcome on a development population, and whether the change is consistent with harm avoidance.
- It does not reuse **EXT-04** and does not authorise **EXT-03B**.

---

*End of Task D. Recommendation only: no authorization granted, no gate built, no training launched.*
