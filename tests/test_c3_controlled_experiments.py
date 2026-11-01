from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import pytest
import torch
from PIL import Image
from torch import nn

from src.data.transforms import SegmentationTransform
from src.research.c3_baselines import experiment as C3


def test_frozen_population_metadata_and_seed_scope():
    result = C3.validate_manifest_contract()
    assert result["train_n"] == 5832
    assert result["val_n"] == 808
    assert result["train_val_overlap"] == 0
    assert set(result["val_domains"]) == {"ISIC", "BUSI", "KVASIR", "KUB"}
    for seed in C3.EXPECTED_SEEDS:
        config = C3.build_experiment_config("unet", seed)
        assert config["seed"] == seed
        assert config["dataset"]["test_access"] is False
        assert config["dataset"]["external_access"] is False
        assert config["protocol"]["sha256"] == C3.EXPECTED_PROTOCOL_SHA256
        assert config["recipe"]["resolution"] == 512
        assert config["recipe"]["channels"] == 3
    with pytest.raises(C3.C3ExecutionError):
        C3.build_experiment_config("unet", 7)


def test_real_training_is_hard_blocked_and_test_split_rejected(tmp_path):
    train_factory, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1)
    with pytest.raises(C3.C3ExecutionError, match="PENDING_SEPARATE_AUTHORIZATION"):
        C3.train_run("unet", 42, train_factory, val_loader, tmp_path, synthetic=False)
    with pytest.raises(C3.C3ExecutionError, match="only supports TRAIN and VAL"):
        C3.SyntheticSegmentationDataset("TEST")
    with pytest.raises(C3.C3ExecutionError, match="PENDING_SEPARATE_AUTHORIZATION"):
        C3.main(["run-real", "--model", "unet", "--seed", "42"])


def test_canonical_preprocessing_contract_on_generated_images():
    image = Image.fromarray(np.full((19, 27, 3), 127, dtype=np.uint8), mode="RGB")
    mask_array = np.zeros((19, 27), dtype=np.uint8)
    mask_array[4:13, 7:18] = 255
    mask = Image.fromarray(mask_array, mode="L")
    transform = SegmentationTransform(size=256, train=False, image_mode="RGB")
    image_tensor, mask_tensor, _ = transform(image, mask)
    assert tuple(image_tensor.shape) == (3, 256, 256)
    assert tuple(mask_tensor.shape) == (1, 256, 256)
    assert set(torch.unique(mask_tensor).tolist()).issubset({0.0, 1.0})


def test_domain_macro_metric_is_equal_domain_and_seed_order_is_deterministic():
    _, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1, batch_size=2)

    class ZeroLogit(nn.Module):
        def forward(self, image):
            return torch.zeros((len(image), 1, image.shape[-2], image.shape[-1]))

    _, domains, records = C3._evaluate(
        ZeroLogit(), val_loader, C3.BCEDiceLoss(0.5, 0.5, 1e-6),
        torch.device("cpu"), 0.5, False)
    macro = C3.macro_domain_dice({d: domains[d]["dice"] for d in C3.DOMAIN_ORDER})
    expected = sum(np.mean([r["dice"] for r in records if r["domain"] == d]) for d in C3.DOMAIN_ORDER) / 4
    assert macro == pytest.approx(expected)
    assert len(records) == 4 and len({r["sample_id"] for r in records}) == 4
    from src.data.domain_balanced_sampler import build_domain_balanced_sampler
    labels = ["ISIC"] * 4 + ["BUSI"] * 2 + ["KVASIR"] * 2 + ["KUB"] * 4
    order1 = list(build_domain_balanced_sampler(labels, 42, 3))
    order2 = list(build_domain_balanced_sampler(labels, 42, 3))
    assert order1 == order2


def test_checkpoint_resume_recovers_history_and_rejects_corruption(tmp_path):
    out = tmp_path / "run"
    train_factory, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1, batch_size=2)
    first = C3.train_run("unet", 42, train_factory, val_loader, out, epochs=1,
                         device="cpu", synthetic=True, base_channels=4)
    assert first["status"] == "SYNTHETIC_TEST_ONLY"
    (out / "history.jsonl").write_text("truncated", encoding="utf-8")
    second = C3.train_run("unet", 42, train_factory, val_loader, out, epochs=2,
                          device="cpu", synthetic=True, resume=True, base_channels=4)
    rows = [json.loads(line) for line in (out / "history.jsonl").read_text(encoding="utf-8").splitlines()]
    assert second["completed_epochs"] == 2
    assert [r["epoch"] for r in rows] == [1, 2]
    uninterrupted = tmp_path / "uninterrupted"
    C3.train_run("unet", 42, train_factory, val_loader, uninterrupted, epochs=2,
                 device="cpu", synthetic=True, base_channels=4)
    resumed_state = torch.load(out / "latest.pt", map_location="cpu", weights_only=False)["model_state"]
    uninterrupted_state = torch.load(uninterrupted / "latest.pt", map_location="cpu", weights_only=False)["model_state"]
    assert all(torch.equal(resumed_state[k], uninterrupted_state[k]) for k in resumed_state)
    (out / "latest.pt").write_bytes(b"corrupt")
    with pytest.raises(C3.C3ExecutionError, match="corrupt or incomplete checkpoint"):
        C3.train_run("unet", 42, train_factory, val_loader, out, epochs=3,
                     device="cpu", synthetic=True, resume=True, base_channels=4)


def test_per_image_and_per_domain_exports_and_synthetic_rejection(tmp_path):
    run_dir = tmp_path / "run"
    train_factory, val_loader = C3.make_synthetic_loaders(42, image_size=16, samples_per_domain=1, batch_size=2)
    C3.train_run("unet", 42, train_factory, val_loader, run_dir, epochs=1,
                 device="cpu", synthetic=True, base_channels=4)
    result = C3.evaluate_best_checkpoint(run_dir)
    assert result["status"] == "SYNTHETIC_TEST_ONLY"
    assert len(result["per_image"]) == 8
    assert len(result["per_domain"]) == 4
    assert (run_dir / "per_image_metrics.csv").is_file()
    assert (run_dir / "per_domain_metrics.csv").is_file()
    with pytest.raises(C3.C3ExecutionError, match="synthetic fixture rejected"):
        C3.aggregate_controlled_results([run_dir], tmp_path / "aggregate.json")
    with pytest.raises(C3.C3ExecutionError, match="missing result input"):
        C3.evaluate_best_checkpoint(tmp_path / "missing")


def test_empty_results_schema_has_all_missing_cells_no_metrics(tmp_path):
    result = C3.write_empty_results_schema(tmp_path / "results.json")
    assert result["status"] == "NOT_ESTABLISHED"
    assert len(result["expected_runs"]) == 15
    assert len(result["missing_runs"]) == 15
    assert all(row["status"] == "MISSING" for row in result["expected_runs"])
    assert not any("dice" in row for row in result["expected_runs"])
    disk = json.loads((tmp_path / "results.json").read_text(encoding="utf-8"))
    assert disk["protocol_sha256"] == C3.EXPECTED_PROTOCOL_SHA256


def test_result_schema_rejects_mismatched_run_roster(tmp_path):
    result = C3.write_empty_results_schema(tmp_path / "results.json")
    result["missing_runs"].pop()
    with pytest.raises(C3.C3ExecutionError, match="missing-run roster"):
        C3.validate_controlled_results_schema(result)


def test_model_registry_parameter_counts_and_forward_shapes():
    expected = {
        "unet": 7_763_041,
        "attention_unet": 7_851_285,
        "deeplabv3plus": 40_347_041,
        "transformer_mit_unet": 16_347_777,
        "unetpp": 9_159_681,
    }
    for key in C3.ARCHITECTURES:
        model = C3.build_model(key)
        assert C3.parameter_count(model) == expected[key]
        model.eval()
        with torch.no_grad():
            output = model(torch.zeros((1, 3, 64, 64)))
        assert tuple(output.shape) == (1, 1, 64, 64)
        del model, output
        gc.collect()


def test_analytical_compute_is_labeled_lower_bound():
    model = C3.build_model("unet", base_channels=4)
    result = C3.analytical_macs_lower_bound(model, (1, 3, 32, 32))
    assert result["macs_lower_bound"] > 0
    assert result["gmacs_lower_bound"] > 0
    assert "excludes attention" in result["method"]
    assert C3.estimate_optimizer_checkpoint_bytes(100) == 2400
