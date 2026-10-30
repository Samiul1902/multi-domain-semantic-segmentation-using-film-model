# Phase-20 keep-alive + completion driver — execution memory

Purpose: keep the single authorized Phase-20 run
(`phase20_shared_unetpp_fourdomain_seed42_clean_v3`, UNet++ shared four-domain,
seed 42, clean-v3) alive across harness teardown (~2 h) and, once it terminates
naturally, run `scripts/phase20_post_training_pipeline.py`.

Never: second seed / second experiment dir / hyperparameter change / epoch-1
restart / `schtasks` / `nohup` / TEST reads / Phase-21 start.

## Log of cycles

### Cycle 2026-09-26 01:02 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `experiments/.../closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) plus a `.venv/Scripts/python`
  companion and 4 worker processes spawned 00:59:48-00:59:57 -> ALIVE.
  - run log mtime 00:59; last line `EPOCH 009 ... macro=0.644731` (00:59:47).
  - `history.csv` = header + 9 rows (epochs 1-9), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 7 macro=0.671088; latest epoch 9 macro=0.644731; bad=2/15.
  `checkpoints/.../best.pt` (00:39) and `latest.pt` (00:59) both present ->
  resume is durable.
- Note: an earlier same-cycle relaunch is already recorded in the log — RUN START
  pid=6556 at 23:19:25 (died), then pid=1728 at 23:24:48 which logged
  "RESUME requested but no latest.pt found; starting from epoch 1" (the documented
  graceful degradation; this is NOT a protocol violation and must not be re-run).

### Cycle 2026-09-26 02:03 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; WINPID 1728 alive (`Python311\python.exe`, STIME 23:24:45)
  + 4 workers spawned 01:59:56-02:00:05 (epoch-16 workers) -> ALIVE.
  - run log mtime 01:59; last line `EPOCH 015 ... macro=0.701148` (01:59:56).
  - `history.csv` = header + 15 rows (epochs 1-15), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 13 macro=0.715905 (ISIC 0.8344 / BUSI 0.7508 / KVASIR 0.7046 /
  KUB 0.5738); latest epoch 15 macro=0.701148; bad=2/15.
  `best.pt` (01:39) and `latest.pt` (01:59) both present -> resume is durable.
- Cadence steady at 592-609 s/epoch, matching the ~11 min/epoch budget.
- Progress since last cycle: 9 -> 15 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 03:04 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 03:00:19-03:00:28 (epoch-22 workers) -> ALIVE.
  - run log mtime 03:00; last line `EPOCH 021 ... macro=0.756119` (03:00:19).
  - `history.csv` = header + 21 rows (epochs 1-21), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 21 macro=0.756119 (ISIC 0.8455 / BUSI 0.7878 / KVASIR 0.7052 /
  KUB 0.6860); latest = best; bad=0/15. Strong upward trend since epoch 13
  (0.7159 -> 0.7211 -> 0.7477 -> 0.7561) with KUB improving 0.5738 -> 0.6860.
- `checkpoints/phase20_.../best.pt` and `latest.pt` both present, both mtime 03:00
  -> resume is durable.
- Cadence steady 592-609 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 15 -> 21 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 04:06 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 04:00:40-04:00:49 (epoch-28 workers) -> ALIVE.
  - run log mtime 04:00; last line `EPOCH 027 ... macro=0.707397` (04:00:39).
  - `history.csv` = header + 27 rows (epochs 1-27), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 24 macro=0.767838 (ISIC 0.8464 / BUSI 0.8028 / KVASIR 0.7291 /
  KUB 0.6931); latest epoch 27 macro=0.707397; bad=3/15.
- `checkpoints/phase20_.../best.pt` (03:30) and `latest.pt` (04:00) both present
  -> resume is durable.
- Cadence steady 596-610 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 21 -> 27 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 05:06 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 05:01:35-05:01:44 (epoch-34 workers) -> ALIVE.
  - run log mtime 05:01; last line `EPOCH 033 ... macro=0.774746` (05:01:34).
  - `history.csv` = header + 33 rows (epochs 1-33), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 33 macro=0.774746 (ISIC 0.8361 / BUSI 0.8205 / KVASIR 0.7624 /
  KUB 0.6800); latest = best; bad=0/15. New bests at 30 (0.771434) then 33
  (0.774746) — new high-water mark for the run.
- `checkpoints/phase20_.../best.pt` and `latest.pt` both present, both mtime 05:01
  -> resume is durable.
- Cadence steady 598-620 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Note: epoch 32 shows a transient KUB collapse (KUB 0.2490, macro 0.6575) that
  recovered fully at epoch 33 — an unstable epoch, not a divergence; bad counter
  correctly returned to 0. Worth watching but no intervention warranted.
- Progress since last cycle: 27 -> 33 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 06:09 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `experiments/.../closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 06:08:06-06:08:15 (epoch-40 workers) -> ALIVE.
  - run log mtime 06:08; last line `EPOCH 040 ... macro=0.782112` (06:08:06).
  - `history.csv` = header + 40 rows (epochs 1-40), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 38 macro=0.782401 (ISIC 0.8539 / BUSI 0.7845 / KVASIR 0.7619 /
  KUB 0.7294); latest epoch 40 macro=0.782112; bad=2/15. Epoch 38 set a new
  high-water mark (prev best 33 = 0.774746); epoch 40 nearly matched it, so the
  run is plateauing near ~0.782 with the best checkpoint protected.
- Checkpoint dir is `checkpoints/phase20_.../` at repo root (NOT under
  `experiments/`): `best.pt` (05:49) and `latest.pt` (06:08) both present
  -> resume is durable.
- Cadence steady 549-582 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 33 -> 40 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 07:12 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `experiments/.../closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 07:09:22-07:09:31 (epoch-47 workers) -> ALIVE.
  - run log mtime 07:09; last line `EPOCH 046 ... macro=0.771276` (07:09:21).
  - `history.csv` = header + 46 rows (epochs 1-46), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 38 macro=0.782401 (ISIC 0.8539 / BUSI 0.7845 / KVASIR 0.7619 /
  KUB 0.7294); latest epoch 46 macro=0.771276; **bad=8/15**. Epochs 39-46 all in the
  0.736-0.781 band without beating epoch 38 -> plateau near ~0.78. Early stop would
  fire at bad=15 (epoch ~53) if no new best appears.
- `checkpoints/phase20_.../best.pt` (05:49) and `latest.pt` (07:09) both present
  -> resume is durable.
- Cadence steady 549-633 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 40 -> 46 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 08:13 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `experiments/.../closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 08:09:46-08:09:55 (epoch-53 workers) -> ALIVE.
  - run log mtime 08:09; last line `EPOCH 052 ... macro=0.784205` (08:09:46).
  - `history.csv` = header + 52 rows (epochs 1-52), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 49 macro=0.788822 (ISIC 0.8652 / BUSI 0.8043 / KVASIR 0.7523 /
  KUB 0.7335); latest epoch 52 macro=0.784205; bad=3/15. Epoch 49 set a new
  high-water mark (prev best 38 = 0.782401); epoch 52 nearly matched it.
  Early stop would fire at bad=15 (epoch ~61) if no new best appears.
- `checkpoints/phase20_.../best.pt` and `latest.pt` both present -> resume is durable.
- Cadence steady 549-633 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 46 -> 52 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 09:14 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `experiments/.../closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 09:12:02-09:12:11 (epoch-59 workers) -> ALIVE.
  - run log mtime 09:12; last line `EPOCH 058 ... macro=0.790560` (09:12:02).
  - `history.csv` = header + 58 rows (epochs 1-58), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 55 macro=0.792007 (ISIC 0.8601 / BUSI 0.8163 / KVASIR 0.7710 /
  KUB 0.7207); latest epoch 58 macro=0.790560; bad=3/15. Epoch 55 set a new
  high-water mark (prev best 49 = 0.788822); epochs 56-58 stayed in the
  0.778-0.791 band, just under it. Early stop would fire at bad=15 (~epoch 70)
  if no new best appears.
- `checkpoints/phase20_.../best.pt` (08:41) and `latest.pt` (09:12) both present
  -> resume is durable.
- Cadence steady 603-648 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 52 -> 58 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 10:21 (+06) — STEP 2, trainer ALIVE, no action
- STEP 1: `experiments/.../closure.json` ABSENT -> training unfinished -> STEP 2.
- STEP 2: lock pid=1728; `ps -W | grep python` shows WINPID 1728 alive
  (`Python311\python.exe`, STIME 23:24:45) + `.venv/Scripts/python` companion
  + 4 workers spawned 10:16:55-10:17:05 (epoch-65 workers) -> ALIVE.
  - run log mtime 10:16; last line `EPOCH 064 ... macro=0.778184` (10:16:55).
  - `history.csv` = header + 64 rows (epochs 1-64), consistent.
- Action: none. No relaunch (correct per protocol). No second run started.
- State: best epoch 55 macro=0.792007 (ISIC 0.8601 / BUSI 0.8163 / KVASIR 0.7710 /
  KUB 0.7207); latest epoch 64 macro=0.778184 (ISIC 0.8673 / BUSI 0.7992 /
  KVASIR 0.7657 / KUB 0.6805); **bad=9/15**. Epochs 56-64 all sit in the
  0.769-0.790 band, none beating epoch 55 -> plateau near ~0.79. Early stop fires
  at bad=15, i.e. ~epoch 70 if no new best appears.
- `checkpoints/phase20_.../best.pt` (08:41) and `latest.pt` (10:16) both present
  -> resume is durable.
- Cadence steady 589-659 s/epoch. `RUN START` count in log = 2 (both historical,
  no new launch added).
- Progress since last cycle: 58 -> 64 completed epochs in ~1 h; no intervention needed.

### Cycle 2026-09-26 11:22 (+06) — STEP 1 -> STEP 4, TRAINING TERMINATED, pipeline COMPLETE
- STEP 1: `experiments/.../closure.json` **PRESENT** (11:21) -> training terminated -> STEP 4.
  (STEP 2/3 skipped: no liveness check, no relaunch.)
- Training: best epoch **55** macro-domain Dice **0.792007328746103** (ISIC 0.860071 /
  BUSI 0.816301 / KVASIR 0.770995 / KUB 0.720662); final epoch 70;
  `EARLY_STOPPING_PATIENCE`; 70 epochs / 43001 s; history = header + 70 rows.
- STEP 4 first check: the 3 completion artifacts were MISSING at 11:22, BUT the pipeline
  was already RUNNING — launched 11:21:52 by a **concurrent WorkBuddy session**
  (`python -u scripts/phase20_post_training_pipeline.py 2>&1 | tail -60`, parent bash
  payload `codebuddy-shell-payload-25208`). Correct action taken: **do NOT launch a
  second instance** (the "one canonical pass" rule); monitored to completion instead.
- Pipeline result: ALL STAGES PASS.
  - 1/4 closure+replay -> `PHASE20_CHECKPOINT_SELECTION_REPLAY_PASS`
  - 2/4 canonical VAL eval -> 808/808 samples, 1 inference pass, 808 prob + 808 pred
    persisted, `test_reads` all 0, 123 s
  - 3/4 analysis -> tables/confusion matrices/calibration/bootstrap CIs/KUB subgroups +
    size strata/64-case gallery (16 pages) present
  - `phase20_phase21_entry_criteria.json`: **12/12 met**, `phase21_may_start=false`
  - `phase20_notebook_determinism.json`: SHA `367f5e54...` identical builds #2/#3,
    `deterministic: true`; notebook 61 cells / 30 code / 30 executed / 0 errors
- Watch-outs for future cycles:
  - A **concurrent session** patched `scripts/notebooks/build_phase20_notebook.py` (11:26)
    and `scripts/phase20_post_training_pipeline.py` (11:27, now 5 steps with analysis
    pass B + THREE notebook builds), re-ran the pipeline, then edited
    `scripts/audits/sync_phase20_registries.py` (11:33). Do not edit/re-run those scripts
    while that session works; and note the pipeline file's own schema changed from
    `build_1_sha256/build_2_sha256` to `final_notebook_sha256/rebuild_sha256`.
  - Remaining MANUAL step (not this automation's remit): registry/README/MASTER_PLAN
    synchronization + the 71-item final report.
  - Terminal state: `PHASE20_SHARED_GLOBAL_BASELINE_COMPLETE__PHASE21_ELIGIBLE_NOT_STARTED`.
    Phase 21 NOT started. TEST reads 0. No frozen code modified by this automation.

## Standing operational notes
- Liveness must use git-bash `ps -W | grep python`; `tasklist //FI` and bare
  `Get-Process python` are unreliable on this host.
- **`ps -W` output does NOT include command lines** — to identify a *specific* script
  (e.g. pipeline vs trainer), use PowerShell
  `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*<script>*" }`.
  Grepping `ps -W` for a script name always returns 0 and yields a false "process gone".
- Relaunch command (STEP 3) must use the Bash tool with `run_in_background: true`,
  `--resume --recover-stale-lock`, appending to the same run log.
- Epoch cadence observed ~549-690 s (~9-11.5 min), matching the ~11 min/epoch budget.
- Phase-20 checkpoint dir is `checkpoints/phase20_shared_unetpp_fourdomain_seed42_clean_v3/`
  at the REPO ROOT (there is no `experiments/.../checkpoints/` path).
- Post-training pipeline (STEP 4) is considered already complete only when all of
  `reports/audits/phase20_phase21_entry_criteria.json`,
  `reports/audits/phase20_notebook_determinism.json`, and
  `notebooks/phasewise/phase_20_multidomain_baselines/phase20_shared_global_unetpp_baseline.ipynb`
  exist; otherwise run `scripts/phase20_post_training_pipeline.py` and report the
  first failing step verbatim without patching frozen scientific code.
