import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

old = '''        fig, ax = plt.subplots(figsize=(5.6, 2.8))
        ys = np.arange(len(pc))
        for i, r in enumerate(pc):
            p = float(r[pkey]); l = float(r[lo]); h = float(r[hi])
            col = VERM if l > 0 or h < 0 else GREY
            ax.plot([l, h], [i, i], color=col, linewidth=1.5)
            ax.scatter([p], [i], color=col, s=26, zorder=4)
            tag = "excludes 0" if (l > 0 or h < 0) else "includes 0"
            ax.text(h + abs(h - l) * 0.04, i, tag, va="center", fontsize=5.6,
                    color=col)
        ax.axvline(0, color="#333333", linewidth=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels([r[ckey] for r in pc], fontsize=6.2)
        ax.invert_yaxis()
        ax.set_xlabel("Paired Δ Dice (95% CI)")
        ax.set_title("Matched paired contrasts — A8 vs A7 includes zero")
        ax.grid(axis="y", visible=False)'''

new = '''        fig, ax = plt.subplots(figsize=(6.0, 2.9))
        ys = np.arange(len(pc))
        ticklabels = []
        for i, r in enumerate(pc):
            p = float(r[pkey]); l = float(r[lo]); h = float(r[hi])
            excl = (l > 0 or h < 0)
            col = VERM if excl else GREY
            ax.plot([l, h], [i, i], color=col, linewidth=1.6, solid_capstyle="butt")
            ax.scatter([p], [i], color=col, s=30, zorder=4,
                       edgecolor="white", linewidth=0.5)
            ticklabels.append(f"{r[ckey]}   {'CI excludes 0' if excl else 'CI includes 0'}")
        ax.axvline(0, color="#333333", linewidth=0.8)
        ax.set_yticks(ys)
        ax.set_yticklabels(ticklabels, fontsize=6.2)
        ax.invert_yaxis()
        ax.set_xlabel("Paired Δ Dice (95% CI)")
        ax.set_title("Matched paired contrasts — A8 vs A7 includes zero")
        ax.grid(axis="y", visible=False)
        ax.text(0.02, 0.04,
                "A8_vs_A7 CI is 1.6e-5 wide and is drawn to scale",
                transform=ax.transAxes, fontsize=5.6, color=GREY)'''
assert old in s
s = s.replace(old, new)
p.write_text(s, encoding="utf-8")
print("PATCHED")
