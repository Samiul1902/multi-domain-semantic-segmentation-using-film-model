import json, os

with open('notebooks/00_project_visual_index.ipynb', 'r', encoding='utf-8') as f:
    nb = json.load(f)

for idx, c in enumerate(nb['cells']):
    if c['cell_type'] == 'code':
        c['source'] = [
            'import pandas as pd\n',
            'import json, os\n',
            'from IPython.display import display, Markdown\n',
            '\n',
            'inv_path = "reports/audits/notebook_visualization_inventory.json" if os.path.exists("reports/audits/notebook_visualization_inventory.json") else "../reports/audits/notebook_visualization_inventory.json"\n',
            'csv_path = "reports/audits/notebook_visualization_inventory.csv" if os.path.exists("reports/audits/notebook_visualization_inventory.csv") else "../reports/audits/notebook_visualization_inventory.csv"\n',
            '\n',
            'with open(inv_path, "r") as f:\n',
            '    inv = json.load(f)\n',
            'print(f"Total Notebooks Audited: {len(inv)}")\n',
            '\n',
            'df = pd.read_csv(csv_path)\n',
            'display(df[["filename", "phase", "total_cells", "image_output_count", "rendered_figures_present"]])\n'
        ]

with open('notebooks/00_project_visual_index.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
print('Fixed 00_project_visual_index.ipynb!')

