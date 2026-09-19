"""Build display-only Phase 11-R1 manual prediction demo notebook."""
from pathlib import Path
import nbformat as nbf

ROOT = Path(__file__).resolve().parents[2]
nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {"display_name": "jup-venv", "language": "python", "name": "jup-venv"},
    "language_info": {"name": "python", "version": "3.11"},
    "phase": "11-R1",
    "display_only": True,
}


def md(s):
    return nbf.v4.new_markdown_cell(s)


def code(s):
    return nbf.v4.new_code_cell(s)


nb.cells = [
    md(
        "# Phase 11-R1 — KUB Manual Prediction Demo & Future Auto-Domain Interface\n\n"
        "This notebook demonstrates the reusable KUB manual prediction utility (`predict_kub`) "
        "on a permitted validation sample, and documents the planned architecture and interface for "
        "future unified automatic domain routing (**Auto-RA-MedFiLM-Seg++**).\n\n"
        "**Governance & Integrity:**\n"
        "- Model: UNet++ (`phase10_kub_unetpp_seed42_512` best checkpoint @ threshold 0.5)\n"
        "- Sample: Permitted KUB VAL split image\n"
        "- TEST & External Data: Locked; reads blocked by `TestAccessError`\n"
        "- Retraining / Optimization: None"
    ),
    code(
        "import sys\n"
        "from pathlib import Path\n"
        "import pandas as pd\n"
        "import matplotlib.pyplot as plt\n"
        "from IPython.display import display\n\n"
        "ROOT = Path.cwd().resolve()\n"
        "if ROOT.name == 'notebooks': ROOT = ROOT.parent\n"
        "if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))\n\n"
        "from src.inference.kub_predict import predict_kub, show_kub_prediction\n"
        "from src.inference.predict import predict\n\n"
        "val_df = pd.read_csv(ROOT / 'manifests/val.csv')\n"
        "sample_row = val_df[val_df['dataset'] == 'KUB'].iloc[0]\n"
        "sample_image_path = sample_row['image_path']\n"
        "print(f\"Selected VAL sample ID: {sample_row['sample_id']}\")"
    ),

    md("## 1. Current KUB manual prediction (`predict_kub`)"),
    code(
        "result = predict_kub(\n"
        "    image_path=sample_image_path,\n"
        "    model_name='unetpp',\n"
        "    checkpoint_path=ROOT / 'checkpoints/phase10_kub_unetpp_seed42_512/best.pt',\n"
        "    threshold=0.5,\n"
        "    device='cpu'\n"
        ")\n"
        "fig, axes = show_kub_prediction(result)\n"
        "plt.show()\n"
        "print(f\"Domain: {result['domain']} (Task {result['task_id']}) | Source: {result['domain_source']}\")\n"
        "print(f\"Original shape: {result['original_shape']}\")"
    ),
    md(
        "## 2. Future unified automatic-domain inference interface\n\n"
        "The intended final architecture for the unified multi-domain phase is **RA-MedFiLM-Seg++ with Automatic Domain Routing**.\n\n"
        "### Task ID Mapping:\n"
        "- **Task 0**: ISIC (dermatology / skin lesion)\n"
        "- **Task 1**: BUSI (breast ultrasound / breast lesion)\n"
        "- **Task 2**: Kvasir-SEG (gastrointestinal endoscopy / polyp)\n"
        "- **Task 3**: KUB-StoneX (urinary radiography / stone)\n\n"
        "### Intended API Usage:\n"
        "```python\n"
        "from src.inference.predict import predict\n\n"
        "# Automatic domain routing (planned for unified multi-domain phase):\n"
        "result = predict(image_path, task='auto')\n\n"
        "# Explicit domain override (for debugging and oracle routing experiments):\n"
        "result = predict(image_path, task='KUB')\n"
        "```\n\n"
        "**Status Notice:** Automatic domain routing is part of the planned unified "
        "RA-MedFiLM-Seg++ phase and is not implemented/validated at Phase 11. Requesting `task='auto'` raises `NotImplementedError`."
    ),
    code(
        "try:\n"
        "    predict(sample_image_path, task='auto')\n"
        "except NotImplementedError as e:\n"
        "    print(f'Expected safety exception caught: {e}')"
    ),
    md(
        "## 3. Phase control\n\n"
        "**Phase 11-R1 complete. STOP. Phase 12 requires explicit researcher authorization.**"
    ),
]

output = ROOT / "notebooks/09b_kub_manual_prediction_demo.ipynb"
output.write_text(nbf.writes(nb), encoding="utf-8")
print(output)
