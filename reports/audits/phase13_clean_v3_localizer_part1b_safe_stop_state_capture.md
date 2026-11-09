# PHASE-13 PART-1B — EMERGENCY SAFE-STOP STATE CAPTURE

- **experiment_id:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_clean_v3`
- **status:** **PASS**
- **stop semantics:** SIGTERM (graceful), exit code 143 — not SIGKILL
- **trainer pid:** 1931
- **relaunch / resume performed:** NO
- **code modified during stop:** NO

---

## 1. Last fully completed epoch

| item | value |
|---|---|
| final completed history epoch | **28** |
| history rows | **28** |
| epochs contiguous `1..N` | **YES (1..28)** |
| `latest.pt` epoch | **28** |
| `best.pt` epoch | **27** |

Epoch 29 was mid-flight when the process was terminated. It produced **no completed
history row** and is therefore **not scientific evidence**; it was not reconstructed.

`best.pt` legitimately lags `latest.pt` by one epoch: epoch 28 was **not** a new best
(`is_new_best=False`, `bad_epochs=1`), so `best.pt` still holds epoch 27.

---

## 2. Lock / process state

| check | result |
|---|---|
| trainer process running | **NO** |
| second trainer exists | **NO** |
| background waiters running | **NO** |
| lock present | **YES** |
| lock stale (pid 29652 dead) | **YES** |
| lock released | **NO** |

> **Residual item.** The lock file
> `experiments/<EXP>/.experiment.lock` remains on disk because SIGTERM does not execute
> Python's `finally:` block, so the in-run `release_lock()` never fired. It is **stale**
> (pid 29652 is not alive), harmless to data, and was **preserved as evidence, not deleted**.
>
> **Consequence:** `acquire_lock(..., recover_stale=False)` will **refuse to start** while
> this file exists, so it must be cleared before any future run of this experiment ID.

---

## 3. Evidence hashes (SHA-256)

| artifact | sha256 |
|---|---|
| `history.csv` | `70fca5b796d112b1322ae945570ec94a271f3502af0bac61664954a4b0d13031` |
| `latest.pt` | `7f6f0b2e0d6fe2d61743ec0e3f8d2cf5e986f5711442cdf3113932da59152407` |
| `best.pt` | `d71aed3e084653bfc49acf9461cc2f0b3332c03b43026947a54393f89cebd04c` |
| runner | `f9d8c0d4166b283f279a43102083ad2d898724385729ab30ab6a3723fc4744f0` |
| config | `922ff26916c1f7ebea0ea526fbaa6adbb9a7419f1f08b16d33ed5df049c4c8bf` |
| training log | `92a9bb910e2dc545f2ebe204f4dc79b37fcd8dfb0a6bdbb9ecc62cdd09a26170` |

The runner and config hashes are **byte-identical to the launch-time training-start audit**,
proving neither was modified during the run or during the stop.

No separate stderr log exists — stderr was merged into the stdout log via `2>&1`.

No files were altered after hashing.

---

## 4. Side-effect counts

| counter | observed | expected |
|---|---|---|
| completed epochs | 28 | — |
| optimizer steps (physically recorded) | **5404** | — |
| grid configurations evaluated | **0** | 0 ✅ |
| TEST content reads | **0** | 0 ✅ |

Cross-check: `28 epochs × 193 train batches = 5404`, exactly matching the persisted
`global_step` in `latest.pt`. This confirms only whole epochs were committed, with no
partial-epoch optimizer steps persisted.

---

## 5. Carried-forward scientific defect (NOT repaired here)

`DEGENERATE_ALL_NEGATIVE_HEATMAP` — the model converged to a spatially uniform,
sub-threshold logit field (`head.bias ≈ −2.2245` → `sigmoid ≈ 0.09757 < 0.10` threshold),
so **zero proposals** were ever generated and `recall90` was pinned to 0 for all 28 epochs.

- `best.pt` is **UNTRUSTWORTHY** for downstream analysis (`DO_NOT_USE_FOR_DOWNSTREAM_ANALYSIS`).
- No repair was performed. No parameter was retuned.
- The manifest-provenance amendment remains **intact**.

Full diagnosis: `reports/audits/phase13_clean_v3_localizer_training_abort_incident.{json,md}`

---

## 6. Closure

**NO CODE REPAIR. NO RESUME. NO NEW EXPERIMENT ID. NO PROPOSAL ANALYSIS.
NO PREDICTED-REGION SEGMENTATION. TEST NOT TOUCHED.**

NEXT ACTION: `WAIT_FOR_SUPERVISOR_METRIC_SEMANTICS_REPAIR`
