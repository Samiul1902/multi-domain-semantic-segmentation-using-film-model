# Project MEMORY — D:\Softfors\jup

Hot index only. **Full detail → `NOTES_ARCHIVE.md` + dated logs (append-only).**

## MODEL IDENTITY — do not misstate (user correction 2026-10-21)
**RA-MedFiLM-BARR** = a **FiLM** model, **NOT** teacher-student/distillation. G=GlobalMedFiLM
(`src/models/film/global_medfilm.py`; FiLM at 5 sites, `F_hat=(1+γ(t))*F+β(t)`, γ/β=tanh, zero-init
out-proj) · R_psi=RegionalRefiner · B_phi=BenefitRouter · S_omega=PostSafety
(`src/models/barr/ra_medfilm_barr.py`). `D:\Softfors\teacher_student` is a protected **PATH**, not the
model. EXT-03 = non-FiLM baseline matrix, not student nets.

## HARD RULES
- Interpreter `D:\Softfors\jup\.venv\Scripts\python.exe` (py3.11.9, torch 2.6.0+cu124, RTX 3060 Ti 8 GB).
- **NEVER touch `D:\Softfors\teacher_student`.** TEST is PHASE39-ONLY; ROUTER_HOLDOUT locked.
- SHA-256 = `Path(p).read_bytes()`. Write-once = `O_CREAT|O_EXCL|O_WRONLY|O_BINARY` + full-write loop +
  `os.fsync` + post-write `st_size`. Superseded artifacts **MOVED** to `_superseded_*`, never deleted.
- **NO `or` FALLBACK when resolving a registry key.** Key is **`checkpoint_sha`**; absent ⇒ ABORT.
- Scientific delta = DISTINCT repair CLASSES; raw-hunk counts MUST NOT be reported as the delta.
- Never hard-code a *derived* SHA; read from disk. Never hand-author a timestamp.
  `attempt_consumed = TRUE FOREVER`.
- **Never claim a test ran if the interpreter cannot execute.** Report `NOT_RUN` + cause.

## HOST
Clock NOT synchronised (2026-10-26): `Leap Indicator: 3`, `Source: Local CMOS Clock`, no successful sync
ever. **All absolute timestamps carry unquantified offset**; only within-session ordering is trustworthy.
O8 (CMOS battery + UPS + NTP) owed. No UPS enumerated.
64-bit `python -c` segfault (2026-11-02, `0xc0000005`, module `unknown`) — **REPAIRED by 2026-11-03**;
torch/CUDA verified. Root cause never formally identified.

## POPULATION + THRESHOLDS (load-bearing, never conflate)
TRAIN 5832 / VAL 808 / TEST 1683. ROUTER_DEVELOPMENT 4957 + ROUTER_HOLDOUT 875 = 5832 (asserted).
`ROI_PROPOSAL_THRESHOLD=0.30` (bbox/action only) ≠ `SEGMENTATION_OUTPUT_THRESHOLD=0.50` (final mask/Dice);
`SOMEGA_ACCEPT_THRESHOLD=0.50`. Refiner runs **before** the S_omega gate ⇒ `refiner_forwards == selected`,
a rejected candidate already paid.

## EXT-03 — v1.0 ADJUDICATED · v1.1 SUPERSEDED · v1.2 GOVERNANCE VERIFIED
15/15 COMPLETE, all `best.pt` SHA-verified. VAL808 macro Dice: deeplabv3plus **0.6657** > unetpp .6409 >
attention_unet .6249 > segformer_b0 .5904 > unet .5421. **All 15 REDUCED PROTOCOL** (Adam 1e-3, BCE-only,
no aug) — never cite as protocol-faithful. v1.2 manifest `36fe4337…`.
**C1 FiLM · C2 BARR router+safety · C3 protocol-faithful baselines — ALL NOT_ESTABLISHED.**
GlobalMedFiLM ckpt has **ZERO router/safety tensors** ⇒ FiLM-off control silent on BARR; no
safety-*specific* metric, no `S_omega`-absent arm ⇒ C2b not executable. AS-08 UNRESOLVED.
Params **3,523,001**; FiLM+emb **90,768 (2.58%)**; F1 freeze-at-init ⇒ trainable 3,432,233.
**Freezing never reduces total params.**

## MATCHED-ARM INVARIANT — DO NOT MISREAD AS A DEFECT
`build_matched_arms`: `control = deepcopy(treatment)` then freeze ⇒ **C1-T and C1-C have IDENTICAL total
params (3,523,001) and IDENTICAL initial weights**. Trainable delta **90,768** = conditioning count. Never
assert a total-param difference or differing initial digests (my 2026-11-01 error). Proof:
`scripts/verification/c1_synthetic_chain_test.py` → `CHAIN_SOUND`.

## BARR-M1 — DESIGN READY, NOTHING AUTHORISED
Frozen Phase-28 arms **A0/A1/A8**. **approval block NOT APPROVED.** Traps: **`POLICY_COMPARISON`, NOT
router causal ablation** (A8 vs A1 differs in 4 fields; only `A7_vs_A8` pre-registered) · **"refine-all net
harmful" does NOT transfer** (Ph22 VAL808+ORACLE ROI −34.32 vs A1 DEV +8.219) · **harm-rate denominator
trap**: 32.37%=390/1205 is CONDITIONAL on acceptance ⇒ 42.67%→32.37% INVALID; correct 42.6670%→7.8677%
(uncond) and 42.6670%→33.2526%→32.3651% (cond) · **IN-SAMPLE** (4957 ⊂ TRAIN) · **ZERO GPU** · join
KEYED on `sample_id` (order differs) · frozen `mean_true_delta_dice_routed` is **POOLED** · `n_executed`
is a POLICY property. Internal 1239 = 1205 acc + 34 rej; external 184 = 139 + 45; workload **25.0%**.
Full detail → `NOTES_ARCHIVE.md` § BARR-M1.

## EXTERNAL 884 — `VERDICT CONSISTENT`, 0 failures
CVC 612 / BrEaST 252 / Stones 20. Global→BARR 68.66→68.97 · 70.78→70.81 · 8.08→8.21 pp. BrEaST
`270 = 252 + 4 + 14`; patient-level independence **NOT verifiable**. Stones `n_clusters=20` ⇒
**image-level descriptive**. **IQR exactly [0,0]** ⇒ "sits on zero", NEVER "straddles". Accepted-with-
negative-change: CVC 14, BrEaST 20, **Stones 0/9** ⇒ never fabricate a harmful Stones case.

## C1 RELEASES — RC1/RC2/RC3 frozen; RC4 = DECISION_I successor
RC1 `1aec5e17…f93ff9c1` · RC2 `54794efc…a5e737ed` · RC3 `54d1273a…3549f`.
**RC3 defect: gate refuses its own digest.** `mint_rc3_grant`→`rc2_mint_grant`→`verify_release_rc2`
(requires `release_id==RC2`); `verify_release_rc3` never called; `RC3Grant.release_digest` returns the RC2
digest. All 27 RC3 tests pass, **none presents the release with its OWN digest** ⇒ that is why it shipped.
Do NOT "fix" by editing RC3.
**RC4** `05a330d1…4eada2` (`src/research/c1_film_launch_rc4/`, 7 bound) verifies its OWN identity, refuses
RC1/RC2/RC3 digests, trust root `%ProgramData%\InstitutionalC1TrustRC4` — **UNPROVISIONED**.
`run_c1_campaign_launch.py` still hard-codes the RC3 digest; RC4 draft launcher raises
`C1_RC4_DRAFT_LAUNCHER_NOT_AUTHORIZED`. **No production CLI drives RC4 to training** = smallest missing step.

## C1 AUTHORITY — `DECISION_I` recorded conversationally; `DECISION_R` NEVER selected
`docs/c1_execution_authority_decision_v1_0.md`: form unsigned; **Addendum 2026-11-01 records `DECISION_I`**;
institutional approval PENDING, signatory NOT IDENTIFIED, key custody NOT ESTABLISHED. **`DECISION_R` is an
unselected OPTION — zero implementation references.** A Markdown signature is not software authorization.
`configs/c1_operator/approval.json` claims `Institutional Chief Scientist` — **agent-generated, never
existed**. `time_status.json` claims `VERIFIED/NTP` — **false**. Both MUST_NOT_BE_REUSED, both still on
disk untouched (evidence). Legacy store `C:\ProgramData\InstitutionalC1Trust` untouched;
`BUILTIN\Users`=Write ⇒ admin separation ABSENT.

## EXECUTION SURFACES — verified 2026-11-02
- C1-T/C1-C: `scripts/analysis/run_c1_campaign_launch.py [--execute]` → `launch_driver_rc3.launch` →
  `mint_rc3_grant` → `real_loader_factory` → `Trainer.run`. Preflight passes, gate refuses.
- Baselines: `scripts/analysis/stage6_eight_model.py baseline-run --model <M> --seed <S> [--resume]
  [--grant-provider MOD:CALLABLE]`. **No `--device`, no `--execute`.** `src/research/stage6/baseline_real.py`
  is a **library** (0 argparse, 0 `__main__`) ⇒ `python -m ...baseline_real` is a **silent no-op, exit 0**.
- Stage6 matrix: 8 models × `SEEDS=(42,123,3407)` ⇒ **24 cells**, all `MISSING` = **NOT_ESTABLISHED**.
- LITE `src/research/stage6/lite_chain.py`: `if not synthetic: raise LiteChainError(REAL_BLOCK)` ⇒
  synthetic-only; real needs cross-fitted OOF labels (`BLOCKED`).

## FULL PIPELINE (Phase A, 2026-11-03) — `src/research/full_pipeline/`
Single three-seed orchestrator, `STAGE_ORDER=("G","CACHE","R","L","B","S")`. CLI
`scripts/training/full_barr_three_seed.py {prepare,validate,plan,dry-run,run,resume,export}`.
Reuses canonical producers (BARRRefinerCropDataset, roi_geometry/extract_roi_triplet,
build_feature_vector, fuse_full_field, compute_numeric_features, GTFreeBARRInference, TapRecorder).
`BARRBenefitRouterV1`/`BARRPostSafetyV1` re-declared because canonical producers are non-importable scripts.
B/S cross-fit consumes the **frozen Phase-25D FIT/EARLY_STOP/OUTER_TARGET table** — never an invented
permutation. Real training raises `AuthorizationRequired` without a grant. Detail → `2026-11-03.md`.

## PHASE36 — `NOT_COMPLETE_PENDING_V1_22_EXECUTION`, Phase37 NOT_STARTED
**v1.22 ELIGIBLE_NOT_STARTED (never executed)**; v1.20/v1.21 consumed or frozen; D95/D96 repaired.
Gate: `PHASE36_V1_22_EXECUTE=1` + `PHASE36_V1_22_LAUNCH_AUTHORITY`. **SHAs → NOTES_ARCHIVE.**
