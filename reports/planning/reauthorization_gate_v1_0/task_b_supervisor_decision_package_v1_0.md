# Task B — Supervisor Decision Package

**Classification:** `RA_MEDFILM_BARR_SUPERVISOR_DECISION_PACKAGE`
**Version:** 1.0
**Prepared local:** 2026-10-26T22:46 (+06:00)
**Mode:** decision support only. Nothing here authorises an experiment.

**Standing status entering this gate**

| Item | Status |
|---|---|
| EXT-03 v1.0 / v1.1 / v1.2 evidence | **PRESERVED** (v1.1 manifest `206ca0a8…`, v1.2 manifest `36fe4337…`) |
| Phase 01–40 scientific record | **PRESERVED**, unmodified |
| AS-08 | **UNRESOLVED** |
| C1 / C2 / C3 | **NOT_ESTABLISHED** |
| EXT-04 | **RESERVED** for its frozen progression/scaling studies (AS-01, AS-02, AS-03, AS-04, AS-05, AS-07) |
| EXT-03B | **PROVISIONAL, NOT AUTHORISED** |
| FiLM-off study | **PROSPECTIVE SUPPLEMENTARY ABLATION — never a Phase-28 arm** |

---

## 0. A correction to my own v1.2 statement

The v1.2 memorandum addendum described the BARR integrated-vs-backbone delta as *"single-seed … within noise."* That was wrong, and the record should be corrected before a decision rests on it.

`reports/audits/phase29_phase_d_three_seed_descriptive_summary.json` (population VAL808, `descriptive: true`) reports **three seeds** (42 / 123 / 3407):

| Metric | seed 42 | seed 123 | seed 3407 | mean | sample SD (n−1) | sign-consistent |
|---|---:|---:|---:|---:|---:|---|
| `macro_final_dice` (R+B+S integrated) | 0.837289 | 0.838467 | 0.837948 | **0.837901** | 0.000590 | **true** |
| `macro_global_dice` (frozen backbone) | 0.835079 | 0.835079 | 0.835079 | **0.835079** | ~0 | — |
| `macro_delta_dice` | +0.002210 | +0.003388 | +0.002869 | **+0.002822** | 0.000590 | **true** |

So the delta is **three-seed and positive at every seed**, not a single-seed artefact. Two qualifications survive unchanged and one new one appears:

1. **It is the joint effect of R + B + S**, not attributable to any one component. There is no component-wise ablation.
2. **VAL808 is the development/selection split** — this is a descriptive decomposition, not held-out performance.
3. **The backbone is one frozen checkpoint**, so all observed variance sits on the integrated side. The comparison has no treatment-side replication of the backbone.

**Corrected claim:** *"the integrated R+B+S stack improved VAL808 equal-domain macro Dice by +0.00282 (0.34% relative) over the frozen backbone, positive at all three seeds, SD 0.00059, descriptive."* That is a real but small effect, and it is not yet decomposed.

---

## 1. The three candidate studies

### C1 — Architecture-matched FiLM-off training control

**Exact research question.** Holding architecture, protocol, data population, seed and schedule fixed, does removing task conditioning from GlobalMedFiLM change the selected VAL808 equal-domain macro Dice — and by how much?

**Eligible data.** Internal TRAIN (5,832) / VAL808 (808), manifest `phase4_v3`. Development split only. **No TEST. No external inference.** Same population as Phase-21.

**Existing frozen authority.**
- `experiments/phase21_global_medfilm_fourdomain_seed42_clean_v3/config.json` — the complete frozen treatment protocol: `AdamW lr 1e-4 wd 1e-4`, `bce_dice 0.5/0.5 ε 1e-6`, `CosineAnnealingLR T_max 100`, batch 4, 512², 3-channel, patience 15, AMP, seed 42, `phase20_domain_balanced_uniform_v1` sampling, `phase20_macro_domain_mean_dice_v1` selection, full augmentation.
- GlobalMedFiLM checkpoint `286689fd…` (total 3,523,001 params) as the treatment reference.
- **No frozen contract contains a FiLM-off arm.** Phase-28's `R2` is *router* task-conditioning removal, not GlobalMedFiLM FiLM. This study is therefore **prospective and supplementary** and must carry its own identifier.

**Necessary controls.**
- **Design F1 (freeze-at-init):** `film_layers` + `task_embedding` present, `requires_grad=False`, zero-init out-projection ⇒ γ ≡ 0, β ≡ 0 ⇒ `F_hat = F` exactly. Total **3,523,001 (unchanged)**, trainable **3,432,233**, frozen 90,768. This is the only design giving an equal-capacity, architecture-identical comparison.
- **Treatment re-execution** under the identical frozen protocol, so both arms are trained in the same session on the same host — otherwise a host-level difference is confounded with the treatment.
- **Positive control:** the re-executed treatment must land near the recorded Phase-21 value (0.835079 at epoch 66) within a pre-declared tolerance; failure aborts rather than being reported.
- **Negative control:** a deliberately mis-conditioned arm (FiLM active, `task_id` permuted) must *differ* from the control; if it does not, the task signal is inert and the whole comparison is void.

**Expected compute.** Measured from the Phase-21 closure: `total_elapsed_seconds = 34,588.8` for 81 epochs = **427 s/epoch ⇒ 9.61 h per seed**. Three seeds ≈ **28.8 h** pure compute per arm; two arms (control + treatment) × 3 seeds ≈ **57.6 h ≈ 2.4 days**, plus gate construction and the negative-control battery.

**Limitations.**
- n = 3 maximum → sample SD with 2 degrees of freedom; no confirmatory test.
- VAL808 is the selection set → selection-contaminated.
- Isolates FiLM **within GlobalMedFiLM only**. Silent on BARR, on safety, and on baseline comparability.
- Single architecture; does not generalise across backbones.
- Requires physical remediation (Task A P1–P3) or an interruption-tolerant design.

**Approval requirements.** New work order; frozen control harness; prelaunch gate with a direct authority edge; explicit written supervisor authorisation. **Must not be inserted into Phase-28** — that contract sets `post_hoc_factor_addition_forbidden: true`.

---

### C2 — BARR router and safety mechanisms, and their eligible frozen studies

**Exact research question.** Two separable questions that must not be merged:

- **C2a (router).** On one fixed population with one fixed fusion rule, does *benefit routing* (refine only selected cases) produce higher macro Dice than *refine-all* and than *global-only*?
- **C2b (safety).** Does `S_omega` change any **safety-relevant** outcome relative to `S_omega` absent?

**Eligible data.** `ROUTER_DEVELOPMENT` (n = 4,957) as fixed by the Phase-28 contract's `held_constant`. **Note the population conflict:** the Phase-29 descriptive summary and the Phase-22 harm analysis both use VAL808 (n = 808). These are *different populations* and must not be silently mixed; whichever is chosen must be frozen before launch.

**Existing frozen authority.**
- `reports/audits/phase28_one_factor_control_contract.json` — **13 arms**: A0–A8, R1–R3, F1. Critically: `governance_only: true`, **`execution: "NONE"`**, `post_hoc_factor_addition_forbidden: true`. The design is frozen; **nothing in it has ever been executed.**
- Frozen components by digest: GlobalMedFiLM `286689fd…`, Phase-25A refiner `6d28608a…`, Phase-25D `B_phi` `8a412b2f…`, Phase-25F `S_omega` `eee9b97b…`.
- Held constant: preprocessing/ROI rule (threshold 0.30, expansion 1.50, resolution 256), fusion rule (outside-ROI `p_global`; inside-ROI `p_refined`; threshold 0.50), budget 0.25, λ 0.25, bootstrap n_boot 2000 seed 42.

**Existing executed evidence — descriptive, not a controlled ablation.**
- **Phase-29, three seeds, VAL808:** integrated 0.837901 vs backbone 0.835079 ⇒ **+0.002822**, SD 0.000590, sign-consistent; mean `n_selected` 265 of 808 (32.8% routed).
- **Phase-22 harm analysis, oracle ROI, n = 808:** a case is *harmed* when the regional arm reduces Dice. **536 of 808 harmed (harm rate 0.663)**, mean harm −0.0957, worst −0.833, **net gain −34.32**. Harm by domain: BUSI 0.810, KVASIR 0.724, ISIC 0.683, KUB 0.575.

**The most important reading of these two together.** With an *oracle* ROI, refining everywhere is **net harmful** (−34.32). The routed system is **slightly net positive** (+0.0028) while refining only a third of cases. That is consistent with the router's value being **harm avoidance rather than gain creation** — a far more defensible and more interesting claim than superiority, and one this project can actually support.

**A blocking gap for C2b.** The frozen 13-arm design contains **no arm in which `S_omega` is absent** — A8 is *"POST_SAFETY = S_omega present (baseline)"*, and every other arm varies routing, router features, or refiner input. **The safety contribution therefore has no ablation arm even in the frozen design**, and `post_hoc_factor_addition_forbidden: true` means one cannot be added retrospectively. C2b requires a **new prospective study**, not a Phase-28 execution.

**Necessary controls.** Minimum triple A0 (global only) / A1 (refine all) / A8 (baseline), all other factors held per contract; paired bootstrap 2000 / seed 42; identical population and fusion rule across arms; per-arm prediction persistence so harm can be recomputed independently.

**Expected compute.** Because every component is **frozen**, A0/A1/A8 are **inference-only over the population — no training**. At a few forward passes per case this is order **single-digit GPU-hours** for the full 4,957 population and three arms, not days. This is by far the cheapest of the three studies.

**Limitations.**
- Oracle ROI ≠ predicted ROI; the Phase-22 harm figures are an upper bound on what routing must overcome, not a system-level measurement.
- The +0.0028 is small (0.34% relative) and descriptive.
- C2b is **unmeasurable within Phase-28** and has no metric defined at all.
- Component attribution requires arms that exist only in a governance document.

**Approval requirements.** Authorisation to **execute** a contract that is explicitly `execution: "NONE"`; population choice frozen in writing; a separate prospective study for C2b.

---

### C3 — EXT-03B protocol-faithful baseline benchmark

**Exact research question.** Under the **frozen phase09/10 recipe** — AdamW 1e-4, wd 1e-4, `bce_dice` 0.5/0.5 ε 1e-6, full augmentation, **1-channel input**, cosine T_max 100, batch 4, patience 15 — what is the VAL808 equal-domain macro Dice of each of the five baseline architectures across three seeds, and how do they order against each other?

**Eligible data.** Internal TRAIN (5,832) / VAL808 (808), manifest `phase4_v3`. **No TEST. No external inference.**

**Existing frozen authority.** `configs/phase09_clean_v3/*.yaml`, `configs/phase10_clean_v3/*.yaml`, `scripts/training/train_phase10_baselines.py` (L46/L89 execute `AdamW` and `BCEDiceLoss`), `ext02_1_baseline_training_protocol_freeze.json`. This is the authority EXT-03 diverged from in five parameters.

**Necessary controls.**
- Rebuilt prelaunch gate with **at least one edge that reads the frozen authority directly** and compares concrete values (optimizer name, LR, loss name, augmentation operation count, channel count) — not a digest of a derived artifact. This is the specific repair the v1.1 supersession register requires.
- **Per-run harness SHA binding** (EXT-03 bound none).
- 1-channel parameter expectations: unet 7,762,465 · attention_unet 7,850,709 · unetpp 9,159,105 · deeplabv3plus 40,340,769 · segformer_b0 3,714,401 (vs the 3-channel values +576/+576/+576/+6272).
- Full per-epoch log persistence and per-domain metric persistence (EXT-03 discarded per-domain Dice at runtime).
- Positive and negative gate controls.

**Expected compute.** Measured EXT-03 throughput 550–1,030 s/epoch across architectures; augmentation and `bce_dice` add cost. Estimate **~700–1,100 s/epoch × ~75 epochs × 15 runs ≈ 250 h ≈ 10.4 days** pure compute, **12–18 days** with margin and interruption allowance.

**Limitations.**
- Answers **only** C3. Does not isolate FiLM, does not speak to BARR, does not measure safety.
- Three seeds → no confirmatory inference.
- VAL808 remains selection-contaminated.
- Even when protocol-faithful, comparison against GlobalMedFiLM still bundles architecture, task conditioning and seed treatment.

**Approval requirements.** New work order; frozen protocol-faithful harness; rebuilt gate; **Task A P1–P3 remediation first**; explicit supervisor authorisation. Identifier **`EXT-03B`** (provisional) — **not** EXT-04, which is reserved.

---

## 2. Side-by-side

| | **C1 FiLM-off control** | **C2 BARR router / safety** | **C3 EXT-03B baselines** |
|---|---|---|---|
| Answers | FiLM conditioning | router (C2a) · safety (C2b) | protocol-faithful baseline ranking |
| Training required | **yes** (2 arms × seeds) | **no** — components frozen | **yes** (15 runs) |
| Compute | ~57.6 h (2 arms × 3 seeds) | **single-digit GPU-hours** | ~250 h (12–18 d wall) |
| Frozen authority | Phase-21 config | Phase-28 contract (`execution: NONE`) | phase09/10 configs + trainer |
| Executed evidence today | none for the control | Phase-29 +0.00282; Phase-22 harm 0.663 | EXT-03 (divergent) |
| Blocking gap | control never run | **no `S_omega`-absent arm exists** | five protocol divergences |
| Repairs AS-08 | no | no | **yes** |
| Strengthens the central claim | **yes** | **yes** (as harm-avoidance) | indirectly |
| Safety answered | **no** | **no** (C2b needs a new study) | no |
| Host remediation needed | yes | **no** (inference-only) | yes |

---

## 3. Binding constraints on any choice

1. **No retrospective insertion into a frozen study.** Phase-28 sets `post_hoc_factor_addition_forbidden: true`; EXT-03 is COMPLETE and frozen; AS-08 cannot be retro-filled. C1, C2b and C3 each need their **own** identifier and their **own** work order.
2. **EXT-04 stays reserved.** It means AS-01/02/03/04/05/07 progression and scaling. It is not a baseline slot.
3. **FiLM-off is prospective and supplementary.** It is not, and may never be described as, a historically preregistered Phase-28 arm.
4. **AS-08 remains UNRESOLVED** until a protocol-faithful baseline study actually completes and is adjudicated.
5. **C1 / C2 / C3 remain NOT_ESTABLISHED** until the corresponding evidence exists. No document in this package upgrades any of them.
6. **No protected TEST access, no unapproved external inference**, in any option.

---

*End of Task B. Decision support only; no authorisation granted, no experiment launched.*
