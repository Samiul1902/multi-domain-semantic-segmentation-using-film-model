# EXT-03 Supervisor Memorandum Addendum — Scientific Framing Correction v1.2

**Classification:** `EXT03_SUPERVISOR_MEMORANDUM_ADDENDUM`
**Version:** 1.2 (additive to v1.1; the v1.1 memorandum is retained byte-for-byte)
**Generated local:** 2026-10-26T22:29 (+06:00) — provenance `AUTHOR_ENTERED_AT_WRITE`; the computed, timezone-aware value is in the companion `.json` `generated_local`
**Mode:** read-only. No training, no inference, no frozen configuration changed, no TEST / ROUTER_HOLDOUT / external access.

**Additive to:** `ext03_supervisor_decision_memorandum_v1_1.md`
**Supersedes:** the *framing* of Option C in that memorandum. It supersedes no bytes and no measurement.

---

## 0. Purpose, and what this addendum does not do

The v1.1 memorandum presented three options without separating three **scientifically distinct claims** that the options are often assumed to settle together. That conflation is the defect this addendum corrects.

**This addendum does not authorise the FiLM-off control.** It adds a requirement that any future authorisation must satisfy. The decision block in v1.1 §6 remains blank. Nothing here may be read as approval.

The three claims are:

| # | Claim | Model under test | The control that could settle it |
|---|---|---|---|
| **C1** | Task-conditioned **FiLM** improves multi-domain segmentation over an identical, unconditioned backbone | GlobalMedFiLM | FiLM-off control, same protocol / seed / data |
| **C2** | The **BARR benefit router** and **post-safety** modules improve on the GlobalMedFiLM backbone | RA-MedFiLM-BARR | Router-off and safety-off arms against the same backbone |
| **C3** | The proposed model outperforms **standard baselines under a common frozen protocol** | RA-MedFiLM-BARR vs 5 baselines | Protocol-faithful baseline matrix (`EXT-03B`, provisional) |

**These are three experiments, not one.** No single run settles more than one of them.

---

## 1. The conflation, stated plainly

The most likely misreading of the v1.1 memorandum is:

> *"Run the FiLM-off control, and if the conditioned model wins, the architecture is validated."*

That inference is invalid, for a reason that is verifiable in the checkpoint itself rather than a matter of interpretation:

> **The GlobalMedFiLM checkpoint contains no router and no safety tensors.**
> Measured from `checkpoints/phase21_global_medfilm_fourdomain_seed42_clean_v3/best.pt`
> (86 tensors): the parameter groups are `encoder1..4`, `bridge`, `decoder1..4`, `head`,
> `film_layers`, `task_embedding`. A search across all 86 tensor names for
> `router`, `safety`, or `benefit` returns **zero hits**.

A FiLM-off control therefore manipulates a variable that exists only inside GlobalMedFiLM. It cannot, even in principle, produce evidence about modules that are not present in the model being controlled. **A FiLM-off result is silent on BARR by construction, not by caution.**

---

## 2. What a FiLM-off control can establish — and only this

**Can establish.** For one fixed protocol, one fixed seed, one fixed dataset, and one fixed evaluation rule: whether removing task conditioning from GlobalMedFiLM changes the selected VAL808 equal-domain macro Dice, and by how much. That is one number describing one comparison.

**Cannot establish**, and must never be cited as having established:

| Not established | Why not |
|---|---|
| BARR superiority | Router and safety modules are absent from the controlled model |
| Safety, robustness, or failure-mode behaviour | No safety metric exists in the evaluation; Dice is a segmentation-overlap measure and carries no safety semantics |
| Router benefit | `B_phi` is not in the checkpoint; the FiLM control never touches it |
| Protocol-faithful baseline comparability | That is C3, an entirely different experiment |
| Generalisation | VAL808 is the checkpoint-selection set; any number computed on it is selection-contaminated |
| That FiLM is the *only* difference | Architecture, protocol and seed treatment differ from every baseline (see v1.1 addendum §8) |

**The safety point deserves emphasis.** `S_omega` is a post-hoc safety module. Whether it improves *safety* is a question that requires a safety-relevant metric — a violation rate, an abstention behaviour, a catastrophic-error count. Dice cannot answer it, and a FiLM ablation does not touch it. **No safety claim of any kind is supported by any experiment currently in this repository.**

---

## 3. Total versus trainable parameter counts — the definitional distinction

This distinction is routinely collapsed in writing about frozen controls, and collapsing it produces false claims. It is defined here explicitly.

For any model, define:

- **Total parameters** — `sum(p.numel() for p in model.parameters())`. Every parameter tensor that exists in the module tree, whether or not it receives gradients.
- **Trainable parameters** — `sum(p.numel() for p in model.parameters() if p.requires_grad)`. The subset the optimiser updates.

**Freezing does not reduce total parameters.** Setting `requires_grad = False` on a module changes what the optimiser updates; it does not remove the tensor from the model, the graph, or the state dict. A frozen module is still *there*.

Two control designs are therefore available, and they are **not the same experiment**:

### Design F1 — freeze-at-init (architecture-identical)

`film_layers` and `task_embedding` are **present** and frozen at their zero-initialised values.

- Total parameters: **3,523,001** — *identical to GlobalMedFiLM*
- Trainable parameters: **3,432,233**
- Because the FiLM output projection is zero-initialised, γ ≡ 0 and β ≡ 0 for every task, so
  `F_hat = (1+γ)·F + β = F` **exactly**. The model is a plain residual UNet that receives `task_id`
  but cannot act on it.
- Equal-capacity comparison against GlobalMedFiLM: **yes**.

### Design F2 — remove the modules

`film_layers` and `task_embedding` are **deleted** from the model.

- Total parameters: **3,432,233**
- Trainable parameters: **3,432,233**
- The identity property still holds trivially (there is no FiLM to apply), but the model class and
  parameter count differ from GlobalMedFiLM.
- Equal-capacity comparison against GlobalMedFiLM: **no**.

### Measured parameter budget of GlobalMedFiLM

From the frozen checkpoint (`best.pt`, 86 tensors):

| Group | Parameters | Share of total |
|---|---:|---:|
| `decoder4` | 1,192,704 | 33.85% |
| `bridge` | 1,082,368 | 30.72% |
| `encoder4` | 516,864 | 14.67% |
| `decoder3` | 359,808 | 10.21% |
| `encoder3` | 129,408 | 3.67% |
| **`film_layers`** | **90,640** | **2.57%** |
| `decoder2` | 90,048 | 2.56% |
| `encoder2` | 32,448 | 0.92% |
| `decoder1` | 22,560 | 0.64% |
| `encoder1` | 6,000 | 0.17% |
| **`task_embedding`** | **128** | **0.004%** |
| `head` | 25 | 0.0007% |
| **TOTAL** | **3,523,001** | 100% |

FiLM site breakdown (`film_layers`, 90,640 total):

| Site | Parameters |
|---|---:|
| bridge | 35,392 |
| decoder4 | 27,072 |
| decoder3 | 14,592 |
| decoder2 | 8,352 |
| decoder1 | 5,232 |
| **Total** | **90,640** |

Conditioning budget: `film_layers` 90,640 + `task_embedding` 128 = **90,768**, or **2.5764%** of total.

### The arithmetic that must appear in any write-up

| Quantity | F1 (freeze-at-init) | F2 (remove) |
|---|---:|---:|
| Total parameters | 3,523,001 | 3,432,233 |
| Trainable parameters | 3,432,233 | 3,432,233 |
| Frozen parameters | 90,768 | 0 |
| Δ total vs GlobalMedFiLM | **0** | −90,768 |
| Δ trainable vs GlobalMedFiLM | −90,768 | −90,768 |
| Architecture-identical to GlobalMedFiLM | **yes** | no |

**Three claims that must not be made:**

1. ~~"The frozen control has 2.58% fewer parameters."~~ — False for F1. Total is unchanged. Only *trainable* falls by 2.58%.
2. ~~"The frozen control is a smaller model."~~ — False for F1. It is the same model with a smaller optimised subset.
3. ~~"F1 and F2 are equivalent controls."~~ — False. They differ in total capacity and in model class, and only F1 supports an equal-capacity claim.

**Recommended design: F1.** It is the only design in which the control and the treatment have identical total capacity, identical parameter layout, and identical forward graph — so the only difference is whether task conditioning is active. That is what a one-factor control is supposed to be.

---

## 4. When the identity property holds — and when it does not

The exact-identity claim (`F_hat = F`) is often stated too broadly. Precisely:

- **Holds** for a *freshly initialised* model whose FiLM output projection is zero-initialised and whose
  FiLM parameters are then frozen. γ = 0, β = 0, identity exact, for every task and every input.
- **Does not hold** for the trained GlobalMedFiLM checkpoint. After training γ and β are non-zero — that
  is the entire point of training them. Measured on the frozen checkpoint: `decoder1` γ is positive at
  every domain (+0.235 / +0.434 / +0.455 / +0.311), `bridge` γ separates the domains into two clusters,
  and β has mean absolute magnitude 0.036–0.187 across sites.

So the control is **not** "GlobalMedFiLM with FiLM zeroed". It is "the same architecture, trained from
scratch with conditioning held at identity." The distinction matters: the control does not reuse the
trained weights, and any comparison is a from-scratch retrain, not an ablation of the trained model.

---

## 5. Naming

Per `ext03_study_identifier_namespace_reconciliation_v1_2.md`, the protocol-faithful baseline study is
provisionally **`EXT-03B`**, not EXT-04 (EXT-04 is a frozen progression/scaling slot).

The FiLM-off control is **not an EXT study**. It belongs to the Phase-28 one-factor ablation family
(`phase28_one_factor_control_contract.json`). If a supervisor requires an EXT label, the only defensible
provisional choice is `EXT-03C`.

---

## 6. Requirements any future authorisation must satisfy

Should the supervisor ever authorise the FiLM-off control, the authorisation must fix, in writing and
before launch:

1. **Design** — F1 or F2, stated explicitly. F1 is recommended.
2. **Both parameter counts** — total and trainable, reported for the control and for GlobalMedFiLM.
3. **Seed count** — one seed is a point estimate; a claim of a FiLM effect needs ≥3 seeds or an explicit
   single-seed limitation.
4. **Protocol** — frozen before launch, and identical between control and treatment.
5. **The claim boundary** — a pre-registered statement that the result speaks to C1 only, and to C2, C3
   and safety not at all.
6. **The selection caveat** — VAL808 is the selection set; the result is a selection-contaminated
   decomposition, not held-out performance.
7. **Host remediation** — the clock is currently unsynchronised (`Source: Local CMOS Clock`, no
   successful sync) and the RTC was previously 5.19 days behind. Any timed run inherits that uncertainty.

**Requirement 5 is the one that most needs to be written down before the run, not after it.** A result
obtained first and interpreted second is how the FiLM attribution gap arose in the first place.

---

## 7. Status

| Item | Status |
|---|---|
| C1 FiLM attribution | **NOT_ESTABLISHED** — control never run |
| C2 BARR router / safety contribution | **NOT_ESTABLISHED** — no ablation arm; +0.0028 integrated vs backbone is a single-seed difference within noise, and no safety metric exists |
| C3 Protocol-faithful benchmarking | **NOT_ESTABLISHED** — EXT-03 divergent in five parameters; AS-08 remains UNRESOLVED |
| FiLM-off control | **NOT AUTHORISED**, not executed |
| Safety claim | **NO SUPPORTING EXPERIMENT EXISTS** |
| AS-08 | **UNRESOLVED** — not marked complete, not relabelled |

---

*End of addendum. No training, no inference, no frozen configuration modified, no TEST or ROUTER_HOLDOUT access, no control authorised.*
