# EXT-03 Scientific Acceptance and Protocol-Adjudication Audit

**Classification:** `EXT03_SCIENTIFIC_ACCEPTANCE_AND_PROTOCOL_ADJUDICATION`
**Version:** 1.0
**Generated local:** 2026-10-26T21:20 (+06:00)
**Mode:** STRICT READ-ONLY. No training, no inference, no re-runs, no source edits.
**Preservation:** all checkpoints, logs, manifests, registries, source and completion summaries were read only. No byte was modified. Verified after audit: `ext03_matrix_final_family_summary_v1_0.csv` SHA still `6d1a4910…`; `ext03_run_registry.json` SHA still `ea474c49…`.

---

## 0. Verdict

**`EXT03_COMPLETE__PROTOCOL_DIVERGENT__AS08_PRIMARY_EVIDENCE_NOT_ESTABLISHED`**

The matrix is **technically complete and internally consistent**: 15/15 runs, 15/15 checkpoints SHA-verified, 15/15 stopping rules arithmetically exact. Nothing is corrupted and nothing is overstated.

But the executed protocol is **not** the frozen phase09/10 authority. Five divergences (optimizer class, learning rate, loss, augmentation, input channels) were baked into the harness before the first run, were certified as "training protocol unchanged" by a gate that compared the harness **to its own resolved protocol rather than to the higher authority**, and that resolved protocol itself mis-states the authority it claims to inherit.

Consequence: **EXT-03 cannot supply AS-08 primary evidence for a protocol-faithful baseline comparison**, and cannot be used as the comparator against RA-MedFiLM-BARR. It remains valid as a **common-protocol architecture ranking** (all five families shared the same reduced recipe, so the *relative* ordering is internally fair) and as a **reduced-protocol reference matrix** with mandatory disclosure.

---

## 1. Task 1 — Frozen authority inventory

### 1.1 Governing hierarchy (as written)

| Rank | Artifact | SHA-256 (verified on disk) | What it actually binds |
|---|---|---|---|
| A | `reports/external_extension/ext02_1_baseline_training_protocol_freeze.json` | `dcda2719…08fb89` | Top-level EXT-02.1 freeze. Declares recipe fields "as frozen internal baseline authority", `ext03_may_not_tune: true`, and names the authority set in `authority_binding`. |
| B | `configs/phase09_clean_v3/phase09_unet_baseline_clean_v3.yaml` | `8a45458c…b5172a` | Concrete recipe for UNet. |
| B | `configs/phase10_clean_v3/phase10_attention_unet_clean_v3.yaml` | `70e08ad5…260c02` | Concrete recipe. |
| B | `configs/phase10_clean_v3/phase10_unetpp_clean_v3.yaml` | `e2788e50…4f24f53` | Concrete recipe + `initialization: random_kaiming_no_pretrained_weights`. |
| B | `configs/phase10_clean_v3/phase10_deeplabv3plus_clean_v3.yaml` | `a5220e31…dd5b57` | Concrete recipe. |
| B | `scripts/training/train_phase10_baselines.py` | (named in A) | **Executed historical authority.** L46/L89 `AdamW(lr=1e-4, wd=1e-4)`; L46 `BCEDiceLoss()`; `SegmentationTransform` train-mode augmentation. |
| C | `src/losses/segmentation.py` L17–23 | — | `BCEDiceLoss(bce_weight=0.5, dice_weight=0.5, epsilon=1e-6)`. |
| C | `src/data/transforms.py` L18–41 | — | Augmentation implementation: mirror p=0.5, rotate ±5° (bilinear image / nearest mask), brightness ±0.1, contrast ±0.1. |
| D | `reports/planning/ext02_1a_advanced_study_program_freeze.json` | — | Assigns **AS-08 + AS-27 (baseline reproducibility)** to EXT-03. Rules: `no_best_seed_headline`, `negative_results_retained`, `exploratory_not_confirmatory`. |
| D | `reports/baselines/ext03_training_protocol_resolved.json` | `1d456f9f…7eaf2e2` | The protocol **actually certified**. Contains the contradiction in §2.2. |
| D | `reports/baselines/ext03_initialization_policy.json` | — | All five scratch; no medical pretrained weights. |
| D | `reports/baselines/ext03_implementation_identities.json` | — | Model source SHAs. **All still match on disk** (verified). |
| D | `reports/baselines/ext03r_segformer_identity.json` | — | SegFormer `CONFIG_ONLY__NO_PRETRAINED_WEIGHTS`, 3,714,401 params. |
| D | `reports/baselines/ext03r_run_harness_freeze.json` | — | Harness `7c7287d7…`, forbidden states `BAD_RESULT / LOW_SCORE / RETRY_FOR_BETTER_SCORE`, resume-safety contract. |

### 1.2 Frozen recipe, resolved per field

| Field | Frozen value | Source |
|---|---|---|
| Optimizer | **AdamW** | all four configs; `train_phase10_baselines.py` L46, L89 |
| Learning rate | **1e-4** | same |
| Weight decay | **1e-4** | same |
| Loss | **BCE+Dice, 0.5/0.5, ε=1e-6** | configs `loss:`; `BCEDiceLoss` |
| Augmentation | **mirror 0.5 / rot ±5° / brightness ±0.1 / contrast ±0.1** | configs `augmentation:`; `SegmentationTransform` |
| Scheduler | CosineAnnealingLR, T_max 100 | configs |
| Batch | 4, accumulation 1, effective 4 | configs |
| Input channels | **1** | configs `model.input_channels: 1` |
| Base channels | 32 | configs |
| Initialization | random / Kaiming, **no pretrained** | configs; `ext03_initialization_policy.json` |
| Epoch cap | 100 | configs |
| Patience | 15 | configs |
| Threshold | 0.5 | configs |
| AMP | true | configs |
| Checkpoint selection | macro-domain dev-val Dice, equal domain weighting | `ext02_1` freeze; configs `monitor: val_macro_dice` |
| Gradient clipping | **silent** (no value in any authority) | — |
| num_workers | 0 | configs |

### 1.3 Harness version chain (reconstructed)

| SHA-256 | Role | Recorded where | Timestamp |
|---|---|---|---|
| `7c7287d7…6d9c5e5` | EXT-03R frozen harness | `ext03r_run_harness_freeze.json` | 2026-10-11T18:30Z |
| `bcdbada2…18e67965` | **Harness that actually executed the first runs** | `ext03_recovery_audit_v1.json` `runner_sha`; D97 `runner_sha_before` | observed 2026-10-20T16:47 |
| `46d5841d…2f302a3fd0` | Post-D97 (persistence reorder) | `ext03_d97_resume_state_repair_v1.json` | 2026-10-20/21 |
| `91fc1733…119abb67ae` | Post-D99 (LR override + non-finite guard), current, 12,437 B | on disk | 2026-10-25 |

**Finding 1.1 — the frozen harness never ran.** `7c7287d7…` ≠ `bcdbada2…`. The transition `7c7287d7 → bcdbada2` is **undocumented**; no artifact records it.

**Finding 1.2 — Stage B launched with no recorded harness SHA.** `ext03_stageb_prelaunch_acceptance.json` records `training_protocol_sha` but no `harness_sha`. The Stage B executable is therefore unbound at launch. Combined with Finding 1.1, **no artifact proves which harness produced the 15 runs**, other than inference from the recovery audit's `bcdbada2` observation on 2026-10-20.

### 1.4 Fail-closed gate that was overridden

`reports/baselines/ext03_pretraining_acceptance.json` (2026-10-11T17:00Z):

- `"training recipe resolved": "PARTIAL"`
- `"effective batch policy resolved": "PENDING"`
- `"all_pass": false`
- `"decision": "EXT-03 CANNOT COMPLETE; STOP BEFORE FULL SCIENTIFIC TRAINING per the frozen rule."`

Training nevertheless began 2026-10-16T07:18. The blocker was cleared by `ext03_stageb_prelaunch_acceptance.json` (2026-10-11T19:00Z, `all_pass: true`), whose gate **"training protocol unchanged" = PASS** is the pivotal claim. §2.2 shows why that claim is vacuous.

---

## 2. Task 2 — Reduced-protocol discrepancy

### 2.1 Divergence register

**D1 — Optimizer class**

| | |
|---|---|
| Frozen | `AdamW` |
| Executed | `Adam` |
| Source | `scripts/training/run_ext03_baseline_matrix.py` **L137**: `opt = torch.optim.Adam(model.parameters(), lr=lr_used, weight_decay=WD)` |
| Authorized pre-observation | **No** — no artifact authorizes replacing AdamW. The resolved protocol asserts `"optimizer": "Adam (phase09/10 authority)"`, which is factually false (§2.2). |
| Scientific consequence | AdamW decouples weight decay from the gradient moment; Adam applies L2 inside the adaptive denominator. With wd 1e-4 the practical difference is small but non-zero, and it is not the frozen recipe. |
| Comparability | Breaks protocol identity with phase09/10 and with RA-MedFiLM-BARR. |
| AS-08 eligible | **No** (as protocol-faithful evidence) |

**D2 — Learning rate**

| | |
|---|---|
| Frozen | `1e-4` |
| Executed | `1e-3` for unet / attention_unet / unetpp / deeplabv3plus; `1e-4` for segformer_b0 |
| Source | **L50** `LR = 1e-3`; **L54** `LR_OVERRIDE = {"segformer_b0": 1e-4}`; **L136** `lr_used = LR_OVERRIDE.get(a, LR)`; **L137** |
| Authorized pre-observation | **No.** No artifact records a 10× LR increase. `ext02_1` freeze: `ext03_may_not_tune: true`. |
| Scientific consequence | 10× larger steps under AMP. This is the direct cause of **D99**: SegFormer-B0 from scratch at 1e-3 overflowed fp16 in the decode head, poisoned `BatchNorm1d(256)` running statistics to inf/nan by epoch 5, and produced a non-resumable checkpoint. It also plausibly explains `unet_seed123`'s collapse to 0.3606 (BCE-only at 1e-3 can lock onto all-background). |
| Comparability | **Material.** This is the single largest confound. |
| AS-08 eligible | **No** |

**D3 — Loss function**

| | |
|---|---|
| Frozen | `bce_dice`, bce_weight 0.5, dice_weight 0.5, ε 1e-6 |
| Executed | `F.binary_cross_entropy_with_logits(out.float(), y)` — **BCE only, no Dice term** |
| Source | **L190** |
| Authorized pre-observation | **No.** Resolved protocol says `"loss": "as frozen phase09/10 authority"` — which is `bce_dice`. The claim and the code disagree. |
| Scientific consequence | Without the Dice term there is no explicit overlap pressure, so a BCE-only model on 4 pooled domains with class-imbalanced masks can settle into predicting background. **This is the most likely mechanism behind `unet_seed123` (0.3606) and it is exactly what the frozen `bce_dice` was there to prevent.** |
| Comparability | **Material.** Loss family is a first-order determinant of segmentation behaviour. |
| AS-08 eligible | **No** |

**D4 — Augmentation**

| | |
|---|---|
| Frozen | mirror p=0.5, rotation ±5°, brightness ±0.1, contrast ±0.1 |
| Executed | **none** |
| Source | **L84–98** `load_pair()` — aspect-preserving resize (bilinear image / nearest mask) + symmetric pad + `/255.0` + `>0` binarization. No flip, no rotation, no photometric transform anywhere in the file. |
| Authorized pre-observation | **No.** Resolved protocol says nothing about augmentation at all — it is simply absent from the resolved artifact, so the gate had nothing to compare against. |
| Scientific consequence | 5,832 training slices without augmentation. Regularization is reduced, variance across seeds increases, and small-data overfitting is unmasked. Directly relevant to the 0.2770 UNet spread. |
| Comparability | **Material**, especially for seed variance claims. |
| AS-08 eligible | **No** |

**D5 — Input channels**

| | |
|---|---|
| Frozen | `input_channels: 1` (all four configs); phase09/10 models are grayscale-input |
| Executed | `in_channels=3` |
| Source | **L43–45** `KW = {..., "unet": dict(in_channels=3, out_channels=1), ...}` |
| Authorized pre-observation | **Partially.** `ext03_training_protocol_resolved.json` declares `"channels": "1->3 (frozen channel semantics)"`, so the change is *documented* prospectively. But it contradicts the configs it claims to inherit, and it was **not carried into the parameter verification** (§4, item 14). |
| Scientific consequence | **+576 params** for the three UNets (2 extra input channels × 32×3×3) and **+6,272** for DeepLabV3+ (2 × 7×7×64). The executed models are not the frozen models. |
| Comparability | Moderate — all five families received 3 channels, so the internal comparison is fair; but the models differ from phase09/10. |
| AS-08 eligible | **No** (as protocol-faithful), **Yes** (as a fair internal comparison) |

**D6 — SegFormer-B0 learning rate (D99)**

| | |
|---|---|
| Frozen | 1e-4 |
| Executed | 1e-4 |
| Source | **L54**, **L136–141** |
| Authorized pre-observation | **No — this one is post-hoc.** It was introduced *after* observing NaN at epoch 5 of `segformer_b0_seed42` on 2026-10-25. |
| Scientific consequence | **Corrective, and in the direction of the authority.** 1e-4 *is* the frozen phase09/10 LR; the 1e-3 it replaced was the anomaly. So D99's repair restores one frozen value while the other four divergences remain. |
| Comparability | Improves SegFormer's comparability with the authority; leaves it incomparable with the other four families *on LR*. |
| AS-08 eligible | No, but this is the **least** objectionable divergence — it is a return to authority, not a departure. |

### 2.2 Why the "training protocol unchanged = PASS" gate is vacuous

The gate compared the harness against `ext03_training_protocol_resolved.json`, and recorded `training_protocol_sha = 1d456f9f8f3b666ba8d0b128e4a5336be6e59b7ef3a8c6855383102867eaf2e2`. **I verified that this is exactly the SHA-256 of that file.** So the gate is self-referential: it certifies the harness equals the resolved protocol, and never checks the resolved protocol equals the authority.

And the resolved protocol is internally contradictory:

```
"recipe": {
    "optimizer": "Adam (phase09/10 authority)",      <-- false
    "loss": "as frozen phase09/10 authority",        <-- false (BCE != bce_dice)
    ...
    "resolved_from_config": {
        "optimizer": {"name": "AdamW", "learning_rate": 0.0001, ...}   <-- the truth
        "loss": {"name": "bce_dice", "bce_weight": 0.5, ...}           <-- the truth
    }
}
```

The same artifact contains both the correct inherited values and a false summary of them. A gate that reads the summary passes; a gate that reads `resolved_from_config` fails. The gate read the summary.

**Adjudication:** D1–D5 were *not* authorized as scientific protocol changes. They were **silently encoded and then certified by a gate that could not see them.** The distinction matters: an authorized divergence is disclosable; this one was invisible until the completion summary surfaced it.

---

## 3. Task 3 — Verification of all 15 run histories

### 3.1 Checkpoint identity — 15/15 PASS

For every run, three independent facts agree: registry `checkpoint_sha` == raw-byte SHA-256 of `best.pt`; `best.pt["epoch"]` == registry `best_epoch`; `best.pt["macro"]` == registry `best_metric` (exact to 1e-9).

| Run | Best | Ep | Stop | Resume | `best.pt` SHA | Bytes |
|---|---|---|---|---|---|---|
| unet_seed42 | 0.6279 | 66 | 81 | 0 | `48f55e22…` ✓ | 31,107,096 |
| unet_seed123 | 0.3606 | 16 | 31 | 0 | `8c75c7e1…` ✓ | 31,107,096 |
| unet_seed3407 | 0.6376 | 93 | 100 | **2** | ✓ | 31,107,096 |
| attention_unet_seed42 | 0.6367 | 75 | 90 | **1** | ✓ | 31,480,512 |
| attention_unet_seed123 | 0.6392 | 71 | 86 | 0 | ✓ | 31,480,512 |
| attention_unet_seed3407 | 0.5987 | 38 | 53 | 0 | ✓ | 31,480,512 |
| unetpp_seed42 | 0.6615 | 94 | 100 | **4** | ✓ | 36,715,928 |
| unetpp_seed123 | 0.6449 | 70 | 85 | **1** | ✓ | 36,715,928 |
| unetpp_seed3407 | 0.6163 | 71 | 86 | 0 | ✓ | 36,715,928 |
| deeplabv3plus_seed42 | 0.6591 | 62 | 77 | 0 | ✓ | 161,719,960 |
| deeplabv3plus_seed123 | 0.6719 | 92 | 100 | 0 | ✓ | 161,719,960 |
| deeplabv3plus_seed3407 | 0.6662 | 85 | 100 | **1** | ✓ | 161,719,960 |
| segformer_b0_seed42 | 0.5951 | 40 | 55 | 0 | `a241b104…` ✓ | 14,932,758 |
| segformer_b0_seed123 | 0.5913 | 40 | 55 | 0 | ✓ | 14,932,758 |
| segformer_b0_seed3407 | 0.5849 | 28 | 43 | 0 | ✓ | 14,932,758 |

### 3.2 Stopping rule — 15/15 arithmetically exact

Every run satisfies `stop_epoch == min(100, best_epoch + 15)`. This is an exact identity, not an approximation, and it holds for all fifteen:

`66+15=81` · `16+15=31` · `93+15>100→100` · `75+15=90` · `71+15=86` · `38+15=53` · `94+15>100→100` · `70+15=85` · `71+15=86` · `62+15=77` · `92+15>100→100` · `85+15=100` · `40+15=55` · `40+15=55` · `28+15=43`

**No run stopped early, no run overran, no run was retried for a better score.** The forbidden states `BAD_RESULT / LOW_SCORE / RETRY_FOR_BETTER_SCORE` do not appear in the registry.

### 3.3 Independent recomputation from epoch logs — 9/15

Where epoch-level console output survives, I recomputed `best = max(macro)` and `best_epoch = argmax(macro)` from the raw epoch lines. **All nine matched the registry exactly** (tolerance 5e-5):

`deeplabv3plus_seed42` (ep1–77) · `deeplabv3plus_seed123` (1–100) · `deeplabv3plus_seed3407` (1–100) · `unetpp_seed123` (1–85) · `unetpp_seed3407` (1–86) · `unetpp_seed42` (30–100 only) · `segformer_b0_seed42` (1–55) · `segformer_b0_seed123` (1–55) · `segformer_b0_seed3407` (1–43)

**6/15 have no epoch log on disk at all** — all three `unet` and all three `attention_unet` runs. Their selection cannot be independently recomputed (§4, item 12).

### 3.4 The four flagged runs

**`unet_seed123` — 0.3606, NOT a defect.** Best at ep16, patience stop at ep31, `resume_count = 0`, `technical_failure_reason = null`. A clean, complete run that converged to a degenerate solution. Given D3 (BCE-only) and D2 (1e-3), this is the *expected* failure mode, and it is **evidence for the frozen `bce_dice`**, not evidence against the architecture. Classifying it as a defect would be wrong; suppressing it would be worse (`negative_results_retained: true`).

**`unet_seed3407` — resume_count = 2, both resumes before the D97 repair.** The two resumes occurred on/before 2026-10-18T13:54, while `bcdbada2` (defective ordering) was in force. D97's mechanism: `latest.pt` lagged one epoch, so on resume `best` was understated and `bad` inflated. This run reached the 100-epoch ceiling (best ep93, bad=7 at ep100), so **early stopping was never triggered** and the inflated counter had no effect. The residual risk is the overwrite scenario: a later epoch with `macro` between the understated and true best would overwrite `best.pt` with a worse model. **Direction of any error is conservative — understated, never inflated.** It cannot be resolved without the missing epoch log.

**`attention_unet_seed42` — resume_count = 1, D97 ordering concern confirmed.** The resume occurred before the repair (completion 2026-10-19T08:13, repair 2026-10-20/21). Stopping is `75+15=90` exactly, which is consistent with a correct `bad` counter at the final best. Same conservative-direction argument; same unresolvability without the missing log.

**`unetpp_seed42` — resume_count = 4, and the one run whose resume checkpoint was manually edited.** This is the run that exposed D97. `latest.pt` was reconciled in place (selection metadata restored from `best.pt` + registry — no tensor modified, no value invented). Evidence: the 2026-10-21T00:09 resume log opens at ep30 with `best=0.5817 bad=1`, i.e. the reconciled state, not the defective `0.5754 / bad=3`. **`best.pt` was never touched** — its SHA matches the registry and its internal epoch is 94, well after the repair. Scientific artifact integrity holds.

**D99 chronology (all three segformer runs).** `seed42` diverged at ep5 on 2026-10-25 under 1e-3; the poisoned attempt was **moved** (not deleted) to `reports/baselines/recovery_evidence/segformer_b0_seed42_d99_void_ep5/` with `PROVENANCE.json`; the LR override was added; all three seeds then ran clean. Registry preserves the void attempt under `d99_void_attempt` (best 0.00274, lr 1e-3). **153 epochs across three seeds with zero non-finite losses** after the repair. The guard `if not torch.isfinite(loss): raise` (L196–197) never fired.

### 3.5 Ordinary interruption vs scientifically invalid continuation

| Run | Interruption class | Continuation valid? |
|---|---|---|
| unet_seed3407 (rc=2) | Host-level termination, checkpoint intact | **Valid but under D97 ordering** — may understate |
| attention_unet_seed42 (rc=1) | Host-level termination | **Valid but under D97 ordering** — may understate |
| unetpp_seed42 (rc=4) | Host-level + D97-exposed | **Valid** — state reconciled with evidence, then clean |
| unetpp_seed123 (rc=1) | Host-level | **Valid** — post-repair harness |
| deeplabv3plus_seed3407 (rc=1) | Host-level | **Valid** — post-repair harness |
| segformer_b0_seed42 | D99 divergence (not interruption) | **Invalid attempt voided and preserved**; repaired re-run valid |

None of the 15 runs was repeated for low performance.

---

## 4. Task 4 — Evidence completeness

**Rule applied: absent evidence is marked MISSING, not PASS.**

| # | Required evidence | Status | Basis |
|---|---|---|---|
| 1 | 15 complete recorded runs | **PASS** | registry 15/15 `COMPLETE`, 0 `technical_failure_reason` |
| 2 | 15 matching checkpoints | **PASS** | SHA + internal epoch + internal macro all agree, 15/15 |
| 3 | Three prescribed seeds per architecture | **PASS** | 42/123/3407 × 5 architectures |
| 4 | True scientific batch size 4 | **PARTIAL** | `BATCH = 4` at L49, no accumulation; but **not recorded per run** in the registry, and the harness changed three times |
| 5 | Source/configuration provenance | **MISSING** | `training_config_sha` and `model_source_sha` are `null` for **all 15 runs**; no Stage B harness SHA recorded; `log_path` in the registry points to `runs/<id>/train.log` which **does not exist for any run** (15/15 dangling) |
| 6 | Eligible TRAIN5832 / VAL808 population identity | **PASS** | manifests `28702fc3…` (TRAIN) and `082c80b2…` (VAL) match the frozen values; logs confirm `TRAIN=5832 VAL=808` |
| 7 | No TEST / ROUTER_HOLDOUT / external leakage | **PASS (static only)** | source references only `manifests/phase4_v3/train.csv` and `val.csv` (L40–41); no test path appears anywhere in the harness. **But** the claimed `test_accessed=false` in the completion summary is a hard-coded literal with no counter behind it |
| 8 | Per-seed metrics | **PASS** | one `best_metric` per run |
| 9 | **Per-domain metrics** | **MISSING** | `eval_val` computes `dom` (L122) and returns it (L125); `run_one` binds it at L205 and **never persists it**. Per-domain Dice is discarded at runtime |
| 10 | Dice | **PASS** | equal-domain macro Dice, threshold 0.5 |
| 11 | **IoU, precision, recall, valid HD95** | **MISSING** | not computed anywhere in the harness |
| 12 | **Training curves** | **MISSING (6/15) / PARTIAL (9/15)** | no machine-readable per-epoch artifact for any run; curves exist only as console text. `unet`×3 and `attention_unet`×3 have **no epoch log at all**; `unetpp_seed42` is missing ep1–29 |
| 13 | **Selected-checkpoint histories** | **MISSING** | no record of which epochs were ever written to `best.pt` or overwritten |
| 14 | Parameter counts | **PARTIAL — and the frozen record is wrong** | runtime guard `PARAMS` (L46) is **correct** and matches actual instantiation. But `ext03r_param_verification.json` records the **1-channel** counts and claims `all_match: true, implementation_drift: []`. Actual: unet 7,763,041 vs recorded 7,762,465; attention 7,851,285 vs 7,850,709; unetpp 9,159,681 vs 9,159,105; deeplabv3plus 40,347,041 vs 40,340,769; segformer matches. Model sources are byte-identical to the frozen identities, so the discrepancy is entirely the 1→3 channel change (D5). **That artifact verifies a configuration that never ran.** |
| 15 | Runtime / compute records | **PARTIAL** | `start_time` / `completion_time` present; **no per-epoch seconds, no GPU-memory record**, although `ext03r_run_harness_freeze.json` promises "wall-clock + gpu-mem tracking". Wall-clock also contains interruption dead time, so it is not a clean compute measure (e.g. `unet_seed3407` 36.2 h/100 ep vs `unet_seed42` 13.0 h/81 ep) |

### 4.1 Additional provenance defects found

**P1 — `last_resume_time` is not a resume timestamp.** The runner writes it **every epoch** (L220–223), so for all 15 runs it equals `completion_time`. Actual resume instants are unrecoverable from the registry. This is why §3.4 can only bound the D97 exposure by inference.

**P2 — 12/15 runs have no recorded learning rate.** `lr_used` / `lr_source` (L140–141) were added by the D99 repair on 2026-10-25. Only the three segformer runs carry them. For the twelve CNN runs, the executed LR is known **only** from `LR = 1e-3` at L50 in the *current* source, which has changed twice since those runs executed.

**P3 — no runtime leak counters.** `ext03_stageb_prelaunch_reconciliation.json` records `test_reads: 0` etc. as pre-launch counters. Nothing increments or re-checks them post-run. The leak claim rests on static source inspection, which is strong but is not what the completion summary asserts.

---

## 5. Task 5 — Completion-summary generator audit

Artifacts audited: `reports/baselines/ext03_matrix_completion_summary_v1_0.json` (`8e35499a…`, 11,433 B), `reports/tables/ext03_matrix_final_family_summary_v1_0.csv` (`6d1a4910…`, 479 B), `scripts/analysis/ext03_matrix_completion_summary.py`.

| Check | Verdict | Detail |
|---|---|---|
| Numeric aggregation | **PASS — exact** | Independently recomputed all 5 families × 5 statistics from the registry at 1e-12 tolerance. Mean, min, max, spread, and SD all match exactly. Ranking order correct. `gap_to_global_medfilm` = 0.8350791259413984 − mean, correct. |
| SD convention declared? | **DEFECT** | `statistics.stdev` is the **sample** SD (n−1). Undeclared. With n=3 this is material: UNet SD is 0.157195 sample vs 0.128349 population — an 18% difference on the number most likely to be quoted. |
| SHA guard when digest absent | **DEFECT — fails open** | L~78: `if recorded and actual != recorded:` — when `checkpoint_sha` is missing/`None`/empty, the condition short-circuits and the guard **silently passes**. A run with no recorded digest is treated as verified. Should be fail-closed (`if not recorded: abort`). |
| CSV write-once enforcement | **DEFECT — not enforced** | L163 `OUT_CSV.write_text(...)` is a plain overwrite. Only the JSON is write-once (`O_CREAT|O_EXCL|O_WRONLY` + `O_BINARY` + full-write loop + `fsync` + `st_size` check, L140–155). The CSV can be silently rewritten. |
| JSON write-once | **PASS — verified empirically** | Re-running the generator raises `FileExistsError: [Errno 17]` at L143. The abort occurs *before* the CSV write, so the probe left the CSV byte-identical (`6d1a4910…` re-confirmed). |
| Failure mode quality | **DEFECT (minor)** | The re-run failure is an uncaught traceback, not a clean fail-closed diagnostic. |
| Hard-coded UTC timestamp | **DEFECT — confirmed** | L109 `"generated_utc": "2026-10-26T20:52:00Z"` is a literal, not derived from the clock. It happens to be close to the real generation time, which makes it more dangerous, not less: it cannot be distinguished from a genuine timestamp. |
| Data-access safeguards backed by evidence? | **DEFECT — unsupported** | L113–114 `"test_accessed": False`, `"router_holdout_accessed": False` are hard-coded literals. Nothing in the generator opens, counts, or verifies anything. The claim is true (the generator only reads the registry and checkpoints) but the artifact asserts it without evidence — exactly the pattern this audit exists to catch. |
| Self-binding to inputs | **DEFECT** | The artifact records neither the registry SHA nor its own generator SHA. It cannot be tied to the inputs that produced it, so a later registry mutation would go undetected. |
| Selection integrity checked? | **DEFECT** | The generator verifies status, metric range and checkpoint SHA — but never `best_epoch ≤ current_epoch`, never the `stop == min(100, best+15)` identity, and never the presence of all three prescribed seeds. §3.2's strongest result is not enforced by the artifact that certifies completion. |

**Recommended repair (not performed — read-only mandate):** v1.1 with fail-closed digest guard, clock-derived UTC, write-once CSV, `sd_convention: "sample_n_minus_1"`, `registry_sha` + `generator_sha` binding, execution-derived access evidence (or removal of the claim), and enforcement of the stopping identity. The v1.0 artifacts should then be **moved** to `reports/audits/_v1_00_*superseded*`, never deleted.

---

## 6. Consequences for the scientific record

1. **EXT-03 is a valid common-protocol architecture ranking.** All five families shared the same reduced recipe, so the ordering — DeepLabV3+ 0.6657 > UNet++ 0.6409 > Attention-UNet 0.6249 > SegFormer-B0 0.5904 > UNet 0.5421 — is internally fair. This is the strongest claim the matrix supports.

2. **EXT-03 is not AS-08 primary evidence for protocol-faithful baselines.** D1–D4 are unauthorized divergences. Any manuscript sentence of the form "our baselines were trained under the same protocol as the proposed model" is **false** and must not be written.

3. **The 0.1694 gap to GlobalMedFiLM (0.83508) is uninterpretable as a FiLM effect.** It bundles five protocol divergences, architecture, and task conditioning. This confirms — and now *quantifies the reason for* — the standing prohibition on "FiLM caused +X".

4. **The `unet_seed123` collapse is the most scientifically useful datum in the matrix.** It is the natural experiment that the frozen `bce_dice` was designed to prevent, and it failed exactly as predicted. Report it as such.

5. **Nothing requires re-running to fix a low score.** Re-running would violate `RETRY_FOR_BETTER_SCORE`. The defects are provenance and disclosure defects; they are repaired by documentation and by a prospective protocol-faithful study, not by repeating runs.

---

## 7. Open items carried forward (not actioned here)

- **O1** — Prospective protocol-faithful baseline study (AdamW 1e-4, `bce_dice` 0.5/0.5, full augmentation, 1-channel-or-3-channel declared once). Requires explicit authorization; cannot be an EXT-03 retry.
- **O2** — FiLM-off control (architecture-identical, zero-init frozen `film_layers`) — still the single missing experiment for the central architectural claim.
- **O3** — Recover or declare-lost the epoch logs for `unet`×3 and `attention_unet`×3.
- **O4** — Correct `ext03_training_protocol_resolved.json`'s false `"Adam (phase09/10 authority)"` field (documentation only; supersede, do not edit in place).
- **O5** — Correct `ext03r_param_verification.json`, whose `all_match: true` refers to a 1-channel configuration that never executed.
- **O6** — Record a Stage B harness SHA retroactively from the recovery-audit evidence, and document the `7c7287d7 → bcdbada2` transition.
- **O7** — Repair the completion-summary generator to v1.1 per §5.
- **O8** — Hardware: CMOS battery + UPS. Three host terminations in four days, RTC 5.19 days behind.

---

*End of audit. No training, no inference, no source modification, no TEST access, no ROUTER_HOLDOUT access was performed.*
