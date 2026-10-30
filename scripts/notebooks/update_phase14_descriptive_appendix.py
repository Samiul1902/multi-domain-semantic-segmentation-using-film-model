"""Additively append a descriptive segmentation-evaluation appendix to the Phase-14 notebook.

Preserves the old SHA in the transition record; writes the new SHA.
No frozen Phase-14 metric or gate is changed.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks" / "phasewise" / "phase_14_regional_refiner" / "phase_14_regional_refiner_pipeline.ipynb"
OLD_SHA = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
nb = nbformat.read(str(NB_PATH), as_version=4)
print("Phase-14 notebook cells before:", len(nb.cells), "| old SHA:", OLD_SHA)

MD = r"""
## 20. Descriptive segmentation-evaluation appendix (post-audit)

Added by the project-wide evaluation-metrics audit. The frozen Phase-14 diagnostic
metrics (`reports/tables/phase14_clean_v3_mode_summary.csv`) are UNCHANGED; this
appendix only adds **descriptive** pixel, boundary and calibration metrics for the
GLOBAL / ORACLE_REGIONAL / PREDICTED_REGIONAL modes, produced by ONE logged
deterministic VAL-only replay.

All values are labelled `DESCRIPTIVE_SUPPORTING_METRIC__NOT_PROSPECTIVE_GATE`.
"""

CODE = r"""
import json as _json
import pandas as _pd

_bf = _json.loads((ROOT / "reports/audits/project_evaluation_metrics_backfill.json").read_text(encoding="utf-8"))
_sum = _pd.read_csv(ROOT / "reports/tables/project_evaluation_segmentation_summary.csv")
_p14 = _sum[_sum["arm"].isin(["GLOBAL", "ORACLE_REGIONAL", "PREDICTED_REGIONAL"])]
_cols = ["arm", "pooled_dice", "pooled_iou", "pooled_precision", "pooled_recall", "pooled_specificity",
         "pooled_balanced_accuracy", "pooled_mcc", "image_mean_hd95", "image_mean_assd",
         "image_mean_surface_dice", "brier", "ece", "roc_auc", "average_precision",
         "dice_ci_low", "dice_ci_high"]
display(_p14[[c for c in _cols if c in _p14.columns]])

print()
print("Frozen Phase-14 primary metrics reproduced exactly by the replay:")
for _arm, _r in _bf["reproduction_gate"].items():
    print(f"  {_arm}: dice {_r['replayed_mean_dice']:.10f} vs frozen {_r['frozen_reference']:.10f} -> {_r['match']}")

print()
print("Boundary units:", _bf["boundary_units"], "| pixel spacing available:", _bf["pixel_spacing_available"])
print("All appended metrics are:", _bf["metric_labels"]["all_new_metrics"])
"""

ASSERT = r"""
import json as _json2
_bf2 = _json2.loads((ROOT / "reports/audits/project_evaluation_metrics_backfill.json").read_text(encoding="utf-8"))
for _a in ["GLOBAL", "ORACLE_REGIONAL", "PREDICTED_REGIONAL"]:
    assert _bf2["reproduction_gate"][_a]["match"] is True, _a
assert _bf2["governance"]["frozen_gates_changed"] is False
assert _bf2["governance"]["thresholds_changed"] is False
assert _bf2["governance"]["test_reads"] == 0
_md = _pd.read_csv(ROOT / "reports/tables/phase14_clean_v3_mode_summary.csv").set_index("mode")
assert abs(float(_md.loc["GLOBAL_ONLY", "mean_dice"]) - 0.6359172411726776) < 1e-12
assert abs(float(_md.loc["PREDICTED_REGIONAL", "mean_dice"]) - 0.4185309062818487) < 1e-12
print("✓ Phase-14 descriptive appendix assertions passed (frozen Phase-14 metrics unchanged).")
"""

nb.cells.append(nbformat.v4.new_markdown_cell(MD.strip("\n")))
nb.cells.append(nbformat.v4.new_code_cell(CODE.strip("\n")))
nb.cells.append(nbformat.v4.new_code_cell(ASSERT.strip("\n")))
nbformat.write(nb, str(NB_PATH))

print("Re-executing Phase-14 notebook...")
client = NotebookClient(nb, kernel_name="jup-venv", timeout=900,
                        resources={"metadata": {"path": str(ROOT)}})
client.execute()
nbformat.write(nb, str(NB_PATH))

errors = 0
for i, c in enumerate(nb.cells):
    if c.cell_type == "code":
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                errors += 1
                print(f"  ERROR cell {i}: {o.get('ename')}: {o.get('evalue')}")
counts = [c.get("execution_count") for c in nb.cells if c.cell_type == "code"]
mono = all(counts[i] == i + 1 for i in range(len(counts)))
new_sha = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
print(f"Cells: {len(nb.cells)} | code cells: {len(counts)}")
print(f"Zero tracebacks: {'PASS' if errors == 0 else 'FAIL'} | monotonic: {'PASS' if mono else 'CHECK'}")
print("Old SHA:", OLD_SHA)
print("New SHA:", new_sha)

rec_path = ROOT / "reports" / "audits" / "project_evaluation_notebook_sha_updates.json"
rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.exists() else {
    "artifact": "project_evaluation_notebook_sha_updates",
    "status": "NOTEBOOK_SHA_TRANSITIONS_RECORDED",
    "note": "Additive notebook updates performed by the project-wide evaluation-metrics audit.",
    "transitions": [],
}
entry = {
    "notebook": "notebooks/phasewise/phase_14_regional_refiner/phase_14_regional_refiner_pipeline.ipynb",
    "change": "appended section 20 (descriptive segmentation-evaluation appendix) + assertions",
    "old_sha256": OLD_SHA, "new_sha256": new_sha, "frozen_metrics_changed": False,
}
rec["transitions"] = [t for t in rec["transitions"] if t["notebook"] != entry["notebook"]] + [entry]
rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
print("Recorded SHA transition ->", rec_path.name)
