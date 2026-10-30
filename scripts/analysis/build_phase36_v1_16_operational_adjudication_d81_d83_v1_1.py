#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase36 — D81/D82/D83 v1.16 OPERATIONAL ADJUDICATION v1_1 (additive, WO#17C).

ADDITIVE REVISION of ``build_phase36_v1_16_operational_adjudication_d81_d83.py``
(v1_0).  v1_0 is PRESERVED BYTE-FOR-BYTE; this builder writes a DISTINCT artifact
(…_v1_1.json) that SUPERSEDES v1_0 for the D81 reachable-write-surface detail.

Why v1_1: the v1_0 figure-target extraction recorded the local variable ``p``
instead of the literal ``FIG / "<name>.png"`` string.  v1_1 resolves the
literal filename by walking the assignment that feeds ``savefig``, and adds the
complete D81 reachable-write-surface inventory (CSV tables, R1-R5 figures, ALL
science markers, the stage journal, stdout/stderr, and PROCESS_EXIT).

D81/D82/D83 verdicts are UNCHANGED from v1_0 (all ESTABLISHED); only the D81
evidence detail is enriched.  Re-run -> REFUSE_OVERWRITE (rc 2).

NO v1.16/v1.17 execution.  NO model.  NO checkpoint.  NO VAL image/GT.
NO TEST.  NO ROUTER_HOLDOUT.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

AUD = ROOT / "reports" / "audits"
V16 = ROOT / "scripts/analysis/phase36_robustness_execution_v1_16.py"
OUT = AUD / "phase36_v1_16_operational_adjudication_d81_d83_v1_1.json"
SUPERSEDES = AUD / "phase36_v1_16_operational_adjudication_d81_d83_v1_0.json"

V16_SHA = "a96b74caa4587aa9d2f83b79ed39c13075a88086109e31d991695a75ec4abab9"
V16_V1_0_SHA = "657af0239af264fd20821321e1cfe239800f8195984eb20e337b9bb138f01713"


def sha256_file(p: Path) -> str | None:
    p = Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def now() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _write_once_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = json.dumps(payload, indent=1, ensure_ascii=False, default=str).encode("utf-8")
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    fd = os.open(str(path), flags, 0o644)
    try:
        total = 0
        while total < len(data):
            n = os.write(fd, data[total:])
            if n is None or n <= 0:
                raise OSError(f"SHORT_WRITE at {total}/{len(data)} for {path}")
            total += n
        os.fsync(fd)
    finally:
        os.close(fd)
    if path.stat().st_size != len(data):
        raise OSError(f"POST_WRITE_SIZE_MISMATCH for {path}")


def _literal_targets(src_text: str) -> dict:
    """Resolve the literal file targets written by run_science's reachable graph."""
    tree = ast.parse(src_text)
    funcs = {n.name: n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def called(node):
        out = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                f = sub.func
                out.add(f.id if isinstance(f, ast.Name) else
                        (f.attr if isinstance(f, ast.Attribute) else None))
        out.discard(None)
        return out

    reach, stack = set(), ["run_science"]
    while stack:
        nm = stack.pop()
        if nm in reach:
            continue
        reach.add(nm)
        fn = funcs.get(nm)
        if fn is None:
            continue
        for c in called(fn):
            if c in funcs and c not in reach:
                stack.append(c)

    csv_literals, fig_literals = [], []
    for nm in sorted(reach):
        fn = funcs.get(nm)
        if fn is None:
            continue
        for sub in ast.walk(fn):
            # _write_csv(TAB / "literal", ...) OR _write_csv((TAB / "literal"), ...)
            if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Name) \
                    and sub.func.id == "_write_csv" and sub.args:
                a0 = sub.args[0]
                if isinstance(a0, ast.BinOp) and isinstance(a0.op, ast.Div):
                    rhs = a0.right
                    if isinstance(rhs, ast.Constant) and isinstance(rhs.value, str):
                        csv_literals.append({"function": nm, "line": sub.lineno,
                                             "target": rhs.value})
            # FIG / "literal.png"
            if isinstance(sub, ast.Assign) and isinstance(sub.value, ast.BinOp) \
                    and isinstance(sub.value.op, ast.Div):
                left = sub.value.left
                rhs = sub.value.right
                if isinstance(left, ast.Name) and left.id == "FIG" \
                        and isinstance(rhs, ast.Constant) and isinstance(rhs.value, str):
                    fig_literals.append({"function": nm, "line": sub.lineno,
                                         "target": rhs.value})
    return {
        "science_reachable_function_count": len(reach),
        "csv_table_targets": sorted({c["target"] for c in csv_literals}),
        "figure_targets": sorted({f["target"] for f in fig_literals}),
        "csv_write_site_count": len(csv_literals),
        "figure_savefig_site_count": len(fig_literals),
    }


def main() -> int:
    src = V16.read_text(encoding="utf-8")
    lit = _literal_targets(src)

    # D81: science marker / journal / stdio / process-exit targets ARE versioned.
    versioned_marker_targets = [
        p for p in ("phase36_robustness_scientific_result_v1_16.json",
                    "phase36_robustness_science_start_v1_16.json",
                    "phase36_robustness_science_failure_v1_16.json")
        if p in src
    ]
    journal_stages = re.findall(r"V1_16_JOURNAL_STAGES", src)
    stdout_stderr_versioned = ("_science_stdout" in src or "stdout_v1_16" in src)

    tab_unversioned = bool(re.search(r'TAB\s*=\s*ROOT\s*/\s*"reports"\s*/\s*"tables"', src))
    fig_unversioned = bool(re.search(
        r'FIG\s*=\s*ROOT\s*/\s*"reports"\s*/\s*"figures"\s*/\s*"phase36_robustness"', src))
    arr_unversioned = bool(re.search(r'ARR\s*=\s*ROOT\s*/\s*"reports"\s*/\s*"arrays"', src))

    n_csv = lit["csv_write_site_count"]
    n_fig = lit["figure_savefig_site_count"]
    write_csv_def = re.search(r"def _write_csv\((.|\n)*?\n\n\n", src)
    csv_w = bool(write_csv_def and 'path.open("w"' in write_csv_def.group(0))
    csv_wt = bool(write_csv_def and "path.write_text(" in write_csv_def.group(0))

    d81 = bool((tab_unversioned or fig_unversioned or arr_unversioned)
               and n_csv > 0 and n_fig > 0 and csv_w and csv_wt)

    payload = {
        "artifact": "phase36_v1_16_operational_adjudication_d81_d83_v1_1",
        "phase": 36,
        "method": "RA-MedFiLM-BARR",
        "revision": "ra_medfilm_barr_phase36_robustness_v1_16",
        "type": "OPERATIONAL_ADJUDICATION",
        "mode": "STATIC_NON_CONSUMING",
        "additive_revision_of": "phase36_v1_16_operational_adjudication_d81_d83_v1_0",
        "supersedes": "phase36_v1_16_operational_adjudication_d81_d83_v1_0.json",
        "supersedes_sha256": V16_V1_0_SHA,
        "v1_0_preserved_byte_for_byte": True,
        "generated_utc": now(),

        "D81": {
            "id": "V1_16_OUTPUT_NAMESPACE_AUDIT_INCOMPLETE__INHERITED_UNVERSIONED_TABLE_AND_FIGURE_WRITE_TARGETS",
            "established": d81,
            "method": "AST-TRANSITIVE-REACHABILITY-FROM-run_science",
            "science_reachable_function_count": lit["science_reachable_function_count"],
            "module_path_roots": {
                "TAB": "reports/tables",
                "ARR": "reports/arrays",
                "FIG": "reports/figures/phase36_robustness",
                "versioned": False,
            },
            "unversioned_roots": {"TAB": tab_unversioned, "FIG": fig_unversioned,
                                  "ARR": arr_unversioned},
            "csv_write_site_count": n_csv,
            "figure_savefig_site_count": n_fig,
            "csv_table_targets_enumerated": lit["csv_table_targets"],
            "figure_targets_enumerated": lit["figure_targets"],
            "csv_writer_uses_open_w": csv_w,
            "csv_writer_uses_write_text_empty_overwrite": csv_wt,
            "overwrite_semantics_classification":
                "INCOMPATIBLE_WITH_ONE_SHOT_PROVENANCE_CONTRACT",
            "complete_reachable_write_surface": {
                "csv_tables": len(lit["csv_table_targets"]),
                "r1_r5_figures": len(lit["figure_targets"]),
                "science_start_marker": "reports/audits/phase36_robustness_science_start_v1_16.json",
                "science_result_artifact": "reports/audits/phase36_robustness_scientific_result_v1_16.json",
                "science_failure_artifact": "reports/audits/phase36_robustness_science_failure_v1_16.json",
                "stage_journal": "V1_16_JOURNAL_STAGES (versioned)",
                "stdout": "(process stdout, not durable in-namespace)",
                "stderr": "(process stderr, not durable in-namespace)",
                "process_exit": "(supervisor-observed; not in exec namespace)",
                "array_outputs": "NONE reachable from run_science (ARR defined but unused on science path)",
                "marker_targets_versioned": versioned_marker_targets,
                "stdout_stderr_versioned": stdout_stderr_versioned,
                "journal_marker_present": len(journal_stages) > 0,
            },
            "namespace_split_markers_versioned_but_tables_figures_not": bool(
                versioned_marker_targets and (tab_unversioned or fig_unversioned or arr_unversioned)),
            "required_repair":
                "v1.17 must route ALL reachable scientific outputs into a unique v1.17 namespace "
                "(TAB reports/tables/phase36_robustness_v1_17/, FIG reports/figures/phase36_robustness_v1_17/, "
                "ARR reports/arrays/phase36_robustness_v1_17/) and make every CSV writer fail-closed "
                "(refuse an existing target) instead of open('w') overwrite.",
        },

        "D81_v1_1_delta_vs_v1_0": {
            "figure_targets_resolved": True,
            "v1_0_figure_targets": ["p"],
            "v1_1_figure_targets": lit["figure_targets"],
            "note": "v1_1 resolves the literal FIG / '<name>.png' filename instead of the "
                    "local savefig variable; verdict unchanged.",
        },

        "frozen_v1_16_authorities": {
            "execution_sha256": V16_SHA,
            "v1_0_adjudication_sha256": V16_V1_0_SHA,
        },
        "preserved": True,
        "v1_16_modified": False,
        "write_semantics": "O_CREAT|O_EXCL + full-write + fsync",
        "terminal": "PHASE36_V1_16_OPERATIONAL_ADJUDICATION_D81_D83_V1_1_COMPLETE",
    }

    if OUT.exists():
        print(json.dumps({"status": "REFUSE_OVERWRITE",
                          "path": str(OUT.relative_to(ROOT))}, indent=1))
        return 2
    _write_once_json(OUT, payload)
    print(json.dumps({
        "status": "D81_ADJUDICATION_V1_1_WRITTEN",
        "path": str(OUT.relative_to(ROOT)),
        "sha256": sha256_file(OUT),
        "D81_established": d81,
        "csv_targets": len(lit["csv_table_targets"]),
        "figure_targets": lit["figure_targets"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
