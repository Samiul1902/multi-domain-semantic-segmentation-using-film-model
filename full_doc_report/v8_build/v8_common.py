"""Shared infrastructure for the ReMedFiLM V8 report reconstruction.

Design rules
------------
* Every derived artifact is written from exactly one registry.  No figure or
  table is allowed to hardcode a scientific number.
* Artifacts are write-once.  A pre-existing V8 artifact is MOVED to
  ``_superseded_v8`` with a numeric generation suffix, never deleted.
* SHA-256 always comes from ``Path.read_bytes()`` of the real file on disk.
* No training, no inference, no protected TEST1683 access occurs here.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]          # D:\Softfors\jup
FDR = ROOT / "full_doc_report"
FIG = FDR / "figures"
BUILD = FDR / "v8_build"
SUPERSEDED = FDR / "_superseded_v8"

# Canonical frozen evidence -------------------------------------------------
SRC = {
    "val808": FDR / "REMEDFILM_FULL_VAL808_METRICS.csv",
    "per_sample": FDR / "tables" / "REMEDFILM_INTERNAL_PER_SAMPLE.csv",
    "paired_delta": FDR / "tables" / "REMEDFILM_PAIRED_DELTA.json",
    "external": FDR / "tables" / "REMEDFILM_FULL_EXTERNAL_METRICS.csv",
    "external_raw": ROOT / "reports" / "tables" / "c1_external_stress_summary.csv",
    "stones_sub": ROOT / "reports" / "tables" / "c1_external_stress_stones_subgroups.csv",
    "ablation": FDR / "REMEDFILM_ABLATION_AND_PROGRESSION.csv",
    "ablation_raw": ROOT / "reports" / "tables" / "phase28_table_02_arm_primary_metrics.csv",
    "history": FDR / "tables" / "REMEDFILM_COMPONENT_TRAINING_HISTORY.csv",
    "run_registry": FDR / "tables" / "REMeDFiLM_TRAINING_RUN_REGISTRY.csv",  # corrected below
    "six_model": ROOT / "reports" / "tables" / "phase21_six_model_comparison.csv",
    "efficiency": FDR / "tables" / "REMEDFILM_EFFICIENCY.csv",
    "components": FDR / "REMEDFILM_FULL_COMPONENT_REGISTRY.json",
    "reconciliation": FDR / "REMEDFILM_FULL_RESULT_RECONCILIATION.json",
    "routing": ROOT / "reports" / "tables" / "phase27_val808_predictions.csv",
    "figure_registry": FDR / "figure_registry.json",
    "visual_index": FDR / "tables" / "REMEDFILM_FULL_VISUAL_EVIDENCE_INDEX.csv",
}
SRC["run_registry"] = FDR / "tables" / "REMEDFILM_TRAINING_RUN_REGISTRY.csv"

# Design system -------------------------------------------------------------
NAVY = "#122A43"
NAVY_2 = "#1D3C5C"
BLUE = "#2E6FB7"          # GlobalMedFiLM / backbone
BLUE_LIGHT = "#E8F1FC"
TEAL = "#0E8C7F"          # ReMedFiLM FULL
TEAL_LIGHT = "#E4F4F1"
AMBER = "#C9821A"
RED = "#B83B3B"
GREY = "#5B6B7B"
GREY_LIGHT = "#EEF2F6"
PURPLE = "#6C4FA3"
PURPLE_LIGHT = "#F0EAF9"
WHITE = "#FFFFFF"

PALETTE = {
    "navy": NAVY, "blue": BLUE, "blue_light": BLUE_LIGHT,
    "teal": TEAL, "teal_light": TEAL_LIGHT, "amber": AMBER,
    "red": RED, "grey": GREY, "grey_light": GREY_LIGHT,
    "purple": PURPLE, "purple_light": PURPLE_LIGHT, "white": WHITE,
}

FONT_SERIF = "Georgia, 'Times New Roman', serif"
FONT_SANS = "'Segoe UI', Arial, Helvetica, sans-serif"


def sha256(path: Path | str) -> str:
    """SHA-256 of the bytes actually on disk.  Never a cached/derived value."""
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_artifact(path: Path | str, data: bytes | str) -> Path:
    """Write-once artifact; move a previous generation aside instead of deleting.

    Returns the final path.  Uses O_CREAT|O_EXCL and fsync, then verifies size.
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():
        SUPERSEDED.mkdir(parents=True, exist_ok=True)
        n = 1
        while (SUPERSEDED / f"{p.name}.gen{n}").exists():
            n += 1
        shutil.move(str(p), str(SUPERSEDED / f"{p.name}.gen{n}"))
    raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
    fd = os.open(str(p), os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0))
    try:
        written = 0
        while written < len(raw):
            written += os.write(fd, raw[written:])
        os.fsync(fd)
    finally:
        os.close(fd)
    if p.stat().st_size != len(raw):
        raise IOError(f"short write for {p}: {p.stat().st_size} != {len(raw)}")
    return p


def write_json(path: Path | str, obj) -> Path:
    return write_artifact(path, json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n")


def write_csv(path: Path | str, rows: list[dict], columns: list[str] | None = None) -> Path:
    import io
    if not rows:
        raise ValueError(f"refusing to write empty CSV: {path}")
    cols = columns or list(rows[0].keys())
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in cols})
    return write_artifact(path, buf.getvalue())


def read_csv(path: Path | str) -> list[dict]:
    with open(path, "r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def rel(path: Path | str) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def fmt(x, nd: int = 4) -> str:
    """Uniform decimal precision for the report, with explicit NOT_RECORDED."""
    if x is None or x == "" or x == "NOT_RECORDED":
        return "NOT_RECORDED"
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return str(x)
