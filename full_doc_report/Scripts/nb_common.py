"""Shared helpers for generating the ReMedFiLM notebook family."""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

ROOT = Path(r"D:\Softfors\jup")
OUT = ROOT / "full_doc_report"
FIG = OUT / "figures"
TABLES = OUT / "tables"

BOOTSTRAP = r'''
import sys
from pathlib import Path
sys.path.insert(0, r"D:\Softfors\jup\full_doc_report\Scripts")
import remedfilm_guard as GUARD
GUARD.install()

REPO = Path(r"D:\Softfors\jup")
REPORT = REPO / "full_doc_report"
TABLES = REPORT / "tables"
FIG = REPORT / "figures"

import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from IPython.display import Image, display, Markdown

def fig(subdir, name, width=760):
    """Display a generated figure, failing loudly if it is missing."""
    p = FIG / subdir / f"{name}.png"
    if not p.exists():
        raise FileNotFoundError(f"missing figure: {p}")
    display(Image(filename=str(p), width=width))

def table(path, **kw):
    return pd.read_csv(path, **kw)

GUARD.require()
'''

SELF_TEST = r'''
# Negative control — enforcement must be real, not a flag.
for name, verdict in GUARD.self_test():
    print(f"  {name:28s}: {verdict}")
assert all(v.startswith("blocked") for _, v in GUARD.self_test()), "GUARD FAILED"
print("analysis-only guard verified")
'''


def md(text: str):
    return nbf.v4.new_markdown_cell(text.strip("\n"))


def code(src: str):
    return nbf.v4.new_code_cell(src.strip("\n"))


def write(path: Path, cells: list, meta_extra: dict | None = None) -> None:
    nb = nbf.v4.new_notebook()
    nb["cells"] = cells
    meta = {
        "kernelspec": {"display_name": "Python 3 (ReMedFiLM analysis)",
                       "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.11.9"},
        "remedfilm": {
            "execution_mode": "ANALYSIS_ONLY",
            "training_allowed": False,
            "new_inference_allowed": False,
            "test_access_allowed": False,
            "analysis_seed": 20261027,
            "generated_by": "full_doc_report/Scripts",
        },
    }
    if meta_extra:
        meta["remedfilm"].update(meta_extra)
    nb["metadata"] = meta
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(nbf.writes(nb), encoding="utf-8")
    print(f"WROTE {path.relative_to(ROOT).as_posix()}  cells={len(cells)}")


def standard_open(title: str, subtitle: str, sections: str) -> list:
    """Title + scope + bootstrap + guard self-test."""
    return [
        md(f"""
# {title}

{subtitle}

{sections}
"""),
        code(BOOTSTRAP),
        code(SELF_TEST),
    ]
