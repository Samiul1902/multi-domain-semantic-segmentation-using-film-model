"""Additively add the post-audit DESCRIPTIVE metric section to Notebook 06.

Preserves the old notebook SHA in the provenance record and writes the new SHA.
Does not change any frozen H3 metric or gate.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(r"D:/Softfors/jup")
NB_PATH = ROOT / "notebooks" / "phasewise" / "post_phase14_h3_proposal_supply" / "06_h3_downstream_evaluation.ipynb"

OLD_SHA = hashlib.sha256(NB_PATH.read_bytes()).hexdigest()
nb = nbformat.read(str(NB_PATH), as_version=4)
print("Notebook 06 cells before:", len(nb.cells), "| old SHA:", OLD_SHA)

MD = r"""
## 30. Post-audit descriptive metric augmentation

The project-wide evaluation-metrics audit added a set of **descriptive** pixel,
boundary, calibration and uncertainty metrics that the original frozen evaluators
never persisted. They were produced by ONE logged deterministic VAL-only replay
(`scripts/evaluation/project_evaluation_metrics_backfill.py`).

**These metrics are `DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE`.** The frozen H3
formal metric domain (detection = component overlap >= 1 px) and the frozen
`TinyRecall_H3 = 59/72` / `R_H3 = 2/15` are UNCHANGED and are not affected by
anything in this section.
"""

CODE = r"""
import json as _json
import pandas as _pd
from pathlib import Path as _P

_bf = _json.loads((ROOT / 'reports/audits/project_evaluation_metrics_backfill.json').read_text(encoding='utf-8'))
_sum = _pd.read_csv(ROOT / 'reports/tables/project_evaluation_segmentation_summary.csv')
_h3 = _sum[_sum['arm'] == 'H3_DOWNSTREAM'].iloc[0]
_conf = _json.loads((ROOT / 'reports/tables/project_evaluation_confusion_matrices.json').read_text(encoding='utf-8'))

print('label           :', _bf['metric_labels']['h3_specific'])
print('safe replay     :', _bf['safe_replay_rule']['verdict'])
print('reproduction    :', {a: r['match'] and r['tiny_match'] for a, r in _bf['reproduction_gate'].items()})
print()
print('H3 DESCRIPTIVE pixel metrics (new, non-gating):')
print('  pooled TP/TN/FP/FN :', _h3['pooled_tp'], '/', _h3['pooled_tn'], '/', _h3['pooled_fp'], '/', _h3['pooled_fn'])
print('  pooled Dice / IoU  :', _h3['pooled_dice'], '/', _h3['pooled_iou'])
print('  pooled precision   :', _h3['pooled_precision'])
print('  pooled recall      :', _h3['pooled_recall'])
print('  pooled specificity :', _h3['pooled_specificity'])
print('  pooled MCC         :', _h3['pooled_mcc'])
print('  balanced accuracy  :', _h3['pooled_balanced_accuracy'])
print('  HD95 (px) mean     :', _h3['image_mean_hd95'])
print('  ASSD (px) mean     :', _h3['image_mean_assd'])
print('  surface Dice @2px  :', _h3['image_mean_surface_dice'])
print('  Brier / ECE / AUROC:', _h3['brier'], '/', _h3['ece'], '/', _h3['roc_auc'])
print('  component TP/FP/FN :', _h3['component_tp_total'], '/', _h3['component_fp_total'], '/', _h3['component_fn_total'])
print('  component precision:', _h3['component_precision_overall'])
print('  Dice 95% CI        :', _h3['dice_ci_low'], '-', _h3['dice_ci_high'])
print()
print('Frozen H3 formal metric (UNCHANGED):')
print('  TinyRecall_H3 =', fd['TinyRecall_H3'], '=', fd['TinyRecall_H3_fraction'])
print('  R_H3          =', fd['R_H3'], '->', fd['interpretation_band'])
"""

ASSERT = r"""
# ── Post-audit descriptive augmentation assertions ───────────────────────────
import json as _json2
_bf2 = _json2.loads((ROOT / 'reports/audits/project_evaluation_metrics_backfill.json').read_text(encoding='utf-8'))
assert _bf2['metric_labels']['h3_specific'] == 'DESCRIPTIVE_SUPPORTING_METRIC__NOT_H3_GATE'
assert _bf2['safe_replay_rule']['verdict'] == 'REPLAY_PERFORMED_LAWFULLY'
for _a, _r in _bf2['reproduction_gate'].items():
    assert _r['match'] is True and _r['tiny_match'] is True, _a
assert _bf2['governance']['frozen_gates_changed'] is False
assert _bf2['governance']['thresholds_changed'] is False
# The frozen H3 formal metric is untouched by the augmentation.
assert down['formal_downstream']['TinyRecall_H3_fraction'] == '59/72'
assert abs(down['formal_downstream']['R_H3'] - 2/15) < 1e-12
assert down['formal_downstream']['interpretation_band'] == 'insufficient'
print('✓ Post-audit descriptive augmentation assertions passed (frozen H3 metric unchanged).')
"""

# Locate the Assertions markdown cell and insert before it
idx_assert_md = next(i for i, c in enumerate(nb.cells)
                     if c.cell_type == "markdown" and "## Assertions" in "".join(c.source))
nb.cells.insert(idx_assert_md, nbformat.v4.new_code_cell(CODE.strip("\n")))
nb.cells.insert(idx_assert_md, nbformat.v4.new_markdown_cell(MD.strip("\n")))

# Append the extra assertion cell at the end
nb.cells.append(nbformat.v4.new_code_cell(ASSERT.strip("\n")))

nbformat.write(nb, str(NB_PATH))
print("Re-executing Notebook 06...")
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

# Record the SHA transition additively
import json
rec_path = ROOT / "reports" / "audits" / "project_evaluation_notebook_sha_updates.json"
rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.exists() else {
    "artifact": "project_evaluation_notebook_sha_updates",
    "status": "NOTEBOOK_SHA_TRANSITIONS_RECORDED",
    "note": "Additive notebook updates performed by the project-wide evaluation-metrics audit.",
    "transitions": [],
}
entry = {
    "notebook": "notebooks/phasewise/post_phase14_h3_proposal_supply/06_h3_downstream_evaluation.ipynb",
    "change": "added section 30 (post-audit descriptive metric augmentation) + assertions",
    "old_sha256": OLD_SHA, "new_sha256": new_sha,
    "frozen_metrics_changed": False,
}
rec["transitions"] = [t for t in rec["transitions"] if t["notebook"] != entry["notebook"]] + [entry]
rec_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
print("Recorded SHA transition ->", rec_path.name)
