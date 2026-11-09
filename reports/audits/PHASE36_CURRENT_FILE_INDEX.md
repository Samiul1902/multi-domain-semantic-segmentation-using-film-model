# PHASE36 CURRENT FILE INDEX (NON-AUTHORITATIVE NAVIGATION ONLY)

**STATUS: NAVIGATION AID — NOT A SCIENTIFIC AUTHORITY.**
This file is a human-readable map of the CURRENT Phase36 (RA-MedFiLM-BARR robustness)
source-repair chain. It is **NOT** a frozen contract, **NOT** a gate, **NOT** an evidence
artifact, and **NOT** a substitute for any runtime-integrity manifest, source freeze, or
eligibility record. If this index ever disagrees with any frozen artifact, **the frozen
artifact wins**. No file listed here is moved, renamed, duplicated, or deleted by the
creation of this index.

- **Current version:** v1.14 (governance repair; **one successful synthetic smoke CONSUMED**; science release ATTESTED; **science attempt CONSUMED/FAILED** at the clean-equivalence gate).
- **Predecessors (frozen, byte-preserved):** v1.13 (interpreter/CUDA pre-dispatch readiness; **never consumed, not authorized by supervisor** — D40–D43 defects), v1.12 (launch-anchor convergence; retry FORBIDDEN). Both **HISTORICAL / FROZEN**.
- **Scientific execution:** v1.14 science **CONSUMED — FAILED** (`CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION`); retry **FORBIDDEN**; D44 recorded (full `eq` not durably preserved). **Smoke:** v1.14 **CONSUMED_SUCCESS** — one attempt, `smoke_all_pass=true` 53/53, retry **FORBIDDEN**.
- **Clean-equivalence diagnostic v1.0:** PREPARED (`ELIGIBLE_NOT_STARTED`) — static audit `STATIC_ROOT_CAUSE_NOT_ESTABLISHED`; durable-`eq` diagnostic harness + launcher prepared; **NO execution**.
- **Post-smoke adjudication:** PASS — 62/62 facts (`phase36_v1_14_post_smoke_adjudication.json`).
- **Science-release attestation:** WRITTEN ONCE (`phase36_v1_14_science_release_attestation.json`), binds exec bytes + write-once smoke bytes; D40 non-dispatch gate = **RELEASED**.
- **v1.12 first smoke attempt:** CONSUMED, FAILED_PRE_MODEL (wrong interpreter — CPU-only torch build). **PRESERVED.**
- **v1.13:** never consumed (no smoke/science run). Preserved byte-unchanged.
- **Phase37:** NOT_STARTED. **TEST:** REMAINS_PHASE39_ONLY (closed). **ROUTER_HOLDOUT:** off-limits.
- **All hashes below are on-disk BYTE SHA-256** (`sha256sum` over raw bytes; CRLF preserved).
  Do not recompute with text-mode reads — that normalizes CRLF→LF and desynchronizes the hash.

---

## PHASE36 v1.14 — POST-SMOKE UPLOAD SET (HISTORICAL / PRE-SCIENCE)

> **HISTORICAL / PRE-SCIENCE (navigation banner only — no scientific revision, no frozen artifact
> modified).** These 6 files were the pre-science upload set captured at the moment the v1.14 smoke
> passed and the science-release attestation was written. The state statement below ("science
> ELIGIBLE_NOT_STARTED") is **superseded**: the sole authorized v1.14 science attempt was subsequently
> **CONSUMED — FAILED** at the clean-equivalence gate
> (`CLEAN_EQUIVALENCE_GATE_FAILED__STOP_BEFORE_PERTURBATION`). See the top-level STATUS and the
> "CLEAN EQUIVALENCE DIAGNOSTIC v1.0" section for the current state. Retained for lineage only.

Upload these 6 files to review the successful v1.14 synthetic smoke and the science-release
attestation. Smoke is **CONSUMED_SUCCESS** (retry FORBIDDEN); science is
**ELIGIBLE_NOT_STARTED** with the D40 release gate **RELEASED**; **no science was executed**.

| # | File | SHA-256 (bytes) |
|---|---|---|
| 1 | `reports/audits/phase36_robustness_smoke_start_v1_14.json` | `e7c685e37eb23de0105b6d487be88437cf60c4c3ffc970668207db120cfbfca1` |
| 2 | `reports/audits/phase36_robustness_smoke_v1_14.json` | `53543729fb0c48695c2af202c5f3d2f5ebdfc29d87c7a7f100bcde9f94882441` |
| 3 | `reports/audits/phase36_v1_14_post_smoke_adjudication.json` | `ee52a9cc32d8c71effb6d867ce0675eb1cfb956966cebe5e045a01197393e079` |
| 4 | `reports/audits/phase36_v1_14_science_release_attestation.json` | `1045123ad03f953aca5da530c1de303b4db32c4412c5ea92749f11d6f1bb5682` |
| 5 | `reports/audits/phase36_science_eligibility_post_smoke_v1_14.json` | `d4c8b4200772a5acad57295ff36d2f52488cdf9b353af2dfc0d3aee6edce77d1` |
| 6 | `reports/audits/phase36_v1_14_post_smoke_release_no_science_execution_audit.json` | `87643647d62aa1ee438ef89053c98bc294c1c9187e784dbae389ab8b7445794f` |

**State (HISTORICAL — captured at the pre-science point):** smoke `CONSUMED_SUCCESS` (retry FORBIDDEN) ·
science `ELIGIBLE_NOT_STARTED` → **now CONSUMED/FAILED** · release gate `RELEASED`
(`POST_SMOKE_RELEASE_ADJUDICATION`) · Phase37 `NOT_STARTED` · TEST `REMAINS_PHASE39_ONLY`.

---

## PHASE36 — CLEAN EQUIVALENCE DIAGNOSTIC v1.0 (PREPARATION / NO EXECUTION)

The one authorized v1.14 science attempt is **CONSUMED — FAILED** at the clean-equivalence
gate; retry of v1.14 is **FORBIDDEN**. This section lists the PREPARED (never executed)
diagnostic deliverable set that (a) reconciled the failure forensics, (b) ran a targeted
static authority audit (verdict `STATIC_ROOT_CAUSE_NOT_ESTABLISHED`), and (c) prepared a
durable-`eq` clean diagnostic harness. **No model, checkpoint, VAL image, or GT was read in
preparing this set; `scientific_output=false` throughout.**

| # | File | Purpose | SHA-256 (bytes) |
|---|---|---|---|
| 1 | `reports/audits/phase36_v1_14_science_failure_forensic_reconciliation_v2.json` | Additive forensic reconciliation v2 (binds 5 SHAs; corrections R1 dispatch-mechanism-not-resolved, R2 `H_dice_comparisons_808` not statically ruled out). | `cc9a3b502f59e3855c395b9d6afa2f5616f513d60af4756e4477a9370889cc3c` |
| 2 | `reports/audits/phase36_clean_equivalence_targeted_static_audit_v1_0.json` | Targeted static authority audit → **`STATIC_ROOT_CAUSE_NOT_ESTABLISHED`** (0 static defects; threshold provenance, Dice definition, GT construction, branch/safety, feature/runtime all PROVEN equivalent). | `8def086c44a7e80461c729f41ab61c0be347ef1589c94d6884a082adbde64ed4` |
| 3 | `scripts/analysis/phase36_clean_equivalence_diagnostic_v1_0.py` | Durable-`eq` clean diagnostic (imports frozen v1.14 callables; steps 1–7 only; write-once start/result/failure; one-shot `PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1`). | `7cc51cceacfa314d7f84acb8a6dc482a2b46ea81de0ec695c0c8f0ca8b0b50f7` |
| 4 | `scripts/analysis/launch_phase36_clean_equivalence_diagnostic_v1_0.py` | Diagnostic launcher (pins diagnostic + frozen v1.14 exec `ac09ff8d…` + manifest `b4c358df…`; `--verify-only` non-dispatching; no auto-relaunch). | `a34923faf6c27dd741ee1a1a1b4d1cbef1233664c2b02825e53b42c22c75b228` |
| 5 | `scripts/analysis/phase36_clean_equivalence_diagnostic_unit_v1_0.py` | Diagnostic unit suite (**26/26 pass**). | `33e72386699aa0100c314846ffe2592f740ca7fb76e926a704cf4d46fbf78bf5` |
| 6 | `scripts/analysis/phase36_clean_equivalence_diagnostic_preflight_v1_0.py` | Diagnostic static preflight (**29/29 pass**). | `92c2d855e931d037e965d862a2ce0feb091d53e1bff0f91020f85729842e6653` |

**Diagnostic governance artifacts (`reports/audits/`):**

| File | SHA-256 (bytes) |
|---|---|
| `phase36_clean_equivalence_diagnostic_contract_v1_0.json` | `2f9b59818180bc62e39c483a95a16a774004bb3d851706ac97fa2abd741a9b64` |
| `phase36_clean_equivalence_diagnostic_source_freeze_v1_0.json` | `3bade02b0c4e0fdfbb9120893d932f926aaa04fe3f533fb7bb64ddfb654ff8f8` |
| `phase36_clean_equivalence_diagnostic_preflight_v1_0.json` | `7c423ded09f5791a005d4586a9ef79c6088173f1ea7c7588cb11c33707f92e08` |
| `phase36_clean_equivalence_diagnostic_eligibility_v1_0.json` | `d7e6bcead9df4fbb3047dbc48464cff0293f7d6e3ddb99a1252a5378366df448` |
| `phase36_clean_equivalence_diagnostic_no_execution_audit_v1_0.json` | `b6e37d97c0bd52ebe8535a75828b2e802a4df0fa6751088aa6e2173df536a7c3` |

**Diagnostic state:** `ELIGIBLE_NOT_STARTED` · one-shot · `automatic_retry=false` ·
requires `PHASE36_CLEAN_EQ_DIAGNOSTIC_EXECUTE=1` + canonical venv interpreter + CUDA ·
v1.14 science retry **FORBIDDEN** · Phase37 `NOT_STARTED` · TEST `REMAINS_PHASE39_ONLY`.

---

## PHASE36 v1.14 — PRE-SMOKE (historical; superseded by the post-smoke set above)

Upload these files first. They are the v1.14 deliverable set: the D40–D43 governance
repair (machine-enforced science eligibility + non-tautological validator + smoke-check-ID
accounting + raw-byte transform proof) with all v1.13 predecessors preserved byte-unchanged.

> **Run the launcher with the canonical interpreter ONLY:**
> `D:\Softfors\jup\.venv\Scripts\python.exe scripts\analysis\launch_phase36_v1_14.py --mode smoke --verify-only`
> A bare-system-`python` invocation FAILS CLOSED with
> `PHASE36_V1_14_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED` and does NOT consume the revision.
>
> **Science is released ONLY after a successful v1.14 smoke + a bound post-smoke release
> attestation.** Absent that, `--mode science` FAILS CLOSED before the token / exec import /
> marker with `PHASE36_V1_14_SCIENCE_NOT_RELEASED__SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED`.

### `scripts/analysis/`
| File | Purpose | SHA-256 (bytes) |
|---|---|---|
| `phase36_robustness_execution_v1_14.py` | v1.14 execution source. Raw-byte governance token revision of frozen v1.13 **plus** the additive D40 science-release gate (main() call + appended block). 4382 lines, CRLF. **D43: untransform ⇒ byte-identical to frozen v1.13 ⇒ `new_scientific_choice=false`.** | `ac09ff8ded3610244920e66612145b246b33127140d344a9730d454bab27cff5` |
| `launch_phase36_v1_14.py` | Production launcher. Carries D37/D38/D39 + **new D40** pre-dispatch science-release gate (after verify-only stop, before token/exec-import). Literal frozen SHAs; no env override. | `2339d6afa1507d68decd1b63b3f3250d86ecd01659580394c6f8dace4052e2c3` |
| `phase36_robustness_unit_v1_14.py` | Unit suite (38/38 pass): D40–D43 + preserved D22–D39. Report SHA `4790a2bc…`. | `f837de2421ca464910b1b41c1ac29c5eae8fb686ba01e8b41fc499305b8ab7e7` |
| `phase36_robustness_preflight_v1_14.py` | Static preflight (24/24 pass). Report SHA `bef3bd42…`. | `5ef73cc0a468c736ebce577c7be8186adbd37996ec48ddb29ed43e9c341143b8` |
| `phase36_robustness_negative_controls_v1_14.py` | Negative controls NC115–NC138 (25/25 pass). Report SHA `36b8cb13…`. | `640b69b158018885a8990b9759f86aef9bf92097cbfe3dc48d57c334a9f6559a` |

### `reports/audits/`
| File | Purpose | SHA-256 (bytes) |
|---|---|---|
| `phase36_v1_14_runtime_source_integrity_manifest.json` | Canonical non-circular anchor: exec SHA `ac09ff8d…` + 14 dependency hashes + 4 checkpoint hashes; `launcher_sha256` absent by design. | `b4c358dfcb5e7b59beb6ae1ba2cffc64677d10049e12568b4c8eea8e79bb911e` |
| `phase36_preexecution_source_freeze_v1_14.json` | Source freeze. Binds **both** v1.12 and v1.13 historical evidence hashes; `smoke=ELIGIBLE_NOT_STARTED`, `science=INELIGIBLE_NOT_STARTED`, `science_machine_enforced=true`, `TEST=REMAINS_PHASE39_ONLY`. | `332e6ad8db0d62baf19fcc10ce2809daee367b38cf56f7cda99a95f049e64655` |
| `phase36_synthetic_smoke_eligibility_v1_14.json` | Smoke/science eligibility: smoke `ELIGIBLE_NOT_STARTED`, science `INELIGIBLE_NOT_STARTED`, `science_machine_enforced: true`, `science_release_requires_successful_smoke: true`. | `63d9fd04d86541629675669cda4c7ed0b5482ff51a22b08b110816e4cfccffbb` |
| `phase36_v1_13_to_v1_14_semantic_diff.json` | D43 raw-byte semantic diff: untransform identity ⇒ `new_scientific_choice=false`, 53 smoke-check IDs unchanged. | `45d382c6180b449587c1af301ab51163057b89f3933dc4278c5f0b969ff4c3f8` |

**Supporting v1.14 artifacts (review, not upload-first):**
`phase36_v1_14_direct_source_byte_audit.json` (`8c9b5775…`),
`phase36_v1_14_no_scientific_execution_audit.json` (`576f1b83…`),
`phase36_v1_14_science_release_attestation_contract.json` (`5567cc5a…`),
`phase36_v1_14_launcher_co_edit_negative_control.json` (`60a33d0b…`),
`phase36_robustness_unit_v1_14.json` / `phase36_robustness_preflight_v1_14.json` / `phase36_v1_14_negative_controls.json`.

### D40 — MACHINE-ENFORCED SCIENCE RELEASE (the v1.14 core repair)
```
science --verify-only            -> exit 0, does NOT release science
science (non-verify-only)        -> reads release attestation FIRST
   no attestation                -> NOT_RELEASED (NO_ATTESTATION)
   -> terminal PHASE36_V1_14_SCIENCE_NOT_RELEASED__SUCCESSFUL_SMOKE_REQUIRED__NO_ATTEMPT_CONSUMED
   -> exit 2, BEFORE token / exec import / marker / model / VAL
science RELEASED only when: revision matches AND execution_source_sha256 == THIS source's
   bytes AND smoke_artifact_sha256 == the write-once smoke artifact's bytes AND
   smoke_all_pass == True AND scientific_output == False AND
   release_gate == "POST_SMOKE_RELEASE_ADJUDICATION"
   (a bare editable {"released": true} JSON CANNOT satisfy the gate — NC124)
```
**POST-SMOKE STATUS (now):** the release attestation HAS been written by the post-smoke
adjudication, so the D40 gate (verified NON-DISPATCH, without `PHASE36_EXECUTE` and without
creating a science start marker) evaluates to `RELEASED` / `SUCCESSFUL_SMOKE_BOUND`. Science
remains **ELIGIBLE_NOT_STARTED** — release is necessary but not sufficient: running science
additionally requires the human to set `PHASE36_EXECUTE=1`.

---

## PHASE36 v1.13 — HISTORICAL / FROZEN (never consumed; superseded by v1.14)

> v1.13 was **ELIGIBLE_NOT_STARTED but NOT AUTHORIZED** by the independent supervisor
> because of the D40–D43 defects. It was **never consumed** (no smoke/science run) and is
> preserved byte-unchanged. All v1.13 files are **HISTORICAL / FROZEN — DO NOT MODIFY.**

## PHASE36 v1.13 — FULL ARTIFACT SET (historical)

Upload these 7 files first. They are the v1.13 deliverable set (5 static/device-only
gate artifacts + 2 device-only/environment records). Nothing else is required to review
the interpreter/CUDA pre-dispatch repair.

> **Run the launcher with the canonical interpreter ONLY:**
> `D:\Softfors\jup\.venv\Scripts\python.exe scripts\analysis\launch_phase36_v1_13.py --mode smoke --verify-only`
> A `python …` invocation of the bare system interpreter FAILS CLOSED with
> `PHASE36_V1_13_LAUNCH_FAIL_CLOSED__WRONG_INTERPRETER__NO_ATTEMPT_CONSUMED` and does NOT consume the revision.

### `scripts/analysis/`
| File | Purpose | SHA-256 (bytes) |
|---|---|---|
| `phase36_robustness_execution_v1_13.py` | v1.13 execution source. Governance-only token revision of frozen v1.12 (untransform identity ⇒ `new_scientific_choice=false`). 4256 lines, LF. | `57f78447e77f2bcee07265825232cf0a8f96d1a31974d5d52c4cc82229e5d39c` |
| `launch_phase36_v1_13.py` | Production launcher with D37 (exact interpreter identity), D38 (CUDA readiness, device-only), D39 (pre-consumption order). Literal frozen SHAs; no env override; no auto-relaunch. | `5f7fc91f9f0b8689adf42fc50527e216227ce7c4b853ba82ae1bce92a4805cab` |
| `phase36_robustness_unit_v1_13.py` | Unit suite (46/46 pass). Report SHA `0494a9df…`. | `a390ddc7721b4b911d090f5da64d973cb74c73028d7438308a7abe3c9bcd5cde` |

### `reports/audits/`
| File | Purpose | SHA-256 (bytes) |
|---|---|---|
| `phase36_v1_13_runtime_source_integrity_manifest.json` | Canonical non-circular anchor: exec SHA `57f78447…` + 14 dependency hashes + 4 checkpoint hashes; `launcher_sha256` absent by design. | `1f261eb95ab246619cf68a2340e8fc52e2887fe2d019fe9bc77ae8a9d5f5f1fe` |
| `phase36_v1_13_environment_readiness.json` | Device/environment readiness evidence: interpreter exact-match, torch 2.6.0+cu124, CUDA available, device count 1, RTX 3060 Ti, `get_device=cuda:0`, `ready_for_dispatch: true`. | `83cc7424055e2f67da904e4e41baf37355a23438d3cdd599d4683b64f08f4d2e` |
| `phase36_preexecution_source_freeze_v1_13.json` | Source freeze. Binds the five v1.12 historical evidence hashes; `smoke=ELIGIBLE_NOT_STARTED`, `science=INELIGIBLE_NOT_STARTED`, `TEST=REMAINS_PHASE39_ONLY`. | `86348c5ab5fbc4bd5408ef1d7357a2032951a86c1a7e2855cc3cd3ce2e311c26` |
| `phase36_synthetic_smoke_eligibility_v1_13.json` | Smoke eligibility: `smoke_eligible: true`, smoke `ELIGIBLE_NOT_STARTED`, science `INELIGIBLE_NOT_STARTED`. | `1e964fa26bfc20f8aab0365963075e1dcf2ba083bb5646fbbf0c82fbd44c8bec` |

**Supporting v1.13 artifacts (review, not upload-first):** `phase36_v1_12_to_v1_13_semantic_diff.json`
(`eabb4f93…`), `phase36_v1_13_direct_source_byte_audit.json` (`d541adc6…`),
`phase36_v1_13_no_scientific_execution_audit.json` (`8a24ca3a…`),
`phase36_robustness_preflight_v1_13.py` / `.json` (`9a495f20…`),
`phase36_robustness_negative_controls_v1_13.py` / `phase36_v1_13_negative_controls.json` (`e43597c5…`),
`phase36_v1_13_launcher_co_edit_negative_control.json`.

---

## PHASE36 v1.13 — FULL v1.13 ARTIFACT SET

### `scripts/analysis/`
| File | Purpose | Status |
|---|---|---|
| `build_phase36_v1_13_execution.py` | Deterministic write-once generator (governance token transform v1.12→v1.13, with semantic-safety assertions). | **CURRENT** |
| `build_phase36_v1_13_environment_readiness.py` | Device-only readiness builder (refuses non-venv interpreter). | **CURRENT** |
| `build_phase36_v1_13_freeze_and_audits.py` | Semantic diff + direct byte audit + no-execution audit + freeze + eligibility. | **CURRENT** |
| `build_phase36_v1_13_launcher_co_edit_control.py` | Co-edit negative control (frozen launcher rejects co-edited source+manifest). | **CURRENT** |
| `phase36_robustness_preflight_v1_13.py` | Static preflight (25/25 pass). | **CURRENT** |
| `phase36_robustness_negative_controls_v1_13.py` | Negative controls NC100–NC114 (15/15 pass). | **CURRENT** |

### `reports/audits/`
| File | Purpose | Status |
|---|---|---|
| `phase36_v1_13_launcher_co_edit_negative_control.json` | Co-edit control: `all_mutants_rejected: true`, `canonical_authorized: true`. | **CURRENT** |
| `phase36_robustness_unit_v1_13.json` | Unit gate report (46/46 pass). | **CURRENT** |
| `phase36_robustness_preflight_v1_13.json` | Static preflight report (25/25 pass). | **CURRENT** |
| `phase36_v1_13_negative_controls.json` | Negative-control report (15/15 pass, NC100–NC114). | **CURRENT** |

### PRE-DISPATCH ORDER (D39) — exactly as enforced by `launch_phase36_v1_13.py::main()`
1. parse mode → 2. verify immutable exec+manifest SHA anchor → 3. verify exact project interpreter (D37)
→ 4. verify CUDA readiness (D38) → 5. `--verify-only` STOP (exit 0, no dispatch) → 6. set
`PHASE36_V1_13_LAUNCH_AUTHORITY=1` → 7. dispatch frozen v1.13 source → 8. source mode-authorization gate
→ 9. only then may its exclusive `v1_13` start marker be created.

---

## 1. `scripts/analysis/` — HISTORICAL / FROZEN (v1.12) SOURCE FILES

> **HISTORICAL.** Superseded by v1.13 then v1.14. Listed for lineage only; **DO NOT MODIFY.**

| File | Purpose | SHA-256 (bytes) | Status |
|---|---|---|---|
| `phase36_robustness_execution_v1_12.py` | Executable execution source. D34 repair: no longer requires `manifest["launcher_sha256"]`; fails CLOSED if it appears; requires launch-authority token. 4248 lines, LF. | `8ed75a9b8f4ea8c204875bf1810e17df3f9c342a434f25399154f355ee888ea4` | **HISTORICAL / FROZEN** |
| `launch_phase36_v1_12.py` | Production launcher. D35 repair: literal frozen constants ONLY; no env/CLI override of expected exec+manifest SHAs; fails closed on launcher_sha256 in manifest. 220 lines. | `b3ffe88c44f084f9f03700419cd717afb0be8b103afad43d458ece3a42b4ad9d` | **CURRENT** |
| `phase36_robustness_unit_v1_12.py` | Unit suite; retargets D22–D33 and adds D34 (100–105), D35 (110–116), D36 (120–128) incl. cross-contract test 126. Report SHA `df445f6b…`. | `ae5042b1016fcc4094f3241ba640d2b4b0f407327e446b03387f632def429b58` | **CURRENT** |
| `phase36_robustness_preflight_v1_12.py` | Static preflight; sections A–L retargeted + section M (D34/D35/D36 three-file cross-binding). Report SHA `82e68675…`. | `bd7bc4ad63de64518b41f70d87b553b727713819253d643c919ba7f0ee4657a6` | **CURRENT** |
| `phase36_robustness_negative_controls_v1_12.py` | NC86–NC99; D35 mutants NC89 (exec-only), NC90 (manifest-only), NC91 (co-edit), NC92 (old-env inert) via in-memory harness; production launcher never weakened. Report SHA `7a47bcce…`. | `d2693a2726c445272d92f53967c253321b6063360810c31522726741f9d27676` | **CURRENT** |
| `build_phase36_v1_12_runtime_integrity_manifest.py` | Write-once builder of the runtime integrity manifest (non-circular anchor, no launcher_sha256). Byte-deterministic. | `d9e39066c751e0c947ea2abd4effcec9481e3ed2409bd7656f43414e8982deb0` | **CURRENT** |
| `build_phase36_v1_12_semantic_diff.py` | v1.11→v1.12 semantic diff with reporting repair (identical sets → `is_superset=true`, `is_strict_superset=false`). Report SHA `af0a32f1…`. | `6d3d9dd53d069ed92f88668d2a2f9f7e244ca609ea6b4cc9d75217b64e6446ef` | **CURRENT** |
| `build_phase36_v1_12_launcher_co_edit_control.py` | Co-edit negative control (frozen launcher rejects co-edited source+manifest). Report SHA `c28b6705…`. | `17a1905caa74cfee527befa6fc246cee4516d695eb987c52c92601b21082e3d1` | **CURRENT** |
| `audit_phase36_v1_12_direct_source_bytes.py` | Direct source byte audit (61/61 PASS). Report SHA `f4d3266d…`. | `d61968ae5fa754476cf65f17fb52d5e9c1aa5f0d51751b60e4f80f45d9f9dcc8` | **CURRENT** |
| `audit_phase36_v1_12_no_execution.py` | Zero-execution audit (all counters zero). Report SHA `a1457df8…`. | `8d6ed6370d59fa590ed1f32e20498094fe79c8b65a8608ab71f9dd062990d479` | **CURRENT** |
| `build_phase36_v1_12_freeze_and_eligibility.py` | Aggregates all static gates and writes source freeze + smoke eligibility. | `119ee1344dffcf0c8b1961995d0f2b9e73f16ba281825025b8a2040d1dd51fd6` | **CURRENT** |

## 2. `reports/audits/` — HISTORICAL / FROZEN (v1.12) ARTIFACTS

> **HISTORICAL.** Superseded by v1.13 then v1.14. Listed for lineage only; **DO NOT MODIFY.**

| File | Purpose | SHA-256 (bytes) | Status |
|---|---|---|---|
| `phase36_v1_12_runtime_source_integrity_manifest.json` | Canonical non-circular anchor: exec SHA `8ed75a9b…` + 14 dependency hashes + 4 checkpoint hashes; `launcher_sha256_absent_by_design: true`. CRLF. | `f75b719e125ac85f901950034c7364bb77614831ce425660d41d2a9f432b1b35` | **CURRENT** |
| `phase36_robustness_unit_v1_12.json` | Unit gate report (96/96 pass). | `df445f6bcca211486111d7aaffd81878a658d6677d18e0a905798368222138a5` | **CURRENT** |
| `phase36_robustness_preflight_v1_12.json` | Static preflight report (87/87 pass). | `82e6867507b76202053f9ba9f9b5b53de6c5f2af33a29aeebd35f76d64dafa76` | **CURRENT** |
| `phase36_v1_12_negative_controls.json` | Negative-control report (14/14 pass, NC86–NC99). | `7a47bcce324fc5d14b7cdbe09aff005768dc04679163925e32451c23d6260851` | **CURRENT** |
| `phase36_v1_11_to_v1_12_semantic_diff.json` | Semantic diff v1.11→v1.12; `new_scientific_choice=false`, all semantic groups unchanged, no prohibited changes, `is_strict_superset=false`. | `af0a32f108556ff5b8b7f91ba16dc2316b757c63c5976cb828820f56966b889b` | **CURRENT** |
| `phase36_v1_12_direct_source_byte_audit.json` | Direct byte audit (61/61 PASS). | `f4d3266d7f215e8d3e28356bc6591cf5a8f0054c2fd4c4565aff3eeaaa0e7221` | **CURRENT** |
| `phase36_v1_12_source_repair_no_execution_audit.json` | Zero-execution audit (all counters zero). | `a1457df87da363f9b6ce0bd7b39f24ccb42844615ff206541ecfa76257b917fd` | **CURRENT** |
| `phase36_v1_12_launcher_co_edit_negative_control.json` | Co-edit control: `all_mutants_rejected: true`, `canonical_authorized: true`. | `c28b67052dd8c93424dffe2550eb7baee6569f9e9c0c443ee3928a4e452fa2ae` | **CURRENT** |
| `phase36_preexecution_source_freeze_v1_12.json` | Source freeze record. Terminal `PHASE36_V1_12_SOURCE_FREEZE_COMPLETE__SMOKE_AND_SCIENCE_NOT_STARTED`. | `f6bf76954ae0e2c053defe117b518e6d3fa4f4130065de0091cb61f7f026a2b2` | **CURRENT** |
| `phase36_synthetic_smoke_eligibility_v1_12.json` | Smoke eligibility. Terminal `PHASE36_V1_12_SYNTHETIC_SMOKE_ELIGIBLE_NOT_STARTED__SCIENCE_INELIGIBLE_NOT_STARTED`; smoke `ELIGIBLE_NOT_STARTED`, science `INELIGIBLE_NOT_STARTED`. | `5a976c5d79daa6a422f66491cc9c843fd9665e6c64af3b0f721c4b1196753935` | **CURRENT** |

---

## 3. FROZEN HISTORICAL FILES (BYTE-PRESERVED — DO NOT MODIFY)

| File | SHA-256 (bytes) | Version | Status |
|---|---|---|---|
| `scripts/analysis/phase36_robustness_execution_v1_11.py` | `dc4928417444304ad637907c53089e512577254b368e438d0098ade6202083f0` | v1.11 | **FROZEN** |
| `scripts/analysis/launch_phase36_v1_11.py` | `56612332d220f93611fc627b1f495aca3013bb3578ab801ee10b4ee0386b25b0` | v1.11 | **FROZEN** |
| `scripts/analysis/phase36_robustness_unit_v1_11.py` | `189b9957704beccff1ba9c198e7f2f9ed29fa351e9cfc6f46d03441adeaeac41` | v1.11 | **FROZEN** |
| `reports/audits/phase36_v1_11_runtime_source_integrity_manifest.json` | `d795d41152accde6cf59717d2d17ab429b0cdf8fc1ff98bca11dcb13a591bda7` | v1.11 | **FROZEN** |
| `scripts/analysis/phase36_robustness_execution_v1_9.py` | `433bad87b4ef77fd6997c77f688eb295e526bfa3e88dece4ec5d3d550255cbd0` | v1.9 | **FROZEN** |
| `scripts/analysis/phase36_robustness_execution_v1_8.py` | `c95ff9884ec05a859b39ce7976376bf40e4543b1a8d8a19830e5893120039f4d` | v1.8 | **FROZEN** |
| `scripts/analysis/phase36_robustness_execution_v1_7.py` | `87062d2b38232c73b8ce620d7bfafb389658c4b877d9196a26b8b01d09daf192` | v1.7 | **FROZEN** |

> v1.0–v1.6, v1.10 and every `*_v1_X_*.json` audit/freeze/eligibility report of those
> versions remain on disk, byte-preserved, and are enumerated by directory listing.
> This index lists only the most recent frozen lineage; it does not claim to be exhaustive.

---

## 4. THE v1.12 NON-CIRCULAR RELEASE CHAIN (HISTORICAL — one internally consistent architecture; superseded by the v1.13/v1.14 chain)

```
SUPERVISOR (human/governance, outside the repo)
  │  pins EXTERNALLY:  launcher SHA  +  source-freeze SHA
  ▼
LAUNCHER  (launch_phase36_v1_12.py)
  │  holds IMMUTABLE literal constants:
  │     FROZEN_EXPECTED_EXEC_SHA      = 8ed75a9b…
  │     FROZEN_EXPECTED_MANIFEST_SHA  = f75b719e…
  │  verifies BOTH before dispatch; NO env/CLI override of these constants (D35)
  │  fails CLOSED if manifest unexpectedly declares launcher_sha256
  ▼
MANIFEST  (phase36_v1_12_runtime_source_integrity_manifest.json)
  │  declares: exec SHA + 14 dependency hashes + 4 checkpoint hashes
  │  does NOT declare launcher_sha256     ← breaks the cycle (D34)
  ▼
EXECUTION SOURCE  (phase36_robustness_execution_v1_12.py)
     verifies: manifest / execution / dependencies / checkpoints
     requires: launch-authority token  PHASE36_V1_12_LAUNCH_AUTHORITY == "1"
     does NOT require manifest["launcher_sha256"]   ← D34 repair
     fails CLOSED if launcher_sha256 appears in manifest
```

---

## 5. HOW TO USE THIS FILE

1. Start here to locate the CURRENT files you need — the top-level STATUS block and the
   "CLEAN EQUIVALENCE DIAGNOSTIC v1.0" section for the current diagnostic-preparation set.
   The "POST-SMOKE UPLOAD SET" and "PRE-SMOKE" sections are HISTORICAL / PRE-SCIENCE (the v1.14
   science attempt is now CONSUMED/FAILED), and the v1.13/v1.12 sections are HISTORICAL / FROZEN —
   read them for lineage only.
2. Before editing anything, confirm the file is **CURRENT**, not **FROZEN**.
3. Trust only the frozen manifests/freezes/eligibility for authority — never this index.
4. Recompute any SHA with `sha256sum <path>` (raw bytes), never a text-normalized read.
