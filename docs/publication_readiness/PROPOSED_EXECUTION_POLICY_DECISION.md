# Proposed Execution-Policy Decision

**Status:** `PROPOSED_NOT_APPROVED__DECISION_MATERIAL_ONLY`
**Revision:** `RA_MEDFILM_BARR_PUB_READINESS_POLICY_V1_0`
**Does not edit:** `reports/planning/c1_film_attribution_v1/protocol.json` (frozen, SHA `531e3eb2…087a61`)
**Does not mint:** keys, grants, nonces, signatures or trust-root files
**Does not change:** the recorded 2026-11-01 `DECISION_I` selection, which remains an immutable historical record

---

## 1. What the repository currently enforces

| Control | Current state | Consequence |
|---|---|---|
| Frozen protocol | `status = PROTOCOL_READY_FOR_APPROVAL__NOT_APPROVED`; `scientific_execution_enabled = false`; `real_data_driver_included = false` | Real training is disabled at the protocol level, not only at the gate. |
| RC4 release identity | `05a330d1aee18487de8582958a0f6fe1ff4597b36d0b4e20efb92db7424eada2`; `authorization_model = DECISION_I`; `trust_store = EXTERNAL_INSTITUTIONAL_UNPROVISIONED`; `institutional_approval = PENDING`; `scientific_execution = NOT_AUTHORIZED` | RC4 is **DECISION_I-only by construction**. |
| RC4 trust root | `C:\ProgramData\InstitutionalC1TrustRC4` **absent** | Gate fails closed with `C1_RC4_TRUST_ROOT_MISSING`. |
| RC4 execution surface | `scripts/analysis/run_c1_campaign_launch_rc4_draft.py` exists, but `DRAFT_AUTHORIZED = False`; `--execute` is refused unconditionally | There is **no authorized production C1 training command today**. |
| RC3 surface | `scripts/analysis/run_c1_campaign_launch.py --execute` hard-codes the RC3 digest `54d1273a…` and the legacy store | **Must not be used**: RC3 refuses its own digest and the legacy store is contaminated. |
| Contaminated artefacts | `configs/c1_operator/approval.json` (agent-generated), `time_status.json` (`VERIFIED/NTP`, false) | Excluded; must never be presented as authority. |

**Key distinction.** Journals require an ethics statement, data-permission statement and reproducible code — they do **not** require institutional cryptographic signing. RC4's signed trust root is a **repository design choice**, not a publication prerequisite. The least burdensome legitimate policy should therefore be driven by the actual university/dataset requirements, not by the ranking of the venue.

---

## 2. DECISION_I versus DECISION_R

| Dimension | DECISION_I — institution-signed execution | DECISION_R — researcher-operated execution |
|---|---|---|
| Who authorises | An independent institutional signatory, with a separately provisioned key custodian and time authority | The researcher, who personally attests dataset licences and ethics |
| Scientific endpoint | Identical: same protocol, same populations, same estimator, same seeds | Identical: same protocol, same populations, same estimator, same seeds |
| Governance claim | Can state "institutional approval" | Must state "no institutional oversight claimed" |
| Separation of duties | Enforced by RC4 (`check_separation`) | Not available; single-operator responsibility is disclosed |
| Trust material | Institution provisions `%ProgramData%\InstitutionalC1TrustRC4` (binding, signed policy, SUPERVISOR/LAUNCH_OPERATOR/TIME_AUTHORITY keys, clock attestation) | A researcher-operated release; no institutional key custody |
| Practical burden | High: requires a real institution, signatory, custodian and time authority | Lower: requires the researcher's written attestation and a reviewed release |
| Current feasibility | **Not feasible today** — trust root absent, signatory not identified | **Potentially feasible** — but only if the attestations in §4 can truthfully be made |
| Implementation status | RC4 implements it | **Not implemented**; would require a new prospective release candidate (below) |
| Effect on publication | Strongest governance statement | Acceptable if the paper states the absence of institutional oversight and the licence/ethics basis |

Neither choice changes the protocol, the recipe, the seeds, the splits, the endpoint or the analysis plan.

---

## 3. Recommendation (conditional, not a determination)

**Principle:** use the least burdensome legitimate policy consistent with (a) actual university requirements, (b) each dataset licence, and (c) researcher/supervisor authorisation.

- **If** the institution determines that no review/exemption is required for this secondary analysis of public, de-identified data, **and** each licence permits the use, **and** the KUB permission conflict is resolved in favour of reuse, **then `DECISION_R` is the least burdensome legitimate policy.** The paper must state that no institutional oversight is claimed.
- **If** the institution requires review, **or** KUB requires owner permission, **or** any licence is incompatible, **then `DECISION_I` is required** and the institution must provision RC4.
- **If** neither condition can be established, the correct state is **`HOLD`** — not a silent default.

This is a recommendation for a human decision. I do not select it, sign it, or treat it as approved.

---

## 4. Proposed prospective amendment — `DECISION_R` (PROPOSED_NOT_APPROVED)

> **Label:** `C1_DECISION_R_AMENDMENT_V1_0` · **Status:** `PROPOSED_NOT_APPROVED` · **Not implemented** · **No keys, no signatures, no trust-root files created.**

### 4.1 What it would be

A new, additive release candidate that binds the **same frozen protocol** and the **same scientific content**, but changes only the authority model:

| Field | Proposed value |
|---|---|
| `amendment_id` | `C1_DECISION_R_AMENDMENT_V1_0` |
| `study_id` | `C1_FILM_ATTRIBUTION_V1` |
| `protocol_sha256` | `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61` (**unchanged**) |
| `populations` | TRAIN 5,832 / VAL 808 (**unchanged**); TEST, ROUTER_HOLDOUT, EXTERNAL, QUARANTINE prohibited |
| `arms` / `seeds` | C1-T, C1-C × 42, 123, 3407 (**unchanged**) |
| `recipe` / `endpoint` | Unchanged from the frozen protocol |
| `authority_model` | `DECISION_R` |
| `institutional_oversight_claimed` | `false` |
| `operator_identity` | **blank — to be completed by the human** |
| `licence_attestation` | **blank — to be completed by the human** |
| `ethics_attestation` | **blank — to be completed by the human** |
| `contaminated_store` | `configs/c1_operator/approval.json` and `time_status.json` excluded, quarantined as evidence |
| `release_identity` | A new digest over this amendment + the unchanged protocol; **not computed here** |

### 4.2 What it would require

1. The operator's **own words** attestation that use of ISIC 2018, BUSI-WHU, Kvasir-SEG and KUB-StoneX for this training is permitted by each dataset's terms.
2. The operator's attestation that any applicable ethics, privacy or data-transfer obligation is satisfied without institutional oversight.
3. A reviewed release that sets an execution surface for the RC4 driver (today `DRAFT_AUTHORIZED = False`).
4. The paper, the run records and any publication to state the absence of institutional oversight explicitly.

### 4.3 What would make `DECISION_R` unavailable

- Any dataset licence that does not permit the use.
- Any institutional requirement for review or approval.
- An unresolved KUB permission.
- An inability or unwillingness to make the attestations truthfully.

In any of those cases the amendment is void and `DECISION_I` (or `HOLD`) applies.

### 4.4 Human approval record (template — **PROPOSED_NOT_APPROVED**)

```
DOCUMENT:  C1_DECISION_R_AMENDMENT_V1_0 — HUMAN APPROVAL RECORD
STATUS:    PROPOSED_NOT_APPROVED  (this template is not an approval)

Operator name:        ______________________________________
Affiliation:          ______________________________________
Date:                 ______________

Attestation A (dataset terms):
  I attest that use of ISIC 2018, BUSI-WHU, Kvasir-SEG and KUB-StoneX for
  C1_FILM_ATTRIBUTION_V1 training and publication is permitted by the applicable
  dataset terms. I have read those terms.
  Signature: ______________________

Attestation B (ethics / privacy):
  I attest that any applicable ethics, privacy or data-transfer obligation covering
  these images is satisfied for execution by me without institutional oversight.
  Signature: ______________________

Declaration:
  I understand that DECISION_R makes no claim of institutional oversight, that the
  frozen protocol is unchanged, that TEST1683 and ROUTER_HOLDOUT are excluded, and
  that the contaminated operator artefacts are excluded.
  Signature: ______________________

This record is INVALID until all three signatures exist and the release is separately
reviewed. No signature has been created by an agent.
```

---

## 5. What I did not do

- I did not edit the frozen protocol or change `scientific_execution_enabled`.
- I did not mint keys, grants, nonces or signatures.
- I did not create or modify `%ProgramData%\InstitutionalC1TrustRC4`.
- I did not select `DECISION_R`, declare an ethics exemption, or claim any licence covers the use.
- I did not implement the `DECISION_R` release or the missing RC4 execution surface.
- I did not alter the historical `DECISION_I` record of 2026-11-01.
