import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

# --- gallery: ISIC also draws from the challenge's own Test archive (pooled, re-split) ---
old = '''        c = s.replace("_segmentation.png", ".jpg") \\
             .replace("Task1_Training_GroundTruth", "Task1-2_Training_Input") \\
             .replace("Task1_Validation_GroundTruth", "Task1-2_Validation_Input")'''
new = '''        c = s.replace("_segmentation.png", ".jpg") \\
             .replace("Task1_Training_GroundTruth", "Task1-2_Training_Input") \\
             .replace("Task1_Validation_GroundTruth", "Task1-2_Validation_Input") \\
             .replace("Task1_Test_GroundTruth", "Task1-2_Test_Input")'''
assert old in s
s = s.replace(old, new)

# --- efficiency scatter: keep annotation inside the axes, separate U-Net labels ---
old2 = '''        ax.annotate(m.replace(" (G)", ""), (gm, dice[m]), fontsize=6.2,
                    xytext=(5, -2), textcoords="offset points", color=DARK)'''
new2 = '''        off = {"U-Net": (-34, -10), "Attention U-Net": (5, 4)}.get(
            m.replace(" (G)", ""), (5, -2))
        ax.annotate(m.replace(" (G)", ""), (gm, dice[m]), fontsize=6.2,
                    xytext=off, textcoords="offset points", color=DARK)'''
assert old2 in s
s = s.replace(old2, new2)

old3 = '''    ax.annotate("ReMedFiLM FULL\\n4.84M params · 32.44 cond. GMACs",
                (rx, dice["ReMedFiLM (FULL)"]), fontsize=6.6, color=VERM,
                xytext=(-104, 12), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.7))'''
new3 = '''    ax.annotate("ReMedFiLM FULL\\n4.84M params\\n32.44 cond. GMACs",
                (rx, dice["ReMedFiLM (FULL)"]), fontsize=6.4, color=VERM,
                xytext=(26, -34), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.7,
                                shrinkA=0, shrinkB=4))'''
assert old3 in s
s = s.replace(old3, new3)

p.write_text(s, encoding="utf-8")
print("PATCHED")
