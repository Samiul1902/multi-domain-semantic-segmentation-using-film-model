import pathlib

p = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
s = p.read_text(encoding="utf-8")

# T2: keep the best-epoch callout inside the axes and add headroom.
old = '''    ax.annotate(f"best {y[best_epoch-1]:.4f} @ ep {best_epoch}",
                xy=(best_epoch, y[best_epoch - 1]), fontsize=6.5, color=VERM,
                xytext=(-70, 12), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.6))'''
new = '''    ax.set_ylim(y.min() - 0.012, y.max() + 0.016)
    ax.annotate(f"best {y[best_epoch-1]:.4f} @ ep {best_epoch}",
                xy=(best_epoch, y[best_epoch - 1]), fontsize=6.5, color=VERM,
                xytext=(-92, -26), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=VERM, linewidth=0.6,
                                shrinkA=2, shrinkB=3))'''
assert old in s
s = s.replace(old, new)

# EFF01: separate the backbone label from the star and stop clipping the long name.
old2 = '''        off = {"U-Net": (-34, -10), "Attention U-Net": (5, 4)}.get(
            m.replace(" (G)", ""), (5, -2))'''
new2 = '''        off = {"U-Net": (-34, -10), "Attention U-Net": (5, 4),
               "GlobalMedFiLM": (7, -11)}.get(m.replace(" (G)", ""), (5, -2))'''
assert old2 in s
s = s.replace(old2, new2)

old3 = '''    ax.set_xlim(25, 110)'''
new3 = '''    ax.set_xlim(25, 122)'''
assert old3 in s
s = s.replace(old3, new3)

p.write_text(s, encoding="utf-8")
print("PATCHED")
