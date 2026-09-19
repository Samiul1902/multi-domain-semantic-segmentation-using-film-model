import nbformat
from nbclient import NotebookClient
import os, sys
from pathlib import Path

def execute_notebook(nb_path, output_path=None):
    if output_path is None:
        output_path = nb_path
    print(f"Executing {nb_path}...")
    with open(nb_path, 'r', encoding='utf-8') as f:
        nb = nbformat.read(f, as_version=4)
    
    # Run from PROJECT ROOT
    root_dir = Path('.').resolve()
    client = NotebookClient(nb, timeout=600, kernel_name='python3', resources={'metadata': {'path': str(root_dir)}})
    client.execute()
    
    with open(output_path, 'w', encoding='utf-8') as f:
        nbformat.write(nb, f)
    
    img_count = sum(1 for c in nb.cells if c.cell_type == 'code' for o in c.outputs if 'image/png' in o.get('data', {}))
    errors = [o for c in nb.cells if c.cell_type == 'code' for o in c.outputs if o.output_type == 'error']
    print(f"Done! {nb_path} -> Images: {img_count}, Errors: {len(errors)}")
    if errors:
        for err in errors:
            print("ERROR:", err.get('ename'), err.get('evalue'))
    return len(errors) == 0, img_count

if __name__ == '__main__':
    nb_target = sys.argv[1] if len(sys.argv) > 1 else 'notebooks/00_project_visual_index.ipynb'
    success, imgs = execute_notebook(nb_target)
    print(f"Result: success={success}, images={imgs}")

