# EXT-03 Supervisor Decision Memorandum — v1.1

**Classification:** `EXT03_SUPERVISOR_DECISION_MEMORANDUM`
**Version:** 1.1 (additive; authorises nothing)
**Generated local:** 2026-10-26T21:42 (+06:00)
**Mode:** strict read-only. No training, no inference, no TEST / ROUTER_HOLDOUT / external access, no frozen artifact modified.

**Addressed to:** Project supervisor / principal investigator.
**Prepared by:** Automated governance audit, on the completed record.

**Authority chain:** `ext03_scientific_acceptance_and_protocol_adjudication_v1_0.{md,json}` → `ext03_evidence_provenance_reconciliation_v1_1.json` → `ext03_scientific_adjudication_addendum_v1_1.{md,json}` → `ext03_false_certification_supersession_register_v1_1.json` → `ext03_missing_evidence_disposition_v1_1.json` → this memorandum.

---

## 0. What this document is and is not

**It is** a statement of the decision that now rests with the supervisor, three defensible courses of action, their costs and their limits, and one recommendation with reasons.

**It is not** an authorisation. Nothing here grants EXT-04, a FiLM-control run, a re-scoring pass, a protocol change, or a re-opening of AS-08. The terminal disposition of the work package is unchanged and is restated so it cannot drift:

> `EXT03_PROTOCOL_DEVIATION_DOCUMENTED__GOVERNANCE_REPAIR_COMPLETE__SCIENTIFIC_REAUTHORIZATION_PENDING`

The word *PENDING* is the whole point of this memorandum. No scientific authority was restored by the repairs. Only the record was made honest.

---

## 1. The decision

EXT-03 completed. It produced fifteen checkpoints, fifteen verified final metrics, and a five-family ordering. It also produced a documented, unauthorised divergence from the frozen phase09/10 training protocol in five parameters, a post-hoc sixth divergence, three defective certification artifacts, and six runs whose epoch histories no longer exist.

The supervisor must now decide **what the project claims**, given that the evidence base for its baseline comparison does not support the claim it was built to support.

The question is not *"was EXT-03 run well?"* — that is settled. The question is:

> **Does the project (a) withdraw the protocol-faithful baseline claim and proceed on other evidence, (b) fund a new prospective baseline study to earn the claim back, or (c) redirect the next unit of compute at the project's central claim, whose control experiment has never been run?**

These are genuinely exclusive as *next actions*, because only one training process may run at a time and each requires its own work order and prelaunch gate.

---

## 2. What is settled — not open for renegotiation

These findings are complete, independently re-validated, and not affected by whichever option is chosen.

| # | Finding | Status |
|---|---|---|
| 1 | Fifteen runs COMPLETE; 15/15 `best.pt` SHA-match the registry; 15/15 internal epoch and macro match; stopping identity `stop == min(100, best+15)` holds 15/15 exactly | **VERIFIED** |
| 2 | Five protocol divergences from the frozen authority (D1 AdamW→Adam, D2 lr 1e-4→1e-3, D3 `bce_dice`→BCE-only, D4 augmentation→none, D5 in_channels 1→3) | **DOCUMENTED, static source** |
| 3 | Sixth divergence D6 (SegFormer lr 1e-4) is a **post-outcome** intervention and a **cross-family confound** | **DOCUMENTED** |
| 4 | The Stage B gate's "training protocol unchanged = PASS" is **self-referential** — it compared the harness to a derived artifact, never to the authority | **PROVEN** |
| 5 | A prior fail-closed gate returned `all_pass=false` and an explicit STOP; training began five days later | **ON RECORD** |
| 6 | Three certification artifacts (S1, S2, S3) are mutually consistent and jointly wrong; the chain forms a closed loop with no edge to the frozen configs | **PROVEN** |
| 7 | D97 exposure is **measured**, not inferred: six runs lag by exactly one, nine are exact, split follows completion timestamps without exception | **MEASURED** |
| 8 | Six epoch histories are permanently `MISSING_FROM_AVAILABLE_ARTIFACTS`; recovery exhausted across logs, archives and run directories | **EXHAUSTED** |
| 9 | No FiLM-off / no-FiLM / task-conditioning-removed control exists anywhere in the repository | **ZERO HITS** |
| 10 | AS-08 primary evidence: **NOT ESTABLISHED**. FiLM attribution: **NOT ESTABLISHED**. TEST: never read. | **TERMINAL** |

**Consequence for the manuscript, whichever option is chosen:** no sentence attributing a performance difference to architecture may rest on EXT-03 as protocol-faithful evidence, and no sentence may attribute the 0.1694 gap to FiLM.

---

## 3. The three options

### Option A — Declare EXT-03 exploratory and proceed on other evidence

**Action.** Accept the v1.0/v1.1 disposition as final. Report EXT-03 only as a reduced-protocol exploratory ranking and a negative-results record. Withdraw AS-08 from the manuscript's claims and mark it `UNRESOLVED` / out of scope. Run no further training.

**What it delivers.** An honest, closed evidence base today. The five-family ordering remains usable if labelled correctly: *"under a common reduced protocol (Adam 1e-3, BCE-only, no augmentation, 3-channel input), DeepLabV3+ achieved the highest mean equal-domain macro Dice on the development-validation split (0.6657, n=3), UNet the lowest (0.5421, SD 0.1572)."* The `unet_seed123` collapse and the SegFormer from-scratch instability remain as a legitimate failure-mode record.

**What it costs.** The manuscript has no protocol-faithful baseline comparison. The architecture ranking cannot appear as primary evidence; at best an exploratory appendix. AS-08 is conceded, not repaired. The FiLM claim remains unsupported, so the paper's central contribution rests on a comparison with no control.

**Risk.** Low. No compute, no new gate, no host exposure.

**Does not repair.** AS-08; FiLM attribution; the six missing curves; the false fields in S1/S2.

**Authorisation needed.** None. This is the default state if no decision is made.

---

### Option B — Prospective protocol-faithful baseline study (EXT-04)

**Action.** Run the five architectures × three seeds under the **frozen** phase09/10 recipe — AdamW, lr 1e-4, wd 1e-4, `bce_dice` 0.5/0.5 ε 1e-6, full augmentation (mirror 0.5 / rot ±5° / brightness ±0.1 / contrast ±0.1), **1-channel input**, cosine T_max 100, batch 4, patience 15 — behind a **rebuilt prelaunch gate** that contains at least one direct edge to the frozen authority comparing concrete values (optimizer name, LR, loss name, augmentation operation count, channel count), and that binds the executing harness by digest per run.

**What it delivers.** The only path to AS-08 primary evidence. A defensible baseline table. A protocol-faithful comparison against GlobalMedFiLM that still — importantly — cannot isolate FiLM (§4), because the architecture and seed treatment still differ.

**What it costs.** Fifteen runs. EXT-03 consumed 10 d 13 h 33 m of wall clock for 1,142 epochs across fifteen runs including three host terminations. Protocol-faithful runs are slower per epoch: `bce_dice` adds a Dice term and augmentation adds per-sample transform cost, and 1-channel input does not offset either. A realistic planning envelope is **3–5 weeks** including gate construction, gate testing, and the negative-control battery, with **2–4 weeks** of that being compute. This is an estimate, not a commitment, and it must be re-derived from a measured single-epoch timing before any launch.

**Risk.** Moderate to high. The host produced three terminations during EXT-03 (2026-10-22 ep52, 2026-10-25 ep98, 2026-10-25 SegFormer ep5), attributed to a failing CMOS battery / RTC drift (5.19 days behind, Time-Service ID 52, offset 448,320 s) with no UPS. **Launching fifteen more runs before replacing the battery and installing a UPS would be a foreseeable repetition of a known, unfixed fault.**

**Does not repair.** FiLM attribution. AS-27 reproducibility is improved but not established (three seeds is still n=3). EXT-03's own defects remain on the record.

**Authorisation needed.** A new work order, a frozen protocol-faithful harness, a rebuilt gate, a battery + UPS remediation, and explicit supervisor sign-off. None of this exists.

---

### Option C — FiLM-off control: redirect the next unit of compute at the central claim

**Action.** Run the architecture-identical FiLM control that has never been run. Because the FiLM output projection is zero-initialised, freezing `film_layers` and `task_embedding` at initialisation yields a plain residual UNet that is **exactly identical to GlobalMedFiLM at step 0** and differs from it only by the absence of task conditioning during training. Same architecture, same parameter count, same protocol, same seed, same data.

**What it delivers.** The one experiment that can move `FiLM attribution: NOT_ESTABLISHED` to a measured effect. It converts the project's central claim from an assertion into a controlled result. At roughly **10–11 hours for one seed** under the Phase-21 protocol, it is one to two orders of magnitude cheaper than Option B and it addresses the larger of the two evidence gaps — a baseline table is supporting evidence; FiLM attribution is the contribution.

**What it costs.** ~11 hours of compute plus gate construction and a control-specific prelaunch artifact. One seed is a point estimate, not a variance estimate; a defensible claim would want a second and third seed (≈22–33 h total) or an explicit single-seed limitation statement.

**Risk.** Low to moderate. Same host risk applies, so the battery + UPS remediation should precede it — but the exposure window is 11 hours per seed, not three weeks.

**Does not repair.** AS-08. It is orthogonal: a FiLM-off control says nothing about whether the baselines were protocol-faithful. Choosing C leaves AS-08 `UNRESOLVED` exactly as Option A does.

**Authorisation needed.** A separate work order, a frozen control harness, a prelaunch gate, and explicit sign-off. **Not authorised here and not executed here.**

---

## 4. Comparison

| Dimension | **A** — Exploratory only | **B** — Protocol-faithful EXT-04 | **C** — FiLM-off control |
|---|---|---|---|
| Compute | none | ~2–4 weeks (15 runs) | ~11 h/seed (1–3 seeds) |
| Time to result | immediate | 3–5 weeks | 1–2 days |
| Repairs AS-08 | ✗ (concedes) | **✓ (only option)** | ✗ |
| Repairs FiLM attribution | ✗ | ✗ | **✓ (only option)** |
| Restores EXT-03 usability | ✗ | ✗ | ✗ |
| New gate required | none | yes, with authority edge | yes |
| Host risk exposure | none | **high** | low–moderate |
| Manuscript impact | loses baseline table | gains baseline table | gains central claim |
| Prerequisite | none | battery + UPS | battery + UPS (advisable) |
| Can run alongside another option | — | no (one trainer at a time) | no (one trainer at a time) |

**What no option repairs, ever:** the six missing epoch histories; the retroactive authorisation class of D6; the unverifiable intent behind the string `"Adam (phase09/10 authority)"`; whether any D97-exposed run's `best.pt` was overwritten by a worse model (error direction is strictly conservative — understated, never inflated — but the question is unanswerable). These are permanent features of the record and are now disclosed as such.

---

## 5. Recommendation

**Recommend Option C as the immediate next authorisation, with Option B deferred, and Option A as the default if no authorisation is granted.**

Reasoning, in order of weight:

1. **The larger gap is the central claim.** The manuscript's contribution is task-conditioned FiLM. `FiLM attribution: NOT_ESTABLISHED` means the central claim has no control arm in its own ablation family. A protocol-faithful baseline table strengthens a supporting comparison; it does not rescue the contribution. Value per unit compute therefore favours C by roughly two orders of magnitude.

2. **C is the cheaper experiment by an order of magnitude and the more decisive one.** Eleven hours versus three weeks. And a positive FiLM-off result is interpretable on its own, whereas Option B's product is a table that still cannot isolate FiLM (§4, and addendum §8: the 0.1694 gap bundles task conditioning, protocol, architecture and seed treatment).

3. **B's expected value is conditional on a decision the supervisor has not made.** If the manuscript reframes around conditioning rather than around a baseline leaderboard, AS-08 stops being load-bearing and Option B becomes optional. Spending three weeks of host time on a supporting table before settling the framing is the wrong order.

4. **C does not foreclose B.** They are sequential, not exclusive. Doing C first produces a measured FiLM effect, which sharpens what the baseline comparison is even for, and makes the case for or against B on evidence rather than on hope.

5. **A is honest and costs nothing, and is what happens by default.** It should be understood as a real option, not a failure mode. A project that discloses a divergent baseline study and reframes its claim around a controlled result is in better scientific standing than one that runs fifteen more experiments to protect a table.

**Sequencing if C is approved:** battery + UPS remediation → control harness frozen → prelaunch gate with an authority edge → negative-control battery → one seed → review → decide on seeds 2–3 and on B.

**Explicit statement.** This recommendation is advice. It authorises nothing. No training, no inference, no gate construction and no protocol change may begin on the strength of this memorandum. A supervisor decision recorded in §6 is required first, followed by a separate work order.

---

## 6. Decision record — for supervisor completion

```
DECISION:            [ ] A  Exploratory only, AS-08 withdrawn
                     [ ] B  Protocol-faithful EXT-04 (requires battery + UPS first)
                     [ ] C  FiLM-off control (recommended)
                     [ ] D  Other / sequenced — specify: ______________________

SCOPE AUTHORISED:    ______________________________________________________
SEEDS AUTHORISED:    ______________________________________________________
PREREQUISITES:       [ ] CMOS battery replaced   [ ] UPS installed
                     [ ] Gate rebuilt with authority edge
                     [ ] Work order issued

EXPLICITLY NOT AUTHORISED BY THIS DECISION:
  EXT-04 at large · FiLM-control beyond the scope above · re-scoring existing
  checkpoints · TEST access · ROUTER_HOLDOUT access · any change to a frozen
  artifact · any relaunch of a consumed revision · result-driven retry

SUPERVISOR:          ____________________  DATE: ____________
```

Until this block is completed and a work order is issued, the project's scientific state is:

`EXT03_PROTOCOL_DEVIATION_DOCUMENTED__GOVERNANCE_REPAIR_COMPLETE__SCIENTIFIC_REAUTHORIZATION_PENDING`

---

## 7. Items that should proceed regardless of the decision

These are record-integrity repairs, not scientific ones. None requires a training authorisation. None is authorised by this memorandum; each needs its own instruction.

| ID | Item | Why it matters |
|---|---|---|
| O4 | Correct the false field `recipe.optimizer = "Adam (phase09/10 authority)"` — additively, leaving the original bytes intact | A false statement currently sits in the record with the appearance of authority |
| O5 | Correct `ext03r_param_verification.json`'s 1-channel counts and vacuous `all_match: true` — additively | It certifies a configuration that never ran |
| O6 | Record the retroactive Stage B harness SHA (`bcdbada2…`) and the version chain | The executing harness is bound by no prelaunch artifact |
| O8 | Replace CMOS battery, install UPS | Three terminations in ten days, known cause, unfixed — this is the highest-probability cause of the next failure |

**O8 should precede any training authorisation.** Recommending compute on a host with a known, diagnosed, unfixed fault would be indefensible.

---

## 8. Closing statement

EXT-03 is not a scandal and it is not a success. It is fifteen real runs, honestly measured, conducted under a protocol nobody authorised, certified by a gate that could not see the divergence, and now fully disclosed. Every checkpoint is intact. Every reported number is the number its checkpoint carries. The divergence was detectable on 2026-10-11 and was not detected; that failure is now on the record in three independent places.

What the record cannot do is decide what the project claims. That is a scientific judgement, it belongs to the supervisor, and it has not been made.

---

*End of memorandum. No training, no inference, no source modification, no TEST or ROUTER_HOLDOUT access, no frozen artifact modified, no authorisation granted.*
