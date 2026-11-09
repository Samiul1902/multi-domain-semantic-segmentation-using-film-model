# PHASE-13 PART-1B — SECOND SCIENTIFIC SAFE STOP (COVERAGE-SEMANTICS CONFLICT)

- **experiment_id:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`
- **status:** **PASS**
- **trainer stopped:** YES (forceful — graceful refused by Windows)
- **waiters stopped:** YES
- **relaunch / resume / restart:** NO
- **code modified:** NO

---

## Why this stop matters — the conflict is CONFIRMED MATERIAL

Historical executing Phase-13 coverage was effectively **bbox-intersection**
(`gt_components` never attached native masks, so `evaluate_roi_coverage` used its
bbox fallback). R2B changed clean-v3 primary coverage to **pixel-mask** coverage.

R2/R2A give precedence to **historical executing code** for the primary
checkpoint-selection protocol, so R2B is potentially a **material primary
checkpoint-metric change once proposals become nonzero**.

**That condition is now satisfied.** Epoch 31 emitted **4.1456 proposals/image**
with nonzero primary recall, so the two semantics can no longer coincide.

---

## Completed state

| item | value |
|---|---|
| last completed epoch | **31** |
| history rows | **31** |
| contiguous `1..N` | **YES** |
| `latest.pt` epoch | **31** |
| `best.pt` epoch | **31** |
| `best_epoch_so_far` | **31** |
| `bad_epochs` | **0** |
| `global_step` | **5983** |

### Completed epochs ≥ 29 (read from immutable history; not recomputed)

| epoch | tiny_recall90 | overall_recall90 | mean_roi_area_fraction | mean_proposals_per_image | is_new_best | best_epoch_so_far | bad_epochs |
|---|---|---|---|---|---|---|---|
| 29 | 0.000000 | 0.000000 | 0.00000000 | 0.0000 | **True** | 29 | 0 |
| 30 | 0.000000 | 0.000000 | 0.00000000 | 0.0000 | False | 29 | 1 |
| 31 | **0.402778** | **0.427632** | **0.00391812** | **4.1456** | **True** | **31** | 0 |

Epochs 29–30 were zero-proposal, so R2B was *invariant* there. **Epoch 31 is the
first epoch where the R2B pixel-mask semantics actually changed the primary
metrics — and it became the new best checkpoint.**

---

## Classification

- **Rows 1–28:** `VALIDATED_ZERO_PROPOSAL_INVARIANT`
- **Rows ≥ 29:** `R2B_PIXEL_SEMANTICS_PROVISIONAL_NOT_ACCEPTED_FOR_PRIMARY_SELECTION`

Rows ≥ 29 are **not** invalid training epochs — their optimizer/model state may
still be salvageable. Only their **primary checkpoint-selection interpretation**
is pending supervisor decision. Nothing was deleted or rewritten.

---

## Evidence hashes (SHA-256)

| artifact | sha256 |
|---|---|
| `history.csv` | `27f99fb1b8760995373bfeb47bbc3f2a1f2ab81e08fbdb44abb3b6f479ab9440` |
| `latest.pt` | `806ce086dc0fa0163029e0fb335ad6ae9605ea6b550b12371a2cb0d5340eb575` |
| `best.pt` | `1a4863c96484871fda2a70b02678ac602245ceea4bc8c093160a407009ba8ecc` |
| runner | `15a0c2f0cf02916f96f60b7cf3d148fac4d931df11d5e119eb9c76f22a0c889b` |
| config | `922ff26916c1f7ebea0ea526fbaa6adbb9a7419f1f08b16d33ed5df049c4c8bf` |
| R2B JSON | `5574cd60a0bb69f392e818b96915fc522f4b706e9958d2d39a22911fe8424497` |
| training log | `420beb2544cccfa5863c34c7d9b8dac0de8c75e49abbe0d28928d2acada118a2` |

> **Disclosure — `best.pt` was overwritten.** The **authorized** resume
> legitimately replaced `best.pt` at epoch 31 under the frozen strict-improvement
> rule. The pre-stop epoch-27 `best.pt`
> (`d71aed3e084653bfc49acf9461cc2f0b3332c03b43026947a54393f89cebd04c`) **no longer
> exists on disk**. Its *metrics* survive in the immutable epoch-27 history row,
> but the epoch-27 *weights* are not recoverable. Reported, not hidden.

---

## Lock / process

| check | result |
|---|---|
| trainer process | **ABSENT** |
| waiters | **ABSENT** |
| second trainer | **ABSENT** |
| lock present | **YES (stale)** |
| lock owner pid | 23452 (dead) |
| lock deleted in this task | **NO** — recorded only, per instruction |

### Stop mechanism (full disclosure)

Graceful interruption **failed at every available level**:

1. `SIGINT` — not deliverable from Git Bash to a native Windows console process
2. `SIGTERM` — same limitation
3. `taskkill /PID 11396` (graceful) — **refused by Windows**: *"This process can
   only be terminated forcefully (with /F option)"*

Only then was `/F` used, which is the supervisor's stated precondition. Note the
MSYS PID (1210) differs from the Windows PID (11396); the first attempts targeted
the MSYS PID and therefore matched nothing.

---

## TEST / GRID

| counter | value |
|---|---|
| grid configurations evaluated | **0** |
| TEST content reads | **0** |

---

## Closure

**NO coverage-semantics patch. NO resume. NO restart. NO threshold change.
NO loss change. NO 20-grid. NO downstream analysis. TEST untouched.**

NEXT ACTION: `WAIT_FOR_SUPERVISOR_COVERAGE_SEMANTICS_DECISION`
