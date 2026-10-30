# Automation 21cfca4f — Phase-20B keep-alive (hourly)

Purpose: keep the Phase-20B four-model conventional benchmark sequence alive.
Models: unet, attention_unet, deeplabv3plus, transformer_mit_unet.
Driver: `scripts/training/run_phase20b_sequence.py` → `logs/phase20b_sequence.log`.
Rule: relaunch the driver ONLY if >=1 model lacks a completed closure.json
(stop_reason in {EARLY_STOPPING_PATIENCE, MAX_EPOCHS}) AND no Phase-20B run lock is active.
Never start a second independent run; never delete/reset a checkpoint; never retrain UNet++ (20A).

**STATUS (2026-09-28T15:05): ALL TRAINING COMPLETE + POST-TRAINING FREEZE CHAIN COMPLETE.**
There is no model left to train and no freeze step left to run. Future runs of this automation
must simply VERIFY the five closures + freeze artifact exist and then IDLE/report — do NOT
relaunch the driver, do NOT start Phase 21.

## Execution log

### 2026-09-26T16:27 (GMT+6) — first recorded run
- State: `unet` IN PROGRESS, epoch 8, best macro-domain VAL Dice 0.673906 (best_epoch 8, bad=0).
- Lock: ACTIVE — `phase20b_shared_unet_fourdomain_seed42_clean_v3`, PID 39952 (host DESKTOP-A568FKR).
- Driver PID 37300 alive, queued behind the lock (started 15:26).
- closure.json: none for any of the four models → all four still incomplete.
- Action: NO relaunch (a run was active). No changes to protocol/bindings/checkpoints.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run should: verify lock/driver aliveness, and if driver died with models remaining, relaunch driver.

### 2026-09-26T17:29 (GMT+6)
- State: `unet` IN PROGRESS, epoch 17, best macro-domain VAL Dice 0.720539 (best_epoch 17, bad=0).
- Lock: ACTIVE (`unet`, PID 39952); driver PID 37300 alive and queued; fresh dataloader workers seen.
- closure.json: still none for any of the four models → all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Housekeeping: consolidated workspace MEMORY.md 12,352 → 6,721 chars.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T18:31 (GMT+6)
- State: `unet` IN PROGRESS, epoch 24, best macro-domain VAL Dice 0.736883 (best_epoch 21, bad=3).
- Lock: ACTIVE (`unet`, PID 39952); driver PID 37300 alive and queued; fresh dataloader workers (18:24).
- closure.json: still none for any of the four models → all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T20:34 (GMT+6)
- State: `unet` IN PROGRESS, epoch 38, best macro-domain VAL Dice 0.770078 (best_epoch 37, bad=1).
- Lock: ACTIVE (`unet`, PID 39952); driver PID 37300 alive and queued; dataloader workers ~20:27.
- closure.json: still none for any of the four models → all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T19:32 (GMT+6)
- State: `unet` IN PROGRESS, epoch 31, best macro-domain VAL Dice 0.764877 (best_epoch 30, bad=1).
- Lock: ACTIVE (`unet`, PID 39952); driver PID 37300 alive and queued; dataloader worker spawned 19:32.
- closure.json: still none for any of the four models → all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T22:36 (GMT+6)
- State: `unet` IN PROGRESS, epoch 055, best macro-domain VAL Dice 0.783542 (best_epoch 55, bad=0, new_best).
- Lock: ACTIVE (`unet`, PID 39952); driver PID 37300 alive and queued; dataloader workers present (epoch line 22:34).
- closure.json: still none for any of the four models → all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T21:35 (GMT+6)
- State: `unet` IN PROGRESS, epoch 46, best macro-domain VAL Dice 0.776211 (best_epoch 44, bad=2).
- Lock: ACTIVE (`unet`, PID 39952, owner alive); driver PID 37300 alive and queued; latest epoch line 21:31.
- closure.json: still none for any of the four models → all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T22:36 (GMT+6)
- State: `unet` IN PROGRESS, epoch 055, best macro-domain VAL Dice 0.783542 (best_epoch 55, bad=0, new_best).
- Lock: ACTIVE (`unet`, PID 39952); driver PID 37300 alive and queued; dataloader workers present (epoch line 22:34).
- closure.json: still none for any of the four models -> all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-26T23:37 (GMT+6)
- State: `unet` IN PROGRESS, epoch 064, best macro-domain VAL Dice 0.786838 (best_epoch 64, bad=0, new_best).
- Lock: ACTIVE (`unet`, PID 39952, owner alive, 638 MB); driver PID 37300 alive and queued; epoch line 23:37.
- closure.json: still none for any of the four models -> all four incomplete.
- Action: NO relaunch (run active + driver alive). No protocol/binding/checkpoint changes.
- Remaining after unet: attention_unet, deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; if driver dead with models remaining, relaunch driver.

### 2026-09-27T02:09 (GMT+6) — RELAUNCH after death
- Finding: run AND driver had both died (~00:15). Last epoch 069; lock PID 39952 stale/dead; no python procs.
- closure.json: none for any of the four models -> all four incomplete.
- Action: RELAUNCHED driver in background (task LuIVjW). It reclaimed stale lock (new PID 23196,
  recovered_stale_lock=True) and resumed the SAME `unet` logical run via --resume.
- State now: `unet` IN PROGRESS, resumed epoch 69 -> next 70, best macro-domain VAL Dice 0.787293
  (best_epoch 66, bad=3/15), history_rows=69.
- Remaining: unet, attention_unet, deeplabv3plus, transformer_mit_unet.
- No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Note: stale lock does NOT block the trainer (acquire_lock only raises when active=True).

### 2026-09-27T02:22 (GMT+6) — second relaunch, VERIFIED live
- Finding: the 02:08 relaunch had itself died within ~4 min (background task gone, no python procs,
  lock PID 23196 stale/dead, run log stopped at RUN START 02:08:41, latest.pt unchanged at 00:15).
- closure.json: still none for all four -> RELAUNCHED driver again (task XcZ72l).
- It reclaimed the stale lock (new PID 21960, recovered_stale_lock=True) and resumed the SAME `unet` run.
- VERIFIED: epoch 070 logged 02:21:47 -> macro=0.783421, best_ep=66 bad=4, 557.6s; latest.pt rewritten
  02:21; history_rows=71. Lock ACTIVE, owner alive.
- Remaining: unet, attention_unet, deeplabv3plus, transformer_mit_unet.
- Lesson: do not trust `RUN START` as liveness; require a new EPOCH line before reporting progress.

### 2026-09-27T07:25 (GMT+6) — checked after user asked "why 2 running"
- `unet` COMPLETE & closed: best_epoch=74 best_macro=0.787832506974712, final_epoch=89,
  stop=EARLY_STOPPING_PATIENCE, resume_count=1, duplicate_runs=0, test_reads 0.
- Driver advanced automatically: `attention_unet` STARTED 04:28:04 (resume=False).
- `attention_unet` IN PROGRESS: epoch 023 @07:16:44, macro=0.744335, best_ep=21 bad=2; lock ACTIVE (PID 15292).
- "Two running" cards = ONE real job. Chain: cmd 16736 -> driver 24572 -> trainer 8728 -> worker 15292
  -> 4 dataloaders. The 02:12 driver already exited at 04:28 (finished unet); its background-task record
  was never reaped, so the client still lists it as Running. Not a duplicate run; no lock contention.
- Remaining: attention_unet, deeplabv3plus, transformer_mit_unet.
- Action: NO relaunch (attention_unet actively training). No protocol/binding/checkpoint changes.

### 2026-09-27T07:56 (GMT+6) — progress + full-process ETA
- Added read-only reporter `scripts/training/phase20b_progress_eta.py` (history.csv/closure.json only).
- Observed rate ~450 s/epoch (unet mean 451; attention_unet mean 446).
- `attention_unet` 27 ep done, best_ep 26, macro 0.755976.
- Projected remaining (attn + deeplabv3plus + transformer_mit_unet): ~24.8-32.3 h.
- Projected full-sequence completion: **Mon 2026-09-28 ~08:41 .. 16:11 (GMT+6)**.
- Next runs: prefer this reporter over log-tail guessing; still verify the driver is alive.

### 2026-09-27T10:08 (GMT+6) — ETA refresh
- `attention_unet` 43 ep done, best_ep 32, bad 11/15, macro 0.774943; lock ACTIVE (owner alive). Healthy.
- Rate: attn last-10 mean 495 s/epoch (used 490 conservative); unet overall 451 s.
- Remaining 3 models: best ~16.9 h (Mon ~03:00), typical ~24.8-30.5 h (Mon ~10:54-16:37),
  worst ~32.0 h (Mon ~18:07). Headline: ~1 to 1.3 days, done sometime Mon 28 Sep.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-27T14:38 (GMT+6) — 2 of 4 complete
- `attention_unet` COMPLETE 14:29:04 after 10.02 h: 79 ep, best_ep 64, macro 0.789039, EARLY_STOPPING_PATIENCE.
- `deeplabv3plus` IN PROGRESS since 14:29:04: epoch 001, macro 0.589998, 40,347,041 params; lock ACTIVE (PID 34340).
- Driver chain intact: 16736 -> 24572 (driver) -> 15028 (trainer) -> 34340 (worker) -> dataloaders.
- `transformer_mit_unet` NOT_STARTED. Projected remaining 18.8-23.8 h -> completion Mon 28 Sep ~09:24-14:27.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-27T14:41 (GMT+6) — class/subclass + completed-model comparison
- Wrote `reports/tables/phase20b_model_comparison_in_progress.csv` and
  `reports/tables/phase20_model_comparison.md` (VAL-only, no TEST reads).
- 3 of 5 models complete. Ranking by macro-domain VAL Dice at own best epoch:
  U-Net++ 0.792007 > Attention U-Net 0.789039 > U-Net 0.787833 (spread 0.42 pp = tie).
  KUB is the only real discriminator (UNet++/UNet ~0.721 vs Attention 0.696).
- Classes: UNet / AttentionUNet / DeepLabV3Plus (40.3 M, random-init) /
  TransformerMiTUNet (16.3 M, LOCAL_RANDOM_INIT, not official MiT-B1).
- 20A closure.json lacks class fields (pre-20B schema) — read class from src/models/unetpp.py.

### 2026-09-27T16:12 (GMT+6) — update
- `deeplabv3plus` IN PROGRESS epoch 014, macro 0.779714 (best_ep 12), ~405 s/epoch; lock ACTIVE (PID 34340).
  Per-domain at best: ISIC 0.8678 / BUSI 0.8535 / KVASIR 0.7842 / KUB 0.6134 — strongest ISIC/BUSI/KVASIR
  of any model so far, but KUB is the weakest of all five so far.
- `transformer_mit_unet` NOT_STARTED. Projected remaining 17.0-22.0 h -> completion Mon 28 Sep ~09:14-14:15.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-27T20:14 (GMT+6) — deeplabv3plus now leads
- `deeplabv3plus` IN PROGRESS epoch 046, best_ep 39, **best macro 0.823777**, bad=7/15, ~485 s/epoch.
  Clearly ahead of all three U-Net variants (~+0.032 over U-Net++ 0.792007).
- Per-domain at best (ep 39): ISIC 0.8864 / BUSI 0.8563 / KVASIR 0.8144 / KUB 0.7380 — best on EVERY
  domain, incl. KUB (which had looked weakest at ep 12: 0.6134 -> 0.7380).
- `transformer_mit_unet` NOT_STARTED. Projected remaining 13.0-18.0 h -> completion Mon 28 Sep ~09:15-14:15.

### 2026-09-27T21:10 (GMT+6) — new best for deeplabv3plus
- `deeplabv3plus` IN PROGRESS epoch 054, **new best_ep 52, macro 0.827018** (recovered past bad=12).
  Per-domain at best: ISIC 0.8883 / BUSI 0.8591 / KVASIR 0.8193 / KUB 0.7414 — best on all four.
  Gap over U-Net++ = +0.0350 (+3.50 pp). bad=2/15, patience would trip ~ep 67.
- `transformer_mit_unet` NOT_STARTED. Projected remaining 12.0-17.0 h -> completion Mon 28 Sep ~09:10-14:10.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-27T23:09 (GMT+6) — another new best
- `deeplabv3plus` IN PROGRESS epoch 069, **new best_ep 57, macro 0.827653**. bad=12/15 -> patience trips
  ~ep 72 unless a new best lands. Per-domain at best: ISIC 0.8868 / BUSI 0.8592 / KVASIR 0.8204 / KUB 0.7405.
  Gap over U-Net++ = +0.0356 (+3.56 pp).
- `transformer_mit_unet` NOT_STARTED. Projected remaining 11.3-15.2 h -> completion Mon 28 Sep ~10:28-14:22.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-28T05:20 (GMT+6) — 3 of 4 complete; final model training
- `deeplabv3plus` COMPLETE 09-27 23:30:02 after 9.02 h: 72 ep, best_ep 57, macro 0.827653
  (benchmark leader, +0.0356 over U-Net++). resume 0, dup 0, test_reads 0.
- `transformer_mit_unet` IN PROGRESS since 23:30:02 (16,347,777 p): epoch 042, macro 0.808595,
  best_ep 42, bad=0, ~487 s/epoch. 2nd best overall. KUB weak spot 0.6946 vs deeplabv3plus 0.7405.
- Lock ACTIVE (PID 36592, owner alive). Projected remaining 4.2-6.7 h -> completion ~09:31-12:04.
- Next run: watch for transformer closure; then the five-model freeze + replay + bootstrap remain.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-28T08:19 (GMT+6) — transformer still improving
- `transformer_mit_unet` IN PROGRESS epoch 065, **new best_ep 65, macro 0.818400** (late recovery
  past bad=12, like deeplabv3plus). Per-domain at best: ISIC 0.8897 / BUSI 0.8584 / KVASIR 0.8078 / KUB 0.7177.
- 2nd overall. Lock ACTIVE (PID 36592). Projected remaining 1.9-3.8 h -> completion ~10:13-12:08.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-28T09:31 (GMT+6) — transformer closing on leader
- `transformer_mit_unet` IN PROGRESS epoch 074, best_ep 74, **macro 0.822381**, bad=0 (still improving).
  Per-domain: ISIC 0.8871 / BUSI 0.8640 / KVASIR 0.8133 / KUB 0.7252. KUB up from 0.6946.
- **Gap to leader deeplabv3plus (0.827653) only 0.005272 (~0.53 pp)** — top-two race is tight.
- Refreshed `reports/tables/phase20b_model_comparison_in_progress.csv`.
- Projected remaining 1.9-2.7 h -> completion ~11:26-12:12.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-28T10:41 (GMT+6) — transformer plateauing, near close
- `transformer_mit_unet` IN PROGRESS epoch 083/084, best_ep 74, macro 0.822381 unchanged, bad=10/15.
  Plateau ~0.820-0.822. If no new best -> patience trips at **epoch 89** (~40-45 min out).
- Per-epoch time improved to ~400-434 s. Chain intact (driver 24572 -> trainer 30856 -> worker 36592).
- Projected remaining ~1.5-1.9 h -> completion ~12:12-12:35.
- No relaunch needed; no protocol/binding/checkpoint changes.

### 2026-09-28T11:16 (GMT+6) — SEQUENCE COMPLETE (final entry for this automation's purpose)
- Driver (task XcZ72l) exited 11:15:40 with `PHASE 20B SEQUENCE COMPLETE: all requested models
  naturally terminated`. `transformer_mit_unet` closed in 11.76 h (89 ep, best_ep 74, 0.822381).
- All four 20B models closed; all locks released; zero rc=2 governance aborts over 33h 03m.
- FINAL: DeepLabV3+ 0.827653 > Transformer/MiT 0.822381 > UNet++ 0.792007 > Attention U-Net 0.789039
  > U-Net 0.787833. Top-2 margin 0.005272 = provisional pending paired bootstrap.
- Deliverables: `reports/tables/phase20b_five_model_comparison.csv`,
  `reports/tables/phase20_five_model_final_report.md`.
- **No further keep-alive relaunch is needed: there is no model left to train.** Future runs of this
  automation should verify all five closures exist and then IDLE/report — do NOT relaunch the driver.
- Remaining work is the POST-TRAINING freeze chain (replay, canonical VAL pass, bootstrap CI,
  confusion matrices, 808-row table, KUB subgroups, 64 gallery cases, notebooks, paired bootstrap,
  freeze JSON + terminal marker). Phase 21 still NOT STARTED. No TEST reads; no protocol changes.

### 2026-09-27T04:11 (GMT+6) — VERIFIED healthy, no relaunch
- State: `unet` IN PROGRESS, epoch 086 (04:07:51, 389.5s), best macro-domain VAL Dice 0.787833
  (best_ep 74, bad=12/15); latest epoch macro 0.785546.
- Liveness: lock ACTIVE (`unet`, PID 21960, recovered_stale_lock=True); driver PID 16736 alive since
  02:12:18 with trainer PID 21716; 4 dataloader workers spawned 04:07-04:08 → genuinely progressing.
- closure.json: none for any of the four models -> all four incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: unet (in progress; bad=12/15 → early stop imminent), attention_unet, deeplabv3plus,
  transformer_mit_unet.

### 2026-09-27T05:12 (GMT+6) — `unet` CLOSED, attention_unet live, no relaunch
- MILESTONE: `unet` closure.json DONE — stop_reason EARLY_STOPPING_PATIENCE, best_epoch 74,
  best_macro 0.787833, final epoch 89, resume_count=1, wall 2.26h (driver DONE line 04:28:04).
- Current: `attention_unet` IN PROGRESS, epoch 006 (05:08:46, 395.4s), best macro-domain VAL Dice
  0.650817 (best_ep 5, bad=1/15); latest epoch macro 0.629829 [ISIC .7368/BUSI .7114/KVASIR .6021/KUB .4691].
  params=7,851,285; started 04:28:09 (fresh run, resume=False).
- Liveness: lock ACTIVE (`attention_unet`, PID 15292, owner_alive=true, payload started 22:28 UTC);
  driver PID 16736 alive since 02:12:18 with trainer PID 8728 (04:28:04); history.csv written 05:08:46.
- closure.json: unet DONE; attention_unet / deeplabv3plus / transformer_mit_unet absent → 3 incomplete.
- Action: NO relaunch (active run + live driver). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T03:10 (GMT+6) — VERIFIED healthy, no relaunch
- State: `unet` IN PROGRESS, epoch 077 (03:08:24, 388.5s), best macro-domain VAL Dice 0.787833
  (best_ep 74, bad=3/15); latest epoch macro 0.784676.
- Liveness: lock ACTIVE (`unet`, PID 21960); driver PID 16736 alive since 02:12:23 with trainer
  PID 21716; 4 dataloader workers spawned 03:08:24+ → genuinely progressing.
- closure.json: none for any of the four models -> all four incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: unet (in progress), attention_unet, deeplabv3plus, transformer_mit_unet.

### 2026-09-27T06:14 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 015 (06:10:34, 504.0s), best macro-domain VAL Dice
  0.722075 (best_ep 15, bad=0, new_best); latest epoch macro 0.722075
  [ISIC 0.8127/BUSI 0.8269/KVASIR 0.6854/KUB 0.5633]; history.csv 15 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292, owner_alive=true, stale=false, age 6,365s);
  driver PID 16736 alive since 02:12:18 with trainer PID 8728 (04:28:04); 4 dataloader workers
  spawned 06:10; best.pt/latest.pt rewritten 06:10:34 → genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent → 3 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T08:16 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 030 (08:14:41, 504.0s), best macro-domain VAL Dice
  0.768631 (best_ep 30, bad=0, new_best=True); latest epoch macro 0.768631
  [ISIC .8431/BUSI .8066/KVASIR .7131/KUB .7117]; history.csv 30 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292); driver PID 16736 alive since 02:12:18 with
  trainer PID 8728 (04:28:04); 4 dataloader workers spawned 08:14 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T09:17 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 037 (09:13:18, 518.9s), best macro-domain VAL Dice
  0.774943 (best_ep 32, bad=5/15); latest epoch macro 0.764387
  [ISIC .8410/BUSI .8177/KVASIR .7084/KUB .6904]; history.csv 37 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292); driver PID 16736 alive since 02:12:18 with
  trainer PID 8728 (04:28:04); run log mtime 09:13 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- ETA (read-only reporter `scripts/training/phase20b_progress_eta.py`, rate 454 s/ep): full sequence
  done Mon 2026-09-28 ~09:01-16:36 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T10:19 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 045 (10:17:07, 407.4 s), best macro-domain VAL Dice
  0.774943 (best_ep 32, bad=13/15); latest epoch macro 0.769965
  [ISIC .8535/BUSI .7803/KVASIR .7291/KUB .7170]; history.csv 45 data rows.
- Liveness: lock ACTIVE (`attention_unet`); driver PID 16736 alive since 02:12:18 with trainer
  PID 8728 (04:28:04); 4 dataloader workers spawned 10:17 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- ETA (reporter, 456 s/ep): attn 3.8-6.3 h; full sequence done Mon 2026-09-28 ~09:07-16:42 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T11:20 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 054 (11:17:25, 405.5 s), best macro-domain VAL Dice
  0.784813 (best_ep 50, bad 4/15); latest epoch macro 0.771322
  [ISIC .8501/BUSI .7871/KVASIR .7433/KUB .7048]; history.csv 54 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292, owner_alive=true, stale=false, age 24,737 s);
  driver PID 16736 alive since 02:12:18 with trainer PID 8728 (04:28:04); 4 dataloader workers
  spawned 11:17 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- ETA (reporter, 452 s/ep): attn 2.6-5.2 h; full sequence done Mon 2026-09-28 ~08:50-16:22 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T12:21 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 062 (12:13:57, 506.8 s), best macro-domain VAL Dice
  0.788071 (best_ep 55, bad 7/15); latest epoch macro 0.775435
  [ISIC .8501/BUSI .7879/KVASIR .7479/KUB .7159]; history.csv 62 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292, owner_alive=true, stale=false);
  driver PID 16736 alive since 02:12:18 -> trainer PID 8728 (04:28:04) -> 2 dataloader workers
  spawned 12:21:24/12:21:30 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete
  (deeplabv3plus & transformer_mit_unet dirs not created yet).
- ETA (reporter, 451 s/ep): attn 1.9-4.1 h; full sequence done Mon 2026-09-28 09:01-16:17 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T13:23 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 070 (13:18:02, 476.0 s), best macro-domain VAL Dice
  0.789039 (best_ep 64, bad 6/15); latest epoch macro 0.773649
  [ISIC .8598/BUSI .8221/KVASIR .7632/KUB .6495]; history.csv 70 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292, owner_alive=true, stale=false, age 31,817 s);
  full chain alive — driver 16736 (02:12:18) -> trainer 8728 (04:28:04) -> worker 15292 (666 MB)
  -> 4 dataloader workers spawned 13:18 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- ETA (reporter, 452 s/ep): attn 1.9-3.1 h; full sequence done Mon 2026-09-28 10:07-16:24 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T14:24 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 078 (14:21:33, 484.3 s), best macro-domain VAL Dice
  0.789039 (best_ep 64, bad 14/15 — one epoch from early stop); latest epoch macro 0.781440
  [ISIC .8556/BUSI .8190/KVASIR .7492/KUB .7020]; history.csv 78 data rows.
- Liveness: lock ACTIVE (`attention_unet`, PID 15292, owner_alive=true, stale=false); full chain
  alive — driver 16736 (02:12:18) -> trainer 8728 (04:28:04) -> worker 15292 (636 MB) -> 4
  dataloader workers spawned 14:21 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833, final 89);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress, early stop imminent), deeplabv3plus, transformer_mit_unet.
- Next run: expect attention_unet CLOSED and deeplabv3plus started; re-verify lock/driver; only
  relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T07:15 (GMT+6) — VERIFIED healthy, no relaunch
- State: `attention_unet` IN PROGRESS, epoch 022 (07:08:24, 475.0s), best macro-domain VAL Dice
  0.755 (best_ep 21, bad=1); latest epoch macro 0.737195 [ISIC .8280/BUSI .7949/KVASIR .7127/KUB .6131].
- Liveness: lock ACTIVE (`attention_unet`, PID 15292); driver PID 16736 alive since 02:12:18 with
  trainer PID 8728 (04:28:04); epoch line 07:08 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, best_macro 0.787833);
  attention_unet / deeplabv3plus / transformer_mit_unet absent -> 3 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: attention_unet (in progress), deeplabv3plus, transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T15:25 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 007 (15:19:30, 404.5 s), best macro-domain VAL Dice 0.749738
  (best_ep 7, bad 0/15); latest epoch macro 0.749738 [ISIC .8719/BUSI .8214/KVASIR .7596/KUB .5461];
  40,347,041 params; history.csv 7 data rows.
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=True, stale=False, age 3,382 s);
  full chain alive — driver 16736/24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340 (1.94 GB)
  -> 4 dataloader workers spawned 15:19 -> genuinely progressing.
- closure.json: `unet` DONE; `attention_unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 64, macro 0.789039,
  final 79, 10.02 h); deeplabv3plus / transformer_mit_unet absent -> 2 of 4 incomplete.
- ETA (reporter, 453 s/ep): deeplabv3plus 8.5-11.1 h; transformer_mit_unet 9.4-11.9 h; full sequence
  done Mon 2026-09-28 ~09:24-14:25 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: deeplabv3plus (in progress), transformer_mit_unet.
- Next run: re-verify lock/driver; only relaunch if driver dead with <4 closure.json complete.

### 2026-09-27T16:26 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 016 (16:21:17, 414.8 s), best macro-domain VAL Dice 0.790304
  (best_ep 15, bad 1/15); latest epoch macro 0.787047 [ISIC .8582/BUSI .8515/KVASIR .7746/KUB .6639];
  history.csv 16 data rows.
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=true, stale=false); full chain alive —
  driver 16736/24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340 (1.87 GB) -> 4 dataloader
  workers spawned 16:21 -> genuinely progressing.
- closure.json: `unet` DONE; `attention_unet` DONE; deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- ETA (reporter, 451 s/ep): deeplabv3plus 7.4-9.9 h; transformer_mit_unet 9.4-11.9 h; full sequence
### 2026-09-27T17:28 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 025 (17:22:40, 392.9 s), best macro-domain VAL Dice 0.813594
  (best_ep 24, bad 1/15); latest epoch macro 0.809240 [ISIC .8867/BUSI .8578/KVASIR .7970/KUB .7128];
  history.csv 25 data rows.
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=true, stale=false,
  recovered_stale_lock=false, age 10,741 s); full chain alive — driver 24572 (02:12:18) -> trainer 15028
  (14:29:04) -> worker 34340 (1.87 GB) -> 4 dataloader workers spawned 17:22 -> genuinely progressing.
- closure.json: `unet` DONE; `attention_unet` DONE; deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- ETA (reporter, 449 s/ep): deeplabv3plus 6.2-8.7 h; transformer_mit_unet 9.3-11.8 h; full sequence
  done Mon 2026-09-28 ~09:02-14:01 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: deeplabv3plus (in progress), transformer_mit_unet.
- Note: `deeplabv3plus` best macro 0.813594 at epoch 24 already exceeds ALL completed models
  (UNet++ 0.792007 / Attn-U-Net 0.789039 / U-Net 0.787833), driven by ISIC/BUSI/KVASIR; KUB 0.7128
  still trailing UNet++ 0.720662.

### 2026-09-27T18:29 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 034 (18:29:26, 490.7 s), best macro-domain VAL Dice 0.817424
  (best_ep 33, bad 1/15); latest epoch macro 0.809824 [ISIC .8829/BUSI .8510/KVASIR .8089/KUB .7269].
- Liveness: lock ACTIVE (`deeplabv3plus`, owner_alive=true, stale=false, age 14,430 s); full chain alive —
  driver 16736 -> 24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340 (1.87 GB) -> 2 dataloader
  workers spawned 18:21-18:29 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, 0.787833); `attention_unet` DONE
  (EARLY_STOPPING_PATIENCE, best_ep 64, 0.789039); deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- ETA (reporter, 448 s/ep): deeplabv3plus 5.1-7.6 h; transformer_mit_unet 9.3-11.8 h; full sequence
  done Mon 2026-09-28 ~08:56-13:55 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: deeplabv3plus (in progress), transformer_mit_unet.
- Note: deeplabv3plus best macro 0.817424 now exceeds ALL completed models; its KUB 0.7269 also now
  leads UNet++ (0.720662).

### 2026-09-27T19:30 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 041 (19:26:41, 492.1 s), best macro-domain VAL Dice 0.823746
  (best_ep 37, bad 2/15); latest epoch macro 0.817343 [ISIC .8872/BUSI .8409/KVASIR .8076/KUB .7337];
  history.csv 41 data rows.
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=true, stale=false, age 18,100 s);
  full chain alive — driver 16736 -> 24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340 (1.87 GB)
  -> 4 dataloader workers -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, 0.787833); `attention_unet` DONE
  (EARLY_STOPPING_PATIENCE, best_ep 64, 0.789039); deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: deeplabv3plus (in progress), transformer_mit_unet.
- Note: deeplabv3plus best macro 0.823746 comfortably exceeds ALL completed models; KUB 0.738 also leads.

### 2026-09-27T20:32 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 049 (20:28:54, 406.1 s), best macro-domain VAL Dice 0.823777
  (best_ep 39, bad 10/15); latest epoch macro 0.820687 [ISIC .8881/BUSI .8545/KVASIR .8043/KUB .7359].
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=true); full chain alive — driver 16736
  -> 24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340 (1.87 GB) -> 4 dataloader workers
  (PIDs 34276/33048/26312/20796) -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, 0.787833); `attention_unet` DONE
  (EARLY_STOPPING_PATIENCE, best_ep 64, 0.789039); deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- ETA (reporter, 450 s/ep): deeplabv3plus 3.3-5.8 h; transformer_mit_unet 9.4-11.9 h; full sequence
  done Mon 2026-09-28 ~09:10-14:10 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Note: deeplabv3plus best macro 0.823777 leads all four U-Net variants; bad=10/15 (early stop ~epoch 54).
- Remaining: deeplabv3plus (in progress), transformer_mit_unet.

### 2026-09-27T21:33 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 057 (21:29:15, 493.6 s), best macro-domain VAL Dice 0.827653
  (best_ep 57, bad 0/15, NEW BEST); latest epoch [ISIC .8853/BUSI .8669/KVASIR .8197/KUB .7387];
  history.csv 57 data rows.
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=true, recovered_stale_lock=false);
  full chain alive — driver 16736 -> 24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340 (776 MB)
  -> 4 dataloader workers (PIDs 22256/35844/35644/36660) -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, 0.787833); `attention_unet` DONE
  (EARLY_STOPPING_PATIENCE, best_ep 64, 0.789039); deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Note: deeplabv3plus 0.827653 is the best of all five models; +0.0356 over U-Net++ 0.792007.
- Remaining: deeplabv3plus (in progress), transformer_mit_unet (not started).

### 2026-09-27T22:34 (GMT+6) — VERIFIED healthy, no relaunch
- State: `deeplabv3plus` IN PROGRESS, epoch 064 (22:26:41, 501.8 s), best macro-domain VAL Dice 0.827653
  (best_ep 57, bad 7/15); latest epoch macro 0.825208 [ISIC .8893/BUSI .8638/KVASIR .8132/KUB .7345];
  history.csv 64 data rows.
- Liveness: lock ACTIVE (`deeplabv3plus`, PID 34340, owner_alive=true, stale=false, age 29,125 s);
  full chain alive — driver 16736 -> 24572 (02:12:18) -> trainer 15028 (14:29:04) -> worker 34340
  -> 2 dataloader workers spawned 22:34:13/22:34:18 -> genuinely progressing.
- closure.json: `unet` DONE (EARLY_STOPPING_PATIENCE, best_ep 74, 0.787833); `attention_unet` DONE
  (EARLY_STOPPING_PATIENCE, best_ep 64, 0.789039); deeplabv3plus / transformer_mit_unet absent
  -> 2 of 4 incomplete.
- ETA: deeplabv3plus ~1-2 h (early stop expected ~ep 72); transformer_mit_unet 9.4-11.9 h;
  full sequence done Mon 2026-09-28 ~09:10-14:10 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: deeplabv3plus (in progress), transformer_mit_unet (not started).

### 2026-09-28T00:37 (GMT+6) — verified healthy, no relaunch
- State: `transformer_mit_unet` IN PROGRESS, epoch 008 (00:32:06, 500.5 s), best macro-domain VAL Dice
  0.735284 (best_ep 8, bad 0/15, new_best); per-domain [ISIC .8719/BUSI .8397/KVASIR .7056/KUB .5239];
  history.csv 9 rows; best.pt/latest.pt rewritten 00:32.
- Liveness: lock ACTIVE (PID 36592, owner_alive=true, stale=false, recovered_stale_lock=false);
  full chain alive — driver 16736/24572 (02:12:18) -> trainer 30856 (23:30:02) -> worker 36592 (1.7 GB)
  -> 4 dataloader workers spawned 00:32 -> genuinely progressing.
- closure.json: unet DONE / attention_unet DONE / deeplabv3plus DONE / transformer_mit_unet absent
  -> 1 of 4 incomplete.
- ETA (500 s/ep): transformer 9.4-11.9 h -> full sequence done Mon 2026-09-28 ~08:50-11:20 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: transformer_mit_unet (in progress, LAST).
- Next run: expect transformer epoch 9-12; verify driver alive; NO relaunch while lock active.

- `deeplabv3plus` CLOSED 23:30:02 after 9.02 h: 72 ep, best_ep 57, **macro 0.827653**,
  EARLY_STOPPING_PATIENCE. This is the best of all five models (+0.0356 over U-Net++ 0.792007).
- `transformer_mit_unet` STARTED 23:30:02 (fresh, resume=False) — last model of the sequence.
  At check time (23:36) no epoch line yet (first epoch ~450 s, expected ~23:37:40); dir had only
  `.experiment.lock`, but lock payload = ACTIVE, PID 36592, owner_alive=true, stale=false,
  recovered_stale_lock=false, and PID 36592 holds a CUDA context per nvidia-smi -> genuinely training.
- closure.json: unet DONE / attention_unet DONE / deeplabv3plus DONE / transformer_mit_unet absent
  -> 1 of 4 incomplete.
- Chain alive: driver 16736 alive since 02:12:18 -> trainer 15028 -> new worker 36592 (1.70 GB).
- ETA (reporter, 452 s/ep): transformer 9.4-11.9 h -> projected final 75-95 ep; full sequence done
  Mon 2026-09-28 ~09:01-11:32 (GMT+6).
- Action: NO relaunch (active run + live driver). No protocol/binding/checkpoint changes.
- Remaining: transformer_mit_unet (in progress, LAST).
- Next run: expect transformer epoch 1-2 logged; verify driver alive; NO relaunch while lock active.

### 2026-09-28T01:38 (GMT+6) — VERIFIED healthy, no relaunch
- State: `transformer_mit_unet` IN PROGRESS, epoch 015 (01:30:09, 509.3 s), best macro-domain VAL Dice
  0.759203 (best_ep 15, bad 0/15, new_best); per-domain [ISIC .8690/BUSI .8450/KVASIR .7522/KUB .5707];
  history.csv 16 rows.
- Liveness: lock ACTIVE (PID 36592, owner_alive=true, stale=false, age 7,707 s); chain alive —
  driver 24572 -> trainer 30856 -> worker 36592 (1.93 GB); epoch 015 logged 01:30 -> progressing.
- closure.json: unet / attention_unet / deeplabv3plus DONE; transformer_mit_unet absent -> 1 of 4 incomplete.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes.
- Remaining: transformer_mit_unet (in progress, LAST). ETA 8.4-9.9 h -> full sequence Mon 28 Sep ~10:05-11:35.
- Next run: re-verify lock/driver; relaunch driver ONLY if it died with transformer still incomplete.

### 2026-09-28T02:39 (GMT+6) — VERIFIED healthy, no relaunch
- State: `transformer_mit_unet` IN PROGRESS, epoch 023 (02:36:59, 505.8 s), best macro-domain VAL Dice
  0.777056 (best_ep 23, bad 0/15, new_best); per-domain [ISIC .8845/BUSI .8523/KVASIR .7539/KUB .6175];
  history.csv 24 rows.
- Liveness: lock ACTIVE (PID 36592, owner_alive=true, stale=false, recovered_stale_lock=false,
  started 2026-09-27T17:30:07 UTC); chain alive — driver 24572 -> trainer 30856 (23:30:03) -> worker 36592
  (23:30:03) -> 4 dataloader workers spawned 02:37 -> genuinely progressing.
- closure.json: unet (EARLY_STOPPING_PATIENCE, best_ep 74, 0.787833); attention_unet (EARLY_STOPPING_PATIENCE,
  best_ep 64, 0.789039); deeplabv3plus (EARLY_STOPPING_PATIENCE, best_ep 57, **0.827653**); transformer absent
  -> 1 of 4 incomplete.
- ETA (reporter, 455 s/ep): transformer 6.6-9.1 h -> full sequence done Mon 2026-09-28 ~09:14-11:46 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes; no TEST reads;
  Phase 21 not started.
- Remaining: transformer_mit_unet (in progress, LAST).
- Next run: re-verify lock/driver; relaunch driver ONLY if it died with transformer still incomplete.

### 2026-09-28T03:41 (GMT+6) — VERIFIED healthy, no relaunch
- State: `transformer_mit_unet` IN PROGRESS, epoch 030 (03:35:28, 494.8 s), best macro-domain VAL Dice
  0.800879 (best_ep 30, bad 0/15, new_best); per-domain [ISIC .8911/BUSI .8530/KVASIR .7868/KUB .6727];
  history.csv 30 rows; best.pt/latest.pt rewritten 03:35:27-28.
- Liveness: lock ACTIVE (PID 36592, owner_alive=true, stale=false, age 15,056 s); chain alive —
  driver 16736/24572 -> trainer 30856 -> worker 36592 (1.93 GB) -> 4 dataloader workers -> progressing.
- closure.json: unet / attention_unet / deeplabv3plus DONE (all EARLY_STOPPING_PATIENCE);
  transformer_mit_unet absent -> 1 of 4 incomplete.
- ETA: transformer median ~75-95 ep -> remaining ~6-8 h; sequence finish Mon 2026-09-28 ~09:40-12:00 (GMT+6).
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes; no TEST reads;
  Phase 21 not started.
- Remaining: transformer_mit_unet (in progress, LAST).
- Next run: expect transformer epoch ~35-42; re-verify lock/driver; relaunch driver ONLY if it died with
  transformer still incomplete.

### 2026-09-28T04:42 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` is the LAST incomplete model.
- Lock: ONLY transformer active (PID 36592); unet/attention_unet/deeplabv3plus locks inactive.
- State: transformer IN PROGRESS epoch 038 (04:41:11, 477.0 s), NEW BEST best_ep 38 macro 0.806834
  (bad 0/15) [ISIC .8858/BUSI .8492/KVASIR .7887/KUB .7037]; history.csv 38 rows.
- Chain alive: driver 16736/24572 (02:12:18) -> trainer 30856 (23:30:02) -> worker 36592 -> 4 dataloaders
  spawned 04:41 -> genuinely progressing.
- Action: NO relaunch (run active AND driver alive). No protocol/binding/checkpoint changes; no TEST
  reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). ETA remaining ~5-7 h -> finish Mon 28 Sep ~09:40-12:00.

### 2026-09-28T05:44 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` LAST incomplete.
- Lock check: [(unet,False),(attention_unet,False),(deeplabv3plus,False),(transformer_mit_unet,True)]
  -> exactly ONE active run; NO relaunch (rule requires no active lock).
- State: transformer epoch 046 (05:42:09), best_ep 45, best macro 0.810610 (bad 1/15),
  ~464 s/ep; per-domain at best [ISIC .8909/BUSI .8609/KVASIR .8008/KUB .6898]; history.csv 46 rows.
- Chain alive: driver 16736/24572 (02:12:18) -> trainer 30856 (23:30:02) -> worker 36592 (lock owner,
  owner_alive, age 22,411 s) -> 4 dataloaders spawned 05:42 -> progressing.
- Action: NO relaunch. No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). ETA ~4-6 h -> finish Mon 28 Sep ~10:00-12:00 (GMT+6).
- Next run: expect transformer epoch ~50-60; re-verify lock/driver; relaunch ONLY if driver died while
  transformer still incomplete.

### 2026-09-28T06:45 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` LAST incomplete.
- Lock check: [(unet,False),(attention_unet,False),(deeplabv3plus,False),(transformer_mit_unet,True)]
  -> exactly ONE active run; NO relaunch (rule requires no active lock).
- State: transformer epoch 054 (06:44:37), best_ep 53, best macro 0.812390 (bad 1/15), 499.2 s/ep;
  per-domain @ep54 [ISIC .8899/BUSI .8610/KVASIR .8008/KUB .6756]; history.csv 54 rows.
- Chain alive: driver 24572/16736 -> trainer 30856 -> worker 36592 (lock owner, 1.93 GB, owner_alive)
  -> 4 dataloaders -> progressing.
- Action: NO relaunch. No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). ETA ~4-6 h -> finish Mon 28 Sep ~10:45-12:45 (GMT+6).
- Next run: expect transformer epoch ~60-70; re-verify lock/driver; relaunch ONLY if driver died while
  transformer still incomplete.

### 2026-09-28T07:45 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` LAST incomplete.
- Lock check: [(unet,False),(attention_unet,False),(deeplabv3plus,False),(transformer_mit_unet,True)]
  -> exactly ONE active run; NO relaunch (rule requires no active lock).
- State: transformer epoch 061 (07:42:20), best_ep 55, best macro 0.815756 (bad 6/15), 505.9 s/ep;
  latest macro 0.813946 [ISIC .8861/BUSI .8536/KVASIR .8045/KUB .7115]; history.csv 61 rows.
- Chain alive: driver 16736/24572 -> trainer 30856 -> worker 36592 (lock owner, owner_alive, age 29,759 s)
  -> progressing; best.pt 06:53 / latest.pt 07:42.
- Action: NO relaunch. No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). ETA ~2-4 h -> finish Mon 28 Sep ~10:00-12:00 (GMT+6).
- Next run: expect transformer epoch ~65-75 (patience trips ~ep 70 unless new best); re-verify lock/driver;
  relaunch ONLY if driver died while transformer still incomplete.

### 2026-09-28T08:47 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` LAST incomplete.
- Lock check: [(unet,False),(attention_unet,False),(deeplabv3plus,False),(transformer_mit_unet,True)]
  -> exactly ONE active run; NO relaunch (rule requires no active lock).
- State: transformer epoch 068 (08:40:14, 498.4 s), best_ep 68, best macro 0.819886 (bad 0/15, NEW BEST);
  per-domain @ep68 [ISIC .8845/BUSI .8648/KVASIR .8112/KUB .7190]; history.csv 68 rows.
- Chain alive: driver 16736/24572 (02:12:18) -> trainer 30856 (23:30:02) -> worker 36592 (lock owner,
  owner_alive, stale=false) -> 4 dataloader workers spawned 08:40 -> progressing.
- Reporter ETA: 1.9-3.4 h -> sequence finish Mon 2026-09-28 ~10:42-12:14 (GMT+6).
- Action: NO relaunch. No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). Next run: expect epoch ~75+ / possible closure; re-verify
  lock/driver; relaunch ONLY if driver died while transformer still incomplete.

### 2026-09-28T09:52 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` LAST incomplete.
- Lock check: [(unet,False),(attention_unet,False),(deeplabv3plus,False),(transformer_mit_unet,True)]
  -> exactly ONE active run; NO relaunch (rule requires no active lock).
- State: transformer epoch 077 (09:51:23, 416.0 s/ep), best_ep 74, best macro 0.822381 (bad 3/15);
  per-domain @ep74 [ISIC .8871/BUSI .8640/KVASIR .8133/KUB .7252]; history.csv 77 rows.
- Chain alive: driver 16736/24572 (02:12:18) -> trainer 30856 (23:30:02) -> worker 36592 (lock owner,
  662 MB, owner_alive, age 37,459 s) -> 4 dataloaders spawned 09:51 -> progressing.
- Gap to leader deeplabv3plus (0.827653) = 0.005272 (0.53 pp) -> top-two race tight.
- Action: NO relaunch. No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). ETA ~40-70 min to patience trip (~ep 89) or MAX_EPOCHS.
### 2026-09-28T11:02 (GMT+6) — VERIFIED healthy, no relaunch
- 3 of 4 closure.json complete (unet 0.787833 / attention_unet 0.789039 / deeplabv3plus 0.827653,
  all EARLY_STOPPING_PATIENCE); `transformer_mit_unet` LAST incomplete.
- Lock check: [(unet,False),(attention_unet,False),(deeplabv3plus,False),(transformer_mit_unet,True)]
  -> exactly ONE active run; NO relaunch (rule requires no active lock).
- State: transformer epoch 087 (11:01:41, 411.9 s/ep, elapsed ~11.53 h), best_ep 74, best macro 0.822381
  (bad 13/15); per-domain @best [ISIC .8871/BUSI .8640/KVASIR .8133/KUB .7252]; history.csv 87 rows.
- Chain alive: driver 16736/24572 (02:12:18) -> trainer 30856 (23:30:02) -> worker 36592 (lock owner,
  775 MB, owner_alive) -> 4 dataloader workers spawned 11:01 -> progressing.
- Reporter ETA: 1.0-1.9 h -> sequence finish ~12:04-12:57. Patience should trip at epoch 89 (~11:17).
- Action: NO relaunch. No protocol/binding/checkpoint changes; no TEST reads; Phase 21 not started.
- Remaining: transformer_mit_unet only (LAST). Next run: expect transformer CLOSURE; if all 4 closed,
  report sequence complete and note the five-model freeze + disk-only VAL replay + paired bootstrap
  still remain (not started here).

### 2026-09-28T15:05 (GMT+6) — FREEZE CHAIN COMPLETE (terminal entry)
- All four 20B models were already closed (EARLY_STOPPING_PATIENCE). No training remained.
- Built and ran the previously-missing five-model post-training freeze chain (5 new scripts under
  scripts/: phase20b_common, audits/phase20b_training_closure_and_replay, evaluation/
  evaluate_phase20b_val, analysis/run_phase20b_analysis, notebooks/build_phase20b_notebook).
- Produced: per-model closure + disk-only replay (4x PASS), 1 canonical 808-sample VAL pass/model,
  five-model comparison, paired domain-stratified bootstrap, confusion matrices, KUB subgroups +
  size stratification, combined per-image table, 64-case gallery (matches frozen 20A IDs), figure.
- KEY RESULT: tier separation significant (two-stage models beat every U-Net variant, p≈0.000);
  top-two ordering NOT significant (deeplabv3plus vs transformer +0.005270, p=0.282 → tied).
- Wrote `reports/audits/phase20_five_model_baseline_benchmark_freeze.json`
  (terminal `PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`,
  protocol SHA b74f1f9f… match, TEST reads 0, phase21_started false).
- FIXED a notebook-determinism bug: pandas Styler random table ids + memory-address text/plain repr
  made rebuilds non-byte-stable; fixed via set_uuid + address normalisation. 3 builds now identical
  (SHA 8c13cd14…). Recorded in `reports/audits/phase20b_notebook_determinism.json`.
- Appended a Phase-20B section to the phase-20 README (additive only).
- NO protocol/binding/check JSON modified; NO TEST reads; Phase 21 NOT started.
- Future runs: verify closures + freeze artifact, then IDLE — do not relaunch the driver.

### 2026-09-28T15:42 (GMT+6) — IDLE verification (no relaunch)
- Verified: 4/4 closure.json complete (all EARLY_STOPPING_PATIENCE; unet 0.787833 / attention_unet 0.789039 /
  deeplabv3plus 0.827653 / transformer_mit_unet 0.822381). Lock check all False; no python procs; sequence log
  terminal "PHASE 20B SEQUENCE COMPLETE" 11:15:40.
- Freeze artifact `reports/audits/phase20_five_model_baseline_benchmark_freeze.json` present and valid
  (terminal PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED, protocol SHA
  b74f1f9f… match True, top_model deeplabv3plus, top-two margin 0.005270 NOT significant).
- Action: NO relaunch (zero work remaining). Nothing modified. Phase 21 NOT started; no TEST reads.
- This automation's purpose is fulfilled — future runs should verify-and-idle only.

### 2026-09-28T15:57 (GMT+6) — REVIEWER PACKAGE REPAIR + VISUALIZATION AUDIT (terminal entry)
- Authorized Phase-20B reviewer-package repair (NO training / NO new inference / NO canonical VAL
  rerun / NO TEST). Built canonical folder notebooks/phasewise/phase_20b_five_model_baselines/
  (README + notebook); migrated off phase_20_multidomain_baselines/.
- New: src/analysis/phase20b_reviewer.py, src/analysis/phase20b_figures.py (153 figures);
  scripts/analysis/run_phase20b_reviewer_package.py, sync_phase20b_governance.py, write_phase20b_audits.py;
  scripts/notebooks/build_phase20b_notebook.py (rebuilt), sync_phasewise_index_notebook.py.
- Notebook = FULL evidence: 76 cells (34 md/42 code), 130 PNG + 49 HTML, 0 tracebacks.
  3-build determinism PASS: SHA 77dc0aa8… (identical across 3 builds). Size 39 MB.
- Figures 153 (114 embedded); matrix visualization coverage 51/51 = 100%. Gallery disk 178→44 MB.
- Fixed: sty() fmt-dict signature; provenance binding resolved via frozen protocol code_shas (20A
  closure lacks protocol_sha256); matplotlib boxplot(tick_labels=); pandas 3.x applymap; 5-model
  view via per-model concatenation (combined CSV had 4 models).
- Governance synced additively: map.{csv,json,md}, phasewise README, PROJECT_MASTER_PLAN, index
  notebook (re-exec, SHA ff418ba5…), visualization registry (+4), dataset coverage (+4),
  execution manifest (+19/20/20B).
- New artifacts: phase20b_reviewer_package_audit.json, phase20b_reviewer_package_freeze.json,
  phase20b_notebook_location_migration.json, phase20b_notebook_determinism.json, figure inventory
  + matrix coverage CSV.
- Frozen science UNCHANGED (protocol b74f1f9f…); TEST reads 0; Phase 21 NOT STARTED.
  Doc terminal PHASE20B_REVIEWER_PACKAGE_COMPLETE__FULL_VISUAL_EVIDENCE__PHASE21_ELIGIBLE_NOT_STARTED.
- Future runs: verify-and-idle; do NOT retrain, do NOT rerun canonical VAL, do NOT start Phase 21.

### 2026-09-28T16:43 (GMT+6) — IDLE verification (no relaunch)
- 4/4 closure.json complete (all EARLY_STOPPING_PATIENCE): unet 0.787833 / attention_unet 0.789039 /
  deeplabv3plus 0.827653 / transformer_mit_unet 0.822381.
- Lock check all False; no python processes; sequence log terminal 11:15:40; freeze artifact valid
  (terminal PHASE20_FIVE_MODEL_BASELINE_BENCHMARK_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED, phase21_started False).
- Action: NO relaunch (zero work remaining). Nothing modified. Phase 21 NOT started; no TEST reads.
- Housekeeping: consolidated workspace MEMORY.md 10,448 -> ~4.3k chars.
- Purpose fulfilled — future runs: verify-and-idle only.

---

# ============================ SCOPE CHANGE ============================
# From 2026-09-28 the supervisor AUTHORIZED Phase 21. This automation has been
# REPURPOSED from "Phase-20B keep-alive" to "Phase-21 Global MedFiLM keep-alive"
# (name, prompt and validUntil updated). Phase 20A + 20B are COMPLETE and frozen;
# do NOT relaunch the Phase-20B driver any more.
# ======================================================================

### 2026-09-28T17:45 (GMT+6) — PHASE 21 AUTHORIZED; pre-training governance COMPLETE; TRAINING LIVE
- Supervisor AUTHORIZATION for Phase 21 (GLOBAL MedFiLM reference, four-domain
  task-conditioned global segmentation). NOT the final RA-MedFiLM-Seg++; GLOBAL reference only.
- **Pre-training governance COMPLETE (fail-closed, all PASS):**
  - `reports/audits/phase21_entry_gate.json` — 15/15 checks PASS, `training_may_start=true`.
  - `reports/audits/phase21_legacy_medfilm_architecture_audit.json` — legacy FiLM evidence
    (`medfilm_weak_segmentation_v2.py` SHA 64c4eb40…, `plain_weak_segmentation_v2.py` SHA 47b60429…),
    exact equation `F_hat=(1+gamma(t))*F+beta(t)`, gamma/beta=tanh, zero-init output ⇒ identity at
    init, 5 sites (bridge, decoder4..decoder1), embedding dim 32 / film hidden 64, NO SE, NO deep
    supervision. Classified REFERENCE_ONLY; historical results NOT claimed as current.
  - `reports/audits/phase21_protocol_binding.json` — 24/24 inherited values IDENTICAL to the frozen
    Phase-20 protocol (b74f1f9f…), **unintentional_differences = []**.
  - `reports/audits/phase21_global_medfilm_architecture_binding.json` — ONE architecture frozen
    BEFORE training; 3,523,001 params; forbidden-module audit PASS; no sweep.
  - `reports/audits/phase21_pre_execution_check.json` — 27/27 PASS.
- **NEW code:** `src/models/film/global_medfilm.py` (+ `__init__.py`), factory keys `medfilm` /
  `global_medfilm`; `scripts/training/phase21_common.py`;
  `scripts/training/train_phase21_global_medfilm.py`; `scripts/evaluation/evaluate_phase21_val.py`;
  `scripts/analysis/run_phase21_analysis.py`, `phase21_conditioning_diagnostic.py`,
  `phase21_efficiency.py`, `write_phase21_freeze.py`, `run_phase21_post_training_pipeline.py`,
  `sync_phase21_governance.py`; `src/analysis/phase21_figures.py`;
  `scripts/notebooks/build_phase21_notebook.py`.
- **TRAINING LIVE:** `phase21_global_medfilm_fourdomain_seed42_clean_v3`, launched 17:28:59.
  Governance preflight OK, TRAIN 5832 / VAL 808, model 3,523,001 params, seed 42, 100 epochs max,
  patience 15. **Epoch 001 done in 596.4s: train_loss 0.3894, val_loss 0.2901, macro-domain VAL Dice
  0.615488** (ISIC 0.8067 / BUSI 0.6790 / KVASIR 0.4858 / KUB 0.4904); best_ep 1, bad 0. Lock ACTIVE,
  owner alive, not stale; GPU ~97% peak.
- Rate ≈ 596 s/epoch ⇒ projected 10-16 h to natural termination (early stop typically ~ep 60-90).
- Architecture note: FiLM output projection is zero-initialised, so d(loss)/d(task_embedding) is
  EXACTLY zero at step 0 (identity at init). The projection itself DOES receive gradient at step 0,
  and after ONE optimizer step the embedding path opens. Both facts are recorded in the
  pre-execution check — this is expected, not a defect.
- Resume is bit-exact BY CONSTRUCTION (per-epoch `derive_epoch_seed(seed, epoch)`; explicit
  `make_generator(seed)` + `seed_worker`; dataset has NO internal RNG), so no RNG-state persistence
  is needed.
- **Next run must:** verify lock/driver; if not terminated AND no active lock ⇒ relaunch
  `train_phase21_global_medfilm.py --resume` in background; once `phase21_training_closure.json`
  has stop_reason in {EARLY_STOPPING_PATIENCE, MAX_EPOCHS} ⇒ run
  `scripts/analysis/run_phase21_post_training_pipeline.py` (canonical VAL eval → analysis →
  conditioning → efficiency → figures → notebook x3 determinism → freeze → governance sync).
- Hard constraints unchanged: NO TEST reads, NO protocol/architecture change, NO second seed,
  NO Phase-22 start, no causal FiLM claims. No frozen artifact modified.

### 2026-09-28T18:22 (GMT+1/BST) — Phase-21 keep-alive: VERIFIED HEALTHY, no relaunch
- **State:** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch 006 logged
  18:15:37 (409.5 s). best_ep 6, **best macro-domain VAL Dice 0.728646**, bad 0/15, resume_count 0,
  cumulative 2799.8 s. Monotone new-best every epoch so far (0.6155 → 0.6387 → 0.6655 → 0.6866 →
  0.7178 → 0.7286).
- **Liveness:** lock `experiments/<exp>/.experiment.lock` ACTIVE, owner_alive=true, PID 10212
  (1.99 GB RSS), stale=false, age 3,216 s. PID 10212 holds a CUDA context (nvidia-smi); 4 dataloader
  workers + parent alive. GPU 6,125/8,192 MiB. Chain genuinely progressing.
- **closure.json:** ABSENT (`reports/audits/phase21_training_closure.json` does not exist) → run NOT
  terminated. **Action: NO relaunch** (rule requires no active lock).
- **IMPORTANT GOTCHA (record for future runs):** `src.utils.run_lock.inspect_lock()` takes an
  experiment **DIRECTORY** path, not an experiment_id. Passing the bare id silently returns
  `{"present": false, "reason": "no lock file"}` and looks like a dead run. Always call
  `inspect_lock('experiments/<experiment_id>')`.
- **Artifact layout gotcha:** `history.csv` / `history.json` / `training_state.json` / `config.json` /
  `run_manifest.json` / `.experiment.lock` live under `experiments/<experiment_id>/`, NOT under
  `checkpoints/<experiment_id>/` (which holds only best.pt / last.pt / latest.pt).
- **Rate ≈ 409–467 s/epoch (mean ~457 s).** Projected natural termination (patience trip ~ep 60–90):
  roughly 7–12 h from now, i.e. ~2026-09-29 01:00–06:00.
- **Pending conversational item completed:** answered the supervisor's "is it light weight?" question
  with evidence (params + analytical MACs). See below.
- **NOT done deliberately:** did NOT run `scripts/analysis/phase21_mac_count.py --all-models`. That
  script uses forward hooks (a real forward pass per model at 512², six models) and its own docstring
  says to run it after training when the CPU/GPU is free — running it now would contend with the live
  run. It remains a scheduled post-training pipeline step (`mac_count_six_models`).
- Hard constraints unchanged: NO TEST reads, NO protocol/architecture change, NO second seed,
  NO Phase-22 start. No frozen artifact modified.

### 2026-09-28T20:35 — six-model cost comparison produced (supervisor request "update with compare")
- Training still healthy: epoch 025, best macro **0.816123** (best_ep 24), bad 1/15, lock active.
- Produced `reports/tables/phase21_six_model_compute.csv` (NEW) and updated
  `reports/phase21_global_medfilm_report.md` (464 → 559 lines, new §16.1 six-model comparison +
  §11 frozen-baseline scaffold). Panel: Global MedFiLM 3.52M/31.55 G MACs · U-Net 7.76M/46.14 ·
  Attn U-Net 7.85M/47.22 · DeepLabV3+ 40.35M/69.14 · Transformer-MiT 16.35M/99.10 · U-Net++ 9.16M/137.94.
  **MedFiLM is rank 1/6 on BOTH params and compute.**
- **Corrected a wrong constant:** U-Net is 7,763,041 params, NOT 31,042,337. Now an active fail-closed
  cross-check (rc=3) in `phase21_mac_count.py`.
- **New environment rule:** `CUDA_VISIBLE_DEVICES=""` is IGNORED on this host — pass an explicit
  `--device cpu` instead. Orchestrator steps updated accordingly.
- `mac_count_*` steps now already DONE; the post-training pipeline will simply regenerate them identically.
  Remaining pending: efficiency (GPU benchmark — must stay deferred until training ends), analysis,
  conditioning, figures, notebook, freeze.

### 2026-09-28T22:19–22:31 — **RUN WAS DEAD; RESUMED SUCCESSFULLY** (teardown, not a crash)
- **Found dead:** log frozen at EPOCH 029 (21:03:39, mid-epoch 30); `owner_alive=false`, lock stale;
  GPU idle 606 MiB; PID 10212 gone; closure.json absent. Survived 3h35m (17:28:57 → 21:03:39).
- **Diagnosis = EXTERNAL PROCESS-TREE TEARDOWN, not a crash.** All diagnostic checks empty:
  0 application-crash events (1000/1001/1002), no WER *python* report, no hang, no Kernel-Power 42/107,
  no EventID 41, no Resource-Exhaustion-Detector, 21.3/32.7 GB RAM free. Log ends cleanly after a flush
  (a SIGKILL signature; an exception would have written a traceback). Matches this host's ~2–3.5 h ceiling.
- **Resume provenance verified first:** `latest.pt` = epoch 29, best_epoch 27, best_macro 0.819244,
  bad 2/15, with model/optimizer/scheduler/grad_scaler states. RNG state correctly ABSENT — resume is
  bit-exact BY CONSTRUCTION in this project, so this is not a defect.
- **Relaunched:** `--resume --recover-stale-lock` via Bash run_in_background=true. Clean recovery:
  `recovered_stale_lock: true`, new PID **12656**; log `RESUME … at epoch 29 -> next 30`.
  Relaunch log: `logs/phase21_resume_20260928_2219.log`.
- **EPOCH 030 completed** in 576.6 s: train_loss 0.0968, val_loss 0.1533, macro **0.818102**,
  best_ep 27 preserved, bad 3/15, new_best=False → trajectory continuous, no divergence.
  `resume_count: 1`; checkpoint `resume_events` now records the interruption permanently.
- **Automation PROMPT UPDATED** to handle this case: the previous prompt only escalated a *stale lock*
  when the run had TERMINATED, so it would have IDLED on a dead-but-unterminated run forever — that is
  the gap that let the run sit dead for 75 min. The prompt now treats "no log progress for >15 min" as
  teardown, resumes on `owner_alive=false` while un-terminated, and warns that `tasklist` is not a
  liveness check (it listed the dead PID 10212 for over an hour).
- Next expected event: another teardown near the ceiling → same resume. Then natural termination
  (patience 15; currently bad 3/15, best ep 27) → post-training pipeline.

### 2026-09-28T18:40 (GMT+6) — Phase-21 keep-alive: VERIFIED HEALTHY, no relaunch
- **State: TRAINING.** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch 009
  logged 18:40:15 (515.2 s, cumulative 4277.7 s). train_loss 0.1727 / val_loss 0.1907,
  **macro-domain VAL Dice 0.761398**, best_ep 9, bad 0/15, new_best=True, resume_count 0.
  Per-domain @ep09: ISIC 0.8797 / BUSI 0.8384 / KVASIR 0.7115 / KUB 0.6160.
- **Liveness:** epoch line 18:40:15 vs check time 18:40:18 (3 s) ⇒ genuinely progressing.
  Lock ACTIVE, owner_alive=true, stale=false, PID 10212 (791 MB), age 4272 s. GPU 6109/8192 MiB
  (transient 4% sample — between epochs). latest.pt / history.csv / run log all rewritten 18:40:1x.
- **closure.json:** ABSENT in BOTH candidate locations (`experiments/<exp>/phase21_training_closure.json`
  and `reports/audits/phase21_training_closure.json`) ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active ⇒ rule not satisfied). Nothing modified; no checkpoint touched.
- **Progress:** monotone new best every epoch so far (0.6155 → 0.6387 → 0.6655 → 0.6866 → 0.7178 →
  0.7286 → 0.7307 → 0.7579 → 0.7614). Rate ~457–515 s/epoch (mean ~477 s).
- **ETA:** early stop cannot trip before epoch 24 (~2.0 h out, ~20:45). Typical natural termination
  at ep 60–90 ⇒ ~7–11 h from now ⇒ **2026-09-29 ~01:30–05:45**; worst case (MAX_EPOCHS 100) ~07:05.
- **Remaining:** finish training → then `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → final freeze → governance sync).
- Hard constraints unchanged: NO TEST reads (0), NO protocol/architecture change, NO second seed,
  NO Phase-22 start, no causal FiLM claim. No frozen artifact modified.

### 2026-09-28T19:41 (GMT+6) — Phase-21 keep-alive: VERIFIED HEALTHY, no relaunch
- **State: TRAINING.** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch 017
  logged 19:37:16 (408.8 s, cumulative 7699.3 s). train_loss 0.1239 / val_loss 0.1648,
  **macro-domain VAL Dice 0.804096**, best_ep 17, bad 0/15, new_best=True, resume_count 0.
  Per-domain @ep17: ISIC 0.8836 / BUSI 0.8512 / KVASIR 0.7710 / KUB 0.7106.
- **Liveness:** lock ACTIVE, owner_alive=true, stale=false, PID 10212, age 7944 s (started 17:28:57).
  best.pt / last.pt / latest.pt all rewritten 19:37; history.csv 17 rows; training_state.json epoch 17.
  Epoch line 19:37:16 vs check 19:41 ⇒ ~4 min old, consistent with ~410 s/epoch ⇒ progressing.
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active ⇒ rule requires no active lock). Nothing modified; no checkpoint touched.
- **Progress:** best macro-domain Dice trajectory 0.6155 → 0.6387 → 0.6655 → 0.6866 → 0.7178 → 0.7286 →
  0.7307 → 0.7579 → 0.7614 → … → 0.7915 (ep13) → 0.7953 (ep14) → 0.8041 (ep17). Strongly monotone.
  Compare: Phase-20 conventional baselines at best epoch span 0.787833–0.827653 — Phase 21 already
  sits inside that band at epoch 17 of 100.
- **Rate ≈ 399–419 s/epoch (recent mean ~412 s).** Early stop cannot trip before epoch 32 (~1.7 h out).
  Typical natural termination ep 60–90 ⇒ ~5–8 h from now ⇒ **2026-09-29 ~00:30–04:00 (GMT+6)**;
  worst case (MAX_EPOCHS 100) ~09:00.
- **Remaining:** finish training → then `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → final freeze → governance sync).
- Hard constraints unchanged: NO TEST reads (0), NO protocol/architecture change, NO second seed,
  NO Phase-22 start, no causal FiLM claim. No frozen artifact modified.

### 2026-09-28T20:42 (GMT+6) — Phase-21 keep-alive: VERIFIED HEALTHY, no relaunch
- **State: TRAINING.** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch 026 logged
  20:39:30 (449.4 s, cumulative 11433.2 s). train_loss 0.1045 / val_loss 0.1638, latest macro-domain VAL
  Dice 0.811633; best_ep 24, **best macro 0.816123**, bad 2/15, new_best=False, resume_count 0.
  Per-domain @ep26: ISIC 0.8738 / BUSI 0.8546 / KVASIR 0.7860 / KUB 0.7322.
- **Liveness:** epoch line 20:39:30 vs check 20:42:31 (~3 min old, consistent with ~440 s/epoch) ⇒ genuinely
  progressing. Lock ACTIVE, owner_alive=true, stale=false, PID 10212 (647 MB) confirmed in tasklist;
  best.pt 20:25 / last.pt+latest.pt 20:39; history.csv 26 rows; training_state.json epoch 26, stop_reason null.
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active ⇒ rule requires no active lock). Nothing modified; no checkpoint touched.
- **Progress:** best trajectory 0.6155 → … → 0.8041 (ep17) → 0.8151 (ep19) → **0.816123 (ep24)**; now
  plateauing in the upper part of the Phase-20 conventional band (0.787833–0.827653).
- **Rate ≈ 395–450 s/epoch (26-epoch mean ~440 s).** Early stop cannot trip before epoch 39 (~1.6 h out,
  ~22:20). Typical natural termination ep 60–90 ⇒ ~4–8 h from now ⇒ **2026-09-29 ~00:50–04:20 (GMT+6)**;
  worst case (MAX_EPOCHS 100) ~06:00.
- **Remaining:** finish training → then `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → final freeze → governance sync).
- Housekeeping: consolidated workspace MEMORY.md (deduplicated Phase-20/20B + Phase-21 + cost sections).
- Hard constraints unchanged: NO TEST reads (0), NO protocol/architecture change, NO second seed,
  NO Phase-22 start, no causal FiLM claim. No frozen artifact modified.

### 2026-09-28T23:19 (GMT+6) — Phase-21 keep-alive: **TRAINING (post-resume), VERIFIED HEALTHY, no relaunch**
- **State: TRAINING (resumed lineage).** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS,
  epoch **036** logged 23:15:04 (489.1 s, cumulative 3243.7 s since the 22:21 resume). train_loss 0.0898 /
  val_loss 0.1572, latest macro 0.820482; **best_ep 32, best macro-domain VAL Dice 0.826218**, bad 4/15,
  new_best=False, resume_count 1. Per-domain @ep36: ISIC 0.8895 / BUSI 0.8657 / KVASIR 0.7928 / KUB 0.7339.
- **Liveness:** lock `experiments/<exp>/.experiment.lock` ACTIVE, owner_alive=true, stale=false,
  PID **12656** (the resume PID from 22:21:00, so the recovery held), age 3510 s. Log mtime 23:15:04 vs
  check 23:19:27 (~4.4 min, consistent with ~410–510 s/epoch) ⇒ genuinely progressing. last.pt/latest.pt
  rewritten 23:15:04; best.pt 22:44:41 (= epoch 32, the current best). training_state.json epoch 36,
  stop_reason null.
- **Teardown+resume history:** the run WAS torn down at 21:03:39 mid-epoch-30 (3h35m ceiling) and was
  resumed at 22:21 by the previous automation run (`--resume --recover-stale-lock`, `recovered_stale_lock=true`,
  new PID 12656). No teardown occurred during THIS window — the current process is the survivor of that
  same resume. So "teardown+resume occurred" = YES for the lineage, but no new resume action was needed now.
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active AND owner alive ⇒ decision path (a) IDLE). Nothing modified;
  no checkpoint touched; no protocol/binding/checkpoint-JSON change; no TEST reads (0).
- **Progress vs baselines:** best 0.826218 (ep32) now sits at/just above the top of the Phase-20
  conventional band (0.787833–0.827653) — i.e. the Global MedFiLM reference is already comparable to the
  best conventional baseline on the same 808-sample VAL protocol. Trajectory still improving (new bests at
  ep 27, 31, 32); bad only 4/15 so patience cannot trip before epoch 47 (~1.3 h out).
- **Rate ≈ 405–588 s/epoch.** Typical natural termination ep 60–90 ⇒ ~3–7 h from now ⇒
  **2026-09-29 ~02:00–06:00 (GMT+6)**; worst case (MAX_EPOCHS 100) ~08:00. Expect ≥1 more teardown+resume.
- **Remaining:** finish training → `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-five-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → freeze → governance sync).

### 2026-09-29T01:21 (GMT+6) — Phase-21 keep-alive: **TRAINING, VERIFIED HEALTHY, no relaunch**
- **State: TRAINING.** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch **053** logged
  01:19:46 (388.0 s, cumulative 10,726.1 s since the 22:21 resume). train_loss 0.0708 / val_loss 0.1503,
  latest macro 0.829493; **best_ep 49, best macro-domain VAL Dice 0.832606**, bad 4/15, new_best=False,
  resume_count 1. Per-domain @ep53: ISIC 0.8920 / BUSI 0.8660 / KVASIR 0.8138 / KUB 0.7461.
- **Liveness:** epoch line 01:19:46 vs check 01:21:42 (2 min old, inside the 384–501 s/epoch band) ⇒
  genuinely progressing. Lock `experiments/<exp>/.experiment.lock` ACTIVE, owner_alive=true, stale=false,
  PID **12656** (survivor of the 22:21 resume), age 10,848 s. closure.json ABSENT in both locations.
- **Teardown+resume history:** YES for the lineage — killed 2026-09-28 21:03:39 mid-epoch-30 (3h35m ceiling),
  resumed 22:21 (`--resume --recover-stale-lock`, `recovered_stale_lock=true`, PID 12656). **No NEW teardown
  in this window** — the current process is still that same resume, now ~3h00m old (approaching the ceiling).
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active AND owner alive ⇒ decision path (a) IDLE). Nothing modified; no
  checkpoint touched; no protocol/binding/check JSON change; no TEST reads (0).
- **Progress vs baselines:** best 0.832606 (ep49) **exceeds the top of the Phase-20 conventional band**
  (0.787833–0.827653) and the 20B leader DeepLabV3+ (0.827653), on the SAME 808-sample VAL protocol.
  Still improving (new bests at ep 41, 42, 44, 49); bad 4/15 ⇒ patience cannot trip before epoch 64 (~1.5 h).
- **Rate ≈ 384–501 s/epoch (recent mean ~430 s).** Typical natural termination ep 60–90 ⇒ ~0.5–4.5 h from
  now ⇒ **2026-09-29 ~02:00–06:00 (GMT+6)**; worst case (MAX_EPOCHS 100) ~07:00. **Expect ≥1 more
  teardown+resume imminently** (current process ~3h old vs the ~2–3.5 h ceiling).
- **Remaining:** finish training → `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-five-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → freeze → governance sync).

### 2026-09-29T00:20 (GMT+6) — Phase-21 keep-alive: **TRAINING, VERIFIED HEALTHY, no relaunch**
- **State: TRAINING.** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch **044** logged
  00:14:36 (477.2 s, cumulative 6816.4 s since the 22:21 resume). train_loss 0.0789 / val_loss 0.1481,
  **macro-domain VAL Dice 0.831430 — NEW BEST, best_ep 44, bad 0/15, new_best=True**, resume_count 1.
  Per-domain @ep44: ISIC 0.8953 / BUSI 0.8631 / KVASIR 0.8150 / KUB 0.7524. history.csv 45 rows (44 epochs).
- **Liveness:** lock ACTIVE, owner_alive=true, stale=false, PID **12656**, age 7178.6 s ⇒ genuinely progressing.
  Epoch line 00:14:36 vs check 00:20:32 (~6 min old) is within the observed 384–588 s/epoch band.
  best.pt / last.pt / latest.pt all rewritten 00:14:36. training_state.json epoch 44, stop_reason null.
- **Teardown+resume history:** YES for the lineage — killed 2026-09-28 21:03:39 mid-epoch-30 (3h35m ceiling),
  resumed 22:21 by a prior automation run (`--resume --recover-stale-lock`, `recovered_stale_lock=true`,
  PID 12656). No NEW teardown in this window; the current process is the survivor of that resume.
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active AND owner alive ⇒ decision path (a) IDLE). Nothing modified; no
  checkpoint touched; no protocol/binding/check JSON change; no TEST reads (0).
- **Progress vs baselines:** best 0.831430 (ep44) **now EXCEEDS the top of the Phase-20 conventional band**
  (0.787833–0.827653) and the 20B benchmark leader DeepLabV3+ (0.827653) — on the SAME 808-sample VAL
  protocol. Trajectory still improving; bad only 0/15 so patience cannot trip before epoch 59 (~2.6 h out).
- **Rate ≈ 384–588 s/epoch (recent mean ~450 s).** Typical natural termination ep 60–90 ⇒ ~2.5–7 h from now
  ⇒ **2026-09-29 ~03:00–07:00 (GMT+6)**; worst case (MAX_EPOCHS 100) ~09:00. Expect ≥1 more teardown+resume.
- **Remaining:** finish training → `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-five-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → freeze → governance sync).

### 2026-09-29T02:23 (GMT+6) — Phase-21 keep-alive: **TRAINING, VERIFIED HEALTHY, no relaunch**
- **State: TRAINING.** `phase21_global_medfilm_fourdomain_seed42_clean_v3` IN PROGRESS, epoch **062** logged
  02:18:14 (393.6 s, cumulative 27,115.6 s). train_loss 0.0661 / val_loss 0.1496, latest macro 0.831393;
  **best_ep 57, best macro-domain VAL Dice 0.833947**, bad 5/15, new_best=False (latest best was ep 57),
  resume_count 1. Per-domain @ep62: ISIC 0.8909 / BUSI 0.8639 / KVASIR 0.8155 / KUB 0.7553.
- **Liveness:** lock ACTIVE, owner_alive=true, stale=false, PID **12656** (survivor of the 22:21 resume),
  age 14,517 s; psutil confirms 12656 running, RSS 1,036 MB, 26 threads, with 4 multiprocessing dataloader
  children (1616/5376/29196/29880). Epoch line 02:18:14 vs check 02:23:01 = 4.8 min old, inside the
  observed 379–511 s/epoch band ⇒ genuinely progressing. last.pt/latest.pt/history.csv/state all 02:18:14.
- **Teardown+resume history:** YES for the lineage — killed 2026-09-28 21:03:39 mid-epoch-30 (3h35m ceiling),
  resumed 22:21 (`--resume --recover-stale-lock`, `recovered_stale_lock=true`, PID 12656). **No NEW teardown
  in this window**; current process ~3h02m old, i.e. again approaching the ~2–3.5 h ceiling.
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run.
- **Action: NO relaunch** (lock active AND owner alive ⇒ decision path (a) IDLE). Nothing modified; no
  checkpoint touched; no protocol/binding/check JSON change; no TEST reads (0).
- **Progress vs baselines:** best 0.833947 (ep57) remains **above the whole Phase-20 conventional band**
  (0.787833–0.827653) and above the 20B leader DeepLabV3+ (0.827653), same 808-sample VAL protocol.
  Still improving (new bests at ep 49 and 57); bad 5/15 ⇒ patience cannot trip before epoch 72 (~70 min out).
- **Rate ≈ 379–511 s/epoch (recent mean ~394 s).** Natural termination ep 72–90 ⇒ ~1.0–3.0 h from now ⇒
  **2026-09-29 ~03:30–05:30 (GMT+6)**; worst case (MAX_EPOCHS 100) ~07:00. **Expect ≥1 more teardown+resume.**
- **Remaining:** finish training → `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-five-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → freeze → governance sync).
- Hard constraints unchanged: NO TEST reads, NO protocol/architecture change, NO second seed, NO Phase-22
  start, no causal FiLM claim. No frozen artifact modified.

### 2026-09-29T03:24 (GMT+6) — Phase-21 keep-alive: **TRAINING, VERIFIED HEALTHY, no relaunch**
- **State: TRAINING.** epoch **072** logged 03:23:48 (419.7 s, cumulative 31,049.6 s). train_loss 0.0599 /
  val_loss 0.1481, latest macro 0.832418; **best_ep 66, best macro-domain VAL Dice 0.8350791259413984**,
  bad 6/15, new_best=False. Per-domain @ep72: ISIC 0.8938 / BUSI 0.8563 / KVASIR 0.8177 / KUB 0.7618.
  history.csv 73 rows (72 epochs); run log 72 EPOCH lines.
- **Liveness:** lock ACTIVE, owner_alive=true, stale=false, PID **12656** (survivor of the 22:21 resume),
  age 18,200 s (5h03m). psutil: running, RSS 988 MB, 26 threads, 4 dataloader children (30736/10444/8836/
  30376). Epoch line 03:23:48 vs check 03:24:26 = **0.6 min old** ⇒ unambiguously progressing (well inside
  the 379–511 s/epoch band). best.pt 02:44:10 (= ep 66, the frozen best), last/latest .pt 03:23:47–48,
  state epoch 72, stop_reason null, resume_count 1.
- **Teardown+resume history:** YES for the lineage — killed 2026-09-28 21:03:39 mid-epoch-30 (3h35m ceiling),
  resumed 22:21 (`--resume --recover-stale-lock`, `recovered_stale_lock=true`, PID 12656). **No NEW teardown
  in this window**, despite the process now being ~5h03m old — i.e. it has already outlived the reported
  ~2–3.5 h ceiling, so the survival window is wider than documented and teardown is not imminent per se.
- **closure.json:** ABSENT in BOTH `experiments/<exp>/` and `reports/audits/` ⇒ run NOT terminated.
  `reports/audits/phase21_final_freeze.json` also ABSENT ⇒ post-training pipeline NOT yet run. Phase-21
  governance artifacts all present & untouched (entry_gate/binding/pre_execution_check/legacy audit/
  protocol_binding, plus phase21_analytical_mac_count.json 20:32 and phase21_progress_status.json 20:34).
- **Action: NO relaunch** (lock active AND owner alive ⇒ decision path (a) IDLE). Nothing modified; no
  checkpoint touched; no protocol/binding/check JSON change; no TEST reads (0).
- **Progress vs baselines:** best 0.835079 (ep66) remains **above the whole Phase-20 conventional band**
  (0.787833–0.827653) and above the 20B leader DeepLabV3+ (0.827653), same 808-sample VAL protocol.
  Plateauing (last new best ep 66; bad 6/15) but patience cannot trip before epoch 81 (~1 h out);
  `lr` at 1.813e-05 is mid-schedule, so a late-decay improvement to ~ep 85–90 is still plausible.
- **Rate ≈ 379–511 s/epoch (recent mean ~394 s).** Natural termination ep 81–90 ⇒ ~1.0–2.5 h from now ⇒
  **2026-09-29 ~04:30–06:00 (GMT+6)**; worst case (MAX_EPOCHS 100, ~8 more epochs) ~07:00.
- **Remaining:** finish training → `scripts/analysis/run_phase21_post_training_pipeline.py`
  (canonical VAL pass 808 → analysis/bootstrap/paired-vs-five-baselines/KUB strata → conditioning diagnostic
  → efficiency → figures → notebook ×3 determinism → freeze → governance sync). Next run should jump
  straight to step 5 once closure.json appears with stop_reason in {EARLY_STOPPING_PATIENCE, MAX_EPOCHS}.


## 2026-09-29 04:25 (GMT+6) — COMPLETE
- **State: COMPLETE.** Training had already terminated NATURALLY (early stopping, no teardown this run):
  ep 81, `stop_reason=EARLY_STOPPING_PATIENCE`, best_ep 66, best macro-domain Dice **0.835079**,
  per-domain ISIC .8972 / BUSI .8588 / KVASIR .8202 / KUB .7641. 1 resume event (from ep 29, 09-28 22:21).
- **Action:** decision path (c) → ran the post-training pipeline. It FAILED CLOSED 6× on real bugs, which I
  fixed one at a time (all in `scripts/analysis/`, none touching governance, architecture, hyperparams, or TEST):
  1. `run_phase21_analysis.py` — `res[...]` CI key typo (`macro_domain_dice_ci_*` vs actual `macro_dice_ci_*`).
  2. `run_phase21_post_training_pipeline.py` — `from src.analysis import` ran before `sys.path.insert(ROOT)`.
  3. `src/analysis/phase21_figures.py` — gallery assumed `phase20b_unetpp_prediction_manifest.csv`; U-Net++ is
     Phase-20A and uses `phase20_prediction_manifest.csv` (same special-case the analysis script already had).
  4. **freeze↔notebook circular dependency** — notebook consumes `phase21_final_freeze.json` (asserts terminal
     state); freeze requires `phase21_notebook_determinism.json`. Resolved with an explicit **two-pass freeze**:
     pass 1 writes real content (rc=2, expected) → 3 notebook builds → pass 2 must verify (rc=0).
  5. **Notebook self-reference** — cell "Artifact index" globbed `phase21_*.json`, embedding the freeze's OWN
     SHA/size while the freeze records the notebook SHA ⇒ permanently non-byte-identical. Fixed by excluding
     `{phase21_final_freeze.json, phase21_notebook_determinism.json}` from the index.
- **Final:** pipeline rc=0. `phase21_final_freeze.json` `freeze_verified=true`, `validation_problems=[]`,
  terminal_state `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED`, phase22_started=false,
  notebook ×3 byte-identical (`bb916f5429…`). TEST reads all **0**. 43 figures, 77-cell notebook.
- **Results (GLOBAL reference only):** rank 1/6; macro VAL Dice 0.835079 [0.787749, 0.878006] vs DeepLabV3+ .827652,
  Transformer/MiT .822383, U-Net++ .792010, Attn U-Net .789037, U-Net .787832. Paired bootstrap: significant vs
  U-Net / Attn U-Net / U-Net++ / Transformer-MiT; **NOT significant vs DeepLabV3+** (diff +0.007427, CI
  [−0.002042, +0.018313], p=.124). Conditioning `CONDITIONING_EFFECT_PRESENT`
  (mean |Δ Dice| wrong-task 0.1842 on the frozen 64 gallery). No causal FiLM claim made anywhere.
- **Remaining:** none for Phase 21. Phase 22 is ELIGIBLE but NOT STARTED (do not start it here).

## 2026-09-29 06:07 (GMT+6) — COMPLETE (verify-and-idle)
- **State: COMPLETE.** No training process, no lock. `inspect_lock(experiments/phase21_..._clean_v3)` →
  `{'present': False, 'active': False, 'stale': False, 'owner_alive': None, 'reason': 'no lock file'}`.
  `psutil` scan for `train_phase21` / `run_phase21_post_training`: no live process (only this run's own
  inspection commands matched). Run log frozen at 04:22:47 (TRAINING COMPLETE ep 66 best / ep 81 stop).
- **Decision path (c)-(already-done):** closure.json `stop_reason=EARLY_STOPPING_PATIENCE` AND
  `reports/audits/phase21_final_freeze.json` exists → post-training pipeline was already run to rc=0 by the
  04:25 execution. **No relaunch, no resume, nothing run this turn.**
- **Verified:** `phase21_final_freeze.json` (mtime 2026-09-29 05:05:48) `freeze_verified=true`,
  `validation_problems=[]`, `canonical_val_inference_runs=1` (808/808), notebook ×3 byte-identical
  `bb916f5429…` (43 figures, 77 cells); `phase21_governance_sync.json` additive_only,
  frozen_science_modified=false, test_reads=0; terminal_state
  `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED`, phase22_started=false.
- Best macro-domain VAL Dice **0.835079** (ep 66); ISIC .8972 / BUSI .8588 / KVASIR .8202 / KUB .7641.
  Rank 1/6; only DeepLabV3+ NOT separable (p=.124). Teardown occurred earlier (09-28, from ep 29) and was
  already recovered — no teardown this run.
- **No changes made:** no checkpoint touched, no protocol/binding/pre_execution_check modified, TEST reads 0.
- **Housekeeping:** consolidated workspace `MEMORY.md` 21,566 → 10,580 chars (deduped, merged, Phase-21
  status/arch/result and the post-training re-run fixes retained).
- **Remaining:** none for Phase 21. Phase 22 ELIGIBLE but NOT STARTED — do NOT start it from this automation.
  Future runs of this automation should be pure verify-and-idle.

## 2026-09-29 08:05 (GMT+6) — RETIRED (automation paused)
- **State: COMPLETE / RETIRED.** Phase 21 reached its terminal state on 2026-09-28/29 and the
  post-training pipeline is verified (`phase21_final_freeze.json` freeze_verified=true,
  validation_problems=[]). The automation's own prior entry said "Future runs of this automation
  should be pure verify-and-idle" — an hourly no-op has no purpose, so this automation was
  **paused** (status ACTIVE → PAUSED) via automation_update. Not deleted, so the definition and
  this history remain inspectable; it can be resumed if Phase 21 ever needs re-verification.
- Matches the project convention: the Phase-20 keep-alive (4da839e6-…) was likewise PAUSED, not deleted.
- **Verified before retiring:** closure stop_reason=EARLY_STOPPING_PATIENCE; no lock file; no live
  train/post-training process; freeze_verified=true; terminal
  `PHASE21_GLOBAL_MEDFILM_REFERENCE_COMPLETE__PHASE22_ELIGIBLE_NOT_STARTED`; phase22_started=false;
  test_reads=0 on all four counters.
- **Remaining:** none. Phase 22 is ELIGIBLE but NOT STARTED — do NOT start it.
