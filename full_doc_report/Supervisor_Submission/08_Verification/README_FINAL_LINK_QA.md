# README Final Link QA

Result of the local, read-only link audit of the public documentation.

- Auditor: [`assets/figures/readme/verify_readme_links.py`](../assets/figures/readme/verify_readme_links.py)
- Machine-readable report: [`docs/link_verification_readme.json`](link_verification_readme.json)
- Scope: `README.md`, `docs/RESEARCH_VISUAL_GALLERY.md`,
  `docs/README_VISUAL_ASSET_MANIFEST.md`, `docs/README_SCIENTIFIC_EVIDENCE_INDEX.md`,
  and this file.

Reproduce:

```powershell
.\.venv\Scripts\python.exe assets\figures\readme\verify_readme_links.py
```

---

## 1. Summary

| Metric | Value |
|---|---|
| Internal links and images checked | **117** |
| Broken | **0** |
| External URLs | 7 — listed but **not fetched** (no network call is made by this audit) |
| Absolute Windows paths in link targets | **0** |
| Backslash separators in link targets | **0** |
| Targets excluded by `.gitignore` | **0** |

The audit exits non-zero on any failure, so the command above is a usable CI gate.

---

## 2. What the auditor checks

| Check | Method |
|---|---|
| Target exists | filesystem `Path.exists()` on the resolved path |
| Relative resolution | resolved against the *source document's* directory, then asserted to stay inside the repository |
| Forward slashes only | any `\` in a target is a hard failure |
| No absolute paths | `^[A-Za-z]:[\\/]` is a hard failure |
| GitHub-renderable image | extension must be one of `.png .jpg .jpeg .gif .svg .webp` |
| Asset will actually render | `git check-ignore` on the resolved path — an ignored asset would 404 on GitHub |
| Anchors | `#fragment` must match a slugified heading in the same document |
| HTML embeds | `<img src>` and `<a href>` are parsed in addition to Markdown syntax |

---

## 3. Per-document results

| Document | Verified | Broken |
|---|---|---|
| `README.md` | 33 | 0 |
| `docs/RESEARCH_VISUAL_GALLERY.md` | 58 | 0 |
| `docs/README_VISUAL_ASSET_MANIFEST.md` | 3 | 0 |
| `docs/README_SCIENTIFIC_EVIDENCE_INDEX.md` | 21 | 0 |
| `docs/README_FINAL_LINK_QA.md` (this file) | 2 | 0 |
| **Total** | **117** | **0** |

These are the measured values from the run recorded in
[`link_verification_readme.json`](link_verification_readme.json). Re-running the audit is the
authoritative check.

---

## 4. Image assets specifically

| Asset | Path from repo root | Renders on GitHub |
|---|---|---|
| Methodology infographic | `assets/figures/remedfilm_inference_infographic.png` | yes |
| Four-domain gallery | `assets/figures/readme/remedfilm_four_domain_predictions.png` | yes |
| ISIC panel | `assets/figures/readme/prediction_isic.png` | yes |
| BUSI panel | `assets/figures/readme/prediction_busi.png` | yes |
| Kvasir panel | `assets/figures/readme/prediction_kvasir.png` | yes |
| KUB panel | `assets/figures/readme/prediction_kub.png` | yes |
| Internal performance | `assets/figures/readme/internal_domain_performance.png` | yes |
| Seven-model comparison | `assets/figures/readme/historical_model_comparison.png` | yes |
| External evaluation | `assets/figures/readme/external_evaluation.png` | yes |
| 13-arm ablation | `assets/figures/readme/complete_ablation.png` | yes |
| Accuracy vs compute | `assets/figures/readme/remedfilm_accuracy_compute.png` | yes |
| Training history | `assets/figures/readme/training_history.png` | yes |

All 12 are inside the repository, none is git-ignored, and every one is referenced with a
forward-slash relative path from the repository root.

---

## 5. Sizes and legibility

| Constraint | Limit | Worst asset | Verdict |
|---|---|---|---|
| GitHub per-file soft limit | 50 MB | 2.5 MB (`prediction_kvasir.png`) | pass |
| README visual payload | practical ~10 MB | 8.6 MB total | pass |
| Minimum rendered width | ~880 px in a GitHub column | all ≥ 1,874 px native | pass |
| Text legibility at 880 px | readable without zoom | verified by downscaling the combined gallery and the ISIC panel to 880 px and inspecting | pass |
| Aspect distortion | none | every figure is embedded at `width="100%"`, so GitHub scales uniformly | pass |

The individual per-domain panels are tall (3,155–3,730 px). At GitHub's column width the
masks stay legible and the metric captions remain readable; fine detail requires opening the
full-resolution file, which is why each panel is wrapped in a link to itself.

---

## 6. Text-level checks

| Check | Result |
|---|---|
| Stale figure numbers | none — figures are numbered 1–12 in reading order and each is referenced by that number |
| `ReMedFiLM FULL` identified as the proposed model | yes — header, Overview, Key Contributions, every results figure |
| Backbone-only results labelled as backbone | yes — the model table marks GlobalMedFiLM **"backbone, not the full model"** |
| Absolute local paths in public prose | none |
| Dataset licence statements present | yes — per-domain table plus a dedicated section |
| Unsupported significance/safety claims | none — C1/C2/C3 status stated in three places |
| Publication status | explicitly "no paper, no DOI" |

---

## 7. Known non-blocking issues

| Issue | Status |
|---|---|
| External URLs are not fetched | by design — this audit is offline and read-only |
| `full_doc_report/figures/` directory links resolve to a directory, not a page | valid on GitHub; the audit treats an existing directory as OK |
| The saved mask cache is not tracked, so `build_readme_figures.py` cannot regenerate the prediction panels from a fresh clone | documented in the manifest § 6; the panels themselves are committed |
| The audit does not validate image *content* | content was verified separately by inspection and by the GT-foreground identity assertion |

---

## 8. Git publication status

Nothing was committed or pushed. At the time of writing:

- `assets/figures/readme/` is untracked but **not** ignored — it can be staged as-is.
- `docs/RESEARCH_VISUAL_GALLERY.md`, `docs/README_VISUAL_ASSET_MANIFEST.md`,
  `docs/README_SCIENTIFIC_EVIDENCE_INDEX.md`, `docs/README_FINAL_LINK_QA.md` and the
  rewritten `README.md` are untracked/modified working-tree changes.
- No file under `.gitignore` is referenced by any public link.
- No credential, checkpoint, spreadsheet or patient record is referenced.

To publish (not performed):

```powershell
git add README.md docs assets/figures/readme assets/figures/remedfilm_inference_infographic.png
git status --short
```
