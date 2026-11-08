import pathlib
import re

# ---------- 1. store bootstrap replicates so the density plot is genuine ----
m = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_metrics.py")
s = m.read_text(encoding="utf-8")
old = '''        "cross_check_phase27_macro_point": 0.0022101452700813433,
    }'''
new = '''        "cross_check_phase27_macro_point": 0.0022101452700813433,
        "bootstrap_hist": _hist(boots, 80),
    }'''
assert old in s
s = s.replace(old, new)

helper = '''
def _hist(values, bins):
    counts, edges = np.histogram(values, bins=bins)
    return {"bin_edges": [float(x) for x in edges],
            "counts": [int(x) for x in counts]}


def main() -> None:'''
s = s.replace("\ndef main() -> None:", helper, 1)
m.write_text(s, encoding="utf-8")
print("build_metrics patched")

# ---------- 2. figures: requested subdirectories + Statistics set ----------
f = pathlib.Path(r"D:\Softfors\jup\full_doc_report\Scripts\build_figures.py")
g = f.read_text(encoding="utf-8")

old_dirs = '''SUBDIRS = ["architecture", "datasets", "training_epochs", "internal_evaluation",
           "subgroups", "segmentation", "external_evaluation", "progression",
           "ablation", "routing_safety", "robustness", "efficiency"]'''
new_dirs = '''# Requested report layout.
SUBDIRS = ["Architecture", "Training curves", "Internal validation",
           "Semantic segmentation", "External evaluation", "Ablation",
           "Progression", "Routing and safety", "Statistics", "Robustness",
           "Efficiency"]

# Internal section keys -> requested report directory.
SUBDIR_MAP = {
    "architecture": "Architecture",
    "training_epochs": "Training curves",
    "internal_evaluation": "Internal validation",
    "subgroups": "Internal validation",
    "datasets": "Statistics",
    "segmentation": "Semantic segmentation",
    "external_evaluation": "External evaluation",
    "ablation": "Ablation",
    "progression": "Progression",
    "routing_safety": "Routing and safety",
    "robustness": "Robustness",
    "efficiency": "Efficiency",
    "statistics": "Statistics",
}'''
assert old_dirs in g
g = g.replace(old_dirs, new_dirs)

old_save = '''def save(fig, subdir: str, name: str, evidence: str, caption: str,
         notebook_section: str, sources: list[str]) -> None:
    png = FIG / subdir / f"{name}.png"'''
new_save = '''def save(fig, subdir: str, name: str, evidence: str, caption: str,
         notebook_section: str, sources: list[str]) -> None:
    subdir = SUBDIR_MAP.get(subdir, subdir)
    png = FIG / subdir / f"{name}.png"'''
assert old_save in g
g = g.replace(old_save, new_save)
f.write_text(g, encoding="utf-8")
print("build_figures patched")
