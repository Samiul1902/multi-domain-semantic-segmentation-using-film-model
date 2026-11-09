# EXT-03 Scientific Adjudication Addendum — v1.1

**Classification:** `EXT03_SCIENTIFIC_ADJUDICATION_ADDENDUM`
**Version:** 1.1 (additive to v1.0; v1.0 retained byte-identical)
**Generated local:** 2026-10-26T21:50 (+06:00)
**Mode:** strict read-only. No training, no inference, no TEST / ROUTER_HOLDOUT / external access, no frozen artifact modified.

**Authority:** `reports/audits/ext03_scientific_acceptance_and_protocol_adjudication_v1_0.md` (`7ad12fdb…`) and `.json` (`5e4f88d8…`), independently re-validated in `ext03_evidence_provenance_reconciliation_v1_1.json`.

---

## Purpose and scope

v1.0 established *what happened*. This addendum establishes *what may and may not be claimed*. It does not revise any measurement, does not rehabilitate any run, and does not soften any finding. Where v1.0 was uncertain, v1.1 either narrows the uncertainty with new evidence or states plainly that it cannot be narrowed.

The headline disposition is unchanged and is restated here so it cannot drift:

> **`EXT03_COMPLETE__PROTOCOL_DIVERGENT__AS08_PRIMARY_EVIDENCE_NOT_ESTABLISHED`**

---

## 1. D1–D5 — frozen versus executed protocol mismatches

Five parameters of the training recipe differ from the frozen phase09/10 authority. All five were encoded in the harness before the first run on 2026-10-16T07:18 and were never separately authorized as scientific protocol changes.

| ID | Parameter | Frozen authority | Executed | Evidence class |
|---|---|---|---|---|
| D1 | optimizer class | `AdamW` | `Adam` | static source (L137) |
| D2 | learning rate | `1e-4` | `1e-3` (4 architectures) | static source (L50, L136–137) |
| D3 | loss | `bce_dice` 0.5/0.5, ε 1e-6 | `binary_cross_entropy_with_logits` only | static source (L190) |
| D4 | augmentation | mirror 0.5 / rot ±5° / brightness ±0.1 / contrast ±0.1 | none | static source (L84–98) |
| D5 | input channels | `1` | `3` | static source (L43–45), corroborated by parameter deltas |

The frozen authority is not ambiguous. `scripts/training/train_phase10_baselines.py` — named as an authority by the EXT-02.1 freeze — executes `AdamW(lr=1e-4, weight_decay=1e-4)` with `BCEDiceLoss()` at L46 and L89, and consumes `SegmentationTransform(train=True)` for augmentation. The four phase09/10 YAML configs state the same values in declarative form. There is no reading of these artifacts under which `Adam`, `1e-3`, BCE-only and no augmentation are the frozen recipe.

**D5 deserves separate note.** It is the only divergence that was *documented* prospectively — `ext03_training_protocol_resolved.json` declares `"channels": "1->3 (frozen channel semantics)"`. But it was documented in an artifact that simultaneously mis-states the authority for D1 and D3, and it was never carried into the parameter verification (see §7 and the supersession register). Documentation inside a defective instrument does not constitute authorization.

**Authorization status, stated precisely.** These five divergences were *gated* — the Stage B prelaunch acceptance passed on 2026-10-11T19:00Z, before any run — but they were not *authorized*, because the gate that passed them could not see them (§3). The distinction is not pedantic: an authorized divergence is disclosable in a methods section; an invisible one is a defect.

---

## 2. D6 — a post-outcome repair and a cross-family confound, not a value mismatch

D6 is frequently mis-described, so it is stated here in the negative first.

**D6 is not a divergence from the frozen learning rate.** SegFormer-B0 ran at `1e-4`. The frozen authority value is `1e-4`. On the learning-rate axis, D6 *agrees* with the authority.

**D6 is a post-outcome intervention.** It was introduced on 2026-10-25 *after* observing that `segformer_b0_seed42` produced NaN by epoch 5 at `1e-3`. Its authorization is therefore retroactive by construction: the decision to change it could not have been made before the outcome that motivated it. This is materially weaker than D1–D5, which predate every observation.

**D6 is a cross-family confound.** After the repair, SegFormer-B0 is the only family whose learning rate differs from the other four. The matrix therefore does not compare five architectures at one learning rate; it compares four architectures at `1e-3` and one at `1e-4`. Any statement of the form "SegFormer-B0 underperforms DeepLabV3+ under a common protocol" is false on the LR axis.

**Why it was still the right call.** `1e-4` is the frozen internal-baseline LR. The anomaly was `1e-3`, not the override. D6 moved one parameter *toward* the authority while D1–D4 remained *away* from it. The correct characterisation is: **a partial, post-hoc, architecture-specific return to authority, which improves comparability with the frozen protocol and simultaneously destroys LR-comparability within the matrix.**

Both consequences are real and both must be disclosed. Neither cancels the other.

---

## 3. Why the matrix cannot establish AS-08 protocol-faithful primary evidence

AS-08 is the baseline-comparison study assigned to EXT-03 by `ext02_1a_advanced_study_program_freeze.json`, together with AS-27 (baseline reproducibility). The freeze also binds `ext03_may_not_tune: true`.

AS-08's evidentiary value depends on one property: that the baselines were trained under the protocol the manuscript claims. They were not — five parameters differ (§1). Three independent reasons make this fatal for primary-evidence status:

**(a) The certification is self-referential.** `ext03_stageb_prelaunch_acceptance.json` records `training_protocol_sha = 1d456f9f…`. That value is exactly the SHA-256 of `ext03_training_protocol_resolved.json` — verified in v1.0 and re-verified here. The gate therefore compared the harness to the resolved protocol and never compared the resolved protocol to the phase09/10 authority. The resolved protocol contains the contradiction in plain text:

```
"recipe":               { "optimizer": "Adam (phase09/10 authority)" }   ← false
"resolved_from_config": { "optimizer": {"name": "AdamW", ...} }          ← true
```

A gate reading the first line passes. A gate reading the second fails. The gate read the first line.

**(b) A prior stop decision was overridden.** `ext03_pretraining_acceptance.json` returned `all_pass: false`, with `"training recipe resolved": "PARTIAL"`, `"effective batch policy resolved": "PENDING"`, and the explicit decision *"EXT-03 CANNOT COMPLETE; STOP BEFORE FULL SCIENTIFIC TRAINING per the frozen rule."* Training began five days later. Whatever the justification, the record shows a fail-closed gate that did not close.

**(c) Reproducibility (AS-27) is unestablished by construction.** AS-27 asks whether the baselines reproduce. With five unaudited protocol differences and no recorded per-run learning rate for 12 of 15 runs, EXT-03 cannot answer that question even about itself.

**Consequence.** EXT-03 may not supply AS-08 primary evidence. AS-08 remains `UNRESOLVED`. No sentence attributing a performance difference to architecture, when that difference is measured across divergent protocols, may appear in the manuscript.

---

## 4. Why the five-family ordering is descriptive, not fully controlled

The matrix does support *one* controlled claim, and it is worth stating precisely so the boundary is clear.

**Supported:** all five families shared the *same* executed recipe — Adam `1e-3` (except SegFormer at `1e-4`), BCE-only, no augmentation, 3-channel input, batch 4, cosine schedule over 100 epochs, patience 15, identical TRAIN 5832 / VAL 808, identical equal-domain macro-Dice selection, identical threshold 0.5. On that basis the ordering is a **fair internal comparison under a common reduced protocol**:

DeepLabV3+ 0.6657 > UNet++ 0.6409 > Attention-UNet 0.6249 > SegFormer-B0 0.5904 > UNet 0.5421

**Not supported, and this is the part that must travel with the number:**

1. **The ordering is not protocol-invariant.** D4 (no augmentation) inflates seed variance, which the UNet family demonstrates at SD 0.1572. Under a protocol with augmentation the variance structure — and possibly the ordering among the three CNN families, which span only 0.0409 — could differ. UNet++ and Attention-UNet are separated by 0.0160, well inside the range that a protocol change of this magnitude can move.
2. **One family has a different learning rate.** SegFormer-B0 is not comparable to the others on LR (§2), so its position is descriptive only.
3. **Three seeds is not a variance estimate.** n=3 gives a sample SD with 2 degrees of freedom. No confidence interval, no significance test, and no confirmatory comparison exists in EXT-03.
4. **`no_best_seed_headline: true` applies.** The ranking must be reported with per-seed values and family spread, never as a best-seed table.

The honest formulation is: *"under a common reduced protocol, DeepLabV3+ achieved the highest mean equal-domain macro Dice on the development-validation split, and UNet the lowest with the widest seed spread."* Not: *"DeepLabV3+ is the best baseline."*

---

## 5. Why U-Net seed 123 does not isolate a BCE-versus-BCE+Dice effect

`unet_seed123` is the most tempting result in the matrix and the most dangerous to over-read. It reached 0.3606, collapsed to a degenerate solution, and stopped by patience at epoch 31. It is natural to read this as evidence that BCE-only fails and `bce_dice` rescues. That inference is not available.

**(a) Four confounds move together.** Relative to the authority, `unet_seed123` differs in optimizer class, learning rate (10×), loss and augmentation. Any of them, or their interaction, could produce a collapse. A 10× LR increase alone is a sufficient explanation and requires no loss-based account.

**(b) There is no BCE+Dice control.** No run in EXT-03 uses `bce_dice`. The comparison that would isolate the loss — same architecture, same seed, same everything else, loss varied — does not exist and was never run.

**(c) The effect is seed-conditional.** `unet_seed42` reached 0.6279 and `unet_seed3407` 0.6376 under the *identical* BCE-only protocol. A loss-function explanation must therefore explain why the loss is catastrophic for one seed in three and benign for the other two. That is a much stronger claim than "BCE-only is worse", and EXT-03 provides no basis for it.

**(d) n = 1.** One seed, one architecture, one observed collapse.

**What may be said:** the collapse is *consistent with* the class-imbalance failure mode that `bce_dice` is designed to prevent, and it is a legitimate hypothesis-generating observation that argues for a proper controlled loss ablation. **What may not be said:** that EXT-03 demonstrates BCE-only causes collapse, or that `bce_dice` would have prevented it.

The result is retained in full. `negative_results_retained: true` is a frozen rule, and a low score is not a defect — it is a datum. It must not be suppressed, and it must not be promoted to a causal claim.

---

## 6. Remaining uncertainty: D97 and the missing epoch histories

D97 (`LATEST_PT_SELECTION_METADATA_LAGS_ONE_EPOCH`) was repaired on 2026-10-20/21. Six runs completed before the repair and may have resumed under the defective ordering.

**v1.1 narrows this materially.** The `latest.pt` selection metadata is itself a forensic instrument. Under correct ordering, the counter written at the final epoch satisfies `bad == current_epoch − best_epoch`. Under the D97 lag, it is exactly one lower.

| Run | `current − best` | `latest.pt['bad']` | Verdict | Completed |
|---|---|---|---|---|
| unet_seed42 | 15 | 14 | **lag** | 2026-10-16T20:18 |
| unet_seed123 | 15 | 14 | **lag** | 2026-10-17T01:33 |
| unet_seed3407 | 7 | 6 | **lag** | 2026-10-18T13:54 |
| attention_unet_seed42 | 15 | 14 | **lag** | 2026-10-19T08:13 |
| attention_unet_seed123 | 15 | 14 | **lag** | 2026-10-20T01:53 |
| attention_unet_seed3407 | 15 | 14 | **lag** | 2026-10-20T11:01 |
| unetpp_seed42 | 6 | 6 | exact | 2026-10-21T17:12 |
| unetpp_seed123 | 15 | 15 | exact | 2026-10-22T18:53 |
| unetpp_seed3407 | 15 | 15 | exact | 2026-10-23T16:31 |
| deeplabv3plus_seed42 | 15 | 15 | exact | 2026-10-24T04:42 |
| deeplabv3plus_seed123 | 8 | 8 | exact | 2026-10-24T20:31 |
| deeplabv3plus_seed3407 | 15 | 15 | exact | 2026-10-25T19:40 |
| segformer_b0_seed42 | 15 | 15 | exact | 2026-10-26T05:48 |
| segformer_b0_seed123 | 15 | 15 | exact | 2026-10-26T14:13 |
| segformer_b0_seed3407 | 15 | 15 | exact | 2026-10-26T20:51 |

The split is perfect and follows the completion timestamps without exception: **all six lagging runs completed before the repair, all nine exact runs after it.** D97 exposure is therefore no longer inferred from resume counts — it is measured, and the repair boundary is dated to the interval 2026-10-20T11:01 → 2026-10-21T17:12.

**What remains genuinely uncertain, and cannot be resolved:**

1. **Whether any exposed run's `best.pt` was overwritten by a worse model.** D97's mechanism allows a later epoch with `macro` between the understated and true best to satisfy `macro > best` and overwrite the genuine checkpoint. The error direction is strictly conservative — any such run is **understated, never inflated** — but for the six affected runs the epoch histories are absent, so the question cannot be answered.
2. **The true per-epoch curve for six runs.** No epoch log exists anywhere in the repository for `unet` × 3 or `attention_unet` × 3 (verified by exhaustive pattern search across all file types). These are permanently `MISSING_FROM_AVAILABLE_ARTIFACTS`.
3. **The executed learning rate as a runtime fact for 12 runs.** `lr_used` was added by the D99 repair and exists only for the three SegFormer runs.
4. **Resume instants.** `last_resume_time` is overwritten every epoch and therefore equals `completion_time` for all 15 runs.

No run may be repeated to resolve these. `RETRY_FOR_BETTER_SCORE` is a forbidden state, and repetition would replace a disclosed uncertainty with an undisclosed selection.

---

## 7. Why SHA agreement proves artifact consistency, not protocol correctness

Every EXT-03 integrity check passes: 15/15 `best.pt` files match their registry digests, 15/15 internal epochs match `best_epoch`, 15/15 internal macros match `best_metric`, and 15/15 satisfy the stopping identity exactly. It is important to be precise about what that buys.

**What it proves:** the checkpoint on disk is the checkpoint the registry describes; the number reported is the number that checkpoint carries; the run stopped where the stated rule says it should stop. That is *internal consistency of the record*.

**What it does not prove:** that the process producing that record followed the frozen recipe. A perfectly consistent record of a divergent protocol is still a divergent protocol. SHA-256 has no opinion about whether the optimizer was AdamW.

Two concrete illustrations, both verified in this session:

- **`ext03r_param_verification.json`** records `all_match: true` with `implementation_drift: []` — and it is wrong. It records the **1-channel** parameter counts (unet 7,762,465) while the executed models are **3-channel** (7,763,041). The model sources are byte-identical to their frozen identities, so the entire discrepancy is D5. The artifact is internally consistent, cryptographically unremarkable, and certifies a configuration that never ran. The runtime guard `PARAMS` in the harness is the only correct record, and it is correct precisely because it was re-baselined to the drifted values — which means it could never have detected the drift.
- **The harness freeze** records `7c7287d7…` as the frozen harness. The harness that actually executed the first runs was `bcdbada2…`. Both are valid digests of real files. The freeze is a true statement about a file that never ran.

Integrity verification and protocol verification are different activities. EXT-03 passes the first and fails the second, and no amount of the first substitutes for the second.

---

## 8. Why the frozen GlobalMedFiLM comparison cannot isolate FiLM's contribution

GlobalMedFiLM (Phase 21, frozen, checkpoint `286689fd…`, `best_macro_domain_dice` 0.83508 at epoch 66) sits 0.1694 above the best EXT-03 family. This number will be quoted. It must never be quoted as a FiLM effect.

The comparison bundles at least four separable factors:

1. **Task conditioning.** GlobalMedFiLM receives `task_id` and applies FiLM at five sites; the five baselines receive no task signal and cannot know which modality they are segmenting. This is the factor of interest and it is *also* the most obviously advantageous one.
2. **Protocol.** GlobalMedFiLM used `bce_dice` + full augmentation + AdamW `1e-4`. The baselines used BCE-only + no augmentation + Adam `1e-3` (§1). These are different experiments.
3. **Architecture.** A custom residual UNet with GroupNorm and five FiLM sites is not any of the five baselines. The 0.1694 cannot be decomposed into "conditioning" and "architecture" without an architecture-matched control.
4. **Seed treatment.** GlobalMedFiLM is a **single seed** (42). The baselines are three-seed means. Comparing a single run to a three-seed mean compares a point estimate to a point estimate with a variance the other side does not have.

**And the decisive fact: no FiLM-off control exists anywhere in the repository.** A pattern search across `src/`, `scripts/` and `reports/` for a no-FiLM / FiLM-off / task-conditioning-removed variant returns zero hits. In the 13-arm one-factor ablation contract (`phase28_one_factor_control_contract.json`), every arm holds the Phase-21 global **frozen**; `R2`, described as "task conditioning removed", removes `task_id` from the **router**, not from GlobalMedFiLM. The central architectural claim of the project has no control arm in its own ablation family.

The Phase-21 report's own interpretation guard already forbids the sentence. Nothing since has earned it back. **`FiLM attribution: NOT_ESTABLISHED`.**

A feasible control exists and has not been run: because the FiLM output projection is zero-initialised, freezing `film_layers` and `task_embedding` at initialisation yields an architecture-identical, exact-identity plain residual UNet, at roughly 10–11 hours for one seed under the Phase-21 protocol. It is not authorized here and is not executed here.

---

## 9. Unfavorable and inconclusive results — retained

Recorded so that no downstream document can quietly drop them.

| Item | Value | Status |
|---|---|---|
| `unet_seed123` | 0.3606 (best ep16, stop ep31) | degenerate convergence, retained, **not** a defect |
| UNet family SD | 0.1572 (sample), spread 0.2770 | widest instability in the matrix |
| SegFormer-B0 | 0.5904, rank 4 of 5 | below all three modern CNNs |
| Every EXT-03 family mean | 0.5421–0.6657 | below GlobalMedFiLM 0.83508 |
| Gap to GlobalMedFiLM | 0.1694 (best family) | **not** attributable to FiLM |
| Integrated model vs backbone | 0.8379 vs 0.8351 = **+0.0028** | the R+B+S stack adds almost nothing |
| AS-08 | — | **UNRESOLVED** |
| FiLM attribution | — | **NOT ESTABLISHED** |
| Confirmatory tests | 0 | exploratory only |
| TEST evaluation | 0 | locked, never read |
| Per-domain metrics | — | computed then discarded at runtime |
| IoU / precision / recall / HD95 | — | never computed |
| Epoch logs for 6 of 15 runs | — | **MISSING_FROM_AVAILABLE_ARTIFACTS** |

---

## 10. Disposition

`EXT03_COMPLETE__PROTOCOL_DIVERGENT__AS08_PRIMARY_EVIDENCE_NOT_ESTABLISHED`

Permitted uses of EXT-03:
1. A common-protocol architecture ranking, explicitly labelled reduced-protocol and exploratory.
2. A negative-results and failure-mode record (the `unet_seed123` collapse; the SegFormer from-scratch instability).
3. A demonstration that task-conditioned multi-domain segmentation requires conditioning, stated as a *motivation* rather than a measured effect.

Prohibited uses: AS-08 primary evidence; protocol-faithful baseline comparison; comparator against RA-MedFiLM-BARR; any causal claim about FiLM, about `bce_dice`, or about augmentation.

No EXT-04 authorization is granted or implied by this document. No FiLM-control run is authorized. The three options for the supervisor's decision are set out in `ext03_supervisor_decision_memorandum_v1_1.md`.

---

*End of addendum. No training, no inference, no source modification, no TEST or ROUTER_HOLDOUT access.*
