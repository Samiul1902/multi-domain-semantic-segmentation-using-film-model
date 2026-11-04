"""Exercise frozen analysis primitives without running their scientific entrypoints."""
from pathlib import Path

import numpy as np
import pytest
import torch

from scripts.analysis import phase36_robustness_common_v1_0 as robustness


@pytest.mark.parametrize("condition", robustness.image_condition_ids())
def test_frozen_image_perturbations_are_deterministic(condition):
    x = np.random.default_rng(42).random((3, 512, 512), dtype=np.float32)
    before = x.copy()
    a = robustness.apply_image_condition(x, condition, "synthetic-control", base_seed=42)
    b = robustness.apply_image_condition(x, condition, "synthetic-control", base_seed=42)
    assert np.array_equal(a, b) and np.array_equal(x, before)
    assert a.shape == x.shape and np.isfinite(a).all()
    assert a.min() >= 0 and a.max() <= 1


@pytest.mark.parametrize("condition", robustness.proposal_condition_ids())
def test_frozen_spatial_proposal_perturbations(condition):
    geom = robustness.proposal_geometry(40, 100, 50, 110, 512, 512)
    a = robustness.apply_proposal_condition(geom, condition, 512, 512)
    b = robustness.apply_proposal_condition(geom, condition, 512, 512)
    assert a == b


def test_frozen_gradcam_actual_logits_and_no_parameter_gradient():
    from src.models.film import GlobalMedFiLM
    from scripts.analysis import phase35_interpretability_execution_v1_0h as attribution
    torch.manual_seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = GlobalMedFiLM().to(device).eval()
    image = torch.rand(1, 3, 64, 64, device=device)
    result = attribution.gradcam_gradient_enabled_numerically_guarded_v1_0f(
        model, image, torch.tensor([0], device=device), torch.zeros(64, 64, dtype=torch.bool, device=device))
    assert result["empty_mask_helper_check"]["comparison_pass"]
    assert all(torch.isfinite(cam).all() for cam in result["cams"].values())
    assert all(p.grad is None for p in model.parameters())
    assert all(not model.film_layers[name]._forward_hooks for name in attribution.GRADCAM_LAYERS)


def test_phase39_preflight_refuses_before_any_reader(monkeypatch, tmp_path):
    from scripts.analysis import phase39_final_test_execution_v1_2 as execution
    # Isolate only output accounting; retain the real fail-closed static preflight.
    monkeypatch.setattr(execution.C, "ROOT", tmp_path)
    monkeypatch.setattr(execution, "history_gate", lambda: {})
    monkeypatch.setattr(execution, "load_models", lambda: pytest.fail("model load reached"))
    monkeypatch.setattr(execution, "open_manifest", lambda _: pytest.fail("manifest opened"))
    monkeypatch.delenv(execution.C.GATE_ENV, raising=False)
    assert execution.main() == 1
    import json
    failure = json.loads((tmp_path / execution.C.OUT["FAILURE"]).read_text())
    assert "PREFLIGHT" in str(failure)
    assert not (tmp_path / execution.C.OUT["RESULT"]).exists()


def test_phase39_exclusive_publication(tmp_path, monkeypatch):
    from scripts.analysis import phase39_final_test_execution_v1_2 as execution
    monkeypatch.setattr(execution.C, "ROOT", tmp_path)
    execution._exclusive_write_json("synthetic/result.json", {"evidence_class": "SYNTHETIC_TEST_ONLY"})
    with pytest.raises(FileExistsError):
        execution._exclusive_write_json("synthetic/result.json", {})
