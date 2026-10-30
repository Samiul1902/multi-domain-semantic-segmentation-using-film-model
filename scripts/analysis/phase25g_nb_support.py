"""Phase25G notebook rendering helpers (deterministic; no Styler, no addresses)."""
from __future__ import annotations

import json

import pandas as pd
from IPython.display import Image, display

import phase25g_common as C

PD_OPTS = {"display.max_rows": None, "display.max_columns": None,
           "display.width": 240, "display.max_colwidth": 70}


def table(name, columns=None):
    df = pd.read_csv(C.TABLE / name)
    if columns:
        df = df[list(columns)]
    with pd.option_context(*[x for kv in PD_OPTS.items() for x in kv]):
        display(df)
    return df


def table_where(name, mask_col, value, columns=None):
    df = pd.read_csv(C.TABLE / name)
    df = df[df[mask_col] == value]
    if columns:
        df = df[list(columns)]
    with pd.option_context(*[x for kv in PD_OPTS.items() for x in kv]):
        display(df)
    return df


def audit(name, keys=None):
    d = C.jload(C.AUD / name)
    if keys:
        d = {k: d[k] for k in keys if k in d}
    print(json.dumps(d, indent=1, sort_keys=True))
    return d


def fig(name):
    display(Image(filename=str(C.FIG / name)))


def say(text):
    print(text)
