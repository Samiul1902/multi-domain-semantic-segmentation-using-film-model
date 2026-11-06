# Project MEMORY — D:\Softfors\jup

**Hot index only.** Full detail → `NOTES_ARCHIVE.md` + dated logs `YYYY-MM-DD.md` (append-only).
Never re-derive numbers settled there. Condensed 2026-11-04; nothing deleted, detail archived.

## MODEL IDENTITY — do not misstate
**RA-MedFiLM-BARR** is **FiLM**, NOT teacher-student/distillation. G=GlobalMedFiLM
(`src/models/film/global_medfilm.py`, 5 FiLM sites, `F_hat=(1+γ)*F+β`, zero-init out-proj) ·
R_psi=RegionalRefiner · B_phi=BenefitRouter · S_omega=PostSafety (`src/models/barr/ra_medfilm_barr.py`).
`D:\Softfors\teacher_student` is a protected **PATH**, not the model. EXT-03 = non-FiLM baseline matrix.

## HARD RULES
- Interpreter `D:\Softfors\jup\.venv\Scripts\python.exe` (py3.11.9, torch 2.6.0+cu124, 3060 Ti 8 GB).
- **NEVER touch `D:\Softfors\teacher_student`.** TEST1683 is PHASE39-ONLY; ROUTER_HOLDOUT locked.
- SHA-256 = `Path(p).read_bytes()`. Write-once = `O_CREAT|O_EXCL|O_WRONLY|O_BINARY` + full-write +
  `os.fsync` + post-write `st_size`. Superseded artifacts **MOVED** to `_superseded_*`, never deleted.
- **NO `or` FALLBACK resolving a registry key.** Key is **`checkpoint_sha`**; absent ⇒ ABORT.
- Scientific delta = DISTINCT repair CLASSES, never raw-hunk counts.
- Never hard-code a *derived* SHA (read disk); never hand-author a timestamp. `attempt_consumed=TRUE FOREVER`.
- **Never claim a test ran if the interpreter cannot execute** ⇒ `NOT_RUN` + cause.
- Generic synthetic unit tests ≠ a required frozen smoke test / phase gate.

## HOST
Clock NOT synchronised (`Leap Indicator: 3`, Local CMOS, no sync ever) ⇒ absolute timestamps carry
unquantified offset; only within-session ordering trustworthy. No UPS enumerated. 64-bit `python -c`
segfault (2026-11-02, `0xc0000005`) **REPAIRED 2026-11-03**; root cause never formally identified.

## POPULATION + THRESHOLDS (load-bearing, never conflate)
TRAIN 5832 / VAL 808 / TEST 1683. ROUTER_DEV 4957 + ROUTER_HOLDOUT 875 = 5832.
`ROI_PROPOSAL_THRESHOLD=0.30` (bbox/action) ≠ `SEGMENTATION_OUTPUT_THRESHOLD=0.50` (final mask/Dice);
`SOMEGA_ACCEPT_THRESHOLD=0.50`. Refiner runs **before** S_omega ⇒ `refiner_forwards == selected`.

## SCIENTIFIC STATUS (never overstate; detail → archive/logs)
- **EXT-03** v1.0 adjudicated (15/15, ALL REDUCED PROTOCOL — never cite as protocol-faithful), v1.1
  superseded, v1.2 verified. VAL808 Dice deeplabv3plus .6657 > unetpp .6409 > attention_unet .6249 >
  segformer_b0 .5904 > unet .5421. **C1 FiLM / C2 BARR / C3 faithful baselines ALL NOT_ESTABLISHED**;
  GlobalMedFiLM ckpt has ZERO router/safety tensors; AS-08 unresolved. Params 3,523,001; FiLM+emb
  90,768 (2.58%); trainable 3,432,233. **Freezing never reduces total params.**
- **MATCHED-ARM INVARIANT (not a defect):** `control=deepcopy(treatment)` ⇒ C1-T/C1-C IDENTICAL total
  params (3,523,001) AND initial weights; trainable delta 90,768. Proof `c1_synthetic_chain_test.py`
  → `CHAIN_SOUND`. Never assert a total-param difference.
- **BARR-M1** DESIGN READY, approval NOT APPROVED. POLICY_COMPARISON not causal ablation;
  32.37%=390/1205 is CONDITIONAL (correct uncond 42.6670%→7.8677%); IN-SAMPLE; ZERO GPU; join keyed
  on `sample_id`; `n_executed` is a POLICY property. Traps → `NOTES_ARCHIVE.md` § BARR-M1.
- **EXTERNAL 884** VERDICT CONSISTENT, 0 failures (CVC 612 / BrEaST 252 / Stones 20). IQR exactly
  [0,0] ⇒ "sits on zero", never "straddles". Stones 0/9 negative-change ⇒ never fabricate a harmful
  Stones case. BrEaST patient-level independence NOT verifiable.
- **C1 RELEASES:** RC1/2/3 frozen. RC3 defect = gate refuses its OWN digest (`verify_release_rc3`
  never called; `release_digest` returns RC2's); 27 tests pass because none presents its own digest —
  do NOT fix by editing RC3. RC4 verifies its own identity, trust root UNPROVISIONED, no production
  CLI drives it to training. **`DECISION_R` = unselected OPTION, zero implementation refs**; `DECISION_I`
  conversational only; approval/signatory/key custody all PENDING. `configs/c1_operator/approval.json`
  + `time_status.json` are agent-generated falsehoods — MUST_NOT_BE_REUSED, kept on disk as evidence.
- **SURFACES:** `run_c1_campaign_launch.py [--execute]` preflight passes, gate refuses.
  `stage6_eight_model.py baseline-run` has NO `--device`/`--execute`; `baseline_real.py` is a library
  ⇒ `python -m` silent no-op exit 0. Stage6 = 24 cells ALL MISSING = NOT_ESTABLISHED. Lite
  `lite_chain.py` synthetic-only; real BLOCKED on cross-fitted OOF labels.

## PIPELINE CODE (verified; real training NEVER started)
- **FULL Phase A** `src/research/full_pipeline/`: `STAGE_ORDER=("G","CACHE","R","L","B","S")`, 3 seeds,
  CLI `scripts/training/full_barr_three_seed.py`; real training raises `AuthorizationRequired`.
  **OOF BOUNDARY: refiner/router/safety OOF=TRUE, backbone OOF=FALSE** ⇒ ΔQ backbone-in-sample, harm
  rates optimistic; recorded by `label_stage.oof_contract()`, deliberately NOT repaired.
  G 3,523,001 · R 1,276,401 · B 36,801 · S 1,217 = **4,837,420**.
- **PHASE B Lite** (`496c8d6`) `src/research/lite_pipeline/`: 6-stage DAG, adapters not forks,
  `oof_contract` v2 `backbone_out_of_fold=False` asserted. Reduction **94.3647 %** vs 4,837,420;
  **92.2623 % = WRONG denominator**. Lite graph **272,601**; **1,586,817 FABRICATED — never cite**.
  Full suite **1040 tests / 1 failed / 1 xfail** (RC2 host-specific, deliberately NOT repaired).
- **PHASE C** unified eval + stats: CODING ONLY; four real defects found and fixed; torn-append
  semantics verified → `2026-11-03.md`.

## PHASE36
`NOT_COMPLETE_PENDING_V1_22_EXECUTION`; Phase37 NOT_STARTED. **v1.22 ELIGIBLE_NOT_STARTED (never
executed)**; v1.20/21 consumed or frozen; D95/D96 repaired. Gate `PHASE36_V1_22_EXECUTE=1` +
`PHASE36_V1_22_LAUNCH_AUTHORITY`. SHAs → `NOTES_ARCHIVE.md`.
