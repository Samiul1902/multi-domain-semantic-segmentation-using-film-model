import pytest
from src.research.evaluation import figures
from src.research.deployment.artifacts import digest


def test_missing_measurement_is_not_fabricated(tmp_path, monkeypatch):
    payload = {"banner": "SYNTHETIC_TEST_ONLY", "evidence_classes": ["SYNTHETIC_TEST_ONLY"],
        "cells": [{"model_key": "synthetic", "seed": 42, "status": "COMPLETE_VALIDATED",
                   "equal_domain_macro_dice": .5, "per_domain": {"ISIC": {"dice": .5}}}]}
    monkeypatch.setattr(figures.reports, "collect_results", lambda root: payload)
    monkeypatch.setattr(figures.reports, "per_domain_rows", lambda cells: [
        {"model_key": "synthetic", "seed": 42, "domain": "ISIC", "dice": .5}])
    root = tmp_path / "figures"
    manifest = figures.write_figures(tmp_path, root)
    assert manifest["accuracy_latency_status"] == "PENDING_MEASURED_LATENCY"
    assert not (root / "accuracy_latency.png").exists()
    for name, entry in manifest["files"].items():
        assert digest(root / name) == entry["sha256"]
    with pytest.raises(FileExistsError):
        figures.write_figures(tmp_path, root)
    payload["evidence_classes"].append("REAL")
    with pytest.raises(ValueError, match="mixed"):
        figures.write_figures(tmp_path, tmp_path / "mixed")


def test_no_validated_cells_refused(tmp_path, monkeypatch):
    monkeypatch.setattr(figures.reports, "collect_results", lambda root: {"cells": []})
    with pytest.raises(ValueError):
        figures.write_figures(tmp_path, tmp_path / "empty")
