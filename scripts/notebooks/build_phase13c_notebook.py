import nbformat as nbf
from pathlib import Path
import hashlib

def create_notebook():
    nb = nbf.v4.new_notebook()
    
    cells = []
    
    # Markdown
    cells.append(nbf.v4.new_markdown_cell("# Phase 13B Stage-4D: Final Localizer Redesign\n\n## 1. Motivation\nClean V3 optimization exhibited severe background dominance. Mean max probability barely rose above the 0.10 initialization prior. To reduce the dense negative penalty (16x reduction) without compromising spatial detection, we explore an output heatmap of 128x128 instead of 512x512.\n\n## 2. One-Factor Hypothesis\nWe hypothesize that preserving the exact 512x512 architecture and extracting logits into a parameter-free stride-4 pooling reduction will provide an isolated, non-confounded test of the lower-resolution geometry."))
    
    cells.append(nbf.v4.new_markdown_cell("## 3. Rejected: Truncated Decoder Tapping\nAlthough removing the final upsampling stages would save FLOPs, it was rejected because it modifies network depth, feature representation, and optimization dynamics, making it an un-controlled change."))
    
    cells.append(nbf.v4.new_markdown_cell("## 4. Geometry Comparison and Sigma Equivalence\n- 512x512: 262,144 pixels. Sigma = 3.0.\n- 128x128: 16,384 pixels. Geometrically equivalent Sigma = 0.75.\nNo component collisions (TRAIN/VAL collisions = 0)."))
    
    cells.append(nbf.v4.new_markdown_cell("## 5. Preflight Diagnostics\n- Parameter Count: Unchanged.\n- Constant Initialization: Preserved after AvgPool2d.\n- Coordinate Round Trip: Max error strictly bounded (<= 2 pixels)."))
    
    cells.append(nbf.v4.new_markdown_cell("## 6. Pre-Registered Protocol\n- **ID:** `phase13b_kub_localizer_r512_h128_sigmaeq075_centernetfocal_seed42_v1`\n- **Loss:** CenterNet Focal Loss\n- **Init:** $p=0.10$\n- **Optimizer:** AdamW 1e-4\n- **Epochs:** 100 max\n\n**Continuation Gate:**\n- Tiny >= 0.50\n- Overall >= 0.50\n- Hard Tiny >= 2/16\n- ROI <= 0.10\n- Props <= 5\n\n**Stopping Rule:** If this fails, the learned-localizer branch will be formally closed."))
    
    cells.append(nbf.v4.new_markdown_cell("## 7. Status\n**TRAINING NOT YET AUTHORIZED.**"))
    
    nb.cells = cells
    
    path = "D:/Softfors/jup/notebooks/11c_kub_final_localizer_redesign.ipynb"
    with open(path, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
        
    with open(path, "rb") as f:
        bytes = f.read()
        sha256 = hashlib.sha256(bytes).hexdigest()
        print(f"Notebook created with SHA256: {sha256}")

if __name__ == "__main__":
    create_notebook()

