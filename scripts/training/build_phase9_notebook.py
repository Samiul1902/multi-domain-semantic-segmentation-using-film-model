"""Build the display-only Phase-9 results notebook; this script never trains."""
from pathlib import Path
import json
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
summary = json.loads((ROOT / "experiments/phase9_kub_unet_baseline_seed42_512/summary.json").read_text(encoding="utf-8"))
metrics = summary["validation_metrics"]

nb = nbf.v4.new_notebook()
nb["metadata"] = {
    "kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
    "language_info": {"name": "python", "version": "3.11"},
    "phase": 9,
    "display_only": True,
}
nb["cells"] = [
    nbf.v4.new_markdown_cell(
        "# Phase 9 — KUB U-Net Baseline Training\n\n"
        "**Completed results notebook — display only.** This notebook reads saved Phase-9 assets. "
        "It does **not** import or invoke the training entrypoint and will not retrain on Restart/Run All.\n\n"
        "- Experiment: `phase9_kub_unet_baseline_seed42_512`\n"
        "- Manifest: `phase4_v2`\n- Evaluation split: **VAL only** (n=283)\n"
        "- Fixed threshold: 0.5\n- TEST: locked and not evaluated\n- External data: not used"
    ),
    nbf.v4.new_code_cell(
        "from pathlib import Path\nimport json\nimport pandas as pd\n"
        "from IPython.display import display, Image, Markdown\n\n"
        "ROOT = Path.cwd().resolve()\n"
        "if ROOT.name == 'notebooks': ROOT = ROOT.parent\n"
        "EXP = ROOT / 'experiments/phase9_kub_unet_baseline_seed42_512'\n"
        "TABLES = ROOT / 'reports/tables'\nFIGURES = ROOT / 'reports/figures/phase9_unet_baseline'\n"
        "QUAL = ROOT / 'reports/qualitative/phase9_unet_baseline'\n"
        "summary = json.loads((EXP / 'summary.json').read_text(encoding='utf-8'))\n"
        "assert summary['manifest_version'] == 'phase4_v2'\n"
        "assert summary['test_accessed'] is False and summary['external_accessed'] is False\n"
        "print('Display-only asset validation: PASS')"
    ),
    nbf.v4.new_markdown_cell("## Frozen protocol and run outcome"),
    nbf.v4.new_code_cell(
        "protocol = pd.DataFrame([\n"
        " ['Model', 'Standard U-Net (1→1 channels, base=32; 7,762,465 parameters)'],\n"
        " ['Input', '512×512 aspect-ratio resize + symmetric padding'],\n"
        " ['Training', 'Seed 42; batch 4; AMP; AdamW (LR=1e-4, WD=1e-4)'],\n"
        " ['Objective', '0.5 BCEWithLogitsLoss + 0.5 DiceLoss'],\n"
        " ['Selection', 'VAL macro Dice; fixed threshold 0.5; patience 15'],\n"
        " ['Outcome', f\"Epochs {summary['epochs_completed']}; best epoch {summary['best_epoch']}; early stopped={summary['early_stopped']}\"],\n"
        "], columns=['Item','Value'])\ndisplay(protocol)"
    ),
    nbf.v4.new_markdown_cell("## Overall VAL metrics"),
    nbf.v4.new_code_cell("display(pd.read_csv(TABLES / 'phase9_unet_val_summary.csv'))"),
    nbf.v4.new_markdown_cell("## Training curves"),
    nbf.v4.new_code_cell(
        "display(Image(filename=str(FIGURES / 'phase9_unet_loss_curves.png'), width=900))\n"
        "display(Image(filename=str(FIGURES / 'phase9_unet_val_dice_curve.png'), width=900))\n"
        "display(Image(filename=str(FIGURES / 'phase9_unet_metrics_curve.png'), width=900))\n"
        "display(Image(filename=str(FIGURES / 'phase9_unet_lr_curve.png'), width=900))"
    ),
    nbf.v4.new_markdown_cell("## FOV and category results"),
    nbf.v4.new_code_cell(
        "display(pd.read_csv(TABLES / 'phase9_unet_fov_summary.csv'))\n"
        "display(Image(filename=str(FIGURES / 'phase9_unet_fov_performance.png'), width=900))\n"
        "display(pd.read_csv(TABLES / 'phase9_unet_category_summary.csv'))\n"
        "display(Image(filename=str(FIGURES / 'phase9_unet_category_performance.png'), width=900))"
    ),
    nbf.v4.new_markdown_cell(
        "## Object-level and frozen size-stratum results\n\n"
        "Size labels use `kub_size_v1`, whose thresholds were frozen from TRAIN FULL_FIELD components only. "
        "They are dataset-relative and are not clinical millimeter categories."
    ),
    nbf.v4.new_code_cell(
        "display(pd.read_csv(TABLES / 'phase9_unet_object_summary.csv'))\n"
        "display(pd.read_csv(TABLES / 'phase9_unet_size_summary.csv'))\n"
        "display(Image(filename=str(FIGURES / 'phase9_unet_size_object_recall.png'), width=900))"
    ),
    nbf.v4.new_markdown_cell(
        "## FULL_FIELD single- versus multi-component analysis\n\n"
        "Grouping uses the existing original-space `component_count` field: single-component means 1 and "
        "multi-component means >1. Object recall is pooled component recall from the existing per-component "
        "table; missed-object rate is its complement."
    ),
    nbf.v4.new_code_cell(
        "import numpy as np\n"
        "per_image = pd.read_csv(TABLES / 'phase9_unet_val_per_image.csv')\n"
        "per_component = pd.read_csv(TABLES / 'phase9_unet_val_per_component.csv')\n"
        "ff = per_image[per_image['view_type'].eq('FULL_FIELD')].copy()\n"
        "ff['Component_Group'] = np.where(ff['component_count'].gt(1), 'MULTI_COMPONENT', 'SINGLE_COMPONENT')\n"
        "component_detection = per_component.groupby('sample_id')['detected'].agg(['sum', 'count'])\n"
        "ff = ff.join(component_detection, on='sample_id')\n"
        "multi_summary = ff.groupby('Component_Group').agg(\n"
        "    N=('sample_id', 'size'), Macro_Dice=('dice', 'mean'),\n"
        "    GT_Components=('count', 'sum'), Detected_Components=('sum', 'sum'))\n"
        "multi_summary['Object_Recall'] = multi_summary['Detected_Components'] / multi_summary['GT_Components']\n"
        "multi_summary['Missed_Object_Rate'] = 1 - multi_summary['Object_Recall']\n"
        "display(multi_summary.reset_index())"
    ),
    nbf.v4.new_markdown_cell("## Deterministic qualitative examples — R3 traceability labels"),
    nbf.v4.new_code_cell("display(Image(filename=str(QUAL / 'phase9_val_qualitative_panel_r3.png'), width=1200))"),
    nbf.v4.new_markdown_cell("## Deterministic failure panel — R3 traceability labels"),
    nbf.v4.new_code_cell("display(Image(filename=str(QUAL / 'phase9_val_failure_panel_r3.png'), width=1200))"),
    nbf.v4.new_markdown_cell(
        "## HD95 validity and provenance\n\n"
        f"HD95 was valid for **{metrics['HD95_Valid_N']}** images and invalid for "
        f"**{metrics['HD95_Invalid_N']}** images. All invalid cases were empty predictions and are recorded "
        "as invalid/NaN rather than assigned a fabricated distance.\n\n"
        "Authoritative source tables are retained under `reports/tables/`; checkpoint and result hashes are "
        "recorded in `reports/audits/phase9_kub_unet_baseline.json`. No TEST metrics are present."
    ),
    nbf.v4.new_code_cell(
        "display(per_image.groupby(['hd95_valid','hd95_invalid_reason'], dropna=False).size().rename('N').reset_index())\n"
        "original_rows = per_component.groupby('sample_id').size()\n"
        "row_audit = per_image[['sample_id','view_type','component_count','gt_component_count']].copy()\n"
        "row_audit['original_component_rows'] = row_audit['sample_id'].map(original_rows).fillna(0).astype(int)\n"
        "display(row_audit[row_audit['original_component_rows'] != row_audit['gt_component_count']])\n"
        "print(f'Per-image rows: {len(per_image)}; original-space per-component rows: {len(per_component)}')"
    ),
    nbf.v4.new_markdown_cell(
        "### Why the component CSV has 333 rows while the object summary has 332 components\n\n"
        "The schemas count components at different stages. `phase9_unet_val_per_component.csv` has one row "
        "for each **original-space GT component** from the retained component metadata (333 rows). The object "
        "summary labels the binary GT masks **after** aspect-ratio resize and padding at 512×512 (332 components). "
        "For sample `32c06da36a7221dc5369e3ee4723c10c`, two original FULL_FIELD components (1,145 and "
        "1,047 pixels) become touching and merge into one connected component after nearest-neighbor downsampling. "
        "Thus the one-row difference is expected, traceable preprocessing behavior—not a prediction-only or "
        "spurious row. Original-component recall and preprocessed-mask object totals remain scientifically "
        "consistent within their explicitly documented schemas."
    ),
    nbf.v4.new_markdown_cell(
        "## Phase control\n\n**Phase 9 complete. STOP. Phase 10 was not executed and requires explicit researcher authorization.**"
    ),
]

output = ROOT / "notebooks/07_kub_unet_baseline_training.ipynb"
output.write_text(nbf.writes(nb), encoding="utf-8")
print(output)
