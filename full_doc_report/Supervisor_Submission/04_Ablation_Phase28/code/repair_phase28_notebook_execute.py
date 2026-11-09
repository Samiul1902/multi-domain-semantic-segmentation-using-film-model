"""Phase 28 -- notebook compliance repair §12-§17.

Full notebook EXECUTION (nbclient) + presentation normalization + 3x determinism
+ PNG integrity.

The notebook is executed THREE times from identical frozen artifacts; each run is
a FULL execution (not a re-serialization). Presentation nondeterminism is
normalized; scientific content, history rows, table bytes, SHAs and PNG bytes are
never altered.

Outputs
-------
reports/audits/phase28_notebook_postrepair_determinism.json
reports/audits/phase28_notebook_postrepair_visual_integrity.json

Usage:
    ./.venv/Scripts/python.exe scripts/analysis/repair_phase28_notebook_execute.py
"""
from __future__ import annotations

import base64
import copy
import hashlib
import io
import json
import re
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
sys.path.insert(0, str(ROOT))

import nbformat  # noqa: E402
from nbclient import NotebookClient  # noqa: E402

NB_DIR = ROOT / "notebooks" / "phasewise" / "phase_28_model_ablation"
NB_PATH = NB_DIR / "phase28_comprehensive_ablation.ipynb"
AUD = ROOT / "reports" / "audits"
WORK = NB_DIR / "_det_exec"

TERMINAL = ("PHASE28_COMPREHENSIVE_ABLATION_MATRIX_COMPLETE__"
            "CORE_ROUTER_AND_REFINER_ABLATIONS_FROZEN__PHASE29_ELIGIBLE_NOT_STARTED")

# --------------------------------------------------------------------------- #
# presentation normalization (§15): ONLY reviewer-presentation nondeterminism.
# Never touches scientific numbers, history rows, table bytes, SHAs or PNG bytes.
# --------------------------------------------------------------------------- #
_ADDR = re.compile(r"0x[0-9a-fA-F]{6,}")
_UUID = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b")
# pandas Styler emits a random hex table id `T_<hex>` (length varies by version)
# and derived `<tableid>_level<r>_col<c>` / `_row<r>_col<c>` element ids.
_STYLE_ID_TABLE = re.compile(r"T_[0-9a-f]{4,12}")
_STYLE_ID_ELEMENT = re.compile(r"(T_[0-9a-f]{4,12})_(level\d+_col\d+|row\d+_col\d+)")
_TIMING = re.compile(r"(\d+(?:\.\d+)?)\s*(?:s|ms|us|µs|ns)\s*(?:per loop|wall time|\u00b1)", re.I)


def normalize_text(s: str) -> str:
    """Strip presentation-only nondeterminism from a text blob."""
    s = _ADDR.sub("0xADDR", s)
    s = _UUID.sub("UUID", s)
    s = _STYLE_ID_ELEMENT.sub(lambda m: "T_STYLEID_" + m.group(2), s)
    s = _STYLE_ID_TABLE.sub("T_STYLEID", s)
    return s


def normalize_outputs(nb) -> None:
    """Normalize reviewer-presentation nondeterminism in place.

    Includes coalescing of consecutive stdout stream chunks (the kernel may split
    the same byte stream into a different number of `stream` outputs between
    runs). The concatenated text is unchanged -- only the chunk boundaries are
    normalized. Scientific numbers, history rows, table bytes, SHAs and PNG bytes
    are never touched.
    """
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        # drop transient kernel/execution metadata that is not part of the evidence
        cell.metadata.pop("execution", None)
        cell.metadata.pop("ExecuteTime", None)

        # ---- coalesce consecutive same-name stream outputs ----
        merged = []
        for out in cell.get("outputs", []):
            out = copy.deepcopy(out)
            if (merged and out.get("output_type") == "stream"
                    and merged[-1].get("output_type") == "stream"
                    and merged[-1].get("name") == out.get("name")):
                merged[-1]["text"] = merged[-1].get("text", "") + out.get("text", "")
            else:
                merged.append(out)

        new_outputs = []
        for out in merged:
            if out.get("output_type") == "stream":
                out["text"] = normalize_text(out.get("text", ""))
            data = out.get("data")
            if isinstance(data, dict):
                for mime in ("text/plain", "text/html"):
                    if mime in data:
                        v = data[mime]
                        data[mime] = ([normalize_text(x) for x in v]
                                      if isinstance(v, list) else normalize_text(v))
            new_outputs.append(out)
        cell["outputs"] = new_outputs


def canonical_bytes(nb) -> bytes:
    """Serialize the *executed* notebook after presentation normalization."""
    nb = copy.deepcopy(nb)
    normalize_outputs(nb)
    nb.metadata.pop("widgets", None)
    return (json.dumps(nb, indent=1, ensure_ascii=False) + "\n").encode("utf-8")


def execute(nb) -> object:
    client = NotebookClient(
        nb,
        timeout=1800,
        kernel_name="python3",
        allow_errors=False,
        record_timing=False,
        resources={"metadata": {"path": str(ROOT)}},
    )
    return client.execute()


def audit_execution(nb, label: str) -> dict:
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    counts = [c.get("execution_count") for c in code_cells]
    errs = []
    pngs = 0
    for ci, c in enumerate(code_cells):
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                errs.append({"cell": ci, "ename": o.get("ename"),
                             "evalue": o.get("evalue")})
            if "image/png" in o.get("data", {}):
                pngs += 1
    non_null = [c for c in counts if c is not None]
    monotonic = non_null == list(range(1, len(code_cells) + 1))
    traceback_text = 0
    for c in code_cells:
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                t = o.get("text", "")
                if "Traceback (most recent call last)" in t:
                    traceback_text += 1
    return {
        "label": label,
        "n_code_cells": len(code_cells),
        "n_executed": len(non_null),
        "all_execution_counts_non_null": len(non_null) == len(code_cells),
        "execution_counts_monotonic": monotonic,
        "execution_counts": counts,
        "n_error_outputs": len(errs),
        "errors": errs[:5],
        "n_embedded_png_outputs": pngs,
        "traceback_text_occurrences": traceback_text,
    }


def png_integrity(nb) -> dict:
    from PIL import Image
    results = []
    for ci, c in enumerate(nb.cells):
        if c.cell_type != "code":
            continue
        for oi, o in enumerate(c.get("outputs", [])):
            b64 = o.get("data", {}).get("image/png")
            if not b64:
                continue
            raw = b64 if isinstance(b64, str) else "".join(b64)
            rec = {"cell": ci, "output": oi}
            try:
                data = base64.b64decode(raw, validate=True)
                rec["strict_base64_decode"] = True
            except Exception as e:
                rec["strict_base64_decode"] = False
                rec["decode_error"] = str(e)
                results.append(rec)
                continue
            rec["png_magic"] = data[:8] == b"\x89PNG\r\n\x1a\n"
            rec["has_iend"] = data.rstrip().endswith(b"IEND\xaeB`\x82")
            try:
                im = Image.open(io.BytesIO(data))
                im.verify()
                rec["pil_verify"] = True
                rec["size"] = list(im.size)
            except Exception as e:
                rec["pil_verify"] = False
                rec["verify_error"] = str(e)
            rec["sha256"] = hashlib.sha256(data).hexdigest()
            results.append(rec)
    ok = all(r.get("strict_base64_decode") and r.get("png_magic")
             and r.get("has_iend") and r.get("pil_verify") for r in results)
    return {"n_png_outputs": len(results), "all_png_valid": ok, "pngs": results}


def main() -> int:
    if WORK.exists():
        shutil.rmtree(WORK)
    WORK.mkdir(parents=True, exist_ok=True)

    src = nbformat.read(NB_PATH, as_version=4)
    n_code = sum(1 for c in src.cells if c.cell_type == "code")
    print(f"source notebook: {len(src.cells)} cells | {n_code} code cells")

    run_records = []
    canonical = []
    for r in (1, 2, 3):
        t0 = time.time()
        nb = nbformat.read(NB_PATH, as_version=4)
        nb = execute(nb)
        dt = time.time() - t0
        aud = audit_execution(nb, f"run{r}")
        aud["wall_sec"] = round(dt, 2)
        (WORK / f"run{r}.ipynb").write_bytes(canonical_bytes(nb))
        h = hashlib.sha256((WORK / f"run{r}.ipynb").read_bytes()).hexdigest()
        aud["executed_sha256"] = h
        canonical.append(h)
        run_records.append(aud)
        print(f"run{r}: executed={aud['n_executed']}/{aud['n_code_cells']} "
              f"monotonic={aud['execution_counts_monotonic']} errors={aud['n_error_outputs']} "
              f"pngs={aud['n_embedded_png_outputs']} wall={aud['wall_sec']}s sha={h[:16]}")

    three_x = len(set(canonical)) == 1

    # promote run1 as the canonical executed notebook
    shutil.copyfile(WORK / "run1.ipynb", NB_PATH)

    # ---- §17 determinism audit ----
    det = {
        "artifact": "phase28_notebook_postrepair_determinism",
        "phase": 28,
        "classification": "PHASE28_NOTEBOOK_POSTREPAIR_DETERMINISM",
        "notebook": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
        "execution_engine": "nbclient.NotebookClient",
        "kernel": "python3",
        "n_full_executions": 3,
        "executed_notebook_sha256": canonical,
        "run1_sha256": canonical[0],
        "run2_sha256": canonical[1],
        "run3_sha256": canonical[2],
        "notebook_3x_FULL_EXECUTION_byte_identical": three_x,
        "runs": run_records,
        "all_runs_executed": all(x["all_execution_counts_non_null"] for x in run_records),
        "all_runs_monotonic": all(x["execution_counts_monotonic"] for x in run_records),
        "all_runs_zero_errors": all(x["n_error_outputs"] == 0 for x in run_records),
        "all_runs_zero_tracebacks": all(x["traceback_text_occurrences"] == 0 for x in run_records),
        "presentation_normalization": [
            "text memory addresses (0x...)",
            "UUID-like transient ids",
            "pandas Styler row/col id hashes",
            "transient cell execution metadata",
        ],
        "scientific_content_normalized": False,
        "history_rows_normalized": False,
        "table_bytes_normalized": False,
        "artifact_shas_normalized": False,
        "png_bytes_normalized": False,
        "canonical_notebook_sha256": hashlib.sha256(NB_PATH.read_bytes()).hexdigest(),
        "reads_locked_population": False,
        "all_pass": three_x and all(x["n_error_outputs"] == 0 for x in run_records),
    }
    with open(AUD / "phase28_notebook_postrepair_determinism.json", "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(det, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("determinism 3x:", three_x)

    # ---- §16 visual integrity audit ----
    nb_exec = nbformat.read(NB_PATH, as_version=4)
    vis = png_integrity(nb_exec)
    fig_files = sorted((ROOT / "reports" / "figures").glob("p28_fig*.png"))
    frozen_shas = {hashlib.sha256(p.read_bytes()).hexdigest() for p in fig_files}
    embedded_shas = {r["sha256"] for r in vis["pngs"] if "sha256" in r}
    vis_out = {
        "artifact": "phase28_notebook_postrepair_visual_integrity",
        "phase": 28,
        "classification": "PHASE28_NOTEBOOK_POSTREPAIR_VISUAL_INTEGRITY",
        "notebook": str(NB_PATH.relative_to(ROOT)).replace("\\", "/"),
        "n_embedded_png_outputs": vis["n_png_outputs"],
        "all_png_valid": vis["all_png_valid"],
        "n_frozen_figure_files": len(fig_files),
        "frozen_figure_sha256": sorted(frozen_shas),
        "embedded_figure_sha256": sorted(embedded_shas),
        "embedded_matches_frozen_set": embedded_shas == frozen_shas,
        "all_8_figures_embedded": len(embedded_shas) == 8,
        "pngs": [{k: v for k, v in r.items() if k != "sha256"} for r in vis["pngs"]],
        "all_pass": vis["all_png_valid"] and embedded_shas == frozen_shas,
    }
    with open(AUD / "phase28_notebook_postrepair_visual_integrity.json", "w",
              encoding="utf-8", newline="\n") as f:
        json.dump(vis_out, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("PNG integrity:", vis_out["all_pass"], "| embedded figs:", len(embedded_shas),
          "| matches frozen:", vis_out["embedded_matches_frozen_set"])
    shutil.rmtree(WORK, ignore_errors=True)
    return 0 if det["all_pass"] and vis_out["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
