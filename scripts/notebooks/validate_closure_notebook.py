"""Validate and execute all cells in notebooks/12_phase14_15_gate_closure.ipynb with hardened guards."""
import hashlib
import json
import sys
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NB_PATH = PROJECT_ROOT / "notebooks/12_phase14_15_gate_closure.ipynb"
OLD_SHA = "0fc771b731a2aed75a79aeb8a1dd620d127de3af354653ab6eec9097696ce565"

REQUIRED_SECTIONS = [
    "Phase 14 & Phase 15",
    "Phase-13 Canonical",
    "Phase-14 Intended",
    "Phase-15 Dependency",
    "Current Project State",
    "Provenance",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def validate_notebook_structure_and_execution(nb):
    reasons = []
    
    total_cells = len(nb.cells)
    if total_cells == 0:
        reasons.append("total cell count == 0")
        return False, reasons, {"total": 0, "markdown": 0, "code": 0, "executed": 0, "errors": 0}

    markdown_count = 0
    code_count = 0
    executed_code_count = 0
    error_count = 0
    training_calls_found = False
    test_access_found = False
    external_access_found = False

    all_markdown_text = ""

    for idx, cell in enumerate(nb.cells):
        if cell.cell_type == "markdown":
            markdown_count += 1
            all_markdown_text += "\n" + cell.source
        elif cell.cell_type == "code":
            code_count += 1
            if cell.get("execution_count") is not None and cell.get("execution_count") > 0:
                executed_code_count += 1
            else:
                reasons.append(f"Cell {idx} (code) is unexecuted")

            src = cell.source
            if "optimizer.step" in src or "loss.backward" in src or ".train()" in src:
                training_calls_found = True
                reasons.append(f"Cell {idx} contains forbidden training call")
            if "test_loader" in src or "read_test_data" in src or "TEST_CSV" in src:
                test_access_found = True
                reasons.append(f"Cell {idx} contains forbidden TEST data access")
            if "external_test" in src or "external_data" in src:
                external_access_found = True
                reasons.append(f"Cell {idx} contains forbidden external data access")

            for output in cell.get("outputs", []):
                if output.get("output_type") == "error":
                    error_count += 1
                    reasons.append(f"Cell {idx} error: {output.get('ename')}: {output.get('evalue')}")

    if markdown_count == 0:
        reasons.append("markdown cell count == 0")
    if code_count == 0:
        reasons.append("code cell count == 0")
    if executed_code_count != code_count:
        reasons.append(f"executed code count ({executed_code_count}) != total code count ({code_count})")
    if error_count > 0:
        reasons.append(f"total execution errors: {error_count}")

    for sec in REQUIRED_SECTIONS:
        if sec.lower() not in all_markdown_text.lower():
            reasons.append(f"Required section '{sec}' missing from markdown cells")

    stats = {
        "total": total_cells,
        "markdown": markdown_count,
        "code": code_count,
        "executed": executed_code_count,
        "errors": error_count,
        "training_calls": training_calls_found,
        "test_access": test_access_found,
        "external_access": external_access_found,
    }

    is_pass = len(reasons) == 0
    return is_pass, reasons, stats


def main():
    print(f"Reading target notebook: {NB_PATH}")
    with open(NB_PATH, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    client = NotebookClient(nb, timeout=300, kernel_name="python3")
    print(f"Executing all {len(nb.cells)} cells via nbclient (Run All)...")
    client.execute()

    is_pass, reasons, stats = validate_notebook_structure_and_execution(nb)
    if not is_pass:
        print("Validation FAILED with reasons:")
        for r in reasons:
            print(f"  - {r}")
        sys.exit(1)

    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    final_sha256 = sha256_file(NB_PATH)
    status = "PASS" if is_pass else "FAIL"

    audit = {
        "phase": "14-15",
        "notebook_path": "notebooks/12_phase14_15_gate_closure.ipynb",
        "run_all_status": status,
        "python_executable": "D:\\Softfors\\jup\\.venv\\Scripts\\python.exe",
        "old_sha": OLD_SHA,
        "final_notebook_sha256": final_sha256,
        "final_cell_count": stats["total"],
        "final_markdown_cells": stats["markdown"],
        "final_code_cells": stats["code"],
        "final_executed_code_cells": stats["executed"],
        "final_error_count": stats["errors"],
        "training_calls_found": stats["training_calls"],
        "test_access_found": stats["test_access"],
        "external_access_found": stats["external_access"],
    }

    audit_path = PROJECT_ROOT / "reports/audits/phase14_15_closure_notebook_validation.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    md_lines = [
        "# Phase 14/15 Closure Notebook Validation Audit",
        "",
        f"- **Notebook:** `notebooks/12_phase14_15_gate_closure.ipynb`",
        f"- **Status:** {status}",
        f"- **Old SHA-256 (Markdown-only shell):** `{OLD_SHA}`",
        f"- **New SHA-256 (Executable Audit):** `{final_sha256}`",
        f"- **Total Cells:** {stats['total']} (Markdown: {stats['markdown']}, Code: {stats['code']})",
        f"- **Executed Code Cells:** {stats['executed']}",
        f"- **Execution Errors:** {stats['errors']}",
        f"- **Training Calls Found:** {stats['training_calls']}",
        f"- **TEST Access Found:** {stats['test_access']}",
        f"- **External Access Found:** {stats['external_access']}",
    ]
    (PROJECT_ROOT / "reports/audits/phase14_15_closure_notebook_validation.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Validation complete: {status} (Errors: {stats['errors']})")
    print(f"Final SHA-256: {final_sha256}")


if __name__ == "__main__":
    main()
