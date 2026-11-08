import pathlib
import re

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

start = s.index('    # pipeline flow')
end = s.index('# =============================================================== datasets ====')
new_block = '''    # pipeline flow
    fig, ax = plt.subplots(figsize=(7.0, 3.6))
    ax.set_xlim(0, 10.4)
    ax.set_ylim(0, 5)
    ax.axis("off")

    def box(x, y, w, h, label, color, fs=7.0):
        ax.add_patch(FancyBboxPatch((x, y), w, h,
                                    boxstyle="round,pad=0.05,rounding_size=0.10",
                                    linewidth=1.0, edgecolor=color,
                                    facecolor=color + "1F"))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
                fontsize=fs, color=DARK, linespacing=1.35)

    def arrow(x1, y1, x2, y2, color="#555555", rad=0.0, dashed=False):
        ax.add_patch(FancyArrowPatch(
            (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=10,
            linewidth=1.0, color=color,
            linestyle="--" if dashed else "-",
            connectionstyle=f"arc3,rad={rad}", shrinkA=3, shrinkB=4))

    # top row of components
    box(0.10, 3.35, 1.35, 0.95, "Image +\\ntask id", "#8C8C8C")
    box(1.75, 3.35, 2.10, 0.95, "G\\nGlobalMedFiLM", BLUE)
    box(4.15, 3.35, 1.55, 0.95, "B_phi\\nBenefit Router", ORANGE)
    box(6.00, 3.35, 1.55, 0.95, "R_psi\\nRegional Refiner", GREEN)
    box(7.85, 3.35, 1.55, 0.95, "S_omega\\nPost-Safety", PURPLE)

    for x1, x2 in ((1.45, 1.75), (3.85, 4.15), (5.70, 6.00), (7.55, 7.85)):
        arrow(x1, 3.82, x2, 3.82)

    # final mask box
    box(3.55, 0.30, 3.30, 0.85, "Final segmentation mask", VERM, fs=7.6)

    # three outcomes, each from its own component to its own landing point
    arrow(2.80, 3.35, 4.05, 1.19, color=BLUE, rad=-0.18)
    arrow(6.78, 3.35, 5.60, 1.19, color=GREEN, rad=0.10)
    arrow(8.62, 3.35, 6.95, 1.19, color=PURPLE, rad=0.30, dashed=True)

    ax.text(3.05, 2.22, "outcome 1 · SKIP\\n(global kept)", fontsize=6.3,
            color=BLUE, rotation=-33, ha="center", va="center")
    ax.text(6.42, 2.02, "outcome 2 · REFINE + ACCEPT", fontsize=6.3,
            color=GREEN, rotation=38, ha="center", va="center")
    ax.text(8.42, 2.10, "outcome 3 · REFINE\\n+ REJECT (fallback)", fontsize=6.3,
            color=PURPLE, rotation=52, ha="center", va="center")

    ax.text(0.10, 4.72, "ReMedFiLM FULL inference path", fontsize=8.8,
            fontweight="bold")
    ax.text(0.10, 0.05,
            "GlobalMedFiLM alone produces only outcome 1; the FULL system can take any of the three.",
            fontsize=6.2, color=GREY)
    save(fig, "architecture", "A03_remedfilm_inference_path",
         "CANONICAL_ARCHITECTURE_CONTRACT",
         "Three outcome branches of the FULL assembly: skip, refine+accept, "
         "refine+reject. Only the four-component assembly can take branches 2 and 3.",
         "03", ["src/models/barr/ra_medfilm_barr.py",
                "reports/tables/phase27_val808_predictions.csv"])


'''
s = s[:start] + new_block + s[end:]
p.write_text(s, encoding="utf-8")
print("PATCHED")
