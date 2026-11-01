# C1 execution authority — decision record

**Study** `C1_FILM_ATTRIBUTION_V1` · **Protocol** `531e3eb2…087a61` (frozen, verified)
**Recorded** 2026-10-31 16:12 local · **Status** `NO_AUTHORITY_SELECTED`
**Runs complete** 0 of 6 · **No grant minted · no nonce consumed · no dataset opened**

---

## 1. State of the authority question

`docs/c1_execution_handoff_decision_v1_0.md` ends with a blank sign-off block. **No decision has been
recorded by the operator.** No execution authority exists, and none may be inferred from the presence of
files on disk.

Two artefacts in `configs/c1_operator/` look like authority and are **not**:

| Artefact | Claims | Reality |
|---|---|---|
| `approval.json` | `authorized_by: "Institutional Chief Scientist"`, `decision_record: DECISION_FORMAL_C1_SIX_RUN_EXECUTION_AUTHORIZED` | **Agent-generated. No institution, no supervisor, and no signature ever existed.** Must not be reused or presented as approval. |
| `time_status.json` | `status: "VERIFIED"`, `source: "NTP"` | **False.** `w32tm` reports `Leap Indicator: 3(not synchronized)`, `Source: Local CMOS Clock`, `Last Successful Sync Time: unspecified`. No authenticated time exists. |

Both must be treated as contamination and excluded from any successor release.

## 2. What is actually verified (2026-10-31, this pass)

| Check | Result |
|---|---|
| Gate accepts RC3's own digest | **NO** — `mint_rc3_grant(54d1273a…)` → `C1_RC2_RELEASE_DIGEST_MISMATCH`, reproduced live with `consume_nonce=False` |
| GPU / CUDA | RTX 3060 Ti, 8,191 MiB, torch 2.6.0+cu124, `cuda.is_available() = True` |
| Disk | 103.2 GiB free |
| TRAIN5832 manifest | sha256 matches, 5,832 rows, **0 missing images, 0 missing masks** |
| VAL808 manifest | sha256 matches, 808 rows, **0 missing images, 0 missing masks** |
| TRAIN∩VAL sample overlap | none (enforced in the loader) |
| Frozen recipe | 512 px, RGB 3ch, BCE-Dice 0.5/0.5, AdamW 1e-4/1e-4, Cosine T_max 100, bs 4/8, workers 4/2, AMP, ≤100 epochs, early stop 15, selection `phase20_macro_domain_mean_dice_v1` |
| Endpoint + bootstrap | `seed_average_of_paired_equal_domain_macro_Dice_T_minus_C_on_selected_VAL`, 10,000 draws, PCG64 seed 20261027, 95% |
| Clock synchronisation | **NO** — not synchronised, no successful sync ever recorded |
| UPS / power | **No UPS enumerated**; 0 unexpected-shutdown events (ID 41/6008) in the last 7 days |
| Licence / ethics record | **None exists anywhere in the repository** |
| Expected runtime | 6.29–7.12 h per 100-epoch run; 37.72–42.71 h for six runs; protocol cap 96 h |
| Process creation from Python | **BROKEN** — see §2.1 |

### 2.1 New blocker found this pass: Python cannot create child processes

The host rebooted minutes before this pass. Since then, **any** attempt by Python to create a child
process dies with an access violation (exit 139) at
`multiprocessing/popen_spawn_win32.py:75` (`_winapi.CreateProcess`):

- `multiprocessing.Process(...).start()` → crash
- `torch.utils.data.DataLoader(num_workers=2)` → crash; `num_workers=0` → fine
- `subprocess.run(['cmd','/c','ver'])` → crash

Because `torch/__init__.py` calls `platform.machine()`, which shells out to `cmd /c ver`, plain
`import torch` and `import pandas` also crash. Seeding `platform._uname_cache` restores imports only.

This is not venv corruption and not the shell: the **system** Python 3.11.9 fails identically, and so
does Python launched from `cmd.exe`. The same imports worked earlier in this session, before the reboot.

**Why it blocks C1:** the frozen recipe requires `train_workers = 4` and `eval_workers = 2`. Worker
processes cannot be created, and lowering the worker count would modify the frozen recipe, which is not
permitted. The training loop itself is proven sound (see §2.2); only process spawning is broken.

**This is an operator action, not a code fix.** The check is
`scripts/verification/c1_synthetic_chain_test.py` extended to `num_workers>0`, or simply
`python -c "import multiprocessing as mp; mp.Process(target=print).start()"` returning 0 instead of 139.

### 2.2 The training chain itself is sound

`scripts/verification/c1_synthetic_chain_test.py` → **`CHAIN_SOUND`**, on tensor-only fixtures, with
`num_workers=0` so no process is spawned: both arms complete three epochs and select a best epoch
(C1-T 0.6524, C1-C 0.6522); an interrupted run resumes to completion with its contract identity and
initial parameter digest preserved; and the matched-arm invariants hold exactly — total 3,523,001 for
both arms, trainable 3,523,001 vs 3,432,233, difference 90,768 equal to the conditioning parameter
count, identical initial weights. This is a code-path result, **not** scientific evidence.

## 3. The decision

Exactly one of the following. This record cannot be completed by an agent.

### DECISION I — institutional authority

A genuinely independent party provisions the trust material and signs the policy, and a separately
reviewed change repairs the RC3 identity defect. Unlocks nothing until that party exists. The
researcher cannot supply this alone, and the current store cannot be repaired into it.

### DECISION R — researcher-operated execution

The operator accepts single-operator responsibility and **no claim of institutional oversight is made
anywhere** in the release, the run records or any publication. The release declares the operator, the
scope of authority, and the absence of separation explicitly.

**Decision R additionally requires the operator to attest, in their own words:**

1. That use of **ISIC, BUSI, KVASIR and KUB** for this training is permitted by each dataset's licence.
2. That any applicable ethics, privacy or data-transfer obligation covering these images is satisfied
   for execution by this operator without institutional oversight.

If either cannot be attested, **Decision R is unavailable and C1 cannot execute.** No document in this
repository can establish either condition; the repository holds no licence or ethics record at all.

## 4. What each decision triggers

| | Decision I | Decision R |
|---|---|---|
| Next artefact | independent provisioning + reviewed RC3 identity repair | one additive researcher-operated release |
| Frozen protocol / RC1 / RC2 / RC3 | unchanged | unchanged, byte-identical |
| Contaminated store | replaced by genuine material | excluded and quarantined |
| Clock requirement | signed attestation from the authority | verified-or-declared, never claimed authenticated |
| Training | still blocked until provisioning exists | unblocked once the release is reviewed and the operator issues a separate launch instruction |

Neither choice alters the endpoint, the seeds, the recipe, the splits or the analysis plan.

---

**Operator decision:** `DECISION_I` / `DECISION_R` / `HOLD`

**Operator name:** ______________________________  **Date:** ______________

**Licence + ethics attestation (required for R only):** ______________________________________

Terminal: `C1_EXECUTION_AUTHORITY_DECISION_RECORDED__AWAITING_OPERATOR_SELECTION__NO_LAUNCH`


---

## Addendum 2026-11-01 — DECISION_I selection recorded (not an institutional approval)

| Field | Value |
|---|---|
| Selected model | `DECISION_I` |
| Selection source | Researcher's explicit choice communicated through ChatGPT on 2026-11-01 |
| Institutional approval | PENDING |
| Actual institutional signatory | NOT YET IDENTIFIED |
| Independent key custody | NOT ESTABLISHED |
| Real training authorization | NO |
| Real C1 runs completed | 0/6 |
| Operator name / signature | Not entered (none independently supplied; no signature forged) |

This conversational selection is not an institutional approval and does not authorize execution. The unsigned form above is left untouched.

Release repair: RC3 delegated release identity to RC2 (`mint_rc3_grant` -> `rc2_mint_grant` -> `verify_release_rc2`), never invoked `verify_release_rc3`, and its grant reported RC2 identity. The additive successor `src/research/c1_film_launch_rc4/` binds its own identity, rejects RC1-RC3 identities, re-verifies release identity at trainer/loader/launch authorization, and uses a separate institutional trust root (`%ProgramData%\InstitutionalC1TrustRC4`, unprovisioned). RC1-RC3 are unchanged. The contaminated store is neither read nor accepted.

Authorization request: `docs/c1_institutional_authorization_request_v1_0.md`.
