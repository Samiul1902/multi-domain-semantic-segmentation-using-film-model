# Supervisor Action Request

**Status:** `DECISION_REQUEST__NOT_AN_APPROVAL__NOT_A_PERMISSION`
**Revision:** `RA_MEDFILM_BARR_PUB_READINESS_ACTION_V1_0`
**Repository HEAD:** `45b85c1`
**Companion documents:** `AUTHORIZATION_REQUIREMENTS_AND_OPEN_QUESTIONS.md`, `PROPOSED_EXECUTION_POLICY_DECISION.md`, `Q1_RESEARCH_EVIDENCE_GAP_AND_RUN_ORDER.md`

---

## The exact decision needed

> **Who authorises C1, under which policy, and on what evidence of dataset and ethics permission?**

Until that is answered by a human, C1 cannot lawfully start. The blocker is **not** software: the interpreter, CUDA, protocol SHA, TRAIN/VAL manifests, TEST lock and matched-arm initialisation all pass. The blocker is authority.

---

## Five decisions (all human)

| # | Decision | Owner | What it unlocks | Current state |
|---|---|---|---|---|
| **D1** | Confirm that each primary dataset's terms permit this training and publication, and that any required ethics review/exemption exists | Institution research office / dataset owners | The legal basis for any run | `HUMAN_DETERMINATION_REQUIRED`; no licence/DUA record; KUB conflict unresolved |
| **D2** | Choose the execution policy: `DECISION_I` (institution-signed) or `DECISION_R` (researcher-operated with personal attestation) | Researcher + supervisor | Which authority model the release must implement | `DECISION_I` recorded conversationally on 2026-11-01; **institutional approval PENDING**; `DECISION_R` not selected |
| **D3** | Approve the frozen protocol and set `scientific_execution_enabled = true` | Authorised signatory | Protocol-level execution | `PROTOCOL_READY_FOR_APPROVAL__NOT_APPROVED`; `false` |
| **D4** | Provision the RC4 trust root (if D2 = I) **or** approve the `DECISION_R` amendment (if D2 = R) | Institution + key custodian / researcher | A grant can be minted | RC4 root `C:\ProgramData\InstitutionalC1TrustRC4` **absent**; `DECISION_R` release **not implemented** |
| **D5** | Authorise an RC4 production execution surface | Supervisor | Training can actually start | `run_c1_campaign_launch_rc4_draft.py` has `DRAFT_AUTHORIZED = False`; `--execute` is refused; RC3 CLI is defective and must not be used |

**D1–D5 are not independent.** If D1 fails, D2–D5 are moot. If D2 = R, D4 changes from "provision institutional keys" to "approve a researcher-operated release".

---

## Exact artifacts that are missing

**If D2 = `DECISION_I`:**
1. `%ProgramData%\InstitutionalC1TrustRC4\` (directory, administrator-created).
2. `c1_rc4_binding.json` — institution, approving authority, key custodian, provisioning reference, owner public key, policy digest.
3. `policy.json` — signed by the owner key; key records with roles `SUPERVISOR` / `LAUNCH_OPERATOR` / `TIME_AUTHORITY`, distinct custodians.
4. A signed host-clock attestation from the TIME_AUTHORITY.
5. A fresh signed, single-use time proof for each of the six runs.
6. An RC4-bound `instruction.json` — the on-disk one binds RC3 `54d1273a…`, not RC4 `05a330d1…`.
7. A protocol approval that sets `scientific_execution_enabled = true`.
8. A reviewed release that authorises the RC4 execution surface (D5).

**If D2 = `DECISION_R`:**
1. The signed human attestation A (dataset terms) and B (ethics/privacy) in `PROPOSED_EXECUTION_POLICY_DECISION.md` §4.4.
2. A reviewed, additive `DECISION_R` release binding the unchanged protocol.
3. The same protocol approval (D3) and execution-surface authorisation (D5).
4. No institutional key is required; no institutional oversight may be claimed.

---

## First command after eligibility is satisfied

### Step 1 — preflight (no data access, no training)

```bat
.venv\Scripts\python.exe scripts\analysis\run_c1_campaign_launch_rc4_draft.py ^
  --release-digest 05a330d1aee18487de8582958a0f6fe1ff4597b36d0b4e20efb92db7424eada2 ^
  --owner-key-fingerprint <institution-published-out-of-band> ^
  --approval <signed-approval.json> ^
  --instruction <rc4-bound-instruction.json> ^
  --budget <budget.json> ^
  --time-proof-dir <signed-time-proofs> ^
  --recovery-dir <recovery-records>
```

Expected terminal: `RC4 preflight PASSED for all six runs. No training was started.`
Today this fails closed at `C1_RC4_TRUST_ROOT_MISSING`.

### Step 2 — first training command (becomes valid only after D5)

The same command with `--execute` is the intended production entry. It is **refused today** because `DRAFT_AUTHORIZED = False`. It becomes valid only when a human authorises the reviewed RC4 release. The first scientific run is **C1-T, seed 42**, followed by **C1-C, seed 42**; seeds 123/3407 are not automatic.

> Do **not** use `scripts/analysis/run_c1_campaign_launch.py --execute`: it is bound to the defective RC3 digest `54d1273a…` and the contaminated legacy store.

---

## What happens after each decision

- **D1 + D3 done, D2 = I:** provision D4, authorise D5, run preflight, then C1-T/42 and C1-C/42.
- **D1 + D3 done, D2 = R:** sign the attestations, approve the additive release, authorise D5, run preflight, then the same two arms.
- **D1 unresolved or negative:** stop. `DECISION_R` is unavailable; `DECISION_I` cannot be provisioned without an institution.
- **D2 = HOLD:** stop. No default is assumed.

---

## What I will not do

- I will not sign, simulate or generate an approval, attestation, key, grant, nonce or trust-root file.
- I will not declare an ethics exemption or assert that a licence covers the use.
- I will not change `DECISION_I`, the frozen protocol, the recipe, the seeds or the endpoint.
- I will not use the RC3 surface or the contaminated `configs/c1_operator/` artefacts.
- I will not reopen TEST1683.
- I will not start another coding or governance phase.

---

## Current terminal

```text
C1_EXECUTION_BLOCKED__HUMAN_AUTHORIZATION_ACTION_REQUIRED
```

Reason: protocol `NOT_APPROVED` with `scientific_execution_enabled = false`; RC4 trust root absent; institutional approval, signatory and key custody pending; no licence/ethics record; no authorised RC4 execution surface.
