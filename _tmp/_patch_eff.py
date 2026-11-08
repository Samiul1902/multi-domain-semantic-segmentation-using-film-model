import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

old = '''        off = {"U-Net": (-34, -10), "Attention U-Net": (5, 4),
               "GlobalMedFiLM": (7, -11)}.get(m.replace(" (G)", ""), (5, -2))
        ax.annotate(m.replace(" (G)", ""), (gm, dice[m]), fontsize=6.2,
                    xytext=off, textcoords="offset points", color=DARK)'''
new = '''        name = m.replace(" (G)", "")
        off, ha = {
            "U-Net": ((-36, -10), "left"),
            "Attention U-Net": ((6, 3), "left"),
            "GlobalMedFiLM": ((-9, -15), "right"),
            "Transformer/MiT-style U-Net": ((-8, 7), "right"),
            "DeepLabV3+": ((7, -2), "left"),
        }.get(name, ((6, -2), "left"))
        ax.annotate(name, (gm, dice[m]), fontsize=6.2, xytext=off, ha=ha,
                    textcoords="offset points", color=DARK)'''
assert old in s
s = s.replace(old, new)

old2 = '''    ax.annotate("ReMedFiLM FULL\\n4.84M params\\n32.44 cond. GMACs",
                (rx, dice["ReMedFiLM (FULL)"]), fontsize=6.4, color=VERM,
                xytext=(26, -34), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.7,
                                shrinkA=0, shrinkB=4))'''
new2 = '''    ax.annotate("ReMedFiLM FULL\\n4.84M params\\n32.44 cond. GMACs",
                (rx, dice["ReMedFiLM (FULL)"]), fontsize=6.4, color=VERM,
                xytext=(34, -52), textcoords="offset points", ha="left",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.7,
                                shrinkA=0, shrinkB=6))'''
assert old2 in s
s = s.replace(old2, new2)

s = s.replace("    ax.set_xlim(25, 122)", "    ax.set_xlim(25, 136)")
p.write_text(s, encoding="utf-8")
print("PATCHED efficiency labels")
