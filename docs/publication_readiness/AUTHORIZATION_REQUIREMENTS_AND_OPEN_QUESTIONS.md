# Authorization Requirements and Open Questions

**Status:** `DECISION_MATERIAL__NOT_A_PERMISSION__NOT_AN_ETHICS_DETERMINATION`
**Revision:** `RA_MEDFILM_BARR_PUB_READINESS_AUTH_V1_0`
**Repository HEAD at drafting:** `45b85c1`
**Frozen protocol:** `reports/planning/c1_film_attribution_v1/protocol.json`
SHA-256 `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61`

---

## 0. Scope and integrity rule

This document inventories **what the repository actually records** about dataset provenance, licences, data-use terms and ethics. It does **not**:

- declare an ethics exemption or approval;
- assert that a licence covers the planned use;
- replace an IRB, ethics committee, data-access committee or institutional signatory;
- create or imply any permission.

Where the evidence is absent or contradictory, the item is marked **`HUMAN_DETERMINATION_REQUIRED`**. A missing file is reported as a missing file, not as proof that approval is legally mandatory, and not as proof that it is unnecessary.

---

## 1. What the repository actually contains

| Artefact | What it says | What it does **not** establish |
|---|---|---|
| `docs/manuscript/RA_MEDFILM_BARR_MANUSCRIPT_DRAFT.md` §18 | Primary datasets "obtained from public, de-identified research repositories (ISIC 2018, BUSI, Kvasir-SEG, KUB-StoneX) under their respective licences. **No IRB or ethics approval was obtained for this secondary analysis, and none is claimed.**" | That each licence was read or that its terms permit this use; that an institution agrees no review is required. |
| Same manuscript, §21.7 | "Not yet satisfied: … ethics/approval statement (none claimed), **dataset licence verification per cohort**, patient-level split verification for ISIC, BUSI and Kvasir." | Nothing is verified by this statement; it is the authors' own admission of a gap. |
| `docs/c1_execution_authority_decision_v1_0.md` | "**Licence / ethics record: None exists anywhere in the repository.**" DECISION_R requires the operator to attest licence + ethics in their own words. | That the datasets are unusable; only that the repository holds no record. |
| `docs/POST_FREEZE_RESEARCH_EXTENSION_PLAN.md` (EXT-02.1) | HAM10000 `CC BY-NC 4.0`; CVC-ClinicDB and BrEaST `LICENSE_CHECK_REQUIRED` (blocks EXT-06 publication, not internal EXT-03). | Terms for the **primary** datasets (ISIC 2018 archive, BUSI-WHU, Kvasir-SEG, KUB-StoneX). HAM10000 is an external cohort, not the primary ISIC archive. |
| Dataset roots on disk | `isic2018/`, `BUSI-WHU/`, `Kvasir-SEG/`, `KUB-Stonex/` contain **no** `LICENSE`, `README`, `TERMS` or `DUA` file at top level. | Any licence text at all. |
| `manifests/phase4_v3/README.md` | Split provenance, row counts, SHA-256 of the CSVs. | Dataset licences or ethics. |
| `docs/evaluation_r2/R2_INTEGRITY_REPORT.md` | KUB has `429` verified groups; KUB/Kvasir pixel spacing `NOT_AVAILABLE`. | KUB source, licence or permission to reuse. |

**Conclusion of §1:** the repository contains a **claim** of public, de-identified, licence-covered use, and simultaneously records that **per-cohort licence verification and an ethics statement are not satisfied**. It contains **no licence text, no DUA and no ethics determination** for any primary dataset.

---

## 2. Per-dataset determination

Legend: **`HUMAN_DETERMINATION_REQUIRED`** = cannot be established from the repository; a named human must decide or supply a document.

### 2.1 ISIC 2018

| Field | Finding |
|---|---|
| Authoritative provider | International Skin Imaging Collaboration (ISIC); the archive is `ISIC2018_Task1-2_*` (Task 1 lesion segmentation). Identifiable from the directory names; **not confirmed by a stored provider record**. |
| Terms recorded in repo | **None.** No licence file. HAM10000's `CC BY-NC 4.0` (EXT-02.1) is recorded for the **external** HAM10000 cohort, not for this primary archive. |
| Planned use covered? | **`HUMAN_DETERMINATION_REQUIRED`** — obtain the ISIC 2018 archive licence/terms and confirm that non-commercial secondary research training and publication are permitted. |
| Patient / examination metadata | Image-level. The primary archive does not supply verified patient linkage; HAM10000 `metadata.csv` is reporting-only. No patient identifiers are used as model inputs. |
| Ethics review / exemption | **`HUMAN_DETERMINATION_REQUIRED`** — the institution must decide whether secondary analysis of public, de-identified dermoscopy requires review or a formal exemption. |
| Publication permission | **`HUMAN_DETERMINATION_REQUIRED`** — check whether the licence is non-commercial and whether the authors' affiliation/venue is compatible. |

### 2.2 BUSI-WHU

| Field | Finding |
|---|---|
| Authoritative provider | BUSI (Breast Ultrasound Images), Al-Dhabyani et al.; the local directory is the `BUSI-WHU` distribution. **No provider record stored.** |
| Terms recorded in repo | **None.** No licence file at `BUSI-WHU/`. |
| Planned use covered? | **`HUMAN_DETERMINATION_REQUIRED`** — obtain the BUSI terms and confirm research training/publication. |
| Patient / examination metadata | BUSI carries case/category labels; patient-level linkage is **not verified** in the manifest (`patient_id` is not a verified BUSI patient key). |
| Ethics review / exemption | **`HUMAN_DETERMINATION_REQUIRED`**. |
| Publication permission | **`HUMAN_DETERMINATION_REQUIRED`**. |

### 2.3 Kvasir-SEG

| Field | Finding |
|---|---|
| Authoritative provider | Simula Research Laboratory / Kvasir project (Jha et al., 2020). **No provider record stored.** |
| Terms recorded in repo | **None.** No licence file at `Kvasir-SEG/`. |
| Planned use covered? | **`HUMAN_DETERMINATION_REQUIRED`** — obtain the Kvasir-SEG terms. |
| Patient / examination metadata | Image-level endoscopic frames; no patient identifiers. |
| Ethics review / exemption | **`HUMAN_DETERMINATION_REQUIRED`**. |
| Publication permission | **`HUMAN_DETERMINATION_REQUIRED`**. |

### 2.4 KUB-StoneX — highest-risk item

| Field | Finding |
|---|---|
| Authoritative provider | **Not established.** The data live at `D:\Softfors\omni_seg\data_raw\KUB-Stone\KUB-Stonex` with categories `Bladder_Stone`, `Kidney_Stone`, `Normal_NoStone`, `Ureteric_Stone` and a `patient-XXXXX` key. The manuscript calls it a "public, de-identified research repository"; **no source URL, licence or DUA is stored**. |
| Terms recorded in repo | **None.** |
| Planned use covered? | **`HUMAN_DETERMINATION_REQUIRED` — and this is a direct conflict.** `docs/c1_execution_authority_decision_v1_0.md` states: "Permissions signed for the original KUB dataset collection are **not presumed** to authorize this experiment." The manuscript's "public repository" claim contradicts that caution. |
| Patient / examination metadata | **Yes.** `patient_id` is present and used for grouping (429 verified groups in the R2 report). This is individual-level examination linkage, even if de-identified. |
| Ethics review / exemption | **`HUMAN_DETERMINATION_REQUIRED`** — because patient-level linkage exists, the institution must decide explicitly. A generic "public data" statement is not sufficient here. |
| Publication permission | **`HUMAN_DETERMINATION_REQUIRED`** — a written permission or licence from the KUB data owner is the safest closure. |

### 2.5 External cohorts (for completeness)

| Cohort | Recorded status | Determination |
|---|---|---|
| HAM10000 | `CC BY-NC 4.0` (EXT-02.1); **manuscript says it was excluded** because the folder is the classification release and the masks cannot be attributed | **Conflict** — EXT-01 says "masks FOUND (10,015)", the manuscript says "no masks / not used". No inference was run, so science is unaffected, but the record must be reconciled by a human. `HUMAN_DETERMINATION_REQUIRED`. |
| CVC-ClinicDB | `LICENSE_CHECK_REQUIRED` (EXT-02.1) | `HUMAN_DETERMINATION_REQUIRED` before publication. |
| BrEaST-Lesions-USG | `LICENSE_CHECK_REQUIRED` (EXT-02.1) | `HUMAN_DETERMINATION_REQUIRED` before publication. |
| Stones_where_are_you | `ELIGIBILITY_PENDING`; annotation completeness unresolved; 4 zero-annotation images | Not eligible as primary external validation. |

---

## 3. Cross-cutting questions

| # | Question | Who answers | Status |
|---|---|---|---|
| Q1 | Does each primary dataset's licence permit non-commercial research training **and** publication of derived metrics/figures? | Dataset owner terms + institution | `HUMAN_DETERMINATION_REQUIRED` |
| Q2 | Is a formal ethics review, exemption, or "not human-subjects research" determination required for secondary analysis of these public, de-identified data? | Institution / IRB | `HUMAN_DETERMINATION_REQUIRED` |
| Q3 | Is KUB-StoneX genuinely a public research repository, and does the original collection permission extend to this experiment? | KUB data owner + institution | `HUMAN_DETERMINATION_REQUIRED` (conflict recorded) |
| Q4 | Are any licences non-commercial, and does that constrain the venue or the authors' affiliations? | Institution / corresponding author | `HUMAN_DETERMINATION_REQUIRED` |
| Q5 | Is patient-level linkage available and verified for ISIC, BUSI and Kvasir? If not, are image-level splits acceptable to the venue/reviewer? | Authors + institution | `HUMAN_DETERMINATION_REQUIRED`; the manuscript already discloses image-level splits |
| Q6 | Does the institution require its own signatory for a study with no human-subjects intervention? | Institution | `HUMAN_DETERMINATION_REQUIRED` |
| Q7 | Must the HAM10000 record be corrected (EXT-01 "masks found" vs manuscript "no masks / not used")? | Authors | `HUMAN_DETERMINATION_REQUIRED` — documentation reconciliation only |

---

## 4. What would close this document

1. A written dataset-use determination **per primary cohort** (ISIC 2018, BUSI-WHU, Kvasir-SEG, KUB-StoneX), signed by whoever owns the data or the institution's research office.
2. A written ethics determination (approval, exemption, or "not human-subjects research") from the institution.
3. A specific KUB permission that resolves the conflict in §2.4.
4. A decision on the non-commercial licence constraint, if any.

Until those exist, the honest state is: **licence and ethics are `HUMAN_DETERMINATION_REQUIRED`, not established and not refuted.**
