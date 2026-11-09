# RULES — Hard Governance Constraints

**Purpose:** The non-negotiable MUST / MUST NOT rule set. When a rule and a convenience
conflict, the rule wins. Violating a MUST is a scientific-integrity event: stop and return
`CHECK_REQUIRED`. See [PRD.md](PRD.md) for goals, [ARCHITECTURE.md](ARCHITECTURE.md) for
structure, [DESIGN.md](DESIGN.md) for experiment design, [TASKS.md](TASKS.md) for status,
[MEMORY.md](MEMORY.md) for operational handoff.

**Last verified:** 2026-10-01 — Phase25D COMPLETE canonical;
Phase25E ELIGIBLE_NOT_STARTED
**Strategy revision:** **SR-1** (Regional-Aware Multi-Domain FiLM) — status **ADOPTED**;
method name **RA-MedFiLM-BARR**

**Canonical source paths:**
- `PROJECT_MASTER_PLAN.md` §4–6, §8–11 (governance, test lock, provenance, notebook, statistics)
- `ANTIGRAVITY_WORKFLOW.md` (agent contract, TEST lock, what requires approval)
- `PROJECT_CONTEXT.md` §Governance
- `src/utils/test_lock.py`, `manifest_guard.py`, `device.py`, `run_lock.py`, `targets.py`
- `reports/audits/antigravity_current_state.json` (live `test_content_reads: 0`)

---

## 1. TEST lock — absolute

- **MUST NOT** use TEST for training, validation, checkpoint selection, threshold tuning,
  architecture selection, loss selection, preprocessing selection, **proposal selection,
  fusion selection, FiLM-design selection**, or hyperparameter tuning.
- **MUST** maintain **0 TEST content reads** during development.
- TEST is evaluated **only in Phase 39**, after protocols/thresholds/architectures are
  frozen in Phase 38. **No tuning after TEST access.**
- `KUBDataset` **MUST** raise on TEST construction unless `allow_test=True` (never set in
  development). `src/utils/test_lock.py` provides lock verification.
- **External data is locked** from tuning as well.

## 2. Manifest discipline — v3 active, v2 historical

- **MUST** use `phase4_v3` (`manifests/phase4_v3/`) for all new scientific development.
- **MUST NOT** silently load root `manifests/train.csv` (that is **historical v2** evidence).
- **MUST** call `validate_manifest_version_strict('phase4_v3')` before loading.
- **MUST NOT** modify or delete `phase4_v2` — required to reproduce historical Phases 06–15.
- **MUST NOT** present a v2 result as a clean-v3 result, or compare v2↔v3 numbers as if the
  splits matched.

## 3. Leakage

- Historical v2 leakage status is
  `KNOWN_SPLIT_CONTAMINATION_DISCOVERED_RETROSPECTIVELY`; v3 is `REMEDIATED` (Phase 05 1E).
- **MUST** preserve patient-level disjointness between TRAIN and VAL (verified: overlap 0).
- **MUST NOT** reintroduce quarantined or duplicate-grouped samples into development splits.

## 4. Frozen taxonomy — `kub_size_clean_v3_v1`

- **MUST** use `kub_size_clean_v3_v1` for clean-v3 KUB size work
  (`reports/audits/kub_size_clean_v3_v1_thresholds.json`).
- **MUST NOT** modify, recompute, or conflate it with historical `kub_size_v1` (**IMMUTABLE**).
- **MUST NOT** use the taxonomy to retune training; it is reporting/stratification metadata.
- **MUST NOT** apply KUB size thresholds directly to other domains; each domain needs its own
  TRAIN-derived scale characterization if scale-stratified analysis is required.

## 5. Foreground rule — binary segmentation is FROZEN

- **MUST** define KUB foreground as `mask > 0` via `src/utils/targets.py::binarize_mask`.
- **MUST NEVER** test `mask == 1`. Raw labels 1/2/3/255 are all foreground.
- **MUST NOT** reinterpret raw labels as multiclass pixel classes, and **MUST NOT**
  manufacture multiclass masks for any domain.
- All four domains remain **binary** semantic segmentation (lesion/polyp/stone vs background).

## 6. Device / CUDA — fail loud

- **MUST** use `get_device(require_cuda=True)` on canonical paths.
- **MUST NOT** silently fall back to CPU. If CUDA is unavailable: **STOP / CHECK_REQUIRED**.
- Expected GPU: NVIDIA GeForce RTX 3060 Ti; interpreter `D:\Softfors\jup\.venv\Scripts\python.exe`.

## 7. Scientific change control — STOP before changing science

- **MUST STOP and return `CHECK_REQUIRED`** before any change to: architecture, loss,
  learning rate / weight decay, batch size, resolution, augmentation, scheduler, patience,
  threshold, seed, checkpoint metric, preprocessing, **proposal mechanism, fusion, gate,
  FiLM site, conditioning input, or metadata input**.
- Agents **MAY** fix mechanical / path / logging bugs without authorization.
- **MUST NOT** tune because metrics look good or bad; **MUST NOT** reduce batch size
  autonomously on OOM; **MUST NOT** silently skip NaN/Inf batches (STOP instead).
- **MUST NOT** autonomously advance to the next phase or train unapproved models.

## 8. Single-writer and resume

- **MUST** acquire `src/utils/run_lock.py` before training; an **active** conflict
  **MUST** fail loudly.
- A **stale** lock **MAY** be reclaimed only after explicit inspection, with the recovery
  recorded.
- **MUST** resume with the **same** experiment ID. **MUST NOT** append `_retry`, `_v2`,
  `_new`, `_fix` for ordinary interruption recovery.
- **MUST** compare `latest.pt` against `history.csv` before resuming; if inconsistent, STOP.
- Exactly **one** training process per experiment ID.

## 9. Evidence, notebooks, statistics

- **MUST NOT** fabricate metrics, figures, tables, statistics, or epochs.
- **One-row-per-completed-epoch rule (MANDATORY for every training reviewer notebook).**
  `1 completed epoch = 1 table row`; the table **MUST** be complete and **untruncated**,
  built from the **immutable** `history.csv`; no missing epochs, no duplicate epochs;
  `history.csv` itself **MUST NOT** be modified. Applies later to regional-component
  training, localizer training (if epoch-based), multi-domain baseline training,
  Global MedFiLM, RA-MedFiLM-Seg++, and ablation/reproducibility runs.
- Notebooks are **display / analysis / audit** artifacts, **not training**. They **MUST**
  run top-to-bottom (Run All: unexecuted 0, errors 0), **MUST NOT** touch TEST, and
  **MUST** report reproducible SHA-256 hashes. **MUST NOT** auto-retrain on Run All.
- **MUST NOT** claim significance unless actually tested (paired testing, confidence
  intervals, effect sizes). **MUST NOT** claim superiority from a single seed.
- Reviewer VAL scope **MUST** be KUB-only (280 rows). **MUST NOT** let multi-domain
  (ISIC/BUSI/Kvasir) or `NOT_AVAILABLE` rows into a KUB gallery.
- Gallery subset means **MUST** be labelled `DETERMINISTIC_GALLERY_SUBSET_ONLY`.
- **MUST** keep Experiment A (`D:\Softfors\final\medfilm_seg_kub_extension`) unmodified.

## 10. Material vs cosmetic — blocking policy

| Class | Examples | Action |
|---|---|---|
| **MATERIAL (blocking)** | architecture, deep supervision, loss/weights, LR, WD, batch, accumulation, resolution, augmentation, scheduler, patience, threshold, seed, checkpoint metric, preprocessing, manifest version, taxonomy, TRAIN/VAL membership, TEST access, **proposal/fusion/gate/FiLM design, conditioning inputs** | **STOP → `CHECK_REQUIRED`**; requires supervisor authorization |
| **COSMETIC / GOVERNANCE (non-blocking, must be declared)** | fail-loud CUDA contract, centralized `mask > 0` helper, single-writer lock, NaN/Inf fail-loud guard, extra provenance/checkpoint metadata, clean experiment ID, taxonomy metadata binding, logging/path fixes | Proceed; record in the protocol-diff audit as `scientifically_material = False` |

Every clean-v3 rerun **MUST** produce a v2→v3 protocol-diff table with columns
`field, historical_v2, clean_v3, same_or_changed, change_reason, scientifically_material`.
**Unauthorized material differences MUST be 0**; if nonzero → `CHECK_REQUIRED`.

## 11. SR-1 architecture governance (adopted direction)

- **A.** No agent **MUST** implement or train `RA-MedFiLM-Seg++` before its authorized phase
  (Phase 24–26). The architecture is `PROPOSED_NOT_IMPLEMENTED`.
- **B.** No agent **MUST** skip **Phase 12**, **Phase 13**, and
  **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** before promoting the regional mechanism.
- **C.** Phases **14–18 are conditional** on that gate
  (`PENDING_POST_PHASE13_REGIONAL_INTEGRATION_GATE`). They **MUST NOT** proceed automatically.
- **D.** No agent **MUST** autonomously redesign Phases 14–26.
- **E.** Any new architecture, conditioning input, proposal mechanism, fusion, gate, FiLM
  site, metadata input, loss, or threshold **MUST** have supervisor authorization.
- **F.** Metadata unavailable at deployment **MUST NOT** be silently used as model
  conditioning (see §13).
- **G.** Kidney/Bladder/Ureteric **MUST** remain metadata, not segmentation mask classes.
- **H.** TEST **MUST** remain Phase 39 only.
- **I.** The one-row-per-completed-epoch notebook rule (§9) **MUST** remain mandatory for
  all training phases.

## 12. Prospective gate freeze

- The **`REGIONAL_INTEGRATION_GATE_AFTER_PHASE13`** criteria (GO / REVISE_LOCALIZER /
  NO_GO) **MUST** be frozen **prospectively** — before inspecting the relevant Phase-12/13
  results.
- **MUST NOT** define numerical GO/NO-GO thresholds post hoc to fit observed results.

## 13. Metadata conditioning governance

Every metadata field used in future multi-domain work **MUST** eventually be classified as
one of:

- **`CONDITIONING_ALLOWED`** — legitimately available at inference/deployment time.
- **`REPORTING_ONLY`** — usable for stratified reporting, never as model input.
- **`FORBIDDEN_AS_INPUT`** — ground-truth-only or annotation-derived; cannot be an
  inference-time shortcut.

- **MUST NOT** automatically feed diagnosis, pathology result, GT subtype, or
  annotation-derived information into FiLM.
- **KUB Kidney/Bladder/Ureteric remain `REPORTING_ONLY`** unless future governance
  explicitly proves legitimate inference-time availability.

## 14. Current locked state (must be encoded consistently everywhere)

> **Updated 2026-10-01** (Phase25D canonical reviewer-notebook compliance repair complete).
> The Phase-11/12/13 statements historically recorded here are retained in
> [MEMORY_ARCHIVE_pre_2026_09_30.md](MEMORY_ARCHIVE_pre_2026_09_30.md) and the dated logs.

- **Phases 00–23 COMPLETE** (historical roadmap status preserved).
- **Phase 24 COMPLETE**; **Phase 24 v1.1** exact-spec freeze historical;
  **Phase 24 v1.2** router feature specification **COMPLETE** (RF-1/RF-2/RF-3 + D1 + D2).
- **Phase 25A COMPLETE canonical** — terminal
  `PHASE25A_CANONICAL_RERUN_COMPLETE__ROI_PROPOSAL_THRESHOLD_0P30__SEGMENTATION_OUTPUT_THRESHOLD_0P50__PHASE25B_ELIGIBLE_NOT_STARTED`;
  refiner checkpoint `6d28608a…`; ROI-0.50 run **NONCANONICAL_PROTOCOL_DEVIATION** (preserved only).
- **Phase 25B COMPLETE canonical** — 202-D GT-free pre-refinement feature cache frozen
  (4957 × 202); handoff semantics repaired (`science_changed = false`).
- **Phase 25C COMPLETE canonical** — 4957 leakage-safe OOF paired refinement-gain labels frozen;
  at Phase25C completion, Phase25D was eligible/not started; it has since completed canonically.
- **Phase25D first blocked attempt = BLOCKED_ATTEMPT_PROVENANCE**.
- **Phase25D router training spec v1.2.1 = COMPLETE / FROZEN**.
- **Phase25D benefit router = COMPLETE_CANONICAL / TRAINED / FROZEN**.
- **Phase25E = ELIGIBLE_NOT_STARTED**.
- **Phase25F = NOT_STARTED**.
- **Phase25G = NOT_STARTED**.
- **TEST is locked until Phase 39.**
- The benefit router is **TRAINED / FROZEN**. The historical Phase-21/22 baselines are
  **TIED** — no winner is declared.

## 15. Consolidated hard rules (RA-MedFiLM-BARR)

1. **TEST remains locked until Phase 39.**
2. **ROUTER_HOLDOUT outcomes remain locked** until the designated one-shot evaluation.
3. **Existing VAL808 is continuity/development only** — not router training data.
4. **Never silently resolve a frozen-value conflict** — report `CHECK_REQUIRED`.
5. **Additive provenance only.** Historical artifacts are never deleted or overwritten.
6. **Never rename/delete a frozen artifact without an explicit migration record.**
7. **Historical noncanonical runs remain preserved** and scientifically excluded where declared.
8. **ROI threshold 0.30 ≠ segmentation threshold 0.50.**
9. **Feature extraction for the router must be pre-refinement and GT-free.**
10. **No refined features enter the pre-execution benefit router.**
11. **No architecture/hyperparameter changes based on holdout outcomes.**
12. **A blocked phase ⇒ do NOT manufacture a fake completion notebook.**
13. **Every completed scientific phase requires a real executed notebook.**
14. **Training notebooks include complete epoch tables.**
15. **Notebook build determinism must not trigger retraining.**
16. **Normalize nondeterministic execution metadata / stream chunking only when that
    normalization changes presentation/provenance bytes, not scientific content.**
17. **All checkpoint writes atomic.**
18. **RNG state restored on legitimate resume.**
19. **Assert generated artifacts exist; builder exit code alone is insufficient.**
20. **Never use pandas `~` directly on an object-dtype bool Series for fail-closed checks;
    cast to bool first.**
21. **If a specification is incomplete, STOP before execution.**

---

**Cross-links:** [PRD.md](PRD.md) · [ARCHITECTURE.md](ARCHITECTURE.md) ·
[DESIGN.md](DESIGN.md) · [TASKS.md](TASKS.md) · [MEMORY.md](MEMORY.md)
