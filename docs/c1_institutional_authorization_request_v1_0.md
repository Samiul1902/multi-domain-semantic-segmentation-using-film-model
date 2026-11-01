# C1 Institutional Authorization Request — UNSIGNED DRAFT

Status: **PENDING — not an approval.** Prepared by the researcher's tooling for review by an actual institution. No signature, reference number or approval is implied.

| Item | Content |
|---|---|
| Study | RA-MedFiLM-BARR (experiment `C1_FILM_ATTRIBUTION_V1`) |
| Purpose | Non-commercial academic deep-learning research into task-conditioned FiLM attribution in multi-domain medical image segmentation |
| Datasets | ISIC2018, BUSI-WHU, Kvasir-SEG, KUB-StoneX |
| Research data | Public/research-source de-identified images and segmentation masks, subject to their applicable permissions |
| Experiment | Six matched treatment/control (C1-T / C1-C) training runs, seeds 42, 123, 3407 |
| Populations | TRAIN5832 and VAL808 only |
| Protected evaluation | TEST1683 remains excluded from this campaign |
| Compute | Locally operated RTX 3060 Ti workstation |
| Frozen protocol SHA-256 | `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61` |
| Release identity | RC4 (`src/research/c1_film_launch_rc4/RELEASE_DIGEST_RC4.txt`) |

Permissions signed for the original KUB dataset collection are **not presumed** to authorize this experiment. No patient identifiers, private metadata or dataset files are included.

## Decisions required from the institution

1. Is this research approved? — PENDING
2. Is independent ethics review or an exemption determination required? — PENDING
3. Who may authorize execution? — PENDING
4. Who controls the trust root and signing keys (separate from the researcher's development account)? — PENDING

## Evidence requested

- Signed institutional approval or equivalent verifiable authorization: PENDING
- Protocol / ethics reference: PENDING
- Authorized signatory (name, role, institution): PENDING
- Institution-approved key provisioning (public keys for SUPERVISOR, LAUNCH_OPERATOR, TIME_AUTHORITY; custodians; RC4 binding file): PENDING

| Field | Value |
|---|---|
| Institution | PENDING |
| Approving authority | PENDING |
| Signatory | PENDING |
| Key custodian | PENDING |
| Reference no. | PENDING |
| Date | PENDING |

## Clock / operational readiness (no system changes made)

Windows Time service is inactive with no verified synchronization; local CMOS readings are not authenticated time. RC4 fails closed (`C1_RC4_HOST_CLOCK_UNVERIFIED`) until a valid signed host-clock attestation exists. Minimum steps, all requiring a real administrator or time authority:

1. An administrator enables and synchronizes the Windows Time service against an institution-approved NTP source.
2. The institution's TIME_AUTHORITY key holder issues a signed host-clock attestation (offset within tolerance, unexpired) into the provisioned trust root.
3. A fresh signed, single-use time proof is issued for each of the six runs.

The institutional time requirement is not downgraded or removed.
