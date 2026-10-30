"""Build the phasewise evaluation/visualization coverage matrix and update
master documentation (phasewise index notebook + phasewise README).

No training, no inference, no TEST access, no frozen-gate change.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
COVERAGE = ROOT / "reports" / "tables" / "phasewise_evaluation_visualization_coverage.csv"
INDEX_NB = ROOT / "notebooks" / "phasewise" / "00_PHASEWISE_PROJECT_INDEX.ipynb"
README = ROOT / "notebooks" / "phasewise" / "README.md"
REC = ROOT / "reports" / "audits" / "phasewise_evaluation_visualization_sha_updates.json"

YES, NO, NA, UNAVAIL = "YES", "NO", "NA", "UNAVAILABLE_FROM_SAVED_ARTIFACTS"

COLS = ["phase", "notebook", "scientific_domain", "confusion_matrix", "dice", "iou", "precision",
        "recall", "specificity", "mcc", "boundary_metrics", "calibration", "component_metrics",
        "proposal_metrics", "pr_curve", "froc", "confidence_intervals", "qualitative_examples",
        "training_curves", "status", "reason_for_na"]


def row(phase, notebook, domain, **kw):
    r = {c: NA for c in COLS}
    r.update({"phase": phase, "notebook": notebook, "scientific_domain": domain, "reason_for_na": ""})
    r.update(kw)
    return r


ROWS = [
    row("Phase 09", "notebooks/phasewise/phase_09_baseline_training/phase09_clean_v3_unet_training_review.ipynb",
        "PIXEL_SEGMENTATION (training)",
        confusion_matrix=UNAVAIL, dice=YES, iou=YES, precision=YES, recall=YES, specificity=UNAVAIL,
        mcc=UNAVAIL, boundary_metrics=UNAVAIL, calibration=UNAVAIL, component_metrics=UNAVAIL,
        proposal_metrics=NA, pr_curve=NA, froc=NA, confidence_intervals=UNAVAIL,
        qualitative_examples=YES, training_curves=YES, status="SYNCED",
        reason_for_na="Phase-09 model is a UNet, which is not among the four central safe-replay arms "
                      "(GLOBAL=UNet++, ORACLE_REGIONAL, PREDICTED_REGIONAL, H3_DOWNSTREAM); no per-pixel "
                      "maps persisted; no new inference permitted."),
    row("Phase 10", "notebooks/phasewise/phase_10_baseline_comparison/phase10_clean_v3_final_baseline_comparison.ipynb",
        "PIXEL_SEGMENTATION (four-model comparison)",
        confusion_matrix=YES, dice=YES, iou=YES, precision=YES, recall=YES, specificity=YES, mcc=YES,
        boundary_metrics=YES, calibration=YES, component_metrics=YES, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=YES, qualitative_examples=YES, training_curves=YES, status="SYNCED",
        reason_for_na="Confusion / boundary / calibration metrics apply ONLY to UNet++ (the GLOBAL arm); "
                      "the other three models have no persisted per-pixel maps."),
    row("Phase 11", "notebooks/phasewise/phase_11_failure_analysis/phase11_clean_v3_baseline_failure_analysis.ipynb",
        "OBJECT_COMPONENT_DETECTION (failure analysis)",
        confusion_matrix=NO, dice=YES, iou=NO, precision=NO, recall=YES, specificity=NA, mcc=NA,
        boundary_metrics=YES, calibration=NA, component_metrics=YES, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=NO, qualitative_examples=YES, training_curves=YES, status="SYNCED",
        reason_for_na="Failure analysis is component/detection-focused; pixel confusion for the same "
                      "(GLOBAL) arm is reported in Phase 10/12 rather than duplicated here."),
    row("Phase 12", "notebooks/phasewise/phase_12_oracle_roi/phase12_clean_v3_oracle_regional_analysis.ipynb",
        "PIXEL_SEGMENTATION + OBJECT_COMPONENT_DETECTION (oracle upper bound)",
        confusion_matrix=YES, dice=YES, iou=YES, precision=YES, recall=YES, specificity=YES, mcc=YES,
        boundary_metrics=YES, calibration=YES, component_metrics=YES, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=YES, qualitative_examples=YES, training_curves=NA, status="SYNCED",
        reason_for_na="ORACLE_REGIONAL is a diagnostic upper bound (GT bboxes); it is not deployable "
                      "performance and has no proposal curve."),
    row("Phase 13", "notebooks/phasewise/phase_13_predicted_roi_localization/phase13_clean_v3_best_checkpoint_proposal_analysis.ipynb",
        "LOCALIZATION_PROPOSAL_SUPPLY + OBJECT_COMPONENT_DETECTION",
        confusion_matrix=NA, dice=NA, iou=YES, precision=YES, recall=YES, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=YES, proposal_metrics=YES, pr_curve=YES,
        froc=YES, confidence_intervals=NO, qualitative_examples=YES, training_curves=YES, status="SYNCED",
        reason_for_na="Proposal/localizer task has no defensible negative unit, so no TN-based confusion "
                      "matrix; 'iou' here denotes proposal-to-GT box IoU, not mask IoU."),
    row("Phase 14", "notebooks/phasewise/phase_14_regional_refiner/phase_14_regional_refiner_pipeline.ipynb",
        "PIXEL_SEGMENTATION + OBJECT_COMPONENT_DETECTION (regional refiner)",
        confusion_matrix=YES, dice=YES, iou=YES, precision=YES, recall=YES, specificity=YES, mcc=YES,
        boundary_metrics=YES, calibration=YES, component_metrics=YES, proposal_metrics=YES, pr_curve=NA,
        froc=NA, confidence_intervals=YES, qualitative_examples=YES, training_curves=YES, status="SYNCED",
        reason_for_na="GLOBAL / ORACLE_REGIONAL / PREDICTED_REGIONAL only; no proposal PR/FROC curve "
                      "(the refiner diagnostic reports proposal burden, not detection curves)."),
    row("H3-01", "notebooks/phasewise/post_phase14_h3_proposal_supply/01_proposal_root_cause_diagnostic.ipynb",
        "LOCALIZATION_PROPOSAL_SUPPLY + OBJECT_COMPONENT_DETECTION",
        confusion_matrix=NA, dice=NA, iou=NA, precision=NA, recall=YES, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=YES, proposal_metrics=YES, pr_curve=UNAVAIL,
        froc=UNAVAIL, confidence_intervals=NO, qualitative_examples=UNAVAIL, training_curves=NA, status="SYNCED",
        reason_for_na="Proposal-domain diagnostic; H3 proposal curves are degenerate (sentinel score)."),
    row("H3-02", "notebooks/phasewise/post_phase14_h3_proposal_supply/02_h3_axis_priority_diagnostic.ipynb",
        "CAUSAL_COUNTERFACTUAL_DIAGNOSTIC + LOCALIZATION_PROPOSAL_SUPPLY",
        confusion_matrix=NA, dice=NA, iou=NA, precision=NA, recall=YES, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=YES, proposal_metrics=YES, pr_curve=UNAVAIL,
        froc=UNAVAIL, confidence_intervals=NO, qualitative_examples=UNAVAIL, training_curves=NA, status="SYNCED",
        reason_for_na="Counterfactual unit is a component, not a pixel; no TN-based confusion matrix."),
    row("H3-03", "notebooks/phasewise/post_phase14_h3_proposal_supply/03_h3_design_and_pretraining_binding.ipynb",
        "DESIGN / PRETRAINING BINDING",
        confusion_matrix=NA, dice=NA, iou=NA, precision=NA, recall=NA, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=NA, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=NA, qualitative_examples=NA, training_curves=NA, status="NOT_MODIFIED",
        reason_for_na="Design/binding notebook with no evaluation domain; no segmentation confusion "
                      "matrix or metric panel is applicable by task design."),
    row("H3-04", "notebooks/phasewise/post_phase14_h3_proposal_supply/04_h3_training.ipynb",
        "TRAINING_OPTIMIZATION",
        confusion_matrix=NA, dice=NA, iou=NA, precision=NA, recall=NA, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=NA, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=NA, qualitative_examples=NA, training_curves=YES, status="SYNCED",
        reason_for_na="Training record: optimization/training metrics only; evaluation metrics belong to "
                      "H3-05/H3-06 and are not duplicated."),
    row("H3-05", "notebooks/phasewise/post_phase14_h3_proposal_supply/05_h3_supply_axis_evaluation.ipynb",
        "LOCALIZATION_PROPOSAL_SUPPLY + OBJECT_COMPONENT_DETECTION",
        confusion_matrix=NA, dice=NA, iou=NA, precision=YES, recall=YES, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=YES, proposal_metrics=YES, pr_curve=UNAVAIL,
        froc=UNAVAIL, confidence_intervals=NO, qualitative_examples=YES, training_curves=NA, status="SYNCED",
        reason_for_na="H3 proposal PR/FROC are NOT meaningful: best_proposal_score uses a -1.0 sentinel, "
                      "making the score perfectly separable (NA_DEGENERATE_SENTINEL_SCORE)."),
    row("H3-06", "notebooks/phasewise/post_phase14_h3_proposal_supply/06_h3_downstream_evaluation.ipynb",
        "PIXEL_SEGMENTATION + OBJECT_COMPONENT_DETECTION + BOUNDARY_SURFACE_QUALITY + PROBABILITY_CALIBRATION",
        confusion_matrix=YES, dice=YES, iou=YES, precision=YES, recall=YES, specificity=YES, mcc=YES,
        boundary_metrics=YES, calibration=YES, component_metrics=YES, proposal_metrics=NO, pr_curve=NA,
        froc=NA, confidence_intervals=YES, qualitative_examples=YES, training_curves=NO, status="SYNCED",
        reason_for_na="H3 downstream segmentation arm; proposal curves are degenerate for H3 supply."),
    row("Phase 15", "notebooks/phasewise/phase_15_loss_study/phase15_loss_function_comparison.ipynb",
        "PROTOCOL DESIGN (not executed)",
        confusion_matrix=NA, dice=NA, iou=NA, precision=NA, recall=NA, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=NA, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=NA, qualitative_examples=NA, training_curves=NA, status="NOT_MODIFIED",
        reason_for_na="Phase 15 is a frozen protocol with NO trained models; populating it with metrics "
                      "would fabricate evidence. See the future-phase requirement template in the README."),
    row("Phase 16-40", "(organizational folders only)",
        "NOT_STARTED",
        confusion_matrix=NA, dice=NA, iou=NA, precision=NA, recall=NA, specificity=NA, mcc=NA,
        boundary_metrics=NA, calibration=NA, component_metrics=NA, proposal_metrics=NA, pr_curve=NA,
        froc=NA, confidence_intervals=NA, qualitative_examples=NA, training_curves=NA, status="NOT_APPLICABLE",
        reason_for_na="Future phases remain organizational only; no evaluation outputs are fabricated. "
                      "Prospective acceptance requirements are documented in the phasewise README."),
]


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_coverage() -> str:
    import csv
    COVERAGE.parent.mkdir(parents=True, exist_ok=True)
    with open(COVERAGE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        for r in ROWS:
            w.writerow(r)
    return sha(COVERAGE)


README_SECTION = """
## Evaluation / visualization synchronization

A project-wide evaluation-metrics audit (terminal state
`PROJECT_EVALUATION_METRICS_AUDIT_COMPLETE__H3_ADJUDICATION_PENDING`) produced reusable
descriptive metrics, confusion matrices, per-image / per-component tables, confidence
intervals, boundary metrics, calibration metrics, proposal metrics and figures. These
have now been synchronized into the completed phasewise notebooks.

**No new inference was run.** Every added value is read from already-saved artifacts;
notebook-only plotting from saved tables is used where a central figure mixed arms that
are not all relevant to a phase.

### What was synchronized

| Phase | Confusion matrix | Advanced metrics | Proposal / FROC | Visual evidence |
| :--- | :--- | :--- | :--- | :--- |
| Phase 09 (UNet) | UNAVAILABLE_FROM_SAVED_ARTIFACTS | Dice/IoU/precision/recall + training curves | NA | gallery |
| Phase 10 (4-model) | YES (UNet++ = GLOBAL arm only) | Dice/IoU/precision/recall/specificity/MCC/HD95/ASSD/surface Dice/Brier/ECE + CIs | NA | per-model Dice boxplot |
| Phase 11 (failure) | NO (component focus) | size-stratified recall, HD95, FP/FN | NA | failure dashboards |
| Phase 12 (oracle) | YES (GLOBAL + ORACLE) | full pixel/boundary/calibration + paired Dice | NA (GT-derived) | confusion + paired benefit |
| Phase 13 (localizer) | NA (no TN unit) | proposal precision, component recall, box IoU | PR + FROC (Phase-13B) | proposal gallery |
| Phase 14 (refiner) | YES (3 modes) | pixel/boundary/calibration + paired Dice | proposal burden | diagnostic figures |
| H3-01 / H3-02 | NA | proposal / component diagnostics | UNAVAILABLE (degenerate) | component outcome chart |
| H3-04 (training) | NA | training / optimization curves only | NA | loss + recall curves |
| H3-05 (supply) | NA | supply coverage by size | UNAVAILABLE (degenerate sentinel) | coverage-by-size |
| H3-06 (downstream) | YES | pixel/boundary/calibration + paired Dice | NA | confusion + paired diff |

### Metric-availability conventions

- `YES` — present and model-identity-matched.
- `NA` — not applicable by task design (e.g. no TN unit for proposal detection).
- `UNAVAILABLE_FROM_SAVED_ARTIFACTS` — the value was never persisted and may not be
  produced without new inference, which is forbidden here.
- `NO` — deliberately not added (e.g. pixel confusion is not duplicated into the
  component-focused failure-analysis notebook).

### Which metrics are NA by task design

- Proposal/localizer notebooks (Phase 13, H3-01, H3-02, H3-05): **no TN-based confusion
  matrix** — background is unbounded, so a defensible negative unit does not exist.
- H3 supply PR/FROC curves: **NA_DEGENERATE_SENTINEL_SCORE** — the persisted
  `best_proposal_score` uses a `-1.0` sentinel and is perfectly separable by construction.

### Which evidence is unavailable

- Pixel confusion / boundary / calibration for any model that is **not** one of the four
  central safe-replay arms (GLOBAL = Phase-10 UNet++, ORACLE_REGIONAL,
  PREDICTED_REGIONAL, H3_DOWNSTREAM). In particular the Phase-09 UNet has no persisted
  per-pixel maps, so those families are `UNAVAILABLE_FROM_SAVED_ARTIFACTS` there.

### Coverage matrix

`reports/tables/phasewise_evaluation_visualization_coverage.csv`
SHA-256 `{COVERAGE_SHA}`

### Provenance

`reports/audits/phasewise_evaluation_visualization_sha_updates.json`
records old/new SHA-256 for every modified notebook, with
`inference_performed=false`, `training_performed=false`, `frozen_metrics_changed=false`.

### Governance

- No training. No inference. No TEST access (TEST reads = 0, external TEST reads = 0).
- Thresholds, checkpoints and frozen scientific gates are unchanged.
- H3 formal adjudication remains **PENDING** (`H3_DOWNSTREAM_EVALUATION_COMPLETE__FORMAL_ADJUDICATION_PENDING`);
  Notebook 07 was not created.
- Phase 15 remains `NOT_STARTED_AND_NOT_AUTHORIZED`.

---

## Future modeling-phase evaluation acceptance template

Every FUTURE modeling / evaluation phase notebook must, **as applicable**, include the
following before it can be accepted. This is a requirement template — it is not data,
and it must never be populated with fabricated values.

1. Complete training curves (loss, task metric, learning rate, epoch timing).
2. Aggregate metrics (pooled and macro).
3. Per-case (per-image) metric tables.
4. Confusion matrix for segmentation / classification tasks (raw + row-normalized).
5. Proposal TP / FP / FN for localization tasks (no TN-based matrix).
6. Component / object recall (size-stratified where relevant).
7. Dice / IoU.
8. Precision / recall / specificity / MCC.
9. Boundary metrics (HD95 / ASSD / surface Dice) with declared units.
10. Uncertainty (bootstrap CIs) and, where compared, paired tests + effect size.
11. Success examples and failure examples (never success-only).
12. Saved figures written to `reports/figures/`.
13. Executed notebook outputs (monotonic execution counts, zero tracebacks).
14. Recorded SHA-256 for the notebook and its source artifacts.
15. TEST leakage = 0 (TEST reads and TEST visualizations both zero).
"""


def main() -> None:
    cov_sha = build_coverage()
    print("Coverage matrix:", COVERAGE.relative_to(ROOT), cov_sha[:16])

    rec = json.loads(REC.read_text(encoding="utf-8"))
    rec["coverage_matrix"] = {"path": "reports/tables/phasewise_evaluation_visualization_coverage.csv",
                              "sha256": cov_sha, "rows": len(ROWS)}

    # ── README ──────────────────────────────────────────────────────────────
    old_readme = sha(README)
    text = README.read_text(encoding="utf-8")
    section = README_SECTION.replace("{COVERAGE_SHA}", cov_sha).strip("\n")
    if "## Evaluation / visualization synchronization" in text:
        head = text[: text.index("## Evaluation / visualization synchronization")]
        text = head + section + "\n"
    else:
        text = text.rstrip("\n") + "\n\n---\n\n" + section + "\n"
    README.write_text(text, encoding="utf-8")
    rec["phasewise_readme"] = {"path": "notebooks/phasewise/README.md",
                               "old_sha256": old_readme, "new_sha256": sha(README)}
    print("README:", old_readme[:12], "->", sha(README)[:12])

    # ── Master index notebook ───────────────────────────────────────────────
    old_idx = sha(INDEX_NB)
    nb = nbformat.read(str(INDEX_NB), as_version=4)
    if not any("Evaluation / Visualization Synchronization Status" in c.source for c in nb.cells):
        nb.cells.append(nbformat.v4.new_markdown_cell(
            "## Evaluation / Visualization Synchronization Status\n\n"
            "Per-completed-phase status of the post-audit evaluation/visualization synchronization.\n"
            "Values: `YES` present · `NO` deliberately not added · `NA` not applicable by design ·\n"
            "`UNAVAILABLE_FROM_SAVED_ARTIFACTS` never persisted and not producible without new inference.\n"
        ))
        nb.cells.append(nbformat.v4.new_code_cell(
            "import pandas as pd\n"
            "from pathlib import Path\n"
            "_cov = pd.read_csv(ROOT / 'reports/tables/phasewise_evaluation_visualization_coverage.csv')\n"
            "display(_cov[['phase', 'main_notebook' if 'main_notebook' in _cov.columns else 'notebook',\n"
            "               'confusion_matrix', 'boundary_metrics', 'calibration', 'component_metrics',\n"
            "               'proposal_metrics', 'pr_curve', 'confidence_intervals', 'qualitative_examples',\n"
            "               'training_curves', 'status']])"
        ))
    nbformat.write(nb, str(INDEX_NB))
    print("Executing master phasewise index ...")
    NotebookClient(nb, kernel_name="jup-venv", timeout=900,
                   resources={"metadata": {"path": str(ROOT)}}).execute()
    nbformat.write(nb, str(INDEX_NB))
    errs = sum(1 for c in nb.cells if c.cell_type == "code"
               for o in c.get("outputs", []) if o.get("output_type") == "error")
    counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
    mono = all(counts[i] == i + 1 for i in range(len(counts)))
    rec["master_phasewise_index"] = {"path": "notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb",
                                     "old_sha256": old_idx, "new_sha256": sha(INDEX_NB),
                                     "code_cells": len(counts), "tracebacks": errs,
                                     "monotonic_execution": bool(mono)}
    print(f"Index: {old_idx[:12]} -> {sha(INDEX_NB)[:12]} | cells={len(counts)} errors={errs} mono={mono}")

    rec["status"] = "PHASEWISE_EVALUATION_VISUALIZATION_SYNC_RECORDED"
    REC.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    print("Record updated:", REC.relative_to(ROOT))


if __name__ == "__main__":
    main()
