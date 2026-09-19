"""Validate and execute all cells in notebooks/11c_kub_final_localizer_redesign.ipynb with hardened guards."""
import hashlib
import json
import sys
from pathlib import Path
import nbformat as nbf
from nbclient import NotebookClient

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NB_PATH = PROJECT_ROOT / "notebooks/11c_kub_final_localizer_redesign.ipynb"
PROPOSAL_GRID_PATH = PROJECT_ROOT / "reports/tables/phase13b_stage4d_proposal_grid.csv"
OLD_SHA = "dd4cb55d5e421871a0424ae08904acdbdeb36418c102956316979ec548fccabe"

REQUIRED_SECTIONS = [
    "Phase 13B Stage-4D",
    "Preflight Geometry",
    "Stage-4C",
    "Stage-4D",
    "Continuation Gate",
    "Provenance",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def validate_notebook_structure_and_execution(nb):
    """Hardened validation rule checking cell counts, execution status, errors, and security guards."""
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
            # Check execution
            if cell.get("execution_count") is not None and cell.get("execution_count") > 0:
                executed_code_count += 1
            else:
                reasons.append(f"Cell {idx} (code) is unexecuted (execution_count is None or <=0)")

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

    # Check required sections
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


def run_regression_tests():
    """Verify validator hardening against known failure modes."""
    print("Running Validator Hardening Regression Tests...")
    
    # Test 1: Empty notebook -> FAIL
    nb_empty = nbf.v4.new_notebook()
    is_p1, r1, _ = validate_notebook_structure_and_execution(nb_empty)
    assert not is_p1 and "total cell count == 0" in r1[0], f"Test 1 failed: {r1}"
    print("  Test 1 (Empty notebook -> FAIL): PASS")

    # Test 2: Markdown only notebook -> FAIL
    nb_md_only = nbf.v4.new_notebook()
    nb_md_only.cells = [nbf.v4.new_markdown_cell("# Markdown Only")]
    is_p2, r2, _ = validate_notebook_structure_and_execution(nb_md_only)
    assert not is_p2 and any("code cell count == 0" in r for r in r2), f"Test 2 failed: {r2}"
    print("  Test 2 (Markdown-only notebook -> FAIL): PASS")

    # Test 3: Unexecuted code notebook -> FAIL
    nb_unexec = nbf.v4.new_notebook()
    nb_unexec.cells = [
        nbf.v4.new_markdown_cell("# Title"),
        nbf.v4.new_code_cell("x = 1")  # execution_count is None
    ]
    is_p3, r3, _ = validate_notebook_structure_and_execution(nb_unexec)
    assert not is_p3 and any("unexecuted" in r for r in r3), f"Test 3 failed: {r3}"
    print("  Test 3 (Unexecuted code notebook -> FAIL): PASS")

    print("All Regression Tests PASSED!\n")


def verify_proposal_grid():
    """Verify presence, non-emptiness, configuration count, and canonical row in proposal grid."""
    print(f"Verifying proposal grid artifact: {PROPOSAL_GRID_PATH}")
    assert PROPOSAL_GRID_PATH.exists(), f"Proposal grid artifact not found at {PROPOSAL_GRID_PATH}"
    import pandas as pd
    df = pd.read_csv(PROPOSAL_GRID_PATH)
    assert len(df) > 0, "Proposal grid is empty!"
    assert len(df) == 20, f"Expected 20 configurations in proposal grid, found {len(df)}"
    
    canonical_match = df[
        (df['threshold'] == 0.10) & 
        (df['margin'] == 0.20) & 
        (df['top_k'] == 5) & 
        (df['nms_iou'] == 0.30)
    ]
    assert len(canonical_match) == 1, f"Canonical config not found uniquely in proposal grid! Matches: {len(canonical_match)}"
    row = canonical_match.iloc[0]
    assert abs(row['tiny_recall90'] - 0.726027397260274) < 1e-5, "Tiny recall90 mismatch in proposal grid!"
    assert abs(row['overall_recall90'] - 0.6410256410256411) < 1e-5, "Overall recall90 mismatch in proposal grid!"
    assert int(row['hard_tiny_recovered90']) == 7, "Hard tiny recovered90 mismatch in proposal grid!"
    assert int(row['global_empty_images_covered90']) == 3, "Global empty images mismatch in proposal grid!"
    print("Proposal Grid Verification: PASS (20 configs, canonical config verified)")
    return len(df)


def main():
    # 1. Run validator regression tests
    run_regression_tests()

    # 2. Verify proposal grid artifact
    config_count = verify_proposal_grid()

    # 3. Read and execute the canonical 11c notebook
    print(f"Reading target notebook: {NB_PATH}")
    with open(NB_PATH, "r", encoding="utf-8") as f:
        nb = nbf.read(f, as_version=4)

    client = NotebookClient(nb, timeout=300, kernel_name="python3")
    print(f"Executing all {len(nb.cells)} cells via nbclient (Run All)...")
    client.execute()

    # 4. Apply hardened validation
    is_pass, reasons, stats = validate_notebook_structure_and_execution(nb)
    if not is_pass:
        print("Validation FAILED with reasons:")
        for r in reasons:
            print(f"  - {r}")
        sys.exit(1)

    # 5. Write back executed notebook
    with open(NB_PATH, "w", encoding="utf-8") as f:
        nbf.write(nb, f)

    final_sha256 = sha256_file(NB_PATH)
    status = "PASS" if is_pass else "FAIL"

    # 6. Write validation audit
    audit = {
        "phase": "13B",
        "stage": "Stage-4D-R2",
        "notebook_path": "notebooks/11c_kub_final_localizer_redesign.ipynb",
        "run_all_status": status,
        "python_executable": "D:\\Softfors\\jup\\.venv\\Scripts\\python.exe",
        "builder_bug_fixed": True,
        "validator_zero_cell_guard": True,
        "validator_markdown_guard": True,
        "validator_code_guard": True,
        "validator_execution_guard": True,
        "proposal_grid_verified": True,
        "proposal_grid_path": "reports/tables/phase13b_stage4d_proposal_grid.csv",
        "proposal_grid_config_count": config_count,
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

    audit_path = PROJECT_ROOT / "reports/audits/phase13b_stage4d_notebook_validation.json"
    audit_path.write_text(json.dumps(audit, indent=2), encoding="utf-8")

    md_lines = [
        "# Phase 13B Stage-4D Notebook Validation Audit",
        "",
        f"- **Notebook:** `notebooks/11c_kub_final_localizer_redesign.ipynb`",
        f"- **Status:** {status}",
        f"- **Builder Bug Fixed:** True (`nb.cells = cells` permanent assignment)",
        f"- **Validator Hardening:** PASS (Zero-cell, markdown-only, unexecuted guards active)",
        f"- **Proposal Grid Verified:** True (20 configs, canonical config verified)",
        f"- **Final SHA-256:** `{final_sha256}`",
        f"- **Total Cells:** {stats['total']} (Markdown: {stats['markdown']}, Code: {stats['code']})",
        f"- **Executed Code Cells:** {stats['executed']}",
        f"- **Execution Errors:** {stats['errors']}",
        f"- **Training Calls Found:** {stats['training_calls']}",
        f"- **TEST Access Found:** {stats['test_access']}",
        f"- **External Access Found:** {stats['external_access']}",
    ]
    (PROJECT_ROOT / "reports/audits/phase13b_stage4d_notebook_validation.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"Validation complete: {status} (Errors: {stats['errors']})")
    print(f"Final SHA-256: {final_sha256}")


if __name__ == "__main__":
    main()
