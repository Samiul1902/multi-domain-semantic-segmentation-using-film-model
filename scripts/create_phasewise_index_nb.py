import nbformat as nbf
import json
from pathlib import Path

# Load phasewise map
with open("reports/audits/phasewise_notebook_map.json", "r", encoding="utf-8") as jf:
    phases = json.load(jf)

nb = nbf.v4.new_notebook()
nb.metadata = {
    "kernelspec": {
        "display_name": "Python 3 (ipykernel)",
        "language": "python",
        "name": "python3"
    },
    "language_info": {
        "name": "python",
        "version": "3.11.9"
    }
}

cells = []

cells.append(nbf.v4.new_markdown_cell("""# 00: Master Phase-Wise Project Index & Reviewer Visual Navigation

**Project Title:** RA-MedFiLM-Seg++ (Regional Scale-Aware Feature Interleaving Multi-Domain Medical Segmentation)  
**Target Venue:** Q1 / A* Peer-Reviewed Medical Computer Vision  
**Execution Environment:** `D:\\Softfors\\jup\\.venv\\Scripts\\python.exe` (Kernel: `jup-venv`, PyTorch 2.6.0+cu124, NVIDIA RTX 3060 Ti 8GB)  
**Governance Barrier:** Untouched TEST Split strictly locked (`TEST reads = 0`, `TEST visualizations = 0`).

---

## 1. Architectural Stages & Progression

The 41-phase canonical research progression spans four sequential stages:
- **Stage A (Phases 00–18):** KUB Radiograph Regional & Tiny-Object Development
- **Stage B (Phases 19–26):** Multi-Domain Harmonization & RA-MedFiLM Architecture (ISIC, BUSI, Kvasir, KUB)
- **Stage C (Phases 27–37):** Multi-Domain Rigor, Ablation, Reproducibility, & Clinical Evidence
- **Stage D (Phases 38–40):** Protocol Freeze, Single-Pass Untouched Test Benchmark, & Reproducibility Audit
"""))

cells.append(nbf.v4.new_code_cell("""import pandas as pd
import json
from pathlib import Path
from IPython.display import display, HTML, Image

def find_root():
    p = Path.cwd()
    for _ in range(5):
        if (p / 'reports').exists() and (p / 'manifests').exists():
            return p
        p = p.parent
    return Path('D:/Softfors/jup')

ROOT = find_root()
with open(ROOT / 'reports/audits/phasewise_notebook_map.json', 'r', encoding='utf-8') as f:
    phases = json.load(f)

df = pd.DataFrame(phases)
display(HTML("<h3>Canonical 41-Phase Master Navigation Table</h3>"))
display(df[['phase_id', 'stage', 'title', 'status', 'reviewer_notebook']])
"""))

cells.append(nbf.v4.new_markdown_cell("""## 2. Multi-Domain Standard Dataset Visualizations ($\ge 12$ Samples per Dataset)

The Q1/A* visual evidence standard requires explicit qualitative visualization of sample cases across all four target medical domains from the authorized training cohort:
- **KUB:** Kidney-Ureter-Bladder Radiographs
- **ISIC 2018:** Dermoscopic Lesion Segmentation
- **BUSI:** Breast Ultrasound Lesion Segmentation
- **Kvasir-SEG:** Gastrointestinal Polyp Endoscopy Segmentation
"""))

cells.append(nbf.v4.new_code_cell("""# Display sample grids for all 4 medical imaging domains
import glob
sample_grids = sorted(glob.glob(str(ROOT / 'reports/figures/sample_visualizations/*_sample_grid_12cases.png')))
print(f"Loaded {len(sample_grids)} multi-domain sample grids (12 cases each):")
for g in sample_grids:
    display(Image(filename=g, width=900))
"""))

cells.append(nbf.v4.new_markdown_cell("""## 3. Reviewer Verification & Status Summary

All historical phases through Phase 14 are COMPLETE. Phase 15 protocol is FROZEN awaiting supervisor decision. All later phases (16+) are cleanly partitioned with structured README specifications and zero synthetic/fake results.
"""))

nb.cells = cells
out_path = Path("notebooks/phasewise/00_PHASEWISE_PROJECT_INDEX.ipynb")
nbf.write(nb, str(out_path))
print(f"Wrote master phasewise index notebook: {out_path}")

