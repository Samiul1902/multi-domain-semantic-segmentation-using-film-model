"""Create Phase-9 R3 label-only panel versions from existing rendered panels."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
TABLE = ROOT / "reports/tables/phase9_unet_val_per_image.csv"
QUAL = ROOT / "reports/qualitative/phase9_unet_baseline"
results = pd.read_csv(TABLE)

sorted_results = results.sort_values("dice")
representative_indices = [
    0,
    len(sorted_results) // 4,
    len(sorted_results) // 2,
    3 * len(sorted_results) // 4,
    len(sorted_results) - 1,
]
selections = {
    "phase9_val_qualitative_panel": sorted_results.iloc[representative_indices],
    "phase9_val_failure_panel": sorted_results.head(4),
}

for stem, selected in selections.items():
    source = QUAL / f"{stem}.png"
    image = Image.open(source).convert("RGB")
    figure, axis = plt.subplots(figsize=(15, 15 if len(selected) == 5 else 12))
    axis.imshow(image)
    axis.axis("off")
    for row_index, (_, row) in enumerate(selected.iterrows()):
        y = 1.0 - (row_index + 0.5) / len(selected)
        label = (
            f"{row['sample_id']}\n"
            f"{row['category']} | {row['view_type']}\n"
            f"Dice {row['dice']:.6f} | IoU {row['iou']:.6f}"
        )
        axis.text(
            -0.015, y, label, transform=axis.transAxes, ha="right", va="center",
            fontsize=8, family="monospace",
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "0.5"},
        )
    figure.subplots_adjust(left=0.25, right=0.995, top=0.995, bottom=0.005)
    for extension in ("png", "svg", "pdf"):
        figure.savefig(QUAL / f"{stem}_r3.{extension}", dpi=320, bbox_inches="tight")
    plt.close(figure)
    print(stem, selected["sample_id"].tolist())
