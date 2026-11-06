# Final Dataset Permission and Execution Decision

**Status:** `DECISION_MATERIAL__NOT_A_PERMISSION__NOT_AN_ETHICS_DETERMINATION`
**Revision:** `RA_MEDFILM_BARR_FINAL_PERMISSION_DECISION_V1_0`
**Repository HEAD:** `45b85c1`
**Evidence access date:** 2026-11-05 (host clock; not synchronised — absolute times carry an unquantified offset)
**Frozen protocol SHA-256:** `531e3eb255a66381201d1aaf49bbe55abfdbe529640f5c584ef100d298087a61`

---

## 0. Verdict

All four primary datasets have **verified public licences** that permit non-commercial research use. The earlier `HUMAN_DETERMINATION_REQUIRED` for *dataset terms* is now **resolved to VERIFIED** for all four. The remaining human gate is **not** the licences; it is the **institutional ethics/data-use determination** and the **policy choice** (`DECISION_I` vs `DECISION_R`), plus a reviewed execution surface.

`DECISION_R` is therefore **not yet recommendable**: condition 1 (dataset permissions) is met, but condition 2 (ethics determination), condition 3 (explicit human choice) and condition 4 (reviewed release) are not.

No TEST1683 or candidate external image was opened. No training was run. No signature, key or approval was created.

---

## 1. Verified official sources and exact terms

| Dataset | Official source | Exact licence / terms | Verified |
|---|---|---|---|
| **ISIC 2018 Task 1** | https://challenge.isic-archive.com/data/ (2018 table); local `LICENSE.txt` + `ATTRIBUTION.txt` | **CC0 1.0 Universal** (public-domain dedication). Task 1 row shows `CC-0`. | **VERIFIED** — official table + full CC0 legal code stored locally |
| **BUSI-WHU** | https://data.mendeley.com/datasets/k6cpmwybk3/3 · DOI `10.17632/k6cpmwybk3.3` | **CC BY 4.0**. Version 3, published 2025-07-23. 927 images. Ethics: **WDRY2022-K217**, ethics committee of Renmin Hospital of Wuhan University. | **VERIFIED** — Mendeley metadata |
| **Kvasir-SEG** | https://datasets.simula.no/kvasir-seg/ · paper DOI `10.1007/978-3-030-37734-2_37` | “restricted for **research and educational purposes**. The use … for **commercial purposes is forbidden without prior written permission**.” Citation mandatory. 1,000 images. | **VERIFIED** — Simula terms of use |
| **KUB-StoneX** | https://doi.org/10.6084/m9.figshare.32049369.v1 · Figshare API `license.name` | **CC BY 4.0**. Version 1, published 2026-04-30. 2,570 images / 1,703 patients. Ethics: **REC-FSIT-2025/No: 12732** (FSIT, Daffodil International University); retrospective, anonymised, Declaration of Helsinki. | **VERIFIED** — Figshare API JSON |

**Important distinctions verified against the specific releases, not the names:**

- ISIC 2018 **Task 3** is `CC-BY-NC`, but **Task 1** (the segmentation task used here) is **CC0**. The two must not be conflated.
- BUSI-WHU is the **Wuhan University** release (`BUSI_WHU`, Renmin Hospital, 927 images), **not** the separate Cairo `BUSI` dataset.
- Kvasir-SEG has **no Creative Commons licence**; it is a custom research/education permission with a commercial-use prohibition.
- KUB-StoneX is a **2026 Figshare v1** release with its own IRB, not the earlier local `KUB-Stone` collection assumed in the frozen authority document.

---

## 2. Local provenance verification

| Dataset | Local path | Local counts | Official counts | Pairing / naming | Confidence |
|---|---|---|---|---|---|
| ISIC 2018 | `D:\Softfors\omni_seg\data_raw\isic2018\` | train **2,594** / val **100** / test **1,000** | 2,594 / 100 / 1,000 | `ISIC_<7-digit>.jpg` + `ISIC_<id>_segmentation.png`; `LICENSE.txt` = CC0; `ATTRIBUTION.txt` present | **VERIFIED (HIGH)** |
| BUSI-WHU | `…\BUSI_WHU Breast Cancer Ultrasound Image  Dataset\BUSI-WHU\` | img **927** / gt **927** | 927 | `00001.bmp` ↔ `00001_anno.bmp`; **927/927 paired, 0 unpaired** | **VERIFIED (HIGH)** |
| Kvasir-SEG | `D:\Softfors\omni_seg\data_raw\Kvasir-SEG\` | images **1,000** / masks **1,000** | 1,000 | **1,000/1,000 paired**; `kavsir_bboxes.json` present (the archive’s bounding-box JSON) | **VERIFIED (HIGH)** |
| KUB-StoneX | `D:\Softfors\omni_seg\data_raw\KUB-Stone\KUB-Stonex\` | Bladder **432** / Kidney **573** / Ureteric **177** / Normal **1,388** = **2,570** | 432 / 573 / 177 / 1,388 = 2,570 | per-class counts and folder/naming match Figshare v1 exactly | **VERIFIED that it derives from v1; PARTIAL as a complete mirror** |

### 2.1 KUB-StoneX: resolved findings

- The local cohort **does derive from the public Figshare v1 release**: per-class image counts match exactly (432/573/177/1,388), the class folders match, and the file naming (`NNNNN-NN-NNNNNNN.png`) matches.
- It is **not a complete mirror**: the local copy has **32 missing masks** (1 kidney, 31 ureteric), and the Figshare `ROI_Metadata/`, `Radiomic_Features/`, `annotations.json` and `*_patient/` folders are absent locally.
- The project’s TRAIN+VAL KUB population is **not 2,258 full images**. It is **873 full images + 1,385 ROI instance patches** (`…/<class>/ROI/<stem>_stone_obj1_m15.png`), i.e. a **mixed unit of analysis**. The 1,385 ROI patches come from 893 unique source images.
- The 32 maskless images are **never used as full-image rows**; 16 of them are used as ROI sources (their ROI masks exist). This is internally consistent, but the 32-image gap must be disclosed.
- The earlier “2,816 > 2,570” arithmetic alarm was a **unit mismatch** (images vs ROI instances), not evidence of leakage. No TEST data was read to reach this conclusion.

**Consequence for the paper:** the KUB task must be described as **ROI-instance segmentation on a derived subset**, not as whole-radiograph segmentation, and the 873/1,385 mixture and the 32 missing masks must be disclosed.

### 2.2 Privacy handling

- **BUSI-WHU** ships `Patient_infos_BUSI-WHU.xlsx`; it is present locally but was **not opened**. It must never be used as a model input, joined to outputs, or published.
- **KUB-StoneX** carries `patient_id` and `*_patient/` folders; the manifest uses `patient_id` only for grouping (429 groups in TRAIN+VAL). No personal information is exposed in this document.
- **ISIC / Kvasir** are image-level; no verified patient linkage exists.

---

## 3. Permissions register

| Field | ISIC 2018 Task 1 | BUSI-WHU | Kvasir-SEG | KUB-StoneX |
|---|---|---|---|---|
| **Provider** | International Skin Imaging Collaboration (ISIC) | Wuhan University / Renmin Hospital (Mendeley Data) | Simula Research Laboratory | Figshare (Zerin et al.) |
| **Publication / DOI** | Codella et al. 2018, arXiv:1902.03368; Tschandl et al. 2018, doi:10.1038/sdata.2018.161 | doi:10.17632/k6cpmwybk3.3 | Jha et al. 2020, doi:10.1007/978-3-030-37734-2_37 | doi:10.6084/m9.figshare.32049369.v1 |
| **Release / version** | ISIC 2018 Task 1-2 archive (2018) | Version 3 (2025-07-23) | Kvasir-SEG v1 (2020) | Version 1 (2026-04-30) |
| **Source URL** | https://challenge.isic-archive.com/data/ | https://data.mendeley.com/datasets/k6cpmwybk3/3 | https://datasets.simula.no/kvasir-seg/ | https://doi.org/10.6084/m9.figshare.32049369.v1 |
| **Exact licence** | **CC0 1.0** | **CC BY 4.0** | Research/education; **commercial forbidden without written permission** | **CC BY 4.0** |
| **Required attribution** | Not legally required (CC0); scholarly citation expected | Attribution to BUSI-WHU authors + licence indication | Citation of Jha et al. 2020 mandatory | Attribution to KUB-StoneX authors + licence indication; indicate ROI derivative |
| **Local provenance confidence** | VERIFIED (HIGH) | VERIFIED (HIGH) | VERIFIED (HIGH) | Derivation VERIFIED; mirror PARTIAL (32 masks absent) |
| **Remaining restrictions** | None from copyright; institutional ethics statement still needed | Patient workbook not usable/publishable; ethics determination | **Non-commercial only**; written permission for commercial use | Ethics determination; disclose 32 missing masks and ROI mixture |
| **Human ethics/institutional determination** | `HUMAN_DETERMINATION_REQUIRED` | `HUMAN_DETERMINATION_REQUIRED` | `HUMAN_DETERMINATION_REQUIRED` | `HUMAN_DETERMINATION_REQUIRED` |
| **Status** | **VERIFIED** | **VERIFIED** | **VERIFIED (restricted)** | **VERIFIED (licence) / PARTIAL (mirror)** |

**Retained evidence:** local ISIC `LICENSE.txt` (full CC0 legal code) and `ATTRIBUTION.txt`; durable citations are the URLs/DOIs above. The Mendeley/Figshare/Simula terms are cited, not copied, to avoid redistributing third-party pages.

---

## 4. Exact unresolved questions

1. **Ethics determination.** Does the institution require IRB review, an exemption, or a “not human-subjects research” determination for secondary analysis of these four public, de-identified datasets? *(The manuscript currently says “no IRB … and none is claimed”; that is a disclosure, not a determination.)*
2. **Kvasir-SEG commercial constraint.** Is the intended publication and author affiliation strictly non-commercial? If any commercial use is involved, written permission from Simula (`debesh@simula.no`) is required.
3. **KUB-StoneX secondary-use confirmation.** Does the FSIT IRB `REC-FSIT-2025/No: 12732` plus CC BY 4.0 satisfy the institution for this secondary analysis? The earlier authority-document caution (“permissions for the original KUB collection are not presumed”) is now largely answered by the public v1 release, but the institution must say so in writing.
4. **BUSI-WHU patient workbook.** Confirm it is excluded from all model inputs, joins and publications.
5. **KUB population description.** Confirm that the paper will describe ROI-instance segmentation and disclose 873 full images + 1,385 ROI patches, 893 source images, 32 missing masks.
6. **Attribution text.** Approve the exact attribution block for BUSI-WHU and KUB-StoneX (CC BY 4.0) and the Kvasir citation.
7. **Policy choice.** `DECISION_I` (institutional signing) or `DECISION_R` (researcher-operated with personal attestation), or `HOLD`.

---

## 5. Human execution decision sheet

**Recommendation rule (from the brief):** recommend `DECISION_R` only if **all four** hold.

| Condition | Status | Evidence |
|---|---|---|
| 1. All required dataset-use permissions established | **MET** | All four licences verified (§1, §3) |
| 2. Applicable institutional/ethics obligations determined and satisfied | **NOT MET** | `HUMAN_DETERMINATION_REQUIRED`; no written determination exists |
| 3. Human researcher explicitly chooses the policy | **PENDING** | No signed choice; the 2026-11-01 `DECISION_I` note is conversational only |
| 4. Prospective, reviewed, authorised operational release prepared | **NOT MET** | `DECISION_R` release not implemented; RC4 is `DECISION_I`-only; `DRAFT_AUTHORIZED = False` |

**Recommendation: preserve `DECISION_I` or `HOLD`. Do not select `DECISION_R` yet.**

If conditions 2–4 are later met, `DECISION_R` becomes the least burdensome legitimate policy: the datasets are public and licence-covered, the study is a secondary analysis of de-identified images, and no institutional cryptographic signing is required by journals. The paper must then state the absence of institutional oversight.

**No signature, approval, key or attestation has been created here.**

---

## 6. Minimum launch implementation gap

Even with a valid policy, C1 cannot start today because there is **no authorised production execution surface**. The minimum work is:

1. **Human policy decision** — `DECISION_I` or `DECISION_R` (or `HOLD`). No code can substitute for this.
2. **If `DECISION_I`:** provision `%ProgramData%\InstitutionalC1TrustRC4` (binding, signed policy, SUPERVISOR/LAUNCH_OPERATOR/TIME_AUTHORITY keys with distinct custodians, signed host-clock attestation), and set the protocol to approved with `scientific_execution_enabled = true`.
3. **If `DECISION_R`:** implement the additive `C1_DECISION_R_AMENDMENT_V1_0` release (same protocol SHA, same populations, same endpoint; operator attestation; no institutional claim), with a new release digest.
4. **Production launcher (the actual gap).** One reviewed module that calls the existing `src/research/c1_film_launch_rc4/launch_driver_rc4.py::launch(arm, seed, …)` for the six runs, with:
   - RC4 release-identity verification (`05a330d1…4eada2`) and external owner-key fingerprint;
   - one signed, single-use time proof and one recovery record per run;
   - write-once `start` / `result` / `failure` / `process_exit` artifacts;
   - an append-only `events.jsonl` recording resume events, per-epoch wall-clock and GPU memory, and the launching release identity (the frozen trainer does not persist these);
   - a **pre-specified** best-checkpoint re-inference on VAL808 to produce masks and HD95/ASSD (the trainer does not persist masks or boundary metrics).
5. **Replace `DRAFT_AUTHORIZED = False`** only through a reviewed release, not by editing the draft in place.
6. **Tests:** a synthetic end-to-end launcher run (no real data) and a fail-closed preflight; no change to the frozen protocol bytes or the RC4 release identity.

**Not implemented here.** No protocol byte, RC4 identity, model, recipe, seed or split was modified.

---

## 7. Single next human action

> **Obtain a written institutional ethics/data-use determination for secondary analysis of ISIC 2018 (CC0), BUSI-WHU (CC BY 4.0), Kvasir-SEG (research/education, non-commercial) and KUB-StoneX (CC BY 4.0, IRB REC-FSIT-2025/No: 12732), from the researcher’s institution or research office.**

That single document resolves condition 2. Immediately after it, the supervisor can make the policy choice (condition 3) and authorise the reviewed release (condition 4), which unlocks C1.

Until then:

```text
C1_EXECUTION_BLOCKED__HUMAN_AUTHORIZATION_ACTION_REQUIRED
```
