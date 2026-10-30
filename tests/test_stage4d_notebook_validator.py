"""Regression tests for Stage-4D notebook validator hardening."""
import pytest
import nbformat as nbf
from pathlib import Path
from scripts.notebooks.validate_stage4d_notebook import (
    validate_notebook_structure_and_execution,
    verify_proposal_grid,
    PROJECT_ROOT,
    NB_PATH
)


def test_empty_notebook_fails():
    nb = nbf.v4.new_notebook()
    is_pass, reasons, stats = validate_notebook_structure_and_execution(nb)
    assert not is_pass
    assert any("total cell count == 0" in r for r in reasons)


def test_markdown_only_notebook_fails():
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell("# Title")]
    is_pass, reasons, stats = validate_notebook_structure_and_execution(nb)
    assert not is_pass
    assert any("code cell count == 0" in r for r in reasons)


def test_unexecuted_code_notebook_fails():
    nb = nbf.v4.new_notebook()
    nb.cells = [
        nbf.v4.new_markdown_cell("# Title"),
        nbf.v4.new_code_cell("x = 1")  # execution_count is None
    ]
    is_pass, reasons, stats = validate_notebook_structure_and_execution(nb)
    assert not is_pass
    assert any("unexecuted" in r for r in reasons)


def test_proposal_grid_verified():
    count = verify_proposal_grid()
    assert count == 20
