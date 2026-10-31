# Project MEMORY — D:\Softfors\jup

Hot index only. **Full detail → `NOTES_ARCHIVE.md` + dated logs (append-only).**
BARR-M1 trap wording → `NOTES_ARCHIVE.md` § BARR-M1 + `2026-10-27.md`; C1 → `2026-10-28.md`.

## MODEL IDENTITY — do not misstate (user correction 2026-10-21)
**RA-MedFiLM-BARR** = a **FiLM** model, **NOT teacher-student/distillation**. G=GlobalMedFiLM
(`src/models/film/global_medfilm.py`; FiLM at 5 sites, `F_hat=(1+γ(t))*F+β(t)`, γ/β=tanh, zero-init
out-proj) · R_psi=RegionalRefiner · B_phi=BenefitRouter · S_omega=PostSafety
(`src/models/barr/ra_medfilm_barr.py`). `D:\Softfors\teacher_student` is a protected **PATH**, not the
model. EXT-03 = non-FiLM baseline matrix, not student nets.

## HARD RULES
- Interpreter `D:\Softfors\jup\.venv\Scripts\python.exe`; repo `D:\Softfors\jup`.
- **NEVER touch `D:\Softfors\teacher_student`.** TEST is PHASE39-ONLY; ROUTER_HOLDOUT locked.
- SHA-256 = `Path(p).read_bytes()`. Write-once = `O_CREAT|O_EXCL|O_WRONLY|O_BINARY` + full-write loop +
  `os.fsync` + post-write `st_size`. Superseded artifacts **MOVED** to `_superseded_*`, never deleted.
- **NO `or` FALLBACK when resolving a registry key.** `r.get("best_sha256") or r.get("checkpoint_sha256")`
  + `ok = (exp is None) or (actual==exp)` = FAIL-OPEN. Key is **`checkpoint_sha`**; absent ⇒ ABORT.
  (This exact bug shipped in v1.1 Section C: 15/15 null, match=true.)
- Scientific delta = DISTINCT repair CLASSES; raw-hunk counts MUST NOT be reported as the delta.
  Unknown hunks stay UNCLASSIFIED and block the validator.
- Never hard-code a *derived* SHA; read from disk. Never hand-author a timestamp — compute it or label
  `AUTHOR_ENTERED_AT_WRITE`. `attempt_consumed = TRUE FOREVER`; never relaunch a consumed revision.

## HOST — CLOCK NOT SYNCHRONISED (measured 2026-10-26)
`w32tm` → `Leap Indicator: 3(not synchronized)`, `Source: Local CMOS Clock`, no successful sync ever;
service Stopped/Manual. RTC previously 5.19 d behind (ID 52, 448320 s). **All absolute timestamps carry
unquantified offset; only within-session ordering is trustworthy.** O8 (CMOS battery + UPS + NTP) must
precede any training. **No UPS enumerated**; KP41 85 in log, 0 since current boot.

## EXT-03 — v1.0 ADJUDICATED · v1.1 SUPERSEDED · v1.2 GOVERNANCE VERIFIED
15/15 COMPLETE, all `best.pt` SHA-verified. VAL808 macro Dice: deeplabv3plus **0.6657** (sd .0064) >
unetpp .6409 > attention_unet .6249 > segformer_b0 .5904 (sd .0051) > unet .5421 (sd .1572).
**All 15 REDUCED PROTOCOL** (Adam 1e-3, BCE-only, no aug; segformer 1e-4) — never cite as
protocol-faithful. D1 AdamW→Adam · D2 lr 1e-3 · D3 BCE-only · D4 no aug · D5 in_ch 1→3 · D6 segformer
(post-outcome + LR confound). v1.1 manifest `206ca0a8…` KEPT BYTE-FOR-BYTE incl. its null-SHA defect
(audit trail). v1.2 `reports/audits/ext03_disposition_v1_2/`, manifest `36fe4337…` (0 null).
**C1 FiLM · C2 BARR router+safety · C3 protocol-faithful baselines — ALL NOT_ESTABLISHED.**
GlobalMedFiLM ckpt has **ZERO router/safety tensors** ⇒ FiLM-off control is silent on BARR by
construction. **No safety-*specific* metric and NO `S_omega`-absent arm exists** (C2b not executable as
designed; `phase22_harm_analysis.json` defines *harm* — 536/808 — but is not a safety metric). AS-08
UNRESOLVED. FiLM-off control NOT authorised.
Params: total **3,523,001**; FiLM+emb **90,768 (2.58%)**. F1 freeze-at-init ⇒ total UNCHANGED, trainable
3,432,233. F2 remove ⇒ total 3,432,233. **Freezing never reduces total params.**
Protocol-faithful baseline study = provisional **`EXT-03B`** (EXT-04 frozen: AS-01..05,07 progression).

## BARR-M1 — DESIGN/APPROVAL READY, NOTHING AUTHORISED
= frozen Phase-28 arms **A0/A1/A8** (not an `EXT-` id). Manifests `fe91aadc…` / gate harness `e82ecdb7…`.
Terminals `BARR_M1_SCIENTIFIC_DESIGN_RECONCILED__AWAITING_AUTHORIZATION` /
`BARR_M1_APPROVAL_PACKAGE_READY__SCIENTIFIC_EXECUTION_NOT_AUTHORIZED`; **approval block NOT APPROVED**.
Traps (full wording → NOTES_ARCHIVE): **`POLICY_COMPARISON`, NOT router causal ablation** (A8 vs A1
differs in 4 fields ⇒ router not identifiable; only `A7_vs_A8` is pre-registered) · **"refine-all net
harmful" does NOT transfer** (Ph22 VAL808+ORACLE ROI −34.32 vs A1 DEV +8.219) · **harm-rate denominator
trap**: 32.37% = 390/1205 is CONDITIONAL on acceptance, so 42.67%→32.37% is INVALID; correct pairs are
unconditional 42.6670%→7.8677% and conditional 42.6670%→33.2526%→32.3651% · **IN-SAMPLE** (4957 ⊂ TRAIN
5832, VAL808+HOLDOUT consumed, TEST locked ⇒ no pristine population) · **ZERO GPU** (9/9 exact, 0
models/forwards) · SD 0.000590 = downstream retraining only · **join KEYED on `sample_id`** (order
differs 4955/4957) · frozen `mean_true_delta_dice_routed` is **POOLED**, not macro · `n_executed` is a
POLICY property.

## C1 — TECH READINESS (`0f9aadd`) then RELEASE FROZEN (`bdb0f9d`), NO EXECUTION
Terminals `RA_MEDFILM_BARR_C1_FINAL_TECHNICAL_READINESS_ASSESSED__SCIENTIFIC_EXECUTION_PENDING` /
`C1_LAUNCH_RELEASE_CANDIDATE_FROZEN__AUTHORIZATION_PENDING__NO_SCIENTIFIC_EXECUTION`. Protocol
`531e3eb2…` byte-identical. **CUDA backward nondeterministic** (interpolate/scatter): fwd bit-identical,
resume max|Δ| 2.82e-4 model / 1.82e-4 macro-Dice, selected epoch same ⇒ **never claim CUDA bitwise**;
CPU IS exact. VRAM at frozen recipe: TRAIN 512/B4/AMP reserved **3866 MiB** (of 8192), EVAL B8 2954.
`requirements.txt`/`pyproject` have **ZERO pins** — install torch `2.6.0+cu124` from cu124 index FIRST.
**NEVER flip `scientific_execution_enabled`** (breaks digest chain). Endpoint in-sample on
selection-consumed VAL808.

`src/research/c1_film_launch/` (additive; frozen pkg untouched) · **release_digest `1aec5e17…f93ff9c1`** ·
manifest `0e3f1719…` · **33 bound sources**, 8/8 `c1_film` modules. No circular hashing (manifest excludes
itself; digest=`sha256(canonical_json(manifest))`); coverage declared **in CODE** so an omitting manifest
fails. Two-phase gate — Phase A structural codes, Phase B trust with **`AUTHORIZED_ANCHOR_SHA256 = ()`
EMPTY BY DESIGN** ⇒ a complete, correctly-signed approval still fails
`C1_TRUST_ANCHOR_NOT_ALLOWLISTED`. `Trainer(...,grant=None)`; `run_real` keeps `approval`/`launch` kwargs
only to raise ReadinessError not TypeError. **Any bound-file edit voids the release** ⇒ re-run
`c1_launch_release_freeze.py` (editing a bound test ⇒ 42 failures until re-frozen). 102 tests + 23
subtests PASS; `c1_launch_release_verify.py` (imports nothing from the pkg) → `VERIFICATION_PASSED`.
Windows workers 4/2 verified; **worker-local augmentation RNG** ⇒ sample order identical but pixel
Δ ≤0.123 vs 0 workers; resume at fixed workers IS bit-exact. Endpoint ambiguity resolved additively
(`best_records`, recompute agrees 1e-6). Dep lock 104 pkgs (15 direct, `e9683c27…`), **clean-install NOT
verified**. `ENGINEERING_RELEASE_READY=true` · `HOST_READY=false` · approval=false · launch=false.
**Git byte-exactness:** `core.autocrlf=true` with **no `.gitattributes`** ⇒ a normal checkout yields CRLF
and FAILS the manifest (`global_medfilm.py` → `8f29fa3a…` vs bound `a04ff3e6…`, 297 CR injected), while
`control.py` (CRLF-bound, LF worktree) round-trips fine. 15/33 bound files CRLF, 18 LF ⇒ both directions
affected. Byte-exact round-trip needs `.gitattributes -text` + renormalise, which **changes committed
blobs** ⇒ deferred to a separately reviewed change.
7 formerly-untracked bound sources committed in **`fbc0af2`** ("chore(research): track C1 release-bound
scientific dependencies", 7 files, 944 insertions) — RC1 `bdb0f9d` NOT amended; digest unchanged.

## C1 RC2 — FROZEN `54794efc…a5e737ed` (additive; RC1 `1aec5e17…` UNTOUCHED)
`src/research/c1_film_launch_rc2/` · 9 bound · manifest `f5169ced…`. RC2 pins RC1 manifest+digest AND
re-verifies RC1's own identity. Trust = **EXTERNAL OS-scope store outside the repo**
(`%ProgramData%\InstitutionalC1Trust`): binding + policy **signed by the policy owner** ⇒ provisioning
is a DATA operation, **no release revision**. Ships 0 keys/0 policy ⇒ production UNPROVISIONED,
fail-closed. Refusals DIAGNOSTIC (5 codes) vs RC1's single code. Time = signed, identity-bound,
**single-use nonce vs durable on-disk ledger**; **`host_clock_trust = NOT_ESTABLISHED` always** ⇒
production training refused `C1_RC2_HOST_CLOCK_UNVERIFIED` (O8 still owed). `SYNTHETIC_TEST` grants
refused by BOTH `authorize_trainer` and `authorize_loader` (latter is the real-data path).
Honest limit: Python cannot resist in-process code execution; Windows ACL check is advisory.
Verified: 43 RC2 + 89 RC1(+23 subtests) + 22 CUDA + 13 MP; both verifiers PASS.
`.gitattributes` `-text`: 33 RC1 + 11 RC2 ⇒ checkout **33/33 & 9/9** under autocrlf true/false/input
(was 13/33). 0 remotes ⇒ `GIT_PUSH_STATUS: BLOCKED`. Detail → `2026-10-28.md`;
report → `reports/audits/c1_rc2_v1_0/`.

## C1 RC3 — `54d1273a…3549f` · TRUST BOUNDARY CONTAMINATED, LAUNCH NO-GO (2026-10-30)
RC3 (manifest `6cf2ffbd…45c01`, 8 bound) verifies, but **the gate refuses its own digest**:
`mint_rc3_grant(<RC3>)` → `C1_RC2_RELEASE_DIGEST_MISMATCH`; only **RC2** `54794efc…` passes, because
`mint_rc3_grant`→`rc2_mint_grant`→`verify_release_rc2` (requires `release_id==RC2`). `RC3_RELEASE_ID` /
`RC2_FROZEN_DIGEST` are **dead constants**; `verify_release_rc3` never called by gate/driver;
`RC3Grant.authorize_trainer` never checks `release_digest` ⇒ **identity downgrade to RC2 is the only
accepted path**. RC3 is authorization-inert. Do NOT "fix" by editing RC3.
`provision_trust_store.py` (untracked, now gitignored) generated **all 4 role keys in one process**
and signed policy/approval/instruction/attestation into `C:\ProgramData\InstitutionalC1Trust` +
`configs/c1_operator/`. **No private key persisted** (ephemeral). Store owner = researcher with
**FullControl**; `BUILTIN\Users` has **Write** ⇒ documented admin separation ABSENT. Root of trust is
**self-referential**: binding carries the owner public key that signs the policy.
Material is inert twice over: envelopes fail `C1_RC2_SIGNATURE_INVALID` (script signs inner payload;
verifier canonicalises envelope minus `signature`). NTP measurement itself was genuine.
**No grant minted · no nonce consumed · no dataset opened · no training.** Nothing deleted.
`C1_TRUST_BOUNDARY_CONTAMINATED__OPERATOR_REVIEW_REQUIRED__SCIENTIFIC_LAUNCH_NO_GO`.
Full detail → `2026-10-30.md`; report → `reports/audits/c1_trust_recovery_v1_0/`.

## PHASE36 — `NOT_COMPLETE_PENDING_V1_22_EXECUTION`, Phase37 NOT_STARTED
**v1.22 ELIGIBLE_NOT_STARTED (never executed)**; v1.20/v1.21 consumed or frozen; D95/D96 repaired.
Gate: `PHASE36_V1_22_EXECUTE=1` + `PHASE36_V1_22_LAUNCH_AUTHORITY`. **SHAs → NOTES_ARCHIVE.**
