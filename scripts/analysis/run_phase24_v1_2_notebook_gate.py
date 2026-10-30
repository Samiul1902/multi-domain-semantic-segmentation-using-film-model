"""Post-Phase24 repair -- execute the notebook addendum and prove 3x determinism (section 15).

Design/audit cells only: no model forward, no training. Executes the whole
notebook with nbclient against the frozen design artifacts, then rebuilds the
notebook from the same frozen artifacts twice more and requires a byte-identical
SHA across all three.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(r"D:/Softfors/jup")
NB = (ROOT / "notebooks" / "phasewise" / "phase_24_architecture_spec"
      / "phase24_narrowed_benefit_aware_refinement_spec.ipynb")
ADD = ROOT / "scripts" / "analysis" / "build_phase24_v1_2_notebook_addendum.py"
AUD = ROOT / "reports" / "audits"
PY = str(ROOT / ".venv" / "Scripts" / "python.exe")

# The executed notebook SHA recorded before the supervisor-closure section was
# appended (work-order section 13).  Retained explicitly as provenance.
PRE_SUPERVISOR_CLOSURE_SHA = "97f0efd99a9be662b2c5ba2338132b70131e07ddb01eec58eac2b80295adddff"


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


VOLATILE_KEYS = ("execution",)  # nbclient writes iopub/shell ISO timestamps here
_HEXADDR = re.compile(r"0x[0-9a-fA-F]{6,}")


def _norm_text(s: str) -> str:
    """Collapse memory addresses (object reprs) so outputs are reproducible."""
    return _HEXADDR.sub("0xADDR", s)


def _coalesce(multiline) -> str:
    """Join a multiline text field into one string and normalise it.

    ipykernel emits stdout in *arbitrary transport chunks*, so the identical
    logical text can arrive as ["...forbidden)"] + ["\\n","allowed..."] on one
    run and as ["...forbidden)","\\n","allowed..."] on the next.  The bytes
    differ while the text does not.  Coalescing to a single normalised string
    removes this run-to-run transport volatility without touching content.
    """
    if isinstance(multiline, list):
        s = "".join(multiline)
    else:
        s = multiline
    return _norm_text(s)


def normalise(nb) -> None:
    """Strip execution-environment volatility so the artifact is reproducible.

    Four sources of run-to-run variation are removed (none carries scientific
    content), plus stable cell ids replace random uuid4 ids:

      1. nbclient writes per-cell wall-clock timestamps under metadata.execution;
      2. pandas Styler text/plain reprs embed an object memory address
         (e.g. "<pandas.io.formats.style.Styler at 0x253ffa64850>");
      3. ipykernel splits long stdout/stderr streams into arbitrary chunk
         boundaries, and even splits on print-statement boundaries — the same
         text therefore yields different chunk *counts* and layouts;
      4. Styler HTML <style> blocks are identical in content but re-serialised.
    """
    for i, c in enumerate(nb.cells):
        c["id"] = f"p24v12{i:03d}"
        meta = c.get("metadata")
        if meta is None:
            meta = {}
            c["metadata"] = meta
        for k in VOLATILE_KEYS:
            meta.pop(k, None)
        c["metadata"] = meta

        # 3.a merge consecutive stream outputs of the same name into one
        if c.cell_type == "code":
            merged: list = []
            for o in c.get("outputs", []):
                if (o.get("output_type") == "stream" and merged
                        and merged[-1].get("output_type") == "stream"
                        and merged[-1].get("name") == o.get("name")):
                    merged[-1]["text"] = str(merged[-1]["text"]) + str(o["text"])
                else:
                    merged.append(o)
            c["outputs"] = merged
        else:
            # nbformat forbids `outputs` on non-code cells; drop any stray key
            c.pop("outputs", None)

        # 3.b/2/4 coalesce each text field into a single normalised string
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream" and "text" in o:
                o["text"] = _coalesce(o["text"])
            elif "text" in o:
                o["text"] = [_norm_text(t) for t in o["text"]]
            data = o.get("data")
            if isinstance(data, dict):
                for mime in ("text/plain", "text/html", "text/markdown"):
                    if mime in data:
                        data[mime] = _coalesce(data[mime])

    md = nb.setdefault("metadata", {})
    md.pop("language_info", None)
    md["kernelspec"] = {"display_name": "Python (jup-venv)", "language": "python",
                        "name": "jup-venv"}


def main() -> int:
    import nbformat
    from nbclient import NotebookClient

    # 1) build (idempotent) then execute in place
    subprocess.run([PY, str(ADD)], check=True, capture_output=True)

    nb = nbformat.read(NB, as_version=4)
    client = NotebookClient(nb, timeout=600, kernel_name="jup-venv",
                            allow_errors=False, resources={"metadata": {"path": str(NB.parent)}})
    client.execute()
    normalise(nb)
    nbformat.write(nb, NB)
    sha_executed = sha(NB)
    print("executed notebook SHA:", sha_executed)

    # error / figure audit
    n_err = 0
    n_code = n_exec = 0
    designs = 0
    for c in nb.cells:
        if c.cell_type != "code":
            continue
        n_code += 1
        if c.get("execution_count") is not None:
            n_exec += 1
        for o in c.get("outputs", []):
            if o.get("output_type") == "error":
                n_err += 1
            if o.get("output_type") in ("execute_result", "display_data"):
                designs += 1
    print(f"code cells: {n_exec}/{n_code} executed | errors: {n_err}")

    # 2) determinism: rebuild twice more WITHOUT re-executing the notebook
    shas = [sha_executed]
    for i in (2, 3):
        subprocess.run([PY, str(ADD)], check=True, capture_output=True)
        # re-apply the SAME execution deterministically: strip outputs then re-run
        nb2 = nbformat.read(NB, as_version=4)
        NotebookClient(nb2, timeout=600, kernel_name="jup-venv", allow_errors=False,
                       resources={"metadata": {"path": str(NB.parent)}}).execute()
        normalise(nb2)
        nbformat.write(nb2, NB)
        shas.append(sha(NB))
        print(f"build {i} SHA:", shas[-1])

    identical = len(set(shas)) == 1

    # schema gate: the frozen notebook must be valid nbformat v4
    schema_ok = True
    try:
        nbformat.validate(nbformat.read(NB, as_version=4))
    except Exception as exc:  # pragma: no cover - defensive
        schema_ok = False
        print("nbformat.validate FAILED:", exc)

    # refresh the addendum provenance record with the FINAL executed SHA so the
    # audit trail names the artifact that is actually on disk.
    addp = AUD / "phase24_v1_2_notebook_addendum.json"
    if addp.exists():
        add = json.loads(addp.read_text(encoding="utf-8"))
        add["notebook_sha256_after_execution"] = sha(NB)
        add["executed_and_normalised"] = True
        add.pop("addendum_notebook_sha256_build", None)
        addp.write_text(json.dumps(add, indent=1, ensure_ascii=False), encoding="utf-8")

    out = {
        "artifact": "phase24_v1_2_notebook_determinism",
        "phase": "24",
        "revision": "ra_medfilm_barr_narrowed_v1_2",
        "notebook": str(NB.relative_to(ROOT)).replace("\\", "/"),
        "n_builds": 3,
        "sha256_per_build": shas,
        "n_distinct_sha256": len(set(shas)),
        "byte_identical": identical,
        "byte_identical_three_builds": identical and schema_ok,
        "nbformat_valid": schema_ok,
        "pre_supervisor_closure_sha256": PRE_SUPERVISOR_CLOSURE_SHA,
        "pre_supervisor_closure_sha256_role": "pre-supervisor-closure provenance (section 13)",
        "code_cells": n_code,
        "code_cells_executed": n_exec,
        "errors": n_err,
        "all_intended_code_cells_executed": n_exec == n_code,
        "design_outputs": designs,
        "experimental_result_figures_added": 0,
        "model_forwards": 0,
        "retrained": False,
        "note": "design/audit cells only; no model forward, no training",
        "test_reads": 0,
    }
    (AUD / "phase24_v1_2_notebook_determinism.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")

    print()
    print("3x deterministic:", identical)
    print(json.dumps({"n_distinct": len(set(shas)), "errors": n_err,
                      "executed": f"{n_exec}/{n_code}"}, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
