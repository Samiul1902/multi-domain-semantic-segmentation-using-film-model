# GitHub Publication Safety Check

**Artifact:** `docs/GITHUB_PUBLICATION_SAFETY_CHECK.md`
**Scope:** the repository as it would appear on a public GitHub remote
**Date of audit:** 2026-11-08
**Verdict:** **CONDITIONAL PASS** — the documentation surface is safe to publish;
two release-blocking actions are listed in § 2 and must be done by the repository
owner before pushing.

This document records what was checked, what was found, and what was
**deliberately not changed**. It is an audit, not a cleanup. No file was deleted,
moved or renamed during this check.

---

## 1. Release-blocking actions (owner must do)

| # | Action | Why it blocks |
|---|---|---|
| **B1** | `git add` the 14 untracked files listed in § 3 | 45 relative README links resolve **on disk** but nine linked files are not in the git index. On a public clone they would be 404s. |
| **B2** | Decide whether `_tmp/` (4,342 tracked files, 2.87 GB) should remain in the repository | Pre-existing tracked scratch content, including 42 MB `.pt` checkpoint copies. Not created by this documentation task, so it was **not** removed. See § 5. |

Neither action was taken here: B1 is a commit decision, B2 is a repository-owner
policy decision. Taking either unilaterally would be out of scope.

---

## 2. Check results

| Check | Result | Evidence |
|---|---|---|
| README relative links resolve | **PASS 45/45** | `scripts/analysis/verify_readme_links.py` → `RESULT: PASS`, 0 broken |
| All 16 required sections present | **PASS** | see `docs/README_LINK_VERIFICATION.md` § 4 |
| Every number traced to a frozen artifact | **PASS** | see `docs/README_LINK_VERIFICATION.md` § 5 |
| No publication acceptance claimed | **PASS** | "accepted for publication", "published in", "IEEE TMI (accepted)", "DOI: 10." all absent |
| Citation block says research code, not peer-reviewed | **PASS** | `README.md` § Citation |
| Negative results preserved | **PASS** | Stones Dice ≈ 0.08, 14/14 stone-free false positives, A8-vs-A7 CI includes zero |
| `0.837862` not presented as a result | **PASS** | only appears in the section explaining why it is wrong |
| Backbone ≠ FULL model stated explicitly | **PASS** | callout in § Overview + § Limitations |
| C1 / C2 / C3 status honest | **PASS** | 0/6 runs, not established, 0/24 cells |
| No clinical / deployment claim | **PASS** | "Research code. Not clinically validated." |
| README + new docs free of Windows absolute paths | **PASS 0** | regex `(?<![A-Za-z0-9])[A-Za-z]:(?:\\|/(?!/))…` → 0 hits in 5 files |
| No patient-identifiable material in published docs | **PASS** | 2 files *mention* the excluded BUSI-WHU workbook; no workbook is shipped |
| Dataset licences stated | **PASS** | CC0 / CC BY 4.0 / research-only Kvasir-SEG |
| `LICENSE` file absence stated honestly | **PASS** | no `LICENSE` exists; README says so |
| `.gitignore` covers weights and raw data | **PASS** | `checkpoints/`, `*.pt`, `*.pth`, `*.ckpt`, `data_raw/`, `data_cache/`, `reports/`, `configs/c1_operator/`, `runs/` |
| C1 operator / trust-store material excluded | **PASS** | `configs/c1_operator/` and `scripts/analysis/provision_trust_store.py` gitignored |
| Figures are vector-editable | **PASS** | SVG + PDF emitted from `generate_methodology.py` |
| No training triggered by documentation commands | **PASS** | link check and figure generator are pure reads/writes to `assets/` |

---

## 3. Untracked files that README links to (action B1)

All 14 exist on disk, are **not** gitignored, and are simply absent from the
index. They must be staged before publication.

```
assets/figures/generate_methodology.py
assets/figures/remedfilm_full_methodology.pdf
assets/figures/remedfilm_full_methodology.png
assets/figures/remedfilm_full_methodology.svg
assets/figures/remedfilm_inference_infographic.png
assets/figures/remedfilm_methodology_compact.svg
docs/GITHUB_PUBLICATION_SAFETY_CHECK.md          (this file)
docs/METHODOLOGY_FIGURE_QA.md
docs/METHODOLOGY_IMPLEMENTATION_MAP.md
docs/README_LINK_VERIFICATION.md
docs/REPOSITORY_MAP.md
docs/REPRODUCIBILITY_GUIDE.md
full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv
full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md
full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json
full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md
full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb
scripts/analysis/verify_readme_links.py
```

Suggested staging (owner to review and run):

```powershell
git add README.md docs/ assets/figures/ scripts/analysis/verify_readme_links.py `
         full_doc_report/REMEDFILM_FULL_COMPONENT_REGISTRY.json `
         full_doc_report/REMEDFILM_FULL_RESULT_RECONCILIATION.md `
         full_doc_report/REMEDFILM_FINAL_SCIENTIFIC_QA.md `
         full_doc_report/REMEDFILM_COMPONENT_TRAINING_HISTORY.csv `
         full_doc_report/ReMedFiLM_COMPLETE_MASTER_VERIFIED.ipynb
git status --short
```

> Already tracked and therefore safe: all eleven `full_doc_report/figures/*`
> directories, `src/models/film/global_medfilm.py`,
> `src/models/barr/ra_medfilm_barr.py`,
> `full_doc_report/PENDING_CONTROLLED_EXPERIMENTS.md`.

---

## 4. External URLs (not fetched)

Six `shields.io` badge URLs and four dataset-provider URLs. Full list in
`docs/README_LINK_VERIFICATION.md` § 3. Badges degrade to plain text on outage.

Dataset terms were transcribed from the provider landing pages recorded in the
repository; **they were not re-verified against the live sites in this session**.
Re-check before any redistribution decision:

| Dataset | Term recorded |
|---|---|
| ISIC 2018 Task 1 | CC0 |
| BUSI-WHU | CC BY 4.0, attribution required |
| Kvasir-SEG | research/educational; commercial use needs written permission |
| KUB-StoneX | CC BY 4.0, attribution required |

---

## 5. `_tmp/` — recorded, not acted on (action B2)

| Property | Value |
|---|---|
| Tracked files under `_tmp/` | **4,342** |
| Total size on disk | **2.87 GB / 5,100 files** |
| Largest single file | 43.6 MB (phase 05 notebook, also duplicated in three archive trees) |
| Contains | scratch `.py` diagnostics, regression harnesses, 42 MB `.pt` checkpoint copies |
| Gitignored? | **No** (directory not ignored; only `*.pt` inside it is) |

This scratch tree predates the documentation task. It is **not** referenced by
the README, and it contains no patient data, but publishing 2.87 GB of scratch
material is undesirable and some of it may embed host-local paths.

**Recommendation to the owner (choose one):**

1. Add `_tmp/` to `.gitignore` and `git rm -r --cached _tmp/` — keeps the working
   copy intact, removes it from future commits; or
2. Leave it, accepting the repository size.

**No deletion was performed.** Removing tracked files is a destructive,
owner-level decision, and the personal-files safety rules prohibit broad
recursive deletion of directories outside the immediate task scope.

---

## 6. Absolute host paths in legacy docs (informational)

32 Windows absolute paths appear in **legacy** docs (`docs/ARCHITECTURE.md`,
`docs/MEMORY.md`, `docs/c1_*`), e.g. `D:\Softfors\final\external_test_ds\…`.
These refer to local dataset locations and institutional trust-store paths, not
to secrets. They are pre-existing and were left untouched.

The **newly created / edited** documentation surface is clean:

| File | Absolute host paths |
|---|---|
| `README.md` | 0 |
| `docs/README_LINK_VERIFICATION.md` | 0 |
| `docs/METHODOLOGY_IMPLEMENTATION_MAP.md` | 0 |
| `docs/REPOSITORY_MAP.md` | 0 |
| `docs/REPRODUCIBILITY_GUIDE.md` | 0 |
| `docs/GITHUB_PUBLICATION_SAFETY_CHECK.md` | 0 |
| `docs/METHODOLOGY_FIGURE_QA.md` | 0 |

---

## 7. What was NOT done

- No file was deleted, renamed or moved (except a prior-session README backup to
  `docs/archive/`, which was retained).
- No `.gitignore` entry was removed. No valid ignore rule needed removal.
- No training, no checkpoint loading for inference, no TEST1683 access.
- No C1 / C2 / C3 experiment was run or implied to have run.
- No `LICENSE` was invented. The absence is stated instead.
- No author list, affiliation, DOI or acceptance status was fabricated.
- No external URL was fetched.

---

## 8. Final condition

**CONDITIONAL PASS.** The documentation is scientifically honest, internally
consistent and link-complete. Publication is safe once **B1** (stage the linked
files) is done; **B2** (`_tmp/` policy) is a size/hygiene decision, not a
correctness blocker.
