import pathlib

p = pathlib.Path(r"D:\Softfors\jup\assets\figures\generate_methodology.py")
s = p.read_text(encoding="utf-8")

start = s.index("def build_compact() -> None:")
end = s.index('if __name__ == "__main__":')

new = '''def build_compact() -> None:
    """Single-column version: vertical chain plus an explicit global-fallback lane."""
    BOXES.clear()
    fig = plt.figure(figsize=(3.45, 4.25))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    MX, MW = 3, 66          # main column
    LANE = 84               # global-fallback lane x

    stages = [
        (89, 9, GREY, "$x$,  $t$", "image + task id", "S1"),
        (76, 11, BLUE, "G  GlobalMedFiLM", "task-conditioned FiLM backbone", "S2"),
        (63, 10, BLUE, "ROI proposal", "$P_g$, $F_g$ -> candidate regions", "S3"),
        (50, 10, TEAL, "$B_\\\\phi$  Benefit Router", "decides: refine this ROI?", "S4"),
        (37, 10, VIOLET, "$R_\\\\psi$  Regional Refiner", "residual correction $\\\\Delta P$", "S5"),
        (24, 10, AMBER, "$S_\\\\omega$  Post-Safety Gate", "decides: accept this refinement?", "S6"),
        (6, 13, NAVY, "ReMedFiLM Final Segmentation $\\\\hat{P}$",
         "ROI composition, else global $P_g$", "S7"),
    ]
    for y, h, col, title, sub, _ in stages:
        box(ax, MX, y, MW, h, col, title, sub, fs=6.0, sfs=4.5, owner="C/" + title[:4])

    # vertical chain
    for i in range(len(stages) - 1):
        y_top = stages[i][0]
        y_bot = stages[i + 1][0] + stages[i + 1][1]
        arrow(ax, (MX + MW / 2, y_top), (MX + MW / 2, y_bot), lw=1.1)

    # REFINE tag on the S4 -> S5 link
    tag(ax, MX + MW / 2 + 12, 47.4, "REFINE", GREEN, fs=4.6)
    # ACCEPT tag on the S6 -> S7 link
    tag(ax, MX + MW / 2 + 12, 21.0, "ACCEPT", GREEN, fs=4.6)

    # global-fallback lane: SKIP (from S4) and REJECT (from S6)
    arrow(ax, (MX + MW, 55), (LANE, 55), color=ORANGE, lw=1.0)
    ax.plot([LANE, LANE], [55, 14], color=ORANGE, linewidth=1.0, zorder=2)
    arrow(ax, (MX + MW, 29), (LANE, 29), color=ORANGE, lw=1.0)
    arrow(ax, (LANE, 14), (MX + MW, 14), color=ORANGE, lw=1.0)

    tag(ax, LANE - 9.5, 58.5, "SKIP", ORANGE, fs=4.4)
    tag(ax, LANE - 9.5, 32.5, "REJECT", ORANGE, fs=4.4)
    ax.text(LANE + 1.0, 44, "global\\nfallback", fontsize=4.2, color=ORANGE,
            ha="center", va="center", rotation=90, linespacing=1.2)

    ax.text(50, 1.4, "Three outcomes: skip · refine+accept · refine+reject (global fallback)",
            fontsize=4.2, color=NAVY, ha="center", va="center")

    fig.savefig(OUT / "remedfilm_methodology_compact.svg", format="svg",
                bbox_inches="tight", pad_inches=0.03, facecolor="white")
    fig.savefig(OUT / "remedfilm_methodology_compact.png", dpi=600,
                bbox_inches="tight", pad_inches=0.03, facecolor="white")
    plt.close(fig)
    print("wrote remedfilm_methodology_compact.{svg,png}")


'''

s = s[:start] + new + s[end:]
p.write_text(s, encoding="utf-8")
print("compact rewritten")
