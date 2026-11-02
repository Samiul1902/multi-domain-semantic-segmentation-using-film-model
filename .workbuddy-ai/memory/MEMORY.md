# Project MEMORY — D:\Softfors\jup

Hot index only. **Full detail → `NOTES_ARCHIVE.md` + dated logs (append-only).**
BARR-M1 traps → `NOTES_ARCHIVE.md` § BARR-M1 + `2026-10-27.md` · C1 → `2026-10-28.md`…`2026-11-01.md`.

## MODEL IDENTITY — do not misstate (user correction 2026-10-21)
**RA-MedFiLM-BARR** = a **FiLM** model, **NOT** teacher-student/distillation. G=GlobalMedFiLM
(`src/models/film/global_medfilm.py`; FiLM at 5 sites, `F_hat=(1+γ(t))*F+β(t)`, γ/β=tanh, zero-init
out-proj) · R_psi=RegionalRefiner · B_phi=BenefitRouter · S_omega=PostSafety
(`src/models/barr/ra_medfilm_barr.py`). `D:\Softfors\teacher_student` is a protected **PATH**, not the
model. EXT-03 = non-FiLM baseline matrix, not student nets.

## HARD RULES
- Interpreter `D:\Softfors\jup\.venv\Scripts\python.exe`; repo `D:\Softfors\jup`.
- **NEVER touch `D:\Softfors\teacher_student`.** TEST is PHASE39-ONLY; ROUTER_HOLDOUT locked.
- SHA-256 = `Path(p).read_bytes()`. Write-once = `O_CREAT|O_EXCL|O_WRONLY|O_BINARY` + full-write loop +
  `os.fsync` + post-write `st_size`. Superseded artifacts **MOVED** to `_superseded_*`, never deleted.
- **NO `or` FALLBACK when resolving a registry key.** Key is **`checkpoint_sha`**; absent ⇒ ABORT.
  (`r.get("best_sha256") or r.get("checkpoint_sha256")` + `ok=(exp is None) or ...` = FAIL-OPEN; shipped
  in v1.1 §C: 15/15 null, match=true.)
- Scientific delta = DISTINCT repair CLASSES; raw-hunk counts MUST NOT be reported as the delta. Unknown
  hunks stay UNCLASSIFIED and block the validator.
- Never hard-code a *derived* SHA; read from disk. Never hand-author a timestamp — compute it or label
  `AUTHOR_ENTERED_AT_WRITE`. `attempt_consumed = TRUE FOREVER`.
- **Never claim a test ran if the interpreter cannot execute.** Report `NOT_RUN` + cause.

## HOST — CLOCK NOT SYNCHRONISED (2026-10-26) + CODE EXECUTION BROKEN (2026-11-02)
`w32tm` → `Leap Indicator: 3(not synchronized)`, `Source: Local CMOS Clock`, no successful sync ever;
service Stopped/Manual. **All absolute timestamps carry unquantified offset; only within-session ordering
is trustworthy.** O8 (CMOS battery + UPS + NTP) owed. **No UPS enumerated**; KP41 85 in log, 0 since boot.

**2026-11-02: `python -c <anything>` → exit 139 on EVERY invocation.** `python -V` still returns 0.
System Python 3.11.9 identical; **outside the sandbox identical**; `-S`/`-E`/`-I`/`-u` all fail;
`pytest` dies silently. **PowerShell also dies `0xC0000005`.** Native binaries (git, cmd, bash, sha256sum)
work. Supersedes the 2026-11-01 "cannot spawn processes" defect (that one at least ran `-c`).
⇒ No tests, no training, no hash-by-python. Static inspection only.

## EXT-03 — v1.0 ADJUDICATED · v1.1 SUPERSEDED · v1.2 GOVERNANCE VERIFIED
15/15 COMPLETE, all `best.pt` SHA-verified. VAL808 macro Dice: deeplabv3plus **0.6657** > unetpp .6409 >
attention_unet .6249 > segformer_b0 .5904 > unet .5421. **All 15 REDUCED PROTOCOL** (Adam 1e-3, BCE-only,
no aug) — never cite as protocol-faithful. v1.1 manifest `206ca0a8…` KEPT BYTE-FOR-BYTE incl. its null-SHA
defect. v1.2 `reports/audits/ext03_disposition_v1_2/`, manifest `36fe4337…` (0 null).
**C1 FiLM · C2 BARR router+safety · C3 protocol-faithful baselines — ALL NOT_ESTABLISHED.**
GlobalMedFiLM ckpt has **ZERO router/safety tensors** ⇒ FiLM-off control is silent on BARR. No
safety-*specific* metric and NO `S_omega`-absent arm ⇒ C2b not executable as designed. AS-08 UNRESOLVED.
Params total **3,523,001**; FiLM+emb **90,768 (2.58%)**; F1 freeze-at-init ⇒ trainable 3,432,233, total
UNCHANGED. **Freezing never reduces total params.**

## MATCHED-ARM INVARIANT — DO NOT MISREAD AS A DEFECT
`build_matched_arms`: `control = deepcopy(treatment)` then freeze ⇒ **C1-T and C1-C have IDENTICAL total
params (3,523,001) and IDENTICAL initial weights**. Trainable 3,523,001 vs 3,432,233, delta **90,768** =
conditioning count. Never assert a total-param difference or differing initial digests (my 2026-11-01
error). Chain proof: `scripts/verification/c1_synthetic_chain_test.py` → `CHAIN_SOUND`.

## BARR-M1 — DESIGN/APPROVAL READY, NOTHING AUTHORISED
= frozen Phase-28 arms **A0/A1/A8**. Manifests `fe91aadc…` / gate `e82ecdb7…`. **approval block NOT
APPROVED.** Traps: **`POLICY_COMPARISON`, NOT router causal ablation** (A8 vs A1 differs in 4 fields;
only `A7_vs_A8` pre-registered) · **"refine-all net harmful" does NOT transfer** (Ph22 VAL808+ORACLE ROI
−34.32 vs A1 DEV +8.219) · **harm-rate denominator trap**: 32.37% = 390/1205 is CONDITIONAL on
acceptance ⇒ 42.67%→32.37% INVALID; correct pairs 42.6670%→7.8677% (unconditional) and
42.6670%→33.2526%→32.3651% (conditional) · **IN-SAMPLE** (4957 ⊂ TRAIN 5832; VAL808+HOLDOUT consumed;
TEST locked) · **ZERO GPU** · SD 0.000590 = downstream retraining only · **join KEYED on `sample_id`**
(order differs 4955/4957) · frozen `mean_true_delta_dice_routed` is **POOLED**, not macro · `n_executed`
is a POLICY property.

## COMPUTE — `refiner_forwards == selected`, NOT accepted (settled 2026-10-31)
Refiner runs **before** the S_omega gate ⇒ a rejected candidate already paid. External: selected 184 =
139 acc + 45 rej. Internal: **1,239 = 1,205 acc + 34 rej** ⇒ that triple is the **internal BARR-M1
population**, never external. `A8.n_routed = 1,205` is an **ADOPTION count**; `A7.n_routed = 1,239`.
Workload **25.0%**, NOT 24.3% (defect was `build_verified_comparison_figures.py::fig3()`). Cost contract
preserved: `accept_reject_differ: false`; 2.345×10⁹ MAC saving at `p_activate = 27.43%`.

## EXTERNAL 884 — `VERDICT CONSISTENT`, 0 failures (2026-10-31, no re-inference)
CVC 612 / BrEaST 252 / Stones 20. Global→BARR 68.66→68.97 · 70.78→70.81 · 8.08→8.21 pp. BrEaST
`270 = 252 + 4 + 14` (14 `_other` views of 7 cases never in manifest + 4 excluded primaries); 252 distinct
`case_id`, patient-level independence **NOT verifiable**. Stones interval REAL (`n_clusters=20`) ⇒
**image-level descriptive**. 0/14 stone-absent predicted empty yet median TN 259,214/262,144 px ⇒
**case-level** failure. **IQR exactly [0,0]** (700/884 untouched) ⇒ "sits on zero", NEVER "straddles".
Accepted-with-negative-change: CVC 14, BrEaST 20, **Stones 0/9** ⇒ never fabricate a harmful Stones case.

## C1 RELEASES — RC1/RC2/RC3 frozen & intact; RC4 = DECISION_I successor
RC1 `1aec5e17…f93ff9c1` (33 bound) · RC2 `54794efc…a5e737ed` (9 bound) · RC3 `54d1273a…3549f` (8 bound).
**RC3 defect: gate refuses its own digest.** `mint_rc3_grant`→`rc2_mint_grant`→`verify_release_rc2`
(requires `release_id==RC2`); `RC3_RELEASE_ID`/`RC2_FROZEN_DIGEST` are dead constants; `verify_release_rc3`
never called; `RC3Grant.release_digest` → `self._rc2_grant.release_digest`. All 27 RC3 tests pass and
**none presents the release with its OWN digest** (only `"INVALID_DIGEST"`) ⇒ that is why it shipped.
Do NOT "fix" by editing RC3.
**RC4** `05a330d1…4eada2` (`src/research/c1_film_launch_rc4/`, manifest `edb8bfcf…`, 7 bound) verifies its
OWN identity, refuses RC1/RC2/RC3 digests, re-verifies at trainer/loader/launch, trust root
`%ProgramData%\InstitutionalC1TrustRC4` — **UNPROVISIONED (absent on disk)**. Digest file records
`authorization_model=DECISION_I`, `institutional_approval=PENDING`, `host_clock_trust=NOT_ESTABLISHED`,
`scientific_execution=NOT_AUTHORIZED`.
**No CLI drives RC4 to training.** `run_c1_campaign_launch.py` still hard-codes the RC3 digest;
`run_c1_campaign_launch_rc4_draft.py` → `campaign_rc4_draft.execute_campaign` with `execute=True` raises
`C1_RC4_DRAFT_LAUNCHER_NOT_AUTHORIZED` (`DRAFT_AUTHORIZED = False`, hardcoded). ⇒ RC4 is authorization-ready
in code but has **no production launcher**; that is the smallest missing implementation step.

## C1 AUTHORITY — `DECISION_I` recorded conversationally; `DECISION_R` NEVER selected
`docs/c1_execution_authority_decision_v1_0.md`: unsigned form blank + **Addendum 2026-11-01 records
`DECISION_I`** ("researcher's explicit choice communicated through ChatGPT"), institutional approval
PENDING, signatory NOT IDENTIFIED, key custody NOT ESTABLISHED. Commit `855cb25`.
**`DECISION_R` is an unselected OPTION — zero implementation references.** Do not treat a Markdown
signature as software authorization.
`configs/c1_operator/approval.json` claims `Institutional Chief Scientist` — **agent-generated, never
existed**. `time_status.json` claims `VERIFIED/NTP` — **false**. Both MUST_NOT_BE_REUSED, and both are
still on disk untouched (evidence). Legacy store `C:\ProgramData\InstitutionalC1Trust` (3 files,
2026-10-30 10:54) also untouched; owner researcher FullControl, `BUILTIN\Users` = Write ⇒ admin separation
ABSENT; root of trust self-referential.

## EXECUTION SURFACES — verified 2026-11-02
- C1-T/C1-C: `scripts/analysis/run_c1_campaign_launch.py [--execute]` → `launch_driver_rc3.launch` →
  `mint_rc3_grant` → `real_loader_factory` → `Trainer.run`. Real chain, preflight passes, gate refuses.
- Baselines: `scripts/analysis/stage6_eight_model.py baseline-run --model <M> --seed <S> [--resume]
  [--grant-provider MOD:CALLABLE]`. **No `--device`, no `--execute`.** `src/research/stage6/baseline_real.py`
  is a **library** (0 argparse, 0 `__main__`) ⇒ `python -m src.research.stage6.baseline_real ...` is a
  **silent no-op, exit 0**. `STAGE6_BASELINE_LAUNCH_GRANT_REQUIRED` with no grant provider.
- Stage6 matrix: `MODEL_KEYS = (FULL, LITE, GLOBAL, + 5 baselines)`, `SEEDS=(42,123,3407)` ⇒ **24 cells**,
  `build_cells()` marks every one `MISSING`. All 24 = **NOT_ESTABLISHED**.
- FULL producers all exist under `scripts/training/` (`train_phase21_global_medfilm.py`,
  `train_phase25a_refiner.py`, `phase25d_router.py`, `phase25f_execution_common.py`) but **no automated
  multi-seed G→R→B→S pipeline** (`multi_seed_producer: MISSING`).
- LITE `src/research/stage6/lite_chain.py`: `if not synthetic: raise LiteChainError(REAL_BLOCK)` ⇒
  synthetic-only; real needs cross-fitted OOF labels (`BLOCKED`).

## PHASE36 — `NOT_COMPLETE_PENDING_V1_22_EXECUTION`, Phase37 NOT_STARTED
**v1.22 ELIGIBLE_NOT_STARTED (never executed)**; v1.20/v1.21 consumed or frozen; D95/D96 repaired.
Gate: `PHASE36_V1_22_EXECUTE=1` + `PHASE36_V1_22_LAUNCH_AUTHORITY`. **SHAs → NOTES_ARCHIVE.**
